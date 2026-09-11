# Prototype Skill v3：定位重塑 + antd 官方规范落地 —— 执行与验收手册

> 日期：2026-09-11　版本：v3（执行手册版）
> 读者：独立执行模型。**本文件自包含，不依赖任何前置对话上下文。**
> 上游依据：用户四轮定位访谈（2026-09-11 收口）+ `references/design-sources/ant-design-official/`（Ant Design 官方设计团队规范，MIT）
>
> **与历史手册的关系**：
> - 本手册**取代** `docs/plans/2026-09-11-antd-official-visual-conformance-plan.md`（该文件已删除，内容并入本文）。
> - `docs/plans/2026-09-10-prototype-ant-design-skill-engine-upgrade-plan-and-acceptance.md` 的 **T-2A 路径（引入 ProComponents）已被本手册废止**：用户 2026-09-11 拍板卸载该依赖。9-10 手册的 **T-0（Tabler 阴影对齐）也被本手册 §2.4 覆盖**（"除颜色外全按 antd 官方"包含阴影）。
> - 9-10 手册保留作为历史执行记录，不再作为执行依据。

---

## 0. 执行前置（必读）

### 0.1 环境绝对路径

| 项 | 值 |
| :-- | :-- |
| 仓库根 | `D:\work\ShitPM`（Git Bash 中写作 `/d/work/ShitPM`） |
| 原型模板工程 | `D:\work\ShitPM\templates\prototype-vite` |
| 主题文件 | `templates\prototype-vite\src\theme\tablerTheme.ts` |
| 图标单一入口 | `templates\prototype-vite\src\shared\icons\index.jsx` |
| 共享组件 | `templates\prototype-vite\src\shared\ui\index.jsx` |
| Skill 源（唯一改这里） | `D:\work\ShitPM\skills\spm-prototype\SKILL.md`、`D:\work\ShitPM\skills\spm-prototype-review\SKILL.md` |
| Skill 已安装副本 | `C:\Users\guduj\.workbuddy\skills\spm-prototype\SKILL.md`（**与源仓库同 inode，改源即生效，无需复制**） |
| 评审清单 | `D:\work\ShitPM\contracts\prototype-review-checklist.md` |
| 官方规范（本次权威来源） | `D:\work\ShitPM\references\design-sources\ant-design-official\`（6 份 md + `ADAPTATION.md`） |
| 存量真实工程（T-5 目标） | `D:\work\交投软件中心\审计系统\output\prototype` |
| 门禁脚本 | `D:\work\ShitPM\scripts\python\prototype-consistency-check.py`、`prototype-source-check.py` |
| 回归测试 | `D:\work\ShitPM\scripts\python\test-*.py`（12 套件） |

**Python / Node**：直接用 `python`、`npm`、`node`，执行前用 `python -V`、`npm -v` 自检。浏览器实测用 Playwright（`C:/Users/guduj/.workbuddy/binaries/python/envs/default/Scripts/python.exe`，chromium 位于 `C:\Users\guduj\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe`），**临时脚本一律写 `.tmp/`，不得进仓库**。

### 0.2 硬约束（违反即任务失败）

1. **全程在分支 `codex/prototype-skill-v3` 上工作**（如该分支不存在则创建）。
2. **不得 push**；合入 `main` 前等用户拍板。
3. **不得删除 `.workbuddy/` 目录**。
4. **不得新增仓库级检查脚本、报告 JSON、回执或门禁**（`AGENTS.md` §1 工具准入）。所有验收使用**现有**脚本；临时验证脚本放 `.tmp/` 并在 T-6 清理。
5. **不得修改 Design 事实源**（`output/design/` 下任何文件）。
6. **不得引入任何新的重型运行时依赖**（本次是净减依赖：卸载 2 个包）。
7. `prototype-consistency-check.py` 的分类语义不得改变。

### 0.3 已核实的事实（执行时直接采信，不要重新验证）

| 事实 | 值 | 来源 |
| :-- | :-- | :-- |
| 模板工程依赖 | `antd ^6.6.0`、`@ant-design/pro-components 3.1.14-7`、`@tabler/icons-react ^3.34.0`、`echarts ^6.1.0`、`dayjs`、`react ^18.3.1` | `templates/prototype-vite/package.json` |
| `@ant-design/icons` | **6.3.2**，已作为 antd 6.6.0 的依赖存在于 `node_modules`；需在 `package.json` 显式声明 | `node_modules/@ant-design/icons/package.json` |
| 图标现状 | `src/shared/icons/index.jsx` 已存在，是 22 个 Tabler 图标的**语义名再导出**（`IconPlus` 等）；直接引用 `@tabler/icons-react` 的文件共 **9 个**（其中 2 个随 T-1 删除） | `grep -rl` |
| 图标规模（存量工程） | 4 个文件、149 处、45 个不同图标 | 审计系统工程实测 |
| 用户区现状 | `src/App.jsx` L102-103 写死 `<Avatar>{'示'}</Avatar><span>{'演示用户'}</span>`，**无下拉、无角色概念** | 模板源码 |
| 交付通路 | `原型工具.bat` 第 4 项 = `npx --yes wrangler pages deploy "dist"`；生产域名为 `https://<wrangler.toml 的 name>.pages.dev`（hash 子域每次变化，不可作分享地址） | `原型工具.bat` |
| 官方规范覆盖 | `layout.md` 1266 行、`components_Table.md` 820 行、`components_Form.md`（含抽屉/弹窗选型 40+ 处）、`components_List.md`、`components_DescriptionList.md`、`components_Chart.md`（基于 `@ant-design/charts`，本库用 ECharts，需按 `ADAPTATION.md` 适配） | 本库 `references/design-sources/ant-design-official/` |
| 官方规范授权 | MIT（可自由使用、修改、商用，保留版权声明） | 上游仓库 LICENSE |
| Skill 副本关系 | `skills/` 与 `~/.workbuddy/skills/` 为**同一 inode**，改源即生效 | `stat -c %i` |

### 0.4 ⚠️ 基线实测：三条已被证伪的旧口径（不得再作论据）

| 旧口径 | 实测结果 | 处置 |
| :-- | :-- | :-- |
| "引入 ProComponents 可让单页代码 **-50%**" | 业务页 `ProblemList.jsx` 从 **102 → 162 行（+59%）** | **指标废止**。行数会因显式锚点增加，属负收益指标 |
| "包体积减少近 **1MB**" | 实测增量为 **+562 kB / +179 kB gzip（+24%）**，且 HEAD 本就触发 Vite chunk 告警 | 数字更正；**该指标不得作为选型依据**（原型不交付研发） |
| "`dist/` 中不得出现 `#1677ff`" | antd 6 编译产物**自带**调色板字典，静态 grep **永远不可能通过** | 阈值改为「`src/` 不得出现」+「浏览器计算样式无泄漏」 |

**替换后的主指标**：① 首次运行缺陷数；② 评审现场返工轮次；③ AI 生成时是否仍需临场决策视觉规则（命中规范即零决策）。

### 0.5 基线（T-0 须复现确认）

