#!/usr/bin/env python3
"""PRD 一致性检查分类与退出语义回归测试。"""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/python/prd-consistency-check.py"

DESIGN_EXTRA = """# 退款设计基线

## 页面清单

| 页面 | 终端 | 说明 |
|---|---|---|
| 退款列表 | PC | 查看退款 |

## 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 退款编号 | 字符串 | 是 | 无 | 无 | 退款服务 | 退款唯一编号 |

## 权限定义

### 退款列表
- 运营人员：允许查看退款
"""

DESIGN = """# 设计基线

## 页面清单

| 页面 | 终端 | 说明 |
|---|---|---|
| 订单列表 | PC | 查看订单 |

## 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""

PRD_BASE = """# 订单 PRD

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 页面任务 |
|---|---|---|
| 订单列表 | 管理端 | 查看订单 |

## 功能需求

### 订单管理

#### 4.1.1 模块概览

##### 功能概述

订单管理接收订单并完成状态推进。

##### 角色与能力矩阵

| 角色 | 查看订单 | 导出订单 |
|---|---|---|
| 运营人员 | 可 | 可 |
| 财务人员 | 可 | 否 |

#### 4.1.2 订单

##### 业务过程

订单创建后进入处理，处理完成后结束。

##### 对象规则

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

##### 异常与边界

订单写入失败时保留原状态。

##### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 新建订单 | 无有效状态 | 使用默认状态草稿 | 状态精确匹配 |

#### 4.1.3 页面功能

##### 订单列表

运营人员查看订单编号和状态。
"""


NEW_STRUCTURE_PRD = """# 订单 PRD

## 功能需求

### 客户履约业务闭环

#### 4.1.1 模块概览

##### 功能概述

模块按业务结果组织。

##### 角色与能力矩阵

| 角色 | 查看订单 |
|---|---|
| 运营人员 | 可 |

#### 4.1.2 订单确认

##### 业务过程

订单确认动作在允许状态下完成。

##### 对象规则

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

##### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 查看订单 | 已创建订单 | 展示订单编号和状态 | 字段值与 Design 一致 |
"""


# 新模板四列字段表：| 字段 | 类型/取值 | 来源或约束 | 使用说明 |，枚举值内联在"类型/取值"列。
NEW_TEMPLATE_4COL_PRD = """# 订单 PRD

## 功能需求

### 履约闭环

#### 4.1.1 模块概览

##### 功能概述

履约闭环维护订单。

##### 角色与能力矩阵

| 角色 | 查看订单 |
|---|---|
| 运营人员 | 可 |

#### 4.1.2 订单

##### 业务过程

订单创建后进入处理。

##### 对象规则

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 订单编号 | 字符串 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举：草稿、已完成 | 订单服务 | 订单处理状态 |

##### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 新建订单 | 未提交状态 | 默认为草稿 | 状态精确匹配 |
"""

# 新模板四列字段表 + 显式"必填"列（对抗探针 CLEAN 写法）。
NEW_TEMPLATE_5COL_PRD = """# 订单 PRD

## 功能需求

### 履约闭环

#### 4.1.1 模块概览

##### 功能概述

履约闭环维护订单。

##### 角色与能力矩阵

| 角色 | 查看订单 |
|---|---|
| 运营人员 | 可 |

#### 4.1.2 订单

##### 业务过程

订单创建后进入处理。

##### 对象规则

| 字段 | 类型/取值 | 必填 | 来源或约束 | 使用说明 |
|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举：草稿、已完成 | 是 | 订单服务 | 订单处理状态 |

##### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 新建订单 | 未提交状态 | 默认为草稿 | 状态精确匹配 |
"""

PAGE_MAPPING_PRD = """# 订单 PRD

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 所属业务闭环 | 主要承接阶段 |
|---|---|---|---|
| 订单列表 | 管理端 | 客户履约业务闭环 | 订单确认 |
| 现场处置 | 移动端 | 客户履约业务闭环 | 订单确认 |
"""

# 斜杠合并字段（如"反馈人/回复人"）应拆分匹配，不整体判为缺失或新增。
SLASH_FIELD_DESIGN = """# 设计基线

## 页面清单

| 页面 | 终端 | 说明 |
|---|---|---|
| 订单列表 | PC | 查看订单 |

## 字段定义

### 报告意见反馈

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 反馈人 | 关联 | 否 | 无 | 无 | 用户表 | 反馈提交人 |
| 回复人 | 关联 | 否 | 无 | 无 | 用户表 | 审计方回复人 |
"""

SLASH_FIELD_PRD = """# PRD 正文

## 功能需求

### 反馈闭环

#### 4.1.1 模块概览

##### 功能概述

反馈闭环保存报告意见。

##### 角色与能力矩阵

| 角色 | 查看反馈 |
|---|---|
| 运营人员 | 可 |

#### 4.1.2 报告意见反馈

##### 业务过程

报告意见提交后形成反馈记录。

##### 对象规则

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 反馈人/回复人 | 关联 | 被审单位/审计方 | 留痕 |

##### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 提交反馈 | 反馈人与回复人已确定 | 两项均写入反馈记录 | 人员标识精确匹配 |
"""

# 页面"数据字典"与 PRD 章节同名，不应被章节黑名单误过滤。
DICT_PAGE_DESIGN = """# 设计基线

## 页面清单

| 页面 | 终端 | 说明 |
|---|---|---|
| 数据字典 | PC | 枚举与编码配置 |
"""

DICT_PAGE_PRD = """# PRD 正文

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 页面任务 |
|---|---|---|
| 数据字典 | PC | 配置枚举与编码 |

## 功能需求

### 系统管理

#### 4.1.1 模块概览

##### 功能概述

系统管理维护基础字典。

##### 角色与能力矩阵

| 角色 | 配置数据字典 |
|---|---|
| 管理员 | 可 |

#### 4.1.2 数据字典对象

##### 业务过程

管理员维护枚举与编码。

##### 对象规则

数据字典名称必须唯一。

##### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 保存字典 | 唯一名称 | 保存成功 | 名称精确匹配 |

#### 4.1.3 页面功能

##### 数据字典

管理员查看并维护枚举与编码。
"""

# 状态组合值拆分 + "下一状态"列读取 + 同章节箭头列表状态表达。
COMBINED_STATE_PRD = """# PRD 正文

## 功能需求

### 系统管理

#### 4.10.5 状态与业务规则

| 对象 | 状态 | 规则 |
|---|---|---|
| 检查项 | 启用/停用 | 可切换 |
| 审批流程实例 | 进行中/已通过 | 流转 |

