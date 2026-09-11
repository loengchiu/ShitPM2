# ShitPM 原型视觉规范（Tabler 默认基础设施 · Ant Design 6 实现）

> 用途：生成 / 修改 Vite + React 18 + Ant Design 6 原型时，作为视觉 Token、页面骨架、组件状态矩阵与自检清单的**唯一事实源**。
> 调用时机：每次生成或评审原型页面前读取本文件；本文件之外的视觉数值一律以本文件为准，不得在页面、`prototype-writing.md` 或模板中定义第二套视觉值。
> 视觉口径（2026-09-11 v3 拍板）：**结构、尺寸、间距、字体、圆角、阴影、控件规格与图标一律按 Ant Design 官方默认**（权威来源 `references/design-sources/ant-design-official/`，读法见其 `ADAPTATION.md`）；**颜色体系沿用 Tabler**。组件仍用 Ant Design，Tabler 颜色主题由模板自动注入；页面不承担主题选择或换肤决策。项目组的三栏壳层、页面标签、底部操作栏、行为和代码习惯与视觉规范分离。
> 字体：走 antd 官方默认系统字体栈，不做字体覆盖（2026-09-11 拍板①：官方默认栈不含 CJK 显式声明，中文由系统 fallback 渲染，实测显示正常，接受该口径）。
> 图标：**@ant-design/icons**（antd 官方图标库），统一经 `src/shared/icons/` 语义名再导出取用，不直接 import 图标库。
> 组件行为：组件怎么用、什么场景、什么边界见 `references/prototype-component-behavior.md`（本文件的行为补充层）；本文件 Token、骨架、状态与自检清单与之共同构成运行时视觉唯一事实源。
> 落地文件：`templates/prototype-vite/src/theme/tablerTheme.ts` / `tablerTokens.ts`（Tabler 颜色映射与 CSS 变量，**只含颜色 token**）+ `styles/global.css`（壳层全局补丁）+ `src/shared/ui/`（高频共享组件）+ `src/shared/icons/`（官方图标语义映射）+ `src/shared/charts/TablerChart.jsx`（图表适配）。改风格先改视觉规范，再同步主题（限颜色）与共享组件并复验。
> 状态：**已采纳，ShitPM 运行时视觉事实源**（2026-08-17 评审通过；图标随样张确认一并落地）。
> 与 `references/prototype-writing.md` 的关系：其第三节只保留 antd 令牌名作配置参考并指向本文件；数值、页面骨架与状态以本文件为准。

---

## 目录

- 0. 执行流程
- 1. 设计 Token（仅颜色）
- 2. 页面类型与图表适配（结构见 prototype-page-types.md）
- 3. 状态与空态
- 4. 组件状态矩阵
- 5. 自检清单
- 附：取值来源
- 另见: `references/prototype-page-types.md`（页面类型与标准结构）、`references/prototype-role-permission.md`（角色权限表达）、`references/prototype-component-behavior.md`（组件行为规范）

## 0. 执行流程（每轮生成原型走这套）

1. 普通页面直接按模板的主题基础设施组合 shared/ui；页面类型与标准结构按 `references/prototype-page-types.md` 判定并执行，本文件不再重复骨架定义。结果 / 异常页仍走居中卡片骨架，不套业务骨架。
2. 检查页面对应的高频结构是否已有共享组件（`src/shared/ui/`），有则组合，没有才在页面内实现；页面只表达 Design 业务事实。
3. 颜色套用第 1 节 Token 常量，不现场发明色值；尺寸、间距、字号、阴影不写死，走 antd 官方默认；找不到合适颜色 Token 时按 1.8 记录来源与用途，先改 Token 再使用。
4. 状态与空态按第 3、4 节用语义组件表达；图标一律经 `src/shared/icons/` 取用官方图标（第 1.7 节），图表用 `shared/charts/TablerChart.jsx`（第 2.1 节）。
5. 生成后逐条过第 5 节自检清单，未过则改到过为止。

