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

- [ ] **Step 1: 读取 design.md 和 metadata/design，执行 design-review 检查项**

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

- [ ] **Step 2: 写入 design-review-1.json**

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

- [ ] **Step 3: 读取 prd.md 和 metadata/prd，执行 prd-review 检查项**

读取以下文件：
- `output/prd/prd.md`
- `.workflow/metadata/prd/` 下全部 6 个 JSON

按 `skills/prd-review/SKILL.md` 的 10 项检查清单逐项检查。重点关注：
- 坏味道（标签式、流水账、纯表格、模糊表述）
- 三层覆盖（展示规则、交互逻辑、异常边界）
- 一致性（与 design 镜像）

- [ ] **Step 4: 写入 prd-review-1.json**

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

- [ ] **Step 5: 更新 status.json 的 latest_reviews**

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

- [ ] **Step 6: 验证**

```bash
python -c "import json; json.load(open('.workflow/reviews/design-review-1.json')); json.load(open('.workflow/reviews/prd-review-1.json')); print('OK')"
```

---

## Task 2: stage-prep.py status.json 自动同步

**Files:**
- Modify: `scripts/python/stage-prep.py`

- [ ] **Step 1: 在 stage-prep.py 的 main() 末尾增加 status.json 同步逻辑**

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

- [ ] **Step 2: 验证 stage-prep.py 语法**

```bash
python -c "import py_compile; py_compile.compile('scripts/python/stage-prep.py', doraise=True); print('OK')"
```

- [ ] **Step 3: 运行 stage-prep.py --stage prd --dry-run 确认不报错**

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

- [ ] **Step 1: 运行 stage-context.py 确认可进入 prototype**

```bash
python scripts/python/stage-context.py .
```

预期：`next_recommended` = `"prototype"`，`gate.can_proceed` = true。

- [ ] **Step 2: 读取 design.md 的页面清单**

从 `output/design/design.md` 提取 4 个页面：
1. 收支记录列表页
2. 新增编辑收支页
3. 月度汇总页
4. 分类占比页

- [ ] **Step 3: 生成 output/prototype/index.html**

按 `templates/prototype.html` 骨架，生成轻量原型。只做页面骨架和导航，不做真实数据交互。

