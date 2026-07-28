---
name: spm-prd
description: "PRD 阶段——根据已确认的 Design 直接生成研发可评审的 PRD。用于用户要求生成 PRD、需求规格或产品需求文档时；必须通过 Design 确认，保持 Design 语义，不依赖 Prototype，不把高影响未决事实静默拍板。"
---

## 路径解析

从系统 prompt 的 `ShitPM bundle root:` 读取 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 路径使用 `$BUNDLE/` 前缀。
- `.workflow/`、`output/` 路径使用当前项目根目录。

## 模型建议（运行时输出）

流程开始时必须输出模型等级和推理深度建议：

- **深度推理模型**：Design 复杂，需要全文语义理解、跨模块一致展开或处理未决事实。
- **轻量模型**：Design 决策完整、关系简单，主要按模板展开明确规格。
- **无法判断时**：使用深度推理模型。

模型在流程开始前选择，执行中不切换；建议必须作为实际运行输出呈现。

## 职责与准入

`spm-prd` 是 Design 的直接下游，不依赖 Prototype，也不读取 Design 的 决策记录 作为产品事实。

准入条件：

1. `output/design/design.md` 存在且可读。
2. Design 确认 有效。运行：

   ```text
   python $BUNDLE/scripts/python/design-confirmation.py --project-root . check
   ```

3. Design 中的高影响待确认事实已经在正文中可见，PRD 不得自行拍板。

检查非成功时停止，不生成或覆盖 PRD，提示用户先确认或重新确认 Design：

```text
python $BUNDLE/scripts/python/design-confirmation.py --project-root . confirm
```

不要求以下前置条件：Design metadata、page-fields、Prototype、Design Review 通过。

## 运行时上下文装载

规范性规则由 `$BUNDLE/contracts/context-loading.manifest.json` 编译为分阶段上下文包，不再默认全文读取所有 PRD 规则和示例。`output/design/design.md` 仍是唯一产品事实源；运行包只用于当前执行、校验和审计。
执行前可用 `context-budget.py` 对规划包、模块输入和 Design 做保守体量检查；该检查默认只报告，不替主 Agent 拆分模块。需要确定性拒绝超限时，显式传入 `--max-tokens <n> --fail-on-budget`。

### P0-P1：确认门与全局规划

先运行 Design confirmation 检查，并读取完整 `output/design/design.md`。随后生成全局规划包：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass plan
```
先用同一选择执行一次预算预检（默认只报告，不设未经用户确认的硬上限）：

```text
python $BUNDLE/scripts/python/context-budget.py --bundle-root $BUNDLE --project-root . --stage prd --pass plan --input output/design/design.md --json
```

规划包包含 PRD 边界、结构、名词、版本和模板；不包含示例，也不包含按场景展开的专项检查。Prototype 不作为事实源；如存在，先用确定性脚本提取页面、路由、动作和可见字段等结构线索：

```text
python $BUNDLE/scripts/python/prototype-structure.py --project-root . --input output/prototype/index.html --output .workflow/runtime/context/prd/prototype-structure.json
```

只有结构线索显示疑似冲突时，才定向读取对应 HTML 片段。

### P2：模块写作与示例按章节加载

大型 PRD 仅在业务模块边界清晰且单次写作会明显增加上下文负担时按模块生成内部草稿；“10 页或 50 个字段”仅是经验参考，不是硬门槛。小型 PRD 由主 Agent 一次完成。先建立适用性文件，再按模块生成专项包：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass module --card <scene-key> --example <example-key>
```

`--example` 只选择命中的示例章节，例如 `complex-action`、`action-body`、`field-table`；不为“保险”加载 `prd-writing-examples.md` 全文。模块草稿只能写入 `.workflow/runtime/context/prd/handoff/`，不能直接覆盖 `output/prd/prd.md`，共享角色、状态、字段和规则由主 Agent 统一维护。

### P3-P4：全局整合与生成内审查

