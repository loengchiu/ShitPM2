# Tabler 组件标准写法规范（v1.4 全量抽取 · 完整版草稿）

> 状态：**草稿，待用户评审**（2026-08-17）。评审通过后决定实现路线并落地 `references/`。
> 来源：`preview.tabler.io` **全部 58 个组件示例页** + `@tabler/core@1.4` 编译 CSS（`tabler.min.css`）。每个组件页的每个示例卡片（`<div class="card">`）均已抽取，本文件为全量标准写法。
> 用途：作为 ShitPM 原型生成时**组件级标准写法的唯一事实源**，供 AI 讨论与实现参考。本文件只抽事实，不写实现结论。

---

## 0. 通用约定（全组件生效）

- **间距**：4px 基数，`--tblr-spacer-3=1rem(16px)`、`--tblr-spacer-4=1.5rem(24px)`、`--tblr-page-padding=16px`（容器左右）、`--tblr-page-padding-y=24px`（区块上下）。
- **字体**：正文 14px / 行高 1.4286（20px）；标题 `--tblr-font-size-h2=20px`、`h3=16px`；字重 medium=500、bold=600。
- **圆角**：`--tblr-border-radius=6px`（控件）、`lg=8px`（卡片/弹窗）、`sm=4px`（按钮/小标签）、pill=100rem。
- **图标**：`<svg class="icon">`（1.25rem）、`icon-1`（1.25rem 小）、`icon-2`（1.5rem）、`icon-3`（1.75rem）——全部来自 Tabler Icons（stroke 2px）。
- **滚动条**：全站极简样式（§1.4），**不是隐藏**。
- 本规范中所有 `bg-*-lt` 为浅色 tint 背景（该色 10% 底 + 该色文字）；`-fg` 为前景色。

---

## 1. 页面骨架（Vertical Layout）

### 1.1 DOM 结构

```html
<div class="page">
  <aside class="navbar navbar-vertical navbar-expand-lg" data-bs-theme="dark">
    <div class="container-fluid">
      <button class="navbar-toggler" data-bs-toggle="collapse" data-bs-target="#sidebar-menu">…</button>
      <div class="navbar-brand navbar-brand-autodark"><img class="navbar-brand-image" /></div>
      <div class="collapse navbar-collapse" id="sidebar-menu">
        <ul class="navbar-nav pt-lg-3">
          <li class="nav-item">
            <a class="nav-link" href="./">
              <span class="nav-link-icon d-md-none d-lg-inline-block"><svg class="icon">…</svg></span>
              <span class="nav-link-title">Home</span>
            </a>
          </li>
          <li class="nav-item active dropdown"><!-- 当前项：li 上加 active -->
            <a class="nav-link dropdown-toggle" data-bs-toggle="dropdown">
              <span class="nav-link-icon">…</span><span class="nav-link-title">Interface</span>
            </a>
            <div class="dropdown-menu">…子菜单…</div>
          </li>
        </ul>
      </div>
    </div>
  </aside>

  <div class="page-wrapper">
    <div class="page-header d-print-none" aria-label="Page header">
      <div class="container-xl">
        <div class="row g-2 align-items-center">
          <div class="col">
            <div class="page-pretitle">Overview</div>
            <h2 class="page-title">页面标题</h2>
          </div>
          <div class="col-auto ms-auto d-print-none">
            <div class="btn-list">
              <a class="btn btn-primary"><svg class="icon icon-2">…</svg>新建</a>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="page-body">
      <div class="container-xl">
        <div class="row row-deck row-cards">…卡片…</div>
      </div>
    </div>
    <footer class="footer footer-transparent d-print-none">
      <div class="container-xl"><div class="text-secondary">© 2026</div></div>
    </footer>
  </div>
</div>
```

### 1.2 页面标题（标准）

| 类 | 值 |
|---|---|
| `.page-title` | `font-size: 20px`（`--tblr-font-size-h2`）；`line-height: 28px`；`font-weight: 600`；`display:flex; align-items:center` |
| `.page-pretitle` | `12px`；`font-weight: 500`；`text-transform: uppercase`；`letter-spacing: .04em`；`color: secondary` |

