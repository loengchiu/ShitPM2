---
name: spm-prototype-review
description: "Prototype Review：独立审查 Prototype 的源码工程、构建、路由、Design 一致性、状态权限表达和视觉规范执行。触发于用户要求审查 Prototype；只输出第二意见，不修改、修复或推进。"
---

## 目的与边界

Review 是独立第二意见，事实基线是被审 Prototype 模块登记的 Design 依据。读取当前项目的 `output/design/`、`output/prototype/`、`.workflow/`，以及 `$BUNDLE/contracts/`、`$BUNDLE/scripts/python/` 和契约指向的 references。

- 内容只读：不手工编辑 `src/`、`index.html`、`dist` 或其他原型文件。`npm ci`、`npm run build` 和构建预览产生的 `node_modules/`、`dist/` 仅作为验证副作用，不作为 Review 修复或交付修改。
- 不自动修复、确认、推进或调用 `spm-fix`。
- PRD 只作冲突参考；不要求 metadata、`pages.json` 或其他 Review 产物。
- 结论区分确定性问题、产品风险和待用户决策项；无法判断的项显式标记。

## 审查流程

1. 读取 `.workflow/provenance/prototype.json` 中该 target 的 `design_inputs` 对应正式 Design 文件、Design 修改状态和 Prototype 源码工程；PRD 如存在，仅作为冲突线索。**完成条件**：Design 依据和被审源码均可读；缺失或无法解析时直接输出阻塞，不继续假设。
2. 运行：

```text
python $BUNDLE/scripts/python/prototype-source-check.py --project-root .
```

**完成条件**：源码工程检查结果已记录。只有 dist/compiled.js 时至少记为 structure P1，结论不能为“通过”。
3. 在 `output/prototype/` 执行 `npm ci`、`npm run build`，并用 `npm run preview` 或等价构建预览打开默认页和全部注册路由。**完成条件**：构建结果及每条注册路由的白屏/console 观察结果均已记录；构建失败或路由白屏按 structure P1 处理，跳过后续业务语义审查但仍输出结论。
4. 运行：

```text
python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root . --module <被审模块>
```

**完成条件**：一致性结果已作为审查证据记录；脚本结果不是 Review 启动门禁。
5. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/prototype-review-checklist.md` 和 `$BUNDLE/references/prototype-writing.md`；发现多页面 shell、导航、路由或空白页问题时再读取 `$BUNDLE/references/prototype-shell.md`。**完成条件**：专项契约的每个适用结构、内容和一致性检查项均有证据和结论。
6. 从 Design 页面清单提取全部页面，与 `src/routes.jsx` 逐项对照 `存在 / 缺失 / 幻觉`；再核对字段、状态、主路径、权限、操作限制、异常反馈和 Design 未授权高影响行为。**完成条件**：每个页面和关键对象都有明确结论或待决策标记。
7. 读取 `$BUNDLE/references/prototype-visual-spec.md`，按 Prototype 专项契约审查视觉事实源、共享 UI、状态矩阵、图标和图表。**完成条件**：每个适用视觉检查项均有证据和结论；表现问题与业务语义问题分开，Design 冲突已设置 `needs_upstream_sync`。
8. 根据被审源码的真实场景读取 `$BUNDLE/references/prototype-component-behavior.md` 中全部适用章节；至少覆盖命中的表格、Form/Modal、Portal/响应式、回退和跨层契约规则。**完成条件**：每个适用项均有证据和结论；不存在的场景标记不适用，不因生成路径变短而漏审；违反行为规范的项按表现问题输出位置、影响和建议，不修改源码。
9. 按公共契约写入 `.workflow/reviews/prototype-review-N.md`。**完成条件**：结论符合三档门槛，每个 P0/P1 可追溯到位置、影响和建议，逐页面结果、三类问题分布及上游同步信息完整；未把验证副作用当作修复或交付修改，输出后停止。

## 判定与失败

- 结论门槛、问题分级和专项严重度以公共契约与 Prototype 专项契约为准。
- Design 待确认事实不能在 Prototype 中被当成确定行为；只报告问题并设置 `needs_upstream_sync`。
- 失败处理按公共契约执行；脚本、构建或共享依据失败时保留原始错误，不把退出码包装成质量证明。
