---
name: spm-prototype
description: "Prototype 阶段——根据已确认的 Design 生成可运行、可讨论的源码工程原型。用于用户要求生成、修改或查看原型时；直接读取 Design，不依赖 PRD；必须使用标准 Vite + React 18 + Ant Design 6 源码工程，src 是唯一编辑源、dist 是可重建构建产物、用户通过 原型工具.bat 完成本地预览/构建/条件式上传；缺少源码工程时停止。"
---

## 路径与资源

从系统 prompt 读取 `$BUNDLE`。bundle 资源使用 `$BUNDLE/templates/`、`$BUNDLE/references/` 和 `$BUNDLE/scripts/python/`；项目产物使用当前项目根目录的 `output/` 和 `.workflow/`。

流程开始时输出模型建议：页面少且行为明确、主要做既定表达与实现时可用轻量或代码模型；涉及跨页面任务路径、复杂交互或高影响表达时使用深度推理模型；无法判断时使用深度推理模型。

## 职责与准入

- Prototype 是 Design 的直接下游，不依赖 PRD、Design metadata、`page-fields`、分页流水线或逐页字段计数。
- `output/design/design.md` 必须存在、可读且通过 Design confirmation gate；失败时停止，不生成或覆盖 Prototype。
- 技术契约固定为**标准 Vite + React 18 + Ant Design 6 源码工程**：
  1. `output/prototype/src/` 是唯一业务编辑源；`output/prototype/dist/` 是构建产物，只由 `npm run build` 生成，可删除重建，不是产品事实源，AI 不直接编辑。
  2. 本地即时预览使用开发服务器（`npm run dev`）；本地交付预览和 Cloudflare 部署都使用同一份构建产物 `dist/`（`npm run preview`）。
  3. 依赖统一由 `package.json` 和 `package-lock.json` 定义，安装用 `npm ci`；不引入浏览器端 Babel、本地 UMD lib、外部 CDN 或第二套构建链。
  4. 面向用户只提供一个 `output/prototype/原型工具.bat`：双击后通过中文菜单完成本地预览、构建预览、重建、依赖修复和条件式 Cloudflare 上传；不得要求用户打开 PowerShell 或手动输入 npm 命令。
  5. `原型工具.bat` 只调用 `package.json` 中的标准 scripts（dev/build/preview），不在 BAT 中另写一套构建逻辑。
- 原型只表达 Design，不重新定义业务规则、权限、状态、跨系统责任、模块边界或其他高影响行为。

确认检查：

```text
python $BUNDLE/scripts/python/design-confirmation.py --project-root . check
```

退出码非 0 或 Design 未确认/哈希不一致时停止，用自然语言询问用户是否确认当前 Design；仅在用户明确确认后，由你运行 `confirm` 记录哈希，再继续。不得在用户未明确确认前运行 `confirm`，也不要求用户输入命令行。不要求 PRD、metadata 或 Prototype Review 存在。

## 输入资源

1. `output/design/design.md`：唯一产品事实源，必须直接读取。
2. `$BUNDLE/templates/prototype-vite/`：标准 Vite 源码工程模板（应用壳、Hash 路由、`原型工具.bat`、README、标准 npm scripts）。
3. `$BUNDLE/references/prototype-writing.md`：通用后台基座、Ant Design 6、页面组织和视觉细则。多页面 shell、共享布局、导航激活、路由或空白页问题才读取 `$BUNDLE/references/prototype-shell.md`。
4. `$BUNDLE/templates/prototype-feedback-classification.md`：有反馈时的归类格式。
5. 如存在 `output/prototype/prototype-feedback.md`，读取后先归类；如 PRD 存在，只能作为辅助参考，与 Design 冲突时以 Design 为准。
6. 不读取 `.workflow/metadata/design/` 或 `output/design/decision-notes.md` 作为产品事实输入。

## 首次生成流程