每个页面一个 `<div class="page" id="page-N">`，包含：
- 页面标题
- 主要区域占位（用 section div）
- 关键交互元素的静态展示（按钮、表单字段、表格列头）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>原型 - 个人记账工具</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .nav { background: #f5f5f5; padding: 10px 20px; border-bottom: 1px solid #ddd; }
    .nav a { margin-right: 15px; text-decoration: none; color: #333; cursor: pointer; padding: 5px 10px; }
    .nav a:hover, .nav a.active { color: #1890ff; border-bottom: 2px solid #1890ff; }
    .page { display: none; padding: 20px; max-width: 1200px; margin: 0 auto; }
    .page.active { display: block; }
    .page-title { font-size: 20px; font-weight: bold; margin-bottom: 20px; }
    .section { margin: 16px 0; padding: 16px; border: 1px solid #eee; border-radius: 4px; }
    .section-title { font-size: 14px; color: #666; margin-bottom: 12px; }
    .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }
    th { background: #fafafa; font-weight: 500; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .tag-income { background: #e6f7e6; color: #52c41a; }
    .tag-expense { background: #fff1f0; color: #f5222d; }
    .card { display: inline-block; width: 30%; padding: 16px; margin: 8px 1%; border: 1px solid #eee; border-radius: 8px; text-align: center; }
    .card-value { font-size: 24px; font-weight: bold; }
    .card-label { font-size: 14px; color: #666; margin-top: 4px; }
    .btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 4px; background: #fff; cursor: pointer; }
    .btn-primary { background: #1890ff; color: #fff; border-color: #1890ff; }
    .form-row { margin-bottom: 12px; }
    .form-label { display: block; font-size: 14px; margin-bottom: 4px; }
    .form-input { width: 100%; padding: 6px 12px; border: 1px solid #d9d9d9; border-radius: 4px; }
    .chart-placeholder { height: 300px; background: #fafafa; border: 1px dashed #ddd; display: flex; align-items: center; justify-content: center; color: #999; }
  </style>
</head>
<body>
  <nav class="nav">
    <a data-page="page-1" class="active">收支记录</a>
    <a data-page="page-2">记一笔</a>
    <a data-page="page-3">月度汇总</a>
    <a data-page="page-4">分类占比</a>
  </nav>

  <div class="page active" id="page-1">
    <div class="page-title">收支记录列表</div>
    <div class="toolbar">
      <div>
        <select class="form-input" style="width:150px"><option>2026年5月</option></select>
        <span style="margin-left:16px;color:#52c41a">收入: ¥0.00</span>
        <span style="margin-left:16px;color:#f5222d">支出: ¥0.00</span>
        <span style="margin-left:16px">净收支: ¥0.00</span>
      </div>
      <div>
        <input class="form-input" style="width:200px" placeholder="搜索备注...">
        <button class="btn btn-primary" style="margin-left:8px">+ 记一笔</button>
      </div>
    </div>
    <div class="section">
      <table>
        <tr><th>日期</th><th>类型</th><th>分类</th><th>金额</th><th>备注</th><th>操作</th></tr>
        <tr><td colspan="6" style="text-align:center;color:#999;padding:40px">本月暂无记录，点击右上角"记一笔"开始记账</td></tr>
      </table>
    </div>
  </div>

  <div class="page" id="page-2">
    <div class="page-title">新增收支记录</div>
    <div class="section" style="max-width:600px">
      <div class="form-row">
        <label class="form-label">收支类型</label>
        <button class="btn" style="margin-right:8px">收入</button><button class="btn btn-primary">支出</button>
      </div>
      <div class="form-row"><label class="form-label">金额 *</label><input class="form-input" placeholder="0.00"></div>
      <div class="form-row"><label class="form-label">分类 *</label><select class="form-input"><option>请选择分类</option></select></div>
      <div class="form-row"><label class="form-label">备注</label><textarea class="form-input" rows="3" placeholder="可选，最多200字符"></textarea></div>
      <div class="form-row"><label class="form-label">日期 *</label><input class="form-input" type="date"></div>
      <div style="margin-top:16px"><button class="btn btn-primary">保存</button><button class="btn" style="margin-left:8px">取消</button></div>
    </div>
  </div>

  <div class="page" id="page-3">
    <div class="page-title">月度汇总</div>
    <div class="toolbar"><select class="form-input" style="width:150px"><option>2026年5月</option></select></div>
    <div>
      <div class="card"><div class="card-value" style="color:#52c41a">¥0.00</div><div class="card-label">收入</div></div>
      <div class="card"><div class="card-value" style="color:#f5222d">¥0.00</div><div class="card-label">支出</div></div>
      <div class="card"><div class="card-value">¥0.00</div><div class="card-label">净收支</div></div>
    </div>
    <div class="section" style="margin-top:16px"><div class="chart-placeholder">柱状图区域（按日展示收入/支出）</div></div>
  </div>

  <div class="page" id="page-4">
    <div class="page-title">分类占比</div>
    <div class="toolbar"><select class="form-input" style="width:150px"><option>2026年5月</option></select></div>
    <div style="display:flex;gap:20px">
      <div class="section" style="flex:1"><div class="chart-placeholder" style="height:250px">饼图区域（支出分类占比）</div></div>
      <div class="section" style="flex:1"><p style="color:#999;text-align:center;padding:40px">本月暂无支出记录</p></div>
    </div>
  </div>

  <script>
    document.querySelectorAll('.nav a').forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.nav a').forEach(a => a.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        this.classList.add('active');
        document.getElementById(this.dataset.page).classList.add('active');
      });
    });
  </script>
</body>
</html>
```

- [ ] **Step 4: 写入 metadata/prototype/index.json**

```json
{
  "schema_version": "1.0.0",
  "stage": "prototype",
  "artifact_path": "output/prototype/index.html",
  "generated_at": "2026-05-10T...",
  "page_count": 4
}
```

- [ ] **Step 5: 写入 metadata/prototype/page-map.json**

```json
[
  {"page_id": "page-1", "title": "收支记录列表页", "source_page_ref": "PAGE-design-001"},
  {"page_id": "page-2", "title": "新增编辑收支页", "source_page_ref": "PAGE-design-002"},
  {"page_id": "page-3", "title": "月度汇总页", "source_page_ref": "PAGE-design-003"},
  {"page_id": "page-4", "title": "分类占比页", "source_page_ref": "PAGE-design-004"}
]
```

- [ ] **Step 6: 运行 stage-prep.py --stage prototype**

```bash
python scripts/python/stage-prep.py --stage prototype --project-root .
```

预期：status.json 自动更新 `current_stage: "prototype"`，`next_recommended: "fix"`。

- [ ] **Step 7: 运行 prototype-review**

读取 `output/prototype/index.html` 和 `.workflow/metadata/prototype/`，按 `skills/prototype-review/SKILL.md` 的 5 项检查清单审查。将结果写入 `.workflow/reviews/prototype-review-1.json`。

---

## Task 4: Fix 同步修复链路

**Files:**
- Modify: `output/design/design.md` — 增加"标签"字段
- Modify: `.workflow/metadata/design/fields.json` — 同步
- Modify: `output/prd/prd.md` — 同步
- Modify: `output/prototype/index.html` — 同步（可选）
- Modify: `.workflow/status.json`

- [ ] **Step 1: 按 fix SKILL.md 最小判断清单 6 步执行**

1. **读取修改指令**：在 design.md 的收支记录实体中增加一个"标签"字段
2. **判断修改指向的对象**：字段（FIELD 级别）
3. **判定问题归属层**：设计层（design 是事实源）
4. **判定事实源所在阶段**：design
5. **判定受影响的最深阶段**：prd（数据字典 + 详细需求说明）、prototype（可选）
6. **生成修复顺序**：design → prd → prototype

- [ ] **Step 2: 更新 design.md — 增加"标签"字段**

在字段定义表格中追加一行：

```
| 标签 | string | 50 | 否 | 空 | — | — | 用户输入 | 自定义标签，用于分类标记 |
```

在支出分类枚举后增加标签相关说明。

- [ ] **Step 3: 更新 metadata/design/fields.json**

追加：
```json
{"id": "FIELD-design-009", "type": "field", "title": "标签", "attributes": {"数据类型": "string", "长度": 50, "必填": false, "默认值": "空", "枚举值": null, "格式": null, "业务来源": "用户输入", "说明": "自定义标签，用于分类标记"}}
```

- [ ] **Step 4: 运行 stage-prep.py --stage design 同步 metadata**

```bash
python scripts/python/stage-prep.py --stage design --project-root .
```

- [ ] **Step 5: 更新 prd.md — 同步"标签"字段**

在数据字典表格中追加标签字段行。在新增编辑收支页的表单描述中增加标签输入框。在收支记录列表页的行展示中增加标签列。

- [ ] **Step 6: 更新 metadata/prd/field-anchor.json**

追加标签字段锚点。

- [ ] **Step 7: 运行 stage-prep.py --stage prd 同步 metadata**

```bash
python scripts/python/stage-prep.py --stage prd --project-root .
```

- [ ] **Step 8: 更新 prototype（可选）**

在 index.html 的列表页表格增加"标签"列，在新增页表单增加标签输入框。

- [ ] **Step 9: 执行 design-review 和 prd-review 确认无遗留**

重新执行 review，将结果写入 `.workflow/reviews/design-review-2.json` 和 `.workflow/reviews/prd-review-2.json`。确认无新增问题。

- [ ] **Step 10: 输出 fix 完成报告**

```
建议进入 design-review，检查对象：[字段定义、数据字典]
建议进入 prd-review，检查对象：[数据字典、新增编辑收支页、收支记录列表页]
```

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

**Type consistency:** review-result.schema.json 的 7 字段在 Task 1 的 JSON 模板中一致使用。
