# ShitPM 原型组件行为规范（Tabler 标准 · Ant Design 6 落地）

> 用途：作为 `prototype-visual-spec.md` 的行为补充层，回答"每个组件怎么用、什么场景、什么边界"。视觉 Token、间距、字号、圆角、颜色、断点等数值仍以 `prototype-visual-spec.md` 与 `tablerTokens.ts` 为准；本文件只规定**组件的 DOM 结构、默认行为、场景边界、禁止事项与验收口径**，不重复定义数值。
> 事实来源：Tabler 官方预览站 `preview.tabler.io` + `@tabler/core@1.4` 编译 `tabler.min.css`（全量抽取稿：`docs/plans/2026-08-17-tabler-components-spec-draft.md`；交叉核对：`docs/reports/2026-08-17-tabler-official-design-language-research.md`）。涉及与 Tabler 官方默认值不一致的产品选择，标注 `[ShitPM 适配]`。
> 调用时机：生成或修改原型前与视觉规范一同读取；页面代码不得与本表冲突。

---

## 目录

- 0. 总则：行为层级三条
- 1. 页面标题（PageHeader）
- 2. 侧栏（Sider / Navbar Vertical）
- 3. 卡片（Card / SectionCard / MetricCard）
- 4. 表格与数据表（Table / DataTable）
- 5. 表单与输入（Form / FormSection / ActionBar）
- 6. 工具栏（Toolbar）
- 7. 状态、徽章与标签（StatusTag / Badge / Tag）
- 8. 弹窗（Modal）
- 9. 空态 / 加载 / 结果
- 10. 验收清单

---

## 0. 总则：行为层级三条

1. **先选语义再选样式**：组件行为由 Ant Design 6 提供（交互、可访问性、状态），视觉由 Tabler 语言覆盖；两者冲突时以本文件的行为规则为准，不改写 antd 行为。
2. **共享 UI 优先**：高频结构必须使用 `src/shared/ui/` 提供的组件（页头、卡片、指标卡、工具栏、表格、状态、空态、操作栏、行操作）；页面内不得复制整套局部 Tabler CSS。
3. **默认克制，特例授权**：本文件中的每条"默认"是生成器必须遵守的基线；确需例外时先在页面注释写明业务原因并同步到本文件，禁止无依据的自由发挥。

---

## 1. 页面标题（PageHeader）

### 标准结构（Tabler `.page-header`）

```
<div class="page-pretitle">模块前缀</div>   <!-- 12px / 500 / uppercase / 字距 0.04em -->
<h1 class="page-title">页面标题</h1>        <!-- 默认 20px / 600（h2 级） -->
<p class="page-subtitle">副标题或上下文</p>  <!-- 14px 次要色 -->
```

### 行为要求

- 一个页面只能有一个主标题。前缀用 `TablerPageHeader` 的 `prefix`，标题用 `title`，说明用 `subtitle`。
- **默认不设页面大标题**：普通列表 / 表单 / 看板页由壳层**页签栏**（当前路由 title + 关闭按钮）表达当前页面，页面内容首行只放操作区（`.page-actions` 右对齐）；`TablerPageHeader` 仅用于详情 / 结果 / 异常等特殊页。`[ShitPM 适配]`
- **标题字号默认 20px/600**（Tabler h2）；需要强调大标题时可用 24px（`.page-title-lg` 变体），但默认不得通页使用。`[ShitPM 适配]`：当前模板 `global.css` 的 `.page-title` 设为 24px，属"大标题变体"选择，已在视觉规范注明，不作为 Tabler 默认值对外宣传。
- 副标题最多 1 行说明（约 72ch），超出换行；不放与页面无关的装饰文字。
- 动作区：主按钮 1 个（primary），其余为次级/图标按钮；窄屏动作换行不拆字。

### 禁止

- 不用裸 `h1` 或任意 `div` 当页面标题；不把"页面标题"写在表格、卡片或面包屑里冒充主标题。
- 不用 `（只读）/（必填）/入口：` 等解释性标注代替真实 UI 状态。

---

## 2. 侧栏（Sider / Navbar Vertical）

### 标准结构（Tabler `.navbar-vertical`）

```
侧栏（240px 官方 / 200px ShitPM 适配，深色底，z-index 1030 级）
├─ Logo 标识区（固定，56px 高，下边框分隔）
└─ 菜单滚动区（overflow-y: auto，独立滚动）
   └─ 菜单项（active 项主色高亮）
```

### 行为要求

- 侧栏**自身不做整体滚动**；只有菜单区滚动，Logo 和底部固定。模板已用 `.sider-menu-scroll` 实现，页面不得改回"整个 Sider 滚动"。
- **LOGO 在顶栏，不在侧栏**：顶栏一行 = LOGO + 搜索框 + 用户区（对齐 Tabler 顶栏），侧栏只放菜单。`[ShitPM 适配]`
- **滚动条可见但弱化，不是隐藏**：Tabler 官方是极简细滚动条（thumb 圆角、透明轨道、hover 加深）。模板已实现 8px 细滚动条；禁止 `::-webkit-scrollbar{display:none}` 式的隐藏写法。`[ShitPM 适配]`：视觉规范将 Sider 宽定为 200px 属产品选择；Tabler 官方为 15rem=240px，如需对齐改 token `layout.siderWidth`，App.jsx 与 token 两处必须同步。
- 菜单项：嵌套/分组用 `Menu` 的原生分组，不用裸文本堆层级。

