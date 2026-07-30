# PRD Skill 极简化：执行与验收方案

> 日期：2026-07-30  
> 交付对象：执行 AI  
> 状态：已决策，可直接执行  
> 前置方案：`docs/plans/2026-07-30-design-skill-radical-simplification-execution-plan.md`
>
> 本文只规定 PRD 阶段的精简与质量保护。若旧 PRD 流程、旧测试或历史方案与本文冲突，以本文为执行依据。不要把被删除的 `plan`、`integration`、`verification` 阶段改名后重新引入，也不要新增综合门禁、验证回执或检查 JSON。

## 1. 目标与已拍板决策

### 1.1 PRD 只有两个质量维度

PRD 的质量目标收敛为两类，其中内容质量包含两个不可拆开的要求：

1. **内容质量**
   - 完整承接：Design 已确定的内容必须在 PRD 中有准确、可实施的落点；
   - 事实一致：PRD 不得偏离 Design，不得增加 Design 未授权的产品事实。
2. **阅读质量**
   - PRD 必须适合产品、研发、测试直接阅读和评审；
   - 下文列出的十类阅读问题均属于正式质量标准，不是可选偏好。

除此之外，不以任务数量、中间文件数量、检查回执、结构 Schema 通过率或脚本退出码数量评价 PRD 质量。

### 1.2 要解决的问题

当前 `spm-prd` 把“写出正确 PRD”拆成了多轮重复证明：

```text
plan
  ↓
module
  ↓
integration
  ↓
verification
  ↓
prd-style-lint.py
  ↓
prd-consistency-check.py
```

同时还存在：

- 固定运行 `context-budget.py`；
- 可选读取 Prototype 并生成结构提取结果；
- 首次写入前建立独立承接矩阵；
- 每个模块自检、全局整合检查、verification 再检查、最终脚本继续检查；
- `prd-consistency-check.py` 将明确冲突、可能遗漏、需要语义判断全部返回同一种非零退出码；
- 工具结果容易被误当成语义质量结论，而不是 AI 的辅助线索。

这套流程的问题不是“检查器数量多”本身，而是同一内容责任被重复拆成程序阶段，且不确定结果被错误升级为硬门禁。它增加上下文消耗和执行复杂度，却不能替代 AI 对 Design 与 PRD 的语义判断。

### 1.3 最终目标流程

```text
检查 Design confirmation
  ↓
读取确认版 Design
  ↓
判断普通 PRD / 超大型 PRD
  ↓
生成 prd.md 与 decision-notes.md
  ↓
在同一写作动作内完成内容承接和事实一致性自检，并直接修正
  ↓
运行 prd-style-lint.py
  ↓
运行 prd-consistency-check.py
  ↓
修正确认存在的问题；高影响未知仍无法判断时询问用户
  ↓
交付最终 PRD
```

普通 PRD 不拆分阶段。超大型 PRD 只允许为解决上下文容量按业务模块分批，不增加独立规划、整合审查或验证阶段。

### 1.4 已拍板原则

1. `output/design/design.md` 是 PRD 唯一产品事实源。
2. `output/prd/prd.md` 是 PRD 最终交付物，不是新的产品事实源。
3. PRD 写作的核心责任是完整承接和准确表达 Design，不重新做一轮产品定义。
4. 内容承接自检与 PRD 生成合并，发现问题在同一写作动作内直接修正。
5. 保留 `prd-style-lint.py`，因为十类阅读问题是明确验收目标。
6. 保留 `prd-consistency-check.py`，但只有明确事实冲突和明确幻觉属于程序阻断。
7. “可能遗漏”和“需要语义判断”只提供线索，由 AI 对照 Design 判断；不能因解析器不确定直接阻断。
8. 涉及核心流程、角色权限、数据范围、关键状态、系统边界或范围边界的高影响事实仍无法确认时，停止并询问用户或回到 Design。
9. 超大型 PRD 的模块拆分只解决上下文容量，不产生新的事实源、检查回执或结构门禁。
10. 最终质量必须查看真实生成的 `prd.md`，不能只依赖脚本退出码。

## 2. 保留、删除与暂不处理边界

### 2.1 必须保留

#### Design 确认检查

PRD 开始前继续直接运行：

```powershell
python $BUNDLE/scripts/python/design-confirmation.py --project-root . check
```

它只证明用户确认仍绑定当前 `design.md`，不证明 Design 或 PRD 的语义质量。

#### `prd-style-lint.py`

保留十类可机械识别的阅读质量检查。它的价值是直接发现最终 PRD 中的阅读问题，而不是证明某个中间步骤执行过。

#### `prd-consistency-check.py`

保留 Design 与 PRD 的确定性比对能力，包括明确幻觉、明确字段冲突、枚举冲突、权限反转等。不得把解析器无法确定的语义直接当成产品事实错误。

#### `output/prd/decision-notes.md`

继续保留为轻量决策记录，仅记录：

- Design 已有待确认项；
- 写作中的表达取舍；
- 发现但未擅自拍板的高影响未知；
- Prototype 与 Design 不一致时“以 Design 为准”的处理。

它不是事实源、不是承接矩阵、不是通过证明，也不能为 PRD 偏离 Design 提供免责理由。不存在内容时写“无”。

#### 业务模块分批能力

