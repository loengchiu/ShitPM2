#!/usr/bin/env python3
"""stage-context.py — vNext 轻量导航和上下文脚本

职责：
- 读取 status.json（兼容旧字段）
- 检查 Design 确认标记（.workflow/confirmations/design.json）的哈希是否仍然有效
- 输出 available_actions 列表（PRD 与 Prototype 是 Design 的两个独立下游）
- 不再把 current_stage 当成唯一流程真相
- 不再把旧 metadata 或旧 Review 记录当成新流程硬门禁
- 不生成 metadata，不修改产物

用法：
  python stage-context.py --project-root <path> [--stdin-status]
"""

import argparse
import json
import sys
from pathlib import Path


VALID_STAGES = ["align", "design", "design-review", "prd", "prd-review", "prototype", "prototype-review", "fix", "done"]

DESIGN_ARTIFACT = "output/design/design.md"
CONFIRMATION_FILE = ".workflow/confirmations/design.json"


# 每个阶段推荐的最小读取集合（仅作为参考，不再构成硬门禁）
MINIMAL_READ_SET = {
    "align": [
        ".workflow/status.json",
        "references/align-writing.md",
        "templates/align.md",
    ],
    "design": [
        ".workflow/status.json",
        "output/align/align.md",  # 可选
        "references/design-writing.md",
        "references/design-state-format.md",
        "templates/design.md",
    ],
    "prd": [
        ".workflow/status.json",
        "output/design/design.md",
        "references/prd-writing.md",
        "references/prd-writing.profile.json",
        "templates/prd.md",
    ],
    "prototype": [
        ".workflow/status.json",
        "output/design/design.md",
        "templates/prototype.html",
        "references/prototype-writing.md",
    ],
    "fix": [
        ".workflow/status.json",
    ],
    "design-review": [
        ".workflow/status.json",
        "output/design/design.md",
        "contracts/review-checklist.md",
        "references/design-writing.md",
        "references/design-state-format.md",
    ],
    "prd-review": [
        ".workflow/status.json",
        "output/design/design.md",
        "output/prd/prd.md",
        "contracts/review-checklist.md",
    ],
    "prototype-review": [
        ".workflow/status.json",
        "output/design/design.md",
        "output/prototype/index.html",
        "contracts/review-checklist.md",
    ],
}


def load_status(project_root: Path, stdin_status: bool = False) -> dict | None:
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


