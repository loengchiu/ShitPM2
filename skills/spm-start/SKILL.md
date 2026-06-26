---
name: spm-start
description: "启动阶段——识别当前项目阶段，给唯一下一步建议。用于用户说启动、开始、当前状态、看看进度时。不修改文件，不做需求判断。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 最小读取

**一次读取**：
1. `.workflow/status.json`（不存在 → 走路径 B）
2. `output/` 下各阶段产物（存在则读）
3. `.workflow/reviews/` 下最近 review（存在则读）

## 执行路径

### 路径 A：有 status.json

1. 读 `.workflow/status.json`。 JSON 解析失败 → 路径 C
2. 读 `current_stage`
3. 扫描对应产物是否存在
4. 读最近 review
5.  状态与产物不一致 → 路径 D
6. 输出下一步唯一建议

### 路径 B：无 status.json（新项目/扫描）

扫描 `output/` 产物判断当前阶段：

| 产物状态 | 当前阶段 | 下一步 |
|---------|---------|--------|
| 全空 | 对齐 | `/spm-align` |
| 仅 align | 设计 | `/spm-design` |
| design 存在，无 review | 设计 review | `/spm-design-review` |
| design review 通过，无 PRD/prototype | PRD 或原型 | `/spm-prd` 或 `/spm-prototype` |
| PRD 存在，无 review | PRD review | `/spm-prd-review` |
| PRD review 通过 | 原型或修复 | `/spm-prototype` 或等变更 |

**不创建** `status.json`（由 writer 阶段首次产出时创建）。

### 路径 C：JSON 解析失败

告知损坏，展示前 500 字符。建议手动修复或删除走路径 B。停止，不自动修复。

### 路径 D：状态与产物不一致

列出不一致项，给出两种处理建议：① 回退 status.json current_stage ② 补建缺失产物。停止，等用户决定。

## 输出格式

```
## 项目状态
- 当前阶段：[阶段]
- status.json：存在/不存在

## 产物清单
| 阶段 | 人读 | 机读 | Review |
|------|------|------|--------|
| 对齐 | ✅/❌ | ✅/❌ | — |
| 设计 | ✅/❌ | ✅/❌ | ✅/❌/— |
| PRD | ✅/❌ | ✅/❌ | ✅/❌/— |
| 原型 | ✅/❌ | ✅/❌ | ✅/❌/— |

## 最近 Review
[摘要或"无"]

## 下一步建议
唯一建议：[操作]
```

## 硬规则

1. 不做需求判断 / 写作质量判断 / reviewer 职责
2. 不修改任何文件——只读取和输出
3. 路径 C/D 不自动修复，只报告和建议
4. 输出后停止，不追加多余解释
