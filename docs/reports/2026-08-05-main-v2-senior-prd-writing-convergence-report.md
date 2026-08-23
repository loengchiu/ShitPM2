# main 与 V2 详细需求说明融合收敛验收报告

> 日期：2026-08-05
> 依据：`docs/plans/2026-08-05-main-v2-senior-prd-writing-convergence-plan.md`
> 前置：`2026-08-05-prd-rule-landing-remediation-plan.md`（已完成）、`2026-08-05-main-prd-writing-merge-remediation-plan.md`（已完成）
> 决策材料：`docs/plans/2026-08-05-main-v2-fusion-decision-table.md`

## 一、结论

**融合完成。** main 的资深产品经理写作长处已按决策表吸收进 `references/prd-writing-rules.md`（唯一规则源）和 `references/prd-writing-examples.md`（示例）；V2 的事实边界、结构和交付约束全部保留，没有"main 全量覆盖 V2"或"V2 全量压过 main"的简单迁移。8/8 回归测试全绿，融合规则已进入 context-pack writing 编译产物，真实样本验收通过。

## 二、main 与 V2 的融合决策

完整决策表见 `docs/plans/2026-08-05-main-v2-fusion-decision-table.md`（40 项决策 + 8 项补示例 + 6 项明确不迁移）。核心决策摘要：

| 主题 | 决策 | 落点 |
|---|---|---|
| 动作正文组织 | 合并（C） | V2 三层骨架 + main 的"按操作顺序写主链路、关键分支单列、状态变化落到结果、下一步衔接角色写在结果处" |
| UI 文案 | 合并（C） | 已确认文案用双引号嵌入正文，不单独列文案表 |
| 动态数据来源 | 合并（C） | 说明数据来自系统计算/接口返回/关联带出/用户输入 |
| 长文本处理 | 合并（C） | 写清截断、换行、滚动、悬停查看全文 |
| 默认角色可见性 | 合并（C） | 模块 `4.1.3` 统一说明，特殊角色限制就近写 |
| 三种表达形式 | 合并（C） | 自然段/数字编号/`·` 并列按语义选择 |
| 页面标题/动作标记 | 保留 V2（B） | `###### 页面` + `**动作**`，不迁回 main 的加粗页面/`·` 动作 |
| 状态机交付 | 保留 V2（B） | draw.io 源文件 + PNG，不迁 Mermaid |
| 模块组织 | 保留 V2（B） | 业务闭环→业务阶段，不迁回小模块嵌套 |
| 禁用表达式 | V2 更强（D） | V2 profile 覆盖 main 且更全 |
| 场景清单 | V2 更强（D） | 保持 V2 七类场景，补"资深规格回读"问题 |

## 三、关联 references 与装载链复核

| 参考内容 | 复核结果 |
|---|---|
| `references/prd-writing-rules.md` | 融合后唯一规则源；新增 §2 主链路/角色衔接、§2.1 写作建议（文案引号/动态来源/长文本/三种表达/默认角色）、§6.1 信息密度、§6.2 三种表达形式；V2 三层骨架保留 |
| `references/prd-writing-examples.md` | 重做：新增普通表单、文案长文本动态来源、默认角色集中+特殊就近三类对照；反例扩为四类（流水账/原因腔/重复话术/标签式小节）；8 类对照齐备 |
| `references/prd-glossary-format.md` | 保持 V2，术语章节与来源边界未动 |
| `references/prd-versioning.md` | 保持 V2，版本记录规范未动 |
| `references/prd-scene-checklist.md` | 保持七类场景，补"是否写成资深规格"回读问题 |
| `templates/prd.md` | 保留 V2 章节和标记；`4.1.6` 动作注释同步融合写法（主链路/文案引号/长文本/默认角色） |
| `contracts/prd-review-checklist.md` | 新增 11a 资深规格回读检查项（P2） |
| `contracts/prd-writing.profile.json` | 保持现状，未改；确定性禁用表达式完整 |
| `contracts/context-loading.manifest.json` | 复核：writing/module 两 pass 均装载 `references/prd-writing-rules.md`，规则源唯一进入上下文；examples 不装载（手动阅读） |
| `scripts/python/prd-style-lint.py` | 保持现状，未改；融合样本 lint 通过（0 error） |

## 四、详细需求说明写作规则落点

规则只落在两处，不重复扩散：

1. **规则源** `references/prd-writing-rules.md`：
   - §2 动作因果链 + 主链路/角色衔接；
   - §2.1 三层（硬约束/复杂度最低覆盖/写作建议），最低覆盖表补"下一步衔接角色"；
   - §3 结构化自然语言（禁标签式正文）；
   - §5 状态与规则、§6 查询统计、§6.1 信息密度、§6.2 三种表达形式、§7 表单配置、§8 异常恢复；
   - 事实边界（Design 唯一事实源、推断值承接、高影响待确认）保持。
2. **消费者只引用不复制**：
   - `spm-prd/SKILL.md`：模块完成条件 #4a、生成内自检 #6a 补"按融合规则回读"；
   - `templates/prd.md`：动作注释引用规则源并同步融合写法；
   - `prd-scene-checklist.md`、`prd-review-checklist.md`：检查项写"是否满足规则章节 + 应看什么证据"。

