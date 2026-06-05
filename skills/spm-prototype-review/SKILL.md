---
name: spm-prototype-review
description: "原型 review——判断原型的质量。用于用户说 prototype review、原型 review、review 原型时，先跑预检查脚本确认准入，再审查页面结构、状态表达、交互路径和权限表现。不代写原型代码。"
triggers:
  - "prototype review"
  - "原型 review"
  - "review 原型"
  - "spm-prototype-review"
---
## 脚本路径

> 🔴 **所有 Python 脚本位于 SKILL bundle 的 `scripts/python/` 目录下，不在项目目录下。**
> SKILL bundle 根目录：`D:\work\ShitPM`
> 脚本完整路径示例：`D:\work\ShitPM\scripts\python\review-precheck.py`
>
> 执行时使用 SKILL bundle 绝对路径拼接脚本名，禁止在项目目录下搜索脚本。


# 原型 Review

## 触发条件

用户要求进行原型 review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 运行 `scripts/python/review-precheck.py --stage prototype --stdin-artifact`（agent 已读取 index.html，通过 stdin 传入），生成 `.workflow/runtime/prototype/review-precheck.json`

🔴 **失败分支：预检查脚本失败**——脚本执行失败时停下告知用户，不跳过。如 `can_start_review` = false，停止并输出阻塞项。

2. 检查 index.html 是否存在且为有效 HTML
3. 检查 metadata/prototype 是否完整（index.json、page-map.json）

🔴 **检查点：预检查结果**——如有阻塞问题（index.html 不存在），停止并输出阻塞项清单，不进入第二段。

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

## 失败模式与 Fallback

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|---------|---------|-----------|
| 预检查脚本失败 | review-precheck.py 返回非零退出码 | 检查脚本路径和 Python 环境 | 停下告知用户具体错误，不跳过预检查 |
| can_start_review = false | 预检查发现阻塞问题 | 输出阻塞项清单，停下等用户修复 | 不绕过预检查直接审查 |
| 假阳性（alias_missed） | 章节名称不匹配但实际存在 | 列出 warnings 条目，等用户确认 | 用户确认后可继续 |
| 人读审查发现 P0 | 核心章节缺失或严重不一致 | 输出阻塞 verdict，不进入 metadata 生成 | 等用户修复后重新 review |
| metadata 生成失败 | stage-prep.py 报错 | 检查 design.md 格式 | 告知用户 metadata 未生成，verdict 降级 |
| metadata 校验不一致 | 字段数/页面数与 design.md 不匹配 | 输出具体不一致项 | verdict 降级为"有问题需修改" |

## 不要做什么

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|--------|------------|---------|
| 1 | 代写被审查的正文 | reviewer 和 writer 应独立 | 只输出问题清单，不代写 |
| 2 | 自行修改被审查文件 | 审查不应改变被审查内容 | 输出问题清单，等用户或 fix skill 处理 |
| 3 | 自动推进到下一阶段 | 用户可能需要验证 review 结果 | 输出 verdict 后停下等用户确认 |
| 4 | 跳过预检查脚本 | 预检查能发现结构问题，跳过会浪费审查时间 | 预检查失败就停下，不绕过 |
| 5 | verdict 后自动触发 fix/推进 | fix 和推进应由用户决定 | 输出 verdict 后停下等用户指令 |
| 6 | 把 P2 问题计入 verdict | P2 不影响 verdict 判定，计入会过度阻塞 | P2 写入 issues 数组但不计入 verdict |
| 7 | 放过 P0 问题 | P0 是阻塞性缺陷，放过会导致下游返工 | 发现 P0 必须输出阻塞 verdict |
