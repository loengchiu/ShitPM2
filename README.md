# ShitPM

把需求从一句话推进到可评审的 PRD、设计基线和 HTML 原型。

ShitPM 是一套面向产品经理和 AI 协作的需求生产工作流。它把“需求对齐、设计展开、PRD 撰写、原型生成、质量审查”拆成稳定阶段，让每一步都有明确产物、进入条件和验收口径。

## 为什么需要它

需求文档最常见的问题不是写不出来，而是写着写着失控：

- 对齐稿讲目标，PRD 又重新发明字段和状态
- 设计里有页面，原型里少页面
- 权限、字段、状态分散在多份文档里，越改越不一致
- AI 能快速出稿，但长文容易变成操作说明、表格堆砌或模板腔

ShitPM 的目标是把这些风险前置处理。它让 AI 不是“直接写一篇文档”，而是按阶段继承事实、生成产物、同步校验依据、再进入审查。

## 它能做什么

- **需求对齐**：把业务目标、范围边界、角色场景先讲清楚，再进入设计。
- **设计基线**：沉淀模块、页面、字段、页面落点、规则、状态和权限，作为后续唯一事实源。
- **PRD 生成**：基于设计基线生成研发可评审的 PRD，按模块、页面、动作展开页面行为。
- **原型生成**：生成可打开的 HTML 原型，用于评审页面结构、状态表现和主路径。
- **同步修复**：上游事实变化后，沿 design、PRD、prototype 链路同步传播。
- **质量审查**：通过 review skill 和脚本检查章节完整性、产物完整性、PRD 写作坏味道和跨阶段一致性。

## 工作流

| 阶段 | 产物 | 重点 |
|------|------|------|
| `align` | 对齐稿 | 目标、范围、角色、边界 |
| `design` | 设计基线 | 模块、页面、字段、规则、状态、权限 |
| `design-review` | 设计审查结果 | 事实是否完整、是否可进入 PRD |
| `prd` | PRD 正文 | 详细需求、权限汇总、数据字典、状态机 |
| `prd-review` | PRD 审查结果 | 是否可被研发和测试直接评审 |
| `prototype` | HTML 原型 | 页面结构、主路径、状态和权限表现 |
| `prototype-review` | 原型审查结果 | 页面覆盖和交互表达是否完整 |

## 核心原则

### Design 是事实源

字段、权限、状态的完整定义保存在 design 阶段。PRD 和 prototype 负责展开和表达，不重新定义事实。

### 产物和校验同步

每个阶段都有面向人评审的文档，也有供脚本校验和跨阶段追踪的结构化数据。产物更新后，需要同步刷新对应阶段的校验数据。

### PRD 不写成操作流水账

PRD 详细需求说明按“模块 -> 页面 -> 动作”组织。动作正文需要覆盖展示规则、交互逻辑、状态变化、异常边界，而不是只写“点击、填写、提交”。

### 轻量但不偷懒

权限汇总默认到页面级和按钮级；字段权限例外写进对应需求说明。数据字典默认保留字段、类型、必填、说明；额外属性只在确实影响实现时写入说明。

## 快速开始

### 环境要求

- Python 3.10+
- 一个包含 `.workflow/status.json` 的业务项目，或使用 `/spm-start` 初始化

### 查看当前阶段

```powershell
python scripts/python/stage-context.py .
```

输出中的 `current_stage` 表示当前阶段，`next_recommended` 表示建议下一步。

### 生成或刷新阶段元数据

```powershell
python scripts/python/stage-prep.py --stage design
python scripts/python/stage-prep.py --stage prd
python scripts/python/stage-prep.py --stage prototype
```

### 运行 review 预检查

```powershell
python scripts/python/review-precheck.py --stage prd
```

### 检查 PRD 文风

```powershell
python scripts/python/prd-style-lint.py output/prd/prd.md
```

## 常用 Skill

| Skill | 用途 |
|------|------|
| `/spm-start` | 识别当前项目和可继续入口 |
| `/spm-align` | 需求对齐 |
| `/spm-design` | 生成或修正设计基线 |
| `/spm-design-review` | 审查设计基线 |
| `/spm-prd` | 生成 PRD |
| `/spm-prd-review` | 审查 PRD |
| `/spm-prototype` | 生成 HTML 原型 |
| `/spm-prototype-review` | 审查原型 |
| `/spm-fix` | 跨阶段同步修复 |

## 适合谁

- 需要把零散需求快速整理成可评审规格的产品经理
- 需要用 AI 写 PRD，但担心长文失控的团队
- 需要维护 design、PRD、prototype 一致性的项目组
- 想把需求评审从“凭感觉看文档”推进到“有门禁、有锚点、有同步链路”的团队

## 更多文档

- [使用说明](USAGE.md)
- [测试与验收](02-测试与验收.md)
- [实现总规约](01-新辅助器实现总规约.md)
