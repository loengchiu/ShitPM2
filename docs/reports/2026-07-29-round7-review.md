# ShitPM 第七轮全量对抗性审查（大迭代回归版）

> 日期：2026-07-29
> 触发：用户称"又做了一次大迭代"，要求从头全量对抗性审查
> 方法：不信任记忆、不信任描述性文字、全部实测验证；结论与代码/运行结果对齐
> 基线：第六轮报告 `docs/reports/2026-07-29-context-loading-round6-review.md`

## Verdict：不通过（2 项 P0，3 项 P1，4 项 P2，4 项 P3）

本轮"大迭代"在解决第6轮 P2/P3 的同时，引入了两个 P0 级回归：

1. **同一 commit 里 AGENTS.md 与 skill/contract/orchestrator 直接矛盾**——AGENTS.md 7.7.1（三次核心动作）、7.7.5（唯一下一动作）、8.10（第四次审查属无效做法）、8.11（主代理重规划属无效做法）四条硬规则，被 spm-design SKILL.md 第3、8节、design-orchestration-contract.md、design-orchestrator.py 在同一 commit 里直接推翻。仓库规则自相矛盾，下游无法判断以哪个为准。
2. **PRD 检查器在正常流程下必然阻断**——当 design.md 用 spm-design 5.2 强制的新格式（固定标题）、prd.md 用 PRD 标准格式（表格+粗体块）时，`prd-consistency-check.py` 实测 exit 1，4 个 design 实体全部被报为 missing。任何合规项目的 PRD 检查都会被阻断。

此外，本轮核心新增的 680 行 `design-orchestrator.py` 是**孤儿脚本**，从未被任何 skill 调用；第6轮 P2-1（context-runtime-check --require design-model 接线）是**假修**——skill 加了文字，但编排器从不产出 design-model.json/design-challenge.json，门禁即使被调用也必然失败。

---

## 一、本轮实际改了什么（基线）

修改（15 个文件，+1300 / -799 行）：
- `AGENTS.md` +157 行：新增第7节"运行编排与验收教训"（7.1-7.10）和第8节"已知无效做法"（8.1-8.13）。
- `skills/spm-design/SKILL.md` +384 行：引入"依赖图与 `ready_actions[]`"、A/B/C 三层并行、3.2 节层内并行描述。
- `scripts/python/context-budget.py` / `context-pack.py`：移除本地 `estimate_tokens`，改 import `token_estimate.py`；context-pack 新增 `duration_ms` / `metrics_dir` 参数。
- `scripts/python/prd-consistency-check.py` +178 行：新增 `indexed_active` 分支，调用 `design-index.py:extract_document_entities` 解析 PRD。
- `scripts/python/prototype-consistency-check.py` +88 行：新增 `load_verified_index` 硬依赖。
- `contracts/subagent-context-contract.md` / `contracts/design-review-checklist.md` / `references/design-quality-rubric.md`（+323）/ `references/design-writing.md`（+371）/ `templates/design.md`（+185）：写作规则与模板对齐 5.2 节固定属性结构。
- `skills/spm-align/SKILL.md` +9 行：复用材料资产、不重复建索引。

新增（未跟踪）：
- `scripts/python/design-orchestrator.py`（680 行）：完整模式 25+ 节点依赖图，`init/next/accept/answer/status` CLI。
- `scripts/python/design-index.py`（538 行）：从 design.md 提取页面/区块/字段/操作固定结构实体。
- `scripts/python/source-index.py` / `context-runtime-check.py` / `context-run.py` / `token_estimate.py`：第6轮新增，本轮未变。
- `scripts/python/fake-design-host.py` / `test-design-orchestrator.py` / `test-design-orchestration-replay.py` / `test-design-index.py` / `test-context-runtime.py`：测试。
- `contracts/design-orchestration-contract.md` / `schemas/design-orchestration-action.schema.json`：编排契约与 schema。
- `docs/plans/`（11 个文档）/ `docs/wiki/`（1 个）/ `docs/reports/`（2 个）。