仅在超大型 PRD 中保留 `module` pass。模块边界必须来自 Design 已定义的业务模块，不按页面数、字段数或固定字数机械切片。

#### `context-budget.py`

保留为按需估算工具，不作为普通 PRD 固定前置步骤，不设置统一硬阈值，不用它自动决定业务模块边界。

### 2.2 从 PRD 主流程删除或合并

删除或合并以下行为：

- 独立 `plan` pass；
- 独立 `integration` pass；
- 独立 `verification` pass；
- 固定执行上下文预算预检；
- PRD 阶段的 Prototype 结构提取；
- 首次写入前必须输出承接矩阵或覆盖结论；
- 每批一次、整合一次、verification 一次、脚本再一次的重复检查链；
- 检查报告、检查回执、最终签名、结果哈希链；
- 把检查脚本输出包装成新的统一门禁；
- 为证明分批正确而新增模块 Schema、模块索引或模块验证角色。

承接矩阵中的有效思考责任不得删除，应收回 `spm-prd` 的写作内自检清单，但不输出独立矩阵文件。

### 2.3 本次不删除的文件

以下文件即使从 PRD 主流程移除，也不因本方案直接删除：

- `scripts/python/context-budget.py`
- `scripts/python/prototype-structure.py`
- `scripts/python/stage-prep.py`
- `scripts/python/design-index.py`
- `scripts/python/context-pack.py`

原因：它们可能仍有其他阶段、导航或测试消费者。本次只清理 PRD 活动流程中的调用和错误依赖，不扩大为全仓库工具重构。

### 2.4 本次不做的事

- 不重写 `prd-consistency-check.py` 的全部解析逻辑；
- 不把 `stage-prep.py` 的 Design 元数据逻辑迁移到新公共模块；
- 不创建 PRD 编排器；
- 不创建大型 PRD 专用数据库、向量索引或新的中间协议；
- 不修改 Prototype 阶段的产品行为；
- 不借机重写所有 PRD 参考文档；
- 不把独立 PRD Review 合并进 PRD 生成流程。

## 3. 目标上下文结构

### 3.1 PRD pass 只保留两种

`contracts/context-loading.manifest.json` 中 PRD pass 收敛为：

| pass | 使用范围 | 责任 |
|---|---|---|
| `writing` | 所有 PRD | 完整 PRD 写作、全局语义保持、写作内自检和最终整合 |
| `module` | 仅超大型 PRD | 按 Design 业务模块生成受边界约束的内部草稿 |

删除：

- `plan`
- `integration`
- `verification`

`writing` 建议固定装载以下规范性 pack：

- `prd-core`
- `prd-writing-structure`
- `prd-writing-action`
- `prd-writing-glossary`
- `prd-writing-versioning`
- `prd-verification`

其中 `prd-verification` 只作为写作动作内的自检清单，不再对应独立 verification pass。保留现有名称即可，不为改名制造无价值改动。

`module` 建议固定装载：

- `prd-core`
- `prd-writing-structure`
- `prd-writing-action`
- `prd-cards`

示例不默认全量装载。确实命中特定写作难点时，显式追加 `prd-examples` 和具体 `--example`；示例永远不是规范性规则。

### 3.2 普通 PRD 的上下文

普通 PRD 只执行一次 `writing`：

```powershell
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass writing
```

随后完整读取 Design，直接生成完整 PRD，在同一动作内完成内容和阅读质量自检。

不得因为“未来可能很大”默认进入模块分批。能在当前上下文中稳定处理完整 Design 和 PRD 时，就属于普通 PRD。

### 3.3 超大型 PRD 的判定

不设置“10 页”“50 个字段”或固定 token 数作为硬门槛。满足以下任一实际风险时，主 Agent 可以判定为超大型 PRD：

- 完整 Design、写作规则和目标 PRD 无法稳定同时留在当前上下文；
- 业务模块很多，一次生成明显容易遗忘前文中的角色、状态、权限或共享字段；
- 单次写作已出现截断、重复章节、前后冲突或遗漏趋势；
- `context-budget.py` 的估算提示上下文余量不足。

`context-budget.py` 只提供容量参考。最终是否分批由主 Agent 基于真实材料判断，不能由脚本按页数或字段数自动切分。

### 3.4 超大型 PRD 的模块上下文包

每个模块草稿必须同时获得两类输入。

**当前模块事实**：

- 当前业务模块在 Design 中的完整内容；
- 当前模块的页面、动作、字段、规则、异常和验收要求；
- 当前模块与上下游模块的接口关系。

**全局共享事实**：

- 全局目标与范围边界；
- 全局角色；
- 全局状态及跨模块状态约束；
- 全局权限和数据范围；
- 跨模块共享对象与字段；
- 跨模块业务规则；
- 系统边界、事实源和同步方向；
- Design 中仍存在的待确认项。

全局共享事实可以是主 Agent 在当前执行中的简洁工作摘要，但必须可回溯到 Design。不得把摘要保存为新的产品基线，也不得让模块写作者只读摘要而完全失去当前模块的 Design 原文。

### 3.5 超大型 PRD 的写作顺序

```text
扫描 Design 的目录、全局规则和业务模块边界
  ↓
形成当前执行使用的全局共享事实摘要
  ↓
按业务模块生成内部草稿
  ↓
主 Agent 使用 writing 上下文统一组织 prd.md
  ↓
主 Agent 完成一次全局承接与一致性自检并直接修正
  ↓
运行最终两个检查脚本
```

