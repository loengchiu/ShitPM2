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
DESIGN_FRAGMENT_PACK = 'design-fragment'
DESIGN_REL = Path('output/design/design.md')
# 大 Design 阈值：与 SKILL 阶段 A “约 1000 行”一致；只有超过该规模才启用片段比例约束。
LARGE_DESIGN_LINES = 1000
# 标题锚点：Design 按“### 闭环X：名称 / ### 页面：名称 / ## 共用章节”组织，按锚点确定性切分。
# 注意：匹配的是去掉 # 前缀后的标题文本，正则不得带 ### 前缀。
CLOSURE_HEADING_RE = re.compile(r'^闭环[一二三四五六七八九十0-9A-Za-z]+[：:]\s*(.+)$')
PAGE_HEADING_RE = re.compile(r'^页面[：:]\s*(.+)$')
SHARED_HEADING_KEYWORDS = ('业务对象', '角色、权限', '权限与数据范围', '页面清单', '待确认事项')


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
            raise RuntimeError(f'pack {pack_name} 需要 --mode simple 或 full')
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


def _design_headings(text: str) -> list[dict[str, Any]]:
    """解析 design.md 标题：记录所有标题用于边界计算；只对“闭环X：/页面：/共用章节”打锚点标记。"""
    headings = []
    for line_no, line in enumerate(text.splitlines(), 1):
        match = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        kind = None
        name = None
        closure = CLOSURE_HEADING_RE.match(title)
        page = PAGE_HEADING_RE.match(title)
        if closure:
            kind, name = 'closure', closure.group(1).strip()
        elif page:
            kind, name = 'page', page.group(1).strip()
        elif level == 2 and any(keyword in title for keyword in SHARED_HEADING_KEYWORDS):
            kind, name = 'shared', title
        elif level == 3 and title in ('页面清单', '待确认事项'):
            kind, name = 'shared', title
        headings.append({'line': line_no, 'level': level, 'title': title, 'kind': kind, 'name': name})
    return headings


def _scope_end(lines: list[str], headings: list[dict[str, Any]], index: int) -> int:
    """当前标题的作用域到下一个同级或更高级标题为止（所有 markdown 标题都参与边界计算）。"""
    current = headings[index]
    for next_heading in headings[index + 1:]:
        if next_heading['level'] <= current['level']:
            return next_heading['line'] - 1
    return len(lines)


def _heading_text(lines: list[str], start_line: int, end_line: int) -> str:
    return '\n'.join(lines[start_line - 1:end_line]).rstrip()


def _longest_common_substring(a: str, b: str) -> str:
    """确定性字符串算法：两段文本的最长公共子串，用于闭环与页面的标题词关联。"""
    if not a or not b:
        return ''
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    best = ''
    for start in range(len(shorter)):
        for length in range(len(shorter) - start, len(best), -1):
            candidate = shorter[start:start + length]
            if candidate in longer:
                best = candidate
                break
    return best


def _match_module(headings: list[dict[str, Any]], module: str) -> dict[str, Any] | None:
    """模块名匹配闭环标题：名称精确、模块名含于闭环名、闭环名含于模块名（去掉“模块”后缀）。"""
    candidates = [heading for heading in headings if heading['kind'] == 'closure']
    stripped = re.sub(r'模块$', '', module)
    for heading in candidates:
        name = heading['name']
        if name == module or module in name or name in module or stripped in name or name in stripped:
            return heading
    return None


def _match_pages(headings: list[dict[str, Any]], names: list[str]) -> list[dict[str, Any]]:
    """按页面名匹配“### 页面：名称”章节；只接受名称唯一且精确的匹配，避免短名误命。"""
    pages = [heading for heading in headings if heading['kind'] == 'page']
    by_name: dict[str, dict[str, Any]] = {}
    for heading in pages:
        by_name.setdefault(heading['name'], heading)
    matched = []
    for name in names:
        name = re.sub(r'模块$', '', name.strip())
        if not name:
            continue
        if name in by_name:
            matched.append(by_name[name])
    return matched


