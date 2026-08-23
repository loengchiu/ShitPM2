# Round 13 全量对抗性审查（2026-07-31）

> 前提：上轮报告（`2026-07-31-full-adversarial-review.md`，8 P1/11 P2）的修复据称已全部执行。
> 本轮立场：①修复本身是被审对象；②整仓全量重审（skills 10 + templates 7 + references 16 + contracts 11 + schemas 7 + scripts 关键脚本 + 测试套件），上轮声明"不重复审"的 scripts 层本轮纳入。
> 方法：3 个子代理并行深审三层，主代理逐条核验修复真实性与子代理关键指控，12 个测试套件真跑。

## 1. 上轮修复核验结果：8 P1 全部真修，11 P2 大部分落地

| 上轮编号 | 核验结论 | 证据 |
|---|---|---|
| P1-1 模板/glossary 禁标题 | 真修 | 全仓 grep"模块业务对象及关系"仅剩 prd-writing-rules.md:55 的禁令本身 |
| P1-2 §7 未承接状态机8规则 | 真修 | spm-design:89 逐条点名 8 规则（出路/入路/回退/歧义/覆盖/二次流转/操作人/自洽） |
| P1-3 §7 未承接字段表8列 | 真修 | spm-design:89 八列点名+逐行无合并+落点对齐 |
| P1-4 模板缺操作人 | 真修 | templates/design.md:91 已含操作人 |
| P1-5 review 预检查矛盾 | 真修 | 预检查条款已删，失败处理仅剩三条自洽规则 |
| P1-6 b6/c4 废动作名 | 真修 | subagent-contract 零命中，落点表与 orchestrator L311-319 对齐 |
| P1-7 challenger 定性矛盾 | 真修 | 角色定性与白名单/manifest 一致 |
| P1-8 §6 阅读清单缺漏 | 真修 | spm-design:41 补列 analysis-protocol（完整模式）+ state-format（涉及状态机时） |
| P2-G/H/K/L 等 | 落地 | schema 无 report_completed；context-runtime-check 改"仅在动作明确需要时"弱化措辞；baseline/fact 增互认说明 |

修复未引入直接回归；12/12 测试套件全绿（regression 3 用例、orchestrator 8、replay 6、anti-hallucination 4 类、design-index OK、context-runtime、prd 三件套、resource-integrity、context-loading、design-simplification passed:true）。

**但修复引入/暴露了新的不彻底处，见下。**

## 2. 结论摘要

- **P0：0**（子代理提名 2 个 P0，主代理核验后均降级，理由见各条）
- **P1：6**
- **P2：约 15**
- **已知未落地最大缺口：双门方案（不计入新发现，但必须表态）**

## 3. 已知最大缺口：双门方案仍零落地（要求用户表态）

- 事实（读码确认，非文档）：`design-confirmation.py cmd_confirm`（:124-145）唯一前置是 design.md 存在，不查编排器 accept/receipt/state=completed；spm-prd/prototype 判据仍是单门 `check`；start-action-matrix:9"Design 存在|未确认"行 confirm-design 直接可用无前置；全仓 grep"双门/编排器接受"仅命中 docs/plans 与 memory，contracts 零命中。
- 更要命的是**契约反向自洽**：`design-orchestration-contract.md:63`"不由编排器或确认工具重复证明"——与 `docs/plans/2026-07-30-confirm-gate-fix-execution-plan.md` 的三道门禁方案**直接矛盾**。`test-shitpm-regression.py:55` 还在断言"无前置 confirm 成功"，测试锁定的是单门行为。
- 定性：上轮已声明"待落地、不计新发现"，用户说的"修复执行完了"指上轮 8P1/11P2，不含此项，故不算欺骗。但现状是**方案与主线契约互相矛盾地并存**，后续执行者读 plan 会按三道门改，读 contract 会拒绝改。
- 要求表态（二选一）：①落地 plan（confirm 加编排器 receipt 前置，改 matrix 与下游判据与回归测试）；②废弃 plan 并归档，接受单门。不能继续悬着。

