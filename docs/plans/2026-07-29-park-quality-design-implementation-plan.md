# Park 级质量 Design 编排实施计划

> 日期：2026-07-29  
> 状态：待执行  
> 仓库：`D:\work\ShitPM`  
> 设计基准：`docs/plans/2026-07-29-park-quality-pm-design-orchestration.md`  
> 约束：本计划只指导实施，不允许 Git commit，不允许 Git push。

## 1. 实施目标

把当前“材料事实 → 综合分析 → 业务模型挑战 → Design 写作”的单动作链，改造成同时支持简单模式和完整模式的新编排：

```text
简单模式
项目材料准备或复用
→ 最小闭环分析与统一写作
→ 生成内检查
→ Design 索引

完整模式
项目材料准备或复用
→ A 层需求理解
→ B 层业务建模与一致性审查
→ C 层产品承接与跨层审查
→ 全新上下文的设计总编统一写作
→ 三类并行成品检查
→ 有限局部修复
→ Design 索引
```

实施完成后必须同时解决三件事：

1. **质量**：完整模式保留 Park 级分析责任，最终 `design.md` 足以约束 PRD 和原型；
2. **上下文**：主任务只做调度、提问和完成报告，不读取原始材料正文和完整专项报告；
3. **时间**：同批无依赖专项可以并行，失败或修改只重跑受影响节点和下游。

## 2. 明确不做的事

本次不做以下事项：

- 不恢复“固定三次核心模型调用”；
- 不保留“一次只能返回一个动作”的限制；
- 不让主任务重新读取全部结果并亲自写 `design.md`；
- 不让多个专项子代理直接拼接最终 Design；
- 不用固定 token 上限截断业务结论；
- 不用 Hook；
- 不把 `fake-design-host.py` 的结果当成真实子代理证据；
- 不要求宿主先提供隐藏上下文或操作系统级文件审计，才允许继续产品测试；
- 不取消简单模式，也不让完整模式静默降级为简单模式；
- 不把数据库字段、表结构、接口结构等研发设计重新塞进 Design；
- 不删除或覆盖当前工作区中无法确认来源的既有修改。

## 3. 成功标准

实施代码完成不等于任务完成。必须满足：

- `spm-design` 仍只有简单模式和完整模式；
- 未指定模式时只询问一次；
- 简单模式不启动完整模式全部专项；
- 完整模式使用依赖图，并一次返回当前全部 `ready_actions`；
- 同批动作可分别完成、分别失败、分别恢复；
- 每个专项任务声明依赖、只读输入、禁止输入、输出、输入哈希和检查规则；
- 每个专项子代理和设计总编使用全新上下文，启动参数为 `fork_context=false`；
- 主任务收到的子代理回复为短回执，不包含分析正文；
- A、B、C 层均形成可复用的结构化基线；
- 最终由单一、全新上下文的设计总编写 `design.md`；
- 三类生成内成品检查并行执行；
- `design.md` 可确定性编译 `design-index.json`；
- PRD 和原型检查能识别页面、区块、字段、操作的遗漏、新增和语义改变；
- 材料未变化时不重新提取；
- 中断、单节点失败和用户局部决策不会触发全量重跑；
- 所有零模型测试和现有回归测试通过。

## 4. 现状盘点与迁移原则

当前工作区已有未提交修改。开始实施前必须先运行：

```powershell
git -C D:\work\ShitPM status --short
git -C D:\work\ShitPM diff --stat
git -C D:\work\ShitPM diff --name-only
```

不得使用 `git reset --hard`、`git clean` 或覆盖式还原。每个待改文件先看当前内容和差异，再做局部修改。

### 4.1 保留并复用

