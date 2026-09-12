# Design Review 检查项

> 本文件只保存 Design 专项检查项映射。通用审查结论、预检查、输出、独立性和停止规则见 [Review 公共执行契约](review-checklist.md)。详细解释按检查项读取 [Design 写作规则](../references/design-writing.md)、[Design 质量标准](../references/design-quality-rubric.md)、[状态定义格式](../references/design-state-format.md) 和 [业务流程格式](../references/design-flow-format.md)。
>
> 当前 Design 的主要读者是产品经理。Design 正文是 PRD 和 Prototype 的唯一产品事实源。页面、区块、字段和操作按业务复杂度选择表达格式（复杂场景推荐八列/十列表格，简单场景使用紧凑清单或结构化段落），固定标题、八列表格和十列表格不再是所有新 Design 的默认硬门槛；只有格式造成事实遗漏、歧义或下游无法承接时才判定问题。旧版宽表和 metadata 只作为兼容材料，不构成当前产品事实源。

## 检查项映射

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 1. 方案摘要可判断 | 缺少问题、方案、结果、范围或重点确认事项，产品经理无法先理解本期要做什么 | [Design 模块模板](../templates/design-module.md)；[设计地图模板](../templates/design-map.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `structure` / 方案摘要 |
| 2. 目标、用户、场景和成功标准完整 | 只有功能清单，缺少用户问题、使用场景、成功判定或失败判定 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 用户、场景与目标 |
| 3. 范围、边界和依赖明确 | 范围外、系统边界、外部责任或限制缺失，导致下游可能重新引入排除项 | [Design 模块模板](../templates/design-module.md)；[设计地图模板](../templates/design-map.md) | P1 | `content` / 摘要或外部协作 |
| 4. 关键业务闭环可走完 | 缺触发、参与者、阶段、分支、结果、恢复或后续责任 | [Design 写作规则](../references/design-writing.md)；[业务流程格式](../references/design-flow-format.md) | P1 | `content` / 业务闭环 |
| 5. 简单流程不过度展开 | 单角色、无分支、无异常的流程被强制拆成无意义的空表格或重复步骤 | [业务流程格式](../references/design-flow-format.md) | P2 | `content` / 业务闭环 |
| 6. 对象、规则和状态互相解释 | 核心对象关系、生命周期、规则、状态或责任之间存在断链 | [Design 分析协议](../references/design-analysis-protocol.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `consistency` / 业务模型 |
| 7. 状态机结构闭环 | 非终态无出路、非初始态无入路、回退目标非法或迁移含义不明确 | [状态定义格式](../references/design-state-format.md) | P1 | `content` / 状态位置 |
| 8. 状态条件和副作用完整 | 缺触发角色、前置条件、可逆性、限制条件、数据变化或异常处理 | [状态定义格式](../references/design-state-format.md) | P1 | `content` / 状态迁移 |
| 9. 权限和数据范围可执行 | 只有角色列表，没有可见范围、可执行动作、字段例外或敏感操作限制 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 权限与数据范围 |
| 10. 页面核心属性完整 | 页面缺少核心目的、适用角色、进入条件或数据范围，导致无法判断使用边界；不适用属性合理省略不判错 | [Design 模块模板](../templates/design-module.md)；[设计地图模板](../templates/design-map.md)；[Design 写作规则](../references/design-writing.md) | P1 | `structure` / 页面位置 |
| 11. 区块按用户任务组织 | 区块按数据库表、接口或技术模块拆分，或区块没有明确目的 | [Design 写作规则](../references/design-writing.md) | P2 | `content` / 区块位置 |
| 12. 字段事实完整 | 缺业务含义、字段来源、展示条件、输入与编辑、取值与默认、交互方式或校验反馈等实际适用事实，或用模糊词替代；格式适配复杂度，不因未用八列表自动判错 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 字段位置 |
| 13. 操作事实与结果闭环 | 只有按钮名，缺适用角色、入口/触发方式、可用条件、确认、成功结果、数据/状态变化、失败恢复或后续去向等实际适用事实；操作输入粗粒度导致下游无法承接；格式适配复杂度，不因未用十列表自动判错 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 操作位置 |
| 14. 产品字段使用业务名称 | 用数据库字段名、内部编号或技术类型替代中文业务名称 | [Design 写作规则](../references/design-writing.md) | P2 | `content` / 字段位置 |
| 15. 页面与字段落点存在 | 用户可见、可编辑、可筛选或动作直接依赖的字段没有页面、区块落点 | [Design 写作规则](../references/design-writing.md) | P1 | `consistency` / 字段落点 |
| 16. 页面落点不引入未定义字段 | 页面、区块或操作出现没有正式定义的产品字段 | [Design 写作规则](../references/design-writing.md) | P1 | `consistency` / 页面位置 |
| 17. 非页面字段例外合理 | 内部字段未说明原因，或可见/可编辑/可筛选字段被错误归入内部字段 | [Design 模块模板](../templates/design-module.md)；[设计地图模板](../templates/design-map.md) | P1 | `consistency` / 非页面落点字段 |
| 18. 页面清单与正式页面一致 | 页面速览有页面未展开，或正式页面不在清单中且造成覆盖歧义 | [Design 模块模板](../templates/design-module.md)；[设计地图模板](../templates/design-map.md) | P1 | `consistency` / 页面位置 |
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

专项检查按触发证据启动，无对应业务事实时不预设存在，不因缺少不适用章节判错：

| 检查项 | 触发证据 | 默认严重度 | 输出位置 |
|---|---|---:|---|
| X1. 横切能力事实状态可判断 | 需求或正文中实际涉及待办、提醒、编号、字典、文件/档案或多侧入口等横切能力时，未区分已定义、局部定义、未定义或冲突；无相关业务时不触发 | P1 | `content` / `consistency` |
| X2. 页面展示状态可回读 | 需求或页面实际涉及关键展示状态（空态、无权限、异常态、超长文本、默认值），但缺产品口径；无相关场景时不触发 | P1 | `content` / 页面位置 |
| X3. 状态驱动展示完整 | 页面实际存在业务状态流转并驱动展示变化，但缺操作显隐/置灰、字段显隐或状态变化后的刷新说明；无状态流转时不触发 | P1 | `content` / 页面或状态位置 |
| X4. 自动动作失败闭环 | 业务实际存在自动生成/挂号/归档/迁移等系统动作，但只有成功路径，缺失败状态、用户反馈、重试/补偿/人工处理或待确认；无自动动作时不触发 | P1 | `content` / 业务闭环 |
| X5. 删除传播可判定 | 业务实际涉及删除、软删除、停用、撤回、作废或归档等破坏性/生命周期变更，未说明关联影响与审计追溯；无删除类操作时不触发 | P1 | `content` / 生命周期 |
| X6. 枚举与上限有来源 | 业务实际涉及枚举选项、分页、导出或批量处理，但只有占位符或未明确上限；无相关操作时不触发 | P1 | `content` / 规则或页面位置 |
| X7. 操作交互维度完整 | 实际存在的操作缺入口/触发方式、是否二次确认、后续去向或字段级输入，导致动作不闭环；简单单步操作不强制使用十列宽表，事实清晰即可 | P1 | `content` / 操作位置 |
| X8. 推断值未随正文落实 | 正文出现默认值/排序/分页/提示文案/标签颜色等可推断值时未写清取值依据；高影响项（权限/状态机/删除传播/外部系统）被当推断值静默写入 | P1 | `content` / `consistency` |

## Review 输出要求

- 每项问题写明证据位置、影响对象、严重度和建议的上游同步方向；
- Review 只提出问题和第二意见，不修改 Design、不自动 Fix、不自动确认、不自动推进阶段；
- 缺少适用章节时作为审查问题返回，不再因为“章节不齐”自动把 Review 当作门禁；
- 页面、区块、字段和操作按业务复杂度表达，事实完整优先于表格形式。复杂页面的八列字段表和十列操作表是推荐格式；简单页面可使用紧凑短表或结构化段落。不因格式未采用宽表判定缺陷，但事实遗漏、歧义或导致下游无法承接时按 P1 判定；
- **合理不适用判定**：结合需求目标、范围和业务场景判断，不因章节缺失自动判错。无状态机、无外部系统、无删除类操作的需求，简短说明或省略属合理不适用；
- **高影响未决处理**：高影响未决事项已明确记录（写明问题、影响范围、保守表达和确认人）且局部阻塞时，不把未决本身判定为缺陷；若受影响内容仍被正文静默拍板，则按 P1 判定；
- **双下游对照（用户明确要求时）**：对照 PRD 和 Prototype 检查事实一致性，区分 Design 缺失、PRD/Prototype 偏离和需要回写 Design 的问题，给出修改建议，不直接修改产物。
