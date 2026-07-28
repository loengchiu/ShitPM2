---
name: spm-prototype-review
description: "原型 review——ShitPM：按需独立挑战，判断原型质量。不要求 metadata，不要求先通过其他 Review，不自动修改产物，不自动推进阶段，不承担计划内补全。结论区分确定性问题、产品风险和待用户决策问题。不代写原型代码。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 模型建议（运行时输出）

流程开始时输出模型等级和推理深度建议（直接复用 PRD §6.3 推荐矩阵）：

- **深度推理模型**：需要发现业务、权限、状态、跨模块或方案风险时
- **轻量模型或脚本**：只做标题、结构、文件、格式和明显缺失检查时
- **无法判断时**：使用深度推理模型

建议必须是实际运行输出，不只是背景说明。

## ShitPM 职责定位

- **独立调用**：可随时调用，不要求先通过其他 Review
- **不要求 metadata**：即使无 metadata 也可执行
- **不自动修改产物**：只输出 verdict + issues，不修改 index.html
- **不自动推进阶段**：输出建议后停止等用户确认
- **不承担计划内补全**：计划内缺口由 spm-prototype 负责，Review 只输出问题
- **结论区分**：确定性问题、产品风险、待用户决策问题

## 预检查（仅在硬阻塞时阻止执行）

运行确定性预检查：

```bash
python $BUNDLE/scripts/python/review-precheck.py --project-root . --stage prototype --artifact-file output/prototype/index.html
```

输出写入 `.workflow/runtime/prototype/review-precheck.json`。

**仅在以下情况阻止 Review 执行**：
- 目标文件 `output/prototype/index.html` 不存在
- 目标文件不可读
- 目标文件完全无法解析（如内容为空、非 HTML、二进制等）

**以下情况不阻止 Review，应作为 Review finding 输出**：
- 缺页面 → Review finding（P0 或 P1）
- 内容不足 → Review finding
- 冲突问题 → Review finding
- 质量问题 → Review finding
- metadata 缺失 → 不阻塞，可在 warnings 中提示

脚本失败或 `can_start_review=false` 时，**人工核查文件存在性和可读性**：
- 文件确实不存在或不可读 → 停止，输出阻塞项
- 文件存在且可读但脚本误报 → 继续执行 Review，在 warnings 中记录

**ShitPM 不要求**：
- metadata 存在
- pages.json 存在
- 其他 Review 通过
- PRD 已生成

## 质量审查

1. **页面覆盖 checklist（ShitPM：直接读 design.md 页面清单）**：

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
5. **Design 未授权高影响行为检查（ShitPM 强化）**：

   逐项审查 Prototype 是否引入了 Design 未授权的高影响行为：
   - 新增页面/状态/权限分支未在 design.md 中出现 → P0
   - 修改 design.md 已定义的状态迁移、操作限制 → P0
   - 静默拍板 design.md 中"待确认"问题 → P0
   - 引入与 design.md 业务流程、跨系统责任、模块边界冲突的交互 → P0

6. **已有 PRD 与 Design 冲突检查**（如 PRD 存在）：
   - PRD 表达与 Design 冲突而 Prototype 未以 Design 为准 → P1
   - Prototype 应以 Design 为准（不以 PRD 为准）；冲突需在 Review finding 中报告

7. **结论分类（ShitPM 新增）**

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

**ShitPM 不再生成 metadata**：
- 不运行 stage-prep.py
- 不写 metadata_generated 字段（或写 false）
- 不更新 status.json 中 metadata_paths

## 失败模式

| 场景 | 一线 | 兜底 |
|------|------|------|
| 预检查脚本失败 | 检查路径和环境 | 人工核查文件存在性，文件可读则继续 Review |
| 文件不存在或不可读 | 输出阻塞项 | 不绕过 |
| 脚本误报 can_start_review=false | 人工核查文件可读性，文件可读则继续 | 在 warnings 中记录 |
| design.md 不存在 | 提示用户先完成 spm-design 并确认 | 不绕过 |

## 硬规则

1. 不代写原型代码
2. 不自行修改 index.html
3. 问题具体到页面和区域
4. 预检查仅在文件不存在/不可读/无法解析时阻止 Review；缺页面、内容不足、冲突、质量问题应作为 finding
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
15. 调用 review-precheck.py 时使用 `--artifact-file` 参数传入目标文件路径，不依赖空 stdin
16. 不要求模型输出思维过程，只输出结论、finding、建议
