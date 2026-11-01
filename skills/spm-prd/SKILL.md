---
name: spm-prd
description: "PRD 阶段：根据 Design 事实闭包生成研发可评审的 PRD。触发于用户要求生成 PRD、需求规格或需求文档；按模块概览、对象单元、共用规则、页面功能和跨对象异常组织，保持 Design 语义，不依赖 Prototype，不把高影响未决事实静默拍板；成功后记录 PRD 模块依据。"
---

## 事实源与职责

设计集清单登记的正式 Design 文件（系统级基线、跨模块契约、模块设计）是唯一产品事实体系。Prototype、旧 PRD、示例和通用经验只能帮助理解，不能覆盖或补造 Design 事实。`output/prd/prd.md` 是交付物，不是事实源。PRD 与 Prototype 互不作为前置。

`references/prd-writing-rules.md` 是模块详细需求的唯一写作规范。`templates/prd.md` 提供骨架，`references/prd-writing-examples.md` 提供一个真实样板，`output/verification/<业务闭环或模块名>.md` 供作者核对规则和数值。样板和验证包都不能成为 PRD 的阅读依赖。

PRD 完成后，后端只读当前模块就能确定对象、状态、规则、写入、失败保留和终态；前端只读页面功能就能确定页面任务、区块、字段、操作、反馈和结果；测试只读验收场景就能取得带输入、预期和精度的用例。

## 开始前检查

1. 确认 `output/design/设计地图.md` 和 `output/design/设计集清单.json` 存在、可解析，清单能定位目标模块。
2. 运行 `python $BUNDLE/scripts/python/stage-context.py --project-root .`。`design_change.active` 必须为 `false`；存在活动事务时先执行 `design-set.py recover` 并复查。
3. 按 `$BUNDLE/contracts/context-loading.manifest.json` 装载目标模块事实闭包和写作上下文：

~~~text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass module [--card <scenes|data>] --module <模块名>
~~~

完成条件：命令成功返回，只包含目标模块事实闭包、对象单元规范、适用场景卡和真实样板；模块名与设计集清单登记名称一致。

## 执行模式

写作前明确模式：

- 首次生成：目标 PRD 尚不存在，按模块分片生成。
- 重新生成：用户明确要求重跑、整体重写，或质量问题涉及多个对象或页面时，从模块概览到跨对象异常整体重写。
- 局部修复：只修改用户指定对象、页面、动作或问题。
- 中断恢复：从最后一个未完成模块继续；运行时规则变化时，受影响模块重新生成。

所有 PRD 统一按模块分片。Subagent 只能并行读取材料或分析模块，没有最终写入权。

## 阶段 A：全局扫描

建立目标范围、系统边界、角色权限与数据范围、核心业务对象、对象关系、共用规则、页面清单、流程图适用性和待确认事项的导航视图。

读取设计地图和设计集清单。需要页面、状态、字段和操作摘要时运行 `python $BUNDLE/scripts/python/design-index.py compile --project-root .`，不把索引全文粘贴进上下文。

模块写作前比较状态表、页面操作和字段校验。同一高影响事实口径不兼容时停止该模块并回到 Design Fix，不自行裁决。
完成条件：导航视图完整；高影响冲突已处理或明确转回 Design。

## 阶段 B：建立最终 PRD 骨架

创建或维护 `output/prd/prd.md`，写入文档信息、产品概述、总体说明、功能模块标题和模块内实际存在的章节。运行：

~~~text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass writing
~~~

按 `templates/prd.md` 建立模块概览、对象单元、共用规则、页面功能和跨对象异常的位置。对象单元按 Design 业务对象建立，共用规则和跨对象异常按需建立，不创建空章节，不按旧固定编号补占位。

未知对象、状态、页面或字段先回 Design 核对。不得用“待补充”“待定”占位。
完成条件：最终骨架无空章节，页面和对象标题与 Design 名称一致，写作上下文成功装载。

## 阶段 C：模块分片写入

每次只处理一个业务模块。运行：

~~~text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage prd --pass module [--card <scenes|data>] --module <模块名>
~~~

