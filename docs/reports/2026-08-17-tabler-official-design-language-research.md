# Tabler 官方设计语言研究报告（dashboard / page header / cards / tables / navbar / sidebar / scroll）

> 日期：2026-08-17
> 任务边界：独立、只读为主的官方资料研究；未修改任何业务原型源码（`output/`、Prototype 相关目录零改动），仅新增本报告一个文件。
> 研究方法：全部采用一手来源——Tabler 官方预览站（https://preview.tabler.io/）的页面与编译产物、Tabler 官方 GitHub 仓库（`tabler/tabler`，分支 `dev`，commit `2a0664098cba2c94ba7e5c7102f2a3666771af55`，2026-08-17）的 SCSS 源码与文档源文件。未使用任何二手转述。
> 版本指纹：preview.tabler.io 首页 HTML 头注释 `@version 1.4.0`；`core/package.json` 为 `@tabler/core 1.4.0`；preview 的 `tabler.min.css` cache-buster 为 `?1784061868`（约 2026-07-17 构建）。下文「源码值」以本次克隆的 `dev` 提交为准，「编译值」以 preview.tabler.io 的 `dist/css/tabler.min.css` 为准；两处有差异的会显式标注。

---

## 1. 结论速览

| 主题 | 核心可复用规则 | 关键证据选择器 / 值 | 来源 |
|---|---|---|---|
| Dashboard 骨架 | 页面 = `.page`（flex 列、min-height:100%）> `.navbar` + `.page-wrapper` > `.page-header` + `.page-body` > `.container-*` | `.page` `.page-wrapper` `.page-body` `.container-xl` | [layout/_page.scss], [page-layouts.mdx] |
| 页面内边距 | 左右 `--page-padding:1rem`（<lg 时 0.5rem），上下 `--page-padding-y:1.5rem`；内容容器最大宽 1320px | `--page-padding` `--page-padding-y` `container-max-widths(xxl)` | [layout/_root.scss], [_variables.scss] |
| Page header | 一行为 预标题(.page-pretitle 大写小字) + 标题(.page-title) + 右侧动作(.btn-list)，小屏动作收缩为图标按钮 | `.page-header` `.page-pretitle` `.page-title` | [layout/_page.scss], [page-headers.mdx] |
| 卡片 | `.card` 1px 边框 + 8px 圆角 + `--card-spacer-y/x` 内边距；`row-deck` 等高、`row-cards` 网格 gap=页面内边距 | `.card` `.row-deck` `.row-cards` | [bootstrap/_card.scss], [ui/_cards.scss], [ui/_grid.scss] |
| 表格 | `.table-responsive` 横向滚动；表头 th 不可换行 + 背景 `--bg-surface-tertiary`；`.table-vcenter/.table-nowrap/.table-mobile/.table-sort` | `.table` `.table-responsive` `.table-vcenter` | [ui/_tables.scss], [table.mdx] |
| Navbar | 高 3.5rem、底部 1px 边框、`navbar-expand-md` 响应式；active 由 2px 下边框表达 | `.navbar` `.navbar-expand-md` | [layout/_navbar.scss], [navbars.mdx] |
| Sidebar | 即 `.navbar-vertical`（垂直导航），宽 15rem、fixed、z-index 1030、自身 `overflow-y:scroll`；内容区用 `~ .page` padding 或 `~ .page-wrapper` margin 让位 | `.navbar-vertical` `$sidebar-width:15rem` | [layout/_navbar.scss], [page-layouts.mdx] |
| 滚动行为 | 全局 `scrollbar-gutter:stable` + 细滚动条混入；`.scrollable/.scroll-y/.scroll-x`；表头 sticky 用 `.sticky-top`(z 1020) | `scrollbar-gutter` `@include scrollbar()` `.scrollable` `.sticky-top` | [layout/_core.scss], [mixins/_mixins.scss], [utils/_scroll.scss], [table.mdx] |

---

## 2. 一手来源清单

