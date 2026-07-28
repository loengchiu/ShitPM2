## 1. 语言原则

- 默认使用简体中文。
- 技术术语保留英文原文，必要时首次标注中文。
- 文档直接、清楚、可执行。
- 对外产物不得出现 AI 痕迹、内部路径、metadata 字段或调试字段。
- 写作与产物规则优先描述目标状态；只有门禁、安全、越界、防幻觉才优先用禁止式写法。

## 2. ShitPM 产品契约

本仓库当前产品契约以 `output/shitpm-v2-prd.md` 和 `output/shitpm-v2-implementation-design.md` 为批准基线。旧 V2 review、旧实施指令和历史讨论仅作为审计材料，不得覆盖当前基线。

所有 Skill、脚本、模板、契约和文档必须遵守：

1. **核心目标是 Design 质量**：V2 的首要目标是让完整模式的最终 `design.md` 达到 Park A、B、C 三层完整分析的质量，同时保持一份适合人类阅读的文档。
2. **两种用户模式**：`spm-design` 只提供简单模式和完整模式。由用户选择；未指定时只询问一次，不自动判断模式。
3. **简单模式最小闭环**：只完成目标、范围、主路径、关键规则、必要状态与权限、功能、数据、异常和验收，不生成无关空章节。
4. **完整模式 ABC 责任**：逐项考虑需求理解、业务建模、业务模型一致性挑战、系统需求和跨层一致性挑战；只输出适用、影响方案或必须说明“不适用”的结论，不机械生成所有答案或章节。ABC 是内部分析责任，不是最终文档目录。
5. **实现机制不是产品目标**：稳定 ID、Schema、缓存、单模型、多遍处理、Sub-agent 或其他编排方式可以按实现需要选择，但不得作为产品完成证明，也不得污染最终产物。
6. **Align 可选**：`spm-align` 是可选需求整理模块，无 Align 也能直接进入 `spm-design`。
7. **Design 双重职责和唯一事实源**：`spm-design` 同时承担 Product Definition 和 Design Baseline；用户确认后的 `output/design/design.md` 是 PRD 和 Prototype 的唯一产品事实基线。
8. **双下游并列**：PRD 和 Prototype 都是 Design 的直接下游，可以独立生成、任意顺序生成或只生成其中一个。
9. **首次生成承担完整责任**：Design 必须在首次正式写入前完成对应模式的分析、挑战和成品审查；Review 不承担计划内补全。
10. **Review 按需**：Review 是独立第二意见，不是流程门禁，不自动推进阶段，不自动修改产物。
11. **确定性检查边界**：程序只阻断可可靠证明的结构、引用、完整性和执行错误；业务合理性、隐含语义和高影响判断由分析协议和用户确认处理。
12. **decision-notes.md 仅审计**：只记录设计决策、偏离、权衡、待确认，不作为下游事实输入，不参与确认有效性判断。
13. **内部记录不成为事实源**：metadata、status、旧 review 结果、ABC 中间分析和内部缓存只用于兼容、导航、执行或审计，不得向 PRD、Prototype 注入 Design 中不存在的事实。
14. **下游边界保持**：本版本不重写 PRD 的页面组织和写作风格，不改变 Prototype 的 HTML + Vue + Tailwind + daisyUI + 本地 lib 架构。

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

## 过程审计

Design / PRD 产出时同时输出 decision-notes.md，记录相对于上游基准的四类决策：

- **设计决策**：上游未覆盖但必须做的选择；
- **偏离**：未按上游执行的地方及理由；
- **权衡**：考虑过但未采用的方案及原因；
- **待确认**：需要用户定夺的问题。

路径：Design → `output/design/decision-notes.md`（基准：实际输入基准，align.md 或用户原始需求），PRD → `output/prd/decision-notes.md`（基准 Design）。按四类分节，每条列表项写决策和原因；无内容写“无”。
