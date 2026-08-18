# 组件行为规范修复 · 对抗性审查报告

> 日期：2026-08-18 00:20
> 审查对象：其他 AI 对"组件行为规范"的修复落地（工作树未提交改动：`references/prototype-component-behavior.md` 新建 + spm-prototype / spm-prototype-review / review-checklist / templates/prototype-vite 同步改动）
> 基准：`docs/plans/2026-08-17-tabler-components-spec-draft.md`（Tabler 全量抽取规范）
> 结论：**0 P0 / 1 P1 / 4 P2**。整体质量高，核心规范与落地一致；P1 为两份必读规范互相矛盾，需二选一后合入。

---

## 审查通过项（达成）

| 项 | 证据 |
|---|---|
| 行为规范文档本体 | `references/prototype-component-behavior.md`：10 章 + 验收清单；Tabler 标准值准确（标题 h2 20px/600、侧栏 15rem、滚动条极简非隐藏、表格无固定列、操作列 ≤3、`bg-*-lt` 状态、`space-y` 表单）；产品选择（侧栏 200 / 卡内边距 24 / 标题 24）均标 `[ShitPM 适配]` |
| 生成侧执行链 | `spm-prototype/SKILL.md` 第 5 步必读 behavior，完成条件含"表格固定列、操作列 ≤3、主按钮唯一"等 |
| 审查侧执行链 | `spm-prototype-review/SKILL.md` 第 8 步按 behavior 第 10 节验收；`contracts/prototype-review-checklist.md` 新增第 18 条"组件行为规范执行"（P2 级） |
| 模板落地 | Sider 220→**200px** + `sider-menu-scroll` 菜单独立滚动 + 8px 细滚动条（`scrollbar-width: thin`，**非隐藏**）；`.page-title` 24px/600；表格 fixed 层级规则齐（`isolation:isolate` + fixed 实底背景 + thead z-index 4 / tbody z-index 3 + 左右边界轻阴影）；`@tabler/icons-react` 入依赖 |
| 模板样例 | `Home.jsx` 操作列 3 个图标按钮（查看/编辑/删除），符合 ≤3 |
| 测试 | 除资源完整性外全绿（source-check 8 用例 / design-set / prd-style-lint / regression / design-index） |

---

## P1（必改，阻断合入）

### P1-1：两份必读规范互相矛盾——表格 fixed 列

- `references/prototype-component-behavior.md` §4："**默认不固定列**"，列多用 `.table-responsive` 整表横滚；固定列需特殊授权。
- `references/prototype-visual-spec.md` 断点表（134 行）："宽屏 ≥1200：完整桌面层级；**表格操作列 `fixed: right` 冻结**"。

生成器同时必读两份文档，得到相反指令：behavior 说默认不固定，visual-spec 说宽屏默认固定右列。这正是养护项目"固定列重叠"缺陷的根源写法，被重新写回了规范。

**修复建议（二选一，推荐前者）**：删除 visual-spec 134 行"操作列 fixed: right 冻结"表述，改为"宽屏：操作列 ≤3 按钮，多用 '更多' 下拉；确需 fixed 时按 behavior §4 层级规则"。与 Tabler 标准（无固定列）+ behavior 保持一致。两文件必须同步后再合入。

---

## P2（建议修，不阻断）

### P2-1：behavior §1 引用失效
behavior §1 声称"当前模板 `.page-title` 设为 24px……**已在视觉规范注明**"，但 `prototype-visual-spec.md` 无此注明（全文无 page-title / 大标题 / 标题 24px 条目）。补 visual-spec 注明，或改 behavior 表述。

### P2-2：新文件未过资源完整性门禁
`test-resource-integrity` 失败：`prototype-component-behavior.md` 超 100 行但缺"目录"。新文件没跑通门禁就进了工作树。

### P2-3：SKILL 编号重复
`spm-prototype/SKILL.md` 出现两个"5."（behavior 读取与 feedback 归类都编成 5），后者应为 6。

### P2-4：模板缺 .gitignore
`templates/prototype-vite/` 无 `.gitignore`，`node_modules/` 与 `dist/assets` 进入 git untracked，污染状态。模板应带 `.gitignore`（`node_modules/`、`dist/`）。

---

## 附：未验证项

- 未用真实 Design 重新生成原型做端到端验收（behavior 的"操作列 ≤3 / 无固定列 / 滚动条"需在真实生成产物上确认不复发）——建议修完 P1 后用养护平台 Design 重生成对照。
