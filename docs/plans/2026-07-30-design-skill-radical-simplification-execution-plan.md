# Design Skill 极简化：执行与验收方案

> 日期：2026-07-30  
> 交付对象：执行 AI  
> 状态：已决策，可直接执行  
> 本文替代以下两份未执行方案中的结论：  
> - `docs/plans/2026-07-30-confirm-gate-fix-execution-plan.md`  
> - `docs/plans/2026-07-30-validation-simplification-plan.md`
>
> 若旧方案与本文冲突，以本文为唯一执行依据。不要把旧方案中的“三道门禁”“最终验证回执”“确认双门”重新引入。

## 1. 目标与核心决策

### 1.1 要解决的问题

当前 Design 流程把 Skill 做成了程序化工作流平台：

- 完整模式拆成大量细粒度分析动作；
- Design 生成后再生成多份检查 JSON；
- 编排器校验检查 JSON、基线 JSON、交接结构和输出哈希；
- 用户确认时又运行状态机检查；
- 下游再运行确认、来源和一致性检查；
- 很多工具只证明“步骤执行过”，并不直接改善 `design.md`。

真实项目已经出现错误时序：用户先确认，AI 后校验。继续叠加门禁只会让流程更慢、更难理解，不能保证产品判断正确。

### 1.2 最终目标流程

```text
简单模式
材料整理
  ↓
生成 Design，并在同一写作动作中完成一次 AI 自检和必要修正
  ↓
展示最终 Design
  ↓
用户确认，只记录 design.md 哈希
  ↓
PRD 或 Prototype

完整模式
材料整理
  ↓
A 层：需求、目标、用户、场景、范围、不确定项
  ↓
仅在存在高影响不确定项时询问用户
  ↓
B 层：业务流程、对象、规则、状态、权限、数据范围、异常
  ↓
C 层：功能、页面、字段、操作、产品承接、验收、跨层一致性
  ↓
生成 Design，并在同一写作动作中完成一次 AI 自检和必要修正
  ↓
展示最终 Design
  ↓
用户确认，只记录 design.md 哈希
  ↓
PRD 或 Prototype
```

### 1.3 已拍板的设计原则

1. `output/design/design.md` 是 Design 阶段唯一产品事实基线。
2. 保留 ABC 三层思考责任，不保留细粒度 ABC 程序节点。
3. AI 自检属于 `spm-design` 的执行要求，不生成独立检查报告，不需要程序证明。
4. 用户确认只表示用户确认当前 Design，不在确认时运行质量检查。
5. 下游只检查用户确认是否仍绑定当前 `design.md`。
6. 不建立最终验证回执、机器验证签名、检查结果哈希链或新的门禁文件。
7. 独立 Design Review 仍为用户按需调用的第二意见，不是确认前置。
8. 工具是否保留，以“能否直接改变最终产物”为判断标准，不以代码已经存在或理论上更安全为理由。
9. 不为了保留旧测试而保留已废弃行为；删除行为时同步删除或改写对应测试。
10. 不自动确认 Design，不自动生成 PRD 或 Prototype。

## 2. 保留、移除与暂不处理的边界

### 2.1 必须保留

#### ABC 三层责任

完整模式必须保留：

- A 层需求理解；
- B 层业务建模；
- C 层产品承接；
- 最终 Design 写作中的一次跨层自检。

保留的是分析责任，不是现有二十多个任务 ID。

#### 高影响问题升级给用户

以下内容不明确且不同答案会改变方案时，AI 必须在进入下一层前询问用户：

- 核心业务流程；
- 角色责任；
- 权限或数据范围；
- 审批、撤销、驳回、删除等关键行为；
- 对象唯一性或归属关系；
- 生命周期关键状态；
- 系统边界或范围边界；
- 跨系统失败后的业务处理。

不得为了不中断流程而自行补全高影响事实。

#### Design 确认哈希

