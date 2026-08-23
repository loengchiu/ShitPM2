# Prototype 效率优化迭代对抗性审查报告

> 日期：2026-08-18
> 审查对象：`docs/plans/2026-08-18-prototype-shared-ui-loading-path-closeout-optimization-plan-and-acceptance.md` 及其执行结果
> 审查方法：通读计划 + 对照 `git diff` 与改后文件逐条核 + 跑确定性测试 + 构建
> 基线：跨层契约修复（仍在未提交工作树，V2 分支）作为既有基线，本轮在其上叠加

## 1. 结论

**0 P0 / 0 P1 / 3 P2（全非阻断）。放行。**

本轮按计划完成了四件事：高频结构默认路径前移、behavior 收敛、规则冲突消除、TablerModal 按消费者门槛延期。没有新增检查器/回执/门禁，没有为缩短文档而删停止条件或真实浏览器验收，符合 AGENTS.md 精简原则。3 个 P2 均为文档轻微过期或验证证据归属问题，不影响交付。

## 2. 本轮修改核实（逐文件）

| 文件 | 改动 | 核实 |
|---|---|---|
| `skills/spm-prototype/SKILL.md` | 第5步从"必读全文 behavior"改为"先查 shared/ui 真实导出"；第6步改为"仅命中场景时读 behavior 对应章节"；完成门槛保留并强化（真实浏览器交互、条件加载 behavior） | ✓ 符合计划阶段2，未删停止条件 |
| `references/prototype-component-behavior.md` | 269 行 → 51 行；只留组件选择判断/特定例外/跨层契约/适用验收四类，删除全部 API 复述、视觉值、工程写法 | ✓ 符合阶段3，无第二套数值 |
| `references/prototype-writing.md` | 补 hash query 解析、CSS 变量挂 documentElement、JSX import、稳定 ID、Table wrapper 不丢配置、dayjs 双向、Modal footer 规则；**表格 fixed 列从"操作列 fixed:right"改为"确有需要才固定"** | ✓ 消除与 behavior 冲突 |
| `references/prototype-visual-spec.md` | TablerIconButton 从"文本按钮"纠正为"图标按钮"；TablerDataTable 去"操作列固定"改"默认不固定列"；断点 768px→575/576/991/992；列表/表单页头改"壳层页签表达" | ✓ 纠正旧错误描述 |
| `skills/spm-prototype-review/SKILL.md` | 第8步从"逐项第10节"改为"按真实场景读适用章节，不漏审" | ✓ 生成路径变短未导致 Review 漏项 |
| `contracts/prototype-review-checklist.md` | 第18项改为"适用组件行为边界"；新增第19项跨层运行时契约（P1） | ✓ |
| `templates/prototype-vite/src/shared/ui/index.jsx` | TablerRowActions 图标按钮→文字按钮（代码化 Tabler 约定）；TablerStatusTag 未知状态→error 档（不伪装）；TablerDataTable scroll/locale 正确合并；TablerEmptyState span→div | ✓ 运行时代码改动，构建通过 |

## 3. 对抗性审查发现

### P2-1：visual-spec 对 behavior 的章节引用过期

`prototype-visual-spec.md` 列表页第4条写"行末文字操作列……与组件行为规范 §4 一致"。但新 behavior 文档已重排为四节，操作列规则实际在 **§2（特定场景例外 → 表格与操作）**，§4 是"适用验收"。规则内容本身在 visual-spec 已自包含正确，仅章节号指错。

- 处置：改 visual-spec 第4条引用为"§2"即可；不影响实现。

### P2-2：TablerRowActions 文档注释仍列 `icon` 字段但可见按钮已不渲染图标

`shared/ui/index.jsx` 第139行注释 `items: [{ key, label, icon, danger, disabled, onClick }]`，但可见按钮已改为 `<Button>{it.label}</Button>`，不再使用 `it.icon`。当前调用方（Home.jsx）不传 `icon`，无功能影响；仅注释与实现轻微脱节。

- 处置：注释去掉 `icon` 或注明"文字按钮不使用 icon"；非阻断。

### P2-3：运行时代码改动缺少本轮专属浏览器验证证据

本轮修改了 `shared/ui`（TablerRowActions 图标→文字、TablerStatusTag 未知→error），属运行时代码，按计划 §6.3 应做构建 + 浏览器回归。构建已通过（5.05s）；但 `.playwright-cli/` 现有 26 个快照时间戳均为跨层修复期（12:23–14:36），未见效率优化期新增的"文字操作列/未知状态红标"专项截图。该改动为纯视觉、不改交互逻辑、跨层已验证 Home 交互，风险极低，但证据归属不清晰。

- 处置：若执行方声称已验，补 1440 宽下"操作列文字按钮 + 一个未知状态红标"截图；否则在交付中明说"未独立验证，沿用跨层浏览器证据"。

## 4. 验证证据

| 检查 | 结果 |
|---|---|
| `test-prototype-source-check.py` | 8 用例通过 |
| `test-shitpm-regression.py` | 3 用例通过 |
| `test-resource-integrity.py` | 通过（路径/链接/目录/消费者引用正常） |
| `git -c core.whitespace=cr-at-eol diff --check` | 干净（跟踪文件无 trailing whitespace） |
| `npm run build` | 5.05s 通过（chunk >500kB 警告为既有状态） |
| 废弃写法搜索（第10节/return hash||'/'/:id/768px/操作列固定） | 活跃规则文件零命中；仅历史报告/计划文档引用 |

## 5. 关键判断

1. **TablerModal 决策正确**：模板仅 `modal.confirm`（Home.jsx），无受控 `<Modal>` 消费者。按阶段5门槛**延期不实现**，未造孤立组件、未伪造演示消费者。符合"A-08"。
2. **无悬空引用**：旧 behavior "第10节验收清单"已不下存在；SKILL/review/checklist 全部改为"命中章节/适用边界"，活跃文件零指向已删章节。
3. **调用方安全**：Home.jsx 的 TablerRowActions items 均显式 `key`（view/edit/delete），移除 `it.key || it.label` 兜底无副作用。
4. **效率目标达成**：普通页面生成路径从"读 260 行 behavior 全文"降为"查 shared/ui 源码 + 命中场景才读 behavior 章节"；Tabler 约定（文字操作列、未知状态红标）已代码化，AI 不必读文档即得。例外路径（表格/表单/Portal/响应式）仍完整，Review 不漏项。

## 6. 保留问题与建议

1. P2-1/P2-2 两处文档轻微过期，建议提交前顺手修（各一行）。
2. P2-3 浏览器证据归属：补截图或明说"未独立验证"。
3. 工作树仍为跨层修复 + 效率优化合计 20 改 + 4 未跟踪，未 commit/未 push（符合规则）。提交后推 gitee(origin) 正常；推 github 需 Clash 代理：`git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=... push github V2`。
4. 历史损坏文件 `docs/plans/2026-08-17-tabler-components-spec-draft.md`（base64 损坏，非本轮所改）仍需在提交前 `git checkout --` 还原，否则随专项入库。
