# 项目级材料摄取实施设计

日期：2026-07-29  
状态：实施中（首轮材料资产与输入边界已落地）
基准：`2026-07-29-real-orchestration-audit.md`、`2026-07-29-project-material-intake-design.md`

## 1. 目标与边界

### 1.1 目标

本设计只解决两个性能问题：

1. 减少同一材料版本被模型重复读取；
2. 减少 Align、Design、挑战、写作和验证之间的上下文重复传递。

目标状态：

```text
同一来源版本
  -> 一次材料事实读取
  -> 可复用材料资产
  -> Align / Design / PRD / Review / Fix 读取压缩事实
```

这里的“一次”具体指：同一个来源文件或索引片段版本只进入材料事实提取上下文一次。大型材料允许按不重叠的来源边界分批，但禁止同一来源片段跨批次重复注入。

### 1.2 不在本次范围内

- 不改变 Design 的产品责任：Design 仍然负责产品定义和唯一 Design 基线；
- 不把材料事实包变成产品事实源；
- 不把 Align 改成硬前置；
- 不通过增加上下文压缩次数解决问题；
- 不通过增加子代理数量解决问题；
- 不引入 Hook；
- 不改变 PRD 和 Prototype 的现有产品契约；
- 不在材料摄取阶段决定角色、权限、流程、状态、模块边界或系统方案。

## 2. 目标架构

### 2.1 项目级材料资产

材料资产从阶段上下文中独立出来：

```text
.workflow/runtime/materials/
├── manifest.json
├── source-index.json
├── facts.json
└── runs/
    └── <run-id>.json
```

阶段运行资产仍然保留：

```text
.workflow/runtime/context/<stage>/
├── packs/
├── handoff/
└── run.json
```

两者不得混用：

- `materials/`：跨阶段复用的材料资产；
- `context/<stage>/`：本次阶段运行的短交接和规则包；
- `output/`：面向用户的阶段产物。

### 2.2 责任分层

```text
宿主预检
  -> 检查材料版本
  -> 材料未变化：复用材料资产
  -> 材料变化：执行项目级材料摄取
       ├─ 确定性文件扫描、哈希、索引
       └─ 隔离材料事实读取
            -> facts.json

Align（可选）
  -> manifest.json + facts.json + 用户本轮文字

Design
  -> facts.json + align.md（如存在）+ 用户确认 + Design规则短包
       -> design-model.json
       -> 隔离 Design Challenger
       -> design-challenge.json
       -> Design 写作
       -> 机器验证
```

关键变化是：**材料摄取成为宿主在阶段启动前保证的项目资产，不再是 Design 内部临时追加的步骤。**

## 3. 材料资产定义

### 3.1 `manifest.json`

记录材料版本和来源清单，不承载业务结论：

```json
{
  "version": 1,
  "material_revision": "sha256-of-sorted-source-hashes",
  "generated_at": "2026-07-29T00:00:00Z",
  "sources": [
    {
      "source_id": "source-001",
      "path": "V1/智慧服务区-智慧停车区PRD文档V1.0_20260323.md",
      "sha256": "...",
      "lines": 1032,
      "characters": 0,
      "segments": 0,
      "status": "active"
    }
  ]
}
```

规则：

- `source_id` 在路径稳定时保持稳定；
- `sha256` 变化即视为来源版本变化；
- `material_revision` 由排序后的来源 ID、路径和哈希计算，不使用时间戳；
- 只要来源集合、路径或内容发生变化，就不能静默复用旧事实包；
- 用户本轮文字如果不是文件材料，作为单独的 `user-input` 来源记录，不能与历史文件事实混淆。

### 3.2 `source-index.json`

只做定位和体量信息：

```json
{
  "version": 1,
  "material_revision": "...",
  "files": [
    {
      "source_id": "source-001",
      "path": "V1/智慧服务区-智慧停车区PRD文档V1.0_20260323.md",
      "sha256": "...",
      "segments": [
        {
          "segment_id": "source-001-seg-003",
          "title": "车流实时监控",
          "line_start": 189,
          "line_end": 348,
          "keywords": ["车流", "车型", "停靠时间"],
          "tokens": 0
        }
      ]
    }
  ]
}
```

