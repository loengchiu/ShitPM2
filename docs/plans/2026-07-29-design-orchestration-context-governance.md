# Design 完整模式确定性编排与上下文治理设计

日期：2026-07-29  
状态：待确认，未实施代码改动

> 历史作废说明：本文属于旧版 `design-orchestration-*` 方案，已被 `docs/plans/2026-07-29-park-quality-pm-design-orchestration.md` 系列方案取代，仅作历史审计材料，不作为当前实施依据。


## 1. 文档目的

本文定义 ShitPM 完整模式 Design 的目标编排。它只解决两个问题：

1. 减少同一材料、规则和阶段产物被重复送入模型造成的低效率；
2. 防止主对话持续携带历史、工具结果和中间产物导致上下文膨胀。

本文建立在现有项目级材料资产、编译式规则装载和交接校验能力之上，不重新设计 Design 的产品责任，也不展开低成本测试体系。测试方案在本设计确认后单独制定。

当本文与以下历史讨论稿在“谁负责推进流程、是否保持同一主对话、是否默认执行独立成品审查、规则包保存位置”上冲突时，以本文为准：

```text
docs/plans/2026-07-29-design-context-performance.md
docs/plans/2026-07-29-material-ingestion-orchestration-discussion.md
docs/plans/2026-07-29-project-material-intake-design.md
docs/plans/2026-07-29-project-material-intake-implementation-design.md
```

上述文档中的材料清单、来源索引、材料事实资产和增量失效原则继续有效；英文文件名属于历史路径，本文统一使用“项目级材料准备”“材料事实提取”等中文名称。

## 2. 决策摘要

本设计采用“程序控制阶段边界，模型处理阶段内业务判断”的混合编排：

1. 新增确定性 Design 编排器，程序根据有效产物和依赖计算唯一下一动作；
2. `spm-design` 由长篇流程执行者收缩为入口和宿主执行适配层，不再自行规划整条流程；
3. 项目级材料准备是跨阶段共享的运行时前置能力，不归属 Align，也不归属 Design；
4. 主对话只保留状态、动作、路径、哈希、短摘要和待用户回答的问题，不读取完整工作产物；
5. “Design 负责人”是可从持久化产物恢复的逻辑角色，不绑定某个持续增长的聊天上下文；
6. 材料缓存命中时，完整模式默认只执行三次核心模型调用：分析、挑战、写作与生成内自查；
7. 默认不再执行独立成品审查子代理；确定性检查失败时只生成局部修复任务，独立 Design Review 仍按用户需要单独调用；
8. 静态规则包按内容哈希缓存在 ShitPM 安装目录，不再作为项目内容每次重新生成；
9. 阶段交接只通过有版本、有来源、有结构约束的文件完成，不通过聊天历史完成；
10. 不使用 Hook，不构建后台守护服务，不把 Align 改成 Design 的硬前置。

## 3. 已确认事实、判断与假设

### 3.1 已确认事实

当前仓库已经具备以下基础能力：

- `scripts/python/source-index.py` 能生成项目级材料清单、来源索引、材料版本并识别复用、增加、修改和删除；
- `scripts/python/context-pack.py` 能按阶段、模式、处理步骤、适用场景和子代理角色确定性选择规则；
- `scripts/python/context-runtime-check.py` 能检查材料资产、`design-model.json` 和 `design-challenge.json` 的结构、来源、版本和体量；
- `skills/spm-design/SKILL.md` 已描述材料准备、分析、挑战、写作和成品审查的上下文边界；
- `scripts/python/context-run.py` 只记录耗时和输入体量，不决定下一动作，也不启动隔离执行；
- `context-pack.py` 当前会在项目 `.workflow/runtime/context/<stage>/packs/` 下删除并重新写入规则包 Markdown 文件。

真实运行审计已经证明：本地命令耗时不是主要瓶颈；主要成本来自同一主对话反复携带材料、规则、Design 和工具历史。材料索引和缓存能减少原文进入次数，但不能单独阻止主对话继续膨胀。

### 3.2 设计判断

