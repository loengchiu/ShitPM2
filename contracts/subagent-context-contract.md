# Sub-agent 上下文契约

## 目的

本契约限制 Sub-agent 在 ShitPM Design / PRD 执行中的输入、输出和权限。Sub-agent 是可选的内部执行机制，不是产品完成证明，也不是首次生成的必需前置。

## 默认策略

- 简单模式 Design 和小型 PRD 默认不启用 Sub-agent。
- 只有输入材料多、独立挑战价值明确，或 PRD 规模已经使单次写作明显增加上下文负担且业务模块边界清晰时，才考虑启用。原先的“10 页或 50 个字段”仅可作为经验参考，不是硬门槛，也不替代主 Agent 对模块边界和上下文预算的判断。
- 主 Agent 始终持有最终产品事实、跨模块业务模型、来源冲突处理和最终写入权。

## 允许角色

### Material Reader

输入只能是明确指定的一份或一组原始材料，以及事实提取要求。输出必须逐条带来源路径和可定位证据，分为已确认事实、来源冲突、缺失信息和不可直接推导项。不得做最终产品决策，不得把推测写成事实。

### Design Challenger

输入是原始证据、Design 草稿、适用场景卡和挑战要求。输出只能是缺陷、影响对象、证据位置、可否由已确认事实修正、是否需要用户确认和是否阻止写作。不得直接修改 Design，不得输出独立 Review 的正式评分或 verdict。

### PRD Module Writer

输入是全局不变量、单一业务模块的 Design 片段、适用场景卡和必要写作规则。可以产生内部模块草稿，但不得重新定义共享角色、状态、权限、字段、事实源或跨模块规则，不得直接写入或覆盖 `output/prd/prd.md`。

### Module Verifier

输入是对应 Design 模块、PRD 模块草稿和检查清单。输出遗漏、冲突和证据位置，不得静默补充 Design 未确认的高影响事实。

## 角色与 pack 白名单

Sub-agent 请求上下文包时必须同时通过 `context-pack.py --role <role> --pass <pass>` 选择角色和授权 pass；`<role>` 必须使用 manifest `subagent_roles` 的 CLI 键（例如 `material-reader`），不是下表中的显示名称。`--pass` 必须属于该角色在当前阶段的白名单；角色不允许脱离授权 pass 单独指定 pack，越界请求直接失败。装载器依据 `contracts/context-loading.manifest.json` 中的 `subagent_roles` 做确定性校验。

| 角色 | CLI 键 | 阶段与 pass | 允许 pack |
|---|---|---|---|
| Material Reader | `material-reader` | Design `analysis`；PRD `plan` | Design：`design-core`、`design-mode`；PRD：`prd-core`、`prd-writing-structure` |
| Design Challenger | `design-challenger` | Design `challenge` | `design-core`、`design-mode`、`design-cards` |
| PRD Module Writer | `prd-module-writer` | PRD `module` | `prd-core`、`prd-writing-structure`、`prd-writing-action`、`prd-examples`、`prd-cards` |
| Module Verifier | `module-verifier` | PRD `verification` | `prd-core`、`prd-writing-structure`、`prd-writing-action`、`prd-verification` |

角色白名单只约束上下文装载边界，不授予最终产物写入权；Sub-agent 的输出仍须带来源并由主 Agent 复核。

## 采纳规则

- 没有来源路径的输出拒绝采纳。
- Sub-agent 之间结论冲突时，主 Agent 回到原始证据判断，不能用多数投票替代业务证据和用户确认。
- Sub-agent 输出只能进入 `.workflow/runtime/context/<stage>/handoff/`，不得进入最终产品事实目录。
- 最终写作必须重新以原始证据、确认版 Design 和适用规则为依据；交接文件不是事实源。
- Sub-agent 不能绕过确定性检查、confirmation 门或待确认边界。
