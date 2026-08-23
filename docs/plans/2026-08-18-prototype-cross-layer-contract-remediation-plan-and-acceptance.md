# Prototype 跨层契约专项修复计划与验收方案

> 日期：2026-08-18  
> 状态：待执行  
> 执行者：其他 AI  
> 目标：修复 Ant Design 6、Tabler 图标、自定义主题、Hash 路由、共享 UI 与真实浏览器验证之间的跨层契约缺口。  
> 与既有计划的关系：本文件是 [Tabler 设计语言 + Ant Design 原型视觉迭代计划](2026-08-17-tabler-antd-visual-iteration-plan-and-acceptance.md) 的专项补充。既有计划继续负责视觉体系；本文件只负责运行时、行为、值、身份、路由、Portal、响应式和规则同步。  
> 文档边界：本文件是仓库维护计划，不是运行时规则。执行完成后，稳定行为必须落入对应 Skill、reference 或模板，不能只停留在本计划中。

## 1. 最终目标

执行完成后，必须同时满足以下结果：

1. 真实可见操作都有可观察后置结果，不再出现“按钮存在但没有行为”“必填星号存在但没有校验”“固定 loading 冒充提交状态”。
2. Hash 路由能区分路径和 query：query 不破坏路由匹配，也不会被静默丢弃；同一路径 query 改变时页面会更新。
3. 表单明确处理 UI 值、业务值、初始化、回填、提交、重置和空值；页面外 ActionBar 能调用真实 Form 提交与重置。
4. route、row、menu、action、field 使用稳定 ID，展示文本不再作为身份兜底。
5. Portal 内容能读取主题变量，Modal、Dropdown、Select、DatePicker 等弹层与 Sider、sticky ActionBar 的层级和交互正确。
6. 共享组件明确哪些 props 使用默认值、合并、覆盖或原样透传，不再静默丢失调用方配置。
7. 响应式断点在视觉规范、antd Sider 和 CSS 中一致。
8. Skill、reference、模板和 Review 使用同一套规则，不保留相互冲突的代码示例或验收描述。
9. 构建、静态检查和真实浏览器验收全部完成；任何未验证项明确报告，不能写成“已通过”。

## 2. 根因与执行原则

本专项按一个统一判断执行：

> 问题根因不是 antd 或 Tabler 单独不成熟，而是混合栈中的隐式契约没有显式定义。

每个修改都必须回答五个问题：

1. **渲染位置**：组件最终在页面容器还是 Portal 中渲染？主题、层级、焦点和键盘行为是否仍有效？
2. **稳定身份**：route、row、action、field 的唯一 ID 是什么？是否错误使用了标题、中文文案或数组下标？
3. **值形状**：UI 值和业务值分别是什么？如何初始化、回填、提交、重置和表达空值？
4. **行为结果**：用户操作后能观察到什么结果？
5. **事实来源**：这条规则的唯一权威文件是什么？哪些消费者必须同步？

发现问题后使用最小修复：优先修既有 Skill、reference、模板和共享组件，不新增统一检查器、检查 JSON、评分器或新的中间回执。

## 3. 事实与待验证项

### 3.1 已确认问题

- FormDemo.jsx 的必填字段没有 name、rules、onFinish，ActionBar 在 Form 外且没有调用 form.submit() / form.resetFields()，提交按钮固定 loading。
- Home.jsx 中“查询”“新建任务”“查看”“编辑”“重置”“保存”等操作没有可观察结果。
- useHashRoute.js 通过丢弃问号后的内容修复了匹配，却没有向页面保留 query。
- prototype-shell.md 仍展示 return hash || '/'，与模板实现不一致。
- prototype-shell.md 示例登记了 /plan/detail/:id，但极简路由只做字符串精确匹配，实际不支持动态路径参数。
- TablerRowActions 使用 it.key || it.label，展示文案同时承担 React key、Menu key 和动作定位。
- TablerDataTable 会重建 scroll、pagination、locale，其中 locale 可能丢失调用方的其他配置。
- prototype-visual-spec.md 一处规定表格默认不固定操作列，状态矩阵另一处仍写“操作列固定”。
- 响应式同时存在视觉规范 576/992、Sider breakpoint=lg 和 CSS 768/390 三套边界。
- 移动端 Sider 使用 z-index: 1001，与 Modal、遮罩和其他 Portal 的层级关系没有经过组合场景验收。

