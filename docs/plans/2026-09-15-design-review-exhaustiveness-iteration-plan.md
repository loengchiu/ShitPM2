# Design 业务闭环质量改进迭代计划

> 日期：2026-09-15
> 状态：待执行
> 决策人：用户 / ShitPM 维护者
> 执行人：后续接手本计划的 AI
> 依据：D:/work/交投软件中心/设备租赁/.workflow/reviews/design-review-1.md 至 design-review-13.md、D:/work/交投软件中心/设备租赁/.workflow/tools/design-surface-audit.py、D:/work/ShitPM/docs/reports/2026-09-15-design-review-exhaustiveness-plan-audit.md、D:/work/ShitPM/docs/reports/2026-09-15-design-plan-second-pass.md、D:/work/ShitPM/docs/reports/2026-09-15-design-plan-third-pass.md、D:/work/ShitPM/docs/reports/2026-09-15-design-plan-final-pass.md、用户于 2026-09-15 对本计划全部方案的确认
> 关联执行报告：D:/work/ShitPM/docs/reports/2026-09-15-design-business-closure-iteration-report.md

<!--
本文件是已确认的执行基线，不是讨论稿，也不是执行报告。
执行者必须按 T-0 至 T-9 顺序推进，不得跳过候选工具准入实验，不得先写通用检查器再补证据。
每一步完成后立即记录证据；失败时按第 8 节降级或停止，不得自行降低阈值。
未经用户明确授权不得 git commit 或 git push。
-->

## 0. 用户已确认的结论

### 0.1 要解决的问题

设备租赁 Design 连续 13 轮 Review 仍不断发现新问题。主要缺陷集中在权限、流程、状态、规则、字段来源、异常恢复和结果去向等业务语义关系，不是文档章节结构。

当前机制有三个直接问题：

1. Design 生成时虽然有自检，但检查的是抽象维度，没有逐个核心业务闭环回读，所以可能分别写了角色、状态和操作，却没有发现它们互相矛盾。
2. 完整 Review 一次读取过大的 Design，只能抽样关注。审查角度每变化一次，就会再发现一批问题，因此多轮不收敛。
3. Fix 按被点名的文本位置修改，没有把问题还原成业务约束并检查全部承载位置，导致“宣称已修复，正文仍有遗漏”。

### 0.2 已确认采用的解决办法

用户于 2026-09-15 确认以下方案全部采用：

1. **Design 生成保持快速**：在现有写作动作内增加核心业务闭环自检；发现已写事实矛盾时直接重写，遇到高影响未知时询问用户；不新增独立检查任务、报告或回执。
2. **Design Review 做完整语义审查**：按主业务对象生命周期或端到端业务闭环拆分审查单元，不按文件机械切分；完成各单元后再检查跨单元交接。
3. **Fix 按业务约束传播**：从问题提炼业务约束，检查系统规则、契约、页面、字段、操作、状态、导出和验收等全部适用承载面，只修改真正受影响的位置。
4. **覆盖闭合替代“第二轮无新增”**：每个适用关系必须有 pass、red、risk、decision 或有正文依据的 excluded 结论；第二轮新增问题数只作参考指标。
5. **脚本只做确定性候选提取**：允许新增候选枚举器，但必须先用 13 轮历史做最小准入实验，且实验分母限定为“当前仍可复现的问题子集”（设备租赁只有 1 个 commit、无逐轮快照，多数历史问题已被 fix-1 至 fix-13 修掉）；脚本不得判断业务合理性、补写产品事实或宣布 Design 语义通过。
6. **候选脚本先用于 Review**：只有历史实验达标才保留；只有同模型同输入的重复 A/B 同时证明质量提升和耗时可接受，才允许接入 Design 生成。
7. **修复确定性基础**：模板继续使用标准页面标题；design-index.py 同时兼容多级编号；仅当已提取 blocks/fields/operations 但 pages=0 时显式失败，unsupported_format 旧项目仍正常降级。多级编号修复会同时启用现有页面清单解析。随之暴露的 4 条页面清单与详情配对错误已实测归因：同一处不匹配被双向各报一次（清单行写 `P-SET-03 月度汇总结算单管理页`，详情标题写同一页名加括注 `（非定向方案 B 专用；…）`），属比较器不归一括注的缺口，不是产品缺陷。处理方式为两侧比对键统一剥尾括注，剥括注后页面配对错误归零。落点必须是独立的比对键函数，只作用于页面清单行与详情页名之间的三处比较（清单侧归一化、detail_names 侧、反向检查侧），不得全局修改 _normalize_label 的返回，因为 page["name"] 会被下游页面级事实消费。该修复只作用于比对键，不改正文事实，且比对键必须保留页面编号前缀，两侧同名不同括注又无编号时不得静默合并，应记 risk 交人工确认。
8. **真实产物验收**：同模型同输入至少重复 3 次；使用未参与方法设计的 held-out 项目或独立准备的隐藏缺陷验证；不能用脚本退出码、静态 PASS 或检查表存在代替质量结论。

### 0.3 执行者必须理解的原理

以“设备归还”为例，真正要检查的是一条完整业务能否连起来：

- 谁能发起归还，能看到哪些设备；
- 什么状态下允许发起；
- 发起后设备和归还单分别进入什么状态；
- 谁负责验收，验收通过和不通过分别产生什么结果；
- 损坏、逾期和费用规则使用什么数据，由谁确认；
- 撤回、驳回、处理失败后如何恢复；
- 最终结果同步到哪些列表、详情、统计和导出。

“权限、状态、规则章节都存在”不能证明这些关系正确。生成、Review 和 Fix 都要围绕具体业务关系工作：机器帮助查找对象和引用，AI 负责业务判断。

## 1. 当前状态与执行边界

### 1.1 当前状态

- **当前已确认事实**：
  - 设备租赁 Design 已完成 13 轮 Review，共记录 P0×2、P1×50、P2×104，共 156 条分级问题记录；第 13 轮另有待决×3，不计入 156。
  - 13 份 Review 没有记录统一的“类别/分类”字段。此前 17/14/14/7 的分布是人工归纳，但缺少逐问题分类台账，因此不作为当前可复核统计；T-0 必须重新建立分类明细后才能使用分类比例。
  - 第 3 轮和第 5 轮曾宣布通过，随后第 4 轮和第 6 轮继续发现高影响问题。
  - 第 5 轮以后，第 6 至第 13 轮仍发现 P1×29、P2×86。
  - 第 10 轮加入项目专项脚本后，第 11 至第 13 轮仍发现 P1×12、P2×28。
  - 第 11 轮复查第 10 轮修复时，20 项中有 6 项未真正闭环，其中 5 项属于只改点名位置、漏掉同一约束的其他承载面。第 12 轮使用“约束 × 承载面 × 现状”枚举和修后同族回扫后，17 项全部落地，承载面从 4 个扩展到 9 个，证明该做法有效但尚未固化进通用契约。
  - 设备租赁 Design 于 2026-09-15 18:28 被 fix-13 更新。18:45 重测快照为：5 文件 161698 字节，4 份人读 Design 159767 字节，模块设计单文件 94689 字节；执行 T-0 时必须再次重测并冻结，不能把此快照当永久常量。
  - 当前未修改代码时，design-index.py 在设备租赁真实 Design 上得到 pages=0、blocks=14、fields=89、operations=7、errors=50。把真实修复施加到 _normalize_label（多级编号）后的探针结果为 pages=4、blocks=14、fields=89、operations=7、errors=31，新增 page_summary_missing_detail×2 与 page_detail_missing_summary×2；在此基础上再对两侧比对键剥尾括注，结果为 pages=4、errors=27，页面配对错误归零。该 4 条是比对键括注归一化缺口，不是产品缺陷：设备租赁 P-SET-01 至 P-SET-04 四个页面在清单与标题各出现一次，仅 2 个标题带括注。旧格式夹具为 pages/blocks/fields/operations=0/0/0/0 且带 unsupported_format，必须继续走 legacy 降级。按错误码分组：50 条为 block_without_page×14、missing_attribute×14、combined_field_name×9、duplicate_entity×5、block_without_items×5、semantic_conflict×3；修复后 27 条为 missing_attribute×14、combined_field_name×9、block_without_items×4，即消失的 23 条全部来自页面提取失败及其连带错误，剩余三类与本轮提取器修复无关。compile 输出的 ok 字段在修复前后均为 false，不能用作本轮判据。
  - prd-consistency-check.py 会输出 possible_omission 和 permission/state cannot_extract，但仍启用缺页 Index，页面实体和页面级权限事实没有参加对账；prototype-consistency-check.py 是同一 Index 的第二个真实消费者，也需要验证拒绝关键空集。
  - test-phase7-scenarios.py 的准确现状是：F1 有真实断言；F2 计算 has_dead_state 但未使用，且当前夹具被 stage-prep.py 判为终态，预期断言本身不成立；F3 至 F6 没有真实断言；F7 只断言规范文档措辞。
