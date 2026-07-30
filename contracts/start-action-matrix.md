# 启动动作判定契约

## 可用动作矩阵

| 产物状态 | Design 确认 | 可用动作 |
|---------|------------|---------|
| 全空 | — | `/spm-align`、`/spm-design`（Design 内先完成 Align） |
| 仅 Align | — | `/spm-design` |
| Design 存在 | 未确认 | `confirm-design`、`/spm-design`（修改）、`/spm-design-review` |
| Design 存在 | 已确认 | `/spm-prd`、`/spm-prototype`、`/spm-design-review`、`confirm-design`（重新确认） |
| Design + PRD | 已确认 | `/spm-prototype`、`/spm-prd-review`、`/spm-design-review` |
| Design + Prototype | 已确认 | `/spm-prd`、`/spm-prototype-review`、`/spm-design-review` |
| Design + PRD + Prototype | 已确认 | `/spm-prd-review`、`/spm-prototype-review`、`/spm-design-review`、`/spm-fix`、`/spm-prototype-mark` |


## 每个动作的运行时模型建议（动作级模型建议）

`spm-start` 必须为每个可用动作输出实际模型等级和推理深度建议；下面是默认建议，运行时可根据任务复杂度调整，但不能省略动作级建议。

| 动作 | 默认建议 | 可使用轻量模型的条件 |
|---|---|---|
| `/spm-align` | 视任务而定 | 目标、范围和边界已明确，仅需整理材料 |
| `/spm-design` | 深度推理模型 | 业务简单、输入完整、无方案权衡、角色/状态/权限关系简单 |
| `/spm-prd` | 根据确认版 Design 判断 | Design 决策完整，主要按既有模板展开明确规格 |
| `/spm-prototype` | 根据交互和实现复杂度判断 | 页面少、路径单一、行为明确，主要做既定表达与实现 |
| `/spm-design-review` | 深度推理模型 | 只做结构和明确规则检查时可用轻量模型或脚本 |
| `/spm-prd-review` | 深度推理模型 | 只做结构和明确规则检查时可用轻量模型或脚本 |
| `/spm-prototype-review` | 深度推理模型 | 只做结构和明确规则检查时可用轻量模型或脚本 |
| `/spm-fix` | 根据变更影响判断 | 修改范围、正确结果和受影响位置都明确 |
| `/spm-prototype-mark` | 轻量模型 | 主动发现产品或交互问题时另行使用深度 Review |

无法判断任务复杂度时建议深度推理模型。模型在动作开始前选择，执行中不切换。

## Design confirmation 状态

使用：

```text
python $BUNDLE/scripts/python/design-confirmation.py --project-root . check
```

- 退出码 `0`：已确认且哈希一致。
- 退出码 `2`：`design.md` 已修改，旧确认失效；PRD 和 Prototype 不可用，需重新确认。
- 退出码 `3`：无确认记录，按未确认处理。

## 约束

- `spm-start` 只读取和展示，不修改 `status.json`、产物或 confirmation。
- `PRD` 和 `Prototype` 是 Design 的并列下游，不互相构成前置。
- 旧 metadata 和旧 Review 记录不作为主流程事实源，也不阻塞导航。
- `/spm-prototype-mark` 行保持兼容；本轮不修改该 Skill。
