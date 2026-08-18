# 原型写法参考

> 本文件只说明 Ant Design 组件调用、源码工程边界和页面组织。视觉 Token、7 类页面骨架、状态矩阵与视觉自检的唯一事实源是 `prototype-visual-spec.md`；生成或修改页面前先读取它。
> 流程、停止条件和反馈传播由 `skills/spm-prototype/SKILL.md` 负责；多页面 shell、导航或空白页问题再读取 `prototype-shell.md`。

## 目录

- 一、源码工程边界
- 二、组件与视觉入口
- 三、交互硬规则
- 四、表格、表单与弹层规则
- 五、页面组合
- 六、输入与反馈边界
- 七、交付前检查

## 一、源码工程边界

Prototype 与 PRD 平级，均以 Design 为事实基线；原型只表达 Design，不新增业务规则、字段、状态、权限、流程或跨系统责任。

标准工程使用 Vite + React 18 + Ant Design 6：

```text
output/prototype/
├─ 原型工具.bat       用户唯一操作入口
├─ index.html          应用入口
├─ package.json        依赖与 dev/build/preview scripts
├─ package-lock.json   锁文件，安装使用 npm ci
├─ vite.config.js      Vite 配置
├─ src/                唯一业务编辑源
│  ├─ main.jsx         ConfigProvider 与应用挂载
│  ├─ App.jsx          shell
│  ├─ routes.jsx       唯一路由注册表
│  ├─ modules/<模块>/  Design 模块页面
│  ├─ shared/          共享 UI、图标、图表和异常页
│  └─ styles/          全局样式
├─ public/             静态资源
└─ dist/               只由 npm run build 生成
```

执行边界：

1. 只编辑 `src/`、`index.html`、`package.json`、`vite.config.js`、`public/`、README 等源码文件；dist、node_modules 和带哈希构建资源由工具生成。
2. 依赖统一由 package.json/package-lock.json 定义；不复制旧原型 lib，不使用外部 CDN、浏览器端 Babel、UMD lib 或第二套构建链。
3. 路由使用 Hash 模式；页面由 `src/routes.jsx` 和模块组件表达，默认保留 `path: "*"` 的 NotFound 兜底。
4. 本地即时预览使用 `npm run dev`；交付前必须 `npm run build` 后用 `npm run preview` 检查构建产物；用户操作写入 `原型工具.bat`，不要求用户手输 npm 命令。

Hash 地址可能带查询参数（例如 `#/demo-form?case=1`）；路由匹配前只使用 `?` 之前的路径，不能把查询参数拼进路由名导致已注册页面落入 NotFound。模板路由解析结果至少提供 `{ path, query, route }`，query 使用 `URLSearchParams` 保留；同一路径 query 改变时页面必须更新，`navigate()` 接受 `/demo-form?mode=edit&id=1` 或 `#/demo-form?mode=edit&id=1`。

## 二、组件与视觉入口

视觉规则只从 `prototype-visual-spec.md` 读取；可执行 Token 在模板 `src/theme/tablerTokens.ts`，Ant Design 映射在 `src/theme/tablerTheme.ts`，高频结构在 `src/shared/ui/`。页面不复制全局颜色、字号、间距、圆角或阴影。

需要被全局样式或 Portal 内容读取的 CSS 变量挂在 `document.documentElement`；不要只挂在 `#root`。Ant Design 的 Modal、Dropdown 等内容可能渲染到 `document.body`，无法继承 `#root` 上的变量。

常用组件：

| 用途 | 首选写法 |
| --- | --- |
| 按钮 | `<Button type="primary">保存</Button>` |
| 查询 | `<Form layout="inline">` + `Form.Item`，查询/重置属于 Form |
| 表单 | `Form layout="vertical"` + `Form.Item` + `Row/Col` |
| 下拉/日期/数字 | `Select` / `DatePicker` / `InputNumber` |
| 表格 | `TablerDataTable`；字段和数据来自 Design |
| 状态 | `TablerStatusTag`，不直接自造颜色 |
| 详情 | `Descriptions`，默认两列，长文本独占一行 |
| 结果/异常 | `Result` + 恢复或返回操作 |
| 空态 | `TablerEmptyState` 或 `TablerDataTable` 内置空态 |
| 页面级操作 | `TablerActionBar` sticky 底部操作栏 |

图表统一使用 `src/shared/charts/TablerChart.jsx`，色板和坐标轴来自该封装；页面 option 使用 `useMemo` 保持引用稳定：

```jsx
const trendOption = useMemo(() => ({
  color: tablerChartPalette,
  tooltip: { trigger: "axis" },
  xAxis: { type: "category", data: labels, ...tablerChartAxis },
  yAxis: { type: "value", ...tablerChartAxis },
  series: [{ type: "line", data: values }],
}), [labels, values]);
```

图标统一使用 `@tabler/icons-react`，优先复用 `src/shared/icons/`；不混用 Ant Icons。找不到精确图标时使用语义接近的官方 Tabler 图标，并在共享映射中记录。

## 三、交互硬规则

