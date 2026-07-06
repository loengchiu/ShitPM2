#!/usr/bin/env python3
"""prd-style-lint.py — PRD 文风 lint 脚本

职责：检查 PRD 正文中可机械识别的 9 类问题。
不做业务语义判断，不做全文重写。

用法：python prd-style-lint.py <prd_file_path> [--format text|json] [--output <path>]

问题类型：
  STYLE001 - 标签式正文
  STYLE002 - 动作流水账特征
  STYLE003 - 表格主导
  STYLE004 - 重复页面编号
  STYLE005 - 跨节引用
  STYLE006 - 机读字段泄漏
  STYLE007 - AI 痕迹
  STYLE008 - 占位符
  STYLE009 - 名词说明章节缺失
"""

import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from shared_md import find_stable_id_leaks, load_json


@dataclass
class Issue:
    code: str
    severity: str  # error / warning / info
    line: int
    message: str
    suggestion: str


# 占位符/空话词与标签式正文：以 references/prd-writing.profile.json 的 forbidden_expressions 为单一事实源
# 加载失败时降级为内置兜底列表，保证脚本可独立运行
_PROFILE_PATH = Path(__file__).resolve().parent.parent.parent / "references" / "prd-writing.profile.json"
_PROFILE = load_json(_PROFILE_PATH) or {}
_PROFILE_FORBIDDEN = _PROFILE.get("constraints", {}).get("forbidden_expressions", [])

# 标签式正文模式：从 profile 的 ** 开头表达式动态生成（单一事实源）
# 降级兜底：profile 加载失败时使用内置 5 项
_FALLBACK_LABEL_EXPRS = [
    "**页面目标：**", "**关键动作：**", "**状态变化：**", "**异常提示：**", "**关联功能点：**",
]
_LABEL_EXPRS = [w for w in _PROFILE_FORBIDDEN if w.startswith("**")] or _FALLBACK_LABEL_EXPRS
LABEL_PATTERNS = []
for _expr in _LABEL_EXPRS:
    _name = _expr.strip("*").rstrip("：:").strip()
    _pat = r'\*\*' + re.escape(_name) + r'[：:]\*\*'
    LABEL_PATTERNS.append((_pat, f"{_name}标签"))

# 原因腔词：从 forbidden_expressions 中识别，单独检查以避免误报正常描述
# "方便用户""避免用户" 后接动词才是原因腔；"需支持""需考虑" 后接标点或行尾才是占位符
_CAUSE_VERB_CHARS = "操|作|查|看|浏|览|输|入|编|辑|删|除|添|加|修|改|选|择|点|击|提|交|保|存|取|消|关|闭|打|开|使|用"
CAUSE_PHRASE_PATTERNS = {
    "方便用户": re.compile(r'方便用户(?:' + _CAUSE_VERB_CHARS + r')'),
    "避免用户": re.compile(r'避免用户(?:' + _CAUSE_VERB_CHARS + r')'),
    "需支持": re.compile(r'需支持(?:[。，；、,\s]|$)'),
    "需考虑": re.compile(r'需考虑(?:[。，；、,\s]|$)'),
}
_CAUSE_PHRASE_WORDS = set(CAUSE_PHRASE_PATTERNS.keys())

