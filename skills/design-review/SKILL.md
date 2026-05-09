---
name: spm-design-review
description: 设计 review——判断 design 基线的质量
triggers:
  - "design review"
  - "设计 review"
  - "review 设计"
---

# 设计 Review

## 触发条件

用户要求进行设计 review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 检查 design.md 是否存在
2. 检查核心章节是否全部存在：
   - 角色定义
   - 模块定义
   - 页面清单
   - 字段定义
   - 规则与状态定义
   - 权限定义
3. 检查 metadata/design 是否完整（9 个 JSON 文件）
4. 检查稳定 ID 是否正确生成（6 种前缀）
5. 检查 design.md 正文中是否有稳定 ID 泄漏
6. 检查人读稿与机读镜像数量一致性

如有阻塞问题（如核心章节缺失、机读物不完整），停止并输出阻塞项。

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

## 输出要求

### 机读结果

写入 `.workflow/reviews/design-review.json`，包含：

- `stage`: `"design"`
- `verdict`: `"通过"` / `"有问题需修改"` / `"阻塞，不能继续"`
- `issues`: 问题列表
- `issue_layer`: 问题归属层分布
- `affected_objects`: 受影响对象
- `needs_upstream_sync`: 是否需要回上游
- `next_recommended`: 下一步建议

### 人读摘要

简短 Markdown，包含：

1. 结论
2. 主要问题
3. 是否需要回上游
4. 下一步建议

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞，不能继续**：有 P0 或 2+ 个 P1

## 硬规则

1. review 通过后不自动推进阶段，由 PM 手动进入下一阶段
2. 不代写 design 正文
3. 不自行修改 design.md
4. 问题必须具体到章节和内容
