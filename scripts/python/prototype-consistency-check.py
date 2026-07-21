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


class VisibleTextParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
        self.candidates = []
        self.state_candidates = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "template"):
            self.hidden += 1
        for key in ("aria-label", "title", "placeholder", "value", "data-page", "data-route"):
            if attrs.get(key):
                self.candidates.append(attrs[key])
        if attrs.get("data-state"):
            self.state_candidates.append(attrs["data-state"])

    def handle_endtag(self, tag):
        if tag in ("script", "style", "template") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def _scan(root: Path) -> tuple[str, list[str]]:
    parser = VisibleTextParser()
    for path in sorted((root / "output" / "prototype").rglob("*.html")):
        try:
            parser.feed(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return "\n".join(parser.parts + parser.candidates), parser.state_candidates


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
    design = _load_design_parser().generate_design_metadata(design_path.read_text(encoding="utf-8"), "design", root)
    text, explicit_states = _scan(root)
    fields = _compare(_names(design.get("fields", [])), text)
    pages = _compare(_names(design.get("pages", [])), text)
    states = _compare(_names(design.get("states", [])), text)
    design_state_names = set(states["expected"])
    states["hallucinated"] = sorted(set(explicit_states) - design_state_names)
    if states["hallucinated"]:
        states["ok"] = False
    result = {
        "ok": not (fields["missing"] or pages["missing"] or states["missing"] or states["hallucinated"]),
        "source": {"design": "output/design/design.md", "prototype": "output/prototype/**/*.html"},
        "pages": pages,
        "fields": fields,
        "states": states,
        "summary": {
            "total_missing": len(fields["missing"]) + len(pages["missing"]) + len(states["missing"]),
            "total_hallucinated": len(states["hallucinated"]),
        },
        "exit_reason": "deterministic_conflict" if states["hallucinated"] else ("ok" if not (fields["missing"] or pages["missing"] or states["missing"]) else "possible_omission"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
