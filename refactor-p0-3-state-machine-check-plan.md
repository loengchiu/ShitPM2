# P0-3 执行计划：状态机闭环结构层脚本化

## 一、背景与障碍

`spm-design-review` 的状态机闭环 8 条审查里，结构层 4 条是纯图论校验，目前由 LLM 在 60K+ 降智区做——又贵又易漏。目标是把这 4 条交给脚本。

**核心障碍（已核实）**：

现有 `states.json` 只有 `{id, type, title}`，**零迁移信息**。`stage-prep.py:271-275` 提取状态机表时只取 `row[0]`（状态名列），丢弃了操作人/触发动作/下一状态/限制条件 4 列，也未记录状态所属实体。34 个状态像扁平清单，看不出归属、终态、迁移关系。

结构层 4 条校验全靠迁移数据，所以 P0-3 必须先补迁移 + 实体归属，才能做图论校验。

**结构层 4 条（来自 `references/design-state-format.md`）**：

1. 非终态必有出路：每个非终态至少一条正向迁移，不悬空
2. 非初始态必有入路：每个非初始状态至少一条迁移指向它，不孤岛
3. 回退目标合法：回退/驳回的 to_state 必须是该实体历史正向路径上的状态
4. 迁移无歧义：同一 `trigger + operator` 组合在不同状态下不能指向冲突的 to_state

## 二、方案选择

**采用方案 A：扩展 `stage-prep.py` 补迁移 + 新增 `state-machine-check.py` 做图论校验。**

| 维度 | 方案 A（扩展 stage-prep + 新脚本） | 方案 B（新脚本直接读 design.md 自解析） |
|------|----------------------------------|--------------------------------------|
| 解析器 | 单一，metadata 完整，所有消费者受益 | 与 stage-prep 重复，两套解析易不一致 |
| 回归风险 | 中（改 stage-prep，但 states 无脚本消费者） | 低（不动 stage-prep） |
| metadata 残缺 | 一并修复 | stage-prep 残缺留存 |

选 A 的理由：stage-prep 现有状态提取本就残缺（只取状态名），方案 B 会让残缺永久化。且 `review-precheck.py` 不读 states、`design-metadata.schema.json` 是 `additionalProperties: true`，改 stage-prep 给 states 增补字段低风险。

## 三、states.json 目标结构

向后兼容：保留现有 `id/type/title`，增补 `entity`（所属实体）和 `transitions`（迁移列表）。终态用 `is_terminal: true` 标记。

```json
[
  {
    "id": "STATE-design-001",
    "type": "state",
    "title": "草稿",
    "entity": "周报",
    "is_terminal": false,
    "transitions": [
      {"trigger": "提交", "operator": "编制人", "to_state": "已提交", "condition": "本周完成内容和下周计划非空", "line": 42}
    ]
  },
  {
    "id": "STATE-design-004",
    "type": "state",
    "title": "已归档",
    "entity": "周报",
    "is_terminal": true,
    "transitions": []
  }
]
```

## 四、实施步骤

### 步骤 1：扩展 `stage-prep.py` 的状态机表提取

**文件**：`scripts/python/stage-prep.py`，函数 `extract_entities_from_tables`（line 210-302）

**改法**：
1. line 271-275 的状态机表提取，从只取 `row[0]` 改为解析完整 6 列：`状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件`
2. 处理"留空行延续"规则：状态名留空时，归属上一行的状态（同状态多条迁移）
3. 记录实体归属：状态机表所属的最近 `###` 标题作为 `entity`
4. 识别终态：触发动作和下一状态均为"—"时 `is_terminal: true`，`transitions: []`
5. 防御性解析：表头非标准 6 列时跳过迁移提取，只保留原 title（向后兼容）

**验证**：在 `test-fixture/output/design/design.md` 上重跑 `stage-prep.py --stage design`，检查生成的 states.json 含 transitions 和 entity 字段，迁移数与 design.md 状态机表行数对齐。

### 步骤 2：新增 `scripts/python/state-machine-check.py`

**职责**：读 `.workflow/metadata/design/states.json`，按 entity 分组，对每个实体的状态机做结构层 4 条图论校验，输出 violations JSON。

**输入**：`--project-root <path>`（默认 `.`）
**输出**：JSON 到 stdout，结构：