- 回归测试：**12 套件 11 绿**；唯一红灯 `test-prd-simplification.py`（`Skill 缺少核心语义责任: 跨页面推进`）在 `HEAD` 上同样失败 = **存量问题，不记本次账**。
- `npm run build`：exit 0，产物约 **2.88 MB / gzip 931 KB**，触发 1 条 chunk 告警。
- 当前工作区有 22 个未提交改动（含 9-10 遗留）。**T-0 必须记录；本次提交只包含本手册列明的文件，不得混入这些遗留改动。**
- **已知坑（本轮踩过，已修）**：`references/design-sources/ant-design-official/*.md` 是逐字引入的官方原文，其中**上游仓库的跨仓库相对路径**（形如 `references/components_Form.md`、`references/global-style.css`）会被 `test-resource-integrity.py` 判为**资源引用不存在**并 exit 1。修法：去掉 `references/` 前缀改为同目录文件名引用，**不要在"阅读须知"的说明文字里再写出该完整路径**（同样会命中正则）。新增或改动官方文档后必须复跑该测试。

---

## 1. 任务总览与决策树

```text
T-0  基线记录（测试 + 构建 + 工作区快照）
              │
              ▼
T-1  卸载 ProComponents 与死资产 ──► 门禁：src/ 0 命中 + build exit 0
              │
              ▼
T-2  视觉对齐官方（主题 / CSS / shared-ui / 图标）
              │                     门禁：主题无非颜色覆盖 + 图标单一入口 + build exit 0
              ▼
T-3  新增 7 类标准结构与角色权限规范（2 个新 references）
              │                     门禁：两文件含 ## 目录 + 五段齐备
              ▼
T-4  SKILL / 评审契约 / 既有规范同步
              │                     门禁：全仓 grep Pro/Claude/三选一 0 命中
              ▼
T-5  存量审计系统统一（T-5a 视觉层 + T-5b 规范增量回改，均可独立回退）
              │
              ▼
T-6  验收与报告（§5 全量）──► 产出 docs/reports/2026-09-11-prototype-skill-v3-acceptance.md
              │
              ▼
    等用户拍板合入（不 push）
```

**顺序铁律**：T-1 与 T-2 必须**分两次提交**（卸载、视觉对齐各自可独立回退）；T-3 的两份文档必须先经用户审阅再进入 T-4（SKILL 要引用它们的章节号）。

---

## 2. 目标形态：做完之后技能长什么样

### 2.1 规范体系的分层（谁是权威）

| 层 | 文件 | 权威范围 |
| :-- | :-- | :-- |
| **官方结构与交互规则** | `references/design-sources/ant-design-official/*.md`（6 份，MIT） | 尺寸、间距、控件规格、组件选型、弹层选型、长文本省略、分页、卡头表达 |
| **颜色体系** | `templates/prototype-vite/src/theme/tablerTheme.ts` | 全部色值（Tabler） |
| **项目组习惯** | `references/prototype-shell.md`、`prototype-writing.md` | 仅 §2.5 白名单 6 条 |
| **页面结构** | `references/prototype-page-types.md`（新增） | 7 类页面的标准结构与顺序 |
| **角色与权限表达** | `references/prototype-role-permission.md`（新增） | 角色切换器形态、权限层级表达 |
| **组件级行为边界** | `references/prototype-component-behavior.md` | 组件选型与例外、跨层运行时契约 |

**冲突裁决顺序：官方规则 > 项目组习惯（仅白名单 6 条）> 本库其他约定。**

### 2.2 页面分类：**7 类 + 公共页**

> ⚠️ **命名冲突必须处理**：`references/prototype-visual-spec.md` §2.5 现有「看板页（Kanban）」指 **Trello 式拖拽任务板**，与用户口径的「看板页 = 一屏指标概览」**不是同一个东西**。
> 处置：用户口径的**类 7 定名「看板页（概览/驾驶舱）」**；旧 Kanban 骨架改称「**任务看板页**」并**移出 7 类**，归入「公共页」，`visual-spec.md` 中标注。

| # | 页面类型 | 判别 | 官方章节书签 |
| :-- | :-- | :-- | :-- |
| 1 | 标准查询表格 | 筛选项 **≥5** | `components_Table.md` §筛选组件使用规则 / 列表页顶部筛选 / 表格样式规范 / 分页规范 / 表格卡头部表达 |
| 2 | 轻量工具栏表格 | 筛选项 **≤4** | `components_Table.md` §工具栏布局 / 表格卡头部表达 / 卡内顶部 Tab Strip |
| 3 | 批量操作表格 | 行选择 + 批量动作 | `components_Table.md` §4 批量操作表格 / 工具栏布局 |
| 4 | 多步骤长流程表单 | ≥3 步或有先后依赖 | `components_Form.md` §分步表单选型 / §3 竖向分步表单 |
| 5 | 配置类 / 分组表单 | 单页多分组、无步骤依赖 | `components_Form.md` §4 嵌入模式表单 / 输入框宽度规范 / 操作按钮位置 |
| 6 | 对象详情页 | 只读呈现单对象 | `components_DescriptionList.md` §描述列表选型 / §3 分组卡片描述列表 / 布局规则 |
| 7 | **看板页（概览/驾驶舱）** | 一屏指标 + 图表 | `components_Chart.md` + `layout.md` §主内容区规范 |
| — | **公共页** | 登录 / 个人中心 / 结果页 / 异常页（403/404/500）/ 任务看板页 | `components_Form.md` §6 登录表单 + `layout.md` |

**另有 1 个横切模式**（不占 7 类名额）：

| 模式 | 触发 | 手册依据 |
| :-- | :-- | :-- |
| **快照 / 只读态** | 展示已归档版本或不可再编辑的记录 | 存量 `SnapshotBar` 实践（附录 A 末尾），官方手册无对应章节 |

**每类配一份「文字版标准结构」**（写死顺序与必须项，**不写代码骨架**）。初稿见附录 A，经用户审定后落 `references/prototype-page-types.md`。

> ⚠️ **类 2 与类 4 是净新增要求**，存量审计系统 0 例（详见附录 A.0）。写规范时不得把它们描述成"整理现有做法"——它们是新增约束，且**不回溯改存量**。

### 2.3 角色与权限表达规范

**切换器形态**（参考存量审计系统并按下述修正）：

- 右上角：`Avatar`（品牌色底 + 白字，**取当前角色首字**）+ **角色名文本**
- **点击角色名展开** `Dropdown`，平铺列出全部角色；选中即切换，**不刷新页面**
- 默认角色：**管理员 / 主管视角**（先给全局，再演"一线看不到某些按钮"的落差）
- 角色数 > 6 时再考虑分组

**权限表达层级**：

| 层级 | 表达方式 | 硬规则 |
| :-- | :-- | :-- |
| 菜单可见 | 无权限项 **不渲染** | 不得渲染后置灰（菜单灰项会让评审误以为"系统坏了"） |
| 按钮可点 | 无权限 → **不渲染**；有条件可用（状态不满足）→ `disabled` + 悬浮说明 | 禁止用"（无权限）"这类文字标注代替真实控件状态 |
| 字段可见 / 只读 | 不可见 → **整个 label:value 对不渲染**；只读 → 值正常展示、不出现编辑控件 | 禁止渲染成禁用输入框 |
| **数据范围** | **粗粒度示意**：表格顶部一行范围提示（如"以下仅显示本人提交的 3 条"） | **不做部门树、不做范围筛选器** |