1. 检查 Design confirmation 和 `templates/prototype-vite/` 模板；缺失时报告具体路径并停止。
2. 读取 Design 的模块、页面、字段、状态、权限、流程、操作限制和异常要求。
3. 正式写入前完成 Design → Prototype 语义对照：列出必须表达的页面、字段、状态、角色权限、主要路径和关键反馈；显式标出 Design 的“待确认”项，不静默拍板。
4. 从 `$BUNDLE/templates/prototype-vite/` 复制标准工程到 `output/prototype/`。若 `output/prototype/` 已存在旧静态原型（HTML + compiled.js 形态），先与用户确认迁移方案，不直接覆盖；迁移只允许把旧产物作为一次性参考，不得把 compiled.js 当作长期源码。
5. 生成 `原型工具.bat` 和面向用户的首屏说明（模板已带，按项目名微调即可），README 首屏只写“请双击 `原型工具.bat` 并选择操作”。
6. 读取并执行 `$BUNDLE/references/prototype-writing.md` 的通用基座、Ant Design 6、页面组织和视觉细则；多页面或 shell 相关任务再读取 `$BUNDLE/references/prototype-shell.md`。按 Design 在 `src/modules/<模块>/` 创建业务页面组件并注册到 `src/routes.jsx`；共享壳层、角色切换、异常页放在 `src/shared/`。确认版 Design 是唯一产品事实源，PRD 仅可选辅助，冲突时以 Design 为准。
7. 允许编辑 `src/`、`index.html`、`package.json`、`vite.config.js`、`public/`、`README.md`；禁止直接编辑 `dist/`、`node_modules/` 和 Vite 生成的带哈希资源文件。
8. 依赖与构建：运行 `npm ci`，再运行 `npm run build`；构建失败先修复源码，不部署旧 dist 冒充新版本。
9. 验证 `原型工具.bat` 的三个本地选项（“启动本地即时预览”“构建并预览发布版本”“重新构建部署包”）实际可用：双击能打开中文菜单并进入选项（选项只调用 package.json 标准 scripts，读文件确认映射即可）；不做 dev 浏览器抽查、不逐路由验证。
10. 生成后检查（浏览器验证只跑一遍构建预览，不再 dev/preview 双份全路由）：
   - **浏览器渲染**：构建预览（`npm run preview` 或静态服务 dist）逐一打开默认页与每个注册路由，均不得白屏（`#root` 非空）、console 不得报错；等待策略用 `domcontentloaded` + 短等待（≤2s/页）查 `#root` 与 console，禁止无脑 `networkidle` 长等（vite 下会空等 5-30s/页，路由多时整体拖到数十分钟）；
   - **交互回显分级验证（浏览器只走一条代表性主链路）**：完整交互回显（操作后状态/数据回写、跨页/跨角色联动）只挑一条代表性主链路在浏览器内完整走通（如 修正→重算→确认应收→确认缴纳→返回列表验证回显）；其余页面、字段和操作的联动回显不逐条开浏览器点验，改为源码逻辑核对（store 重算函数、状态机/权限分支、Design 字段与页面映射）并靠确定性检查覆盖；只有“全部路由白屏 + console 无报错”仍按上一条逐一检查。
   - **验证不依赖截图**：文字模型无视觉能力，禁止以截图作为检查证据或“验证过程存档”；渲染、白屏、console 与回显检查一律用 DOM/页面文本/console 文本断言（`#root` 非空、关键文本与状态可见）；仅当用户明确索要截图时才拍摄，不为检查拍摄。
   - **空/异常/加载态可观察**：每个列表/看板页空 dataSource 时显示 Table 内置"暂无数据"空态（不得移除空态表达）；关键页必须能表达"加载失败点击重试"与无权限拦截，不允许只展示满数据 mock 而不交代异常态；
   - **多角色页面必须有角色视角**：Design 页面清单"适用角色"多于一个角色的项目，角色切换统一放壳层 Header（Select，角色用全称如"被审单位对接人"），页内不放"演示角色切换"；角色不满足的操作不渲染；不得静默只按单一角色渲染；
   - **配置管理页不得用占位**：新增/编辑/停用/启用等操作必须用真实 `Modal` + `Form`（字段按 Design 对应页面章节），二次确认用 `Modal.confirm`，禁止 `message.info('…（示意）')` 占位；
   - **状态驱动操作必须可见禁用**：Design 状态机要求的操作可用条件必须用 antd `disabled` 属性（或等价置灰）表达，不得只写文字说明或全部可点；**与角色规则区分：角色不满足 → 不渲染；状态机不允许 → 置灰禁用**；关键权限/状态/限制/主路径/异常反馈必须有表达。
   - **超高保真，禁止页面内解释性标注**：原型页面内不得出现“入口：…去向：…”、“（只读）/（必填）/（选填）”、操作说明（Design）、勾选规则（Design）等解释性文本；字段的必填/只读/选填状态通过 UI 本身表达（必填项用 `Form.Item required` 红 asterisk、只读/系统判定用 `disabled`、选填无星）。所有评审注释统一走 `prototypemark` 流程，不在 base 原型页面里写注解。
