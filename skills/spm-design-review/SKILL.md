---
name: spm-design-review
description: "Design Review——独立审查 Design 基线的结构完整性、业务质量、一致性和高影响缺口。用于用户要求 review、审查、检查 Design 时；不修改产物、不自动推进、不替代 Design 生成。"
---

## 路径与资源

从系统 prompt 读取 `$BUNDLE`。项目文件使用当前根目录的 `.workflow/` 和 `output/`；共享依据使用 `$BUNDLE/contracts/`、`$BUNDLE/schemas/`、`$BUNDLE/references/` 和 `$BUNDLE/scripts/python/`。

流程开始时输出模型建议：需要发现业务、权限、状态、跨模块或方案风险时使用深度推理模型；只做标题、结构、文件、格式和明显缺失检查时可用轻量模型或脚本；无法判断时使用深度推理模型。

## 职责边界

Review 是独立第二意见，不是生成门禁，也不承担计划内补全。

- 只审查，不修改 `output/design/design.md`、决策记录或 metadata。
- 审查后停在结论输出，不自动修复、不自动确认、不自动推进阶段，不自动调用 `spm-fix`。
- 审查只依赖 Design 与确认状态，不要求 metadata、`page-fields.json` 或其他 Review 存在。
- 只有输入文件不存在、不可读或完全无法解析时才硬阻塞。
- 结论必须区分确定性问题、产品风险和待用户决策问题。

完成判据：审查清单全部逐项执行并记录结论；产出含结论、问题清单（位置/影响/建议）；无修改产物、无自动推进；无法判断项已显式标注而非默认通过。

## 执行流程

1. 读取 `output/design/design.md`、Design confirmation 状态、用户指定范围和最近 Review（如有）。confirmation 只作为上下文，不构成 Review 门禁。
2. 确认 `output/design/design.md` 存在、可读且可解析；缺失或不可读时停止，缺章节、冲突和质量问题继续作为审查问题。
3. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/design-review-checklist.md` 和 `$BUNDLE/references/design-quality-rubric.md` 的独立 Review 评分部分；再按具体检查项读取 `$BUNDLE/references/design-state-format.md`、`design-flow-format.md`、`design-writing.md` 等细则。只有检测到 `.workflow/metadata/design/` 时才读取 `$BUNDLE/contracts/metadata-anchor-rules.md`。按检查项审查字段密度、状态闭环、流程密度、权限、页面/字段落点、高影响缺口、横切能力和旧 metadata（仅存在时）。重点核对待办、提醒、编号、字典、文件/档案、审计侧/被审侧入口、自动动作失败、删除传播、枚举来源、独立上限以及页面展示状态。
5. 从人读稿而不是 metadata 判断 Design 事实；不能确认的内容标记为产品风险或待用户决策，不擅自补全。
6. 输出人读审查结果：`.workflow/reviews/design-review-N.md`，必须包含审查结论（通过 / 有问题需修改 / 阻塞）、问题清单（每条含编号、严重级别、位置、影响、建议）、三类问题分布（structure / content / consistency）、`needs_upstream_sync`、`affected_objects` 和下一步建议；P2 记录但不计入审查结论。
7. 输出审查结论后停止，等待用户决定是否修复或确认。

## 判定与停止

- 共享契约的统一门槛：零 P0/P1 为“通过”；零 P0 且 1 个 P1 为“有问题需修改”；存在 P0 或至少 2 个 P1 为“阻塞”。
- 违反 Design 的高影响完整性、状态闭环、权限或事实源规则时，不把问题交给下游生成 Skill 补全。
- Review 通过不等于 Design confirmation，不自动允许 PRD 或 Prototype。

## 失败处理

- 文件不存在或不可读：输出具体阻塞项，不绕过。
- 共享契约、schema 或必要脚本缺失：报告路径，不凭记忆补写完整清单。
- 不运行 `stage-prep.py`，不生成 metadata，不修改被审查产物。
