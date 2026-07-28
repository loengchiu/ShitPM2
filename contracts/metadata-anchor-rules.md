# Metadata 规则（legacy compatibility）

> **ShitPM 状态：legacy compatibility**
> 本文件描述的 metadata 机制在 ShitPM 主流程中不再作为事实索引或硬门禁。
> 新项目无需生成 metadata，仍可正常生成、Review、Fix、Start。
> 旧项目保留的 metadata 文件可被读取、诊断和逐步迁移，但不构成当前产物质量证明。
>
> 本文件保留作为 `stage-prep.py`（legacy）和 `verify-against-metadata.py`（legacy）的规则来源，仅供旧项目兼容诊断使用。

## 失败模式速查表（legacy）

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

## 反例黑名单（legacy）

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|---|---|---|
| 1 | **手动编写 metadata JSON** | 容易与人读稿不一致 | 由 stage-prep.py 自动生成 |
| 2 | **在正文中使用稳定 ID** | 违反人读机读分离原则 | ID 只存在于 .workflow/metadata/ |
| 3 | **引入 REQ-/RISK-/CASE-/WVR- 前缀** | 第一版只允许 8 种前缀 | 如需新类型，先更新本文件再实现 |
| 4 | **把下游实体塞回上游关系** | 违反关系独立建模原则 | 关系用 REL- 前缀独立 ID |
| 5 | **跳过 read_existing_entities()** | 新运行会重排已有 ID | 每次生成前先读取已有 ID 映射 |
| 6 | **metadata 文件留空不报错** | 空文件可能是提取失败，不是真没内容 | 检查 METADATA_EMPTY_OK 白名单 |
| 7 | **把 metadata 当成新项目硬门禁** | ShitPM 新项目不要求 metadata | 新项目可直接生成 Design/PRD/Prototype，无需 metadata |
| 8 | **把 metadata 当成产物质量证明** | ShitPM 旧 metadata 仅用于兼容诊断 | 以确认版 Design 为唯一事实基线 |


## 一、稳定 ID 前缀规范（legacy）

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

## 二、ID 生成规则（legacy）

1. 稳定 ID 首次在 design 阶段生成
2. 稳定 ID 只存在于外置机读物（`.workflow/metadata/`）
3. PRD、prototype 正文不得出现稳定 ID
4. ID 格式：`{PREFIX}-{stage}-{NNN}`，NNN 为 3 位数字
5. 同一前缀的编号只增不减，多次运行从 max+1 继续
6. 同步修复时由脚本维护稳定 ID，不靠人工手改

## 三、关系建模规范（legacy）

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

## 四、metadata 文件清单（legacy）

> 以下文件清单仅在旧项目或显式运行 legacy 脚本时存在。ShitPM 新项目不会生成这些文件。

### align 阶段（2 个文件，legacy）

- `index.json`：总索引
- `relations.json`：关系列表

### design 阶段（10 个文件，legacy）

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

### PRD 阶段（已移除）

ShitPM 不再为 PRD 阶段生成 metadata。

### prototype 阶段（已移除）

ShitPM 不再为 prototype 阶段生成 metadata。

## 五、校验职责划分（ShitPM 调整后）

| 脚本 | ShitPM 职责 | legacy 行为 |
|------|------|---------|
| verify-against-metadata.py | legacy compatibility：仅在旧项目存在 metadata 时按需执行 | schema 校验 + ID 唯一性校验 |
| prd-consistency-check.py | ShitPM：直接读取人读 Design 和人读 PRD，检查明确可解析的标题、角色、对象、状态、关键动作和明显冲突 | 不依赖 Design metadata |
| review-precheck.py | ShitPM：文件存在性、可读性和基础结构检查 | 不决定是否允许 Review |
| prd-style-lint.py | ShitPM：PRD 模板、文风和格式 | 不变 |
| state-machine-check.py | ShitPM：按需检查，不作为所有生成任务的硬门禁 | 无 metadata 时降级 |
| stage-prep.py | legacy compatibility：新主流程不默认调用 | 仅旧项目兼容诊断 |
| design-confirmation.py | ShitPM：Design 确认标记读写 | 无 legacy 对应 |

幻觉检测和语义一致性判断责任划分：
- **首次生成阶段**：PRD、Prototype 生成 Skill 必须在正式写入前完成与确认版 Design 的语义对照，覆盖核心对象、角色、状态、关键动作、流程、权限、模块和跨系统边界。这是生成责任，不是 Review 责任。
- **Review 阶段**：Review 作为第二意见独立挑战一致性，不承担首次生成的计划内补全。
- **确定性辅助**：`prd-consistency-check.py` 负责明确可解析的标题、角色、对象、状态、关键动作和明显冲突的机械检查，不替代模型语义判断。
