#!/usr/bin/env python3
"""prd-consistency-check.py — PRD 与 design 确定性结构对比（ShitPM: 直接读人读稿，多模板兼容）

ShitPM 变更：
- 不再依赖 .workflow/metadata/design/ 下的 metadata 文件。
- 直接读取 output/design/design.md 和 output/prd/prd.md，从人读稿中提取实体做集合对比。
- 复用 stage-prep.py 的 generate_design_metadata 函数从 design.md 提取实体（不写入 metadata 文件）。
- 多模板兼容：支持业务模块内分散字段、系统全景页面映射和旧模板章节。
- 只做确定性提取和集合对比，不做语义判断。
- 可靠结构事实（字段属性、内部字段交付、明确权限允许/禁止反转）由脚本检查；复杂业务语义仍由 Review 判断。

退出码：
- 0: 无明确冲突；可能遗漏和需要语义判断的分类仍会输出，或 skipped（Prototype-only + --allow-no-prd）
- 1: 发现 deterministic_conflict，调用方必须修正后重新检查
- 2: 致命错误（design.md 或 prd.md 不存在等）

用法：
  python prd-consistency-check.py --project-root .

处理约定：
- 输出分类区分确定性冲突、可能遗漏和需要语义判断，供调用方逐项阅读。
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
# 页面展示/请求过程状态：不属于业务状态机，不得判为业务状态幻觉。
# 只有在 Design 明确把同类词定义为业务状态时，才需要人工核对表达口径。
PROCESS_OR_DISPLAY_STATE_MARKERS = frozenset({
    "保存失败", "已保存", "已加载", "未保存", "部分数据缺失",
    "加载中", "加载失败", "实时更新中", "网络较慢", "离线缓存", "拉流失败",
})

_FIELD_SPLIT_RE = re.compile(r"[、，,；;/｜|]+")
_ACTION_FRAGMENT_RE = re.compile(
    r"回退|退回|回到|重新|撤回|修改后|保存后|发送后|删除后|新增后|可修改|重新提交|继续处理|再提交"
)


def _clean_object_name(name: str) -> str:
    """从章节标题提取对象名：去编号前缀、去括号补充说明、去尾缀'对象/表'。"""
    if not name:
        return ""
    text = strip_heading_number(name)
    text = re.sub(r"[（(][^）)]*[）)]", "", text)
    text = text.replace(" ", "").strip()
    for suffix in ("对象", "表"):
        if text.endswith(suffix) and len(text) > len(suffix):
            text = text[:-len(suffix)]
    return text


def _normalize_field_title(title: str) -> str:
    """归一化字段名：去空格、去括号内容，用于匹配拼写差异（如'报告 ID'/'报告ID'）。"""
    text = re.sub(r"[（(][^）)]*[）)]", "", str(title or ""))
    return re.sub(r"\s+", "", text).strip()


def _split_field_tokens(raw: str) -> list:
    """拆分合并字段名（如'反馈人/回复人'→['反馈人','回复人']）。"""
    if not raw:
        return []
    parts = _FIELD_SPLIT_RE.split(str(raw).replace("\n", "、"))
    tokens = []
    for part in parts:
        token = part.strip().strip("`")
        if token and token not in ("—", "-"):
            tokens.append(token)
    return tokens


def _split_state_tokens(raw: str) -> list:
    """拆分状态单元格或箭头片段中的组合值，并清理标注和动作残留。"""
    if not raw:
        return []
    text = str(raw).strip().strip("`")
    # 去掉括号注释（如'已上报告（设定上报告标记）'→'已上报告'）
    text = re.sub(r"[（(][^）)]*[）)]", "", text)
    tokens = []
    for part in _FIELD_SPLIT_RE.split(text):
        token = part.strip().strip("`").strip("。；;，,、")
        if not token:
            continue
        if token in NON_CONCRETE_STATE_NAMES:
            continue
        if re.match(r'^[A-Z]\[', token) or token.startswith("|") or token.endswith("]"):
            continue
        if any(ch in token for ch in ("-->", "---", "==>", "~~", ">>", "<<")):
            continue
        if _ACTION_FRAGMENT_RE.search(token):
            continue
        # 过滤版本号等带数字小数的片段（如 V1.0→V2.0 递增说明），避免误当状态
        if re.search(r"\d+\.\d+", token):
            continue
        if len(token) > 12:
            continue
        tokens.append(token)
    return tokens


SECTION_ALIASES = {
    "详细需求说明": ["详细需求说明", "详细需求", "需求说明", "详细需求规格", "需求详细说明"],
    "数据字典": ["数据字典", "字段定义", "字段清单", "字段列表", "数据项定义", "数据与字段定义"],
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
        headings, ["详细需求说明", "数据字典", "字段定义", "字段清单", "数据与字段定义"]
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
            if "字段" not in header_text:
                continue
            name_idx = _idx(headers, ("字段",), ("字段权限",))
            type_idx = _idx(headers, ("类型",))
            description_idx = _idx(headers, ("说明", "含义", "用途"))
            # 新结构允许字段按对象或页面分散定义；旧 PRD 的局部字段表可能没有单独的“类型”列，
            # 只要仍有字段名和含义/说明列，就按字段集合读取，类型等价性留给人工判断。
            if name_idx is None or (type_idx is None and description_idx is None):
                continue
            required_idx = _idx(headers, ("必填",))
            constraint_idx = _idx(headers, ("取值约束", "约束", "规则", "枚举"))
            length_idx = _idx(headers, ("长度",))
            default_idx = _idx(headers, ("默认值", "默认"))
            format_idx = _idx(headers, ("格式",))
            source_idx = _idx(headers, ("业务来源", "来源"))

            object_name = _clean_object_name(table.get("section_title", ""))
            for row in table["rows"]:
                if not row:
                    continue
                raw_name = _cell(row, name_idx)
                if not raw_name or raw_name in ("---", "字段"):
                    continue
                name_tokens = _split_field_tokens(raw_name)
                if not name_tokens:
                    continue
                merged = len(name_tokens) > 1
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
                    # 兼容新模板把枚举值内联在"类型/取值"列：枚举：a、b 或 枚举(a、b)
                    # 只有明确的枚举声明才从类型列解析，避免合并类型单元格误判。
                    if _looks_like_enum_declaration(field_type):
                        enum_values = _parse_enum_values(field_type)
                    if not enum_values:
                        enum_values = _parse_enum_values(constraint_text)
                    if not enum_values:
                        enum_values = _parse_enum_values(description)
                for name in name_tokens:
                    record = {
                        "name": name,
                        "object": object_name,
                        "line": table.get("line_offset"),
                        "type": field_type,
                        "required": required,
                        "has_required_column": required_idx is not None,
                        "constraints": constraint_text,
                        "length": length,
                        "default": default,
                        "format": field_format,
                        "source": source,
                        "description": description,
                        "combined_text": combined_text,
                        "enum_values": enum_values,
                    }
                    if merged:
                        record["merged_split"] = True
                        record["raw_name"] = raw_name
                    fields.append(record)

    # 新结构允许字段表分散在多个业务模块、对象和阶段；只要表头明确为字段/类型，就合并读取。
    # 页面映射、权限和验收等天然表格不会同时具备这两个表头，因此不会被误当字段。
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

    def _add_page(name, ignore_blacklist=False):
        name = clean_page_title(name).strip()
        if not name:
            return
        if not ignore_blacklist and name in blacklist:
            return
        if name not in seen:
            seen.add(name)
            pages.append(name)

    # 新结构：总体说明中的页面清单是页面身份的确定性落点。
    # 只读取“页面清单”章节，避免把角色权限矩阵中的“页面”列误识别为页面。
    mapping_ranges = _find_multiple_section_ranges(headings, ["页面清单", "页面与终端映射"])
    mapping_tables = _tables_in_ranges(parse_tables_with_context(content, headings), mapping_ranges)
    if mapping_tables:
        for table in mapping_tables:
            headers = table.get("headers", [])
            if not headers or not any("页面" in h or "入口" in h for h in headers):
                continue
            page_idx = next((i for i, h in enumerate(headers) if "页面" in h or "入口" in h), None)
            if page_idx is None:
                continue
            for row in table.get("rows", []):
                if page_idx >= len(row):
                    continue
                value = row[page_idx].strip()
                if value and value not in {"页面/入口", "页面", "入口", "---"}:
                    # 页面清单是页面身份的确定性落点：即使与章节同名（如"数据字典"），
                    # 也按真实页面处理，不再被章节黑名单误过滤。
                    _add_page(value, ignore_blacklist=True)
        # 新结构的映射表是页面身份的唯一权威来源，不再继续扫描正文中的粗体动作标题。
        return pages
    else:
        # 旧模板兼容：无新结构映射章节时，保留原有全文扫描逻辑。
        for table in parse_tables_with_context(content, headings):
            headers = table.get("headers", [])
            if not headers or not any("页面" in h or "入口" in h for h in headers):
                continue
            page_idx = next((i for i, h in enumerate(headers) if "页面" in h or "入口" in h), None)
            if page_idx is None:
                continue
            for row in table.get("rows", []):
                if page_idx >= len(row):
                    continue
                value = row[page_idx].strip()
                if value and value not in {"页面/入口", "页面", "入口", "---"}:
                    _add_page(value)

    # 候选章节：仅页面说明类章节（不再含“详细需求说明”，避免子模块标题误判为页面）
    candidate_ranges = _find_multiple_section_ranges(
        headings, ["页面说明", "页面清单", "页面列表", "页面规划", "页面目录"]
    )

    # 格式 1: 粗体块页面名 **N.N.N 页面名**
    page_bold_pattern = re.compile(r'^\*\*(\d+(?:\.\d+)+)\s+(.+?)\*\*\s*$')
    # 格式 2: ### page-N 页面名
    page_legacy_pattern = re.compile(r'^#+\s+page[-_]?(\d+)\s+(.+?)\s*$', re.IGNORECASE)
    # 格式 3: ### N.N 页面名
    page_numbered_pattern = re.compile(r'^#+\s+(\d+\.\d+(?:\.\d+)*)\s+(.+?)\s*$')

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

        # 新结构：带终端标识的粗体页面名，例如 **现场处置（移动端）**。
        m = re.match(r'^\*\*(.+?(?:管理端|移动端|PC端|Web端|APP|App|页面|列表|详情|看板).+?)\*\*\s*$', stripped)
        if m and "动作" not in m.group(1):
            _add_page(m.group(1))
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
    2. 状态机/状态清单表格：表头含"状态"，并含"触发动作/进入条件/下一状态/含义/规则"之一
    """
    # 新结构允许每个业务闭环就近放置“状态与规则/状态与业务规则”，也可能使用
    # “状态机”子标题；逐个收集这些标题的范围，避免漏掉管理端与移动端的状态表。
    candidate_ranges = []
    state_heading_prefixes = ("状态与规则", "状态与业务规则", "状态机", "状态定义", "状态流转")
    for heading in headings:
        title = strip_heading_number(heading["title"])
        if not title.startswith(state_heading_prefixes):
            continue
        end = None
        for next_heading in headings:
            if next_heading["line"] > heading["line"] and next_heading["level"] <= heading["level"]:
                end = next_heading["line"]
                break
        candidate_ranges.append((heading["line"], end, heading["level"]))
    if not candidate_ranges:
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

        # 格式 1: 状态机/状态清单表格。读取“状态”和“下一状态”列，
        # 组合值（如“启用/停用”）按枚举集合拆分，避免整体当作单一状态。
        for table in _tables_in_ranges(tables, candidate_ranges):
            headers = table.get("headers", [])
            if not headers:
                continue
            header_text = "|".join(headers)
            if "状态" not in header_text or not any(
                marker in header_text for marker in ("触发动作", "进入条件", "下一状态", "含义", "规则")
            ):
                continue
            state_cols = [i for i, h in enumerate(headers) if h.strip() in ("状态", "展示状态", "下一状态")]
            for row in table["rows"]:
                for col_idx in state_cols:
                    if col_idx < len(row) and row[col_idx]:
                        for token in _split_state_tokens(row[col_idx]):
                            _add_state(token)

        # 格式 2: 同章节内的箭头/列表状态表达（如“审计问题：待定性 → 已上报告”）。
        # 无论是否存在状态表都扫描，避免遗漏仅以箭头表达的状态；动作残留片段会被过滤。
        for line in ranges_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("<!--") or stripped.startswith("-->"):
                continue
            if stripped.startswith("|"):
                continue
            if "→" not in stripped and "->" not in stripped:
                continue
            if any(ui_word in stripped for ui_word in ("点击", "跳转", "打开", "弹出", "返回", "进入页面")):
                continue
            arrow = "→" if "→" in stripped else "->"
            for part in stripped.split(arrow):
                part = re.sub(r'^[^：:]*[：:]', '', part).strip()
                for token in _split_state_tokens(part):
                    _add_state(token)

    # 策略 2: 候选章节未找到，降级为全文扫描
    if not states:
        for table in tables:
            headers = table.get("headers", [])
            if not headers:
                continue
            header_text = "|".join(headers)
            if "状态" not in header_text or not any(
                marker in header_text for marker in ("触发动作", "进入条件", "下一状态", "含义", "规则")
            ):
                continue
            state_cols = [i for i, h in enumerate(headers) if h.strip() in ("状态", "展示状态", "下一状态")]
            for row in table["rows"]:
                for col_idx in state_cols:
                    if col_idx < len(row) and row[col_idx]:
                        for token in _split_state_tokens(row[col_idx]):
                            _add_state(token)

        if not states:
            for line in content_clean.split("\n"):
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("<!--") or stripped.startswith("-->"):
                    continue
                if stripped.startswith("|"):
                    continue
                if "→" in stripped or "->" in stripped:
                    if any(ui_word in stripped for ui_word in ("点击", "跳转", "打开", "弹出", "返回", "进入页面")):
                        continue
                    arrow = "→" if "→" in stripped else "->"
                    for part in stripped.split(arrow):
                        part = re.sub(r'^[^：:]*[：:]', '', part).strip()
                        for token in _split_state_tokens(part):
                            _add_state(token)

    return states


