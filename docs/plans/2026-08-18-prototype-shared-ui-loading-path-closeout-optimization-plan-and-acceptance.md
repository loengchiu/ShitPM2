# Prototype 共享 UI 默认路径与规则按需加载收尾迭代执行及验收文档

> 日期：2026-08-18
>
> 状态：待其他 AI 执行与验收
>
> 迭代性质：已完成 Tabler + Ant Design 视觉迭代及后续运行时契约修复之后的效率收尾
>
> 目标：不降低 Design 事实、交互、运行时和真实浏览器验收标准，缩短普通 Prototype 页面生成与修改时的规则读取和重复实现路径。
>
> 文档边界：本文件是仓库维护计划，不是运行时规则。执行完成后，长期有效的内容必须落入 `skills/`、`references/`、`contracts/` 或 `templates/`。

## 1. 本轮结论

上一轮已经完成的视觉体系、共享 UI、运行时契约和浏览器验收要求，全部视为本轮基线，不重新实施。本轮只做四件事：

1. 把高频结构的默认实现入口前移到现有 `shared/ui`。
2. 把 `prototype-component-behavior.md` 从“每次完整读取的实现说明”收敛为“命中例外时读取的判断与契约”。
3. 消除 Skill、behavior、writing、visual spec、Review 之间的重复或冲突规则。
4. 仅在存在真实普通 Modal 消费者时，新增薄 `TablerModal`；没有消费者时不得为了完成计划制造演示页面或孤立组件。

本轮不是再次修复 Portal、dayjs、组件 import、稳定 ID、wrapper props、路由或响应式问题。这些内容只作为不可回退的验收基线。

## 2. 成功标准

完成后必须同时满足：

- 普通列表、卡片、指标、状态、空态、工具栏、行操作、页头和表单分区，先检查并复用当前 `src/shared/ui/` 的真实导出。
- `shared/ui` 是默认路径，不是绝对禁令；Ant Design 原生组件和页面特有结构仍可在有明确理由时使用。
- 普通任务不再无条件完整读取 `prototype-component-behavior.md`。
- `prototype-component-behavior.md` 不复制共享组件 API、DOM、CSS 或视觉数值，只保留 AI 必须判断的边界、例外和跨层运行时契约。
- 通用停止条件和完成门槛留在 `spm-prototype/SKILL.md`，不能为了缩短文档而被删除，也不能通过“交付前再完整读取 behavior”把读取成本加回来。
- 每条活动规则只有一个权威来源，其他文件只保留触发条件和指针。
- 现有构建、全部注册路由、真实交互、console、Portal 和响应式验收不降级。
- 不新增检查器、检查 JSON、评分器、回执文件或只证明步骤执行过的工具。

以下不能单独证明完成：文档行数减少、`npm run build` 通过、搜索零命中、共享组件数量增加。

## 3. 前置事实与保护边界

### 3.1 已完成基线

执行者以当前工作区真实文件为准。以下能力已由前序迭代建立，不属于本轮新增范围：

- Tabler 视觉规范、Token、Ant Design 主题和模板壳层；
- 当前 `shared/ui` 中已经存在的高频组件；
- Portal、Modal、日期值、稳定身份、wrapper props、路由和真实浏览器验证契约；
- Prototype Review 对源码、构建、路由、交互和视觉的审查入口。

历史计划只用于理解本轮为何存在，不是执行时必须加载的运行时事实源。不得照历史计划重做已经落地的修复。

### 3.2 工作区保护

开始前运行：

```powershell
git status --short
git diff -- skills/spm-prototype/SKILL.md references/prototype-component-behavior.md references/prototype-writing.md references/prototype-visual-spec.md skills/spm-prototype-review/SKILL.md contracts/prototype-review-checklist.md templates/prototype-vite/src/shared/ui/index.jsx
```

要求：

- 把现有修改和未跟踪文件视为用户基线；
- 只修改本计划列出的文件；
- 不使用 `git reset`、`git checkout`、批量格式化或覆盖写入清理工作区；
- 不修改 `dist/`、`node_modules/`、Design、PRD 或真实项目业务事实；
- 不执行 commit 或 push，除非用户另行明确授权。

