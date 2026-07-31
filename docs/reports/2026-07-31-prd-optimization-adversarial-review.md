# PRD 优化迭代 · 全量对抗性审查报告

> 日期：2026-07-31  
> 审查者：WorkBuddy（全量对抗性审查，非仅审未提交代码）  
> 审查对象：`D:\work\ShitPM` 当前工作树（含本轮 PRD 优化迭代的全部改动 + 全仓既有脚本/规则/Skill 交叉一致性）  
> 方法：读 diff 与全文脚本、跑全量回归与三个 PRD 专项测试、用新模板结构构造"干净/带毒"对抗样本端到端跑两个脚本、核查已知 bug 与孤儿脚本。

## 结论先行

迭代**方向正确、边界守住了**（未新增检查器/门禁/回执，上下文装载通过，三个 PRD 专项测试与全量回归全绿）。但发现 **1 个 P1 确定性误报**，会导致"严格按新模板写出来的 PRD"被一致性脚本判为 `deterministic_conflict`、退出码 1、**阻断交付**。该问题被现有测试掩盖（测试夹具用的是旧七列格式，从未覆盖新模板的字段表写法）。

- **P0：无**
- **P1：1 项（主）+ 1 项强相关**
- **P2：4 项（整洁/健壮性）**

任何 P1 未修复前，不能宣称"正常新结构样本退出码为 0"。

> **2026-07-31 订正**：下述 P1 已修复并实测验证，本报告发布时的"未修复"表述有误。
> `extract_prd_fields` 已加入"类型/取值"列枚举回退解析（`prd-consistency-check.py:206-212`），
> `compare_fields` 对整列缺失的"必填"降级处理（同文件 973 行附近），
> 测试 `test-prd-consistency-semantics.py` 已补新模板内联枚举夹具。
> 复跑对抗探针：CLEAN 新结构 `exit=0`、DIRTY 仍 `exit=1`（4 字段 + 1 页面 + 1 状态确定性冲突），
> 四套测试（文风、一致性、全量回归、上下文装载）全绿。P2 四项仍未处理。

## 审查范围与方法

| 动作 | 结果 |
|---|---|
| 全量回归 `test-shitpm-regression.py` | 通过（3 用例） |
| `test-prd-style-lint.py` | 通过（九类问题、级别、退出码） |
| `test-prd-consistency-semantics.py` | 通过（新结构页面映射、分散字段、冲突、遗漏、语义判断、致命错误） |
| `test-context-loading.py` | 通过（manifest、marker、来源、去重、边界） |
| 对抗探针：新模板 CLEAN 样本跑两个脚本 | **consistency 退出码 1（应为 0）← 发现 P1** |
| 对抗探针：新模板 DIRTY 样本（幻觉页面/字段/枚举冲突/标签式） | consistency 退出码 1 且正确归类；style 退出码 1（STYLE001 标签式）|
| 已知 orchestrator bug 复查 | `repair_fingerprints`/`design-repair:`/`review_findings` 当前代码中已不存在（已修复/代码已变）|
| 孤儿脚本复查 | `download-prototype-libs.py`、`context-run.py` 仍为 legacy/孤儿 |
| 范围膨胀核查 | 仅改动计划内 16 个文件 + 新增 5 个 `docs/plans/*` 方案文档；**未新增任何脚本/检查器/门禁/回执** |

## P1：新模板字段表与一致性脚本枚举提取自相矛盾（阻断交付）

### 现象（可复现）
用新模板结构写一份"干净" PRD（页面映射、字段、状态全部如实承接 Design），跑 `prd-consistency-check.py`：

```
consistency exit=1 reason=deterministic_conflict
  DC field_attrs=[{
    "name":"状态",
    "mismatch_kinds":["type","enum"],
    "prd_enum_values":[],            ← PRD 侧枚举值解析为空
    "design_enum_values":["在场","已离场"],
    "enum_missing":["在场","已离场"]  ← 误报"枚举缺失"
  }]
```

`prd_enum_values=[]` 而 Design 侧 `['在场','已离场']` → 判为 `enum` 确定性冲突 → 退出码 1。

### 根因（已定位）
- 新模板字段表把枚举值**内联在"类型/取值"列**：`templates/prd.md:100` → `| 字段 | 类型/取值 | 来源或约束 | 使用说明 |`，例如 `| 状态 | 枚举：在场、已离场 | … |`。
- `prd-consistency-check.py` 的 `extract_prd_fields` 只在**独立的"取值约束/约束/规则/枚举"列或说明列**解析枚举（`_parse_enum_values(constraint_text)` / `_parse_enum_values(description)`），**不解析"类型/取值"列里的内联枚举**。
- 结果：模板写法下 `prd_enum_values` 永远为空 → 每个枚举字段都误报 `enum_missing` → 确定性冲突 → 阻断交付。

### 为什么现有测试没发现
`test-prd-consistency-semantics.py` 的 `NEW_STRUCTURE_PRD` 与 `PRD_BASE` 字段表用的是**旧七列格式** `| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |`，枚举值放在独立的"取值约束"列 → 能被正确解析 → 测试通过。新模板的"类型/取值"合并列写法**从未被任何测试覆盖**，于是给了"全绿"的假象。

