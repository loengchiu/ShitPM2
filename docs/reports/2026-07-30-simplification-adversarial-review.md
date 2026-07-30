# Design Skill 极简化：全量对抗性审查

> 审查对象：`docs/plans/2026-07-30-design-skill-radical-simplification-execution-plan.md` 对应改动
> 审查日期：2026-07-30
> 审查方式：静态代码审查 + 全量测试运行 + 残留引用扫描 + 下游接线核查 + `py_compile` 全量编译
> 结论：**主干改动正确、可上线；发现 1 处方案偏离（P2，可还原）+ 2 处低风险瑕疵（P2）。无 P0/P1 阻断。**

---

## 1. 核心结论（先说结果）

改动与方案高度一致，没有把"门禁换皮"或"重新引入检查 JSON"。关键事实：

- 四个废弃脚本已删除：`review-precheck.py` / `artifact-guard.py` / `state-machine-check.py` / `verify-against-metadata.py`。
- `design-orchestrator.py` 内 `review_findings`、`repair`、`repair_fingerprints`、`_validate_comprehensive_review`、`run_deterministic_gate`、`generated_check`、`compile-design-index`、`report-completed`、`context-runtime-check` 调用、`_handoff_requirements` **全部移除**（Grep 零命中）。
- 模式收敛为 `("simple","full")`，`full-layered` 在代码与活动文档中零残留。
- `design-confirmation.py` 已简化：`confirm` 只算哈希并保存；`check` 只比对哈希与结构；无外部质量检查、无 `subprocess`。
- 全量测试真实跑通、零跳过；所有 `.py` 编译通过。

---

## 2. 验证证据

### 2.1 测试套件（真实运行，非跳过）

| 测试 | 结果 |
|------|------|
| test-design-orchestrator.py | 6 用例通过 |
| test-design-orchestration-replay.py | 5 用例通过 |
| test-design-simplification.py | simple=5 / business=8 / complex=9 任务；recovery stale_rejected；通过 |
| test-shitpm-regression.py | 3 用例通过（含确认闭环、废弃脚本删除、保留工具存在） |
| test-design-index.py | 16 用例 OK |
| test-context-loading.py | 通过 |
| test-resource-integrity.py | 通过 |
| test-anti-hallucination.py | 4/4 幻觉检出通过 |

### 2.2 残留引用扫描（活动根：README/USAGE/skills/contracts/references/schemas/scripts/python）

- 已删脚本名（`review-precheck.py` 等 4 个）：**全库零活动引用**（仅命中历史 `docs/plans`、`docs/reports`、测试 fixture 报告）。
- 废弃动作/模式（`simple-generated-check` / `review-comprehensive` / `compile-design-index` / `report-completed` / `full-layered` 等）：**活动代码/Skill/合同/测试零命中**。
- `py_compile` 对 `scripts/python/*.py` 全量编译：**全部通过**。

### 2.3 任务图（与方案 §3 一致）

- `simple`：`material-index → material-facts:* → material-merge → simple-design`
- `full`：`material-index → material-facts:* → material-merge → a-layer → b-layer → c-layer → design-editor`
- `design-editor` 接受仍要求 A/B/C 基线 + design-brief 存在（`_validate_design_writer_upstream`），但不跑索引/门禁。
- 全部必需任务完成后 `next_action` 直接返回 `state=completed`。

### 2.4 下游接线（方案 §F）

- `spm-prd` / `spm-prototype` 入口只走 `design-confirmation.py check`；完成后保留 `prd-consistency-check.py` / `prototype-consistency-check.py`。
- skills 全库**零 `artifact-guard` 引用**。
- `prd-consistency-check.py` 直接 `import design-index.py`（line 1101）与 `stage-prep.py`（line 1283），**按需编译索引**，不依赖编排器预编译——移除 `compile-design-index` 不影响下游。

### 2.5 确认语义（方案 §D）

`confirm`：仅计算 `design.md` SHA-256 并写 `.workflow/confirmations/design.json`，保留 `ok/confirmed/reason/confirmed_at` 与原因 `no_confirmation_record`/`confirmation_invalid`/`hash_match`/`hash_mismatch`；不检查编排器/Review/A-B-C/索引。`check` 仅校验确认记录结构与当前哈希。

---

## 3. 发现的问题

### P2-1（方案偏离）：批量删除了历史计划与报告文件

git status 显示以下**历史** `docs/plans`、`docs/reports` 文件被删除（共 15 个，均为 2026-07-29 / round7 / round8）：

```
docs/plans/2026-07-29-design-context-performance.md
docs/plans/2026-07-29-design-orchestration-context-governance.md
docs/plans/2026-07-29-design-orchestration-implementation-and-test-runbook.md
docs/plans/2026-07-29-design-orchestration-low-cost-test-plan.md
docs/plans/2026-07-29-material-ingestion-orchestration-discussion.md
docs/plans/2026-07-29-park-quality-design-acceptance-plan.md
docs/plans/2026-07-29-park-quality-design-implementation-plan.md
docs/plans/2026-07-29-park-quality-pm-design-orchestration.md
docs/plans/2026-07-29-project-material-intake-design.md
docs/plans/2026-07-29-project-material-intake-implementation-design.md
docs/reports/2026-07-29-context-loading-round6-review.md
docs/reports/2026-07-29-park-quality-design-acceptance-result.md
docs/reports/2026-07-29-round7-recheck.md
docs/reports/2026-07-29-round7-review.md
docs/reports/2026-07-30-round8-fix-verification.md
```