PLACEHOLDER_PATTERNS = [w for w in _PROFILE_FORBIDDEN if not w.startswith("**") and w not in _CAUSE_PHRASE_WORDS] or [
    "待定", "待补充", "TBD", "TODO",
]
PLACEHOLDER_RULES = {
    "待定": re.compile(r'(?<![\u4e00-\u9fa5])待定(?!性|稿|人|项|状态|原因|结论|计划|方案)'),
    "待补充": re.compile(r'(?<![\u4e00-\u9fa5])待补充(?!说明|材料|资料|附件|内容|信息|证据|记录|明细|清单)'),
}

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

    特征：连续 3+ 个数字编号短步骤（`1.` `2.` `3.`），行很短（< 50 字符）。
    新编号体系下页面动作用 `·` 并列项，不触发本规则；
    本规则主要针对业务流程/处理链路里用 `1. 2. 3.` 写成的步骤流水账。
    """
    issues = []
    consecutive_steps = 0
    step_start_line = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^\d+\.\s*\S', stripped) and len(stripped) < 50:
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
    """STYLE004: 检查重复页面编号

    新编号体系下，页面用粗体块 `**N.N.N.N 页面名**` 表示。
    检查粗体块中的编号是否重复。
    """
    issues = []
    page_ids = {}

    # 只在详细需求说明章节内检查，避免字段定义表等误报
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

        # 匹配粗体块页面：**N.N.N 页面名** 或 **N.N.N.N 页面名**
        match = re.match(r'^\*\*(\d+(?:\.\d+)+)\s+.+?\*\*\s*$', stripped)
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
    for line_no, _match in find_stable_id_leaks('\n'.join(lines)):
        issues.append(Issue(
            code="STYLE006",
            severity="error",
            line=line_no,
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


def check_cause_phrase(lines: list) -> list:
    """检查原因腔表述（属于 STYLE008 的子检查）

    "方便用户""避免用户""需支持""需考虑"等词在 forbidden_expressions 中，
    但用 `in line` 匹配会误报正常描述（如"需支持多种场景"）。
    本检查用更精确的匹配：原因腔词后接特定上下文才报。
    """
    issues = []
    for i, line in enumerate(lines):
        for word, pattern in CAUSE_PHRASE_PATTERNS.items():
            if pattern.search(line):
                issues.append(Issue(
                    code="STYLE008",
                    severity="warning",
                    line=i + 1,
                    message=f"原因腔表述：发现 '{word}'",
                    suggestion="改用具体规则描述，不用原因腔",
                ))
    return issues


def check_placeholders(lines: list) -> list:
    """STYLE008: 检查占位符与原因腔表述"""
    issues = []
    for i, line in enumerate(lines):
        for pattern in PLACEHOLDER_PATTERNS:
            rule = PLACEHOLDER_RULES.get(pattern)
            if rule:
                if rule.search(line):
                    issues.append(Issue(
                        code="STYLE008",
                        severity="error",
                        line=i + 1,
                        message=f"占位符：发现 '{pattern}'",
                        suggestion="填写具体内容，不得使用占位符",
                    ))
            elif pattern in line:
                issues.append(Issue(
                    code="STYLE008",
                    severity="error",
                    line=i + 1,
                    message=f"占位符：发现 '{pattern}'",
                    suggestion="填写具体内容，不得使用占位符",
                ))
    # 原因腔词单独检查，避免误报正常描述
    issues.extend(check_cause_phrase(lines))
    return issues


def check_glossary_section(lines: list) -> list:
    """STYLE009: 检查名词说明章节存在性

    PRD 必须包含"名词说明"章节（别名"术语说明"），
    让研发在进入详细需求前建立统一术语认知。
    """
    issues = []
    has_glossary = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^#{1,2}\s.*名词说明', stripped) or re.match(r'^#{1,2}\s.*术语说明', stripped):
            has_glossary = True
            break

    if not has_glossary:
        issues.append(Issue(
            code="STYLE009",
            severity="error",
            line=1,
            message="缺少名词说明章节",
            suggestion="在文档概述之后、范围之前新增名词说明章节，按类别分组列出业务术语",
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
    check_glossary_section,
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
        print("用法: python prd-style-lint.py <prd_file> [--format text|json] [--output <path>]", file=sys.stderr)
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

    output_path = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = Path(sys.argv[idx + 1])

    with open(prd_path, encoding="utf-8") as f:
        content = f.read()

    issues = run_lint(content)

    json_output = format_json(issues)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_output)

    if output_format == "json":
        print(json_output)
    else:
        print(format_text(issues))

    if any(i.severity == "error" for i in issues):
        sys.exit(1)


if __name__ == "__main__":
    main()
