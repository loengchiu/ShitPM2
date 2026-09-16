# 本次迭代改动 Review（T-0 ~ T-9 落地后）

审查时间：2026-09-16
审查对象：`git diff` 15 个改动文件（405 增 / 45 删）+ 新增 `references/design-business-closure.md`（127 行）
审查方式：全量读 diff + 端到端实证，不抽查、不依赖执行报告的自述

审查结论：**P0 × 0，P1 × 2，P2 × 4，待决 × 1**

**2026-09-16 更新：7 项已全量修复并逐项实证，待决项按建议处理。回归验证：pytest 86 passed、14 个直跑脚本全 OK、设备租赁真实 Design 复验无回退。修复记录见文末「修复记录」。**

---

## P1-1 `_normalize_label` 分隔符由必选改可选，静默改坏实体名

**位置**：`scripts/python/design-index.py:161`

```python
# 旧
value = re.sub(r"^[一二三四五六七八九十0-9]+[、.．)]\s*", "", value)
# 新
value = re.sub(r"^[一二三四五六七八九十0-9]+(?:[.．][0-9]+)*[、.．)]?\s*", "", value)
```

改动把尾部分隔符 `[、.．)]` 从**必选**变成**可选**，并把「多级编号」的支持与「单级分隔符」耦合在同一条正则里。结果：任何以数字开头、后面不跟分隔符的标题都会被剥掉数字前缀。

**端到端实证**（Design 含页面清单 + `### 页面：<名称>` 正式标题）：

| 输入页面名 | 提取出的 `page["name"]` |
|---|---|
| 订单列表 | `订单列表` ✓ |
| 4.2 订单列表 | `订单列表` ✓（本轮目标） |
| 3D 模型展示 | `D 模型展示` ✗ |
| 2024 年度汇总 | `年度汇总` ✗ |
| 2C 端页面 | `C 端页面` ✗ |
| 5G 设备台账 | `G 设备台账` ✗ |

旧规则下这四个输入全部安全（分隔符必选，`5G` 不匹配）。**这是本轮新引入的回归。**

**为什么危险**：清单侧和标题侧用的是同一个 `_normalize_label`，剥离是**对称**的，所以本轮新增的配对检查**不报错**——`page_summary_missing_detail` / `page_detail_missing_summary` 都不触发。但 `page["name"]` 已经被改成错的，下游 `prd-consistency-check` 拿 `D 模型展示` 去和 PRD 里的 `3D 模型展示` 对账，会同时产生 **missing + hallucinated 双向假信号**，且链路内无任何环节暴露。

这与本轮要消灭的假绿是同一类问题，只是换了个入口。

**建议修法**：单级保留必选分隔符，只对多级放开。

```python
value = re.sub(r"^(?:[0-9]+(?:[.．][0-9]+)+\s*|[一二三四五六七八九十0-9]+[、.．)]\s*)", "", value)
```

验证：`4.2 订单列表` ✓、`1.1.1 X` ✓、`三、X` ✓、`5G 设备台账` 保留 ✓、`2024 年度汇总` 保留 ✓。

**测试缺口**：新增的 6 个测试全部是「要支持的形态」，`test-design-index.py` 里没有任何一个「不该被剥」的对照组。这是回归漏网的直接原因。建议补：`3D`、`2024`、`2C` 三个反例断言 `page["name"]` 原样保留。

---

## P1-2 `design-business-closure.md` 未定义「承载面」，却被指向为唯一权威源

**位置**：`references/design-business-closure.md`

文件里「承载面」出现 4 次（:20、:113、:115、:119），**没有一处给出定义**：

- :115「三者的共同前提：都使用本文件的**关系实例、适用、排除、risk、decision、承载面**定义，不各自解释。」
- :119「fix 把每个问题还原成业务约束，再枚举该约束的全部承载面」

而三个文件把本文件指为承载面的权威来源：