## 4. 规则事实源与目标加载路径

### 4.1 唯一职责

| 事实或规则 | 唯一权威来源 | 其他文件允许保留什么 |
| --- | --- | --- |
| 产品字段、状态、权限、流程、页面和范围 | 已确认 Design | 只引用，不补写 |
| 共享组件真实名称、props 和默认实现 | `templates/prototype-vite/src/shared/ui/` 源码 | 只写“先查真实导出”，不复制 API 索引 |
| 视觉值、Token、断点和层级关系 | `prototype-visual-spec.md` 与对应 Token | 只写触发指针，不复制数值 |
| Ant Design 工程写法 | `prototype-writing.md` | 只引用适用章节 |
| 组件选择、组合边界、例外和跨层行为 | `prototype-component-behavior.md` | Skill/Review 只保留触发条件 |
| 生成流程、停止条件和通用完成门槛 | `spm-prototype/SKILL.md` | 不下沉成需要每次再读取的长文档 |
| 独立审查流程 | `spm-prototype-review/SKILL.md` 与 checklist | 指向上述权威来源，不复制全文 |

### 4.2 目标加载路径

普通页面：

```text
已确认 Design
  → spm-prototype 流程和通用完成门槛
  → 当前模板与 shared/ui 真实导出
  → 直接组合页面
  → 构建和真实浏览器验收
```

命中例外时：

```text
普通路径
  → 根据明确触发词读取 behavior 的对应章节
  → 使用 writing / visual spec 的权威规则
  → 实施、构建和真实浏览器验收
```

不得把“最终验收”设计成再次完整读取 behavior。所有任务都适用的完成门槛应以短指令留在 Skill；只有特定场景才进入 behavior。

## 5. 执行阶段

### 阶段 1：建立规则迁移清单，不直接改写

逐节阅读当前 `prototype-component-behavior.md`，对每条规则只做以下一种归类：

| 分类 | 判定 | 处理 |
| --- | --- | --- |
| `Keep` | AI 必须做场景判断，源码无法自动表达 | 留在 behavior，压缩为正向指令 |
| `Move` | 内容属于视觉值、工程写法或通用完成门槛 | 移到唯一权威文件，原处只留必要指针 |
| `Source` | 组件源码已经完整实现 | behavior 删除复述，改为检查真实导出 |
| `Delete` | 过时、重复、矛盾或无稳定消费者 | 直接删除，不迁移到新包装文件 |

不要新建迁移 JSON、检查报告或长期清单文件。最终交付中用一张简表说明关键归类即可。

阶段完成条件：

- [ ] behavior 每条现有规则均有唯一归类。
- [ ] 已识别所有与 writing、visual spec、Skill、Review 或源码重复的内容。
- [ ] 尚未删除任何无法确定权威来源的规则；不确定项先核对当前实现。

### 阶段 2：修改 `skills/spm-prototype/SKILL.md`

保留 Design 事实源、停止条件、源码交付、构建和真实浏览器验收要求。只调整高频结构入口和 behavior 的加载条件。

必须加入的核心指令：

> 生成或修改页头、区块卡片、指标卡、工具栏、数据表格、状态、空态、图标按钮、行操作、表单分区和页面操作栏前，先读取当前模板 `src/shared/ui/` 的真实导出和目标组件实现。命中现有共享组件时直接复用，不在页面内复制它已经承担的 DOM、CSS 或默认行为。共享组件无法表达已确认 Design 要求时，允许组合 Ant Design 原生组件或页面特有结构，并说明回退原因。

行为文档只按以下触发条件加载：

| 触发场景 | 读取内容 | 期望结果 |
| --- | --- | --- |
| 固定列、复杂表格、超过默认数量的行操作、自定义分页或空态 | behavior 的表格与操作边界 | 明确是否扩展共享组件或局部组合 |
| Form、普通 Modal、确认弹窗、回填、提交、重置、页面外 ActionBar | behavior 的表单与弹层边界 | 明确生命周期归属和组件选择 |
| Dropdown、Select、DatePicker、Modal、移动 Sider、sticky 层级 | behavior 的 Portal 与响应式契约 | 验证层级、主题、焦点和交互 |
| 共享组件无法承接 Design | behavior 的回退规则 | 说明为何不复用、为何不扩展 |
| 新建共享组件或修改共享组件契约 | 完整 behavior + 目标源码调用方 | 防止破坏现有消费者 |

