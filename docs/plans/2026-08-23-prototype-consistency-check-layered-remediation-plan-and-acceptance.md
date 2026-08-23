# Prototype 事实一致性检查分层改造计划与验收方案

> 日期：2026-08-23
> 状态：待执行
> 执行者：其他 AI
> 目标：参考 PRD 一致性检查，将 Prototype 检查拆成确定性脚本检查、运行时验证和语义/视觉审查，提升事实一致性检查对大模型幻觉的实际拦截能力。
> 前置依据：Prototype 对抗审查报告、当前 prototype-consistency-check.py、prototype-source-check.py、PRD 一致性检查及其语义测试。
> 文档边界：本文件是仓库维护计划，不是运行时规则。执行完成后，长期有效的规则必须同步落入 skills、references、contracts、scripts/python 或 templates。

## 1. 最终目标

完成后必须达到以下结果：

1. 明确区分“确定性事实冲突”“可能遗漏”和“需要语义判断”，不再把脚本退出码当作 Prototype 业务质量证明。
2. 脚本可以稳定阻断已知的未授权页面、路由、字段、操作、状态和显式属性冲突。
3. Design 中存在但源码无法可靠确认的内容，进入 possible_omissions，交给 LLM 或人工逐项判断；不得因为字符串未命中就直接声称事实冲突。
4. 同义表达、字段合并/拆分、流程条件、复杂权限、状态转换和异常后果进入 needs_semantic_judgment，不得由脆弱的字符串规则代替业务判断。
5. 路由注册表、源码工程、构建和浏览器运行时检查各自承担明确职责，不互相冒充。
6. 当前无视觉能力的大模型不再被要求凭截图判断审美质量；可脚本或浏览器观察的视觉事实由工具完成，主观视觉质量明确标记为人工或视觉模型验收。
7. spm-prototype、spm-prototype-review、spm-fix、Prototype Review checklist、脚本和测试对同一套分类及调用方式保持一致。

以下结论不得作为完成证明：脚本退出码为 0；所有 Design 名称在源码文本中出现；npm run build 通过；生成了检查报告或中间 JSON；无视觉模型对截图作出主观判断。

## 2. 已确认问题与根因

### 2.1 当前脚本实际能做什么

当前 Prototype 一致性脚本主要读取设计集清单和已验证 Design Index，扫描 HTML 与 src 下的 JS/JSX/MJS，并用字符串包含匹配页面、区块、字段、操作和状态名称；对显式 data-page、data-block、data-field、data-operation、data-state 做有限的未知实体检查。

这能拦截一部分名称级问题和显式事实锚点冲突，但不能证明业务事实完整或无幻觉。

### 2.2 已复现的契约错误

spm-prototype-review 和 spm-fix 当前要求调用 prototype-consistency-check.py --project-root . --module <模块名>，但脚本没有 --module 参数，实际会因 argparse 报错。

执行者必须二选一并真实落实：

- 方案 A：实现真实模块过滤，并用测试证明过滤有效；
- 方案 B：确认脚本只适合全量检查，从 Skill 和契约中删除 --module，明确模块级判断由 LLM 根据全量结果和 Design 分模块完成。

不得只接受参数但忽略它，也不得保留不可执行的文档命令。

### 2.3 事实检查盲区

- 普通 JSX 中没有事实锚点的未授权字段、按钮或操作可能漏过；
- 路由标题、路由路径、模块和 Design 页面没有逐项对照；
- 页面标题出现不能证明有真实页面组件或可访问路由；
- 角色权限、数据范围、状态转换、前置条件和失败后果无法稳定从当前源码抽取；
- 字段类型、必填、只读、枚举和默认值没有可靠的当前契约；
- 动态渲染、接口/Mock 数据和点击后的运行时结果不在静态扫描范围内；
- HTML 入口判断没有完全复用源码扫描的排除目录，错误分类可能不准确。

### 2.4 PRD 检查可复用的模式

PRD 检查已经形成三类输出：

- deterministic_conflicts：脚本可以确定的幻觉、属性冲突、权限反转等，退出码 1；
- possible_omissions：可能没有承接，但需要结合正文和上下文判断，退出码 0；
- needs_semantic_judgment：同义表达、结构适配、复杂语义等，退出码 0，但必须明确列出，不能默认为通过。

