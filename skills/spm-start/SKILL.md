---
name: spm-start
description: "ShitPM 项目启动与导航——只读扫描当前产物、Design 修改状态、下游受影响状态和可用动作。用于用户要求查看项目状态、下一步、可用 Skill 或当前阶段时；不修改文件，不给唯一下一步。"
---

## 路径与资源

从系统 prompt 读取 $BUNDLE。项目文件使用当前项目根目录；bundle 资源使用 $BUNDLE/contracts/start-action-matrix.md、$BUNDLE/templates/start-report.md 和 $BUNDLE/scripts/python/stage-context.py。

## 职责边界

spm-start 只读导航，不做需求判断、写作质量判断、Review 或修复。

- 不修改 status.json、产物、metadata、Review 结果或 Design 修改事务。
- 展示所有当前可用动作，不按线性阶段给唯一下一步。
- Design 修改状态（活动事务）和下游受影响模块必须单独展示。
- PRD 和 Prototype 作为 Design 的两个并列下游展示。
- 旧 metadata 和旧 Review 记录只用于导航参考，不作为产品事实源。
- 不读取详细模块 Design 正文，不计算全部文件指纹。

## 执行流程

1. 读取 .workflow/status.json、output/ 产物和最近 Review 人读文件（.workflow/reviews/<stage>-review-N.md，如存在）。
2. 有 status.json 时运行：

   ~~~text
   python $BUNDLE/scripts/python/stage-context.py --project-root .
   ~~~

   使用脚本输出的产物状态、available_actions、design_change 和 downstream_impact。

3. 没有 status.json 时扫描 output/，按 $BUNDLE/contracts/start-action-matrix.md 判断可用动作；不创建 status.json。
4. JSON 解析失败时展示损坏文件的前 500 字符，建议手动修复或删除后重新扫描，停止执行。
5. 状态与产物不一致时列出不一致项，给出回退状态或补建产物两种建议，停止执行。
6. 读取 $BUNDLE/contracts/start-action-matrix.md 中的动作级默认建议，根据实际任务复杂度为每个可用动作输出模型等级和推理深度；无法判断时建议深度推理模型。模型在动作开始前选择，执行中不切换。
7. 按 $BUNDLE/templates/start-report.md 输出项目状态、产物清单、最近 Review、Design 修改状态、下游受影响模块、可用动作和建议。
8. 输出后停止。

完成判据：当前产物、Design 修改状态、下游受影响模块、可用动作已扫描并输出；未修改任何文件；未给唯一下一步。

## Design 状态

Design 存在性以设计地图与设计集清单为准；不再有确认动作。存在活动事务（design_change.active=true）时提示先执行 design-set.py recover；下游受影响模块（downstream_impact）逐项列出。

## 动作矩阵

完整可用动作矩阵、Design 状态规则和动作级模型建议只读取 $BUNDLE/contracts/start-action-matrix.md，不在 Skill 中复制。

## 硬规则

- 不自动修复路径 C/D。
- 不修改任何文件。
- 不把 Review 通过当成 Design 状态。
- 不把 PRD 当作 Prototype 的前置，或把 Prototype 当作 PRD 的前置。
