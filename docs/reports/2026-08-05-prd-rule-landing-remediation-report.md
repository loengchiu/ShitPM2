# PRD 写作规则落点补救验收报告

> 日期：2026-08-05  
> 依据：`docs/plans/2026-08-05-prd-rule-landing-remediation-plan.md`  
> 关系：作为 `2026-08-05-prd-writing-consolidation.md` 的补救方案执行结果；不改写历史方案和验收报告。  
> 范围：只收敛 PRD 写作规则的落点归属；冻结范围（lint、推断值、Design 操作表）只确认不冲突，不扩大改动。

---

## 一、补救结论

**补救完成。** 原方案已验证的行为改动全部保留，规则组织方式按目标架构重建：

1. `references/prd-writing-rules.md` 成为 PRD 动作语义的唯一完整规则源；
2. 动作规则拆分为硬约束 / 复杂度最低覆盖 / 写作建议三层，四问降为自检视角；
3. `spm-prd` Skill、模板、示例、场景清单、Review 清单不再复制完整规则正文，只承担流程入口、局部提示、写法示范和证据要求；
4. 简单动作不再被四问硬性绑架；
5. 冻结范围内的既有成果（lint、Design 推断值、Design 操作表十列）未被回滚，与新规则不冲突；
6. 三类动作探针通过，8 项既有测试全部通过。

## 二、保留的既有成果

| 成果 | 状态 | 说明 |
|---|---|---|
| Design 操作表交互维度（入口/字段级输入/二次确认/后续去向） | 保留 | 未触碰（`design-index.py`、十列相关文件冻结） |
| PRD 页面区块和展示行为列表式写法 | 保留 | 规则 §3.2、模板示例、场景清单、Review T 系列不变 |
| 行首标签式正文确定性 lint 约束 | 保留 | `prd-style-lint.py` + `prd-writing.profile.json` 冻结，未改动 |
| Design 推断值登记与一次性 confirmation 汇总 | 保留 | `design-writing.md`、`spm-design/SKILL.md` 冻结，未触碰 |
| 分片装载、事实边界、非页面字段回读、跨层检查 | 保留 | Skill 阶段 A/B/C/D 流程、规则 §9/§10/§11、清单未变 |

## 三、废止或改写的旧规则

| 旧规则 | 处置 |
|---|---|
| 同一套完整规则复制到 rules / SKILL / 模板 / 示例 / Review 清单 | 废止：唯一语义源收敛到 `prd-writing-rules.md`，其余位置只引用或转成检查问题 |
| "动作内部组织公式"（业务判断与结果 → 字段/状态 → 展示 → 异常）作为固定格式 | 改写：降为可选写作提示，不构成固定顺序 |
| "每个动作都完整回答四问"作为统一硬门槛 | 改写：降为中高复杂动作的自检视角，简单动作不虚构表单/确认/异常 |
| "六处同步"当作规则架构正确的证明 | 废止：不再以同步数量证明正确性 |
| 上轮把 PRD 写作整合、Design 推断值、lint 增强混成一份验收范围 | 改写：本报告拆分报告规则收敛、Design 交互、推断值、lint、测试五类结果 |

## 四、规则唯一源与各消费者职责

| 内容类型 | 唯一事实源 | 消费者职责 | 落地情况 |
|---|---|---|---|
| PRD 内容硬规则、事实边界、动作分级 | `references/prd-writing-rules.md` | 其他位置只引用或转成检查问题 | ✅ 见 §五 |
| PRD 生成流程、停止条件、装载顺序 | `skills/spm-prd/SKILL.md` | 不复制规则全文 | ✅ 模块完成条件 #4、生成内自检 #6 改为引用 `prd-writing-rules.md` §2.1 |
| 输出章节、标题和局部填充提示 | `templates/prd.md` | 只保留模板局部提示和格式示例 | ✅ 动作注释改为"按复杂度承接 §2.1"，删除四问全文 |
| 正反例 | `references/prd-writing-examples.md` | 只展示写法，不承担规范解释 | ✅ 删除规则定义段落，每节标注"规则见 §x.x"，新增区块自然句示例 |
| 模块写作自检 | `references/prd-scene-checklist.md` | 写检查问题，指向规则章节 | ✅ 动作闭环项改为"是否满足 §2.1 分层 + 证据" |
| Review 判定 | `contracts/prd-review-checklist.md` | 写证据要求和问题，不重新定义规则 | ✅ 检查项 #11 改为"违反 §2.1 分层"证据式判定 |
| 可确定的标签/格式检查 | `contracts/prd-writing.profile.json` + `prd-style-lint.py` | 只检查稳定文本模式 | ✅ 冻结未动 |
| Design 推断值 | `references/design-writing.md` + `spm-design/SKILL.md` | PRD 只承接已确认 Design | ✅ 冻结未动 |
| 上下文装载 | `contracts/context-loading.manifest.json` | 只负责路由 | ✅ 见 §六 |

