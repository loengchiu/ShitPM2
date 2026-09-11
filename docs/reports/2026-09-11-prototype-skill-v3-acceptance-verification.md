# Prototype Skill v3 独立验收报告（2026-09-11）

> 被验收对象：`docs/reports/2026-09-11-prototype-skill-v3-acceptance.md`（执行方自评结论：PASS）
> 执行手册：`docs/plans/2026-09-11-prototype-skill-v3-plan-and-acceptance.md`
> 验收人：独立第三方（不复用执行方任何探针脚本）
> **结论：不通过（REJECTED）** —— 1 项事实性错误写入运行时规范 + 3 项未完成/不达标 + 4 处报告陈述与实测不符。

## 一、验收方法（独立复现，不使用执行方脚本）

| 手段 | 说明 |
| :-- | :-- |
| 浏览器实测 | 自写 5 个 playwright 探针（4 轮本地 + 1 轮线上），逐元素取计算样式，非复用 `.tmp/visual-check.py` |
| 源码级验证 | 直接读 `node_modules/@rc-component/table` 与 `antd` 源码确认 API 行为，非依赖文档推断 |
| 对撞实验 | 用 `renderToStaticMarkup` 对同一 columns 施加不同 `fixed` 取值，比对字节数 |
| 静态复核 | 12 套回归套件 / source-check / consistency-check / `npm run build` / 禁词扫描 |
| 交付复核 | 线上 `https://audit-system-prototype.pages.dev` 真实 Chromium 打开 |

## 二、复现通过项（执行方结论成立）

| 项 | 实测证据 |
| :-- | :-- |
| ProComponents 已卸载 | `package.json` 依赖仅 `@ant-design/icons / antd / dayjs / echarts / react / react-dom`；运行时禁词 0 命中 |
| 图标统一官方 | 本地与线上 `svgOutsideAnticon = 0`；审计工程 `@tabler/icons-react` 0 命中；两工程 `shared/icons/index.jsx` 在位 |
| 控件高度 32px | 模板与线上实测 `btnH = 32`、`inputH = 32`、`selectH = 32` |
| 主色 / 页面底 | `rgb(6, 111, 209)`、`rgb(249, 250, 251)`，且无 `#1677ff` / `#1890ff` 泄漏 |
| 浮层阴影 | 实测 `rgba(0,0,0,0.08) 0 6px 16px, rgba(0,0,0,0.12) 0 3px 6px -4px, rgba(0,0,0,0.05) 0 9px 28px 8px` = antd 官方 `boxShadowSecondary`，**非** `rgba(18,18,23)` |
| 字体栈 | `.ant-app` 及全部 antd 组件为官方栈（`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto…`），不含 Inter；`body` 呈 `Times New Roman` 但**不承载可见文本**，判定成立 |
| console | 本地与线上均 0 error / 0 warning |
| 角色差异（核心项） | 菜单：管理员 2 项 → 一线操作员 1 项（消失非置灰）；按钮：`/detail` 掉「编辑」、`/` 16 → 3；字段：`/detail` 掉「联系人 / 联系电话」；数据范围：首页出现「以下仅显示本人负责的 1 条任务」，行数收窄；切换 URL 不变（无刷新） |
| 钉列生效 | 线上 `.ant-table-cell-fix-end` 实测 5 / 4 个细胞 |
| 线上交付 | HTTP 200；`返回列表` 与标题 `年度计划详情` **同一水平行**（T-5b #1 落地）；分页「共 4 条」（#3 落地）；长文本 `ellipsis` 细胞 6 个（#7 落地） |
| 静态工具 | `source-check` 全 PASS exit 0；`consistency-check` `deterministic_conflicts = 0` / `possible_omissions = 0` |
| 构建 | 模板 `npm run build` exit 0；体积 2,342.38 kB / gzip 758.80 kB（卸载 Pro 后回落至 HEAD 2,319.71 kB 量级） |
| 回归套件 | 12 套件 **11 绿 1 红**（红项见 §三.6） |

## 三、不通过项

### 1. 【事实性错误】F4 结论错误，且已写入运行时规范

**执行方结论**：「antd 6 的 rc-table 只认 `fixed: 'start' | 'end'`；写 `'left'/'right'` 不报错但静默失效，存量 19 处 + 模板 2 处全部中招，钉列实际从未生效」，并据此改了 21 处 + 写入规范 + 建议其他项目排查。

**实测反证（两条独立证据）**：

