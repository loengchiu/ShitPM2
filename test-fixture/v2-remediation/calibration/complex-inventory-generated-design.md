# 物资调拨设计基线

> 项目：智慧服务区资产管理—物资调拨  
> 文档状态：可评审，暂不可确认  
> 设计编号：PRJ-ASSET-TRANSFER  
> 本文的中文正文是给产品、业务和研发阅读的主文；文末的结构化契约只用于一致性校验，不能替代正文。

## 一、先看结论

本闭环解决“一个服务区把可用物资转给另一个服务区”的业务问题：调出服务区发起申请，审核角色审核，调入服务区确认接收，系统最后同时更新双方资产台账并留下调拨履历。

当前稿可以用于评审流程、角色、状态和数据边界，但不能直接确认或生成下游 PRD，原因是存在尚未决策的高影响问题：原始材料同时出现“财务部管理员参与审核”和“运营部/区域中心审核”两种口径；可用数量在审核期间何时冻结或预占也没有确定答案。

**建议阅读顺序：**先读范围和闭环主线，再读角色权限、对象数据和状态，最后看页面、字段和验收。业务操作编号只用于追踪，不要求读者先理解编号。

## 二、范围、非目标和系统边界

### 本次范围

- 从调出服务区资产台账中选择标准物资或已编码物资，支持按物资、按单件以及同一单据混合选择，填写调入服务区和调拨数量。
- 支持调拨申请暂存、提交、审核、调入服务区确认或拒绝。
- 调拨完成后扣减调出服务区可用数量、增加调入服务区数量，并生成调拨履历。
- 保留申请、审核、确认和拒绝的操作记录。

### 本次不做

- 不重新设计入库、出库、报废和盘点闭环。
- 不实现外部财务系统自动回传编码或自动记账接口。
- 不重新设计完整的资产生命周期；但本闭环必须保留已编码物资的资产编码、单件选择和调拨后的状态变化。
- 不在本稿中决定调拨期间的冻结、预占或人工补偿方案；这些问题必须先完成产品或技术决策。

### 系统边界

本闭环由智慧服务区物业管理系统负责申请、审核、确认、台账变更和履历记录。外部财务系统是已编码物资的既有来源，本期不建立自动同步接口；因此 C6 仅分析编码来源和边界，不把外部系统同步伪装成本期能力。编码缺失、重复或来源异常的责任边界和人工处理方式需要在相关方案中单独确认。

## 三、物资调拨业务闭环（LOOP-TRANSFER-CLOSE）

### 3.1 谁在什么时候接手

1. **服务区管理员**从本服务区资产台账发起调拨，选择标准物资或已编码物资，按物资数量、按单件或混合方式填写调入服务区、数量、税后单价和备注，并可先暂存草稿。
2. **审核角色**打开“审核中”调拨单，检查调出和调入服务区、物资、数量及申请意见，选择通过或驳回。当前材料明确运营部管理员和区域中心管理员可审核；财务部管理员是否也能审核，列为待用户决策。
3. **调入服务区管理员**在“待确认”状态查看调拨明细，选择确认接收或拒绝接收。确认时系统必须把调出、调入两边台账和调拨履历作为一个完整结果处理，不能只成功一边。

### 3.2 业务操作清单

| 业务操作 | 业务操作编号 | 执行角色 | 前置条件 | 主要输入 | 成功结果 | 失败结局 |
|---|---|---|---|---|---|---|
| 暂存物资调拨申请 | ACT-TRANSFER-SAVE-DRAFT | 服务区管理员 | 具有调出服务区数据范围 | 调入服务区、明细、数量、单价、备注 | 保存为草稿，可继续编辑 | 字段或明细格式错误时不写入错误数据 |
| 提交物资调拨申请 | ACT-TRANSFER-SUBMIT | 服务区管理员 | 草稿完整；调入服务区不能等于调出服务区；数量为正整数 | 调拨单和调拨明细 | 状态由草稿变为审核中 | 校验失败时保持草稿，并定位失败项 |
| 导入调拨明细 | ACT-TRANSFER-IMPORT-LINES | 服务区管理员 | 正在编辑草稿 | Excel 文件 | 先完成全量解析和逐行校验；无错误时写入草稿 | 有错误时逐项反馈，合法行是否部分写入、重复导入幂等规则待用户决策，不改变调拨单状态 |
| 审核物资调拨申请 | ACT-TRANSFER-APPROVE | 运营部管理员、区域中心管理员；财务部管理员资格待确认 | 调拨单处于审核中，审核人具有相应数据范围 | 审核意见 | 通过后进入待确认 | 审核结果保存失败时保持审核中，可重试 |
| 驳回物资调拨申请 | ACT-TRANSFER-REJECT-REVIEW | 运营部管理员、区域中心管理员；财务部管理员资格待确认 | 调拨单处于审核中，驳回原因必填 | 驳回原因 | 状态变为已驳回，申请人可见原因 | 原因为空或保存失败时不改变状态 |
| 确认接收调拨物资 | ACT-TRANSFER-CONFIRM | 调入服务区管理员 | 调拨单处于待确认且属于目标服务区 | 确认结果 | 状态变为已完成；调出侧进入已调出、调入侧进入在库，双方台账和履历同步更新 | 任一写入失败时整体回滚，调出侧恢复变更前状态并保持待确认 |
| 拒绝接收调拨物资 | ACT-TRANSFER-REJECT-RECEIVE | 调入服务区管理员 | 调拨单处于待确认且属于目标服务区 | 拒绝原因 | 状态变为已驳回并保留原因 | 原因为空或保存失败时不改变状态 |
| 查看物资调拨详情 | ACT-TRANSFER-VIEW | 参与服务区管理员、运营部管理员、区域中心管理员；财务部管理员范围待确认 | 具有该调拨单数据范围 | 查询条件 | 看见当前状态、明细、处理人和履历 | 无权限时不返回单据内容 |

### 3.3 状态主线

调拨单的主线是：**草稿 → 审核中 → 待确认 → 已完成**；物资台账另有一条状态主线：**在库 → 调拨中 → 已调出**，调入拒绝或回滚时回到“在库”。

- 草稿：申请人可以编辑、暂存或提交。
- 审核中：等待审核角色处理；申请人不能直接改变审核结果。
- 待确认：审核通过，等待调入服务区确认或拒绝。
- 已完成：调拨结果已落到双方台账并生成履历，不允许再次处理。
- 已驳回：审核驳回或调入拒绝后的终态；必须保留原因。审核驳回不改变调出侧台账状态；调入拒绝则把已进入“调拨中”的调出侧物资恢复为“在库”。

审核通过和审核驳回的责任角色必须与“审核物资调拨申请”保持一致。审核通过后，调出侧关联物资先进入“调拨中”；确认成功后变为“已调出”，调入侧形成“在库”记录。可用数量冻结或预占的具体时点仍由待用户决策项约束，不能被状态变化偷换。

### 3.4 对象和数据如何变化

- **调拨单**记录单号、调出服务区、调入服务区、申请人、申请时间、当前状态、审核意见、拒绝原因、确认结果和处理时间。
- **调拨明细**记录标准物资、选择方式（按物资或按单件）、调拨数量、已编码物资的资产编码清单、按物资选择时的先进先出分配结果、税后单价、备注、来源行号和校验结果。同一单据允许不同明细采用不同选择方式，但同一资产编码不得在同一单据重复出现。
- **已编码物资条目**记录资产编码、标准物资、来源台账、调拨前状态、调拨中状态和调拨后状态；按物资选择时由系统按先进先出规则分配可用编码并留下分配轨迹。
- **调出服务区资产台账**记录变更前后数量、可用数量、物资状态、变更原因、关联调拨单号和幂等键；审核通过后关联条目进入“调拨中”，确认成功后进入“已调出”，拒绝或回滚恢复为变更前状态。
- **调入服务区资产台账**记录服务区、标准物资、已编码资产编码（如有）、变更前后数量、初始状态、变更原因、关联调拨单号和幂等键；确认成功后增加数量或新建“在库”记录。
- **调拨履历**记录申请、审核、确认或拒绝、台账变更前后值、操作人、操作时间、结果、失败原因、回滚结果和请求幂等键。

数量校验至少满足：数量为大于 0 的整数、调入服务区不能等于调出服务区、提交和完成时不能超过可用数量；已编码物资还必须校验资产编码存在、来源属于调出服务区且未被其他未完成调拨占用。可用数量在审核中是否冻结或预占，当前没有确定口径。

## 四、角色、权限和数据范围

