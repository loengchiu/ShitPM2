from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESOURCE_DIRS = [ROOT / "references", ROOT / "templates", ROOT / "contracts"]
FAILURES: list[str] = []


def fail(message: str) -> None:
    FAILURES.append(message)


def slug(text: str) -> str:
    text = re.sub(r"[`*_]", "", text.lower().strip())
    text = re.sub(r"[^\w\u4e00-\u9fff -]+", "", text)
    return re.sub(r"\s+", "-", text)


def check_resource_paths() -> None:
    path_pattern = re.compile(r"(?:\$BUNDLE/)?(?:references|templates|contracts)/[A-Za-z0-9._/-]+\.(?:md|json|html|py)")
    scan_roots = [ROOT / "skills", ROOT / "scripts", ROOT / "references", ROOT / "templates", ROOT / "contracts"]
    for base in scan_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".json"}:
                continue
            if path.name == "references-optimization-plan.md":
                continue
            text = path.read_text(encoding="utf-8")
            for raw in path_pattern.findall(text):
                rel = raw.removeprefix("$BUNDLE/")
                target = ROOT / rel
                if not target.exists():
                    fail(f"资源引用不存在: {path}:{raw}")


def check_markdown_links() -> None:
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for base in RESOURCE_DIRS:
        for path in base.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            headings = {slug(m.group(1)) for m in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", text)}
            for target in link_pattern.findall(text):
                target = target.strip()
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                if target.startswith("#"):
                    if target[1:] not in headings:
                        fail(f"锚点链接不存在: {path}:{target}")
                    continue
                target_path, _, fragment = target.partition("#")
                if target_path.startswith("$BUNDLE/"):
                    resolved = ROOT / target_path.removeprefix("$BUNDLE/")
                else:
                    resolved = (path.parent / target_path).resolve()
                if not resolved.exists():
                    fail(f"Markdown 链接目标不存在: {path}:{target}")
                if fragment and fragment not in {
                    slug(m.group(1)) for m in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", resolved.read_text(encoding="utf-8") if resolved.is_file() else "")
                }:
                    fail(f"Markdown 链接锚点不存在: {path}:{target}")


def check_long_file_tocs() -> None:
    for base in [ROOT / "references", ROOT / "contracts"]:
        for path in base.glob("*.md"):
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) > 100 and not any(line.strip() == "## 目录" for line in lines):
                fail(f"超过 100 行但缺少目录: {path}")


def check_stage_context() -> None:
    stage = ROOT / "scripts/python/stage-context.py"
    text = stage.read_text(encoding="utf-8")
    for rel in re.findall(r'"((?:references|templates|contracts)/[A-Za-z0-9._/-]+)"', text):
        if not (ROOT / rel).exists():
            fail(f"stage-context.py 读取集合路径不存在: {rel}")


def check_context_manifest() -> None:
    path = ROOT / "contracts/context-loading.manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"context-loading.manifest.json 不是有效 JSON: {exc}")
        return
    if data.get("version") != 1:
        fail("context-loading.manifest.json version 必须为 1")
    for rel in ("scripts/python/context-pack.py", "scripts/python/context-budget.py", "scripts/python/test-context-loading.py", "scripts/python/prototype-structure.py"):
        if not (ROOT / rel).is_file():
            fail(f"上下文装载工具不存在: {rel}")
    sections = data.get("sections", {})
    for section_id, spec in sections.items():
        if spec.get("shared") and not spec.get("reuse_note"):
            fail(f"共享上下文章节缺少 reuse_note: {section_id}")
    for section_id, spec in sections.items():
        source = ROOT / spec.get("source", "")
        if not source.is_file():
            fail(f"上下文章节来源不存在: {section_id} -> {source}")
            continue
        if spec.get("selector") == "marker":
            text = source.read_text(encoding="utf-8-sig")
            start = f"<!-- context:{section_id}:start -->"
            end = f"<!-- context:{section_id}:end -->"
            if text.count(start) != 1 or text.count(end) != 1:
                fail(f"上下文章节标记不完整: {section_id} -> {source}")


