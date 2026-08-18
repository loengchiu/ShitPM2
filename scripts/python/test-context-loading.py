from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK_SCRIPT = ROOT / 'scripts/python/context-pack.py'
MARKER_RE = re.compile(r'<!--\s*context:([A-Za-z0-9_.-]+):(start|end)\s*-->')
FAILURES: list[str] = []


def fail(message: str) -> None:
    FAILURES.append(message)


def load_pack_module():
    spec = importlib.util.spec_from_file_location('context_pack', PACK_SCRIPT)
    if spec is None or spec.loader is None:
        fail(f'无法加载上下文装载器: {PACK_SCRIPT}')
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_manifest(module) -> None:
    try:
        manifest = module.load_manifest(ROOT)
    except Exception as exc:
        fail(str(exc))
        return
    sections = manifest.get('sections', {})
    roles = manifest.get('subagent_roles', {})
    for role, role_spec in roles.items():
        for stage, stage_rules in role_spec.get('allowed', {}).items():
            if stage not in manifest.get('stages', {}):
                fail(f'Sub-agent 角色 {role} 引用不存在阶段: {stage}')
                continue
            stage_spec = manifest['stages'][stage]
            for pass_name in stage_rules.get('passes', []):
                if pass_name not in stage_spec.get('passes', {}):
                    fail(f'Sub-agent 角色 {role} 引用不存在 pass: {stage}.{pass_name}')
            for pack_name in stage_rules.get('packs', []):
                if pack_name not in stage_spec.get('packs', {}):
                    fail(f'Sub-agent 角色 {role} 引用不存在 pack: {stage}.{pack_name}')
    if not sections:
        fail('manifest.sections 为空')
        return
    referenced: set[str] = set()
    for stage, stage_spec in manifest.get('stages', {}).items():
        for pass_name, pack_names in stage_spec.get('passes', {}).items():
            for pack_name in pack_names:
                if pack_name not in stage_spec.get('packs', {}):
                    fail(f'{stage}.{pass_name} 引用不存在 pack: {pack_name}')
        for pack_name, pack in stage_spec.get('packs', {}).items():
            ids = list(pack.get('sections', []))
            for mode_ids in pack.get('mode_sections', {}).values():
                ids.extend(mode_ids)
            for card_ids in pack.get('card_sections', {}).values():
                ids.extend(card_ids)
            for example_ids in pack.get('example_sections', {}).values():
                ids.extend(example_ids)
            for section_id in ids:
                referenced.add(section_id)
                if section_id not in sections:
                    fail(f'{stage}.{pack_name} 引用未定义章节: {section_id}')
                elif sections[section_id].get('stage') != stage:
                    fail(f'章节阶段不匹配: {section_id}')
    # 跨 pack 重用章节必须显式标记，避免维护时把误复制误认为合法共享。
    section_consumers: dict[str, list[str]] = {}
    for stage, stage_spec in manifest.get('stages', {}).items():
        for pack_name, pack in stage_spec.get('packs', {}).items():
            ids = list(pack.get('sections', []))
            for mode_ids in pack.get('mode_sections', {}).values():
                ids.extend(mode_ids)
            for card_ids in pack.get('card_sections', {}).values():
                ids.extend(card_ids)
            for example_ids in pack.get('example_sections', {}).values():
                ids.extend(example_ids)
            for section_id in ids:
                section_consumers.setdefault(section_id, []).append(f'{stage}/{pack_name}')
    for section_id, consumers in section_consumers.items():
        if len(consumers) > 1 and not sections.get(section_id, {}).get('shared', False):
            fail(f'章节被多个 pack 引用但未标记 shared: {section_id} -> {", ".join(consumers)}')

    for section_id, spec in sections.items():
        source = ROOT / spec.get('source', '')
        if not source.is_file():
            fail(f'章节来源不存在: {section_id} -> {source}')
            continue
        text = source.read_text(encoding='utf-8-sig')
        selector = spec.get('selector', 'marker')
        if selector == 'marker':
            start = f'<!-- context:{section_id}:start -->'
            end = f'<!-- context:{section_id}:end -->'
            if text.count(start) != 1 or text.count(end) != 1:
                fail(f'章节标记不完整: {section_id} -> {source}')
            else:
                begin = text.index(start) + len(start)
                finish = text.index(end, begin)
                if not text[begin:finish].strip():
                    fail(f'章节内容为空: {section_id} -> {source}')
        elif selector != 'whole':
            fail(f'不支持的 selector: {section_id}={selector}')
    # manifest 中允许保留未来只被显式 pack 调用的章节，但当前版本不允许孤立资源。
    for section_id in sections:
        if section_id not in referenced:
            fail(f'章节未被任何 pack 引用: {section_id}')