索引不能决定：

- 哪个角色应该拥有什么权限；
- 哪个状态可以回退；
- 哪个功能必须建设；
- 哪个方案更合理。

### 3.3 `facts.json`

只记录材料层事实和事实缺口：

```json
{
  "version": 1,
  "material_revision": "...",
  "facts": [
    {
      "fact_id": "fact-001",
      "statement": "V1 文档描述通过卡口摄像头采集车辆进出信息",
      "status": "source-stated",
      "source_refs": [
        {
          "source_id": "source-001",
          "line_start": 13,
          "line_end": 24,
          "sha256": "..."
        }
      ]
    }
  ],
  "conflicts": [],
  "unknowns": [],
  "non_derivable_items": [],
  "coverage": {
    "source_count": 0,
    "fact_count": 0,
    "conflict_count": 0,
    "unknown_count": 0
  }
}
```

`facts.json` 不允许出现以下内容作为已确认事实：

- “系统应该采用某种架构”；
- “某个角色必须拥有某项权限”；
- “某个告警必须自动关闭”；
- “某个状态应该允许回退”；
- “某个模块必须纳入一期”。

这些属于 Design 决策，必须回到 Design 处理。

### 3.4 `runs/<run-id>.json`

记录一次材料摄取的执行证据：

```json
{
  "run_id": "...",
  "material_revision": "...",
  "started_at": "...",
  "completed_at": "...",
  "changed_sources": [],
  "reused_sources": [],
  "reader_batches": [],
  "facts_path": ".workflow/runtime/materials/facts.json",
  "status": "completed"
}
```

该文件是审计记录，不是下游事实输入。

## 4. 材料摄取生命周期

### 4.1 首次运行

```text
检查 manifest.json
  -> 不存在
  -> 扫描用户明确提供的材料
  -> 计算哈希和索引
  -> 隔离材料事实读取
  -> 写入 manifest、source-index、facts、run
  -> 进入 Align 或 Design
```

材料摄取过程中不进入用户交互，不询问产品决策问题。材料事实中的冲突和缺失只被记录，留给 Align 或 Design 处理。

### 4.2 材料未变化

```text
检查 manifest.json
  -> 来源集合和哈希完全一致
  -> 直接复用 facts.json
  -> 不重新读取原始材料
  -> 不重新启动材料事实读取
```

确定性哈希检查可以每次执行，因为它不会把原文注入模型上下文。

### 4.3 部分材料变化

```text
比较新旧 manifest
  -> 未变化来源：复用旧事实
  -> 新增或变化来源：重新建立索引并读取一次
  -> 删除来源：移除其事实
  -> 重新计算跨来源冲突
  -> 生成新的 material_revision 和 facts.json
```

变化来源不能继续使用旧的事实；未变化来源不应被重新送入模型。

### 4.4 用户要求强制重读

用户明确要求“重新核对原文”时，生成新的材料运行记录。即使哈希没有变化，也必须在审计中标记为 `forced_refresh`，不能让强制重读看起来像普通缓存命中。

## 5. 阶段输入边界

### 5.1 Align

允许输入：

```text
manifest.json
facts.json
用户本轮明确文字
Align规则短包
```

默认禁止输入：

```text
原始材料全文
完整历史对话
完整 Design
其他阶段完整输出
```

例外：用户要求核验，或者事实冲突必须定位时，只读取指定来源的指定行范围。

### 5.2 Design分析

允许输入：

```text
facts.json
align.md（如存在）
用户最新确认
Design Core规则
完整模式规则
适用场景卡
```

Design分析首先生成：

```text
.workflow/runtime/context/design/handoff/design-model.json
```

主 Agent 不再从 V1 原文重新提取基础事实。遇到事实冲突时，读取 `facts.json` 中的来源定位，而不是重新全文扫描材料目录。