测试现状（实测）：
- `test-design-orchestrator.py` PASS（5 用例，0 模型调用）
- `test-context-runtime.py` PASS（含计时冒烟：强制重建 95.1ms / 复用 94.1ms）
- `test-context-loading.py` PASS
- `state-machine-check.py` 调用方式变更（不再是位置参数）

第6轮 P2-1 / P3-1 / P3-2 / P3-3 / P3-4 / P3-5 全部表面修复（详见下文 P1-2 与"值得肯定"段）。

---

## 二、P0（阻断级，必须立即修）

### P0-1 — AGENTS.md 7.7/8.10/8.11 与本轮 skill/contract/orchestrator 在同一 commit 里直接矛盾

AGENTS.md 第7节开头明文："以下规则来自真实项目运行、冷启动、编排测试和宿主验收中已经确认的问题，**后续设计、实现和测试必须遵守**。"本轮在同一 commit 里既新增了这些硬规则，又新增了直接违反它们的 skill/contract/orchestrator：

| AGENTS.md 硬规则 | 本轮直接违反处 |
|---|---|
| 7.7.1 "完整模式主路径默认只有**三次核心模型动作**：分析、业务模型挑战、Design 写作并在写作内自查" | `skills/spm-design/SKILL.md:209` "不固定'三次核心调用'或任何固定模型调用次数"；`design-orchestrator.py:258-286` 完整模式 task_definitions 共 **25+ 个专项动作**（a1-a5、b1-b6、c1-c4）+ 3 个独立生成内检查 |
| 7.7.5 "**编排器每次只返回一个确定的下一动作**，主代理不得自行重新规划完整流程" | `skills/spm-design/SKILL.md:34` "编排器每轮返回当前所有已满足依赖的 `ready_actions[]`，数量可以是 0、1 或多个"；`SKILL.md:208` "不把 `ready_actions[]` 重新压成唯一下一动作"；`design-orchestration-contract.md:46` "A/B/C 专项同批动作通过 `ready_actions[]` 并行"；`design-orchestrator.py:482-484` 一次返回所有 ready 动作 |
| 8.10 "把第四次独立成品审查作为完整模式固定动作属**已知无效做法**" | `design-orchestrator.py:283-284` 把 `review-pm-readability` / `review-park-coverage` / `review-downstream-sufficiency` 三类生成内检查作为独立动作 |
| 8.11 "让主代理根据长对话自行重新规划完整流程属**已知无效做法**" | `skills/spm-design/SKILL.md:78` "主对话只处理模式选择、用户问题、动作回执和完成报告，**不自行重排依赖**"——这一条本身合规，但 SKILL.md 第3节"依赖图与 ready_actions[]"整体设计允许主对话在多 ready 动作间选择，与 7.7.5 张力 |

**后果**：仓库规则自相矛盾。下游 PRD/Review/Skill 不知道以 AGENTS.md 还是 SKILL.md 为准。例如，按 AGENTS.md 7.7.1 完整模式应只有三次核心模型动作，按 SKILL.md/编排器却有 25+ 次——产品经理无法判断实际模型调用次数，违反 7.10"实际模型调用次数必须明确写出"。

**修复**（二选一，不能并存）：
- 方案 A：用户认为 25+ 专项并行是新方向，则改 AGENTS.md 7.7.1/7.7.5/8.10/8.11，明确推翻旧教训。
- 方案 B：用户认为三次核心动作仍是基线，则删 design-orchestrator.py 的 25+ 节点依赖图，回到三次核心动作；SKILL.md 第3、8节删掉"不固定三次核心调用""不把 ready_actions[] 压成唯一下一动作"。

**不能继续并存**。这是阻断级，必须在任何下游使用前解决。

### P0-2 — PRD 检查器在正常流程下必然 exit 1，阻断 spm-prd 流水线

