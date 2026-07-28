---
name: spm-start
description: "ShitPM 项目启动与导航——只读扫描当前产物、Design confirmation 和可用动作。用于用户要求查看项目状态、下一步、可用 Skill 或当前阶段时；不修改文件，不给唯一下一步。"
---

## 路径与资源

从系统 prompt 读取 `$BUNDLE`。项目文件使用当前项目根目录；bundle 资源使用 `$BUNDLE/contracts/start-action-matrix.md`、`$BUNDLE/templates/start-report.md`、`$BUNDLE/scripts/python/stage-context.py` 和 `design-confirmation.py`。

## 职责边界

`spm-start` 只读导航，不做需求判断、写作质量判断、Review 或修复。

- 不修改 `status.json`、产物、metadata、Review 结果或 confirmation。
- 展示所有当前可用动作，不按线性阶段给唯一下一步。
- Design confirmation 必须单独展示。
- PRD 和 Prototype 作为 Design 的两个并列下游展示。
- 旧 metadata 和旧 Review 记录只用于导航参考，不作为产品事实源。

## 执行流程

1. 读取 `.workflow/status.json`、`output/` 产物和最近 Review（如存在）。
2. 有 `status.json` 时运行：

   ```text
   python $BUNDLE/scripts/python/stage-context.py --project-root .
   ```

   使用脚本输出的产物状态、`available_actions` 和 `design_confirmation`。

3. 没有 `status.json` 时扫描 `output/`，按 `$BUNDLE/contracts/start-action-matrix.md` 判断可用动作；不创建 `status.json`。
4. JSON 解析失败时展示损坏文件的前 500 字符，建议手动修复或删除后重新扫描，停止执行。
5. 状态与产物不一致时列出不一致项，给出回退状态或补建产物两种建议，停止执行。
6. 读取 `$BUNDLE/contracts/start-action-matrix.md` 中的动作级默认建议，根据实际任务复杂度为每个可用动作输出模型等级和推理深度；无法判断时建议深度推理模型。模型在动作开始前选择，执行中不切换。
7. 按 `$BUNDLE/templates/start-report.md` 输出项目状态、产物清单、最近 Review、可用动作和建议。
8. 输出后停止。

## Design confirmation

需要时运行：

```text
python $BUNDLE/scripts/python/design-confirmation.py --project-root . check
```

- `0`：已确认且哈希一致。
- `2`：Design 已修改，旧确认失效；PRD 和 Prototype 不可用。
- `3`：无确认记录，按未确认处理。

## 动作矩阵

完整可用动作矩阵、Design confirmation 规则和动作级模型建议只读取 `$BUNDLE/contracts/start-action-matrix.md`，不要在 Skill 中复制。该矩阵保留 `/spm-prototype-mark` 的兼容动作行；本轮不修改该 Skill。

## 硬规则

- 不自动修复路径 C/D。
- 不修改任何文件。
- 不把 Review 通过当成 Design confirmation。
- 不把 PRD 当作 Prototype 的前置，或把 Prototype 当作 PRD 的前置。
