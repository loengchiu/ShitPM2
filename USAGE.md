# ShitPM 使用说明

ShitPM 是运行在 AI 编程助手中的产品工作台。ShitPM 以确认版 `design.md` 为唯一产品事实基线，PRD 与 Prototype 是 Design 的并列下游，Review、Fix、Prototype Mark 按需调用，不再有固定八步门禁。

## 1. 环境准备

- Python 3.10+
- 项目根目录为本仓库根目录（以下命令中的 `.` 代表项目根）
- 不需要安装任何开发工具或构建链
- 不需要预先创建 `.workflow/` 目录或 `status.json`

## 2. 安装与卸载

ShitPM 通过 junction 把本仓库注册到宿主工具的 bundle 目录，宿主因此能加载 Skill 和全局规则。

```powershell
# 安装到指定宿主
python scripts/python/shitpm-host.py install --host <codex|trae-cn|claude-code|workbuddy>

# 验证安装
python scripts/python/shitpm-host.py verify --host <host>

# 卸载
python scripts/python/shitpm-host.py remove --host <host>
```

关于 junction 安装的性质：

- junction 指向当前仓库工作树，仓库内容变化实时反映到宿主侧，无需重新安装
- `verify` 只检查 junction 是否指向本仓库、Skill 映射和全局规则是否就位，不检查 commit 哈希、不证明版本完整性、也不是发布版本证明
- 修改 Skill、模板、契约或脚本后无需重装；只有更换宿主或卸载时才需要重新执行安装命令

安装覆盖以下 10 个 Skill：

| Skill | 职责 |
|------|------|
| `spm-start` | 状态与导航，列出可用动作和模型建议 |
| `spm-align` | Design 前的需求事实形成；可单独调用，也会由 Design 自动执行 |
| `spm-design` | 产品定义 与 Design 基线生成 |
| `spm-prd` | PRD 生成（基于确认版 Design） |
| `spm-prototype` | Prototype 生成（基于确认版 Design） |
| `spm-fix` | 变更同步传播 |
| `spm-design-review` | Design 独立挑战 |
| `spm-prd-review` | PRD 独立挑战 |
| `spm-prototype-review` | Prototype 独立挑战 |
| `spm-prototype-mark` | 原型标注副本生成 |

## 3. 启动与状态查询

每次开始工作前查询项目状态和当前就绪动作：

```powershell
python scripts/python/stage-context.py --project-root .
```

`spm-start` 是只读导航：它输出项目状态、产物清单、最近 Review 和当前 `ready_actions[]`。它不把依赖图压成唯一下一步；用户可以看到所有已满足依赖的动作，编排器负责判断动作是否真的就绪。

输出关键字段：

| 字段 | 含义 |
|------|------|
| `current_stage` | 历史兼容字段，从 `status.json` 读取，缺失时回退到 `actual_stage` |
| `actual_stage` | 基于 canonical 文件探测得出的实际阶段 |
| `ready_actions[]` | 当前所有已满足依赖、可以执行的动作；每项至少包含动作标识、依赖、原因、输入范围、预期输出和模型建议 |
| `design_confirmation` | Design 确认状态，含 `confirmed`、`reason`、`confirmed_at` 等 |
| `bundle_resources` | bundle root 及 templates/references/contracts/schemas 路径与存在性 |
| `status_source` | `loaded` / `missing` / `corrupted`，表示 `status.json` 读取情况 |

说明：

- 无 `status.json` 时仍应能基于 canonical 文件和有效产物输出就绪动作；
- 同一批无硬依赖的动作可以并行；
- 动作失败只使受影响动作及其下游重新就绪，不重跑仍然有效的上游；
- `ready_actions[]` 是执行导航，不是产品事实；运行状态、动作卡、缓存和内部分析不得写入 Design 正文。

## 4. ShitPM 流程总览

