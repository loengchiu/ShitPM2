---
name: spm-design-review
description: "Design Review：独立审查 Design 基线的结构完整性、业务质量、一致性和高影响缺口。触发于用户要求审查 Design；默认局部审查，整套 Design 仅在用户明确要求完整 Review 时审查。只输出第二意见，不修改或推进。"
---

## 路径与资源

从系统 prompt 读取 `$BUNDLE`。项目文件使用当前根目录的 `.workflow/` 和 `output/`；共享依据使用 `$BUNDLE/contracts/`、`$BUNDLE/schemas/`、`$BUNDLE/references/` 和 `$BUNDLE/scripts/python/`。

流程开始时输出模型建议：需要发现业务、权限、状态、跨模块或方案风险时使用深度推理模型；只做标题、结构、文件、格式和明显缺失检查时可用轻量模型或脚本；无法判断时使用深度推理模型。

## 职责边界

Review 是独立第二意见，不是生成门禁，也不承担计划内补全。

- 只审查，不修改正式 Design 文件、设计集清单、决策记录或 metadata。
- 审查后停在结论输出，不自动修复、不自动确认、不自动推进阶段，不自动调用 `spm-fix`。
- 审查只依赖 Design 集合与修改状态，不要求 metadata、`page-fields.json` 或其他 Review 存在。
- 只有输入文件不存在、不可读或完全无法解析时才硬阻塞。
- 结论必须区分确定性问题、产品风险和待用户决策问题。

## 默认局部 Review

默认只审查用户指定范围的目标文件闭包；完整 Review（整套 Design）只由用户明确触发。

## 执行流程

1. 确定局部或完整 Review 范围，读取设计地图、设计集清单、目标 Design 文件闭包（目标文件 + 必要系统基线 + 直接契约 + 真正相关的相邻模块）、Design 修改状态、用户指定范围和最近 Review（如有）。修改状态只作为上下文，不构成 Review 门禁。**完成条件**：审查范围、目标文件闭包和每个输入的来源路径已明确。
2. 确认设计集清单可解析且目标 Design 文件可读。缺失或不可读时停止；缺章节、冲突和质量问题继续作为审查问题。**完成条件**：输入可供审查，或阻塞路径与原因已具体记录。
3. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/design-review-checklist.md` 和 `$BUNDLE/references/design-quality-rubric.md` 的独立 Review 部分；按专项契约的触发证据读取对应权威规则来源。只有检测到 `.workflow/metadata/design/` 时才读取 `$BUNDLE/contracts/metadata-anchor-rules.md`。**完成条件**：每个适用检查项的权威依据已加载；缺失依据已按路径记录。
4. 从人读 Design 而不是 metadata 判断产品事实，按专项契约逐项审查；旧 metadata 仅在存在时作为兼容材料。**完成条件**：每个适用检查项均有证据和结论；无法判断项已标记为产品风险或待用户决策，未被默认通过。
5. 按公共契约写入 `.workflow/reviews/design-review-N.md`。**完成条件**：结论符合三档门槛，每个 P0/P1 可追溯到位置、影响和建议，三类问题分布及上游同步信息完整。
6. 输出审查结论后停止，等待用户决定是否修复。**完成条件**：未修改 Design、设计集清单、决策记录或 metadata，未确认或推进阶段。

## 判定与失败

- 结论门槛、问题分级和输出字段以公共契约与 Design 专项契约为准。
- 违反 Design 的高影响完整性、状态闭环、权限或事实源规则时，不把问题交给下游生成 Skill 补全。
- Review 通过不等于 Design 可生成下游；下游可用性由 Design 修改状态和事实闭包决定。
- 失败处理按公共契约执行；共享契约或必要依据缺失时报告具体路径，不凭记忆重建检查项。
