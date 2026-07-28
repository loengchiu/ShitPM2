# PRD Review 检查项

> 本文件只保存 PRD 专项检查项映射。通用审查结论、预检查、输出、独立性和停止规则见 [Review 公共执行契约](review-checklist.md)。详细解释按检查项读取 [PRD 写作规则](../references/prd-writing-rules.md)、[PRD 示例](../references/prd-writing-examples.md)、[名词说明格式](../references/prd-glossary-format.md)、[版本规则](../references/prd-versioning.md) 和 [场景检查清单](../references/prd-scene-checklist.md)。

## 目录

- [坏味道与规则边界](#坏味道与规则边界)
- [覆盖与写作质量](#覆盖与写作质量)
- [Design 一致性与结构](#design-一致性与结构)
- [机读交叉与幻觉](#机读交叉与幻觉)
- [高影响事实与上游回退](#高影响事实与上游回退)

## 坏味道与规则边界

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 1. 禁止标签式正文 | 出现“页面目标/关键动作/状态变化/异常提示/关联功能点”等标签堆叠 | [PRD 写作规则](../references/prd-writing-rules.md)；`prd-writing.profile.json` | P2 | `content` / 具体段落 |
| 2. 禁止动作流水账 | 页面正文只按点击顺序描述，没有业务判断、结果和约束 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P1 | `content` / 具体动作 |
| 3. 页面正文不是纯表格 | 页面正文全部由字段/动作表格组成，缺少连续说明 | [PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 页面正文 |
| 4. 控制加粗和模板腔 | 过多加粗，或出现“用于承载/用于支撑/需支持/同常规”等模板化表达 | `prd-writing.profile.json`；[PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 具体段落 |
| 5. 禁止模糊表达 | 出现“按配置/按规范/待补充/详见原型/待定/按业务规则”等未落地表达 | `prd-writing.profile.json`；[PRD 写作规则](../references/prd-writing-rules.md) | P1 | `content` / 具体段落 |
| 6. 禁止原因腔 | 出现“方便用户理解/避免用户误判/符合操作习惯”等不能验收的理由 | `prd-writing.profile.json`；[PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 具体段落 |

## 覆盖与写作质量

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 7. 三层覆盖完整 | 页面同时有界面元素/展示规则、交互逻辑/状态流转、异常/边界处理 | [PRD 写作规则](../references/prd-writing-rules.md)；[场景检查清单](../references/prd-scene-checklist.md) | P1 | `content` / 页面或动作 |
| 8. 标题层级稳定 | 标题跳级、编号混乱或结构无法定位 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 模板](../templates/prd.md) | P2 | `structure` / 标题位置 |
| 9. 模块到动作组织正确 | 详细需求按模块 → 小模块 → 页面 → 动作组织，不按页面平铺整章 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P1 | `structure` / 模块位置 |
| 10. 模块职责和页面范围先行 | 模块开头没有职责与涉及页面，读者无法建立上下文 | [PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 模块位置 |
| 11. 页面动作按用户意图组织 | 按 UI 区域盘点，或没有以动词短语形成动作分块 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P1 | `content` / 页面位置 |
| 12. 动作信息可验收 | 关键动作缺触发、过程、结果或异常中的关键信息 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `content` / 动作位置 |
| 13. 复杂度与篇幅匹配 | 简单动作过度展开，复杂动作被一句模糊话带过 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P2 | `content` / 动作位置 |
| 14. 顺序与并列表达正确 | 有顺序流程未使用有序列表，并列规则被写成混乱长句 | [PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 具体段落 |
| 15. PRD 整体业务流程不混入页面操作 | 整体流程写成页面跳转、按钮点击、抽屉/弹窗操作流水 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P1 | `content` / 业务流程 |
| 16. 字段表不搬入页面正文 | 页面正文重复字段定义表的完整属性清单，而非只写当前动作需要的字段 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P2 | `content` / 页面正文 |
| 17. 关键业务信息优先 | 动作开头先写排序、分页、默认加载等通用规则，掩盖业务判断和状态 | [PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 动作位置 |
| 18. 数值和动态内容明确 | 出现占位数字、静态文案未加引号或动态内容无数据来源 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P1 | `content` / 具体段落 |
| 19. 长文本和按钮规则完整 | 未说明截断/换行/滚动，或按钮缺可用条件、反馈、成功变化、失败提示 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `content` / 动作位置 |
| 20. 表单、列表和弹窗边界完整 | 缺输入限制/校验时机、加载/空/失败状态或弹窗关闭/遮罩/优先级 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `content` / 控件规则 |
| 21. 异常具备降级处理 | 网络异常、权限不足或关键功能失效没有结果、提示和恢复方式 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `content` / 异常位置 |
| 22. 无空栏目和伪缩进 | 标题下为空、占位段，或用伪缩进字符/手敲空格制造层级 | [PRD 写作规则](../references/prd-writing-rules.md) | P2 | `structure` / 具体位置 |
| 23. 表格使用边界正确 | 用表格承载页面长正文或流程叙述，而不是字段、权限、状态、枚举等结构化信息 | [PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 表格位置 |

## Design 一致性与结构

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 24. 名词说明可追溯 | PRD 术语未在 glossary 规则要求的位置收录，或术语前后含义漂移 | [名词说明格式](../references/prd-glossary-format.md)；[PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / glossary |
| 25. 页面组织保持既有方向 | 核心章节缺名词说明或详细需求，模块/小模块/页面/动作层级被改写 | [PRD 模板](../templates/prd.md)；[PRD 写作规则](../references/prd-writing-rules.md) | P1 | `structure` / 章节位置 |
| 26. 字段定义格式适配实际语义 | 字段表没有按实体分组，或机械铺开无关属性造成无法阅读 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 模板](../templates/prd.md) | P2 | `structure` / 字段表 |
| 27. 状态机按核心对象组织 | 状态没有对象、迁移、触发动作或限制条件 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 模板](../templates/prd.md) | P1 | `content` / 状态机 |
| 28. 辅助章节按真实约束出现 | 验收汇总、风险或待确认章节为空，或真实约束被省略 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 场景清单](../references/prd-scene-checklist.md) | P1 | `structure` / 辅助章节 |
| 29. 页面和字段覆盖 Design | Design 页面/字段未在 PRD 对应章节、字段表或必要落点出现 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / affected_objects |
| 30. 权限表达保持一致 | PRD 权限口径与 Design 的页面、按钮、字段例外或数据范围不一致 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / 权限位置 |
| 31. 状态表达保持一致 | PRD 状态集合、迁移、触发或限制与 Design 不一致 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / 状态位置 |
| 32. 页面编号唯一 | 页面编号重复，或动作/页面引用无法定位 | [PRD 模板](../templates/prd.md)；[PRD 写作规则](../references/prd-writing-rules.md) | P2 | `structure` / 页面编号 |
| 33. 动作避免机械复用 | 不同页面动作正文完全照抄，未说明页面特有条件和结果 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P2 | `content` / 动作位置 |
| 34. 规则放置位置正确 | 一个页面的规则被跨节代写，或字段/状态/权限规则落错位置 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / 规则位置 |
| 35. 三类读者可执行 | 开发不能写代码、测试不能写用例或设计不能画原型 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `content` / 审查问题 |

## 机读交叉与幻觉

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 36. 功能覆盖完整 | Design 页面清单中每个页面都有对应 PRD 章节 | `prd-consistency-check.py`；[PRD 模板](../templates/prd.md) | P1 | `consistency` / 页面位置 |
| 37. 字段覆盖完整 | Design 字段定义中的业务字段出现在字段定义表或页面章节 | `prd-consistency-check.py`；[PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / 字段位置 |
| 38. 字段落点可追溯 | 字段在详细需求、权限、状态、验收或风险待确认中没有明确落点 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / 字段位置 |
| 39. 字段跨页规则一致 | 同一字段在不同页面的展示格式、校验规则或来源发生冲突 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / 字段位置 |
| 40. 权限与按钮一致 | 权限规则和页面按钮可见性/可操作性不匹配 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / 权限位置 |
| 41. 状态与页面表达一致 | 状态机和页面筛选、展示或动作条件不匹配 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / 状态位置 |
| 42. 变更传播完整 | 修改字段、页面动作、状态、权限、阈值或验收项后，相关章节未同步 | [PRD 写作规则](../references/prd-writing-rules.md)；[同步修复传播规则](fix-propagation-rules.md) | P1 | `consistency` / affected_objects |
| 43. 无 Design 外字段/页面/状态幻觉 | PRD 出现 Design 未定义的字段、页面或状态 | `prd-consistency-check.py`；[PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / hallucination |
| 44. 业务流程可实现 | 状态流转只有集合无迁移，或分支、异常、降级策略无法执行 | [PRD 写作规则](../references/prd-writing-rules.md)；[PRD 示例](../references/prd-writing-examples.md) | P1 | `content` / 流程位置 |
| 45. 跨页面流转有自然语言边界 | 状态变更或跨页面结果没有在详细需求中说明 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `content` / 相关动作 |

## 高影响事实与上游回退

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 46. 不引入 Design 未授权高影响事实 | PRD 新增字段、状态、权限、流程、模块边界或跨系统责任 | [PRD 写作规则](../references/prd-writing-rules.md)；[同步修复传播规则](fix-propagation-rules.md) | P1 | `consistency` / affected_objects |
| 47. 不静默拍板 Design 待确认项 | PRD 将 Design 的待确认问题自行结论化 | [PRD 写作规则](../references/prd-writing-rules.md) | P1 | `consistency` / affected_objects |
| 48. 表达问题留在 PRD | 只是措辞、结构、格式或覆盖不足，不改变 Design 事实 | [PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 具体位置 |
| 49. 上游问题回退 Design | Design 缺失或错误导致 PRD 无法保持语义时，PRD 不自行补事实 | [同步修复传播规则](fix-propagation-rules.md) | P1 | `consistency` / needs_upstream_sync |
| 50. Review 不承担计划内补全 | Review 结果直接代写 PRD 或把生成责任推给 Review | [Review 公共执行契约](review-checklist.md)；[PRD 写作规则](../references/prd-writing-rules.md) | P2 | `content` / 审查问题 |
