# 生成 PRD 时分片读取 Design：优化执行与验收计划

> 日期：2026-08-05
> 执行对象：其他 AI
> 编制依据：审计系统真实产物暴露的上下文爆炸问题——生成 PRD 时一次性全读 4565 行 / 325KB 的 design.md，小上下文模型爆栈后产生幻觉，PRD 字段定义章节全缺、52 个页面两行式、"刷新页面重试"重复 122 次
> 目标：让"生成 PRD 时按模块读 Design 片段"从口头指令变成可执行、可验证的确定性行为

## 1. 结论

分片读 Design **早已设计**（spm-prd SKILL 阶段 A"只读导航九项，不保留全部页面正文"+ 阶段 C"只重新读取当前模块对应的 Design 片段"），但审计系统 PRD 生成时**一次性全读了 SKILL + rules + design.md**，因为：

1. **没有"按模块提取 design.md 片段"的工具**——SKILL 说"只读片段"但没给"怎么读"的可执行方式，模型只能自己 grep/sed 定位 325KB 文件，必然失控；
2. **小上下文模型适配不足**——即使分片，SKILL + rules + scene + template 基线（约 770 行）+ context-pack 模块装载（443 行 / 6454 tokens）+ Design 片段，对 8k/16k 模型仍偏紧；
3. **没有"禁止一次性全读 design.md"的确定性约束**——全读不发生任何错误，只是悄悄爆上下文。

本轮目标：扩展上下文装载工具支持"按模块装载 Design 片段"，SKILL 明确"用命令读片段、禁止一次性全读 design.md"，阶段 A 大 Design 时读索引不读正文。不新增检查器/门禁/回执/覆盖率文件。

## 2. 真实项目暴露的问题

### 2.1 实证数据（`D:\work\交投软件中心\审计系统`）

| 项 | 数据 |
|---|---|
| design.md 规模 | 4565 行 / 325KB / 279 个 `###` 页面区块标题 |
| PRD 生成方式 | 一次性全读 SKILL + rules + design.md（上下文爆炸） |
| PRD 结果 | 字段定义章节全缺（"字段定义" 0 命中）；52 个页面两行式；"刷新页面重试"×122；"待确认"仅 2 次 |
| design.md 结构 | 按业务闭环组织（四、闭环一~九）+ 页面清单 + `### 页面：xxx`（可按模块切） |

### 2.2 根因链

```text
SKILL 说"只读当前模块 Design 片段"（口头指令）
  → 没有工具按模块提取片段（模型只能自己 grep/sed 定位 325KB 文件）
  → 模型失控，退化为一次性全读 SKILL+rules+design.md
  → 小上下文模型爆栈
  → 幻觉 + 偷工减料（字段定义没写、页面只两行、重复文案凑数）
  → 没有任何确定性约束拦住"全读"这个行为
```

### 2.3 与既有设计的关系

- 阶段 A"只读导航九项，不保留全部页面正文"——设计正确，但"导航九项"也需要读 design.md 的相当篇幅（页面清单、核心对象、状态、权限），大 Design 时仍多；
- 阶段 C"只重新读取当前模块对应的 Design 片段"——设计正确，但"怎么读"没有工具支撑；
- `design-index.py` 已能解析 design.md 成结构化实体（页面/字段/状态），但目前只服务 `prd-consistency-check` 的一致性对比，没有作为"分片读"的入口；
- `context-pack.py` 已做编译式装载（rules/scene 按 pass 装载），但目前只装仓库规则，不装项目产物（design.md 片段）。

## 3. 目标行为

生成 PRD 时读 Design 的方式：

1. **阶段 A（全局扫描）**：Design 较小时读 design.md 导航层（页面清单、核心对象、状态、权限、闭环清单、待确认）；**Design 超过阈值时，先读 `design-index.py` 生成的结构化索引**（页面清单 + 核心对象 + 状态 + 权限的精简视图），不读 design.md 正文；
2. **阶段 C（模块写作）**：**禁止一次性全读 design.md**；必须用命令按模块提取片段：
   ```text
   python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass module --card scenes --module <模块名>
   ```
   一次输出：模块写作规则 + 场景自检清单 + **该模块的 Design 片段**（对应闭环章节 + 该闭环涉及的页面章节 + 共用的业务对象/权限相关部分）；
3. **阶段 D（整合/验收）**：按需读已完成模块的片段，不全读。

确定性约束（程序可判断）：
- `context-pack.py --module` 提取的片段行数远小于 design.md 全文（可设阈值，如 ≤ 全文 1/3）；
- 阶段 C 未提供 `--module` 时，不宣称该模块按分片流程完成；
- SKILL 明确"一次性全读 design.md（sed 1,$p 或等效）视为违反分片流程"。

