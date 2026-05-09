---
name: spm-prototype-review
description: 原型 review——判断原型的质量
triggers:
  - "prototype review"
  - "原型 review"
  - "review 原型"
---

# 原型 Review

## 触发条件

用户要求进行原型 review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 检查 index.html 是否存在且为有效 HTML
2. 检查 metadata/prototype 是否完整（index.json、page-map.json）
3. 检查原型是否读取了 design.md

### 第二段：人读质量审查

1. 原型是否展示了 design 中定义的页面结构
2. 状态表达是否覆盖核心状态
3. 交互主路径是否覆盖
4. 权限表现是否覆盖
5. metadata/prototype 与原型是否一致

## 检查项清单（5 项）

引用验收 §9.5：

1. 原型是否展示了 design 中定义的页面结构
2. 状态表达是否覆盖核心状态
3. 交互主路径是否覆盖
4. 权限表现是否覆盖
5. metadata/prototype 与原型是否一致

## 输出要求

### 机读结果

写入 `.workflow/reviews/prototype-review.json`，结构同 review-result.schema.json。
verdict 字段只允许三档值。

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
2. 不代写原型代码
3. 不自行修改 index.html
4. 问题必须具体到页面和区域
