# ShitPM 使用说明

ShitPM 是运行在 AI 编程助手中的产品工作台。ShitPM 以多文件 Design（设计地图 + 设计集清单 + 系统级基线 + 跨模块契约 + 模块设计）为唯一产品事实体系，PRD 与 Prototype 是 Design 的并列下游，Review、Fix、Prototype Mark 按需调用，不再有确认动作和固定八步门禁。

## 1. 环境准备

- Python 3.10+
- 项目根目录为本仓库根目录（以下命令中的 . 代表项目根）
- 不需要安装任何开发工具或构建链
- 不需要预先创建 .workflow/ 目录或 status.json

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
- verify 只检查 junction 是否指向本仓库、Skill 映射和全局规则是否就位，不检查 commit 哈希、不证明版本完整性、也不是发布版本证明
- 修改 Skill、模板、契约或脚本后无需重装；只有更换宿主或卸载时才需要重新执行安装命令

安装覆盖以下 10 个 Skill：

| Skill | 职责 |
|------|------|
| `spm-start` | 状态与导航，列出可用动作、Design 修改状态和下游受影响模块 |
| `spm-align` | Design 前的需求事实形成；可单独调用，也会由 Design 自动执行 |
| `spm-design` | 产品定义 与多文件 Design 基线生成 |
| `spm-prd` | PRD 生成（基于 Design 事实闭包） |
| `spm-prototype` | Prototype 生成（基于 Design 事实闭包） |
| `spm-fix` | 变更同步传播（连续同步实际受影响下游，无确认停顿） |
| `spm-design-review` | Design 独立挑战（默认局部，完整 Review 由用户触发） |
| `spm-prd-review` | PRD 独立挑战（按被审模块的 Design 依据） |
| `spm-prototype-review` | Prototype 独立挑战（按被审模块的 Design 依据） |
| `spm-prototype-mark` | 原型标注副本生成 |

## 3. 启动与状态查询

每次开始工作前查询项目状态和当前就绪动作：

```powershell
python scripts/python/stage-context.py --project-root .
```

`spm-start` 是只读导航：它输出项目状态、产物清单、最近 Review、Design 修改状态、下游受影响模块和当前 `available_actions[]`。它不把依赖图压成唯一下一步；用户可以看到所有可用动作。

输出关键字段：

| 字段 | 含义 |
|------|------|
| `current_stage` | 历史兼容字段，从 `status.json` 读取，缺失时回退到 `actual_stage` |
| `actual_stage` | 基于 canonical 文件探测得出的实际阶段 |
| `available_actions[]` | 当前所有可用动作；每项包含动作标识、原因、模型建议 |
| `design_change` | Design 修改状态（活动事务），含 `active`、`mode`、`phase` |
| `downstream_impact` | 下游受影响模块（PRD / Prototype 依据中的 affected / incomplete 目标） |
| `bundle_resources` | bundle root 及 templates/references/contracts/schemas 路径与存在性 |
| `status_source` | `loaded` / `missing` / `corrupted`，表示 `status.json` 读取情况 |

说明：

- 无 `status.json` 时仍应能基于 canonical 文件和有效产物输出可用动作；
- 存在活动 Design 事务时，PRD、Prototype、Review 和 fix 不读取正在变化的 Design 集合，先执行 `design-set.py recover`；
- 运行状态、动作卡、缓存和内部分析不得写入 Design 正文。

## 4. ShitPM 流程总览

```text
spm-align（Design 必经的需求事实形成；材料可选）
        ↓
spm-design（简单模式 / 完整模式）
        ↓
    设计地图 + 设计集清单 + 系统级基线 + 跨模块契约 + 模块设计
        ↓
    design-set.py check（校验通过后即为事实体系）
        ├───────────────┐
        ▼               ▼
     spm-prd       spm-prototype
（记录 PRD 依据）（记录 Prototype 依据）

按需辅助：spm-design-review / spm-prd-review / spm-prototype-review / spm-fix / spm-prototype-mark
```

