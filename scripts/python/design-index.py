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

OPERATION_ONLY_ATTRIBUTES = {"availability", "confirmation", "success_result", "state_change", "failure_recovery", "destination"}


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


def _parse_design(content: str, design_sha256: str) -> dict[str, Any]:
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
            "parent": parent,
            "attributes": _extract_attributes(_segment_for_heading(lines, headings, index)),
        }
        if parent:
            path = parent["path"] + [node["name"]]
        else:
            path = [node["name"]]
        node["path"] = path
        node["id"] = _make_id(entity_type, path)
        entity_nodes.append(node)

    if not entity_nodes:
        _add_error(
            errors,
            "unsupported_format",
            "design.md 未发现固定的页面/区块/字段/操作标题结构；不能编译为 Design v1 索引，请由下游兼容解析器处理旧格式",
        )

    # 校验层级，并将节点挂到固定的页面 → 区块 → 字段/操作树。
    pages: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    seen_by_scope: dict[tuple[str, str, str], dict[str, Any]] = {}

    for node in entity_nodes:
        parent = node.get("parent")
        valid = True
        if node["type"] == "page":
            if parent:
                valid = False
                _add_error(errors, "page_nested", "页面不能嵌套在其他实体下", node)
            item = {"id": node["id"], "name": node["name"], "line": node["line"], "attributes": node["attributes"], "blocks": []}
            pages.append(item)
        elif node["type"] == "block":
            if not parent or parent["type"] != "page":
                valid = False
                _add_error(errors, "block_without_page", "区块必须直接位于页面下", node)
            item = {"id": node["id"], "name": node["name"], "line": node["line"], "attributes": node["attributes"], "page_id": parent["id"] if parent and parent["type"] == "page" else None, "fields": [], "operations": []}
            blocks.append(item)
            if parent and parent["type"] == "page":
                page = next((candidate for candidate in pages if candidate["id"] == parent["id"]), None)
                if page:
                    page["blocks"].append(item)
        elif node["type"] in {"field", "operation"}:
            if not parent or parent["type"] != "block":
                valid = False
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
def compile_index(project_root: Path) -> dict[str, Any]:
    design_path = project_root / "output" / "design" / "design.md"
    if not design_path.is_file():
        raise FileNotFoundError(f"design.md 不存在: {design_path}")
    raw = design_path.read_bytes()
    content = raw.decode("utf-8")
    return _parse_design(content, _sha256(raw))


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


def validate_index(project_root: Path, stored: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any], str | None]:
    try:
        expected = compile_index(project_root)
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
        return False, expected, "Design 索引解析失败"
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
            return None, "Design 索引解析失败", False
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
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    if args.command == "compile":
        try:
            data = compile_index(root)
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
    valid, expected, reason = validate_index(root, stored)
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
