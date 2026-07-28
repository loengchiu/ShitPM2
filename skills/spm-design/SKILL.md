---
name: spm-design
description: "设计阶段——ShitPM：同时承担 产品定义 和唯一 Design 基线。用于用户说开始设计、做设计或进入设计时。首次生成必须完成业务流程、角色权限、数据范围、状态转换、模块边界、跨系统责任、异常路径和方案权衡；高影响问题不能推迟给 PRD、Prototype 或 Review。"
---

## 路径与资源

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:`，记为 `$BUNDLE`。bundle 资源使用 `$BUNDLE/`，`.workflow/` 和 `output/` 使用当前项目根目录。

流程开始时输出模型建议：默认使用深度推理模型；只有业务确实简单、输入完整且不需要方案权衡时才使用轻量模型；无法判断时使用深度推理模型。

## 模式选择

本 Skill 只提供两种模式：**简单模式**和**完整模式**。模式必须由用户选择。

- 用户已明确模式：直接采用，不再次询问，不自动升级或降级。
- 用户未明确模式：只询问一次“本次使用简单模式还是完整模式？”并说明简单模式完成最小业务闭环、完整模式完成 ABC 分析和一致性挑战。未获得选择前不正式写入 Design。
- 不根据需求关键词、文件数量、历史产物、模型判断或复杂度评分自动选择模式。
- Align 可选；没有 Align 或 `status.json` 也可以直接进入 Design。

## 职责与事实源

`spm-design` 同时承担 **产品定义** 和 **Design 基线**。

- Design 是唯一产品事实源；用户确认后的 `output/design/design.md` 是 PRD 和 Prototype 的共同基线。
- 首次生成承担完整责任，不把高影响问题推迟给 PRD、Prototype 或 Review。
- 影响下游的未决事实必须在 `design.md` 中显式标记“待确认”，不能只写在 决策记录 中。
- Align 只是可选输入参考；没有 Align、没有 `status.json` 的空项目也必须能直接进入 Design。

## 运行时上下文装载

规范性规则不再按文件列表全文装载，而由 `$BUNDLE/contracts/context-loading.manifest.json` 编译为分阶段上下文包。规则原文仍是唯一权威来源，运行包只用于当前执行、校验和审计。
执行前可用 `context-budget.py` 对当前运行包和业务输入做保守体量检查；该检查默认只报告，不替主 Agent 选择模式或模块。需要确定性拒绝超限时，显式传入 `--max-tokens <n> --fail-on-budget`。

### D0：预检与分析包

先读取项目状态、`output/align/align.md`（如存在）、用户原始需求和现有 `output/design/design.md`，再按用户选择生成分析包：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage design --mode <simple|full> --pass analysis
```
先用同一选择执行一次预算预检（默认只报告，不设未经用户确认的硬上限）：

```text
python $BUNDLE/scripts/python/context-budget.py --bundle-root $BUNDLE --project-root . --stage design --mode <simple|full> --pass analysis --json
```

未指定模式时仍只询问一次；不能用装载器或文件数量替用户选择模式。分析包只包含 `Core` 和当前 `Mode`，不包含写作规则、示例和成品质量标准。

### D1：适用性与专项卡

在分析包中逐项判断流程、状态、页面/模块、字段、权限、跨系统等场景是否适用，创建仅用于运行时的 `.workflow/runtime/context/design/applicability.json`。状态只能是 `applicable`、`not_applicable` 或 `unknown`；`unknown` 按保守策略装载对应场景卡。然后生成挑战包：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage design --mode <simple|full> --pass challenge --applicability-json .workflow/runtime/context/design/applicability.json
```

缺少适用性键、manifest、来源文件或章节标记时停止，不凭模型记忆补规则。

### D2-D4：写作与生成内审查包

写作和成品审查使用新的干净上下文，不携带完整历史对话。写作包只加载分析/挑战交接结果、适用场景卡、写作规则、模板和决策记录模板：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage design --mode <simple|full> --pass writing --applicability-json .workflow/runtime/context/design/applicability.json
```

