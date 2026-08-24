#!/usr/bin/env python3
"""Prototype 与 Design 的分层事实一致性检查。

脚本只裁决低误报、可稳定抽取的事实：显式 data-* 锚点和路由注册表。
业务语义、动态渲染、权限、流程和主观视觉质量必须由后续审查完成。
"""

from __future__ import annotations

import argparse
import html.parser
import json
import re
import sys
from pathlib import Path
from typing import Any

from shared_md import load_sibling



EXCLUDED_DIRS = {"dist", "node_modules", "prototype-p0"}
ENTITY_TYPES = ("page", "block", "field", "operation", "state")
CLASSIFICATION_TYPES = (
    "deterministic_conflicts",
    "possible_omissions",
    "needs_semantic_judgment",
)


def _empty_classification() -> dict[str, list[dict[str, Any]]]:
    return {key: [] for key in CLASSIFICATION_TYPES}


def _fatal(message: str, source: dict[str, Any] | None = None) -> int:
    result: dict[str, Any] = {
        "ok": False,
        "source": source or {},
        "classification": _empty_classification(),
        "summary": {key: 0 for key in CLASSIFICATION_TYPES},
        "exit_reason": "fatal_input_error",
        "error": message,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 2


def _item(
    code: str,
    message: str,
    *,
    entity_type: str | None = None,
    name: str | None = None,
    source: str | None = None,
    path: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {"code": code, "message": message}
    for key, item in (("entity_type", entity_type), ("name", name), ("source", source), ("path", path)):
        if item is not None:
            value[key] = item
    if extra:
        value.update(extra)
    return value


class AnchorParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: dict[str, list[dict[str, Any]]] = {key: [] for key in ENTITY_TYPES}
        self.buttons: list[dict[str, Any]] = []
        self.hidden = 0
        self._button_stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value for key, value in attrs if value}
        if tag in {"script", "style", "template"}:
            self.hidden += 1
        if self.hidden:
            return
        for key, entity_type in (
            ("data-page", "page"),
            ("data-block", "block"),
            ("data-section", "block"),
            ("data-field", "field"),
            ("data-operation", "operation"),
            ("data-state", "state"),
        ):
            if values.get(key):
                self.anchors[entity_type].append({"name": values[key].strip(), "attribute": key})
        if tag == "button":
            self._button_stack.append({"operation": values.get("data-operation"), "text": []})

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.hidden or tag != "button":
            return
        values = {key: value for key, value in attrs if value}
        if not values.get("data-operation"):
            self.buttons.append({"text": values.get("aria-label") or values.get("title") or "未命名按钮"})

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self._button_stack and not self.hidden:
            button = self._button_stack.pop()
            if not button["operation"]:
                self.buttons.append({"text": " ".join(button["text"]).strip()})
        if tag in {"script", "style", "template"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if self.hidden:
            return
        for button in self._button_stack:
            button["text"].append(data)


def _record_anchor(anchors: dict[str, list[dict[str, Any]]], entity_type: str, name: str, source: str) -> None:
    if name:
        anchors[entity_type].append({"name": name.strip(), "attribute": f"data-{entity_type}", "source": source})


def _strip_js_strings_and_comments(text: str) -> str:
    """保留 JSX 标签及其属性，移除 JS 字符串、模板字面量和注释。

    Prototype 锚点只从真实 JSX/HTML 标签属性中提取。字符串中的 HTML
    模板不能作为事实锚点，否则示例文案或隐藏内容会制造确定性冲突。
    """
    output: list[str] = []
    state = "normal"
    in_tag = False
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if state == "line_comment":
            output.append("\n" if char == "\n" else " " )
            if char == "\n":
                state = "normal"
            index += 1
            continue
        if state == "block_comment":
            output.append("\n" if char == "\n" else " " )
            if char == "*" and next_char == "/":
                output.append(" " )
                index += 2
                state = "normal"
                continue
            index += 1
            continue
        if state in {"single_quote", "double_quote", "template"}:
            if escaped:
                output.append("\n" if char == "\n" else " " )
                escaped = False
            elif char == "\\":
                output.append(" " )
                escaped = True
            elif (state == "single_quote" and char == "'") or (state == "double_quote" and char == '"') or (state == "template" and char == "`"):
                output.append(" " )
                state = "normal"
            else:
                output.append("\n" if char == "\n" else " " )
            index += 1
            continue
        if char == "/" and next_char == "/":
            output.extend([" ", " "])
            state = "line_comment"
            index += 2
            continue
        if char == "/" and next_char == "*":
            output.extend([" ", " "])
            state = "block_comment"
            index += 2
            continue
        if char == "<" and re.match(r"/?[A-Za-z]", text[index + 1:]):
            in_tag = True
            output.append(char)
            index += 1
            continue
        if char == ">" and in_tag:
            in_tag = False
            output.append(char)
            index += 1
            continue
        if char in {"'", '"', "`"} and not in_tag:
            state = {"'": "single_quote", '"': "double_quote", "`": "template"}[char]
            output.append(" " )
            index += 1
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _attribute_value(attributes: str, name: str) -> str | None:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*(['\"])(.*?)\1", attributes, flags=re.S)
    return match.group(2).strip() if match else None


def _iter_object_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    stack: list[int] = []
    state = "normal"
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if state == "line_comment":
            if char == "\n":
                state = "normal"
            index += 1
            continue
        if state == "block_comment":
            if char == "*" and next_char == "/":
                state = "normal"
                index += 2
                continue
            index += 1
            continue
        if state in {"single_quote", "double_quote", "template"}:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif (state == "single_quote" and char == "'") or (state == "double_quote" and char == '"') or (state == "template" and char == "`"):
                state = "normal"
            index += 1
            continue
        if char == "/" and next_char == "/":
            state = "line_comment"
            index += 2
            continue
        if char == "/" and next_char == "*":
            state = "block_comment"
            index += 2
            continue
        if char in {"'", '"', "`"}:
            state = {"'": "single_quote", '"': "double_quote", "`": "template"}[char]
        elif char == "{":
            stack.append(index)
        elif char == "}" and stack:
            start = stack.pop()
            blocks.append(text[start:index + 1])
        index += 1
    return blocks


def _scan_source(root: Path, source_root: Path | None = None) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[str]]:
    anchors: dict[str, list[dict[str, Any]]] = {key: [] for key in ENTITY_TYPES}
    buttons: list[dict[str, Any]] = []
    files: list[str] = []
    if source_root is None:
        source_root = root / "output" / "prototype" / "src"
    if not source_root.is_dir():
        raise FileNotFoundError(f"Prototype 源码目录不存在: {source_root}")
    source_paths = [
        path for path in sorted(source_root.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in {".html", ".js", ".jsx", ".mjs", ".ts", ".tsx"}
        and not any(part in EXCLUDED_DIRS for part in path.parts)
    ]
    if not source_paths:
        raise FileNotFoundError("Prototype 源码目录中没有可检查的源码文件")
    for path in source_paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        relative = path.relative_to(root).as_posix()
        files.append(relative)
        if path.suffix.lower() == ".html":
            parser = AnchorParser()
            parser.feed(text)
            for entity_type, values in parser.anchors.items():
                for value in values:
                    value["source"] = relative
                    anchors[entity_type].append(value)
            buttons.extend({**button, "source": relative} for button in parser.buttons)
            continue
        clean = _strip_js_strings_and_comments(text)
        for attribute, entity_type in (
            ("data-page", "page"),
            ("data-block", "block"),
            ("data-section", "block"),
            ("data-field", "field"),
            ("data-operation", "operation"),
            ("data-state", "state"),
        ):
            pattern = rf"{re.escape(attribute)}\s*=\s*['\"]([^'\"]+)['\"]"
            for match in re.finditer(pattern, clean):
                _record_anchor(anchors, entity_type, match.group(1), relative)
        for match in re.finditer(r"<button\b([^>]*?)/>", clean, flags=re.S | re.I):
            attributes = match.group(1)
            if not re.search(r"\bdata-operation\s*=", attributes):
                buttons.append({"text": _attribute_value(attributes, "aria-label") or _attribute_value(attributes, "title") or "未命名按钮", "source": relative})
        for match in re.finditer(r"<button\b([^>]*)>(.*?)</button\s*>", clean, flags=re.S | re.I):
            attributes, body = match.groups()
            if not re.search(r"data-operation\s*=", attributes):
                text_value = re.sub(r"<[^>]+>", " ", body)
                buttons.append({"text": re.sub(r"\s+", " ", text_value).strip(), "source": relative})
    if not files:
        raise FileNotFoundError("Prototype 源码文件均不可读")
    return anchors, buttons, files


def _parse_routes(path: Path, root: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"路由注册表不存在: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"路由注册表无法读取: {path}: {exc}") from exc
    routes: list[dict[str, Any]] = []
    for block in _iter_object_blocks(text):
        match = re.search(r"\bpath\s*:\s*(['\"])(.*?)\1", block, flags=re.S)
        if not match:
            continue
        def field(name: str) -> str | None:
            found = re.search(rf"\b{name}\s*:\s*(['\"])(.*?)\1", block, flags=re.S)
            return found.group(2).strip() if found else None

        component = re.search(r"\bcomponent\s*:\s*([A-Za-z_$][\w$]*)", block)
        element = re.search(r"\belement\s*:\s*<([A-Za-z_$][\w$]*)\b", block)
        routes.append({
            "path": match.group(2).strip(),
            "title": field("title"),
            "module": field("module"),
            "component": component.group(1) if component else (element.group(1) if element else None),
            "placeholder": field("placeholder"),
            "source": path.relative_to(root).as_posix(),
        })
    if not routes:
        raise ValueError(f"路由注册表未发现 path 登记项: {path}")
    return routes


def _load_verified_index(root: Path) -> tuple[dict[str, Any] | None, str | None, bool]:
    index_path = root / ".workflow" / "runtime" / "context" / "design" / "index" / "design-index.json"
    if not index_path.is_file():
        return None, f"Design 索引不存在: {index_path}", False
    return load_sibling("design-index.py", "design_index_for_proto").load_verified_index(root)


def _names(index: dict[str, Any], entity_type: str) -> list[str]:
    key = f"{entity_type}s"
    return sorted({
        str(item.get("name", "")).strip()
        for item in index.get(key, [])
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    })


def _unique_anchors(anchors: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    result: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for entity_type, values in anchors.items():
        result[entity_type] = {}
        for value in values:
            result[entity_type].setdefault(value["name"], []).append(value)
    return result


def _component_exists(component: str | None, scanned_files: list[str]) -> bool:
    if not component:
        return False
    return any(Path(source).stem.lower() == component.lower() for source in scanned_files)


def _run(root: Path, prototype_src: Path | None = None, design_manifest: Path | None = None) -> tuple[dict[str, Any], int]:
    proto_src = (prototype_src or (root / "output" / "prototype" / "src")).resolve()
    manifest_path = (design_manifest or (root / "output" / "design" / "设计集清单.json")).resolve()
    source = {
        "design_manifest": manifest_path.relative_to(root).as_posix() if manifest_path.is_relative_to(root) else str(manifest_path),
        "design_index": ".workflow/runtime/context/design/index/design-index.json",
        "prototype_source": proto_src.relative_to(root).as_posix() + "/**/*.{html,js,jsx,mjs,ts,tsx}",
        "routes": (proto_src / "routes.jsx").relative_to(root).as_posix() if (proto_src / "routes.jsx").is_relative_to(root) else str(proto_src / "routes.jsx"),
        "excluded_dirs": sorted(EXCLUDED_DIRS),
    }
    if not manifest_path.is_file():
        _fatal(f"设计集清单不存在: {manifest_path}", source)
        return {}, 2
    try:
        json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fatal(f"设计集清单无法解析: {manifest_path}: {exc}", source)
        return {}, 2
    try:
        index, index_error, index_from_file = _load_verified_index(root)
    except Exception as exc:
        _fatal(f"Design Index 无法验证: {type(exc).__name__}: {exc}", source)
        return {}, 2
    if index is None or index_error:
        _fatal(index_error or "Design Index 无法验证", source)
        return {}, 2
    source["design_index_from_file"] = index_from_file
    try:
        anchors, buttons, scanned_files = _scan_source(root, proto_src)
        routes = _parse_routes(proto_src / "routes.jsx", root)
    except (OSError, UnicodeDecodeError, ValueError, FileNotFoundError) as exc:
        _fatal(str(exc), source)
        return {}, 2

    classification = _empty_classification()
    indexed = _unique_anchors(anchors)
    expected = {entity_type: _names(index, entity_type) for entity_type in ENTITY_TYPES}
    expected_sets = {entity_type: set(names) for entity_type, names in expected.items()}

    matched_pages: set[str] = set()
    unresolved_routes: list[dict[str, Any]] = []
    for route in routes:
        if route["path"] == "*":
            continue
        title = route.get("title")
        if title in expected_sets["page"]:
            matched_pages.add(title)
        elif _component_exists(route.get("component"), scanned_files) or not title:
            unresolved_routes.append(route)
            classification["possible_omissions"].append(_item(
                "route_page_identity_unresolved",
                f"路由“{title or route['path']}”未能仅凭登记项与 Design 页面精确对账，需结合组件和运行时判断",
                entity_type="page", name=title or route["path"], source=route["source"], path=route["path"],
                extra={"module": route.get("module"), "component": route.get("component")},
            ))
        else:
            classification["deterministic_conflicts"].append(_item(
                "unregistered_route",
                f"路由“{title or route['path']}”未登记在 Design 页面索引中，且没有可确认的源码组件",
                entity_type="page", name=title or route["path"], source=route["source"], path=route["path"],
                extra={"module": route.get("module"), "component": route.get("component")},
            ))
        if title in expected_sets["page"] and (route.get("component") == "Placeholder" or route.get("placeholder")):
            classification["possible_omissions"].append(_item(
                "placeholder_route",
                f"页面“{title}”有路由登记，但组件明确为占位实现，需逐项核对 Design 承接程度",
                entity_type="page", name=title, source=route["source"], path=route["path"],
            ))

    unmatched_pages = [page_name for page_name in expected["page"] if page_name not in matched_pages]
    for page_name in unmatched_pages[len(unresolved_routes):]:
            classification["possible_omissions"].append(_item(
                "design_page_without_route",
                f"Design 页面“{page_name}”未找到可确认的真实路由登记",
                entity_type="page", name=page_name, source="Design Index",
            ))

    for entity_type in ENTITY_TYPES:
        for anchor_name, values in indexed[entity_type].items():
            if anchor_name not in expected_sets[entity_type]:
                classification["deterministic_conflicts"].append(_item(
                    "unknown_explicit_anchor",
                    f"显式 {entity_type} 锚点“{anchor_name}”不在 Design Index 中",
                    entity_type=entity_type, name=anchor_name, source=values[0].get("source"),
                    extra={"attribute": values[0].get("attribute")},
                ))

    for entity_type in ENTITY_TYPES:
        for name in expected[entity_type]:
            if name in indexed[entity_type]:
                continue
            if entity_type == "state":
                classification["needs_semantic_judgment"].append(_item(
                    "state_without_explicit_anchor",
                    f"Design 状态“{name}”未发现稳定 data-state 锚点，可能由运行时状态或组合表达承接",
                    entity_type=entity_type, name=name, source="Design Index",
                ))
            else:
                classification["possible_omissions"].append(_item(
                    "entity_without_explicit_anchor",
                    f"Design {entity_type}“{name}”未发现稳定显式事实锚点，需结合源码和运行时逐项判断",
                    entity_type=entity_type, name=name, source="Design Index",
                ))

    for button in buttons:
        classification["needs_semantic_judgment"].append(_item(
            "unanchored_button",
            "发现未绑定 data-operation 的按钮，不能仅凭按钮文案判断其是否为 Design 授权操作",
            entity_type="operation", name=button.get("text") or "未命名按钮", source=button.get("source"),
        ))
    classification["needs_semantic_judgment"].append(_item(
        "semantic_scope_not_static",
        "权限、数据范围、流程前置条件、复杂状态转换和动态渲染不由本脚本裁决",
        source="Prototype 一致性检查边界",
    ))

    summary = {key: len(classification[key]) for key in CLASSIFICATION_TYPES}
    if summary["deterministic_conflicts"]:
        exit_reason, exit_code = "deterministic_conflict", 1
    elif summary["possible_omissions"]:
        exit_reason, exit_code = "possible_omission", 0
    elif summary["needs_semantic_judgment"]:
        exit_reason, exit_code = "needs_semantic_judgment", 0
    else:
        exit_reason, exit_code = "no_static_conflict", 0
    return {
        "ok": not bool(summary["deterministic_conflicts"]),
        "source": {**source, "scanned_files": scanned_files},
        "classification": classification,
        "summary": summary,
        "exit_reason": exit_reason,
    }, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Prototype Design 分层一致性检查（全量入口）")
    parser.add_argument("--project-root", required=True, help="项目根目录")
    parser.add_argument("--prototype-src", type=Path, default=None,
                        help="覆盖 Prototype 源码目录（默认 <project-root>/output/prototype/src）")
    parser.add_argument("--design-manifest", type=Path, default=None,
                        help="覆盖设计集清单路径（默认 <project-root>/output/design/设计集清单.json）")
    args = parser.parse_args()
    try:
        result, code = _run(
            Path(args.project_root).resolve(),
            prototype_src=(Path(args.prototype_src).resolve() if args.prototype_src else None),
            design_manifest=(Path(args.design_manifest).resolve() if args.design_manifest else None),
        )
    except Exception as exc:
        return _fatal(f"Prototype 一致性检查无法执行: {type(exc).__name__}: {exc}")
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
