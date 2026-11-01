---
name: spm-prd-review
description: "PRD Review：独立审查 PRD 的读者任务、单一归属、Design 一致性、数据与验收完整性。触发于用户要求审查 PRD；只输出独立第二意见，不修改、修复或推进。"
---

## 路径与资源

从项目根目录读取 `output/` 和 `.workflow/`；从 `$BUNDLE/` 读取 `contracts/`、`references/` 和 `scripts/python/`。

## 职责边界

- Review 是独立第二意见，不是流程门禁，不承担补全 Writing 或 Fix。
- 只审查，不修改 `output/prd/prd.md`、Design 或决策记录，不自动调用 `spm-fix`。
- 审查依赖被审 PRD 模块、模块 Design 依据、Design 修改状态和已有 Review 上下文，不要求额外 Review 资产。
- 输入文件不存在、不可读或完全无法解析时硬阻塞；缺章节、内容不足、冲突和写作质量问题作为审查问题。
- 问题级别按 `contracts/review-checklist.md` 的 `red`、`risk`、`decision` 映射，并按 P0/P1/P2 输出。

## 执行流程

1. 读取 `.workflow/provenance/prd.json` 中目标模块的 Design 输入、`output/prd/prd.md`、Design 修改状态和已有 Review。修改状态只作上下文，不构成门禁。
2. 运行 `python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md`，记录退出码和诊断。脚本失败不等于文字不可审。
3. 运行 `python $BUNDLE/scripts/python/prd-consistency-check.py --project-root . --module <被审模块>`，处理 `deterministic_conflict`、`possible_omission` 和 `needs_semantic_judgment`。无法判断时写“未评估”，不写零冲突。
4. 读取 `contracts/prd-review-checklist.md`、`references/prd-writing-rules.md`、`contracts/prd-writing.profile.json`；命中数据结果时读取 `references/data-definition-rules.md`。需要核对预期时读取 `output/verification/`，但 PRD 验收场景本身必须自包含。
5. 先按模块概览、对象单元、页面功能做读者任务试读。每个对象给后端和测试各 2 至 3 个任务，每个页面给前端 2 至 3 个任务，存在跨对象异常时补恢复任务。任务试读只读当前 PRD 模块，不查 Design、Prototype 或旧 PRD。
6. 记录题目的访问标题顺序、标题切换、答错、追问、被迫猜测和答案是否唯一。必须追问或存在两种合理解释时记 P1；只增加重复阅读时记 P2。
7. 每个对象抽取一条状态迁移、一条公式或阈值、一条异常或并发事实，做全文单一归属抽查。其他位置只能出现对象名、状态名、入口、页面反馈或结果去向。
8. 任务试读完成后读取 Design 依据，检查目标、范围、页面、字段、角色、权限、状态、枚举、流程和未决事项。发现 PRD 新增事实或冲突时标为 P1，并写 `affected_objects`；Design 本身缺失时写 `needs_upstream_sync`。
9. 按公共契约写入 `.workflow/reviews/prd-review-N.md`。结论必须包含任务、位置、影响、建议和未评估范围。
10. 输出后停止，不修改 PRD 或 Design，不调用 Fix，不推进阶段。

## 固定判定

- 后端只读当前模块仍不能确定对象起点、状态、写入、失败保留或终态：P1。
- 前端不查 Prototype 仍不能确定页面任务、区块、字段、操作、反馈或去向：P1。
- 测试不打开验证包仍不能取得输入、预期和精度：P1。
- 同一事实有两份完整定义或两个口径：P1。
- 页面或区块标题带“所属对象”“只读承接”等内部标注：P2。
- 验收场景带规则 ID、验证包位置或追溯说明：P1。
- 同一组数值在对象规则和验收场景重复：P2。
- 空章节、作者说明或“待补充/待定/按配置/按规则处理”掩盖未知：P1。
- 没有可执行验收预期而只有覆盖声明：P1。
- 只有脚本通过，没有任务试读和单一归属抽查：不能宣布通过。