- 方案 §2.3、§6 Phase 4、§11 明确要求**保留历史计划与报告**，不为清理扩大改动范围；方案 §10 禁止"修改历史计划和报告以伪造从未存在过旧流程"。
- 这批文件是已提交（tracked）的历史记录，删除后丢失审计轨迹，且不属于方案清单中的删除项（方案只要求删 4 个脚本 + 活动引用）。
- **非功能性、可完全还原**：`git checkout HEAD -- <path>` 即可恢复。
- **建议**：除非你明确想清理这些历史文档，否则还原它们；若确要删除，建议单独说明并保留 round 评审作为依据，不要在本次重构里顺手删。

### P2-2（歧义措辞，有踩坑风险）：spm-prd 流程里直接给出 `confirm` 命令

`skills/spm-prd/SKILL.md` 第 38-42 行：check 失败 → 停止 → "提示用户先确认或重新确认 Design" 下方贴了 `design-confirmation.py ... confirm` 命令。

- 当前语义由"提示用户"限定为**用户执行**，不违反方案 §10"不自动确认 Design"。
- 但把 `confirm` 命令直接放在 PRD 流程分支里，是典型的 footgun：模型可能据此"替用户跑 confirm"，从而实际变成自动确认。
- **建议**：在该分支显式加一句"AI 不运行 confirm，由用户执行后重跑 PRD"，或把 confirm 命令移出 PRD 流程段落。`spm-prototype` 未出现此问题。

### P2-3（文档瑕疵）：spm-design SKILL 章节编号错位

`skills/spm-design/SKILL.md` 第 40 行 `## 4. 执行主图`，其下子节写成 `### 3.1 简单模式` / `### 3.2 完整模式`（应为 4.1 / 4.2）。仅文档编号，不影响功能。

---

## 4. 需要你拍板/持续观察的风险（非缺陷）

- **质量安全网整体移除**：原 `review-comprehensive` 等自动检查已删，Design 质量现在完全依赖 `spm-design` §7 的 AI 写作内自检清单 + PRD/Prototype 的下游一致性检查。这是方案的核心论点，但真实项目若出现质量下降，只能回补 `spm-design` 的 AI 检查清单（方案 §9 明确要求：禁止第一反应重新加脚本/门禁/回执）。建议用 1 个简单 + 2 个复杂真实项目跑一遍（方案 §8 场景 A/B/C）做质量验收，不要只信脚本全绿。
- **编排器接受回执仍在**：`handle_accept` 仍写每任务 `receipt_path` JSON（line 718-725），用于中断续跑与"必需输出存在"判定。这是方案 §2.1 保留的最小调度能力，**不是**方案 §1.3 原则 6 所禁的"新质量回执"，确认无误。

---

## 5. 方案 §11 执行报告要素核对

| 要素 | 状态 |
|------|------|
| 修改文件列表 | 见 git status（README/USAGE/contracts/schemas/skills/scripts/python 等 38 个 modified） |
| 删除文件列表 | 4 脚本（按方案）+ 15 历史文档（偏离，见 P2-1） |
| 新 simple / full 任务图 | 已核对，与方案 §3 一致 |
| design-confirmation.py 最终语义 | 已核对，符合方案 §D |
| 保留但移出主流程的工具 | design-index.py / stage-prep.py / prd-consistency-check.py / prototype-consistency-check.py / context-runtime-check.py（按需诊断） |
| 删除/改写旧测试 | test-design-orchestrator / replay / simplification / regression 重写覆盖新行为；无验证废弃行为的测试残留 |
| 自动化测试结果 | 全绿（见 §2.1） |
| 真实质量场景结果 | 测试用合成项目覆盖 simple/full/复杂冲突；**真实项目场景 A/B/C/D 尚未由本次改动执行**，建议补充 |
| 活动引用残留 | 无（见 §2.2） |
| 未解决风险 | P2-1（历史文档删除）、P2-2（confirm 措辞）、P2-3（编号）；质量安全网移除需真实项目验收 |

---

## 6. 放行判定

**主干代码可放行**：模式收敛、门禁与检查脚本删除、确认简化、下游接线、测试覆盖、编译均正确，无 P0/P1 阻断。

**放行前建议处理**：
1. （P2-1）确认是否还原 15 个历史文档；若保留删除需你明确表态。
2. （P2-2）给 spm-prd 加一句"AI 不自动 confirm"的显式约束，消除 footgun。
3. （P2-3）修正 spm-design 章节编号。
4. （验收）用真实项目跑方案 §8 场景 A/B/C，确认质量未下降。