| 动作 | 可用条件 |
|------|----------|
| `spm-align` | 可单独调用；Design 首次生成或输入变化时自动必经 |
| `spm-design` | 始终可用；用户必须选择简单模式或完整模式 |
| `spm-prd` | 设计地图与设计集清单存在 |
| `spm-prototype` | 设计地图与设计集清单存在 |
| `spm-design-review` | 设计集清单存在 |
| `spm-prd-review` | `prd.md` 存在 |
| `spm-prototype-review` | 原型源码工程存在（`prototype/index.html` + `src/`） |
| `spm-fix` | 始终可用 |
| `spm-prototype-mark` | 原型源码工程存在（`prototype/index.html` + `src/`） |

每个动作的默认模型建议见 `$BUNDLE/contracts/start-action-matrix.md`（唯一权威），运行时由 `spm-start` 输出动作级模型建议。

关键原则：

- Align 是 Design 的必经分析责任，但原始材料可选；空项目使用用户原话和回答形成事实；
- Design 同时承担产品定义与 Design 基线，是唯一产品事实体系；每项正式事实只有一个归属处；
- 设计集清单登记的正式 Design 文件是 PRD 和 Prototype 的唯一产品事实体系；
- PRD 与 Prototype 并列，可以任意顺序、单独生成；
- Review 是按需独立挑战，不构成门禁，不自动阻塞下游；
- 默认流程不依赖 metadata、`stage-prep.py` 或三个 Review 全部通过；
- 用户不再执行“确认 Design”或确认哈希；高影响未知只询问具体业务问题。

## 5. 核心流程

### 5.1 需求事实形成：spm-align

使用方式：

- 用户可以单独调用 Align，先整理目标、范围、边界和高影响未知；
- 用户直接调用 Design 时，Design 在当前任务内自动先完成 Align；
- 有原始材料时逐项保留页面、字段、操作、枚举、规则、状态、异常和验收；
- 没有材料时使用用户原话和回答形成事实，`source_count=0` 合法；
- Align 需要高影响回答时暂停，回答写回后自动继续。

产物：`output/align/align.md` 和 `.workflow/runtime/align/align-notes.json`。

Align 不承担最终方案决策，但不能只做摘要；Design 至少读取 Align 完整结果、详细材料事实和必要来源片段。需要读取历史 Design 时按目标事实闭包读取。

### 5.2 设计生成：spm-design

输入：

- 当前任务内已完成或复用的 Align 完整对齐稿；
- 用户原始需求、回答、业务材料和补充说明；
- 已准备且仍有效的材料事实资产；
- 当前模式允许读取的专项基线和证据。

产物（多文件 Design 集合）：

- `output/design/设计地图.md` — 系统导航（低分辨率）；
- `output/design/设计集清单.json` — 机器定位（稳定 ID、路径、依赖、指纹、决策）；
- `output/design/系统级基线/` — 系统级事实（删除某模块后仍成立）；
- `output/design/跨模块契约/` — 跨模块交接（只在交接时成立）；
- `output/design/模块设计/` — 模块内部事实（只影响一个模块内部）。

模式选择必须由用户决定：

- **简单模式**：完成目标、范围、主路径、关键规则、必要状态/权限、实际功能/数据、页面/区块/字段/操作、异常和验收；不生成无关空章节、完整 ABC 中间分析或虚构状态机。
- **完整模式**：在简单模式基础上，完成 A 层需求理解、B 层业务建模与一致性挑战、C 层产品承接与跨层一致性挑战；这些是内部责任，最终只保留产品方案结论、风险和未决事项，不把分析过程写入正式 Design 文件。
- 用户已明确模式则直接采用；未明确则只询问一次，未获得选择前不正式写入 Design。

最终 Design 按产品经理理解顺序组织，模块设计中的正式页面定义使用：页面目的、适用角色、进入条件、数据范围、主要状态；页面下按区块定义目的；区块下按字段和操作定义固定属性。详细格式见 `$BUNDLE/templates/design-map.md`、`design-system.md`、`design-contract.md`、`design-module.md` 和 `$BUNDLE/references/design-writing.md`。

