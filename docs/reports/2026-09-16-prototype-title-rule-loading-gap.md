# 一级页面主标题回归——根因与修复（2026-09-16）

## 结论

规则没丢，也**不是"加载不完"**。规则所在的那一节（`prototype-component-behavior.md §1`）在生成侧**没有任何读取触发条件**，约 250 token 的片段从来不会被读——它等于不存在，"文件已写、规则已入库"这个事实反而掩盖了失效。

同时存在一处**规范内部矛盾**：`prototype-page-types.md` 六处把「内页标题」写成必须项，`prototype-component-behavior.md` 说列表/表单/看板页不放大标题，两处都是"必须"语气，且都没定义"一级页面"与"内页"的区别。生成侧命中哪一条，哪一条生效。

## 违规事实

租赁原型（`D:\work\交投软件中心\设备租赁\output\prototype`）两处一级页面渲染了 `PageHeader` + `subtitle`：

| 文件 | 路由 | 页面性质 |
| :-- | :-- | :-- |
| `src/modules/settlement/SettlementSheets.jsx:510` | `/settlement/sheets`（`menu: true`，另 `/` 默认页复用） | 一级列表页 |
| `src/modules/settlement/MonthlySummarySheets.jsx:549` | `/settlement/monthly-summary`（`menu: true`） | 一级列表页 |

被删的两个标题（`我的租赁单 / 设备结算单 / 基础结算单管理`）与壳层 `App.jsx:29-40` 的角色化页面名**逐字相同**——原 `PageHeader` 是纯重复表达，不是额外信息。两个详情页（`SettlementSheetDetail` / `MonthlySummaryDetail`）的 `PageHeader` + 返回属内页，保留。

## 根因（四处，相互独立）

1. **触发条件不覆盖章节（决定性的那处）**。`skills/spm-prototype/SKILL.md` step 5 对 `prototype-component-behavior.md` 的触发条件是「Portal、sticky、Sider 或特定响应式」——只覆盖 §2；§1 无触发。扫描全部 7 个原型 reference 的一级标题与触发条件，**只有 `component-behavior.md §1` 完全无触发**，而规则恰好只在那里。

2. **同一规则的两处口径未裁决**。`page-types` 的类 1/2/4/5/6 结构均写「内页标题」，类 6 写「内页标题（标题 + 状态标签 + 右上返回）」；`behavior` 写「普通列表、表单、看板页……不额外放大标题」。两文件互不引用，无优先级声明，"内页"未定义。

3. **官方规范要求页面标题区，且权威顺序把它排第一**。`ADAPTATION.md` 写明「尺寸、字号、间距、阴影、控件规格与**结构规则**一律照官方原文执行」；官方 `layout.md` 有整节页面标题区（主标题 / 副标题 / extra / titleSuffix），`components_List.md:138-139` 明确要求列表页主标题 + 副标题。原 `ADAPTATION.md` 只列了「图表 API」「固定表头」两处豁免，**页面标题区没有豁免**，于是官方要求被照做。

4. **模板 fixture 是反向示范**。`templates/prototype-vite/src/routes.jsx` 把 `/detail`（商户详情）、`/form-demo`（出库申请）注册为 `menu: true`，两个组件都带 `PageHeader` + `onBack` —— 等于示范"一级菜单页用 PageHeader"。模板是每次生成必读的样板。

## 关于"是不是规则太多"

不是。用数据回答：

| 项 | 体量 |
| :-- | --: |
| 原型自有规范全部（SKILL + 7 refs + 评审清单） | ≈ 40.5k token |
| 官方 design-sources 6 章 | ≈ 112.7k token |
| 单个类 1 页面命中的官方书签 `components_Table.md` | ≈ 20.3k token |
| **规则所在的 `component-behavior.md §1`** | **≈ 250 token** |

违的这条规则只占 250 token，删掉十条别的规则，它照样不会被读。**"按需加载的触发条件"是人工维护的，它才是可失效点**：一条规则只要没有触发条件覆盖，运行时就不存在，而且失效没有任何告警——"已入库"给人一种已覆盖的错觉。规则越多，触发条件的维护面越大，漏一个就永久静默。所以正确方向不是减规则，而是：跨页型通用约束上移到常驻短规则、消除同一规则的副本、给触发覆盖本身一个核对动作。

