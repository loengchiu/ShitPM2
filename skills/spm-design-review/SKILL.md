---
name: spm-design-review
description: "设计 review——判断 design 基线的质量。用于用户说 design review、设计 review、review 设计时，先跑预检查脚本确认准入，再逐项审查核心章节、字段定义、权限覆盖和一致性。不代写 design 正文。"
triggers:
  - "design review"
  - "设计 review"
  - "review 设计"
  - "spm-design-review"
---

# 设计 Review

## 触发条件

用户要求进行设计 review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 运行 `review-precheck.py --stage design --stdin-artifact`（agent 已读取 design.md，通过 stdin 传入），生成 `.workflow/runtime/design/review-precheck.json`

🔴 **检查点：预检查脚本**——如脚本执行失败或返回非零退出码，停下来告知用户，不跳过预检查继续。如 `can_start_review` = false，停止并输出阻塞项。

2. 检查 design.md 是否存在
3. 检查核心章节是否全部存在：
   - 角色定义
   - 模块定义
   - 页面清单
   - 字段定义
   - 规则与状态定义
   - 权限定义
4. 检查 metadata/design 是否完整（9 个 JSON 文件）
5. 检查稳定 ID 是否正确生成（6 种前缀）
6. 检查 design.md 正文中是否有稳定 ID 泄漏
7. 检查人读稿与机读镜像数量一致性
8. 检查 field-constraints.json 是否存在且每个字段的 `multi_select`、`editable`、`required` 属性与 design.md 正文一致

🔴 **检查点：预检查结果**——如有阻塞问题（核心章节缺失、机读物不完整），停止并输出阻塞项清单，不进入第二段。

### 第二段：人读正文质量审查

1. 字段定义属性是否齐全（9 属性）
2. 权限定义是否覆盖到字段级
3. 权限是否按"页面 > 角色 > 字段权限例外"组织
4. 状态定义是否覆盖完整
5. 模块/页面/字段是否能在 align.md 中找到来源（不新增 align 未确认的范围）
6. metadata/design 与 design.md 是否 100% 一致

## 检查项清单

引用规约 §7.2 坏味道定义。design review 重点检查：

1. 核心章节完整性
2. 字段定义属性齐全性
3. 权限定义覆盖到字段级
4. 状态定义覆盖完整性
5. metadata/design 与 design.md 一致性
6. 稳定 ID 正确性
7. 不新增 align 未确认范围
8. field-constraints.json 与 design.md 字段约束一致性

## 输出要求

### 机读结果

写入 `.workflow/reviews/design-review-N.json`（N 为同阶段递增序号），包含：

- `stage`: `"design"`
- `verdict`: `"通过"` / `"有问题需修改"` / `"阻塞，不能继续"`
- `issues`: 问题列表
- `issue_layer`: 问题归属层分布
- `affected_objects`: 受影响对象
- `needs_upstream_sync`: 是否需要回上游
- `next_recommended`: 下一步建议
- `reviewed_at`: ISO 8601 时间戳

### 人读摘要

写入 `.workflow/reviews/design-review-N.md`（N 为同阶段递增序号），包含：

1. 结论
2. 主要问题
3. 是否需要回上游
4. 下一步建议

🔴 **检查点：verdict 输出**——输出 verdict 后，🔴 **停止并等待用户确认**。不自动推进阶段，不自动触发 fix。

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞，不能继续**：有 P0 或 2+ 个 P1

### 严重级别说明

- **P0**：阻塞性缺陷（核心章节缺失、字段定义丢失、design 新增 align 未确认范围等）
- **P1**：影响质量但不阻塞推进（字段属性缺失、权限未覆盖到字段级等）
- **P2**：格式/风格类问题，不影响功能（稳定 ID 泄漏、lint warning 等）。**P2 必须写入 issues 数组**，但 **不计入 verdict 判定**

### issue_layer 格式

必须为对象 `{"structure": N, "content": N, "consistency": N}`，三个字段均为必填整数。

- `structure`：归入结构层的 issue 数
- `content`：归入内容层的 issue 数
- `consistency`：归入一致性层的 issue 数

## 硬规则

1. review 通过后不自动推进阶段，由 PM 手动进入下一阶段
2. 不代写 design 正文
3. 不自行修改 design.md
4. 问题必须具体到章节和内容
5. 预检查脚本失败时停下告知用户，不跳过

## 不要做什么

- 不代写 design 正文
- 不自行修改 design.md
- 不自动推进到下一阶段
- 不跳过预检查脚本直接进入人读审查
- 不在 verdict 输出后自动触发 fix 或推进
- 不把 P2 问题计入 verdict 判定
