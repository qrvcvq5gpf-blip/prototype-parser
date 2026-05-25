#!/usr/bin/env python3
"""
原型解析器快速入口
提供简化的 API 调用方式，适合在 Claude Code skill 中使用
"""

import sys
import json
from pathlib import Path
from typing import Optional


def quick_parse(
    source: str,
    framework: str = "react",
    output_dir: str = "./prototype-output",
    record_interaction: bool = False,
    with_figma_api: bool = False,
    component_library: Optional[str] = None,
    enhanced_analysis: bool = False,
):
    """
    快速解析原型（一键调用）

    Args:
        source: URL 或截图路径
        framework: react/vue/html/nextjs
        output_dir: 输出目录
        record_interaction: 是否录制交互
        with_figma_api: 是否使用 Figma API
        component_library: 组件库 (antd/shadcn/mui/element-plus)
        enhanced_analysis: 是否使用增强分析（更精确但更慢）
    """
    from parser import PrototypeParser
    from code_generator import CodeGenerator
    from doc_generator import DocGenerator
    from vision_analyzer import VisionAnalyzer

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 基础解析
    pp = PrototypeParser()
    result = pp.parse(
        source=source,
        framework=framework,
        record_interaction=record_interaction,
        output_dir=output_dir,
        with_figma_api=with_figma_api,
    )

    # 增强分析（可选）
    if enhanced_analysis and not source.startswith("http"):
        print("🔬 执行增强分析...")
        analyzer = VisionAnalyzer()
        with open(source, "rb") as f:
            screenshot = f.read()

        grid_analysis = analyzer.analyze_with_grid_overlay(screenshot)
        (output_path / "grid_analysis.json").write_text(grid_analysis, encoding="utf-8")

        component_details = analyzer.analyze_component_details(screenshot)
        (output_path / "component_details.json").write_text(
            component_details, encoding="utf-8"
        )

    # 使用组件库生成代码（可选）
    if component_library:
        print(f"🎨 使用 {component_library} 组件库重新生成代码...")
        cg = CodeGenerator()
        files = cg.generate(
            layout_analysis=result["layout_analysis"],
            interactions=result.get("interactions"),
            framework=framework,
            component_library=component_library,
        )
        for filename, content in files.items():
            file_path = output_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            print(f"   📄 {filename}")

    # 生成交互流程文档
    if result.get("interactions"):
        print("📊 生成交互流程文档...")
        dg = DocGenerator()
        flow_doc = dg.generate_interaction_flow(result["interactions"])
        (output_path / "interaction_flow.md").write_text(flow_doc, encoding="utf-8")

    print(f"\n🎉 全部完成！输出目录: {output_path.absolute()}")
    return result


def setup_environment():
    """检查并安装依赖"""
    import subprocess

    requirements = ["anthropic", "playwright", "Pillow", "requests"]
    missing = []

    for pkg in requirements:
        try:
            __import__(pkg.lower().replace("-", "_").replace("P", "p"))
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"📦 安装缺失依赖: {', '.join(missing)}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + missing,
            check=True,
            capture_output=True,
        )

    # 安装 Playwright 浏览器
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception:
        print("🌐 安装 Playwright Chromium...")
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
        )

    print("✅ 环境检查通过！")


if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser(description="原型解析器快速入口")
    subparsers = arg_parser.add_subparsers(dest="command")

    # setup 命令
    subparsers.add_parser("setup", help="检查并安装依赖")

    # parse 命令
    parse_cmd = subparsers.add_parser("parse", help="解析原型")
    parse_cmd.add_argument("source", help="URL 或截图路径")
    parse_cmd.add_argument("--framework", default="react", help="目标框架")
    parse_cmd.add_argument("--output-dir", default="./prototype-output", help="输出目录")
    parse_cmd.add_argument("--record-interaction", action="store_true", help="录制交互")
    parse_cmd.add_argument("--with-figma-api", action="store_true", help="Figma API 模式")
    parse_cmd.add_argument("--component-library", help="组件库 (antd/shadcn/mui/element-plus)")
    parse_cmd.add_argument("--enhanced", action="store_true", help="增强分析模式")

    args = arg_parser.parse_args()

    if args.command == "setup":
        setup_environment()
    elif args.command == "parse":
        quick_parse(
            source=args.source,
            framework=args.framework,
            output_dir=args.output_dir,
            record_interaction=args.record_interaction,
            with_figma_api=args.with_figma_api,
            component_library=args.component_library,
            enhanced_analysis=args.enhanced,
        )
    else:
        arg_parser.print_help()
