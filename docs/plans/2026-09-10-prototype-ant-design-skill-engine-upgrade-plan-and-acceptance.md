# Prototype 生成引擎升级 —— 执行手册（v3）

> 日期：2026-09-10　版本：v3（执行手册版）
> 读者：独立执行模型。**本文件自包含，不依赖任何前置对话上下文。**
> 上游审计依据：`docs/reports/2026-09-10-prototype-pro-engine-plan-audit.md`
>
> **v3 与 v2 的关系**：v2 是论证型计划（含背景、争议、权衡）。v3 只保留**可执行的指令、可判定的验收、明确的分支决策**。执行期间以本文件为准；需要了解"为什么"时再读 v2 论证与审计报告。

---

## 0. 执行前置（必读）

### 0.1 环境绝对路径

| 项 | 值 |
| :-- | :-- |
| 仓库根 | `D:\work\ShitPM`（Git Bash 中写作 `/d/work/ShitPM`） |
| 原型模板工程 | `D:\work\ShitPM\templates\prototype-vite` |
| 主题文件 | `templates\prototype-vite\src\theme\tablerTheme.ts` |
| 共享组件 | `templates\prototype-vite\src\shared\ui\index.jsx` |
| Skill 源（唯一改这里） | `D:\work\ShitPM\skills\spm-prototype\SKILL.md`、`D:\work\ShitPM\skills\spm-prototype-review\SKILL.md` |
| Skill 已安装副本 | `C:\Users\guduj\.workbuddy\skills\spm-prototype\SKILL.md`（**与源仓库内容一致，改完源后需同步复制**） |
| 评审清单 | `D:\work\ShitPM\contracts\prototype-review-checklist.md` |
| 行为规范 | `D:\work\ShitPM\references\prototype-component-behavior.md` |
| 实验基线 | `D:\work\ShitPM\experiments\antd-tabler-efficiency\` |
| 门禁脚本 | `D:\work\ShitPM\scripts\python\prototype-consistency-check.py`、`prototype-source-check.py` |

**Python / Node**：直接用 `python`、`npm`、`node`，执行前用 `python -V`、`npm -v` 自检。实验目录 `node_modules` 是指向 `templates/prototype-vite/node_modules` 的符号链接，**依赖必须装在模板工程**，实验目录自动共享。

### 0.2 硬约束（违反即任务失败）

1. **全程在分支 `codex/upgrade-prototype-pro-engine` 上工作**，先 `git checkout -b codex/upgrade-prototype-pro-engine`。
2. **不得 push**（用户规则：未 commit 前禁止 push；本次一律不 push，合入 `main` 前等用户拍板）。
3. **不得删除 `.workbuddy/` 目录**。
4. **不得新增检查脚本、报告 JSON、回执或门禁**（仓库 `AGENTS.md` §1 精简原则）。本手册所有验收均使用**现有**脚本。
5. **不得修改 Design 事实源**（`output/design/` 下任何文件）。
6. `prototype-consistency-check.py` 的**分类语义不得改变**，只允许扩展锚点解析来源（T-2A-4）。

### 0.3 已核实的事实（执行时直接采信，不要重新验证）

| 事实 | 值 | 来源 |
| :-- | :-- | :-- |
| 项目 antd 版本 | `^6.6.0` | `templates/prototype-vite/package.json` |
| pro-components `latest` | `2.8.10`，peer `antd ^4.24.15 \|\| ^5.11.2` → **与 antd 6 冲突** | npm registry |
| pro-components `beta` | `3.1.14-7`（2026-08-28 发布），peer `antd ^6.0.0`、`react >=18` | npm registry dist-tags |
| 官方 Skill 仓库 | `https://github.com/AntGroupDesign/Ant-Design-Skill`，`scripts/` 下 **32 个 TSX 模板** | GitHub API |
| 官方模板依赖 | 基于 `ProTable` / `ProColumns`（`@ant-design/pro-components`） | 模板源码首行 |
| 官方模板自带基线 | `colorPrimary:'#1677ff'`（antd 5 默认蓝）、`global-style.css` 76KB | 模板源码 |
| consistency-check 退出码 | `0`=无静态冲突（`possible_omission` 也返回 0）、`1`=deterministic_conflict、`2`=致命错误 | 脚本 L486-492 |

