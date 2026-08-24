# Prototype 组件行为边界

> 本文件只在命中特定场景时读取。它负责组件选择、组合边界、稳定例外和跨层运行时契约；共享 UI 的名称、props、DOM、CSS 和默认实现以 templates/prototype-vite/src/shared/ui/ 源码为准，视觉值与 Token 以 prototype-visual-spec.md 为准，工程写法以 prototype-writing.md 为准，通用完成门槛以 skills/spm-prototype/SKILL.md 为准。

## 1. 组件选择与组合判断

- 每个视图只有一个主操作；Card 头部直接操作不超过 2 个，更多操作进入下拉。
- 查询条件区与业务工具栏分离：查询、重置属于查询 Form；新增、批量和业务操作属于工具栏。
- 普通列表、表单、看板页默认由壳层页签表达当前页面，不额外放大标题；详情、结果、异常等需要上下文标题的页面才使用 TablerPageHeader。
- 表格默认不固定列；只有宽度、阅读连续性或关键操作确有需要时才固定，并在真实浏览器中横向滚动复核固定列的遮挡、背景和层级。
- 当前 TablerRowActions 的可见操作与更多操作口径以实际源码为准；不要在规则文档中维护另一份 API 表。
- 高频结构先查并复用 shared/ui。共享组件不承载 Design 字段、权限、状态机、接口或流程；无法承接已确认 Design 时，才组合 Ant Design 原生组件或页面特有结构，并记录回退原因。
- Modal 与 Drawer 的选择由任务性质决定，不能由包装组件静默决定。普通 Modal 使用真实 Modal + Form；破坏性确认使用 Modal.confirm；页面级提交、保存、审批和返回使用页面操作栏。
- 表单校验使用字段规则和内联反馈；必填、只读、禁用和角色权限用组件语义表达，不用解释性文字代替。
- 列表、详情和结果场景必须有可观察的空态、加载、失败/重试、无权限或其他 Design 要求状态；按钮必须产生可观察后置结果。
- 只有跨项目重复出现且已经稳定的例外，才升级为全局规则；一次性例外留在页面实现及其原因中，不要求回写本文件。

## 2. 特定场景例外

### 表格与操作

- 固定列只在业务上必须常驻可见，或宽度与阅读连续性确实要求时使用；其他情况用横向滚动。固定列必须有实色背景、正确层级和边界阴影，普通表头文字不得穿透固定列表头区域。
- 操作列密度见 writing §4（默认 ≤3 文字操作，多余进下拉）；Design 要求更高密度时说明业务原因并验证窄屏可操作性。
- 自定义分页、空态或表格 wrapper 时，不得静默丢失调用方的 scroll、pagination、locale；pagination={false} 必须保持语义。

### 表单与弹层

- Form、普通 Modal、回填、提交、重置或页面外 ActionBar 场景，确认 Form 实例、稳定字段名、校验规则和提交/重置生命周期归属；不要让共享包装组件接管业务字段或流程。
- 日期控件、Modal footer 等写法以 writing §4 为准；本文件只在「共享包装组件接管了业务字段或流程」或「footer 丢失原语义」这类越界时介入判断。

### Portal、响应式与回退

- Dropdown、Select、DatePicker、Modal 等 Portal 内容必须能看到主题变量，且真实浏览器检查焦点、Esc、关闭后焦点回归和点击穿透。
- CSS 变量若需被 Portal 读取，挂在 document.documentElement；不以 #root 继承作为假设。
- Sider 只让菜单区滚动，遮罩、sticky ActionBar 与 Portal 使用统一层级；响应式按 <576、576–991、≥992、≥1200 检查，390px 只作额外窄屏优化。
- 共享组件无法表达 Design 时，说明缺失能力和选择原生/局部组合的原因；不得为了复用而改变产品事实，也不得为了规则完整而新增演示消费者。

## 3. 跨层运行时契约

- 当前 antd 版本、组件支持的 DOM/props 和真实渲染结果以模板锁定依赖与源码为准；不要把内部类名清单、复制的 API 或历史实现写成本文件契约。
- JSX 使用的组件、图标和工具函数必须显式 import。图标按钮必须有稳定 aria-label；可见操作必须有打开/关闭层、校验、状态/列表/路由变化或反馈。
- Hash 路由按 path 匹配并保留 query；同一路径 query 改变必须更新页面。对象 ID、route、row、menu、action、field 使用稳定唯一 ID，不以文案或数组下标定位。
- 页面外 ActionBar 通过 Form 实例触发提交或重置，按钮 loading 只由真实提交过程驱动；共享 wrapper 不得静默改变分页、滚动、locale 或反馈上下文。
- Modal、message、notification 使用 antd App 上下文实例；Portal 主题、焦点、Esc、关闭回焦和点击穿透必须以真实浏览器结果为准。

## 4. 适用验收

- 只核对当前任务命中的章节和真实源码消费者；不存在的 Modal、Drawer、DatePicker、固定列或响应式场景标记为不适用，不制造页面凑验收。
- 适用场景必须验证行为闭环、状态可观察性、稳定身份、wrapper props、Portal/反馈上下文和响应式边界；构建、路由、console 和其他通用完成门槛遵循 spm-prototype/SKILL.md。
