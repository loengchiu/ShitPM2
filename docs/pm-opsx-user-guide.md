# PM 版 OpenSpec 操作手册

> 本文档面向产品经理，指导日常如何使用 PM 版 OpenSpec 管理需求。

---

## 可用命令速查

| 命令 | 用途 | 何时使用 |
|---|---|---|
| `/opsx:explore` | 需求探索 | 信息不全，需要先理清思路 |
| `/opsx:propose` | 创建需求 + 生成对齐稿 | 信息明确，可以开始 |
| `/opsx:continue` | 逐步生成下一个工件 | 需求复杂，想逐步确认 |
| `/opsx:ff` | 快进——一次性生成所有规划工件 | 需求简单，想快速出稿 |
| `/opsx:apply` | 按任务清单逐项完成 | design 确认后，填充 PRD 和原型 |
| `/opsx:design-sync` | 同步 design 内部一致性 | 你修改了 design 的某部分后 |
| `/opsx:verify` | 检查 PRD/prototype 质量 | 生成完成后检查 |
| `/opsx:archive` | 结案 | 需求关闭，规则合库 |

---

## 场景一：接到新需求，信息明确（快速路径）

```
You: /opsx:propose A-system-batch-approve
AI:  Created openspec/changes/A-system-batch-approve/
     ✓ proposal.md
     ✓ design.md
     Ready to create: prd, prototype

You: /opsx:ff
AI:  ✓ prd.md
     ✓ index.html
     ✓ tasks.md
     Ready for implementation. Run /opsx:apply.

You: /opsx:apply
AI:  [逐项完成 PRD 正文和 Prototype 页面]

You: /opsx:verify
AI:  [检查 PRD/prototype 是否完整继承 design]

You: /opsx:archive
AI:  [结案]
```

---

## 场景二：接到新需求，信息不全（先探索）

```
You: /opsx:explore A 系统的批量审批

AI:  [探索、分析代码库、比较方案、提出疑问]

[聊清楚后]
You: /opsx:propose A-system-batch-approve

[后续同上]
```

---

## 场景三：需求复杂，逐步确认

```
You: /opsx:propose A-system-complex-feature
AI:  Created openspec/changes/A-system-complex-feature/
     ✓ proposal.md
     Ready to create: design

[审阅 proposal，没问题后]
You: /opsx:continue
AI:  ✓ design.md — 模块、页面、字段、落点、权限
     Ready to create: prd, prototype

[打开 design.md 逐段审阅。发现页面落点漏了字段，直接编辑文件修改]

[修改完后让 AI 同步 design 内部]
You: /opsx:apply design-sync
AI:  同步完成。你新增了 X 字段，已同步更新数据字典和权限定义。

[design 确认无问题后]
You: /opsx:continue
AI:  ✓ prd.md
     ✓ index.html
     ✓ tasks.md
     Ready for implementation.

You: /opsx:apply
AI:  [按 tasks 逐项填充 PRD 和 prototype]

You: /opsx:verify
You: /opsx:archive
```

---

## 场景四：你修改了 design 后的处理流程

**这是最关键的操作。** 你修改 design 后，需要两步：

**第一步：让 AI 同步 design 内部一致性**

```
You: /opsx:apply design-sync

AI:  同步完成。你修改了 X 字段落点，已同步更新：
     - 字段定义：补充字段属性
     - 权限定义：更新字段权限
     无冲突。
```

**第二步：重新生成下游产物**

```
You: /opsx:apply prd
AI:  基于同步后的 design 重新生成 PRD。

You: /opsx:apply prototype
AI:  基于同步后的 design 重新生成 prototype。

You: /opsx:verify
AI:  检查通过。PRD/prototype 完整继承了 design 的所有点。
```

---

## 场景五：同时处理多个系统的需求

```
[创建三个独立的需求]
You: /opsx:propose A-system-req-1
You: /opsx:propose B-system-req-1
You: /opsx:propose C-system-req-1

[在 A 上工作]
You: /opsx:apply A-system-req-1
AI:  [生成 A 的 PRD + prototype]

[中途切到 B]
You: /opsx:apply B-system-req-1
AI:  [生成 B 的 PRD + prototype]

[完成后分别验证和归档]
You: /opsx:verify A-system-req-1
You: /opsx:archive A-system-req-1
```

---

## 场景六：纯新系统（没有 specs 基线）

```
You: /opsx:propose system-d-mvp
AI:  Created openspec/changes/system-d-mvp/
     ✓ proposal.md — 新系统 D 的背景、目标、范围
     ✓ specs/system-d/spec.md — 系统 D 的首套规则（全 ADDED）
     ✓ design.md
     ✓ tasks.md

[后续正常流程]
You: /opsx:ff
You: /opsx:apply
You: /opsx:verify
You: /opsx:archive

[归档后，specs/system-d/spec.md 自动成为系统 D 的基线]
```

---

## 场景七：需求完成后复盘

```
You: /opsx:show A-system-batch-approve
AI:  [展示需求详情：对齐稿、design、PRD、prototype、tasks]

You: /opsx:list
AI:  [列出所有进行中的需求]
```

---

## 日常操作要点

1. **先对齐再展开** — proposal 阶段明确目标、范围、边界，不要跳过直接进入 design
2. **design 是唯一事实源** — PRD 和 prototype 必须完整继承 design 的每一个点
3. **修改 design 后先同步** — 用 `/opsx:apply design-sync` 让 design 内部一致，再重新生成下游
4. **完成后必验** — 用 `/opsx:verify` 检查是否有遗漏或引入新字段
5. **及时归档** — 需求关闭后 `/opsx:archive`，Delta 规格合入主库
