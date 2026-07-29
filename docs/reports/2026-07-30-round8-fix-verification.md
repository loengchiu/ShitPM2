# ShitPM 第八轮审查（第七轮修复验证轮）

> 日期：2026-07-30 00:55
> 触发：用户完成第七轮复审（round7-recheck）全部修复后要求重审
> 基线：`docs/reports/2026-07-29-round7-recheck.md`（1 P0，2 P1，6 P2，4 P3）
> 方法：逐项实测复核，不沿用任何记忆结论

## Verdict：通过（0 P0，0 P1，2 项新 P2，1 项 P3 备注）

第七轮复审的 1 项 P0、2 项 P1、6 项 P2、4 项 P3 **全部真修**，均实测验证。本轮新发现 2 项 P2（都在 legacy 兼容路径，不阻断新格式主线）。

## 一、第七轮问题逐项验证结果

| 编号 | 验证结果 | 实测证据 |
|---|---|---|
| **P0-2** PRD 检查器必然 exit 1 | **已修** | 新格式 design.md + 模板规范 PRD（`**5.1.1 页面名**` + `· 动作` + 7 列表）→ `expected_count: 3, matched_count: 3`，**EXIT 0**。修复方式：`_compare_indexed_structure` 在 `extract_document_entities` 无命中时回退到 PRD 专用提取器（prd_pages/prd_fields/`·` 操作行 + 粗体页面标记定位），flexible 模式放宽 block 匹配。故意造不合模板的 PRD（粗体块写操作）仍正确 exit 1——阻断的是真违规，不再误伤合规产物 |
| **P1-1** orchestrator 孤儿 | **已修** | SKILL.md:82-88 写明 `init/next/accept/answer/status` 五个命令的调用步骤并引用 `design-orchestration-contract.md`。冒烟实测：`init --mode simple` → `next` 正确返回 `ready_actions[]`（material-index 动作卡完整：input_hashes/rule_pack_ref/forbidden_inputs 齐全） |
| **P1-2'** 交接门禁双向架空 | **已修** | ① `context-runtime-check.py:138` 新增 `V2_HANDOFFS` 6 类型（a/b/c-baseline、design-brief、business/cross-layer-conflicts），进 `--require` choices；② `design-orchestrator.py:582-594` `accept_outputs` 按 `_handoff_requirements` 映射自动调用门禁，returncode 非 0 拒绝采纳；③ design-model/design-challenge 保留为旧版兼容，SKILL.md:90 明确其仅用于"读取旧版兼容性交接包时" |
| P2-1 旧格式静默空索引 | **已修** | 旧表格格式 design.md 编译 → `errors[].code: "unsupported_format"` + 明确提示"请由下游兼容解析器处理"；PRD 检查器 :1143 据此走 legacy 路径（`enabled: false`），不再误报索引幻觉 |
| P2-2 contract/schema 无人加载 | **已修** | `design-orchestrator.py:545` 实际加载 `design-orchestration-action.schema.json` 校验动作卡；契约 :41 明文"可执行字段约束统一加载 schema，本契约只描述语义" |
| P2-3 design-writing.md 双"## 六" | **已修** | 章节现为 一~七 + 附录，顺序正确无重复 |
| P2-4 test-fixture/design-index 缺失 | **已修** | 目录已建：duplicate-page/ invalid-hierarchy/ missing-field-attribute/ valid/，test-design-index.py EXIT 0 |
| P2-5 online 测试脚本悬空引用 | **已修** | runbook 和 low-cost-test-plan 头部加"历史作废说明"，正文引用处标注"待实现；不可执行；本轮不运行"且命令已注释 |
| P2-6 新旧方向文档并存无标注 | **已修** | design-orchestration-* 三份（context-governance / runbook / low-cost-test-plan）头部均有"已被 park-quality 系列取代，仅作历史审计材料" |
| P3-1 第6轮报告结论过时 | **已修** | round6 报告头部加"后续状态"标注 |
| P3-2/P3-3 参数重复/恒等冗余 | **已修** | :493 和 :1369 原位置现为注释，冗余代码已清 |
| P3-4 spm-align 未指明生成脚本 | **已修** | spm-align SKILL.md 明确 `source-index.json 由 $BUNDLE/scripts/python/source-index.py 生成或复用` |

