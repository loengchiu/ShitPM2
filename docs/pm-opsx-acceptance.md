# PM 版 OpenSpec 改造验收文档

> 本文档用于验收 PM 版 OpenSpec 改造是否完成、是否正确。
> 验收方可以是人，也可以是 AI。

---

## 一、文件结构验收

### 检查项

以下文件必须全部存在：

```
openspec/
├── schemas/
│   └── pm-workflow/
│       ├── schema.yaml
│       └── templates/
│           ├── proposal.md
│           ├── design.md
│           ├── prd.md
│           ├── prototype.html
│           └── tasks.md
└── config.yaml
```

### 验证命令

```bash
openspec schemas
```

**预期输出**：`pm-workflow` 出现在 schema 列表中。

---

## 二、schema.yaml 验收

### 检查项

1. 必须定义 5 个 artifact：proposal、design、prd、prototype、tasks
2. 依赖关系必须为：
   - proposal 无依赖
   - design 依赖 proposal
   - prd 依赖 design
   - prototype 依赖 design
   - tasks 依赖 prd 和 prototype
3. `applies-required` 为 true 的 artifact：proposal、design、prd、prototype

### 验证方法

打开 `openspec/schemas/pm-workflow/schema.yaml`，逐行核对。

---

## 三、模板验收

### 3.1 proposal.md

**必须包含的章节**：
- 需求概述
- 建设范围（本期范围、后续范围、明确不做）
- 建设方式（iteration / new_build / hybrid）
- 涉及系统
- 现有线索
- 待确认问题

### 3.2 design.md

**必须包含的章节**：
- 角色定义
- 模块定义
- 页面清单（表格形式）
- 字段定义（9 列表格）
- 页面与字段落点
- 规则与状态定义
- 权限定义

### 3.3 prd.md

**必须包含的章节**：
- 详细需求说明（模块 → 页面 → 动作）
- 权限汇总
- 数据字典（轻量表格，默认 4 列）
- 状态机

### 3.4 prototype.html

**必须包含的元素**：
- Element Plus CDN 引用（CSS + JS + Icons）
- Vue 3 CDN 引用
- 统一后台基座（顶栏、左侧导航、页签区、主体工作区）
- CSS 变量定义（--shell-bg、--shell-primary 等）

### 3.5 tasks.md

**必须包含的章节**：
- PRD 撰写任务
- Prototype 制作任务

---

## 四、config.yaml 验收

### 检查项

1. `schema` 必须设为 `pm-workflow`
2. `context` 必须包含以下规则：
   - Design 写作规则（9 列表格、页面与字段落点、权限组织方式）
   - PRD 写作规则（模块→页面→动作、三层覆盖、禁止标签式正文）
   - Proposal 对齐纪律（一次只问一个问题）
   - Prototype 制作规则（Element Plus、后台基座）
3. `rules` 必须包含 design、prd 两个 artifact 的规则

### 验证命令

```bash
cat openspec/config.yaml
```

逐行核对。

---

## 五、端到端流程验收

### 测试场景

创建一个测试需求，走完完整流程。

### 步骤

**1. 创建测试需求**

```
/opsx:new test-pm-workflow --schema pm-workflow
```

**预期**：`openspec/changes/test-pm-workflow/` 目录创建成功，包含 `.openspec.yaml`。

**2. 生成 proposal**

```
/opsx:continue
```

**预期**：生成 `proposal.md`，包含需求概述、建设范围、建设方式等章节。

**3. 生成 design**

```
/opsx:continue
```

**预期**：生成 `design.md`，包含角色定义、模块定义、页面清单（表格）、字段定义（9 列）、页面与字段落点、规则与状态、权限定义。

**4. 生成 prd + prototype + tasks**

```
/opsx:ff
```

**预期**：
- `prd.md` 包含详细需求说明（模块→页面→动作）、权限汇总（默认页面级/按钮级，字段例外写入详细需求说明）、数据字典（默认 4 列，额外属性并入说明）、状态机
- `index.html` 包含 Element Plus CDN + 统一后台基座
- `tasks.md` 包含 PRD 撰写任务和 Prototype 制作任务

**5. 检查 PRD 质量**

打开 `prd.md`，检查：
- [ ] 没有标签式正文（**页面目标：**XX / **关键动作：**XX）
- [ ] 没有动作流水账（1.点击 2.填写 3.提交）
- [ ] 没有模糊表述（"按配置""待补充""详见原型"）
- [ ] 没有模板腔（"用于承载""需支持""按规范处理"）
- [ ] 数据字典使用轻量表格，默认保留字段、类型、必填、说明
- [ ] PRD 中没有引入 design 中不存在的新字段、新权限、新状态

**6. 检查 Prototype 质量**

打开 `index.html`，检查：
- [ ] 有 Element Plus CDN 引用
- [ ] 有统一后台基座（顶栏、导航、页签）
- [ ] 页面名称在页签条中

**7. 检查 design 与 PRD 一致性**

核对：
- [ ] design 中的每个字段都出现在 PRD 数据字典中
- [ ] design 中的每个权限都出现在 PRD 权限汇总中
- [ ] design 中的每个状态都出现在 PRD 状态机中
- [ ] design 页面清单中的每个页面都在 PRD 详细需求说明中有对应章节

**8. 归档**

```
/opsx:archive
```

**预期**：变更移动到 `openspec/changes/archive/`，Delta 规格合入主库。

---

## 六、验收判定

| 检查项 | 通过标准 | 结果 |
|---|---|---|
| 文件结构 | 7 个文件全部存在 | ☐ 通过 ☐ 失败 |
| schema.yaml | 5 个 artifact + 正确依赖 | ☐ 通过 ☐ 失败 |
| proposal 模板 | 6 个章节齐全 | ☐ 通过 ☐ 失败 |
| design 模板 | 7 个核心章节齐全 | ☐ 通过 ☐ 失败 |
| prd 模板 | 4 个核心章节齐全 | ☐ 通过 ☐ 失败 |
| prototype 模板 | Element Plus + 后台基座 | ☐ 通过 ☐ 失败 |
| config.yaml | schema + context + rules 齐全 | ☐ 通过 ☐ 失败 |
| 端到端流程 | 8 个步骤全部通过 | ☐ 通过 ☐ 失败 |
| PRD 质量 | 6 项检查全部通过 | ☐ 通过 ☐ 失败 |
| Prototype 质量 | 3 项检查全部通过 | ☐ 通过 ☐ 失败 |
| 一致性 | 4 项检查全部通过 | ☐ 通过 ☐ 失败 |

全部通过则改造成功。任一失败则需排查对应问题。