生成前分析协议见 `$BUNDLE/references/design-analysis-protocol.md`；质量分级见 `$BUNDLE/references/design-quality-rubric.md`。质量标准主要检查需求理解、业务建模、产品承接、跨层一致性和问题发现，不授权补写产品事实。

首次生成责任：

- 明确产品目标、范围、非目标和外部边界；
- 形成端到端业务流程、对象、规则、状态和关键分支；
- 设计角色职责、权限和数据范围；
- 把业务方案落实到页面、区块、字段、操作和用户反馈；
- 识别异常、恢复、不可逆行为和外部责任；
- 比较主要方案并说明选择理由；
- 高影响未决事项显式暴露，登记到设计集清单 decisions（status=pending），不能伪装成确定事实。

### 5.3 Design 校验

Design 不再有人工确认动作或哈希确认。写作完成后运行：

```powershell
python scripts/python/design-set.py check --project-root .
```

校验设计集清单：Schema、ID、相对路径、依赖、地图引用和文件指纹。局部修改走事务：

- 单文件：`stage-single --id <ID>` → 写入 staged 路径 → `commit-single`；
- 多文件：`begin --ids <ID...>` → 写入 staged 目录 → `commit`；
- 中断或检查失败：`recover` 恢复旧完整集合或完成新集合。

PRD、Prototype 通过 `.workflow/provenance/` 记录各业务模块实际读取的 Design 文件依据；Design 文件变化只影响真实依赖它的目标。

### 5.4 PRD 生成：spm-prd

权威输入：目标业务模块的 Design 事实闭包（系统级基线、跨模块契约、模块设计）。`align.md` 和已有 Prototype 仅作辅助参考。

产物：

- `output/prd/prd.md`
- `output/prd/diagrams/*.drawio` 与 `*.png`（按需）
- `.workflow/provenance/prd.json`（模块依据）

首次生成责任：

- 维持 Design 的产品语义；PRD 按业务闭环组织功能模块，总体说明只定义跨模块共用事实，页面、字段、状态、权限、异常和验收就近归入所属闭环。
- 正式写入前完成 Design → PRD 语义对照，覆盖核心对象、角色、状态、关键动作、流程、权限、模块和跨系统边界；
- 已识别的事实偏差和语义漂移在首次交付前修正；
- 发现必须新增高影响产品判断时不得猜测，返回 Design 处理；
- 成功后用 `design-set.py record-inputs` 记录该模块实际读取的 Design 文件依据。

不读取决策记录作为事实输入。

### 5.5 Prototype 生成：spm-prototype

权威输入：目标业务模块的 Design 事实闭包。已有 PRD 可作为页面、字段和动作细节的辅助参考，但不能成为产品事实源。

产物：`output/prototype/` 标准 Vite 源码工程（`src/` 唯一编辑源、`dist/` 可重建构建产物、`原型工具.bat` 用户唯一操作入口）和 `.workflow/provenance/prototype.json`（模块依据）。

首次生成责任：

- 覆盖本轮指定的模块、页面、核心任务路径和关键状态；
- 业务流程、角色权限、核心状态和产品边界与 Design 一致；
- 使用标准 Vite + React 18 + Ant Design 6 源码工程；`src/` 是唯一编辑源，`dist/` 只由 `npm run build` 生成，不直接修改 dist；
- 正式交付前运行 `npm ci` + `npm run build`，分别用开发预览与构建预览检查渲染、交互可达性、关键状态和资源加载；
- 用户通过双击 `原型工具.bat` 完成本地预览、构建、重建；已配置 Cloudflare 时经确认后上传，不需要输入命令；
- 发现必须改变业务行为才能完成原型时返回 Design，不在页面中静默发明规则；
- 成功后用 `design-set.py record-inputs` 记录该模块实际读取的 Design 文件依据。