#### 4.10.6 状态机

| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
|---|---|---|---|---|---|
| 草稿 | 编辑中 | 编制人 | 发送签署 | 已发出 | — |
| 已发出 | 签署中 | 用户 | 签署 | 待签署 | — |
"""

# PRD 写作规则禁止把状态表写进正文，合规 PRD 只能用自然语言枚举状态；
# 该写法必须能被识别，否则状态维度会整体误报（Design 状态全被判遗漏）。
DESIGN_WITH_STATE_MACHINE = """# 设计基线

### 页面：订单列表

- 页面目的：查看订单
- 适用角色：运营人员
- 进入条件：已登录
- 数据范围：本组织
- 主要状态：无状态机

#### 状态机：订单状态

| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
| --- | --- | --- | --- | --- | --- |
| 草稿 | 编制中 | 经办人 | 提交 | 待审核 | — |
| 待审核 | 等待审核 | 审核人 | 通过 | 已完成 | — |
| 已完成 | 结束 | — | — | — | — |
"""

PRD_PROSE_STATES = """# 订单 PRD

## 详细需求说明

订单编号为订单唯一编号。

#### 4.1.5 状态与业务规则

订单状态分为草稿、待审核与已完成三种枚举值。
"""

# 同名"状态"字段按对象区分（年度计划 vs 审批流程实例），不得跨对象误配属性。
SAME_NAME_DESIGN = """# 设计基线

## 数据字典

### 年度计划

| 字段 | 类型 | 必填 | 枚举值 / 规则 | 说明 |
|---|---|---|---|---|
| 状态 | 枚举 | 是 | 草稿/待审批/已通过 | 计划状态 |

### 审批流程实例

| 字段 | 类型 | 必填 | 枚举值 / 规则 | 说明 |
|---|---|---|---|---|
| 状态 | 枚举 | 是 | 进行中/已通过/已驳回 | 实例状态 |
"""

SAME_NAME_PRD = """# PRD 正文

## 功能需求

### 计划模块

#### 4.1.1 模块概览

##### 功能概述

计划模块维护年度计划。

##### 角色与能力矩阵

| 角色 | 维护年度计划 |
|---|---|
| 计划人员 | 可 |

#### 4.1.2 年度计划

##### 业务过程

年度计划编制后提交审批。

##### 对象规则

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 状态 | 枚举 | 草稿/待审批/已通过 | 计划状态 |

##### 状态迁移

| 状态 | 动作 | 角色 | 条件 | 下一状态 | 失败保留 |
|---|---|---|---|---|---|
| 草稿 | 提交审批 | 计划人员 | 内容完整 | 待审批 | 保持草稿 |

##### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 查看计划状态 | 草稿 | 展示草稿 | 状态精确匹配 |
"""


# ── 权限维度：Design 事实读取收敛（design-index）+ PRD 侧 ID 空间边界 ──
#
# 覆盖 R23 根因 RC-1 / RC-2：
# - Design 侧权限必须来自 design-index 的 page/operation 必填属性 roles（不再走 stage-prep）；
# - PRD 侧「角色 × 业务能力」矩阵的列是业务能力，不得进入 page ID 空间；
# - 权限章节自身标题不得被当作权限页面名；
# - 两侧不同构时必须 not_evaluated，不得产生确定性冲突。

MODULE_INDEXED = """# 订单 模块设计

## 四、页面、区块、字段与操作设计

### 页面：订单列表
- 页面目的：查看订单
- 适用角色：运营人员、财务人员（含对账）
- 进入条件：已登录
- 数据范围：本组织
- 主要状态：无状态机

#### 区块：订单筛选
- 区块目的：按条件筛选订单

##### 字段表

| 字段名称 | 业务含义 | 字段来源 | 展示条件 | 输入与编辑规则 | 取值与默认规则 | 交互方式 | 校验与反馈 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 订单编号 | 订单唯一编号 | 订单服务 | 始终 | 只读 | 系统生成 | 文本 | 无 |

#### 页面操作
- 区块目的：页面级操作

##### 操作表

| 操作 | 适用角色 | 入口/触发方式 | 输入（字段级） | 展示与可用条件 | 是否二次确认 | 成功结果 | 数据与状态变化 | 失败与恢复 | 后续去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 导出订单 | 运营人员 | 顶部按钮 | 无 | 已选筛选 | 否 | 下载文件 | 无 | 提示重试 | 停留当前页 |
"""

_PERM_FIELD_BLOCK = """##### 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 系统生成 | 订单服务 | 订单唯一编号 |
"""

# 官方模板形态：「行 = 角色，列 = 业务能力」。
PRD_CAPABILITY_MATRIX = f"""# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.1 模块概览

##### 功能概述

订单管理维护订单。

##### 角色与能力矩阵

| 角色 | 查看订单 | 导出订单 |
|---|---|---|
| 运营人员 | 可 | 可 |
| 财务人员 | 可 | 否 |

#### 4.1.2 订单

##### 业务过程

订单创建后可被查看。

##### 对象规则

{_PERM_FIELD_BLOCK}"""

# 自然语言权限：能提取角色事实，但不做页面级确定性比对。
PRD_PROSE_PERMISSION = f"""# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.1 模块概览

##### 功能概述

订单管理维护订单。

##### 角色与能力矩阵

运营人员可以查看和导出订单；财务人员可以查看订单，但不能导出。外包人员不在本模块可见范围内。

#### 4.1.2 订单

##### 业务过程

订单创建后可被查看。

##### 对象规则

{_PERM_FIELD_BLOCK}"""

# 行=页面、列=角色的旧式矩阵：新结构中不作为规范写法，交人工核对。
PRD_ROW_OBJECT_PERMISSION = f"""# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.1 模块概览

##### 功能概述

订单管理维护订单。

##### 角色与能力矩阵

| 页面 | 运营人员 | 财务人员 |
|---|---|---|
| 订单列表 | 可 | 可 |

#### 4.1.2 订单

##### 业务过程

订单创建后可被查看。

##### 对象规则

{_PERM_FIELD_BLOCK}"""

# 旧格式（防回归）：「## 权限汇总 + ### 页面名 + - role：action」，与 Design 同构。
PRD_LEGACY_PERMISSION_SUMMARY = f"""# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.2 订单

##### 业务过程

订单创建后可被查看。

##### 对象规则

{_PERM_FIELD_BLOCK}

## 权限汇总

### 订单列表

