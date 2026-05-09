#!/usr/bin/env python3
"""prd-style-lint.py — PRD 文风 lint 脚本

职责：检查 PRD 正文中可机械识别的 8 类问题。
不做业务语义判断，不做全文重写。

用法：python prd-style-lint.py <prd_file_path> [--format text|json]

问题类型：
  STYLE001 - 标签式正文
  STYLE002 - 动作流水账特征
  STYLE003 - 表格主导
  STYLE004 - 重复页面编号
  STYLE005 - 跨节引用
  STYLE006 - 机读字段泄漏
  STYLE007 - AI 痕迹
  STYLE008 - 占位符
"""

import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Issue:
    code: str
    severity: str  # error / warning / info
    line: int
    message: str
    suggestion: str


# 标签式正文模式
LABEL_PATTERNS = [
    (r'\*\*页面目标[：:]\*\*', "页面目标标签"),
    (r'\*\*关键动作[：:]\*\*', "关键动作标签"),
    (r'\*\*状态变化[：:]\*\*', "状态变化标签"),
    (r'\*\*异常提示[：:]\*\*', "异常提示标签"),
    (r'\*\*关联功能点[：:]\*\*', "关联功能点标签"),
]

# 稳定 ID 泄漏模式
STABLE_ID_PATTERN = re.compile(r'(MODULE|PAGE|FIELD|RULE|FLOW|REL|REQ|RISK|CASE|WVR)-(design|prd)-\d{3}')

# 占位符模式
PLACEHOLDER_PATTERNS = [
    "待补充", "待定", "按配置", "按规范", "同常规", "TBD", "TODO",
    "需支持", "需考虑", "详见原型", "按业务规则", "具体数值见配置",
]

# AI 痕迹模式
AI_PATTERNS = [
    "作为AI", "作为 AI", "根据我的理解",
    "I will", "Let me", "Here is",
    "需要注意的是", "值得一提的是",
]


def check_label_style(lines: list) -> list:
    """STYLE001: 检查标签式正文"""
    issues = []
    for i, line in enumerate(lines):
        for pattern, label in LABEL_PATTERNS:
            if re.search(pattern, line):
                issues.append(Issue(
                    code="STYLE001",
                    severity="error",
                    line=i + 1,
                    message=f"发现标签式正文：{label}",
                    suggestion="改用自然规格说明段落，不用加粗标签拼接",
                ))
    return issues


def check_action_list(lines: list) -> list:
    """STYLE002: 检查动作流水账特征

    特征：连续 3+ 个编号步骤，每步以动词开头且行很短
    """
    issues = []
    consecutive_steps = 0
    step_start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^(\d+\.|（\d+）)\s*\S', stripped) and len(stripped) < 50:
            if consecutive_steps == 0:
                step_start_line = i + 1
            consecutive_steps += 1
        else:
            if consecutive_steps >= 3:
                issues.append(Issue(
                    code="STYLE002",
                    severity="warning",
                    line=step_start_line,
                    message=f"疑似动作流水账：连续 {consecutive_steps} 个短步骤",
                    suggestion="改用自然段落描述，加入展示规则、状态流转和异常边界",
                ))
            consecutive_steps = 0

    if consecutive_steps >= 3:
        issues.append(Issue(
            code="STYLE002",
            severity="warning",
            line=step_start_line,
            message=f"疑似动作流水账：连续 {consecutive_steps} 个短步骤",
            suggestion="改用自然段落描述，加入展示规则、状态流转和异常边界",
        ))

    return issues


def check_table_dominance(lines: list) -> list:
    """STYLE003: 检查表格主导

    特征：在"详细需求说明"章节中，表格行数 > 段落行数
    """
    issues = []
    in_detail_section = False
    table_lines = 0
    paragraph_lines = 0
    section_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 遇到同级或更高级标题时，结束当前详细需求章节统计
        if in_detail_section and re.match(r'^#{1,2}\s', stripped) and not re.match(r'^#{1,4}\s.*详细需求', stripped):
            if table_lines > 0 and (paragraph_lines == 0 or table_lines > paragraph_lines * 2):
                issues.append(Issue(
                    code="STYLE003",
                    severity="warning",
                    line=section_start,
                    message="表格行数远超段落数，疑似纯表格式页面正文",
                    suggestion="页面正文应以自然规格说明为主，表格仅用于天然映射内容",
                ))
            in_detail_section = False
            table_lines = 0
            paragraph_lines = 0

        if re.match(r'^#{1,4}\s.*详细需求', stripped):
            in_detail_section = True
            table_lines = 0
            paragraph_lines = 0
            section_start = i + 1
            continue

        if in_detail_section:
            if stripped.startswith('|') and '|' in stripped[1:]:
                table_lines += 1
            elif stripped and not stripped.startswith('#') and not stripped.startswith('<!--'):
                paragraph_lines += 1

    # 检查最后一个章节
    if in_detail_section and table_lines > 0 and (paragraph_lines == 0 or table_lines > paragraph_lines * 2):
        issues.append(Issue(
            code="STYLE003",
            severity="warning",
            line=section_start,
            message="表格行数远超段落数，疑似纯表格式页面正文",
            suggestion="页面正文应以自然规格说明为主，表格仅用于天然映射内容",
        ))

    return issues


