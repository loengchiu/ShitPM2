# ShitPM 校验流程精简方案

> 2026-07-30 | 基于"确认/审查顺序错误"根因分析和真实项目使用反馈

## 1. 核心判断

**校验不是不够，是散落各处、互相不知对方在做什么。** 精简的目标不是"少检查"，是"把检查收拢到一个真正有效的关口，删掉不拦人的薄封装和脚本越位"。

## 2. 现状：四层校验，各自为政

### 一层：编排器内部（生成时自动跑）

`design-orchestrator.py` 的 `accept_outputs` 在每次接受动作时已运行：

- **结构门禁**：`design-index.py compile --require-current-format`（退出码非 0 拒）
- **综合审查**：`_validate_comprehensive_review` 校验 comprehensive.json 的 schema 和 6 项 coverage（P0/P1 不通过拒）
- **交接门禁**：`context-runtime-check.py` 校验 v2 基线资产（handoff schema 不符拒）
- **上游完整性**：`_validate_design_writer_upstream` 检查 a/b/c baseline 存在 + material_revision 新鲜

**这层是最全的，但只对编排器自己可见——确认和下游都不查它。**

### 二层：确认门禁（人按确认时跑）

`design-confirmation.py` 的 `run_deterministic_gate` **只跑一道**：

- `state-machine-check.py`（P1 > 0 拒）

编排器 accept 跑了三道（结构+综合审查+交接），确认只跑一道（状态机）。**编排器拒了的东西，确认可能放行。**

### 三层：下游准入（PRD/Prototype 生成时跑）

PRD/Prototype 入口：

1. `design-confirmation.py check` → 状态机 + 哈希比对
2. `artifact-guard.py record` → 再查确认 + 一致性检查（`prd-consistency-check.py` / `prototype-consistency-check.py`）

同一份 `design.md` 被独立解析了 3 次：design-index 一次、state-machine-check（通过 stage-prep）一次、prd-consistency-check（也通过 stage-prep）一次。

### 四层：Review 前检查（可选，但脚本很重）

`review-precheck.py`：645 行，检查文件存在、7 个核心章节、7 个产品定义章节、legacy metadata、页面字段覆盖、PRD 风格 lint、PRD 实体覆盖。**所有检查结果标注为"informational，不阻塞 Review"。**

## 3. 过度设计证据

### 3.1 数量证据

| 指标 | 数值 |
|------|------|
| 生产脚本总数 | 26 |
| 生产代码总行数 | ~10,000 |
| 同一份 design.md 被独立解析次数 | 3 |
| "只报告、不阻塞"的脚本 | 1（review-precheck，645 行） |
| 标注"legacy"但被 3 个脚本依赖的代码 | stage-prep.py（1116 行） |

### 3.2 结构证据：确认和编排器是两套独立门禁

```
编排器 accept_outputs                    design-confirmation.py confirm
  ├── 结构门禁 ✅                           ├── 状态机 ✅
  ├── 综合审查 ✅                           ├── 结构门禁 ❌ 没有
  └── 交接门禁 ✅                           └── 综合审查 ❌ 没有
       ↑                                          ↑
    最全的门禁                             用户"确认"时唯一跑的门禁
    但确认不看它                           但比编排器弱
```

结果：编排器因为结构错误拒了 design-editor → 用户仍然可以 `confirm` 成功（确认只看状态机）→ 下游基于有结构缺陷的 design.md 生成 PRD。**质量风险恰恰在确认太弱，不在检查太少。**

### 3.3 被删了也没影响的检查

| 脚本 | 行数 | 实际阻挡了什么？ |
|------|------|-----------------|
| review-precheck.py | 645 | 无。所有 finding 标注"不阻塞 Review"。 |
| artifact-guard.py | 169 | 无。check-input 是 design-confirmation 的薄封装，record 是一致性检查的薄封装。 |
| context-runtime-check.py（在编排器 accept 中） | — | 编排器自己的 receipt 机制已在做同样的 output hash + material_revision 校验。 |
| verify-against-metadata.py | 195 | 无。metadata 已不生成（AGENTS.md 已删，主流程不走 metadata）。 |