完成判据：适用自检项全部完成，且页面在 1440 宽度下无横向溢出、无贴边、无裸文字状态；按实际命中的断点检查响应式行为。本轮不执行 390px 专项测试。

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

### 1.4 字体（antd 官方默认）

- 字体家族：**走 antd 6 官方默认系统字体栈，主题不覆盖 `fontFamily`**（2026-09-11 拍板①）。官方栈不含 CJK 显式声明，中文由系统 fallback 渲染（Windows 下为微软雅黑），实测显示正常。
- 基准：正文 **14px / 行高 22**（官方默认 `fontSize: 14`）
- 字阶（一套系统控制在 **3–5** 种）：`12 / 14 / 16 / 20 / 24 / 30`
- 字重：`400` regular / `500` medium（中文标题）/ `600` semibold（标题强调）
- 页面主标题（`.page-title`）：**24px / 600 / 行高 32**（`[ShitPM 适配]`，全局唯一主标题，与组件行为规范 §1 一致）
- 数字：`font-variant-numeric: tabular-nums;` 等宽，纵向对比时**右对齐**
- 标题用 `medium`/`semibold` 字重拉开层级，不用颜色堆层级

### 1.5 尺寸、断点与密度

**布局尺寸**

| 项 | 值 | 说明 |
|---|---|---|
| 画板基准 | 1440 | 向上 1920、向下 1280/1366 适配 |
| 顶部导航高 | 56（与官方 `--nav-header-height` 一致；与 `global.css` 的 `calc(100vh - 56px)` 唯一一致） | 二级导航 48 |
| 侧边栏宽 | 200 | 移动端折叠为 0（`collapsedWidth=0`，Header 按钮展开） |
| 内容区边距 | ≥ 16 / 24 | 不贴边；`.content-wrap` 默认 24，992px 以下 16，576px 以下 12 |
| 内容区宽度策略 | 不设全局硬上限 | 表单 `max-width: 960`，结果 / 异常卡 `max-width: 720`（容器级） |
| 弹窗 Modal | 480 / 640 / 800 | 小 / 默认 / 大（不用 Drawer 抽屉，见组件行为规范 §8） |
| 表格单元格 padding | **16 × 16**（官方默认） | 表头字号 **14**（官方默认）；不写死行高，由单元格 padding 撑起 |
| 分页高 | 24 / 32 | — |
| 控件高 | 24 / 32 / 40 | SM / 默认 / LG（官方默认档位，默认 **32**；主题不覆盖 `controlHeight`） |
| 栅格 | 24 列 | gutter 16/24，动态缩放列宽 |

**断点与响应式**

| 断点 | 宽度 | 行为 |
|---|---|---|
| 移动 | < 576 | 内容边距 12；指标卡 2 列；页头纵向堆叠；表格横向滚动；sticky 操作栏铺满；Header 用户名字隐藏 |
| 平板 | 576–991 | Sider 自动折叠（`breakpoint=lg`）；内容边距 16；指标卡 2 列；查询区换行 |
| 桌面 | 992–1199 | 完整侧栏与 4 列指标卡、工具栏换行回收 |
| 宽屏 | ≥ 1200 | 完整桌面层级；操作列 ≤3 按钮，多余收进"更多"下拉（默认不固定列，与组件行为规范 §4 一致） |

### 1.6 层级与阴影（antd 官方默认）

- **阴影走 antd 官方原生**（黑基），主题不覆盖 `boxShadow*` token；2026-09-11 拍板：Tabler 阴影基准（`rgba(18,18,23)` 基）作废，覆盖 2026-09-10 的 Tabler 阴影对齐口径（该项可单独回退）。
- **Level 0 平面**：仅背景 / 分割线区分（列表行、静态区）
- **Level 1**：1px 浅边框（表格、卡片默认态）
- **Level 2 浮层阴影**（下拉 / 弹窗 / 悬浮面板）：antd 全局 token `boxShadowSecondary` 官方默认值，不在页面或 CSS 写死
- hover：卡片轻微上浮 + 阴影加深，过渡 150–200ms；主按钮无投影

