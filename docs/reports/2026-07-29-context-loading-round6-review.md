# ShitPM 上下文装载迭代 · 第六轮全量对抗性审查（编排提速版）

> 日期：2026-07-29
> 触发：用户因"运行太慢"修改了流程编排，要求重新全量审查
> 方法：不信任记忆、全部实测验证；结论与代码/运行结果对齐
> 后续状态：本报告中的 design-model/design-challenge 门禁缺口已在第七轮复审后的实现中纳入兼容门禁与 v2 交接门禁；本报告仅保留历史审计结论。

## Verdict：通过（无 P0 / P1，1 项 P2，6 项 P3）

这一轮是**真实架构迁移**，不是小修。用户把"每次重扫 marker + 主 Agent 长对话串行注入原文"改成了"预建项目级材料索引（`source-index.py`）+ 缓存复用 + 隔离上下文读取 + 确定性交接门禁（`context-runtime-check.py`）"。架构方向正确，核心提速逻辑（索引/复用/来源校验）经测试与实测均成立。**但有一个契约级接线缺口：最重要的两个交接（design-model / design-challenge）的确定性门禁在代码里存在、实测可用，却从没被 skill 调用。**

---

## 一、本轮实际改了什么（基线）

新增脚本（全未跟踪）：
- `scripts/python/source-index.py` — 项目级材料索引：按标题/80 行窗口切片、sha256、缓存到 `.workflow/runtime/materials/`，材料未变则复用（`material_revision` 为缓存键）。
- `scripts/python/context-runtime-check.py` — 确定性门禁：交叉校验 manifest/index/facts 的 `material_revision`、hash、行范围、体量，防陈旧缓存与越界输入。
- `scripts/python/context-run.py` — **指标记录器**（注意：名字像编排器，实际只写 metrics，不做编排）。
- `scripts/python/test-context-runtime.py` — 新测试，覆盖 source-index 五态 + facts 校验 + 版本/来源越界拒绝。

修改：
- `contracts/subagent-context-contract.md` — Material Reader / Design Challenger 输入改为索引片段 / `facts.json`；"所有交接必须通过 context-runtime-check.py"。
- `skills/spm-design/SKILL.md` — D0 新增材料资产准备步骤；`facts.json` 复用策略；`material-facts` 检查标注为完整模式专用。
- `skills/spm-align/SKILL.md` — 大改写（-139 行），优先复用材料资产、不重复建索引。
- `scripts/python/context-pack.py` — 仅新增 metrics 输出（耗时/体量埋点）。
- `scripts/python/stage-context.py` — `context-runtime-check.py` 加入 design 阶段 MINIMAL_READ_SET。

测试现状：`test-context-loading` / `test-resource-integrity` / `test-context-runtime` 全 PASS；`state-machine-check` 0 P1、1 历史遗留 P2（非本迭代）。

---

## 二、P2（契约级接线缺口，必须修）

### P2-1 — `design-model.json` / `design-challenge.json` 交接门禁从未被调用
- 契约（`subagent-context-contract.md`）明令：**"所有交接必须通过 context-runtime-check.py 的来源、版本和体量检查后才能被主 Agent 采纳"**。
- `context-runtime-check.py` **已支持** `--require design-model --require design-challenge`（校验 design-model.json 的 7 个必需字段、design-challenge.json 的 findings、以及体量上限）。
- 实测确认门禁**本身可用**：手动造合法文件 → `valid=True`、四项全过；篡改缺字段 → 正确拒绝（EXIT=1）。
- **但全仓 grep 证实：没有任何 skill / harness 调用 `--require design-model` 或 `--require design-challenge`**。spm-design / spm-align 的 SKILL.md 只调用 `material-manifest / material-index / material-facts` 三种。
- 后果：按 spm-design 跑，主 Agent 写出 `design-model.json` 后**直接采纳、从不校验来源/版本/体量**——契约的硬要求被架空。本轮编排的核心卖点之一"隔离上下文 + 确定性交接门禁"在这两个最关键交接上**形同虚设**。
- **修复**：在 spm-design 的完整模式流程里，写完 `design-model.json` 后、主 Agent 采纳前，插入 `context-runtime-check.py --require design-model`；同理 `design-challenge.json` 后插入 `--require design-challenge`。（注意：这恰是 round 1 发现的"门存在但没接线"同类问题在新生子系统上的重演。）

---

## 三、P3（质量/维护性，非阻断）

### P3-1 — `estimate_tokens` 已复制 5 份，漂移风险升级
`context-budget.py:22` / `context-pack.py:180` / `context-run.py:12` / `context-runtime-check.py:13` / `source-index.py:30` 各有独立副本，公式均为 `cjk*0.6 + 非cjk*0.25`。
- round 3/4 时只有 2 份；本轮新增 3 个脚本又各抄一份 → 现在 5 份。
- 风险：任一处调参，其余 4 处静默不一致，导致预算/体量核算跨组件漂移。
- **修复**：抽成 `scripts/python/token_estimate.py` 单一模块，5 处 import。本次架构扩张正好该做这件事。