| 角色 | 业务责任 | 当前确定的数据范围 | 允许的业务操作 |
|---|---|---|---|
| 服务区管理员 | 发起调拨、维护草稿、确认或拒绝调入物资 | 本服务区；确认时仅限目标服务区 | 暂存、提交、确认、拒绝接收、查看参与本服务区的单据 |
| 运营部管理员 | 审核调拨、查看全局调拨 | 全部服务区 | 审核通过、审核驳回、查看 |
| 区域中心管理员 | 审核所辖服务区的调拨、查看所辖数据 | **所辖服务区**，不是全部服务区 | 审核通过、审核驳回、查看所辖数据 |
| 财务部管理员 | 原始材料的权限矩阵列出查看和审核，但流程表未列出 | **待用户决策** | 在确认前不自动放开或排除审核权限 |

权限判断必须同时考虑业务操作和数据范围。区域中心管理员不能因为拥有审核业务操作就看到全部服务区；财务部管理员的权限冲突必须先解决再进入正式下游。

## 五、页面和模块落点

本闭环归属于“资产调拨”模块（MOD-ASSET-TRANSFER），建议至少包含三个阅读入口：

- **调拨申请页：**服务区管理员创建、编辑、导入明细、暂存和提交草稿。
- **调拨审核页：**审核角色查看申请内容、校验数量和业务依据，执行通过或驳回。
- **调拨确认页：**调入服务区查看待确认明细，执行确认或拒绝，并查看完成后的双方台账和履历。

页面只是业务操作的入口。页面正文不能新增闭环中没有定义的状态、角色或数据字段；字段详细属性应与本设计的结构化契约保持一致。

## 六、数据定义和验收关注点

### 6.1 首批必须落地的数据字段

| 对象 | 必须明确的字段或约束 |
|---|---|
| 调拨单 | 调拨单号、调出服务区、调入服务区、申请人、申请时间、状态、审核意见、拒绝原因、确认结果、确认时间 |
| 调拨明细 | 必填：标准物资、选择方式、数量；条件必填：按单件时资产编码清单，按物资时 FIFO 分配结果；来源为调出服务区台账或 Excel 行；数量为正整数；同一单据内资产编码唯一；保留导入行号和逐行校验结果 |
| 已编码物资条目 | 必填：资产编码、标准物资、来源台账、调拨前状态、调拨后状态；资产编码全局唯一；状态变化必须有调拨单号和履历关联 |
| 双边资产台账 | 必填：服务区、标准物资、变更前数量、变更数量、变更后数量、可用数量、物资状态、变更原因、关联调拨单号、幂等键；数量变化前后可核对 |
| 调拨履历 | 必填：调拨单号、业务操作、操作人、操作时间、处理结果、失败原因、回滚结果、请求幂等键；不得物理覆盖历史记录 |

并发校验规则仍有一项待决策：提交、审核通过还是调入确认时冻结或预占可用数量；除此之外，上述字段的必填性、来源、格式、唯一性、历史保留和回写关联已形成 Design 基线。

### 6.2 验收边界

- 正常：合法调拨从草稿提交、审核通过、目标服务区确认到已完成，双方数量和履历一致。
- 边界：数量为 0、负数、小数、超过可用数量、调入调出服务区相同，均被拒绝并定位原因。
- 导入：Excel 文件格式错误、重复明细、非法物资、非法数量或资产编码问题逐项反馈；导入持久化方式按待决策项执行，不能把未确认的部分成功或幂等规则写成既定事实。
- 编码物资：按单件选择只允许选择可用且属于调出服务区的资产编码；按物资选择按先进先出分配并可追溯；同一单据混合选择不重复占用资产编码。
- 权限：服务区管理员不能审核他人单据；区域中心管理员只看所辖服务区；目标服务区以外的管理员不能确认。
- 状态：审核通过后调出侧进入“调拨中”；审核驳回保持“在库”；调入拒绝恢复“在库”；确认成功后调出侧为“已调出”、调入侧为“在库”；已完成不能重复确认。
- 一致性：确认失败不产生单边扣减或单边状态变化；重试不能重复扣减、重复生成履历或重复转移资产编码。
- 审计：申请、审核、确认、拒绝均可追溯到操作人、时间和处理结果。

## 七、待用户决策和风险

以下问题不阻止生成评审稿，但会阻止确认和下游正式使用。

| 问题性质 | 业务影响 | 证据等级 | 问题 | 影响范围 | 当前处理 |
|---|---|---|---|---|---|
| 待用户决策 | 高 | 已证实 | 财务部管理员是否参与调拨查看和审核？权限矩阵与调拨流程表口径冲突。 | 角色、权限、审核状态 | 保留冲突，不静默决定 |
| 确定性冲突 | 高 | 已证实 | 区域中心管理员的范围不能定义为全部服务区，应为所辖服务区。 | 数据范围、查看、审核和驳回 | 按所辖服务区修正 |
| 确定性冲突 | 高 | 已证实 | 审核业务操作允许的角色必须与审核状态转换执行角色一致。 | 状态、权限、审计 | 标记为修正项 |
| 产品风险 | 高 | 已证实 | 调拨单、调拨明细、双边台账和履历缺少完整字段及约束定义。 | 数据模型、验收、实现 | 已补充字段、来源、唯一性、历史保留和并发校验口径；冻结/预占时点仍单列待决策 |
| 确定性遗漏 | 高 | 已证实 | Excel 导入调拨明细及失败反馈必须成为独立业务操作。 | 申请页、业务闭环、验收 | 已纳入闭环，持久化语义另列待决策 |
| 待用户决策 | 阻塞 | 证据不足 | 可用数量在提交、审核通过还是调入确认时冻结或预占？ | 并发、数量一致性、失败重试 | 保留为阻塞待确认 |
| 未知项 | 一般 | 证据不足 | 双边写入失败后的告警、重试和人工补偿入口由谁负责？ | 异常处理、运维和审计 | 留待技术方案确认 |
| 产品风险 | 高 | 已证实 | 审核通过后的调出侧物资必须进入“调拨中”，拒绝或回滚时恢复“在库”，确认成功后转为“已调出”。 | 状态、台账、履历、验收 | 已补充独立的物资状态主线 |
| 产品风险 | 高 | 已证实 | 已编码物资支持按单件、按物资 FIFO 和同单据混合选择；资产编码必须唯一且可追溯。 | 调拨明细、资产台账、验收 | 已纳入范围、对象和验收 |
| 待用户决策 | 一般 | 证据不足 | Excel 导入出现部分错误时，合法行是否部分落库、重复导入如何幂等以及草稿如何保留？ | 导入、草稿、验收 | 只固定逐行解析和反馈，其余不静默决定 |

## 八、评审结论

本稿已经把物资调拨的业务闭环、角色交接、业务操作、调拨单状态、物资状态、编码物资选择、数据约束、权限边界、异常路径和验收入口集中在同一份人读正文中。它可以用于产品和研发评审；在财务部管理员权限、可用数量冻结/预占以及 Excel 导入持久化语义确认前，不得写入 Design 确认标记，也不得生成正式 PRD。

---

