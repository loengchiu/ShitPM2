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
- 用户入口只有 `output/prototype/原型工具.bat`；它调用 `package.json` 的 `dev`、`build`、`preview` scripts，第 4 项通过 Wrangler 上传 Cloudflare Pages。
- 每次生成前从项目的设计地图、设计集清单和目标 Design 文件读取事实闭包，取代单体 `design.md` 与旧确认哈希流程。
- 视觉口径：结构、尺寸、间距、字体、阴影、控件规格与图标一律按 Ant Design 官方规范（`$BUNDLE/references/design-sources/ant-design-official/`，读法见同目录 `ADAPTATION.md`）；颜色体系沿用 Tabler 主题（`src/theme/tablerTheme.ts`）。页面不承担主题选择或换肤决策；主题文件只保留颜色 token，不得新增非颜色覆盖。
- 页面只表达 Design 已定义的字段、状态、权限、流程、异常和责任边界，不补写高影响事实。

## 每次任务先读取

按以下顺序读取，且每一步完成后再进入下一步：

1. 运行 `python $BUNDLE/scripts/python/stage-context.py --project-root .`。**完成条件**：确认 Design 清单可读，且 `design_change.active` 不为 `true`；有活动事务先恢复或停止。
2. 读取设计地图、设计集清单、目标模块的 Design 事实闭包和现有 `output/prototype/`。**完成条件**：能列出本次必须表达的页面、字段、状态、角色权限、主路径、关键反馈和待确认项。
3. 读取 `$BUNDLE/references/prototype-visual-spec.md`。普通页面直接使用模板提供的主题基础设施和语义 shared/ui；仅在复杂或特殊页面命中对应规则时，读取相关状态矩阵和响应式要求。
4. 读取 `$BUNDLE/references/prototype-writing.md`；只有多页面 shell、导航、路由或空白页任务才读取 `$BUNDLE/references/prototype-shell.md`。**完成条件**：已确定组件 API、源码目录、路由登记和构建边界。
5. 按本 Skill「页面分类与标准结构」路由表判定每个页面的类型，读取 `$BUNDLE/references/prototype-page-types.md` 命中章节；同时读取当前模板 `src/shared/ui/` 的真实导出和目标组件实现。生成或修改页头、区块卡片、指标卡、工具栏、数据表格、状态、空态、图标按钮、行操作、表单分区和页面操作栏时，命中现有共享组件的必须直接复用，不在页面内复制它已经承担的 DOM、CSS 或默认行为；未命中共享组件时允许组合 Ant Design 原生组件或页面特有结构，并说明回退原因。**完成条件**：每个页面都能说明页面类型与结构来源。
6. 只读取本任务命中的章节：页面类型规则在 page-types 命中章节；组件选型与例外、Form/Modal/Drawer/提交重置、Portal 与响应式、跨层运行时契约读 `$BUNDLE/references/prototype-component-behavior.md` §1–§3 对应小节；页面含角色差异时读取 `$BUNDLE/references/prototype-role-permission.md`。新建或修改共享组件契约时读取完整 behavior 和目标源码调用方。**完成条件**：根据页面类型或触发词得到组件选择、权限表达方式或跨层验收结果，不预读未命中的章节。
7. 如存在 `output/prototype/prototype-feedback.md`，读取并按 `$BUNDLE/templates/prototype-feedback-classification.md` 先归类。**完成条件**：每条反馈已分成表现问题、语义问题或待澄清项。

缺少规则、模板、Design 输入或无法解析时，报告具体路径并停止；不凭记忆补写产品事实。

## 页面分类与标准结构

页面结构唯一事实源是 `$BUNDLE/references/prototype-page-types.md`（7 类 + 公共页 + 快照/只读态横切模式，每类含标准结构 / 必须项 / 禁止项 / 官方章节书签 / 锚点约定五段）。尺寸、间距、弹层选型等细节按各页型书签读 `$BUNDLE/references/design-sources/ant-design-official/` 对应章节；组件级选型与跨层契约读 `prototype-component-behavior.md`。

