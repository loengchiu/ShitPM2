---
name: spm-design
description: "设计阶段——ShitPM：同时承担产品定义和唯一 Design 基线。只提供简单模式与完整模式；首次生成必须完成适用的业务闭环、角色权限、数据范围、状态、页面、字段、操作、异常和方案权衡，高影响问题不能推迟给 PRD、Prototype 或 Review。"
---

## 1. 定位与资源

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:`，记为 `$BUNDLE`。bundle 资源使用 `$BUNDLE/`，`.workflow/` 和 `output/` 使用当前项目根目录。

`spm-design` 同时承担产品定义和 Design 基线。确认后的 `output/design/design.md` 是 PRD 和 Prototype 的唯一产品事实基线，主要阅读和确认对象是产品经理。Design 不承担数据库、接口、普通技术类型、高保真视觉或完整测试用例说明。

流程开始时可以给出模型建议，但模型建议不是模式选择、质量证明或用户确认的替代品。

## 2. 模式选择

本 Skill 只提供两种模式：**简单模式**和**完整模式**。模式必须由用户选择。

- 用户已明确模式：直接采用，不再次询问；
- 用户未明确模式：只询问一次“本次使用简单模式还是完整模式？”，并说明两者差异；
- 不根据文件数量、关键词、历史产物、模型判断或复杂度评分自动升级、降级或静默选择；
- Align 是可选输入；没有 Align、`status.json` 或旧版 metadata，也可以直接进入 Design；
- 两种模式都生成产品经理可读的 `output/design/design.md` 和审计用 `output/design/decision-notes.md`。

### 2.1 简单模式

只完成当前需求的最小业务闭环：目标、范围、主路径、关键规则、必要状态和权限、实际涉及的功能/数据、页面/区块/字段/操作、异常和验收。没有真实事实的章节删除，不生成无关空章节、完整 ABC 中间分析或虚构状态机。

### 2.2 完整模式

在简单模式责任之上，完成适用的需求理解、业务建模、业务模型一致性挑战、产品承接和跨层一致性挑战。内部可以拆分多个专项并行，但最终只输出经过合并的产品方案，不把 A/B/C、任务 ID、运行日志或子代理过程写入 Design 正文。

## 3. 依赖图与 `ready_actions[]`

Design 执行由依赖图决定，不由主对话凭长历史重新规划。编排器每轮返回当前所有已满足依赖的 `ready_actions[]`，数量可以是 0、1 或多个；同一批互不依赖的动作可以并行执行。不存在“唯一下一动作”作为当前 Design 契约。

每个就绪动作至少要能说明：

- `action_id`：稳定的动作标识；
- `type`：隔离分析、写作、确定性检查、询问用户或局部修复；
- `depends_on`：必须先完成的动作；
- `input_files` 与输入哈希：允许读取的输入及版本；
- `expected_outputs`：必须产生的产物；
- `completion_check`：可确定性检查的完成条件；
- `forbidden_inputs`：禁止读取的历史、全文材料或无关阶段产物。

### 3.1 共同主图

```text
材料准备/复用
      ↓
模式分支
  ┌───┴───────────────────────────────┐
  │                                   │
简单模式                            完整模式
  │                                   │
最小闭环分析                         A 层需求理解
  ↓                                   ↓
统一写作与生成内自审                 B 层业务建模与一致性挑战
  ↓                                   ↓
确定性检查                           C 层产品承接与跨层一致性挑战
  ↓                                   ↓
Design 索引 ←──────────── Design 写作与生成内自审
                                      ↓
                         三类成品检查可并行进入 ready_actions[]
                                      ↓
                         有限局部修复 → Design 索引