### 禁止

- 禁止隐藏滚动条；禁止 Sider 整体 `overflow: auto` 导致 Logo 跟着滚走。
- 深色侧栏上不用浅色 hover 底（保持暗色系 hover/选中态）。

---

## 3. 卡片（Card / SectionCard / MetricCard）

### 标准结构（Tabler `.card`）

```
<div class="card">                       ← 1px 边框、8px 圆角、极轻阴影
  <div class="card-header">
    <h3 class="card-title">标题</h3>      ← 16px / 600
    <div class="card-actions">…≤2 个图标操作…</div>
  </div>
  <div class="card-body">…内容…</div>
  <div class="card-footer">…页脚…</div>
</div>
```

### 行为要求

- 卡片间距：聚合页指标卡间距 16，区块（Section）之间 24；卡片内边距 24。`[ShitPM 适配]`：Tabler 官方卡片内边距为 16/20px 档，视觉规范统一为 24px 属产品选择。
- 卡头操作 ≤2 个图标按钮（`card-actions`），多余操作收进"更多"下拉。
- 卡片标题一律用 `h3` 层级（16px/600），不用正文改大字号冒充标题。
- 表格类卡片：header 可含描述行（`card-title mb-0` + 次要色描述）。

### 禁止

- 不用重阴影堆层级；不把卡片当普通 div 用（无边框、无内边距）。
- 不在卡片标题下堆多个无意义按钮；卡片互相贴紧（间距必须 ≥16）。

---

## 4. 表格与数据表（Table / DataTable）

### 标准结构（Tabler `.table-responsive > .table`）

```
<div class="card">
  <div class="table-responsive">           <!-- 整表横向滚动容器 -->
    <table class="table table-vcenter card-table">
      <thead><tr><th>名称</th><th class="text-end">数值</th><th class="w-1">操作</th></tr></thead>
      <tbody>…行…</tbody>
    </table>
  </div>
</div>
```

### 行为要求

- **默认不固定列**：列多时用 `.table-responsive` 整表横滚（`scroll={{ x: 'max-content' }}`），不默认写 `fixed`。
- **操作列 ≤3 个按钮，用文字按钮（不用图标按钮）**（窄列 `w-1`）：查看 / 编辑 / 删除等直接以文字显示在行内；超过 3 个的业务操作合并进"更多"下拉菜单。`[ShitPM 适配]`：文字按钮为产品业务习惯（图标歧义高），Tabler 官方示例用图标按钮，此处不一致属有意为之。
- 确需"固定列"时（业务上必须常驻可见的编号/操作列），用模板已固化的 `.tabler-table-panel` / `.tabler-data-table` 规则：fixed 列宽上限（如 160px）、实色背景、thead z-index 4 / tbody z-index 3、左右边界轻阴影。**CSS 实现位置**：`templates/prototype-vite/src/styles/global.css` 的 `.tabler-table-panel .ant-table-container { position: relative; isolation: isolate }` + fixed 单元格实底 + thead z-index 4 / tbody z-index 3 + 左右边界轻阴影。新原型由模板生成自动带；旧原型未带规则的需按此补齐。**因固定列且层级缺失导致的横向滚动重叠遮挡属于必须拦截的缺陷。**
- **表头文字层级（必看）**：横向滚动时**普通列表头的文字不得穿到 fixed 列表头区域**——"金额(元)"等普通表头文字在滚动中不能浮在"操作"等固定列表头之上造成两个表头叠在一起。固定列表头必须**实色背景**（`background: var(--spm-color-fill-alter) !important`） + **z-index 高于普通表头**（thead fixed z-index ≥ 4，普通表头 ≤ 3）。验收时**必须横向滚动到中段截图复核**，不能只看静态。
- 数字列右对齐 + `tabular-nums`（Tabler `text-end`）；表头不换行；空态用 `TablerEmptyState`；分页用 `pagination`。
- 状态列用 `TablerStatusTag`（`bg-*-lt` 浅底彩字），不用实心彩色徽章。

### 禁止

- 禁止为"好看"默认固定列；禁止操作列超过 3 个按钮并排平铺。
- 禁止固定列单元格透明背景（内容穿透露底）；禁止 fixed 单元格 z-index 低于滚动内容；**禁止普通表头文字穿透到 fixed 列表头区域**（表头文字层级缺失，常见于固定列表头未实底 + z-index 不够）。
- 表中不写裸文字状态（"状态：正常"这类解释性标注）。

---

## 5. 表单与输入（Form / FormSection / ActionBar）

### 标准结构（Tabler `form.space-y`）

