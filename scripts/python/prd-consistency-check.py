#!/usr/bin/env python3
"""prd-consistency-check.py — PRD 与 design 确定性结构对比（vNext: 直接读人读稿，多模板兼容）

vNext 变更：
- 不再依赖 .workflow/metadata/design/ 下的 metadata 文件。
- 直接读取 output/design/design.md 和 output/prd/prd.md，从人读稿中提取实体做集合对比。
- 复用 stage-prep.py 的 generate_design_metadata 函数从 design.md 提取实体（不写入 metadata 文件）。
- 多模板兼容：支持新归位模板（字段/状态/权限归位到 §5 详细需求说明）和旧模板（数据字典/状态机/权限汇总独立章节 + `### page-N 页面名`）。
- 只做确定性提取和集合对比，不做语义判断。
- 语义判断（规则覆盖、字段类型/必填一致性）由 review skill 的 LLM 完成。

退出码：
- 0: 通过（无 missing、无 hallucinated、无 attribute_mismatch）
- 1: 发现 hallucinated / missing / attribute_mismatch（调用方必须修正后重新检查）
- 2: 致命错误（design.md 或 prd.md 不存在等）

用法：
  python prd-consistency-check.py --project-root .
"""

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

from shared_md import (
    parse_headings,
    parse_tables_with_context,
    fuzzy_field_match,
    fuzzy_page_match,
    fuzzy_state_match,
    clean_page_title,
    load_json,
    strip_heading_number,
)

# PRD 章节别名（用于章节定位，但 vNext 主要采用全文扫描策略，章节定位仅作辅助）
SECTION_ALIASES = {
    "详细需求说明": ["详细需求说明", "详细需求", "需求说明", "详细需求规格", "需求详细说明"],
    "数据字典": ["数据字典", "字段定义", "字段清单", "字段列表", "数据项定义"],
    "页面说明": ["页面说明", "页面清单", "页面列表", "页面规划", "页面目录"],
    "状态机": ["状态机", "状态定义", "状态流转", "规则与状态定义"],
    "权限汇总": ["权限汇总", "权限定义", "权限规则", "权限矩阵", "权限"],
}


# ── 章节定位（辅助） ────────────────────────────────────────────

def _find_section_range(headings: list, canonical: str) -> tuple:
    """定位章节范围，返回 (start_line, end_line, section_level)

    支持别名匹配。多个匹配时取 level 最低（最高级标题）的那个。
    未找到返回 (None, None, None)。
    """
    aliases = SECTION_ALIASES.get(canonical, [canonical])
    best = None  # (line, level)

    for h in headings:
        for alias in aliases:
            # 用 shared_md.strip_heading_number 去除阿拉伯和中文数字前缀
            title_no_prefix = strip_heading_number(h["title"])
            if title_no_prefix.startswith(alias):
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


def _find_multiple_section_ranges(headings: list, canonical_list: list) -> list:
    """定位多个候选章节范围，返回 [(start, end, level), ...]"""
    ranges = []
    for canonical in canonical_list:
        start, end, level = _find_section_range(headings, canonical)
        if start is not None:
            ranges.append((start, end, level))
    return ranges


def _tables_in_ranges(tables: list, ranges: list) -> list:
    """返回指定行范围集合内的表格"""
    result = []
    for t in tables:
        line = t["line_offset"]
        for start, end, _ in ranges:
            if start <= line < (end or float("inf")):
                result.append(t)
                break
    return result


def _lines_in_ranges(content: str, ranges: list) -> str:
    """返回指定行范围集合内的文本"""
    lines = content.split("\n")
    result = []
    for start, end, _ in ranges:
        end_idx = end if end else len(lines)
        result.extend(lines[start - 1:end_idx - 1])
    return "\n".join(result)


# ── PRD 实体提取（多模板兼容） ─────────────────────────────────

def extract_prd_fields(headings: list, tables: list, content: str) -> list:
    """从 PRD 提取字段（含属性）

    vNext 多模板兼容策略：
    - 候选章节：详细需求说明、数据字典、字段定义、字段清单
    - 在候选章节范围内的表头含"字段"和"类型"的表视为字段定义表
    - 如候选章节都未找到，降级为全文扫描所有表头含"字段"和"类型"的表

    PRD 字段表格式：| 字段 | 类型 | 必填 | 说明 |（4 列，轻量格式）

    返回 [{"name": str, "type": str, "required": bool}, ...]
    """
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["详细需求说明", "数据字典", "字段定义", "字段清单"]
    )

    fields = []

    def _extract_from_tables(table_list):
        for table in table_list:
            headers = table.get("headers", [])
            if not headers:
                continue
            header_text = "|".join(headers)
            if "字段" not in header_text or "类型" not in header_text:
                continue
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

    # 策略 1: 在候选章节范围内提取
    if candidate_ranges:
        _extract_from_tables(_tables_in_ranges(tables, candidate_ranges))

    # 策略 2: 候选章节未找到，降级为全文扫描
    if not fields:
        _extract_from_tables(tables)

    return fields