| 页面类型 | 判别 | page-types 章节 | 官方书签 |
| :-- | :-- | :-- | :-- |
| 标准查询表格（筛 ≥5） | 列表页且筛选项 ≥5 | 二 | `components_Table.md` 筛选组件使用规则 / 表格样式规范 / 分页规范 / 表格卡头部表达 |
| 轻量工具栏表格（筛 ≤4） | 列表页且筛选项 ≤4 | 三 | `components_Table.md` 工具栏布局 / 表格卡头部表达 / 卡内顶部 Tab Strip |
| 批量操作表格 | 类 1/2 + 行选择与批量动作 | 四 | `components_Table.md` 批量操作表格 / 工具栏布局 |
| 多步骤长流程表单 | ≥3 步或步骤有先后依赖 | 五 | `components_Form.md` 分步表单选型 / 竖向分步表单 |
| 配置类 / 分组表单 | 单页多分组、无步骤依赖 | 六 | `components_Form.md` 嵌入模式表单 / 输入框宽度规范 / 操作按钮位置 |
| 对象详情页 | 只读呈现单对象 | 七 | `components_DescriptionList.md` 描述列表选型 / 分组卡片描述列表 / 布局规则 |
| 看板页（概览/驾驶舱） | 一屏指标 + 图表汇总 | 八 | `components_Chart.md` + `layout.md` 主内容区规范 |
| 公共页（含任务看板页） | 登录 / 个人中心 / 结果 / 异常 / Kanban | 九 | `components_Form.md` 登录表单 + `layout.md` |

判定规则：

1. 先判类再动手；一类页面只允许一种筛选形态（≥5 独立搜索卡且默认折叠可展开，≤4 单行工具栏）。
2. 命中页型的标准结构 / 必须项 / 禁止项逐条核对；类 2 与类 4 是净新增要求，不得以「存量没有样本」为由省略或降级。
3. 两条存量让路口径不得改回去：空字段一律显示 `—`（不用「未填写」）；表格钉列与横向滚动只修真的会溢出的页。
4. 字段锚点约定：`data-page` / `data-block` / `data-field` / `data-operation` / `data-state` 只写在真实 JSX 标签属性上；antd `columns` 数组对象不是 JSX 标签，不得把锚点写进列配置对象。
5. 视觉入口唯一：`tablerTheme` 只承担颜色；页面与组件不得传 `theme`、不得引入外部样式表、不得写死色值；图标一律经 `src/shared/icons/` 取用。

## shared/ui 复用

现有 11 个语义组件（`PageHeader / SectionCard / MetricCard / Toolbar / DataTable / StatusTag / IconButton / RowActions / FormSection / EmptyState / ActionBar`）全部保留；高频结构命中即复用，不在页面内复制实现，也不新造与它们重复的局部封装。

## 首次生成

1. 检查 `$BUNDLE/templates/prototype-vite/` 完整。目标目录不存在或为空时，将模板复制到 `output/prototype/`；目标目录已存在且非空、但不同时具备 `package.json` 与 `src/` 时，先报告迁移边界并等待确认，不直接覆盖。**复制后立即清掉自带样张**：删除 `src/modules/demo/` 下的 `DesignGallery.jsx`、`DetailDemo.jsx`、`FormDemo.jsx`，以及 `src/routes.jsx` 中对应的 import 与路由登记（`/gallery`、`/detail`、`/form-demo`）；`Placeholder.jsx` 是占位页壳层组件、被真实路由复用，保留原位。**完成条件**：目标包含 `package.json`、`src/`、入口、路由表和 `原型工具.bat`；侧栏不残留样张入口且 `npm run build` 仍通过。
2. 先完成 Design → Prototype 语义对照，再在 `src/modules/<模块>/` 创建页面并在 `src/routes.jsx` 登记；共享 shell、角色区、异常页放在 `src/shared/`。**完成条件**：Design 页面与路由逐项对应，未确认事实没有被静默拍板。
3. 按「页面分类与标准结构」路由表判定页面类型并按对应标准结构落位；组合 `src/shared/ui/`、`src/shared/icons/` 和 `src/shared/charts/`，填入 Design 字段与状态，字段锚点用 `data-field` 写在控件或单元格元素上。新颜色先按视觉规范 1.8 进入 Token，不在页面现场拍值；尺寸、间距、阴影不写死，走官方默认。**完成条件**：页面没有复制一套局部视觉规则，高频结构来自共享 UI，且每个页面都能说明页面类型。
4. 只编辑 `src/`、`index.html`、`package.json`、`vite.config.js`、`public/`、README 等源码工程文件；不编辑 `dist/`、`node_modules/` 或带哈希资源。**完成条件**：所有业务改动都能在源码中定位。
5. 在 `output/prototype/` 执行 `npm ci` 和 `npm run build`。**完成条件**：构建成功，且没有用旧 `dist/` 冒充新版本。

