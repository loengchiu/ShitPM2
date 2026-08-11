# Round 22 全量对抗性审查报告

> 审查对象：R21 基线（`3c1396d`）之后的全部改动，含已提交 4 个 commit（`4c650e5`/`9a02646`/`7279ddc`/`17ba90c`）与 **未提交工作树改动**（10 改 + 3 新文件 + 新增 `templates/prototype-vite/` 工程）。
> 审查性质：原型架构路线翻转（无构建 HTML ↔ Vite 源码工程）+ PRD 自包含 + review schema 精简 的对抗性复核——重点排查「路线翻转未收口导致双架构并存」「删除 schema 留悬空引用」「新检查被弱化以适配」。
> 审查日期：2026-08-11
> 方法：逐文件 diff 阅读 + 跨层引用程序化校验 + **真实素材实证**（对 `templates/prototype-vite/` 跑 source-check、对仓库自带 fixture 跑 consistency/structure）+ 全量 13 个测试套件复跑。

## 结论速览

- **无 P0 / 无 P1（阻断级）**。所有 13 个测试套件复跑全绿。
- **发现 4 个 P2**（均非阻断，但指向同一根因：原型架构路线翻转未收口）：
  - **P2-1**：已提交 HEAD 仍强制「无构建 HTML + 本地 lib」，未提交工作树整体翻回「Vite 源码工程」。`templates/prototype.html` 与 `lib/react-antd/`（6.9 MB）被降级为"迁移参考专用"，但仍在 bundle 内。
  - **P2-2**：`templates/prototype.html`（316 行）+ `lib/react-antd/*`（6.9 MB 完整 vendored minified React/AntD/echarts）在新项目下成为死重；无构建方案本身仅 `7279ddc` 引入，几乎无真实无构建原型需迁移。
  - **P2-3**：`scripts/python/download-prototype-libs.py`（向 `lib/react-antd/` 下载 vendored lib）在 Vite 路线下无消费者（依赖走 npm），沦为死代码。
  - **P2-4**：`stage-context.py` 的 `MINIMAL_READ_SET["prototype"]` 仍并列 `templates/prototype.html` 与新的 `templates/prototype-vite` + `prototype-source-check.py`；按"迁移专用"定位，`prototype.html` 不应再进入 prototype 阶段读取集。
- **schema 删除干净**：`review-result.schema.json` / `common.schema.json` 无一脚本实际加载（仅 `stage-prep.py` 注释提及 `status.schema.json`，该文件仍存在）。无运行期悬空引用。
- **新检查未弱化**：`prototype-source-check.py` + 其 8 用例测试真实覆盖有效工程 / 缺失 src / 缺 build / src 引 dist / compiled 旧产物 / 单 BAT 菜单 / consistency 读 JSX 排除 dist·node_modules / structure 提取路由，含一处针对性回归守卫（空串后字段引号配对漂移）。

---

## 一、审查范围与基线

| 维度 | 内容 |
|---|---|
| 上次审查基线 | R21 `3c1396d` |
| 本次新增已提交 | `4c650e5`（质量回归计划，docs）、`9a02646`（PRD 自包含）、`7279ddc`（无构建方案）、`17ba90c`（移除 review schema + prototype 写法沉淀） |
| 本次未提交 | 10 改 + 3 新文件（`references/prototype-mark-injection.md` 247 行、`scripts/python/prototype-source-check.py` 150 行、`test-prototype-source-check.py` 239 行）+ 新增 `templates/prototype-vite/` Vite 工程 |
| 已提交净变更 | 40 文件，+2316 / −757 |
| 未提交净变更 | 10 文件，+635 / −540 + 新文件 |
| 最大改动面 | prototype 全套（SKILL×3、USAGE、consistency +89、structure +143、新增 source-check + template + mark-injection）+ PRD 自包含（模板/SKILL/writing-rules） |

本次是「路线翻转 + 自包含强化」主线：prototype 在 `7279ddc` 切到无构建后，工作树又整体翻回 Vite；PRD 改为不依赖外部文件、页面标题逐字采用 Design 名称、恢复流程图交付。

---

## 二、逐层审查与实证结果

### 2.1 原型架构路线（核心）
- **HEAD（已提交）** = 无构建：`spm-prototype` SKILL 强制「HTML + React 18 + Ant Design 6 + 本地 lib」；`prototype-consistency-check.py` 解析 `*.html`（`rglob("*.html")`，期望 `output/prototype/**/*.html`）。
- **工作树（未提交）** = Vite：全套 `spm-prototype` / `spm-prototype-review` / `spm-prototype-mark` / `USAGE.md` 均改为「标准 Vite + React 18 + Ant Design 6 源码工程」，`src/` 唯一编辑源、`dist/` 可重建、`原型工具.bat` 唯一入口；`prototype-consistency-check.py`(+89) / `prototype-structure.py`(+143) 改为解析 JSX；新增 `prototype-source-check.py` 校验 Vite 契约；新增 `templates/prototype-vite/` 标准工程。
- **工作树 Vite 方向内部自洽**：grep 确认 skills/references/contracts/USAGE 中已无「无构建 / 本地 lib / HTML + React / babel」残留表述；`prototype-mark` 正确注入 `src/` JSX 并在 `App.jsx` 挂载 `MarkLayer`；`USAGE.md` 工具表新增 `prototype-source-check.py`。
- **实证**：对 `templates/prototype-vite/` 跑 `prototype-source-check.py` → 其 10 项契约（index.html / package.json+lock / vite 配置 / src / dev·build·preview scripts / main.jsx+routes / src 不引 dist / 无 compiled 补丁链 / 不依赖 prototype-p0 / node_modules 不在 dist / BAT 调 dev·build·preview / README 首屏 BAT 入口）全部通过（测试 `test_valid_project_passes` 复验）。Vite 模板静态核对：import 链完整（`main.jsx`→`App.jsx`→`routes.jsx`→`modules/home/Home.jsx`）、`base:'./'` 适配 Cloudflare 子路径、菜单从路由表派生。✓（强项）

