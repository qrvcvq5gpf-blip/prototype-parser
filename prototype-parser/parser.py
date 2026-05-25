#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原型解析器核心模块
支持 URL、截图、Figma API 三种输入模式

经验教训（来自实际测试）：
- Windows 环境下 stdout 需要强制 UTF-8 编码
- 墨刀等国产原型工具 DOM 结构特殊，get_by_text 不可靠，需用坐标点击
- 多页面原型需要逐页截取，单次截图只获取当前活动页
- 原型工具自身 UI（侧栏/工具栏）会出现在截图中，AI 分析时需明确指示忽略
- networkidle 后仍需额外等待（2-4秒）确保动态内容渲染完成
"""

import os
import sys
import io
import json
import time
import base64
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union
import anthropic
from playwright.sync_api import sync_playwright
from PIL import Image
import requests

# Windows 环境下强制 UTF-8 输出，避免 GBK 编码错误
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 各原型工具的特征配置
PROTOTYPE_TOOL_CONFIGS = {
    "modao": {
        "domains": ["modao.cc"],
        "page_list_selector": '[class*="screen"], [class*="rn-list-item"]',
        "content_area_selector": ".preview-content-container",
        "extra_wait": 4,
        "needs_multi_page": True,
        "ai_ignore_hint": "左侧是墨刀的页面列表面板（可忽略），中间白色区域是实际原型内容，请只分析中间的原型内容部分。",
    },
    "figma": {
        "domains": ["figma.com"],
        "page_list_selector": None,
        "content_area_selector": None,
        "extra_wait": 3,
        "needs_multi_page": False,
        "ai_ignore_hint": "",
    },
    "jishi": {
        "domains": ["js.design"],
        "page_list_selector": '[class*="page-item"]',
        "content_area_selector": '[class*="canvas"]',
        "extra_wait": 3,
        "needs_multi_page": True,
        "ai_ignore_hint": "左侧是即时设计的页面列表（可忽略），请只分析中间的设计内容。",
    },
    "axure": {
        "domains": ["axure.cloud", "axshare.com"],
        "page_list_selector": "#sitemapTreeContainer li",
        "content_area_selector": "#mainPanel",
        "extra_wait": 3,
        "needs_multi_page": True,
        "ai_ignore_hint": "左侧是 Axure 的页面导航树（可忽略），请只分析右侧的原型内容。",
    },
    "lanhu": {
        "domains": ["lanhuapp.com", "lanhu.com"],
        "page_list_selector": '[class*="page-list"] [class*="item"]',
        "content_area_selector": '[class*="canvas"]',
        "extra_wait": 3,
        "needs_multi_page": True,
        "ai_ignore_hint": "左侧是蓝湖的页面列表（可忽略），请只分析中间的设计内容。",
    },
    "mastergo": {
        "domains": ["mastergo.com"],
        "page_list_selector": '[class*="page-item"]',
        "content_area_selector": '[class*="canvas"]',
        "extra_wait": 3,
        "needs_multi_page": True,
        "ai_ignore_hint": "左侧是 MasterGo 的页面列表（可忽略），请只分析中间的设计内容。",
    },
}


def _detect_tool(url: str) -> Dict:
    """根据 URL 检测原型工具类型"""
    for tool_name, config in PROTOTYPE_TOOL_CONFIGS.items():
        for domain in config["domains"]:
            if domain in url:
                return {"name": tool_name, **config}
    return {
        "name": "unknown",
        "domains": [],
        "page_list_selector": None,
        "content_area_selector": None,
        "extra_wait": 3,
        "needs_multi_page": False,
        "ai_ignore_hint": "如果截图中包含原型工具的 UI 框架（侧栏、工具栏等），请忽略这些部分，只分析实际的原型设计内容。",
    }


class PrototypeParser:
    """原型解析器主类"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 ANTHROPIC_API_KEY，请设置环境变量或传入参数")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        self.cookies_file = Path.home() / ".claude" / "prototype-parser" / "cookies.json"
        self.cookies_file.parent.mkdir(parents=True, exist_ok=True)

    def parse(
        self,
        source: str,
        framework: str = "react",
        record_interaction: bool = False,
        output_dir: str = "./prototype-output",
        full_page: bool = True,
        with_figma_api: bool = False,
    ) -> Dict:
        """
        解析原型并生成代码和文档

        Args:
            source: 原型 URL 或本地截图路径
            framework: 目标框架 (react/vue/html/nextjs)
            record_interaction: 是否录制交互逻辑
            output_dir: 输出目录
            full_page: 是否截取完整页面
            with_figma_api: 是否使用 Figma API 增强模式

        Returns:
            包含代码、文档、交互数据的字典
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"[START] Parsing prototype: {source}")
        print(f"[INFO] Output dir: {output_path.absolute()}")

        # 判断输入类型
        if source.startswith("http"):
            if "figma.com" in source and with_figma_api:
                return self._parse_with_figma_api(source, framework, output_path)
            else:
                return self._parse_from_url(
                    source, framework, record_interaction, output_path, full_page
                )
        else:
            return self._parse_from_screenshot(source, framework, output_path)

    def _parse_from_url(
        self,
        url: str,
        framework: str,
        record_interaction: bool,
        output_path: Path,
        full_page: bool,
    ) -> Dict:
        """从 URL 解析原型"""
        tool_config = _detect_tool(url)
        tool_hint = tool_config["ai_ignore_hint"]
        print(f"[INFO] Detected tool: {tool_config['name']}")

        # 多页面原型：逐页截取
        if tool_config["needs_multi_page"]:
            print("[INFO] Multi-page prototype detected, capturing all pages...")
            page_results = self._capture_multi_page(url, output_path)
            # 使用第一页作为主分析对象
            screenshot = page_results[0]["screenshot"]
        else:
            print("[INFO] Capturing screenshot...")
            screenshot, cookies = self._capture_screenshot(url, full_page)
            if cookies:
                self._save_cookies(cookies)

        # 录制交互（可选）
        interactions = None
        if record_interaction:
            print("[INFO] Starting interaction recording (30s)...")
            interactions = self._record_interactions(url)
            self._save_json(interactions, output_path / "interactions.json")

        # AI 分析
        print("[INFO] AI visual analysis...")
        layout_analysis = self._analyze_layout(screenshot, tool_hint)
        self._save_text(layout_analysis, output_path / "layout_analysis.json")

        # 生成代码
        print(f"[INFO] Generating {framework} code...")
        code = self._generate_code(layout_analysis, interactions, framework)
        code_file = self._get_code_filename(framework)
        self._save_text(code, output_path / code_file)

        # 生成文档
        print("[INFO] Generating spec document...")
        doc = self._generate_doc(layout_analysis, interactions)
        self._save_text(doc, output_path / "spec.md")

        print(f"[DONE] Output files:")
        print(f"   - {code_file}")
        print(f"   - spec.md")
        print(f"   - layout_analysis.json")
        if interactions:
            print(f"   - interactions.json")

        return {
            "code": code,
            "doc": doc,
            "interactions": interactions,
            "layout_analysis": layout_analysis,
        }

    def _parse_from_screenshot(
        self, image_path: str, framework: str, output_path: Path
    ) -> Dict:
        """从截图解析原型"""
        print(f"[INFO] Loading screenshot: {image_path}")

        screenshot = self._load_image(image_path)

        print("[INFO] AI visual analysis...")
        layout_analysis = self._analyze_layout(screenshot)
        self._save_text(layout_analysis, output_path / "layout_analysis.json")

        print(f"[INFO] Generating {framework} code...")
        code = self._generate_code(layout_analysis, None, framework)
        code_file = self._get_code_filename(framework)
        self._save_text(code, output_path / code_file)

        print("[INFO] Generating spec document...")
        doc = self._generate_doc(layout_analysis, None)
        self._save_text(doc, output_path / "spec.md")

        print(f"[DONE] Output files: {code_file}, spec.md")

        return {
            "code": code,
            "doc": doc,
            "interactions": None,
            "layout_analysis": layout_analysis,
        }

    def _parse_with_figma_api(
        self, figma_url: str, framework: str, output_path: Path
    ) -> Dict:
        """使用 Figma API 精确提取"""
        if not self.figma_token:
            raise ValueError("Figma API 模式需要设置 FIGMA_ACCESS_TOKEN 环境变量")

        print("[INFO] Using Figma API for precise extraction...")

        # 提取 file_key
        file_key = self._extract_figma_file_key(figma_url)

        # 调用 Figma API
        file_data = self._fetch_figma_file(file_key)
        self._save_json(file_data, output_path / "figma_raw.json")

        # 提取布局和交互
        layout_data = self._extract_figma_layout(file_data)
        interactions = self._extract_figma_reactions(file_data)

        self._save_json(layout_data, output_path / "layout_analysis.json")
        self._save_json(interactions, output_path / "interactions.json")

        # 生成代码
        print(f"[INFO] Generating {framework} code...")
        code = self._generate_code(json.dumps(layout_data), interactions, framework)
        code_file = self._get_code_filename(framework)
        self._save_text(code, output_path / code_file)

        # 生成文档
        print("📝 生成技术文档...")
        doc = self._generate_doc(json.dumps(layout_data), interactions)
        self._save_text(doc, output_path / "spec.md")

        print(f"[DONE] Output files:")
        print(f"   - {code_file}")
        print(f"   - spec.md")
        print(f"   - interactions.json")

        return {
            "code": code,
            "doc": doc,
            "interactions": interactions,
            "layout_analysis": layout_data,
        }

    def _capture_screenshot(
        self, url: str, full_page: bool = True
    ) -> tuple[bytes, Optional[List]]:
        """
        使用 Playwright 截图

        经验教训：
        - networkidle 后仍需额外等待 2-4 秒（动态渲染）
        - 墨刀等工具可能弹出登录提示横幅，不影响截图但会占据空间
        - headless=True 时无法手动登录，需要切换到 headless=False
        """
        cookies = self._load_cookies()
        tool_config = _detect_tool(url)
        extra_wait = tool_config["extra_wait"]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                # 关键：额外等待动态内容渲染完成
                time.sleep(extra_wait)

                # 检测是否需要登录
                current_url = page.url.lower()
                if any(kw in current_url for kw in ["login", "signin", "auth"]):
                    print("[INFO] Detected login required, opening visible browser...")
                    browser.close()

                    browser = p.chromium.launch(headless=False)
                    context = browser.new_context(viewport={"width": 1920, "height": 1080})
                    page = context.new_page()
                    page.goto(url)

                    print("[INFO] Please login in the browser window (60s timeout)...")
                    page.wait_for_url(
                        lambda u: not any(
                            kw in u.lower() for kw in ["login", "signin", "auth"]
                        ),
                        timeout=60000,
                    )
                    time.sleep(extra_wait)

                # 截图
                screenshot = page.screenshot(full_page=full_page)
                new_cookies = context.cookies()

            except Exception as e:
                print(f"[ERROR] Screenshot failed: {e}")
                raise
            finally:
                browser.close()

        return screenshot, new_cookies

    def _capture_multi_page(
        self, url: str, output_path: Path, max_pages: int = 10
    ) -> List[Dict]:
        """
        逐页截取多页面原型

        经验教训（来自墨刀测试）：
        - 左侧面板同一坐标可能有多层 DOM 元素，需要去重（按 y 坐标 ±5px）
        - get_by_text 对国产工具不可靠，坐标点击更稳定
        - 点击后需要等待 networkidle + 额外 2 秒
        - SVG 等非 HTMLElement 没有 innerText，query 时需要 try-catch
        """
        tool_config = _detect_tool(url)
        cookies = self._load_cookies()
        pages_dir = output_path / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(tool_config["extra_wait"])

            # 截取默认页面
            default_screenshot = page.screenshot(full_page=False)
            default_path = pages_dir / "page_01_default.png"
            default_path.write_bytes(default_screenshot)
            results.append({"name": "default", "path": str(default_path), "screenshot": default_screenshot})

            # 获取左侧面板中的页面列表项（通过坐标定位，避免 DOM 结构差异）
            left_panel_items = page.evaluate("""
                () => {
                    const allEls = document.querySelectorAll('*');
                    const items = [];
                    const seenY = new Set();

                    for (const el of allEls) {
                        const rect = el.getBoundingClientRect();
                        // 左侧面板区域(x < 260), 合适大小, y > 400(跳过工具栏)
                        if (rect.x >= 0 && rect.x < 260 && rect.width > 100 && rect.width < 260 &&
                            rect.height > 20 && rect.height < 50 && rect.y > 300) {

                            // 获取直接文本内容（避免 SVG 等非 HTML 元素报错）
                            let text = '';
                            try { text = el.textContent?.trim() || ''; } catch(e) {}

                            if (text && text.length > 2 && text.length < 80) {
                                // 按 y 坐标去重（±5px 视为同一项）
                                const yKey = Math.round(rect.y / 5) * 5;
                                if (!seenY.has(yKey)) {
                                    seenY.add(yKey);
                                    items.push({
                                        text: text.substring(0, 50),
                                        x: Math.round(rect.x + rect.width / 2),
                                        y: Math.round(rect.y + rect.height / 2),
                                    });
                                }
                            }
                        }
                    }
                    return items.sort((a, b) => a.y - b.y);
                }
            """)

            print(f"[INFO] Found {len(left_panel_items)} page items in left panel")

            # 逐个点击并截图（跳过第一项，因为已经截取了默认页面）
            for i, item in enumerate(left_panel_items[1:max_pages], start=2):
                try:
                    page.mouse.click(item["x"], item["y"])
                    time.sleep(2)
                    try:
                        page.wait_for_load_state("networkidle", timeout=8000)
                    except Exception:
                        pass
                    time.sleep(1)

                    safe_name = item["text"][:20].replace(" ", "_").replace("/", "_").replace("\\", "_")
                    filename = f"page_{i:02d}_{safe_name}.png"
                    screenshot = page.screenshot(full_page=False)
                    filepath = pages_dir / filename
                    filepath.write_bytes(screenshot)

                    results.append({"name": item["text"], "path": str(filepath), "screenshot": screenshot})
                    print(f"  [OK] page {i}: {item['text'][:30]}")
                except Exception as e:
                    print(f"  [FAIL] page {i}: {str(e)[:60]}")
                    continue

            # 保存 cookies
            new_cookies = context.cookies()
            if new_cookies:
                self._save_cookies(new_cookies)

            browser.close()

        print(f"[INFO] Captured {len(results)} pages total")
        return results

    def _record_interactions(self, url: str) -> List[Dict]:
        """录制交互逻辑"""
        interactions = []
        cookies = self._load_cookies()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()

            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()

            # 监听导航事件
            def on_navigate(frame):
                if frame == page.main_frame:
                    interactions.append({"type": "navigate", "url": frame.url})

            page.on("framenavigated", on_navigate)

            # 监听点击事件（通过 JS 注入）
            page.add_init_script(
                """
                document.addEventListener('click', (e) => {
                    const target = e.target;
                    window.__interactions = window.__interactions || [];
                    window.__interactions.push({
                        type: 'click',
                        tagName: target.tagName,
                        id: target.id,
                        className: target.className,
                        text: target.innerText?.substring(0, 50),
                        timestamp: Date.now()
                    });
                });
            """
            )

            page.goto(url, wait_until="networkidle")

            print("[INFO] Please interact with the prototype in the browser (30s)...")
            page.wait_for_timeout(30000)

            # 获取记录的交互
            js_interactions = page.evaluate("window.__interactions || []")
            interactions.extend(js_interactions)

            browser.close()

        return interactions

    def _load_image(self, image_path: str) -> bytes:
        """加载本地图片"""
        with open(image_path, "rb") as f:
            return f.read()

    def _analyze_layout(self, screenshot: bytes, tool_hint: str = "") -> str:
        """
        AI 视觉分析布局

        Args:
            screenshot: 截图二进制数据
            tool_hint: 原型工具 UI 忽略提示（告诉 AI 哪些部分是工具框架）
        """
        image_data = base64.standard_b64encode(screenshot).decode("utf-8")

        # 根据图片格式判断 media_type
        media_type = "image/png"
        if screenshot[:3] == b'\xff\xd8\xff':
            media_type = "image/jpeg"
        elif screenshot[:4] == b'RIFF':
            media_type = "image/webp"

        tool_ignore_instruction = ""
        if tool_hint:
            tool_ignore_instruction = f"\n\n**重要提示**：{tool_hint}\n"

        prompt = f"""分析这个设计稿，提取以下信息（JSON 格式）：
{tool_ignore_instruction}