| # | 来源 | 类型 | 取用内容 |
|---|---|---|---|
| S1 | https://preview.tabler.io/ | 官方预览站（Dashboard 页） | 页面骨架真实标记：`.page > header.navbar.navbar-expand-md > .page-wrapper > .page-header + .page-body`；`.card-table.table-responsive > table.table.table-vcenter`；`.row-cards` 网格；版本头注释 `@version 1.4.0` |
| S2 | https://preview.tabler.io/dist/css/tabler.min.css | 官方编译产物 | 成品 CSS 的选择器与最终值（变量编译为 `--tblr-*` 前缀） |
| S3 | https://github.com/tabler/tabler/tree/dev/core/scss/layout/_page.scss | 源码 | 页面骨架、page-header、page-pretitle/title/subtitle、page-tabs、page-body-card |
| S4 | https://github.com/tabler/tabler/tree/dev/core/scss/layout/_navbar.scss | 源码 | navbar、navbar-expand、navbar-vertical（sidebar）、submenu 缩进、active 指示 |
| S5 | https://github.com/tabler/tabler/tree/dev/core/scss/layout/_root.scss | 源码 | `--page-padding` / `--page-padding-y` 根变量 |
| S6 | https://github.com/tabler/tabler/tree/dev/core/scss/layout/_core.scss | 源码 | `html{scrollbar-gutter:stable}`、layout-fluid/boxed、body 设置 |
| S7 | https://github.com/tabler/tabler/tree/dev/core/scss/ui/_cards.scss | 源码 | 卡片变体：标题/子标题/header/footer/table/status/stamp 等 |
| S8 | https://github.com/tabler/tabler/tree/dev/core/scss/bootstrap/_card.scss | 源码 | `.card` 基线（CSS 变量、header/footer 内边距、圆角） |
| S9 | https://github.com/tabler/tabler/tree/dev/core/scss/ui/_tables.scss | 源码 | 表头、table-responsive、nowrap/vcenter/center/mobile/sort/selectable |
| S10 | https://github.com/tabler/tabler/tree/dev/core/scss/ui/_grid.scss | 源码 | row-deck（等高）、row-cards（网格 gap）、container-* 变体 |
| S11 | https://github.com/tabler/tabler/tree/dev/core/scss/utils/_scroll.scss | 源码 | `.scrollable/.scroll-x/.scroll-y/.no-scroll` |
| S12 | https://github.com/tabler/tabler/tree/dev/core/scss/mixins/_mixins.scss | 源码 | `@mixin scrollbar()`（细滚动条）、`@mixin subheader()`（预标题样式） |
| S13 | https://github.com/tabler/tabler/tree/dev/core/scss/_variables.scss 与 _settings.scss | 源码 | 全部令牌：spacer、断点、容器宽、卡片/表格/navbar 变量、z-index |
| S14 | https://github.com/tabler/tabler/tree/dev/docs/content/ui/layout/page-layouts.mdx | 官方文档源 | 横向 Navbar 骨架、Footer、Sidebar 布局（含完整页面骨架示例） |
| S15 | https://github.com/tabler/tabler/tree/dev/docs/content/ui/layout/page-headers.mdx | 官方文档源 | Page header 的 5 种官方用法（预标题/元信息/搜索/边框/面包屑） |
| S16 | https://github.com/tabler/tabler/tree/dev/docs/content/ui/layout/navbars.mdx | 官方文档源 | Navbar 官方用法与 `navbar-expand-md` 约定 |
| S17 | https://github.com/tabler/tabler/tree/dev/docs/content/ui/components/card.mdx | 官方文档源 | 卡片默认/内边距档位/标题/row-deck/状态条/stamp/tabs 用法 |
| S18 | https://github.com/tabler/tabler/tree/dev/docs/content/ui/components/table.mdx | 官方文档源 | 表格基础/响应式/nowrap/变体/「sticky header」官方用法 |

> 在线文档与仓库源文件同源：Tabler 文档站即由该 Astro 项目（`docs/`）构建。对应在线地址：https://tabler.io/docs/ui/layout/page-layouts、/page-headers、/navbars、/ui/components/cards、/ui/components/table。

---

## 3. Dashboard / 页面骨架

### 3.1 官方结构（页面如何组装）

官方「Sample layout」文档明确给出一页的标准容器结构（S14）：

```html
<div class="page">
  <header class="navbar navbar-expand-sm navbar-light d-print-none">
    <div class="container-xl"> … </div>
  </header>
  <div class="page-wrapper">
    <div class="page-body">
      <div class="container-xl">
        <div class="row row-deck row-cards"> <div class="col-4"><div class="card">…</div></div> … </div>
      </div>
    </div>
  </div>
</div>
```

preview.tabler.io Dashboard 页（S1）与之一致：`<div class="page">` → `<header class="navbar navbar-expand-md d-print-none">` → `<div class="page-wrapper">` → `.page-header`（含 `.page-pretitle`+`.page-title`）→ `.page-body`。

### 3.2 源码证据（S3）

| 选择器 | 关键规则 | 作用 |
|---|---|---|
| `.page` | `position:relative; display:flex; flex-direction:column; min-height:100%;` | 全页纵向弹性壳，保证高度撑满 |
| `.page-center` | `justify-content:center` | 居中布局（登录页等） |
| `.page-wrapper` | `display:flex; flex:1; flex-direction:column;`（打印时 `margin:0 !important`） | 导航与 footer 之间的内容包装 |
| `.page-body` | `display:flex; flex:1; flex-direction:column; margin-top/bottom: var(--page-padding-y)` | 内容主体，上下留白 = 1.5rem |
| `.page-body-card` | 背景 `--bg-surface`、顶部分隔线、`padding: var(--page-padding) 0` | 整页卡片背景变体 |
| `.page-cover` / `.page-cover-img` | 封面区，min-height 6rem→12rem(md)→15rem(lg)，背景图 blur 过滤 | 页首大图 |
| `.skip-link` | `position:fixed; z-index: $zindex-tooltip` | 无障碍跳过链接（层级最高之一） |