## 4. 修改范围

### 4.1 必改文件

| 文件 | 修改目标 |
|---|---|
| `scripts/python/context-pack.py` | 扩展支持 `--module <模块名>`（或 `--closure`/`--pages`）：从 `--project-root/output/design/design.md` 提取该模块对应片段（闭环章节 + 相关页面章节 + 共用业务对象/权限部分），与 rules/scene 一起输出；片段超阈值时截断或报错 |
| `skills/spm-prd/SKILL.md` | 阶段 A 补"大 Design 时先读 design-index 索引"；阶段 C 补"禁止一次性全读 design.md，必须用 `--module` 命令读片段"；模块上下文命令补 `--module <模块名>` 参数 |
| `references/prd-writing-rules.md` | 补"生成 PRD 时 Design 按模块分片读取"的规则段（与全量分片写作对应） |
| `references/prd-scene-checklist.md` | 模块自检加"当前模块 Design 片段已通过 `--module` 命令装载，未一次性全读 design.md" |
| `contracts/prd-review-checklist.md` | 加"Design 全读痕迹"检查项（如动作/字段与模块无关章节混入、上下文爆栈典型症状：字段定义全缺/页面两行式/重复文案） |

### 4.2 按实际影响同步

| 文件 | 处理方式 |
|---|---|
| `contracts/context-loading.manifest.json` | 仅当 `--module` 装载逻辑需要 manifest 声明（如 design.md 路径/章节锚点）时才补最小配置 |
| `scripts/python/design-index.py` | 如现有索引无法输出"导航视图"（页面清单/核心对象/状态/权限精简版），补一个 `--nav` 或 `--fragment <模块>` 输出；不重复造解析逻辑 |
| `scripts/python/test-context-loading.py` / `test-prd-simplification.py` | 补 `--module` 提取片段的确定性测试（片段非空、远小于全文、含目标模块内容、不含无关模块内容） |
| `USAGE.md` / 相关文档 | 仅当描述旧流程时同步 |

### 4.3 禁止修改

- 用户正式项目 `output/design/design.md`、`output/prd/prd.md`、Design confirmation（审计系统 PRD 的重生成需用户另行决定）；
- 历史计划/报告；
- Prototype Skill、Design Skill 或其他无关 skill；
- 不得新增检查器、门禁、回执、覆盖率 JSON、承接矩阵或机器签名；
- 不得执行 Git commit / push。

## 5. 具体规则要求（草案）

### 5.1 context-pack.py 扩展（核心）

新增 `--module <模块名>` 参数（与 `--pass module --card scenes` 组合）：

```text
输入：--project-root 下的 output/design/design.md + 模块名
提取逻辑（确定性，不依赖语义判断）：
  1. 按标题匹配 design.md 的闭环章节（如"### 闭环X：<模块名>"或含模块名的闭环标题）；
  2. 提取该闭环章节全文；
  3. 提取该闭环涉及的页面章节（闭环正文引用的页面名 → 对应"### 页面：<页面名>"章节）；
  4. 提取共用的业务对象/权限相关部分（闭环涉及的核心对象、角色）；
  5. 与 rules/scene 一起按既有 pack 格式输出；
  6. 片段行数 > 阈值（默认 design.md 全文 1/3）时截断并标注，或报错提示模块边界过大需拆分。
兜底：
  - 模块名匹配不到闭环时，按页面名模糊匹配（模块名 ≈ 页面名/对象名）；
  - 匹配不到任何章节时报错并列出 design.md 的闭环/页面标题清单，不静默返回空。
```

设计边界：提取按**标题锚点**切分（design.md 有 `### 闭环X：`、`### 页面：X`、`## 五/六` 等稳定标题），不做语义相似度检索，不做内容摘要压缩——输出的是 design.md 原文片段，不是 AI 概括。

### 5.2 SKILL 阶段 A/C 指令补强

阶段 A 补：

```text
Design 超过阈值（默认约 1000 行）时，先运行 design-index 生成结构化索引（页面清单 + 核心对象 + 状态 + 权限精简视图），以索引为导航，不一次性读 design.md 正文；Design 未超阈值时可读正文导航层。
```

阶段 C 补：

```text
禁止一次性全读 design.md（如 sed 1,$p、全文粘贴或等效行为）。必须用 `--module <模块名>` 命令装载当前模块的 Design 片段；片段不得包含无关模块内容。模块边界过大（片段超阈值）时，先按子闭环/页面拆分模块再分片。
```

### 5.3 Review 检查（识别"全读爆栈"产物）

prd-review-checklist 加"上下文爆栈典型症状"检查（供 Review 识别，非脚本门禁）：

