# Round 11 全量对抗性审查报告

- 时间：2026-07-30 14:10
- 对象：用户"修复完了"后的工作区（V2 分支，20 文件 modified + 13 文件 untracked，全部未提交）
- 方法：从零开始，不信任记忆与验收报告；逐项实证 + 重跑全量测试
- 前置：Round 10 提出 1 个 P1（v2 资产/事实 schema 未文档化且未接入动作卡）+ 2 个 P2（表格解析脆弱性、gitignore 排除核心测试）

## 总评

**Round 10 的 3 个问题全部真修，且经实证确认；本轮未发现任何新的 P0/P1/P2 阻断；全量 9/9 测试绿。**

本轮质量明显好于以往：用户没有再用伪宿主掩盖契约盲区，而是把 v2 资产格式落成了可执行文档 + 动作卡 schema + 门禁强制三位一体的闭环。可以进入真实项目试跑。

---

## 已修确认（逐项实证，非看报告）

### P1（原：v2 资产/事实 schema 未文档化、动作卡 output_schema 仍是 required:[]，真实模型必卡 B/C 层门禁）—— 真修

**文档层**：新增 `references/design-baseline-format.md`、`references/design-fact-format.md`，明确规定：
- v2 基线公共包装含 `schema_version: design-analysis/v2` + `task_id` + `status∈{completed,success}` + `coverage[]` + `source_refs[]` + `input_fingerprint`/`conclusions`/`conflicts`/`questions`/`payload`
- 合并事实库含 `version:1` + `material_revision` + `confirmed_facts`/`source_conflicts`/`missing_information`/`non_derivable_items`

**接入层**（关键防回归点）：`design-orchestrator.py:435-501` 的 `output_contract(task)` 不再是全局 `required:[]` 兜底，而是按任务类型分支返回：
- `task_kind=="baseline"` → `required:["schema_version","task_id","status","coverage","source_refs"]` + `schema_ref` 指向 doc + `schema_version` enum 约束
- `material_facts:` / `material_merge` / `review-comprehensive` / `generated_check` 各自返回对应必填 schema

**覆盖完整性**：门禁 `V2_HANDOFFS`（`context-runtime-check.py:138-144`）强制的 6 个 v2 资产（a/b/c-baseline、design-brief、business-conflicts、cross-layer-conflicts）全部由 `task_kind=="baseline"` 的任务产出（a-layer/b-layer/c-layer、a5-merge-review、b6-model-review、c3-acceptance、c4-cross-layer-review）。旧 `full` 模式的 b6/c4/a5/c3 同样走 baseline 分支，**旧模式未被破坏**。

**实证**（直接跑门禁）：
- 合规基线（含全部必填）→ `rc=0, valid=True`
- 模型式残缺（只写 `status`）→ `rc=1`，缺 `schema_version`
- 错误 `schema_version: design-analysis/v1` → `rc=1`
- 错误 `status: done` → `rc=1`

结论：动作卡现在把门禁强制的字段原样告诉模型，真实模型写出的 JSON 能过门禁；伪宿主硬编码的输出也与此完全一致（集成测试确实在用真实门禁校验真实契约，无偏离）。

### P2-a（原：字段表前加一句说明文字即被静默丢弃整张表）—— 真修

`design-index.py:208-253` 的 `_table_after_heading` 重写为"扫描标题直属范围内第一张有效表"：表前的说明文字、空行、HTML 注释一律 `continue` 跳过，只有找到"表头行 + 分隔行"这一对才认定表格开始。docstring 第 215-217 行明确写明修复目的。

**实证**：在合规 design 的字段表前加"下面列出字段："→ `rc=0, ok=True, errors=0`（Round 10 时为 `rc=1`）。

### P2-b（原：.gitignore 排除 4 个核心测试，克隆/CI 跑不到回归网）—— 真修