1. 源码：`node_modules/@rc-component/table/es/hooks/useColumns/index.js:43`
   ```js
   const parsedFixed = fixed === true || fixed === 'left' ? 'start' : fixed === 'right' ? 'end' : fixed;
   ```
   旧值被**归一化**，从未失效。
2. 对撞实验（SSR 同 columns 不同取值）：
   ```
   fixed='left'   → ["ant-table-cell-fix-end","ant-table-cell-fix-start"] | bytes: 2258
   fixed='start'  → ["ant-table-cell-fix-end","ant-table-cell-fix-start"] | bytes: 2258
   fixed='right'  → ["ant-table-cell-fix-end"]                            | bytes: 2246
   fixed='end'    → ["ant-table-cell-fix-end"]                            | bytes: 2246
   ```
   同值输出**字节数完全相同**，即完全等价。

**真实根因**：钉列不渲染是**该表没有横向溢出**（缺 `scroll={{ x }}` 或列宽总和不超容器），被误诊为 API 取值变更。执行方引用的"实测 `ant-table-cell-fix-end` 类渲染正常"只证明新值可用，**不能证明旧值失效**——单向验证冒充了双向验证。

**影响**：错误结论进入 `references/prototype-page-types.md`（运行时加载），会持续误导后续所有原型生成；报告 §七 #5 建议其他 antd6 项目排查 `fixed` 取值，属错误扩散。

**处置（本次已修）**：`references/prototype-page-types.md:43` 已更正为"两值等价、团队统一写 `start/end`；钉列不渲染先查溢出条件"。审计工程 19 处改动**语义等价、无需回滚**（属无效改动，非破坏）。

### 2. 【未完成】T-5a「同步主题文件」实际未执行

执行方自评「T-5a 视觉层：存量审计原型 14/14 阈值实测 PASS」。但两份 `src/theme/tablerTheme.ts` 并非同一份：

| 色值语义 | 模板工程（新） | 审计工程（线上实测） |
| :-- | :-- | :-- |
| 主色 hover / active | `#0563BC` / `#045db0` | `#0559a8` |
| 正文 | `#1f2937` | `#232e3c` |
| 次要 / 弱化 | `#6b7280` / `#9ca3af` | `#626976` / `#959dac` |
| 表头底 | `#f9fafb` | `#fafbfc` |

审计工程仍是**旧一套 Tabler 色值映射**，且缺模板工程已有的 `Menu / Tabs / Descriptions / Card / Input / DatePicker` 配置段。直接后果：**§5.2 第 11 项「表头底色 `rgb(249,250,251)`」在审计工程实测为 `rgb(250,251,252)`，不达标**（报告称 14/14 通过）。视觉差异极小，但"统一"这一动作本身没发生。

另：审计工程表格单元格 padding 实测 `16px`，模板工程实测 `12px 8px`，同一版本 antd（6.6.0）下两者不一致，根因待查（倾向审计工程某处等效 `size="large"`）。

### 3. 【不达标】T-5b #10 版权行覆盖不全

口径为"**有底部操作栏的页面**统一补版权行"。实测：底部操作栏 26 处，版权行 20 处。

| 模块 | 底部操作栏 | 版权行 |
| :-- | :-- | :-- |
| SystemModule | 2 | **0** |
| ArchiveModule | 1 | **0** |
| PlanModule | 4 | 1 |

已核实 `SystemModule.jsx:575` 与 `:1320` 是标准页面级底部操作栏（`position:'sticky', bottom:0` + `borderTop` + `flex` + `zIndex:10`，与 PlanModule 写法一致），但该模块版权行 0 处。**至少 3 处漏补**（差额 6 处中其余待逐项确认）。报告称"18 处页面级 ✓"，实际 20 处且存在漏项。

### 4. 【不达标】模板工程卡片内边距 12px ≠ 阈值 24px

模板工程 8 处 `<Card size="small">`（`DesignGallery` 4 / `FormDemo` 2 / `DetailDemo` 1 / `shared/ui/DetailList.jsx` 1）渲染出 `.ant-card-small`，body padding 为 **12px**；antd 6 官方默认（无 size）为 `bodyPadding = paddingLG = 24px`（`/roles` 页实测 24px 印证）。

按 v3 口径"尺寸/间距按 antd 官方默认"，`size="small"` 属**未清理的密度残留**（Tabler 40px 高密度遗产）。§5.2 第 3 项阈值 24px 因此不成立；报告称 13/13 通过不实。注意 `DetailList` 是**共享组件**，影响所有详情页。

### 5. 【标准错误】§5.2 第 4 项阈值与 antd 6 官方默认不符

