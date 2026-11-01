# Design 理解与建模规则迭代验收

> 日期：2026-11-01
> 执行依据：`D:/work/ShitPM/docs/plans/2026-11-01-design-modeling-iteration-plan.md`
> 本轮性质：修改 Design、Review、fix、Align 的运行时规则；不修改真实业务项目的 Design、PRD 或 Prototype。

## 1. 结论

| 层级 | 结论 | 依据 |
|---|---|---|
| 规范层 | 通过（本轮范围） | D-1 至 D-7 均已落入运行时文件；来源、建模选择、草图、Review 输入和 fix 分诊只有单点定义 |
| 实现层 | 通过 | 上下文装载测试通过；manifest JSON 可解析；`context-pack.py` full analysis 实际包含新建模选择与模型草图规则 |
| 产物层 | 部分通过 | T-8 两个推导案例均在第一轮草图暴露原模型错误；T-9 完成三个独立案例对照，但执行者已知新规则，不构成盲测 |
| 本轮总状态 | 部分完成 | T-0 至 T-8 完成；T-9 完成对照但不满足“盲测”条件；T-10 已收口，用户对草图负担和首轮可读性的确认仍待完成 |

本报告不宣布 Design 阶段已经彻底解决，也不宣布油站、租金或其他真实项目的 Design 已经修正。

## 2. 深层问题与本轮落点

本轮没有只修“过度设计”和“设计不当”的结果，而是改到四个产生这些结果的位置。

| 深层问题 | 表现 | 本轮落点 |
|---|---|---|
| 理解只存在 AI 内部，写页面前没有人能核对 | 对象拆分、汇总口径和动作边界直到原型阶段才暴露 | 完整模式命中复杂规则时，写页面前展示一段带具体数值的例子和一张记录清单；记录清单写唯一键、动作、角色、可见范围、原始或聚合、列表一行含义 |
| Review 只检查 Design 自身是否自洽，无法判断是否忠于用户说法 | Design Review 有大量 P0/P1，却没有发现核心模型错误 | Review 默认读取 Align 的已确认事实、用户明确回答和用户纠正，Align 只作对照物；新增“模型与用户原话不一致”的 6a 检查 |
| fix 把“改取值”和“模型错了”混在一起 | 用户纠正后仍逐句补丁，越修越偏 | fix 先判断六个模型信号：记录归属、唯一键、对象划分、实体与视图、列表一行含义、角色可见范围；任一项变化或无法判断时回 `spm-design` 重建受影响对象 |
| 规则只增不减，同类判据多处定义 | 检查项越来越多，真正建模被挤掉 | 合并 fix 第 16、17 条；删除对象卡字段清单的重复定义；来源要求、Review 输入和检查项均扩写既有条目，不新增检查器或中间资产 |

Align 的补充规则是“用户纠正必须写回”：用户纠正是 AI 理解错误的证据，要记录原话、推翻的旧理解和纠正后的理解。该规则只写回 `align.md`，不把 Align 升级为事实源。

## 3. 规范层改动

### 3.1 Design

权威文件：

- `D:/work/ShitPM/references/design-analysis-protocol.md`
- `D:/work/ShitPM/references/design-quality-rubric.md`
- `D:/work/ShitPM/skills/spm-design/SKILL.md`

已加入：

- §4.2 B 层新增“建模选择”：列出合并、拆分、派生视图、字段等候选，写明选定项、来源原话和放弃原因；无法区分候选时列为高影响未决。
- 完整模式命中 §5.2 复杂规则时，在写页面前展示模型草图。草图格式是一段带具体数值或人员的例子，加一张记录清单。
- 记录清单必须回答：记录名称、唯一键、产生动作、所属角色、可见角色、展示位置、原始或聚合、相关列表一行代表什么、来源类型；模型推测记录单独标为 AI 补充。
- 用户只指出问题，由 AI 改写并复述；草图不写入 Design 文件，不新增 JSON。
- 完成条件增加“每个事实能回指来源”；可直接回指的已确认事实不重复加标签，模型推测、无来源或跨来源推导的内容标明来源或列入待确认。
- 来源类型为用户原话、材料、用户回答、可直接推导、模型推测；不新增字段列。