保留 `scripts/python/design-confirmation.py`，但只承担：

- `confirm`：记录当前 `design.md` 的 SHA-256 和确认时间；
- `check`：比较当前 `design.md` 与确认记录；
- `show`：展示确认记录。

哈希用于判断确认后文件是否变化，不是质量证明。

#### 编排器的最小调度能力

本次不删除 `design-orchestrator.py`，保留：

- 模式初始化；
- A/B/C 顺序；
- 用户问题暂停与回答；
- 输入版本变化后使下游动作失效；
- 中断后继续；
- 必需输出是否存在且可读取。

这些能力直接支持长任务执行和避免读取陈旧材料，不属于生成后质量检查。

### 2.2 从 Design 主流程移除

必须移除以下动作：

- `simple-generated-check`
- `review-comprehensive`
- `review-pm-readability`
- `review-park-coverage`
- `review-downstream-sufficiency`
- `compile-design-index`
- `report-completed`

必须移除以下主流程行为：

- Design 写作接受时自动运行 `design-index.py compile`；
- 用户确认时运行 `state-machine-check.py`；
- `check` 时再次运行状态机或其他质量检查；
- A/B/C 基线接受时调用额外的 `context-runtime-check.py` 结构门禁；
- 根据生成后检查 JSON 启动自动 repair 循环；
- 以检查文件、检查回执或编排器回执作为“可以确认”的证明。

### 2.3 本次直接删除的脚本

以下脚本不再进入任何活动 Skill 主流程，直接删除：

- `scripts/python/review-precheck.py`
- `scripts/python/artifact-guard.py`
- `scripts/python/state-machine-check.py`
- `scripts/python/verify-against-metadata.py`

删除时同步处理活动调用方、契约说明和测试。历史计划与历史报告可以保留原文，不要求抹除历史引用。

### 2.4 本次暂时保留

#### `design-index.py`

暂时保留，因为当前：

- `prd-consistency-check.py` 会按需调用；
- `prototype-consistency-check.py` 会按需调用。

但从 Design 生成完成主流程移除 `compile-design-index`。下游确实需要时自行按需编译，不提前生成。

#### `stage-prep.py`

暂时保留，因为当前仍被：

- `prd-consistency-check.py`
- `prototype-consistency-check.py`

直接加载。不要在本次改造中花费大量工作把 1116 行逻辑迁移到另一个文件。后续只有在下游一致性检查也决定精简时，再评估删除。

#### `prd-consistency-check.py` 与 `prototype-consistency-check.py`

本次保留。它们可能直接发现最终 PRD/Prototype 与 Design 的不一致，并触发最终产物修正，不能在没有单独评估的情况下与 Design 检查工具一起删除。

#### `context-runtime-check.py`

保留脚本供上下文装载和显式诊断使用，但移除编排器对 A/B/C 中间输出的强制调用。中间输出只需满足当前动作可读取、依赖存在和输入未陈旧。

## 3. 模式收敛

### 3.1 只保留两种用户模式

用户可选模式收敛为：

- `simple`
- `full`

删除用户可见的 `full-layered` 模式名。

现有 `full-layered` 的三层思路成为新的 `full`，现有细粒度 `full` 任务图删除。

不保留 `full-layered` 兼容别名。旧运行若使用该模式，明确提示重新初始化，不自动迁移，不静默映射。

### 3.2 新 `simple` 任务图

```text
material-index
  ↓
material-facts:*（按材料数量，可并行）
  ↓
material-merge
  ↓
simple-design
  ↓
运行完成
```

`simple-design` 同时负责：

- 最小业务闭环分析；
- Design 写作；
- 写作后的单次 AI 自检；
- 发现问题后在同一动作内修正；
- 输出 `design.md` 和 `decision-notes.md`。

不再生成 `simple-generated-check.json`。

### 3.3 新 `full` 任务图