def extract_prd_pages(content: str, headings: list) -> list:
    """从 PRD 提取页面名

    vNext 多模板兼容策略，识别以下格式：
    1. 新编号体系粗体块：`**N.N.N 页面名**` 或 `**N.N.N.N 页面名**`
    2. 旧模板格式：`### page-N 页面名`（如 `### page-1 我的周报列表`）
    3. 中编号格式：`### N.N 页面名`（如 `### 3.1 我的周报列表`）
    4. 在"页面说明"章节内的 `### 页面名` 标题（无编号）

    跳过大模块（##）和容器章节标题。
    """
    blacklist = {
        "业务流程", "核心业务流程", "状态变化", "状态流转",
        "权限汇总", "权限定义", "数据字典", "字段定义",
        "状态机", "状态定义", "验收标准", "风险与待确认",
        "页面说明", "页面清单", "页面列表", "页面规划", "页面目录",
        "详细需求说明", "详细需求", "需求说明",
    }

    pages = []
    seen = set()

    # 候选章节范围：页面说明 / 详细需求说明
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["页面说明", "页面清单", "页面列表", "详细需求说明"]
    )

    # 格式 1: 粗体块页面名 **N.N.N 页面名**
    page_bold_pattern = re.compile(r'^\*\*(\d+(?:\.\d+)+)\s+(.+?)\*\*\s*$')
    # 格式 2: ### page-N 页面名
    page_legacy_pattern = re.compile(r'^#+\s+page[-_]?(\d+)\s+(.+?)\s*$', re.IGNORECASE)
    # 格式 3: ### N.N 页面名
    page_numbered_pattern = re.compile(r'^#+\s+(\d+\.\d+(?:\.\d+)*)\s+(.+?)\s*$')

    def _add_page(name):
        name = clean_page_title(name).strip()
        if not name or name in blacklist:
            return
        if name not in seen:
            seen.add(name)
            pages.append(name)

    lines = content.split('\n')
    in_candidate = False
    current_range_idx = 0
    candidate_ranges_sorted = sorted(candidate_ranges, key=lambda r: r[0])

    for i, line in enumerate(lines):
        line_no = i + 1

        # 检查是否进入或离开候选章节
        while current_range_idx < len(candidate_ranges_sorted):
            start, end, _ = candidate_ranges_sorted[current_range_idx]
            if line_no < start:
                break
            elif line_no >= start and (end is None or line_no < end):
                in_candidate = True
                break
            elif end is not None and line_no >= end:
                current_range_idx += 1
                in_candidate = False
                continue
            else:
                break

        stripped = line.strip()

        # 格式 1: 粗体块页面名（新编号体系）
        m = page_bold_pattern.match(stripped)
        if m:
            _add_page(m.group(2))
            continue

        # 格式 2: ### page-N 页面名（旧模板）
        m = page_legacy_pattern.match(stripped)
        if m:
            _add_page(m.group(2))
            continue

        # 格式 3: ### N.N 页面名（中编号）
        # 仅在候选章节内识别，避免误匹配其他编号标题
        if in_candidate:
            m = page_numbered_pattern.match(stripped)
            if m:
                _add_page(m.group(2))
                continue

            # 格式 4: ### 页面名（在"页面说明"章节内的无编号标题，level >= 3）
            heading_match = re.match(r'^(#{3,})\s+(.+?)\s*$', stripped)
            if heading_match:
                title = heading_match.group(2)
                _add_page(title)

    return pages


