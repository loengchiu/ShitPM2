# 上下文装载架构批次 0—3 基线报告

- 日期：2026-07-28
- 项目：ShitPM
- 设计基准：`docs/plans/2026-07-28-context-loading-architecture-design.md`
- 执行状态：已按用户确认执行；本报告与设计稿是正式架构记录，当前工作区未执行 Git commit 或 Git push

## 1. 结论

本批次已把 Design / PRD 的规则装载从“执行前读取多份规则文件”改为“按阶段、模式、分析遍次和命中卡片编译稳定章节上下文包”。规则仍以原 reference 为权威来源，没有维护第二份人工规则摘要。

PRD 规划包在拆分写作规则后为 **6,664 字符**，相对于当前 PRD 静态规则基线 **12,970 字符**，约为 **51.4%**，低于设计目标约 65%。完整 Design 写作包为 **10,877 字符**，相对于当前 Design 静态规则基线 **21,756 字符**，约为 **50.0%**，低于设计目标约 70%。

这些比例只衡量规则上下文，不包含业务输入、Design / PRD 正文和模型输出；当前 token 使用中英文混合保守启发式估算，仅用于显式预算检查和回归比较，不能替代目标模型 tokenizer 或质量验收。

## 2. 实施内容

### 2.1 稳定章节标记

为 Design、PRD 的 reference 和模板增加稳定的 `context:<id>:start/end` 标记。运行时只提取被 manifest 显式选择的章节，不再把整个 reference 文件作为默认输入。

### 2.2 上下文装载 manifest

新增 `contracts/context-loading.manifest.json`，定义：

- Design：核心规则、模式规则、专项卡、写作、输出、生成内审查、兼容规则；
- PRD：核心边界、结构规则、动作规则、名词、版本记录、专项场景、示例、生成内审查；
- 示例必须通过 `--example` 命中，不参与规范性规则判断；
- 强制规则由显式 pack、模式和适用性卡选择，不由普通相似度检索决定。

### 2.3 上下文工具

新增或接入以下工具：

- `scripts/python/context-pack.py`：编译上下文包，记录来源哈希、章节哈希和运行记录，并支持陈旧检查；
- `scripts/python/context-budget.py`：统计规则、业务输入和运行时上下文的字符、行数和估算 token；
- `scripts/python/test-context-loading.py`：检查 manifest、章节标记、来源、去重、陈旧运行包和产品边界；
- `scripts/python/prototype-structure.py`：提取 Prototype 结构摘要，避免 PRD 阶段默认全文读取 HTML。

### 2.4 多遍执行边界

- Design：分析、挑战、写作、生成内审查使用不同上下文包；
- PRD：规划、模块写作、全局整合、生成内审查分开装载；
- 主 Agent 保持全局业务模型、冲突裁决、最终写入和确定性检查所有权；
- Sub-agent 仅允许承担材料阅读、独立挑战、模块草稿和模块验证等有边界工作，不能直接写最终 Design / PRD；
- 当前未实际启动 Sub-agent，这是普通任务默认不启用的有意策略。

## 3. 体量测量

### 3.1 实施前 HEAD 基线

| 范围 | 字符 | 行数 | 粗略 token |
| --- | ---: | ---: | ---: |
| Design 静态规则 | 19,933 | 857 | 4,984 |
| PRD 静态规则（不含示例） | 12,381 | 482 | 3,096 |
| PRD 示例全文 | 6,567 | 260 | 1,642 |

### 3.2 当前静态源文件基线

当前静态源文件包含稳定标记，因此比 HEAD 略大；增加的体量是装载索引开销，不是规则复制。

| 范围 | 字符 | 行数 | 粗略 token |
| --- | ---: | ---: | ---: |
| Design 静态规则 | 21,756 | 897 | 5,443 |
| PRD 静态规则（不含示例） | 12,970 | 496 | 3,246 |
| PRD 示例全文 | 7,477 | 280 | 1,870 |

### 3.3 典型 Design 运行包

| 遍次 | 选择 | 字符 | 相对当前 Design 静态基线 |
| --- | --- | ---: | ---: |
| 简单模式分析 | `analysis` + `simple` | 2,143 | 9.9% |
| 完整模式分析 | `analysis` + `full` | 4,036 | 18.6% |
| 完整模式写作 | `writing` + `full` + `state` + `permissions` | 10,877 | 50.0% |
| 完整模式生成内审查 | `verification` + `full` + `state` + `cross-system` | 8,004 | 36.8% |

### 3.4 典型 PRD 运行包

| 遍次 | 选择 | 字符 | 说明 |
| --- | --- | ---: | --- |
| 规划 | `plan` | 6,664 | 相对 PRD 静态规则基线 51.4% |
| 模块写作 | `module` + `scenes` + `complex-action` + `action-body` | 10,472 | 同时含专项场景和命中示例；相对“规则+示例”基线 51.2% |
| 全局整合 | `integration` | 11,444 | 刻意加载完整整合所需规则，不与模块写作的预算混为一谈 |
| 生成内审查 | `verification` | 9,286 | 仅加载整合审查所需规则 |

PRD 规则原先将 6.1—6.4 作为一个大章节；本批次已拆为 `prd-writing-structure` 和 `prd-writing-action`。因此规划包不再提前加载动作正文规则、名词规则和版本记录规则。

## 4. 验证结果

以下检查已通过：

```text
python scripts/python/test-context-loading.py
python scripts/python/test-resource-integrity.py
python -m py_compile scripts/python/context-pack.py scripts/python/context-budget.py scripts/python/test-context-loading.py scripts/python/prototype-structure.py scripts/python/stage-context.py
git diff --check
python scripts/python/test-shitpm-regression.py
python scripts/python/test-anti-hallucination.py prepare
python scripts/python/test-anti-hallucination.py verify
python scripts/python/test-anti-hallucination.py clean
python scripts/python/state-machine-check.py --project-root . --source auto
```

结果：

- 上下文装载测试通过；
- 资源完整性检查通过；
- Python 编译检查通过；
- `git diff --check` 通过；
- ShitPM 回归测试：36 项通过，0 项失败；
- 反幻觉测试：4 类预期幻觉全部检出；
- 状态机检查：结构检查通过，当前 Design 仅报告 1 个 P2 提示：初始态由 `draft` 行首推断，未阻断。

Prototype 结构提取已在当前 `output/prototype/index.html` 上运行成功。

## 5. 产品边界检查

本批次没有修改以下产品事实源：

- `output/design/design.md`
- `output/prd/prd.md`
- `output/shitpm-v2-prd.md`
- `output/shitpm-v2-implementation-design.md`

上下文运行包、来源哈希、metadata 和 Sub-agent 交接信息均不进入 Design / PRD 最终产物。`decision-notes.md` 仍只用于过程审计，不作为下游事实输入。

## 6. 尚未做的事情

1. 没有基于本次架构重新生成业务 Design 或 PRD；本批次目标是执行上下文装载架构，不是改写现有产品事实。
2. 没有把 Sub-agent 强制引入普通 Design / PRD；复杂项目可以按契约显式启用，普通项目不增加编排成本。
3. 字符数预算没有证明推理质量一定提升；后续仍应以完整模式 Design 的业务模型覆盖、跨层一致性和已知失败样例回归为高优先级验收条件。
