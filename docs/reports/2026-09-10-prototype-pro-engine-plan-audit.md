# Prototype ProComponents 引擎升级计划 · 对抗性审计报告（v2 修订版）

> 审计日期：2026-09-10
> 审计对象：`docs/plans/2026-09-10-prototype-ant-design-skill-engine-upgrade-plan-and-acceptance.md`
> 事实源：`AntGroupDesign/Ant-Design-Skill`（用户提供）、npm registry、本地 `templates/prototype-vite/`、`scripts/python/prototype-consistency-check.py`、`~/.workbuddy/skills/spm-prototype/SKILL.md`
> 结论：**2 项 P0 阻断 + 5 项 P1 必修 + 3 项 P2 建议**。方向正确、依据真实，但存在一处会直接卡死执行的技术硬伤与一处会削弱核心防幻觉能力的架构冲突。

---

## 0. 修订说明（审计自纠，必读）

本审计 v1 曾判定计划的两项前提为"转述幻觉"：**此项判定错误，予以撤回**。原因是审计时核验了同名近似的另一个仓库 `ant-design/antd-skill`（Ant Design CLI 团队，74 行 SKILL.md + `@ant-design/cli` 离线查询），而计划实际引用的是 `AntGroupDesign/Ant-Design-Skill`（Ant Design 官方设计团队，103 stars）。二者是**不同团队、不同用途的两个官方仓库**。

撤回内容：

| v1 判定 | 核实结果 | 处置 |
| :-- | :-- | :-- |
| "29 套生产级模板"是幻觉 | 官方仓库 `scripts/` 确有 **32 个 TSX 模板**（3 布局 + 6 表单 + 6 表格 + 8 列表 + 3 描述列表 + 6 图表） | **撤回**。资产真实；计划写 29，数字略偏（早期版本或计数口径差异） |
| "360KB 规范文档"是稻草人 | `references/` 实测 **362,096 字节 ≈ 354 KB** | **撤回**。数据基本准确；且官方 SKILL.md 自身即写明"体量较大，禁止一次性通读全文" |

教训入库：核实外部引用时，必须先确认**引用方指的是哪个具体实体**，不能用"同名近似的另一个对象"去否定。

**仍然成立且不受影响的结论**：P0-1（依赖与 antd 6 冲突）、P0-2（`consistency-check` 在 ProTable 下失效）——二者均由 npm registry 与本地源码直接证明。

---

## 1. 官方资产核实结果（供计划修订直接引用）

```
AntGroupDesign/Ant-Design-Skill  (Ant Design 官方设计团队, 103★, 最后推送 2026-07-14)
├── SKILL.md                     26,381 B   含"按任务选读"路由表 + 模板优先级规则
├── references/                 362,096 B   ≈354 KB
│   ├── layout.md                74,210 B
│   ├── global-style.css         75,945 B
│   ├── components_Table.md      52,415 B
│   ├── components_List.md       46,954 B
│   ├── components_Form.md       44,723 B
│   ├── components_Chart.md      55,879 B
│   └── components_DescriptionList.md 11,970 B
└── scripts/                     32 个 TSX 模板
    ├── layout/          3  (MixedLayout / SideLayout / TopLayout)
    ├── form/            6  (BasicForm / HorizontalStepsForm / VerticalStepsForm / EmbedForm / QueryFilter / LoginForm)
    ├── table/           6  (BasicTable / FilterSortTable / NestedTable / BatchTable / DragSortTable / ToolbarTable)
    ├── list/            8  (BasicList / EditList / ToolbarList / ExpandableList / SelectableList / QueryList / VerticalList / CardList)
    ├── description-list/3  (BasicDescriptions / EditableDescriptions / GroupedCardDescriptions)
    └── charts/          6  (OnlyChartsBlock / Basic-Icon-Total-Nested-TabsStatisticCard)
```

**官方模板确认基于 ProComponents**——`scripts/table/06-ToolbarTable.tsx` 首行：

