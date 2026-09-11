# Prototype 生成引擎升级 —— 验收报告（T-4）

| 项    | 值                                                                                            |
| :--- | :------------------------------------------------------------------------------------------- |
| 执行手册 | `docs/plans/2026-09-10-prototype-ant-design-skill-engine-upgrade-plan-and-acceptance.md`（v3） |
| 分支   | `codex/upgrade-prototype-pro-engine`（**未 push**）                                             |
| 执行范围 | T-0 → T-1 → T-2A（T-2A-1 ~ T-2A-8）→ T-3 → T-4                                                 |
| 路径判定 | **T-2A（全面引入 ProComponents）**                                                                 |
| 放行结论 | **通过差分门槛**；4 项绝对值门槛全 PASS，2 项观测项未测/负收益（见 §4）                                                 |
| 报告日期 | 2026-09-10                                                                                   |

---

## 1. T-1 探针结果：**GO**

### 1.1 R-A 依赖可行性（PASS）

| 检查                                        | 结果   | 证据                                                                                                                                                      |
| :---------------------------------------- | :--- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `@ant-design/pro-components@3.1.14-7` 可安装 | PASS | `package.json` L12 精确值 `"3.1.14-7"`（无 `^`），`--save-exact` 安装                                                                                            |
| 无 ERESOLVE / peer 冲突                      | PASS | 安装过程未触发 `--legacy-peer-deps` / `--force`；beta 的 peer 为 `antd ^6.0.0`                                                                                    |
| 关键导出存在                                    | PASS | `ProTable` / `ProConfigProvider` / `ProForm*` / `QueryFilter` / `LightFilter` / `StepsForm` / `BetaSchemaForm` 均可从 `@ant-design/pro-components` 导入，构建通过 |
| 与 antd 6 共存                               | PASS | 模板工程 `antd ^6.6.0` 下 `npm run build` 退出码 0                                                                                                              |

### 1.2 R-B 锚点风险（PASS，但暴露真实缺口并已补救）

用真实项目验收副本 `.tmp/acceptance/审计系统` 做同口径对照，脚本为 `scripts/python/prototype-consistency-check.py`：

| 场景                                | 脚本版本             | `possible_omissions` | 结论                                                          |
| :-------------------------------- | :--------------- | -------------------: | :---------------------------------------------------------- |
| 项目原始 `output/prototype/src`（现状基线） | 修复后              |              **742** | 基线                                                          |
| 现状 + `ProTable` 探针页（`probe-src`）  | **未打补丁（HEAD 版）** |              **742** | **ProTable 的 9 个 `dataField` 锚点 100% 不可见，指标不动 = 防幻觉能力静默失效** |
| 现状 + `ProTable` 探针页               | 修复后              |              **733** | 补丁生效，9 个锚点被正确识别                                             |

**判定**：R-B 风险被实测证实（不是推测），T-2A-4 的补救机制同时被证实有效，且分类语义未变（`deterministic_conflicts` / `needs_semantic_judgment` 数值不受补丁影响）。

### 1.3 门禁判定

V-T1-1（依赖）/ V-T1-2（构建）/ V-T1-3（主题未污染，`#1677ff` 0 命中）/ V-T1-4（剥离清单 0 命中）全 PASS → **GO，进入 T-2A**。探针文件 `ProbeTable.jsx` 与临时 `/probe` 路由已清理。

---


## 2. 执行路径：T-2A（各节点完成情况）

