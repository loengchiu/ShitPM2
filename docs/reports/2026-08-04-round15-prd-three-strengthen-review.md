# PRD Skill 三项补强 · R15 对抗性验收报告

> 日期：2026-08-04
> 审查者：WorkBuddy（对抗性验收，非仅审 diff）
> 审查对象：`D:\work\ShitPM` 当前工作树（PRD Skill 三项补强，对应 `docs/plans/2026-08-04-prd-skill-three-strengthen-plan-and-acceptance.md`；含 R14 已审的分片修订未提交改动）
> 方法：读 SKILL/规则/模板全文与 diff、跑 12 套测试 + 对抗探针、**实跑 context-pack 实证 `--example` 装载行为**、核对 plan §7 解析器五项修复的实现与测试夹具、核查范围外新增物。

## 结论先行

三项补强**落地质量高**：SKILL 与写作规则双落地且一致，位置、阻断规则、重验收全部按 plan；解析器 923 行改动是**纯解析重构**（无新增门禁/JSON/回执）；测试针对性新增 5 类夹具 + P1 回归，12/12 全绿；对抗探针 CLEAN=`ok` / DIRTY 正确拦截；模板按 plan §3.2 加了非页面提示。

**1 个 P1（R14 遗留未修，本轮实证）**：

- **P1（R14 遗留）**：`--example <example-key>` 在 module pass 下仍被静默忽略。SKILL line 117 原样，实跑 `context-pack --pass module --card scenes --example simple-action` 装载的 6 个 section **不含任何 example section**。第三份 plan §3.1 未安排修它。

> **2026-08-04 订正（P1 已修复）**：经用户授权，P1 已按方案 A 修复并实测验证：
> 1. `skills/spm-prd/SKILL.md` 阶段 C 命令改为 `--pass module --card scenes`（删 `--example <example-key>`，写死 `scenes`），并补说明"示例不作为装载内容，写作难点直接阅读 `references/prd-writing-examples.md` 对应章节"；
> 2. `contracts/context-loading.manifest.json` 删除未被任何 pass 引用的 `prd-examples` pack 与 10 个 `prd-example-*` section 死配置；
> 3. `scripts/python/test-context-loading.py` 的 module case 去掉已无意义的 examples 参数。
> 验证：manifest JSON 有效；`context-pack --pass module --card scenes --dry-run` 正常装载 6 section；12/12 测试全绿；探针 CLEAN=ok / DIRTY 拦截不变。

> **2026-08-04 订正**：初稿中的 P1-B（`evals/judges/*.ps1`）与"范围外新增物"章节已按用户说明撤销——`evals/` 评估框架与根目录 `SKILL.md` 是**外部 CLI（qodercli 评测）自动生成**，不属于 ShitPM 仓库维护内容，不在本轮审查范围，不再作为仓库问题审计。

## 审查范围与方法

| 动作 | 结果 |
|---|---|
| 12 套 `test-*.py` 全量回归 | 全绿（exit=0） |
| 对抗探针 `probe.py` | CLEAN exit=0 **reason=ok**（解析器修复后从 possible_omission 转 ok）/ DIRTY exit=1（4字段+1页面+1状态+STYLE001）|
| context-pack 实跑 `--pass module --card scenes --example simple-action --dry-run` | 装载 6 section（core-boundary/structure/template/profile/action/scenes），**0 个 example section** → P1-A 实证 |
| plan §7 五项解析器修复核对 | 测试夹具逐项对应 + 权限 zero 信号实现确认（line 1882-2000） |
| 范围核查 | 923 行 diff 无新增 JSON/回执/门禁；evals/、根 SKILL.md 为外部 CLI 误入物（已确认非仓库改动，不审计） |

## P1：`--example` 静默失效（R14 遗留，本轮未修，已实证）

- `skills/spm-prd/SKILL.md:117` 仍指示 `--pass module --card <scene-key> --example <example-key>`。
- `contracts/context-loading.manifest.json` 本轮零新增（diff 仅为 R14 已审的 `prd-module-writer` purpose 改动），`prd-examples` pack（10 个 `example_sections`）仍**未被任何 pass 引用**。
- 实跑证据（`--dry-run` 输出）：`requested_packs=[prd-core, prd-writing-structure, prd-writing-action, prd-cards]`，`sections=[prd-core-boundary, prd-writing-structure, prd-template, prd-profile, prd-writing-action, prd-verification-scenes]`——传 `--example simple-action` 前后无差别。
- 建议（同 R14）：方案 A——SKILL 删 `--example <example-key>` + manifest 删未被引用的 `prd-examples` 死配置；方案 B——把 `prd-examples` 挂进 module pass 让参数生效（不推荐，示例非规范）。**本轮 plan 未覆盖此修复，需用户安排**。

