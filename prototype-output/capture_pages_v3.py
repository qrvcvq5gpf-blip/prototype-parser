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
    print('✅ 第1页截取完成（默认页面）')

    # 从之前的分析知道左侧有页面列表
    # 通过文本定位器依次点击
    page_texts = [
        '质检报告 0',      # 第1个
        '质检报告 1',      # 第2个
        '坐席通话',        # 第3个
        '坐席服务质量',    # 第4个
        '坐席快速工台',    # 第5个
        '采集查询1',       # 第6个
        '采集查询2',       # 第7个
        '采集查询3',       # 第8个
    ]

    # 先尝试用 locator 来点击
    for i, text_hint in enumerate(page_texts):
        try:
            # 使用 text locator
            locator = page.get_by_text(text_hint, exact=False).first
            if locator.is_visible(timeout=3000):
                locator.click()
                time.sleep(2)
                page.wait_for_load_state('networkidle', timeout=10000)
                time.sleep(1)

                filename = f'page_{i+2:02d}_{text_hint.replace(" ", "_")}.png'
                page.screenshot(path=os.path.join(pages_dir, filename), full_page=False)
                print(f'✅ 第{i+2}页截取: {text_hint}')
            else:
                print(f'⚠️  未找到: {text_hint}')
        except Exception as e:
            print(f'❌ 第{i+2}页失败({text_hint}): {str(e)[:60]}')
            continue

    browser.close()
    print('\n截取完成！')

# 列出结果
print('\n截取的文件:')
for f in sorted(os.listdir(pages_dir)):
    size = os.path.getsize(os.path.join(pages_dir, f))
    print(f'  {f} ({size//1024}KB)')