### 3.3 间距/宽度令牌（S5 + S13）

| 令牌 | 值 | 说明 |
|---|---|---|
| `$spacer-2` / `$spacer-3` / `$spacer-4` | `0.5rem` / `1rem` / `1.5rem` | Tabler 间距刻度（0.5/1/1.5rem 三档为主） |
| `--page-padding` | `var(--spacer-3)` = **1rem**；< lg 降为 `var(--spacer-2)` = **0.5rem** | 页面左右内边距基线 |
| `--page-padding-y` | `var(--spacer-4)` = **1.5rem** | 页面上下内边距基线 |
| `$container-padding-x` | `calc(var(--page-padding) * 2)` = 2rem | 容器内边距 |
| `$grid-gutter-width` | 变量表出现两处：`var(--page-padding)` 与 `1rem`；以编译产物为准 | 栅格 gutter |
| `$container-max-widths` | sm 540 / md 720 / lg 960 / xl 1140 / **xxl 1320px** | 容器档位，dashboard 常规用 `container-xl`=1140px |
| `$container-variations` | `slim:16rem` / `tight:32rem` / `narrow:61.875rem` | `.container-slim/tight/narrow` 窄容器（表单页、文档页） |
| 断点 | xs 0 / sm 576 / md 768 / lg 992 / xl 1200 / xxl 1400 | Bootstrap 断点（`_settings.scss`） |
| 字号 | base 0.875rem(14px)；h1 1.5rem；h2 1.25rem；h3 1rem；h4 0.875rem；h5 0.75rem | 层级明确（S13） |
| 字重 | 400/500(**medium**)/600(**semibold**)/700 | 只用 4 档（S13） |
| 圆角 | xs 2px / sm 4px / **base 6px** / lg 8px | 卡片用 lg，控件用 base（S13） |

### 3.4 可执行结论

1. 页面骨架固定为 `page > navbar + page-wrapper(page-header + page-body) + footer` 的纵深结构；外壳纵向 flex、`min-height:100%`。
2. 页面左/右内边距基线 1rem、上/下 1.5rem；窄屏（<992px）左右降为 0.5rem。内容主体 `margin: 1.5rem 0`。
3. 业务页面常规容器 `container-xl`（最大 1140px），整宽大屏可选 `container-xxl`（1320px）；表单/详情窄页用 `container-narrow` 或 `container-tight`。
4. 数据看板网格统一 `row row-deck row-cards`（等高 + 等 gap），gap = 页面内边距（1rem）。

---

## 4. Page header（页头）

### 4.1 官方用法（S15，5 种范式）

1. **Simple header**：`.page-header` 内一行栅格，左 = `.page-pretitle` + `.page-title`，右 = `.col-auto.ms-auto` 放 `.btn-list`；主按钮小屏 `d-sm-none` 换 `btn-icon`（文字在 <576px 隐藏，只留图标）。
2. **With meta, avatar and actions**：左侧加 `avatar`，标题下加 `.page-subtitle`（元信息行，图标+链接）。
3. **With meta, search and actions**：左侧标题 + 结果计数（`text-secondary`），右侧搜索框（`input-icon`）+ 主按钮；搜索域 <md 隐藏。
4. **Bordered header**：`.page-header.page-header-border`，容器用 `container-fluid`，底部分隔线。
5. **With breadcrumb and actions**：面包屑 + `.page-title`（长标题加 `text-truncate`）+ 右侧 `.btn-list`。

Dashboard 页（S1）实际标记即范式 1：`<div class="page-header d-print-none"> <div class="container-xl"> <div class="row g-2 align-items-center"> … </div>`。

### 4.2 源码证据（S3 + S12 + S13）

| 选择器 / 混入 | 关键规则 | 注释 |
|---|---|---|
| `.page-header` | `display:flex; flex-direction:column; flex-wrap:wrap; justify-content:center; max-width:100%; min-height:2.25rem;`；在 `.page-wrapper` 内时 `margin: var(--page-padding-y) 0 0` | 页头高基线 2.25rem，顶部 1.5rem 间距 |
| `.page-header-border` | `padding: var(--page-padding-y) 0; margin:0 !important; background: var(--bg-surface); border-bottom: 1px solid var(--border-color)` | 有边框页头：整体为背景块 + 底边线 |
| `.page-pretitle` | `@include subheader()` → `font-size:h5 0.75rem; font-weight:500; text-transform:uppercase; letter-spacing:0.04em; color:var(--secondary)` | 预标题 = 大写小字 |
| `.page-title` | flex 居中；`font-size:h2 1.25rem; font-weight:600(semibold); line-height:h2`；内联 svg `1.5rem × 1.5rem`、`margin-inline-end:0.25rem` | 页标题 = h2 级别、600 字重 |
| `.page-title-lg` | `font-size:h1 1.5rem` | 大标题变体 |
| `.page-subtitle` | `margin-top:0.25rem; color:var(--secondary)` | 副标题/元信息行 |
| `.page-tabs` | `margin-top:0.5rem` | 页头下贴标签页 |
| `.page-header-tabs` + `.page-body-card` | 常见组合，`+ .page-body-card { margin-top:0 }` | 页头标签 + 整页卡片 |