11. 运行：

```text
python $BUNDLE/scripts/python/prototype-source-check.py --project-root .
python $BUNDLE/scripts/python/prototype-consistency-check.py --project-root .
```

确定性检查或浏览器检查失败时先修复并重新验证，不交付未验证的原型。
design-set 格式项目（无 `output/design/design.md`）由脚本直接支持：从 `output/design/设计集清单.json` 的模块设计文件提取页面/字段/操作/状态，执行与经典 design.md 同一套对账，不再报 "design.md 不存在"。
12. 更新 `.workflow/status.json`：`current_stage=prototype`，`artifacts.prototype=output/prototype/index.html`；不使用 `current_stage=done` 表达线性完成。

## 修改流程

1. 修改开始前先验证源码工程完整：`output/prototype/package.json` 存在、`src/` 存在并包含入口、`npm run build` 已定义、当前业务页面能在 `src/` 中定位。如果只有 `dist/`、静态 compiled.js 或构建后的 HTML：停止，报告“Prototype 源码工程缺失”，提出源码恢复或一次性迁移方案；不修改 dist、不反编译构建资源、不用字符串锚点补丁生成物。
2. 从 `src/routes.jsx` 和 `src/modules/` 定位业务页面，只修改 `src/`。
3. 运行开发预览核对修改效果，然后 `npm run build` 重新构建。
4. 用构建预览复验（只验证本次改动的页面 + 默认页，不再全路由双份），确认与开发预览一致；复验 `原型工具.bat` 的相关菜单选项。
   - 交互回显只重验本次改动涉及的链路（浏览器一遍即可）；未改动页面的回显逻辑改由源码核对与确定性检查覆盖，不逐条重开浏览器。
5. 重新运行 `prototype-source-check.py` 与 `prototype-consistency-check.py`，通过后再交付。
   - design-set 项目同上处理（consistency-check 已支持设计集清单，正常参与检查）。

## 反馈处理

读取反馈后必须先按 `$BUNDLE/templates/prototype-feedback-classification.md` 输出归类，再开始修改。表现问题只改 Prototype；语义问题不得静默改动字段、状态、权限、流程或模块边界，必须停止并转入 Design/Fix；表现问题与语义问题不能混改。

- **表现问题**：布局、视觉层级、间距、颜色、字体、响应式或组件呈现问题；只改 Prototype，不改变 Design 事实。
- **语义问题**：缺少 Design 要求，或与 Design 的对象、字段、状态、权限、交互、异常和责任边界冲突；先回写 Design，使旧 confirmation 失效，用户重新确认后再按影响范围生成下游。
- 同时包含两类时拆成独立处理项；空类别保留并写“无”。

## 失败与停止

- 模板、写法参考或 Design 缺失：报告具体路径，不凭记忆生成完整产物。
- Design confirmation 失败：停止，不覆盖原型。
- 只有 dist 没有 src、`package.json` 或构建脚本缺失、业务页面只能在构建产物中找到、构建失败、或需要通过直接修改 dist 才能完成用户要求：停止，报告源码工程缺失或构建错误，不修改 dist。
- 页面渲染空白、console 报错、确定性检查失败：先修复并重新验证；必要时回滚到上一个可工作版本。
- 发现幻觉字段、页面、状态、权限或 Design 未授权高影响行为：删除或不写入，并报告；不静默拍板。
- 用户反馈无法归类：停止澄清，不直接修改。
- 不依赖 PRD 存在，不依赖 metadata，不使用外部 CDN、Vue/daisyUI/`el-` 组件、浏览器端 Babel 或临时项目级编译脚本来替代标准工程。

## 产物

- `output/prototype/src/`：唯一业务编辑源（`main.jsx`、`App.jsx`、`routes.jsx`、`modules/`、`shared/`、`styles/`）。
- `output/prototype/原型工具.bat`：用户唯一操作入口（中文菜单：本地即时预览、构建并预览发布版本、重新构建部署包、条件式上传 Cloudflare、修复依赖并重新构建）。
- `output/prototype/index.html`、`package.json`、`package-lock.json`、`vite.config.js`、`README.md`：源码工程组成。
- `output/prototype/dist/`：可删除、可重建的构建产物（Cloudflare 部署目录）。
- `output/prototype/prototype-feedback.md`：可选反馈记录。
- `.workflow/status.json`：导航状态和产物路径。