def extract_prd_states(content: str, headings: list, tables: list) -> list:
    """从 PRD 提取状态名

    vNext 多模板兼容策略：
    - 候选章节：详细需求说明、状态机、状态定义、状态流转
    - 在候选章节范围内查找箭头文本和状态机表格
    - 如候选章节都未找到，降级为全文扫描

    支持格式：
    1. 箭头文本：state1 → state2 或 state1 -> state2
    2. 状态机表格：表头同时含"状态"和"触发动作"
    """
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["详细需求说明", "状态机", "状态定义", "状态流转"]
    )

    states = []
    seen = set()

    def _add_state(name):
        name = name.strip().strip("`")
        if not name or name in ("—", "-", "N/A", "任意状态", "状态"):
            return
        if name not in seen:
            seen.add(name)
            states.append(name)

    # 策略 1: 在候选章节范围内查找
    if candidate_ranges:
        ranges_content = _lines_in_ranges(content, candidate_ranges)
        ranges_lines = ranges_content.split("\n")

        # 格式 1: 箭头文本
        for line in ranges_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "→" in stripped or "->" in stripped:
                if any(ui_word in stripped for ui_word in ("点击", "跳转", "打开", "弹出", "返回", "进入页面")):
                    continue
                arrow = "→" if "→" in stripped else "->"
                parts = [p.strip().strip("`") for p in stripped.split(arrow)]
                for p in parts:
                    p = re.sub(r'^[^：:]*[：:]', '', p).strip()
                    _add_state(p)

        # 格式 2: 状态机表格
        for table in _tables_in_ranges(tables, candidate_ranges):
            headers = table.get("headers", [])
            if not headers:
                continue
            header_text = "|".join(headers)
            if "状态" not in header_text or "触发动作" not in header_text:
                continue
            state_cols = [i for i, h in enumerate(headers) if "状态" in h]
            for row in table["rows"]:
                for col_idx in state_cols:
                    if col_idx < len(row) and row[col_idx]:
                        _add_state(row[col_idx])

    # 策略 2: 候选章节未找到，降级为全文扫描
    if not states:
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "→" in stripped or "->" in stripped:
                if any(ui_word in stripped for ui_word in ("点击", "跳转", "打开", "弹出", "返回", "进入页面")):
                    continue
                arrow = "→" if "→" in stripped else "->"
                parts = [p.strip().strip("`") for p in stripped.split(arrow)]
                for p in parts:
                    p = re.sub(r'^[^：:]*[：:]', '', p).strip()
                    _add_state(p)

        for table in tables:
            headers = table.get("headers", [])
            if not headers:
                continue
            header_text = "|".join(headers)
            if "状态" not in header_text or "触发动作" not in header_text:
                continue
            state_cols = [i for i, h in enumerate(headers) if "状态" in h]
            for row in table["rows"]:
                for col_idx in state_cols:
                    if col_idx < len(row) and row[col_idx]:
                        _add_state(row[col_idx])

    return states


def extract_prd_permission_pages(headings: list, tables: list, content: str) -> list:
    """从 PRD 提取权限页面名

    vNext 多模板兼容策略：
    - 候选章节：详细需求说明、权限汇总、权限定义、权限规则
    - 策略 1：在候选章节范围内提取 `### N.N xxx` 大模块标题
    - 策略 2：在权限汇总章节内的表格第一列提取页面名（旧模板格式）
    - 策略 3：候选章节未找到，降级为全文扫描权限表

    design permissions.json 的 page 字段是模块名（如"审计计划""项目启动"），
    与 PRD 的大模块标题或权限表第一列对应。
    """
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["详细需求说明", "权限汇总", "权限定义", "权限规则"]
    )

    pages = []
    seen = set()

    def _add_page(name):
        name = name.strip()
        # 去掉编号前缀
        name = re.sub(r'^\d+\.\d+(?:\.\d+)*\s*', '', name)
        # 去掉尾部的"模块"二字
        if name.endswith("模块"):
            name = name[:-2].strip()
        # 去掉尾部的"页"字
        if name.endswith("页"):
            name = name[:-1].strip()
        if not name:
            return
        if name not in seen:
            seen.add(name)
            pages.append(name)

    # 策略 1: 在候选章节范围内提取 ### N.N xxx 大模块标题
    for h in headings:
        for start, end, _ in candidate_ranges:
            if h["line"] < start:
                continue
            if end is not None and h["line"] >= end:
                continue
            if h["level"] != 3:
                continue
            _add_page(h["title"])
            break

    # 策略 2: 在权限汇总章节内的表格第一列提取页面名（旧模板）
    perm_ranges = _find_multiple_section_ranges(headings, ["权限汇总", "权限定义", "权限规则"])
    if perm_ranges:
        for table in _tables_in_ranges(tables, perm_ranges):
            headers = table.get("headers", [])
            if not headers:
                continue
            header_text = "|".join(headers)
            # 权限表的特征：表头含"页面"或"对象"或"模块"
            if not any(k in header_text for k in ("页面", "对象", "模块")):
                continue
            # 第一列是页面名
            for row in table["rows"]:
                if not row or not row[0] or row[0] in ("---",):
                    continue
                _add_page(row[0])

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
    matched_pairs = set()

    for prd_field in prd_fields:
        if not isinstance(prd_field, dict) or "name" not in prd_field:
            continue
        prd_name = prd_field["name"]
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

    matched_design = set()
    matched_prd = set()

    for prd_page in prd_set:
        if prd_page in design_pages_with_perms:
            matched_design.add(prd_page)
            matched_prd.add(prd_page)
        else:
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

