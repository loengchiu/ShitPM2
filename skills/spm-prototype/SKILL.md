---
name: spm-prototype
description: "原型阶段——把 design 或 PRD 的页面行为表达成可看、可讨论的原型。用于用户说开始原型、做原型、生成原型时，基于 design 基线生成 HTML 原型。反馈先归类再修改，表现问题只改 prototype，语义问题先回写 design。"
triggers:
  - "开始原型"
  - "做原型"
  - "生成原型"
---
## 路径解析规则

🔴 **关键：ShitPM 安装在 bundle 目录，不在当前项目目录。**

执行本 skill 前，先从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段中读取 `ShitPM bundle root:` 的值，下文以 `$BUNDLE` 表示。

路径分类：
- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE` 下解析（绝对路径）
- `.workflow/`、`output/` 开头 → 当前项目根目录下解析（CWD 相对路径，不变）

示例：
```
# 脚本调用
python $BUNDLE/scripts/python/stage-context.py --stage design --project-root .

# 读取 bundle 资源
Read $BUNDLE/templates/design.md
Read $BUNDLE/references/design-writing.md

# 读取项目文件（CWD 相对，不变）
Read output/design/design.md
Read .workflow/status.json
```

> 下文所有以 `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头的路径一律在 `$BUNDLE` 下解析。

# 原型
## 触发条件

用户要求生成原型。

## 输入依赖

1. 必须读取：`output/design/design.md`
2. 如已存在，还需读取：`output/prd/prd.md` 中的详细需求说明、状态机、权限汇总、数据字典
3. 如存在反馈，读取：`output/prototype/prototype-feedback.md`

## 最小读取集合

🔴 **一次读取**——用一次工具调用读取以下全部文件：

1. `.workflow/status.json`
2. `output/design/design.md`
3. `templates/prototype.html`（HTML 骨架）
4. `references/prototype-writing.md`（写法参考）

> 页面落点和字段约束从 design.md 原文读取，不依赖 metadata JSON。

## 执行顺序

### 步骤 1：资源检查

检查以下资源是否存在：

| 资源 | 路径 | 缺失时动作 |
|------|------|-----------|
| HTML 骨架 | `templates/prototype.html` | 🔴 停下告知用户，不凭记忆生成 |
| CSS/JS 库 | `lib/` 目录下 daisyui-themes.css、daisyui.css、tailwind.js、vue.global.prod.js | 🔴 停下告知用户，列出缺失文件 |
| 写法参考 | `references/prototype-writing.md` | 跳过参考，按硬规则生成 |

🔴 **CHECKPOINT · 资源可读性**——templates/prototype.html 和 lib/ 目录下的 CSS/JS 文件是否存在？缺失时停下告知用户具体缺失文件路径，不凭记忆生成原型。

### 步骤 2：读取 design 基线

读取 `output/design/design.md`，提取：

1. 页面清单（全部页面名称和编号）
2. 字段定义（每个字段的类型、枚举值、约束）
3. 页面与字段落点（每个页面的区域/动作对应哪些字段）
4. 状态定义（状态集合和迁移）
5. 权限定义（角色和字段级权限）

### 步骤 3：生成原型

按 design 基线生成 HTML 原型，遵守以下规则：

**通用后台基座：**
1. 原型默认使用 `templates/prototype.html` 里的通用后台基座，不为每个项目重新发明页框
2. 页框固定包含：顶栏、左侧导航、页签区、主体工作区
3. 顶栏、导航、页签只负责承载项目与页面切换，不承载具体业务规则
4. 业务差异主要落在主体工作区，不通过大改页框结构表达
5. 若用户已提供明确 UI 壳层稿，原型页框应优先贴近该稿复刻，不再继续抽象成另一套后台母版

**组件使用规则：**
1. 通用组件默认使用 Element Plus（中文站：https://element-plus.org/zh-CN/）对应组件能力
2. **表格禁止使用 `el-table`**：el-table 在 Codex 内置浏览器中列全部竖向堆叠，经确认为渲染机制不兼容，无法通过 CSS 修复。所有数据表格必须使用**原生 HTML `<table>` + Vue 数据绑定**（详见 `references/prototype-writing.md`）
3. 可直接使用的常见组件包括：`el-form`、`el-card`、`el-tabs`、`el-button`、`el-tag`、`el-dialog`、`el-drawer`、`el-pagination`
4. `el-select` 在 Codex 浏览器中同样存在渲染问题，筛选控件使用原生 `<select>` 替代
5. 如无明确视觉要求，不重写 Element Plus 的基础交互语义，只做版式、间距、信息层级适配

**Dashboard / 监控面板布局规则：**
1. 使用 CSS Grid 或 Flexbox 布局卡片，不使用 el-row/el-col
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

🔴 **lib/ 必须随原型一起输出**——生成完所有 HTML 后，必须把 `lib/` 复制到 `output/prototype/lib/`：

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

🔴 不依赖外部 CDN（file:// 协议下外部资源可能加载失败）。

### 步骤 4：生成后自检

每次生成或修改原型 HTML 后，必须执行以下自检：

| 序号 | 检查项 | 检查方式 | 不通过时动作 |
|------|--------|---------|------------|
| 1 | 页面能正常渲染 | 在浏览器中打开验证 | 立即回滚到修改前版本 |
| 2 | Vue 控制台无报错 | 检查控制台输出 | 排查变量丢失问题 |
| 3 | 字符串替换格式正确 | 确认文件换行符格式（\n vs \r\n） | 用 Python 脚本按行号操作 |

