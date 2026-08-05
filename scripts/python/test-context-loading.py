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
    for rel in ('output/design/design.md', 'output/prd/prd.md', 'output/prototype/index.html'):
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8-sig')
        for marker in ('context pack:', 'source-hash:', '.workflow/runtime/context'):
            if marker in text:
                fail(f'产品产物出现运行时上下文标记: {rel}:{marker}')


def build_sample_design(root: Path, *, large: bool = False) -> Path:
    """构造多闭环、多页面、含共用对象/权限/页面清单/待确认的 design.md 样本。"""
    design_dir = root / 'output/design'
    design_dir.mkdir(parents=True, exist_ok=True)
    lines = ['# 产品方案设计', '## 一、方案摘要', '### 要解决的问题', '测试样本']
    fill = 400 if large else 40
    lines += [
        '## 四、关键业务闭环',
        '### 闭环一：订单处理',
        '#### 流程速览',
        '下单到发货闭环。',
        '涉及页面：订单列表、订单详情',
    ]
    lines += [f'订单处理内容 {i}' for i in range(fill)]
    lines += ['### 闭环二：库存管理', '#### 流程速览', '入库到出库闭环。', '涉及页面：库存列表']
    lines += [f'库存管理内容 {i}' for i in range(fill)]
    lines += ['## 五、业务对象、规则与状态', '### 核心业务对象及关系']
    lines += [f'对象规则内容 {i}' for i in range(fill)]
    lines += ['### 关键对象生命周期与状态', '### 状态机：订单']
    lines += [f'状态机内容 {i}' for i in range(50)]
    lines += ['## 六、角色、权限与数据范围', '### 默认权限与角色例外', '订单角色：订单处理员', '库存角色：库存管理员']
    lines += ['## 七、页面、区块、字段与操作设计', '### 页面清单', '| 页面 | 用户任务 |', '| --- | --- |']
    lines += ['| 订单列表 | 查看订单 |', '| 订单详情 | 查看订单详情 |', '| 库存列表 | 查看库存 |']
    for page in ('订单列表', '订单详情', '库存列表'):
        lines += [f'### 页面：{page}', f'- 页面目的：{page}相关']
        lines += [f'{page}内容 {i}' for i in range(30)]
    lines += ['### 待确认事项', '无']
    lines += ['## 十、方案权衡、风险与待确认', '### 待确认事项', '订单状态流转冲突待确认']
    path = design_dir / 'design.md'
    path.write_text('\n'.join(lines), encoding='utf-8')
    return path


def build_page_heavy_design(root: Path) -> Path:
    """构造闭环/共用小、页面大的 design.md 样本：验证页面行数计入片段阈值（P1-1 回归防线）。"""
    design_dir = root / 'output/design'
    design_dir.mkdir(parents=True, exist_ok=True)
    lines = ['# 产品方案设计', '## 一、方案摘要', '### 要解决的问题', '测试样本']
    lines += [
        '## 四、关键业务闭环',
        '### 闭环一：订单处理',
        '#### 流程速览',
        '下单到发货闭环。',
        '涉及页面：订单列表、订单详情、订单编辑、订单删除、订单导出、订单导入',
    ]
    lines += ['订单处理内容'] * 30
    lines += ['### 闭环二：库存管理', '#### 流程速览', '入库到出库闭环。', '涉及页面：库存列表']
    lines += ['库存管理内容'] * 30
    lines += ['## 五、业务对象、规则与状态', '### 核心业务对象及关系']
    lines += ['对象规则内容'] * 30
    lines += ['## 七、页面、区块、字段与操作设计', '### 页面清单', '| 页面 | 用户任务 |', '| --- | --- |']
    page_names = ['订单列表', '订单详情', '订单编辑', '订单删除', '订单导出', '订单导入']
    for page in page_names:
        lines.append(f'| {page} | 查看订单 |')
    for page in page_names:
        lines += [f'### 页面：{page}', f'- 页面目的：{page}相关']
        lines += [f'{page}内容 {i}' for i in range(150)]
    lines += ['### 待确认事项', '无']
    path = design_dir / 'design.md'
    path.write_text('\n'.join(lines), encoding='utf-8')
    return path