```text
- 字段定义章节是否整体缺失；
- 页面是否只有"职责 + 业务阶段"两行（无区块、无字段、无展示行为、无动作展开）；
- 是否出现大面积机械重复文案（同一失败/恢复话术重复 N 次）；
- 待确认事项是否异常稀少（高影响未知被静默拍板）。
命中多项时提示：疑似生成时一次性全读 design.md 导致上下文爆栈，应按分片流程重新生成受影响模块。
```

## 6. 验收方案

### 6.1 静态同步验收

- SKILL 阶段 A/C 含"读索引/禁止全读/`--module` 命令"指令；
- context-pack.py `--module` 可运行；
- rules/scene/Review 有对应段落；
- 现有测试全绿。

### 6.2 功能验收（确定性）

构造 design.md 样本（多闭环、多页面、含共用对象），验证：

1. `--module <闭环名>` 输出片段非空、含目标闭环内容、不含无关闭环内容；
2. 片段行数 ≤ design.md 全文 1/3（大 Design 场景显著小于全文）；
3. 模块名匹配不到时返回标题清单报错，不静默返回空；
4. 大 design.md（如模拟 4000+ 行）时片段仍可控；
5. 与 `--pass module --card scenes` 组合时输出包含规则 + 清单 + 片段三部分。

### 6.3 上下文预算验收（小上下文模拟）

- 记录"SKILL + rules + scene + template + design-index 索引 + 单模块片段"的总 token 估算，对照 8k/16k/32k 预算给出可装载性结论；
- 验证"单模块片段"装载后剩余预算足以支撑模块写作。

### 6.4 真实项目回归（副本）

- 使用审计系统副本（禁止改正式项目），按分片流程重新生成受影响模块（如底稿作业），验证：
  - 生成过程未一次性全读 design.md（以 `--module` 命令痕迹为准）；
  - 重新生成的模块有字段定义章节、页面非两行式、无大面积重复文案；
  - 对比旧 PRD 同模块，字段/动作/页面展开度提升可回读。

### 6.5 现有测试验收

至少运行：test-context-loading、test-prd-simplification、test-prd-style-lint、test-prd-consistency-semantics、test-design-simplification、test-design-index、test-shitpm-regression、test-resource-integrity。

结果处理：本轮引起的失败必须修复；无关既有失败单独报告；不以退出码代替真实 PRD 人工回读。

## 7. 总体验收标准

全部满足才可宣布完成：

1. `--module` 提取片段确定性可用（非空/远小于全文/含目标模块/不含无关模块）；
2. SKILL 阶段 A/C 含"读索引/禁止全读/用 `--module`"指令；
3. 无"一次性全读 design.md"的合法路径（SKILL 明确禁止）；
4. 审计系统副本重生成受影响模块后：字段定义章节存在、页面非两行式、重复文案消失、生成过程走 `--module` 分片；
5. 未新增检查器/门禁/回执/覆盖率文件；
6. 未修改用户正式项目、未执行 commit/push；
7. 测试全绿。

## 8. 执行 AI 最终报告格式

```text
一、结论
- 通过 / 有问题需修改 / 阻塞

二、实际修改文件
- 文件：修改目的：

三、功能验收
- --module 提取（非空/远小于全文/含目标模块/不含无关模块）：
- 匹配不到时行为：
- 大 design.md 场景：

四、上下文预算
- 基线装载 token 估算：
- 单模块片段装载 token 估算：
- 8k/16k/32k 可装载性结论：

五、真实项目回归（副本）
- 分片执行痕迹：
- 字段定义章节：
- 页面展开度：
- 重复文案：

六、自动化结果
- 测试清单与结果：

七、未解决问题与待确认事项

八、Git 状态
- 工作区；未执行 commit/push 说明
```

## 9. 停止条件

1. design.md 无稳定标题锚点可切（如闭环/页面标题不规范）——停止，先修 Design 结构规范，不强行用语义检索；
2. `--module` 提取需要语义判断才能准确定位模块边界——停止，说明该模块边界需人工确认，不用工具硬切；
3. 片段仍超小上下文预算——停止，报告需进一步拆分模块或精简基线装载；
4. 补分片读需要新增检查器/门禁/回执——停止，报告，不越界。

## 10. 禁止重新引入的复杂度

- 不新增"Design 全读检测器"、上下文用量监控、回执链或机器签名；
- 不把"读 Design 片段"拆成新的编排阶段或任务节点；
- 不要求生成"分片装载证明 JSON"；
- `--module` 提取只做确定性标题切分，不做语义相似度检索、不做 AI 摘要压缩；
- 分片读是读写方式（工具 + SKILL 指令），不是新检查流程。