| 节点     | 内容                            | 状态                        | 交付物                                                                                                                                                                                           |
| :----- | :---------------------------- | :------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T-2A-1 | 依赖锁定 + `ProConfigProvider` 接入 | 完成                        | `package.json`（`3.1.14-7`）、`src/main.jsx`（`ProConfigProvider` 嵌在 `ConfigProvider` 内，视觉入口唯一仍是 `tablerTheme`）                                                                                   |
| T-2A-2 | 6 个模板转写 + 剥离清单                | 完成                        | `src/shared/templates/`：`ToolbarTable` / `QueryFilterTable` / `BatchTable` / `VerticalStepsForm` / `EmbedForm` / `GroupedCardDescriptions` + `index.js`（含 `TEMPLATE_ROUTES`）+ `templates.css` |
| T-2A-3 | 阴影对齐                          | 完成（前方会话，commit `5f5cfc0`） | `tablerTheme.ts` / `global.css` 阴影基准统一 `rgba(18,18,23)`                                                                                                                                       |
| T-2A-4 | `columns[].dataField` 锚点解析    | 完成                        | `prototype-consistency-check.py`：`_strip_js_strings_and_comments(preserve_strings=True)` + `dataField: '...'` 提取；分类语义未改                                                                       |
| T-2A-5 | `behavior.md` 六章重建            | 完成                        | `references/prototype-component-behavior.md`：5,305 → **11,380** 字节，新增 §4~§9，各带 `route:` id                                                                                                    |
| T-2A-6 | `spm-prototype/SKILL.md` 改写   | 完成                        | 渐进装载路由表 + 模板起步强制规则 + 未命中回退契约 + `shared/ui` 11 组件处置清单 + 视觉入口唯一约束 + 禁止 `DataTable`/`ProTable` 混用                                                                                                |
| T-2A-7 | 评审侧同步（同批）                     | 完成                        | `contracts/prototype-review-checklist.md`（15/18/22 条扩展 + 新增第 24 条）、`skills/spm-prototype-review/SKILL.md`（第 4、8 步）                                                                            |
| T-2A-8 | A/B 实验 + 真实项目回归               | 完成                        | `experiments/antd-tabler-efficiency/D-pro-template/`（组 D）+ 回归 harness                                                                                                                         |

**副本同步校验**（源与已安装副本 md5 一致）：

```
spm-prototype        : 6c107dd4411bbd3a3ec1723c03e3a50e  SAME
spm-prototype-review : b4713798b58c5109ff0a450f30f4d8ca  SAME
```

**剥离清单实测（8 项全 0 命中）**：`global-style` / `colorPrimary` / `#1677ff` / `ConfigProvider` / `ProColumns` / `tableListDataSource` / `from 'antd/es` / `from "antd/es`。图标导入仅 `@tabler/icons-react`。

---

## 3. §6.1 工程与交互验收逐条结果

### 3.1 工程命令

| 命令                               | 目标                         |  退出码  | 实测                                                                         |
| :------------------------------- | :------------------------- | :---: | :------------------------------------------------------------------------- |
| `npm run build`                  | `templates/prototype-vite` | **0** | 3.41s，`dist/assets/index-*.js` 2,881.91 kB（gzip 931.77 kB），仅 chunk 体积提示    |
| `prototype-source-check.py`      | `templates/prototype-vite` | **0** | 15/15 PASS                                                                 |
| `prototype-source-check.py`      | `.tmp/acceptance/审计系统`     | **0** | 15/15 PASS                                                                 |
| `prototype-consistency-check.py` | `.tmp/acceptance/审计系统`     |   1   | `deterministic_conflict`：10 个 `unregistered_route`（**全部既有，新增 0**，详见 §4、§6） |

> 注意 `source-check` 的 `--project-root` 语义是「项目根」，内部固定取 `<root>/output/prototype`；对回归 harness 需改传 `--prototype-root`，对一致性检查需改传 `--prototype-src`。手册 §6.1 未写明这两个覆盖参数，本次已实测确认。

### 3.2 交互清单（真实浏览器，Playwright + chromium-1243）