- `skills/spm-fix/SKILL.md` 步骤 5：「定义以 `$BUNDLE/references/design-business-closure.md` 为唯一权威来源」
- `contracts/fix-propagation-rules.md:62` 给出了唯一的具体枚举（系统规则、跨模块契约、页面、字段、操作、状态机、导出、验收和未决事项），**但它不是被指向的那个权威源**

**影响**：Fix 的「业务约束 × 承载面 × 对象」三维影响表，第二维在被指向的权威文件里没有定义。执行者按 SKILL 指引去权威源查 → 查不到 → 退化为各人自由解释，三维表实际退成二维。这正好是本轮要解决的「影响面枚举不全」的失效点。

**建议**：在 `design-business-closure.md` §3 增补 §3.4「承载面」，把 `fix-propagation-rules.md:62` 的那份枚举上移为权威定义，并说明「承载面 ≠ 文件」，一个承载面可能跨文件、一个文件可能含多个承载面。

---

## P2-1 `enabled: False` 分支近乎不可达，修复效果被高估

**位置**：`scripts/python/prd-consistency-check.py:1836`

改动本身方向正确（零预期时不得报告「已启用」）。但可达性分析：

`_indexed_expected_entities`（:1786）把 pages / blocks / fields / operations 全部计入 `expected` ⇒ `expected` 为空 ⟺ 四类实体全空 ⟺ 通常伴随 `unsupported_format` ⇒ **先被上一个分支（:1826）拦截返回**，永远到不了 `if not expected`。

唯一可达路径：pages 非空但所有 `page["name"]` 为空（被 :1805 的 `if item.get("name")` 过滤掉）——极窄。

更要紧的是：**本轮真正要消的假绿场景（pages=0 而 fields/operations 非空）根本不经过这个分支**，因为那时 `expected` 非空、走完整比对。那个场景靠的是 `load_verified_index` 抛 `page_extraction_empty` 拦住的。

**结论**：改动无害但近乎无效；执行报告把它列为「消假绿的一环」会夸大效果。建议在报告或代码注释里写明「本分支只防零实体误报 enabled，页面层空转由 `load_verified_index` 拦截」。

---

## P2-2 语法矛盾：「同时满足以下之一」

**位置**：`references/design-business-closure.md:87`

> 同时满足以下之一，即判定该关系实例**适用**

「同时」与「之一」冲突，应为「满足以下任一」。这是会被下游逐字执行的判定规则，措辞矛盾会直接产生两种相反的执行。

---

## P2-3 已落盘旧索引的项目，`page_extraction_empty` 的诊断原因被掩盖

**位置**：`scripts/python/design-index.py:1163` vs `validate_index:1091`

`validate_index` 会重新编译 `expected`。项目里已有旧落盘索引时：

- 新增的错误码让 `stored != expected` → `stored_core != expected_core` → 返回 `False, expected, "索引内容与 Design 文件的确定性编译结果不一致"`
- `load_verified_index` 在 `if not valid:` 分支直接 `return None, reason, True` → **走不到** `if _has_page_extraction_empty(expected)`

结果：不假绿（确实报错了），但用户看到的原因是「内容不一致」，而不是「页面提取为空」，诊断价值丢失，修起来会往错误方向查。

**建议**：把 `page_extraction_empty` 的判断提到 `if not valid:` 之前，或在 `validate_index` 里就把它识别为独立 reason（比照 `invalid_type` 的写法）。

---

## P2-4 「候选实例数」要求了，但没定义候选集怎么产生

`contracts/design-review-checklist.md` 新增要求报告必须给出「候选/实例数」，`spm-design-review/SKILL.md` 步骤 8 同样要求。但 `design-business-closure.md` 只定义了「关系实例是什么」，没有定义**候选实例从哪里枚举出来**（页面清单？状态机实体？字段表？字典？）。

结果：不同审查者、不同轮次的「覆盖率」数字不可比，也无法用数字判断覆盖是否闭合——而新增的覆盖要求恰恰把「覆盖闭合」定为通过条件。