要求：

1. 模块草稿只解决上下文容量，不是最终交付物；
2. 模块草稿不定义 Design 没有的全局事实；
3. 主 Agent 负责统一名词、编号、字段表、跨模块规则和重复内容；
4. 不增加独立模块验证 Agent；
5. 不为每个模块运行两个最终检查脚本；
6. 不为每个模块生成检查回执；
7. 最终只对完整 `output/prd/prd.md` 运行全局检查；
8. 临时草稿若落盘，只能放在 `.workflow/runtime/context/prd/` 下，不进入 `output/prd/`，不要求稳定 Schema，不作为后续事实输入。

## 4. 内容完整承接规则

### 4.1 “完整承接”的含义

完整承接不是逐句复制 Design，也不是要求 PRD 重复所有分析过程。它要求 Design 中已经确定、会影响研发或测试理解的产品事实，在 PRD 中有明确落点。

至少覆盖以下内容类别，但只在 Design 实际存在时承接：

- 产品目标与范围边界；
- 用户、角色和职责；
- 核心业务场景与流程；
- 业务对象、字段、来源、约束和生命周期；
- 页面或功能模块；
- 用户动作、前置条件、成功结果和失败结果；
- 状态、状态变化和状态限制；
- 权限与数据范围；
- 业务规则、校验和例外；
- 列表、查询、筛选、排序、分页等 Design 已确认规则；
- 文件、导入导出、批量、重复提交和并发等 Design 已确认规则；
- 跨系统边界、事实源、同步方向、失败结果和责任归属；
- Design 已确定的产品级非功能要求与验收条件；
- Design 中明确保留的待确认项。

### 4.2 承接允许转换表达，不允许改变语义

允许：

- 将 Design 的业务模型转换为页面、动作、字段和规则说明；
- 合并 Design 中重复出现的同一事实；
- 将抽象规则放到最接近使用场景的位置；
- 为提高可读性调整章节顺序；
- 将同义表述统一为一个正式名词。

不允许：

- 删除看似“实现细节”但实际影响业务行为的 Design 事实；
- 为让 PRD 看起来完整而补造默认值、枚举、权限、状态或异常处理；
- 把 Design 的待确认项写成确定结论；
- 将 Design 的范围外事项改成当前需求；
- 用 Prototype 或历史 PRD 覆盖确认版 Design；
- 因检查器报告遗漏就直接补写未经语义确认的事实。

### 4.3 写作内承接自检

生成者在展示 PRD 前，使用同一写作动作完成以下自检并直接修正：

1. Design 的每个业务模块是否在 PRD 中有落点；
2. 每个角色、权限和数据范围是否被准确表达；
3. 每个状态、转换条件和限制是否被准确表达；
4. 每个 Design 字段是否进入合适的页面展示、页面输入、查询筛选、动作依赖或系统内部字段说明；
5. 每个核心动作是否说明必要的前置条件、输入与校验、成功/失败结果、状态或数据副作用；
6. 跨模块共享规则是否前后一致；
7. Design 中的待确认项是否仍保持待确认；
8. 是否出现 Design 未授权的新页面、新字段、新角色、新状态、新权限或新流程。

该自检只形成最终修正后的 PRD，不输出承接矩阵、覆盖 JSON 或自检报告。

## 5. 事实一致性与幻觉处理

### 5.1 事实来源优先级

PRD 生成时的事实优先级固定为：

```text
当前已确认的 output/design/design.md
  > 其他参考材料
  > 历史 PRD
  > Prototype
  > AI 推测
```

其他材料只能帮助理解，不能覆盖确认版 Design。

### 5.2 结果分类与处理

`prd-consistency-check.py` 的输出继续保留三类结果，但阻断语义必须区分：

| 分类 | 例子 | 程序退出 | AI 处理 |
|---|---|---:|---|
| `deterministic_conflict` | 幻觉字段、枚举明确冲突、权限反转、Design 无此页面/角色/状态 | `1` | 阻断交付，直接修复；若必须新增事实则回到 Design |
| `possible_omission` | 名称变体、解析不到落点、可能缺字段或模块 | `0` | AI 对照 Design 判断；确认遗漏则修复，确认等价表达则不改 |
| `needs_semantic_judgment` | 字段类型等价性、复合字段表达、语义合并 | `0` | AI 做语义判断；无法判断且高影响时询问用户 |
| `ok` | 未发现问题 | `0` | 继续交付前人工阅读 |
| 致命运行错误 | 文件缺失、内容不可解析、程序异常 | `2` | 停止并修复运行问题 |

不得只看退出码 `0` 就宣布内容一致。AI 必须阅读分类输出，逐项判断 `possible_omission` 和 `needs_semantic_judgment`。

### 5.3 高影响未知的停止条件

以下事实如 Design 没有确定，PRD 不得自行补全：

- 核心流程走向；
- 角色权限；
- 数据可见范围；
- 关键状态及状态转换；
- 系统边界、事实源或同步责任；
- 会改变产品范围的页面、模块或能力；
- 会改变数据含义的核心字段、枚举或默认值。

处理顺序：

