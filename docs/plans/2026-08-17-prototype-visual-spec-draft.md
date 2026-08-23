# ShitPM 原型视觉规范（Ant Design 6 基线）

> 用途：生成 / 修改 Vite + React 18 + Ant Design 6 原型时，作为视觉与布局的**唯一事实源**。
> 调用时机：每次生成或评审原型页面前读取本文件；本文件之外的视觉数值一律以本文件为准。
> 来源：Ant Design 官方视觉规范（colors / layout / font / proximity / alignment / contrast / repetition / motion）与 antd v6 全局 Token。取值已按 `templates/prototype-vite/package.json`（antd ^6.6.0）核对。
> 状态：**已采纳**——正式版见 `references/prototype-visual-spec.md`（ShitPM 运行时视觉事实源，2026-08-17 评审通过，字体家族采用思源黑体）。本草稿保留作评审溯源。

---

## 0. 执行流程（每轮生成原型走这套）

1. 确定页面类型（聚合 / 表单 / 列表 / 详情 / 看板）→ 取用第 2 节的对应骨架。
2. 套用第 1 节 Token 常量，不现场发明色值 / 间距 / 字号。
3. 状态与空态按第 3 节用语义组件表达。
4. 生成后逐条过第 4 节自检清单，未过则改到过为止。

完成判据：自检清单全部勾选，且页面在 1440 宽度下无横向溢出、无贴边、无裸文字状态。

---

## 1. 设计 Token（唯一事实源）

> 所有视觉数值从这里取。需要新值先在组内找最接近的 8 的倍数，不要随手写 10/18/22 这类非标数。

### 1.1 色彩

| 角色 | Token | 值 | 用途 |
|---|---|---|---|
| 主色 | `colorPrimary` | `#1677ff` | 主行动按钮、当前导航、链接、重要信息高亮 |
| 成功 | `colorSuccess` | `#52c41a` | 成功 / 已完成 / 已验证 |
| 警告 | `colorWarning` | `#faad14` | 待处理 / 接近阈值 / 需关注 |
| 错误 | `colorError` | `#ff4d4f` | 失败 / 校验不通过 / 破坏性操作 |
| 进行中 | `colorInfo` | `#1677ff` | 进行中 / 提示（复用主色） |
| 文字一级 | `colorText` | `rgba(0,0,0,0.88)` | 标题、正文、主要数据 |
| 文字二级 | `colorTextSecondary` | `rgba(0,0,0,0.65)` | 辅助文字、标签 |
| 文字禁用 | `colorTextDisabled` | `rgba(0,0,0,0.40)` | 禁用态 |
| 边框 | `colorBorder` | `#d9d9d9` | 控件、卡片边界 |
| 分割线 | `colorSplit` | `rgba(5,5,5,0.06)` | 行内 / 区块分隔 |
| 页面背景 | `colorBgLayout` | `#f5f5f5` | 内容区底色 |
| 容器背景 | `colorBgContainer` | `#ffffff` | 卡片、表格、面板 |
| 浅层背景 | `colorFillAlter` | `rgba(0,0,0,0.02)` | 表头、标签底色 |

蓝阶衍生（仅当需浅色 hover / 背景时取，不要另起色号）：
`#E6F4FF #BAE0FF #91CAFF #69B1FF #4096FF #1677FF #0958D9 #003EB3 #002C8C #001D66`

色彩纪律：
- 主色每视图只服务**一个**主行动；其余行动用次级 / 文本按钮。
- 功能色只表达状态，不用于装饰；一套产品内功能色保持一致。
- 页面整体色彩克制，主色 + 中性色为主，功能色点缀。
- 正文 / 标题对比度 ≥ 7:1（WCAG AAA）。

### 1.2 间距（8px 栅格）

尺度（px）：`4 / 8 / 12 / 16 / 24 / 32 / 48`