def load_align_notes(project_root: Path) -> dict | None:
    notes_path = project_root / ".workflow" / "runtime" / "align" / "align-notes.json"
    if not notes_path.exists():
        return None
    try:
        with open(notes_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _has_file(project_root: Path, rel: str | None) -> bool:
    if not rel:
        return False
    return (project_root / rel).exists()


def _compute_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_design_confirmation(project_root: Path) -> dict | None:
    path = project_root / CONFIRMATION_FILE
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def design_confirmation_status(project_root: Path) -> dict:
    """检查 Design 确认状态。返回 {confirmed, reason, current_sha256, confirmed_sha256, confirmed_at}"""
    design_path = project_root / DESIGN_ARTIFACT
    confirmation = load_design_confirmation(project_root)

    if not design_path.exists():
        return {
            "confirmed": False,
            "reason": "design_not_found",
            "hint": "output/design/design.md 不存在，请先生成 Design。",
        }

    current_digest = _compute_sha256(design_path)

    if confirmation is None:
        return {
            "confirmed": False,
            "reason": "no_confirmation_record",
            "current_sha256": current_digest,
            "hint": "用户尚未确认当前 Design。请由用户明确确认后下游才能继续。",
        }

    stored_digest = confirmation.get("content_sha256", "")
    if current_digest == stored_digest:
        return {
            "confirmed": True,
            "reason": "hash_match",
            "current_sha256": current_digest,
            "confirmed_sha256": stored_digest,
            "confirmed_at": confirmation.get("confirmed_at"),
        }
    return {
        "confirmed": False,
        "reason": "hash_mismatch",
        "current_sha256": current_digest,
        "confirmed_sha256": stored_digest,
        "confirmed_at": confirmation.get("confirmed_at"),
        "hint": "design.md 在上次确认后被修改。需要用户重新确认后下游才能继续。",
    }


def determine_actual_stage(status: dict, project_root: Path) -> str:
    """根据产物存在情况给出一个历史兼容的实际阶段标识。
    vNext 不再线性推进，此字段仅用于兼容旧逻辑读取。"""
    current_stage = status.get("current_stage", "align")
    if current_stage in ("design-review", "prd-review", "prototype-review"):
        return current_stage

    artifacts = status.get("artifacts", {})
    has_design = _has_file(project_root, artifacts.get("design"))
    has_prd = _has_file(project_root, artifacts.get("prd"))
    has_prototype = _has_file(project_root, artifacts.get("prototype"))
    has_align = _has_file(project_root, artifacts.get("align"))

    if not has_design:
        return "design" if has_align else "align"
    if not has_prd and not has_prototype:
        return "design"
    if has_prd and has_prototype:
        return "done"
    return "design"  # 双下游中只完成一项时仍归 design 阶段


def build_available_actions(
    project_root: Path,
    status: dict,
    design_conf: dict,
) -> list[dict]:
    """构建 available_actions 列表：每个动作是否可用 + 原因。"""
    artifacts = status.get("artifacts", {})
    has_align = _has_file(project_root, artifacts.get("align"))
    has_design = _has_file(project_root, artifacts.get("design"))
    has_prd = _has_file(project_root, artifacts.get("prd"))
    has_prototype = _has_file(project_root, artifacts.get("prototype"))

    design_confirmed = design_conf.get("confirmed", False)
    design_conf_reason = design_conf.get("reason", "")

    actions: list[dict] = []

    # spm-align 可选
    actions.append({
        "action": "spm-align",
        "available": True,
        "reason": "可选需求整理模块，无需 Align 也可进入 Design。",
    })

    # spm-design：始终可用，重新生成或修改 Design
    actions.append({
        "action": "spm-design",
        "available": True,
        "reason": "可生成或修改 Design 基线（Product Definition）。",
    })

    # confirm-design：只有 design.md 存在才可用
    actions.append({
        "action": "confirm-design",
        "available": has_design,
        "reason": "design.md 存在，可由用户明确确认。" if has_design else "design.md 不存在，无法确认。",
    })

    # spm-prd：需 design.md 存在 + 已确认
    if not has_design:
        actions.append({"action": "spm-prd", "available": False, "reason": "design.md 不存在。"})
    elif not design_confirmed:
        actions.append({
            "action": "spm-prd",
            "available": False,
            "reason": f"Design 未确认（{design_conf_reason}）。请先由用户确认当前 Design。",
        })
    else:
        actions.append({
            "action": "spm-prd",
            "available": True,
            "reason": "Design 已确认，可直接生成 PRD。",
        })

    # spm-prototype：需 design.md 存在 + 已确认
    if not has_design:
        actions.append({"action": "spm-prototype", "available": False, "reason": "design.md 不存在。"})
    elif not design_confirmed:
        actions.append({
            "action": "spm-prototype",
            "available": False,
            "reason": f"Design 未确认（{design_conf_reason}）。请先由用户确认当前 Design。",
        })
    else:
        actions.append({
            "action": "spm-prototype",
            "available": True,
            "reason": "Design 已确认，可直接生成 Prototype。",
        })

    # 三个 Review：按需独立调用，不要求 metadata，不要求先通过其他 Review
    for review_action, target_artifact in [
        ("spm-design-review", artifacts.get("design")),
        ("spm-prd-review", artifacts.get("prd")),
        ("spm-prototype-review", artifacts.get("prototype")),
    ]:
        if _has_file(project_root, target_artifact):
            actions.append({
                "action": review_action,
                "available": True,
                "reason": "按需独立 Review，不构成门禁，不要求 metadata。",
            })
        else:
            actions.append({
                "action": review_action,
                "available": False,
                "reason": f"待审产物不存在：{target_artifact or '未指定'}",
            })

    # spm-fix：始终可用
    actions.append({
        "action": "spm-fix",
        "available": True,
        "reason": "高影响修改需回写 Design 并使旧确认失效；表现层修改可只改对应下游。",
    })

    # spm-prototype-mark：prototype 存在时可用
    if has_prototype:
        actions.append({
            "action": "spm-prototype-mark",
            "available": True,
            "reason": "保留标注能力，不修改原始 Prototype。",
        })
    else:
        actions.append({
            "action": "spm-prototype-mark",
            "available": False,
            "reason": "output/prototype/index.html 不存在。",
        })

    return actions


def collect_context(project_root: Path, stdin_status: bool = False) -> dict:
    status = load_status(project_root, stdin_status=stdin_status)
    if status is None:
        return {
            "error": "status.json not found",
            "hint": "请先初始化 .workflow/status.json（最小字段：current_stage、artifacts）。",
        }

    current_stage = status.get("current_stage", "align")
    if current_stage not in VALID_STAGES:
        return {
            "error": f"invalid stage: {current_stage}",
            "valid_stages": VALID_STAGES,
        }

    align_notes = load_align_notes(project_root)
    design_conf = design_confirmation_status(project_root)
    actual_stage = determine_actual_stage(status, project_root)
    available_actions = build_available_actions(project_root, status, design_conf)

    # 最小读取集合（参考用，不再构成硬门禁）
    read_set = MINIMAL_READ_SET.get(current_stage, [])
    resolved_read_set = {}
    for p in read_set:
        full_path = project_root / p
        resolved_read_set[p] = {
            "exists": full_path.exists(),
            "path": str(full_path),
        }

    # vNext：不再线性推进，next_recommended 始终为 null，由用户从 available_actions 自行选择
    next_recommended = None

    result = {
        "current_stage": current_stage,
        "actual_stage": actual_stage,
        "artifacts": status.get("artifacts", {}),
        # 历史字段保留兼容读取
        "metadata_paths": status.get("metadata_paths", {}),
        "latest_reviews": status.get("latest_reviews", {}),
        "align_notes": align_notes if align_notes else {},
        # vNext 字段
        "design_confirmation": design_conf,
        "available_actions": available_actions,
        "next_recommended": next_recommended,
        "minimal_read_set": resolved_read_set,
        "gate": {
            "can_proceed": True,  # vNext 不再由本脚本阻塞，由各 Skill 自行判断
            "blocking_issues": [],
            "note": "vNext 不再使用线性门禁；请参考 available_actions 判断可用动作。",
        },
    }

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="vNext 轻量导航和上下文脚本")
    parser.add_argument("--project-root", required=True, help="项目根目录")
    parser.add_argument("--stdin-status", action="store_true", help="从 stdin 读取 status.json 内容")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"错误: 项目根目录不存在: {project_root}", file=sys.stderr)
        return 1

    result = collect_context(project_root, stdin_status=args.stdin_status)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if "error" in result:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