def extract_prd_state_enum_values(tables: list) -> list:
    """从字段定义表提取状态类字段的枚举值（如“签署状态｜待签署/已签署/已过期”）。

    只读取字段名含“状态”的字段行，用于识别以字段枚举形式交付的状态，
    不把页面展示标签误当成状态机转换。Design 与 PRD 字段表共用此解析。
    """
    values = []
    seen = set()
    for table in tables:
        headers = table.get("headers", [])
        if not headers:
            continue
        header_text = "|".join(headers)
        if "字段" not in header_text:
            continue
        name_idx = next((i for i, h in enumerate(headers) if "字段" in h and "字段权限" not in h), None)
        if name_idx is None:
            continue
        type_idx = next((i for i, h in enumerate(headers) if "类型" in h or "取值" in h), None)
        constraint_idx = next((i for i, h in enumerate(headers) if "约束" in h or "规则" in h or "枚举" in h), None)
        for row in table["rows"]:
            if name_idx >= len(row):
                continue
            name = row[name_idx].strip()
            if "状态" not in name:
                continue
            raw = ""
            if type_idx is not None and type_idx < len(row):
                raw = row[type_idx]
            if not _parse_enum_values(raw) and constraint_idx is not None and constraint_idx < len(row):
                raw = row[constraint_idx]
            for value in _parse_enum_values(raw):
                if value not in seen:
                    seen.add(value)
                    values.append(value)
    return values


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
    """归一化类型字符串以便比较：去空格、转小写。

    兼容"类型/取值"合并列（枚举：a、b 或 枚举(a、b)）：比较时只保留类型名，
    避免把内联枚举值误判为类型差异。
    """
    if not type_str:
        return ""
    text = str(type_str)
    if re.match(r"枚举\s*[：:（(]", text):
        text = "枚举"
    return re.sub(r"\s+", "", text).lower()


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