### 0.4 ⚠️ 基线实测：原"代码行数下降 ≥50%"目标已作废

执行前必须知道，**v2 的核心量化目标建立在错误前提上**：

| 组 | src 总行数 | 业务页合计 | 代表性业务页 `ProblemList.jsx` |
| :-- | --: | --: | --: |
| A 组（裸 antd，无护栏） | 1388 | 722 | 99 |
| C 组（现状：shared/ui + Tabler 主题） | 1406 | 725 | **102** |

实测命令（可复现）：

```bash
cd /d/work/ShitPM/experiments/antd-tabler-efficiency
wc -l A-pure-antd/src/modules/*/*.jsx C-converged/src/modules/*/*.jsx
```

**结论**：现状业务页已经是 **~100 行**，不是 v2 假设的 300~500 行——`shared/ui` 早就把抽象做掉了。而且 C 组比 A 组**多 3 行**，引入护栏并未增加行数。

因此：

- **"单页代码行数下降 ≥50%"（即降到 ≤51 行）物理上不可达，已废止。**
- 行数降级为**观测项**（只记录，不作放行门槛）。
- 放行主指标改为：**首次运行缺陷数**、**返工轮次**、**生成 Token**、`possible_omissions` 变化（见 §6.2）。

> 若执行中实测发现某个具体页面确实超过 300 行，可在验收报告里单独记录该页，但不得据此恢复行数门槛。

---

## 1. 任务总览与决策树

```text
T-0  Tabler 阴影对齐 ──────► 无条件执行（不依赖任何探针）
                                    │
                                    ▼
T-1  阶段 0 探针（半天）────► Go / No-Go 门禁
                                    │
              ┌─────────────────────┴─────────────────────┐
              │ GO                                        │ NO-GO
              ▼                                            ▼
   T-2A 全面实施（引入 ProComponents）          T-2B 备选（不引包）
   T-2A-1 锁定依赖 + ProConfigProvider          T-2B-1 移植官方规范进 behavior.md
   T-2A-2 转写 6 个模板 + 剥离清单              （仅文字规则，代码仍用 shared/ui）
   T-2A-3 阴影已在 T-0 完成                     T-2B-2 验收（同 §6，行数指标不适用）
   T-2A-4 扩展 columns 锚点解析
   T-2A-5 重建 behavior.md 章节
   T-2A-6 改写 spm-prototype SKILL.md
   T-2A-7 同步评审侧（review SKILL + checklist）
   T-2A-8 A/B 实验 + 真实项目回归
              │                                            │
              └─────────────────► T-3 验收 ◄───────────────┘
                                    │
                                    ▼
                          T-4 输出验收报告（等用户拍板合入）
```

**执行顺序铁律**：T-0 先行且独立验收；T-1 未通过 GO 前，**禁止**触碰 T-2A 的任何文件（T-2A 全部以引入 ProComponents 为前提）。

---

## 2. T-0　Tabler 官方阴影对齐（无条件执行）

**目标**：把阴影体系对齐 Tabler 官方。**色值、圆角、字号经实测已全部一致，不动**。

### 2.1 现状

`tablerTheme.ts` 的**全局 token 三兄弟已改完**（`boxShadowCard` / `boxShadow` / `boxShadowSecondary`，L53-56），但**组件级与 CSS 变量仍有 6 处旧值残留**，且缺 hover 阴影。

### 2.2 精确改动清单（逐条执行）

文件：`D:\work\ShitPM\templates\prototype-vite\src\theme\tablerTheme.ts`