### 5.3 Design挑战

Challenger 只接收：

```text
design-model.json
facts.json
适用场景卡
挑战要求
```

允许按来源定位补读原文，但必须记录补读原因、来源和行范围。不得接收：

- 主 Agent完整历史对话；
- 完整 Align；
- 完整 Design 草稿；
- 未经筛选的原始材料目录。

### 5.4 Design写作

写作上下文由以下内容组成：

```text
design-model.json
design-challenge.json
facts.json 中被引用的事实摘要
Design写作规则
必要的用户确认
```

写作阶段不再读取完整 V1，也不再读取完整历史对话。

### 5.5 Design验证

验证分成两类：

1. 机器验证：直接读取 `design.md` 和结构化运行结果，输出短机器结论；
2. 业务复核：读取 `design-model.json`、`design-challenge.json` 和 Design 必要章节。

验证脚本源码、规则原文和完整 Design 不应同时作为一个模型调用的输入。

## 6. 子代理边界

完整模式的主路径固定为：

```text
材料版本检查
  -> Material Reader（隔离上下文）
  -> 主 Agent Design分析
  -> Design Challenger（隔离上下文）
  -> 主 Agent写作和最终裁决
```

### Material Reader

输入：

- 当前材料版本的索引片段；
- 对应原始来源行范围；
- 事实提取要求。

输出：

- `facts`；
- `conflicts`；
- `unknowns`；
- `non_derivable_items`；
- 来源证据。

禁止：

- 读取完整历史对话；
- 生成产品方案；
- 修改 Design；
- 直接决定一期范围、流程、权限和状态。

### Design Challenger

输入：

- `design-model.json`；
- `facts.json`；
- 适用场景卡；
- 用户已确认的硬要求。

输出：

- 缺口；
- 跨层冲突；
- 必须确认项；
- 证据和影响范围。

禁止：

- 修改 `design.md`；
- 生成正式 Review 结论；
- 代替主 Agent做最终产品决策；
- 重新读取全部原始材料。

## 7. 当前改动的处理清单

以下清单针对当前工作区已有的上下文相关改动，实施时必须按“删除旧链路、保留必要能力”的原则处理。

| 路径 | 处理方向 | 原因 |
|---|---|---|
| `skills/spm-design/SKILL.md` | 重写 D0；删除 Design 内材料索引和默认原文读取；改为读取项目级材料资产 | 当前版本把摄取责任叠加进 Design |
| `skills/spm-align/SKILL.md` | 增加材料资产预检和复用说明；删除重复全文读取要求 | Align 只消费材料资产，仍保持可选 |
| `contracts/subagent-context-contract.md` | 保留隔离输入输出约束；改为 Material Reader 消费材料资产片段 | 子代理必须在主要读取阶段就隔离，而不是后半程补调用 |
| `scripts/python/source-index.py` | 保留索引能力，迁移到项目级材料资产目录；增加哈希、版本和增量复用 | 索引能力有价值，但不能挂在 Design D0 |
| `scripts/python/context-runtime-check.py` | 拆分材料资产检查和阶段交接检查；检查 `materials/`，不把材料事实绑定到 Design 目录 | 当前检查器假设材料资产位于 Design 上下文 |
| `scripts/python/context-pack.py` | 保留规则包编译、体量和运行指标；删除其对业务材料的隐式依赖 | 规则包和材料事实必须分离 |
| `scripts/python/stage-context.py` | 从 Design 最小读取集合中移除材料摄取脚本；只保留阶段确实需要的规则编译和验证脚本 | 防止每次 Design 都重新装载摄取实现 |
| `scripts/python/context-run.py` | 不作为 Design 材料摄取步骤；若只用于指标，迁移为独立指标记录，不进入模型上下文 | 当前新增运行记录不能成为新的长链路步骤 |
| `scripts/python/test-context-runtime.py` | 扩展为材料版本复用、变更失效和阶段输入边界测试 | 仅验证文件存在不能证明性能目标 |
| `docs/plans/2026-07-29-project-material-intake-design.md` | 保留为责任模型基准 | 已确认项目级责任方向 |
| `docs/plans/2026-07-29-real-orchestration-audit.md` | 保留为真实运行证据和旧链路删除依据 | 防止实施时只加不减 |

