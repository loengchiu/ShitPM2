---
name: spm-fix
description: "同步修复——vNext：把变更影响沿链路传播到当前真相。用于用户说同步修复、fix、修复传播、回写上游、一致性修复时，或 review 结论建议回上游修复、跨阶段一致性需要同步时。按 fix-propagation-rules.md 的传播矩阵逐层覆盖，不整篇重写，不自动推进阶段，不自动确认 Design，不自动生成所有下游。"
---

## 路径解析

从系统 prompt 的 `<!-- SHITPM GLOBAL RULES START -->` 段读取 `ShitPM bundle root:` 的值，记为 `$BUNDLE`。

- `scripts/python/`、`references/`、`templates/`、`contracts/`、`lib/` 开头 → `$BUNDLE/` 下
- `.workflow/`、`output/` 开头 → 当前项目根目录下

## 模型建议（运行时输出）

流程开始时输出模型等级和推理深度建议（直接复用 PRD §6.3 推荐矩阵）：

- **根据变更影响判断**
- **轻量模型**：修改范围、正确结果和受影响位置都已明确
- **深度推理模型**：需要判断影响范围、跨模块关系或方案取舍时；无法判断时使用深度推理模型

建议必须是实际运行输出，不只是背景说明。

## vNext 职责定位

- **Design 是唯一高影响产品事实源**：高影响 Fix 必须回写 Design
- **按实际存在的下游分支修复**：不要求 PRD 和 Prototype 同时存在
- **仅在 PRD 存在时运行 PRD consistency checker**；Prototype-only 项目必须有合法验证路径
- **Design 修改后旧确认立即失效**（哈希自动不一致），并提示用户重新确认
- **不自动确认 Design**：仅告知用户运行 `design-confirmation.py confirm` 重新确认
- **不自动生成所有下游**：用户重新确认后才按需重新生成 PRD 或 Prototype
- **纯格式/措辞/排版/视觉表达修复**：可以只改对应下游，不触发 Design 失效
- **无法判断影响范围时**：按高影响变化处理，先回写 Design

## 输入事实源

读取以下文件：

1. `.workflow/status.json`（当前阶段和产物路径，兼容旧字段读取）
2. 用户修改指令（原始文本）
3. 当前阶段人读稿（如 `output/design/design.md`）
4. `contracts/fix-propagation-rules.md`（传播矩阵定义）

## 修复流程

### 步骤 1：接收并解析修改指令

读取用户修改指令，拆解为两个要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| 改什么 | 具体字段/页面/规则/目标 | "审计类型字段" |
| 改成什么 | 变更后的状态 | "枚举值增加'专项审计'" |

修改指令缺少"改什么"或"改成什么"时，停下追问用户，不猜测、不推断、不补全。

### 步骤 2：定位修改对象的归属层

按以下分类表定位修改对象属于哪一层：

| 类别 | 判断标准 | 归属层 | 事实源文件 | 是否触发 Design 确认失效 |
|------|---------|--------|-----------|----------------------|
| 目标/范围/建设方式 | 涉及一期做什么、不做什么 | 设计层 | `output/design/design.md`（vNext：Design 是唯一事实源，目标/范围纳入 Design） | 是 |
| 模块/页面/字段/规则 | 涉及数据结构或业务规则定义 | 设计层 | `output/design/design.md` | 是 |
| 流程/状态/权限 | 涉及状态机、权限矩阵、审批流 | 设计层 | `output/design/design.md` | 是 |
| 跨系统责任/异常路径 | 涉及系统边界或异常处理 | 设计层 | `output/design/design.md` | 是 |
| 表现层布局/样式/视觉 | 仅涉及 UI 呈现，不涉及语义 | 原型层 | `output/prototype/index.html`（及 `pages/` 目录，若存在） | 否 |
| 文案/措辞/格式 | 纯文字修改不涉及语义 | PRD 或 Prototype 对应层 | `output/prd/prd.md` 或 `output/prototype/` | 否 |

**vNext 事实源原则**：Align 是可选输入参考，不是事实源。目标/范围/建设方式的事实源是 `output/design/design.md`，对齐稿 `output/align/align.md`（若存在）仅作为 Design 的输入参考。修改目标/范围必须回写 Design，不通过 Align 反向定源。