| # | 行号 | 字段 | 现值（旧） | 改为 |
| :-: | :-- | :-- | :-- | :-- |
| 1 | 66 | `Button.primaryShadow` | `0 1px 1px rgba(31,41,55,0.06)` | `0 1px 2px 0 rgba(18,18,23,0.05)` |
| 2 | 67 | `Button.defaultShadow` | `0 1px 1px rgba(31,41,55,0.06)` | `0 1px 2px 0 rgba(18,18,23,0.05)` |
| 3 | 74 | `Card.boxShadow` | `0 0 4px rgba(31,41,55,0.04)` | `0 1px 2px 0 rgba(18,18,23,0.05)` |
| 4 | 124 | `Input.boxShadow` | `0 1px 1px rgba(31,41,55,0.06)` | `0 1px 2px 0 rgba(18,18,23,0.05)` |
| 5 | 143 | `--card-shadow` | `0 0 4px rgba(31,41,55,0.04)` | `0 1px 2px 0 rgba(18,18,23,0.05)` |
| 6 | 144 | `--control-shadow` | `0 1px 1px rgba(31,41,55,0.06)` | `0 1px 2px 0 rgba(18,18,23,0.05)` |
| 7 | 新增 | `--card-shadow-hover`（在 `tablerCssVars` 中，`--card-shadow` 之后） | 无 | `0 4px 6px -2px rgba(18,18,23,0.05), 0 10px 15px -3px rgba(18,18,23,0.08)` |

**不要改**：`Input.activeShadow`（L125，`0 0 0 2px rgba(6,111,209,0.25)`，是品牌蓝聚焦环，非阴影体系）。

**同步要求**：若 `--card-shadow` 被 `src/global.css` 或壳层引用 hover 效果，新增的 `--card-shadow-hover` 需一并在消费处接入；先 grep 确认消费点：

```bash
cd /d/work/ShitPM/templates/prototype-vite && grep -rn "card-shadow\|control-shadow" src/
```

### 2.3 T-0 验收

```bash
cd /d/work/ShitPM/templates/prototype-vite

# V-T0-1：旧阴影色必须清零
grep -c "rgba(31,41,55" src/theme/tablerTheme.ts
# 期望输出：0

# V-T0-2：新基准色出现次数（6 改 + 2 全局 + 注释）
grep -c "rgba(18,18,23" src/theme/tablerTheme.ts
# 期望输出：≥ 5

# V-T0-3：hover 阴影存在
grep -c "card-shadow-hover" src/theme/tablerTheme.ts
# 期望输出：≥ 1

# V-T0-4：构建通过
npm run build
# 期望：退出码 0，无 Error
```

**判定**：4 项全过 → T-0 完成，commit（`git commit -m "theme: align Tabler official shadow tokens"`）。任一不过 → 修正后重跑，**不得带病进入 T-1**。

---

## 3. T-1　阶段 0 可行性探针（Go / No-Go 门禁）

**目标**：用最小成本证伪/证实两项架构级风险。
- **R-A**：beta 依赖能否装上并构建通过（antd 6 兼容性）。
- **R-B**：改用 ProTable 后，一致性锚点丢失多少、门禁是否变弱。

**前置**：T-0 已完成并通过。分支已创建。

### 3.1 执行步骤

**Step 1 · 安装 beta 依赖（在模板工程内）**

```bash
cd /d/work/ShitPM/templates/prototype-vite
npm i @ant-design/pro-components@3.1.14-7 --save-exact
```

**Step 2 · 验证安装结果**

```bash
npm ls @ant-design/pro-components
# 期望：@ant-design/pro-components@3.1.14-7，且无 ERESOLVE / peer 警告
```

若出现 `ERESOLVE` → **立即停止，判 NO-GO**，记录错误原文，转 T-2B。不要尝试 `--legacy-peer-deps` 或 `--force` 绕过（绕过会让 beta 与 antd 6 的不兼容在运行时才爆，风险不可控）。

**Step 3 · 验证 ProTable 导出存在**

```bash
npm view @ant-design/pro-components@3.1.14-7 dependencies --json
node -e "console.log(Object.keys(require('@ant-design/pro-components')).join(','))"
# 期望：输出中含 ProTable
```

**Step 4 · 移植一个模板做样本**

从官方仓库取 `table/06-ToolbarTable.tsx` 作为样本，落到 `templates/prototype-vite/src/modules/demo/ProbeTable.jsx`，并**严格执行剥离清单**（§3.2）。

取文件（GitHub API，raw 在部分网络下会返回空，用 API）：

```bash
curl -s "https://api.github.com/repos/AntGroupDesign/Ant-Design-Skill/contents/ant-design-skill/scripts/table/06-ToolbarTable.tsx?ref=main" \
| python -c "import json,sys,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode('utf-8'))" \
> /d/work/ShitPM/templates/prototype-vite/src/modules/demo/_probe_source.tsx
```

