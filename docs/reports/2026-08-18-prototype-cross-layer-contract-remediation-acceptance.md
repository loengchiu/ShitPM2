# Prototype 跨层契约专项修复验收报告

> 日期：2026-08-18
> 验收对象：[2026-08-18-prototype-cross-layer-contract-remediation-plan-and-acceptance.md](../plans/2026-08-18-prototype-cross-layer-contract-remediation-plan-and-acceptance.md)
> 验收方式：git 工作树全量核对 + 源码逐文件通读 + 三套确定性脚本重跑 + 构建复验 + Playwright 证据核查 + 规则一致性全文搜索
> 基线：HEAD `00f48e4`（V2 分支），20 个 Modified + 3 个未跟踪，未 commit（无授权不提交，符合规则）

## 1. 结论

**核心契约修复完成且质量合格，放行条件 14/16 达标，2 项证据不足。** 计划 §3.1 列的全部"已确认问题"在源码与文档侧均已修复，且修复方式遵循 AGENTS.md 精简原则（未新增任何检查器/检查 JSON/门禁/回执）。工作树中计划范围外的 3 个改动（package.json / 原型工具.bat / draft 文档）经 mtime 核实**均为专项执行前已存在的用户基线**（08:24/08:25 端口修复、09:47 文档损坏），执行者只动了计划 §5.1 内的文件——**无超范围修改**。但工作树存在 **1 个 P1 基线文档损坏**（提交前必须还原）与 **2 个 P2 验证证据缺口**（详见 §3）。

## 2. 放行条件逐项核对（对照计划 §8）

| # | 放行条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | 阶段 0 原始工作区改动保留 | ✅ | 无 reset/checkout 痕迹；全部改动为增量 diff |
| 2 | 规则唯一事实源和同步矩阵落实 | ✅ | visual-spec(断点/z-index/操作列) / shell(路由) / behavior(§9.1) / writing / SKILL / review-checklist(新增第 19 项) 六处互相一致 |
| 3 | Hash path/query 接口 reference 与模板一致 | ✅ | `prototype-shell.md` 路由示例与 `useHashRoute.js` 实现逐行一致（readLocation/URLSearchParams/navigate 不重复 #） |
| 4 | 不再声称 :id 动态路径 | ✅ | `references/templates/skills/contracts` 全文 grep 零命中 `/plan/detail/:id`、`return hash \|\| '/'`、`768px`、`操作列固定`（命中仅在计划文档自身的问题清单引用） |
| 5 | FormDemo 字段/校验/提交/重置/只读/loading 真实 | ✅ | `Form.useForm()`、稳定 name+rules、query 驱动 create/edit/view、页外 ActionBar 调 `submit()/resetFields()`、loading 由提交态驱动、view 只读无伪提交 |
| 6 | Home 无死操作 | ✅ | "查询/重置/保存"已删；新建→`?mode=create`、查看/编辑→带 id、删除→`modal.confirm`（App.useApp 上下文）确认后删行+反馈 |
| 7 | RowActions 不用 label 作 key、Table 稳定 rowKey | ✅ | `TablerRowActions` menu/React key/回调全用 `it.key`；Home 显式 `rowKey="id"` |
| 8 | DataTable 不静默丢失 locale/scroll/pagination | ✅ | scroll 仅 undefined 时给默认、pagination false 原样保留否则合并、locale 先保调用方只覆盖 emptyText |
| 9 | 未知状态不伪装 | ✅ | `TablerStatusTag` 未知→error 档 + "未知状态"，不落 weak |
| 10 | CSS 变量 Portal 可见、反馈统一上下文 | ✅ | `document.documentElement` 挂载 + `AntdApp` 容器 + `App.useApp()` |
| 11 | 576/992 响应式边界一致 | ✅ | token `breakpoints`、CSS `max-width:991/575/390`、visual-spec 三处同源；768px 清零 |
| 12 | Sider/Modal/Dropdown/Select/ActionBar 组合 | ✅ | `390-modal-sider.png` 截图 + Select 展开/Modal confirm 的 aria snapshot |
| 13 | 构建、确定性测试、CRLF diff check | ✅ | build 2.75s 通过；source-check 8 用例 / regression 3 用例 / resource-integrity 全绿；diff check 仅被破坏的 draft 文档报 whitespace |
| 14 | 路由/query/代表性交互 console 无 error | ✅ | 首页/404/表单/编辑/查看/Select/Modal 均有 snapshot；console log 仅 DevTools 提示 |
| 15 | 390/1440 截图人工检查；575/576/991/992 已观察 | ⚠️ | 390、1440 有截图（各 1-2 张）；**575/576/991/992 边界无截图、yml 无 viewport 记录，无法独立复核** |
| 16 | 未验证项明确列出 | ⚠️ | **执行者未留下最终交付说明**（§10 格式要求的交付回复不可见），证据缺口只能由验收方从工作树推断 |

## 3. 发现的问题

### P1-1：`docs/plans/2026-08-17-tabler-components-spec-draft.md` 被工具误处理损坏（基线，非本专项引入）