## 已修（9 文件）

| 文件 | 改动 |
| :-- | :-- |
| `references/prototype-page-types.md` | §一 新增「一级页面与内页的标题口径（唯一裁决）」：判定方式（按进入路径：菜单/页签可直达 = 一级；下钻需返回 = 内页）、四行对照表（主标题 / 副标题 / 右上返回 / 页面内其他标题）、禁止项、看板类一级页面同规则；并声明各章「内页标题」按本节裁决 |
| `skills/spm-prototype/SKILL.md` | 常驻短规则加标题口径一条（**这一条使规则可达**）；step 4 从"只读命中章节"改为"§一 总则 + 命中章节"（总则含全局裁决，必读）；step 5 触发列表补「组件选型、组合边界」并列出三层小节；统一验证第 3 条加"一级页面不放大标题" |
| `references/design-sources/ant-design-official/ADAPTATION.md` | 新增「页面标题区的额外说明（官方有规则，本库不适用）」：说明官方 `layout.md` 页面标题区与 `components_List/Table` 的主标题+副标题要求不适用一级页面，指向唯一裁决，不复述判据 |
| `references/prototype-writing.md` | 组件清单表 `PageHeader` 行补「仅内页使用」及一级页面禁止项（该文件每任务必读，是触达性最高的一处） |
| `references/prototype-component-behavior.md` | §1 原句改为指向 `page-types` 唯一裁决，不自留第二套定义 |
| `references/prototype-visual-spec.md` | 1.4 页面主标题 24px 条款：原「全局唯一主标题」易被读成"每页都有"→ 明确只服务内页 |
| `contracts/prototype-review-checklist.md` | 新增检查项 26「一级页面不放大标题」（P2，`content`/页面或元素） |
| `templates/prototype-vite/src/{App.jsx,routes.jsx}` | 壳层渲染点说明页面名由壳层表达；两处内页样张的路由登记处标明"仅为可达性登记为菜单项，内页才渲染 PageHeader" |
| `AGENTS.md` | §2 新增「按需加载的可达性」3 条维护规则（见下） |

`AGENTS.md` §2 新增：

- 12. 触发条件必须覆盖被加载文件的全部一级章节；补不上触发条件就删掉该章节；改动按需路径时核对"文件一级标题清单 vs 触发条件"。
- 13. 跨页型通用的硬约束放进常驻短规则，不放按需章节；判断方法：若某约束可由"页面种类"枚举出会被违反的场景，它就是通用约束。
- 14. 同一规则只保留一处权威定义；下游只写引用，不复述（含"六类/九维"这类数量词）。

## 租赁原型修复

`SettlementSheets.jsx`、`MonthlySummarySheets.jsx` 删除 `PageHeader` 调用与随之无用的 import，原位留一行注释说明口径。`data-page` 锚点在根 `div` 上，未受影响。

## 验证

- 租赁原型 `npm run build` 通过（2.38s，dist 重建）
- 租赁原型 `prototype-shared-guard` / `prototype-source-check` 均 exit 0
- 模板 `npm run build` 通过（模板自带 `node_modules`；`dist/` 已被 `.gitignore` 忽略，构建无副作用）
- ShitPM `pytest -q` **88 passed**；`test-resource-integrity.py` exit 0（路径、链接、目录、marker 全通过）
- 口径唯一性核验：全仓库「一级页面与内页的标题口径」只在 `page-types.md` 定义，另 4 处均为引用

## 已知边界

**本次修复没有机械守护。** 改动落在指令层与规范层，没有任何测试会因回退它而转红——这与本仓库此前"修复必须能指出哪条测试会因回退它而转红"的要求不符。可机械化的是"SKILL.md 触发条件是否覆盖被引用文件的一级章节"，但中文章节名与散文触发条件之间的匹配误报率很难压到准入标准，按 `AGENTS.md` §1 #7 暂不新增脚本；当前以 `AGENTS.md` §2 #12 的人工核对动作替代。是否需要机械化由用户决定。
