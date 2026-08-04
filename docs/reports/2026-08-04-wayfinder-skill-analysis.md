# Wayfinder Skill 解析与 ShitPM 补强分析

> 日期：2026-08-04
> 来源：https://github.com/mattpocock/skills/tree/main/skills/engineering/wayfinder
> 配套研读：grill-with-docs / research / domain-modeling / 仓库 18 个 skill 生态定位

## 1. Wayfinder 是什么（30 秒版）

**Wayfinder = 决策地图工作流。** 当一个工作量超过单次 AI 会话容量、且路线还没看清时，它不让你硬着头皮一次做完，而是：

1. 先**给目的地命名**（Destination）——终点是一份 spec、一个决策还是一次改动；
2. 画一张**决策地图**（Map，一个 issue）——上面只记索引：已决策清单、迷雾区、范围外；
3. 把每个待决策问题拆成一张**门票**（Ticket）——门票大小 = 恰好一次 100K token 会话能解决；
4. **一次会话只解决一张门票**，解决后记录、关闭、让新迷雾"毕业"成新门票，循环直到路线清晰。

核心哲学三句话：

- **Plan, don't do**——规划是默认动作，地图走完（路线清晰）即交付，执行是另一回事。
- **决策只存在一处**——地图是索引不是仓库，答案写在自己的门票里，地图只摘要+链接。
- **refer by name**——人类可读的叙述永远用门票标题引用，不甩 `#42` 这种裸编号。

## 2. 核心机制拆解

### 2.1 地图结构（Map）

```markdown
## Destination        # 终点，一两行，每次会话先看它
## Notes             # 领域、该 consult 的 skill、本 effort 的偏好
## Decisions so far  # 索引：每行 = 已关闭门票名 + 链接 + 一句话答案
## Not yet specified # 迷雾：看不清、还不能开票的决策（推进后毕业）
## Out of scope      # 范围外：永久排除，永不毕业
```

地图是**低分辨率**视图，一次会话只加载地图本身，门票详情按需 zoom。

### 2.2 门票类型（Ticket Types）

| 类型 | HITL/AFK | 用途 | 解决方式 |
|------|----------|------|----------|
| Research | AFK | 查文档/API/知识库，决策依赖的事实 | `/research` 子代理，可并行 |
| Prototype | HITL | "长什么样/怎么表现"是核心问题 | 廉价原型给人看 |
| Grilling | HITL | 默认类型，逐问访谈直到决策树收拢 | 真人对话 |
| Task | HITL/AFK | 决策前必须做完的体力活（签约、开通、搬数据） | 自己做或给人清单 |

**HITL 铁律：HITL 门票只能通过真人对话解决，agent 永远不能替人类一侧作答**——"一个自己回答自己问题的 grilling agent 已经破坏了规矩"。

### 2.3 前线（Frontier）

前线 = 打开 + 未被阻塞 + 未被认领的门票。阻塞用 issue tracker 原生依赖关系表达，这样前线在 tracker UI 里**可视化**，人不用开地图就知道现在能取哪张。

### 2.4 迷雾判据（Fog or ticket?）

> **Fog or ticket? The test is whether you can state the question precisely now — not whether you can answer it now.**

- 问题现在能精确陈述 → 开票（哪怕被阻塞暂时做不了）
- 不能精确陈述 → 记入 Not yet specified（迷雾）

### 2.5 工作纪律

- 一次会话最多解决一张门票（research 例外，可并行）
- 工作前先**认领**门票（assign 给自己），防并发冲突
- 解决后：发 resolution 评论 → 关票 → 追加地图 Decisions so far → 让新迷雾毕业 → 越界票关闭移入 Out of scope
- Out of scope 永不毕业，只有目的地重画才可能回来（且算新 effort）

### 2.6 与配套 skill 的关系

- **grill-with-docs / grilling**：盘问式访谈，直到决策树每个分支都解决；顺带写 CONTEXT.md 术语表和 ADR
- **domain-modeling**：术语表 + ADR 三条件（难逆转 / 无上下文会惊讶 / 真权衡）才写 ADR
- **research**：后台子代理查一手来源，写成带引用的 Markdown 文件
- **to-tickets / to-spec / triage / implement**：对话→spec→tickets→执行闭环

## 3. ShitPM 现状对照

