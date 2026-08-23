# R17 对抗性审查报告：PRD 写法迭代（PRD Skill 最终优化 + 跨层缺陷优化）合并审计

> 日期：2026-08-04
> 审查对象：工作区全部未提交迭代（19 个改动文件），即两份方案的叠加落地：
> 1. `docs/plans/2026-08-04-prd-skill-final-optimization-and-acceptance.md`（PRD Skill 最终优化，R16 已审）
> 2. `docs/plans/2026-08-04-skill-defect-cross-layer-optimization-execution-and-acceptance.md`（Skill 缺陷跨层优化 12 项，**R16 之后落地，未审计**）
> 基线：b9a4a0e
> 方法：12 项缺陷逐项落点核对 + R16 结论复核 + 全量测试 + 上下文装载实证 + 文档结构对抗检查

## 1. 结论

**0 P0 / 1 P1 / 6 P2。** 两份方案的核心内容均真实落地：12 项缺陷在 Design 链与 PRD 链都有对应规则落点，12/12 测试全绿，模块上下文装载命令可跑，R16 的 P2-1（spm-fix 缺格式引用）已被后续改动修复。

**唯一 P1：`references/design-state-format.md` 章节结构被新内容插坏**——新章节"页面状态与状态驱动展示"插在"## 闭环要求"标题与其正文之间，导致闭环要求的正文和结构层/业务层 8 条状态机规则（4 结构 + 4 业务）全部错误归属到新章节名下。讽刺的是，本轮迭代自己在方案 §2.1 里把"Markdown 结构损坏"列为必须消灭的缺陷，却在这份被 `design-card-state` 上下文装载直接引用的规则文件里制造了同类损坏。

**跨层优化方案的验收未执行**：方案 §4 阶段 4/5 要求简单项目样本 + 审计系统副本回归（A-01~A-12），当前仓库没有任何执行报告或验证产物。文件改了，验收没做。

## 2. 审查范围

| 范围 | 说明 |
|---|---|
| Design 链 | spm-design、spm-design-review、spm-fix、design-analysis-protocol、design-fact-format、design-state-format、design-writing、templates/design.md、design-review-checklist、test-design-simplification |
| PRD 链 | spm-prd、spm-prd-review、prd-writing-rules、prd-scene-checklist、prd-review-checklist、prd-writing-examples、templates/prd.md、test-prd-simplification、test-prd-style-lint |
| 未审计部分 | 跨层优化落地（R16 之后新增的 Design 链 + PRD 链扩展内容） |

## 3. 跨层优化 12 项缺陷落点核对（方案 §2/§4 逐项）

| # | 缺陷 | Design 链落点 | PRD 链落点 | 判定 |
|---|---|---|---|---|
| 1 | 页面展示事实承接（无权限/加载/空态/异常/超长/默认值/标签色值） | spm-design §5.1、输出要求、自检；design-writing 页面属性与常见错误表；templates/design.md 页面属性 + 展示行为/状态驱动展示项 | spm-prd A-1、模块输入、完成条件 11、自检 14；templates/prd.md 展示行为段；rules §3.2 | ✅ |
| 2 | 横切能力识别（待办/提醒/编号/字典/文件/归档） | spm-design §5.1 十项清单；design-writing 横切章节 | spm-prd A-1 扩展、完成条件 12 | ✅ |
| 3 | 分页/导出/批量/首页/文件限制分开 | spm-design §5.1 末项 | spm-prd 完成条件 12、自检 16；rules §8.1 | ✅ |
| 4 | 产品事实冲突/结构适配/人工语义分开 | — | prd-consistency-check.py 已有三类输出（确定性冲突/可能遗漏/needs_semantic_judgment）；spm-prd-review 职责边界三类 | ⚠️ 部分：检查器覆盖"结构适配差异"（state_via_enum 等），但契约/SKILL 未显式命名该类别 |
| 5 | 审计侧/被审侧入口统一表达 | spm-design §5.1；design-writing | spm-prd A-1、自检；spm-prd-review 检查项 | ✅ |
| 6 | 页面展示行为写作位置 | design-state-format 新章节（**结构插坏，见 P1-1**） | templates/prd.md 页面展示行为段；rules §3.2/3.3 | ⚠️ 落点存在但文件结构损坏 |
| 7 | 完成条件可回读到 PRD 落点 | — | spm-prd 完成条件 11/12（"能定位""能回读"） | ✅ |
| 8 | 页面区块与布局业务目的 | design-writing 页面属性；templates/design.md 区块 | rules §3.2（区块及区块业务目的）；spm-prd-review 检查项 | ✅ |
| 9 | 自动动作失败闭环 | spm-design §5.1/自检；design-writing 横切章节；design-analysis-protocol 新检查项 | spm-prd 完成条件 12、自检 15；rules §8.1；prd-review-checklist 25.1 | ✅ |
| 10 | 枚举三选一 | spm-design §5.1 | spm-prd 完成条件 12；rules §8.1；prd-review-checklist 25.3 | ✅ |
| 11 | 删除传播 | spm-design §5.1/自检；design-writing 横切章节 | spm-prd 完成条件 12、自检 15；rules §8.1；prd-review-checklist 25.2 | ✅ |
| 12 | 状态驱动展示 | design-state-format 新章节（**结构插坏**）；design-writing | spm-prd 模块输入、完成条件 11；rules §3.3；prd-review-checklist 18.2 | ⚠️ 落点存在但文件结构损坏 |

