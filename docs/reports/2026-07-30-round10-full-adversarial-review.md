# ShitPM 全量对抗性审查（Round 10，从零开始）

日期：2026-07-30
范围：本次迭代（新增 `full-layered` 层级实验路径 + 统一 `material_revision` 算法 + 表格格式 Design 门禁）后的完整仓库。
方法：不信任上一轮结论与验收报告，重新通读代码、构造最小复现、跑全量测试套件、逐项实证。
环境：`C:/Users/guduj/.workbuddy/binaries/python/versions/3.13.12/python.exe`，仓库根 `D:\work\ShitPM`，分支 `V2`（含 18 个未提交修改 + 5 个未跟踪文件）。

---

## 0. Verdict

**主线（合成项目 + 伪宿主）通过：无 P0，全部 9 项测试绿灯。**

但发现 **1 个 P1（真实运行阻断，被假宿主测试完全掩盖）**、**2 个 P2**、**若干 P3**。
最关键的 P1 不在"代码跑不通"，而在"程序对模型产出的契约要求，执行期文档与动作卡都没有传达"——这正是上一轮用伪宿主做验证时必然会漏掉的盲区。

> 一句话：这一轮把"编排起不来"的历史 P0 真修了，架构方向正确；但在踏入真实项目之前，必须先补"v2 交接/资产 JSON schema 的文档化"，否则 full 与 full-layered 两条主链都会在 B/C 层被门禁卡死。

---

## 一、本次迭代已真修好的强项（实证确认）

| # | 结论 | 实证方式 |
|---|---|---|
| S1 | **`material_revision` 算法已统一**，source-index 与 design-orchestrator 三处结果完全一致（历史 P0 修复） | 单独跑 source-index 生成 manifest，再用 orchestrator.material_revision 重算，`manifest==index==orchestrator: True` |
| S2 | **`full-layered` 任务图正确接线**：material-index→material-facts*→material-merge→a-layer→b-layer→c-layer→design-layered→review-comprehensive→compile-design-index→report-completed（design-orchestrator.py:281-289） | 代码通读 + test-design-simplification 通过 |
| S3 | **Design 写作接受前真门禁 A/B/C 基线**（提案 §6.1 满足）：`_validate_design_writer_upstream`（:660）先 `output_valid` 查四个基线文件存在，再 `_current_dependency_outputs`（:648）比对 a/b/c 层 receipt 输出哈希新鲜度 | 代码通读 |
| S4 | **Design 结构门禁正确且不超严格**：完全合规 design → `rc=0, ok=True, 0 errors`；缺页面属性/区块目的时给出精确错误 | 构造合规 design 实测 rc=0；构造缺属性 design 实测精确报错 |
| S5 | **模板/参考文档表头与门禁严格表头完全一致**（无模板-门禁错配） | `templates/design.md:132/146`、`references/design-writing.md:78/108` 与 `design-index.py` 的 `FIELD_TABLE_HEADERS`/`OPERATION_TABLE_HEADERS` 逐字一致 |
| S6 | **PRD 一致性检查器无回归**，历史 P0-2 修复保持（合规产物 EXIT 0，未触发 `indexed_active` 误杀） | 在含 401 字段/54 页的大 fixture 上跑 `prd-consistency-check.py` → `EXIT=0` |
| S7 | **SKILL↔契约↔schema 对 `full-layered` 自洽**，无悬空 `design-model`/`design-challenge` 引用（门禁 `--require` 同时支持 legacy 与 V2_HANDOFFS 六类，SKILL §3.3 引用合法） | `context-runtime-check.py:191` + grep 全仓 |
| S8 | **shitpm-host P1-A 修复保持**（AGENTS.md→README.md 判据） | `git diff scripts/python/shitpm-host.py` |
| S9 | **全量测试 9/9 通过** | 见第四节 |

---

## 二、对抗性发现

### P1（必须在进入真实项目前修复）—— v2 交接/资产 JSON schema 已强制，但执行期从未告诉模型

**事实链：**

1. `context-runtime-check.py:138-145` 的 `V2_HANDOFFS` 对 a/b/c-baseline、design-brief、business-conflicts、cross-layer-conflicts **强制要求**：
   - `schema_version == "design-analysis/v2"`
   - `task_id` 为非空字符串
   - `status in {"completed","success"}`
   - `coverage` 为 list、`source_refs` 为 list
