# Design 确定性编排动作契约 v2

## 目的

本契约定义 Design 阶段控制平面的接口。编排器使用固定依赖图计算当前全部 `ready_actions[]`；主任务只负责调度、用户提问和完成报告，不自行规划阶段、不重排依赖、不读取专项正文。

## CLI

```text
python scripts/python/design-orchestrator.py init --project-root <path> --request <text> [--mode simple|full] [--materials <path>]
python scripts/python/design-orchestrator.py next --project-root <path>
python scripts/python/design-orchestrator.py accept --project-root <path> --action-id <id> [--result success|failure] [--error <text>] [--fingerprint <hash>]
python scripts/python/design-orchestrator.py answer --project-root <path> --question-id <id> --answer <text>
python scripts/python/design-orchestrator.py status --project-root <path>
```

未指定模式时只返回一次 `select-mode`；不能根据材料自动判断。`next` 的主结果为：

```json
{
  "state": "ready",
  "ready_actions": [],
  "blocked_by_user_questions": [],
  "completed_actions": []
}
```

## 动作字段

每个动作必须包含：

- `action_id`、`task_id`：稳定的动作和任务标识；
- `type`、`role`、`objective`、`task_kind`：执行责任；
- `mode`、`depends_on`、`batch_key`：模式、依赖和并行批次；
- `input_files`、`input_hashes`：只读输入白名单及生成时哈希；
- `rule_pack_ref`：规则包内容哈希和缓存引用；
- `expected_outputs`、`output_schema`、`completion_check`：输出边界；
- `forbidden_inputs`、`allowed_evidence_ranges`：上下文隔离边界；
- 隔离动作必须带 `fork_context=false`。

动作说明同时写入 JSON 任务卡和 Markdown 阅读卡；Markdown 不是事实源，JSON 是程序校验依据。可执行字段约束统一加载 `schemas/design-orchestration-action.schema.json`，本契约只描述控制平面语义和执行边界。专项只返回短回执，分析正文写入声明的输出文件。

## 模式

- 简单模式只执行材料准备、`simple-design`、生成内检查、必要的局部修复、索引和完成报告；
- 完整模式执行 A、B、C 依赖图，由单一、全新上下文的 `design-editor` 统一写作；A/B/C 专项同批动作通过 `ready_actions[]` 并行；
- 三类生成内检查可以同批并行，默认不生成独立第四次成品审查；
- 确定性动作不计模型调用，零模型伪造宿主也不能冒充真实宿主证据。

## 局部失效与恢复

材料、用户回答、输入哈希或上游输出变化时，只让受影响节点及其下游重新就绪。单节点失败不撤销同批其他已完成节点；重试达到上限只阻断受影响路径。状态文件丢失时应根据现有产物和输入哈希恢复，读取旧版 `run.json` 时返回 `migration_required`，不自动迁移。
