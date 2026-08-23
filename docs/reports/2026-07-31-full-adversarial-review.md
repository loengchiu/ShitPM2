# Simplification 后全量对抗性审查（2026-07-31）

> 范围：simplification 对抗性审查（`2026-07-30-simplification-adversarial-review.md`）闭环之后，working tree 中全部未提交改动。
> 立场：找问题，不打勾。结论以真实文件当前态为准。
> 第一轮只审了 PRD 批次（见同目录 `2026-07-31-prd-batch-adversarial-review.md`），本轮补齐 align/design/contracts 批次并合并为全量。

## 1. 审查范围

| 批次 | 涉及文件 |
|---|---|
| PRD 承接缺口修复 + 角色×状态联动 | templates/prd.md、references/prd-writing-rules.md、references/prd-glossary-format.md、skills/spm-prd/SKILL.md、test-fixture/output/prd/prd-new-sample.md、prd-5.1-skill-generated.md |
| AGENTS.md §2 扩充 | AGENTS.md |
| Align | skills/spm-align/SKILL.md、templates/align.md、references/align-writing.md |
| Design skill/模板 | skills/spm-design/SKILL.md、skills/spm-design-review/SKILL.md、skills/spm-fix/SKILL.md、templates/design.md |
| Design references | references/design-methodology.md、design-state-format.md、design-writing.md、design-analysis-protocol.md、design-baseline-format.md(新)、design-fact-format.md(新) |
| Contracts + schemas | contracts/design-orchestration-contract.md、design-review-checklist.md、start-action-matrix.md、subagent-context-contract.md、metadata-anchor-rules.md、context-loading.manifest.json、schemas/design-orchestration-action.schema.json |

scripts 侧（design-orchestrator.py / design-confirmation.py / design-index.py / stage-prep.py 等）在 simplification 那轮已审，本轮不重复，仅核对其调用是否在 skill/contract 层留有死引用。

## 2. 结论摘要

- **P0：0**
- **P1：8**
- **P2：11**
- **整体**：主干可放行，无致命缺陷。P1 全部是"改了规则/动作没同步配套文件"或"契约与代码实际动作名对不上"——属配置漂移，不是设计错误，修法均为单点改动。

## 3. P1 发现

### P1-1 模板保留规则已禁的独立"模块业务对象及关系"标题（PRD）
- 证据：`templates/prd.md:54,102` 注释骨架仍示范独立标题；`prd-writing-rules.md:55` 规则 6.2.4 明确"不单独起标题"；`prd-glossary-format.md:70` 引用该已删标题。
- 影响：AI 按模板生成会产出违反 6.2.4 的独立标题。
- 修法：删模板两处标题行；glossary 第 70 行改为"与各大模块职责段落提到的业务对象名称一致"。

### P1-2 design SKILL §7 自检未承接状态机闭环8规则
- 证据：`skills/spm-design/SKILL.md:89` §7 仅"状态到出路"一句；`references/design-state-format.md:36-49` 定义4结构+4业务共8条闭环规则。
- 影响：状态机断链（孤岛/二次流转死锁/操作人错配）这类高频质量问题不进自检，靠 LLM 自由发挥，与 AGENTS.md §1 #5"状态合理性优先写入 Skill 自检清单"冲突。
- 修法：§7 自检展开，或显式引用 state-format §闭环要求，至少点名"非终态有出路/非初始态有入路/回退合法/无歧义/出路全覆盖/二次流转闭环/操作人匹配"。

### P1-3 design SKILL §7 未承接字段表8列与逐行无合并
- 证据：`SKILL.md:89`"页面到字段和操作"过抽象；`design-writing.md:84-95` 强制8列、:95 禁合并、:190 逐行无代表字段。
- 影响：字段表偷工（合并字段、缺列）不进自检，是 PRD 字段表问题的上游根因。
- 修法：§7 增"字段表八列齐全、每个字段单独一行无合并、页面落点与定义对齐"。

### P1-4 templates/design.md 状态模板列缺操作人
- 证据：`templates/design.md:91` §5 关键对象生命周期列项为"状态含义/进入条件/可执行动作/下一状态/限制条件/终态"，缺"操作人"；`design-state-format.md:5,18` 和 `design-writing.md:151` 均强制6列含操作人。
- 影响：按模板写状态机漏操作人，下游 PRD 状态机表也跟着漏。
- 修法：模板 §5 列项补"操作人"。

### P1-5 spm-design-review 失败处理自相矛盾
- 证据：`skills/spm-design-review/SKILL.md:42`"预检查脚本失败"与 :45"不运行 stage-prep.py"冲突；执行流程（23-32）未跑任何预检查脚本。
- 影响：reviewer 不知该查哪个脚本，预检查条款成死规则。
- 修法：删 :42 预检查条款，或指明具体脚本；与 simplification 后"review 不依赖脚本预检查"方向一致应删。

### P1-6 subagent-context-contract 引用已废动作名 b6/c4
- 证据：`contracts/subagent-context-contract.md:21` 声明"业务模型挑战由 `b6-model-review` 和 `c4-cross-layer-review` 承担"；`design-orchestrator.py:282-323` 实际 task_id 是 `a-layer`/`b-layer`/`c-layer`/`design-editor`。
- 影响：阅读契约者去找不存在的 b6/c4 动作卡；与 baseline-format.md 落点表（a-baseline/b-baseline/c-baseline）命名不符。
- 修法：b6→b-layer，c4→c-layer。