**建议**：在 §3 补一段候选来源清单（至少覆盖：页面与区块清单、状态机实体、字段与操作表、角色清单、字典条目、导出物定义），并说明「候选集不全」本身要记为方法缺口。

---

## P2-5 死码未清理（既有问题，本轮继续绕过）

`design-index.py` 的 `_FATAL_ERROR_CODES`（:1122）与 `_is_fatal_index_error`（:1140）仍是零调用方的死码；本轮新增的致命判定继续写成内联分支（`_has_page_extraction_empty`），没有复用也没有清理这对常量。

不是本轮引入的，但方向相反：每加一类致命错误就多一处内联，`_FATAL_ERROR_CODES` 越来越像装饰。建议单独一轮要么接上、要么删掉，不要留第三种形态。

---

## 待决 × 1

`contracts/design-review-checklist.md` 新增的「最小覆盖摘要」要求报告输出 7 类计数。这与 `AGENTS.md` §1#8「对最终产物无影响的工具应删除」、以及 ShitPM「Review 是第二意见不是门禁」的定位存在张力：**计数摘要是过程指标，不是产品事实**。若执行者为了满足摘要而机械填数，会变成新形式的回执。需要你判断：覆盖摘要是写进契约强制要求，还是降为「建议包含」。

---

## 通过项（已实证，非抽查）

| 项 | 证据 |
|---|---|
| `page_extraction_empty` 结构判据正确 | 与 `unsupported_format` 互斥；`BLOCK_ONLY_NO_PAGE_DESIGN` 命中，`LEGACY_FLAT_DESIGN`（全 0）不误伤 |
| `_page_compare_key` 只作用于比较点 | `page["name"]` 保留尾括注，测试已锁定「实体名不得被改」 |
| 新增测试有真断言 | 无恒 PASS；双消费者测试用 `assertNotEqual(rc,0)` + `assertIn("page_extraction_empty")` 双条件，规避了 `prototype-*-check` 缺参 exit=2 静默全 0 的坑 |
| 资源完整性 | `test-resource-integrity.py` exit 0；marker 恰好一对；`design-business-closure.md` 127 行有 `## 目录` |
| manifest 装载 | `design-business-closure` 挂入 design pack，`stage: design`，source 路径正确 |
| 规范层编号无冲突 | 检查项 31/32/33 无重号；`spm-fix` 步骤 5→9 重编号无悬空引用；`design-writing.md` 自检项 6→12 重排后外部无按号引用 |
| 引用一致性 | `spm-fix/SKILL.md`「第四节步骤 0」与 `fix-propagation-rules.md` 第四节（:54）实际位置一致 |
| Review 步骤改造对症 | 步骤 1 移除历史读取、步骤 7 冻结后才回归核对，直接针对「先入为主把没复发当成通过」 |

---

## 建议处理顺序

1. 修 P1-1（正则 + 补三个反例测试）—— 静默改坏实体名，影响下游对账正确性
2. 修 P1-2（补 §3.4 承载面定义）—— 否则 Fix 的三维影响表第二维悬空
3. P2-1 改成注释/报告口径修正（不改代码行为）
4. P2-2 / P2-3 / P2-4 可并入下一轮
5. 待决项由你定

---

## 修复记录（2026-09-16 全量执行）