### 4.3 可执行结论

1. 页头固定一行三区：左标题区（pretitle + title + subtitle）、右动作区（`.btn-list`），用 `row g-2 align-items-center` 排列；右区用 `ms-auto` 靠右。
2. 标题阶梯固定：预标题 0.75rem/500/大写/字距0.04em/次要色；主标题 1.25rem/600；副标题 0.875rem 次要色、距标题 0.25rem。
3. 页头动作按钮数 ≤2，主按钮带图标；窄屏（<576px）动作收缩为 `btn-icon` 纯图标，必要时整组隐藏。
4. 需要分隔线时用 `.page-header-border`（背景块 + 底部 1px），否则页头随页面背景。
5. Navbar/页头默认 `d-print-none`（打印不输出），打印时整页卡片去边框去阴影。

---

## 5. Cards（卡片）

### 5.1 官方用法（S17）

- 默认：`.card` + `.card-body`；`.card-title`（放 body 内或 `.card-header` 内）；`.card-sm/md/lg` 调整内边距；`.row-deck` 等高卡片行；`.card-status-top/start` 状态条；`.card-stamp` 大水印图标；`.card-stacked` 叠层；`.card-tabs` 卡片标签页。

### 5.2 源码证据（S8 + S7 + S13）

基线与结构（S8，bootstrap/_card.scss）：

```css
.card {
  --card-spacer-y: 1.25rem;  --card-spacer-x: 1.25rem;        /* 正文内边距（源码 dev 值） */
  --card-cap-padding-y: 1.25rem; --card-cap-padding-x: 1.25rem; /* header/footer 内边距 */
  --card-border-width: var(--border-width);                    /* 1px */
  --card-border-color: var(--border-color-translucent);
  --card-border-radius: var(--border-radius-lg);               /* 8px */
  --card-bg: var(--bg-surface);
  --card-cap-bg: var(--bg-surface-tertiary);
  display: flex; flex-direction: column; min-width: 0;
  background-color: var(--card-bg);
  border: var(--card-border-width) solid var(--card-border-color);
  border-radius: var(--card-border-radius);
}
```

| 选择器 | 关键数值 | 注释 |
|---|---|---|
| `.card-body` | `padding: var(--card-spacer-y) var(--card-spacer-x)`（源码 1.25rem；preview 编译产物为 1rem/1.25rem，见 §11 差异说明） | 正文内边距 |
| `.card-header` / `.card-footer` | `padding: var(--card-cap-padding-y/x)`；header 底边框、footer 顶边框；first-child 顶部圆角 = inner radius | 分隔线由边框表达 |
| `.card-title` | `font-size:h3 1rem; font-weight:500; line-height:1.5rem; margin-bottom:1rem; color:var(--heading-color)`；放 header 内则 `margin:0` | 卡片标题 = h3/500 |
| `.card-subtitle` | `font-weight:400; color:var(--secondary); margin-bottom:1.25rem`（间距 = `$card-title-spacer-y`） | 卡片副标题 |
| `.card-body` 多段 | `& + & { border-top: 1px solid var(--border-color) }` | 连续 body 之间用线分隔 |
| `.card-sm/.card-md/.card-lg` | body 内边距档位：sm 1rem / md 2.5rem(≥768px) / lg 2rem(≥768px) 再 4rem(≥992px) | 内边距密度档 |
| `.card-body-scrollable` | `overflow:auto` | 卡片内滚动容器 |
| `.card-actions` | `--card-actions-gutter:0.5rem`；标题行右侧动作 | 标题行动作 |
| `.card-table` | 首/末列 `padding-inline: 1.25rem`（=`$card-spacer-x`）、首行列无左边框、四角圆角修正、底部行去边框 | 表格直接嵌入卡片 |
| `.card-active` | `--card-border-color: var(--primary); --card-bg: var(--active-bg)` | 选中态卡片 |
| `.card-status-top/start/bottom` | 绝对定位状态条 | 状态着色条 |
| `.card-stamp` / `-lg` | 尺寸 7rem / 13rem，旋转 10deg 的角标 | 装饰水印 |