|  #  | 清单项                                             |    结果    | 实测证据                                                                                            |
| :-: | :---------------------------------------------- | :------: | :---------------------------------------------------------------------------------------------- |
|  1  | 搜索准确筛选；重置清空表单并**自动重新拉取全量数据**                    | **PASS** | 30 行分页探针：重置后表格行数 = 10（= pageSize，证明重拉而非残留）；输入框值 `''`                                            |
|  2  | 切换筛选或重置时**当前页码自动回到 1**                          | **PASS** | 翻到第 2 页 → 点查询 → 当前页 `1`；再翻到第 3 页 → 点重置 → 当前页 `1`                                                |
|  3  | 桌面端抽屉「确定/取消」固定 Header 右侧，滚动不脱离视口、不抖动            |   不适用   | `templates/prototype-vite/src` 内 `Drawer` **0 命中**；本次转写的 6 个模板均为卡内布局，无抽屉型模板（官方 `05-QueryFilter` 的抽屉分支未纳入转写范围）。**本次变更范围内无可测对象，不得记为"通过"** |
|  4  | 长文本 `ellipsis + Tooltip`，不撑高行高                  | **PASS** | 样张页 `.ant-table-cell-ellipsis` = 12 个单元格                                                        |
|  5  | 分步表单：完成态/当前态清晰，校验未过无法下一步，支持草稿暂存                 | **PASS** | 未填点「下一步」被拦截：错误提示 3 条、当前步仍为第 1 步；`暂存草稿` 按钮存在                                                     |
|  6  | Console **0 Errors**（含打开所有 Modal / Drawer / 下拉） | **PASS** | 模板工程 5 路由 + 全部模板交互 = **0 error / 0 warning**；组 D 页面（筛选 / Modal / 删除确认）= **0 error / 0 warning** |

补充：`EmbedForm` 保存链路单独验证 —— 填必填项后保存，成功提示出现（`.ant-message-notice` = 1）。


### 3.3 Tabler 视觉清单（计算样式实测）

| 清单项                                                                  |             结果             | 实测值                                                                                                                                                                  |
| :------------------------------------------------------------------- | :------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 主色 `#066fd1`，无 `#1677ff` 残留                                          |          **PASS**          | 主按钮 `rgb(6, 111, 209)`；全页扫描 `color/backgroundColor/borderColor/outlineColor` **无 `#1677ff` / `#1890ff` 命中**（含分页、链接、聚焦环）                                              |
| 卡片阴影 `0 1px 2px 0 rgba(18,18,23,.05)`，hover 升为 `--card-shadow-hover` |          **PASS**          | `cardShadow = rgba(18, 18, 23, 0.05) 0px 1px 2px 0px`；`--card-shadow-hover = 0 4px 6px -2px rgba(18,18,23,0.05), 0 10px 15px -3px rgba(18,18,23,0.08)`               |
| 输入框 / 按钮阴影同基准                                                        |          **PASS**          | `inputShadow` / `primaryShadow` / `defaultShadow` 均为 `rgba(18, 18, 23, 0.05) 0px 1px 2px 0px`；旧色 `rgba(31,41,55,*)` **0 命中**                                         |
| 下拉 / 浮层为四层 Tabler 浮层阴影                                               | **PASS（机制与手册描述不符，见 §6-2）** | 打开真实下拉：`rgba(18,18,23,.04) 0 2px 4px, rgba(18,18,23,.04) 0 5px 8px, rgba(18,18,23,.03) 0 10px 18px, rgba(18,18,23,.04) 0 24px 48px` = 官方 `--tblr-shadow-dropdown` 四层 |
| 控件 / 卡片 / Tag 圆角未被 Pro 内部样式覆盖                                        |          **PASS**          | 卡片 `8px`、按钮 `6px`、Tag `4px`（= Tabler 主题 token `borderRadius:6` / `Card.borderRadiusLG:8` / `Tag.borderRadiusSM:4`）                                                   |
| 表头底 `#f9fafb`（非 `#fafafa`）                                           |          **PASS**          | 表头计算底色 `rgb(249, 250, 251)`；`src` 内 `#fafafa` 仅出现在注释与 Claude 主题                                                                                                      |
| 无 `global-style.css` 引入，无模板 `theme` 常量残留                             |          **PASS**          | 两文件 grep 均 0 命中                                                                                                                                                      |

---

## 4. §6.2 放行阈值表（填实测值）

