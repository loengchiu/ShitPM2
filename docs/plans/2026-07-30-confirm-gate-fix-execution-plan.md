# 确认门禁时序修复：执行与验收方案

> 交付对象：执行 AI。本文自包含，含现状证据（文件:行号）、改动任务、验收清单、边界。
> 产品经理已拍板方案：把"AI 自检全绿"从"确认之后"前移到"交付确认之前"；下游放行看"人确认 + 机自检"双门。

## 1. 背景（产品视角）

现在的问题：用户一按"确认"，AI 才开始校验，验出问题又把确认拦下——校验和确认顺序反了。用户确认的是一份 AI 自己还没验过的东西，所以"确认"没意义；而且校验只跑了一道（状态机），结构错误和综合审查缺失都查不到。

目标：
1. AI 交付给用户确认前，必须自己跑完全部校验、全绿才发出"请确认"。
2. 用户按确认时不再触发校验（交付前已验完），确认 = 人签字。
3. 下游（PRD/原型）放行 = 人确认 AND 机自检全绿，双门缺一不可。

## 2. 现状与根因（证据）

- `scripts/python/design-confirmation.py:118-153` `run_deterministic_gate`：confirm/check 时只调 `state-machine-check.py` 一道。结构门禁（`design-index.py`）和综合审查都不在确认链路。
- `design-confirmation.py:163-193` `cmd_confirm`：confirm 时跑上面那道，过才写哈希。
- `design-confirmation.py:196-265` `cmd_check`：check 时也跑那道 + 比哈希。"已确认" = 哈希一致 AND 状态机过。**只一道。**
- `skills/spm-prd/SKILL.md:30-34`、`skills/spm-prototype/SKILL.md:15,19-25`：下游放行只看 `design-confirmation.py check`。
- `scripts/python/design-orchestrator.py:806-813` `accept_outputs`（design-editor 接受时）：其实校验综合审查 + 基线齐全（AI 自校验），但**确认链路和下游都不查它**。
- `skills/spm-design/SKILL.md:201-217` §7：报告"完成"条件含"无 P0/P1"和"依赖图必需动作已完成"，但没把"三道门禁全绿"显式钉为"交付确认"前置。
- `contracts/start-action-matrix.md:9-10`：review 在未确认/已确认都可选，不卡门（**保持不变**）。

根因一句话：确认门禁只跑状态机一道、且在 confirm 时跑（事后）；结构门禁和综合审查没进确认链路；下游只看这道弱门禁。

## 3. 执行任务

### 任务 A — spm-design：交付确认前强制 AI 自检全绿

**文件**：`skills/spm-design/SKILL.md` §7（201-217 行附近）

**改**：在"满足以下条件才报告 Design 生成或修改完成"清单中，把第 4 条"不存在 P0 或未处理 P1"扩展为显式三道门禁前置，措辞与现有风格一致：

1. **结构门禁**：`python $BUNDLE/scripts/python/design-index.py compile --project-root . --require-current-format` 退出码 0；
2. **状态机门禁**：`python $BUNDLE/scripts/python/state-machine-check.py --project-root .` 报告 P1=0（Design 明确声明"无状态机/无状态流转"时此项跳过）；
3. **综合审查**（full / full-layered 模式）：编排器 design-editor 已 accept，即 `.workflow/runtime/context/design/review/comprehensive.json` 存在且 P1=0、P2 已处理。

任一未过：**不准发出"请确认"或"Design 完成"**，必须生成受影响的局部修复动作并重验，循环到全绿。简单模式不要求第 3 项。

**为什么**：把 AI 自校验从"确认后"前移到"交付前"，从源头保证用户确认的是已验证产物。

### 任务 B — design-confirmation：confirm/check 前置扩展为三道

**文件**：`scripts/python/design-confirmation.py`

**改**：`run_deterministic_gate`（118-153 行）从"只跑 state-machine-check"扩展为依次跑：

1. `state-machine-check.py --project-root . --source design`（现状保留，P1=0 才过）；
2. `design-index.py compile --project-root . --require-current-format`（**新增**，退出码 0 才过）；
3. 若存在 `.workflow/runtime/context/design/review/comprehensive.json`，校验其 P1=0（**新增**）；不存在则跳过该项（兼容简单模式与无综合审查的场景）。

任一未过：confirm 拒绝写哈希（沿用现有失败 JSON 结构 `{"ok":false,"error":...,"deterministic_gate":...,"hint":...}`，返回 1）；check 返回 `deterministic_gate_failed`（沿用现有 reason，返回 1）。

