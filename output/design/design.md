# 团队周报收集工具 - 设计基线

## 一、角色定义

- **member**：普通成员，可填写、查看、撤回自己的周报
- **admin**：团队负责人，可查看所有成员周报、导出

## 二、模块定义

### 周报管理模块

职责：覆盖周报填写、查看、提交、汇总和归档。
包含页面：我的周报列表、填写周报、团队汇总、历史归档。

## 三、页面清单

| 页面编号 | 页面名称 | 所属模块 | 主要功能 |
|------|------|------|------|
| P01 | 我的周报列表 | 周报管理模块 | 查看自己提交的周报，按所属周和状态筛选，进入填写页 |
| P02 | 填写周报 | 周报管理模块 | 新建、暂存、提交周报 |
| P03 | 团队汇总 | 周报管理模块 | 查看团队成员周报，按所属周和提交人筛选 |
| P04 | 历史归档 | 周报管理模块 | 查看历史归档周报 |

## 四、字段定义

| 字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明 |
|------|------|------|------|--------|--------|------|----------|------|
| report.id | string | 32 | 是 | 系统生成 | — | UUID | 系统生成 | 周报唯一编号 |
| report.submitter | string | 64 | 是 | 当前登录人 | — | 姓名 | 系统生成 | 周报提交人 |
| report.week | string | 16 | 是 | 当前周 | — | YYYY-WW | 系统生成 | 周报所属周 |
| report.this_week | text | 2000 | 是 | — | — | 长文本 | 用户填写 | 本周完成内容 |
| report.next_week | text | 2000 | 是 | — | — | 长文本 | 用户填写 | 下周计划 |
| report.coordination | text | 2000 | 否 | — | — | 长文本 | 用户填写 | 需协调事项 |
| report.tags | string | 100 | 否 | — | — | 多值文本 | 用户填写 | 周报标签 |
| report.status | enum | 16 | 是 | draft | draft、submitted | 枚举 | 系统生成 | 周报状态 |
| report.creator_id | string | 64 | 是 | 当前登录人 ID | — | UUID | 系统生成 | 创建人内部标识 |
| report.created_at | datetime | 19 | 是 | 提交时生成 | — | YYYY-MM-DD HH:mm:ss | 系统生成 | 创建时间 |

## 五、核心业务流程

1. 成员进入填写周报页面，新建或继续编辑当前周周报。
2. 成员提交后，周报状态从 `draft` 变为 `submitted`。
3. 成员在允许条件下可撤回已提交周报，状态回退为 `draft`。
4. 负责人在团队汇总页面查看成员周报并按需要导出。

## 六、页面与字段落点

### 我的周报列表

| 区域/动作 | 字段 |
|------|------|
| 列表展示 | report.id、report.week、report.status |
| 列表辅助信息 | report.submitter |
| 筛选条件 | report.week、report.status |

### 填写周报

| 区域/动作 | 字段 |
|------|------|
| 页面头部信息 | report.week、report.status |
| 表单输入 | report.this_week、report.next_week、report.coordination、report.tags |

### 团队汇总

| 区域/动作 | 字段 |
|------|------|
| 列表展示 | report.id、report.submitter、report.week、report.status |
| 查看内容摘要 | report.this_week、report.next_week、report.coordination、report.tags |
| 筛选条件 | report.submitter、report.week、report.status |

### 历史归档

| 区域/动作 | 字段 |
|------|------|
| 列表展示 | report.id、report.submitter、report.week、report.status |
| 查看内容摘要 | report.this_week、report.next_week、report.coordination、report.tags |

### 非页面落点字段

| 字段 | 原因 |
|------|------|
| report.creator_id | 内部关联字段，仅用于记录创建人标识，不在页面单独展示 |
| report.created_at | 审计时间字段，仅系统留痕，不在当前页面方案中单独展示 |

## 七、规则与状态定义

### 状态集合

- `draft`：草稿
- `submitted`：已提交

### 状态迁移

1. 创建周报后进入 `draft`
2. 提交后进入 `submitted`
3. 撤回后从 `submitted` 回到 `draft`

### 业务规则

1. 每人每周仅可创建一份周报。
2. 仅草稿状态的周报允许继续编辑。
3. 已提交周报仅在允许条件下可撤回。

## 八、权限定义

### 我的周报列表

- `member`：可查看自己的周报列表，可进入填写页
- `admin`：可查看所有成员周报列表

### 填写周报

- `member`：可新建、编辑、提交、撤回自己的周报
- `admin`：默认不代成员编辑

### 团队汇总

- `member`：无权限
- `admin`：可查看团队成员周报，可导出

### 历史归档

- `member`：可查看自己的历史周报
- `admin`：可查看全部历史周报
