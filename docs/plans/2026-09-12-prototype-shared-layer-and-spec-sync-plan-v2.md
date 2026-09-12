# Prototype 共享层与规范同步实施计划（执行基线）

> 日期：2026-09-12
> 状态：待执行
> 执行对象：其他 AI 执行，主 Agent 负责最终验收
> 目标产物：可持续生成、评审和维护的高保真 Prototype
> 决策人：产品负责人（PM）

## 一、目标与边界

本轮只解决三个问题，按优先级排序：

1. **降低生成和修改页面的上下文成本**：普通页面不重复读取与任务无关的完整视觉和行为规范。
2. **提高新页面的规范落地率**：把稳定、无业务语义的共性行为下沉到模板和 `shared/ui`，并让模板样板本身成为正确示例。
3. **降低多工程共享层漂移**：模板工程与审计 Prototype 的共享 UI、图标、主题基础设施保持可核对的一致状态。

本轮不做：

- 页面 spec 化或渲染引擎；
- 一页一文件或一页一独立 HTML 地址；
- 单文件 HTML 分发版；
- 部署链路改造；
- 审计工程 66 页全面重写；
- 补齐全部 `data-field` / `data-page` 锚点；
- 将自动检查接入 `spm-prototype-review` 作为阻塞门禁；
- 用脚本替代 Design、权限、状态机、流程和异常的业务判断。

## 二、必须遵守的职责边界

### 2.1 模板和共享 UI

模板 `templates/prototype-vite/` 是新项目的真实起点，也是 AI 最容易模仿的代码样板。模板和 `src/shared/` 只承载稳定的视觉、结构和通用交互，不承载 Design 业务事实。

允许下沉：

- 页头、区块卡、工具栏、数据表、状态标签、空态、操作栏、页脚、详情列表；
- 图标语义映射和图表适配（**指统一入口与适配机制，不是跨工程统一映射内容**；各工程业务图标不同，见 6.2）；
- 主题颜色注入和壳层基础 CSS；
- 分页、空表态、空字段等可稳定定义的默认展示行为。

禁止下沉：

- 业务字段、权限、角色、状态机、流程、接口、数据范围和业务异常；
- 共享组件对业务字段或流程的静默推断；
- 为了满足共享率而改变 Design 已确认的产品事实。

### 2.2 `spm-prototype`

生成 Skill 负责读取 Design 事实闭包、判定页面类型、按场景读取规则、选择共享组件、表达业务事实、生成后自检和构建/浏览器验证。

Skill 不重复维护共享组件的完整 DOM/CSS 细节。详细组件行为以模板真实源码为准，规则文档只说明边界和使用条件。

### 2.3 `spm-prototype-review`

Review 保持独立，只读 Prototype 并给出第二意见。Review 必须继续读取完整视觉规范和适用专项规则，结合 Design、源码、构建和浏览器证据判断：

- 共享 UI 是否正确使用；
- 页面是否绕过共享组件的默认行为；
- 共享组件是否静默丢失调用方参数；
- 权限、状态、异常、流程和运行时交互是否闭环。

生成侧自检返回 0 不能替代 Review；Review 也不能仅凭脚本结果判定业务质量。

## 三、实施原则

1. 先改模板真实能力，再改 Skill 读取策略，再迁移存量工程。
2. 先做小范围代表页面实验，验证组件行为后再决定是否批量迁移。
3. 只把误报可控、可稳定解析的规则交给脚本；业务语义留给 AI 和 Review。
4. 存量工程采用增量迁移：本轮覆盖共享基础设施和受影响页面，未受影响页面列清单，不宣称全库完成。
5. 所有事实源修改必须同步消费者并运行仓库回归套件。
6. 不覆盖用户已有修改；审计工程修改前必须生成带时间戳的完整备份。

## 四、阶段 0：事实源与模板能力收口

本阶段只修改模板、规范和仓库内 Skill/契约，不修改审计工程。执行者必须先逐项读取现有文件，再按下面的目标修改；不得将“同步”“清理”“修正”理解为全文件重写。

### 4.1 输入与基线

执行前确认以下路径真实存在：

