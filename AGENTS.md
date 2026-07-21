## 1. 语言原则

- 默认使用简体中文。
- 技术术语保留英文原文，必要时首次标注中文。
- 文档直接、清楚、可执行。
- 对外产物不得出现 AI 痕迹、内部路径、metadata 字段或调试字段。
- 写作与产物规则优先描述目标状态；只有门禁、安全、越界、防幻觉才优先用禁止式写法

## 2. vNext 产品契约

本仓库的 ShitPM 产品契约以 `output/shitpm-vnext-prd.md` 和 `output/shitpm-vnext-implementation-design.md` 为批准基线。所有 Skill、脚本、Schema、模板、契约、文档必须遵守：

1. **Align 可选**：`spm-align` 是可选需求整理模块。空项目、无 Align 也能直接进入 `spm-design`。
2. **Design 双重职责**：`spm-design` 同时承担 Product Definition 和 Design Baseline，不新增 `spm-define` 阶段。
3. **Design 是唯一事实源**：用户确认后的 `output/design/design.md` 是 PRD 和 Prototype 的唯一产品事实基线。确认标记为 `.workflow/confirmations/design.json`，只记录版本哈希，不复制产品事实。
4. **双下游并列**：PRD 和 Prototype 都是 Design 的直接下游，可以独立生成、任意顺序生成、只生成其中一个。PRD 不是 Prototype 的前置，Prototype 不是 PRD 的前置。
5. **首次生成承担完整责任**：生成 Skill 必须在首次正式写入前完成语义对照和自检。Review 不承担计划内补全。
6. **Review 按需**：Review 是独立挑战和第二意见，不是流程门禁，不自动推进阶段，不自动修改产物。
7. **decision-notes.md 仅审计**：只记录设计决策、偏离、权衡、待确认，不作为下游事实输入，不参与确认有效性判断。
8. **metadata legacy**：metadata、status、旧 review 结果只用于兼容、导航或确定性辅助，不得成为产品事实源。新主流程不依赖 metadata。
9. **一个流程一个模型**：模型在独立流程开始前选择，执行中不切换。模型建议必须是运行时输出，不只在背景说明。
10. **不可改变的产品决策**：PRD 模板/页面组织/写作风格不改；Prototype 的 HTML + Vue + Tailwind + daisyUI + 本地 lib 架构不改；不引入 Sub-agent、自动路由和模型中途切换。

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
 ```
 1. [Step] → verify: [check]
 2. [Step] → verify: [check]
 3. [Step] → verify: [check]
 ```

 Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 7. 执行环境

- 执行 PowerShell 命令时固定使用 PowerShell 7：`C:\Users\guduj\AppData\Local\Microsoft\WindowsApps\Microsoft.PowerShell_8wekyb3d8bbwe\pwsh.exe`。
- 执行 Bash 命令时固定使用 Git Bash：`C:\Program Files\Git\bin\bash.exe`。
- 不依赖裸命令 `pwsh` 或 `bash` 的 PATH 解析，避免命中错误的应用别名或 WSL 入口。

## 过程审计

design/prd 产出时同时输出 decision-notes.md，记录相对于上游基准的四类决策：

- **设计决策**：上游未覆盖但必须做的选择
- **偏离**：未按上游执行的地方及理由
- **权衡**：考虑过但未采用的方案及原因
- **待确认**：需要用户定夺的问题

路径：design → `output/design/decision-notes.md`（基准：实际输入基准，align.md 或用户原始需求），prd → `output/prd/decision-notes.md`（基准 design）。按四类分节，每条列表项写决策+原因，无内容写"无"。
