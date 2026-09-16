# Design 业务闭环质量改进迭代 · 执行报告

> 执行日期：2026-09-16
> 依据计划：`D:/work/ShitPM/docs/plans/2026-09-15-design-review-exhaustiveness-iteration-plan.md`
> baseline commit：`5035a42a9a7b06fcb61aeb34156169f1e42b9f65`（main）
> 关联台账：`docs/reports/2026-09-16-design-review-p1-ledger.md`
> held-out 证据：`docs/reports/2026-09-16-heldout-review-audit-system.md`

---

## 1. 实际修改的文件

### 规范层

| 文件 | 改动 |
|---|---|
| `references/design-business-closure.md` | **新增**（127 行，含 `## 目录`）。业务闭环单元、九类关系维度、对象细分类型、属性集差集、适用/排除/risk/decision、fast/full/fix 三种责任与成本边界 |
| `references/design-analysis-protocol.md` | §5 跨层回读表前加一句职责划分与指针（维度级 vs 实例级），避免两份定义 |
| `references/design-writing.md` | `design-writing-self-check` 章节：新增第 6 条「核心闭环回读」（六类高影响关系 + 细分类型 + 属性集差集），原 6–11 顺延为 7–12 |
| `references/design-quality-rubric.md` | `design-verification-self-review` §2.1：新增一条核心闭环回读，明确「写作动作内的回读，不是独立检查任务，不产生单独报告或回执」 |
| `skills/spm-design/SKILL.md` | §7 写作动作内自检加入核心闭环回读指针（保留 `context-pack.py` 与 manifest 装载指针） |
| `skills/spm-design-review/SKILL.md` | 执行流程由 6 步改 9 步：步骤 1 去掉「读最近 Review」；新增步骤 4 划分单元、步骤 5 逐单元（先维度差集再逐实例结论）、步骤 6 跨单元合并、步骤 7 冻结后读历史；步骤 8 要求最小覆盖摘要与单报告 |
| `contracts/design-review-checklist.md` | 新增检查项 31/32/33（单元切分、实例闭合、维度差集）；新增「审查覆盖要求」段；输出要求加历史只用于回归、最小覆盖摘要、单报告 |
| `skills/spm-fix/SKILL.md` | 执行流程新增步骤 5（影响面枚举：约束化 → 类别差集 → 三维影响表 → 整页/整列检查 → 回读），原 5–8 顺延；完成输出加「宣称与实际对照」 |
| `contracts/fix-propagation-rules.md` | 第四节新增步骤 0（影响面枚举，位于任何写操作之前）；第五节新增「宣称与实际对照」 |
| `contracts/context-loading.manifest.json` | 新增 section `design-business-closure`（marker），加入 `design-core` pack → analysis/challenge/writing 三个 pass 均装载 |

### 实现层

| 文件 | 改动 |
|---|---|
| `scripts/python/design-index.py` | ①`_normalize_label` 兼容多级编号（`4.2 页面：…`）；②新增 `_page_compare_key`（只剥尾括注、保留编号前缀），只作用于三处页面清单↔详情比较点，不改 `page["name"]`；③新增结构式 `page_extraction_empty`（`blocks+fields+operations>0 且 pages==0`），排在 `unsupported_format` 之后；④`load_verified_index` 两条路径（内存编译 / 落盘校验）在 unsupported_format 之后返回显式错误 |
| `scripts/python/prd-consistency-check.py` | `_compare_indexed_structure` 空 expected 分支由 `enabled=True` 改为 `False`，并加注释说明「已启用、零预期」会伪装成对账通过 |
| `scripts/python/test-design-index.py` | 新增 4 组夹具（多级编号、带括注页面、有区块无页面、旧格式扁平）；新增 6 个测试：多级编号提取、比对键剥括注（含实体名不被改）、结构式关键空集、旧格式仍降级、load_verified_index 拒绝关键空集、两个消费者拒绝关键空集 |
| `scripts/python/test-prd-consistency-semantics.py` | 新增 `test_empty_expected_entities_is_not_reported_enabled` |
| `scripts/python/test-phase7-scenarios.py` | F2 改用「仅作目标态、无自有行」的确定夹具并真实断言 `dead == ["待审核"]`；新增 F2 反例（有「—」自有行判终态不误报）；F3/F4 删除假 PASS（属 LLM 判断，无确定性对象）；F5–F7 改为文档措辞断言并在 evidence 显式标注「不证明模型行为」 |

---

## 2. T-0 冻结基线

