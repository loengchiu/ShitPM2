---
name: spm-align
description: "可选需求整理模块——整理目标、范围、背景、已有材料和不确定点。vNext 中 Align 不是 Design 的硬前置；用户可跳过 Align 直接进入 Design。不承担最终业务流程、权限、状态和方案决策。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 模型建议（运行时输出）

流程开始时输出模型等级和推理深度建议（直接复用 PRD §6.3 推荐矩阵）：

- **轻量模型**：目标、范围和边界已经明确，仅需整理材料
- **深度推理模型**：存在明显冲突、范围不清或复杂业务背景；无法判断时使用深度推理模型

建议必须是实际运行输出，不只是背景说明。

## 职责边界

vNext：Align 是**可选**的需求整理模块，不是 Design 的硬前置。

- **只整理**：目标、范围、背景、已有材料、不确定点
- **不承担**：最终业务流程、权限、状态、模块边界、跨系统责任、方案权衡等设计决策
- **不强制**：固定问答、固定字段密度、固定轮次、固定前置依赖

用户可以：
- 跳过 Align 直接进入 Design
- 只整理部分维度后进入 Design
- 在 Design 过程中回过头来补充 Align

## 输入事实源

读取以下文件（模板/参考不存在时停下告知缺失路径，不凭记忆生成）：

1. `.workflow/status.json`（如存在）
2. `.workflow/runtime/align/align-notes.json`（如存在）
3. `references/align-writing.md`（如存在）
4. `templates/align.md`
5. 用户提供的背景材料（文件路径、链接、原话摘要）

## 整理要求

按用户当前问题的实际复杂度决定整理深度，**不强制覆盖固定维度**。可参考的整理维度（按需选择，不要求全部完成）：

- **目标**：这个需求要解决什么问题
- **范围**：一期做什么、不做什么
- **边界**：和哪些系统有交互、数据边界、用户边界
- **建设方式**：在现有系统上扩展还是新建
- **已有材料**：用户提供的资料清单
- **不确定点**：用户尚未明确的问题

**整理原则**：
- 能从用户提供的资料查到的，直接查不问
- 已明确的部分直接写入 align.md，不重复追问
- 用户回答"跳过"后标"待确认"，不强行追问
- 真实阻塞的项才追问；用户表示"先这样"或"进入 Design"时立即停止

## 失败模式

| 场景 | 一线 | 兜底 |
|------|------|------|
| 模板缺失 | 内置最小模板 | 停下，要求安装 |
| 参考缺失 | 跳过参考 | — |
| notes.json 损坏 | 备份后重建 | 停下让用户手动修复 |
| 用户输入自相矛盾 | 列出矛盾，追问 | 最保守策略记录两种可能 |
| 用户表示跳过 Align | 直接冻结，输出最小 align.md（或跳过不写） | — |

## 产物

| 序号 | 文件 | 来源 |
|------|------|------|
| 1 | `output/align/align.md` | 按 `templates/align.md` 骨架 |
| 2 | `.workflow/runtime/align/align-notes.json` | 判断结果（AI 直接写入，schema 见 `schemas/align-notes.schema.json`） |
| 3 | `.workflow/status.json` | 首次创建或更新（AI 直接写入 current_stage、artifacts.align） |

### align-notes.json 字段参考

```json
{"blocking_gaps":[],"needs_ask_back":false,"ask_back_reason":null,"judgement_note":"","last_updated_at":"2026-07-02T10:00:00Z"}
```

完整 schema 定义见 `$BUNDLE/schemas/align-notes.schema.json`。

## 完成报告

输出完成后告知用户：
- Align 已完成（或已跳过）
- 可直接调用 `/spm-design` 进入 Design（无需 Align "通过"或"完成"作为前置）

## 停止条件

满足以下任意一条即可停止：
1. 用户明确表示"进入 Design"或"完成 Align"
2. 目标/范围/边界/建设方式中至少 3 项已确认，且无阻塞性缺口
3. 用户表示"先这样"，记录当前状态并冻结

## 不要做什么

| # | 反模式 | 替代 |
|---|--------|------|
| 1 | 凭猜测补全信息 | 追问或标"待确认" |
| 2 | 强制覆盖所有维度 | 按用户实际复杂度决定整理深度 |
| 3 | 展开页面/字段细节（页面布局、字段定义、按钮文案、状态迁移表） | 这些是 Design 的职责 |
| 4 | 重新定义已确认范围 | 记录原话不改写 |
| 5 | 无限追问 | 用户表示"先这样"立即停止 |
| 6 | 自动推进 design | 停下等触发 |
| 7 | 写 PRD 或原型 | 严格限需求整理维度 |
| 8 | 把 Align 当成 Design 的硬前置 | Align 是可选模块，用户可跳过 |
| 9 | 把 align-notes.json 当作 Design 准入门禁 | align-notes.json 只是整理结果记录，不是 Design 准入条件；用户随时可进入 Design，不读取 align-notes.json 判断是否可进入 Design |