实测复现（`/tmp/shitpm-p0-test/`）：
- 用 spm-design SKILL.md 5.2 强制的新格式写 design.md（`### 页面：登录页` / `#### 区块：登录表单` / `##### 字段：用户名` / `##### 操作：登录` 固定标题 + 固定属性）
- 用 PRD 标准格式写 prd.md（`**1.1.1 登录页**` 粗体块 + 7 列字段表）
- `design-index.py compile` 正确编译出 pages:1 / blocks:1 / fields:1 / operations:1
- `prd-consistency-check.py` 报告 `total_missing: 4`（页面+区块+字段+操作全部 missing）、`exit_reason: "possible_omission"`
- **真实 exit code: 1**

根因（`prd-consistency-check.py:1141-1148`）：
```python
def _compare_indexed_structure(index, content, index_module):
    expected = _indexed_expected_entities(index)
    actual_nodes = index_module.extract_document_entities(content)  # ← 用错解析器
    actual = [_indexed_entity_key(item) for item in actual_nodes]
    ...
    missing = [item for item in expected if _indexed_entity_key(item) not in actual_keys]
```

`index_module.extract_document_entities` 是 `design-index.py:379` 的函数，注释明文："提取下游文档中使用**同一固定标题结构**的实体"。它通过 `_split_heading_lines` 只识别 `### 页面：`/`##### 字段：` 等固定标题。但 PRD 模板（`templates/prd.md`）和 `spm-prd/SKILL.md` 规定 PRD 用 **7 列字段表 + `**N.N.N.N 页面名**` 粗体块**，不是固定标题。结果：`actual_nodes` 恒为空，`expected` 全部被报为 missing。

同时 `prd-consistency-check.py:1295-1300` 的 `if indexed_active:` 分支把 legacy 字段/页面/属性/枚举/内部字段检查整段置空跳过，导致 indexed_active 时没有任何 fallback 路径。

**后果**：任何按 spm-design 5.2 写的合规 design.md + 按 spm-prd 标准格式写的合规 prd.md，PRD 检查器**必然 exit 1**。这违反 AGENTS.md 7.8"合成测试未通过时真实项目验收必须暂停"——但本轮根本没有合成测试覆盖这条路径（test-shitpm-regression.py 用的是旧表格格式 design.md，规避了此 bug）。

**修复**（二选一）：
- indexed_active 分支改用 PRD 专用提取器（如 `extract_prd_fields` / `extract_prd_pages`），不要复用 design 的 `extract_document_entities`。
- 或保留 legacy 检查路径作为 fallback，indexed_active 仅作补充而非替代。

---

## 三、P1（必须修）

### P1-1 — `design-orchestrator.py` 是孤儿，从未被任何 skill 调用

全仓 grep 实测：
- `skills/spm-design/SKILL.md`、`skills/spm-align/SKILL.md`、`skills/spm-prd/SKILL.md` 引用 `design-orchestrator` **零命中**
- `scripts/python/stage-context.py`、`stage-prep.py` 零命中
- 只有 `fake-design-host.py:12`、`test-design-orchestrator.py:12`、`test-design-orchestration-replay.py:14` 引用（均为零模型测试）

`skills/spm-design/SKILL.md:80` 只调用 `context-pack.py` 和 `context-runtime-check.py`，全文无 `design-orchestrator.py`。

**后果**：本轮"大迭代"核心新增的 680 行编排器 + 25+ 节点依赖图**实际不会跑**。SKILL.md 第3节"编排器每轮返回 ready_actions[]"是空话——skill 流程里从没调用编排器。所有"层内并行""依赖图""ready_actions[]"描述对实际运行无效。

**修复**：在 spm-design 流程里显式接入 `design-orchestrator.py init/next/accept`，或删掉编排器和相关描述。当前是"写了不用"的最坏状态。

### P1-2 — 第6轮 P2-1 假修：`context-runtime-check --require design-model/design-challenge` 仍从未被真正调用

