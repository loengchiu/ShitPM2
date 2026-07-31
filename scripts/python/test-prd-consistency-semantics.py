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

    print("test-prd-consistency-semantics: PASS（新结构页面映射、分散字段、新模板内联枚举、冲突、遗漏、语义判断和致命错误）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
