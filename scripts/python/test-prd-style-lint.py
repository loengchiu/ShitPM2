#!/usr/bin/env python3
"""PRD 文风检查的十类针对性回归测试。"""

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/python/prd-style-lint.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prd_style_lint", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STYLE = load_module()

VALID = """# 订单 PRD

## 名词说明

订单：业务订单的处理对象。

## 详细需求说明

### 订单列表

订单列表展示当前用户可见的订单，用户可以按订单编号查询，查询结果保留当前筛选条件。

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
"""

CASES = {
    "STYLE001": "**关键动作：** 点击保存",
    "STYLE002": "1. 点击查询\n2. 选择条件\n3. 保存结果",
    "STYLE003": "## 名词说明\n订单：业务订单。\n\n## 详细需求说明\n| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |\n|---|---|---|---|---|---|---|\n| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |\n| 状态 | 枚举 | 否 | 草稿、完成 | 无 | 订单服务 | 订单状态 |\n| 创建时间 | 时间 | 是 | 无 | 无 | 订单服务 | 创建时间 |",
    "STYLE004": "## 名词说明\n订单：业务订单。\n\n## 详细需求说明\n**1.1 订单列表**\n**1.1 订单详情**",
    "STYLE005": "## 名词说明\n订单：业务订单。\n\n## 详细需求说明\n查询规则详见 3.2。",
    "STYLE006": "## 名词说明\n订单：业务订单。\n\n## 详细需求说明\n内部标识 FIELD-design-001 不展示给用户。",
    "STYLE007": "## 名词说明\n订单：业务订单。\n\n## 详细需求说明\n根据我的理解，这里展示订单。",
    "STYLE008": "## 名词说明\n订单：业务订单。\n\n## 详细需求说明\n字段说明：待补充。",
    "STYLE009": "# 订单 PRD\n\n## 详细需求说明\n订单列表展示订单。",
    "STYLE010": "# 订单 PRD\n\n## 名词说明\n订单：业务订单。\n\n## 详细需求说明\n| 字段 | 类型 | 必填 | 说明 |\n|---|---|---|---|\n| 订单编号 | 字符串 | 是 | 订单唯一编号 |",
}


def codes(issues):
    return {issue.code for issue in issues}


def main() -> int:
    valid_issues = STYLE.run_lint(VALID)
    errors = [issue for issue in valid_issues if issue.severity == "error"]
    if errors:
        raise AssertionError(f"完整样本不应有 error: {valid_issues}")

    for code, sample in CASES.items():
        found = codes(STYLE.run_lint(sample))
        if code not in found:
            raise AssertionError(f"未识别 {code}: {found}")

    warning_only = VALID + "\n字段按配置决定展示。\n"
    warning_issues = STYLE.run_lint(warning_only)
    if not warning_issues or any(issue.severity == "error" for issue in warning_issues):
        raise AssertionError(f"只有 warning/info 的样本结果不正确: {warning_issues}")
    if not any(issue.code == "STYLE008" and issue.severity == "warning" for issue in warning_issues):
        raise AssertionError(f"高误报占位表达未降为 warning: {warning_issues}")

    with tempfile.TemporaryDirectory() as temp_dir:
        prd = Path(temp_dir) / "prd.md"
        prd.write_text(VALID, encoding="utf-8")
        ok = subprocess.run([sys.executable, str(SCRIPT), str(prd)], capture_output=True, text=True, encoding="utf-8")
        if ok.returncode != 0:
            raise AssertionError(f"完整样本退出码应为 0: {ok.returncode}\n{ok.stdout}\n{ok.stderr}")
        warning_prd = Path(temp_dir) / "warning.md"
        warning_prd.write_text(warning_only, encoding="utf-8")
        warning = subprocess.run([sys.executable, str(SCRIPT), str(warning_prd)], capture_output=True, text=True, encoding="utf-8")
        if warning.returncode != 0:
            raise AssertionError(f"只有 warning/info 时退出码应为 0: {warning.returncode}\n{warning.stdout}")
        error_prd = Path(temp_dir) / "error.md"
        error_prd.write_text(VALID + "\n待补充。\n", encoding="utf-8")
        error = subprocess.run([sys.executable, str(SCRIPT), str(error_prd)], capture_output=True, text=True, encoding="utf-8")
        if error.returncode != 1:
            raise AssertionError(f"确定性 error 时退出码应为 1: {error.returncode}")

    missing = subprocess.run([sys.executable, str(SCRIPT), str(ROOT / "does-not-exist-prd.md")], capture_output=True, text=True, encoding="utf-8")
    if missing.returncode != 2:
        raise AssertionError(f"文件不存在时退出码应为 2: {missing.returncode}")

    print("test-prd-style-lint: PASS（十类问题、严重级别和退出码）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