- `skills/spm-prototype/SKILL.md`
- `skills/spm-prototype-review/SKILL.md`
- `contracts/review-checklist.md`
- `contracts/prototype-review-checklist.md`
- `references/prototype-writing.md`
- `references/prototype-visual-spec.md`
- `references/prototype-shell.md`
- `references/prototype-page-types.md`
- `references/prototype-component-behavior.md`
- `references/prototype-role-permission.md`
- `scripts/python/prototype-source-check.py`
- `scripts/python/prototype-consistency-check.py`
- `scripts/python/test-resource-integrity.py`
- `scripts/python/test-prototype-source-check.py`
- `scripts/python/test-prototype-consistency-check.py`
- `templates/prototype-vite/src/shared/ui/index.jsx`
- `templates/prototype-vite/src/shared/ui/PageFooter.jsx`
- `templates/prototype-vite/src/shared/ui/DetailList.jsx`
- `templates/prototype-vite/src/shared/icons/index.jsx`
- `templates/prototype-vite/src/shared/charts/TablerChart.jsx`
- `templates/prototype-vite/src/theme/tablerTheme.ts`
- `templates/prototype-vite/src/theme/tablerTokens.ts`
- `templates/prototype-vite/src/styles/global.css`
- `templates/prototype-vite/src/main.jsx`
- `templates/prototype-vite/src/routes.jsx`
- `templates/prototype-vite/src/App.jsx`
- `templates/prototype-vite/src/modules/home/Home.jsx`
- `templates/prototype-vite/src/modules/demo/DetailDemo.jsx`
- `templates/prototype-vite/src/modules/demo/FormDemo.jsx`
- `templates/prototype-vite/src/modules/demo/DesignGallery.jsx`

先运行：

```text
python scripts/python/test-resource-integrity.py
```

记录基线失败项。基线失败不能被伪装成“本轮新增”，本轮改动产生的新失败必须在继续前修复。

### 4.2 规范数值同步：必须改的具体内容

#### 文件：`references/prototype-visual-spec.md`

只修改与当前运行时主题不一致的数值表和相关自检项，不改颜色角色、视觉原则、状态矩阵和页面类型规则。至少完成以下替换：

| 原文旧值 | 统一为 | 对应语义 |
|---|---|---|
| `#0559a8` | `#0563BC` | 主色 hover / active |
| `#232e3c` | `#1f2937` | 一级正文和标题 |
| `#626976` | `#6b7280` | 二级文字、表头和图表标签 |
| `#959dac` | `#9ca3af` | 三级文字、弱化文字 |
| `#fafbfc` | `#f9fafb` | 页面背景、表头和描述标签背景 |
| `#182433` | `#ffffff` | 侧栏背景，当前项目已拍板浅色侧栏 |

同步检查表中的：

- 主色 hover / active 使用 `#0563BC`；
- 正文使用 `#1f2937`；
- 次要文字使用 `#6b7280`；
- 三级文字使用 `#9ca3af`；
- 页面底和表头底使用 `#f9fafb`；
- 侧栏使用白底。

不要把 `#066fd1` 改成 `#0563BC`；主色和 hover 色必须保留两个不同角色。不要把 `rgba(4,32,69,0.1)`、功能色和图表轴色无依据替换成其他值；这些值先与 `tablerTheme.ts` 逐项核对。

#### 文件：`references/prototype-shell.md`

修正“正确实现模板”中的失效示例：

1. 将 `var(--spm-color-primary)` 替换为模板实际注入的变量，例如 `var(--brand)`；示例中的 Avatar 必须能够从 `main.jsx` 注入的 `tablerCssVars` 取得颜色。
2. 将示例中的原生 `<Card><Table ... pagination={false} size="middle" /></Card>` 改成 `SectionCard`/`DataTable` 语义入口；删除示例里的 `size="middle"` 和默认关闭分页写法。
3. 示例返回按钮、操作按钮和图标必须符合当前 `shared/ui`、`shared/icons` 入口，不得继续示范页面直接拼装旧实现。
4. 检查示例代码中的 `useMemo` import；示例若使用 `useMemo`，必须在 import 中明确列出，不能留下照抄即运行时报错的示例。
5. 保留 Hash 路由、`routes.jsx` 唯一路由注册表和 query 保留规则，不因修示例而改动路由架构。