生成内成品审查重新建立上下文，只加载 Design 草稿、原始证据、适用场景卡和生成自审标准：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage design --mode <simple|full> --pass verification --applicability-json .workflow/runtime/context/design/applicability.json
```

旧项目检测到 metadata 时，额外显式装载 `design-compatibility`，不得默认读取。

### 输入事实边界

`.workflow/runtime/context/` 下的 `run.json`、pack、适用性和交接文件只用于执行、导航、校验和审计；不得写入 Design、不得参与 confirmation、不得成为 PRD 或 Prototype 的事实源。最终产品只读取用户材料、可验证证据和确认后的 `output/design/design.md`。

## Sub-agent 边界

默认不启用 Sub-agent。需要独立材料阅读或完整模式挑战时，必须遵守 `$BUNDLE/contracts/subagent-context-contract.md`：Sub-agent 只能输出带来源的事实、缺陷和证据，不能定义共享业务模型、直接修改最终 Design、输出正式 Review verdict 或替代用户确认；主 Agent 负责最终裁决和写入。

## 生成质量门槛

以下内容必须在 Design 中完成或明确标记“待确认”。章节顺序可以调整，但不能省略事实责任。

### 产品定义（6 类）

- 产品目标与非目标。
- 目标用户与使用场景。
- 核心业务流程：关键路径、阶段、角色处理、具体分支和异常路径。
- 数据范围：角色可见数据边界及多级组织架构下的数据范围层级。
- 系统边界与跨系统责任。
- 高影响待确认：影响下游的未决事实必须在 `design.md` 可见。

### Design 基线（7 类）

- 角色定义。
- 模块定义。
- 页面清单。
- 字段定义。
- 页面与字段落点。
- 规则与状态定义。
- 权限定义。

关键动作还必须形成完整产品结果：执行角色与前置条件、影响对象和字段、成功与失败结果、状态及副作用、后续责任和可恢复路径。场景涉及唯一性、时间边界、数据生命周期、文件、导入导出、批量、重复/并发或跨系统时，必须写清对应产品口径；不涉及时不生成空章节。

### 结构和密度规则

- 多级组织架构必须同时说明角色可见范围、页面展示差异、随范围变化的字段以及页面/字段落点差异。
- 字段定义使用 9 列：`字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明`；无值写“—”，枚举列列出完整枚举项，业务来源和业务含义不得省略。
- 有状态流转的实体按 `references/design-state-format.md` 生成状态机表，且状态机表必须 6 列：`状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件`。操作人必须具体到业务角色，限制条件不能留空，终态必须占行；无状态流转的实体必须明确写“无状态机”。
- 业务流程按 `references/design-flow-format.md` 组织；涉及多角色或 3+ 步骤时必须有流程速览、分阶段动作、具体判断条件和异常降级策略。
- 权限按“页面 > 角色 > 字段权限例外”组织，先写默认规则再写例外；字段定义章节不混入权限表。
- 页面与字段落点必须按“页面 > 区域/动作 > 字段”组织。页面清单、字段定义、落点三处互相对齐；用户可见、可编辑、可筛选或页面动作依赖的字段不能放入非页面例外表。纯内部字段进入例外表并说明原因。
- 页面清单、字段定义、页面与字段落点和非页面落点例外均使用结构化表格，优先保证可机读，再润色人读表达。
- 列表默认行为、文件、导入导出、批量、重复提交、并发冲突和跨系统失败只在实际存在时展开；写产品结果和验收口径，不写 API、HTTP 状态码、数据库、锁、队列或加密算法。
- 产品级性能、安全、审计、留存和兼容要求只在会影响方案或验收时写入，并给出可观察口径；不得用“性能良好”“安全可靠”等空话替代。
- 具体写法、正反例和推导方法必须通过 `writing` 或适用场景卡装载，不要凭记忆替代；规范性规则不得由相似度检索决定是否装载。

## 执行流程

1. 判断是首次生成还是修改已有 Design；现有 `design.md` 是当前事实基线。
2. 通过 `analysis` 包完成共同输入整理和模式责任；简单模式完成最小闭环，完整模式完成 A、B、B3、C 和跨层挑战。
3. 通过适用性文件选择专项卡；挑战必须在首次写入前完成。完整模式可由独立 Challenger 提供缺陷和证据，但主 Agent 负责统一业务模型和最终裁决。
4. 通过 `writing` 包生成或局部修改 `output/design/design.md`，同时生成 `output/design/decision-notes.md`。最终按业务闭环组织，不按 A/B/C 过程写目录，不写 metadata、调试字段、内部路径或 AI 运行痕迹。
5. 通过 `verification` 包在新的干净上下文中完成生成内成品审查；发现可修复问题回到写作，发现高影响未决事实则写入 Design 的“待确认”或停止请求用户决定。
6. 运行适用的确定性检查。检查器失败、解析失败或发现可证明结构错误时先修复，不推给 Review；本 Skill 不自动执行 Review，也不自动确认 Design。
7. 创建或更新 `.workflow/status.json`：`current_stage=design`，`artifacts.design=output/design/design.md`；不自动创建或更新 Design confirmation。

## 模式输出差异

- 简单模式输出最小闭环；不生成与需求无关的干系人地图、完整 ABC 中间分析、空章节或虚构状态机。
- 完整模式的 A/B/B3/C 和跨层挑战必须影响最终事实、待确认项或验收；ABC 过程本身不出现在最终文档。
- 两种模式都只交付人类可读 `design.md` 和审计用 `decision-notes.md`。

## 输出、确认与停止

写入：

- `output/design/design.md`：包含 Design 基线 7 类和 产品定义 6 类。
- `output/design/decision-notes.md`：四类审计记录。
- `.workflow/status.json`：导航状态和产物路径。

完成后明确告知：Design 已生成或修改；用户显式确认后才能生成 PRD 或 Prototype；确认命令为：

```text
python $BUNDLE/scripts/python/design-confirmation.py --project-root . confirm
```

满足以下条件才报告完成：

1. Design 基线 7 类和 产品定义 6 类均存在，或明确标记了真实待确认项。
2. 产品目标、非目标、用户、核心流程、数据范围、系统边界和高影响待确认没有静默缺口。
3. 页面清单、字段定义和页面与字段落点互相对齐。
4. 关键动作的条件、结果、状态副作用、数据变化、失败恢复和验收能够互相解释；实际存在的唯一性、时间、生命周期、重复/并发和跨系统问题已有产品口径。
5. `decision-notes.md` 已生成，确定性检查已完成。

## 失败与禁止事项

- 高影响问题无法判断：在 `design.md` 标记“待确认”，在 决策记录 记录原因；不能推迟给下游。
- 状态机检查失败：先修复 Design，不把问题交给 Review。
- 参考文件缺失：报告路径；仅在明确允许降级时跳过，不能凭记忆生成完整规则。
- 不写研发级页面正文、不写高保真视觉表达、不执行 Review、不自动推进阶段。
- 不重新定义已确认范围，不静默合并新材料，不把 Prototype 表现问题提升为业务事实。
- 不自动写 confirmation、不要求 Align 存在、不要求 metadata、不要求 Review 先通过、不要求模型输出思维过程。

旧版 metadata 规则只按 `$BUNDLE/contracts/metadata-anchor-rules.md` 读取；新主流程不生成 metadata，Design 正文不得出现稳定 ID。
