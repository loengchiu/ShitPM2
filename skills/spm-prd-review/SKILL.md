---
name: spm-prd-review
description: "PRD review——ShitPM：按需独立挑战，判断 PRD 正文质量。不要求 metadata，不要求先通过其他 Review，不自动修改产物，不自动推进阶段，不承担计划内补全。结论区分确定性问题、产品风险和待用户决策问题。不代写 PRD 正文。"
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
- **不自动修改产物**：只输出 verdict + issues，不修改 prd.md
- **不自动推进阶段**：输出建议后停止等用户确认
- **不承担计划内补全**：计划内缺口由 spm-prd 负责，Review 只输出问题
- **结论区分**：确定性问题、产品风险、待用户决策问题

## 预检查（仅在硬阻塞时阻止执行）

运行确定性预检查：

```bash
python $BUNDLE/scripts/python/review-precheck.py --project-root . --stage prd --artifact-file output/prd/prd.md
```

输出写入 `.workflow/runtime/prd/review-precheck.json`。

**仅在以下情况阻止 Review 执行**：
- 目标文件 `output/prd/prd.md` 不存在
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

文风检查：运行 `python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md`。
检查 prd.md 无稳定 ID 泄漏。

**ShitPM 不要求**：
- metadata 存在
- page-fields.json 存在
- 其他 Review 通过

## 人读质量审查

1. **坏味道**：标签式正文/动作流水账/纯表格/过多加粗/模糊表述
2. **三层覆盖**：界面元素与展示规则/交互逻辑与状态流转/异常处理与边界
3. **一致性（脚本兜底 + LLM 语义增强）**：

   运行确定性结构对比（ShitPM：直接读取人读 design.md 与 prd.md，不依赖 metadata）：
   ```bash
   python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .
   ```

   直接引用脚本 JSON 报告中的 missing/hallucinated/attribute_mismatch 项。

   然后 LLM 补充检查（脚本无法覆盖的部分）：
   - 规则 checklist：读取 `output/design/design.md` 中规则与状态机章节，每条规则 × PRD 正文 → [存在/缺失]

   判定：
   - 脚本报告的 hallucinated 项 = P0
   - 脚本报告的 missing 项 = P1（缺失率 > 50% 升级 P0）
   - 脚本报告的 attribute_mismatch 项 = P1
   - LLM 发现的规则缺失 = P1

4. **结构**：每个小模块末尾含字段定义、状态机归位内容；大模块开头含权限规则归位；状态机按核心业务对象组织，含状态集合/迁移/触发动作和限制条件；权限规则含页面级/按钮级权限

5. **Design 未授权高影响事实检查（ShitPM 强化）**：

   逐项审查 PRD 是否引入了 Design 未授权的高影响产品事实：
   - 新增模块/页面/字段/状态/权限规则未在 design.md 中出现 → P0
   - 修改 design.md 已定义的字段类型、必填、枚举值、状态迁移 → P0
   - 静默拍板 design.md 中"待确认"问题 → P0
   - 引入与 design.md 业务流程、跨系统责任、模块边界冲突的描述 → P0

6. **已有 Prototype 与 Design 冲突检查**（如 Prototype 存在）：
   - Prototype 表达与 Design 冲突而 PRD 未报告 → P1
   - PRD 应以 Design 为准，并在 decision-notes.md 中报告冲突（如 PRD 生成时已报告则不重复报）

7. **结论分类（ShitPM 新增）**

   输出 verdict 时必须区分：
   - **确定性问题**：结构性缺失、密度不达标、明显幻觉、Design 未授权高影响事实等可判定的问题
   - **产品风险**：方案权衡可能存在但需要业务判断的问题
   - **待用户决策问题**：Design 待确认项被静默拍板、高影响缺口等需要用户定夺的问题

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞**：有 P0 或 2+ 个 P1

| 级别 | 示例 |
|------|------|
| P0 | 核心章节缺失、设计边界违反、幻觉项（PRD 引入 design 不存在的实体）、Design 未授权高影响事实、缺失率>50% |
| P1 | 缺失项（design 有 PRD 没写，但缺失率≤50%）、页面缺展示规则、状态变化缺失 |
| P2 | lint warning、稳定 ID 泄漏（写入 issues 不计 verdict）|

issue_layer：`{"structure":N,"content":N,"consistency":N}`。

## 输出

- 机读：`.workflow/reviews/prd-review-N.json`（stage/verdict/issues/issue_layer/affected_objects/needs_upstream_sync/next_recommended/reviewed_at）
- 人读：`.workflow/reviews/prd-review-N.md`（结论/主要问题/分类（确定性问题/产品风险/待用户决策）/是否回上游/下一步）

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
| design.md 不存在 | 提示用户先完成 spm-design 并确认 | 不绕过 |

## 硬规则

1. 不代写 PRD 正文
2. 不自行修改 prd.md
3. 问题具体到页面/章节/内容
4. 预检查仅在文件不存在/不可读/无法解析时阻止 Review；缺章节、内容不足、冲突、质量问题应作为 finding
5. P2 写入 issues 但不计入 verdict
6. review 通过后不自动推进
7. 脚本报告的 missing/hallucinated/attribute_mismatch 项逐条列出；为零时直接引用脚本结论
8. LLM 补充检查（规则覆盖）必须逐项列出，不允许笼统结论
9. 幻觉项（PRD 有 design 没有）必须标 P0，不放过
10. Design 未授权高影响事实必须标 P0，不放过
11. 不要求 metadata 存在
12. 不要求先通过其他 Review
13. 不承担计划内补全
14. 结论必须区分确定性问题、产品风险、待用户决策问题
15. 不运行 stage-prep.py 生成 metadata
16. 不自动调用 spm-fix 回写 Design（仅输出 needs_upstream_sync 建议）
17. 调用 review-precheck.py 时使用 `--artifact-file` 参数传入目标文件路径，不依赖空 stdin
18. 不要求模型输出思维过程，只输出结论、finding、建议
