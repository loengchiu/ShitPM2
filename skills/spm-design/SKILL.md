---
name: spm-design
description: "设计阶段——把对齐结果结构化成稳定基线。用于用户说开始设计、做设计、进入设计时，按固定顺序生成角色、模块、页面、字段、规则、权限等完整设计基线。设计是唯一事实源。"
triggers:
  - "开始设计"
  - "做设计"
  - "进入设计"
---
## 脚本路径

> 🔴 **所有 Python 脚本位于 SKILL bundle 的 `scripts/python/` 目录下，不在项目目录下。**
> SKILL bundle 根目录：`D:\work\ShitPM`
> 脚本完整路径示例：`D:\work\ShitPM\scripts\python\review-precheck.py`
>
> 执行时使用 SKILL bundle 绝对路径拼接脚本名，禁止在项目目录下搜索脚本。


# 设计

## 触发条件

用户要求开始设计，或 stage-context 建议进入 design 阶段。

## 前置检查

运行 `scripts/python/stage-context.py` 检查准入：

1. align.md 存在
2. metadata/align 完整
3. align-notes.json 中 `can_enter_design` = true

如检查不通过，🔴 停止并输出阻塞项，不写任何产物。

🔴 **失败分支：stage-context.py 执行失败**——脚本报错时停下告知用户，不跳过前置检查。

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
   - 页面与字段落点
   - 业务流程设计（按需，无流程需求时不写）
   - 状态设计
   - 规则设计
   - 权限定义（细到字段级）
4. 生成 design.md 人读产物
5. 更新 status.json

> **metadata 生成时机**：design.md 的机读产物（metadata/design/）不在本阶段生成，
> 而是在 /spm-design-review 通过后由 stage-prep.py 脚本一次性提取。
> 设计阶段只关注人读物质量，PM 修订时也只改 design.md，不再双写。

## 硬规则

### 用户角色与数据范围层级

当设计涉及多级组织架构（如：集团→区域→服务区）时，必须明确：

1. 角色定义中列出角色的数据可见范围层级
2. 页面清单中标注每个页面在不同数据范围下的展示差异
3. 字段定义中标注哪些字段随数据范围变化（如：服务区名称在"全部服务区"时必须展示）
4. 页面与字段落点中按数据范围层级标注差异

🔴 **检查点**——如设计涉及多级组织架构但未定义数据范围层级，停下补充，不进入 PRD。

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

### 页面与字段落点

1. `design` 内必须显式存在“页面与字段落点”章节，作为字段定义与页面使用之间的唯一对照层
2. 页面清单、字段定义、页面与字段落点三处必须能互相对齐，不能只写字段表、不写页面落点
3. 页面与字段落点按“页面 > 区域/动作 > 字段”组织，不展开成 PRD 级页面正文
4. 页面与字段落点里的字段名必须直接引用字段定义中的标准字段名，不得在这里改写别名
5. 每个页面清单中的页面都必须在页面与字段落点章节出现；如该页无业务字段，明确写“无业务字段”
6. 每个字段必须满足二选一：要么出现在页面与字段落点，要么出现在“非页面落点字段”例外表并写明原因
7. 用户可见字段、可编辑字段、可筛选字段、页面动作直接依赖字段，必须进入页面与字段落点，不得放进例外表规避
8. 纯内部字段可进入“非页面落点字段”例外表，例如用户 ID、数据 ID、创建时间、更新时间、内部关联 ID、审计字段
9. 字段既不在页面与字段落点，也不在例外表时，直接判为缺口，不得静默保留

### 结构化写法

1. 页面清单必须使用结构化表格，不用散文或纯标题平铺
2. 字段定义必须使用结构化表格，不用 `### 字段名` 逐条散写
3. 页面与字段落点必须按页面分小节，每个小节内使用结构化表格，至少包含“区域/动作”“字段”两列
4. “非页面落点字段”使用结构化表格，至少包含“字段”“原因”两列
5. 生成 design 时优先保证这三处结构可机读，再追求人读润色

## 不要做什么

1. 不写研发级页面正文
2. 不写高保真视觉表达
3. 不新增 align 没确认的范围
4. 不把 prototype 的表现层问题直接提升为业务事实
5. 不重新判断建设类型
6. 不重新解释原始材料
7. 不静默合并新材料

### 稳定 ID 规则

1. 稳定 ID 首次在 design 阶段生成
2. 只存在于外置机读物，由 review 通过后 `scripts/python/stage-prep.py` 脚本注入，由 review 通过后 `scripts/python/stage-prep.py` 脚本注入
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
- 页面与字段落点
- 规则与状态定义
- 权限定义

辅助章节可选：
- 文档概述
- 范围与建设方式
- 核心业务流程

### 状态更新

更新 `.workflow/status.json`：

- `current_stage`：更新为 `"design"`
- `artifacts.design`：指向 `output/design/design.md`
- `metadata_paths.design`：指向 `.workflow/metadata/design/`
- `next_recommended`：`"prd"` 或 `"prototype"`

## 停止条件

1. design.md 核心章节全部存在
2. 无新增 align 未确认的范围
3. 页面清单、字段定义、页面与字段落点三处能互相对齐

满足以上 3 条后停止，建议 `/spm-design-review`。

## 明确不做什么

1. 不写研发级页面正文（那是 PRD 的职责）
2. 不写高保真视觉表达
3. 不执行 review（建议 `/spm-design-review`）
4. 不自动推进到下一阶段
