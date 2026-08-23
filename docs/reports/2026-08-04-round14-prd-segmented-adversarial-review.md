# PRD 全量分片写作修订 · R14 全量对抗性审查报告

> 日期：2026-08-04
> 审查者：WorkBuddy（全量对抗性审查）
> 审查对象：`D:\work\ShitPM` 当前工作树（PRD 全量分片写作修订，对应 `docs/plans/2026-08-04-prd-segmented-writing-plan-and-acceptance.md`）
> 方法：读工作树全文与 diff、跑 12 套测试 + 对抗探针、核对 manifest/context-pack.py 实际装载行为、复核上轮 4 P2 处置、交叉一致性。

## 结论先行

修订**方向正确、四层验收基本通过**：规则层/结构层/语义层达标，行为层落地但有 1 个 P1（指令与实现不符）。未越界（无新增检查器/门禁/回执/覆盖率 JSON），12 套测试全绿，对抗探针 CLEAN 不阻断 / DIRTY 正确拦截。

- **P0：无**
- **P1：1 项**（`--example` 参数在 module pass 下被静默忽略，SKILL 指令骗模型）
- **P2：9 项**（行为层措辞 5 / 死代码 2 / 上轮遗留 2）

P1 未修复前，不能宣称"SKILL 阶段 C 指令可被模型稳定执行"。

## 审查范围与方法

| 动作 | 结果 |
|---|---|
| 12 套 `test-*.py` 全量回归 | 全绿（exit=0） |
| 对抗探针 `.tmp/adversarial-probe/probe.py` | CLEAN exit=0（possible_omission，不阻断）/ DIRTY exit=1（4字段+1页面+1状态确定性冲突 + STYLE001）|
| manifest + context-pack.py 装载行为核对 | 发现 P1：`--example` 在 module pass 静默失效 |
| 上轮 4 P2 复查 | P2-2 已缓解；P2-1/P2-3 未处理；P2-4 部分误判（订正） |
| 范围膨胀核查 | 改动严格落在 plan §3 的 10 文件 + AGENTS.md 四象限 + 1 plan 文档；**未新增任何脚本/检查器/门禁/回执** |

## P1：`--example` 参数在 module pass 下被静默忽略（指令与实现不符）

### 现象（可复现）

`skills/spm-prd/SKILL.md` 阶段 C 指示模型运行：

```text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass module --card <scene-key> --example <example-key>
```

但实际跑这条命令时，`--example <example-key>` 被**静默忽略**，模型拿不到任何 `prd-writing-examples.md` 示例章节。

### 根因（已定位）

1. `contracts/context-loading.manifest.json` 中 `prd` stage 的 `module` pass 只挂载 4 个 pack：`prd-core`、`prd-writing-structure`、`prd-writing-action`、`prd-cards`。
2. `--example` 对应的 `prd-examples` pack（含 10 个 `example_sections`：simple-action/complex-action/field-table/page-fields/action-body/page-layout/glossary/small-module/bad-action/flow）**没有被任何 pass 引用**。
3. `scripts/python/context-pack.py:90-94` 的处理逻辑：

   ```python
   if 'example_sections' in pack:
       for example in examples:
           if example not in pack['example_sections']:
               raise RuntimeError(...)
           section_ids.extend(pack['example_sections'][example])
   ```

   只对**含 `example_sections` 字段的 pack** 处理 `--example`。module pass 的 4 个 pack 都没有该字段 → `--example` 参数被完全跳过，不报错也不装载。

### 为什么测试没发现

`test-prd-simplification.py` 加强了断言（锁住旧路径不复活 + 新规则必须存在），但**只断言 SKILL 文本里出现 `--pass writing`/`--pass module` 字样，未断言 `--example` 参数的实际装载行为**。`test-context-loading.py` 也没构造"传 --example 验证示例 section 是否进 pack"的用例。又是一处"文本存在 ≠ 行为生效"的测试盲区。

### 影响

不阻断交付（writing/module pass 已装载规则+模板+动作规则，模型有规范可依），但属于"指令骗模型"类 footgun：模型按 SKILL 传 `--example simple-action`，以为拿到了简单动作示例，实际什么都没装载。模型若据此判断"已参考示例"会误信，若发现没示例可能自行猜测 SKILL 指令意图。

### 建议修复（二选一）

- **方案 A（推荐）**：SKILL 阶段 C 删掉 `--example <example-key>`。示例是非规范性写作参考，模块写入时规则+模板已够；符合 AGENTS.md §1 #8"对最终结果无影响的工具应删除"与精简原则。同步删 manifest 里未被引用的 `prd-examples` pack 定义（死配置）。
- **方案 B**：manifest 把 `prd-examples` 加进 `module` pass 的 pack 列表，让 `--example` 真正生效。但这会让 module pass 每次都按 example key 装载示例，增加上下文且示例非规范，不推荐。

