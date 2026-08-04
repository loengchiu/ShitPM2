# 生成 PRD 时分片读取 Design：执行与验收报告

> 日期：2026-08-05
> 执行依据：`docs/plans/2026-08-05-prd-design-fragment-reading-plan-and-acceptance.md`
> 执行方式：按计划第 8 节报告格式输出

## 一、结论

**通过**。`context-pack.py --module` 分片提取确定性可用，SKILL/rules/scene/Review 四件套指令落地，无"一次性全读 design.md"的合法路径，副本回归字段定义/页面展开度/重复文案三项全部改善，未新增检查器/门禁/回执，未修改正式项目，未执行 commit/push，12/12 测试全绿。

## 二、实际修改文件

| 文件 | 修改目的 |
|---|---|
| `scripts/python/context-pack.py` | 新增 `--module <模块名>` / `--pages` / `--fragment-threshold`：按标题锚点从 `output/design/design.md` 确定性提取模块片段（闭环章节 + 相关页面 + 共用业务对象/权限/页面清单/待确认），按既有 pack 格式输出为独立 `design-fragment` pack；片段行数超过全文 1/3（仅大 Design ≥1000 行生效）时报错提示拆分模块；匹配不到时列出标题清单报错不静默返回空；`verify_run` 支持项目级 source（fragment 从项目根校验，避免 bundle 内同名残留文件误判陈旧） |
| `skills/spm-prd/SKILL.md` | 阶段 A 补"大 Design 先读 design-index 索引、禁止全文粘贴索引 JSON、compile 非零退出 ≠ 不可用"；阶段 C 命令补 `--module <模块名>`，补"禁止一次性全读 design.md（sed 1,$p 或等效）、片段不含无关模块内容、超阈值先拆模块、匹配不到按报错清单修正" |
| `references/prd-writing-rules.md` | §0 全量分片写作补第 7 条"Design 按模块分片读取"（阶段 A 读索引 / 阶段 C 用 `--module` / 禁止全读） |
| `references/prd-scene-checklist.md` | 模块结束检查补"当前模块 Design 片段已通过 `--module` 装载，未一次性全读 design.md，片段不含无关模块内容" |
| `contracts/prd-review-checklist.md` | 新增检查项 8.1"Design 全读痕迹（上下文爆栈症状）"：字段定义全缺 / 页面两行式 / 机械重复文案 / 待确认异常稀少，命中多项时提示按分片流程重新生成 |
| `scripts/python/test-context-loading.py` | 新增 `check_design_fragment`：--module 提取非空/含目标闭环/不含无关闭环与页面/行数远小于全文/页面名兜底/匹配失败列标题清单/大 Design 超阈值报错/CLI 组合输出规则+清单+片段/写入后 verify 不误报陈旧 |
| `scripts/python/test-prd-simplification.py` | SKILL 补"design-index compile / 禁止一次性全读 / --module / 片段不含无关内容 / sed 1,$p 示例"断言；rules 补"Design 按模块分片读取"断言；scenes 补 `--module` 装载自检断言；Review 补"Design 全读痕迹 / 上下文爆栈"断言 |

计划 §4.2 的"按实际影响同步"项：manifest 无需补配置（fragment 不经过 manifest 装载，直接作为独立 pack 追加）；design-index.py 无需新增 `--nav`（现有 compile 输出的 pages/states/attributes 已足够导航，且精简视图实测 4.9k token 可读）；USAGE.md 无旧流程描述无需同步。

## 三、功能验收

在审计系统副本（`D:/ShitPM-tmp/audit_copy`，design.md 4565 行）上实测：

1. **`--module 底稿作业` 提取**：非空 ✓；含目标闭环（闭环三：底稿作业全生命周期）✓；不含无关闭环（闭环六/八）✓；相关页面精确命中 4 个（底稿列表/编辑/详情/意见反馈）✓；无关页面（整改台账/档案借阅/知识条目）只出现在共用部分的页面清单（全局导航）中，闭环与页面章节干净 ✓
2. **片段行数远小于全文**：491 行 / 4565 行 = **10.7%**（阈值 33%），大 Design 场景显著可控 ✓
3. **匹配不到时行为**：`不存在的模块xyz` 报错并列出 design.md 全部闭环/页面标题清单，不静默返回空 ✓
4. **大 design.md 场景**：模拟 2805 行大模块超阈值报错并提示"按子闭环或页面拆分模块"；小 design（14 行）不误伤（≤1000 行不启用比例约束，与 SKILL 阶段 A 阈值一致）✓
5. **与 `--pass module --card scenes` 组合**：输出 5 个 pack（prd-core / prd-writing-structure / prd-writing-action / prd-cards / design-fragment），含规则 + 场景清单 + 片段三部分，`run.json` 记录 `module` 字段，`verify-run` 判定 valid（无陈旧）✓

## 四、上下文预算

| 装载项 | 行数 | token |
|---|---|---|
| 基线（module pass + scenes 卡，含 rules/template/profile） | 468 | 7,251 |
| 底稿作业模块片段（增量） | 491 | ~13,029 |
| 阶段 C 单模块合计（基线 + 片段） | 959 | 20,280 |
| SKILL.md 本身 | 284 | 4,559 |
| 阶段 C 完整上下文（SKILL + 模块装载） | — | **24,839** |
| design-index 索引全文（61 页 + 729 字段） | — | 177,926（不可读） |
| 索引精简导航视图（页面名 + purpose/roles/states/data_scope/entry_condition） | — | **4,910** |
| 阶段 A 完整上下文（SKILL + 导航视图） | — | **9,469** |
| 旧方案（一次性全读 design.md 325KB + SKILL + 基线） | — | ~130,000+ |