**权限事实来源**：

- 可推断的（菜单 / 按钮 / 字段级）→ 汇总成**推断表**（落 `output/design/decision-notes.md` 或评审前一次性呈报），用户一次拍板
- **高影响必须问**（不得推断）：数据范围、审批链、谁能删谁、跨组织可见性

**最强现成载体：状态机动作按钮组**（从存量 `rectify/r06` 抽出的模式，本次直接采纳）：

详情页底部操作栏里，把该实体的**全部状态迁移动作**一次列全，按「当前状态 + 当前角色」决定每个按钮是**渲染 / `disabled` / 不渲染**。评审时切角色，就能当场看出"这个角色能做什么、不能做什么"——这正是用户定义的评审核心（"不同角色时候的各种问题"）。

> 不要只演菜单差异。菜单差异一眼可见、信息量低；**按钮级启停 + 状态迁移**才是评审现场真正会被问住的地方。

### 2.4 视觉口径：**颜色留 Tabler，其余全按 antd 官方**

**动作原则：不逐个改成官方值，而是把主题里所有"非颜色覆盖"删掉，让官方默认自己生效。** 这样不会漏项。

**删除清单（`tablerTheme.ts`）**：

| 位置 | 现值 | 官方默认 | 动作 |
| :-- | :-- | :-- | :-- |
| `token.controlHeight` | 40 | **32** | 删 ← 按钮"臃肿"的根因 |
| `token.fontSize` | 14 | 14 | 删（冗余） |
| `token.fontFamily` | `"Inter", …` | 系统字体栈 | 删 |
| `token.borderRadius` | 6 | 6 | 删（冗余） |
| `token.boxShadow` / `boxShadowCard` / `boxShadowSecondary` | Tabler 深蓝黑基 `rgba(18,18,23)` | antd 原生黑基 | 删 |
| `Button.controlHeight` / `fontWeight` / `borderRadius` / `primaryShadow` / `defaultShadow` / `defaultBorderColor` / `defaultBg` | Tabler | antd | 删 |
| `Card.borderRadiusLG` / `boxShadow` / `headerPadding` / `bodyPadding` | 8 / Tabler / 16-20 | 8 / antd / **24** | 删 |
| `Table.headerFontSize` / `cellPaddingBlock` / `cellPaddingInline` | 12 / 12 / 12 | **14** / **16** / **16** | 删 |
| `Input.boxShadow` / `activeShadow` | Tabler 微阴影 + 蓝 ring | antd | 删 |
| `Menu.itemBorderRadius` / `Modal.borderRadiusLG` / `Tag.borderRadiusSM` | 6 / 8 / 4 | 同值 | 删（冗余） |
| `Avatar.colorTextLightSolid` | `#6b7280` | 白 | 删（改为品牌色底 + 白字） |

**保留（颜色体系 = Tabler）**：`colorPrimary*`、`colorBg*`、`colorText*`、`colorBorder*`、`colorSplit`、`colorSuccess/Warning/Error/Info/Link*`、`Layout.siderBg/headerBg`、`Menu.*`（选中/悬停色）、`Tabs.*`、`Descriptions.labelBg`、`Select.*`（选项底色）、`Input/DatePicker.colorBgContainer`、`Table.headerBg/headerColor/rowHoverBg/borderColor`。

**`tablerCssVars` 同步**：删除 `--card-shadow`、`--card-shadow-hover`、`--control-shadow`（阴影交官方）；`--avatar-bg` 改品牌色；其余保留。

**`global.css` 与 `shared/ui` 同步**：清掉基于 40px 控件推导的写死间距/行高；尺寸类改用官方值或交给官方默认。

### 2.5 项目组习惯白名单（官方手册不覆盖，以此为准）

| # | 规则 | 状态 |
| :-- | :-- | :-- |
| ① | 三栏固定：顶栏（品牌 + 主模块标签 + 用户区）/ 侧栏（当前模块菜单）/ 标签页栏（可关闭，首页常驻） | 保留 |
| ② | 标签页替代页面大标题；内页才显示标题 + 右上返回 | 保留 |
| ③ | 页面级操作按钮统一放**底部通栏贴底操作栏** | 保留 |
| ④ | 操作栏上方放版权"研发单位：广西计算中心" | 保留 |
| ⑤ | ~~详情列表一行两对 label:value = 17% / 33%~~ | **本次去掉**，详情页排版按官方默认 |
| ⑥ | 表格首末列钉住 + 允许横向滚动 | 保留 |
| ⑦ | 表单一律 label 在上、控件在下的竖排 | 保留 |

### 2.6 图标：统一 `@ant-design/icons`

- **不需要新增运行时依赖**：`@ant-design/icons@6.3.2` 已随 antd 6.6.0 安装；需在 `package.json` **显式声明**（避免隐式依赖）。
- 现有 `@tabler/icons-react` **删除**（净减一个依赖）。
- `src/shared/icons/index.jsx` 改为从 `@ant-design/icons` **再导出，语义名不变**（页面无需改动）：

  ```jsx
  // 示例：语义名保持不变，右侧换成官方图标
  export {
    PlusOutlined as IconPlus,
    DeleteOutlined as IconTrash,
    // …其余 20 个同理
  } from '@ant-design/icons';
  ```

- **硬规则**：页面与组件一律从 `shared/icons` 取图标，**禁止直接 import** `@ant-design/icons` 或 `@tabler/icons-react`。
- 找不到语义精确对应的图标时，在 `shared/icons/index.jsx` **集中登记**"语义最近"的选择，**不臆造图标名**。
- 规模（T-1 删除后）：模板工程 **7 个文件**需改引用；存量审计系统 **4 个文件、149 处、45 个图标**。

### 2.7 交付：静态包 → Cloudflare

- 通路**已存在**：`原型工具.bat` 第 4 项即上传 Cloudflare，工程已有 `wrangler.toml`。
- 验收必须包含**打开线上网址实测**（默认页 + 3 个代表路由 + 角色切换）。
- `README.md` 首屏保持"双击 bat"为唯一用户入口。

---

## 3. 现状盘点

### 3.1 保留（资产）

| 资产 | 位置 | 理由 |
| :-- | :-- | :-- |
| Tabler 颜色体系 | `theme/tablerTheme.ts`（颜色部分） | 用户拍板保留；且圆角 6/8/4 与官方本就一致 |
| 官方规范 6 份 + 适配说明 | `references/design-sources/ant-design-official/` | 本次规范的权威来源（MIT） |
| 页面级交互规则 | `references/prototype-component-behavior.md` §4–§9 | 与依赖无关，转写为附录 A 的正文 |
| 轻量组件封装 | `src/shared/ui/`（11 组件，228 行，无黑盒状态） | 目标 3（fix 快）的资产 |
| 壳层与布局习惯 | `references/prototype-shell.md`、`prototype-writing.md` | 白名单 6 条的载体 |
| 两个一致性工具 | `scripts/python/prototype-{source,consistency}-check.py` | 已有真实消费者 |
| demo 样张排除前缀 | `prototype-consistency-check.py` 的 `EXCLUDED_SOURCE_PREFIXES` | 防样张锚点污染（2026-09-11 刚修，保留） |
| Cloudflare 交付链 | `原型工具.bat` 第 4 项 + `wrangler.toml` | 用户唯一的交付方式 |