- 运营人员：可查看、可导出
- 财务人员：可查看
"""

# 可选页面说明的两种最小形态：消费者必须按标题和实体工作，不依赖固定验收编号。
PRD_WITHOUT_PAGE_SPEC = """# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.4 业务流程

订单从待处理进入已完成。

#### 4.1.5 业务规则

订单编号是订单唯一标识。

#### 4.1.6 功能说明

##### 订单列表

查看订单。

##### 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

#### 4.1.7 异常处理

读取失败可重试。

#### 4.1.8 验收标准

订单编号一致，状态取值为草稿或已完成。

#### 4.1.9 待确认事项

无。
"""

PRD_WITH_PAGE_SPEC = """# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.4 业务流程

订单从待处理进入已完成。

#### 4.1.5 业务规则

订单编号是订单唯一标识。

#### 4.1.6 功能说明

##### 订单列表

查看订单。

##### 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

#### 4.1.7 页面说明

列表与详情共用字段只读规格。

#### 4.1.8 异常处理

读取失败可重试。

#### 4.1.9 验收标准

订单编号一致，状态取值为草稿或已完成。

#### 4.1.10 待确认事项

无。
"""


def _design_page_names(design: str) -> list[str]:
    names = []
    for match in re.finditer(r"(?m)^###\s*页面[：:]\s*(.+?)\s*$", design):
        names.append(match.group(1).strip())
    in_page_list = False
    for line in design.splitlines():
        stripped = line.strip()
        if re.match(r"^##\s*页面清单\s*$", stripped):
            in_page_list = True
            continue
        if in_page_list and stripped.startswith("## "):
            break
        if not in_page_list or not stripped.startswith("|") or re.match(r"^\|[\s\-:|]+\|$", stripped):
            continue
        first = stripped.strip("|").split("|")[0].strip()
        if first and first not in {"页面", "页面/入口", "入口"} and first not in names:
            names.append(first)
    return names


def _ensure_required_object_slots(text: str) -> str:
    """给测试夹具中已有对象单元补齐必需槽位，避免测试数据本身不满足新结构。"""
    slot_names = {"业务过程", "状态迁移", "对象规则", "异常与边界", "验收场景", "待确认"}
    container_names = {"模块概览", "功能概述", "对象关系", "角色与能力矩阵", "页面清单", "共用规则", "页面功能", "跨对象异常"}
    required = ("业务过程", "对象规则", "验收场景")

    def clean_title(title: str) -> str:
        title = re.sub(r"^\d+(?:\.\d+)*[.\s]*", "", title.strip())
        return title.strip()

    lines = text.split("\n")
    headings = []
    for line_no, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            headings.append((line_no, len(match.group(1)), clean_title(match.group(2))))
    insertions = []
    for index, (line_no, level, title) in enumerate(headings):
        if level < 3 or title in slot_names or title in container_names:
            continue
        end_line = len(lines)
        for next_line, next_level, _ in headings[index + 1:]:
            if next_level <= level:
                end_line = next_line
                break
        child_slots = {
            child_title for child_line, child_level, child_title in headings
            if line_no < child_line < end_line and child_level == level + 1 and child_title in slot_names
        }
        if not child_slots:
            continue
        missing = [slot for slot in required if slot not in child_slots]
        if not missing:
            continue
        block = []
        for slot in missing:
            block.extend([f"{'#' * (level + 1)} {slot}", ""])
            if slot == "业务过程":
                block.append("测试对象按业务顺序推进。")
            elif slot == "对象规则":
                block.append("测试对象按现有字段和规则处理。")
            else:
                block.extend([
                    "| 场景 | 输入 | 预期输出 | 精度或判定 |",
                    "|---|---|---|---|",
                    "| 补充测试场景 | 已有记录 | 展示记录 | 字段值精确匹配 |",
                ])
            block.append("")
        insertions.append((end_line, block))

    for insert_at, block in sorted(insertions, reverse=True):
        lines[insert_at:insert_at] = block
    return "\n".join(lines)


def complete_object_unit_fixture(prd: str, design: str) -> str:
    """为实体提取回归夹具补齐对象单元骨架。

    旧结构门禁由独立原始夹具覆盖；其余用例只回归实体提取和分类逻辑，
    因而保留原事实块，并在测试输入中补足模块概览、对象槽位和页面功能。
    """
    additions = []
    if not re.search(r"(?m)^#{3,6}\s+(?:\d+(?:\.\d+)*\s+)?模块概览\s*$", prd):
        overview = """### 测试模块

#### 4.8.1 模块概览

##### 功能概述

测试模块维护业务对象。
"""
        if not re.search(
            r"(?m)^#{2,6}\s+(?:\d+(?:\.\d+)*\s+)?(?:角色与能力矩阵|权限汇总|权限定义|权限矩阵)\s*$",
            prd,
        ):
            overview += """
##### 角色与能力矩阵

| 角色 | 查看业务对象 |
|---|---|
| 运营人员 | 可 |
"""
        additions.append(overview)
    if not re.search(r"(?m)^#{3,6}\s+(?:\d+(?:\.\d+)*\s+)?业务过程\s*$", prd):
        additions.append("""#### 4.8.2 测试对象

##### 业务过程

测试对象按业务顺序推进。
""")
    if not re.search(r"(?m)^#{3,6}\s+(?:\d+(?:\.\d+)*\s+)?对象规则\s*$", prd):
        additions.append("""##### 对象规则

测试对象按现有字段和规则处理。
""")
    if not re.search(r"(?m)^#{3,6}\s+(?:\d+(?:\.\d+)*\s+)?验收场景\s*$", prd):
        additions.append("""##### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 查看测试对象 | 已有记录 | 展示记录 | 字段值精确匹配 |