```text
material-index
  ↓
material-facts:*（按材料数量，可并行）
  ↓
material-merge
  ↓
a-layer
  ↓
b-layer
  ↓
c-layer
  ↓
design-editor
  ↓
运行完成
```

建议复用现有 `full-layered` 的层级输出路径，避免新建格式：

- `a-layer` → `a-baseline.json`
- `b-layer` → `b-baseline.json`、`business-conflicts.json`
- `c-layer` → `c-baseline.json`、`cross-layer-conflicts.json`、`design-brief.json`
- `design-editor` → `output/design/design.md`、`output/design/decision-notes.md`

删除现有细粒度完整模式的 A1-A5、B1-B6、C1-C4 动作定义及其专用调度分支。

### 3.4 三层输出的最小语义

不新增严格结构契约。执行提示中只要求以下最低内容。

#### A 层

- 已知事实；
- 目标、用户、场景和范围；
- 非目标和边界；
- 材料冲突；
- 推测与不确定项；
- 需要用户回答的高影响问题。

#### B 层

- 核心业务流程；
- 必要业务对象及关系；
- 关键规则；
- 必要状态和生命周期；
- 角色、操作权限和数据范围；
- 异常、驳回、撤销、重复、并发和跨系统失败的适用处理；
- 与 A 层冲突或无法推导的内容。

B 层不得把新推测写成已确认业务事实。

#### C 层

- 业务流程对应的产品功能；
- 页面、区块、字段和操作；
- 状态、权限、数据范围在页面上的表达；
- 集成和产品级非功能要求；
- 验收条件；
- A/B/C 跨层冲突；
- 无法承接或需要用户决定的高影响问题。

C 层不得创造 A/B 层不存在的高影响业务规则。

## 4. 最终 Design 自检规则

### 4.1 自检属于写作动作

`simple-design` 和 `design-editor` 在正式报告完成前，各自执行一次内部自检。自检不拆成新任务，不生成 JSON，不写检查回执。

最低检查清单：

1. 目标、用户、场景、范围和非目标是否一致；
2. 核心业务流程是否从触发到业务结果闭环；
3. 必要业务对象、规则和状态是否互相支持；
4. 角色权限与数据范围是否混淆或冲突；
5. 页面、区块、字段和操作是否承接关键流程；
6. 状态变化是否存在对应操作和结果；
7. 驳回、撤销、失败、超时、重复、并发等适用异常是否有业务处理；
8. 是否把推测写成事实；
9. 是否存在未暴露给用户的高影响拍板；
10. PRD 和 Prototype 是否可以直接读取当前 Design 继续工作。

发现问题时直接修改 `design.md` 或 `decision-notes.md`，完成后才结束当前写作动作。

### 4.2 对用户的完成语义

只有以下条件满足，`spm-design` 才能对用户说“Design 已完成，请确认”：

- 当前模式的必需分析动作完成；
- `design.md` 和 `decision-notes.md` 已生成；
- 写作动作已完成一次自检和必要修正；
- 不存在仍会改变核心流程、权限、数据范围、状态或范围边界的未回答问题。

不要求：

- 生成后检查 JSON；
- Design Review；
- 状态机脚本报告；
- Design 索引；
- 最终验证回执；
- 用户逐层确认 A/B/C。

## 5. 具体执行任务

### 任务 A：重写 `spm-design` 模式与主流程

**文件**：

- `skills/spm-design/SKILL.md`

**改动**：

1. 模式只保留简单模式和完整模式；
2. 删除 `full-layered` 实验路径的全部用户说明；
3. 完整模式改为 A/B/C 三层；
4. 删除生成后独立检查、确定性检查和索引作为完成前置的描述；
5. 将最终自检明确放进 Design 写作动作；
6. 明确 AI 自检完成并修正后才能展示最终 Design；
7. 保持 Review 可选、确认由用户触发、下游不自动启动；
8. 删除对 `state-machine-check.py`、`review-precheck.py`、最终验证回执的要求；
9. 删除把“依赖图所有检查动作完成”作为完成条件，改为当前模式必要分析和写作动作完成。