### 3.2 删除（负债）

| 目标 | 动作 |
| :-- | :-- |
| `templates/prototype-vite/src/shared/templates/`（9 文件：6 模板 + index + css） | 删目录 |
| `templates/prototype-vite/src/modules/demo/TemplateGallery.jsx` | 删文件 |
| `@ant-design/pro-components@3.1.14-7` | 移出 `package.json` 并更新 lock（`options={false}` 等 Pro 专用写法一并消失） |
| `@tabler/icons-react` | 移出 `package.json`（改走官方图标） |
| `main.jsx` 的 `ProConfigProvider` | 删包裹层 |
| `routes.jsx` 的 `/template-gallery` 路由与 import | 删登记 |
| `theme/claudeTheme.ts` | 删（零运行时引用） |
| `references/design-sources/claude-2-design-system/` + `claude-DESIGN.md` | 删（死资产，约 301KB） |
| `prototype-consistency-check.py` 的 `columns[].dataField` 解析补丁 | 回退（ProTable 专用） |
| `spm-prototype/SKILL.md`「页面模板起步」整节 + Pro 相关自检项 | 重写 |
| `prototype-review-checklist.md` 第 22/24 条的 Pro 专属部分 | 回退 |
| `spm-prototype-review/SKILL.md` 的 ProTable 段落 | 回退 |

### 3.3 修改（口径冲突）

| 文件 | 改什么 |
| :-- | :-- |
| `theme/tablerTheme.ts` | 按 §2.4 删除非颜色覆盖 |
| `styles/global.css` | 阴影/尺寸同步官方 |
| `src/shared/ui/index.jsx` | 核对并清掉写死尺寸（`height:40`、`fontSize:12` 一类） |
| `src/shared/icons/index.jsx` | 改官方图标再导出（语义名不变） |
| `src/App.jsx` / `routes.jsx` / `modules/home/Home.jsx` / `modules/demo/*` | 图标来源改走 `shared/icons` |
| `src/App.jsx` 用户区 | 按 §2.3 实现角色切换器（替换写死的"演示用户"） |
| `references/prototype-visual-spec.md` | §1.4 字体、§1.5 尺寸、§1.6 阴影改按官方；§1.7 图标改官方；§2 七类骨架改为指向新文档 + 标注 Kanban 改名 |
| `references/prototype-writing.md` | 「Tabler 视觉入口」→「官方结构 + Tabler 颜色」；组件语义名 |
| `references/prototype-component-behavior.md` | §4–§9 迁出至页型文档；本文件只留 §1–§3 组件级规则 |
| `references/design-sources/ant-design-official/ADAPTATION.md` | 补"尺寸/字号/间距/阴影一律照官方原文；仅颜色换 Tabler"的明文口径 |

### 3.4 新增（缺口）

| 文件 | 内容 |
| :-- | :-- |
| `references/prototype-page-types.md` | 7 类 + 公共页：标准结构 / 必须出现 / 禁止出现 / 官方章节书签 / 锚点约定（初稿见附录 A） |
| `references/prototype-role-permission.md` | 角色切换器形态 + 四级权限表达表 + 推断表模板 + 高影响问题清单 |
| `docs/reports/2026-09-11-prototype-skill-v3-acceptance.md` | 验收报告（T-6 产出） |

**已知缺口（技能现状）**：`skills/spm-prototype/SKILL.md` 仍强制"6 类模板起步"，与本次卸载冲突；用户口径的页面分类在技能与 references 中 **0 定义**。

---

## 4. 执行步骤

> 每步独立可验证；发现前置不成立时**停止并报告**，不跳过。

### T-0　基线记录

```bash
cd /d/work/ShitPM
# 1) 全量回归测试基线
for f in scripts/python/test-*.py; do n=$(basename "$f"); python "$f" > ".tmp/t0-$n.log" 2>&1; echo "$n exit=$?"; done
# 2) 构建基线与体积
cd templates/prototype-vite && npm run build 2>&1 | tail -20
# 3) 工作区快照
cd /d/work/ShitPM && git status --short > .tmp/t0-status.txt && wc -l .tmp/t0-status.txt
```

**完成判据**：12 套件退出码全部记录；**与 §0.5 基线差分无变化**（预期 11 绿 + 1 存量红）；构建体积与告警数记录。**若与基线不一致，先查清原因再继续。**

### T-1　卸载 ProComponents 与死资产

**精确改动清单**（逐条执行）：

```bash
cd /d/work/ShitPM/templates/prototype-vite
rm -rf src/shared/templates
rm -f src/modules/demo/TemplateGallery.jsx
rm -f src/theme/claudeTheme.ts
rm -rf /d/work/ShitPM/references/design-sources/claude-2-design-system
rm -f /d/work/ShitPM/references/design-sources/claude-DESIGN.md
npm uninstall @ant-design/pro-components
```

再手工改两处：

1. `src/main.jsx`：删除 `import { ProConfigProvider } from '@ant-design/pro-components';` 与 `<ProConfigProvider>…</ProConfigProvider>` 包裹，恢复为 `<ConfigProvider locale={zhCN} theme={tablerTheme}><AntdApp><App /></AntdApp></ConfigProvider>`。
2. `src/routes.jsx`：删除 `TemplateGallery` 的 import 与 `/template-gallery` 路由登记。

```bash
# 验收
grep -rn "pro-components\|ProTable\|ProForm\|ProConfigProvider\|ProColumns" src/ | wc -l   # 期望 0
ls src/shared/templates 2>&1                                                                # 期望 No such file
grep -c "pro-components" package.json                                                       # 期望 0
npm run build 2>&1 | tail -5                                                                # 期望 exit 0
```

**完成判据**：以上四条全过；`git status` 中新增删除项仅限本清单。

### T-2　视觉对齐官方（模板工程）

**改动顺序**（先主题、后图标、再核对 CSS）：

1. `src/theme/tablerTheme.ts`：按 §2.4 删除清单逐 token 删除；同步改 `tablerCssVars`（删 3 个阴影变量、`--avatar-bg` 改品牌色）。
2. `src/shared/icons/index.jsx`：从 `@ant-design/icons` 再导出，语义名不变；`package.json` 加 `@ant-design/icons` 显式依赖。
3. 替换 7 个文件的图标引用（`App.jsx` / `routes.jsx` / `modules/home/Home.jsx` / `modules/demo/{DesignGallery,DetailDemo,FormDemo}.jsx` / `shared/ui/index.jsx`），全部改走 `shared/icons`。
4. `src/App.jsx` 用户区：按 §2.3 实现角色切换器（Avatar 取角色首字 + 角色名 + 点击展开 Dropdown）。
5. `src/styles/global.css` 与 `shared/ui/index.jsx`：清掉基于 40px 推导的写死尺寸。