1. **布局结构**：
   - 容器层级（从外到内）
   - 布局方式（Flexbox/Grid/绝对定位）
   - 主轴和交叉轴方向

2. **间距规范**（精确数值，单位 px）：
   - padding（上右下左）
   - margin（上右下左）
   - gap（行间距、列间距）

3. **组件清单**：
   - 组件类型（按钮/输入框/卡片/导航栏等）
   - 组件位置和尺寸
   - 组件状态（默认/悬停/激活）
   - 语义标注（如"主操作按钮"、"搜索输入框"）

4. **设计令牌**：
   - 颜色（主色/辅助色/文本色/背景色，HEX 值）
   - 字体（字体族、字号、行高、字重）
   - 圆角（border-radius）
   - 阴影（box-shadow）

5. **响应式断点建议**：
   - 移动端（<768px）
   - 平板（768-1024px）
   - 桌面端（>1024px）

**要求**：
- 间距数值通过视觉测量尽可能精确（误差 ±2px）
- 识别重复的设计模式（如卡片列表、表单组）
- 标注组件的层级关系（父子关系）
- 如果有明显的网格系统，描述网格参数

**输出格式**（严格 JSON）：
```json
{
  "layout": {
    "type": "flex|grid|absolute",
    "direction": "row|column",
    "containers": [...]
  },
  "spacing": {
    "padding": {...},
    "margin": {...},
    "gap": {...}
  },
  "components": [
    {
      "type": "button|input|card|...",
      "semantic": "主操作按钮",
      "position": {"x": 0, "y": 0},
      "size": {"width": 120, "height": 40},
      "children": [...]
    }
  ],
  "tokens": {
    "colors": {...},
    "typography": {...},
    "borderRadius": {...},
    "shadows": {...}
  },
  "responsive": {
    "mobile": {...},
    "tablet": {...},
    "desktop": {...}
  }
}
```"""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            return response.content[0].text

        except Exception as e:
            print(f"[ERROR] AI analysis failed: {e}")
            raise

    def _generate_code(
        self, layout_analysis: str, interactions: Optional[List], framework: str
    ) -> str:
        """生成代码"""
        framework_config = {
            "react": {
                "extension": "jsx",
                "template": "React + Tailwind CSS",
                "imports": "import React from 'react';",
            },
            "vue": {
                "extension": "vue",
                "template": "Vue 3 + Tailwind CSS",
                "imports": "<script setup>",
            },
            "html": {
                "extension": "html",
                "template": "HTML + Tailwind CSS",
                "imports": "<!DOCTYPE html>",
            },
            "nextjs": {
                "extension": "jsx",
                "template": "Next.js + Tailwind CSS",
                "imports": "import React from 'react';",
            },
        }

        config = framework_config.get(framework, framework_config["react"])

        interaction_text = ""
        if interactions:
            interaction_text = f"\n\n交互逻辑：\n{json.dumps(interactions, ensure_ascii=False, indent=2)}"

        prompt = f"""基于以下布局分析和交互逻辑，生成 {config['template']} 代码：

