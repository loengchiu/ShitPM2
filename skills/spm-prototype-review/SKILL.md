---
name: spm-prototype-review
description: "原型 review——判断原型质量。用于用户说 prototype review、原型 review、review 原型时。预检查 → 页面结构/状态/交互/权限审查。不代写原型代码。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 执行顺序（两段式）

### 第一段：预检查

1. `python $BUNDLE/scripts/python/review-precheck.py --stage prototype --stdin-artifact`（agent 已读 index.html，stdin 传入）→ `.workflow/runtime/prototype/review-precheck.json`
2.  脚本失败或 `can_start_review=false` → 停止，输出阻塞项
3. 检查 index.html 存在且有效
4. prototype 阶段不生成独立 metadata，跳过 metadata 检查

 有阻塞 → 停止，不进入第二段。

### 第二段：质量审查

1. **页面覆盖 checklist**：

   读取 `.workflow/metadata/design/pages.json`

   逐项输出对比结果（结构化）：
   - design 每个页面 × 原型 HTML → [存在/缺失/幻觉]
   - 原型出现的页面不在 design → 标记为幻觉

   判定：
   - 幻觉页面 = P0
   - 缺失页面 = P1（缺失率 > 50% 升级 P0）

2. 状态表达覆盖核心状态
3. 交互主路径覆盖
4. 权限表现覆盖

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

- 机读：`.workflow/reviews/prototype-review-N.json`（stage/verdict/issues/issue_layer/affected_objects/needs_upstream_sync/next_recommended/reviewed_at）
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
7. 页面覆盖审查必须输出逐项 checklist
8. 不允许笼统结论