1. 检查 Design 是否已有答案但 PRD 未承接；
2. 检查是否只是表达等价或解析器误报；
3. 若 Design 确实缺失且会改变实现，停止写作；
4. 合并成少量阻断问题询问用户，或提示回到 Design 修复；
5. 不用“合理默认”“通常做法”或检查器推断替用户拍板。

## 6. 阅读质量十项标准

以下十项是最终 PRD 的正式验收标准。`prd-style-lint.py` 负责发现其中可机械识别的线索，AI 负责判断和最终修正。

### 6.1 标签式正文

**问题**：使用“**前置条件：**”“**关键动作：**”“**成功结果：**”等标签连续拼接正文，使页面规格像模板填空。

**通过标准**：页面和动作说明以自然、连贯的规格语言表达；仅在天然列表或定义项中使用标签，不用标签代替正文组织。

### 6.2 动作流水账

**问题**：用连续短步骤记录点击顺序，却没有说明展示规则、业务约束、状态变化、失败结果和恢复方式。

**通过标准**：按业务意图组织动作说明；只在顺序本身不可替代时使用步骤，且同时写清关键规则和结果。

### 6.3 表格过多

**问题**：把页面说明、交互逻辑和异常规则全部塞进表格，PRD 退化为表格集合。

**通过标准**：正文承担业务说明；表格只用于字段、权限、状态、版本记录等天然映射结构。表格不能替代对关键行为的解释。

### 6.4 页面编号重复

**问题**：同一个页面编号指向多个页面，或同一页面被无意义地重复定义。

**通过标准**：需要页面编号时保持唯一且稳定；不需要编号时不为满足模板强行编号。

### 6.5 跨节引用

**问题**：大量使用“见 3.2”“同上”“参考前文”，迫使读者频繁跳转，且容易在修改后失效。

**通过标准**：关键规则尽量在使用位置就地说明；确实需要共享规则时写简洁摘要并指向唯一权威章节，不用跨节引用逃避当前说明。

### 6.6 机读字段泄漏

**问题**：稳定 ID、内部索引键、检查器字段或运行时元数据进入人读正文。

**通过标准**：PRD 只展示业务需要的标识。内部机读字段留在运行时数据或工具输出中，不进入正文。

### 6.7 AI 痕迹

**问题**：出现“作为 AI”“根据我的理解”“建议进一步确认”等对话式、推测式或自我说明语言。

**通过标准**：只保留正式产品规格、已知决策和明确待确认项，不出现生成过程说明或模型口吻。

### 6.8 占位符

**问题**：出现“待补充”“TBD”“按需配置”“后续确认”等没有责任人和业务含义的空占位。

**通过标准**：能由 Design 确定的内容写成明确事实；Design 中真实未决事项明确标记为待确认并说明影响，不能用空话掩盖缺失。

### 6.9 名词说明缺失

**问题**：业务术语、角色名、状态名或缩写直接使用，读者无法确认其唯一含义。

**通过标准**：PRD 包含名词说明；只收录真实使用且容易歧义的名词，定义与 Design 一致，不为凑章节写常识词。

### 6.10 字段表结构不合格

**问题**：字段表缺少研发交付所需信息，或把所有属性压缩进“说明”列。

**通过标准**：字段表统一提供：

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|

Design 未定义且业务上明确不适用的属性写“无”或“不适用”；如果缺失属性会改变实现，停止并回到 Design，不得用“未定义”“待补充”占位，也不能自行补造。系统内部字段也应说明来源与用途，但不虚构页面落点。

## 7. 两个检查脚本的最终职责

### 7.1 `prd-style-lint.py`

**保留职责**：

- 检查十类阅读质量问题；
- 输出具体位置、问题类型和修正建议；
- 对确定性问题返回非零退出码；
- 对存在误报可能的线索使用 warning 或 info，由 AI 判断。

**目标退出语义**：

| 结果 | 退出码 |
|---|---:|
| 无 error，可有待 AI 判断的 warning/info | `0` |
| 至少一个确定性 error | `1` |
| 文件不存在或程序无法运行 | `2` |

**交付规则**：

- 所有 error 必须修复后才能交付；
- 所有 warning/info 必须由 AI 阅读，确认是真问题则修复；
- 允许保留确认后的误报，但不能以“脚本只是警告”为由跳过判断；
- 不生成永久检查报告或回执；默认控制台输出即可。

**不得做**：

- 不把所有 warning 一律升级为硬错误；
- 不把语义可读性完全交给正则判断；
- 不为每一条写作偏好新增规则编号；
- 不扩展为通用 Markdown 风格平台。

### 7.2 `prd-consistency-check.py`

**保留职责**：

- 读取 `output/design/design.md` 和 `output/prd/prd.md`；
- 识别可稳定判断的幻觉和明确事实冲突；
- 提示可能遗漏和需要语义判断的项目；
- 输出分类结果供 AI 处理。

**本次最小改动**：

1. 保留现有三类 classification；
2. 保留 `exit_reason`，但修改进程退出逻辑；
3. 只有 `deterministic_conflict` 返回 `1`；
4. `possible_omission` 和 `needs_semantic_judgment` 返回 `0`；
5. 致命运行错误继续返回 `2`；
6. 修改帮助、注释和测试，避免调用方将所有非 `ok` 结果都视为程序失败；
7. 不趁机重写 1591 行解析器；
8. 不迁移 `stage-prep.py` 或 Design 索引逻辑；
9. 不创建新的综合判定字段或独立结果文件作为门禁。