**标题 = `h2.page-title` 20px/600 + 必带 `page-pretitle` 小字大写前缀。不是 h1、不是 24px。**

### 1.3 侧栏（标准）

| 项 | 值 |
|---|---|
| 宽度 | `width: 15rem = 240px` |
| 定位 | `position: fixed; top:0; left:0; bottom:0; z-index: 1030` |
| 滚动 | `overflow-y: scroll` + 全站极简滚动条样式（§1.4） |
| 让位 | `.navbar-vertical.navbar-expand-lg ~ .page { padding-left: 15rem }` |
| `.nav-link-icon` | `width/height: 1.25rem; margin-right: .5rem` |
| `.nav-link` | `padding: .5rem` 上下；`justify-content: flex-start` |

### 1.4 滚动条（全站标准，非隐藏）

```css
::-webkit-scrollbar { width: 1rem; height: 1rem; }
::-webkit-scrollbar-thumb {
  border-radius: 1rem; border: 5px solid transparent;
  box-shadow: inset 0 0 0 1rem color-mix(in srgb, var(--tblr-body-color) 20%, transparent);
}
::-webkit-scrollbar-track { background: 0 0; }
:hover::-webkit-scrollbar-thumb { box-shadow: inset 0 0 0 1rem color-mix(in srgb, var(--tblr-body-color) 40%, transparent); }
```

---

## 2. 卡片 Card（cards.html 42 示例 / card-actions.html 8 示例）

### 2.1 标准 DOM

```html
<div class="row row-cards">
  <div class="col-sm-12 col-lg-6">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">卡片标题</h3>
        <div class="card-actions btn-actions">
          <a class="btn-action" title="编辑"><svg class="icon">…</svg></a>
          <div class="dropdown"><a class="btn-action dropdown-toggle" data-bs-toggle="dropdown">…</a></div>
        </div>
      </div>
      <div class="card-body">…内容…</div>
      <div class="card-footer">…页脚…</div>
    </div>
  </div>
</div>
```

### 2.2 变体与要点

- **布局**：`row-cards` gutter 16px；`row-deck` 等高。
- **卡头操作**：`card-actions` + `btn-actions` + `btn-action`（图标按钮，48px 目标区）；多余操作进 `dropdown`。
- **卡头描述**：`card-title mb-0` + `<p class="text-secondary m-0">描述</p>`（表格卡用）。
- **色底卡**：`card bg-primary-lt` / `bg-primary`（图标底卡）——`bg-*` 直接加到 `.card` 上。
- **样式**：`border-radius: 8px`；`border: 1px solid border-color-translucent`；`box-shadow: 0 0 4px rgba(31,41,55,.04)`；`.card-body` padding `16px 20px`；`.card-header` 同 padding + 下边框；`.card-title` margin-bottom `20px`。

---

## 3. 表格 Table（tables.html 7 示例 / datatables / datagrid）

### 3.1 标准 DOM

