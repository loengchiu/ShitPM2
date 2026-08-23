# PRD 优化迭代执行指令

下面整段内容可直接复制给负责实施的 AI。

---

你要在 `D:\work\ShitPM` 仓库内实施一次 PRD 结构与写作优化。

## 一、任务结论

这不是只改 `templates/prd.md` 的任务。

你需要让以下整条链路使用同一套新规则：

- PRD 模板；
- PRD 写作规则；
- PRD 生成 Skill；
- 场景清单和写作示例；
- PRD Review 清单与 Review Skill；
- 既有 PRD 文风脚本和一致性脚本；
- 受影响的现有测试；
- 少量 README、USAGE 和 Prototype 辅助说明。

目标是：PRD 按业务闭环组织，完整承接确认版 Design，同一模块内容尽量放在一起，使用结构化自然语言，有必要的流程使用 draw.io 源文件并导出 SVG。

## 二、先读，不要先改

必须完整读取：

1. `D:\work\ShitPM\AGENTS.md`
2. `D:\work\ShitPM\docs\plans\2026-07-31-prd-structure-design.md`
3. `D:\work\ShitPM\docs\plans\2026-07-31-prd-writing-design.md`
4. `D:\work\ShitPM\docs\plans\2026-07-31-prd-optimization-implementation-plan.md`
5. `D:\work\ShitPM\docs\plans\2026-07-31-prd-optimization-acceptance.md`

两份 Design 文档是本轮结构和写法的已确认基线；执行方案定义影响范围和实施顺序；验收方案定义最终通过标准。不要自行重新设计另一套 PRD 结构。

读取后先检查当前 Git 状态和修改前测试基线，但不要暂存、提交或推送。

## 三、必须遵守的边界

### 1. 事实边界

- 确认版 `output/design/design.md` 是 PRD 的产品事实源；
- 不能从常见产品经验静默补造页面、字段、状态、权限、流程、参数、提示文案或外部系统行为；
- 涉及核心流程、角色权限、数据范围、关键状态、系统边界或范围边界的未知，必须保留为待确认或回到 Design；
- 结构和自然语言可以优化，但不能改变 Design 语义。

### 2. 实施边界

禁止新增：

- Design → PRD 承接矩阵；
- 覆盖率 JSON；
- 新结构 Schema；
- 新检查器、统一检查器或综合门禁；
- 生成回执、验证回执或机器签名；
- 新 PRD 中间资产；
- draw.io 导出脚本；
- 新 Review 阶段或新固定 pass。

不要把 AI 应承担的业务判断写进 Python 脚本。脚本只处理确定性问题。

### 3. 修改边界

- 只修改与本轮 PRD 优化直接相关的文件；
- 不重构无关脚本；
- 不统一全仓库格式；
- 不修改 Design、Align、Prototype、Fix 的主流程；
- 不修改 Review 输出 Schema 和判定门槛；
- 不覆盖真实项目文件；
- 不执行 Git commit；
- 不执行 Git push。

## 四、必须修改的文件

按执行方案逐项处理：

1. `templates/prd.md`
2. `references/prd-writing-rules.md`
3. `skills/spm-prd/SKILL.md`
4. `references/prd-scene-checklist.md`
5. `references/prd-writing-examples.md`
6. `contracts/prd-review-checklist.md`
7. `skills/spm-prd-review/SKILL.md`
8. `references/prd-glossary-format.md`
9. `contracts/review-checklist.md`
10. `scripts/python/prd-style-lint.py`
11. `scripts/python/test-prd-style-lint.py`
12. `scripts/python/prd-consistency-check.py`
13. `scripts/python/test-prd-consistency-semantics.py`
14. `USAGE.md`
15. `README.md`
16. `references/prototype-writing.md`

以下文件只在现有测试因本轮新结构真实失败时修改：

- `scripts/python/test-anti-hallucination.py`
- `scripts/python/test-design-index.py`
- `scripts/python/test-prd-simplification.py`
- `scripts/python/test-shitpm-regression.py`
- `contracts/prd-writing.profile.json`
- `contracts/context-loading.manifest.json`

