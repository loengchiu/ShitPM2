---
name: spm-prototype
description: "Prototype 生成与修改：根据 Design 事实闭包创建或更新可运行的 Vite + React 18 + Ant Design 6 源码原型。触发于生成原型或修改原型；评审原型使用 spm-prototype-review；源码工程缺失时停止。"
---

## 运行前提

从系统 prompt 读取 `ShitPM bundle root:`，记为 `$BUNDLE`。项目文件使用当前项目根目录；规则、模板和脚本使用 `$BUNDLE/`。流程开始时给出一次模型建议：跨页面任务、复杂交互或高影响表达使用深度推理模型；只有明确的结构或格式检查才使用轻量模型；无法判断时使用深度推理模型。

Prototype 直接下游于 Design：

- 设计地图、设计集清单和目标模块 Design 事实闭包是唯一产品事实输入；PRD 只能辅助发现表达差异，冲突时以 Design 为准。
- `output/prototype/src/` 是唯一编辑源；`dist/` 只由 `npm run build` 生成，不能作为产品事实或编辑入口。
- 工程使用标准 Vite + React 18 + Ant Design 6；依赖由 `package.json` 和 `package-lock.json` 管理，安装使用 `npm ci`。
- 用户入口只有 `output/prototype/原型工具.bat`；它调用 `package.json` 的 `dev`、`build`、`preview` scripts。
- 页面只表达 Design 已定义的字段、状态、权限、流程、异常和责任边界，不补写高影响事实。

## 每次任务先读取

按以下顺序读取，且每一步完成后再进入下一步：

1. 运行 `python $BUNDLE/scripts/python/stage-context.py --project-root .`。**完成条件**：确认 Design 清单可读，且 `design_change.active` 不为 `true`；有活动事务先恢复或停止。
2. 读取目标模块的 Design 事实闭包和现有 `output/prototype/`。**完成条件**：能列出本次必须表达的页面、字段、状态、角色权限、主路径、关键反馈和待确认项。
3. 读取 `$BUNDLE/references/prototype-visual-spec.md`。**完成条件**：已为每个页面选择 7 类骨架之一，并知道所需共享 UI、状态矩阵和响应式要求。
4. 读取 `$BUNDLE/references/prototype-writing.md`；只有多页面 shell、导航、路由或空白页任务才读取 `$BUNDLE/references/prototype-shell.md`。**完成条件**：已确定组件 API、源码目录、路由登记和构建边界。
5. 读取 `$BUNDLE/references/prototype-component-behavior.md`。**完成条件**：已明确每个高频组件的默认行为、场景边界和禁止事项（页面标题层级、Sider 滚动条、表格固定列、操作列 ≤3、卡片间距、主按钮唯一等），并确认页面写法不与其中任何一条冲突。
6. 如存在 `output/prototype/prototype-feedback.md`，读取并按 `$BUNDLE/templates/prototype-feedback-classification.md` 先归类。**完成条件**：每条反馈已分成表现问题、语义问题或待澄清项。

缺少规则、模板、Design 输入或无法解析时，报告具体路径并停止；不凭记忆补写产品事实。

## 首次生成

1. 检查 `$BUNDLE/templates/prototype-vite/` 完整。将模板复制到 `output/prototype/`；若目标是旧静态 HTML + compiled.js 原型，先报告迁移边界并等待确认，不直接覆盖。**完成条件**：目标包含 `package.json`、`src/`、入口、路由表和 `原型工具.bat`。
2. 先完成 Design → Prototype 语义对照，再在 `src/modules/<模块>/` 创建页面并在 `src/routes.jsx` 登记；共享 shell、角色区、异常页放在 `src/shared/`。**完成条件**：Design 页面与路由逐项对应，未确认事实没有被静默拍板。
3. 先按视觉规范选择页面骨架，再组合 `src/shared/ui/`、`src/shared/icons/` 和 `src/shared/charts/`，最后填入 Design 字段和状态。新颜色、间距、字号、圆角或阴影先按视觉规范 1.8 进入 Token，不在页面现场拍值。**完成条件**：页面没有复制一套局部视觉规则，且高频结构来自共享 UI。
4. 只编辑 `src/`、`index.html`、`package.json`、`vite.config.js`、`public/`、README 等源码工程文件；不编辑 `dist/`、`node_modules/` 或带哈希资源。**完成条件**：所有业务改动都能在源码中定位。
5. 在 `output/prototype/` 执行 `npm ci` 和 `npm run build`。**完成条件**：构建成功，且没有用旧 `dist/` 冒充新版本。

## 修改已有原型

1. 先运行 `prototype-source-check.py`，确认 `package.json`、`src/`、入口、build script 和业务页面都存在。**完成条件**：源码检查通过；只有 dist/compiled.js 时停止并报告“Prototype 源码工程缺失”。
2. 从 `src/routes.jsx` 和 `src/modules/` 定位受影响页面，只改源码；语义问题先回到 Design/Fix，表现问题只改 Prototype。**完成条件**：变更范围与反馈分类一致，没有混改业务事实。
3. 运行开发预览观察修改，再用 `npm run build` 生成构建产物并复验构建预览。**完成条件**：开发预览与构建预览都能打开默认页和全部注册路由。

## 统一验证与完成判据

生成或修改完成前，按以下顺序自修并验证：

1. 检查默认页和每个注册路由均可渲染，浏览器 console 无错误；页面、字段、状态、角色、权限、主路径和关键反馈与 Design 一致。
2. 检查加载、空数据、失败/重试、无权限、禁用/只读、选中和响应式状态可通过 UI 观察；列表/看板保留空态，配置操作使用真实 `Modal` + `Form`，状态机限制使用 `disabled`。
3. 检查页面没有“入口：”“（只读）”“（必填）”等解释性标注代替真实 UI 状态；图标统一使用 Tabler，图表使用 `TablerChart`。
4. 逐条核对 `prototype-component-behavior.md` 第 10 节验收清单：主标题唯一、Sider 独立滚动且细滚动条可见、表格默认不固定列、操作列 ≤3（多余收进“更多”下拉）、卡片间距、每视图一个 primary、状态用 `TablerStatusTag`。
4. 运行：

```text
python $BUNDLE/scripts/python/prototype-source-check.py --project-root .
python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root . --module <模块名>
```

**完成条件**：源码检查、构建、路由/浏览器验证和针对性一致性检查均通过；任何未验证项都已明确报告。随后更新 `.workflow/status.json` 的 `current_stage=prototype` 和 Prototype 产物路径，并按实际读取的 Design 文件记录 `design-set.py record-inputs`。

## 反馈分类与停止条件

- **表现问题**：布局、视觉层级、间距、颜色、字体、响应式或组件呈现；只改 Prototype。
- **语义问题**：字段、状态、权限、流程、异常、责任边界或模块缺失/冲突；停止静默修改，转入 Design/Fix。
- **待澄清项**：用户反馈无法判断属于哪一类；停止并请求澄清。

发现幻觉页面、字段、状态、权限或未授权高影响行为时，删除未授权表达并报告；发现活动 Design 事务、清单不可读、源码工程缺失、构建失败、白屏或 console 错误时，停止交付并给出具体原因。

Review 使用 `spm-prototype-review`，不会由本 Skill 自动修复或推进。

## 产物

- `output/prototype/src/`：源码编辑源。
- `output/prototype/原型工具.bat`：用户操作入口。
- `output/prototype/index.html`、`package.json`、`package-lock.json`、`vite.config.js`、README：工程文件。
- `output/prototype/dist/`：可重建构建产物。
- `.workflow/status.json`：阶段与产物导航状态。
