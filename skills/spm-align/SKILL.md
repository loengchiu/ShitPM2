---
name: spm-align
description: "可选需求整理模块——整理目标、范围、背景、已有材料和不确定点。用于需求尚未成形、需要先澄清边界或整理输入时；Align 不是 Design 的硬前置，不承担最终流程、权限、状态或方案决策。"
---

## 路径与资源

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:`，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`schemas/`、`lib/` → `$BUNDLE/`
- `.workflow/`、`output/` → 当前项目根目录

流程开始时输出模型建议：目标、范围和边界明确时可用轻量模型；存在冲突、范围不清或复杂背景时使用深度推理模型；无法判断时使用深度推理模型。

## 职责边界

Align 是可选的需求整理模块，不是 Design 的硬前置。

- 只整理目标、范围、背景、已有材料和不确定点。
- 不承担最终业务流程、权限、状态、模块边界、跨系统责任或方案权衡。
- 不强制固定问答、字段密度、轮次或前置依赖。
- 用户可以跳过 Align、只整理部分维度，或在 Design 中回补 Align。

## 输入事实源

按以下顺序读取；模板缺失时报告具体路径，不凭记忆生成完整产物：

1. `.workflow/status.json`（如存在）
2. `.workflow/runtime/align/align-notes.json`（如存在）
3. `$BUNDLE/references/align-writing.md`（如存在）
4. `$BUNDLE/templates/align.md`
5. `$BUNDLE/schemas/align-notes.schema.json`（JSON 结构的唯一来源）
6. 用户提供的背景材料、文件路径、链接和原话

## 执行流程

1. 从用户材料中直接提取已确认事实，不重复追问；不要改写已确认范围。
2. 按实际复杂度选择需要整理的维度：目标、范围、边界、建设方式、已有材料、不确定点；不强制全部覆盖。
3. 能从材料查到的内容直接查，不因整理方便而追问；只对真实阻塞追问。
4. 用户说“跳过”“先这样”或“进入 Design”时立即冻结当前结果，不无限追问。
5. 按 `$BUNDLE/templates/align.md` 写入 `output/align/align.md`；用户明确跳过时可记录跳过，不把 Align 伪装成已完成。
6. 按 `$BUNDLE/schemas/align-notes.schema.json` 写入或更新 `.workflow/runtime/align/align-notes.json`。该文件只记录整理结果和未解决问题，不是 Design 准入门禁。
7. 首次产出时创建或更新 `.workflow/status.json`：`current_stage=align`，`artifacts.align=output/align/align.md`。

## 产物与完成报告

- `output/align/align.md`：按 `$BUNDLE/templates/align.md` 组织的人读整理稿。
- `.workflow/runtime/align/align-notes.json`：按 schema 组织的内部判断记录。
- `.workflow/status.json`：导航状态和产物路径。

完成后告知用户 Align 已完成或已跳过，并说明可直接调用 `/spm-design`，无需 Align 作为准入门禁。

## 输出与停止

满足以下任一条件即可停止：

- 用户明确表示进入 Design 或完成 Align。
- 目标、范围、边界、建设方式至少 3 项已确认且没有阻塞缺口。
- 用户表示“先这样”，记录状态并冻结。

## 失败处理与禁止事项

- 模板缺失：报告具体路径并停止；若运行环境提供明确的最小 fallback，只能用于保持核心边界，仍不得凭记忆生成完整设计。
- 参考缺失：可跳过参考，但必须保持本 Skill 的核心边界规则。
- `align-notes.json` 损坏：先报告损坏内容；在可安全保留旧文件的前提下备份并按 schema 重建，重建失败则停止，请求用户处理。
- 输入矛盾：列出矛盾并追问；无法追问时记录多种可能，不擅自定案。
- 不展开页面、字段、按钮、状态迁移和业务流程细节。
- 不自动进入 Design，不写 PRD 或 Prototype，不把 Align 重新定义为硬前置。