### 1.7 图标（@ant-design/icons，官方图标库）

- 来源：**统一经 `src/shared/icons/` 再导出取用**（内部映射到 `@ant-design/icons` 官方图标）；**禁止**页面或组件直接 import 任何图标库。
- 语义名保持 `IconXxx` 习惯（如 `IconPlus`、`IconTrash`），页面调用点无需感知具体官方图标名；新增语义映射时挑官方库中语义最贴切的一个，**先查 `node_modules/@ant-design/icons` 实际导出清单，不臆造图标名**。
- 尺寸：默认 **16px**；卡片图标徽章 / 强调处可用 **20–24px** 但同一视图保持统一档。适配层把 `size` 映射为官方图标的 `fontSize`。
- 风格：官方图标线性描边原样沿用，不改 `stroke`。
- 与文字间距：**4–8px**（图标在文字左侧时）。
- 状态点 / 圆形图标按钮：用 `IconButton` 或图标包在圆形浅底容器（32px 圆）。

### 1.8 新增 Token 规则

找不到合适 Token 时（仅限颜色；尺寸 / 间距 / 阴影走官方默认，不新增）：

1. 先在 1.1 的颜色组内找最接近的同色相值，禁止现场拍值或写进页面级 `style`；
2. 需要新颜色 → 先在 `tablerTokens.ts` 的定义处补充并标注来源分类（`tabler-source` 直接采用 Tabler 参考值 / `antd-adapter` 为映射 antd 的必要适配 / `shitpm-business` 为业务可用性适配）；
3. 同步到本节对应表格，写明用途；页面代码引用 Token 名，不引用裸值。

---

## 2. 页面类型与图表适配

> **页面结构唯一事实源已迁至 `references/prototype-page-types.md`**（7 类 + 公共页 + 快照/只读态横切模式，每类含标准结构 / 必须项 / 禁止项 / 官方章节书签 / 锚点约定）。原第 2 节的 7 类骨架自 v3 起由该文档承担；其中旧「看板页（Kanban）」已改名**任务看板页**并移出 7 类，归入公共页。本节只保留图表适配规则。

### 2.1 图表适配（数据看板）

- 统一使用模板 `src/shared/charts/TablerChart.jsx`：`TablerChart` 容器 + `tablerChartPalette` 色板 + `tablerChartAxis` 坐标轴 / 网格（值来自 `tablerTokens.chart`，不复刻 Arco）。
- 折线图（趋势 / 时间序列）：`color: tablerChartPalette`，`xAxis/yAxis` 展开 `tablerChartAxis`，line `width: 2`，可加浅色面积渐变。
- 饼图 / 环形图（占比 / 分布）：数据少用环形 `radius: [45%, 70%]`；Legend 圆点、`icon: circle`、文字色 `#626976`。
- Tooltip：`trigger: axis`（趋势）/ `trigger: item`（占比），不做自定义皮肤。
- `option` 必须 `useMemo` 保持引用稳定（TablerChart 内部依赖 `[option]`，否则反复 init/dispose）；容器随窗口 resize，不手写尺寸逻辑。

---

## 3. 状态与空态（语义化，不用裸文字）

- **状态**：用 `StatusTag` 语义五档——成功 `success` / 进行中 `progress`(蓝) / 警告 `warning` / 失败 `error` / 弱状态 `weak`(灰)。不写裸文字表达状态。
- **空态**：列表 / 详情无数据用 `EmptyState`（Tabler `IconInbox` 类图标 + 标题 + 指引 + 主操作）；`DataTable` 内置空态兜底。
- **加载**：表格 / 卡片用 `<Skeleton>` 或 `<Spin>` 或 Table `loading`；按钮提交中 `loading`；不空白闪烁。
- **反馈**：成功 / 警告 / 错误用 `message` 或 `notification`（可带对应 Tabler 图标），停留约 3s，文字 ≤ 30 字。