**Step 5 · 接入主题并构建**

```bash
cd /d/work/ShitPM/templates/prototype-vite && npm run build
```

**Step 6 · 锚点丢失量实测**

在探针页上按 §5（T-2A-4 方案）标注 `dataField`，然后对比"标注前 / 标注后"的 `possible_omissions` 数量。

### 3.2 剥离清单（强制，逐项检查）

官方模板移植时必须删除以下内容，**残留即判失败**：

| 剥离项 | 判据 |
| :-- | :-- |
| `import ... global-style.css` | 文件中不得出现 `global-style` |
| 模板内 `const xxxTheme = { token: {...} }` 常量 | 不得出现 `colorPrimary` |
| `<ConfigProvider theme={xxxTheme}>` | 不得出现模板自带的 `ConfigProvider` |
| 官方 antd5 蓝 `#1677ff` | 全文不得出现 |
| mock 数据（`tableListDataSource`、"应用A"、"负责人A" 等） | 全部替换为 Design 字段 |
| TS 语法（`ProColumns<T>[]`、类型标注、interface） | 转 JSX 后不得残留 |
| 非 `@tabler/icons-react` 的图标导入 | 统一替换为 `@tabler/icons-react` |

自动化检查：

```bash
cd /d/work/ShitPM/templates/prototype-vite/src/modules/demo
grep -n "global-style\|colorPrimary\|#1677ff\|tableListDataSource\|ConfigProvider" ProbeTable.jsx
# 期望：无输出（0 命中）
```

### 3.3 T-1 验收与门禁

```bash
# V-T1-1 依赖
npm ls @ant-design/pro-components | grep -q "3.1.14-7" && echo PASS || echo FAIL

# V-T1-2 构建
npm run build >/dev/null 2>&1 && echo PASS || echo FAIL

# V-T1-3 主题未被污染：产物中不得出现 antd5 默认蓝
grep -rq "#1677ff" dist/ && echo FAIL || echo PASS

# V-T1-4 剥离清单
grep -q "global-style\|colorPrimary\|#1677ff" src/modules/demo/ProbeTable.jsx && echo FAIL || echo PASS
```

| 门禁 | 判定 |
| :-- | :-- |
| **GO** | V-T1-1/2/3/4 全 PASS → 进入 T-2A |
| **NO-GO** | 任一 FAIL → 删除探针文件、卸载依赖（`npm uninstall @ant-design/pro-components`），转 **T-2B** |

**NO-GO 后必须清理**：`git status` 中不得残留探针文件与 `package.json` / `package-lock.json` 的改动（T-0 的改动保留）。

---

## 4. T-2A　全面实施路径（仅 T-1 判 GO 后执行）

### T-2A-1　依赖锁定与 Provider 接入

1. `package.json` 中 `@ant-design/pro-components` 必须是 `3.1.14-7`（**精确值，不得带 `^`**）。用 `--save-exact` 安装已保证；完成后人工确认一次。
2. `src/App.jsx`（或 `main.jsx`）接入 `ProConfigProvider`，与既有 `ConfigProvider` 嵌套。**`tablerTheme` 必须是唯一视觉入口**，Pro 侧不得传 `theme`。
3. 验证：`npm run build` 退出码 0。

### T-2A-2　模板转写（6 个）

目标目录：`templates/prototype-vite/src/shared/templates/`（新建）。

| 本库模板（JSX） | 官方来源（`ant-design-skill/scripts/`） |
| :-- | :-- |
| `QueryFilterTable.jsx` | `form/05-QueryFilter.tsx` + `table/06-ToolbarTable.tsx` |
| `ToolbarTable.jsx` | `table/06-ToolbarTable.tsx` |
| `VerticalStepsForm.jsx` | `form/03-VerticalStepsForm.tsx` |
| `EmbedForm.jsx` | `form/04-EmbedForm.tsx` |
| `BatchTable.jsx` | `table/04-BatchTable.tsx` |
| `GroupedCardDescriptions.jsx` | `description-list/03-GroupedCardDescriptions.tsx` |

每个模板转写后必须通过 §3.2 剥离清单的同款 grep 检查。**六个模板全部转写完再统一 build**，不要边写边改主题。

