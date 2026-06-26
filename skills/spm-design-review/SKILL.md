---
name: spm-design-review
description: "设计 review——判断 design 基线质量。用于用户说 design review、设计 review、review 设计时。预检查 → 逐项审查 → metadata 生成。不代写 design正文。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 执行顺序（三段式）

**先读 design.md 全文**，后续通过 `--stdin-artifact` 传入脚本。

### 第一段：预检查

1. 运行 `scripts/python/review-precheck.py --stage design --no-metadata --stdin-artifact` → `.workflow/runtime/design/review-precheck.json`
2.  脚本失败或 `can_start_review=false` → 停止输出阻塞项。假阳性（alias_missed>0 且 blocking_issues 空）→ 列出 warnings 等用户确认后可继续
3. 检查核心章节：角色定义/模块定义/页面清单/字段定义/页面与字段落点/规则与状态/权限定义
4. 检查表格仍为结构化格式（字段定义、页面落点、状态流转、权限矩阵）

 有阻塞问题（核心章节缺失）→ 停止，不进入第二段。

### 第二段：人读质量审查

1. 字段定义属性是否齐全（9 属性）
2. 权限定义覆盖到字段级，按"页面 > 角色 > 字段权限例外"组织
3. 状态定义覆盖完整
4. 模块/页面/字段能在 align.md 中找到来源（不新增未确认范围）
5. 关键表格结构性检查

 存在 P0 或 2+ 个 P1 → 输出 verdict 停止，不进入第三段。

### 第三段：metadata 生成（仅第二段通过后）

1. `scripts/python/stage-prep.py --stage design --project-root <path>` 生成 metadata
2. 一致性校验：8 个 JSON 完整性、字段/页面/模块数与 design.md 一致、page-fields 覆盖率、non-page-fields 覆盖率（≤40%）、design.md 无稳定 ID 泄漏
3. 校验失败 → 输出不一致项，verdict 降级为"有问题需修改"
4. 校验通过 → 更新 `status.json` 中 `metadata_paths.design`

## 判定规则

- **通过**：零 P0、零 P1（含 metadata 校验）
- **有问题需修改**：零 P0，1 个 P1
- **阻塞**：有 P0 或 2+ 个 P1

verdict = max(第二段 verdict, 第三段 verdict)。

| 级别 | 含义 | 示例 |
|------|------|------|
| P0 | 阻塞 | 核心章节缺失、新增未确认范围 |
| P1 | 影响质量 | 字段属性缺失、权限未覆盖字段级 |
| P2 | 格式 | lint warning（写入 issues 不计 verdict） |

issue_layer：`{"structure":N,"content":N,"consistency":N}`，三个整数必填。

## 输出

- 机读：`.workflow/reviews/design-review-N.json`（stage/verdict/issues/issue_layer/affected_objects/needs_upstream_sync/next_recommended/reviewed_at/metadata_generated）
- 人读：`.workflow/reviews/design-review-N.md`（结论/主要问题/是否回上游/下一步/metadata 状态）

 输出 verdict 后停止等用户确认，不自动推进。

## 失败模式

| 场景 | 一线 | 兜底 |
|------|------|------|
| 预检查脚本失败 | 检查路径和环境 | 停下，不跳过 |
| can_start_review=false | 输出阻塞项 | 不绕过 |
| 假阳性 | 列出 warnings 等确认 | 确认后继续 |
| 人读发现 P0 | 输出阻塞 verdict | 不进入 metadata |
| metadata 生成失败 | 检查 design.md 格式 | 降级 verdict |
| metadata 校验不一致 | 输出不一致项 | 降级 verdict |

## 硬规则

1. 不代写 design 正文
2. 不自行修改 design.md
3. 问题具体到章节和内容
4. 预检查失败不跳过
5. metadata 只在第二段通过后生成
6. P2 写入 issues 但不计入 verdict
7. review 通过后不自动推进