**不得新增**：

- 新检查 Skill；
- 新检查脚本；
- 新检查 JSON；
- 新的 P0/P1 机器判定；
- 新的最终验证文件。

### 任务 B：收敛 `design-orchestrator.py` 任务图

**文件**：

- `scripts/python/design-orchestrator.py`

**改动**：

1. `SUPPORTED_MODES` 改为 `("simple", "full")`；
2. 将现有 `full-layered` 的 A/B/C 层级图迁为 `full`；
3. 删除旧 `full` 细粒度 A1-A5、B1-B6、C1-C4 任务图；
4. 删除所有 `generated_check` 动作；
5. 删除 `compile-design-index` 动作；
6. 删除无输出的 `report-completed` 动作；
7. 所有必需任务完成后直接返回 `state=completed`；
8. 删除生成后检查失败触发的 `review_findings()` 和自动 repair 分支；
9. 删除 `_validate_comprehensive_review()` 及对应调用；
10. 删除 `accept_outputs()` 中自动调用 `design-index.py compile` 的分支；
11. 删除 `_handoff_requirements()` 及 A/B/C 接受时调用 `context-runtime-check.py` 的分支；
12. 保留输出存在/可读取、动作输入新鲜度、材料版本新鲜度和依赖完成判断；
13. Design 写作仍要求 A/B/C 基线存在，但不再对每份中间 JSON 运行外部结构门禁。

**同步清理**：

- `output_contract()` 中已删除任务的专用契约；
- `command_for_task()` 中已删除任务的命令；
- `completion_checks()` 中已删除任务的检查；
- 生成后检查路径和 coverage 常量；
- 只服务旧细粒度 full 的任务类型和分支；
- 未再使用的 import、常量和辅助函数。

### 任务 C：移除 `full-layered` 模式

**至少检查并修改**：

- `schemas/design-orchestration-action.schema.json`
- `contracts/design-orchestration-contract.md`
- `contracts/context-loading.manifest.json`
- `scripts/python/context-pack.py`
- `scripts/python/fake-design-host.py`
- `scripts/python/test-design-orchestrator.py`
- `scripts/python/test-design-orchestration-replay.py`
- `scripts/python/test-design-simplification.py`
- `skills/spm-design/SKILL.md`
- `README.md`
- `USAGE.md`

**要求**：

- 活动代码和活动文档只出现 `simple/full`；
- 历史计划、历史报告、`.workbuddy` 记忆不作为活动资源，不要求改写；
- 旧 `full-layered` 运行不自动迁移，返回明确错误或要求重新初始化；
- 不新增第三个模式名作为替代。

### 任务 D：简化 Design 确认

**文件**：

- `scripts/python/design-confirmation.py`

**改动**：

1. 删除 `run_deterministic_gate()`；
2. 删除 `subprocess` 等仅为状态机检查存在的依赖；
3. `cmd_confirm()` 只计算当前 `design.md` 哈希并保存确认；
4. `cmd_check()` 只校验确认记录结构和当前哈希；
5. 删除输出中的 `deterministic_gate` 字段；
6. 保留现有核心输出语义：`ok`、`confirmed`、`reason`、`confirmed_at`；
7. 保留原因：
   - `no_confirmation_record`
   - `confirmation_invalid`
   - `hash_match`
   - `hash_mismatch`
8. Design 不存在、确认文件损坏时继续失败关闭；
9. 不检查编排器状态，不检查 Review，不检查 A/B/C 文件，不检查 Design 索引。

### 任务 E：删除无最终价值的检查脚本

**删除文件**：

- `scripts/python/review-precheck.py`
- `scripts/python/artifact-guard.py`
- `scripts/python/state-machine-check.py`
- `scripts/python/verify-against-metadata.py`

