#!/usr/bin/env python3
"""check-stage.py -- current stage to active skill mapping.

Usage: python check-stage.py <project_root>
"""

import json
import sys
from pathlib import Path

STAGE_SKILL_MAP = {
    "align": "spm-align",
    "design": "spm-design",
    "design-review": "spm-design-review",
    "prd": "spm-prd",
    "prd-review": "spm-prd-review",
    "prototype": "spm-prototype",
    "prototype-review": "spm-prototype-review",
    "fix": "spm-fix",
}

SKILL_ARTIFACTS = {
    "spm-align": ["output/align/align.md"],
    "spm-design": ["output/design/design.md"],
    "spm-design-review": ["output/design/design.md"],
    "spm-prd": ["output/prd/prd.md"],
    "spm-prd-review": ["output/prd/prd.md"],
    "spm-prototype": ["output/prototype/index.html"],
    "spm-prototype-review": ["output/prototype/index.html"],
    "spm-fix": ["any stage"],
}

SKILL_LABELS = {
    "spm-align": "align",
    "spm-design": "design",
    "spm-design-review": "design review",
    "spm-prd": "prd",
    "spm-prd-review": "prd review",
    "spm-prototype": "prototype",
    "spm-prototype-review": "prototype review",
    "spm-fix": "fix",
}

SKILL_TRIGGERS = {
    "spm-align": "say /spm-align or make align",
    "spm-design": "say /spm-design or make/edit design",
    "spm-design-review": "say /spm-design-review",
    "spm-prd": "say /spm-prd or make prd",
    "spm-prd-review": "say /spm-prd-review",
    "spm-prototype": "say /spm-prototype or make prototype",
    "spm-prototype-review": "say /spm-prototype-review",
    "spm-fix": "say /spm-fix or fix",
}


def sep(title: str):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check():
    if len(sys.argv) < 2:
        print("Usage: python check-stage.py <project_root>")
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()
    if not project_root.exists():
        print(f"Error: project root not found: {project_root}")
        sys.exit(1)

    status_path = project_root / ".workflow" / "status.json"
    if not status_path.exists():
        sep("No workflow status found")
        print("  .workflow/status.json does not exist")
        print("  Run /spm-start to initialize")
        return

    with open(status_path, encoding="utf-8") as f:
        status = json.load(f)

    current_stage = status.get("current_stage", "unknown")
    skill = STAGE_SKILL_MAP.get(current_stage, "unknown")
    label = SKILL_LABELS.get(skill, "")
    artifacts = status.get("artifacts", {})
    reviews = status.get("latest_reviews", {})
    next_rec = status.get("next_recommended", "")

    sep(f"Stage: {current_stage}  ->  Skill: {skill} ({label})")
    print(f"  Next recommended: {next_rec if next_rec else '(none)'}")
    print()

    print("  Artifacts:")
    stage_order = ["align", "design", "prd", "prototype"]
    for s in stage_order:
        artifact_path = artifacts.get(s, "")
        review = reviews.get(s, {})
        verdict = review.get("verdict", "unreviewed")
        exists = (project_root / artifact_path).exists() if artifact_path else False
        icon = "[x]" if exists else "[ ]"
        print(f"    {icon} {s}: {artifact_path or '(unset)'}  [{verdict}]")
    print()

    print(f"  Active skill: {skill}")
    print(f"  Stage label: {label}")
    print(f"  Manages: {', '.join(SKILL_ARTIFACTS.get(skill, []))}")
    print(f"  Trigger: {SKILL_TRIGGERS.get(skill, 'describe intent')}")
    print()

    print("  Quick ref - edit other artifacts:")
    for s, sk in STAGE_SKILL_MAP.items():
        if sk == skill:
            continue
        trig = SKILL_TRIGGERS.get(sk, "")
        arts = ", ".join(SKILL_ARTIFACTS.get(sk, []))
        print(f"    {arts} -> {trig}")
    print()

    # Tip for back-editing design during prototype
    if current_stage in ("prd", "prototype"):
        d_review = reviews.get("design", {})
        if d_review.get("verdict") and d_review["verdict"] in ("通过", "閫氳繃", "passed"):
            print("  Tip: design already reviewed. To edit design.md:")
            print('    Say "edit design" or "modify design document" to trigger spm-design')
            print('    After editing, consider re-review (/spm-design-review)')
            print('    Or use /spm-fix for sync propagation')

    print("=" * 60)


if __name__ == "__main__":
    check()

