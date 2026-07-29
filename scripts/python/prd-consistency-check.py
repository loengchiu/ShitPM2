#!/usr/bin/env python3
"""prd-consistency-check.py — PRD 与 design 确定性结构对比（ShitPM: 直接读人读稿，多模板兼容）

ShitPM 变更：
- 不再依赖 .workflow/metadata/design/ 下的 metadata 文件。
- 直接读取 output/design/design.md 和 output/prd/prd.md，从人读稿中提取实体做集合对比。
- 复用 stage-prep.py 的 generate_design_metadata 函数从 design.md 提取实体（不写入 metadata 文件）。
- 多模板兼容：支持新归位模板（字段/状态/权限归位到 §5 详细需求说明）和旧模板（数据字典/状态机/权限汇总独立章节 + `### page-N 页面名`）。
- 只做确定性提取和集合对比，不做语义判断。
- 可靠结构事实（字段属性、内部字段交付、明确权限允许/禁止反转）由脚本检查；复杂业务语义仍由 Review 判断。

退出码：
- 0: 通过（无 missing、无 hallucinated、无 attribute_mismatch），或 skipped（Prototype-only + --allow-no-prd）
- 1: 发现 hallucinated / missing / attribute_mismatch（调用方必须修正后重新检查）
- 2: 致命错误（design.md 或 prd.md 不存在等）

用法：
  python prd-consistency-check.py --project-root .

ShitPM 修复包 D 增强：
- 输出分类区分确定性冲突、可能遗漏、需模型语义判断，便于调用方（如 Fix）按严重程度处理。
- 支持 --allow-no-prd 参数：Prototype-only 项目无 PRD 时返回 skipped，退出码 0，不阻塞 Fix。
- 字段类型差异保留给语义判断；必填、长度、默认值、枚举、格式、业务来源及内部字段交付的明确差异视为确定性问题。
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

# PRD 章节别名（用于章节定位，但 ShitPM 主要采用全文扫描策略，章节定位仅作辅助）
NON_CONCRETE_STATE_NAMES = frozenset({"—", "-", "N/A", "任意状态", "状态"})


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
    """从 PRD 提取字段及可确定比较的属性。

    支持 7 列交付格式、Design 9 列镜像格式和历史 4/5 列格式。历史格式中的
    属性只从独立列或带标签的“取值约束/规则/说明”中兼容提取，避免用整段包含关系掩盖缺失。
    """
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["详细需求说明", "数据字典", "字段定义", "字段清单"]
    )
    fields = []

    def _idx(headers, tokens, exclude=()):
        for i, header in enumerate(headers):
            if any(token in header for token in tokens) and not any(token in header for token in exclude):
                return i
        return None

    def _cell(row, idx):
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    def _labeled_value(raw, labels):
        if not raw:
            return ""
        label_pattern = "|".join(re.escape(label) for label in labels)
        match = re.search(
            rf"(?:{label_pattern})\s*(?:[：:]|≤|≥|<=|>=|<|>)\s*([^；;\n]+)",
            raw,
        )
        return match.group(1).strip() if match else ""

    def _extract_from_tables(table_list):
        for table in table_list:
            headers = table.get("headers", [])
            if not headers:
                continue
            header_text = "|".join(headers)
            if "字段" not in header_text or "类型" not in header_text:
                continue
            name_idx = _idx(headers, ("字段",), ("字段权限",))
            type_idx = _idx(headers, ("类型",))
            if name_idx is None or type_idx is None:
                continue
            required_idx = _idx(headers, ("必填",))
            constraint_idx = _idx(headers, ("取值约束", "约束", "规则", "枚举"))
            length_idx = _idx(headers, ("长度",))
            default_idx = _idx(headers, ("默认值", "默认"))
            format_idx = _idx(headers, ("格式",))
            source_idx = _idx(headers, ("业务来源", "来源"))
            description_idx = _idx(headers, ("说明", "含义", "用途"))

            for row in table["rows"]:
                if not row:
                    continue
                name = _cell(row, name_idx)
                if not name or name in ("---", "字段"):
                    continue
                required = None
                required_cell = _cell(row, required_idx)
                if required_cell in ("是", "否"):
                    required = required_cell == "是"
                field_type = _cell(row, type_idx)
                constraint_text = _cell(row, constraint_idx)
                description = _cell(row, description_idx)
                length = _cell(row, length_idx)
                if not length:
                    length = _labeled_value(constraint_text, ("最大长度", "长度", "字符数"))
                field_format = _cell(row, format_idx)
                if not field_format:
                    field_format = _labeled_value(constraint_text, ("格式",))
                default = _cell(row, default_idx)
                if default_idx is None:
                    default = _labeled_value(constraint_text, ("默认值", "默认")) or _labeled_value(description, ("默认值", "默认"))
                source = _cell(row, source_idx)
                if source_idx is None:
                    source = _labeled_value(constraint_text, ("业务来源", "来源")) or _labeled_value(description, ("业务来源", "来源"))
                combined_text = "；".join(v for v in (
                    constraint_text, length, field_format, default, source, description,
                ) if v)
                enum_values = []
                if "enum" in field_type.lower() or "枚举" in field_type:
                    enum_values = _parse_enum_values(constraint_text)
                    if not enum_values:
                        enum_values = _parse_enum_values(description)
                fields.append({
                    "name": name,
                    "line": table.get("line_offset"),
                    "type": field_type,
                    "required": required,
                    "constraints": constraint_text,
                    "length": length,
                    "default": default,
                    "format": field_format,
                    "source": source,
                    "description": description,
                    "combined_text": combined_text,
                    "enum_values": enum_values,
                })

    if candidate_ranges:
        _extract_from_tables(_tables_in_ranges(tables, candidate_ranges))
    if not fields:
        _extract_from_tables(tables)
    return fields


def extract_prd_pages(content: str, headings: list) -> list:
    """从 PRD 提取页面名

    ShitPM 多模板兼容策略，识别以下格式：
    1. 新编号体系粗体块：`**N.N.N 页面名**` 或 `**N.N.N.N 页面名**`
    2. 旧模板格式：`### page-N 页面名`（如 `### page-1 我的周报列表`）
    3. 中编号格式：`### N.N 页面名`（如 `### 3.1 我的周报列表`）
    4. 在"页面说明"章节内的 `### 页面名` 标题（无编号）

    跳过大模块（##）和容器章节标题。
    ShitPM 修复：候选章节不再包含"详细需求说明"，避免把详细需求下的子模块标题误识别为页面。
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

    # 候选章节范围：仅页面说明类章节（不再含"详细需求说明"，避免子模块标题误判为页面）
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["页面说明", "页面清单", "页面列表", "页面规划", "页面目录"]
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


