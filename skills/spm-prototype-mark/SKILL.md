---
name: spm-prototype-mark
description: "原型标注——ShitPM：为已生成的源码工程原型添加悬浮导航栏、关键点标记和内容备注弹窗。用于用户说开始标注、原型标注、prototype mark 时，复制原型到 prototypemark 目录并注入标注系统，AI 根据 design 和（可选）PRD 自动生成初始备注。不进入 review 链路，不修改原始原型，不成为产品事实源，高影响意见交由 Fix 回写 Design。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/` 开头 → `$BUNDLE/` 下
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

触发场景：用户提供原型（可选 PRD），要求开始标注。

## 步骤 1：前置检查

| 资源 | 路径 | 必需 | 缺失动作 |
|------|------|------|---------|
| 源码工程原型 | `output/prototype/` 含 `package.json`、`src/` | 是 | 停下，先运行 `prototype-source-check.py`；只有 dist/compiled.js 时报告源码工程缺失，需先迁移或重建 |
| PRD | `output/prd/prd.md` | 否 | 退化为基于 `output/design/design.md` 生成备注 |
| Design | `output/design/design.md` | 是 | 停下，告知需先完成 spm-design 并确认 |

先运行：

```text
python $BUNDLE/scripts/python/prototype-source-check.py --project-root .
```

源码工程检查失败时停止，不复制、不标注、不修改任何产物。

**ShitPM PRD 缺失时的退化策略**：
- 读取 `output/design/design.md` 中字段定义、状态机、权限规则章节
- 浮窗内容直接引用 design.md 对应章节描述
- 在浮窗顶部标注"内容来源：design.md（PRD 未生成）"

## 步骤 2：复制源码工程

将 `output/prototype/` 源码工程复制为 `output/prototypemark/`，**排除 `node_modules/` 和旧 `dist/`**；`package.json`、`package-lock.json`、`vite.config.js`、`src/`、`index.html`、`public/`、README、`原型工具.bat` 一并复制。复制后运行：

```text
cd output/prototypemark
npm ci
npm run build
```

先验证副本可构建，再开始注入标注。

## 步骤 3：模块化需求聚合

读取 `output/prd/prd.md`（ShitPM：PRD 缺失时退化为读取 `output/design/design.md` 中对应模块章节），以模块化聚合整合需求点：

- **组件归一化**：同一组件/模块只标一个角标。将属于同一功能区域的需求整合至一个编号内。
  - 示例：列表行的编辑/删除/查看/权限控制 → 一个角标，挂在操作栏标题。
  - 示例：筛选区所有输入框/下拉框/查询/重置 → 一个角标，挂在筛选区右上角。
  - 示例：Tabs 切换逻辑 → 一个角标，挂在 Tabs 整体右上角。
- **零丢失提取**：浮窗内容必须包含该模块下所有原始描述、业务逻辑、前置条件及异常流程，严禁概括或删减细节。

## 步骤 4：定位关键元素并加标注属性

遍历 `output/prototypemark/src/` 下所有业务页面 JSX（排除 `shared/pm/` 自身和 `dist/`）。对每个页面定位需求点对应的关键元素。对每个标注点，在目标元素上添加 `data-pm-mark="N"` 属性（N 为 1-999 编号，全项目唯一，同一模块可复用同一编号）。

定位规则：
- 列表/表格 → 标注容器（`<Table>`、Card 父 div），不标注每一行。
- 按钮/操作区 → 标注按钮组的父容器。
- 表单 → 标注 `<Form>` 或最外层 `<div>`。
- 页面级 → 可在页面容器上加 `data-pm-mark-page="N"`。

**编辑原则**：只做 `data-pm-mark` 属性插入，不修改任何现有 class、结构、content。

## 步骤 5：注入标注系统

按 `$BUNDLE/references/prototype-mark-injection.md` 在副本中注入：

1. 创建 `src/shared/pm/annotations.js`：标注数据（编号 → 标题 + 内容），content 用单引号包裹。
2. 创建 `src/shared/pm/MarkLayer.jsx`：角标 + 浮窗组件（`position: fixed` + `document.body` 挂载、点击开合、容器可见性控制）。
3. 创建 `src/styles/pm.css` 并引入。
4. 在 `src/App.jsx` 挂载 `<MarkLayer />`。
5. 重新构建：`npm run build`，输出 `output/prototypemark/dist/`。

交互规范（硬规则）：

| 行为 | 规范 |
|------|------|
| 浮窗打开 | **点击角标**触发（非 hover）。再次点击同一角标关闭。 |
| 浮窗关闭 | ① X 按钮；② 再次点击同一角标；③ 点击页面空白处关闭所有。 |
| 多浮窗 | 同一编号只能开一个；不同编号可同时开多个。 |
| 位置 | 默认角标右下方：`top: badgeRect.bottom + 8; left: badgeRect.left`。智能避让：右超 → 左移；下超 → 上方；都不够 → 贴顶 16px。 |
| 层级 | 浮窗 `z-index: 99999`，角标 `z-index: 9998`。 |
| 容器 | 抽屉/弹窗打开时隐藏主页角标（body class 控制）。 |

## 步骤 6：自检

完成后对照执行与自检清单逐项确认（见文末）。

