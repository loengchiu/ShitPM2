# Design v2 分析交接资产格式

<!-- context:design-asset-contract:start -->

## 适用范围

本格式适用于 A/B/C 基线、`design-brief.json`、`business-conflicts.json` 和
`cross-layer-conflicts.json`。这些文件是动作输出，不是最终 Design 事实源；写入后可由运行时做确定性可读性校验，但校验通过不证明业务质量。动作卡必须同时声明本格式的字段要求。

## 公共 JSON 包装

```json
{
  "schema_version": "design-analysis/v2",
  "task_id": "a-layer",
  "input_fingerprint": "sha256:...",
  "material_revision": "sha256:...",
  "status": "completed",
  "conclusions": [],
  "conflicts": [],
  "questions": [],
  "coverage": ["目标与范围"],
  "source_refs": [],
  "payload": {}
}
```

必须字段：

- `schema_version`：固定为 `design-analysis/v2`；
- `task_id`：当前动作的非空 ID，不得复用上游动作 ID；
- `status`：只能是 `completed`、`success`；
- `coverage`：数组，列出本次实际覆盖的责任范围；
- `source_refs`：数组，列出每个关键结论对应的材料/上游资产证据。没有证据时只能留空并在
  `questions` 或 `conflicts` 中说明原因，不能用空数组掩盖未分析；其中引用材料时应绑定当前 `material_revision`。
- `material_revision`：可选。存在材料输入时填写当前材料版本；无材料时不填写。它与材料事实资产中的 `material_revision` 同名但用途不同：前者绑定本次分析输入，后者绑定事实资产。

`schema_version` 是分析交接资产的格式版本；材料合并事实库的 `version` 是事实库内部版本，二者不互换。分析资产中的 `source_refs` 是结论级证据引用，材料事实中的 `source` 是单条事实的定位对象，二者不要求同形。

`conclusions`、`conflicts`、`questions`、`payload` 按具体动作责任使用；不得把推测写成已确认业务事实，不得把正式 Review 的评分或 verdict 写入基线。完整模式的 A/B/C 必须分别覆盖设计分析协议中与 Park 对齐的责任；页面、字段、操作、规则、状态、异常和验收的重要结论不能只留在基线，必须被 `design-editor` 写入最终 Design 或显式列为待确认。

## 证据引用

`source_refs` 中的每项至少包含 `path`；引用原始材料时应包含 `line_start`、`line_end` 和可核对的
`sha256`，引用上游分析时应包含资产路径和结论定位。行范围必须来自当前材料索引，不能凭空编造。

## 各资产落点

| 资产 | 输出路径 | 责任 |
| --- | --- | --- |
| A 基线 | `context/design/baselines/a-baseline.json` | 用户、目标、场景、范围、成功标准 |
| B 基线 | `context/design/baselines/b-baseline.json` | 流程、对象、规则、状态、权限、数据范围 |
| C 基线 | `context/design/baselines/c-baseline.json` | 页面、字段、操作、异常、验收 |
| Design 简报 | `context/design/baselines/design-brief.json` | 写作所需的合并结论、边界和待确认问题 |
| 业务冲突 | `context/design/conflicts/business-conflicts.json` | B 层冲突、影响对象、证据和处理建议 |
| 跨层冲突 | `context/design/conflicts/cross-layer-conflicts.json` | C 层与 A/B 层的不一致、影响和修复建议 |

## 采纳前检查

模型不能只返回“分析完成”文字；必须把完整 JSON 写入动作卡的 `expected_outputs`。缺少任一公共字段、
版本错误、状态不合法或数组类型错误，均属于输出不合格，应修复当前动作而不是让下游猜测补齐。

<!-- context:design-asset-contract:end -->