本表不是立即执行清单。代码修改必须在本设计再次确认后进行。

## 8. 实施顺序

### 第一步：先建立材料资产，不接入 Design

实现并测试：

- manifest 生成；
- source-index 生成；
- material_revision 计算；
- unchanged 命中；
- changed source 增量失效；
- facts 结构和来源定位检查。

验证方式：使用当前智慧停车区样例，第二次运行必须证明没有再次生成材料事实。

### 第二步：迁移 Material Reader

将完整模式的材料事实读取从 Design 主路径移到项目级材料摄取入口。主 Agent不再负责首次原文读取。

验证方式：记录 Material Reader 的输入来源，检查同一 source_id 和 sha256 是否只出现一次。

### 第三步：缩短 Align 和 Design 输入

先改变 Skill 和上下文装载边界，再删除旧的原文读取指令。不能先保留旧路径再新增资产路径。

验证方式：生成阶段输入清单，确认 Design 输入不包含原始材料全文。

### 第四步：接入隔离挑战

Design 先生成短的 `design-model.json`，再启动 Challenger。Challenger 完成后，主 Agent只读取短的 `design-challenge.json`，不读取 Challenger 全部过程历史。

验证方式：挑战输入和输出均能单独统计 token，且不存在完整历史对话字段。

### 第五步：收紧写作和验证

写作只消费模型交接和挑战交接；验证优先由程序完成，业务复核只读取必要章节。

验证方式：检查写作和验证阶段的输入包大小及原始来源出现次数。

### 第六步：使用同一真实样例回放

不先用人工构造小样例宣称提速。必须使用原始运行对应的智慧停车区材料，比较：

- 原始材料模型读取次数；
- 主 Agent输入 token；
- 子代理输入 token；
- 总输入 token；
- 上下文压缩次数；
- Design阶段耗时；
- 本地命令耗时；
- 生成质量和未决项数量。

## 9. 验收标准

### 功能和边界

- Align仍然可选；
- 直接进入 Design时，宿主可以先完成无交互材料资产检查或摄取；
- Design不负责建立项目级材料索引；
- Design确认后的 `output/design/design.md` 仍是产品事实基线；
- 材料事实不能绕过用户确认直接成为产品决策；
- Material Reader和Design Challenger不能修改最终 Design。

### 复用和失效

- 材料未变化：复用 `facts.json`，不启动材料事实读取；
- 新增材料：只读取新增来源；
- 修改材料：只读取修改来源，并重新审计跨来源冲突；
- 删除材料：删除其事实引用并生成新的材料版本；
- 强制重读：记录为显式刷新，不伪装成缓存命中。

### 性能

首轮验收目标：

- Design默认输入不超过模型窗口的 35%～50%；
- 原始材料全文在 Design、PRD、Review、Fix默认输入中出现次数为 0；
- 同一来源版本在材料事实读取中只出现一次；
- 总输入 token 相对真实旧链路下降 50%以上；
- 上下文压缩次数明显下降，而不是通过增加压缩次数维持运行；
- Design主路径不再出现“读取原文—写入—再读取原文”的循环。

性能目标若未达到，优先检查旧链路是否仍被调用，不先增加缓存、压缩或子代理。

## 10. 实施确认记录

本设计已按用户确认开始实施，落实的原则是：

> 新材料链必须替换旧读取链，不得与旧链路并存。

本轮实施顺序：

- 先建立项目级材料资产、版本复用和变更失效；
- 再切换 Align / Design 的输入边界，删除 Design 默认材料索引脚本；
- 本轮不提交、不推送；真实样例回放作为下一轮验收，不以小样例结果代替。
