---
name: spm-prototype
description: "Prototype 生成与修改：根据多文件 Design 事实闭包创建或更新可运行的 Vite + React 18 + Ant Design 6 源码原型。触发于生成原型或修改原型；评审原型使用 spm-prototype-review；源码工程缺失时停止。"
---

## 运行前提

从系统 prompt 读取 `ShitPM bundle root:`，记为 `$BUNDLE`。项目文件使用当前项目根目录；规则、模板和脚本使用 `$BUNDLE/`。流程开始时给出一次模型建议：跨页面任务、复杂交互或高影响表达使用深度推理模型；只有明确的结构或格式检查才使用轻量模型；无法判断时使用深度推理模型。

Prototype 直接下游于 Design 事实闭包：

- 设计地图、设计集清单和目标模块 Design 事实闭包是唯一产品事实输入；PRD 只能辅助发现表达差异，冲突时以 Design 为准。
- `output/prototype/src/` 是唯一编辑源；`dist/` 只由 `npm run build` 生成，不能作为产品事实或编辑入口。
- 工程使用标准 Vite + React 18 + Ant Design 6；依赖由 `package.json` 和 `package-lock.json` 管理，安装使用 `npm ci`。
- 用户入口只有 `output/prototype/原型工具.bat`；它调用 `package.json` 的 `dev`、`build`、`preview` scripts。
- 每次生成前从项目的设计地图、设计集清单和目标 Design 文件读取事实闭包，取代单体 `design.md` 与旧确认哈希流程。
- 生成前选择一套品牌主题：Claude、Tabler 或 traework。一个原型内只使用一套品牌主题；当前模板默认 Tabler，项目组的壳层、交互和代码习惯与品牌主题分离。切换流程见 `references/prototype-writing.md`「品牌主题接入」。
- 页面只表达 Design 已定义的字段、状态、权限、流程、异常和责任边界，不补写高影响事实。

## 每次任务先读取

按以下顺序读取，且每一步完成后再进入下一步：

1. 运行 `python $BUNDLE/scripts/python/stage-context.py --project-root .`。**完成条件**：确认 Design 清单可读，且 `design_change.active` 不为 `true`；有活动事务先恢复或停止。
2. 读取设计地图、设计集清单、目标模块的 Design 事实闭包和现有 `output/prototype/`。**完成条件**：能列出本次必须表达的页面、字段、状态、角色权限、主路径、关键反馈和待确认项。
3. 读取 `$BUNDLE/references/prototype-visual-spec.md`。**完成条件**：已为每个页面选择 7 类骨架之一，并知道所需共享 UI、状态矩阵和响应式要求。
4. 读取 `$BUNDLE/references/prototype-writing.md`；只有多页面 shell、导航、路由或空白页任务才读取 `$BUNDLE/references/prototype-shell.md`。**完成条件**：已确定组件 API、源码目录、路由登记和构建边界。
5. 生成或修改页头、区块卡片、指标卡、工具栏、数据表格、状态、空态、图标按钮、行操作、表单分区和页面操作栏前，先读取当前模板 `src/shared/ui/` 的真实导出和目标组件实现。命中现有共享组件时直接复用，不在页面内复制它已经承担的 DOM、CSS 或默认行为；共享组件无法表达已确认 Design 要求时，允许组合 Ant Design 原生组件或页面特有结构，并说明回退原因。
6. 仅在命中以下场景时读取 `$BUNDLE/references/prototype-component-behavior.md` 的对应章节：固定列、复杂表格、超过默认数量的行操作、自定义分页或空态，读取表格与操作边界；Form、普通 Modal、确认弹窗、回填、提交、重置或页面外 ActionBar，读取表单与弹层边界；Dropdown、Select、DatePicker、Modal、移动 Sider 或 sticky 层级，读取 Portal 与响应式契约；共享组件无法承接 Design，读取回退规则；新建共享组件或修改共享组件契约，读取完整 behavior 和目标源码调用方。完成条件：根据触发词得到组件选择、回退原因或跨层验收结果，不把 behavior 当作普通任务的必读全文。
7. 如存在 `output/prototype/prototype-feedback.md`，读取并按 `$BUNDLE/templates/prototype-feedback-classification.md` 先归类。**完成条件**：每条反馈已分成表现问题、语义问题或待澄清项。