布局分析：
{layout_analysis}
{interaction_text}

**要求**：
1. 使用 Tailwind CSS 实现样式（不要写内联样式）
2. 组件化设计，拆分为可复用的子组件
3. 包含交互逻辑（如果有）：点击事件、页面跳转、状态管理
4. 响应式布局（使用 Tailwind 的响应式前缀）
5. 代码注释清晰，标注关键布局和交互
6. 使用语义化的 HTML 标签
7. 确保可访问性（ARIA 属性、键盘导航）

**输出格式**：
- 直接输出完整的可运行代码
- 无需解释，只要代码
- 如果是 React/Vue，包含必要的 import 语句
- 如果是 HTML，包含完整的 <!DOCTYPE> 和 <head>

开始生成代码："""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=16384,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text

        except Exception as e:
            print(f"[ERROR] Code generation failed: {e}")
            raise

    def _generate_doc(self, layout_analysis: str, interactions: Optional[List]) -> str:
        """生成技术文档"""
        interaction_text = ""
        if interactions:
            interaction_text = f"\n\n交互逻辑：\n{json.dumps(interactions, ensure_ascii=False, indent=2)}"

        prompt = f"""基于以下信息，生成技术规格文档（Markdown 格式）：

布局分析：
{layout_analysis}
{interaction_text}