- **当前已观察到的表象**：
  - Review 每轮换一个角度就能继续发现新问题。
  - 固定轴脚本可能出现假阴性、分块错误和文本归一化误差。
  - Fix 报告的修复声明与当前正文不一致。
  - 确定性 Index 能以 enabled 状态向下游提供缺少页面的结果。
- **当前尚未确认的事项**：
  - 通用候选枚举对“当前仍可复现的历史 P1 子集”的覆盖率和误报率。设备租赁项目只有 1 个 commit（133d0a7），无逐轮快照，50 个 P1 产自 13 个不同修订且多数已被 fix-1 至 fix-13 修掉，因此不能把 50 直接当作覆盖率分母；分母口径见 T-0 与 T-2。
  - 候选输入接入 Design 生成后的实际耗时。
  - 新 Review 方法在 held-out 项目或隐藏缺陷上的效果。
- **本轮目标**：
  - Design 展示前能消除明显的权限、流程、状态、规则和异常断点。
  - 完整 Review 能说明实际审过哪些业务闭环和关系，并在一次完整 Review 内形成闭合结论。
  - Fix 能覆盖同一业务约束的全部适用承载位置。
  - 候选脚本只有在真实历史验证达标后才进入活动流程。

### 1.2 执行边界

- **本轮范围**：
  - 修改 Design 生成、Design Review、Fix 的行为协议及其共享语义规则。
  - 修复 design-index 页面标题解析和关键实体空集处理。
  - 修复与本轮直接相关的失真测试。
  - 完成候选枚举最小实验、重复 A/B、held-out Review 和 Fix 闭环验证。
- **本轮不修改**：
  - D:/work/交投软件中心/设备租赁/output/design 下的正式产品事实。
  - 设备租赁第 13 轮问题本身。
  - PRD 和 Prototype 的语义方法。
  - D:/work/ShitPM/references/prd-writing-rules.md 的现有未提交修改。
  - D:/work/ShitPM/docs/reports/2026-09-15-design-review-exhaustiveness-plan-audit.md。
- **允许修改的层**：规范层、确定性实现层、测试和验证产物层。
- **执行前置条件**：
  - 在 D:/work/ShitPM 工作区的 main 分支执行。
  - 开始前记录 git status，保留并避开用户已有修改。
  - 所有真实项目试验在隔离副本中执行，不改正式 Design。
  - 明确 A/B 隔离边界：`~/.workbuddy/skills/spm-design` 是指向 D:/work/ShitPM/skills/spm-design 的 junction（`readlink -f C:/Users/guduj/.workbuddy/shitpm` 为 `/d/work/ShitPM`），活动工作区本身就是 Skill 与 reference 的装载源。因此规范层改动无法用 git worktree 隔离，A 组的隔离方式见 T-8。
- **不可逆动作**：无。不得 commit、push、发布或修改外部系统。

## 2. 表象 → 根因映射

| ID | 表象 | 级别 | 根因 ID | 根因所在层 | 复现证据 | 同根因的其他表象 | 当前判断 |
|---|---|---|---|---|---|---|---|
| P-1 | 第 3、5 轮宣布通过后仍出现新 P1 | P1 | RC-1、RC-2、RC-3 | 规范/执行 | design-review-3.md 至 design-review-6.md | P-2、P-3 | 已确认 |
| P-2 | 第 6 至第 13 轮每轮换角度继续发现问题 | P1 | RC-1、RC-2 | 规范/执行 | design-review-6.md 至 design-review-13.md | P-1 | 已确认 |
| P-3 | 第 13 轮只换核对面即新增 P1×3、P2×4 | P1 | RC-1、RC-2 | 规范/执行 | design-review-13.md | P-1、P-2 | 已确认 |
| P-4 | 专项脚本先报 0 命中，人工仍找到高影响问题 | P1 | RC-4 | 实现/方法 | design-review-11.md 至 design-review-13.md | P-5 | 已确认 |
| P-5 | 固定脚本出现整块子串、分块和归一化问题 | P1 | RC-4、RC-6 | 实现 | design-surface-audit.py 与对应 Review | P-4、P-7 | 已确认 |
| P-6 | 20 项修复中 6 项未真正闭环 | P1 | RC-5 | 规范/执行 | design-review-11.md | P-8 | 已确认 |
| P-7 | 正文有页面标题，Index 却 pages=0 | P1 | RC-6 | 实现 | 2026-09-15 隔离复现实验 | P-5、P-9 | 已确认 |
| P-8 | 修复新句与既有操作或规则冲突 | P1 | RC-5 | 规范/执行 | design-review-11.md 至 design-review-13.md | P-6 | 已确认 |
| P-9 | 测试显示 PASS 但没有真实断言 | P1 | RC-7 | 验证 | test-phase7-scenarios.py | P-1、P-4 | 已确认 |

## 3. 根因证据

### RC-1｜抽象检查维度没有展开为具体业务关系

- **根因描述**：现有规则会要求检查权限、状态、规则和异常，但没有要求先枚举当前业务中实际存在的角色、对象、状态、动作、数据范围和结果关系，再逐项判断。
- **复现步骤**：
  1. 对照 design-review-6.md 至 design-review-13.md。
  2. 查看每轮新增的问题类型和承载位置。
  3. 可观察到每增加一个核对角度，就会出现上一轮未覆盖的新实例。
- **复现结果**：固定维度被检查过，不代表该维度下每个适用实例都被检查过。
- **为什么不是表象级补丁**：继续向清单增加“单据类型”“导出”“自动动作”等词，只会形成更长的固定轴，未来仍会出现新的关系类型和写法变体。
- **现有机制为什么没解决**：Design 自检和 Review 检查项没有统一的适用判据、排除依据和逐实例完成条件。
- **证据边界**：
  - **已证明**：13 轮中固定角度反复漏掉具体实例。
  - **仅推断**：候选提取可能降低漏找对象的概率。
  - **待验证**：候选提取的覆盖率和误报率，由 T-2 验证。第 13 轮已证明除实例遗漏外还存在“核对维度遗漏”，共享方法必须先纳入对象细分类型和属性集差集。

### RC-2｜单次审查范围超过注意力预算

- **根因描述**：2026-09-15 18:45 快照中，4 份人读 Design 达到 159767 字节，模块设计单文件达到 94689 字节。即使检查项正确，一个审查者也会在大范围文本中采样关注；T-0 必须对执行时版本重新测量。
- **复现步骤**：
  1. 统计设备租赁 Design 文件大小。
  2. 对照连续 Review 的新增角度和新增问题。
  3. 观察同一批文本在换角度后立即产生新命中。
- **复现结果**：整套 Design 或一个超大模块文件不能稳定作为一个不可拆分审查单元。
- **为什么不是表象级补丁**：把检查清单改成更长的实例表仍会增加单次负担。
- **现有机制为什么没解决**：完整 Review 只定义范围，没有定义执行单元及跨单元合并方法。
- **证据边界**：业务闭环是本轮采用的切分原则，具体单元数量由目标 Design 的真实生命周期决定，不设置机械字数阈值。

### RC-3｜Review 过早读取历史结论，独立审查被旧答案污染

- **根因描述**：spm-design-review 当前第 1 步读取最近 Review。审查者容易先复验已知问题，再把“旧问题没有复发”误当成当前 Design 已全面通过。
- **复现结果**：第 3、5 轮出现错误通过，后续仍发现新的高影响问题。
- **修复原则**：先完成当前 Design 的单元划分、关系覆盖和问题集冻结，再读取历史 Review 做复发核对。
- **证据边界**：历史 Review 仍有价值，但只能用于回归核对，不能生成当前问题集。