def _strip_code_blocks(text: str) -> str:
    """排除 fenced code block（```...```），避免 Mermaid 图语法被当成状态文本

    保留代码块占位行（空行），保持行号一致。
    """
    lines = text.split("\n")
    result = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            result.append("")
            continue
        if in_fence:
            result.append("")
            continue
        result.append(line)
    return "\n".join(result)


def extract_prd_states(content: str, headings: list, tables: list) -> list:
    """从 PRD 提取状态名

    ShitPM 多模板兼容策略：
    - 候选章节：详细需求说明、状态机、状态定义、状态流转
    - 在候选章节范围内查找箭头文本和状态机表格
    - 如候选章节都未找到，降级为全文扫描
    - ShitPM 修复：先排除 fenced code block，避免 Mermaid 图语法（A[草稿] -->、|审批通过| C[已通过]）被误识别为状态

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
        if not name or name in NON_CONCRETE_STATE_NAMES:
            return
        # 过滤 Mermaid 残留片段（如 A[草稿]、|审批通过|）
        if re.match(r'^[A-Z]\[', name) or name.startswith("|") or name.endswith("]"):
            return
        # 过滤含特殊语法的片段
        if any(ch in name for ch in ("-->", "---", "==>", "~~", ">>", "<<")):
            return
        if name not in seen:
            seen.add(name)
            states.append(name)

    # ShitPM 修复：先排除代码块再扫描
    content_clean = _strip_code_blocks(content)

    # 策略 1: 在候选章节范围内查找
    if candidate_ranges:
        ranges_content = _lines_in_ranges(content_clean, candidate_ranges)
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
        for line in content_clean.split("\n"):
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

    ShitPM 多模板兼容策略：
    - 候选章节：权限汇总、权限定义、权限规则（ShitPM 修复：移除"详细需求说明"，避免子模块标题误判为权限页面）
    - 策略 1：在权限章节范围内的 `### N.N xxx` 大模块标题
    - 策略 2：在权限汇总章节内的表格第一列提取页面名（旧模板格式）
    - 策略 3：候选章节未找到，降级为全文扫描权限表

    design permissions.json 的 page 字段是模块名（如"审计计划""项目启动"），
    与 PRD 的大模块标题或权限表第一列对应。
    """
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["权限汇总", "权限定义", "权限规则"]
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
    if candidate_ranges:
        for table in _tables_in_ranges(tables, candidate_ranges):
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


# ── 权限角色对提取（ShitPM 增强：覆盖角色级一致性） ────────────

# 权限章节关键词（与 stage-prep.py _PERM_SECTION_KEYWORDS 保持一致并扩展）
_PERM_SECTION_KEYWORDS_EXTENDED = (
    "权限汇总", "权限定义", "权限规则", "角色权限", "权限矩阵", "权限",
)

# 列表项 - role：action 模式（与 stage-prep.py _KEY_VALUE_LIST_PATTERN 等价）
_KV_LIST_PATTERN = re.compile(r'^[-*]\s*`?([^`：:\s]+)`?\s*[：:]\s*(.+)$')


def _extract_perm_pairs_from_table(table: dict, pairs: list, seen: set) -> None:
    """从单个权限表格提取 (page, role) 二元组，追加到 pairs 列表"""
    headers = table.get("headers", [])
    if not headers or len(headers) < 2:
        return
    # 权限表特征：第一列表头含"模块"、"操作对象"、"页面"、"对象"
    if not any(k in headers[0] for k in ("模块", "操作对象", "页面", "对象")):
        return
    # 表头其他列是角色名
    role_cols = [(i, h) for i, h in enumerate(headers) if i > 0 and h and h != "---"]
    for row in table["rows"]:
        if not row or not row[0] or row[0] in ("---",):
            continue
        page_name = re.sub(r'^\d+\.\d+(?:\.\d+)*\s*', '', row[0].strip())
        if not page_name:
            continue
        for col_idx, role_name in role_cols:
            if col_idx < len(row):
                cell = row[col_idx] if row[col_idx] else ""
                # 单元格非空且非分隔符即认为该 (page, role) 二元组存在
                if cell.strip() and cell.strip() != "---":
                    role_clean = re.sub(r'^\d+\.\d+(?:\.\d+)*\s*', '', role_name.strip()).strip('`')
                    if not role_clean:
                        continue
                    key = (page_name, role_clean)
                    if key not in seen:
                        seen.add(key)
                        pairs.append({"page": page_name, "role": role_clean, "action": cell.strip()})