| 现有能力 | 处理方式 | 原因 |
| --- | --- | --- |
| 项目材料清单、来源索引、材料事实库 | 保留并接入新依赖图 | 避免 Design 重复读取原始材料 |
| 材料内容哈希和版本 | 保留 | 支持缓存与局部失效 |
| 规则包内容寻址缓存 | 保留，调整引用方式 | 静态规则可跨项目复用 |
| 输入哈希、输出来源信息 | 保留并扩展到每个节点 | 支持陈旧产物拒绝和恢复 |
| 自动重试上限 | 保留 | 防止无限循环 |
| 中断恢复 | 保留并从单动作扩展为多节点 | 支持长流程恢复 |
| `context-run.py` 指标记录 | 保留并扩展 | 记录节点耗时和声明输入体量 |
| 零模型、回放、合成在线、真实项目分层测试 | 保留测试思想 | 降低真实项目反复试跑成本 |

### 4.2 必须重写

| 文件或能力 | 当前问题 | 目标状态 |
| --- | --- | --- |
| `scripts/python/design-orchestrator.py` | 固定三段链、单个活动动作 | 两种模式、依赖图、`ready_actions[]`、多节点状态 |
| `contracts/design-orchestration-contract.md` | 明确禁止并行并固定三次调用 | 定义依赖、同批并行、短回执、局部失效和恢复 |
| `schemas/design-orchestration-action.schema.json` | 只描述单动作，缺少依赖和任务类别 | 支持专项任务、依赖、批次、问题和回执 |
| `scripts/python/fake-design-host.py` | 模拟旧三段流程 | 只作为新依赖图的零模型执行器 |
| `scripts/python/test-design-orchestrator.py` | 断言唯一下一动作和三次调用 | 断言两种模式、并行动作集合和节点失效 |
| `scripts/python/test-design-orchestration-replay.py` | 回放旧三段链 | 回放简单模式和完整模式依赖图 |
| `skills/spm-design/SKILL.md` | D1-D4 仍以大包和少数模型调用组织 | 主任务调度边界、两种模式和真实子代理执行规则 |
| `templates/design.md` | 面向研发规格，页面字段表达不稳定 | 面向产品经理的产品方案基线 |
| Design 写作、质量和 Review 规则 | 读者和检查重点偏研发 | 产品经理可读、Park 覆盖、下游可展开 |
| PRD、原型一致性检查 | 主要依赖旧表格和正文规则 | 优先读取由 Design 编译的索引 |

### 4.3 仅作历史保留，不得继续作为现行规范

以下文档不删除，但在 README 或文档头部标注“已被新设计取代”，不能再用作实施依据：

- `docs/plans/2026-07-29-design-orchestration-context-governance.md`
- `docs/plans/2026-07-29-design-orchestration-implementation-and-test-runbook.md`
- `docs/plans/2026-07-29-design-orchestration-low-cost-test-plan.md`

被取代的内容包括：固定三次模型调用、唯一下一动作、综合分析/挑战/写作固定链和把完整宿主审计作为进入测试的前置条件。

## 5. 运行时结构和事实边界

### 5.1 项目运行目录

新运行使用：

```text
.workflow/runtime/context/design/
├── inputs/
│   ├── request.json
│   ├── material-ref.json
│   └── user-decisions.json
├── tasks/
├── analysis/
│   ├── simple/
│   ├── a/
│   ├── b/
│   └── c/
├── baselines/
│   ├── a-baseline.json
│   ├── b-baseline.json
│   ├── c-baseline.json
│   └── design-brief.json
├── conflicts/
│   ├── business-conflicts.json
│   ├── cross-layer-conflicts.json
│   └── user-questions.json
├── reviews/
│   ├── pm-readability.json
│   ├── park-coverage.json
│   └── downstream-sufficiency.json
├── index/
│   └── design-index.json
├── receipts/
└── run.json
```

### 5.2 唯一产品事实源

- 运行目录中的专项结果、基线、问题账本、索引和回执都是内部运行记录；
- 用户确认后，只有 `output/design/design.md` 是 PRD 和原型的产品事实基线；
- `output/design/decision-notes.md` 只用于审计；
- `design-index.json` 只能从 `design.md` 提取，不能补充事实；
- PRD 和原型生成仍读取 `design.md`，索引只用于定位、覆盖和一致性检查。

### 5.3 旧运行兼容

新状态版本改为 `design-orchestration/v2`。

