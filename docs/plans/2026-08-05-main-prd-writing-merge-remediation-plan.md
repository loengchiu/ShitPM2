# main PRD 详细需求说明迁移补救方案

> 日期：2026-08-05  
> 状态：已被修订，不按本文执行  
> 修订原因：本文仍以“迁移 main 写法”为主，未充分体现“结合 main 与 V2 优点、以资深产品经理质量为最终目标”。  
> 新方案：`docs/plans/2026-08-05-main-v2-senior-prd-writing-convergence-plan.md`  
> 前置背景：`main:references/prd-writing.md` 的详细需求说明写法已经被用户认可；此前迁移到 V2 的执行结果虽然加入了部分内容，但把目标扩展成了新的“动作交互治理体系”，导致规则重复、写法变重、验收范围混杂。  
> 本方案：以 `main` 已认可的写法为基准，补齐 V2 详细需求说明部分；保留 V2 的事实边界、分片流程、页面标题格式和已有确定性检查，不重新设计 PRD 整体架构。

## 1. 原始目标重新定义

本次补救只解决一个问题：

> 让 V2 的 `4.x.6 功能详细说明` 回到 main 中“按用户动作写产品规格”的表达质量。

必须迁移的行为：

- 页面内按用户动作组织，动词短语直接作为动作名，例如“查询入库记录”“发起入库申请”；
- 页面开头可以用一段交代页面区域组成和职责，但正文按用户动作组织，不按“筛选区”“列表区”等 UI 区域盘点；
- 动作下需要交代页面区块或信息分组时，区块较多或存在子分组才用列表拆开；区块很少且内容很短时用自然句，不强行拆列表；
- 按操作顺序写成产品规格说明，主链路写清步骤，关键分支单列，状态变化落到结果；
- 每个动作覆盖触发条件、操作过程、操作结果、异常处理，但不套固定四段格式；
- 短句优先，一句表达一层规则，少讲原因，多写展示字段、可点条件、状态变化、失败提示和边界限制；
- UI 文案直接嵌入正文并用双引号标明，不单独另列文案表；
- 动态展示说明数据来自系统计算、接口返回、关联带出还是用户输入；
- 超长文本必须说明截断、换行、滚动或悬停查看全文等处理方式；
- 正文使用自然段、数字编号列表和 `·` 并列列表，按场景选择；
- 页面或模块开头的自然段只交代语境，进入动作后不能用大段背景说明替代规格；
- 默认角色可见性在模块权限区统一说明，动作正文只写特殊限制；
- 动作结果之后直接说明下一步由谁衔接，或状态如何自动进入下一阶段；
- 用“手机号不合法时”“弱网环境下”“倒计时归零后”等场景条件引出规则，不用“界面元素/交互逻辑/异常处理”作小节标题。

## 2. 明确保留的 V2 约束

本次不是把 main 原文整份搬回 V2，以下内容继续以 V2 为准：

- Design 是唯一产品事实源，PRD 不得静默新增高影响事实；
- V2 的 `###### 页面名称`、`**动作名称**` 页面和动作标记；
- V2 的模块、业务阶段、页面、动作组织方式；
- V2 的分片读取和直接写入最终 PRD 流程；
- V2 的非页面字段回读、状态/权限/异常/删除传播和枚举来源要求；
- V2 的 draw.io + PNG 流程图交付方式；
- V2 已有的 Design 操作表十列和推断值确认机制；
- 现有 `prd-writing.profile.json` 和 `prd-style-lint.py` 的确定性约束。

明确不迁移 main 中与 V2 已确认方向冲突的内容：

- `大模块 → 小模块 → 页面 → 动作` 的强制嵌套；
- Mermaid 流程图；
- main 旧版页面粗体和 `·` 动作标记；
- main 旧版模板中与 V2 标题、流程和事实边界冲突的写法。

## 3. 关联参考内容与迁移映射

`main:skills/spm-prd/SKILL.md` 的 PRD 写作流程不是只读取 `prd-writing.md`。执行迁移时必须逐项核对以下关联内容：