12 项中 10 项完整落地，问题 4 部分落地，问题 6/12 落点存在但所在文件结构损坏。

## 4. R16 结论复核（当前状态）

| R16 结论 | 当前状态 | 判定 |
|---|---|---|
| 四约束写入 spm-prd 本体 | 仍在，且叠加了跨层优化扩展 | ✅ |
| 页面 `######` / 动作 `**` 格式统一 | 模板/规则/SKILL/示例一致，test 断言钉死 | ✅ |
| `--card scenes` 真实装载 | 实测 dry-run 443 行 / 6454 tokens，含 prd-scene-checklist 6 个新章节 | ✅ |
| 7+ 测试全绿 | 12/12 全绿（含新增 test_cross_layer_contracts_are_synced） | ✅ |
| P2-1 spm-fix 缺格式引用 | **已修复**：spm-fix 补格式规则引用，且"只应用到被触达的页面或动作，不整篇迁移存量格式" | ✅ |
| P2-2 无确定性兜底 | 仍成立（设计取舍，方案明确禁止新增检查器） | 延续 |
| P2-3 新旧格式并存 | 仍成立，spm-fix 的"不整篇迁移"措辞使并存成为显式策略 | 延续 |
| P2-4 两层治理未执行 | **仍未执行**：10 个 SKILL 中"完成判据："命中 0 处，否定句数量未减 | 延续 |
| P2-5 80% 目标无依据 | 计划层未执行 | 延续 |

## 5. 对抗性实证

### 5.1 全量测试（12/12 绿）

test-prd-simplification / test-prd-style-lint / test-prd-consistency-semantics / test-design-simplification（含新增 cross_layer_contracts 断言）/ test-design-index / test-shitpm-regression / test-context-loading / test-anti-hallucination / test-design-orchestrator / test-design-orchestration-replay / test-context-runtime / test-resource-integrity 全部通过。

### 5.2 上下文装载实证

- `context-pack.py --pass module --card scenes` dry-run 可跑：4 个来源文件、6 个 section、443 行、6454 tokens，含 `prd-verification-scenes`；
- `design-card-state` 在 manifest `design-cards` 包内（L72），装载范围为 design-state-format.md L39-102，新章节内容会被装载；
- 跨层优化的 rules 均落在既有 context 标记内（design-card-cross-layer、design-card-state、prd-verification-scenes、prd-writing-structure 等），无需改 manifest。

### 5.3 文档结构对抗检查（本轮主要发现）

**P1-1：design-state-format.md 章节归属错乱。**

```
L40  ## 闭环要求          ← 空标题
L42  ## 页面状态与状态驱动展示  ← 新章节插在中间
L44-57  页面展示规则正文
L59  状态机必须形成完整闭环…违反任一条即判 P1  ← 原"闭环要求"正文被挤到新章节下
L61+ ### 结构层（可机读）…  ### 业务层（人审）  ← 状态机 8 条规则全部归属新章节
```

后果：状态机闭环检查的 4 条结构规则 + 4 条业务规则（状态机检查的核心判据）在文档中全部归入"页面状态与状态驱动展示"名下；"## 闭环要求"成为空壳。该文件被 `design-card-state` 直接装载给模型，标题是模型组织规则语义的锚点，错位会污染模型对"闭环要求（状态机检查标准）"与"页面展示状态（展示行为）"两个概念的边界认知。修复成本极低：把新章节整体移到"### 业务层（人审）"之后。

## 6. 发现的问题

### P1（1 项，阻断合并前必须修）

