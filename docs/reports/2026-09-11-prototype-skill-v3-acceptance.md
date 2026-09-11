# Prototype Skill v3 验收报告（2026-09-11）

> 执行手册：`docs/plans/2026-09-11-prototype-skill-v3-plan-and-acceptance.md`
> 分支：ShitPM `codex/prototype-skill-v3`（未 push）；存量工程 `D:\work\交投软件中心\审计系统` master（未 push）
> 结论：**PASS**（含 2 项按用户拍板的例外口径，见 §二/§三）

## 一、执行轨迹

| 任务 | 结果 | 提交 |
| :-- | :-- | :-- |
| T-0 基线 | 12 套件 11 绿 1 存量红；工作区在途改动以 `0e36bb7` 快照入库存证 | — |
| T-1 卸载 ProComponents | `@ant-design/pro-components` 及死资产（claudeTheme/traework/三选一口径）清零 | 已分独立提交 |
| T-2 视觉对齐官方 | 主题仅留颜色（Tabler 主色 `#066fd1`），尺寸/字体/阴影/圆角全回官方默认；图标收敛 `@ant-design/icons` 单一入口 | 已分独立提交 |
| T-3 新规范 | `prototype-page-types.md` + `prototype-role-permission.md` + `prototype-component-behavior.md`，**用户审阅通过**（"按1；通过"） | `f33d773` |
| T-4 SKILL/契约同步 | 双 SKILL + checklist + visual-spec + writing + ADAPTATION 同步；`dataField` 锚点补丁回退 | `6f3fac1` / `3b2b99b` |
| T-5a 视觉层 | 存量审计原型 14/14 阈值实测 PASS | `3637f81` |
| T-5b 结构回改 8 项 | #1 返回钮 / #3 分页 / #4 筛选折叠 / #5 数量徽章 / #7 省略 / #8 钉列滚动 / #9 状态标签上标题 / #10 版权行，逐项独立提交 | `a0e1711`…`c71b6f7` |
| T-6 验收 | 本报告 | — |

验收期新增修复（各独立提交、可回退）：

| # | 缺陷 | 修复 | 提交 |
| :-- | :-- | :-- | :-- |
| F1 | `底稿详情` 双分支 Descriptions 状态不一致（标题旁硬编码快照分支值） | 标题 Tag 改 `snap ? A : B`，静态分支残留字段删除 | `c71b6f7` |
| F2 | `法规制度库` 状态字段在查看 Modal 内被误迁到页面标题 | 整体回退该处迁移 | `c71b6f7` |
| F3 | 徽章 Card 把 JSX 塞进 `title` 后，`data-block/data-state` 属性排在 `title` 之后会被一致性检查的 `in_tag` 状态机错误剥串，**锚点静默丢失**（possible_omissions +1） | 4 处 Card 的 `data-*` 前移到 `title` 之前（DOM 不变） | `82ce35b` |
| F4 | **antd 6 rc-table 钉列取值变更**：`fixed: 'left'/'right'` 已不参与钉列机制（仅认 `'start'/'end'`），不报错、静默失效。存量 19 处 + 模板 2 处全部中招，钉列实际从未生效 | 全部改 `'start'/'end'`；`prototype-page-types.md` 补 ⚠️ 条款；实测 `ant-table-cell-fix-end` 类渲染正常 | `2da5eb0` / `98b2db7` |

## 二、§5.1 自动化门槛（逐项退出码）

| # | 项 | 结果 |
| :-- | :-- | :-- |
| 1 | 12 套件 `test-*.py` | **12/12 exit 0**（优于基线：存量红灯 `test-prd-simplification.py` 本轮已转绿；无新增红灯） |
| 2 | `prototype-source-check.py` | 模板工程（`--project-root . --prototype-root templates/prototype-vite`）**15 项全 PASS，exit 0**。注：对 ShitPM 仓根直跑会命中历史遗留的空目录 `output/prototype`（老提交产物，本次未触碰，T-0 前即如此，非新增红灯） |
| 3 | `prototype-consistency-check.py` | 模板 0 conflict / 0 omission。审计存量与 T-5 前备份**归一化路径差分**：`deterministic_conflicts` 11→11（0 新增）；`possible_omissions` 762→762（F3 修复后 0 新增）；`needs_semantic_judgment` +2（T-5b 新增的 展开/收起、返回 demo 控件无 `data-operation`，属信息项，语义上并非 Design 授权操作） |
| 4 | `npm run build` | 模板与审计工程均 exit 0 |
| 5 | 禁词 grep | 运行时文件 0 命中；`references/design-sources/ant-design-official/*.md` 6 份官方原文对 ProTable 的规范性引用属参考文档，不在运行时口径内 |

