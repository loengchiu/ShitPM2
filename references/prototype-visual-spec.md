# ShitPM 原型视觉规范（Claude、Tabler 或 traework 三选一 · Ant Design 6 实现）

> 用途：生成 / 修改 Vite + React 18 + Ant Design 6 原型时，作为视觉 Token、页面骨架、组件状态矩阵与自检清单的**唯一事实源**。
> 调用时机：每次生成或评审原型页面前读取本文件；本文件之外的视觉数值一律以本文件为准，不得在页面、`prototype-writing.md` 或模板中定义第二套视觉值。
> 品牌主题：**Claude**、**Tabler** 与 **traework** 三选一。组件仍用 Ant Design，主题文件分别承载品牌 Token；当前模板默认 Tabler。项目组的三栏壳层、页面标签、底部操作栏、行为和代码习惯独立于品牌主题，不在单个原型内混用两套主题。切换流程见 `prototype-writing.md`「品牌主题接入」。
> 字体：西文 / 数字走 **Inter**（Tabler 同款），中文回落**思源黑体**（2026-08-17 评审结论）；未安装思源黑体时系统默认无衬线正常显示，不把内置 / 下载字体作为阻塞条件。
> 图标：**@tabler/icons-react**（100% Tabler 图标，不混用 Ant Icons）。
> 组件行为：组件怎么用、什么场景、什么边界见 `references/prototype-component-behavior.md`（本文件的行为补充层）；本文件 Token、骨架、状态与自检清单与之共同构成运行时视觉唯一事实源。
> 落地文件：`templates/prototype-vite/src/theme/` 下的 `claudeTheme.ts` / `tablerTheme.ts`（antd 映射与 CSS 变量）+ `styles/global.css`（全局补丁）+ `src/shared/ui/`（高频共享组件）+ `src/shared/icons/`（图标语义映射）+ `src/shared/charts/TablerChart.jsx`（图表适配）。改风格先改对应主题 Token 与视觉规范，再同步全局样式和共享组件。
> 状态：**已采纳，ShitPM 运行时视觉事实源**（2026-08-17 评审通过；图标随样张确认一并落地）。
> 与 `references/prototype-writing.md` 的关系：其第三节只保留 antd 令牌名作配置参考并指向本文件；数值、页面骨架与状态以本文件为准。

---

## 目录

- 0. 执行流程
- 1. 设计 Token
- 2. 页面骨架
- 3. 状态与空态
- 4. 组件状态矩阵
- 5. 自检清单
- 附：取值来源
- 另见: `references/prototype-component-behavior.md`（组件行为规范）

## 0. 执行流程（每轮生成原型走这套）

1. 确定页面类型（聚合 / 列表 / 表单 / 详情 / 看板 / 结果 / 异常，共 7 类）→ 取用第 2 节的对应骨架；结果 / 异常页是特殊页，走居中卡片骨架，不套业务骨架。
2. 检查页面对应的高频结构是否已有共享组件（`src/shared/ui/`），有则组合，没有才在页面内实现；页面只表达 Design 业务事实。
3. 套用第 1 节 Token 常量，不现场发明色值 / 间距 / 字号；找不到合适 Token 时按 1.8 记录来源与用途，先改 Token 再使用。
4. 状态与空态按第 3、4 节用语义组件表达；图标一律用 `@tabler/icons-react`（第 1.7 节），图表用 `shared/charts/TablerChart.jsx`（第 2.8 节）。
5. 生成后逐条过第 5 节自检清单，未过则改到过为止。

完成判据：自检清单全部勾选，且页面在 1440 宽度下无横向溢出、无贴边、无裸文字状态；390px 下无页面级横向溢出（表格允许局部横向滚动）。

---

## 1. 设计 Token（唯一事实源）

> 所有视觉数值从这里取。需要新值先在组内找最接近的 4 的倍数，不要随手写 10/18/22 这类非标数。

### 1.1 色彩（对齐 Tabler 真实值）

