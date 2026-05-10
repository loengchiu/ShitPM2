# 团队周报收集工具 - 设计基线

## 一、角色定义
- **member**: 普通成员，可填写/查看/撤回自己的周报
- **admin**: 团队负责人，可查看所有成员周报、导出

## 二、模块定义
### 1．report
周报管理模块

## 三、页面清单
### page-1 我的周报列表
### page-2 填写周报
### page-3 团队汇总
### page-4 历史归档

## 四、字段定义
### report.id
周报编号，string，主键

### report.submitter
提交人，string，必填

### report.week
所属周，string，必填

### report.this_week
本周完成，text，必填

### report.next_week
下周计划，text，必填

### report.coordination
需协调事项，text，选填

### report.tags
标签，string，选填

### report.status
状态，enum，必填

## 五、规则与状态定义
### 状态机：report.status
- draft → submitted
- submitted → withdrawn

## 六、权限定义
### member 权限
- 可创建自己的周报
- 可编辑草稿状态的周报
- 可撤回已提交的周报
- 可查看自己的周报列表
- 可查看团队汇总

### admin 权限
- 可查看所有成员的周报
- 可导出周报