### RC-4｜固定轴脚本承担了不适合程序化的语义判断

- **根因描述**：项目专项脚本把已知问题写成关键词和固定核对轴，无法稳定处理新关系类型、同义写法和业务适用性。
- **复现结果**：第 11 至第 13 轮脚本曾先报告 0 硬命中，人工仍发现 P1×12、P2×28。
- **为什么不是表象级补丁**：继续加正则会把历史问题固化为脚本，不会获得通用业务理解。
- **修复原则**：程序只提取实体、位置、显式引用和 cannot_extract；AI 逐候选判断业务语义。
- **证据边界**：候选提取是否值得保留尚未证明，必须先执行 T-2。

### RC-5｜Fix 传播的是被点名文本，不是业务约束

- **根因描述**：当前 Fix 重点是唯一事实归属和 Design 向下游传播，没有要求在 Design 集合内部检查同一约束的全部承载位置、写法变体和同类实例。
- **复现结果**：第 11 轮复核的 20 项中有 6 项未闭环，其中 5 项漏掉其他承载面，1 项产生新冲突；这是改进前证据。第 12 轮使用“约束 × 承载面 × 现状”枚举和修后同族回扫后，17 项全部落地，承载面从 4 个扩展到 9 个，已经证明该做法有效。
- **为什么不是表象级补丁**：逐条增加搜索关键词仍会漏掉不同表述；有效动作目前只存在于项目实践，没有成为 spm-fix 的稳定契约。
- **修复原则**：把第 12 轮已验证的做法固化为“业务约束 × 承载面 × 对象（含细分类型）”，同时检查整页、整列属性和写法变体，修改后逐位置回读。第 13 轮在 Fix 已明显收敛后仍新增 P1×3、P2×4，说明当前主要瓶颈已经迁移到 Review 覆盖，因此 T-5 的优先级高于 T-6。

### RC-6｜确定性索引允许关键实体静默为空

- **根因描述**：design-index.py 的 _normalize_label 只剥离单级编号，无法正确处理“4.2 页面：...”；页面提取为空没有形成消费者必须拒绝的 fatal 错误。
- **复现步骤**：
  1. 在设备租赁 Design 隔离副本执行 design-index.py compile。
  2. 记录 pages=0、errors=50。
  3. 仅去除 4 个页面标题中的多级编号并再次执行。
  4. 手工只修改页面标题文本时记录 pages=4、errors=27；该值没有启用页面清单解析，不能作为代码修复的完成判据。
  5. 在真实修复点 _normalize_label 应用多级编号归一化时记录 pages=4、errors=31；新增的 4 条页面配对错误来自页面清单行与详情标题的括注差异，属比对键未归一括注。
  6. 在步骤 5 基础上再对两侧比对键剥尾括注，记录 pages=4、errors=27，页面配对错误归零。
- **已证明影响**：页面实体没有进入 PRD 结构预期；页面角色和数据范围无法由 Index 提供。_FATAL_ERROR_CODES 和 _is_fatal_index_error 当前没有真实调用方，只修改集合不会改变消费者行为；prd-consistency-check.py 的空 expected 分支仍硬编码 enabled=true，prototype-consistency-check.py 也会继续使用非空但缺页的 Index。旧格式 Design 可能含“页面说明”等普通标题，但 pages/blocks/fields/operations 全为 0，并依赖 unsupported_format 分支继续降级。
- **修复原则**：page_extraction_empty 使用结构判据“blocks + fields + operations > 0 且 pages == 0”，不得使用“标题含页面”之类宽文本信号。load_verified_index 必须先处理 unsupported_format，再按既有 invalid_type 的返回语义处理 page_extraction_empty；在两个真实消费者的活跃分支中拒绝该 Index，或把 _is_fatal_index_error 接入真实返回路径。不得只修改死集合。页面清单启用后暴露的 4 条配对错误按 F-5（Index 关键实体完整性）处理：用独立比对键剥尾括注后归零，不修改设备租赁产品事实；比对键只作用于三处配对比较、保留页面编号前缀，无编号且同名不同括注时不得静默合并，应记 risk。
- **证据边界**：Index 完整只证明实体提取正常，不证明业务语义正确。

### RC-7｜验证验证了 PASS 文本，没有验证真实行为

- **根因描述**：test-phase7-scenarios.py 的部分场景没有断言或直接写入 PASS；单次生成和同源缺陷集也不能证明方法有效。
- **修复原则**：确定性代码使用真实断言；语义质量使用同模型同输入 n≥3、独立 Review、held-out 项目或隐藏缺陷验证。
- **证据边界**：静态测试只证明确定性机制，不能代替产物层验收。

## 4. 三层归属

| 根因/改动 ID | 根因或改动 | 修复层 | 规范层依赖 | 实现层依赖 | 产物层证据 | 不替代的验收 |
|---|---|---|---|---|---|---|
| RC-1 / F-1 | 建立业务闭环和关系实例方法 | 规范 | 新共享 reference | 无强制脚本 | 生成和 Review 覆盖记录 | 规则存在不证明模型执行 |
| RC-1 / F-2 | Design fast 核心闭环自检 | 规范 | F-1 | 无强制脚本 | T-8 Design A/B | Skill 文本修改不证明模型执行 |
| RC-2、RC-3 / F-3 | Review 分单元、当前优先、历史后读 | 规范 | F-1 | 可选候选输入 | held-out Review 报告 | 报告存在不证明覆盖正确 |
| RC-5 / F-4 | Fix 语义影响闭环 | 规范 | F-1 | 现有文件检索 | 隔离副本修复对照 | diff 存在不证明无漏改 |
| RC-6 / F-5 | Index 多级编号和关键空集失败 | 实现 | 当前页面标题规范 | design-index 与消费者 | 真实 Design 复现结果 | pages>0 不证明语义正确 |
| RC-4 / F-6 | 候选枚举准入实验 | 实现/证据 | F-1 的关系定义 | 临时实验代码 | 历史覆盖率和误报率 | 候选不等于缺陷 |
| RC-7 / F-7 | 修复失真测试和语义验收 | 验证/产物 | 最终行为契约 | 测试和试验环境 | n≥3 A/B、held-out | 测试 PASS 不替代真实产物 |

### 4.1 规范层

- **权威文件**：
  - 新增 D:/work/ShitPM/references/design-business-closure.md。
  - 按需修改 D:/work/ShitPM/references/design-analysis-protocol.md：仅当新增共享规则与现有分析协议重复时，把重复部分改为指针；T-3 必须明确改或不改，不得留下两份定义。
  - 修改 D:/work/ShitPM/references/design-writing.md 中现有 design-writing-self-check marker 章节。
  - 修改 D:/work/ShitPM/references/design-quality-rubric.md 中现有 design-verification-self-review marker 章节。
  - 修改 D:/work/ShitPM/skills/spm-design/SKILL.md。
  - 修改 D:/work/ShitPM/skills/spm-design-review/SKILL.md。
  - 修改 D:/work/ShitPM/contracts/design-review-checklist.md。
  - 修改 D:/work/ShitPM/skills/spm-fix/SKILL.md。
  - 修改 D:/work/ShitPM/contracts/fix-propagation-rules.md。
  - 修改 D:/work/ShitPM/contracts/context-loading.manifest.json，确保 Design 写作期实际加载 fast 规则。优先把新 section 加入现有 pack；只有确需新增 pack 时，才同步修改 D:/work/ShitPM/contracts/subagent-context-contract.md 的角色白名单表。
- **本轮修复的规则**：
  - 定义业务闭环、关系实例、适用、排除、risk、decision 和承载面。
  - 分别定义 Design fast、Review full 和 Fix propagation 的责任与成本。
  - 规定 Review 当前状态优先、分单元审查、跨单元合并和覆盖闭合。
- **规则不负责的内容**：不替用户决定具体项目的角色权限、状态、数据范围、规则和系统边界。
- **规范层完成条件**：同一概念只有一个权威定义；三个 Skill 通过指针引用，不复制多份定义；高影响未知继续交用户决定。

### 4.2 实现层

