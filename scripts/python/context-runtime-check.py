from __future__ import annotations

"""检查项目级材料资产，阻止版本错配与越界输入。"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from token_estimate import estimate_tokens
from typing import Any



def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except FileNotFoundError as exc:
        raise RuntimeError(f'文件不存在: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'JSON 格式错误: {path}: {exc}') from exc


def require_list(data: dict, key: str, path: Path) -> list:
    value = data.get(key)
    if not isinstance(value, list):
        raise RuntimeError(f'{path.name} 的 {key} 必须是数组')
    return value


def resolve_source(project_root: Path, item: dict) -> Path:
    source = Path(item.get('absolute_path') or item.get('path', ''))
    if not source.is_absolute():
        source = project_root / source
    return source.resolve()


def source_digest(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()


def check_manifest(path: Path, project_root: Path) -> dict:
    data = read_json(path)
    if data.get('version') != 1 or data.get('kind') != 'project-materials':
        raise RuntimeError(f'项目级材料清单格式不受支持: {path}')
    revision = str(data.get('material_revision', ''))
    if not re.fullmatch(r'(?:sha256:)?[0-9a-f]{64}', revision):
        raise RuntimeError(f'项目级材料清单缺少合法 material_revision: {path}')
    sources = require_list(data, 'sources', path)
    if data.get('source_count') != len(sources):
        raise RuntimeError(f'项目级材料清单 source_count 不匹配: {path}')
    seen = set()
    for item in sources:
        source_id = item.get('source_id')
        source_path = item.get('path')
        digest = item.get('sha256')
        if not source_id or not source_path or not re.fullmatch(r'[0-9a-f]{64}', str(digest or '')):
            raise RuntimeError(f'项目级材料清单缺少合法来源字段: {item}')
        if source_path in seen:
            raise RuntimeError(f'项目级材料清单存在重复来源: {source_path}')
        seen.add(source_path)
        source = resolve_source(project_root, item)
        if not source.is_file():
            raise RuntimeError(f'材料清单来源不存在: {source}')
        if source_digest(source) != digest:
            raise RuntimeError(f'材料清单来源已变化: {source_path}')
    return data


def check_material_index(path: Path, manifest: dict, project_root: Path) -> dict:
    data = read_json(path)
    if data.get('version') != 2 or data.get('kind') != 'project-material-index':
        raise RuntimeError(f'项目级材料索引格式不受支持: {path}')
    if data.get('material_revision') != manifest.get('material_revision'):
        raise RuntimeError('材料索引与材料清单的 material_revision 不一致')
    files = require_list(data, 'files', path)
    if data.get('file_count') != len(files) or len(files) != len(manifest['sources']):
        raise RuntimeError(f'材料索引文件数量与材料清单不一致: {path}')
    manifest_by_path = {item['path']: item for item in manifest['sources']}
    for item in files:
        source_path = item.get('path')
        if source_path not in manifest_by_path:
            raise RuntimeError(f'材料索引包含清单外来源: {source_path}')
        if item.get('sha256') != manifest_by_path[source_path]['sha256']:
            raise RuntimeError(f'材料索引来源哈希与清单不一致: {source_path}')
        source = resolve_source(project_root, item)
        content = source.read_text(encoding='utf-8-sig')
        if source_digest(source) != item['sha256']:
            raise RuntimeError(f'材料索引来源已变化: {source_path}')
        if not isinstance(item.get('segments'), list):
            raise RuntimeError(f'材料索引 segments 必须是数组: {source_path}')
        line_count = len(content.splitlines())
        for segment in item['segments']:
            start = int(segment.get('line_start', 0))
            end = int(segment.get('line_end', 0))
            if start < 1 or end < start or end > line_count:
                raise RuntimeError(f'材料索引行范围非法: {source_path}: {segment}')
    return data


def check_fact_item(item: dict, name: str, source_by_path: dict[str, dict]) -> None:
    source = item.get('source')
    if not isinstance(source, dict) or not source.get('path'):
        raise RuntimeError(f'{name} 缺少 source.path: {item}')
    source_path = source['path']
    indexed = source_by_path.get(source_path)
    if indexed is None:
        raise RuntimeError(f'{name} 引用了未在材料索引中的来源: {source_path}')
    if source.get('sha256') and source['sha256'] != indexed['sha256']:
        raise RuntimeError(f'{name} 的 source.sha256 与材料索引不一致: {source_path}')
    start = source.get('line_start')
    end = source.get('line_end')
    max_line = indexed.get('lines', 0)
    if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > max_line:
        raise RuntimeError(f'{name} 缺少合法 source 行范围: {item}')
    if not item.get('statement') and not item.get('description') and not item.get('claim'):
        raise RuntimeError(f'{name} 缺少可审计事实内容: {item}')


def check_material_facts(path: Path, manifest: dict, index: dict, max_tokens: int) -> dict:
    data = read_json(path)
    if data.get('version') != 1:
        raise RuntimeError(f'{path.name} version 必须为 1')
    if data.get('material_revision') != manifest.get('material_revision'):
        raise RuntimeError(f'{path.name} 与当前材料的 material_revision 不一致')
    source_by_path = {item['path']: item for item in index['files']}
    for key in ('confirmed_facts', 'source_conflicts', 'missing_information', 'non_derivable_items'):
        for number, item in enumerate(require_list(data, key, path), start=1):
            if not isinstance(item, dict):
                raise RuntimeError(f'{path.name}:{key}[{number}] 必须是对象')
            check_fact_item(item, f'{path.name}:{key}[{number}]', source_by_path)
    tokens = estimate_tokens(path.read_text(encoding='utf-8-sig'))
    if tokens > max_tokens:
        raise RuntimeError(f'{path.name} 约 {tokens} token，超过上限 {max_tokens}')
    return {'path': str(path), 'tokens': tokens, 'material_revision': data['material_revision']}



# 这些上限只限制材料事实包的体量，防止上下文再次膨胀；
# 它们不是产品完整性、字段数量或业务复杂度门槛。
DEFAULT_MAX_MATERIAL_FACTS = 8000


def main() -> int:
    parser = argparse.ArgumentParser(description='检查项目级材料资产')
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--require', action='append', choices=['material-manifest', 'material-index', 'material-facts'], default=[])
    parser.add_argument('--max-material-facts', type=int, default=DEFAULT_MAX_MATERIAL_FACTS)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    materials = project_root / '.workflow' / 'runtime' / 'materials'
    checked = []
    try:
        manifest = None
        index = None
        if any(name in args.require for name in ('material-manifest', 'material-index', 'material-facts')):
            manifest = check_manifest(materials / 'manifest.json', project_root)
        if 'material-index' in args.require or 'material-facts' in args.require:
            index = check_material_index(materials / 'source-index.json', manifest, project_root)
        for name in args.require:
            if name == 'material-manifest':
                checked.append({'name': name, 'sources': manifest['source_count'], 'material_revision': manifest['material_revision']})
            elif name == 'material-index':
                checked.append({'name': name, 'files': index['file_count'], 'material_revision': index['material_revision']})
            elif name == 'material-facts':
                checked.append({'name': name, **check_material_facts(materials / 'facts.json', manifest, index, args.max_material_facts)})
        print(json.dumps({'valid': True, 'checked': checked}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({'valid': False, 'error': str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