```

上图表示依赖关系，不表示固定模型调用次数。材料版本未变化时复用事实资产；有效产物不因下游失败而重跑。

### 3.2 完整模式的层内并行

- A 层：需求澄清完成后，干系人与责任、目标与成功指标可并行；场景与旅程依赖前述结果；用户故事和范围边界可并行；最后汇总为 A 基线；
- B 层：业务过程与用例可并行；数据流、业务对象、规则、异常可在满足依赖后并行；对象关系与数据定义可并行；生命周期和逻辑数据模型可并行；最后进行业务模型一致性审查；
- C 层：系统功能、权限、集成和产品级非功能可并行；交互与系统数据可并行；验收条件和跨层一致性审查在对应基线齐全后执行；
- Design 写作只读取合并后的产品事实包、适用规则、必要证据和待确认问题，不读取所有专项全文。

主对话只处理模式选择、用户问题、动作回执和完成报告，不自行重排依赖、不把所有专项正文重新装入上下文。

### 3.3 编排器执行流程

当前执行机制以 `$BUNDLE/contracts/design-orchestration-contract.md` 为准，使用 `$BUNDLE/scripts/python/design-orchestrator.py` 驱动依赖图，不用主对话手工拼接阶段。项目根目录以下用 `<project-root>` 表示：

1. 开始或重建一次 Design 运行时，执行 `python scripts/python/design-orchestrator.py init --project-root <project-root> --request "<用户需求>" --mode simple|full`；
2. 主任务循环执行 `python scripts/python/design-orchestrator.py next --project-root <project-root>`，读取返回的全部 `ready_actions[]`，并调度这一批所有互不依赖的动作；不得把数组压成单个动作，也不得自行重排依赖；
3. 每个动作完成后，按动作标识执行 `python scripts/python/design-orchestrator.py accept --project-root <project-root> --action-id <action-id> --result success --fingerprint <输出指纹>`；失败时只提交当前动作的失败回执并保留上游有效结果；
4. 编排器返回用户问题时，主任务只负责向用户提问，收到回答后执行 `python scripts/python/design-orchestrator.py answer --project-root <project-root> --question-id <question-id> --answer "<用户回答>"`，再继续读取下一批就绪动作；
5. 需要查看运行状态时执行 `python scripts/python/design-orchestrator.py status --project-root <project-root>`；完成以编排器返回的完成状态和确定性检查结果为准。

运行阶段交接仍通过项目级门禁校验：上下文包由 `python scripts/python/context-pack.py --stage design --mode simple|full` 按 `contracts/context-loading.manifest.json` 分层装载；在需要材料事实时执行 `python scripts/python/context-runtime-check.py --stage design --require material-manifest --require material-index --require material-facts`；在接收 v2 交接物时，由每个动作的 `accept` 对 `a-baseline`、`b-baseline`、`c-baseline`、`design-brief`、`business-conflicts`、`cross-layer-conflicts` 执行对应的 `context-runtime-check.py --require` 校验；读取旧版兼容性交接包时才使用 `--require design-model --require design-challenge`。这些门禁只校验输入与交接包的结构、版本和来源，不代表固定模型调用链，也不替代 v2 依赖图。

## 4. 材料与上下文边界

项目材料准备是 Align 和 Design 共用的基础能力，不是 Design 额外的业务分析层。材料未变化时复用材料清单、来源索引和事实资产；只有新增、修改或删除的来源及其下游结果失效。

Design 默认读取：

- 用户原始需求；
- 可选的 `output/align/align.md`；
- 有效材料清单、来源索引和事实资产；
- 当前模式需要的规则包、模板和既有 Design；
- 依赖图声明的必要专项产物和定点证据。

Design 默认不读取：

- 无关项目的完整聊天历史；
- 全部原始材料正文；
- 不在动作卡授权范围内的完整专项报告；
- `.workflow/runtime/context/` 中的运行状态、调试字段、缓存和内部记录作为产品事实。

遇到事实冲突或高影响疑点时，只按来源索引定点读取必要原文。任何运行时文件都不能直接写成产品决策，也不能成为 PRD 或 Prototype 的事实源。

## 5. 产品方案写作规则

### 5.1 固定产品结构

最终 `design.md` 按产品经理理解顺序组织，优先使用以下章节：

1. 方案摘要；
2. 用户、场景与目标；
3. 产品方案总览；
4. 关键业务闭环；
5. 业务对象、规则与状态；
6. 角色、权限与数据范围；
7. 页面、区块、字段与操作设计；
8. 外部协作与异常处理；
9. 成功与验收；
10. 方案权衡、风险与待确认。

章节不是机械门槛。没有适用事实时删除；但实际涉及页面、区块、字段或操作时，不得省略对应定义。

### 5.2 页面、区块、字段、操作

页面正式定义必须使用固定标题和属性：

```markdown
### 页面：[页面名称]