阈值表写「表格单元格 padding `16px × 16px`」。实测 antd 6 表格根类为 `ant-table-medium`，官方默认 `cellPaddingBlockMD = paddingSM = 12`、`cellPaddingInlineMD = paddingXS = 8`，即 **12px 8px**（`node_modules/antd/es/table/style/index.js:209-210`）。该阈值沿用 antd 5 认知，**应修订为 12px 8px**（若某工程用 `size="large"` 则为 16px/16px，需分别标注）。

### 6. 【陈述不实】4 处报告与实测不符

| # | 报告原文 | 实测 |
| :-- | :-- | :-- |
| 1 | 「12 套件 **12/12 exit 0**（优于基线：存量红灯 `test-prd-simplification.py` 本轮已转绿）」 | **11 绿 1 红**，`test-prd-simplification.py` exit=1（`AssertionError: Skill 缺少核心语义责任: 跨页面推进`），未转绿。该红项按 §5.1 口径**不计本次账**，但"已转绿"无依据 |
| 2 | 「§5.2 第 4 项单元格 16px×16px PASS」 | 12px 8px（见 §三.5） |
| 3 | 「§5.2 第 3 项卡片内边距 PASS」 | 模板工程业务页 12px（见 §三.4） |
| 4 | 「版权行 ✓（18 处页面级）」 | 20 处，且有模块漏补（见 §三.3） |

### 7. 【门禁弱化】`excluded_source_prefixes: ["modules/demo/"]`

`prototype-consistency-check.py` 硬编码排除整个 `modules/demo/`，使模板工程的三个示范页（`DesignGallery` / `DetailDemo` / `FormDemo`）**完全脱离一致性门禁**。这属于"门禁指标变好看、防幻觉能力变弱"的已知模式：排除后 `conflicts = 0` / `omissions = 0` 的绿灯，不能代表这三个页面无遗漏。建议改为在 demo 页去业务名，或把排除范围收窄到具体文件。

### 8. 【文档未同步】§5.2 第 7 项判据两处不一致

手册 §5.2 第 7 项仍写「含 `PingFang SC` / `Microsoft YaHei`」，执行报告按用户拍板改为「不含 `Inter`」判定。判定本身合规（用户已授权），但**手册未同步**，后续复验会再次冲突。同理 §5.2 第 3/4 项阈值需按 §三.4/5 修订。

## 四、需用户拍板

| # | 事项 | 选项 |
| :-- | :-- | :-- |
| 1 | 模板工程 8 处 `<Card size="small">`（含共享 `DetailList`） | 去掉（真正全按官方默认，卡片变 24px）／ 保留（承认紧凑是项目习惯，并把阈值改为 12px） |
| 2 | 审计工程主题是否与模板工程同步 | 同步（消除 7 处色差 + 表头底达标）／ 维持现状（视差异为可接受） |
| 3 | 是否补 SystemModule(2) / ArchiveModule(1) 版权行 | 补齐（符合 #10 口径）／ 不补（改口径为"部分页面"） |
| 4 | §三.1 的 19 处 `start/end` 改动 | 保留（语义等价、零风险）／ 回滚（无必要） |

## 五、验收结论

```text
结论：REJECTED（不通过）
- §5.1 自动化：5/5 项复现通过（1 处报告陈述不实，不影响判据）
- §5.2 尺寸阈值：模板工程 11/13（第 3、4 项不达标/标准有误）；审计工程 12/14（第 11 项表头底不达标）
- §5.3 角色差异：7/7 通过（独立复现，成立）
- §5.4 反向检查：通过（颜色未覆、习惯在、线上可交付）
- §5.5 交付：https://audit-system-prototype.pages.dev 实测通过
- 必须修复：F4 假知识（已就地更正）；T-5a 主题未同步；T-5b #10 版权行漏补
- 负面结论（不得省略）：
  1. antd 6 rc-table 对 fixed: 'left'/'right' 的归一化行为已由源码与字节对撞双重确认，'left'/'right' 从未失效；
  2. ~~antd 6 表格官方默认密度为 12px 8px~~（**已撤回**：无 size 时默认 16×16，12×8 仅在显式 size="middle" 时出现）；
  3. 同版本 antd 下模板与审计两工程主题色值不一致，"统一"未完成（修复轮已同步）。
```

**总评**：核心功能（角色差异、线上交付、钉列、分页、返回位置、图标统一）实测成立，返工量小；但存在 1 项会持续误导后续生成的事实性错误，及 3 项"报告称已完成而实际未完成"的动作。建议按 §四拍板后，以一次小批次修复收口，再复跑 §5.1 与线上抽样。