""")
    if not re.search(r"(?m)^#{3,6}\s+(?:\d+(?:\.\d+)*\s+)?页面功能\s*$", prd):
        pages = _design_page_names(design)
        page_blocks = "\n".join(f"##### {name}\n\n{name}按页面任务展示业务结果。" for name in pages)
        if not page_blocks:
            page_blocks = "本模块按页面任务展示业务结果。"
        additions.append(f"#### 4.8.3 页面功能\n\n{page_blocks}\n")
    result = "\n".join(additions) + "\n\n" + prd if additions else prd
    return _ensure_required_object_slots(result)


def run_case(prd: str, design: str = DESIGN, complete_structure: bool = True, module: str | None = None, extra_module_design: str | None = None):
    if complete_structure:
        prd = complete_object_unit_fixture(prd, design)
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "output/design").mkdir(parents=True)
        (root / "output/prd").mkdir(parents=True)
        write_design_set(root, design, extra_module_design)
        (root / "output/prd/prd.md").write_text(prd, encoding="utf-8")
        command = [sys.executable, str(SCRIPT), "--project-root", str(root)]
        if module:
            command.extend(["--module", module])
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"检查输出不是 JSON: {result.stdout}\n{result.stderr}") from exc
        return result.returncode, report


def write_design_set(root: Path, design_text: str, extra_module_design: str | None = None) -> None:
    """构造最小多文件 Design 集：地图 + 清单 + 一个或两个模块文件。"""
    import hashlib
    design_dir = root / "output/design"
    module_dir = design_dir / "模块设计" / "订单"
    module_dir.mkdir(parents=True, exist_ok=True)
    module_path = module_dir / "订单管理.md"
    module_path.write_text(design_text, encoding="utf-8")
    extra_path = None
    if extra_module_design is not None:
        extra_dir = design_dir / "模块设计" / "退款"
        extra_dir.mkdir(parents=True, exist_ok=True)
        extra_path = extra_dir / "退款管理.md"
        extra_path.write_text(extra_module_design, encoding="utf-8")
    map_path = design_dir / "设计地图.md"
    map_lines = [
        "# 设计地图", "", "## 模块与职责", "",
        "- MOD-001 [订单](模块设计/订单/订单管理.md)：负责订单。",
    ]
    if extra_path is not None:
        map_lines.append("- MOD-002 [退款](模块设计/退款/退款管理.md)：负责退款。")
    map_path.write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    def sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "shitpm-design-set/v1",
        "set_sha256": "",
        "files": [
            {"id": "MAP-001", "path": "设计地图.md", "type": "map", "module": None, "business_chains": [], "depends_on": [], "sha256": sha(map_path)},
            {"id": "MOD-001", "path": "模块设计/订单/订单管理.md", "type": "module", "module": "订单", "business_chains": ["订单业务链"], "depends_on": [], "sha256": sha(module_path)},
        ],
        "decisions": [],
    }
    if extra_path is not None:
        manifest["files"].append({
            "id": "MOD-002",
            "path": "模块设计/退款/退款管理.md",
            "type": "module",
            "module": "退款",
            "business_chains": ["退款业务链"],
            "depends_on": [],
            "sha256": sha(extra_path),
        })
    parts = []
    for f in sorted(manifest["files"], key=lambda x: x["id"]):
        parts.append(f["id"] + f["path"] + f["sha256"])
    manifest["set_sha256"] = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
    (design_dir / "设计集清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

def main() -> int:
    code, report = run_case(PRD_BASE)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"完全一致样本应为 ok/0: {code}, {report.get('exit_reason')}")

    # 旧结构不得返回失败或通过，必须明确输出未检查。
    legacy_structure_prd = """# 订单 PRD

## 详细需求说明

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |

## 权限定义

### 订单列表

- 运营人员：允许查看订单
"""
    code, report = run_case(legacy_structure_prd, complete_structure=False)
    if code != 0 or report.get("exit_reason") != "not_evaluated":
        raise AssertionError(f"旧结构应输出未检查/0: {code}, {report.get('exit_reason')}")
    if report.get("structure_evaluation", {}).get("status") != "not_evaluated":
        raise AssertionError(f"旧结构结构状态错误: {report.get('structure_evaluation')}")
    if report.get("summary", {}).get("check_status") != "not_evaluated":
        raise AssertionError(f"旧结构摘要不得显示已评估: {report.get('summary')}")
    if any(report.get("classification", {}).get(section, {}).get("count") for section in (
        "deterministic_conflicts", "possible_omissions", "needs_semantic_judgment"
    )):
        raise AssertionError("旧结构未检查时不得输出确定性问题结论")

    # 只有模块概览、页面功能但对象槽位未嵌入对象单元的伪结构，必须未检查。
    malformed_structure_prd = """# 订单 PRD

## 模块概览

##### 功能概述

只有导航，没有对象单元。

## 详细需求说明

### 业务过程

订单创建后进入处理。

### 状态迁移

| 状态 | 动作 | 角色 | 条件 | 下一状态 | 失败保留 |
|---|---|---|---|---|---|
| 草稿 | 提交 | 运营人员 | 有订单编号 | 已完成 | 保持草稿 |

## 页面功能

##### 订单列表

查看订单。
"""
    code, report = run_case(malformed_structure_prd, complete_structure=False)
    if code != 0 or report.get("exit_reason") != "not_evaluated":
        raise AssertionError(f"槽位不在对象单元下时应未检查: {code}, {report.get('exit_reason')}")

    # 附录中的示例对象单元不能被当作目标模块对象；对象单元必须位于功能需求模块范围内。
    appendix_example_prd = """# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.1 模块概览

##### 功能概述

订单管理维护订单。

#### 4.1.2 页面功能

##### 订单列表

查看订单。

## 附录

### 示例对象

#### 业务过程

示例流程。

#### 对象规则

示例规则。

#### 验收场景

| 场景 | 输入 | 预期输出 | 精度或判定 |
|---|---|---|---|
| 示例 | 1 | 2 | 精确 |
"""
    code, report = run_case(appendix_example_prd, complete_structure=False)
    if code != 0 or report.get("exit_reason") != "not_evaluated":
        raise AssertionError(f"模块外示例对象不应让结构通过: {code}, {report.get('exit_reason')}")

    # 页面名只出现在其他页面正文中，不能被当作页面级正文落点。
    two_page_design = DESIGN.replace(
        "| 订单列表 | PC | 查看订单 |",
        "| 订单列表 | PC | 查看订单 |\n| 订单详情 | PC | 查看详情 |",
    )
    page_mention_prd = PRD_BASE.replace(
        "运营人员查看订单编号和状态。",
        "运营人员查看订单编号和状态；订单详情由另一个页面打开。",
    )
    code, report = run_case(page_mention_prd, design=two_page_design, complete_structure=False)
    if code != 0 or report.get("exit_reason") != "possible_omission":
        raise AssertionError(f"页面只在正文出现时应报告落点遗漏: {code}, {report.get('exit_reason')}")
    body_issues = report.get("classification", {}).get("possible_omissions", {}).get("page_body", [])
    if not any(item.get("name") == "订单详情" for item in body_issues):
        raise AssertionError(f"页面正文落点遗漏未分类: {body_issues}")

    # 页面完全未出现在 PRD 时，也必须形成落点遗漏，而不是静默通过。
    code, report = run_case(PRD_BASE, design=two_page_design, complete_structure=False)
    if code != 0 or report.get("exit_reason") != "possible_omission":
        raise AssertionError(f"页面完全缺失时应报告落点遗漏: {code}, {report.get('exit_reason')}")
    missing_pages = report.get("classification", {}).get("possible_omissions", {}).get("page_body", [])
    if not any(item.get("name") == "订单详情" for item in missing_pages):
        raise AssertionError(f"完全缺失页面未分类: {missing_pages}")

    # --module 必须切出目标模块，其他模块的额外字段不能污染结果。
    extra_module = PRD_BASE + """

