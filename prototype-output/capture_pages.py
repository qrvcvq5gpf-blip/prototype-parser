from playwright.sync_api import sync_playwright
import time
import os
import json

url = 'https://modao.cc/proto/fAF286wtte8zivDczzAk3p/sharing?view_mode=device'
output = r'D:\Claude code\prototype-output'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()

    page.goto(url, wait_until='networkidle', timeout=30000)
    time.sleep(3)

    # 找到所有页面项（左侧列表）
    screen_items = page.query_selector_all('[class*="screen"]')
    print(f'找到 screen 相关元素: {len(screen_items)}')

    # 获取左侧页面列表中可点击的项
    clickable_items = page.evaluate("""
        () => {
            // 找到左侧页面列表
            const items = document.querySelectorAll('[class*="screen"]');
            const result = [];
            for (const item of items) {
                const text = item.innerText?.trim();
                if (text && text.length > 2 && text.length < 100 && !result.some(r => r.text === text)) {
                    const rect = item.getBoundingClientRect();
                    if (rect.width > 50 && rect.width < 400 && rect.height > 20 && rect.height < 100) {
                        result.push({
                            text: text.replace(/\\n/g, ' '),
                            class: item.className?.toString()?.substring(0, 60),
                            rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height}
                        });
                    }
                }
            }
            return result;
        }
    """)

    print(f'\n可点击页面项: {len(clickable_items)}')
    for item in clickable_items[:10]:
        print(f'  - {item["text"][:40]} | class: {item["class"][:40]}')

    # 先截取当前可视的原型内容（不含墨刀 UI 边框）
    # 尝试找到原型画布区域
    canvas_info = page.evaluate("""
        () => {
            // 墨刀的原型预览区域
            const canvas = document.querySelector('[class*="canvas"]') ||
                          document.querySelector('[class*="artboard"]') ||
                          document.querySelector('[class*="prototype-view"]') ||
                          document.querySelector('.preview-content-container');
            if (canvas) {
                const rect = canvas.getBoundingClientRect();
                return {
                    found: true,
                    class: canvas.className?.toString()?.substring(0, 80),
                    rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height}
                };
            }

            // 查找 iframe 内的原型内容
            return {found: false};
        }
    """)

    print(f'\n画布区域: {json.dumps(canvas_info, ensure_ascii=False)}')

    # 截取每个页面（点击左侧列表项切换页面）
    # 先截取第一页
    pages_dir = os.path.join(output, 'pages')
    os.makedirs(pages_dir, exist_ok=True)

    # 截取当前页面（第1页）
    page.screenshot(path=os.path.join(pages_dir, 'page_01_overview.png'), full_page=False)
    print('\n已截取第1页')

    # 点击左侧列表中的每一项，截取对应页面
    for i, item in enumerate(clickable_items[:8]):  # 最多截取前8页
        try:
            # 点击对应元素
            selector = f'[class*="screen"]'
            elements = page.query_selector_all(selector)
            for el in elements:
                text = el.inner_text().strip()
                if item['text'][:20] in text:
                    el.click()
                    time.sleep(2)
                    page.wait_for_load_state('networkidle', timeout=10000)
                    time.sleep(1)

                    # 截图
                    filename = f'page_{i+1:02d}_{item["text"][:20].replace(" ", "_").replace("/", "_")}.png'
                    page.screenshot(path=os.path.join(pages_dir, filename), full_page=False)
                    print(f'已截取第{i+1}页: {item["text"][:30]}')
                    break
        except Exception as e:
            print(f'第{i+1}页截取失败: {e}')
            continue

    browser.close()
    print('\n全部截取完成！')
