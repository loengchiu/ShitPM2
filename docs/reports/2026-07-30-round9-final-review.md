# 第九轮审查报告（最终轮，2026-07-30 早晨）

## Verdict：主线通过，但发现 1 项新 P1（宿主安装器被 AGENTS.md 删除砸坏），1 项新 P2（legacy 枚举提取假阳性），1 项 P3

审查范围：第8轮遗留 P2-A/P2-B 修复验证 + AGENTS.md 整文件删除（commit 6c7e332）的影响面 + 全仓收口扫描。所有结论均实测，非文字核对。

---

## 一、第8轮遗留项验证：全部真修

### P2-A（legacy 状态通配词）：已修 ✅
- `prd-consistency-check.py:46` 新增 `NON_CONCRETE_STATE_NAMES = frozenset({"—","-","N/A","任意状态","状态"})`，`:1403-1405` 注明 legacy 对比边界排除通配/占位行。
- 实测：legacy fixture（test-fixture/output 全量）`total_missing: 0`——第8轮的"任意状态永远 missing"假阳性消失。

### P2-B（subagent 契约过时输入）：已修 ✅
- `subagent-context-contract.md:21` 重写：v2 主链不再以 `design-model.json` 为输入，挑战职责由 `b6-model-review` / `c4-cross-layer-review` 承担，输入为过门禁的 A/B/C baseline；`:23` 明确 `design-model.json` 仅旧版兼容路径。与 v2 依赖图一致。

### 主线回归：全部保持 ✅
- 新格式合规产物（design 5.2 格式 + PRD 模板格式）：EXIT 0。
- 故意违规产物：EXIT 1（正确阻断）。
- 定向实验：在新格式 design「取值与默认」写 `格式：V1.0、V2.0，默认 V1.0`、PRD 表写 `格式 V1.0、V2.0` → EXIT 0，`total_deterministic_attribute_mismatch: 0`。新格式主线不受下述 P2-C 影响。
- 测试套件 7 项全绿（orchestrator / replay / design-index / context-runtime / context-loading / regression / resource-integrity）。

---

## 二、新发现问题

### P1-A：AGENTS.md 整文件删除砸坏宿主安装器（必修）

commit 6c7e332 删除了整个 AGENTS.md（102 行），但 `scripts/python/shitpm-host.py:189` 的 `verify_bundle_mapping` 把 `AGENTS.md` 存在性作为 bundle 映射正确性的判据：

```python
if not (path / 'AGENTS.md').exists() or not (path / 'skills').exists():
    raise RuntimeError(f'bundle mapping target wrong: {path}')
```

- `cmd_install`（:303-310）和 `cmd_verify`（:313-317）都调用它。
- **实测**：`python scripts/python/shitpm-host.py verify --host codex` → `bundle mapping target wrong: C:\Users\guduj\.codex\shitpm`，真实 EXIT 1。
- 影响：README.md:157-176 的四条 install 命令和 verify 命令**全部必然失败**。新用户按 README 安装 ShitPM 直接挂。
- 修复二选一：
  1. 改 `shitpm-host.py:189` 判据为 `skills/` + `README.md`（或 `contracts/`），不再依赖已删除的 AGENTS.md；
  2. 保留一个极简 AGENTS.md 占位（但既然决定删除，方案 1 更干净）。
- 附带：user_memory 和安装器写入宿主的 global rules 中"读 AGENTS.md"的指引也已过时，需同步清理。

### P2-C：legacy 字段提取器把约束文字当枚举值 → legacy fixture 仍 false exit 1

P2-A 修掉了状态层假阳性，但 legacy 路径还有第二层：test-fixture/output 全链路复测 `exit_reason` 从 `possible_omission` 变成 `deterministic_conflict`，**仍然 EXIT 1**。

- `total_deterministic_attribute_mismatch: 38`，逐项核查全部是提取假阳性，典型：
  - `计划版本`：design 原文 `格式：V1.0、V2.0` 被拆成枚举 `["格式：V1.0","V2.0"]`，PRD 侧 `格式 V1.0、V2.0`（无冒号）不拆 → 判"确定性枚举冲突"；
  - `附件`：`单文件≤100M、支持多文件` 成了两个"枚举值"；
  - `通知书编号`：`格式：TZ-YYYY-NNN、系统自动生成` 成了枚举；
  - `保管期限`：design `10年` vs PRD `10 年`——空格差异被判确定性冲突（无规范化）。
- 根因：legacy 表格「枚举值/规则」一列混装约束说明和真枚举，提取器无差别按顿号切分；且比较前不做空白规范化。
- 边界已实测确认：新格式主线走 PRD 专用提取器，不受影响。此问题只阻断旧格式项目。
- 修法方向：legacy 枚举提取加启发式过滤（含"格式：""系统自动""≤""最大""唯一"等约束特征词的不算枚举）+ 比较前去空白规范化。

### P3：回归测试仍未覆盖 legacy fixture 全链路

P2-A（第8轮）和 P2-C（本轮）都发生在同一条 legacy 路径上，且都只能靠人工全链路跑 test-fixture/output 才能发现。`test-shitpm-regression.py` 至今没有"legacy fixture 全量对照必须 EXIT 0"的用例。不补这条，legacy 路径每改一次就可能再引入一个假阳性。

---

## 三、AGENTS.md 删除的内容影响评估（除安装器外）

- 原第2节产品契约 14 条：核心语义已分布在 `skills/spm-design/SKILL.md`、`contracts/fix-propagation-rules.md`、`contracts/review-checklist.md`、`references/prd-writing-rules.md`、USAGE.md 中，且原文自述"产品契约以仓库内现行 skills/contracts/references/schemas/templates 定义为准"。**契约语义无丢失**。
- 原第 3-6 节工程原则（Think Before Coding / Simplicity First 等）：无代码依赖，删除无影响。
- 全仓 grep：除 `shitpm-host.py` 外无其他脚本/skill/契约引用 AGENTS.md。悬空面收敛在安装器一处。

---

## 四、九轮审查最终状态

| 项 | 状态 |
| --- | --- |
| P0 | 0 |
| P1 | 1（P1-A 安装器，本轮新发现，修复量约 1 行） |
| P2 | 1（P2-C legacy 枚举提取，不阻断新格式主线） |
| P3 | 1（回归缺 legacy 全链路用例） |
| 新格式主线（design→index→PRD 检查→orchestrator） | 双向验证通过，可用 |
| 测试套件 | 7/7 绿 |

## 五、放行条件

1. **修 P1-A 后**即可进入小型合成项目在线冒烟——主线功能本身已就绪，安装器是新环境部署的前置。
2. P2-C 不阻断新项目，可与在线冒烟并行修。
3. P3 建议随 P2-C 一起补：regression 加一条 "legacy fixture 全链路 EXIT 0" 用例，作为 legacy 路径的守门。