| 角色 | Token | 值 | 用途 |
|---|---|---|---|
| 主色 | `colorPrimary` | `#066fd1` | 主行动按钮、当前导航、链接、重要信息高亮 |
| 主色 hover | `colorPrimaryHover` | `#0559a8` | 主按钮 / 链接 hover |
| 成功 | `colorSuccess` | `#2fb344` | 成功 / 已完成 / 已验证 |
| 警告 | `colorWarning` | `#f59f00` | 待处理 / 接近阈值 / 需关注 |
| 错误 | `colorError` | `#d63939` | 失败 / 校验不通过 / 破坏性操作 |
| 信息 | `colorInfo` | `#4299e1` | 进行中 / 提示（Tabler 独立信息蓝，不复用主色） |
| 文字一级 | `colorText` | `#232e3c` | 标题、正文、主要数据 |
| 文字二级 | `colorTextSecondary` | `#626976` | 辅助文字、标签、表头 |
| 文字三级 | `colorTextTertiary` | `#959dac` | 占位符、禁用、次要说明 |
| 边框 | `colorBorder` | `#e5e7eb` | 控件、卡片边界（Tabler 浅灰，比 antd 默认浅） |
| 分割线 | `colorSplit` | `#e5e7eb` | 行内 / 区块分隔 |
| 页面背景 | `colorBgLayout` | `#f9fafb` | 内容区底色（比 antd 更白净） |
| 容器背景 | `colorBgContainer` | `#ffffff` | 卡片、表格、面板 |
| 浅层背景 | `colorFillAlter` | `#fafbfc` | 表头、标签底色、hover 行 |
| 深色侧栏 | `colorSider` | `#182433` | 侧栏背景（Tabler dark nav 色） |
| 深色侧栏选中态 | `colorSiderSelectedBg` | `rgba(6,111,209,0.22)` | 深色侧栏当前导航背景（`antd-adapter`） |
| 深色背景文字 | `colorTextOnDark` | `#ffffff` | 深色侧栏当前导航文字（`antd-adapter`） |
| 主色浅选中态 | `colorPrimarySelectedBg` | `rgba(6,111,209,0.09)` | Select 等控件的已选项背景（`antd-adapter`） |
| 焦点光圈 | `focusRing` | `rgba(6,111,209,0.18)` | 键盘可见焦点 ring（配合 `outline` 2px） |

色彩纪律（同 Tabler 克制观感）：
- 主色每视图只服务**一个**主行动；其余行动用次级 / 文本按钮。
- 功能色只表达状态，不用于装饰；一套产品内功能色保持一致。
- 页面整体色彩克制，主色 + 中性色为主，功能色点缀。
- 正文 / 标题对比度 ≥ 7:1（WCAG AAA）。

### 1.2 间距（4px 基数，对齐 Tabler / Bootstrap 尺度）

尺度（px）：`4 / 8 / 12 / 16 / 20 / 24 / 32 / 48`

| Token | 值 | 用法 |
|---|---|---|
| `paddingXS` | 8 | 控件内边距下限、紧凑元素间距 |
| `paddingSM` | 12 | 小卡片内边距 |
| `padding` | 16 | 默认内边距 |
| `paddingMD` | 20 | 中等间距（区块内次间隔） |
| `paddingLG` | 24 | 卡片 / 区块内边距 |
| `paddingXL` | 32 | 大区块上下间距 |

- 卡片内边距：**24**
- 卡片与其他卡片间距：**16 或 24**（聚合页指标卡用 16，区块间用 24）
- 区块上下间距：**24 / 32**（Tabler 比 antd 默认更透气）
- 栅格 `gutter`：**16**（密集）或 **24**（宽松）

### 1.3 圆角（Tabler 阶梯，base 6）

| Token | 值 | 用法 |
|---|---|---|
| `borderRadiusSM` | 4 | 小标签、徽标、状态点 |
| `borderRadius` | 6 | 控件唯一圆角：按钮、输入框等一律取 6 |
| `borderRadiusLG` | 8 | 卡片、弹窗、图标徽章 |
| 圆形 | `999px` | 仅头像、状态点、圆形图标按钮、图标徽章 |

### 1.4 字体

- 字体家族：`Inter Var,Inter,Source Han Sans SC,Noto Sans SC,Source Han Sans CN,思源黑体,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,PingFang SC,Microsoft YaHei,sans-serif`（完整引号写法见 `tablerTokens.typography.fontFamily`）
  - 西文 / 数字：**Inter**（Tabler 同款，几何无衬线、字重 300–700、数字 tabular）
  - 中文：**思源黑体**首选，未安装回退系统无衬线；不依赖下载 / 内置字体，不因字体缺失阻塞构建。