第6轮 P2-1 要求"在 spm-design 写完 design-model.json 后插入 context-runtime-check --require design-model"。本轮 `skills/spm-design/SKILL.md:80` 加了文字：
> "在读取兼容性交接包时执行 `python scripts/python/context-runtime-check.py --stage design --require design-model --require design-challenge`"

但三重悬空：
1. **这只是描述性段落**（3.2 节"完整模式的层内并行"末尾），不是具体步骤，没有"步骤 N：执行此命令"。
2. **没有任何任务产出 design-model.json 或 design-challenge.json**。`design-orchestrator.py:275` 的 `b6-model-review` 产出 `b-baseline.json` + `business-conflicts.json`；`:281` 的 `c4-cross-layer-review` 产出 `c-baseline.json` + `cross-layer-conflicts.json` + `design-brief.json`。`expected_outputs` 里完全没有 `design-model.json` 或 `design-challenge.json`。
3. **编排器本身也没被 skill 调用**（见 P1-1）。

`context-runtime-check.py:187-189` 期望从 `.workflow/runtime/context/design/handoff/design-model.json` 和 `design-challenge.json` 读取。但全仓只有 `test-context-runtime.py:141-155` 会创建这两个文件（测试 fixture）。生产路径下这两个文件永远不会存在。

**后果**：第6轮 P2-1 表面修复实质未修。契约（`subagent-context-contract.md:48`）"所有交接必须通过 context-runtime-check.py 的来源、版本和体量检查后才能被主 Agent 采纳"对 design-model / design-challenge 这两个最关键交接**仍完全架空**。如果按 SKILL.md:80 字面执行，门禁会直接报"文件不存在"失败。

**修复**（三选一）：
- 让编排器的 b6-model-review 产出 `design-model.json`、c4-cross-layer-review 产出 `design-challenge.json`，文件名与门禁期望对齐；并在 skill 流程的具体步骤里调用 `context-runtime-check --require`。
- 或修改门禁期望，改为校验 `b-baseline.json` / `c-baseline.json` 等编排器实际产出的文件。
- 或删除 SKILL.md:80 那句空话，明文承认本轮不实现 design-model/design-challenge 交接门禁。

### P1-3 — `docs/plans/` 引用不存在的 `test-design-orchestration-online.py`

实测：
- `docs/plans/2026-07-29-design-orchestration-low-cost-test-plan.md:745,776-778` 写 `python scripts/python/test-design-orchestration-online.py --scenario ...`
- `docs/plans/2026-07-29-design-orchestration-implementation-and-test-runbook.md:224,225,237` 同样
- `scripts/python/` 下**无此文件**
- `AGENTS.md:247-249`（8.12）明文："当前工作区没有 `scripts/python/test-design-orchestration-online.py`。**在脚本不存在时，不能再次尝试按该命令运行，也不能把它写成已通过**；必须先补齐测试实现或明确报告在线测试无法执行。"

**后果**：plan 文档与 AGENTS.md 8.12 直接冲突。照 plan 执行必报 FileNotFoundError。这违反 7.5.5"测试文档引用的脚本必须真实存在"。

**修复**：补齐 `test-design-orchestration-online.py`，或在两份 plan 中将这些命令标注为"待实现/不可运行"。

---

## 四、P2（建议修）

### P2-1 — `design-index.py` 对旧格式 design.md 静默返回空索引，下游检查器误报

实测：`test-fixture/output/design/design.md` 用表格格式（`| 页面 | 页面类型 | 核心用途 |`），`design-index.py compile` 返回 `pages:0 / fields:0 / operations:0 / blocks:0` **不报错**。下游 `prd-consistency-check.py` 拿到空索引，对比时把所有 PRD 实体误报为 hallucinated（实测 `total_hallucinated: 1`）。

**修复**：`design-index.py` 检测到无固定标题时 warning 或 exit 非 0；或更新 `test-fixture/output/design/design.md` 为新格式。

### P2-2 — `design-orchestration-contract.md` 与 `design-orchestration-action.schema.json` 未被任何脚本/skill 加载