栅格配合（S10）：

```css
.row-deck > .col, .row-deck > [class*='col-'] { display:flex; align-items:stretch; }
.row-deck .card { flex:1 1 auto; }              /* 等高卡片 */
.row-cards { --gutter-x: var(--page-padding); --gutter-y: var(--page-padding); } /* gap=1rem */
```

### 5.3 可执行结论

1. 卡片基线：白底（`--bg-surface`）、1px 半透明边框、8px 圆角、正文内边距 1.25rem、标题 h3(1rem)/500。
2. 卡片头部语义用 `.card-header`（底色微灰、底部 1px 线），不要在 body 里手工加分隔线。
3. 密度档位固定三档：sm=1rem（小组件/侧栏）、默认=1.25rem、lg=2rem→4rem（营销/大图文）；小屏自动收窄。
4. 看板一律 `row-deck row-cards` 保证同列等高；col 组合按 12 栅格（col-lg-3/col-lg-6/col-12 最常用，见 S14 示例）。
5. 表格进卡片用 `.card-table`（自动对齐卡片圆角与边距），不要手写负 margin。
6. 状态表达用 `.card-status-top/start`（色条），比整卡描边更贴近官方语言。

---

## 6. Tables（表格）

### 6.1 官方用法（S18）

- 基础：`<div class="table-responsive"><table class="table table-vcenter">…</table></div>`；`table-nowrap` 禁换行；`table-primary/danger/…` 行变体；**官方明确提供「sticky header」用法：`<thead class="sticky-top">`** 在长表滚动时保持表头可见。

### 6.2 源码证据（S9 + S13）

| 选择器 | 关键规则 | 注释 |
|---|---|---|
| `.table` | `font:inherit`；表头 `th { padding-top/bottom:0.5rem; white-space:nowrap; background:var(--bg-surface-tertiary); @include subheader() }` | 表头 = 大写小字 + 灰底 + 不换行 |
| 单元格 | `$table-cell-padding-x/y: 0.75rem`；th 横向同样 0.75rem、纵向 0.5rem | 行列内边距 |
| `.table-responsive` | `overflow-x:auto; -webkit-overflow-scrolling:touch;` 且内部 `.table{margin-bottom:0}` | 横向滚动（编译产物 S2 已确认） |
| `.table-responsive{-sm\|-md\|-lg\|-xl}` | 到断点为止横向滚动，断点以上恢复正常（官方文档原文） | 指定断点响应 |
| `.table-nowrap` | `> :not(caption) > * > * { white-space:nowrap }` | 全表禁换行 |
| `.table-vcenter` | 单元格 `vertical-align:middle` | 垂直居中 |
| `.table-center` | 单元格 `text-align:center` | 水平居中 |
| `.td-truncate` | `width:100%; max-width:1px` + 配合 `.text-truncate` | 单格截断（长文本列） |
| `.table-mobile` | <断点 时 `thead{display:none}`、行变纵向卡片，`td[data-label]::before` 输出标签 | 移动端纵向化（需在 td 写 `data-label`） |
| `.table-sort` | 按钮化 th；`:hover/.asc/.desc` 变深；`::after` 用 mask 渲染排序箭头（1rem，margin-start .25rem） | 排序表头 |
| `.table-selectable` | `tbody tr:has(.table-selectable-check:checked)` 高亮，`.on-checked/.on-unchecked` 切换 | 行选择 |
| `.sticky-top` | `position:sticky; top:0; z-index:1020`（编译产物 S2 确认） | 官方文档用它做 sticky 表头 |

### 6.3 可执行结论

1. 表格外一律套 `.table-responsive`（长表横向滚动、不压列宽）；短表可直接 `<table class="table table-responsive">`。
2. 表头规则固定：不换行、大写小字（0.75rem/500/uppercase）、灰底、单元格内边距 0.75rem、th 纵向 0.5rem。
3. 长表表头钉住用官方方案：`<thead class="sticky-top">`（position:sticky; top:0; z-index:1020）——无需自研 JS。
4. 常规列垂直居中 `.table-vcenter`；需要禁换行 `.table-nowrap`；单格长文本用 `.td-truncate + .text-truncate`。
5. 列表页移动端适配用 `.table-mobile`（th 隐藏、行变卡片、`data-label` 标注），比横向滚动更接近官方体验。
6. 行内操作（编辑/删除）应作为最右一列 `th class="w-1"` 窄列，文本用 `text-secondary` 弱化（S18 基础示例）。

---

## 7. Navbar（顶部导航）

### 7.1 官方用法（S16）

```html
<header class="navbar navbar-expand-md d-print-none">
  <div class="container-xl"> … </div>
</header>
```