| main 来源 | V2 对应位置 | 迁移要求 |
|---|---|---|
| `main:references/prd-writing.md` | `references/prd-writing-rules.md` + `references/prd-writing-examples.md` | 迁移用户认可的写法和正反例；不迁移与 V2 冲突的旧层级和旧标记 |
| `main:references/prd-writing.profile.json` | `contracts/prd-writing.profile.json` | 核对 `forbidden_expressions`、`constraints.granularity.three_layers` 等机读约束是否完整保留；确认只是路径职责调整，不发生规则丢失 |
| `main:references/prd-glossary-format.md` | `references/prd-glossary-format.md` | 保留名词章节的位置、来源、收录边界、表格格式和正反例；由 `prd-writing-glossary` 装载 |
| `main:references/prd-versioning.md` | `references/prd-versioning.md` | 保留版本记录维护方式、触发条件、版本号递增和字段填写规则；由 `prd-writing-versioning` 装载 |
| `main:references/prd-scene-checklist.md` | `references/prd-scene-checklist.md` | 保留数据展示、按钮与操作、表单与输入、列表与加载、弹窗、异常与降级、边界七类场景，并补充本轮动作/页面写法自检 |
| `main:templates/prd.md` | `templates/prd.md` | 保留 V2 章节骨架和标记格式，只迁移详细需求说明中的写法提示和示例 |
| `main:contracts/review-checklist.md` | `contracts/review-checklist.md` | 作为 Review 的通用检查入口核对，不把 Review 检查项误当成 PRD 写作事实源 |
| `main:skills/spm-prd/SKILL.md` | `skills/spm-prd/SKILL.md` | 核对所有 `$BUNDLE` 读取、生成顺序、状态更新和失败处理；格式明细仍不直接复制进 Skill |

验收不能只检查 `prd-writing-rules.md` 是否出现若干关键词，必须确认上述文件在 V2 的实际装载链中仍然可达。`contracts/context-loading.manifest.json` 负责证明装载关系，不负责承载这些规则本身。

## 4. 规则落点

### 4.1 `references/prd-writing-rules.md`：唯一规范源

把 main 的行为要求整理到现有 V2 规则文件的对应章节，不新建第二套 PRD 写作规则文件。

建议落点：

| main 内容 | V2 落点 |
|---|---|
| 页面按动作组织、动词短语动作名 | `§3 页面落点`、`§4 模块内部结构` |
| 动作按时序写规格 | `动作与业务自然语言 §2` |
| 复杂度分级 | `动作与业务自然语言 §2.1` |
| 三类内容融进行动流程 | `§2.1`，明确是内容覆盖维度 |
| 场景条件引出规则 | `§2.1`、`§3 结构化自然语言` |
| 页面区块动作优先、区块为辅 | `§3.2 页面展示行为与区块条件` |
| UI 文案、动态数据来源 | `§2.1` 或 `§6 查询/表单规则` |
| 超长文本处理 | `§3.2`、`§3.3 状态驱动展示` |
| 三种表达形式 | `§3 结构化自然语言` |
| 默认角色可见性和衔接角色 | `§3.1 页面操作逐项承接`、动作规则 |
| 空栏目、伪缩进、原因腔、模板腔 | `常见错误` 和 `§3 结构化自然语言` |

规则文件中必须明确区分：

- **硬要求**：动作不能缺少业务触发、处理、结果和必要异常；高影响事实不能补造；页面动作必须可实现、可验证；
- **写作偏好**：短句、少讲原因、动作优先、按复杂度定篇幅、区块不强行拆列表；
- **禁止格式**：固定标签小节、流水账、伪缩进、空标题和无事实占位。

“业务判断与关键结果 → 关键字段/状态 → 默认展示规则 → 异常/边界”保留为推荐组织顺序，不写成固定模板。

### 4.2 `references/prd-writing-examples.md`：只承载示例

从 main 提取并改写为 V2 标记的代表性示例：

