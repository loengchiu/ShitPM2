# PRD 对象单元重构验收报告

日期：2026-11-01

## 1. 结论

| 层级 | 结论 | 依据 |
|---|---|---|
| 规范层 | 通过（本轮范围） | PRD 写作、Review、Design 对象卡和测试级歧义规则已写入运行时文件，禁用项与必需项一致 |
| 实现层 | 通过 | 标题名定位、严格对象单元结构、页面标题落点、目标模块切片和旧结构未检查均有回归测试；PRD、Design 索引和装载测试通过 |
| 产物层 | 部分通过 | 两个试点的产品负责人真人试读已通过；要求的 T-9 新会话复现尚未执行 |
| 本轮总状态 | 部分完成 | T-0 至 T-8 完成；T-4 的三角色逐题记录按用户确认不作为本轮阻碍；T-9 未执行，T-10 按部分完成收口 |

本报告不宣布所有项目 PRD 已完成迁移，也不宣布 Design 已无歧义。

## 2. 规范层

### 2.1 PRD

权威文件：

- `D:/work/ShitPM/references/prd-writing-rules.md`
- `D:/work/ShitPM/references/prd-writing-examples.md`
- `D:/work/ShitPM/templates/prd.md`
- `D:/work/ShitPM/skills/spm-prd/SKILL.md`
- `D:/work/ShitPM/skills/spm-prd-review/SKILL.md`
- `D:/work/ShitPM/contracts/prd-review-checklist.md`
- `D:/work/ShitPM/contracts/prd-writing.profile.json`

结构为模块概览、对象单元、共用规则、页面功能、跨对象异常。对象单元固定使用业务过程、状态迁移、对象规则、异常与边界、验收场景、待确认六个职责槽位。对象单元必须位于功能需求模块范围内，附录中的示例对象不计入。

已删除或禁止：

- 验收场景规则 ID、验证包位置和追溯说明。
- 页面区块的“所属对象”“只读承接”等内部标注。
- 同一组数值在对象规则和验收场景重复。
- 空章节、作者说明、过程记录。
- 对 `4.x.3`、`4.x.5`、`4.x.6`、`4.x.9` 等固定末位编号的阅读依赖。

运行时样板已补齐页面清单的名称、终端、任务和结果去向，角色矩阵已改为“可、否或条件”，对象规则不再重复页面默认值、字段限制、保存保护和跨对象异常。

### 2.2 Design

已增量修改八个 Design 运行时文件：

- `references/design-writing.md`
- `references/design-business-closure.md`
- `references/design-fact-format.md`
- `references/design-quality-rubric.md`
- `contracts/design-review-checklist.md`
- `templates/design-module.md`
- `skills/spm-design/SKILL.md`
- `skills/spm-design-review/SKILL.md`

新增责任：

- 每个独立对象写对象卡，锁住生命周期边界、状态、终态、迁移表位置、归属页面和引用共用规则。
- 页面清单和页面区块写所属对象。
- 未决事项写可选答案及各自后果，不只写推荐答案。
- 复杂规则探测触发时机、舍入与尾差顺序、人工覆盖边界、并发批次可见性。

## 3. 实现层

### 3.1 标题名定位

`scripts/python/prd-consistency-check.py` 已按标题名定位：

- 模块概览。
- 业务过程。
- 状态迁移。
- 对象规则。
- 异常与边界。
- 验收场景。
- 页面功能。
- 共用规则。
- 跨对象异常。

页面正文落点只读取“页面功能”下一级页面标题，正文提到页面名不能替代标题。状态迁移读取“状态迁移”表。角色权限事实读取“角色与能力矩阵”或其他权限标题。

`--module` 现在会先切出目标 PRD 模块，并把 Design 索引过滤到目标模块，再执行结构、页面、字段、状态和 Design 索引比对；其他模块内容不能污染目标模块。PRD 含多个模块但未指定 `--module` 时输出 `not_evaluated`，不执行全文误判。

### 3.2 旧结构处理

D-8 采用 B。PRD 缺少完整对象单元结构时：

- 模块概览、页面功能、对象单元及其直接子槽位按标题名识别。
- 每个对象单元必须直接包含业务过程、对象规则和验收场景；状态迁移、异常与边界、待确认按适用性保留。
- 退出码为 0。
- `evaluation_status`、`structure_evaluation.status`、`summary.check_status` 和 `exit_reason` 均为 `not_evaluated`。
- 不输出冲突、遗漏或通过结论。
- Design 索引损坏等输入错误仍在结构判断前返回致命错误，不会被“未检查”掩盖。

### 3.3 针对性验证

