# Design 推断值机制执行与验收报告

> 日期：2026-08-05
> 执行依据：`docs/plans/2026-08-05-inference-value-confirmation-plan-and-acceptance.md`
> 执行方式：按计划第 7 节报告格式输出
> 结论：**通过**。低影响展示层推断值（默认值/排序/分页/文案/标签颜色/界面层超时重试/低影响交互措辞）改为"直接写值 + 登记 decision-notes 推断值清单 + confirmation 汇总表一次拍板"；高影响清单（权限/状态机/删除传播/外部系统/历史数据/数据层超时重试/统计口径）维持"必须确认"未放宽；12/12 测试全绿；未新增检查器/门禁/回执；未执行 commit/push。

## 二、实际修改文件

| 文件 | 修改目的 |
|---|---|
| `docs/plans/2026-08-05-inference-value-confirmation-plan-and-acceptance.md` | 本方案（边界、机制、验收） |
| `references/prd-writing-rules.md` | §2"不得静默新增"拆分：推断值在 Design 阶段产生并登记，PRD 只承接拍板后的值，不自行新增；§2.1 交互四问按影响分级（低影响交互措辞承接推断值、高影响交互待确认）；§4 事实/推断值/待确认分开 |
| `skills/spm-design/SKILL.md` | 新增 §5.2 可推断值（范围/登记格式/套话禁止/高影响隔离）；输出段 decision-notes 加推断值清单；发"请确认"前呈现推断值汇总表（#/位置/值/依据/确认结果）；自检段交互细节分级 |
| `references/design-writing.md` | 新增"七·一、可推断值的写法"（直接写值、登记格式、场景化、高影响不得进入）；写作后自检第 11 项；反模式表加"机械重复文案冒充推断值""推断值未登记" |
| `templates/decision-notes.md` | 新增"推断值清单"段（表格式：推断值/位置/推断依据/确认结果，含使用说明注释） |
| `contracts/design-review-checklist.md` | 新增 X8"推断值登记完整"（正文推断值无登记记录、机械重复 N 次、高影响被当推断值静默写入） |
| `skills/spm-prd/SKILL.md` | 事实边界段：PRD 只承接确认后 Design（含拍板推断值），展示层推断值不在 PRD 新增；完成条件 4 与自检 6 交互细节分级 |
| `skills/spm-align/SKILL.md` | 执行流程 6 衔接：Align 的可推导结论/模型推测进入 Design 后，低影响展示层→推断值登记、高影响→待确认 |

未改：`design-fact-format.md`（`confirmed_facts` 仍只收材料事实，推断值不进——与机制一致，无需改）；无脚本改动（推断值清单是 decision-notes 段落，非新资产，符合 AGENTS.md 禁止新增检查器/回执）。

## 三、静态同步核对（五处落点）

| 落点 | 内容 | 状态 |
|---|---|---|
| spm-design §5.2 | 可推断范围 + 登记格式 + 高影响隔离清单 | ✅ |
| design-writing 七·一 | 直接写值、登记、场景化、反模式 | ✅ |
| templates/decision-notes | 推断值清单表格段 | ✅ |
| prd-writing-rules §2/§2.1/§4 | PRD 只承接、交互分级、事实/推断值/待确认分开 | ✅ |
| design-review-checklist X8 | 登记完整检查项 | ✅ |
| spm-prd 事实边界/完成条件/自检 | 承接规则 + 交互分级 | ✅ |
| spm-align 衔接 | 推测分流（推断值/待确认） | ✅ |

高影响清单（权限、数据范围、角色、状态机、流程/审批、删除传播、外部系统行为、历史数据处理方式、数据层超时/重试/补偿、金额与统计口径、范围边界）在 spm-design §5.2 与 prd-writing-rules §2 明确"必须确认"，无遗漏放宽。

## 四、功能验收

| 验收项 | 结果 |
|---|---|
| 展示层推断值可直接写值 | ✅ rules §2 原文：默认值/排序/分页/提示文案等由 Design 直接写推断值并登记；不再要求"保守表达" |
| 推断值登记格式 | ✅ decision-notes 模板：`推断值 \| 位置 \| 推断依据 \| 确认结果` 表 |
| confirmation 汇总表 | ✅ spm-design：发"请确认"前呈现推断值汇总表，用户一次拍板（接受/修改/拒绝），结果更新清单 |
| 高影响隔离 | ✅ 构造场景核对：权限/状态机/删除传播/外部系统/历史数据/数据层超时重试均列"必须确认"清单，spm-design §5.2 与 rules §2 双重声明 |
| 套话拒绝 | ✅ design-writing 反模式"机械重复文案冒充推断值"+ X8 检查项（同一话术跨场景重复 N 次为缺陷）；写不出依据的不写 |
| PRD 不自行新增推断值 | ✅ spm-prd 事实边界：推断值在 Design 阶段产生并登记，PRD 只承接拍板后的值 |

## 五、自动化结果

12/12 全绿：test-context-loading / test-prd-simplification / test-prd-style-lint / test-prd-consistency-semantics / test-design-simplification / test-design-index / test-shitpm-regression / test-resource-integrity / test-context-runtime / test-anti-hallucination / test-design-orchestrator / test-design-orchestration-replay。本轮无失败项。

## 六、未解决问题

1. **真实项目验证未做**：推断值机制是 AI 行为协议（登记/汇总表/拍板），需在下一个真实 Design 生成时验证"登记完整度"——AI 是否把每条推断值如实登记、汇总表是否可扫读。建议在下一轮真实项目 Design 时观察，按 X8 检查。
2. **"高影响交互"判定依赖模型**：二次确认/权限入口/破坏性分支的归类靠 AI 判断，无脚本兜底（符合 AGENTS.md 不加检查器的边界）；misjudge 时 X8/Review 可兜底。
3. **存量 Design 不迁移**：已确认的存量 design.md 不受影响；新机制自下一个 Design 生效。

## 七、Git 状态

- 本轮改动 8 个文件（方案 + rules + 2 SKILL + design-writing + 模板 + checklist + 验收报告），均未提交；
- 未执行 commit / push（等用户指示）。
