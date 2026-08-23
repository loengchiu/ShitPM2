from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

_EXCLUDED_DIRS = {"dist", "node_modules", "prototype-p0"}
_JS_SUFFIXES = {".js", ".jsx", ".mjs"}


class PrototypeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[dict[str, str]] = []
        self.routes: list[str] = []
        self.actions: list[dict[str, str]] = []
        self.fields: list[dict[str, str]] = []
        self._text_stack: list[str] = []
        self._text_buffer: list[str] = []
        self._current_heading: str | None = None
        self._current_action: dict[str, str] | None = None

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or '' for key, value in attrs}

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = self._attrs(attrs)
        tag_lower = tag.lower()
        if tag_lower in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self._current_heading = tag_lower
            self._text_buffer = []
        if tag_lower in {'button', 'summary'} or attr.get('role') == 'button':
            self._current_action = {
                'tag': tag_lower,
                'id': attr.get('id', ''),
                'class': attr.get('class', ''),
                'data_action': attr.get('data-action', ''),
                'aria_label': attr.get('aria-label', ''),
            }
            self._text_buffer = []
        if tag_lower == 'a':
            href = attr.get('href', '')
            is_external = href.startswith(('http://', 'https://', '//', 'mailto:', 'tel:'))
            if (href and not is_external) or attr.get('data-route'):
                route = attr.get('data-route') or href
                if route and route not in self.routes:
                    self.routes.append(route)
        if tag_lower in {'input', 'select', 'textarea'}:
            self.fields.append({
                'tag': tag_lower,
                'id': attr.get('id', ''),
                'name': attr.get('name', ''),
                'type': attr.get('type', ''),
                'placeholder': attr.get('placeholder', ''),
                'aria_label': attr.get('aria-label', ''),
            })
        self._text_stack.append(tag_lower)

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        text = self._clean(''.join(self._text_buffer))
        if self._current_heading == tag_lower:
            if text:
                self.headings.append({'tag': tag_lower, 'text': text})
            self._current_heading = None
            self._text_buffer = []
        if self._current_action and self._current_action['tag'] == tag_lower:
            if text:
                self._current_action['text'] = text
            self.actions.append(self._current_action)
            self._current_action = None
            self._text_buffer = []
        if self._text_stack:
            self._text_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._current_heading is not None or self._current_action is not None:
            self._text_buffer.append(data)


def _dedup(items):
    seen = set()
    result = []
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _scan_jsx(path: Path) -> dict:
    text = path.read_text(encoding='utf-8-sig')
    cleaned = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
    cleaned = re.sub(r'//[^\n]*', ' ', cleaned)
    headings = []
    for m in re.finditer(r'<(?:h[1-6]|Title)\b[^>]*>([^<>{}\n]+)</(?:h[1-6]|Title)>', cleaned):
        value = re.sub(r'\s+', ' ', m.group(1)).strip()
        if value:
            headings.append({'tag': 'heading', 'text': value})
    routes = []
    for m in re.finditer(r"(?:path|href|to)\s*[:=]\s*['\"]([^'\"]+)['\"]", cleaned):
        value = m.group(1).strip()
        if value and not value.startswith(('http://', 'https://', '//', 'mailto:', 'tel:')) and value not in routes:
            routes.append(value)
    actions = []
    for m in re.finditer(r'>([^<>{}\n]{1,40})<', cleaned):
        value = re.sub(r'\s+', ' ', m.group(1)).strip()
        if value:
            actions.append({'tag': 'jsx-text', 'text': value})
    for m in re.finditer(r'data-operation\s*=\s*["\']([^"\']+)["\']', cleaned):
        actions.append({'tag': 'jsx', 'data_action': m.group(1).strip()})
    fields = []
    for m in re.finditer(r'placeholder\s*[:=]\s*["\']([^"\']+)["\']', cleaned):
        fields.append({'tag': 'jsx', 'name': '', 'placeholder': m.group(1).strip(), 'label': ''})
    for m in re.finditer(r'label\s*[:=]\s*["\']([^"\']+)["\']', cleaned):
        fields.append({'tag': 'jsx', 'name': '', 'placeholder': '', 'label': m.group(1).strip()})
    for m in re.finditer(r'data-field\s*=\s*["\']([^"\']+)["\']', cleaned):
        fields.append({'tag': 'jsx', 'name': m.group(1).strip(), 'placeholder': '', 'label': ''})
    return {
        'source': path.name,
        'characters': len(text),
        'lines': len(text.splitlines()),
        'headings': _dedup(headings),
        'routes': _dedup(routes),
        'actions': _dedup(actions),
        'fields': _dedup(fields),
    }


def _scan_directory(root: Path, project_root: Path) -> dict:
    files = []
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if any(part in _EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() == '.html':
            extractor = PrototypeParser()
            try:
                text = path.read_text(encoding='utf-8-sig')
            except (OSError, UnicodeDecodeError):
                continue
            extractor.feed(text)
            files.append({
                'source': path.relative_to(project_root).as_posix(),
                'characters': len(text),
                'lines': len(text.splitlines()),
                'headings': extractor.headings,
                'routes': extractor.routes,
                'actions': extractor.actions,
                'fields': extractor.fields,
            })
        elif path.suffix.lower() in _JS_SUFFIXES:
            try:
                files.append(_scan_jsx(path))
                files[-1]['source'] = path.relative_to(project_root).as_posix()
            except (OSError, UnicodeDecodeError):
                continue
    combined = '\n'.join(json.dumps(f, ensure_ascii=False, sort_keys=True) for f in files)
    return {
        'source': root.relative_to(project_root).as_posix(),
        'source_hash': hashlib.sha256(combined.encode('utf-8')).hexdigest(),
        'characters': sum(f['characters'] for f in files),
        'lines': sum(f['lines'] for f in files),
        'files': files,
        'headings': _dedup([h for f in files for h in f['headings']]),
        'routes': _dedup([r for f in files for r in f['routes']]),
        'actions': _dedup([a for f in files for a in f['actions']]),
        'fields': _dedup([d for f in files for d in f['fields']]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='提取 Prototype 的结构线索，避免 PRD 默认全文读取 HTML/JSX')
    parser.add_argument('--input', type=Path, default=None, help='原型文件或目录（默认 <project-root>/output/prototype）')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--project-root', type=Path, default=Path.cwd(), help='项目根目录，用于输出相对 source 路径')
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    target = args.input.resolve() if args.input else project_root / 'output' / 'prototype'
    if not target.exists():
        print(f'Prototype 不存在: {target}', file=sys.stderr)
        return 1
    if target.is_dir():
        result = _scan_directory(target, project_root)
    else:
        text = target.read_text(encoding='utf-8-sig')
        extractor = PrototypeParser()
        extractor.feed(text)
        try:
            source = target.relative_to(project_root).as_posix()
        except ValueError:
            source = target.name
        result = {
            'source': source,
            'source_hash': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'characters': len(text),
            'lines': len(text.splitlines()),
            'headings': extractor.headings,
            'routes': extractor.routes,
            'actions': extractor.actions,
            'fields': extractor.fields,
        }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding='utf-8')
    else:
        print(payload, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
