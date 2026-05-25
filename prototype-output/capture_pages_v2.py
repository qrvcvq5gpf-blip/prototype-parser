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
    time.sleep(3)

    # 使用 JavaScript 获取所有 screen id 和名称
    screen_data = page.evaluate("""
        () => {
            // 查找所有 screen 列表项
            const items = document.querySelectorAll('[class*="screen-name"], [class*="page-name"]');
            const result = [];
            for (const item of items) {
                const text = item.textContent?.trim();
                if (text) result.push(text);
            }

            // 如果上面没找到，尝试从当前 URL 推断
            const currentUrl = window.location.href;
            const screenMatch = currentUrl.match(/screen=([^&]+)/);
            const canvasMatch = currentUrl.match(/canvasId=([^&]+)/);

            return {
                page_names: result,
                current_screen: screenMatch ? screenMatch[1] : null,
                current_canvas: canvasMatch ? canvasMatch[1] : null,
                current_url: currentUrl
            };
        }
    """)

    print(f'页面信息: {json.dumps(screen_data, ensure_ascii=False, indent=2)}')

    # 尝试点击左侧列表展开所有页面
    # 先看看有没有折叠的组
    page.evaluate("""
        () => {
            // 点击所有展开按钮
            const expandBtns = document.querySelectorAll('[class*="expand"], [class*="toggle"], [class*="arrow"]');
            for (const btn of expandBtns) {
                btn.click();
            }
        }
    """)
    time.sleep(1)

    # 使用更通用的方式：获取左侧面板中所有可点击元素
    all_screen_links = page.evaluate("""
        () => {
            const result = [];
            // 查找左侧面板中的所有 div/span 带有文本的
            const panel = document.querySelector('[class*="panel"], [class*="sidebar"], [class*="page-list"]');
            const container = panel || document.body;

            const allElements = container.querySelectorAll('div, span, li, a');
            for (const el of allElements) {
                const text = el.textContent?.trim();
                const rect = el.getBoundingClientRect();
                // 左侧面板中的元素（x < 300）且大小合适
                if (text && text.length > 3 && text.length < 50 &&
                    rect.x < 300 && rect.width > 50 && rect.width < 300 &&
                    rect.height > 15 && rect.height < 60 &&
                    !result.some(r => r.text === text)) {
                    result.push({
                        text: text,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height),
                        tag: el.tagName
                    });
                }
            }
            return result.sort((a, b) => a.y - b.y);
        }
    """)

    print(f'\n左侧面板元素 ({len(all_screen_links)}个):')
    for item in all_screen_links[:20]:
        print(f'  [{item["y"]:4d}px] {item["text"][:40]}')

    # 通过坐标点击每个页面项并截图
    page_names = []
    for i, item in enumerate(all_screen_links):
        # 只处理看起来像页面名称的项
        text = item['text']
        if '质检' in text or '报告' in text or '采集' in text or '坐席' in text or '通话' in text or '速览' in text:
            page_names.append(item)

    print(f'\n识别到原型页面: {len(page_names)}个')
    for item in page_names:
        print(f'  - {item["text"]}')

    # 逐个点击并截图
    for i, item in enumerate(page_names[:8]):
        try:
            # 通过坐标点击
            page.mouse.click(item['x'] + item['w'] // 2, item['y'] + item['h'] // 2)
            time.sleep(2)
            page.wait_for_load_state('networkidle', timeout=10000)
            time.sleep(1)

            # 截图
            safe_name = item['text'][:25].replace(' ', '_').replace('/', '_').replace('-', '_')
            filename = f'page_{i+1:02d}_{safe_name}.png'
            page.screenshot(path=os.path.join(pages_dir, filename), full_page=False)
            print(f'✅ 截取第{i+1}页: {item["text"][:30]}')
        except Exception as e:
            print(f'❌ 第{i+1}页失败: {e}')
            continue

    browser.close()
    print('\n截取完成！')