```bash
# 验收（静态）
grep -n "controlHeight\|fontFamily\|boxShadow" src/theme/tablerTheme.ts        # 人工逐条确认仅颜色 token 保留
grep -rn "@tabler/icons-react" src/ | wc -l                                     # 期望 0
grep -rn "from '@ant-design/icons'" src/ | grep -v "shared/icons" | wc -l       # 期望 0
npm run build 2>&1 | tail -5                                                    # 期望 exit 0
```

```bash
# 验收（浏览器实测，§5.2 全部 13 项）
python .tmp/visual-check.py          # 临时脚本，T-6 清理
```

**完成判据**：静态四条全过；`npm ci && npm run build` exit 0；§5.2 阈值表全命中；§5.4 反向检查无回归。

### T-3　新增 7 类标准结构与角色权限规范

- 按 §2.2 / §2.3 / 附录 A 落 `references/prototype-page-types.md` 与 `references/prototype-role-permission.md`。
- 把 `prototype-component-behavior.md` §4–§9 内容**迁入**页型文档，原文件只留 §1–§3。

**完成判据**：7 类 + 公共页各有"标准结构 / 必须 / 禁止 / 官方章节书签 / 锚点约定"**五段**；两文件均含 `## 目录`（>100 行门禁，`test-resource-integrity.py` 会校验）；**提交用户审阅后再进 T-4**。

### T-4　SKILL / 评审契约 / 既有规范同步

- 重写 `skills/spm-prototype/SKILL.md`：删「页面模板起步」；改为「页面分类与标准结构」路由表（7 类 + 公共页 → `prototype-page-types.md` 章节 + 官方书签 + `behavior.md` 章节）；加角色/权限规范引用；加 Cloudflare 交付验收；删 Tabler 三选一残留。
- 同步 `skills/spm-prototype-review/SKILL.md`（回退 ProTable 段落，新增角色差异 / 官方尺寸合规 / 图标来源统一三条）。
- 同步 `contracts/prototype-review-checklist.md`（回退第 22/24 条 Pro 专属部分）。
- 同步 `references/prototype-visual-spec.md`、`references/prototype-writing.md`、`ADAPTATION.md`（按 §3.3）。
- 回退 `prototype-consistency-check.py` 的 `dataField` 补丁（保留 `EXCLUDED_SOURCE_PREFIXES`）。

```bash
# 验收
grep -rn "pro-components\|ProTable\|ProForm\|claudeTheme\|traework\|三选一" \
  skills/ references/ contracts/ scripts/ templates/prototype-vite/src/ 2>/dev/null | wc -l   # 期望 0（历史 docs 除外）
python scripts/python/test-resource-integrity.py      # 期望 exit 0
```

**完成判据**：全仓运行时文件 0 命中；`test-resource-integrity.py` exit 0。

### T-5　存量审计系统工程统一（**视觉层 + 规范增量回改**）

- 目标：`D:\work\交投软件中心\审计系统\output\prototype`。
- **前置动作（必做）**：确认该工程可回退（git 提交或目录备份）。**不可回退则停止并报告。**
- ⚠️ **本步骤范围已扩大**：附录 A.0.1 已逐条拍板，**T-5 不再只是"纯视觉层"**，含 7 项结构级回改。拆成两个可独立回退的子步骤。

#### T-5a　视觉层统一（低风险，先做）

- 同步主题文件（删非颜色覆盖）+ 图标换官方（4 文件 / 149 处）+ 清与官方冲突的写死尺寸（实测：写死字号 72 处、内边距 52 处、**按钮高度仅 3 处**，绝大部分随主题自动生效）。
- **不改**页面结构与业务事实。

#### T-5b　规范增量回改（结构级，逐项可单独跳过）

来源 = 附录 A.0.1「存量回改」列为 `回改` 的 7 项：

| # | 项 | 改动 | 规模 |
| :-- | :-- | :-- | :-- |
| 1 | 返回按钮 | 底部操作栏 → **内页标题右上** | 24 处 / 8 模块 |
| 3 | 分页 | `pagination={false}` → **带分页 + 总条数** | 27 个列表页 |
| 4 | 筛选卡 | 平铺 → **筛≥5 默认折叠可展开** | 含 ≥5 筛选的列表页 |
| 5 | 表格卡头 | 纯文字标题 → **标题 + 数量徽章 + 右侧工具栏** | 全部表格卡 |
| 7 | 长文本 | 不省略 → **`ellipsis` + 悬浮全文** | 长文本列 |
| 9 | 状态标签 | 字段行内 → **内页标题旁** | 详情页 |
| 10 | 版权行 | 仅 1 处 → **有底部操作栏的页面全局补** | 约 20 页 |
| 8 | 钉列 / 滚动 | 不一致 → **只修真的会溢出的页**（折中口径，勿全量套用） | 3 页缺 `scroll` + 3 页操作列缺 `fixed` |

> 每项**独立提交**，任一出现视觉回归可单独 `git revert`，不影响其余项与 T-1~T-4。

**完成判据（T-5a + T-5b 合并）**：build exit 0；§5.2 阈值表在该工程同样全过；回改项逐一在浏览器复验；`git diff --stat` 涉及的**非视觉文件仅限上表列明的项**。

### T-6　验收与报告

- 按 §5 全量执行，产出 `docs/reports/2026-09-11-prototype-skill-v3-acceptance.md`（结构照 9-10 验收报告：探针结果 / 走了哪条路径 / §5 逐条结果 / 阈值表实测值 / 未解决项与建议）。
- 追加 `.workbuddy/memory/2026-09-11.md` 日志；更新 `MEMORY.md` 中已作废口径。
- 清理 `.tmp/` 下本次临时脚本与日志。

**完成判据**：§5.1 全绿或逐项说明；§5.2 全过；报告落盘；临时文件清零。

---

## 5. 验收方案

### 5.1 自动化门槛（必须全绿，逐项记录退出码）

| # | 命令 | 通过判据 |
| :-- | :-- | :-- |
| 1 | `python scripts/python/test-*.py`（12 套件） | 与 T-0 基线**差分：无新增红灯**；存量红灯 `test-prd-simplification.py` 不计本次账 |
| 2 | `python scripts/python/prototype-source-check.py --project-root .` | exit 0 |
| 3 | `python scripts/python/prototype-consistency-check.py --project-root <项目根>` | **无新增** `deterministic_conflicts`；`possible_omissions` 不因本次改动增加 |
| 4 | `npm run build` | exit 0 |
| 5 | 全仓 grep：`pro-components` / `ProTable` / `ProForm` / `claudeTheme` / `traework` | 运行时文件 0 命中（历史 docs 除外） |

> ⚠️ **`--project-root` 语义坑**：该参数指「**含 `output/prototype` 的项目根**」。对只给 src 目录的回归 harness，必须改传 `--prototype-root`（source-check）/ `--prototype-src`（consistency-check），否则 consistency-check 以 `fatal_input_error` exit=2 **静默返回全 0**（看起来"没问题"）。**退出码 0 也不代表无遗漏**（`possible_omissions` 同样返回 0）。

### 5.2 浏览器实测阈值表（真实浏览器计算样式，13 项必须全命中）