def check_selection(module) -> None:
    try:
        manifest = module.load_manifest(ROOT)
        cases = [
            ('design', 'simple', 'analysis', [], []),
            ('design', 'full', 'writing', ['state', 'permissions'], []),
            ('prd', None, 'writing', [], []),
            ('prd', None, 'module', ['scenes'], []),
        ]
        for stage, mode, pass_name, cards, examples in cases:
            _, section_ids = module.resolve_selection(manifest, stage, mode, pass_name, [], cards, examples, None)
            if len(section_ids) != len(set(section_ids)):
                fail(f'选择结果含重复章节: {stage}.{pass_name}')
            if stage == 'prd' and pass_name == 'module':
                for required in ('prd-example-simple-readonly', 'prd-example-multi-role-state'):
                    if required not in section_ids:
                        fail(f'module pass 未自动装载写作示例: {required}')
                for forbidden in (
                    'prd-example-dashboard', 'prd-example-external-auto', 'prd-template', 'prd-profile',
                    'prd-writing-versioning', 'prd-writing-glossary', 'prd-writing-structure',
                ):
                    if forbidden in section_ids:
                        fail(f'module pass 不应装载章节: {forbidden}')
            sections = module.build_sections(ROOT, manifest, stage, section_ids)
            if not sections:
                fail(f'选择结果为空: {stage}.{pass_name}')
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / stage
                selected_packs, pack_sections = module.resolve_pack_sections(
                    manifest, stage, mode, pass_name, [], cards, examples, None,
                )
                record = module.write_run(
                    ROOT, stage, mode, pass_name, selected_packs, pack_sections,
                    sections, output_dir, None, role=None,
                )
                verification = module.verify_run(ROOT, stage, output_dir)
                if not verification['valid']:
                    fail(f'新生成运行包被判定为陈旧: {stage}.{pass_name}')
                stale_path = output_dir / 'stale-manifest.json'
                record_data = json.loads((output_dir / 'run.json').read_text(encoding='utf-8-sig'))
                record_data['manifest_hash'] = '0' * 64
                stale_path.write_text(json.dumps(record_data, ensure_ascii=False), encoding='utf-8')
                stale_check = module.verify_run(ROOT, stage, stale_path)
                if stale_check['valid']:
                    fail(f'manifest 变化未被陈旧检查识别: {stage}.{pass_name}')
        authorized_cases = [
            ('material-reader', 'design', 'simple', 'analysis'),
            ('design-challenger', 'design', 'full', 'challenge'),
            ('prd-module-writer', 'prd', None, 'module'),
        ]
        for role, stage, mode, pass_name in authorized_cases:
            try:
                module.resolve_selection(manifest, stage, mode, pass_name, [], [], [], None, role)
            except RuntimeError as exc:
                fail(f'角色白名单合法请求被拒绝: {role}: {exc}')
        unauthorized_cases = [
            ('design-challenger', 'design', 'full', 'writing'),
            ('prd-module-writer', 'prd', None, 'writing'),
            ('material-reader', 'prd', None, 'writing'),
        ]
        for role, stage, mode, pass_name in unauthorized_cases:
            try:
                module.resolve_selection(manifest, stage, mode, pass_name, [], [], [], None, role)
            except RuntimeError:
                pass
            else:
                fail(f'角色白名单越界未阻断: {role} -> {stage}.{pass_name}')
        try:
            module.resolve_selection(manifest, 'design', None, 'analysis', [], [], [], None)
        except RuntimeError:
            pass
        else:
            fail('缺少 --mode 时未阻断 Design 选择')
        try:
            module.resolve_selection(manifest, 'design', 'full', None, ['design-core'], [], [], None, 'material-reader')
        except RuntimeError:
            pass
        else:
            fail('带 --role 但缺少 --pass 时未阻断角色选择')
        try:
            module.validate_output_dir(ROOT, 'design', ROOT)
        except RuntimeError:
            pass
        else:
            fail('项目根目录被错误允许作为上下文输出目录')
    except Exception as exc:
        fail(f'选择测试异常: {exc}')


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f'无法加载测试脚本: {path}')
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_runtime_script_behaviors() -> None:
    prototype = load_module(ROOT / 'scripts/python/prototype-structure.py', 'prototype_structure_test')
    budget = load_module(ROOT / 'scripts/python/context-budget.py', 'context_budget_test')
    stage = load_module(ROOT / 'scripts/python/stage-context.py', 'stage_context_test')
    if prototype is not None:
        parser = prototype.PrototypeParser()
        parser.feed(
            '<h2>订单</h2>'
            '<a href="rel.html">相对页面</a>'
            '<a href="foo/bar">嵌套页面</a>'
            '<a href="https://example.com">外部</a>'
            '<a data-route="/orders">订单</a>'
            '<button data-action="save">保存</button>'
            '<input name="title" placeholder="标题">'
        )
        if parser.routes != ['rel.html', 'foo/bar', '/orders']:
            fail(f'Prototype 相对路由提取错误: {parser.routes}')
        if not parser.headings or parser.headings[0]['text'] != '订单':
            fail(f'Prototype 标题提取错误: {parser.headings}')
        if not parser.actions or parser.actions[0].get('data_action') != 'save':
            fail(f'Prototype 动作提取错误: {parser.actions}')
        if not parser.fields or parser.fields[0].get('name') != 'title':
            fail(f'Prototype 字段提取错误: {parser.fields}')
    if budget is not None:
        chinese = budget.estimate_tokens('中文' * 100)
        english = budget.estimate_tokens('ab' * 100)
        if chinese < 100 or chinese <= english:
            fail(f'预算估算未对中文采取保守系数: 中文={chinese}, 非中文={english}')
    pack = load_pack_module()
    if pack is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            import subprocess
            command = [
                sys.executable, str(PACK_SCRIPT), '--bundle-root', str(ROOT),
                '--project-root', str(ROOT), '--stage', 'design', '--mode', 'simple',
                '--pass', 'analysis', '--max-tokens', '1', '--dry-run',
            ]
            completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            if completed.returncode != 0:
                fail(f'context-pack dry-run 预算测试失败: {completed.stderr.strip()}')
            else:
                try:
                    dry_run = json.loads(completed.stdout)
                    if dry_run.get('budget', {}).get('within_budget') is not False:
                        fail(f'context-pack dry-run 未输出超预算结果: {dry_run}')
                except json.JSONDecodeError as exc:
                    fail(f'context-pack dry-run 输出不是 JSON: {exc}')
    if stage is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_bundle = Path(temp_dir) / 'bundle'
            result = stage.collect_context(ROOT, bundle_root=custom_bundle)
            actual = Path(result['bundle_resources']['bundle_root'])
            if actual != custom_bundle.resolve():
                fail(f'stage-context 未使用 --bundle-root 覆盖: {actual}')
            prd_read_set = result['minimal_read_set']
            if 'scripts/python/prototype-structure.py' in prd_read_set:
                fail('PRD 最小读取集合仍依赖 Prototype 结构提取')