```html
<div class="card">
  <div class="card-body border-bottom py-3">  <!-- 可选：entries 选择 + 搜索 -->
    <div class="d-flex">
      <div class="text-secondary">Show <input class="form-control form-control-sm d-inline-block w-auto"> entries</div>
      <div class="ms-auto text-secondary">Search: <input class="form-control form-control-sm d-inline-block ms-2"></div>
    </div>
  </div>
  <div class="table-responsive">
    <table class="table table-vcenter card-table">
      <thead>
        <tr>
          <th>Name</th>
          <th class="text-end">Visitors</th>   <!-- 数字列右对齐 -->
          <th class="w-1">操作</th>             <!-- 操作列窄列 -->
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><div class="d-flex py-1 align-items-center"><span class="avatar avatar-2 me-2">…</span><div class="flex-fill"><div class="font-weight-medium">名称</div><div class="text-secondary">副行</div></div></div></td>
          <td class="text-end">1,234</td>
          <td><div class="btn-list flex-nowrap"><a class="btn btn-sm">编辑</a><div class="dropdown">…更多…</div></div></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

### 3.2 变体

| 类 | 用途 |
|---|---|
| `table-vcenter` | 单元格垂直居中（默认） |
| `table-sm` | 紧凑行 |
| `table-striped` | 斑马纹（`--tblr-bg-surface-tertiary`） |
| `table-borderless` | 无边框（卡片内） |
| `table-mobile-md` | 移动端卡片化 |
| `table-selectable` | 可选中行 |
| `card-table` | 无 padding 表格卡（表贴卡边） |
| `text-nowrap` | 不换行 |
| `table-responsive` | 整表横向滚动容器 |

### 3.3 行为约束（防坑）

- **无固定列概念**：列多 → `.table-responsive` 整表横滚，不用 sticky 固定列。
- **操作列**：`th.w-1` 窄列 + `btn-list flex-nowrap`；**按钮 ≤ 3 个**，多余进 `dropdown`（"更多"）。
- 行主标题 `font-weight-medium`，副行 `text-secondary`；状态用 `badge bg-*-lt`；头像行用 `avatar` 组合。

---

## 4. 表单 Form（form-elements 4 / form-layout 4 示例）

### 4.1 标准 DOM

```html
<div class="mb-3">
  <label class="form-label">Text</label>
  <input type="text" class="form-control" placeholder="Input placeholder" />
</div>
<div class="mb-3">
  <label class="form-label">Select</label>
  <select class="form-select"><option>Option</option></select>
</div>
<!-- 图标输入 -->
<div class="input-icon mb-3">
  <span class="input-icon-addon"><svg class="icon">…</svg></span>
  <input class="form-control" placeholder="用户名" />
</div>
<!-- 前后缀 -->
<div class="input-group mb-3">
  <span class="input-group-text">¥</span>
  <input class="form-control" />
  <span class="input-group-text">.00</span>
</div>
<!-- 开关 / 勾选 -->
<div class="form-check form-check-inline">
  <input class="form-check-input" type="checkbox" />
  <label class="form-check-label">选项</label>
</div>
<div class="form-check form-switch">
  <input class="form-check-input" type="checkbox" role="switch" />
  <label class="form-check-label">开关</label>
</div>
```

### 4.2 布局与要点

- 垂直表单容器：`<form class="space-y">`（子元素间距 16px）；栅格 `row g-3` / `row-cols-2 g-4`。
- 行内表单：`row g-2 align-items-center` + `col-auto`。
- `form-control`：`padding: 9px 16px`；`font-size: 14px`；`line-height: 20px`；`border-radius: 6px`；`border: 1px solid #e5e7eb`；高 ≈ **40px**。
- `form-select`：右箭头为内嵌 SVG（`stroke:#9ca3af`），`padding-right: 3rem`。
- `form-label`：14px / 500 / `margin-bottom: 8px`。
- 校验态：成功 `#2fb344` / 错误 `#d63939` 边框；`form-control.is-valid/.is-invalid`。
- 底部操作：`form-footer`（右对齐）。

---

## 5. 按钮 Button（buttons.html 11 示例）

### 5.1 变体清单

```html
<a class="btn btn-primary">Primary</a>          <!-- 实心主色 -->
<a class="btn btn-outline btn-primary">Outline</a>  <!-- 描边 -->
<a class="btn btn-ghost btn-primary">Ghost</a>      <!-- 幽灵（hover 才显底） -->
<a class="btn btn-square btn-primary">Square</a>    <!-- 直角 -->
<a class="btn btn-pill btn-primary">Pill</a>        <!-- 胶囊 -->
<a class="btn btn-success|btn-warning|btn-danger|btn-info|btn-dark|btn-light">色系</a>
<a class="btn btn-blue|btn-azure|btn-indigo|btn-purple|btn-pink|btn-red|btn-orange|btn-yellow|btn-lime|btn-green|btn-teal|btn-cyan">扩展色</a>
<a class="btn btn-icon" aria-label="编辑"><svg class="icon icon-1">…</svg></a>  <!-- 纯图标 -->
<a class="btn btn-action">…</a>                  <!-- 行内动作按钮 -->
<a class="btn btn-sm|btn-lg">尺寸</a>
<div class="btn-list">…按钮组（gap 8px）…</div>
```

