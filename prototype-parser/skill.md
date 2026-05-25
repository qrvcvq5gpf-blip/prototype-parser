---
name: prototype-parser
description: "解析在线原型（墨刀/Figma/Axure/即时设计等），提取布局间距和交互逻辑，生成代码和技术文档。支持 URL 输入、截图上传、交互录制。输出 React/Vue/HTML 代码及结构化规格文档。"
---

# 原型解析器 (Prototype Parser)

自动解析在线原型工具的设计稿，提取布局、间距、交互逻辑，生成生产级代码和技术文档。

## 适用场景

**使用本技能的情况：**
- 用户需要将墨刀/Figma/Axure/即时设计等原型转换为代码
- 用户提供原型 URL 或截图，要求生成 React/Vue/HTML 代码
- 用户需要提取原型的布局规范、间距数值、交互逻辑
- 用户需要生成技术规格文档（包含组件清单、交互流程图）
- 用户提到"原型转代码"、"解析原型"、"提取交互逻辑"、"墨刀转 React"

**不适用的情况：**
- 用户只是询问如何使用某个原型工具（直接回答即可）
- 用户需要设计原型而非解析原型（使用其他设计工具）
- 用户需要修改已有代码而非从原型生成（直接编辑代码）

## 支持的输入格式

### 1. 在线原型 URL
- **墨刀 (MockingBot)**: `https://modao.cc/app/xxx`
- **Figma**: `https://www.figma.com/file/xxx` 或 `https://www.figma.com/proto/xxx`
- **Axure RP**: 发布后的原型链接
- **即时设计 (JiShi)**: `https://js.design/f/xxx`
- **蓝湖 (Lanhu)**: `https://lanhuapp.com/xxx`
- **MasterGo**: `https://mastergo.com/file/xxx`
- **其他工具**: 任何可通过浏览器访问的原型链接

### 2. 本地截图
- 支持格式: PNG, JPG, JPEG, WebP
- 建议分辨率: 1920x1080 或更高
- 可上传多张截图（用于多页面原型）

### 3. Figma 文件（增强模式）
- 提供 Figma 文件 Key 和 Access Token
- 可精确提取布局属性和交互逻辑

## 输出内容

### 1. 代码生成
- **React + Tailwind CSS** (默认)
- **Vue 3 + Tailwind CSS**
- **HTML + Tailwind CSS**
- **Next.js + Tailwind CSS**

代码特点：
- 组件化设计，可复用
- 响应式布局
- 包含交互逻辑（如果启用录制）
- 清晰的代码注释

### 2. 技术规格文档
包含以下章节：
- **页面结构**: 整体布局层级描述
- **布局规范**: padding/margin/gap 数值表
- **组件清单**: 所有组件及其属性
- **交互逻辑**: Mermaid 流程图
- **设计令牌**: 颜色/字体/间距变量
- **响应式策略**: 断点和适配规则

### 3. 交互流程图
- Mermaid 格式的交互流程图
- 可视化页面跳转和事件触发

## 使用方式

### 基础用法
```
/prototype-parser <URL或截图路径>
```

### 高级选项
```
/prototype-parser <输入> --framework react --record-interaction --output-dir ./output
```

**可用选项：**
- `--framework <react|vue|html|nextjs>`: 输出框架（默认 react）
- `--record-interaction`: 启用交互录制（需要浏览器操作）
- `--output-dir <路径>`: 输出目录（默认 ./prototype-output）
- `--full-page`: 截取完整页面（默认仅可视区域）
- `--with-figma-api`: 使用 Figma API 增强模式（需提供 token）

## 工作流程

### 模式 A：URL 输入（推荐）
1. **截图采集**: 使用 Playwright 自动打开原型链接并截图
2. **交互录制**（可选）: 在浏览器中手动操作，录制点击/跳转事件
3. **AI 视觉分析**: Claude Opus 4.6 分析布局、间距、组件
4. **代码生成**: 基于分析结果生成目标框架代码
5. **文档生成**: 生成结构化技术规格文档

### 模式 B：截图输入
1. **加载图片**: 读取本地截图文件
2. **AI 视觉分析**: 同上
3. **代码生成**: 同上
4. **文档生成**: 同上（无交互逻辑部分）

### 模式 C：Figma API 增强
1. **API 调用**: 通过 Figma REST API 获取文件结构
2. **精确提取**: 提取 Auto Layout、Reactions、Variables
3. **代码生成**: 基于精确数据生成代码
4. **文档生成**: 包含完整交互逻辑

## 技术实现

### 核心依赖
- **Playwright**: 浏览器自动化（截图、交互录制）
- **Anthropic SDK**: Claude Opus 4.6 视觉分析
- **Requests**: HTTP 请求（Figma API）
- **Pillow**: 图片处理

### AI 分析能力
使用 Claude Opus 4.6 的视觉理解能力：
- 识别布局层级（Flexbox/Grid）
- 测量间距数值（padding/margin）
- 识别组件类型（按钮/输入框/卡片）
- 提取颜色和字体
- 推断响应式断点

### 交互录制原理
通过 Playwright 的 CDP (Chrome DevTools Protocol) 监听：
- 点击事件及目标元素
- 页面导航和 URL 变化
- 表单提交和输入
- 动画和转场效果

## 示例

### 示例 1：解析墨刀原型
```
/prototype-parser https://modao.cc/app/abc123 --framework react --record-interaction
```