**注意**：退出码收窄不代表忽略遗漏。`spm-prd` 必须明确要求 AI 阅读 JSON 输出并逐项判断非阻断结果。

## 8. 文件级执行任务

### 任务 A：重写 `spm-prd` 主流程

**文件**：

- `skills/spm-prd/SKILL.md`

**改动**：

1. 将职责开头收敛为内容完整承接、事实一致和阅读质量；
2. 保留 Design confirmation 检查；
3. 删除 P0-P4 的阶段式描述；
4. 删除固定 `plan`、`integration`、`verification` 调用；
5. 普通 PRD 只调用 `writing` pass；
6. 超大型 PRD 才调用 `module` pass，并由主 Agent 最终统一写入 `prd.md`；
7. 删除 Prototype 结构提取命令及其输入要求；
8. 将 `context-budget.py` 改为按需工具；
9. 删除“首次写入前必须建立并输出承接矩阵”的要求；
10. 将承接责任改写为写作内自检清单；
11. 保留 `decision-notes.md`，明确其非事实源、非通过证明；
12. 明确两个脚本的执行顺序和分类处理；
13. 明确只有高影响未知仍无法判断时才询问用户；
14. 明确最终交付必须人工阅读真实 `prd.md`；
15. 不自动执行 PRD Review，不自动推进 Prototype。

**验证**：

- Skill 中不存在 `--pass plan`、`--pass integration`、`--pass verification`；
- Skill 中不存在 `prototype-structure.py`；
- Skill 中普通 PRD 只走 `writing`；
- Skill 中 `module` 明确只用于超大型 PRD；
- Skill 中没有承接矩阵文件、检查报告或回执要求。

### 任务 B：收敛 PRD 上下文清单

**文件**：

- `contracts/context-loading.manifest.json`

**改动**：

1. PRD passes 只保留 `writing` 和 `module`；
2. `writing` 装载完整规范和写作内自检所需 pack；
3. `module` 只装载模块写作所需 pack；
4. 示例改为按命中项显式追加，不默认全量塞入普通写作上下文；
5. 删除 PRD 的 `plan`、`integration`、`verification` pass；
6. 删除 `module-verifier` 角色；
7. `prd-module-writer` 只允许 `module`；
8. 删除 `material-reader` 对 PRD `plan` 的授权；若没有真实 PRD 消费者，不为其新增 `writing` 授权。

**不得改动**：

- Design 阶段现有 pass 和角色，除非另一个已批准方案同时要求；
- pack 的权威来源和章节内容，除非为完成本任务确有必要。

### 任务 C：同步 Sub-agent 契约

**文件**：

- `contracts/subagent-context-contract.md`

**改动**：

1. 删除 Material Reader 的 PRD `plan` 说明；
2. 保留 PRD Module Writer，仅允许 PRD `module`；
3. 删除 Module Verifier；
4. 明确模块写作者只生成受 Design 边界约束的内部草稿；
5. 明确主 Agent 对最终整合、全局一致性和交付负责；
6. 不新增“PRD Planner”“Integration Agent”“Final Verifier”等替代角色。

### 任务 D：移除 PRD 阶段的 Prototype 依赖

**至少修改**：

- `skills/spm-prd/SKILL.md`
- `scripts/python/stage-context.py`

**改动**：

1. 从 PRD 最小读取集合删除 `scripts/python/prototype-structure.py`；
2. 删除 PRD 主流程生成 `.workflow/runtime/context/prd/prototype-structure.json` 的要求；
3. 明确 PRD 不依赖 Prototype 存在；
4. Prototype 与 Design 冲突时始终以 Design 为准。

**暂不删除**：

- `scripts/python/prototype-structure.py`
- 对该脚本本身仍有价值的资源完整性或行为测试。

### 任务 E：收窄一致性检查退出语义

**文件**：

- `scripts/python/prd-consistency-check.py`

**改动**：

1. 按第 7.2 节修改退出码；
2. 保留分类详情；
3. 更新注释和帮助文本；
4. 不改变明确冲突的识别范围；
5. 不把可能遗漏改名包装成新的门禁等级；
6. 不自动修改 PRD；
7. 不根据解析结果补写产品事实。

### 任务 F：校准阅读质量检查

**文件**：

- `scripts/python/prd-style-lint.py`
- `contracts/prd-writing.profile.json`
- `references/prd-writing-rules.md`

**改动**：

1. 确认 STYLE001-STYLE010 分别覆盖十项阅读质量；
2. 修正规则、配置和写作说明之间的明显冲突；
3. 确定性问题用 error；高误报风险线索用 warning/info；
4. 确保字段表标准仍为七列；
5. 明确跨节引用、动作流水账、表格过多不能只靠退出码判断；
6. 删除“生成前后多轮重复检查”的表述，改为写作内自检加最终一次 lint；
7. 不为边缘文风偏好继续新增规则。

### 任务 G：同步文档和用户说明

**按活动引用检查并修改**：

- `README.md`
- `USAGE.md`
- `contracts/*.md`
- `references/*.md`
- 其他活动 Skill 中直接描述 PRD passes 或 PRD 完成语义的文件

PowerShell 中先展开文件列表，不要把通配路径直接传给 `rg`。

**要求**：