- 新 `init` 只创建 v2 运行；
- 读取到旧 v1 `run.json` 时不得猜测迁移；
- 返回明确的 `migration_required`，保留旧运行文件；
- 用户可另启新运行，或以后单独开发迁移工具；
- 本次不实现自动迁移，避免把旧三段产物误认成新基线。

## 6. 通用任务输出契约

每个模型专项输出一个 JSON 文件，至少包含：

```json
{
  "schema_version": "design-analysis/v2",
  "task_id": "a1-requirement-clarification",
  "input_fingerprint": "sha256:...",
  "status": "completed",
  "conclusions": [],
  "conflicts": [],
  "questions": [],
  "coverage": [],
  "source_refs": [],
  "payload": {}
}
```

要求：

- `conclusions` 区分事实、用户决策和明确推断；
- `source_refs` 引用材料事实 ID、用户决策 ID 或上游结论 ID；
- `questions` 使用 P0/P1/P2 分级；
- `coverage` 声明本任务已检查和不适用的责任；
- `payload` 保存该专项的领域结构；
- 不允许只有空泛摘要而没有可用于下游合并的结论；
- 程序只检查结构、哈希、引用和必填字段，不判断业务结论是否合理。

每个任务完成后另写短回执：

```json
{
  "action_id": "a1-requirement-clarification",
  "status": "completed",
  "output_paths": [],
  "output_hashes": {},
  "finding_count": 0,
  "high_impact_question_count": 0,
  "duration_ms": 0
}
```

主任务只接收这类回执，不接收分析正文。聊天回执限制在 300 个汉字以内。

## 7. 完整模式任务依赖图

动作 ID、依赖和输出必须固定，不能由主任务临时规划。

### 7.1 项目材料准备

| 动作 ID | 依赖 | 输入 | 输出 |
| --- | --- | --- | --- |
| `material-index` | 无 | 用户指定材料路径、可选 Align | 材料清单、来源索引、材料版本 |
| `material-facts:<source-id>` | 对应来源索引 | 单个新增或变化来源 | 分来源材料事实 |
| `material-merge` | 当前版本全部分来源事实 | 分来源事实 | 统一材料事实库和冲突列表 |

多份变化材料可以并行提取。材料缓存命中时直接复用，不生成事实提取动作。

### 7.2 A 层：需求理解

| 动作 ID | 依赖 | 主要输入 | 输出路径 |
| --- | --- | --- | --- |
| `a1-requirement-clarification` | 材料基线 | 材料事实、原始需求、可选 Align | `analysis/a/a1-requirement-clarification.json` |
| `a2-stakeholders` | A1 | A1 | `analysis/a/a2-stakeholders.json` |
| `a2-goals-success` | A1 | A1 | `analysis/a/a2-goals-success.json` |
| `a3-scenarios-journeys` | A1、两个 A2 | A1、A2 | `analysis/a/a3-scenarios-journeys.json` |
| `a4-user-stories` | A3 | A3 | `analysis/a/a4-user-stories.json` |
| `a4-scope-boundary` | A1、A2、A3 | A1、A2、A3 | `analysis/a/a4-scope-boundary.json` |
| `a5-merge-review` | A 层全部专项 | A 层专项 | `baselines/a-baseline.json` |

两个 A2 同批并行，两个 A4 同批并行。

### 7.3 B 层：业务建模

| 动作 ID | 依赖 | 主要输入 | 输出路径 |
| --- | --- | --- | --- |
| `b1-business-process` | A 基线 | A 基线 | `analysis/b/b1-business-process.json` |
| `b1-use-cases` | A 基线 | A 基线 | `analysis/b/b1-use-cases.json` |
| `b2-data-flow` | 业务过程 | A 基线、业务过程 | `analysis/b/b2-data-flow.json` |
| `b2-business-objects` | 业务过程、用例 | A 基线、B1 | `analysis/b/b2-business-objects.json` |
| `b2-business-rules` | 业务过程、用例 | A 基线、B1 | `analysis/b/b2-business-rules.json` |
| `b2-exceptions-boundaries` | 业务过程、用例、A 基线 | A 基线、B1 | `analysis/b/b2-exceptions-boundaries.json` |
| `b3-data-dictionary` | 数据流、业务对象 | B2 指定结果 | `analysis/b/b3-data-dictionary.json` |
| `b3-object-relations` | 业务对象 | 业务对象 | `analysis/b/b3-object-relations.json` |
| `b4-logical-data-model` | 数据字典、对象关系 | B3 | `analysis/b/b4-logical-data-model.json` |
| `b4-lifecycle-states` | 业务对象、业务过程、业务规则 | B1、B2 | `analysis/b/b4-lifecycle-states.json` |
| `b5-object-behavior` | 用例、对象关系、生命周期 | 指定 B 结果 | `analysis/b/b5-object-behavior.json` |
| `b6-model-review` | B 层全部专项 | A 基线、B 层专项 | `baselines/b-baseline.json`、`conflicts/business-conflicts.json` |

