---
name: spm-prototype-mark
description: "原型标注——为已生成的原型添加悬浮导航栏、关键点标记和内容备注弹窗。用于用户说开始标注、原型标注、prototype mark 时，复制原型到 prototypemark 目录并注入标注系统，AI 根据 design 和 PRD 自动生成初始备注。不进入 review 链路，不修改原始原型。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下


# 任务判定

执行前先判定用户意图：
- 指令不明确 → 主动问：**"请问需要【初始化标注】还是【增量更新】？"**
- 指令明确 → 按下方工作流执行。

# Workflow A：初始化标注

触发场景：用户提供 prd.md 和原型页面，要求开始标注。

## 步骤 1：前置检查

| 资源 | 路径 | 缺失动作 |
|------|------|---------|
| PRD | `output/prd/prd.md` |  停下，告知需先完成 spm-prd |
| 原型 | `output/prototype/` 目录下有 `.html` 文件 |  停下，告知需先完成 spm-prototype |

## 步骤 2：复制原型

```bash
cp -r output/prototype/ output/prototypemark/
```

 `output/prototype/lib/` 已随原型一起输出，复制后 `output/prototypemark/lib/` 自然存在，**不需要做任何路径修正**。

## 步骤 3：模块化需求聚合

读取 `output/prd/prd.md`，以模块化聚合整合需求点：

- **组件归一化**：同一组件/模块只标一个角标。将属于同一功能区域的需求整合至一个编号内。
  - 示例：列表行的编辑/删除/查看/权限控制 → 一个角标，挂在操作栏标题。
  - 示例：筛选区所有输入框/下拉框/查询/重置 → 一个角标，挂在筛选区右上角。
  - 示例：Tabs 切换逻辑 → 一个角标，挂在 Tabs 整体右上角。
- **零丢失提取**：浮窗内容必须包含该模块下所有原始描述、业务逻辑、前置条件及异常流程，严禁概括或删减细节。

## 步骤 4：定位关键元素并加标注属性

遍历 `output/prototypemark/` 下**所有** `.html` 文件（除了 index.html），对每个页面定位需求点对应的关键 DOM 元素。对每个标注点，在目标元素上添加 `data-pm-mark="N"` 属性（N 为 1-999 编号，全项目唯一，同一模块可复用同一编号）。

定位规则：
- v-for 列表/表格 → 标注容器（`<table>`、`<tbody>`、卡片父 div），不标注每一行。
- 按钮/操作区 → 标注按钮组的父容器。
- 表单 → 标注 `<form>` 或最外层 `<div>`。
- 页面级 → 可在页面容器上加 `data-pm-mark-page="N"`。

**编辑原则**：只做 `data-pm-mark` 属性插入，不修改任何现有 class、结构、content。使用 Edit 工具精确替换 `<tag` 为 `<tag data-pm-mark="N"`。

## 步骤 5：注入标注系统

对 `output/prototypemark/` 下**每个** `.html` 文件的 `</body>` 前注入 `<style>` + `<script>` 块，包含：

1. **CSS**：角标样式 + 浮窗样式（见视觉规范）
2. **标注数据**：`<script>var __PM_ANNOTATIONS = {...};</script>`
3. **标注运行时 JS**：角标渲染、浮窗管理、拖拽、Markdown 解析

注入方式：用 Edit 工具在 `</body>` 前插入。

## 步骤 6：自检

完成后对照执行与自检清单逐项确认。

# Workflow B：增量更新

触发场景：prd.md 或原型有调整，需要更新已有标注。

1. **差异识别**：对比当前标注与调整后的 prd.md / 原型，识别新增/修改/删除项。
2. **样式锁定**：严禁修改任何视觉样式参数（角标颜色、尺寸、浮窗背景、偏移量等）。
3. **精准替换**：
   - 新增项 → 按既定规范生成新角标，编号连续递增。
   - 修改项 → 仅替换 `__PM_ANNOTATIONS` 中对应编号的 Markdown 内容，不改角标位置（除非组件位置变化）。
   - 删除项 → 移除对应 `data-pm-mark` 属性、角标 DOM 和 `__PM_ANNOTATIONS` 条目。

# 实现规范

视觉样式、浮窗交互、运行时 JS 架构的详细规范见 `references/prototype-mark-spec.md`。步骤 5 注入标注系统时严格遵循该规范。

# 硬规则

- **不反写 prd.md**。编号 [1] [2] 只存在于 prototypemark 副本，不写入 `output/prd/prd.md`。
- **不修改 `output/prototype/`**。只操作 `output/prototypemark/`。
- **不修改 lib/ 路径**。prototype 已自包含 `lib/`，复制后路径自然正确。
- **不引入 Python 脚本**。AI 直接用 Edit 工具编辑 HTML。
- **不引入外部 CDN**。所有代码内联。
- **不进入 review 链路**。prototype-mark 是辅助工具，不生成 metadata、不触发 review。
- **不生成页面级角标时不标**。非必要不加页面级标记。

# 执行与自检

完成后逐项自检：

- [ ] 执行的是初始化还是增量更新？
- [ ] 同一组件/模块是否只有一个角标？
- [ ] 浮窗信息是否足够替代 PRD？
- [ ] 浮窗是否支持拖拽？是否只能通过 X 关闭？点击浮窗是否隔离了页面事件？
- [ ] 角标是否 10px 粗体 amber？层级是否正确？
- [ ] 浮窗是否还原了 Markdown 层级与重点？
- [ ] 是否未修改 output/prototype/ 和 output/prd/prd.md？