### 强相关次级：`--card <scene-key>` 措辞误导（P2-1）

manifest 的 `prd-cards` 只有 `scenes` 一个 `card_sections` key。SKILL 写 `--card <scene-key>` 暗示按模块选不同 scene key，实际合法值只有 `scenes`；模型传其他值会触发 `context-pack.py:87` 的 `RuntimeError`。应写死 `--card scenes` 或说明"当前 PRD 只有 scenes 一个 card"。

## P2：健壮性与整洁项

### 行为层措辞（5 项）

1. **阶段 A"全局扫描"未明说读取 Design 的动作**：SKILL §阶段 A 说"只读取并建立以下导航信息"，但没说用 `context-pack`（writing pass 不含 Design 内容）还是直接 `Read output/design/design.md`。模型可能困惑。建议明说"直接阅读 `output/design/design.md` 建立导航，不要求全文驻留上下文"。
2. **"生成内自检与直接修正"未适配分片流程**：该节措辞"展示 PRD 前，在同一写作动作内逐项回读 Design"仍像一次性生成。分片流程下应区分：每个模块写入时做局部自检（模块完成条件 8 条），最终整合时做全局自检（11 条中跨模块项）。当前措辞会让模型在单模块写入时试图检查"每个功能模块"（无法做到）。
3. **中断恢复"找最后一个未完成模块"判据未明说**：SKILL §中断恢复 5 步没说怎么判断"未完成"。建议明示"4.x.6 功能详细说明为空或缺失即未完成模块"。
4. **模板 4.1.6.1 只给一个业务阶段示例**：`templates/prd.md:79` 只示例 `##### 4.1.6.1 业务阶段名称` 一个阶段，可能诱导模型只写一个阶段。应说明"每个业务阶段一个 ##### 标题，按业务结果拆分"。
5. **写作规则 §0 没说"如何从 Design 识别业务闭环"**：规则 §0 #1"分片边界来自业务闭环（Design 的业务边界）"，但 Design 模板/规则是否产出显式"业务闭环"概念未交叉说明。若 Design 按页面/对象组织，模型可能无法稳定识别闭环边界。建议在 Design 侧或 PRD 规则侧点明"业务闭环从 Design 的业务过程/业务结果章节识别"。

### 死代码（2 项）

6. **`extract_prd_modules` 死路径未删**：`prd-consistency-check.py:794-801` 仍只从"详细需求说明"章节提取模块，新结构容器是 `## 4. 功能需求`、模块是 `### 4.1`，没有"详细需求说明"章节 → 函数恒返回空 → line 1548 调用结果 inert。违反 AGENTS.md §1 #8"删除死代码"。建议删除或改造为从 `## 4. 功能需求` 下的 `### 4.x` 提取。
7. **`context-run.py` 孤儿脚本**：`scripts/python/context-run.py`（2799 字节）零生产引用（grep 全仓只命中 memory 和历史报告，无 skill/contract/生产脚本调用）。按 AGENTS.md §1 #13"删除死代码"原则，应删除。

### 上轮遗留（2 项）

8. **STYLE003 表格主导检测仍锚定标题关键词**（上轮 P2-1，未处理）：`prd-style-lint.py:171` `if re.search(r'业务闭环|业务模块|业务阶段|功能需求|功能详细说明', title)` 仍硬耦合标题关键词。当前模板容器 `## 4. 功能需求` 能匹配，但重命名即静默失效。已加"功能详细说明"兜底，仍未根治。建议改为"对整个 `## 4.` 业务模块区统一扫描"。
9. **`prd-writing-examples.md` small-module 示例跳过部分章节**：示例只写 4.1.1/4.1.3/4.1.6/4.1.7/4.1.9/4.1.10，跳过 4.1.2/4.1.4/4.1.5/4.1.8。结尾注释"真实模块必须就近写全对象与关系、流程、状态与业务规则、异常处理"已兜底，但模型可能模仿示例跳章。低风险。

## 已验证通过（正面项，避免误判）

