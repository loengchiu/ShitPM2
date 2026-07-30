#!/usr/bin/env python3
"""PRD 一致性检查分类与退出语义回归测试。"""

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

    print("test-prd-consistency-semantics: PASS（冲突、遗漏、语义判断和致命错误）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
