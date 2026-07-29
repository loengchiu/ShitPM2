# Design 完整模式上下文提速方案

日期：2026-07-29
状态：暂缓；由材料摄取编排讨论稿重新审议

## 1. 根因

真实运行记录显示，工具执行时间不是主要瓶颈；主要耗时来自同一主 Agent 长对话持续携带完整历史、反复全文读取 V1/Skill/模板/Design，以及自动压缩后继续在同一上下文中工作。上下文压缩三次是上下文压力的证据，但不是优化目标本身。优化目标是让压缩前的输入规模保持有界。

## 2. 目标

- 完整模式 Design 的主模型单次输入尽量不超过 50,000 token；
- 原始材料全文扫描次数不超过 1 次；
- 阶段之间不传递完整历史对话；
- 材料事实、业务模型、挑战结果均可定位来源；
- `context-pack` 和确定性检查不成为新的耗时瓶颈；
- 不使用 Hook，不改变最终产品产物结构。

## 3. 方案

采用“索引 + 隔离读取 + 有界 handoff + 最终写入权集中”的流水线：

```text
确定性材料索引
  -> Material Reader：只提取带来源事实
  -> 主 Agent：统一业务建模
  -> Design Challenger：独立挑战模型
  -> 主 Agent：写入 Design
  -> 独立验证 + 确定性检查
```

主 Agent 保留最终业务模型、冲突裁决、待确认项和 Design 写入权；隔离角色不能修改最终产物，也不能把推测写成事实。

## 4. 运行时文件

```text
.workflow/runtime/context/design/source-index.json
.workflow/runtime/context/design/source-index.md
.workflow/runtime/context/design/handoff/material-facts.json
.workflow/runtime/context/design/handoff/design-model.json
.workflow/runtime/context/design/handoff/design-challenge.json
.workflow/runtime/metrics/*.json
```

交接文件只用于执行、导航、校验和审计，不成为 Design、PRD 或 Prototype 的事实源。

## 5. 失败与恢复

- 索引缺失、来源哈希变化或行范围不可读：停止当前 pass，重新生成索引；
- handoff 缺少来源、类别或超过预算：拒绝采纳，不进入写作；
- challenge 失败：允许主 Agent基于现有模型继续，但必须把失败记录为运行指标，并不得假装完成独立挑战；
- 任一阶段重跑只重建该阶段输入，不恢复完整历史对话。

## 6. 验收

使用同一固定样例连续运行三次，分别记录机器运行时间和用户确认等待时间。目标为完整模式 Design P50 不超过 10 分钟、P90 不超过 12 分钟；运行包和检查总耗时不超过 2 分钟。若未达到，继续定位模型调用和输入体量，不通过增加压缩次数掩盖问题。