**文档结构**：

# 技术规格文档

## 1. 页面概述
（一句话描述页面功能和目标用户）

## 2. 页面结构
（描述整体布局层级，使用树状结构）
```
Container
├── Header
│   ├── Logo
│   └── Navigation
├── Main
│   ├── Sidebar
│   └── Content
└── Footer
```

## 3. 布局规范

### 3.1 容器布局
| 容器 | 布局方式 | 主轴方向 | 对齐方式 |
|------|---------|---------|---------|
| ... | ... | ... | ... |

### 3.2 间距规范
| 元素 | Padding | Margin | Gap |
|------|---------|--------|-----|
| ... | ... | ... | ... |

## 4. 组件清单

### 4.1 按钮组件
- **类型**: 主按钮 / 次按钮 / 文本按钮
- **尺寸**: 大 / 中 / 小
- **状态**: 默认 / 悬停 / 激活 / 禁用
- **样式**: （颜色、圆角、阴影等）

### 4.2 输入框组件
...

## 5. 交互逻辑

### 5.1 交互流程图
```mermaid
graph TD
    A[首页] -->|点击登录| B[登录页]
    B -->|登录成功| C[用户中心]
    B -->|登录失败| D[错误提示]
```

### 5.2 交互说明
| 触发器 | 事件 | 目标 | 动画 |
|--------|------|------|------|
| ... | ... | ... | ... |