**约束**：保持现有 JSON 输出字段不变（`ok/error/hint/deterministic_gate/confirmed/reason`），下游和测试依赖这些字段。`deterministic_gate` 报告对象可扩展为含三道各自结果，但不删除现有字段。

**为什么**：让"已确认"判据从"哈希+状态机"升级为"哈希+三道全绿"。下游（spm-prd/prototype）不用改代码，仍调 `check`，自动拿到双门。

### 任务 C — 下游与矩阵：点明双门语义（小改，不改逻辑）

**文件**：`skills/spm-prd/SKILL.md`、`skills/spm-prototype/SKILL.md`、`contracts/start-action-matrix.md`

**改**：在 spm-prd/spm-prototype 的"准入条件"处加一句说明："`design-confirmation.py check` 通过即表示 ① 用户已确认（哈希一致）② AI 自检全绿（结构门禁 + 状态机 + 综合审查，适用项均通过），下游方可继续。" start-action-matrix 的 review 位置（前后可选、不卡门）**保持不变**，仅在"约束"区补一句"review 是可选第二意见，不构成确认或下游放行门禁"。

**为什么**：避免执行者误以为要另查编排器状态；明确 review 仍可选。逻辑不动，只补语义说明。

## 4. 验收清单（可测）

自动化（构造 fixture 跑 `design-confirmation.py`）：

1. **结构错误** design（缺页面必要属性）→ `confirm` 被拒，exit 1，错误信息含 design-index 报错。
2. **状态机孤岛** design（合并实体导致孤岛）→ `confirm` 被拒，exit 1，错误含 state-machine-check P1。
3. **合规简单模式** design（无状态机声明）→ `confirm` 通过，exit 0，`deterministic_gate` 三道结果齐全（综合审查项标 skipped）。
4. **综合审查不达标**：构造 `comprehensive.json` 存在但 P1>0 → `confirm` 被拒，exit 1。
5. **已确认后改 design.md** → `check` exit 2（哈希不一致），reason=`hash_mismatch`。
6. **下游放行**：未确认时 spm-prd 停止、确认后放行（现有行为，不回归）。

回归（跑测试套件，必须全绿）：

7. `python scripts/python/test-shitpm-regression.py` → 37 通过 0 失败（含"坏 Design 含状态孤岛时确认失败关闭"用例）。
8. `python scripts/python/test-design-orchestrator.py` → 12 用例通过。
9. `python scripts/python/test-design-simplification.py` → 通过（双模式 full + full-layered 不回归）。
10. 上一轮"`#### 状态机` 多机归并"修复不回归：合规多状态机 design 的 `confirm` 正确通过。

流程验收（人工/真实跑 spm-design 观察）：

11. full 模式下，编排器未 accept（无 comprehensive.json）时，spm-design 不发出"请确认"（任务 A 生效）。

## 5. 不要碰（边界）

- 不改 `design-orchestrator.py` 的 `accept_outputs` / `_validate_comprehensive_review` 逻辑（综合审查校验已正确）。
- 不改 `design-index.py` / `state-machine-check.py` 内部（上一轮已修状态机 `####` 归并）。
- 不把 review 改成强制门（保持可选第二意见）。
- 不自动确认、不自动推进下游。
- 简单模式不强制要求编排器 accept（兼容）。
- 不引入新模式名词，SKILL 措辞与现有风格一致。

## 6. 给执行 AI 的注意事项

- 三任务可并行，但**任务 B 改完先单独跑验收 1-5**，再跑 7-9 回归，最后做 10-11。
- `design-confirmation.py` 扩展门禁时，三道校验任何一道崩溃/超时都要失败关闭（沿用现有 `try/except` + 返回 False 的模式），不能因一道崩了就放行。
- `design-index.py compile` 的退出码：0=通过，非 0=有错误（JSON 含 `summary.errors`）。判断"通过"用退出码 0 且 JSON `ok==true`。
- `comprehensive.json` 的 P1 判定：读 JSON 的 `issues` 数组中 `severity=="P1"` 计数，或若该文件用 `verdict/issues` 结构则按实际 schema（参考 `design-orchestrator.py:_validate_comprehensive_review` 760-779 行的字段读取方式）。执行前先读该函数确认字段名。
- 任务 A 的 SKILL 措辞要可被模型遵守：写明具体命令和判定（exit 0 / P1=0），不要只写"确保质量"这类模糊词。
- 全部改完，三项测试套件全绿 + 验收 1-6 通过，才算完成。
