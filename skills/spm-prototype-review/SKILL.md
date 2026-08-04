---
name: spm-prototype-review
description: "Prototype Review——独立审查原型页面覆盖、Design 一致性、状态/交互/权限表达和高影响行为。用于用户要求 review、审查或检查 Prototype 时；不修改原型、不自动修复、不自动推进。"
---

## 路径与资源

使用当前项目根目录读取 `output/design/`、`output/prototype/` 和 `.workflow/`；使用 `$BUNDLE/contracts/`、`$BUNDLE/schemas/`、`$BUNDLE/scripts/python/` 和契约指定的 references。

流程开始时输出模型建议：需要发现业务、权限、状态、跨页面或高影响交互风险时使用深度推理模型；只做页面存在性、结构和明确格式检查时可用轻量模型或脚本；无法判断时使用深度推理模型。

## 职责边界

- Review 是独立第二意见，只审查不修改 `output/prototype/index.html` 或其他原型文件。
- 审查后停在结论输出，不自动修复、不自动确认、不自动推进、不自动调用 `spm-fix`。
- 审查只依赖 Design 与 Prototype，不要求 metadata、`pages.json`、PRD 或其他 Review 存在。
- 只有 Design 或 Prototype 输入缺失、不可读或完全无法解析时才硬阻塞。
- 结论分为确定性问题、产品风险和待用户决策问题。

完成判据：审查清单全部逐项执行并记录结论；产出含结论、问题清单（位置/影响/建议）；无修改产物、无自动推进；无法判断项已显式标注而非默认通过。

## 执行流程

1. 读取确认版 `output/design/design.md`、`output/prototype/index.html`、必要的页面资源、Design confirmation 状态和 PRD（如存在，仅用于冲突参考）。Prototype 必须以 Design 为事实源。
2. 确认 `output/prototype/index.html` 存在、可读且可解析；缺失或不可读时停止，缺页面、内容不足、冲突和质量问题继续作为审查问题。
3. 运行：

```text
python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root .
```

一致性检查结果作为审查问题，不把检查当作 Review 启动门禁。
4. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/prototype-review-checklist.md` 和 `$BUNDLE/references/prototype-writing.md`；发现多页面 shell、路由或空白页问题时再读取 `$BUNDLE/references/prototype-shell.md`；从 Design 的“页面清单”提取全部页面，逐项输出 `存在 / 缺失 / 幻觉`，并审查字段、状态、主路径、权限、操作限制、异常反馈和 Design 未授权高影响行为。
5. 按 `$BUNDLE/schemas/review-result.schema.json` 输出：
   - 机读：`.workflow/reviews/prototype-review-N.json`
   - 人读：`.workflow/reviews/prototype-review-N.md`
   - 必须包含逐页面检查项、`verdict`、`issues`、`issue_layer`、`affected_objects`、`needs_upstream_sync`、`reviewed_at`；P2 记录但不计入 `verdict`。
6. 输出审查结论后停止，不修改任何原型文件。

## 判定与失败处理

- 共享契约的统一门槛：零 P0/P1 为“通过”；零 P0 且 1 个 P1 为“有问题需修改”；存在 P0 或至少 2 个 P1 为“阻塞”。页面幻觉、Design 未授权高影响行为和主路径不可用按契约处理。
- Design 的“待确认”事实不得在 Prototype 中静默拍板；需要回上游时只设置 `needs_upstream_sync` 并报告受影响对象。
- 输入缺失、不可读或无法解析时硬阻塞并报告具体路径；脚本或契约缺失时报告错误，不伪装为通过。
- 不运行 `stage-prep.py`，不生成 metadata，不自动调用 Fix。
