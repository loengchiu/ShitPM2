# R18 对抗性审查报告：PRD 分片读取 Design（context-pack --module）执行验收复核

> 日期：2026-08-05
> 审查对象：工作区相对 HEAD `2915771` 的全部未提交改动（15 个文件），核心为 fragment-reading 方案落地（`context-pack.py --module` 分片读 Design + SKILL/rules/scene/Review 四件套 + 测试），含历史遗留（操作表十列等 action-interaction 内容）复核
> 审查基线：`docs/plans/2026-08-05-prd-design-fragment-reading-plan-and-acceptance.md`（方案）+ `docs/reports/2026-08-05-prd-design-fragment-reading-report.md`（执行报告，自称"通过、12/12 绿"）
> 方法：执行报告结论逐项复核 + 审计系统副本（`D:/ShitPM-tmp/audit_copy`，design.md 4565 行）实测 + 对抗性模拟（阈值绕过、LCS 漏关联、--pages 语义）+ 全量测试 + R17 遗留项核对

## 1. 结论

**0 P0 / 2 P1 / 4 P2。** 执行报告的"通过"结论**不成立**——方案的核心确定性约束（片段行数 ≤ 全文 1/3 超阈值报错）存在可被真实场景绕过的实现缺陷，且 SKILL 的 `--pages` 指令与实现行为不一致会导致页面静默缺失。其余声称（12/12 全绿、token 预算、compile 索引行为、副本回归）经复核均属实。

**修复状态（2026-08-05 同日）**：2 项 P1 均已修复并实证，新增 2 项回归断言，12/12 测试全绿（详见 §3 与 §5）。

| 结论项 | 执行报告声称 | 复核结果 |
|---|---|---|
| 12/12 测试全绿 | ✓ | ✓ 属实（全量重跑通过） |
| --module 提取非空/含目标闭环/不含无关闭环 | ✓ | ✓ 属实（审计副本闭环三提取正确） |
| 片段行数 491 行 / 4565 = 10.7%（远小于全文） | ✓ | **✗ 口径错误**：实际片段内容 802 行 = 17.6%；491 是 `included_lines`，**页面章节行数未计入**（详见 P1-1） |
| 片段超阈值时报错提示拆分 | ✓ | **✗ 约束可被绕过**：页面行数不计入阈值判断，大页面模块可静默产出接近/超过全文的片段（详见 P1-1，模拟实证 103%） |
| 匹配不到时报错列标题清单 | ✓ | ✓ 属实 |
| `--pages` 显式补充页面 | ✓（SKILL 指令） | **✗ 闭环匹配时 `--pages` 被静默忽略**（详见 P1-2） |
| 上下文预算 24.8k、32k 可跑通 | ✓ | ✓ token 数字属实（13,029 / 20,280 / 24,839 均为真实估算）；行数标签错误不影响结论 |
| design-index compile 非零退出 ≠ 不可用 | ✓ | ✓ 属实（compile 失败时索引文件仍生成） |
| 副本回归字段定义/页面展开度/重复文案改善 | ✓ | ✓ 样本存在，改善可回读（旧 PRD 0 字段定义 vs 新样本 21 字段逐行定义；"刷新页面重试" 122 → 0） |

## 2. 审查范围与实证方法

| 范围 | 说明 |
|---|---|
| 核心 | `scripts/python/context-pack.py`（+228 行，--module/--pages/--fragment-threshold/verify fragment 来源）、`skills/spm-prd/SKILL.md`、`references/prd-writing-rules.md` §0.7、`references/prd-scene-checklist.md`、`contracts/prd-review-checklist.md` 8.1、`test-context-loading.py`、`test-prd-simplification.py` |
| 复核 | `design-index.py`（操作表十列）、`templates/design.md`、`templates/prd.md`、`design-review-checklist.md` X7、`fake-design-host.py`、`test-design-index.py`、`design-writing.md` |
| 实测环境 | 审计副本 `D:/ShitPM-tmp/audit_copy`（design.md 4565 行 / 279 页面区块 / 61 页索引）；模拟 design 构造；全量 12 个测试套件 |

对抗性实证一览：

```
[实测1] 审计副本 --module 底稿作业：included_lines=491，实际片段内容=802 行（17.6%），run.json 记录 491
[实测2] 模拟 10 页面×100 行（全文 1116 行）：实际片段 1151 行 = 全文 103%，included=90 ≤ 372 不触发超阈值报错
[实测3] extra_pages=['整改台账'] + 闭环匹配：片段不含"整改台账"（静默忽略）
[实测4] 页面名与闭环名无共享 2 字（入库单/出库单 vs 订单处理）：0 页面关联，--pages 也无法补救
[实测5] compile 缺页面属性 exit=1：索引文件仍生成于 .workflow/.../design-index.json（与 SKILL 描述一致）
[实测6] 全量 12 套件重跑：12/12 绿（含 --module 分片用例）
```

## 3. 发现的问题

### P1（2 项，阻断合并前必须修）

#### P1-1：超阈值约束被绕过——页面行数未计入 `included_lines`，片段统计口径失真