```text
spm-align（Design 必经的需求事实形成；材料可选）
        ↓
材料准备/复用
        ├───────────────┐
        ▼               ▼
     简单模式         完整模式
        │               │
  最小闭环分析       A → B → C
        │               │
  写作与生成内自审   设计写作与生成内自审
        └───────┬───────┘
                ▼
      页面 → 区块 → 字段/操作
                ↓
        用户明确确认 design.md
          ├───────────────┐
          ▼               ▼
       spm-prd       spm-prototype

按需辅助：spm-design-review / spm-prd-review / spm-prototype-review / spm-fix / spm-prototype-mark
```

| 动作 | 可用条件 | 默认模型等级 |
|------|----------|--------------|
| `spm-align` | 可单独调用；Design 首次生成或输入变化时自动必经 | 视任务而定 |
| `spm-design` | 始终可用；用户必须选择简单模式或完整模式 | 无法判断时使用深度推理模型 |
| `confirm-design` | `design.md` 存在 | 无需模型 |
| `spm-prd` | `design.md` 存在且已确认 | 根据确认版 Design 判断 |
| `spm-prototype` | `design.md` 存在且已确认 | 根据交互和实现复杂度判断 |
| `spm-design-review` | `design.md` 存在 | 深度推理模型 |
| `spm-prd-review` | `prd.md` 存在 | 深度推理模型 |
| `spm-prototype-review` | `prototype/index.html` 存在 | 深度推理模型 |
| `spm-fix` | 始终可用 | 根据变更影响判断 |
| `spm-prototype-mark` | `prototype/index.html` 存在 | 轻量模型 |

关键原则：

- Align 是 Design 的必经分析责任，但原始材料可选；空项目使用用户原话和回答形成事实；
- Design 同时承担产品定义与 Design 基线，是主链路唯一人工确认点；
- 用户确认后的 `design.md` 是 PRD 和 Prototype 的唯一产品事实基线；
- PRD 与 Prototype 并列，可以任意顺序、单独生成；
- Review 是按需独立挑战，不构成门禁，不自动阻塞下游；
- 默认流程不依赖 metadata、`stage-prep.py` 或三个 Review 全部通过；
- Design 内部使用依赖图和 `ready_actions[]`，不使用固定三段式或唯一下一动作。

## 5. 核心流程

### 5.1 需求事实形成：spm-align

使用方式：

- 用户可以单独调用 Align，先整理目标、范围、边界和高影响未知；
- 用户直接调用 Design 时，Design 在当前任务内自动先完成 Align；
- 有原始材料时逐项保留页面、字段、操作、枚举、规则、状态、异常和验收；
- 没有材料时使用用户原话和回答形成事实，`source_count=0` 合法；
- Align 需要高影响回答时暂停，回答写回后自动继续。

产物：`output/align/align.md` 和 `.workflow/runtime/align/align-notes.json`。

Align 不承担最终方案决策，但不能只做摘要；Design 至少读取 Align 完整结果、详细材料事实和必要来源片段。

### 5.2 设计生成：spm-design

输入：

- 当前任务内已完成或复用的 Align 完整对齐稿；
- 用户原始需求、回答、业务材料和补充说明；
- 已准备且仍有效的材料事实资产；
- 当前模式依赖图允许读取的专项基线和证据。

产物：

- `output/design/design.md` — 面向产品经理的产品方案设计；
- `output/design/decision-notes.md` — 过程审计（设计决策、偏离、权衡、待确认）。

模式选择必须由用户决定：

- **简单模式**：完成目标、范围、主路径、关键规则、必要状态/权限、实际功能/数据、页面/区块/字段/操作、异常和验收；不生成无关空章节、完整 ABC 中间分析或虚构状态机。
- **完整模式**：在简单模式基础上，按依赖图完成 A 层需求理解、B 层业务建模与一致性挑战、C 层产品承接与跨层一致性挑战；这些是内部责任，最终只保留产品方案结论、风险和待确认，不把分析过程写入 `design.md`。
- 用户已明确模式则直接采用；未明确则只询问一次，未获得选择前不正式写入 Design。