根因不是“材料读取命令慢”，也不是“没有显式输入 `$spm-design`”，而是：

> 当前流程的控制状态存在于模型上下文中，模型既承担业务分析，又承担阶段规划、输入发现、子代理调度、结果汇总和失败恢复。

只要这一责任不移出模型上下文，增加更多索引、缓存、规则包或提示说明都可能成为新的步骤和上下文来源。

### 3.3 实施假设

本设计依赖以下宿主能力：

1. 宿主能够创建不继承主对话历史的子代理或等价新会话；
2. 隔离执行实例可以读取任务说明中授权的文件，并把产物写回当前项目；
3. 主代理可以执行编排器命令、读取短小的动作 JSON，并机械调用宿主提供的子代理工具；
4. Python 脚本本身不能直接调用 Codex 的 `spawn_agent`，因此必须存在“程序控制平面”和“宿主执行适配层”两个责任。

如果宿主未来提供正式的代理调用 API，可以替换宿主执行适配层；产物依赖、任务说明和上下文边界不需要改变。

## 4. 目标与非目标

### 4.1 目标

- 同一个材料版本只进行一次模型级事实提取；
- 材料未变化时不重新建立索引、不重新提取事实、不重新读取原文；
- 每次模型调用只接收当前动作所需的输入；
- 主对话不接收原始材料正文、完整规则正文、完整中间产物和子代理工作过程；
- 新会话能够根据文件状态直接恢复，不需要回放历史；
- 完整模式在材料缓存命中时默认收敛为三次核心模型调用；
- 失败只使当前产物或其下游失效，不从流程起点重新执行；
- Design 首次生成仍完成完整模式要求的分析、独立挑战、统一裁决、成品写作和生成内自查；
- 用户确认后的 `output/design/design.md` 继续是 PRD 和 Prototype 的唯一产品事实基线。

### 4.2 非目标

- 不改变简单模式与完整模式的产品定义；
- 不把 Align 改成硬前置；
- 不重写 PRD 或 Prototype 编排；
- 不改变 Design、PRD、Prototype 的最终产物目录；
- 不让运行时材料资产、任务说明或交接文件成为下游事实源；
- 不把业务合理性判断交给确定性程序；
- 不按 ABC、角色、状态、页面等维度拆成多个子代理后拼接 Design；
- 不建立多项目后台队列、任务看板或常驻服务；
- 不使用 Hook；
- 本文不定义测试样例、测试夹具和真实项目回放策略。

## 5. 核心原则

### 5.1 控制状态外置

下一动作由程序根据已存在且通过校验的产物计算，不由模型回忆“刚才做到哪一步”。运行状态用于记录执行证据，但有效产物及其依赖才是恢复依据。

### 5.2 一个内容只保留一个权威副本

- 原始材料只存在于用户项目原路径；
- 材料事实只存在于 `materials/facts.json`；
- 业务模型只存在于 `design-model.json`；
- 挑战发现只存在于 `design-challenge.json`；
- 用户明确回答只存在于本次 Design 的用户输入记录；
- 规则正文只存在于 ShitPM 权威规则源和内容寻址缓存；
- 任务说明引用文件，不复制同一内容的多个版本。

### 5.3 逻辑角色与聊天实例分离

“Design 负责人”拥有统一业务模型和最终写入权，但不要求分析、挑战后的裁决和写作发生在同一个长对话中。逻辑连续性由结构化产物、用户输入记录和来源引用保证。

### 5.4 隔离执行不是自由探索

子代理不是拿到几个目录后自行查找。每个隔离执行实例只能处理一个确定动作，只读取任务说明列出的输入；需要原始证据时只能按来源索引给出的路径和行范围定点补读。

### 5.5 自动循环必须有边界

不执行无上限的“审查—修复—复审”。相同检查指纹连续失败时停止自动修复并报告；高影响事实无法从现有输入确定时进入等待用户状态。

## 6. 目标架构

