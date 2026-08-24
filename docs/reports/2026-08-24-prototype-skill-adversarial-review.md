# Prototype 技能全量对抗式审查（第2轮 · 2026-08-24）

> 审查对象：`skills/spm-prototype/SKILL.md`、references（`prototype-writing.md` / `prototype-shell.md` / `prototype-visual-spec.md` / `prototype-component-behavior.md` / `prototype-mark-injection.md` / `templates/prototype-feedback-classification.md`）、模板 `templates/prototype-vite/`、脚本 `scripts/python/prototype-{source-check,consistency-check,structure}.py`、`design-confirmation.py`、`design-set.py` 及测试套件。
> 方法：全量阅读 → 逐项核对 08-23 审查 D1–D10 修复状态 → 跑脚本实证（规范目标 / 真实模板 / 构造 fixture / 回归测试）→ 边缘交叉（今天改动的断链、孤儿 pyc、并发覆盖风险）。
> 结论先行：**0 个 P0，1 个 P1（新增，D11），6 个待修 P2 + 1 个纠正项（D17 保留）**。相比 08-23（1 P0 / 3 P1 / 6 P2），结构性死点已清除，剩余为一致性与沉积问题。注：本报告原稿将 D17（prototype-p0）列为待修，最终核验确认其跨契约/测试/扫描为活规则，保留正确，已从待修清单移除。

## 评级摘要

| 级 | 编号 | 问题 | 状态 |
|---|---|---|---|
| P1 | D11 | `prototype-consistency-check.py` 参数化编辑被并发覆盖，出现"内部变量化但 CLI 未暴露"破损中间态 | 本轮实证发现并已修复 |
| P2 | D12 | `prototype-visual-spec.md` 标题仍写"Claude / Tabler"二分，与 L5 三选一不一致 | 新发现 |
| P2 | D13 | `prototype-writing.md` L3 引言仍写"Claude 或 Tabler"，与 L51 三选一不一致 | 新发现 |
| P2 | D14 | `SKILL.md` L54 自检项仍写"Claude 或 Tabler 之一"，与 L17 三选一不一致 | 新发现 |
| P2 | D15 | `prototype-shell.md` 示例 Sider/Menu 仍用 `theme="dark"`，与"必须浅色否则覆盖 token"教训冲突 | 新发现 |
| P2 | D16 | `design-confirmation.py` / `prototype-structure.py` 删除后残留 4 个 `__pycache__/*.pyc` | 新发现 |
| P2 | D17 | `prototype-p0` 检查在契约、测试与扫描中均有实际引用，**保留合理**（08-23 D8 维持现状，非缺陷） | 最终核验纠正 |
| P2 | D18 | `SKILL.md` L36 迁移分支仍以 `compiled.js` 为特征词，不覆盖"多 sample HTML"形态（08-23 D4 部分未修） | 核对 |

---

## 一、08-23 审查 D1–D10 修复状态核对

### 已修复（实证确认）

- **D1（P0，design-set 被确认门卡死）→ 已修**。`design-confirmation.py` 已从仓库删除（`scripts/python/` 无此文件，仅剩 `__pycache__` pyc）。08-23 分层修复计划文档明确"不恢复 design-confirmation.py、人工 Design 确认、确认哈希或单体 design.md fallback"。SKILL L16 同步改为"取代单体 `design.md` 与旧确认哈希流程"。原确认门（`design-confirmation.py`）整链移除，design-set 死锁不复存在。设计选型路线从"哈希确认"转向"provenance 依据记录"（`design-set.py record-inputs`）。
- **D2（P1，步骤9/10 验证指令矛盾）→ 已修**。当前 SKILL 已重构为「统一验证与完成判据」单节，L52 只有一条正向指令"用真实浏览器打开默认页和每个注册路由"；"不做浏览器抽查、不逐路由验证"的对立措辞已消失。
- **D3（P1，`_normalize_name` 正则 `s+` bug）→ 已修**。`prototype-consistency-check.py` 现使用 `re.sub(r"\s+", " ", ...)`（L300）归一化按钮文本，无 `r"s+"` 字面 bug；按钮/文本提取链路（L296-300）实测正常，`test-prototype-consistency-check.py` 12 用例全过。
- **D6（P2，退出码语义缺失）→ 已修**。SKILL L63 已写清："只有确定性冲突返回 1；输入或源码工程等致命错误返回 2；返回 0 不代表事实完整"。
- **D7（P2，prototype-structure.py 孤儿）→ 已修（删除）**。`prototype-structure.py` 已从仓库删除；`test-prd-simplification.py` L87/L187 对它的引用是**负向断言**（断言 PRD 最小读取集合不再包含该脚本），语义正确，非死引用。
- **D9（P2，闸门 rglob 未排除 dist）→ 已修**。`_scan_source` 现用 `source_root.rglob("*")` + `EXCLUDED_DIRS`（dist/node_modules/prototype-p0）过滤（L257-261），闸门扫描范围与 `_scan` 一致。

