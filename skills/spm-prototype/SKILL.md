---
name: spm-prototype
description: "原型阶段——把确认版 design.md 的页面行为表达成可看、可讨论的原型。ShitPM：直接读取确认版 Design，不依赖 PRD、Design metadata、page-fields、分页流水线或逐页字段计数。保留 HTML + Vue + Tailwind + daisyUI + 本地 lib 架构。反馈先归类再修改，表现问题只改 prototype，语义问题先回写 design。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 模型建议（运行时输出）

流程开始时输出模型等级和推理深度建议（直接复用 PRD §6.3 推荐矩阵）：

- **深度推理模型**：仍需进行信息架构、跨页面任务路径或复杂交互设计时
- **轻量或合适的代码模型**：上游行为明确、页面和路径简单，主要做既定表达与实现
- **无法判断时**：使用深度推理模型

建议必须是实际运行输出，不只是背景说明。

## ShitPM 职责定位

- **直接读取**确认版 `output/design/design.md`
- **不依赖** PRD、Design metadata、page-fields、分页流水线或逐页字段计数
- **保留** HTML + Vue + Tailwind + daisyUI + 本地 lib 架构
- **首次正式写入前**必须完成 Design 到 Prototype 的语义对照
- 关键角色权限、状态、操作限制、主要路径和关键反馈必须表达
- **不得引入** Design 未授权的高影响行为

## 前置检查

### 准入条件

1. `output/design/design.md` 存在
2. Design 确认标记有效：运行 `python $BUNDLE/scripts/python/artifact-guard.py --project-root . check-input --stage prototype`
   - 退出码 0 → 哈希一致，可继续
   - 非 0 → design.md 未确认或已修改。**拒绝继续**，提示用户重新确认

如 Design 未确认或哈希不一致，停下告知用户：
> Design 未确认或已修改。请由用户明确确认当前 Design 后再生成 Prototype。
> 确认方式：运行 `python $BUNDLE/scripts/python/design-confirmation.py --project-root . confirm`

**不要求**：
- PRD 存在
- Design metadata 存在
- page-fields.json 存在
- Prototype Review 通过

## 输入事实源

1. **必须读取**：`output/design/design.md`
2. **如存在反馈**，读取：`output/prototype/prototype-feedback.md`
3. **如 PRD 存在**，允许作为页面细节辅助参考，但**不得成为事实源或前置条件**；与 Design 冲突时以 Design 为准并报告
4. **不读取** `.workflow/metadata/design/` 下任何文件
5. **不读取** `output/design/decision-notes.md` 作为事实输入

## 资源检查

检查以下资源是否存在：

| 资源 | 路径 | 缺失时动作 |
|------|------|-----------|
| HTML 骨架 | `templates/prototype.html` | 停下告知用户，不凭记忆生成 |
| CSS/JS 库 | `lib/` 目录下 daisyui-themes.css、daisyui.css、tailwind.js、vue.global.prod.js | 停下告知用户，列出缺失文件 |
| 写法参考 | `references/prototype-writing.md` | 跳过参考，按硬规则生成 |

## 首次写入前的语义对照

正式写入原型前必须完成 Design → Prototype 的语义对照（输出对照结果，不要求思维过程）：

- 列出 design 中的模块、页面、字段、状态、权限清单
- 标记关键角色权限、状态、操作限制、主要路径、关键反馈
- 标记 Design 中"待确认"项，Prototype 不得静默拍板
- 已有 PRD 与 Design 冲突时，以 Design 为准并在反馈归类/修复摘要中报告

## 生成规则

### 通用后台基座

1. 原型默认使用 `templates/prototype.html` 里的通用后台基座，不为每个项目重新发明页框
2. 页框固定包含：顶栏、左侧导航、页签区、主体工作区
3. 顶栏、导航、页签只负责承载项目与页面切换，不承载具体业务规则
4. 业务差异主要落在主体工作区，不通过大改页框结构表达
5. 若用户已提供明确 UI 壳层稿，原型页框应优先贴近该稿复刻，不再继续抽象成另一套后台母版

### 组件使用规则

1. 通用组件用 **daisyUI 5**（CSS-only，无 JS 依赖）——组件类名参考 `references/prototype-writing.md` 第三章
2. **禁止任何 `el-` 前缀组件**——daisyUI 已全面替代 Element Plus
3. 表格用原生 `<table>` + Tailwind 样式（`table table-zebra`）
4. `select` 用原生 `<select class="select select-bordered">`
5. 如无明确视觉要求，不重写 daisyUI 基础交互语义，只做版式、间距、信息层级适配