1. 简单动作：1–2 句完成触发和结果；
2. 中等动作：字段、校验、提交结果和失败保留；
3. 高复杂动作：多角色、状态推进、关键分支；
4. 场景条件引出规则的好例和坏例；
5. 页面区块较多时的列表写法；
6. 页面区块很少时的自然句写法；
7. UI 文案、超长文本、动态数据来源和角色衔接示例；
8. 流水账、术语标签小节、默认角色重复和原因腔反例。

示例只展示“怎么写”，不在每个示例后重复一遍完整规范。

### 4.3 `templates/prd.md`：只保留局部提示

模板只保留：

- V2 页面和动作标题格式；
- 页面区块列表和展示行为列表的局部示例；
- 动作正文的最小提示；
- 指向 `references/prd-writing-rules.md` 和示例文件的引用。

模板不嵌入完整的四问清单、完整风格手册或一大段业务规则。模板里的业务名称只能作为占位示例，不能暗示所有项目必须使用同样的区块名称。

### 4.4 `skills/spm-prd/SKILL.md`：只负责流程和门禁

Skill 保留：

- Design confirmation 前置条件；
- 全局扫描、骨架、模块分片、有限整合和中断恢复；
- 高影响未知停止；
- 生成内回读和最终检查；
- 指向规则文件和示例文件的读取要求。

Skill 不再承载详细格式手册，不重复 main 写法的完整段落，也不把动作四问复制到多个自检位置。自检只写成“按动作复杂度回读规则覆盖是否完整”。

### 4.5 其他位置

- `references/prd-scene-checklist.md`：只保留自检问题，不复制长篇写法；
- `references/prd-glossary-format.md`：保留名词说明的独立写作规范，不并入动作规则；
- `references/prd-versioning.md`：保留版本记录维护规范，不并入 PRD 正文写作；
- `contracts/prd-review-checklist.md`：只保留审查证据，不重新定义风格；
- `contracts/review-checklist.md`：作为通用 Review 入口，不作为 PRD 规则正文；
- `contracts/prd-writing.profile.json`：只维护可确定的禁用表达式；
- `scripts/python/prd-style-lint.py`：只处理稳定坏味道，不判断短句、业务密度或动作是否自然；
- `contracts/context-loading.manifest.json`：确认规则和示例在 writing/module 装载路径可达，不增加新 pass；
- `AGENTS.md`：不放 PRD 运行时规则。

## 5. 执行步骤

### 第一步：建立 main 到 V2 的完整迁移清单

逐条核对 main 的以下来源：

- §一“复杂度分级”；
- §2.3“动作正文要写到的内容”；
- §2.4“页面区块排版”；
- §三“坏例子：动作流水账”；
- §四“业务流程写法”中与动作规格有关的部分；
- §五“对照速查”中 UI 文案、长文本、列表形式、角色可见性和角色衔接规则；
- 本方案第 1 节用户明确补充的规则。

同时核对本方案第 3 节列出的全部关联 references、模板、Skill 和 Review 入口。

每条规则必须标记为：已存在、需改写、需新增、与 V2 冲突而不迁移、已外置但需验证装载。

### 第二步：先确认 references 依赖和装载关系

先验证：

1. `prd-writing-glossary` 实际装载 `references/prd-glossary-format.md`；
2. `prd-writing-versioning` 实际装载 `references/prd-versioning.md`；
3. `prd-verification-scenes` 实际装载 `references/prd-scene-checklist.md`；
4. `prd-profile` 实际装载 `contracts/prd-writing.profile.json`；
5. `prd-template` 实际装载 `templates/prd.md`；
6. `prd-writing-structure` 与 `prd-writing-action` 从同一份 `references/prd-writing-rules.md` 读取对应章节；
7. `spm-prd-review` 能读取 `contracts/review-checklist.md`、`contracts/prd-review-checklist.md` 和需要的 references。

如果引用文件存在但没有进入实际装载路径，不能算“已迁移”。

### 第三步：先改规则源，再改消费者

顺序固定为：