如果条件未满足，保持不变。尤其应尽量保留现有 marker 和 manifest，不要为了重命名而扩大修改。

原则上不修改：

- `contracts/subagent-context-contract.md`
- `references/prd-versioning.md`
- `schemas/review-result.schema.json`
- 其他 Design、Prototype、Fix Skill 和模板。

## 五、核心实施要求

### 1. 模板

把 `templates/prd.md` 改为：

- 文档信息；
- 产品定义与范围；
- 系统全景与共享规则；
- 若干业务闭环模块；
- 待确认事项索引。

每个业务模块能够就近容纳：

- 目标与边界；
- 业务对象；
- 角色、权限和数据范围；
- 流程；
- 状态与规则；
- 按业务阶段展开的功能；
- 字段；
- 外部协作、异常与恢复；
- 模块验收；
- 模块待确认事项。

删除旧的固定要求：

- 模块 → 小模块 → 页面 → 动作；
- 大模块末尾统一七列字段表；
- 小模块末尾固定状态机；
- Mermaid；
- 文末统一验收汇总；
- 文末统一风险与待确认。

必须保留：

```md
<!-- context:prd-template:start -->
<!-- context:prd-template:end -->
```

### 2. 写作规则

把两份已确认设计基线落实到 `references/prd-writing-rules.md`，至少覆盖：

- 按业务闭环组织；
- 系统共享规则与模块规则的边界；
- 管理端和移动端共同闭环；
- 页面作为承接载体但不是唯一组织轴；
- 结构化自然语言；
- 动作的条件、输入、处理、结果、状态、权限、失败和恢复；
- 字段“对象级定义 + 使用处补充”；
- 业务状态、展示状态、过程状态分开；
- 权限、异常、验收、待确认事项就近；
- 查询、统计、下钻、导出；
- 表单保存与提交、配置生效与历史影响；
- 外部系统的数据责任边界；
- 提示文案、默认值和数字只能在有事实依据时具体化；
- draw.io 源文件 + SVG；
- 最终逐项回读 Design，既查遗漏也查未授权新增。

必须保留 marker：

- `prd-writing-structure`
- `prd-writing-action`
- `prd-core-boundary`

### 3. PRD Skill

`skills/spm-prd/SKILL.md` 保持精简：

- 保留 Design confirmation；
- 普通 PRD 只走 `writing`；
- 超大型 PRD 才走 `module`；
- 不新增 pass、矩阵、回执或门禁；
- 生成前识别业务闭环；
- 生成后直接回读最终 PRD 并修正；
- 有必要的流程生成 `.drawio` 和 SVG；
- 最终质量检查使用业务闭环、事实承接、模块独立可读、图文一致、无未授权新增等标准。

不要把详细规则全文复制进 Skill。

### 4. 场景与示例

`references/prd-scene-checklist.md`：

- 不再默认要求长度、默认值、草稿、自动保存、分页、排序、超时、重试和补偿；
- 这些内容只有 Design 已确认或业务确实适用且有依据时才写；
- 保留 `prd-verification-scenes` marker；
- 补齐保存/提交、空值/零值/未知、配置生效和历史影响等新口径。

`references/prd-writing-examples.md`：

- 重写旧结构、Mermaid、七列表和无依据数字的正例；
- 增加业务闭环、跨端协作、业务阶段、字段两层表达、状态分类、外部协作、模块验收、模块待确认和 draw.io 引用示例；
- 尽量保留所有现有 `prd-example-*` marker ID，避免修改 manifest。

### 5. Review

`contracts/prd-review-checklist.md` 和 `skills/spm-prd-review/SKILL.md` 必须使用新口径：

- 检查业务闭环和模块独立可读；
- 检查页面、字段、状态、权限、异常、验收和待确认事项的准确落点；
- 检查管理端和移动端是否被拆散；
- 检查 draw.io、SVG 与正文一致；
- 检查 Design 无遗漏、无冲突、无未授权新增；
- 不再要求每个页面独立成章；
- 不再要求统一字段表；
- 不再要求文末验收和风险汇总；
- 不再要求补未确认分页、排序或上限。