两个 B1 同批并行；四个 B2 在各自依赖满足后同批并行；两个 B3 并行；两个 B4 并行。

### 7.4 C 层：产品承接

| 动作 ID | 依赖 | 主要输入 | 输出路径 |
| --- | --- | --- | --- |
| `c1-system-functions` | A、B 基线 | A、B 基线 | `analysis/c/c1-system-functions.json` |
| `c1-permissions` | A、B 基线 | A、B 基线 | `analysis/c/c1-permissions.json` |
| `c1-integrations` | A、B 基线 | A、B 基线 | `analysis/c/c1-integrations.json` |
| `c1-product-nfr` | A、B 基线 | A、B 基线 | `analysis/c/c1-product-nfr.json` |
| `c2-interaction-prototype` | 系统功能、A、B 基线 | 指定基线和 C1 功能 | `analysis/c/c2-interaction-prototype.json` |
| `c2-system-data` | 系统功能、B 基线 | B 基线和 C1 功能 | `analysis/c/c2-system-data.json` |
| `c3-acceptance` | C 层全部专项 | C1、C2 | `analysis/c/c3-acceptance.json` |
| `c4-cross-layer-review` | A、B、C 全部结果 | A、B 基线、C 层结果 | `baselines/c-baseline.json`、`conflicts/cross-layer-conflicts.json`、`baselines/design-brief.json` |

四个 C1 同批并行，两个 C2 同批并行。

### 7.5 统一写作和成品检查

| 动作 ID | 依赖 | 输入 | 输出 |
| --- | --- | --- | --- |
| `design-editor` | `design-brief.json` 有效、无未处理 P0 | `design-brief.json`、`user-decisions.json`、模板、写作规则、术语表 | `output/design/design.md`、`output/design/decision-notes.md` |
| `review-pm-readability` | Design 初稿 | Design、可读性规则 | `reviews/pm-readability.json` |
| `review-park-coverage` | Design 初稿 | Design、A/B/C 基线、覆盖规则 | `reviews/park-coverage.json` |
| `review-downstream-sufficiency` | Design 初稿 | Design、下游边界和检查规则 | `reviews/downstream-sufficiency.json` |
| `design-repair:<fingerprint>` | 三类检查存在可修复问题 | Design、问题清单、`design-brief.json` | 局部修改后的 Design 和决策记录 |
| `compile-design-index` | Design 通过生成内检查 | `output/design/design.md` | `index/design-index.json` |
| `report-completed` | 索引有效 | 运行状态和短回执 | 完成报告 |

三类检查并行，只输出问题，不重写 Design。局部修复由设计总编完成，相同问题指纹达到上限后停止。

## 8. 简单模式任务图

简单模式不得复用完整模式全部节点。固定主路径为：

| 动作 ID | 依赖 | 输入 | 输出 |
| --- | --- | --- | --- |
| `simple-design` | 材料准备完成 | 材料事实、原始需求、可选 Align、模板和简单模式规则 | Design、决策记录、`analysis/simple/simple-coverage.json` |
| `simple-generated-check` | `simple-design` | Design、简单模式完整性规则 | `reviews/simple-generated-check.json` |
| `simple-repair:<fingerprint>` | 检查有问题 | Design、问题清单 | 局部修改后的 Design |
| `compile-design-index` | 检查通过 | Design | Design 索引 |
| `report-completed` | 索引有效 | 状态和回执 | 完成报告 |

