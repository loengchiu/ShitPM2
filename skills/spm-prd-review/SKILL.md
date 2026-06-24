---
name: spm-prd-review
description: "PRD review——判断 PRD 正文的质量。用于用户说 prd review、PRD review、review PRD 时，先跑预检查脚本确认准入，再逐页审查坏味道、三层覆盖、一致性和结构。不代写 PRD 正文。"
triggers:
  - "prd review"
  - "PRD review"
  - "review PRD"
  - "spm-prd-review"
---
## 路径解析规则

🔴 **关键：ShitPM 安装在 bundle 目录，不在当前项目目录。**

执行本 skill 前，先从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段中读取 `ShitPM bundle root:` 的值，下文以 `$BUNDLE` 表示。

路径分类：
- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE` 下解析（绝对路径）
- `.workflow/`、`output/` 开头 → 当前项目根目录下解析（CWD 相对路径，不变）

示例：
```
# 脚本调用
python $BUNDLE/scripts/python/stage-context.py --stage design --project-root .

# 读取 bundle 资源
Read $BUNDLE/templates/design.md
Read $BUNDLE/references/design-writing.md

# 读取项目文件（CWD 相对，不变）
Read output/design/design.md
Read .workflow/status.json
```

> 下文所有以 `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头的路径一律在 `$BUNDLE` 下解析。

# PRD Review
## 触发条件

用户要求进行 PRD review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 运行 `scripts/python/review-precheck.py --stage prd --no-metadata --stdin-artifact`（agent 已读取 prd.md，通过 stdin 传入），生成 `.workflow/runtime/prd/review-precheck.json`

🔴 **失败分支：预检查脚本失败**——脚本执行失败时停下告知用户，不跳过。如 `can_start_review` = false，停止并输出阻塞项。

2. 检查 prd.md 是否存在
3. 检查核心章节是否全部存在：
   - 详细需求说明
   - 权限汇总
   - 数据字典
   - 状态机
5. 运行 `scripts/python/prd-style-lint.py` 检查文风问题
6. 检查数据字典是否使用约定轻量格式
7. 检查 prd.md 中是否有稳定 ID 泄漏

🔴 **检查点：预检查结果**——如有阻塞问题（核心章节缺失），停止并输出阻塞项清单，不进入第二段。

### 第二段：人读正文质量审查

逐页检查：

1. **坏味道检查**
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
11. PRD 中字段约束（单选/多选、只读/可编辑）是否与 design.md 数据字典一致（prd 生成阶段已用 verify-against-metadata.py 自检，review 时抽查确认）

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

P0 示例：核心章节缺失、设计边界违反、字段/权限/状态镜像不一致、design.md 标记多选的字段在 PRD 中被写成单选

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
