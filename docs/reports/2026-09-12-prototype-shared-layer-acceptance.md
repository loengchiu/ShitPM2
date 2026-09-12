# Prototype 共享层与规范同步：执行验收报告

> 日期：2026-09-12
> 验收人：主 Agent（独立验收，未采信执行方自述）
> 验收对象：`docs/plans/2026-09-12-prototype-shared-layer-and-spec-sync-plan-v2.md` 阶段 0–4
> 行为准则：以备份做差分基线、跑仓库回归套件、构建与浏览器实测，不凭报告结论判定

## 一、结论

**条件通过（PASS with conditions）**

阶段 0 / 1 / 3 / 4 达到计划要求，质量高于预期；阶段 2 完成度符合计划最低要求但收益面很小。登记 3 项 P2 缺陷，均可在半日内修复，无 P0/P1。

## 二、通过项（附实测证据）

### 阶段 0 事实源与模板能力收口 —— 通过

| 检查项 | 实测结果 |
|---|---|
| 规范色值替换表 6 项 | `#0559a8`/`#232e3c`/`#626976`/`#959dac`/`#fafbfc`/`#182433` 在 references 与模板 src 中**全部归零**；新值 `#0563BC`/`#1f2937`/`#6b7280`/`#9ca3af`/`#f9fafb`/`#ffffff` 到位 |
| 主色未被误改 | `#066fd1` 保留 3 处，未与 hover 色合并 |
| shell.md 失效示例 | `--spm-*` 归零，改用 `var(--brand)`；`size="middle"` / `pagination={false}` 违规示例已清除 |
| writing.md 定点修复 | `fixed` 统一为 `start/end`，并注明 `left/right` 仍被 rc-table 归一化；Token 入口表述已改为"运行时入口是 tablerTheme.ts，图表色由 tablerTokens.ts 的 chart 段提供" |
| page-types.md | 已明确 `left/right` **并未失效**、钉列不渲染的真实原因是无横向溢出（与 v3 验收源码结论一致） |
| tablerTokens.ts | 93 → **12 行**，仅保留 `chart` 段；`tablerCssVariables` 已删；`chart.label` 更新为 `#6b7280`；`TablerChart.jsx` 所需 4 字段（colors/axis/grid/label）齐备 |
| DetailList 空字段 | `formatDetailValue` 实现，`null/undefined/''` → `—`，`0`/`false`/React element 原样保留 |
| DataTable 空值 | `normalizeColumns` 对**无自定义 render** 的普通列补 `—`，有 render 的列原样放行（不静默接管），递归处理 `col.children` |
| 样张页 | Home 旧 `Tabler*` 名归零；`/demo-form` → `/form-demo`；导航目标与 `routes.jsx` 注册项**无未注册项**（坏链已修） |
| 构建 | `npm run build` 通过（2.34 MB，仅体积警告） |
| 浏览器实测 | `/#/`、`/#/detail`、`/#/form-demo`、`/#/gallery` 全部可达，无 404、无 pageerror、无 console.error；`--brand` 注入为 `#066fd1`；DetailDemo 空值渲染为 `—` |

### 阶段 1 生成侧上下文分层 —— 通过（指标未留档，见 D2）

- SKILL.md 已建立分层读取：常驻核心短规则 + "按条件触发读取（未命中不读取）"；page-types 只读取命中章节
- 短规则完整保留：空字段 3 处、`shared/icons` 4 处、`shared/ui` 4 处、官方默认 2 处
- 未误伤 Review 侧：`spm-prototype-review` 第 7 步仍要求完整读取 `prototype-visual-spec.md`

### 阶段 3 最小生成侧自检 —— 通过

- 新增 `prototype-shared-guard.py` + `test-prototype-shared-guard.py`，自测 **7 项全过**
- **G5 口径实现正确**：只遍历模板 `shared/ui/*.jsx` 同名文件做 SHA256 比对；不比 `shared/icons/`，不比整个 `src/shared/`，模板没有的文件不判红 → 不会重演"恒红门禁"
- G1（页面层直引图标库）实现正确，允许从 `shared/icons` 引入
- 已按 ADR-5 接入生成侧自检，未接入 Review 作阻塞

### 阶段 4 Review 契约同步 —— 通过（质量最高的一项）

- 检查项 19：口径改为"是否绕过/静默破坏共享组件默认行为"，并明确**共享组件已承担默认行为时，页面不再重复手写不得判为缺陷**
- 检查项 22：同上，且"共享组件已封装默认行为时页面直接复用不得误判为手写缺失"
- 检查项 25：明确**空字段由共享层自动格式化为 `—` 视为达标**
- 这三条正是本轮最危险的冲突点（"改得越彻底报得越多"），已被正确消除

