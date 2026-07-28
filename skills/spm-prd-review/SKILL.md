---
name: spm-prd-review
description: "PRD Review——独立审查 PRD 的结构、写作质量、Design 一致性、场景覆盖和未授权高影响事实。用于用户要求 review、审查或检查 PRD 时；不修改 PRD、不自动修复、不自动推进。"
---

## 路径与资源

从当前项目根目录读取 `output/` 和 `.workflow/`；从 `$BUNDLE/`读取 `contracts/`、`schemas/`、`references/` 和 `scripts/python/`。

流程开始时输出模型建议：需要发现业务、权限、状态、跨模块或写作风险时使用深度推理模型；只做明确结构或脚本检查时可用轻量模型；无法判断时使用深度推理模型。

## 职责边界

- Review 是独立第二意见，不是流程门禁，也不承担计划内补全。
- 不修改 `output/prd/prd.md`、Design 或 决策记录，不自动调用 `spm-fix`。
- 不要求 metadata、`page-fields.json` 或其他 Review 存在。
- 只有输入文件不存在、不可读或完全无法解析时才硬阻塞。
- 发现的问题分为确定性问题、产品风险和待用户决策问题。

## 执行流程

1. 读取 `output/design/design.md`、`output/prd/prd.md`、Design confirmation 状态和相关 Review 上下文（如有）；confirmation 只作为上下文，不构成 Review 门禁。
2. 运行：

```text
python $BUNDLE/scripts/python/review-precheck.py --project-root . --stage prd --artifact-file output/prd/prd.md
python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md
```

预检查输出位于 `.workflow/runtime/prd/review-precheck.json`。只有目标文件不存在、不可读或无法解析时停止；缺章节、内容不足、冲突、写作质量问题和 metadata 缺失继续作为审查问题。脚本误报 `can_start_review=false` 时人工核对文件可读性，可读则继续并记录警告。
3. 运行：

```text
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .
```

直接引用 JSON 报告中的 `missing`、`hallucinated`、`attribute_mismatch`，再按检查项补充脚本覆盖不到的语义一致性、人读质量和 Design 未授权事实。
4. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/prd-review-checklist.md`、`$BUNDLE/references/prd-writing-rules.md` 和 `$BUNDLE/contracts/prd-writing.profile.json`。按具体检查项再读取 `$BUNDLE/references/prd-writing-examples.md`、`prd-glossary-format.md`、`prd-versioning.md` 或 `prd-scene-checklist.md`；示例仅在取证需要时加载。按检查清单审查坏味道、三层覆盖、模块/页面/动作组织、字段/状态/权限落点、场景、幻觉和 Design 冲突。
5. 按 `$BUNDLE/schemas/review-result.schema.json` 输出：
   - 机读：`.workflow/reviews/prd-review-N.json`
   - 人读：`.workflow/reviews/prd-review-N.md`
   - 必须包含 `verdict`、`issues`、`issue_layer`、`affected_objects`、`needs_upstream_sync`、`reviewed_at`；P2 记录但不计入 `verdict`。
6. 输出审查结论后停止，不修改任何被审查产物。

## 判定规则

- 共享契约的统一门槛：零 P0/P1 为“通过”；零 P0 且 1 个 P1 为“有问题需修改”；存在 P0 或至少 2 个 P1 为“阻塞”。
- PRD 引入 Design 未授权字段、页面、状态、权限、流程、模块边界，或静默拍板 Design 的“待确认”事实时，必须作为高影响审查问题，并建议回上游。
- 一致性校验是 Review 审查问题依据，不是阻止 Review 开始的门禁。
- Review 通过不等于 Design confirmation，也不自动推进阶段。

## 失败处理

- 预检查或确定性脚本失败：报告具体错误；文件可读时仍可继续人读审查，但不得伪装脚本通过。
- 文件不存在或不可读：输出具体阻塞项，不绕过。
- 共享契约、schema、references 或脚本缺失：报告路径，不凭记忆补写完整清单。
- 不运行 `stage-prep.py`，不生成 metadata，不修改 PRD、Design 或决策记录。