| Token | 值 | 用法 |
|---|---|---|
| `paddingXS` | 8 | 控件内边距下限、紧凑元素间距 |
| `paddingSM` | 12 | 小卡片内边距 |
| `padding` | 16 | 默认内边距 |
| `paddingLG` | 24 | 卡片 / 区块内边距 |
| `paddingXL` | 32 | 大区块上下间距 |

纵向三档：`8`（小）/ `16`（中）/ `24`（大）；公式 `y = 8 + 8n`。
- 卡片内边距：**24**
- 卡片与其他卡片间距：**16 或 24**
- 区块上下间距：**24 / 32**
- 栅格 `gutter`：**16**（密集）或 **24**（宽松）

### 1.3 圆角

| Token | 值 | 用法 |
|---|---|---|
| `borderRadiusSM` | 4 | 小标签、徽标 |
| `borderRadius` | 6 | 按钮、输入框等控件 |
| `borderRadiusLG` | 8 | 卡片、弹窗、抽屉 |
| 圆形 | — | 仅头像、状态点 |

### 1.4 字体

- 字体家族：`'Source Han Sans SC', 'Noto Sans SC', 'Source Han Sans CN', '思源黑体', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif`（中文 B 端首选思源黑体；未安装时回退系统无衬线）
- 基准：正文 **14px / 行高 22**（lineHeight ≈ 1.5714）
- 字阶（一套系统控制在 **3–5** 种）：`12 / 14 / 16 / 20 / 24 / 30`
- 字重：`400` regular / `500` medium（中文标题）/ `600` semibold（英文加粗、标题强调）
- 数字：`font-variant-numeric: tabular-nums;` 等宽，纵向对比时**右对齐**
- 标题用 `medium`/`semibold` 字重拉开层级，不用颜色堆层级

### 1.5 尺寸（布局）

| 项 | 值 | 说明 |
|---|---|---|
| 画板基准 | 1440 | 向上 1920、向下 1280/1366 适配 |
| 顶部导航高 | 64（48+8n） | 二级导航 48 |
| 侧边栏宽 | 200（200+8n） | 收起态 80 |
| 内容区边距 | ≥ 16 / 24 | 不贴边 |
| 抽屉 Drawer | 400 | 右侧滑出 |
| 表格行高 | 36 / 40 / 48 | 默认 40，密集 36 |
| 表头高 | 56（大栏 80） | — |
| 分页高 | 24 / 32 | — |
| 栅格 | 24 列 | gutter 16/24，动态缩放列宽 |

### 1.6 层级与阴影

- **Level 0 平面**：仅背景 / 分割线区分（列表行、静态区）
- **Level 1**：1px hairline 边框（表格、卡片默认态）
- **Level 2 轻阴影**（浮动面板 / 弹窗 / 悬浮卡片）：
  `0 6px 16px 0 rgba(0,0,0,0.08), 0 3px 6px -4px rgba(0,0,0,0.12), 0 9px 28px 8px rgba(0,0,0,0.05)`
- hover：卡片轻微上浮 + 阴影加深，过渡 150–200ms

---

## 2. 页面骨架（按类型取用）

> 每类页面套对应骨架，保证同类页面结构稳定、可复用。骨架是参考，不是死模板；字段多少可裁剪，但区块顺序与层级不变。

### 2.1 聚合页（Dashboard）
1. 顶部：统计卡片行（`<Statistic>` 嵌 `<Card>`，4 等分，`gutter` 16）
2. 中部：图表区（Responsive Grid + `<Card>` 包裹，每卡标题 + 图表）
3. 下部：最近动态 / 待办列表（`<List>` 或紧凑 `<Table>`）
- 卡片内边距 24；区块间距 24。

### 2.2 列表页（List）
1. 筛选区：`<Form>` 横向排列或 `<Card>` 包裹的筛选条
2. 操作栏：左侧主操作（`<Button type="primary">`）+ 右侧搜索 / 刷新
3. 表格：斑马纹、固定表头、分页、空态；批量操作在勾选后浮出
4. 行内操作：查看 / 编辑放在末列，字数 ≤ 6