### P3-2 — `source-index.py` 悬空引用 `facts.json`
`source-index.py:264-265` 在 run 记录里写 `facts_path: 'materials/facts.json'` 和 `facts_reused: bool(reused and facts.json.is_file())`，但**整个脚本从不创建 `facts.json`**（它是 Material Reader 的 LLM 产物）。
- 后果：run 记录里的 `facts_path` 指向一个本脚本不负责的文件；`facts_reused` 标志含义模糊（source-index 并不管理 facts 生命周期）。
- **修复**：要么移除该字段，要么把"facts 复用"语义明确交给调用方（Material Reader 阶段）写入，source-index 不越权报告。

### P3-3 — `test-context-runtime.py:119` 死代码
```python
stage_context = read(ROOT / 'scripts/python/stage-context.py') if False else None
```
`if False else None` 恒为 None 且从未使用，属调试残留。删除。

### P3-4 — `context-runtime-check.py` 的 token 上限是魔法数字，与契约原则张力
`--max-material-facts 8000` / `--max-design-model 16000` / `--max-design-challenge 8000`（line 159-161）。
- 契约（subagent-context-contract.md 改写段）明确**"不使用固定页数或字段数作为硬门槛"**；而脚本用硬编码 token 上限做硬拒。
- 交接产物的体量上限（防止隔离上下文膨胀）与"不用品类数量门槛"语义不同，但命名/原则上容易混淆。
- **修复**：在契约或脚本注释里说明"交接产物体量上限是隔离机制的一部分，非产品门槛"，消除读者误解；或把数字提成常量并注明依据。

### P3-5 — 提速主张无基准测试
本轮改动理由明确是"太慢"。但：
- 无 before/after 耗时基准、无性能断言测试；
- 正确性（索引/复用/来源校验）已充分测，但"是否真更快、快多少"未实证。
- **修复**：加一个计时冒烟（如 5 次 source-index 复用 vs 全量重扫耗时对比），把提速从主张变成可回归指标。

### P3-6 — `facts.json` 复用语义的边界情况
skill 规定"材料未变化时复用已有 `facts.json`"。但 `material_revision` 只绑定**材料内容**，不绑定**本轮分析意图**。若材料未变、但本轮问题变了，复用的旧 `facts.json` 可能与新意图无关。
- 当前设计把 facts 视为"材料派生事实"，不随问题变，属合理取舍；风险低。
- **修复**：若希望 facts 随意图失效，需在 `facts.json` 记录分析意图指纹并在复用时比对。属可选增强，非必须。

---

## 四、值得肯定的（做对了的部分）

- **source-index 复用/差异逻辑扎实**：`created / reused / updated / added / removed` 五态在 `test-context-runtime.py` 全测；单来源变更、增删来源识别正确；`material_revision` 跨 manifest/index 一致。
- **context-runtime-check 来源校验严格**：manifest/index/facts 三方 `material_revision` 交叉、sha256 比对、行范围合法性、重复来源检测——这是 AGENTS.md 规则 11"程序只阻断可可靠证明的结构错误"的正确落地。
- **simple 模式不误触发 material-facts**：`--require material-facts` 仅在完整模式块内出现，不会在 simple 模式因 `facts.json` 缺失而硬失败（round 5 曾担心的盲区，实测安全）。
- **上下文装载层未受影响**：context-pack 仍每轮从 references/templates 实读，不受 material 索引缓存影响，无陈旧风险。
- **测试套件全绿**。

---

## 五、提交前建议清单

| 优先级 | 项 | 动作 |
|--------|----|------|
| **P2** | P2-1 | 在 spm-design 完整模式里接线 `context-runtime-check --require design-model / design-challenge`，落实契约硬要求 |
| P3 | P3-1 | 抽 `token_estimate.py` 单一模块，消除 5 份副本 |
| P3 | P3-2 | 清理 source-index 对 facts.json 的悬空引用/误导字段 |
| P3 | P3-3 | 删 test-context-runtime.py:119 死代码 |
| P3 | P3-4 | 澄清 token 上限与"非硬门槛"原则的关系 |
| 建议 | P3-5 | 加提速基准测试，把"更快"变成可回归指标 |

**总结**：编排提速的架构方向正确、核心机制经测可用，无阻断项。唯一的 P2 是契约级接线缺口——**确定性交接门禁对 design-model / design-challenge 这两个最关键交接完全没接线**，门在代码里存在且实测有效，但 skill 不调用，等于架空了本轮"隔离 + 确定性交接"的核心承诺。修 P2-1 即可提交；P3-1（5 份 estimate_tokens）建议顺手清，因为架构已扩张到 5 个脚本共用同一公式。