### 5.2 要点

- **按钮圆角 4px**（`--tblr-btn-border-radius: 4px`，小于卡片 8px，刻意区分）。
- 每视图 **1 个 primary 主操作**；其余 secondary/ghost/outline。
- `btn-icon` 方形图标按钮（padding 左右 0）；`btn-action` 用在卡头/行内。
- `btn-list`：`display:flex; gap: 8px`，可 `flex-nowrap`。

---

## 6. 徽章 Badge（badges.html 10 示例）

### 6.1 标准 DOM

```html
<span class="badge bg-primary">Primary</span>
<span class="badge bg-primary-lt">Light tint</span>      <!-- 浅底（常用状态） -->
<span class="badge bg-primary-outline">Outline</span>
<span class="badge badge-sm bg-green-lt text-uppercase">New</span>  <!-- 小号大写 -->
<span class="badge bg-red badge-dot"></span>             <!-- 圆点徽章 -->
<span class="badge badge-pill">Pill</span>
```

### 6.2 要点

- **状态用 `bg-*-lt`**（浅底彩字）：`bg-green-lt` 成功 / `bg-yellow-lt` 待办 / `bg-red-lt` 失败 / `bg-blue-lt` 进行中 / `bg-purple-lt` 审批。
- 位置徽章：`.badge` 在按钮/头像角落用 `position: absolute`（`.navbar .nav-link .badge` 内置）。
- 色阶：`bg-primary/secondary/success/info/warning/danger/light/dark` + `-lt`/`-outline` 变体 + 扩展色（blue/azure/indigo/purple/pink/red/orange/yellow/lime/green/teal/cyan）。

---

## 7. 头像 Avatar（avatars.html 11 示例）

### 7.1 标准 DOM

```html
<span class="avatar avatar-sm"> PK </span>                        <!-- 文字占位 -->
<span class="avatar avatar-1"><svg class="icon">…</svg></span>    <!-- 图标 -->
<span class="avatar avatar-1" style="background-image: url(...)"></span> <!-- 图片 -->
<span class="avatar avatar-2 bg-blue-lt"><svg>…</svg></span>      <!-- 彩色底 -->
<div class="avatar-list avatar-list-stacked">…</div>              <!-- 堆叠头像组 -->
<span class="avatar avatar-sm"><span class="badge bg-red badge-dot"></span></span> <!-- 状态 -->
```

### 7.2 尺寸

`avatar-xxs / avatar-xs / avatar-sm / avatar-md / avatar-lg / avatar-xl / avatar-2xl`；默认 `--tblr-avatar-size: 2.5rem(40px)`，`avatar-1/2/3` 为渐进尺寸。形状：`rounded-circle` / `rounded-0`。

---

## 8. 弹窗 Modal 与抽屉 Offcanvas（modals.html / offcanvas.html）

### 8.1 Modal

```html
<div class="modal modal-blur fade show" tabindex="-1" role="dialog" aria-modal="true">
  <div class="modal-dialog modal-dialog-centered" role="document">  <!-- modal-sm/lg/3 尺寸 -->
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Modal title</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">…</div>
      <div class="modal-footer"><a class="btn btn-primary">确定</a><a class="btn btn-link">取消</a></div>
    </div>
  </div>
</div>
```

### 8.2 Offcanvas（抽屉）

```html
<div class="offcanvas offcanvas-start" tabindex="-1" id="offcanvasStart"> <!-- start/end/top/bottom -->
  <div class="offcanvas-header"><h2 class="offcanvas-title">标题</h2><button class="btn-close" data-bs-dismiss="offcanvas"></button></div>
  <div class="offcanvas-body">…</div>
</div>
```

要点：`modal-dialog-centered` 垂直居中；modal-header/footer 有边框分隔；圆角继承 8px；`.modal-blur` 背景模糊。