不要求 PRD 存在；Prototype-only 是合法状态。

Prototype Mark 收集的高影响反馈按 `$BUNDLE/templates/prototype-feedback-classification.md` 区分为**表现问题**（可直接改 Prototype）与**语义问题**（缺失/偏离 Design 事实，交给 `spm-fix` 或回到 Design 处理，不在原型阶段自行拍板）。

## 6. 按需动作

### 6.1 Review

三个 Review（`spm-design-review`、`spm-prd-review`、`spm-prototype-review`）按需独立调用，不构成门禁。

- 简单项目可以不调用 Review；
- Design Review 默认只审查目标文件闭包，完整 Review 由用户明确触发；
- PRD / Prototype Review 读取被审模块记录的 Design 依据；
- Review 不修改原始产物、不自动推进阶段；
- Review 结论区分确定性缺陷、产品风险、需用户决策的问题；
- 预检查只在目标文件不存在、不可读或完全无法解析时阻止执行；缺章节、内容不足、冲突和质量问题作为审查问题返回；
- 深度业务 Review 使用深度推理模型；结构和明确规则核对可使用轻量模型或脚本。

### 6.2 Fix

`spm-fix` 用于在用户确认事实或产品决策发生变化后传播影响。

- 高影响变化先回写 Design（按事务），再连续同步所有实际存在且受影响的 PRD / Prototype 模块，无确认停顿；
- 仅表现层变化可以只修改 Prototype；
- 支持 PRD-only、Prototype-only 和双下游项目；只同步实际存在的下游，不自动创建；
- PRD 存在时运行 `prd-consistency-check.py --module <模块名>`；Prototype-only 项目无 PRD 时使用 `--allow-no-prd` 跳过，不阻塞 Fix；
- 针对性检查通过后更新下游依据，消除受影响状态；检查失败时保留 affected 或 incomplete，不得伪装通过。

### 6.3 Prototype Mark

`spm-prototype-mark` 复制原型源码工程到 `output/prototypemark/`（排除 `node_modules/` 与旧 `dist/`），在副本 `src/` 中注入标注组件并重新构建，原始原型不变。

- 不修改原始 Prototype；
- 不回写 Design 或 PRD；
- 不进入默认主链路；
- 高影响反馈通过结构化输出约定供 Fix 使用。

## 7. 模型选择建议

模型选择发生在每个独立流程开始前，开始后不切换。每个动作的默认模型建议和可使用轻量模型的条件以 `$BUNDLE/contracts/start-action-matrix.md` 为唯一权威；`spm-start` 会为每个可用动作输出动作级模型建议。

无法判断任务复杂度时使用深度推理模型，优先保护首次产物质量。模型建议不写入业务产物正文，不构成强制门禁。

## 8. 确定性脚本速查

| 脚本 | 功能 |
|------|------|
| `stage-context.py` | 状态查询、可用动作、Design 修改状态、下游受影响模块；无 `status.json` 也能正常工作 |
| `design-set.py check` | 校验设计集清单（Schema、ID、路径、依赖、地图引用、指纹） |
| `design-set.py refresh` | 重算清单中全部文件指纹与 set_sha256 并写回（首次创建清单时使用） |
| `design-set.py closure` | 按目标 ID 沿 depends_on 输出递归依赖闭包 |
| `design-set.py stage-single/commit-single` | 单文件 Design 修改事务 |
| `design-set.py begin/commit` | 多文件 Design 修改事务 |
| `design-set.py recover` | 从单文件或多文件中断状态恢复 |
| `design-set.py record-inputs` | 写入 PRD / Prototype 模块依据 |
| `design-set.py check-inputs` | 检查下游模块是否 current / affected / incomplete；下游产物存在但无依据记录时报告 incomplete（provenance_missing），不静默当作无影响 |
| `prd-consistency-check.py` | PRD 与 Design 确定性对比，输出 `hallucinated` / `missing` / `attribute_mismatch`；`--allow-no-prd` 支持 Prototype-only 项目；`--module` 按模块运行 |
| `prd-style-lint.py` | PRD 风格检查（坏味道、流水账、模糊表述等） |
| `prototype-source-check.py` | Prototype 源码工程确定性检查（src/dist/package/BAT/README 契约，通过返回 0，失败返回 1，不自动修复） |
| `prototype-consistency-check.py` | Prototype 与 Design 确定性对比；`--module` 按模块运行 |
| `stage-prep.py` | 旧版兼容：仅旧项目兼容诊断，ShitPM 主流程不依赖 |
| `shitpm-host.py install/verify/remove` | 安装、验证、卸载宿主映射 |