## 外部工具误入物（已按用户指示撤销审计）

初稿曾将 `evals/`（含 `judges/check-design.ps1`、`check-prd.ps1`）与根目录 `SKILL.md` 列为仓库问题。经用户确认：这两项是**外部 CLI（qodercli 评测）自动生成**，不属于 ShitPM 仓库维护内容，不构成执行 AI 的越界，**不再审计**。用户已确认"这是错的"，相关清理由外部工具配置层面处理。

## P2：R14 遗留未处理（本轮仍存在）

| 项 | 状态 |
|---|---|
| `--card <scene-key>` 措辞误导（合法值仅 `scenes`） | 未处理，SKILL line 117 |
| `extract_prd_modules` 死路径（line 921/1892，重构后仍在） | 未处理 |
| `context-run.py` 孤儿脚本 | 未处理 |
| STYLE003 表格主导检测锚定标题关键词（style-lint line 171） | 未处理 |
| 中断恢复"最后一个未完成模块"判据未明说 | 未处理（部分缓解：模块完成条件 #1 可作判据） |
| 自检"展示 PRD 前同一写作动作"措辞未适配分片 | 部分缓解（变更失效规则补齐了模块级重验收） |
| 阶段 A 读取 Design 动作未明说 | 部分缓解（阶段 A-1 给了识别路径） |
| `prd-writing-examples.md` small-module 示例跳章 | 未处理（有注释兜底） |

## 已验证通过（正面项）

- **补强一（Design 风险清单）**：SKILL 阶段 A-1 位置正确（全局扫描后、模块写作前）；四类清单（事实冲突/高影响未知/处理结论/模块影响）；识别路径六步；高影响未知五类；阻断规则五条；"不得页面优先/数据字典优先"；明确"临时工作材料，不是新的永久交付物或证明文件"（防越界）。规则 §9 + 事实边界 §5 同步。
- **补强二（非页面字段回读）**：模块完成条件新增 #9——落点 8 类、内部字段 7 类、"不能因无页面控件而删除"、"高影响字段一字段一行、合并仅限完全一致"。规则 §10 同步。模板 line 95 加三条提示（非页面字段入对象定义/一字段一行/合并不掩盖）。
- **补强三（变更失效）**：触发 9 项（含阶段 D 整合修改）；重验收 7 项；Design 上游变化只使受影响模块失效 + 共享引用进入影响评估 + 不得默认全验收；"不得用旧快照或旧哈希掩盖，哈希变化必须说明原因并以后一次重验收为准"。规则 §11 同步。
- **解析器五项修复**：斜杠合并字段（`_split_field_tokens`）、数据字典页面 vs 章节黑名单、状态组合值（`_split_state_tokens`/`extract_prd_state_enum_values`）、同名按对象（`_compare_field_sets`/`_design_field_objects`）、权限 zero → `not_evaluated=True` + "权限无法从当前正文提取，需人工验收"（line 1882-2000）。测试新增夹具逐项对应，12/12 绿。
- **边界守住**：923 行 diff 无新增 JSON/回执/综合门禁；探针 CLEAN 从 possible_omission 转 ok（解析更准）且 DIRTY 拦截能力保留；未修改用户正式 Design/PRD/confirmation；未 commit 未 push。

## 遗留 / 需用户决策

1. **P1 修不修**：`--example` 未修。建议方案 A（删 `--example` + 删 `prd-examples` 死配置）。这是 R14 就已报告的指令骗模型问题，连续两轮未处理。
2. **外部工具误入物（已撤销审计）**：`evals/` 与根目录 `SKILL.md` 是外部 CLI 自动生成，清理由外部工具配置层面处理，与 ShitPM 仓库无关。
3. **行为层真实生成验收仍未做**：plan §14（简单/复杂/中断恢复）与三补强 plan §11-13（简单/复杂样本、变更失效）都要求真实生成，本次仍未实跑。建议 P1 修复后统一安排。
4. 未提交、未推送（符合两 plan 停止条件）。

## 审查所用证据

- 全文：`skills/spm-prd/SKILL.md`（line 45-182）、`references/prd-writing-rules.md`、`templates/prd.md`、`docs/plans/2026-08-04-prd-skill-three-strengthen-plan-and-acceptance.md`。
- diff：`contracts/context-loading.manifest.json`、`scripts/python/prd-consistency-check.py`（函数级）、`scripts/python/test-prd-consistency-semantics.py`、`references/prd-writing-rules.md`、`templates/prd.md`。
- 实跑：12 套测试、`probe.py`、`context-pack.py --dry-run`（--example 实证）。
- 外部物核对（已撤销审计）：`evals/`、根目录 `SKILL.md` 为外部 CLI 生成，确认非仓库改动。