## 4. P1 新发现

### P1-1 PRD 字段表位置规则自相矛盾（同一文件内）
- 证据：`prd-writing-rules.md` 6.4#5"字段表、状态机表放小模块末尾" vs 6.2.18"每个大模块最后一个页面之后写大模块字段定义表"（templates/prd.md、spm-prd 自检均按大模块）。
- 影响：写作与 Review 依同一规则文件得出相反结论。6.2.18 是本轮承接修复的主体，6.4#5 是漏改的旧文。
- 修法：6.4#5 删"字段表"，保留"状态机表放小模块末尾"。

### P1-2 PRD"类型"列在 Design 侧无来源（子代理提名 P0，降级 P1）
- 证据：`prd-writing-rules.md:81` 字段表 7 列含"类型"；`design-writing.md:74` 8 列无类型列，且 :74"不使用普通技术类型"明令 Design 不写类型。
- 降级理由：6.5.2"不得新增 Design 不存在的字段"限制的是字段（行），不是属性（列），不构成"规则自锁死"；但"类型"列内容在上游确无载体，AI 只能从"交互方式/取值规则"推断或臆造——真实幻觉风险。
- 修法（二选一）：PRD 侧注明"类型由取值约束与交互方式推导，推导不出时写'待研发定'"；或 Design 字段表增"数据形态"业务列。需用户拍板方向。

### P1-3 页面属性清单四套口径互不覆盖
- 证据：`design-writing.md:52` 要求 9 项，紧接示例只给 5 项且与 9 项零重叠，:188 写后检查只查 4 项，templates/design.md 是 12 项注释。
- 影响：写作者无法判断达标线，§7 自检"页面到字段和操作"无法对齐具体属性集。
- 修法：以模板为唯一权威清单，writing.md 改为引用模板并修正示例。

### P1-4 状态要素数承接链逐跳掉信息
- 证据：state-format 6 列 ↔ `design-writing.md:152` 要求可判断 8 项（多"是否可逆、终态结果"）↔ PRD 状态机表 6 列却要求"明确业务副作用和失败后状态"（表中无此两列，只能塞正文）。
- 影响：每一跳都有要求超出载体列数、又不说明落在哪的缺口；`design-state-format.md:99` 反例判据"缺少是否可逆和关键副作用"连自己的正例都不满足。
- 修法：定 6 列为唯一表载体，超出项显式规定落正文哪段；state-format:99 判据同步修正。

### P1-5 prototype-mark 对单文件主原型零生效
- 证据：`spm-prototype-mark:72` 遍历"所有 .html 除 index.html"；而 spm-prototype 的单文件原型全部页面在 index.html 内。
- 影响：单文件原型（默认形态）标注数为 0，skill 空转。
- 修法：改为"排除纯 shell/路由文件"或显式支持 index.html 内多页面标注。

### P1-6 ask_user 动作违反自身 schema，发射侧零校验
- 证据：orchestrator :580,595 发射的 select-mode/question:* 动作缺 task_id/mode/task_kind/depends_on/batch_key 五个 schema required 字段；`validate_task_contract` 仅在 handle_accept 调用，next 发射路径不校验。
- 影响：按 schema 实现的宿主解析 ask_user 必失败；误 accept 时报错信息误导。
- 修法：schema 加 if/then（ask_user 放宽 required），handle_accept 对 ask_user 给明确拒绝语。

## 5. P2 新发现（按层归组）