`.gitignore` diff 删除了对 `test-shitpm-regression.py`、`test-context-loading.py`、`test-resource-integrity.py`、`test-anti-hallucination.py`、`test-fixture/` 的忽略。现在这些文件可见（`git status` 显示 `??` 未跟踪而非被忽略），一旦提交即进入版本控制。

---

## 测试结果

**9/9 全绿**（真实 python 3.13.12 重跑）：

| 测试 | 结果 |
| --- | --- |
| test-anti-hallucination.py | PASS（4 类幻觉全检出） |
| test-context-loading.py | PASS |
| test-context-runtime.py | PASS（复用/失效/门禁正常） |
| test-design-index.py | PASS（16 tests） |
| test-design-orchestration-replay.py | PASS（16 用例） |
| test-design-orchestrator.py | PASS（12 用例） |
| test-design-simplification.py | PASS |
| test-resource-integrity.py | PASS |
| test-shitpm-regression.py | PASS（37 通过 0 失败） |

test-design-simplification.py 同时覆盖 `full` 与 `full-layered` 双模式，确认旧 full 模式未被回归。

---

## 新扫描结论（无 P0/P1/P2 阻断）

- **契约/动作卡/SKILL 自洽**：`design-orchestration-contract.md` 增补 `command` 字段、material-index 不可伪造、full-layered 显式可选不替换 full，均与代码一致。
- **无孤儿脚本**：`design-confirmation.py`、`download-prototype-libs.py`、`review-precheck.py`（含 `prd_entity_coverage` 函数，line 76）均真实存在；Round 10 报告里担心的 `design-model.json`/`design-challenge.json` 仅作旧版兼容，新主链不再依赖。
- **综合审查有真校验**：`accept_outputs` → `_validate_comprehensive_review`（760-779 行）在 accept 时强制 comprehensive.json 存在、为 dict、`schema_version==design-check/v2`、`findings` 为数组、`coverage` 覆盖全部 6 项责任。无静默通过缺口。
- **design-editor 接受门禁完好**：`_validate_design_writer_upstream`（782-804）对 full-layered 校验 material_revision 新鲜度 + a/b/c 基线 + design-brief 存在性；`accept_outputs` 再叠加综合审查 + 交接门禁 + design.md 格式门禁。

---

## 遗留 P3（不阻断，建议后续收口）

1. **review-comprehensive 的 schema_ref 指向规划文档**：`output_contract` 中 `review-comprehensive` 分支的 `schema_ref` 为 `docs/plans/2026-07-30-shitpm-simplification-proposal.md#4.4...`。这是规划文档，若被移动/删除则引用悬空（仅文档导航用途，门禁不读它，无功能影响）。建议把综合审查格式沉淀到 `references/` 稳定位置。

2. **基线 doc 的"必须字段"与示例小不一致**：`design-baseline-format.md` 示例含 `input_fingerprint`，但第 30-35 行"必须字段"清单未列它；门禁也不强制 `input_fingerprint`。当前不阻断（doc 写明其余字段"按责任使用"），但若希望基线可溯源，应把它纳入必须字段并让动作卡/output_contract 一并要求。

3. **所有修复均未提交**：当前 20 文件 modified + 13 文件 untracked，均在 working tree。验收报告"9 测试全绿"现在基于已入库可追踪的文件（gitignore 已修），但正式进入协同/CI 前需 `git add` + commit。

---

## 进入真实项目试跑的前提

- P1 已闭环，真实模型能拿到 v2 资产 schema 并过门禁；
- 9/9 测试绿，含双模式；
- 唯一建议：先 `git commit` 把修复固化，再跑一个小型真实项目在线冒烟（不依赖伪宿主），重点观察 B/C 层基线产出是否真的被模型写成 v2 格式、以及综合审查 coverage 是否填满 6 项。

Round 10 担心的"伪宿主掩盖真实阻断"本轮已通过文档+动作卡+schema 三位一体闭环消除。
