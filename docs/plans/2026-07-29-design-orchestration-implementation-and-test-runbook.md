# Design 编排实施与测试指令

日期：2026-07-29  
状态：待执行

> 历史作废说明：本文属于旧版 `design-orchestration-*` 方案，已被 `docs/plans/2026-07-29-park-quality-*` 系列方案取代，仅作历史审计材料，不作为当前实施依据。文中的在线测试脚本当前未实现、不可执行；本轮不运行。

本文是给新会话直接复制使用的执行指令。目标是先完成编排实现和零模型测试，再决定是否运行在线模型或真实项目。

## 一、执行原则

- 工作目录：`D:\work\ShitPM`
- 先读设计文档和测试方案，再改代码。
- 保留当前工作区已有修改，不重置、不清理、不覆盖。
- 不使用 Hook。
- 不执行 `git commit`。
- 不执行 `git push`。
- 在零模型测试通过前，不运行真实项目。
- 不把墙钟时间作为唯一性能结论，必须同时记录模型调用次数、输入文件、输入哈希和估算 token。

必读文件：

```text
D:\work\ShitPM\AGENTS.md
D:\work\ShitPM\docs\plans\2026-07-29-design-orchestration-context-governance.md
D:\work\ShitPM\docs\plans\2026-07-29-design-orchestration-low-cost-test-plan.md
D:\work\ShitPM\contracts\subagent-context-contract.md
D:\work\ShitPM\skills\spm-align\SKILL.md
D:\work\ShitPM\skills\spm-design\SKILL.md
```

---

## 二、新会话一：实施与零模型测试

将下面整段复制到新会话：

```text
在 D:\work\ShitPM 实施 Design 确定性编排和低成本测试方案。

先阅读：

- D:\work\ShitPM\AGENTS.md
- D:\work\ShitPM\docs\plans\2026-07-29-design-orchestration-context-governance.md
- D:\work\ShitPM\docs\plans\2026-07-29-design-orchestration-low-cost-test-plan.md
- D:\work\ShitPM\contracts\subagent-context-contract.md
- D:\work\ShitPM\skills\spm-align\SKILL.md
- D:\work\ShitPM\skills\spm-design\SKILL.md

目标：

1. 程序根据产物、依赖和哈希计算唯一下一动作；
2. 主代理不再自行规划 Design 完整模式的执行顺序；
3. 项目级材料准备在 Design 前完成并复用；
4. 材料未变化时不重复建立索引和事实提取；
5. 材料缓存命中时，Design 主路径只有三次核心模型动作：分析、挑战、写作与生成内自查；
6. 默认不执行第四次独立成品审查；
7. 下游失败不重跑有效上游；
8. 中断后可以从第一个无效依赖恢复；
9. 不把完整原始材料、完整规则包和完整阶段产物重新装入主对话；
10. 不使用 Hook，不建立后台常驻服务。

执行顺序：

第一步：检查工作区

- 执行 `git -C D:\work\ShitPM status --short`；
- 记录现有修改；
- 不删除、不重置、不覆盖已有修改；
- 不提交、不推送。

第二步：实现零模型控制平面

实现或完善：

- `next`、`accept`、`answer`、`status`；
- 运行输入快照；
- 产物依赖和哈希计算；
- 材料缓存复用和局部失效；
- 中断恢复；
- 规则包内容哈希复用；
- 阶段任务说明的输入白名单、输入哈希和输出约束；
- 自动修复次数和重复失败指纹边界。

先不要接真实模型调用，先让伪造宿主可以驱动编排器。

第三步：实现零模型测试

建议新增：

- `D:\work\ShitPM\scripts\python\test-design-orchestrator.py`
- `D:\work\ShitPM\scripts\python\test-design-orchestration-replay.py`
- `D:\work\ShitPM\scripts\python\fake-design-host.py`
- `D:\work\ShitPM\test-fixture\design-orchestration\`

伪造宿主只能读取编排器返回的当前动作、写入固定阶段产物、记录事件并接受动作，不能自行规划流程。

至少覆盖：

- `next` 每次只返回一个动作；
- 模式未指定时只询问一次；
- Align 不存在时仍可直接进入 Design；
- 材料未变化时事实提取次数为 0；
- 单个材料来源变化只使对应事实和下游失效；
- 下游失败不重跑有效上游；
- 检查脚本变化只重跑确定性检查；
- 中断后从第一个无效依赖恢复；
- 删除 `run.json` 后可从有效产物恢复；
- 旧产物哈希陈旧时拒绝错误恢复；
- 规则包按内容哈希复用；
- 任务说明输入白名单和输出约束有效；
- 自动修复在重复失败指纹下停止；
- 缓存命中时恰好三次核心模型动作；
- 默认没有第四次独立成品审查；
- 第一至第三层测试不产生任何模型调用。

第四步：运行零模型测试

```powershell
python -m compileall D:\work\ShitPM\scripts\python
python D:\work\ShitPM\scripts\python\test-design-orchestrator.py
python D:\work\ShitPM\scripts\python\test-design-orchestration-replay.py
python D:\work\ShitPM\scripts\python\test-context-loading.py
python D:\work\ShitPM\scripts\python\test-context-runtime.py
python D:\work\ShitPM\scripts\python\test-resource-integrity.py
python D:\work\ShitPM\scripts\python\test-shitpm-regression.py
python D:\work\ShitPM\scripts\python\test-anti-hallucination.py
```

如果新测试文件还没有实现，不要静默跳过，明确报告未完成原因。

第五步：实施阶段结束条件

只有满足以下条件才结束实施阶段：

- 零模型测试全部通过；
- 正常完整模式动作轨迹可重放；
- 缓存命中时核心模型动作数为 3；
- 不存在默认第四次独立成品审查；
- 下游失败不重跑有效上游；
- 中断恢复测试通过；
- 没有引入 Hook；
- 没有修改 Align 可选、Design 唯一事实源和双下游边界。

最终报告必须包含：修改文件、测试命令及结果、动作轨迹、模型调用次数、材料提取次数、未解决问题和当前 `git status --short`。
```