验收方式：把修改后的 shell 示例逐字复制到临时模板页面或最小示例中，使用模板依赖执行构建；禁止只用肉眼判断“应该能跑”。

#### 文件：`references/prototype-writing.md`

完成以下定点修复：

1. 表格固定列示例和文字中的 `fixed: "right"` 统一改为 `fixed: "end"`；左侧统一使用 `fixed: "start"`。
2. 与 `prototype-page-types.md` 的说明保持一致：注明旧的 `left/right` 在 antd 6 仍会被 rc-table 归一化，但项目新代码统一使用 `start/end`。
3. 将“可执行 Token 唯一入口”改成准确表述：运行时主题入口是 `src/theme/tablerTheme.ts`；图表必要颜色由 `tablerTokens.ts` 的 `chart` 段提供；不得继续声称整个 `tablerTokens.ts` 是所有视觉 Token 的唯一运行时入口。
4. 保留普通页面、复杂场景和 Review 的读取职责差异，不在本文件中新增第二套颜色表。

#### 文件：`references/prototype-page-types.md`

1. 保留 `start/end` 作为新代码统一写法。
2. 删除或改写会让读者误以为 `left/right` 已失效的表述；明确它们是兼容写法，但不是本项目新代码推荐写法。
3. 保留“只有确有横向溢出才使用滚动和固定列”的让路条款。

### 4.3 Token 文件和真实消费者

#### 文件：`templates/prototype-vite/src/theme/tablerTheme.ts`

- 保留当前实际生效的颜色值和 `tablerCssVars`；
- 保留 `tablerCssVars` 注入到 `document.documentElement` 的契约；
- 不新增尺寸、字号、字体、阴影和圆角覆盖；
- 修改前搜索所有 import，确认 `tablerTheme`、`tablerCssVars` 和每个颜色变量的消费者。

#### 文件：`templates/prototype-vite/src/theme/tablerTokens.ts`

- 删除前先搜索全仓库真实 import 和属性读取；
- 删除未被使用的 `colors`、`spacing`、`typography`、`radii`、`layout`、`elevation`、`motion`、`breakpoints`、`layers` 数据；
- 保留 `chart.colors`、`chart.axis`、`chart.label`、`chart.grid` 及 `TablerChart.jsx` 实际读取所需字段；
- 删除未被使用的 `tablerCssVariables` 导出；
- 将仍在使用的 `chart.label` 从旧值 `#626976` 更新为 `#6b7280`；
- 如果搜索发现某字段仍有真实消费者，不得删除，先在计划执行记录中列出消费者。

#### 文件：`templates/prototype-vite/src/shared/charts/TablerChart.jsx`

只验证并适配现有 `chart` 字段，不把图表业务数据或页面字段下沉到共享层。确认颜色、坐标轴、网格和标签都能从保留的 `chart` 段取得。

### 4.4 共享组件的具体修改

#### 文件：`templates/prototype-vite/src/shared/ui/DetailList.jsx`

在 `descItems` 构造前增加展示值归一化：

- `null`、`undefined`、空字符串转换为 `—`；
- `0`、`false` 原样保留；
- React element、`StatusTag`、链接等非空节点原样保留；
- 不修改 `label`、`variant`、`column` 和 Card/Descriptions 的既有布局契约。

#### 文件：`templates/prototype-vite/src/shared/ui/index.jsx`

只在实验确认稳定后修改 `TablerDataTable`：

- 保留 `pagination={false}` 的关闭语义；
- 保留调用方显式分页对象，并与默认分页合并；
- 保留 `scroll`、`locale`、`loading`、`rowSelection`、`columns` 等调用方属性；
- 对没有自定义 `render` 的普通列，评估是否能统一显示空值 `—`；
- 对已有 `render` 的状态、金额、链接、操作列不得静默接管；
- 不改变默认 `scroll={{ x: 'max-content' }}` 的现有行为，除非实验发现它破坏现有页面。

实验至少覆盖：普通文本空值、数字 0、布尔 false、状态 render、操作 render、分页关闭、受控分页、空表态和横向滚动。实验失败时保留现状，并把空字段规则限定在 `DetailList` 和页面自定义 render，不强行给 `DataTable` 加默认接管。