| 项 | 值 | 与计划旧快照的差异 |
|---|---|---|
| baseline commit | `5035a42` | — |
| P0/P1/P2 | 2 / 50 / 104（合计 156） | 一致；R13 另有待决×3 |
| 5 文件总字节 | **161626** | 计划旧值 161698，**漂移 -72** |
| 4 份人读字节 | 159767 | 一致 |
| 模块设计单文件 | 94689 | 一致 |
| Index 冻结值 | pages=0, blocks=14, fields=89, operations=7, errors=50 | 一致 |

错误码构成（50）：`block_without_page`×14、`missing_attribute`×14、`combined_field_name`×9、`duplicate_entity`×5、`block_without_items`×5、`semantic_conflict`×3。

**逐问题台账**（52 条 = P0×2 + P1×50）已建立，见 `docs/reports/2026-09-16-design-review-p1-ledger.md`。

- **可复现 0 条、不可复现 52 条（其中 1 条存疑 D13-02）、cannot_judge 0 条。**
- 原因：设备租赁只有 1 个 commit，当前 Design 是 fix-13（18:28）之后的状态，即**已修完 R13 全部问题的状态**。R13 报告 17:28 落盘 → Design 18:28 被 fix-13 更新，历史标的因此全部消失。这不是方法失效，是标的消失。
- 抽验 3 条（D13-03 / D2-01 / ISSUE-01）台账引用的行号（MOD L148/226/305/395、L210/288、SYS L173/188）实测属实。
- 主类别分布（替代此前无法复核的 17/14/14/7）：权限与可见性 12、字段定义与落点 9、状态与迁移 7、命名与口径 7、规则与来源 6、动作与前置条件 4、异常与恢复 3、技术污染 2、跨文件一致 2。

---

## 3. 确定性实现结果

### T-1

| | 修复前 | 修复后 |
|---|---|---|
| pages | 0 | **4** |
| errors | 50 | **27** |
| `block_without_page` | 14 | 0 |
| `duplicate_entity` | 5 | 0 |
| `semantic_conflict` | 3 | 0 |
| 页面配对错误 | 4（清单↔详情双向各报） | 0 |
| `missing_attribute` | 14 | 14 |
| `combined_field_name` | 9 | 9 |
| `block_without_items` | 5 | 4 |

消失的 23 条 = `block_without_page`14 + `duplicate_entity`5 + `semantic_conflict`3 + `block_without_items`1，全部是页面提取失败及其连带错误。`block_without_items` 减 1 是修复后区块正确挂载到页面下的连带结果（计划 T-1 动作 10 写「不增不减」，实测该条减 1，此处如实记录偏差原因，未为迎合判据修改代码）。页面实体名保留括注，未发生同名误合并（P-SET-01~04 在清单与标题各出现一次，仅 2 个标题带括注）。

### T-7

- F2 新夹具实测：`待审核 is_terminal=False, transitions=0` → `dead == ["待审核"]`。
- 反例：有「—」自有行 → `is_terminal=True`，不进入 dead。
- **红绿验证**：故意破坏 `stage-prep.py` 的「目标态进入状态集合」逻辑 → F2 断言失败（变红）；还原 → 绿。已还原，`stage-prep.py` 无残留修改。

### 测试

| 入口 | 结果 |
|---|---|
| `C:/Python314/python.exe -m pytest -q` | **84 passed**（基线 77 + 新增 7），零回归 |
| `scripts/python/test-*.py` 共 14 个直跑 | 全部 OK/PASS |

---

## 4. T-2 候选枚举实验

**分母口径**：可复现 P1 子集为 0（< 15 条），按计划 T-2 改用「从 Review 引用的正文重建最小片段夹具」作分母。

**实验设置**：12 个夹具（10 个含缺陷 + 2 个对照），缺陷形态取自台账各类别（D13-03 / R6-01 / D11-02 / D7-08 / R4-02 / D9-04 / D8-02 / D9-05 / D12-01 / D13-01）。提取器只输出 candidate 与 cannot_extract，不输出 pass/red/risk/decision。

| 指标 | 结果 | 门槛 |
|---|---|---|
| 覆盖率 | **8/10 = 80%** | ≥60% ✅ |
| 误报（对照组） | **0 条** | < 真实命中×2 ✅ |

未覆盖 2 项：**F09 跨文件一致**、**F10 对象细分类型** —— 这两类恰恰是 R12/R13 的高命中类别，确定性提取覆盖不了。

**必须记录的局限**：夹具与提取器同源设计（先写提取器、再造夹具，调试中又按夹具修正了提取器），覆盖率存在明显的乐观偏差；且分母是重建夹具而非真实历史问题（真实可复现子集为 0）。

**结论：字面达标，但不建议保留生产脚本。** 理由：①同源偏差使 80% 不可作决策依据；②未覆盖的两类正是最高命中的维度；③按仓库精简原则，新增脚本须回答「删除它最终产物会错在哪」——本例答不出（规范层已把这两类写入关系维度清单，由人工/LLM 判断）。因此**未创建 `design-relationship-candidates.py`**，实验代码未入库。此项列为待用户决策（见 §7）。

