---
name: spm-prd
description: "PRD 阶段——根据已确认的 Design 直接生成研发可评审的 PRD。用于用户要求生成 PRD、需求规格或产品需求文档时；必须通过 Design 确认，按业务闭环组织，保持 Design 语义，不依赖 Prototype，不把高影响未决事实静默拍板。"
---

## 路径解析

从系统 prompt 的 `ShitPM bundle root:` 读取 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`schemas/` 使用 `$BUNDLE/` 前缀。
- `.workflow/`、`output/` 使用当前项目根目录。

## 核心职责

PRD 只有两条质量主线：

1. **内容质量**：完整承接已确认 Design 的产品事实，并保持事实一致。
2. **阅读质量**：按业务闭环连续阅读，让产品、研发、测试可以直接评审。

确认版 `output/design/design.md` 是唯一产品事实源；存在 Design confirmation 时，按当前项目约定读取确认结果。Prototype、旧 PRD、示例和通用产品经验只能帮助理解，不能覆盖或补造 Design 事实。`output/prd/prd.md` 是交付物，不是新的事实源。

## 开始前检查

1. 确认 `output/design/design.md` 存在且可读。
2. 运行 Design confirmation 检查：

   ```text
   python $BUNDLE/scripts/python/design-confirmation.py --project-root . check
   ```

3. 检查失败时停止，不生成或覆盖 PRD；用自然语言说明需要用户确认当前 Design。只有用户明确确认后，才运行 `confirm` 记录哈希：

   ```text
   python $BUNDLE/scripts/python/design-confirmation.py --project-root . confirm
   ```

不得在用户未明确确认前运行 `confirm`。不要求 Prototype、Design Review、metadata 或其他历史中间文件作为 PRD 前置条件。

## 模型与上下文

流程开始时根据 Design 的复杂度选择推理深度；执行中不切换模型。

先完整读取确认版 Design，再选择路径：

### 普通 PRD

普通 PRD 只执行一次 `writing`，随后直接写完整 PRD：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass writing
```

`writing` 按 `$BUNDLE/contracts/context-loading.manifest.json` 装载 PRD 边界、结构、动作、名词、版本和写作内自检所需规范。示例只在命中特定写作难点时追加，不默认全量加载。

### 超大型 PRD

只有完整 Design、规则和目标 PRD 无法稳定同时保留，或一次写作已出现截断、重复、冲突、遗漏趋势时，才使用 `module`：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass module --card <scene-key> --example <example-key>
```

`module` 只用于超大型 PRD；模块边界必须来自 Design 的业务边界，不按页数、字段数或字数机械切片。模块草稿只写入 `.workflow/runtime/context/prd/` 临时位置，不进入 `output/prd/`，不成为事实源。主 Agent 最终只写入一次完整 PRD，统一名词、跨模块共用规则和重复内容；最终检查只针对完整 PRD。

`context-budget.py` 仅作容量参考，不是普通 PRD 的固定前置步骤，不自动决定是否分批。

## 写作流程

1. 读取确认版 Design，识别产品目标、范围、系统边界、共用规则和业务闭环。
2. 先写“总体说明”：只放跨模块共用且只需定义一次的名词、角色/组织/数据范围基线、共用状态规则和页面映射。
3. 按业务结果组织业务模块。每个模块就近写目标与边界、对象关系、角色/权限/数据范围、流程、状态与规则、业务阶段、字段、外部协作/异常/恢复、模块验收和待确认事项。
4. 将管理端和移动端放在所属闭环的真实业务阶段；页面是承接载体，不是全文唯一组织轴。共用页面只定义一次，其他模块说明适用范围。
5. 字段按业务对象定义一次，在页面或动作处补充使用差异；状态、权限、异常、恢复和验收放在所属模块，不依赖文末总表。
6. 需要表达跨角色、跨系统或关键状态闭环时，生成 `.drawio` 源文件并按 2 倍分辨率（X2）导出 `.png`；不使用 Mermaid。图、源文件和正文使用相同名称和流程。
7. 把跨模块待确认项放在总体说明，把模块待确认项放在对应模块末尾；文末只做索引。