| 项 | 修复内容 | 实证 |
|---|---|---|
| P1-1 | `design-index.py:161` 正则改为「单级保留必选分隔符、仅对多级放开」：`^(?:[0-9]+(?:[.．][0-9]+)+\s*\|[一二三四五六七八九十0-9]+[、.．)]\s*)` | 正例 `4.2 页面：订单列表`→`页面：订单列表`、`1.1.1 页面：X`、`三、`、`十、`、`1.` 全部正常；反例 `3D 模型展示`／`5G 设备台账`／`2C 端页面`／`2024 年度汇总`／`4A 景区导览` 全部原样保留 |
| P1-1 测试 | 新增 `test_numeric_prefix_without_separator_is_not_stripped`（5 个反例 + 3 个单级正例）与 `test_page_name_with_numeric_prefix_survives_compile`（端到端夹具 `NUMERIC_PREFIX_PAGE_DESIGN`，断言 `page["name"] == "3D 模型展示"` 且配对错误不出现） | `test-design-index.py` 25 个测试全 OK（原 23 + 新增 2） |
| P1-2 | 新增 `design-business-closure.md` §3.4「承载面」：9 类清单 +「承载面不等于文件」枚举要点；`fix-propagation-rules.md:62` 去掉本地枚举改为指向 3.4，消除两处漂移 | 权威源已有定义，唯一定义处唯一 |
| P2-1 | `prd-consistency-check.py` 补可达性注释；**上一轮追加的两个 `design-index-unavailable` 分支经复审判定为死代码并已回退**（见文末「第二轮复审」） | 名称全空 → `enabled=False, expected_count=0`；有名称 → `enabled=True, expected_count=1`；sabotage 证明该分支无测试可守护 |
| P2-2 | §4.1「同时满足以下之一」→「满足以下任一条」 | — |
| P2-3 | `load_verified_index` stored 路径把 `_has_page_extraction_empty` 提到 `if not valid:` 之前 | 旧落盘索引 + 页面空集 → 返回真实原因 `page_extraction_empty`（原为「内容不一致」）；旧格式降级仍 `error=None` 且返回索引；非致命错误仍可用 |
| P2-4 | 新增 §3.5「候选实例的来源」：7 类来源 +「候选集不全记为方法缺口，不得用实例数充抵」 | — |
| P2-5 | 删除死码 `_FATAL_ERROR_CODES` 与 `_is_fatal_index_error`（已确认零调用方） | grep 全仓库无残留引用 |
| 待决 | 覆盖摘要从「必须给出 7 类计数」改为「用于说明覆盖如何闭合，不得为凑齐字段机械填数，也不得用计数充抵闭合判断」，并指向 §3.5 候选来源 | `design-review-checklist.md` 与 `spm-design-review/SKILL.md` 步骤 8 同步 |

### 回归验证

- `C:/Python314/python.exe -m pytest -q`：**86 passed**（修复前 84，+2 新增测试，无失败）
- 14 个 `test-*.py` 直跑：全部 OK/PASS
- `test-resource-integrity.py`：exit 0（新增内容未破坏路径/链接/marker/目录/消费者引用）
- 设备租赁真实 Design 复验：`pages=4 / blocks=14 / fields=89 / operations=7`，`errors=27`（`missing_attribute 14 / combined_field_name 9 / block_without_items 4`），**与修复前一致，正则改动未引入回退**

---

## 第二轮复审（2026-09-16，全量）

复审方式：全量读 diff + sabotage 反证（把修复逐条还原成缺陷，看测试是否转红）+ 引用一致性扫描。

复审结论：**P1 × 3（含 1 项自我纠错），全部已处理。**

### R-1（P1，自我纠错）P2-1 追加的分支是死代码，已回退

上一轮报告称"报告漏列的连带隐患"是 `indexed_active=False` 时落到 legacy 分支谎报 `legacy-empty`，并加了两个 `elif design_data is None` 分支标注 `design-index-unavailable`。

复审判定该分支**不可达**：

- `design_index` 来自 `_load_verified_design_index` → `load_verified_index`
- `load_verified_index` 返回 `None` 时**必然**带 `error`（所有返回 None 的分支都带原因）
- `prd-consistency-check.py:2145` 判 `if design_index_error:` → 直接 `sys.exit(1)`
- 且 `page_extraction_empty` 正走这条路 → 在 main 里永远到不了 `_compare_indexed_structure`

所以 `enabled=False` 只剩"pages 存在但 name 全空"这一条窄路径，而该路径下原代码的 `if design_data else []` 本来就兜住了 None，不会崩，只是标注不准。

