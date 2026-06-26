---
name: spm-align
description: "对齐阶段——确认目标、范围、边界、建设方式。用于用户说开始对齐、做对齐、需求对齐时，或 stage-context 建议进入 align 阶段时。一次只追一个问题，6 轮未冻结必须暂停。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 最小读取集合

**一次读取**：
1. `.workflow/status.json`
2. `.workflow/runtime/align/align-notes.json`（如存在）
3. `references/align-writing.md`
4. `templates/align.md`

 模板/参考不存在时停下告知缺失路径，不凭记忆生成。

## 执行顺序

### 步骤 1：读取上下文 → 步骤 2：识别需求

```
需求识别结果：
- 原始需求：[用户原话摘要]
- 背景材料：[文件路径或"无"]
- 初步理解：[一句话概括]
```

 无任何背景材料时先追问背景，不直接开始收集。

### 步骤 3：结构化信息收集（逐项）

| 序号 | 收集项 | 输出 |
|------|--------|------|
| 1 | 目标 | 一句话目标 |
| 2 | 范围 | 三列：期内/期外/明确不做 |
| 3 | 边界 | 系统关系、数据边界、用户边界 |
| 4 | 建设方式 | iteration/new_build/hybrid + 理由 |
| 5 | 业务阶段 | 当前阶段与约束 |

 5 项全完成才进入步骤 4。

### 步骤 4：ask-back 追问

只为真实阻塞追问。一次只问一个问题，先查资料再问 PM。格式固定：

```
[轮次 N] 需要确认：
问题：[唯一问题]
背景：[为什么需要确认]
影响：[不确认的后果]
```

 4 轮以上必须生成轮次摘要。**6 轮以上强制冻结**，输出 best-effort 对齐稿，不无限追问。

### 步骤 5：建设类型判断

| 类型 | 判断 | 输出 |
|------|------|------|
| iteration | 现有系统扩展 | 写明挂载点+约束 |
| new_build | 全新建设 | 写明边界+主流程 |
| hybrid | 部分复用 | 写明复用/新建/对接 |

 凭猜测不得进入设计，判断写入 `judgement_note`。

### 步骤 6：上下文自检

| 必填字段 | 缺失动作 |
|---------|---------|
| request_summary（>10 字符） | 追问需求描述 |
| solution_shape（含建设方式） | 补充判断 |
| business_stage | 追问业务阶段 |
| material_paths（≥1 项或"无材料"） | 确认 |
| context_gaps（阻塞性缺口为空） | 列出缺口 |

 有缺失不得建议进入 design。

### 步骤 7：生成产物

| 序号 | 文件 | 来源 |
|------|------|------|
| 1 | `output/align/align.md` | 按 `templates/align.md` 骨架 |
| 2 | `.workflow/metadata/align/index.json` | 结构化提取 |
| 3 | `.workflow/metadata/align/entities.json` | 实体 |
| 4 | `.workflow/metadata/align/relations.json` | 关系 |
| 5 | `.workflow/runtime/align/align-notes.json` | 判断结果 |
| 6 | `.workflow/status.json` | 更新 current_stage |

## 失败模式

| 场景 | 一线 | 兜底 |
|------|------|------|
| 模板缺失 | 内置最小模板 | 停下，要求安装 |
| 参考缺失 | 跳过参考 | — |
| notes.json 损坏 | 备份后重建 | 停下让用户手动修复 |
| 用户输入自相矛盾 | 列出矛盾，追问 | 最保守策略记录两种可能 |
| 轮次超限（>6） | 强制冻结 | 建议补充材料后重新运行 |
| metadata 写入失败 | 创建目录后重试 | 告知不影响人读 |

## 硬规则

1. 一次只追一个问题
2. 6 轮未冻结必须暂停
3. 只写：目标/范围/边界/建设方式/建设类型初判/待确认
4. 不展开页面和字段细节
5. 不写 PRD 正文、不做原型、不生成稳定 ID
6. 不自动推进到 design

## 产物 Schema

### align-notes.json
```json
{"blocking_gaps":[],"needs_ask_back":true,"ask_back_reason":"","can_enter_design":false,"judgement_note":"","ask_back_round":0,"last_updated_at":""}
```

## 停止条件

同时满足：① 目标/范围/边界/建设方式已确认 ② 建设类型初判完成 ③ 自检通过 ④ 无阻塞缺口。

## 不要做什么

| # | 反模式 | 替代 |
|---|--------|------|
| 1 | 一次问多个问题 | 每次一个 |
| 2 | 凭猜测补全信息 | 追问或标"待确认" |
| 3 | 跳过建设类型判断 | 步骤 5 必须完成 |
| 4 | 展开页面/字段细节 | 只写四要素 |
| 5 | 重新定义已确认范围 | 记录原话不改写 |
| 6 | 无限追问（>6） | 强制冻结 |
| 7 | 自动推进 design | 停下等触发 |
| 8 | 写 PRD 或原型 | 严格限四要素 |