- **规则层**：SKILL/模板/写作规则/Review checklist/scene checklist/examples/subagent contract/test 七处描述同一条分片落盘流程，无自相矛盾。
- **结构层**：`4.x.6 功能详细说明` 在 SKILL 模块完成条件 #1、模板 4.1.6 注释、写作规则 §0 #6、Review checklist S1-S5、scene checklist 模块结束检查 五处一致硬约束。
- **行为层**：四阶段 A/B/C/D 齐全；中断恢复 5 步；不依赖 subagent 且三方一致（manifest purpose / subagent contract / SKILL）；分片直接写入最终 `prd.md`；禁止"草稿全部完成后再整篇重写"在 SKILL、规则 §0 #2、subagent contract 三处锁死。
- **语义层**：事实边界明确（不得补造页面/字段/角色/权限/状态/流程/默认值/超时/重试/补偿/提示文案/外部行为）；待确认不静默拍板；交互细节不越 Design 边界。
- **测试**：12/12 全绿；`test-prd-simplification.py` 断言加强（forbidden 列表锁旧路径、required 列表锁新规则、模板与规则断言新增）。
- **对抗探针**：CLEAN 新结构 `exit=0`（上轮 P1 枚举误报确认已修）、DIRTY 正确拦截（确定性冲突 + STYLE001）。
- **未越界**：无新增检查器/门禁/回执/覆盖率 JSON/承接矩阵（符合 AGENTS.md §1 #8/#9）；`prd-writing-rules.md` 常见错误表新增"用 Mermaid 代替交付流程图"反模式，与 drawio+PNG 交付一致。
- **subagent 收敛**：`prd-module-writer` 改为"只能并行分析、输出事实要点、不得产生内部草稿、无最终写入权"，与"不依赖 subagent"主线一致。
- **上轮 P1（枚举误报）**：`extract_prd_fields` 已加"类型/取值"列内联枚举回退解析 + 必填列整列缺失降级，探针复跑确认修复。
- **上轮 P2-2（页面提取标题硬耦合）**：已缓解，`prd-consistency-check.py:268` 兼容 `["页面清单", "页面与终端映射"]`。
- **上轮 P2-4 订正**：`download-prototype-libs.py` 被 `references/prototype-writing.md:34` 引用，且该文件是 `spm-prototype`/`spm-prototype-review` 运行时规则 → **非孤儿，合法按需工具**（上轮误判）。

## 上轮遗留处置汇总

| 上轮编号 | 内容 | 本轮状态 |
|---|---|---|
| P1（枚举误报） | `extract_prd_fields` 不解析"类型/取值"列内联枚举 | ✅ 已修（探针验证） |
| P2-1 | STYLE003 表格主导检测锚定标题关键词 | 未处理（本轮 P2-8，已加兜底关键词） |
| P2-2 | 页面提取硬耦合"页面与终端映射"标题 | ✅ 已缓解（兼容"页面清单"） |
| P2-3 | `extract_prd_modules` 死路径 | 未处理（本轮 P2-6） |
| P2-4 | `download-prototype-libs.py` / `context-run.py` 孤儿 | 订正：前者非孤儿；`context-run.py` 仍孤儿（本轮 P2-7） |

## 遗留 / 需用户决策

- **P1 必须修**：`--example` 在 module pass 静默失效。建议方案 A（SKILL 删 `--example` + manifest 删 `prd-examples` 死配置），符合精简原则。
- **P2 行为层措辞 5 项**：不阻断，但影响模型稳定执行。建议在下次 PRD Skill 维护时一并修正。
- **P2 死代码 2 项**：`extract_prd_modules` 死路径 + `context-run.py` 孤儿，按 AGENTS.md §1 #8/#13 应删。
- **行为层验收未做真实生成**：plan §14 要求简单样本/复杂样本/中断恢复三场景实跑。本次审查只做了规则/结构/语义层 + 对抗探针，未真实生成 PRD 验证分片落盘行为。建议 P1 修复后由用户安排真实项目冒烟（重点观察：阶段 A 是否稳定识别业务闭环、中断恢复判据是否可执行、`--card scenes` 是否被模型正确传参）。
- 未提交、未推送（符合 plan §3.3 停止条件），无需处理 git 状态。

## 审查所用方法

- 全文阅读：`skills/spm-prd/SKILL.md`、`templates/prd.md`、`references/prd-writing-rules.md`、`contracts/context-loading.manifest.json`。
- diff 核对：`contracts/subagent-context-contract.md`、`contracts/prd-review-checklist.md`、`references/prd-scene-checklist.md`、`references/prd-writing-examples.md`、`skills/spm-prd-review/SKILL.md`、`scripts/python/test-prd-simplification.py`、`AGENTS.md`。
- 代码核对：`scripts/python/context-pack.py`（`--card`/`--example` 处理逻辑 line 77-94、371-372、402）、`scripts/python/prd-consistency-check.py`（`extract_prd_modules` line 794-801、页面提取 line 268）、`scripts/python/prd-style-lint.py`（table_dominance line 171）。
- 探针：`.tmp/adversarial-probe/probe.py`。