```text
用户 / 主对话
  |
  | 只接收状态、唯一动作和待回答问题
  v
宿主执行适配层（spm-design）
  |
  | next / accept / answer
  v
Design 确定性编排器
  |-- 检查产物依赖和哈希
  |-- 生成唯一下一动作
  |-- 编译阶段任务说明
  |-- 校验阶段输出
  |-- 记录状态和指标
  |
  +--> 项目级材料准备（共享能力）
  |
  +--> 干净上下文：Design 分析
  |
  +--> 干净上下文：业务模型挑战
  |
  +--> 干净上下文：Design 写作与生成内自查
  |
  +--> 确定性检查 / 局部修复
```

### 6.1 程序控制平面

编排器负责：

- 建立和读取本次运行输入快照；
- 根据依赖计算唯一下一动作；
- 判断材料资产是否可复用；
- 生成阶段任务说明；
- 指定执行角色、授权输入和预期输出；
- 调用现有确定性检查；
- 记录完成、失败、等待用户和失效原因；
- 根据输入哈希只废弃受影响下游；
- 输出短小、机读的动作 JSON。

编排器不负责：

- 判断业务方案是否合理；
- 补全材料中不存在的产品事实；
- 替代 Design 负责人裁决挑战意见；
- 直接生成 Design 正文。

### 6.2 宿主执行适配层

`spm-design` 不再包含需要主代理临场理解的完整操作流程，而只执行固定循环：

```text
1. 调用编排器 next
2. 根据 action.type 执行唯一动作
3. 将执行结果交给编排器 accept
4. 重复，直到 completed / waiting_user / failed
```

宿主动作只允许以下类型：

| 动作类型 | 宿主责任 |
|---|---|
| `run_command` | 执行编排器给出的确定性命令，不自行追加探索命令 |
| `run_isolated_agent` | 使用任务说明启动干净子代理或等价新会话 |
| `ask_user` | 原样向用户提出编排器给出的单一问题，并记录回答 |
| `report_completed` | 报告产物路径、运行摘要和未决事项 |
| `stop_failed` | 报告失败动作、确定原因和可恢复方式 |

主代理不读取隔离角色生成的完整产物；只有编排器返回 `ask_user` 或最终摘要时才向用户展示必要内容。

### 6.3 隔离执行实例

隔离执行实例负责阶段内不可确定的模型工作。它必须：

- 从干净上下文启动；
- 只执行任务说明中的唯一目标；
- 只读取授权输入；
- 把完整结果写入指定文件；
- 向宿主返回状态、产物路径和短摘要；
- 不自行决定下一阶段；
- 不更新 `.workflow/status.json`；
- 不直接确认 Design；
- 不把内部分析写入最终产物。

## 7. 运行输入快照

当前长对话隐式保存了用户原始请求、模式选择和补充回答。改为干净上下文后，这些输入必须显式持久化，否则新执行实例会丢失直接进入 Design 时的用户要求。

建议目录：

```text
.workflow/runtime/context/design/inputs/
  request.md
  input-manifest.json
  user-decisions.json
```

### 7.1 `request.md`

保存触发本次 Design 的用户原始要求，不做模型改写。宿主只负责按原文写入。

### 7.2 `input-manifest.json`

至少记录：

```json
{
  "mode": "full",
  "request_path": ".workflow/runtime/context/design/inputs/request.md",
  "align_path": "output/align/align.md",
  "material_inputs": [],
  "existing_design_path": "output/design/design.md",
  "created_at": "..."
}
```

未指定模式时，编排器只返回一次 `ask_user`；用户选择写入清单后继续，不由模型自动判断。

### 7.3 `user-decisions.json`

只保存本次 Design 过程中用户对高影响问题的明确回答：

```json
{
  "decisions": [
    {
      "question_id": "...",
      "question": "...",
      "answer": "...",
      "answered_at": "...",
      "invalidates": ["analysis", "challenge", "writing"]
    }
  ]
}
```

它是 Design 生成期间的输入证据，不是 PRD 或 Prototype 的直接事实源。Design 确认后，下游仍然只读取确认后的 Design。

## 8. 产物依赖图与唯一下一动作

### 8.1 依赖图