Review 仍然只审查，不修改、不自动修复、不自动推进，输出结构和判定门槛不变。

同步：

- `references/prd-glossary-format.md` 不再固定第二章，“所在大模块”改为“所在业务模块”；
- `contracts/review-checklist.md` 只修改“补入统一字段定义表”的那一条，改为按所属业务对象或业务阶段就近补充。

### 6. 现有脚本

#### `prd-style-lint.py`

- STYLE003 适配业务模块正文，不再只依赖“详细需求说明”；
- STYLE004 支持新页面标识或页面锚点；
- 删除 STYLE010 对固定七列字段表的强制检查，并同步规则数量、帮助文案和测试；
- 保留其他低误报机械坏味道；
- 不新增业务闭环完整性、字段覆盖率或模块自包含率检查。

#### `prd-consistency-check.py`

最小适配：

- 从系统页面映射和业务模块页面落点识别页面；
- 合并读取多个业务对象或业务阶段中的局部字段表；
- 不依赖“详细需求说明/数据字典/字段定义”总章；
- 不把 PRD 业务闭环名称与 Design 菜单模块名称逐字比较；
- 模块语义完整性交给 AI；
- 保留明确页面、字段和已确认属性的确定性检查；
- 保持现有分类和退出码：只有 `deterministic_conflict` 返回 1，`possible_omission` 与 `needs_semantic_judgment` 返回 0。

同步现有测试，不新增测试框架。

### 7. 用户说明

最小修改：

- `USAGE.md`：不再写维持旧模板和页面组织，改为按业务闭环并在同一次生成中回读 Design；
- `README.md`：不再把统一字段定义表和独立 Design 清单作为目标；
- `references/prototype-writing.md`：PRD 辅助读取改为所属业务模块中的页面、字段、状态、权限和动作；Prototype 仍以 Design 为唯一事实源。

## 六、严格执行顺序

1. 读取全部基线与当前文件；
2. 运行修改前测试，记录基线；
3. 修改模板；
4. 修改正式写作规则；
5. 修改 PRD Skill；
6. 修改场景清单和示例；
7. 修改 Review 清单、Review Skill、名词规则和公共 Review 一条；
8. 修改文风脚本和现有测试；
9. 修改一致性脚本和现有测试；
10. 运行回归，根据真实失败决定条件文件是否需要修改；
11. 同步 USAGE、README 和 Prototype 辅助说明；
12. 运行完整验收；
13. 生成简单样本；
14. 在临时目录生成智慧停车区候选 PRD 与 draw.io/SVG；
15. 逐项回读 Design 并直接修正候选与规则缺陷；
16. 汇报结果并停止，不提交、不推送。

## 七、必须运行的自动化验证

从 `D:\work\ShitPM` 运行：

```powershell
python scripts\python\test-context-loading.py
python scripts\python\context-pack.py --project-root . --bundle-root . --stage prd --mode full --pass writing --dry-run
python scripts\python\context-pack.py --project-root . --bundle-root . --stage prd --mode full --pass module --dry-run
python scripts\python\test-prd-style-lint.py
python scripts\python\test-prd-consistency-semantics.py
python scripts\python\test-anti-hallucination.py prepare
python scripts\python\test-anti-hallucination.py verify
python scripts\python\test-anti-hallucination.py clean
python scripts\python\test-prd-simplification.py
python scripts\python\test-design-index.py
python scripts\python\test-resource-integrity.py
python scripts\python\test-shitpm-regression.py
```

如果某测试修改前已失败，要报告为基线失败。不要为通过测试而恢复旧 PRD 结构，也不要修改无关功能。

## 八、真实样本验收

只读使用：

- `D:\work\交投软件中心\智慧服务区\智慧停车区\output\design\design.md`
- `D:\work\交投软件中心\智慧服务区\智慧停车区\.workflow\confirmations\design.json`
- `D:\work\交投软件中心\智慧服务区\智慧停车区\output\prd\prd.md`