- 页面目的：
- 适用角色：
- 进入条件：
- 数据范围：
- 主要状态：

#### 区块：[区块名称]

- 区块目的：

##### 字段：[字段名称]

- 业务含义：
- 字段来源：
- 展示条件：
- 输入与编辑：
- 取值与默认：
- 交互方式：
- 校验与反馈：

##### 操作：[操作名称]

- 适用角色：
- 展示与可用条件：
- 二次确认：
- 成功结果：
- 数据与状态变化：
- 失败与恢复：
- 后续去向：
```

字段使用业务名称，不使用数据库字段名、稳定 ID 或普通技术类型代替。操作不能混入字段。表格只用于速览，不与固定属性定义形成第二套事实。详细正反例读取 `$BUNDLE/references/design-writing.md` 和 `$BUNDLE/templates/design.md`。

### 5.3 高影响问题

会改变目标、范围、流程、权限、数据范围、状态、对象关系、页面、字段、操作、外部责任、异常结果或验收的问题，必须在 Design 阶段处理：

- 已决定的内容写入 Design 正文；
- 无法安全决定的内容写入“待确认事项”，同时写影响范围、当前保守表达和需要谁确认；
- 不能只写在 `decision-notes.md`，不能静默拍板，不能推迟给 PRD、Prototype 或 Review。

## 6. 生成内自审与确定性检查

写作在首次正式写入前完成适用的生成内自审。简单模式检查最小闭环；完整模式检查全部适用的需求理解、业务建模、产品承接和跨层一致性责任。

至少检查：

- 目标、用户、场景、范围、依赖和成功标准；
- 业务闭环、对象、规则、状态、权限、数据范围和异常；
- 页面、区块、字段和操作的固定属性；
- 页面落点与字段定义、权限、状态、业务结果和验收的一致性；
- 事实、推导、风险和待确认的边界；
- 实际涉及的唯一性、时间、生命周期、文件、导入导出、批量、重复/并发和跨系统失败。

确定性检查只能阻断可证明的结构、引用、完整性或执行错误，不能自行补写产品事实。发现问题时优先生成受影响的局部修复动作；不重跑仍然有效的上游动作。局部修复次数必须有限，相同检查指纹不能无限重试。

`spm-design` 不自动执行独立 Review，不自动确认 Design，不自动推进 PRD 或 Prototype。Review 是用户按需调用的第二意见。

## 7. 输出、确认与停止

必须写入：

- `output/design/design.md`：产品经理可读的产品方案；
- `output/design/decision-notes.md`：设计决策、偏离、权衡和待确认的审计记录。

只有用户显式确认 Design 后，才允许生成 PRD 或 Prototype。确认只记录版本哈希，不复制产品事实。

满足以下条件才报告 Design 生成或修改完成：

1. 已按用户选择执行简单模式或完整模式；
2. 目标、范围、用户、关键闭环、角色权限、数据范围、状态、页面、字段、操作、异常和验收的适用内容均已形成证据；
3. 页面、区块、字段、操作的正式定义互相对齐；
4. 不存在 P0 或未处理 P1；
5. `decision-notes.md` 已生成；
6. 依赖图中所有必需动作已完成，或唯一阻断已明确呈现给用户。

## 8. 禁止事项

- 不提供第三种模式，不自动升级或降级模式；
- 不把 `ready_actions[]` 重新压成唯一下一动作；
- 不固定“三次核心调用”或任何固定模型调用次数；
- 不让主对话读取全部原始材料和完整专项报告；
- 不让多个专项直接拼接最终 Design；
- 不把 ABC 中间过程、运行日志、metadata、稳定 ID 或模型编排写入产品正文；
- 不写数据库结构、接口结构、缓存、队列、Hook 或其他未经产品要求的实现机制；
- 不把高影响问题推迟给 PRD、Prototype 或 Review；
- 不自动执行 Review、确认或下游生成。
