---
name: spm-start
description: "启动阶段——vNext：识别当前状态和可用动作，不做产品判断，不修改产物。展示 PRD 和 Prototype 两个独立动作，并为每个可用动作附带模型等级和推理深度建议。不按固定线性阶段只给唯一下一步。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 职责定位

- 只负责识别当前状态和可用动作
- 不做产品判断、不修改产品产物
- 不按固定线性阶段只给唯一下一步
- 同时展示 PRD 和 Prototype 两个独立动作
- 展示 Design 确认状态
- 为每个可用动作附带模型等级和推理深度建议

## 输入事实源

读取以下文件（不存在时按"无"处理，不阻断输出）：

1. `.workflow/status.json`（可选；不存在时仍能输出）
2. `output/align/align.md`（可选）
3. `output/design/design.md`（可选）
4. `output/prd/prd.md`（可选）
5. `output/prototype/index.html` 或 `output/prototype/` 下 `.html` 文件（可选）
6. `.workflow/confirmations/design.json`（可选）
7. `.workflow/reviews/` 下最近 review（可选，仅作为参考，不作为准入依据）

## 执行路径

### 路径 A：有 status.json

1. 运行 `python $BUNDLE/scripts/python/stage-context.py --project-root .`
2. 直接引用脚本输出的 `available_actions` 列表，展示所有可用动作
3. 引用 `design_confirmation` 字段展示 Design 确认状态
4. JSON 解析失败 → 路径 C
5. 状态与产物不一致 → 路径 D

### 路径 B：无 status.json（新项目/扫描）

按"可用动作判定矩阵"扫描 `output/` 产物判断当前可用动作。**不创建** `status.json`（由 writer 阶段首次产出时创建）。

### 路径 C：JSON 解析失败

告知损坏，展示前 500 字符。建议手动修复或删除走路径 B。停止，不自动修复。

### 路径 D：状态与产物不一致

列出不一致项，给出两种处理建议：① 回退 status.json current_stage ② 补建缺失产物。停止，等用户决定。

## 可用动作判定矩阵

| 产物状态 | Design 确认 | 可用动作 |
|---------|------------|---------|
| 全空 | — | `/spm-align`（可选）、`/spm-design` |
| 仅 align | — | `/spm-design` |
| design 存在 | 未确认 | `confirm-design`、`/spm-design`（修改）、`/spm-design-review` |
| design 存在 | 已确认 | `/spm-prd`、`/spm-prototype`、`/spm-design-review`、`confirm-design`（重新确认） |
| design + PRD | 已确认 | `/spm-prototype`、`/spm-prd-review`、`/spm-design-review` |
| design + Prototype | 已确认 | `/spm-prd`、`/spm-prototype-review`、`/spm-design-review` |
| design + PRD + Prototype | 已确认 | `/spm-prd-review`、`/spm-prototype-review`、`/spm-design-review`、`/spm-fix`、`/spm-prototype-mark` |

Design 哈希一致性通过 `python $BUNDLE/scripts/python/design-confirmation.py --project-root . check` 判断：
- 退出码 0 → 已确认且哈希一致
- 退出码 2 → design.md 已修改，旧确认失效，两个下游动作都不可用，需要用户重新确认
- 退出码 3 → 无确认记录，按"未确认"处理

## 模型建议（运行时输出）

每个可用动作必须附带模型等级和推理深度建议，直接复用 PRD §6.3 推荐矩阵。建议必须是实际运行输出，不只是背景说明。

| 动作 | 默认建议 | 可使用轻量模型的条件 |
|------|----------|----------------------|
| `/spm-align` | 视任务而定 | 目标、范围和边界已经明确，仅需整理 |
| `/spm-design` | 深度推理模型 | 业务确实简单、输入完整、无方案权衡、角色状态权限关系简单 |
| `/spm-prd` | 根据确认版 Design 判断 | Design 决策完整，主要按现有模板展开明确规格 |
| `/spm-prototype` | 根据交互和实现复杂度判断 | 页面少、路径单一、行为明确，主要做既定表达与实现 |
| `/spm-design-review` | 深度推理模型 | 仅做结构和明确规则检查时可改用轻量模型或脚本 |
| `/spm-prd-review` | 深度推理模型 | 仅做结构和明确规则检查时可改用轻量模型或脚本 |
| `/spm-prototype-review` | 深度推理模型 | 仅做结构和明确规则检查时可改用轻量模型或脚本 |
| `/spm-fix` | 根据变更影响判断 | 修改范围、正确结果和受影响位置都已明确 |
| `/spm-prototype-mark` | 轻量模型 | 主动发现产品或交互问题时应另行使用深度 Review |

无法判断任务复杂度时，建议深度推理模型，优先保护首次产物质量。

## 输出格式

```
## 项目状态
- 当前阶段：[stage]（历史字段，仅供参考）
- status.json：存在/不存在
- Design 确认：已确认/未确认/已修改需重新确认/无确认记录
- Design 哈希：[一致/不一致/无记录]

## 产物清单
| 阶段 | 人读 | Review |
|------|------|--------|
| 对齐 | ✅/❌/— | — |
| 设计 | ✅/❌ | ✅/❌/— |
| PRD | ✅/❌ | ✅/❌/— |
| 原型 | ✅/❌ | ✅/❌/— |

## 最近 Review
[摘要或"无"]

## 可用动作
| 动作 | 可用 | 模型建议 | 原因 |
|------|------|---------|------|
| /spm-align | ✅/❌ | [轻量/深度推理/视任务而定] | [原因] |
| /spm-design | ✅/❌ | [深度推理/轻量] | [原因] |
| confirm-design | ✅/❌ | — | [原因] |
| /spm-prd | ✅/❌ | [根据 Design 判断/深度推理/轻量] | [原因] |
| /spm-prototype | ✅/❌ | [根据复杂度判断/深度推理/轻量] | [原因] |
| /spm-design-review | ✅/❌ | [深度推理/轻量或脚本] | [原因] |
| /spm-prd-review | ✅/❌ | [深度推理/轻量或脚本] | [原因] |
| /spm-prototype-review | ✅/❌ | [深度推理/轻量或脚本] | [原因] |
| /spm-fix | ✅/❌ | [根据变更影响判断] | [原因] |
| /spm-prototype-mark | ✅/❌ | [轻量] | [原因] |

## 建议
[一句话概括，不再给唯一下一步]
```

## 硬规则

1. 不做需求判断 / 写作质量判断 / reviewer 职责
2. 不修改任何文件——只读取和输出
3. 路径 C/D 不自动修复，只报告和建议
4. 输出后停止，不追加多余解释
5. 不按线性阶段给"唯一下一步"——展示所有可用动作
6. Design 确认状态必须展示
7. PRD 和 Prototype 作为两个独立下游动作并列展示
8. 每个可用动作必须附带模型等级建议
9. 无 status.json 时仍能正常输出（走路径 B）
10. 旧 metadata 或旧 review 记录不阻塞启动和导航