def _related_pages(headings: list[dict[str, Any]], closure: dict[str, Any] | None,
                   closure_text: str, module: str) -> list[dict[str, Any]]:
    """确定页面关联：①闭环正文子串引用；②页面名与闭环名/模块名共享 ≥2 字最长公共子串；两者取并集。

    不做语义检索；页面与闭环的标题词关联由字符串算法确定，避免模型自行猜测。
    """
    names = sorted({h['name'] for h in headings if h['kind'] == 'page'}, key=len, reverse=True)
    referenced = [name for name in names if len(name) >= 2 and name in closure_text]
    subjects = [module]
    if closure is not None:
        subjects.append(closure['name'])
    for name in names:
        if name in referenced:
            continue
        for subject in subjects:
            shared = _longest_common_substring(name, subject)
            if len(shared) >= 2:
                referenced.append(name)
                break
    return _match_pages(headings, referenced)


def extract_design_fragment(project_root: Path, module: str,
                            threshold_fraction: float = 1 / 3,
                            extra_pages: list[str] | None = None) -> dict[str, Any]:
    """按标题锚点从 output/design/design.md 确定性提取模块片段（原文，不做语义检索、不做概括）。

    提取范围：目标闭环章节全文 + 闭环正文引用的页面章节 + 共用章节（业务对象/权限/页面清单/待确认）。
    匹配不到模块时报错并列出标题清单；片段行数超过全文阈值时报错提示拆分模块。
    """
    design_path = project_root / DESIGN_REL
    if not design_path.is_file():
        raise RuntimeError(f'Design 文件不存在: {design_path}')
    text = design_path.read_text(encoding='utf-8-sig')
    lines = text.splitlines()
    headings = _design_headings(text)
    closure = _match_module(headings, module)
    matched_pages: list[dict[str, Any]] = []
    closure_text = ''
    if closure is None:
        matched_pages = _match_pages(headings, [module] + list(extra_pages or []))
        if not matched_pages:
            available = '\n'.join(
                f'  {h["title"]}' for h in headings
                if h['kind'] in ('closure', 'page')
            ) or '  （design.md 无闭环/页面标题锚点）'
            raise RuntimeError(
                f'模块名 “{module}” 匹配不到任何闭环或页面章节，不静默返回空。'
                f'design.md 可用闭环/页面标题：\n{available}'
            )
    parts: list[str] = []
    included_lines = 0
    if closure is not None:
        index = headings.index(closure)
        end = _scope_end(lines, headings, index)
        closure_text = _heading_text(lines, closure['line'], end)
        parts.append(f'## 模块闭环：{closure["title"]}\n\n{closure_text}')
        included_lines += end - closure['line'] + 1
        matched_pages = _related_pages(headings, closure, closure_text, module)
        # --pages 显式追加页面：闭环匹配成功后仍生效（补充标题词关联漏掉的页面），按名称精确匹配去重。
        for page in _match_pages(headings, list(extra_pages or [])):
            if page['name'] not in {p['name'] for p in matched_pages}:
                matched_pages.append(page)
    else:
        # 模块名即页面名：目标页面已从 [module]+extra_pages 精确匹配，直接作为相关页面输出。
        matched_pages = _match_pages(headings, [module] + list(extra_pages or []))
    page_lines = 0
    for page in matched_pages:
        index = headings.index(page)
        end = _scope_end(lines, headings, index)
        parts.append(f'\n## 相关页面：{page["name"]}\n\n{_heading_text(lines, page["line"], end)}')
        page_lines += end - page['line'] + 1
    included_lines += page_lines
    shared_parts: list[str] = []
    page_names = {p['name'] for p in matched_pages}
    for heading in headings:
        if heading['kind'] != 'shared':
            continue
        index = headings.index(heading)
        end = _scope_end(lines, headings, index)
        section_text = _heading_text(lines, heading['line'], end)
        if heading['title'] == '页面清单' and page_names:
            # 页面清单只保留与本模块页面匹配的数据行（表头/分隔行保留），避免每个模块都携带全量页面清单。
            kept = []
            for raw in section_text.splitlines():
                line = raw.strip()
                if line.startswith('|'):
                    cells = [c.strip() for c in line.strip('|').split('|')]
                    first = cells[0] if cells else ''
                    if first in page_names or first in ('页面', '页面/入口', '页面名称') or set(first) <= {'-', ' ', ''}:
                        kept.append(raw)
                    continue
                kept.append(raw)
            section_text = '\n'.join(kept)
        shared_parts.append(f'\n## 共用部分：{heading["title"]}\n\n{section_text}')
        included_lines += len(section_text.splitlines())
    fragment_text = '\n'.join(parts)
    if shared_parts:
        fragment_text += '\n' + '\n'.join(shared_parts)
    # 片段比例只约束大 Design（防止爆上下文）；小 Design 可接近全文，不误伤。
    if len(lines) >= LARGE_DESIGN_LINES and included_lines > max(1, int(len(lines) * threshold_fraction)):
        raise RuntimeError(
            f'模块 “{module}” 的 Design 片段 {included_lines} 行超过阈值 '
            f'（design.md 全文 {len(lines)} 行的 {threshold_fraction:.0%}）。'
            f'模块边界过大，请按子闭环或页面拆分模块后再分片。'
        )
    section_id = f'design-fragment:{module}'
    return {
        'id': section_id,
        'source': DESIGN_REL.as_posix(),
        'source_hash': sha256_text(text),
        'content_hash': sha256_text(fragment_text),
        'selector': 'fragment',
        'content': fragment_text,
        'characters': len(fragment_text),
        'lines': included_lines,
        'module': module,
        'fragment_meta': {
            'design_lines': len(lines),
            'fragment_lines': included_lines,
            'threshold_fraction': threshold_fraction,
        },
    }



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
              metrics_dir: Path | None = None, module: str | None = None) -> dict[str, Any]:
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
        'module': module,
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
    # --module 装载的 design.md 片段按 selector=fragment 判定为项目级来源，从项目根解析；
    # 其余 source 一律从 bundle 解析（bundle 内的同名输出文件不参与校验）。
    project_sources = {
        item.get('source')
        for item in record.get('sections', [])
        if isinstance(item, dict) and item.get('selector') == 'fragment'
    }
    for source, expected in record.get('source_hashes', {}).items():
        if source in project_sources:
            path = project_root / source
        else:
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
    parser.add_argument('--module', help='按模块名装载 design.md 片段（与 --pass module 组合使用）：提取闭环章节 + 相关页面 + 共用对象/权限部分')
    parser.add_argument('--pages', action='append', default=[], help='显式追加提取的页面名（模块名匹配不到闭环时按页面名兜底）')
    parser.add_argument('--fragment-threshold', type=float, default=1 / 3,
                        help='Design 片段行数阈值占 design.md 全文比例，默认 1/3；超过时报错提示拆分模块')
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
    if args.module and (args.fragment_threshold <= 0 or args.fragment_threshold >= 1):
        parser.error('--fragment-threshold 必须是 (0, 1) 区间的小数')
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
        if args.module:
            fragment = extract_design_fragment(
                project_root, args.module,
                threshold_fraction=args.fragment_threshold,
                extra_pages=args.pages,
            )
            section_data.append(fragment)
            selected_packs = list(dict.fromkeys(selected_packs + [DESIGN_FRAGMENT_PACK]))
            pack_sections[DESIGN_FRAGMENT_PACK] = [fragment['id']]
        characters = sum(item['characters'] for item in section_data)
        preview = {
            'stage': args.stage,
            'mode': args.mode,
            'pass': args.pass_name,
            'role': args.role,
            'module': args.module,
            'bundle_root': str(bundle_root),
            'requested_packs': selected_packs,
            'sections': [item['id'] for item in section_data],
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
            module=args.module,
        )
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, OSError) as exc:
        print(f'上下文装载失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
