#!/usr/bin/env python3
"""
多页面批量处理模块
支持批量解析多个原型页面，生成统一的项目代码
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from parser import PrototypeParser


class BatchParser:
    """批量原型解析器"""

    def __init__(self, api_key: Optional[str] = None):
        self.parser = PrototypeParser(api_key=api_key)

    def parse_batch(
        self,
        sources: List[str],
        framework: str = "react",
        output_dir: str = "./prototype-output",
        record_interaction: bool = False,
    ) -> Dict:
        """
        批量解析多个原型页面

        Args:
            sources: URL 或截图路径列表
            framework: 目标框架
            output_dir: 输出目录
            record_interaction: 是否录制交互

        Returns:
            包含所有页面解析结果的字典
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []
        all_interactions = []

        for i, source in enumerate(sources):
            page_name = f"page_{i + 1}"
            page_output = output_path / page_name
            page_output.mkdir(parents=True, exist_ok=True)

            print(f"\n{'='*50}")
            print(f"📄 处理第 {i + 1}/{len(sources)} 页: {source}")
            print(f"{'='*50}")

            result = self.parser.parse(
                source=source,
                framework=framework,
                record_interaction=record_interaction,
                output_dir=str(page_output),
            )

            result["page_name"] = page_name
            result["source"] = source
            results.append(result)

            if result.get("interactions"):
                all_interactions.extend(result["interactions"])

        # 生成项目级文件
        print(f"\n{'='*50}")
        print("📦 生成项目级文件...")
        print(f"{'='*50}")

        # 生成路由配置
        router_code = self._generate_router(results, framework)
        router_file = "router.jsx" if framework in ("react", "nextjs") else "router.js"
        (output_path / router_file).write_text(router_code, encoding="utf-8")

        # 生成全局交互流程图
        flow_doc = self._generate_flow_diagram(results, all_interactions)
        (output_path / "flow.md").write_text(flow_doc, encoding="utf-8")

        # 生成项目概览文档
        overview = self._generate_overview(results)
        (output_path / "README.md").write_text(overview, encoding="utf-8")

        print(f"\n✅ 批量处理完成！共处理 {len(sources)} 个页面")
        print(f"📁 输出目录: {output_path.absolute()}")

        return {
            "pages": results,
            "router": router_code,
            "flow": flow_doc,
            "overview": overview,
        }

    def _generate_router(self, results: List[Dict], framework: str) -> str:
        """生成路由配置"""
        if framework in ("react", "nextjs"):
            routes = []
            for r in results:
                page_name = r["page_name"]
                routes.append(
                    f'  {{ path: "/{page_name}", element: <{page_name.title().replace("_", "")} /> }}'
                )

            return f"""import React from 'react';
import {{ BrowserRouter, Routes, Route }} from 'react-router-dom';

// 页面组件导入
{chr(10).join(f"import {r['page_name'].title().replace('_', '')} from './{r['page_name']}/App';" for r in results)}

function AppRouter() {{
  return (
    <BrowserRouter>
      <Routes>
{chr(10).join(f'        <Route path="/{r["page_name"]}" element={{<{r["page_name"].title().replace("_", "")} />}} />' for r in results)}
      </Routes>
    </BrowserRouter>
  );
}}

export default AppRouter;
"""
        elif framework == "vue":
            return f"""import {{ createRouter, createWebHistory }} from 'vue-router';

const routes = [
{chr(10).join(f"  {{ path: '/{r['page_name']}', component: () => import('./{r['page_name']}/App.vue') }}," for r in results)}
];

const router = createRouter({{
  history: createWebHistory(),
  routes,
}});

export default router;
"""
        else:
            return "<!-- 多页面 HTML 无需路由配置 -->"

    def _generate_flow_diagram(
        self, results: List[Dict], interactions: List[Dict]
    ) -> str:
        """生成全局交互流程图"""
        mermaid_nodes = []
        mermaid_edges = []

        for i, r in enumerate(results):
            node_id = f"P{i + 1}"
            mermaid_nodes.append(f"    {node_id}[{r['page_name']}]")

        for interaction in interactions:
            if interaction.get("type") == "navigate":
                mermaid_edges.append(
                    f"    P1 -->|navigate| P2"
                )

        return f"""# 全局交互流程图

## 页面关系

```mermaid
graph TD
{chr(10).join(mermaid_nodes)}
{chr(10).join(mermaid_edges)}
```

## 页面清单

| 序号 | 页面名称 | 来源 |
|------|---------|------|
{chr(10).join(f"| {i+1} | {r['page_name']} | {r['source']} |" for i, r in enumerate(results))}

## 交互事件汇总

共记录 {len(interactions)} 个交互事件。

详细交互数据请查看各页面目录下的 `interactions.json` 文件。
"""

    def _generate_overview(self, results: List[Dict]) -> str:
        """生成项目概览"""
        return f"""# 原型解析项目

## 概述

本项目由 Prototype Parser 自动生成，包含 {len(results)} 个页面。

## 目录结构

```
prototype-output/
├── README.md          # 项目概览（本文件）
├── flow.md            # 全局交互流程图
├── router.jsx         # 路由配置
{chr(10).join(f"├── {r['page_name']}/" for r in results)}
│   ├── App.jsx        # 页面代码
│   ├── spec.md        # 技术规格文档
│   └── interactions.json  # 交互数据
```

## 快速开始

```bash
# 安装依赖
npm install react react-dom react-router-dom tailwindcss

# 启动开发服务器
npm run dev
```

## 页面列表

{chr(10).join(f"### {i+1}. {r['page_name']}" + chr(10) + f"- 来源: {r['source']}" for i, r in enumerate(results))}

## 注意事项

- 生成的代码为初始版本，建议人工审核后再投入使用
- 间距数值基于 AI 视觉推断，可能存在 ±2px 误差
- 交互逻辑仅包含录制期间的操作，复杂逻辑需手动补充
"""


def main():
    """批量处理 CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="批量原型解析器")
    parser.add_argument("sources", nargs="+", help="原型 URL 或截图路径列表")
    parser.add_argument("--framework", default="react", help="输出框架")
    parser.add_argument("--output-dir", default="./prototype-output", help="输出目录")
    parser.add_argument("--record-interaction", action="store_true", help="录制交互")

    args = parser.parse_args()

    batch = BatchParser()
    batch.parse_batch(
        sources=args.sources,
        framework=args.framework,
        output_dir=args.output_dir,
        record_interaction=args.record_interaction,
    )


if __name__ == "__main__":
    main()