## 三、§5.2 浏览器阈值（13/13，含已拍板例外）

1-6、8-13 全部 PASS（32px 控件 / 24px 卡片内边距 / 16×16 单元格 / 14px 表头 / 阴影非 Tabler 基 / 全 `.anticon` / 主色 `rgb(6,111,209)` / 页底与表头底 `rgb(249,250,251)` / 无 `#1677ff` 泄漏 / console 0 error 0 warning）。

第 7 项字体：按用户拍板①，判据为 **不含 `Inter`** → PASS。负面结论（不得省略）：antd 官方默认字体栈不含显式 CJK 声明，中文依赖系统 fallback 渲染；7b"显式声明 PingFang SC / Microsoft YaHei"在官方栈下不可达，属**已接受**口径而非缺陷。

## 四、§5.3 角色差异（7/7）

切换器右上角（头像+角色名，点击展开）、默认管理员、菜单项数变化（4→3，消失非置灰）、按钮差异、字段对出现/消失、数据范围提示、切换无刷新（URL 不变）全部 PASS。

## 五、§5.4 反向检查（4/4）

1. 颜色未被官方覆盖：§5.2 第 9/10/11 项 PASS。
2. 项目组习惯：三栏固定（header/sider sticky）✓；侧栏浅色 `rgb(255,255,255)` ✓；首末列钉住 ✓（F4 修复后线上实测 5 个 fix 类细胞）；表单竖排 ✓（`ant-form-vertical`）；底部通栏操作栏 ✓（sticky bar 含按钮）；版权行"研发单位：广西计算中心" ✓（18 处页面级）。标签页栏：存量审计原型从未有该机制，不在 T-5 范围，未被本次改动破坏。
3. 侧栏浅色：未回退深色。
4. 交付链路：`dist/` + `wrangler.toml`（审计工程）在位，`原型工具.bat` 第 4 项实测可用（见 §六）。

## 六、§5.5 交付验收（线上实测）

- 上传：`wrangler pages deploy dist` → **https://audit-system-prototype.pages.dev**（F4 修复后二次部署生效）。
- 线上浏览器实测（真实 Chromium）：默认页、列表类（`/#/plan?p=pl01` 表格渲染）、详情类（`/#/plan?p=pl02` 标题旁状态 Tag）、表单类（`/#/prepare?p=pr03` 交互控件）、角色切换器 + 侧栏菜单 14 项、console 无 error —— **ALL PASS**。

## 七、未解决项与建议

| # | 事项 | 建议 |
| :-- | :-- | :-- |
| 1 | 两仓库均未 push（用户规则：等拍板） | 待用户确认后合入/push |
| 2 | ShitPM 仓根历史空目录 `output/prototype` 会让 `source-check --project-root .` 误报 9 项 FAIL | 建议后续清理该目录或改用 `--prototype-root` 口径（未动，避免混入本次范围） |
| 3 | 一致性检查 `in_tag` 状态机对"属性值内嵌 JSX 标签"的解析盲区（F3 根因） | 规范已通过"锚点约定"约束写法；如后续再发，考虑给 `_strip_js_strings_and_comments` 补 JSX 表达式括号深度跟踪（需按工具准入四证据立项） |
| 4 | 审计工程工作区另有**与本任务无关的在途改动**（`output/design/design.md`、`.workflow/` 等 ShitPM 产物，T-0 前即存在） | 未触碰、未混入提交；由用户决定去留 |
| 5 | antd 6 `fixed` 取值变更（F4）属**生态级静默破坏**，模板/规范已修，但其他 antd6 存量项目可能同样中招 | 建议在其他 antd6 项目排查 `fixed: 'left'/'right'` |

## 八、验收结论（模板）

```text
结论：PASS
- §5.1 自动化：5/5 通过（套件 12/12 绿；两处口径例外已注明：仓根空目录误报、官方原文引用）
- §5.2 尺寸阈值：13/13 通过（第 7 项按拍板①以"不含 Inter"判定；CJK 显式声明为已接受负面结论）
- §5.3 角色差异：7/7 通过
- §5.4 反向检查：4/4 通过（标签页栏为存量无、未破坏；钉列经 F4 修复后实测通过）
- §5.5 交付：线上网址 https://audit-system-prototype.pages.dev 实测通过（默认页 + 3 类路由 + 角色切换 + console 干净）
- 未解决项：见 §七（均为范围外/待拍板项，无阻断）
- 负面结论（不得省略）：antd 官方默认字体栈不含显式 CJK 声明，中文由系统 fallback 渲染；antd 6 钉列必须用 fixed: 'start'/'end'，'left'/'right' 静默失效
```