🔴 **CHECKPOINT · 自检通过**——自检全部通过后，才进入步骤 5 输出产物。

### 步骤 5：输出产物

生成以下文件：

| 序号 | 文件路径 | 说明 |
|------|---------|------|
| 1 | `output/prototype/index.html` | 主原型文件（或按页面拆分） |
| 2 | `output/prototype/lib/` | 🔴 **必须复制**——从 `lib/` 复制到 `output/prototype/lib/`，使原型目录自包含 |
| 3 | `.workflow/metadata/prototype/index.json` | 原型索引 |
| 4 | `.workflow/metadata/prototype/page-map.json` | 页面映射 |
| 5 | `output/prototype/prototype-feedback.md` | 可选，反馈模板 |

🔴 **lib/ 复制必须在生成 HTML 后立即执行**。用 `cp -r lib/ output/prototype/lib/`（如果已有旧 lib/ 则先删除再复制）。

生成后运行 `scripts/python/verify-against-metadata.py --stage prototype --project-root .` 校验幻觉。

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

🔴 **CHECKPOINT · 归类完成**——未输出归类结果前，不得开始修改任何文件。

归类规则：

- 表现问题：只修改 prototype + metadata/prototype，不回写 design
- 语义问题：先回写 design + metadata/design，再视影响范围重生 PRD 或 prototype
- 若某一类为空，保留标题并写"无"

## 失败模式与 Fallback

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|---------|---------|-----------|
| HTML 骨架缺失 | `templates/prototype.html` 不存在 | 告知用户具体缺失路径 | 停下，不凭记忆生成 |
| lib/ 目录不完整 | CSS/JS 文件缺失 | 列出缺失文件清单 | 停下，要求用户补充资源到 `lib/` |
| design.md 不存在 | `output/design/design.md` 不存在 | 检查是否有 PRD 可替代 | 停下告知用户需要先完成设计阶段 |
| 页面渲染空白 | 生成的 HTML 在浏览器中不显示 | 检查 Vue 初始化代码和数据绑定 | 回滚到上一个可工作的版本 |
| Vue 控制台报错 | 运行时报错 | 根据错误信息定位变量丢失或组件注册问题 | 回滚并排查 |
| 字符串替换静默失败 | \n vs \r\n 差异导致替换不生效 | 改用 Python 脚本按行号操作 | 告知用户手动替换 |
| verify 脚本报幻觉 | `verify-against-metadata.py` 检测到 design 中不存在的字段 | 删除幻觉字段，从 design.md 重新提取 | 标注幻觉项让用户确认 |
| el-table 渲染异常 | 使用了 el-table 导致列堆叠 | 替换为原生 `<table>` + Vue 数据绑定 | —— |
| 反馈归类不清 | 用户反馈同时涉及表现和语义 | 拆分为两个独立修复任务 | 追问用户确认优先级 |

## Shell 环境规则

🔴 **硬性约束**——Codex 默认 shell 为 PowerShell，以下操作在 PowerShell 中会失败：

1. **不要用 Python -c 内联复杂脚本**——引号嵌套会被 PS 解析破坏。改为写入临时 .py 文件再执行
2. **不要用 heredoc（<< 'EOF'）**——PS 不支持 heredoc 语法
3. **不要用 Unix 命令**（head、cat、find -maxdepth、grep）——PS 没有这些命令
4. **不要用字符串替换修改 HTML**——\n vs \r\n 差异导致替换静默失败。改为用 Python 脚本按行号操作
5. **需要内联 Python 时**，用以下安全模式：
   ```python
   # 写入临时文件再执行，避免 PS 引号问题
   python -c "open('_tmp.py','w').write('print(1)'); exec(open('_tmp.py').read())"
   ```
   或直接用 Node.js（Codex 内置，无引号问题）。

## 不要做什么

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|--------|------------|---------|
| 1 | 重新定义业务规则 | 原型应忠实反映 design，不应自行发明规则 | 严格按 design.md 的字段定义和状态机生成 |
| 2 | 替代 PRD | 原型是可看可讨论的表达，不是完整需求规格 | 需求细节留给 PRD，原型只做视觉化表达 |
| 3 | 引入重构建链 | 原型应轻量快速，复杂构建链增加维护成本 | 使用单文件 HTML + 本地 lib/ |
| 4 | 语义问题只改 prototype | 语义问题源头在 design，只改原型会掩盖不一致 | 先回写 design，再同步 prototype |
| 5 | 跳过归类直接修改 | 可能把表现问题当语义问题改，或反之 | 先输出归类结果，等确认后再改 |
| 6 | 资源缺失时凭记忆生成 | 记忆可能过时或不准确，导致引用错误 | 停下告知用户，等资源就绪 |
| 7 | 使用 el-table | Codex 浏览器列全部竖向堆叠，无法修复 | 用原生 `<table>` + Vue 数据绑定 |
| 8 | 使用外部 CDN | file:// 协议下加载失败 | 使用本地 `output/prototype/lib/`，每次生成后复制 |
| 9 | 使用 el-row/el-col | Codex 浏览器中表现不稳定 | 用 CSS Grid 或 Flexbox |
| 10 | 不验证直接交付 | 可能存在渲染空白、控制台报错等问题 | 每次修改后执行步骤 4 自检 |
