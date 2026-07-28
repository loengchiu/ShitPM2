# 原型写法参考

> 本文件是原型阶段的示例和对照说明。
> 硬规则在 `skills/spm-prototype/SKILL.md`。




## 目录

- [常见错误](#常见错误)
- [一、原型定位](#一原型定位)
- [二、通用后台基座](#二通用后台基座)
- [三、daisyUI 组件使用约定](#三daisyui-组件使用约定)
- [四、页面落位方式](#四页面落位方式)
- [五、原型输入](#五原型输入)
- [六、反馈输入边界](#六反馈输入边界)
- [七、视觉细节规则（零成本打磨）](#七视觉细节规则零成本打磨)
  - [1. 文本换行](#1-文本换行)
  - [2. 同心圆角](#2-同心圆角)
  - [3. 数字对齐](#3-数字对齐)
  - [4. 字体平滑](#4-字体平滑)
  - [5. 阴影代边框](#5-阴影代边框)

## 常见错误

| 级别 | 场景 | 识别信号 | 为什么错 | 首选修复 | 仍失败处理 |
|---|---|---|---|---|---|
| 失败处理 | 原型只有一个 HTML 无法维护 | 页面过多全塞在一个文件 | 命中该场景说明当前产物未满足对应要求 | 按模块拆分 HTML 文件 | 若文件超过 5000 行，必须拆分 |
| 失败处理 | 原型重新定义业务规则 | HTML 中包含独立于 design 的业务规则 | 命中该场景说明当前产物未满足对应要求 | 检查原型中的业务规则是否与 design 一致 | 若不一致，回退到 fix 流程 |
| 失败处理 | 原型拆分不当 | 按技术层拆而不是按业务模块 | 命中该场景说明当前产物未满足对应要求 | 一个子系统一个 HTML 文件，index.html 做入口 | 若模块间有共享组件，提取到公共 JS |
| 失败处理 | 表现问题被当成语义问题 | UI 布局问题被误判为业务错误 | 命中该场景说明当前产物未满足对应要求 | 先归类：表现问题 vs 语义问题 | 表现问题只改 prototype，语义问题才回写 design |
| 失败处理 | 未归类就开始修改 | 读完 feedback 后直接改 | 命中该场景说明当前产物未满足对应要求 | 必须先输出归类结果，再开始修改 | 若无法归类，停在澄清，不直接改 |
| 失败处理 | 原型依赖 lib/ 缺失 | `lib/` 目录下 vue/tailwind/daisyui 缺失 | 命中该场景说明当前产物未满足对应要求 | 提示用户运行 `python scripts/python/download-prototype-libs.py` | 停下，不凭记忆生成 |
| 失败处理 | 状态表达不完整 | 只有默认状态，缺异常/空/加载状态 | 命中该场景说明当前产物未满足对应要求 | 按 design 状态定义逐个补入原型 | 若状态过多，先补核心状态，其余在 output/prototype/decision-notes.md 中记录待补，不在原型中残留 [TODO] |
| 失败处理 | 页面渲染空白 | createShellApp 选项合并错误 / lib 缺失 | 命中该场景说明当前产物未满足对应要求 | 1) 检查四件套[^四件套] lib 引用 2) 按 references 第七章模板重写 shell | 回滚到上一可工作版本 |
| 失败处理 | 页面无样式 | HTML 缺 Tailwind/daisyUI 引用 | 命中该场景说明当前产物未满足对应要求 | 给全部 HTML 补齐本地 lib/ 四件套[^四件套]引用 | —— |
| 反模式 | 把所有页面塞进一个 HTML | 出现该做法 | 无法维护，打开很慢 | 按模块拆分，用 index.html 做入口 | — |
| 反模式 | 原型独立定义业务规则 | 出现该做法 | 与 design 不一致，造成混乱 | 原型只做展示，业务规则以 design 为准 | — |
| 反模式 | 跳过归类直接修改 | 出现该做法 | 表现问题和语义问题的传播路径完全不同 | 必须先归类再修改 | — |
| 反模式 | 表现问题回写 design | 出现该做法 | 表现层反馈不应改变 design 业务定义 | 表现问题只改 prototype | — |
| 反模式 | 使用外部 CDN | 出现该做法 | file:// 协议下加载失败 | 使用本地 lib/ 目录四件套[^四件套] | — |
| 反模式 | 使用 Element Plus 组件（`el-xxx`） | 出现该做法 | 已废弃，改用 daisyUI | 用 daisyUI 组件类（`btn`/`table`/`card` 等） | — |
| 反模式 | 自造 createShellApp 框架 | 出现该做法 | 选项合并易出 bug（曾导致全部页面空白） | 复用 references 第七章模板 | — |
| 反模式 | 把页面 extraData 展开到 shell 的 data() | 出现该做法 | Vue 选项被当响应式数据，挂载报错 | 页面用独立组件 + `<component :is>` | — |

## 一、原型定位

- 原型与 PRD 平级，均以 design 为基线
- 原型只做展示，不重新定义业务规则
- 第一版走最小原型，不追求重型系统

## 二、通用后台基座

新的原型默认复用统一后台壳层，不再每个项目从空白 HTML 开始搭页框。

固定壳层包括：

1. **顶栏**
   - 高度固定
   - 承载项目名、当前模块名、全局操作入口、用户区
   - 不承载页面级业务规则
2. **左侧导航**
   - 用于模块和页面切换
   - 可分组
   - 当前项高亮
3. **页签区**
   - 位于主体区顶部白色条带内
   - 用于同模块下的子页面或同页多视图切换
   - 页签直接展示页面名称
   - 活动页签默认带关闭按钮
   - 只表达当前工作上下文
4. **主体工作区**
   - 承载查询区、操作区、表格区、表单区、详情区、统计卡片等真正业务内容
   - 上述内容块按页面主任务按需出现，不是每页都全量出现

版式方向：

- 顶栏白底
- 左侧导航白底
- 主体区浅灰背景
- 页签条白底，紧贴主体区顶部
- 主体内容使用白色卡片承载
- 层级靠间距、卡片、标题和按钮优先级表达，不靠花哨装饰

## 三、daisyUI 组件使用约定

通用组件默认使用 daisyUI 5（基于 Tailwind 的 CSS-only 组件库），不再使用 Element Plus。

daisyUI 5 是 CSS-only 库，无 JS 依赖。交互态（modal/dropdown 开关）通过 Vue 响应式变量或原生 `tabindex` + `:focus-within` 管理。

推荐映射（Element Plus → daisyUI）：

| 用途 | Element Plus（已废弃） | daisyUI 替代 |
|------|----------------------|-------------|
| 查询区 | `el-form` + `el-form-item` | `<form class="form-control">` + `<label class="label">` |
| 操作按钮 | `el-button` | `<button class="btn btn-primary">` |
| 下拉菜单 | `el-dropdown` | `<div class="dropdown">` + `tabindex` |
| 数据表格 | `el-table` | `<table class="table">`（原生 table + daisyUI 类） |
| 页签 | `el-tabs` | `<div role="tablist" class="tabs tabs-bordered">` |
| 统计卡片 | `el-card` + `el-statistic` | `<div class="card">` + `<div class="stat">` |
| 详情侧栏 | `el-drawer` | `<div class="drawer drawer-end">` + Vue 状态控制 |
| 确认弹窗 | `el-dialog` | `<dialog class="modal">` 或 `<div class="modal" :class="{'modal-open': visible}">` |
| 分页 | `el-pagination` | `<div class="join">` + 多个 `<button class="join-item btn">` |
| 状态标签 | `el-tag` | `<span class="badge badge-primary">` |
| 输入框 | `el-input` | `<input class="input input-bordered">` |
| 下拉选择 | `el-select` | `<select class="select select-bordered">` |
| 多选 | `el-checkbox` | `<input type="checkbox" class="checkbox">` |
| 单选 | `el-radio` | `<input type="radio" class="radio">` |
| 文本域 | `el-input type=textarea` | `<textarea class="textarea textarea-bordered">` |
| 警告提示 | `el-alert` | `<div role="alert" class="alert alert-warning">` |
| 折叠面板 | `el-collapse` | `<div class="collapse collapse-arrow">` |

约束：

1. 先用 daisyUI 现成组件类满足通用交互
2. 再通过 Tailwind utility class（`flex`/`gap-3`/`px-6`/`rounded-md` 等）做版式适配
3. 不要为了"更像设计稿"就把通用控件全部手写一遍
4. **禁止使用任何 `el-` 前缀的组件**——已废弃 Element Plus

## 四、页面落位方式

推荐顺序：

1. 先套统一页框
2. 再确定当前页面主任务
3. 再按需选择查询区 / 操作区 / 主表格 / 详情区 / 表单区等内容块
4. 最后补弹窗、抽屉、空状态、分页等辅助区域

坏例子：

- 每个页面重新发明一套导航
- 页签一页一套视觉语言
- 主体内容还没写清，先花大量时间做装饰

好例子：

- 页框统一
- 页签条直接承载“当前页面名 + 关闭按钮”
- 内容区差异清楚
- 有查询就放查询，没有查询就直接进入主内容，不为凑模板硬加一条工具栏
- 页面切换关系稳定

## 五、原型输入

确认版 Design 是 Prototype 的唯一产品事实源。PRD 仅可选用于发现表达差异或冲突，不是 Prototype 生成前置；冲突时以 Design 为准。


1. 必须读取 design.md
2. 如 prd.md 已存在，还需读取：详细需求说明（含字段定义表、状态机表、权限规则）
3. 如存在反馈，读取 `output/prototype/prototype-feedback.md`

## 六、反馈输入边界

反馈分类、停止条件和语义变更传播由 `skills/spm-prototype/SKILL.md` 与 `contracts/fix-propagation-rules.md` 负责；本文件只保留原型生成和表现层写法。






## 七、视觉细节规则（零成本打磨）

> 目标：用一行 CSS 或一个 Tailwind 类，把原型从"能用"提到"像样"。零构建成本，纯 CSS，不引入动画。
> 模板 `<style>` 已内置第 1/3/4 条；第 2 条通过 daisyUI 组件类间接落地（模板已定义 `--rounded-*` 变量）；第 5 条通过 Tailwind 类落地

### 1. 文本换行
- 标题用 `text-wrap: balance`（Tailwind: `text-balance`）
- 段落用 `text-wrap: pretty`（Tailwind: `text-pretty`）
- 避免标题孤字、段落末行单字

### 2. 同心圆角
- 嵌套元素内圆角 = 外圆角 − padding
- 例：外卡片 `rounded-lg`（0.5rem），内元素 `rounded-md`（0.375rem）
- 模板变量已内置层级：`--rounded-box` > `--rounded-btn` > `--rounded-selector`，生成时按此递减，不要反向

### 3. 数字对齐
- 表格、统计卡片、监控数值用 `font-variant-numeric: tabular-nums`（Tailwind: `tabular-nums`）
- 等宽数字，列对齐整齐，避免数字跳动

### 4. 字体平滑
- 已在模板 `<style>` 内置（`-webkit-font-smoothing: antialiased`）
- macOS 观感提升，生成时无需手动加

### 5. 阴影代边框
- 卡片优先用 `shadow-sm` 而非 `border`，层级感更柔
- 嵌套卡片用 `shadow-md` 区分层级
- 避免多层 `border` 堆叠造成"线条感"；确需边框时只用一层 `border border-slate-200`

[^四件套]: 指 `lib/` 目录下的 `vue.global.prod.js`、`tailwind.js`、`daisyui.css`、`daisyui-themes.css` 四个本地依赖文件，所有 HTML 通过相对路径引用。