```tsx
import type { ProColumns } from '@ant-design/pro-components';
import { LightFilter, ProFormDatePicker, ProTable } from '@ant-design/pro-components';
import { Button, ConfigProvider, Space } from 'antd';
```

即：计划 §5.1.1"引入 `@ant-design/pro-components`"的**动机成立**——要复用官方模板就必须引这个包。这一条不是拍脑袋。

官方 SKILL.md 亦已内置"模板起步"强制规则（原文）：

> **有代码模板时必须模板起步**：凡 `scripts/` 中已提供模板的场景，必须以对应模板复制改造为起点，只替换业务字段、数据、文案、图表配置与提交逻辑。

即计划 §3.1 的"模板起步"与 §6.2 的"选读路由表"**是忠实移植官方设计**，不是自创。计划的方法论主干是对的。

---

## 2. P0 阻断项

### P0-1 依赖与 antd 6 直接冲突；且官方模板是 antd 5 基线

| 项 | 事实 | 来源 |
| :-- | :-- | :-- |
| 项目 antd | `^6.6.0` | `templates/prototype-vite/package.json` |
| pro-components `latest` | `2.8.10`，peer `antd: ^4.24.15 \|\| ^5.11.2` | npm registry |
| pro-components `2.7.0`（计划指定） | peer `antd: ^4.24.15 \|\| ^5.11.2` | npm registry |
| 唯一支持 antd 6 的版本 | `3.1.14-7`，peer `antd: ^6.0.0`，**dist-tag = beta** | npm registry |

npm 7+ 对 peer 冲突默认 ERESOLVE 失败。计划 §5.1.1 写 `^2.7.0`、§9.1.3 写"经核实完全支持 React 18"——**该核实结论为假，且方向错**（见 P1-5）。按现文档执行，阶段 1 第一条命令即失败。

**加重情节**：官方模板内部硬编码 antd 5 基线 token——

```tsx
const tableTheme = { token: { fontSize: 14, colorPrimary: '#1677ff', borderRadius: 6 },
                     components: { Table: { headerBg: '#fafafa' } } };
```

`#1677ff` 是 **antd 5 默认主色**，圆角 6px；而 ShitPM Tabler 要求 `#066fd1` / 8px。即移植的不是"中性模板"，而是**自带 antd 5 视觉基线**的模板。

结论：移植 = **beta 依赖 + antd 5 遗产模板**双重风险，与 §11 自称的"高确定性"矛盾。

### P0-2 `consistency-check` 在 ProTable 路径下读取不到字段，防漂移能力被削弱

计划 §9.1 风险 2 原文：

> 下游的 `prototype-consistency-check.py` 具有硬性拦截能力，一旦发现字段名或操作按钮与 Design 不符直接报红阻断，倒逼模型必须精准填空。

本地源码事实（`scripts/python/prototype-consistency-check.py`）：

1. **提取方式**：`AnchorParser(HTMLParser)` 仅从 **JSX/HTML 标签属性**读取 `data-page/data-block/data-section/data-field/data-operation/data-state`；源码注释明写"Prototype 锚点只从真实 JSX/HTML 标签属性中提取"。
2. **ProTable 命中不了**：官方模板的列定义就是 JS 对象数组 `const columns: ProColumns<T>[] = [{ title: '应用名称', dataIndex: 'name' }]`——**没有 JSX 标签，无处挂载 `data-field`**。
3. **"字段遗漏"不报红**：Design 有而源码未标 → 落入 `possible_omissions`（risk），**不是** `deterministic_conflicts`（red），不阻断。只有"源码标了 Design 没有的锚点"才进 red。

后果是**方向相反**的：改用 ProTable 后，"多标"变难（red 数下降）而"漏标"变易（risk 上升）。脚本的返回码会更好看，事实保障却更弱——这是**用门禁指标变好看换取防幻觉能力变弱**，而防幻觉正是 ShitPM 的核心资产。

