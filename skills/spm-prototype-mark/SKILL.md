---
name: spm-prototype-mark
description: "原型标注——ShitPM：为已生成的原型添加悬浮导航栏、关键点标记和内容备注弹窗。用于用户说开始标注、原型标注、prototype mark 时，复制原型到 prototypemark 目录并注入标注系统，AI 根据 design 和（可选）PRD 自动生成初始备注。不进入 review 链路，不修改原始原型，不成为产品事实源，高影响意见交由 Fix 回写 Design。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 模型建议（运行时输出）

流程开始时输出模型等级和推理深度建议（整体工作流定位）：

- **轻量模型**：明确标注的定位和展示
- **深度推理模型（Prototype Review）**：主动发现产品或交互问题属于 Prototype Review，不属于 Mark

建议必须是实际运行输出，不只是背景说明。

## ShitPM 职责定位

- **不修改原始 Prototype**：只操作 `output/prototypemark/` 副本
- **不成为产品事实源**：标注内容只是 PRD/Design 内容的展示载体，不是新事实源；**不承诺脱离源文件后仍是权威规格**
- **可以展示必要上下文，但必须标明来源**：浮窗内容需标注"内容来源：design.md"或"内容来源：prd.md"，脱离源文件后不构成权威规格
- **高影响意见交由 Fix 回写 Design**：标注过程中发现的高影响问题（缺失模块、错误状态等）不直接修改 Prototype 或 Design，而是按"高影响反馈结构化输出约定"输出意见清单，提示用户通过 spm-fix 回写 Design
- **PRD 可选**：ShitPM 中 Prototype 可独立于 PRD 生成，标注也可在无 PRD 时基于 design.md 生成
- **不进入 review 链路**：不生成 metadata、不触发 review

# 任务判定

执行前先判定用户意图：
- 指令不明确 → 主动问：**"请问需要【初始化标注】还是【增量更新】？"**
- 指令明确 → 按下方工作流执行。

# Workflow A：初始化标注

触发场景：用户提供原型页面（可选 PRD），要求开始标注。

## 步骤 1：前置检查

| 资源 | 路径 | 必需 | 缺失动作 |
|------|------|------|---------|
| 原型 | `output/prototype/` 目录下有 `.html` 文件 | 是 | 停下，告知需先完成 spm-prototype |
| PRD | `output/prd/prd.md` | 否 | 退化为基于 `output/design/design.md` 生成备注 |
| Design | `output/design/design.md` | 是 | 停下，告知需先完成 spm-design 并确认 |

**ShitPM PRD 缺失时的退化策略**：
- 读取 `output/design/design.md` 中字段定义、状态机、权限规则章节
- 浮窗内容直接引用 design.md 对应章节描述
- 在浮窗顶部标注"内容来源：design.md（PRD 未生成）"

## 步骤 2：复制原型

将 `output/prototype/` 整个目录复制为 `output/prototypemark/`（跨平台兼容的目录复制，结果须保证 `output/prototypemark/` 与 `output/prototype/` 内容一致，包括 `lib/` 子目录）。

`output/prototype/lib/` 已随原型一起输出，复制后 `output/prototypemark/lib/` 自然存在，**不需要做任何路径修正**。

## 步骤 3：模块化需求聚合

读取 `output/prd/prd.md`（ShitPM：PRD 缺失时退化为读取 `output/design/design.md` 中对应模块章节），以模块化聚合整合需求点：

- **组件归一化**：同一组件/模块只标一个角标。将属于同一功能区域的需求整合至一个编号内。
  - 示例：列表行的编辑/删除/查看/权限控制 → 一个角标，挂在操作栏标题。
  - 示例：筛选区所有输入框/下拉框/查询/重置 → 一个角标，挂在筛选区右上角。
  - 示例：Tabs 切换逻辑 → 一个角标，挂在 Tabs 整体右上角。
- **零丢失提取**：浮窗内容必须包含该模块下所有原始描述、业务逻辑、前置条件及异常流程，严禁概括或删减细节。

## 步骤 4：定位关键元素并加标注属性

遍历 `output/prototypemark/` 下**所有** `.html` 文件。单页面文件（如 `index.html` 含多页面内容）正常标注其内部各页面段；纯路由跳转或空壳页面（无实际页面内容）跳过不标注。对每个页面定位需求点对应的关键 DOM 元素。对每个标注点，在目标元素上添加 `data-pm-mark="N"` 属性（N 为 1-999 编号，全项目唯一，同一模块可复用同一编号）。

