# Prototype 技能对抗式审查（含边缘交叉检查）

> 审查对象：`skills/spm-prototype/SKILL.md`、依赖 references（`prototype-writing.md` / `prototype-shell.md` / `prototype-feedback-classification.md`）、模板 `templates/prototype-vite/`、检测脚本 `scripts/python/prototype-{source-check,consistency-check,structure}.py` 与 `design-confirmation.py`。
> 方法：全量阅读技能与依赖资产 → 跑检测脚本实证（干净模板 + 真实仓库 `output/prototype/` + 构造 design-set 工程）→ 边缘交叉（跨阶段依赖、孤儿脚本、遗留引用、真实产物状态）。
> 日期：2026-08-23。结论先行：1 个 P0 阻断死点（design-set 被确认门永久卡死），3 个 P1，6 个 P2。

## 评级摘要

| 级 | 编号 | 问题 | 是否实证 |
|---|---|---|---|
| P0 | D1 | design-set 项目被 `design-confirmation.py confirm` 永久卡死 | 是（end-to-end 复现） |
| P1 | D2 | SKILL 步骤9 vs 步骤10 验证指令自相矛盾 | 是（读代码） |
| P1 | D3 | consistency-check `_normalize_name` 正则 bug `s+`→`\s+`（误报 missing） | 是（读代码） |
| P1 | D4 | 真实 `output/prototype/` 是旧静态 HTML 样本堆，SKILL 迁移分支覆盖不到 | 是（ls + source-check 8 FAIL） |
| P2 | D5 | `prototype-writing.md` 内部视觉规格矛盾（默认主题、顶栏高度） | 是（读代码） |
| P2 | D6 | SKILL 步骤11 未交代退出码语义；exit 2 无恢复路径 | 是（读代码 + 实证回退） |
| P2 | D7 | `prototype-structure.py` 是孤儿脚本（SKILL 未引用） | 是（grep） |
| P2 | D8 | `prototype-p0` 遗留死引用 | 是（读代码） |
| P2 | D9 | consistency-check L233 闸门扫描范围与 `_scan` 不一致 | 是（读代码） |
| P2 | D10 | README 首屏检查较脆 + 步骤9 "三个本地选项"措辞 | 是（读代码） |

---

## P0

### D1 — design-set 项目被确认门永久卡死（实证）

**事实**

- SKILL.md 明确声明 design-set 格式（无 `output/design/design.md`，改用 `设计集清单.json` + 模块设计文件）受支持（L69：「design-set 格式项目（无 output/design/design.md）由脚本直接支持」）。
- 但「确认检查」块（L24-30）强制先跑 `design-confirmation.py`，且规定「仅在用户明确确认后，由你运行 `confirm` 记录哈希，再继续」——即 `confirm` 必须先成功写入哈希，原型生成才能开始。
- `design-confirmation.py` 的 `cmd_confirm`（L124-145）只对 `output/design/design.md`（常量 `DESIGN_ARTIFACT`，L38/L127）计算 SHA-256。design-set 没有这个文件。

**实证（构造 design-set 工程，无 design.md）**

```
design-confirmation.py confirm  →  exit=1, stderr: {"ok":false,"error":"design.md 不存在: .../output/design/design.md"}
design-confirmation.py check    →  exit=3, {"confirmed":false,"reason":"no_confirmation_record"}  （先于 design.md 检查返回）
```

`check` 在「无确认记录」时返回 3（先于 design.md 存在性检查），所以 SKILL 确认检查会走到「停，询问用户确认」；用户确认后，agent 跑 `confirm` → 因无 design.md 可哈希 → **exit=1，哈希永远写不进** → 确认门永远不过 → 原型生成死锁。

**后果**：design-set 项目无法进入原型生成，与 SKILL L69 自相矛盾。这是技能级阻断死点。