### Dashboard / 监控面板布局规则

1. 使用 CSS Grid 或 Flexbox 布局卡片
2. 卡片内如有数据表格，超过 10 行必须分页（使用原生 `<table>` + 分页组件）
3. 同一页面内多个卡片应合理分配宽度，避免某个卡片过窄导致内容换行或截断
4. 卡片标题简洁，数据范围随筛选条件动态变化（如"南宁区域·3 个服务区"）
5. 监控类卡片优先展示关键指标（数值、趋势），次要信息折叠或分页

### 页面组织规则

1. 每个页面先复用统一页框，再按当前页面主任务组织主体内容；查询区、操作区、列表区、详情区、表单区都只是按需出现的内容块，不是固定全量标配
2. 主体区优先写清当前页面的主任务和主信息，不把顶栏、导航、页签重复写成业务内容
3. 同一项目内多个页面必须共用同一套顶栏、导航和页签语言，不得一页一个壳
4. 无特殊要求时，页面背景、卡片样式、页签样式、按钮层级遵循基座模板，不单页自行漂移
5. 页面名称默认放在主体区顶部的页签条中表达；页签支持关闭按钮，不再另起一块大页头重复写页面标题
6. 模板中的查询工具条、卡片容器、留白区域只用于示意内容层级，不代表所有页面都必须有查询条件或工具栏

### 关键语义表达要求（ShitPM 强化）

1. 关键角色权限必须表达：不同角色看到的页面/按钮/字段差异按 design 权限定义呈现
2. 状态必须表达：有状态机的实体，列表/详情/按钮可用性按 design 状态机呈现
3. 操作限制必须表达：design 中的业务规则和限制条件在原型交互中体现
4. 主要路径必须表达：design 中的核心业务流程在原型中可走通
5. 关键反馈必须表达：操作成功/失败/异常的反馈按 design 异常路径呈现
6. **不得引入** Design 未授权的高影响行为（新增字段、状态、权限、流程、模块边界）

## 生成后自检

每次生成或修改原型 HTML 后，必须执行以下自检：

| 序号 | 检查项 | 检查方式 | 不通过时动作 |
|------|--------|---------|------------|
| 1 | 页面能正常渲染 | 在浏览器中打开验证 | 立即回滚到修改前版本 |
| 2 | Vue 控制台无报错 | 检查控制台输出 | 排查变量丢失问题 |
| 3 | 字段与 design.md 一致 | 对照 design 字段定义表 | 删除幻觉字段，从 design.md 重新提取 |
| 4 | 关键语义已表达 | 对照 design 权限/状态/规则 | 补充缺失的语义表达 |

确定性检查命令：`python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root .`
通过后运行 `python $BUNDLE/scripts/python/artifact-guard.py --project-root . record --stage prototype` 登记来源哈希。来源记录写入 `.workflow/provenance/prototype.json`；Design 或 Prototype 后续变化时，运行 `artifact-guard.py check --stage prototype` 必须报告陈旧或一致性失败。

## 产物

生成以下文件：

| 序号 | 文件路径 | 说明 |
|------|---------|------|
| 1 | `output/prototype/index.html` | 主原型文件（或按页面拆分） |
| 2 | `output/prototype/lib/` | **必须自包含**——`output/prototype/` 目录下必须包含运行所需的所有 CSS/JS 资源（daisyui-themes.css、daisyui.css、tailwind.js、vue.global.prod.js），使原型目录可直接打开运行 |
| 3 | `output/prototype/prototype-feedback.md` | 可选，反馈模板 |

**lib/ 资源必须确保存在于 `output/prototype/lib/`**：从 `$BUNDLE/lib/` 复制所需 CSS/JS 文件到 `output/prototype/lib/`（如已有旧 lib/ 则先删除再复制）。复制操作跨平台兼容，最终结果须保证 `output/prototype/lib/` 下文件完整可用。

## 状态更新

更新 `.workflow/status.json`：

- `current_stage`：`"prototype"`
- `artifacts.prototype`：`"output/prototype/index.html"`
- `next_recommended`：可省略或设为 `null`

**不以 `current_stage=done` 表达线性完成状态**。原型阶段完成即 `current_stage=prototype`，是否同时有 PRD 不影响该字段。

## 处理反馈

