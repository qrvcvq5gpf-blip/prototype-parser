# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import base64
import json
import anthropic

# 配置
clean_dir = r'D:\Claude code\prototype-output\pages_clean'
output_dir = r'D:\Claude code\prototype-output\result'
os.makedirs(output_dir, exist_ok=True)

client = anthropic.Anthropic()

# 选取第1页和第6页分析（质检报告 + 坐席申诉 两种典型页面）
pages_to_analyze = [
    ('page_01_质检报告_展开.png', '智能质检-质检报告(展开状态)'),
    ('page_06_坐席申诉_成绩查询1.png', '智能质检-坐席申诉-成绩查询'),
]

for filename, page_name in pages_to_analyze:
    filepath = os.path.join(clean_dir, filename)
    print(f'\n{"="*60}')
    print(f'Analyzing: {page_name}')
    print(f'{"="*60}')

    with open(filepath, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    # ============ Step 1: 布局分析 ============
    print('\n[1/3] AI Layout Analysis...')

    layout_prompt = """分析这个中石化智能质检系统的设计稿，提取以下信息（JSON格式）：

注意：这是墨刀原型工具的预览界面，左侧是页面列表（可忽略），中间白色区域是实际原型内容。请只分析中间的原型内容部分。

1. **布局结构**：
   - 容器层级（从外到内）
   - 布局方式（Flexbox/Grid）
   - 主轴和交叉轴方向

2. **间距规范**（精确数值，单位px，基于4px基础单位）：
   - 各区域的 padding
   - 元素间的 margin/gap
   - 列间距、行间距

3. **组件清单**：
   - 类型（表格/按钮/输入框/标签/面包屑等）
   - 位置和尺寸
   - 语义标注

4. **设计令牌**：
   - 颜色（主色/辅色/文本色/背景色，HEX值）
   - 字体（字号/行高/字重）
   - 圆角/阴影

5. **数据结构推断**：
   - 表格列定义
   - 表单字段

输出严格JSON格式。"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                {"type": "text", "text": layout_prompt}
            ]
        }]
    )

    layout_analysis = response.content[0].text
    layout_file = os.path.join(output_dir, f'{filename.replace(".png", "")}_layout.json')
    with open(layout_file, 'w', encoding='utf-8') as f:
        f.write(layout_analysis)
    print(f'  Saved: {layout_file}')

    # ============ Step 2: 代码生成 ============
    print('[2/3] Generating React code...')

    code_prompt = f"""基于以下布局分析，生成 React + Tailwind CSS 代码。

布局分析：
{layout_analysis}

要求：
1. 使用 React 函数组件 + Hooks
2. 使用 Tailwind CSS（不要内联样式）
3. 使用 Ant Design (antd) 组件库的 Table, Button, Input, Select, DatePicker 等
4. 组件化设计
5. 包含模拟数据(mock data)
6. 响应式布局
7. 中文界面

直接输出完整可运行的 React 代码（包含 import 语句）："""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16384,
        messages=[{"role": "user", "content": code_prompt}]
    )

    code = response.content[0].text
    code_file = os.path.join(output_dir, f'{filename.replace(".png", "")}_App.jsx')
    with open(code_file, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f'  Saved: {code_file}')

    # ============ Step 3: 技术文档 ============
    print('[3/3] Generating spec document...')

    doc_prompt = f"""基于以下布局分析，生成技术规格文档（Markdown格式）。

布局分析：
{layout_analysis}

页面名称：{page_name}

文档结构：
# {page_name} - 技术规格文档

## 1. 页面概述
## 2. 页面结构（树状图）
## 3. 布局规范（间距表格）
## 4. 组件清单
## 5. 交互逻辑（Mermaid流程图）
## 6. 设计令牌（CSS变量）
## 7. 响应式策略
## 8. 实现建议

生成完整文档："""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": doc_prompt}]
    )

    doc = response.content[0].text
    doc_file = os.path.join(output_dir, f'{filename.replace(".png", "")}_spec.md')
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(doc)
    print(f'  Saved: {doc_file}')

print(f'\n\nAll done! Results in: {output_dir}')
print('\nGenerated files:')
for f in sorted(os.listdir(output_dir)):
    size = os.path.getsize(os.path.join(output_dir, f)) // 1024
    print(f'  {f} ({size}KB)')