### T-2A-3　阴影

T-0 已完成，本步无操作。若 T-0 因故跳过，必须先补完 T-0。

### T-2A-4　一致性锚点机制改造（对应 R-B）

**问题**：`prototype-consistency-check.py` 只从 **JSX/HTML 标签属性**提取 `data-field`；ProTable 的 `columns` 是 JS 对象数组，锚点会大面积丢失。且"Design 有、源码未标"落入 `possible_omissions`（退出码 0，**不阻断**），会导致指标变好看而防幻觉能力变弱。

**采用方案一**：约定 `columns` 每项携带 `dataField`：

```js
{ title: '审计问题名称', dataIndex: 'name', dataField: '审计问题名称' }
```

**脚本改动范围（最小化）**：只在 `prototype-consistency-check.py` 的锚点提取环节增加一条来源——从 `columns` 数组（JS 源码文本）中解析 `dataField: '...'`。**不得修改分类语义**（`deterministic_conflicts` / `possible_omissions` / `needs_semantic_judgment` 的归属规则不变）。

**验收**：与 C 组基线同口径对比，同一页面 `possible_omissions` **不得增加**。

### T-2A-5　重建 `behavior.md` 章节

文件：`D:\work\ShitPM\references\prototype-component-behavior.md`

现状：5,305 字节，4 个二级章节（§2 下有 3 个三级子节）。需要新增 6 个专属章节以支撑渐进装载路由表：

| 页面类型 | 需建章节 | 起步模板 | 单章体积上限 |
| :-- | :-- | :-- | :-- |
| 标准查询表格（筛选项 ≥5） | 表格与 QueryFilter 选型 | `QueryFilterTable.jsx` | 4KB |
| 轻量工具栏表格（筛选项 ≤4） | 单行工具栏与表头对齐 | `ToolbarTable.jsx` | 4KB |
| 多步骤长流程表单 | 分步表单与步骤校验 | `VerticalStepsForm.jsx` | 4KB |
| 配置类 / 分组表单 | 嵌入表单与分区 | `EmbedForm.jsx` | 4KB |
| 对象详情页 | 分组描述列表 | `GroupedCardDescriptions.jsx` | 4KB |
| 批量操作表格 | 批量操作与行选择 | `BatchTable.jsx` | 4KB |

**铁律**：章节与路由表**同批交付**。只写路由表不建章节，模型会读到空章节后自由发挥——比没有路由表更糟。

内容来源：官方 `references/` 实测 354KB（`components_Table.md` 52KB、`components_Form.md` 45KB），**禁止整篇拷贝**，必须按上表切分。核心要吸收的确定性规则：筛选临界值（≤4 项单行工具栏 vs ≥5 项独立搜索卡）、桌面端抽屉操作区置顶、表格卡头部三要素（实体标题 / 数量 / 操作）、表体单行 ellipsis + Tooltip。

### T-2A-6　改写 `spm-prototype/SKILL.md`

必须写入 4 项：

1. **渐进装载路由表**（§T-2A-5 表格），每次任务只装载 1 个微规范 + 1 个模板；
2. **"模板起步"强制规则**：凡存在适用模板的场景，必须以模板为起点，只替换业务字段与配置（移植官方 SKILL.md 既有强制条款）；
3. **无模板回退契约**：未命中模板时沿用 `shared/ui` + 原生 antd，并在交付说明中记录"未命中模板"；
4. **shared/ui 处置清单**（下表）。

`src/shared/ui/index.jsx` 现有 11 个组件，处置规则：

| 组件 | 处置 |
| :-- | :-- |
| `PageHeader` / `SectionCard` / `MetricCard` / `ActionBar` / `PageFooter` | **保留**（项目组习惯，官方模板无对应物） |
| `StatusTag` / `IconButton` / `EmptyState` | **保留**（已收敛 Tabler 视觉，无替换收益） |
| `DataTable` | **过渡期并存**：Pro 场景用 `ProTable`，其余沿用 `DataTable` |
| `RowActions` / `FormSection` | **保留**（ProTable 操作列 / ProForm 分区内复用） |

**硬约束**：同一页面内**不得** `DataTable` 与 `ProTable` 混用。