<!-- SPM-CONTRACT-START -->
```json
{
  "schema_version": "2.0.0",
  "project": {
    "id": "PRJ-ASSET-TRANSFER",
    "name": "智慧服务区资产管理—物资调拨"
  },
  "globals": {
    "roles": [
      {
        "id": "ROLE-SERVICE-ADMIN",
        "name": "服务区管理员"
      },
      {
        "id": "ROLE-OPERATIONS-ADMIN",
        "name": "运营部管理员"
      },
      {
        "id": "ROLE-REGION-ADMIN",
        "name": "区域中心管理员"
      },
      {
        "id": "ROLE-FINANCE-ADMIN",
        "name": "财务部管理员",
        "description": "原始材料权限矩阵列出该角色；是否参与调拨查看和审核待用户决策。"
      }
    ],
    "objects": [
      {
        "id": "OBJ-TRANSFER-ORDER",
        "name": "调拨单",
        "description": "记录调出服务区、调入服务区、申请人、时间、状态、审核和确认结果。"
      },
      {
        "id": "OBJ-TRANSFER-LINE",
        "name": "调拨明细",
        "description": "记录标准物资、选择方式（按物资或按单件）、调拨数量、已编码物资资产编码清单、按物资选择时的先进先出分配结果、税后单价、备注、来源行号和校验结果；同一单据内资产编码不得重复。"
      },
      {
        "id": "OBJ-SOURCE-LEDGER",
        "name": "调出服务区资产台账",
        "description": "记录调出服务区、标准物资、已编码资产编码（如有）、变更前后数量、可用数量、物资状态、变更原因、关联调拨单号和幂等键；审核通过后关联条目进入调拨中，确认成功后进入已调出。"
      },
      {
        "id": "OBJ-TARGET-LEDGER",
        "name": "调入服务区资产台账",
        "description": "记录调入服务区、标准物资、已编码资产编码（如有）、变更前后数量、初始在库状态、变更原因、关联调拨单号和幂等键。"
      },
      {
        "id": "OBJ-TRANSFER-HISTORY",
        "name": "调拨履历",
        "description": "记录调拨单号、业务操作、操作人、时间、处理结果、台账或资产状态变更前后值、失败原因、回滚结果和请求幂等键，历史记录不得被覆盖。"
      },
      {
        "id": "OBJ-TRANSFER-ASSET-ITEM",
        "name": "调拨资产条目",
        "description": "已编码物资的调拨专用条目，记录资产编码、标准物资、来源台账、调拨前状态、调拨中状态、调拨后状态和关联调拨单号；不扩展完整资产生命周期。"
      }
    ],
    "dictionaries": [
      {
        "id": "DICT-TRANSFER-STATUS",
        "name": "调拨状态"
      },
      {
        "id": "DICT-TRANSFER-MODE",
        "name": "调拨选择方式"
      }
    ],
    "scopes": [
      {
        "id": "SCOPE-ALL-SERVICE-AREAS",
        "name": "全部服务区"
      },
      {
        "id": "SCOPE-SOURCE-SERVICE-AREA",
        "name": "调出服务区"
      },
      {
        "id": "SCOPE-TARGET-SERVICE-AREA",
        "name": "调入服务区"
      },
      {
        "id": "SCOPE-OWNED-SERVICE-AREAS",
        "name": "所辖服务区",
        "description": "区域中心管理员只能查看和处理其组织关系内的服务区。"
      }
    ],
    "rules": [
      {
        "id": "RULE-TARGET-DIFFERENT",
        "name": "调入服务区不得与调出服务区相同"
      },
      {
        "id": "RULE-QTY-POSITIVE",
        "name": "调拨数量为大于 0 的整数"
      },
      {
        "id": "RULE-QTY-AVAILABLE",
        "name": "提交与完成时重新校验可用数量；冻结或预占时点待用户决策"
      },
      {
        "id": "RULE-ATOMIC-POSTING",
        "name": "完成调拨时两边台账与履历必须一致写入"
      },
      {
        "id": "RULE-TRANSFER-AUDIT",
        "name": "审核和确认结果必须保留操作记录"
      },
      {
        "id": "RULE-IMPORT-LINES",
        "name": "Excel 导入先逐行解析和校验；部分成功与重复导入语义待用户决策"
      },
      {
        "id": "RULE-ENCODED-ASSET-SELECT",
        "name": "已编码物资支持按单件、按物资先进先出和同单据混合选择"
      },
      {
        "id": "RULE-ASSET-CODE-UNIQUE",
        "name": "同一调拨单及未完成调拨中资产编码不得重复占用"
      },
      {
        "id": "RULE-LEDGER-STATE",
        "name": "审核通过进入调拨中，拒绝或回滚恢复在库，完成后调出侧为已调出"
      }
    ],
    "systems": [
      {
        "id": "SYS-ASSET-MANAGEMENT",
        "name": "智慧服务区物业管理系统"
      }
    ],
    "organizations": [
      {
        "id": "ORG-OPERATIONS",
        "name": "运营部"
      },
      {
        "id": "ORG-REGION",
        "name": "区域中心"
      },
      {
        "id": "ORG-SERVICE-AREA",
        "name": "服务区"
      }
    ]
  },
  "modules": [
    {
      "id": "MOD-ASSET-TRANSFER",
      "name": "资产调拨",
      "summary": "承载调拨申请、审核、调入确认和双边台账回写。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ]
    }
  ],
  "loops": [
    {
      "id": "LOOP-TRANSFER-CLOSE",
      "name": "物资调拨闭环",
      "title": "物资调拨闭环",
      "summary": "调出服务区提交调拨申请，经运营部或区域中心审核后，由调入服务区确认接收并完成双边台账回写。",
      "objective": "把可用物资从一个服务区转移到另一个服务区，并留下可追溯的调拨履历。",
      "scope": "仅覆盖服务区之间的物资调拨，不覆盖入库、出库、报废和盘点。",
      "start": "调出服务区管理员从本服务区资产台账发起调拨。",
      "end": "调入服务区确认接收，调拨单为已完成。",
      "completion_conditions": [
        "调拨状态为已完成",
        "调出服务区可用数量扣减",
        "调入服务区台账数量增加或新建",
        "调拨履历生成"
      ],
      "termination_conditions": [
        "申请校验失败",
        "审核驳回",
        "调入服务区拒绝"
      ],
      "role_ids": [
        "ROLE-SERVICE-ADMIN",
        "ROLE-OPERATIONS-ADMIN",
        "ROLE-REGION-ADMIN"
      ],
      "owner_role_id": "ROLE-SERVICE-ADMIN",
      "data_scope_ids": [
        "SCOPE-SOURCE-SERVICE-AREA",
        "SCOPE-TARGET-SERVICE-AREA"
      ],
      "primary_object_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE"
      ],
      "related_object_ids": [
        "OBJ-SOURCE-LEDGER",
        "OBJ-TARGET-LEDGER",
        "OBJ-TRANSFER-HISTORY"
      ],
      "action_ids": [
        "ACT-TRANSFER-SAVE-DRAFT",
        "ACT-TRANSFER-SUBMIT",
        "ACT-TRANSFER-APPROVE",
        "ACT-TRANSFER-REJECT-REVIEW",
        "ACT-TRANSFER-CONFIRM",
        "ACT-TRANSFER-REJECT-RECEIVE",
        "ACT-TRANSFER-VIEW",
        "ACT-TRANSFER-IMPORT-LINES"
      ],
      "entry_action_ids": [
        "ACT-TRANSFER-SAVE-DRAFT",
        "ACT-TRANSFER-SUBMIT",
        "ACT-TRANSFER-IMPORT-LINES"
      ],
      "exit_action_ids": [
        "ACT-TRANSFER-CONFIRM",
        "ACT-TRANSFER-REJECT-RECEIVE",
        "ACT-TRANSFER-REJECT-REVIEW"
      ]
    }
  ],
  "actions": [
    {
      "id": "ACT-TRANSFER-SAVE-DRAFT",
      "loop_id": "LOOP-TRANSFER-CLOSE",
      "name": "暂存物资调拨申请",
      "intent": "保存尚未填写完整的调拨单，供申请人继续编辑。",
      "initiator_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "responsible_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "actor_role_id": "ROLE-SERVICE-ADMIN",
      "object_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE"
      ],
      "data_scope_ids": [
        "SCOPE-SOURCE-SERVICE-AREA"
      ],
      "input_object_refs": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE"
      ],
      "business_rule_ids": [],
      "trigger": "申请人在调拨申请页点击暂存。",
      "preconditions": [
        "申请人具备调出服务区管理员身份。"
      ],
      "data_effects": [
        "保存已填写字段，允许必填项暂时为空。"
      ],
      "result": "调拨单保存为草稿，不进入审核。",
      "success_result": "列表可按草稿状态找到并编辑。",
      "failure_paths": [
        "保存失败时保留当前表单内容并提示重试。"
      ],
      "compensation": [
        "无业务补偿；未成功保存不得改变单据状态。"
      ],
      "entry_points": [
        "P-05 资产调拨页—申请弹窗"
      ],
      "feedback": [
        "提示暂存成功或明确保存失败原因。"
      ],
      "acceptance_criteria": [
        "部分字段为空时仍可保存草稿。"
      ],
      "state_transition_ids": [],
      "permission_ids": [
        "PERM-SERVICE-SAVE-DRAFT"
      ],
      "source_refs": [
        "SRC-PRD-L746-L761"
      ],
      "evidence_refs": [
        "EVD-TRANSFER-01"
      ],
      "certainty": "确定"
    },
    {
      "id": "ACT-TRANSFER-SUBMIT",
      "loop_id": "LOOP-TRANSFER-CLOSE",
      "name": "提交物资调拨申请",
      "intent": "提交完整调拨申请进入审核。",
      "initiator_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "responsible_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "actor_role_id": "ROLE-SERVICE-ADMIN",
      "object_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE",
        "OBJ-SOURCE-LEDGER",
        "OBJ-TARGET-LEDGER",
        "OBJ-TRANSFER-ASSET-ITEM"
      ],
      "data_scope_ids": [
        "SCOPE-SOURCE-SERVICE-AREA",
        "SCOPE-TARGET-SERVICE-AREA"
      ],
      "input_object_refs": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE"
      ],
      "business_rule_ids": [
        "RULE-TARGET-DIFFERENT",
        "RULE-QTY-POSITIVE",
        "RULE-QTY-AVAILABLE",
        "RULE-ENCODED-ASSET-SELECT",
        "RULE-ASSET-CODE-UNIQUE"
      ],
      "trigger": "申请人完成调入服务区、物资和数量填写后点击提交。",
      "preconditions": [
        "调入服务区已选择且不同于调出服务区。",
        "至少存在一条调拨明细。",
        "每条数量为大于 0 的整数且不超过当前可用数量。"
      ],
      "data_effects": [
        "记录申请人和申请时间。",
        "保留调出服务区为申请人所在服务区。"
      ],
      "result": "创建或更新调拨单并进入审核中。",
      "success_result": "调拨单状态从草稿变为审核中，列表刷新。",
      "failure_paths": [
        "字段校验失败时不改变状态并定位失败明细。",
        "提交时可用数量已变化时拒绝提交并要求重新加载。"
      ],
      "compensation": [
        "提交失败不写入业务状态。"
      ],
      "entry_points": [
        "P-05 资产调拨页—申请弹窗"
      ],
      "feedback": [
        "成功提示提交成功；数量不足提示调拨数量超过可用数量。"
      ],
      "acceptance_criteria": [
        "相同服务区不可提交；数量边界校验可判定；提交后仅审核角色可继续审核。"
      ],
      "state_transition_ids": [
        "TRANS-TRANSFER-DRAFT-REVIEWING"
      ],
      "permission_ids": [
        "PERM-SERVICE-SUBMIT"
      ],
      "source_refs": [
        "SRC-PRD-L744-L755"
      ],
      "evidence_refs": [
        "EVD-TRANSFER-02"
      ],
      "certainty": "有依据"
    },
    {
      "id": "ACT-TRANSFER-IMPORT-LINES",
      "loop_id": "LOOP-TRANSFER-CLOSE",
      "name": "导入调拨明细",
      "title": "导入调拨明细",
      "intent": "从 Excel 文件解析调拨明细并逐行反馈校验结果；合法行部分写入、重复导入幂等和草稿保留策略待用户决策。",
      "initiator_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "responsible_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "actor_role_id": "ROLE-SERVICE-ADMIN",
      "object_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE",
        "OBJ-TRANSFER-ASSET-ITEM"
      ],
      "data_scope_ids": [
        "SCOPE-SOURCE-SERVICE-AREA"
      ],
      "input_object_refs": [
        "OBJ-TRANSFER-LINE"
      ],
      "business_rule_ids": [
        "RULE-IMPORT-LINES",
        "RULE-QTY-POSITIVE",
        "RULE-ENCODED-ASSET-SELECT",
        "RULE-ASSET-CODE-UNIQUE"
      ],
      "trigger": "申请人在编辑草稿时选择 Excel 文件导入。",
      "preconditions": [
        "调拨单处于草稿状态",
        "申请人具有调出服务区数据范围"
      ],
      "data_effects": [
        "解析选择方式、数量、资产编码和来源行并逐行返回校验结果。",
        "是否写入合法行及失败行保留方式按 ISSUE-TRANSFER-IMPORT-SEMANTICS 决策。"
      ],
      "result": "展示导入校验结果，申请人可修正失败行后重试。",
      "success_result": "校验无错误且导入持久化策略已确认时，明细可进入草稿并继续编辑。",
      "failure_paths": [
        "文件格式错误时拒绝导入并说明格式原因",
        "明细重复、物资不存在、资产编码不可用或数量非法时逐行反馈",
        "导入失败不得改变调拨单状态"
      ],
      "compensation": [
        "不产生台账变更"
      ],
      "entry_points": [
        "P-05 资产调拨页—申请弹窗"
      ],
      "feedback": [
        "展示成功行数、失败行号和失败原因"
      ],
      "acceptance_criteria": [
        "每行都有可定位的校验结果",
        "资产编码选择不重复且来源范围可核对",
        "持久化方式以待用户决策项为准"
      ],
      "state_transition_ids": [],
      "permission_ids": [
        "PERM-SERVICE-IMPORT-LINES"
      ],
      "source_refs": [
        "SRC-PRD-L763-L765"
      ],
      "evidence_refs": [
        "EVD-TRANSFER-01"
      ],
      "certainty": "待确认"
    },
    {
      "id": "ACT-TRANSFER-APPROVE",
      "loop_id": "LOOP-TRANSFER-CLOSE",
      "name": "审核物资调拨申请",
      "intent": "由运营部或区域中心审核调拨申请是否可以交由调入方确认。",
      "initiator_role_ids": [
        "ROLE-OPERATIONS-ADMIN",
        "ROLE-REGION-ADMIN"
      ],
      "responsible_role_ids": [
        "ROLE-OPERATIONS-ADMIN",
        "ROLE-REGION-ADMIN"
      ],
      "actor_role_id": "ROLE-OPERATIONS-ADMIN",
      "object_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE"
      ],
      "data_scope_ids": [
        "SCOPE-ALL-SERVICE-AREAS"
      ],
      "input_object_refs": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE"
      ],
      "business_rule_ids": [
        "RULE-TRANSFER-AUDIT"
      ],
      "trigger": "审核角色打开审核中调拨单并选择通过。",
      "preconditions": [
        "调拨单状态为审核中。",
        "审核人拥有覆盖调出和调入服务区的数据范围。"
      ],
      "data_effects": [
        "记录审核人、审核时间和审核意见。"
      ],
      "result": "调拨单进入待确认。",
      "success_result": "调入服务区管理员获得确认入口。",
      "failure_paths": [
        "审核信息保存失败时状态保持审核中。"
      ],
      "compensation": [
        "无。"
      ],
      "entry_points": [
        "P-05 资产调拨页—审核弹窗"
      ],
      "feedback": [
        "提示审核完成。"
      ],
      "acceptance_criteria": [
        "只有运营部或区域中心审核角色可通过；通过后不能重复审核。"
      ],
      "state_transition_ids": [
        "TRANS-TRANSFER-REVIEWING-PENDING",
        "TRANS-TRANSFER-REVIEWING-PENDING-REGION",
        "TRANS-ASSET-STOCK-IN-TRANSFER-OPS",
        "TRANS-ASSET-STOCK-IN-TRANSFER-REGION"
      ],
      "permission_ids": [
        "PERM-OPS-APPROVE",
        "PERM-REGION-APPROVE"
      ],
      "source_refs": [
        "SRC-PRD-L767-L774"
      ],
      "evidence_refs": [
        "EVD-TRANSFER-03"
      ],
      "certainty": "确定"
    },
    {
      "id": "ACT-TRANSFER-REJECT-REVIEW",
      "loop_id": "LOOP-TRANSFER-CLOSE",
      "name": "驳回物资调拨申请",
      "intent": "在审核阶段终止不符合条件的调拨申请。",
      "initiator_role_ids": [
        "ROLE-OPERATIONS-ADMIN",
        "ROLE-REGION-ADMIN"
      ],
      "responsible_role_ids": [
        "ROLE-OPERATIONS-ADMIN",
        "ROLE-REGION-ADMIN"
      ],
      "actor_role_id": "ROLE-OPERATIONS-ADMIN",
      "object_ids": [
        "OBJ-TRANSFER-ORDER"
      ],
      "data_scope_ids": [
        "SCOPE-ALL-SERVICE-AREAS"
      ],
      "input_object_refs": [
        "OBJ-TRANSFER-ORDER"
      ],
      "business_rule_ids": [
        "RULE-TRANSFER-AUDIT"
      ],
      "trigger": "审核角色在审核弹窗选择驳回并填写审核意见。",
      "preconditions": [
        "调拨单状态为审核中。",
        "驳回意见已填写。"
      ],
      "data_effects": [
        "记录驳回人、时间和意见。"
      ],
      "result": "调拨单进入已驳回。",
      "success_result": "申请人可查看驳回原因，单据不再进入确认。",
      "failure_paths": [
        "驳回意见为空时禁止提交。"
      ],
      "compensation": [
        "无。"
      ],
      "entry_points": [
        "P-05 资产调拨页—审核弹窗"
      ],
      "feedback": [
        "提示审核完成。"
      ],
      "acceptance_criteria": [
        "驳回后调出和调入台账均不发生数量变化。"
      ],
      "state_transition_ids": [
        "TRANS-TRANSFER-REVIEWING-REJECTED",
        "TRANS-TRANSFER-REVIEWING-REJECTED-REGION"
      ],
      "permission_ids": [
        "PERM-OPS-REJECT",
        "PERM-REGION-REJECT"
      ],
      "source_refs": [
        "SRC-PRD-L767-L774"
      ],
      "evidence_refs": [
        "EVD-TRANSFER-03"
      ],
      "certainty": "确定"
    },
    {
      "id": "ACT-TRANSFER-CONFIRM",
      "loop_id": "LOOP-TRANSFER-CLOSE",
      "name": "确认接收调拨物资",
      "intent": "由调入服务区确认接收，完成双边台账数量回写。",
      "initiator_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "responsible_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "actor_role_id": "ROLE-SERVICE-ADMIN",
      "object_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE",
        "OBJ-SOURCE-LEDGER",
        "OBJ-TARGET-LEDGER",
        "OBJ-TRANSFER-ASSET-ITEM",
        "OBJ-TRANSFER-HISTORY"
      ],
      "data_scope_ids": [
        "SCOPE-SOURCE-SERVICE-AREA",
        "SCOPE-TARGET-SERVICE-AREA"
      ],
      "input_object_refs": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE"
      ],
      "business_rule_ids": [
        "RULE-QTY-AVAILABLE",
        "RULE-ATOMIC-POSTING",
        "RULE-TRANSFER-AUDIT",
        "RULE-LEDGER-STATE",
        "RULE-ASSET-CODE-UNIQUE"
      ],
      "trigger": "调入服务区管理员在待确认单据上点击确认接收。",
      "preconditions": [
        "调拨单状态为待确认。",
        "当前调出服务区仍有足够可用数量。",
        "调入服务区管理员只能确认目标服务区的数据。"
      ],
      "data_effects": [
        "调出侧关联台账或资产条目由调拨中转为已调出。",
        "调入侧台账或资产条目增加并进入在库。",
        "生成包含前后状态和数量的调拨履历。",
        "记录调入确认结果。"
      ],
      "result": "调拨单进入已完成。",
      "success_result": "两边台账和履历均可查询，用户看到调拨成功。",
      "failure_paths": [
        "数量不足时拒绝确认且不写入任一方。",
        "任一台账写入或履历写入失败时整体回滚并保留待确认状态。",
        "重复点击只允许一个确认成功。"
      ],
      "compensation": [
        "以事务回滚和幂等键避免单边扣减或单边状态变化；人工补偿流程作为未知项待确认。"
      ],
      "entry_points": [
        "P-05 资产调拨页—确认弹窗"
      ],
      "feedback": [
        "提示调拨成功或明确失败原因。"
      ],
      "acceptance_criteria": [
        "确认成功必须同时完成双边数量变化和履历生成；并发确认不能重复扣减。"
      ],
      "state_transition_ids": [
        "TRANS-TRANSFER-PENDING-COMPLETED",
        "TRANS-ASSET-IN-TRANSFER-COMPLETED"
      ],
      "permission_ids": [
        "PERM-TARGET-CONFIRM"
      ],
      "source_refs": [
        "SRC-PRD-L776-L780"
      ],
      "evidence_refs": [
        "EVD-TRANSFER-04"
      ],
      "certainty": "有依据"
    },
    {
      "id": "ACT-TRANSFER-REJECT-RECEIVE",
      "loop_id": "LOOP-TRANSFER-CLOSE",
      "name": "拒绝接收调拨物资",
      "intent": "由调入服务区拒绝待确认调拨并保留拒绝原因。",
      "initiator_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "responsible_role_ids": [
        "ROLE-SERVICE-ADMIN"
      ],
      "actor_role_id": "ROLE-SERVICE-ADMIN",
      "object_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE",
        "OBJ-SOURCE-LEDGER",
        "OBJ-TRANSFER-ASSET-ITEM",
        "OBJ-TRANSFER-HISTORY"
      ],
      "data_scope_ids": [
        "SCOPE-TARGET-SERVICE-AREA"
      ],
      "input_object_refs": [
        "OBJ-TRANSFER-ORDER"
      ],
      "business_rule_ids": [
        "RULE-LEDGER-STATE",
        "RULE-TRANSFER-AUDIT"
      ],
      "trigger": "调入服务区管理员在待确认单据上点击拒绝并填写原因。",
      "preconditions": [
        "调拨单状态为待确认。",
        "拒绝原因已填写。"
      ],
      "data_effects": [
        "调出侧调拨中条目恢复为在库。",
        "记录拒绝原因和状态恢复履历。"
      ],
      "result": "调拨单进入已驳回，台账数量不变。",
      "success_result": "申请人可查看拒绝原因。",
      "failure_paths": [
        "原因为空时禁止提交。"
      ],
      "compensation": [
        "无。"
      ],
      "entry_points": [
        "P-05 资产调拨页—拒绝确认框"
      ],
      "feedback": [
        "提示已拒绝。"
      ],
      "acceptance_criteria": [
        "拒绝后不能再次确认同一单据。"
      ],
      "state_transition_ids": [
        "TRANS-TRANSFER-PENDING-REJECTED",
        "TRANS-ASSET-IN-TRANSFER-REJECTED"
      ],
      "permission_ids": [
        "PERM-TARGET-REJECT"
      ],
      "source_refs": [
        "SRC-PRD-L782-L784"
      ],
      "evidence_refs": [
        "EVD-TRANSFER-05"
      ],
      "certainty": "确定"
    },
    {
      "id": "ACT-TRANSFER-VIEW",
      "loop_id": "LOOP-TRANSFER-CLOSE",
      "name": "查看物资调拨详情",
      "intent": "让参与角色追踪调拨单、明细、审核和确认结果。",
      "initiator_role_ids": [
        "ROLE-SERVICE-ADMIN",
        "ROLE-OPERATIONS-ADMIN",
        "ROLE-REGION-ADMIN"
      ],
      "responsible_role_ids": [
        "ROLE-SERVICE-ADMIN",
        "ROLE-OPERATIONS-ADMIN",
        "ROLE-REGION-ADMIN"
      ],
      "actor_role_id": "ROLE-SERVICE-ADMIN",
      "object_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE",
        "OBJ-TRANSFER-HISTORY"
      ],
      "data_scope_ids": [
        "SCOPE-SOURCE-SERVICE-AREA",
        "SCOPE-TARGET-SERVICE-AREA",
        "SCOPE-ALL-SERVICE-AREAS"
      ],
      "input_object_refs": [
        "OBJ-TRANSFER-ORDER"
      ],
      "business_rule_ids": [],
      "trigger": "用户在调拨列表点击调拨单号。",
      "preconditions": [
        "用户具有该单据数据范围内的查看权限。"
      ],
      "data_effects": [],
      "result": "展示单头、明细、审核记录和确认结果。",
      "success_result": "用户可以沿闭环追踪当前状态和责任人。",
      "failure_paths": [
        "单据不存在或无权访问时提示并返回列表。"
      ],
      "compensation": [
        "无。"
      ],
      "entry_points": [
        "P-05 资产调拨页—详情弹窗"
      ],
      "feedback": [
        "明确无权访问或数据不存在。"
      ],
      "acceptance_criteria": [
        "详情展示内容与当前状态和权限一致。"
      ],
      "state_transition_ids": [],
      "permission_ids": [
        "PERM-SERVICE-VIEW",
        "PERM-OPS-VIEW",
        "PERM-REGION-VIEW"
      ],
      "source_refs": [
        "SRC-PRD-L738-L742",
        "SRC-PRD-L786-L788"
      ],
      "evidence_refs": [
        "EVD-TRANSFER-06"
      ],
      "certainty": "确定"
    }
  ],
  "states": [
    {
      "id": "STATE-TRANSFER-DRAFT",
      "entity_id": "OBJ-TRANSFER-ORDER",
      "name": "草稿",
      "meaning": "申请尚未提交，可由申请人继续编辑。",
      "kind": "initial",
      "transitions": [
        {
          "id": "TRANS-TRANSFER-DRAFT-REVIEWING",
          "from_state_id": "STATE-TRANSFER-DRAFT",
          "to_state_id": "STATE-TRANSFER-REVIEWING",
          "action_id": "ACT-TRANSFER-SUBMIT",
          "actor_role_id": "ROLE-SERVICE-ADMIN",
          "trigger": "提交校验通过",
          "condition": "目标服务区不同且明细数量满足可用数量约束",
          "failure_handling": [
            "校验失败保持草稿并反馈"
          ]
        }
      ]
    },
    {
      "id": "STATE-TRANSFER-REVIEWING",
      "entity_id": "OBJ-TRANSFER-ORDER",
      "name": "审核中",
      "meaning": "等待运营部或区域中心审核；审核通过时调出侧关联物资进入调拨中。",
      "kind": "normal",
      "transitions": [
        {
          "id": "TRANS-TRANSFER-REVIEWING-PENDING",
          "from_state_id": "STATE-TRANSFER-REVIEWING",
          "to_state_id": "STATE-TRANSFER-PENDING",
          "action_id": "ACT-TRANSFER-APPROVE",
          "actor_role_id": "ROLE-OPERATIONS-ADMIN",
          "trigger": "审核通过",
          "condition": "审核意见已记录；调出侧物资状态同步为调拨中",
          "failure_handling": [
            "保存失败保持审核中"
          ]
        },
        {
          "id": "TRANS-TRANSFER-REVIEWING-REJECTED",
          "from_state_id": "STATE-TRANSFER-REVIEWING",
          "to_state_id": "STATE-TRANSFER-REJECTED",
          "action_id": "ACT-TRANSFER-REJECT-REVIEW",
          "actor_role_id": "ROLE-OPERATIONS-ADMIN",
          "trigger": "审核驳回",
          "condition": "驳回意见已记录",
          "failure_handling": [
            "意见缺失时禁止提交"
          ]
        },
        {
          "id": "TRANS-TRANSFER-REVIEWING-PENDING-REGION",
          "from_state_id": "STATE-TRANSFER-REVIEWING",
          "to_state_id": "STATE-TRANSFER-PENDING",
          "action_id": "ACT-TRANSFER-APPROVE",
          "actor_role_id": "ROLE-REGION-ADMIN",
          "trigger": "区域中心审核通过",
          "condition": "审核意见已记录且单据属于所辖服务区；调出侧物资状态同步为调拨中",
          "failure_handling": [
            "保存失败保持审核中"
          ]
        },
        {
          "id": "TRANS-TRANSFER-REVIEWING-REJECTED-REGION",
          "from_state_id": "STATE-TRANSFER-REVIEWING",
          "to_state_id": "STATE-TRANSFER-REJECTED",
          "action_id": "ACT-TRANSFER-REJECT-REVIEW",
          "actor_role_id": "ROLE-REGION-ADMIN",
          "trigger": "区域中心审核驳回",
          "condition": "驳回意见已记录且单据属于所辖服务区",
          "failure_handling": [
            "意见缺失时禁止提交"
          ]
        }
      ]
    },
    {
      "id": "STATE-TRANSFER-PENDING",
      "entity_id": "OBJ-TRANSFER-ORDER",
      "name": "待确认",
      "meaning": "审核通过，调出侧物资已进入调拨中，等待调入服务区确认接收。",
      "kind": "normal",
      "transitions": [
        {
          "id": "TRANS-TRANSFER-PENDING-COMPLETED",
          "from_state_id": "STATE-TRANSFER-PENDING",
          "to_state_id": "STATE-TRANSFER-COMPLETED",
          "action_id": "ACT-TRANSFER-CONFIRM",
          "actor_role_id": "ROLE-SERVICE-ADMIN",
          "trigger": "确认接收且双边回写成功",
          "condition": "数量、资产状态、事务和幂等校验通过；可用数量冻结或预占时点按待决策项执行",
          "failure_handling": [
            "任一写入失败整体回滚，恢复调出侧变更前状态并保持待确认"
          ]
        },
        {
          "id": "TRANS-TRANSFER-PENDING-REJECTED",
          "from_state_id": "STATE-TRANSFER-PENDING",
          "to_state_id": "STATE-TRANSFER-REJECTED",
          "action_id": "ACT-TRANSFER-REJECT-RECEIVE",
          "actor_role_id": "ROLE-SERVICE-ADMIN",
          "trigger": "调入方拒绝接收",
          "condition": "拒绝原因已记录，调出侧调拨中物资可恢复为在库",
          "failure_handling": [
            "原因缺失时禁止提交"
          ]
        }
      ]
    },
    {
      "id": "STATE-TRANSFER-COMPLETED",
      "entity_id": "OBJ-TRANSFER-ORDER",
      "name": "已完成",
      "meaning": "调拨闭环完成，调出侧物资为已调出，调入侧物资为在库，双边台账和履历已写入。",
      "kind": "terminal",
      "transitions": []
    },
    {
      "id": "STATE-TRANSFER-REJECTED",
      "entity_id": "OBJ-TRANSFER-ORDER",
      "name": "已驳回",
      "meaning": "申请在审核或调入确认阶段被拒绝；审核驳回不改变台账，调入拒绝将调出侧调拨中物资恢复为在库。",
      "kind": "terminal",
      "transitions": []
    },
    {
      "id": "STATE-ASSET-IN-STOCK",
      "entity_id": "OBJ-TRANSFER-ASSET-ITEM",
      "name": "在库",
      "meaning": "已编码物资可被调拨选择，尚未进入本次调拨。",
      "kind": "initial",
      "transitions": [
        {
          "id": "TRANS-ASSET-STOCK-IN-TRANSFER-OPS",
          "from_state_id": "STATE-ASSET-IN-STOCK",
          "to_state_id": "STATE-ASSET-IN-TRANSFER",
          "action_id": "ACT-TRANSFER-APPROVE",
          "actor_role_id": "ROLE-OPERATIONS-ADMIN",
          "trigger": "审核通过",
          "condition": "调出服务区范围和审核意见校验通过",
          "failure_handling": [
            "保存失败保持在库"
          ]
        },
        {
          "id": "TRANS-ASSET-STOCK-IN-TRANSFER-REGION",
          "from_state_id": "STATE-ASSET-IN-STOCK",
          "to_state_id": "STATE-ASSET-IN-TRANSFER",
          "action_id": "ACT-TRANSFER-APPROVE",
          "actor_role_id": "ROLE-REGION-ADMIN",
          "trigger": "区域中心审核通过",
          "condition": "单据属于所辖服务区且审核意见已记录",
          "failure_handling": [
            "保存失败保持在库"
          ]
        }
      ]
    },
    {
      "id": "STATE-ASSET-IN-TRANSFER",
      "entity_id": "OBJ-TRANSFER-ASSET-ITEM",
      "name": "调拨中",
      "meaning": "审核通过，资产条目已被本次调拨占用，等待调入确认；可用数量冻结或预占时点另由待决策项确定。",
      "kind": "normal",
      "transitions": [
        {
          "id": "TRANS-ASSET-IN-TRANSFER-COMPLETED",
          "from_state_id": "STATE-ASSET-IN-TRANSFER",
          "to_state_id": "STATE-ASSET-TRANSFERRED",
          "action_id": "ACT-TRANSFER-CONFIRM",
          "actor_role_id": "ROLE-SERVICE-ADMIN",
          "trigger": "调入确认成功",
          "condition": "目标服务区范围、数量、事务和幂等校验通过",
          "failure_handling": [
            "失败恢复在调拨中"
          ]
        },
        {
          "id": "TRANS-ASSET-IN-TRANSFER-REJECTED",
          "from_state_id": "STATE-ASSET-IN-TRANSFER",
          "to_state_id": "STATE-ASSET-IN-STOCK",
          "action_id": "ACT-TRANSFER-REJECT-RECEIVE",
          "actor_role_id": "ROLE-SERVICE-ADMIN",
          "trigger": "调入拒绝",
          "condition": "拒绝原因已记录",
          "failure_handling": [
            "保存失败保持调拨中"
          ]
        }
      ]
    },
    {
      "id": "STATE-ASSET-TRANSFERRED",
      "entity_id": "OBJ-TRANSFER-ASSET-ITEM",
      "name": "已调出",
      "meaning": "调拨确认成功，资产条目已从调出侧转移并在调入侧形成在库记录。",
      "kind": "terminal",
      "transitions": []
    }
  ],
  "permissions": [
    {
      "id": "PERM-SERVICE-SAVE-DRAFT",
      "role_id": "ROLE-SERVICE-ADMIN",
      "action_id": "ACT-TRANSFER-SAVE-DRAFT",
      "scope": "SCOPE-SOURCE-SERVICE-AREA",
      "decision": "允许",
      "conditions": [
        "仅能保存本人所在调出服务区的申请"
      ]
    },
    {
      "id": "PERM-SERVICE-SUBMIT",
      "role_id": "ROLE-SERVICE-ADMIN",
      "action_id": "ACT-TRANSFER-SUBMIT",
      "scope": "SCOPE-SOURCE-SERVICE-AREA",
      "decision": "允许",
      "conditions": [
        "申请人必须是调出服务区管理员"
      ]
    },
    {
      "id": "PERM-SERVICE-IMPORT-LINES",
      "role_id": "ROLE-SERVICE-ADMIN",
      "action_id": "ACT-TRANSFER-IMPORT-LINES",
      "scope": "SCOPE-SOURCE-SERVICE-AREA",
      "decision": "允许",
      "conditions": [
        "仅可导入调出服务区草稿的明细"
      ]
    },
    {
      "id": "PERM-OPS-APPROVE",
      "role_id": "ROLE-OPERATIONS-ADMIN",
      "action_id": "ACT-TRANSFER-APPROVE",
      "scope": "SCOPE-ALL-SERVICE-AREAS",
      "decision": "允许",
      "conditions": [
        "覆盖调出和调入服务区"
      ]
    },
    {
      "id": "PERM-REGION-APPROVE",
      "role_id": "ROLE-REGION-ADMIN",
      "action_id": "ACT-TRANSFER-APPROVE",
      "scope": "SCOPE-OWNED-SERVICE-AREAS",
      "decision": "允许",
      "conditions": [
        "仅覆盖其所辖服务区"
      ]
    },
    {
      "id": "PERM-OPS-REJECT",
      "role_id": "ROLE-OPERATIONS-ADMIN",
      "action_id": "ACT-TRANSFER-REJECT-REVIEW",
      "scope": "SCOPE-ALL-SERVICE-AREAS",
      "decision": "允许",
      "conditions": [
        "覆盖调出和调入服务区"
      ]
    },
    {
      "id": "PERM-REGION-REJECT",
      "role_id": "ROLE-REGION-ADMIN",
      "action_id": "ACT-TRANSFER-REJECT-REVIEW",
      "scope": "SCOPE-OWNED-SERVICE-AREAS",
      "decision": "允许",
      "conditions": [
        "仅覆盖其所辖服务区"
      ]
    },
    {
      "id": "PERM-TARGET-CONFIRM",
      "role_id": "ROLE-SERVICE-ADMIN",
      "action_id": "ACT-TRANSFER-CONFIRM",
      "scope": "SCOPE-TARGET-SERVICE-AREA",
      "decision": "允许",
      "conditions": [
        "只能确认目标服务区的调拨单"
      ]
    },
    {
      "id": "PERM-TARGET-REJECT",
      "role_id": "ROLE-SERVICE-ADMIN",
      "action_id": "ACT-TRANSFER-REJECT-RECEIVE",
      "scope": "SCOPE-TARGET-SERVICE-AREA",
      "decision": "允许",
      "conditions": [
        "只能拒绝目标服务区的调拨单"
      ]
    },
    {
      "id": "PERM-SERVICE-VIEW",
      "role_id": "ROLE-SERVICE-ADMIN",
      "action_id": "ACT-TRANSFER-VIEW",
      "scope": "SCOPE-SOURCE-SERVICE-AREA",
      "decision": "允许",
      "conditions": [
        "仅查看参与本服务区的调拨单"
      ]
    },
    {
      "id": "PERM-OPS-VIEW",
      "role_id": "ROLE-OPERATIONS-ADMIN",
      "action_id": "ACT-TRANSFER-VIEW",
      "scope": "SCOPE-ALL-SERVICE-AREAS",
      "decision": "允许",
      "conditions": []
    },
    {
      "id": "PERM-REGION-VIEW",
      "role_id": "ROLE-REGION-ADMIN",
      "action_id": "ACT-TRANSFER-VIEW",
      "scope": "SCOPE-OWNED-SERVICE-AREAS",
      "decision": "允许",
      "conditions": [
        "仅覆盖其所辖服务区"
      ]
    }
  ],
  "issues": [
    {
      "id": "ISSUE-TRANSFER-LOCK-TIMING",
      "nature": "待用户决策",
      "impact": "高",
      "evidence_level": "证据不足",
      "summary": "需要确认可用数量何时冻结或预占：提交、审核通过还是调入确认。",
      "affected_ids": [
        "LOOP-TRANSFER-CLOSE",
        "ACT-TRANSFER-SUBMIT",
        "ACT-TRANSFER-CONFIRM",
        "OBJ-SOURCE-LEDGER"
      ],
      "blocking": true,
      "description": "原始材料只规定提交和确认时不得超过可用数量，没有明确中间阶段的并发占用策略。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "确认冻结/预占时点及并发失败后的用户处理方式。",
      "owner": "产品负责人",
      "status": "待确认"
    },
    {
      "id": "ISSUE-TRANSFER-COMPENSATION",
      "nature": "未知项",
      "impact": "一般",
      "evidence_level": "证据不足",
      "summary": "双边回写失败后的人工补偿入口未在原始材料中定义。",
      "affected_ids": [
        "ACT-TRANSFER-CONFIRM",
        "OBJ-TRANSFER-HISTORY"
      ],
      "blocking": false,
      "description": "设计要求事务回滚避免单边扣减；若外部数据库或历史记录服务不可用，人工补偿责任尚未定义。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "在技术方案评审时确定重试、告警和人工补偿责任。",
      "owner": "技术负责人",
      "status": "待确认"
    },
    {
      "id": "ISSUE-TRANSFER-FINANCE-ROLE",
      "nature": "待用户决策",
      "impact": "高",
      "evidence_level": "已证实",
      "summary": "原始材料的财务部管理员权限矩阵与调拨流程表对审核角色的描述不一致。",
      "affected_ids": [
        "ROLE-FINANCE-ADMIN",
        "ACT-TRANSFER-APPROVE",
        "ACT-TRANSFER-VIEW"
      ],
      "blocking": true,
      "description": "在确认财务部管理员是否参与调拨查看和审核前，不得静默排除或放开该角色。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "由产品负责人确认财务部管理员在本闭环中的业务责任和数据范围。",
      "owner": "产品负责人",
      "status": "待确认"
    },
    {
      "id": "ISSUE-TRANSFER-REGION-SCOPE",
      "nature": "确定性冲突",
      "impact": "高",
      "evidence_level": "已证实",
      "summary": "区域中心管理员范围应为所辖服务区，不应为全部服务区。",
      "affected_ids": [
        "ROLE-REGION-ADMIN",
        "SCOPE-OWNED-SERVICE-AREAS",
        "PERM-REGION-APPROVE",
        "PERM-REGION-REJECT",
        "PERM-REGION-VIEW"
      ],
      "blocking": false,
      "description": "已按原始材料将区域中心权限范围修正为所辖服务区。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "保持权限校验与组织关系同步。",
      "owner": "Design 生成者",
      "status": "已解决"
    },
    {
      "id": "ISSUE-TRANSFER-STATE-ROLE",
      "nature": "确定性冲突",
      "impact": "高",
      "evidence_level": "已证实",
      "summary": "审核业务操作的允许角色必须与审核状态转换执行角色一致。",
      "affected_ids": [
        "ACT-TRANSFER-APPROVE",
        "ACT-TRANSFER-REJECT-REVIEW",
        "STATE-TRANSFER-REVIEWING"
      ],
      "blocking": false,
      "description": "已补充区域中心审核状态转换；财务部管理员资格仍受独立待决策项约束。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "确认财务角色后同步补充或排除状态转换。",
      "owner": "Design 生成者",
      "status": "已解决"
    },
    {
      "id": "ISSUE-TRANSFER-DATA-DEFINITION",
      "nature": "产品风险",
      "impact": "高",
      "evidence_level": "已证实",
      "summary": "调拨单、调拨明细、双边台账和履历的字段、来源、唯一性、历史保留和回写约束已补充；可用数量冻结或预占仍单列待决策。",
      "affected_ids": [
        "OBJ-TRANSFER-ORDER",
        "OBJ-TRANSFER-LINE",
        "OBJ-SOURCE-LEDGER",
        "OBJ-TARGET-LEDGER",
        "OBJ-TRANSFER-HISTORY"
      ],
      "blocking": false,
      "description": "正文已给出字段的必填性、来源、格式、唯一性、历史保留、幂等和回写关联；实现不得以“系统处理”替代这些约束。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "按正文字段表实现，并在冻结/预占决策确定后补充并发口径。",
      "owner": "Design 生成者",
      "status": "已解决"
    },
    {
      "id": "ISSUE-TRANSFER-IMPORT-LINES",
      "nature": "确定性冲突",
      "impact": "高",
      "evidence_level": "已证实",
      "summary": "Excel 导入调拨明细及失败反馈属于本闭环的独立业务操作。",
      "affected_ids": [
        "ACT-TRANSFER-IMPORT-LINES",
        "OBJ-TRANSFER-LINE"
      ],
      "blocking": false,
      "description": "已补充业务操作、权限、入口、失败反馈和验收边界。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "实现时保持逐行校验和失败行可定位。",
      "owner": "Design 生成者",
      "status": "已解决"
    },
    {
      "id": "ISSUE-TRANSFER-INVENTORY-STATE",
      "nature": "产品风险",
      "impact": "高",
      "evidence_level": "已证实",
      "summary": "审核通过后的调出侧物资状态必须进入调拨中，拒绝或回滚恢复在库，完成后转为已调出。",
      "affected_ids": [
        "STATE-ASSET-IN-STOCK",
        "STATE-ASSET-IN-TRANSFER",
        "STATE-ASSET-TRANSFERRED",
        "RULE-LEDGER-STATE",
        "ACT-TRANSFER-APPROVE",
        "ACT-TRANSFER-CONFIRM",
        "ACT-TRANSFER-REJECT-RECEIVE"
      ],
      "blocking": false,
      "description": "原始材料要求审核通过后进入调拨中；已在契约中建立独立物资状态主线，并与调拨单状态、台账和履历关联。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "保持物资状态变化与调拨单状态转换原子一致。",
      "owner": "Design 生成者",
      "status": "已解决"
    },
    {
      "id": "ISSUE-TRANSFER-ENCODED-ASSET",
      "nature": "产品风险",
      "impact": "高",
      "evidence_level": "已证实",
      "summary": "已编码物资必须支持按单件、按物资先进先出和同单据混合选择。",
      "affected_ids": [
        "OBJ-TRANSFER-LINE",
        "OBJ-TRANSFER-ASSET-ITEM",
        "RULE-ENCODED-ASSET-SELECT",
        "RULE-ASSET-CODE-UNIQUE"
      ],
      "blocking": false,
      "description": "已补充选择方式、资产编码、FIFO 分配轨迹、唯一性、状态变化和验收。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "实现时保持资产编码来源、唯一性和状态履历可追溯。",
      "owner": "Design 生成者",
      "status": "已解决"
    },
    {
      "id": "ISSUE-TRANSFER-IMPORT-SEMANTICS",
      "nature": "待用户决策",
      "impact": "一般",
      "evidence_level": "证据不足",
      "summary": "Excel 导入出现部分错误时，合法行是否部分落库、重复导入如何幂等以及草稿如何保留尚未确定。",
      "affected_ids": [
        "ACT-TRANSFER-IMPORT-LINES",
        "OBJ-TRANSFER-LINE",
        "RULE-IMPORT-LINES"
      ],
      "blocking": false,
      "description": "原始材料只明确解析、填充和反馈错误，没有规定部分成功、重复导入和草稿保留语义；本 Design 不静默补齐。",
      "loop_ids": [
        "LOOP-TRANSFER-CLOSE"
      ],
      "suggested_action": "由产品负责人确认导入持久化和幂等策略后同步动作、字段和验收。",
      "owner": "产品负责人",
      "status": "待确认"
    }
  ],
  "analysis_coverage": {
    "protocol": "ShitPM V2 Design 分析协议",
    "items": [
      {
        "id": "A",
        "name": "最小 A：输入纪律",
        "group": "最小 A",
        "mode": "固定",
        "triggered": true,
        "status": "已执行",
        "summary": "分离原始材料事实、基于材料的设计推断和未决未知项；限定范围为物资调拨闭环。",
        "reason": "所有项目固定执行。",
        "evidence_refs": [
          "SRC-PRD-L21",
          "SRC-PRD-L730-L788"
        ],
        "issue_ids": [
          "ISSUE-TRANSFER-LOCK-TIMING",
          "ISSUE-TRANSFER-COMPENSATION"
        ],
        "loop_ids": [
          "LOOP-TRANSFER-CLOSE"
        ]
      },
      {
        "id": "B",
        "name": "完整 B：业务建模",
        "group": "完整 B",
        "mode": "固定",
        "triggered": true,
        "status": "已执行",
        "summary": "已建模调拨过程、单据与明细、双边台账、履历、业务操作、规则、异常、状态、数据和一致性关系。",
        "reason": "所有项目固定执行。",
        "evidence_refs": [
          "SRC-PRD-L244-L262",
          "SRC-PRD-L730-L788"
        ],
        "issue_ids": [
          "ISSUE-TRANSFER-LOCK-TIMING",
          "ISSUE-TRANSFER-COMPENSATION",
          "ISSUE-TRANSFER-DATA-DEFINITION",
          "ISSUE-TRANSFER-IMPORT-LINES",
          "ISSUE-TRANSFER-INVENTORY-STATE",
          "ISSUE-TRANSFER-ENCODED-ASSET",
          "ISSUE-TRANSFER-IMPORT-SEMANTICS"
        ],
        "loop_ids": [
          "LOOP-TRANSFER-CLOSE"
        ]
      },
      {
        "id": "C3",
        "name": "C3：权限",
        "group": "C3 权限",
        "mode": "风险触发",
        "triggered": true,
        "status": "已执行",
        "summary": "命中多角色、多组织和审批；已定义调出、审核、调入确认的数据范围与业务操作权限。",
        "reason": "服务区管理员、运营部管理员、区域中心管理员分别承担申请、审核和确认。",
        "evidence_refs": [
          "SRC-PRD-L114-L142",
          "SRC-PRD-L767-L784"
        ],
        "issue_ids": [
          "ISSUE-TRANSFER-FINANCE-ROLE",
          "ISSUE-TRANSFER-REGION-SCOPE",
          "ISSUE-TRANSFER-STATE-ROLE"
        ],
        "loop_ids": [
          "LOOP-TRANSFER-CLOSE"
        ]
      },
      {
        "id": "C4",
        "name": "C4：系统数据",
        "group": "C4 系统数据",
        "mode": "风险触发",
        "triggered": true,
        "status": "已执行",
        "summary": "命中数量、可用数量、双边一致性和并发风险；已定义原子回写、幂等和数量再校验责任。",
        "reason": "调拨数量受可用数量约束，完成时调出扣减、调入增加并生成履历。",
        "evidence_refs": [
          "SRC-PRD-L261",
          "SRC-PRD-L776-L780"
        ],
        "issue_ids": [
          "ISSUE-TRANSFER-LOCK-TIMING",
          "ISSUE-TRANSFER-COMPENSATION",
          "ISSUE-TRANSFER-INVENTORY-STATE",
          "ISSUE-TRANSFER-ENCODED-ASSET"
        ],
        "loop_ids": [
          "LOOP-TRANSFER-CLOSE"
        ]
      },
      {
        "id": "C5",
        "name": "C5：非功能",
        "group": "C5 非功能",
        "mode": "风险触发",
        "triggered": false,
        "status": "不适用",
        "summary": "本闭环材料未命中实时、设备、高并发、大数据量或长期留存的明确要求。",
        "reason": "当前闭环未给出专项非功能指标；并发一致性已纳入 C4。",
        "evidence_refs": [
          "SRC-PRD-L730-L788"
        ],
        "issue_ids": [],
        "loop_ids": [
          "LOOP-TRANSFER-CLOSE"
        ]
      },
      {
        "id": "C6",
        "name": "C6：集成",
        "group": "C6 集成",
        "mode": "风险触发",
        "triggered": true,
        "status": "已执行",
        "summary": "命中已编码物资的外部财务系统来源；已明确本期不做自动同步，并把编码来源和异常责任作为系统边界。",
        "reason": "外部财务系统提供既有资产编码，本期只消费其结果，不建立自动同步接口。",
        "evidence_refs": [
          "SRC-PRD-L1191-L1194",
          "SRC-PRD-L1158-L1161"
        ],
        "issue_ids": [],
        "loop_ids": [
          "LOOP-TRANSFER-CLOSE"
        ]
      },
      {
        "id": "C7",
        "name": "C7：验收",
        "group": "C7 验收",
        "mode": "固定",
        "triggered": true,
        "status": "已执行",
        "summary": "已为正常、边界、异常、权限、状态、数量一致性和审计结果定义可判定验收口径。",
        "reason": "所有项目固定执行。",
        "evidence_refs": [
          "SRC-PRD-L1175"
        ],
        "issue_ids": [
          "ISSUE-TRANSFER-IMPORT-LINES",
          "ISSUE-TRANSFER-INVENTORY-STATE",
          "ISSUE-TRANSFER-ENCODED-ASSET",
          "ISSUE-TRANSFER-IMPORT-SEMANTICS"
        ],
        "loop_ids": [
          "LOOP-TRANSFER-CLOSE"
        ]
      }
    ]
  }
}
```
<!-- SPM-CONTRACT-END -->
