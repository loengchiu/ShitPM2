# ShitPM references / templates / contracts 内容优化计划（执行基线）

> 本文件是本轮执行基线。目标是让每条规则只有一个权威来源，并让 Skill 按任务条件读取资源；不追求“一件事一个文件”，也不讨论 Skill 自带 references 或文件归属问题，统一使用 Plugin 根目录资源。

## 一、职责边界

| 资源 | 唯一职责 |
| --- | --- |
| `SKILL.md` | 阶段职责、输入顺序、门禁、执行流程、停止条件、写入顺序和事实源边界 |
| `references/` | 详细分析方法、写作规则、业务语义、正反例和按场景查阅说明 |
| `templates/` | 输出骨架、固定标题、表格列和占位结构，不定义业务政策 |
| `contracts/` | 跨 Skill 共用的传播、Review、导航和 legacy 兼容契约 |
| JSON profile / schema | 程序实际消费、可以确定性校验的机读约束 |

硬规则使用“必须/不得”，建议使用“推荐/不推荐”，示例内容使用“示例/反例”。失败模式速查表与反例黑名单统一为六列表：

```text
| 级别 | 场景 | 识别信号 | 为什么错 | 首选修复 | 仍失败处理 |
```

超过 100 行的 Markdown 资源必须有可跳转目录；资源文档使用相对 Markdown 链接，Skill 使用完整 `$BUNDLE/references/...`、`$BUNDLE/templates/...` 或 `$BUNDLE/contracts/...` 路径，并写明读取时机。模板不写内部路径。

## 二、references 调整

保留原有 Design 六文件和 Align 单文件；References 最终为 14 个文件。

### PRD

删除 `references/prd-writing.md`，新增：

- `references/prd-writing-rules.md`：PRD 事实源边界、复杂度、编号、模块/小模块/页面/动作组织、字段/状态/权限落位、PRD 整体业务流程、写作和交付检查。
- `references/prd-writing-examples.md`：只保存字段、页面、动作、区块、小模块、业务流程的正反例。

`prd-glossary-format.md`、`prd-versioning.md`、`prd-scene-checklist.md` 继续作为各自主题的权威来源；PRD 业务流程保留自身职责，不引用 Design 流程规范替代。

### Prototype

保留并收缩 `references/prototype-writing.md`，新增 `references/prototype-shell.md`。通用基座、Design 唯一事实源、daisyUI、页面落位和视觉细节留在 `prototype-writing.md`；多页面 shell、共享布局、导航激活、路由和空白页防护迁入 `prototype-shell.md`。shell 只在多页面、共享 shell 或路由/空白页问题时读取；单页面和普通局部样式不读取。Prototype 不以 PRD 为生成前置，PRD 只可选辅助，冲突时 Design 优先。

### Design / Align

Design 六文件不继续按章节拆分：

- `design-state-format.md` 接管状态流转速览和“状态集合 + 迁移列表”不足的反例。
- `design-flow-format.md` 接管简单流程可用一段话表达的例外。
- `design-writing.md` 保留模块、页面、字段、权限、事实源和最终编排规则，删除重复的完整状态/流程正例，并链接到对应 reference。
- `design-quality-rubric.md` 明确分为“生成成品自审”和“独立 Review 评分”两个使用区；生成自审不输出评分，独立 Review 的五维评分只评价当前 Design。外部基准对比和版本盲审只属于 V2 研发验收，不进入真实项目会加载的 Skill、reference 或 Review 资源。
- `align-writing.md` 不拆分，保留目标、范围、建设方式判断、追问触发条件和兜底。

## 三、templates 调整

保持 7 个模板。模板只保留结构骨架、固定标题、表格列和占位结构：

- `design.md`：保留可选章节、状态六列表头和内容落位，不重复 ABC、Review 或生成机制。
- `prd.md`：保留版本、章节层级、模块/小模块/页面/动作骨架和字段结构，不复制 glossary、流程密度和字段/状态/权限政策。
- `prototype-feedback-classification.md`：只保留表现问题、语义问题和反馈项的记录结构。
- `prototype.html`：保留可运行 HTML + Vue + Tailwind + daisyUI + 本地 lib 最小骨架。
- `align.md`、`decision-notes.md`、`start-report.md`：保留固定输出结构和“无”的表达。