**活动调用方同步修改**：

- `skills/spm-prd/SKILL.md`
- `skills/spm-prototype/SKILL.md`
- `skills/spm-fix/SKILL.md`
- `skills/spm-prototype-review/SKILL.md`
- `skills/spm-design-review/SKILL.md`
- `skills/spm-prd-review/SKILL.md`
- `README.md`
- `USAGE.md`
- `contracts/*.md`
- `references/*.md`
- 活动测试文件

**替代规则**：

- PRD/Prototype 开始前直接调用 `design-confirmation.py check`；
- PRD 完成时如仍保留 `prd-consistency-check.py`，直接调用，不再经过 `artifact-guard.py`；
- Prototype 完成时如仍保留 `prototype-consistency-check.py`，直接调用，不再经过 `artifact-guard.py`；
- Review Skill 直接按自身语义清单审查，不运行 `review-precheck.py`；
- Design 状态闭环由 `spm-design` 最终自检负责，不使用 `state-machine-check.py`；
- 旧 metadata 诊断不再作为新 bundle 能力保留。

删除 `artifact-guard.py` 后，不新增 provenance 替代脚本或来源回执。Design 修改后，确认哈希失效；现有下游一致性检查直接比较当前产物。

### 任务 F：调整下游 Skill

#### `spm-prd`

入口只保留：

```text
design-confirmation.py check
```

通过后直接读取已确认 Design 生成 PRD。

完成阶段允许保留一次直接的 `prd-consistency-check.py`，因为它可能改变最终 PRD。删除 `artifact-guard record/check`。

#### `spm-prototype`

入口只保留：

```text
design-confirmation.py check
```

通过后直接读取已确认 Design 生成 Prototype。

完成阶段允许保留一次直接的 `prototype-consistency-check.py` 和浏览器实际检查。删除 `artifact-guard record/check`。

#### Review Skill

- 不执行 `review-precheck.py`；
- 不因为缺少预检查报告拒绝 Review；
- 直接读取当前事实源进行语义审查；
- Review 发现的问题仍通过 `spm-fix` 回到事实源，不自动修改。

### 任务 G：更新测试，不保留废弃行为

**原则**：

- 删除专门验证已删除脚本的测试；
- 删除验证生成后检查动作、综合审查 schema、检查重试和检查回执的测试；
- 删除验证 `full-layered` 与旧 `full` 并存的测试；
- 不把旧测试改成检查一个没有实际意义的新回执；
- 新测试只覆盖剩余真实行为。

**必须覆盖**：

1. `simple` 任务图最终停在 `simple-design`；
2. `full` 任务图为 A → B → C → Design；
3. `full-layered` 被拒绝；
4. 所有必需任务完成后编排器直接完成；
5. 不出现任一生成后检查动作；
6. 不出现 `compile-design-index` 和 `report-completed`；
7. Design 写作缺少 A/B/C 输出时不能开始或接受；
8. 材料发生变化时旧 A/B/C/Design 动作失效；
9. `confirm` 不调用外部检查脚本；
10. `confirm` 成功写入哈希；
11. `check` 对未确认、匹配、修改后不匹配分别返回正确结果；
12. PRD/Prototype 入口只依赖有效确认；
13. 活动资源不再引用已删除脚本。

## 6. 执行顺序

### Phase 1：先改核心任务图

1. 将 `full-layered` 三层图迁为新 `full`；
2. 删除旧细粒度 `full`；
3. 删除生成后检查、索引和报告任务；
4. 调整完成判断；
5. 更新编排器直接测试。

此阶段暂时不要先删除脚本，避免调用方处于半迁移状态。

### Phase 2：改 Skill 行为

1. 重写 `spm-design` 模式与自检规则；
2. 更新上下文模式声明；
3. 更新主合同和动作 schema；
4. 更新虚拟宿主和回放测试。

### Phase 3：简化确认与下游入口