- **现象**：该文件不在计划 §5.1/§5.2 修改范围。14 处内容被编码成 `![svg](data:image/svg+xml;base64,...)` 形式，其中第 14 行的超长 base64 把"图标/滚动条/bg-*-lt 说明 + §1.1 页面骨架 DOM 结构"整段吞掉；另有 13 处 `<svg>` 图标被转成 base64 data URI（base64 占全文 9.4%）。diff check 在 3、4、14-21 行报 trailing whitespace。
- **时间线**：mtime **09:47**，早于专项执行窗口（12:23 起，`.playwright-cli/` 最早证据）；属转换类工具（markitdown 类）处理文档时的误操作，与本专项执行者无关，执行者正确保留了该基线（符合阶段 0"已有用户修改视为基线，不 reset 不覆盖"）。
- **影响**：该文档是"Tabler 58 页组件规范草稿"（用户明确要求抽取的资产，状态"待用户评审"），内容损坏影响后续评审。若随专项一起提交，损坏将入库。
- **处置建议**：提交前 `git checkout -- docs/plans/2026-08-17-tabler-components-spec-draft.md` 还原该文件（不参与本专项）；若确实需要 svg→data URI 转换，另行单独提交并说明用途。同时确认 09:47 是哪个会话/工具所为，避免复发。

### P2-1：浏览器验收证据缺口（非实现缺陷）

- 575/576/991/992 边界宽度：无截图、无 viewport 记录，无法独立复核"边界已观察"。
- 键盘/焦点（Tab/Esc/Enter/关闭后焦点回归）：无证据。
- 同路由 query 切换（edit id=1 → id=2 页面立即更新）：无直接证据。
- Select"选择选项后"、删除"确认后列表变化"：仅有弹层打开证据，无后续状态 snapshot。
- 验收主要在 dev server（127.0.0.1:5173）进行，计划 §7.2 要求"构建预览中"逐项验收，构建产物预览未覆盖。
- **判定**：从代码静态核验看这些行为实现正确（useHashRoute query 变化必触发 setLocation；FormDemo useEffect 依赖 [form, initialValues]；modal.confirm onOk 删行），属"证据不足"而非"实现缺陷"；但按计划 §9"不得仅凭 build 或静态检查放行"，这些项应标记为**未独立验证**。

### P2-2：`.playwright-cli/` 无验收脚本，过程不可复现

- 只有 26 个 aria snapshot + 3 截图 + 1 console log，无 spec 脚本。计划 §7.3/7.4 的视口/键盘矩阵无法从证据还原具体执行步骤。该目录属计划 §5.3 既定的"已有未跟踪内容保留"范围，不作为本专项缺陷，但影响验收可追溯性。

### 基线确认（非问题，专项范围外改动的归因澄清）

- `templates/prototype-vite/package.json`（mtime 08:24）与 `原型工具.bat`（08:25，含 193 行 CRLF→LF 行尾变更 + dev/preview 改 `--open`）：**今日 08:23 用户拍板的"端口冲突修复"**（多项目并行预览时 5173 被占自动顺延），属阶段 0 用户基线；执行者正确保留，且该修复与专项无冲突。仓库约定：dev/preview 脚本**不得再写回 `--strictPort`**（见当日工作日志）。bat 行尾为基线工具写入所致，非专项引入；若在意可单独还原行尾，不影响功能。

## 4. 证据清单

- **确定性测试**：`test-prototype-source-check.py`（8 用例 ✅）、`test-shitpm-regression.py`（3 用例 ✅）、`test-resource-integrity.py`（✅）
- **构建**：`npm run build` 2.75s 通过（chunk >500kB 警告为既有状态，非本专项引入）
- **Playwright 证据**（`.playwright-cli/`，时间戳 2026-08-18 12:23–15:16）：
  - 截图 3 张：`2026-08-18-prototype-390-modal-sider.png`（移动 Sider+Modal 组合）、`...1440-home.png`、`...1440-home-clean.png`
  - aria snapshot 26 个：覆盖首页、404（NotFound）、表单页（含 Select 下拉展开态）、删除确认 Modal（dialog + 取消/删除按钮）
  - console log：无页面 error，仅 React DevTools 提示与 dev server 断开记录
- **规则一致性**：`references/templates/skills/contracts` 对 5 类废弃写法全文搜索零命中（除计划文档自身引用）
- **契约接口**：`prototype-consistency-check.py --help` 确认仅支持 `--project-root`（SKILL 中 `--module` 修正为 `--project-root` 是与脚本真实接口对齐，非引入新错误）

## 5. 保留问题（提交前必须处理）

1. **P1-1**：还原被损坏的 `docs/plans/2026-08-17-tabler-components-spec-draft.md`（`git checkout --` 该文件），防止损坏随专项入库；并查清 09:47 的误操作来源。
2. **P2-1**：若执行者声称"575/576/991/992 边界已观察"，需补充边界宽度截图或 viewport 记录；否则在交付中明确标"未验证"。
3. 基线说明：package.json/bat 的端口顺延改动是 08:23 用户修复，随专项一并提交合理；bat 行尾变更非本专项引入，可保持现状。
4. 未 commit/未 push（符合规则）；提交后推送 gitee(origin) 正常，推 github 需 Clash 代理（`git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=... push github V2`）。

## 6. 对后续工作的影响

- 本次专项与"AI 编辑税"话题正交：它把跨层运行时契约（路由/表单/身份/Portal/响应式）从文档规则固化为模板代码 + reference 契约，模板 `shared/ui/` 组件库与 behavior §9.1 同步更新后，后续原型生成可直接继承，不新增编辑负担。
- SKILL.md 第 1/4/5 步强化了"真实浏览器逐路由 + 代表性交互"要求，与 spm-prototype-review 第 8 步"逐项第 10 节完整清单"形成闭环，符合 AGENTS.md"行为结果可观察"原则。