### 部分修复 / 未修复（本次仍生效）

- **D4（P1，迁移分支不覆盖真实目录）→ 部分缓解**。今天已清空 `output/prototype/`（见后文 D19 相关工作），首次生成会直接复制模板，不再触发迁移分支；但 SKILL L36 判定仍以 `compiled.js` 特征词为准（D18），对"非标准 Vite 工程但无 compiled.js"的目录形态仍无明确分支。
- **D5（P2，writing 内部矛盾）→ 大部分已修**。顶栏高度 64px 表述已消除（grep 无 64px 命中，visual-spec L118 统一 56px）；但默认主题在 visual-spec 标题 / writing 引言处仍二分（D12/D13）。
- **D8（P2，prototype-p0 检查）→ 保留（最终核验纠正）**。两脚本仍检查"src 不依赖 prototype-p0 等兄弟目录"（source-check L96-105；consistency-check `EXCLUDED_DIRS` L22）。初判为"死引用"，但最终核验确认契约层 `contracts/prototype-review-checklist.md` L19 明确把"src 引用 prototype-p0"列为 P1 检查项、`test-prototype-consistency-check.py` L228 实际使用、扫描逻辑一致——保留是正确决定，不删（见 D17）。
- **D10（P2，README 首屏检查 + 步骤9措辞）→ 部分保留**。README 首屏检查（source-check L118-139）逻辑与 08-23 一致（"npm run"/"打开 PowerShell"/"在 PowerShell 中执行"任一出现即 FAIL），但这是合理的门禁（BAT 是唯一用户入口），08-23 定为 P2 低危，保留可接受；SKILL 步骤9"三个本地选项"措辞已随重构消失。

---

## 二、新发现问题

### D11 — `prototype-consistency-check.py` 参数化编辑被并发覆盖（P1，本轮实证）

**事实**：今天上午对 `prototype-consistency-check.py` 做了参数化（新增 `--prototype-src` / `--design-manifest`，透传 `_run`）。首次验证通过。但数小时后复查发现：`_run` 签名（L368）与 `main()` 的 argparse（L502-507）**被外部回滚/覆盖**，只剩函数体内的 `proto_src` 变量化逻辑（L369-397）与 `_scan_source(root, proto_src)` 调用——形成"内部已变量化、CLI 未暴露参数"的**破损中间态**：脚本 `--help` 报 `unrecognized arguments`，外部无法指向真实工程。

**根因推断**：多 AI 工具并行编辑同一文件（用户在多 IDE 间切换），或文件被部分恢复。**这正是对抗式审查要抓的活案例：无 git 提交保护的脚本改动有被并发覆盖风险。**

**影响**：脚本参数化功能失效；任何依赖 `--prototype-src` 的调用（如本次 review 的旁证验证）都会失败。

**处理（本次已修复）**：重新补齐 `_run` 签名与 `main()` 参数，验证：`py_compile` 通过；默认调用清单缺失 exit=2；`--prototype-src templates/prototype-vite/src` 生效（source 路径正确反映）；回归 12 用例全过。**建议**：重要脚本改动后立即 `git add` + commit（用户规则"修复未 commit 前不 push"适用于 push，commit 不受限），或至少完成后复读一次全文。

### D12 / D13 / D14 — 品牌主题三选一口径未贯通（P2×3）

今天已把权威入口（SKILL L17、visual-spec L5、writing L51）改为"Claude/Tabler/traework 三选一、默认 Tabler"，但三处旧表述漏改：

- **D12**：`prototype-visual-spec.md` L1 标题"# ShitPM 原型视觉规范（Claude / Tabler 品牌主题 · Ant Design 6 实现）"仍二分。
- **D13**：`prototype-writing.md` L3 引言"品牌主题可选 Claude 或 Tabler，但单个原型只选一套"仍二分。
- **D14**：`SKILL.md` L54 自检项"品牌主题只使用本轮选择的 Claude 或 Tabler 之一"仍二分。

影响：agent 读不同文件会得到"三选一 vs 二选一"两种口径，与 D2 同类的指令歧义（低危但同类）。修复：三处统一为"Claude/Tabler/traework 三选一（默认 Tabler）"或直接指向权威入口。

### D15 — `prototype-shell.md` 示例仍用 `theme="dark"`（P2）