2. `design-orchestrator.py:686-693` 的 `accept_outputs` 在 **b-layer / c-layer 接受时**真会调 `context-runtime-check --require b-baseline business-conflicts ...`（经 `_handoff_requirements` 映射）。不满足 → 拒绝采纳，流水线卡死。
3. 但执行期文档**完全没有规定这套 schema**：
   - grep `references/ skills/ contracts/ templates/`：**零命中** `design-analysis/v2` / `source_refs` / `coverage` 基线 schema。
   - 全仓唯一规定处是 `docs/plans/2026-07-29-park-quality-design-implementation-plan.md`（规划文档，非执行契约）。
   - `subagent-context-contract.md:21` 只讲基线"内容"（缺陷/影响/证据…），不讲 JSON 包装 schema。
4. 动作卡也不传达：`make_action`（`design-orchestrator.py:430`）给模型的 `output_schema` 是 `{"type":"object","required":[]}`，`completion_check` 只写"输出文件存在 / JSON 可解析 / 输入哈希匹配"——**没有要求 `design-analysis/v2`/`coverage`/`source_refs`**。

**后果（被测试掩盖）：**
- 真实模型写出的 `a-baseline.json` / `b-baseline.json` / `c-baseline.json` / `design-brief.json` / 两类 conflicts 几乎必然**不含 `coverage` 与 `source_refs` 这两个 list 字段，也不带 `schema_version: design-analysis/v2`**。
- 在 b-layer / c-layer 接受时，`context-runtime-check --require` 返回非 0 → `accept_outputs` 拒绝 → **full 与 full-layered 两条主链的真实运行都会在 B/C 层卡死**。
- 假宿主 `fake-design-host.py:36` **硬编码**了完整 schema（`schema_version/ task_id/ status/ coverage/ source_refs`），所以所有合成/回放测试都过——这正是假宿主验证必然漏掉的盲区。

**同类问题：** `material-facts` 的 `confirmed_facts/source_conflicts/missing_information/non_derivable_items` 固定键 + `source.path/sha256/line_start/line_end` 行范围（`context-runtime-check.py:127`），同样在执行文档里未规定，真实事实提取动作也会被 `--require material-facts` 拒。

**修复方向（建议二选一或结合）：**
- 新增 `references/design-baseline-format.md` 与 `references/design-fact-format.md`，规定 v2 资产 JSON schema，被 `skills/spm-design/SKILL.md`、`contracts/subagent-context-contract.md`、`contracts/design-orchestration-contract.md` 显式引用；
- 让 `make_action` 的 `output_schema`/`completion_check` 指向该 schema（至少要求 `schema_version`/`status`/`coverage`/`source_refs`），使动作卡本身传达约束；
- 可选：门禁对 `coverage`/`source_refs` 缺失给"文档未规定"式的友好错误，提示模型补齐而非静默失败。

**严重性说明：** 不算"代码 bug"，但属真实运行阻断。与本轮"未进入真实项目"的声明一致——这只是把"下一阶段必经的坑"提前暴露，而不是推翻本次迭代。

---

### P2（建议本迭代内修）—— 表格解析器对"表前说明文字"过度脆弱（本轮新引入）

**事实：**
- `design-index.py` 新增表格解析 `_table_after_heading`（diff 新增）：遇到 `##### 字段表`/`##### 操作表` 标题后，从下一行开始，**首个非空白/非注释行若不是表**，直接 `break`，`table_start=None` → 判 `invalid_field_table_headers`（"未找到有效表格"）+ `block_without_items`（"区块没有字段或操作"）。
- 实测：合规 design 仅在字段表前加一句"下面列出字段："，`--require-current-format` 即从 `rc=0` 变为 `rc=1`，**字段数从 1 掉到 0，整张字段表被静默丢弃**。

**后果：** 模型在表格前加一句引导语是极常见行为，会触发"字段/操作表丢失 → 门禁失败"。这是本轮新表格格式引入的脆弱性（旧 heading 格式无此问题）。

**修复：** 解析时跳过非表、非分隔行，直到遇到第一张有效表（而非首个非空白行就 break）。属于低风险局部改动。

---

### P2（建议修）—— 核心回归测试被 `.gitignore` 排除在版本控制外