Design 内部依赖图：

```text
Align（必经）
  ├─ 简单：材料事实保留（有材料时）→ 最小闭环分析与写作内自审
  └─ 完整：材料事实保留（有材料时）→ A → B → C → Design 写作与跨层自检
```

编排器每轮返回当前全部 `ready_actions[]`。Align 必须先于材料和 Design 分析；同批无硬依赖动作可以并行；有效上游不因下游失败重跑；不固定模型调用次数，也不把 `ready_actions[]` 压成唯一下一动作。材料内容未变化时复用事实资产，不重复全文提取；材料或输入变化时先使 Align 失效。

最终 `design.md` 按产品经理理解顺序组织，正式页面定义使用：页面目的、适用角色、进入条件、数据范围、主要状态；页面下按区块定义目的；区块下按字段和操作定义固定属性。详细格式见 `$BUNDLE/templates/design.md` 和 `$BUNDLE/references/design-writing.md`。

生成前分析协议见 `$BUNDLE/references/design-analysis-protocol.md`；冻结后质量分级见 `$BUNDLE/references/design-quality-rubric.md`。质量标准主要检查需求理解、业务建模、产品承接、跨层一致性和问题发现，不授权补写产品事实。

首次生成责任：

- 明确产品目标、范围、非目标和外部边界；
- 形成端到端业务流程、对象、规则、状态和关键分支；
- 设计角色职责、权限和数据范围；
- 把业务方案落实到页面、区块、字段、操作和用户反馈；
- 识别异常、恢复、不可逆行为和外部责任；
- 比较主要方案并说明选择理由；
- 高影响待确认事项显式暴露，不能伪装成确定事实。

`decision-notes.md` 只用于过程审计，不作为下游事实输入。

### 5.3 Design 确认

Design 是主链路唯一人工确认点。用户明确确认当前 `design.md` 后，它才成为下游事实基线。

```powershell
# 确认当前 design.md
python scripts/python/design-confirmation.py --project-root . confirm

# 检查确认是否仍然有效（design.md 修改后旧确认自动失效）
python scripts/python/design-confirmation.py --project-root . check

# 查看当前确认记录
python scripts/python/design-confirmation.py --project-root . show
```

`confirm` 计算 `design.md` 的 sha256 并写入 `.workflow/confirmations/design.json`。`check` 比对当前 sha256 与已记录 sha256，不匹配时返回 `confirmed: false` 并提示需要重新确认。

确认行为说明：

- 修改 `design.md` 后旧确认自动失效，下游动作会被 `stage-context.py` 标记为不可用
- 仅修改 `decision-notes.md` 不影响确认
- 确认记录只标识版本，不复制产品事实，不构成事实索引

### 5.4 PRD 生成：spm-prd

权威输入：当前确认版 `design.md`。`align.md` 和已有 Prototype 仅作辅助参考。

产物：

- `output/prd/prd.md`
- `output/prd/decision-notes.md`

首次生成责任：

- 维持确认版 Design 的产品语义；PRD 按业务闭环组织功能模块，总体说明只定义跨模块共用事实，页面、字段、状态、权限、异常和验收就近归入所属闭环。
- 正式写入前完成 Design → PRD 语义对照，覆盖核心对象、角色、状态、关键动作、流程、权限、模块和跨系统边界
- 已识别的事实偏差和语义漂移在首次交付前修正
- 发现必须新增高影响产品判断时不得猜测，返回 Design 处理

不读取 Design `decision-notes.md` 作为事实输入。

### 5.5 Prototype 生成：spm-prototype

权威输入：当前确认版 `design.md`。已有 PRD 可作为页面、字段和动作细节的辅助参考，但不能成为产品事实源。

产物：`output/prototype/index.html` 及本地运行资源。

首次生成责任：

