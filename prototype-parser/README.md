# Prototype Parser

在线原型解析器 - 将墨刀/Figma/Axure/即时设计等原型自动转换为代码和技术文档。

## 快速开始

### 1. 安装依赖

```bash
cd ~/.claude/skills/prototype-parser
python run.py setup
```

或手动安装：

```bash
pip install anthropic playwright Pillow requests
playwright install chromium
```

### 2. 配置环境变量

```bash
# 必需
set ANTHROPIC_API_KEY=your_key_here

# 可选（Figma API 增强模式）
set FIGMA_ACCESS_TOKEN=your_token_here
```

### 3. 使用

```bash
# 解析墨刀原型
python run.py parse https://modao.cc/app/xxx

# 解析截图
python run.py parse ./design.png --framework vue

# 带交互录制
python run.py parse https://modao.cc/app/xxx --record-interaction

# 使用组件库
python run.py parse ./design.png --component-library antd

# Figma API 精确模式
python run.py parse https://www.figma.com/file/xxx --with-figma-api

# 增强分析（更精确的间距测量）
python run.py parse ./design.png --enhanced

# 批量处理
python batch_parser.py https://url1 https://url2 ./screenshot.png
```

## 文件说明

```
prototype-parser/
├── skill.md                 # Skill 定义（Claude Code 识别）
├── parser.py               # 核心解析逻辑（截图+AI分析+生成）
├── vision_analyzer.py      # AI 视觉分析增强（精确间距+组件详情）
├── interaction_recorder.py # 交互录制增强（事件捕获+自动探索）
├── code_generator.py       # 代码生成增强（多框架+组件库）
├── doc_generator.py        # 文档生成增强（规格+流程图+交接文档）
├── batch_parser.py         # 批量处理（多页面+路由生成）
├── run.py                  # 快速入口（一键调用）
├── requirements.txt        # Python 依赖
└── README.md               # 本文件
```

## 支持的原型工具

| 工具 | URL 支持 | 截图支持 | API 增强 |
|------|---------|---------|---------|
| 墨刀 (MockingBot) | ✅ | ✅ | ❌ |
| Figma | ✅ | ✅ | ✅ |
| Axure RP | ✅ | ✅ | ❌ |
| 即时设计 (JiShi) | ✅ | ✅ | ❌ |
| 蓝湖 (Lanhu) | ✅ | ✅ | ❌ |
| MasterGo | ✅ | ✅ | ❌ |
| 其他 | ✅ | ✅ | ❌ |

## 输出框架

| 框架 | 选项值 | 输出文件 |
|------|--------|---------|
| React + Tailwind | `react` | App.jsx |
| Vue 3 + Tailwind | `vue` | App.vue |
| HTML + Tailwind | `html` | index.html |
| Next.js + Tailwind | `nextjs` | page.jsx |

## 组件库支持

| 组件库 | 选项值 | 适用框架 |
|--------|--------|---------|
| Ant Design | `antd` | React |
| shadcn/ui | `shadcn` | React/Next.js |
| Material UI | `mui` | React |
| Element Plus | `element-plus` | Vue |

## 工作流程

```
输入 (URL/截图)
    ↓
┌─────────────────┐
│ Playwright 截图  │ ← URL 输入时自动执行
│ (支持登录态保持) │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Claude Opus 4.6 │ ← AI 视觉分析
│ 布局+间距+组件  │
└────────┬────────┘
         ↓
┌────────┴────────┐
↓                 ↓
代码生成          文档生成
(多框架)         (规格+流程图)
```

## 注意事项

1. **需要登录的原型**：首次访问时会弹出浏览器窗口，手动登录后 cookies 自动保存
2. **交互录制**：启用后浏览器保持打开 30 秒，请在此期间操作原型
3. **布局精度**：AI 推断精度约 90-95%，建议人工校验关键数值
4. **API 费用**：每次解析约消耗 $0.05-0.20 的 Claude API 费用

## 迭代优化方向

- [ ] 支持多页面自动探索（无需手动操作）
- [ ] 接入更多原型工具 API（墨刀、即时设计）
- [ ] 支持 Design Token 标准格式导出
- [ ] 增加对比模式（设计稿 vs 生成代码截图）
- [ ] 支持增量更新（只更新变化的部分）