无新增规则总表、覆盖率 JSON、回执或新的编排阶段。

## 五、真实模块样本验收

### 样本

- 隔离副本：`test-fixture/output/fusion-acceptance/`（design.md + prd-fusion-sample.md），不修改正式 `output/`；
- 事实源：审计管理系统 Design（1941 行，含第八章页面与字段落点）；
- 覆盖三类模块：简单列表/查询（操作日志）、普通表单状态变更（计划编辑）、多角色多状态外部协作（年度计划审批闭环），共 10 个动作。

### 五问核验

| 问题 | 结论 |
|---|---|
| 是否先讲业务动作而非盘点 UI | 是。动作正文以业务结果开头（"管理员在操作日志页填写筛选条件后点击查询"），区块只作辅助 |
| 是否知道谁做、何时做、做完变成什么 | 是。每个动作写清角色（编制人/审批人/管理员）、允许状态（草稿/已驳回/待审批）、结果状态（待审批/已通过/已驳回） |
| 研发测试能否直接找到字段、按钮、文案、异常、恢复 | 是。筛选条件、必填校验、标红提示、"查询失败，请稍后重试"文案、失败保留均直接可读 |
| 是否有重复、空话、模板化句式 | 否。无"用于承载""支持相关操作"；每个动作失败处理按场景写，未套统一话术 |
| 是否像资深产品经理而非"规则检查通过的 AI 文档" | 是。主链路按操作顺序、分支单列、状态变化落到结果、下一步衔接角色写在结果处（如"驳回后编制人可修改后重新提交"） |

### 事实边界验证

Design 未定义处均保守处理：导出格式和上限、删除恢复、年度计划调整审批失败处理——全部列为待确认，未补造。

### lint 验证

样本通过 `prd-style-lint.py`（0 error；2 warning 均为文档性误报）。lint 还反向验证了融合规则有效性：样本初稿的"见 4.2.6"跨节引用（STYLE005）和"用于承载"（STYLE008）被 lint 拦截，修正后通过。

## 六、保留的 V2 事实边界与既有能力

- 确认版 Design 唯一事实源、高影响未知待确认、推断值承接（Design 登记 + confirmation 拍板）；
- 页面/动作/业务阶段的 V2 组织方式（`###### 页面` + `**动作**` + `##### 阶段`）；
- 状态、权限、数据范围、字段属性、异常恢复、删除传播完整性要求；
- 非页面字段回读、三处交叉比较、已完成模块变更失效；
- draw.io 源文件 + PNG 流程图交付（Mermaid 不迁回）；
- 分片读取和直接写入最终 PRD；
- Design 操作表十列、已有确定性 lint、`prd-writing.profile.json` 禁用表达式。

## 七、自动化回归结果

8/8 测试全绿：

| 测试 | 结果 |
|---|---|
| test-prd-simplification | PASS |
| test-prd-style-lint | PASS |
| test-prd-consistency-semantics | PASS |
| test-design-simplification | PASS |
| test-design-index | PASS |
| test-context-loading | PASS |
| test-shitpm-regression | PASS |
| test-resource-integrity | PASS |

补充验证：`context-pack --pass writing` 编译正常，融合规则（主链路×3、衔接角色×2、双引号×2）已进入 `003-prd-writing-action.md` 编译产物；module pass 由 test-context-loading 覆盖。

## 八、未解决问题

1. **探针删除**：`scripts/python/probe-prd-action-tier.py` 无稳定消费者（仅被自身和上轮报告引用），按仓库准入原则删除；上轮报告 `2026-08-05-prd-rule-landing-remediation-report.md` 中的探针描述成为历史记录，不更新（避免改写历史证据）。
2. **fixture 无 V2 结构大项目 Design**：仓库现有 1941 行审计 Design 是 main 风格（无操作表十列），无法直接用 context-pack `--module` 装载验证模块级装载；已由 test-context-loading 覆盖 module pass 正确性。后续如有 V2 结构真实项目，建议补一个正例样本。
3. **正式项目 output/ 未动**：周报系统 Design（124 行）规模不足以验证复杂场景，融合规则对真实复杂项目的效果需在实际 V2 项目生成时进一步检验。
4. **融合样本留在 test-fixture**：`test-fixture/output/fusion-acceptance/` 作为验收证据保留；其中 `output/design` 空壳子目录（context-pack 验证遗留）无法通过安全删除器移除，不影响任何测试。

## 九、Git 状态

- 本轮改动（7 个文件 + 2 个新增）：
  - 修改：`references/prd-writing-rules.md`、`references/prd-writing-examples.md`、`references/prd-scene-checklist.md`、`contracts/prd-review-checklist.md`、`skills/spm-prd/SKILL.md`、`templates/prd.md`
  - 新增：`docs/plans/2026-08-05-main-v2-fusion-decision-table.md`（决策表）、`test-fixture/output/fusion-acceptance/`（验收样本）
  - 删除：`scripts/python/probe-prd-action-tier.py`
- 未执行 `git commit` / `git push`；工作区还有 R20 以来未提交改动（推断值 + lint 增强）与本轮改动混在一起，提交拆分待用户决定。