- 覆盖本轮指定的模块、页面、核心任务路径和关键状态
- 业务流程、角色权限、核心状态和产品边界与 Design 一致
- 沿用 HTML + Vue + Tailwind + daisyUI + 本地 `lib/` 的轻量基座
- 正式交付前实际打开并检查渲染、交互可达性、关键状态和资源加载
- 发现必须改变业务行为才能完成原型时返回 Design，不在页面中静默发明规则

不要求 PRD 存在；Prototype-only 是合法状态。

Prototype Mark 收集的高影响反馈按 `$BUNDLE/templates/prototype-feedback-classification.md` 区分为**表现问题**（可直接改 Prototype）与**语义问题**（缺失/偏离 Design 事实，交给 `spm-fix` 或回到 Design 处理，不在原型阶段自行拍板）。

## 6. 按需动作

### 6.1 Review

三个 Review（`spm-design-review`、`spm-prd-review`、`spm-prototype-review`）按需独立调用，不构成门禁。

- 简单项目可以不调用 Review
- Review 不修改原始产物、不自动推进阶段、不自动确认 Design
- Review 结论区分确定性缺陷、产品风险、需用户决策的问题
- 预检查只在目标文件不存在、不可读或完全无法解析时阻止执行；缺章节、内容不足、冲突和质量问题作为审查问题返回，不用 `can_start_review=false` 阻止
- 深度业务 Review 使用深度推理模型；结构和明确规则核对可使用轻量模型或脚本

### 6.2 Fix

`spm-fix` 用于在用户确认事实或产品决策发生变化后传播影响。

- 高影响变化先回写 Design 并使旧确认失效，再由用户决定重新生成哪个下游
- 仅表现层变化可以只修改 Prototype
- 支持 PRD-only、Prototype-only 和双下游项目
- PRD 存在时运行 `prd-consistency-check.py`；Prototype-only 项目无 PRD 时使用 `--allow-no-prd` 跳过，不阻塞 Fix
- 不自动确认 Design，不自动重新生成全部下游

### 6.3 Prototype Mark

`spm-prototype-mark` 复制原型到 `output/prototypemark/`，注入悬浮导航栏、关键点标记和内容备注弹窗。

- 不修改原始 Prototype
- 不回写 Design 或 PRD
- 不进入默认主链路
- 高影响反馈通过结构化输出约定供 Fix 使用

## 7. 模型选择建议

模型选择发生在每个独立流程开始前，开始后不切换。

| 动作 | 默认建议 | 可使用轻量模型的条件 |
|------|----------|----------------------|
| `spm-align` | 视任务而定 | 目标、范围和边界已明确，仅需整理 |
| `spm-design` | 深度推理模型 | 业务确实简单、输入完整、无方案权衡、角色状态权限关系简单 |
| `spm-prd` | 根据确认版 Design 判断 | Design 决策完整，主要按现有模板展开明确规格 |
| `spm-prototype` | 根据交互和实现复杂度判断 | 页面少、路径单一、行为明确，主要做既定表达与实现 |
| `spm-design-review` | 深度推理模型 | 仅做结构和明确规则检查时可改用轻量模型或脚本 |
| `spm-prd-review` | 深度推理模型 | 仅做结构和一致性检查时可改用轻量模型或脚本 |
| `spm-prototype-review` | 深度推理模型 | 仅做结构检查时可改用轻量模型或脚本 |
| `spm-fix` | 根据变更影响判断 | 修改范围、正确结果和受影响位置都已明确 |
| `spm-prototype-mark` | 轻量模型 | 主动发现产品或交互问题时应另行使用深度 Review |

无法判断任务复杂度时使用深度推理模型，优先保护首次产物质量。模型建议不写入业务产物正文，不构成强制门禁。

## 8. 确定性脚本速查

