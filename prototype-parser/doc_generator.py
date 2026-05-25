#!/usr/bin/env python3
"""
文档生成增强模块
生成结构化技术规格文档和交互流程图
"""

import json
from typing import Dict, List, Optional
import anthropic
import os


class DocGenerator:
    """文档生成器"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def generate_spec(
        self,
        layout_analysis: str,
        interactions: Optional[List[Dict]],
        page_name: str = "页面",
    ) -> str:
        """生成技术规格文档"""
        interaction_text = ""
        if interactions:
            interaction_text = f"\n\n交互数据：\n```json\n{json.dumps(interactions[:50], ensure_ascii=False, indent=2)}\n```"

        prompt = f"""基于以下分析数据，生成完整的技术规格文档。

布局分析：
{layout_analysis}
{interaction_text}

**文档要求**：
- 使用 Markdown 格式
- 包含 Mermaid 流程图（交互逻辑）
- 间距数值使用表格展示
- 组件清单包含所有属性
- 设计令牌使用 CSS 变量格式

**文档结构**：

# {page_name} - 技术规格文档

## 1. 页面概述
（功能描述、目标用户、核心场景）

## 2. 页面结构
（树状结构图 + 说明）

## 3. 布局规范
### 3.1 整体布局
（Flexbox/Grid 配置）
### 3.2 间距规范表
（表格：元素 | padding | margin | gap）
### 3.3 尺寸规范
（表格：元素 | width | height | min/max）

## 4. 组件清单
### 4.1 [组件名]
- 类型/变体/尺寸/状态
- 样式属性
- 交互行为

## 5. 交互逻辑
### 5.1 交互流程图（Mermaid）
### 5.2 事件清单表
### 5.3 状态管理

## 6. 设计令牌
### 6.1 颜色系统
### 6.2 字体系统
### 6.3 间距系统
### 6.4 圆角和阴影

## 7. 响应式策略
### 7.1 断点定义
### 7.2 各断点布局变化

## 8. 实现建议
### 8.1 推荐技术栈
### 8.2 开发优先级
### 8.3 注意事项

请生成完整文档："""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=12288,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def generate_interaction_flow(self, interactions: List[Dict]) -> str:
        """生成交互流程文档"""
        if not interactions:
            return "# 交互流程\n\n暂无交互数据。请使用 `--record-interaction` 选项录制交互。"

        prompt = f"""基于以下交互录制数据，生成交互流程文档。

交互数据：
```json
{json.dumps(interactions[:100], ensure_ascii=False, indent=2)}
```

**要求**：
1. 生成 Mermaid 流程图（graph TD 格式）
2. 列出所有交互事件表
3. 标注页面跳转关系
4. 识别交互模式（如表单提交流程、导航流程）

**输出格式**：

# 交互流程文档

## 1. 交互流程图

```mermaid
graph TD
    A[页面A] -->|点击按钮| B[页面B]
    ...
```

## 2. 事件清单

| 序号 | 事件类型 | 触发元素 | 目标/效果 | 时间戳 |
|------|---------|---------|----------|--------|
| 1 | click | 登录按钮 | 跳转登录页 | 0ms |
| ... | ... | ... | ... | ... |

## 3. 页面跳转关系

| 起始页 | 目标页 | 触发条件 |
|--------|--------|---------|
| ... | ... | ... |

## 4. 交互模式分析

### 4.1 [模式名称]
- 触发条件
- 执行步骤
- 预期结果

请生成文档："""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def generate_component_api_doc(self, layout_analysis: str) -> str:
        """生成组件 API 文档"""
        prompt = f"""基于以下布局分析，为识别出的组件生成 API 文档。

{layout_analysis}

**文档格式**（每个组件）：

### ComponentName

**描述**: 一句话描述

**Props**:
| 属性 | 类型 | 默认值 | 必填 | 说明 |
|------|------|--------|------|------|
| variant | 'primary' \\| 'secondary' | 'primary' | 否 | 按钮变体 |

**事件**:
| 事件名 | 参数 | 说明 |
|--------|------|------|
| onClick | event: MouseEvent | 点击回调 |

**示例**:
```jsx
<ComponentName variant="primary" onClick={{handleClick}}>
  按钮文字
</ComponentName>
```

请为所有识别出的组件生成 API 文档："""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def generate_handoff_doc(
        self,
        layout_analysis: str,
        interactions: Optional[List[Dict]],
        code_files: Dict[str, str],
    ) -> str:
        """生成设计-开发交接文档"""
        code_summary = "\n".join(
            f"- `{name}`: {len(content)} 字符" for name, content in code_files.items()
        )

        interaction_summary = ""
        if interactions:
            interaction_summary = f"共 {len(interactions)} 个交互事件"

        prompt = f"""生成设计-开发交接文档。

布局分析：
{layout_analysis[:3000]}

交互概况：{interaction_summary}

已生成代码文件：
{code_summary}

**文档结构**：

# 设计-开发交接文档

## 1. 设计意图
（设计师想要表达什么）

## 2. 关键设计决策
（为什么这样设计，有哪些约束）

## 3. 开发注意事项
### 3.1 必须精确还原的部分
（间距、颜色、字体等关键数值）
### 3.2 可以灵活处理的部分
（动画细节、边缘情况等）

## 4. 已知限制
（AI 分析可能不准确的地方）

## 5. 验收标准
（如何判断开发完成）

## 6. 后续迭代建议
（可以优化的方向）

请生成文档："""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text