---

## 三、新会话二：独立审查与回归

会话一完成后，建议再开一个新会话，把下面内容复制进去：

```text
审查并测试 D:\work\ShitPM 当前已经完成的 Design 编排实施。

本会话只审查和测试，不修改代码、Skill、契约或模板，不提交、不推送。

先阅读：

- D:\work\ShitPM\AGENTS.md
- D:\work\ShitPM\docs\plans\2026-07-29-design-orchestration-context-governance.md
- D:\work\ShitPM\docs\plans\2026-07-29-design-orchestration-low-cost-test-plan.md

先检查：

```powershell
git -C D:\work\ShitPM status --short
git -C D:\work\ShitPM diff --stat
git -C D:\work\ShitPM diff --name-only
```

运行：

```powershell
python -m compileall D:\work\ShitPM\scripts\python
python D:\work\ShitPM\scripts\python\test-design-orchestrator.py
python D:\work\ShitPM\scripts\python\test-design-orchestration-replay.py
python D:\work\ShitPM\scripts\python\test-context-loading.py
python D:\work\ShitPM\scripts\python\test-context-runtime.py
python D:\work\ShitPM\scripts\python\test-resource-integrity.py
python D:\work\ShitPM\scripts\python\test-shitpm-regression.py
python D:\work\ShitPM\scripts\python\test-anti-hallucination.py
```

重点审查：

1. `next` 是否每次只返回一个动作；
2. 是否存在主代理自行规划流程的回退路径；
3. 材料命中缓存后是否仍重复读取原始材料；
4. Design 主路径是否超过三次核心模型动作；
5. 是否错误执行第四次独立成品审查；
6. 挑战或写作失败时是否错误重跑上游；
7. 删除 `run.json` 后是否能恢复；
8. 旧哈希产物是否可能被错误复用；
9. 任务说明是否允许读取未授权目录；
10. 宿主无法证明的上下文隔离是否被错误标记为自动通过；
11. 是否重新引入 Hook；
12. 是否改变 Align 可选、Design 唯一事实源或双下游边界。

按 P0/P1/P2/P3 输出问题。每个问题必须包含事实证据、复现步骤、根因、影响和建议修复范围。

零模型测试全部通过后，只报告“可以进入在线合成冒烟”，不要自动运行在线模型和真实项目。
```

---

## 四、在线合成冒烟指令

只有新会话二明确确认可以进入在线测试后，才执行下面指令：

```text
在 D:\work\ShitPM 执行小型合成项目在线冒烟。

前置条件：

- 零模型测试全部通过；
- 现有回归测试全部通过；
- 不使用真实项目；
- 不连续重跑；
- 不提交、不推送。

先测试材料冷启动和复用：

```powershell
# 当前未实现、不可执行；本轮不运行。以下仅保留历史命令示意。
# python D:\work\ShitPM\scripts\python\test-design-orchestration-online.py --scenario material-cold-start
# python D:\work\ShitPM\scripts\python\test-design-orchestration-online.py --scenario material-reuse
```

必须确认：

- 首次运行生成材料事实资产；
- 相同材料第二次运行时，材料事实提取次数为 0；
- 材料提取和 Design 核心调用分开计数。

再测试 Design 主路径：

```powershell
# 当前未实现、不可执行；本轮不运行。以下仅保留历史命令示意。
# python D:\work\ShitPM\scripts\python\test-design-orchestration-online.py --scenario design-main-path
```

必须确认：

- Design 分析 1 次；
- 业务模型挑战 1 次；
- Design 写作与生成内自查 1 次；
- 核心模型调用总数恰好为 3；
- 没有第四次独立成品审查；
- 三个动作使用独立执行实例；
- 主对话没有读取完整原始材料和完整阶段产物；
- 每个动作都有输入哈希和执行事件记录。

宿主无法提供的历史继承信息或实际读取日志，必须标记为证据缺失，不能标记为上下文隔离通过。
```

---

## 五、真实项目验收指令

在线合成冒烟通过后，再为真实项目单独开会话。真实项目只执行：

1. 一次冷启动；
2. 一次相同材料版本的恢复或复用运行。

不得连续多次冷启动。必须记录：

- 材料版本；
- 动作轨迹；
- 每个动作的输入文件、哈希和估算 token；
- 材料事实提取次数；
- 三类 Design 核心调用次数；
- 独立成品审查次数；
- 失败、重试和局部修复次数；
- 是否读取完整原始材料；
- 是否继承父对话历史；
- 最终 Design 质量结果；
- 与旧运行的耗时和调用量对比。

总耗时只能和上述证据一起解释，不能单独作为结论。

## 六、执行顺序摘要

```text
新会话一
  -> 实施控制平面
  -> 实现伪造宿主和零模型测试
  -> 运行第一至第三层测试

新会话二
  -> 不改代码
  -> 独立审查实现
  -> 重跑零模型回归
  -> 确认是否允许在线冒烟

新会话三
  -> 小型合成项目在线冒烟
  -> 材料冷启动与复用
  -> Design 三次核心调用验证

新会话四
  -> 真实项目一次冷启动
  -> 真实项目一次复用或恢复
  -> 发布级验收
```