### 3.4 违反"脚本只做模型做不稳的事"原则

`review-precheck.py` 做的事：读文件 → 检查章节标题是否存在 → 输出报告。这是模型在 Review SKILL 里就能做的判断。脚本做模型判断 = 越位。

## 4. 精简方案

### 4.1 核心原则

1. **编排器 accept 是唯一全量校验点。** 所有确定性检查（结构+状态机+综合审查）在编排器接受 design-editor 时一次性跑完。
2. **确认不重复检查。** 确认只看"编排器已 accept design-editor + 哈希一致"，不再独立跑任何检查。
3. **下游只看确认。** PRD/Prototype 的准入 = 确认有效（编排器 accept + 哈希一致）。一致性检查保留，但不再经过薄封装。
4. **模型做模型的事，脚本做模型做不稳的事。** Review 的章节/质量检查由 Review SKILL 的检查清单驱动，不写脚本。

### 4.2 P0：确认门禁改为"编排器已接受"判据

**文件**：`scripts/python/design-confirmation.py`、`scripts/python/design-orchestrator.py`

**改什么**：

- `design-confirmation.py confirm`：不再调 `run_deterministic_gate`。改为检查 `.workflow/runtime/context/design/` 下编排器的 design-editor 接受记录（receipt）存在且 design.md 哈希一致。有 receipt 才写确认标记。
- `design-confirmation.py check`：检查 receipt 存在 + 哈希一致。"已确认" = receipt 有效 + 哈希一致。
- `design-orchestrator.py accept_outputs`：在 design-editor 接受时**增加** `state-machine-check.py` 调用（当前只有结构门禁+综合审查，缺状态机）。确保编排器 accept 跑全三道。
- `run_deterministic_gate` 函数：删除。

**效果**：

- 确认从"只查一道（状态机）"升级为"编排器全量（结构+状态机+综合审查）都通过才让确认"
- 确认入口安全等级**上升**，不是下降
- 去掉确认和编排器的重复解析

**不碰的**：

- `design-index.py`、`state-machine-check.py`、编排器的 `_validate_comprehensive_review`：内部逻辑不动，只调整调用位置
- `design-confirmation.py` 的输出 JSON 字段：`ok/confirmed/reason/confirmed_at` 保留，兼容下游和测试

### 4.3 P0：删除 review-precheck.py，检查项并入 Review SKILL

**文件**：`scripts/python/review-precheck.py`（删除）、`skills/spm-design-review/SKILL.md`、`skills/spm-prd-review/SKILL.md`

**改什么**：

- 将 review-precheck 的检查清单（核心章节存在性、产品定义章节、PRD 实体覆盖等）作为 Review SKILL 的"检查前快速扫描"步骤写入 SKILL.md
- `spm-design-review` 和 `spm-prd-review` 在开始语义审查前，先快速扫描这些结构项作为 warm-up
- 删除 `review-precheck.py` 脚本

**效果**：

- 这些检查本来就是"informational，不阻塞"，模型做比脚本做更灵活（能判断别名、能区分"缺了但不需要"和"缺了有问题"）
- 减少 645 行脚本代码
- 符合"脚本做确定性、模型做判断"原则

**为什么不会降质量**：review-precheck 从不阻塞 Review 开始。模型在 Review 过程中本来就会注意到章节缺失——现在把它正式化为 SKILL 里的检查步骤，反而更可能被遵循。

### 4.4 P1：合并 artifact-guard.py 到下游 SKILL

**文件**：`scripts/python/artifact-guard.py`（删除）、`skills/spm-prd/SKILL.md`、`skills/spm-prototype/SKILL.md`

**改什么**：