- `navbar-expand-{bp}` 决定水平菜单在哪个断点以上展开（`navbar-expand-sm/md/lg/…`）；断点以下自动变纵向堆叠（源码 `navbar-vertical-nav` mixin，非只 Bootstrap 默认行为）。
- 内容约定：`navbar-brand`（logo，`navbar-brand-image`）、`navbar-nav > .nav-item > .nav-link`（图标 + 标题）、右侧 `navbar-nav flex-row order-md-last ms-auto`（用户/通知/操作）。

### 7.2 源码证据（S4 + S13）

| 选择器 / 变量 | 关键规则 |
|---|---|
| `$navbar-height` | **3.5rem**（顶部导航高基线） |
| `$navbar-padding-y` | 0.25rem |
| `.navbar` | `align-items:stretch; min-height:$navbar-height;` 背景 `var(--navbar-bg)=--bg-surface`；底部色调线用 `box-shadow: inset 0 -1px 0 0 var(--navbar-border-color)`（不用 border） |
| `.navbar .nav-link` | `justify-content:center; min-width:2.5rem; min-height:2.5rem; border-radius:6px`；badge 绝对定位右上角 |
| `.navbar-expand-*` 的 active | `.nav-item.active::after` 底部 **2px** 主色横条（`inset-inline-start/end:0; bottom:-0.25rem`） |
| `.navbar-vertical` 的 active | 左侧 **3px** 主色竖条（见 §8） |
| `.navbar-brand` | `gap:0.5rem; font-weight:600; line-height:1`；`$navbar-brand-image-height: 2rem` |
| `.navbar-toggler` | 宽高 = brand-image-height（2rem），icon = 三条线动效（展开变 45°） |
| `.navbar-transparent` | 透明背景 + 无边框 |
| `.navbar-overlap` | `::after` 向下延伸 9rem 同色块（`$navbar-overlap-height: 9rem`），用于 hero 叠加 |
| `$navbar-active-border-color` | `var(--primary)` |
| `$navbar-light-active-bg` | `rgba(0,0,0,0.2)` |

### 7.3 可执行结论

1. 顶部导航高度固定 3.5rem，白底 + 底部 1px 分隔线（实现用 inset shadow，等价 border-bottom 但随主题变量）。
2. 菜单项触达区最小 2.5×2.5rem，圆角 6px；当前项用底部 2px 主色条表达（宽度占满 item）。
3. 响应式断点按内容复杂度选 `navbar-expand-md`（默认）或 `navbar-expand-sm`；断点以下菜单纵向堆叠、下拉菜单展开为静态列表（官方已内置，无需自写折叠逻辑）。
4. Logo 高度 2rem；右侧操作区用 `navbar-nav flex-row order-md-last ms-auto`（移动端排到最右/顶行）。
5. 打印时导航整组隐藏（`d-print-none`）。

---

## 8. Sidebar（垂直侧栏 = `.navbar-vertical`）

> 术语：官方没有独立 `sidebar` 组件类名，侧栏就是「垂直模式的 navbar」，类名 `.navbar-vertical`（S4、S14 均如此）。若在旧文档看到独立 Sidebar 组件，那是 v1.2 前结构，**不要混用**。

### 8.1 官方用法（S14「Sidebar layout」）

```html
<div class="page">
  <aside class="navbar navbar-vertical navbar-expand-sm position-absolute" data-bs-theme="dark">
    <div class="container-fluid">
      <button class="navbar-toggler">…</button>
      <h1 class="navbar-brand navbar-brand-autodark">…</h1>
      <div class="collapse navbar-collapse" id="sidebar-menu">
        <ul class="navbar-nav pt-lg-3">
          <li class="nav-item"><a class="nav-link"><span class="nav-link-title">Home</span></a></li>
        </ul>
      </div>
    </div>
  </aside>
  <div class="page-wrapper">
    <div class="page-header d-print-none">…</div>
    <div class="page-body">…</div>
  </div>
</div>
```

### 8.2 源码证据（S4 + 编译产物 S2）

| 选择器 / 变量 | 关键规则 |
|---|---|
| `$sidebar-width` | **15rem（240px）** |
| `.navbar-vertical.navbar-expand-{bp}`（≥断点） | `position:fixed; left:0; top:0; bottom:0; z-index:1030; width:15rem; align-items:start; padding:0; overflow-y:scroll; transition: transform .3s` |
| `.navbar-vertical ~ .page` | `padding-inline-start:15rem`；且 `.page [class^=container]` 再补 `padding-inline 1.5rem`（内容不贴侧栏） |
| `.navbar-expand-{bp}.navbar-vertical ~ .page-wrapper` | `margin-inline-start:15rem`（结构未包 `.page` 时用 margin 方案；两种让位机制并存，见 §8.3） |
| `.navbar-vertical.navbar-right / .navbar-end` | 镜像到右侧（`left:auto; right:0`，page padding 换到右侧） |
| `.navbar-vertical .navbar-nav .nav-link` | `padding-top/bottom:0.5rem` |
| 子菜单缩进 | 一级子项 +1.75rem、二级 +3.25rem、三级 +4.75rem（相对菜单内边距 `container-padding-x/2 = 1rem`） |
| 移动端（`navbar-vertical-nav` mixin，<断点） | 折叠为纵向普通菜单：`.dropdown-menu{position:static;背景透明无边框无阴影}`、active 改为左侧 3px 主色竖条、`.dropdown-toggle::after{margin-left:auto}` |
| 品牌区 | `padding: ($navbar-height-$navbar-brand-image-height)*0.5 ≈ 0.75rem 0; justify-content:center` |