def _extract_perm_pairs_from_list(content: str, pairs: list, seen: set) -> None:
    """从权限章节内的 ### 页面名 + - role：action 列表提取 (page, role) 二元组"""
    lines = content.split('\n')
    in_perm_section = False
    current_page = ""

    for line in lines:
        stripped = line.strip()
        # 检测进入/退出权限章节（h1/h2 级别）
        if re.match(r'^#{1,2}\s+', stripped):
            if any(kw in stripped for kw in _PERM_SECTION_KEYWORDS_EXTENDED):
                in_perm_section = True
            else:
                in_perm_section = False
            current_page = ""
            continue
        if not in_perm_section:
            continue
        # h3/h4 子标题 = 页面分组名
        if re.match(r'^#{3,}\s+', stripped):
            current_page = re.sub(r'^#{3,}\s+', '', stripped).strip()
            current_page = re.sub(r'^\d+\.\d+(?:\.\d+)*\s*', '', current_page)
            continue
        # - role：action 列表项
        match = _KV_LIST_PATTERN.match(stripped)
        if match and current_page:
            role = match.group(1).strip().strip('`')
            if not role:
                continue
            key = (current_page, role)
            if key not in seen:
                seen.add(key)
                pairs.append({"page": current_page, "role": role, "action": match.group(2).strip()})


def extract_prd_permission_role_pairs(headings: list, tables: list, content: str) -> list:
    """从 PRD 提取权限 (page, role) 二元组

    支持两种格式：
    - 表格格式：表头是角色名列表，第一列是模块/操作对象名（ShitPM PRD 模板）
    - 列表格式：### 页面名 + - role：action（与 design 权限格式一致）

    返回 [{"page": str, "role": str, "action": str}, ...]
    """
    pairs = []
    seen = set()

    candidate_ranges = _find_multiple_section_ranges(
        headings, list(_PERM_SECTION_KEYWORDS_EXTENDED)
    )

    # 策略 1：从权限章节内的表格提取
    for table in _tables_in_ranges(tables, candidate_ranges):
        _extract_perm_pairs_from_table(table, pairs, seen)

    # 策略 2：从权限章节内的列表提取
    _extract_perm_pairs_from_list(content, pairs, seen)

    return pairs


def extract_prd_roles(headings: list, tables: list, content: str) -> list:
    """从 PRD 权限章节提取所有角色名集合

    来源：
    - 权限表格的表头列名（除第一列）
    - 权限列表的 role 部分

    返回排序后的角色名列表
    """
    roles = set()

    candidate_ranges = _find_multiple_section_ranges(
        headings, list(_PERM_SECTION_KEYWORDS_EXTENDED)
    )

    # 从表格表头提取角色名
    for table in _tables_in_ranges(tables, candidate_ranges):
        headers = table.get("headers", [])
        if not headers or len(headers) < 2:
            continue
        if not any(k in headers[0] for k in ("模块", "操作对象", "页面", "对象")):
            continue
        for h in headers[1:]:
            if h and h != "---":
                role = re.sub(r'^\d+\.\d+(?:\.\d+)*\s*', '', h.strip()).strip('`')
                if role:
                    roles.add(role)

    # 从列表项提取角色名
    lines = content.split('\n')
    in_perm_section = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^#{1,2}\s+', stripped):
            if any(kw in stripped for kw in _PERM_SECTION_KEYWORDS_EXTENDED):
                in_perm_section = True
            else:
                in_perm_section = False
            continue
        if not in_perm_section:
            continue
        match = _KV_LIST_PATTERN.match(stripped)
        if match:
            role = match.group(1).strip().strip('`')
            if role:
                roles.add(role)

    return sorted(roles)


def compare_permission_role_pairs(
    design_perms: list,
    prd_perm_pairs: list,
) -> dict:
    """对比 (page, role) 二元组集合

    PRD 中出现 design 没有的 (page, role) 视为 hallucinated
    Design 中出现 PRD 没有的 (page, role) 视为 missing

    page 用 fuzzy_page_match 做模糊匹配，role 要求精确匹配。
    """
    design_pairs = set()
    for p in design_perms:
        if isinstance(p, dict) and p.get("page") and p.get("role"):
            design_pairs.add((p["page"], p["role"]))

    prd_pairs = set()
    for p in prd_perm_pairs:
        if isinstance(p, dict) and p.get("page") and p.get("role"):
            prd_pairs.add((p["page"], p["role"]))

    design_pages = {p[0] for p in design_pairs}

    matched_design = set()
    matched_prd = set()

    for prd_page, prd_role in prd_pairs:
        # 精确匹配
        if (prd_page, prd_role) in design_pairs:
            matched_design.add((prd_page, prd_role))
            matched_prd.add((prd_page, prd_role))
            continue
        # 模糊匹配 page（role 必须精确一致）
        for dp in design_pages:
            if dp == prd_page:
                continue
            if fuzzy_page_match(prd_page, {dp: dp}):
                if (dp, prd_role) in design_pairs:
                    matched_design.add((dp, prd_role))
                    matched_prd.add((prd_page, prd_role))
                    break

    missing = sorted(design_pairs - matched_design)
    hallucinated = sorted(prd_pairs - matched_prd)

    missing_list = [{"page": p, "role": r} for p, r in missing]
    hallucinated_list = [{"page": p, "role": r} for p, r in hallucinated]

    return {
        "missing": missing_list,
        "hallucinated": hallucinated_list,
        "matched_count": len(matched_design),
    }


# ── 模块提取与对比（ShitPM 增强：覆盖模块职责一致性） ──────────

def extract_prd_modules(headings: list, content: str) -> list:
    """从 PRD 详细需求说明章节提取模块名

    策略：在"详细需求说明"章节范围内，提取 ### N.N 模块名 标题
    返回去重后的模块名列表
    """
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["详细需求说明", "详细需求", "需求说明", "详细需求规格", "需求详细说明"]
    )

    modules = []
    seen = set()

    for h in headings:
        for start, end, _ in candidate_ranges:
            if h["line"] < start:
                continue
            if end is not None and h["line"] >= end:
                continue
            if h["level"] != 3:
                continue
            title = strip_heading_number(h["title"])
            title = re.sub(r'^\d+\.\d+(?:\.\d+)*\s*', '', title).strip()
            if not title:
                continue
            if title not in seen:
                seen.add(title)
                modules.append(title)
            break

    return modules