| # | 项 | 阈值 | 判定 |
| :-- | :-- | :-- | :-- |
| 1 | 主按钮高度 | `32px` | 绝对 |
| 2 | 输入框 / 下拉框高度 | `32px` | 绝对 |
| 3 | 卡片内边距 | `24px` | 绝对 |
| 4 | 表格单元格 padding | `16px × 16px` | 绝对 |
| 5 | 表头字号 | `14px` | 绝对 |
| 6 | 卡片/浮层阴影 | antd 原生（**非** `rgba(18,18,23,…)`） | 绝对 |
| 7 | 字体栈 | 含 `PingFang SC` / `Microsoft YaHei`，**不含 `Inter`** | 绝对 |
| 8 | 图标 DOM | 全部 `.anticon` 类 | 绝对 |
| 9 | 主色 | `rgb(6, 111, 209)` | 绝对（颜色未被动） |
| 10 | 页面底色 | `rgb(249, 250, 251)` | 绝对 |
| 11 | 表头底色 | `rgb(249, 250, 251)` | 绝对 |
| 12 | 全页计算样式 | 无 antd 默认蓝 `#1677ff` / `#1890ff` 泄漏 | 绝对 |
| 13 | 浏览器 console | 0 error、0 warning | 绝对 |

### 5.3 角色差异验收（本次新增的核心项）

| # | 场景 | 判据 |
| :-- | :-- | :-- |
| 1 | 切换器位置与形态 | 右上角显示"头像 + 角色名"；**点击角色名**展开角色列表 |
| 2 | 默认角色 | 进页面即管理员/主管视角 |
| 3 | 菜单差异 | 切换后侧栏菜单**项数发生变化**（无权限项消失，非置灰） |
| 4 | 按钮差异 | 切换后同一页面按钮**出现/消失**（无权限按钮不渲染） |
| 5 | 字段差异 | 切换后同一页面字段对**出现/消失**或由可编辑变只读 |
| 6 | 数据范围示意 | 有范围限制时表格顶部出现范围提示行 |
| 7 | 切换无刷新 | 切换角色后页面不整页刷新 |

### 5.4 反向检查（防止改过头）

| # | 项 | 判据 |
| :-- | :-- | :-- |
| 1 | 颜色未被官方覆盖 | §5.2 第 9/10/11 项通过 |
| 2 | 项目组习惯 6 条仍在 | 三栏固定 / 标签页替代标题 / 底部通栏操作栏 / 版权行 / 首末列钉住 / 表单竖排，逐条人工确认 |
| 3 | 侧栏为浅色 | 未回退为深色或透明 |
| 4 | 构建产物可上传 | `dist/` 生成后 `原型工具.bat` 第 4 项可用（`wrangler.toml` 在位） |

### 5.5 交付验收

| # | 步骤 | 判据 |
| :-- | :-- | :-- |
| 1 | `npm run build` | exit 0 |
| 2 | 上传 Cloudflare（`原型工具.bat` 第 4 项） | 返回可访问网址 |
| 3 | 打开**线上网址** | 默认页 + 3 个代表路由（列表类 / 表单类 / 详情类各一）可打开，无白屏 |
| 4 | 线上角色切换 | 切换器可用，菜单/按钮差异在线上同样生效 |

### 5.6 验收结论模板

```text
结论：PASS / REJECTED
- §5.1 自动化：n/n 通过（列出例外与理由）
- §5.2 尺寸阈值：n/13 通过
- §5.3 角色差异：n/7 通过
- §5.4 反向检查：n/4 通过
- §5.5 交付：线上网址 <url> 实测通过/失败
- 未解决项：<逐条>
- 负面结论（不得省略）：<如某阈值不可达的真实原因>
```

---

## 6. 停止条件与回滚

| # | 风险 | 应对 |
| :-- | :-- | :-- |
| 1 | 删除尺寸覆盖后，`global.css` 与 `shared/ui` 中基于 40px 推导的写死值错位 | T-2 逐文件核对；§5.2 浏览器实测兜底 |
| 2 | 45 个 Tabler 图标中部分在官方库无精确对应 | 允许"语义最近"并在 `shared/icons` 集中登记，**不臆造** |
| 3 | 阴影改官方会覆盖 2026-09-10 的 Tabler 阴影基准（commit `5f5cfc0`） | §2.4 已显式声明；**仅此一项可单独回退**（保留 Tabler 阴影不影响其余口径） |
| 4 | 改存量工程（审计系统）可能引入视觉回归 | T-5 前**必须确认可回退**（git / 备份）；不可回退则停止 |
| 5 | 官方图标与 Tabler 图标视觉风格不同，用户可能不接受 | 换库仅涉 7–11 个文件，回退成本低 |
| 6 | 卸载 ProComponents 后 6 个模板的交互实现（分页归位、步骤校验、草稿暂存）消失 | 这些行为转为 `prototype-page-types.md` 的**强制规则**（文字版），由 AI 按规则实现 |

**通用停止条件**：任一 T 步骤的"完成判据"不成立 → 停止，报告不成立项与已做改动，**不进入下一步**。

**回滚方式**：T-1 / T-2 各自独立提交，可分别 `git revert`；T-5 依赖其自身的备份/git 历史。

---

## 7. 不做什么

- 不引入 ProComponents 或任何重型组件库
- 不把代码行数 / 包体积当验收指标
- 不做 390px 专项响应式测试（已有约定）
- 不做看板下钻（用户明确：要做会专门说）
- 不新增检查脚本（`AGENTS.md` §1 工具准入：无真实证据不新增）
- 不改 Design 事实源；不 push

---

## 附录 A　7 类页面「文字版标准结构」（已对存量实测比对）

> 每类的"标准结构"= 页面从上到下的固定顺序；"必须"= 缺一项即不合格；"禁止"= 出现即不合格。
> 尺寸与间距一律按官方手册，颜色按 Tabler，壳层按 §2.5 白名单。

### A.0　存量审计系统实测对照（2026-09-11，只读扫描 12 模块 / 12203 行 JSX）

写这一类结构之前，先实测了存量工程 `D:\work\交投软件中心\审计系统\output\prototype` 到底做到了哪一步。**结论：骨架已覆盖，但有 5 层缺失 + 2 类是净新增。**

| 类 | 存量实况 | 差异性质 |
| :-- | :-- | :-- |
| 类1 标准查询表格 | 17+ 页，形态成熟 | 缺：分页、卡头数量徽章、筛选卡展开/收起、操作栏上方版权行 |
| 类2 轻量工具栏表格 | **0 页**（所有列表页一律"独立筛选卡"，含 11 项筛选的 `archive/a01`） | **净新增要求**，无样本可抄，**不回改存量** |
| 类3 批量操作表格 | 2 页有 `rowSelection`（`feedback/fb05`、`rectify/r01`） | 缺："已选 N 项"提示条 |
| 类4 多步骤长流程表单 | **0 页**（`<Steps` 全工程 0 命中；用 Modal 内"上一步/下一步"顶替） | **净新增要求**，无样本可抄 |
| 类5 配置类 / 分组表单 | 形态最贴合（`project/pj03`、`system/s12`） | 缺：分组卡说明文字 |
| 类6 对象详情页 | 成熟（`project/pj02`、`implementation/im04`） | 缺：首屏概览卡；返回位置见下 |
| 类7 看板页 | 近乎空白（图表库 0 引入、`Statistic` 仅 `home` 3 处、无页头时间范围） | 基本等于净新增 |
| 公共页 | 仅 `NotFound`（`Result` 404） | 缺：登录 / 个人中心 / 结果页 / 403 / 500 |

