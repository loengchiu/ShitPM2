# PRD 写作规则落点补救方案

> 日期：2026-08-05  
> 状态：已被修订，不按本文执行  
> 修订原因：本文把用户原始目标抽象成了泛化的“规则落点治理”，没有准确承接 `main:references/prd-writing.md` 中用户认可的详细需求说明写法。  
> 新方案：`docs/plans/2026-08-05-main-prd-writing-merge-remediation-plan.md`

## 1. 结论

前一轮执行结果不需要整体回滚，但原方案的规则组织方式需要推倒重做。

保留：

- Design 操作表补充入口、字段级输入、二次确认、后续去向等交互维度；
- PRD 页面区块和展示行为的列表式写法；
- 行首标签式正文的确定性 lint 约束；
- Design 推断值登记与一次性 confirmation 汇总机制；
- 已有分片装载、事实边界、非页面字段回读和跨层检查。

废止或改写：

- 不再把同一套完整规则复制到 `rules`、`SKILL`、模板、示例和 Review 清单；
- 不再把“动作内部组织公式”作为固定格式；
- 不再把“每个动作都完整回答四问”作为统一硬门槛；
- 不再把“六处同步”当作规则架构正确的证明；
- 不再把 PRD 写作整合、Design 推断值、lint 增强混成一份验收范围。

## 2. 当前问题

### 2.1 规则事实源重复

动作交互要求同时出现在：

- `references/prd-writing-rules.md`
- `skills/spm-prd/SKILL.md` 的模块完成条件和生成内自检
- `templates/prd.md`
- `references/prd-writing-examples.md`
- `references/prd-scene-checklist.md`
- `contracts/prd-review-checklist.md`

这些位置可以同时出现，但只能有一个地方定义完整语义。其他位置只能承担流程入口、局部提示、示例或审查问题，不能重新定义规则。

### 2.2 硬约束和写作建议混在一起

“动作最低覆盖”“高影响未知不得静默补造”是硬约束；“场景条件引出”“动作优先、区块为辅”“按复杂度定篇幅”是写作建议。原方案把它们统称为“软约束”，会导致执行者不知道哪些可以裁量。

### 2.3 四问与简单动作互相冲突

简单的查询、查看、返回动作不一定存在表单、二次确认或异常分支；如果要求每个动作都完整写入口、表单、反馈、分支，模型会重新生成模板化流水账。

### 2.4 验收范围已经漂移

原方案声明“不动 lint”，但实际改动已包含 `prd-style-lint.py`、`prd-writing.profile.json`、Design/Align/Review Skill 和多个契约文件。后续验收必须拆分：

1. PRD 写作和页面表达收敛；
2. Design 推断值机制；
3. 行首标签 lint 增强；
4. Design 操作表交互维度补强。

不能用一份“全部同步、全部通过”的报告覆盖四类不同变更。

## 3. 目标规则架构

| 内容类型 | 唯一事实源 | 其他位置的职责 |
|---|---|---|
| PRD 内容硬规则、事实边界、动作分级要求 | `references/prd-writing-rules.md` | 其他位置只引用或转成检查问题 |
| PRD 生成流程、停止条件、装载顺序 | `skills/spm-prd/SKILL.md` | 不复制规则全文 |
| 输出章节、标题和局部填充提示 | `templates/prd.md` | 只保留模板局部提示和格式示例 |
| 正反例 | `references/prd-writing-examples.md` | 只展示写法，不承担规范解释 |
| 模块写作自检 | `references/prd-scene-checklist.md` | 写检查问题，指向规则章节 |
| Review 判定 | `contracts/prd-review-checklist.md` | 写证据要求和问题，不重新定义规则 |
| 可确定的标签/格式检查 | `contracts/prd-writing.profile.json` + `scripts/python/prd-style-lint.py` | 只检查稳定的文本模式，不判断业务语义 |
| Design 推断值 | `references/design-writing.md` + `skills/spm-design/SKILL.md` | PRD 只承接已确认 Design，不复制完整分类 |
| 上下文装载 | `contracts/context-loading.manifest.json` | 只负责路由，不增加产品规则 |

`AGENTS.md` 不承载 PRD 运行时写作规则；它只维护 ShitPM 仓库本身的开发约束。

## 4. 动作规则重新分层

### 4.1 硬约束

写入 `references/prd-writing-rules.md`，只保留以下不可省略的语义要求：

- 动作必须能定位角色、前置条件、业务处理和结果；
- 状态变更、权限、数据范围、失败后业务影响不得丢失；
- 高影响未知必须待确认，不得由 PRD 静默拍板；
- 已有 Design 交互事实必须承接；
- 不得把动作写成纯点击流水账或标签式伪正文。

### 4.2 按复杂度确定最低覆盖

不要要求所有动作使用同一篇幅和同一结构：

| 动作级别 | 最低覆盖 |
|---|---|
| 简单查询、查看、返回 | 触发条件 + 业务结果；Design 已定义的异常或特殊展示才补充 |
| 普通表单或状态变更 | 前置条件 + 输入/校验 + 处理 + 成功结果 + 失败处理 |
| 高复杂、多分支、破坏性、跨角色或外部协作 | 角色/状态/入口、字段和确认、各分支结果、状态变化、失败恢复和后续去向 |

### 4.3 四问降为自检视角

“入口、表单、反馈、分支与确认”保留，但只作为中高复杂动作的覆盖视角：

- 不要求正文出现四个小标题；
- 不要求简单动作虚构不存在的表单或异常；
- Design 未定义的高影响交互列为待确认；
- 四问不再在 `SKILL.md`、模板和示例中全文重复。