通用完成门槛必须直接留在 Skill，至少包含：构建成功、默认页和全部注册路由可打开、实际存在的关键交互可操作、console 无运行时错误、适用 Portal/响应式场景经过真实浏览器检查。措辞保持短，不复制测试脚本细节。

阶段完成条件：

- [ ] 普通高频页面先查 `shared/ui`，不是先读完整 behavior。
- [ ] 每个条件指针都有触发词、读取目标和结果，不使用模糊的“必要时参考”。
- [ ] Skill 没有写成“所有结构必须使用 shared/ui”。
- [ ] 通用完成门槛未被下沉、删除或弱化。

### 阶段 3：收敛 `prototype-component-behavior.md`

目标结构只保留四类内容：

1. 文件用途、适用条件和权威来源指针；
2. 组件选择与组合判断；
3. 特定场景例外；
4. 跨层运行时契约。

必须保留的判断规则包括：

- 每个视图只有一个主操作；
- Card 头部直接操作不超过 2 个，更多操作进入下拉；
- 查询条件区与业务工具栏分离；
- 表格默认不固定列，只有宽度、阅读连续性或关键操作确有需要时才固定；
- 当前 `TablerRowActions` 的可见操作与更多操作口径，以实际源码为准；
- Modal 与 Drawer 的选择由任务性质决定，不能由包装组件静默决定；
- 共享组件不承载 Design 字段、权限、状态机、接口或流程；
- 只有跨项目重复出现且已经稳定的例外，才升级为全局规则。

必须保留但只写一次的跨层契约包括：Portal 主题可见性、JSX import、当前 antd 版本与 DOM/props、DatePicker/dayjs 值形状、Modal footer、稳定身份、wrapper props 和真实浏览器交互。

必须删除或迁出的内容：

- 当前 `shared/ui` 已经实现的 DOM、CSS、默认值和 props 复述；
- 共享组件完整名称/API 表；组件源码才是事实源；
- visual spec 已定义的颜色、间距、字号、圆角、宽度、断点和 z-index 数值；
- writing 已定义的工程写法；
- Skill 已定义的通用执行步骤和完成门槛；
- 已废弃 antd 类名、失效代码示例和历史临时例外。

不设 40 行、100 行或任何固定行数目标。放行依据是每条旧规则都有正确归宿，且普通任务不再必须读取全文。

阶段完成条件：

- [ ] behavior 不再维护共享组件 API 索引。
- [ ] 每条保留规则都是行为判断、例外或跨层契约。
- [ ] 文档内没有第二套视觉值或工程实现说明。
- [ ] 规则短但具备动作、条件和完成结果，不能只剩“见源码”。

### 阶段 4：消除相邻规则冲突

只同步与本轮加载路径直接相关的文件：

- `prototype-writing.md`：表格默认不固定列；确有必要时才使用 `fixed: 'right'`。删除与 behavior 相反的无条件固定表述。
- `prototype-visual-spec.md`：核对 `TablerIconButton` 的类型描述，不得把图标按钮写成文本按钮；统一普通列表/表单是否显示 `TablerPageHeader` 的当前口径。
- `spm-prototype-review/SKILL.md`：Review 根据场景读取全部适用规则；普通生成路径变短不能导致 Review 漏项。
- `prototype-review-checklist.md`：只保留问题类型、证据要求和权威指针，不复制 behavior 全文。
- `prototype-component-behavior.md`：删除“任何例外都必须写回本文件”；改为只有重复、稳定、跨项目的例外才升级。

`spm-prd` 不在本轮修改。Prototype 的 antd、Tabler、Portal 或组件封装细节不得倒灌到 PRD Skill。

阶段完成条件：