Prototype 应采用同一原则，但只实现脚本能够稳定、低误报抽取的事实，不照搬 PRD 的文本解析逻辑。

## 3. 不做什么

本轮明确不做：

- 不恢复 design-confirmation.py、人工 Design 确认、确认哈希或单体 design.md fallback；
- 不修改 Design、PRD 或任何真实项目业务事实；
- 不通过检查器静默补写页面、字段、权限、状态或流程事实；
- 不新增统一检查器、最终门禁、检查回执 JSON、评分器或只证明步骤执行过的中间资产；
- 不用字符串命中、源码行数、组件数量或脚本退出码替代业务语义验收；
- 不要求无视觉能力的 LLM 凭截图判断色彩、层级、密度或品牌审美；
- 不直接修改 dist、node_modules、带哈希构建产物或工作区已有的无关修改；
- 不执行 commit 或 push，除非用户另行明确授权。

## 4. 目标检查架构

    Design / Design Index
            ↓
    Prototype 事实锚点与路由注册表
            ↓
    脚本：deterministic_conflicts / possible_omissions / needs_semantic_judgment
            ↓
    源码工程、build、浏览器 route/console/交互验证
            ↓
    LLM：语义、流程、权限和复杂状态判断
            ↓
    人工或视觉模型：主观视觉质量验收

### 4.1 各层职责

| 层 | 负责内容 | 默认结论方式 |
| --- | --- | --- |
| 工程结构 | src、入口、依赖、路由注册表、build/preview、旧产物污染 | 脚本确定性阻断 |
| Design 事实对账 | 显式页面、字段、区块、操作、状态、属性锚点，路由与模块登记 | 明确冲突阻断；遗漏分层 |
| 运行时 | 默认页、全部注册路由、console、白屏、query、真实交互、Portal、响应式可操作性 | 浏览器证据 |
| 业务语义 | 同义表达、合并拆分、角色权限、数据范围、状态机、前置条件、异常后果 | LLM 逐项审查；高影响未知回上游 |
| 主观视觉 | 信息层级、密度、品牌感觉、审美、可读性 | 用户或视觉模型验收 |

### 4.2 事实锚点原则

脚本只能把可稳定识别的结构当作确定性证据。优先使用已有或补充以下显式锚点：页面 data-page 或路由登记项；区块 data-block 或 data-section；字段 data-field 配合稳定 name；操作 data-operation 配合稳定 action key；状态 data-state；以及明确契约且能稳定抽取的 required、disabled、readOnly、枚举等属性。

任意普通文字、注释、变量名或隐藏字符串不得单独证明业务事实已实现。无法稳定识别时只能进入 possible_omissions 或 needs_semantic_judgment。

## 5. 计划内修改范围

### 5.1 必须评估并可能修改

- scripts/python/prototype-consistency-check.py
- 新增 scripts/python/test-prototype-consistency-check.py
- skills/spm-prototype/SKILL.md
- skills/spm-prototype-review/SKILL.md
- skills/spm-fix/SKILL.md
- contracts/prototype-review-checklist.md
- references/prototype-writing.md
- references/prototype-visual-spec.md（仅同步可脚本/浏览器观察的视觉检查边界）
- templates/prototype-vite/src/ 下确需增加事实锚点的模板文件

### 5.2 条件修改

- prototype-source-check.py：只有发现与本轮分类或扫描范围直接相关的可复现缺陷才修改；
- test-shitpm-regression.py：只有现有回归入口需要纳入新增独立测试时修改；
- design-index.py 或其他 Design 解析器：只有证明当前 Index 缺少本轮所需的稳定字段，且最小补充不会改变 Design 事实时修改。

### 5.3 明确不修改

- output/design、output/prd 和真实项目产物；
- design-confirmation.py 相关旧流程；
- 与本轮无关的视觉 Token、Ant Design 主题和业务页面；
- 任何只为存放检查结果而新增的长期 JSON、报告或回执文件。

## 6. 分阶段执行

每阶段完成并记录证据后再进入下一阶段。发现 Design 事实缺失、冲突或高影响未知时停止并报告，不由执行者补事实。

### 阶段 0：保护基线与复现现状

