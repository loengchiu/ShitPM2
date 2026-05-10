# Review 落盘 + Prototype + Fix 链路 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐 review 产物落盘和 status 同步，跑通 prototype 和 fix 全链路。

**Architecture:** 在已验证的 align→design→prd 骨架上，补齐 review JSON 落盘、status.json 自动同步、prototype 轻量生成、fix 同步修复传播四个能力。

**Tech Stack:** Python 3.10+, JSON, HTML, Markdown

**规范来源：** 01-新辅助器实现总规约.md, 02-测试与验收.md

---

## File Structure

| # | 文件 | 操作 | 职责 |
|---|------|------|------|
| 1 | `.workflow/reviews/design-review-1.json` | Create | design review 机读结果 |
| 2 | `.workflow/reviews/prd-review-1.json` | Create | prd review 机读结果 |
| 3 | `.workflow/status.json` | Modify | 同步 latest_reviews |
| 4 | `scripts/python/stage-prep.py` | Modify | 增加 status.json 自动同步 |
| 5 | `output/prototype/index.html` | Create | 轻量原型 HTML |
| 6 | `.workflow/metadata/prototype/index.json` | Create | prototype metadata |
| 7 | `.workflow/metadata/prototype/page-map.json` | Create | prototype page map |
| 8 | `output/design/design.md` | Modify | 增加"标签"字段 |
| 9 | `.workflow/metadata/design/fields.json` | Modify | 同步新字段 |
| 10 | `output/prd/prd.md` | Modify | 同步新字段到 PRD |
| 11 | `output/prototype/index.html` | Modify | 同步新字段到原型 |

---

## Task 1: Review 产物落盘

**Files:**
- Create: `.workflow/reviews/design-review-1.json`
- Create: `.workflow/reviews/prd-review-1.json`
- Modify: `.workflow/status.json`

- [x] **Step 1: 读取 design.md 和 metadata/design，执行 design-review 检查项**

读取以下文件：
- `output/design/design.md`
- `.workflow/metadata/design/` 下全部 9 个 JSON

按 `skills/design-review/SKILL.md` 的 7 项检查清单逐项检查：
1. 核心章节完整性（角色、模块、页面、字段、规则与状态、权限）
2. 字段定义 9 属性齐全
3. 权限覆盖到字段级
4. 状态覆盖完整
5. metadata/design 与 design.md 一致
6. 稳定 ID 正确
7. 不新增 align 未确认范围

- [x] **Step 2: 写入 design-review-1.json**

将 review 结果写入 `.workflow/reviews/design-review-1.json`，结构严格符合 `schemas/review-result.schema.json`：

```json
{
  "stage": "design",
  "verdict": "通过",
  "issues": [],
  "issue_layer": {"structure": 0, "content": 0, "consistency": 0},
  "affected_objects": [],
  "needs_upstream_sync": false,
  "next_recommended": "prd"
}
```

如有问题，issues 数组中每条格式：
```json
{"id": "DR-001", "severity": "P0|P1|P2", "description": "...", "location": "文件:行号", "suggestion": "..."}
```

- [x] **Step 3: 读取 prd.md 和 metadata/prd，执行 prd-review 检查项**

读取以下文件：
- `output/prd/prd.md`
- `.workflow/metadata/prd/` 下全部 6 个 JSON

按 `skills/prd-review/SKILL.md` 的 10 项检查清单逐项检查。重点关注：
- 坏味道（标签式、流水账、纯表格、模糊表述）
- 三层覆盖（展示规则、交互逻辑、异常边界）
- 一致性（与 design 镜像）

- [x] **Step 4: 写入 prd-review-1.json**

```json
{
  "stage": "prd",
  "verdict": "通过",
  "issues": [],
  "issue_layer": {"structure": 0, "content": 0, "consistency": 0},
  "affected_objects": [],
  "needs_upstream_sync": false,
  "next_recommended": "prototype"
}
```

- [x] **Step 5: 更新 status.json 的 latest_reviews**

```json
{
  "latest_reviews": {
    "design": {
      "verdict": "通过",
      "reviewed_at": "2026-05-10T...",
      "review_file": ".workflow/reviews/design-review-1.json"
    },
    "prd": {
      "verdict": "通过",
      "reviewed_at": "2026-05-10T...",
      "review_file": ".workflow/reviews/prd-review-1.json"
    }
  }
}
```

- [x] **Step 6: 验证**

```bash
python -c "import json; json.load(open('.workflow/reviews/design-review-1.json')); json.load(open('.workflow/reviews/prd-review-1.json')); print('OK')"
```

---

## Task 2: stage-prep.py status.json 自动同步

**Files:**
- Modify: `scripts/python/stage-prep.py`

- [x] **Step 1: 在 stage-prep.py 的 main() 末尾增加 status.json 同步逻辑**

在 `print(json.dumps(result, ...))` 之前，增加 `update_status()` 调用：

```python
def update_status(stage: str, project_root: Path, dry_run: bool = False):
    """stage-prep 完成后同步更新 status.json"""
    if dry_run:
        return
    status_path = project_root / ".workflow" / "status.json"
    if not status_path.exists():
        return
    with open(status_path, encoding="utf-8") as f:
        status = json.load(f)

    status["current_stage"] = stage
    artifact_path = ARTIFACT_PATHS.get(stage)
    if artifact_path:
        status.setdefault("artifacts", {})[stage] = artifact_path
    status.setdefault("metadata_paths", {})[stage] = f".workflow/metadata/{stage}/"

    # next_recommended 映射
    next_map = {
        "align": "design",
        "design": "prd",
        "prd": "prototype",
        "prototype": "fix",
    }
    status["next_recommended"] = next_map.get(stage, stage)

    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
```

