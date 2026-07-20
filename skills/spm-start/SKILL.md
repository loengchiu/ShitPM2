---
name: spm-start
description: "启动阶段——vNext：识别当前状态和可用动作，不做产品判断，不修改产物。展示 PRD 和 Prototype 两个独立动作。不按固定线性阶段只给唯一下一步。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## vNext 职责定位

- 只负责识别当前状态和可用动作
- 不做产品判断
- 不修改产品产物
- 不再按固定线性阶段只给唯一下一步
- 能展示 PRD 和 Prototype 两个独立动作
- 展示 Design 确认状态

## 最小读取

**一次读取**：
1. `.workflow/status.json`（不存在 → 走路径 B）
2. `output/` 下各阶段产物（存在则读）
3. `.workflow/confirmations/design.json`（如存在，读 Design 确认状态）
4. `.workflow/reviews/` 下最近 review（如存在则读，仅作为参考）

## 执行路径

### 路径 A：有 status.json

1. 运行 `python $BUNDLE/scripts/python/stage-context.py --project-root .`
2. 直接引用脚本输出的 `available_actions` 列表，展示所有可用动作
3. 引用 `design_confirmation` 字段展示 Design 确认状态
4. JSON 解析失败 → 路径 C
5. 状态与产物不一致 → 路径 D

### 路径 B：无 status.json（新项目/扫描）

扫描 `output/` 产物判断当前可用动作：

| 产物状态 | Design 确认 | 可用动作 |
|---------|------------|---------|
| 全空 | — | `/spm-align`（可选）、`/spm-design` |
| 仅 align | — | `/spm-design` |
| design 存在 | 未确认 | `confirm-design`、`/spm-design`（修改）、`/spm-design-review` |
| design 存在 | 已确认 | `/spm-prd`、`/spm-prototype`、`/spm-design-review`、`confirm-design`（重新确认） |
| design + PRD | 已确认 | `/spm-prototype`、`/spm-prd-review`、`/spm-design-review` |
| design + Prototype | 已确认 | `/spm-prd`、`/spm-prototype-review`、`/spm-design-review` |
| design + PRD + Prototype | 已确认 | `/spm-prd-review`、`/spm-prototype-review`、`/spm-design-review`、`/spm-fix`、`/spm-prototype-mark` |

**不创建** `status.json`（由 writer 阶段首次产出时创建）。

### 路径 C：JSON 解析失败

告知损坏，展示前 500 字符。建议手动修复或删除走路径 B。停止，不自动修复。

### 路径 D：状态与产物不一致

列出不一致项，给出两种处理建议：① 回退 status.json current_stage ② 补建缺失产物。停止，等用户决定。

## 输出格式

```
## 项目状态
- 当前阶段：[stage]（历史字段，仅供参考）
- status.json：存在/不存在
- Design 确认：已确认/未确认/无确认记录
- Design 哈希：[一致/不一致]

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
| 动作 | 可用 | 原因 |
|------|------|------|
| /spm-align | ✅/❌ | [原因] |
| /spm-design | ✅/❌ | [原因] |
| confirm-design | ✅/❌ | [原因] |
| /spm-prd | ✅/❌ | [原因] |
| /spm-prototype | ✅/❌ | [原因] |
| /spm-design-review | ✅/❌ | [原因] |
| /spm-prd-review | ✅/❌ | [原因] |
| /spm-prototype-review | ✅/❌ | [原因] |
| /spm-fix | ✅/❌ | [原因] |
| /spm-prototype-mark | ✅/❌ | [原因] |

## 建议
[一句话概括，不再给唯一下一步]
```

## 硬规则

1. 不做需求判断 / 写作质量判断 / reviewer 职责
2. 不修改任何文件——只读取和输出
3. 路径 C/D 不自动修复，只报告和建议
4. 输出后停止，不追加多余解释
5. 不再按线性阶段给"唯一下一步"——展示所有可用动作
6. Design 确认状态必须展示
7. PRD 和 Prototype 作为两个独立下游动作并列展示