1. 运行 git status --short，记录已有修改和未跟踪文件。
2. 确认当前分支、HEAD 和工作区，不使用 reset、checkout 或覆盖写入清理基线。
3. 阅读当前脚本、三个 Skill、Review checklist 和 PRD 检查脚本的调用方式。
4. 复现以下命令并保留原始结果：

    python scripts/python/prototype-consistency-check.py --project-root . --module demo
    python scripts/python/test-prototype-source-check.py
    python scripts/python/test-prd-consistency-semantics.py
    python scripts/python/test-shitpm-regression.py

验收：--module 错误被记录为真实基线问题；既有测试结果与本轮修改区分；不能因仓库根目录缺少真实 output/design 而伪造一致性通过结论。

### 阶段 1：确定检查契约和模块策略

若选择方案 A，必须明确模块来源，过滤 Design Index、设计集清单或路由登记表中的稳定模块字段；无法归属模块的对象要明确报告；增加测试证明不同模块的结果确实不同。

若选择方案 B，必须从 Skill 和契约中删除错误的 --module 调用，明确 Prototype 一致性检查只执行全量检查；模块级审查由 LLM 根据全量结果和 Design 分模块阅读完成；增加测试或文档检查，确保没有残留不可执行命令。

阶段验收：只有一个真实入口，参数行为、Skill、Fix、Review 三者一致；选择理由写入执行报告，不新增永久回执文件。

### 阶段 2：改造 Prototype 一致性脚本

#### 2.1 统一输出三分类

结果至少包含 classification.deterministic_conflicts、classification.possible_omissions、classification.needs_semantic_judgment、summary 和 exit_reason。

要求：只有确定性冲突返回 1；输入缺失、Index 无法验证、源码工程不可读等致命错误返回 2；possible_omissions 和 needs_semantic_judgment 不因解析不确定直接阻断，但必须完整输出；返回 0 时不得暗示事实完整或无幻觉。

#### 2.2 修复入口与扫描范围

- HTML 入口判断必须与扫描使用相同的排除目录规则；
- 只剩 dist、node_modules 或 prototype-p0 时，明确报告源码工程缺失；
- 保留 Design 清单和已验证 Index 的 fail-fast；
- 不扫描构建产物来补足源码事实。

#### 2.3 路由和页面对账

- 读取 routes.jsx 或约定的路由注册表；
- 对照 Design Index 的页面和模块；
- 未登记但存在的路由页面进入确定性冲突；
- Design 页面未找到可确认路由进入 possible_omissions，不能仅因标题字符串出现而算通过；
- 路由指向明确占位组件时，按页面承接不足输出 possible_omissions 或 needs_semantic_judgment，不把占位文本当作完整实现。

#### 2.4 显式事实锚点对账

- 显式未知 data-page、data-block、data-field、data-operation、data-state 进入确定性冲突；
- Design 中有事实但没有稳定锚点，进入 possible_omissions，不由任意字符串包含匹配自动通过；
- 同义文案、合并字段、拆分字段和状态枚举表达进入 needs_semantic_judgment；
- 对脚本无法可靠推断的权限、流程和后置结果，输出需语义审查，不能输出权限一致。

#### 2.5 可机械检查的属性

只实现低误报、可稳定抽取的属性检查。字段类型的等价表达、同名字段所属对象、复杂枚举映射、多个控件共同表达一个业务字段、动态条件渲染和运行时状态不得硬判。

阶段验收：任一确定性冲突能定位到类型、对象和来源；可能遗漏和语义判断不会误报成确定性冲突；脚本不再依赖全源码任意字符串出现作为唯一通过依据；没有通过新增统一回执或评分器换皮增加复杂度。

### 阶段 3：建立独立对抗测试

新增 test-prototype-consistency-check.py，使用临时目录和最小 Design、Index、Prototype fixture，不依赖真实项目业务事实。至少覆盖：

1. Design 清单缺失、损坏和 Index 缺失：退出码 2；
2. 页面路由、模块和 Design 一致：正常分类；
3. 未登记路由：deterministic_conflicts；
4. Design 页面只有同名文本、没有真实路由：possible_omissions；
5. 显式未知字段、操作、状态和页面：deterministic_conflicts；
6. 普通 JSX 中出现未授权按钮但没有锚点：不得假装确定性通过，至少进入需进一步审查的结果；
7. 合并字段、同义字段、状态组合值：needs_semantic_judgment；
8. Design 缺少源码落点：possible_omissions，退出码仍为 0；
9. dist、node_modules、prototype-p0 不参与源码扫描；
10. --module 的真实行为符合阶段 1 选择；
11. 空字符串、注释、隐藏脚本内容不会造成错误命中；
12. 输出 JSON 可解析，分类字段稳定存在。