**vNext 高影响判定原则**：无法判断影响范围时，按高影响变化处理，归入设计层。

若修改指令同时涉及多层（如"新增字段并在页面展示"），必须拆分为多步逐层修复，不混在一层改。

### 步骤 3：读取传播矩阵，确定影响范围

读取 `contracts/fix-propagation-rules.md`，按传播矩阵列出所有受影响的产物文件。**vNext 时序：Fix 阶段只修复事实源层，下游重新生成由用户重新确认 Design 后显式触发 spm-prd / spm-prototype，不自动同步**。

| 修改层 | Fix 阶段必须更新（事实源层） | 下游处理（用户重新确认后由用户显式触发） | 触发 Design 确认失效 |
|--------|------------------------|---------------------------------------|--------------------|
| 对齐层 | `output/align/align.md` → `output/design/design.md` | spm-prd / spm-prototype（由用户显式触发，不自动同步） | 是（design.md 被修改） |
| 设计层 | `output/design/design.md` | spm-prd / spm-prototype（由用户显式触发，不自动同步） | 是 |
| 原型层（纯表现） | `output/prototype/index.html`（及 `pages/`，若存在） | 无下游 | 否 |
| PRD 纯文案 | `output/prd/prd.md` | 无下游 | 否 |

输出格式（必须逐行列出）：

```
受影响产物清单：
1. [文件路径] — Fix 阶段修复（原因：字段定义变更，事实源层）
2. [文件路径] — 用户重新确认后由用户显式触发 spm-prd/spm-prototype 重新生成（原因：下游镜像，不自动同步）
3. [文件路径] — 无需更新（原因：不涉及该字段）
触发 Design 确认失效：是/否
```

列出全部受影响文件后，停下等用户确认再执行修复。

### 步骤 4：修复事实源层（仅事实源，不修改下游）

vNext 强制时序：**修改事实源 → 旧确认失效 → 用户审阅并重新确认 Design → 用户显式触发下游重新生成**。Fix 阶段只负责修复事实源层，**不直接修改下游 PRD 或 Prototype**。

修复动作：

1. 打开事实源文件（如 `output/design/design.md`）
2. 定位受影响的段落/表格/章节（不整篇重写）
3. 执行局部修改：替换字段名、新增行、删除行、更新枚举值
4. 验证修改后章节内引用一致性（如字段名在同一文件其他章节的引用是否同步更新）

事实源定位规则：

| 修改归属层 | 事实源文件 | Fix 阶段是否修改下游 |
|-----------|-----------|-------------------|
| 对齐层 | `output/align/align.md` → `output/design/design.md` | 否（design.md 修改后立即停下，等用户重新确认） |
| 设计层 | `output/design/design.md` | 否（修改 design.md 后立即停下，等用户重新确认） |
| 原型层（纯表现） | `output/prototype/index.html`（及 `pages/`，若存在） | 是（直接改原型，无 Design 确认问题） |
| PRD 纯文案/措辞 | `output/prd/prd.md` | 是（直接改 PRD，无 Design 确认问题） |

完成事实源层修复后，输出修改摘要（改了哪些段落、改了什么），进入步骤 5。

### 步骤 5：Design 确认失效处理（vNext 强制时序，必须先于下游修改）

若步骤 4 修改了 `output/design/design.md`（设计层或对齐层波及 design）：

1. 提示用户当前 Design 已被修改，旧确认立即失效（哈希自动不一致）：
   ```
   Design 已修改，旧确认标记失效。
   请重新确认当前 Design：
   python $BUNDLE/scripts/python/design-confirmation.py --project-root . confirm

   重新确认后，如需同步下游产物，请由用户显式触发：
   - spm-prd：重新生成 PRD（基于新确认的 Design，走完整首次生成责任流程）
   - spm-prototype：重新生成 Prototype（基于新确认的 Design，走完整首次生成责任流程）
   ```

