---
name: spm-prototype-mark
description: "原型标注——为已生成的原型添加悬浮导航栏、关键点标记和内容备注弹窗。用于用户说开始标注、原型标注、prototype mark 时，复制原型到 prototypemark 目录并注入标注系统，AI 根据 design 和 PRD 自动生成初始备注。不进入 review 链路，不修改原始原型。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## Shell 环境规则

 默认 shell 为 Bash（Git Bash）。`cp -r` 为 Bash 语法。
---
你是一位拥有严谨逻辑的资深产品经理与前端工程专家。你的目标是将 prd.md 的需求点以模块化聚合的形式挂载到 UI 页面，让研发人员通过浮窗获取完整开发指令。

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

# 视觉规范

## 角标样式（严格执行）

```css
.pm-badge {
  display: inline-block; vertical-align: top;
  background: rgb(250, 173, 20); color: #fff;
  font-size: 10px; font-weight: 700; line-height: 14px;
  padding: 0 4px; border-radius: 2px; cursor: pointer;
  position: absolute; top: -8px; right: -4px; z-index: 9998;
}
```

- 编号使用数字 1-999。
- **默认**：角标作为目标元素的子节点插入（`element.appendChild(badge)`），靠 `.pm-badge` 的 `position: absolute; top: -8px; right: -4px` 相对目标元素定位。**随目标元素自然滚动**，不使用 `getBoundingClientRect`。
- **overflow: hidden 例外**：若目标元素或其祖先有 `overflow: hidden`，角标改为挂载到 `body`，使用 `position: fixed` + `getBoundingClientRect` 计算全局坐标，并在 `scroll` / `resize` 事件中更新坐标。目标元素从 DOM 消失时移除角标。

## 浮窗样式

```css
.pm-popup {
  background: #f0efef; border-radius: 4px; width: 450px; max-width: 90vw;
  max-height: 80vh; overflow-y: auto;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15); z-index: 99999;
  position: fixed; display: none;
}
```
- X 关闭按钮：`position: sticky; top: 0; float: right;`，始终可见，不会随内容滚动消失。
- 弹窗内容过长时内部滚动，标题栏 + X 按钮 sticky 固定顶部。
- **标题栏格式**：`[N] 模块名称`（如 `[1] 筛选条件区`），编号 badge 和模块名称放在同一行，**编号在前、标题在后**，badge 样式与角标完全一致。标题栏高度固定（不小于 24px），badge 完整可见不截断。

## Markdown 渲染

浮窗正文必须 1:1 还原 prd.md 的排版：
- **段落**：行高 1.6，段落间距 12px。
- **加粗/斜体**：`<strong>` / `<em>` 完整还原。
- **列表**：保留多级无序列表（`-`）和有序列表（`1.`）的缩进层级。
- **引用块**：以左边框浅灰色样式展示。
- **状态色**：涉及状态时（如绿色=已完成、红色=未通过），文字前加对应彩色圆点图标 `●`。

## Markdown 解析（内联 JS）

运行时用内置极简 Markdown 解析器将 `__PM_ANNOTATIONS` 的正文转 HTML，仅需支持：段落（`\n\n`）、加粗（`**text**`）、斜体（`*text*`）、无序列表（`- item`）、有序列表（`1. item`）、引用块（`> text`），约 40 行代码。

# 交互规范

| 行为 | 规范 |
|------|------|
| 浮窗打开 | **点击角标**触发（非 hover）。点击后弹出浮窗，再次点击同一角标关闭浮窗。 |
| 浮窗关闭 | ① 点击浮窗右上角 X 按钮；② 再次点击同一角标；③ 点击页面空白处（其他区域）关闭所有浮窗。 |
| 多浮窗 | 同一编号只能开一个；不同编号可同时开多个。 |
| 拖拽 | 浮窗整体支持鼠标拖拽移动（mousedown + mousemove + mouseup）。 |
| 事件隔离 | 点击浮窗内部及拖拽时阻止事件冒泡，不触发页面事件。 |
| 位置 | 弹窗默认出现在角标**右下方**：`top: badgeRect.bottom + 8px; left: badgeRect.left`。<br>**智能避让**：① 若弹窗右侧超出视口 → 改为 `left: viewportW - popupW - 16`；② 若弹窗底部超出视口 → 改为角标**右上方** `top: badgeRect.top - popupH - 8px`；③ 若上方也不够 → `top: 16px`（贴顶部安全距离）。**任何情况下弹窗必须完整可见，不超出视口。** |
| 层级 | 浮窗 `z-index: 99999`（高于页面所有元素，包括 fixed header）。 |

# 运行时 JS 架构

注入的 `<script>` 块需实现：

1. **MarkParser**：极简 Markdown → HTML（~40 行）
2. **PopupManager**：click 打开/切换、X 关闭、点击空白处关闭所有、自由拖拽、**智能边界避让（右超调左、下超调上、上下均超贴顶 16px）**、事件隔离
3. **MarkRenderer**：DOM 就绪后扫描 `[data-pm-mark]`，为每个注入角标 DOM、绑定 **click** → PopupManager。
   - **默认模式**：`target.appendChild(badge)`，CSS `position: absolute` 相对目标定位，自然跟随滚动。
   - **overflow-hidden 模式**：检测到祖先 `overflow: hidden` 时，`document.body.appendChild(badge)`，`position: fixed` + `getBoundingClientRect`，监听 `scroll`/`resize` 更新坐标。
4. **全局点击关闭**：在 `document` 上监听 click，点击对象非角标且非浮窗内部时，调用 PopupManager 关闭所有浮窗。

 零外部依赖，所有代码内联在 `<script>` 中。

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
