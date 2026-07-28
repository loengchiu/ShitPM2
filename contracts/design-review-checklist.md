# Design Review 检查项

> 本文件只保存 Design 专项检查项映射。通用审查结论、预检查、输出、独立性和停止规则见 [Review 公共执行契约](review-checklist.md)。详细解释按检查项读取 [Design 写作规则](../references/design-writing.md)、[状态定义格式](../references/design-state-format.md) 和 [业务流程格式](../references/design-flow-format.md)。

## 检查项映射

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 1. 核心章节覆盖角色、模块、页面、字段、规则/状态和权限 | 章节缺失，或标题存在但没有可定位内容 | [Design 写作规则](../references/design-writing.md)；[Design 模板](../templates/design.md) | P1 | `structure` / 对应章节 |
| 2. 辅助章节只在有真实事实时出现 | 空章节、无事实的“不适用”占位或无关完整模式章节 | [Design 写作规则](../references/design-writing.md) | P2 | `structure` / 对应章节 |
| 3. 关键内容使用结构化表格 | 字段定义、页面落点、状态流转或权限矩阵退化为不可解析的散文/平铺标题 | [Design 模板](../templates/design.md) | P1 | `structure` / 表格位置 |
| 4. 字段定义属性齐全 | 业务字段缺名称、类型、长度、必填、默认值、枚举值、格式、业务来源或说明 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 字段位置 |
| 5. 权限覆盖到字段和敏感操作 | 只有角色列表，没有字段例外、数据范围或敏感操作限制 | [Design 写作规则](../references/design-writing.md) | P1 | `content` / 权限位置 |
| 6. 权限按页面、角色、字段例外组织 | 逐字段重复平铺，无法判断默认规则和例外 | [Design 写作规则](../references/design-writing.md) | P2 | `content` / 权限位置 |
| 7. 状态机结构闭环 | 非终态无出路、非初始态无入路、回退目标非法或迁移含义不明确 | [状态定义格式](../references/design-state-format.md) | P1 | `content` / 状态位置 |
| 8. 状态机业务条件完整 | 缺触发角色、前置条件、可逆性、副作用或异常处理 | [状态定义格式](../references/design-state-format.md) | P1 | `content` / 状态迁移位置 |
| 9. 页面与字段落点存在 | 数据字典字段没有页面、区域或动作落点 | [Design 写作规则](../references/design-writing.md) | P1 | `consistency` / 字段落点 |
| 10. 页面落点不引入未定义字段 | 页面与字段落点出现数据字典未定义字段 | [Design 写作规则](../references/design-writing.md) | P1 | `consistency` / 字段落点 |
| 11. 内部字段明确列入例外 | 内部关联字段、审计字段未说明原因，或可见/可编辑/可筛选字段被错误归入内部字段 | [Design 写作规则](../references/design-writing.md) | P1 | `consistency` / 非页面落点字段 |
| 12. 页面清单与页面落点一致 | 页面清单有页面未展开，或落点章节出现清单外页面 | [Design 写作规则](../references/design-writing.md) | P1 | `consistency` / 页面位置 |
| 13. 状态表达同时包含速览、明细和迁移 | 只有状态集合，或只有迁移列表，无法判断进入/退出条件 | [状态定义格式](../references/design-state-format.md) | P1 | `content` / 状态位置 |
| 14. 多阶段流程按阶段展开 | 多角色、三步以上流程仍为动作流水账或标题平铺 | [业务流程格式](../references/design-flow-format.md) | P1 | `content` / 流程位置 |
| 15. 简单流程不过度展开 | 单角色、无分支、无异常的简单流程被强制拆成无意义的空表格 | [业务流程格式](../references/design-flow-format.md) | P2 | `content` / 流程位置 |
| 16. 关键分支和异常可执行 | 缺具体判断条件、异常结果、回退/中止/补偿或责任人 | [业务流程格式](../references/design-flow-format.md) | P1 | `content` / 流程位置 |
| 17. 业务闭环与系统承接一致 | 流程、角色权限、数据范围、状态、模块边界、跨系统责任或异常路径之间存在断链 | [Design 分析协议](../references/design-analysis-protocol.md)；[Design 写作规则](../references/design-writing.md) | P1 | `consistency` / affected_objects |
| 18. 高影响问题在 Design 阶段暴露 | 产物把高影响决定推迟给 PRD、Prototype 或 Review | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `content` / 审查问题 |
| 19. 未授权高影响假设被显式标记 | Design 静默新增流程、权限、状态、数据范围或跨系统责任 | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `consistency` / 审查问题 |
| 20. Design 不依赖 metadata 判断事实 | 人读 Design 与 metadata 不一致，或 审查者只依据 metadata 加分 | [Design 质量标准](../references/design-quality-rubric.md)；存在旧版 metadata 时读取 [metadata 兼容契约](metadata-anchor-rules.md) | P1 | `consistency` / 审查问题 |
| 21. 旧版 metadata 与人读 Design 一致（按需） | 仅在 `.workflow/metadata/design/` 存在时，字段/页面/模块数量或 page-fields 覆盖不一致 | [metadata 兼容契约](metadata-anchor-rules.md) | P2 | `consistency` / 旧版兼容问题 |
| 22. 旧版非页面字段覆盖合理（按需） | 非页面字段比例异常或例外原因缺失 | [metadata 兼容契约](metadata-anchor-rules.md) | P2 | `consistency` / 旧版兼容问题 |
| 23. 旧版稳定 ID 兼容检查（按需） | 旧 metadata 存在时 ID 前缀/生成关系错误，或正文泄漏稳定 ID | [metadata 兼容契约](metadata-anchor-rules.md) | P2 | `consistency` / 旧版兼容问题 |
| 24. 事实、推导和待确认可区分 | 评审无法判断哪些是输入事实、设计推导或仍需用户决策 | [Design 质量标准](../references/design-quality-rubric.md) | P1 | `content` / 审查问题 |
| 25. 关键动作产品结果闭环 | 动作缺前置条件、影响对象/字段、成功/失败结果、状态副作用、后续责任或恢复路径 | [Design 分析协议](../references/design-analysis-protocol.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `content` / 动作位置 |
| 26. 数据生命周期可判定（按需） | 删除、作废、归档、恢复或历史记录存在，但当前数据、历史和关联数据结果不明确 | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `content` / 对象或规则位置 |
| 27. 唯一性、时间和并发边界可判定（按需） | 唯一性冲突、周期/时区、重复提交或并发更新存在多个合法解释 | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `content` / 规则或动作位置 |
| 28. 文件、导入导出和批量结果完整（按需） | 场景存在但缺范围、格式/大小/数量、上限、部分失败或结果反馈 | [Design 分析协议](../references/design-analysis-protocol.md) | P1 | `content` / 对应闭环位置 |
| 29. 跨系统和产品级质量约束可验收（按需） | 缺事实源、同步方向、失败/部分成功结果、补偿、最终责任，或性能/安全/审计/兼容约束无法验收 | [Design 分析协议](../references/design-analysis-protocol.md)；[Design 质量标准](../references/design-quality-rubric.md) | P1 | `content` / 集成或验收位置 |
