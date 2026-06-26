#!/usr/bin/env python3
"""prd-consistency-check.py — PRD 与 design 确定性结构对比

从 PRD 正文确定性提取字段/页面/状态/权限实体集合，
与 design metadata 做集合对比，输出 JSON 报告。

只做确定性提取和集合对比，不做语义判断。
语义判断（规则覆盖、字段类型/必填一致性）由 review skill 的 LLM 完成。

用法：
  cat output/prd/prd.md | python prd-consistency-check.py --project-root .
  python prd-consistency-check.py --project-root . < output/prd/prd.md
"""

import argparse
import json
import re
import sys
from pathlib import Path

from shared_md import (
    parse_headings,
    parse_tables_with_context,
    fuzzy_field_match,
    fuzzy_page_match,
    clean_page_title,
    load_json,
)

# PRD 章节别名
SECTION_ALIASES = {
    "数据字典": ["数据字典", "字段定义", "字段清单"],
    "权限汇总": ["权限汇总", "权限定义", "权限矩阵"],
    "状态机": ["状态机", "状态定义", "状态流转"],
    "详细需求说明": ["详细需求说明", "详细需求", "需求说明"],
}


# ── 章节定位 ──────────────────────────────────────────────────

def _find_section_range(headings: list, canonical: str) -> tuple:
    """定位章节范围，返回 (start_line, end_line, section_level)

    支持别名匹配。多个匹配时取 level 最低（最高级标题）的那个。
    未找到返回 (None, None, None)。
    """
    aliases = SECTION_ALIASES.get(canonical, [canonical])
    best = None  # (line, level)

    for h in headings:
        for alias in aliases:
            if alias in h["title"]:
                if best is None or h["level"] < best[1]:
                    best = (h["line"], h["level"])
                break

    if best is None:
        return None, None, None

    start_line, section_level = best
    end_line = None
    for h in headings:
        if h["line"] > start_line and h["level"] <= section_level:
            end_line = h["line"]
            break

    return start_line, end_line, section_level


def _tables_in_range(tables: list, start: int, end: int) -> list:
    """返回指定行范围内的表格"""
    return [t for t in tables if start <= t["line_offset"] < (end or float("inf"))]


# ── PRD 实体提取 ──────────────────────────────────────────────

def extract_prd_fields(content: str, headings: list, tables: list) -> list:
    """从数据字典表格提取字段名（第一列）"""
    start, end, _ = _find_section_range(headings, "数据字典")
    if start is None:
        return []

    fields = []
    for table in _tables_in_range(tables, start, end):
        if not table["rows"]:
            continue
        for row in table["rows"]:
            if row and row[0] and row[0] not in ("---", "字段"):
                fields.append(row[0].strip())
    return fields


def extract_prd_pages(headings: list) -> list:
    """从详细需求说明提取页面名

    识别规则：
    - ### 标题不含模块标记（（一）等）→ 页面
    - #### 标题不含非页面标记 → 页面

    过滤：跳过中文序号标题（一、二、等）和章节容器标题。
    """
    start, end, _ = _find_section_range(headings, "详细需求说明")
    if start is None:
        return []

    # 章节容器标题黑名单
    blacklist = {
        "业务流程", "核心业务流程", "状态变化", "状态流转",
        "权限汇总", "权限定义", "数据字典", "字段定义",
        "状态机", "状态定义", "验收标准", "风险与待确认",
    }

    pages = []
    for h in headings:
        if h["line"] <= start:
            continue
        if end and h["line"] >= end:
            break
        if h["level"] == 3:
            title = h["title"].strip()
            # 跳过中文序号标题（一、二、等）
            if re.match(r'^[一二三四五六七八九十]+[、．.]', title):
                continue
            # 跳过模块标记（（一）等）
            if re.match(r'^[（(][一二三四五六七八九十\d]+[）)]', title):
                continue
            # 跳过章节容器标题
            if title in blacklist:
                continue
            pages.append(clean_page_title(title))
        elif h["level"] == 4:
            title = h["title"].strip()
            if "非页面落点" in title:
                continue
            pages.append(clean_page_title(title))
    return pages