---

## 5. 产物层

### T-8 Design A/B：**未执行**

- 输入材料存在（`output/align`、`.workflow/runtime/align`、两份需求解读文档），子代理通道存在。
- 未执行原因：①需 6 次完整 Design 生成（目标产物 4 文件约 160KB），单次成本与耗时远超本轮资源边界；②A 组需串行回退规范层改动，而工作区常驻用户未提交的 `references/prd-writing-rules.md`，回退存在危及用户工作的风险；③计划 §8 明确允许「无法获得同一模型、同一输入的 A/B → 标记产物层未完成，不得用手写样本代替」。
- **不伪造 harness**：未生成任何替代性 A/B 数据。

### T-8 Fix 验证：**未执行**（依赖同上，3 个样本已选：D13-03、D11-01、D12-01）

### T-9 held-out：**单侧执行**

审计系统（`D:/work/交投软件中心/审计系统`，703KB 完整 Design 集，未参与本方法形成）作为 held-out，由独立子代理（lite 模型）按新规范执行一次局部 Review，范围「审计实施 → 审计反馈 → 审计整改」端到端闭环。

- 结果：划分 **6 个单元**、**236 个关系实例**，pass 202 / red 7 / risk 21 / excluded 6（均带正文依据）/ cannot_extract 1 / decision 0；P0×0、P1×17、P2×10，结论「阻塞」。
- 证明：新规范能被独立执行者理解并按「划分单元 → 维度差集 → 逐实例结论 → 跨单元合并 → 覆盖摘要」走通。
- **未证明**：没有 A 组（旧方法）裁定基线对照，因此不能得出「新方法优于旧方法」。计划 T-9 要求「先由独立审查形成裁定基线，再执行新方法对照」，本轮只完成新方法一侧。

---

## 6. 临时文件清理

已清理：`t0/`、`t1/`（隔离副本与索引输出）、`t0-ledger-{A,B,C}.md`（合并后入库）、`heldout-review.md`（已入库为报告）。
保留：`C:/Users/guduj/AppData/Local/Temp/t2/`（T-2 实验代码与夹具，未入库；如需复核可查看，确认后可删）。

---

## 7. 待用户决策

| # | 事项 | 现状 | 建议 |
|---|---|---|---|
| U-1 | T-2 候选脚本是否入库 | 达标但未入库 | 建议不入库（同源偏差 + 高命中维度未覆盖）；若采纳，§4 局限即为最终结论 |
| U-2 | T-8 Design A/B 是否执行 | 未执行 | 需用户确认可接受的资源开销与 `prd-writing-rules.md` 回退风险 |
| U-3 | T-9 裁定基线是否补齐 | 只有新方法一侧 | 需再派一次旧方法 Review 对同一范围，才能得出对照结论 |
| U-4 | 设备租赁历史问题是否用新方法复验 | 台账显示 52 条全部不可复现 | 当前 Design 已是修完 R13 的状态；若要验证新方法，需用 held-out 项目而非本项目 |

---

## 8. 总结结论

| 层 | 结论 |
|---|---|
| **规范层** | **通过**。共享规则单一权威定义，三个 Skill 通过指针引用；写作期实际装载已验证（`context-pack.py --stage design --pass writing --mode full` 输出含 `design-business-closure`）；资源完整性与装载测试通过 |
| **实现层** | **通过**。pages 0→4、errors 50→27，结构式关键空集明确失败且两个消费者拒绝，旧格式仍降级；F2 真实红绿；84 passed / 14 个直跑脚本全绿，零回归 |
| **产物层** | **部分完成**。held-out 新方法单侧走通，但无 A/B、无裁定基线对照、Fix 隔离验证未执行 |

**本轮总状态：部分完成**（产物层验证缺失，按计划不得写已完成）。

### 不得省略的负面结论

- **Design 生成效果未证明**：无同模型同输入的 A/B，新方法在生成侧的收益是未验证的假设。
- **Review 通用性未证明**：held-out 只做了新方法一侧，没有旧方法裁定基线，不能说新方法更好。
- **候选脚本未进入主流程**：未创建 `design-relationship-candidates.py`，T-3 至 T-6 使用 instruction-only 方案。
- **不承诺未来所有未知业务关系能被一次穷尽**：本轮改进的是「可枚举、可闭合、可说明覆盖」，不是「绝对穷尽」。
- 已修 History：设备租赁 52 条历史问题在当前 Design 上全部不可复现，这个台账**不能**用来证明新方法比旧方法更会找问题。