**改完后必须同步副本**：

```bash
cp /d/work/ShitPM/skills/spm-prototype/SKILL.md /c/Users/guduj/.workbuddy/skills/spm-prototype/SKILL.md
```

### T-2A-7　评审侧同步（与 T-2A-6 同批，不可分批）

分批会产生"按新规生成、按旧规评审"的错位期。

**保留不动**：`spm-prototype-review/SKILL.md` 第 4 步关于 `possible_omissions` / `needs_semantic_judgment` 的口径——它写的是"必须逐项给出判断，不能因退出码 0 视为通过"，**这是正确口径，不得修改**。

**待补内容**：

| # | 文件 | 位置 | 改动 |
| :-: | :-- | :-- | :-- |
| 1 | `contracts/prototype-review-checklist.md` | 第 15 条 | 补充锚点来源：ProTable 字段锚点可来自 `columns[].dataField`，不得因锚点不在 JSX 标签上即判"未授权" |
| 2 | 同上 | 第 18 条 | 扩展触发证据：第三方组件自带视觉基线覆盖主题（ProComponents 原生蓝、模板 `theme` 残留、引入 `global-style.css`） |
| 3 | 同上 | 第 22 条 | 扩展：页面手写 ProComponents 已承担的实现（筛选 / 分页 / 重置 / 提交状态机），与"复制共享 UI 已承担的实现"同类 |
| 4 | 同上 | 新增第 24 条 | **模板起步与模板残留**：① 有适用模板却从零手写；② 模板 mock 数据 / 示例字段残留（按幻觉处理）；③ 模板 `theme` 常量或 CSS 未剥离。默认 P2，**mock 残留按幻觉升 P1** |
| 5 | `skills/spm-prototype-review/SKILL.md` | 第 4 步 | 补充：ProTable 场景下 `possible_omissions` 增加属**已知架构风险**，应结合 `columns` 源码逐项判断，不得一律记为遗漏 |

同步副本：

```bash
cp /d/work/ShitPM/skills/spm-prototype-review/SKILL.md /c/Users/guduj/.workbuddy/skills/spm-prototype-review/SKILL.md
```

### T-2A-8　A/B 实验与真实项目回归

1. 使用 `experiments/antd-tabler-efficiency/EXPERIMENT_INPUT.md` 作为输入，生成组 D（升级后），与 **C 组**对比（**不是 A 组**——A 组是裸 antd 下界，不是现状基线）。
2. 记录：生成 Token、耗时、代码行数（观测项）、五类缺陷计数、`possible_omissions`。
3. 真实项目回归：选一个未实现的高难度页面（多步表单或复杂表格），跑通 `prototype-source-check.py` 与 `prototype-consistency-check.py`。

---

## 5. T-2B　备选路径（仅 T-1 判 NO-GO 后执行）

**不引入 ProComponents**，只移植官方**规范与结构规则**，代码继续用 `shared/ui` + 原生 antd。

**执行内容**：

1. 把官方确定性规则写进 `references/prototype-component-behavior.md`：筛选临界值（≤4 项工具栏 vs ≥5 项搜索卡）、表头三要素、表体单行 ellipsis+Tooltip、桌面端抽屉操作区置顶、卡片对齐线。
2. T-0 的阴影对齐已完成，本路径**照常受益**。
3. 按 T-2A-5 的章节表建章节，但不绑定 ProTable 模板（起步骨架改为 `shared/ui` 现有组件组合）。

**T-2A-7 评审侧同步整体取消**——全部新增检查项都以 ProComponents 为前提，无 Pro 场景下是恒定噪音。

**验收**：走 §6.1 工程与交互验收；§6.2 中"代码行数""Token 下降"两项**不适用**，只验缺陷数与 `possible_omissions`。

**代价**：放弃"状态机零手写"与代码量下降。实施成本约为 T-2A 的三分之一。

---

## 6. 验收方案（T-3）

### 6.1 工程与交互验收（T-2A / T-2B 通用）