```text
运行输入快照
  + 项目材料清单 / 来源索引
        -> 材料事实资产

运行输入快照
  + Align（如存在）
  + 材料事实资产
  + 分析规则引用
        -> design-model.json
        -> applicability.json

设计业务模型
  + 材料事实资产
  + 挑战规则引用
        -> design-challenge.json

设计业务模型
  + 挑战发现
  + 材料事实资产
  + 用户回答
  + 写作和生成内自查规则引用
        -> design.md
        -> decision-notes.md

Design 草稿
  + 必要交接哈希
        -> 确定性检查结果
        -> 完成 / 局部修复 / 等待用户
```

### 8.2 状态计算

编排器不只相信 `current_state` 字段，而要检查：

- 文件是否存在；
- 结构是否有效；
- 输入哈希是否与当前版本一致；
- 上游依赖是否仍然有效；
- 产物是否通过对应门禁；
- 当前是否存在未回答的阻断问题。

`next` 每次只能返回一个动作。宿主不能自行选择跳过、并行或重排依赖动作。

### 8.3 动作接口示意

```text
python $BUNDLE/scripts/python/design-orchestrator.py next --project-root .
python $BUNDLE/scripts/python/design-orchestrator.py accept --project-root . --action-id <id>
python $BUNDLE/scripts/python/design-orchestrator.py answer --project-root . --question-id <id> --answer-file <path>
python $BUNDLE/scripts/python/design-orchestrator.py status --project-root .
```

`next` 返回示例：

```json
{
  "action_id": "design-analysis-001",
  "type": "run_isolated_agent",
  "role": "design-owner",
  "task_path": ".workflow/runtime/context/design/tasks/001-analysis.md",
  "expected_outputs": [
    ".workflow/runtime/context/design/handoff/design-model.json",
    ".workflow/runtime/context/design/applicability.json"
  ]
}
```

命令和字段名在实施时可以按现有代码风格微调，但“一次只返回一个动作”和“主代理不得重新规划”是固定契约。

## 9. 项目级材料准备

### 9.1 责任位置

项目级材料准备是 `spm-start`、`spm-align` 和 `spm-design` 可共同触发的运行时前置能力，不是新的用户可见阶段。

直接进入 Design 时也必须可用；因此不能只放到 Align。

### 9.2 缓存命中

当材料来源集合和内容哈希未变化时：

- 复用 `manifest.json`；
- 复用 `source-index.json`；
- 复用 `facts.json`；
- 不启动材料事实提取子代理；
- Design 不全文读取原始材料。

哈希检查可以重复执行，因为确定性文件扫描不会把原文送入模型上下文。

### 9.3 部分变化

- 未变化来源继续复用旧事实；
- 新增和修改来源只处理变化片段；
- 删除来源移除对应事实；
- 相互独立的变化来源可以并行提取；
- 汇总后生成新的 `material_revision`；
- 只有依赖旧材料版本的 Design 产物失效。

### 9.4 原始证据补读

分析、挑战或写作发现事实冲突或高影响疑点时，不能重新扫描整个材料目录。任务说明必须给出：

```text
source_id
source_path
line_start
line_end
补读原因
```

补读结果进入当前阶段产物的来源引用，不复制成新的全文材料包。

## 10. 三次核心模型调用

材料缓存命中时，完整模式默认执行以下三次核心模型调用。

### 10.1 第一次：Design 分析

执行角色：逻辑上的 Design 负责人。  
上下文：全新。

输入：

- 运行输入快照；
- `output/align/align.md`，如存在；
- `materials/facts.json`；
- 分析规则包引用；
- 需要时的定点原始证据。

输出：

```text
.workflow/runtime/context/design/handoff/design-model.json
.workflow/runtime/context/design/applicability.json
```

`design-model.json` 必须足以让新的写作实例恢复统一业务模型，至少覆盖：

- 目标、范围和非目标；
- 角色及数据范围；
- 模块边界；
- 主流程和异常路径；
- 状态及转换；
- 权限；
- 跨系统责任；
- 产品不变量；
- 已做决策和理由；
- 被否决方案和权衡；
- 待确认项；
- 来源引用。

