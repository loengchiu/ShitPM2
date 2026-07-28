# ShitPM references / templates / contracts 优化验证报告

- **执行日期**：2026-07-28
- **工作区**：`D:\work\ShitPM`
- **执行基线**：`references-optimization-plan.md`
- **结论**：本轮资源重组、消费者同步和静态/回归验证已完成；计划内自动化验证全部通过。

## 一、执行摘要

本轮没有改动批准产品基线、PRD 页面组织或 Prototype 技术架构；随后完成了人读表达的全局复查。核心结果如下：

1. 规则职责已按 `SKILL.md`、`references/`、`templates/`、`contracts/` 和 JSON profile 分离。
2. PRD reference 已从旧入口拆为 rules/examples，并删除旧 `references/prd-writing.md`。
3. Prototype shell 已从通用写法中拆出为条件读取的 `references/prototype-shell.md`。
4. Review 公共执行契约与 Design/PRD/Prototype 专项检查项已分离；三个专项 checklist 使用统一五列表格。
5. `prd-writing.profile.json` 已收缩为程序实际消费的字段。
6. `stage-context.py`、PRD/Prototype/Review Skill 已同步新路径和条件加载策略。
7. 新增 `test-resource-integrity.py`，覆盖路径、链接、目录、profile、消费者和条件资源检查。
8. 纠正 Design 质量标准的职责越界：版本研发阶段的外部基准对比不再进入真实项目运行时；生成自审与独立 Review 只评价当前 Design。
9. 完成人读文档术语复查：建设方式、字段类型、Review 执行术语和旧版兼容说明统一使用中文；机读字段、路径、命令和代码示例按契约保留。

## 二、资源变更

### 2.1 新增

References：

- `references/prd-writing-rules.md`
- `references/prd-writing-examples.md`
- `references/prototype-shell.md`

Contracts：

- `contracts/design-review-checklist.md`
- `contracts/prd-review-checklist.md`
- `contracts/prototype-review-checklist.md`

测试：

- `scripts/python/test-resource-integrity.py`

### 2.2 删除

- `references/prd-writing.md`

删除前已完成全仓消费者扫描；新的 Skill、脚本、contracts、templates 和 references 中没有实际消费者继续读取旧入口。

### 2.3 重组或修正

References：

- `references/design-writing.md`：删除重复的完整状态/流程示例，保留模块、页面、字段、权限、事实源和最终编排规则。
- `references/design-state-format.md`：接管状态流转速览及“状态集合 + 迁移列表”不足的反例。
- `references/design-flow-format.md`：接管简单流程可用一段话表达的例外。
- `references/design-quality-rubric.md`：明确“生成成品自审”和“独立 Review 评分”两个使用区；运行时只评价当前 Design，外部基准对比和版本盲审不进入生成或 Review 资源。
- `references/prototype-writing.md`：保留通用基座、Design 事实源、页面落位和视觉规则，修正 PRD 不是生成前置的错误。
- `references/align-writing.md`、`contracts/fix-propagation-rules.md`、`contracts/metadata-anchor-rules.md`：统一失败模式表格式，并保留各自独有规则和兜底。

Templates：

- `templates/prd.md`：收缩为版本、章节、模块/页面/动作和字段结构骨架。
- `templates/prototype-feedback-classification.md`：收缩为反馈分类和记录结构。

Contracts：

- `contracts/review-checklist.md`：只保留公共 Review 执行契约。
- 三个专项 checklist：保留对应检查内容，统一为“检查项 / 触发证据 / 权威规则来源 / 默认严重度 / 输出位置”映射。
- `contracts/prd-writing.profile.json`：删除无程序消费者的历史字段，仅保留 `forbidden_expressions` 数组及元信息。

Consumers：

- `scripts/python/stage-context.py`
- `skills/spm-design-review/SKILL.md`
- `skills/spm-fix/SKILL.md`
- `skills/spm-prd-review/SKILL.md`
- `skills/spm-prd/SKILL.md`
- `skills/spm-prototype-review/SKILL.md`
- `skills/spm-prototype/SKILL.md`

## 三、职责与加载策略验证

### 3.1 已确认的权威来源

- Design 状态：`references/design-state-format.md`
- Design 业务流程：`references/design-flow-format.md`
- Design 质量：`references/design-quality-rubric.md`
- PRD 人读规则：`references/prd-writing-rules.md`
- PRD 示例：`references/prd-writing-examples.md`
- PRD 禁用表达：`contracts/prd-writing.profile.json` 的 `constraints.forbidden_expressions`
- Prototype 通用写法：`references/prototype-writing.md`
- Prototype 多页面 shell：`references/prototype-shell.md`
- Review 公共执行：`contracts/review-checklist.md`
- Review 专项检查：三个专项 checklist
- 跨阶段传播：`contracts/fix-propagation-rules.md`
- 旧版 metadata：`contracts/metadata-anchor-rules.md`，仅旧 metadata 存在时读取

### 3.2 运行时质量边界

- `references/design-quality-rubric.md` 只把批准产品目标转成当前 Design 的可观察质量要求，不读取或比较外部基准产物。
- `spm-design` 只读取生成成品自审部分，不输出 L0–L3 评分或 Review 审查结论，也不得根据量表补写未授权产品事实。
- `spm-design-review` 可对当前 Design 做五维评分；评分写入人读 Review，机读结果仍服从公共 schema，不要求额外比较产物。
- 版本研发阶段的外部对标、测试集比较和盲评不属于真实项目的 Skill、参考文档或 Review 输入。