```
<form class="space-y">
  <div class="mb-3">
    <label class="form-label">字段名</label>   <!-- 14px / 500 / 距输入框 8px -->
    <input class="form-control" />             <!-- 高 40、6px 圆角、浅边框 -->
  </div>
  <div class="form-footer">取消 | 提交(primary)</div>
</form>
```

### 行为要求

- 三列表单用 `Row gutter` + `Col span={8}`；多行长文本 `Input.TextArea autoSize`，长文本独占 `span={24}`。
- 控件聚焦：蓝色边框 + 3px 浅蓝光圈（antd / `global.css` 已提供）。
- 必填、只读、选填：`Form.Item required` / `disabled` / 不加标记，不用解释性文字。
- 页面级保存 / 提交 / 审批 / 返回统一放 `TablerActionBar`（sticky 底部），同一操作不重复出现。
- 校验错误内联提示，不靠弹窗；破坏性操作用 `Modal.confirm`。

### 禁止

- 不用原生 `alert/confirm/window.confirm` 代替 Modal；不用弹窗跳过 Form 校验。
- 不在页面内现场发明新的间距 / 字号 / 圆角值（先改 Token 或视觉规范）。

---

## 6. 工具栏（Toolbar）

### 标准结构（Tabler `.btn-list` + 筛选）

```
[查询 Form: 条件 + 查询 + 重置]   [工具栏: 新增(primary) + 刷新/导出…]
```

### 行为要求

- 查询、查询重置按钮属于查询 Form；新增、批量等业务操作属于工具栏。
- 每视图**只允许一个 primary 主按钮**，其余为次级 / 图标 / 文本按钮。
- 按钮组 `btn-list` gap 8px；窄屏换行堆叠不拆字。

### 禁止

- 禁止同时出现多个 primary；禁止把查询按钮当主操作。

---

## 7. 状态、徽章与标签（StatusTag / Badge / Tag）

### 标准（Tabler `badge bg-*-lt`）

- 成功 `success`（绿）/ 进行中 `progress`（蓝）/ 警告 `warning`（黄）/ 失败 `error`（红）/ 弱状态 `weak`（灰）五档，统一 `TablerStatusTag`。
- 徽章用浅底彩字（`bg-*-lt`），不用大面积实心色块；`badge-dot`（圆点）只在状态圆点场景使用。

### 禁止

- 禁止用裸文字表达状态；禁止同页出现多个不同语义色系的状态样式。
- 状态颜色只表达状态，不用于装饰。

---

## 8. 弹窗（Modal）

### 标准（Tabler `.modal`）

- **不用 Drawer，统一用 Modal 弹窗**（业务习惯：信息密度高、需对比上下文的场景也用 Modal，不用侧滑抽屉）。`[ShitPM 适配]`
- Modal 垂直内容用真实 `Modal + Form`；尺寸 `modal-sm/md/lg` 按内容；破坏性确认用 `Modal.confirm`。
- Modal 底部操作：取消（次级）+ 确定（primary），中文文案。

### 禁止

- 禁止拦截关闭、捕获点击导致的"关不掉"；不在弹层里再套弹层确认关键操作。

---

## 9. 空态 / 加载 / 结果

### 标准

- 列表 / 详情空数据：`TablerEmptyState`（图标 + 标题 + 指引 + 主操作）；表格内置空态兜底。
- 加载：表格 `loading`、卡片 `Skeleton` / `Spin`、按钮 `loading`；不空白闪烁。
- 结果 / 异常页：居中卡片 + `Result`（success / error / 404 / 403 / 500）+ 返回 / 重试操作。

### 禁止

- 禁止空态只留白板；禁止"加载中"用纯文字代替组件。

---

## 10. 验收清单（生成或修改后逐条核对）

- [ ] 页面主标题唯一，`prefix + title + subtitle` 三层齐全，标题字号默认 20px（或明确采用 24px 大标题变体）；普通列表/表单/看板页默认**不设大标题**，由壳层页签栏（含关闭按钮）表达当前页面
- [ ] 顶栏 = LOGO + 搜索 + 用户区同一行；Sider 独立滚动、细滚动条可见且弱化，无"整体滚动"或"隐藏滚动条"
- [ ] 表格默认不固定列；确需固定列时满足列宽上限 + 实底 + z-index 层级 + 边界阴影
- [ ] **表头文字层级（必复核）**：固定列时横向滚动到中段截图，普通列表头文字**不得穿到 fixed 列表头区域**（固定列表头实底 + thead z-index ≥ 4）
- [ ] 操作列 ≤3 个**文字按钮**（不用图标），多的进"更多"下拉；无超过 3 个按钮并排平铺
- [ ] 卡片间距 ≥16、区块间距 24、卡片标题 h3；卡头操作 ≤2 个
- [ ] 每视图一个 primary 主按钮；状态用 `TablerStatusTag` 五档浅底样式
- [ ] 数字列右对齐 + tabular-nums；表头不换行
- [ ] 空态 / 加载 / 结果 / 异常全部用组件表达，无裸文字状态
- [ ] 页面无现场拍值（颜色 / 间距 / 字号 / 圆角都来自 Token 或共享组件）
- [ ] 任何例外已在页面注释写明业务原因并记录到本文件
