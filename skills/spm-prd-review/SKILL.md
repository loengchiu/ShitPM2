---
name: spm-prd-review
description: "PRD Review：独立审查 PRD 的业务闭环、写作质量、Design 一致性、场景覆盖、权限状态和未授权高影响事实。触发于用户要求审查 PRD；只输出独立第二意见，不修改、修复或推进。"
---

## 路径与资源

从当前项目根目录读取 `output/` 和 `.workflow/`；从 `$BUNDLE/` 读取 `contracts/`、`schemas/`、`references/` 和 `scripts/python/`。

## 职责边界

- Review 是独立第二意见，不是流程门禁，也不承担计划内补全。
- 只审查，不修改 `output/prd/prd.md`、Design 或决策记录，不自动调用 `spm-fix`。
- 审查只依赖 PRD 模块记录的设计依据与 Design 修改状态，不要求 metadata、`page-fields.json` 或其他 Review 资产存在。
- 只有输入文件不存在、不可读或完全无法解析时才硬阻塞；缺章节、内容不足、冲突和写作质量问题继续作为审查问题。
- 每条问题按 `$BUNDLE/contracts/review-checklist.md` 的 `red`、`risk` 或 `decision` 标注，并按既有 P0/P1/P2 门槛输出。

## 执行流程

1. 读取被审 PRD 模块的 Design 依据（`.workflow/provenance/prd.json` 中该 target 的 `design_inputs` 对应正式 Design 文件）、`output/prd/prd.md`、Design 修改状态和已有 Review 上下文（如有）。修改状态只作为上下文，不构成 Review 门禁。**完成条件**：被审模块、Design 输入闭包和 PRD 均可读；否则输出具体阻塞项并停止。
2. 运行：

```text
python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md
```

目标文件不存在、不可读或无法解析时停止；缺章节、内容不足、冲突和写作质量问题继续作为审查问题。**完成条件**：命令、退出码和诊断已记录；脚本失败未被写成通过。
3. 运行：

```text
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root . --module <被审模块>
```

引用 JSON 中的三类输出：①确定性冲突（`missing`、`hallucinated`、`attribute_mismatch`、权限反转）标为 `red`；②可能遗漏逐条判定为 `risk`、`decision` 或不成立；③`needs_semantic_judgment`（含结构适配差异）按业务语义判定。脚本返回 `0` 不代表 PRD 通过，返回 `1` 也不替代问题定位。**完成条件**：三类输出均已处理；无法提取、可能遗漏和语义判断项已写为明确结论或“未评估”，未被默认通过。
4. 读取 `$BUNDLE/contracts/review-checklist.md`、`$BUNDLE/contracts/prd-review-checklist.md`、`$BUNDLE/references/prd-writing-rules.md`、`$BUNDLE/references/data-definition-rules.md`、`$BUNDLE/references/verification-and-oracle.md` 和 `$BUNDLE/contracts/prd-writing.profile.json`；被审模块命中复杂规则且存在正式 `output/verification/` 文件时读取对应文件，按“验收标准”标题核对规则 ID 是否真实存在、预期输出是否被改写；无验证包时检查是否如实记录缺口，不把缺失伪造成通过。按专项契约的触发证据读取 `$BUNDLE/references/prd-writing-examples.md`、`prd-glossary-format.md`、`prd-versioning.md` 或 `prd-scene-checklist.md`。Review 不再只判断“有没有提到”，而是按动作复杂度检查适用的信息责任；从产品、研发和测试视角各做一次任务式试读：第一次只读“业务流程”判断能否复述具体业务对象从起点到终态，第二次读“业务规则”和“功能说明”判断动作边界、失败保留和状态或金额变化是否可实施，第三次继续读功能说明的页面任务和操作，判断页面区块、字段、按钮、反馈和状态驱动展示是否可承接；存在“页面说明”时补充核对跨动作共用规格。检查“业务流程”是否按具体业务对象拆分并连续叙述，“业务规则”的复杂规则是否有可复算的最小数值例子，“功能说明”是否按页面任务和动作闭环组织，“页面说明”（如存在）是否存在真实复用价值且不重复动作闭环；Review 在记录中核对每个动作能否回溯业务流程的事件并在功能说明本页任务中找到页面、区块和入口，问题只写“动作脱离业务流程”或“动作缺少页面入口”，不要求正文增加追溯说明；检查正文是否出现“对应流程第几步”、流程步骤对照、动作追溯表、映射表或固定回执；检查单块是否堆叠多层事实；对重要数据结果依据 `$BUNDLE/references/data-definition-rules.md` 执行四档责任分类与八类适用问题试读，判断是否存在改变数值或处理的第二种合理实现（若存在或无法写用例则判 P1 / 上游决策）；检查自包含与有效重复（无新增上下文的重复属原地重述），并检查“业务生命线”“动作与页面承接”等新造词和“XX与XX”式硬拼标题。**完成条件**：专项契约的每个适用项均有证据和结论；契约规定的审查顺序、数据口径试读、三层试读、动作内部核对与复杂动作逐项验收已执行；无法判断项已显式标记。
5. 按公共契约写入 `.workflow/reviews/prd-review-N.md`。**完成条件**：结论符合三档门槛，每个 P0/P1 可追溯到位置、影响和建议，三类问题分布及上游同步信息完整。
6. 输出审查结论后停止。**完成条件**：未修改 PRD、Design 或决策记录，未调用 `spm-fix` 或推进阶段。

## 判定与失败

- 结论门槛、问题分级、专项严重度和上游同步条件以公共契约与 PRD 专项契约为准。
- Review 通过不改变 Design 修改状态，也不自动推进阶段。
- 失败处理按公共契约执行；确定性脚本失败但文件可读时继续人读审查并保留原始错误；共享依据缺失时报告具体路径，不凭记忆重建检查项。

- 不能据此宣布的结论：Review 结论不能替代研发试读与人工确认，不能据此宣布 PRD 零缺陷。