### 我补入 v2 的修正项 —— 均被正确执行

| 修正项 | 实测 |
|---|---|
| H1 图标不得强制一致 | 审计 icons 113 → **124 行**，`IconFileCertificate`/`IconSpeakerphone`/`cloneElement` 全部保留，模板图标 `IconMoneybag` 未混入 → 未发生"同步即瘫" |
| H3 主题不强制同步 | 审计 `global.css` 仍为自有版（276 行差异保留），未被覆盖 |

## 三、缺陷登记

### D1（P2）重写导致区块锚点丢失 3 个

`PlanModule.jsx` 整文件重写（903 → 895 行，1798 行 diff）后：

| 页面 | 旧 | 新 |
|---|---|---|
| Pagepl02 | 项目信息、页面操作 | **全部丢失** |
| Pagepl03 | 项目信息、页面操作 | 页面操作（丢项目信息） |
| Pagepl01 / pl04 / pl05 | 各 1 个 | 保持 |

`data-block` 总数 7 → 4。锚点是 `prototype-consistency-check.py` 的比对依据，丢失会削弱门禁覆盖。计划 6.4 明确"不删除与本次改动无关的旧代码"，此属违反。

**修复方式**：在 `Pagepl02` 的详情卡与操作区、`Pagepl03` 的详情卡补回 `data-block` 属性（值按备份原文）。

### D2（P2）阶段 1 可验收指标未留档

计划 5.3 要求给出常驻读取量前后对照、额外触发次数、规则不减项、Review 侧未受影响四项数据。**未找到任何执行记录文档**。现状无法证明"省了多少 token"，用户核心诉求之一不可度量。

### D3（P2）阶段 2 未迁移清单未留档

计划 6.5 要求"未迁移页面清单、原因和残余风险已记录"。实测 12 个模块文件中仅 `PlanModule.jsx` 被迁移，其余 11 个（含 61 页）未动，但无清单留档。

### D4（说明项，不判缺陷）阶段 2 收益面很小

- 迁移范围：1 个模块文件 / 12 个，覆盖 5 页 / 66 页
- 横切收敛几乎未做：版权行 28 → **26 处**，手写 `pageSize` 22 → **22 处**
- 判定：计划 6.3 只要求"至少三类代表页面先迁移"，`PlanModule` 内确实含列表/详情/表单三类；6.4 又明确分页"不得初始阶段直接批量处理"。**符合计划最低要求，不判违规**
- 但后果是：**省 token 的收益在审计工程上尚未兑现**（66 页中仅 5 页受益）

## 四、整文件重写的内容安全性（重点复核）

`PlanModule.jsx` 被整文件重写，违反计划 4.1"不得将'同步''清理''修正'理解为全文件重写"。为此做了内容等价性复核：

| 指标 | 旧 | 新 | 结论 |
|---|---|---|---|
| 页面函数 | 5（pl01–pl05） | 5 | ✅ 无丢失 |
| 状态映射 `STAG` | 2 处 | 2 处 | ✅ |
| `disabled` 权限表达 | 15 处 | 15 处 | ✅ |
| 中文业务文案集合 | 193 条 | 194 条 | ✅ **零丢失**，新增 1 条 |
| `data-block` 锚点 | 7 | 4 | ❌ 见 D1 |

结论：写法违规，但**未吞掉业务内容**，可接受（D1 单独修）。

## 五、回归与验证

- 仓库回归套件：**12 通过 / 1 失败**（新增 `test-prototype-shared-guard.py` 通过；失败项 `test-prd-simplification.py` 为改造前既有的存量红，非本轮引入）
- 模板工程 `npm run build`：通过
- 审计工程 `npm run build`：通过（1.64 MB）
- 浏览器实测：模板 4 路由 + 审计 3 路由全部可达，无 pageerror / console.error，`--brand` 注入正常
- 审计工程备份：`output/prototype-backup-20260912-1053` 存在（6.1 硬要求满足）

## 六、建议

1. 修 D1（补 3 个 `data-block`），成本约 10 分钟
2. 补 D2、D3 两份留档（指标对照 + 未迁移清单），成本约半小时
3. D4 决策点：是否继续迁移剩余 61 页。建议**不要为迁移而迁移**——等下次有批量改动时顺带做，避免新旧结构并存（历史教训）
4. 本轮真实收益目前落在**新项目模板**上（阶段 0/1/3/4 全通过），审计工程仅 5 页受益，汇报口径应按此如实表述