- 基准：正文 **14px / 行高 22**（lineHeight ≈ 1.5714）
- 字阶（一套系统控制在 **3–5** 种）：`12 / 14 / 16 / 20 / 24 / 30`
- 字重：`400` regular / `500` medium（中文标题）/ `600` semibold（英文加粗、标题强调）
- 页面主标题（`.page-title`）：Tabler 标准 h2 = **20px / 600 / 行高 28**；模板采用 **24px / 600 / 行高 32** 大标题变体（`[ShitPM 适配]`，全局唯一主标题，与组件行为规范 §1 一致）
- 数字：`font-variant-numeric: tabular-nums;` 等宽，纵向对比时**右对齐**
- 标题用 `medium`/`semibold` 字重拉开层级，不用颜色堆层级

### 1.5 尺寸、断点与密度

**布局尺寸**

| 项 | 值 | 说明 |
|---|---|---|
| 画板基准 | 1440 | 向上 1920、向下 1280/1366 适配 |
| 顶部导航高 | 56（Tabler 顶栏略矮于 antd 默认 64；与 `global.css` 的 `calc(100vh - 56px)` 唯一一致） | 二级导航 48 |
| 侧边栏宽 | 200 | 移动端折叠为 0（`collapsedWidth=0`，Header 按钮展开） |
| 内容区边距 | ≥ 16 / 24 | 不贴边；`.content-wrap` 默认 24，992px 以下 16，576px 以下 12 |
| 内容区宽度策略 | 不设全局硬上限 | 表单 `max-width: 960`，结果 / 异常卡 `max-width: 720`（容器级） |
| 弹窗 Modal | 480 / 640 / 800 | 小 / 默认 / 大（不用 Drawer 抽屉，见组件行为规范 §8） |
| 表格行高 | 40（密集 36） | 表头 56，模板 `cellPaddingBlock: 10` |
| 分页高 | 24 / 32 | — |
| 控件高 | 24 / 32 / 40 | SM / 默认 / LG |
| 栅格 | 24 列 | gutter 16/24，动态缩放列宽 |

**断点与响应式**

| 断点 | 宽度 | 行为 |
|---|---|---|
| 移动 | < 576 | 内容边距 12；指标卡 2 列；页头纵向堆叠；表格横向滚动；sticky 操作栏铺满；Header 用户名字隐藏 |
| 平板 | 576–991 | Sider 自动折叠（`breakpoint=lg`）；内容边距 16；指标卡 2 列；查询区换行 |
| 桌面 | 992–1199 | 完整侧栏与 4 列指标卡、工具栏换行回收 |
| 宽屏 | ≥ 1200 | 完整桌面层级；操作列 ≤3 按钮，多余收进"更多"下拉（默认不固定列，与组件行为规范 §4 一致） |

### 1.6 层级与阴影（Tabler 极轻）

- **Level 0 平面**：仅背景 / 分割线区分（列表行、静态区）
- **Level 1**：1px hairline 浅边框（表格、卡片默认态），边框色统一 `#e5e7eb`（非 antd 默认 `#d9d9d9`）
- **Level 2 轻阴影**（浮动面板 / 弹窗 / 悬浮卡片）：`0 2px 4px rgba(35,46,60,0.04)`（极轻，几乎只一道浅影）
- hover：卡片轻微上浮 + 阴影加深（`0 4px 10px rgba(35,46,60,0.08)`），过渡 150–200ms
- **Tabler 去噪哲学**：默认不靠重边框和深阴影堆层次，靠**浅底 + 留白 + 极轻边框**分隔；主按钮无投影

### 1.7 图标（@tabler/icons-react，100% Tabler）

- 来源：从 `@tabler/icons-react` 引入，如 `import { IconBolt, IconSearch } from @tabler/icons-react`；**不混用 `@ant-design/icons`**。
- 常用操作与状态的语义映射集中在 `src/shared/icons/index.jsx`（搜索 / 刷新 / 查看 / 编辑 / 删除 / 返回 / 保存 / 确认 / 警告 / 错误等），页面优先复用，不重复维护清单。
- 尺寸：默认 **16px**；卡片图标徽章 / 强调处可用 **20–24px** 但同一视图保持统一档。
- 风格：Tabler 图标本身即线性描边（outline），沿用默认 `stroke-width` 与线性描边原样。
- 与文字间距：**4–8px**（图标在文字左侧时）。
- 状态点 / 圆形图标按钮：用 `TablerIconButton` 或 `<IconX size={16} />` 包在圆形浅底容器（`.tabler-icon-badge`，32px 圆）。
- 命名：用 Tabler 官方图标名（如 `IconChargingPile`、`IconAlertTriangle`、`IconCircleCheck`），生成时挑语义最贴切的一个；找不到精确图标时在 `shared/icons/index.jsx` 集中记录替代选择，不臆造名称。