| 脚本 | 功能 |
|------|------|
| `stage-context.py` | 状态查询、可用动作、模型建议；无 `status.json` 也能正常工作 |
| `design-confirmation.py confirm` | 写入 Design 确认记录（sha256 + 时间戳） |
| `design-confirmation.py check` | 检查当前 `design.md` 是否仍与已确认版本一致 |
| `design-confirmation.py show` | 查看当前确认记录 |
| `prd-consistency-check.py` | PRD 与 Design 确定性对比，输出 `hallucinated` / `missing` / `attribute_mismatch`；`--allow-no-prd` 支持 Prototype-only 项目 |
| `prd-style-lint.py` | PRD 风格检查（坏味道、流水账、模糊表述等） |
| `design-analysis-protocol.md` | spm-design 生成前的分析责任协议（双模式、ABC 内部责任边界） |
| `design-quality-rubric.md` | Design 成品质量分级标准（五维度 L0–L3，覆盖需求理解、业务建模、产品承接和跨层一致性） |
| `stage-prep.py` | 旧版兼容：仅旧项目兼容诊断，ShitPM 主流程不依赖 |
| `shitpm-host.py install/verify/remove` | 安装、验证、卸载宿主映射 |

典型用法：

```powershell
python scripts/python/stage-context.py --project-root .
python scripts/python/design-confirmation.py --project-root . confirm
python scripts/python/design-confirmation.py --project-root . check
python scripts/python/prd-consistency-check.py --project-root .
python scripts/python/prd-consistency-check.py --project-root . --allow-no-prd
python scripts/python/prd-style-lint.py output/prd/prd.md --format json --output .workflow/runtime/prd/lint.json
```

## 9. 常见问题

**Q: 没有 `status.json` 能用吗？**
能。`stage-context.py` 优先探测 canonical 文件，`status_source` 标记为 `missing` 时仍正常输出 `ready_actions[]`。

**Q: PRD 一定要先于 Prototype 吗？**
不一定。两者并列，可以任意顺序、单独生成。Prototype-only 是合法状态。

**Q: Design 改了，PRD 还能用吗？**
不能直接用。`design.md` 修改后旧确认自动失效，`stage-context.py` 会把 PRD、Prototype 标记为不可用。需要重新确认 Design 后再生成下游。

**Q: 只想生成 Prototype 不想生成 PRD 可以吗？**
可以。Design 确认后直接调用 `spm-prototype`，PRD 不存在不影响 Prototype 生成。

**Q: Review 不通过会阻塞下一步吗？**
不会。Review 是审查问题而不是门禁，不自动阻断后续工作，也不替用户决定是否继续。

**Q: 旧项目有 metadata 怎么办？**
不影响 ShitPM 主流程。canonical 文件探测优先于 `status.json` 的 artifacts 镜像，metadata 不再构成硬门禁。`stage-prep.py` 仅作为旧版兼容诊断保留。

**Q: `stage-context.py` 报 `status_source: corrupted` 怎么办？**
`status.json` JSON 损坏。脚本仍会基于 canonical 文件输出可用动作，但建议修复或删除 `.workflow/status.json` 后由后续流程重建。

**Q: `design-confirmation.py check` 返回 `hash_mismatch` 怎么办？**
`design.md` 在上次确认后被修改。需要重新运行 `confirm` 命令重新确认当前版本，下游动作才会恢复可用。

## 10. 验收标准（ShitPM）

ShitPM 主流程应满足：

1. Design 编排输出 `ready_actions[]`；PRD、Prototype 在 Design 确认后可用
2. Design 修改后旧确认自动失效，`design-confirmation.py check` 返回 `hash_mismatch`
3. PRD、Prototype 可独立生成，任意顺序
4. Review 不再因章节缺失被预检查阻止，缺章节作为审查问题返回
5. 无 `status.json` 时 `stage-context.py` 仍能正常输出
6. Prototype-only 项目调用 `prd-consistency-check.py --allow-no-prd` 不阻塞 Fix
7. 安装后 `verify` 通过，10 个 Skill 映射就位