典型用法：

```powershell
python scripts/python/stage-context.py --project-root .
python scripts/python/design-set.py check --project-root .
python scripts/python/design-set.py closure --project-root . --targets MOD-001
python scripts/python/design-set.py record-inputs --project-root . --artifact prd --target-id prd:订单 --target-name 订单 --output-path output/prd/prd.md --output-locator '## 4.6 订单' --inputs SYS-001,CON-001,MOD-001
python scripts/python/prd-consistency-check.py --project-root . --module 订单
python scripts/python/prd-consistency-check.py --project-root . --allow-no-prd
python scripts/python/prd-style-lint.py output/prd/prd.md --format json --output .workflow/runtime/prd/lint.json
```

## 9. 常见问题

**Q: 没有 `status.json` 能用吗？**
能。`stage-context.py` 优先探测 canonical 文件，`status_source` 标记为 `missing` 时仍正常输出 `available_actions[]`。

**Q: PRD 一定要先于 Prototype 吗？**
不一定。两者并列，可以任意顺序、单独生成。Prototype-only 是合法状态。

**Q: Design 改了，PRD 还能用吗？**
看下游依据。`design-set.py check-inputs` 会报告相关模块为 affected；用户明确修改事实时由 fix 连续同步所有实际存在且受影响的 PRD / Prototype 模块；外部未知修改只标记影响，不自动改写下游。

**Q: 只想生成 Prototype 不想生成 PRD 可以吗？**
可以。Design 生成后直接调用 `spm-prototype`，PRD 不存在不影响 Prototype 生成。

**Q: Review 不通过会阻塞下一步吗？**
不会。Review 是审查问题而不是门禁，不自动阻断后续工作，也不替用户决定是否继续。

**Q: 旧项目有 metadata 怎么办？**
不影响 ShitPM 主流程。canonical 文件探测优先于 `status.json` 的 artifacts 镜像，metadata 不再构成硬门禁。`stage-prep.py` 仅作为旧版兼容诊断保留。

**Q: `stage-context.py` 报 `status_source: corrupted` 怎么办？**
`status.json` JSON 损坏。脚本仍会基于 canonical 文件输出可用动作，但建议修复或删除 `.workflow/status.json` 后由后续流程重建。

**Q: 旧单体 Design 项目如何迁移？**
手工复制项目文件夹后执行 `docs/plans/2026-08-16-旧单体Design迁移提示词.md`，按提示词把 `design.md` 拆为多文件 Design；迁移只改变组织，不改变产品事实。

## 10. 验收标准（ShitPM）

ShitPM 主流程应满足：

1. `spm-start` 输出 Design 修改状态和下游受影响模块；PRD、Prototype 在设计地图与清单存在时可用
2. Design 文件变化只影响真实依赖它的下游目标，provenance 记录各模块依据
3. PRD、Prototype 可独立生成，任意顺序
4. Review 不再因章节缺失被预检查阻止，缺章节作为审查问题返回
5. 无 `status.json` 时 `stage-context.py` 仍能正常输出
6. Prototype-only 项目调用 `prd-consistency-check.py --allow-no-prd` 不阻塞 Fix
7. 安装后 `verify` 通过，10 个 Skill 映射就位
8. 活动 Design 事务存在时，下游动作不读取正在变化的集合，先 recover