### 3.2 高概率风险，必须通过真实浏览器确认

- 移动端 Sider 展开后打开 Modal，Sider、遮罩或 Modal 互相覆盖。
- Select、Dropdown、DatePicker 弹层被 sticky/fixed 元素遮挡，或读取不到 CSS 变量。
- 静态 Modal.confirm、message、notification 与 ConfigProvider 的主题、locale 或上下文不一致。
- Modal 编辑态关闭后再次打开，残留上一次字段值和校验状态。
- 同一路径只改变 query 时 React 页面不更新。
- Tab、Esc、Enter、关闭后焦点回归和移动端点击穿透未被验证。

高概率风险在验证前不能写成确定缺陷；验证失败后再按实际证据修复。

## 4. 唯一事实源与文件职责

| 主题 | 权威文件 | 消费者 | 规则 |
| --- | --- | --- | --- |
| Prototype 执行顺序、停止条件、完成判据 | skills/spm-prototype/SKILL.md | 生成者 | 只保留流程和指针，不复制组件细节 |
| 行为闭环、值转换、工程写法、浏览器验证 | references/prototype-writing.md | 生成者、Review | 放工程规则；视觉数值引用视觉规范 |
| 表单、表格、Modal、共享组件行为 | references/prototype-component-behavior.md | 生成者、Review、模板 | 每条组件契约只在这里完整定义一次 |
| 路由、菜单、共享 shell | references/prototype-shell.md | 多页面 Prototype | 路由实现示例必须与模板完全一致 |
| Token、断点、层级、状态视觉 | references/prototype-visual-spec.md | theme、CSS、共享 UI | 视觉值唯一来源 |
| 可执行默认行为 | templates/prototype-vite/src/ | 新生成 Prototype | 实现 reference 已确认的规则，不新增业务事实 |
| Review 问题映射 | contracts/prototype-review-checklist.md | spm-prototype-review | 只写触发证据和权威指针，不复制整套规范 |

同一条完整规则不得同时写入多个 reference。非权威文件只保留一句指针和适用条件。

## 5. 修改范围

### 5.1 计划内文件

- skills/spm-prototype/SKILL.md
- skills/spm-prototype-review/SKILL.md
- contracts/prototype-review-checklist.md
- references/prototype-writing.md
- references/prototype-component-behavior.md
- references/prototype-visual-spec.md
- references/prototype-shell.md
- templates/prototype-vite/src/main.jsx
- templates/prototype-vite/src/App.jsx
- templates/prototype-vite/src/shared/useHashRoute.js
- templates/prototype-vite/src/shared/ui/index.jsx
- templates/prototype-vite/src/modules/home/Home.jsx
- templates/prototype-vite/src/modules/demo/FormDemo.jsx
- templates/prototype-vite/src/styles/global.css
- 与以上行为直接相关的 templates/prototype-vite/README.md

### 5.2 条件修改

- templates/prototype-vite/src/theme/tablerTokens.ts、tablerTheme.ts：只有统一断点或层级需要可执行 Token/antd theme 映射时修改。
- templates/prototype-vite/package.json、package-lock.json：本专项原则上不增加依赖；只有现有依赖无法完成要求且证据充分时修改。
- 现有 Python 脚本：只有确定性检查本身出现可复现误报或漏检时修改。语义问题继续由 Skill 自检和真实浏览器验收承担。

### 5.3 不在本专项修改

- skills/spm-prd/SKILL.md：不写入 antd、Tabler、Portal、路由或 Playwright 细节。PRD 只保持“未知事实不静默补全、Design 是事实基线”的既有边界。
- Design、PRD 和任何真实项目业务事实。
- dist/、node_modules/、带哈希的构建产物。
- .playwright-cli/、test-fixture/design-set/ 等已有未跟踪内容；除非能证明是本次执行者新建且安全可删，否则保留。
- 与本专项无关的格式化、重构、死代码清理。

## 6. 执行顺序

严格按以下阶段执行。每个阶段完成验收后再进入下一阶段。

### 阶段 0：保护基线

#### 检查

1. 运行 git status --short，记录执行前的已修改和未跟踪文件。
2. 对计划内文件运行 git diff -- <files>，识别已有用户修改。
3. 在 templates/prototype-vite/ 运行 npm ci、npm run build，记录当前结果。
4. 启动当前构建预览，打开 #/、#/demo-form、#/demo-form?mode=edit&id=1，记录 console 和实际行为；此时只记录，不修复。