**其他硬事实（逐条 grep 复核，可直接采信）**：

- `pagination={false}` 主导全工程，**唯一例外** `archive` 内一个嵌套材料表的 `pagination={{ pageSize: 5 }}`。
- `<Empty` **0 命中** → "空态占位"是净新增要求。
- `page-head` = `global.css:70` 的 `h2.page-title`（20px / 600）+ `p.page-sub`，**结构上不含任何按钮** → 标题右上返回在存量里不存在；`返回列表` / `返回` 共 24 处、分布在 **8 个模块**，位置**全在底部操作栏**。
- 版权行"研发单位：广西计算中心"**仅 `total/v02` 1 处**，不是存量全局习惯。
- 已稳定且应保留的存量优点：独立搜索卡、分组 `Card`、`Descriptions column={2}`、表单一律 `layout="vertical"`、`sticky` 底部操作栏、状态用 `Tag`、表格 `scroll={{x}}` + 操作列 `fixed:'right'`。

### A.0.1　差异处置决定（**用户逐条拍板，2026-09-11，共 18 条 — 本表为准**）

> 三轮问答全部结束。**「决定」列为最终口径，任何后续文档与本表冲突时以本表为准。**
> 「存量回改」列决定 T-5 的范围：`回改` = 存量审计系统同步修；`不回改` = 只约束以后新生成的页面。

| # | 差异项 | 存量做法 | 规范原要求 | 决定 | 存量回改 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | 返回按钮位置 | 底部操作栏，24 处 / 8 模块 | 内页标题右上 | **按规范** | 回改 |
| 2 | 类2 单行工具栏 | 0 例 | 筛≤4 用单行工具栏 | **按规范**；定性为**净新增** | 不回改 |
| 3 | 分页 | `pagination={false}` 27 处 | 分页靠右 + 总条数 | **按规范** | 回改 |
| 4 | 筛选卡展开/收起 | 一律平铺（11 项也平铺） | 筛≥5 加折叠 | **按规范** | 回改 |
| 5 | 表格卡头数量徽章 | 0 处 | 标题 + 数量徽章 + 右侧工具栏 | **按规范** | 回改 |
| 6 | 空字段显示 | `—` | "未填写" | **按存量**（规范改字为 `—`，全库统一） | 不回改 |
| 7 | 长文本省略 | 基本未用 | 省略 + 悬浮显示全文 | **按规范** | 回改 |
| 8 | 表格横向滚动 / 钉列 | 不一致（3 页无 `scroll`、3 页操作列无 `fixed`） | 统一首末列钉住 | **折中口径**：只修**真的会溢出**的页 | 局部 |
| 9 | 详情页状态标签位置 | 在第 4 行字段里 | 内页标题旁 | **按规范** | 回改 |
| 10 | 版权行 | 仅 `total/v02` 1 处 | 全局 | **按规范** | 回改（约 20 页） |
| 11 | 类3 批量提示条 | 0 处 | "已选 N 项" + 批量动作 + 取消 | **按规范** | 不回改（存量仅 2 页有选择，可顺手补） |
| 12 | 空态 `Empty` | 0 命中 | 无数据时空态占位 | **按规范** | 不回改（演示数据不触发） |
| 13 | 表单校验反馈 | 只写 `required`，无 `message` | 校验失败有明确提示 | **按规范** | 新页强制；存量不动 |
| 14 | 详情页首屏概览卡 | 无此层 | 概览卡（关键字段 + 主要操作）打头 | **按规范** | 新页强制；存量不动 |
| 15 | 类4 多步骤长流程表单 | 0 例（无 `Steps`） | 纵向步骤条 + 单步校验 + 末步汇总 | **按规范，保留为必做** | 不回改 |
| 16 | 类7 看板页 | 0 图表、无页头时间范围 | 指标卡等宽 + 2~4 图表 + 时间范围 | **全量按规范**（图表用 ECharts） | 不回改 |
| 17 | 快照 / 只读态 | `SnapshotBar` 6 页在用 | 规范里没有 | **补进规范**（横切模式，见本文末） | 不回改 |
| 18 | 状态机动作按钮组 | `rectify/r06` 13 个按钮按角色+状态启停 | 规范只写到"菜单 / 按钮差异" | **补进规范**（角色差异最强载体，见 §2.3） | 不回改 |

**统计**：按规范 14 条 / 按存量 1 条（第 6 条）/ 折中 1 条（第 8 条）/ 反向补录 2 条（第 17、18 条）。

**由此推导出的两条执行约束**：

1. **T-5 不再是"纯视觉层"**——它现在包含 7 项结构级回改（第 1、3、4、5、7、9、10 条）。已在 §4 T-5 拆为 T-5a / T-5b 并列出精确清单。
2. **`references/prototype-page-types.md` 落盘时必须逐条对齐本表**，尤其第 6 条（`—` 而非"未填写"）与第 8 条（只修溢出页）——这两条是"规范向存量让路"，最容易被后续 AI 改回去。

### 类 1 · 标准查询表格（筛选项 ≥5）

**标准结构**：内页标题 + 右上返回 → **独立搜索卡**（筛选项网格 2~3 列，`展开/收起`，`查询`/`重置` 靠右）→ **表格卡**（卡头 = 标题 + 数量徽章 + 右侧工具栏；表内 = 首末列钉住 + 长文本省略）→ 分页（靠右）→ 底部通栏操作栏 → 操作栏上方版权行

**必须**：筛选 ≥5 时独立成卡且**默认折叠**（`展开` 后显示全部）；卡头有**数量徽章**；**有分页且显示总条数**；`查询`/`重置` 后页码回第 1 页；`重置` 清空全部输入；长文本省略 + 悬浮显示全文；表头不换行；状态/短列有最小宽度；内页标题右上返回

**禁止**：把 ≥5 个筛选塞进单行；表头换行；列挤不下还不上横向滚动；分页状态被筛选操作丢失

### 类 2 · 轻量工具栏表格（筛选项 ≤4）

> ⚠️ **净新增要求**：存量审计系统 **0 例**（所有列表页一律"独立筛选卡"）。本类只约束**以后新生成**的页面，**不回溯改存量**。命中本类时必须真的用单行工具栏，不得退回独立筛选卡。

**标准结构**：内页标题 → **单行工具栏**（左：搜索框 + ≤4 个筛选；右：刷新/列设置 + 主操作按钮）→ 表格卡 → 分页 → 底部操作栏

**必须**：≤4 个筛选与工具栏同一行；主操作按钮带图标 + 文字

**禁止**：为 ≤4 个筛选单独开一张搜索卡

### 类 3 · 批量操作表格

**标准结构**：同 类 1 或 类 2 + 表头复选列 → 选中后出现的**批量提示条**（"已选 N 项" + 批量动作 + 取消）→ 批量动作二次确认

