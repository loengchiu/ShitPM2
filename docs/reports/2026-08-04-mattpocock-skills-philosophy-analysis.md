# Matt Pocock Skills 仓库设计哲学解析与 ShitPM 借鉴

> 日期：2026-08-04
> 来源：https://github.com/mattpocock/skills （mattpocock/skills，~60k 订阅者的个人 agent skill 仓库）
> 研读素材：仓库 README（四大失败模式）、writing-great-skills 全文、CLAUDE.md、CONTEXT.md 术语表、wayfinder / grilling / to-spec / to-tickets / code-review / handoff / research / domain-modeling / ask-matt、.agents/adr/0001、.out-of-scope/question-limits.md

## 1. 仓库定位（一句话）

> 个人每日使用的工程 agent skills，小而可组合、任何模型可用、刻意对抗"流程拥有者"型框架（GSD/BMAD/Spec-Kit）。根哲学写在元 skill `writing-great-skills` 里：**skill 的存在是为了从随机系统（LLM）里榨出确定性——可预测性（predictability）是根美德。**

## 2. 四大失败模式（README 的驱动逻辑）

仓库里每个 skill 都能追溯到作者在实际使用 agent 时踩过的坑：

1. **Agent 没做我想要的事** → 对齐问题 → `grill-me`/`grill-with-docs`（盘问式访谈）
2. **Agent 太啰嗦** → 共享语言问题 → `domain-modeling`（CONTEXT.md 术语表 + ADR）
3. **代码不工作** → 反馈回路问题 → `tdd`（红-绿-重构）+ `diagnosing-bugs`
4. **代码变成屎山** → 设计问题 → `to-spec` + `improve-codebase-architecture`

**要点：每个 skill 都对应一个真实失败模式，不是"觉得有用就造"。** 这与 ShitPM 的工具准入四项证据同构。

## 3. 设计哲学核心（writing-great-skills 提炼）

### 3.1 根美德：可预测性

> A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same *process* every run, not producing the same output — is the root virtue.

- 追求的是**过程可复现**，不是输出相同
- 所有设计决策（信息层级、leading words、完成判据）都为它服务

### 3.2 四条杠杆

| 杠杆 | 含义 | 对 ShitPM 的对照 |
|------|------|-----------------|
| 信息层级 | 步骤（in-skill step）> 引用（reference）> 外部文件（progressive disclosure），按"agent 多快需要"排序 | ShitPM 已有 context-pack 分章装载，符合此结构 |
| 完成判据 | 每步以"可检查的完成条件"结尾——`can the agent tell done from not-done?`，且要穷尽（"every modified model accounted for"） | ShitPM 的"每节点落盘产物存在性"正是程序化的完成判据 |
| leading words | 用模型预训练里已存在的紧凑概念锚定行为（如 fog of war、tracer bullets、red loop）——一个词顶三句话 | ShitPM 已有"孤岛"“基线”“迷雾"式术语，可更系统化 |
| 裁剪纪律 | 单一事实源；逐句跑 no-op 测试（这句话改变行为吗？不改变就删整句）；激进删 | ShitPM 的"程序只做确定性检查"同向，但 SKILL 层可更狠 |

### 3.3 六种失败模式（写 skill 时的自检清单）

1. **premature completion（提前完工）**——agent 注意力滑向"做完"，步骤没真做完就收尾。防御：先加严完成判据；判据无法收紧且观察到抢跑时，把后续步骤藏到另一个 skill（sequence cut）。
2. **duplication（重复）**——同一含义出现在多处。
3. **sediment（沉淀）**——不敢删旧层，默认命运。
4. **sprawl（蔓延）**——skill 太长。治愈是信息层级：把 reference 披露到外部、按分支/顺序拆分。
5. **no-op（废话行）**——模型默认就服从的指令（"要全面"），付费说空话。测试：删掉它行为变吗？
6. **negation（否定式指令）**——"别想大象"反而让大象更可得。**要正面陈述目标行为**，禁令只留作无法正面表述的硬护栏。

