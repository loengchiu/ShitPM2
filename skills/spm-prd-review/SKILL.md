---
name: spm-prd-review
description: "PRD review——判断 PRD 正文质量。用于用户说 prd review、PRD review、review PRD 时。预检查 → 坏味道/三层覆盖/一致性/结构审查。不代写 PRD 正文。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 执行顺序（两段式）

### 第一段：预检查

1. `scripts/python/review-precheck.py --stage prd --no-metadata --stdin-artifact`（agent 已读 prd.md，stdin 传入）→ `.workflow/runtime/prd/review-precheck.json`
2.  脚本失败或 `can_start_review=false` → 停止，输出阻塞项
3. 检查核心章节：详细需求说明/权限汇总/数据字典/状态机
4. 运行 `scripts/python/prd-style-lint.py` 检查文风
5. 检查数据字典使用约定轻量格式
6. 检查 prd.md 无稳定 ID 泄漏

 有阻塞问题 → 停止，不进入第二段。

### 第二段：人读质量

1. **坏味道**：标签式正文/动作流水账/纯表格/过多加粗/模糊表述
2. **三层覆盖**：界面元素与展示规则/交互逻辑与状态流转/异常处理与边界
3. **一致性**：字段列表/权限口径/状态机与 design.md 一致；页面编号无重复；无动作复用；无跨节代写
4. **结构**：状态机按核心业务对象组织，含状态集合/迁移/触发动作和限制条件；权限汇总含页面级/按钮级权限

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞**：有 P0 或 2+ 个 P1

| 级别 | 示例 |
|------|------|
| P0 | 核心章节缺失、设计边界违反、字段/权限/状态镜像不一致 |
| P1 | 页面缺展示规则、状态变化缺失 |
| P2 | lint warning、稳定 ID 泄漏（写入 issues 不计 verdict）|

issue_layer：`{"structure":N,"content":N,"consistency":N}`。

## 输出

- 机读：`.workflow/reviews/prd-review-N.json`
- 人读：`.workflow/reviews/prd-review-N.md`（结论/主要问题/是否回上游/下一步）

 输出 verdict 后停止等用户确认，不自动推进。

## 失败模式

| 场景 | 一线 | 兜底 |
|------|------|------|
| 预检查脚本失败 | 检查路径和环境 | 停下，不跳过 |
| can_start_review=false | 输出阻塞项 | 不绕过 |
| 假阳性 | 列出 warnings 等确认 | 确认后继续 |
| 人读发现 P0 | 输出阻塞 verdict | 停止 |

## 硬规则

1. 不代写 PRD 正文
2. 不自行修改 prd.md
3. 问题具体到页面/章节/内容
4. 预检查失败不跳过
5. P2 写入 issues 但不计入 verdict
6. review 通过后不自动推进