**8k/16k/32k 可装载性结论**（未含宿主系统 prompt，只计 ShitPM 上下文）：

- **8k**：阶段 A 9.5k、阶段 C 24.8k 均超限，8k 模型不可行（旧方案同样不可行）；
- **16k**：阶段 A 9.5k ✓；阶段 C 24.8k 超限（超约 8.8k），需进一步拆模块粒度或压基线；
- **32k**：阶段 A ✓、阶段 C 24.8k ✓，可稳定完成单模块写作，剩余预算足以支撑写作回读。

对比旧方案 13 万+ token，分片后降至 2.5 万，降一个数量级。审计系统这种 4565 行大 Design，分片流程下 32k 模型可跑通，16k 需配合更细的模块拆分。

## 五、真实项目回归（副本）

副本：`D:/ShitPM-tmp/audit_copy`（design.md 由正式项目复制，禁止改正式项目；正式项目仅只读旧 PRD 用于对比）。

- **分片执行痕迹**：`context-pack.py --module 底稿作业` 装载，产物 `.workflow/runtime/context/prd/packs/005-design-fragment.md`（含 source-hash），`run.json` 记录 `module: 底稿作业`；本模块写作全程只读该 491 行片段，未读 design.md 全文。
- **字段定义章节**：新样本模块含对象级字段定义（4.x.5，21 个字段逐行定义含义/来源/必填/规则）；旧 PRD 全文字段定义 **0 命中**。
- **页面展开度**：新样本 4 个页面均有区块、字段、页面展示行为、状态驱动展示、完整动作因果链（21 个动作，交互四问齐备）；旧 PRD 页面为"职责 + 业务阶段"两行式。
- **重复文案**：新样本"刷新页面重试" **0 次**；旧 PRD **122 次**；新样本待确认按 Design 空清单保守表达，不静默拍板。
- 回归样本落盘：`D:/ShitPM-tmp/audit_copy/output/prd/module-draft-底稿作业.md`（标注为分片流程验证样本，不冒充正式 PRD；正式 PRD 重生成需用户另行决定）。

## 六、自动化结果

12/12 全绿（含本轮新增断言）：

| 测试 | 结果 |
|---|---|
| test-context-loading（含新增 --module 分片用例） | PASS |
| test-prd-simplification（含新增分片读取断言） | PASS |
| test-prd-style-lint | PASS |
| test-prd-consistency-semantics | PASS |
| test-design-simplification | PASS |
| test-design-index | 16/16 OK |
| test-shitpm-regression | 3 用例 PASS |
| test-resource-integrity | PASS |
| test-context-runtime | PASS |
| test-anti-hallucination | PASS |
| test-design-orchestrator | 8 用例 PASS |
| test-design-orchestration-replay | 6 用例 PASS |

本轮无失败项；无关既有失败：无。

## 七、未解决问题与待确认事项

1. **页面与闭环的关联靠标题词（最长公共子串 ≥2 字）+ 正文子串 + `--pages` 兜底**，属确定性近似：闭环正文不出现页面名（真实项目常见，如"录入底稿"而非"底稿列表"）时依赖标题词关联；极端情况下（闭环与页面无共享词）需模型传 `--pages` 显式补充。不做语义检索是计划 §5.1/§10 的明确边界。
2. **`--pages` 显式补充页面的可用性**：SKILL 已写明"匹配不到闭环时可取页面名或加 `--pages`"，但 `--pages` 与 `--module` 组合的更多场景（多页面精确指定）未在真实项目验证，建议真实项目重生成时按需使用并回读。
3. **16k 模型下的模块粒度**：预算显示阶段 C 单模块 24.8k 超 16k；大 Design 项目若用 16k 模型，需先按子闭环拆更细（如"底稿录入"与"征求意见与复核"拆开）。计划停止条件 3（片段仍超小上下文预算）未触发（32k 下可控），但 16k 下可能触发。
4. **design-index 索引全文 17.8 万 token**：已通过 SKILL 指令"只读精简视图、禁止全文粘贴"约束，无脚本门禁（符合计划 §10 不新增检查器）；依赖模型遵守指令。
5. 正式项目（审计系统）PRD 重生成**未执行**——计划 §4.3 禁止修改正式项目，重生成需用户另行决定。

## 八、Git 状态

- 本轮实际改动 7 个文件：`scripts/python/context-pack.py`、`skills/spm-prd/SKILL.md`、`references/prd-writing-rules.md`、`references/prd-scene-checklist.md`、`contracts/prd-review-checklist.md`、`scripts/python/test-context-loading.py`、`scripts/python/test-prd-simplification.py`（另有本轮新增报告与计划文件）。
- 工作区存在大量历史遗留未提交改动（design-index.py、spm-design、templates 等，来自前几轮），非本轮产生；本轮未执行 commit/push，计划 §4.3 禁止项均未触碰。
- 副本回归产物位于 `D:/ShitPM-tmp/audit_copy`（临时目录，不入库）。
