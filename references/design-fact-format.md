# 材料事实资产格式

<!-- context:design-fact-contract:start -->

## 适用范围

材料事实分两层落盘：按来源提取的事实文件供 `material-merge` 读取；合并后的
`.workflow/runtime/materials/facts.json` 供 Align、A/B/C 和 Design 读取。两层格式都必须绑定当前 `material_revision`。

材料事实是证据资产，不是最终产品事实源。最终产品事实只能进入设计集清单登记的正式 Design 文件，不能以事实文件数量或格式完整代替语义判断。

## 分来源事实文件

路径：`.workflow/runtime/materials/facts/<source_id>.json`。

```json
{
  "schema_version": "material-fact/v2",
  "source_path": "materials/01-background.md",
  "source_hash": "<64位十六进制>",
  "material_revision": "sha256:<64位十六进制>",
  "facts": [
    {
      "kind": "page|section|field|metric|action|state|enum|rule|exception|integration|non_functional|acceptance|other",
      "statement": "可由材料直接确认的单条事实",
      "source": {"path": "materials/01-background.md", "sha256": "...", "line_start": 1, "line_end": 8}
    }
  ]
}
```

`source_path`、`source_hash` 必须对应动作输入的单一材料；每条事实必须有可定位来源行范围。不得把跨来源冲突、用户回答或模型推测写入已确认事实。`kind` 用来保护事实粒度，不得把多个不同字段、操作或枚举合并成一条摘要。

至少逐项保留：目标和范围、角色边界、页面/子页面/区块、展示/搜索/筛选/表单字段、统计指标、操作及前置和结果、状态迁移、枚举和数据字典、规则和统计口径、异常和恢复、外部系统和数据流向、非功能与验收。

## 合并事实库

路径：`.workflow/runtime/materials/facts.json`。顶层格式固定为：

```json
{
  "version": 1,
  "material_revision": "sha256:<64位十六进制>",
  "confirmed_facts": [],
  "source_conflicts": [],
  "missing_information": [],
  "non_derivable_items": []
}
```

四个数组都必须存在。每项必须是对象，包含 `source.path`、合法的 `source.line_start` / `source.line_end`，以及 `statement`、`description`、`claim` 三者之一；`source.path` 必须出现在 `source-index.json`，`source.sha256`（如填写）必须与索引一致。

`confirmed_facts` 中的事实应保持字段级、操作级、规则级和枚举级粒度；`source_conflicts` 保留冲突双方和影响；`missing_information` 保留材料没有说明的事项；`non_derivable_items` 保留不能从材料安全推出、需要用户判断的事项。

下游在形成 Design 时按以下最小口径表达事实状态：已定义对应 `confirmed_facts`；局部定义同时保留已确认事实并把缺失部分写入 `missing_information` 或 `non_derivable_items`；未定义写入 `missing_information`/`non_derivable_items`；冲突写入 `source_conflicts`，并说明影响对象和受影响模块。不能因为 `confirmed_facts` 非空就把局部定义、未定义或冲突事项写成完整确定事实。

无材料时允许 `material_revision` 对应空来源集合、四个数组为空；不得伪造来源路径或行号，需求事实由 Align 的用户原话和回答承接。

## 禁止事项

- 不把没有材料证据的推断放入 `confirmed_facts`；
- 不省略冲突、缺失信息或不可推导项来制造“事实已完整”的假象；
- 不使用旧的 `facts/v2` 合并格式替代上述 `version: 1` 格式；
- 不跨材料复制同一来源引用，行范围超界必须修复来源或标记缺失；
- 不把“相关字段”“基本信息”“支持查询等”当作多个详细事实的替代；
- 不把事实资产、Align 摘要或中间基线作为最终 Design 的唯一输入。

<!-- context:design-fact-contract:end -->