### 2.2 Review schema 删除
- `17ba90c` 删除 `schemas/review-result.schema.json`（67 行）并精简 `common.schema.json`(−10) / `status.schema.json`(−20)。
- 程序化校验：全仓活动脚本/skills 无任何 `import`/`json.load` 指向这两个已删文件；仅 `docs/plans/*`（陈旧计划）与 `stage-prep.py` 注释提及，不影响运行。review 输出改为人读 `.workflow/reviews/*-review-N.md`（含结论/问题清单/三类分布/needs_upstream_sync）。✓（干净）

### 2.3 PRD 自包含与页面承接
- `templates/prd.md` 首段改为「本文已承接已确认产品事实，研发以本 PRD 正文为开发依据；正文不依赖外部规格文件」。
- `prd-writing-rules.md` 新增：规则 6（流程图条件）、规则 8（流程图生成：drawio + 2× PNG 嵌入 `4.x.4`）、规则 5（自包含硬约束：禁止 `Design §x.x` / `output/design/design.md` 等跨文件指针）、规则 6（图只辅助、不新增事实）。
- SKILL 阶段 B/C/D 同步：页面标题逐字采用 Design 页面名称；流程图适用性判断；自包含整合。
- 逻辑闭环：页面标题与 Design 名称严格一致后，既满足「承接 Design」又满足「不写 `Design §x.x`」——跨文件指针由生成期 consistency 门禁（比对 Design）承担，最终产物不含外部引用。**与 R21 P2-3 修复（"引用上游 Design 写 Design §x.x"）相比是更强约束的演进，非矛盾**。✓
- 测试覆盖：`test-prd-consistency-semantics` / `test-prd-style-lint` / `test-prd-simplification` 全绿，自包含与页面命名改动未弱化门禁语义。

### 2.4 Design 编排（小改）
- `design-index.py`(+8) / `stage-prep.py`(+36) / `stage-context.py`(+5)：小改。`test-design-index`(16) / `test-design-orchestrator`(8) / `test-design-orchestration-replay`(6) 全绿，未引入回归。

### 2.5 Tests 层
- 未提交新增 `test-prototype-source-check.py`（239 行，8 用例）真实覆盖 Vite 契约与 JSX 解析回归，非为适配而弱化（见 §2.1 实证 + §四强项 2）。

---

## 三、发现（分级）

### P2-1：原型架构路线翻转未收口，双架构并存
**证据**：HEAD `spm-prototype` SKILL 强制「HTML + 本地 lib 无构建」，工作树整体改为「Vite 源码工程」。已提交态与工作态对原型技术契约的定义完全相反。

**影响**：当前 bundle 若以 HEAD 为准则强制无构建、且不含 Vite 模板/source-check；若以工作树为准则强制 Vite。两者各自内部自洽，但**未提交改动未收口前，bundle 实质携带两套互斥的原型架构定义**。任何"基于当前提交发布"的动作都会把矛盾冻结进发布物。

**修复**：提交 Vite 翻转（或显式 revert 回无构建），使 HEAD 与工作树一致；不要带着"已提交无构建 + 未提交 Vite"的中间态发布。

### P2-2：无构建产物成为新项目死重（6.9 MB + 316 行）
**证据**：`templates/prototype.html`（316 行）与 `lib/react-antd/*`（6.9 MB，含 react/react-dom/antd/echarts/reset.css/antd.css 完整 vendored minified）在 Vite 路线下被 SKILL 降级为「仅旧静态原型一次性迁移参考，新项目不使用」，但仍随 bundle 分发。

**影响**：新项目从不使用这些文件，却要承担 6.9 MB vendored lib + 316 行模板的 bundle 体积与"哪份是权威"的认知混乱。无构建方案仅 `7279ddc`（2026-08 初）引入，现实中几乎不存在需迁移的无构建原型。

**修复**：提交 Vite 翻转时一并删除 `templates/prototype.html` 与 `lib/react-antd/`（或移入明确标注的 `legacy/` 并加醒目弃用说明）。若确有旧无构建产物需迁移，保留迁移脚本即可，不必常驻主 bundle。