### 8.3 内容让位的两种机制（开发时二选一）

编译产物（S2）中同时存在：

```css
.navbar-expand-md.navbar-vertical ~ .navbar,
.navbar-expand-md.navbar-vertical ~ .page-wrapper { margin-inline-start: 15rem; }   /* 方案 A：page-wrapper 整体让位 */
.navbar-vertical.navbar-expand-md ~ .page { padding-inline-start: 15rem; }           /* 方案 B：.page 内边距让位 */
.navbar-vertical.navbar-expand-md ~ .page [class^='container'] { padding-inline:1.5rem; }
```

官方文档示例采用方案 A（`.page` 内含 `<aside>` + `.page-wrapper`）；preview 的「layout-vertical」类页面历史上用方案 B（侧栏与 `.page` 平级）。**落地时选定一种结构，不要混用，否则会出现 15rem 双倍偏移。**

### 8.4 可执行结论

1. 侧栏宽度唯一规格 15rem（240px），全高 fixed、自身纵向滚动（`overflow-y:scroll`），层级 z-index 1030。
2. 侧栏即垂直 navbar：断点以上固定、断点以下折叠成普通菜单，折叠逻辑（collapse + navbar-toggler）直接用官方 Bootstrap 组件，不另写。
3. 当前项指示 = 左侧 3px 主色竖条 + 深色底；子菜单缩进按 1.75/3.25/4.75rem 三档，深色主题（`data-bs-theme="dark"`）是官方示例默认。
4. 右侧布局用 `navbar-vertical navbar-right`（镜像），不要手写位移。
5. 侧栏偏移只实现一种机制（推荐 A：`.page-wrapper` margin），避免双倍偏移；内容是 `.page` 直子时改用 B，并在代码注释里声明。

---

## 9. Scroll behavior（滚动行为）

### 9.1 全局分栏稳定性（S6）

```css
html { scrollbar-gutter: stable; }          /* 无 scrollbar-gutter 支持时 overflow-y: scroll 兜底 */
```

- 目的：固定右侧滚动条槽位，避免进出长页时内容横向跳动。**这是官方默认行为**：Tabler 默认整页滚动，只有侧栏自身滚动。

### 9.2 细滚动条（S12，`@include scrollbar()`）

| 规则 | 值 |
|---|---|
| `scrollbar-color` | `color-mix(…, --scrollbar-color(默认 body-color), 0.2) transparent` |
| `::-webkit-scrollbar` | 宽/高 **1rem**，背景过渡 |
| thumb | 圆角 1rem，**5px 透明边框**（视觉细滚动条），box-shadow 内收 1rem、透明度 0.2 |
| hover | thumb 透明度 0.4 |
| track / corner | 透明 |

### 9.3 滚动容器工具（S11）

| 选择器 | 规则 | 用途 |
|---|---|---|
| `.scrollable` | `overflow-x:hidden; overflow-y:auto; -webkit-overflow-scrolling:touch` | 内容区自滚容器 |
| `.scrollable.hover` | 平时 `overflow-y:hidden`，hover/focus/active 才放开滚动 | 悬停滚动 |
| `.scroll-y` / `.scroll-x` | 单轴 auto/隐藏 | 单轴滚动 |
| `.no-scroll` | `overflow:hidden` | 禁滚 |
| `.card-body-scrollable` | `overflow:auto` | 卡片内滚动 |
| `.table-responsive` | `overflow-x:auto` | 表格横向滚动 |

### 9.4 Sticky / 固定层级（S13 + 编译确认）

| 选择器 | 值 | 用途 |
|---|---|---|
| `$zindex-sticky` / `.sticky-top` | **1020**；`position:sticky; top:0` | 表头钉住（官方文档用法）、工具条 |
| `$zindex-fixed` / `.navbar-vertical` | **1030**；`position:fixed` | 侧栏 |
| `$zindex-dropdown` | Bootstrap 默认（1000 档） | 下拉 |
| `$zindex-tooltip`（`.skip-link` 用） | 1080 档 | 顶层级 |

### 9.5 可执行结论

