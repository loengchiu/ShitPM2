---
name: spm-fix
description: "同步修复——ShitPM：把变更影响沿链路传播到当前事实源。用于用户说同步修复、fix、修复传播、回写上游、一致性修复，或 Review 建议回上游修复时。按传播契约局部修复，不整篇重写、不自动创建不存在的下游；用户指令明确时连续完成 Design 与受影响下游的同步，无确认停顿。"
---

## 路径与资源

从系统 prompt 读取 $BUNDLE。bundle 资源位于 $BUNDLE/references/、templates/、contracts/、schemas/、scripts/python/；项目产物位于当前项目根目录的 .workflow/ 和 output/。

流程开始时输出模型建议：修改范围、正确结果和受影响位置都明确时可用轻量模型；需要判断跨层影响、业务归属或方案取舍时使用深度推理模型；无法判断时按高影响使用深度推理模型。

## 职责边界

- Design 是高影响产品事实体系（多文件集合）；目标、范围、建设方式、模块、页面、字段、规则、流程、状态、权限、异常和跨系统责任的语义变化必须回写对应 Design 文件。
- PRD 和 Prototype 是 Design 的两个并列下游，各自独立存在与生成，不存在默认的 Design → PRD → Prototype 链路；只同步实际存在的下游。
- Align 仅作 Design 输入参考，不是事实源；目标、范围和建设方式以 Design 为准，不经 Align 反向定源。
- 纯格式、措辞、排版或视觉表现修改可以只改对应下游，不触发 Design 同步。
- 纯格式/措辞/排版修改直接改 PRD 时，页面、动作和终端名称遵循 $BUNDLE/templates/prd.md 的当前格式：页面用 ###### 页面名称，动作用 **动作名称**，PC 页面不加（管理端）（PC端）后缀，特殊终端（移动端/小程序/自助终端）保留终端标识；格式只应用到被触达的页面或动作，不整篇迁移存量 PRD 格式。
- 无法判断影响范围时按高影响变化处理。
- 用户指令明确时一次 fix 连续完成：修改 Design → 同步所有实际存在且受影响的 PRD / Prototype 模块 → 针对性检查 → 更新下游依据；不停止等待重新确认。

## 输入事实源

1. 用户原始修改指令（必须明确改什么和改成什么）。
2. .workflow/status.json（如存在）。
3. 当前阶段人读产物。
4. $BUNDLE/contracts/fix-propagation-rules.md（唯一传播规则来源）。
5. 设计地图与设计集清单：定位唯一事实归属和受影响下游。
6. 实际受影响分支所需的上游/下游 references、templates、contracts 和确定性检查脚本；不读取无关阶段资源。

## 执行流程

1. 读取并解析用户修改指令；必须明确改什么和改成什么，缺一项就停止追问。
2. 判断修改对象属于目标/范围/建设方式、模块/页面/字段/规则/流程/状态/权限、跨系统/异常，还是表现层/措辞/格式。
3. 读取设计地图与设计集清单，从问题位置定位唯一事实归属文件（系统级基线/跨模块契约/模块设计）。
4. 读取 $BUNDLE/contracts/fix-propagation-rules.md，判定受影响的最深阶段和实际存在的下游分支。
5. 修改 Design 时按事务写入：单文件用 design-set.py stage-single/commit-single，多文件用 begin/commit；检查失败或中断用 recover。纯组织变化只更新 ID/路径/指纹和依据，下游保持 current。
6. 计算受影响下游：用 design-set.py check-inputs --artifact prd|prototype 检查当前依据；返回 incomplete（provenance_missing）时说明下游产物存在但无依据记录，先补 record-inputs 再继续；用户明确修改事实时连续同步所有实际存在且受影响的 PRD / Prototype 模块，无确认停顿。
7. 仅对实际存在且受影响的分支运行针对性检查：PRD 使用 `prd-consistency-check.py --module <模块名>`；Prototype 使用全量 `prototype-consistency-check.py --project-root .`。Prototype 的模块级判断由语义审查结合全量结果和对应 Design 模块完成。PRD 不存在时不伪造 PRD 检查，Prototype-only 项目仍需走合法原型检查路径。
8. 针对性检查通过后更新下游依据：record-inputs 更新 design_inputs 指纹，status 置 current、check_status 置 passed、清空 affected_by；检查失败时保留 affected 或 incomplete，不得伪装通过。

完成判据：修改对象与影响范围已判定；唯一事实归属已定位；Design 修改已按事务提交；所有实际存在且受影响的下游已同步；针对性检查已运行；下游依据与结果一致。

## Design 变化处理

- 用户明确说明改什么、改成什么：修改唯一事实归属并连续同步所有实际存在且受影响的下游，无确认停顿。
- Design 没变、下游不一致：只修错误下游，不修改 Design 和另一份下游。
- 外部未知修改（非当前任务造成）：当前任务触达时用 check-inputs 标记相关下游 affected，不自动传播、不自动改写下游。
- 纯组织变化（文件移动、拆分、排版、措辞）：更新指纹和依据，下游保持 current，不重新生成。
- 无法形成唯一产品事实（新产品选择、事实冲突或指令不完整）：停在具体业务问题询问，不要求确认 Design 或确认哈希。

## Fix 完成输出

Fix 完成后输出：

- 实际修改的事实归属文件和文件。
- 修改对象及影响范围。
- 实际同步的下游模块（PRD / Prototype，如适用）。
- 实际运行的检查及结果。
- 建议进入哪个 Review、检查哪些对象；不自动执行 Review。

建议格式：

~~~text
建议进入 [阶段] review，检查对象：[对象列表]
已同步下游：[PRD/Prototype 模块列表]（如适用）
~~~

## 失败与停止

- 传播契约缺失：报告具体路径，不凭记忆扩展传播矩阵。
- 指令含义不清或归属层无法判断：停止澄清，不直接改下游。
- 下游不存在：只处理实际存在的分支，不为了完整创建产物。
- 脚本检查失败：报告确定性错误，不伪装为通过。
- 发现 Design 语义需要修改但用户未说明正确结果：停在具体业务问题询问。

## 硬规则

- 不要求用户确认 Design、确认哈希或选择 Design 文件。
- 不自动创建不存在的 PRD 或 Prototype。
- 不把决策记录、metadata 或旧 Review 结果当作产品事实源。
- 不整篇重写与修改无关的产物。
- 不自动调用 spm-fix 自身形成循环，不自动推进阶段。