**位置**：`scripts/python/context-pack.py` `extract_design_fragment`（`page_lines` 变量计算后从未加入 `included_lines`）

```python
page_lines = 0
for page in matched_pages:
    ...
    page_lines += end - page['line'] + 1   # ← 算了
# ...
if len(lines) >= LARGE_DESIGN_LINES and included_lines > max(1, int(len(lines) * threshold_fraction)):
    raise RuntimeError(...)                # ← included_lines 不含页面行
```

**实证**：
- 审计副本"底稿作业"：`included_lines=491`（闭环 37 + 共用 454），实际片段 802 行（页面 4 章 ≈ 300 行）；报告"491 行 / 4565 = 10.7%"实际应为 **802 行 / 17.6%**；run.json `lines=491` 与 pack 文件实际 812 行（含渲染头）不一致。
- 模拟（10 个"订单页面×"100 行，全文 1116 行）：实际片段 **1151 行 = 全文 103%**，`included=90 ≤ 1116/3=372` → **不触发超阈值报错**。

**影响**：方案 §6.2 验收第 2 条（"片段行数 ≤ 全文 1/3"）与 SKILL"模块边界过大（片段超阈值报错）时按子闭环/页面拆分"的确定性防线**有洞**——真实项目闭环关联 6-8 个页面（页面部分 800-1600 行）时即可静默产出超限片段，恰是本方案要消灭的"上下文爆炸"场景。报告与 run.json 的行数口径失真还会误导下游消费者（metrics/verify 若以 lines 判断会误判）。

**修复**：`included_lines += page_lines`（或阈值判断与 `lines` 字段直接用实际片段行数）；同步修正执行报告数字（491→802、10.7%→17.6%）与 `check_design_fragment` 测试断言口径（当前测试与实现同口径，测不出此问题）。

**已修复（同日）**：`page_lines` 在页面循环后加入 `included_lines`（context-pack.py `extract_design_fragment`）；新增 `build_page_heavy_design` 回归用例（闭环/共用小、页面 6×150 行，全文 ≥1000 行，修复前静默通过、修复后报错"拆分"）。修复后实证：审计副本"底稿作业" `included_lines` 491→784（实际片段 802 行，占比 17.2%，仍 < 1/3 不误伤）；模拟 10 页面×100 行（全文 1116 行）修复前不报错（实际片段 103% 全文）、修复后触发超阈值报错；小 Design（212 行）不误伤（lines=206）。run.json fragment lines 同步修正 491→784，总 lines 959→1252。12/12 测试全绿。

#### P1-2：SKILL 的 `--pages` 指令与实现不一致——闭环匹配时 extra_pages 被静默忽略

**位置**：`extract_design_fragment`（closure 匹配分支不消费 `extra_pages`）；`skills/spm-prd/SKILL.md` 阶段 C（"加 `--pages <页面名>` 显式补充页面"）

**实证**：
- `extra_pages=['整改台账']` + 模块"底稿作业"（闭环匹配成功）→ 片段**不含**"整改台账"，无任何告警。
- 叠加场景：闭环正文不出现页面名（真实项目常见，如"录入底稿"而非"底稿列表"）、页面名与闭环名无共享 ≥2 字（LCS 失败）→ **页面必漏**，且此时 `--pages` 也无法补救（SKILL 却告诉模型可以）。

**影响**：模型照 SKILL 操作拿不到声明页面，页面漏关联直接导致 PRD 模块写作缺页面事实（违反"每个 Design 页面必须至少在一个功能模块的 4.x.6 落点"）。执行报告 §七.2 已承认 `--pages` 组合"未在真实项目验证"，但问题不止"未验证"——**当前实现下闭环匹配时该参数根本不生效**，属指令与行为的确定性不一致。

**修复**：closure 匹配时把 `extra_pages` 并入 `matched_pages`（按 `_match_pages` 精确匹配去重）；SKILL 措辞改为"`--pages` 显式追加页面（用于补充标题词关联漏掉的页面）"。

**已修复（同日）**：closure 匹配分支在 `_related_pages` 后并入 `extra_pages` 精确匹配的页面（按名称去重，不存在的页面名静默跳过，与兜底分支行为一致）；SKILL 阶段 C 措辞改为"`--pages <页面名>` 可显式追加页面（用于补充标题词关联漏掉的页面，可重复传多个），闭环匹配成功后同样生效"。新增断言：`extract_design_fragment(root, '订单处理', extra_pages=['库存列表'])` 必须含"相关页面：库存列表"。实证：审计副本 `--pages 整改台账` + 模块"底稿作业"（闭环匹配）→ 片段含"整改台账" ✓；不存在的页面名被跳过不报错 ✓。12/12 测试全绿。

### P2（4 项）

