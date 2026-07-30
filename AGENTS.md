# ShitPM 仓库开发规则

本文件仅用于维护 ShitPM 仓库本身，不属于 ShitPM 用户项目的运行时规则。
安装脚本不会将本文件加载到用户项目上下文。
用户运行时行为以 `skills/`、`contracts/`、`references/`、`schemas/`、`templates/` 和 `USAGE.md` 为准；产品契约详见 `USAGE.md`。

## 1. Skill 定位与精简原则

### Skill 的定位

1. **Skill 是 AI 行为协议，不是应用程序、工作流引擎或审计平台**：Skill 的职责是约束 AI 如何理解问题、做出判断、生成和修改最终产物；不要把每个思考步骤实现成程序节点、状态、回执或中间服务。
2. **最终产物优先于执行证明**：评价 Skill 只看最终 Design、PRD、Prototype 是否正确、完整、可用，以及用户操作是否清晰；"动作全部执行""Schema 全部通过""回执齐全"不能作为质量证明。
3. **分析责任不等于程序步骤**：ABC 是完整模式必须承担的需求理解、业务建模和产品承接责任，不是固定任务数量、JSON 数量、模型调用次数或最终文档目录。允许 AI 在一次完整思考中承担一层责任。
4. **不要过度设计**：给出方案之前要思考这个方案是不是过度设计了，是不是有更简洁更高效的实现方式。

### 工具和检查的准入原则

5. **默认不新增检查工具**：章节覆盖、业务闭环、状态合理性、权限一致性、页面承接、字段遗漏和高影响判断，优先写入对应 Skill 的 AI 自检清单，不为此新增解析脚本、检查器或结构契约。
6. **指令优先于脚本，程序只处理确定性问题**：默认 instruction-only，脚本只在需要确定性行为或外部工具接入时才引入；程序只承担 AI 不适合稳定完成的确定性问题（文件是否存在、内容能否解析、确认后哈希是否变化、真实页面能否加载、依赖库是否缺失）。程序不得替代业务判断，也不得根据结构结果补写产品事实。
7. **新增工具必须同时满足四项证据**：真实项目中同类缺陷反复发生；AI 自检仍经常漏掉；工具能以较低误报稳定识别；识别结果会直接触发最终产物修正。缺少任一证据，不得进入主流程。
8. **对最终结果无影响的工具应删除**：只生成报告、只记录 provenance、只包装其他命令、只验证内部中间 JSON、只证明某步骤执行过，且没有稳定消费者或不会改变最终产物的工具，不得因"可能有用"继续保留在活动主流程。
9. **禁止复杂度换皮**：删除多个检查器后，不得再创建"统一检查器""最终验证回执""综合门禁""机器签名"或新的检查 JSON 来重新包装同一套复杂度。

### 生成与确认原则

10. **自检与生成合并**：产物生成者在展示前按 Skill 清单自检，发现问题直接在同一动作内修正；默认不拆成独立检查任务，不生成检查报告，不要求检查回执。
11. **高影响未知必须问用户**：涉及核心流程、角色权限、数据范围、关键状态、系统边界或范围边界的歧义，不得由检查器或 AI 静默补全；应合并成少量阻断问题询问用户。

### 精简和质量回归原则

12. **先删除证明流程，再保护分析责任**：可以删除检查脚本、回执、检查 JSON、细粒度任务和重复解析，但不得删除简单模式的最小业务闭环、完整模式的 ABC 责任和最终一次跨层自检。
13. **精简不是把代码搬家**：删除旧工具前先确认是否仍有真实消费者；若没有，直接删除，不把上千行逻辑迁移到另一个脚本或公共模块以维持旧结构。
14. **测试服务当前产品行为**：行为被明确删除后，同步删除或改写验证旧行为的测试；不得为了保持旧测试数量而保留废弃工具，也不得用模拟回执证明语义质量。
15. **质量以真实最终产物验收**：语义质量应使用简单项目和复杂真实项目检查最终产物中的错误事实、高影响遗漏和下游返工，不能用脚本退出码、任务数量或中间资产完整率代替。
16. **出现质量问题先修 Skill**：精简后出现遗漏时，先定位缺失的分析责任，改进材料读取、ABC 提示、高影响提问或最终自检清单；只有满足工具准入证据后，才能考虑新增程序检查。