def check_duplicate_page_ids(lines: list) -> list:
    """STYLE004: 检查重复页面编号"""
    issues = []
    page_ids = {}

    # 只在详细需求说明章节内检查，避免数据字典等章节误报
    in_detail = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^#{1,4}\s.*详细需求', stripped):
            in_detail = True
            continue
        if re.match(r'^#{1,3}\s', stripped) and in_detail:
            # 新的顶级章节，退出详细需求
            if re.match(r'^#{1,2}\s', stripped):
                in_detail = False
                continue
        if not in_detail:
            continue

        match = re.match(r'^#{2,4}\s+(\d+(?:\.\d+)*)\s*[\.、．]', stripped)
        if match:
            pid = match.group(1)
            if pid in page_ids:
                issues.append(Issue(
                    code="STYLE004",
                    severity="error",
                    line=i + 1,
                    message=f"页面编号重复：{pid}（首次出现在第 {page_ids[pid]} 行）",
                    suggestion="确保每个页面编号唯一",
                ))
            else:
                page_ids[pid] = i + 1

    return issues


def check_cross_section_refs(lines: list) -> list:
    """STYLE005: 检查跨节引用"""
    issues = []
    # 只匹配"见 X.X"、"参见 X.X"、"详见 X.X"，排除"参考"（太常见的词）
    cross_ref_pattern = re.compile(r'(?:见|参见|详见)\s*\d+\.\d+')

    for i, line in enumerate(lines):
        if cross_ref_pattern.search(line):
            issues.append(Issue(
                code="STYLE005",
                severity="info",
                line=i + 1,
                message="发现跨节引用，可能导致读者跳转",
                suggestion="考虑将相关内容直接写在当前段落",
            ))

    return issues


def check_stable_id_leak(lines: list) -> list:
    """STYLE006: 检查机读字段泄漏"""
    issues = []
    for i, line in enumerate(lines):
        matches = STABLE_ID_PATTERN.findall(line)
        for match in matches:
            issues.append(Issue(
                code="STYLE006",
                severity="error",
                line=i + 1,
                message="机读字段泄漏：稳定 ID 出现在正文",
                suggestion="稳定 ID 只存在于外置机读物，不得出现在人读正文",
            ))
    return issues


def check_ai_traces(lines: list) -> list:
    """STYLE007: 检查 AI 痕迹"""
    issues = []
    for i, line in enumerate(lines):
        for pattern in AI_PATTERNS:
            if pattern in line:
                issues.append(Issue(
                    code="STYLE007",
                    severity="warning",
                    line=i + 1,
                    message=f"AI 痕迹：发现 '{pattern}'",
                    suggestion="使用正式产品规格说明文风，避免 AI 对话痕迹",
                ))
    return issues


def check_placeholders(lines: list) -> list:
    """STYLE008: 检查占位符"""
    issues = []
    for i, line in enumerate(lines):
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern in line:
                issues.append(Issue(
                    code="STYLE008",
                    severity="error",
                    line=i + 1,
                    message=f"占位符：发现 '{pattern}'",
                    suggestion="填写具体内容，不得使用占位符",
                ))
    return issues


ALL_CHECKS = [
    check_label_style,
    check_action_list,
    check_table_dominance,
    check_duplicate_page_ids,
    check_cross_section_refs,
    check_stable_id_leak,
    check_ai_traces,
    check_placeholders,
]


def run_lint(content: str) -> list:
    """运行所有检查"""
    lines = content.split('\n')
    all_issues = []
    for check_fn in ALL_CHECKS:
        all_issues.extend(check_fn(lines))
    return all_issues


def format_text(issues: list) -> str:
    """文本格式输出"""
    if not issues:
        return "无问题"

    lines = []
    for issue in issues:
        lines.append(f"[{issue.severity.upper()}] {issue.code} L{issue.line}: {issue.message}")
        lines.append(f"  建议: {issue.suggestion}")
        lines.append("")

    error_count = sum(1 for i in issues if i.severity == "error")
    warning_count = sum(1 for i in issues if i.severity == "warning")
    info_count = sum(1 for i in issues if i.severity == "info")
    lines.append(f"汇总: {error_count} error, {warning_count} warning, {info_count} info")

    return "\n".join(lines)


def format_json(issues: list) -> str:
    """JSON 格式输出"""
    return json.dumps({
        "issues": [asdict(i) for i in issues],
        "summary": {
            "error": sum(1 for i in issues if i.severity == "error"),
            "warning": sum(1 for i in issues if i.severity == "warning"),
            "info": sum(1 for i in issues if i.severity == "info"),
        },
    }, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print("用法: python prd-style-lint.py <prd_file> [--format text|json]", file=sys.stderr)
        sys.exit(1)

    prd_path = Path(sys.argv[1]).resolve()
    if not prd_path.exists():
        print(f"错误: 文件不存在: {prd_path}", file=sys.stderr)
        sys.exit(2)

    output_format = "text"
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]

    with open(prd_path, encoding="utf-8") as f:
        content = f.read()

    issues = run_lint(content)

    if output_format == "json":
        print(format_json(issues))
    else:
        print(format_text(issues))

    if any(i.severity == "error" for i in issues):
        sys.exit(1)


if __name__ == "__main__":
    main()
