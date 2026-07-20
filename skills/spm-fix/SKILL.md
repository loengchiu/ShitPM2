---
name: spm-fix
description: "同步修复——vNext：把变更影响沿链路传播到当前真相。用于用户说同步修复、fix、修复传播、回写上游、一致性修复时，或 review 结论建议回上游修复、跨阶段一致性需要同步时。按 fix-propagation-rules.md 的传播矩阵逐层覆盖，不整篇重写，不自动推进阶段，不自动确认 Design，不自动生成所有下游。"
---
## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## vNext 职责定位

- **高影响 Fix 必须回写 Design**：业务流程、权限、状态、模块边界、跨系统责任等高影响产品事实变更必须先改 design.md
- **Design 修改后旧确认立即失效**：调用 design-confirmation.py check 会发现哈希不一致
- **不自动确认 Design**：仅告知用户运行 `design-confirmation.py confirm` 重新确认
- **不自动生成所有下游**：用户重新确认后才按需重新生成 PRD 或 Prototype
- **纯格式/措辞/排版/视觉表达修复**：可以只改对应下游，不触发 Design 失效
- **无法判断影响范围时**：按高影响变化处理，先回写 Design

## 最小读取集合

**一次读取**——用一次工具调用读取以下全部文件：

1. `.workflow/status.json`（当前阶段和产物路径，兼容旧字段读取）
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

| 类别 | 判断标准 | 归属层 | 事实源文件 | 是否触发 Design 确认失效 |
|------|---------|--------|-----------|----------------------|
| 目标/范围/建设方式 | 涉及一期做什么、不做什么 | 对齐层 | `output/align/align.md` | 否（但若 align 改了，下游 design 应同步审视） |
| 模块/页面/字段/规则 | 涉及数据结构或业务规则定义 | 设计层 | `output/design/design.md` | 是 |
| 流程/状态/权限 | 涉及状态机、权限矩阵、审批流 | 设计层 | `output/design/design.md` | 是 |
| 跨系统责任/异常路径 | 涉及系统边界或异常处理 | 设计层 | `output/design/design.md` | 是 |
| 表现层布局/样式/视觉 | 仅涉及 UI 呈现，不涉及语义 | 原型层 | `output/prototype/index.html`（及 `pages/` 目录，若存在） | 否 |
| 文案/措辞/格式 | 纯文字修改不涉及语义 | PRD 或 Prototype 对应层 | `output/prd/prd.md` 或 `output/prototype/` | 否 |

**vNext 高影响判定原则**：无法判断影响范围时，按高影响变化处理，归入设计层。

**CHECKPOINT · 归属层确认**——若修改指令同时涉及多层（如"新增字段并在页面展示"），必须拆分为多步逐层修复，不混在一层改。

**CHECKPOINT · 阶段一致性校**——对比修改归属层与 `status.json` 的 `actual_stage` 或 `current_stage`（vNext 优先读 actual_stage）：
- 归属层对应的阶段 > 实际阶段 → 警告用户"当前项目尚未进入该阶段"，建议先推进，不直接修复
- 归属层对应的阶段 < 实际阶段 → 允许修复，但提示"修改上游可能影响下游已有产物"
- 实际阶段为 `fix` 或 `done` → 从 `artifacts` 字段推断实际最远阶段，按上述规则判断

阶段映射：align → design → (prd ∥ prototype)。review 子阶段等于对应主阶段。vNext 中 prd 与 prototype 并列，不分先后。

### 步骤 3：读取传播矩阵，确定影响范围

读取 `contracts/fix-propagation-rules.md`，按传播矩阵列出所有受影响的产物文件：

| 修改层 | 必须更新 | 需检查是否更新 | 触发 Design 确认失效 |
|--------|---------|---------------|--------------------|
| 对齐层 | `output/align/align.md` → `output/design/design.md` | `output/prd/prd.md`、`output/prototype/index.html`（及 `pages/`，若存在） | 否（design 改了才触发） |
| 设计层 | `output/design/design.md` | `output/prd/prd.md`、`output/prototype/index.html`（及 `pages/`，若存在） | 是 |
| 原型层 | `output/prototype/index.html`（及 `pages/`，若存在） | 无下游 | 否 |

