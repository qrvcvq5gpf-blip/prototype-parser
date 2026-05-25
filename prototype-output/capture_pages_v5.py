# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
import time
import os
import json

url = 'https://modao.cc/proto/fAF286wtte8zivDczzAk3p/sharing?view_mode=device'
output = r'D:\Claude code\prototype-output'
pages_dir = os.path.join(output, 'pages')
os.makedirs(pages_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()

    page.goto(url, wait_until='networkidle', timeout=30000)
    time.sleep(4)

    # 获取完整的 DOM 结构来分析左侧面板
    left_panel_info = page.evaluate("""
        () => {
            const allEls = document.querySelectorAll('*');
            const leftItems = [];
            for (const el of allEls) {
                const rect = el.getBoundingClientRect();
                // 左侧面板区域(x < 250), 且是合适大小的元素
                if (rect.x >= 0 && rect.x < 250 && rect.width > 100 && rect.width < 260 &&
                    rect.height > 20 && rect.height < 50 && rect.y > 400) {
                    const text = el.textContent?.trim();
                    const directText = el.childNodes.length <= 3 ? el.textContent?.trim() : '';
                    if (directText && directText.length > 2 && directText.length < 80) {
                        // 避免重复
                        if (!leftItems.some(item => Math.abs(item.y - rect.y) < 5)) {
                            leftItems.push({
                                text: directText.substring(0, 50),
                                x: Math.round(rect.x + rect.width / 2),
                                y: Math.round(rect.y + rect.height / 2),
                                w: Math.round(rect.width),
                                h: Math.round(rect.height),
                                tag: el.tagName,
                                cls: (el.className?.toString() || '').substring(0, 50)
                            });
                        }
                    }
                }
            }
            return leftItems.sort((a, b) => a.y - b.y);
        }
    """)

    print(f'Left panel items ({len(left_panel_info)}):')
    for item in left_panel_info:
        print(f'  y={item["y"]:4d} | {item["text"][:40]} | {item["cls"][:30]}')

    # 点击每一项并截图
    captured = 0
    for i, item in enumerate(left_panel_info):
        text = item['text']
        # 过滤掉不是页面名称的项
        if len(text) < 3:
            continue

        try:
            page.mouse.click(item['x'], item['y'])
            time.sleep(2)
            page.wait_for_load_state('networkidle', timeout=8000)
            time.sleep(1)

            captured += 1
            safe_name = text[:20].replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f'page_{captured:02d}_{safe_name}.png'
            page.screenshot(path=os.path.join(pages_dir, filename), full_page=False)
            print(f'[OK] page {captured}: {text[:30]}')
        except Exception as e:
            print(f'[FAIL] ({text[:20]}): {str(e)[:60]}')
            continue

    browser.close()

print(f'\nTotal captured: {captured} pages')
print('\nCaptured files:')
for f in sorted(os.listdir(pages_dir)):
    if f.startswith('page_'):
        size = os.path.getsize(os.path.join(pages_dir, f))
        print(f'  {f} ({size//1024}KB)')