### 1.8 新增 Token 规则

找不到合适 Token 时：

1. 先在 1.1–1.7 的组内找最接近的 4 的倍数或同色相值，禁止现场拍值或写进页面级 `style`；
2. 需要新值 → 先在 `tablerTokens.ts` 的定义处补充并标注来源分类（`tabler-source` 直接采用 Tabler 参考值 / `antd-adapter` 为映射 antd 的必要适配 / `shitpm-business` 为业务可用性适配）；
3. 同步到本节对应表格，写明用途；页面代码引用 Token 名，不引用裸值。

---

## 2. 页面骨架（7 类 · Tabler 哲学）

> 每类页面套对应骨架。骨架是参考，不是死模板；字段多少可裁剪，但区块顺序与层级不变。
> 基础骨架 5 类（聚合 / 列表 / 表单 / 详情 / 看板）+ 特殊页 2 类（结果 / 异常）；结果 / 异常页不套业务骨架，走居中卡片。
> **Tabler 共性**：卡片浅边框 + 极轻阴影 + 24 内边距 + 区块留白 24/32；表格浅边框、可选极浅斑马纹；表单聚焦蓝色光圈（3px 浅蓝 ring）。

### 2.1 聚合页（Dashboard）
1. 顶部：统计卡片行（`TablerMetricCard`，4 等分，`gutter` 16）；**每卡左上角一个圆形图标徽章**（浅底 + Tabler 图标）
2. 中部：图表区（`TablerSectionCard` 包裹，`TablerChart`）
3. 下部：最近动态 / 待办列表（`TablerDataTable` 或 `<List>`）
- 卡片内边距 24；区块间距 24。

### 2.2 列表页（List）
1. 壳层页签栏表达当前页面；只有 Design 要求上下文标题时才使用 `TablerPageHeader`
2. 筛选区：`<Form>` 横向排列（`rowGap: 12`）或 `<Card>` 包裹的筛选条
3. 操作栏：`TablerToolbar` 左侧主操作（`<Button type="primary">`）带 Tabler 图标 + 右侧刷新等图标按钮
4. 表格：`TablerDataTable` 浅边框、固定表头、分页、空态；行末**文字操作列**（≤3 个文字按钮，查看 / 编辑 / 删除，不用图标；多余操作收进"更多"下拉；默认不固定列，与组件行为规范 §4 一致）
5. 批量操作在勾选后浮出

### 2.3 表单页（Form）
1. 壳层页签栏表达当前页面 → `Form(layout=vertical, max-width 960)` → `TablerFormSection` 分区 Card；详情或需要上下文标题时才加 `TablerPageHeader`
2. 必填项星标；错误内联提示，不靠弹窗
3. 控件聚焦：蓝色边框 + 3px 浅蓝光圈（antd 由 `colorPrimary` 派生，`global.css` 提供 focus-visible ring）
4. 动作区固定底部：`TablerActionBar`（取消 + 提交 primary）

### 2.4 详情页（Detail）
1. 返回按钮（`TablerPageHeader onBack`，带 `IconArrowLeft`）+ 标题 + 右上操作区（图标按钮）
2. 主体：`<Descriptions>`（标签浅底 `colorFillAlter`）分区展示；长文本字段 `span: 2` 整行独占
3. 多段内容用 `<Tabs>` 分区；关联信息：时间线 / 子列表放底部（`TablerDataTable` pagination false）

### 2.5 看板页（Kanban）
1. 筛选 / 工具栏（`TablerToolbar`）→ 横向列容器（每列 `TablerSectionCard`），列头显示计数
2. 列内条目卡片（标题 + 关键字段 + `TablerStatusTag`）
3. 窄屏下列容器改为纵向堆叠；条目可拖拽（原型可用静态占位）

### 2.6 结果页（Result）
居中内容卡（max-width 720）→ `<Result status=success|error>` + 恢复操作（返回 / 重试）

### 2.7 异常页（Error）
居中内容卡（max-width 720）→ `<Result status=404|403|500>` + 返回按钮；模板 `NotFound.jsx` 即 404 示例

### 2.8 图表适配（数据看板）