`design-orchestrator.py:494` 内联 `validate_task_contract`，required 清单写死在 `:495`。`contract` / `schema` 仅被 `docs/plans`、`docs/reports`、`design-rule-cache`（JSON 缓存）引用，无 skill 引用，orchestrator 也不读取 schema 文件做 jsonschema 校验。

**后果**：契约/schema 与代码校验易漂移。schema 加字段，orchestrator 不校验；orchestrator 加字段，schema 不同步。

**修复**：让 orchestrator 加载 schema 做 jsonschema 校验，或在 contract 标注"仅文档，代码以 orchestrator 内联校验为准"。

### P2-3 — `references/design-writing.md` 章节编号错乱

实测：存在两个 `## 六、`（line 18 "六、常见错误"；line 197 "六、最终 Design 的表达原则"），且 "七"（line 177）在第二个 "六"（line 197）之前。实际顺序 6→1→2→3→4→5→7→6，目录（line 7-15）只列一个"六"。

**修复**：后者改为"八"并更新目录，或并入"七"。

### P2-4 — `test-fixture/design-index/` 不存在但被 plan 当作可运行 fixture

`docs/plans/2026-07-29-park-quality-design-acceptance-plan.md:131-134,326-327` 引用 `D:\work\ShitPM\test-fixture\design-index\{valid,missing-field-attribute,duplicate-page,invalid-hierarchy}` 并 instruct 运行 `design-index.py compile/check`。实测 `test-fixture/` 下只有 `design-orchestration/`、`output/`、`v2-remediation/`，无 `design-index/`。实际 `test-design-index.py:90-92` 用 tempfile 自建，不依赖该目录。

**修复**：补 fixture 或删除 plan 中对应命令。

---

## 五、P3（可选）

### P3-1 — 第6轮报告结论已过时

`docs/reports/2026-07-29-context-loading-round6-review.md` 仍把 P3-1（token_estimate 抽取）/ P3-2（source-index facts.json 悬空引用）列为待修。但代码已修复：
- `context-budget.py:8` / `context-pack.py:11` / `context-run.py:10` / `context-runtime-check.py:10` / `source-index.py:13` 全部 `from token_estimate import estimate_tokens`
- `source-index.py` grep `facts_path|facts_reused` 零命中

**修复**：在报告标注 P3-1/P3-2 已解决。

### P3-2 — `prd-consistency-check.py:493` `perm_ranges` 与 `:457` `candidate_ranges` 参数完全重复

可直接复用。

### P3-3 — `prd-consistency-check.py:1369` indexed_active 时 `total_attribute_mismatch` 与 `total_deterministic_attribute_mismatch` 恒等

二者均加 `len(indexed_result["attribute_mismatch"])`，`needs_semantic_judgment` 分支不可达。非 bug，语义冗余。

### P3-4 — `skills/spm-align/SKILL.md:37` 引用 `source-index.json` 未指明由哪个脚本生成

读者需自行关联 `source-index.py`。建议补脚本名。

---

## 六、值得肯定的（做对了的部分）

- **第6轮 P3-1 已修**：`token_estimate.py` 抽取完成，5 处全部 import，公式统一。这是本轮最干净的修复。
- **第6轮 P3-2 已修**：`source-index.py` 的 `facts_path` / `facts_reused` 悬空字段已清除。
- **第6轮 P3-3 已修**：`test-context-runtime.py:119` `if False else None` 死代码已删。
- **第6轮 P3-4 已修**：`context-runtime-check.py:151-155` 魔法数字加了注释"这些上限只限制隔离交接包的体量，防止上下文再次膨胀；它们不是产品完整性、字段数量或业务复杂度门槛"。
- **第6轮 P3-5 已修**：`test-context-runtime.py` 新增计时冒烟（强制重建 95.1ms / 复用 94.1ms，明文"仅记录，不以小样例推断真实模型提速"）。
- **测试套件全绿**：`test-design-orchestrator` / `test-context-runtime` / `test-context-loading` / `test-design-index` 全 PASS。
- **AGENTS.md 第7、8节本身写得清楚**：7.7/7.8/7.10 和 8.1-8.13 把历次教训固化成硬规则，方向正确——只是被同一 commit 里的 skill/contract/orchestrator 推翻了。