**要求**：计划必须先回答"ProTable 的 `columns` 如何产生可被 `consistency-check` 读取的字段锚点"。可行方向：约定 `columns` 内每项携带 `dataField` 字段并扩展脚本解析，或改为在列定义处生成带 `data-field` 的 `render`。答不上来之前，§3.3 成功标准第 3 条（`deterministic_conflicts = 0`）是无效验收项。

---

## 3. P1 必修项

### P1-3 官方模板自带的 75KB CSS 与硬编码 token 会与 Tabler 主题打架（新增）

官方每个模板首部均有 `import '../../references/global-style.css';`（75,945 B），且模板内嵌 `ConfigProvider theme`（`#1677ff` / `borderRadius: 6` / `headerBg: #fafafa`）。

计划 §5.1.2/§5.1.3 只写了"引入 `ProConfigProvider`""扩展 `tablerTheme.ts`"，**未处理**：
- 是否搬运官方 `global-style.css`（75KB）；若搬运，与 ShitPM 既有 `global.css` 的层叠冲突由谁裁决；
- 6 个模板内部的 `tableTheme` 硬编码 token 是否清除；不清则每个页面自带一套 antd 5 蓝；
- ShitPM 现有规则"三处表头统一为 `#faf9f5`"与官方 `headerBg: '#fafafa'` 不一致。

建议：移植时**强制剥离**模板内 `theme` 常量与 `global-style.css` 引用，视觉一律由 `tablerTheme.ts` 单点供给；并在模板转换清单中逐项记录剥离点。

### P1-4 `behavior.md` 现有章节与路由表对不上，且移植后体量将膨胀约 10 倍

`references/prototype-component-behavior.md` 现仅 **5,305 B、4 个章节**（组件选择与组合判断 / 特定场景例外 / 跨层运行时契约 / 适用验收）。

计划 §6.2 路由表引用的"§表格与 QueryFilter 选型""§单行工具栏与表头对齐""§分步表单与步骤校验""§嵌入表单与分区""§分组描述列表""§浮层与 Header 操作区"**目前一个都不存在**；§5.1.6 只承诺新增 4 条规则，覆盖不了路由表需要的 6 节（缺"分步表单与步骤校验""嵌入表单与分区"）。模型按表执行会读到空章节后自行发挥，恰好制造计划想消灭的"现场发明 DOM"。

叠加体量问题：若按官方规范移植，`components_Table.md` 52KB + `components_Form.md` 45KB 就已是现有 behavior.md（5.3KB）的 18 倍。计划 §3.2 承诺"不全量灌入"与 §6.2"单点装载"必须靠**重新切分章节**实现，不能简单拷贝——这一点计划未写。

### P1-5 已有 11 个 shared/ui 组件承担"轻量 ProComponents"角色，计划无退役决策

`templates/prototype-vite/src/shared/ui/index.jsx`（228 行）已导出：`PageHeader / SectionCard / MetricCard / Toolbar / DataTable / StatusTag / IconButton / RowActions / FormSection / EmptyState / ActionBar`（`Tabler*` 与品牌中立双别名），且 `SKILL.md` 第 5 条已强制"先读真实导出，命中即复用"。

引入 `ProTable` 与 `TablerDataTable` 职能重叠、`ProForm` 与 `TablerFormSection` 重叠，而计划未写任何共存/退役规则——**正在复刻本项目 2026-08-05 的老坑**（"原型架构翻转未收口"导致双架构并存，最终由 `5f51d53` 收口）。

**要求**：§5 增补"现有 shared/ui 处置清单"——保留哪些、被 Pro 替代哪些、过渡期是否允许同页混用。

### P1-6 阶段 0 重复劳动，且基线口径错误

`experiments/antd-tabler-efficiency/` 已于 **2026-08-28 产出 A-pure-antd 与 C-converged 两套完整产物**（各含 `dist/`、`dist-tabler/`、`dist-claude/`、`src/`），`EXPERIMENT_INPUT.md`、`A-prompt.md`、`C-prompt.md` 齐全。计划阶段 0 要求"全新生成一次"属重复劳动。

