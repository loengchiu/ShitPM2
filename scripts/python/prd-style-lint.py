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
  STYLE010 - 页面元数据连续块
  STYLE011 - UI 动作词直接作为动作标题
  STYLE012 - 连续键值对句式承载正文
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


# 占位符/空话词与标签式正文：以 contracts/prd-writing.profile.json 的 forbidden_expressions 为单一事实源
# 加载失败时降级为内置兜底列表，保证脚本可独立运行
_PROFILE_PATH = Path(__file__).resolve().parent.parent.parent / "contracts" / "prd-writing.profile.json"
_PROFILE = load_json(_PROFILE_PATH) or {}
_PROFILE_FORBIDDEN = _PROFILE.get("constraints", {}).get("forbidden_expressions", [])

# 标签式正文模式：从 profile 的 forbidden_expressions 动态生成（单一事实源）
# 两类：
#   1. 加粗标签 `**名称：**`：出现在行中任意位置即报；
#   2. 行首标签 `名称：内容`（不带加粗，独立成行）：以 `^名称：` 行首锚定识别，
#      避免正文中"系统处理：xxx"等行中自然出现"处理："时误报。
# 降级兜底：profile 加载失败时使用内置完整列表（从 prd-writing.profile.json 同步）
_FALLBACK_LABEL_EXPRS = [
    "**页面目标：**", "**关键动作：**", "**状态变化：**", "**异常提示：**", "**关联功能点：**",
    "触发：", "处理：", "成功结果：", "失败与恢复：", "失败结果：",
]
_PLACEHOLDER_FALLBACK = [
    "按配置", "按规范", "同常规", "待补充", "需支持", "需考虑",
    "详见原型", "待定", "按业务规则", "具体数值见", "用于承载", "用于支撑",
    "方便用户", "避免用户", "符合操作", "TBD", "TODO",
]
_LABEL_EXPRS = [w for w in _PROFILE_FORBIDDEN if w.startswith("**") or w.endswith(("：", ":"))] or _FALLBACK_LABEL_EXPRS
LABEL_PATTERNS = []
LEADING_LABEL_PATTERNS = []
for _expr in _LABEL_EXPRS:
    _name = _expr.strip("*").rstrip("：:").strip()
    if _expr.startswith("**"):
        _pat = r'\*\*' + re.escape(_name) + r'[：:]\*\*'
        LABEL_PATTERNS.append((_pat, f"{_name}标签"))
    else:
        _pat = r'^\s*' + re.escape(_name) + r'[：:]'
        LEADING_LABEL_PATTERNS.append((_pat, f"{_name}标签"))

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

