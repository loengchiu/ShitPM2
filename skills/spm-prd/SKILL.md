---
name: spm-prd
description: "PRD 阶段——根据已确认的 Design 直接生成研发可评审的 PRD。用于用户要求生成 PRD、需求规格或产品需求文档时；必须通过 Design 确认，保持 Design 语义，不依赖 Prototype，不把高影响未决事实静默拍板。"
---

## 路径解析

从系统 prompt 的 `ShitPM bundle root:` 读取 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`schemas/` 使用 `$BUNDLE/` 前缀。
- `.workflow/`、`output/` 使用当前项目根目录。

## 核心职责

PRD 只有两条质量主线：

1. **内容质量**：完整承接已确认 Design 的产品事实，并保持事实一致。
2. **阅读质量**：让产品、研发、测试可以连续阅读、直接评审；遵守十类阅读质量标准。

`output/design/design.md` 是唯一产品事实源。其他材料、历史 PRD、Prototype 只能帮助理解，不能覆盖确认版 Design。`output/prd/prd.md` 是交付物，不是新的事实源。

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

流程开始时输出模型等级和推理深度建议：Design 复杂、跨模块或存在高影响未决事实时使用深度推理模型；决策完整且关系简单时可用轻量模型；无法判断时按深度推理模型处理。执行中不切换模型。

先完整读取确认版 Design，再选择路径：

### 普通 PRD

普通 PRD 只执行一次 `writing`，随后直接写完整 PRD：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass writing
```

上下文规则由 `$BUNDLE/contracts/context-loading.manifest.json` 清单装载；`writing` 已包含 PRD 边界、结构、动作、名词、版本和写作内自检所需规范。示例只在确实命中特定写作难点时显式追加，不默认全量加载。

### 超大型 PRD

只有在完整 Design、规则和目标 PRD 无法稳定同时保留，或一次写作已出现截断、重复、冲突、遗漏趋势时，才判定为超大型。可以按 Design 已定义的业务模块生成内部草稿：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass module --card <scene-key> --example <example-key>
```

`module` 只用于超大型 PRD；模块边界必须来自 Design 业务模块，不按页数、字段数或固定字数机械切片。模块草稿只写入 `.workflow/runtime/context/prd/` 下的临时位置，不进入 `output/prd/`，不成为事实源。每个模块同时携带当前模块事实和全局共享事实：目标与范围、角色、状态、权限、数据范围、共享字段、跨模块规则、系统边界、事实源、同步责任及 Design 待确认项。主 Agent 最终只写入一次完整 `output/prd/prd.md`，统一名词、编号、字段表、跨模块规则和重复内容；最终检查只针对完整 PRD 运行一次。

`context-budget.py` 仅是按需容量参考，不是普通 PRD 的固定前置步骤，不自动决定是否分批：

```text
python $BUNDLE/scripts/python/context-budget.py --bundle-root $BUNDLE --project-root . --stage prd --pass writing --input output/design/design.md --json
```

## 写作规则与写作内自检

直接根据 Design 生成 `output/prd/prd.md`，同时生成 `output/prd/decision-notes.md`。不要先输出独立覆盖清单或中间验收文件。

承接允许调整章节顺序、合并重复事实、把抽象规则放到使用场景；不允许删除影响研发或测试理解的事实，不允许补造页面、字段、角色、状态、权限、枚举、默认值、异常或范围。Design 待确认项必须仍标为待确认。Prototype 与 Design 不一致时以 Design 为准，并在决策记录中说明处理。

展示 PRD 前，在同一写作动作内完成自检并直接修正：

1. Design 每个业务模块是否在 PRD 中有准确落点；
2. Design 的角色职责、数据范围、敏感操作与职责分离是否就近承接（放大模块开头或涉及动作正文），不集中到全局章节；
3. Design 的核心业务对象及关系是否融入对应大模块开头职责段落（不单独起标题），跨模块关联写明指向模块；
4. Design 关键业务闭环的详细分阶段动作与异常补偿是否就近放对应小模块页面动作正文；
5. Design 外部协作与异常是否就近放涉及的小模块或大模块；
6. 状态含义与流程图是否位于对应小模块层，状态机表是否留在小模块末尾并与流程图就近；状态、转换条件和限制是否准确；
7. 每个 Design 字段是否归位到对应大模块字段定义表（页面展示、输入、查询筛选、动作依赖或系统内部字段说明），字段表覆盖大模块全部实体；
8. 每个核心动作是否写清前置条件、输入与校验、成功/失败结果、状态或数据副作用；
9. 跨模块共享规则、名词、编号、业务对象速览和字段表是否前后一致；
10. Design 待确认项是否仍保持待确认；
11. 是否出现 Design 未授权的新页面、新字段、新角色、新状态、新权限或新流程。
12. 强动作（新建/删除/调整/提交审批/停用等）是否显式写明执行角色，不靠模块权限规则反推；列表页操作列按钮是否按角色×状态展开可见性与可点性，无笼统“按权限显示”。

阅读质量按十项标准自检：标签式正文、动作流水账、表格过多、页面编号重复、跨节引用、机读字段泄漏、AI 痕迹、空占位符、名词说明缺失、状态含义和流程图层级错误、字段表不符合七列结构。正文应自然连贯；字段、权限、状态、版本等天然结构才使用表格；字段表统一为“字段、类型、必填、取值约束、默认值、业务来源、说明”七列。

`decision-notes.md` 只记录 Design 已有待确认项、表达取舍、未擅自拍板的高影响未知，以及 Prototype 与 Design 冲突时以 Design 为准的处理。它不是事实源、不是通过证明；没有内容时写“无”。

## 最终检查与结果处理

PRD 写入后按顺序运行：

```text
python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .
```

`prd-style-lint.py`：确定性阅读问题返回 `1`；只有 warning/info 返回 `0`；文件不存在或程序无法运行返回 `2`。所有 error 必须修复；warning/info 必须逐项阅读，确认是真问题就修复，确认是误报才保留。不生成永久检查报告或回执。

`prd-consistency-check.py` 保留分类输出：

- `deterministic_conflict`：明确幻觉、字段/枚举/属性冲突、权限反转等，返回 `1`，阻断交付并修复；必要时回到 Design。
- `possible_omission`：可能遗漏或解析不到落点，返回 `0`，必须由 AI 对照 Design 判断是遗漏还是等价表达。
- `needs_semantic_judgment`：需要语义判断，返回 `0`，由 AI 判断；高影响且仍无法判断时停止并询问用户。
- `ok`：返回 `0`，仍需人工阅读最终 `prd.md`。
- 致命运行错误：返回 `2`，停止并修复输入或运行问题。

不得只看退出码 `0` 就宣布 PRD 一致。任何涉及核心流程、角色权限、数据范围、关键状态、系统边界、产品范围或核心字段含义的未知，不能用“合理默认”或工具推断替用户拍板。

## 输出与停止边界

写入：

- `output/prd/prd.md`：最终人读 PRD；
- `output/prd/decision-notes.md`：轻量决策记录；
- `.workflow/status.json`：更新 `current_stage` 为 `prd`，登记 `artifacts.prd` 为 `output/prd/prd.md`。

最终交付前必须直接阅读真实 `prd.md`，确认内容完整、事实一致、阅读质量可接受。不要自动执行 PRD Review，不自动推进 Prototype，不自动修改 Design 确认。Design 缺失、确认失效、输入不可解析或高影响事实缺失时停止并报告，不用补丁掩盖问题。
