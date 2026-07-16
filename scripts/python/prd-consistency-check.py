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
# 字段/状态/权限按小模块归位到 §5 详细需求说明
SECTION_ALIASES = {
    "详细需求说明": ["详细需求说明", "详细需求", "需求说明", "详细需求规格", "需求详细说明"],
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

def extract_prd_fields(headings: list, tables: list) -> list:
    """从 §5 详细需求说明提取字段（含属性）

    归位后字段表分布在小模块末尾。
    识别规则：在详细需求说明章节范围内，表头含"字段"和"类型"的表视为字段定义表。
    PRD 字段表格式：| 字段 | 类型 | 必填 | 说明 |（4 列）

    返回 [{"name": str, "type": str, "required": bool}, ...]
    """
    start, end, _ = _find_section_range(headings, "详细需求说明")
    if start is None:
        return []

    fields = []
    for table in _tables_in_range(tables, start, end):
        headers = table.get("headers", [])
        if not headers:
            continue
        # 字段定义表的特征：表头含"字段"和"类型"
        header_text = "|".join(headers)
        if "字段" not in header_text or "类型" not in header_text:
            continue
        # 定位列索引
        name_idx = next((i for i, h in enumerate(headers) if "字段" in h), 0)
        type_idx = next((i for i, h in enumerate(headers) if "类型" in h), 1)
        required_idx = next((i for i, h in enumerate(headers) if "必填" in h), None)
        for row in table["rows"]:
            if not row or not row[0] or row[0] in ("---", "字段"):
                continue
            name = row[name_idx].strip() if name_idx < len(row) else ""
            if not name:
                continue
            field_type = row[type_idx].strip() if type_idx < len(row) else ""
            required = None
            if required_idx is not None and required_idx < len(row):
                required_cell = row[required_idx].strip()
                required = required_cell == "是" if required_cell in ("是", "否") else None
            fields.append({"name": name, "type": field_type, "required": required})
    return fields


def extract_prd_pages(content: str, headings: list) -> list:
    """从详细需求说明提取页面名

    识别规则（新编号体系）：
    - 页面用粗体块 `**N.N.N.N 页面名**` 表示，不再是 Markdown 标题
    - 大模块是 `### N.N 模块名`，子模块是 `#### N.N.N 子模块名`
    - 跳过大模块（###）和子模块（####）标题，只提取粗体块页面名
    """
    start, end, _ = _find_section_range(headings, "详细需求说明")
    if start is None:
        return []

    # 章节容器标题黑名单（粗体块页面名等于以下词条时跳过，避免章节标题被误识别为页面）
    # 包含归位前旧章节名（权限汇总/数据字典/状态机等），保留用于兼容历史 PRD
    blacklist = {
        "业务流程", "核心业务流程", "状态变化", "状态流转",
        "权限汇总", "权限定义", "数据字典", "字段定义",
        "状态机", "状态定义", "验收标准", "风险与待确认",
    }

    # 粗体块页面名模式：**N.N.N 页面名** 或 **N.N.N.N 页面名**
    # N.N.N 是单子模块大模块的页面，N.N.N.N 是多子模块大模块的页面
    page_bold_pattern = re.compile(r'^\*\*(\d+(?:\.\d+)+)\s+(.+?)\*\*\s*$')

    pages = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line_no = i + 1
        if line_no <= start:
            continue
        if end and line_no >= end:
            break

        m = page_bold_pattern.match(line.strip())
        if m:
            page_name = m.group(2).strip()
            if page_name in blacklist:
                continue
            pages.append(clean_page_title(page_name))

    return pages


def extract_prd_states(content: str, headings: list, tables: list) -> list:
    """从 §5 详细需求说明提取状态名

    归位后状态机表分布在小模块末尾。
    识别规则：在详细需求说明章节范围内，表头同时含"状态"和"触发动作"的表视为状态机表。
    同时兼容箭头文本格式（state1 → state2）。
    """
    start, end, _ = _find_section_range(headings, "详细需求说明")
    if start is None:
        return []

    states = []

    # 格式 1: 箭头文本（→ 或 ->）——在详细需求说明范围内扫描
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

    # 格式 2: 状态机表格——表头同时含"状态"和"触发动作"
    for table in _tables_in_range(tables, start, end):
        headers = table.get("headers", [])
        if not headers:
            continue
        header_text = "|".join(headers)
        if "状态" not in header_text or "触发动作" not in header_text:
            continue
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


def extract_prd_permission_pages(headings: list, tables: list) -> list:
    """从 §5 详细需求说明提取大模块名作为权限页面覆盖检查的来源

    权限规则归位到大模块开头。
    识别规则：在详细需求说明章节范围内，提取所有 `### N.N xxx` 大模块标题。
    design permissions.json 的 page 字段是模块名（如"审计计划""项目启动"），
    与 PRD 的大模块标题对应。
    """
    start, end, _ = _find_section_range(headings, "详细需求说明")
    if start is None:
        return []

    pages = []
    for h in headings:
        if h["line"] < start:
            continue
        if end and h["line"] >= end:
            continue
        # 大模块标题：### N.N xxx（level 3）
        if h["level"] != 3:
            continue
        title = h["title"]
        # 去掉编号前缀
        cleaned = re.sub(r'^\d+\.\d+\s*', '', title).strip()
        # 去掉尾部的"模块"二字
        if cleaned.endswith("模块"):
            cleaned = cleaned[:-2].strip()
        if cleaned:
            pages.append(cleaned)
    return pages


# ── 字段属性对比 ──────────────────────────────────────────────

def _normalize_type(type_str: str) -> str:
    """归一化类型字符串以便比较：去空格、转小写"""
    if not type_str:
        return ""
    return re.sub(r"\s+", "", type_str).lower()


def compare_field_attributes(
    design_fields: list,
    prd_fields: list,
    design_title_to_id: dict,
    fuzzy_fn=None,
) -> list:
    """对比 matched 字段的类型和必填属性

    返回 attribute_mismatch 列表：
    [{"name": str, "design_type": str, "prd_type": str,
      "design_required": bool, "prd_required": bool}, ...]
    """
    # 构建 design title → attributes 映射
    design_attrs = {}
    for f in design_fields:
        if not isinstance(f, dict) or "title" not in f:
            continue
        attrs = f.get("attributes", {})
        design_attrs[f["title"]] = {
            "type": attrs.get("数据类型", ""),
            "required": attrs.get("必填"),
        }

    mismatches = []
    matched_pairs = set()  # 避免重复匹配

    for prd_field in prd_fields:
        if not isinstance(prd_field, dict) or "name" not in prd_field:
            continue
        prd_name = prd_field["name"]
        # 尝试匹配 design 字段名
        matched_design = _try_match(prd_name, design_title_to_id, fuzzy_fn)
        if not matched_design or matched_design not in design_attrs:
            continue
        pair_key = (prd_name, matched_design)
        if pair_key in matched_pairs:
            continue
        matched_pairs.add(pair_key)

        d_attrs = design_attrs[matched_design]
        d_type = _normalize_type(d_attrs["type"])
        p_type = _normalize_type(prd_field.get("type", ""))
        d_required = d_attrs["required"]
        p_required = prd_field.get("required")

        type_mismatch = d_type != p_type and d_type and p_type
        required_mismatch = (
            d_required is not None and p_required is not None
            and d_required != p_required
        )

        if type_mismatch or required_mismatch:
            mismatches.append({
                "name": prd_name,
                "design_type": d_attrs["type"],
                "prd_type": prd_field.get("type", ""),
                "design_required": d_required,
                "prd_required": p_required,
            })

    return mismatches


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
    field_title_to_id = {f["title"]: f.get("id", f["title"]) for f in design_fields if isinstance(f, dict) and "title" in f}
    page_title_to_id = {p["title"]: p.get("id", p["title"]) for p in design_pages if isinstance(p, dict) and "title" in p}
    state_title_to_id = {s["title"]: s.get("id", s["title"]) for s in design_states if isinstance(s, dict) and "title" in s}

    # 从 PRD 提取实体
    prd_fields = extract_prd_fields(headings, tables)
    prd_pages = extract_prd_pages(content, headings)
    prd_states = extract_prd_states(content, headings, tables)
    prd_perm_pages = extract_prd_permission_pages(headings, tables)

    # 集合对比（字段用名称列表做集合对比）
    prd_field_names = [f["name"] for f in prd_fields if isinstance(f, dict) and "name" in f]
    field_result = compare_entities(
        [f["title"] for f in design_fields if isinstance(f, dict)],
        prd_field_names, field_title_to_id, fuzzy_field_match,
    )
    # 字段属性对比（类型 + 必填）
    field_result["attribute_mismatch"] = compare_field_attributes(
        design_fields, prd_fields, field_title_to_id, fuzzy_field_match,
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
    total_attribute_mismatch = len(field_result["attribute_mismatch"])

    result = {
        "fields": field_result,
        "pages": page_result,
        "states": state_result,
        "permissions": perm_result,
        "summary": {
            "total_missing": total_missing,
            "total_hallucinated": total_hallucinated,
            "total_attribute_mismatch": total_attribute_mismatch,
            "has_hallucination": total_hallucinated > 0,
        },
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if total_hallucinated > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
