---
name: spm-fix
description: "同步修复——把变更影响沿链路传播到当前真相。用于用户说同步修复、fix、修复传播、回写上游、一致性修复时，或 review 结论建议回上游修复、跨阶段一致性需要同步时。按 fix-propagation-rules.md 的传播矩阵逐层覆盖，不整篇重写，不自动推进阶段。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 最小读取集合

**一次读取**——用一次工具调用读取以下全部文件：

1. `.workflow/status.json`（当前阶段和产物路径）
2. 用户修改指令（原始文本）
3. 当前阶段人读稿（如 `output/design/design.md`）
4. `contracts/fix-propagation-rules.md`（传播矩阵定义）

## 执行顺序

### 步骤 1：接收并解析修改指令

读取用户修改指令，拆解为两个要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| 改什么 | 具体字段/页面/规则/目标 | "审计类型字段" |
| 改成什么 | 变更后的状态 | "枚举值增加'专项审计'" |

**CHECKPOINT · 指令完整性**——修改指令是否同时包含「改什么」和「改成什么」？缺少任一项时，停下追问用户，不猜测、不推断、不补全。

### 步骤 2：定位修改对象的归属层

按以下分类表定位修改对象属于哪一层：

| 类别 | 判断标准 | 归属层 | 事实源文件 |
|------|---------|--------|-----------|
| 目标/范围/建设方式 | 涉及一期做什么、不做什么 | 对齐层 | `output/align/align.md` |
| 模块/页面/字段/规则 | 涉及数据结构或业务规则定义 | 设计层 | `output/design/design.md` |
| 流程/状态/权限 | 涉及状态机、权限矩阵、审批流 | 设计层 | `output/design/design.md` |
| 表现层布局/样式/视觉 | 仅涉及 UI 呈现，不涉及语义 | 原型层 | `output/prototype/index.html`（及 `pages/` 目录，若存在） |

**CHECKPOINT · 归属层确认**——若修改指令同时涉及多层（如"新增字段并在页面展示"），必须拆分为多步逐层修复，不混在一层改。

**CHECKPOINT · 阶段一致性校验**——对比修改归属层与 `status.json` 的 `current_stage`：
- 归属层对应的阶段 > `current_stage` → 警告用户"当前项目尚未进入该阶段"，建议先推进，不直接修复
- 归属层对应的阶段 < `current_stage` → 允许修复，但提示"修改上游可能影响下游已有产物"
- `current_stage` 为 `fix` 或 `done` → 从 `artifacts` 字段推断实际最远阶段，按上述规则判断

阶段映射：align → design → prd → prototype。review 子阶段等于对应主阶段。

### 步骤 3：读取传播矩阵，确定影响范围

读取 `contracts/fix-propagation-rules.md`，按传播矩阵列出所有受影响的产物文件：

| 修改层 | 必须更新 | 需检查是否更新 |
|--------|---------|---------------|
| 对齐层 | `output/align/align.md` → `output/design/design.md` | `output/prd/prd.md`、`output/prototype/index.html`（及 `pages/`，若存在） |
| 设计层 | `output/design/design.md` | `output/prd/prd.md`、`output/prototype/index.html`（及 `pages/`，若存在） |
| 原型层 | `output/prototype/index.html`（及 `pages/`，若存在） | 无下游 |

输出格式（必须逐行列出）：

```
受影响产物清单：
1. [文件路径] — 需要更新（原因：字段定义变更）
2. [文件路径] — 需要检查（原因：可能引用了旧字段名）
3. [文件路径] — 无需更新（原因：不涉及该字段）
```

**CHECKPOINT · 影响范围确认**——列出全部受影响文件后，停下等用户确认再执行修复。不跳过此确认直接改文件。

### 步骤 4：按顺序执行修复

修复顺序严格遵守：**事实源层 → 下游层**（先改 design 再改 prd，先改 align 再改 design）。

每层修复动作：

1. 打开事实源文件（如 `output/design/design.md`）
2. 定位受影响的段落/表格/章节（不整篇重写）
3. 执行局部修改：替换字段名、新增行、删除行、更新枚举值
4. 验证修改后章节内引用一致性（如字段名在同一文件其他章节的引用是否同步更新）