**修复（最短路径）**：`design-confirmation.py` 的 `cmd_confirm` / `cmd_check` 增加 design-set 分支——当 `设计集清单.json` 存在而 `design.md` 不存在时，确认对象改为「清单 + 各模块设计文件」的联合内容哈希（复用 consistency-check 已有的 `_load_design_set_expected` / `_extract_design_set_names` 思路），写入同样的 `.workflow/confirmations/design.json`，`artifact` 字段记为 `output/design/设计集清单.json`。SKILL 确认检查相应说明 design-set 走清单哈希。

---

## P1

### D2 — SKILL 步骤9 vs 步骤10 验证指令自相矛盾

- L51（步骤9）：「（选项只调用 package.json 标准 scripts，读文件确认映射即可）；**不做 dev 浏览器抽查、不逐路由验证**」。
- L53（步骤10）：「构建预览……**逐一打开默认页与每个注册路由**，均不得白屏」。

两条相邻步骤对「是否逐路由验证」给出相反指令，完成标准（completion criterion）自相矛盾，agent 无法判断 done/not-done（正是文档写作里最该避免的歧义）。

**修复**：明确两步对象不同——步骤9 = 「只读文件核对 BAT 菜单与 package scripts 映射，不启动浏览器」；步骤10 = 「构建预览后逐路由开浏览器渲染验证」。把步骤9 的「不逐路由验证」改为「此步不启动浏览器，仅核对 BAT→package.json 映射」，消除对立措辞。

### D3 — consistency-check `_normalize_name` 正则 bug（误报 missing）

`prototype-consistency-check.py` L144-147：

```python
def _normalize_name(value):
    text = re.sub(r"[（(][^）)]*[）)]", "", str(value or ""))
    return re.sub(r"s+", "", text)   # BUG：s+ 无反斜杠，匹配字面 "s+"，永不匹配空白
```

意图是去空白，但 `r"s+"` 是字面两字符，空白不被归一。后果：design 名与扫描文本空格数不一致（如 design「测试 名称」vs 扫描「测试名称」「测试 名称」）时，`_compare` 判为 missing → **假阳性不一致** → 原型被错误判失败。

**修复**：`re.sub(r"\s+", "", text)`（或更稳妥地 `.strip()` + 折叠空白）。补一个回归用例：design 页面名带空格、扫描文本无空格（或反之），断言不误报 missing。

### D4 — 真实 `output/prototype/` 是旧静态 HTML 样本堆，SKILL 迁移分支覆盖不到

仓库根 `output/prototype/` 实测内容：`sample-antd.html` / `sample-arco-*.html` / `lib/` / `_arco_src/` / `_parse_spec.py` / `_shots/` —— **无 `src/`、无 `package.json`、无 `原型工具.bat`**。对其跑 `prototype-source-check.py`：**8 项 FAIL**（package.json / package-lock / vite.config / src / main.jsx / routes / 原型工具.bat / README 均 FAIL）。

SKILL 步骤4 迁移分支只覆盖「旧静态原型（HTML + compiled.js 形态）」，不覆盖「多 sample HTML + lib + _arco_src 杂项」。agent 遇到此真实目录时落入模糊区：既非干净 Vite 工程，也不精确匹配「HTML+compiled.js」特征词。

**修复**：步骤4 判定改为「`output/prototype/` 已存在且非标准 Vite 工程（缺 `src/` 或 `package.json`）→ 停，报告『检测到非标准原型目录』，让用户决定迁移/清空」，不再依赖 `compiled.js` 特征词。

---

## P2

### D5 — `prototype-writing.md` 内部视觉规格矛盾

- L102「模板当前使用 Claude 主题」vs L146「已收录品牌：tabler（…**当前默认**）、claude（…）」——默认主题自相矛盾（SKILL 与工作记忆定稿 claude 为默认）。
- L209「顶栏通栏（Header，fixed 顶部，高 **56px**）」vs L171「顶栏高 Header **64px**」——顶栏高度两值；`prototype-shell.md` 与模板实现 `App.jsx` 均用 56px，64px 是过时值。

**修复**：默认主题统一为 claude；顶栏高度统一 56px（与 shell 模板一致），删除 64px 表述。

### D6 — SKILL 步骤11 未交代退出码语义；exit 2 无恢复路径

