# Round 21 全量对抗性审查报告

> 审查对象：R19（`443a93e`）之后的全部改动，含已提交 `4b5bc2b`（含 R20 报告）、`df6c178`（移除 context-run.py + 上下文加载优化）与 **20 个未提交文件**（净删 550 行）。
> 审查性质：精简迭代的对抗性复核——重点排查「简化过程中丢约束 / 误伤合规产物 / 测试被弱化以适配简化」。
> 审查日期：2026-08-05
> 方法：逐文件 diff 阅读 + 跨层引用程序化校验 + **真实素材实证**（真实 PRD/Design 对喂脚本）+ 全量测试套件复跑。

## 结论速览

- **无 P0 / 无 P1（阻断级）**。
- **发现 3 个 P2**（均局部、非阻断，但建议尽快修）：
  - **P2-1**：`prd-consistency-check.py` 枚举值比较空白敏感，`10年` vs `10 年` 被误判为确定性冲突，触发硬门禁（退出 1）。
  - **P2-2**：`prd-style-lint.py` 的 STYLE009（名词说明章节）因第三别名 `总体说明` 与模板强制章节同名，**形同虚设**，无法检测术语表缺失。
  - **P2-3**：STYLE005（跨节引用）与「新模板页面无编号」约定存在张力，SKILL 未明确页面引用写法，旧习惯写「见 5.1.1.2」会误报 error。
- **测试未弱化**：`test-prd-simplification.py` 重写后更严（断言精简装载面、SKILL≤160 行、lint 退出语义收窄到 `deterministic_conflict`）；5 个测试套件全绿。
- **悬空引用清零**：`context-run.py` 无生产引用；`prd-profile` 等旧 pack 彻底移除，`manifest` marker/section 引用程序化校验通过。

---

## 一、审查范围与基线

| 维度 | 内容 |
|---|---|
| 上次审查基线 | R19 `443a93e`（R20 已审至 `4b5bc2b`） |
| 本次新增改动 | `df6c178`（移除 context-run.py）+ 20 个未提交文件 |
| 净变更 | +1102 / −1652 行（净删 550） |
| 受影响层 | skills×2、contracts×4、references×5、scripts×3、templates×1、tests×5 |
| 最大改动 | `references/prd-writing-rules.md` −444 行、`skills/spm-prd/SKILL.md` −286 行、`scripts/context-pack.py` +332、`prd-style-lint.py` +179、`prd-consistency-check.py` +321 |

这是一次以「精简」为主线的迭代：PRD skill 从 ~280 行砍到 ~89 行，references 大幅瘦身，consistency-check 从结构匹配重写为名称级集合对比，context-pack 重写。

---

## 二、逐层审查与实证结果

### 2.1 SKILL 层（spm-prd / spm-fix）
- PRD skill △286 行后保留完整流程闭环（A 全局扫描 → B 骨架 → C 分片写入 → D 整合 → 最终检查），高影响未知、Design 确认、分片读取等约束均在。
- 最终门禁明确：`prd-style-lint.py` error→必须修复；`prd-consistency-check.py` `deterministic_conflict`→阻断。门禁语义清晰。
- `spm-fix` 引用从 `prd-writing-rules.md §5` 改为 `templates/prd.md`，与模板实际承载位置一致。✓

### 2.2 Contracts 层
- `prd-review-checklist.md` **新增**前端/后端独立开发检查项（V1–V9、W1–W10），补偿了 writing-rules 的部分删减，且包含「Design 全读痕迹 / 一次性全读 design.md / 上下文爆栈」等本次分片治理的专项项。✓（强项）
- `context-loading.manifest.json` 删除 `prd-profile` pack；程序化校验所有 marker 与 section 引用一致。✓

### 2.3 References 层
- `prd-writing-rules.md` −444 行，但关键约束（详细需求说明写作规范、自然语言硬约束、行首标签禁用、动作按业务结果/复杂度、跨前后端完整业务链、事实边界与信息密度）经 `test-prd-simplification.py` 断言仍存在。✓
- draw.io→PNG（2 倍分辨率）规则未丢，落在模板 `4.1.4 业务流程` 注释 + review checklist 第 44/45 条。✓