它不能只是过度压缩的章节提纲，否则写作实例仍然需要重新分析材料。

### 10.2 第二次：业务模型挑战

执行角色：独立挑战者。  
上下文：全新。

输入：

- `design-model.json`；
- `materials/facts.json`；
- `applicability.json`；
- 挑战规则包引用；
- 需要时的定点原始证据。

输出：

```text
.workflow/runtime/context/design/handoff/design-challenge.json
```

挑战者只输出缺陷、影响、证据、可否由现有事实修正、是否需要用户确认和是否阻止写作，不写最终 Design，不重新定义共享业务模型。

### 10.3 第三次：写作与生成内自查

执行角色：重新建立的 Design 负责人。  
上下文：全新。

输入：

- 运行输入快照；
- `design-model.json`；
- `design-challenge.json`；
- `materials/facts.json`；
- `user-decisions.json`；
- 写作规则、输出模板和生成内自查规则引用。

输出：

```text
output/design/design.md
output/design/decision-notes.md
```

写作实例负责：

1. 统一裁决挑战意见；
2. 对无法从现有事实解决的高影响问题停止并请求用户；
3. 写出完整 Design；
4. 在正式落盘前按生成内自查清单复核；
5. 同步生成四类 decision-notes。

默认不再启动独立成品审查子代理。独立 `spm-design-review` 继续作为用户按需调用的第二意见，不成为首次生成的固定门禁。

## 11. 阶段任务说明

建议目录：

```text
.workflow/runtime/context/design/tasks/
  001-analysis.json
  001-analysis.md
  002-challenge.json
  002-challenge.md
  003-writing.json
  003-writing.md
  repair-<id>.json
  repair-<id>.md
```

JSON 用于程序校验，Markdown 用于隔离执行实例读取。两者由同一次编译生成，不能分别由模型维护。

任务说明至少包含：

```json
{
  "action_id": "...",
  "objective": "...",
  "role": "...",
  "allowed_inputs": [
    {
      "path": "...",
      "hash": "...",
      "purpose": "...",
      "allowed_ranges": []
    }
  ],
  "rule_refs": [],
  "expected_outputs": [],
  "completion_checks": [],
  "stop_conditions": [],
  "forbidden_reads": []
}
```

约束：

- 任务说明不复制完整规则包和已有产物正文；
- 每个输入包含用途，避免子代理自行猜测；
- 默认禁止遍历项目、ShitPM 安装目录、`.workflow` 和历史输出目录；
- 如果任务需要定点原始证据，必须列出允许范围；
- 输出文件通过校验前，动作不能完成。

## 12. 上下文边界

### 12.1 主对话允许保留

- 当前模式；
- 当前动作类型；
- 动作 ID；
- 产物路径和哈希；
- 一行阶段摘要；
- 待用户回答的问题；
- 错误码和恢复动作；
- 耗时与 token 指标汇总。

### 12.2 主对话禁止装载

- 原始材料正文；
- 完整材料事实资产；
- 完整规则包；
- 完整 `design-model.json`；
- 完整 `design-challenge.json`；
- Design 草稿全文；
- 子代理工具调用过程；
- 子代理完整分析报告。

如果需要向用户展示具体缺口，编排器生成短摘要或定点摘录，而不是让主代理读取整个产物后自行总结。

### 12.3 隔离执行实例输入原则

- 同一文件在同一任务中只进入一次；
- 不同时包含原始材料全文和其完整事实摘要；
- 不传递父对话历史；
- 不传递上一执行实例的工具日志；
- 不为了“可能有用”装载其他阶段规则；
- 上下文预算用于预警和诊断，不得截断产品事实责任。

## 13. 静态规则包缓存

### 13.1 当前问题

`context-pack.py` 当前每次在项目目录生成 `packs/*.md`。这些文件不是占位模板，也不是测试数据，而是从 ShitPM 权威规则源提取出的运行时规则视图。