缺少规则、模板、Design 输入或无法解析时，报告具体路径并停止；不凭记忆补写产品事实。

## 首次生成

1. 检查 `$BUNDLE/templates/prototype-vite/` 完整。目标目录不存在或为空时，将模板复制到 `output/prototype/`；目标目录已存在且非空、但不同时具备 `package.json` 与 `src/` 时，先报告迁移边界并等待确认，不直接覆盖。**完成条件**：目标包含 `package.json`、`src/`、入口、路由表和 `原型工具.bat`。
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

1. 用真实浏览器打开默认页和每个注册路由，检查浏览器 console 无错误；对项目实际存在的关键交互至少各操作一次，包括 Modal、Form、Select、角色切换和响应式状态。没有对应场景时明确记录“模板/项目无此场景”，不能用静态检查代替浏览器验证。
2. 检查加载、空数据、失败/重试、无权限、禁用/只读、选中和响应式状态可通过 UI 观察；列表/看板保留空态，配置操作使用真实 `Modal` + `Form`，状态机限制使用 `disabled`。
3. 检查页面没有“入口：”“（只读）”“（必填）”等解释性标注代替真实 UI 状态；图标统一使用 Tabler，图表使用 `TablerChart`；品牌主题只使用本轮从 Claude、Tabler、traework 中选择的一套，默认 Tabler。
4. 对本任务命中的 behavior 章节逐条核对对应规则；跨任务通用的完成门槛以本 Skill 为准，不通过交付前再次完整读取 behavior 来替代。
5. 运行：

```text
python $BUNDLE/scripts/python/prototype-source-check.py --project-root .
python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root .
```

一致性脚本只提供全量检查，结果必须按三类阅读：`deterministic_conflicts` 是可确定冲突，`possible_omissions` 是需要结合 Design 和源码逐项判断的可能遗漏，`needs_semantic_judgment` 是脚本不能可靠裁决的语义项。只有确定性冲突返回 1；输入或源码工程等致命错误返回 2；返回 0 不代表事实完整、无幻觉或视觉通过。

**完成条件**：构建成功；默认页和全部注册路由可打开；实际存在的关键交互可操作；console 无运行时错误；适用 Portal/响应式场景已用真实浏览器检查；三类一致性结果已逐项处理，未把可能遗漏或语义判断写成自动通过。任何未验证项都已明确报告。随后更新 `.workflow/status.json` 的 `current_stage=prototype` 和 Prototype 产物路径，并按实际读取的 Design 文件记录 `design-set.py record-inputs`。

## 反馈分类与停止条件

- **表现问题**：布局、视觉层级、间距、颜色、字体、响应式或组件呈现；只改 Prototype。
- **语义问题**：字段、状态、权限、流程、异常、责任边界或模块缺失/冲突；停止静默修改，转入 Design/Fix。
- **待澄清项**：用户反馈无法判断属于哪一类；停止并请求澄清。

发现幻觉页面、字段、状态、权限或未授权高影响行为时，删除未授权表达并报告；发现活动 Design 事务、清单不可读、源码工程缺失、构建失败、白屏或 console 错误时，停止交付并给出具体原因。

Review 使用 `spm-prototype-review`，不会由本 Skill 自动修复或推进。

## 标注副本（prototypemark，按需）

仅当用户要求生成带编号角标 + 浮窗的设计/PRD 标注原型时，才读取 `$BUNDLE/references/prototype-mark-injection.md`，把标注系统注入 `output/prototypemark/`（`output/prototype/` 的副本）。该副本不进入 review 链路、不反写 Design/PRD、不生成 metadata；高影响意见按反馈分类转交 `spm-fix`。普通原型任务不读取本文件。

## 产物

- `output/prototype/src/`：源码编辑源。
- `output/prototype/原型工具.bat`：用户操作入口。
- `output/prototype/index.html`、`package.json`、`package-lock.json`、`vite.config.js`、README：工程文件。
- `output/prototype/dist/`：可重建构建产物。
- `.workflow/status.json`：阶段与产物导航状态。