- **权威实现或真实消费者**：
  - D:/work/ShitPM/scripts/python/design-index.py。
  - D:/work/ShitPM/scripts/python/prd-consistency-check.py。
  - D:/work/ShitPM/scripts/python/prototype-consistency-check.py。
  - D:/work/ShitPM/scripts/python/test-design-index.py、test-prd-consistency-semantics.py、test-prototype-consistency-check.py。
  - 候选实验达标后才允许新增 D:/work/ShitPM/scripts/python/design-relationship-candidates.py。
- **本轮修复的机制**：页面标题归一化；在 unsupported_format 之后使用“blocks + fields + operations > 0 且 pages == 0”的关键空集 fatal；消费者拒绝缺页 Index；候选实体、对象细分类型、属性集合与显式引用提取。
- **实现层不承担的判断**：业务规则是否合理、角色是否应有权限、状态是否符合产品目标、未知事实如何拍板。
- **实现层完成条件**：确定性行为有直接测试；候选实验不达标时生产脚本不存在；消费者没有静默降级。

### 4.3 产物层

- **目标产物**：
  - D:/work/ShitPM/docs/reports/2026-09-15-design-business-closure-iteration-report.md。
  - 隔离副本中的 A/B Design、held-out Review 和 Fix 验证差异，路径记录在执行报告中。
- **本轮要证明的结果**：生成阶段减少高影响断点；Review 覆盖可说明；Fix 无同约束漏改；耗时受控。
- **不接受的替代证据**：design-set check、Index 编译 exit 0、候选数量、Skill 关键词存在、静态测试 PASS、第二次 Review 无新增。
- **产物层完成条件**：完成同模型同输入 n≥3 A/B、held-out 盲审和多承载面 Fix 验证；未决事实没有被静默补全。

## 5. 用户必须决策的事项

以下决策已由用户于 2026-09-15 全部确认，执行者不得重新提问或自行改选：

| ID | 决策问题 | 已确认结论 | 影响层 | 当前状态 |
|---|---|---|---|---|
| D-1 | Design、Review、Fix 的总体机制 | 生成快速闭环自检；Review 分闭环完整审查；Fix 按业务约束传播 | 规范 | 已确认 |
| D-2 | 候选枚举是否进入本轮 | 先做最小历史实验；达到门槛才保留；失败立即删除 | 实现/证据 | 已确认 |
| D-3 | Review 单元如何切分 | 按主业务对象生命周期或端到端闭环，不按文件机械切分 | 规范 | 已确认 |
| D-4 | Review 如何判定收敛 | 以覆盖闭合和 held-out 为主；第二轮新增数只作参考 | 规范/产物 | 已确认 |
| D-5 | pages=0 如何修 | 模板保持标准标题；提取器兼容多级编号；unsupported_format 先降级；仅当 blocks+fields+operations>0 且 pages=0 时 fatal；两个消费者拒绝该关键空集；4 条页面配对错误经实测定性为比对键括注归一化缺口，按 F-5 剥尾括注后归零 | 实现 | 已确认 |
| D-6 | Design fast 的成本边界 | 同模型同输入至少 3 次；墙钟中位数不超过基线 1.25 倍 | 产物 | 已确认 |

只有执行中出现新的高影响产品事实、不可逆动作或本计划未覆盖的架构分支时，才需要再次请求用户决策。

## 6. 执行顺序

| 步骤 | 前置条件 | 层级 | 动作 | 修改范围 | 交付物 | 完成判据 | 失败后的动作 |
|---|---|---|---|---|---|---|---|
| T-0 | 无 | 证据 | 记录 baseline commit；重测并冻结当前 Design 字节数、Index 输出和逐问题分类台账；选取候选实验、Fix 和 held-out 样本 | 只读设备租赁 Review/Design；临时工作目录 | 执行报告中的快照与样本清单 | 数字来自执行时版本且可逐项复核，held-out 未泄露给审查者 | 数据有漂移则以新快照更新，不沿用旧常量 |
| T-1 | T-0 | 实现 | 先写失败测试，再修复 Index 多级编号、比对键括注归一化、结构式关键空集 fatal 和两个消费者；保留旧格式降级 | design-index.py、prd-consistency-check.py、prototype-consistency-check.py、对应测试 | 代码和测试差异 | 在 T-0 冻结快照上 pages 0→4，且 block_without_page、duplicate_entity、semantic_conflict 与页面配对错误全部归零（2026-09-15 18:45 快照为 pages 0→4、errors 50→27；快照变化时按新基线重算并记录新旧值）；两个消费者拒绝关键空集；unsupported_format 仍降级；页面配对错误归零且未误合并同名页面 | 未修复则停止后续候选实验 |
| T-2 | T-1 | 证据/实验 | 在临时代码中实现最小候选枚举，按 T-0 台账核对“当前仍可复现”的历史 P1 子集 | 临时目录；达标后才进入 scripts/python | 候选可行性结果 | 对可复现子集覆盖率≥60%，错误候选<真实命中×2，不可复现项数与 cannot_extract 明确 | 未达标则删除实验，走无脚本方案 |
| T-3 | T-2 已得结论 | 规范 | 先把对象细分类型和属性集差集纳入关系维度，再编写共享规则并更新真实加载指针 | reference、analysis protocol、writing/rubric marker、manifest | 共享规则与加载测试 | 维度清单含对象细分类型和属性集差集；fast/full/fix 定义单一；目录、marker 和消费者守卫通过 | 资源完整性或维度缺失则不得改 Skill |
| T-4 | T-3 | 规范 | 在 design-writing-self-check 与 design-verification-self-review 既有章节中增量改写自检，并同步 spm-design 指针 | design-writing.md、design-quality-rubric.md、spm-design/SKILL.md | Design fast 行为 | 不新增重复自检章节；自检仍在一次写作动作内，无报告和第二任务 | 若形成独立门禁或重复规则则回退 |
| T-5 | T-3 | 规范 | 改写 Design Review 的执行顺序、分单元方法、单元维度差集和收敛条件 | spm-design-review、design-review-checklist | Review full 行为 | 当前状态先审、每单元先做维度差集、历史后读、覆盖闭合、单报告 | 若漏维度差集、按文件切分或先读历史则修正 |
| T-6 | T-5 | 规范 | 先将问题归入约束类别并与关系维度清单做类别差集，再将“约束 × 承载面 × 对象（含细分类型）”与同族回扫固化进 Fix，并检查整页/整列属性缺失 | spm-fix、fix-propagation-rules | Fix closure 行为 | 约束类别差集与三维影响面逐项回读，仍是定点修改 | 若漏类别差集、只按字符串同族或演变成整篇重写则修正 |
| T-7 | T-1 | 验证 | 用“状态仅作目标态出现、无自有行”的确定夹具重写 F2 并形成真实死状态断言；为 F3-F6 补真实断言或删除假 PASS | test-phase7-scenarios.py 及直接测试；只有实测需要时才改 stage-prep.py | 真实红绿测试 | F2 检出 is_terminal=false 且 transitions=0；有“—”自有行的终态不误报；F3-F6 无常量 PASS | 不得删除已可确定的 F2 场景 |
| T-8 | T-4 至 T-7；T-0 已记录 baseline commit；可调用同一便宜模型的独立子代理 | 产物 | A 组串行运行（按显式路径回退规范层改动回到 baseline 后跑 3 次，再恢复并跑 B 组 3 次），不使用 worktree；每组 3 个独立代理处理同一输入，产物分目录隔离；同时做 Fix 验证 | 隔离输入与输出目录、baseline 只读副本（备用） | 6 份原始 Design、A/B 与 Fix 对照、两组装载哈希 | 两组哈希不相等；质量改善且时间中位数≤1.25 倍；运行上下文可复核；Fix 无漏改 | 隔离失效或无同模型执行通道则产物层部分完成，不得伪造 harness |
| T-9 | T-5、T-8 | 产物 | 执行 held-out Review，汇总三层结果并清理临时资产 | 隔离项目、执行报告 | 最终执行报告 | held-out 达标，临时资产清理，工作区范围正确 | 未达标则报告部分完成，不伪报成功 |

## 7. 每步完成判据

### 7.1 步骤判据

#### T-0｜冻结验证基线