问题在于：规则源、模式、处理步骤和适用场景组合未变化时，重复生成相同 Markdown 没有价值，也使项目运行目录看起来包含额外业务材料。

### 13.2 目标方式

静态规则包按内容哈希缓存在 ShitPM 安装目录：

```text
$BUNDLE/.cache/context-packs/<pack-hash>.md
```

缓存键至少包含：

```text
manifest hash
规则源 hash
stage
mode
pass
role
section ids
```

项目目录只保存引用：

```json
{
  "bundle_revision": "...",
  "packs": [
    {
      "name": "design-core",
      "hash": "...",
      "cache_path": "..."
    }
  ]
}
```

规则更新或选择变化时生成新哈希文件；旧项目运行记录仍可通过哈希审计，不覆盖旧内容。

### 13.3 边界

- 静态规则包可以跨项目复用；
- 材料事实、适用性、业务模型、挑战结果和任务说明不能跨项目复用；
- 项目运行状态不能写入安装目录缓存；
- 缓存不可用时可以重新编译，但不能退回主代理全文扫描规则文件。

## 14. 运行时目录

在不改变现有主要路径的前提下，目标目录为：

```text
.workflow/runtime/
  materials/
    manifest.json
    source-index.json
    source-index.md
    facts.json
    runs/

  context/design/
    run.json
    inputs/
      request.md
      input-manifest.json
      user-decisions.json
    tasks/
      001-analysis.json
      001-analysis.md
      002-challenge.json
      002-challenge.md
      003-writing.json
      003-writing.md
    handoff/
      design-model.json
      design-challenge.json
    applicability.json
    rule-refs.json
    checks/
      final-check.json
      repair-<id>.json

  metrics/
```

运行时文件只用于：

- 当前 Design 的输入证据；
- 编排；
- 恢复；
- 交接；
- 校验；
- 审计；
- 性能测量。

除用户原始请求和明确回答外，运行时文件不能向 Design 注入上游不存在的产品事实；任何最终产品决定都必须写入 Design，PRD 和 Prototype 不读取这些运行时文件。

## 15. 失效与恢复

### 15.1 失效规则

| 变化 | 失效范围 |
|---|---|
| 材料内容变化 | 材料事实中对应来源、Design 分析及全部下游 |
| Align 内容变化 | Design 分析及全部下游 |
| 用户原始要求或模式变化 | Design 分析及全部下游 |
| 用户回答变化 | 声明依赖该回答的动作及其下游 |
| 分析规则变化 | `design-model.json` 及全部下游 |
| 挑战规则变化 | `design-challenge.json` 及写作下游 |
| 写作或自查规则变化 | Design 和 decision-notes |
| 仅最终检查脚本变化 | 重新检查，不自动重跑分析和挑战 |

### 15.2 中断恢复

恢复时：

1. 读取运行输入快照；
2. 校验材料版本；
3. 校验已有产物及其上游哈希；
4. 找到第一个缺失或失效产物；
5. 返回唯一下一动作。

不读取旧聊天记录，不依赖上下文压缩摘要，不要求用户重新说明已持久化的输入。

### 15.3 失败处理

- 传输或宿主启动失败：同一任务说明允许重试，不重建上游；
- 输出缺失或结构错误：拒绝 `accept`，生成当前动作的修复说明；
- 来源或版本错误：使当前产物失效，返回对应上游恢复动作；
- 高影响事实缺失：进入 `waiting_user`，不允许写作实例静默决定；
- 相同检查指纹再次出现：停止自动修复并报告，避免无限循环；
- 编排器异常：保留已通过校验的产物，新会话从状态检查恢复。

## 16. 确定性检查与局部修复

写作完成后仍执行现有可确定证明的检查，例如：

- 必需文件和章节存在；
- decision-notes 四类结构完整；
- 状态机表结构有效；
- 交接产物来源和版本一致；
- 运行时内部路径没有进入对外产物；
- 可确定的引用和结构错误；
- 上下文装载来源未陈旧。

程序不得判断业务方案是否合理，也不得因为某字段数量不足而推断 Design 不完整。