### P2-3：`download-prototype-libs.py` 在 Vite 路线下沦为死代码
**证据**：该脚本向 `lib/react-antd/` 下载 React 18 / Ant Design 6.5.4 / babel / dayjs 等 vendored lib，是无构建方案的配套下载器。Vite 路线依赖走 `npm ci`（package.json/package-lock.json），不再需要 vendored lib。

**影响**：无消费者，纯死代码；与 P2-2 同源。

**修复**：随 P2-2 一并删除，或在脚本顶部加弃用注释说明仅用于遗留无构建迁移。

### P2-4：`stage-context.py` prototype 读取集仍含 `prototype.html`
**证据**（`stage-context.py:96`，未提交 diff）：`MINIMAL_READ_SET["prototype"]` 在新增 `templates/prototype-vite` + `prototype-source-check.py` 的同时，仍保留 `templates/prototype.html`。

**影响**：无害（仅多加载一个迁移专用模板进上下文），但与"新项目不使用 prototype.html"的定位不一致，增加上下文噪声。

**修复**：提交 Vite 翻转时从 prototype 读取集移除 `templates/prototype.html`。

---

## 四、已确认干净的强项（非缺陷，记录以备查）

1. **工作树 Vite 翻转完整自洽**：SKILL×3 / USAGE / consistency·structure / source-check / 模板 / 测试 / mark 全部对齐 Vite，无"无构建"表述残留；`prototype-mark` 正确注入 `src/` 并在 `App.jsx` 挂载标注层。
2. **`test-prototype-source-check.py` 质量高**：8 用例真实覆盖 Vite 契约各分支，且含针对"空串后字段引号配对漂移"的回归守卫——证明 consistency 解析器曾真实修过该 bug 并锁定。
3. **schema 删除无悬空运行期引用**：仅陈旧的 `docs/plans/` 与 `stage-prep.py` 注释提及，不影响脚本。
4. **PRD 自包含逻辑闭环**：页面标题严格对齐 Design 名称，使"承接 Design"与"不写跨文件指针"可同时满足；consistency 门禁在生成期承担跨文件比对，最终产物零外部依赖。
5. **Vite 模板工程化正确**：`package.json`（react 18.3.1 / antd ^6.6.0 / vite ^8.2.1）、`base:'./'` 适配 Cloudflare 子路径、Hash 路由、菜单由路由表派生——满足 source-check 全部 10 项契约（测试实证）。

---

## 五、测试结论

| 套件 | 结果 |
|---|---|
| test-anti-hallucination | PASS |
| test-context-loading | PASS |
| test-context-runtime | PASS |
| test-design-index | PASS（16） |
| test-design-orchestration-replay | PASS（6） |
| test-design-orchestrator | PASS（8） |
| test-design-simplification | PASS |
| test-prd-consistency-semantics | PASS |
| test-prd-simplification | PASS |
| test-prd-style-lint | PASS（十二类） |
| test-prototype-source-check | PASS（8，新增） |
| test-resource-integrity | PASS |
| test-shitpm-regression | PASS（3） |

13/13 全绿。新增 `test-prototype-source-check` 真实覆盖 Vite 契约与 JSX 解析回归，未发现为适配简化/翻转而弱化的断言。

---

## 六、修复优先级建议

| 优先级 | 项 | 修复量 | 门禁影响 |
|---|---|---|---|
| 高（收口前必做） | P2-1 提交 Vite 翻转，消除双架构并存 | 提交现有工作树（含 P2-2/3/4 清理） | 否则发布物冻结架构矛盾 |
| 中 | P2-2 删除 `prototype.html` + `lib/react-antd/` | ~6.9 MB + 316 行移除 | 降 bundle 体积与认知混乱 |
| 中 | P2-3 删除 `download-prototype-libs.py` | ~47 行 | 去死代码 |
| 低 | P2-4 `stage-context.py` 读取集移除 `prototype.html` | 1 行 | 降上下文噪声 |

四项同源（路线翻转未收口），建议一次性随 Vite 翻转提交收口，而非零散改。

---

## 七、审查方法备注

- 本报告结论均经**实证**而非仅代码阅读：对 `templates/prototype-vite/` 跑 `prototype-source-check.py` 验证 Vite 契约全通过；用 `test-prototype-source-check.py` 的 jsx fixture 验证 consistency 读 JSX、排除 dist/node_modules 及空串字段引号配对回归；程序化校验 schema 删除无脚本加载残留；grep 确认工作树无"无构建"表述残留。
- 关于"0 行空文件"的误判已纠正：初看 `wc -l` 显示 `dayjs.min.js`/`locale-zh-cn.js` 为 0 行，查证为 minified 单行（7161 / 1463 字节），vendored lib 实际完整，无构建方案并非因文件缺失而坏——死重论点成立但非"损坏"所致。
- 曾一度将"HEAD 与工作树架构相反"判为 P1（担心已提交态 broken），实证确认 HEAD 内部自洽（无构建 SKILL + HTML 解析检查）、工作树内部自洽（Vite SKILL + JSX 解析检查），分歧仅存在于 HEAD↔工作树之间，故下调为 P2（路线翻转未收口的过程风险）。记录以免后续 reviewer 重复误判。
