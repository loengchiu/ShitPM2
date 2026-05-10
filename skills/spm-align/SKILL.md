---
name: spm-align
description: 对齐阶段——确认目标、范围、边界、建设方式
triggers:
  - "开始对齐"
  - "做对齐"
  - "需求对齐"
---

# 对齐

## 触发条件

用户要求开始对齐，或 stage-context 建议进入 align 阶段。

## 最小读取集合

1. `.workflow/status.json`（当前状态）
2. `.workflow/runtime/align/align-notes.json`（如存在）
3. `references/align-writing.md`（写法参考）
4. `templates/align.md`（产物骨架）

## 执行顺序

1. 读取最小读取集合
2. 识别用户原始需求和背景材料
3. 按以下顺序收集信息：
   - 目标（要做什么）
   - 范围（一期做什么、二期做什么、不做什么）
   - 边界（与现有系统的关系）
   - 建设方式（iteration / new_build / hybrid）
   - 业务阶段
4. 如有阻塞性缺口，按 ask-back 纪律追问
5. 生成对齐产物
6. 更新 align-notes.json
7. 更新 status.json

## 硬规则

### ask-back 纪律

1. 只为真实阻塞追问——能从材料中推断的不问
2. 一次只追一个问题——不一次问多个
3. 先查资料，查不出再问 PM
4. 最后一行收口为唯一问题

### 建设类型判断

进入设计前必须完成建设类型判断：

- `iteration`：在现有系统上扩展，有明确挂载点和约束
  - 追问重点：挂载点在哪、约束是什么
- `new_build`：全新建设
  - 追问重点：模块边界、主流程
- `hybrid`：部分复用、部分新建
  - 追问重点：哪些复用、哪些新建、怎么对接

### 产出约束

1. 对齐阶段只写：目标、范围、边界、建设方式、建设类型初判、待确认问题
2. 不展开页面和字段细节
3. 不写 PRD 正文
4. 不做原型表达
5. 不生成稳定 ID

### 轮次控制

- 4 轮以上：必须生成轮次摘要
- 6 轮以上：必须冻结状态后再决定是否继续

### 上下文自检

退出前必须验证以下字段可支撑"是否可推进"的判断：

- `request_summary`
- `solution_shape`
- `business_stage`
- `material_paths`
- `context_gaps`

如有缺失，不得建议进入设计。

## 输出要求

### 人读产物

写入 `output/align/align.md`，按 `templates/align.md` 骨架组织。

### 机读产物

1. `.workflow/metadata/align/index.json`
   - 包含：`request_summary`、`solution_shape`、`business_stage`、`context_gaps`
2. `.workflow/metadata/align/entities.json`
   - 包含：`system_or_page_clues`、`material_paths`、已确认角色/场景/关键对象
3. `.workflow/metadata/align/relations.json`
   - 包含：来源关系、承接关系、线索到对象映射
4. `.workflow/runtime/align/align-notes.json`
   - 包含：`blocking_gaps`、`needs_ask_back`、`ask_back_reason`、`can_enter_design`、`judgement_note`、`last_updated_at`

### 状态更新

更新 `.workflow/status.json`：

- `current_stage`：保持 `"align"`
- `artifacts.align`：指向 `output/align/align.md`
- `metadata_paths.align`：指向 `.workflow/metadata/align/`
- `next_recommended`：
  - 如 `can_enter_design` = true → `"design"`
  - 如 `needs_ask_back` = true → `"align"`（继续对齐）
- `align_notes`：来自 `align-notes.json`

## 停止条件

1. 已完成目标、范围、边界、建设方式确认
2. 建设类型初判完成
3. 上下文自检通过
4. 无真实阻塞缺口

满足以上 4 条后输出产物并停止，建议进入设计阶段。

## 明确不做什么

1. 不重新定义已确认的范围
2. 不展开页面和字段细节
3. 不写 PRD 正文
4. 不做原型表达
5. 不自动推进到设计阶段