1. `references/prd-writing-rules.md`；
2. `references/prd-writing-examples.md`；
3. `references/prd-glossary-format.md`、`references/prd-versioning.md`、`references/prd-scene-checklist.md` 的缺失内容；
4. `contracts/prd-writing.profile.json` 的路径和约束完整性；
5. `templates/prd.md`；
6. `skills/spm-prd/SKILL.md`；
7. `contracts/review-checklist.md`、`contracts/prd-review-checklist.md`；
8. 只同步受影响的测试断言。

不得先在 Skill、模板和清单中分别补句子，再回头拼规则。

### 第三步：确认当前已执行成果不回退

本次只检查，不重新设计：

- Design 操作表十列；
- `design-index.py` 的十列表头解析；
- 推断值登记与 confirmation 汇总；
- 行首标签 lint；
- 页面列表式写法；
- 分片上下文装载。

若发现冲突，优先调整 PRD 写法说明和消费者引用，不回滚这些已有能力。

## 6. 行为验收

### 5.1 页面组织

样本页面必须满足：

- 页面开头可以交代区域组成和职责；
- 进入正文后按“查询入库记录”“发起入库申请”等动作组织；
- 不按“筛选区”“列表区”逐块盘点动作。

### 5.2 区块表达

分别验证：

- 多区块或有子分组：使用 `-` 列表；
- 一两个短区块：使用自然句；
- 不生成“页面区块与业务目的：”等标题式前缀；
- 不把区块列表替代动作正文。

### 5.3 动作写作

至少验证一个查询动作、一个表单提交动作和一个多角色流转动作：

- 动作名是动词短语；
- 主链路按操作顺序写；
- 状态变化落到结果；
- 关键分支单列；
- 失败时写提示、数据保留和恢复方式；
- UI 文案用双引号嵌入正文；
- 动态展示注明数据来源；
- 超长文本写明处理方式；
- 下一步衔接角色写在动作结果之后；
- 不重复默认可见角色；
- 不出现固定四段标签或流水账。

### 5.4 事实边界

Design 未定义按钮、文案、字段、权限、状态或外部行为时：

- 高影响内容进入待确认；
- 低影响展示细节按当前 Design 推断值机制处理；
- PRD 不自行新增产品事实。

## 7. 自动化和人工验收

运行现有相关测试：

- `test-prd-simplification`
- `test-prd-style-lint`
- `test-prd-consistency-semantics`
- `test-design-simplification`
- `test-design-index`
- `test-context-loading`
- `test-shitpm-regression`
- `test-resource-integrity`

测试通过不能代替 main 写法迁移验收。人工验收必须回读真实规则、示例、模板和 Skill 的加载关系，并确认：

- main 的目标行为已经进入 V2 唯一规则源；
- main 关联的 glossary、versioning、scene checklist、profile、template 和 Review 入口没有漏迁或断装载；
- Skill 没有重新承载格式明细；
- 示例和模板没有把规则改写成固定模板；
- Design 十列表格、推断值机制和 lint 没有回退；
- 未把 main 中与 V2 冲突的小模块嵌套、Mermaid 和旧标记带回 V2。

## 8. 完成标准

1. main 中用户认可的详细需求说明写法逐条在 V2 找到落点；
2. main 关联的 references、模板、profile 和 Review 入口均已完成内容或装载核对；
3. V2 的 `4.x.6` 能按动作写成连续、克制、高密度的产品规格；
4. 简单动作不过度展开，高复杂动作不缺关键分支；
5. 页面区块是辅助表达，不替代动作组织；
6. UI 文案、动态来源、超长文本、默认角色可见性和衔接角色规则均有明确写法；
7. 规则正文只有一个完整事实源，Skill/模板/示例/清单各司其职；
8. V2 已有事实边界、标题格式、分片流程和确定性检查保持有效；
9. 未修改正式项目，未新增检查器、回执或编排阶段；
10. 未执行 `git commit` 或 `git push`。

## 9. 最终报告格式

```text
一、结论
二、main 规则迁移清单
三、V2 规则唯一落点
四、Skill/模板/示例/清单职责核对
五、三类动作和两类页面区块样本验收
六、事实边界与既有能力回归
七、自动化测试结果
八、未迁移内容及原因
九、Git 状态
```
