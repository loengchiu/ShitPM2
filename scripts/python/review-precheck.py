#!/usr/bin/env python3
"""review-precheck.py — reviewer 开始前的确定性预检查

职责：
1. 记录当前阶段 reviewer 读取的是哪份人读稿和哪套机读物
2. 记录脚本已完成的结构检查结果
3. 提前暴露阻塞 reviewer 的缺口
4. 告诉 reviewer 本轮应重点做人审，还是先回上游补结构

它不是：最终 review 结论、人读摘要、第二份 reviewer 报告。

用法：python review-precheck.py --stage <stage> [--project-root <path>]
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_STAGES = ["design", "prd", "prototype"]

ARTIFACT_PATHS = {
    "design": "output/design/design.md",
    "prd": "output/prd/prd.md",
    "prototype": "output/prototype/index.html",
}

METADATA_FILE_MAP = {
    "design": ["index.json", "entities.json", "relations.json", "modules.json", "pages.json", "fields.json", "rules.json", "states.json", "permissions.json", "page-fields.json", "non-page-fields.json", "field-constraints.json"],
    "prd": ["index.json", "entities.json", "relations.json", "page-anchor.json", "rule-anchor.json", "field-anchor.json"],
    "prototype": ["index.json", "page-map.json"],
}

METADATA_EMPTY_OK = {
    "design": {"relations.json"},
    "prd": {"relations.json"},
}

CORE_SECTIONS = {
    "design": ["角色定义", "模块定义", "页面清单", "字段定义", "页面与字段落点", "规则与状态定义", "权限定义"],
    "prd": ["详细需求说明", "权限汇总", "数据字典", "状态机"],
    "prototype": [],
}

STABLE_ID_PATTERN = re.compile(r'(MODULE|PAGE|FIELD|RULE|FLOW|REL|REQ|RISK|CASE|WVR)-(design|prd)-\d{3}')



def check_field_constraints_consistency(project_root: Path, stage: str) -> dict:
    """检查 field-constraints.json 与 design.md 的字段约束是否一致"""
    if stage != "design":
        return {"check": "field_constraints_consistency", "passed": True, "detail": "非 design 阶段，跳过"}

    fc_path = project_root / ".workflow/metadata/design/field-constraints.json"
    if not fc_path.exists():
        return {"check": "field_constraints_consistency", "passed": False, "detail": "field-constraints.json 不存在"}

    artifact_path = project_root / ARTIFACT_PATHS[stage]
    if not artifact_path.exists():
        return {"check": "field_constraints_consistency", "passed": False, "detail": f"{ARTIFACT_PATHS[stage]} 不存在"}

    with open(fc_path, encoding="utf-8") as f:
        constraints = json.load(f)
    with open(artifact_path, encoding="utf-8") as f:
        content = f.read()

    issues = []
    for field in constraints:
        name = field.get("name", "")
        multi_select = field.get("multi_select")
        editable = field.get("editable")

        # 检查 multi_select 一致性
        if multi_select is True:
            # design.md 中应该有"多选"或"允许选择多个"
            if "只能选择 1 个" in content and name in content:
                issues.append(f"{name}: field-constraints 标记 multi_select=true，但 design.md 中有'只能选择 1 个'")
        if multi_select is False:
            # design.md 中应该有"单选"或"只能选择 1 个"
            pass  # 正向检查较难，跳过

    if issues:
        return {"check": "field_constraints_consistency", "passed": False, "detail": "; ".join(issues)}
    return {"check": "field_constraints_consistency", "passed": True, "detail": "字段约束一致性通过"}


def check_artifact_exists(project_root: Path, stage: str) -> dict:
    artifact_rel = ARTIFACT_PATHS[stage]
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


def check_core_sections(project_root: Path, stage: str) -> list:
    if stage not in CORE_SECTIONS or not CORE_SECTIONS[stage]:
        return []
    artifact_rel = ARTIFACT_PATHS[stage]
    artifact_path = project_root / artifact_rel
    if not artifact_path.exists():
        return [{"check": "core_sections", "passed": False, "detail": f"{artifact_rel} 不存在，无法检查章节"}]
    with open(artifact_path, encoding="utf-8") as f:
        content = f.read()
    results = []
    for section in CORE_SECTIONS[stage]:
        found = bool(re.search(re.escape(section), content))
        results.append({
            "check": "core_section_present",
            "passed": found,
            "detail": section if found else f"缺少章节：{section}",
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


def check_stable_id_leak(project_root: Path, stage: str) -> dict:
    if stage == "prototype":
        artifact_rel = ARTIFACT_PATHS[stage]
        artifact_path = project_root / artifact_rel
        if not artifact_path.exists():
            return {"check": "stable_id_leak", "passed": True, "detail": "原型文件不存在，跳过检查"}
        with open(artifact_path, encoding="utf-8") as f:
            content = f.read()
        matches = STABLE_ID_PATTERN.findall(content)
        if matches:
            return {
                "check": "stable_id_leak",
                "passed": False,
                "detail": f"原型 HTML 中发现 {len(matches)} 处稳定 ID 泄漏",
            }
        return {"check": "stable_id_leak", "passed": True, "detail": "无稳定 ID 泄漏"}

    artifact_rel = ARTIFACT_PATHS[stage]
    artifact_path = project_root / artifact_rel
    if not artifact_path.exists():
        return {"check": "stable_id_leak", "passed": True, "detail": "人读稿不存在，跳过检查"}
    with open(artifact_path, encoding="utf-8") as f:
        content = f.read()
    matches = STABLE_ID_PATTERN.findall(content)
    if matches:
        return {
            "check": "stable_id_leak",
            "passed": False,
            "detail": f"人读稿中发现 {len(matches)} 处稳定 ID 泄漏",
        }
    return {"check": "stable_id_leak", "passed": True, "detail": "无稳定 ID 泄漏"}


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
        overlap_fields = [field_title_by_id.get(fid, fid) for fid in overlap_ids]
        problems.append(f"字段同时出现在页面落点和非页面落点: {', '.join(overlap_fields[:8])}")
    if missing_fields:
        missing_field_titles = [field_title_by_id.get(fid, fid) for fid in missing_fields]
        problems.append(f"数据字典中的字段既未在页面与字段落点出现，也未在非页面落点字段声明: {', '.join(missing_field_titles[:8])}")

    if problems:
        return {
            "check": "design_page_field_coverage",
            "passed": False,
            "detail": "；".join(problems),
        }

    return {
        "check": "design_page_field_coverage",
        "passed": True,
        "detail": f"字段覆盖通过：{len(mapped_pages)}/{len(page_ids)} 个页面，{len(mapped_fields)} 个页面落点字段，{len(exempted_fields)} 个非页面落点字段",
    }


def run_prd_style_lint(project_root: Path) -> list:
    prd_path = project_root / ARTIFACT_PATHS["prd"]
    if not prd_path.exists():
        return []
    lint_script = project_root / "scripts" / "python" / "prd-style-lint.py"
    if not lint_script.exists():
        return []
    lint_output = project_root / ".workflow" / "runtime" / "prd" / "lint.json"
    lint_output.parent.mkdir(parents=True, exist_ok=True)

    # 启动 lint 子进程
    try:
        result = subprocess.run(
            [sys.executable, str(lint_script), str(prd_path), "--format", "json", "--output", str(lint_output)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except (OSError, ValueError) as e:
        return [f"lint 进程启动失败: {e}"]

    # 优先从 --output 文件读取 lint 结果，确保消费方式一致
    lint_data = None
    if lint_output.exists():
        try:
            with open(lint_output, encoding="utf-8") as f:
                lint_data = json.load(f)
        except (json.JSONDecodeError, OSError, ValueError) as e:
            return [f"lint 输出文件解析失败: {e}"]

    # 回退：从 stdout 读取（兼容不传 --output 的场景）
    if lint_data is None:
        if result.stdout.strip():
            try:
                lint_data = json.loads(result.stdout)
            except (json.JSONDecodeError, ValueError) as e:
                return [f"lint stdout 解析失败 (exit={result.returncode}): {e}"]

    # 无数据可解析时，根据 returncode 判断
    if lint_data is None:
        if result.returncode != 0:
            stderr_tail = result.stderr.strip()[-200:] if result.stderr.strip() else "(无 stderr)"
            return [f"lint 执行失败 (exit={result.returncode}): {stderr_tail}"]
        return []

    issues = lint_data if isinstance(lint_data, list) else lint_data.get("issues", [])
    warnings = []
    for issue in issues:
        sev = issue.get("severity", "info")
        if sev in ("error", "warning"):
            warnings.append(f"{issue.get('code', 'UNKNOWN')}: {issue.get('message', '')}")
    return warnings


def main():
    parser = argparse.ArgumentParser(description="review 确定性预检查")
    parser.add_argument("--stage", required=True, choices=VALID_STAGES, help="被 review 的阶段")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="项目根目录")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    stage = args.stage

    deterministic_checks = []
    blocking_issues = []
    warnings = []

    artifact_check = check_artifact_exists(project_root, stage)
    deterministic_checks.append(artifact_check)
    if not artifact_check["passed"]:
        blocking_issues.append(artifact_check["detail"])

    section_checks = check_core_sections(project_root, stage)
    deterministic_checks.extend(section_checks)
    for sc in section_checks:
        if not sc["passed"]:
            blocking_issues.append(sc["detail"])

    metadata_checks = check_metadata_complete(project_root, stage)
    deterministic_checks.extend(metadata_checks)
    for mc in metadata_checks:
        if not mc["passed"]:
            blocking_issues.append(mc["detail"])

    id_leak_check = check_stable_id_leak(project_root, stage)
    deterministic_checks.append(id_leak_check)
    if not id_leak_check["passed"]:
        warnings.append(id_leak_check["detail"])

    if stage == "design":
        coverage_check = check_design_page_field_coverage(project_root)
        deterministic_checks.append(coverage_check)
        if not coverage_check["passed"]:
            blocking_issues.append(coverage_check["detail"])
        fc_check = check_field_constraints_consistency(project_root, stage)
        deterministic_checks.append(fc_check)
        if not fc_check["passed"]:
            blocking_issues.append(fc_check["detail"])

    if stage == "prd":
        lint_warnings = run_prd_style_lint(project_root)
        if lint_warnings:
            deterministic_checks.append({
                "check": "prd_style_lint",
                "passed": len(lint_warnings) == 0,
                "detail": f"lint 发现 {len(lint_warnings)} 个问题",
            })
            warnings.extend(lint_warnings)

    can_start_review = len(blocking_issues) == 0

    if blocking_issues:
        recommended_focus = "先回上游补结构"
    elif warnings:
        recommended_focus = "正文写法与一致性"
    elif stage == "design":
        recommended_focus = "字段定义属性齐全性、权限覆盖、状态完整性"
    elif stage == "prd":
        recommended_focus = "坏味道、三层覆盖、与 design 镜像一致性"
    elif stage == "prototype":
        recommended_focus = "页面结构、状态表达、交互主路径"
    else:
        recommended_focus = "正文质量"

    metadata_dir = project_root / ".workflow" / "metadata" / stage
    metadata_paths = []
    if metadata_dir.exists():
        for fname in sorted(metadata_dir.glob("*.json")):
            metadata_paths.append(f".workflow/metadata/{stage}/{fname.name}")

    output = {
        "stage": stage,
        "artifact_path": ARTIFACT_PATHS[stage],
        "metadata_paths": metadata_paths,
        "deterministic_checks": deterministic_checks,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "can_start_review": can_start_review,
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