### 4.5 模板样板具体修改

> **执行前须知（关系到本节的收益口径）**：`skills/spm-prototype/SKILL.md` 第 63 步已规定——复制模板后**立即删除** `src/modules/demo/` 下的 `DesignGallery.jsx`、`DetailDemo.jsx`、`FormDemo.jsx`，以及 `routes.jsx` 中对应的 import 与路由登记（`/gallery`、`/detail`、`/form-demo`）。
>
> 因此本节的改造作用范围仅限于：①模板工程自身构建与阶段 0 验收期间的正确性；②生成流程执行删除动作前，若已读过模板源码时的示范正确性。
>
> 执行者不得因为本节做了改造，就认为样张页会进入用户项目；也不得把"样张页已合规"写成本轮对用户的对外收益。若判断本节投入与收益不匹配，应先报告再决定是否简化。

#### 文件：`templates/prototype-vite/src/modules/home/Home.jsx`

- 将 `TablerPageHeader`、`TablerSectionCard`、`TablerDataTable` 等旧实现名改为 `PageHeader`、`SectionCard`、`DataTable` 等语义导出名；
- 将所有 `/demo-form` 改为已注册的 `/form-demo`；
- 检查所有按钮和导航目标均能在 `routes.jsx` 找到；
- 清理本次替换产生的无用 import。

#### 文件：`templates/prototype-vite/src/modules/demo/DetailDemo.jsx`

- 用 `PageHeader` 的 `onBack` 替换手写返回按钮；
- 用 `DetailList` 或 `SectionCard` 承载详情分组；
- 使用 `StatusTag` 表达状态；
- 使用 `PageFooter` 和 `ActionBar`；
- 空字段交给 `DetailList` 的默认 `—` 行为；
- 保留样板业务文案，不新增真实业务字段、权限或状态。

#### 文件：`templates/prototype-vite/src/modules/demo/FormDemo.jsx`

- 使用 `FormSection`；
- 每个可编辑字段具备稳定 `name`；
- 必填和格式规则通过 `rules` 表达；
- 页面外操作通过 Form 实例触发提交和重置；
- 使用 `ActionBar`，不保留第二套页面底部按钮；
- 关闭态和校验失败态必须能在浏览器观察。

#### 文件：`templates/prototype-vite/src/modules/demo/DesignGallery.jsx`

- 作为控件展示台保留或删除必须由执行者按模板生成流程决定；
- 若保留，文件头明确“仅用于展示原生控件观感，不作为业务页面写法样板”；
- 其特殊例外不得扩大到其他 `modules/` 页面；
- 不把 gallery 的原生控件作为 `shared/ui` 迁移标准。

### 4.6 阶段 0 验收

模板目录执行：

```text
npm ci
npm run build
```

使用真实浏览器验证：

- `/`、`/detail`、`/form-demo`、`/gallery` 可达；
- Home 所有跳转不进入 NotFound；
- DetailDemo 的空值显示为 `—`；
- FormDemo 提交、重置、校验失败可观察；
- DataTable 的分页、空态、scroll 和自定义 render 未被破坏；
- Portal 内容可读取主题变量；
- 无新增直接图标库 import、外部 CSS 或第二套主题。


## 五、阶段 1：生成侧上下文分层

### 5.1 目标

把普通页面的常驻读取内容压缩为稳定短规则，同时保留复杂场景的详细规范，不能通过删除规则来省 Token。

### 5.2 `spm-prototype` 调整

在 Skill 中保留普通任务必需的短规则：

- 事实输入是 Design 闭包；
- 先判页面类型；
- 高频结构命中即复用 `shared/ui`；
- 颜色走 `tablerTheme`；
- 尺寸、间距、字体、阴影走 Ant Design 官方默认；
- 图标走 `shared/icons`，图表走 `shared/charts`；
- 空字段使用 `—`；
- 不新增 Design 未定义事实；
- 完成后按适用场景验证构建、路由、交互和 console。

详细规范按触发条件读取：

- 新增颜色、主题或共享组件：读取视觉规范相关完整章节；
- 图表：读取图表规则和 `TablerChart`；
- Portal、sticky、Sider 或响应式：读取 behavior 对应章节；
- 角色差异：读取 `prototype-role-permission.md`；
- 多页面 shell、导航、路由或白屏：读取 `prototype-shell.md`；
- 页面类型：只读取命中的 `prototype-page-types.md` 章节。