# Workflow B：增量更新

触发场景：design.md / prd.md / 原型有调整，需要更新已有标注。

1. **差异识别**：对比当前标注与调整后的 design.md / prd.md / 原型，识别新增/修改/删除项。
2. **样式锁定**：严禁修改任何视觉样式参数（角标颜色、尺寸、浮窗背景、偏移量等）。
3. **精准替换**：
   - 新增项 → 按既定规范生成新角标，编号连续递增。
   - 修改项 → 仅替换 `annotations.js` 中对应编号的 content，不改角标位置（除非组件位置变化）。
   - 删除项 → 移除对应 `data-pm-mark` 属性、角标 DOM 和 `annotations.js` 条目。
4. **重新构建**：修改副本源码后运行 `npm run build` 更新 `output/prototypemark/dist/`。
5. **高影响意见处理（ShitPM 新增）**：标注过程中发现的高影响问题（缺失模块、错误状态、权限漏洞等）→ 不直接修改 Prototype 或 Design，而是按"高影响反馈结构化输出约定"在标注报告末尾列出"高影响意见清单"，建议用户通过 spm-fix 回写 Design。

## 高影响反馈结构化输出约定（ShitPM 新增）

标注过程中发现的高影响问题必须有明确、可被 spm-fix 使用的结构化输出。每条意见包含以下字段：

```
高影响意见清单：

1. 归属层：[对齐层 / 设计层 / 原型层]
   改什么：[具体对象，如"审计模块状态机缺少'驳回'状态"]
   改成什么：[建议状态，如"在状态机表中新增'驳回'状态及对应迁移"]
   影响范围：[受影响的产物文件清单]
   来源：[发现位置，如"prototypemark/src/modules/plan/PlanList.jsx '审批' 按钮"]
   建议处理：[通过 spm-fix 回写 Design / 仅改 Prototype 等]
```

此清单可被 spm-fix 直接读取并解析为修复指令的输入。

# 硬规则

- **不反写 prd.md / design.md**。编号 [1] [2] 只存在于 prototypemark 副本，不写入 `output/prd/prd.md` 或 `output/design/design.md`。
- **不修改 `output/prototype/`**。只操作 `output/prototypemark/`。
- **不直接修改 dist**。副本的 `dist/` 只由 `npm run build` 生成。
- **不引入外部 CDN**。标注组件全部本地实现。
- **不引入 Python 脚本**。AI 直接用通用编辑工具编辑 JSX（不依赖特定 Agent 工具名）。
- **不进入 review 链路**。prototype-mark 是辅助工具，不生成 metadata、不触发 review。
- **不生成页面级角标时不标**。非必要不加页面级标记。
- **角标一律 `position: fixed` + `document.body` 挂载**。禁止 `position: absolute`，禁止插入目标元素内部。
- **annotations.js 的 content 字段必须用单引号包裹**。内部中文引号保留原样，英文单引号用 `\'` 转义。
- **不成为产品事实源（ShitPM）**。标注内容只是 PRD/Design 内容的展示载体，不构成新事实源；不承诺脱离源文件后仍是权威规格。
- **展示必要上下文必须标明来源**：浮窗内容需标注"内容来源：design.md"或"内容来源：prd.md"。
- **高影响意见交由 Fix 回写 Design（ShitPM）**。不直接修改 Prototype 或 Design，按"高影响反馈结构化输出约定"输出意见清单。
- **不使用 `cp -r` 等 Unix 专属命令**：目录复制操作描述目标结果，由实际工具跨平台执行。
- **不硬编码特定 Agent 工具协议**：用通用编辑工具描述代替。

# 执行与自检

完成判据：标注系统已注入副本源码工程；关键点标记与备注已按 design 生成；副本构建通过；原始源码工程未修改；下方自检清单逐项通过。

完成后逐项自检：

- [ ] 执行的是初始化还是增量更新？
- [ ] 副本是否排除了 node_modules 和旧 dist，且 `npm run build` 通过？
- [ ] 同一组件/模块是否只有一个角标？
- [ ] 浮窗内容是否标注了来源（design.md / prd.md），且未声明脱离源文件后仍是权威规格？
- [ ] 浮窗是否支持点击开合与 X 关闭？点击浮窗是否隔离了页面事件？
- [ ] 角标是否 10px 粗体 amber？层级是否正确？
- [ ] 是否未修改 output/prototype/、output/prd/prd.md 和 output/design/design.md？
- [ ] **角标定位**：是否所有角标统一使用 `position: fixed` + `document.body` 挂载？
- [ ] **多容器场景**：是否检测了角标容器归属（`pm-badge-in-page` / `pm-badge-in-drawer` / `pm-badge-in-modal`）？抽屉/弹窗打开时主页角标是否隐藏？
- [ ] **数据格式**：`annotations.js` 的 content 字段是否使用单引号包裹？
- [ ] **来源标注**：浮窗内容是否标注了"内容来源：design.md"或"内容来源：prd.md"？
- [ ] **高影响意见清单**：是否在报告末尾按结构化输出约定列出待用户决策的高影响意见（ShitPM）？每条意见是否包含归属层、改什么、改成什么、影响范围、来源、建议处理六字段？