def check_no_runtime_in_product() -> None:
    for rel in ('output/design/设计地图.md', 'output/prd/prd.md', 'output/prototype/index.html'):
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8-sig')
        for marker in ('context pack:', 'source-hash:', '.workflow/runtime/context'):
            if marker in text:
                fail(f'产品产物出现运行时上下文标记: {rel}:{marker}')


def build_sample_design(root: Path, *, large: bool = False) -> Path:
    """构造多文件 Design 集：设计地图 + 系统级基线 + 跨模块契约 + 两个模块。"""
    design_dir = root / 'output/design'
    (design_dir / '系统级基线').mkdir(parents=True, exist_ok=True)
    (design_dir / '跨模块契约').mkdir(parents=True, exist_ok=True)
    (design_dir / '模块设计' / '订单').mkdir(parents=True, exist_ok=True)
    (design_dir / '模块设计' / '库存').mkdir(parents=True, exist_ok=True)
    fill = 400 if large else 40
    map_text = '\n'.join([
        '# 设计地图',
        '',
        '## 一、系统目标与边界',
        '',
        '订单与库存管理系统。',
        '',
        '## 二、主业务链',
        '',
        '订单处理 → 库存管理',
        '',
        '## 三、模块与职责',
        '',
        '- MOD-001 [订单](模块设计/订单/订单管理.md)：负责订单处理。',
        '- MOD-002 [库存](模块设计/库存/库存管理.md)：负责库存管理。',
        '',
        '## 四、跨模块契约',
        '',
        '- CON-001 [订单与库存](跨模块契约/订单与库存.md)：定义订单扣减库存的交接。',
    ])
    map_path = design_dir / '设计地图.md'
    map_path.write_text(map_text, encoding='utf-8')
    sys_text = '# 系统级基线：系统边界\n\n本系统只处理订单和库存。\n'
    (design_dir / '系统级基线' / '系统边界.md').write_text(sys_text, encoding='utf-8')
    contract_text = '\n'.join([
        '# 跨模块契约：订单与库存',
        '',
        '## 一、交接双方与触发条件',
        '',
        '订单模块提交订单时触发库存扣减。',
        '',
        '## 二、状态衔接',
        '',
        '扣减成功则订单转为已提交。',
    ])
    (design_dir / '跨模块契约' / '订单与库存.md').write_text(contract_text, encoding='utf-8')
    order_lines = ['# 模块设计：订单管理', '## 一、模块职责与边界', '负责订单处理。', '## 二、模块业务闭环', '### 订单创建闭环', '#### 流程速览', '下单到发货闭环。']
    order_lines += [f'订单处理内容 {i}' for i in range(fill)]
    order_path = design_dir / '模块设计' / '订单' / '订单管理.md'
    order_path.write_text('\n'.join(order_lines), encoding='utf-8')
    stock_lines = ['# 模块设计：库存管理', '## 一、模块职责与边界', '负责库存管理。', '## 二、模块业务闭环', '### 库存扣减闭环', '#### 流程速览', '入库到出库闭环。']
    stock_lines += [f'库存管理内容 {i}' for i in range(fill)]
    stock_path = design_dir / '模块设计' / '库存' / '库存管理.md'
    stock_path.write_text('\n'.join(stock_lines), encoding='utf-8')
    import hashlib
    def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {
        'schema_version': 'shitpm-design-set/v1',
        'set_sha256': '',
        'files': [
            {'id': 'MAP-001', 'path': '设计地图.md', 'type': 'map', 'module': None, 'business_chains': [], 'depends_on': [], 'sha256': sha(map_path)},
            {'id': 'SYS-001', 'path': '系统级基线/系统边界.md', 'type': 'system', 'module': None, 'business_chains': [], 'depends_on': [], 'sha256': sha(design_dir / '系统级基线' / '系统边界.md')},
            {'id': 'CON-001', 'path': '跨模块契约/订单与库存.md', 'type': 'contract', 'module': None, 'business_chains': ['订单业务链'], 'depends_on': ['SYS-001'], 'sha256': sha(design_dir / '跨模块契约' / '订单与库存.md')},
            {'id': 'MOD-001', 'path': '模块设计/订单/订单管理.md', 'type': 'module', 'module': '订单', 'business_chains': ['订单业务链'], 'depends_on': ['SYS-001', 'CON-001'], 'sha256': sha(order_path)},
            {'id': 'MOD-002', 'path': '模块设计/库存/库存管理.md', 'type': 'module', 'module': '库存', 'business_chains': ['订单业务链'], 'depends_on': ['SYS-001', 'CON-001'], 'sha256': sha(stock_path)},
        ],
        'decisions': [],
    }
    parts = []
    for f in sorted(manifest['files'], key=lambda x: x['id']):
        parts.append(f['id'] + f['path'] + f['sha256'])
    manifest['set_sha256'] = hashlib.sha256(''.join(parts).encode('utf-8')).hexdigest()
    manifest_path = design_dir / '设计集清单.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return map_path