### 3.2 Review

权威文件：

- `D:/work/ShitPM/skills/spm-design-review/SKILL.md`
- `D:/work/ShitPM/contracts/design-review-checklist.md`

已加入：

- Review 读取 `output/align/align.md` 的已确认事实、用户明确回答和用户纠正；文件不存在时记入覆盖摘要，不阻塞。
- Review 对照 Align 检查 Design 是否把用户没有说的拆分、合并、实体或动作写成确定事实。
- 检查项 6a 扩为“对象无依据拆分，或模型与用户原话、材料不一致”。
- 检查项 16 扩为“未定义字段或规则，或字段、规则缺少可回指来源”。
- 6a、16 都是既有编号扩写，没有新增检查编号。

### 3.3 fix

权威文件：

- `D:/work/ShitPM/skills/spm-fix/SKILL.md`
- `D:/work/ShitPM/contracts/fix-propagation-rules.md`

已加入：

- fix 第 1 步先做六项模型分诊；模型信号变化或无法判断时回 `spm-design` 重建受影响对象，六项都不变才局部修复。
- 用户给出的清单、具体数值和明确说明代表实际数据的例子仍是权威来源；仅用于解释模型的示例按“示例与模型说明”保留，修改后逐项对照。
- 第 16、17 条合并为第 16 条；原先分散在同一主题纠正、用户清单、具体数值和实际示例判定中的内容，现在统一由第 16 条处理。

### 3.4 Align

权威文件：

- `D:/work/ShitPM/references/align-writing.md`
- `D:/work/ShitPM/skills/spm-align/SKILL.md`
- `D:/work/ShitPM/templates/align.md`

已加入：

- 用户纠正记录原话、被推翻的旧理解、纠正后的理解、影响的已确认事实和来源。
- 旧理解明确标为废弃，不继续沿用。
- 纠正只写回 Align，不在 Align 里生成 Design 方案。

### 3.5 规则减法

| 处理 | 对象 | 净变化 |
|---|---|---|
| 合并 | `fix-propagation-rules.md` 第 16、17 条 | -1 |
| 删除重复 | `design-business-closure.md` 2.1 末段的对象卡字段清单，改为指向 `design-writing.md` 六、对象卡与状态 | -1 |
| 新增 | 用户纠正写回 | +1 |
| 新增 | 建模选择 | +1 |
| 新增 | 模型草图 | +1 |

本轮按可执行判据计净增 1 条。超出部分只有“模型草图”，由 D-1、D-2、D-7 明确要求，且没有既有规则可替代。其余改动均通过合并、删除或扩写既有条目完成；没有新增脚本、检查器、JSON、回执或模板文件。

## 4. 实现层验证

| 检查 | 结果 | 说明 |
|---|---|---|
| `python scripts/python/test-context-loading.py` | 通过 | manifest、章节标记、来源、选择去重、`--module` 分片和产品边界正常 |
| `python -m json.tool contracts/context-loading.manifest.json` | 通过 | JSON 可解析 |
| `context-pack.py --stage design --mode full --pass analysis` | 通过 | full 模式规则包实际包含“建模选择”“模型草图”“记录清单” |
| `python scripts/python/test-resource-integrity.py` | 通过 | 全量资源完整性检查通过；此前 7 项 PRD 侧失败已在同一工作区修复 |

新增内容都落在既有 marker 内，`contracts/context-loading.manifest.json` 不需要新增 section。实际装载使用的临时目录已删除。

## 5. 产物层重放

### 5.1 T-8 推导案例

| 案例 | 模型草图结果 | 对照原 Design | 结论 |
|---|---|---|---|
| 油站日报、月报 | 甲、乙、丙各提交一份个人报表；汇总列表按日期或月份一行；详情一行代表一座油站在该日期的汇总数据，填报人只作来源字段 | 原 Design 第 54、58 行把汇总详情写成逐份展示来源个人报表，存在“按人分行”风险 | 通过：第一轮草图即可暴露 |
| 租金确认收入 | 财务复核到账通过时同时形成正式实收，并按到账登记月份进入收入表；收入表没有独立确认动作 | 原 Design 第 79 行写明收入确认与复核到账“不合并为一个动作” | 通过：第一轮草图直接暴露冲突 |