直接写入 `output/prd/prd.md`，同时按既有项目约定维护 `output/prd/decision-notes.md`；不要生成额外的 Design→PRD 对照表、覆盖率 JSON、验证回执或其他证明性中间资产。

## 事实边界

不得从常见产品经验补造页面、字段、角色、权限、状态、流程、接口参数、默认值、排序、分页、超时、重试、补偿、逐字提示文案、历史数据处理方式或外部系统行为。高影响未知必须保留为待确认并回到 Design；低影响未知可以用不承诺具体值的保守表达。

Design 待确认项必须仍标为待确认。若 Prototype 或旧 PRD 与 Design 不一致，以 Design 为准，并在决策记录中说明处理；若 Design 本身需要改变，停止并回到上游 Fix，而不是在 PRD 中自行改写事实。

## 生成内自检与直接修正

展示 PRD 前，在同一写作动作内逐项回读 Design，并发现问题就直接修正：

1. 目标、范围、系统边界和共用规则是否准确承接；
2. 每个业务闭环是否有清楚的起点、业务结果、终点和边界；
3. 管理端、移动端、页面和动作是否落在真实业务阶段，共用页面是否只有一个权威定义；
4. 角色、权限、数据范围、敏感动作和职责分离是否就近可读；强动作是否显式写明执行角色和允许状态；
5. 对象、字段、字段属性、状态、状态变化、异常和恢复是否准确且有权威落点；
6. 每个核心动作是否写清前置条件、输入与校验、处理规则、成功/失败结果和数据/状态副作用；
7. 查询、统计、下钻、导出、表单配置和外部协作是否写清适用口径，是否误加无依据数字；
8. 模块是否可以脱离其他模块独立理解，是否存在“同上”或模糊跨节引用掩盖关键内容；
9. 图、`.drawio` 源文件、PNG 与正文的名称、角色和流程是否一致；
10. Design 待确认项是否仍保留，是否出现未授权的新页面、字段、角色、状态、权限或流程；
11. 文风是否存在标签式正文、动作流水账、表格主导、重复稳定标识、机读字段泄漏、AI 痕迹或明确占位符。

不要用额外对照表、覆盖率、脚本退出码或签名类证明文件证明语义完整性。

## 最终检查与结果处理

按顺序运行：

```text
python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .
```

`prd-style-lint.py` 只识别确定性阅读坏味道：error 返回 `1`，只有 warning/info 返回 `0`，文件不存在或程序无法运行返回 `2`。所有 error 必须修复；warning/info 必须逐项阅读，确认是真问题就修复，确认是误报才保留。不生成永久检查报告或回执。

`prd-consistency-check.py` 保留分类输出：

- `deterministic_conflict`：明确幻觉、字段/枚举/属性冲突、权限反转等，返回 `1`，阻断交付并修复；必要时回到 Design。
- `possible_omission`：可能遗漏或解析不到落点，返回 `0`，由 AI 对照 Design 判断。
- `needs_semantic_judgment`：需要语义判断，返回 `0`；高影响且仍无法判断时停止并询问用户。
- `ok`：返回 `0`，仍需人工阅读最终 `prd.md`。
- 致命运行错误：返回 `2`，停止并修复输入或运行问题。

不得只看退出码 `0` 就宣布 PRD 一致。

## 输出与停止边界

写入：

- `output/prd/prd.md`：最终人读 PRD；
- `output/prd/decision-notes.md`：按项目约定维护的轻量决策记录；
- `.workflow/status.json`：更新 `current_stage` 为 `prd`，登记 `artifacts.prd` 为 `output/prd/prd.md`。

最终交付前必须直接阅读真实 `prd.md`，确认内容完整、事实一致、模块可独立阅读、图文一致。不要自动执行 PRD Review，不自动推进 Prototype，不自动修改 Design 确认。Design 缺失、确认失效、输入不可解析或高影响事实缺失时停止并报告，不用补丁掩盖问题。