### 2.3 表单页（Form）
1. 单列或两列 `<Form>`；标签右对齐（colon）或上下布局
2. 必填项星标；错误内联提示，不靠弹窗
3. 动作区固定底部：取消（次级）+ 提交（主）
4. 长表单用 `<Steps>` 或分区 `<Card>`

### 2.4 详情页（Detail）
1. 返回按钮 + 标题 + 右上操作区
2. 主体：`<Descriptions>`（标签灰底 `colorFillAlter`）分区展示
3. 多段内容用 `<Tabs>` 分区
4. 关联信息：时间线 / 子列表放底部

### 2.5 看板页（Kanban）
1. 横向列（每列 `<Card>` 容器），列头显示计数
2. 列内条目卡片（标题 + 关键字段 + 状态 Tag）
3. 顶部：新建列 / 筛选；条目可拖拽（原型可用静态占位）

---

## 3. 状态与空态（语义化，不用裸文字）

- **状态**：用 `<Tag>` 语义色——成功 `green` / 警告 `gold` / 错误 `red` / 进行中 `blue` / 禁用 `default`。不写裸文字表达状态。
- **空态**：列表 / 详情无数据用 `<Empty>` + 一句引导文案 + 主操作按钮；**不留白板**。
- **加载**：表格 / 卡片用 `<Skeleton>` 或 `<Spin>`；不空白闪烁。
- **反馈**：成功 / 警告 / 错误用 `message` 或 `notification`，停留约 3s，文字 ≤ 30 字。

---

## 4. 自检清单（完成判据）

生成后逐条核对，全部通过才算完成：

- [ ] 所有间距取自 `4/8/12/16/24/32/48`（优先 8 的倍数）
- [ ] 主色 `#1677ff` 只用于主行动 / 当前导航 / 链接；**一视图仅一个主按钮**
- [ ] 功能色只表达状态，不装饰；成功绿 / 警告金 / 错误红 / 进行中蓝
- [ ] 正文 14/22，字阶 ≤ 5 种，标题用 500/600 字重
- [ ] 数字 `tabular-nums` + 右对齐
- [ ] 每类页面套用第 2 节对应骨架（区块顺序 / 层级不变）
- [ ] 所有列表 / 详情有 `<Empty>` 空态，有加载态
- [ ] 状态用 `<Tag>` 语义色，无裸文字状态
- [ ] 1440 宽度下无横向溢出、元素不贴边（边距 ≥ 16）
- [ ] 图标统一 Ant Design Icons、outline、默认 16px、与文字间距 4–8px
- [ ] 对比度：正文 / 标题 vs 背景 ≥ 7:1（浅色背景）

---

## 附：取值来源（评审溯源）

- 色彩：https://ant.design/docs/spec/colors-cn （主色 #1677ff、中性色阶、蓝阶衍生）
- 布局：https://ant.design/docs/spec/layout-cn （1440 画板、8px 网格、24 栅格、常用模度）
- 字体：Ant Design v5/v6 全局 Token（base 14/22、字重 400/500/600、tabular-nums；v4 规范 https://4x.ant.design/docs/spec/font-cn 同义）
- 间距 / 圆角 / 尺寸 Token：`templates/prototype-vite/package.json` 对应 antd ^6.6.0 全局 Token（paddingXS 8 / SM 12 / 16 / LG 24 / XL 32；borderRadius 6 / LG 8；顶栏 64、侧栏 200+8n）
- 原则：Proximity（8/16/24）、Alignment（文案左对齐 / 表单冒号右对齐 / 数字右对齐）、Contrast（主次 / 状态用色+形）、Repetition（重复元素建立关联）、Motion（自然 / 克制 / 高性能，150–300ms）
- 图标：Ant Design v6 已将独立图标规范合并入组件体系，遵循 Ant Design Icons（outline、默认 16px）；官网 https://ant.design/components/icon-cn

> 注：v6 的 `colorInfo` 默认等同 `colorPrimary`(#1677ff)。若后续换肤，主色以 `ConfigProvider` 实际注入值为准，本表同步更新。
