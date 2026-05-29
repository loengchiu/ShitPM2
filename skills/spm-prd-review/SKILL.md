---
name: spm-prd-review
description: "PRD review——判断 PRD 正文的质量。用于用户说 prd review、PRD review、review PRD 时，先跑预检查脚本确认准入，再逐页审查坏味道、三层覆盖、一致性和结构。不代写 PRD 正文。"
triggers:
  - "prd review"
  - "PRD review"
  - "review PRD"
  - "spm-prd-review"
---

# PRD Review

## 触发条件

用户要求进行 PRD review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 运行 `review-precheck.py --stage prd --stdin-artifact`（agent 已读取 prd.md，通过 stdin 传入），生成 `.workflow/runtime/prd/review-precheck.json`

🔴 **检查点：预检查脚本**——如脚本执行失败或返回非零退出码，停下来告知用户，不跳过预检查继续。如 `can_start_review` = false，停止并输出阻塞项。

2. 检查 prd.md 是否存在
3. 检查核心章节是否全部存在：
   - 详细需求说明
   - 权限汇总
   - 数据字典
   - 状态机
4. 检查 metadata/prd 是否完整（6 个 JSON 文件）
5. 运行 `prd-style-lint.py` 检查文风问题
6. 检查数据字典是否使用约定轻量格式
7. 检查 prd.md 中是否有稳定 ID 泄漏

🔴 **检查点：预检查结果**——如有阻塞问题（核心章节缺失、机读物不完整），停止并输出阻塞项清单，不进入第二段。

### 第二段：人读正文质量审查

逐页检查：

1. **坏味道检查**（引用规约 §7.2）
   - 是否为标签式正文
   - 是否为动作流水账
   - 是否为纯表格式页面正文
   - 是否过多加粗
   - 是否有模糊表述

2. **三层覆盖检查**
   - 每个页面是否覆盖界面元素与展示规则
   - 每个页面是否覆盖交互逻辑与状态流转
   - 每个页面是否覆盖异常处理与边界场景

3. **一致性检查**
   - PRD 字段列表与 design.md 字段定义是否一致
   - PRD 权限口径与 design.md 权限定义是否一致
   - PRD 状态机与 design.md 状态定义是否一致
   - 页面编号是否重复
   - 是否存在动作复用
   - 是否跨节代写

4. **结构检查**
   - 状态机是否按核心业务对象组织
   - 状态机是否包含状态集合、迁移、触发动作和限制条件
   - 权限汇总是否包含页面级、按钮级权限

## 检查项清单（10 项）

引用规约 §3.4 和 §7.2：

1. 是否命中坏味道（标签式、流水账、纯表格、过多加粗、模板腔、模糊表述）
2. 页面是否缺展示规则
3. 页面是否缺状态变化
4. 页面是否缺异常边界
5. 页面编号是否重复
6. 是否跨节代写
7. 是否存在动作复用
8. 核心章节是否完整
9. 数据字典是否使用约定轻量格式
10. PRD 与 design 的字段/权限/状态是否镜像一致
11. PRD 中每个字段的单选/多选、只读/可编辑约束是否与 field-constraints.json 一致（重点检查：备选项是否被错误收窄为单选）

## 输出要求

### 机读结果

写入 `.workflow/reviews/prd-review-N.json`（N 为同阶段递增序号），结构同 review-result.schema.json。

最小字段：`stage`、`verdict`、`issues`、`issue_layer`、`affected_objects`、`needs_upstream_sync`、`next_recommended`、`reviewed_at`。

### 人读摘要

写入 `.workflow/reviews/prd-review-N.md`（N 为同阶段递增序号），包含：

1. 结论
2. 主要问题（逐页引用）
3. 是否需要回上游（回 design）
4. 下一步建议

🔴 **检查点：verdict 输出**——输出 verdict 后，🔴 **停止并等待用户确认**。不自动推进阶段，不自动触发 fix。

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞，不能继续**：有 P0 或 2+ 个 P1

P0 示例：核心章节缺失、设计边界违反、字段/权限/状态镜像不一致、field-constraints.json 标记 multi_select:true 的字段在 PRD 中被写成单选

### 严重级别说明

- **P0**：阻塞性缺陷（核心章节缺失、设计边界违反、字段/权限/状态镜像不一致等）
- **P1**：影响质量但不阻塞推进（页面缺少展示规则、状态变化缺失等）
- **P2**：格式/风格类问题，不影响功能（lint warning、稳定 ID 泄漏等）。**P2 必须写入 issues 数组**，但 **不计入 verdict 判定**

### issue_layer 格式

必须为对象 `{"structure": N, "content": N, "consistency": N}`，三个字段均为必填整数。

- `structure`：归入结构层的 issue 数
- `content`：归入内容层的 issue 数
- `consistency`：归入一致性层的 issue 数

## 硬规则

1. review 通过后不自动推进阶段，由 PM 手动进入下一阶段
2. 不代写 PRD 正文
3. 不自行修改 prd.md
4. 问题必须具体到页面、章节和内容
5. 不放过 P0 问题
6. 预检查脚本失败时停下告知用户，不跳过

## 不要做什么

- 不代写 PRD 正文
- 不自行修改 prd.md
- 不自动推进到下一阶段
- 不跳过预检查脚本直接进入人读审查
- 不在 verdict 输出后自动触发 fix 或推进
- 不把 P2 问题计入 verdict 判定
- 不放过 P0 问题——发现 P0 必须输出阻塞 verdict