### 3.3 条件读取确认

- `prd-writing-examples.md` 不在 `stage-context.py` 的 PRD 最小集合中，仅在高复杂动作、组织方式无法直接判断、自检命中失败模式或用户要求对照示例时读取。
- `prototype-shell.md` 不在 Prototype 最小集合中，仅在多页面、共享 shell、路由、导航激活或空白页问题时读取。
- `metadata-anchor-rules.md` 不参与新主流程，仅在检测到旧 metadata 时读取。
- 三个 Review Skill 均读取公共 Review 契约和正确的专项检查清单；Design Review 另读取质量标准的独立 Review 部分。

## 四、自动化验证结果

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 资源完整性 | `python scripts/python/test-resource-integrity.py` | **通过**：路径、相对链接、目录、profile、stage-context、运行时质量边界、旧路径消费者和专项 checklist 均正常 |
| ShitPM 回归 | `python scripts/python/test-shitpm-regression.py` | **通过**：32 通过，0 失败 |
| 反幻觉准备 | `python scripts/python/test-anti-hallucination.py prepare` | **通过**：生成固定测试 metadata 并注入预期幻觉 |
| 反幻觉验证 | `python scripts/python/test-anti-hallucination.py verify` | **通过**：4 类预期幻觉全部检出 |
| 反幻觉清理 | `python scripts/python/test-anti-hallucination.py clean` | **通过**：测试产物清理完成 |
| `stage-context.py` 可执行性 | `python scripts/python/stage-context.py --help` | **通过** |
| Git 空白检查 | `git diff --check` | **通过** |

回归场景以脚本当前实际 `SCENARIOS` 为准，本次确认是 **32 个场景**，没有使用过期的“28 项”口径。

## 五、行为和边界核对

已保留或验证的关键行为：

- Design 首次生成仍承担业务流程、角色权限、状态、异常、跨系统责任、方案权衡和成品自审责任。
- 简单模式不因完整模式 rubric 而生成无关空章节。
- PRD 和 Prototype 仍是 Design 的两个并列直接下游。
- Prototype 无 PRD 时仍可生成；PRD 只作为可选冲突线索，不能覆盖 Design。
- Review 仍是独立第二意见，不修改产物、不自动 Fix、不自动推进阶段。
- Prototype 表现问题与语义问题仍必须分离；语义问题按传播契约回上游。
- metadata、决策记录、旧 Review 结果和 ABC 中间分析没有被提升为下游事实源。
- `spm-prototype-mark` 业务 Skill 未修改，仅纳入路径和回归验证范围。

## 六、未修改与保护项

以下内容未被本轮修改：

- `output/shitpm-v2-prd.md`
- `output/shitpm-v2-implementation-design.md`
- `skills/spm-prototype-mark/SKILL.md`
- `README.md`、`USAGE.md` 和 `AGENTS.md` 已同步清理人读术语，不属于批准产品基线。

Git 未执行 `commit` 或 `push`。

## 七、全局人读表达审计补充

本次全局扫描范围为 `AGENTS.md`、`README.md`、`USAGE.md`、`skills/`、`references/`、`templates/` 和 `contracts/`。确认并修复以下同类问题：

1. `references/prd-writing-examples.md` 中的 `string` 字段类型改为“文本”，并删除已失效的 `constraints.granularity.three_layers` 引用。
2. `references/design-state-format.md` 与 `references/design-flow-format.md` 的人读示例改用中文状态、字段和流程表达；Prototype 源码示例中的机读状态值保持不变。
3. `contracts/review-checklist.md`、三个专项 Review 契约及三个 Review Skill 中，将 `precheck`、`finding`、`verdict`、`reviewer`、`writer`、`legacy` 等人读说明改为中文；`verdict`、`issues` 等 JSON 字段以反引号保留。
4. `references/design-quality-rubric.md`、`AGENTS.md` 和其他入口文档不再把 Park 或外部基准产物作为真实项目运行时的比较对象。

扫描结果：`iteration`、`new_build`、`hybrid`、失效 PRD profile 引用和人读资源中的 Park/盲审残留均为零。

## 八、已知限制与剩余风险

1. 本轮主要是资源职责、引用和加载策略重组；没有重新生成一套完整 Design/PRD/Prototype 产物做逐字语义等价比较，行为验证以现有 32 个回归场景、反幻觉验证和静态资源校验为主。
2. 没有在本轮生成新的浏览器 Prototype 页面，因此没有增加一次真实浏览器渲染截图级验收；Prototype 相关路径、shell 条件加载和一致性门禁已完成静态与回归验证。
3. 专项 Review checklist 已从原大清单改为检查项映射；详细生成规则依赖 reference 链接。若后续发现某个 Review 场景仍缺少证据解释，应补充对应 reference，不应把生成政策重新复制回 checklist。
4. `references-optimization-plan.md` 已更新为本轮执行基线，但仍是未提交工作区文件；是否纳入后续版本控制由用户决定。

## 九、最终判定

**验证通过，可以进入人工内容审查或后续提交准备。**

本轮没有发现会阻断资源解析、Skill 加载、回归门禁或反幻觉检测的错误；剩余风险主要是未生成新下游产物进行视觉/语义人工对照，不影响本轮资源重组的自动化验收结论。