输出格式（必须逐行列出）：

```
受影响产物清单：
1. [文件路径] — 需要更新（原因：字段定义变更）
2. [文件路径] — 需要检查（原因：可能引用了旧字段名）
3. [文件路径] — 无需更新（原因：不涉及该字段）
触发 Design 确认失效：是/否
```

**CHECKPOINT · 影响范围确认**——列出全部受影响文件后，停下等用户确认再执行修复。不跳过此确认直接改文件。

### 步骤 4：按顺序执行修复

修复顺序严格遵守：**事实源层 → 下游层**（先改 design 再改 prd/prototype，先改 align 再改 design）。

每层修复动作：

1. 打开事实源文件（如 `output/design/design.md`）
2. 定位受影响的段落/表格/章节（不整篇重写）
3. 执行局部修改：替换字段名、新增行、删除行、更新枚举值
4. 验证修改后章节内引用一致性（如字段名在同一文件其他章节的引用是否同步更新）

**CHECKPOINT · 单层修复完成**——每完成一层修复后，输出修改摘要（改了哪些段落、改了什么），再继续下一层。

### 步骤 5：一致性校验（vNext：基于人读稿，不依赖 metadata）

修复涉及 design/PRD/prototype 层时，运行基于人读稿的一致性校验：

```bash
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .
```

vNext 不再运行 `verify-against-metadata.py`（标记为 legacy）。校验未通过 → 回到步骤 4 修复。

若旧项目存在 metadata 且用户希望执行 legacy 一致性校验，可显式调用：

```bash
python $BUNDLE/scripts/python/verify-against-metadata.py --stage design --project-root .
```

但 legacy 校验结果不作为新流程硬门禁，仅作为参考。

### 步骤 6：Design 确认失效处理（vNext 新增）

若步骤 4 修改了 `output/design/design.md`（设计层或对齐层波及 design）：

1. 提示用户当前 Design 已被修改，旧确认立即失效：
   ```
   Design 已修改，旧确认标记失效。
   请重新确认当前 Design：
   python $BUNDLE/scripts/python/design-confirmation.py confirm --project-root .
   ```

2. 不自动调用 `design-confirmation.py confirm`
3. 不自动重新生成 PRD 或 Prototype
4. 用户重新确认后，由用户显式触发 spm-prd 或 spm-prototype 重新生成

若仅修改了 PRD 或 Prototype（纯格式/措辞/排版/视觉表达修复），不触发 Design 确认失效，跳过本步。

### 步骤 7：修复后输出

输出修复摘要，格式固定：

```
修复摘要：
- 修改文件：[文件1路径]、[文件2路径]
- 修改内容：[一句话概括]
- Design 确认状态：[未失效 / 已失效，需重新确认]
- 下游影响：[哪些下游产物需要后续同步]
- 建议操作：
  - 若 Design 已修改：建议运行 design-confirmation.py confirm 重新确认，再按需运行 spm-prd / spm-prototype
  - 若仅改下游：建议重新执行对应阶段 review
```

不自动执行 review，不自动推进阶段，不自动重新生成 metadata，不自动确认 Design。

