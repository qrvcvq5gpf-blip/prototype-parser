# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
import time
import os

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

    # 截取第1页（默认加载页）
    page.screenshot(path=os.path.join(pages_dir, 'page_01_default.png'), full_page=False)
    print('[OK] page 1 captured (default)')

    # 从之前分析的文本列表，用 get_by_text 点击切换
    page_texts = [
        '0展开',
        '1编辑',
        '坐席通话',
        '坐席服务质量',
        '坐席快速工台',
        '采集查询1',
        '采集查询2',
        '采集查询3',
    ]

    for i, text_hint in enumerate(page_texts):
        try:
            locator = page.get_by_text(text_hint, exact=False).first
            locator.click(timeout=5000)
            time.sleep(2)
            page.wait_for_load_state('networkidle', timeout=10000)
            time.sleep(1)

            safe_name = text_hint.replace(' ', '_').replace('/', '_')
            filename = f'page_{i+2:02d}_{safe_name}.png'
            page.screenshot(path=os.path.join(pages_dir, filename), full_page=False)
            print(f'[OK] page {i+2}: {text_hint}')
        except Exception as e:
            print(f'[FAIL] page {i+2} ({text_hint}): {str(e)[:80]}')
            continue

    browser.close()
    print('\nAll pages captured!')

# 列出结果
print('\nCaptured files:')
for f in sorted(os.listdir(pages_dir)):
    size = os.path.getsize(os.path.join(pages_dir, f))
    print(f'  {f} ({size//1024}KB)')
