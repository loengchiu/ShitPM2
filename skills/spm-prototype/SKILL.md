---
name: spm-prototype
description: "原型阶段——把 design 或 PRD 的页面行为表达成可看、可讨论的原型。用于用户说开始原型、做原型、生成原型时，基于 design 基线生成 HTML 原型。反馈先归类再修改，表现问题只改 prototype，语义问题先回写 design。"
triggers:
  - "开始原型"
  - "做原型"
  - "生成原型"
---

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
3. `.workflow/metadata/design/page-fields.json`（页面→字段落点）+ `field-constraints.json`（字段约束）
4. `templates/prototype.html`（HTML 骨架）
5. `references/prototype-writing.md`（写法参考）

🔴 **检查点：资源可读性**——templates/prototype.html 和 lib/ 目录下的 CSS/JS 文件是否存在？缺失时停下告知用户，不凭记忆生成原型。

## 输出要求

1. `output/prototype/index.html` 或按页面拆分的原型文件
2. `.workflow/metadata/prototype/index.json`
3. `.workflow/metadata/prototype/page-map.json`
4. 可选 `output/prototype/prototype-feedback.md`

## 硬规则

### 通用后台基座

1. 原型默认使用 `templates/prototype.html` 里的通用后台基座，不为每个项目重新发明页框
2. 页框固定包含：顶栏、左侧导航、页签区、主体工作区
3. 顶栏、导航、页签只负责承载项目与页面切换，不承载具体业务规则
4. 业务差异主要落在主体工作区，不通过大改页框结构表达
5. 若用户已提供明确 UI 壳层稿，原型页框应优先贴近该稿复刻，不再继续抽象成另一套后台母版

### 组件使用规则

1. 通用组件默认使用 Element Plus（中文站：https://element-plus.org/zh-CN/）对应组件能力
2. **表格禁止使用 `el-table`**：el-table 在 Codex 内置浏览器中列全部竖向堆叠，经确认为渲染机制不兼容，无法通过 CSS 修复。所有数据表格必须使用**原生 HTML `<table>` + Vue 数据绑定**（详见 `references/prototype-writing.md`）
3. 可直接使用的常见组件包括：`el-form`、`el-card`、`el-tabs`、`el-button`、`el-tag`、`el-dialog`、`el-drawer`、`el-pagination`
4. `el-select` 在 Codex 浏览器中同样存在渲染问题，筛选控件使用原生 `<select>` 替代
5. 如无明确视觉要求，不重写 Element Plus 的基础交互语义，只做版式、间距、信息层级适配

### Dashboard / 监控面板布局规则

当页面为仪表盘、监控面板、数据看板类型时：

1. 使用 CSS Grid 或 Flexbox 布局卡片，不使用 el-row/el-col
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

### CDN 与资源引用

1. 原型使用本地 `lib/` 目录下的 CSS/JS 文件，不依赖外部 CDN（file:// 协议下外部资源可能加载失败）
2. 需要预先下载的文件：`element-plus.css`、`vue.global.prod.js`、`element-plus.js`、`element-plus-icons.js`、`echarts.js`
3. HTML 中引用方式：`<link rel="stylesheet" href="lib/element-plus.css">`

### prototype-feedback 归类规则

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

🔴 **检查点：归类完成**——未输出归类结果前，不得开始修改任何文件。

归类规则：

- 表现问题：只修改 prototype + metadata/prototype，不回写 design
- 语义问题：先回写 design + metadata/design，再视影响范围重生 PRD 或 prototype
- 若某一类为空，保留标题并写"无"
- 未输出归类结果前，不得开始修改任何文件

## 不要做什么

1. 不重新定义业务规则
2. 不替代 PRD
3. 不引入很重的构建链
4. 不把语义问题只留在 prototype 闭环
5. 不跳过归类直接修改
6. 不在 templates/prototype.html 或 lib/ 缺失时凭记忆生成原型
7. 不使用 el-table（Codex 浏览器不兼容）
8. 不使用外部 CDN（file:// 协议下加载失败）
9. 不使用 el-row/el-col 做布局（在 Codex 浏览器中表现不稳定）

🔴 **编辑后自检**——每次修改原型 HTML 后，必须：
   a. 在浏览器中打开验证页面能正常渲染
   b. 检查 Vue 控制台是否有报错
   c. 如页面空白或报错，立即回滚到修改前的版本，排查变量丢失问题
   d. 字符串替换前先确认文件中的换行符格式（\n vs \r\n），避免替换失败