def check_design_fragment(module) -> None:
    """--module 分片提取的确定性行为测试（计划 6.2 功能验收）。"""
    import subprocess
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_sample_design(root)
        full_text = (root / 'output/design/design.md').read_text(encoding='utf-8')
        full_lines = len(full_text.splitlines())
        fragment = module.extract_design_fragment(str(root), '订单处理')
        content = fragment['content']
        if not content.strip():
            fail('--module 提取片段为空')
        if '模块闭环：闭环一：订单处理' not in content:
            fail('--module 片段未包含目标闭环内容')
        if '模块闭环：闭环二：库存管理' in content:
            fail('--module 片段包含无关闭环内容')
        if '相关页面：库存列表' in content:
            fail('--module 片段包含无关页面章节')
        if '相关页面：订单列表' not in content or '相关页面：订单详情' not in content:
            fail('--module 片段未包含目标闭环相关页面')
        if fragment['lines'] <= 0 or fragment['lines'] > full_lines:
            fail(f'--module 片段行数异常: {fragment["lines"]}')
        if full_lines >= 1000 and fragment['lines'] > full_lines // 3:
            fail(f'大 Design 片段未显著小于全文: {fragment["lines"]}/{full_lines}')
        # --pages 显式追加页面：闭环匹配成功后同样生效（P1-2 回归防线）
        appended = module.extract_design_fragment(str(root), '订单处理', extra_pages=['库存列表'])
        if '相关页面：库存列表' not in appended['content']:
            fail('--pages 显式追加页面未生效（闭环匹配时）')
        # 显式闭环映射优先：闭环正文不引用页面名时，仍按映射装载相关页面，且不混入无关页面
        with tempfile.TemporaryDirectory() as map_dir:
            map_root = Path(map_dir)
            build_sample_design(map_root)
            map_design = map_root / 'output/design/design.md'
            map_text = map_design.read_text(encoding='utf-8')
            map_text = map_text.replace('涉及页面：订单列表、订单详情', '页面由映射文件指定')
            map_design.write_text(map_text, encoding='utf-8')
            mapping_file = map_root / 'prd-module-map.json'
            mapping_file.write_text(json.dumps({
                'closures': {'闭环一：订单处理': ['订单列表', '订单详情']},
            }, ensure_ascii=False), encoding='utf-8')
            mapped = module.extract_design_fragment(
                str(map_root), '订单处理', mapping=module.parse_closure_mapping(mapping_file),
            )
            if '相关页面：订单列表' not in mapped['content'] or '相关页面：订单详情' not in mapped['content']:
                fail('显式闭环映射未装载目标相关页面')
            if '库存列表' in mapped['content']:
                fail('显式闭环映射装载了无关页面')
        # 页面清单共用部分按模块页面名过滤：不携带全量清单行（P2-2）
        if '| 库存列表 |' in content:
            fail('页面清单共用部分未按模块页面名过滤')
        # 模板格式标题"页面清单（可选速览）"同样被识别并过滤（P2-2 兼容）
        with tempfile.TemporaryDirectory() as tpl_dir:
            tpl_root = Path(tpl_dir)
            build_sample_design(tpl_root)
            tpl_design = tpl_root / 'output/design/design.md'
            tpl_text = tpl_design.read_text(encoding='utf-8')
            tpl_text = tpl_text.replace('### 页面清单', '### 页面清单（可选速览）')
            tpl_design.write_text(tpl_text, encoding='utf-8')
            tpl_frag = module.extract_design_fragment(str(tpl_root), '订单处理')
            if '共用部分：页面清单（可选速览）' not in tpl_frag['content']:
                fail('模板标题"页面清单（可选速览）"未被识别为共用部分')
            if '| 库存列表 |' in tpl_frag['content']:
                fail('模板标题下页面清单未按模块页面名过滤')
        # 闭环字母编号（闭环A/B/C）可匹配（P2-1）
        with tempfile.TemporaryDirectory() as alpha_dir:
            alpha_root = Path(alpha_dir)
            build_sample_design(alpha_root)
            alpha_design = alpha_root / 'output/design/design.md'
            alpha_text = alpha_design.read_text(encoding='utf-8')
            alpha_text = alpha_text.replace('### 闭环一：订单处理', '### 闭环A：订单处理')
            alpha_design.write_text(alpha_text, encoding='utf-8')
            alpha_frag = module.extract_design_fragment(str(alpha_root), '订单处理')
            if '模块闭环：闭环A：订单处理' not in alpha_frag['content']:
                fail('闭环字母编号（闭环A）未能匹配')
        # 模块名匹配不到闭环时按页面名兜底
        page_fragment = module.extract_design_fragment(str(root), '订单详情')
        if '相关页面：订单详情' not in page_fragment['content']:
            fail('页面名兜底未提取目标页面')
        # 匹配不到任何章节时报错并列出标题清单，不静默返回空
        try:
            module.extract_design_fragment(str(root), '不存在的模块xyz')
            fail('匹配不到模块时未报错')
        except RuntimeError as exc:
            message = str(exc)
            if '闭环一' not in message or '订单列表' not in message:
                fail(f'匹配失败报错未列出标题清单: {message[:80]}')
        # 大 Design 超阈值时报错提示拆分，不静默截断
        with tempfile.TemporaryDirectory() as big_dir:
            big_root = Path(big_dir)
            build_sample_design(big_root, large=True)
            try:
                module.extract_design_fragment(str(big_root), '订单处理')
            except RuntimeError as exc:
                if '拆分' not in str(exc):
                    fail(f'大模块超阈值报错未提示拆分: {str(exc)[:80]}')
            else:
                fail('大模块超阈值未报错')
        # 页面大模块超阈值（闭环/共用小、页面多行）：页面行数必须计入片段规模（P1-1 回归防线）
        with tempfile.TemporaryDirectory() as page_big_dir:
            page_big_root = Path(page_big_dir)
            build_page_heavy_design(page_big_root)
            try:
                module.extract_design_fragment(str(page_big_root), '订单处理')
            except RuntimeError as exc:
                if '拆分' not in str(exc):
                    fail(f'页面大模块超阈值报错未提示拆分: {str(exc)[:80]}')
            else:
                fail('页面大模块未报错：页面行数未计入片段阈值')
        # CLI 全链路：--module 与 --pass module --card scenes 组合输出规则 + 清单 + 片段
        command = [
            sys.executable, str(PACK_SCRIPT), '--bundle-root', str(ROOT),
            '--project-root', str(root), '--stage', 'prd', '--pass', 'module',
            '--card', 'scenes', '--module', '订单处理', '--dry-run',
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
                if 'design-fragment:订单处理' not in ids:
                    fail(f'CLI 未装载 design-fragment 章节: {ids}')
                if dry.get('module') != '订单处理':
                    fail(f'CLI 未记录 module 字段: {dry.get("module")}')
        # 非 dry-run 写入后 verify 不误报陈旧
        command = [
            sys.executable, str(PACK_SCRIPT), '--bundle-root', str(ROOT),
            '--project-root', str(root), '--stage', 'prd', '--pass', 'module',
            '--card', 'scenes', '--module', '订单处理',
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