测试套件 6 项全绿：test-design-orchestrator / test-design-orchestration-replay / test-design-index / test-context-runtime / test-context-loading / test-shitpm-regression 均 EXIT 0。

## 二、本轮新发现

### P2-A — legacy 路径状态通配词处理不对称（建议优先修）

实测：test-fixture 旧格式 design+prd 对照跑 `prd-consistency-check.py` → **EXIT 1**，`states.missing: ["任意状态"]`。

根因：PRD 侧状态提取 :367 明确排除通配词（`"—", "-", "N/A", "任意状态", "状态"`），design 侧 legacy 状态提取**没有同样的排除**——design.md 状态机表首列的"任意状态"（:835/:845，是通配行不是真实状态）被当成期望状态，PRD 侧永远提取不出来 → 合规旧格式项目 false exit 1。

影响范围：仅 legacy 格式项目（新格式走索引路径不受影响）。修复：design 侧状态提取套用与 :367 相同的排除清单。

### P2-B — subagent-context-contract.md 的 Design Challenger 输入已过时

`subagent-context-contract.md:21`（本轮刚更新过）写 Design Challenger 输入是 `design-model.json` + `materials/facts.json`，但 v2 依赖图中不存在 design-model.json 产出方（挑战职责由 b6-model-review / c4-cross-layer-review 承担，产出 b/c-baseline + conflicts）。SKILL.md:90 已把 design-model 降级为"旧版兼容性交接包"，此契约条目与 v2 现实不一致。修复：把 :21 的输入描述改为 v2 实际输入（上游 baseline/analysis JSON），或明确标注该角色描述适用于旧版路径。

### P3 备注 — 回归测试未覆盖 test-fixture/output 全量对照

test-shitpm-regression 全绿，但 P2-A 的 false positive 没被任何测试捕获（回归用例是独立小样本）。建议加一条用 test-fixture/output 完整对照的端到端用例，legacy 与新格式各一。

## 三、结论

两条修复主线（PRD 检查线、编排接线）全部落地且实测通过，P0/P1 清零。八轮 lineage 首次达到"可进入下一阶段"状态：

- **可以做的**：按 AGENTS.md 原第 7.8 节精神（虽已删除，工程上仍合理），先跑小型合成项目在线冒烟，再考虑真实项目观察性试跑。
- **建议先修的**：P2-A 一行排除清单的事，修完 legacy 项目才不会被 false block；P2-B 改一句契约。
- **不阻断**：两项 P2 都不影响新格式主线流水线。
## 四、问题处理结果

本轮报告中的两项 P2 已确认属实并完成修复：

- **P2-A 已修复**：`prd-consistency-check.py` 在 Design 与 PRD 的状态集合对比边界排除“任意状态”等通配/占位项；状态机内部仍保留该伪状态，避免影响状态机完整性检查。

- **P2-B 已修复**：`subagent-context-contract.md` 已明确 v2 主链由 `b6-model-review` 和 `c4-cross-layer-review` 承担挑战职责，使用 A/B/C baseline、analysis 结果及动作卡声明的输入；`design-model.json`、`design-challenge.json` 仅保留为旧版兼容路径。
- **P3 覆盖建议已处理**：本地回归套件新增 H5 用例，验证旧格式状态机不会因“任意状态”产生误报；该测试脚本属于仓库现有的本地测试资产忽略范围，未改变发布文件边界。

直接验证结果：

- `test-shitpm-regression.py`：37 个用例通过，0 个失败；
- `python -m compileall D:\work\ShitPM\scripts\python`：通过；
- `git diff --check`：通过；
- 未执行在线合成测试、真实项目测试、T4/T5/T6/T8。

