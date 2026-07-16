# Metadata 规则

> 本文件是 stage-prep.py（metadata 生成）和 verify-against-metadata.py（结构校验）的规则来源。
> 引用规约 §3.6 和 §5.2。

## 失败模式速查表

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|---|
| stable ID 编号跳跃 | stage-prep.py 运行中断后重跑 | read_existing_entities() 从 max+1 继续，跳号正常 | 若跳号影响追溯，手动检查 fields.json |
| ID 前缀用错 | 把 REQ- 或 RISK- 写入 metadata | 只允许 8 种前缀：MODULE/PAGE/FIELD/RULE/FLOW/REL/STATE/PERM | 全文搜索非法前缀并替换 |
| ID 前缀与 type 不匹配 | 历史 pages.json 误用 PERM- 前缀 | read_existing_entities() 前缀校验：前缀不符 type 则不复用，重新分配 | 清空 metadata 目录重跑 stage-prep |
| ID 泄漏到人读正文 | design.md 或 prd.md 出现 FIELD-design-001 | 运行 review-precheck.py 检查 stable_id_leak | 手动搜索并删除正文中的 ID |
| 关系引用的实体不存在 | relations.json 中 from/to 引用了未定义的 ID | 检查 modules.json/pages.json/fields.json/rules.json 中是否有对应 ID | 若实体已删除，同步删除关系记录 |
| metadata 文件为空数组 | stage-prep.py 未提取到内容 | 检查 design.md 对应章节是否有结构化表格 | 若表格格式被破坏，修复 design.md 后重新生成 |
| 多次 re-extract 后 ID 不稳定 | design.md 表格顺序变化 | read_existing_entities() 按 title 匹配已有 ID | 若 title 也变了，视为新实体 |
| page-fields 覆盖率不足 | 页面清单中有页面未出现在 page-fields.json | 检查 design.md 的页面与字段落点章节是否遗漏 | 若页面无业务字段，声明 declared_empty |
| schema 校验失败 | metadata 文件结构不符合 schema | 查看 verify-against-metadata.py 的 integrity_errors 详情 | 按 schema 修正后重跑 stage-prep |
| metadata 与正文数量不一致 | 字段数/页面数/模块数对比偏差 | 运行 stage-prep.py --stage design 重新生成 | 若重新生成仍不一致，检查 design.md 表格格式 |
| 状态/权限提取到章节标题 | states.json 含"状态集合"等容器标题 | _extract_states_from_content 改解析列表项，非标题 | 确认 design 状态章节格式为列表项 |

## 反例黑名单（不要做的事）

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|---|---|---|
| 1 | **手动编写 metadata JSON** | 容易与人读稿不一致 | 由 stage-prep.py 自动生成 |
| 2 | **在正文中使用稳定 ID** | 违反人读机读分离原则 | ID 只存在于 .workflow/metadata/ |
| 3 | **引入 REQ-/RISK-/CASE-/WVR- 前缀** | 第一版只允许 8 种前缀 | 如需新类型，先更新本文件再实现 |
| 4 | **把下游实体塞回上游关系** | 违反关系独立建模原则 | 关系用 REL- 前缀独立 ID |
| 5 | **跳过 read_existing_entities()** | 新运行会重排已有 ID | 每次生成前先读取已有 ID 映射 |
| 6 | **metadata 文件留空不报错** | 空文件可能是提取失败，不是真没内容 | 检查 METADATA_EMPTY_OK 白名单 |


## 一、稳定 ID 前缀规范

第一版只使用以下 8 种前缀：

| 前缀 | 对象 | 示例 |
|------|------|------|
| `MODULE-` | 模块 | `MODULE-design-001` |
| `PAGE-` | 页面 | `PAGE-design-001` |
| `FIELD-` | 字段 | `FIELD-design-001` |
| `RULE-` | 规则 | `RULE-design-001` |
| `FLOW-` | 流程 | `FLOW-design-001` |
| `REL-` | 关系 | `REL-design-001` |
| `STATE-` | 状态 | `STATE-design-001` |
| `PERM-` | 权限 | `PERM-design-001` |

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

### align 阶段（2 个文件）

- `index.json`：总索引
- `relations.json`：关系列表

### design 阶段（10 个文件）

- `index.json`：总索引
- `relations.json`：关系列表
- `modules.json`：模块定义
- `pages.json`：页面清单
- `fields.json`：字段定义
- `rules.json`：规则定义
- `states.json`：状态定义
- `permissions.json`：权限定义
- `page-fields.json`：页面与字段落点映射
- `non-page-fields.json`：非页面落点字段例外表

### PRD 阶段（2 个文件）

- `index.json`：总索引
- `relations.json`：关系列表

### prototype 阶段（1 个文件）

- `index.json`：总索引

## 五、校验职责划分

| 脚本 | 职责 | 不做的事 |
|------|------|---------|
| verify-against-metadata.py | schema 校验 + ID 唯一性校验 | 语义检测、幻觉检测、一致性比对 |
| prd-consistency-check.py | PRD 幻觉字段检测 + 集合对比 | 不生成 metadata，不校验 |
| review-precheck.py | review 前置结构完整性检查 | 语义检测 |
| prd-style-lint.py | PRD 文风 lint（标签式、流水账、占位符等） | 语义检测 |

幻觉检测和语义一致性判断由 review skill 的 LLM 逐项 checklist 完成，不依赖脚本。
