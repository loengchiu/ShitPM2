# Metadata Anchor 规则

> 本文件是 anchor-build.py 和 anchor-verify.py 的规则来源。
> 引用规约 §3.6 和 §5.2。

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

### design 阶段（9 个文件）

- `index.json`：总索引
- `entities.json`：实体列表
- `relations.json`：关系列表
- `modules.json`：模块定义
- `pages.json`：页面清单
- `fields.json`：字段定义
- `rules.json`：规则定义
- `states.json`：状态定义
- `permissions.json`：权限定义

### PRD 阶段（6 个文件）

- `index.json`：总索引
- `entities.json`：实体列表
- `relations.json`：关系列表
- `page-anchor.json`：页面锚点
- `rule-anchor.json`：规则锚点
- `field-anchor.json`：字段锚点
