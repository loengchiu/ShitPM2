---
name: spm-prototype
description: "原型阶段——把 design 或 PRD 的页面行为表达成可看、可讨论的原型。用于用户说开始原型、做原型、生成原型时，或 stage-context 建议进入 prototype 阶段时。基于 design 基线生成 HTML 原型。反馈先归类再修改，表现问题只改 prototype，语义问题先回写 design。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下


## 输入依赖

1. 必须读取：`output/design/design.md`
2. 如已存在，还需读取：`output/prd/prd.md` 中的详细需求说明、状态机、权限汇总、数据字典
3. 如存在反馈，读取：`output/prototype/prototype-feedback.md`

## 最小读取集合

**一次读取**——用一次工具调用读取以下全部文件：

1. `.workflow/status.json`
2. `.workflow/metadata/design/page-fields.json`（页面→字段索引，仅用于定位，不作内容源）
3. `output/design/design.md`（逐页切片时读对应段落，不一次读全文）
4. `output/prd/prd.md`（如已存在，作为字段对齐第二事实源）
5. `templates/prototype.html`（HTML 骨架）
6. `references/prototype-writing.md`（写法参考）

>  fields.json/permissions.json/states.json 是 stage-prep 生成的机读镜像，供 review 与一致性检查使用，**AI 不读**。AI 只从 design.md 原文逐页照抄。

## 分页流水线生成策略

**禁止一口气生成全量原型**——design.md 可能 120KB+、50+ 页，上下文窗口后半段必然遗忘。与 spm-prd 共用同一份 `page-fields.json` 索引，逐页生成：

1. 先读 `page-fields.json` 获取全部页面→字段名列表（仅索引，无字段值）
2. 按 design.md 页面清单顺序，逐页处理：
   a. 从 design.md 原文中读取**当前页**的完整段落——字段列表、类型、枚举值、必填标记、权限规则、状态规则（按 page-fields.json 索引定位，每次只读 2-3KB）
   b. **照抄**：字段类型/枚举值/必填标记/权限/状态一律从 design.md 原文照抄，不改写不推断
   c.  PRD 已存在时，对照 PRD 同页的字段数量和名称为"第二事实源"——PRD 和原型必须字段对齐
   d. 生成该页 HTML 片段，生成立即自检：该页字段与 design.md 原文是否一致
3. 全部页面生成完后组装页框、导航
4.  全量自检：所有页面字段数量总和与 design.md 原文定义是否对齐
5. 运行 `verify-against-metadata.py`（结构完整性安全网——只校验 schema 和 ID 唯一性，不做语义对比。幻觉检测由 AI 在步骤 d 自检完成）

> **分页流水线核心：每页上下文 ~15KB，AI 只读 design.md 原文照抄。幻觉自检在生成阶段由 AI 对照 design.md 完成，verify 脚本只做结构兜底。**


## 执行顺序

### 步骤 1：资源检查

检查以下资源是否存在：

| 资源 | 路径 | 缺失时动作 |
|------|------|-----------|
| HTML 骨架 | `templates/prototype.html` |  停下告知用户，不凭记忆生成 |
| CSS/JS 库 | `lib/` 目录下 daisyui-themes.css、daisyui.css、tailwind.js、vue.global.prod.js |  停下告知用户，列出缺失文件 |
| 写法参考 | `references/prototype-writing.md` | 跳过参考，按硬规则生成 |

**CHECKPOINT · 资源可读性**——templates/prototype.html 和 lib/ 目录下的 CSS/JS 文件是否存在？缺失时停下告知用户具体缺失文件路径，不凭记忆生成原型。

### 步骤 2：分批生成（替换旧"读全文"模式）

**不再一次性读取 design.md 全文**。改用分页流水线：

1. 读 `page-fields.json` → 获取全部页面及对应字段名（仅索引）
2. 逐页处理（按 design.md 页面清单顺序）：
   - 从 design.md 原文定位当前页段落，只读 2-3KB
   -  所有字段类型/枚举值/必填/权限/状态一律从 design.md 原文照抄
   - 生成当前页 HTML 片段
   - 生成立即自检：字段与 design.md 原文一致
3. 全部页面生成完后组装页框、导航
4. 运行 `verify-against-metadata.py`（结构完整性安全网，只校验 schema + ID 唯一性）

**CHECKPOINT · 逐页生成**——每页生成后自检字段对齐，全量组装后验证总字段数 = design.md 定义。

### 步骤 3：生成原型

按 design 基线生成 HTML 原型，遵守以下规则：

**通用后台基座：**
1. 原型默认使用 `templates/prototype.html` 里的通用后台基座，不为每个项目重新发明页框
2. 页框固定包含：顶栏、左侧导航、页签区、主体工作区
3. 顶栏、导航、页签只负责承载项目与页面切换，不承载具体业务规则
4. 业务差异主要落在主体工作区，不通过大改页框结构表达
5. 若用户已提供明确 UI 壳层稿，原型页框应优先贴近该稿复刻，不再继续抽象成另一套后台母版

**组件使用规则：**
1. 通用组件用 **daisyUI 5**（CSS-only，无 JS 依赖）——组件类名参考 `references/prototype-writing.md` 第三章
2. **禁止任何 `el-` 前缀组件**——daisyUI 已全面替代 Element Plus
3. 表格用原生 `<table>` + Tailwind 样式（`table table-zebra`）
4. `select` 用原生 `<select class="select select-bordered">`
5. 如无明确视觉要求，不重写 daisyUI 基础交互语义，只做版式、间距、信息层级适配

