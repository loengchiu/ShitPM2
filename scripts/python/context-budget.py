from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from token_estimate import estimate_tokens
from shared_md import load_sibling

ROOT = Path(__file__).resolve().parents[2]



def measure_files(project_root: Path, files: list[str]) -> dict:
    items = []
    for rel in files:
        path = project_root / rel
        if not path.is_file():
            raise RuntimeError(f'预算输入不可读: {path}')
        text = path.read_text(encoding='utf-8-sig')
        items.append({
            'path': rel,
            'characters': len(text),
            'lines': len(text.splitlines()),
            'tokens': estimate_tokens(text),
        })
    return {
        'files': items,
        'file_count': len(items),
        'characters': sum(item['characters'] for item in items),
        'lines': sum(item['lines'] for item in items),
        'tokens': sum(item['tokens'] for item in items),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='统计 ShitPM 上下文规则和业务输入体量')
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--bundle-root', type=Path, help='ShitPM bundle 根目录，默认统计脚本所在 bundle')
    parser.add_argument('--stage', choices=['design', 'prd'])
    parser.add_argument('--mode', choices=['simple', 'full'])
    parser.add_argument('--pass', dest='pass_name')
    parser.add_argument('--pack', action='append', default=[])
    parser.add_argument('--card', action='append', default=[])
    parser.add_argument('--example', action='append', default=[])
    parser.add_argument('--applicability-json', type=Path)
    parser.add_argument('--input', action='append', default=[], help='业务输入或产物相对路径，可重复')
    parser.add_argument('--files', nargs='*', default=[], help='静态文件相对路径，可重复或空格分隔')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--max-tokens', type=int, help='可选 token 预算；结果中返回是否超限')
    parser.add_argument('--fail-on-budget', action='store_true', help='与 --max-tokens 一起使用，超预算时返回失败')
    args = parser.parse_args()
    if args.fail_on_budget and args.max_tokens is None:
        parser.error('--fail-on-budget 必须与 --max-tokens 一起使用')
    project_root = args.project_root.resolve()
    try:
        result = {'project_root': str(project_root)}
        if args.stage:
            module = load_sibling('context-pack.py', 'context_pack_for_budget')
            bundle_root = (args.bundle_root or module.ROOT).resolve()
            manifest = module.load_manifest(bundle_root)
            applicability_path = args.applicability_json
            if applicability_path and not applicability_path.is_absolute():
                applicability_path = project_root / applicability_path
            applicability = module.parse_json_mapping(applicability_path)
            pack_names, section_ids = module.resolve_selection(
                manifest, args.stage, args.mode, args.pass_name, args.pack,
                args.card, args.example, applicability,
            )
            sections = module.build_sections(bundle_root, manifest, args.stage, section_ids)
            result['runtime'] = {
                'stage': args.stage,
                'mode': args.mode,
                'pass': args.pass_name,
                'packs': pack_names,
                'sections': section_ids,
                'sources': sorted({item['source'] for item in sections}),
                'source_file_count': len({item['source'] for item in sections}),
                'section_count': len(sections),
                'characters': sum(item['characters'] for item in sections),
                'lines': sum(item['lines'] for item in sections),
                'tokens': module.estimate_tokens('\n'.join(item['content'] for item in sections)),
            }
        static_files = list(args.files)
        input_files = list(args.input)
        if static_files:
            result['static'] = measure_files(project_root, static_files)
        if input_files:
            result['business_input'] = measure_files(project_root, input_files)
        if not args.stage and not static_files and not input_files:
            parser.error('至少指定 --stage、--files 或 --input')
        if args.max_tokens is not None and args.max_tokens < 0:
            parser.error('--max-tokens 不能为负数')
        if args.max_tokens is not None:
            measured_sections = [result[key] for key in ('runtime', 'static', 'business_input') if key in result]
            total_tokens = sum(section['tokens'] for section in measured_sections)
            result['budget'] = {
                'max_tokens': args.max_tokens,
                'tokens': total_tokens,
                'within_budget': total_tokens <= args.max_tokens,
                'method': 'heuristic-cjk-0.6-non-cjk-0.25',
            }
            if args.fail_on_budget and total_tokens > args.max_tokens:
                raise RuntimeError(f'上下文估算约 {total_tokens} token，超过预算 {args.max_tokens} token')
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"项目根目录: {result['project_root']}")
            for key, label in (('runtime', '运行时上下文'), ('static', '静态文件'), ('business_input', '业务输入')):
                section = result.get(key)
                if not section:
                    continue
                file_count = section.get('file_count', section.get('source_file_count', 0))
                print(f"{label}: {file_count} 个文件, {section['characters']} 字符, {section['lines']} 行, 约 {section['tokens']} token")
        return 0
    except (RuntimeError, OSError) as exc:
        print(f'上下文预算统计失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