SKILL 只说「确定性检查或浏览器检查失败时先修复并重新验证」，未区分 `source-check`(0/1) 与 `consistency-check`(0/1/2)。`consistency-check` 的 exit 2（「design.md 与 设计集清单.json 均不存在」或「Design 索引解析失败」）中，「Design 索引解析失败」是 Design 阶段产物（`design-index.json`），Prototype 阶段无法重生成，SKILL 无恢复指引 → agent 遇 corrupt index 无措。

注：实证显示 `design-index.json` 缺失时 consistency-check **优雅回退**到 design.md 派生期望（`from_file=false`，exit 正常），所以 exit 2 仅在索引文件存在但损坏时触发。

**修复**：SKILL 补一段退出码说明：「source-check 1 = 工程不合规需修；consistency 1 = 缺页面/字段需补，2 = design 索引损坏需回 Design 阶段重跑索引」。

### D7 — `prototype-structure.py` 是孤儿脚本

grep 确认：SKILL.md 未引用 `prototype-structure.py`（plan 文档 L542 明确「Skill 中不存在 prototype-structure.py」）；它仅被 `test-prototype-source-check.py` 与已被 PRD 删除的流程引用。SKILL 步骤11 只跑 source/consistency。测试在维护一个无人从技能调用的脚本。

**修复**：二选一——要么在 SKILL 步骤11 显式引用（若它仍有价值，如生成原型结构快照供 PRD/对齐读取），要么从测试与仓库移除。倾向保留为独立工具，但在 SKILL 或 USAGE 显式说明其用途与非必跑地位。

### D8 — `prototype-p0` 遗留死引用

`prototype-source-check.py` L7（「src 不依赖 prototype-p0 等兄弟目录」）、`prototype-consistency-check.py` L62 / `_EXCLUDED_DIRS`。Vite 收口后架构已无 `prototype-p0` 兄弟目录，属 cargo-cult 引用。低危，但属沉积。

**修复**：若确认无 `prototype-p0` 概念，移除这些专用检查/排除；或加注释说明其为历史迁移遗留、保留以防回归。

### D9 — consistency-check L233 闸门扫描范围与 `_scan` 不一致

L233 `rglob("*.html")` 未排除 `dist/node_modules/prototype-p0`，而真正扫描的 `_scan`（L113）排除它们。后果：半构建/损坏项目（src 被删但 dist 在）闸门仍过、`_scan` 扫不到源码 → 批量假 missing；且闸门意图（源码页存在）未被真正检查。

**修复**：L233 也加 `_EXCLUDED_DIRS` 过滤。

### D10 — README 首屏检查较脆 + 步骤9 措辞

- 低危：`prototype-source-check.py` L132-138 的 README 首屏检查，只要首屏出现「npm run」「打开 PowerShell」「在 PowerShell 中执行」任一即 FAIL（即便上下文合理）；模板当前通过。
- SKILL 步骤9 称 BAT「三个本地选项」，但 BAT 选项5（修复依赖并重新构建）亦属本地，措辞轻微不准。

---

## 通过项（实证未崩，记录以证不是全坏）

- `prototype-source-check.py` 对干净模板 `templates/prototype-vite/`：15 项全 PASS。
- `prototype-consistency-check.py` 对 design-set 工程：exit 0，页面匹配正常（走 `设计集清单.json`）。
- `design-index.json` 缺失时 consistency-check 优雅回退（from_file=false），不崩。
- BAT 菜单 → `package.json` scripts 映射一致（`test_template_has_single_menu_bat` 覆盖：dev/build/preview 均在 BAT 且 BAT 不硬编码项目名）。
- 模板 README 首屏通过（「双击 原型工具.bat」+ 无 npm/PowerShell 步骤）。

## 修复优先级建议

1. **先修 D1（P0）**：design-confirmation.py 加 design-set 分支，否则 design-set 原型生成整条链死锁。
2. **再修 D2/D3/D4（P1）**：指令矛盾、正则 bug、真实目录迁移——三者都让 agent 在真实项目里卡住或误判。
3. **D5–D10（P2）**：一致性/沉积清理，可合并在一次文档与脚本小修里收口。
