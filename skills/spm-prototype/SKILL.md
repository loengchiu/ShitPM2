---
name: spm-prototype
description: "Prototype 阶段——根据已确认的 Design 生成可运行、可讨论的 HTML 原型。用于用户要求生成、修改或查看原型时；直接读取 Design，不依赖 PRD，必须保持 HTML + Vue + Tailwind + daisyUI + 本地 lib 架构，不自行引入 Design 未授权的高影响行为。"
---

## 路径与资源

从系统 prompt 读取 `$BUNDLE`。bundle 资源使用 `$BUNDLE/templates/`、`$BUNDLE/references/`、`$BUNDLE/lib/` 和 `$BUNDLE/scripts/python/`；项目产物使用当前项目根目录的 `output/` 和 `.workflow/`。

流程开始时输出模型建议：页面少且行为明确、主要做既定表达与实现时可用轻量或代码模型；涉及跨页面任务路径、复杂交互或高影响表达时使用深度推理模型；无法判断时使用深度推理模型。

## 职责与准入

- Prototype 是 Design 的直接下游，不依赖 PRD、Design metadata、`page-fields`、分页流水线或逐页字段计数。
- `output/design/design.md` 必须存在、可读且通过 Design confirmation gate；失败时停止，不生成或覆盖 Prototype。
- HTML + Vue + Tailwind + daisyUI + 本地 `lib/` 架构固定，不引入新的构建链、外部 CDN 或 `el-` 前缀组件。
- 原型只表达 Design，不重新定义业务规则、权限、状态、跨系统责任、模块边界或其他高影响行为。

确认检查：

```text
python $BUNDLE/scripts/python/design-confirmation.py --project-root . check
```

退出码非 0 或 Design 未确认/哈希不一致时停止，用自然语言询问用户是否确认当前 Design；仅在用户明确确认后，由你运行 `confirm` 记录哈希，再继续。不得在用户未明确确认前运行 `confirm`，也不要求用户输入命令行。不要求 PRD、metadata 或 Prototype Review 存在。

## 输入资源

1. `output/design/design.md`：唯一产品事实源，必须直接读取。
2. `$BUNDLE/templates/prototype.html`：HTML 壳层和产物骨架。
3. `$BUNDLE/references/prototype-writing.md`：通用后台基座、daisyUI、页面组织和视觉细则。多页面 shell、共享布局、导航激活、路由或空白页问题才读取 `$BUNDLE/references/prototype-shell.md`。
4. `$BUNDLE/lib/`：本地 Vue、Tailwind 和 daisyUI 运行资源。
5. `$BUNDLE/templates/prototype-feedback-classification.md`：有反馈时的归类格式。
6. 如存在 `output/prototype/prototype-feedback.md`，读取后先归类；如 PRD 存在，只能作为辅助参考，与 Design 冲突时以 Design 为准。
7. 不读取 `.workflow/metadata/design/` 或 `output/design/decision-notes.md` 作为产品事实输入。

## 执行流程

1. 检查 Design confirmation、HTML 模板、写法参考和本地 lib；缺失时报告具体路径并停止。
2. 读取 Design 的模块、页面、字段、状态、权限、流程、操作限制和异常要求。
3. 正式写入前完成 Design → Prototype 语义对照：列出必须表达的页面、字段、状态、角色权限、主要路径和关键反馈；显式标出 Design 的“待确认”项，不静默拍板。
4. 读取并执行 `$BUNDLE/references/prototype-writing.md` 的通用基座、daisyUI、页面组织和视觉规则；多页面或 shell 相关任务再读取 `$BUNDLE/references/prototype-shell.md`；以 `$BUNDLE/templates/prototype.html` 为基础生成或局部修改。确认版 Design 是唯一产品事实源，PRD 仅可选辅助，冲突时以 Design 为准。
5. 将 `$BUNDLE/lib/` 所需文件复制到 `output/prototype/lib/`，保证原型目录自包含、可直接打开；至少核对 `daisyui-themes.css`、`daisyui.css`、`tailwind.js`、`vue.global.prod.js`。
6. 生成后依次检查：浏览器是否正常渲染、Vue 控制台是否报错、页面和字段是否与 Design 一致、关键权限/状态/限制/主路径/异常反馈是否有表达。
7. 运行：

```text
python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root .
```

确定性检查或浏览器检查失败时先修复并重新验证，不交付未验证的原型。
8. 更新 `.workflow/status.json`：`current_stage=prototype`，`artifacts.prototype=output/prototype/index.html`；不使用 `current_stage=done` 表达线性完成。

完成判据：原型页面生成且可运行；Design 已确认；未引入 Design 未授权架构/技术；页面覆盖清单可核对；确定性检查与浏览器检查已通过。

## 产物

- `output/prototype/index.html`：主原型文件；页面多时可按业务模块拆分，但必须有可运行入口。
- `output/prototype/lib/`：自包含的本地 CSS/JS 运行资源。
- `output/prototype/prototype-feedback.md`：可选反馈记录。
- `.workflow/status.json`：导航状态和产物路径。

## 反馈处理

读取反馈后必须先按 `$BUNDLE/templates/prototype-feedback-classification.md` 输出归类，再开始修改。表现问题只改 Prototype；语义问题不得静默改动字段、状态、权限、流程或模块边界，必须停止并转入 Design/Fix；表现问题与语义问题不能混改。

- **表现问题**：布局、视觉层级、间距、颜色、字体、响应式或组件呈现问题；只改 Prototype，不改变 Design 事实。
- **语义问题**：缺少 Design 要求，或与 Design 的对象、字段、状态、权限、交互、异常和责任边界冲突；先回写 Design，使旧 confirmation 失效，用户重新确认后再按影响范围生成下游。
- 同时包含两类时拆成独立处理项；空类别保留并写“无”。

## 失败与停止

- 模板、写法参考、lib 或 Design 缺失：报告具体路径，不凭记忆生成完整产物。
- Design confirmation 失败：停止，不覆盖原型。
- 页面渲染空白、Vue 控制台报错、确定性检查失败：先修复并重新验证；必要时回滚到上一个可工作版本。
- 发现幻觉字段、页面、状态、权限或 Design 未授权高影响行为：删除或不写入，并报告；不静默拍板。
- 用户反馈无法归类：停止澄清，不直接修改。
- 不依赖 PRD 存在，不依赖 metadata，不使用外部 CDN、`el-` 组件或 Unix 专属命令描述来替代本地资源方案。