| 检查 | 结果 |
|---|---|
| `test-prd-consistency-semantics.py` | PASS |
| `test-prd-style-lint.py` | PASS |
| `test-prd-simplification.py` | PASS |
| `test-context-loading.py` | PASS |
| `test-design-index.py` | 27 项通过 |
| `test-design-set.py` | 20 项通过 |
| `test-resource-integrity.py` | PASS |
| 租金试点样式检查 | 无问题 |
| 停车试点样式检查 | 无问题 |
| 规范样板样式检查 | 无问题 |
| manifest、profile JSON 解析 | PASS |
| writing、module scenes、module data dry-run | PASS |
| 重编号功能需求 lint 回归 | PASS |
| `git diff --check` | PASS |

基线失败与本轮结果见 `.tmp/prd-object-unit/T7-checks.md`。

### 3.4 复审后修复

- 对象结构判定改为按对象单元直接子槽位核对，并要求对象单元位于功能需求模块范围内，杜绝“模块概览、页面功能和任意两个槽位”或附录示例对象误判为已检查。
- 清理 Fix 中残留的 PRD `4.x.9` 依赖，改为同步受影响对象单元的验收场景。
- 修复 context 契约、PRD Skill 装载入口、验证包锚点、样板图片引用和三份长文目录；`test-resource-integrity.py` 已通过。
- 页面正文落点改为页面标题匹配；页面只出现在其他页面正文或完全缺失时均报告落点遗漏。
- `--module` 在 PRD 读取后即切片，页面、字段、状态和 Design 索引比较使用同一目标模块。
- PRD Review 的对象单元阅读范围笔误已修正；流程图改为按适用性触发。
- 功能需求标题编号、样式检查提示和 profile 配置已解除固定 `4.x` 依赖，并增加重编号回归。
- T-4 按用户 2026-11-01 确认不作为本轮验收阻碍，相关逐题原始记录不在本报告重复展开。

## 4. Design 歧义探测

租金清分隔离副本：

- 源文件 SHA256：`3cc48b3d6fb6c65963fe2e701807036a4d0e83f61fc3fb7ed7832dd1798d9143`
- 探测记录：`.tmp/prd-object-unit/design-probe/probe-record.md`
- 带结论副本：`.tmp/prd-object-unit/design-probe/租金清分.probe.md`

命中三项：

1. 提成账单在上游数据晚到后何时生成。
2. 提成金额、账单应收和分月收入的舍入与尾差顺序。
3. 新增租金账单的手工金额允许边界。

三项均写明可选答案及对页面、状态、金额、报表或验收的后果，均未选择方案。正式租金清分 Design 未修改。

## 5. 产物层

### 5.1 已完成的真人试读

试读文件：

- `.tmp/prd-object-unit/rent/pilot.md`
- `.tmp/prd-object-unit/parking/pilot.md`

产品负责人真人反馈：

> 我试读了，我觉得通过了，继续吧。

记录位置：`.tmp/prd-object-unit/trial/human/pm-self-review.md`。

用户已确认 T-4 不再作为本轮验收阻碍。本报告保留产品负责人自读事实，不把缺少三角色逐题原始记录引用的结论写成失败，也不用它替代尚未执行的 T-9。

### 5.2 未执行

T-9 要求全新会话只依据运行时规范和隔离 Design 副本重新生成两个试点。当前线程已有完整修改与试读历史，不能提供独立证据。

未执行记录：`.tmp/prd-object-unit/regen/T9-pending.md`。

因此产物层只判“部分通过”，不能用 T-3 的真人试读替代 T-9。

## 6. 仍未验证

- 租金清分三个歧义尚未由业务负责人决定，正式 Design 未修复。
- 其他项目和模块尚未按新结构重生成。
- 正式租金清分、停车区 PRD、Design、Prototype、标注版、讲解稿和验证包未修改。
- Prototype 和标注版是否引用旧章节编号尚未扫描。
- `C:/Users/guduj/.agents/skills` 的全局 Skill 副本未同步。
- T-9 新会话结构复现和单一归属抽查未完成。

## 7. 后续顺序

1. 新建独立任务执行 T-9，只读运行时规范和隔离 Design 副本，不复用本线程历史。
2. T-9 通过后，补做 T-10 产物层结论。
3. 三个租金歧义由业务负责人分别决定，再在租金清分项目用 `spm-fix` 回写 Design。
4. 正式项目按模块逐个迁移，不批量重写已有 PRD。
5. Prototype、标注版和讲解稿在正式 PRD 重生成前扫描旧章节引用。

## 8. 交付边界

- 未执行 `git commit`、`git push`、`git reset` 或 `git checkout --`。
- 正式项目文件保持只读。
- 工作区中 `contracts/fix-propagation-rules.md`、`references/align-writing.md`、`skills/spm-fix/SKILL.md` 等并发修改不属于本任务，未覆盖或回退。