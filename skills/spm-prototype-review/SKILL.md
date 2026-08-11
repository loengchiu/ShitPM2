---
name: spm-prototype-review
description: "Prototype Review——独立审查原型源码工程完整性、构建可用性、页面覆盖、Design 一致性、状态/交互/权限表达和高影响行为。用于用户要求 review、审查或检查 Prototype 时；不修改原型、不自动修复、不自动推进。"
---

## 路径与资源

使用当前项目根目录读取 `output/design/`、`output/prototype/` 和 `.workflow/`；使用 `$BUNDLE/contracts/`、`$BUNDLE/schemas/`、`$BUNDLE/scripts/python/` 和契约指定的 references。

流程开始时输出模型建议：需要发现业务、权限、状态、跨页面或高影响交互风险时使用深度推理模型；只做页面存在性、结构和明确格式检查时可用轻量模型或脚本；无法判断时使用深度推理模型。

## 职责边界

- Review 是独立第二意见，只审查不修改 `output/prototype/src/`、`output/prototype/index.html` 或其他原型文件；不手工修改 dist。
- 审查后停在结论输出，不自动修复、不自动确认、不自动推进、不自动调用 `spm-fix`。
- 审查只依赖 Design 与 Prototype，不要求 metadata、`pages.json`、PRD 或其他 Review 存在。
- 只有 Design 或 Prototype 输入缺失、不可读或完全无法解析时才硬阻塞。
- 结论分为确定性问题、产品风险和待用户决策问题。
- Review 可以运行构建（npm run build）和构建预览作为验证动作，构建产物 dist 由标准 scripts 生成，不属于手工修改。

完成判据：审查清单全部逐项执行并记录结论；产出含结论、问题清单（位置/影响/建议）；无修改产物、无自动推进；无法判断项已显式标注而非默认通过。

## 执行流程

1. 读取确认版 `output/design/design.md`、`output/prototype/` 源码工程、Design confirmation 状态和 PRD（如存在，仅用于冲突参考）。Prototype 必须以 Design 为事实源。
2. 运行源码工程检查：

```text
python $BUNDLE/scripts/python/prototype-source-check.py --project-root .
```

   通过是 Review 启动前提。若只有 dist/compiled.js 没有 src：不继续业务审查，直接输出“源码工程缺失”为 structure P1 且结论不得为“通过”。
3. 运行构建与构建预览验证：

```text
cd output/prototype
npm ci
npm run build
npm run preview
```

   构建失败时记录为 structure 问题并停止业务审查；构建成功后在构建预览中逐个打开默认页和全部注册路由，检查白屏和 console 错误。
4. 运行：

```text
python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root .
```

   一致性检查结果作为审查问题，不把检查当作 Review 启动门禁。
5. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/prototype-review-checklist.md` 和 `$BUNDLE/references/prototype-writing.md`；发现多页面 shell、路由或空白页问题时再读取 `$BUNDLE/references/prototype-shell.md`；从 Design 的“页面清单”提取全部页面，与 `src/routes.jsx` 路由表逐项对照输出 `存在 / 缺失 / 幻觉`，并审查字段、状态、主路径、权限、操作限制、异常反馈和 Design 未授权高影响行为。
6. 输出人读审查结果：`.workflow/reviews/prototype-review-N.md`，必须包含逐页面检查项、审查结论（通过 / 有问题需修改 / 阻塞）、问题清单（每条含编号、严重级别、位置、影响、建议）、三类问题分布（structure / content / consistency）、`needs_upstream_sync`、`affected_objects` 和下一步建议；P2 记录但不计入审查结论。
7. 输出审查结论后停止，不修改任何原型文件。

## 判定与失败处理

- 共享契约的统一门槛：零 P0/P1 为“通过”；零 P0 且 1 个 P1 为“有问题需修改”；存在 P0 或至少 2 个 P1 为“阻塞”。页面幻觉、Design 未授权高影响行为和主路径不可用按契约处理。
- **只有 dist 没有 src（源码工程缺失）至少记为 structure P1，且审查结论不得为“通过”**。
- 构建失败、路由无法打开、默认页或注册路由白屏按 structure P1 处理，不得通过。
- Design 的“待确认”事实不得在 Prototype 中静默拍板；需要回上游时只设置 `needs_upstream_sync` 并报告受影响对象。
- 输入缺失、不可读或无法解析时硬阻塞并报告具体路径；脚本或契约缺失时报告错误，不伪装为通过。
- 不运行 `stage-prep.py`，不生成 metadata，不自动调用 Fix。
