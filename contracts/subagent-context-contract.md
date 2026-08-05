# Sub-agent 上下文契约

## 目的

本契约限制 Sub-agent 在 ShitPM Design / PRD 执行中的输入、输出和权限。Sub-agent 是内部隔离执行机制，不是产品完成证明；简单模式可以不启用，完整模式必须使用 Sub-agent 或等价的新会话隔离材料读取和挑战。

## 默认策略

- 简单模式 Design 和小型 PRD 默认不启用 Sub-agent。
- 完整模式默认启用 Material Reader 和 Design Challenger，以避免主 Agent 上下文膨胀；简单模式和小型 PRD 仍可不启用。所有 PRD 统一分片写作，不按 Design 大小选择“普通/大型”路径；分片边界来自业务闭环，不使用固定页数或字段数作为硬门槛。
- PRD 阶段默认单 Agent 串行分片，不依赖 Sub-agent；宿主支持 Sub-agent 时，只能并行加速材料读取或模块分析，不承担完成条件，也没有最终写入权。
- 主 Agent 始终持有最终产品事实、跨模块业务模型、来源冲突处理和最终写入权。

## 允许角色

### Material Reader

输入只能是项目级 `source-index.json` 命中的明确材料片段、必要原始行范围和事实提取要求；不得接收完整历史对话。输出必须逐条带来源路径和可定位证据，分为已确认事实、来源冲突、缺失信息和不可直接推导项。不得做最终产品决策，不得把推测写成事实。

### Design Challenger（独立挑战角色）

v2 主链不再以 `design-model.json` 作为当前输入。Design Challenger 在 `challenge` pass 中对已通过门禁的 A/B/C baseline、analysis 结果、适用场景卡、必要材料事实和动作卡声明的定点证据做独立挑战；当前编排动作的落点使用 `b-layer` 和 `c-layer`，输出分别进入 `b-baseline.json`、`business-conflicts.json`、`c-baseline.json`、`cross-layer-conflicts.json` 和 `design-brief.json`。具体输入文件、哈希和允许证据范围以动作卡为准，不得接收完整历史对话。输出只能是缺陷、影响对象、证据位置、可否由已确认事实修正、是否需要用户确认和是否阻止写作。不得直接修改 Design，不得输出独立 Review 的正式评分或 verdict。

所有 v2 基线与冲突资产必须遵循 `$BUNDLE/references/design-baseline-format.md`；材料事实必须遵循 `$BUNDLE/references/design-fact-format.md`。动作卡中的 `output_schema` 和 `completion_check` 是执行期约束，不能只依赖模型记忆。

读取旧版兼容性交接包时，才使用 `design-model.json`、`design-challenge.json` 和项目级 `materials/facts.json`；旧版路径不代表 v2 主链输入。

### PRD Module Writer

输入是全局不变量、单一业务模块的 Design 片段、适用场景卡和必要写作规则。只能做并行模块分析，输出带来源的事实要点；不得产生内部模块草稿，不得重新定义共享角色、状态、权限、字段、事实源或跨模块规则，不得直接写入或覆盖 `output/prd/prd.md`。分片正文由主 Agent 直接写入最终 PRD，禁止“草稿全部完成后再整篇重写”的路径。

## 角色与 pack 白名单

Sub-agent 请求上下文包时必须同时通过 `context-pack.py --role <role> --pass <pass>` 选择角色和授权 pass；`<role>` 必须使用 manifest `subagent_roles` 的 CLI 键（例如 `material-reader`），不是下表中的显示名称。`--pass` 必须属于该角色在当前阶段的白名单；角色不允许脱离授权 pass 单独指定 pack，越界请求直接失败。装载器依据 `contracts/context-loading.manifest.json` 中的 `subagent_roles` 做确定性校验。

| 角色 | CLI 键 | 阶段与 pass | 允许 pack |
|---|---|---|---|
| Material Reader | `material-reader` | Design `analysis` | `design-core`、`design-mode` |
| Design Challenger | `design-challenger` | Design `challenge` | `design-core`、`design-mode`、`design-cards` |
| PRD Module Writer | `prd-module-writer` | 仅 PRD `module` | `prd-core`、`prd-writing-structure`、`prd-writing-action`、`prd-cards`、`prd-writing-examples` |

角色白名单只约束上下文装载边界，不授予最终产物写入权；Sub-agent 的输出仍须带来源并由主 Agent 复核。

## 采纳规则

- 没有来源路径的输出拒绝采纳。
- Sub-agent 之间结论冲突时，主 Agent 回到原始证据判断，不能用多数投票替代业务证据和用户确认。
- 材料事实提取结果进入 `.workflow/runtime/materials/facts.json`，必须绑定当前 `material_revision`；Design Challenger 等阶段交接仍只能进入 `.workflow/runtime/context/<stage>/handoff/`，不得进入最终产品事实目录。主 Agent 采纳交接时必须核对来源、版本和体量；`context-runtime-check.py` 仅在当前动作明确需要时作为确定性校验工具使用，不构成独立的 Review 门禁。
- 最终写作必须以项目级材料事实资产、必要的定点原始证据、确认版 Design 和适用规则为依据；运行交接文件不是产品事实源。
- 交接体量上限只用于阻止隔离上下文膨胀，不代表产品完整性、字段数量或业务复杂度门槛。
- Sub-agent 不能绕过确定性检查、confirmation 门或待确认边界。