def _normalize_enum_value(value: str) -> str:
    """压缩枚举值内部空白并转小写，避免「10年」与「10 年」被判为不一致。"""
    return re.sub(r"\s+", "", str(value).strip()).lower()


def _attribute_present_in_prd(design_value, prd_value) -> bool:
    """只比较独立列或已解析的标签值，避免被其他属性中的同词误判为已交付。"""
    design_norm = _normalize_scalar(design_value)
    if not design_norm:
        return True
    return _normalize_scalar(prd_value) == design_norm


def _looks_like_enum_declaration(raw: str) -> bool:
    """判断单元格是否为明确的枚举声明（如“枚举：a、b”“枚举(a、b)”）。

    避免把“文件/字符串/枚举/字符串”这类合并类型单元格误解析成枚举值列表。
    """
    text = str(raw or "").strip()
    return bool(re.search(r"(?:枚举(?:值)?|取值)\s*[：:]", text)) or text.startswith("枚举")


def compare_field_attributes(
    design_fields: list,
    prd_fields: list,
    design_title_to_id: dict,
    fuzzy_fn=None,
    design_field_objects: list = None,
) -> list:
    """对比 matched 字段的可确定属性。

    type 仍可能存在等价别名，单独标记为需语义判断；其余明确属性缺失或差异
    均可由结构化字段表可靠证明。同名字段（如多个对象的“状态”）优先按对象
    上下文区分，无法区分时归入语义判断，不直接判定冲突。
    """
    design_items = []
    for field in (design_field_objects if design_field_objects is not None else design_fields):
        if not isinstance(field, dict) or "title" not in field:
            continue
        attrs = field.get("attributes", {})
        design_items.append({
            "title": field["title"],
            "title_norm": _normalize_field_title(field["title"]),
            "object": field.get("object", ""),
            "type": attrs.get("数据类型", ""),
            "required": attrs.get("必填"),
            "length": attrs.get("长度", ""),
            "default": attrs.get("默认值", ""),
            "enum_values": _parse_enum_values(attrs.get("枚举值", "")),
            "format": attrs.get("格式", ""),
            "source": attrs.get("业务来源", ""),
        })

    def _find_design(prd_name: str, prd_object: str):
        norm = _normalize_field_title(prd_name)
        exact = [d for d in design_items if d["title"] == prd_name or d["title_norm"] == norm]
        fuzzy = []
        if not exact and fuzzy_fn:
            for d in design_items:
                if fuzzy_fn(prd_name, {d["title"]: d["title"]}) == d["title"]:
                    fuzzy.append(d)
        candidates = exact or fuzzy
        if not candidates:
            return None, "no_match"
        if len(candidates) == 1:
            return candidates[0], "unique"
        # 同名字段：优先按对象上下文区分（如“年度计划”的“状态”与“审批流程实例”的“状态”）
        obj_key = _clean_object_name(prd_object)
        by_object = [
            d for d in candidates
            if d["object"] and obj_key and (obj_key == d["object"] or obj_key in d["object"] or d["object"] in obj_key)
        ]
        if len(by_object) == 1:
            return by_object[0], "by_object"
        return None, "ambiguous"

    mismatches = []
    merged_attr_skipped = 0
    matched_pairs = set()
    for prd_field in prd_fields:
        if not isinstance(prd_field, dict) or "name" not in prd_field:
            continue
        if prd_field.get("merged_split"):
            # 合并字段行（如“相关附件/附件名称/附件类型/上传附件”）的类型和约束单元格
            # 混合了多个字段的属性，无法可靠做确定性属性对比，交给语义判断。
            merged_attr_skipped += 1
            continue
        prd_name = prd_field["name"]
        design, match_kind = _find_design(prd_name, prd_field.get("object", ""))
        if design is None:
            if match_kind == "ambiguous":
                mismatches.append({
                    "name": prd_name,
                    "object": prd_field.get("object", ""),
                    "mismatch_kinds": ["same_name_ambiguous"],
                    "deterministic": False,
                    "reason": "同名字段存在多个 Design 候选且无法按对象区分，需人工判断",
                })
            continue
        pair_key = (prd_name, design["title"])
        if pair_key in matched_pairs:
            continue
        matched_pairs.add(pair_key)

        mismatch_kinds = []
        d_type = _normalize_type(design["type"])
        p_type = _normalize_type(prd_field.get("type", ""))
        if d_type and p_type and d_type != p_type:
            mismatch_kinds.append("type")

        d_required = design["required"]
        p_required = prd_field.get("required")
        if d_required is not None and p_required is not None and d_required != p_required:
            mismatch_kinds.append("required")
        elif (
            d_required is not None
            and p_required is None
            and prd_field.get("has_required_column")
        ):
            # 字段表没有"必填"列时（新模板为"类型/取值|来源或约束|使用说明"四列），
            # 必填由写作规则要求用正文表达，结构上无法确定性证明缺失；
            # 不判 deterministic required_missing，避免"照模板写→误报"。
            mismatch_kinds.append("required_missing")

        for key in ("length", "default", "format", "source"):
            if not _attribute_present_in_prd(design[key], prd_field.get(key, "")):
                mismatch_kinds.append(key)

        d_enum = design["enum_values"]
        p_enum = prd_field.get("enum_values", [])
        d_enum_norm = [_normalize_enum_value(v) for v in d_enum]
        p_enum_norm = [_normalize_enum_value(v) for v in p_enum]
        if d_enum_norm != p_enum_norm and (d_enum_norm or p_enum_norm):
            mismatch_kinds.append("enum")

        if mismatch_kinds:
            # 枚举差异只有在两侧都解析出明确枚举集合时才是确定性问题；
            # 仅一侧有枚举（另一侧可能以正文或约束表达）时归入语义判断。
            both_enum_present = bool(d_enum and p_enum)
            deterministic_kinds = [
                kind for kind in mismatch_kinds
                if kind != "type" and not (kind == "enum" and not both_enum_present)
            ]
            mismatches.append({
                "name": prd_name,
                "object": prd_field.get("object", ""),
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
                "enum_missing": sorted(set(d_enum_norm) - set(p_enum_norm)),
                "enum_hallucinated": sorted(set(p_enum_norm) - set(d_enum_norm)),
            })
    return {"mismatches": mismatches, "merged_attr_skipped": merged_attr_skipped}


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