**与 ShitPM 最相关的两条：premature completion（正是"模型自觉遵守流程"假设证伪的机理）和 negation（SKILL 里大量"不要…"可能反向激活）。**

## 4. 工作流哲学（流程类 skill 的共同骨架）

- **grilling**：一次只问一个问题（"同时多问令人困惑"）；每个问题**附推荐答案**；**事实去环境里查，决策才问人**；未达成共识不动手。这是整个仓库最核心的对话纪律。
- **to-spec**：**不访谈**，只合成已讨论内容；spec 模板含 Problem/Solution/User Stories/Implementation/Testing/Out of Scope。
- **to-tickets**：tracer-bullet 垂直切片，每票声明 **blocking edges**；宽重构用 expand–contract 例外；切完**先 quiz 用户**（粒度对吗？依赖边对吗？）再发布。
- **code-review**：**双轴并行子代理**——Standards（代码规范 + Fowler 坏味道基线）和 Spec（是否忠实实现需求）分开跑、分开报告、**不做跨轴排名**——防止一个轴掩盖另一个轴。
- **handoff**：跨会话交接文档，**不重复已有产物**（引用路径），脱敏，存临时目录。
- **wayfinder**：决策门票 + 战争迷雾 + 前线（前一轮已详细分析）。
- **context hygiene**：主流程（grill→spec→tickets）保持在**一个未压缩上下文窗口**；每个 implement 从 ticket 出发开**全新窗口**；超 smart zone（~120k tokens）就 handoff，不硬推。

## 5. 仓库自身的 meta 实践（最值得学的地方）