def _load_design_entities_from_md(project_root: Path):
    """vNext: 从 output/design/design.md 直接提取实体（不依赖 metadata）

    复用 stage-prep.py 的 generate_design_metadata 函数。
    返回 (design_data, error_message)；成功时 error_message 为 None。
    """
    design_path = project_root / "output" / "design" / "design.md"
    if not design_path.exists():
        return None, f"design.md not found: {design_path}"
    try:
        with open(design_path, encoding="utf-8") as f:
            content = f.read()
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("stage_prep", os.path.join(scripts_dir, "stage-prep.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        data = mod.generate_design_metadata(content, "design", project_root)
        return data, None
    except Exception as e:
        return None, f"从 design.md 解析实体失败: {e}"


def main():
    parser = argparse.ArgumentParser(description="PRD 与 design 确定性结构对比（vNext: 直接读人读稿，多模板兼容）")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="项目根目录")
    args = parser.parse_args()

    project_root = args.project_root.resolve()

    # vNext: 直接读 prd.md（兼容 stdin 模式以保留旧调用方式）
    if not sys.stdin.isatty():
        content = sys.stdin.read()
        if not content.strip():
            prd_path = project_root / "output" / "prd" / "prd.md"
            print(json.dumps({"error": f"stdin 为空且未提供 PRD 内容；尝试读取 {prd_path} 失败"}, ensure_ascii=False))
            sys.exit(2)
    else:
        prd_path = project_root / "output" / "prd" / "prd.md"
        if not prd_path.exists():
            print(json.dumps({"error": f"prd.md not found: {prd_path}"}, ensure_ascii=False))
            sys.exit(2)
        with open(prd_path, encoding="utf-8") as f:
            content = f.read()

    # vNext: 从 design.md 直接提取实体（不依赖 metadata）
    design_data, err = _load_design_entities_from_md(project_root)
    if design_data is None:
        print(json.dumps({"error": err or "无法加载 design 实体"}, ensure_ascii=False))
        sys.exit(2)

    design_fields = design_data.get("fields", []) or []
    design_pages = design_data.get("pages", []) or []
    design_states = design_data.get("states", []) or []
    design_permissions = design_data.get("permissions", []) or []

    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)

    # 构建 title → id 映射
    field_title_to_id = {f["title"]: f.get("id", f["title"]) for f in design_fields if isinstance(f, dict) and "title" in f}
    page_title_to_id = {p["title"]: p.get("id", p["title"]) for p in design_pages if isinstance(p, dict) and "title" in p}
    state_title_to_id = {s["title"]: s.get("id", s["title"]) for s in design_states if isinstance(s, dict) and "title" in s}

    # 从 PRD 提取实体（多模板兼容）
    prd_fields = extract_prd_fields(headings, tables, content)
    prd_pages = extract_prd_pages(content, headings)
    prd_states = extract_prd_states(content, headings, tables)
    prd_perm_pages = extract_prd_permission_pages(headings, tables, content)

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
        prd_states, state_title_to_id, fuzzy_state_match,
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
        "source": {
            "design": "output/design/design.md (human-readable)",
            "prd": "output/prd/prd.md (human-readable)",
        },
        "extracted": {
            "prd_fields_count": len(prd_fields),
            "prd_pages_count": len(prd_pages),
            "prd_states_count": len(prd_states),
            "prd_permission_pages_count": len(prd_perm_pages),
        },
        "fields": field_result,
        "pages": page_result,
        "states": state_result,
        "permissions": perm_result,
        "summary": {
            "total_missing": total_missing,
            "total_hallucinated": total_hallucinated,
            "total_attribute_mismatch": total_attribute_mismatch,
            "has_hallucination": total_hallucinated > 0,
            "has_missing": total_missing > 0,
            "has_attribute_mismatch": total_attribute_mismatch > 0,
        },
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # vNext: missing / hallucinated / attribute_mismatch 任一非零都返回退出码 1
    # 调用方必须修正后重新检查
    if total_hallucinated > 0 or total_missing > 0 or total_attribute_mismatch > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
