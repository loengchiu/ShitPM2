from __future__ import annotations

"""建立可跨阶段复用的项目级材料资产。"""

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from token_estimate import estimate_tokens
from material_revision import material_revision as shared_material_revision, source_id_for
from typing import Iterable

TEXT_SUFFIXES = {'.md', '.markdown', '.txt', '.csv', '.json', '.yaml', '.yml', '.html'}
EXCLUDED_DIRS = {'.git', '.workflow', 'output', '__pycache__'}
HEADING_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$')
WORD_RE = re.compile(r'[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,8}')
STOPWORDS = {'以及', '然后', '可以', '需要', '进行', '相关', '内容', '信息', '系统', '用户', '这个', '当前'}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha256_object(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return sha256_text(payload)



def relative_path(project_root: Path, path: Path) -> str:
    return path.relative_to(project_root).as_posix() if path.is_relative_to(project_root) else str(path)


def resolve_inputs(project_root: Path, values: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in values:
        path = Path(raw)
        if not path.is_absolute():
            path = project_root / path
        path = path.resolve()
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = sorted(
                candidate for candidate in path.rglob('*')
                if candidate.is_file()
                and candidate.suffix.lower() in TEXT_SUFFIXES
                and not any(part in EXCLUDED_DIRS for part in candidate.relative_to(path).parts)
            )
        else:
            raise RuntimeError(f'材料路径不存在或不可读: {path}')
        for candidate in candidates:
            if candidate.suffix.lower() in TEXT_SUFFIXES and candidate not in paths:
                paths.append(candidate)
    if not paths:
        raise RuntimeError('至少指定一个可索引的 --input 文件或目录')
    return paths


def load_previous_materials(materials_dir: Path) -> tuple[dict | None, dict | None]:
    manifest_path = materials_dir / 'manifest.json'
    index_path = materials_dir / 'source-index.json'
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
        index = json.loads(index_path.read_text(encoding='utf-8-sig'))
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None
    if manifest.get('version') != 1 or index.get('version') != 2:
        return None, None
    return manifest, index


def load_reuse_inputs(project_root: Path, materials_dir: Path) -> list[Path]:
    manifest, _ = load_previous_materials(materials_dir)
    if not manifest or not isinstance(manifest.get('sources'), list):
        raise RuntimeError('未提供 --input，且项目级材料资产不存在或版本不受支持')
    paths: list[Path] = []
    for source in manifest['sources']:
        raw = source.get('absolute_path') or source.get('path')
        path = Path(raw)
        if not path.is_absolute():
            path = project_root / path
        path = path.resolve()
        if not path.is_file():
            raise RuntimeError(f'材料索引来源不存在: {path}；如材料集合发生变化，请重新指定 --input')
        paths.append(path)
    return paths


def keywords(text: str, limit: int = 12) -> list[str]:
    counts = Counter(word.lower() for word in WORD_RE.findall(text) if word not in STOPWORDS)
    return [word for word, _ in counts.most_common(limit)]


def segments(text: str) -> list[dict]:
    lines = text.splitlines()
    headings = [(index, match.group(1), match.group(2).strip())
                for index, line in enumerate(lines, start=1)
                if (match := HEADING_RE.match(line))]
    result: list[dict] = []
    if headings:
        for pos, (start, level, title) in enumerate(headings):
            end = headings[pos + 1][0] - 1 if pos + 1 < len(headings) else len(lines)
            body = '\n'.join(lines[start - 1:end]).strip()
            result.append({
                'title': title,
                'topic': title,
                'line_start': start,
                'line_end': end,
                'heading_level': len(level),
                'keywords': keywords(body),
                'characters': len(body),
                'tokens': estimate_tokens(body),
            })
        return result

    window = 80
    for start in range(1, len(lines) + 1, window):
        end = min(len(lines), start + window - 1)
        body = '\n'.join(lines[start - 1:end]).strip()
        if body:
            result.append({
                'title': f'材料片段 {start}-{end}',
                'topic': '未分节材料',
                'line_start': start,
                'line_end': end,
                'heading_level': None,
                'keywords': keywords(body),
                'characters': len(body),
                'tokens': estimate_tokens(body),
            })
    return result


def build_sources(project_root: Path, input_paths: list[Path], previous_index: dict | None = None) -> list[dict]:
    sources = []
    previous_by_path = {
        item.get('path'): item
        for item in (previous_index or {}).get('files', [])
    }
    for path in sorted(input_paths, key=lambda item: relative_path(project_root, item)):
        text = path.read_text(encoding='utf-8-sig')
        rel = relative_path(project_root, path)
        digest = sha256_text(text)
        previous = previous_by_path.get(rel)
        if previous and previous.get('sha256') == digest and isinstance(previous.get('segments'), list):
            reused = dict(previous)
            reused['absolute_path'] = str(path)
            sources.append(reused)
            continue
        source_id = source_id_for(rel)
        sources.append({
            'source_id': source_id,
            'path': rel,
            'absolute_path': str(path),
            'sha256': digest,
            'characters': len(text),
            'lines': len(text.splitlines()),
            'tokens': estimate_tokens(text),
            'segments': segments(text),
        })
    return sources


def material_revision(sources: list[dict]) -> str:
    return shared_material_revision(sources)


def build_assets(project_root: Path, sources: list[dict], previous_manifest: dict | None) -> tuple[dict, dict, dict]:
    revision = material_revision(sources)
    old_by_path = {item.get('path'): item for item in (previous_manifest or {}).get('sources', [])}
    new_by_path = {item['path']: item for item in sources}
    reused = sorted(path for path, item in new_by_path.items() if old_by_path.get(path, {}).get('sha256') == item['sha256'])
    changed = sorted(path for path, item in new_by_path.items() if path in old_by_path and old_by_path[path].get('sha256') != item['sha256'])
    added = sorted(path for path in new_by_path if path not in old_by_path)
    removed = sorted(path for path in old_by_path if path not in new_by_path)
    now = datetime.now(timezone.utc).isoformat()
    manifest_sources = [
        {
            key: item[key]
            for key in ('source_id', 'path', 'absolute_path', 'sha256', 'characters', 'lines', 'tokens')
        }
        for item in sources
    ]
    manifest = {
        'version': 1,
        'kind': 'project-materials',
        'generated_at': now,
        'project_root': str(project_root),
        'material_revision': revision,
        'source_count': len(manifest_sources),
        'sources': manifest_sources,
    }
    index = {
        'version': 2,
        'kind': 'project-material-index',
        'generated_at': now,
        'project_root': str(project_root),
        'material_revision': revision,
        'file_count': len(sources),
        'files': sources,
    }
    change = {
        'reused_sources': reused,
        'changed_sources': changed,
        'added_sources': added,
        'removed_sources': removed,
        'material_changed': bool(changed or added or removed),
        'unchanged': bool(previous_manifest and not (changed or added or removed)),
    }
    return manifest, index, change


def render_markdown(index: dict) -> str:
    lines = ['# 项目级材料索引', '', '> 该索引只用于定位材料；事实资产必须带材料版本和来源行范围。', '']
    for item in index['files']:
        lines.extend([
            f"## {item['path']}", '',
            f"- 来源 ID：`{item['source_id']}`",
            f"- SHA-256：`{item['sha256']}`",
            f"- 规模：{item['lines']} 行，约 {item['tokens']} token", '',
            '| 主题 | 行范围 | 关键词 | 体量 |', '|---|---:|---|---:|',
        ])
        for segment in item['segments']:
            words = '、'.join(segment['keywords']) or '—'
            title = segment['title'].replace('|', '／')
            lines.append(f"| {title} | {segment['line_start']}-{segment['line_end']} | {words} | {segment['tokens']} |")
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='生成可跨阶段复用的项目级材料资产')
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--input', action='append', default=[], help='材料文件或目录，可重复指定；省略时复用既有材料清单')
    parser.add_argument('--output-dir', type=Path, default=Path('.workflow/runtime/materials'))
    parser.add_argument('--force', action='store_true', help='即使材料未变化也重新写入资产')
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    materials_dir = args.output_dir if args.output_dir.is_absolute() else project_root / args.output_dir
    materials_dir = materials_dir.resolve()
    started = time.perf_counter()
    try:
        previous_manifest, previous_index = load_previous_materials(materials_dir)
        if args.input:
            input_paths = resolve_inputs(project_root, args.input)
        elif previous_manifest is not None:
            input_paths = load_reuse_inputs(project_root, materials_dir)
        elif any((materials_dir / name).exists() for name in ('manifest.json', 'source-index.json')):
            input_paths = load_reuse_inputs(project_root, materials_dir)
        else:
            # 空项目也要生成合法的空材料资产，避免把“没有材料”误判为材料准备失败。
            input_paths = []
        sources = build_sources(project_root, input_paths, previous_index)
        manifest, index, change = build_assets(project_root, sources, previous_manifest)
        reused = bool(previous_manifest and previous_index and change['unchanged'] and not args.force)
        if not reused:
            write_json(materials_dir / 'manifest.json', manifest)
            write_json(materials_dir / 'source-index.json', index)
            (materials_dir / 'source-index.md').write_text(render_markdown(index), encoding='utf-8')
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + manifest['material_revision'][:12]
        run = {
            'version': 1,
            'run_id': run_id,
            'kind': 'project-material-preparation',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'material_revision': manifest['material_revision'],
            'status': 'reused' if reused else ('updated' if previous_manifest else 'created'),
            'assets_reused': reused,
            'duration_ms': round((time.perf_counter() - started) * 1000),
            **change,
        }
        write_json(materials_dir / 'runs' / f'{run_id}.json', run)
        print(json.dumps({
            'materials_dir': str(materials_dir),
            'manifest': str(materials_dir / 'manifest.json'),
            'index': str(materials_dir / 'source-index.json'),
            'run': str(materials_dir / 'runs' / f'{run_id}.json'),
            **run,
        }, ensure_ascii=False, indent=2))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f'项目级材料资产准备失败：{exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
