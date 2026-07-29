# Park 级质量 Design 编排重构验收结果

- 日期：2026-07-29
- 仓库：`D:\work\ShitPM`
- 范围：维护 ShitPM 仓库本身
- 真实项目 Design：未生成
- `/spm`：未执行
- 模型调用：0

## 1. 修改和新增文件

### 1.1 已修改文件

- `AGENTS.md`
- `README.md`
- `USAGE.md`
- `contracts/design-review-checklist.md`
- `contracts/subagent-context-contract.md`
- `references/design-quality-rubric.md`
- `references/design-writing.md`
- `scripts/python/context-budget.py`
- `scripts/python/context-pack.py`
- `scripts/python/prd-consistency-check.py`
- `scripts/python/prototype-consistency-check.py`
- `scripts/python/stage-context.py`
- `skills/spm-align/SKILL.md`
- `skills/spm-design/SKILL.md`
- `templates/design.md`

### 1.2 新增文件或目录

- `contracts/design-orchestration-contract.md`
- `schemas/design-orchestration-action.schema.json`
- `scripts/python/context-run.py`
- `scripts/python/context-runtime-check.py`
- `scripts/python/design-index.py`
- `scripts/python/design-orchestrator.py`
- `scripts/python/fake-design-host.py`
- `scripts/python/source-index.py`
- `scripts/python/token_estimate.py`
- `scripts/python/test-context-runtime.py`
- `scripts/python/test-design-index.py`
- `scripts/python/test-design-orchestrator.py`
- `scripts/python/test-design-orchestration-replay.py`
- `design-rule-cache/`
- `docs/` 下本次已有计划及报告文件

没有删除或覆盖工作区既有未提交文件，没有执行 `git reset --hard`、`git clean` 或其他覆盖式还原。

## 2. 阶段 0 至阶段 10

| 阶段 | 结果 | 说明 |
|---|---|---|
| 阶段 0：建立修改基线 | 完成 | 已记录初始 `git status --short`、`diff --stat`、`diff --name-only`，并保留既有差异。 |
| 阶段 1：产品契约和 Design 格式 | 完成 | 保留简单/完整两种模式；Design 面向产品经理；页面、区块、字段、操作使用确认版固定结构。 |
| 阶段 2：v2 契约和数据结构 | 完成 | 新增编排契约和动作 Schema；动作包含稳定 ID、依赖、输入、输出和责任；未恢复固定三次模型调用或唯一下一动作。 |
| 阶段 3：编排器核心 | 完成 | 使用依赖图计算 `ready_actions[]`；支持同批乱序、失败重试、中断恢复、收据恢复、局部材料失效、用户决策局部失效和陈旧状态拒绝。 |
| 阶段 4：简单模式 | 完成 | 零模型轨迹只包含简单路径、生成检查、索引编译和完成报告。 |
| 阶段 5：完整模式 A 层 | 完成 | A2、A4 等无依赖动作可同批就绪；A5 在 A 层依赖完成后解锁。 |
| 阶段 6：B 层 | 完成 | B1、B2、B3、B4 按依赖图组织；B6 作为业务模型汇总和挑战节点。 |
| 阶段 7：C 层 | 完成 | C1、C2 可按依赖同批就绪；C4 形成跨层基线和 Design brief 输出。 |
| 阶段 8：设计总编和三类检查 | 完成 | 由单一设计总编统一写作；三类成品检查同批就绪；失败只重试当前节点，不重跑 A/B/C。 |
| 阶段 9：Design 索引及下游检查 | 完成 | 索引只从 `design.md` 确定性生成；覆盖页面、区块、字段、操作及属性一致性。 |
| 阶段 10：清理旧断言和文档入口 | 完成 | README、USAGE、Skill、契约和检查规则已迁移到 v2 语义；当前测试不再断言旧三段式或唯一下一动作。 |

## 3. 简单模式零模型动作轨迹

```text
simple-design
→ simple-generated-check
→ compile-design-index
→ report-completed
```

## 4. 完整模式每一批 `ready_actions[]` 动作轨迹

1. `a1-requirement-clarification`
2. `a2-stakeholders`、`a2-goals-success`
3. `a3-scenarios-journeys`
4. `a4-user-stories`、`a4-scope-boundary`
5. `a5-merge-review`
6. `b1-business-process`、`b1-use-cases`
7. `b2-data-flow`、`b2-business-objects`、`b2-business-rules`、`b2-exceptions-boundaries`
8. `b3-data-dictionary`、`b3-object-relations`、`b4-lifecycle-states`
9. `b4-logical-data-model`、`b5-object-behavior`
10. `b6-model-review`
11. `c1-system-functions`、`c1-permissions`、`c1-integrations`、`c1-product-nfr`
12. `c2-interaction-prototype`、`c2-system-data`
13. `c3-acceptance`
14. `c4-cross-layer-review`
15. `design-editor`
16. `review-pm-readability`、`review-park-coverage`、`review-downstream-sufficiency`
17. `compile-design-index`
18. `report-completed`

伪造宿主记录的隔离状态为 `simulated_only`。这只能证明仓库侧流程回放，不证明真实 Codex 宿主启动了子代理或完成了真实文件访问审计。

## 5. T0、T1、T2、T3、T7 测试命令和结果

### T0：当前状态基线

执行：

```powershell
git -C D:\work\ShitPM status --short
git -C D:\work\ShitPM diff --stat
git -C D:\work\ShitPM diff --name-only
```

