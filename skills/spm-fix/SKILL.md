---
name: spm-fix
description: "同步修复——ShitPM：把变更影响沿链路传播到当前事实源。用于用户说同步修复、fix、修复传播、回写上游、一致性修复，或 Review 建议回上游修复时。按传播契约局部修复，不整篇重写、不自动确认 Design、不自动生成所有下游。"
---

## 路径与资源

从系统 prompt 读取 `$BUNDLE`。bundle 资源位于 `$BUNDLE/references/`、`templates/`、`contracts/`、`schemas/`、`scripts/python/` 和 `lib/`；项目产物位于当前项目根目录的 `.workflow/` 和 `output/`。

流程开始时输出模型建议：修改范围、正确结果和受影响位置都明确时可用轻量模型；需要判断跨层影响、业务归属或方案取舍时使用深度推理模型；无法判断时按高影响使用深度推理模型。

## 职责边界

- Design 是高影响产品事实源；目标、范围、建设方式、模块、页面、字段、规则、流程、状态、权限、异常和跨系统责任的语义变化必须回写 Design。
- PRD 和 Prototype 是 Design 的两个并列下游，不要求同时存在，也不存在默认的 Design → PRD → Prototype 链路。
- Align 仅作 Design 输入参考，不是事实源；目标、范围和建设方式不能通过 Align 反向定源。
- 纯格式、措辞、排版或视觉表现修改可以只改对应下游，不触发 Design confirmation 失效。
- 无法判断影响范围时按高影响变化处理。
- Fix 只修事实源层，不自动局部重写下游；用户重新确认 Design 后再显式触发对应下游生成。

## 输入事实源

1. 用户原始修改指令。
2. `.workflow/status.json`（如存在）。
3. 当前阶段人读产物。
4. `$BUNDLE/contracts/fix-propagation-rules.md`（唯一传播规则来源）。
5. 实际受影响分支所需的上游/下游 references、templates、contracts 和确定性检查脚本；不读取无关阶段资源。

## 执行流程

必须按契约的最小判断清单执行：

1. 读取并解析用户修改指令；必须明确“改什么”和“改成什么”，缺一项就停止追问。
2. 判断修改对象属于目标/范围/建设方式、模块/页面/字段/规则/流程/状态/权限、跨系统/异常，还是表现层/措辞/格式。
3. 判定问题归属层和事实源所在阶段；跨层指令拆为独立动作，不混在一层改。
4. 读取 `$BUNDLE/contracts/fix-propagation-rules.md`，判定受影响的最深阶段和实际存在的下游分支。
5. 只修改事实源层，局部覆盖当前真相，不整篇重写、不制造多版本；不得把 PRD 或 Prototype 直接提升为 Design 事实。
6. 若修改 `design.md`，必须先处理旧 confirmation 失效，再停止下游传播；Fix 不先改 PRD 或 Prototype。
7. 仅对实际存在且受影响的分支运行适用检查：`design-confirmation.py`、`artifact-guard.py`、`prd-consistency-check.py`、`prototype-consistency-check.py`。PRD 不存在时不伪造 PRD 检查，Prototype-only 项目仍需走合法原型检查路径。

## Confirmation 与输出

修改 Design 后不手动删除 confirmation 文件，也不自动调用 `confirm`；通过 `design-confirmation.py check` 或 `stage-context.py` 让哈希不一致显现，并明确告知：旧确认失效，用户重新确认后才能生成下游。

Fix 完成后输出：

- 实际修改的事实源层和文件。
- 修改对象及影响范围。
- Design confirmation 是否失效。
- 实际运行的检查及结果。
- 建议进入哪个 Review、检查哪些对象；不自动执行 Review。

建议格式：

```text
建议进入 [阶段] review，检查对象：[对象列表]
若修改了 design.md：Design 已修改，旧确认失效。请由用户重新确认 Design 后再生成下游。
```

## 失败与停止

- 传播契约缺失：报告具体路径，不凭记忆扩展传播矩阵。
- 指令含义不清或归属层无法判断：停止澄清，不直接改下游。
- 下游不存在：只处理实际存在的分支，不为了“完整”创建产物。
- 脚本检查失败：报告确定性错误，不伪装为通过。
- 发现 Design 语义需要修改：修改事实源后立即停止，不自动生成或同步所有下游。

## 硬规则

- 不自动确认 Design。
- 不自动生成所有下游。
- 不把 决策记录、metadata 或旧 Review 结果当作产品事实源。
- 不整篇重写与修改无关的产物。
- 不自动调用 `spm-fix` 自身形成循环，不自动推进阶段。