## 4. 组件状态矩阵（全状态覆盖）

> 生成和评审都以“状态可通过 UI 观察”为准，不用“（只读）/（必填）/（选填）”文字代替。`disabled`/`loading`/`status`/`required`/`aria-*` 统一用 antd 语义机制表达。

| 组件 | 默认 | hover | focus-visible | active/selected | disabled/readonly | loading | empty | error/forbidden | 响应式 / 弹层 |
|---|---|---|---|---|---|---|---|---|---|
| `PageHeader`（内部默认实现 `TablerPageHeader`） | 三段式页头 | — | 返回按钮 ring | 返回可点击 | — | — | — | — | 窄屏纵向堆叠、操作换行 |
| `SectionCard`（内部默认实现 `TablerSectionCard`） | 浅边框 + 白底 | 轻上浮 + 阴影加深 | — | — | — | Card loading | — | — | 卡片宽度自适应 |
| `MetricCard`（内部默认实现 `TablerMetricCard`） | 标题 + 数值 + 徽章 | 同卡片 hover | — | — | — | 可配 Spin | 无数据文案 | 异常趋势标红 | 2 列 → 4 列 |
| `Toolbar`（内部默认实现 `TablerToolbar`） | 主区 + 操作区 | — | — | — | 批量按钮随禁用 | — | 无操作时隐藏操作区 | 批量操作禁用于未勾选 | 换行堆叠 |
| `DataTable`（内部默认实现 `TablerDataTable`） | 浅表头 / 浅边框 | 行 hover 高亮 | 单元格内控件 ring | 行选中 | 行级禁改 | `loading` Spin | 内置空态 | 错误态可重试（业务列表达） | 横向滚动，默认不固定列 |
| `StatusTag`（内部默认实现 `TablerStatusTag`） | 语义五档 | — | — | — | 弱状态灰 | — | — | 用 error 档 | 不换行 |
| `IconButton`（内部默认实现 `TablerIconButton`） | 图标按钮 | 浅底 | ring | pressed | `disabled` 置灰 | `loading` | — | `danger` 标红 | 窄屏保持可点击区域 |
| `FormSection`（内部默认实现 `TablerFormSection`） | 分区 Card | — | 字段内控件 ring | — | 系统字段 `disabled` | — | — | 校验错误红边 + 内联提示 | 三列 → 单列 |
| `EmptyState`（内部默认实现 `TablerEmptyState`） | 图标 + 文案 + 操作 | — | 操作按钮 ring | — | 无权限时操作禁用 / 隐藏 | — | 主体即空态 | 失败可重试 | 居中自适应 |
| `ActionBar`（内部默认实现 `TablerActionBar`） | 底部 sticky | — | 按钮 ring | — | 提交中整体禁用 | 按钮 `loading` | — | 校验错误阻止提交 | 窄屏铺满、不拆字 |

弹层与状态联动：Modal 用 antd 原生，`disabled` / `loading` / 校验随触发元素状态联动；隐藏层级的选中态（Select option、Table row、Tabs、导航）全部可观察。

---

## 5. 自检清单（完成判据）

生成后逐条核对，全部通过才算完成：