- **输入**：D:/work/交投软件中心/设备租赁/.workflow/reviews/design-review-1.md 至 design-review-13.md。
- **动作**：
  1. 记录 git rev-parse HEAD，作为后续 A 组 baseline commit。
  2. 复核 P0×2、P1×50、P2×104，并单独记录第 13 轮待决×3；156 只代表分级问题记录。
  3. 重新统计执行时 Design 的 5 文件总字节、4 份人读字节和模块文件字节；记录文件最后修改时间。2026-09-15 18:45 的 161698/159767/94689 只作为对照，不直接沿用。
  4. 在未修改代码的隔离副本重跑 Index，冻结 pages、blocks、fields、operations、errors 和错误码分布。
  5. 为 50 个 P1 逐项记录 Review 编号、问题编号、主类别、分类依据、涉及对象、承载面，以及“在当前 Design 上是否仍可复现”的判定与依据；分类比例必须从该台账计算，不能沿用无明细的 17/14/14/7。设备租赁只有 1 个 commit、无逐轮快照，已被 fix-1 至 fix-13 修掉的 P1 在候选实验里“找不到”属标的消失而非方法失效，必须单独统计不可复现项数，作为 T-2 的分母口径依据。可复现判定标准：该 P1 的缺陷陈述在当前 Design 正文中仍能找到对应的事实缺口（位置可不同、表述可变化）记为可复现；正文已改写导致标的消失记为不可复现；无法判定记为 cannot_judge，从分子和分母同时剔除并单独计数。
  6. 从第 11 至第 13 轮选至少 3 个多承载面 Fix 问题，在正式 Design 的隔离副本中使用。
  7. 在方法实现前确定 held-out 来源；优先使用未参与本方法形成的复杂项目，或由独立准备方生成 8 至 12 个隐藏缺陷变体。
- **必须留下的证据**：baseline commit、执行时文件快照、Index 原始输出、逐问题分类台账（含可复现标记与不可复现项数）、样本路径和选择时间。
- **完成判据**：统计可复核；台账明确给出“当前可复现 P1 子集”的条数与不可复现条数；候选实验、Fix 和 held-out 三类样本用途分开；held-out 答案不提供给执行 Review 的上下文。
- **不能据此宣布的结论**：不能说明新方法有效。

#### T-1｜修复 Index 确定性缺陷

- **输入**：design-index.py、prd-consistency-check.py、prototype-consistency-check.py、test-design-index.py、test-prd-consistency-semantics.py、test-prototype-consistency-check.py、设备租赁 Design 隔离副本。
- **动作**：
  1. 先添加多级编号页面标题的失败测试。
  2. 添加结构式关键空集测试：blocks + fields + operations > 0 且 pages == 0 时产生 page_extraction_empty；不得以标题包含“页面”作为信号。夹具构造要点：字段与操作提取挂在页面或区块之下，因此要命中该判据，夹具必须包含区块标题（如“### 区块：X”）并在其下放置字段或操作，且全文不含任何页面标题。反例必须同时断言：只有“## 字段定义”表而无区块、无页面的 Design 实测为 pages/blocks/fields/operations=0/0/0/0 并带 unsupported_format，测不到目标分支，它必须继续 legacy 降级，不得报 page_extraction_empty。
  3. 扩展 _normalize_label，使单级和多级数字编号均能归一化，不破坏中文编号和无编号标题。
  4. 统一页面清单行与详情标题的比对键口径：新增独立的比对键处理（剥除名称尾部的括注），只作用于 design-index.py 页面清单与详情配对的三个比较点，使同一实体不因一侧带括注而双向各报一次。不得改 _normalize_label 的全局返回，因为 page["name"] 会被下游页面级事实消费。比对键必须保留页面编号前缀；两侧同名、括注不同且无编号可判别时不得静默合并，应记 risk。
  5. 增加旧格式回归夹具：pages/blocks/fields/operations=0/0/0/0 且包含 unsupported_format，即使正文出现“页面说明”等普通标题也必须继续 legacy 降级。
  6. 生成 page_extraction_empty 错误。_FATAL_ERROR_CODES 和 _is_fatal_index_error 当前没有调用方，不得只把错误码加入集合后宣布完成。
  7. load_verified_index 的顺序必须是：先处理 unsupported_format 并返回现有降级结果，再按既有 invalid_type 的返回写法处理 page_extraction_empty；不得在 unsupported_format 之前执行新 fatal。design-index.py 的 no_entities_extracted 只属于 CLI diagnostics，不得与持久 Index 的 page_extraction_empty 合并。
  8. 在 load_verified_index 的真实返回路径接入 fatal 判断，或分别在 prd-consistency-check.py 和 prototype-consistency-check.py 的活跃消费分支中拒绝该错误；两条消费者路径都必须有回归测试。
  9. 修正 prd-consistency-check.py 中 expected 为空仍返回 enabled=true 的语义。注意路径边界：当 pages=0 而 blocks/fields 非空时 expected 实体并不为空，不会进入 `not expected` 这条硬编码分支，因此真正关闭静默空转的是第 8 步的消费者拒绝；本步只作兜底，必须有测试覆盖该分支，不能只改文本后宣布完成。
  10. 在 T-0 冻结快照上验证真实修复结果，判据必须是结构式而非单一数字：pages 由 0 变为 4；block_without_page、duplicate_entity、semantic_conflict 与页面配对错误全部归零；missing_attribute、combined_field_name、block_without_items 三类计数与 T-0 冻结基线一致，不增不减。2026-09-15 18:45 快照的对照值为 errors 50→31→27；修复后剩余 27 条由 missing_attribute×14、combined_field_name×9、block_without_items×4 构成，属 Design 写作层既有问题，与本轮提取器修复无关，不得为降低错误数去修改设备租赁产品事实或放宽这三类错误的判定语义；本轮不修改设备租赁 Design 正文。
- **必须留下的证据**：失败前测试输出、修复后测试输出、两个消费者的红绿测试、隔离副本按错误码分组的修复前后对照（2026-09-15 18:45 快照为 pages 0→4、errors 50→31→27）。
- **完成判据**：标准标题、多级编号标题均正确提取；结构式关键空集明确失败；PRD 和 Prototype 两个消费者都拒绝关键空集；unsupported_format 旧项目继续降级可用；页面配对错误归零且未误合并同名页面；既有测试无新增失败；剩余错误码构成与 T-0 冻结基线一致，未通过放宽判定语义换取数量下降。
- **不能据此宣布的结论**：不能宣布 Design 语义正确或候选枚举有效。

#### T-2｜候选枚举最小准入实验

- **输入**：T-0 的逐问题台账（含“当前仍可复现”标记）、T-1 修复后的 Index、设备租赁 Design 隔离副本。
- **动作**：
  1. 在临时目录实现最小提取器，只读取明确实体、对象细分类型、属性集合、来源位置、显式引用和解析失败。
  2. 对需要用正文串匹配字典或矩阵的候选先做确定性串归一化：剥离括注，剥离“全部字段”“与…入口”类后缀，并按并列分隔拆成独立项。
  3. 输出 candidate 和 cannot_extract，不输出 pass、red、risk、decision。
  4. 人工逐条核对哪些“当前仍可复现”的 P1 能由候选提示触达；已被修复、在现版本 Design 上不复现的 P1 单独计数，不计入覆盖率分子或分母。
  5. 统计真实命中、错误候选、未覆盖的可复现 P1、不可复现 P1 数和 cannot_extract；单独复现第 13 轮⑯轴 7→3、④轴 3→0 的误报下降基线。
- **准入门槛**：
  - 对“当前仍可复现的历史 P1 子集”覆盖率 ≥ 60%。若该子集少于 15 条，改从 Review 引用的正文重建 8 至 12 个最小片段夹具作为分母，并在报告中写明分母口径、夹具构造方式和不可复现项数。
  - 错误候选数量 < 真实命中数量的 2 倍。
  - 输出能定位到 Design 文件和正文位置。
  - 串归一化后不得重新出现第 13 轮⑯轴 7 条、④轴 3 条的已知解析噪声；应达到对应 3 条和 0 条基线，或在报告中证明输入已变化。
  - cannot_extract 不得被当作无问题。