- [ ] 固定列、行操作、图标按钮、PageHeader 和例外升级规则没有两套口径。
- [ ] Review 能找到全部适用规则，但生成 Skill 不再无条件加载 behavior。
- [ ] 每条规则只有一个完整定义，其余位置只保留指针。

### 阶段 5：按消费者证据决定是否新增 `TablerModal`

先搜索当前模板、测试夹具和本轮允许修改的源码中是否存在普通受控 Modal：

```powershell
rg -n "<Modal|Modal\." templates/prototype-vite test-fixture -g "*.jsx" -g "*.tsx" -g "*.js" -g "*.ts"
```

判定：

- 只有 `Modal.confirm()`：不实现 `TablerModal`，不把确认 API 强改成受控 Modal。
- 没有普通 Modal 消费者：不实现孤立组件，不新增演示业务；最终报告记为“经消费者门槛判定延期”，不算核心加载路径失败。
- 存在真实普通 Modal，且重复 footer、尺寸或按钮默认值：实现并迁移至少一个真实消费者。

实施时 `TablerModal` 必须是薄封装：

- 继续使用 antd 内置 footer，不自行用 `div`、`float` 或另一套 Button 布局重造；
- `size="sm|md|lg"` 可映射 480 / 640 / 800，显式 `width` 优先；
- 默认 `okText="确定"`、`cancelText="取消"`；
- 通过合并 `okButtonProps` 与 `cancelButtonProps` 提供 `IconCheck`、`IconX`，调用方显式设置优先；
- 透传 `footer`、`className`、`styles`、`afterOpenChange`、`destroyOnHidden`、`confirmLoading` 和当前锁定 antd Modal 支持的其他 props；
- `footer={null}` 和自定义 footer 不得被覆盖；
- 不接管 Form 初始化、回填、提交、重置、列表刷新、路由、权限或业务字段；
- 不决定 Modal 与 Drawer 的产品选择。

阶段完成条件：

- [ ] 消费者搜索证据明确。
- [ ] 无消费者时没有新增孤立组件或伪造入口。
- [ ] 有消费者时至少一个真实场景完成迁移、构建和浏览器交互验收。
- [ ] 包装组件只减少重复默认值，没有形成新的组件体系。

## 6. 验证方案

### 6.1 文档与事实源检查

执行定向搜索，逐项人工判断；搜索命中本身不等于失败：

```powershell
rg -n "prototype-component-behavior|shared/ui|TablerModal|fixed:|TablerIconButton|TablerRowActions|TablerPageHeader|任何例外" skills references contracts templates/prototype-vite/src
rg -n "ant-modal-content|float:|#root|dayjs|documentElement|pagination=|locale=|it\.key" skills references contracts templates/prototype-vite/src
```

检查结果必须能回答：

1. 普通页面是否还被要求完整读取 behavior？
2. shared UI 的 API 是否只由源码定义？
3. 判断规则、视觉值、工程写法和完成门槛是否各有唯一来源？
4. 前序迭代的运行时契约是否仍存在且没有相互矛盾？
5. Review 是否仍能覆盖普通路径和例外路径？

### 6.2 确定性检查

在仓库根目录运行：

```powershell
python scripts/python/test-resource-integrity.py
python scripts/python/test-shitpm-regression.py
git -c core.whitespace=cr-at-eol diff --check
```

不新增脚本来判断语义质量。已有脚本失败时保留原始错误，判断是本轮回归、既有基线还是脚本不适用。

### 6.3 模板构建与浏览器回归

只有修改了模板源码、共享组件或依赖文件时，才进入本节。先构建：

```powershell
Push-Location 'templates/prototype-vite'
npm run build
Pop-Location
```

依赖文件未变化且现有依赖可用时，不必重复 `npm ci`；缺少依赖或 lockfile 变化时再执行。构建通过后，在独立终端或可回收的长驻会话运行 `npm run preview -- --host 127.0.0.1`，完成验收后停止服务。

真实浏览器至少检查：默认页、全部注册路由、当前实际存在的 Form、Select、行操作、Modal/Portal、hash query 和响应式场景。不存在的场景标记“不适用”，不得制造页面凑验收；存在的场景不得用静态检查或 build 代替。