def extract_prd_states(content: str, headings: list, tables: list) -> list:
    """从状态机提取状态名

    覆盖两种格式：
    1. 箭头文本: state1 → state2 → state3
    2. 表格: | 状态 | 含义 | ... |
    """
    start, end, _ = _find_section_range(headings, "状态机")
    if start is None:
        return []

    states = []

    # 格式 1: 箭头文本（→ 或 ->）
    lines = content.split("\n")
    for i, line in enumerate(lines):
        line_no = i + 1
        if line_no < start:
            continue
        if end and line_no >= end:
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "→" in stripped or "->" in stripped:
            arrow = "→" if "→" in stripped else "->"
            parts = [p.strip().strip("`") for p in stripped.split(arrow)]
            for p in parts:
                # 去掉前缀（如 "周报状态："）
                p = re.sub(r'^[^：:]*[：:]', '', p).strip()
                if p and p not in ("—", "-", "N/A"):
                    states.append(p)

    # 格式 2: 表格（"当前状态"/"状态"+"目标状态"/"下一状态"列）
    for table in _tables_in_range(tables, start, end):
        headers = table["headers"]
        # 找所有含"状态"的列（当前状态、目标状态、下一状态等）
        state_cols = [i for i, h in enumerate(headers) if "状态" in h]
        if not state_cols:
            continue
        for row in table["rows"]:
            for col_idx in state_cols:
                if col_idx < len(row) and row[col_idx]:
                    cell = row[col_idx].strip().strip("`")
                    if cell and cell not in ("—", "-", "状态", "任意状态"):
                        states.append(cell)

    # 去重保序
    seen = set()
    unique = []
    for s in states:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


def extract_prd_permission_pages(content: str, headings: list, tables: list) -> list:
    """从权限汇总提取页面名

    支持两种表格格式：
    - 格式 A（页面为行）：第一列=页面名，表头=角色名
    - 格式 B（角色为行）：第一列=角色名，表头=页面名
    """
    start, end, _ = _find_section_range(headings, "权限汇总")
    if start is None:
        return []

    pages = []
    for table in _tables_in_range(tables, start, end):
        if len(table["headers"]) < 2:
            continue
        first_header = table["headers"][0].strip()
        # 格式 B：第一列表头是"角色"→ 页面名在表头（第二列起）
        if "角色" in first_header:
            for h in table["headers"][1:]:
                page = clean_page_title(h.strip())
                if page:
                    pages.append(page)
        else:
            # 格式 A：第一列=页面名
            for row in table["rows"]:
                if not row or not row[0] or row[0] in ("---", "页面"):
                    continue
                page = clean_page_title(row[0].strip())
                if page:
                    pages.append(page)
    return pages


# ── 集合对比 ──────────────────────────────────────────────────

def _try_match(name: str, name_to_id: dict, fuzzy_fn) -> str | None:
    """尝试精确匹配 → 模糊匹配，返回匹配到的 design 名称；未匹配返回 None"""
    if name in name_to_id:
        return name
    if fuzzy_fn:
        matched_id = fuzzy_fn(name, name_to_id)
        if matched_id:
            for t, eid in name_to_id.items():
                if eid == matched_id:
                    return t
    return None


def compare_entities(
    design_items: list,
    prd_items: list,
    design_title_to_id: dict,
    fuzzy_fn=None,
) -> dict:
    """对比 design 与 PRD 实体集合

    返回 {missing, hallucinated, matched_count}
    - missing: design 有但 PRD 没有
    - hallucinated: PRD 有但 design 没有
    """
    design_set = set(design_items)
    prd_set = set(prd_items)

    matched_design = set()
    matched_prd = set()

    for prd_item in prd_set:
        matched = _try_match(prd_item, design_title_to_id, fuzzy_fn)
        if matched:
            matched_design.add(matched)
            matched_prd.add(prd_item)

    missing = sorted(design_set - matched_design)
    hallucinated = sorted(prd_set - matched_prd)

    return {
        "missing": missing,
        "hallucinated": hallucinated,
        "matched_count": len(matched_design),
    }