- 活动文档只描述 `writing/module`；
- 不再宣称 PRD 必须经过 plan/integration/verification；
- 不再宣称 Prototype 是 PRD 输入；
- 不再把两个脚本的退出码等同于完整语义验收；
- 历史计划、历史报告和归档材料不要求改写。

### 任务 H：更新测试，不保留废弃行为

**现有测试至少检查**：

- `scripts/python/test-context-loading.py`
- `scripts/python/test-resource-integrity.py`
- `scripts/python/test-context-runtime.py`
- `scripts/python/test-anti-hallucination.py`
- `scripts/python/test-design-index.py`

**要求**：

1. 删除对 PRD `plan/integration/verification` 的期望；
2. 删除对 `module-verifier` 的期望；
3. 新增 `writing/module` 的合法装载测试；
4. 保留 `prd-module-writer` 不能越界读取其他 pass 的测试；
5. 不删除 Prototype 结构工具自身仍有价值的测试；
6. 不用模拟回执证明 PRD 内容质量；
7. 行为被删除后同步删除验证旧行为的断言，不为维持测试数量保留废弃流程。

## 9. 新增或改写的针对性测试

### 9.1 `test-prd-style-lint.py`

**建议文件**：

- `scripts/python/test-prd-style-lint.py`

**至少覆盖**：

1. 标签式正文可被识别；
2. 动作流水账可被提示；
3. 表格主导可被提示；
4. 重复页面编号可被识别；
5. 跨节引用可被提示；
6. 机读字段泄漏可被识别；
7. AI 痕迹可被提示；
8. 占位符可被识别；
9. 名词说明缺失可被识别；
10. 七列字段表缺列可被识别；
11. 一个符合要求的完整样本无 error；
12. error 返回 `1`；
13. 只有 warning/info 时返回 `0`；
14. 文件不存在返回 `2`。

测试应验证真实规则行为，不只验证常量或规则编号存在。

### 9.2 `test-prd-consistency-semantics.py`

**建议文件**：

- `scripts/python/test-prd-consistency-semantics.py`

也可以在现有 `test-anti-hallucination.py` 中扩展，但不要重复建立两套同类测试框架。

**至少覆盖**：

1. PRD 新增 Design 不存在的字段：`deterministic_conflict`，退出 `1`；
2. 字段枚举或明确属性与 Design 冲突：退出 `1`；
3. 权限方向反转：退出 `1`；
4. Design 项可能遗漏：保留 `possible_omission`，退出 `0`；
5. 字段类型等价性需要语义判断：保留 `needs_semantic_judgment`，退出 `0`；
6. 完全一致：`ok`，退出 `0`；
7. Design 或 PRD 文件缺失：退出 `2`。

测试不能把“退出 `0`”断言成“语义一定通过”，还要断言分类结果仍被输出。

### 9.3 `test-prd-simplification.py`

**建议文件**：

- `scripts/python/test-prd-simplification.py`

**至少覆盖活动配置和 Skill**：

1. PRD manifest 只存在 `writing/module`；
2. `writing` 含完整写作和自检所需 pack；
3. `module` 仍可合法装载；
4. `plan/integration/verification` 选择被拒绝；
5. `module-verifier` 不再存在；
6. `spm-prd/SKILL.md` 不包含 Prototype 结构提取；
7. `spm-prd/SKILL.md` 不要求承接矩阵产物；
8. `spm-prd/SKILL.md` 不要求检查报告、验证回执或签名；
9. `spm-prd/SKILL.md` 明确普通 PRD 使用 `writing`；
10. `spm-prd/SKILL.md` 明确超大型 PRD 才使用 `module`。

测试只保护目标行为，不绑定整段文案和无关格式。

## 10. 执行顺序

### Phase 1：先改主行为

1. 重写 `skills/spm-prd/SKILL.md`；
2. 把内容质量、事实一致和阅读质量写成唯一主线；
3. 写清普通 PRD 与超大型 PRD 两条路径；
4. 删除重复阶段和 Prototype 依赖。

**阶段验证**：仅通过阅读新 Skill 就能回答“读什么、怎么写、何时分批、检查结果怎么处理、何时问用户”。

### Phase 2：收敛上下文配置

1. 修改 `contracts/context-loading.manifest.json`；
2. 修改 `contracts/subagent-context-contract.md`；
3. 修改 `scripts/python/stage-context.py`；
4. 同步上下文装载测试。

**阶段验证**：普通 PRD 只需 `writing`；超大型 PRD 可额外使用 `module`；旧 pass 不可再调用。

### Phase 3：校准两个最终检查器

1. 修改 `prd-consistency-check.py` 退出语义；
2. 校准 `prd-style-lint.py` 的十项覆盖和严重级别；
3. 同步 profile 与写作规则；
4. 增加针对性测试。

**阶段验证**：明确冲突阻断，不确定结果仍输出但不由程序硬阻断；十项阅读问题都有真实测试。

### Phase 4：清理活动引用

1. 扫描活动 Skill、README、USAGE、contracts、references 和测试；
2. 删除旧 pass 和 Prototype 依赖；
3. 不改历史计划、历史报告、测试夹具原文；
4. 不删除仍有其他消费者的脚本。

### Phase 5：自动化回归与真实 PRD 验收

