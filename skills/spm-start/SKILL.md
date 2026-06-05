---
name: spm-start
description: "启动阶段——识别当前项目、当前阶段、当前可继续的入口。用于用户说启动、开始、当前状态、看看进度时，扫描 workflow 产物推断阶段并给出唯一下一步建议。不修改任何文件，不做需求判断。"
triggers:
  - "启动"
  - "开始"
  - "当前状态"
  - "看看进度"
  - "spm-start"
---

# 启动

## 触发条件

用户要求启动、查看当前状态、或问现在到哪了。

## 最小读取集合

🔴 **一次读取**——用一次工具调用读取以下文件：

1. `.workflow/status.json`（如不存在，进入新项目扫描流程）
2. `output/` 目录下各阶段产物（存在则读，不存在则跳过）
3. `.workflow/reviews/` 目录下最近一次 review 结果（存在则读）

## 执行顺序

### 路径 A：有 status.json

1. 读取 `.workflow/status.json`
2. 🔴 **CHECKPOINT · JSON 合法性**——如解析失败，走路径 C
3. 读取 `current_stage` 字段，确定当前阶段
4. 扫描对应阶段的产物文件是否存在
5. 读取最近一次 review 结果（如存在）
6. 读取对齐阶段判断记录（如存在）
7. 🔴 **CHECKPOINT · 状态一致性**——status.json 声称的阶段与实际产物是否匹配（如 status 说 design 已完成但 `output/design/design.md` 不存在），不匹配时走路径 D
8. 输出下一步唯一建议后停止

### 路径 B：无 status.json（新项目）

1. 扫描 `output/` 目录，检查各阶段人读产物是否存在：
   - `output/align/align.md`
   - `output/design/design.md`
   - `output/prd/prd.md`
   - `output/prototype/index.html`
2. 扫描 `.workflow/metadata/` 目录，检查各阶段机读物是否存在
3. 扫描 `.workflow/reviews/` 目录，检查是否有 review 结果
4. 按主链路顺序判断当前阶段：

| 产物状态 | 当前阶段 | 下一步建议 |
|---------|---------|-----------|
| 产物全空 | 对齐 | `/spm-align` |
| 仅 align 存在 | 设计 | `/spm-design` |
| design 存在但无 review | 设计 review | `/spm-design-review` |
| design review 通过但无 PRD/prototype | PRD 或 prototype | `/spm-prd` 或 `/spm-prototype` |
| PRD 存在但无 review | PRD review | `/spm-prd-review` |
| PRD review 通过 | 原型或同步修复 | `/spm-prototype` 或等待变更 |

5. 输出下一步唯一建议后停止
6. **不创建** `.workflow/status.json`（由 writer 阶段首次产出时创建）

### 路径 C：status.json 解析失败

1. 告知用户：`.workflow/status.json` 内容损坏，JSON 解析失败
2. 展示原始文件内容（前 500 字符）供用户判断
3. 建议：手动修复 JSON 或删除后重新走新项目扫描
4. 停止，不尝试自动修复

### 路径 D：状态与产物不一致

1. 告知用户具体不一致项（如 status 声称 design 阶段已完成，但 `output/design/design.md` 不存在）
2. 给出两种处理建议：
   - 回退：将 status.json 的 `current_stage` 回退到实际产物支持的阶段
   - 补建：手动补建缺失产物
3. 停止，等用户决定

## 输出格式

输出必须包含以下固定结构：

```
## 项目状态

- 当前阶段：[阶段名]
- status.json：存在/不存在

## 产物清单

| 阶段 | 人读产物 | 机读产物 | Review |
|------|---------|---------|--------|
| 对齐 | ✅/❌ | ✅/❌ | — |
| 设计 | ✅/❌ | ✅/❌ | ✅/❌/— |
| PRD | ✅/❌ | ✅/❌ | ✅/❌/— |
| 原型 | ✅/❌ | ✅/❌ | ✅/❌/— |

## 最近 Review

[review 结果摘要或"无"]

## 对齐判断

[align-notes 摘要或"无"]

## 下一步建议

唯一建议：[具体操作]
```

## 失败模式与 Fallback

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|---------|---------|-----------|
| status.json 不存在 | `.workflow/status.json` 文件不存在 | 走路径 B（新项目扫描） | —— |
| status.json 解析失败 | JSON 格式错误 | 走路径 C，展示原始内容 | —— |
| 状态与产物不一致 | status 声称的阶段与实际产物不匹配 | 走路径 D，列出不一致项 | —— |
| output/ 目录不存在 | `output/` 目录不存在 | 当作产物全空，走路径 B | —— |
| reviews/ 中 JSON 损坏 | review 结果文件解析失败 | 跳过该 review，继续扫描其他文件 | 告知用户哪个 review 文件损坏 |
| 多个 review 文件存在 | 同一阶段有多个 review | 取序号最大的（最新） | —— |

## 硬规则

1. 不做需求判断
2. 不做写作质量判断
3. 不做 reviewer 职责
4. 不修改任何文件——只读取和输出
5. 路径 C/D 情况下不尝试自动修复，只报告和建议

## 停止条件

输出当前状态和下一步建议后停止。不追加多余解释。

## Shell 环境规则

🔴 **Codex 默认 shell 为 PowerShell**——不要用 Unix 命令（head、cat、find），用 Get-ChildItem / Select-String。

## 不要做什么

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|--------|------------|---------|
| 1 | 自动创建或修改 status.json | status.json 应由 writer 阶段首次产出时创建 | 只读取，不写入 |
| 2 | 猜测用户意图 | 用户可能只是想看状态，不代表要推进 | 输出状态后停下，等用户明确指令 |
| 3 | 展开阶段内部细节 | 那是对应 skill 的职责，越界会干扰用户 | 只输出当前阶段和下一步建议 |
| 4 | 自行决定回退到哪个阶段 | 回退策略应由用户决定 | 列出不一致项，给出两种建议，等用户选 |
| 5 | 跳过 JSON 合法性检查 | 可能读到损坏数据导致误判 | 先验证 JSON 格式，失败走路径 C |