| # | 问题 | 位置 | 说明 |
|---|---|---|---|
| P2-1 | `CLOSURE_HEADING_RE` 不认字母编号 | context-pack.py | 只认 `闭环[一二三四五六七八九十0-9]+`，"闭环A/B/C"匹配不到 → 按页面名兜底 → 兜不住报错列清单（不静默，可接受）；但报错信息会误导（明明有闭环章节）。建议正则加 `A-Za-z`。 |
| P2-2 | shared 章节全量提取 vs 计划"相关部分" | context-pack.py `_design_headings` / 提取逻辑 | 计划 §5.1 第 4 条"提取共用的业务对象/权限**相关部分**"，实现为全量 shared 章节（审计副本 4 章：业务对象 286 行 + 权限 105 行 + 页面清单 68 行 + 待确认 5 行，每模块全量携带）。页面清单对 279 页面大项目会显著膨胀；"片段 ≤ 1/3"约束被 shared 全量进一步压缩。确定性近似可辩护（"相关"需语义），但计划文本与实现有偏差，且页面清单可按"仅保留与模块页面相关的行"确定性过滤。 |
| P2-3 | R17 六项 P2 仅修 1 项，5 项延续 | 全仓库 | R17 P2-6（模板展示行为段）已随列表式格式修复 ✓；**P2-1 跨层优化 A-01~A-12 验收仍未执行**（fragment-reading 的副本回归是另一回事）；P2-3 编号小数混排**加剧**（新增 8.1/9.1，现共 7 处小数编号）；P2-4 结构适配差异未成类；P2-5 两层治理方案仍未执行（"完成判据：" 0 命中）；P2-2 行尾符仅做了一半（md 统一 LF、py 保持 CRLF，混合仍存）。 |
| P2-4 | 执行报告行数口径错误 | fragment-reading 报告 §三/§四 | "491 行 / 10.7%"应为 802 行 / 17.6%；"阶段 C 单模块合计 959 行"应为 1270 行。token 数字（13,029 / 20,280 / 24,839）为真实估算不受影响，32k/16k 结论成立。 |

### 观察（非问题）

- `--module` 与 `--pass` 不绑定（`--pass writing --module` 也会装载 fragment）——宽松，无实际危害。
- LCS 2 字关联在审计副本恰好全对（含"底稿"的 4 个页面全部命中、无其他含"底稿"页面），但这是"碰巧"：若存在"底稿删除记录"等页面会误关联，若闭环正文不提页面名且无共享 2 字会漏（P1-2 场景）。
- SKILL 阶段 A"禁止全文粘贴索引 JSON"依赖模型遵守指令，无脚本门禁（方案 §10 明确不新增检查器），与 R17 判断一致。
- 测试 `check_design_fragment` 的 large 用例期望报错，恰是因为样本 shared 全量较大（included 816 > 全文/3），与 P1-1 的绕过路径无关——同口径缺陷，修 P1-1 后需同步。

## 4. R16/R17 结论复核（当前状态）

| 前轮结论 | 当前状态 | 判定 |
|---|---|---|
| R17 P1-1 design-state-format 章节结构损坏 | 已修复并随 2915771 提交 | ✅ |
| R17 P2-6 模板展示行为段为正文示例 | 已改为 `<!-- -->` 注释 + 列表式示例（L89/93），标题前缀已清除（rules §3 格式要求 + scenes 137 行自检钉死） | ✅ |
| R17 P2-3 编号小数混排 | 未修且加剧（新增 8.1/9.1） | ❌ 延续 |
| R17 P2-4 结构适配差异未成类 | 未修 | ❌ 延续 |
| R17 P2-5 两层治理未执行 | 未执行（"完成判据：" 0 命中） | ❌ 延续 |
| R17 P2-1 跨层优化验收未执行 | 未执行（无 A-01~A-12 报告） | ❌ 延续 |
| R16 操作表十列 + design-index 解析器同步 | 与记忆一致：OPERATION_TABLE_HEADERS 十列、fake-design-host/test-design-index 样本同步、Review X7 检查项落地 | ✅ |

## 5. 建议（按优先级）

1. **修 P1-1（已完成）**：`included_lines += page_lines`，让超阈值约束与 `lines` 字段反映真实片段规模；同步修正执行报告与 run.json 口径、测试断言。已执行并回归通过（见 §3）。
2. **修 P1-2（已完成）**：closure 匹配时合并 `extra_pages` 进 `matched_pages`；SKILL 措辞改为"显式追加"。已执行并回归通过（见 §3）。
3. 低风险一致性（P2-1/P2-2）：CLOSURE_HEADING_RE 加字母编号；页面清单按模块页面名过滤行。
4. 明确 R17 五项延续 P2 的去留：跨层验收（A-01~A-12）与两层治理是否纳入后续轮次，需与用户对齐预期——已跨两轮未决。
5. 提交前统一行尾符（md LF / py CRLF 现状），避免 git 历史噪音。

## 6. Git 状态

- 本次审查只读（未修改任何仓库文件）；临时探针脚本位于 `D:/ShitPM-tmp/`（不入库）；
- 工作区 15 个改动文件 + 4 个未跟踪方案/报告均未提交（fragment-reading 7 文件 + action-interaction 历史遗留 8 文件叠加）；
- 未执行 commit / push。
- **修复后追加改动**（相对上述审查基线）：`scripts/python/context-pack.py`（P1-1/P1-2 修复）、`scripts/python/test-context-loading.py`（`build_page_heavy_design` + 2 项断言）、`skills/spm-prd/SKILL.md`（`--pages` 措辞）、本报告。以上均未提交。
