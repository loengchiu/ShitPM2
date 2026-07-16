---
name: spm-prd-review
description: "PRD review——判断 PRD 正文质量。用于用户说 prd review、PRD review、review PRD 时。预检查 → 坏味道/三层覆盖/一致性/结构审查。不代写 PRD 正文。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 执行顺序（两段式）

### 第一段：预检查

1. `python $BUNDLE/scripts/python/review-precheck.py --stage prd --no-metadata --stdin-artifact`（agent 已读 prd.md，stdin 传入）→ `.workflow/runtime/prd/review-precheck.json`
2.  脚本失败或 `can_start_review=false` → 停止，输出阻塞项
3. 检查核心章节：详细需求说明（含每个小模块末尾的字段/状态机归位 + 大模块开头的权限规则归位）
4. 运行 `python $BUNDLE/scripts/python/prd-style-lint.py` 检查文风
5. 检查 prd.md 无稳定 ID 泄漏

 有阻塞问题 → 停止，不进入第二段。

### 第二段：人读质量

1. **坏味道**：标签式正文/动作流水账/纯表格/过多加粗/模糊表述
2. **三层覆盖**：界面元素与展示规则/交互逻辑与状态流转/异常处理与边界
3. **一致性（脚本兜底 + LLM 语义增强）**：

   运行确定性结构对比：
   ```bash
   cat output/prd/prd.md | python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .
   ```

   直接引用脚本 JSON 报告中的 missing/hallucinated/attribute_mismatch 项。

   然后 LLM 补充检查（脚本无法覆盖的部分）：
   - 规则 checklist：design rules.json 每条规则 × PRD 正文 → [存在/缺失]

   判定：
   - 脚本报告的 hallucinated 项 = P0
   - 脚本报告的 missing 项 = P1（缺失率 > 50% 升级 P0）
   - 脚本报告的 attribute_mismatch 项 = P1
   - LLM 发现的规则缺失 = P1

4. **结构**：每个小模块末尾含字段定义、状态机归位内容；大模块开头含权限规则归位；状态机按核心业务对象组织，含状态集合/迁移/触发动作和限制条件；权限规则含页面级/按钮级权限

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞**：有 P0 或 2+ 个 P1

| 级别 | 示例 |
|------|------|
| P0 | 核心章节缺失、设计边界违反、幻觉项（PRD 引入 design 不存在的实体）、缺失率>50% |
| P1 | 缺失项（design 有 PRD 没写，但缺失率≤50%）、页面缺展示规则、状态变化缺失 |
| P2 | lint warning、稳定 ID 泄漏（写入 issues 不计 verdict）|

issue_layer：`{"structure":N,"content":N,"consistency":N}`。

## 输出

- 机读：`.workflow/reviews/prd-review-N.json`（stage/verdict/issues/issue_layer/affected_objects/needs_upstream_sync/next_recommended/reviewed_at）
- 人读：`.workflow/reviews/prd-review-N.md`（结论/主要问题/是否回上游/下一步）

 输出 verdict 后停止等用户确认，不自动推进。

## 失败模式

| 场景 | 一线 | 兜底 |
|------|------|------|
| 预检查脚本失败 | 检查路径和环境 | 停下，不跳过 |
| can_start_review=false | 输出阻塞项 | 不绕过 |
| 假阳性 | 列出 warnings 等确认 | 确认后继续 |
| 人读发现 P0 | 输出阻塞 verdict | 停止 |

## 硬规则

1. 不代写 PRD 正文
2. 不自行修改 prd.md
3. 问题具体到页面/章节/内容
4. 预检查失败不跳过
5. P2 写入 issues 但不计入 verdict
6. review 通过后不自动推进
7. 脚本报告的 missing/hallucinated/attribute_mismatch 项逐条列出；为零时直接引用脚本结论
8. LLM 补充检查（规则覆盖）必须逐项列出，不允许笼统结论
9. 幻觉项（PRD 有 design 没有）必须标 P0，不放过
