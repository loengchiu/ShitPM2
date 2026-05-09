---
name: spm-prd
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
6. 少用标签式正文

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
- `next_recommended`：`"prototype"` 或 `"prd-review"`

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
5. 不执行 review（建议 `/spm-prd-review`）
6. 不自动推进到下一阶段
