# 官方规范引入说明（Ant Design Skill）

> 来源：`https://github.com/AntGroupDesign/Ant-Design-Skill`（Ant Design 官方**设计团队**）
> 许可：MIT License, Copyright (c) 2024-present Ant Design Skill
> 抓取日期：2026-09-11

## 本目录是什么

本库的**页面排版与组件行为规范源**。提供"结构与交互规则"——按钮放哪、用弹窗还是抽屉、表头怎么对齐、列宽档位、内容线留白等。

生成原型时**按页面类型只读命中章节**（路由见 `skills/spm-prototype/SKILL.md`），**不整包加载**。

## 引入范围（只取规则）

| 官方资产 | 是否引入 | 原因 |
| :-- | :-- | :-- |
| `references/` 6 个 md（约 290KB） | **引入** | 纯规则 + 通用写法示例，零依赖 |
| `references/global-style.css`（76KB） | **不引入** | antd5 原生配色（`--color-primary: #1677ff`），与本库 Tabler 颜色主题冲突 |
| `scripts/` 32 个 TSX 模板 | **不引入** | 依赖 Pro 系列组件包（beta），本库不引入任何重型组件库 |

## 总口径（2026-09-11 拍板）

**尺寸、字号、间距、阴影、控件规格与结构规则一律照官方原文执行；仅颜色换 Tabler。** 主题文件只保留颜色 token，不覆盖任何非颜色项，官方默认自行生效。

官方原文中出现的 Pro 系列增强组件写法（表格 / 表单 / 卡片等的高级封装组件），一律按语义等价的 antd 原生组件实现（Table / Form / Card + 组合），本库不引入该依赖；其描述的**布局结构、间距节奏与交互规则**仍然有效。

## 三条转换规则（读任何一章前先看这里）

1. **颜色一律用本库主题，不用官方色。** 官方文档基于 antd5 默认蓝（`--color-primary: #1677ff`、success `#52c41a`、warning `#faad14`、error `#ff4d4f`）。本库是 Tabler 主题（主色 `#066fd1`）。文档里出现的任何色值只作**语义标签**理解（"主色""成功色""警示色"），实际取值以 `templates/prototype-vite/src/theme/tablerTheme.ts` 与 `src/styles/global.css` 为准。

2. **`var(--xxx)` 只取数值语义，不照抄变量名。** 本库未定义官方 `global-style.css` 那套变量（`--padding-lg` / `--color-text` / `--nav-space-6` 等）。遇到时按其**字面数值**换算：`var(--padding-lg)` → `24px`，`var(--color-text)` → 本库正文色 token。

3. **结构与行为规则原样执行。** 表头不换行、短枚举列宽档位、弹窗三段式高度、抽屉按钮位置、内容线对齐、筛选数量阈值（≤4 单行工具栏 / ≥5 独立搜索卡）、文本省略与浮窗等，是本目录的核心价值，逐条执行。

## 数值对照（结构数值基本一致，可直接采用）

| 语义 | 官方变量 | 官方值 | 本库 |
| :-- | :-- | --: | :-- |
| 圆角 · 控件 | `--border-radius` | 6px | `borderRadius: 6` ✅ 一致 |
| 圆角 · 小 | `--border-radius-sm` | 4px | `Tag.borderRadiusSM: 4` ✅ 一致 |
| 圆角 · 大 | `--border-radius-lg` | 8px | `borderRadiusLG: 8` ✅ 一致 |
| 间距 · 基础 | `--padding` | 16px | 16px ✅ 一致 |
| 间距 · 大 | `--padding-lg` | 24px | 内容区 24px ✅ 一致 |
| 正文字号 | `--font-size-sm` | 14px | 14px ✅ 一致 |
| 顶部导航高 | `--nav-header-height` | 56px | 56px ✅ 一致 |
| 表头底色 | `--color-table-header-bg` | `#fafafa` | `#f9fafb`（**以本库为准**） |

> 结论：官方与本库在**圆角/间距/字号/导航高**上完全同源，只有**品牌色**不同。因此官方规则可直接执行，只需替换颜色。

## 图表章节的额外说明

`components_Chart.md` 基于 `@ant-design/charts`（10 处引用），本库使用 **ECharts**。
**适用**：图表选型、容器规则、标题与操作区、视觉规格、Tooltip 规则、颜色/图例/标签规范、数据表达、加载/空态/错误态、指标卡全部规则。
**不适用**：`@ant-design/charts` 的 API 写法，实现时改用本库 ECharts。

## 已知缺口（本库自行补充，官方 6 章均 0 处）

- **固定表头（sticky header）**：官方未涉及。本库规则见 `references/prototype-visual-spec.md` 表格章节与 `references/prototype-component-behavior.md`。

## 原文完整性

6 个文档**正文未改动**，仅在每篇一级标题后注入一段「阅读须知」引用块（标明本库转换规则）。
升级方式：重新抓取官方仓库同名文件覆盖正文，保留顶部须知与本 ADAPTATION.md。