不要删除 `spm-prototype-review` 的完整视觉规范读取要求。生成侧和 Review 侧读取策略必须不同。

### 5.3 可验收指标

阶段 1 完成后必须给出前后对照数据，否则无法判断"省了多少"，本阶段不得只以"已改为分层读取"作为完成结论。

1. **常驻读取量**：用一个普通改页任务做样本，记录实际读入的规范文件清单与总行数，并与改造前对照。记录测算口径（按字节或按 token 估算均可，但必须写明），不得只写结论不写口径。
2. **额外触发次数**：连续若干次普通改页任务中，额外触发专项规范读取的次数与触发原因。普通页的预期是 0 次额外触发；每出现 1 次触发，须记录该触发条件是否已写入分层规则。
3. **规则不减项**：分层读取后，`spm-prototype` 保留的短规则条数与原规范硬规则条数对照，说明每一条硬规则在短规则或触发条件中的落点。**不得因省 Token 而删除规则**；若有规则被移除，必须单独说明理由并经确认。
4. **Review 侧未受影响**：确认 `spm-prototype-review` 仍完整读取 `prototype-visual-spec.md`，未被一并改成条件读。

指标 1、2 若无法精确测量，按实际读入文件清单与行数如实记录，不得估算后写成结论。


## 六、阶段 2：审计 Prototype 增量迁移

### 6.1 备份和边界

审计工程不在 git 管理下。任何修改前，先在审计工程同级目录创建完整备份：

```text
output/prototype -> output/prototype-backup-20260912-<HHmm>
```

执行时输出实际绝对路径，并确认备份包含 `src/`、工程文件、入口脚本和必要静态资源。不得依赖旧备份代替本次备份。

模板工程和审计工程的工作区可能有用户修改，不得用全量覆盖方式同步；先生成差异清单，再按文件处理。

### 6.2 共享基础设施同步

权威源固定为：

```text
templates/prototype-vite/src/shared/ui/
```

审计工程对应路径为同步目标。

**`shared/ui/` 纳入内容一致性比较。** 页头、区块卡、工具栏、数据表、状态标签、空态、操作栏、页脚、详情列表都是语义通用组件，不承载业务事实，可以跨工程强制一致。

**`shared/icons/` 不纳入内容一致性比较。** 图标是业务语义映射层，不是通用层：同一语义名在不同项目指向不同官方图标。实测审计工程有 **30 个模板没有的独有图标**（`IconFileCertificate → AuditOutlined`、`IconSpeakerphone → NotificationOutlined`、`IconFileCheck` 等），模板侧则是 `IconPackage`、`IconBuilding`、`IconMoneybag` 等通用样张映射。若按模板覆盖，审计工程这 30 个图标名立即失效，8 个业务模块报错。

图标侧只执行一条硬规则校验：**页面层不得直接 import `@ant-design/icons` 或任何第三方图标库**。语义映射的具体内容由各工程自行保留，不判红、不同步。

不比较整个 `src/shared/` 目录。审计工程允许保留其业务专用共享文件，例如 `demoContext/`、`snapshotView/` 以及其他已存在且不属于模板共享层的文件；这些文件不参与哈希一致性判定，也不得为了通过检查而删除。

**主题与全局样式不在本轮强制同步范围内。** 执行前须核对并记录现状，不得顺手覆盖：

- `src/theme/tablerTheme.ts`：两工程**色值已一致**（实测仅差 3 行说明性注释，以及审计工程多一行 `export default tablerTheme;`，属导出方式差异而非视觉差异）。如需统一导出方式，单独提出，不在本轮处理。
- `src/styles/global.css`：两工程差异约 **276 行**，属审计工程自身壳层布局（顶栏、侧栏、标签栏等结构样式）。**不得按模板覆盖**，否则破坏审计工程现有布局。
- `src/main.jsx`：只核对 `tablerCssVars` 注入契约是否成立，不做全文同步。

同步前先列出模板和审计工程两侧 `shared/ui/` 的相对文件清单，并登记审计工程 `shared/icons/index.jsx` 的图标语义名清单（只登记，不同步）。同步规则为：

