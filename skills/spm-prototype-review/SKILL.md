---
name: spm-prototype-review
description: "原型 review——判断原型质量。预检查 → 页面结构/状态/交互/权限审查。不代写原型代码。"
triggers:
  - "prototype review"
  - "原型 review"
  - "review 原型"
  - "spm-prototype-review"
---
## 路径解析

从 `<!-- SHITPM GLOBAL RULES START -->` 取 `$BUNDLE`。`scripts/` `templates/` `references/` `contracts/` `lib/` → `$BUNDLE` 绝对路径；`.workflow/` `output/` → 项目根相对路径。

# 原型 Review

## 触发条件

用户要求原型 review。

## 执行顺序（两段式）

### 第一段：预检查

1. `scripts/python/review-precheck.py --stage prototype --stdin-artifact`（agent 已读 index.html，stdin 传入）→ `.workflow/runtime/prototype/review-precheck.json`
2.  脚本失败或 `can_start_review=false` → 停止，输出阻塞项
3. 检查 index.html 存在且有效
4. 检查 metadata/prototype 完整（index.json、page-map.json）

 有阻塞 → 停止，不进入第二段。

### 第二段：质量审查

1. 原型展示 design 中定义的页面结构
2. 状态表达覆盖核心状态
3. 交互主路径覆盖
4. 权限表现覆盖
5. metadata/prototype 与原型一致

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞**：有 P0 或 2+ 个 P1

| 级别 | 示例 |
|------|------|
| P0 | 页面结构缺失、交互主路径不通 |
| P1 | 状态表达不完整、权限不覆盖 |
| P2 | 稳定 ID 泄漏（写入 issues 不计 verdict）|

issue_layer：`{"structure":N,"content":N,"consistency":N}`。

## 输出

- 机读：`.workflow/reviews/prototype-review-N.json`
- 人读：`.workflow/reviews/prototype-review-N.md`（结论/主要问题/是否回上游/下一步）

 输出 verdict 后停止等用户确认。

## 失败模式

| 场景 | 一线 | 兜底 |
|------|------|------|
| 预检查脚本失败 | 检查路径和环境 | 停下，不跳过 |
| can_start_review=false | 输出阻塞项 | 不绕过 |
| 假阳性 | 列出 warnings 等确认 | 确认后继续 |

## 硬规则

1. 不代写原型代码
2. 不自行修改 index.html
3. 问题具体到页面和区域
4. 预检查失败不跳过
5. P2 写入 issues 但不计入 verdict
6. review 通过后不自动推进