| 指标                        | 门槛                | 实测                                            |                判定                |
| :------------------------ | :---------------- | :-------------------------------------------- | :------------------------------: |
| `deterministic_conflicts` | 必须为 **0**         | 10（全部 `unregistered_route`，**新增 0**；基线集合完全一致） | **差分 PASS / 绝对值 FAIL**（原因见 §6-6） |
| `possible_omissions`      | 不得比 C 组基线增加       | 回归 harness **716** vs 基线 **742** → **-26**    |             **PASS**             |
| 首次运行缺陷数（五类计数）             | ≤ 1               | **0**                                         |             **PASS**             |
| 高危缺陷（重置失效 / 分页未归位）        | 必须为 **0**         | **0**（浏览器实测，见 §3.2-1/2）                       |             **PASS**             |
| `npm run build`           | 退出码 0             | **0**                                         |             **PASS**             |
| Console Errors            | 0                 | **0**（模板工程 + 组 D）                             |             **PASS**             |
| 生成 Token                  | 下降 ≥ 30%（观测，非硬门槛） | **未测**                                        |                不适用               |
| 单页代码行数                    | **不设门槛，仅记录**      | 见 §5                                          |                记录                |

### 4.1 「五类缺陷」的操作性定义（手册缺定义，本报告自行定义）

手册 §6.2 引用「五类缺陷计数」但**未在手册内定义**。本次验收采用可测量的五类口径，实测全部为 0：

| 类别        | 判据                                                       |   实测   |
| :-------- | :------------------------------------------------------- | :----: |
| D1 高危交互缺陷 | 重置未清空 / 未重拉 / 分页未归位                                      |    0   |
| D2 主题污染   | `#1677ff` 计算样式残留 / 模板 `theme` 常量 / `global-style.css` 引入 |    0   |
| D3 锚点净损失  | 同一页面 `possible_omissions` 相比基线上升                         | 0（-26） |
| D4 新增冲突   | 相对基线新增 `deterministic_conflicts`                         |    0   |
| D5 运行时噪声  | Console error / warning                                  |  0 / 0 |

---

## 5. 代码行数观测（不设门槛）

口径沿用手册 §0.4：`wc -l <组>/src/modules/*/*.jsx`。

| 组                             | 说明       | `src/modules/*/*.jsx` | `ProblemList.jsx` |
| :---------------------------- | :------- | --------------------: | ----------------: |
| A（裸 antd，无护栏）                 | 下界，非基线   |                   722 |                99 |
| C（现状：`shared/ui` + Tabler 主题） | **现状基线** |                   725 |           **102** |
| D（升级后：模板起步 + ProComponents）   | 本次产物     |                 1,056 |           **162** |

必须如实说明的偏差：

- 组 D 的 `src/modules/*/*.jsx` 含新增样张页 `TemplateGallery.jsx`（271 行，非业务页），剔除后业务页合计 ≈ 785。
- **单页业务页行数上升 60 行（+59%）**，来源三处：① 每列显式声明 `dataField` 锚点（防幻觉契约，T-2A-4 的前提）；② `ToolbarTable` 把筛选/操作/分页/空态从 `shared/ui` 的隐式封装改为显式声明；③ 筛选字段改用 `ProForm*` 表单项。这是**负收益项**，与"引入护栏不增行数"的既有结论相反，手册 §0.4 已把行数降级为观测项，故不构成放行障碍，但不应对外宣称"代码更短"。
- 新增共享模板库一次性成本 **575 行**（6 模板 + `index.js` + `templates.css`），按页面摊薄。
- 全量 `src` 目录行数（含 `.css`/`.ts`）：A 1,975 → C 1,993 → D 2,932（同样含样张页与模板库）。

---


## 6. 未解决项与建议

**1）手册 §6.2「五类缺陷」缺定义 —— 建议回写手册。**  
本次自行定义（§4.1）以保证可复现；建议把该定义回写进手册，否则后续复跑会各写一套口径。

**2）手册 §6.1「下拉/浮层为四层 `--tblr-shadow-dropdown`」与实现不符 —— 建议改描述。**  
项目**不存在** `--tblr-shadow-dropdown` CSS 变量；四层浮层阴影是通过 antd 全局 token `boxShadowSecondary` 落地的（`tablerTheme.ts` L55-56）。视觉效果达标，但按字面去 grep 变量会误判为失败。建议手册改为「浮层为四层 `rgba(18,18,23)` 阴影（经 `boxShadowSecondary` 落地）」。

