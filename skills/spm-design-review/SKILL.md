---
name: spm-design-review
description: "设计 review——ShitPM：按需独立挑战，判断 design 基线质量。不要求 metadata，不要求先通过其他 Review，不自动修改产物，不自动推进阶段，不承担计划内补全。结论区分确定性问题、产品风险和待用户决策问题。不代写 design 正文。"
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
- **不自动修改产物**：只输出 verdict + issues，不修改 design.md
- **不自动推进阶段**：输出建议后停止等用户确认
- **不自动确认 Design**：Review 通过不等于 Design 已确认
- **不承担计划内补全**：计划内缺口由 spm-design 负责，Review 只输出问题
- **结论区分**：确定性问题、产品风险、待用户决策问题

## 预检查（仅在硬阻塞时阻止执行）

运行确定性预检查：

```bash
python $BUNDLE/scripts/python/review-precheck.py --project-root . --stage design --artifact-file output/design/design.md
```

输出写入 `.workflow/runtime/design/review-precheck.json`。

**仅在以下情况阻止 Review 执行**：
- 目标文件 `output/design/design.md` 不存在
- 目标文件不可读
- 目标文件完全无法解析（如内容为空、非 Markdown、二进制等）

**以下情况不阻止 Review，应作为 Review finding 输出**：
- 缺章节 → Review finding（P0 或 P1）
- 内容不足 → Review finding
- 冲突问题 → Review finding
- 质量问题 → Review finding
- metadata 缺失 → 不阻塞，可在 warnings 中提示

脚本失败或 `can_start_review=false` 时，**人工核查文件存在性和可读性**：
- 文件确实不存在或不可读 → 停止，输出阻塞项
- 文件存在且可读但脚本误报 → 继续执行 Review，在 warnings 中记录

**ShitPM 不要求**：
- metadata 存在
- page-fields.json 存在
- 其他 Review 通过

## 人读质量审查

### A. 密度审查（按列逐项查，缺列或缺值即 P1）

1. **字段定义密度**：每张字段表必须 9 列齐全 `字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明`；无值属性写"—"不留空；缺列或缺值的表定位到具体实体名报 P1
2. **状态机密度**：每张状态机表必须 6 列齐全 `状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件`；"操作人"必须到角色（"用户""系统"等模糊主体即 P1）；"限制条件"不能省略（写"—"仅限真正无限制）；终态未占行即 P1；缺列或缺值的表定位到具体实体名报 P1

### A2. 状态机闭环审查（按 `references/design-state-format.md` 闭环要求 8 条逐项查，违反即 P1）

3. **结构层（脚本校验）**：运行 `python $BUNDLE/scripts/python/state-machine-check.py --project-root .`，直接引用输出 JSON 中的 violations。脚本覆盖 4 条：
   - non_terminal_must_have_exit：非终态至少一条正向迁移，悬空即 P1
   - non_initial_must_have_entry：非初始状态至少一条迁移指向它，孤岛即 P1
   - rollback_target_illegal：回退/驳回的"下一状态"必须在正向可达路径上，回退到从未经历的状态即 P1
   - transition_ambiguity：同一"触发动作 + 操作人"组合在不同状态下指向冲突的"下一状态"，P2 提示人审是否有业务理由

   ShitPM：脚本无 states.json 时降级为基于 design.md 解析；解析失败时跳过结构层检查，仅人审业务层。

4. **业务层（人审，逐张状态机表检查）**：
   - 合法出路全覆盖：从业务语义看当前状态所有合法操作（推进/撤回/退回/驳回/取消），少一种即 P1
   - 二次流转闭环：回退/驳回后的状态必须能再次推进回原路径，死锁即 P1
   - 操作人匹配业务角色：迁移的"操作人"与业务角色职责不一致即 P1（如业务上组长/主审才能发征求意见，状态机写编制人即 P1）
   - 状态语义与迁移自洽：状态含义描述的待办事项必须有对应出路迁移，断链即 P1

### B. 完整性审查

5. 权限定义覆盖到字段级，按"页面 > 角色 > 字段权限例外"组织
6. 模块/页面/字段能在 align.md 或用户原始需求中找到来源（不新增未确认范围）
7. 关键表格结构性检查

### C. 高影响缺口暴露审查（ShitPM 强化）

8. 业务流程、角色权限、数据范围、状态转换、模块边界、跨系统责任、异常路径和方案权衡是否存在静默缺口
9. 是否存在"推迟给下游"的高影响问题
10. 是否存在未经用户确认的高影响假设
11. **影响下游的未决事实是否在 design.md 中可见**（不能只藏在 decision-notes.md 中）

### D. 结论分类（ShitPM 新增）

输出 verdict 时必须区分：
- **确定性问题**：结构性缺失、密度不达标、明显幻觉等可判定的问题
- **产品风险**：方案权衡可能存在但需要业务判断的问题
- **待用户决策问题**：高影响缺口、未确认假设等需要用户定夺的问题

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞**：有 P0 或 2+ 个 P1

| 级别 | 含义 | 示例 |
|------|------|------|
| P0 | 阻塞 | 核心章节缺失、新增未确认范围、高影响缺口静默 |
| P1 | 影响质量 | 字段属性缺失、权限未覆盖字段级、状态机不闭环 |
| P2 | 格式 | lint warning（写入 issues 不计 verdict） |

issue_layer：`{"structure":N,"content":N,"consistency":N}`，三个整数必填。

## 输出

- 机读：`.workflow/reviews/design-review-N.json`（stage/verdict/issues/issue_layer/affected_objects/needs_upstream_sync/next_recommended/reviewed_at）
- 人读：`.workflow/reviews/design-review-N.md`（结论/主要问题/分类（确定性问题/产品风险/待用户决策）/是否回上游/下一步）

输出 verdict 后停止等用户确认，不自动推进。

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
| 人读发现 P0 | 输出阻塞 verdict | 停止 |
| state-machine-check.py 依赖 states.json 不存在 | 降级为基于 design.md 解析 | 解析失败时仅人审业务层 |

## 硬规则

1. 不代写 design 正文
2. 不自行修改 design.md
3. 问题具体到章节和内容
4. 预检查仅在文件不存在/不可读/无法解析时阻止 Review；缺章节、内容不足、冲突、质量问题应作为 finding
5. P2 写入 issues 但不计入 verdict
6. review 通过后不自动推进
7. review 通过不等于 Design 已确认（用户需另行运行 design-confirmation.py confirm）
8. 不要求 metadata 存在
9. 不要求先通过其他 Review
10. 不承担计划内补全
11. 结论必须区分确定性问题、产品风险、待用户决策问题
12. 不运行 stage-prep.py 生成 metadata
13. 不自动调用 spm-fix 回写 Design（仅输出 needs_upstream_sync 建议）
14. 调用 review-precheck.py 时使用 `--artifact-file` 参数传入目标文件路径，不依赖空 stdin
15. 不要求模型输出思维过程，只输出结论、finding、建议
