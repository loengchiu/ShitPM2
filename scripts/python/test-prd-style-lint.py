#!/usr/bin/env python3
"""PRD 文风检查的十二类针对性回归测试（含新格式语义坏味道）。"""

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

## 总体说明

订单：业务订单的处理对象。

### 术语定义

| 术语 | 定义 |
|---|---|
| 订单 | 业务订单的处理对象 |

## 功能需求

### 订单处理业务闭环

订单处理模块承接订单查询和处理结果。

#### 处理阶段

###### 订单列表

订单列表展示当前用户可见的订单，用户可以按订单编号查询，查询结果保留当前筛选条件。


**确认订单**

运营人员在订单处于草稿状态时确认订单；确认成功后订单进入已完成状态，失败时不改变原状态。


| 字段 | 类型/取值 | 使用说明 |
|---|---|---|
| 订单编号 | 字符串 | 订单唯一编号 |
"""

CASES = {
    "STYLE001": "**关键动作：** 点击保存",
    "STYLE002": "1. 点击查询\n2. 选择条件\n3. 保存结果",
    "STYLE003": "## 功能需求\n\n### 订单处理业务闭环\n\n| 字段 | 类型 | 使用说明 |\n|---|---|---|\n| 订单编号 | 字符串 | 编号 |\n| 状态 | 枚举 | 状态 |\n| 创建时间 | 时间 | 创建时间 |",
    "STYLE004": "## 总体说明\n订单：业务订单。\n\n## 功能需求\n### 订单处理业务闭环\n**1.1 订单列表**\n**1.1 订单详情**",
    "STYLE005": "## 总体说明\n订单：业务订单。\n\n## 功能需求\n查询规则详见 3.2。",
    "STYLE006": "## 总体说明\n订单：业务订单。\n\n## 功能需求\n内部标识 FIELD-design-001 不展示给用户。",
    "STYLE007": "## 总体说明\n订单：业务订单。\n\n## 功能需求\n根据我的理解，这里展示订单。",
    "STYLE008": "## 总体说明\n订单：业务订单。\n\n## 功能需求\n字段说明：待补充。",
    "STYLE009": "# 订单 PRD\n\n## 功能需求\n订单处理模块展示订单。",
    "STYLE010": "## 功能需求\n### 订单处理业务闭环\n###### 订单列表\n页面职责：展示订单。\n使用对象：运营人员。\n入口与返回：菜单进入。\n区块清单：列表、筛选。",
    "STYLE011": "## 功能需求\n### 订单处理业务闭环\n###### 订单列表\n**返回**",
    "STYLE012": "## 功能需求\n### 订单处理业务闭环\n###### 订单列表\n字段名：订单编号。\n来源：用户输入。\n结果：列表展示。",
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

    # STYLE005 收窄：引用目标真实存在时不再产生提示（旧版对全部引用刷 info 是低价值噪音）。
    valid_ref = "## 总体说明\n订单：业务订单。\n\n## 功能需求\n### 3.2 订单查询\n查询规则详见 3.2。"
    style005_valid = [issue for issue in STYLE.run_lint(valid_ref) if issue.code == "STYLE005"]
    if style005_valid:
        raise AssertionError(f"目标存在的内部引用不应再提示: {style005_valid}")
    # 引用目标不存在才报 error。
    broken_ref = "## 总体说明\n订单：业务订单。\n\n## 功能需求\n查询规则详见 9.9。"
    style005_broken = [issue for issue in STYLE.run_lint(broken_ref) if issue.code == "STYLE005"]
    if not style005_broken or style005_broken[0].severity != "error":
        raise AssertionError(f"引用目标不存在应报 error: {style005_broken}")
    # 裸引用回归：见 §6.8 / （§10.1） / 按 §13.5 被识别为裸引用问题；
    # 目标不是当前 PRD 章节且未写 Design 前缀时报 error。
    bare_refs = "## 总体说明\n订单：业务订单。\n\n## 功能需求\n查询规则见 §6.8；时间口径（§10.1）按 Design 处理；导出按 §13.5 限制。"
    bare_issues = [issue for issue in STYLE.run_lint(bare_refs) if issue.code == "STYLE005" and issue.severity == "error"]
    if len(bare_issues) < 3:
        raise AssertionError(f"见 §6.8 /（§10.1）/ 按 §13.5 应被识别为裸引用: {bare_issues}")
    # “Design §6.8” 显式上游引用不误报。
    design_ref = "## 总体说明\n订单：业务订单。\n\n## 功能需求\n状态机见 Design §6.8。"
    design_issues = [issue for issue in STYLE.run_lint(design_ref) if issue.code == "STYLE005"]
    if design_issues:
        raise AssertionError(f"Design §x.x 显式上游引用不应误报: {design_issues}")
    # 裸引用目标是当前 PRD 真实章节时通过。
    valid_bare_ref = "## 总体说明\n订单：业务订单。\n\n## 功能需求\n### 6.8 告警规则\n告警规则见 §6.8。"
    valid_bare_issues = [issue for issue in STYLE.run_lint(valid_bare_ref) if issue.code == "STYLE005"]
    if valid_bare_issues:
        raise AssertionError(f"目标存在的裸引用不应误报: {valid_bare_issues}")

    # STYLE009 正向：模板合规的 H3「术语定义」章节应通过（不报 STYLE009）；
    # 旧名「名词说明」也应兼容通过。去掉「总体说明」别名后，无术语章节才报错。
    glossary_ok = "## 总体说明\n订单：业务订单。\n\n### 术语定义\n\n| 术语 | 定义 |\n|---|---|\n| 订单 | 业务订单 |\n\n## 功能需求\n订单处理模块展示订单。"
    if "STYLE009" in codes(STYLE.run_lint(glossary_ok)):
        raise AssertionError("含 H3 术语定义章节的样本不应报 STYLE009")
    glossary_old = "## 总体说明\n订单：业务订单。\n\n## 名词说明\n订单：业务订单。\n\n## 功能需求\n订单处理模块展示订单。"
    if "STYLE009" in codes(STYLE.run_lint(glossary_old)):
        raise AssertionError("含旧名名词说明章节的样本不应报 STYLE009")

    # STYLE010 回归：少于 3 个元数据标签行不报（元数据事实可融入语境）。
    meta_ok = "## 功能需求\n### 订单处理业务闭环\n###### 订单列表\n页面职责：展示订单。\n列表按订单编号排序。"
    if any(issue.code == "STYLE010" for issue in STYLE.run_lint(meta_ok)):
        raise AssertionError("少于 3 个元数据标签行不应判为元数据块")

    # STYLE011 回归：动作标题带业务结果（返回车辆列表）不误报。
    action_ok = "## 功能需求\n### 订单处理业务闭环\n###### 订单列表\n**返回车辆列表**"
    if any(issue.code == "STYLE011" for issue in STYLE.run_lint(action_ok)):
        raise AssertionError("带业务结果的动作标题不应误报 UI 动作词")

    # STYLE012 回归：单行或两行偶发冒号句不判为键值对模板。
    kv_ok = "## 功能需求\n### 订单处理业务闭环\n###### 订单列表\n字段名：订单编号。\n来源：用户输入。"
    if any(issue.code == "STYLE012" for issue in STYLE.run_lint(kv_ok)):
        raise AssertionError("少于 3 行的冒号句不应判为键值对模板")
    # 字段来源：作为页面元数据标签时按 STYLE010 连续块识别。
    meta_source = "## 功能需求\n### 订单处理业务闭环\n###### 订单列表\n页面职责：展示订单。\n使用对象：运营人员。\n字段来源：车辆记录。\n入口与返回：菜单进入。"
    if not any(issue.code == "STYLE010" for issue in STYLE.run_lint(meta_source)):
        raise AssertionError("字段来源：应参与页面元数据连续块识别")

    leading_label = "## 功能需求\n\n### 订单处理业务闭环\n\n**确认订单**\n\n触发：卡口摄像头推送数据。\n\n处理：系统创建订单。\n\n成功结果：订单可见。\n\n失败与恢复：识别失败进入异常。"
    leading_issues = STYLE.run_lint(leading_label)
    leading_errors = [issue for issue in leading_issues if issue.code == "STYLE001" and issue.severity == "error"]
    if len(leading_errors) < 4:
        raise AssertionError(f"行首标签式正文应识别 4 处以上: {leading_issues}")
    # 行中自然出现的"处理："（如"系统处理：xxx"）不得误报
    inline_sample = "## 总体说明\n订单：业务订单。\n\n## 功能需求\n系统处理：按规则执行。"
    inline = [i for i in STYLE.run_lint(inline_sample) if i.code == "STYLE001"]
    if inline:
        raise AssertionError(f"行中“系统处理：”不应判为行首标签: {inline}")

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

    print("test-prd-style-lint: PASS（十二类问题、严重级别和退出码）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