1. 模板是 `shared/ui/` 的唯一权威源；`shared/icons/` 无跨工程权威源；
2. `shared/ui/` 目标文件存在但内容不同，按差异确认后同步；同步前必须确认审计工程未对该文件做本地扩展（额外 props、本地样式钩子等），有扩展则先报告再决定；
3. `shared/ui/` 模板有而目标没有的文件，复制并验证 import；
4. `shared/ui/` 目标有而模板没有的文件，保留，不判红；
5. `shared/charts/`、`shared/role.jsx`、`shared/NotFound.jsx` 以及 `shared/` 下其他文件只有在本轮明确列入同步清单时才处理，不因目录哈希而被连带覆盖。

如实现哈希比较脚本，**只比较 `shared/ui/` 这一个相对路径子集**，使用规范化后的 UTF-8 文件内容 SHA-256，并打印具体差异文件。脚本不得比较 `shared/icons/`，不得比较整个 `src/shared/`，不得把审计工程特有文件列为错误，不得判断业务字段、权限或状态，也不得创建新的综合回执。

同步后验证：

- `shared/ui/` 同名文件相对路径与内容一致；
- 审计工程 `shared/icons/index.jsx` 原有语义名全部仍然存在（数量不少于同步前），页面层无新增直接图标库 import；
- 审计工程特有共享文件（`demoContext/`、`snapshotView/` 等）仍然存在；
- 审计工程主题色值未因本轮改动发生变化；
- 共享 UI、图标、图表和主题依赖可以构建；
- 审计工程原有业务模块 import 未被静默删除。

### 6.3 迁移清单

批量修改前，生成逐文件清单：

```text
文件 | 页面类型 | 版权实现 | 返回实现 | 分页实现 | 空字段实现 | 共享件目标 | 风险 | 状态
```

至少选择三类代表页面先迁移：

1. 详情页：验证 `PageHeader`、`DetailList`、空字段和返回；
2. 列表页：验证 `DataTable`、分页、空态和行操作；
3. 表单页：验证 `FormSection`、`Form`、`ActionBar`、提交和重置。

三类页面均通过构建和浏览器验证后，才决定剩余页面是否可以批量处理。

### 6.4 可批量与不可批量内容

可以批量处理且需要人工抽查 diff：

- 明确重复的版权行；
- 明确的旧图标库 import；
- 明确的旧主题变量；
- 已确认错误的 `/demo-form` 路由；
- 共享基础设施文件同步。

不得初始阶段直接批量处理：

- 返回按钮：可能包含页面特有返回逻辑；
- 分页：可能包含服务端分页、受控页码或特殊 `showTotal`；
- 表格列 `render`：可能承担状态、金额、链接和操作业务语义；
- 表单提交、重置和操作栏；
- 角色权限、状态机和异常路径。

每个页面完成迁移后，清理本次产生的无用 import、局部 CSS 和变量，但不删除与本次改动无关的旧代码。

### 6.5 阶段 2 验收

在模板和审计工程分别执行：

```text
npm ci
npm run build
```

审计工程至少验证：

- 所有本轮实际修改过的页面和路由；
- 详情、列表、表单三类代表页面的关键交互；
- 共享组件默认行为没有丢失 `scroll`、`pagination`、`locale`、`loading` 和 Form 生命周期；
- 浏览器 console 无新增错误；
- 未迁移页面清单、原因和残余风险已记录。

本阶段可以不做 66 页全量浏览器探针，但不得把抽查结果表述为“66 页全部迁移完成”。

## 七、阶段 3：最小生成侧自检

### 7.1 准入条件

只有阶段 0 至阶段 2 已证明某一类缺陷反复发生、AI 自检容易漏掉、且脚本能够低误报稳定识别时，才新增检查；否则只更新 Skill 自检清单，不新增脚本。

### 7.2 初版允许检查的范围

如证据充分，新增脚本可命名为：

```text
scripts/python/prototype-shared-guard.py
```

初版只检查低误报、可确定识别的事实：