1. 删除确认时状态机检查；
2. 更新确认测试；
3. 删除下游 `artifact-guard` 调用；
4. 确认 PRD/Prototype 只通过确认哈希准入。

### Phase 4：删除脚本与引用

1. 删除四个废弃脚本；
2. 删除对应测试；
3. 清理 Skill、README、USAGE、contracts、references 中的活动引用；
4. 保留历史计划和报告，不为清理历史文字扩大改动范围。

### Phase 5：回归与真实质量验收

1. 运行程序测试；
2. 使用一个简单项目和至少两个复杂项目执行新流程；
3. 只比较最终 Design，不比较中间动作数和 JSON 数量；
4. 记录真实遗漏、错误事实和返工，不用“脚本全部执行”作为质量结论。

## 7. 自动化验收

在 `D:\work\ShitPM` 下使用 PowerShell 执行。根据实际保留的测试文件调整命令，但以下主测试必须有等价覆盖：

```powershell
python scripts/python/test-design-orchestrator.py
python scripts/python/test-design-orchestration-replay.py
python scripts/python/test-design-simplification.py
python scripts/python/test-shitpm-regression.py
python scripts/python/test-design-index.py
python scripts/python/test-context-loading.py
python scripts/python/test-resource-integrity.py
git diff --check
```

注意：

- 回归测试数量允许减少，因为废弃工具的测试应删除；
- 不要求保持旧的“37 项”数量；
- 不能通过跳过失败测试或吞掉异常获得全绿；
- 如果某个测试文件完全只服务被删除行为，可以删除该测试文件，并在执行报告中说明原因；
- 不新增模拟“最终验证回执”的测试。

### 7.1 活动引用扫描

以下扫描范围中不应再出现已删除脚本名：

```powershell
$activeRoots = @(
  'README.md',
  'USAGE.md',
  'skills',
  'contracts',
  'references',
  'schemas',
  'scripts/python'
)
$files = foreach ($root in $activeRoots) {
  if (Test-Path -LiteralPath $root -PathType Leaf) {
    Get-Item -LiteralPath $root
  } elseif (Test-Path -LiteralPath $root -PathType Container) {
    Get-ChildItem -LiteralPath $root -Recurse -File
  }
}
$files | Select-String -Pattern 'review-precheck\.py|artifact-guard\.py|state-machine-check\.py|verify-against-metadata\.py'
```

预期：无活动引用。历史 `docs/plans`、`docs/reports` 和 `.workbuddy` 不纳入该扫描。

### 7.2 废弃动作扫描

```powershell
$files = Get-ChildItem -LiteralPath . -Recurse -File | Where-Object {
  $_.FullName -notmatch '\\.git\\' -and
  $_.FullName -notmatch '\\docs\\plans\\' -and
  $_.FullName -notmatch '\\docs\\reports\\' -and
  $_.FullName -notmatch '\\.workbuddy\\'
}
$files | Select-String -Pattern 'simple-generated-check|review-comprehensive|review-pm-readability|review-park-coverage|review-downstream-sufficiency|compile-design-index|report-completed|full-layered'
```

预期：活动代码、Skill、合同和测试中无废弃动作或模式引用。

## 8. 真实质量验收

自动化测试只能证明流程可运行，不能证明 Design 产品质量。不得重新创建大量检查脚本代替真实验收。

### 场景 A：简单项目

选择一个只有单一角色、单一主流程、少量页面的真实或合成需求。

验收：

- 使用 `simple`；
- 不生成 ABC 中间分析；
- 不虚构审批、状态机或复杂权限；
- 最终 Design 包含适用的目标、范围、主路径、规则、页面、字段、操作、异常和验收；
- AI 自检后再展示；
- 用户确认后 PRD/Prototype 可直接启动。

### 场景 B：复杂审批与状态项目

选择包含申请、审批、驳回、撤销、重新提交、权限和数据范围的需求。

验收：