| # | 问题 | 位置 | 说明 |
|---|---|---|---|
| P1-1 | design-state-format.md 章节结构损坏（**已修复**） | `references/design-state-format.md`（原 L40-61） | "## 页面状态与状态驱动展示"插在"## 闭环要求"标题与正文之间，闭环要求正文和状态机结构层/业务层 8 条规则全部错误归属。与本轮方案 §2.1 自己列为缺陷的"Markdown 结构损坏"同类。**修复（2026-08-04 同日）：新章节整体移至"### 反例"之后、`design-card-state` 结束标记之前；结构层/业务层/反例恢复归属"## 闭环要求"。修复后 test-design-simplification（含 cross_layer_contracts 断言）、test-resource-integrity、`--pass writing --mode full --card state` 装载（707 行/8910 tokens）均通过。** |

### P2（6 项）

| # | 问题 | 位置 | 说明 |
|---|---|---|---|
| P2-1 | 跨层优化验收未执行 | 全仓库无执行报告/验证产物 | 方案 §7 要求 A-01~A-12 验收（简单项目样本 + 审计系统副本回归），§9 要求执行 AI 报告格式，当前只有文件改动，无任何验收证据。12 项缺陷是否在真实项目表现成立，未经样本验证。 |
| P2-2 | 行尾符混合（CRLF/LF） | 10 个文件 | prd-review-checklist（72+34）、prd-writing-rules（120+100）、prd-writing-examples（96+50）、design-analysis-protocol（142+9）、spm-prd-review（56+14）、templates/prd.md（109+16）、test-design-simplification（145+32）、test-prd-style-lint（104+12）、design-fact-format（1+67）、test-prd-simplification（1+145）。git diff 出现大量"内容相同仅行尾不同"的虚假修改行，评审噪音大，Windows 工具链有潜在风险。建议提交前统一 CRLF。 |
| P2-3 | prd-review-checklist 编号体系插入小数 | contracts/prd-review-checklist.md | 在整数编号 18/25 后插入 18.1/18.2/25.1/25.2/25.3，与其他整数编号混排，Review 引用编号易混淆。建议重排为整数或独立字母段。 |
| P2-4 | 问题 4 的"结构适配差异"未显式成类 | spm-prd-review / prd-review-checklist | 检查器内部已覆盖（needs_semantic_judgment 含 state_via_enum、merged_split_unmatched 等），但 SKILL 和契约未命名"结构适配差异"类别，验收 A-05 要求的三类划分在文档层缺一类。 |
| P2-5 | 两层治理方案仍未执行 | 全部 10 个 SKILL | "完成判据："命中 0 处；否定句数量无下降。R16 P2-4 延续。 |
| P2-6 | 模板展示行为段为正文示例而非注释 | templates/prd.md | "页面展示行为和状态驱动展示：按已确认事实说明…"未用 `<!-- -->` 包裹，模型可能照抄指导语进真实 PRD（与"页面职责和使用对象。"占位示例同性质，但更具体、更易被原样保留）。 |

## 7. 观察（非问题）

- spm-fix 的格式规则引用处理谨慎："只应用到被触达的页面或动作，不整篇迁移存量 PRD 格式"，兼顾了新旧并存策略，是对 R16 P2-1 的合格修复。
- test_cross_layer_contracts_are_synced 用字符串断言钉死 6 个文件的关键短语，与 R16 对 test-prd-simplification 的判断一致（"措辞微调即挂，设计可接受"），但后续措辞调整会同步改测试。
- 横切能力/自动动作/删除传播等规则在 SKILL、rules、checklist、review 多处重复出现，是方案要求的"逐层落点"设计（Skill 本体 + 参考规则 + 场景清单 + Review 契约），非冗余缺陷。
- prd-consistency-check.py 本轮未改（R16 已实证页面身份以页面清单表为权威源，新格式无冲击），符合方案 4.2"只有确定性误报被证明后才改脚本"。
- templates/prd.md 的新格式注释（`###### 页面名称` 等）与 rules §5 完全一致。

## 8. 建议（按优先级）

1. **修 P1-1（已完成）**：把 design-state-format.md 的"页面状态与状态驱动展示"章节移到"### 业务层（人审）"之后，恢复"## 闭环要求"标题与正文相邻。已执行并回归通过（见第 6 节）。
2. **补跨层优化验收**：按方案 §7 的 A-01~A-12 至少完成简单项目样本 + 冲突阻断 + 自动动作/删除传播/枚举探针，输出验收报告；审计系统副本回归可作为下一步。
3. **提交前统一行尾符**（P2-2），避免污染 git 历史。
4. 明确两层治理（P2-5）是否要执行——若本轮迭代范围不含它，需与用户对齐预期。
5. 重排 prd-review-checklist 编号（P2-3）、在 spm-prd-review 显式命名"结构适配差异"类别（P2-4），均为低成本一致性修正。

## 9. Git 状态

- 本次审查只读，未修改任何文件（除本报告）；
- 工作区 19 个改动文件 + 5 个未跟踪文档均未提交；
- 未执行 commit / push。