测试行为意图，不测试实现细节；不要为了保持旧测试数量而保留旧语义。

### 阶段 4：同步 Skill、Review、Fix 和契约

- spm-prototype：说明先执行源码工程检查，再执行 Prototype 一致性检查；明确退出码和三类输出含义；不得写脚本通过即事实一致；
- spm-prototype-review：引用三类结果，逐条处理可能遗漏和语义判断；明确无视觉模型时的视觉验收边界；
- spm-fix：使用真实可执行的全量或模块入口；确定性冲突可修复，语义或高影响未知回 Design 或交用户确认；
- prototype-review-checklist：将脚本事实冲突、可能遗漏、语义判断和主观视觉分别列入证据要求；
- prototype-writing：约定稳定事实锚点的使用场景，不要求页面用解释性文字替代真实 UI 状态；
- prototype-visual-spec：仅补充脚本/浏览器可观察和人工/视觉模型判断的边界，不把审美判断变成脚本门禁。

阶段验收：旧的不可执行 --module 命令已删除或真实实现；所有 Skill 都说明返回 0 不等于无幻觉；Review 不把无视觉模型无法判断的审美项写成自动通过；同一规则只有一个完整定义。

### 阶段 5：运行时和视觉检查边界验证

如果修改了模板或运行时入口，执行 npm ci、npm run build 和 npm run preview，并在真实浏览器或可用自动化工具中检查默认页、全部注册路由、query、console、实际存在的 Form、Select、Modal、Dropdown、删除确认、响应式、Portal、焦点、Esc、点击穿透和 sticky 操作栏。

至少观察 390px、576px 边界、992px 边界和 1440px 的页面级横向溢出。

没有视觉能力时，用 DOM、计算样式、console、截图尺寸和自动化交互验证可观察事实；将视觉层级、品牌感觉、密度和审美标记为人工/视觉模型验收或未评估，不得宣称自动通过。

## 7. 验收方案

### 7.1 确定性命令

在仓库根目录执行：

    python scripts/python/test-prototype-source-check.py
    python scripts/python/test-prototype-consistency-check.py
    python scripts/python/test-prd-consistency-semantics.py
    python scripts/python/test-shitpm-regression.py
    python scripts/python/test-resource-integrity.py
    git -c core.whitespace=cr-at-eol diff --check

如新增测试被纳入总回归，同时运行总回归入口并保留单测原始结果。

### 7.2 输出分类验收

| 分类 | 典型内容 | 退出码 | 放行要求 |
| --- | --- | ---: | --- |
| deterministic_conflicts | 未授权路由/显式事实锚点、可确定属性冲突 | 1 | 必须修复或明确阻塞 |
| possible_omissions | Design 事实没有可靠源码落点、页面正文承接不足 | 0 | 逐项由 LLM/人工判断，不能写成自动通过 |
| needs_semantic_judgment | 同义表达、字段合并拆分、复杂状态和权限语义 | 0 | 逐项给出结论、未评估或回上游 |
| 主观视觉 | 层级、审美、密度、品牌感觉 | 不由脚本裁决 | 用户或视觉模型验收；无能力时明确未评估 |

### 7.3 对抗样例验收

| 样例 | 预期 |
| --- | --- |
| 未授权 data-field | 确定性冲突 |
| 未授权 data-operation | 确定性冲突 |
| 未授权普通 JSX 按钮但无锚点 | 不得误报为完整通过，进入需进一步审查 |
| Design 字段没有源码锚点 | 可能遗漏 |
| 同义字段或合并字段 | 语义判断 |
| 未登记路由 | 确定性冲突 |
| 只有标题字符串、没有对应真实路由 | 可能遗漏或页面承接不足 |
| 只剩 dist | 源码工程错误或致命错误 |

### 7.4 文档契约验收