### 4.9 退款

#### 4.9.1 退款字段

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 不存在字段 | 字符串 | 否 | 无 | 无 | 退款服务 | 其他模块字段 |
"""
    code, report = run_case(extra_module, complete_structure=False, module="订单")
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"--module 未隔离其他模块字段: {code}, {report.get('exit_reason')}")

    code, report = run_case(extra_module, complete_structure=False)
    if code != 0 or report.get("exit_reason") != "not_evaluated":
        raise AssertionError(f"多模块未指定 --module 时不应误判: {code}, {report.get('exit_reason')}")

    # Design 索引也必须按目标模块过滤，其他模块的页面和字段不能成为目标模块遗漏。
    code, report = run_case(
        PRD_BASE,
        design=DESIGN,
        complete_structure=False,
        module="订单",
        extra_module_design=DESIGN_EXTRA,
    )
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"Design 索引未按目标模块过滤: {code}, {report.get('exit_reason')}")

    # 标题名定位不依赖末位编号。
    renumbered_prd = (
        PRD_BASE.replace("4.1.1", "7.3.1")
        .replace("4.1.2", "7.3.2")
        .replace("4.1.3", "7.3.3")
    )
    code, report = run_case(renumbered_prd, complete_structure=False)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"重编号对象单元应按标题名正常检查: {code}, {report.get('exit_reason')}")
    if report.get("structure_evaluation", {}).get("status") != "evaluated":
        raise AssertionError(f"重编号对象单元未按标题名识别: {report.get('structure_evaluation')}")

    hallucinated = PRD_BASE.replace(
        "| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |",
        "| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |\n| 不存在字段 | 字符串 | 否 | 无 | 无 | 订单服务 | 幻觉字段 |",
    )
    code, report = run_case(hallucinated)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"幻觉字段应阻断并返回 1: {code}, {report.get('exit_reason')}")
    if not report["classification"]["deterministic_conflicts"]["fields"]:
        raise AssertionError("幻觉字段未进入 deterministic_conflict 分类")

    # 回归：Design 没有的泛化字段「主题指标」继续被识别为确定性多出字段。
    theme_index_prd = PRD_BASE.replace(
        "| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |",
        "| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |\n| 主题指标 | 枚举 | 否 | 无 | 无 | 统计服务 | 泛化指标字段 |",
    )
    code, report = run_case(theme_index_prd)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"主题指标应继续被识别为确定性多出字段: {code}, {report.get('exit_reason')}")
    theme_items = [
        f for f in report["classification"]["deterministic_conflicts"]["fields"]
        if (f.get("name") if isinstance(f, dict) else f) == "主题指标"
    ]
    if not theme_items:
        raise AssertionError(f"主题指标未进入确定性多出字段分类: {report['classification']['deterministic_conflicts']['fields']}")

    enum_conflict = PRD_BASE.replace("草稿、已完成", "草稿、已归档").replace("| 状态 | 枚举 | 是 | 草稿、已归档 |", "| 状态 | 枚举 | 是 | 草稿、已归档 |")
    code, report = run_case(enum_conflict)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"枚举冲突应阻断并返回 1: {code}, {report.get('exit_reason')}")

    # 角色与能力矩阵不是页面权限 ID 空间，只能输出两侧事实，不得伪造确定性权限结论。
    if report["permission_evaluation"]["status"] != "not_evaluated":
        raise AssertionError(f"角色与能力矩阵应标记未评估: {report['permission_evaluation']}")
    if report.get("permission_inversions"):
        raise AssertionError("角色与能力矩阵不得产生页面级权限反转")

    required_reversal = PRD_BASE.replace("| 订单编号 | 字符串 | 是 |", "| 订单编号 | 字符串 | 否 |", 1)
    code, report = run_case(required_reversal)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"必填反转应阻断并返回 1: {code}, {report.get('exit_reason')}")
    if not report["classification"]["deterministic_conflicts"]["field_attributes"]:
        raise AssertionError("必填反转未进入 deterministic_conflict 分类")

    omission = PRD_BASE.replace("| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |\n", "")
    code, report = run_case(omission)
    if code != 0 or report.get("exit_reason") != "possible_omission":
        raise AssertionError(f"可能遗漏应保留分类但返回 0: {code}, {report.get('exit_reason')}")
    if not report["classification"]["possible_omissions"]["fields"]:
        raise AssertionError("可能遗漏未输出分类详情")

    semantic = PRD_BASE.replace("| 订单编号 | 字符串 |", "| 订单编号 | 整数 |", 1)
    code, report = run_case(semantic)
    if code != 0 or report.get("exit_reason") != "needs_semantic_judgment":
        raise AssertionError(f"字段类型差异应返回语义判断/0: {code}, {report.get('exit_reason')}")
    if not report["classification"]["needs_semantic_judgment"]["attribute_mismatches"]:
        raise AssertionError("语义判断项目未输出分类详情")

    code, report = run_case(NEW_STRUCTURE_PRD)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"分散字段和不同业务模块名称样本应为 ok/0: {code}, {report.get('exit_reason')}\n{report}")
    if report["extracted"]["prd_fields_count"] != 2:
        raise AssertionError(f"分散字段表未合并读取: {report['extracted']}")

    # 可选页面说明两种章节编号形态：现有消费者不依赖验收编号，两形态均应通过。
    for label, fixture in (("无页面说明", PRD_WITHOUT_PAGE_SPEC), ("有页面说明", PRD_WITH_PAGE_SPEC)):
        code, report = run_case(fixture)
        if code != 0 or report.get("exit_reason") != "ok":
            raise AssertionError(f"{label}样本应被现有消费者接受: {code}, {report.get('exit_reason')}\n{report.get('classification')}")
        if report["extracted"]["prd_fields_count"] != 2:
            raise AssertionError(f"{label}样本字段未被消费者提取: {report['extracted']}")

    # 存量标题兼容：明确容器标题不得成为页面实体，真实业务页面的括号仍保留。
    for label, title in (("全角括号", "页面说明（按需）"), ("半角括号", "页面说明(按需)")):
        fixture = PRD_WITH_PAGE_SPEC.replace("#### 4.1.7 页面说明", f"#### 4.1.7 {title}")
        code, report = run_case(fixture)
        if code != 0 or report.get("exit_reason") != "ok":
            raise AssertionError(f"{label}容器标题应按 ok/0 消费: {code}, {report.get('exit_reason')}\n{report.get('classification')}")
        if report["extracted"]["prd_fields_count"] != 2:
            raise AssertionError(f"{label}容器标题样本字段未被提取: {report['extracted']}")

    # Review Skill 按对象和标题名审查；验收场景不得重新引入规则 ID。
    review_skill = (ROOT / "skills/spm-prd-review/SKILL.md").read_text(encoding="utf-8-sig")
    for required in ("对象", "页面功能", "状态迁移", "验收场景带规则 ID"):
        if required not in review_skill:
            raise AssertionError(f"spm-prd-review 缺少对象单元审查入口: {required}")
    for forbidden in ("按“验收标准”标题核对规则 ID", "核对 `4.x.9` 引用的规则 ID"):
        if forbidden in review_skill:
            raise AssertionError(f"spm-prd-review 仍依赖规则 ID 或固定编号: {forbidden}")

    # 回归：斜杠合并字段拆分后应匹配 Design 两侧字段，不再整体判为缺失或新增。
    code, report = run_case(SLASH_FIELD_PRD, design=SLASH_FIELD_DESIGN)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"斜杠合并字段样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["extracted"]["prd_fields_count"] != 2:
        raise AssertionError(f"斜杠合并字段未拆分: {report['extracted']}")
    if report["fields"]["missing"] or report["fields"]["hallucinated"]:
        raise AssertionError(f"斜杠合并字段拆分后仍误报: {report['fields']}")

    # 回归：页面"数据字典"与章节同名，不应被黑名单误过滤为缺失。
    code, report = run_case(DICT_PAGE_PRD, design=DICT_PAGE_DESIGN)
    if code != 0:
        raise AssertionError(f"数据字典页面样本不应是确定性冲突: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["pages"]["missing"] or report["pages"]["hallucinated"]:
        raise AssertionError(f"数据字典页面被误报: {report['pages']}")


    # 回归：同名"状态"字段按对象区分，不跨对象误配属性。
    code, report = run_case(SAME_NAME_PRD, design=SAME_NAME_DESIGN)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"同名状态按对象区分样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["fields"]["attribute_mismatch"]:
        raise AssertionError(f"同名状态字段跨对象误配: {report['fields']['attribute_mismatch']}")

    # 回归：权限解析为空时输出"无法提取、需人工验收"信号，不显示为权限一致。
    no_perm_prd = re.sub(r"##### 角色与能力矩阵.*?(?=#### 4\.1\.2)", "", PRD_BASE, flags=re.S)
    code, report = run_case(no_perm_prd)
    perm_eval = report.get("permission_evaluation", {})
    if perm_eval.get("status") != "cannot_extract" or "需人工验收" not in perm_eval.get("message", ""):
        raise AssertionError(f"权限提取为空未给出无法提取信号: {perm_eval}")
    if report.get("permissions", {}).get("not_evaluated") is not True:
        raise AssertionError("权限未提取时 missing/hallucinated 应标记为 not_evaluated")

    # P1 回归：新模板"类型/取值"合并列 + 无"必填"列，严格照模板写不应误报确定性冲突。
    code, report = run_case(NEW_TEMPLATE_4COL_PRD)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"新模板四列字段表样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["extracted"]["prd_fields_count"] != 2:
        raise AssertionError(f"新模板四列字段表未合并读取: {report['extracted']}")

    # P1 回归：新模板四列 + 显式"必填"列（对抗探针 CLEAN 写法）同样应为 ok。
    code, report = run_case(NEW_TEMPLATE_5COL_PRD)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"新模板四列+必填列样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")

    # P1 回归：内联枚举仍须拦截真实冲突（枚举值差异 → deterministic_conflict/1）。
    enum_conflict_new = NEW_TEMPLATE_5COL_PRD.replace("枚举：草稿、已完成", "枚举：草稿、已归档")
    code, report = run_case(enum_conflict_new)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"新模板内联枚举冲突应阻断并返回 1: {code}, {report.get('exit_reason')}")
    enum_items = [item for item in report["classification"]["deterministic_conflicts"]["field_enums"] if item.get("name") == "状态"]
    if not enum_items or "已完成" not in enum_items[0].get("enum_missing", []):
        raise AssertionError(f"内联枚举冲突未正确归类: {enum_items}")

    # P2-1 回归：枚举值仅空白差异（Design「10年」vs PRD「10 年」）不应判确定性冲突。
    design_ws = DESIGN.replace("草稿、已完成", "10年、20年、永久")
    prd_ws = PRD_BASE.replace("草稿、已完成", "10 年、20 年、永久")
    code, report = run_case(prd_ws, design_ws)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"枚举空白差异应 ok/0: {code}, {report.get('exit_reason')}")
    # 真阳性仍须拦截：枚举值实质不同（「已归档」替换「永久」）判确定性冲突/1。
    enum_real = prd_ws.replace("10 年、20 年、永久", "10 年、20 年、已归档")
    code, report = run_case(enum_real, design_ws)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"枚举实质差异应确定性冲突: {code}, {report.get('exit_reason')}")

    # P1 回归：extract_prd_fields 能从"类型/取值"列解析内联枚举，且识别无"必填"列表。
    spec = importlib.util.spec_from_file_location("prd_consistency_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise AssertionError("无法加载一致性脚本模块")
    spec.loader.exec_module(module)
    business_page_fixture = PRD_WITH_PAGE_SPEC.replace(
        "#### 4.1.10 页面说明\n\n列表与详情共用字段只读规格。",
        "#### 4.1.10 页面功能\n\n##### 现场处置（移动端）\n\n列表与详情共用字段只读规格。",
    )
    if business_page_fixture == PRD_WITH_PAGE_SPEC:
        business_page_fixture = PRD_WITH_PAGE_SPEC + "\n\n#### 4.9.7 页面功能\n\n##### 现场处置（移动端）\n\n列表与详情共用字段只读规格。\n"
    headings = module.parse_headings(business_page_fixture)
    pages = module.extract_prd_pages(business_page_fixture, headings)
    if "现场处置（移动端）" not in pages:
        raise AssertionError(f"真实业务页面的括号被容器兼容逻辑吞掉: {pages}")

    headings = module.parse_headings(PAGE_MAPPING_PRD)
    pages = module.extract_prd_pages(PAGE_MAPPING_PRD, headings)
    if pages != ["订单列表", "现场处置"]:
        raise AssertionError(f"总体说明页面清单提取错误: {pages}")

    headings4 = module.parse_headings(NEW_TEMPLATE_4COL_PRD)
    tables4 = module.parse_tables_with_context(NEW_TEMPLATE_4COL_PRD, headings4)
    fields4 = module.extract_prd_fields(headings4, tables4, NEW_TEMPLATE_4COL_PRD)
    status4 = next((f for f in fields4 if f["name"] == "状态"), None)
    if status4 is None or status4.get("enum_values") != ["已完成", "草稿"]:
        raise AssertionError(f"新模板内联枚举未从类型/取值列解析: {status4}")
    if status4.get("has_required_column") is not False:
        raise AssertionError(f"新模板四列字段表应标记无必填列: {status4}")

    # 回归：Design 页面只在页面清单出现、未在“页面功能”形成正文落点 → 页面正文落点可能遗漏。
    page_list_only_prd = """# PRD 正文

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 所属业务闭环 | 主要承接阶段 |
|---|---|---|---|
| 两客一危统计 | 管理端 | 两客一危核查与告警 | 统计与下钻 |
| 车辆信息记录 | 管理端 | 车辆记录与离场 | 记录查询 |

