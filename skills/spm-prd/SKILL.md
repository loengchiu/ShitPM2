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

## 输入事实源

按以下顺序读取：

1. `.workflow/status.json`（如存在，仅用于导航和兼容）。
2. `output/design/design.md`：唯一产品事实源。
3. `$BUNDLE/templates/prd.md`：章节骨架。
4. `$BUNDLE/references/prd-writing-rules.md`：完整写作规则和结构规则。满足示例加载条件时，再读取 `$BUNDLE/references/prd-writing-examples.md`；示例文件只提供正反例。
5. `$BUNDLE/contracts/prd-writing.profile.json`：机读写作约束。
6. `$BUNDLE/references/prd-glossary-format.md`：名词说明规则。
7. `$BUNDLE/references/prd-versioning.md`：版本记录规则。
8. `$BUNDLE/references/prd-scene-checklist.md`：场景覆盖自检。
9. `output/prototype/`（如存在，仅用于发现冲突；与 Design 冲突时以 Design 为准并报告）。

不得读取 `.workflow/metadata/design/` 作为产品事实，也不得读取 `output/design/decision-notes.md` 作为事实输入。

## 首次写入前的语义对照

正式写入 `output/prd/prd.md` 前必须完成 Design → PRD 语义对照，并输出对照结论：

- 从 Design 列出模块、页面、字段、状态、权限和关键流程。
- 逐项核对角色、核心对象、关键动作、流程、权限、状态、异常、模块边界和跨系统责任，确认 PRD 不超出 Design 范围。
- 标记 Design 中的待确认项，PRD 不得静默拍板。
- 对 Design 未授权但 PRD 可能需要的高影响事实，写入 `output/prd/decision-notes.md` 的“待确认”。
- 发现已有 Prototype 与 Design 冲突时，以 Design 为准，并写入 决策记录。

## 生成策略

1. 通读 `output/design/design.md`，建立整体认知。
2. 完成首次写入前的语义对照。
3. 完整读取并执行 `$BUNDLE/references/prd-writing-rules.md`、名词说明、版本记录、场景检查清单和配置文件；只有正在生成高复杂动作、规则无法直接决定组织方式、自检命中失败模式或用户要求对照示例时，才读取 `$BUNDLE/references/prd-writing-examples.md`。不得只依赖模板注释或模型记忆。
4. 按 `$BUNDLE/templates/prd.md`，依模块、页面和动作生成 `output/prd/prd.md`。
5. 大型 Design（超过 10 页或 50 个字段）可以分批生成；每批完成后立即自检字段和语义对齐，最后再做全量检查。
6. 不使用分页流水线、逐页 Checkpoint、page-fields 索引等能力补偿型机制。

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

PRD 必须包含版本记录表、名词说明和详细需求说明；每个小模块末尾归位字段定义表及适用的状态机表，大模块开头归位权限规则。文档概述、范围、业务流程、验收标准汇总、风险与待确认等辅助章节，只在存在真实内容时保留，不用空标题占位。具体结构和写法以对应参考文档、模板和配置文件为准。

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