`prototype-shell.md` L115/L117 的 App.jsx 示例仍写 `<Sider theme="dark">` / `<Menu theme="dark">`。这与项目已实证教训冲突：**Sider/Menu 写 `theme="dark"` 会覆盖 antd 主题 token（记忆：2026-08-21 踩坑）**，真实模板 `templates/prototype-vite/src/App.jsx` 已验证无 `theme=` 属性（浅色模式）。shell.md 是"多页面 shell 任务"的读取文件，示例会教坏 agent。

修复：示例删除 `theme="dark"`（或改为注释说明"必须浅色模式，深色观感由 CSS 变量承载"），与真实模板一致。

### D16 — 已删脚本残留 `__pycache__` pyc（P2）

`scripts/python/__pycache__/` 残留 4 个已删脚本的编译缓存：`design-confirmation.cpython-313.pyc` / `-314.pyc`、`prototype-structure.cpython-313.pyc` / `-314.pyc`。任何 `import` 扫描或误引用都可能碰到陈旧字节码。修复：删除这 4 个 pyc（无源码的缓存是纯垃圾）。

### D17 — `prototype-p0` 检查保留（最终核验纠正：非死引用）

初判（本报告原稿）认为 `prototype-p0` 是"死引用"，建议从两脚本移除。最终核验推翻该判断：

- `contracts/prototype-review-checklist.md` L19 把"src 引用 dist 或 prototype-p0"明确列为**P1 检查项**（不得通过）。
- `test-prototype-consistency-check.py` L228 用 `("dist", "node_modules", "prototype-p0")` 作排除目录断言。
- `prototype-source-check.py` L96-105 与 `prototype-consistency-check.py` L22 的扫描/排除逻辑与契约、测试一致。

结论：`prototype-p0` 是跨契约→测试→扫描的**活规则**，保留正确；若未来确无此概念，应从契约、测试、脚本三处同步移除，而非单删脚本。**不列为待修项。**

### D18 — SKILL 迁移分支特征词过窄（P2，08-23 D4 未修）

SKILL L36"若目标是旧静态 HTML + compiled.js 原型，先报告迁移边界"——只覆盖 `compiled.js` 形态。对"多 sample HTML + lib + 空目录"等非标准形态无明确分支。今天清空 `output/prototype/` 后首次生成直接复制模板、不触发该分支，故当前无实际影响，但判定逻辑仍窄。修复：改为"目标已存在且非标准 Vite 工程（缺 src/ 或 package.json）→ 停，报告非标准目录"。

---

## 三、实证记录（非结论，供溯源）

- `prototype-source-check.py`：规范目标 `output/prototype/`（已清空）→ 9 项 FAIL（缺工程，符合"未生成"预期）；真实模板 `templates/prototype-vite/` → 全部 PASS。
- `prototype-consistency-check.py`：默认调用 → 清单缺失 exit=2（行为正确）；`--prototype-src templates/prototype-vite/src` → source 路径正确生效；回归 12 用例全过。
- `design-set.py`：`record-inputs` / `check-inputs` / `commit-single` 子命令均存在；`test-design-set.py` 20 用例 OK。
- `test-prd-simplification.py` / `test-prototype-source-check.py`（7 用例）：PASS。
- 今天清理 `output/prototype/` 残留（旧 arco/vue 样例）后目录为空，`git status` 仅登记 `index.html` 删除，未 commit。

---

## 四、问题分类统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 结构性问题 | 0 | 无 P0；D1 死点已通过删除确认门解决 |
| 内容质量问题 | 0 | — |
| 一致性问题（P2） | 5 | D12/D13/D14 三选一未贯通、D15 shell dark 示例、D18 迁移特征词（D17 已纠正为"保留"） |
| 工程/流程问题 | 2 | D11 并发覆盖风险（P1）、D16 pyc 残留（P2） |

---

## 五、修复优先级建议

1. **D11（P1，已修）**：本次已重新补齐参数化并验证；建议建立"重要脚本改动后立即 commit"习惯，防止多 AI 并发覆盖。
2. **D12/D13/D14（P2）**：三处二分表述统一为三选一，一处编辑即可收口。
3. **D15（P2）**：shell.md 示例去 `theme="dark"`，与模板及教训一致。
4. **D16/D18（P2）**：清 pyc、扩迁移判定——可合并一次小修。D17 不修（保留合理）。

## 六、与 08-23 轮对比

| 维度 | 08-23 | 08-24 |
|---|---|---|
| P0 | 1（确认门死锁） | 0 |
| P1 | 3 | 1（D11，且已修） |
| P2 | 6 | 7 |
| 结构性死点 | design-set 无法生成 | 无（可生成，缺真实 Design 对齐） |

---

审查时间：2026-08-24