**3）手册 §6.1 圆角数值只对 Tabler 成立 —— 建议补限定。**  
实测 Tabler = 控件 6px / 卡片 8px / Tag 4px（与手册一致）；但 `claudeTheme.ts` = 控件 8px / 卡片 12px。手册未标「随主题」，跨主题时会误判。

**4）新模板的固定按钮缺 `data-operation` 锚点 —— 建议一次性补锚点。**  
回归 harness 中新增 7 条 `unanchored_button`（`needs_semantic_judgment` 桶，不阻断），来自模板内部的 `查询/重置/新建/批量/上一步/下一步/暂存草稿` 等由 props 或表达式生成文案的按钮。模板是共享层，锚一次即可让所有下游页面继承，比每页手工核准更省。属产品改进建议，**未擅自实施**（手册未包含此项）。

**5）`QueryFilterTable` 的 `pagination` prop 展开顺序有隐患。**  
`pagination={{ current, onChange: setCurrent, ...(pagination ?? {}) }}` —— 调用方若在 `pagination` 里传 `current` / `onChange`，会覆盖内部受控分页并破坏「回到第 1 页」。当前 6 个模板的用法均未触发，属潜在坑。建议交换展开顺序或在 `behavior.md` 明确禁止项。

**6）真实项目回归的 10 个 `deterministic_conflicts` 需在真实项目复核。**  
10 条全部为 `unregistered_route`（`/total`、`/plan`、`/project`… 共 10 个模块路由），且**基线与回归集合完全一致**，属验收副本自身状态（副本只保留 `output/design` 的部分内容，Design 页面索引与模块路由表不对应）。因此 §6.2 的「conflicts 必须为 0」只能按**差分（新增 = 0）**判定。建议在完整真实项目上复跑一次取绝对值，而不是依赖剥离副本。

**7）生成 Token 未测量。**  
无 token 计数工具链，且实验为「同模型、不同 prompt」的手工运行，隔离采样成本高于收益。该项为观测项，不影响放行，但手册 §6.2 的「下降 ≥30%」目前**没有任何证据支撑**，建议要么补测要么从门槛表移除。

**8）分支存在与本计划无关的未提交改动，且含一项待确认的产品口径收窄。**  
未提交改动中，以下文件**不属于本计划范围**（前序会话遗留）：

| 文件                                                         | 性质                                                     | 需确认                                                          |
| :--------------------------------------------------------- | :----------------------------------------------------- | :----------------------------------------------------------- |
| `references/prototype-visual-spec.md`                      | 把「Claude / Tabler / traework 三选一」改写为「**Tabler 默认且唯一**」 | **是** —— 与既有用户拍板（默认 Tabler + 可切换 Claude/traework）不一致，属产品口径变更 |
| `references/prototype-writing.md`                          | 删除「品牌主题接入」整节（0 命中）                                     | **是** —— 同上                                                  |
| `README.md` / `USAGE.md` / `scripts/python/shitpm-host.py` | 文档与宿主脚本重写                                              | 是（是否为另一条工作线）                                                 |
| `templates/prototype-vite/src/theme/`                      | `traeworkTheme.ts` 已不存在；`claudeTheme.ts` 仍在但文档不再引用     | 是 —— 半收敛状态                                                   |

**9）提交状态：本计划的全部改动仍未提交。**  
分支 `codex/upgrade-prototype-pro-engine` 目前只有 T-0 一个 commit（`5f5cfc0`），T-2A 的全部文件处于未提交状态。**按手册「等用户拍板合入」的约定未提交、未 push**。建议的提交切分（需用户确认后执行）：