def compare_permission_pages(
    design_perms: list,
    prd_perm_pages: list,
) -> dict:
    """对比权限页面覆盖（不检查角色级，角色名映射交给 LLM）

    直接用 permissions.json 的 page 集合对比，不通过 pages.json 中转
    ——因为权限矩阵中的页面名可能是模块级名称，和 pages.json 的具体页面名不同。
    """
    design_pages_with_perms = set()
    for p in design_perms:
        if isinstance(p, dict) and p.get("page"):
            design_pages_with_perms.add(p["page"])

    prd_set = set(prd_perm_pages)

    # 精确匹配 + 已知变体匹配
    matched_design = set()
    matched_prd = set()

    for prd_page in prd_set:
        if prd_page in design_pages_with_perms:
            matched_design.add(prd_page)
            matched_prd.add(prd_page)
        else:
            # 尝试 fuzzy_page_match 处理已知变体
            for dp in design_pages_with_perms:
                if fuzzy_page_match(prd_page, {dp: dp}):
                    matched_design.add(dp)
                    matched_prd.add(prd_page)
                    break

    missing = sorted(design_pages_with_perms - matched_design)
    hallucinated = sorted(prd_set - matched_prd)

    return {
        "missing": missing,
        "hallucinated": hallucinated,
        "matched_count": len(matched_design),
    }


# ── 主入口 ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PRD 与 design 确定性结构对比")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="项目根目录")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    content = sys.stdin.read()

    meta_dir = project_root / ".workflow" / "metadata" / "design"

    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)

    # 加载 design metadata
    design_fields = load_json(meta_dir / "fields.json") or []
    design_pages = load_json(meta_dir / "pages.json") or []
    design_states = load_json(meta_dir / "states.json") or []
    design_permissions = load_json(meta_dir / "permissions.json") or []

    # 构建 title → id 映射
    field_title_to_id = {f["title"]: f["id"] for f in design_fields if isinstance(f, dict) and "title" in f}
    page_title_to_id = {p["title"]: p["id"] for p in design_pages if isinstance(p, dict) and "title" in p}
    state_title_to_id = {s["title"]: s.get("id", s["title"]) for s in design_states if isinstance(s, dict) and "title" in s}

    # 从 PRD 提取实体
    prd_fields = extract_prd_fields(content, headings, tables)
    prd_pages = extract_prd_pages(headings)
    prd_states = extract_prd_states(content, headings, tables)
    prd_perm_pages = extract_prd_permission_pages(content, headings, tables)

    # 集合对比
    field_result = compare_entities(
        [f["title"] for f in design_fields if isinstance(f, dict)],
        prd_fields, field_title_to_id, fuzzy_field_match,
    )
    page_result = compare_entities(
        [p["title"] for p in design_pages if isinstance(p, dict)],
        prd_pages, page_title_to_id, fuzzy_page_match,
    )
    state_result = compare_entities(
        [s["title"] for s in design_states if isinstance(s, dict)],
        prd_states, state_title_to_id, None,
    )
    perm_result = compare_permission_pages(design_permissions, prd_perm_pages)

    total_missing = (
        len(field_result["missing"])
        + len(page_result["missing"])
        + len(state_result["missing"])
        + len(perm_result["missing"])
    )
    total_hallucinated = (
        len(field_result["hallucinated"])
        + len(page_result["hallucinated"])
        + len(state_result["hallucinated"])
        + len(perm_result["hallucinated"])
    )

    result = {
        "fields": field_result,
        "pages": page_result,
        "states": state_result,
        "permissions": perm_result,
        "summary": {
            "total_missing": total_missing,
            "total_hallucinated": total_hallucinated,
            "has_hallucination": total_hallucinated > 0,
        },
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if total_hallucinated > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
