#!/usr/bin/env python3
"""stage-context.py — 准入和上下文脚本

职责：读取状态、判断当前阶段、收集最小读取集合、给出下一步建议。
不生成 metadata，不修改文件，不做业务语义判断。

用法：python stage-context.py <project_root>
"""

import json
import sys
from pathlib import Path

VALID_STAGES = ["align", "design", "design-review", "prd", "prd-review", "prototype", "prototype-review", "fix", "done"]

# 每个阶段的上游依赖
UPSTREAM_DEPS = {
    "align": [],
    "design": ["align"],
    "prd": ["design"],
    "prototype": ["design"],
    "fix": [],  # fix 可从任意阶段发起
}

# 每个阶段必须存在的人读产物
REQUIRED_ARTIFACTS = {
    "align": [],
    "design": ["output/align/align.md"],
    "prd": ["output/design/design.md"],
    "prototype": ["output/design/design.md"],
    "fix": [],
}

# 每个阶段必须存在的机读物目录
REQUIRED_METADATA = {
    "align": [],
    "design": [".workflow/metadata/align/"],
    "prd": [".workflow/metadata/design/"],
    "prototype": [".workflow/metadata/design/"],
    "fix": [],
}

# 每个阶段的最小读取集合
MINIMAL_READ_SET = {
    "align": [
        ".workflow/status.json",
        "references/align-writing.md",
        "templates/align.md",
    ],
    "design": [
        ".workflow/status.json",
        "output/align/align.md",
        ".workflow/metadata/align/",
        "references/design-writing.md",
        "templates/design.md",
    ],
    "prd": [
        ".workflow/status.json",
        "output/design/design.md",
        ".workflow/metadata/design/",
        "references/prd-writing.md",
        "references/prd-writing.profile.json",
        "templates/prd.md",
    ],
    "prototype": [
        ".workflow/status.json",
        "output/design/design.md",
        ".workflow/metadata/design/",
        "templates/prototype.html",
        "references/prototype-writing.md",
    ],
    "fix": [
        ".workflow/status.json",
    ],
}


def load_status(project_root: Path, stdin_status: bool = False) -> dict:
    """加载 status.json"""
    if stdin_status:
        try:
            content = sys.stdin.read()
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return None
    status_path = project_root / ".workflow" / "status.json"
    if not status_path.exists():
        return None
    with open(status_path, encoding="utf-8") as f:
        return json.load(f)


def check_artifacts_exist(project_root: Path, paths: list) -> list:
    """检查必要产物是否存在，返回缺失列表"""
    missing = []
    for p in paths:
        full_path = project_root / p
        if not full_path.exists():
            missing.append(p)
    return missing


def check_metadata_dirs(project_root: Path, dirs: list) -> list:
    """检查必要机读物目录是否存在且非空，返回缺失列表"""
    missing = []
    for d in dirs:
        full_dir = project_root / d
        if not full_dir.exists() or not any(full_dir.iterdir()):
            missing.append(d)
    return missing


def load_align_notes(project_root: Path):
    """加载 align-notes.json（如存在）"""
    notes_path = project_root / ".workflow" / "runtime" / "align" / "align-notes.json"
    if not notes_path.exists():
        return None
    with open(notes_path, encoding="utf-8") as f:
        return json.load(f)


def determine_stage(project_root: Path, status: dict) -> str:
    """根据 status 和产物存在情况判断实际应处阶段"""
    artifacts = status.get("artifacts", {})

    has_align = artifacts.get("align") and (project_root / artifacts["align"]).exists()
    has_design = artifacts.get("design") and (project_root / artifacts["design"]).exists()
    has_prd = artifacts.get("prd") and (project_root / artifacts["prd"]).exists()
    has_prototype = artifacts.get("prototype") and (project_root / artifacts["prototype"]).exists()

    if not has_align:
        return "align"
    if not has_design:
        return "design"
    if not has_prd:
        return "prd"
    if not has_prototype:
        return "prototype"
    return status.get("current_stage", "prototype")