- 统一使用模板 `src/shared/charts/TablerChart.jsx`：`TablerChart` 容器 + `tablerChartPalette` 色板 + `tablerChartAxis` 坐标轴 / 网格（值来自 `tablerTokens.chart`，不复刻 Arco）。
- 折线图（趋势 / 时间序列）：`color: tablerChartPalette`，`xAxis/yAxis` 展开 `tablerChartAxis`，line `width: 2`，可加浅色面积渐变。
- 饼图 / 环形图（占比 / 分布）：数据少用环形 `radius: [45%, 70%]`；Legend 圆点、`icon: circle`、文字色 `#626976`。
- Tooltip：`trigger: axis`（趋势）/ `trigger: item`（占比），不做自定义皮肤。
- `option` 必须 `useMemo` 保持引用稳定（TablerChart 内部依赖 `[option]`，否则反复 init/dispose）；容器随窗口 resize，不手写尺寸逻辑。

---

## 3. 状态与空态（语义化，不用裸文字）

- **状态**：用 `TablerStatusTag` 语义五档——成功 `success` / 进行中 `progress`(蓝) / 警告 `warning` / 失败 `error` / 弱状态 `weak`(灰)。不写裸文字表达状态。
- **空态**：列表 / 详情无数据用 `TablerEmptyState`（Tabler `IconInbox` 类图标 + 标题 + 指引 + 主操作）；`TablerDataTable` 内置空态兜底。
- **加载**：表格 / 卡片用 `<Skeleton>` 或 `<Spin>` 或 Table `loading`；按钮提交中 `loading`；不空白闪烁。
- **反馈**：成功 / 警告 / 错误用 `message` 或 `notification`（可带对应 Tabler 图标），停留约 3s，文字 ≤ 30 字。

## 4. 组件状态矩阵（全状态覆盖）

> 生成和评审都以“状态可通过 UI 观察”为准，不用“（只读）/（必填）/（选填）”文字代替。`disabled`/`loading`/`status`/`required`/`aria-*` 统一用 antd 语义机制表达。

| 组件 | 默认 | hover | focus-visible | active/selected | disabled/readonly | loading | empty | error/forbidden | 响应式 / 弹层 |
|---|---|---|---|---|---|---|---|---|---|
| `TablerPageHeader` | 三段式页头 | — | 返回按钮 ring | 返回可点击 | — | — | — | — | 窄屏纵向堆叠、操作换行 |
| `TablerSectionCard` | 浅边框 + 白底 | 轻上浮 + 阴影加深 | — | — | — | Card loading | — | — | 卡片宽度自适应 |
| `TablerMetricCard` | 标题 + 数值 + 徽章 | 同卡片 hover | — | — | — | 可配 Spin | 无数据文案 | 异常趋势标红 | 2 列 → 4 列 |
| `TablerToolbar` | 主区 + 操作区 | — | — | — | 批量按钮随禁用 | — | 无操作时隐藏操作区 | 批量操作禁用于未勾选 | 换行堆叠 |
| `TablerDataTable` | 浅表头 / 浅边框 | 行 hover 高亮 | 单元格内控件 ring | 行选中 | 行级禁改 | `loading` Spin | 内置空态 | 错误态可重试（业务列表达） | 横向滚动，默认不固定列 |
| `TablerStatusTag` | 语义五档 | — | — | — | 弱状态灰 | — | — | 用 error 档 | 不换行 |
| `TablerIconButton` | 图标按钮 | 浅底 | ring | pressed | `disabled` 置灰 | `loading` | — | `danger` 标红 | 窄屏保持可点击区域 |
| `TablerFormSection` | 分区 Card | — | 字段内控件 ring | — | 系统字段 `disabled` | — | — | 校验错误红边 + 内联提示 | 三列 → 单列 |
| `TablerEmptyState` | 图标 + 文案 + 操作 | — | 操作按钮 ring | — | 无权限时操作禁用 / 隐藏 | — | 主体即空态 | 失败可重试 | 居中自适应 |
| `TablerActionBar` | 底部 sticky | — | 按钮 ring | — | 提交中整体禁用 | 按钮 `loading` | — | 校验错误阻止提交 | 窄屏铺满、不拆字 |

弹层与状态联动：Modal 用 antd 原生，`disabled` / `loading` / 校验随触发元素状态联动；隐藏层级的选中态（Select option、Table row、Tabs、导航）全部可观察。

---

## 5. 自检清单（完成判据）

生成后逐条核对，全部通过才算完成：