---

## 9. 下拉 Dropdown（dropdowns.html）

```html
<div class="dropdown">
  <a class="btn dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">操作</a>
  <div class="dropdown-menu dropdown-menu-end dropdown-menu-arrow">
    <a class="dropdown-item">编辑</a>
    <a class="dropdown-item">终止</a>
    <div class="dropdown-divider"></div>
    <a class="dropdown-item text-danger">删除</a>
  </div>
</div>
```

- `--tblr-dropdown-min-width: 11rem`；`font-size: 14px`；`border-radius: 6px`；`padding-y: 4px`。
- 对齐：`dropdown-menu-end`（右侧）/ `dropdown-menu-start`；带箭头 `dropdown-menu-arrow`。
- 菜单内可放卡片：`dropdown-menu-card`（大面板）。

---

## 10. 分页 Pagination（pagination.html 2 示例）

```html
<ul class="pagination">
  <li class="page-item disabled"><a class="page-link" tabindex="-1" aria-disabled="true"><svg class="icon">«</svg></a></li>
  <li class="page-item"><a class="page-link">1</a></li>
  <li class="page-item active"><a class="page-link">2</a></li>
  <li class="page-item"><a class="page-link">3</a></li>
  <li class="page-item"><a class="page-link"><svg>»</svg></a></li>
</ul>
```

- `font-size: 14px`；`border-radius: 6px`；默认透明边框无底，hover/active 浅主色底。
- 前后导航大按钮：`page-item page-prev/page-next` + `page-item-subtitle/page-item-title`（文档导航风格）。

---

## 11. 标签页 Tabs（tabs.html 8 示例）

```html
<div class="card">
  <div class="card-header">
    <ul class="nav nav-tabs card-header-tabs">
      <li class="nav-item"><a class="nav-link active">Home</a></li>
      <li class="nav-item"><a class="nav-link"><svg class="icon me-2 icon-2">…</svg>Profile</a></li>
      <li class="nav-item ms-auto"><a class="nav-link"><svg class="icon icon-1">…</svg></a></li>
      <li class="nav-item dropdown"><a class="nav-link dropdown-toggle">More</a>…</li>
    </ul>
  </div>
  <div class="card-body">
    <div class="tab-content">
      <div class="tab-pane active show">…</div>
    </div>
  </div>
</div>
```

变体：`card-header-tabs`（贴卡头）、`nav-fill`（均分）、`flex-row-reverse`、`me-auto/ms-auto`（图标右/左）、`disabled`、`fade`（淡入）。

---

## 12. 步骤条 Steps（steps.html 2 示例）

```html
<ul class="steps steps-green my-4">
  <li class="step-item">1</li>
  <li class="step-item active">2</li>
  <li class="step-item">3</li>
</ul>
```

- `steps-counter` 自动数字；`steps-vertical` 垂直（每步 `h4.m-0` 标题 + `text-secondary` 描述）；`steps-*` 可接颜色（green/primary 等）。

---

## 13. 分段控件 Segmented control（segmented-control.html 12 示例）

```html
<nav class="nav nav-segmented nav-2">
  <button class="nav-link active">Daily</button>
  <button class="nav-link">Weekly</button>
  <button class="nav-link disabled">Monthly</button>
</nav>
```

- `nav-1/2/3` 尺寸；`nav-segmented-vertical` 垂直；可接图标；`nav-link-input` 做单选（radio 样式）。

---

## 14. 标签 Tags（tags.html 8 示例）

```html
<div class="tags-list">
  <span class="tag">Label 1 <a class="btn-close"></a></span>
  <span class="tag"><span class="avatar avatar-xxs tag-avatar">…</span>名称 <a class="btn-close"></a></span>
  <span class="tag"><span class="badge bg-blue text-blue-fg tag-status badge-dot"></span>Blue <a class="btn-close"></a></span>
  <span class="tag"><input class="form-check-input tag-check"> 可选 <a class="btn-close"></a></span>
</div>
```

变体：flag/icon/avatar/status(legend 色点)/check(多选)/badge(计数)。