**Skills/Templates：**
- spm-design-review 步骤号 1,2,4…缺 3（上轮删条款留下的编号空洞）。
- 三个 review skill 列必填字段漏 `stage`（schema required 含之），照抄清单即不合规。
- spm-prd:92"十项标准"实列 11 项；自检 #3 要求"见 5.1"跨模块指向与 STYLE005 禁跨节引用打架。
- spm-prototype description 含"查看原型"触发词，但 skill 无只读分支，触发即重生成覆盖——建议删"查看"归 start/review。
- spm-prototype-mark:15 引"PRD §6.3 推荐矩阵"死引用（实际在 start-action-matrix）；:301 自检与 5.7 三种关闭方式矛盾。
- start-action-matrix：/spm-fix、/spm-prototype-mark 只出现在三产物齐全行，与 fix"下游不要求同时存在"、mark"PRD 可选"矛盾。
- spm-align"Design 自动继续"与矩阵"仅 Align"并存；simple/full 模式采集责任在 align/design 间悬空（align 不采集，design 要求用户选）。
- templates/design.md 未示范 `### 状态机：X` 独立标题骨架，而 state-format:13 强制独立标题且理由还写着已删解析器——规则、模板、事实三方不齐。
- templates/design.md:148 页面操作缺 `##### 操作表` 骨架，与 design-writing.md:98-112 不一致。

**References：**
- prototype-writing.md:36,44"按第七章模板重写 shell"自引用错误（本文件第七章是视觉细节，模板在 prototype-shell.md）。
- prd-glossary-format.md 收录范围 4 类含"状态术语"，分组顺序 4 类却无状态——集合不闭合；:74"Design 第五章'核心业务对象及关系'"与模板章名不符。
- design-baseline-format.md"必须字段"标题下列可选的 material_revision，与 :60"缺任一公共字段不合格"冲突；`input_fingerprint` 全文无定义；status 同时允许 completed/success 无语义区分。
- sha256 前缀不统一：material_revision 带 `sha256:`，source_hash 裸 64 位，无换算说明。
- prd-writing-examples.md:77 引用已外置的旧"四段式"写作条款，与现行 6.3#2 八要素不符。
- 闭环要素 writing 七问 vs quality-rubric 自审五要素，自审门比写作门宽。
- design-methodology.md:55"信息密度为'重'"分级全仓无定义。

**Contracts/仓库卫生：**
- review-checklist.md:13 `verdict=max(severity)` 与 :45-47 三档判定互斥（1 P1 到底算"有问题"还是按 max 直接定级），skill 只抄后者。
- status.schema 声明 current_stage 为兼容历史字段，spm-prd/prototype 仍强制写入，归属矛盾。
- 仓库根 `tmp-baseline-payload.txt`、`tmp-baselines.txt` 零引用遗留，应删；67 文件 +7426/-14724 全部未提交，审查基线持续漂移，**应尽快 commit**。

## 6. 正面结论（已验证）

- 上轮 8 P1 全部真修且修法正确，无敷衍修复。
- 12/12 测试套件全绿。
- context-loading.manifest 24 source 全存在、48 章节 ID 逐一命中、packs 零悬空（脚本实测）。
- 已删 4 脚本 + report_completed + full-layered 在活动层零残留；repair_fingerprints/review_findings 遗留 bug 随代码删除消失，无需再跟踪。
- shitpm-host 不加载仓库根新 AGENTS.md（引用均为 codex host base），README.md 判据成立。
- 8 个 test-*.py 无死测试（grep 11 个已删符号零命中）。
- skills 全部 $BUNDLE 路径与 .py 引用真实存在；无"甩命令给用户"、无自动 confirm/自动推进下游 footgun；自检清单未膨胀违反 §1#10。

## 7. 处理建议（按优先级）

1. **表态双门方案**：落地或废弃，消除 plan 与 contract 的活矛盾（§3）。
2. **P1 批量修**：6 处均为单点改动（删一句/改引用/加 if-then/改遍历条件），无流程重构。
3. **commit**：67 文件改动先提交，否则下轮审查无稳定基线，tmp 文件顺手删。
4. P2 按层批量清理，其中"模板缺状态机/操作表骨架"两条建议与 P1 一起修（同属模板与规则不齐）。

本审查未修改任何代码或规则文件，仅产出本报告。