### 2.4 Scripts 层（重写三件套）
- **context-pack.py（+332）**：资源完整性 / marker 提取 / 分片选择逻辑重写；`test-context-loading.py` 全绿（manifest、标记、来源、去重、module 分片、产品边界均正常）。✓
- **prd-style-lint.py（+179）**：STYLE005 从「全量刷 info 噪音」改为「仅目标不存在时报 error」（降噪改进）；新增 STYLE010/011/012 启发式。**实证发现 P2-2、P2-3（见第三节）**。
- **prd-consistency-check.py（+321）**：从结构匹配重写为「名称级存在性 + 确定性属性比对」，语义判断显式降级给 Review（符合仓库「脚本只做确定性问题」原则）。
  - 实证：在仓库自带真实对 `test-fixture/output`（prd.md + design.md）上跑通，稳定提取 401 字段 / 54 页 / 34 状态。
  - 真实捕获 1 个真阳性（PRD「用户类型」枚举擅自扩张）+ 1 个**空格误报**（P2-1）+ 10 个内部字段承接项（属语义判断范畴）。**降级未导致真实冲突漏检**。✓（核心能力保留）

### 2.5 Templates 层
- `templates/prd.md` 结构自洽：术语用表格（§3.6）、页面用六级标题（###### 页面名称）、动作用单独加粗行（**动作名称**）、字段补充用对象字段表。与 SKILL/references 一致。✓

### 2.6 Tests 层
- **未弱化**：`test-prd-simplification.py` 重写后断言更严（writing pack=5、module pack=4、SKILL≤160 行 / ≤2500 token、`--example` 键齐全、旧 pass 被清晰拒绝、lint 退出语义收窄到 `deterministic_conflict`）。
- 5 套件全绿：`test-prd-style-lint` / `test-prd-consistency-semantics` / `test-prd-simplification` / `test-context-loading` / `test-design-index`。✓

---

## 三、发现（分级）

### P2-1：consistency-check 枚举值空白敏感 → 空格误报触发硬门禁
**证据**（真实对 `test-fixture/output` 输出）：
```
保管期限  design_enum=["10年","20年","永久"]  prd_enum=["10 年","20 年","永久"]
→ enum_missing=["10年","20年"]  enum_hallucinated=["10 年","20 年"]  deterministic=true
→ exit_reason=deterministic_conflict（退出 1，阻断）
```
唯一差别是空格。`_parse_enum_values` / 比较分支未对枚举值做空白归一化（也未处理全半角），把「10年」≠「10 年」判成确定性冲突。

**影响**：consistency 是 PRD 最终硬门禁（`deterministic_conflict` 返回 1 阻断并修复）。一处空格即可阻断合规 PRD 交付。属重写引入的新代码路径缺陷。

**修复**：在枚举解析/比较前对值做 `re.sub(r'\s+', '', v)` 归一（必要时再补全半角归一）。建议同时在该分支单测补用例（"10年" vs "10 年" 应判相等）。

### P2-2：STYLE009 名词说明检查形同虚设
**证据**（`prd-style-lint.py:485-487`）：
```python
re.match(r'^#{1,2}\s.*名词说明', stripped) or
re.match(r'^#{1,2}\s.*术语说明', stripped) or
re.match(r'^#{1,2}\s.*总体说明', stripped)   # ← 第三别名
```
模板强制章节为 `## 3 总体说明`（H2）。任意模板合规 PRD 必有该章节，于是 `has_glossary` 恒为 True，**术语表是否真定义过不过问**。

**实证**：用当前模板（含 `### 3.6 术语定义` + 术语表）生成的极简 PRD 跑 lint → 「无问题」，STYLE009 不触发；去掉 `## 3 总体说明` 后才报错。

**影响**：非阻断（error 但实际永不触发），但语义空洞——无法检出「总体说明在、术语表空」的缺陷。同时：别名列表也未含模板实际用的 `术语定义`，若未来去掉 `总体说明` 别名则会反向误杀合规 PRD（本轮已用实证排除该反向风险）。

