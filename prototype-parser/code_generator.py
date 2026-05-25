#!/usr/bin/env python3
"""
代码生成增强模块
支持多框架输出和 Tailwind CSS 配置生成
"""

import json
from typing import Dict, List, Optional
import anthropic
import os


class CodeGenerator:
    """代码生成器"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def generate(
        self,
        layout_analysis: str,
        interactions: Optional[List[Dict]],
        framework: str = "react",
        component_library: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        生成完整项目代码

        Args:
            layout_analysis: 布局分析 JSON
            interactions: 交互数据
            framework: 目标框架
            component_library: 组件库 (antd/shadcn/mui/element-plus)

        Returns:
            文件名到代码内容的映射
        """
        files = {}

        # 生成主组件
        main_code = self._generate_main_component(
            layout_analysis, interactions, framework, component_library
        )
        files[self._get_main_filename(framework)] = main_code

        # 生成 Tailwind 配置
        tailwind_config = self._generate_tailwind_config(layout_analysis)
        files["tailwind.config.js"] = tailwind_config

        # 生成子组件（如果布局复杂）
        sub_components = self._generate_sub_components(
            layout_analysis, framework, component_library
        )
        files.update(sub_components)

        return files

    def _generate_main_component(
        self,
        layout_analysis: str,
        interactions: Optional[List[Dict]],
        framework: str,
        component_library: Optional[str],
    ) -> str:
        """生成主组件代码"""
        lib_instruction = ""
        if component_library:
            lib_map = {
                "antd": "Ant Design (antd)，使用 Button, Input, Card, Table 等组件",
                "shadcn": "shadcn/ui，使用 Button, Input, Card 等组件",
                "mui": "Material UI (@mui/material)，使用 Button, TextField, Card 等组件",
                "element-plus": "Element Plus，使用 el-button, el-input, el-card 等组件",
            }
            lib_instruction = f"\n6. 使用 {lib_map.get(component_library, component_library)} 组件库"

        interaction_text = ""
        if interactions:
            interaction_text = f"\n\n交互逻辑数据：\n```json\n{json.dumps(interactions, ensure_ascii=False, indent=2)}\n```"

        framework_instructions = {
            "react": """
- 使用 React 函数组件 + Hooks
- 使用 useState/useEffect 管理状态
- 事件处理使用 onClick/onChange 等
- 导出默认组件""",
            "vue": """
- 使用 Vue 3 Composition API (<script setup>)
- 使用 ref/reactive 管理状态
- 事件处理使用 @click/@change 等
- 模板使用 <template> 标签""",
            "html": """
- 纯 HTML + Tailwind CSS
- 使用 Alpine.js 处理交互（如果有）
- 包含完整的 <!DOCTYPE html> 结构
- 通过 CDN 引入 Tailwind""",
            "nextjs": """
- 使用 Next.js App Router
- 文件顶部添加 'use client' 指令（如果有交互）
- 使用 React 函数组件 + Hooks
- 支持 Server Components（纯展示部分）""",
        }

        prompt = f"""基于以下布局分析，生成 {framework} 代码：

布局分析：
{layout_analysis}
{interaction_text}

**框架要求**：
{framework_instructions.get(framework, framework_instructions['react'])}

**通用要求**：
1. 使用 Tailwind CSS 实现所有样式
2. 组件化设计，复杂区域拆分为子组件
3. 响应式布局（sm/md/lg/xl 断点）
4. 语义化 HTML 标签
5. 可访问性（ARIA 属性）{lib_instruction}

**代码质量**：
- 变量命名清晰有意义
- 组件职责单一
- 避免硬编码的魔法数字
- 使用 Tailwind 的设计令牌（如 space-4 而非 16px）

直接输出完整代码，不要解释："""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=16384,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _generate_tailwind_config(self, layout_analysis: str) -> str:
        """生成 Tailwind 配置"""
        prompt = f"""基于以下设计分析，生成 tailwind.config.js 配置文件：

{layout_analysis}

要求：
1. 提取设计令牌（颜色、字体、间距）
2. 配置自定义主题
3. 包含常用插件
4. 配置 content 路径

直接输出 tailwind.config.js 代码："""

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _generate_sub_components(
        self,
        layout_analysis: str,
        framework: str,
        component_library: Optional[str],
    ) -> Dict[str, str]:
        """生成子组件"""
        prompt = f"""基于以下布局分析，判断是否需要拆分子组件。

{layout_analysis}

如果需要拆分，列出子组件名称和职责（JSON 格式）：
```json
{{
  "components": [
    {{"name": "Header", "responsibility": "顶部导航栏"}},
    {{"name": "Sidebar", "responsibility": "侧边栏菜单"}}
  ]
}}
```

如果不需要拆分（页面简单），返回：
```json
{{"components": []}}
```"""

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        # 解析响应
        try:
            text = response.content[0].text
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0:
                data = json.loads(text[json_start:json_end])
                components = data.get("components", [])
            else:
                components = []
        except (json.JSONDecodeError, IndexError):
            components = []

        # 为每个子组件生成代码
        files = {}
        for comp in components[:5]:  # 最多 5 个子组件
            name = comp["name"]
            responsibility = comp["responsibility"]

            comp_code = self._generate_single_component(
                name, responsibility, layout_analysis, framework, component_library
            )

            ext = "vue" if framework == "vue" else "jsx"
            files[f"components/{name}.{ext}"] = comp_code

        return files

    def _generate_single_component(
        self,
        name: str,
        responsibility: str,
        layout_analysis: str,
        framework: str,
        component_library: Optional[str],
    ) -> str:
        """生成单个子组件"""
        prompt = f"""生成 {framework} 子组件 "{name}"。

职责: {responsibility}

参考布局分析（提取相关部分）：
{layout_analysis[:2000]}

要求：
- 使用 Tailwind CSS
- 组件接收必要的 props
- 包含类型定义（TypeScript 风格注释）
- 响应式设计

直接输出代码："""

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _get_main_filename(self, framework: str) -> str:
        """获取主文件名"""
        filenames = {
            "react": "App.jsx",
            "vue": "App.vue",
            "html": "index.html",
            "nextjs": "page.jsx",
        }
        return filenames.get(framework, "App.jsx")