def _normalize_module_name(name: str) -> str:
    """归一化模块名：去尾部"模块"二字，便于 design 和 PRD 对比"""
    if not name:
        return ""
    name = name.strip()
    if name.endswith("模块"):
        name = name[:-2].strip()
    return name


def compare_modules(design_modules: list, prd_modules: list) -> dict:
    """对比模块名集合（归一化后对比）

    design modules title 通常带"模块"后缀（如"审计计划模块"），
    PRD 模块标题可能带也可能不带"模块"后缀。
    归一化后做集合对比。
    """
    design_set = {_normalize_module_name(m) for m in design_modules if m}
    prd_set = {_normalize_module_name(m) for m in prd_modules if m}

    matched = design_set & prd_set
    missing = sorted(design_set - matched)
    hallucinated = sorted(prd_set - matched)

    return {
        "missing": missing,
        "hallucinated": hallucinated,
        "matched_count": len(matched),
    }


# ── 字段属性对比 ──────────────────────────────────────────────

def _normalize_type(type_str: str) -> str:
    """归一化类型字符串以便比较：去空格、转小写。"""
    if not type_str:
        return ""
    return re.sub(r"\s+", "", type_str).lower()


def _normalize_scalar(value) -> str:
    """归一化可直接比较的字段属性；占位符视为空。"""
    if value is None:
        return ""
    text = str(value).strip().strip("`")
    if text in ("", "—", "-", "无", "不适用", "N/A", "NA", "null", "None"):
        return ""
    return re.sub(r"[\s，,；;。]+", "", text).lower()


def _parse_enum_values(raw: str) -> list[str]:
    """解析明确枚举值；兼容“状态（draft/submitted）”这类旧说明写法。"""
    if not raw:
        return []
    text = raw.strip().strip("`")
    if text in ("—", "-", "无", "无枚举", "N/A", "NA"):
        return []
    labeled = re.search(r"(?:枚举(?:值)?|取值)\s*[：:]\s*([^；;\n]+)", text)
    if labeled:
        text = labeled.group(1)
    else:
        parenthesized = re.findall(r"[（(]([^（）()]+)[）)]", text)
        if parenthesized:
            delimited = [part for part in parenthesized if re.search(r"[,，/、;；|\n]", part)]
            if len(delimited) == 1:
                text = delimited[0]
    if not re.search(r"[,，/、;；|\n]", text):
        return []
    values = re.split(r"[,，/、;；|\n]+", text)
    return sorted({
        re.sub(r"^[-*●]\s*", "", value).strip(" `（）()")
        for value in values if value.strip(" `（）()")
    })


def _attribute_present_in_prd(design_value, prd_value) -> bool:
    """只比较独立列或已解析的标签值，避免被其他属性中的同词误判为已交付。"""
    design_norm = _normalize_scalar(design_value)
    if not design_norm:
        return True
    return _normalize_scalar(prd_value) == design_norm