## 五、三类动作探针结果

探针：`scripts/python/probe-prd-action-tier.py`（合成样本 + lint 语义判定）。

| 动作级别 | 通过条件 | 结果 |
|---|---|---|
| 简单动作（查询/查看/返回） | 不被要求虚构表单、确认或异常分支；仍能读出触发条件和业务结果 | ✅ PASS |
| 普通状态变更（提交） | 能读出角色、允许状态、输入、处理、成功结果和失败处理；无固定四段标题或标签式正文 | ✅ PASS |
| 高复杂动作（审批，多角色/多出口/外部协作） | 入口、字段/确认、分支、状态、副作用和恢复方式可定位；Design 未定义的高影响内容进入待确认 | ✅ PASS |
| 反例（模板化流水账） | 确定性底线未放松：仍被 lint 拦截（STYLE001/STYLE002 error） | ✅ PASS |

## 六、页面格式与事实边界回归

- **页面表达**：页面区块和展示行为保持列表式写法，长标题前缀（"页面区块与业务目的：""页面展示行为和状态驱动展示："）无残留（仅规则/清单/模板中作为"禁止项"被引用，属禁止性声明而非示例标题）。
- **事实边界**：§事实边界、§8.1 自动动作/删除传播/枚举上限、§9/§9.1 Design 冲突、§10 非页面落点字段回读、§11 变更失效、§12 引用可定位均未改动。
- **上下文装载回归**：`context-pack.py --pass writing` 编译输出 8 个章节（含 `prd-writing-action` 新分层内容），`--pass module` 输出 5 个章节，均引用唯一源 `references/prd-writing-rules.md`；marker 标记完整，装载非空。

## 七、自动化测试结果

| 测试 | 结果 |
|---|---|
| test-prd-simplification | ✅ PASS |
| test-prd-style-lint | ✅ PASS |
| test-prd-consistency-semantics | ✅ PASS |
| test-design-simplification | ✅ PASS |
| test-design-index | ✅ PASS |
| test-context-loading | ✅ PASS |
| test-shitpm-regression | ✅ PASS |
| test-resource-integrity | ✅ PASS |

补充：`prd-writing-examples.md` 的 lint 报 STYLE009（缺名词说明章节）/STYLE002（流水账警告）为 **HEAD 版本即存在**的固有误报（示例合集文档天然不含完整 PRD 的"总体说明"章节），经 `git show HEAD` 对比确认非本次改动引入，未处理。

## 八、未解决问题

1. **examples 文件固有 lint 误报**：STYLE009/STYLE002 对"示例合集"类文档天然误报。属 lint 适用范围问题（lint 只面向成品 `prd.md`），不在本次补救范围；如需消除可在后续把 lint 入口限定为实际 PRD 路径。
2. **存量项目格式问题**：历史 PRD 产物（test-fixture 等）未做格式迁移，本次未触碰（方案 §5.3 明确不做）。
3. **四问在公共 Review 契约的落点**：`contracts/review-checklist.md`（公共审查契约）未复制动作规则，无需处理；如后续公共契约需要引用动作分层，应从 `prd-writing-rules.md` 引用而非复制。

## 九、Git 状态

- 本次改动文件：
  - `references/prd-writing-rules.md`（动作规则三层 + 四问降级）
  - `skills/spm-prd/SKILL.md`（模块完成条件 #4、生成内自检 #6 改为引用）
  - `templates/prd.md`（动作注释改为承接 §2.1）
  - `references/prd-writing-examples.md`（删除规则定义段、每节指向规则、新增自然句区块示例）
  - `references/prd-scene-checklist.md`（动作闭环项改为规则分层 + 证据）
  - `contracts/prd-review-checklist.md`（检查项 #11 改为违反分层证据式判定）
  - 新增：`scripts/python/probe-prd-action-tier.py`（行为探针）
- 冻结范围未改动：`prd-writing.profile.json`、`prd-style-lint.py`、`test-prd-style-lint.py`、`design-index.py`、Design 推断值相关文件、Design 操作表十列相关文件。
- 未修改正式项目 `output/design/design.md` / `output/prd/prd.md`；未新增规则总表、覆盖率 JSON、检查器、回执或编排阶段。
- **未执行 `git commit` / `git push`**（用户规则）。