- A 层能区分事实、推测和高影响未知项；
- 对审批范围、撤销条件等不明确内容会询问用户；
- B 层流程、规则、状态、权限和异常闭环；
- C 层页面和操作承接关键状态变化；
- 最终 Design 不需要状态机脚本，也能明确表达进入、退出和异常路径；
- 不出现材料中没有依据的多级审批或虚构角色。

### 场景 C：多角色与数据隔离项目

选择包含组织、部门、项目、跨组织协作或多角色数据范围的需求。

验收：

- A 层明确角色目标和范围边界；
- B 层区分“能做什么”和“能看哪些数据”；
- C 层页面、筛选、操作和异常符合数据范围；
- 最终 Design 不把操作权限与数据权限混为一谈；
- 高影响归属关系不明确时会询问用户，不自行拍板。

### 场景 D：确认时序

验收步骤：

1. 运行 Design；
2. AI 在写作自检完成前不得提示确认；
3. AI 展示最终 Design；
4. 用户确认；
5. 确认命令不输出任何结构、状态机或综合检查结果；
6. 立即启动 PRD 或 Prototype，确认检查通过；
7. 修改 `design.md`；
8. 再启动下游，确认检查返回 `hash_mismatch`；
9. 用户重新确认后恢复准入。

## 9. 质量通过标准

新流程通过的标准不是“检查数量减少”，而是以下结果同时成立：

1. 简单项目不被迫执行 ABC；
2. 复杂项目仍完整执行 A/B/C 三层责任；
3. A 层不把高影响推测静默传给 B/C；
4. B 层形成业务闭环，不为了模型完整虚构对象和状态；
5. C 层能够把业务模型落到页面、字段、操作和验收；
6. 最终写作完成一次跨层自检；
7. 生成后没有独立检查动作和检查报告；
8. 用户确认时不运行质量检查；
9. 下游只通过确认哈希准入；
10. 删除的工具没有被新包装或新回执替代；
11. 与旧流程相比，真实项目没有新增高影响遗漏或错误事实；
12. 执行步骤、模型调用和中间产物数量显著减少。

若真实项目发现质量下降，先判断是哪项分析责任缺失，再补充 `spm-design` 的 AI 检查清单或 A/B/C 提示。禁止第一反应重新新增脚本、结构门禁、检查 JSON 或回执证明。

## 10. 禁止事项

执行 AI 不得：

- 实现第一份旧方案中的“三道门禁”；
- 实现第二份旧方案中的“编排器最终验证回执”；
- 新增 `design-verification.json`；
- 把 `design-editor` 回执改造成确认门禁；
- 在 `confirm` 或 `check` 中调用任何质量检查；
- 用新的统一检查器替代被删的四个检查器；
- 将五个生成后检查合并成一个新的综合检查动作；
- 为每层增加用户确认；
- 删除 ABC 分析责任；
- 让简单模式执行完整 ABC；
- 删除仍被下游直接使用的 `design-index.py` 或 `stage-prep.py`；
- 未经单独评估删除 `prd-consistency-check.py` 或 `prototype-consistency-check.py`；
- 修改历史计划和报告以伪造“从未存在过旧流程”；
- 自动确认 Design；
- 自动进入 PRD 或 Prototype；
- 执行 `git commit` 或 `git push`。

## 11. 执行报告要求

执行完成后，执行 AI 必须报告：

1. 修改文件列表；
2. 删除文件列表；
3. 新的 `simple` 和 `full` 任务图；
4. `design-confirmation.py` 的最终语义；
5. 保留但移出 Design 主流程的工具；
6. 删除或改写了哪些旧测试，以及原因；
7. 所有自动化测试命令和结果；
8. 三类真实质量场景的结果；
9. 是否仍存在活动引用残留；
10. 尚未解决但确实影响最终产物的风险。

不要用“代码行数减少”代替质量报告，也不要用“所有回执齐全”作为完成证明。
