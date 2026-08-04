# SKILL 两层治理优化执行报告（否定式指令正面化 + 完成判据显式化）

> 日期：2026-08-05
> 执行依据：`docs/plans/2026-08-04-skill-two-layer-governance-plan-and-acceptance.md`（R16 P2-4 / R17 P2-5 遗留，用户 2026-08-05 拍板执行）
> 范围：`skills/` 下全部 10 个 SKILL.md；未改 references/templates/contracts/schemas/scripts/测试；未执行 commit（提交由用户在"改完提交"指令中另行授权，见 Git 状态）

## 一、否定句分类统计（优化一）

| SKILL | 改前 | 改后 | B 类正面化 | A 类保留（已配对） | C 类删除 |
|---|---:|---:|---:|---:|---:|
| spm-prd | 23 | 14 | 7（阶段A导航/三处交叉比较/模块装载/非页面字段落点/输出资产/语义证明/停交付点） | 16（事实边界/阻断规则/禁止全读/索引精简/格式护栏等，均已有正面配对或正文补配对） | 0 |
| spm-align | 12 | 7 | 4（材料主输入/无材料继续/能查不追问/回答写回/Align 前置陈述） | 7（不替用户拍板/完整保留/失败处理等） | 0 |
| spm-design | 8 | 5 | 3（材料原文读取/规则包≠完成/Align 必经） | 5（正文格式护栏/操作表规范/待确认不补造等） | 0 |
| spm-fix | 3 | 0 | 1（下游并列陈述） | 2（Align 不反向定源/下游不提升 Design 事实） | 0 |
| spm-prototype | 2 | 2 | 0 | 2（confirm 前置/语义问题归 Fix） | 0 |
| spm-prototype-mark | 7 | 7 | 0 | 7（零丢失/角标定位/单引号/样式锁定/不成为事实源/跨平台命令/通用工具描述） | 0 |
| spm-prd-review | 5 | 5 | 1（只依赖 Design/PRD） | 4（不修改产物/硬阻塞条件/不伪装通过/不绕过） | 0 |
| spm-design-review | 5 | 5 | 1（只依赖 Design） | 4 | 0 |
| spm-prototype-review | 6 | 6 | 1（只依赖 Design/Prototype） | 5 | 0 |
| spm-start | 2 | 1 | 1（动作矩阵只读引用） | 1（"不可用"为陈述非指令） | 0 |
| **合计** | **73** | **52** | **19** | **54** | **0** |

说明：无 C 类删除（grep 到的否定句均为操作性指令或事实边界，无 no-op 冗余；spm-design 曾有两句近似"规则包≠完成"，分别在 §3 上下文与 §7 自检语境，语义不同，按方案停止条件"拿不准归 A 类"保留）。剩余否定句中 A 类硬护栏占比 54/73 ≈ 74%，接近方案目标 80%（差异来自"只有…才硬阻塞""缺失…时停止"等条件句，属于无法正面化的阻塞语义，已配对正面替代）。

## 二、完成判据覆盖（优化二）

| SKILL | 判据数 | 覆盖步骤 |
|---|---:|---|
| spm-prd | 6 | 阶段 A 全局扫描、阶段 A-1 风险清单、阶段 B 骨架、阶段 D 整合、中断恢复、最终检查；阶段 C 引用既有 12 项模块完成条件（不重复建设） |
| spm-align | 3 | 材料读取、提问+写回、Align 完成 |
| spm-design | 2 | 简单模式、完整模式；通用判据（L114"只有…才能告诉用户请确认"）已为判据形式 |
| spm-fix | 2 | 执行流程 7 步、Confirmation 与输出 |
| spm-prototype | 1 | 生成完成（执行流程第 8 步后） |
| spm-prototype-mark | 1 | 执行与自检（引用既有 12 项自检清单） |
| spm-prd-review | 1 | 审查完成（统一模板） |
| spm-design-review | 1 | 审查完成（统一模板） |
| spm-prototype-review | 1 | 审查完成（统一模板） |
| spm-start | 1 | 扫描输出完整性 |
| **合计** | **19** | 全部可执行步骤覆盖；判据均绑定既有产物/脚本/章节，未引入新动作 |

