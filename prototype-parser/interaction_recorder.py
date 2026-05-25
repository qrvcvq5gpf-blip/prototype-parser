#!/usr/bin/env python3
"""
交互录制增强模块
支持更丰富的交互事件捕获和分析
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext


class InteractionRecorder:
    """交互录制器"""

    def __init__(self):
        self.interactions: List[Dict] = []
        self.page_screenshots: List[Dict] = []

    def record(
        self,
        url: str,
        duration: int = 30,
        cookies: Optional[List] = None,
        auto_explore: bool = False,
    ) -> Dict:
        """
        录制交互逻辑

        Args:
            url: 原型 URL
            duration: 录制时长（秒）
            cookies: 登录 cookies
            auto_explore: 是否自动探索（点击所有可交互元素）

        Returns:
            交互数据字典
        """
        self.interactions = []
        self.page_screenshots = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=None,
            )

            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()

            # 注入交互监听脚本
            self._inject_listeners(page)

            # 监听页面事件
            self._setup_page_listeners(page, context)

            page.goto(url, wait_until="networkidle")

            # 截取初始状态
            self._capture_state(page, "initial")

            if auto_explore:
                print("🤖 自动探索模式启动...")
                self._auto_explore(page, duration)
            else:
                print(f"👆 请在浏览器中操作原型（{duration}秒后自动结束）...")
                page.wait_for_timeout(duration * 1000)

            # 获取 JS 层记录的交互
            js_data = page.evaluate("window.__protoRecorder?.getData() || {}")
            if js_data:
                self.interactions.extend(js_data.get("events", []))

            browser.close()

        return {
            "url": url,
            "duration": duration,
            "events": self.interactions,
            "screenshots": self.page_screenshots,
            "summary": self._generate_summary(),
        }

    def _inject_listeners(self, page: Page):
        """注入交互监听脚本"""
        page.add_init_script("""
            window.__protoRecorder = {
                events: [],
                startTime: Date.now(),

                record(event) {
                    this.events.push({
                        ...event,
                        timestamp: Date.now() - this.startTime
                    });
                },

                getData() {
                    return { events: this.events };
                }
            };

            // 监听点击
            document.addEventListener('click', (e) => {
                const target = e.target;
                const rect = target.getBoundingClientRect();
                window.__protoRecorder.record({
                    type: 'click',
                    target: {
                        tagName: target.tagName,
                        id: target.id,
                        className: target.className,
                        text: target.innerText?.substring(0, 100),
                        href: target.href || target.closest('a')?.href,
                        role: target.getAttribute('role'),
                        ariaLabel: target.getAttribute('aria-label'),
                    },
                    position: {
                        x: Math.round(rect.left + rect.width / 2),
                        y: Math.round(rect.top + rect.height / 2)
                    },
                    elementRect: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                });
            }, true);

            // 监听输入
            document.addEventListener('input', (e) => {
                const target = e.target;
                window.__protoRecorder.record({
                    type: 'input',
                    target: {
                        tagName: target.tagName,
                        id: target.id,
                        name: target.name,
                        placeholder: target.placeholder,
                        type: target.type,
                    },
                    value: target.value?.substring(0, 50)
                });
            }, true);

            // 监听滚动
            let scrollTimer;
            document.addEventListener('scroll', (e) => {
                clearTimeout(scrollTimer);
                scrollTimer = setTimeout(() => {
                    window.__protoRecorder.record({
                        type: 'scroll',
                        scrollTop: window.scrollY,
                        scrollLeft: window.scrollX,
                        target: e.target === document ? 'window' : e.target.className
                    });
                }, 200);
            }, true);

            // 监听悬停（仅记录有交互效果的悬停）
            document.addEventListener('mouseenter', (e) => {
                const target = e.target;
                const style = window.getComputedStyle(target);
                if (style.cursor === 'pointer' || target.closest('[data-hover]')) {
                    window.__protoRecorder.record({
                        type: 'hover',
                        target: {
                            tagName: target.tagName,
                            id: target.id,
                            className: target.className,
                        }
                    });
                }
            }, true);

            // 监听表单提交
            document.addEventListener('submit', (e) => {
                window.__protoRecorder.record({
                    type: 'form_submit',
                    target: {
                        id: e.target.id,
                        action: e.target.action,
                        method: e.target.method,
                    }
                });
            }, true);

            // 监听键盘事件（仅快捷键）
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey || e.metaKey || e.altKey || e.key === 'Escape' || e.key === 'Enter') {
                    window.__protoRecorder.record({
                        type: 'keyboard',
                        key: e.key,
                        modifiers: {
                            ctrl: e.ctrlKey,
                            meta: e.metaKey,
                            alt: e.altKey,
                            shift: e.shiftKey
                        }
                    });
                }
            }, true);
        """)

    def _setup_page_listeners(self, page: Page, context: BrowserContext):
        """设置页面级事件监听"""

        def on_navigate(frame):
            if frame == page.main_frame:
                self.interactions.append(
                    {
                        "type": "page_navigate",
                        "url": frame.url,
                        "timestamp": int(time.time() * 1000),
                    }
                )

        def on_popup(popup_page):
            self.interactions.append(
                {
                    "type": "popup",
                    "url": popup_page.url,
                    "timestamp": int(time.time() * 1000),
                }
            )

        def on_dialog(dialog):
            self.interactions.append(
                {
                    "type": "dialog",
                    "dialog_type": dialog.type,
                    "message": dialog.message,
                    "timestamp": int(time.time() * 1000),
                }
            )
            dialog.dismiss()

        page.on("framenavigated", on_navigate)
        page.on("popup", on_popup)
        page.on("dialog", on_dialog)

    def _auto_explore(self, page: Page, duration: int):
        """自动探索模式：自动点击所有可交互元素"""
        start_time = time.time()
        visited_urls = set()
        visited_urls.add(page.url)

        while time.time() - start_time < duration:
            # 查找所有可点击元素
            clickable = page.query_selector_all(
                "a, button, [role='button'], [onclick], [data-action], "
                "input[type='submit'], .clickable, [cursor='pointer']"
            )

            for element in clickable:
                if time.time() - start_time >= duration:
                    break

                try:
                    # 截图当前状态
                    self._capture_state(page, f"before_click_{len(self.page_screenshots)}")

                    # 点击元素
                    element.click(timeout=3000)
                    page.wait_for_timeout(1000)

                    # 检查是否跳转到新页面
                    if page.url not in visited_urls:
                        visited_urls.add(page.url)
                        self._capture_state(page, f"new_page_{page.url}")

                        # 返回上一页继续探索
                        page.go_back()
                        page.wait_for_timeout(500)

                except Exception:
                    continue

            # 如果没有更多可点击元素，结束
            break

    def _capture_state(self, page: Page, label: str):
        """截取当前页面状态"""
        try:
            screenshot = page.screenshot()
            self.page_screenshots.append(
                {
                    "label": label,
                    "url": page.url,
                    "timestamp": int(time.time() * 1000),
                    "screenshot_size": len(screenshot),
                }
            )
        except Exception:
            pass

    def _generate_summary(self) -> Dict:
        """生成交互摘要"""
        event_types = {}
        for event in self.interactions:
            event_type = event.get("type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        pages_visited = set()
        for event in self.interactions:
            if event.get("type") == "page_navigate":
                pages_visited.add(event.get("url"))

        return {
            "total_events": len(self.interactions),
            "event_types": event_types,
            "pages_visited": list(pages_visited),
            "screenshots_taken": len(self.page_screenshots),
        }


def main():
    """交互录制 CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="原型交互录制器")
    parser.add_argument("url", help="原型 URL")
    parser.add_argument("--duration", type=int, default=30, help="录制时长（秒）")
    parser.add_argument("--auto-explore", action="store_true", help="自动探索模式")
    parser.add_argument("--output", default="interactions.json", help="输出文件")

    args = parser.parse_args()

    recorder = InteractionRecorder()
    result = recorder.record(
        url=args.url,
        duration=args.duration,
        auto_explore=args.auto_explore,
    )

    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n📊 录制摘要:")
    print(f"   总事件数: {result['summary']['total_events']}")
    print(f"   事件类型: {result['summary']['event_types']}")
    print(f"   访问页面: {len(result['summary']['pages_visited'])}")
    print(f"   输出文件: {args.output}")


if __name__ == "__main__":
    main()
