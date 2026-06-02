---
name: spm-design-review
description: "设计 review——判断 design 基线的质量。用于用户说 design review、设计 review、review 设计时，先跑预检查脚本确认准入，再逐项审查核心章节、字段定义、权限覆盖和一致性，最后生成 metadata。不代写 design 正文。"
triggers:
  - "design review"
  - "设计 review"
  - "review 设计"
  - "spm-design-review"
---
## 脚本路径

> 🔴 **所有 Python 脚本位于 SKILL bundle 的 `scripts/python/` 目录下，不在项目目录下。**
> SKILL bundle 根目录：`D:\work\ShitPM`
> 脚本完整路径示例：`D:\work\ShitPM\scripts\python\review-precheck.py`
>
> 执行时使用 SKILL bundle 绝对路径拼接脚本名，禁止在项目目录下搜索脚本。


# 设计 Review

## 触发条件

用户要求进行设计 review。

## 执行顺序（三段式）

🔴 **一次读取**——先用一次工具调用读取 design.md 全文，后续通过 --stdin-artifact 传入脚本。

### 第一段：确定性预检查

1. 运行 `scripts/python/review-precheck.py --stage design --no-metadata --stdin-artifact`（agent 已读取 design.md，通过 stdin 传入），生成 `.workflow/runtime/design/review-precheck.json`

🔴 **失败分支：预检查脚本失败**——脚本执行失败或返回非零退出码时，🔴 停下告知用户具体错误，不跳过预检查继续。不尝试手动绕过脚本直接审查。如 `can_start_review` = false，停止并输出阻塞项。

🔴 **假阳性降级**——当 can_start_review = false 但输出 JSON 中 alias_missed_count > 0 且 blocking_issues 为空时：
1. agent 逐项列出 warnings 中的"章节名称不匹配"条目，标注实际文档中的章节标题
2. 输出到人读摘要，等待用户确认
3. 用户确认后可继续第二段审查

2. 检查 design.md 是否存在
3. 检查核心章节是否全部存在：
   - 角色定义
   - 模块定义
   - 页面清单
   - 字段定义
   - 规则与状态定义
   - 权限定义
4. 检查关键表格仍为结构化格式（字段定义、页面落点、状态流转、权限矩阵使用 Markdown 表格，列名符合模板约定）

🔴 **检查点：预检查结果**——如有阻塞问题（核心章节缺失），停止并输出阻塞项清单，不进入第二段。

> **注意**：此阶段不检查 metadata 存在性和一致性——metadata 将在第三段 review 通过后生成。

### 第二段：人读正文质量审查

1. 字段定义属性是否齐全（9 属性）
2. 权限定义是否覆盖到字段级
3. 权限是否按"页面 > 角色 > 字段权限例外"组织
4. 状态定义是否覆盖完整
5. 模块/页面/字段是否能在 align.md 中找到来源（不新增 align 未确认的范围）
6. 结构规范性：确认关键表格（字段定义、页面落点、状态流转、权限矩阵）仍是结构化表格，列名符合模板约定

🔴 **检查点：第二段 verdict**——如第二段存在 P0 或 2+ 个 P1，输出 verdict 后停止，不进入第三段。metadata 不会在有阻塞问题时生成。

### 第三段：metadata 生成与校验（仅在第二段通过后执行）

1. 运行 `scripts/python/stage-prep.py --stage design --project-root <path>` 生成 `.workflow/metadata/design/` 下全部文件
2. 运行一致性校验：
   - metadata 文件完整性（11 个 JSON：index, entities, relations, modules, pages, fields, rules, states, permissions, page-fields, non-page-fields, field-constraints）
   - 字段数/页面数/模块数与 design.md 表格行数对比
   - page-fields 覆盖率：所有页面清单中的页面是否出现在 page-fields.json
   - non-page-fields 覆盖率：非页面落点字段是否合理（不超过总字段 40%）
   - field-constraints.json 与 design.md 字段约束一致性
   - design.md 正文中无稳定 ID 泄漏
3. 如校验失败 → 输出具体不一致项，verdict 降级为"有问题需修改"（P1）
4. 如校验通过 → metadata 作为 review 通过的产物输出，更新 status.json 中 `metadata_paths.design`

## 检查项清单

### Phase A：人读质量（第一段 + 第二段）

1. 核心章节完整性
2. 字段定义属性齐全性
3. 权限定义覆盖到字段级
4. 状态定义覆盖完整性
5. 不新增 align 未确认范围
6. 关键表格结构规范性
7. 页面清单、字段定义、页面与字段落点三处互相对齐

### Phase B：metadata 一致性（第三段，由 stage-prep.py 生成后自动校验）

8. metadata/design 与 design.md 字段/页面/模块数量一致
9. page-fields 覆盖率
10. non-page-fields 覆盖率
11. field-constraints 一致性
12. 稳定 ID 正确性（6 种前缀）
13. design.md 正文中无稳定 ID 泄漏

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
- `metadata_generated`: boolean，第三段是否成功生成 metadata

### 人读摘要

写入 `.workflow/reviews/design-review-N.md`（N 为同阶段递增序号），包含：

1. 结论
2. 主要问题
3. 是否需要回上游
4. 下一步建议
5. metadata 生成状态（第三段通过/失败/未执行）

🔴 **检查点：verdict 输出**——输出 verdict 后，🔴 **停止并等待用户确认**。不自动推进阶段，不自动触发 fix。

## 判定规则

- **通过**：零 P0、零 P1（含第三段 metadata 校验）
- **有问题需修改**：零 P0，1 个 P1
- **阻塞，不能继续**：有 P0 或 2+ 个 P1

verdict 判定 = max(第二段 verdict, 第三段 verdict)。

### 严重级别说明

- **P0**：阻塞性缺陷（核心章节缺失、字段定义丢失、design 新增 align 未确认范围等）
- **P1**：影响质量但不阻塞推进（字段属性缺失、权限未覆盖到字段级、metadata 校验不一致等）
- **P2**：格式/风格类问题，不影响功能（lint warning 等）。**P2 必须写入 issues 数组**，但 **不计入 verdict 判定**

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
6. metadata 只在第二段人读质量审查通过后才生成——不在有阻塞问题时生成

## Shell 环境规则

🔴 **Codex 默认 shell 为 PowerShell**——不要用 Python -c 内联脚本，写临时 .py 文件执行。

## 不要做什么

- 不代写 design 正文
- 不自行修改 design.md
- 不自动推进到下一阶段
- 不跳过预检查脚本直接进入人读审查
- 不在 verdict 输出后自动触发 fix 或推进
- 不把 P2 问题计入 verdict 判定
- 不在第二段有阻塞问题时跳到第三段生成 metadata
