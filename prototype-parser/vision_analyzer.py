#!/usr/bin/env python3
"""
AI 视觉分析增强模块
提供更精确的布局间距分析和多轮迭代优化
"""

import base64
import json
from typing import Dict, Optional
import anthropic


class VisionAnalyzer:
    """AI 视觉分析器"""

    def __init__(self, api_key: Optional[str] = None):
        import os
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def analyze_with_grid_overlay(self, screenshot: bytes) -> str:
        """带网格参考线的精确间距分析"""
        image_data = base64.standard_b64encode(screenshot).decode("utf-8")

        prompt = """你是一个专业的 UI 设计分析师。请精确分析这个设计稿的布局间距。

**分析方法**：
1. 将页面划分为 12 列网格（假设页面宽度 1920px，每列 160px）
2. 从上到下逐区域分析
3. 对每个元素，测量其与相邻元素的距离

**输出格式**（JSON）：
```json
{
  "page_width": 1920,
  "page_height": "实际高度",
  "grid": {
    "columns": 12,
    "column_width": 160,
    "gutter": 24
  },
  "sections": [
    {
      "name": "区域名称",
      "y_start": 0,
      "y_end": 80,
      "layout": {
        "type": "flex",
        "direction": "row",
        "justify": "space-between",
        "align": "center",
        "padding": {"top": 16, "right": 24, "bottom": 16, "left": 24},
        "gap": 16
      },
      "children": [
        {
          "name": "元素名称",
          "type": "组件类型",
          "grid_span": 3,
          "width": 480,
          "height": 40,
          "margin": {"top": 0, "right": 0, "bottom": 0, "left": 0}
        }
      ]
    }
  ]
}
```

**精度要求**：
- 所有数值为像素值
- 间距精度 ±2px
- 使用 4px 为基础单位（设计系统常用）
- 如果间距接近 4 的倍数，优先使用 4 的倍数

请开始分析："""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return response.content[0].text

    def analyze_component_details(self, screenshot: bytes) -> str:
        """组件级别的详细分析"""
        image_data = base64.standard_b64encode(screenshot).decode("utf-8")

        prompt = """分析这个设计稿中的所有 UI 组件，提取详细属性。

对每个组件，提取：
1. **类型**: button / input / card / badge / avatar / dropdown / modal / tab / table / ...
2. **变体**: primary / secondary / outline / ghost / ...
3. **尺寸**: sm / md / lg / xl
4. **状态**: default / hover / active / disabled / focus
5. **样式属性**:
   - background-color (HEX)
   - border (width, style, color)
   - border-radius (px)
   - box-shadow (x, y, blur, spread, color)
   - font-size (px)
   - font-weight (number)
   - line-height (number)
   - color (HEX)
   - padding (top, right, bottom, left)
   - width / height (px 或 auto)

**输出格式**（JSON）：
```json
{
  "components": [
    {
      "id": "btn_primary_1",
      "type": "button",
      "variant": "primary",
      "size": "md",
      "state": "default",
      "text": "按钮文字",
      "position": {"x": 100, "y": 200},
      "styles": {
        "backgroundColor": "#3B82F6",
        "border": "none",
        "borderRadius": "8px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "fontSize": "14px",
        "fontWeight": 500,
        "lineHeight": 1.5,
        "color": "#FFFFFF",
        "padding": {"top": 8, "right": 16, "bottom": 8, "left": 16},
        "width": 120,
        "height": 36
      }
    }
  ],
  "design_system": {
    "colors": {
      "primary": "#3B82F6",
      "secondary": "#10B981",
      "danger": "#EF4444",
      "warning": "#F59E0B",
      "text": {"primary": "#1F2937", "secondary": "#6B7280"},
      "background": {"primary": "#FFFFFF", "secondary": "#F9FAFB"}
    },
    "typography": {
      "h1": {"size": "32px", "weight": 700, "lineHeight": 1.2},
      "h2": {"size": "24px", "weight": 600, "lineHeight": 1.3},
      "body": {"size": "16px", "weight": 400, "lineHeight": 1.5},
      "caption": {"size": "12px", "weight": 400, "lineHeight": 1.4}
    },
    "spacing_scale": [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64],
    "border_radius": {"sm": "4px", "md": "8px", "lg": "12px", "full": "9999px"}
  }
}
```

请开始分析："""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return response.content[0].text

    def iterative_refinement(
        self, screenshot: bytes, initial_analysis: str, feedback: str
    ) -> str:
        """迭代优化分析结果"""
        image_data = base64.standard_b64encode(screenshot).decode("utf-8")

        prompt = f"""基于之前的分析结果和用户反馈，优化布局分析。

**之前的分析**：
{initial_analysis}

**用户反馈**：
{feedback}

请根据反馈修正分析结果，输出更新后的完整 JSON。
重点关注用户指出的问题区域。"""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        return response.content[0].text

    def compare_pages(self, screenshots: list[bytes]) -> str:
        """对比多个页面，提取共同设计模式"""
        contents = []
        for i, screenshot in enumerate(screenshots):
            image_data = base64.standard_b64encode(screenshot).decode("utf-8")
            contents.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data,
                    },
                }
            )

        contents.append(
            {
                "type": "text",
                "text": """对比以上多个页面设计，提取共同的设计模式：

1. **共享组件**: 在多个页面中重复出现的组件
2. **布局模式**: 共同的布局结构（如统一的 Header/Footer）
3. **设计令牌**: 统一的颜色、字体、间距
4. **交互模式**: 共同的交互方式

输出格式（JSON）：
```json
{
  "shared_components": [...],
  "layout_patterns": [...],
  "design_tokens": {...},
  "interaction_patterns": [...]
}
```""",
            }
        )

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": contents}],
        )

        return response.content[0].text