- **通过后**：才允许将代码整理为 D:/work/ShitPM/scripts/python/design-relationship-candidates.py，并增加直接测试和真实消费者指针。
- **失败后**：删除临时代码，不创建生产脚本；T-3 至 T-9 使用 instruction-only 的分闭环方案继续。
- **不能据此宣布的结论**：候选命中不等于业务缺陷成立，也不证明适合接入 Design fast。

#### T-3｜建立共享业务闭环规则

- **输入**：RC-1 至 RC-5、T-2 结论、现有 design-analysis-protocol.md。
- **动作**：新增 design-business-closure.md，至少定义：
  1. 业务闭环单元：一个主业务对象生命周期或一个端到端业务结果。
  2. 关系实例：角色、对象、对象细分类型、状态/前提、动作、数据范围、规则/来源、属性/字段集合、结果/去向、异常/恢复的实际组合。存在统称/分类表述时，必须按细分类型分别判断权限、可见性、状态和数据范围；同类页面或对象必须对属性集做差集，识别整页、整列或整组字段缺失。
  3. 适用：Design 已声明两端，或一端明确引用另一端。
  4. 排除：必须引用正文事实；无依据时不得排除。
  5. 不确定：一般语义不确定记 risk；会改变流程、权限、状态、数据范围、系统边界或验收的记 decision。
  6. Design fast：只回读核心闭环和高影响关系，在同一写作动作内修正。
  7. Review full：分单元逐实例判断，再做跨单元合并。
  8. Fix propagation：业务约束 × 影响对象 × 承载面，修改后逐位置回读。
- **必须留下的证据**：共享 reference、manifest 或 Skill 真实指针、context-loading 和 resource-integrity 测试结果。
- **完成判据**：定义只维护一份；三个 Skill 不复制完整定义；Design 写作 pass 能实际装载 fast 章节；新增 reference 超过 100 行时包含 ## 目录；每个 selector=marker 的 section 在源文件中恰好有一对 start/end marker。优先把 section 加入现有 pack；若新增 pack，必须同步 subagent-context-contract.md 的角色白名单。

#### T-4｜改造 Design fast

- **输入**：spm-design/SKILL.md、design-analysis-protocol.md、共享业务闭环规则。
- **动作**：
  1. 保留现有 simple/full、A/B/C 和 design-editor 责任。
  2. 在 references/design-writing.md 的 design-writing-self-check 和 references/design-quality-rubric.md 的 design-verification-self-review 两个既有 marker 章节中增量改写核心闭环回读，不新增重复自检章节或新的流程节点。
  3. 对每个核心闭环至少回读权限、动作条件、状态结果、规则来源、异常恢复和输出去向。
  4. 已写事实矛盾时在同一次动作内修正；高影响未知按 decision 暴露给用户。
  5. 候选实验未达标时不引用候选脚本；达标时也只把候选作为可选输入。
  6. 修改 skills/spm-design/SKILL.md 时必须保留 context-pack.py 和 context-loading.manifest.json 两个真实装载指针，不得用新 reference 指针替换现有分层装载机制。
- **完成判据**：流程仍为生成 → 写作自检 → 必要确定性检查 → 展示；无独立自检报告、回执或语义退出码。

#### T-5｜改造 Design Review full

- **输入**：spm-design-review/SKILL.md、design-review-checklist.md、review-checklist.md、共享业务闭环规则。
- **动作**：
  1. 第一步只确定当前 Design 范围和业务闭环单元，不读取历史问题结论。
  2. 每个单元携带直接相关的页面、角色、动作、状态、字段、规则、异常和契约。
  3. 跨模块交接作为集成单元审查；不能把一个模块文件自动当作一个单元。
  4. 每个单元先做维度差集：对照关系维度清单，确认本单元是否还使用对象细分类型、属性集、单据类型或其他未纳入核对面的维度；维度缺口与已知维度下的实例缺口分别记录。
  5. 逐项检查权限、动作条件、状态迁移、规则来源、对象细分类型、属性集差异、异常恢复和输出去向。
  6. 每个适用关系输出 pass、red、risk、decision 或带正文依据的 excluded。
  7. 每个 cannot_extract 必须人工处理或保留为 risk，不得静默通过。
  8. 当前问题集冻结后再读取最近 Review，逐编号核对复发和修复声明。
  9. P0/P1 必须完成当前范围；发现 P0 后可停止继续展开低优先级 P2。
  10. 最终只形成一份 design-review-N.md；分单元过程不得产生一组独立 Review 报告或 JSON 回执。
- **最小覆盖摘要**：审查单元、关系类型、候选/实例数、red/risk/decision/pass 数、排除数及依据、cannot_extract 数。
- **完成判据**：所有单元及跨单元关系闭合；已知关系类型的新遗漏实例算覆盖失败；新关系类型算方法缺口；第二轮新增数不作为主通过条件。

#### T-6｜改造 Fix propagation

- **输入**：spm-fix/SKILL.md、fix-propagation-rules.md、共享业务闭环规则。
- **动作**：
  1. 将每个问题改写为业务约束。
  2. 先做约束类别差集：把问题归入约束类别（角色与可见性、状态与迁移、动作与前置条件、数据范围、规则与来源、异常与恢复、结果与去向等），对照共享规则的关系维度清单，确认是否有整类约束从未进入过核对；类别缺口与同类下的实例缺口分别记录。依据：第 12 轮自证 fix-11 的枚举表只列 3 个约束、漏掉“角色维度可见性约束”整类，其 4 个 P1 中 2 个属从未列入核对面的类型。
  3. 建立“业务约束 × 承载面 × 对象（含细分类型）”三维影响表，覆盖角色、状态、动作、数据范围和业务类型。
  4. 检查系统规则、跨模块契约、页面、字段、操作、状态机、导出、验收和未决事项等适用承载面，并检查整页、整列属性或整组字段是否缺失。
  5. 搜索字面变体、统称下的细分类型、同类型对象和兄弟页面，但只修改确认受影响的位置。
  6. 修改后逐位置回读，并检查新句与旧规则的冲突。
  7. 在后续 Review 中逐问题输出“上一轮宣称修改位置 ↔ 当前正文实际内容”。
- **完成判据**：约束类别差集与三维影响面逐项回读；Fix 仍定点修改；没有把影响检查变成批量重写；多承载面问题的隔离副本验证无漏改。

#### T-7｜修复失真测试

- **输入**：test-phase7-scenarios.py 和本轮直接相关测试。
- **动作**：
  1. 记录规范依据：references/design-state-format.md 规定终态也有自有行，触发动作和下一状态写“—”；因此当前 F2 中“待审核”有自有占位行，按规范就是终态，不构成死状态。
  2. 直接把 F2 夹具改为可确定形态：待审核只作为其他状态的目标态出现，状态机表中没有待审核自己的行。断言 stage-prep 输出该状态 is_terminal=false、transitions=0，并由 has_dead_state 检出。
  3. 同时保留反例断言：有自有行且触发动作/下一状态均为“—”时必须判为终态，不得误报。只有上述 B 形态在当前实现中也无法确定时，才停止并记录，不得直接删除 F2 场景。
  4. F3 至 F6 对应真实确定性行为时，执行真实代码并断言结果；没有可执行对象时删除虚假 PASS。
  5. 保留 F1 的真实断言；把 F7 准确描述为规范文档措辞断言，不把它写成模型行为验证。
  6. 不为保持测试数量新增模拟回执。
- **完成判据**：F2 使用“仅作目标态、无自有行”的夹具并真实检出非终态无出路；有“—”自有行的终态不误报；F3-F6 不再无断言写 PASS；保留场景能在故意破坏目标行为时变红，修复后变绿。
- **不能据此宣布的结论**：不能说明模型语义行为有效。

#### T-8｜Design A/B 与 Fix 验证

