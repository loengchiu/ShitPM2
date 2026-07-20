---
name: spm-prototype-review
description: "原型 review——vNext：按需独立挑战，判断原型质量。不要求 metadata，不要求先通过其他 Review，不自动修改产物，不自动推进阶段，不承担计划内补全。结论区分确定性问题、产品风险和待用户决策问题。不代写原型代码。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## vNext 职责定位

- **独立调用**：可随时调用，不要求先通过其他 Review
- **不要求 metadata**：即使无 metadata 也可执行
- **不自动修改产物**：只输出 verdict + issues，不修改 index.html
- **不自动推进阶段**：输出建议后停止等用户确认
- **不承担计划内补全**：计划内缺口由 spm-prototype 负责，Review 只输出问题
- **结论区分**：确定性问题、产品风险、待用户决策问题

## 执行顺序（两段式）

### 第一段：预检查（结构完整性）

1. `python $BUNDLE/scripts/python/review-precheck.py --project-root . --stage prototype --artifact-file output/prototype/index.html` → `.workflow/runtime/prototype/review-precheck.json`
2.  脚本失败或 `can_start_review=false` → 停止，输出阻塞项
3. 检查 index.html 存在且有效

 有阻塞 → 停止，不进入第二段。

**vNext 不要求**：
- metadata 存在
- pages.json 存在
- 其他 Review 通过
- PRD 已生成

### 第二段：质量审查

1. **页面覆盖 checklist（vNext：直接读 design.md 页面清单）**：

   读取 `output/design/design.md` 中"页面清单"章节，提取 design 定义的全部页面。

   逐项输出对比结果（结构化）：
   - design 每个页面 × 原型 HTML → [存在/缺失/幻觉]
   - 原型出现的页面不在 design → 标记为幻觉

   判定：
   - 幻觉页面 = P0
   - 缺失页面 = P1（缺失率 > 50% 升级 P0）

2. 状态表达覆盖核心状态
3. 交互主路径覆盖
4. 权限表现覆盖
5. **Design 未授权高影响行为检查（vNext 强化）**：

   逐项审查 Prototype 是否引入了 Design 未授权的高影响行为：
   - 新增页面/状态/权限分支未在 design.md 中出现 → P0
   - 修改 design.md 已定义的状态迁移、操作限制 → P0
   - 静默拍板 design.md 中"待确认"问题（design decision-notes.md 中"待确认"类目） → P0
   - 引入与 design.md 业务流程、跨系统责任、模块边界冲突的交互 → P0

6. **结论分类（vNext 新增）**

   输出 verdict 时必须区分：
   - **确定性问题**：页面缺失、状态表达不闭环、明显幻觉、Design 未授权高影响行为等可判定的问题
   - **产品风险**：交互方案权衡可能存在但需要业务判断的问题
   - **待用户决策问题**：Design 待确认项被静默拍板、高影响缺口等需要用户定夺的问题

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞**：有 P0 或 2+ 个 P1

| 级别 | 示例 |
|------|------|
| P0 | 页面结构缺失、交互主路径不通、Design 未授权高影响行为 |
| P1 | 状态表达不完整、权限不覆盖 |
| P2 | 稳定 ID 泄漏（写入 issues 不计 verdict）|

issue_layer：`{"structure":N,"content":N,"consistency":N}`。

## 输出

- 机读：`.workflow/reviews/prototype-review-N.json`（stage/verdict/issues/issue_layer/affected_objects/needs_upstream_sync/next_recommended/reviewed_at）
- 人读：`.workflow/reviews/prototype-review-N.md`（结论/主要问题/分类（确定性问题/产品风险/待用户决策）/是否回上游/下一步）

 输出 verdict 后停止等用户确认。

**vNext 不再生成 metadata**：
- 不运行 stage-prep.py
- 不写 metadata_generated 字段（或写 false）
- 不更新 status.json 中 metadata_paths

## 失败模式

| 场景 | 一线 | 兜底 |
|------|------|------|
| 预检查脚本失败 | 检查路径和环境 | 停下，不跳过 |
| can_start_review=false | 输出阻塞项 | 不绕过 |
| 假阳性 | 列出 warnings 等确认 | 确认后继续 |
| design.md 不存在 | 提示用户先完成 spm-design 并确认 | 不绕过 |

## 硬规则

1. 不代写原型代码
2. 不自行修改 index.html
3. 问题具体到页面和区域
4. 预检查失败不跳过
5. P2 写入 issues 但不计入 verdict
6. review 通过后不自动推进
7. 页面覆盖审查必须输出逐项 checklist
8. 不允许笼统结论
9. 不要求 metadata 存在
10. 不要求先通过其他 Review
11. 不承担计划内补全
12. 结论必须区分确定性问题、产品风险、待用户决策问题
13. 不运行 stage-prep.py 生成 metadata
14. 不自动调用 spm-fix 回写 Design（仅输出 needs_upstream_sync 建议）
