"""shared_md.py — Markdown 解析共用的最小函数集

设计原则：只放被多个脚本重复实现的函数，不放只被单个脚本使用的逻辑。
"""

import re


def parse_headings(content: str) -> list:
    """解析 Markdown 标题结构 → [{level, title, line}, ...]"""
    headings = []
    for i, line in enumerate(content.split('\n')):
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            headings.append({
                "level": len(match.group(1)),
                "title": match.group(2).strip(),
                "line": i + 1,
            })
    return headings


def parse_tables_with_context(content: str, headings: list) -> list:
    """解析 Markdown 表格并关联到所在章节

    返回 [{section_title, section_line, headers, rows, line_offset}, ...]
    """
    lines = content.split('\n')
    tables = []
    current_section = ""
    current_section_line = 1

    heading_map = {h["line"]: h["title"] for h in headings}

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if i + 1 in heading_map:
            current_section = heading_map[i + 1]
            current_section_line = i + 1
        if line.startswith("|") and "|" in line[1:] and i + 1 < len(lines):
            sep_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if re.match(r'^\|[\s\-:|]+\|$', sep_line):
                headers = [h.strip() for h in line.split("|")[1:-1]]
                rows = []
                j = i + 2
                while j < len(lines):
                    if lines[j].strip() == "":
                        j += 1
                        continue
                    if not lines[j].strip().startswith("|"):
                        break
                    rows.append([c.strip() for c in lines[j].strip().split("|")[1:-1]])
                    j += 1
                tables.append({
                    "section_title": current_section,
                    "section_line": current_section_line,
                    "headers": headers,
                    "rows": rows,
                    "line_offset": i + 1,
                })
                i = j
                continue
        i += 1
    return tables