读取 `prototype-feedback.md` 后，必须先输出固定格式归类结果，再开始修改：

```
原型反馈归类结果：

一、表现问题
- [页面/区域] 问题描述

二、语义问题
- [页面/区域] 问题描述

三、处理建议
- 仅改 prototype：
  - ...
- 先回写 design 再同步：
  - ...
```

归类规则：

- 表现问题：只修改 prototype，不回写 design
- 语义问题：先回写 design（使旧确认失效），再视影响范围重生 PRD 或 prototype；用户重新确认 Design 后才继续
- 若某一类为空，保留标题并写"无"

## 失败模式

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|---------|---------|-----------|
| HTML 骨架缺失 | `templates/prototype.html` 不存在 | 告知用户具体缺失路径 | 停下，不凭记忆生成 |
| lib/ 目录不完整 | CSS/JS 文件缺失 | 列出缺失文件清单 | 停下，要求用户补充资源到 `lib/` |
| design.md 不存在 | `output/design/design.md` 不存在 | 停下告知用户需要先完成设计阶段 | —— |
| Design 未确认 | design-confirmation.py check 返回非 0 退出码 | 停下告知用户先确认 Design | — |
| 页面渲染空白 | 生成的 HTML 在浏览器中不显示 | 检查 Vue 初始化代码和数据绑定 | 回滚到上一个可工作的版本 |
| Vue 控制台报错 | 运行时报错 | 根据错误信息定位变量丢失或组件注册问题 | 回滚并排查 |
| 字符串替换静默失败 | \n vs \r\n 差异导致替换不生效 | 改用 Python 脚本按行号操作 | 告知用户手动替换 |
| LLM 自检发现幻觉字段 | 生成时 AI 对照 design.md 发现字段不存在 | 删除幻觉字段，从 design.md 原文重新提取 | 标注幻觉项让用户确认 |
| 反馈归类不清 | 用户反馈同时涉及表现和语义 | 拆分为两个独立修复任务 | 追问用户确认优先级 |
| Design 待确认项被静默拍板 | 语义对照发现 Prototype 自行结论化 | 暴露到反馈归类，标"语义问题" | 停下让用户确认 |
| PRD 与 Design 冲突 | 已有 PRD 与 Design 表达不一致 | 以 Design 为准，在反馈归类/修复摘要中报告 | — |

## 不要做什么

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|--------|------------|---------|
| 1 | 重新定义业务规则 | 原型应忠实反映 design，不应自行发明规则 | 严格按 design.md 的字段定义和状态机生成 |
| 2 | 替代 PRD | 原型是可看可讨论的表达，不是完整需求规格 | 需求细节留给 PRD，原型只做视觉化表达 |
| 3 | 引入重构建链 | 原型应轻量快速，复杂构建链增加维护成本 | 使用单文件 HTML + 本地 lib/ |
| 4 | 语义问题只改 prototype | 语义问题源头在 design，只改原型会掩盖不一致 | 先回写 design，再同步 prototype |
| 5 | 跳过归类直接修改 | 可能把表现问题当语义问题改，或反之 | 先输出归类结果，等确认后再改 |
| 6 | 资源缺失时凭记忆生成 | 记忆可能过时或不准确，导致引用错误 | 停下告知用户，等资源就绪 |
| 7 | 使用任何 `el-` 前缀组件 | daisyUI 已全面替代 Element Plus | 参考 `references/prototype-writing.md` 第三章 daisyUI 类名 |
| 8 | 使用外部 CDN | file:// 协议下加载失败 | 使用本地 `output/prototype/lib/`，每次生成后确保资源完整 |
| 9 | 不验证直接交付 | 可能存在渲染空白、控制台报错等问题 | 每次修改后执行生成后自检 |
| 10 | 依赖 PRD 存在 | Prototype 不依赖 PRD | 直接读 Design；PRD 仅作辅助参考 |
| 11 | 依赖 Design metadata/page-fields | ShitPM 取消这些能力补偿机制 | 直接读 design.md 人读事实源 |
| 12 | 引入 Design 未授权的高影响行为 | 违反 Design 是唯一事实源 | 高影响意见先回写 Design |
| 13 | 使用 `cp -r` 等 Unix 专属命令 | 跨平台兼容性 | 描述目标结果（`output/prototype/lib/` 必须包含所需文件），由实际工具执行 |
| 14 | 不要求模型输出思维过程 | 只输出结论、产物、决策和待确认项 | — |
