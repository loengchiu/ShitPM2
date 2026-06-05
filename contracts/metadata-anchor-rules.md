# Metadata Anchor 规则

> 本文件是 stage-prep.py（anchor 生成）和 anchor-verify.py（anchor 校验）的规则来源。
> 引用规约 §3.6 和 §5.2。

## 失败模式速查表

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|---|
| stable ID 编号跳跃 | stage-prep.py 运行中断后重跑 | read_existing_entities() 从 max+1 继续，跳号正常 | 若跳号影响追溯，手动检查 fields.json |
| ID 前缀用错 | 把 REQ- 或 RISK- 写入 metadata | 只允许 6 种前缀：MODULE/PAGE/FIELD/RULE/FLOW/REL | 全文搜索非法前缀并替换 |
| ID 泄漏到人读正文 | design.md 或 prd.md 出现 FIELD-design-001 | 运行 review-precheck.py 检查 stable_id_leak | 手动搜索并删除正文中的 ID |
| 关系引用的实体不存在 | relations.json 中 from/to 引用了未定义的 ID | 检查 entities.json 中是否有对应 ID | 若实体已删除，同步删除关系记录 |
| metadata 文件为空数组 | stage-prep.py 未提取到内容 | 检查 design.md 对应章节是否有结构化表格 | 若表格格式被破坏，修复 design.md 后重新生成 |
| 多次 re-extract 后 ID 不稳定 | design.md 表格顺序变化 | read_existing_entities() 按 title 匹配已有 ID | 若 title 也变了，视为新实体 |
| page-fields 覆盖率不足 | 页面清单中有页面未出现在 page-fields.json | 检查 design.md 的页面与字段落点章节是否遗漏 | 若页面无业务字段，声明 declared_empty |
| field-constraints 与 design.md 不一致 | multi_select 标记错误 | 运行 review-precheck.py 的 field_constraints_consistency | 手动比对 JSON 与 design.md |

## 反例黑名单（不要做的事）

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|---|---|---|
| 1 | **手动编写 metadata JSON** | 容易与人读稿不一致 | 由 stage-prep.py 自动生成 |
| 2 | **在正文中使用稳定 ID** | 违反人读机读分离原则 | ID 只存在于 .workflow/metadata/ |
| 3 | **引入 REQ-/RISK-/CASE-/WVR- 前缀** | 第一版只允许 6 种前缀 | 如需新类型，先更新本文件再实现 |
| 4 | **把下游实体塞回上游关系** | 违反关系独立建模原则 | 关系用 REL- 前缀独立 ID |
| 5 | **跳过 read_existing_entities()** | 新运行会重排已有 ID | 每次生成前先读取已有 ID 映射 |
| 6 | **metadata 文件留空不报错** | 空文件可能是提取失败，不是真没内容 | 检查 METADATA_EMPTY_OK 白名单 |

---


## 一、稳定 ID 前缀规范

第一版只使用以下 6 种前缀：

| 前缀 | 对象 | 示例 |
|------|------|------|
| `MODULE-` | 模块 | `MODULE-design-001` |
| `PAGE-` | 页面 | `PAGE-design-001` |
| `FIELD-` | 字段 | `FIELD-design-001` |
| `RULE-` | 规则 | `RULE-design-001` |
| `FLOW-` | 流程 | `FLOW-design-001` |
| `REL-` | 关系 | `REL-design-001` |

不引入：`REQ-*`、`RISK-*`、`CASE-*`、`WVR-*`

## 二、ID 生成规则

1. 稳定 ID 首次在 design 阶段生成
2. 稳定 ID 只存在于外置机读物（`.workflow/metadata/`）
3. PRD、prototype 正文不得出现稳定 ID
4. ID 格式：`{PREFIX}-{stage}-{NNN}`，NNN 为 3 位数字
5. 同一前缀的编号只增不减，多次运行从 max+1 继续
6. 同步修复时由脚本维护稳定 ID，不靠人工手改

## 三、关系建模规范

1. 关系使用 `REL-` 前缀的独立 ID
2. 关系独立建模，不把下游桶塞回上游对象
3. 关系类型：
   - `derived_from`：来源关系
   - `refines`：细化关系
   - `depends_on`：依赖关系
   - `contains`：包含关系
   - `uses`：使用关系
   - `verifies`：验证关系
4. 关系的 `from` 和 `to` 必须引用已存在的实体 ID

## 四、metadata 文件清单

### design 阶段（11 个文件）

- `index.json`：总索引
- `entities.json`：实体列表
- `relations.json`：关系列表
- `modules.json`：模块定义
- `pages.json`：页面清单
- `fields.json`：字段定义
- `rules.json`：规则定义
- `states.json`：状态定义
- `permissions.json`：权限定义
- `page-fields.json`：页面与字段落点映射
- `non-page-fields.json`：非页面落点字段例外表

### PRD 阶段（6 个文件）

- `index.json`：总索引
- `entities.json`：实体列表
- `relations.json`：关系列表
- `page-anchor.json`：页面锚点
- `rule-anchor.json`：规则锚点
- `field-anchor.json`：字段锚点