检查失败时生成局部修复任务说明，输入只包含：

- 当前 Design；
- 失败检查及定位；
- 相关业务模型片段；
- 相关挑战发现；
- 必要事实和规则引用。

局部修复不重新读取全部原始材料，不重新执行完整分析和挑战。

## 17. 指标与预算

指标按动作记录，不只记录整次运行总量：

```text
材料检查
材料事实提取
Design 分析
业务模型挑战
写作与生成内自查
确定性检查
局部修复
用户等待
```

每个动作记录：

- 开始和结束时间；
- 是否复用；
- 输入文件及哈希；
- 输入估算 token；
- 输出估算 token；
- 模型调用次数；
- 工具调用次数；
- 失败和重试次数；
- 是否发生定点补读。

上下文预算用于发现异常，不作为产品复杂度硬门槛。优先检查：

1. 同一输入是否重复进入同一任务；
2. 是否错误装载父对话历史；
3. 是否同时装载原文和完整事实摘要；
4. 是否装载了当前动作不需要的规则；
5. 是否因检查失败错误重跑上游。

## 18. 与现有文件的关系

### 18.1 保留并复用

```text
scripts/python/source-index.py
scripts/python/context-pack.py
scripts/python/context-budget.py
scripts/python/context-runtime-check.py
scripts/python/context-run.py
contracts/context-loading.manifest.json
contracts/subagent-context-contract.md
```

其中 `context-run.py` 继续只负责指标，不复用其名称承担编排，以避免行为和名称进一步混淆。

### 18.2 计划新增

```text
scripts/python/design-orchestrator.py
schemas/design-run.schema.json
schemas/design-task.schema.json
```

数据结构定义是否拆成两个文件可在实施计划中按现有目录风格确认，但运行状态和任务说明必须有确定性结构校验。

### 18.3 计划修改

```text
skills/spm-design/SKILL.md
contracts/subagent-context-contract.md
contracts/context-loading.manifest.json
scripts/python/context-pack.py
scripts/python/context-runtime-check.py
scripts/python/stage-context.py
```

修改目的分别为：

- Skill 收缩为入口和机械调度协议；
- 契约增加 Design 负责人、短返回和禁止自由探索边界；
- manifest 合并写作与生成内自查所需规则选择；
- context-pack 改为内容寻址缓存和项目引用；
- runtime-check 增加任务说明、输入哈希和运行依赖校验；
- stage-context 只展示可执行入口和当前状态，不替代编排器计算下一动作。

这只是影响范围，不代表本轮已经批准修改这些文件。

## 19. 实施顺序

### 第一步：建立控制平面，不先优化缓存

- 新增 Design 编排器；
- 建立运行输入快照、产物依赖和唯一下一动作；
- 复用当前项目级规则包路径；
- 让主代理只做机械调度；
- 验证中断恢复不依赖聊天历史。

这一阶段优先解决根因：编排状态不再存在于模型上下文。

### 第二步：接入三个隔离执行动作

- 分析输出业务模型和适用性；
- 独立挑战输出挑战发现；
- 写作实例完成统一裁决、成品写作和生成内自查；
- 移除默认独立成品审查调用；
- 保留用户按需 Design Review。

### 第三步：改造规则包复用

- 将静态规则包移到安装目录的内容寻址缓存；
- 项目只保存规则引用和哈希；
- 保留来源追踪和陈旧校验；
- 不改变规范性规则选择逻辑。

### 第四步：接入局部失效和局部修复

- 根据输入哈希精确失效；
- 检查失败只生成局部修复任务；
- 相同失败重复时停止自动循环。

### 第五步：单独制定低成本测试方案

测试设计另文完成，目标是用合成材料、固定录制输入和少量真实项目抽查代替每次完整真实项目回放。未经后续测试设计确认，不把“连续多次真实项目冷启动”设为日常回归方式。

## 20. 验收标准

本文只定义结果，不定义本轮测试实现。

### 20.1 编排

