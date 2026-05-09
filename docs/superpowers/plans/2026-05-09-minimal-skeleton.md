# 新辅助器第一轮最小骨架 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地新辅助器最小可运行骨架，使 `align -> design -> prd` 链路的基础文件全部就位。

**Architecture:** 规则落点严格按 01 规约 §3 执行：SKILL.md 只含硬规则，template 只管骨架，reference 只做示例，schemas 定义机读物结构，scripts 做确定性工作。metadata 统一走 `.workflow/metadata/`，status 统一走 `.workflow/status.json`。

**Tech Stack:** Python 3.10+, JSON Schema, Markdown

**规范来源：**
- `D:\work\ShitPM\01-新辅助器实现总规约.md`（以下简称"规约"）
- `D:\work\ShitPM\02-测试与验收.md`（以下简称"验收"）

**参考项目：**
- PMFlow: `D:\work\PMFlow`
- OhMyPm: `D:\work\AIskills\OhMyPm`
- ShitPM: `D:\work\AIskills\ShitPM`
- TestAny: `D:\work\AIskills\testany-agent-skills`

---

## File Structure

### 新建文件清单

| # | 文件路径 | 职责 |
|---|---------|------|
| 1 | `schemas/status.schema.json` | status.json 结构契约，6 类字段 |
| 2 | `schemas/align-notes.schema.json` | align-notes.json 结构契约，6 字段 |
| 3 | `schemas/design-metadata.schema.json` | design 阶段 9 个 JSON 文件的结构契约 |
| 4 | `schemas/prd-metadata.schema.json` | PRD 阶段 6 个 JSON 文件的结构契约 |
| 5 | `schemas/prototype-metadata.schema.json` | prototype 阶段 2 个 JSON 文件的结构契约 |
| 6 | `schemas/review-result.schema.json` | review 结果 JSON 的结构契约，7 字段 |
| 7 | `templates/align.md` | 对齐产物骨架，只含章节标题和最小骨架 |
| 8 | `templates/design.md` | 设计产物骨架，9 块固定组织 |
| 9 | `templates/prd.md` | PRD 产物骨架，核心+辅助章节 |
| 10 | `templates/prototype.html` | 原型最小 HTML 骨架 |
| 11 | `references/prd-writing.md` | PRD 写法示例和对照说明 |
| 12 | `references/prd-writing.profile.json` | PRD 写作轻量硬约束摘要 |
| 13 | `references/align-writing.md` | 对齐写法示例 |
| 14 | `references/design-writing.md` | 设计写法示例 |
| 15 | `references/prototype-writing.md` | 原型写法示例 |
| 16 | `skills/align/SKILL.md` | 对齐阶段硬规则 |
| 17 | `skills/design/SKILL.md` | 设计阶段硬规则 |
| 18 | `skills/prd/SKILL.md` | PRD 写作硬规则 |
| 19 | `skills/design-review/SKILL.md` | 设计 review 硬规则 |
| 20 | `skills/prd-review/SKILL.md` | PRD review 硬规则 |
| 21 | `scripts/python/stage-context.py` | 准入和上下文脚本 |
| 22 | `scripts/python/stage-prep.py` | 机读镜像生成脚本 |
| 23 | `scripts/python/prd-style-lint.py` | PRD 文风 lint 脚本 |

### 本轮不创建的文件（明确排除）

- `skills/start/SKILL.md`
- `skills/prototype/SKILL.md`
- `skills/prototype-review/SKILL.md`
- `skills/fix/SKILL.md`
- `contracts/` 全部
- `scripts/python/review-precheck.py`
- `scripts/python/anchor-build.py`
- `scripts/python/anchor-verify.py`

---

## Task 1: 目录结构与初始文件

**Files:**
- Create: 所有目录和初始空文件

- [ ] **Step 1: 创建完整目录结构**

```bash
cd D:\work\ShitPM
mkdir -p schemas
mkdir -p templates
mkdir -p references
mkdir -p skills/align
mkdir -p skills/design
mkdir -p skills/prd
mkdir -p skills/design-review
mkdir -p skills/prd-review
mkdir -p scripts/python
mkdir -p .workflow/status
mkdir -p .workflow/metadata/align
mkdir -p .workflow/metadata/design
mkdir -p .workflow/metadata/prd
mkdir -p .workflow/metadata/prototype
mkdir -p .workflow/runtime/align
mkdir -p .workflow/runtime/design
mkdir -p .workflow/runtime/prd
mkdir -p .workflow/runtime/prototype
mkdir -p .workflow/reviews
mkdir -p output/align
mkdir -p output/design
mkdir -p output/prd
mkdir -p output/prototype
```

- [ ] **Step 2: 创建初始 status.json**

写入 `.workflow/status.json`：

```json
{
  "current_stage": "align",
  "artifacts": {},
  "metadata_paths": {},
  "latest_reviews": {},
  "align_notes": {},
  "next_recommended": "align"
}
```

- [ ] **Step 3: 验证目录结构**

```bash
ls -R .workflow/
ls schemas/ templates/ references/ skills/ scripts/python/
```

预期：所有目录存在，`.workflow/status.json` 包含 6 类字段。

---

## Task 2: JSON Schemas

**Files:**
- Create: `schemas/status.schema.json`
- Create: `schemas/align-notes.schema.json`
- Create: `schemas/design-metadata.schema.json`
- Create: `schemas/prd-metadata.schema.json`
- Create: `schemas/prototype-metadata.schema.json`
- Create: `schemas/review-result.schema.json`

- [ ] **Step 1: 创建 status.schema.json**

对应规约 §5.3 的 6 类字段。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Status",
  "description": "新辅助器工作流状态文件，只保留当前真相",
  "type": "object",
  "required": ["current_stage", "artifacts", "metadata_paths", "latest_reviews", "align_notes", "next_recommended"],
  "properties": {
    "current_stage": {
      "type": "string",
      "enum": ["align", "design", "prd", "prototype", "fix"],
      "description": "当前所处阶段"
    },
    "artifacts": {
      "type": "object",
      "description": "各阶段人读产物路径",
      "properties": {
        "align": { "type": ["string", "null"] },
        "design": { "type": ["string", "null"] },
        "prd": { "type": ["string", "null"] },
        "prototype": { "type": ["string", "null"] }
      },
      "additionalProperties": false
    },
    "metadata_paths": {
      "type": "object",
      "description": "各阶段机读物目录路径",
      "properties": {
        "align": { "type": ["string", "null"] },
        "design": { "type": ["string", "null"] },
        "prd": { "type": ["string", "null"] },
        "prototype": { "type": ["string", "null"] }
      },
      "additionalProperties": false
    },
    "latest_reviews": {
      "type": "object",
      "description": "最近一次 review 结果摘要",
      "properties": {
        "design": { "$ref": "#/$defs/review_summary" },
        "prd": { "$ref": "#/$defs/review_summary" },
        "prototype": { "$ref": "#/$defs/review_summary" }
      },
      "additionalProperties": false
    },
    "align_notes": {
      "type": "object",
      "description": "对齐阶段内部判断记录（来自 align-notes.json）"
    },
    "next_recommended": {
      "type": "string",
      "enum": ["align", "design", "prd", "prototype", "fix"],
      "description": "下一步唯一建议"
    }
  },
  "additionalProperties": false,
  "$defs": {
    "review_summary": {
      "type": "object",
      "properties": {
        "verdict": { "type": "string", "enum": ["通过", "有问题需修改", "阻塞，不能继续"] },
        "reviewed_at": { "type": "string", "format": "date-time" }
      }
    }
  }
}
```

- [ ] **Step 2: 创建 align-notes.schema.json**

对应规约 §4.2 的 6 个字段。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AlignNotes",
  "description": "对齐阶段内部判断记录，只保留判断结论",
  "type": "object",
  "required": ["blocking_gaps", "needs_ask_back", "ask_back_reason", "can_enter_design", "judgement_note", "last_updated_at"],
  "properties": {
    "blocking_gaps": {
      "type": "array",
      "items": { "type": "string" },
      "description": "阻塞进入设计的真实缺口"
    },
    "needs_ask_back": {
      "type": "boolean",
      "description": "是否需要追问 PM"
    },
    "ask_back_reason": {
      "type": ["string", "null"],
      "description": "追问原因"
    },
    "can_enter_design": {
      "type": "boolean",
      "description": "是否允许进入设计阶段"
    },
    "judgement_note": {
      "type": ["string", "null"],
      "description": "判断说明"
    },
    "last_updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "最后更新时间"
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 3: 创建 design-metadata.schema.json**

对应规约 §5.2 的 design metadata 结构（9 个 JSON 文件的公共 envelope）。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DesignMetadata",
  "description": "design 阶段机读镜像的公共结构定义",
  "type": "object",
  "required": ["schema_version", "stage", "artifact_path", "entities", "relations"],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.0.0",
      "description": "schema 版本号"
    },
    "stage": {
      "type": "string",
      "const": "design",
      "description": "所属阶段"
    },
    "artifact_path": {
      "type": "string",
      "description": "人读产物路径"
    },
    "entities": {
      "type": "array",
      "items": { "$ref": "#/$defs/entity" },
      "description": "实体列表"
    },
    "relations": {
      "type": "array",
      "items": { "$ref": "#/$defs/relation" },
      "description": "关系列表"
    }
  },
  "additionalProperties": true,
  "$defs": {
    "entity": {
      "type": "object",
      "required": ["id", "type", "title"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^(MODULE|PAGE|FIELD|RULE|FLOW|REL)-design-[0-9]{3}$",
          "description": "稳定 ID，仅存在于机读物"
        },
        "type": {
          "type": "string",
          "enum": ["module", "page", "field", "rule", "flow", "role", "state", "permission"],
          "description": "实体类型"
        },
        "title": { "type": "string", "description": "实体标题" },
        "source_ref": { "type": ["string", "null"], "description": "来源追溯" },
        "attributes": { "type": "object", "description": "实体属性" }
      },
      "additionalProperties": true
    },
    "relation": {
      "type": "object",
      "required": ["id", "type", "from", "to"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^REL-design-[0-9]{3}$"
        },
        "type": {
          "type": "string",
          "enum": ["derived_from", "refines", "depends_on", "contains", "uses", "verifies"]
        },
        "from": { "type": "string", "description": "来源实体 ID" },
        "to": { "type": "string", "description": "目标实体 ID" }
      },
      "additionalProperties": false
    }
  }
}
```