def check_contract_manifest_alignment() -> None:
    contract = ROOT / 'contracts/subagent-context-contract.md'
    manifest_path = ROOT / 'contracts/context-loading.manifest.json'
    text = contract.read_text(encoding='utf-8-sig')
    data = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    marker = '| 角色 | CLI 键 | 阶段与 pass | 允许 pack |'
    if marker not in text:
        fail('Sub-agent 契约缺少可解析的角色白名单表')
        return
    table = text.split(marker, 1)[1].split('\n\n', 1)[0]
    rows = {}
    for line in table.splitlines():
        if not line.startswith('|') or line.startswith('|---'):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) != 4:
            continue
        display, role_key, stage_passes, packs = cells
        role_key = role_key.strip('`')
        stage_matches = re.findall(r'(Design|PRD)\s+`([^`]+)`', stage_passes)
        stage_data = {stage.lower(): {pass_name} for stage, pass_name in stage_matches}
        if 'Design' not in stage_passes and 'PRD' not in stage_passes:
            stage_data = {}
        pack_groups = {}
        for stage_label, group in re.findall(r'(Design|PRD)：([^；]+)', packs):
            pack_groups[stage_label.lower()] = set(re.findall(r'`([^`]+)`', group))
        if not pack_groups:
            pack_groups = {'design': set(re.findall(r'`([^`]+)`', packs))}
        rows[role_key] = {'display': display, 'stages': stage_data, 'packs': pack_groups}
    manifest_roles = data.get('subagent_roles', {})
    if set(rows) != set(manifest_roles):
        fail(f'契约与 manifest 角色键不一致: contract={sorted(rows)}, manifest={sorted(manifest_roles)}')
        return
    for role_key, role_spec in manifest_roles.items():
        row = rows[role_key]
        for stage, rules in role_spec.get('allowed', {}).items():
            expected_passes = set(rules.get('passes', []))
            row_passes = {pass_name for pass_name in row['stages'].get(stage, set())}
            if row_passes != expected_passes:
                fail(f'契约与 manifest pass 不一致: {role_key}/{stage}: contract={sorted(row_passes)}, manifest={sorted(expected_passes)}')
            expected_packs = set(rules.get('packs', []))
            row_packs = row['packs'].get(stage, row['packs'].get('design', set()))
            if row_packs != expected_packs:
                fail(f'契约与 manifest pack 不一致: {role_key}/{stage}: contract={sorted(row_packs)}, manifest={sorted(expected_packs)}')


def check_context_consumers() -> None:
    for rel in ("skills/spm-design/SKILL.md", "skills/spm-prd/SKILL.md"):
        text = (ROOT / rel).read_text(encoding="utf-8-sig")
        if "context-pack.py" not in text or "context-loading.manifest.json" not in text:
            fail(f"Skill 未接入分层上下文装载器: {rel}")
    if "context-loading.manifest.json" not in (ROOT / "scripts/python/stage-context.py").read_text(encoding="utf-8-sig"):
        fail("stage-context.py 未暴露上下文 manifest")


def check_profile() -> None:
    path = ROOT / "contracts/prd-writing.profile.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"PRD profile 不是有效 JSON: {exc}")
        return
    if set(data.get("constraints", {})) != {"forbidden_expressions"}:
        fail("PRD profile 含未约定的 constraints 字段")
    if not isinstance(data.get("constraints", {}).get("forbidden_expressions"), list):
        fail("PRD profile.forbidden_expressions 不是数组")


def check_runtime_quality_standard() -> None:
    path = ROOT / "references/design-quality-rubric.md"
    text = path.read_text(encoding="utf-8")
    for marker in ("Park", "盲审"):
        if marker in text:
            fail(f"Design 运行时质量标准含版本对标内容: {path}:{marker}")
    required_boundaries = (
        "不读取、不要求也不比较任何外部基准产物",
        "不根据量表补写输入中不存在的产品事实",
        "生成自审只使用本文件的质量维度、缺陷等级和完成条件，不执行 L0–L3 正式评分",
    )
    for boundary in required_boundaries:
        if boundary not in text:
            fail(f"Design 运行时质量标准缺少职责边界: {boundary}")


def check_consumers() -> None:
    stale = re.compile(r"(?:\$BUNDLE/)?references/prd-writing\.md|references/prd-writing\.md")
    for base in [ROOT / "skills", ROOT / "scripts", ROOT / "contracts", ROOT / "references", ROOT / "templates"]:
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            if stale.search(text):
                fail(f"发现旧 PRD reference 引用: {path}")
    checks = {
        ROOT / "skills/spm-design-review/SKILL.md": "contracts/design-review-checklist.md",
        ROOT / "skills/spm-prd-review/SKILL.md": "contracts/prd-review-checklist.md",
        ROOT / "skills/spm-prototype-review/SKILL.md": "contracts/prototype-review-checklist.md",
    }
    for path, expected in checks.items():
        if expected not in path.read_text(encoding="utf-8"):
            fail(f"Review Skill 未引用专项 checklist: {path} -> {expected}")


def main() -> int:
    check_resource_paths()
    check_markdown_links()
    check_long_file_tocs()
    check_stage_context()
    check_context_manifest()
    check_contract_manifest_alignment()
    check_context_consumers()
    check_profile()
    check_runtime_quality_standard()
    check_consumers()
    if FAILURES:
        print(f"资源完整性检查失败：{len(FAILURES)} 项")
        for item in FAILURES:
            print(f"- {item}")
        return 1
    print("资源完整性检查通过：路径、链接、目录、profile、stage-context、运行时质量边界和消费者引用均正常")
    return 0


if __name__ == "__main__":
    sys.exit(main())