- `spm-prd` SKILL：直接调用 `design-confirmation.py check` + `prd-consistency-check.py`，去掉 `artifact-guard.py check-input/record` 中间层
- `spm-prototype` SKILL：直接调用 `design-confirmation.py check` + `prototype-consistency-check.py`，去掉中间层
- provenance 记录逻辑：如果 provenance 信息仍有价值，搬到一致性检查脚本的输出里，不单独建文件
- 删除 `artifact-guard.py` 脚本

**效果**：

- 减少一个薄封装层。下游 SKILL 的调用链更短、更清晰
- 一致性检查保留，只是调用方式从"artifact-guard 调一致性检查"变成"SKILL 直接调一致性检查"

### 4.5 P1：彻底迁移 stage-prep.py → design-index.py

**文件**：`scripts/python/stage-prep.py`（删除）、`scripts/python/design-index.py`、`scripts/python/state-machine-check.py`、`scripts/python/prd-consistency-check.py`、`scripts/python/prototype-consistency-check.py`

**改什么**：

- 将 stage-prep 中仍被依赖的解析逻辑（实体提取、状态机解析、页面提取）迁入 design-index.py 或独立的 `design-parser.py`
- state-machine-check、prd-consistency-check、prototype-consistency-check 改用 design-index 的输出格式
- 删除 stage-prep.py

**风险**：stage-prep 的解析逻辑与 design-index 的解析逻辑存在差异（stage-prep 做了表格解析、别名匹配等）。迁移需要对比测试保证等价性。

**可接受的分步策略**：第一步先让三个依赖方改用 design-index.py 的输出格式（design-index 已有 `_extract_states` 等方法）；第二步对比差异，补充 design-index 缺失的解析能力；第三步删除 stage-prep。

### 4.6 P2：去掉编排器 accept 中 context-runtime-check 的重复调用

**文件**：`scripts/python/design-orchestrator.py`

**改什么**：

- `accept_outputs` 中 `_handoff_requirements()` 调 `context-runtime-check.py` 的逻辑可以简化：编排器自己的 `_current_dependency_outputs` 和 receipt 机制已经在检查上游 output hash + material_revision
- `context-runtime-check.py` 保留（SKILL 层的交接门禁仍有独立价值），但从编排器的热路径中移除

**注意**：此项需要仔细验证 receipt 机制确实覆盖了 context-runtime-check 的所有校验项。如果验证发现有关键差异，此项降级或取消。

### 4.7 P2：删除 verify-against-metadata.py

**文件**：`scripts/python/verify-against-metadata.py`（删除）

**理由**：metadata 已不生成。脚本无调用方、无测试覆盖。

## 5. 精简后体系

### 5.1 核心校验流

```
编排器 accept design-editor（唯一全量校验点）
  ├── design-index.py compile           ← 结构完整性
  ├── state-machine-check.py            ← 状态机闭环（从确认迁入）
  ├── _validate_comprehensive_review    ← 6 项 coverage 综合审查
  └── 上游 baseline + receipt 完整性    ← output hash + material_revision

确认（人签字，不重跑检查）
  ├── 编排器 receipt 存在？
  └── design.md 哈希与 receipt 一致？
       ↓ 都满足 → 写入确认标记

下游准入
  ├── design-confirmation.py check      ← 确认有效？（receipt + 哈希）
  ├── prd-consistency-check.py          ← PRD vs Design 结构对比
  └── prototype-consistency-check.py    ← 原型 vs Design 结构对比

Review（可选，模型驱动）
  └── SKILL 检查清单 → 模型做语义审查  ← 脚本不做模型判断
```

### 5.2 精简前后对比

| 指标 | 精简前 | 精简后 |
|------|--------|--------|
| 生产脚本数 | 26 | ~18 |
| 生产代码行数 | ~10,000 | ~7,000（-30%） |
| design.md 被独立解析次数 | 3 | 1（只有 design-index） |
| 确认时跑的检查层 | 1（状态机）+ 编排器 3（但互不通） | 0（只看编排器 receipt） |
| 确认实际安全等级 | 只拦状态机，结构/综合审查兜不住 | 编排器三道全过才让确认 |
| "只报告不阻塞"的脚本 | review-precheck（645 行） | 无 |
| legacy 但仍被依赖的代码 | stage-prep（1116 行） | 无 |
| 薄封装 | artifact-guard（169 行） | 无 |