**CHECKPOINT · 单层修复完成**——每完成一层修复后，输出修改摘要（改了哪些段落、改了什么），再继续下一层。

### 步骤 5：一致性校验

修复涉及 design/PRD/prototype 层时，运行一致性校验：

```bash
python $BUNDLE/scripts/python/verify-against-metadata.py --stage design --project-root .
```

校验未通过（schema 校验失败或 ID 唯一性问题）→ 回到步骤 4 修复。

### 步骤 6：修复后输出

输出修复摘要，格式固定：

```
修复摘要：
- 修改文件：[文件1路径]、[文件2路径]
- 修改内容：[一句话概括]
- 下游影响：[哪些下游产物需要后续同步]
- 建议操作：建议重新执行 /spm-design-review（或对应阶段 review）
```

不自动执行 review，不自动推进阶段。review 通过后 metadata 由 `scripts/python/stage-prep.py` 脚本自动重新生成。

## 失败模式

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|---------|---------|-----------|
| 传播矩阵文件缺失 | `contracts/fix-propagation-rules.md` 不存在 | 按默认传播规则执行：设计层→prd+prototype，对齐层→design+prd+prototype | 停下告知用户，要求手动提供传播规则 |
| 归属层无法判断 | 修改指令模糊，同时涉及多层 | 追问用户确认归属层 | 用户也无法确认时，按最保守策略：从最上游层开始修 |
| 事实源文件不存在 | `output/design/design.md` 不存在 | 检查 `output/align/align.md` 是否存在，如存在则当前项目尚未进入设计阶段 | 停下告知用户当前项目状态不支持此修复 |
| 修复导致下游引用断裂 | 改了字段名但下游 prd 仍在引用旧名 | 自动同步更新下游文件中的旧引用 | 如下游文件结构复杂无法自动同步，列出所有断裂点让用户手动修复 |
| fix-propagation-rules.md 中无对应规则 | 修改类型不在传播矩阵中 | 按最保守策略：从最上游层开始修 | 停下告知用户此修改类型未定义传播规则 |
| metadata 文件存在但人读稿已改 | 人读稿已更新但 metadata 未同步 | 告知用户 metadata 将在下次 review 通过后自动重新生成 | 不手动修改 metadata |

## 硬规则

1. 只改必要内容，不整篇重写——定位到受影响的段落/表格/章节后局部修改
2. 覆盖式更新（当前真相原则），不制造多版本并存
3. 覆盖范围仅限人读物；机读物在下次 review 通过后由脚本重新生成
4. 不允许逆向定源（PRD 不能直接改 design 的语义）
5. 若无法判断归属层，先停在澄清，不得直接改下游
6. 设计是唯一事实源——字段、权限、状态的完整定义只在 design 中
7. 修复后不自动推进阶段
8. 不手动修改 metadata（机读物由 review 通过后 `scripts/python/stage-prep.py` 脚本自动生成）

## 批量修改执行规范

涉及 2 处及以上修改时，用 js 工具一次性完成：列变更清单 → 单个脚本读取/替换/写入 → 抽查校验。

## 不要做什么

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|--------|------------|---------|
| 1 | 整篇重写人读稿 | 破坏未变更内容，引入回归风险 | 只改受影响的段落/表格/章节 |
| 2 | 同时修改人读稿和 metadata | metadata 应由 review 通过后脚本自动生成 | 只改人读稿，metadata 留给 `stage-prep.py` |
| 3 | 跳过传播矩阵直接改下游 | 可能漏改关联产物，导致不一致 | 先读 `fix-propagation-rules.md`，按矩阵逐层修复 |
| 4 | 逆向定源（PRD 改 design 语义） | 破坏"设计是唯一事实源"原则 | 只改事实源层，下游镜像同步 |
| 5 | 发现上游 bug 顺手修 | 修复范围失控，可能引入新问题 | 停下报告用户，等用户决定是否修上游 |
| 6 | 修复后自动推进阶段 | 用户可能需要验证修复结果 | 输出修复摘要，等用户手动触发 review |
| 7 | 修改 review 结论文件 | review 结论是只读的，修正需重新 review | 不碰 `.workflow/reviews/` 下的文件 |
| 8 | 无影响分析直接改文件 | 可能漏改关联产物 | 先完成步骤 3 影响分析，列出清单确认后再改 |