禁止覆盖或修改这些文件。

将候选生成到仓库临时目录，例如：

`D:\work\ShitPM\.tmp\prd-optimization-validation\smart-parking`

候选至少按以下业务闭环组织：

1. 车辆进出与停车记录；
2. 车流、车位与视频监测；
3. 滞留监测与现场处置；
4. 两客一危核查与告警处置；
5. 多级组织汇总分析。

验收重点：

- Design 的 21 个页面均有准确落点，但不要求 21 个独立章节；
- 移动端页面进入所属闭环，不再单独组成移动端大模块；
- “我的处理记录”只有一个权威定义；
- 每个模块可独立回答角色、前置、数据、状态、动作、权限、异常、恢复、验收和待确认事项；
- Design 的字段、页面、状态、规则、权限、异常、验收和待确认事项无高影响遗漏；
- PRD 无 Design 未授权新增事实；
- 必要流程同时存在 `.drawio` 和 SVG，图文一致；
- 不使用 Mermaid；
- 不以行数判断是否通过。

候选项目内运行：

```powershell
python D:\work\ShitPM\scripts\python\prd-style-lint.py output\prd\prd.md
python D:\work\ShitPM\scripts\python\prd-consistency-check.py --project-root .
```

文风错误必须为 0；一致性不得有 `deterministic_conflict`；其他结果必须人工逐项回读。

## 九、draw.io 验证

本机 draw.io：

`C:\Program Files\draw.io\draw.io.exe`

对每个 `.drawio` 重新导出 SVG：

```powershell
& 'C:\Program Files\draw.io\draw.io.exe' --export --format svg --output '<临时输出.svg>' '<源文件.drawio>'
```

确认：

- SVG 非空且可打开；
- 中文正常；
- 节点和连线不严重遮挡；
- 泳道、角色、状态、动作和异常分支与正文一致；
- 图中没有正文和 Design 未定义的新流程；
- 正文引用的 SVG 路径真实存在。

## 十、遇到问题时如何处理

### 可以自行处理

- 标题命名；
- 示例措辞；
- 自然语言组织；
- 低影响格式；
- 为保持 marker 而沿用旧 marker 名称；
- 根据实际测试结果调整已有测试夹具。

### 必须停止并说明

- 两份设计基线实质冲突；
- 需要改变核心流程、权限、状态、系统边界或范围；
- 需要新增检查器、承接矩阵、回执、Schema 或新 pass；
- 需要改变 Review 判定门槛或输出结构；
- 需要覆盖真实项目原文件；
- 需要 Git commit 或 Git push。

不要因为普通实现细节反复询问。目标和路径已经确定，按最小修改原则完成即可。

## 十一、完成后自检

按 `D:\work\ShitPM\docs\plans\2026-07-31-prd-optimization-acceptance.md` 的最终检查表逐项验收。

发现问题时直接修正最终文件和候选样本，不生成独立验证回执，不用“后续再优化”代替当前修复。

## 十二、最终回复格式

先给结论，再给简洁证据：

### 结论

- 本轮是否完成；
- 是否通过验收；
- 若未通过，列出 P0/P1。

### 实际修改

- 修改文件清单；
- 条件文件修改与否及原因；
- 明确未修改的关键文件。

### 自动化验证

用表格列出每条测试命令、退出结果和必要说明。区分本轮失败与修改前基线失败。

### 样本验收

- 简单样本结果；
- 智慧停车区结果；
- 21 个页面落点；
- 五个业务闭环；
- Design 遗漏；
- 未授权新增；
- draw.io/SVG。

### 遗留项

只列真正需要用户判断的高影响事项或已知 P2。

### Git 状态

明确说明：

- 未提交；
- 未推送；
- 当前工作区有哪些变更。

不要只汇报“测试通过”。最终结果的核心是：新 PRD 是否正确、完整、可读、可执行，并且没有改变 Design 事实。

---
