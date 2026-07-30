# Design 编排动作契约 v2

## 目的

本契约定义 Design 阶段的最小调度接口。编排器负责 Align 必经顺序、材料事实保留、模式选择、A/B/C 顺序、用户问题暂停与回答、输入版本失效、断点恢复和必需输出存在性；它不负责证明产品判断正确。

## CLI

```text
python scripts/python/design-orchestrator.py init --project-root <path> --request <text> [--mode simple|full] [--materials <path>]
python scripts/python/design-orchestrator.py next --project-root <path>
python scripts/python/design-orchestrator.py accept --project-root <path> --action-id <id> [--result success|failure] [--error <text>] [--fingerprint <hash>]
python scripts/python/design-orchestrator.py answer --project-root <path> --question-id <id> --answer <text>
python scripts/python/design-orchestrator.py status --project-root <path>
```

未指定模式时只返回一次 `select-mode`；不能根据材料自动判断。旧运行若仍声明不支持的模式，返回错误并要求重新初始化，不自动迁移或静默映射。

## 任务图

Align 是 Design 的首个必经分析责任，不等于必须存在原始材料。材料索引可以复用，但首次执行和输入变化时不能让它绕过 Align。

简单模式：

```text
align → material-index（有材料时）→ material-facts:*（有材料时）→ material-merge → simple-design
```

完整模式：

```text
align → material-index（有材料时）→ material-facts:*（有材料时）→ material-merge → a-layer → b-layer → c-layer → design-editor
```

当前实现可以把材料索引和合并动作作为零材料路径的轻量确定性动作；必须满足：`source_count=0` 合法、有材料时逐来源保留事实、Design 至少读取 Align 完整结果和详细事实资产、完整模式不跳过 A/B/C。不得恢复 Park 的细粒度任务图、固定确认点或完整度检查器。

`material-facts:*` 按材料来源可并行执行；Align 需要高影响回答时，Design 在当前任务内暂停，回答写回后从受影响动作继续。

## 动作字段

每个动作必须包含：

- `action_id`、`task_id`：稳定标识；
- `type`、`role`、`objective`、`task_kind`：执行责任；
- `mode`、`depends_on`、`batch_key`：模式、依赖和并行批次；
- `input_files`、`input_hashes`：允许读取的输入及版本；
- `rule_pack_ref`：规则包内容哈希和缓存引用；
- `expected_outputs`、`output_schema`、`completion_check`：输出边界；
- `forbidden_inputs`、`allowed_evidence_ranges`：上下文边界；
- 隔离动作带 `fork_context=false`；
- 材料索引动作声明 `command`，由宿主执行确定性脚本。

动作卡同时写入 JSON 与 Markdown；JSON 是程序读取依据。Align 使用 `templates/align.md` 和 `schemas/align-notes.schema.json`；材料事实和 A/B/C 基线遵循对应 references 格式；中间输出只需满足当前动作可读取、依赖存在且输入未陈旧。

## 完成语义

一个动作接受时只检查：

1. 声明的输出文件存在且可读取；
2. 动作输入哈希仍与当前用户回答、材料和依赖输出一致；
3. 完整模式的 `design-editor` 已具备 A/B/C 基线输出。

`simple-design` 和 `design-editor` 的一次来源回读、跨层自检和必要修正属于写作动作本身，不生成独立检查 JSON，不由编排器或确认工具重复证明。所有必需任务完成后，`next` 直接返回 `state=completed`。

## 用户问题与回答写回

当 Align、A 层或其他动作发现高影响事实无法安全推导时，写入用户问题并暂停。用户回答后必须写入 `.workflow/runtime/inputs/user-decisions.json`，同时更新当前 Align 结果；受影响动作及其下游根据输入哈希重新就绪。未回答的问题不能静默变成已确认事实。

## 失效与恢复

用户原话、材料、用户回答、输入哈希或上游输出变化时，只让受影响节点及其下游重新就绪；材料变化时先使 Align 失效。中断后根据实际产物、输入哈希和收据恢复，不因状态文件存在就把缺失的分析视为完成。状态文件丢失时根据现有产物与输入哈希恢复；读取旧版 `run.json` 时返回 `migration_required`，不自动迁移。

编排器不判断业务流程是否合理、字段是否完整、权限是否正确、ABC 语义是否优秀或 Design 是否足够可评审；不生成 Design 索引、生成后检查报告、综合回执，不运行 Review，不执行状态机或上下文结构门禁，也不自动确认或启动 PRD/Prototype。
