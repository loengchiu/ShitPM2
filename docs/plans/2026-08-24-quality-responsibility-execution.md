# ShitPM 质量责任架构：执行与验收

> 状态：已确认，待执行。
> 读者：负责维护 ShitPM 仓库的 AI。
> 目标：用最少的脚本和指令，让脚本、LLM 与人类各自只处理最适合的问题；以最终 Design、PRD、Prototype 的质量验收，而不是检查数量或过程证明。

## 1. 不可改变的边界

- Design 是唯一产品事实源；PRD、Prototype 或 Review 不能反向补写或覆盖它。
- Skill 是 AI 行为协议，不是工作流引擎；不新增 `check-all`、统一评分、综合 JSON、检查编排器、机器签名或自动推进门禁。
- 脚本只处理可重复的确定性事实；语义、闭环、体验和可实施性由 LLM 判断；会改变产品的取舍由人决定。
- Review 只输出第二意见，不自动修改、确认、调用 Fix 或推进阶段。
- 每个改动只修改必需文件；先读调用方和测试，再改；每个工作包独立提交、独立验证、可整体回退。

## 2. 唯一的三类质量结论

| 结论 | 主要责任方 | 何时使用 | 处理方式 |
|---|---|---|---|
| `red` | 脚本 | 正式事实、文件或真实运行结果存在可重复的明确错误 | 生成时直接修；Review 时列为确定性问题；可使用失败退出码 |
| `risk` | LLM | 语义、业务闭环、状态、权限、承接、可实施性或体验有风险，无法由字符串或结构稳定裁定 | 给出证据、影响、结论或“未评估”；不能默认通过 |
| `decision` | 人类 | 不同答案会改变流程、权限、数据范围、系统边界或验收标准 | 只向产品负责人给出问题、选项、影响与推荐 |

`P0/P1/P2` 继续表示处理优先级；`structure/content/consistency` 继续表示问题落点。它们不能替代 `red/risk/decision`。

## 3. 脚本、LLM 与人的完成标准

### 脚本

只保留同时满足四项的检查：期望值来自正式事实源或实际运行；输入可稳定解析；相同输入得到相同结论且误报低；结果能直接定位并触发最终产物修正。

- `red`：不可读、不可解析、无法构建、明确缺失、明确冲突。
- `evidence`：页面、路由、字段、锚点等枚举，供 LLM 判断。
- `unsupported`：格式或事实不足，不能安全判断。

只有 `red` 允许失败退出码。脚本达到“已枚举范围内 100% 精确”就停止；不判断页面是否真正帮助用户完成任务。

### LLM

生成时，在同一动作内完成材料理解、适用自检和修正：发现 `red` 直接修；高影响未知转为 `decision`，不静默补写。

Review 时，独立读取事实闭包和脚本结果。每个适用检查项必须有正文落点、`risk` 结论或明确不适用理由；每条 `evidence` / `unsupported` 必须有结论或“未评估”。脚本返回 0 绝不等于语义质量通过。

### 人类

不确认哈希、上下文包、测试数、脚本输出或过程回执。只确认每个 `decision`，并对需要交付的 Prototype 做业务可用性与视觉/品牌验收。未决事项必须保持 pending，不得被下游当作已确认事实。

## 4. 工作线

```text
生成：最小可读性检查 → LLM 分析、写作与自检 → 当前产物适用的脚本核验 → 修正 red 或暴露 decision
Review：目标事实闭包 → 脚本 red/evidence/unsupported → 独立 LLM Review → 人类决定修复或取舍
```

生成线没有 `red` 且高影响未知都已显式处理，才可称当前产物完成。Review 线不自动修改或推进；除不可读、无法解析外，所有问题都作为 Review 结论继续审查。

## 5. 已核实的仓库现状

- 三个 Review Skill 已要求区分确定性问题、产品风险和待用户决策。PRD 与 Prototype 一致性检查也已区分确定性冲突、可能遗漏和需语义判断。因此不重写现有 JSON 输出结构，不为改名新建 JSON。
- `design-set.py`、`prototype-source-check.py`、`prd-style-lint.py` 仍承担合适的确定性职责，保留。
- `prd-consistency-check.py` 和 `prototype-consistency-check.py` 保留；明确事实冲突可为 `red`，别名、同义表达、字段合并/拆分、复杂权限、状态后果和体验只作证据。
- `stage-prep.py` 仍服务旧项目兼容，且被现有 PRD 检查动态使用；本次不动。
- `context-budget.py` 没有运行时 Skill 消费者，但仍被 `stage-context.py` 的推荐读取清单、`test-context-loading.py` 和 `test-resource-integrity.py` 引用。这些是证明性引用，不是用户项目的交付能力。删除候选成立，但删除必须同步清除这些引用。

## 6. 实施步骤

### A. 固化共同语言

1. 阅读 `contracts/review-checklist.md` 和三个 Review Skill 的现有职责段。
2. 在公共契约中只保留一处完整的 `red/risk/decision` 定义与输出规则。
3. 三个 Review Skill 改为引用公共定义，只保留各自范围和行动；压缩重复解释。
4. 在 `spm-design`、`spm-prd`、`spm-prototype` 中仅补充必要的生成自检责任：`red` 直接修，高影响未知转 `decision`。

完成条件：所有 Review 都能把明确脚本错误写为 `red`；非确定性脚本结果写为 `risk`、未评估或上游建议；`decision` 包含问题、选项、影响与推荐；完整定义只出现一处。