定位规则：
- v-for 列表/表格 → 标注容器（`<table>`、`<tbody>`、卡片父 div），不标注每一行。
- 按钮/操作区 → 标注按钮组的父容器。
- 表单 → 标注 `<form>` 或最外层 `<div>`。
- 页面级 → 可在页面容器上加 `data-pm-mark-page="N"`。

**编辑原则**：只做 `data-pm-mark` 属性插入，不修改任何现有 class、结构、content。使用通用编辑工具精确替换 `<tag` 为 `<tag data-pm-mark="N"`（不依赖特定 Agent 工具名）。

## 步骤 5：注入标注系统

对 `output/prototypemark/` 下**每个** `.html` 文件的 `</body>` 前注入 `<style>` + `<script>` 块。

### 5.1 角标样式

```css
.pm-badge {
  display: inline-block;
  background: rgb(250, 173, 20); color: #fff;
  font-size: 10px; font-weight: 700; line-height: 14px;
  padding: 0 4px; border-radius: 2px; cursor: pointer;
  position: fixed; z-index: 9998;
  pointer-events: auto;
}
```

### 5.2 定位策略（硬规则）

**一律使用 `position: fixed` + `document.body` 挂载。**

- 角标 DOM 全部 `document.body.appendChild(badge)`，不插入目标元素内部。
- 通过目标元素的 `getBoundingClientRect()` 计算全局坐标：
  - `top = rect.top - 8`
  - `left = rect.right - 14`（角标右边缘对齐目标元素右边缘，留 4px 间距）
- **scroll/resize 事件**：只更新已有角标的坐标（轻量），不全量重建。
- **禁止使用 `position: absolute`**。禁止将角标插入目标元素内部。

### 5.3 浮窗样式

```css
.pm-popup {
  background: #f0efef; border-radius: 4px; width: 450px; max-width: 90vw;
  max-height: 80vh; overflow-y: auto;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15); z-index: 99999;
  position: fixed; display: none;
}
```
- X 关闭按钮：`position: sticky; top: 0; float: right;`，始终可见。
- **标题栏格式**：`[N] 模块名称`（如 `[1] 筛选条件区`），编号在前、标题在后，badge 样式与角标一致。

### 5.4 多容器场景与 DOM 变更处理

当原型包含抽屉（Drawer）、弹窗（Modal/Dialog）等叠加层时，需要处理容器可见性和 DOM 变更。

**容器归属检测**——渲染角标时检测目标元素所在容器：

```js
function getContainerClass(targetEl) {
  if (targetEl.closest('.drawer-panel, .ant-drawer, .el-drawer, [class*="drawer"]')) return 'pm-badge-in-drawer';
  if (targetEl.closest('.modal, .ant-modal, .el-dialog, [class*="modal"], [class*="dialog"]')) return 'pm-badge-in-modal';
  return 'pm-badge-in-page';
}
```

给角标 DOM 添加对应 class：`pm-badge-in-page` / `pm-badge-in-drawer` / `pm-badge-in-modal`。

**容器可见性控制 CSS**：

```css
body.pm-drawer-open .pm-badge.pm-badge-in-page { display: none; }
body.pm-modal-open .pm-badge.pm-badge-in-page { display: none; }
body:not(.pm-drawer-open) .pm-badge.pm-badge-in-drawer { display: none; }
body:not(.pm-modal-open) .pm-badge.pm-badge-in-modal { display: none; }
```

**统一 DOM 变更处理**——用一个 MutationObserver 同时处理容器状态同步和角标重渲染：

```js
let rafId = null;
let domObserver = null;

function isElVisible(el) {
  return el && el.offsetParent !== null && getComputedStyle(el).display !== 'none';
}

function setupObserver() {
  domObserver = new MutationObserver(() => {
    // 先更新容器状态——检测可见性，不只是 DOM 存在
    const drawerEl = document.querySelector('.drawer-panel, .ant-drawer, .el-drawer, [class*="drawer"]');
    const modalEl = document.querySelector('.modal, .ant-modal, .el-dialog, [class*="modal"], [class*="dialog"]');
    document.body.classList.toggle('pm-drawer-open', isElVisible(drawerEl));
    document.body.classList.toggle('pm-modal-open', isElVisible(modalEl));
    
    // 再延迟重渲染角标（等待框架完成 DOM 更新）
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(() => {
      window.__pmRenderMarks();
      rafId = null;
    });
  });
  domObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style'] });
}
setupObserver();
```