模块 pass 固定装载对象单元规范和一个真实样板；有数据计算时追加 `data` 卡，需要语义自检时追加 `scenes` 卡。不得一次读取整套 Design，不把无关模块内容带入上下文。

按 `references/prd-writing-rules.md` 写当前模块：

- 模块概览只建立对象关系、角色能力和页面导航。
- 每个对象使用固定六个槽位，不增加同义章节。
- 共用规则只在多个对象或页面共同使用且放入任一对象会重复时建立。
- 页面功能按 Design 页面逐页写，区块标题不带对象归属或只读标注。
- 跨对象异常只写对象之间的异常传播、事务边界、部分失败和恢复。
- 命中流程图适用条件时，流程图放在对象业务过程正文后，路径为 `output/prd/diagrams/`；纯查询、无状态变化且无跨角色协作的对象不强制绘图。

验收场景直接写输入、预期和精度，不写规则 ID、验证包位置或追溯说明。同一组数值只在验收场景出现一次。不写作者说明、过程记录、空章节和重复定义。

本阶段固定自检：

1. 后端能确定对象起点、状态、规则、写入、失败保留和终态。
2. 前端能确定页面任务、区块、字段、操作、反馈和结果去向。
3. 测试能直接取得带输入、预期和精度的场景。
4. 每条事实只有一个完整归属位置。
5. 页面、对象和跨对象关系不依赖章节编号或外部文件才能理解。
6. 空章节、规则 ID、对象标注、过程说明和重复数值例子均不存在。

发现摘要化、事实断裂、跨章拼接、正文追溯或多种合理解释时，重写对应位置并重新回读。
完成条件：当前模块的对象、页面、状态、规则、异常和验收场景均可在正文定位；数据计算已按 `data` 卡核对。

## 阶段 D：有限范围整合

只处理模块编号、标题层级、名词、页面引用、对象名、跨模块状态和实际存在的待确认。页面名保持 Design 原名。PRD 必须自包含：确认规则直接写清，内部引用只指向当前 `prd.md` 的真实标题。

合并后发现重复事实时，保留一处完整定义，其他位置改为对象名、状态名、入口或本页新增反馈。
完成条件：标题、对象名、页面名和内部引用可定位；正文没有新增未授权事实。

## 最终检查与交付

最终顺序固定：最后一次修改正文和适用流程图 → 回读受影响模块 → 运行检查 → 修复真实问题 → 如再次修改则重新回读 → 内容不再变化后更新 `.workflow/status.json` → 交付前再次阅读真实 `prd.md`。

按顺序运行：

~~~text
python $BUNDLE/scripts/python/prd-style-lint.py output/prd/prd.md
python $BUNDLE/scripts/python/prd-consistency-check.py --project-root . --module <模块名>
~~~

- lint 返回 1 时必须修复；warning 和 info 逐项判断；退出码 0 不表示语义通过。
- consistency 的 `deterministic_conflict` 返回 1 时必须修复；`possible_omission` 和 `needs_semantic_judgment` 由 AI 对照 Design 判断；`ok` 仍需阅读。
- 无法提取、无法判断或检查通过时都不得写“零歧义”。

## 记录模块依据

模块成功生成或同步后写入 PRD 模块依据：

~~~text
python $BUNDLE/scripts/python/design-set.py record-inputs --project-root . --artifact prd --target-id prd:<模块名> --target-name <模块名> --output-path output/prd/prd.md --output-locator <PRD 模块标题> --inputs <本次实际读取的 Design 文件 ID，逗号分隔>
~~~

`--inputs` 必须来自本次实际事实闭包。语义变化后的模块同步完成后，provenance 和 status 应反映最新内容。

## 输出与停止边界

只写入 `output/prd/prd.md`、必需流程图的 `output/prd/diagrams/*.drawio` 与 `*.png`、`.workflow/provenance/prd.json`，并更新 `.workflow/status.json`。

PRD 完成后停在交付点，不自动触发 PRD Review 或 Prototype。不能据此宣布研发无歧义、逻辑零缺陷或所有项目适用；关键模块仍需研发任务式试读。Design 缺失、活动事务未恢复、输入不可解析或高影响事实缺失时停止并报告。