#!/usr/bin/env python3
"""stage-context.py — ShitPM 轻量导航和上下文脚本

职责：
- 优先探测 canonical 文件：output/align/align.md、output/design/design.md、output/prd/prd.md、output/prototype/
- 检查 Design 确认标记（.workflow/confirmations/design.json）的哈希是否仍然有效
- 输出 available_actions 列表（PRD 与 Prototype 是 Design 的两个独立下游）
- 输出每个动作的模型等级和推理深度建议（来自批准稿 ShitPM PRD §6）
- status.json 只作为兼容镜像，不得覆盖真实文件判断
- 无 status.json 时仍能正常输出上下文和可用动作
- 不生成 metadata，不修改产物

用法：
  python stage-context.py --project-root <path> [--stdin-status]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


VALID_STAGES = ["align", "design", "design-review", "prd", "prd-review", "prototype", "prototype-review", "fix", "done"]

DESIGN_ARTIFACT = "output/design/design.md"
CONFIRMATION_FILE = ".workflow/confirmations/design.json"

# canonical 文件相对路径（ShitPM：真实文件判断优先于 status.artifacts 镜像）
CANONICAL_FILES = {
    "align": "output/align/align.md",
    "design": "output/design/design.md",
    "prd": "output/prd/prd.md",
    "prototype": "output/prototype/index.html",
}


# 模型等级建议（来自 ShitPM PRD §6.2-6.3）
# 不发明新等级，只复用批准稿矩阵
MODEL_TIER_LIGHT = "轻量模型"
MODEL_TIER_DEEP = "深度推理模型"
MODEL_TIER_SCRIPT = "确定性脚本"
MODEL_TIER_UNSURE = "无法判断（按深度推理模型处理）"

# 推理深度建议（按动作给出，便于用户/Agent 选择模型）
REASONING_DEPTH = {
    "spm-align": "整理型可浅；探索型需深。",
    "spm-design": "默认深；首次生成需完整高影响推理。",
    "spm-prd": "Design 决策完整可浅；含未决问题或冲突需深。",
    "spm-prototype": "页面少、路径单一可浅；交互复杂需深。",
    "spm-design-review": "结构检查可浅；语义挑战需深。",
    "spm-prd-review": "结构与一致性检查可浅；坏味道和语义挑战需深。",
    "spm-prototype-review": "结构检查可浅；交互主路径挑战需深。",
    "spm-fix": "范围明确可浅；跨模块或语义变更需深。",
    "spm-prototype-mark": "默认浅；主动发现高影响问题时另行使用深度 Review。",
    "confirm-design": "无需模型。",
}

# 各动作默认模型等级建议（ShitPM PRD §6.3）
DEFAULT_MODEL_TIER = {
    "spm-align": "视任务而定（探索型用深度推理模型，整理型可用轻量模型）",
    "spm-design": MODEL_TIER_DEEP,
    "spm-prd": "根据确认版 Design 判断（决策完整可用轻量模型）",
    "spm-prototype": "根据交互和实现复杂度判断",
    "spm-design-review": MODEL_TIER_DEEP,
    "spm-prd-review": MODEL_TIER_DEEP,
    "spm-prototype-review": MODEL_TIER_DEEP,
    "spm-fix": "根据变更影响判断",
    "spm-prototype-mark": MODEL_TIER_LIGHT,
    "confirm-design": "—",
}


# 每个阶段推荐的最小读取集合（仅作为参考，不再构成硬门禁）
MINIMAL_READ_SET = {
    "align": [
        "references/align-writing.md",
        "templates/align.md",
    ],
    "design": [
        "contracts/context-loading.manifest.json",
        "scripts/python/context-pack.py",
        "scripts/python/context-budget.py",
        "scripts/python/context-runtime-check.py",
        "output/align/align.md",  # 可选业务输入
    ],
    "prd": [
        "contracts/context-loading.manifest.json",
        "scripts/python/context-pack.py",
        "scripts/python/context-budget.py",
        "scripts/python/prototype-structure.py",
        "contracts/subagent-context-contract.md",
        "output/design/design.md",
    ],
    "prototype": [
        "output/design/design.md",
        "templates/prototype.html",
        "references/prototype-writing.md",
    ],
    "fix": [],
    "design-review": [
        "output/design/design.md",
        "contracts/review-checklist.md",
        "contracts/design-review-checklist.md",
        "references/design-quality-rubric.md",
    ],
    "prd-review": [
        "output/design/design.md",
        "output/prd/prd.md",
        "contracts/review-checklist.md",
        "contracts/prd-review-checklist.md",
    ],
    "prototype-review": [
        "output/design/design.md",
        "output/prototype/index.html",
        "contracts/review-checklist.md",
        "contracts/prototype-review-checklist.md",
    ],
}


def load_status(project_root: Path, stdin_status: bool = False) -> dict | None:
    """读取 status.json。返回 dict 或 None。

    ShitPM：JSON 损坏时输出稳定错误而非崩溃；调用方按 __corrupted__ 标记处理。
    """
    if stdin_status:
        try:
            content = sys.stdin.read()
            return json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            return {"__corrupted__": True, "source": "stdin", "error": str(e)}
    status_path = project_root / ".workflow" / "status.json"
    if not status_path.exists():
        return None
    try:
        with open(status_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"__corrupted__": True, "source": str(status_path), "error": str(e)}


def load_align_notes(project_root: Path) -> dict | None:
    notes_path = project_root / ".workflow" / "runtime" / "align" / "align-notes.json"
    if not notes_path.exists():
        return None
    try:
        with open(notes_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def probe_canonical_files(project_root: Path) -> dict:
    """ShitPM：优先探测 canonical 文件，结果覆盖 status.artifacts 镜像。

    返回 {align: bool, design: bool, prd: bool, prototype: bool}
    """
    return {
        key: (project_root / rel).exists()
        for key, rel in CANONICAL_FILES.items()
    }


def _compute_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_design_confirmation(project_root: Path) -> dict | None:
    """读取确认标记。ShitPM：JSON 损坏时返回稳定错误标记。"""
    path = project_root / CONFIRMATION_FILE
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"__corrupted__": True, "source": str(path), "error": str(e)}


def _validate_confirmation_payload(payload: dict) -> list[str]:
    """对确认标记做必要字段校验，返回问题列表（空列表表示通过）。

    ShitPM：确认 Schema 进入执行路径，不依赖可选 jsonschema 库。
    """
    problems: list[str] = []
    if not isinstance(payload, dict):
        return ["confirmation payload 不是对象"]
    artifact = payload.get("artifact")
    if artifact != DESIGN_ARTIFACT:
        problems.append(f"artifact 必须固定为 {DESIGN_ARTIFACT}，实际为 {artifact!r}")
    digest = payload.get("content_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        problems.append("content_sha256 必须是 64 位十六进制字符串")
    else:
        try:
            int(digest, 16)
        except ValueError:
            problems.append("content_sha256 必须是十六进制字符串")
    confirmed_at = payload.get("confirmed_at")
    if not isinstance(confirmed_at, str) or not confirmed_at:
        problems.append("confirmed_at 必须是非空字符串")
    confirmed_by = payload.get("confirmed_by")
    if confirmed_by is not None and not isinstance(confirmed_by, str):
        problems.append("confirmed_by 必须是字符串或 null")
    note = payload.get("note")
    if note is not None and not isinstance(note, str):
        problems.append("note 必须是字符串或 null")
    return problems


def design_confirmation_status(project_root: Path) -> dict:
    """检查 Design 确认状态。返回 {confirmed, reason, current_sha256, confirmed_sha256, confirmed_at, problems}

    ShitPM：JSON 损坏或字段不合法时输出稳定错误，不抛 traceback。
    """
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

    if isinstance(confirmation, dict) and confirmation.get("__corrupted__"):
        return {
            "confirmed": False,
            "reason": "confirmation_corrupted",
            "current_sha256": current_digest,
            "hint": "确认标记 JSON 损坏。请用 design-confirmation.py confirm 重新写入。",
            "error": confirmation.get("error", ""),
            "source": confirmation.get("source", ""),
        }

    problems = _validate_confirmation_payload(confirmation)
    if problems:
        return {
            "confirmed": False,
            "reason": "confirmation_invalid",
            "current_sha256": current_digest,
            "hint": "确认标记字段不合法。请用 design-confirmation.py confirm 重新写入。",
            "problems": problems,
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


def determine_actual_stage(canonical: dict) -> str:
    """根据 canonical 文件存在情况给出历史兼容的实际阶段标识。

    ShitPM 不再线性推进，此字段仅用于兼容旧逻辑读取。
    """
    has_align = canonical.get("align", False)
    has_design = canonical.get("design", False)
    has_prd = canonical.get("prd", False)
    has_prototype = canonical.get("prototype", False)

    if not has_design:
        return "design" if has_align else "align"
    if not has_prd and not has_prototype:
        return "design"
    if has_prd and has_prototype:
        return "done"
    return "design"  # 双下游中只完成一项时仍归 design 阶段


def recommend_model_for_action(action: str) -> dict:
    """输出每个动作的模型等级和推理深度建议（来自 ShitPM PRD §6.2-6.3）。"""
    return {
        "model_tier": DEFAULT_MODEL_TIER.get(action, "—"),
        "reasoning_depth": REASONING_DEPTH.get(action, "—"),
    }


def build_available_actions(
    project_root: Path,
    canonical: dict,
    design_conf: dict,
) -> list[dict]:
    """构建 available_actions 列表：每个动作是否可用 + 原因 + 模型建议。

    ShitPM：优先用 canonical 文件探测结果，不依赖 status.artifacts 镜像。
    """
    has_align = canonical.get("align", False)
    has_design = canonical.get("design", False)
    has_prd = canonical.get("prd", False)
    has_prototype = canonical.get("prototype", False)

    design_confirmed = design_conf.get("confirmed", False)
    design_conf_reason = design_conf.get("reason", "")

    actions: list[dict] = []

    # spm-align 可选
    actions.append({
        "action": "spm-align",
        "available": True,
        "reason": "可选需求整理模块，无需 Align 也可进入 Design。",
        **recommend_model_for_action("spm-align"),
    })

    # spm-design：始终可用，重新生成或修改 Design
    actions.append({
        "action": "spm-design",
        "available": True,
        "reason": "可生成或修改 Design 基线（Product Definition）。",
        **recommend_model_for_action("spm-design"),
    })

    # confirm-design：只有 design.md 存在才可用
    actions.append({
        "action": "confirm-design",
        "available": has_design,
        "reason": "design.md 存在，可由用户明确确认。" if has_design else "design.md 不存在，无法确认。",
        **recommend_model_for_action("confirm-design"),
    })

    # spm-prd：需 design.md 存在 + 已确认
    if not has_design:
        actions.append({
            "action": "spm-prd",
            "available": False,
            "reason": "design.md 不存在。",
            **recommend_model_for_action("spm-prd"),
        })
    elif not design_confirmed:
        actions.append({
            "action": "spm-prd",
            "available": False,
            "reason": f"Design 未确认（{design_conf_reason}）。请先由用户确认当前 Design。",
            **recommend_model_for_action("spm-prd"),
        })
    else:
        actions.append({
            "action": "spm-prd",
            "available": True,
            "reason": "Design 已确认，可直接生成 PRD。",
            **recommend_model_for_action("spm-prd"),
        })

    # spm-prototype：需 design.md 存在 + 已确认
    if not has_design:
        actions.append({
            "action": "spm-prototype",
            "available": False,
            "reason": "design.md 不存在。",
            **recommend_model_for_action("spm-prototype"),
        })
    elif not design_confirmed:
        actions.append({
            "action": "spm-prototype",
            "available": False,
            "reason": f"Design 未确认（{design_conf_reason}）。请先由用户确认当前 Design。",
            **recommend_model_for_action("spm-prototype"),
        })
    else:
        actions.append({
            "action": "spm-prototype",
            "available": True,
            "reason": "Design 已确认，可直接生成 Prototype。",
            **recommend_model_for_action("spm-prototype"),
        })

    # 三个 Review：按需独立调用，不要求 metadata，不要求先通过其他 Review
    for review_action, canonical_key in [
        ("spm-design-review", "design"),
        ("spm-prd-review", "prd"),
        ("spm-prototype-review", "prototype"),
    ]:
        if canonical.get(canonical_key, False):
            actions.append({
                "action": review_action,
                "available": True,
                "reason": "按需独立 Review，不构成门禁，不要求 metadata。",
                **recommend_model_for_action(review_action),
            })
        else:
            actions.append({
                "action": review_action,
                "available": False,
                "reason": f"待审产物不存在：{CANONICAL_FILES[canonical_key]}",
                **recommend_model_for_action(review_action),
            })

    # spm-fix：始终可用
    actions.append({
        "action": "spm-fix",
        "available": True,
        "reason": "高影响修改需回写 Design 并使旧确认失效；表现层修改可只改对应下游。",
        **recommend_model_for_action("spm-fix"),
    })

    # spm-prototype-mark：prototype 存在时可用
    if has_prototype:
        actions.append({
            "action": "spm-prototype-mark",
            "available": True,
            "reason": "保留标注能力，不修改原始 Prototype。",
            **recommend_model_for_action("spm-prototype-mark"),
        })
    else:
        actions.append({
            "action": "spm-prototype-mark",
            "available": False,
            "reason": "output/prototype/index.html 不存在。",
            **recommend_model_for_action("spm-prototype-mark"),
        })

    return actions


def resolve_bundle_resources(bundle_root: Path | None = None) -> dict:
    """按 bundle root 解析 templates/references/contracts/schemas。

    bundle root 推断规则：
    1. 脚本位于 <bundle>/scripts/python/ 下，向上一级为 scripts，再向上一级为 bundle root
    2. 若链接安装到 Codex 等 host 目录，链接目标即 bundle root

    返回 {bundle_root, templates, references, contracts, schemas, exists}
    """
    if bundle_root is None:
        script_path = Path(__file__).resolve()
        # scripts/python/stage-context.py → scripts/python → scripts → bundle_root
        bundle_root = script_path.parent.parent.parent
    else:
        bundle_root = bundle_root.resolve()
    resources = {
        "bundle_root": str(bundle_root),
        "templates": str(bundle_root / "templates"),
        "references": str(bundle_root / "references"),
        "contracts": str(bundle_root / "contracts"),
        "schemas": str(bundle_root / "schemas"),
        "exists": bundle_root.exists(),
        "has_templates": (bundle_root / "templates").exists(),
        "has_references": (bundle_root / "references").exists(),
        "has_contracts": (bundle_root / "contracts").exists(),
        "has_schemas": (bundle_root / "schemas").exists(),
    }
    return resources


def collect_context(project_root: Path, stdin_status: bool = False, bundle_root: Path | None = None) -> dict:
    """ShitPM：无 status.json 时仍能正常输出，优先用 canonical 文件探测。"""
    status = load_status(project_root, stdin_status=stdin_status)
    canonical = probe_canonical_files(project_root)
    design_conf = design_confirmation_status(project_root)
    available_actions = build_available_actions(project_root, canonical, design_conf)
    actual_stage = determine_actual_stage(canonical)

    status_corrupted = isinstance(status, dict) and status.get("__corrupted__")
    status_dict = status if (isinstance(status, dict) and not status_corrupted) else {}

    current_stage = status_dict.get("current_stage", actual_stage)
    if current_stage not in VALID_STAGES:
        current_stage = actual_stage

    align_notes = load_align_notes(project_root)

    # 最小读取集合（参考用，不再构成硬门禁），优先解析 bundle 路径
    bundle_resources = resolve_bundle_resources(bundle_root)
    bundle_root = Path(bundle_resources["bundle_root"])
    read_set = MINIMAL_READ_SET.get(current_stage, [])
    resolved_read_set = {}
    for p in read_set:
        # bundle 资源（references/templates/contracts/schemas）按 bundle root 解析
        if p.startswith(("references/", "templates/", "contracts/", "schemas/")):
            full_path = bundle_root / p
        else:
            full_path = project_root / p
        resolved_read_set[p] = {
            "exists": full_path.exists(),
            "path": str(full_path),
        }

    # ShitPM：不再线性推进，next_recommended 始终为 null，由用户从 available_actions 自行选择
    next_recommended = None

    # status.artifacts 作为兼容镜像保留输出，但不参与决策
    status_artifacts = status_dict.get("artifacts", {})
    # ShitPM：合并 canonical 探测结果到 artifacts_mirror，供 Skill 参考
    artifacts_mirror = {
        "status_registered": status_artifacts,
        "canonical_detected": {k: CANONICAL_FILES[k] for k, v in canonical.items() if v},
    }

    result = {
        "current_stage": current_stage,
        "actual_stage": actual_stage,
        "artifacts": status_artifacts,
        "artifacts_mirror": artifacts_mirror,
        # 历史字段保留兼容读取
        "metadata_paths": status_dict.get("metadata_paths", {}),
        "latest_reviews": status_dict.get("latest_reviews", {}),
        "align_notes": align_notes if align_notes else {},
        # ShitPM 字段
        "design_confirmation": design_conf,
        "available_actions": available_actions,
        "next_recommended": next_recommended,
        "minimal_read_set": resolved_read_set,
        "bundle_resources": bundle_resources,
        "gate": {
            "can_proceed": True,  # ShitPM 不再由本脚本阻塞，由各 Skill 自行判断
            "blocking_issues": [],
            "note": "ShitPM 不再使用线性门禁；请参考 available_actions 判断可用动作。",
        },
    }

    if status is None:
        result["status_source"] = "missing"
        result["status_hint"] = "无 .workflow/status.json；canonical 文件探测已接管产物判断。"
    elif status_corrupted:
        result["status_source"] = "corrupted"
        result["status_error"] = status.get("error", "")
        result["status_hint"] = "status.json 损坏；canonical 文件探测已接管产物判断。请修复或删除 status.json。"
    else:
        result["status_source"] = "loaded"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="ShitPM 轻量导航和上下文脚本")
    parser.add_argument("--project-root", required=True, help="项目根目录")
    parser.add_argument("--stdin-status", action="store_true", help="从 stdin 读取 status.json 内容")
    parser.add_argument("--bundle-root", type=Path, help="ShitPM bundle 根目录，默认脚本所在 bundle")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"错误: 项目根目录不存在: {project_root}", file=sys.stderr)
        return 1

    result = collect_context(project_root, stdin_status=args.stdin_status, bundle_root=args.bundle_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