## 六、修复轮（2026-09-11 下午，用户拍板后执行）

用户对 §四 四项拍板：**①卡片真按官方 24px；②主题同步；③补版权行；④start/end 改动保留。**

### 6.1 按拍板执行的修复

| 项 | 动作 | 结果 |
| :-- | :-- | :-- |
| ①卡片内边距 | 模板工程移除 8 处 `<Card size="small">`（DesignGallery 4 / DetailDemo 1 / FormDemo 2 / **共享 DetailList** 1）及 2 处 `Table size="middle"`、Home 页按钮 small 降级 | 卡片 body 全部 24px，build exit 0 |
| ②主题同步 | 审计工程 `tablerTheme.ts` + `global.css` 与模板工程**逐字一致**（diff 校验通过），`main.jsx` 补 `tablerCssVars` 注入 | §5.2 表头底 `rgb(249,250,251)` 达标 |
| ③版权行 | 按内容定位补 8 处（Archive 1 / Implementation 2 / Plan 3 / System 2，脚本干跑核对后写入），另统一 total 模块 2 处旧样式（居中 12px → 右对齐 14px #606266） | 操作栏 26 / 版权行 26 对齐 |
| ④fixed 取值 | 保留 `start/end`（语义等价） | — |

### 6.2 修复轮新发现并一并修复（全量 66 页扫描暴露）

| 缺陷 | 规模 | 修复 |
| :-- | :-- | :-- |
| **r03 运行时崩溃**（直链访问 `snap=null` 时读 `snap.extra['审核状态']`） | 1 处 | 页头 Tag 加 `snap ?` 守卫（SnapshotBar 本身有 `!snap return null`） |
| **Descriptions span 溢出**（antd6 告警 `Sum of column span not match column`） | 7 处（feedback 1 / implementation 2 / project 1 / report 2 / archive 2） | 逐处调整 span 使各行 ≤ column；archive 的 `Descriptions.Item` 写法为静态扫描盲区，已人工核对全部 8 个实例 |
| **Upload value 注入告警**（Form.Item name 注入字符串 value → antd6 `value is not a valid prop`） | 2 处（fb02 / fb04） | 改本地 state 管控 + 提交手动校验，Upload 脱离 Form 控值 |
| **弃用 API 残留**（审计工程） | `destroyOnClose`/`split`/`direction="vertical"`/`bodyStyle` 0 残留（此前已迁）；Timeline items `children→content` 19 处（antd6 官方迁移映射 `['children','content']` 实证）；Drawer `width→size` 已迁且数字 size 合法（`isNumber(size)` 直通宽度） | console 全净 |
| 与官方默认冲突的 `size` 覆盖 | 审计工程 92 处（Card/Table/Descriptions/Button/Select/Input/DatePicker 的 small/middle） | JSX 开标签扫描器（v1 有嵌套误删缺陷，**已回退重做 v2**）移除；壳层与 Space/Progress 的合法 size 保留 |

### 6.3 修复后终验

| 判据 | 结果 |
| :-- | :-- |
| 12 套回归套件 | 11 绿 1 红（`test-prd-simplification.py` 为**存量红**，与原型无关，未转绿） |
| 两工程 `npm run build` | 均 exit 0（模板 2,342 kB / 审计正常出包） |
| 13 项阈值全量扫描 | **模板 4/4 + 审计 66/66 全过** |
| 角色差异 7 项 | 保持通过（本轮未触及权限层） |
| consistency-check 三指标 | `conflicts=11 / needs=257 / omissions=762` 与改动前基线**逐项一致**，零锚点丢失 |
| console | 全站 0 error / 0 warning |

**探针误报源记录**（后续验收勿再误判）：antd6 复选列默认 padding 16×8（数据列 16×16）；ghost 主按钮背景透明；disabled 主按钮 `rgba(0,0,0,0.04)`（antd6 官方禁用样式）；壳层顶栏（`.ant-layout-header`）的角色切换下拉为 sm 密度，属壳层白名单不在页面阈值内。

### 6.4 遗留（不阻塞，待后续处理）

- `prototype-consistency-check.py` 的 `excluded_source_prefixes: ["modules/demo/"]` 仍整体排除示范页（§三.7），建议后续收窄到具体文件或去除 demo 页业务名。
- 审计工程改动均在本地，**未部署**；线上 `audit-system-prototype.pages.dev` 仍是修复前版本，下次部署后应复跑 66 页扫描。