#### 完成条件

- 执行前工作区状态已记录。
- 已有用户修改被视为基线，没有使用 reset、checkout、覆盖写入或批量格式化清除。
- 当前构建和三条路由的基线结果可复查。

### 阶段 1：收敛规则事实源

#### 1.1 路由契约

在 prototype-shell.md 完整定义并只在 prototype-writing.md 保留摘要指针：

- 极简路由使用精确 path + query，不声称支持 :id 动态路径。
- 业务对象 ID 使用 query，例如 #/plan/detail?id=123。
- 路由解析结果至少提供 { path, query, route }；实现可以额外返回原始 search。
- query 不参与 route path 匹配，但页面必须能读取。
- 同一路径 query 改变必须触发页面更新。
- navigate() 接受包含 query 的 Hash 相对地址，不重复添加 #。

删除或改写 /plan/detail/:id 这种当前实现无法支持的示例，不为一个模板示例引入完整路由库。

#### 1.2 行为闭环与表单最小契约

在 prototype-writing.md 定义通用行为闭环，在 prototype-component-behavior.md 定义 Form/Modal 的组件契约：

- 真实按钮至少产生打开/关闭层、校验、状态变化、列表变化、路由变化或反馈之一。
- 视觉样张不使用可点击按钮伪装真实操作；无行为的操作删除或改为明确的非交互展示。
- 每个可编辑字段必须有稳定 name；必填、格式和范围通过 rules 表达，不能只写 required 外观。
- 页面外 ActionBar 通过 Form 实例调用 form.submit() / form.resetFields()。
- loading 只由真实提交过程驱动；提交完成或失败后必须结束。
- DatePicker/RangePicker、Select、Upload、InputNumber 等非原始值控件明确 UI 值、业务值、初始化、回填、提交和空值。
- Modal 新增、编辑、取消、关闭、重新打开之间必须清理或正确回填值与校验状态。

#### 1.3 身份与共享组件契约

在 prototype-component-behavior.md 定义：

- route、row、menu、action、field 使用稳定唯一 ID。
- TablerRowActions.items[].key 为必填稳定动作 ID，不以 label 兜底。
- Table 明确传入稳定 rowKey，不使用数组下标。
- wrapper 对每个二次处理的 prop 说明默认、合并、覆盖或透传规则。
- 未知状态必须可见地区分为未知/异常，不能静默降级成普通弱状态。
- 图标按钮必须有稳定的 aria-label；可见文字可以变化，但不能承担动作身份。

#### 1.4 Portal、反馈和叠层契约

在组件行为规范和视觉规范之间分工：

- 行为规范定义 Portal 组件需要验证主题、焦点、Esc、关闭后焦点回归和点击穿透。
- 视觉规范定义唯一 z-index 层级关系；具体数值只在视觉规范/Token 出现。
- 全局 CSS 变量挂 document.documentElement。
- 上下文相关的 Modal/message/notification 使用 antd App 上下文实例；不在模板中混用静态 API 和上下文 API。
- Sider、Sider mask、sticky ActionBar、Dropdown、Modal mask、Modal dialog 的上下关系必须通过组合场景验证。

#### 1.5 响应式契约

统一采用视觉规范中的 antd 断点：

- 移动：<576
- 平板：576–991
- 桌面：≥992
- 宽屏：≥1200

CSS 使用与这些区间一致的边界，不继续使用 768px 表达 Sider 的 lg 行为。390px 只能保留为额外窄屏优化，不能替代 <576 的移动规则。

#### 1.6 Review 入口

- spm-prototype/SKILL.md 要求逐项执行组件行为完整清单和真实浏览器代表性交互，不复制单点实现细节。
- spm-prototype-review/SKILL.md 改为“逐项审查第 10 节完整清单”，不要继续列一个会过期的部分子集。
- prototype-review-checklist.md 增加一个“跨层运行时契约”映射项，覆盖行为闭环、表单、query、稳定身份、Portal 和响应式；权威规则仍指向 reference。

#### 阶段完成条件

