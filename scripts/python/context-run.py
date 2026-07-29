from __future__ import annotations

"""记录隔离上下文阶段的机器耗时和输入体量。"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from token_estimate import estimate_tokens



def resolve_files(project_root: Path, values: list[str]) -> list[Path]:
    result = []
    for value in values:
        path = Path(value)
        if not path.is_absolute():
            path = project_root / path
        path = path.resolve()
        if not path.is_file():
            raise RuntimeError(f'指标输入不存在: {path}')
        result.append(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description='记录 ShitPM 隔离上下文阶段指标')
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--stage', required=True)
    parser.add_argument('--pass', dest='pass_name', required=True)
    parser.add_argument('--status', choices=['started', 'completed', 'failed'], required=True)
    parser.add_argument('--input', action='append', default=[])
    parser.add_argument('--handoff', action='append', default=[])
    parser.add_argument('--duration-ms', type=int)
    parser.add_argument('--reused-material-assets', action='store_true')
    parser.add_argument('--material-revision')
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    files = resolve_files(project_root, args.input + args.handoff)
    now = datetime.now(timezone.utc)
    record = {
        'version': 1,
        'stage': args.stage,
        'pass': args.pass_name,
        'status': args.status,
        'recorded_at': now.isoformat(),
        'duration_ms': args.duration_ms,
        'reused_material_assets': args.reused_material_assets,
        'material_revision': args.material_revision,
        'inputs': [
            {
                'path': str(path.relative_to(project_root).as_posix()) if path.is_relative_to(project_root) else str(path),
                'characters': len(path.read_text(encoding='utf-8-sig')),
                'tokens': estimate_tokens(path.read_text(encoding='utf-8-sig')),
            }
            for path in files
        ],
    }
    record['input_tokens'] = sum(item['tokens'] for item in record['inputs'])
    metrics_dir = project_root / '.workflow' / 'runtime' / 'metrics'
    metrics_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime('%Y%m%dT%H%M%S%fZ')
    out = metrics_dir / f'{stamp}-{args.stage}-{args.pass_name}-{args.status}.json'
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'metric': str(out), **record}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
