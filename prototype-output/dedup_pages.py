# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import shutil

pages_dir = r'D:\Claude code\prototype-output\pages'
clean_dir = r'D:\Claude code\prototype-output\pages_clean'
os.makedirs(clean_dir, exist_ok=True)

# 保留每个独立页面的一张截图
unique_pages = {
    'page_01': 'page_01_default.png',
    'page_02': 'page_04_2智能质检-质检报告_1收起.png',
    'page_03': 'page_07_3智能质检-质检报告_2坐席抢插话.png',
    'page_04': 'page_10_4智能质检-质检报告_3坐席音量过高.png',
    'page_05': 'page_13_5智能质检-质检报告_4坐席语速过快.png',
    'page_06': 'page_16_6智能质检-坐席申诉-成绩查询1.png',
    'page_07': 'page_19_7智能质检-坐席申诉-成绩查询2.png',
    'page_08': 'page_22_8智能质检-坐席申诉-成绩查询3.png',
}

page_names = {
    'page_01': '质检报告_展开',
    'page_02': '质检报告_收起',
    'page_03': '质检报告_坐席抢插话',
    'page_04': '质检报告_坐席音量过高',
    'page_05': '质检报告_坐席语速过快',
    'page_06': '坐席申诉_成绩查询1',
    'page_07': '坐席申诉_成绩查询2',
    'page_08': '坐席申诉_成绩查询3',
}

for key, src_file in unique_pages.items():
    src = os.path.join(pages_dir, src_file)
    name = page_names[key]
    dst = os.path.join(clean_dir, f'{key}_{name}.png')
    if os.path.exists(src):
        shutil.copy2(src, dst)
        size = os.path.getsize(dst) // 1024
        print(f'[OK] {key}: {name} ({size}KB)')
    else:
        print(f'[MISS] {src_file}')

print(f'\nClean pages saved to: {clean_dir}')
print(f'Total: {len(os.listdir(clean_dir))} files')