```json
{
  "stage": "design",
  "checked_at": "2026-07-16T...",
  "entity_count": 5,
  "violations": [
    {
      "rule": "non_terminal_must_have_exit",
      "entity": "审计底稿",
      "state": "初审完毕",
      "detail": "非终态但无任何正向迁移，悬空",
      "severity": "P1",
      "line": 128
    }
  ],
  "summary": {"total": 3, "P1": 3}
}
```

**4 条校验算法**：
1. `non_terminal_must_have_exit`：`is_terminal=false` 且 `transitions` 为空 → 违规
2. `non_initial_must_have_entry`：某状态不作为任何迁移的 `to_state` 且不是该实体第一个状态 → 孤岛
3. `rollback_target_legal`：迁移含回退语义（trigger 含"退回/驳回/撤回"）时，`to_state` 必须在该实体从初始态到当前状态的正向路径上。用 BFS/DFS 从初始态建正向可达集，回退目标不在集中即违规
4. `transition_no_ambiguity`：按 `(trigger, operator)` 分组迁移，同组若在不同 from_state 指向不同 to_state 且无业务理由 → 歧义（无业务理由的判定：纯结构层无法判，标 P2 提示人审）

**验证**：在 `test-fixture` 上运行，人工核对 violations 是否合理；构造 3 个已知缺陷状态机（悬空/孤岛/回退非法）测检出率。

### 步骤 3：改 `skills/spm-design-review/SKILL.md` 引用脚本结论

**文件**：`skills/spm-design-review/SKILL.md`，第二段 A2 节

**改法**：结构层 4 条（当前 A2 节第 3 点的 4 个子项）改为"运行 `state-machine-check.py`，直接引用 violations；结构层 4 条不再由 LLM 逐项判断"。LLM 只留业务层 4 条（第 4 点的 4 个子项）。

**验证**：通读改后 SKILL.md，确认结构层 4 条指向脚本、业务层 4 条仍由 LLM 做。

## 五、验收标准

1. `state-machine-check.py` 在 `test-fixture` 上运行无异常，输出合法 JSON
2. 构造 3 个已知缺陷（悬空/孤岛/回退非法）的状态机，脚本全部检出
3. 构造 1 个合规状态机，脚本零 violations
4. `stage-prep.py --stage design` 重跑后，states.json 含 transitions/entity 字段，且不破坏现有 id/type/title
5. `verify-against-metadata.py` 在新 states.json 上仍通过（schema 兼容）
6. 改后的 `spm-design-review/SKILL.md` 结构层 4 条引用脚本，业务层 4 条不变

## 六、风险与回退

| 风险 | 应对 |
|------|------|
| stage-prep 状态机表解析遇非标准格式（列数不对/合并行异常） | 防御性解析：非标准时只保留原 title 提取，跳过迁移，不报错；在 stderr 打 warning |
| 回退合法性判断依赖"正向路径"定义，实体无明确初始态时误判 | 无明确初始态时该规则降级为 warning 不计 P1；初始态判定规则：该实体状态机表第一个状态 |
| 迁移无歧义的"业务理由"结构层无法判 | 标 P2 提示人审，不计 verdict 降级 |

**回退**：若 stage-prep 改造引发回归，`git checkout` stage-prep.py，state-machine-check.py 改为方案 B（自解析 design.md）独立运行。

## 七、不做什么

1. 不改 `review-precheck.py`（它不读 states，零影响）
2. 不改 `prd-consistency-check.py`（PRD 阶段状态机是 design 的镜像，结构校验在 design 阶段做一次即可）
3. 不改 `design-metadata.schema.json`（已是 `additionalProperties: true`，加字段无需改 schema）
4. 不做业务层 4 条脚本化（合法出路全覆盖/二次流转闭环/操作人匹配角色/状态语义自洽——这些需要业务语义判断，留 LLM）
5. 不动 prd 阶段的 states（PRD metadata 不含独立状态机定义，是 design 镜像）

## 八、决策记录

- **设计决策**：states.json 增补 `entity` 字段记录状态所属实体——现有提取无归属，结构层校验（尤其回退合法性）必须 per-entity，不补无法做
- **权衡**：考虑过方案 B（新脚本自解析），放弃——会让 stage-prep 残缺提取永久化，两套解析器不一致
- **待确认**：状态机表的"实体归属"从最近的 `###` 标题推断，若 design.md 状态机表未用 `###` 分实体（用其他层级），需调整推断规则——步骤 1 实施时先在 test-fixture 上验证推断准确性