只有发现真实复杂问题时，编排器才允许按预先定义的条件增加状态、权限、字段或异常专项；不能由主任务自由扩展，也不能因此启动全部完整模式节点。

## 9. 高影响问题处理

每个专项均可输出问题，但不得直接在子代理聊天中询问用户。

统一写入 `conflicts/user-questions.json`，由编排器去重并分级：

- P0：方案无法继续，进入 `waiting_user`；
- P1：会改变流程、权限、数据范围、状态、规则、结果或外部责任；能延后时进入 Design 待确认，不能延后时询问；
- P2：不改变主方案，使用保守表达并记录。

`next` 返回：

```json
{
  "state": "ready",
  "ready_actions": [],
  "blocked_by_user_questions": [],
  "completed_actions": []
}
```

用户回答写入 `inputs/user-decisions.json`。每个问题记录 `affected_action_ids`，只失效对应节点及其下游。

## 10. 编排器实现要求

### 10.1 固定依赖图

在 `design-orchestrator.py` 中使用静态任务定义，不让模型或主任务创建流程。每个节点至少定义：

- `action_id`；
- `mode`；
- `task_kind`；
- `depends_on`；
- `batch_key`；
- `input_files`；
- `forbidden_inputs`；
- `expected_outputs`；
- `rule_pack_selector`；
- `completion_check`；
- `max_attempts`。

### 10.2 多动作状态

把单个 `active_action` 改为按动作记录状态：

```text
pending / ready / running / completed / failed / blocked / stale
```

`next` 每次重新根据文件、输入哈希和依赖计算当前全部可运行节点。不能仅相信 `run.json` 的完成标记。

### 10.3 接受结果

`accept` 需要支持同批动作乱序完成：

- 动作 ID 必须属于当前运行；
- 输入哈希必须仍然有效；
- 输出必须存在并通过结构检查；
- 重复提交同一成功结果保持幂等；
- 一个同批动作失败不撤销其他已完成动作；
- 达到重试上限只阻断受影响路径。

### 10.4 局部失效

建立反向依赖关系。发生以下变化时，只把直接依赖和后代节点标为 `stale`：

- 材料版本变化；
- Align 或用户原始需求变化；
- 用户回答变化；
- 某个专项输出变化；
- Design 局部修复导致索引哈希变化。

不得因为 `run.json` 丢失或一个下游失败而重跑有效上游。状态文件丢失时从现有产物、来源信息和输入哈希重建。

### 10.5 规则包复用

静态规则保存在 ShitPM bundle 的 `skills/`、`contracts/`、`references/`、`schemas/` 和 `templates/`。

- 共享缓存按规则内容哈希保存；
- 项目运行目录只保存 `rule_pack_ref` 和任务卡，不复制三份占位规则 Markdown；
- 缓存缺失或被篡改时从 bundle 重建；
- 同一内容哈希跨项目复用；
- 规则改变只失效引用该规则包的节点和下游。

## 11. Design 模板和写作规则

修改：

- `templates/design.md`
- `references/design-writing.md`
- `references/design-quality-rubric.md`
- `contracts/design-review-checklist.md`
- 必要时同步 `references/design-flow-format.md`、`references/design-state-format.md`

Design 使用产品经理可读目录，按业务问题和闭环组织，不按 A/B/C 目录输出。页面权威定义采用固定标题与属性。

### 11.1 页面

```markdown
### 页面：填写周报

- 页面目的：
- 适用角色：
- 进入条件：
- 数据范围：
- 主要状态：
```

“主要状态”仅在真实存在状态差异时要求。

### 11.2 区块

```markdown
#### 区块：基本信息

- 区块目的：
```

### 11.3 字段

```markdown
##### 字段：所属周

- 业务含义：
- 字段来源：
- 展示条件：
- 输入与编辑：
- 取值与默认：
- 交互方式：
- 校验与反馈：
```

七个属性全部使用固定名称。没有特殊取值、默认、校验或反馈时，明确写“无特殊规则”，不要留给模型或解析器猜测。这样既便于产品经理逐项确认，也便于 PRD、原型和一致性检查稳定解析。

