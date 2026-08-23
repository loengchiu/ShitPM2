# PRD Skill 精简——阶段 0 基线冻结记录

> 日期：2026-08-05  
> 依据计划：`docs/plans/2026-08-05-prd-skill-simplification-execution-and-acceptance.md`  
> 状态：基线已冻结，未提交、未推送

## 一、Git 与工作区

| 项 | 值 |
|---|---|
| 当前分支 | `V2`（跟踪 `origin/V2`） |
| 当前提交 | `df6c178 refactor(context): 移除 context-run.py，优化上下文加载与资源完整性检查` |
| 工作区 | 干净；唯一未跟踪文件为本计划及本基线记录（`docs/plans/2026-08-05-*.md`） |
| 相关分支 | `main=9b26b19`、`park=0bb1a1f`、`vnext-wip-2026-07-27=74bbbf7` |

## 二、真实项目基线

项目：`D:\work\交投软件中心\智慧服务区\智慧停车区`（独立 Git 仓库，master=133d0a7）

### Design confirmation

- `output/design/design.md`：21 页面 / 55 区块 / 298 字段 / 64 操作，1774 行
- confirmation：`hash_match`，当前/确认哈希 `0f375d63bc3d50e9293cf9297f6ed2be8eec7643e14546d9e9b0e2ece847efc3`，确认时间 `2026-08-05T03:01:38+00:00`
- Design 标题结构：业务闭环使用 `### 4.1 车辆进场` 编号式标题（非 `闭环X：名称`）；页面使用 `### 页面：车辆信息记录`

### 现有 PRD 资产（保留，不作为本次四页试写来源，不被覆盖）

| 文件 | 说明 |
|---|---|
| `output/prd/prd.md` | 正式 PRD v5.0（旧 Skill 产物，1665 行） |
| `output/prd/prd-isolated-20260805.md` | 旧 Skill 下的 4.x.6 隔离重写副本（5 模块） |
| `output/prd/rewrite/4.1.6.md` ~ `4.5.6.md` | 隔离重写草稿 |
| `output/prd/prd.md.v32.bak` | v3.2 备份 |
| `output/prd/prd-trial-20260805.md` | 早期试写 |
| `output/prd/decision-notes.md` | 决策记录 |

## 三、上下文预算基线（实测）

测量命令与结果：

| 测量项 | 当前值 | 计划目标上限 |
|---|---:|---:|
| `skills/spm-prd/SKILL.md` 行数 | 202 | 160 |
| `skills/spm-prd/SKILL.md` 字符数 | 12,054 | —（约 2,500 token） |
| writing pass 总 token（`--pass writing --dry-run`） | 12,657 | 6,500 |
| module pass 总 token（页面兜底 `--module 车流实时监控 --pages ...`） | 17,561 | 9,000（同一真实模块总上下文） |
| `--module "车流和车位实时监测"`（编号式闭环） | 失败：匹配不到 | 成功 |

## 四、脚本误判基线样本

### prd-style-lint.py（正式 prd.md）

- 结果：`0 error, 1 warning, 44 info`
- warning：STYLE002 L66 连续 3 个短步骤（误报，业务闭环编号列表）
- info 噪音：STYLE005 L125-L1576 共 44 条“发现跨节引用”（正常内部引用，全部指向真实章节）
- 当前不识别：页面元数据连续块（页面职责/使用对象/入口与返回/区块清单）、UI 动作词直接作动作标题

### prd-consistency-check.py（正式 prd.md，退出码 1）

| 分类 | 数值 | 样本 |
|---|---:|---|
| fields missing/hallucinated | 0 / 0 | — |
| pages | 21/21 匹配 | — |
| states missing | 14 | “停留中、数据异常、离场异常”（“下一状态”列组合值未拆分） |
| states hallucinated | 5 | “保存失败、已保存、已加载、未保存、部分数据缺失”（页面/过程状态误判为业务状态） |
| design_index missing / hallucinated | 362 / 263 | “今日入场车辆”（指标卡片，正文自然语言表达，无字段表落点即判缺失）；字段表无页面位置即判幻觉 |
| design_index matched | 21 / 383 | — |
| possible_omission | 0 | — |
| permissions | cannot_extract（not_evaluated，正确） | — |

## 五、冻结承诺

1. 不修改确认版 `output/design/design.md`。
2. 不覆盖正式 `output/prd/prd.md` 与既有备份。
3. 本专项全部修改只落在 ShitPM `V2` 工作区与真实项目隔离试写位置。
4. 未经用户授权不执行 `git commit`、`git push`。
