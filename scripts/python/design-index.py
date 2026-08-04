#!/usr/bin/env python3
"""从 output/design/design.md 确定性编译和检查 Design 结构索引。

索引是 Design 的只读派生物，不是产品事实源。编译不读取旧 metadata、运行状态或模型输出，
也不写入时间字段；相同的 design.md 必须得到相同的 JSON 内容。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


INDEX_RELATIVE_PATH = Path(".workflow/runtime/context/design/index/design-index.json")
SCHEMA_VERSION = "design-index/v1"

# 固定结构的必填属性。值为“无”或“不适用”时视为明确声明，不视为缺失。
REQUIRED_ATTRIBUTES = {
    "page": ("purpose", "roles", "entry_condition", "data_scope", "states"),
    "block": ("purpose",),
    "field": (
        "meaning",
        "source",
        "display_condition",
        "input_edit",
        "value_default",
        "interaction",
        "validation_feedback",
    ),
    "operation": (
        "roles",
        "availability",
        "confirmation",
        "success_result",
        "state_change",
        "failure_recovery",
        "destination",
    ),
}

ATTRIBUTE_ALIASES = {
    "purpose": ("目的", "用途", "主要任务", "页面目的", "区块目的"),
    "roles": ("角色", "适用角色", "操作人", "责任角色"),
    "entry_condition": ("进入条件", "前置条件", "入口条件"),
    "data_scope": ("数据范围", "可见范围", "可见数据范围"),
    "states": ("主要状态", "状态", "状态集合"),
    "meaning": ("业务含义", "含义", "字段含义"),
    "required": ("必填", "是否必填"),
    "type": ("类型", "数据类型"),
    "length": ("长度",),
    "source": ("来源", "业务来源", "数据来源", "字段来源"),
    "display_condition": ("展示条件", "显示条件", "可见条件"),
    "input_edit": ("输入编辑", "输入/编辑", "输入与编辑", "编辑方式", "是否可编辑"),
    "value_default": ("取值默认", "取值/默认", "取值与默认", "默认值"),
    "interaction": ("交互", "交互方式"),
    "validation_feedback": ("校验反馈", "校验与反馈", "校验", "反馈"),
    "availability": ("可用条件", "展示与可用条件", "使用条件", "执行条件"),
    "entry_source": ("入口/触发方式", "入口", "触发方式", "操作入口"),
    "input_fields": ("输入（字段级）", "输入", "输入字段", "输入构成"),
    "confirmation": ("确认", "确认方式", "二次确认"),
    "success_result": ("成功结果", "成功后的结果", "预期结果"),
    "state_change": ("状态变化", "数据与状态变化", "状态变更", "状态流转"),
    "failure_recovery": ("失败恢复", "失败与恢复", "失败处理", "异常恢复"),
    "destination": ("去向", "后续去向", "页面去向", "下一步去向"),
}

ENTITY_ALIASES = {
    "page": ("页面", "page"),
    "block": ("区块", "区域", "block", "section"),
    "field": ("字段", "field"),
    "operation": ("操作", "动作", "operation", "action"),
}

OPERATION_ONLY_ATTRIBUTES = {"entry_source", "input_fields", "availability", "confirmation", "success_result", "state_change", "failure_recovery", "destination"}

FIELD_TABLE_HEADERS = (
    "字段名称",
    "业务含义",
    "字段来源",
    "展示条件",
    "输入与编辑规则",
    "取值与默认规则",
    "交互方式",
    "校验与反馈",
)
FIELD_TABLE_ATTRIBUTE_KEYS = (
    "meaning",
    "source",
    "display_condition",
    "input_edit",
    "value_default",
    "interaction",
    "validation_feedback",
)
OPERATION_TABLE_HEADERS = (
    "操作",
    "适用角色",
    "入口/触发方式",
    "输入（字段级）",
    "展示与可用条件",
    "是否二次确认",
    "成功结果",
    "数据与状态变化",
    "失败与恢复",
    "后续去向",
)
OPERATION_TABLE_ATTRIBUTE_KEYS = (
    "roles",
    "entry_source",
    "input_fields",
    "availability",
    "confirmation",
    "success_result",
    "state_change",
    "failure_recovery",
    "destination",
)
COMBINED_FIELD_PATTERN = re.compile(r"[/／、]")


def index_path(project_root: Path) -> Path:
    return project_root / INDEX_RELATIVE_PATH


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _clean_text(value: str) -> str:
    value = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    value = re.sub(r"[`*_]", "", value)
    return value.strip()


def _is_explicit_empty(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip() == ""


def _normalize_label(value: str) -> str:
    value = _clean_text(value).strip().strip("| ")
    value = re.sub(r"^[一二三四五六七八九十0-9]+[、.．)]\s*", "", value)
    return value.strip()


def _entity_heading(title: str) -> tuple[str | None, str | None]:
    """识别“页面：名称”这类固定实体标题，不把章节容器当成实体。"""
    title = _normalize_label(title)
    if title == "页面操作":
        # 新格式将页面级操作集中在独立区块中；索引内部仍复用 page → block → operation 树。
        return "block", "页面操作"
    for entity_type, aliases in ENTITY_ALIASES.items():
        for alias in aliases:
            match = re.match(rf"^{re.escape(alias)}\s*(?:[:：\-—]\s*|\s+)(.+)$", title, re.IGNORECASE)
            if match:
                name = _normalize_label(match.group(1))
                if name and name not in {"定义", "清单", "列表", "说明", "与字段落点"}:
                    return entity_type, name
    return None, None


def _canonical_attribute(label: str) -> str | None:
    label = _normalize_label(label)
    label = re.sub(r"[：:]$", "", label).strip()
    for canonical, aliases in ATTRIBUTE_ALIASES.items():
        if label in aliases:
            return canonical
    return None


def _split_heading_lines(content: str) -> list[dict[str, Any]]:
    headings = []
    for line_no, line in enumerate(content.splitlines(), 1):
        match = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        entity_type, name = _entity_heading(match.group(2))
        headings.append({
            "line": line_no,
            "level": len(match.group(1)),
            "title": _clean_text(match.group(2)),
            "entity_type": entity_type,
            "name": name,
        })
    return headings


def _heading_scope_end(headings: list[dict[str, Any]], index: int, total_lines: int) -> int:
    current = headings[index]
    for next_heading in headings[index + 1:]:
        if next_heading["level"] <= current["level"]:
            return next_heading["line"] - 1
    return total_lines


def _split_table_row(raw_line: str) -> list[str]:
    line = raw_line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        return []
    cells = re.split(r"(?<!\\)\|", line[1:-1])
    return [_clean_text(cell.replace(r"\|", "|")).strip() for cell in cells]


def _is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _table_after_heading(
    lines: list[str],
    headings: list[dict[str, Any]],
    heading_index: int,
) -> tuple[int | None, list[str], list[tuple[int, list[str]]]]:
    """读取标题直属范围内的第一张有效 Markdown 表。

    表前允许出现说明文字、空行和 HTML 注释；只有找到“表头行 + 分隔行”
    这一对有效行后才认定表格开始。这样不会因为模型在表格前增加一句
    引导语而把整张表静默丢弃。
    """
    start = headings[heading_index]["line"]
    end = _heading_scope_end(headings, heading_index, len(lines))
    table_start: int | None = None
    invalid_start: int | None = None
    invalid_headers: list[str] = []
    for line_no in range(start + 1, end + 1):
        raw = lines[line_no - 1].strip()
        if not raw or raw.startswith("<!--"):
            continue
        if not raw.startswith("|") or not raw.endswith("|"):
            continue
        headers = _split_table_row(raw)
        if invalid_start is None:
            invalid_start = line_no
            invalid_headers = headers
        separator_line = line_no + 1
        if separator_line > end:
            continue
        separator_raw = lines[separator_line - 1].strip()
        separator = _split_table_row(separator_raw)
        if headers and _is_table_separator(separator) and len(separator) == len(headers):
            table_start = line_no
            break
    if table_start is None:
        if invalid_start is None:
            return None, [], []
        return invalid_start, invalid_headers, []
    headers = _split_table_row(lines[table_start - 1])
    rows: list[tuple[int, list[str]]] = []
    for line_no in range(table_start + 2, end + 1):
        raw = lines[line_no - 1].strip()
        if not raw.startswith("|") or not raw.endswith("|"):
            break
        rows.append((line_no, _split_table_row(raw)))
    return table_start, headers, rows


def _scoped_parent(
    nodes: list[dict[str, Any]],
    entity_type: str,
    line_no: int,
) -> dict[str, Any] | None:
    candidates = [
        node
        for node in nodes
        if node["type"] == entity_type
        and node["line"] < line_no
        and node.get("scope_end", line_no) >= line_no
    ]
    return max(candidates, key=lambda item: (item["level"], item["line"]), default=None)


def _new_table_node(
    entity_type: str,
    name: str,
    line_no: int,
    parent: dict[str, Any],
    attributes: dict[str, str],
) -> dict[str, Any]:
    path = parent["path"] + [name]
    return {
        "type": entity_type,
        "name": name,
        "line": line_no,
        "level": parent["level"] + 1,
        "scope_end": line_no,
        "parent": parent,
        "path": path,
        "id": _make_id(entity_type, path),
        "attributes": attributes,
        "source_format": "table",
    }


def _attribute_from_table_row(cells: list[str]) -> tuple[str | None, str | None]:
    if len(cells) < 2:
        return None, None
    key = _canonical_attribute(cells[0])
    if key is None:
        return None, None
    return key, " | ".join(_clean_text(cell) for cell in cells[1:]).strip()


def _extract_attributes(lines: list[str]) -> dict[str, str]:
    attributes: dict[str, str] = {}
    in_table = False
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("|") and line.count("|") >= 2:
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if all(re.fullmatch(r"[-: ]+", cell or " ") for cell in cells):
                in_table = True
                continue
            key, value = _attribute_from_table_row(cells)
            if key:
                attributes.setdefault(key, value or "")
                in_table = True
                continue
        # 允许“属性：值”、项目符号和加粗属性名三种写法。
        match = re.match(r"^(?:[-*+]\s+)?(?:\*\*)?([^:：|]+?)(?:\*\*)?\s*[:：]\s*(.*)$", line)
        if match:
            key = _canonical_attribute(match.group(1))
            if key:
                attributes.setdefault(key, _clean_text(match.group(2)))
                continue
        # 对“属性 | 内容”表头后的行，继续按两列解析。
        if in_table and line.startswith("|"):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            key, value = _attribute_from_table_row(cells)
            if key:
                attributes.setdefault(key, value or "")
    return attributes


def _segment_for_heading(lines: list[str], headings: list[dict[str, Any]], index: int) -> list[str]:
    current = headings[index]
    start = current["line"]
    end = len(lines) + 1
    for next_heading in headings[index + 1:]:
        if next_heading["level"] <= current["level"]:
            end = next_heading["line"]
            break
    # 只拿当前标题下、首个子标题之前的直接正文，避免把子实体属性串进来。
    for next_heading in headings[index + 1:]:
        if next_heading["level"] > current["level"]:
            end = min(end, next_heading["line"])
            break
    return lines[start:end - 1]


def _nearest_parent(entity_nodes: list[dict[str, Any]], index: int, level: int) -> dict[str, Any] | None:
    for node in reversed(entity_nodes[:index]):
        if node["level"] < level:
            return node
    return None


def _make_id(entity_type: str, path: list[str]) -> str:
    return f"{entity_type}:{'/'.join(path)}"


def _add_error(errors: list[dict[str, Any]], code: str, message: str, node: dict[str, Any] | None = None) -> None:
    item: dict[str, Any] = {"code": code, "message": message}
    if node:
        item["line"] = node.get("line")
        item["path"] = node.get("path")
    errors.append(item)


def _node_public(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node["id"],
        "name": node["name"],
        "line": node["line"],
        "attributes": dict(sorted(node.get("attributes", {}).items())),
    }


def _parse_design(content: str, design_sha256: str, require_current_format: bool = False) -> dict[str, Any]:
    lines = content.splitlines()
    headings = _split_heading_lines(content)
    entity_nodes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for index, heading in enumerate(headings):
        entity_type = heading.get("entity_type")
        if not entity_type:
            continue
        parent = _nearest_parent(entity_nodes, len(entity_nodes), heading["level"])
        node = {
            "type": entity_type,
            "name": heading["name"],
            "line": heading["line"],
            "level": heading["level"],
            "scope_end": _heading_scope_end(headings, index, len(lines)),
            "parent": parent,
            "attributes": _extract_attributes(_segment_for_heading(lines, headings, index)),
            "source_format": "heading",
        }
        if parent:
            path = parent["path"] + [node["name"]]
        else:
            path = [node["name"]]
        node["path"] = path
        node["id"] = _make_id(entity_type, path)
        entity_nodes.append(node)

    table_nodes: list[dict[str, Any]] = []
    for heading_index, heading in enumerate(headings):
        title = _normalize_label(heading["title"])
        if title not in {"字段表", "操作表"}:
            continue
        entity_type = "field" if title == "字段表" else "operation"
        expected_headers = FIELD_TABLE_HEADERS if entity_type == "field" else OPERATION_TABLE_HEADERS
        attribute_keys = FIELD_TABLE_ATTRIBUTE_KEYS if entity_type == "field" else OPERATION_TABLE_ATTRIBUTE_KEYS
        invalid_code = "invalid_field_table_headers" if entity_type == "field" else "invalid_operation_table_headers"
        table_line, headers, rows = _table_after_heading(lines, headings, heading_index)
        marker = {"line": table_line or heading["line"], "path": [heading["title"]]}
        if tuple(headers) != expected_headers:
            actual = " | ".join(headers) if headers else "未找到有效表格"
            _add_error(errors, invalid_code, f"{title}表头必须严格为：{' | '.join(expected_headers)}；实际为：{actual}", marker)
            continue
        parent = _scoped_parent(entity_nodes, "block", heading["line"])
        if parent is None:
            _add_error(errors, "item_without_block", f"{title}必须位于页面区块下", marker)
            continue
        for line_no, cells in rows:
            row_marker = {"line": line_no, "path": parent["path"]}
            if not any(cells):
                continue
            if len(cells) != len(expected_headers):
                _add_error(
                    errors,
                    "invalid_table_row",
                    f"{title}第 {line_no} 行列数应为 {len(expected_headers)}，实际为 {len(cells)}",
                    row_marker,
                )
                continue
            name = _normalize_label(cells[0])
            if not name:
                _add_error(errors, "missing_entity_name", f"{entity_type} 名称不能为空", row_marker)
                continue
            attributes = {key: cells[position + 1] for position, key in enumerate(attribute_keys)}
            table_nodes.append(_new_table_node(entity_type, name, line_no, parent, attributes))

    # ShitPM: 兼容无"字段表"/"操作表"显式标题但表格直接跟在区块后的格式
    # 当显式标题方式未解析到任何字段或操作时，遍历区块标题查找直属表格
    if not table_nodes:
        for heading_index, heading in enumerate(headings):
            entity_type_h = heading.get("entity_type")
            if entity_type_h != "block":
                continue
            table_line, headers, rows = _table_after_heading(lines, headings, heading_index)
            if not headers:
                continue
            if tuple(headers) == FIELD_TABLE_HEADERS:
                table_entity_type = "field"
                attr_keys = FIELD_TABLE_ATTRIBUTE_KEYS
            elif tuple(headers) == OPERATION_TABLE_HEADERS:
                table_entity_type = "operation"
                attr_keys = OPERATION_TABLE_ATTRIBUTE_KEYS
            else:
                continue
            parent = _scoped_parent(entity_nodes, "block", heading["line"])
            if parent is None:
                # 直接从 entity_nodes 中找该区块
                parent = next(
                    (n for n in entity_nodes
                     if n["type"] == "block" and n["line"] == heading["line"]),
                    None,
                )
            if parent is None:
                continue
            for line_no, cells in rows:
                if not any(cells):
                    continue
                if len(cells) != len(headers):
                    _add_error(
                        errors,
                        "invalid_table_row",
                        f"区块“{heading['name']}”第 {line_no} 行列数应为 {len(headers)}，实际为 {len(cells)}",
                        {"line": line_no, "path": parent["path"]},
                    )
                    continue
                name = _normalize_label(cells[0])
                if not name:
                    _add_error(
                        errors,
                        "missing_entity_name",
                        f"{table_entity_type} 名称不能为空",
                        {"line": line_no, "path": parent["path"]},
                    )
                    continue
                attributes = {key: cells[pos + 1] for pos, key in enumerate(attr_keys)}
                table_nodes.append(
                    _new_table_node(table_entity_type, name, line_no, parent, attributes)
                )

    entity_nodes.extend(table_nodes)

    if not entity_nodes:
        _add_error(
            errors,
            "unsupported_format",
            "design.md 未发现固定的页面/区块/字段/操作标题结构；不能编译为 Design v1 索引，请由下游兼容解析器处理旧格式",
        )

    if require_current_format:
        for node in entity_nodes:
            if node["type"] == "field" and node.get("source_format") != "table":
                _add_error(errors, "outdated_field_format", "当前格式要求字段写入区块字段表，不再使用逐字段标题", node)
            if node["type"] == "operation" and node.get("source_format") != "table":
                _add_error(errors, "outdated_operation_format", "当前格式要求操作写入页面操作表，不再使用逐操作标题", node)

    # 校验层级，并将节点挂到固定的页面 → 区块 → 字段/操作树。
    pages: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    seen_by_scope: dict[tuple[str, str, str], dict[str, Any]] = {}

    for node in entity_nodes:
        parent = node.get("parent")
        if node["type"] == "page":
            if parent:
                _add_error(errors, "page_nested", "页面不能嵌套在其他实体下", node)
            item = {"id": node["id"], "name": node["name"], "line": node["line"], "attributes": node["attributes"], "blocks": []}
            pages.append(item)
        elif node["type"] == "block":
            if not parent or parent["type"] != "page":
                _add_error(errors, "block_without_page", "区块必须直接位于页面下", node)
            item = {"id": node["id"], "name": node["name"], "line": node["line"], "attributes": node["attributes"], "page_id": parent["id"] if parent and parent["type"] == "page" else None, "fields": [], "operations": []}
            blocks.append(item)
            if parent and parent["type"] == "page":
                page = next((candidate for candidate in pages if candidate["id"] == parent["id"]), None)
                if page:
                    page["blocks"].append(item)
        elif node["type"] in {"field", "operation"}:
            if not parent or parent["type"] != "block":
                _add_error(errors, "item_without_block", f"{node['type']} 必须位于区块下", node)
            item = {
                "id": node["id"],
                "name": node["name"],
                "line": node["line"],
                "attributes": node["attributes"],
                "page_id": _ancestor_id(parent, "page"),
                "block_id": parent["id"] if parent and parent["type"] == "block" else None,
            }
            if node["type"] == "field":
                fields.append(item)
                if COMBINED_FIELD_PATTERN.search(node["name"]):
                    _add_error(errors, "combined_field_name", f"字段“{node['name']}”疑似合并了多个字段，必须拆成一行一个字段", node)
                if any(key in node["attributes"] for key in OPERATION_ONLY_ATTRIBUTES):
                    _add_error(errors, "operation_as_field", "字段包含操作专属属性，疑似将操作错误写成字段", node)
            else:
                operations.append(item)
            if parent and parent["type"] == "block":
                block = next((candidate for candidate in blocks if candidate["id"] == parent["id"]), None)
                if block:
                    block["fields" if node["type"] == "field" else "operations"].append(item)
        else:
            continue
        scope_id = parent["id"] if parent else "root"
        duplicate_key = (node["type"], scope_id, node["name"])
        if duplicate_key in seen_by_scope:
            previous = seen_by_scope[duplicate_key]
            _add_error(errors, "duplicate_entity", f"同一范围重复定义{node['type']}“{node['name']}”", node)
            if previous.get("attributes") != node.get("attributes"):
                _add_error(errors, "semantic_conflict", f"同名{node['type']}在同一范围的属性不一致", node)
        else:
            seen_by_scope[duplicate_key] = node

        required = REQUIRED_ATTRIBUTES[node["type"]]
        missing = [key for key in required if _is_explicit_empty(node["attributes"].get(key))]
        if missing:
            _add_error(errors, "missing_attribute", f"{node['type']} 缺少必填属性: {', '.join(missing)}", node)

    for page in pages:
        if not page["blocks"]:
            _add_error(errors, "page_without_block", f"页面“{page['name']}”没有正式区块", {"line": page["line"], "path": [page["name"]]})
    for block in blocks:
        if not block["fields"] and not block["operations"]:
            page_name = next((page["name"] for page in pages if page["id"] == block.get("page_id")), "")
            _add_error(errors, "block_without_items", f"区块“{block['name']}”没有字段或操作", {"line": block["line"], "path": [page_name, block["name"]]})

    summary_present = False
    summary_names: list[str] = []
    for heading_index, heading in enumerate(headings):
        if not _normalize_label(heading["title"]).startswith("页面清单"):
            continue
        summary_present = True
        table_line, headers, rows = _table_after_heading(lines, headings, heading_index)
        if "页面" not in headers:
            marker = {"line": table_line or heading["line"], "path": [heading["title"]]}
            _add_error(errors, "invalid_page_summary_table", "页面清单必须包含“页面”列", marker)
            continue
        page_column = headers.index("页面")
        for _, cells in rows:
            if len(cells) > page_column:
                name = _normalize_label(cells[page_column])
                if name:
                    summary_names.append(name)

    if summary_present:
        detail_names = [page["name"] for page in pages]
        for name in dict.fromkeys(summary_names):
            if name not in detail_names:
                _add_error(errors, "page_summary_missing_detail", f"页面清单中的“{name}”没有正式页面定义")
        for page in pages:
            if page["name"] not in summary_names:
                _add_error(errors, "page_detail_missing_summary", f"正式页面“{page['name']}”未出现在页面清单中", {"line": page["line"], "path": [page["name"]]})

    pages_public = []
    for page in pages:
        page_public = _node_public(page)
        page_public["blocks"] = []
        for block in page["blocks"]:
            block_public = _node_public(block)
            block_public["page_id"] = block["page_id"]
            block_public["fields"] = [_node_public(field) | {"page_id": field["page_id"], "block_id": field["block_id"]} for field in block["fields"]]
            block_public["operations"] = [_node_public(operation) | {"page_id": operation["page_id"], "block_id": operation["block_id"]} for operation in block["operations"]]
            page_public["blocks"].append(block_public)
        pages_public.append(page_public)

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_path": "output/design/design.md",
        "design_sha256": design_sha256,
        "pages": pages_public,
        "blocks": [_node_public(block) | {"page_id": block["page_id"]} for block in blocks],
        "fields": [_node_public(field) | {"page_id": field["page_id"], "block_id": field["block_id"]} for field in fields],
        "operations": [_node_public(operation) | {"page_id": operation["page_id"], "block_id": operation["block_id"]} for operation in operations],
        "states": _extract_states(pages),
        "errors": errors,
        "summary": {
            "pages": len(pages),
            "blocks": len(blocks),
            "fields": len(fields),
            "operations": len(operations),
            "errors": len(errors),
        },
    }


def _ancestor_id(node: dict[str, Any] | None, entity_type: str) -> str | None:
    current = node
    while current:
        if current.get("type") == entity_type:
            return current.get("id")
        current = current.get("parent")
    return None



def _extract_states(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    states = []
    seen = set()
    for page in pages:
        raw = page.get("attributes", {}).get("states", "")
        for name in re.split(r"[,，、/；;|]+", raw):
            name = name.strip()
            if not name or name in {"无", "无状态机", "不适用"} or name in seen:
                continue
            seen.add(name)
            states.append({"name": name, "line": page.get("line"), "page_id": page.get("id")})
    return states


def extract_document_entities(content: str) -> list[dict[str, Any]]:
    """提取下游文档中使用同一固定标题结构的实体，不执行 Design 必填校验。"""
    lines = content.splitlines()
    headings = _split_heading_lines(content)
    nodes: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        if not heading.get("entity_type"):
            continue
        parent = _nearest_parent(nodes, len(nodes), heading["level"])
        node = {
            "type": heading["entity_type"],
            "name": heading["name"],
            "line": heading["line"],
            "level": heading["level"],
            "attributes": _extract_attributes(_segment_for_heading(lines, headings, index)),
            "parent": parent,
        }
        node["page_name"] = _ancestor_name(parent, "page")
        node["block_name"] = _ancestor_name(parent, "block")
        nodes.append(node)
    return nodes


def _ancestor_name(node: dict[str, Any] | None, entity_type: str) -> str | None:
    current = node
    while current:
        if current.get("type") == entity_type:
            return current.get("name")
        current = current.get("parent")
    return None
def compile_index(project_root: Path, require_current_format: bool = False) -> dict[str, Any]:
    design_path = project_root / "output" / "design" / "design.md"
    if not design_path.is_file():
        raise FileNotFoundError(f"design.md 不存在: {design_path}")
    raw = design_path.read_bytes()
    content = raw.decode("utf-8")
    return _parse_design(content, _sha256(raw), require_current_format=require_current_format)


def _canonical_index(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_index(project_root: Path, data: dict[str, Any]) -> Path:
    target = index_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_canonical_index(data), encoding="utf-8")
    return target


def load_index(project_root: Path) -> dict[str, Any]:
    target = index_path(project_root)
    if not target.is_file():
        raise FileNotFoundError(f"Design 索引不存在: {target}")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Design 索引无法读取: {target}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Design 索引顶层必须是对象")
    return value


def validate_index(project_root: Path, stored: dict[str, Any] | None = None, require_current_format: bool = False) -> tuple[bool, dict[str, Any], str | None]:
    try:
        expected = compile_index(project_root, require_current_format=require_current_format)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return False, {}, str(exc)
    if stored is None:
        try:
            stored = load_index(project_root)
        except (OSError, ValueError) as exc:
            return False, expected, str(exc)
    if stored != expected:
        if stored.get("design_sha256") != expected.get("design_sha256"):
            reason = "Design 哈希不一致"
        else:
            reason = "索引内容与 design.md 的确定性编译结果不一致"
        return False, expected, reason
    if expected.get("errors"):
        if _is_unsupported_format(expected):
            return False, expected, "Design 索引无法编译（不支持的格式）"
        # 非致命错误（missing_attribute / block_without_items 等）不阻碍索引使用
        # 下游 _compare_indexed_structure 仍可从已解析实体中做有效对比
    return True, expected, None


def _is_unsupported_format(data: dict[str, Any] | None) -> bool:
    return bool(data and any(item.get("code") == "unsupported_format" for item in data.get("errors", []) if isinstance(item, dict)))


def load_verified_index(project_root: Path) -> tuple[dict[str, Any] | None, str | None, bool]:
    """下游读取入口：有索引时先校验；无索引时从 design.md 内存编译。

    返回 (index, error, from_file)。索引永远不能绕过 design.md 哈希和结构校验。
    """
    try:
        stored = load_index(project_root)
    except FileNotFoundError:
        try:
            compiled = compile_index(project_root)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            return None, str(exc), False
        if compiled.get("errors"):
            if _is_unsupported_format(compiled):
                return compiled, None, False
            # 非致命错误仍可使用已解析实体做对比
        return compiled, None, False
    except ValueError as exc:
        return None, str(exc), True
    valid, expected, reason = validate_index(project_root, stored)
    if not valid:
        if _is_unsupported_format(expected):
            return expected, None, True
        return None, reason, True
    return expected, None, True


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Design 索引编译与确定性检查")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("compile", "check"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--project-root", required=True)
        sub.add_argument("--require-current-format", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    if args.command == "compile":
        try:
            data = compile_index(root, require_current_format=args.require_current_format)
            target = write_index(root, data)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            _print_json({"ok": False, "command": "compile", "error": str(exc)})
            return 2
        result = {
            "ok": not bool(data["errors"]),
            "command": "compile",
            "index_path": str(target),
            "design_sha256": data["design_sha256"],
            "summary": data["summary"],
            "errors": data["errors"],
        }
        _print_json(result)
        return 0 if result["ok"] else 1

    try:
        stored = load_index(root)
    except (OSError, ValueError) as exc:
        _print_json({"ok": False, "command": "check", "error": str(exc)})
        return 2
    valid, expected, reason = validate_index(root, stored, require_current_format=args.require_current_format)
    result = {
        "ok": valid,
        "command": "check",
        "index_path": str(index_path(root)),
        "design_sha256": expected.get("design_sha256"),
        "summary": expected.get("summary", {}),
        "errors": expected.get("errors", []),
    }
    if reason:
        result["error"] = reason
    _print_json(result)
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