1. 页面层直接 import `@ant-design/icons` 或其他被禁止的图标库；
2. 页面层引入外部 CSS；
3. 页面层出现明确的版权文案重复实现；
4. 页面层使用已废弃的主题变量或旧主题入口；
5. 模板工程与审计工程 **`shared/ui/` 子集内同名文件内容不一致**。

   本项**只比 `shared/ui/`**：不比 `shared/icons/`（图标是业务语义映射，跨工程必然不同，见 6.2），不比整个 `src/shared/`，审计工程特有文件不判红。实现时必须与 6.2 的口径逐字一致，不得把本项写成"共享目录"或"共享层"等宽泛表述——那样会重新引入恒红门禁。

输出命中文件、行号和规则编号；命中返回 `1`，输入或工程错误返回 `2`，无命中返回 `0`。

### 7.3 初版禁止检查的范围

以下内容不得在初版中直接做成字符串门禁：

- 所有返回按钮；
- 所有 `pageSize`、`showSizeChanger`；
- 所有硬编码颜色；
- 单文件超过 300 行；
- 页面是否已经表达某个业务字段、权限、状态或异常。

这些内容需要结合调用场景和 Design 判断。若未来要加入，必须先提供真实缺陷证据、误报评估和修正动作，不能仅凭“看起来可以检查”加入。

### 7.4 接入方式

脚本只接入 `skills/spm-prototype/SKILL.md` 的生成完成自检节点：

```text
执行脚本 -> 读取命中 -> 生成侧自行修正 -> 重新构建和复验 -> 再交付
```

不得接入 `spm-prototype-review` 作为启动门禁或阻塞条件。脚本返回 `0` 不代表 Prototype 业务完整、权限正确、状态闭环或视觉通过。

## 八、阶段 4：Review 契约同步

### 8.1 共享默认行为的判断口径

同步 `contracts/prototype-review-checklist.md` 和必要的 Review Skill 文字，使判断基准从“页面是否手写”改为：

- 页面是否正确使用了适用的共享组件；
- 页面是否绕过或破坏了共享组件的默认行为；
- 页面是否通过自定义参数合理覆盖默认行为；
- 共享组件无法表达业务字段、权限、状态或流程时，页面是否有合理的原生组件回退。

特别核对检查项 19、22、25，避免共享层已经承担默认行为后，Review 反而把页面不再手写判为缺陷。

### 8.2 生成侧与 Review 侧读取策略

保留差异：

- `spm-prototype`：按普通页面和命中场景分层读取；
- `spm-prototype-review`：继续读取完整 `prototype-visual-spec.md` 和所有适用专项规则。

Review 不接入共享 guard，也不把 guard 结果作为结论。Review 仍须审查共享 UI 使用、绕过默认行为、运行时参数传递、页面类型和真实浏览器结果。

### 8.3 Review 回归验收

至少运行：

```text
python scripts/python/test-resource-integrity.py
python scripts/python/test-prototype-source-check.py
python scripts/python/test-prototype-consistency-check.py
python scripts/python/test-shitpm-regression.py
```

若测试文件的实际入口参数不同，先读取测试文件后按其真实命令执行，不自行猜测参数。回归失败必须区分基线失败与本轮新增失败。

## 九、执行顺序和停止条件

执行顺序固定为：

```text
阶段 0：事实源与模板能力收口
  ↓
阶段 1：生成侧上下文分层
  ↓
阶段 2：审计工程备份与增量迁移
  ↓
阶段 3：最小生成侧自检
  ↓
阶段 4：Review 契约同步与回归
```

可独立交付点：

- 阶段 0 完成后，新项目模板即可受益；
- 阶段 1 完成后，普通生成和修改任务即可减少无关读取；
- 阶段 2 可延后，不阻塞模板和 Skill 收口；
- 阶段 3 只有在检查准入条件满足时执行；
- 阶段 4 必须在共享行为和读取策略定型后执行。

必须停止并报告的情况：

- Design 输入、模板源码或工程路径无法确认；
- 共享组件行为实验不稳定；
- 审计工程备份失败；
- 构建失败、路由白屏或出现新增 console 错误；
- 发现需要补写权限、状态、流程或数据范围事实；
- 用户已有修改会被覆盖；
- 新脚本出现不可接受的误报；
- Review 契约与生成 Skill 无法形成一致的职责边界。

