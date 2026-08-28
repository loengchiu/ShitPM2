---
name: spm-design
description: "产品设计——用于生成或修改 ShitPM 多文件 Design：先完成或复用 Align，再按用户选择的 simple 或 full 模式形成唯一产品事实体系。full 模式承担 A/B/C 责任；最终写作无损整合来源事实并在同一动作内回读修正。"
---

## 1. 定位与事实源

从系统 prompt 的 ShitPM bundle root 段读取 $BUNDLE。bundle 资源使用 $BUNDLE/，.workflow/ 和 output/ 使用当前项目根目录。

spm-design 同时承担产品定义和唯一 Design 基线。Design 是多文件产品事实体系，目录固定为：

~~~text
output/design/
├── 设计地图.md          低分辨率导航：系统目标与边界、主业务链、模块与职责、跨模块契约入口
├── 设计集清单.json      机器定位：稳定 ID、路径、类型、依赖、指纹、决策状态
├── 系统级基线/          删除某模块后仍成立：系统边界、核心对象、生命周期、角色、权限、数据范围
├── 跨模块契约/          只在模块交接时成立：触发、输入输出、状态衔接、失败和人工处理
└── 模块设计/            只影响一个模块内部：模块流程、页面、字段、操作、局部状态、规则、异常和验收
~~~

不再生成 design.md、decision-notes.md、确认标记或合并视图。每项正式事实只有一个归属处；判断方法：删除某模块后仍成立放系统级基线，只在交接时成立放跨模块契约，只影响一个模块内部放模块设计。

Design 面向产品经理，描述目标、范围、业务闭环、角色、权限、数据范围、状态、页面、字段、操作、异常、验收和实际适用的产品级非功能要求。不写数据库、接口实现、缓存、队列、Hook 或其他未经产品要求的实现机制。

## 2. 必经 Align 与模式选择

1. 每次首次生成 Design，或用户原话、回答、材料版本发生实质变化时，先在当前 Design 任务内完成或复用 Align：

- 有效 Align 可复用，不重复追问；
- 没有原始材料也必须继续，使用用户描述和回答形成需求事实；
- 有材料时优先读取材料索引和可定位事实；索引不足或存在冲突时定点核对原文，output/align/align.md 只作为对齐索引；
- Align 需要高影响回答时暂停 Design，回答写回当前 Align 后再继续；
- 用户不需要退出后手工再次调用 /spm-align。

Align 不是最终 Design，不新增用户未确认的高影响流程、状态、权限、数据范围、边界或方案；它必须保留材料已有的页面、字段、操作、枚举、规则、状态、异常和验收。

完成条件：Align 可读取且绑定当前输入版本；事实、冲突、推测和未知已分开；需要回答的高影响问题已回答，或用户已明确接受带未决边界继续。

2. 只保留两种用户模式：

- simple：单一主流程、角色少、业务关系简单；
- full：多角色、审批、状态、数据隔离、跨系统或存在明显方案权衡。

模式必须由用户选择；未明确时只询问一次，不根据材料数量、关键词、历史产物或模型自动切换。

完成条件：当前任务明确记录为 simple 或 full；未获得用户选择前不正式写入 Design。

## 3. 上下文与输入

1. 按 `$BUNDLE/contracts/context-loading.manifest.json` 为分析动作装载最小规则包：

~~~text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage design --mode <simple|full> --pass analysis
~~~

完成条件：命令成功返回，规则包模式与用户选择一致，Design 分析核心和当前模式责任已装载；Align 仍按 §2 单独读取，不把规则包装载误认为已读取 Align 产物。

2. Design 至少读取：

- Align 完整对齐稿及 align-notes.json；
- 用户原始需求和已写回的回答；
- 材料索引、分来源事实和合并事实库（有材料时）；
- 完整模式的 A/B/C 基线和冲突资产；
- 当前动作适用的页面、流程、状态、权限、集成和写作规则；涉及状态机时读取 design-state-format.md。

需要读取历史 Design 时按目标事实闭包读取（设计地图 + 设计集清单 → 目标模块及必要基线与契约），不全量读取整套 Design；契约足够时不再读取相邻模块全文，只有目标事实闭包中的契约不足以支撑当前写作时才读取真正需要的相邻模块内部设计，不升级为全系统扫描。规则包装载不等于分析动作完成；Design 正文只保留产品事实与分析结论，编排器回执、metadata、动作 ID 和中间 JSON 写入正文视为违规。

完成条件：每个采用的产品事实都能追溯到 Align、用户回答、材料事实或目标 Design 闭包；未读取无关模块全文；中间运行资产未被当作产品事实。

3. full 模式进入跨层挑战前装载 challenge pass；两种模式进入最终写作前装载 writing pass：