输出：
- `output/App.jsx` - React 组件代码
- `output/styles.css` - Tailwind 配置
- `output/spec.md` - 技术规格文档
- `output/interactions.json` - 交互录制数据

### 示例 2：截图转代码
```
/prototype-parser ./design-screenshot.png --framework vue
```

输出：
- `output/App.vue` - Vue 组件代码
- `output/spec.md` - 技术规格文档

### 示例 3：Figma 增强模式
```
/prototype-parser https://www.figma.com/file/abc123 --with-figma-api --framework nextjs
```

需要提供：
- Figma Access Token（通过环境变量 `FIGMA_ACCESS_TOKEN`）

## 注意事项

### 1. 需要登录的原型
部分原型工具（如墨刀）可能需要登录才能访问。首次使用时：
- 工具会打开浏览器窗口
- 请手动完成登录
- Cookies 会被保存供后续使用

### 2. 交互录制时长
启用 `--record-interaction` 后：
- 浏览器会保持打开 30 秒
- 请在此期间完成原型操作
- 所有点击和跳转会被自动记录

### 3. 布局精度
- **URL/截图模式**: AI 推断，精度约 90-95%
- **Figma API 模式**: 像素级精确
- 建议人工校验关键间距数值

### 4. 复杂交互
以下交互可能需要手动补充：
- 复杂动画（如 Lottie）
- 条件逻辑（if/else 分支）
- 数据绑定和状态管理
- 第三方 API 调用

## 环境配置

### 必需
```bash
pip install playwright anthropic pillow requests
playwright install chromium
```

### 可选（Figma API）
设置环境变量：
```bash
export FIGMA_ACCESS_TOKEN="your_token_here"
```

获取 Figma Token：
1. 访问 https://www.figma.com/developers/api#access-tokens
2. 生成 Personal Access Token
3. 保存到环境变量

## 常见问题

**Q: 支持哪些原型工具？**
A: 理论上支持所有可通过浏览器访问的原型工具。已测试：墨刀、Figma、Axure、即时设计、蓝湖、MasterGo。

**Q: 生成的代码质量如何？**
A: 基础布局和样式准确率 90%+，复杂交互需人工补充。建议作为起点快速搭建，再手动优化。

**Q: 可以批量处理多个页面吗？**
A: 可以。提供多个 URL 或截图路径，工具会依次处理并生成独立文件。

**Q: 如何提高间距精度？**
A: 使用 Figma API 模式可获得像素级精度。URL/截图模式建议提供高分辨率图片。

**Q: 支持暗色模式吗？**
A: 如果原型包含暗色模式设计，AI 会尝试识别并生成对应的 CSS 变量。

## 更新日志

### v1.1.0 (2026-05-25) - 实战优化版
- 修复 Windows GBK 编码导致 print 崩溃的问题（强制 UTF-8 stdout）
- 新增原型工具自动检测（墨刀/Figma/即时设计/Axure/蓝湖/MasterGo）
- 新增多页面自动逐页截取（坐标点击方式，兼容各工具 DOM 结构）
- 优化 AI 分析 prompt：自动添加"忽略工具 UI 框架"提示
- 修复 networkidle 后动态内容未渲染的问题（增加 extra_wait）
- 修复 Playwright 中 SVG 元素无 innerText 导致的报错
- 修复左侧面板同坐标多层 DOM 导致重复截图的问题（y 坐标去重）
- 去除 print 中的 emoji 字符（Windows 兼容）

### v1.0.0 (2026-05-25)
- 支持 URL 和截图输入
- 集成 Claude Opus 4.6 视觉分析
- 支持 React/Vue/HTML 代码生成
- 交互录制功能（Playwright）
- 技术规格文档生成
- Figma API 增强模式

## 已知坑点（实测总结）

### 1. Windows 编码问题
Python 在 Windows 下默认 stdout 编码为 GBK，print 含中文或 emoji 会崩溃。
**解决**：文件头部强制 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")`

### 2. 墨刀 DOM 结构特殊
- `get_by_text()` 对墨刀侧栏列表不可靠（文本被多层嵌套）
- 同一 y 坐标有 3 层 DOM 元素（`rn-content-item` / `rn-list-item` / `editable-name`）
**解决**：使用坐标点击 + y 坐标去重（±5px 视为同一项）

### 3. networkidle 不够
Playwright 的 `wait_until="networkidle"` 只等网络请求结束，不等 JS 渲染完成。
**解决**：额外 `time.sleep(3-4)` 等待动态内容

### 4. 原型工具 UI 干扰截图
截图会包含工具自身的侧栏、工具栏、登录横幅等。
**解决**：在 AI 分析 prompt 中明确指示忽略哪些区域

### 5. 登录态问题
墨刀分享链接无需登录即可查看，但会弹出"欢迎登录"横幅。
需要登录的原型需要切换到 headless=False 让用户手动登录。
**解决**：检测 URL 中的 login/auth 关键词，自动切换模式

### 6. page.evaluate 中的 JS 陷阱
- SVG 元素没有 `click()` 方法（需要用 `dispatchEvent`）
- `el.className` 在 SVG 元素上返回 SVGAnimatedString 而非 string
**解决**：JS 中用 `try-catch` 包裹，`className?.toString()` 安全转换

## 反馈与改进

如遇到问题或有改进建议，请：
1. 检查输入格式是否正确
2. 查看生成的日志文件 `output/debug.log`
3. 提供原型链接或截图以便复现问题