- 每条规则都能定位到唯一权威文件。
- prototype-shell.md 的路由代码示例与计划采用的模板接口一致。
- prototype-visual-spec.md 不再同时出现“操作列默认不固定”和“操作列固定”的冲突。
- SKILL 和 Review checklist 只保留流程/映射，不复制完整规则。
- 未新增检查器、检查 JSON 或新的运行时规则文件。

### 阶段 2：修复模板运行时契约

#### 2.1 Hash 路由

修改 useHashRoute.js：

1. 保存完整 Hash 地址，而不是只保存 path。
2. 分离 path 与 query；query 使用浏览器原生 URLSearchParams 或等价无依赖实现。
3. 返回 { path, query, route }。
4. hashchange 时即使 path 未变、query 改变，也触发消费者更新。
5. 未知 path 进入 NotFound；合法 path 带 query 不进入 NotFound。

同步修改 App.jsx 和使用路由参数的页面，不让 query 进入 Menu selectedKeys。

#### 2.2 FormDemo 行为闭环

把 FormDemo.jsx 从视觉样张改为最小可运行示例：

- 使用 Form.useForm()。
- 可编辑字段提供稳定 name、rules 和 initialValues。
- 根据 query 中的 mode=create|edit|view 表达新增、编辑、只读；id 只作模板示例身份，不引入业务事实。
- 页面外 TablerActionBar 调用 form.resetFields()、返回/取消和 form.submit()。
- onFinish 和失败路径可观察；loading 由提交状态驱动，不固定为 true。
- view 模式不显示伪提交操作；只读状态通过组件属性表达。
- 使用 Select 的真实值和表单回填，确保浏览器可以真实点击并选择。

#### 2.3 Home 操作闭环

按最小方式处理当前死操作：

- 删除没有查询条件却存在的“查询”按钮。
- “新建任务”导航到 #/demo-form?mode=create。
- “查看”“编辑”分别导航到带 mode 和稳定 id 的 FormDemo 地址。
- 行操作改用 TablerRowActions，每项显式提供稳定 key。
- 如果需要覆盖“更多”分支，可增加一个有真实结果的示例动作；动作总数超过 3 时必须进入 Dropdown，不得增加无行为按钮只为凑数。
- 删除不属于 Dashboard 的底部“重置/保存”ActionBar，或赋予与页面真实状态一致的行为；优先删除。
- 删除操作使用上下文 Modal confirm；取消不改变列表，确认后列表变化并给出反馈。

模板演示行为不得新增到任何真实项目 Design 中；它只证明组件契约可运行。

#### 2.4 共享 UI

修改 shared/ui/index.jsx：

- TablerRowActions 要求 key，React key、Menu key 和回调定位都只使用该 key。
- TablerDataTable：调用方未传 scroll 时才使用默认横滚；已传时按已定义的合并/透传规则处理。
- pagination 使用默认值与调用方配置合并，false 原样保留。
- locale 先保留调用方配置；设置 emptyTitle 时只覆盖 locale.emptyText。
- TablerStatusTag 遇到未知状态时显示明确未知/异常表达，不伪装成正常弱状态。
- TablerEmptyState 使用合法语义结构，不使用 span 包裹块级 div。
- 只清理本次修改导致的未使用 import，不顺手重构其他组件。

#### 2.5 antd 上下文与 Portal

修改 main.jsx，在 ConfigProvider 内加入 antd App 上下文容器；本地壳层组件保持清晰命名，避免与 antd App 混淆。

需要反馈或确认的组件通过 App.useApp() 获取 modal/message/notification 实例。模板继续把 CSS 变量写入 document.documentElement，不要回退到 #root。

#### 2.6 响应式和叠层

修改 global.css、必要时修改 App.jsx：

- Sider 的固定定位适用范围与 <992 一致。
- 内容边距在 <576、576–991、≥992 与视觉规范一致。
- Header 用户名隐藏规则至少覆盖 <576；390px 只用于额外窄屏优化。
- 移动/平板 Sider 展开时提供可点击遮罩，点击遮罩或选择菜单后关闭 Sider，页面内容不点击穿透。
- z-index 取自唯一层级规则；不得通过不断增加任意大数解决遮挡。
- sticky ActionBar 在窄屏不遮挡最后一个字段，按钮可达且不拆字；只有真实验证失败时再增加 safe-area 或额外底部空间。

#### 阶段完成条件