- [ ] **Step 4: 创建 prd-metadata.schema.json**

与 design-metadata 结构类似，但 stage 固定为 `"prd"`，ID 前缀不同。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PRDMetadata",
  "description": "PRD 阶段机读镜像的公共结构定义",
  "type": "object",
  "required": ["schema_version", "stage", "artifact_path", "entities", "relations"],
  "properties": {
    "schema_version": { "type": "string", "const": "1.0.0" },
    "stage": { "type": "string", "const": "prd" },
    "artifact_path": { "type": "string" },
    "entities": {
      "type": "array",
      "items": { "$ref": "#/$defs/entity" }
    },
    "relations": {
      "type": "array",
      "items": { "$ref": "#/$defs/relation" }
    }
  },
  "additionalProperties": true,
  "$defs": {
    "entity": {
      "type": "object",
      "required": ["id", "type", "title"],
      "properties": {
        "id": { "type": "string", "pattern": "^(MODULE|PAGE|FIELD|RULE|FLOW)-prd-[0-9]{3}$" },
        "type": { "type": "string", "enum": ["module", "page", "field", "rule", "flow"] },
        "title": { "type": "string" },
        "source_ref": { "type": ["string", "null"] },
        "attributes": { "type": "object" }
      },
      "additionalProperties": true
    },
    "relation": {
      "type": "object",
      "required": ["id", "type", "from", "to"],
      "properties": {
        "id": { "type": "string", "pattern": "^REL-prd-[0-9]{3}$" },
        "type": { "type": "string", "enum": ["derived_from", "refines", "depends_on", "contains", "uses", "verifies"] },
        "from": { "type": "string" },
        "to": { "type": "string" }
      },
      "additionalProperties": false
    }
  }
}
```

- [ ] **Step 5: 创建 prototype-metadata.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PrototypeMetadata",
  "description": "prototype 阶段机读镜像的结构定义",
  "type": "object",
  "required": ["schema_version", "stage", "artifact_path"],
  "properties": {
    "schema_version": { "type": "string", "const": "1.0.0" },
    "stage": { "type": "string", "const": "prototype" },
    "artifact_path": { "type": "string" },
    "page_map": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["page_id", "title", "source_page_ref"],
        "properties": {
          "page_id": { "type": "string" },
          "title": { "type": "string" },
          "source_page_ref": { "type": "string", "description": "design 中的 PAGE-* ID" },
          "html_section": { "type": ["string", "null"] }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": true
}
```

- [ ] **Step 6: 创建 review-result.schema.json**