## 失败模式

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|---------|---------|-----------|
| 传播矩阵文件缺失 | `contracts/fix-propagation-rules.md` 不存在 | 按默认传播规则执行：设计层→prd+prototype，对齐层→design+prd+prototype | 停下告知用户，要求手动提供传播规则 |
| 归属层无法判断 | 修改指令模糊，同时涉及多层 | 追问用户确认归属层 | 用户也无法确认时，按最保守策略：从最上游层开始修，按高影响变化处理 |
| 事实源文件不存在 | `output/design/design.md` 不存在 | 检查 `output/align/align.md` 是否存在，如存在则当前项目尚未进入设计阶段 | 停下告知用户当前项目状态不支持此修复 |
| 修复导致下游引用断裂 | 改了字段名但下游 prd 仍在引用旧名 | 自动同步更新下游文件中的旧引用 | 如下游文件结构复杂无法自动同步，列出所有断裂点让用户手动修复 |
| fix-propagation-rules.md 中无对应规则 | 修改类型不在传播矩阵中 | 按最保守策略：从最上游层开始修 | 停下告知用户此修改类型未定义传播规则 |
| Design 已修改但用户跳过重新确认 | 用户未运行 design-confirmation.py confirm 就触发下游生成 | 下游 Skill 启动时会通过 design-confirmation.py check 检测到哈希不一致，阻止生成 | 不绕过，强制要求用户先确认 |

## 硬规则

1. 只改必要内容，不整篇重写——定位到受影响的段落/表格/章节后局部修改
2. 覆盖式更新（当前真相原则），不制造多版本并存
3. 覆盖范围仅限人读物
4. 不允许逆向定源（PRD/Prototype 不能直接改 design 的语义）
5. 若无法判断归属层，先停在澄清，不得直接改下游
6. 设计是唯一事实源——字段、权限、状态的完整定义只在 design 中
7. 修复后不自动推进阶段
8. 高影响 Fix（业务流程、权限、状态、模块边界、跨系统责任）必须先回写 Design
9. Design 修改后必须告知用户重新确认，不自动调用 confirm
10. 不自动重新生成所有下游（PRD/Prototype 由用户显式触发）
11. 无法判断影响范围时，按高影响变化处理
12. 不运行 stage-prep.py 生成 metadata（vNext 不再默认生成 metadata）

## 批量修改执行规范

涉及 2 处及以上修改时，用 js 工具一次性完成：列变更清单 → 单个脚本读取/替换/写入 → 抽查校验。

## 不要做什么

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|--------|------------|---------|
| 1 | 整篇重写人读稿 | 破坏未变更内容，引入回归风险 | 只改受影响的段落/表格/章节 |
| 2 | 修改 Design 后不提示重新确认 | 下游会基于过期 Design 生成，导致不一致 | 步骤 6 必须提示用户运行 design-confirmation.py confirm |
| 3 | 自动确认 Design | 用户可能需要验证修改结果 | 仅告知用户重新确认，不自动调用 confirm |
| 4 | 自动重新生成所有下游 | 用户可能只想先修 Design，后续再决定是否同步下游 | 等用户重新确认后由用户显式触发 spm-prd / spm-prototype |
| 5 | 跳过传播矩阵直接改下游 | 可能漏改关联产物，导致不一致 | 先读 `fix-propagation-rules.md`，按矩阵逐层修复 |
| 6 | 逆向定源（PRD/Prototype 改 design 语义） | 破坏"设计是唯一事实源"原则 | 只改事实源层，下游镜像同步 |
| 7 | 发现上游 bug 顺手修 | 修复范围失控，可能引入新问题 | 停下报告用户，等用户决定是否修上游 |
| 8 | 修复后自动推进阶段 | 用户可能需要验证修复结果 | 输出修复摘要，等用户手动触发 review |
| 9 | 修改 review 结论文件 | review 结论是只读的，修正需重新 review | 不碰 `.workflow/reviews/` 下的文件 |
| 10 | 无影响分析直接改文件 | 可能漏改关联产物 | 先完成步骤 3 影响分析，列出清单确认后再改 |
| 11 | 把下游意见直接提升为 Design 事实 | 破坏 Design 唯一事实源地位 | 下游意见须由用户决策后通过 Fix 回写 Design |
| 12 | 高影响 Fix 只停留在 PRD 或 Prototype | 下游不能承载高影响产品事实 | 高影响必须回写 Design 并使旧确认失效 |