1. 运行新增测试；
2. 运行受影响的现有测试；
3. 使用简单和复杂真实材料生成最终 PRD；
4. 直接阅读最终 `prd.md`；
5. 发现质量问题优先修 Skill 责任和上下文策略，而不是新增检查器。

## 11. 自动化验收

### 11.1 基础测试

执行 AI 应根据仓库当前测试入口运行全部受影响测试，至少包括：

```powershell
python scripts/python/test-prd-style-lint.py
python scripts/python/test-prd-consistency-semantics.py
python scripts/python/test-prd-simplification.py
python scripts/python/test-context-loading.py
python scripts/python/test-context-runtime.py
python scripts/python/test-resource-integrity.py
python scripts/python/test-anti-hallucination.py
python scripts/python/test-design-index.py
```

如果选择扩展已有测试而不是创建建议文件，执行报告中列出实际测试路径和等价覆盖项。

### 11.2 PRD pass 验收

以下命令应在 `test-fixture` 的临时副本中执行，避免写入基准夹具。

```powershell
$tempProject = Join-Path $env:TEMP ('shitpm-prd-context-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath 'test-fixture' -Destination $tempProject -Recurse
python scripts/python/context-pack.py --bundle-root . --project-root $tempProject --stage prd --pass writing
python scripts/python/context-pack.py --bundle-root . --project-root $tempProject --stage prd --pass module
```

应成功。

以下旧 pass 应失败，并返回清晰的“不存在 pass”错误：

```powershell
python scripts/python/context-pack.py --bundle-root . --project-root $tempProject --stage prd --pass plan
python scripts/python/context-pack.py --bundle-root . --project-root $tempProject --stage prd --pass integration
python scripts/python/context-pack.py --bundle-root . --project-root $tempProject --stage prd --pass verification
```

### 11.3 活动引用扫描

```powershell
$activityFiles = @(
  (Get-ChildItem skills -Recurse -File),
  (Get-ChildItem contracts -Recurse -File),
  (Get-ChildItem references -Recurse -File),
  (Get-ChildItem scripts\python -Filter '*.py' -File),
  (Get-Item README.md),
  (Get-Item USAGE.md)
) | ForEach-Object { $_.FullName }

rg -n -- '--pass (plan|integration|verification)|prototype-structure\.py|module-verifier' $activityFiles
```

验收方式：

- PRD 活动主流程不得再出现旧 pass；
- `prototype-structure.py` 可以作为独立工具或测试对象存在，但不得出现在 PRD Skill 和 PRD 最小读取集合；
- 历史计划、历史报告和测试夹具不在此扫描范围；
- 若活动文件中的命中属于兼容性错误提示或负向测试，执行报告中说明，不为追求零文本命中删除必要测试。

### 11.4 禁止复杂度扫描

```powershell
$prdSkill = 'skills\spm-prd\SKILL.md'
rg -n '检查回执|最终验证回执|机器签名|承接矩阵文件|综合门禁|检查 JSON|结果哈希链' $prdSkill
```

预期：无活动要求。禁止词出现在“不做的事”中不算失败，但不要因此编写脆弱的纯文本零命中测试。

### 11.5 检查脚本退出语义验收

必须使用真实临时 fixture 验证：

| 场景 | style lint | consistency check |
|---|---:|---:|
| 无问题 | `0` | `0` |
| 只有文风 warning/info | `0` | 不适用 |
| 确定性文风 error | `1` | 不适用 |
| 明确幻觉或事实冲突 | 不适用 | `1` |
| 可能遗漏 | 不适用 | `0`，且输出分类 |
| 需要语义判断 | 不适用 | `0`，且输出分类 |
| 输入缺失或致命错误 | `2` | `2` |

## 12. 真实最终 PRD 质量验收

自动化测试只能证明确定性行为。最终验收必须生成并阅读真实 PRD。

### 12.1 场景 A：普通项目

**建议材料**：

- `test-fixture/output/design/design.md`

**验收目标**：

1. 不进入模块分批；
2. Design 的模块、角色、流程、字段、状态和权限均有准确落点；
3. 未新增 Design 没有的产品事实；
4. 十项阅读质量无确认问题；
5. `decision-notes.md` 不被用作事实补丁；
6. 最终 PRD 可供研发与测试直接评审。

### 12.2 场景 B：复杂库存项目

**建议材料**：

- `test-fixture/v2-remediation/calibration/complex-inventory-generated-design.md`
- `test-fixture/v2-remediation/calibration/complex-inventory-shitpm-original-design.md`
- 对应历史 PRD 只作为对照，不作为事实源。

**验收目标**：

1. 主 Agent 能明确判断是否需要业务模块分批，并说明真实容量原因；
2. 分批边界来自 Design 业务模块，不按页面或固定字数拆分；
3. 每个模块都携带全局角色、状态、权限、共享字段和跨模块规则；
4. 最终 PRD 不出现模块间名词漂移、字段重复定义、权限冲突或状态冲突；
5. 最终只运行一次全局 lint 和 consistency check；
6. 可能遗漏由 AI 对照 Design 判断，不因退出码误判失败或通过。

### 12.3 场景 C：反幻觉与高影响未知

在测试副本中构造：

- PRD 新增 Design 不存在的角色、字段或状态；
- PRD 反转一个已有权限；
- Design 缺少一个会改变核心流程的关键决定；
- 同义字段导致解析器报告可能遗漏。