```bash
cd /d/work/ShitPM/templates/prototype-vite
npm run build; echo "build exit=$?"      # 期望 0

cd /d/work/ShitPM
python scripts/python/prototype-source-check.py --project-root <真实项目根>
echo "source-check exit=$?"               # 期望 0

python scripts/python/prototype-consistency-check.py --project-root <真实项目根>
echo "consistency exit=$?"                # 期望 0（1=有冲突，2=致命错误）
```

> `prototype-consistency-check.py` 退出码 0 **不代表无遗漏**：`possible_omissions` 也返回 0。必须读 JSON 输出里的 `classification.possible_omissions` 人工逐项判断。

**交互清单**（真实浏览器，逐条打勾）：

- [ ] 点击搜索准确筛选；点击重置清空表单并**自动重新拉取全量数据**
- [ ] 切换筛选项或重置时，当前页码自动回到 1
- [ ] 桌面端抽屉"确定/取消"固定在 Header 右侧，长表单滚动时不脱离视口、不抖动
- [ ] 长文本 `ellipsis + Tooltip`，不撑高行高
- [ ] 分步表单：完成态/当前态清晰，校验未通过无法进入下一步，支持草稿暂存
- [ ] 浏览器 Console **0 Errors**（含打开所有 Modal / Drawer / 下拉）

**Tabler 视觉清单**：

- [ ] 主色 `#066fd1`，**无 `#1677ff` 残留**（重点查 ProTable 链接、分页选中、聚焦环）
- [ ] 卡片阴影 `0 1px 2px 0 rgba(18,18,23,.05)`，hover 升为 `--card-shadow-hover`
- [ ] 输入框 / 按钮阴影 `0 1px 2px 0 rgba(18,18,23,.05)`
- [ ] 下拉 / 浮层为四层 `--tblr-shadow-dropdown`
- [ ] 控件圆角 6px、卡片 8px、Tag 4px，未被 Pro 内部样式覆盖
- [ ] 表头底 `#f9fafb`（**非** `#fafafa`）
- [ ] 页面无 `global-style.css` 引入，无模板 `theme` 常量残留

### 6.2 放行阈值

| 指标 | 门槛 | 判定方式 |
| :-- | :-- | :-- |
| `deterministic_conflicts` | **必须为 0** | 脚本 JSON |
| `possible_omissions` | **不得比 C 组基线增加** | 脚本 JSON，同口径对比 |
| 首次运行缺陷数（五类计数） | **≤ 1** | 人工 + 浏览器 |
| 高危缺陷（重置失效 / 分页未归位） | **必须为 0** | 人工 + 浏览器 |
| `npm run build` | 退出码 0 | 命令 |
| Console Errors | 0 | 浏览器 |
| 生成 Token | 下降 ≥ 30%（观测，非硬门槛） | 实验记录 |
| 单页代码行数 | **不设门槛，仅记录** | 见 §0.4 |

> v2 中的"代码行数下降 ≥50%""端到端耗时下降 ≥30%"已废止。行数因基线仅 ~102 行而不可达（§0.4）；耗时受模型与网络波动影响，不构成稳定判据。

### 6.3 交付物

`docs/reports/2026-09-10-prototype-pro-engine-acceptance.md`，内容：

1. T-1 探针结果（GO / NO-GO + 证据原文）；
2. 走了哪条路径（T-2A / T-2B）；
3. §6.1 全部清单的逐条结果；
4. §6.2 阈值表（填实测值，含代码行数观测值）；
5. 未解决项与建议。

---

## 7. 停止条件与回滚

**立即停止并回滚**：

- `npm i` 出现 `ERESOLVE` 且无官方支持路径（**禁止用 `--legacy-peer-deps` / `--force` 绕过**）；
- `npm run build` 出现无法优雅解决的打包错误或严重 CSS 污染；
- 引入 ProComponents 后模型频繁遗漏 Design 业务状态，且 T-2A-4 锚点机制无法纠偏；
- 模型频繁编造非法 Pro Props，返工轮次反超基线；
- 发现必须新增报告 / 回执 / 中间件才能运转（违反 §0.2 第 4 条）。

**回滚动作**：

```bash
cd /d/work/ShitPM
git checkout -- templates/prototype-vite/package.json templates/prototype-vite/package-lock.json
rm -rf templates/prototype-vite/src/shared/templates
git status        # 确认除 T-0 与 behavior.md 的改动外无残留
```