- `next` 每次只返回一个确定动作；
- 主代理不再自行判断完整模式的步骤顺序；
- 中断后新会话能从第一个无效依赖继续；
- 已通过校验的上游不因下游失败而重跑；
- 未显式输入 `$spm-design` 但已正确路由到该 Skill 时，运行行为与显式调用一致。

### 20.2 上下文

- 主对话不读取原始材料和完整阶段产物；
- 子代理不继承父对话历史；
- 同一任务中同一文件正文不重复进入上下文；
- 材料未变化时不启动材料事实提取；
- 默认 Design 主路径不执行第四次独立成品审查模型调用；
- 缓存命中时完整模式默认只有分析、挑战、写作与生成内自查三次核心模型调用。

### 20.3 复用

- 相同规则选择跨项目复用同一个内容哈希规则包；
- 项目目录不再保存重复的静态规则正文；
- 材料变化只使对应事实及其下游失效；
- 仅检查脚本变化时不重跑模型分析。

### 20.4 产品边界

- 完整模式 ABC 分析责任不减少；
- 独立挑战仍在首次正式写入前完成；
- Design 负责人保留统一模型和最终写入权；
- 生成内自查仍在正式 Design 落盘前完成；
- Review 仍是按需第二意见；
- Design 确认、PRD 和 Prototype 边界不改变；
- 运行时文件不成为 PRD 或 Prototype 的产品事实输入。

## 21. 风险与对策

### 风险一：交接过度压缩导致写作重新推理

对策：`design-model.json` 不只保存结论，还保存不变量、决策理由、权衡、待确认项和来源引用；体量预算只预警，不以固定上限截断业务责任。

### 风险二：主代理仍偷偷读取产物

对策：Skill 只允许机械动作；编排器返回的动作不要求主代理解释完整结果；隔离角色以文件写入、短摘要返回；测试阶段增加主对话输入审计。

### 风险三：Python 无法直接强制宿主创建干净上下文

对策：把 `run_isolated_agent` 作为明确宿主协议；任务说明、动作 ID、预期输出和校验由程序控制。若宿主不支持隔离执行则明确失败，不静默退回同一长对话。

### 风险四：减少独立成品审查影响质量

对策：保留独立业务模型挑战；把生成内自查并入写作任务；保留确定性检查和局部修复；独立 Design Review 仍可由用户调用。后续用低成本质量样例验证，不以速度假设代替质量证据。

### 风险五：全局规则缓存陈旧

对策：缓存以 manifest、规则源、章节选择和内容哈希寻址；任务说明记录实际使用哈希；校验失败重新编译，不按文件名盲目复用。

### 风险六：运行状态与真实文件不一致

对策：状态从产物、依赖和哈希重新计算；`run.json` 是执行记录，不是唯一判断依据。

## 22. 保持不变的产品契约

本设计不会改变：

- Design 是 Product Definition 和 Design Baseline；
- 用户确认后的 `output/design/design.md` 是唯一 Design 产品事实基线；
- 完整模式首次生成承担需求理解、业务建模、一致性挑战、系统需求和跨层一致性责任；
- Align 可选；
- PRD 和 Prototype 都直接读取确认后的 Design；
- `decision-notes.md` 只承担审计责任；
- 确定性程序只阻断可可靠证明的问题；
- 高影响未决事实必须由用户决定或在 Design 中明确待确认；
- 不改变 Prototype 技术架构和 PRD 写作边界。

## 23. 待确认决策

本设计需要用户最终确认以下整体方案，不需要逐项另行选择：

1. 同意程序成为真正的阶段编排者，主代理只承担宿主机械调度和用户交互；
2. 同意“Design 负责人”从连续聊天实例改为可由结构化产物恢复的逻辑角色；
3. 同意完整模式默认采用三次核心模型调用；
4. 同意写作和生成内自查合并，默认不再执行独立成品审查子代理；
5. 同意静态规则包迁移到 ShitPM 安装目录的内容寻址缓存，项目只保留引用；
6. 同意先实施编排控制平面，再单独处理低成本测试方案。

本文确认前，不修改 Skill、脚本、契约、数据结构定义和模板；不提交、不推送。