结果：完成基线记录。工作区原有大量未提交修改，已逐项保留；没有执行覆盖式还原。

### T1：零模型单元与契约

执行：

```powershell
python D:\work\ShitPM\scripts\python\test-design-orchestrator.py
```

结果：通过，7 个用例，模型调用 0。

### T2：无模型依赖图回放

执行：

```powershell
python D:\work\ShitPM\scripts\python\test-design-orchestration-replay.py
```

结果：通过，16 个用例，模型调用 0。覆盖简单模式、完整模式批次、同批乱序、A2/C1 单节点失败、设计总编失败、成品检查失败、索引编译失败、A2/B2/设计总编中断恢复、状态文件丢失、材料局部变化、用户决策局部失效、陈旧动作和篡改输出拒绝。

### T3：Design 格式、索引和下游一致性

执行：

```powershell
python D:\work\ShitPM\scripts\python\test-design-index.py
```

结果：通过，11 个测试。覆盖标准 PRD 格式、缺失字段、旧格式显式不支持、索引篡改、重复项和下游一致性。

另外，完整零模型回归中的下列检查也通过：

```powershell
python D:\work\ShitPM\scripts\python\test-context-loading.py
python D:\work\ShitPM\scripts\python\test-context-runtime.py
python D:\work\ShitPM\scripts\python\test-resource-integrity.py
python D:\work\ShitPM\scripts\python\test-shitpm-regression.py
```

结果：上下文装载通过；项目级材料资产测试通过；资源完整性通过；ShitPM 回归 36 通过、0 失败。

### T7：故障、恢复和局部失效（零模型）

T7 使用同一条回放命令执行，不启动在线测试：

```powershell
python D:\work\ShitPM\scripts\python\test-design-orchestration-replay.py
```

结果：通过，16 个回放用例，模型调用 0。其中 12 个用例直接覆盖 T7：

- A2 同批单节点失败只重试失败节点；
- C1 同批单节点失败不重跑同批其他节点和上游；
- 设计总编失败只重试写作；
- 单个成品检查失败不重跑其他检查；
- Design 索引编译失败不重跑总编或检查；
- A2 并行批次中断恢复；
- B2 并行批次中断恢复；
- 设计总编后中断恢复；
- 状态文件丢失后依据收据和输出恢复；
- 单份材料变化只重做相关事实及下游；
- 用户决策变化只失效声明节点及下游；
- 陈旧动作和篡改输出拒绝。

## 6. 模型调用次数

所有已执行测试和回放的模型调用次数均为 **0**。

`fake-design-host.py` 只用于零模型流程验证，不作为真实子代理证据。

## 7. 尚未执行的测试

按本会话要求，以下均未执行：

- T4：简单模式合成在线测试；
- T5：完整模式合成在线测试；
- T6：质量专项验收；
- T8：真实项目验收；
- 合成在线测试；
- 真实项目测试。

因此目前只能判定“仓库侧代码测试和零模型流程回放通过”，不能判定真实宿主运行通过，也不能判定真实 Design 质量已被在线或用户验收。

## 8. 已知问题和风险

1. 尚无真实 Codex 宿主级文件读取、子代理生命周期、父子任务关系和模型输入快照证据；这些不能由 `fake-design-host.py` 补齐。
2. T4、T5、T6、T8 未执行，不能据此判断在线模型输出质量、真实并行效果、真实运行时长或产品经理对最终 Design 的认可。
3. `git diff --check` 已通过；仍保留工作区大量未提交修改，未做覆盖式清理。
4. `design-rule-cache/` 及 `docs/` 中存在未跟踪内容，属于当前工作区已有或本次运行产生的未提交文件，未删除。
5. 完整模式的业务质量仍须通过在线合成和真实用户确认验证；零模型只能验证依赖、状态、收据、局部失效和输出结构。

当前唯一有意保留的验收阻断是：未执行在线测试和真实项目测试；这是本会话明确要求，不是通过旧三段式或临时回退路径绕过。

## 9. 当前 `git status --short`

以最终报告生成前的工作区状态为基线，当前状态包括：

```text
 M AGENTS.md
 M README.md
 M USAGE.md
 M contracts/design-review-checklist.md
 M contracts/subagent-context-contract.md
 M references/design-quality-rubric.md
 M references/design-writing.md
 M scripts/python/context-budget.py
 M scripts/python/context-pack.py
 M scripts/python/prd-consistency-check.py
 M scripts/python/prototype-consistency-check.py
 M scripts/python/stage-context.py
 M skills/spm-align/SKILL.md
 M skills/spm-design/SKILL.md
 M templates/design.md
?? contracts/design-orchestration-contract.md
?? design-rule-cache/
?? docs/
?? schemas/design-orchestration-action.schema.json
?? scripts/python/context-run.py
?? scripts/python/context-runtime-check.py
?? scripts/python/design-index.py
?? scripts/python/design-orchestrator.py
?? scripts/python/fake-design-host.py
?? scripts/python/source-index.py
?? scripts/python/test-context-runtime.py
?? scripts/python/test-design-index.py
?? scripts/python/test-design-orchestration-replay.py
?? scripts/python/test-design-orchestrator.py
?? scripts/python/token_estimate.py
```

生成本报告后，`docs/` 目录仍保持未跟踪状态，未执行暂存。

## 10. Git 操作声明

本次没有执行 `git commit`，没有执行 `git push`。
