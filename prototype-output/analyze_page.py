from playwright.sync_api import sync_playwright
import time
import json

url = 'https://modao.cc/proto/fAF286wtte8zivDczzAk3p/sharing?view_mode=device'
output = r'D:\Claude code\prototype-output'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()

    page.goto(url, wait_until='networkidle', timeout=30000)
    time.sleep(3)

    # 获取左侧页面列表
    page_items = page.query_selector_all('[class*="screen"], [class*="page-item"], [class*="list-item"]')
    print(f'找到页面项: {len(page_items)}')

    # 获取所有链接
    all_links = page.query_selector_all('a')
    modao_links = []
    for link in all_links:
        href = link.get_attribute('href') or ''
        text = link.inner_text().strip()
        if text and len(text) < 100:
            modao_links.append({'text': text, 'href': href})

    print(f'所有链接数: {len(modao_links)}')
    for item in modao_links[:20]:
        print(f'  - {item["text"][:50]} -> {item["href"][:80]}')

    # 检查 iframe
    frames = page.frames
    print(f'\niframe 数量: {len(frames)}')
    for frame in frames:
        print(f'  - {frame.url[:100]}')

    # 获取页面 HTML 结构概览
    html_structure = page.evaluate("""
        () => {
            const body = document.body;
            function getStructure(el, depth) {
                if (depth > 3) return null;
                const result = {
                    tag: el.tagName,
                    class: el.className?.toString()?.substring(0, 80) || '',
                    id: el.id || '',
                    children_count: el.children.length
                };
                return result;
            }

            const main = document.querySelector('[class*="canvas"], [class*="prototype"], [class*="artboard"], [class*="content"]');
            if (main) {
                return {
                    found: true,
                    tag: main.tagName,
                    class: main.className?.toString()?.substring(0, 100),
                    rect: main.getBoundingClientRect()
                };
            }

            // 尝试找到主内容区域
            const divs = document.querySelectorAll('div');
            const large_divs = [];
            for (const div of divs) {
                const rect = div.getBoundingClientRect();
                if (rect.width > 500 && rect.height > 500) {
                    large_divs.push({
                        class: div.className?.toString()?.substring(0, 80),
                        rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height}
                    });
                }
            }
            return {found: false, large_divs: large_divs.slice(0, 10)};
        }
    """)

    print(f'\n页面结构分析:')
    print(json.dumps(html_structure, indent=2, ensure_ascii=False))

    browser.close()