## 修改已有原型

1. 先运行 `prototype-source-check.py`，确认 `package.json`、`src/`、入口、build script 和业务页面都存在。**完成条件**：源码检查通过；只有 dist/compiled.js 时停止并报告“Prototype 源码工程缺失”。
2. 从 `src/routes.jsx` 和 `src/modules/` 定位受影响页面，只改源码；语义问题先回到 Design/Fix，表现问题只改 Prototype。**完成条件**：变更范围与反馈分类一致，没有混改业务事实。
3. 运行开发预览观察修改，再用 `npm run build` 生成构建产物并复验构建预览。**完成条件**：开发预览与构建预览都能打开默认页和全部注册路由。

## 统一验证与完成判据

生成或修改完成前，按以下顺序自修并验证：

1. 用真实浏览器打开默认页和每个注册路由，检查浏览器 console 无错误；对项目实际存在的关键交互至少各操作一次，包括 Modal、Form、Select、角色切换和响应式状态。没有对应场景时明确记录“项目无此场景”，不能用静态检查代替浏览器验证。
2. 检查加载、空数据、失败/重试、无权限、禁用/只读、选中和响应式状态可通过 UI 观察；列表/看板保留空态，配置操作使用真实 `Modal` + `Form`，状态机限制使用 `disabled`。
3. 对照 `$BUNDLE/references/prototype-page-types.md` 命中章节逐条核对标准结构与必须项（含分页与总条数、筛选折叠、卡头徽章、空字段 `—`、长文本省略等让路与新增口径）；页面含角色差异时对照 `$BUNDLE/references/prototype-role-permission.md` §八 核对四级权限表达。图标统一通过 `src/shared/icons/` 取用官方图标，不直接 import 图标库；图表使用 `src/shared/charts/`。
4. 对本任务命中的 page-types、role-permission 与 behavior 章节逐条核对对应规则；跨任务通用的完成门槛以本 Skill 为准，不通过交付前再次完整读取这些文档来替代。响应式按实际命中的断点和场景验收，不执行 390px 专项测试。
5. 运行：

```text
python $BUNDLE/scripts/python/prototype-source-check.py --project-root .
python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root .
```

一致性脚本只提供全量检查，结果必须按三类阅读：`deterministic_conflicts` 是 `red`，直接修正；`possible_omissions` 和 `needs_semantic_judgment` 是 `risk` 的证据，必须结合 Design 和源码逐项判断。高影响未知转为 Design `decision` 或明确报告；只有确定性冲突返回 1，输入或源码工程等致命错误返回 2，返回 0 不代表事实完整、无幻觉或视觉通过。

6. 交付验收：`npm run build` 通过后，可用 `原型工具.bat` 第 4 项上传 Cloudflare Pages；上传后打开线上地址验证默认页、代表路由（列表 / 表单 / 详情类各一）与角色切换可正常使用。不上传时在交付说明中注明未验证线上通路。

**完成条件**：构建成功；默认页和全部注册路由可打开；实际存在的关键交互可操作；console 无运行时错误；适用 Portal/响应式场景已用真实浏览器检查；三类一致性结果已逐项处理，未把可能遗漏或语义判断写成自动通过；页面类型结构与角色权限表达已对照规范核对；交付说明已记录每个页面的页面类型。任何未验证项都已明确报告。随后更新 `.workflow/status.json` 的 `current_stage=prototype` 和 Prototype 产物路径，并按实际读取的 Design 文件记录 `design-set.py record-inputs`。

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
