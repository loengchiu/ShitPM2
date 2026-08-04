# Design Review 检查项

> 本文件只保存 Design 专项检查项映射。通用审查结论、预检查、输出、独立性和停止规则见 [Review 公共执行契约](review-checklist.md)。详细解释按检查项读取 [Design 写作规则](../references/design-writing.md)、[Design 质量标准](../references/design-quality-rubric.md)、[状态定义格式](../references/design-state-format.md) 和 [业务流程格式](../references/design-flow-format.md)。
>
> 当前 Design 的主要读者是产品经理。页面、区块、字段和操作使用固定标题与固定属性；旧版宽表和 metadata 只作为兼容材料，不构成当前产品事实源。

## 检查项映射

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 1. 方案摘要可判断 | 缺少问题、方案、结果、范围或重点确认事项，产品经理无法先理解本期要做什么 | [Design 模板](../templates/design.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `structure` / 方案摘要 |
| 2. 目标、用户、场景和成功标准完整 | 只有功能清单，缺少用户问题、使用场景、成功判定或失败判定 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 用户、场景与目标 |
| 3. 范围、边界和依赖明确 | 范围外、系统边界、外部责任或限制缺失，导致下游可能重新引入排除项 | [Design 模板](../templates/design.md) | P1 | `content` / 摘要或外部协作 |
| 4. 关键业务闭环可走完 | 缺触发、参与者、阶段、分支、结果、恢复或后续责任 | [Design 写作规则](../references/design-writing.md)；[业务流程格式](../references/design-flow-format.md) | P1 | `content` / 业务闭环 |
| 5. 简单流程不过度展开 | 单角色、无分支、无异常的流程被强制拆成无意义的空表格或重复步骤 | [业务流程格式](../references/design-flow-format.md) | P2 | `content` / 业务闭环 |
| 6. 对象、规则和状态互相解释 | 核心对象关系、生命周期、规则、状态或责任之间存在断链 | [Design 分析协议](../references/design-analysis-protocol.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `consistency` / 业务模型 |
| 7. 状态机结构闭环 | 非终态无出路、非初始态无入路、回退目标非法或迁移含义不明确 | [状态定义格式](../references/design-state-format.md) | P1 | `content` / 状态位置 |
| 8. 状态条件和副作用完整 | 缺触发角色、前置条件、可逆性、限制条件、数据变化或异常处理 | [状态定义格式](../references/design-state-format.md) | P1 | `content` / 状态迁移 |
| 9. 权限和数据范围可执行 | 只有角色列表，没有可见范围、可执行动作、字段例外或敏感操作限制 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 权限与数据范围 |
| 10. 页面使用固定属性 | 页面只有名称，缺页面目的、适用角色、进入条件、数据范围或主要状态 | [Design 模板](../templates/design.md)；[Design 写作规则](../references/design-writing.md) | P1 | `structure` / 页面位置 |
| 11. 区块按用户任务组织 | 区块按数据库表、接口或技术模块拆分，或区块没有目的 | [Design 写作规则](../references/design-writing.md) | P2 | `content` / 区块位置 |
| 12. 字段使用固定属性 | 缺业务含义、字段来源、展示条件、输入与编辑、取值与默认、交互方式或校验反馈 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 字段位置 |
| 13. 操作使用固定属性 | 只有按钮名，缺适用角色、入口/触发方式、可用条件、确认、成功结果、数据/状态变化、失败恢复或后续去向；“输入”列非字段级（如“结果、备注”式粗粒度） | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 操作位置 |
| 14. 产品字段使用业务名称 | 用数据库字段名、内部编号或技术类型替代中文业务名称 | [Design 写作规则](../references/design-writing.md) | P2 | `content` / 字段位置 |
| 15. 页面与字段落点存在 | 用户可见、可编辑、可筛选或动作直接依赖的字段没有页面、区块落点 | [Design 写作规则](../references/design-writing.md) | P1 | `consistency` / 字段落点 |
| 16. 页面落点不引入未定义字段 | 页面、区块或操作出现没有正式定义的产品字段 | [Design 写作规则](../references/design-writing.md) | P1 | `consistency` / 页面位置 |
| 17. 非页面字段例外合理 | 内部字段未说明原因，或可见/可编辑/可筛选字段被错误归入内部字段 | [Design 模板](../templates/design.md) | P1 | `consistency` / 非页面落点字段 |
| 18. 页面清单与正式页面一致 | 页面速览有页面未展开，或正式页面不在清单中且造成覆盖歧义 | [Design 模板](../templates/design.md) | P1 | `consistency` / 页面位置 |
| 19. 实际页面规则已覆盖 | 真实存在的列表默认、空/加载/异常、文件、导入导出、批量或跨系统同步没有产品口径 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 页面或闭环 |
| 20. 业务闭环与产品承接一致 | 流程、角色权限、数据范围、状态、页面、字段、操作、外部责任或异常路径存在断链 | [Design 分析协议](../references/design-analysis-protocol.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `consistency` / `affected_objects` |
| 21. 高影响问题在 Design 阶段暴露 | 把会改变方案的问题推迟给 PRD、Prototype 或 Review | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `content` / 待确认事项 |
| 22. 未授权高影响假设被显式标记 | 静默新增流程、权限、状态、数据范围、页面操作或跨系统责任 | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `consistency` / 审查问题 |
| 23. 事实、推导和待确认可区分 | 评审无法判断输入事实、设计推导和仍需用户决定的内容 | [Design 质量标准](../references/design-quality-rubric.md) | P1 | `content` / 审查问题 |
| 24. 关键动作产品结果闭环 | 动作缺前置条件、影响字段/对象、成功/失败结果、状态副作用、后续责任或恢复路径 | [Design 写作规则](../references/design-writing.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `content` / 操作位置 |
| 25. 数据生命周期可判定（按需） | 删除、作废、归档、恢复或历史记录存在，但当前数据、历史和关联数据结果不明确 | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `content` / 对象或规则位置 |
| 26. 唯一性、时间和并发边界可判定（按需） | 唯一性冲突、周期/时区、重复提交或并发更新存在多个合法解释 | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `content` / 规则或操作位置 |
| 27. 文件、导入导出和批量结果完整（按需） | 场景存在但缺范围、格式/大小/数量、上限、部分失败或结果反馈 | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `content` / 对应闭环或页面 |
| 28. 跨系统和产品级质量约束可验收（按需） | 缺事实源、同步方向、失败/部分成功、补偿、最终责任，或产品级质量约束无法观察 | [Design 分析协议](../references/design-analysis-protocol.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `content` / 集成或验收位置 |
| 29. 旧版兼容材料不替代 Design（按需） | 以旧版 metadata、稳定 ID 或历史结构替代人读 Design 判断当前产品事实 | [Design 质量标准](../references/design-quality-rubric.md) | P2；若导致事实冲突则 P1 | `consistency` / 兼容问题 |

## 横切能力、展示与生命周期专项检查

| 检查项 | 触发证据 | 默认严重度 | 输出位置 |
|---|---|---:|---|
| X1. 横切能力事实状态可判断 | 待办、提醒、编号、字典、文件/档案或审计侧/被审侧入口存在，但未区分已定义、局部定义、未定义或冲突 | P1 | `content` / `consistency` |
| X2. 页面展示状态可回读 | 页面缺无权限入口语义、加载中/骨架屏、空态、异常态、超长文本、默认值、标签颜色或筛选保留规则 | P1 | `content` / 页面位置 |
| X3. 状态驱动展示完整 | 状态页面缺可见/置灰/隐藏操作、字段显隐、点击跳转、标签颜色或状态变化后的刷新时机 | P1 | `content` / 页面或状态位置 |
| X4. 自动动作失败闭环 | 自动生成/挂号/归档/迁移只有成功路径，缺失败状态、用户反馈、重试/补偿/人工处理或待确认 | P1 | `content` / 业务闭环 |
| X5. 删除传播可判定 | 删除、软删除、停用、撤回、作废或归档未说明子对象、关联、审批、日志、附件、历史、引用、查询可见性和恢复/审计追溯 | P1 | `content` / 生命周期 |
| X6. 枚举与上限有来源 | 枚举只有“字典/枚举”占位，或分页、导出、批量、首页和文件限制被混成一个未分辨的上限 | P1 | `content` / 规则或页面位置 |
| X7. 操作表交互维度完整 | 操作表缺“入口/触发方式”列或入口未写来源；缺“是否二次确认”“后续去向”列；输入非字段级（粗粒度列法）；存在“字段包括…”描述式字段区块替代字段表 | P1 | `content` / 操作位置 |

## Review 输出要求

- 每项问题写明证据位置、影响对象、严重度和建议的上游同步方向；
- Review 只提出问题和第二意见，不修改 Design、不自动 Fix、不自动确认、不自动推进阶段；
- 缺少适用章节时作为审查问题返回，不再因为“章节不齐”自动把 Review 当作门禁；
- 页面与区块的固定标题、每区块八列字段表和每页面十列操作表是当前正式格式；旧版逐字段属性段落只作为兼容输入，不得在新 Design 中与表格形成第二套事实。