### 4.4 写作建议不再公式化

“业务判断与结果 → 字段/状态 → 展示 → 异常”改为可选写作提示，不作为固定顺序。动作正文应优先表达业务结果，再按实际需要补充字段、状态、展示和异常。

## 5. 文件处理方案

### 5.1 必须收敛

1. `references/prd-writing-rules.md`
   - 明确硬约束、写作建议、按复杂度的最低覆盖；
   - 将四问改成自检视角；
   - 删除会被理解为固定公式的强制语气；
   - 保留页面列表式格式和事实边界。

2. `skills/spm-prd/SKILL.md`
   - 保留阶段流程、停止条件、写入边界和最终自检流程；
   - 把模块完成条件和生成内自检中的长篇动作规则改为指向 `prd-writing-rules.md`；
   - 不再在两个位置复制四问全文。

3. `templates/prd.md`
   - 保留章节、页面标题、动作标题、列表式区块示例；
   - 动作注释只提示“按动作复杂度承接规则”，不再嵌入完整四问清单；
   - 模板不得用具体业务区块名称暗示所有项目都必须这样命名。

4. `references/prd-writing-examples.md`
   - 保留简单动作、复杂动作、场景条件、页面列表式和反例；
   - 删除重复解释“规则是什么”的长段落；
   - 每个示例只说明它展示的一个重点，不承担规范定义。

5. `references/prd-scene-checklist.md`、`contracts/prd-review-checklist.md`
   - 保留检查项；
   - 检查项写成“是否满足规则章节 + 应查看什么证据”；
   - 不再复制完整规则正文。

### 5.2 冻结，不纳入本次补救

- `contracts/prd-writing.profile.json`
- `scripts/python/prd-style-lint.py`
- `scripts/python/test-prd-style-lint.py`
- `scripts/python/design-index.py`
- Design 推断值机制相关文件
- Design 操作表十列相关文件

这些改动已有独立目的和独立验收证据。本次只确认它们与新规则不冲突，不借补救方案再次扩大范围。

### 5.3 明确不做

- 不修改用户正式项目的 `output/design/design.md` 或 `output/prd/prd.md`；
- 不修改历史计划和历史验收报告；
- 不新增规则总表、覆盖率 JSON、检查器、回执或编排阶段；
- 不执行 `git commit` 或 `git push`。

## 6. 执行顺序

1. 先修改 `references/prd-writing-rules.md`，建立唯一语义源和动作分级。
2. 再精简 `skills/spm-prd/SKILL.md`，只保留流程和引用。
3. 精简 `templates/prd.md` 和 `prd-writing-examples.md`，保留局部提示与代表性示例。
4. 同步收敛场景清单和 Review 清单，不新增检查项类型。
5. 回读 `context-loading.manifest.json` 编译结果，确认写作和模块装载仍包含规则唯一源。
6. 用合成样本做行为探针，再运行已有测试。
7. 输出一份拆分范围的补救验收报告，分别报告规则收敛、Design 交互、推断值、lint 和测试结果。

## 7. 行为验收

### 7.1 简单动作

输入一个仅有查询结果的动作。通过条件：

- 不被要求虚构表单、确认或异常分支；
- 仍然能读出触发条件和业务结果。

### 7.2 普通状态变更

输入一个含字段校验和状态变化的提交动作。通过条件：

- 能读出角色、允许状态、输入、处理、成功结果和失败处理；
- 不出现固定四段标题或标签式正文。

### 7.3 高复杂动作

输入一个含多角色、多出口或外部协作的动作。通过条件：

- 入口、字段/确认、分支、状态、副作用和恢复方式可定位；
- Design 未定义的高影响内容仍进入待确认。

### 7.4 页面表达

通过条件：

- 页面区块和展示行为可以用列表或短自然句表达；
- 不再生成“页面区块与业务目的：”“页面展示行为和状态驱动展示：”这类长标题前缀；
- 页面格式要求不扩散为 Skill 中的完整格式手册。

## 8. 自动化与回归验收

至少运行现有相关测试：

- `test-prd-simplification`
- `test-prd-style-lint`
- `test-prd-consistency-semantics`
- `test-design-simplification`
- `test-design-index`
- `test-context-loading`
- `test-shitpm-regression`
- `test-resource-integrity`

测试通过不能替代规则归属和真实样本回读。验收报告必须同时列出：

- 规则唯一源是否明确；
- Skill、模板、示例、清单是否只承担各自职责；
- 三类动作探针结果；
- 当前冻结范围内的已有改动是否保持；
- 仍未解决的存量项目格式问题。

## 9. 补救完成标准

全部满足后，才能宣布补救完成：

1. `references/prd-writing-rules.md` 是 PRD 动作语义的唯一完整规则源；
2. 动作规则已区分硬约束、复杂度最低覆盖和写作建议；
3. 简单动作不再被四问硬性绑架；
4. `spm-prd`、模板、示例和清单没有复制完整规则正文；
5. Design 推断值和十列表格等既有成果未被回滚；
6. 页面列表式格式和标签 lint 仍然有效；
7. 三类动作探针通过，相关测试通过；
8. 未修改正式项目，未新增门禁资产，未执行 commit/push。

## 10. 最终报告格式

```text
一、补救结论
二、保留的既有成果
三、废止或改写的旧规则
四、规则唯一源与各消费者职责
五、三类动作探针结果
六、页面格式与事实边界回归
七、自动化测试结果
八、未解决问题
九、Git 状态
```