## 功能需求

### 两客一危核查与告警

#### 4.4.2 页面功能

##### 两客一危车辆查看

两客一危车辆查看展示比对状态和核查入口。
"""
    headings_pl = module.parse_headings(page_list_only_prd)
    landing = module.find_page_body_landing_issues(
        page_list_only_prd, headings_pl, ["两客一危统计", "车辆信息记录"]
    )
    omission_names = {item["name"] for item in landing["body_omissions"]}
    if "两客一危统计" not in omission_names:
        raise AssertionError(f"页面只在清单出现未列为可能遗漏: {landing}")
    if landing["page_merges"]:
        raise AssertionError(f"未出现合并时不应有合并候选: {landing}")
    # 页面在“页面功能”下有独立标题落点时不误报。
    landed_prd = page_list_only_prd.replace(
        "##### 两客一危车辆查看",
        "##### 两客一危统计\n\n两客一危统计展示统计指标。\n\n##### 两客一危车辆查看",
    )
    headings_lp = module.parse_headings(landed_prd)
    landing_lp = module.find_page_body_landing_issues(landed_prd, headings_lp, ["两客一危统计", "车辆信息记录"])
    if any(item["name"] == "两客一危统计" for item in landing_lp["body_omissions"]):
        raise AssertionError(f"页面已在“页面功能”落点仍被误报: {landing_lp}")

    # 回归：页面在“页面功能”中明确写出合并关系时，不判为确定性错误，交 Review 判断。
    merged_prd = """# PRD 正文

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 所属业务闭环 | 主要承接阶段 |
|---|---|---|---|
| 监控点列表 | 管理端 | 车流和车位实时监测 | 监控绑定 |
| 监控点详情 | 管理端 | 车流和车位实时监测 | 监控绑定 |
| 监控点位管理 | 管理端 | 车流和车位实时监测 | 监控绑定 |