### P1-7 Design Challenger 角色定性自相矛盾
- 证据：`subagent-context-contract.md:19` 标"旧版兼容角色；v2 由模型审查动作承担"，但 :38 白名单与 `context-loading.manifest.json` `subagent_roles.design-challenger` 仍列为活跃可授权角色。
- 影响：执行者无法判断 design-challenger 是否还可申领。
- 修法：二选一——仍活跃则删"旧版兼容"措辞；已废则从 manifest 与白名单同步移除。

### P1-8 design SKILL §6 阅读清单漏 state-format 与 analysis-protocol
- 证据：`skills/spm-design/SKILL.md:83` 仅列 writing/methodology/fact-format/baseline-format 四个 references；但 §7 需状态机规则（state-format）、§4 需 ABC 协议（analysis-protocol）。
- 影响：context-loading.manifest 装载可能漏载这两份规则，自检无据。
- 修法：§6 补列 `design-state-format.md` 与 `design-analysis-protocol.md`。

## 4. P2 发现

### PRD 批次（沿用第一轮报告，此处摘要）

- **P2-A** prd-new-sample.md 4 处违规（删除缺执行角色/状态含义&流程图错层/字段表拆3表），不可作基线，印证 memory。
- **P2-B** prd-5.1 只是单模块片段，文件却声称"其余11模块按同流程生成"未兑现，不能作全文档基线。
- **P2-C** 承接缺口①（design 用户场景与目标）在 PRD 无落点，待用户确认是有意不补还是遗漏。
- **P2-D** design 操作列"按状态和权限显示"笼统 vs PRD 要展开，上下游张力。
- **P2-E** test-fixture 旧对照文件遍布违规写法有误学风险，建议加 README 或移 legacy/。
- **P2-F** spm-prd 自检未覆盖 6.2.8/6.2.9 状态含义与流程图层级。

### Design/Contracts 批次

- **P2-G** design-writing.md 目录第 14 行从"五"跳到"七"，漏"六、最终 Design 的表达原则"（正文 :159 有该节）。
- **P2-H** design-baseline-format 与 design-fact-format schema 不自洽：baseline `source_refs` 不绑 `material_revision`，fact 强制绑；baseline 用 `schema_version`，合并 facts.json 用 `version`；字段名 `source_refs` vs `source` 不一致。建议 baseline 增可选 `material_revision`。
- **P2-I** design-writing.md 闭环要素数不一致：:155 列7要素，templates/design.md:59 速览列6要素，SKILL §7 未指定权威清单。建议统一一份并互相引用。
- **P2-J** design-writing.md:192 第6条"正文无 metadata/稳定 ID/编排回执"未入 design SKILL §7 自检。
- **P2-K** schemas/design-orchestration-action.schema.json:9 `type` enum 仍含 `"report_completed"`，orchestrator 已无此动作发射（simplification 移除 report-completed 调用）。
- **P2-L** subagent-context-contract.md:47 仍强约束"所有交接必须通过 context-runtime-check.py"，但 orchestrator 已不调用该脚本；subagent 路径是否仍走该校验未说明，可能残留隐性硬门。

## 5. 正面结论（已验证合规）

- **AGENTS.md §2 不与 §1/USAGE 重复**：USAGE.md 仅含运行时命令，无 skill 编写原则；§2 的 11 条中 §2.3"指令优先"明确标注与 §1 #6 交叉引用，其余为 §1 未覆盖新内容；§2 未引入新工具/回执/中间结构，符合 §1 #8/#9 简化原则。
- **4 个已删脚本零活动引用**：review-precheck/state-machine-check/verify-against-metadata/artifact-guard 在 skills/references/contracts 层 grep 零命中，仅存于 docs/plans 与 docs/reports（历史记录，预期）。
- **多状态机独立标题规则已闭环**：state-format.md:13 明确 H3/H4 均可，与 stage-prep 修复一致。
- **align SKILL+模板+writing 一致**：align 定位（必经、不替用户拍板、完整保留、可复用）、产物结构、停止语义三者对齐，无 footgun（不甩命令、不自动推进 Design 之外的下游）。
- **spm-prd 无 footgun**：confirm 范式正确，"不得在用户未明确确认前运行 confirm"显式约束，命令一律 AI 执行。
- **承接缺口②③④⑤ 已就近补齐**（PRD）：对象关系/数据范围+敏感操作/外部协作/闭环详细动作均有规则+自检落点。
- **skill 真跑产物合规度优于手工样例**：证明 spm-prd skill 流程可产出符合新规则的 PRD。
- **start-action-matrix 与代码同为旧范式**：双门方案未落地属"已知待落地"，contract 与代码当前一致，无 contract 抢跑（不计为新发现）。

## 6. 整体结论与建议

主干可放行，无 P0。8 个 P1 全是配置漂移（改规则没改配套、契约动作名与代码对不上、自检没承接 references 约束），修法均为单点改动，不涉及流程重构或新机制。

建议处理顺序：
1. **P1 批量修**（模板/glossary/契约动作名/自检承接/阅读清单），预计单点改动 8 处。
2. **决定 P2-C**（用户场景缺口是有意不补还是遗漏）。
3. **决定样例策略**（P2-A/P2-B）：是否用 skill 真跑完整 12 模块 PRD 作新基线。
4. **P2 余项**为改进项，可后续处理。

本审查未修改任何代码或规则文件，仅产出本报告。