2. 不自动调用 `design-confirmation.py confirm`
3. **不修改下游 PRD 或 Prototype**——下游重新生成必须等用户重新确认后由用户显式触发 spm-prd / spm-prototype，走完整生成流程（含首次生成责任和语义自检），而不是由 Fix 内部局部修补
4. 跳到步骤 7 输出修复摘要，结束本次 Fix

若步骤 4 仅修改了 PRD 或 Prototype（纯格式/措辞/排版/视觉表达修复），不触发 Design 确认失效，继续步骤 6。

### 步骤 6：一致性校验（vNext：基于人读稿，不依赖 metadata）

仅当步骤 4 修改了 PRD（纯文案/措辞修复场景，PRD 是事实源）时运行：

```bash
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root .
```

校验未通过 → 回到步骤 4 修复。

**Prototype-only 项目必须有合法验证路径**：当 PRD 不存在但 Prototype 存在时，可通过以下方式验证：
- 用户手动在浏览器中打开原型验证修改正确性
- 调用 `/spm-prototype-review` 获取独立挑战
- 调用 `/spm-design-review` 验证 Design 修改

vNext 不再运行 `verify-against-metadata.py`（标记为 legacy）。若旧项目存在 metadata 且用户希望执行 legacy 一致性校验，可显式调用：

```bash
python $BUNDLE/scripts/python/verify-against-metadata.py --stage design --project-root .
```

但 legacy 校验结果不作为新流程硬门禁，仅作为参考。

### 步骤 7：修复后输出

输出修复摘要，格式固定：

```
修复摘要：
- 修改文件：[文件1路径]、[文件2路径]
- 修改内容：[一句话概括]
- Design 确认状态：[未失效 / 已失效，需重新确认]
- 下游影响：[哪些下游产物需要后续同步]
- 建议操作：
  - 若 Design 已修改：建议运行 python $BUNDLE/scripts/python/design-confirmation.py --project-root . confirm 重新确认；重新确认后由用户显式触发 spm-prd / spm-prototype 重新生成下游（Fix 不自动同步下游）
  - 若仅改下游：建议重新执行对应阶段 review
```

不自动执行 review，不自动推进阶段，不自动重新生成 metadata，不自动确认 Design，不自动同步下游。

## 失败模式

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|---------|---------|-----------|
| 传播矩阵文件缺失 | `contracts/fix-propagation-rules.md` 不存在 | 按默认传播规则执行：只修事实源层（design.md），下游由用户重新确认后显式触发 | 停下告知用户，要求手动提供传播规则 |
| 归属层无法判断 | 修改指令模糊，同时涉及多层 | 追问用户确认归属层 | 用户也无法确认时，按最保守策略：从最上游层开始修，按高影响变化处理 |
| 事实源文件不存在 | `output/design/design.md` 不存在 | 检查 `output/align/align.md` 是否存在，如存在则当前项目尚未进入设计阶段 | 停下告知用户当前项目状态不支持此修复 |
| fix-propagation-rules.md 中无对应规则 | 修改类型不在传播矩阵中 | 按最保守策略：从最上游层开始修 | 停下告知用户此修改类型未定义传播规则 |
| Design 已修改但用户跳过重新确认 | 用户未运行 design-confirmation.py confirm 就触发下游生成 | 下游 Skill 启动时会通过 design-confirmation.py check 检测到哈希不一致，阻止生成 | 不绕过，强制要求用户先确认 |
| 下游与 Design 不一致 | 用户重新确认后显式触发生成下游，但下游仍引用旧字段 | 由 spm-prd / spm-prototype 的首次生成责任流程处理（含 prd-consistency-check.py 自检） | 列出断裂点，由下游 Skill 在生成时修复 |

## 硬规则