# 行首标签式表达式（触发：/处理：/成功结果：/失败与恢复：/失败结果：）属 STYLE001 标签域而非占位符；
# 且 STYLE008 按子串匹配，会从"系统处理：""数据处理："等合法正文中误伤，故从占位符集合排除，
# 只由 STYLE001 的行首锚定拦截（行首`触发：`→error，行内`系统处理：`→不误报）。
_PLACEHOLDER_EXCLUDED = {w for w in _LABEL_EXPRS if not w.startswith("**")}
PLACEHOLDER_PATTERNS = [w for w in _PROFILE_FORBIDDEN if not w.startswith("**") and w not in _CAUSE_PHRASE_WORDS and w not in _PLACEHOLDER_EXCLUDED] or _PLACEHOLDER_FALLBACK
# 只有明确的空占位才硬阻断；“按配置”等表达存在误报可能，作为 warning 交给 AI 判断。
_PLACEHOLDER_ERROR_TERMS = {"待补充", "待定", "TBD", "TODO"}
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
    """STYLE001: 检查标签式正文（加粗标签 + 行首标签两类）"""
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
        for pattern, label in LEADING_LABEL_PATTERNS:
            if re.search(pattern, line):
                issues.append(Issue(
                    code="STYLE001",
                    severity="error",
                    line=i + 1,
                    message=f"发现行首标签式正文：{label}",
                    suggestion="改用自然语言段落表达，不写成“标签：内容”式独立行",
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
    """STYLE003: 检查业务模块正文是否被表格主导。

    页面映射、版本记录和名词/字段等天然结构化区域不作为页面正文判断。
    只对业务闭环模块或业务阶段内部的连续内容做机械提示，不判断业务完整性。
    """
    issues = []
    in_business = False
    table_lines = 0
    prose_lines = 0
    start_line = 0

    def flush():
        if table_lines > 0 and (prose_lines == 0 or table_lines > prose_lines * 2):
            issues.append(Issue(
                code="STYLE003",
                severity="warning",
                line=start_line,
                message="业务模块正文中表格行数远超说明段落，疑似纯表格式正文",
                suggestion="用自然语言说明业务条件、处理、结果和异常，表格只承载天然结构化信息",
            ))

    for i, line in enumerate(lines):
        stripped = line.strip()
        heading = re.match(r'^#{1,6}\s+(.*)$', stripped)
        if heading:
            title = heading.group(1).strip()
            if re.search(r'业务闭环|业务模块|业务阶段|功能需求|功能详细说明', title):
                if in_business:
                    flush()
                in_business = True
                table_lines = 0
                prose_lines = 0
                start_line = i + 1
                continue
            if in_business and re.match(r'^#{1,3}\s', stripped):
                flush()
                in_business = False
                table_lines = 0
                prose_lines = 0

        if in_business:
            if stripped.startswith('|') and '|' in stripped[1:]:
                table_lines += 1
            elif stripped and not stripped.startswith('#') and not stripped.startswith('<!--') and not stripped.startswith('```'):
                prose_lines += 1

    if in_business:
        flush()
    return issues


def check_duplicate_page_ids(lines: list) -> list:
    """STYLE004: 检查明确页面稳定标识是否重复。

    新结构不要求固定页面编号；只对文档中明确写出的编号或 page-id 做重复提示。
    """
    issues = []
    page_ids = {}
    patterns = [
        re.compile(r'^\*\*(\d+(?:\.\d+)+)\s+.+?\*\*\s*$'),
        re.compile(r'<!--\s*page[-_]?id\s*[:=]\s*([A-Za-z0-9_.-]+)'),
    ]
    for i, line in enumerate(lines):
        stripped = line.strip()
        for pattern in patterns:
            match = pattern.search(stripped)
            if not match:
                continue
            pid = match.group(1)
            if pid in page_ids:
                issues.append(Issue(
                    code="STYLE004",
                    severity="error",
                    line=i + 1,
                    message=f"页面稳定标识重复：{pid}（首次出现在第 {page_ids[pid]} 行）",
                    suggestion="确保明确写出的页面编号或 page-id 唯一；没有稳定标识时无需强行编号",
                ))
            else:
                page_ids[pid] = i + 1
            break
    return issues


def check_cross_section_refs(lines: list) -> list:
    """STYLE005: 检查跨节引用——只对“引用目标在当前 PRD 不存在”报错。

    正常指向真实章节的编号引用不再产生提示（旧版对全部引用刷 info 属于低价值噪音）；
    “Design §x.x”等上游引用不属于 PRD 内部引用，不检查。
    """
    issues = []
    cross_ref_pattern = re.compile(r'(?:见|参见|详见)\s*(\d+(?:\.\d+)*)')
    heading_numbers = set()
    for line in lines:
        match = re.match(r'^#{1,6}\s+(\d+(?:\.\d+)*)\s+', line.strip())
        if match:
            heading_numbers.add(match.group(1))

    for i, line in enumerate(lines):
        for match in cross_ref_pattern.finditer(line):
            target = match.group(1)
            if target in heading_numbers:
                continue
            issues.append(Issue(
                code="STYLE005",
                severity="error",
                line=i + 1,
                message=f"内部引用目标不存在：见 {target}",
                suggestion="修正为当前 prd.md 中真实存在的章节编号，或明确写成 Design 上游来源",
            ))

    return issues


PAGE_METADATA_LABELS = (
    "页面职责：", "使用对象：", "所属业务侧：", "所处业务阶段：",
    "入口与返回：", "区块清单：", "页面区块：", "页面展示行为：", "状态驱动展示：",
    "字段来源：",
)


def check_page_metadata_block(lines: list) -> list:
    """STYLE010: 页面正文退化为连续元数据块（页面职责/使用对象/入口与返回/区块清单等）。

    连续 3 个及以上元数据标签行即判定页面主体仍是元数据清单，违反
    “页面从用户任务和业务判断开始”的要求。
    """
    issues = []
    run = 0
    run_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_meta = any(stripped.startswith(label) for label in PAGE_METADATA_LABELS)
        if is_meta:
            if run == 0:
                run_start = i + 1
            run += 1
        else:
            if run >= 3:
                issues.append(Issue(
                    code="STYLE010",
                    severity="error",
                    line=run_start,
                    message=f"页面正文为连续元数据块（共 {run} 个元数据标签行）",
                    suggestion="从用户要完成的业务任务和判断开始写作，元数据事实融入语境、动作前提或结果",
                ))
            run = 0
    if run >= 3:
        issues.append(Issue(
            code="STYLE010",
            severity="error",
            line=run_start,
            message=f"页面正文为连续元数据块（共 {run} 个元数据标签行）",
            suggestion="从用户要完成的业务任务和判断开始写作，元数据事实融入语境、动作前提或结果",
        ))
    return issues


UI_ACTION_WORDS = ("点击", "打开", "切换", "返回", "播放")


def check_ui_word_action_titles(lines: list) -> list:
    """STYLE011: UI 动作词（点击/打开/切换/返回/播放）直接作为动作标题。"""
    issues = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        match = re.match(r'^\*\*(.+?)\*\*\s*$', stripped)
        if not match:
            continue
        title = match.group(1).strip()
        if title in UI_ACTION_WORDS:
            issues.append(Issue(
                code="STYLE011",
                severity="error",
                line=i + 1,
                message=f"动作标题直接使用 UI 动作词：{title}",
                suggestion="动作标题用“动词 + 业务对象/结果”表达，例如“定位异常车辆”“控制视频播放”",
            ))
    return issues


def check_key_value_lines(lines: list) -> list:
    """STYLE012: 连续键值对句式（字段名：说明 / 来源：xxx / 结果：xxx）承载正文。

    独立行或 `·` 列表项以“名称：内容”形式出现且连续 3 行及以上，
    判定为键值对式模板替代自然语义。单行或两行的偶发冒号句不报，
    避免把自然说明误判为模板。
    """
    issues = []
    run = 0
    run_start = 0
    kv_pattern = re.compile(r'^[^：:]{1,40}[：:]\s*\S+')

    for i, line in enumerate(lines):
        stripped = line.strip()
        is_kv = False
        if stripped.startswith('·'):
            is_kv = bool(kv_pattern.match(stripped[1:].strip()))
        elif stripped and not stripped.startswith(('|', '#', '<!--', '```', '>', '*', '-')):
            is_kv = bool(kv_pattern.match(stripped))
        if is_kv:
            if run == 0:
                run_start = i + 1
            run += 1
        else:
            if run >= 3:
                issues.append(Issue(
                    code="STYLE012",
                    severity="error",
                    line=run_start,
                    message=f"连续键值对句式承载正文（共 {run} 行）",
                    suggestion="把字段名、来源、结果等事实融入自然语言段落或列表，不写成“名称：内容”式独立行",
                ))
            run = 0

    if run >= 3:
        issues.append(Issue(
            code="STYLE012",
            severity="error",
            line=run_start,
            message=f"连续键值对句式承载正文（共 {run} 行）",
            suggestion="把字段名、来源、结果等事实融入自然语言段落或列表，不写成“名称：内容”式独立行",
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
                        severity="error" if pattern in _PLACEHOLDER_ERROR_TERMS else "warning",
                        line=i + 1,
                        message=f"占位符：发现 '{pattern}'",
                        suggestion="填写具体内容；若该表达只是规则引用，改为明确说明或由 AI 确认误报",
                    ))
            elif pattern in line:
                issues.append(Issue(
                    code="STYLE008",
                    severity="error" if pattern in _PLACEHOLDER_ERROR_TERMS else "warning",
                    line=i + 1,
                    message=f"占位符：发现 '{pattern}'",
                    suggestion="填写具体内容；若该表达只是规则引用，改为明确说明或由 AI 确认误报",
                ))
    # 原因腔词单独检查，避免误报正常描述
    issues.extend(check_cause_phrase(lines))
    return issues


def check_glossary_section(lines: list) -> list:
    """STYLE009: 检查术语定义章节存在性

    PRD 必须在总体说明下包含"术语定义"章节（兼容旧名"名词说明"/"术语说明"），
    让研发在进入详细需求前建立统一术语认知。
    """
    issues = []
    has_glossary = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^#{1,3}\s.*(名词说明|术语说明|术语定义)', stripped):
            has_glossary = True
            break

    if not has_glossary:
        issues.append(Issue(
            code="STYLE009",
            severity="error",
            line=1,
            message="缺少名词说明章节",
            suggestion="补充术语定义章节（### x.x 术语定义），按确认版 Design 列出业务术语",
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
    check_page_metadata_block,
    check_ui_word_action_titles,
    check_key_value_lines,
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
    import argparse

    parser = argparse.ArgumentParser(
        description="PRD 文风 lint 脚本：检查 PRD 正文中可机械识别的 9 类问题。",
    )
    parser.add_argument("prd_file", help="PRD 文件路径")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式（默认 text）")
    parser.add_argument("--output", type=Path, default=None, help="将 JSON 结果写入指定路径")
    args = parser.parse_args()

    prd_path = Path(args.prd_file).resolve()
    if not prd_path.exists():
        print(f"错误: 文件不存在: {prd_path}", file=sys.stderr)
        sys.exit(2)

    with open(prd_path, encoding="utf-8") as f:
        content = f.read()

    issues = run_lint(content)

    json_output = format_json(issues)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)

    if args.format == "json":
        print(json_output)
    else:
        print(format_text(issues))

    # warning/info 只提示 AI 判断，不阻断命令；确定性 error 才返回 1。
    if any(i.severity == "error" for i in issues):
        sys.exit(1)


if __name__ == "__main__":
    main()