**时序保证**：先 toggle body class，再在 requestAnimationFrame 里调 `__pmRenderMarks()`，确保渲染角标时容器状态已更新。

### 5.5 数据格式（硬规则）

```js
var __PM_ANNOTATIONS = {
  1: { title: '筛选条件区', content: '所有筛选条件...' },
  2: { title: '操作栏', content: '编辑/删除/查看...' }
};
```

- **content 字段必须使用单引号 `'` 包裹**。
- 内部中文引号 `"` `"` 保留原样（单引号字符串中不会终止）。
- 内部英文单引号用 `\'` 转义。
- **禁止使用双引号 `"` 包裹 content**，避免中文引号混用导致 SyntaxError。

### 5.6 框架集成

暴露全局函数供框架调用：

```js
window.__pmRenderMarks = function() {
  // 暂停 observer 避免无限循环
  if (domObserver) domObserver.disconnect();
  
  document.querySelectorAll('.pm-badge').forEach(b => b.remove());
  renderAllMarks();
  
  // 重新启用 observer
  if (domObserver) domObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style'] });
};
```

Vue/React 可直接调用此接口触发角标重渲染。DOM 变更的自动监听已在 5.4 统一处理。

### 5.7 交互规范

| 行为 | 规范 |
|------|------|
| 浮窗打开 | **点击角标**触发（非 hover）。再次点击同一角标关闭。 |
| 浮窗关闭 | ① X 按钮；② 再次点击同一角标；③ 点击页面空白处关闭所有。 |
| 多浮窗 | 同一编号只能开一个；不同编号可同时开多个。 |
| 拖拽 | 浮窗整体支持鼠标拖拽（mousedown + mousemove + mouseup）。 |
| 事件隔离 | 点击浮窗内部及拖拽时阻止事件冒泡。 |
| 位置 | 默认角标右下方：`top: badgeRect.bottom + 8; left: badgeRect.left`。智能避让：右超 → 左移；下超 → 上方；都不够 → 贴顶 16px。 |
| 层级 | 浮窗 `z-index: 99999`。 |

### 5.8 Markdown 渲染

浮窗正文 1:1 还原 prd.md 排版：段落（行高 1.6，间距 12px）、加粗、斜体、多级列表、引用块（左边框浅灰）、状态色（`●` 圆点）。

运行时用内联极简 Markdown 解析器（~40 行）将 content 转 HTML。

### 5.9 运行时 JS 架构

注入的 `<script>` 块实现：

1. **MarkParser**：极简 Markdown → HTML
2. **PopupManager**：click 打开/切换、X 关闭、空白处关闭、拖拽、智能边界避让、事件隔离
3. **MarkRenderer**：扫描 `[data-pm-mark]` → `document.body.appendChild(badge)` → `position: fixed` + `getBoundingClientRect` → 容器归属检测 → 绑定 click
4. **全局点击关闭**：`document` 上监听 click，非角标非浮窗内部时关闭所有
5. **容器状态同步**：按 5.4 节实现
6. **全局接口**：`window.__pmRenderMarks()`

零外部依赖，全部内联。

## 步骤 6：自检

完成后对照执行与自检清单逐项确认。

# Workflow B：增量更新

触发场景：design.md / prd.md / 原型有调整，需要更新已有标注。

1. **差异识别**：对比当前标注与调整后的 design.md / prd.md / 原型，识别新增/修改/删除项。
2. **样式锁定**：严禁修改任何视觉样式参数（角标颜色、尺寸、浮窗背景、偏移量等）。
3. **精准替换**：
   - 新增项 → 按既定规范生成新角标，编号连续递增。
   - 修改项 → 仅替换 `__PM_ANNOTATIONS` 中对应编号的 Markdown 内容，不改角标位置（除非组件位置变化）。
   - 删除项 → 移除对应 `data-pm-mark` 属性、角标 DOM 和 `__PM_ANNOTATIONS` 条目。