~~~text
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage design --mode full --pass challenge [--card <flow|state|page-module|fields|permissions|cross-system> ...]
python $BUNDLE/scripts/python/context-pack.py --bundle-root $BUNDLE --project-root . --stage design --mode <simple|full> --pass writing [--card <flow|state|page-module|fields|permissions|cross-system> ...]
~~~

专项规则较多时，可用 `--applicability-json <path>` 代替重复的 `--card`。只选择当前 Design 实际适用的页面、流程、状态、字段、权限和跨系统规则。

完成条件：当前动作所需 pass 已成功装载；每个实际适用的专项规则均在规则包中，不适用项未机械展开。

## 4. 执行主图

编排器必须保证 Align 是首个必经责任；材料索引是 Align 的输入，不作为 Align 之后的独立产品阶段。

简单模式：

~~~text
Align → simple-design → 写作自检 → design-set check
~~~

simple-design 在一次写作动作内完成最小 A/B/C 责任：目标、范围、用户、场景、最小业务闭环、必要对象/规则/状态/权限/数据、页面/字段/操作、异常和验收，并进行一次内部回读修正。

完成判据：来源事实逐项落入 Design；目标-能力-场景-流程-页面-动作-字段-状态-权限-规则-异常-验收链路完整；字段表八列齐全逐项；操作表十列角色×状态明确；适用的状态机闭环规则满足；多文件 Design 完整可读。

完整模式：

~~~text
Align → A → B → C → design-editor → 写作自检 → design-set check
~~~

完整模式按下述责任工作，不恢复 Park 的细粒度任务图、固定确认点或检查器：

- A：完成需求理解、干系人、目标指标、场景旅程、用户故事、范围和系统边界。
  完成条件：目标、角色、场景、范围内外和系统边界均有来源或未决状态；冲突和高影响未知已显式记录。
- B：完成业务过程和用例、对象及关系、对象行为、状态、规则、异常、数据流、数据字典和业务模型一致性。
  完成条件：每条适用业务链均能从触发走到结果或恢复；对象、状态、规则、异常和数据流互相一致；不能安全决定的高影响事实未被补写。
- C：完成功能、端/菜单/导航/页面、字段和操作、权限、系统数据、集成、非功能和验收。
  完成条件：B 中每项需由产品承接的事实都有页面、字段、操作、权限、集成或验收落点；C 未创造 A/B 中不存在的高影响规则。
- design-editor：完整整合 Align、详细材料事实和 A/B/C 结论，不做摘要替代，并在结束前执行一次跨层自检和修正。
  完成条件：A/B/C 的适用结论全部进入拥有该事实的正式 Design 文件或未决事项；同一事实没有重复归属、冲突表达或概括性丢失。

完成判据：A/B/C 三层责任全部承担且重要结论进入正式 Design 或未决事项；Design 按产品经理理解顺序组织；页面清单中的每个页面正式展开；字段和操作按固定列表格逐项定义；没有高影响未知悬空未记录。

## 5. 高影响问题

答案不同会改变以下内容时必须在进入下一层前询问：核心流程或系统边界、角色责任、操作权限或数据范围、审批/驳回/撤销/删除/恢复、对象唯一性或生命周期、跨系统失败处理，以及任何会改变页面、字段、操作或验收的事实。

A 区分事实、推导、推测和未决；B 不把推测写成事实；C 不创造 A/B 不存在的高影响规则。无法安全决定的事项写入拥有该事实的正式 Design 文件未决事项（系统级写系统级基线、跨模块写跨模块契约、模块内部写模块设计），说明影响范围、当前保守表达和需要谁确认，并登记到设计集清单的 decisions（status=pending）。

## 5.1 横切能力与事实状态识别

在进入页面和模块写作前，按实际适用性对照 `$BUNDLE/references/design-writing.md`「横切能力、自动动作与生命周期」清单（当且仅当未随规则包装载时直接读取该文件），判断相关事实属于已定义、局部定义、未定义或冲突，并把判断结果落实到对应 Design 文件、未决事项或上游冲突说明中。

局部定义必须同时记录已明确部分和缺失部分；未定义或冲突涉及流程、权限、状态、数据边界、生命周期或页面可实现性时，必须进入未决事项并阻断受影响事实的拍板。Design 不得用常见产品经验补齐失败、补偿、历史影响或权限语义。

## 5.2 可推断值与高影响边界

按 `$BUNDLE/references/design-writing.md` 的“可推断值的写法”执行：低影响展示层细节直接写场景化取值和依据；高影响事项（按该文档「不得进入推断值清单的高影响项」清单）保持未决并单独询问。

完成条件：每个推断值都有业务场景和依据；每个高影响未知都进入拥有该事实的正式 Design 文件及设计集清单 decisions，没有被推断值机制静默拍板。

## 6. 输出与写作要求

1. 首次生成必须建立五项目录结构，并写入：

