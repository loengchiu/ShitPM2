---
name: spm-start
description: 启动阶段——识别当前项目、当前阶段、当前可继续的入口
triggers:
  - "启动"
  - "开始"
  - "当前状态"
---

# 启动

## 触发条件

用户要求启动或查看当前状态。

## 最小读取集合

1. `.workflow/status.json`（如不存在，进入新项目扫描流程）

## 新项目扫描流程

当 `.workflow/status.json` 不存在时，按以下顺序扫描并推断：

1. 扫描 `output/` 目录，检查各阶段人读产物是否存在：
   - `output/align/align.md`
   - `output/design/design.md`
   - `output/prd/prd.md`
   - `output/prototype/index.html`
2. 扫描 `.workflow/metadata/` 目录，检查各阶段机读物是否存在
3. 扫描 `.workflow/reviews/` 目录，检查是否有 review 结果
4. 按主链路顺序判断当前阶段：
   - 产物全空 → 当前阶段：对齐，下一步：开始对齐
   - 仅 align 存在 → 当前阶段：设计，下一步：开始设计
   - design 存在但无 review → 当前阶段：设计 review，下一步：执行设计 review
   - design review 通过但无 PRD/prototype → 当前阶段：PRD 或 prototype，下一步：生成 PRD 或 prototype
   - PRD 存在但无 review → 当前阶段：PRD review，下一步：执行 PRD review
   - PRD review 通过 → 当前阶段：原型或同步修复，下一步：生成 prototype 或等待变更
5. 按判断结果初始化 `.workflow/status.json` 的初始结构

## 执行顺序

### 有 status.json 时：

1. 读取 `.workflow/status.json`
2. 判断当前阶段
3. 检查各阶段产物存在情况
4. 读取最近一次 review 结果（如存在）
5. 读取对齐阶段判断记录（如存在）
6. 输出下一步唯一建议

### 无 status.json 时（新项目）：

1. 执行新项目扫描流程
2. 推断当前阶段
3. 输出下一步唯一建议
4. 不创建 `.workflow/status.json`（由 writer 阶段首次产出时创建）

## 输出要求

输出包含以下信息：

- 当前阶段
- 各阶段人读产物路径
- 各阶段机读物路径
- 最近一次 review 结果
- 对齐阶段判断记录（如存在）
- 下一步唯一建议

## 硬规则

1. 不做需求判断
2. 不做写作质量判断
3. 不做 reviewer 职责
4. 不修改任何文件

## 停止条件

输出当前状态和下一步建议后停止。
