from __future__ import annotations

import json
import subprocess
import time
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / 'scripts/python/source-index.py'
CHECK = ROOT / 'scripts/python/context-runtime-check.py'


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, encoding='utf-8')


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def prepare(project: Path, *inputs: Path, force: bool = False) -> dict:
    args = [str(INDEX), '--project-root', str(project)]
    for item in inputs:
        args.extend(['--input', str(item)])
    if force:
        args.append('--force')
    result = run(*args, cwd=ROOT)
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        project = Path(temp)
        materials = project / 'materials'
        materials.mkdir()
        first = materials / 'orders.md'
        second = materials / 'exceptions.md'
        first.write_text('# 订单流程\n提交订单后进入审核。\n\n## 状态\n审核中等待处理。\n', encoding='utf-8')
        second.write_text('# 异常\n审核失败需要补充材料。\n', encoding='utf-8')

        created = prepare(project, materials)
        if created['status'] != 'created' or created['material_changed'] is not True or len(created['added_sources']) != 2:
            print(f'首次生成结果错误: {created}')
            return 1
        if 'facts_path' in created or 'facts_reused' in created:
            print(f'材料索引不应越权记录 facts 生命周期: {created}')
            return 1
        manifest_path = project / '.workflow/runtime/materials/manifest.json'
        index_path = project / '.workflow/runtime/materials/source-index.json'
        if read(manifest_path)['material_revision'] != read(index_path)['material_revision']:
            print('manifest 与 source-index 版本不一致')
            return 1

        reused = prepare(project)
        if reused['status'] != 'reused' or not reused['assets_reused'] or len(reused['reused_sources']) != 2:
            print(f'未变化复用失败: {reused}')
            return 1

        force_durations = []
        reuse_durations = []
        for _ in range(5):
            started = time.perf_counter()
            forced = prepare(project, materials, force=True)
            force_durations.append((time.perf_counter() - started) * 1000)
            if forced['status'] != 'updated' or forced['assets_reused']:
                print(f'强制重建基准状态错误: {forced}')
                return 1
            started = time.perf_counter()
            reused_run = prepare(project)
            reuse_durations.append((time.perf_counter() - started) * 1000)
            if reused_run['status'] != 'reused' or not reused_run['assets_reused']:
                print(f'复用基准状态错误: {reused_run}')
                return 1

        first.write_text(first.read_text(encoding='utf-8') + '\n## 新规则\n需要补充联系人。\n', encoding='utf-8')
        changed = prepare(project, materials)
        if changed['status'] != 'updated' or changed['changed_sources'] != ['materials/orders.md'] or changed['reused_sources'] != ['materials/exceptions.md']:
            print(f'单来源变更识别失败: {changed}')
            return 1

        third = materials / 'new.md'
        third.write_text('# 新材料\n新增说明。\n', encoding='utf-8')
        added = prepare(project, materials)
        if added['added_sources'] != ['materials/new.md'] or len(added['reused_sources']) != 2:
            print(f'新增来源识别失败: {added}')
            return 1

        second.unlink()
        removed = prepare(project, materials)
        if removed['removed_sources'] != ['materials/exceptions.md']:
            print(f'删除来源识别失败: {removed}')
            return 1

        current_manifest = read(manifest_path)
        current_index = read(index_path)
        facts_path = project / '.workflow/runtime/materials/facts.json'
        facts_path.parent.mkdir(parents=True, exist_ok=True)
        facts = {
            'version': 1,
            'material_revision': current_manifest['material_revision'],
            'confirmed_facts': [{
                'statement': '提交订单后进入审核',
                'source': {
                    'path': 'materials/orders.md',
                    'sha256': next(item['sha256'] for item in current_manifest['sources'] if item['path'] == 'materials/orders.md'),
                    'line_start': 1,
                    'line_end': 2,
                },
            }],
            'source_conflicts': [],
            'missing_information': [],
            'non_derivable_items': [],
        }
        facts_path.write_text(json.dumps(facts, ensure_ascii=False), encoding='utf-8')
        checked = run(str(CHECK), '--project-root', str(project), '--require', 'material-manifest', '--require', 'material-index', '--require', 'material-facts', cwd=ROOT)
        if checked.returncode != 0:
            print(checked.stdout, checked.stderr)
            return 1

        bad = dict(facts)
        bad['material_revision'] = '0' * 64
        facts_path.write_text(json.dumps(bad, ensure_ascii=False), encoding='utf-8')
        rejected = run(str(CHECK), '--project-root', str(project), '--require', 'material-facts', cwd=ROOT)
        if rejected.returncode == 0:
            print('版本不匹配的材料事实未被拒绝')
            return 1

        bad_source = dict(facts)
        bad_source['material_revision'] = current_manifest['material_revision']
        bad_source['confirmed_facts'] = [{'statement': '无定位事实', 'source': {'path': 'missing.md', 'line_start': 1, 'line_end': 1}}]
        facts_path.write_text(json.dumps(bad_source, ensure_ascii=False), encoding='utf-8')
        rejected_source = run(str(CHECK), '--project-root', str(project), '--require', 'material-facts', cwd=ROOT)
        if rejected_source.returncode == 0:
            print('清单外来源的材料事实未被拒绝')
            return 1

        skill = (ROOT / 'skills/spm-design/SKILL.md').read_text(encoding='utf-8-sig')
        for marker in ('context-pack.py', 'context-loading.manifest.json', 'Align 完整对齐稿'):
            if marker not in skill:
                print(f'Design Skill 未接入当前分层上下文契约: {marker}')
                return 1

        if (project / '.workflow/runtime/context/design/source-index.json').exists():
            print('旧 Design 材料索引路径不应被创建')
            return 1

    print('项目级材料资产测试通过：首次生成、未变化复用、变更失效、增删来源和版本门禁均正常')
    print(f'材料资产计时冒烟：强制重建平均 {sum(force_durations) / len(force_durations):.1f} ms，复用平均 {sum(reuse_durations) / len(reuse_durations):.1f} ms（仅记录，不以小样例推断真实模型提速）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