主 Agent 读取各模块交接结果、完整 Design 和全局不变量，统一处理跨模块承接、字段归宿、状态/权限一致性、版本记录和决策记录。整合和生成内审查使用新的干净上下文：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass integration --card <scene-key>
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass verification
```

规则来源缺失、章节标记不完整、示例命中条件无法说明或交接结果缺少来源时停止，不凭模型记忆继续。不得读取 `.workflow/metadata/design/` 作为产品事实，也不得读取 `output/design/decision-notes.md` 作为事实输入。

## Sub-agent 边界

默认不启用 Sub-agent。大型 PRD 且模块边界清晰时，才可按业务模块产生内部草稿或模块检查结果，并遵守 `$BUNDLE/contracts/subagent-context-contract.md`。共享角色、状态、权限、字段和跨模块规则只能由主 Agent 统一维护；Sub-agent 不得直接覆盖 `output/prd/prd.md`。

## 首次写入前的语义对照

正式写入 `output/prd/prd.md` 前必须建立 Design → PRD 承接矩阵，并输出覆盖结论。矩阵至少逐项核对：

- 目标、非目标、用户、场景、范围和边界；
- 模块、页面、关键动作、动作前置条件、成功/失败结果和后续责任；
- 全部字段及类型、必填、长度、枚举、格式、范围/精度、默认值、业务来源和说明；
- 每个字段的交付归宿：页面展示、页面输入、查询筛选、动作依赖或系统内部字段；
- 角色、页面/按钮/字段权限、数据范围和敏感操作限制；
- 状态集合、迁移条件、操作人、限制、业务副作用、回退/撤回/恢复；
- 业务规则、唯一性、数据生命周期、时间口径、列表默认、文件、导入导出、批量、重复/并发和异常补偿；
- 系统边界、跨系统事实源/同步方向/失败结果/最终责任、实际适用的产品级非功能约束和验收条件。

承接矩阵只用于生成前自检，不成为新的事实源，也不写入 PRD 正文。发现 Design 已有事实未承接时补入 PRD；发现 Design 本身缺少会改变实现的高影响事实时停止并回退 Design，不能由 PRD 补写。Design 中的待确认项不得静默拍板；已有 Prototype 与 Design 冲突时以 Design 为准，并写入 决策记录。

## 生成策略

1. 通读 `output/design/design.md`，建立整体认知；Design 是唯一产品事实源。
2. 通过 `plan` 包完成全局承接规划和首次写入前的语义对照。
3. 通过 `module` 包按 Design 已定义的业务模块边界写作；只在命中具体复杂动作或写作难点时加载对应示例章节，不把示例当规范性规则。module pass 是受边界约束的内部草稿流程，不按页面、字段或任意篇幅切片。
4. 通过 `integration` 包由主 Agent 完成全局整合，再通过 `verification` 包完成生成内成品审查。
5. 按模板和写作规则生成 `output/prd/prd.md`。
6. 每个关键动作按场景展开前置条件、可操作状态、输入与校验、对象/字段变化、成功/失败反馈、状态及副作用、重复执行结果、恢复路径和下一责任人；不存在的场景跳过。
7. 每个 Design 字段都必须进入 PRD 字段表，并归属于页面展示、页面输入、查询筛选、动作依赖或系统内部字段；内部字段不要求虚构页面落点，但必须保留业务来源和用途。
8. 大型 PRD 可以在业务模块边界清晰且单次写作会明显增加上下文负担时分批生成；“10 页或 50 个字段”仅是经验参考，不是硬门槛。每批完成后立即自检字段和语义对齐，最后再做全量检查。
9. 不使用分页流水线、逐页 Checkpoint、page-fields 索引等能力补偿型机制；module pass 只能按 Design 业务模块边界拆分。

## 过程审计与检查顺序

按 `$BUNDLE/templates/decision-notes.md` 生成 `output/prd/decision-notes.md`，基准是 Design，按“设计决策、偏离、权衡、待确认”四类记录；无内容写“无”。决策记录只用于审计，不参与 Design 确认，也不是下游事实输入。

PRD 正式交付前严格按以下顺序运行：

1. `python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md`
2. `python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .`
3. 两项通过后，运行 `python $BUNDLE/scripts/python/artifact-guard.py --project-root . record --stage prd` 登记 Design 和 PRD 来源哈希。
4. 运行 `python $BUNDLE/scripts/python/artifact-guard.py --project-root . check --stage prd` 复核产物未陈旧。

确定性检查失败时先修复或报告，不能输出“通过”；不能为了消除检查缺口而在 PRD 中发明 Design 没有的事实。

## 输出与状态

写入：

- `output/prd/prd.md`：按模板生成的人读 PRD。
- `output/prd/decision-notes.md`：相对于 Design 的审计记录。

PRD 必须包含版本记录表、名词说明和详细需求说明；每个小模块末尾归位 7 列字段定义表及适用的状态机表，大模块开头归位权限规则。字段定义表完整承接 Design 字段属性和系统内部字段；页面动作承接字段交付归宿、状态副作用、数据生命周期及适用的列表、文件、导入导出、批量、重复/并发和跨系统结果。文档概述、范围、业务流程、验收标准汇总、风险与待确认等辅助章节，只在存在真实内容时保留，不用空标题占位。具体结构和写法以对应参考文档、模板和配置文件为准。

更新 `.workflow/status.json`：

- `current_stage`：`"prd"`
- `artifacts.prd`：`"output/prd/prd.md"`
- `next_recommended`：可省略或设为 `null`

完成报告至少说明 PRD 已生成、决策记录已写入，并提示可调用 `/spm-prd-review`；不自动推进 Prototype，不自动修改 Design 确认。

## 失败与停止

- `design.md` 不存在或不可读：停止，提示先完成 Design。
- Design 确认 失败：停止，不生成或覆盖 PRD。
- 模板、参考文档或配置文件缺失：报告具体路径并停止，不凭记忆生成完整 PRD。
- Design 语义无法对照：停止并暴露冲突，不静默改写。
- Design 待确认项被 PRD 结论化：移入 决策记录 的“待确认”；仍无法推进时停止并请求用户决定。
- lint、consistency 或 artifact guard 失败：先修复或报告，不输出“通过”。

## 不做的事

- 不重新定义范围，不脑补 Design 没确认的页面、字段、权限、状态、流程或模块边界。
- 不把 PRD 变成字段、权限、状态的第二事实源。
- 不执行 Review，不自动修复 Review 问题，不自动推进阶段。
- 不依赖 Prototype 存在；不以 Prototype 覆盖 Design。
- 不要求输出思维过程，只输出结论、产物、决策和待确认项。
