from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from token_estimate import estimate_tokens
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_REL = Path('contracts/context-loading.manifest.json')
GENERATED_PACK_RE = re.compile(r'^\d{3}-[A-Za-z0-9_.-]+\.md$')


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_text(path.read_text(encoding='utf-8-sig'))


def manifest_path(bundle_root: Path) -> Path:
    return bundle_root / MANIFEST_REL


def load_manifest(bundle_root: Path) -> dict[str, Any]:
    path = manifest_path(bundle_root)
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except FileNotFoundError as exc:
        raise RuntimeError(f'上下文装载清单不存在: {path}') from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'上下文装载清单格式错误: {path}: {exc}') from exc
    if data.get('version') != 1:
        raise RuntimeError(f'不支持的上下文装载清单版本: {data.get("version")}')
    return data


def read_section(bundle_root: Path, section_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    source = bundle_root / spec['source']
    if not source.is_file():
        raise RuntimeError(f'上下文来源不可读: {section_id} -> {source}')
    text = source.read_text(encoding='utf-8-sig')
    selector = spec.get('selector', 'marker')
    if selector == 'whole':
        content = text.strip()
    elif selector == 'marker':
        start = f'<!-- context:{section_id}:start -->'
        end = f'<!-- context:{section_id}:end -->'
        if text.count(start) != 1 or text.count(end) != 1:
            raise RuntimeError(f'上下文章节标记不完整: {section_id} -> {source}')
        begin = text.index(start) + len(start)
        finish = text.index(end, begin)
        content = text[begin:finish].strip()
    else:
        raise RuntimeError(f'不支持的上下文选择器: {section_id}: {selector}')
    if not content:
        raise RuntimeError(f'上下文章节为空: {section_id} -> {source}')
    return {
        'id': section_id,
        'source': spec['source'],
        'source_hash': sha256_text(text),
        'content_hash': sha256_text(content),
        'selector': selector,
        'content': content,
        'characters': len(content),
        'lines': len(content.splitlines()),
    }


def _section_ids_for_pack(pack: dict[str, Any], mode: str | None,
                          cards: list[str], examples: list[str], pack_name: str) -> list[str]:
    section_ids = list(pack.get('sections', []))
    if 'mode_sections' in pack:
        if not mode:
            raise RuntimeError(f'pack {pack_name} 需要 --mode simple 或 --mode full')
        if mode not in pack['mode_sections']:
            raise RuntimeError(f'不支持的模式: {mode}')
        section_ids.extend(pack['mode_sections'][mode])
    if 'card_sections' in pack:
        for card in cards:
            if card not in pack['card_sections']:
                raise RuntimeError(f'未定义的场景卡: {card}')
            section_ids.extend(pack['card_sections'][card])
    if 'example_sections' in pack:
        for example in examples:
            if example not in pack['example_sections']:
                raise RuntimeError(f'未定义的 PRD 示例键: {example}')
            section_ids.extend(pack['example_sections'][example])
    return section_ids


def validate_role_selection(manifest: dict[str, Any], stage: str, pass_name: str | None,
                            selected_packs: list[str], role: str | None) -> None:
    if role is None:
        return
    roles = manifest.get('subagent_roles', {})
    if role not in roles:
        raise RuntimeError(f'未定义的 Sub-agent 角色: {role}')
    stage_rules = roles[role].get('allowed', {}).get(stage)
    if not stage_rules:
        raise RuntimeError(f'Sub-agent 角色 {role} 不允许执行阶段: {stage}')
    allowed_passes = set(stage_rules.get('passes', []))
    if pass_name not in allowed_passes:
        expected = '、'.join(sorted(allowed_passes)) or '无'
        raise RuntimeError(f'Sub-agent 角色 {role} 不允许执行 {stage}.{pass_name or "<explicit-pack>"}，允许 pass: {expected}')
    allowed_packs = set(stage_rules.get('packs', []))
    unauthorized = [pack for pack in selected_packs if pack not in allowed_packs]
    if unauthorized:
        raise RuntimeError(f'Sub-agent 角色 {role} 不允许装载 pack: {"、".join(unauthorized)}')


def resolve_pack_sections(manifest: dict[str, Any], stage: str, mode: str | None,
                          pass_name: str | None, pack_names: list[str], cards: list[str],
                          examples: list[str], applicability: dict[str, str] | None,
                          role: str | None = None) -> tuple[list[str], dict[str, list[str]]]:
    stages = manifest.get('stages', {})
    if stage not in stages:
        raise RuntimeError(f'不支持的阶段: {stage}')
    stage_spec = stages[stage]
    if pass_name and pass_name not in stage_spec.get('passes', {}):
        raise RuntimeError(f'阶段 {stage} 不存在 pass: {pass_name}')
    selected_packs = list(stage_spec.get('passes', {}).get(pass_name, [])) if pass_name else []
    selected_packs.extend(pack_names)
    selected_packs = list(dict.fromkeys(selected_packs))
    if not selected_packs:
        raise RuntimeError('至少指定 --pass 或 --pack')
    validate_role_selection(manifest, stage, pass_name, selected_packs, role)
    if applicability is not None:
        derived_cards = []
        for key, status in applicability.items():
            if status in {'applicable', 'unknown'}:
                derived_cards.append(key)
            elif status != 'not_applicable':
                raise RuntimeError(f'未知适用性状态: {key}={status}')
        cards = list(dict.fromkeys(cards + derived_cards))
    packs = stage_spec.get('packs', {})
    result: dict[str, list[str]] = {}
    seen: set[str] = set()
    for pack_name in selected_packs:
        if pack_name not in packs:
            raise RuntimeError(f'阶段 {stage} 不存在 pack: {pack_name}')
        raw_ids = _section_ids_for_pack(packs[pack_name], mode, cards, examples, pack_name)
        ids = []
        for section_id in raw_ids:
            if section_id in seen:
                continue
            ids.append(section_id)
            seen.add(section_id)
        result[pack_name] = ids
    sections = manifest.get('sections', {})
    for section_id in seen:
        if section_id not in sections:
            raise RuntimeError(f'pack 引用未定义章节: {section_id}')
        if sections[section_id].get('stage') != stage:
            raise RuntimeError(f'章节阶段不匹配: {section_id} -> {sections[section_id].get("stage")}')
    return selected_packs, result


def resolve_selection(manifest: dict[str, Any], stage: str, mode: str | None,
                      pass_name: str | None, pack_names: list[str], cards: list[str],
                      examples: list[str], applicability: dict[str, str] | None,
                      role: str | None = None) -> tuple[list[str], list[str]]:
    selected_packs, pack_sections = resolve_pack_sections(
        manifest, stage, mode, pass_name, pack_names, cards, examples, applicability, role,
    )
    return selected_packs, [section_id for ids in pack_sections.values() for section_id in ids]


def build_sections(bundle_root: Path, manifest: dict[str, Any], stage: str,
                   section_ids: list[str]) -> list[dict[str, Any]]:
    sections = manifest['sections']
    return [read_section(bundle_root, section_id, sections[section_id]) for section_id in section_ids]



def render_pack(stage: str, pack_name: str, sections: list[dict[str, Any]]) -> str:
    lines = [
        f'# ShitPM {stage} context pack: {pack_name}',
        '',
        '> 本文件是运行时上下文视图，不是产品事实源。内容按 manifest 从唯一权威来源提取。',
        '',
    ]
    for section in sections:
        lines.extend([
            f'<!-- source: {section["source"]} -->',
            f'<!-- section: {section["id"]} -->',
            f'<!-- source-hash: {section["source_hash"]} -->',
            '',
            section['content'],
            '',
            '---',
            '',
        ])
    return '\n'.join(lines).rstrip() + '\n'


def write_run(project_root: Path, stage: str, mode: str | None, pass_name: str | None,
              selected_packs: list[str], pack_sections: dict[str, list[str]],
              section_data: list[dict[str, Any]], output_dir: Path,
              applicability: dict[str, str] | None, *, bundle_root: Path | None = None,
              manifest_hash: str | None = None, role: str | None = None,
              budget: dict[str, Any] | None = None, duration_ms: int | None = None,
              metrics_dir: Path | None = None) -> dict[str, Any]:
    bundle_root = (bundle_root or ROOT).resolve()
    if manifest_hash is None:
        manifest_hash = sha256_file(manifest_path(bundle_root))
    packs_dir = output_dir / 'packs'
    packs_dir.mkdir(parents=True, exist_ok=True)
    for old in packs_dir.glob('*.md'):
        if GENERATED_PACK_RE.fullmatch(old.name):
            old.unlink()
    by_id = {item['id']: item for item in section_data}
    written_packs = []
    for index, pack_name in enumerate(selected_packs, start=1):
        data = [by_id[section_id] for section_id in pack_sections.get(pack_name, [])]
        if not data:
            continue
        file_name = f'{index:03d}-{pack_name}.md'
        (packs_dir / file_name).write_text(render_pack(stage, pack_name, data), encoding='utf-8')
        written_packs.append(file_name)
    source_hashes = {item['source']: item['source_hash'] for item in section_data}
    characters = sum(item['characters'] for item in section_data)
    record = {
        'stage': stage,
        'mode': mode,
        'pass': pass_name,
        'role': role,
        'packs': written_packs,
        'requested_packs': selected_packs,
        'sections': [
            {key: item[key] for key in ('id', 'source', 'selector', 'source_hash', 'content_hash', 'characters', 'lines')}
            for item in section_data
        ],
        'sources': sorted({item['source'] for item in section_data}),
        'source_file_count': len({item['source'] for item in section_data}),
        'section_count': len(section_data),
        'characters': characters,
        'lines': sum(item['lines'] for item in section_data),
        'tokens': estimate_tokens('\n'.join(item['content'] for item in section_data)),
        'source_hashes': source_hashes,
        'manifest_hash': manifest_hash,
        'manifest_path': MANIFEST_REL.as_posix(),
        'applicability': applicability or {},
        'budget': budget or {},
        'duration_ms': duration_ms,
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'run.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if metrics_dir is not None:
        metrics_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        metric = {
            'version': 1,
            'stage': stage,
            'mode': mode,
            'pass': pass_name,
            'role': role,
            'status': 'completed',
            'generated_at': record['generated_at'],
            'duration_ms': duration_ms,
            'tokens': record['tokens'],
            'characters': characters,
            'section_count': record['section_count'],
            'source_file_count': record['source_file_count'],
            'material_assets_available': all((project_root / '.workflow/runtime/materials' / name).is_file() for name in ('manifest.json', 'source-index.json')),
            'raw_materials_in_pack': False,
            'handoff_dir': str(project_root / '.workflow/runtime/context' / stage / 'handoff'),
        }
        (metrics_dir / f'{stamp}-{stage}-{pass_name or "explicit"}.json').write_text(
            json.dumps(metric, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )
    return record


def expected_context_root(project_root: Path, stage: str) -> Path:
    return project_root.resolve() / '.workflow' / 'runtime' / 'context' / stage


def validate_output_dir(project_root: Path, stage: str, output_dir: Path) -> Path:
    resolved = output_dir.resolve()
    expected = expected_context_root(project_root, stage)
    try:
        resolved.relative_to(expected)
    except ValueError as exc:
        raise RuntimeError(
            f'上下文输出目录必须位于项目运行时目录: {expected}；收到: {resolved}'
        ) from exc
    return resolved


def verify_run(project_root: Path, stage: str, run_path: Path | None = None,
               *, bundle_root: Path | None = None) -> dict[str, Any]:
    bundle_root = (bundle_root or ROOT).resolve()
    if run_path is None:
        run_path = expected_context_root(project_root, stage) / 'run.json'
    elif not run_path.is_absolute():
        run_path = project_root / run_path
    if run_path.is_dir():
        run_path = run_path / 'run.json'
    if not run_path.is_file():
        raise RuntimeError(f'运行记录不存在: {run_path}')
    try:
        record = json.loads(run_path.read_text(encoding='utf-8-sig'))
    except Exception as exc:
        raise RuntimeError(f'运行记录格式错误: {run_path}: {exc}') from exc
    stale = []
    current_hashes = {}
    current_manifest = manifest_path(bundle_root)
    expected_manifest_hash = record.get('manifest_hash')
    if not current_manifest.is_file():
        stale.append({'source': MANIFEST_REL.as_posix(), 'reason': 'missing'})
    else:
        actual_manifest_hash = sha256_file(current_manifest)
        current_hashes[MANIFEST_REL.as_posix()] = actual_manifest_hash
        if not expected_manifest_hash:
            stale.append({'source': MANIFEST_REL.as_posix(), 'reason': 'manifest_hash_missing'})
        elif actual_manifest_hash != expected_manifest_hash:
            stale.append({
                'source': MANIFEST_REL.as_posix(),
                'reason': 'hash_changed',
                'expected': expected_manifest_hash,
                'actual': actual_manifest_hash,
            })
    for source, expected in record.get('source_hashes', {}).items():
        path = bundle_root / source
        if not path.is_file():
            stale.append({'source': source, 'reason': 'missing'})
            continue
        current = sha256_file(path)
        current_hashes[source] = current
        if current != expected:
            stale.append({'source': source, 'reason': 'hash_changed', 'expected': expected, 'actual': current})
    return {
        'run': str(run_path),
        'stage': record.get('stage'),
        'generated_at': record.get('generated_at'),
        'stale': stale,
        'current_hashes': current_hashes,
        'valid': not stale,
    }


def parse_json_mapping(path: Path | None) -> dict[str, str] | None:
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception as exc:
        raise RuntimeError(f'适用性文件格式错误: {path}: {exc}') from exc
    if not isinstance(data, dict):
        raise RuntimeError(f'适用性文件必须是对象: {path}')
    return {str(key): str(value) for key, value in data.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description='按 bundle manifest 编译 ShitPM Design / PRD 运行时上下文包')
    parser.add_argument('--project-root', type=Path, default=Path.cwd(), help='业务项目根目录，默认当前目录')
    parser.add_argument('--bundle-root', type=Path, default=ROOT, help='ShitPM bundle 根目录，默认脚本所在 bundle')
    parser.add_argument('--stage', required=True, choices=['design', 'prd'])
    parser.add_argument('--mode', choices=['simple', 'full'])
    parser.add_argument('--pass', dest='pass_name')
    parser.add_argument('--role', help='Sub-agent 角色；指定后按 manifest 白名单校验 pack')
    parser.add_argument('--pack', action='append', default=[])
    parser.add_argument('--card', action='append', default=[])
    parser.add_argument('--example', action='append', default=[])
    parser.add_argument('--applicability-json', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--list-packs', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verify-run', action='store_true', help='校验已有 run.json 的来源和 manifest 哈希是否陈旧')
    parser.add_argument('--max-tokens', type=int, help='可选上下文 token 预算；估算超过时按 --fail-on-budget 失败')
    parser.add_argument('--fail-on-budget', action='store_true', help='与 --max-tokens 一起使用，超预算时拒绝写入运行包')
    args = parser.parse_args()
    if args.fail_on_budget and args.max_tokens is None:
        parser.error('--fail-on-budget 必须与 --max-tokens 一起使用')
    project_root = args.project_root.resolve()
    bundle_root = args.bundle_root.resolve()
    started = time.perf_counter()
    try:
        manifest = load_manifest(bundle_root)
        if args.verify_run:
            verification = verify_run(project_root, args.stage, args.output_dir, bundle_root=bundle_root)
            print(json.dumps(verification, ensure_ascii=False, indent=2))
            return 0 if verification['valid'] else 1
        if args.list_packs:
            for name, spec in manifest['stages'][args.stage].get('packs', {}).items():
                print(f'{name}: {spec.get("purpose", "")}')
            return 0
        applicability_path = args.applicability_json
        if applicability_path and not applicability_path.is_absolute():
            applicability_path = project_root / applicability_path
        applicability = parse_json_mapping(applicability_path)
        selected_packs, pack_sections = resolve_pack_sections(
            manifest, args.stage, args.mode, args.pass_name, args.pack,
            args.card, args.example, applicability, args.role,
        )
        section_ids = [section_id for ids in pack_sections.values() for section_id in ids]
        section_data = build_sections(bundle_root, manifest, args.stage, section_ids)
        characters = sum(item['characters'] for item in section_data)
        preview = {
            'stage': args.stage,
            'mode': args.mode,
            'pass': args.pass_name,
            'role': args.role,
            'bundle_root': str(bundle_root),
            'requested_packs': selected_packs,
            'sections': section_ids,
            'sources': sorted({item['source'] for item in section_data}),
            'source_file_count': len({item['source'] for item in section_data}),
            'section_count': len(section_data),
            'characters': characters,
            'lines': sum(item['lines'] for item in section_data),
            'tokens': estimate_tokens('\n'.join(item['content'] for item in section_data)),
        }
        if args.max_tokens is not None and args.max_tokens < 0:
            raise RuntimeError('--max-tokens 不能为负数')
        budget = {}
        if args.max_tokens is not None:
            budget = {
                'max_tokens': args.max_tokens,
                'tokens': preview['tokens'],
                'within_budget': preview['tokens'] <= args.max_tokens,
                'method': 'heuristic-cjk-0.6-non-cjk-0.25',
            }
            if not budget['within_budget']:
                message = f"上下文估算约 {preview['tokens']} token，超过预算 {args.max_tokens} token"
                if args.fail_on_budget:
                    raise RuntimeError(message)
                budget['warning'] = message
        if args.dry_run:
            preview['budget'] = budget
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            return 0
        output_dir = args.output_dir
        if output_dir is None:
            output_dir = expected_context_root(project_root, args.stage)
        elif not output_dir.is_absolute():
            output_dir = project_root / output_dir
        output_dir = validate_output_dir(project_root, args.stage, output_dir)
        record = write_run(
            project_root, args.stage, args.mode, args.pass_name,
            selected_packs, pack_sections, section_data, output_dir, applicability,
            bundle_root=bundle_root, manifest_hash=sha256_file(manifest_path(bundle_root)), role=args.role,
            budget=budget,
            duration_ms=round((time.perf_counter() - started) * 1000),
            metrics_dir=project_root / '.workflow' / 'runtime' / 'metrics',
        )
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, OSError) as exc:
        print(f'上下文装载失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