更严重的是**口径**：`A-prompt.md` 明确要求"只使用 antd 标准组件，**不需要任何自定义主题、视觉规范或共享组件**"——A 组是**裸 antd** 基线，不是 ShitPM 现状基线（现状 = 原生 antd + shared/ui + Tabler 主题）。拿它当 §8.3 的"现状 280~450 行"来证"下降 ≥50%"，会把 shared/ui 早已取得的收敛收益**错记到 ProComponents 账上**。

**要求**：基线重定义为 **C 组（当前完整体系）vs D 组（+ProComponents）**；A 组仅作"无护栏裸写"参考下界。

### P1-7 §9.1.3 风险识别错位

计划担心 React 18 兼容性；事实是 pro-components v3 peer 为 `react: >=18.0.0`，React 18 **天然满足**，无需担心。真正会炸的是 **antd 6 不兼容**（P0-1），计划却完全没识别。典型"风险清单很全，风险在清单外"。

---

## 4. P2 建议项

| # | 问题 | 建议 |
| :-- | :-- | :-- |
| 8 | 成功标准自相矛盾：§3.1"首次运行成功率 100%" vs §8.3"≥80%"；且 n=1 撑不起百分比 | 改为**单页首次运行缺陷计数**（重置失效 / 分页未归位 / 抽屉回填陈旧 / 步骤校验绕过 / 闭包陈旧） |
| 9 | §10 争议点二自问"是否需要无模板场景的回退契约"，§5/§6 未答 | 补：无匹配模板时沿用 shared/ui + 原生 antd，并在交付说明记录"未命中模板"（官方 SKILL.md 第 4 条已有同类规则，可直接移植） |
| 10 | 阶段 6"满足阈值合入主干"未定义拍板人与分支关系 | 当前 git 位于 `main`；明确分支 `codex/upgrade-prototype-pro-engine`、拍板人、以及未达标即弃分支（§9.3 已写，需与阶段 6 对齐） |

---

## 5. 计划中应予保留的正确判断

不为挑刺而挑刺。以下判断经核实为正确，重写时须保留：

1. **"负向文字规约 → 正向模板起步"方向正确**，且与官方 SKILL.md 的强制规则一致。
2. **引入 ProComponents 的动机成立**——官方模板确基于 `ProTable`/`ProColumns`，不引包则无法复用。
3. **"不全量灌入 360KB"与"按任务选读路由表"是忠实移植官方设计**（官方 references 实测 354KB，SKILL.md 自己就禁止通读）。
4. **四个不变项全对**：不迁 TypeScript、不开放事实脑补、不推翻 Tabler 视觉、不新增 JSON 报告与门禁——符合 `AGENTS.md` 精简原则与"禁止复杂度换皮"。
5. **§9.2 停止条件扎实**，尤其"发现必须新增复杂报告/中间件才能运行即终止"，符合仓库准入原则。

---

## 6. 放行建议

**不予放行至阶段 0，但建议保留方案继续推进。** 修订顺序：

1. **先做 beta 可行性探针**（约半天，成本最低）：在特性分支装 `3.1.14-7`，移植 1 个官方模板（建议 `06-ToolbarTable`），剥离其 `theme` 常量与 `global-style.css`，接入 `tablerTheme`，然后跑 `npm run build` + `consistency-check.py`。一次证伪/证实三件事：① 能否装上并构建通过；② `data-field` 锚点丢失多少；③ Tabler 主题是否被污染。
2. 探针通过 → 按 P0-1/2 与 P1-3~7 修订计划后重审；探针失败 → 转下方备选。
3. **备选（风险低一个量级）**：不引 ProComponents，只移植官方**规范与结构规则**（筛选临界值、表头三要素、表体单行、抽屉按钮置顶）进 `behavior.md`，代码仍由 shared/ui + 原生 antd 实现。可拿到计划 §3.1 中"原厂设计品质"这一项收益，且不触碰 P0-1/P0-2 任一风险。

> 无论走哪条路，P0-2 都建议单独立项：ProTable 与 `consistency-check` 的锚点机制不兼容，是架构级冲突，不会随版本升级自动消失。