**修复**：去掉 `总体说明` 别名，改为识别 `术语定义` / `名词说明` / `术语说明`，并把层级放宽到 H3（`#{1,3}`），使检查真正落到术语表存在性。

### P2-3：STYLE005 与「无编号页面」约定张力（约定缺口）
**证据**：新模板页面格式为 `###### 页面名称`（**无编号**），但 STYLE005 仅对 `见/参见/详见 <数字编号>` 做存在性校验（`prd-style-lint.py:check_cross_section_refs`）。数字引用只解析 markdown **编号标题**，不解析无编号页面。

**实证**：`test-fixture/output/prd/prd-5.1-skill-generated.md` 用 `**5.1.1.2 年度计划详情**`（加粗非标题）承载页面并写「见 5.1.1.2」，STYLE005 报 5 处「内部引用目标不存在」。该 fixture 属旧生成风格（粗体编号页面），与当前模板不一致——属 fixture 陈旧，但暴露了**约定缺口**：按当前模板，页面无编号，作者若沿用「见 X.X.X」数字引用必然误报 error。

**影响**：非 lint 代码 bug（对坏引用判定正确），而是 SKILL 未定义「页面如何被引用」。作者容易踩坑。

**修复**：在 PRD SKILL 阶段 D 明确「页面引用用名称（见 列表页），不按编号；引用上游 Design 写 `Design §x.x`」，与无编号页面模板对齐。

---

## 四、已确认干净的强项（非缺陷，记录以备查）

1. **测试未弱化反而更严**：精简回归测试断言装载面、规模上限、lint 退出语义，是高质量回归护栏。
2. **悬空引用清零**：`context-run.py` 经 `df6c178` 移除后无任何生产引用（仅 docs 历史）；`prd-profile` 等旧 pack 彻底删除，`manifest` 引用一致性程序化校验通过。
3. **前期死配置正向解决**：R14/R15 报告建议删除的 `prd-examples` 死配置，本轮未删而是**接进 module pass**（自动装载 simple-readonly / multi-role-state + 按需 `--example`），符合「示例非规范但要可用」定位。
4. **STYLE008 占位符误报风险被显式降级**：设计者已知「按配置」等有误报可能，主动设为 warning 交 AI 判断（`prd-style-lint.py:90` 注释），处理得当。
5. **consistency 降级未丢能力**：重写后仍稳定抓真实冲突（用户类型枚举扩张），multipass 提取稳定。
6. **draw.io→PNG 规则未丢**：落在模板注释 + review checklist。

---

## 五、测试结论

| 套件 | 结果 |
|---|---|
| test-prd-style-lint | PASS |
| test-prd-consistency-semantics | PASS |
| test-prd-simplification | PASS（已加强） |
| test-context-loading | PASS |
| test-design-index | PASS |

全部绿。测试覆盖本次简化行为，**未发现为适配简化而弱化的断言**。

---

## 六、修复优先级建议

| 优先级 | 项 | 修复量 | 门禁影响 |
|---|---|---|---|
| 高（尽快） | P2-1 枚举空白归一 | ~5 行 + 单测 | 硬门禁，空格即阻断 |
| 中 | P2-2 STYLE009 别名修正 | ~3 行 | 当前不阻断但检查空洞 |
| 中 | P2-3 SKILL 明确页面引用写法 | 文档补充 | 避免作者误报 |

三项均为局部改动，无架构影响。建议 P2-1 在本次迭代收口前修掉（否则真实 PRD 生成会撞硬门禁）。

---

## 七、审查方法备注

- 本报告结论均经**实证**而非仅代码阅读：用当前模板生成极简 PRD 喂 lint 验证 STYLE009；用仓库自带真实 PRD/Design 对喂 consistency-check 验证降级后能力与误报；程序化校验 manifest marker/section 引用。
- 曾一度将 STYLE009 误判为 P0（认为会误杀合规 PRD），实证后纠正为 P2（实际因 `总体说明` 别名永不触发）。记录此误判以免后续 reviewer 重复踩坑。
