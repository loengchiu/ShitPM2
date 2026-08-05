---
name: spm-prd-review
description: "PRD Review——独立审查 PRD 的业务闭环结构、写作质量、Design 一致性、场景覆盖、权限状态和未授权高影响事实。用于用户要求 review、审查或检查 PRD 时；不修改 PRD、不自动修复、不自动推进。"
---

## 路径与资源

从当前项目根目录读取 `output/` 和 `.workflow/`；从 `$BUNDLE/` 读取 `contracts/`、`schemas/`、`references/` 和 `scripts/python/`。

流程开始时根据问题复杂度选择推理深度；涉及业务闭环、权限、状态、跨模块或高影响事实时使用深度推理模型，无法判断时按深度推理模型处理。

## 职责边界

- Review 是独立第二意见，不是流程门禁，也不承担计划内补全。
- 只审查，不修改 `output/prd/prd.md`、Design 或决策记录，不自动调用 `spm-fix`。
- 审查只依赖 Design、PRD 与确认状态，不要求 metadata、`page-fields.json` 或其他 Review 资产存在。
- 只有输入文件不存在、不可读或完全无法解析时才硬阻塞；缺章节、内容不足、冲突和写作质量问题继续作为审查问题。
- 发现的问题分为确定性问题、产品风险和待用户决策问题，并按既有 P0/P1/P2 门槛输出。

完成判据：审查清单全部逐项执行并记录结论；产出含结论、问题清单（位置/影响/建议）；无修改产物、无自动推进；无法判断项已显式标注而非默认通过。

## 执行流程

1. 读取 `output/design/design.md`、`output/prd/prd.md`、Design confirmation 状态和已有 Review 上下文（如有）。confirmation 只作为上下文，不构成 Review 门禁。
2. 运行：

```text
python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md
```

目标文件不存在、不可读或无法解析时停止；缺章节、内容不足、冲突和写作质量问题继续作为审查问题。
3. 运行：

```text
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .
```

引用 JSON 中的三类输出：①确定性冲突（`missing`、`hallucinated`、`attribute_mismatch`、权限反转）直接采用为问题；②可能遗漏（脚本标注可能冲突但需人工确认）逐条判定；③`needs_semantic_judgment` 语义判断项——含**结构适配差异**（Design 用枚举表达状态而 PRD 改写为独立状态字段、对象合并/拆分后字段归属不一致等结构性改法差异）——由 Review 按业务语义判定，不因脚本无法确认而默认通过。脚本返回 `0` 不代表 PRD 通过，返回 `1` 也不替代问题定位。
4. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/prd-review-checklist.md`、`$BUNDLE/references/prd-writing-rules.md` 和 `$BUNDLE/contracts/prd-writing.profile.json`。按取证需要读取 `$BUNDLE/references/prd-writing-examples.md`、`prd-glossary-format.md`、`prd-versioning.md` 或 `prd-scene-checklist.md`。重点审查：
   - 是否按业务闭环组织，模块边界和模块独立可读是否成立；
   - 管理端和移动端是否落在同一闭环的真实阶段；页面映射与正文落点是否一致；
   - 按模块检查 `4.x.6 功能详细说明` 是否存在且非空，页面是否在该章节落点，而不是只出现在页面清单；
   - 页面区块和动作是否被压缩成空泛摘要，高影响字段、状态、权限、异常和恢复是否有实际落点；
   - 是否出现角色页、组织页、审批页等页面语义被重新解释的问题（如被合并成无差别的“系统配置”摘要）；
   - 对象、字段、状态、权限、异常、恢复、验收和待确认事项是否就近且无冲突；
   - Design 事实是否完整承接，是否出现未授权页面、字段、状态、权限、流程、默认值或外部行为；
   - 页面展示行为是否可回读：所属业务侧、入口/菜单/路由、业务阶段、返回目标、区块目的、无权限、加载中/骨架屏、空态、异常态、超长文本、默认值、标签颜色和状态驱动操作；
   - 自动动作是否有失败处理或待确认；删除/软删除/停用/撤回/作废/归档是否有对象、关联、附件、历史、引用和恢复/审计传播规则；
   - 待办、提醒、编号、字典、文件/档案、审计侧/被审侧入口、枚举来源以及分页、导出、批量、首页和文件限制是否有具体来源或待确认；
   - 查询、统计、表单、配置、跨系统等适用场景是否写清产品结果，是否用经验补造数字；
   - 流程图是否使用 draw.io 源文件和 PNG，图文是否一致；
   - 是否有标签式正文（含“触发：”“处理：”“成功结果：”“失败与恢复：”等行首标签）、流水账、表格主导、模糊跨节引用、AI 痕迹和明确占位符。
5. 按 `$BUNDLE/schemas/review-result.schema.json` 输出既有格式：
   - 机读：`.workflow/reviews/prd-review-N.json`
   - 人读：`.workflow/reviews/prd-review-N.md`
   - 必须包含 `verdict`、`issues`、`issue_layer`、`affected_objects`、`needs_upstream_sync`、`reviewed_at`；P2 记录但不计入 `verdict`。
6. 输出审查结论后停止，不修改任何被审查产物。

## 判定规则

- 共享契约的统一门槛：零 P0/P1 为“通过”；零 P0 且 1 个 P1 为“有问题需修改”；存在 P0 或至少 2 个 P1 为“阻塞”。
- 有页面或业务动作的模块缺少 `4.x.6 功能详细说明`、`4.x.6` 为空、页面只出现在清单未落正文、或页面/动作被压缩成模块摘要时，按结构或内容层 P1 处理。
- PRD 引入 Design 未授权字段、页面、状态、权限、流程、模块边界，或静默拍板 Design 的“待确认”事实时，必须作为高影响审查问题，并在需要时建议回上游。
- 一致性校验是 Review 审查问题依据，不是阻止 Review 开始的门禁。
- Review 通过不等于 Design confirmation，也不自动推进阶段。

## 失败处理

- 预检查或确定性脚本失败：报告具体错误；文件可读时仍可继续人读审查，但不得伪装脚本通过。
- 文件不存在或不可读：输出具体阻塞项，不绕过。
- 共享契约、schema、references 或脚本缺失：报告路径，不凭记忆补写清单。
- 不运行 `stage-prep.py`，不生成 metadata，不修改 PRD、Design 或决策记录。