AI 补充没有写成已确认事实：

- 同一油站存在多个填报人时，是否允许重叠数据、汇总如何合并，仍需用户决定。
- 租金收入表的最终一行粒度需要结合现有报表样表确认；本轮只确认“不设独立确认动作”和“按到账登记时间归月”。

### 5.2 T-9 验证案例

| 案例 | 结果 | 说明 |
|---|---|---|
| 智慧停车区车辆台账 | 明确排除过度合并 | 停车记录与异常记录有不同触发时点、生命周期和修正入口，异常记录不能只当聚合视图 |
| 设备租赁结算单 | 明确排除过度合并 | 汇总单有手工生成入口、独立状态、锁定与退回释放行为，不能只当方向凭据的聚合 |
| 审计整改 | 命中待验证信号 | “经办确认/转办记录、反馈审核记录、整改验收记录、关闭记录”由业务动作自动生成，页面又把它们列为核心数据对象；候选处理是历史事件记录，不是独立对象卡 |

T-9 的限制：三个案例没有参与 T-8 推导，但执行者已经知道新规则，不是盲测。因此只把它记为回归对照，不作为规则泛化有效的证明。

## 6. 仍未验证与不在本轮的事项

1. 用户在模型草图上的首轮阅读负担和指出问题的方式尚未经过真实会话确认。
2. T-9 尚未由不知道新规则的独立执行者盲测。
3. 油站和租金清分的真实 Design 仍保留本轮前的问题；本轮只改规则，真实产物需要单独 fix。
4. 代码简洁之道是否适用于 ShitPM 按用户要求暂停，未纳入本轮。
5. `test-resource-integrity.py` 已通过，不再作为本轮遗留失败。

## 7. 审查后修复

本轮独立审查发现的问题已在同一迭代内修复：

1. 纠正记录只写 `output/align/align.md`，`align-notes.json` 继续遵守原 schema，只保存阻塞和问答判断，不再要求它复制纠正事实。
2. `spm-fix` 命中模型问题时，先读取现有 Align 产物，再调用 `spm-align` 第 5 步写回纠正记录并更新受影响事实，然后进入 `spm-design` 重建对象。
3. 模型草图记录清单增加来源；模型推测记录单独标为 AI 补充，不混入已确认事实。
4. 最终 Design 只要求无法直接回指的模型推测、无来源或跨来源推导内容写明来源或列入待确认；简单模式完成条件同步，Review 检查项 16 改为字段和规则都可追溯。
5. 计划状态改为 T-0 至 T-8 完成、T-9 对照完成但不满足盲测；资源完整性检查的记录补充“未做改动前后基线对照”的限制。
6. 用户示例与确认数据分开；模板新增“示例与模型说明”，只有用户明确说明示例代表实际数据时才进入已确认事实。
7. 模型草图来源增加“示例/模型说明”；`align-notes.json` 只承载阻塞、追问和判断说明，不复制用户回答或纠正事实。

验证：`test-context-loading.py`、`test-resource-integrity.py` 通过，manifest 和 `align-notes.schema.json` 均可解析，目标文件 `git diff --check` 通过，旧表述扫描无残留。

## 8. 实际修改文件

- `D:/work/ShitPM/references/align-writing.md`
- `D:/work/ShitPM/skills/spm-align/SKILL.md`
- `D:/work/ShitPM/templates/align.md`
- `D:/work/ShitPM/skills/spm-design/SKILL.md`
- `D:/work/ShitPM/references/design-analysis-protocol.md`
- `D:/work/ShitPM/references/design-quality-rubric.md`
- `D:/work/ShitPM/references/design-business-closure.md`
- `D:/work/ShitPM/skills/spm-design-review/SKILL.md`
- `D:/work/ShitPM/contracts/design-review-checklist.md`
- `D:/work/ShitPM/skills/spm-fix/SKILL.md`
- `D:/work/ShitPM/contracts/fix-propagation-rules.md`

计划与验收记录：

- `D:/work/ShitPM/docs/plans/2026-11-01-design-modeling-iteration-plan.md`
- `D:/work/ShitPM/docs/reports/2026-11-01-design-modeling-iteration-acceptance.md`