### 11.4 操作

```markdown
##### 操作：提交

- 适用角色：
- 展示与可用条件：
- 二次确认：
- 成功结果：
- 数据与状态变化：
- 失败与恢复：
- 后续去向：
```

会改变数据、状态、页面去向或外部结果的操作必须单独定义，不能当字段处理。

## 12. Design 索引

新增 `scripts/python/design-index.py`，职责单一：

1. 读取 `output/design/design.md`；
2. 解析固定标题和属性；
3. 生成页面 → 区块 → 字段/操作结构；
4. 记录 Design 内容哈希和每项原文定位；
5. 检查同层重复名称、缺失属性和非法层级；
6. 写入 `.workflow/runtime/context/design/index/design-index.json`；
7. 提供 `compile` 和 `check` 两个命令。

不能调用模型，不能根据上下文猜测缺失属性，不能修复 Design。

建议命令：

```powershell
python D:\work\ShitPM\scripts\python\design-index.py compile --project-root <project-root>
python D:\work\ShitPM\scripts\python\design-index.py check --project-root <project-root>
```

## 13. PRD、原型和 Review 同步

### 13.1 PRD

修改：

- `skills/spm-prd/SKILL.md`
- `references/prd-writing-rules.md`
- `scripts/python/prd-consistency-check.py`
- 必要的 PRD 测试样例

要求：

- PRD 生成读取 `design.md`，不把索引当事实输入；
- 一致性检查读取索引以定位 Design 中的页面、区块、字段和操作；
- Design 中的字段或操作在 PRD 缺失时失败；
- PRD 新增或改变高影响页面、字段、操作、权限、状态或结果时失败；
- PRD 可展开研发所需的技术类型、普通长度、控件细节和详细验收，但不得改变产品语义。

### 13.2 原型

修改：

- `skills/spm-prototype/SKILL.md`
- `references/prototype-writing.md`
- `scripts/python/prototype-consistency-check.py`
- 必要的原型测试样例

要求：

- 原型覆盖页面、区块、字段、展示条件、输入与编辑、交互、校验反馈和操作结果；
- 原型遗漏 Design 字段或操作时失败；
- 原型擅自新增会改变业务结果的字段或操作时失败；
- 布局和视觉可展开，不因此误报产品事实变化。

### 13.3 Review

同步：

- `skills/spm-design-review/SKILL.md`
- `contracts/design-review-checklist.md`
- `skills/spm-prd-review/SKILL.md`
- `contracts/prd-review-checklist.md`
- `skills/spm-prototype-review/SKILL.md`
- `contracts/prototype-review-checklist.md`

独立 Review 仍是按需第二意见，不成为生成门禁，也不自动修改产物。

## 14. 分阶段实施任务

### 阶段 0：建立修改基线

操作：

1. 记录当前 `git status --short`、差异文件和现有测试结果；
2. 阅读所有待改文件的现有未提交差异；
3. 把旧三段式断言列为迁移清单；
4. 不做任何清理式 Git 操作。

完成条件：明确哪些行是现有修改，哪些行将由本次重构改变。

### 阶段 1：先改产品契约和 Design 格式

文件：

- `skills/spm-design/SKILL.md`
- `templates/design.md`
- `references/design-writing.md`
- `references/design-quality-rubric.md`
- `contracts/design-review-checklist.md`
- 相关 README、USAGE

先写或修改资源完整性测试，再改文档。

完成条件：两种模式、产品经理读者、页面/区块/字段/操作固定结构和唯一事实源没有冲突。

### 阶段 2：定义 v2 契约和数据结构

文件：

- `contracts/design-orchestration-contract.md`
- `schemas/design-orchestration-action.schema.json`
- 必要时新增一个运行状态 Schema；没有真实校验需求时不要新增多余 Schema
- `references/design-analysis-protocol.md`

完成条件：所有任务都有固定 ID、依赖、输入、输出和责任；契约不再出现固定三次调用或唯一动作。

### 阶段 3：重写编排器核心

文件：

