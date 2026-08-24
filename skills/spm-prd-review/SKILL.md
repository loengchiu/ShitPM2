---
name: spm-prd-review
description: "PRD Review：独立审查 PRD 的业务闭环、写作质量、Design 一致性、场景覆盖、权限状态和未授权高影响事实。触发于用户要求审查 PRD；只输出第二意见，不修改、修复或推进。"
---

## 路径与资源

从当前项目根目录读取 `output/` 和 `.workflow/`；从 `$BUNDLE/` 读取 `contracts/`、`schemas/`、`references/` 和 `scripts/python/`。

流程开始时根据问题复杂度选择推理深度；涉及业务闭环、权限、状态、跨模块或高影响事实时使用深度推理模型，无法判断时按深度推理模型处理。

## 职责边界

- Review 是独立第二意见，不是流程门禁，也不承担计划内补全。
- 只审查，不修改 `output/prd/prd.md`、Design 或决策记录，不自动调用 `spm-fix`。
- 审查只依赖 PRD 模块记录的设计依据与 Design 修改状态，不要求 metadata、`page-fields.json` 或其他 Review 资产存在。
- 只有输入文件不存在、不可读或完全无法解析时才硬阻塞；缺章节、内容不足、冲突和写作质量问题继续作为审查问题。
- 每条问题按 `$BUNDLE/contracts/review-checklist.md` 的 `red`、`risk` 或 `decision` 标注，并按既有 P0/P1/P2 门槛输出。

## 执行流程

1. 读取被审 PRD 模块的 Design 依据（`.workflow/provenance/prd.json` 中该 target 的 `design_inputs` 对应正式 Design 文件）、`output/prd/prd.md`、Design 修改状态和已有 Review 上下文（如有）。修改状态只作为上下文，不构成 Review 门禁。**完成条件**：被审模块、Design 输入闭包和 PRD 均可读；否则输出具体阻塞项并停止。
2. 运行：

```text
python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md
```

目标文件不存在、不可读或无法解析时停止；缺章节、内容不足、冲突和写作质量问题继续作为审查问题。**完成条件**：命令、退出码和诊断已记录；脚本失败未被写成通过。
3. 运行：

```text
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root . --module <被审模块>
```

引用 JSON 中的三类输出：①确定性冲突（`missing`、`hallucinated`、`attribute_mismatch`、权限反转）标为 `red`；②可能遗漏逐条判定为 `risk`、`decision` 或不成立；③`needs_semantic_judgment`（含结构适配差异）按业务语义判定。脚本返回 `0` 不代表 PRD 通过，返回 `1` 也不替代问题定位。**完成条件**：三类输出均已处理；无法提取、可能遗漏和语义判断项已写为明确结论或“未评估”，未被默认通过。
4. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/prd-review-checklist.md`、`$BUNDLE/references/prd-writing-rules.md` 和 `$BUNDLE/contracts/prd-writing.profile.json`；按专项契约的触发证据读取 `$BUNDLE/references/prd-writing-examples.md`、`prd-glossary-format.md`、`prd-versioning.md` 或 `prd-scene-checklist.md`。**完成条件**：专项契约的每个适用项均有证据和结论；契约规定的审查顺序、统计页逐页验收和复杂动作逐项验收已执行；无法判断项已显式标记。
5. 按公共契约写入 `.workflow/reviews/prd-review-N.md`。**完成条件**：结论符合三档门槛，每个 P0/P1 可追溯到位置、影响和建议，三类问题分布及上游同步信息完整。
6. 输出审查结论后停止。**完成条件**：未修改 PRD、Design 或决策记录，未调用 `spm-fix` 或推进阶段。

## 判定与失败

- 结论门槛、问题分级、专项严重度和上游同步条件以公共契约与 PRD 专项契约为准。
- Review 通过不改变 Design 修改状态，也不自动推进阶段。
- 失败处理按公共契约执行；确定性脚本失败但文件可读时继续人读审查并保留原始错误；共享依据缺失时报告具体路径，不凭记忆重建检查项。