---

## 七、提交前建议清单

| 优先级 | 项 | 动作 |
|--------|----|------|
| **P0** | P0-1 | 解决 AGENTS.md 7.7/8.10/8.11 与 SKILL.md/contract/orchestrator 的直接矛盾——要么改 AGENTS.md 推翻旧教训，要么删 orchestrator 25+ 节点回到三次核心动作。**不能并存。** |
| **P0** | P0-2 | 修 `prd-consistency-check.py:1143` indexed_active 分支，改用 PRD 专用提取器或保留 legacy fallback。实测合规 design+prd 必然 exit 1。 |
| **P1** | P1-1 | 决定 `design-orchestrator.py` 去留：要么接入 spm-design 流程，要么删除。当前是"680 行孤儿"。 |
| **P1** | P1-2 | 落实第6轮 P2-1：让编排器产出 `design-model.json`/`design-challenge.json`，或在 skill 具体步骤里调用 `context-runtime-check --require`。当前是文字修复、实质未修。 |
| **P1** | P1-3 | 补 `test-design-orchestration-online.py` 或在 plan 中标注"待实现"。违反 AGENTS.md 8.12。 |
| P2 | P2-1 | `design-index.py` 对旧格式静默返回空索引问题。 |
| P2 | P2-2 | `design-orchestration-contract.md` / schema 与 orchestrator 校验对接。 |
| P2 | P2-3 | `design-writing.md` 章节编号错乱。 |
| P2 | P2-4 | `test-fixture/design-index/` 缺失或 plan 命令删除。 |
| P3 | P3-1 | 第6轮报告标注 P3-1/P3-2 已解决。 |
| P3 | P3-2/3/4 | 小冗余与文档补全。 |

---

## 八、与第6轮的对比

| 维度 | 第6轮 | 第7轮 |
|------|-------|-------|
| Verdict | 通过（无 P0/P1，1 P2，6 P3） | **不通过（2 P0，3 P1，4 P2，4 P3）** |
| 第6轮 P2-1（design-model 门禁接线） | 未修 | **假修**（加了文字，编排器不产出对应文件） |
| 第6轮 P3-1（token_estimate 抽取） | 未修 | **已修**（5 处全 import） |
| 第6轮 P3-2（source-index facts 悬空） | 未修 | **已修** |
| 第6轮 P3-3（死代码） | 未修 | **已修** |
| 第6轮 P3-4（魔法数字） | 未修 | **已修**（加注释） |
| 第6轮 P3-5（提速基准） | 未修 | **已修**（计时冒烟） |
| 第6轮 P3-6（facts 意图绑定） | 未修 | 未修（仍可选增强） |
| 新增 P0 | 0 | **2**（AGENTS.md 矛盾 + PRD 检查器阻断） |
| 新增 P1 | 0 | **3**（编排器孤儿 + P2-1 假修 + 在线测试脚本悬空） |

**总结**：本轮"大迭代"在清理第6轮 P3 方面做得干净（5 项 P3 全修），但引入了两个 P0 级回归。核心问题是**新增的编排架构（design-orchestrator.py + 25+ 节点依赖图 + ready_actions[]）既违反 AGENTS.md 7.7/8.10/8.11，又是孤儿脚本从未被 skill 调用**——这是"写了不用、用了违规"的最坏状态。同时 PRD 检查器在 indexed_active 分支用错解析器，正常流程下必然阻断。建议先解决 P0-1（决定编排架构方向）和 P0-2（修 PRD 检查器），再处理 P1-1/P1-2（编排器接入或删除、P2-1 真修），然后才能进入任何真实项目验收。