- output/design/设计地图.md：系统目标与边界、主业务链、模块与职责、跨模块契约、高影响未决入口；
- output/design/设计集清单.json：登记每个正式文件（MAP/SYS/CON/MOD 稳定 ID、路径、类型、模块归属、业务链、依赖、指纹）和决策（DEC 状态）；
- output/design/系统级基线/：系统级事实；
- output/design/跨模块契约/：跨模块交接；
- output/design/模块设计/：每个业务模块一个文件（或模块目录下按子领域拆分）。

完成条件：设计地图、设计集清单和所有适用的系统级基线、跨模块契约、模块设计文件均已创建；每项正式事实只有一个归属处。

2. 首次建立清单时运行以下命令补全全部文件指纹（AI 不手工计算 sha256）：

~~~text
python $BUNDLE/scripts/python/design-set.py refresh --project-root .
~~~

完成条件：清单中的全部正式文件均有由工具生成的当前指纹，未手工填写 sha256。

3. 写作完成后运行：

~~~text
python $BUNDLE/scripts/python/design-set.py check --project-root .
~~~

check 失败时按错误修正（ID 重复、路径非法、依赖错误、指纹不一致、地图引用无法定位）；通过后清单和地图即为正式事实体系。局部修改时执行完整事务命令：

~~~text
# 单文件修改：先读取 stage-single 返回的 staged_path，再只写该路径
python $BUNDLE/scripts/python/design-set.py stage-single --project-root . --id <ID>
python $BUNDLE/scripts/python/design-set.py commit-single --project-root . --semantic <fact|organization>

# 多文件修改：只写 begin 创建的 staged 目录中的目标文件
python $BUNDLE/scripts/python/design-set.py begin --project-root . --ids <ID1> <ID2> [...]
python $BUNDLE/scripts/python/design-set.py commit --project-root . --semantic <fact|organization>

# 任一事务中断或检查失败
python $BUNDLE/scripts/python/design-set.py recover --project-root .
~~~

完成条件：首次生成通过 `check`；局部修改通过对应事务提交且不存在活动事务；失败时已恢复到旧完整集合或完成可校验的新集合。

4. 按产品经理理解顺序组织最终 Design，不按 A/B/C 或任务目录粘贴；页面、字段、操作和多文件事实归属按 `$BUNDLE/references/design-writing.md`、`design-methodology.md`、`design-fact-format.md`、`design-baseline-format.md` 执行。

完成条件：每个实际页面正式展开；字段和操作均按权威格式逐项定义；页面身份、区块、状态和已确认展示行为可定位；详细事实未被概括词替代。

5. 写作时不因篇幅、分段、命令长度或上下文压力删除事实；可分章节写入，但正式结束前重新读取目标模块完整正文。

完成条件：目标模块所有分段已整合，完整正文可读取，后写内容没有导致前文事实密度下降或相互冲突。

上下文不足时：完成当前模块、写入下游依据（provenance），然后提醒用户调用 handoff（C:/Users/guduj/.codex/skills/handoff/SKILL.md），不声称已经清除上下文。只有用户明确要求导出、打印、人工通读或对外发送时，才生成 `.workflow/runtime/完整Design临时视图.md`，并在文件顶部声明它是自动生成的临时阅读视图、不是产品事实源、不得作为 PRD/Prototype/Review/fix 的默认输入。

## 7. 写作动作内自检

simple-design 和 design-editor 各自只执行一次内部自检，不拆成独立任务、不生成检查 JSON、报告或回执。按 `$BUNDLE/references/design-writing.md` 的写作前后检查清单逐项回读，并结合 §5.1 横切能力四状态判断与 §5.2 推断值边界；涉及状态机时逐项满足 `$BUNDLE/references/design-state-format.md` 的闭环要求。发现 `red` 直接修正对应 Design 文件；不能决定的高影响事项写为 `decision`，保留在该文件未决事项。

完成条件：写作清单中的每个适用项都有正文落点或明确未决；修改后的文件已重新回读；`design-set.py check` 通过；没有未暴露的高影响问题。满足后才能告诉用户 Design 已完成。高影响未决事项保持 pending 状态并说明影响，不要求用户确认 Design 或确认哈希。Review 是按需的第二意见，不是首次生成前置。

## 8. 禁止事项

- 不新增独立完整度检查器、综合报告、验证回执或固定细粒度任务；
- 不把中间资产数量、动作回执、metadata 或规则包哈希当作质量证明；
- 不要求用户确认 Design 或确认哈希；不生成 decision-notes 或合并视图；
- 不自动启动 PRD、Prototype 或 Review；
- 不让完整模式跳过 A/B/C；不让简单模式生成无关的完整 ABC；
- 不把高影响问题推迟给 PRD、Prototype 或 Review。