**Dashboard / 监控面板布局规则：**
1. 使用 CSS Grid 或 Flexbox 布局卡片
2. 卡片内如有数据表格，超过 10 行必须分页（使用原生 `<table>` + 分页组件）
3. 同一页面内多个卡片应合理分配宽度，避免某个卡片过窄导致内容换行或截断
4. 卡片标题简洁，数据范围随筛选条件动态变化（如"南宁区域·3 个服务区"）
5. 监控类卡片优先展示关键指标（数值、趋势），次要信息折叠或分页

**页面组织规则：**
1. 每个页面先复用统一页框，再按当前页面主任务组织主体内容；查询区、操作区、列表区、详情区、表单区都只是按需出现的内容块，不是固定全量标配
2. 主体区优先写清当前页面的主任务和主信息，不把顶栏、导航、页签重复写成业务内容
3. 同一项目内多个页面必须共用同一套顶栏、导航和页签语言，不得一页一个壳
4. 无特殊要求时，页面背景、卡片样式、页签样式、按钮层级遵循基座模板，不单页自行漂移
5. 页面名称默认放在主体区顶部的页签条中表达；页签支持关闭按钮，不再另起一块大页头重复写页面标题
6. 模板中的查询工具条、卡片容器、留白区域只用于示意内容层级，不代表所有页面都必须有查询条件或工具栏

**资源自包含规则：**

**lib/ 必须随原型一起输出**——生成完所有 HTML 后，必须把 `lib/` 复制到 `output/prototype/lib/`：

```bash
cp -r lib/ output/prototype/lib/
```

这样 `output/prototype/` 目录自包含、可独立复制到任意路径打开使用。HTML 模板中已使用相对路径 `lib/xxx`，无需调整。

HTML 中的资源引用方式（模板已内置，无需修改）：
```
<link href="lib/daisyui-themes.css" rel="stylesheet" />
<link href="lib/daisyui.css" rel="stylesheet" />
<script src="lib/tailwind.js"></script>
<script src="lib/vue.global.prod.js"></script>
```

 不依赖外部 CDN（file:// 协议下外部资源可能加载失败）。

### 步骤 4：生成后自检

每次生成或修改原型 HTML 后，必须执行以下自检：

| 序号 | 检查项 | 检查方式 | 不通过时动作 |
|------|--------|---------|------------|
| 1 | 页面能正常渲染 | 在浏览器中打开验证 | 立即回滚到修改前版本 |
| 2 | Vue 控制台无报错 | 检查控制台输出 | 排查变量丢失问题 |
| 3 | 字符串替换格式正确 | 确认文件换行符格式（\n vs \r\n） | 用 Python 脚本按行号操作 |

**CHECKPOINT · 自检通过**——自检全部通过后，才进入步骤 5 输出产物。

### 步骤 5：输出产物

生成以下文件：

| 序号 | 文件路径 | 说明 |
|------|---------|------|
| 1 | `output/prototype/index.html` | 主原型文件（或按页面拆分） |
| 2 | `output/prototype/lib/` | **必须复制**——从 `lib/` 复制到 `output/prototype/lib/`，使原型目录自包含 |
| 3 | `.workflow/metadata/prototype/index.json` | 原型索引 |
| 4 | `output/prototype/prototype-feedback.md` | 可选，反馈模板 |

**lib/ 复制必须在生成 HTML 后立即执行**。用 `cp -r lib/ output/prototype/lib/`（如果已有旧 lib/ 则先删除再复制）。

生成后运行 `scripts/python/verify-against-metadata.py --stage prototype --project-root .` 校验结构完整性（schema + ID 唯一性，不校验幻觉）。

## 处理反馈

AI 读取 `prototype-feedback.md` 后，必须先输出固定格式归类结果，再开始修改：

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

**CHECKPOINT · 归类完成**——未输出归类结果前，不得开始修改任何文件。

归类规则：

- 表现问题：只修改 prototype + metadata/prototype，不回写 design
- 语义问题：先回写 design + metadata/design，再视影响范围重生 PRD 或 prototype
- 若某一类为空，保留标题并写"无"

## 失败模式

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|---------|---------|-----------|
| HTML 骨架缺失 | `templates/prototype.html` 不存在 | 告知用户具体缺失路径 | 停下，不凭记忆生成 |
| lib/ 目录不完整 | CSS/JS 文件缺失 | 列出缺失文件清单 | 停下，要求用户补充资源到 `lib/` |
| design.md 不存在 | `output/design/design.md` 不存在 | 检查是否有 PRD 可替代 | 停下告知用户需要先完成设计阶段 |
| 页面渲染空白 | 生成的 HTML 在浏览器中不显示 | 检查 Vue 初始化代码和数据绑定 | 回滚到上一个可工作的版本 |
| Vue 控制台报错 | 运行时报错 | 根据错误信息定位变量丢失或组件注册问题 | 回滚并排查 |
| 字符串替换静默失败 | \n vs \r\n 差异导致替换不生效 | 改用 Python 脚本按行号操作 | 告知用户手动替换 |
| LLM 自检发现幻觉字段 | 生成时 AI 对照 design.md 发现字段不存在 | 删除幻觉字段，从 design.md 原文重新提取 | 标注幻觉项让用户确认 |
| 反馈归类不清 | 用户反馈同时涉及表现和语义 | 拆分为两个独立修复任务 | 追问用户确认优先级 |

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
| 8 | 使用外部 CDN | file:// 协议下加载失败 | 使用本地 `output/prototype/lib/`，每次生成后复制 |
| 9 | 不验证直接交付 | 可能存在渲染空白、控制台报错等问题 | 每次修改后执行步骤 4 自检 |
