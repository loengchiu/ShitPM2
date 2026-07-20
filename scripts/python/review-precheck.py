#!/usr/bin/env python3
"""review-precheck.py — reviewer 开始前的确定性预检查（vNext: 文件存在性与基础结构检查）

vNext 职责：
1. 检查人读稿文件存在性、可读性和基础结构（核心章节）。
2. 不决定是否允许 Review（can_start_review 仅基于文件存在性，不基于 metadata）。
3. 不要求 metadata 存在。metadata 检查仅在旧项目存在 metadata 时作为参考，记入 warnings。
4. vNext 主流程不生成 metadata，因此 metadata 检查不再是硬阻塞。

它不是：最终 review 结论、人读摘要、第二份 reviewer 报告。

用法：python review-precheck.py --stage <stage> [--project-root <path>]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from shared_md import ARTIFACT_PATHS, METADATA_FILE_MAP, strip_heading_number

VALID_STAGES = ["design", "prd", "prototype"]


METADATA_EMPTY_OK = {
    "design": {"relations.json"},
}

CORE_SECTIONS = {
    "design": ["角色定义", "模块定义", "页面清单", "字段定义", "页面与字段落点", "规则与状态定义", "权限定义"],
    "prd": ["名词说明", "详细需求说明"],
    "prototype": [],
}

SECTION_ALIASES = {
    "design": {
        "角色定义": ["角色定义", "角色权限", "角色", "角色清单", "角色与权限"],
        "模块定义": ["模块定义", "模块清单", "模块列表", "功能模块"],
        "页面清单": ["页面清单", "页面列表", "页面目录", "页面规划"],
        "字段定义": ["字段定义", "数据字典", "字段清单", "字段列表", "数据项定义"],
        "页面与字段落点": ["页面与字段落点", "页面数据落点", "字段落点", "页面字段映射", "页面字段落点"],
        "规则与状态定义": ["规则与状态定义", "规则定义", "状态定义", "状态流转", "状态机", "业务规则与状态"],
        "权限定义": ["权限定义", "角色权限", "权限矩阵", "权限", "权限规则", "权限清单"],
    },
    "prd": {
        "名词说明": ["名词说明", "术语说明", "术语表", "名词解释", "术语定义"],
        "详细需求说明": ["详细需求说明", "详细需求", "需求说明", "详细需求规格", "需求详细说明"],
    },
}


def check_prd_entity_coverage(project_root: Path, stdin_content: str = None) -> dict:
    """校验 PRD 是否覆盖 design 数据字典中的全部实体

    归位后实体字段表按小模块归位到 §5 详细需求说明。
    检查方式：design 数据字典的实体名在 PRD §5 正文中出现即算覆盖
    （实体名会出现在小模块末尾的字段表前、大模块标题或正文描述中）。
    """
    design_path = project_root / "output" / "design" / "design.md"
    if not design_path.exists():
        return {"check": "prd_entity_coverage", "passed": False, "detail": "design.md 不存在"}

    with open(design_path, encoding="utf-8") as f:
        design_content = f.read()

    # Extract entity names from design.md data dictionary section
    design_entities = set()
    in_dd = False
    dd_heading_level = 0
    for line in design_content.split(chr(10)):
        stripped = line.strip()
        m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        # 精确匹配：标题去除编号后与别名完全相等，避免子串误匹配
        title_no_prefix = strip_heading_number(title)
        if any(title_no_prefix == alias or title == alias for alias in SECTION_ALIASES["design"]["字段定义"]) and level <= 2:
            in_dd = True
            dd_heading_level = level
            continue
        if in_dd and level <= dd_heading_level:
            break
        if in_dd and level == dd_heading_level + 1:
            design_entities.add(title)

    if not design_entities:
        return {"check": "prd_entity_coverage", "passed": True, "detail": "design 数据字典无实体，跳过"}

    # Get PRD content
    if stdin_content is not None:
        prd_content = stdin_content
    else:
        prd_path = project_root / "output" / "prd" / "prd.md"
        if not prd_path.exists():
            return {"check": "prd_entity_coverage", "passed": False, "detail": "prd.md 不存在"}
        with open(prd_path, encoding="utf-8") as f:
            prd_content = f.read()

    # 归位后：检查 design 实体名是否在 PRD 正文的关键位置出现
    # 仅在标题/粗体块/表格行首匹配，避免短实体名在任意位置误匹配；
    # 长实体名（>2字）兜底用全文子串匹配保持容错
    missing = []
    for entity in sorted(design_entities):
        _entity_context_pattern = re.compile(
            rf'(?:^#+\s+.*?|^\*\*.*?|^\|\s*){re.escape(entity)}', re.MULTILINE)
        entity_found = bool(_entity_context_pattern.search(prd_content))
        # 对非常短的实体名（≤2字），额外要求出现在标题行或粗体块中
        if not entity_found and len(entity) <= 2:
            _heading_or_bold = re.compile(
                rf'(?:^#+\s+.*?|^\*\*.*?){re.escape(entity)}', re.MULTILINE)
            entity_found = bool(_heading_or_bold.search(prd_content))
        # 兜底：全文子串匹配（宽松，保持对长实体名的容错）
        if not entity_found and len(entity) > 2:
            entity_found = entity in prd_content
        if not entity_found:
            missing.append(entity)

    covered = len(design_entities) - len(missing)
    total = len(design_entities)

    detail_parts = [f"PRD 实体覆盖：{covered}/{total} 实体"]
    if missing:
        detail_parts.append(f"缺失 {len(missing)} 个：{', '.join(missing[:10])}" + ("..." if len(missing) > 10 else ""))

    passed = len(missing) == 0
    return {
        "check": "prd_entity_coverage",
        "passed": passed,
        "detail": "；".join(detail_parts),
        "missing_entities": missing,
        "coverage_ratio": round(covered / total, 2) if total > 0 else 1.0,
    }

def check_artifact_exists(project_root: Path, stage: str, stdin_content: str = None) -> dict:
    artifact_rel = ARTIFACT_PATHS[stage]
    if stdin_content is not None:
        if not stdin_content.strip():
            return {
                "check": "artifact_exists",
                "passed": False,
                "detail": f"{artifact_rel} 读取失败（stdin 为空）",
            }
        result = {
            "check": "artifact_exists",
            "passed": True,
            "detail": artifact_rel,
            "size_chars": len(stdin_content),
        }
        return result
    artifact_path = project_root / artifact_rel
    exists = artifact_path.exists()
    result = {
        "check": "artifact_exists",
        "passed": exists,
        "detail": artifact_rel if exists else f"{artifact_rel} 不存在",
    }
    if exists and stage in ("design", "prd"):
        with open(artifact_path, encoding="utf-8") as f:
            content = f.read()
        result["size_chars"] = len(content)
    return result


def check_core_sections(project_root: Path, stage: str, stdin_content: str = None) -> list:
    if stage not in CORE_SECTIONS or not CORE_SECTIONS[stage]:
        return []
    artifact_rel = ARTIFACT_PATHS[stage]
    artifact_path = project_root / artifact_rel
    if stdin_content is not None:
        content = stdin_content
    elif not artifact_path.exists():
        return [{"check": "core_sections", "passed": False, "detail": f"{artifact_rel} 不存在，无法检查章节"}]
    else:
        with open(artifact_path, encoding="utf-8") as f:
            content = f.read()
    aliases = SECTION_ALIASES.get(stage, {})
    results = []
    for section in CORE_SECTIONS[stage]:
        found = bool(re.search(re.escape(section), content))
        matched_alias = section if found else None
        if not found and section in aliases:
            for alias in aliases[section]:
                if alias != section and re.search(re.escape(alias), content):
                    found = True
                    matched_alias = alias
                    break
        results.append({
            "check": "core_section_present",
            "passed": found,
            "detail": matched_alias if found else f"缺少章节：{section}",
            "canonical": section,
            # found_via_alias=True 表示通过别名匹配上（非精确 canonical 名），存在假阳性风险，需人审确认
            "found_via_alias": matched_alias is not None and matched_alias != section,
        })
    return results


def check_metadata_complete(project_root: Path, stage: str) -> list:
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    expected = METADATA_FILE_MAP.get(stage, [])
    empty_ok = METADATA_EMPTY_OK.get(stage, set())
    results = []
    for fname in expected:
        fpath = metadata_dir / fname
        exists = fpath.exists()
        check = {
            "check": "metadata_file_exists",
            "passed": exists,
            "detail": f".workflow/metadata/{stage}/{fname}" if exists else f".workflow/metadata/{stage}/{fname} 缺失",
        }
        if exists:
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and not data:
                    if fname in empty_ok:
                        check["passed"] = True
                        check["detail"] = f".workflow/metadata/{stage}/{fname} 为空对象（允许为空）"
                    else:
                        check["passed"] = False
                        check["detail"] = f".workflow/metadata/{stage}/{fname} 为空对象"
                elif isinstance(data, list) and not data:
                    if fname in empty_ok:
                        check["passed"] = True
                        check["detail"] = f".workflow/metadata/{stage}/{fname} 为空数组（允许为空）"
                    else:
                        check["passed"] = False
                        check["detail"] = f".workflow/metadata/{stage}/{fname} 为空数组"
            except json.JSONDecodeError:
                check["passed"] = False
                check["detail"] = f".workflow/metadata/{stage}/{fname} JSON 解析失败"
        results.append(check)
    return results


def check_design_page_field_coverage(project_root: Path) -> dict:
    """校验 design 的字段全集与页面字段落点/例外表是否全量对齐"""
    meta_dir = project_root / ".workflow" / "metadata" / "design"
    pages_path = meta_dir / "pages.json"
    fields_path = meta_dir / "fields.json"
    page_fields_path = meta_dir / "page-fields.json"
    non_page_fields_path = meta_dir / "non-page-fields.json"

    if not (pages_path.exists() and fields_path.exists() and page_fields_path.exists() and non_page_fields_path.exists()):
        return {
            "check": "design_page_field_coverage",
            "passed": False,
            "detail": "缺少 pages.json / fields.json / page-fields.json / non-page-fields.json，无法校验字段覆盖",
        }

    try:
        with open(pages_path, encoding="utf-8") as f:
            pages = json.load(f)
        with open(fields_path, encoding="utf-8") as f:
            fields = json.load(f)
        with open(page_fields_path, encoding="utf-8") as f:
            page_fields = json.load(f)
        with open(non_page_fields_path, encoding="utf-8") as f:
            non_page_fields = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {
            "check": "design_page_field_coverage",
            "passed": False,
            "detail": f"页面与字段落点校验读取失败: {e}",
        }

    page_ids = {p.get("id") for p in pages if isinstance(p, dict) and p.get("id")}
    field_ids = {f.get("id") for f in fields if isinstance(f, dict) and f.get("id")}
    field_title_by_id = {f.get("id"): f.get("title") for f in fields if isinstance(f, dict) and f.get("id")}
    page_title_by_id = {p.get("id"): p.get("title") for p in pages if isinstance(p, dict) and p.get("id")}

    mapped_pages = set()
    mapped_fields = set()
    exempted_fields = set()
    missing_page_refs = []
    field_to_pages = {}  # field_id -> [page_titles]
    missing_field_refs = []
    unmatched_fields = []
    empty_pages = []
    invalid_exempt_fields = []
    missing_exempt_reasons = []
    overlap_fields = []

    for entry in page_fields if isinstance(page_fields, list) else []:
        if not isinstance(entry, dict):
            continue
        page_id = entry.get("design_page")
        page_title = entry.get("page_title", "")
        if page_id:
            if page_id in page_ids:
                mapped_pages.add(page_id)
            else:
                missing_page_refs.append(page_title or page_id)
        else:
            missing_page_refs.append(page_title or "(未命名页面)")

        for token in entry.get("unmatched_fields", []):
            unmatched_fields.append(f"{page_title}: {token}")

        refs = entry.get("field_refs", [])
        if refs:
            for fid in refs:
                if fid in field_ids:
                    mapped_fields.add(fid)
                    field_to_pages.setdefault(fid, []).append(page_title)
                else:
                    missing_field_refs.append(f"{page_title}: {fid}")
        elif not entry.get("declared_empty"):
            empty_pages.append(page_title or page_id or "(未命名页面)")

    missing_pages = sorted(page_ids - mapped_pages)
    for entry in non_page_fields if isinstance(non_page_fields, list) else []:
        if not isinstance(entry, dict):
            continue
        fid = entry.get("design_field")
        title = entry.get("field_title", "")
        reason = (entry.get("reason") or "").strip()
        if fid:
            if fid in field_ids:
                exempted_fields.add(fid)
            else:
                invalid_exempt_fields.append(title or fid)
        else:
            invalid_exempt_fields.append(title or "(未命名字段)")
        if not reason:
            missing_exempt_reasons.append(title or fid or "(未命名字段)")

    overlap_ids = sorted(mapped_fields & exempted_fields)
    missing_fields = sorted(field_ids - mapped_fields - exempted_fields)

    problems = []
    if missing_page_refs:
        problems.append(f"页面落点引用了无效页面: {', '.join(missing_page_refs[:5])}")
    if missing_field_refs:
        problems.append(f"页面落点引用了无效字段 ID: {', '.join(missing_field_refs[:5])}")
    if unmatched_fields:
        problems.append(f"页面落点出现未在数据字典定义的字段: {', '.join(unmatched_fields[:5])}")
    if empty_pages:
        problems.append(f"以下页面未声明字段且未标记无业务字段: {', '.join(empty_pages[:5])}")
    if missing_pages:
        missing_page_titles = [page_title_by_id.get(pid, pid) for pid in missing_pages]
        problems.append(f"页面清单中的页面未出现在页面与字段落点: {', '.join(missing_page_titles[:5])}")
    if invalid_exempt_fields:
        problems.append(f"非页面落点字段中引用了数据字典未定义字段: {', '.join(invalid_exempt_fields[:8])}")
    if missing_exempt_reasons:
        problems.append(f"非页面落点字段缺少原因说明: {', '.join(missing_exempt_reasons[:8])}")
    if overlap_ids:
        overlap_details = []
        for fid in overlap_ids[:8]:
            title = field_title_by_id.get(fid, fid)
            pages = field_to_pages.get(fid, [])
            page_str = "、".join(pages[:3]) if pages else "未知页面"
            overlap_details.append(f"{title}(页面落点: {page_str})")
        problems.append(
            "以下字段已正确映射到页面，但重复出现在非页面落点字段表中——"
            "请从非页面落点字段表中移除这些字段，不要清除页面字段映射: "
            + "; ".join(overlap_details)
        )
    if missing_fields:
        missing_field_titles = [field_title_by_id.get(fid, fid) for fid in missing_fields]
        problems.append(f"数据字典中的字段既未在页面与字段落点出现，也未在非页面落点字段声明: {', '.join(missing_field_titles[:8])}")

    # 软警告：非页面落点字段占比异常高
    _extra_warnings = []
    _total = len(field_ids)
    if _total > 0:
        _ratio = len(exempted_fields) / _total
        if _ratio > 0.3:
            _extra_warnings.append(
                f"非页面落点字段占总字段 {len(exempted_fields)}/{_total}({_ratio:.0%})，比例偏高"
                f"——请检查非页面落点字段表中是否有字段实际应分配到页面"
            )

    if problems:
        return {
            "check": "design_page_field_coverage",
            "passed": False,
            "detail": "；".join(problems),
            "warnings": _extra_warnings,
        }

    return {
        "check": "design_page_field_coverage",
        "passed": True,
        "detail": f"字段覆盖通过：{len(mapped_pages)}/{len(page_ids)} 个页面，{len(mapped_fields)} 个页面落点字段，{len(exempted_fields)} 个非页面落点字段",
        "warnings": _extra_warnings,
    }


def run_prd_style_lint(project_root: Path, content: str = None) -> list:
    """Run PRD style lint via direct import instead of subprocess.

    优先使用 content 参数（来自 stdin），否则从磁盘读取。
    """
    if content is not None:
        prd_content = content
    else:
        prd_path = project_root / ARTIFACT_PATHS["prd"]
        if not prd_path.exists():
            return [f"PRD 产物不存在: {ARTIFACT_PATHS['prd']}"]
        with open(prd_path, encoding="utf-8") as f:
            prd_content = f.read()
    try:
        # 文件名含连字符，无法用普通 import，用 importlib 加载
        import importlib.util
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("prd_style_lint", os.path.join(scripts_dir, "prd-style-lint.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        issues = mod.run_lint(prd_content)
        warnings = []
        for issue in issues:
            if issue.severity in ("error", "warning"):
                warnings.append(f"{issue.code}: {issue.message}")
        return warnings
    except ImportError as e:
        return [f"lint 脚本加载失败（依赖缺失）: {e}"]
    except Exception as e:
        return [f"lint 执行异常: {e}"]
def main():
    parser = argparse.ArgumentParser(description="review 确定性预检查（vNext: 文件存在性与基础结构检查）")
    parser.add_argument("--stage", required=True, choices=VALID_STAGES, help="被 review 的阶段")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="项目根目录")
    parser.add_argument("--stdin-artifact", action="store_true", help="从 stdin 读取人读稿内容（需通过管道或重定向传入）")
    parser.add_argument("--artifact-file", type=Path, default=None, help="直接指定人读稿文件路径，避免 stdin 管道依赖")
    parser.add_argument("--no-metadata", action="store_true", help="(vNext: deprecated，metadata 检查默认不阻塞)")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    stage = args.stage

    deterministic_checks = []
    blocking_issues = []
    warnings = []

    # vNext: 优先用 --artifact-file 明确路径；其次 --stdin-artifact；最后从默认产物路径读
    stdin_content = None
    if args.artifact_file is not None:
        artifact_path = args.artifact_file
        if not artifact_path.is_absolute():
            artifact_path = (project_root / artifact_path).resolve()
        if not artifact_path.exists():
            stdin_content = ""
        else:
            with open(artifact_path, encoding="utf-8") as f:
                stdin_content = f.read()
    elif args.stdin_artifact:
        stdin_content = sys.stdin.read()
    artifact_check = check_artifact_exists(project_root, stage, stdin_content)
    deterministic_checks.append(artifact_check)
    if not artifact_check["passed"]:
        blocking_issues.append(artifact_check["detail"])

    section_checks = check_core_sections(project_root, stage, stdin_content)
    deterministic_checks.extend(section_checks)
    for sc in section_checks:
        if not sc["passed"]:
            # vNext: 核心章节缺失直接阻塞 Review（与 review-checklist.md 契约一致）
            blocking_issues.append(sc["detail"])
        elif sc.get("found_via_alias"):
            # 通过别名匹配上：假阳性风险，记入 warning 供 reviewer 人审确认
            warnings.append(f"章节通过别名匹配（请人审确认）：{sc.get('canonical')} → {sc.get('detail')}")

    # vNext: metadata 检查改为可选——只在旧项目存在 metadata 目录时作为参考
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    if metadata_dir.exists():
        metadata_checks = check_metadata_complete(project_root, stage)
        deterministic_checks.extend(metadata_checks)
        for mc in metadata_checks:
            if not mc["passed"]:
                # vNext: metadata 问题记入 warnings，不阻塞 review
                warnings.append(f"[legacy metadata] {mc['detail']}")

        if stage == "design":
            coverage_check = check_design_page_field_coverage(project_root)
            deterministic_checks.append(coverage_check)
            if not coverage_check["passed"]:
                # vNext: 字段覆盖问题记入 warnings，不阻塞 review
                warnings.append(f"[legacy metadata] {coverage_check['detail']}")

    if stage == "prd":
        lint_warnings = run_prd_style_lint(project_root, stdin_content)
        if lint_warnings:
            deterministic_checks.append({
                "check": "prd_style_lint",
                "passed": len(lint_warnings) == 0,
                "detail": f"lint 发现 {len(lint_warnings)} 个问题",
            })
            warnings.extend(lint_warnings)

        entity_cov = check_prd_entity_coverage(project_root, stdin_content)
        deterministic_checks.append(entity_cov)
        if not entity_cov["passed"]:
            # vNext: 实体覆盖问题记入 warnings，不阻塞 review（PRD review 仍可执行）
            warnings.append(f"[prd_entity_coverage] {entity_cov['detail']}")

    # vNext: can_start_review 只基于 artifact 存在和核心章节存在
    can_start_review = len(blocking_issues) == 0

    if blocking_issues:
        recommended_focus = "先回上游补结构"
    elif warnings:
        recommended_focus = "正文写法与一致性"
    elif stage == "design":
        recommended_focus = "结构完整性、表格规范性、字段定义属性齐全性、状态机闭环、高影响缺口暴露"
    elif stage == "prd":
        recommended_focus = "坏味道、三层覆盖、与 design 镜像一致性、Design 未授权高影响事实检查"
    elif stage == "prototype":
        recommended_focus = "页面结构、状态表达、交互主路径、Design 未授权高影响行为检查"
    else:
        recommended_focus = "正文质量"

    metadata_paths = []
    if metadata_dir.exists():
        for fname in sorted(metadata_dir.glob("*.json")):
            metadata_paths.append(f".workflow/metadata/{stage}/{fname.name}")

    alias_missed_count = sum(1 for sc in section_checks if sc.get("passed") and sc.get("found_via_alias"))
    output = {
        "stage": stage,
        "artifact_path": ARTIFACT_PATHS[stage],
        "metadata_paths": metadata_paths,
        "metadata_check_mode": "legacy_optional" if metadata_dir.exists() else "skipped_no_metadata",
        "deterministic_checks": deterministic_checks,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "can_start_review": can_start_review,
        "alias_missed_count": alias_missed_count,
        "recommended_focus": recommended_focus,
    }

    runtime_dir = project_root / ".workflow" / "runtime" / stage
    runtime_dir.mkdir(parents=True, exist_ok=True)
    output_path = runtime_dir / "review-precheck.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(json.dumps(output, ensure_ascii=False, indent=2))

    if not can_start_review:
        sys.exit(1)


if __name__ == "__main__":
    main()