- **A 组隔离的硬约束**：本机 `~/.workbuddy/skills/spm-design` 是指向 D:/work/ShitPM/skills/spm-design 的 junction（`readlink -f C:/Users/guduj/.workbuddy/shitpm` 为 `/d/work/ShitPM`），活动工作区本身就是 Skill 与 reference 的装载源。git worktree 只隔离 scripts/，不隔离 Skill 与 reference 文本；若用 detached worktree 跑 A 组，子代理读到的 SKILL.md 和 references 仍是 B 组已改版本，A≡B，结论无效。因此 A 组不得用 worktree 并行，必须串行。
- **Design A/B 执行通道**：
  1. T-0 记录 baseline commit。
  2. A 组串行执行，按显式路径回退，不使用裸 `git stash`：先记录 T-3 至 T-6 实际改动的文件清单，再对其中已跟踪文件执行 `git stash push -- <逐个路径>`，并把新增的未跟踪文件（如 references/design-business-closure.md）移到临时目录；确认这些规范层文件的文本回到 baseline 后连续运行 A×3，然后 `git stash pop` 并移回新文件，再运行 B×3。T-1、T-2 和 T-7 的实现层改动在两组中同样生效，属共同基线，不得回退；A/B 的唯一差异必须是 Design fast、Review、Fix 的规范层文本。必须避开 D:/work/ShitPM/references/prd-writing-rules.md 等用户已有未提交修改，不得让它们进入 stash。全程不 commit、不 push。
  3. 为同一项目输入创建 6 份隔离副本，A/B 各 3 份，输出目录不得共享。
  4. A/B 各启动 3 个独立子代理；必须使用同一便宜模型、同一输入、相同工具权限和相同任务文本。
  5. 每次运行记录模型标识、开始/结束时间、输入路径、输出路径、工具错误和是否完成；同时记录本次装载证据并断言 A 组与 B 组不相等。装载证据的取法：对 `skills/spm-design/SKILL.md`、`skills/spm-design-review/SKILL.md`、`skills/spm-fix/SKILL.md`，以及 `contracts/context-loading.manifest.json` 中 design 各 pack 的 sections 所解析到的 references 文件，逐个记录绝对路径与 sha256（同一文件按路径去重），不得只对目录取哈希。哈希完全相等即判定通道失效，不得据此比较质量。
  6. Review 执行者不得读取另一组问题答案。
  7. 结束后删除隔离副本，恢复工作区到 B 组状态；原始结果先汇总到执行报告。
- **stash 不可用或无法回到 baseline 文本时**：改用整目录副本——把 baseline 的 skills/ 与 references/ 复制到临时目录，让 A 组子代理只加载该副本，B 组加载当前工作区；仍无法隔离时把产物层标记为部分完成，不得用同源 A/B 冒充对照。
- **无法建立通道时**：若宿主无法固定同一模型或创建独立运行，不得临时手写 eval harness 冒充模型生成；直接把产物层标记为部分完成。
- **Design 通过要求**：
  - 对照前提：A/B 两组实际装载的 SKILL.md 与 references 哈希不相等；相等时本组结论作废。
  - B 组 P0/P1 中位数低于 A 组。
  - 至少 2/3 的配对运行中，B 组高影响业务缺陷少于 A 组。
  - B 组没有增加未授权高影响产品事实。
  - B 组墙钟耗时中位数不超过 A 组 1.25 倍。
- **Fix 验证**：在正式 Design 隔离副本中处理至少 3 个历史多承载面问题，独立 Review 检查宣称与正文、承载面和新冲突。
- **失败处理**：质量无提升则回到 T-3/T-4；耗时超限且候选输入是主因时，Design fast 移除候选输入但保留核心闭环自检。

#### T-9｜held-out 与最终报告

- **held-out 方式**：
  - 优先：由未参与方法设计的独立准备方，在复杂 Design 隔离副本中植入 8 至 12 个隐藏缺陷，覆盖权限、流程、状态、规则和异常；Review 执行者不可读取答案。
  - 备选：选择一个未参与方法形成的复杂真实项目，先由独立审查形成裁定基线，再执行新方法对照。
- **通过要求**：
  - 所有隐藏 P0 被发现。
  - 隐藏 P1 检出率不低于 80%。
  - 未命中的问题必须归因为具体覆盖缺口，不能以“模型随机性”概括。
  - 覆盖摘要与实际问题记录一致。
- **最终报告必须记录**：实际修改文件、候选工具保留或删除结论、全部测试命令与结果、A/B 原始次数和耗时、held-out 结果、Fix 结果、未完成项、临时文件清理、git status。

### 7.2 每项改动卡

> 本节 F-1 至 F-7 是本计划的改动编号，与四份复审报告中的 F-1 至 F-5 不是同一编号空间。正文引用 F-n 时默认指本节编号。

#### F-1｜共享业务闭环规则

- **表象**：三个阶段都写“检查业务闭环”，但没有统一的关系实例、适用、排除和完成定义。
- **根因**：RC-1、RC-2、RC-5。
- **修复层**：规范层。
- **修改内容**：新增 design-business-closure.md，关系维度必须包含对象细分类型和属性集差集，并由 Design、Review、Fix 引用。
- **不修改哪一层**：不实现业务裁判程序，不修改真实项目事实。
- **最终产物证据**：n≥3 A/B、held-out Review、Fix 隔离验证。
- **仅有哪种证据时仍不能宣布完成**：reference 存在或包含关键词。

#### F-2｜Design fast 自检

- **表象**：生成后仍留下权限、流程、状态和规则断点。
- **根因**：RC-1。
- **修复层**：规范层。
- **修改内容**：增量改写现有写作自检，逐核心闭环回读六类高影响关系。
- **不修改哪一层**：不新增第二检查任务、报告、回执或语义门禁。
- **最终产物证据**：T-8 Design A/B。
- **仅有哪种证据时仍不能宣布完成**：Skill 文本修改或静态检查通过。

#### F-3｜Review 分单元与覆盖闭合

- **表象**：完整 Review 多轮换角度仍不收敛。
- **根因**：RC-1、RC-2、RC-3。
- **修复层**：规范层。
- **修改内容**：业务闭环单元、当前优先、历史后读、逐实例结论、跨单元合并、覆盖摘要。
- **不修改哪一层**：Review 不修改、不确认、不推进 Design。
- **最终产物证据**：T-9 held-out Review。
- **仅有哪种证据时仍不能宣布完成**：覆盖表存在或第二轮无新增。

#### F-4｜Fix 语义影响闭环

- **表象**：修复声明与正文不一致，同一约束漏改其他承载面。
- **根因**：RC-5。
- **修复层**：规范层。
- **修改内容**：约束化；先做约束类别差集（含“整类约束从未进入核对面”的缺口）；按“约束 × 承载面 × 对象（含细分类型）”三维枚举；检查整页/整列属性缺失；逐位置回读和宣称与实际对照。
- **不修改哪一层**：不整篇重写，不自动创建不存在的下游。
- **最终产物证据**：至少 3 个隔离副本多承载面问题无漏改。
- **仅有哪种证据时仍不能宣布完成**：搜索命中或 diff 生成。

#### F-5｜Index 关键实体完整性

- **表象**：真实 Design 有页面，Index pages=0 且仍被消费者启用。
- **根因**：RC-6。
- **修复层**：实现层。
- **修改内容**：多级编号归一化；页面清单与详情配对的独立比对键（剥尾括注，保留页面编号前缀，不改 _normalize_label 全局返回）；结构式 page_extraction_empty；unsupported_format 优先降级；两个消费者 fatal；保持 CLI no_entities_extracted diagnostics 独立；直接回归测试。
- **不修改哪一层**：不改变页面业务事实和 Design canonical 写法。
- **最终产物证据**：隔离副本 pages=4、errors 50→31→27，页面配对错误归零，关键空集测试失败，标准格式回归通过。
- **仅有哪种证据时仍不能宣布完成**：compile exit 0。

#### F-6｜候选枚举器

- **表象**：纯人工可能漏找分散对象，固定业务轴脚本又持续漂移。
- **根因**：RC-4。
- **修复层**：实现/证据层。
- **修改内容**：仅在 T-2 达标后保留实体、位置、引用和 cannot_extract 提取器。
- **不修改哪一层**：不判断业务语义，不生成 pass/red/risk/decision，不设置生成或 Review 门禁。
- **最终产物证据**：“当前仍可复现 P1 子集”的覆盖率和误报率；不可复现项数；A/B 耗时。
- **仅有哪种证据时仍不能宣布完成**：候选数量或示例命中。

#### F-7｜真实验证

