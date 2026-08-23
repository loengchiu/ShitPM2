# R20 全量对抗性审查报告

> 日期：2026-08-05
> 审查对象：工作区当前未提交改动（自 R19 commit `443a93e` 起）+ 全量回归
> 范围：推断值机制 + PRD 文风 lint 增强 + 两层治理收尾的 15 改文件 + 2 未跟踪文档；全量 12 套测试
> 方法：git diff 逐文件语义核对、lint 规则/代码闭环验证、bundle 自洽 grep、lint 对样例实测、全量测试

## 1. 结论

**0 P0 / 0 P1 / 3 P2（全部已在本轮修复并实证，12/12 测试绿）。** 自 R19 起的未提交改动是一组高度协同的"推断值机制 + 文风 lint 增强"工作，规则↔lint↔skill↔模板↔示例↔检查清单六处一致；发现 3 处 P2（均属新增 lint 的副作用或文档对齐），已修。

## 2. 审查对象概览（自 R19 起的改动）

- **推断值机制落地**：`design-writing.md` §七·一、`spm-design` §5.2/§7、`spm-prd` 事实边界、`templates/decision-notes.md` 加"推断值清单"段、`contracts/design-review-checklist.md` 新增 X8（推断值登记完整 / 机械重复 / 高影响混入）。
- **PRD 文风 lint 增强**：`contracts/prd-writing.profile.json` 新增 5 个行首标签禁用表达式；`scripts/python/prd-style-lint.py` 新增 `LEADING_LABEL_PATTERNS`（行首锚定 STYLE001 error）；`prd-writing-rules.md`/`prd-writing-examples.md`/`prd-scene-checklist.md`/`prd-review-checklist.md`/`spm-prd`/`spm-prd-review` 同步禁止"触发：处理：成功结果：失败与恢复："等行首标签，并把交互四问按高/低影响分级。
- **操作表两列语义收紧**："是否二次确认"只填 是/否、"后续去向"直接写值，禁止填"待确认"（`design-writing.md`/`templates/design.md`/X7）。

## 3. 发现并修复的问题（P2）

### P2-1：prd-style-lint 把行首标签表达式错当占位符，导致误报与重复

- **根因**：`prd-style-lint.py:82` 的 `PLACEHOLDER_PATTERNS` 由 `forbidden_expressions` 全量生成，把新增的 `触发：/处理：/成功结果：/失败与恢复：/失败结果：` 也纳入；而 STYLE008 按**子串**匹配（`pattern in line`）。
- **两类后果**：
  1. 行首 `触发：…` 同时被 STYLE001（error，正确）和 STYLE008（"占位符" warning，误标 + 重复）命中；
  2. 更严重——`系统处理：按规则执行`、`数据处理：…`、`订单处理：…` 等合法正文被 STYLE008 子串误伤为"占位符"警告，与本意（这些是标签反模式、不是占位符）直接矛盾。这是本次改动引入的回退：改动前 `处理：` 不在禁用表达式，不误报。
- **实测**：修复前样例 `系统处理：按规则执行` 被 STYLE008 命中；修复后该行不再命中，行首 `触发：/处理：/成功结果：` 仍只报 STYLE001（3 error / 0 warning）。
- **修复**：从 `PLACEHOLDER_PATTERNS` 排除非加粗的 `：`/`:` 结尾表达式（即行首标签域），只由 STYLE001 行首锚定拦截。`test-prd-style-lint.py` 仍绿。

### P2-2：spm-design §7 推断值汇总表列序与 decision-notes 模板不一致

- SKILL 写 `# | 位置 | 推断值 | 推断依据 | 确认结果`，模板表头是 `推断值 | 位置 | 推断依据 | 确认结果`（首列一个是 `#`、一个是 `推断值`）。模型若严格按 SKILL 建表，列与待填充模板不对齐。
- **修复**：SKILL 改为 `推断值 | 位置 | 推断依据 | 确认结果`，与模板一致。

### P2-3：prd-writing-rules 禁用标签枚举漏列 `失败结果：`

- profile + lint 已禁用 `失败结果：`，但 §3/§8.1 正文只枚举 触发/处理/成功结果/失败与恢复，未点名 `失败结果：`（靠"等"兜底）。文档与单一事实源不齐。
- **修复**：§3、§8.1 两处枚举补 `失败结果：`。

## 4. 复核通过项

| 项 | 结论 |
|---|---|
| 规则↔lint↔skill↔模板↔示例↔检查清单一致性 | 六处对齐；示例新增"自动动作自然语言"段落示范替代写法 |
| bundle 自洽（references/skills/templates 是否自身违反新禁用标签） | grep 行首标签 0 命中，无自身矛盾 |
| design-index 解析器不受影响 | 操作表仅列值语义收紧（是否二次确认/后续去向），表头十列未变；tuple 严格匹配与 test-design-index 样本均有效 |
| 全量测试 | 12/12 绿（含本轮 P2-1 修复后 lint 测试） |
| 行尾符 | 工作树 32 个 .py 统一为 LF，无文件内混合（纠正旧记忆"py CRLF"） |
| 推断值机制落地形态 | 纯模型行为规范（无新增检查器/门禁/回执），与 AGENTS.md 准入原则及未跟踪执行报告一致 |

## 5. 观察（非缺陷，关联已知项）

- **确认门禁根因仍未落地**：`design-confirmation.py` 仍只做 SHA-256 哈希戳，未校验"编排器接受（含综合审查）"也未校验推断值清单完整性；下游 `spm-prd`/`spm-prototype` 的"已确认"判据仍是弱人类确认。这是 2026-07-30 记录的已知根因（`docs/plans/2026-07-30-confirm-gate-fix-execution-plan.md`），本轮推断值机制按"模型行为规范、不加脚本门禁"的既定取舍未触碰它——属延续状态，非回归。
- **对 references/模板跑 lint 会产生预期噪声**：示例/规则文件会"引用"禁用标签（如"禁止写成'触发：'…"），被 STYLE001 命中——这是把 PRD lint 误用于非 PRD 文档的产物，非产品缺陷；lint 只对 PRD 输出语义有效。

## 6. 修复后 Git 状态（本轮）

- 改 3 文件：`scripts/python/prd-style-lint.py`（P2-1）、`skills/spm-design/SKILL.md`（P2-2）、`references/prd-writing-rules.md`（P2-3）；
- 叠加 R19 以来未提交改动共 18 文件改动 + 2 未跟踪报告/方案；
- 未执行 commit / push（等用户指示）。