### B. 删除重复的预算脚本

1. 在全仓库（包括安装、宿主映射、使用文档）搜索 `context-budget`。
2. 若发现真实运行时调用或对外兼容承诺，停止删除，先迁移到 `context-pack.py` 并验证；不得静默破坏兼容性。
3. 若仍只有已知证明性引用，删除 `scripts/python/context-budget.py`，并同步从 `stage-context.py`、`test-context-loading.py`、`test-resource-integrity.py` 移除相关路径、加载和断言。
4. 保留并验证 `context-pack.py --dry-run --max-tokens` 和 `--fail-on-budget`，这是实际上下文装载路径的预算能力。

完成条件：没有已删除路径的调用、说明或测试；Skill 仍能通过 `context-pack.py` 显示预算；没有为了保留测试数量而保留空测试。

### C. 只按误报证据收紧一致性检查

先为 PRD 和 Prototype 分别补最小样例，再改规则。不要因为“理论上可能误报”而改。

| 现有脚本输出 | 责任归类 | 退出码 |
|---|---|---|
| `deterministic_conflicts`，以及明确 `missing`、`hallucinated`、`attribute_mismatch` | `red` | 失败 |
| `possible_omissions` | `risk` 的证据 | 成功 |
| `needs_semantic_judgment` | `risk` 的证据 | 成功 |
| 输入不可读、索引无效、构建无法执行 | `red` | 失败 |

只有满足“正式事实、稳定解析、可重复、可直接修正”的规则才能硬失败。发现某条硬规则误报时，将它降为 `evidence` 或 `unsupported`，并把对应样例与规则在同一次提交中交付。

完成条件：明确冲突继续失败；别名、合并/拆分和复杂语义不再被硬拦；Review 明确处理每项非确定性证据。

### D. 审计 `context-pack.py`，不预设删除

为每个 CLI 参数列出真实调用方、用户可见用途和测试。无消费者且只记录过程的参数，才以独立小改动删除。

不得仅因参数多而删除 `--role`、`--pass`、`--module`、`--card`、`--applicability-json` 或预算能力。`run.json`、`--verify-run` 和运行记录先按相同证据审计；本方案不预先宣布删除。

完成条件：保留的参数有调用方或明确用户能力；删除的参数没有剩余调用、说明或测试；不产生新的兼容层。

## 7. 验收

### 仓库级

| 验收目标 | 证据 | 通过标准 |
|---|---|---|
| 公共术语唯一 | 搜索三类结论和重复定义 | 公共契约是唯一完整定义，Skill 不复制规则 |
| 脚本不冒充 Review 结论 | 用最小样例触发 `possible_omissions` 和 `needs_semantic_judgment` | Review 要求写 `risk`、未评估或上游建议，不能以退出码为 0 宣布通过 |
| 高影响未知被暴露 | Review 一个权限、状态、数据范围或系统边界不完整的 Design | 输出含选项、影响与推荐的 `decision` |
| 删除预算脚本无残留 | 全仓搜索、安装验证、资源完整性检查 | 无调用、路径断链、过时说明或仅为其存在的测试 |
| 实际预算能力仍可用 | 运行 `context-pack.py --dry-run --max-tokens` 的限额与超限样例 | 输出预算；超限时按 `--fail-on-budget` 失败 |
| 明确冲突仍拦截 | PRD/Prototype 各使用一个正式事实直接冲突样例 | 输出确定性冲突、失败、位置可定位 |
| 语义差异不硬拦 | 别名、字段合并/拆分、复杂权限或状态后果样例 | 成功返回，分类为可能遗漏或需语义判断 |
| 改动范围干净 | 针对性测试、全量回归、`git -c core.whitespace=cr-at-eol diff --check` | 无空白错误；每行改动能对应 A/B/C/D |

合并前建议运行：

```text
python scripts/python/test-context-loading.py
python scripts/python/test-resource-integrity.py
python scripts/python/test-prd-consistency-semantics.py
python scripts/python/test-prototype-consistency-check.py
python scripts/python/test-prototype-source-check.py
python scripts/python/test-shitpm-regression.py
git -c core.whitespace=cr-at-eol diff --check
```

单个工作包只需阻塞其直接相关的测试；合并前再跑完整集合。

### 真实项目

仓库测试通过后，在一个简单项目和一个复杂真实项目的副本中盲测。开始前不得读取历史 Review、旧问题清单、旧评分或生成者理由；只在产物完成后用于比对。

记录事实，不做总分：

1. 脚本发现的明确错误及其真实率；
2. LLM 提出的 `risk`，以及哪些导致修复或被证明误报；
3. `decision` 的数量、质量、最终选择与下游影响；
4. 研发/业务验收发现的遗漏、返工和原因；
5. 产品负责人是否少看过程性信息、更多回答真正改变产品的问题。

架构有效的标准：两个项目完成盲测；明确错误没有明显漏检；脚本误报下降或不升；高影响未知被显式暴露；删除证明性流程没有造成可归因的产物质量倒退。

## 8. 停止与回退

出现下列情况时停止当前工作包，回到事实或 Skill 责任，不新增脚本：无法指出最终产物会具体错在哪里；需要从 PRD/Prototype 反向猜 Design；规则在不同项目中结论不稳定却想硬失败；或用户需要产品选择但系统试图静默默认。

优先补材料读取、分析责任、高影响提问或最终自检。只有真实复发、LLM 常漏、低误报可检出、结果直接触发修正四项证据齐全，才能新增确定性脚本。