- **表象**：测试 PASS 与真实语义质量脱节。
- **根因**：RC-7。
- **修复层**：验证/产物层。
- **修改内容**：真实断言、n≥3 A/B、held-out、Fix 独立 Review。
- **不修改哪一层**：不为了测试方便修改产品事实或降低规则。
- **最终产物证据**：执行报告原始结果。
- **仅有哪种证据时仍不能宣布完成**：单次成功、同源缺陷集或常量 PASS。

## 8. 失败/停止条件

| 触发条件 | 说明 | 处理动作 | 是否允许继续 |
|---|---|---|---|
| blocks+fields+operations>0 且 pages=0，但未产生 page_extraction_empty | 结构式关键空集未识别 | 停止候选实验，回到 T-1 | 否 |
| unsupported_format 旧项目被 page_extraction_empty 打成硬失败 | 破坏既有 legacy 降级 | 回退新 fatal 顺序或判据，补旧格式回归 | 否 |
| 候选对“当前仍可复现 P1 子集”覆盖率低于 60%，或错误候选达到真实命中的 2 倍 | 不满足工具准入 | 删除实验代码，使用 instruction-only 方案。分母含不可复现标的时不算失败，须先按 T-2 重算分母 | 可按降级方案继续 |
| 页面比对键剥括注后，同名不同括注的两个真实页面被静默合并 | 归一化越权，掩盖缺页 | 保留页面编号前缀作第一比对键；无编号可判别时记 risk 交人工确认 | 否 |
| candidate 被当作业务缺陷、通过结论或门禁 | 程序越权裁决语义 | 删除该逻辑并重新验证 | 否 |
| Design fast 形成独立任务、报告或回执 | 违反已确认的生成成本边界 | 合并回现有写作动作 | 否 |
| Design fast 耗时中位数超过基线 1.25 倍 | 超出 D-6 已确认的成本边界 | 先移除候选输入并复测；仍超限则保留证据并询问用户，不得自行放宽阈值 | 否，须询问用户 |
| Review 按模块文件机械切分 | 当前单模块文件已达 94689 字节（2026-09-15 18:45 快照），执行时以 T-0 冻结值为准 | 改按生命周期/端到端闭环切分 | 否 |
| Review 在当前问题集冻结前读取历史问题结论 | 独立性失效 | 清空本次结论并重新执行 | 否 |
| 排除项没有正文依据 | 排除成为漏检后门 | 改记 risk 或 decision | 否 |
| P0 出现后仍大量展开 P2，影响 P0/P1 覆盖 | 优先级错误 | 停止 P2，完成当前范围 P0/P1 | 是 |
| Fix 因回扫同类实例而批量修改无关内容 | 范围扩大 | 回退无依据修改，只保留受影响位置 | 否 |
| F2 未使用“仅作目标态、无自有行”的确定夹具，或误把有“—”自有行的终态当死状态；F3-F6 仍无断言写 PASS | 验证失真 | 按 T-7 修正夹具和断言 | 否 |
| 无法获得同一模型、同一输入的 A/B | 无法证明生成效果 | 标记产物层未完成，不得用手写样本代替 | 可完成规范和实现，但总状态只能部分完成 |
| A 组与 B 组实际装载的 SKILL.md/references 哈希相等 | 装载源就是活动工作区，隔离失效，A≡B | 停止比较；改用串行 stash 或只读目录副本重跑；仍无法隔离则标产物层部分完成 | 否 |
| held-out 与方法设计使用同一批问题答案 | 验证同源 | 更换独立样本 | 否 |
| 出现新的高影响产品事实或架构分支 | 超出已确认结论 | 保留证据并询问用户 | 否 |
| 仅静态测试通过，真实产物未验证 | 证据不足 | 标记部分完成 | 否 |

## 9. 最终验收

### 9.1 规范是否正确

- **权威文件**：design-business-closure.md 及三个 Skill 的指针。
- **规则一致性证据**：fast、full、fix 共用关系实例、对象细分类型、属性集差集、适用、排除、risk、decision 和承载面定义。
- **冲突表述检查**：
  - Design 自检仍在一次写作动作内。
  - Review 仍只审查，不修改、不确认、不推进。
  - Review 完成 P0/P1，发现 P0 后可停低优先级 P2。
  - Fix 仍定点修改，不整篇重写。
- **高影响未决事项**：继续由用户决定。
- **结论**：执行后填写通过、部分通过或未通过。

### 9.2 实现是否正确

- **修改文件**：执行报告列出实际文件，不能用计划范围代替实际范围。
- **确定性行为证据**：多级编号提取、结构式 page_extraction_empty、unsupported_format 保持降级、PRD/Prototype 两个消费者拒绝关键空集、F2 确定夹具真实断言。
- **消费者/回归证据**：design-index.py 是公共依赖，只跑单点脚本不足以支撑“既有测试无新增失败”的判据。必须同时跑全量和直跑两个入口并记录结果：
  - 全量：`C:/Python314/python.exe -m pytest -q`（2026-09-16 基线为 77 passed，约 42s；托管 Python 3.13.12 无 pytest，必须用 `C:/Python314/python.exe`）。
  - 直跑：`scripts/python/test-*.py` 共 14 个脚本逐个执行（真值口径，会打印 PASS/OK 摘要）。
  - 重点单点：test-design-index.py、test-prd-consistency-semantics.py、test-prototype-consistency-check.py、test-phase7-scenarios.py、test-context-loading.py、test-resource-integrity.py，以及新增候选脚本的直接测试（仅当保留）。
- **基线失败与本轮失败**：区分修改前已存在失败和本轮新增失败；不得修无关基线问题。
- **结论**：执行后填写通过、部分通过或未通过。

### 9.3 产物是否有效

- **目标产物**：A/B Design、held-out Review、Fix 隔离副本和执行报告。
- **事实对照证据**：P0/P1 数量、缺陷类别、未授权事实、耗时中位数、候选覆盖与误报、held-out 检出结果、Fix 宣称与正文。
- **真实场景证据**：同模型同输入 n≥3，独立 Review，held-out 盲审。
- **用户可见结果**：Design 生成仍快；Review 能说明覆盖范围；Fix 不再只改被点名句子。
- **仍未验证的内容**：必须逐项列出，不能概括成“后续优化”。
- **结论**：执行后填写通过、部分通过或未通过。

### 9.4 总结结论

- **规范层**：执行后填写。
- **实现层**：执行后填写。
- **产物层**：执行后填写。
- **本轮总状态**：三层全部通过才可写已完成；任一产物验证缺失只能写部分完成。
- **不得省略的负面结论**：
  - 候选实验未达标时，明确写“候选脚本未进入主流程”。
  - 无同模型同输入 A/B 时，明确写“Design 生成效果未证明”。
  - held-out 未通过时，明确写“Review 通用性未证明”。
  - 不承诺未来所有未知业务关系绝对一次穷尽。

## 10. 不在本计划中的问题

| ID | 问题 | 发现证据 | 为什么不纳入本轮 | 后续建议 | 是否需要用户决策 |
|---|---|---|---|---|---|
| O-1 | 继续扩展设备租赁 design-surface-audit.py 的固定业务轴 | 第 11 至第 13 轮脚本和人工结果 | 已证明会随历史问题膨胀，不能形成通用语义判断 | 保留为项目取证资产，不进入 ShitPM 主流程 | 否 |
| O-2 | 给 Design 正文加入机器锚点 | 审计报告建议的备选方案 | 全量锚点会污染人读正文，最小写作期锚点也存在整篇重写时静默丢失和维护漂移风险 | 只有候选实验失败且定位成本仍不可接受时另立计划，对比“不加锚点 / 仅高影响约束最小锚点 / 接受人工定位”三种方案 | 是 |
| O-3 | 修复设备租赁第 13 轮业务问题 | design-review-13.md | 本轮维护 ShitPM 方法，不修改真实项目事实 | 另行触发 spm-fix | 是 |
| O-4 | 优化 PRD 和 Prototype 的语义审查 | 当前事实链范围 | 应先证明 Design 源头方案有效 | 本轮通过后另立计划 | 是 |
| O-5 | 清理或修改 prd-writing-rules.md | 当前 git status 显示已有用户修改 | 与本轮无关，且不得覆盖用户工作 | 保持不动 | 否 |