def compare_field_attributes(
    design_fields: list,
    prd_fields: list,
    design_title_to_id: dict,
    fuzzy_fn=None,
) -> list:
    """对比 matched 字段的可确定属性。

    type 仍可能存在等价别名，单独标记为需语义判断；其余明确属性缺失或差异
    均可由结构化字段表可靠证明。
    """
    design_attrs = {}
    for field in design_fields:
        if not isinstance(field, dict) or "title" not in field:
            continue
        attrs = field.get("attributes", {})
        design_attrs[field["title"]] = {
            "type": attrs.get("数据类型", ""),
            "required": attrs.get("必填"),
            "length": attrs.get("长度", ""),
            "default": attrs.get("默认值", ""),
            "enum_values": _parse_enum_values(attrs.get("枚举值", "")),
            "format": attrs.get("格式", ""),
            "source": attrs.get("业务来源", ""),
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

        design = design_attrs[matched_design]
        mismatch_kinds = []
        d_type = _normalize_type(design["type"])
        p_type = _normalize_type(prd_field.get("type", ""))
        if d_type and p_type and d_type != p_type:
            mismatch_kinds.append("type")

        d_required = design["required"]
        p_required = prd_field.get("required")
        if d_required is not None and p_required is not None and d_required != p_required:
            mismatch_kinds.append("required")
        elif d_required is not None and p_required is None:
            mismatch_kinds.append("required_missing")

        for key in ("length", "default", "format", "source"):
            if not _attribute_present_in_prd(design[key], prd_field.get(key, "")):
                mismatch_kinds.append(key)

        d_enum = design["enum_values"]
        p_enum = prd_field.get("enum_values", [])
        if d_enum != p_enum and (d_enum or p_enum):
            mismatch_kinds.append("enum")

        if mismatch_kinds:
            deterministic_kinds = [kind for kind in mismatch_kinds if kind != "type"]
            mismatches.append({
                "name": prd_name,
                "mismatch_kinds": mismatch_kinds,
                "deterministic": bool(deterministic_kinds),
                "design_type": design["type"],
                "prd_type": prd_field.get("type", ""),
                "design_required": d_required,
                "prd_required": p_required,
                "design_length": design["length"],
                "prd_length": prd_field.get("length", ""),
                "design_default": design["default"],
                "prd_default": prd_field.get("default", ""),
                "design_enum_values": d_enum,
                "prd_enum_values": p_enum,
                "design_format": design["format"],
                "prd_format": prd_field.get("format", ""),
                "design_source": design["source"],
                "prd_source": prd_field.get("source", ""),
                "enum_missing": sorted(set(d_enum) - set(p_enum)),
                "enum_hallucinated": sorted(set(p_enum) - set(d_enum)),
            })
    return mismatches


def compare_internal_field_delivery(
    design_non_page_fields: list,
    prd_fields: list,
    design_title_to_id: dict,
    fuzzy_fn=None,
) -> list:
    """检查 Design 非页面字段是否在 PRD 中保留并说明内部用途。"""
    issues = []
    for entry in design_non_page_fields:
        if not isinstance(entry, dict) or not entry.get("field_title"):
            continue
        title = entry["field_title"]
        matched = None
        for prd_field in prd_fields:
            name = prd_field.get("name", "") if isinstance(prd_field, dict) else ""
            if name == title or _try_match(name, {title: design_title_to_id.get(title, title)}, fuzzy_fn) == title:
                matched = prd_field
                break
        if matched is None:
            issues.append({"name": title, "issue": "missing"})
            continue
        description = matched.get("description", "")
        if not re.search(r"内部|审计|关联|计算|历史|留痕|不在页面|不展示", description):
            issues.append({
                "name": title,
                "issue": "internal_usage_missing",
                "prd_description": description,
                "design_reason": entry.get("reason", ""),
            })
    return issues


def _permission_polarity(action: str) -> str | None:
    """只识别明确、单一的允许或禁止口径，混合权限返回 None。"""
    text = re.sub(r"\s+", "", action or "")
    if not text:
        return None
    action_words = r"查看|编辑|新建|创建|提交|撤回|删除|导出|导入|使用|操作|填写|审批|分配"
    deny_pattern = rf"无权限|无权(?:{action_words})?|不可(?:{action_words})?|不能(?:{action_words})?|禁止(?:{action_words})?|不允许(?:{action_words})?|默认不(?:{action_words})?|不参与(?:{action_words})?"
    has_deny = bool(re.search(deny_pattern, text))
    remaining = re.sub(deny_pattern, "", text)
    has_allow = bool(re.search(rf"允许|有权限|(?:可|可以|能够|有权)?(?:{action_words})", remaining))
    if has_deny and not has_allow:
        return "deny"
    if has_allow and not has_deny:
        return "allow"
    return None


def compare_permission_polarity(design_perms: list, prd_perm_pairs: list) -> list:
    """检查相同页面和角色下可可靠证明的明确允许/禁止反转。"""
    inversions = []
    for design in design_perms:
        if not isinstance(design, dict):
            continue
        d_page, d_role = design.get("page"), design.get("role")
        d_polarity = _permission_polarity(design.get("action", ""))
        if not d_page or not d_role or d_polarity is None:
            continue
        for prd in prd_perm_pairs:
            if not isinstance(prd, dict) or prd.get("role") != d_role:
                continue
            p_page = prd.get("page", "")
            page_matches = p_page == d_page or bool(fuzzy_page_match(p_page, {d_page: d_page}))
            if not page_matches:
                continue
            p_polarity = _permission_polarity(prd.get("action", ""))
            if p_polarity and p_polarity != d_polarity:
                inversions.append({
                    "page": d_page,
                    "role": d_role,
                    "design_action": design.get("action", ""),
                    "prd_action": prd.get("action", ""),
                    "design_polarity": d_polarity,
                    "prd_polarity": p_polarity,
                })
            break
    return inversions


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



def _load_verified_design_index(project_root: Path):
    """优先读取并校验 Design 索引；索引缺失时仅在内存中从 design.md 编译。"""
    path = Path(__file__).with_name("design-index.py")
    spec = importlib.util.spec_from_file_location("design_index", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    index, error, from_file = module.load_verified_index(project_root)
    return module, index, error, from_file


def _indexed_expected_entities(index: dict) -> list[dict]:
    pages_by_id = {item.get("id"): item for item in index.get("pages", []) if isinstance(item, dict)}
    blocks_by_id = {item.get("id"): item for item in index.get("blocks", []) if isinstance(item, dict)}
    expected = []
    for page in index.get("pages", []):
        expected.append({"type": "page", "name": page.get("name"), "page_name": None, "block_name": None, "attributes": page.get("attributes", {})})
        for block in page.get("blocks", []):
            expected.append({"type": "block", "name": block.get("name"), "page_name": page.get("name"), "block_name": None, "attributes": block.get("attributes", {})})
    for entity_type, key in (("field", "fields"), ("operation", "operations")):
        for item in index.get(key, []):
            page = pages_by_id.get(item.get("page_id"), {})
            block = blocks_by_id.get(item.get("block_id"), {})
            expected.append({
                "type": entity_type,
                "name": item.get("name"),
                "page_name": page.get("name"),
                "block_name": block.get("name"),
                "attributes": item.get("attributes", {}),
            })
    return [item for item in expected if item.get("name")]


def _indexed_entity_key(item: dict) -> tuple:
    return (item.get("type"), item.get("page_name"), item.get("block_name"), item.get("name"))


def _normalize_indexed_value(value) -> str:
    if value is None:
        return ""
    value = str(value).strip().strip("`")
    if value in {"", "—", "-", "无", "不适用", "N/A", "NA", "null", "None"}:
        return ""
    return re.sub(r"[\s，,；;。]+", "", value).lower()


def _compare_indexed_structure(index: dict, content: str, index_module) -> dict:
    expected = _indexed_expected_entities(index)
    # 旧格式由 design-index.py 明确标记为 unsupported_format 时，交给 legacy
    # 提取器处理；不能把 PRD 的旧格式实体当成“新增实体”报告为索引幻觉。
    if not expected:
        return {
            "enabled": False,
            "expected_count": 0,
            "matched_count": 0,
            "missing": [],
            "hallucinated": [],
            "attribute_mismatch": [],
        }
    actual_nodes = index_module.extract_document_entities(content)
    flexible = False

    if not actual_nodes:
        headings = parse_headings(content)
        tables = parse_tables_with_context(content, headings)
        prd_pages = extract_prd_pages(content, headings)
        prd_fields = extract_prd_fields(headings, tables, content)
        page_markers = []
        page_pattern = re.compile(r'^\*\*(?:\d+(?:\.\d+)+)\s+(.+?)\*\*\s*$')
        for line_no, line in enumerate(content.splitlines(), 1):
            match = page_pattern.match(line.strip())
            if match:
                page_markers.append((line_no, clean_page_title(match.group(1))))
        page_markers.sort()

        def page_for_line(line_no: int | None) -> str | None:
            if not page_markers:
                return prd_pages[0] if len(prd_pages) == 1 else None
            selected = None
            for marker_line, marker_name in page_markers:
                if line_no is None or marker_line <= line_no:
                    selected = marker_name
                else:
                    break
            return selected

        actual_nodes = [
            {"type": "page", "name": name, "page_name": None, "block_name": None, "attributes": {}, "line": None}
            for name in prd_pages
        ]
        for field in prd_fields:
            attrs = {}
            if field.get("source"):
                attrs["source"] = field["source"]
            if field.get("required") is not None:
                attrs["required"] = "是" if field["required"] else "否"
            actual_nodes.append({
                "type": "field",
                "name": field.get("name"),
                "page_name": page_for_line(field.get("line")),
                "block_name": None,
                "attributes": attrs,
                "line": field.get("line"),
            })
        operation_pattern = re.compile(r'^\s*[·•]\s*(?:\*\*)?([^：:]+?)(?:\*\*)?\s*$')
        for line_no, line in enumerate(content.splitlines(), 1):
            match = operation_pattern.match(line)
            if match:
                name = match.group(1).strip()
                if name and name not in {"动作一", "动作二"}:
                    actual_nodes.append({
                        "type": "operation", "name": name,
                        "page_name": page_for_line(line_no), "block_name": None,
                        "attributes": {}, "line": line_no,
                    })
        flexible = bool(prd_pages or prd_fields)

    def structure_key(item: dict, flexible_mode: bool = False) -> tuple:
        if flexible_mode and item.get("type") in {"field", "operation"}:
            return (item.get("type"), item.get("page_name"), item.get("name"))
        return _indexed_entity_key(item)

    expected_for_compare = [
        item for item in expected
        if not (flexible and item.get("type") == "block")
    ]
    expected_keys = {structure_key(item, flexible) for item in expected_for_compare}
    actual_keys = {structure_key(item, flexible) for item in actual_nodes}
    missing = [item for item in expected_for_compare if structure_key(item, flexible) not in actual_keys]
    hallucinated = [
        {"type": item.get("type"), "name": item.get("name"), "page_name": item.get("page_name"), "block_name": item.get("block_name"), "line": item.get("line")}
        for item in actual_nodes if structure_key(item, flexible) not in expected_keys
    ]
    actual_by_key = {structure_key(item, flexible): item for item in actual_nodes}
    attribute_mismatch = []
    checks = {
        "field": ("source", "required") if flexible else ("source", "required", "display_condition"),
        "operation": () if flexible else ("success_result", "state_change"),
    }
    for item in expected_for_compare:
        if item.get("type") not in checks:
            continue
        actual_item = actual_by_key.get(structure_key(item, flexible))
        if actual_item is None:
            continue
        for attr in checks[item["type"]]:
            expected_value = item.get("attributes", {}).get(attr)
            if expected_value is None or _normalize_indexed_value(expected_value) == "":
                continue
            actual_value = actual_item.get("attributes", {}).get(attr)
            if _normalize_indexed_value(actual_value) != _normalize_indexed_value(expected_value):
                attribute_mismatch.append({
                    "type": item["type"],
                    "name": item["name"],
                    "page_name": item.get("page_name"),
                    "block_name": item.get("block_name"),
                    "attribute": attr,
                    "expected": expected_value,
                    "actual": actual_value or "",
                    "deterministic": True,
                })
    return {
        "enabled": bool(expected),
        "expected_count": len(expected_for_compare),
        "matched_count": len(expected_keys & actual_keys),
        "missing": missing,
        "hallucinated": hallucinated,
        "attribute_mismatch": attribute_mismatch,
    }

# ── 主入口 ────────────────────────────────────────────────────

def _load_design_entities_from_md(project_root: Path):
    """ShitPM: 从 output/design/design.md 直接提取实体（不依赖 metadata）

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
    parser = argparse.ArgumentParser(description="PRD 与 design 确定性结构对比（ShitPM: 直接读人读稿，多模板兼容）")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="项目根目录")
    parser.add_argument(
        "--allow-no-prd",
        action="store_true",
        default=False,
        help="Prototype-only 项目无 PRD 时返回 skipped，退出码 0，不阻塞 Fix",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()

    # ShitPM: 直接读 prd.md（兼容 stdin 模式以保留旧调用方式）
    # ShitPM 修复：stdin 为空时回退读取默认 prd.md，而非直接报错（CI/重定向环境稳定性）
    prd_path = project_root / "output" / "prd" / "prd.md"
    content = None
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read()
        if stdin_content.strip():
            content = stdin_content
    if content is None:
        if not prd_path.exists():
            # ShitPM 修复包 D：--allow-no-prd 时 Prototype-only 项目跳过检查，退出码 0，不阻塞 Fix
            if args.allow_no_prd:
                print(json.dumps({
                    "skipped": True,
                    "reason": "PRD 不存在（Prototype-only 项目），跳过 PRD 一致性检查",
                    "project_type": "prototype-only",
                    "exit_reason": "skipped",
                }, ensure_ascii=False, indent=2))
                sys.exit(0)
            print(json.dumps({"error": f"prd.md not found: {prd_path}"}, ensure_ascii=False))
            sys.exit(2)
        with open(prd_path, encoding="utf-8") as f:
            content = f.read()

    # ShitPM: 从 design.md 直接提取实体（不依赖 metadata）
    design_data, err = _load_design_entities_from_md(project_root)
    if design_data is None:
        print(json.dumps({"error": err or "无法加载 design 实体"}, ensure_ascii=False))
        sys.exit(2)

    # 阶段 9：优先读取与 design.md 哈希绑定的索引；缺失时只在内存中编译，绝不把索引当事实源。
    try:
        design_index_module, design_index, design_index_error, design_index_from_file = _load_verified_design_index(project_root)
    except Exception as exc:
        print(json.dumps({"error": f"Design 索引加载失败: {exc}"}, ensure_ascii=False))
        sys.exit(2)
    if design_index is None or design_index_error:
        print(json.dumps({"error": design_index_error or "Design 索引解析失败"}, ensure_ascii=False))
        sys.exit(2)
    indexed_result = _compare_indexed_structure(design_index, content, design_index_module)
    indexed_active = indexed_result["enabled"]

    design_fields = design_data.get("fields", []) or []
    design_pages = design_data.get("pages", []) or []
    design_states = design_data.get("states", []) or []
    design_permissions = design_data.get("permissions", []) or []
    design_modules_raw = design_data.get("modules", []) or []
    # ShitPM：读取 Design 中标记为“非页面落点字段”的内部/审计字段，用于验证 PRD 是否完整交付
    design_non_page_fields = design_data.get("non_page_fields", []) or []

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

    # PRD 是研发交付物：Design 的页面字段和非页面内部字段都必须出现。
    # 非页面字段无需虚构页面落点，但必须在字段表保留来源和内部用途。

    # 固定结构 Design 使用索引完成页面/字段覆盖和高影响属性检查；旧模板继续走 legacy 解析。
    if indexed_active:
        field_result = {
            "missing": [], "hallucinated": [], "attribute_mismatch": [],
            "enum_mismatch": [], "deterministic_attribute_mismatch": [], "internal_field_issues": [],
        }
        page_result = {"missing": [], "hallucinated": [], "matched_count": 0}
    else:
        prd_field_names = [f["name"] for f in prd_fields if isinstance(f, dict) and "name" in f]
        field_result = compare_entities(
            [f["title"] for f in design_fields if isinstance(f, dict)],
            prd_field_names, field_title_to_id, fuzzy_field_match,
        )
        field_result["attribute_mismatch"] = compare_field_attributes(
            design_fields, prd_fields, field_title_to_id, fuzzy_field_match,
        )
        field_result["enum_mismatch"] = [
            item for item in field_result["attribute_mismatch"]
            if item.get("enum_missing") or item.get("enum_hallucinated")
        ]
        field_result["deterministic_attribute_mismatch"] = [
            item for item in field_result["attribute_mismatch"] if item.get("deterministic")
        ]
        field_result["internal_field_issues"] = compare_internal_field_delivery(
            design_non_page_fields, prd_fields, field_title_to_id, fuzzy_field_match,
        )
        page_result = compare_entities(
            [p["title"] for p in design_pages if isinstance(p, dict)],
            prd_pages, page_title_to_id, fuzzy_page_match,
        )

    # “任意状态”等是状态机通配/占位行，不是需要在 PRD 中单独交付的具体状态。
    # 保留 stage-prep 中的伪状态，供状态机完整性校验使用；这里只在 Design 与 PRD
    # 的下游交付集合对比边界排除它们，避免 legacy 路径误报缺失。
    design_deliverable_states = [
        s["title"]
        for s in design_states
        if isinstance(s, dict) and s.get("title") not in NON_CONCRETE_STATE_NAMES
    ]
    state_result = compare_entities(
        design_deliverable_states,
        prd_states, state_title_to_id, fuzzy_state_match,
    )
    perm_result = compare_permission_pages(design_permissions, prd_perm_pages)

    # ShitPM 增强：权限角色对对比（覆盖角色级一致性，检测 PRD 中 design 没有的角色-页面组合）
    prd_perm_pairs = extract_prd_permission_role_pairs(headings, tables, content)
    perm_pair_result = compare_permission_role_pairs(design_permissions, prd_perm_pairs)
    permission_inversions = compare_permission_polarity(design_permissions, prd_perm_pairs)

    # ShitPM 增强：角色集合对比（检测 PRD 中 design 没有的角色，如"超级管理员"幻觉角色）
    design_roles = sorted({p["role"] for p in design_permissions if isinstance(p, dict) and p.get("role")})
    prd_roles = extract_prd_roles(headings, tables, content)
    role_title_to_id = {r: r for r in design_roles}
    role_result = compare_entities(design_roles, prd_roles, role_title_to_id, None)

    # ShitPM 增强：模块集合对比（覆盖模块职责一致性）
    # 过滤只保留以"模块"结尾的标题，避免从 design 标题推断时误识别非模块标题
    design_modules = [m["title"] for m in design_modules_raw if isinstance(m, dict) and "title" in m and isinstance(m["title"], str) and m["title"].endswith("模块")]
    prd_modules = extract_prd_modules(headings, content)
    module_result = compare_modules(design_modules, prd_modules)

    total_missing = (
        len(field_result["missing"])
        + len(page_result["missing"])
        + len(indexed_result["missing"])
        + len(state_result["missing"])
        + len(perm_result["missing"])
        + len(perm_pair_result["missing"])
        + len(role_result["missing"])
        + len(module_result["missing"])
    )
    total_hallucinated = (
        len(field_result["hallucinated"])
        + len(page_result["hallucinated"])
        + len(indexed_result["hallucinated"])
        + len(state_result["hallucinated"])
        + len(perm_result["hallucinated"])
        + len(perm_pair_result["hallucinated"])
        + len(role_result["hallucinated"])
        + len(module_result["hallucinated"])
    )
    # 索引属性比较是确定性的；旧模板属性比较可能留下需要语义判断的项目。
    # 先拆分两类，再合计，避免在 indexed_active 分支重复累加同一批索引差异。
    needs_semantic_judgment_items = [
        item for item in field_result["attribute_mismatch"] if not item.get("deterministic")
    ]
    needs_semantic_judgment_count = len(needs_semantic_judgment_items)
    total_deterministic_attribute_mismatch = len(field_result["deterministic_attribute_mismatch"]) + len(indexed_result["attribute_mismatch"])
    total_attribute_mismatch = total_deterministic_attribute_mismatch + needs_semantic_judgment_count
    total_internal_field_issues = len(field_result["internal_field_issues"])
    total_permission_inversions = len(permission_inversions)

    # ShitPM 修复包 D：问题分类（确定性冲突 / 可能遗漏 / 需模型语义判断）
    deterministic_conflicts_count = (
        len(field_result["hallucinated"])
        + len(page_result["hallucinated"])
        + len(indexed_result["hallucinated"])
        + len(state_result["hallucinated"])
        + len(perm_result["hallucinated"])
        + len(perm_pair_result["hallucinated"])
        + len(role_result["hallucinated"])
        + len(module_result["hallucinated"])
        + total_deterministic_attribute_mismatch
        + total_internal_field_issues
        + total_permission_inversions
    )
    possible_omissions_count = (
        len(field_result["missing"])
        + len(page_result["missing"])
        + len(indexed_result["missing"])
        + len(state_result["missing"])
        + len(perm_result["missing"])
        + len(perm_pair_result["missing"])
        + len(role_result["missing"])
        + len(module_result["missing"])
    )
    classification = {
        "deterministic_conflicts": {
            "fields": field_result["hallucinated"],
            "field_enums": field_result["enum_mismatch"],
            "field_attributes": field_result["deterministic_attribute_mismatch"],
            "internal_fields": field_result["internal_field_issues"],
            "permission_inversions": permission_inversions,
            "pages": page_result["hallucinated"],
            "states": state_result["hallucinated"],
            "permission_pages": perm_result["hallucinated"],
            "permission_role_pairs": perm_pair_result["hallucinated"],
            "roles": role_result["hallucinated"],
            "modules": module_result["hallucinated"],
            "design_index": indexed_result["hallucinated"] + indexed_result["attribute_mismatch"],
            "count": deterministic_conflicts_count,
        },
        "possible_omissions": {
            "fields": field_result["missing"],
            "pages": page_result["missing"],
            "states": state_result["missing"],
            "permission_pages": perm_result["missing"],
            "permission_role_pairs": perm_pair_result["missing"],
            "roles": role_result["missing"],
            "modules": module_result["missing"],
            "design_index": indexed_result["missing"],
            "count": possible_omissions_count,
        },
        "needs_semantic_judgment": {
            "attribute_mismatches": needs_semantic_judgment_items,
            "count": needs_semantic_judgment_count,
            "hint": "仅字段类型等价性仍需语义判断；明确属性缺失和差异已归入确定性冲突。",
        },
    }

    # ShitPM 修复包 D：exit_reason 按严重程度优先级判定
    # 优先级：deterministic_conflict > possible_omission > needs_semantic_judgment > ok
    if (total_hallucinated > 0 or field_result["enum_mismatch"]
            or total_deterministic_attribute_mismatch > 0
            or total_internal_field_issues > 0
            or total_permission_inversions > 0):
        exit_reason = "deterministic_conflict"
    elif total_missing > 0:
        exit_reason = "possible_omission"
    elif total_attribute_mismatch > 0:
        exit_reason = "needs_semantic_judgment"
    else:
        exit_reason = "ok"

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
            "prd_permission_role_pairs_count": len(prd_perm_pairs),
            "prd_roles_count": len(prd_roles),
            "prd_modules_count": len(prd_modules),
        },
        "fields": field_result,
        "pages": page_result,
        "states": state_result,
        "permissions": perm_result,
        "permission_role_pairs": perm_pair_result,
        "permission_inversions": permission_inversions,
        "roles": role_result,
        "modules": module_result,
        "design_index": {
            "used": True,
            "from_file": design_index_from_file,
            "path": ".workflow/runtime/context/design/index/design-index.json",
            "structure": indexed_result,
        },
        "classification": classification,
        "summary": {
            "total_missing": total_missing,
            "total_hallucinated": total_hallucinated,
            "total_attribute_mismatch": total_attribute_mismatch,
            "total_deterministic_attribute_mismatch": total_deterministic_attribute_mismatch,
            "total_internal_field_issues": total_internal_field_issues,
            "total_permission_inversions": total_permission_inversions,
            "has_hallucination": total_hallucinated > 0,
            "has_missing": total_missing > 0,
            "has_attribute_mismatch": total_attribute_mismatch > 0,
        },
        "exit_reason": exit_reason,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # ShitPM 修复包 D：退出码语义
    # - 0: 无任何问题（exit_reason == "ok"）
    # - 1: 存在确定性冲突 / 可能遗漏 / 属性不一致（调用方按 exit_reason 处理）
    # - 2: 致命错误（design.md 不存在、JSON 损坏等，已在前面 sys.exit(2) 处理）
    if exit_reason != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