- [ ] 所有间距取自 `4/8/12/16/20/24/32/48`（优先 4 的倍数）
- [ ] 主色 `#066fd1` 只用于主行动 / 当前导航 / 链接；**一视图仅一个主按钮**
- [ ] 功能色只表达状态，不装饰；成功 `#2fb344` / 警告 `#f59f00` / 错误 `#d63939` / 信息 `#4299e1`
- [ ] 正文 14/22，字阶 ≤ 5 种，标题用 500/600 字重
- [ ] 字体走 antd 官方默认栈，主题不覆盖 `fontFamily`；无字体下载依赖
- [ ] 数字 `tabular-nums` + 右对齐
- [ ] 圆角按用途取固定值：控件 6、小标签 4、卡片 8
- [ ] 边框色 `#e5e7eb`、页面底 `#f9fafb`、表头浅底 `#fafbfc`（非 antd 默认 `#d9d9d9`/`#f5f5f5`）
- [ ] Header 高度 56 与内容区 `calc(100vh - 56px)` 一致，无两套高度
- [ ] 每类页面按 `prototype-page-types.md` 命中类型的标准结构与必须项执行（含分页总条数、筛选折叠、卡头徽章、空字段 `—` 等口径）
- [ ] 高频结构使用 `src/shared/ui/` 共享组件，页面不复制局部 CSS
- [ ] 所有列表 / 详情有 `TablerEmptyState` 空态，有加载态
- [ ] 状态用 `TablerStatusTag` 语义五档，无裸文字状态
- [ ] 第 4 节状态矩阵各项在页面中可观察（含 disabled/readonly、loading、empty、error、selected、responsive）
- [ ] **图标统一经 `src/shared/icons/` 再导出取用官方图标**，默认 16px、与文字间距 4–8px；不直接 import 任何图标库
- [ ] 图表使用 `shared/charts/TablerChart.jsx` 的色板与坐标轴，不引入 Arco 主题
- [ ] 1440 宽度下无横向溢出、元素不贴边（边距 ≥ 16）；实际命中的响应式断点可操作；本轮不执行 390px 专项测试
- [ ] 对比度：正文 / 标题 vs 背景 ≥ 7:1
- [ ] 页面内出现新颜色时，已按 1.8 记录 Token 来源与用途，不是现场拍值；尺寸 / 间距 / 阴影 / 字号无新增写死值，走官方默认
- [ ] 结构、尺寸、字体、阴影、图标按官方默认；颜色走 Tabler 主题；不包含主题选择或多主题运行时分支

### 检查能力边界

- [ ] 已用脚本或浏览器确认可机械观察的事实：源码工程、路由、显式事实锚点、构建、console、交互、计算样式、响应式边界和页面级溢出
- [ ] 未把信息层级、内容密度、品牌感觉、审美和整体可读性等主观视觉质量写成脚本通过；这些项目由用户、人工评审或视觉模型验收，无能力时明确标记未评估

---

## 附：取值来源（评审溯源）

- Tabler 真实 token（**仅颜色**）：`preview.tabler.io` 编译 CSS（`@tabler/core` dist）的 `--tblr-*` 变量 —— 主色 `#066fd1`、功能色 `#2fb344/#f59f00/#d63939/#4299e1`、底 `#f9fafb`、边框 `#e5e7eb`。圆角 6/4/8 与官方本就一致，字体 / 阴影 / 尺寸已改走官方默认
- 落地映射：
  - `templates/prototype-vite/src/theme/tablerTokens.ts`（可执行 Token，唯一数值入口）
  - `templates/prototype-vite/src/theme/tablerTheme.ts`（antd `theme.token` + `theme.components` 一一对应，值全部来自 tablerTokens）
  - `templates/prototype-vite/src/styles/global.css`（CSS 变量 + 壳层 / 焦点 / 表格 / sticky 全局补丁）
  - `templates/prototype-vite/src/shared/ui/`、`shared/icons/`、`shared/charts/TablerChart.jsx`（共享 UI / 图标映射 / 图表适配）
- 图标：`@ant-design/icons`（antd 官方图标库，6.3.2，与 antd 6 同源）；经 `src/shared/icons/` 语义名再导出
- 字体：antd 官方默认系统字体栈（2026-09-11 拍板①，不做覆盖）；中文由系统 fallback 渲染
- 尺寸 / 间距 / 阴影 / 控件规格：antd 6 官方默认（2026-09-11 拍板：除颜色外全按官方；官方结构与交互规则见 `references/design-sources/ant-design-official/`）
- 原型模板：antd ^6.6.0 + react ^18.3.1（`templates/prototype-vite/package.json`）
- 样张：`docs/plans/2026-08-17-tabler-style-sample.html`（静态视觉验证，含聚合 / 列表 / 表单三类 + Tabler 图标）
