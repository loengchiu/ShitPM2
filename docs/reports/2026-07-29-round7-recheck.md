# ShitPM 第七轮复审（AGENTS.md 第7/8节删除后）

> 日期：2026-07-29 23:35
> 触发：用户删除 AGENTS.md 第7节"运行编排与验收教训"和第8节"已知无效做法"（确认为过时内容），要求重跑审查
> 基线：`docs/reports/2026-07-29-round7-review.md`（第七轮首审）
> 方法：全部实测复核，不沿用首审结论

## Verdict：不通过（1 项 P0，2 项 P1，6 项 P2，4 项 P3）

用户拍板了首审 P0-1 的方向：**删 AGENTS.md 旧教训，保留 ready_actions[] 并行编排架构**。这个决定本身干净——冲突源消除，仓库规则不再自相矛盾。AGENTS.md 现在只剩产品契约（第2节 14 条）+ 工程原则，实测与 SKILL.md/contract/orchestrator 无冲突。

但其余问题与 AGENTS.md 无关，删文档修不掉代码：

## 一、首审问题逐项复核结果

| 首审编号 | 复核结果 | 说明 |
|---|---|---|
| P0-1（AGENTS.md 矛盾） | **已解决** | 第7/8节整体删除，`grep "三次核心\|唯一下一动作\|观察性试跑"` 在 skills/contracts/references 零命中（仅 docs/plans 历史文档残留，见 P2-5） |
| P0-2（PRD 检查器必然 exit 1） | **仍复现** | 2026-07-29 23:36 复测：新格式 design.md + 标准 prd.md → `exit_reason: possible_omission`，EXIT 1。代码未动，问题原样在 |
| P1-1（orchestrator 孤儿） | **仍成立** | `grep design-orchestrator skills/` 零命中；SKILL.md 第3节整节描述"编排器每轮返回 ready_actions[]"但全文无一条调用命令，也不引用 `design-orchestration-contract.md`。执行者无从知道要跑 `design-orchestrator.py next` |
| P1-2（交接门禁架空） | **仍成立且加重** | 见下文 P1-2' |
| P1-3（online 测试脚本悬空） | **降级 P2-5** | AGENTS.md 8.12 规则已删，不再构成契约违反；但 runbook 文档引用不存在的脚本仍是事实错误 |
| P2-1~P2-4 | **全部仍在** | design-index 对旧格式静默空索引（复测 EXIT 0, pages:0）；contract/schema 无人加载；design-writing.md 两个"## 六、"且顺序 6→1→2→3→4→5→7→6（复测确认）；test-fixture/design-index/ 不存在（复测确认） |
| P3-1~P3-4 | 全部仍在 | 未动 |

## 二、当前唯一 P0

### P0-2 — PRD 检查器在正常流程下必然 exit 1（原样未修）

复测：`prd-consistency-check.py:1143` indexed_active 分支用 `design-index.py:379 extract_document_entities` 解析 PRD，该函数只识别 design 的固定标题（`### 页面：`/`##### 字段：`），PRD 标准格式是 7 列表 + 粗体块 → `actual_nodes` 恒空 → 所有 design 实体报 missing → exit 1。

**这是当前阻断真实项目的唯一 P0。** 修复二选一：indexed_active 分支换 PRD 专用提取器；或保留 legacy 检查做 fallback。

## 三、P1（必须修）

### P1-1 — 编排器仍是 680 行孤儿

新基准下问题反而更纯粹：AGENTS.md 不再反对 ready_actions[] 架构，SKILL.md 第3节把它写成"当前 Design 契约"（:34"不存在'唯一下一动作'作为当前 Design 契约"），但**契约声称的执行机制在 skill 里没有任何接线**。SKILL.md:80 只调用 context-pack 和 context-runtime-check。

修复：在 SKILL.md 执行流程里写明 `python scripts/python/design-orchestrator.py init/next/accept` 的具体调用步骤，并引用 `contracts/design-orchestration-contract.md`；否则第3节整节是无法执行的描述。

### P1-2' — 交接门禁双向架空（首审 P1-2 的加重版）

两个方向都断：

1. **门禁等不到文件**：`context-runtime-check.py:162` 的 `--require` 只支持 5 种（material-manifest/index/facts、design-model、design-challenge）。SKILL.md:80 要求"读取兼容性交接包时"校验 design-model/design-challenge，但全仓无任何生产路径产出这两个文件（仅 test-context-runtime.py 测试 fixture 会造）。
2. **文件等不到门禁**：编排器实际交接物是 `b-baseline.json` / `c-baseline.json` / `design-brief.json` / `business-conflicts.json` / `cross-layer-conflicts.json`（design-orchestrator.py:275,281），门禁**没有对应的 --require 类型**，而 `subagent-context-contract.md:48` 明文"所有交接必须通过 context-runtime-check.py 检查后才能被主 Agent 采纳"。v2 的全部关键交接在门禁上无法校验。

修复：给 context-runtime-check 增加 b-baseline/c-baseline/design-brief 的 require 类型并在编排器 accept 时调用；同时决定 design-model/design-challenge 是保留兼容还是删除（若删除，SKILL.md:80 后半句和 --require 两个 choices 一起删）。

## 四、P2（建议修）

- **P2-1** design-index.py 对旧表格格式 design.md 静默返回空索引（EXIT 0），下游误报 hallucinated。
- **P2-2** design-orchestration-contract.md / action.schema.json 无人加载，与 orchestrator 内联校验（:495 required 写死）易漂移。
- **P2-3** references/design-writing.md 两个"## 六、"，实际顺序 6→1→2→3→4→5→7→6，目录不符。
- **P2-4** test-fixture/design-index/ 不存在，但 park-quality-design-acceptance-plan.md:131-134,326-327 当可运行 fixture 引用。
- **P2-5**（原 P1-3 降级）docs/plans 两份文档（low-cost-test-plan.md:745,776-778；implementation-and-test-runbook.md:224-225,237）引用不存在的 `test-design-orchestration-online.py`。runbook 自称可执行手册，照做必报 FileNotFoundError。补脚本或标注"待实现"。
- **P2-6**（新增）docs/plans 内两组方向相反的文档并存：design-orchestration-* 三份主张"唯一下一动作/三次核心调用"，park-quality-design-* 系列明文推翻（implementation-plan.md:41,122）。AGENTS.md 第2节"历史讨论仅审计"可勉强兜底，但没有任何标注说明哪组已作废。给旧方向三份文档头部加"已被 park-quality 系列取代"标注即可。

## 五、P3（可选，同首审）

P3-1 第6轮报告结论过时未标注；P3-2 prd-consistency-check.py:493 参数重复；P3-3 :1369 恒等冗余；P3-4 spm-align:37 未指明 source-index.json 生成脚本。

## 六、结论

删 AGENTS.md 第7/8节解决且只解决了 P0-1。方向争议消除后，剩下的是纯执行缺口，集中在两条线：

1. **PRD 检查线（P0-2 + P2-1）**：indexed_active 分支解析器用错 + 空索引静默通过。这条线不修，spm-prd 流水线对合规项目必然阻断。
2. **编排接线（P1-1 + P1-2' + P2-2）**：SKILL.md 声称的契约（ready_actions[]、交接门禁）与实际可执行路径之间全是断点。要么补接线，要么把声称降级为描述。

修完 P0-2 和两个 P1 之前，仍不建议进入真实项目验收。