def _compare_field_sets(
    design_fields: list,
    prd_fields: list,
    design_title_to_id: dict,
    fuzzy_fn=None,
    design_context_titles: set = None,
) -> dict:
    """对比 Design 与 PRD 字段集合。

    与 compare_entities 的区别：
    - 字段名归一化（去空格/去括号），兼容“报告 ID”/“报告ID”等拼写差异；
    - 合并字段拆分后的碎片（如“报告 ID/编号”拆出的“编号”）若无 Design 匹配，
      归入 needs_semantic_judgment，而不是直接判定为确定性幻觉。
    """
    design_items = [
        {"title": f["title"], "norm": _normalize_field_title(f["title"])}
        for f in design_fields if isinstance(f, dict) and "title" in f
    ]
    prd_items = [
        {
            "name": f["name"],
            "norm": _normalize_field_title(f["name"]),
            "merged_split": bool(f.get("merged_split")),
        }
        for f in prd_fields if isinstance(f, dict) and "name" in f
    ]

    matched_design = set()
    matched_prd = set()
    for p in prd_items:
        matched = None
        if p["name"] in design_title_to_id:
            matched = p["name"]
        else:
            for d in design_items:
                if d["title"] == p["name"] or d["norm"] == p["norm"]:
                    matched = d["title"]
                    break
        if matched is None and fuzzy_fn:
            matched_id = fuzzy_fn(p["name"], design_title_to_id)
            if matched_id:
                for t, eid in design_title_to_id.items():
                    if eid == matched_id:
                        matched = t
                        break
        if matched:
            matched_design.add(matched)
            matched_prd.add(p["name"])

    missing = sorted({d["title"] for d in design_items} - matched_design)
    hallucinated = []
    merged_split_unmatched = []
    for p in prd_items:
        if p["name"] in matched_prd:
            continue
        if p["merged_split"]:
            merged_split_unmatched.append({"name": p["name"], "issue": "merged_split_unmatched"})
        else:
            hallucinated.append(p["name"])
    # 命名/引用变体（如“实例状态”对应 Design“状态”、“审批记录”对应 Design 对象）：
    # 归入语义判断，不直接判定为确定性幻觉。
    hallucinated_kept = []
    for name in hallucinated:
        norm = _normalize_field_title(name)
        if design_context_titles and (
            name in design_context_titles or norm in design_context_titles
        ):
            merged_split_unmatched.append({"name": name, "issue": "object_or_page_reference"})
        elif name.endswith("状态") and "状态" in design_title_to_id:
            merged_split_unmatched.append({"name": name, "issue": "state_name_variant"})
        else:
            hallucinated_kept.append(name)
    return {
        "missing": missing,
        "hallucinated": sorted(set(hallucinated_kept)),
        "matched_count": len(matched_design),
        "merged_split_unmatched": merged_split_unmatched,
    }