## 6. 设计令牌

### 6.1 颜色
```css
:root {{
  --primary: #3B82F6;
  --secondary: #10B981;
  --text: #1F2937;
  --background: #FFFFFF;
}}
```

### 6.2 字体
```css
:root {{
  --font-family: 'Inter', sans-serif;
  --font-size-base: 16px;
  --line-height: 1.5;
}}
```

### 6.3 间距
```css
:root {{
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
}}
```

## 7. 响应式策略

### 7.1 断点定义
- **移动端**: < 768px
- **平板**: 768px - 1024px
- **桌面端**: > 1024px

### 7.2 适配规则
| 断点 | 布局变化 | 字体调整 | 间距调整 |
|------|---------|---------|---------|
| ... | ... | ... | ... |

## 8. 实现建议

### 8.1 技术栈
- 框架: React / Vue / Next.js
- 样式: Tailwind CSS
- 状态管理: （如需要）
- 路由: （如需要）

### 8.2 开发优先级
1. 核心布局和组件
2. 交互逻辑
3. 响应式适配
4. 动画和过渡效果

### 8.3 注意事项
- （列出需要特别注意的技术点）

---

**生成时间**: {prompt}
**工具**: Claude Prototype Parser v1.0
"""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text

        except Exception as e:
            print(f"[ERROR] Doc generation failed: {e}")
            raise

    # ==================== Figma API 方法 ====================

    def _extract_figma_file_key(self, url: str) -> str:
        """从 Figma URL 提取 file_key"""
        parts = url.split("/")
        for i, part in enumerate(parts):
            if part in ("file", "proto", "design") and i + 1 < len(parts):
                return parts[i + 1].split("?")[0]
        raise ValueError(f"无法从 URL 提取 Figma file_key: {url}")

    def _fetch_figma_file(self, file_key: str) -> Dict:
        """调用 Figma REST API 获取文件"""
        headers = {"X-Figma-Token": self.figma_token}
        url = f"https://api.figma.com/v1/files/{file_key}"

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def _extract_figma_layout(self, file_data: Dict) -> Dict:
        """从 Figma 文件数据提取布局信息"""
        layout_data = {"containers": [], "components": [], "tokens": {}}

        def traverse_node(node, depth=0):
            layout_info = {
                "name": node.get("name"),
                "type": node.get("type"),
                "depth": depth,
            }

            # 提取布局属性
            if "layoutMode" in node:
                layout_info["layoutMode"] = node["layoutMode"]
                layout_info["itemSpacing"] = node.get("itemSpacing", 0)
                layout_info["paddingLeft"] = node.get("paddingLeft", 0)
                layout_info["paddingRight"] = node.get("paddingRight", 0)
                layout_info["paddingTop"] = node.get("paddingTop", 0)
                layout_info["paddingBottom"] = node.get("paddingBottom", 0)
                layout_info["layoutAlign"] = node.get("layoutAlign")
                layout_info["layoutGrow"] = node.get("layoutGrow", 0)

            # 提取尺寸和位置
            if "absoluteBoundingBox" in node:
                box = node["absoluteBoundingBox"]
                layout_info["position"] = {"x": box["x"], "y": box["y"]}
                layout_info["size"] = {"width": box["width"], "height": box["height"]}

            # 提取约束
            if "constraints" in node:
                layout_info["constraints"] = node["constraints"]

            layout_data["containers"].append(layout_info)

            # 递归子节点
            for child in node.get("children", []):
                traverse_node(child, depth + 1)

        document = file_data.get("document", {})
        for page in document.get("children", []):
            traverse_node(page)

        return layout_data

    def _extract_figma_reactions(self, file_data: Dict) -> List[Dict]:
        """从 Figma 文件数据提取交互逻辑"""
        reactions = []

        def traverse_for_reactions(node):
            if "reactions" in node and node["reactions"]:
                for reaction in node["reactions"]:
                    reactions.append(
                        {
                            "node_name": node.get("name"),
                            "node_id": node.get("id"),
                            "trigger": reaction.get("trigger", {}).get("type"),
                            "actions": [
                                {
                                    "type": action.get("type"),
                                    "destination_id": action.get("destinationId"),
                                    "navigation": action.get("navigation"),
                                    "transition": action.get("transition"),
                                }
                                for action in reaction.get("actions", [])
                            ],
                        }
                    )

            for child in node.get("children", []):
                traverse_for_reactions(child)

        document = file_data.get("document", {})
        for page in document.get("children", []):
            traverse_for_reactions(page)

        return reactions

    # ==================== 工具方法 ====================

    def _get_code_filename(self, framework: str) -> str:
        """获取代码文件名"""
        extensions = {
            "react": "App.jsx",
            "vue": "App.vue",
            "html": "index.html",
            "nextjs": "page.jsx",
        }
        return extensions.get(framework, "App.jsx")

    def _save_text(self, content: str, path: Path):
        """保存文本文件"""
        path.write_text(content, encoding="utf-8")

    def _save_json(self, data, path: Path):
        """保存 JSON 文件"""
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_cookies(self, cookies: List):
        """保存 cookies"""
        self.cookies_file.write_text(
            json.dumps(cookies, ensure_ascii=False), encoding="utf-8"
        )

    def _load_cookies(self) -> Optional[List]:
        """加载 cookies"""
        if self.cookies_file.exists():
            return json.loads(self.cookies_file.read_text(encoding="utf-8"))
        return None


# ==================== CLI 入口 ====================


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="原型解析器 - 将在线原型转换为代码和文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python parser.py https://modao.cc/app/xxx
  python parser.py ./screenshot.png --framework vue
  python parser.py https://figma.com/file/xxx --with-figma-api
  python parser.py https://modao.cc/app/xxx --record-interaction
        """,
    )

    parser.add_argument("source", help="原型 URL 或本地截图路径")
    parser.add_argument(
        "--framework",
        choices=["react", "vue", "html", "nextjs"],
        default="react",
        help="输出框架 (默认: react)",
    )
    parser.add_argument(
        "--record-interaction",
        action="store_true",
        help="启用交互录制",
    )
    parser.add_argument(
        "--output-dir",
        default="./prototype-output",
        help="输出目录 (默认: ./prototype-output)",
    )
    parser.add_argument(
        "--full-page",
        action="store_true",
        default=True,
        help="截取完整页面 (默认: True)",
    )
    parser.add_argument(
        "--with-figma-api",
        action="store_true",
        help="使用 Figma API 增强模式",
    )

    args = parser.parse_args()

    try:
        pp = PrototypeParser()
        result = pp.parse(
            source=args.source,
            framework=args.framework,
            record_interaction=args.record_interaction,
            output_dir=args.output_dir,
            full_page=args.full_page,
            with_figma_api=args.with_figma_api,
        )
        print("\n[DONE] All complete!")
    except KeyboardInterrupt:
        print("\n[STOP] User interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