**必须**：选中后出现**批量提示条**（"已选 N 项" + 批量动作 + `取消`），无选中时**不渲染**提示条；批量动作有确认弹窗；危险动作（删除）用危险色按钮 + 二次确认；操作完成清空选择

**禁止**：无确认直接执行删除；批量选择与分页状态互相干扰

### 类 4 · 多步骤长流程表单

> ⚠️ **净新增要求**：存量审计系统 **0 例**（`<Steps` 全工程 0 命中，用 Modal 内"上一步/下一步"顶替）。这是 7 类里**唯一没有任何现成样本可抄**的一类，实现难度最高，排 T-3 最后。

**标准结构**：内页标题 → **纵向步骤条** → 当前步（分区标题 + 字段，label 在上）→ 单步 `上一步`/`下一步` → **末步汇总卡** + 确认项 → 底部操作栏（`保存草稿` / `提交`）

**必须**：单步校验拦截（未填不许下一步）；跨步回退不丢已填数据；草稿暂存；末步汇总可见且可返回修改

**禁止**：把所有步骤塞成一张长表单；校验失败无提示

### 类 5 · 配置类 / 分组表单

**标准结构**：内页标题 → **多个分组卡**（每卡：标题 + 说明 + 字段网格，label 在上）→ 底部操作栏（`取消` / `保存`）

**必须**：每个分组有标题与说明；字段宽度按官方档位（短字段不铺满整行）；文本域整行

**禁止**：一张巨卡塞进所有字段；字段宽度随意

### 类 6 · 对象详情页

**标准结构**：内页标题（标题 + 状态标签 + 右上返回）→ **概览卡**（关键字段 + 主要操作）→ **分组卡片描述列表**（每卡一组；一行两对 label:value）→ 关联数据（表格/列表，按需）→ 底部操作栏

**必须**：首屏有**概览卡**（关键字段 + 主要操作）；**状态标签位于内页标题旁**（不放在字段行里）；只读态可辨；**空字段统一显示 `—`**（⚠️ 不用"未填写"，这是 §A.0.1 第 6 条的存量让路口径）；状态用标签表达

**禁止**：详情页做成可编辑表单（编辑走弹窗/抽屉）

### 类 7 · 看板页（概览 / 驾驶舱）

> ⚠️ **近乎净新增**：存量审计系统图表库 **0 引入**（只有 2 处 `Progress`）、`Statistic` 仅 `home` 3 处、指标卡用 flex 均分而非等宽栅格、页头无时间范围选择器。唯一可参考的是 `total/v02` 的区块划分，但图表与时间范围都得从头写。

**标准结构**：内页标题 + 时间范围 → **指标卡行**（3~5 个等宽）→ **图表区**（2~4 个，2 列网格）→ 待办/异常列表 →（无底部操作栏，或仅"导出"）

**必须**：一屏内可看完；每个图表有标题与时间范围；无数据时有空态占位

**禁止**：**下钻**（用户明确不做）；超过 4 个图表堆成长页

### 公共页

**范围**：登录页、个人中心、结果页（提交成功/失败）、异常页（403/404/500）、任务看板页（原 Kanban，已移出 7 类）

**标准结构**：登录页无三栏壳层、居中卡片；其余与业务页同壳层

**必须**：异常页给出返回入口；结果页给出下一步动作

### 跨类模式 · 快照 / 只读态（**存量有、原 7 类漏了，本次补入**）

存量审计系统已有成熟实现（`src/shared/snapshotView.jsx` 的 `SnapshotBar`，用于 prepare / implementation / report / rectify 共 6 页），原 7 类清单里完全没有这一类，属规范缺口。

**触发**：页面展示的是**已归档的历史版本**或**不可再编辑的记录**。

**标准结构**：**顶部只读横幅**（`sticky` 顶栏，浅色底 + 图标 + 文案"归档快照 · 只读" + 快照时间 / 归档人；快照失效时转警示色）→ 内页标题 → 正文（同所属类的只读形态）→ 底部操作栏（无编辑类按钮，仅 `返回` / `导出`）

**必须**：只读横幅在任何滚动位置都可见（`sticky top`）；正文所有编辑控件转为纯文本展示，**不得渲染禁用输入框**；失效快照给出明确原因

**禁止**：把只读态做成"全部字段 `disabled` 的表单"；横幅随内容滚走

> 该模式可适用于任意一类页面的只读形态，**不占 7 类名额**，与"公共页"并列作为横切模式。

---

## 附录 B　命令速查

```bash
# 建分支
cd /d/work/ShitPM && git checkout -b codex/prototype-skill-v3

# 构建
cd /d/work/ShitPM/templates/prototype-vite && npm run build

# 依赖重装（改 package.json 后）
cd /d/work/ShitPM/templates/prototype-vite && npm ci

# 门禁（模板工程）
cd /d/work/ShitPM && python scripts/python/prototype-source-check.py --project-root .

# 一致性（含 output/prototype 的项目根）
python scripts/python/prototype-consistency-check.py --project-root <项目根>

# 一致性（只给 src 的 harness）
python scripts/python/prototype-consistency-check.py --prototype-src <src 路径>

# 全量回归
for f in scripts/python/test-*.py; do python "$f"; done

# 删除软链的正确方式（勿用 rm -rf，会跟随软链删掉目标）
powershell -NoProfile -Command "[System.IO.Directory]::Delete('<link>', \$false)"
```

---

## 附录 C　v3 变更记录

| 相对 | 变更 |
| :-- | :-- |
| `2026-09-11-antd-official-visual-conformance-plan.md` | **已删除并入**。其"判定规则 / 实测基线对照 / T-1~T-4 步骤"全部纳入本文 §2.4 与 §4 |
| `2026-09-10-…-plan-and-acceptance.md` | 其 **T-2A（ProComponents 路径）废止**；其 **T-0（Tabler 阴影）被 §2.4 覆盖**；保留为历史记录 |
| **本文件 2026-09-11 下午修订** | ①对存量审计系统（12 模块 / 12203 行 JSX）做**逐类实测比对**，新增 **附录 A.0** 存量对照表 + 6 条硬事实；②**三轮问答逐条拍板 18 条差异处置**，形成 **附录 A.0.1 权威决定表**（按规范 14 / 按存量 1 / 折中 1 / 反向补录 2）；③据此修订各类「必须」项：类1 补折叠+徽章+分页总数，类3 补批量提示条，类6 空字段改 `—`、状态标签提到标题旁、补概览卡；④**新增横切模式「快照 / 只读态」**（存量有、原清单漏）；⑤§2.3 补「状态机动作按钮组」为角色差异最强载体；⑥**T-5 由"纯视觉层"扩大为 T-5a 视觉层 + T-5b 规范增量回改（7 项结构级，逐项独立提交可单独回退）**；⑦类 2 / 类 4 标注为**净新增**（存量 0 例，不回改存量） |
| 本文件 v2（同日早版） | 结构改为 9-10 体例（执行前置 / 决策树 / 每步精确命令与期望输出 / 停止条件 / 命令速查），并补 §0.3 已核实事实、§0.4 三条证伪口径、§0.5 基线 |
