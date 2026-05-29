---
name: spm-align
description: "对齐阶段——确认目标、范围、边界、建设方式。用于用户说开始对齐、做对齐、需求对齐时，通过结构化追问收集关键信息并生成对齐产物。一次只追一个问题，6 轮未冻结必须暂停。"
triggers:
  - "开始对齐"
  - "做对齐"
  - "需求对齐"
  - "spm-align"
---

# 对齐

## 触发条件

用户要求开始对齐，或 stage-context 建议进入 align 阶段。

## 最小读取集合

🔴 **一次读取**——用一次工具调用读取以下全部文件：

1. .workflow/status.json（当前状态）
2. .workflow/runtime/align/align-notes.json（如存在）
3. references/align-writing.md（写法参考）
4. templates/align.md（产物骨架）

## 执行顺序

### 步骤 1：读取上下文

读取最小读取集合所有文件。

🔴 **检查点：模板可读性**——templates/align.md 和 references/align-writing.md 是否存在且可读？缺失时停下告知用户，不凭记忆生成产物。

### 步骤 2：识别需求

识别用户原始需求和背景材料。

🔴 **检查点：材料充分性**——是否有任何背景材料？完全无材料时，先追问背景再开始对齐，不直接进入信息收集。

### 步骤 3：结构化信息收集

按以下顺序逐项收集：

1. 目标（要做什么）
2. 范围（一期做什么、二期做什么、不做什么）
3. 边界（与现有系统的关系）
4. 建设方式（iteration / new_build / hybrid）
5. 业务阶段

### 步骤 4：ask-back 追问

如有阻塞性缺口，按 ask-back 纪律追问：

1. 只为真实阻塞追问——能从材料中推断的不问
2. 一次只追一个问题——不一次问多个
3. 先查资料，查不出再问 PM
4. 最后一行收口为唯一问题

🔴 **检查点：轮次控制**
- 4 轮以上：必须生成轮次摘要，输出当前已确认项和未确认项
- 6 轮以上：🔴 **必须冻结当前状态**，输出已有成果，建议用户补充材料后再继续。不无限追问。

### 步骤 5：建设类型判断

进入设计前必须完成建设类型判断：

| 类型 | 判断标准 | 追问重点 |
|------|---------|---------|
| iteration | 在现有系统上扩展，有明确挂载点和约束 | 挂载点在哪、约束是什么 |
| new_build | 全新建设 | 模块边界、主流程 |
| hybrid | 部分复用、部分新建 | 哪些复用、哪些新建、怎么对接 |

🔴 **检查点：类型确认**——建设类型判断是否有充分依据？仅凭猜测不得进入设计。

### 步骤 6：上下文自检

退出前必须验证以下字段可支撑"是否可推进"的判断：

- request_summary
- solution_shape
- business_stage
- material_paths
- context_gaps

🔴 **检查点：自检通过**——如有缺失字段，不得建议进入设计，输出缺失项并停下。

### 步骤 7：生成产物并更新状态

1. 写入 output/align/align.md，按 templates/align.md 骨架组织
2. 更新 .workflow/metadata/align/ 下三个机读文件
3. 更新 .workflow/runtime/align/align-notes.json
4. 更新 .workflow/status.json

## 硬规则

1. 一次只追一个问题
2. 6 轮未冻结必须暂停
3. 对齐阶段只写：目标、范围、边界、建设方式、建设类型初判、待确认问题
4. 不展开页面和字段细节
5. 不写 PRD 正文
6. 不做原型表达
7. 不生成稳定 ID
8. 不自动推进到设计阶段

## 产物 Schema

### align-notes.json

```json
{
  "blocking_gaps": ["缺失信息1", "缺失信息2"],
  "needs_ask_back": true,
  "ask_back_reason": "需要确认一期范围边界",
  "can_enter_design": false,
  "judgement_note": "建设类型初判为 iteration，待确认挂载点",
  "ask_back_round": 3,
  "last_updated_at": "2026-05-29T10:00:00+08:00"
}
```

### status.json 相关字段

```json
{
  "current_stage": "align",
  "artifacts": { "align": "output/align/align.md" },
  "metadata_paths": { "align": ".workflow/metadata/align/" },
  "next_recommended": "design",
  "align_notes": ".workflow/runtime/align/align-notes.json"
}
```

## 停止条件

满足以下全部 4 条后输出产物并停止：

1. 已完成目标、范围、边界、建设方式确认
2. 建设类型初判完成
3. 上下文自检通过
4. 无真实阻塞缺口

## 不要做什么

- 不重新定义已确认的范围
- 不展开页面和字段细节
- 不写 PRD 正文
- 不做原型表达
- 不自动推进到设计阶段
- 不一次追问多个问题
- 不在材料不足时凭猜测补全信息
- 不跳过建设类型判断直接进入设计
