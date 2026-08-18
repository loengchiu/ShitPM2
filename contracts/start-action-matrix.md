# 启动动作判定契约

## 可用动作矩阵

| 产物状态 | 可用动作 |
|---------|---------|
| 全空 | /spm-align、/spm-design（Design 内先完成 Align） |
| 仅 Align | /spm-design |
| Design 集合存在（设计地图 + 设计集清单） | /spm-prd、/spm-prototype、/spm-design、/spm-design-review |
| Design + PRD | /spm-prototype、/spm-prd-review、/spm-design-review |
| Design + Prototype | /spm-prd、/spm-prototype-review、/spm-design-review |
| Design + PRD + Prototype | /spm-prd-review、/spm-prototype-review、/spm-design-review、/spm-fix、/spm-prototype-mark |

Design 修改状态（活动事务）和下游受影响模块由 stage-context.py 输出；存在活动事务时 PRD、Prototype、Review 和 fix 不读取正在变化的 Design 集合，先执行 recover。

## 每个动作的运行时模型建议（动作级模型建议）

spm-start 必须为每个可用动作输出实际模型等级和推理深度建议；下面是默认建议，运行时可根据任务复杂度调整，但不能省略动作级建议。

| 动作 | 默认建议 | 可使用轻量模型的条件 |
|---|---|---|
| /spm-align | 视任务而定 | 目标、范围和边界已明确，仅需整理材料 |
| /spm-design | 深度推理模型 | 业务简单、输入完整、无方案权衡、角色/状态/权限关系简单 |
| /spm-prd | 根据 Design 决策完整性判断 | Design 决策完整，主要按既有模板展开明确规格 |
| /spm-prototype | 根据交互和实现复杂度判断 | 页面少、路径单一、行为明确，主要做既定表达与实现 |
| /spm-design-review | 深度推理模型 | 只做结构和明确规则检查时可用轻量模型或脚本 |
| /spm-prd-review | 深度推理模型 | 只做结构和明确规则检查时可用轻量模型或脚本 |
| /spm-prototype-review | 深度推理模型 | 只做结构和明确规则检查时可用轻量模型或脚本 |
| /spm-fix | 根据变更影响判断 | 修改范围、正确结果和受影响位置都明确 |
| /spm-prototype-mark | 轻量模型 | 主动发现产品或交互问题时另行使用深度 Review |

无法判断任务复杂度时建议深度推理模型。模型在动作开始前选择，执行中不切换。

## Design 存在性判断

使用：

~~~text
python $BUNDLE/scripts/python/stage-context.py --project-root .
~~~

- 输出 design_change（活动事务）和 downstream_impact（受影响下游模块）；
- Design 存在性以设计地图与设计集清单为准，不再使用确认标记或哈希。

## 约束

- spm-start 只读取和展示，不修改 status.json、产物或 Design 修改事务。
- PRD 和 Prototype 是 Design 的并列下游，不互相构成前置。
- 旧 metadata 和旧 Review 记录不作为主流程事实源，也不阻塞导航。
- /spm-prototype-mark 行保持兼容。