### 5.3 保留的核心脚本（不动）

| 脚本 | 保留原因 |
|------|---------|
| design-orchestrator.py | 编排引擎，增加 state-machine-check 调用 |
| design-index.py | 核心结构解析，迁入 stage-prep 的剩余逻辑 |
| design-confirmation.py | 确认标记，简化为 receipt 判据 |
| state-machine-check.py | 状态机结构校验，调用位置从确认迁到编排器 |
| prd-consistency-check.py | PRD vs Design 确定性结构对比 |
| prototype-consistency-check.py | 原型 vs Design 确定性结构对比 |
| source-index.py | 材料索引 |
| context-pack.py | 上下文编译 |
| context-budget.py | Token 预算 |
| prd-style-lint.py | PRD 风格检查 |
| prototype-structure.py | 原型结构 |
| material_revision.py | 材料版本追踪 |
| shared_md.py | 公共 Markdown 解析 |
| shitpm-host.py | 宿主安装 |
| stage-context.py | 项目状态查询 |
| context-run.py | 上下文运行时 |

## 6. 质量论证：为什么不会降

### 6.1 确认入口安全等级上升

```
精简前：确认 = 状态机一道
精简后：确认 = 编排器三道全绿（结构 + 状态机 + 综合审查）
```

确认不是在变弱，是在变强。

### 6.2 被删的都是不拦人的

- review-precheck：所有 finding 标注"不阻塞"
- artifact-guard：薄封装，没有独立检查逻辑
- verify-against-metadata：metadata 已不存在，脚本自然失效
- context-runtime-check 在编排器里：receipt 机制已覆盖
- stage-prep：逻辑迁入 design-index，不是丢弃

### 6.3 review-precheck 的替代

review-precheck 的检查清单**写入 Review SKILL**，由模型在执行 Review 时主动扫描。模型比脚本更能判断"这个章节缺了但本项目确实不需要"vs"这个章节缺了是个问题"——脚本只能报存在/不存在，模型能做上下文判断。

### 6.4 什么情况下质量会降

只有一个场景：**编排器 accept 的 receipt 被伪造或丢失，而确认只看 receipt 存在性。** 预防措施：

- receipt 包含 output hash，改 design.md 后 receipt 自动失效
- 确认时校验 design.md 哈希与 receipt 记录一致
- `design-confirmation.py check` 的输出仍有 `reason` 字段，下游可区分"没收据"和"哈希变了"

## 7. 执行顺序

```
Phase 1（P0，先做）
  ├── 1a: 编排器 accept_outputs 增加 state-machine-check 调用
  ├── 1b: design-confirmation 简化为 receipt 判据
  └── 1c: 回归测试全绿 + 手工验收

Phase 2（P0，再做）
  ├── 2a: review-precheck 检查项写入 Review SKILL
  └── 2b: 删除 review-precheck.py

Phase 3（P1）
  ├── 3a: artifact-guard 逻辑拆入下游 SKILL
  ├── 3b: 删除 artifact-guard.py
  ├── 3c: stage-prep 迁移 → design-index
  └── 3d: 删除 stage-prep.py

Phase 4（P2，按需）
  ├── 4a: 验证 receipt 覆盖 context-runtime-check，移除热路径调用
  └── 4b: 删除 verify-against-metadata.py
```

每 phase 完成后跑 `test-shitpm-regression.py`（当前 37/0）确认不回归。

## 8. 不碰的边界

- 不改 `design-index.py`、`state-machine-check.py`、`prd-consistency-check.py`、`prototype-consistency-check.py` 的内部校验逻辑
- 不改 SKILL 的职责定义（谁干什么不变）
- 不改 Review 的可选/不卡门性质
- 不删测试脚本
- 不引新模式名词，SKILL 措辞与现有风格一致
- 不自动确认、不自动推进下游
