---
name: spm-prototype-review
description: "原型 review——判断原型的质量。用于用户说 prototype review、原型 review、review 原型时，先跑预检查脚本确认准入，再审查页面结构、状态表达、交互路径和权限表现。不代写原型代码。"
triggers:
  - "prototype review"
  - "原型 review"
  - "review 原型"
  - "spm-prototype-review"
---

# 原型 Review

## 触发条件

用户要求进行原型 review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 运行 `review-precheck.py --stage prototype`，生成 `.workflow/runtime/prototype/review-precheck.json`

🔴 **检查点：预检查脚本**——如脚本执行失败或返回非零退出码，停下来告知用户，不跳过预检查继续。如 `can_start_review` = false，停止并输出阻塞项。

2. 检查 index.html 是否存在且为有效 HTML
3. 检查 metadata/prototype 是否完整（index.json、page-map.json）
4. 检查原型是否读取了 design.md

🔴 **检查点：预检查结果**——如有阻塞问题（index.html 不存在、metadata 不完整），停止并输出阻塞项清单，不进入第二段。

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

写入 `.workflow/reviews/prototype-review-N.json`（N 为同阶段递增序号），结构同 review-result.schema.json。

最小字段：`stage`、`verdict`、`issues`、`issue_layer`、`affected_objects`、`needs_upstream_sync`、`next_recommended`、`reviewed_at`。

### 人读摘要

写入 `.workflow/reviews/prototype-review-N.md`（N 为同阶段递增序号），包含：

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

- **P0**：阻塞性缺陷（页面结构缺失、交互主路径无法走通等）
- **P1**：影响质量但不阻塞推进（状态表达不完整、权限表现不覆盖等）
- **P2**：格式/风格类问题（稳定 ID 泄漏、UI 细节不一致等）。**P2 必须写入 issues 数组**，但 **不计入 verdict 判定**

### issue_layer 格式

必须为对象 `{"structure": N, "content": N, "consistency": N}`，三个字段均为必填整数。

- `structure`：归入结构层的 issue 数
- `content`：归入内容层的 issue 数
- `consistency`：归入一致性层的 issue 数

## 硬规则

1. review 通过后不自动推进阶段，由 PM 手动进入下一阶段
2. 不代写原型代码
3. 不自行修改 index.html
4. 问题必须具体到页面和区域
5. 预检查脚本失败时停下告知用户，不跳过

## 不要做什么

- 不代写原型代码
- 不自行修改 index.html
- 不自动推进到下一阶段
- 不跳过预检查脚本直接进入人读审查
- 不在 verdict 输出后自动触发 fix 或推进
- 不把 P2 问题计入 verdict 判定