执行定向搜索，逐项人工判断：

    rg -n "prototype-consistency-check.py --module" skills contracts docs references
    rg -n "脚本通过|事实完整|无幻觉|视觉通过|零冲突" skills/spm-prototype skills/spm-prototype-review skills/spm-fix contracts references
    rg -n "deterministic_conflicts|possible_omissions|needs_semantic_judgment" scripts skills contracts

旧 --module 命令只有在方案 A 已实现且测试覆盖时才允许保留；不得出现把返回 0 当成事实完整、无幻觉或视觉通过的表述；三类分类在脚本、Skill、Review 和 Fix 中必须含义一致。

### 7.5 真实 Prototype 验收

在具备正式 Design、Design Index 和 Prototype 的真实项目中运行全量检查；如采用方案 A，再运行模块检查。结果必须同时记录脚本 JSON、确定性冲突及修复位置、可能遗漏逐项判断、语义判断逐项结论、浏览器证据和主观视觉项结论或未评估说明。

不得只在 ShitPM 仓库根目录运行脚本并把“设计清单不存在”包装为通过。

## 8. 最终放行条件

- [ ] 当前工作区已有修改和未跟踪文件均被保留；
- [ ] --module 已真实实现并测试，或已从所有调用方删除；
- [ ] Prototype 脚本输出 PRD 同款三分类；
- [ ] 只有确定性冲突返回 1，致命输入错误返回 2；
- [ ] 可能遗漏和语义判断完整输出，且不会被默认写成通过；
- [ ] 未授权显式页面、字段、区块、操作和状态可被阻断；
- [ ] 路由登记与 Design 页面/模块对账，不再用任意字符串出现冒充页面落地；
- [ ] 扫描范围排除构建产物和旧原型目录，入口检查与扫描范围一致；
- [ ] 独立 Prototype 一致性测试覆盖正例、反例、漏检边界和输出分类；
- [ ] 源码检查、Prototype 测试、PRD 语义测试、ShitPM 回归和 diff check 结果明确；
- [ ] 修改运行时模板时，build、全部路由、代表性交互、console 和适用响应式场景已验证；
- [ ] 无视觉能力的模型没有被要求自动裁决主观审美；
- [ ] 所有未验证、失败、需用户确认和不适用项都被明确列出；
- [ ] 未执行 commit/push，除非用户另行授权。

以下任一情况只能报告“部分完成”或“阻塞”：脚本返回 0 仍被文档表述为无幻觉或事实完整；--module 仍写在文档中但实际不可执行；为提高覆盖率引入高误报的业务正则；可能遗漏或语义判断被静默丢弃；只通过 build 或静态搜索宣布事实一致；没有 fixture 证明反例分类有效；视觉主观项在没有视觉能力时被宣称已通过；发现高影响 Design 未知却由执行者自行补全。

## 9. 执行失败处理

- 已有工作区修改与计划冲突时，保留原修改，说明冲突，不使用 reset 或 checkout 覆盖；
- 脚本无法稳定解析某类业务事实时，降级为 possible_omissions 或 needs_semantic_judgment，不继续扩大脆弱解析器；
- Design Index、设计集清单或真实项目输入缺失时，停止相关事实验收并报告缺失；
- 浏览器环境不可用时，完成脚本和构建验收，并把浏览器项目标记为未验证；
- 现有测试因旧基线失败时，保留原始输出，不删除旧测试或修改无关代码；
- 发现权限、状态机、数据范围、核心流程等高影响未知时，停止下游静默修改，回 Design 或交用户决定。

## 10. 执行者最终交付格式

其他 AI 最终回复必须按以下顺序：

1. 结论：完成 / 部分完成 / 阻塞；
2. 基线与根因：复现了哪些旧问题，最终选择方案 A 还是 B；
3. 修改范围：逐文件说明脚本、测试、Skill、契约和模板的变化；
4. 检查分类：分别列出确定性冲突、可能遗漏、语义判断和视觉未评估项；
5. 测试证据：命令、退出码、关键输出和 fixture/反例结果；
6. 真实项目验证：Design、Index、Prototype 输入是否齐全，脚本和浏览器验证是否执行；
7. 未完成项：失败、阻塞、未验证、不适用和需要用户确认的内容；
8. 工作区边界：说明保留的既有修改，确认未执行 commit/push。

不得只回复“脚本通过”“测试通过”“一致性已修复”或“视觉已验收”。结论必须能够追溯到本计划的放行条件和实际证据。
