#!/usr/bin/env python3
"""PRD 一致性检查分类与退出语义回归测试。"""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/python/prd-consistency-check.py"

DESIGN = """# 设计基线

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

## 名词说明

订单：业务订单。

## 详细需求说明

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""


NEW_STRUCTURE_PRD = """# 订单 PRD

## 总体说明

订单：业务订单。

## 功能需求

### 客户履约业务闭环

模块按业务结果组织，不复制 Design 的菜单模块名称。

#### 订单确认阶段

订单确认动作在允许状态下完成。

##### 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |

##### 订单状态阶段

订单状态用于表示业务处理状态。

##### 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""


# 新模板四列字段表：| 字段 | 类型/取值 | 来源或约束 | 使用说明 |，枚举值内联在"类型/取值"列。
NEW_TEMPLATE_4COL_PRD = """# 订单 PRD

## 功能需求

### 履约闭环

#### 字段定义

##### 订单对象

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 订单编号 | 字符串 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举：草稿、已完成 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""

# 新模板四列字段表 + 显式"必填"列（对抗探针 CLEAN 写法）。
NEW_TEMPLATE_5COL_PRD = """# 订单 PRD

## 功能需求

### 履约闭环

#### 字段定义

##### 订单对象

| 字段 | 类型/取值 | 必填 | 来源或约束 | 使用说明 |
|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举：草稿、已完成 | 是 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
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

#### 字段定义

##### 报告意见反馈

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 反馈人/回复人 | 关联 | 被审单位/审计方 | 留痕 |
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

| 页面/入口 | 终端 | 所属业务闭环 | 主要承接阶段 |
|---|---|---|---|
| 数据字典 | PC | 系统管理 | 配置 |
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

#### 字段定义

##### 年度计划

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 状态 | 枚举 | 草稿/待审批/已通过 | 计划状态 |
"""


def run_case(prd: str, design: str = DESIGN):
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "output/design").mkdir(parents=True)
        (root / "output/prd").mkdir(parents=True)
        (root / "output/design/design.md").write_text(design, encoding="utf-8")
        (root / "output/prd/prd.md").write_text(prd, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"检查输出不是 JSON: {result.stdout}\n{result.stderr}") from exc
        return result.returncode, report


def main() -> int:
    code, report = run_case(PRD_BASE)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"完全一致样本应为 ok/0: {code}, {report.get('exit_reason')}")

    hallucinated = PRD_BASE.replace(
        "| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |",
        "| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |\n| 不存在字段 | 字符串 | 否 | 无 | 无 | 订单服务 | 幻觉字段 |",
    )
    code, report = run_case(hallucinated)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"幻觉字段应阻断并返回 1: {code}, {report.get('exit_reason')}")
    if not report["classification"]["deterministic_conflicts"]["fields"]:
        raise AssertionError("幻觉字段未进入 deterministic_conflict 分类")

    enum_conflict = PRD_BASE.replace("草稿、已完成", "草稿、已归档").replace("| 状态 | 枚举 | 是 | 草稿、已归档 |", "| 状态 | 枚举 | 是 | 草稿、已归档 |")
    code, report = run_case(enum_conflict)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"枚举冲突应阻断并返回 1: {code}, {report.get('exit_reason')}")

    permission_reversal = PRD_BASE.replace("运营人员：允许查看订单", "运营人员：不可查看订单")
    code, report = run_case(permission_reversal)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"权限反转应阻断并返回 1: {code}, {report.get('exit_reason')}")
    if not report.get("permission_inversions"):
        raise AssertionError("权限反转未输出分类详情")

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
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"数据字典页面样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["pages"]["missing"] or report["pages"]["hallucinated"]:
        raise AssertionError(f"数据字典页面被误报: {report['pages']}")

    # 回归：同名"状态"字段按对象区分，不跨对象误配属性。
    code, report = run_case(SAME_NAME_PRD, design=SAME_NAME_DESIGN)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"同名状态按对象区分样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["fields"]["attribute_mismatch"]:
        raise AssertionError(f"同名状态字段跨对象误配: {report['fields']['attribute_mismatch']}")

    # 回归：权限解析为空时输出"无法提取、需人工验收"信号，不显示为权限一致。
    no_perm_prd = PRD_BASE.split("## 权限定义")[0].rstrip() + "\n"
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

    # 回归：状态组合值拆分 + "下一状态"列 + 同章节箭头状态都应被提取。
    headings_cs = module.parse_headings(COMBINED_STATE_PRD)
    tables_cs = module.parse_tables_with_context(COMBINED_STATE_PRD, headings_cs)
    states_cs = module.extract_prd_states(COMBINED_STATE_PRD, headings_cs, tables_cs)
    if set(states_cs) != {"启用", "停用", "进行中", "已通过", "草稿", "已发出", "待签署"}:
        raise AssertionError(f"状态组合值/下一状态/箭头未正确提取: {states_cs}")

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "output/design").mkdir(parents=True)
        (root / "output/prd").mkdir(parents=True)
        (root / "output/design/design.md").write_text(DESIGN, encoding="utf-8")
        missing = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if missing.returncode != 2:
            raise AssertionError(f"输入缺失应返回 2: {missing.returncode}")

    print("test-prd-consistency-semantics: PASS（新结构页面映射、分散字段、斜杠合并字段、数据字典页面、状态组合值、同名按对象、权限 zero 信号、冲突、遗漏、语义判断和致命错误）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