**事实：** `.gitignore:29-32` 排除：
- `scripts/python/test-anti-hallucination.py`
- `scripts/python/test-context-loading.py`
- `scripts/python/test-resource-integrity.py`
- `scripts/python/test-shitpm-regression.py`（含 37 项回归检查，历史多轮反复依赖它做安全网）

**后果：** 验收报告"9 测试全绿"含 4 个未入库文件；克隆仓库或 CI 跑不到回归测试与上下文装载测试，**确定性安全网对团队实际不可见**。本轮"全量对抗性审查"若要可复现，必须让这些测试可入库。

**修复：** 若测试会污染仓库，改为写入临时目录/固定 fixture；否则纳入 VCS；或在 README/CI 明确"本地专用测试 + 等价入口"。

---

### P3（可选加固）

- **P3-1 门禁未独立复核上游基线 material_revision 新鲜度**：`_validate_design_writer_upstream` 只查基线文件存在 + 依赖 receipt 的 output_hashes 未变，不验证基线本身是用"当前 material_revision"算出的。正常流程因 `preview_next` 只在 a/b/c 层 fresh 时才把 design-layered 列为 ready 而间接安全；但若绕过 preview_next 直接 accept 陈旧 design-layered，门禁不拦。建议比对基线 receipt 的 input_hashes 含当前 material_revision 作纵深加固。

- **P3-2 验收报告"性能/耗时下降"基本是构造产物**：9,511ms→1,716ms 等来自 `fake-design-host` 按节点数模拟，节点少自然快，报告已声明"伪造宿主测量"。提醒：该数字只证明"图更小"，不等于真实宿主 token/压缩/耗时下降；真实对比须等在线数据。

- **P3-3 `review-comprehensive` 仅有结构门禁、无语义覆盖强制**：接受只查 `comprehensive.json` 存在 + design.md 结构；`status` 由 `preview_next` 的 `review_findings` 复核。模型可写 `status:passed` + 空 findings 通过。这与 full 模式三检查同构（model review 架构），可接受；建议综合审查契约明示"至少覆盖提案 §4.4 六类责任"，失败时用 repair 而非静默通过。

---

## 三、测试套件实测（9/9 通过，但 4 项未入库）

```
test-anti-hallucination.py        PASS（4 类幻觉均检出）
test-context-loading.py           PASS（manifest/章节/来源/去重/边界，含 full-layered）  [gitignored]
test-context-runtime.py           PASS（首建/复用/变更失效/增删来源/版本门禁）
test-design-index.py              PASS（15 用例）
test-design-orchestration-replay.py PASS（16 用例，模型调用 0）
test-design-orchestrator.py       PASS（7 用例）
test-design-simplification.py     PASS（三类合成项目对比/门禁/恢复，passed:true）
test-resource-integrity.py        PASS（路径/链接/目录/profile/stage-context/运行时边界） [gitignored]
test-shitpm-regression.py         PASS（37 通过 0 失败）                                  [gitignored]
```
> 标注 `[gitignored]` 的 4 项不随仓库入库（见 P2）。

全量测试均用**伪宿主/构造 fixture**，无法覆盖 P1 所述的"真实模型产出不达标线 schema"场景——这正是 P1 被漏掉的根因。

---

## 四、修复优先级建议

1. **P1（最高）**：文档化 v2 资产/交接 JSON schema + 让动作卡携带该 schema。否则真实项目无法跑通任意主链。**这是进入真实项目前的硬门槛。**
2. **P2**：修表格解析器对表前说明文字的脆弱性（低风险局部改）。
3. **P2**：把被 gitignore 的 4 个测试纳入版本控制或给出等价可复现入口。
4. **P3**：门禁纵深加固、验收表述澄清、综合审查语义覆盖明示。

---

## 五、结论

- 本轮迭代方向正确、历史 P0（material_revision 不一致导致编排起不来）**已真修并实证**，`full-layered` 实验路径接线与门禁正确。
- 但"用伪宿主做验证"的本质局限在本轮再次显现：**程序对模型产出的契约要求（v2 资产/交接 schema）在执行期文档与动作卡里完全缺位**，导致真实运行会在 B/C 层被门禁卡死。这是唯一必须在本轮收尾或下一阶段启动前解决的高优先级项。
- 在 P1 修复前，继续"只做合成/伪宿主验证、不进真实项目"是正确姿态（与验收报告结论一致）。