1. 页面滚动策略二选一并写进壳层约定：官方默认是**整页滚动 + `scrollbar-gutter:stable`**（或 overflow-y:scroll 兜底）；只有侧栏/表格/卡片内部用局部滚动容器。
2. 表格横滚用 `.table-responsive`（overflow-x:auto）；长表表头钉住用 `.sticky-top`（z-index 1020），无 JS。
3. 自定义滚动区统一 `.scrollable`；配合细滚动条样式（thumb 1rem 宽、5px 透明边框、圆心角），不做平台默认粗滚动条。
4. z-index 只使用 Sticky 1020 / Fixed 1030 / Tooltip 1080 三档，内部元素不得自行叠加任意大值。

---

## 10. 对 ShitPM Prototype / 壳层的可执行落地清单

以下为「最小采用集」，全部有上述源码证据；落地 Prototype 壳层时逐项勾选：

1. 页面容器：`page > navbar + page-wrapper(page-header + page-body > container-xl) + footer`；纵向 flex、min-height:100%。
2. 间距令牌：页面左右 1rem（<992px 0.5rem）、上下 1.5rem；摘要/详情页容器选 `container-xl`(1140px) 或 `container-narrow`(990px)。
3. 页头：pretitle(0.75/500/uppercase) + title(1.25rem/600) + 右侧动作区；窄屏动作收图标。
4. 卡片：1px 半透明边框、8px 圆角、body 内边距 1.25rem、标题 1rem/500；仪表盘网格 `row-deck row-cards`（gap 1rem）。
5. 表格：`.table-responsive` 包裹；表头灰底大写小字不换行、单元格 0.75rem；长表 `<thead class="sticky-top">`；行操作窄列 `w-1`。
6. 导航：顶栏 3.5rem + 底部 1px 线；侧栏 15rem、fixed、z 1030、自身滚动；当前项左侧 3px 主色条（侧栏）/底部 2px 主色条（顶栏）。
7. 滚动：html 加 `scrollbar-gutter:stable`；滚动容器用 `.scrollable`（overflow-x:hidden; overflow-y:auto）；细滚动条样式；z-index 只用 1020/1030/1080。
8. 打印：navbar、page-header 加 `d-print-none`；卡片打印去边框阴影。

## 11. 版本指纹与注意事项

- **变量命名**：源码 SCSS 变量不带前缀（`--page-padding`、`--card-border-radius`），编译产物统一转为 `--tblr-*`（如 `--tblr-page-padding`、`--tblr-card-border-radius`）。读取线上 CSS 查变量时按 `--tblr-` 前缀。
- **源码与 dist 的数值漂移**：`$card-spacer-y` 在本次克隆的 dev 源码为 `1.25rem`，而 preview.tabler.io 的编译产物（约 2026-07-17 构建）为 `--card-spacer-y:1rem`。二者属不同构建状态；落地前以你锁定的 Tabler 版本编译产物为准（本次所有「编译值」引用均带 S2 标注）。
- **断点**：576/768/992/1200/1400，非 Ant 的 576/768/992/1200/1600。适配 Prototype 壳层时注意断点定义差异。
- **类名冲突提醒**：`page`、`card`、`table` 都是通用词，在 ShitPM Prototype（Vite + React + Ant Design 6）中会与 Ant 命名空间共存；官方规则应只作为**视觉/间距/层级约定**转录为设计令牌与壳层 CSS 变量，不建议把 Bootstrap 依赖整体引入前端工程。
- **未覆盖项**（本报告范围之外，如需可另开研究）：按钮/表单/图标体系、暗色模式令牌（`--bg-surface-primary/secondary/tertiary` 已引用但未展开）、datagrid 与 pagination 组件。
- **研究纪律**：本报告只改动了 `docs/reports/` 下这一个文件；未触碰 `output/`、Prototype 源码及任何既有文件。

---

## 12. 来源（完整列表，按正文引用顺序）

- 预览站与产物：https://preview.tabler.io/ ；https://preview.tabler.io/dist/css/tabler.min.css
- 仓库（分支 `dev`，commit `2a0664098cba2c94ba7e5c7102f2a3666771af55`）：https://github.com/tabler/tabler
  - `core/scss/layout/_page.scss`、`_navbar.scss`、`_root.scss`、`_core.scss`
  - `core/scss/ui/_cards.scss`、`_tables.scss`、`_grid.scss`、`utils/_scroll.scss`
  - `core/scss/bootstrap/_card.scss`、`core/scss/mixins/_mixins.scss`
  - `core/scss/_variables.scss`、`core/scss/_settings.scss`
  - `docs/content/ui/layout/index.mdx`、`page-layouts.mdx`、`page-headers.mdx`、`navbars.mdx`
  - `docs/content/ui/components/card.mdx`、`table.mdx`
- 对应在线文档（与上述源文件同源）：https://tabler.io/docs/ui/layout/page-layouts 、/page-headers 、/navbars 、/ui/components/cards 、/ui/components/table