按 `AGENTS.md`「不为不可能场景写错误处理」，两个分支已回退，只保留注释说明可达性边界。上一轮把它写成"隐患"属定级过高。

### R-2（P1，新发现）两处修复都没有测试守护

用 sabotage 反证：把修复逐条还原成缺陷后跑 pytest，**两次都是 86 passed 全绿**。

- 还原 P2-3 顺序（`_has_page_extraction_empty` 移回 `if not valid` 之后）→ 全绿 = 无测试守护
- 删除 P2-1 的两个分支 → 全绿 = 无测试守护（佐证 R-1：为不可达代码也写不出有效测试）

其中 P2-3 是**真实可达**的修复（已有旧落盘索引 + 页面标题被改坏 → 真实项目会命中），必须补守护。已新增两个测试到 `test-design-index.py`：

- `test_stored_index_page_extraction_empty_reports_real_reason`：monkeypatch `validate_index` 返回"内容不一致"，断言真实原因 `page_extraction_empty` 仍被报出
- `test_stored_index_unsupported_format_still_downgrades`：同一入口下旧格式仍降级可用，不被关键空集误伤

**sabotage 复验**：再次还原 P2-3 顺序 → 转红（`AssertionError: 'page_extraction_empty' not found in '索引内容与 Design 文件的确定性编译结果不一致'`），恢复后绿。测试有效。

### R-3（P1，新引入）"六类高影响关系"三处独立枚举，指向的文件没有该划分

本轮新增的三处文字都写"按 `design-business-closure.md` 的关系实例定义回读**六类**高影响关系"：

- `references/design-quality-rubric.md`：短名枚举（权限/动作条件/状态结果/规则来源/异常恢复/输出去向）
- `skills/spm-design/SKILL.md`：同一组短名枚举
- `references/design-writing.md`：同内容的 ①–⑥ 详细展开

但 `design-business-closure.md` §3.1 定义的是**九个维度**，全文没有"六类"这个划分。引用与被引用不匹配，且三处独立枚举同一清单——正是 P1-2 要消除的漂移形态，本轮自己又造了一个。

已修：在 `design-business-closure.md` 新增 **§3.6 核心闭环最小回读集（Design fast）**，把六类清单连同"其余三维在 fast 阶段只做横切、不做逐实例闭合"的成本边界一并定义；三处改为引用 §3.6，删除本地枚举；`design-review-checklist.md` 的术语列表补入"核心闭环最小回读集"。

### R-4（P2，已修）删死码时一并删掉了语义注释

`_FATAL_ERROR_CODES` 那段注释解释了 `unsupported_format`（旧格式，属迁移范围，继续降级）与 `invalid_type`（清单写错，必须暴露）的区别，删除死码时被一并带走，新增的 `_has_page_extraction_empty` 没有等价说明。

已补：在 `_has_page_extraction_empty` 上方写明它与 `unsupported_format` 的区分——前者是实体齐了只有页面层缺失（设计缺陷，必须报错），后者是实体全空的旧格式（既定迁移范围，继续降级）。

### 通过项（第二轮实证）

| 项 | 证据 |
|---|---|
| P1-1 修复有效且被守护 | sabotage 注入坏正则 → 2 个新测试转红（`['D 模型展示']` vs `['3D 模型展示']`）；恢复后绿 |
| 承载面定义唯一 | 全仓库仅 `design-business-closure.md` §3.4 定义，另三处均改为指向、无重复枚举 |
| 新文件结构合规 | 178 行 + `## 目录` + marker 恰好一对；`test-resource-integrity.py` exit 0 |
| 无回归 | pytest **88 passed**（86 + 新增 2） |
| 设备租赁真实复验 | `pages=4 / blocks=14 / fields=89 / operations=7`，`errors=27`（`missing_attribute 14 / combined_field_name 9 / block_without_items 4`），逐项与修复前一致 |
| 死码引用残留 | 仅存于 `docs/plans`、`docs/reports`、`.workbuddy/memory` 等历史记录，非运行时契约，不需清理 |