主干不留半成品依赖。T-0（阴影对齐）与 `behavior.md` 规范增强属**正向收益**，即使 T-2A 回滚也**保留**。

---

## 附录 A　官方模板全清单（32 个，2026-09-10 核实）

`https://github.com/AntGroupDesign/Ant-Design-Skill` → `ant-design-skill/scripts/`

```text
charts/            00-OnlyChartsBlock  01-BasicStatisticCard  02-IconStatisticCard
                   03-TotalStatisticCard  04-NestedStatisticCard  05-TabsStatisticCard
description-list/  01-BasicDescriptions  02-EditableDescriptions  03-GroupedCardDescriptions
form/              01-BasicForm  02-HorizontalStepsForm  03-VerticalStepsForm
                   04-EmbedForm  05-QueryFilter  06-LoginForm
layout/            MixedLayout  SideLayout  TopLayout
list/              01-BasicList  02-EditList  03-ToolbarList  04-ExpandableList
                   05-SelectableList  06-QueryList  07-VerticalList  08-CardList
table/             01-BasicTable  02-FilterSortTable  03-NestedTable
                   04-BatchTable  05-DragSortTable  06-ToolbarTable
```

取文件统一用 GitHub Contents API（raw 在部分网络返回空）：

```bash
curl -s "https://api.github.com/repos/AntGroupDesign/Ant-Design-Skill/contents/ant-design-skill/scripts/<路径>.tsx?ref=main" \
| python -c "import json,sys,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode('utf-8'))"
```

## 附录 B　基线实测数据（2026-08-28 产物，可直接读取）

```text
experiments/antd-tabler-efficiency/
  A-pure-antd/    src 1388 行   业务页合计 722   ProblemList.jsx 99 行
  C-converged/    src 1406 行   业务页合计 725   ProblemList.jsx 102 行
  EXPERIMENT_INPUT.md   统一输入
  A-prompt.md / C-prompt.md
```

**C 组 = 现状基线**（原生 antd + shared/ui + Tabler 主题）。**A 组仅作下界参考**（其 prompt 要求"不需要任何共享组件"，但工程仍自带 shared/ui，故不代表真实无护栏状态）。

## 附录 C　命令速查

```bash
# 建分支
cd /d/work/ShitPM && git checkout -b codex/upgrade-prototype-pro-engine

# 装依赖
cd templates/prototype-vite && npm i @ant-design/pro-components@3.1.14-7 --save-exact

# 构建
npm run build

# 门禁
python scripts/python/prototype-source-check.py --project-root <项目根>
python scripts/python/prototype-consistency-check.py --project-root <项目根>

# 同步 skill 副本
cp skills/spm-prototype/SKILL.md /c/Users/guduj/.workbuddy/skills/spm-prototype/SKILL.md
cp skills/spm-prototype-review/SKILL.md /c/Users/guduj/.workbuddy/skills/spm-prototype-review/SKILL.md
```

## 附录 D　v2 → v3 变更记录

| 项 | v2 | v3 |
| :-- | :-- | :-- |
| 文档性质 | 论证型计划（含背景/争议/权衡） | 执行手册（指令 + 验收 + 决策树） |
| 代码行数目标 | 下降 ≥50%（硬门槛） | **废止**，降级为观测项（实测基线仅 102 行，不可达） |
| 端到端耗时目标 | 下降 ≥30% | **废止**（受模型/网络波动，非稳定判据） |
| 主指标 | 行数 + Token | 缺陷数 + 返工轮次 + `possible_omissions` |
| Token 目标 | 下降 ≥40% | 下降 ≥30%，且降级为**观测项** |
| T-0 | 未独立 | 独立为无条件执行任务，给出 7 条精确改动 |
| 依赖版本 | 由探针决定 | 明确 `3.1.14-7` + `--save-exact` + 禁止 `--legacy-peer-deps` |
| 探针门禁 | 描述性 | 4 条命令化验收 + GO/NO-GO 判定表 |
| 取模板方式 | 未写 | 给出 GitHub Contents API 命令（raw 会返回空） |
| 官方模板数 | 29 | **32**（实测校正） |
| 争议与权衡章节 | §10 | 移出，需要时读 v2 或审计报告 |