1. 只改必要内容，不整篇重写——定位到受影响的段落/表格/章节后局部修改
2. 覆盖式更新（当前真相原则），不制造多版本并存
3. 覆盖范围仅限人读物
4. 不允许逆向定源（PRD/Prototype 不能直接改 design 的语义）
5. 若无法判断归属层，先停在澄清，不得直接改下游
6. **Design 是唯一高影响产品事实源**——字段、权限、状态、目标/范围的完整定义只在 design 中
7. 修复后不自动推进阶段
8. 高影响 Fix（业务流程、权限、状态、模块边界、跨系统责任、目标/范围）必须先回写 Design
9. Design 修改后必须告知用户重新确认，不自动调用 confirm
10. **Fix 阶段不修改下游 PRD 或 Prototype**——下游重新生成由用户重新确认 Design 后显式触发 spm-prd / spm-prototype（走完整首次生成责任流程）
11. 无法判断影响范围时，按高影响变化处理
12. 不运行 stage-prep.py 生成 metadata（vNext 不再默认生成 metadata）
13. **按实际存在的下游分支提示用户**——不要求 PRD 和 Prototype 同时存在；用户重新确认后按需触发其中之一或两者
14. **仅在步骤 4 修改了 PRD（纯文案/措辞修复场景）时运行 PRD consistency checker**；Prototype-only 项目必须有合法验证路径
15. 修改 design.md 后必须使旧确认失效（哈希自动不一致），并提示用户重新确认
16. 确认命令参数顺序固定为：`python $BUNDLE/scripts/python/design-confirmation.py --project-root . confirm`
17. **Align 不是事实源**——目标/范围/建设方式的事实源是 design.md，align.md 仅作为输入参考；不通过 Align 反向定源

## 不要做什么

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|--------|------------|---------|
| 1 | 整篇重写人读稿 | 破坏未变更内容，引入回归风险 | 只改受影响的段落/表格/章节 |
| 2 | 修改 Design 后不提示重新确认 | 下游会基于过期 Design 生成，导致不一致 | 步骤 5 必须提示用户运行 design-confirmation.py confirm |
| 3 | 自动确认 Design | 用户可能需要验证修改结果 | 仅告知用户重新确认，不自动调用 confirm |
| 4 | Fix 阶段直接修改下游 PRD 或 Prototype | 违反"修改 Design → 重新确认 → 用户显式触发下游"时序；下游应走完整首次生成责任流程 | 修改 design.md 后立即停下；用户重新确认后由用户显式触发 spm-prd / spm-prototype |
| 5 | 跳过传播矩阵直接改下游 | 可能漏改关联产物，导致不一致 | 先读 `fix-propagation-rules.md`，按矩阵定位事实源层 |
| 6 | 逆向定源（PRD/Prototype 改 design 语义） | 破坏"Design 是唯一高影响事实源"原则 | 只改事实源层；下游由用户重新确认后显式触发重新生成 |
| 7 | 发现上游 bug 顺手修 | 修复范围失控，可能引入新问题 | 停下报告用户，等用户决定是否修上游 |
| 8 | 修复后自动推进阶段 | 用户可能需要验证修复结果 | 输出修复摘要，等用户手动触发 review |
| 9 | 修改 review 结论文件 | review 结论是只读的，修正需重新 review | 不碰 `.workflow/reviews/` 下的文件 |
| 10 | 无影响分析直接改文件 | 可能漏改关联产物 | 先完成步骤 3 影响分析，列出清单确认后再改 |
| 11 | 把下游意见直接提升为 Design 事实 | 破坏 Design 唯一事实源地位 | 下游意见须由用户决策后通过 Fix 回写 Design |
| 12 | 高影响 Fix 只停留在 PRD 或 Prototype | 下游不能承载高影响产品事实 | 高影响必须回写 Design 并使旧确认失效 |
| 13 | 要求 PRD 和 Prototype 同时存在才修复 | 项目可能只有 PRD 或只有 Prototype | 按实际存在的下游分支提示用户重新确认后触发 |
| 14 | 在 PRD 不存在时仍运行 prd-consistency-check.py | 脚本会因找不到 prd.md 报错 | 仅在步骤 4 修改了 PRD 时运行；Prototype-only 项目用其他验证路径 |
| 15 | 硬编码 Agent 专属工具名或 Unix 专属命令 | 跨 Agent / 跨平台兼容性 | 用通用工具描述，由实际执行工具完成 |
| 16 | 要求模型输出思维过程 | 只输出结论、产物、决策和待确认项 | — |
| 17 | 把 Align 作为目标/范围的事实源 | 违反 vNext "Design 是唯一事实源"原则 | 目标/范围事实源是 design.md；align.md 仅作为输入参考 |