## 三、典型改写对照（改前 → 改后 → 分类）

1. spm-prd "不得跳过，也不得在未运行时宣布该模块已按全量分片流程完成" → "每个模块必须实际运行该模块上下文装载命令，运行成功后才可宣布该模块完成" → B
2. spm-prd "不要生成额外的 Design→PRD 对照表、覆盖率 JSON、验证回执" → "只写入 `output/prd/prd.md`，同时按既有项目约定维护 `output/prd/decision-notes.md`" → B
3. spm-prd "不要自动执行 PRD Review，不自动推进 Prototype" → "完成后停在 PRD 交付点：PRD Review、Prototype 与 Design 确认由用户显式触发" → B
4. spm-align "不要只把短的 align.md 当作 Design 唯一输入" → "以材料资产的可定位事实为主输入，`align.md` 作索引与汇总，不只是短摘要" → B
5. spm-align "能从材料查到的内容不要追问" → "能从材料查到的内容直接采用，不再追问用户" → B
6. spm-design "不要把规则包存在视为分析已完成" → "规则包装载是分析输入准备，分析是否完成以结论落入 Design 为准" → B
7. spm-design "材料索引可复用，但不能让它绕过 Align" → "材料索引只作为 Align 的输入，Align 责任不可绕过" → B
8. spm-fix "不要求同时存在，也不存在默认的 Design → PRD → Prototype 链路" → "PRD 和 Prototype 是 Design 的两个并列下游，各自独立存在与生成" → B
9. spm-prd-review "不要求 metadata、page-fields.json 或其他 Review 资产存在" → "审查只依赖 Design、PRD 与确认状态，不要求 metadata…存在" → B
10. spm-start "不要在 Skill 中复制" → "不在 Skill 中复制" → B（措辞收紧，避免"不要"触发词）

判据示例：spm-prd 阶段 A "完成判据：导航信息九项全部建立；未要求保留全部页面正文于上下文。"；spm-design 简单模式 "完成判据：来源事实逐项落入 Design；目标-能力-场景-流程-页面-动作-字段-状态-权限-规则-异常-验收链路完整；字段表八列齐全逐项；操作表十列角色×状态明确；状态机闭环规则满足；`design.md` 完整可读。"

## 四、语义与一致性自评

- 命令、路径、阶段编号、规则引用与改前完全一致（grep 复核 `$BUNDLE/scripts`、`design-confirmation.py`、`context-pack.py`、`prd-consistency-check.py` 等无变化）；
- 测试断言的关键短语（"禁止一次性全读 design.md"、"sed 1,$p"、"--module <模块名>"、"页面、动作和终端命名格式遵循"、"Design 全读痕迹"等）原样保留，改写句子均为未断言部分；
- 12/12 测试套件重跑全绿（含 test-prd-simplification / test-design-simplification / test-context-loading 对 SKILL 的字符串断言）；
- 无新增否定句；A 类硬护栏均保留且正文已有正面替代（"应…/要…/必须…"）或本轮补配对；
- 无法写出可检查判据的步骤：无（审查类步骤用统一模板，prototype-mark 引用既有自检清单，prd 阶段 C 引用既有 12 项完成条件）；
- 无法正面化的句子：三个 review 的"只有输入文件不存在…才硬阻塞"、prototype-mark 的"禁止 position: absolute / 禁止双引号"（正面表述"一律 fixed / 必须单引号"已配对）、spm-prd 的事实边界"不得补造…"（正面"承接 Design 已明确写出的内容；未定义的高影响行为保留为待确认"已配对）。

## 五、Git 状态

- 本轮两层治理只改 `skills/` 下 10 个 SKILL.md；未执行 commit；
- 用户的"改完提交"指令覆盖本方案"不执行 Git commit"的执行约束，提交与全量工作区改动一起进行（见最终提交说明）。