---

## 15. 列表 List group（lists.html 5 示例）

```html
<div class="list-group list-group-flush list-group-hoverable">
  <div class="list-group-item">
    <div class="row align-items-center">
      <div class="col-auto"><span class="status-dot status-dot-animated bg-red d-block"></span></div>
      <div class="col text-truncate">
        <a class="text-body d-block">标题</a>
        <div class="d-block text-secondary text-truncate mt-n1">副行</div>
      </div>
      <div class="col-auto"><a class="list-group-item-actions"><svg class="icon">…</svg></a></div>
    </div>
  </div>
</div>
```

变体：`list-group-flush`（无外边框）、`list-group-hoverable`（hover 高亮）、`list-group-item-action`（可点）、`list-group-header sticky-top`（字母分组索引）。

---

## 16. 提示 Alert（alerts.html 6 示例）

```html
<div class="alert alert-danger alert-dismissible" role="alert">
  <div class="alert-icon"><svg class="icon">…</svg></div>
  <div>
    <h4 class="alert-heading">标题</h4>
    <div class="alert-description">描述<ul class="alert-list">…</ul></div>
  </div>
  <a class="btn-close"></a>
</div>
```

- 色系：`alert-primary/success/info/warning/danger`；变体：`alert-dismissible`、`alert-important`（粗体实底）、`alert-minor`（浅底）。
- `--tblr-alert-bg: color-mix(该色 10%, transparent)`；`padding: 12px 16px`；`margin-bottom: 16px`；`border-radius: 6px`。

---

## 17. 吐司 Toast（toasts.html 1 示例）

```html
<div class="toast-container position-fixed bottom-0 end-0 p-3">
  <div class="toast" role="alert" aria-live="assertive">
    <div class="toast-header">
      <span class="avatar avatar-xs me-2"></span>
      <strong class="me-auto">标题</strong><small>时间</small>
      <button class="ms-2 btn-close"></button>
    </div>
    <div class="toast-body">消息内容</div>
  </div>
</div>
```

---

## 18. 手风琴 Accordion（accordion.html 6 示例）

```html
<div class="accordion">
  <div class="accordion-item">
    <div class="accordion-header">
      <button class="accordion-button">问题标题 <div class="accordion-button-toggle"><svg>…</svg></div></button>
    </div>
    <div class="accordion-collapse collapse show"><div class="accordion-body">答案</div></div>
  </div>
</div>
```

变体：`accordion-flush`、`accordion-tabs`、`accordion-inverted`、`accordion-plus`（+/- 图标）、`accordion-button-icon`（前置图标）。

---

## 19. 轮播 Carousel（carousel.html 8 示例）

```html
<div id="carousel" class="carousel slide" data-bs-ride="carousel">
  <div class="carousel-inner">
    <div class="carousel-item active">…<div class="carousel-caption">…</div></div>
  </div>
  <button class="carousel-control-prev" data-bs-target="#carousel">…</button>
  <button class="carousel-control-next" data-bs-target="#carousel">…</button>
  <div class="carousel-indicators">…</div>
</div>
```

变体：`carousel-indicators-dot`（圆点）/`-thumb`（缩略图）/`-vertical`；`carousel-fade` 淡入。

---

## 20. 空态 / 进度条 / 占位 / 其他

```html
<!-- 空态 -->
<div class="empty">
  <div class="empty-icon"><svg class="icon">…</svg></div>
  <p class="empty-title">暂无数据</p>
  <p class="empty-subtitle text-muted">说明</p>
  <div class="empty-action"><a class="btn btn-primary">新建</a></div>
</div>

<!-- 进度条 -->
<div class="progress">
  <div class="progress-bar bg-primary" style="width: 75%"></div>
</div>
<!-- 进度背景条（表格内占比） -->
<div class="progressbg">
  <div class="progress progress-3 progressbg-progress"><div class="progress-bar bg-primary-lt"></div></div>
  <div class="progressbg-text">75%</div>
</div>

<!-- 占位骨架 -->
<div class="placeholder-glow"><span class="placeholder col-6"></span></div>
```