```
commit 1  build(prototype-vite): pin @ant-design/pro-components 3.1.14-7 + ProConfigProvider
          → package.json, package-lock.json, src/main.jsx
commit 2  feat(prototype-vite): add 6 shared page templates + TemplateGallery
          → src/shared/templates/*, src/modules/demo/TemplateGallery.jsx, src/routes.jsx
commit 3  feat(consistency-check): parse columns[].dataField as field anchors
          → scripts/python/prototype-consistency-check.py
commit 4  docs(prototype): template-first routing table + 6 behavior chapters
          → skills/spm-prototype/SKILL.md, skills/spm-prototype-review/SKILL.md,
            contracts/prototype-review-checklist.md, references/prototype-component-behavior.md
commit 5  chore(experiments): add D group source for prototype engine A/B
          → experiments/antd-tabler-efficiency/D-pro-template/{src,index.html,package.json,vite.config.js,.gitignore}
            （勿带 node_modules 符号链接与 dist；A/C 两组含 dist 与 node_modules，需先确认 .gitignore 覆盖再决定是否入库）
```

`references/prototype-visual-spec.md`、`prototype-writing.md`、`README.md`、`USAGE.md`、`scripts/python/shitpm-host.py` **不混入**上述提交，单独确认。

**10）临时产物（已清理，未污染交付物）。**  
本次已删除：`.tmp-probe/`（官方模板缓存）、`.tmp/probe/`、`.tmp/cc-HEAD.py` 及配套 JSON、`.tmp/consistency-*.json`、`.tmp/dev*.log`、`.tmp/d-build.log`、`.tmp/d-preview.log`、`.tmp/probe-*.png`。保留：`.tmp/acceptance/审计系统/{probe-src,regression-src}`（§1.2 与 §4 的对照基线，报告可复现所必需）、`.tmp/pager-probe/`（分页探针源码，依赖软链已移除）、5 个浏览器探针脚本。停掉了本次启动的 3 个本地服务（5173 / 5174 / 4173）。  
另注：仓库根 `.playwright-cli/`（2026-08-28 的 console 日志，110 字节）**不是本次产物**，仍在 untracked 列表中，且未被 `.gitignore` 覆盖——按"不动他人遗留物"原则未删除，建议你决定清理或加入忽略。

---


## 7. 验收证据索引（可复现命令）

```bash
# 构建
cd /d/work/ShitPM/templates/prototype-vite && npm run build; echo "exit=$?"

# 源码结构（模板工程 / 真实项目）
cd /d/work/ShitPM
python scripts/python/prototype-source-check.py --project-root . --prototype-root templates/prototype-vite
python scripts/python/prototype-source-check.py --project-root ".tmp/acceptance/审计系统"

# 一致性（真实项目基线与回归，注意覆盖参数）
python scripts/python/prototype-consistency-check.py --project-root ".tmp/acceptance/审计系统" \
  --prototype-src ".tmp/acceptance/审计系统/output/prototype/src"   # 基线 742
python scripts/python/prototype-consistency-check.py --project-root ".tmp/acceptance/审计系统" \
  --prototype-src ".tmp/acceptance/审计系统/regression-src"          # 回归 716

# 浏览器（需先起 dev: 模板工程 5173 / 探针 5174 / 组 D preview 4173）
# 探针工程 .tmp/pager-probe 首次运行需补依赖软链（Windows，PowerShell 执行）：
#   New-Item -ItemType SymbolicLink -Path '.tmp\pager-probe\node_modules' `
#     -Target 'D:\work\ShitPM\templates\prototype-vite\node_modules'
cd /d/work/ShitPM/templates/prototype-vite && npm run dev                     # 5173
cd /d/work/ShitPM/.tmp/pager-probe    && npm run dev -- --port 5174           # 5174
cd /d/work/ShitPM/experiments/antd-tabler-efficiency/D-pro-template \
  && npm run build && npm run preview -- --port 4173                          # 4173

PY="$USERPROFILE/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
"$PY" .tmp/browser-check.py    # 5 路由 + 6 模板交互 + console 扫描
"$PY" .tmp/pager-check.py      # 分页归位（30 行探针）+ EmbedForm 保存
"$PY" .tmp/visual-check.py     # 阴影 / 圆角 / 表头底 / antd5 蓝残留
"$PY" .tmp/popup-check.py      # 下拉浮层四层阴影
"$PY" .tmp/d-group-check.py    # 组 D 真实页面回归
```

> 探针脚本留在 `.tmp/`（gitignored）；`.tmp/pager-probe/` 已保留源码但依赖软链在收尾时移除，按上面命令重建即可复跑。