- Home 和 FormDemo 的所有可见按钮都有行为或已删除。
- 路由 query、Form、RowActions、确认反馈、Portal、响应式至少各有一个模板场景可验收。
- 模板没有固定 loading、label key 兜底、query 丢弃和重复断点事实。
- 修改范围没有扩展到 Design/PRD 或无关脚本。

### 阶段 3：规则与消费者同步

逐项对照以下同步矩阵：

| 改动 | 必须同步 |
| --- | --- |
| useHashRoute 接口 | prototype-shell.md、prototype-writing.md 指针、App.jsx、示例页面 |
| Form/ActionBar 契约 | prototype-component-behavior.md、prototype-writing.md、FormDemo.jsx |
| RowActions key 与 Table prop 语义 | prototype-component-behavior.md、shared/ui/index.jsx、Home 调用方 |
| Portal/反馈上下文 | prototype-component-behavior.md、main.jsx、使用确认/反馈的页面 |
| 断点和层级 | prototype-visual-spec.md、Token/theme（如适用）、global.css、App.jsx |
| 最终验收流程 | spm-prototype/SKILL.md、spm-prototype-review/SKILL.md、prototype-review-checklist.md |

#### 完成条件

- 任意规则只需修改一个权威位置即可改变行为。
- 所有代码示例都能在当前模板中找到对应实现，不再保留过时缓存。
- rg 搜索不到已废弃的路由实现、动态路径示例和冲突断点描述。

## 7. 验收方案

### 7.1 确定性检查

在仓库根目录执行：

~~~powershell
python scripts/python/test-prototype-source-check.py
python scripts/python/test-resource-integrity.py
python scripts/python/test-shitpm-regression.py
git -c core.whitespace=cr-at-eol diff --check
~~~

在 templates/prototype-vite/ 执行：

~~~powershell
npm ci
npm run build
npm run preview
~~~

规则：

- 静态脚本只证明确定性结构，不证明业务语义或浏览器行为。
- 不在没有正式 Design/Prototype 项目的仓库根目录强行运行 prototype-consistency-check.py 并把退出码当质量证明。
- 如果在隔离真实项目或 fixture 中验证，再运行对应 prototype-source-check.py 和 prototype-consistency-check.py，并单独记录其适用范围。

### 7.2 路由与行为矩阵

构建预览中逐项验收：

| 场景 | 操作 | 通过条件 |
| --- | --- | --- |
| 首页 | 打开 #/ | 页面正常；console 无 error；可见操作都有结果 |
| 默认表单 | 打开 #/demo-form | 使用明确默认 mode；不进入 NotFound |
| 新增表单 | 打开 #/demo-form?mode=create | query 可读；字段初始状态正确 |
| 编辑表单 | 打开 #/demo-form?mode=edit&id=1 | route 匹配；id/mode 可读；正确回填 |
| 查看表单 | 打开 #/demo-form?mode=view&id=1 | 字段只读；不出现伪提交按钮 |
| 同路由 query 切换 | edit id=1 切到 edit id=2 或 view id=1 | 页面立即更新，不需 reload |
| 未知路由 | 打开 #/missing?x=1 | 进入 NotFound；console 无 error |
| 必填校验 | 清空必填字段并提交 | 显示内联错误；不显示成功结果 |
| 重置 | 修改字段后点击重置 | 回到定义的初始值；错误状态清理 |
| 提交 | 填写有效值并提交 | loading 只在处理时出现；完成后结束并反馈 |
| Select | 使用真实点击打开和选择 | 下拉可见、可选、无 Portal 样式错误 |
| 删除取消 | 首页删除后取消确认 | 列表不变 |
| 删除确认 | 首页删除并确认 | 对应稳定 ID 行消失；出现反馈 |
| 更多操作 | 打开行操作 Dropdown（若模板有 >3 项） | 按稳定 key 触发正确动作，不依赖文案 |

### 7.3 视口与层级矩阵

至少检查以下宽度：

- 390px：典型手机截图；
- 575px 与 576px：移动/平板边界；
- 991px 与 992px：Sider lg 边界；
- 1440px：桌面截图。

组合场景：

1. <992 展开 Sider，确认遮罩出现、页面不可点击穿透、点击菜单或遮罩后关闭。
2. Sider 展开状态下打开 Modal；Modal mask/dialog 位于正确层级，Sider 不盖住 Modal。
3. 打开 Select/Dropdown/DatePicker；弹层不被 Header、Sider、Table fixed 列或 ActionBar 遮挡。
4. 表单滚动到底部；ActionBar 不遮挡最后字段，按钮可点击。
5. 有 fixed 列场景时横向滚动到中段；普通表头文字不穿透 fixed 表头。

