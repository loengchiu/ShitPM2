---
name: spm-prototype
description: 原型阶段——把 design 或 PRD 的页面行为表达成可看、可讨论的原型
triggers:
  - "开始原型"
  - "做原型"
  - "生成原型"
---

# 原型

## 触发条件

用户要求生成原型。

## 输入依赖

1. 必须读取：`output/design/design.md`
2. 如已存在，还需读取：`output/prd/prd.md` 中的详细需求说明、状态机、权限汇总、数据字典
3. 如存在反馈，读取：`output/prototype/prototype-feedback.md`

## 最小读取集合

1. `.workflow/status.json`
2. `output/design/design.md`
3. `.workflow/metadata/design/`（页面清单、字段定义）
4. `templates/prototype.html`（HTML 骨架）
5. `references/prototype-writing.md`（写法参考）

## 输出要求

1. `output/prototype/index.html` 或按页面拆分的原型文件
2. `.workflow/metadata/prototype/index.json`
3. `.workflow/metadata/prototype/page-map.json`
4. 可选 `output/prototype/prototype-feedback.md`

## 硬规则

### prototype-feedback 归类规则

AI 读取 `prototype-feedback.md` 后，必须先输出固定格式归类结果，再开始修改：

```
原型反馈归类结果：

一、表现问题
- [页面/区域] 问题描述

二、语义问题
- [页面/区域] 问题描述

三、处理建议
- 仅改 prototype：
  - ...
- 先回写 design 再同步：
  - ...
```

归类规则：

- 表现问题：只修改 prototype + metadata/prototype，不回写 design
- 语义问题：先回写 design + metadata/design，再视影响范围重生 PRD 或 prototype
- 若某一类为空，保留标题并写"无"
- 未输出归类结果前，不得开始修改任何文件

## 明确不做什么

1. 不重新定义业务规则
2. 不替代 PRD
3. 不引入很重的构建链
4. 不把语义问题只留在 prototype 闭环
5. 不跳过归类直接修改