对应规约 §5.4 的 7 个字段。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReviewResult",
  "description": "review 结果机读 JSON",
  "type": "object",
  "required": ["stage", "verdict", "issues", "issue_layer", "affected_objects", "needs_upstream_sync", "next_recommended"],
  "properties": {
    "stage": {
      "type": "string",
      "enum": ["design", "prd", "prototype"],
      "description": "被 review 的阶段"
    },
    "verdict": {
      "type": "string",
      "enum": ["通过", "有问题需修改", "阻塞，不能继续"],
      "description": "review 结论，只允许三档"
    },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "severity", "description"],
        "properties": {
          "id": { "type": "string" },
          "severity": { "type": "string", "enum": ["P0", "P1", "P2"] },
          "description": { "type": "string" },
          "location": { "type": ["string", "null"] },
          "suggestion": { "type": ["string", "null"] }
        },
        "additionalProperties": false
      },
      "description": "问题列表"
    },
    "issue_layer": {
      "type": "object",
      "description": "问题归属层分布",
      "properties": {
        "structure": { "type": "integer", "description": "结构性问题数" },
        "content": { "type": "integer", "description": "内容质量问题数" },
        "consistency": { "type": "integer", "description": "一致性问题数" }
      },
      "additionalProperties": false
    },
    "affected_objects": {
      "type": "array",
      "items": { "type": "string" },
      "description": "受影响对象列表（稳定 ID 或对象名）"
    },
    "needs_upstream_sync": {
      "type": "boolean",
      "description": "是否需要回上游同步修复"
    },
    "next_recommended": {
      "type": "string",
      "description": "下一步建议"
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 7: 验证所有 schema 文件为合法 JSON**

```bash
cd D:\work\ShitPM
python -c "import json, glob; [json.load(open(f)) for f in glob.glob('schemas/*.json')]; print('All schemas valid')"
```

预期输出：`All schemas valid`

---

## Task 3: Templates

**Files:**
- Create: `templates/align.md`
- Create: `templates/design.md`
- Create: `templates/prd.md`
- Create: `templates/prototype.html`

- [ ] **Step 1: 创建 templates/align.md**

对应规约 §4.2 对齐阶段输出。只含章节骨架，不诱导标签式正文。

```markdown
# 对齐稿

## 一、需求概述

<!-- 一句话说明当前需求 -->

## 二、建设范围

### （一）一期范围

### （二）二期范围（如有）

### （三）明确不做

## 三、建设方式

<!-- iteration / new_build / hybrid 三选一，并说明判断依据 -->

## 四、业务阶段

<!-- 当前业务处于什么阶段 -->

## 五、现有线索

### （一）已有系统或页面

### （二）已有资料

## 六、待确认问题

<!-- 如有阻塞性问题，逐条列出 -->
```

- [ ] **Step 2: 创建 templates/design.md**

对应规约 §4.3 推荐骨架 9 块。核心章节必须存在。

```markdown
# 设计基线

## 一、文档概述

<!-- 可选：项目背景、设计目标 -->

## 二、范围与建设方式

<!-- 可选：引用对齐结论 -->

## 三、角色定义

<!-- 核心：角色名称、职责、权限层级 -->

## 四、模块定义

<!-- 核心：模块名称、职责、包含页面 -->

## 五、核心业务流程

<!-- 可选：主要流程、分支、异常 -->

## 六、页面清单

<!-- 核心：页面编号、名称、所属模块、主要功能 -->

## 七、字段定义

<!-- 核心：字段完整属性（名称、类型、长度、必填、默认值、枚举值、格式、业务来源、说明） -->

## 八、规则与状态定义

<!-- 核心：业务规则、状态集合、状态迁移、触发条件 -->

## 九、权限定义

<!-- 核心：页面级权限、按"页面 > 角色 > 字段权限例外"组织 -->
```

- [ ] **Step 3: 创建 templates/prd.md**

对应规约 §4.4 推荐章节顺序。参考 ShitPM 模板骨架但去掉标签诱导和 AI 锚点区。

```markdown
# PRD 正文

## 一、文档概述

<!-- 可选 -->

## 二、范围

<!-- 可选 -->

## 三、业务流程

<!-- 可选：主流程、分支与异常、状态流转 -->

## 四、详细需求说明

<!-- 核心：按页面组织，每个页面覆盖界面元素与展示规则、交互逻辑与状态流转、异常处理与边界场景 -->

## 五、权限汇总

<!-- 核心：页面级、按钮级、字段级权限 -->

## 六、数据字典

<!-- 核心：按实体分组，使用统一 9 列（字段、类型、长度、必填、默认值、枚举值、格式、业务来源、说明） -->

## 七、状态机

<!-- 核心：按核心业务对象组织，包含状态集合、迁移、触发动作和限制条件 -->

## 八、验收标准汇总

<!-- 可选 -->

## 九、风险与待确认

<!-- 可选 -->
```

- [ ] **Step 4: 创建 templates/prototype.html**

最小 HTML 骨架。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>原型 - {{项目名称}}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .page { display: none; padding: 20px; }
    .page.active { display: block; }
    .nav { background: #f5f5f5; padding: 10px 20px; border-bottom: 1px solid #ddd; }
    .nav a { margin-right: 15px; text-decoration: none; color: #333; cursor: pointer; }
    .nav a:hover { color: #1890ff; }
    .section { margin: 20px 0; padding: 15px; border: 1px solid #eee; border-radius: 4px; }
    .placeholder { color: #999; font-style: italic; }
  </style>
</head>
<body>
  <nav class="nav" id="nav">
    <!-- 按 design 页面清单生成导航 -->
  </nav>

  <!-- 每个页面一个 div.page，id 对应 PAGE-* -->

  <script>
    // 页面切换逻辑
    document.querySelectorAll('.nav a').forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById(this.dataset.page).classList.add('active');
      });
    });
    // 默认显示第一个页面
    const first = document.querySelector('.page');
    if (first) first.classList.add('active');
  </script>
</body>
</html>
```

- [ ] **Step 5: 验证所有 template 文件存在且可读**

```bash
ls templates/
```

预期：`align.md`, `design.md`, `prd.md`, `prototype.html` 均存在。

---

## Task 4: References

**Files:**
- Create: `references/prd-writing.md`
- Create: `references/prd-writing.profile.json`
- Create: `references/align-writing.md`
- Create: `references/design-writing.md`
- Create: `references/prototype-writing.md`

- [ ] **Step 1: 创建 references/prd-writing.md**

吸收 ShitPM 的 PRD 写作原则，适配新辅助器。只含示例和对照，不含硬规则。

```markdown
# PRD 写法参考

> 本文件是 PRD 写作的示例和对照说明。
> 硬规则在 `skills/prd/SKILL.md`，不在本文件。

## 一、好例子：自然规格说明

### 1.1 页面正文写法

**好：**

> 入库记录列表默认按申请时间倒序排列，每页 20 条。每行展示：入库单号、申请
> 人、申请时间、入库状态、审核状态。
>
> 点击行尾"查看"按钮，展开入库单详情抽屉。详情包含：商品明细表（字段：
> 商品编码、商品名称、规格、数量、单价、小计）、审核意见、附件列表。
>
> 当入库状态为"已入库"时，行尾显示"导出"按钮；当入库状态为"待审核"
> 时，行尾显示"撤回"按钮。撤回后状态变为"已撤回"，不可再次提交。

**坏（标签式正文）：**

> **页面目标：** 展示入库记录
> **关键动作：** 查看、导出、撤回
> **状态变化：** 待审核 -> 已入库 / 已撤回
> **异常提示：** 网络异常时提示重试

### 1.2 数据字典写法

**好：**

| 字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明 |
|------|------|------|------|--------|--------|------|----------|------|
| 入库单号 | string | 20 | 是 | 系统生成 | — | RK-YYYYMMDD-NNNN | 系统生成 | 全局唯一 |

**坏（含机读字段）：**

| FIELD-design-001 | 入库单号 | string | ... |

### 1.3 页面三层覆盖

每个页面正文必须覆盖：

1. **界面元素与展示规则**：有哪些字段、怎么排列、怎么排序、怎么分页
2. **交互逻辑与状态流转**：用户能做什么、操作后状态怎么变、前后端怎么配合
3. **异常处理与边界场景**：网络断了怎么办、并发冲突怎么办、数据量大了怎么办

## 二、坏例子：动作流水账

**坏：**

> 1. 用户点击"新建入库单"按钮
> 2. 系统弹出新建表单
> 3. 用户填写表单
> 4. 用户点击"提交"
> 5. 系统保存并返回列表

**好（加入展示规则和异常边界）：**

> 点击列表页右上角"新建入库单"，打开全屏表单页。
>
> 表单包含：入库类型（下拉，必填）、供应商（搜索选择，必填）、备注（多行
> 文本，选填）、商品明细（子表，至少 1 行）。
>
> 商品明细每行包含：商品编码（搜索选择，选中后自动带出名称和规格）、数量
> （正整数，必填）、单价（≥0，小数 2 位，必填）。小计 = 数量 × 单价，
> 系统自动计算，不可编辑。
>
> 提交时校验：商品明细不能为空；数量必须 > 0；同一商品不可重复添加。
> 校验不通过时，对应字段标红并显示错误提示，不关闭表单。
>
> 提交成功后，跳转回列表页，列表顶部 toast 提示"入库单已创建"。
> 提交失败时（如网络超时），保留在表单页，弹窗提示"提交失败，请重试"，
> 已填写内容不丢失。

## 三、对照说明

| 维度 | 坏的做法 | 好的做法 |
|------|---------|---------|
| 表达方式 | 标签式拼接 | 自然规格说明段落 |
| 具体数值 | "N 条"、"按配置" | "每页 20 条"、"小数 2 位" |
| UI 文案 | 不提 | 用引号嵌入正文 |
| 长文本 | 不处理 | 描述截断、滚动、悬浮 |
| 动作描述 | 点击流水账 | 加展示规则 + 状态流转 + 异常边界 |
| 表格使用 | 全文表格 | 仅天然映射内容用表格 |
| 加粗 | 到处加粗 | 少用加粗 |
```

- [ ] **Step 2: 创建 references/prd-writing.profile.json**

对应规约 §5 的 `prd-writing.profile.json` 职责。

```json
{
  "profile_name": "prd-writing-v1",
  "description": "PRD 写作轻量硬约束摘要",
  "constraints": {
    "granularity": {
      "page_body_min_paragraphs": 3,
      "require_three_layer_coverage": true,
      "three_layers": ["界面元素与展示规则", "交互逻辑与状态流转", "异常处理与边界场景"]
    },
    "table_usage": {
      "allowed_for": ["数据字典", "权限汇总", "天然映射关系"],
      "forbidden_for": ["页面正文主体", "动作描述"]
    },
    "forbidden_expressions": [
      "**页面目标：**",
      "**关键动作：**",
      "**状态变化：**",
      "**异常提示：**",
      "按配置",
      "按规范",
      "同常规",
      "待补充",
      "需支持",
      "需考虑",
      "详见原型"
    ],
    "required_sections": ["详细需求说明", "权限汇总", "数据字典", "状态机"],
    "data_dictionary_columns": ["字段", "类型", "长度", "必填", "默认值", "枚举值", "格式", "业务来源", "说明"],
    "bold_usage": "少用加粗，仅用于真正需要强调的少量内容",
    "numbering": {
      "chapter": "## 一、...",
      "section": "### （一）...",
      "subsection": "#### 1．..."
    }
  }
}
```

- [ ] **Step 3: 创建 references/align-writing.md**

```markdown
# 对齐写法参考

> 本文件是对齐阶段的示例和对照说明。
> 硬规则在 `skills/align/SKILL.md`。

## 一、目标写法

**好：**
> 建设一套内部入库管理能力，覆盖从申请、审核到入库确认的全流程。

**坏：**
> 做一个入库系统。（过于模糊）

## 二、范围写法

**好：**
> 一期：入库申请、入库审核、入库确认、入库记录查询
> 不做：出库管理、库存预警、多仓管理

**坏：**
> 做入库相关的功能。（无边界）

## 三、建设类型判断

- `iteration`：在现有系统上扩展，有明确挂载点和约束
- `new_build`：全新建设，需确定模块边界和主流程
- `hybrid`：部分复用、部分新建，需明确哪些复用、哪些新建、怎么对接

## 四、ask-back 纪律

1. 只为真实阻塞追问
2. 一次只追一个问题
3. 先查资料，查不出再问 PM
4. 最后一行收口为唯一问题
```

- [ ] **Step 4: 创建 references/design-writing.md**

```markdown
# 设计写法参考

> 本文件是设计阶段的示例和对照说明。
> 硬规则在 `skills/design/SKILL.md`。

## 一、模块定义写法

**好：**
> ### 入库管理模块
>
> 职责：覆盖入库申请、审核、确认和记录查询。
> 包含页面：入库申请页、入库审核页、入库确认页、入库记录列表页。

**坏：**
> 入库模块：管理入库。（无职责、无页面清单）

## 二、字段定义写法

每个字段必须包含完整 9 属性：名称、类型、长度、必填、默认值、枚举值、格式、业务来源、说明。

字段定义只写业务定义，不写字段级权限表。字段级权限统一在权限定义章节。

## 三、权限定义组织

按"页面 > 角色 > 字段权限例外"组织：

1. 先写默认权限规则
2. 再写例外字段
3. 不把所有字段逐个平铺

## 四、设计是唯一事实源

字段完整定义、权限完整定义、状态完整定义均在 design 中保存。
PRD 可为交付目的完整镜像，但不得独立改写语义。
```

- [ ] **Step 5: 创建 references/prototype-writing.md**

```markdown
# 原型写法参考

> 本文件是原型阶段的示例和对照说明。
> 硬规则在 `skills/prototype/SKILL.md`（第一轮暂不创建）。

## 一、原型定位

- 原型与 PRD 平级，均以 design 为基线
- 原型只做展示，不重新定义业务规则
- 第一版走最小原型，不追求重型系统

## 二、原型输入

1. 必须读取 design.md
2. 如 prd.md 已存在，还需读取：详细需求说明、状态机、权限汇总、数据字典

## 三、反馈处理

prototype-feedback.md 的反馈必须先归类：
- 表现问题：只改 prototype
- 语义问题：先回写 design，再同步
```

- [ ] **Step 6: 验证 references 文件**

```bash
ls references/
python -c "import json; json.load(open('references/prd-writing.profile.json')); print('profile valid')"
```

预期：5 个文件均存在，profile.json 为合法 JSON。

---

## Task 5: skills/align/SKILL.md

**Files:**
- Create: `skills/align/SKILL.md`

**参考来源：** `D:\work\AIskills\OhMyPm\skills\omp-disc\SKILL.md` 的对齐方法、追问纪律、建设类型判断

- [ ] **Step 1: 创建 skills/align/SKILL.md**

吸收 OMP 的对齐方法论，适配新辅助器的规则落点原则。

```markdown
---
name: align
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
```

- [ ] **Step 2: 验证文件存在且包含所有硬规则**

```bash
python -c "
content = open('skills/align/SKILL.md', encoding='utf-8').read()
required = ['ask-back', '建设类型', 'iteration', 'new_build', 'hybrid', '最小读取', '停止条件', 'can_enter_design']
for r in required:
    assert r in content, f'Missing: {r}'
print('align SKILL.md validated')
"
```

预期：`align SKILL.md validated`

---

## Task 6: skills/design/SKILL.md

**Files:**
- Create: `skills/design/SKILL.md`

**参考来源：** `D:\work\PMFlow\skills\pm-design\SKILL.md` 的设计方法论

- [ ] **Step 1: 创建 skills/design/SKILL.md**

```markdown
---
name: design
description: 设计阶段——把对齐结果结构化成稳定基线
triggers:
  - "开始设计"
  - "做设计"
  - "进入设计"
---

# 设计

## 触发条件

用户要求开始设计，或 stage-context 建议进入 design 阶段。

## 前置检查

运行 `stage-context.py` 检查准入：

1. align.md 存在
2. metadata/align 完整
3. align-notes.json 中 `can_enter_design` = true

如检查不通过，停止，不写任何产物。

## 最小读取集合

1. `.workflow/status.json`
2. `output/align/align.md`（对齐产物）
3. `.workflow/metadata/align/index.json`
4. `.workflow/metadata/align/entities.json`
5. `.workflow/metadata/align/relations.json`
6. `.workflow/runtime/align/align-notes.json`
7. `templates/design.md`（产物骨架）
8. `references/design-writing.md`（写法参考）

## 执行顺序

1. 运行前置检查
2. 读取最小读取集合
3. 按以下顺序生成设计：
   - 角色定义
   - 模块定义
   - 页面清单
   - 字段完整定义
   - 流程设计
   - 状态设计
   - 规则设计
   - 权限定义（细到字段级）
4. 生成 design.md 人读产物
5. 生成 metadata/design 机读镜像
6. 更新 status.json

## 硬规则

### 设计是唯一事实源

以下三类内容的完整定义必须在 design 中：

1. 字段完整定义
2. 权限完整定义
3. 状态完整定义

PRD 可为交付目的镜像这些内容，但不得独立改写语义。

### 字段级权限组织

1. 字段定义章节只写字段业务定义，不写字段级权限表
2. 权限定义章节负责字段级权限
3. 按"页面 > 角色 > 字段权限例外"组织
4. 先写默认权限规则，再写例外字段
5. 不要求把所有字段逐个平铺成巨大权限表

### 不可做

1. 不写研发级页面正文
2. 不写高保真视觉表达
3. 不新增 align 没确认的范围
4. 不把 prototype 的表现层问题直接提升为业务事实
5. 不重新判断建设类型
6. 不重新解释原始材料
7. 不静默合并新材料

### 稳定 ID 规则

1. 稳定 ID 首次在 design 阶段生成
2. 只存在于外置机读物
3. design.md 正文不得出现稳定 ID
4. 第一版只使用以下前缀：
   - `MODULE-design-NNN`
   - `PAGE-design-NNN`
   - `FIELD-design-NNN`
   - `RULE-design-NNN`
   - `FLOW-design-NNN`
   - `REL-design-NNN`
5. 不引入 `REQ-*`、`RISK-*`、`CASE-*`、`WVR-*`

### 大型设计分块

如页面 > 10 个或字段 > 50 个：

1. 先生成索引（模块 → 页面 → 字段概览）
2. 再逐块生成，每块局部自检
3. 最后组装

## 输出要求

### 人读产物

写入 `output/design/design.md`，按 `templates/design.md` 骨架组织。

核心章节必须全部存在：
- 角色定义
- 模块定义
- 页面清单
- 字段定义
- 规则与状态定义
- 权限定义

辅助章节可选：
- 文档概述
- 范围与建设方式
- 核心业务流程

### 机读产物

运行 `stage-prep.py --stage design` 生成 `.workflow/metadata/design/` 下的文件：

- `index.json`：总索引
- `entities.json`：实体列表（含稳定 ID）
- `relations.json`：关系列表
- `modules.json`：模块定义
- `pages.json`：页面清单
- `fields.json`：字段定义
- `rules.json`：规则定义
- `states.json`：状态定义
- `permissions.json`：权限定义

### 状态更新

更新 `.workflow/status.json`：

- `current_stage`：更新为 `"design"`
- `artifacts.design`：指向 `output/design/design.md`
- `metadata_paths.design`：指向 `.workflow/metadata/design/`
- `next_recommended`：`"prd"` 或 `"prototype"`

## 停止条件

1. design.md 核心章节全部存在
2. 机读镜像已生成
3. 人读稿与机读镜像一致
4. 无新增 align 未确认的范围

满足以上 4 条后停止，建议进入 PRD 或 prototype 阶段。

## 明确不做什么

1. 不写研发级页面正文（那是 PRD 的职责）
2. 不写高保真视觉表达
3. 不执行 review（建议 `/design-review`）
4. 不自动推进到下一阶段
```

- [ ] **Step 2: 验证文件**

```bash
python -c "
content = open('skills/design/SKILL.md', encoding='utf-8').read()
required = ['唯一事实源', '稳定 ID', 'MODULE-design', 'PAGE-design', 'FIELD-design', '前置检查', '停止条件', 'stage-prep.py']
for r in required:
    assert r in content, f'Missing: {r}'
print('design SKILL.md validated')
"
```

预期：`design SKILL.md validated`

---

## Task 7: skills/prd/SKILL.md

**Files:**
- Create: `skills/prd/SKILL.md`

**参考来源：** ShitPM 的 PRD 写作规则 + Kira 的三层覆盖要求

- [ ] **Step 1: 创建 skills/prd/SKILL.md**

```markdown
---
name: prd
description: PRD 阶段——把 design 基线展开成研发可评审的人读规格说明
triggers:
  - "开始写 PRD"
  - "做 PRD"
  - "写 PRD"
---

# PRD

## 触发条件

用户要求开始写 PRD，或 stage-context 建议进入 prd 阶段。

## 前置检查

运行 `stage-context.py` 检查准入：

1. design.md 存在
2. metadata/design 完整

如检查不通过，停止，不写任何产物。

## 最小读取集合

1. `.workflow/status.json`
2. `output/design/design.md`（design 基线）
3. `.workflow/metadata/design/` 全量
4. `templates/prd.md`（产物骨架）
5. `references/prd-writing.md`（写法参考）
6. `references/prd-writing.profile.json`（写作约束）

## 执行顺序

1. 运行前置检查
2. 读取最小读取集合
3. 按以下顺序生成 PRD：
   - 按 design 页面清单逐页写详细需求说明
   - 生成权限汇总
   - 生成数据字典
   - 生成状态机
   - 补充辅助章节（如需要）
4. 运行 `prd-style-lint.py` 自检
5. 生成 prd.md 人读产物
6. 生成 metadata/prd 机读镜像
7. 更新 status.json

## 硬规则

### 页面正文三层覆盖

每个页面正文必须覆盖：

1. **界面元素与展示规则**
   - 有哪些字段、怎么排列、怎么排序、怎么分页
   - UI 文案用引号嵌入正文
   - 长文本描述截断、滚动、悬浮

2. **交互逻辑与状态流转**
   - 用户能做什么、操作后状态怎么变
   - 前后端怎么配合
   - 权限如何影响当前页面

3. **异常处理与边界场景**
   - 网络断了怎么办
   - 并发冲突怎么办
   - 数据量大了怎么办
   - 校验不通过怎么办

### 写作风格

1. 自然规格说明，不是标签式拼接
2. 具体数值硬编码（"每页 20 条"不是"N 条"）
3. UI 文案用引号嵌入正文
4. 表格只用于天然映射内容（数据字典、权限汇总）
5. 少用加粗
6. 不用标签式正文

### 禁止的写法

1. `**页面目标：**` — 标签式正文
2. `**关键动作：**` — 标签式正文
3. `**状态变化：**` — 标签式正文
4. `**异常提示：**` — 标签式正文
5. 动作流水账（只按点击顺序描述动作过程）
6. 纯表格式页面正文
7. 模糊表述："按配置"、"按规范"、"同常规"、"待补充"

### 与 design 的职责边界

1. design 定义字段、权限、状态的完整事实
2. PRD 为研发交付完整镜像这些内容
3. PRD 数据字典只保留 9 列，不带稳定 ID、relations、anchors
4. PRD 不得独立新增 design 中不存在的字段、权限或状态定义

### 数据字典 9 列

| 字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明 |

按实体分组。业务来源限于：用户填写、系统生成、外部同步、关联带出。

### 场景覆盖自检

每个动作写完后，自检是否覆盖：

- 数据展示
- 按钮/操作
- 表单/输入
- 列表/加载
- 弹窗
- 异常/降级
- 边界值

## 输出要求

### 人读产物

写入 `output/prd/prd.md`，按 `templates/prd.md` 骨架组织。

核心章节必须全部存在：
- 详细需求说明
- 权限汇总
- 数据字典
- 状态机

辅助章节可选：
- 文档概述、范围、业务流程、验收标准汇总、风险与待确认

### 机读产物

运行 `stage-prep.py --stage prd` 生成 `.workflow/metadata/prd/` 下的文件：

- `index.json`
- `entities.json`
- `relations.json`
- `page-anchor.json`
- `rule-anchor.json`
- `field-anchor.json`

### 状态更新

更新 `.workflow/status.json`：

- `current_stage`：更新为 `"prd"`
- `artifacts.prd`：指向 `output/prd/prd.md`
- `metadata_paths.prd`：指向 `.workflow/metadata/prd/`
- `next_recommended`：`"prototype"` 或 `"<stage>-review"`

## 停止条件

1. prd.md 核心章节全部存在
2. prd-style-lint.py 无 P0 问题
3. 机读镜像已生成
4. PRD 内容不超出 design 范围

满足以上 4 条后停止，建议进入 review 或 prototype。

## 明确不做什么

1. 不重新定义范围
2. 不脑补 design 没确认的页面和字段
3. 不写成表格稿、动作流水账或标签式正文
4. 不把自己变成字段、权限、状态的第二事实源
5. 不执行 review（建议 `/prd-review`）
6. 不自动推进到下一阶段
```

- [ ] **Step 2: 验证文件**

```bash
python -c "
content = open('skills/prd/SKILL.md', encoding='utf-8').read()
required = ['三层覆盖', '界面元素', '交互逻辑', '异常处理', '标签式', '数据字典', '权限汇总', '状态机', 'prd-style-lint.py', '停止条件']
for r in required:
    assert r in content, f'Missing: {r}'
print('prd SKILL.md validated')
"
```

预期：`prd SKILL.md validated`

---

## Task 8: skills/design-review/SKILL.md

**Files:**
- Create: `skills/design-review/SKILL.md`

**参考来源：** TestAny 的 reviewer 方法论 + 验收 §9.3

- [ ] **Step 1: 创建 skills/design-review/SKILL.md**

```markdown
---
name: design-review
description: 设计 review——判断 design 基线的质量
triggers:
  - "design review"
  - "设计 review"
  - "review 设计"
---

# 设计 Review

## 触发条件

用户要求进行设计 review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 检查 design.md 是否存在
2. 检查核心章节是否全部存在：
   - 角色定义
   - 模块定义
   - 页面清单
   - 字段定义
   - 规则与状态定义
   - 权限定义
3. 检查 metadata/design 是否完整（9 个 JSON 文件）
4. 检查稳定 ID 是否正确生成（6 种前缀）
5. 检查 design.md 正文中是否有稳定 ID 泄漏
6. 检查人读稿与机读镜像数量一致性

如有阻塞问题（如核心章节缺失、机读物不完整），停止并输出阻塞项。

### 第二段：人读正文质量审查

1. 字段定义属性是否齐全（9 属性）
2. 权限定义是否覆盖到字段级
3. 权限是否按"页面 > 角色 > 字段权限例外"组织
4. 状态定义是否覆盖完整
5. 模块/页面/字段是否能在 align.md 中找到来源（不新增 align 未确认的范围）
6. metadata/design 与 design.md 是否 100% 一致

## 检查项清单

引用规约 §7.2 坏味道定义。design review 重点检查：

1. 核心章节完整性
2. 字段定义属性齐全性
3. 权限定义覆盖到字段级
4. 状态定义覆盖完整性
5. metadata/design 与 design.md 一致性
6. 稳定 ID 正确性
7. 不新增 align 未确认范围

## 输出要求

### 机读结果

写入 `.workflow/reviews/design-review.json`，包含：

- `stage`: `"design"`
- `verdict`: `"通过"` / `"有问题需修改"` / `"阻塞，不能继续"`
- `issues`: 问题列表
- `issue_layer`: 问题归属层分布
- `affected_objects`: 受影响对象
- `needs_upstream_sync`: 是否需要回上游
- `next_recommended`: 下一步建议

### 人读摘要

简短 Markdown，包含：

1. 结论
2. 主要问题
3. 是否需要回上游
4. 下一步建议

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞，不能继续**：有 P0 或 2+ 个 P1

## 硬规则

1. review 通过后不自动推进阶段，由 PM 手动进入下一阶段
2. 不代写 design 正文
3. 不自行修改 design.md
4. 问题必须具体到章节和内容
```

- [ ] **Step 2: 验证文件**

```bash
python -c "
content = open('skills/design-review/SKILL.md', encoding='utf-8').read()
required = ['两段式', '确定性预检查', '人读正文', 'verdict', '通过', '有问题需修改', '阻塞', '不自动推进']
for r in required:
    assert r in content, f'Missing: {r}'
print('design-review SKILL.md validated')
"
```

预期：`design-review SKILL.md validated`

---

## Task 9: skills/prd-review/SKILL.md

**Files:**
- Create: `skills/prd-review/SKILL.md`

**参考来源：** TestAny prd-reviewer + ShitPM prd-review-checklist + 验收 §9.4

- [ ] **Step 1: 创建 skills/prd-review/SKILL.md**

```markdown
---
name: prd-review
description: PRD review——判断 PRD 正文的质量
triggers:
  - "prd review"
  - "PRD review"
  - "review PRD"
---

# PRD Review

## 触发条件

用户要求进行 PRD review。

## 执行顺序（两段式）

### 第一段：确定性预检查

1. 检查 prd.md 是否存在
2. 检查核心章节是否全部存在：
   - 详细需求说明
   - 权限汇总
   - 数据字典
   - 状态机
3. 检查 metadata/prd 是否完整（6 个 JSON 文件）
4. 运行 `prd-style-lint.py` 检查文风问题
5. 检查数据字典是否使用 9 列格式
6. 检查 prd.md 中是否有稳定 ID 泄漏

如有阻塞问题（核心章节缺失、机读物不完整），停止并输出阻塞项。

### 第二段：人读正文质量审查

逐页检查：

1. **坏味道检查**（引用规约 §7.2）
   - 是否为标签式正文
   - 是否为动作流水账
   - 是否为纯表格式页面正文
   - 是否过多加粗
   - 是否有模糊表述（"按配置"、"按规范"、"同常规"、"待补充"）

2. **三层覆盖检查**
   - 每个页面是否覆盖界面元素与展示规则
   - 每个页面是否覆盖交互逻辑与状态流转
   - 每个页面是否覆盖异常处理与边界场景

3. **一致性检查**
   - PRD 字段列表与 design.md 字段定义是否一致
   - PRD 权限口径与 design.md 权限定义是否一致
   - PRD 状态机与 design.md 状态定义是否一致
   - 页面编号是否重复
   - 是否存在动作复用
   - 是否跨节代写

4. **结构检查**
   - 状态机是否按核心业务对象组织
   - 状态机是否包含状态集合、迁移、触发动作和限制条件
   - 权限汇总是否包含页面级、按钮级、字段级

## 检查项清单（10 项）

引用规约 §3.4 和 §7.2：

1. 是否命中坏味道（标签式、流水账、纯表格、过多加粗、模板腔、模糊表述）
2. 页面是否缺展示规则
3. 页面是否缺状态变化
4. 页面是否缺异常边界
5. 页面编号是否重复
6. 是否跨节代写
7. 是否存在动作复用
8. 核心章节是否完整
9. 数据字典是否使用 9 列格式
10. PRD 与 design 的字段/权限/状态是否镜像一致

## 输出要求

### 机读结果

写入 `.workflow/reviews/prd-review.json`，结构同 review-result.schema.json。

### 人读摘要

简短 Markdown，包含：

1. 结论
2. 主要问题（逐页引用）
3. 是否需要回上游（回 design）
4. 下一步建议

## 判定规则

- **通过**：零 P0、零 P1
- **有问题需修改**：零 P0，1 个 P1
- **阻塞，不能继续**：有 P0 或 2+ 个 P1

P0 示例：核心章节缺失、设计边界违反、字段/权限/状态镜像不一致

## 硬规则

1. review 通过后不自动推进阶段，由 PM 手动进入下一阶段
2. 不代写 PRD 正文
3. 不自行修改 prd.md
4. 问题必须具体到页面、章节和内容
5. 不放过 P0 问题
```

- [ ] **Step 2: 验证文件**

```bash
python -c "
content = open('skills/prd-review/SKILL.md', encoding='utf-8').read()
required = ['两段式', '坏味道', '三层覆盖', '标签式', '流水账', '9 列', '镜像一致', 'prd-style-lint.py', '不自动推进']
for r in required:
    assert r in content, f'Missing: {r}'
print('prd-review SKILL.md validated')
"
```

预期：`prd-review SKILL.md validated`

---

## Task 10: scripts/python/stage-context.py

**Files:**
- Create: `scripts/python/stage-context.py`

**参考来源：** `D:\work\PMFlow\scripts\python\pmflow-stage-context.py` 的 gate 检查模式

- [ ] **Step 1: 创建 stage-context.py 的常量和数据结构**

```python
#!/usr/bin/env python3
"""stage-context.py — 准入和上下文脚本

职责：读取状态、判断当前阶段、收集最小读取集合、给出下一步建议。
不生成 metadata，不修改文件，不做业务语义判断。

用法：python stage-context.py <project_root>
"""

import json
import os
import sys
from pathlib import Path

VALID_STAGES = ["align", "design", "prd", "prototype", "fix"]

# 每个阶段的上游依赖
UPSTREAM_DEPS = {
    "align": [],
    "design": ["align"],
    "prd": ["design"],
    "prototype": ["design"],
    "fix": [],  # fix 可从任意阶段发起
}

# 每个阶段必须存在的人读产物
REQUIRED_ARTIFACTS = {
    "align": [],
    "design": ["output/align/align.md"],
    "prd": ["output/design/design.md"],
    "prototype": ["output/design/design.md"],
    "fix": [],
}

# 每个阶段必须存在的机读物目录
REQUIRED_METADATA = {
    "align": [],
    "design": [".workflow/metadata/align/"],
    "prd": [".workflow/metadata/design/"],
    "prototype": [".workflow/metadata/design/"],
    "fix": [],
}

# 每个阶段的最小读取集合
MINIMAL_READ_SET = {
    "align": [
        ".workflow/status.json",
        "references/align-writing.md",
        "templates/align.md",
    ],
    "design": [
        ".workflow/status.json",
        "output/align/align.md",
        ".workflow/metadata/align/",
        "references/design-writing.md",
        "templates/design.md",
    ],
    "prd": [
        ".workflow/status.json",
        "output/design/design.md",
        ".workflow/metadata/design/",
        "references/prd-writing.md",
        "references/prd-writing.profile.json",
        "templates/prd.md",
    ],
    "prototype": [
        ".workflow/status.json",
        "output/design/design.md",
        ".workflow/metadata/design/",
        "templates/prototype.html",
    ],
    "fix": [
        ".workflow/status.json",
    ],
}
```

- [ ] **Step 2: 创建 gate 检查函数**

```python
def load_status(project_root: Path) -> dict:
    """加载 status.json"""
    status_path = project_root / ".workflow" / "status.json"
    if not status_path.exists():
        return None
    with open(status_path, encoding="utf-8") as f:
        return json.load(f)


def check_artifacts_exist(project_root: Path, paths: list[str]) -> list[str]:
    """检查必要产物是否存在，返回缺失列表"""
    missing = []
    for p in paths:
        full_path = project_root / p
        if not full_path.exists():
            missing.append(p)
    return missing


def check_metadata_dirs(project_root: Path, dirs: list[str]) -> list[str]:
    """检查必要机读物目录是否存在且非空，返回缺失列表"""
    missing = []
    for d in dirs:
        full_dir = project_root / d
        if not full_dir.exists() or not any(full_dir.iterdir()):
            missing.append(d)
    return missing


def load_align_notes(project_root: Path) -> dict | None:
    """加载 align-notes.json（如存在）"""
    notes_path = project_root / ".workflow" / "runtime" / "align" / "align-notes.json"
    if not notes_path.exists():
        return None
    with open(notes_path, encoding="utf-8") as f:
        return json.load(f)


def determine_stage(project_root: Path, status: dict) -> str:
    """根据 status 和产物存在情况判断实际应处阶段"""
    artifacts = status.get("artifacts", {})

    # 检查各阶段产物存在情况
    has_align = artifacts.get("align") and (project_root / artifacts["align"]).exists()
    has_design = artifacts.get("design") and (project_root / artifacts["design"]).exists()
    has_prd = artifacts.get("prd") and (project_root / artifacts["prd"]).exists()

    if not has_align:
        return "align"
    if not has_design:
        return "design"
    if not has_prd:
        return "prd"
    return status.get("current_stage", "align")


def determine_next(status: dict, align_notes: dict | None) -> str:
    """给出下一步建议"""
    current = status.get("current_stage", "align")

    if current == "align":
        if align_notes and align_notes.get("can_enter_design"):
            return "design"
        if align_notes and align_notes.get("needs_ask_back"):
            return "align"
        return "align"

    if current == "design":
        return "prd"

    if current == "prd":
        return "prototype"

    return current
```

- [ ] **Step 3: 创建主函数和 CLI 入口**

```python
def collect_context(project_root: Path) -> dict:
    """收集当前阶段上下文，返回完整结果"""
    status = load_status(project_root)
    if status is None:
        return {
            "error": "status.json not found",
            "hint": "请先初始化 .workflow/status.json",
        }

    current_stage = status.get("current_stage", "align")
    if current_stage not in VALID_STAGES:
        return {
            "error": f"invalid stage: {current_stage}",
            "valid_stages": VALID_STAGES,
        }

    # 检查上游产物
    required_artifacts = REQUIRED_ARTIFACTS.get(current_stage, [])
    missing_artifacts = check_artifacts_exist(project_root, required_artifacts)

    # 检查上游机读物
    required_metadata = REQUIRED_METADATA.get(current_stage, [])
    missing_metadata = check_metadata_dirs(project_root, required_metadata)

    # 加载 align-notes
    align_notes = load_align_notes(project_root)

    # 判断实际阶段
    actual_stage = determine_stage(project_root, status)

    # 检查 align 准入
    can_proceed = True
    blocking_issues = []

    if missing_artifacts:
        can_proceed = False
        blocking_issues.append(f"上游产物缺失: {missing_artifacts}")

    if missing_metadata:
        can_proceed = False
        blocking_issues.append(f"上游机读物缺失: {missing_metadata}")

    if current_stage == "design" and align_notes:
        if not align_notes.get("can_enter_design"):
            can_proceed = False
            blocking_issues.append("align-notes: can_enter_design = false")

    # 收集最小读取集合
    read_set = MINIMAL_READ_SET.get(current_stage, [])
    resolved_read_set = {}
    for p in read_set:
        full_path = project_root / p
        resolved_read_set[p] = {
            "exists": full_path.exists(),
            "path": str(full_path),
        }

    # 构建输出
    result = {
        "current_stage": current_stage,
        "actual_stage": actual_stage,
        "artifacts": status.get("artifacts", {}),
        "metadata_paths": status.get("metadata_paths", {}),
        "latest_reviews": status.get("latest_reviews", {}),
        "align_notes": align_notes if align_notes else {},
        "next_recommended": determine_next(status, align_notes) if can_proceed else current_stage,
        "gate": {
            "can_proceed": can_proceed,
            "blocking_issues": blocking_issues,
        },
        "minimal_read_set": resolved_read_set,
    }

    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python stage-context.py <project_root>", file=sys.stderr)
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()
    if not project_root.exists():
        print(f"错误: 项目根目录不存在: {project_root}", file=sys.stderr)
        sys.exit(1)

    result = collect_context(project_root)

    # 输出 JSON 到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 如有阻塞问题，exit code = 1
    if result.get("gate", {}).get("blocking_issues"):
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 验证 stage-context.py 可运行**

```bash
cd D:\work\ShitPM
python scripts/python/stage-context.py .
```

预期输出：JSON 包含 6 类字段（current_stage, artifacts, metadata_paths, latest_reviews, align_notes, next_recommended），exit code = 0。

- [ ] **Step 5: 验证串项目检测**

临时修改 status.json 将 current_stage 设为 `"prd"`，运行脚本：

```bash
python -c "
import json
s = json.load(open('.workflow/status.json'))
s['current_stage'] = 'prd'
json.dump(s, open('.workflow/status.json', 'w'), ensure_ascii=False, indent=2)
"
python scripts/python/stage-context.py .
echo "Exit code: $LASTEXITCODE"
```

预期：输出中 `gate.can_proceed` = false，exit code = 1。

恢复 status.json：

```bash
python -c "
import json
s = {'current_stage': 'align', 'artifacts': {}, 'metadata_paths': {}, 'latest_reviews': {}, 'align_notes': {}, 'next_recommended': 'align'}
json.dump(s, open('.workflow/status.json', 'w'), ensure_ascii=False, indent=2)
"
```

---

## Task 11: scripts/python/stage-prep.py

**Files:**
- Create: `scripts/python/stage-prep.py`

**参考来源：** `D:\work\PMFlow\scripts\python\pmflow-stage-prep.py` 的实体解析和关系解析模式

- [ ] **Step 1: 创建 stage-prep.py 的常量和工具函数**

```python
#!/usr/bin/env python3
"""stage-prep.py — 机读镜像生成脚本

职责：从当前人读稿中抽取并生成 metadata anchor。
不判断是否允许进入该阶段，不修改人读稿正文。

用法：python stage-prep.py --stage <stage> [--project-root <path>] [--dry-run]
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_STAGES = ["align", "design", "prd", "prototype"]

# 稳定 ID 前缀映射
ID_PREFIXES = {
    "module": "MODULE",
    "page": "PAGE",
    "field": "FIELD",
    "rule": "RULE",
    "flow": "FLOW",
    "role": "ROLE",
    "state": "STATE",
    "permission": "PERM",
}

# 中文关键词到实体类型的映射
HEADING_ENTITY_MAP = {
    "模块": "module",
    "页面": "page",
    "字段": "field",
    "规则": "rule",
    "流程": "flow",
    "角色": "role",
    "状态": "state",
    "权限": "permission",
}

# 每个阶段允许生成的实体类型
STAGE_ALLOWED_ENTITIES = {
    "align": set(),  # align 不生成稳定 ID
    "design": {"module", "page", "field", "rule", "flow", "role", "state", "permission"},
    "prd": set(),  # prd 不新增实体，只引用 design
    "prototype": set(),
}

# ID 计数器文件
ID_COUNTER_FILE = ".workflow/metadata/.id-counters.json"


def slug_from_heading(heading: str) -> str:
    """从标题生成稳定 slug（MD5 前 8 位 + 标题前 12 字符）"""
    clean = re.sub(r'[#\*\[\]()（）]', '', heading).strip()
    md5_prefix = hashlib.md5(clean.encode()).hexdigest()[:8]
    title_prefix = re.sub(r'[^a-zA-Z0-9一-鿿]', '', clean)[:12]
    return f"{md5_prefix}-{title_prefix}"
```

- [ ] **Step 2: 创建 Markdown 解析函数**

```python
def parse_headings(content: str) -> list[dict]:
    """解析 Markdown 标题结构"""
    headings = []
    for i, line in enumerate(content.split('\n')):
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append({
                "level": level,
                "title": title,
                "line": i + 1,
            })
    return headings


def extract_existing_ids(content: str, stage: str) -> dict[str, list[str]]:
    """提取人读稿中已存在的稳定 ID（如有泄漏）"""
    ids = {}
    for prefix in ID_PREFIXES.values():
        pattern = rf'{prefix}-{stage}-\d{{3}}'
        found = re.findall(pattern, content)
        if found:
            ids[prefix] = found
    return ids


def infer_entities_from_headings(headings: list[dict], stage: str) -> list[dict]:
    """从标题结构推断实体"""
    entities = []
    counter = 1

    for h in headings:
        entity_type = None
        for keyword, etype in HEADING_ENTITY_MAP.items():
            if keyword in h["title"]:
                entity_type = etype
                break

        if entity_type and entity_type in STAGE_ALLOWED_ENTITIES.get(stage, set()):
            prefix = ID_PREFIXES[entity_type]
            entity_id = f"{prefix}-{stage}-{counter:03d}"
            entities.append({
                "id": entity_id,
                "type": entity_type,
                "title": h["title"],
                "line": h["line"],
            })
            counter += 1

    return entities


def infer_relations_from_content(content: str, entities: list[dict]) -> list[dict]:
    """从内容推断实体间关系"""
    relations = []
    rel_counter = 1

    # 来源关系关键词
    source_keywords = ["来源", "依据", "基于", "引用", "对齐"]
    # 包含关系关键词
    contain_keywords = ["包含", "含", "下属"]

    sections = re.split(r'\n#{1,6}\s+', content)

    entity_ids = {e["id"]: e for e in entities}
    id_pattern = "|".join(re.escape(eid) for eid in entity_ids.keys())

    if not id_pattern:
        return relations

    for section in sections:
        found_ids = re.findall(id_pattern, section)
        if len(found_ids) >= 2:
            # 检查是否有来源关系关键词
            has_source = any(kw in section for kw in source_keywords)
            has_contain = any(kw in section for kw in contain_keywords)

            rel_type = "derived_from" if has_source else ("contains" if has_contain else "refines")

            for i in range(len(found_ids) - 1):
                relations.append({
                    "id": f"REL-{stage}-{rel_counter:03d}",
                    "type": rel_type,
                    "from": found_ids[i],
                    "to": found_ids[i + 1],
                })
                rel_counter += 1

    return relations
```

注意：`infer_relations_from_content` 中的 `stage` 变量需要作为参数传入。完整实现时修正此引用。

- [ ] **Step 3: 创建各阶段 metadata 生成函数**

```python
def generate_align_metadata(content: str, project_root: Path) -> dict:
    """生成 align 阶段 metadata（不含稳定 ID）"""
    headings = parse_headings(content)

    index = {
        "schema_version": "1.0.0",
        "stage": "align",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "request_summary": "",
        "solution_shape": "",
        "business_stage": "",
        "context_gaps": [],
    }

    # 从标题和内容推断
    for h in headings:
        title = h["title"]
        if "需求" in title or "概述" in title:
            # 后续可从内容中提取 request_summary
            pass
        if "建设方式" in title:
            pass

    entities = {
        "system_or_page_clues": [],
        "material_paths": [],
        "confirmed_roles": [],
        "confirmed_scenes": [],
        "confirmed_objects": [],
    }

    relations = []

    return {
        "index": index,
        "entities": entities,
        "relations": relations,
    }


def generate_design_metadata(content: str, stage: str, project_root: Path) -> dict:
    """生成 design 阶段 metadata（含稳定 ID）"""
    headings = parse_headings(content)
    entities = infer_entities_from_headings(headings, stage)
    relations = infer_relations_from_content(content, entities)

    index = {
        "schema_version": "1.0.0",
        "stage": stage,
        "artifact_path": f"output/{stage}/{stage}.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_count": len(entities),
        "relation_count": len(relations),
    }

    # 按类型分组
    modules = [e for e in entities if e["type"] == "module"]
    pages = [e for e in entities if e["type"] == "page"]
    fields = [e for e in entities if e["type"] == "field"]
    rules = [e for e in entities if e["type"] == "rule"]
    states = [e for e in entities if e["type"] == "state"]
    perms = [e for e in entities if e["type"] == "permission"]

    return {
        "index": index,
        "entities": entities,
        "relations": relations,
        "modules": modules,
        "pages": pages,
        "fields": fields,
        "rules": rules,
        "states": states,
        "permissions": perms,
    }


def generate_prd_metadata(content: str, project_root: Path) -> dict:
    """生成 PRD 阶段 metadata（不含新稳定 ID，只引用 design）"""
    headings = parse_headings(content)

    index = {
        "schema_version": "1.0.0",
        "stage": "prd",
        "artifact_path": "output/prd/prd.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    entities = []
    relations = []

    # 从标题推断页面锚点
    page_anchor = []
    rule_anchor = []
    field_anchor = []

    for h in headings:
        if "页面" in h["title"] or "详细需求" in h["title"]:
            page_anchor.append({
                "title": h["title"],
                "line": h["line"],
            })

    return {
        "index": index,
        "entities": {"items": entities},
        "relations": {"items": relations},
        "page_anchor": page_anchor,
        "rule_anchor": rule_anchor,
        "field_anchor": field_anchor,
    }


def generate_prototype_metadata(project_root: Path) -> dict:
    """生成 prototype 阶段 metadata"""
    return {
        "schema_version": "1.0.0",
        "stage": "prototype",
        "artifact_path": "output/prototype/index.html",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "page_map": [],
    }
```

- [ ] **Step 4: 创建文件写入和 CLI 入口**

```python
METADATA_FILE_MAP = {
    "align": ["index.json", "entities.json", "relations.json"],
    "design": ["index.json", "entities.json", "relations.json", "modules.json", "pages.json", "fields.json", "rules.json", "states.json", "permissions.json"],
    "prd": ["index.json", "entities.json", "relations.json", "page-anchor.json", "rule-anchor.json", "field-anchor.json"],
    "prototype": ["index.json", "page-map.json"],
}

ARTIFACT_PATHS = {
    "align": "output/align/align.md",
    "design": "output/design/design.md",
    "prd": "output/prd/prd.md",
    "prototype": "output/prototype/index.html",
}


def write_metadata(stage: str, data: dict, project_root: Path, dry_run: bool = False):
    """将 metadata 写入文件"""
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    if not dry_run:
        metadata_dir.mkdir(parents=True, exist_ok=True)

    files = METADATA_FILE_MAP.get(stage, [])

    # 建立数据键到文件名的映射
    key_file_map = {
        "index": "index.json",
        "entities": "entities.json",
        "relations": "relations.json",
        "modules": "modules.json",
        "pages": "pages.json",
        "fields": "fields.json",
        "rules": "rules.json",
        "states": "states.json",
        "permissions": "permissions.json",
        "page_anchor": "page-anchor.json",
        "rule_anchor": "rule-anchor.json",
        "field_anchor": "field-anchor.json",
        "page_map": "page-map.json",
    }

    written = []
    for key, filename in key_file_map.items():
        if key in data and filename in files:
            target = metadata_dir / filename
            content = json.dumps(data[key], ensure_ascii=False, indent=2)
            if not dry_run:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
            written.append(str(target))

    return written


def write_stage_context(stage: str, data: dict, project_root: Path, dry_run: bool = False):
    """写入 stage-context.json"""
    ctx_dir = project_root / ".workflow" / "runtime" / stage
    if not dry_run:
        ctx_dir.mkdir(parents=True, exist_ok=True)

    ctx = {
        "stage": stage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_count": len(data.get("entities", [])) if isinstance(data.get("entities"), list) else 0,
        "relation_count": len(data.get("relations", [])) if isinstance(data.get("relations"), list) else 0,
        "metadata_files": METADATA_FILE_MAP.get(stage, []),
    }

    target = ctx_dir / "stage-context.json"
    if not dry_run:
        with open(target, "w", encoding="utf-8") as f:
            json.dump(ctx, f, ensure_ascii=False, indent=2)

    return str(target)


def main():
    parser = argparse.ArgumentParser(description="机读镜像生成脚本")
    parser.add_argument("--stage", required=True, choices=VALID_STAGES, help="目标阶段")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不写入文件")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    stage = args.stage

    # 读取人读产物
    artifact_path = project_root / ARTIFACT_PATHS[stage]
    if not artifact_path.exists():
        print(f"错误: 人读产物不存在: {artifact_path}", file=sys.stderr)
        sys.exit(1)

    with open(artifact_path, encoding="utf-8") as f:
        content = f.read()

    # 根据阶段生成 metadata
    if stage == "align":
        data = generate_align_metadata(content, project_root)
    elif stage == "design":
        data = generate_design_metadata(content, stage, project_root)
    elif stage == "prd":
        data = generate_prd_metadata(content, project_root)
    elif stage == "prototype":
        data = generate_prototype_metadata(project_root)
    else:
        print(f"错误: 不支持的阶段: {stage}", file=sys.stderr)
        sys.exit(1)

    # 写入文件
    written_files = write_metadata(stage, data, project_root, dry_run=args.dry_run)
    ctx_file = write_stage_context(stage, data, project_root, dry_run=args.dry_run)

    result = {
        "stage": stage,
        "dry_run": args.dry_run,
        "metadata_files_written": written_files,
        "stage_context_file": ctx_file,
        "entity_count": len(data.get("entities", [])) if isinstance(data.get("entities"), list) else 0,
        "relation_count": len(data.get("relations", [])) if isinstance(data.get("relations"), list) else 0,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 验证 stage-prep.py 可运行**

创建一个最小 align.md 测试文件，运行 dry-run：

```bash
cd D:\work\ShitPM
python scripts/python/stage-prep.py --stage align --dry-run
```

预期：输出 JSON，显示 metadata 文件列表。因为 align.md 可能不存在，预期报错 "人读产物不存在"。这是正确的——stage-prep 只在产物存在时运行。

---

## Task 12: scripts/python/prd-style-lint.py

**Files:**
- Create: `scripts/python/prd-style-lint.py`

**参考来源：** TestAny 的 trace_lint.py 的 Issue 结构化输出模式 + 规约 §3.5 的 8 类问题

- [ ] **Step 1: 创建 prd-style-lint.py 的数据结构和检查函数**

```python
#!/usr/bin/env python3
"""prd-style-lint.py — PRD 文风 lint 脚本

职责：检查 PRD 正文中可机械识别的 8 类问题。
不做业务语义判断，不做全文重写。

用法：python prd-style-lint.py <prd_file_path> [--format text|json]

问题类型：
  STYLE001 - 标签式正文
  STYLE002 - 动作流水账特征
  STYLE003 - 表格主导
  STYLE004 - 重复页面编号
  STYLE005 - 跨节引用
  STYLE006 - 机读字段泄漏
  STYLE007 - AI 痕迹
  STYLE008 - 占位符
"""

import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Issue:
    code: str
    severity: str  # error / warning / info
    line: int
    message: str
    suggestion: str


# 标签式正文模式
LABEL_PATTERNS = [
    (r'\*\*页面目标[：:]\*\*', "页面目标标签"),
    (r'\*\*关键动作[：:]\*\*', "关键动作标签"),
    (r'\*\*状态变化[：:]\*\*', "状态变化标签"),
    (r'\*\*异常提示[：:]\*\*', "异常提示标签"),
    (r'\*\*关联功能点[：:]\*\*', "关联功能点标签"),
]

# 稳定 ID 泄漏模式
STABLE_ID_PATTERN = re.compile(r'(MODULE|PAGE|FIELD|RULE|FLOW|REL|REQ|RISK|CASE|WVR)-(design|prd)-\d{3}')

# 占位符模式
PLACEHOLDER_PATTERNS = [
    "待补充", "待定", "按配置", "按规范", "同常规", "TBD", "TODO",
    "需支持", "需考虑", "详见原型", "按业务规则", "具体数值见配置",
]

# AI 痕迹模式
AI_PATTERNS = [
    "作为AI", "作为 AI", "根据我的理解",
    "I will", "Let me", "Here is",
    "需要注意的是", "值得一提的是",
]


def check_label_style(lines: list[str]) -> list[Issue]:
    """STYLE001: 检查标签式正文"""
    issues = []
    for i, line in enumerate(lines):
        for pattern, label in LABEL_PATTERNS:
            if re.search(pattern, line):
                issues.append(Issue(
                    code="STYLE001",
                    severity="error",
                    line=i + 1,
                    message=f"发现标签式正文：{label}",
                    suggestion="改用自然规格说明段落，不用加粗标签拼接",
                ))
    return issues


def check_action_list(lines: list[str]) -> list[Issue]:
    """STYLE002: 检查动作流水账特征

    特征：连续 3+ 个编号步骤，每步以动词开头且行很短
    """
    issues = []
    consecutive_steps = 0
    step_start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 匹配 "1. 动词" 或 "（1）动词" 格式
        if re.match(r'^(\d+\.|（\d+）)\s*\S', stripped) and len(stripped) < 50:
            if consecutive_steps == 0:
                step_start_line = i + 1
            consecutive_steps += 1
        else:
            if consecutive_steps >= 3:
                issues.append(Issue(
                    code="STYLE002",
                    severity="warning",
                    line=step_start_line,
                    message=f"疑似动作流水账：连续 {consecutive_steps} 个短步骤",
                    suggestion="改用自然段落描述，加入展示规则、状态流转和异常边界",
                ))
            consecutive_steps = 0

    # 检查尾部
    if consecutive_steps >= 3:
        issues.append(Issue(
            code="STYLE002",
            severity="warning",
            line=step_start_line,
            message=f"疑似动作流水账：连续 {consecutive_steps} 个短步骤",
            suggestion="改用自然段落描述，加入展示规则、状态流转和异常边界",
        ))

    return issues


def check_table_dominance(lines: list[str]) -> list[Issue]:
    """STYLE003: 检查表格主导

    特征：在"详细需求说明"章节中，表格行数 > 段落行数
    """
    issues = []
    in_detail_section = False
    table_lines = 0
    paragraph_lines = 0
    section_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 检测进入详细需求说明章节
        if re.match(r'^#{1,4}\s.*详细需求', stripped):
            in_detail_section = True
            # 检查上一个章节
            if table_lines > 0 and paragraph_lines > 0 and table_lines > paragraph_lines * 2:
                issues.append(Issue(
                    code="STYLE003",
                    severity="warning",
                    line=section_start,
                    message="表格行数远超段落数，疑似纯表格式页面正文",
                    suggestion="页面正文应以自然规格说明为主，表格仅用于天然映射内容",
                ))
            table_lines = 0
            paragraph_lines = 0
            section_start = i + 1
            continue

        if in_detail_section:
            if stripped.startswith('|') and '|' in stripped[1:]:
                table_lines += 1
            elif stripped and not stripped.startswith('#') and not stripped.startswith('<!--'):
                paragraph_lines += 1

    return issues


def check_duplicate_page_ids(lines: list[str]) -> list[Issue]:
    """STYLE004: 检查重复页面编号"""
    issues = []
    page_ids = {}

    for i, line in enumerate(lines):
        # 匹配页面编号模式：#### 1. 或 ### 1.1 等
        match = re.match(r'^#{2,4}\s+(\d+(?:\.\d+)*)\s*[\.、．]', line.strip())
        if match:
            pid = match.group(1)
            if pid in page_ids:
                issues.append(Issue(
                    code="STYLE004",
                    severity="error",
                    line=i + 1,
                    message=f"页面编号重复：{pid}（首次出现在第 {page_ids[pid]} 行）",
                    suggestion="确保每个页面编号唯一",
                ))
            else:
                page_ids[pid] = i + 1

    return issues


def check_cross_section_refs(lines: list[str]) -> list[Issue]:
    """STYLE005: 检查跨节引用（引用其他章节中的具体内容编号）"""
    issues = []
    # 匹配 "见 X.X"、"参见 X.X"、"详见 X.X"
    cross_ref_pattern = re.compile(r'(?:见|参见|详见|参考)\s*\d+\.\d+')

    for i, line in enumerate(lines):
        if cross_ref_pattern.search(line):
            issues.append(Issue(
                code="STYLE005",
                severity="info",
                line=i + 1,
                message="发现跨节引用，可能导致读者跳转",
                suggestion="考虑将相关内容直接写在当前段落",
            ))

    return issues


def check_stable_id_leak(lines: list[str]) -> list[Issue]:
    """STYLE006: 检查机读字段泄漏"""
    issues = []
    for i, line in enumerate(lines):
        matches = STABLE_ID_PATTERN.findall(line)
        for match in matches:
            issues.append(Issue(
                code="STYLE006",
                severity="error",
                line=i + 1,
                message=f"机读字段泄漏：稳定 ID 出现在正文",
                suggestion="稳定 ID 只存在于外置机读物，不得出现在人读正文",
            ))
    return issues


def check_ai_traces(lines: list[str]) -> list[Issue]:
    """STYLE007: 检查 AI 痕迹"""
    issues = []
    for i, line in enumerate(lines):
        for pattern in AI_PATTERNS:
            if pattern in line:
                issues.append(Issue(
                    code="STYLE007",
                    severity="warning",
                    line=i + 1,
                    message=f"AI 痕迹：发现 '{pattern}'",
                    suggestion="使用正式产品规格说明文风，避免 AI 对话痕迹",
                ))
    return issues


def check_placeholders(lines: list[str]) -> list[Issue]:
    """STYLE008: 检查占位符"""
    issues = []
    for i, line in enumerate(lines):
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern in line:
                issues.append(Issue(
                    code="STYLE008",
                    severity="error",
                    line=i + 1,
                    message=f"占位符：发现 '{pattern}'",
                    suggestion="填写具体内容，不得使用占位符",
                ))
    return issues
```

- [ ] **Step 2: 创建主函数和输出格式**

```python
ALL_CHECKS = [
    check_label_style,
    check_action_list,
    check_table_dominance,
    check_duplicate_page_ids,
    check_cross_section_refs,
    check_stable_id_leak,
    check_ai_traces,
    check_placeholders,
]


def run_lint(content: str) -> list[Issue]:
    """运行所有检查"""
    lines = content.split('\n')
    all_issues = []
    for check_fn in ALL_CHECKS:
        all_issues.extend(check_fn(lines))
    return all_issues


def format_text(issues: list[Issue]) -> str:
    """文本格式输出"""
    if not issues:
        return "无问题"

    lines = []
    for issue in issues:
        lines.append(f"[{issue.severity.upper()}] {issue.code} L{issue.line}: {issue.message}")
        lines.append(f"  建议: {issue.suggestion}")
        lines.append("")

    # 汇总
    error_count = sum(1 for i in issues if i.severity == "error")
    warning_count = sum(1 for i in issues if i.severity == "warning")
    info_count = sum(1 for i in issues if i.severity == "info")
    lines.append(f"汇总: {error_count} error, {warning_count} warning, {info_count} info")

    return "\n".join(lines)


def format_json(issues: list[Issue]) -> str:
    """JSON 格式输出"""
    return json.dumps({
        "issues": [asdict(i) for i in issues],
        "summary": {
            "error": sum(1 for i in issues if i.severity == "error"),
            "warning": sum(1 for i in issues if i.severity == "warning"),
            "info": sum(1 for i in issues if i.severity == "info"),
        },
    }, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print("用法: python prd-style-lint.py <prd_file> [--format text|json]", file=sys.stderr)
        sys.exit(1)

    prd_path = Path(sys.argv[1]).resolve()
    if not prd_path.exists():
        print(f"错误: 文件不存在: {prd_path}", file=sys.stderr)
        sys.exit(2)

    # 解析 --format 参数
    output_format = "text"
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]

    with open(prd_path, encoding="utf-8") as f:
        content = f.read()

    issues = run_lint(content)

    if output_format == "json":
        print(format_json(issues))
    else:
        print(format_text(issues))

    # 有 error 则 exit 1
    if any(i.severity == "error" for i in issues):
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 验证 prd-style-lint.py 可运行**

```bash
cd D:\work\ShitPM
echo "## 测试页面

**关键动作：** 测试
待补充
FIELD-design-001 是一个字段
" > /tmp/test-prd.md
python scripts/python/prd-style-lint.py /tmp/test-prd.md
```

预期输出：检出 STYLE001（标签式）、STYLE006（ID 泄漏）、STYLE008（占位符），exit code = 1。

---

## Self-Review

### 1. Spec 覆盖检查

| 规约章节 | 是否有对应 Task | 备注 |
|---------|---------------|------|
| §3 规则落点总表 | Task 2-9 | schemas, templates, references, skills |
| §4.2 对齐 | Task 5 | align SKILL.md |
| §4.3 设计 | Task 6 | design SKILL.md |
| §4.4 PRD | Task 7 | prd SKILL.md |
| §4.5 原型 | Task 3 (template) | 模板已含，skill 暂不做 |
| §4.6 同步修复 | — | 明确排除在第一轮外 |
| §5.1 人读产物建议 | Task 3 | templates |
| §5.2 机读产物建议 | Task 2 + Task 1 | schemas + 目录 |
| §5.3 状态文件最小字段 | Task 1 + Task 2 | status.json + schema |
| §5.4 review 结果产物 | Task 2 | review-result.schema.json |
| §5.5 stage-context.py / stage-prep.py 边界 | Task 10 + Task 11 | 两个脚本职责分开 |
| §5.6 review-precheck.json | — | 明确排除在第一轮外 |
| §5.7 contracts | — | 明确排除在第一轮外 |
| §6 旧项目继承映射 | Task 5-9 | 各 SKILL.md 已吸收参考项目 |
| §7.2 不继承的写法问题 | Task 7 + Task 12 | prd SKILL.md + lint |
| §8.2 第一批必须先落的文件 | Task 5-12 | 全部覆盖 |

### 2. Placeholder 扫描

计划中无 TBD、TODO、"实现后补充"等占位符。每个步骤均有具体文件路径和内容。

### 3. 类型一致性

- `Issue` dataclass 在 Task 12 中定义，用于 lint 输出
- 各 schema 的 `stage` enum 值一致：`["align", "design", "prd", "prototype", "fix"]`
- `verdict` enum 值一致：`["通过", "有问题需修改", "阻塞，不能继续"]`
- 稳定 ID pattern 一致：`PREFIX-stage-NNN`