def determine_next(status: dict, align_notes) -> str:
    """给出下一步建议，考虑 review 结果"""
    current = status.get("current_stage", "align")
    reviews = status.get("latest_reviews", {})

    if current == "align":
        if align_notes and align_notes.get("can_enter_design"):
            return "design"
        if align_notes and align_notes.get("needs_ask_back"):
            return "align"
        return "align"

    if current == "design":
        design_review = reviews.get("design", {})
        if design_review.get("verdict") == "通过":
            return "prd"
        return "design-review"

    if current == "prd":
        prd_review = reviews.get("prd", {})
        if prd_review.get("verdict") == "通过":
            return "prototype"
        return "prd-review"

    if current == "prototype":
        proto_review = reviews.get("prototype", {})
        if proto_review.get("verdict") == "通过":
            return "done"
        return "prototype-review"

    if current == "fix":
        return "design"

    return current


def collect_context(project_root: Path, stdin_status: bool = False) -> dict:
    """收集当前阶段上下文，返回完整结果"""
    status = load_status(project_root, stdin_status=stdin_status)
    if status is None:
        return {
            "error": "status.json not found",
            "hint": "请先初始化 .workflow/status.json",
        }

    current_stage = status.get("current_stage", "align")
    if current_stage not in VALID_STAGES:
        return {
            "error": f"invalid stage: {current_stage}",
            "valid_stages": VALID_STAGES,
        }

    # 检查上游产物
    required_artifacts = REQUIRED_ARTIFACTS.get(current_stage, [])
    missing_artifacts = check_artifacts_exist(project_root, required_artifacts)

    # 检查上游机读物
    required_metadata = REQUIRED_METADATA.get(current_stage, [])
    missing_metadata = check_metadata_dirs(project_root, required_metadata)

    # 加载 align-notes
    align_notes = load_align_notes(project_root)

    # 判断实际阶段
    actual_stage = determine_stage(project_root, status)

    # 检查准入
    can_proceed = True
    blocking_issues = []

    if missing_artifacts:
        can_proceed = False
        blocking_issues.append(f"上游产物缺失: {missing_artifacts}")

    if missing_metadata:
        can_proceed = False
        blocking_issues.append(f"上游机读物缺失: {missing_metadata}")

    if current_stage == "design" and align_notes:
        if not align_notes.get("can_enter_design"):
            can_proceed = False
            blocking_issues.append("align-notes: can_enter_design = false")

    # 收集最小读取集合
    read_set = MINIMAL_READ_SET.get(current_stage, [])
    resolved_read_set = {}
    for p in read_set:
        full_path = project_root / p
        resolved_read_set[p] = {
            "exists": full_path.exists(),
            "path": str(full_path),
        }

    # 构建输出
    result = {
        "current_stage": current_stage,
        "actual_stage": actual_stage,
        "artifacts": status.get("artifacts", {}),
        "metadata_paths": status.get("metadata_paths", {}),
        "latest_reviews": status.get("latest_reviews", {}),
        "align_notes": align_notes if align_notes else {},
        "next_recommended": determine_next({**status, "current_stage": actual_stage}, align_notes) if can_proceed else actual_stage,
        "gate": {
            "can_proceed": can_proceed,
            "blocking_issues": blocking_issues,
        },
        "minimal_read_set": resolved_read_set,
    }

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="准入和上下文脚本")
    parser.add_argument("project_root", help="项目根目录")
    parser.add_argument("--stdin-status", action="store_true", help="从 stdin 读取 status.json 内容（避免重复读文件）")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"错误: 项目根目录不存在: {project_root}", file=sys.stderr)
        sys.exit(1)

    result = collect_context(project_root, stdin_status=args.stdin_status)

    # 输出 JSON 到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 如有阻塞问题，exit code = 1
    if result.get("gate", {}).get("blocking_issues"):
        sys.exit(1)


if __name__ == "__main__":
    main()
