# Prototype Review 检查项

> 本文件只保存 Prototype 专项检查项映射。通用审查结论、预检查、输出、独立性和停止规则见 [Review 公共执行契约](review-checklist.md)。Prototype 以 Design 集合为唯一产品事实体系；PRD 只作为冲突线索。

## 检查项映射

| 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
| --- | --- | --- | --- | --- |
| 1. 页面覆盖逐项输出 | 没有从 Design 页面清单逐项给出 `存在 / 缺失 / 幻觉` 结果 | [Prototype 写作规则](../references/prototype-writing.md)；[Prototype shell 规则](../references/prototype-shell.md) | P1 | `content` / 页面覆盖表 |
| 2. 页面缺失和幻觉分级 | Design 页面缺失率超过 50%，或 Prototype 出现 Design 未定义页面 | [Prototype 写作规则](../references/prototype-writing.md) | P0（超过 50%）/ P1（其他） | `consistency` / affected_objects |
| 3. 页面结构和共享 shell 可用 | 多页面任务中导航、共享布局、激活状态、路由或空白页防护失效 | [Prototype shell 规则](../references/prototype-shell.md) | P1 | `structure` / 页面或路由 |
| 4. 核心状态和主路径可观察 | Design 要求的状态、交互主路径、关键结果或反馈在原型中不可观察 | [Prototype 写作规则](../references/prototype-writing.md) | P1 | `content` / 页面或动作 |
| 5. 角色权限和操作限制可观察 | 角色差异、按钮权限、字段限制或敏感操作限制缺失/冲突 | [Prototype 写作规则](../references/prototype-writing.md) | P1 | `consistency` / 页面或动作 |
| 6. 不引入 Design 未授权高影响行为 | 原型新增页面、状态、权限分支、业务规则、流程、模块边界或跨系统责任 | [Prototype 写作规则](../references/prototype-writing.md)；[同步修复传播规则](fix-propagation-rules.md) | P1 | `consistency` / affected_objects |
| 7. 不静默拍板待确认事实 | Design 的待确认问题在原型中被当成确定行为展示 | [Prototype 写作规则](../references/prototype-writing.md) | P1 | `consistency` / affected_objects |
| 8. Design 优先于 PRD | Prototype 与 PRD/Design 冲突时以 Design 为准，不能使用 PRD 覆盖 Design | [Prototype 写作规则](../references/prototype-writing.md) | P1 | `consistency` / 审查问题 |
| 9. 异常路径和关键反馈可讨论 | 网络、权限、空数据、失败、限制或恢复路径没有可观察表达 | [Prototype 写作规则](../references/prototype-writing.md) | P1 | `content` / 页面或动作 |
| 10. 表现问题与语义问题分离 | 视觉布局问题与产品事实冲突被混在同一修改项，或 Review 自行修复语义 | [Prototype 写作规则](../references/prototype-writing.md)；[同步修复传播规则](fix-propagation-rules.md) | P2 | `content` / 审查问题 |
| 11. 源码工程完整 | 只有 dist/compiled.js 没有 src；package.json、构建脚本或路由注册表缺失；src 引用 dist 或 prototype-p0；存在 module-*.compiled.js 补丁链 | [Prototype 源码工程检查](../scripts/python/prototype-source-check.py) | P1（不得通过） | `structure` / affected_objects |
| 12. 构建与构建预览可用 | `npm run build` 失败；构建预览中默认页或注册路由白屏、console 报错 | [Prototype 写作规则](../references/prototype-writing.md) | P1 | `structure` / 页面或路由 |
| 13. Review 只读边界 | Review 手工修改 src、dist 或其他原型文件，或把构建产物当作修改输入 | [Prototype 写作规则](../references/prototype-writing.md) | P1 | `structure` / 审查问题 |
| 14. 视觉事实源被读取执行 | 页面视觉值、页面骨架未按 [Prototype 视觉规范](../references/prototype-visual-spec.md) 与 `tablerTokens.ts` 执行，页面现场拍值 | [Prototype 视觉规范](../references/prototype-visual-spec.md)；[Prototype 写作规则](../references/prototype-writing.md) | P2 | `content` / 页面或元素 |
| 15. 共享 UI 使用与局部硬编码 | 高频结构未复用 `src/shared/ui/`，页面复制整套局部 Tabler CSS 或 style 硬编码视觉值 | [Prototype 视觉规范](../references/prototype-visual-spec.md) | P2 | `content` / 页面或元素 |
| 16. 状态矩阵可观察 | 视觉规范组件状态矩阵中的 default/hover/focus/active/selected/disabled/readonly/loading/empty/error/forbidden 有应有状态不可观察，或仍用“（只读）/（必填）”文字代替 UI 状态 | [Prototype 视觉规范](../references/prototype-visual-spec.md) | P2 | `content` / 页面或动作 |
| 17. 图标与图表统一 | 混用 `@ant-design/icons`，未用 `@tabler/icons-react`；图表残留 Arco 色板 / 主题命名，未用 `shared/charts/TablerChart.jsx` | [Prototype 视觉规范](../references/prototype-visual-spec.md) | P2 | `content` / 页面或图表 |
| 18. 组件行为规范执行 | 适用组件行为边界未满足，或页面复制共享 UI 已承担的实现；以真实源码场景和浏览器证据判断，不凭搜索命中判定 | [组件行为规范](../references/prototype-component-behavior.md)；[Prototype 视觉规范](../references/prototype-visual-spec.md) | P2 | `content` / 页面或元素 |
| 19. 跨层运行时契约 | 可见操作无结果；Form 缺少稳定 name/rules 或页面外 ActionBar 未真实提交/重置；Hash query 被丢弃或同路径 query 不更新；row/action/menu/field 以文案或下标作身份；共享 wrapper 静默丢失 locale/scroll/pagination；Modal/message/notification 未使用统一上下文；Portal、Sider 遮罩、sticky ActionBar 或 <576/576–991/≥992/≥1200 边界组合失效 | [Prototype 写作规则](../references/prototype-writing.md)；[组件行为规范](../references/prototype-component-behavior.md)；[Prototype 视觉规范](../references/prototype-visual-spec.md) | P1 | `structure` / `content` / affected_objects |
