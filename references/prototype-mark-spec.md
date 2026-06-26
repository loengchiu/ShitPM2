# 原型标注实现规范

> 本文件是 spm-prototype-mark skill 的实现细节规范（视觉样式、浮窗交互、运行时 JS 架构）。
> skill 只定义行为流程，具体的 CSS/JS 实现参数以本文件为准。

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

## 交互规范

| 行为 | 规范 |
|------|------|
| 浮窗打开 | **点击角标**触发（非 hover）。点击后弹出浮窗，再次点击同一角标关闭浮窗。 |
| 浮窗关闭 | ① 点击浮窗右上角 X 按钮；② 再次点击同一角标；③ 点击页面空白处（其他区域）关闭所有浮窗。 |
| 多浮窗 | 同一编号只能开一个；不同编号可同时开多个。 |
| 拖拽 | 浮窗整体支持鼠标拖拽移动（mousedown + mousemove + mouseup）。 |
| 事件隔离 | 点击浮窗内部及拖拽时阻止事件冒泡，不触发页面事件。 |
| 位置 | 弹窗默认出现在角标**右下方**：`top: badgeRect.bottom + 8px; left: badgeRect.left`。<br>**智能避让**：① 若弹窗右侧超出视口 → 改为 `left: viewportW - popupW - 16`；② 若弹窗底部超出视口 → 改为角标**右上方** `top: badgeRect.top - popupH - 8px`；③ 若上方也不够 → `top: 16px`（贴顶部安全距离）。**任何情况下弹窗必须完整可见，不超出视口。** |
| 层级 | 浮窗 `z-index: 99999`（高于页面所有元素，包括 fixed header）。 |

## 运行时 JS 架构

注入的 `<script>` 块需实现：

1. **MarkParser**：极简 Markdown → HTML（~40 行）
2. **PopupManager**：click 打开/切换、X 关闭、点击空白处关闭所有、自由拖拽、**智能边界避让（右超调左、下超调上、上下均超贴顶 16px）**、事件隔离
3. **MarkRenderer**：DOM 就绪后扫描 `[data-pm-mark]`，为每个注入角标 DOM、绑定 **click** → PopupManager。
   - **默认模式**：`target.appendChild(badge)`，CSS `position: absolute` 相对目标定位，自然跟随滚动。
   - **overflow-hidden 模式**：检测到祖先 `overflow: hidden` 时，`document.body.appendChild(badge)`，`position: fixed` + `getBoundingClientRect`，监听 `scroll`/`resize` 更新坐标。
4. **全局点击关闭**：在 `document` 上监听 click，点击对象非角标且非浮窗内部时，调用 PopupManager 关闭所有浮窗。

零外部依赖，所有代码内联在 `<script>` 中。