实施任何新门禁、检查器、中间结构或回执前，必须先回答：

> 删除它以后，最终产物会具体错在哪里？现有 Skill 自检为什么无法解决？是否有真实项目证据？
>
> 无法给出具体答案时，不实施。

## 2. Skill 与 Plugin 编写原则

> 提炼自 OpenAI《Build skills / Build plugins》官方说明（源文件：`D:/work/AIskills/openai-plugin-and-skill-authoring.md`）。只取可迁移的编写原则；OpenAI 平台专属机制（plugin 目录、MCP 注册、UI 元数据、per-skill `scripts/ references/ assets/` 子目录布局）仅作背景——已映射到 ShitPM 实际约定（skill 是单个 `SKILL.md`，`references/ scripts/ templates/` 在仓库级），不强制套用其目录树。

### 何时用 skill、何时用脚本

1. **可复用工作流才做成 skill**：skill 是"可复用工作流的编写格式"。只有当某个流程值得固化、复用或交给 AI 稳定执行时才写成 skill；一次性任务不必造 skill。
2. **先 skill 后 plugin**：个人工作流先用 skill 快速迭代；只有当要分享、打包多个相关 skill、连接外部服务或分发给团队时，才打包成 plugin。plugin 是可安装的包，可含 skill、MCP server 或两者。
3. **默认指令优先，脚本只在两类情况用**：skill 默认 instruction-only；引入脚本只读当"需要确定性行为"（如哈希、文件存在性、解析、加载校验）或"需要外部工具/外部系统接入"时。其余判断交模型。与 §1 #6 一致：脚本不得替代业务判断、不得据结构结果补写事实。

### Skill 内部结构：什么内容放哪里

> ShitPM 的 skill 是单个 `SKILL.md`，不像 OpenAI 那样在 skill 内再建 `scripts/ references/ assets/` 子目录；这些职责由仓库级目录承担。原则一致：SKILL.md 保持精简，详细的"文档"外置。

4. **SKILL.md 只放指令与元数据**：`name` + `description`（触发契约，见下）+ 工作流步骤（祈使句、写明输入与输出）。这是 skill 被触发时加载的核心，必须精简。
5. **references/ 放文档，不放指令**：详细的格式规范、检查清单、写作样例、领域知识（如 `design-state-format.md`、`prd-writing-rules.md`）放进仓库级 `references/`，由 SKILL.md 引用；不要让 SKILL.md 被大段参考材料撑爆。理由：宿主按 progressive disclosure 只先加载 name+description，SKILL.md 越精简，触发越准、上下文越省。
6. **scripts/ 放确定性程序**：哈希、解析、存在性检查、加载校验等稳定逻辑放仓库级 `scripts/`（Python），由 skill 调用；不在 SKILL.md 里写复杂程序逻辑。
7. **templates/ 放模板与资源**：原型壳、文档骨架等可复用模板放仓库级 `templates/`，对应 OpenAI skill 的 `assets/`。

### 触发与描述

8. **description 是触发契约**：用简洁的 scope 与边界写明"何时该用、何时不该用"，并把关键用例和触发词前置；隐式触发依赖 description，描述被截断时仍能匹配合适的 skill。
9. **单一职责**：一个 skill 只解决一个明确工作流，不把不相关任务塞进一个 skill；需组合时拆多个 skill 再编排。
10. **指令写明输入与输出**：明确每一步读什么、产出什么，不让 AI 猜。
11. **测试触发行为**：用代表性 prompt 验证 skill 是否被正确触发、是否有错误 skill 抢触发；不符就改 description，而非改逻辑迁就错误触发。

## 3. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 4. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 5. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 6. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