| 维度 | ShitPM 现状 | Wayfinder 提供 |
|------|------------|----------------|
| 超大工作处理 | R14 起 PRD 分片落盘；design 编排器 30 节点单会话硬跑 | 决策级分片：一次会话只推进一个决策 |
| 确认门禁 | design-confirmation 仅哈希戳，不查编排器接受/综合审查（R13 双门方案零落地） | **HITL 铁律：确认=真人表态，AI 不代答** |
| 高影响未知 | 规则要求"必须问用户"，但缺"何时问/何时记迷雾"判据 | 迷雾判据：能否精确陈述问题 |
| 上下文治理 | 材料只进子代理、回执≤200 字、主代理重读文件 | 地图低分辨率 + 按需 zoom，同思路的编排层版 |
| 范围控制 | 范围边界分析在 references，无"永不复活"纪律 | Out of scope 显式记录、永不毕业 |
| 命名引用 | 产物以文件名/id 引用 | refer by name，人读起来舒服 |

## 4. 可补强清单（按价值排序）

### P0-1：确认门禁补 HITL 语义（直接修 R13 根因）

**Wayfinder 原话**："A HITL ticket only resolves through that live exchange; the agent never stands in for the human's side of it."

**ShitPM 对应问题**（2026-07-30 根因报告）：design-confirmation.py 只记 SHA-256+时间，check 只比哈希 → 等于 AI 认为"确认过"就是确认过，**AI 替用户确认了**。

**补强**：
- 确认记录必须含**用户表态的证据**（用户原话/明确动作），不是哈希戳
- spm-design 发"请确认"前必须过编排器接受（这是 AI 自校验，属 AFK，只做前置）
- 下游（spm-prd/prototype）"已确认"判据 = 人类确认 AND 编排器接受（双门，呼应 2026-07-30 执行方案三任务）

**落地成本**：低。改 design-confirmation schema + SKILL 措辞，不新增工具。

### P0-2：未知项引入迷雾判据

**补强**：把"高影响未知必须问用户"升级为两条：
1. 能精确陈述 → 立即问（HITL，一次一个，不攒一大坨）
2. 不能精确陈述 → 写入 design 的"Not yet specified"区，设计推进后回看毕业

**落地成本**：低。SKILL 措辞 + design 模板加一节。

### P1-3：决策级分片（工作流探索，面扩大）

**现状**：PRD 已分片落盘（R14），但 design 阶段仍是一次编排器跑完约 30 节点。

**探索方向**：大项目 design 也可以"地图化"——先列决策清单（Destination + 已决策 + 迷雾 + 范围外），按依赖排序，一次会话推进一个决策块，每块落盘后更新清单。这与现有"主对话瘦身"治理目标完全同向，且把编排粒度从"节点"提到"决策"。

**注意**：这是探索，不是立即实施。小项目不该地图化（Wayfinder 自己也说"如果没探到迷雾，就别开地图"）。

### P1-4：范围边界加"永不复活"纪律

**补强**：align/design 的范围外结论显式记录 + 后续阶段不自动复活；范围变更需"目的地重画"级别的动作。

**落地成本**：低。规则措辞即可。

### P2-5：refer by name 惯例

**补强**：SKILL 与回执里引用产物用标题名（Design 基线名、PRD 章节名），不甩裸 id。小改善人读体验。

### P2-6：research 门票化（可选）

ShitPM 已有 subagent 契约 4 角色；可借鉴"research 结论带引用来源"惯例（查一手来源，写带引用的 md）。低优先。

## 5. 明确不建议照搬的部分

1. **issue tracker 集成**（GitHub/Linear）：ShitPM 是本地文件制品，引入外部 tracker 是过度设计。地图/门票用本地 markdown 即可。
2. **Blocking 依赖图可视化**：编排器已有 30 节点依赖图，不必再学 tracker 的可视化。
3. **认领（claim）机制**：ShitPM 单用户无并发，不需要 assign 防冲突。
4. **门票类型全表**：Research/Grilling/Task 三型够用，Prototype 型与现有原型阶段重叠。
5. **"每 session 一张票"的执行节拍**：那是跨会话工作流的产品形态，ShitPM 是单会话 skill 编排，粒度应停在"决策块"而非"门票"。

## 6. 一句话总结

> **Wayfinder 对 ShitPM 的最大价值不是任何脚本或机制，而是一条纪律和一条判据：HITL 确认必须真人表态（修 R13 根因），迷雾判据决定何时问用户。** 其余都是这两条在工作流上的延伸。