如果本轮只修改 Skill、reference 或 checklist，没有修改任何运行时代码，则不重复构建和浏览器回归；改为完成 `6.1`、`6.2` 和 `6.4`。规则文件变化不可能直接改变已构建模板，重复打开浏览器不能证明加载路径正确。

### 6.4 加载路径验收

用两个代表性任务做只读路径演练，不要求生成新的业务原型：

| 任务 | 预期读取路径 | 失败信号 |
| --- | --- | --- |
| 普通列表页修改 | Design → Skill → 当前共享组件源码 → 实施与通用验收 | 无条件打开完整 behavior；页面复制共享组件 CSS |
| Form + Modal 或复杂表格修改 | 普通路径 → behavior 对应章节 → writing/visual spec 的权威规则 | 找不到触发章节；必须在多份文件拼接同一规则 |

执行者记录两条路径实际需要读取的文件、触发原因和发现的重复定义。目的不是精确计算 token，而是证明普通路径确实缩短，例外路径仍然完整。

## 7. 最终验收矩阵

| 编号 | 验收项 | 通过标准 | 证据 |
| --- | --- | --- | --- |
| A-01 | 前序迭代边界 | 没有把已完成视觉/运行时修复重新当成本轮任务 | 修改清单 |
| A-02 | 共享 UI 默认路径 | 高频结构先查真实导出，允许有理由回退 | Skill 原文 |
| A-03 | 条件加载 | 普通任务不再完整读取 behavior；例外有明确触发词 | Skill 原文与路径演练 |
| A-04 | API 事实源 | behavior、writing、Review 不复制 shared UI 完整 API | 搜索与人工核对 |
| A-05 | behavior 收敛 | 只保留判断、例外和跨层契约；旧规则均有归宿 | 迁移简表与 diff |
| A-06 | 通用完成门槛 | 构建、路由、交互、console、Portal/响应式仍在 Skill | Skill 原文 |
| A-07 | 规则一致性 | fixed 列、行操作、IconButton、PageHeader、例外升级无冲突 | 定向搜索 |
| A-08 | Modal 决策 | 按真实消费者门槛实现或延期，没有孤立组件 | 搜索、diff、说明 |
| A-09 | PRD 边界 | `spm-prd`、Design 和业务事实未修改 | git diff |
| A-10 | 确定性回归 | 适用脚本和 CRLF-aware diff check 有明确结果 | 命令输出 |
| A-11 | 工程回归 | 修改运行时代码时模板 build 和适用浏览器场景通过；纯规则改动标记不适用 | 构建与浏览器证据或不适用说明 |
| A-12 | 效率结论 | 普通路径缩短且例外路径完整，不以跳过验收换速度 | 两条路径演练 |

以下任一情况出现时，只能报告“部分完成”或“阻塞”：

- 普通任务仍被要求完整读取 behavior；
- 为减少读取而删除了停止条件或真实浏览器验收；
- behavior 继续维护一份共享组件 API 表；
- 为了完成 `TablerModal` 新增无业务意义的消费者；
- build 通过但真实存在的关键交互未验证；
- 未说明既有失败、未验证项或消费者延期。

## 8. 执行者最终交付格式

其他 AI 最终回复按以下顺序输出：

1. **结论**：完成 / 部分完成 / 阻塞。
2. **本轮修改**：逐文件说明本轮效率收尾改了什么。
3. **未重复实施项**：说明哪些视觉和运行时能力被视为既有基线。
4. **规则迁移结果**：列出关键 `Keep / Move / Source / Delete` 项。
5. **加载路径**：普通任务和例外任务分别读什么。
6. **TablerModal 判定**：消费者证据、实现或延期原因。
7. **验证证据**：搜索、脚本、build、浏览器和路径演练结果。
8. **未完成项**：失败、阻塞、未验证、不适用或延期项。
9. **工作区边界**：说明保留了哪些既有修改；未执行 commit/push。

不得只回复“文档压缩完成”“组件已封装”“build 通过”或“按 Skill 执行完成”。最终结论必须逐项对应 A-01 至 A-12。