- [ ] 所有间距取自 `4/8/12/16/20/24/32/48`（优先 4 的倍数）
- [ ] 主色 `#066fd1` 只用于主行动 / 当前导航 / 链接；**一视图仅一个主按钮**
- [ ] 功能色只表达状态，不装饰；成功 `#2fb344` / 警告 `#f59f00` / 错误 `#d63939` / 信息 `#4299e1`
- [ ] 正文 14/22，字阶 ≤ 5 种，标题用 500/600 字重
- [ ] 字体家族 Inter 优先、中文回落思源黑体、系统无衬线兜底；无字体下载依赖
- [ ] 数字 `tabular-nums` + 右对齐
- [ ] 圆角按用途取固定值：控件 6、小标签 4、卡片 8
- [ ] 边框色 `#e5e7eb`、页面底 `#f9fafb`、表头浅底 `#fafbfc`（非 antd 默认 `#d9d9d9`/`#f5f5f5`）
- [ ] Header 高度 56 与内容区 `calc(100vh - 56px)` 一致，无两套高度
- [ ] 每类页面套用第 2 节对应骨架（7 类，区块顺序 / 层级不变）
- [ ] 高频结构使用 `src/shared/ui/` 共享组件，页面不复制局部 Tabler CSS
- [ ] 所有列表 / 详情有 `TablerEmptyState` 空态，有加载态
- [ ] 状态用 `TablerStatusTag` 语义五档，无裸文字状态
- [ ] 第 4 节状态矩阵各项在页面中可观察（含 disabled/readonly、loading、empty、error、selected、responsive）
- [ ] **图标统一 `@tabler/icons-react`**，默认 16px、线性描边、与文字间距 4–8px，无 Ant Icons 混用；优先复用 `shared/icons`
- [ ] 图表使用 `shared/charts/TablerChart.jsx` 的色板与坐标轴，不引入 Arco 主题
- [ ] 1440 宽度下无横向溢出、元素不贴边（边距 ≥ 16）；575/576 与 991/992 边界可操作；390px 无页面级横向溢出
- [ ] 对比度：正文 / 标题 vs 背景 ≥ 7:1
- [ ] 页面内出现新颜色 / 圆角 / 阴影 / 字号 / 间距时，已按 1.8 记录 Token 来源与用途，不是现场拍值
- [ ] 本轮已明确选择 Tabler / Claude / traework 之一（默认 Tabler，见 §0 品牌主题）；单个原型不混用多套品牌主题

### 检查能力边界

- [ ] 已用脚本或浏览器确认可机械观察的事实：源码工程、路由、显式事实锚点、构建、console、交互、计算样式、响应式边界和页面级溢出
- [ ] 未把信息层级、内容密度、品牌感觉、审美和整体可读性等主观视觉质量写成脚本通过；这些项目由用户、人工评审或视觉模型验收，无能力时明确标记未评估

---

## 附：取值来源（评审溯源）

- Tabler 真实 token：`preview.tabler.io` 编译 CSS（`@tabler/core` dist）的 `--tblr-*` 变量 —— 主色 `#066fd1`、功能色 `#2fb344/#f59f00/#d63939/#4299e1`、圆角 base 6 / sm 4 / lg 8、底 `#f9fafb`、边框 `#e5e7eb`、字体 `Inter Var,Inter,…`、阴影 `0 2px 4px rgba(0,0,0,.04)`
- 落地映射：
  - `templates/prototype-vite/src/theme/tablerTokens.ts`（可执行 Token，唯一数值入口）
  - `templates/prototype-vite/src/theme/tablerTheme.ts`（antd `theme.token` + `theme.components` 一一对应，值全部来自 tablerTokens）
  - `templates/prototype-vite/src/styles/global.css`（CSS 变量 + 壳层 / 焦点 / 表格 / sticky 全局补丁）
  - `templates/prototype-vite/src/shared/ui/`、`shared/icons/`、`shared/charts/TablerChart.jsx`（共享 UI / 图标映射 / 图表适配）
- 图标：`@tabler/icons-react`（React 图标库，与 antd 组件无冲突）
- 字体：Inter（西文 / 数字）+ 思源黑体（中文，2026-08-17 评审结论）；未安装时系统无衬线兜底，不引入 CDN
- 原型模板：antd ^6.6.0 + react ^18.3.1（`templates/prototype-vite/package.json`）
- 样张：`docs/plans/2026-08-17-tabler-style-sample.html`（静态视觉验证，含聚合 / 列表 / 表单三类 + Tabler 图标）