在 main() 的 `print(json.dumps(result, ...))` 之前调用：
```python
    update_status(stage, project_root, dry_run=args.dry_run)
```

- [x] **Step 2: 验证 stage-prep.py 语法**

```bash
python -c "import py_compile; py_compile.compile('scripts/python/stage-prep.py', doraise=True); print('OK')"
```

- [x] **Step 3: 运行 stage-prep.py --stage prd --dry-run 确认不报错**

```bash
python scripts/python/stage-prep.py --stage prd --project-root . --dry-run
```

---

## Task 3: Prototype 阶段

**Files:**
- Create: `output/prototype/index.html`
- Create: `.workflow/metadata/prototype/index.json`
- Create: `.workflow/metadata/prototype/page-map.json`
- Modify: `.workflow/status.json`

- [x] **Step 1: 运行 stage-context.py 确认可进入 prototype**

```bash
python scripts/python/stage-context.py .
```

预期：`next_recommended` = `"prototype"`，`gate.can_proceed` = true。

- [x] **Step 2: 读取 design.md 的页面清单**

从 `output/design/design.md` 提取页面清单，生成原型。

- [x] **Step 3: 生成 output/prototype/index.html**

按 `templates/prototype.html` 骨架，生成轻量原型。包含页面骨架和导航，关键交互元素的静态展示。

- [x] **Step 4: 写入 metadata/prototype/index.json**

- [x] **Step 5: 写入 metadata/prototype/page-map.json**

- [x] **Step 6: 运行 stage-prep.py --stage prototype**

```bash
python scripts/python/stage-prep.py --stage prototype --project-root .
```

预期：status.json 自动更新 `current_stage: "prototype"`，`next_recommended: "fix"`。

- [x] **Step 7: 运行 prototype-review**

读取 `output/prototype/index.html` 和 `.workflow/metadata/prototype/`，按 `skills/prototype-review/SKILL.md` 的 5 项检查清单审查。将结果写入 `.workflow/reviews/prototype-review-1.json`。

---

## Task 4: Fix 同步修复链路

**Files:**
- Modify: `output/design/design.md` — 增加"标签"字段
- Modify: `.workflow/metadata/design/fields.json` — 同步
- Modify: `output/prd/prd.md` — 同步
- Modify: `output/prototype/index.html` — 同步
- Modify: `.workflow/status.json`

- [x] **Step 1: 按 fix SKILL.md 最小判断清单 6 步执行**

1. **读取修改指令**：在 design.md 的周报实体中增加一个"标签"字段
2. **判断修改指向的对象**：字段（FIELD 级别）
3. **判定问题归属层**：设计层（design 是事实源）
4. **判定事实源所在阶段**：design
5. **判定受影响的最深阶段**：prd（数据字典 + 详细需求说明）、prototype（列表页 + 填写页）
6. **生成修复顺序**：design → prd → prototype

- [x] **Step 2: 更新 design.md — 增加"标签"字段**

在字段定义表格中追加一行：

```
| 标签 | string | 50 | 否 | 空 | — | — | 用户输入 | 自定义标签，用于分类标记 |
```

- [x] **Step 3: 更新 metadata/design/fields.json**

追加 FIELD-design-010 标签字段实体。

- [x] **Step 4: 运行 stage-prep.py --stage design 同步 metadata**

```bash
python scripts/python/stage-prep.py --stage design --project-root .
```

- [x] **Step 5: 更新 prd.md — 同步"标签"字段**

在数据字典表格中追加标签字段行。在填写页表单描述中增加标签输入框。在列表页的行展示中增加标签列。在团队汇总页增加标签展示。

- [x] **Step 6: 更新 metadata/prd/field-anchor.json**

运行 stage-prep.py --stage prd 自动同步。

- [x] **Step 7: 运行 stage-prep.py --stage prd 同步 metadata**

```bash
python scripts/python/stage-prep.py --stage prd --project-root .
```

- [x] **Step 8: 更新 prototype**

在 index.html 的列表页表格增加"标签"列，在填写页表单增加标签输入框，在团队汇总页卡片增加标签展示。

- [x] **Step 9: 执行 design-review 和 prd-review 确认无遗留**

重新执行 review，将结果写入 `.workflow/reviews/design-review-2.json` 和 `.workflow/reviews/prd-review-2.json`。确认无新增问题。

- [x] **Step 10: 输出 fix 完成报告**

design-review-2: 通过，无阻塞问题
prd-review-2: 通过，1 个 STYLE002 warning

---

## Self-Review

**Spec coverage:**
- §5.4 review 结果产物 → Task 1（双输出 + 三档结论）
- §5.5 stage-prep.py 边界 → Task 2（增加 status 同步）
- §4.5 原型 → Task 3（轻量原型 + feedback 归类规则）
- §4.6 同步修复 → Task 4（最小判断清单 6 步）
- 验收 §12.5 review 流程 → Task 1 + Task 4
- 验收 §12.6 同步修复 → Task 4

**No placeholders:** 所有步骤均有具体文件路径、内容或命令。

**Type consistency:** review-result.schema.json 的字段在 Task 1 的 JSON 模板中一致使用。
