# 原型写法参考

> 本文件是原型阶段的示例和对照说明。
> 硬规则在 `skills/spm-prototype/SKILL.md`。

## 目录

- [常见错误](#常见错误)
- [一、原型定位](#一原型定位)
- [二、技术栈与加载](#二技术栈与加载)
- [三、Ant Design 6 权威令牌](#三ant-design-6-权威令牌)
- [四、通用后台基座](#四通用后台基座)
- [五、组件使用约定](#五组件使用约定)
- [六、7 类页面固定骨架](#六7-类页面固定骨架)
- [七、页面落位方式](#七页面落位方式)
- [八、原型输入](#八原型输入)
- [九、反馈输入边界](#九反馈输入边界)

## 常见错误

| 级别 | 场景 | 识别信号 | 为什么错 | 首选修复 | 仍失败处理 |
|---|---|---|---|---|---|
| 失败处理 | 原型只有一个 HTML 无法维护 | 页面过多全塞在一个文件 | 命中该场景说明当前产物未满足对应要求 | 按模块拆分 HTML 文件 | 若文件超过 5000 行，必须拆分 |
| 失败处理 | 原型重新定义业务规则 | HTML 中包含独立于 design 的业务规则 | 命中该场景说明当前产物未满足对应要求 | 检查原型中的业务规则是否与 design 一致 | 若不一致，回退到 fix 流程 |
| 失败处理 | 原型拆分不当 | 按技术层拆而不是按业务模块 | 命中该场景说明当前产物未满足对应要求 | 一个子系统一个 HTML 文件，index.html 做入口 | 若模块间有共享组件，提取到公共 JS |
| 失败处理 | 表现问题被当成语义问题 | UI 布局问题被误判为业务错误 | 命中该场景说明当前产物未满足对应要求 | 先归类：表现问题 vs 语义问题 | 表现问题只改 prototype，语义问题才回写 design |
| 失败处理 | 未归类就开始修改 | 读完 feedback 后直接改 | 命中该场景说明当前产物未满足对应要求 | 必须先输出归类结果，再开始修改 | 若无法归类，停在澄清，不直接改 |
| 失败处理 | 原型依赖 lib/ 缺失 | `lib/react-antd/` 下 react/antd/babel/dayjs/echarts 缺失 | 命中该场景说明当前产物未满足对应要求 | 提示用户运行 `python scripts/python/download-prototype-libs.py` | 停下，不凭记忆生成 |
| 失败处理 | 状态表达不完整 | 只有默认状态，缺异常/空/加载状态 | 命中该场景说明当前产物未满足对应要求 | 按 design 状态定义逐个补入原型 | 若状态过多，先补核心状态，其余在 output/prototype/decision-notes.md 中记录待补，不在原型中残留 [TODO] |
| 失败处理 | 页面渲染空白 | 脚本加载顺序错 / lib 缺失 / babel 编译报错 | 命中该场景说明当前产物未满足对应要求 | 1) 核对 lib/react-antd 八件套[^八件套]引用顺序 2) 检查 text/babel 块 JSX 语法 3) 打开浏览器 console 看报错 | 回滚到上一可工作版本 |
| 失败处理 | 页面无样式 | HTML 缺 antd.css/reset.css 引用 | 命中该场景说明当前产物未满足对应要求 | 给全部 HTML 补齐本地 lib 引用 | —— |
| 反模式 | 把所有页面塞进一个 HTML | 出现该做法 | 无法维护，打开很慢 | 按模块拆分，用 index.html 做入口 | — |
| 反模式 | 原型独立定义业务规则 | 出现该做法 | 与 design 不一致，造成混乱 | 原型只做展示，业务规则以 design 为准 | — |
| 反模式 | 跳过归类直接修改 | 出现该做法 | 表现问题和语义问题的传播路径完全不同 | 必须先归类再修改 | — |
| 反模式 | 表现问题回写 design | 出现该做法 | 表现层反馈不应改变 design 业务定义 | 表现问题只改 prototype | — |
| 反模式 | 使用外部 CDN | 出现该做法 | file:// 协议下加载失败，且原型不再离线可用 | 使用本地 lib/ 目录八件套[^八件套] | — |
| 反模式 | 使用 Vue / daisyUI / Tailwind / `el-` 组件 | 出现该做法 | 已废弃，架构固定为 React + Ant Design 6 | 用 antd 组件（`<Button>`/`<Table>` 等） | — |
| 反模式 | 引入 React 19 / 其他构建链 | 出现该做法 | React 19 无 UMD，无构建架构跑不起来 | 用 React 18.3.1 UMD | — |
| 反模式 | 手写 CSS 模拟组件 | 出现该做法 | 与 antd 视觉不一致，且不可维护 | 用 antd 现成组件 | — |
| 反模式 | 手写 SVG/CSS 模拟图表 | 出现该做法 | 与 Arco 风格图表观感不一致，且不可交互 | 数据看板用 ECharts + Arco 风格主题（见五、） | — |

## 一、原型定位

- 原型与 PRD 平级，均以 design 为基线
- 原型只做展示，不重新定义业务规则
- 第一版走最小原型，不追求重型系统
- 技术栈固定为 **React 18 + Ant Design 6**（无构建、离线双击即用），不引入构建链、不引入其他组件库

## 二、技术栈与加载

固定架构（对应 `templates/prototype.html` 的 head/body 引用顺序，不得改变顺序）：

| 顺序 | 文件 | 说明 |
|---|---|---|
| 1 | `lib/react-antd/reset.css` | antd 官方样式重置 |
| 2 | `lib/react-antd/antd.css` | antd 6 全量 CSS（CSS 变量主题，默认主色 `#1677ff`） |
| 3 | `lib/react-antd/react.production.min.js` | React 18.3.1 UMD（全局 `React`） |
| 4 | `lib/react-antd/react-dom.production.min.js` | ReactDOM 18.3.1 UMD（全局 `ReactDOM`） |
| 5 | `lib/react-antd/dayjs.min.js` | 日期库（antd 依赖，全局 `dayjs`） |
| 6 | `lib/react-antd/locale-zh-cn.js` | dayjs 中文 locale |
| 7 | `lib/react-antd/antd-with-locales.min.js` | antd 6.5.4 UMD 全量+中文 locale（全局 `window.antd`） |
| 8 | `lib/react-antd/echarts.min.js` | ECharts 5 UMD（全局 `echarts`），数据看板用 |
| 9 | `lib/react-antd/babel.min.js` | babel-standalone（浏览器端编译 JSX） |

页面代码写在 `<script type="text/babel" data-presets="react">` 块内，用 JSX 语法。挂载方式：

```jsx
const { useState, useMemo } = React;
const { Layout, Menu, ... } = window.antd;
// 解构出用到的组件，直接写 JSX
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
```

约束：

1. 不要改变脚本加载顺序（react 必须在 antd 前，dayjs 必须在 antd 前）
2. 不要用 React 19（无 UMD）；不要引入 npm/vite/构建
3. 不要用外部 CDN；所有资源走本地 `lib/react-antd/`
4. 不要引入其他组件库（MUI、Element 等）；交互全部用 antd 组件实现

## 三、Ant Design 6 权威令牌

以下数值直接取自 antd 源码（`components/theme/themes/seed.ts` 与 `shared/gen*.ts`），是 v6 默认主题的权威值，原型生成时不得另造一套。

**颜色（默认主题）**

| 令牌 | 值 | 用途 |
|---|---|---|
| 主色 colorPrimary | `#1677ff` | 主按钮、选中态、链接 |
| 成功 colorSuccess | `#52c41a` | 成功状态 |
| 警告 colorWarning | `#faad14` | 警告状态 |
| 错误 colorError | `#ff4d4f` | 错误/危险状态 |
| 页面背景 colorBgLayout | `#f5f5f5` | content 区底色 |
| 容器背景 colorBgContainer | `#ffffff` | 卡片/表格底 |
| 边框 colorBorder | `#d9d9d9` | 输入框/卡片边框 |
| 次级边框 colorBorderSecondary | `#f0f0f0` | 表格行分隔等 |
| 正文文字 colorText | `rgba(0,0,0,0.88)` | 主要文字 |
| 次级文字 colorTextSecondary | `rgba(0,0,0,0.65)` | 次要说明 |
| 弱化文字 colorTextTertiary | `rgba(0,0,0,0.45)` | 占位/弱化 |

**间距标尺**（4px 基准，`sizeUnit=4, sizeStep=4`，padding/margin 直接映射）

| 令牌 | 值 |
|---|---|
| sizeXXS / paddingXXS / marginXXS | 4px |
| sizeXS / paddingXS / marginXS | 8px |
| sizeSM / paddingSM / marginSM | 12px |
| size / padding / margin | 16px |
| sizeMD / paddingMD / marginMD | 20px |
| sizeLG / paddingLG / marginLG | 24px |
| sizeXL / paddingXL / marginXL | 32px |
| sizeXXL / marginXXL | 48px |

**尺寸**

| 令牌 | 值 | 用途 |
|---|---|---|
| controlHeightXS | 16px | 迷你控件 |
| controlHeightSM | 24px | 小控件（size="small"） |
| controlHeight | 32px | 默认控件高 |
| controlHeightLG | 40px | 大控件（size="large"） |
| controlPaddingHorizontal | 12px | 控件左右内边距 |
| fontWeightStrong | 600 | 强调字重 |
| 顶栏高 Header | 64px | 壳层固定 |
| 侧栏宽 Sider | 220px | 壳层默认 |

**圆角**（`borderRadius=6` 派生）

| 令牌 | 值 | 用途 |
|---|---|---|
| borderRadiusXS | 2px | 极小元素 |
| borderRadiusSM | 4px | 小元素 |
| borderRadius | 6px | 默认 |
| borderRadiusLG | 8px | 卡片/大容器 |

**字号阶梯**（基准 14，等比缩放取偶）

| 令牌 | 值 | 行高 |
|---|---|---|
| fontSizeSM | 12px | (12+8)/12 = 1.67 |
| fontSize | 14px | 1.57 |
| fontSizeLG | 16px | 1.5 |
| fontSizeXL / heading4 | 20px | 1.4 |
| heading3 | 24px | 1.33 |
| heading2 | 30px | 1.27 |
| heading1 | 38px | 1.21 |

**阴影**（antd 默认有 elevation，弹层/卡片悬浮用）

```css
box-shadow: 0 6px 16px 0 rgba(0,0,0,0.08),
            0 3px 6px -4px rgba(0,0,0,0.12),
            0 9px 28px 8px rgba(0,0,0,0.05);
```

**字体**：默认 `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif`；中文环境由系统回退（苹方/微软雅黑），不要强制指定思源黑体。

## 四、通用后台基座

固定壳层（模板已实现，一般不需要改）：

1. **侧栏（Sider）**：深色主题，宽 220px，可折叠；顶部 logo，下方 Menu 承载模块/页面切换
2. **顶栏（Header）**：高 64px，白底；左侧 Breadcrumb，右侧用户区（头像+退出）
3. **内容区（Content）**：`#f5f5f5` 底，内边距 24px；承载真正的业务内容
4. 页面切换用 `useState` + Menu `items/onClick`，页面组件注册进 `PAGES` 对象

版式方向：

- 侧栏深色、顶栏白底、内容区浅灰
- 内容用白色 Card 承载
- 层级靠间距、Card、标题和按钮优先级表达，不靠花哨装饰

## 五、组件使用约定

全部用 Ant Design 6 组件，写法是 JSX。常用映射：

| 用途 | 写法 |
|---|---|
| 按钮 | `<Button type="primary">保存</Button>`（primary 主操作/ danger 危险/ 默认普通） |
| 查询区 | `<Form layout="inline">` + `<Form.Item label="字段">` |
| 表单 | `<Form layout="vertical">` + `<Form.Item label rules>`，栅格用 `<Row gutter={24}>` + `<Col span={8}>` |
| 下拉 | `<Select options={[{value,label}]} />` |
| 日期 | `<DatePicker />`（dayjs 已配中文） |
| 数字输入 | `<InputNumber min={0} />` |
| 单选 | `<Radio.Group><Radio value={1}>` |
| 表格 | `<Table columns={cols} dataSource={data} pagination={...} />` |
| 状态标签 | `<Tag color="blue/green/red/orange/default">` |
| 统计卡片 | `<Card><Statistic title="..." value={...} /></Card>` |
| 详情描述 | `<Descriptions bordered column={2} items={[{label, children}]} />` |
| 分页 | Table 自带 `pagination={{ pageSize, showTotal }}` |
| 结果/异常 | `<Result status="success/404/403/500" title sub-title extra />` |
| 弹窗 | `<Modal open onOk onCancel />`（不用 window.confirm） |
| 空状态 | `<Empty />`（列表无数据时由 Table 自动展示） |
| 提示 | `<message.success('...')>` / `<message.error('...')>`（antd 全局 message） |
| **图表（数据看板）** | **用 ECharts + Arco 风格主题**（不用手写 SVG/CSS 模拟）。Arco 无官方图表库；Arco Design Pro 官方用的就是 ECharts，下面的配置复刻 Arco 观感 |

ECharts React 封装 + Arco 主题（在 `<script type="text/babel">` 块里定义一次）：

```jsx
// Arco 风格图表主题（主色 #165DFF、浅灰网格、文字 #4E5969、极简无阴影）
const ARCO_COLORS = ['#165DFF', '#0FC6C2', '#FFC72E', '#F53F3F', '#00B42A', '#FF7D00', '#722ED1', '#3491FA'];
const ARCO_AXIS = {
  axisLine: { lineStyle: { color: '#E5E6EB' } },
  axisTick: { show: false },
  axisLabel: { color: '#4E5969', fontSize: 12 },
  splitLine: { lineStyle: { color: '#E5E6EB', width: 1 } },
};
function Chart({ option, height = 260 }) {
  const ref = useRef(null);
  useEffect(() => {
    const chart = echarts.init(ref.current);
    chart.setOption(option);
    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => { window.removeEventListener('resize', onResize); chart.dispose(); };
  }, [option]);
  return <div ref={ref} style={{ width: '100%', height }} />;
}
```

折线图（趋势）和饼图（占比）典型 option：

```jsx
const trendOption = useMemo(() => ({
  color: ARCO_COLORS,
  tooltip: { trigger: 'axis' },
  grid: { left: 12, right: 16, top: 24, bottom: 8, containLabel: true },
  xAxis: { type: 'category', data: ['D1','D2','D3',...], ...ARCO_AXIS },
  yAxis: { type: 'value', ...ARCO_AXIS },
  series: [{ name: '趋势', type: 'line', smooth: true, data: [...],
    itemStyle: { color: '#165DFF' }, lineStyle: { width: 2 },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
      colorStops: [{ offset: 0, color: 'rgba(22,93,255,0.25)' }, { offset: 1, color: 'rgba(22,93,255,0.02)' }] } } }],
}), []);

const pieOption = useMemo(() => ({
  color: ARCO_COLORS,
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, icon: 'circle', itemWidth: 8, itemHeight: 8, textStyle: { color: '#4E5969', fontSize: 12 } },
  series: [{ type: 'pie', radius: ['45%', '70%'], center: ['50%', '42%'],
    label: { color: '#4E5969', fontSize: 12 },
    data: [{ name: '小程序', value: 42 }, { name: 'App', value: 28 }, ...] }],
}), []);
```

调用：`<Chart option={trendOption} height={260} />`。**option 必须用 useMemo 保持引用稳定**（Chart 内部依赖 [option]，否则会反复 init/dispose）。

Table 列定义示例：

```jsx
const columns = [
  { title: '状态', dataIndex: 'status', width: 110,
    render: (v, r) => <Tag color={r.color}>{v}</Tag> },
  // 操作列：必须给 Space 加 whiteSpace:'nowrap'，否则表格列宽紧张时会把"详情"拆成"详/情"两行
  { title: '操作', key: 'action', width: 180,
    render: () => <Space size="middle" style={{ whiteSpace: 'nowrap' }}><a>查看</a><a>编辑</a><a>运维</a></Space> },
];
```

**表格列宽硬规则**：

1. 操作列必须 `whiteSpace: 'nowrap'`（防"详情"被拆成"详/情"两行）
2. 列数 ≥ 5 或总宽超卡片容宽时：每列必须显式 `width` + Table 配 `scroll={{ x: 总宽 }}`，**否则无 width 的列会被 antd 自动压缩成单字宽度**（如"直流充电桩 01"竖排）
3. 推荐列宽：编号类 140、设备名 130、服务区/类型 100-140、状态 90、时间 160、操作 180-200

约束：

1. 先查 antd 有无现成组件满足需求，不要手写 CSS 模拟
2. 交互（弹窗/抽屉/下拉）用 antd 组件 + React 状态，不用原生 `alert/confirm`
3. 不要用 Vue 语法（`v-if`/`v-model`）、daisyUI 类、Tailwind 类
4. 表格数据与字段以 design 为准，mock 数据要贴合业务

## 六、7 类页面固定骨架

B 端顶级页面固定 7 类，生成时按对应骨架搭，不临场发挥：

**1. 聚合页（工作台）**
```
页头（标题+副标题）→ KPI 统计卡 Row（4 列，gutter 16）
→ 待办/列表 Card（Table 或 List）
```

**2. 列表页**
```
页头 → Card[ 查询 Form(inline, style={{rowGap:12}}) → Divider → 工具栏(新增/批量操作) → Table(columns/width/scroll.x) ]
查询按钮（查询/重置）必须在 Form 内最后一项；工具栏只放增删改类操作，不放查询按钮。
Form 换行时两行之间必须有 12px 间距（用 Form 的 rowGap），否则两行挨在一起视觉拥挤。
```

**3. 表单页**
```
页头 → Form(vertical, max-width 960)
→ Card[ 基本信息 ]（Row gutter24 + Col span8 三列，长字段 span 16/24 占满）
→ 底部右对齐操作条（取消 + 保存 primary）
多步骤表单拆多个 Card 顺序排，不用 Tabs
```

**4. 详情页**
```
页头（含返回）→ Card[ Descriptions bordered column=2 ]
→ Card[ 关联明细 Table（pagination false）]
```

**5. 数据看板页**
```
页头 → KPI 统计卡 Row（4 列）→ Row[ 主图 Col span16 + 侧图 Col span8 ]
主图：折线图（趋势/时间序列），ECharts + Arco 风格主题（ARCO_COLORS + ARCO_AXIS）
侧图：饼图或环形图（占比/分布），数据少用环形 radius: ['45%','70%']
option 必须 useMemo 包，Chart 组件内部依赖 [option]，否则反复 init/dispose
```

**6. 结果页**
```
居中 Card（max-width 720）→ Result(status=success/error) + 操作按钮
```

**7. 异常页**
```
居中 Card（max-width 720）→ Result(status=404/403/500) + 返回按钮
```

## 七、页面落位方式

推荐顺序：

1. 先套统一壳层（模板已带）
2. 再确定当前页面主任务，按第六节选页面骨架
3. 再按 Design 填充字段、数据、状态
4. 最后补弹窗、抽屉、空状态、分页等辅助区域

坏例子：

- 每个页面重新发明一套导航
- 页面结构临场发挥，同类页面长不一样
- 主体内容还没写清，先花大量时间做装饰

## 八、原型输入

确认版 Design 是 Prototype 的唯一产品事实源。PRD 仅可选用于发现表达差异或冲突，不是 Prototype 生成前置；冲突时以 Design 为准。

1. 必须读取 design.md
2. 如 prd.md 已存在，还需读取：PRD 中与原型相关的业务闭环、页面落点、字段使用、状态和权限说明（PRD 结构不固定，Design 仍是唯一事实源）
3. 如存在反馈，读取 `output/prototype/prototype-feedback.md`

## 九、反馈输入边界

反馈分类、停止条件和语义变更传播由 `skills/spm-prototype/SKILL.md` 与 `contracts/fix-propagation-rules.md` 负责；本文件只保留原型生成和表现层写法。

[^八件套]: 指 `lib/react-antd/` 目录下的 `reset.css`、`antd.css`、`react.production.min.js`、`react-dom.production.min.js`、`dayjs.min.js`、`locale-zh-cn.js`、`antd-with-locales.min.js`、`babel.min.js` 八个本地依赖文件，所有 HTML 通过相对路径 `./lib/react-antd/...` 引用。
