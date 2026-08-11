#!/usr/bin/env python3
"""Prototype 与 Design 人读事实的确定性一致性检查。"""

import argparse
import html.parser
import importlib.util
import json
import re
import sys
from pathlib import Path


def _load_design_parser():
    path = Path(__file__).with_name("stage-prep.py")
    spec = importlib.util.spec_from_file_location("stage_prep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_design_index_module():
    path = Path(__file__).with_name("design-index.py")
    spec = importlib.util.spec_from_file_location("design_index", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VisibleTextParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
        self.candidates = []
        self.state_candidates = []
        self.explicit_entities = {"page": [], "block": [], "field": [], "operation": []}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "template"):
            self.hidden += 1
        for key in ("aria-label", "title", "placeholder", "value", "data-page", "data-route", "data-block", "data-section", "data-field", "data-operation"):
            if attrs.get(key):
                self.candidates.append(attrs[key])
        for key, entity_type in (("data-page", "page"), ("data-block", "block"), ("data-section", "block"), ("data-field", "field"), ("data-operation", "operation")):
            if attrs.get(key):
                self.explicit_entities[entity_type].append(attrs[key].strip())
        if attrs.get("data-state"):
            self.state_candidates.append(attrs["data-state"])

    def handle_endtag(self, tag):
        if tag in ("script", "style", "template") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


_EXCLUDED_DIRS = {"dist", "node_modules", "prototype-p0"}


def _scan_html(path: Path) -> tuple[list[str], list[str], dict[str, list[str]]]:
    parser = VisibleTextParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return [], [], {}
    return parser.parts + parser.candidates, parser.state_candidates, parser.explicit_entities


def _scan_jsx_text(text: str) -> tuple[list[str], list[str], dict[str, list[str]]]:
    """从 JSX/JS 源码提取人读文本线索：字符串字面量、JSX 文本节点、data-* 显式实体。"""
    parts: list[str] = []
    states: list[str] = []
    explicit: dict[str, list[str]] = {"page": [], "block": [], "field": [], "operation": []}
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    # 空字符串字面量会让引号配对错位（如 c4: '', c5: '' 把后续 "..." 吞掉），先归一为空格
    text = re.sub(r"''", " ", text)
    text = re.sub(r'""', " ", text)
    for key, entity_type in (
        ("data-page", "page"),
        ("data-block", "block"),
        ("data-section", "block"),
        ("data-field", "field"),
        ("data-operation", "operation"),
    ):
        for m in re.finditer(key + r'\s*=\s*["\']([^"\']+)["\']', text):
            explicit[entity_type].append(m.group(1).strip())
    for m in re.finditer(r'data-state\s*=\s*["\']([^"\']+)["\']', text):
        states.append(m.group(1).strip())
    # 同类型引号成对匹配，避免空串/撇号导致配对漂移
    for m in re.finditer(r'(["\'"])([^"\']{1,120})\1', text):
        value = m.group(2).strip()
        if value:
            parts.append(value)
    for m in re.finditer(r">\s*([^<>{}]+?)\s*<", text):
        value = re.sub(r"\s+", " ", m.group(1)).strip()
        if value and len(value) <= 120:
            parts.append(value)
    return parts, states, explicit


def _scan(root: Path) -> tuple[str, list[str], dict[str, list[str]]]:
    parts: list[str] = []
    states: list[str] = []
    explicit: dict[str, list[str]] = {"page": [], "block": [], "field": [], "operation": []}
    prototype_root = root / "output" / "prototype"
    if prototype_root.is_dir():
        for path in sorted(prototype_root.rglob("*.html")):
            if any(part in _EXCLUDED_DIRS for part in path.parts):
                continue
            p, s, e = _scan_html(path)
            parts.extend(p)
            states.extend(s)
            for entity_type, names in e.items():
                explicit[entity_type].extend(names)
        src_root = prototype_root / "src"
        if src_root.is_dir():
            for path in sorted(
                list(src_root.rglob("*.js")) + list(src_root.rglob("*.jsx")) + list(src_root.rglob("*.mjs"))
            ):
                if any(part in _EXCLUDED_DIRS for part in path.parts):
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                p, s, e = _scan_jsx_text(text)
                parts.extend(p)
                states.extend(s)
                for entity_type, names in e.items():
                    explicit[entity_type].extend(names)
    return "\n".join(parts), states, explicit


def _names(items):
    return sorted({item.get("title", "").strip() for item in items if isinstance(item, dict) and item.get("title")})


def _compare(expected, text):
    missing = [name for name in expected if name not in text]
    return {"expected": expected, "missing": missing, "matched_count": len(expected) - len(missing)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Prototype Design 一致性检查")
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    design_path = root / "output" / "design" / "design.md"
    prototype_root = root / "output" / "prototype"
    if not design_path.is_file():
        print(json.dumps({"ok": False, "error": "design.md 不存在"}, ensure_ascii=False))
        return 2
    if not prototype_root.is_dir() or not list(prototype_root.rglob("*.html")):
        print(json.dumps({"ok": False, "error": "prototype HTML 不存在"}, ensure_ascii=False))
        return 2
    design_text = design_path.read_text(encoding="utf-8")
    design = _load_design_parser().generate_design_metadata(design_text, "design", root)
    index_module = _load_design_index_module()
    index, index_error, index_from_file = index_module.load_verified_index(root)
    if index is None or index_error:
        print(json.dumps({"ok": False, "error": index_error or "Design 索引解析失败"}, ensure_ascii=False))
        return 2

    text, explicit_states, explicit_entities = _scan(root)
    indexed_active = bool(index.get("pages") or index.get("blocks") or index.get("fields") or index.get("operations"))
    if indexed_active:
        pages = _compare([item.get("name", "") for item in index.get("pages", [])], text)
        blocks = _compare([item.get("name", "") for item in index.get("blocks", [])], text)
        fields = _compare([item.get("name", "") for item in index.get("fields", [])], text)
        operations = _compare([item.get("name", "") for item in index.get("operations", [])], text)
        expected_explicit = {
            "page": set(pages["expected"]),
            "block": set(blocks["expected"]),
            "field": set(fields["expected"]),
            "operation": set(operations["expected"]),
        }
    else:
        pages = _compare(_names(design.get("pages", [])), text)
        blocks = {"expected": [], "missing": [], "matched_count": 0}
        fields = _compare(_names(design.get("fields", [])), text)
        operations = {"expected": [], "missing": [], "matched_count": 0}
        expected_explicit = {"page": set(pages["expected"]), "block": set(), "field": set(fields["expected"]), "operation": set()}

    index_hallucinated = {
        entity_type: sorted(set(names) - expected_explicit[entity_type])
        for entity_type, names in explicit_entities.items()
    }
    design_states = _names(design.get("states", []))
    indexed_states = [item.get("name", "") for item in index.get("states", []) if isinstance(item, dict)]
    states = _compare(indexed_states or design_states, text)
    design_state_names = set(states["expected"])
    states["hallucinated"] = sorted(set(explicit_states) - design_state_names)
    if states["hallucinated"]:
        states["ok"] = False

    total_missing = sum(len(item["missing"]) for item in (pages, blocks, fields, operations, states))
    total_hallucinated = len(states["hallucinated"]) + sum(len(values) for values in index_hallucinated.values())
    result = {
        "ok": not (total_missing or total_hallucinated),
        "source": {
            "design": "output/design/design.md",
            "design_index": {"path": ".workflow/runtime/context/design/index/design-index.json", "from_file": index_from_file},
            "prototype": "output/prototype/**/*.{html,js,jsx}（排除 dist/node_modules/prototype-p0）",
        },
        "pages": pages,
        "blocks": blocks,
        "fields": fields,
        "operations": operations,
        "states": states,
        "hallucinated": index_hallucinated,
        "summary": {"total_missing": total_missing, "total_hallucinated": total_hallucinated},
        "exit_reason": "deterministic_conflict" if total_hallucinated else ("ok" if not total_missing else "possible_omission"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