1. 先查 Ant Design 是否已有组件；弹窗、抽屉、下拉、确认和反馈使用 antd 组件与 React 状态，不使用原生 `alert`、`confirm` 或 `window.confirm`。
2. 配置管理的新增、编辑、启用、停用必须使用真实 `Modal` + `Form`；破坏性操作使用 `Modal.confirm`，不能用“示意”消息代替。
3. 必填、只读、选填使用 antd 语义表达：必填用 `Form.Item required`，只读/系统判定用 `disabled` 或等价属性，选填不加星；页面不写“（只读）”“（必填）”“入口：”“去向：”等解释性标注。
4. 状态机不允许的操作可见且 `disabled`；角色不满足的操作不渲染。不要把两者混成一种表现。
5. 列表、看板和关键详情必须能观察空数据、加载、失败/重试、无权限或其他 Design 要求的异常状态；不只展示满数据 mock。
6. 多角色项目的角色切换统一放 shell Header；页面不放“演示角色切换”。
7. JSX 中使用的组件、图标和工具函数必须逐一确认已 import；构建通过不代表关闭态或条件渲染分支没有运行时 `ReferenceError`，必须在真实浏览器中打开这些分支。
8. 可见按钮必须产生打开/关闭层、校验、状态变化、列表变化、路由变化或反馈之一；无行为的视觉样张按钮删除或改为非交互展示。可编辑字段使用稳定 `name`，必填/格式/范围通过 `rules` 表达；页面外 ActionBar 通过 Form 实例调用 `submit()` / `resetFields()`。
9. route、row、menu、action、field 使用稳定唯一 ID；共享表格与行操作不得以展示文案或数组下标作为身份。Table wrapper 对 `scroll`、`pagination`、`locale` 明确默认、合并或透传规则，不得静默丢失调用方配置。
10. Modal、message、notification 等上下文相关 API 使用 antd `App.useApp()`；Portal 层必须验证主题变量、焦点、Esc、关闭后焦点回归和点击穿透。响应式统一使用 <576、576–991、≥992、≥1200，390px 只能作为额外窄屏优化。

## 四、表格、表单与弹层规则

### 表格

- 操作列使用 `whiteSpace: "nowrap"`；表头全局不换行；状态列使用 `TablerStatusTag`。
- 列数较多或总宽超过卡片宽度时，每列给出合理 `width` 并设置 `scroll={{ x: ... }}`；只有确有业务需要固定列时才使用 `fixed: "right"`，并按组件行为规范复核背景、层级和横向滚动遮挡。
- 查询按钮和重置按钮放查询 Form；工具栏放新增、批量和其他业务操作。
- 数字、金额和时间按视觉规范处理为可读的等宽数字和合适对齐，不在页面临时发明样式。

### 表单与文本域

- 三列表单使用 `Row gutter` 与 `Col span={8}`；多行/长文本使用 `Input.TextArea`，编辑态用 `autoSize`，长文本字段占 `span={24}`。
- 只读长文本可用 `disabled` 的 TextArea；不要用普通 Input 压缩多行内容。
- 详情 `Descriptions` 默认 `column={2}`；长文本字段 `span: 2`。
- `DatePicker` / `RangePicker` 的控件值使用 Dayjs 对象；如果业务状态保存字符串，必须同时实现字符串 → `dayjs()` 的回填和控件值 → 字符串的提交转换，不能只做单向转换。

### 弹层与页面操作

- Modal/Drawer 内的垂直表单直接占满可用宽度，不用 `Row/Col` 把字段挤成窄列；复杂弹层按内容需要设置宽度。
- OK/取消按钮使用中文文案；页面级保存、提交、审批、返回和取消等操作统一放 `TablerActionBar`，同一操作不重复出现。列表 toolbar 的新建、行内操作和配置入口可留在对应区域。
- 自定义 Modal 底部操作使用 `footer` 或同一 flex 容器布局，保持取消在前、确定在后，并按视觉规范对齐；禁止用 `float` 或零散块级布局拼接按钮。

## 五、页面组合

生成时先读取视觉规范并选择对应的 7 类页面骨架，再按以下顺序落位：统一 shell → 页面骨架 → Design 字段/数据/状态 → 弹窗、抽屉、分页、空态和异常表达。

- 业务页面放 `src/modules/<模块>/`，跨页共享件放 `src/shared/`，路由在 `src/routes.jsx` 登记。
- 高频页头、Card、Toolbar、Table、Status、Empty、ActionBar 和 Chart 优先复用模板共享组件；不要为单个页面复制一套 Tabler CSS。
- 页面结构、Token、状态矩阵、响应式、焦点和弹层要求以视觉规范对应章节为准；本文件不再复制那套数值或 7 类骨架。
- 业务规则以 Design 为准；Design 待确认项不能在原型中静默拍板。

## 六、输入与反馈边界

1. 生成和修改前读取目标模块 Design 事实闭包；PRD 仅用于辅助发现表达差异，冲突时以 Design 为准。
2. 有 `output/prototype/prototype-feedback.md` 时，先按模板分类，再决定修改范围。
3. 表现问题只改 Prototype；字段、状态、权限、流程、异常、责任边界或模块冲突属于语义问题，停止静默修改并转入 Design/Fix。
4. 反馈无法归类时先澄清，不直接改源码。

## 七、交付前检查

完成前确认：源码工程检查通过；npm ci 和 npm run build 通过；用真实浏览器打开默认页、全部注册路由和带 query 的 Hash 地址，且 console 无错；对实际存在的 Modal、Form、Select、角色切换和响应式状态完成代表性操作。角色切换若只存在 React 内存中，切换后先断言，不要立即 reload；除非 Design/实现明确要求持久化。Select 使用真实 `.click()` 打开并选择可见选项；行内操作按 role、可见文字、`aria-label` 或 `title` 定位，不假设一定是链接元素。关键 Design 事实、状态、权限和异常可观察；视觉规范的共享 UI、图标、图表和状态要求已落实；未编辑 dist；未把未验证内容说成完成。

只在必须挂钩样式时使用稳定的自定义 `className` 或 `data-*`；不要维护 Ant Design 内部 DOM 类名清单作为跨版本契约，组件升级后按锁定版本的真实渲染结果复查。