### 建议修复（最小、确定性、不新增语义判断）
在 `extract_prd_fields` 的 `_extract_from_tables` 内，计算 `enum_values` 时增加"从类型列回退解析"：

```python
enum_values = []
if "枚举" in field_type:
    # 兼容新模板把枚举值内联在"类型/取值"列：枚举：a、b 或 枚举(a、b)
    m = re.search(r'枚举[：:（(]\s*([^）)\n]+)', field_type)
    if m:
        enum_values = [v.strip(" `（）()") for v in re.split(r'[,，、;；|]', m.group(1)) if v.strip()]
if not enum_values:
    enum_values = _parse_enum_values(constraint_text)
if not enum_values:
    enum_values = _parse_enum_values(description)
```

并补一条测试：用新模板"类型/取值"合并列写法构造 enum 字段，断言 `exit_reason == "ok"` 且 `prd_enum_values` 非空。

### 强相关次级问题（同一根因，逻辑确定）
新模板字段表**没有强制"必填"列**。当写作者严格照模板（只写 `类型/取值|来源或约束|使用说明`）时，`extract_prd_fields` 的 `required_idx` 为 `None` → Design 中标 `必填=是` 的字段被判 `required_missing` → 同样计入确定性冲突。写作规则要求表达必填，但模板示例未展示该列，形成"照模板写→误报"的陷阱。建议：要么模板字段表示例补齐"必填"列，要么脚本对"无必填列"整体降级为 `possible_omission`（语义判断）而非确定性冲突。

## P2：健壮性与整洁项

1. **STYLE003 表格主导检测锚定标题关键词**：`check_table_dominance` 仅在标题含 `业务闭环|业务模块|业务阶段|功能需求` 时启用扫描。新模板容器标题 `## 4. 业务闭环模块` 含"业务闭环"，故跟随模板时可用；但若未来重命名该容器标题，整段业务模块的表格主导检测会**静默失效**。建议改为"对整个 `## 4.` 业务模块区统一扫描"，不依赖关键词。
2. **页面提取依赖"页面与终端映射"标题**：`extract_prd_pages` 优先读该标题下的映射表；模板确实使用该标题，当前一致。但属于"脚本关键词 ↔ 模板标题"硬耦合，重命名即失配。建议与模板约定一处单一事实源并在测试中标定。
3. **`extract_prd_modules` 在新结构下恒为空**：该函数只从"详细需求说明"章节提取模块，而新结构已移除该章节 → 模块对比永远 inert（`semantic_only`）。无害，但属于死路径，建议删除以减复杂度（符合 AGENTS.md "删除证明流程/死代码"原则）。
4. **孤儿/legacy 脚本**：`download-prototype-libs.py`（仅 `references/prototype-writing.md` 提及，无 SKILL/生产脚本调用）、`context-run.py`（仅被 `test-resource-integrity.py` 引用，生产路径等于死代码）。按本仓库 AGENTS.md 的"删除死代码"原则，应二选一：接入生产或在确认无消费者后删除，不要继续保留无用的"备用"脚本。

## 已验证通过（正面项，避免误判）

- 迭代**未越界**：无新增检查器/门禁/回执/覆盖率 JSON；改动严格落在计划 16 文件内。
- 上下文装载（`context-pack` + manifest）对 PRD `writing`/`module` 均正常；`--mode full --pass writing --dry-run` 参数真实存在且无害。
- 带毒样本（幻觉页面/字段、枚举冲突、标签式正文）均被正确拦截并正确分级：`deterministic_conflict` 退出 1，文风 `STYLE001` 退出 1。
- 字段分散在多个业务模块、业务闭环名称与 Design 菜单名不同——均能被正确合并识别，不误报。
- 设计索引缺失时优雅降级为 legacy 路径，不阻塞。
- 之前 memory 记录的 `design-orchestrator.py` 两个已知 bug（`repair_fingerprints` 不对称、`review_findings` 读错字段）**当前代码中已不存在**，疑似已修复。

## 遗留 / 需用户决策

- **P1 必须修**：否则真实项目按新模板生成 PRD 后，一致性脚本必然误报枚举（及必填）冲突，无法交付。建议先修 `extract_prd_fields` 枚举回退解析 + 补测试，再决定是否同步要求模板补"必填"列。
- 真实"智慧停车区"候选 PRD 尚未在 `.tmp` 生成（方案要求保护原文件），故本次未在真实复杂样本上跑端到端；P1 修复后，建议按方案第六层在 `.tmp` 生成候选并实跑两个脚本做最终验收。
- 未提交、未推送（符合方案停止条件），无需处理 git 状态。

## 审查所用对抗样本

- 探针脚本：`D:\work\ShitPM\.tmp\adversarial-probe\probe.py`（构造 design + 干净/带毒 PRD，端到端跑两个脚本并输出分类与退出码）。
- CLEAN（模板忠实写法）复现了 P1；DIRTY 验证了拦截有效。