4. **高影响意见处理（ShitPM 新增）**：标注过程中发现的高影响问题（缺失模块、错误状态、权限漏洞等）→ 不直接修改 Prototype 或 Design，而是按"高影响反馈结构化输出约定"在标注报告末尾列出"高影响意见清单"，建议用户通过 spm-fix 回写 Design。

## 高影响反馈结构化输出约定（ShitPM 新增）

标注过程中发现的高影响问题必须有明确、可被 spm-fix 使用的结构化输出。每条意见包含以下字段：

```
高影响意见清单：

1. 归属层：[对齐层 / 设计层 / 原型层]
   改什么：[具体对象，如"审计模块状态机缺少'驳回'状态"]
   改成什么：[建议状态，如"在状态机表中新增'驳回'状态及对应迁移"]
   影响范围：[受影响的产物文件清单]
   来源：[发现位置，如"prototypemark/index.html 第 N 页 '审批' 按钮"]
   建议处理：[通过 spm-fix 回写 Design / 仅改 Prototype 等]
```

此清单可被 spm-fix 直接读取并解析为修复指令的输入。

# 硬规则

- **不反写 prd.md / design.md**。编号 [1] [2] 只存在于 prototypemark 副本，不写入 `output/prd/prd.md` 或 `output/design/design.md`。
- **不修改 `output/prototype/`**。只操作 `output/prototypemark/`。
- **不修改 lib/ 路径**。prototype 已自包含 `lib/`，复制后路径自然正确。
- **不引入 Python 脚本**。AI 直接用通用编辑工具编辑 HTML（不依赖特定 Agent 工具名）。
- **不引入外部 CDN**。所有代码内联。
- **不进入 review 链路**。prototype-mark 是辅助工具，不生成 metadata、不触发 review。
- **不生成页面级角标时不标**。非必要不加页面级标记。
- **角标一律 `position: fixed` + `document.body` 挂载**。禁止 `position: absolute`，禁止插入目标元素内部。
- **`__PM_ANNOTATIONS` 的 content 字段必须用单引号包裹**。禁止双引号。
- **不成为产品事实源（ShitPM）**。标注内容只是 PRD/Design 内容的展示载体，不构成新事实源；不承诺脱离源文件后仍是权威规格。
- **展示必要上下文必须标明来源**：浮窗内容需标注"内容来源：design.md"或"内容来源：prd.md"。
- **高影响意见交由 Fix 回写 Design（ShitPM）**。不直接修改 Prototype 或 Design，按"高影响反馈结构化输出约定"输出意见清单。
- **不使用 `cp -r` 等 Unix 专属命令**：目录复制操作描述目标结果，由实际工具跨平台执行。
- **不硬编码特定 Agent 工具协议**：用通用编辑工具描述代替。

# 执行与自检

完成判据：标注系统已注入；关键点标记与备注已按 design 生成；复制到 prototypemark 目录完成；下方自检清单逐项通过。

完成后逐项自检：

- [ ] 执行的是初始化还是增量更新？
- [ ] 同一组件/模块是否只有一个角标？
- [ ] 浮窗内容是否标注了来源（design.md / prd.md），且未声明脱离源文件后仍是权威规格？
- [ ] 浮窗是否支持拖拽？是否只能通过 X 关闭？点击浮窗是否隔离了页面事件？
- [ ] 角标是否 10px 粗体 amber？层级是否正确？
- [ ] 浮窗是否还原了 Markdown 层级与重点？
- [ ] 是否未修改 output/prototype/ 和 output/prd/prd.md 和 output/design/design.md？
- [ ] **角标定位**：是否所有角标统一使用 `position: fixed` + `document.body` 挂载？
- [ ] **多容器场景**：是否检测了角标容器归属（`pm-badge-in-page` / `pm-badge-in-drawer` / `pm-badge-in-modal`）？抽屉/弹窗打开时主页角标是否隐藏？
- [ ] **数据格式**：`__PM_ANNOTATIONS` 的 content 字段是否使用单引号包裹？
- [ ] **框架集成**：是否暴露了 `window.__pmRenderMarks()` 全局接口？
- [ ] **来源标注**：浮窗内容是否标注了"内容来源：design.md"或"内容来源：prd.md"？
- [ ] **高影响意见清单**：是否在报告末尾按结构化输出约定列出待用户决策的高影响意见（ShitPM）？每条意见是否包含归属层、改什么、改成什么、影响范围、来源、建议处理六字段？