## 功能需求

### 车流和车位实时监测

#### 4.2.2 页面功能

##### 监控点位管理

监控点列表与监控点详情合并为监控点位管理，绑定结果在详情中展示。
"""
    headings_mp = module.parse_headings(merged_prd)
    landing_mp = module.find_page_body_landing_issues(
        merged_prd, headings_mp, ["监控点列表", "监控点详情", "监控点位管理"]
    )
    if any(item["name"] in {"监控点列表", "监控点详情"} for item in landing_mp["body_omissions"]):
        raise AssertionError(f"明确合并页面不应列为可能遗漏: {landing_mp}")
    merge_names = {item["name"] for item in landing_mp["page_merges"]}
    if not {"监控点列表", "监控点详情"} <= merge_names:
        raise AssertionError(f"合并页面未进入合并候选交 Review 判断: {landing_mp}")
    if "监控点位管理" in merge_names:
        raise AssertionError(f"有独立“页面功能”标题落点的合并结果页不应进入合并候选: {landing_mp}")

    # 回归：状态组合值拆分 + "下一状态"列 + 同章节箭头状态都应被提取。
    headings_cs = module.parse_headings(COMBINED_STATE_PRD)
    tables_cs = module.parse_tables_with_context(COMBINED_STATE_PRD, headings_cs)
    states_cs = module.extract_prd_states(COMBINED_STATE_PRD, headings_cs, tables_cs)
    if set(states_cs) != {"启用", "停用", "进行中", "已通过", "草稿", "已发出", "待签署"}:
        raise AssertionError(f"状态组合值/下一状态/箭头未正确提取: {states_cs}")

    # 回归：PRD 用自然语言枚举状态时必须能提取（规范禁止正文用状态表）。
    headings_ps = module.parse_headings(PRD_PROSE_STATES)
    prose_states = module.extract_prd_prose_states(PRD_PROSE_STATES, headings_ps)
    if set(prose_states) != {"草稿", "待审核", "已完成"}:
        raise AssertionError(f"自然语言状态枚举未正确提取: {prose_states}")

    # 回归：下拉框/筛选项等界面构件里的括号枚举不是业务状态，不得被当状态来源。
    ui_prd = "## 详细需求说明\n\n筛选栏常设运行状态下拉框（全部状态、在营中、已停用）。\n"
    headings_ui = module.parse_headings(ui_prd)
    ui_states = module.extract_prd_prose_states(ui_prd, headings_ui)
    if ui_states:
        raise AssertionError(f"界面构件括号枚举被误当成业务状态: {ui_states}")

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "output/design").mkdir(parents=True)
        (root / "output/prd").mkdir(parents=True)
        write_design_set(root, DESIGN)
        missing = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if missing.returncode != 2:
            raise AssertionError(f"输入缺失应返回 2: {missing.returncode}")

    # 回归：Design 有状态机、PRD 用自然语言枚举时，已表达的状态不得判为遗漏。
    _, report_prose = run_case(PRD_PROSE_STATES, DESIGN_WITH_STATE_MACHINE)
    if report_prose["states"]["missing"]:
        raise AssertionError(f"PRD 已用自然语言表达的状态不应判为遗漏: {report_prose['states']}")
    if report_prose["state_evaluation"]["status"] != "extracted":
        raise AssertionError(f"状态已提取时应报告 extracted: {report_prose['state_evaluation']}")

    # 回归：真漏掉的状态必须仍被检出，修复不得把状态维度做成摆设。
    dropped_state = PRD_PROSE_STATES.replace("草稿、待审核与已完成", "草稿与已完成")
    _, report_dropped = run_case(dropped_state, DESIGN_WITH_STATE_MACHINE)
    if "待审核" not in report_dropped["states"]["missing"]:
        raise AssertionError(f"PRD 真漏的状态必须被检出: {report_dropped['states']}")

    # 回归：状态完全解析不到时标记未评估，不把解析失败伪造成遗漏清单。
    no_state_prd = "# 订单 PRD\n\n## 详细需求说明\n\n订单编号为订单唯一编号。\n"
    _, report_none = run_case(no_state_prd, DESIGN_WITH_STATE_MACHINE)
    if not report_none["states"].get("not_evaluated"):
        raise AssertionError(f"状态解析为空时应标记未评估: {report_none['states']}")
    if report_none["states"]["missing"]:
        raise AssertionError(f"未评估时不得输出状态遗漏清单: {report_none['states']['missing']}")
    if report_none["state_evaluation"]["status"] != "cannot_extract":
        raise AssertionError(f"状态解析为空时应报告 cannot_extract: {report_none['state_evaluation']}")

    # ── 权限维度回归（R23 RC-1 / RC-2）──
    # 1) 合规「角色 × 业务能力」矩阵：能力列不得进入 page ID 空间，章节自身标题不得被当页面名。
    code, report = run_case(PRD_CAPABILITY_MATRIX, design=MODULE_INDEXED)
    if code != 0:
        raise AssertionError(f"合规能力矩阵 PRD 不应阻断: exit={code}, {report.get('exit_reason')}")
    perms = report["permissions"]
    if perms["hallucinated"] or perms["missing"]:
        raise AssertionError(f"能力矩阵不应产生权限页面级冲突: {perms}")
    if "角色与权限" in perms["hallucinated"]:
        raise AssertionError("权限章节自身标题不得被当作权限页面名")
    facts = report["permission_facts"]
    if facts["design_source"] != "design-index":
        raise AssertionError(f"Design 侧权限应来自 design-index: {facts['design_source']}")
    if set(facts["design_roles"]) != {"运营人员", "财务人员"}:
        raise AssertionError(f"Design 角色切分应剥离括号且不混入条件式描述: {facts['design_roles']}")
    if facts["prd_permission_pages"]:
        raise AssertionError(f"能力列不得进入 page 集合: {facts['prd_permission_pages']}")
    if facts["prd_permission_capabilities"] != ["查看订单", "导出订单"]:
        raise AssertionError(f"业务能力列应作为事实输出: {facts['prd_permission_capabilities']}")
    if facts["comparable"]:
        raise AssertionError("两侧不同构时不得标记为可确定性比对")
    if report["permission_evaluation"]["status"] != "not_evaluated":
        raise AssertionError(f"两侧不同构应标记未评估: {report['permission_evaluation']}")

    # 2) 存量自然语言 4.x.3（审计系统形态）：红线——不得产生成批 missing。
    code, report = run_case(PRD_PROSE_PERMISSION, design=MODULE_INDEXED)
    if report["permissions"]["missing"]:
        raise AssertionError(f"PRD 用自然语言表达权限时不得判为缺失: {report['permissions']}")
    if report["permission_evaluation"]["status"] != "cannot_extract":
        raise AssertionError(f"PRD 权限无法提取时应报 cannot_extract: {report['permission_evaluation']}")
    if "Design 权限为空" in report["permission_evaluation"]["message"]:
        raise AssertionError("Design 侧已有权限事实时不得报「Design 权限为空」")

    # 3) 「行 = 页面，列 = 角色」与 Design 同构：必须保持确定性比对能力，不得被一并降级。
    code, report = run_case(PRD_ROW_OBJECT_PERMISSION, design=MODULE_INDEXED)
    facts = report["permission_facts"]
    if not facts["comparable"]:
        raise AssertionError("行=页面矩阵应可确定性比对")
    if report["permissions"]["matched_count"] < 1:
        raise AssertionError(f"行=页面矩阵应匹配到页面权限: {report['permissions']}")
    if report["permission_role_pairs"]["matched_count"] < 2:
        raise AssertionError(f"行=页面矩阵应匹配到角色对: {report['permission_role_pairs']}")
    if report["permissions"]["hallucinated"] or report["permission_role_pairs"]["hallucinated"]:
        raise AssertionError("行=页面矩阵不应产生幻觉判定")

    # 4) 旧格式「## 权限汇总 / ### 页面名 / - role：action」：确定性比对能力不得回退（RC-2 防回归）。
    code, report = run_case(PRD_LEGACY_PERMISSION_SUMMARY, design=MODULE_INDEXED)
    if code != 0:
        raise AssertionError(f"旧格式权限汇总不应阻断: exit={code}, {report.get('exit_reason')}")
    if not report["permission_facts"]["comparable"]:
        raise AssertionError("旧格式 权限汇总 应保持可确定性比对")
    if report["permissions"]["matched_count"] < 1:
        raise AssertionError(f"旧格式 权限汇总 应匹配到页面权限: {report['permissions']}")

    print("test-prd-consistency-semantics: PASS（新结构页面映射、分散字段、斜杠合并字段、数据字典页面、状态组合值、自然语言状态枚举、状态未评估、同名按对象、权限 zero 信号、权限事实来源收敛、能力列不进 page、行=页面矩阵仍确定性、旧格式权限汇总不回退、冲突、遗漏、语义判断和致命错误）")
    return 0


def test_empty_expected_entities_is_not_reported_enabled() -> None:
    """无实体可比对时不得报告“已启用、零预期”，否则“对账通过”与“无法对账”不可区分。"""
    spec = importlib.util.spec_from_file_location("prd_consistency_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    result = module._compare_indexed_structure({"pages": [], "blocks": [], "fields": [], "operations": []}, "# PRD\n", None)
    assert result["enabled"] is False, f"无预期实体时不得启用对账: {result}"
    assert result["expected_count"] == 0


def test_prd_consistency_semantics() -> None:
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