def _design_field_objects(project_root: Path, design_fields: list) -> list:
    """为 design_fields 补充所属对象（来自 design.md 字段表所在章节标题）。"""
    try:
        content = (project_root / "output" / "design" / "design.md").read_text(encoding="utf-8")
    except Exception:
        return []
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    line_to_object = {
        t["line_offset"]: _clean_object_name(t.get("section_title", ""))
        for t in tables
    }
    result = []
    for field in design_fields:
        if not isinstance(field, dict):
            continue
        item = dict(field)
        item["object"] = line_to_object.get(field.get("line"), "")
        result.append(item)
    return result


def _design_enum_state_values(project_root: Path) -> set:
    """从 design.md 字段表提取状态类字段的枚举值（Design 数据字典口径）。"""
    try:
        content = (project_root / "output" / "design" / "design.md").read_text(encoding="utf-8")
    except Exception:
        return set()
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    return set(extract_prd_state_enum_values(tables))


def _design_context_titles(project_root: Path) -> set:
    """收集 Design 的对象/章节标题，用于识别 PRD 字段名中的对象引用变体。"""
    try:
        content = (project_root / "output" / "design" / "design.md").read_text(encoding="utf-8")
    except Exception:
        return set()
    titles = set()
    for heading in parse_headings(content):
        clean = _clean_object_name(heading["title"])
        if clean:
            titles.add(clean)
    return titles


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
    # 去掉括号注释（如“车牌号（列表列）”“车辆类型（筛选条件）”）和全部空白/标点，
    # 使同一字段在不同页面或列表/筛选语境下的名称可归一化比较。
    value = re.sub(r"[（(][^）)]*[）)]", "", value)
    return re.sub(r"[\s，,；;。、：:]+", "", value).lower()


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
    # 页面/字段只按“名称”做确定比较，不再要求字段具备页面和区块位置：
    # - missing：Design 名称未在 PRD 正文任何位置出现（存在性候选，possible_omission）；
    # - hallucinated：PRD 页面标题/字段表名称不在 Design 索引名称集合中（确定性幻觉）。
    # Design 操作与 PRD 动作不做一对一名称匹配（动作组织由 LLM 按业务结果重组，属语义判断）。
    pages_expected = [item for item in expected if item["type"] == "page"]
    fields_expected = [item for item in expected if item["type"] == "field"]
    operations_expected = [item for item in expected if item["type"] == "operation"]
    normalized_content = re.sub(r"[\s，,；;。、：:（）()\"'“”]+", "", content).lower()
    expected_page_names = {_normalize_indexed_value(item["name"]) for item in pages_expected}
    expected_field_names = {_normalize_indexed_value(item["name"]) for item in fields_expected}

    page_missing = [
        item for item in pages_expected
        if _normalize_indexed_value(item["name"]) not in normalized_content
    ]
    field_missing = [
        item for item in fields_expected
        if _normalize_indexed_value(item["name"]) not in normalized_content
    ]
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    prd_pages = extract_prd_pages(content, headings)
    prd_fields = extract_prd_fields(headings, tables, content)
    page_hallucinated = [
        {"type": "page", "name": name}
        for name in sorted(set(prd_pages))
        if _normalize_indexed_value(name) not in expected_page_names
    ]
    # 字段幻觉只判定“完全无法对应”的名称；命名变体（进场时间/入场时间、占用车辆车牌号/车牌号、
    # 服务区 ID/服务区ID 等）与索引名称共享 ≥2 字公共子串，归入语义判断，不直接判确定性幻觉。
    # 对象级字段表（无页面/区块位置）不再因缺少页面位置被判幻觉。
    field_hallucinated = []
    field_name_variants = []
    expected_names_list = sorted(expected_field_names)
    expected_bigrams = {
        name[j:j + 2]
        for name in expected_names_list
        for j in range(len(name) - 1)
        if len(name) >= 2
    }
    for field in prd_fields:
        if not field.get("name"):
            continue
        norm = _normalize_indexed_value(field["name"])
        if norm in expected_field_names:
            continue
        prd_bigrams = {norm[j:j + 2] for j in range(len(norm) - 1) if len(norm) >= 2}
        if any(en in norm or norm in en for en in expected_field_names) or (
            prd_bigrams & expected_bigrams
        ):
            field_name_variants.append({
                "type": "field", "name": field["name"], "issue": "name_variant",
                "note": "与 Design 索引字段名存在变体或包含关系，需语义判断是否为同一字段",
            })
        else:
            field_hallucinated.append({"type": "field", "name": field["name"]})

    # 新格式的明确属性（来源/必填/展示条件）分散在页面上下文中，对象级字段表无法可靠逐字比较，
    # 一律归语义判断；旧格式项目的属性冲突由 legacy compare_field_attributes 负责。
    attribute_mismatch = []
    return {
        "enabled": bool(expected),
        "expected_count": len(pages_expected) + len(fields_expected) + len(operations_expected),
        "matched_count": len(expected) - len(page_missing) - len(field_missing),
        "missing": page_missing + field_missing,
        "hallucinated": page_hallucinated + field_hallucinated,
        "attribute_mismatch": attribute_mismatch,
        "field_name_variants": field_name_variants,
        "operations": {
            "expected_count": len(operations_expected),
            "matched_count": 0,
            "note": "Design 操作与 PRD 动作不做一对一名称匹配：动作是否完整承接需语义判断，由生成回读与 Review 负责。",
        },
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
    # ShitPM: 索引不可用时优雅降级为 legacy 模式，不阻塞一致性检查。
    design_index_from_file = False
    try:
        design_index_module, design_index, design_index_error, design_index_from_file = _load_verified_design_index(project_root)
    except Exception as exc:
        design_index = None
        design_index_error = str(exc)
    if design_index is None or design_index_error:
        # 索引编译失败（如旧格式/格式变体），降级为 legacy 模式
        indexed_result = {"enabled": False, "expected_count": 0, "matched_count": 0,
                          "missing": [], "hallucinated": [], "attribute_mismatch": []}
        indexed_active = False
    else:
        indexed_result = _compare_indexed_structure(design_index, content, design_index_module)
        indexed_active = indexed_result["enabled"]

    design_fields = design_data.get("fields", []) or []
    design_pages = design_data.get("pages", []) or []
    design_states = design_data.get("states", []) or []
    # 旧 Design 表格可能使用“进入条件/下一状态”而不是 stage-prep
    # 旧版要求的“触发动作”列；此时从确认版 Design 的状态章节回读状态名。
    if not design_states:
        design_path = project_root / "output" / "design" / "design.md"
        with open(design_path, encoding="utf-8") as design_file:
            design_content = design_file.read()
        design_headings = parse_headings(design_content)
        design_tables = parse_tables_with_context(design_content, design_headings)
        design_state_names = extract_prd_states(design_content, design_headings, design_tables)
        design_states = [{"title": name, "id": name} for name in design_state_names]
    design_permissions = design_data.get("permissions", []) or []
    design_modules_raw = design_data.get("modules", []) or []
    # ShitPM：读取 Design 中标记为“非页面落点字段”的内部/审计字段，用于验证 PRD 是否完整交付
    design_non_page_fields = design_data.get("non_page_fields", []) or []

    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)

    # 构建 title → id 映射
    field_title_to_id = {f["title"]: f.get("id", f["title"]) for f in design_fields if isinstance(f, dict) and "title" in f}
    page_title_to_id = {p["title"]: p.get("id", p["title"]) for p in design_pages if isinstance(p, dict) and "title" in p}

    # 从 PRD 提取实体（多模板兼容）
    prd_fields = extract_prd_fields(headings, tables, content)
    prd_pages = extract_prd_pages(content, headings)
    prd_states = extract_prd_states(content, headings, tables)
    prd_perm_pages = extract_prd_permission_pages(headings, tables, content)

    # PRD 是研发交付物：Design 的页面字段和非页面内部字段都必须出现。
    # 非页面字段无需虚构页面落点，但必须在字段表保留来源和内部用途。

    # “任意状态”等是状态机通配/占位行，不是需要在 PRD 中单独交付的具体状态。
    # Design“下一状态”列的组合值（如“停留中、数据异常、离场异常”）先拆分，
    # 避免把组合单元格整体当作单一状态要求 PRD 逐字复刻。
    design_deliverable_states = []
    seen_states: set[str] = set()
    for state in design_states:
        if not isinstance(state, dict) or not state.get("title"):
            continue
        if state["title"] in NON_CONCRETE_STATE_NAMES:
            continue
        for token in _split_state_tokens(state["title"]):
            if token and token not in seen_states:
                seen_states.add(token)
                design_deliverable_states.append(token)
    state_title_to_id = {t: t for t in design_deliverable_states}

    design_field_objects = _design_field_objects(project_root, design_fields)
    if indexed_active:
        # 新格式 Design 以索引为权威：页面/字段存在性、名称级幻觉和显式来源属性
        # 都由 _compare_indexed_structure 负责；stage-prep 的旧格式提取对新结构不可靠，
        # 因此不在此分支混用 legacy 字段/页面集合比较。
        field_result = {
            "missing": [], "hallucinated": [], "attribute_mismatch": [],
            "enum_mismatch": [], "deterministic_attribute_mismatch": [],
            "internal_field_issues": [], "merged_split_unmatched": [], "merged_attr_skipped": 0,
        }
        page_result = {"missing": [], "hallucinated": [], "matched_count": len(prd_pages)}
    else:
        field_result = _compare_field_sets(
            design_fields, prd_fields, field_title_to_id, fuzzy_field_match,
            design_context_titles=_design_context_titles(project_root),
        )
        attr_result = compare_field_attributes(
            design_fields, prd_fields, field_title_to_id, fuzzy_field_match,
            design_field_objects=design_field_objects,
        )
        field_result["attribute_mismatch"] = attr_result["mismatches"]
        field_result["merged_attr_skipped"] = attr_result["merged_attr_skipped"]
        field_result["enum_mismatch"] = [
            item for item in field_result["attribute_mismatch"]
            if item.get("deterministic") and (item.get("enum_missing") or item.get("enum_hallucinated"))
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

    state_result = compare_entities(
        design_deliverable_states,
        prd_states, state_title_to_id, fuzzy_state_match,
    )
    # 状态补充识别：
    # - Design 状态以字段枚举形式交付（如“问题挂销号状态｜已挂号/已销号”）不算遗漏；
    # - PRD 状态机/状态表中出现的状态若来自 Design 数据字典枚举（如“启用/停用”），
    #   属表达口径差异，归入语义判断，不直接判定为确定性幻觉。
    prd_enum_states = extract_prd_state_enum_values(tables)
    design_enum_state_values = _design_enum_state_values(project_root)
    state_result["missing"] = [s for s in state_result["missing"] if s not in prd_enum_states]
    state_via_enum = []
    state_via_process = []
    kept_hallucinated = []
    for s in state_result["hallucinated"]:
        if s in design_enum_state_values:
            state_via_enum.append({
                "state": s,
                "issue": "design_enum_state",
                "note": "PRD 以状态机/状态表表达 Design 数据字典枚举，需人工确认表达口径",
            })
        elif s in PROCESS_OR_DISPLAY_STATE_MARKERS:
            state_via_process.append({
                "state": s,
                "issue": "process_or_display_state",
                "note": "页面展示/请求过程状态，不判为业务状态幻觉；只在 Design 定义为业务状态时再人工核对",
            })
        else:
            kept_hallucinated.append(s)
    state_result["hallucinated"] = kept_hallucinated
    state_result["state_via_enum"] = state_via_enum
    state_result["state_via_process"] = state_via_process
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

    # 权限提取为空时，missing/hallucinated 集合无意义（无法证明缺失或新增），
    # 全部标记为未评估，由人工验收，避免把解析失败当成权限不一致。
    permission_extracted = bool(prd_perm_pages or prd_perm_pairs or prd_roles)
    if not permission_extracted:
        perm_result = {"missing": [], "hallucinated": [], "matched_count": 0, "not_evaluated": True}
        perm_pair_result = {"missing": [], "hallucinated": [], "matched_count": 0, "not_evaluated": True}
        role_result = {"missing": [], "hallucinated": [], "matched_count": 0, "not_evaluated": True}
        permission_inversions = []

    # 业务闭环名称不必与 Design 菜单模块逐字相同；模块边界和完整性由 AI/Review 语义判断。
    # 仍保留模块字段，兼容旧调用方，但不以模块标题集合产生机器冲突。
    prd_modules = extract_prd_modules(headings, content)
    module_result = {"missing": [], "hallucinated": [], "matched_count": len(prd_modules), "semantic_only": True}

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
    # 合并字段拆分后无法匹配的碎片、状态以 Design 数据字典枚举形式表达的口径差异，
    # 都是解析层面的表达差异，归入语义判断，不当作确定性冲突。
    needs_semantic_judgment_items.extend(field_result.get("merged_split_unmatched", []))
    needs_semantic_judgment_items.extend(state_result.get("state_via_enum", []))
    needs_semantic_judgment_items.extend(state_result.get("state_via_process", []))
    needs_semantic_judgment_items.extend(indexed_result.get("field_name_variants", []))
    if indexed_result.get("operations"):
        needs_semantic_judgment_items.append({
            "issue": "operations_semantic",
            "note": indexed_result["operations"]["note"],
            "expected_count": indexed_result["operations"].get("expected_count"),
        })
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
            "hint": "字段类型等价性、同名字段对象归属、合并字段拆分碎片和状态枚举表达口径仍需语义判断；明确属性缺失和差异已归入确定性冲突。",
        },
    }

    # 权限解析为空时，明确给出“无法提取、需人工验收”信号，不显示为“权限一致”。
    permission_extracted = bool(
        prd_perm_pages or prd_perm_pairs or prd_roles
    )
    if permission_extracted:
        permission_evaluation = {
            "status": "extracted",
            "message": "权限内容已从 PRD 正文提取，仍需人工对照 Design 权限矩阵核对。",
        }
    else:
        permission_evaluation = {
            "status": "cannot_extract",
            "message": "权限无法从当前正文提取，需人工验收",
            "note": "解析结果为空不代表权限一致；不得将权限缺失视为通过。",
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
        "permission_evaluation": permission_evaluation,
        "roles": role_result,
        "modules": module_result,
        "design_index": {
            "used": indexed_active,
            "from_file": design_index_from_file,
            "path": ".workflow/runtime/context/design/index/design-index.json",
            "structure": indexed_result,
            "error": design_index_error if design_index is None else None,
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

    # 退出码只反映程序是否发现确定性冲突或发生致命运行错误。
    # possible_omission 和 needs_semantic_judgment 已在分类输出中保留，
    # 由 AI 对照 Design 判断，不能因为解析器不确定直接阻断。
    # - 0: ok / possible_omission / needs_semantic_judgment
    # - 1: deterministic_conflict
    # - 2: 致命错误（已在前面 sys.exit(2) 处理）
    if exit_reason == "deterministic_conflict":
        sys.exit(1)


if __name__ == "__main__":
    main()