**验收目标**：

1. 明确幻觉和权限反转被阻断并修复；
2. 高影响未知不被 PRD 静默补全；
3. 同义表达由 AI 判断，不机械增加重复字段；
4. 必须询问用户时，问题合并为少量高影响阻断项；
5. 不新增检查器处理这些语义问题。

### 12.4 场景 D：阅读质量

使用包含十类问题的 PRD 测试副本，逐项修复后再生成一次完整 PRD。

**验收目标**：

- 标签式正文已改为自然规格说明；
- 动作不再是点击流水账；
- 表格只保留天然结构；
- 页面编号不重复；
- 关键规则不依赖跨节跳转才能理解；
- 无机读字段泄漏；
- 无 AI 对话痕迹；
- 无空占位符；
- 名词说明完整且不堆常识词；
- 字段表符合七列交付结构；
- 真实阅读体验通过，而不只是 lint 返回 `0`。

## 13. 最终通过标准

必须同时满足以下条件才算完成：

### 13.1 流程精简

- PRD pass 只剩 `writing/module`；
- 普通 PRD 不分批；
- 超大型 PRD 才按业务模块使用 `module`；
- 不再存在独立 plan、integration、verification；
- PRD 不依赖 Prototype；
- 不生成承接矩阵、检查报告、回执或签名。

### 13.2 内容质量

- 抽查的 Design 已确定事实在 PRD 中都有准确落点；
- 未发现 PRD 新增 Design 未授权事实；
- 角色、权限、状态、字段和跨系统规则没有事实偏移；
- 高影响未知被暴露，而不是静默拍板；
- 超大型 PRD 跨模块语义保持一致。

### 13.3 阅读质量

- 十项阅读问题均有检查规则和真实测试；
- 最终真实 PRD 中无确认存在的十类问题；
- 文档可连续阅读，不依赖机读字段或频繁跳转；
- 字段表可直接支持研发、测试评审。

### 13.4 工具语义

- `prd-style-lint.py` 只硬阻断确定性 error；
- `prd-consistency-check.py` 只硬阻断确定性冲突；
- 可能遗漏和语义判断项仍被输出并由 AI 处理；
- 致命运行错误继续失败关闭；
- 没有新增统一检查器或最终门禁。

### 13.5 回归

- 所有新增针对性测试通过；
- 所有受影响现有测试通过；
- 简单和复杂真实 PRD 验收通过；
- 未修改无关阶段行为；
- 未覆盖仓库中已有的其他未提交改动。

## 14. 失败与停止条件

执行过程中遇到以下情况必须停止当前分支并报告，不得用补丁掩盖：

- `design.md` 不存在、不可读或确认失效；
- 当前 PRD 活动行为与本文存在无法兼容的另一份已批准方案；
- 删除旧 pass 会影响未识别的真实运行时消费者；
- 一致性检查结果无法区分确定性冲突与解析不确定，且修改会改变现有检测事实；
- 十项阅读质量中的某项没有可稳定机械识别方式：保留 AI 自检，不为凑覆盖写高误报规则；
- 超大型 Design 无法在不丢失全局事实的情况下分批：停止并说明上下文瓶颈，不创建未经批准的新索引系统；
- 高影响 Design 事实缺失，导致 PRD 无法继续；
- 受影响测试失败且根因不在本次改动范围。

报告时必须区分：

- **事实**：实际文件、调用方、测试结果；
- **判断**：为什么某条规则应保留或删除；
- **未确认**：需要用户决定或另开方案的事项。

## 15. 禁止重新引入的复杂度

执行 AI 不得以“提高可靠性”为由新增：

- PRD Orchestrator；
- PRD Planner Agent；
- Integration Agent；
- Module Verifier；
- Final Verification pass；
- 承接矩阵文件；
- 覆盖率 JSON；
- 检查结果签名；
- 检查回执；
- 综合门禁；
- 新的检查器聚合层；
- 每模块 lint/consistency 门禁；
- 固定 token 硬阈值；
- 按页数、字段数或字数机械拆分；
- 让程序根据解析结果自动补写产品事实。

实施任何新检查或中间结构前，必须先回答：

> 删除它以后，最终 `prd.md` 会具体错在哪里？现有 `spm-prd` 写作内自检为什么无法解决？是否有真实项目反复发生且工具能低误报识别的证据？

无法给出具体答案时，不实施。

## 16. 执行报告要求

执行完成后只提交简洁报告，不生成额外审计文件。报告至少包含：

1. **改动文件**：列出实际修改、删除和新增文件；
2. **流程变化**：说明普通 PRD 和超大型 PRD 的最终路径；
3. **检查语义**：说明两个脚本的最终退出码和 AI 处理方式；
4. **自动化测试**：列出运行命令、通过数和失败项；
5. **真实 PRD 验收**：分别说明普通项目和复杂项目发现、修复的内容问题与阅读问题；
6. **活动引用扫描**：说明旧 pass、Prototype 依赖和废弃角色是否仍有活动消费者；
7. **未处理项**：只列真实遗留，不写“未来可进一步优化”式泛化建议；
8. **工作区保护**：说明未覆盖、回滚或提交其他人的未提交改动。

完成标准不是“所有脚本返回 0”，而是：流程已精简，最终 PRD 完整承接 Design、没有事实幻觉，并且真实阅读质量通过。




