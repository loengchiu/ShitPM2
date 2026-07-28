from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


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


def main() -> int:
    parser = argparse.ArgumentParser(description='提取 Prototype 的结构线索，避免 PRD 默认全文读取 HTML')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--project-root', type=Path, default=Path.cwd(), help='项目根目录，用于输出相对 source 路径')
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    path = args.input.resolve()
    if not path.is_file():
        print(f'Prototype 不存在: {path}', file=sys.stderr)
        return 1
    text = path.read_text(encoding='utf-8-sig')
    extractor = PrototypeParser()
    extractor.feed(text)
    try:
        source = path.relative_to(project_root).as_posix()
    except ValueError:
        source = path.name
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
