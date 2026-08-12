# 原型写法参考

> 本文件是原型阶段的示例和对照说明。
> 硬规则在 `skills/spm-prototype/SKILL.md`。

## 目录

- [常见错误](#常见错误)
- [一、原型定位](#一原型定位)
- [二、源码工程与构建边界](#二源码工程与构建边界)
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
| 失败处理 | 源码工程缺失 | 只有 dist、compiled.js 或构建后的 HTML，没有 package.json / src | 后续无法修改，改一次就要反编译或补丁生成物 | 停止，报告“Prototype 源码工程缺失”，提出一次性迁移方案 | 不修改 dist，不反编译，不补丁生成物 |
| 失败处理 | 直接改 dist | 修改发生在 `dist/` 或带哈希资源文件 | dist 是可重建生成物，改了也会被下次 build 覆盖，且源码不同步 | 改 `src/` 后重新 `npm run build` | 构建失败时先修源码，不部署旧 dist |
| 失败处理 | 原型重新定义业务规则 | src 中包含独立于 design 的业务规则 | 命中该场景说明当前产物未满足对应要求 | 检查原型中的业务规则是否与 design 一致 | 若不一致，回退到 fix 流程 |
| 失败处理 | 表现问题被当成语义问题 | UI 布局问题被误判为业务错误 | 命中该场景说明当前产物未满足对应要求 | 先归类：表现问题 vs 语义问题 | 表现问题只改 prototype，语义问题才回写 design |
| 失败处理 | 未归类就开始修改 | 读完 feedback 后直接改 | 命中该场景说明当前产物未满足对应要求 | 必须先输出归类结果，再开始修改 | 若无法归类，停在澄清，不直接改 |
| 失败处理 | 依赖或构建失败 | `npm ci` / `npm run build` 报错 | 没有可运行的构建，就不能交付 | 按报错修 package.json 或源码，重新构建 | 依赖损坏用“修复依赖并重新构建”重装 |
| 失败处理 | 页面渲染空白 | 路由未注册、组件导入路径错、构建报错 | 命中该场景说明当前产物未满足对应要求 | 检查 routes.jsx 注册、模块导入路径和构建输出 | 回滚到上一可工作版本 |
| 失败处理 | 路由无默认页兜底 | 打开 `/#/unknown` 白屏 | 未注册 `*` 兜底路由 | routes.jsx 必须保留 `path: '*'` 的 NotFound 兜底 | 改路由默认解析 |
| 失败处理 | 验收只测默认页 | 只验证 `/#/`，漏掉其他注册路由 | 路由组件可能各自报错 | **验证必须逐个打开全部注册路由，都渲染正常、console 无错才算通过** | 补开其余路由复验 |
| 失败处理 | 把开发预览当部署证据 | 只跑 `npm run dev` 就交付 | 开发模式暴露的资源路径与构建产物不同 | 交付前必须 `npm run build` + 构建预览复验 | 构建预览异常时以构建结果为准修复 |
| 失败处理 | 状态表达不完整 | 只有默认状态，缺异常/空/加载状态 | 命中该场景说明异常路径不可讨论 | 按 design 状态定义逐个补入原型 | 若状态过多，先补核心状态，其余在 output/prototype/decision-notes.md 中记录待补，不在原型中残留 [TODO] |
| 反模式 | 把所有页面塞进一个组件 | 单个 jsx 文件几千行 | 无法维护，打开很慢 | 按业务模块拆分到 `src/modules/<模块>/` | — |
| 反模式 | 按技术层拆分模块 | 按 hooks/components/utils 分目录而不是按业务模块 | 业务定位困难 | 一个业务模块一个目录，共享件放 `src/shared/` | — |
| 反模式 | 原型独立定义业务规则 | 出现该做法 | 与 design 不一致，造成混乱 | 原型只做展示，业务规则以 design 为准 | — |
| 反模式 | 跳过归类直接修改 | 出现该做法 | 表现问题和语义问题的传播路径完全不同 | 必须先归类再修改 | — |
| 反模式 | 表现问题回写 design | 出现该做法 | 表现层反馈不应改变 design 业务定义 | 表现问题只改 prototype | — |
| 反模式 | 使用外部 CDN | 业务源码中引用 http(s) 资源 | 离线/内网不可用，且 Cloudflare 部署不可控 | 依赖统一走 package.json + npm | — |
| 反模式 | 使用 Vue / daisyUI / Tailwind / `el-` 组件 | 出现该做法 | 已废弃，架构固定为 React + Ant Design 6 | 用 antd 组件（`<Button>`/`<Table>` 等） | — |
| 反模式 | 引入浏览器端 Babel 或第二套构建链 | 出现 text/babel、UMD lib、临时编译脚本 | 源码与运行结果被强行拆开，无法标准维护 | 只用标准 Vite 工程的 npm scripts | — |
| 反模式 | 手写 CSS 模拟组件 | 出现该做法 | 与 antd 视觉不一致，且不可维护 | 用 antd 现成组件 | — |
| 反模式 | 手写 SVG/CSS 模拟图表 | 出现该做法 | 与 Arco 风格图表观感不一致，且不可交互 | 数据看板用 ECharts + Arco 风格主题（见五、） | — |
| 反模式 | 原型页面写解释性标注 | 页面出现“入口：…去向：…”、“（只读）/（必填）/（选填）”、操作说明（Design）、勾选规则（Design）等 | 既不是纯高保真原型，也不是规范标注，两边都不讨好；评审注释应走 prototypemark | 删除所有解释性文本；必填/只读/选填通过 UI 本身表达（红 asterisk / disabled / 无星） | — |
| 失败处理 | 字段状态靠文字标注 | label 含“（只读）”“（必填）”而非用 antd 视觉表达 | 不是超高保真，且可能在不同角色/状态下失效 | `required` 出红 asterisk，`disabled` 出置灰，选填无星 | — |
| 失败处理 | 空/异常/加载态缺失 | 列表/看板只有满数据 mock，无空态、加载失败、无权限表达 | 命中该场景说明异常路径不可讨论 | 每个列表页空 dataSource 显示 Table 内置"暂无数据"空态；关键页补"加载失败点击重试"与无权限置灰 | 按 Design 状态逐个补入原型，先补核心状态 |
| 失败处理 | 配置页用占位代替真实交互 | 新增/编辑/停用/启用为 `message.info('…（示意）')` | 命中该场景说明配置交互不可评审 | 用真实 `Modal` + `Form`（字段按 Design 对应章节），二次确认用 `Modal.confirm` | 字段过多时先补核心字段，其余在 decision-notes 记录待补 |
| 失败处理 | 多角色页面无角色视角 | Design 页面"适用角色"多于一个的页面无角色切换/置灰 | 命中该场景说明权限矩阵不可讨论 | 提供角色切换 `Select` 或"无权限置灰" | 无法判断时按 Design 角色清单逐个补 |
| 反模式 | message.info 占位代替真实弹窗（"示意"） | 出现该做法 | 评审无法讨论真实交互与校验 | 用真实 Modal/Drawer/Form 实现，二次确认用 Modal.confirm | — |
| 反模式 | 只有满数据 mock，无空态/异常态 | 出现该做法 | 异常路径不可讨论 | 补空态/加载失败/无权限表达 | — |
| 反模式 | 让用户手动输入 npm 命令 | README 首屏或交付说明要求打开 PowerShell | 用户目标是双击预览，不是学命令 | 交付 `原型工具.bat` 中文菜单，README 首屏只写双击 BAT | — |
| 反模式 | 页内放"演示角色切换" | 角色切换 Select 出现在页面内而非壳层 Header | 角色切换位置不统一，评审聚焦被分散 | 多角色项目角色切换统一放 Header，页内不渲染 | — |
| 反模式 | 长文本字段用单行 Input | 审计范围/问题描述等多行字段用 `<Input>` 而非 TextArea | 多行内容无法完整表达 | 多行/长文本字段一律 `Input.TextArea`，编辑表单 `Col span={24}` 独占一行 | — |
| 失败处理 | 列表操作列未冻结 | 列表设了 `scroll={{ x }}` 但操作列没有 `fixed:'right'` | 横向滚动时操作列看不见 | 操作列 `fixed: 'right'` 冻结 | antd v6 检测用 `position: sticky`，不是 v4 的 `ant-table-cell-fix-right` 类名 |
| 失败处理 | 页面级操作散落卡片 extra | 保存/提交/返回等出现在卡片右上角或多处重复 | 主操作位置不统一，评审无法确认 | 页面级操作统一底部 sticky 操作栏，同一操作只出现一次 | 列表 toolbar"新建"入口、行内操作、配置入口除外 |
| 失败处理 | 角色操作全显+disabled | 角色不满足的操作也渲染出来再置灰 | 与真实系统权限表达不一致 | 角色不满足的操作不渲染；状态不允许的才置灰 | 状态类操作保留"可见禁用"供评审 |

## 一、原型定位

- 原型与 PRD 平级，均以 design 为基线
- 原型只做展示，不重新定义业务规则
- 技术栈固定为 **标准 Vite + React 18 + Ant Design 6 源码工程**：`src/` 是唯一编辑源，`dist/` 是可重建构建产物
- 用户通过一个 `原型工具.bat` 完成本地预览、构建、重建和条件式上传，不要求用户输入命令

## 二、源码工程与构建边界

标准目录（对应 `templates/prototype-vite/`）：

```text
output/prototype/
├─ 原型工具.bat         用户唯一操作入口（中文菜单）
├─ index.html           应用入口页
├─ package.json         依赖与 scripts（dev/build/preview）
├─ package-lock.json    锁文件，安装一律 npm ci
├─ vite.config.js       Vite 配置（base: './'，Hash 路由无需服务端重写）
├─ src/
│  ├─ main.jsx          挂载入口
│  ├─ App.jsx           壳层（Sider/Header/Content）
│  ├─ routes.jsx        路由注册表
│  ├─ modules/<模块>/   业务页面组件（按 Design 模块组织）
│  ├─ shared/           共享壳层、角色切换、异常页
│  └─ styles/           全局样式
├─ public/              静态资源（原样复制到 dist）
└─ dist/                构建产物（只由 npm run build 生成，可删除重建）
```

三种查看方式边界：

1. **本地即时预览**（BAT 选项 1，`npm run dev`，固定端口 5173）：修改 `src/` 后立即更新，用于边改边看；不把开发服务器内容当作最终部署证据。
2. **本地构建预览**（BAT 选项 2，`npm run build` + `npm run preview`，固定端口 4173）：预览 `dist/` 构建结果，必须在交付或部署前执行，能发现开发模式未暴露的资源路径和构建问题。
3. **Cloudflare 在线预览**：部署对象只允许是 `dist/`，由用户通过 BAT 选项 4 确认后上传。

约束：

1. 允许编辑 `src/`、`index.html`、`package.json`、`vite.config.js`、`public/`、`README.md`；禁止直接编辑 `dist/`、`node_modules/` 和带哈希资源文件。
2. 依赖统一由 `package.json`/`package-lock.json` 定义，安装用 `npm ci`；不得复制旧原型 lib、引用外部 CDN、把 `node_modules/` 复制进 dist。
3. 路由使用 Hash 模式（如 `/#/plan/list`），本地预览与静态托管共用同一套可分享地址，不依赖服务端重写规则。
4. 用户只操作 `原型工具.bat`；命令行用法只面向 AI 和研发排障，不写进用户操作步骤。

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

1. **侧栏（Sider）**：深色主题，宽 220px，可折叠；顶部 logo，下方 Menu 承载模块/页面切换；**Sider 独立滚动，不随整页滚动**（`style={{ height:'100vh', overflow:'auto', position:'sticky', top:0 }}`），菜单长时只在侧栏内部滚动
2. **顶栏（Header）**：高 64px，白底；左侧 Breadcrumb，右侧用户区（角色切换 + 头像 + 退出）；**角色切换统一放 Header**，页内不放"演示角色切换"；角色判断用全称（如"被审单位对接人"）
3. **内容区（Content）**：`#f5f5f5` 底，内边距 24px；承载真正的业务内容
4. 壳层只做路由 + 渲染容器；菜单从 `src/routes.jsx` 派生或与路由显式映射，页面组件注册进路由表

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
| 弹窗 | `<Modal open onOk onCancel width={560}>`（不用 window.confirm；宽度 560 起，可视需要调大） |
| 空状态 | `<Empty />`（列表无数据时由 Table 自动展示） |
| 提示 | `<message.success('...')>` / `<message.error('...')>`（antd 全局 message） |
| 文本域 | `<Input.TextArea autoSize={{ minRows: 4, maxRows: 8 }} />` —— 可编辑输入**强制用 `autoSize`**，不要写 `rows` 固定高度；只读展示用 `disabled` + `rows`（见下方硬规则） |
| **图表（数据看板）** | **用 ECharts + Arco 风格主题**（不用手写 SVG/CSS 模拟）。Arco 无官方图表库；Arco Design Pro 官方用的就是 ECharts，下面的配置复刻 Arco 观感 |

ECharts React 封装 + Arco 主题（放在 `src/shared/Chart.jsx`）：

```jsx
import * as echarts from 'echarts';
import { useEffect, useRef } from 'react';

// Arco 风格图表主题（主色 #165DFF、浅灰网格、文字 #4E5969、极简无阴影）
const ARCO_COLORS = ['#165DFF', '#0FC6C2', '#FFC72E', '#F53F3F', '#00B42A', '#FF7D00', '#722ED1', '#3491FA'];
const ARCO_AXIS = {
  axisLine: { lineStyle: { color: '#E5E6EB' } },
  axisTick: { show: false },
  axisLabel: { color: '#4E5969', fontSize: 12 },
  splitLine: { lineStyle: { color: '#E5E6EB', width: 1 } },
};
export function Chart({ option, height = 260 }) {
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
2. **表头全局不换行**：`styles/global.css` 加 `.ant-table-thead th { white-space: nowrap }`（模板已带）
3. 列数 ≥ 5 或总宽超卡片容宽时：每列必须显式 `width` + Table 配 `scroll={{ x: 总宽 }}`，**否则无 width 的列会被 antd 自动压缩成单字宽度**（如"直流充电桩 01"竖排）
4. 列宽估算基准：**列宽 ≥ 中文字数 × 14 + 32（padding）+ 8（余量）**，否则表头/内容会被挤换行；优先按此设足 `width`
5. 推荐列宽：编号类 140、设备名 130、服务区/类型 100-140、状态 90、时间 160、操作 180-200
6. **列表宽于页面（`scroll={{ x }}` 生效）时，操作列 `fixed: 'right'` 冻结**，横向滚动时操作列始终可见；antd v6 检测冻结用 `position: sticky`，不是 v4 的 `ant-table-cell-fix-right` 类名

约束：

1. 先查 antd 有无现成组件满足需求，不要手写 CSS 模拟
2. 交互（弹窗/抽屉/下拉）用 antd 组件 + React 状态，不用原生 `alert/confirm`
3. 不要用 Vue 语法（`v-if`/`v-model`）、daisyUI 类、Tailwind 类
4. 表格数据与字段以 design 为准，mock 数据要贴合业务

**弹窗（Modal/Drawer）布局硬规则**：

1. **不要在 Modal 内用 Row/Col 把 Form.Item 挤在 1/3 宽度**——Modal 本身宽度有限（默认 520），Col span 8 = 157px 太窄；Form layout="vertical" 下 Form.Item 直接放就 100% 宽度
2. 弹窗默认 `width={560}`（简单表单）或 `width={720}`（多项/含描述），不要无 width 让它默认 520 文字挤
3. OK/取消按钮文案：`okText="确定"` / `cancelText="取消"`（不是 antd 默认的英文）

**文本域（TextArea）硬规则**：

1. **多行/长文本字段一律用 `Input.TextArea`，不用单行 `Input`**：如审计范围/目标/重点/立项依据、问题描述、反馈意见等；编辑表单里该字段 `Col span={24}` 独占一行
2. **可编辑 TextArea 必须用 `autoSize={{ minRows: 4, maxRows: 8 }}`**，不要写 `rows={N}` 固定高度
3. 短文本（如备注）`minRows: 2`；审批意见/说明/描述类 `minRows: 4, maxRows: 8`
4. 可编辑长文本（如富描述）`minRows: 6, maxRows: 12`，超过 maxRows 后内部滚动
5. 配套一般加 `showCount maxLength={500}` 之类，提示剩余字数
6. **只读富文本/长文本展示**：`<Input.TextArea disabled rows={6} autoSize={false} />` 整行表达（rows 取 6-8 视内容量），只读状态用 `disabled` 表达，不套 autoSize

**详情描述（Descriptions）硬规则**：

1. 详情页固定 `column={2}`（两组一行）；长文本字段 `span: 2` 整行独占
2. 统计摘要区可例外用 `column={3}`

**页面级操作按钮硬规则**：

1. 详情/编辑/操作页的页面级按钮（保存/提交/发送/审批/下达/发起/转办/取消/返回等）统一放**页面底部 sticky 操作栏**（`position: sticky; bottom: 0`，模板 `global.css` 已带 `.page-action-bar`），不散落在卡片 `extra`
2. 同一操作不重复出现；列表 toolbar"新建"入口、行内操作、配置管理入口除外

## 六、7 类页面固定骨架

B 端顶级页面固定 7 类，生成时按对应骨架搭，不临场发挥：

**1. 聚合页（工作台）**
```
页头（标题+副标题）→ KPI 统计卡 Row（4 列，gutter 16）
→ 待办/列表 Card（Table 或 List）
```

**2. 列表页**
```
页头 → Card[ 查询 Form(inline, style={{rowGap:12}}) → Divider → 工具栏(新增/批量操作) → Table(columns/width/scroll.x，操作列 fixed:'right') ]
查询按钮（查询/重置）必须在 Form 内最后一项；工具栏只放增删改类操作，不放查询按钮。
Form 换行时两行之间必须有 12px 间距（用 Form 的 rowGap），否则两行挨在一起视觉拥挤。
```

**3. 表单页**
```
页头 → Form(vertical, max-width 960)
→ Card[ 基本信息 ]（Row gutter24 + Col span8 三列；长文本/多行字段 Col span=24 独占一行）
→ 底部 sticky 操作栏（取消 + 保存 primary）
多步骤表单拆多个 Card 顺序排，不用 Tabs
```

**4. 详情页**
```
页头（含返回）→ Card[ Descriptions bordered column=2，长文本字段 span:2 整行独占 ]
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
5. 页面组件放 `src/modules/<模块>/`，并在 `src/routes.jsx` 注册；跨页面共享的壳层、角色切换、异常页放 `src/shared/`

坏例子：

- 每个页面重新发明一套导航
- 页面结构临场发挥，同类页面长不一样
- 主体内容还没写清，先花大量时间做装饰
- 直接改 dist 或构建产物来“完成”修改

## 八、原型输入

确认版 Design 是 Prototype 的唯一产品事实源。PRD 仅可选用于发现表达差异或冲突，不是 Prototype 生成前置；冲突时以 Design 为准。

1. 必须读取 design.md
2. 如 prd.md 已存在，还需读取：PRD 中与原型相关的业务闭环、页面落点、字段使用、状态和权限说明（PRD 结构不固定，Design 仍是唯一事实源）
3. 如存在反馈，读取 `output/prototype/prototype-feedback.md`

## 九、反馈输入边界

反馈分类、停止条件和语义变更传播由 `skills/spm-prototype/SKILL.md` 与 `contracts/fix-propagation-rules.md` 负责；本文件只保留原型生成和表现层写法。