def check_design_fragment(module) -> None:
    """按模块事实闭包装载的确定性行为测试（计划 6.2 功能验收）。"""
    import subprocess
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_sample_design(root)
        fragment = module.extract_design_fragment(str(root), '订单')
        content = fragment['content']
        if not content.strip():
            fail('模块闭包片段为空')
        if 'SYS-001' not in content or 'CON-001' not in content or 'MOD-001' not in content:
            fail('模块闭包未包含系统基线、契约和目标模块')
        if '库存管理' in content:
            fail('模块闭包包含无关模块正文')
        if fragment['lines'] <= 0:
            fail('模块闭包行数异常')
        if 'MOD-002' in fragment['fragment_meta']['closure_ids']:
            fail('闭包混入无关模块 MOD-002')
        try:
            module.extract_design_fragment(str(root), '不存在的模块xyz')
            fail('匹配不到模块时未报错')
        except RuntimeError as exc:
            message = str(exc)
            if '订单' not in message and '库存' not in message:
                fail(f'匹配失败报错未列出已登记模块: {message[:80]}')
        command = [
            sys.executable, str(PACK_SCRIPT), '--bundle-root', str(ROOT),
            '--project-root', str(root), '--stage', 'prd', '--pass', 'module',
            '--card', 'scenes', '--module', '订单', '--dry-run',
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        if completed.returncode != 0:
            fail(f'context-pack --module CLI 失败: {completed.stderr.strip()}')
        else:
            try:
                dry = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                fail(f'context-pack --module 输出不是 JSON: {exc}')
            else:
                ids = dry.get('sections', [])
                if 'design-fragment:订单' not in ids:
                    fail(f'CLI 未装载 design-fragment 章节: {ids}')
                if dry.get('module') != '订单':
                    fail('CLI 未记录 module 字段')
        command = [
            sys.executable, str(PACK_SCRIPT), '--bundle-root', str(ROOT),
            '--project-root', str(root), '--stage', 'prd', '--pass', 'module',
            '--card', 'scenes', '--module', '订单',
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        if completed.returncode != 0:
            fail(f'context-pack --module 写入失败: {completed.stderr.strip()}')
        verify = subprocess.run(
            [sys.executable, str(PACK_SCRIPT), '--bundle-root', str(ROOT),
             '--project-root', str(root), '--stage', 'prd', '--verify-run'],
            capture_output=True, text=True, encoding='utf-8',
        )
        try:
            result = json.loads(verify.stdout)
        except json.JSONDecodeError as exc:
            fail(f'verify-run 输出不是 JSON: {exc}')
        else:
            if not result.get('valid'):
                fail(f'--module 写入后被 verify 判定陈旧: {result.get("stale")}')

def main() -> int:
    module = load_pack_module()
    if module:
        check_manifest(module)
        check_selection(module)
        check_design_fragment(module)
    check_runtime_script_behaviors()
    check_no_runtime_in_product()
    if FAILURES:
        print(f'上下文装载测试失败：{len(FAILURES)} 项')
        for item in FAILURES:
            print(f'- {item}')
        return 1
    print('上下文装载测试通过：manifest、章节标记、来源、选择去重、--module 分片和产品边界均正常')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