### 7.4 键盘与焦点

至少完成：

- Tab 能进入当前弹层的主要控件；
- Esc 按组件约定关闭可关闭弹层；
- Enter 在表单中触发真实提交和校验，不绕过 Form；
- Modal 关闭后焦点回到触发按钮或合理位置；
- 图标按钮和“更多操作”有可识别名称；
- console 没有缺失 key、无效 DOM 嵌套或未导入符号造成的错误。

### 7.5 规则一致性搜索

执行者使用 rg 检查以下内容，并根据最终实现调整搜索式：

~~~powershell
rg -n "return hash \\|\\| '/'|/plan/detail/:id|it\\.key \\|\\| it\\.label|max-width: 768px|操作列固定" references templates/prototype-vite skills contracts
rg -n "Form\\.Item.*required|loading[^=]*$|Modal\\.confirm|message\\.|notification\\." templates/prototype-vite/src
~~~

搜索命中不是自动失败；逐项确认它是权威规则、合法实现还是仍待修复的旧缓存。

## 8. 最终放行条件

以下项目全部满足才可报告“完成”：

- [ ] 阶段 0 的原始工作区改动仍被保留。
- [ ] 规则唯一事实源和同步矩阵全部落实。
- [ ] Hash path/query 接口在 reference 与模板中一致。
- [ ] 不再声称极简路由支持未实现的 :id 动态路径。
- [ ] FormDemo 的字段、校验、提交、重置、只读和 loading 均为真实行为。
- [ ] Home 不存在死操作；新增、查看、编辑、删除均有结果或已删除。
- [ ] RowActions 不使用 label 作为 key；Table 使用稳定 rowKey。
- [ ] DataTable 不静默丢失调用方 locale/scroll/pagination 配置。
- [ ] 未知状态不会伪装成正常弱状态。
- [ ] CSS 变量对 Portal 可见；反馈 API 使用统一上下文方式。
- [ ] 576/992 响应式边界在规范、Sider 和 CSS 中一致。
- [ ] Sider、Modal、Dropdown、Select、ActionBar 组合场景通过。
- [ ] 构建、确定性测试、CRLF-aware diff check 全部通过。
- [ ] 默认页、全部注册路由、query 场景和代表性交互在构建预览中通过，console 无 error。
- [ ] 390px 与 1440px 截图已人工检查；575/576/991/992 边界已观察。
- [ ] 所有未验证或失败项都在最终交付中明确列出，没有包装成通过。

## 9. 执行失败处理

- 已有用户修改与本计划冲突时，保留用户修改，说明冲突位置和两种行为差异；不要 reset 或覆盖。
- antd 内部 DOM 或类名不确定时，以锁定版本 antd ^6.6.0 的真实浏览器渲染为准，优先使用公开 props、theme token、自定义 className 或 data-*；不维护永久内部类名清单。
- 某项规则无法确定时，先判断是否会改变产品事实。会改变 Design 事实时停止并询问用户；仅影响模板工程实现时选择最小、可验证方案并记录理由。
- 浏览器自动化环境不可用时，完成其余工作并把真实浏览器矩阵标为未验证；不得仅凭 build 或静态检查放行。
- 测试失败时保留原始错误，先定位本次修改是否导致；不通过修改无关测试、批量格式化或删除既有资产消除失败。

## 10. 执行者最终交付格式

最终回复按以下顺序输出，不新增机器回执文件：

1. **结论**：完成 / 部分完成 / 阻塞。
2. **修改范围**：列出实际修改文件及每个文件的职责变化。
3. **关键决策**：路由 query、表单、稳定 ID、wrapper prop、Portal、断点分别采用什么契约。
4. **验证证据**：命令及结果、浏览器路由矩阵、交互矩阵、视口和截图位置。
5. **保留问题**：未验证、失败、需要产品确认或需要上游同步的项目。
6. **工作区边界**：说明哪些原有修改和未跟踪文件被保留；未执行 commit/push，除非用户另行明确授权。

不得只写“build 通过”“已按 Skill 修改”或“所有测试通过”。结论必须能追溯到本文件的放行条件。