## 四、contracts 调整

保持公共传播和导航契约，Contracts 最终为 8 个文件。

- `review-checklist.md`：只保留 Review 独立性、precheck 硬阻塞边界、P0/P1/P2、verdict、`needs_upstream_sync`、机读/人读结构和共同禁止事项。
- 新增 `design-review-checklist.md`、`prd-review-checklist.md`、`prototype-review-checklist.md`。三个专项文件统一使用：

  ```text
  | 检查项 | 触发证据 | 权威规则来源 | 默认严重度 | 输出位置 |
  ```

  只映射产物检查项，不复制生成规则；详细规则使用相对链接指向 reference。
- `fix-propagation-rules.md` 是跨阶段传播唯一来源；Prototype 语义反馈按该 contract 传播。
- `start-action-matrix.md` 只定义动作可用性、Design confirmation 和动作级模型建议；`start-report.md` 只展示。
- `metadata-anchor-rules.md` 只在检测到旧 metadata 时读取，不参与新主流程，也不成为下游事实源。
- `prd-writing.profile.json` 只保留程序实际消费的 `profile_name`、`description` 和 `constraints.forbidden_expressions`；禁用表达数组是 `prd-style-lint.py` 的唯一来源。

## 五、Skill 与脚本读取策略

| Skill | 必读 | 条件读取 |
| --- | --- | --- |
| `spm-align` | Align reference、Align template | 无 |
| `spm-design` | Design template、analysis protocol、methodology、writing、state、flow、quality rubric 的生成自审部分 | 旧 metadata 存在时读取 legacy contract |
| `spm-design-review` | 公共 Review contract、Design 专项 checklist、quality rubric 独立 Review 部分 | 具体检查需要时读取 writing/state/flow；旧 metadata 存在时读取 legacy contract |
| `spm-prd` | PRD rules、profile、PRD template、glossary、versioning、scene checklist | 高复杂动作、规则无法直接决定组织、自检命中失败模式或用户要求时读取 examples |
| `spm-prd-review` | 公共 Review contract、PRD 专项 checklist、PRD rules、profile | 具体取证需要时读取 examples/glossary/versioning/scene checklist |
| `spm-prototype` | Prototype writing、Prototype template | 多页面或 shell 问题读取 prototype-shell；有反馈时读取 feedback template |
| `spm-prototype-review` | 公共 Review contract、Prototype 专项 checklist、Prototype writing | 多页面 shell、路由或空白页问题读取 prototype-shell |
| `spm-fix` | Fix propagation contract | 按传播对象读取对应上游/下游资源 |
| `spm-start` | Start action matrix、Start report template | 无 |

迁移阶段先让 PRD rules 与 examples 同时可读，行为对照通过后再启用 examples 条件加载；最终默认上下文不包含无关 examples 或 shell。

`stage-context.py` 同步维护新的 PRD 最小集合、Prototype 最小集合和三个 Review 的公共/专项集合，并删除旧 `prd-writing.md` 路径。所有新路径可解析且无旧消费者后，删除旧文件；不保留兼容别名。

## 六、验证与边界

新增 `scripts/python/test-resource-integrity.py`，检查资源路径、相对链接、长文档目录、stage-context 最小集合、profile 字段、旧路径消费者、三个 Review Skill 的专项 checklist 和条件资源边界。

执行以下验证：

```text
python scripts/python/test-resource-integrity.py
python scripts/python/test-shitpm-regression.py
python scripts/python/test-anti-hallucination.py prepare
python scripts/python/test-anti-hallucination.py verify
python scripts/python/test-anti-hallucination.py clean
git diff --check
```

回归场景以脚本实际 `SCENARIOS` 为准；当前为 32 个，不使用过期的 28 项口径。行为对照覆盖简单/完整 Design、PRD、无 PRD Prototype、多页面 shell、三个 Review 以及 Prototype 语义边界。

本轮不修改批准产品基线、PRD 页面组织、Prototype 技术架构和 `spm-prototype-mark` 业务内容；不执行 `git commit` 或 `git push`。