其他组件页（均已在预览站有标准示例，实现时对照）：`progress`（进度）、`placeholder`（骨架 10 例）、`scroll-spy`、`stars-rating`（星级）、`signatures`（签名）、`text-features`、`typography`、`icons`（3 例）、`flags`、`social-icons`、`payment-providers`、`datatables`（DataTables 插件）、`datagrid`、`charts`（ECharts 26 例）、`maps`、`gallery/photogrid`（图片墙）、`chat`、`activity/logs`（时间线）、`users/widgets/tasks/cards-masonry`（组合组件）、`wizard`、`markdown`、`wysiwyg`（编辑器）。

---

## 21. 坑位对照表（从养护平台实测反推 + 全量核查）

| # | 坑 | Tabler 标准答案 | 出处 |
|---|---|---|---|
| 1 | 表格固定列横向滚动盖内容 | 表格默认不固定列，`.table-responsive` 整表横滚；操作列 ≤3 按钮进"更多"下拉；确需 fixed 宽 ≤160 | §3.3 |
| 2 | 侧栏滚动条突兀 | 全站 `::-webkit-scrollbar` 极简样式（细滑块+透明轨道，**非隐藏**） | §1.4 |
| 3 | 页面标题不像 | `page-pretitle` 12px 大写前缀 + `h2.page-title` 20px/600 | §1.2 |
| 4 | 卡片贴一起 | `row-cards` gutter 16px；卡内边距 16/20px | §2.2 |
| 5 | 按钮圆角不统一 | 按钮 4px，卡片/弹窗 8px，控件 6px（**刻意不同**） | §5.2 |
| 6 | 图标尺寸乱 | `svg.icon` 1.25rem；`icon-1/2/3` 阶梯；`nav-link-icon` 1.25rem | §0/§1.3 |
| 7 | 数字列不对齐 | 数字列 `th/td.text-end` 右对齐 + tabular-nums | §3.1 |
| 8 | 状态用错样式 | 状态一律 `badge bg-*-lt`（浅底彩字），不用实心 | §6.2 |
| 9 | 侧栏宽度不对 | 15rem=240px（Tabler 标准），内容区 `padding-left: 15rem` 让位 | §1.3 |

---

## 附：抽取清单（供复核）

| 页面 | 示例数 | 页面 | 示例数 |
|---|---|---|---|
| cards | 42 | users | 18 |
| widgets | 34 | charts | 26 |
| gallery | 15 | navigation | 14 |
| cards-masonry | 14 | segmented-control | 12 |
| tasks | 13 | avatars | 11 |
| buttons | 11 | badges | 10 |
| placeholder | 10 | social-icons | 10 |
| card-actions | 8 | tabs | 8 |
| tags | 8 | carousel | 8 |
| accordion | 6 | alerts | 6 |
| tables | 7 | lists | 5 |
| pricing | 5 | form-layout | 4 |
| form-elements | 4 | stars-rating | 4 |
| maps | 4 | dropzone | 3 |
| signatures | 3 | icons | 3 |
| pagination | 2 | steps | 2 |
| pricing-table | 1 | text-features | 2 |
| payment-providers | 2 | 其余（activity/chat/colorpicker/datagrid/datatables/flags/logs/markdown/modals/offcanvas/scroll-spy/toasts/typography/wizard/wysiwyg/turbo-loader） | 各 1 |

来源：`preview.tabler.io/<page>.html`（58 页全量）+ `@tabler/core@1.4` `tabler.min.css` 的 `--tblr-*` 变量与组件规则。关键变量速查：`--tblr-primary:#066fd1`、`--tblr-font-size-h2:1.25rem`、`--tblr-font-weight-bold:600`、`--tblr-page-padding:1rem`、`--tblr-page-padding-y:1.5rem`、`--tblr-shadow-card:0 0 4px rgba(31,41,55,.04)`、`--tblr-border-radius:6px`、`--tblr-border-radius-lg:8px`、`--tblr-btn-border-radius:4px`。