- `scripts/python/design-orchestrator.py`
- `scripts/python/context-run.py`
- `scripts/python/context-runtime-check.py`
- 必要时局部修改 `context-pack.py` 和 `source-index.py`

顺序：

1. 先实现任务图和纯函数就绪计算；
2. 再实现 `ready_actions[]`；
3. 再实现同批乱序接受；
4. 再实现局部失效和恢复；
5. 最后接入问题账本和局部修复。

完成条件：不调用模型即可完整计算简单模式和完整模式动作轨迹。

### 阶段 4：接入简单模式

先完成简单模式端到端零模型回放，再继续完整模式。这样可以先验证模板、索引和下游边界，不必等待全部 Park 节点。

完成条件：简单模式只出现简单路径动作，能生成并校验 Design 索引。

### 阶段 5：接入完整模式 A 层

文件：编排器任务定义、规则选择、伪造宿主、测试夹具。

完成条件：A2 和 A4 能同批并行；A5 只在全部 A 专项通过后解锁；中断后不重跑已完成节点。

### 阶段 6：接入 B 层

完成条件：B1、B2、B3、B4 按依赖并行；B6 能发现状态孤岛、责任缺失、异常不可恢复和范围回流等已知问题。

### 阶段 7：接入 C 层

完成条件：C1、C2 按依赖并行；C4 输出完整 `design-brief.json`，不以固定 token 截断。

### 阶段 8：接入设计总编和三类检查

完成条件：

- 设计总编只读取规定输入；
- 三类检查同时进入 `ready_actions[]`；
- 检查只输出问题；
- 局部修复次数有限；
- 失败不重跑 A/B/C。

### 阶段 9：接入 Design 索引及下游检查

文件：

- 新增 `scripts/python/design-index.py`
- 修改 PRD、原型一致性检查及测试

完成条件：缺字段、增字段、改字段语义、缺操作和改操作结果都有明确测试。

### 阶段 10：清理旧断言和文档入口

- 更新 README、USAGE 和资源清单；
- 旧计划标注被取代；
- 删除测试代码中的“三次核心调用”和“唯一下一动作”现行断言；
- 不删除历史报告和审计材料。

完成条件：仓库搜索不到把旧设计描述为当前契约的内容。

## 15. 实施时的测试顺序

每个阶段先跑直接相关测试，阶段完成后至少运行：

```powershell
python -m compileall D:\work\ShitPM\scripts\python
python D:\work\ShitPM\scripts\python\test-design-orchestrator.py
python D:\work\ShitPM\scripts\python\test-design-orchestration-replay.py
python D:\work\ShitPM\scripts\python\test-context-loading.py
python D:\work\ShitPM\scripts\python\test-context-runtime.py
python D:\work\ShitPM\scripts\python\test-resource-integrity.py
python D:\work\ShitPM\scripts\python\test-shitpm-regression.py
```

如果 `test-anti-hallucination.py` 的默认调用方式需要子命令，先阅读其帮助，不要盲目按旧计划直接执行：

```powershell
python D:\work\ShitPM\scripts\python\test-anti-hallucination.py --help
```

本阶段不运行真实项目。完整测试顺序以配套验收计划为准。

## 16. 实施完成报告

实施会话最终必须报告：

1. 修改和新增的文件；
2. 每个阶段完成情况；
3. 简单模式动作轨迹；
4. 完整模式动作批次轨迹；
5. 零模型测试命令和结果；
6. 仍未执行的在线测试和真实项目测试；
7. 已知风险；
8. 当前 `git status --short`；
9. 明确说明没有 commit、没有 push。

## 17. 停止条件

遇到以下情况停止，不用补丁绕过：

- 现有未提交修改与本计划发生无法判断的语义冲突；
- 为实现并行必须修改 Codex 宿主而仓库侧无法完成；
- Design 固定结构与现有 PRD/原型检查存在无法兼容的产品契约冲突；
- 零模型测试显示局部失效会错误复用陈旧事实；
- 完整模式需要依赖未定义的模型自由规划才能继续。

停止时只报告根因、影响和需要用户决定的问题，不提交、不推送。