1. **AGENTS.md 只有 9 字节**：内容就是一行 `CLAUDE.md`——入口文件指向真正的规则文件，不重复内容。
2. **CONTEXT.md 术语表**：三段式——Language（术语 + 避免词）/ Relationships（实体关系）/ Flagged ambiguities（已解决歧义）。这就是 domain-modeling 的输出物，仓库自己用它约束所有 skill 的措辞。
3. **.agents/adr/**：架构决策记录。ADR 0001 把"依赖 setup 配置"的 skill 分成 **hard-dependency**（没配置就错，必须显式提示 run setup）和 **soft-dependency**（没配置只是输出不够锐，用模糊措辞即可）——避免 cargo-cult 地把 setup 指针塞进不需要的地方。
4. **.out-of-scope/** 目录：**显式记录拒绝过的功能**——每份文件写"为什么拒绝"+ 对应真实用户请求（如 issue #44）。这是 wayfinder 的 Out of scope 概念在仓库自身的实践。**"拒绝史"本身就是设计文档。**
5. **ask-matt router**：用户不记得所有 skill，所以有 router 统一编排——主流程（idea→ship）+ 两条 on-ramp + vocabulary 层。CLAUDE.md 规定 router 必须随 skill 增删同步更新，"a router that lies"是明确的反模式。
6. **bucket 组织**：engineering/ productivity/（promoted）vs misc/ personal/ in-progress/ deprecated/（不推广）——**promoted 集合是明确的**，未推广的 skill 不写进 README 和 plugin。
7. **context-loading 纪律**：模型可自动触发的 skill（model-invoked）承担常驻上下文开销，所以 description 要极简；用户手动触发的 skill（user-invoked）零上下文开销但消耗用户记忆，数量多了就靠 router 兜底。

## 6. 对 ShitPM 可学的（按价值排序）

### P0-1：SKILL 措辞过一遍 negation 检查

**直接可做。** writing-great-skills 说否定式指令会反向激活（"别想大象"）。ShitPM 的 SKILL 里大量"不要自动生成 PRD""不要静默拍板"类措辞，按此哲学应改为**正面陈述目标行为**，禁令只留硬护栏。这与 R14 发现"SKILL 指令骗模型"（--example 静默失效）同类：指令层面治理，不是加程序。

### P0-2：把"完成判据可检查性"做成 SKILL 层自检条款

ShitPM 已有程序化守门（落盘存在性、baseline 哈希），但 SKILL 的分析步骤缺少"如何判断这一步做完了"的显式判据。对照 writing-great-skills：**每个 step 结尾写可检查的完成条件**，且要穷尽（"every X accounted for"）。低成本高收益，纯措辞。

### P1-3：引入 .out-of-scope/ 拒绝史（仓库级 meta）

**成本极低、收益长期。** ShitPM 的"持续约束"分散在 MEMORY 和报告里，没有集中的"拒绝史"。建议建 `docs/out-of-scope/`，每份文件：功能名 + 为什么拒绝 + 触发请求。这直接服务于"收缩方向"——**明确不做什么，比做什么更能防止膨胀**。

### P1-4：CONTEXT.md 式术语表（三段式）

ShitPM 的 references 有格式规范但**没有集中术语表**。可建 `docs/glossary.md`：Language（ShitPM 术语 + 避免词）/ Relationships（编排器、门禁、基线、确认之间关系）/ Flagged ambiguities（已解决的歧义，如"确认"一词的两种含义）。这能治"模型用 20 个词不如 1 个词"，直接服务上下文治理。

### P1-5：grilling 纪律进 align/design 提问环节

**一次一个问题 + 每个问题附推荐答案 + 事实查环境不问人 + 决策才问人。** ShitPM 的"高影响未知必须问用户"目前没有"一次一个"和"带推荐答案"两条细则。改 SKILL 措辞即可，符合"帮模型干活"而非"替模型干活"。

### P2-6：hard/soft dependency 分拆（对齐 context-loading）

ShitPM 的 context-pack 装载是统一机制，但哪些 pack 是"缺了会错"（硬依赖）、哪些是"缺了只是不锐"（软依赖）没有显式标注。对照 ADR 0001：硬依赖才显式提示，软依赖用模糊措辞。可给 manifest 加依赖等级字段（P2，先不做）。

### P2-7：router 的"地图不撒谎"纪律（spm-start）

ShitPM 已有 spm-start（只读扫描+可用动作），接近 router。对照 ask-matt：router 必须随 skill 增删同步更新，否则是"撒谎的 router"。给 ShitPM 加一条维护规则：**新增/修改 SKILL 时必须检查 spm-start 是否还准确**。

### P2-8：双轴 code-review 哲学（防一个轴掩盖另一个轴）

ShitPM 的对抗性审查是单流程（结构+业务一次审）。对照 code-review：**Standards（结构合规）和 Spec（是否忠实实现）分开跑、分开报告、不做跨轴合并排名**。ShitPM 的 design-check/v2（结构）和综合审查（业务）在编排器里已有分离雏形，可确认它们是否真的"分开报告、不合并排名"。

## 7. 明确不建议照搬的

1. **issue tracker 集成**（GitHub/Linear）：ShitPM 是本地文件制品，不需要。
2. **tracer-bullet 垂直切片**：那是代码工程的切片方式，ShitPM 是文档产物，PRD 分片已是等价物。
3. **expand–contract 宽重构**：代码特有问题，无对应。
4. **Claude plugin / marketplace 发布机制**：ShitPM 不是分发型产品（当前阶段）。
5. **subagent 并行 code-review 的 Agent 实现细节**：ShitPM 已有 subagent 契约，只要双轴报告纪律，不需要照抄编排。

## 8. 一句话总结

> **Matt Pocock 仓库的全部哲学浓缩成三句话：① 每个 skill 都为一个真实失败模式而生；② 写 skill 的目标是从随机模型里榨出可预测性——用可检查的完成判据、信息层级、leading words 和激进的裁剪；③ 仓库自己践行自己的哲学——术语表、ADR、拒绝史、router 地图，全部是"内容只存一处 + 显式记录决策"的体现。ShitPM 最该抄的是第③条（.out-of-scope 拒绝史 + CONTEXT.md 术语表 + hard/soft 依赖分拆）和第①条的 SKILL 措辞治理（negation 检查、完成判据显式化）。**
