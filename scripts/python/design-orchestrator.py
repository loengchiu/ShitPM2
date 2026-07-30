from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from material_revision import file_digest, material_revision as shared_material_revision, source_id_for as shared_source_id_for

REPO_ROOT = SCRIPT_DIR.parent.parent
BUNDLE_ROOT = Path(os.environ.get("SHITPM_BUNDLE_ROOT", "C:/Users/guduj/.codex/shitpm"))
SCHEMA_VERSION = "design-orchestration/v2"
RUNTIME_REL = Path(".workflow/runtime/context/design")
MATERIALS_REL = Path(".workflow/runtime/materials")
MAX_ACTION_ATTEMPTS = 3
SUPPORTED_MODES = ("simple", "full")
ACTION_SCHEMA_PATH = REPO_ROOT / "schemas" / "design-orchestration-action.schema.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hash_object(value: Any) -> str:
    return sha256_text(canonical(value))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def rel_path(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def resolve_rel(project_root: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else project_root / candidate


def file_hash(path: Path) -> str | None:
    try:
        return file_digest(path)
    except (OSError, UnicodeError):
        return None


def safe_file_hash(project_root: Path, value: str | None) -> str | None:
    if not value:
        return None
    return file_hash(resolve_rel(project_root, value))


def runtime_dir(project_root: Path) -> Path:
    return project_root / RUNTIME_REL


def material_dir(project_root: Path) -> Path:
    return project_root / MATERIALS_REL


def state_path(project_root: Path) -> Path:
    return runtime_dir(project_root) / "orchestrator-state.json"


def receipt_path(project_root: Path, task_id: str) -> Path:
    safe = task_id.replace(":", "--")
    return runtime_dir(project_root) / "receipts" / f"{safe}.json"


def default_model_calls() -> dict[str, int]:
    return {"total": 0, "material_fact_extraction": 0, "design_analysis": 0, "business_model_challenge": 0, "design_writing": 0}


def load_state(project_root: Path) -> dict[str, Any]:
    state = read_json(state_path(project_root))
    if state and state.get("schema_version") == SCHEMA_VERSION:
        state.setdefault("nodes", {})
        state.setdefault("events", [])
        state.setdefault("failures", [])
        state.setdefault("answers", {})
        state.setdefault("attempts", {})
        state.setdefault("model_calls", default_model_calls())
        state.setdefault("completed", False)
        return state
    return {"schema_version": SCHEMA_VERSION, "run_id": sha256_text(f"{project_root.resolve()}:{now()}")[:16], "created_at": now(), "nodes": {}, "events": [], "failures": [], "answers": {}, "attempts": {}, "model_calls": default_model_calls(), "completed": False}


def save_state(project_root: Path, state: dict[str, Any]) -> None:
    write_json(state_path(project_root), state)


def read_input_manifest(project_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    value = read_json(runtime_dir(project_root) / "inputs/input-manifest.json")
    if not value:
        return None, "input-manifest.json 不存在或不是 JSON 对象"
    if value.get("schema_version") not in ("design-input/v1", "design-input/v2"):
        return None, "input-manifest.json schema_version 不受支持"
    if value.get("mode") not in (*SUPPORTED_MODES, None):
        return None, "mode 必须是 simple、full 或未指定"
    if not isinstance(value.get("material_inputs", []), list):
        return None, "material_inputs 必须是数组"
    for key in ("request_path", "align_path"):
        if value.get(key):
            path = resolve_rel(project_root, value[key])
            # Align 是首个动作，初始化时其规范输出尚未生成；下游动作再要求它存在。
            if key == "align_path" and not path.exists():
                continue
            if not path.is_file():
                return None, f"{key} 不存在: {value[key]}"
    for item in value.get("material_inputs", []):
        if not isinstance(item, str) or not resolve_rel(project_root, item).is_file():
            return None, f"材料输入不存在: {item}"
    return value, None


def input_hash(project_root: Path, manifest: dict[str, Any], include_align: bool = True) -> str:
    payload = {
        "request": safe_file_hash(project_root, manifest.get("request_path")),
        "align": (safe_file_hash(project_root, manifest.get("align_path")) if include_align and manifest.get("align_path") else None),
        "materials": [(item, safe_file_hash(project_root, item)) for item in manifest.get("material_inputs", [])],
        "mode": manifest.get("mode"),
    }
    return f"sha256:{hash_object(payload)}"


def material_sources(project_root: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    sources = []
    for item in manifest.get("material_inputs", []):
        path = resolve_rel(project_root, item).resolve()
        sources.append({
            "source_id": source_id_for(rel_path(project_root, path)),
            "path": rel_path(project_root, path),
            "sha256": safe_file_hash(project_root, item) or "",
        })
    return sources


def material_revision(project_root: Path, manifest: dict[str, Any]) -> str:
    return shared_material_revision(material_sources(project_root, manifest))


def decisions(project_root: Path) -> list[dict[str, Any]]:
    value = read_json(runtime_dir(project_root) / "inputs/user-decisions.json") or {"decisions": []}
    raw = value.get("decisions", []) if isinstance(value, dict) else []
    return [item for item in raw if isinstance(item, dict) and item.get("question_id")]


def answer_scope_matches(decision: dict[str, Any], task_id: str, task_kind: str, stage: str) -> bool:
    scopes = decision.get("invalidates")
    if not isinstance(scopes, list) or not scopes:
        # 没有影响声明时采用保守全量失效，避免把高影响答案误判为无关。
        return True
    aliases = {
        "analysis": {"analysis", "a", "b", "c"},
        "challenge": {"challenge", "baseline", "b6-model-review", "c4-cross-layer-review"},
        "writing": {"writing", "design_writer", "design-editor", "simple-design"},
    }
    for scope in scopes:
        if not isinstance(scope, str):
            continue
        if scope in {"all", "*", task_id, task_kind, stage}:
            return True
        if scope in aliases and (task_kind in aliases[scope] or stage in aliases[scope] or task_id in aliases[scope]):
            return True
    return False


def answer_hash(project_root: Path) -> str:
    return f"sha256:{hash_object({"decisions": decisions(project_root)})}"


def answer_hash_for_task(project_root: Path, task: dict[str, Any]) -> str:
    task_id = task.get("task_id", "")
    task_kind = task.get("task_kind", "")
    stage = task.get("stage", "")
    relevant = [item for item in decisions(project_root) if answer_scope_matches(item, task_id, task_kind, stage)]
    return f"sha256:{hash_object({"decisions": relevant})}"


def dependency_fingerprints(project_root: Path, task: dict[str, Any]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for dependency in task.get("depends_on", []):
        receipt = read_json(receipt_path(project_root, dependency))
        if not receipt:
            result[dependency] = None
            continue
        # 同一输出内容在不同输入下也必须触发下游重跑，因此同时绑定输入和输出收据。
        result[dependency] = f"sha256:{hash_object({'input_hashes': receipt.get('input_hashes', {}), 'output_hashes': receipt.get('output_hashes', {})})}"
    return result


def source_id_for(value: str) -> str:
    return shared_source_id_for(value)


def rule_pack(project_root: Path, stage: str, mode: str) -> dict[str, Any]:
    files = []
    for root in (BUNDLE_ROOT, REPO_ROOT):
        if files:
            break
        for folder in ("skills", "contracts", "references", "schemas", "templates"):
            base = root / folder
            if base.is_dir():
                files.extend(sorted((p.relative_to(root).as_posix(), file_hash(p) or "") for p in base.rglob("*") if p.is_file()))
    content_hash = f"sha256:{hash_object({'stage': stage, 'mode': mode, 'files': files})}"
    cache_dir = project_root / "design-rule-cache" / content_hash.removeprefix("sha256:")
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": "design-rule-pack/v2", "stage": stage, "mode": mode, "content_hash": content_hash, "files": [{"path": p, "hash": h} for p, h in files]}
    write_json(cache_dir / "manifest.json", manifest)
    return {"content_hash": content_hash, "cache_path": rel_path(project_root, cache_dir / "manifest.json"), "stage": stage, "mode": mode}


def material_manifest(project_root: Path) -> dict[str, Any] | None:
    return read_json(material_dir(project_root) / "manifest.json")


def valid_materials(project_root: Path, manifest: dict[str, Any]) -> tuple[bool, str]:
    cached = material_manifest(project_root)
    if not cached or cached.get("material_revision") != material_revision(project_root, manifest):
        return False, "材料版本不存在或已变化"
    facts = read_json(material_dir(project_root) / "facts.json")
    if not facts or facts.get("material_revision") != material_revision(project_root, manifest):
        return False, "材料事实库不存在或已陈旧"
    for item in manifest.get("material_inputs", []):
        sid = source_id_for(item)
        fact = read_json(material_dir(project_root) / "facts" / f"{sid}.json")
        if not fact or fact.get("source_path") != item or fact.get("source_hash") != safe_file_hash(project_root, item):
            return False, "分来源材料事实缺失或已陈旧"
    return True, "ok"


def facts_valid(project_root: Path, manifest: dict[str, Any]) -> bool:
    facts = read_json(material_dir(project_root) / "facts.json")
    return bool(facts and facts.get("material_revision") == material_revision(project_root, manifest))


def task_definitions(mode: str, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []

    def add(task_id: str, deps: list[str], batch: str, kind: str, outputs: list[str], stage: str, max_attempts: int = MAX_ACTION_ATTEMPTS) -> None:
        tasks.append({
            "task_id": task_id,
            "mode": mode,
            "task_kind": kind,
            "depends_on": deps,
            "batch_key": batch,
            "expected_outputs": outputs,
            "stage": stage,
            "max_attempts": max_attempts,
        })

    add("align", [], "align", "align", [
        "output/align/align.md",
        ".workflow/runtime/align/align-notes.json",
    ], "align")
    # 物料索引可复用；preview_next 已先完成 Align，确保首次运行不会绕过 Align。
    add("material-index", [], "materials", "material_preparation", [
        ".workflow/runtime/materials/manifest.json",
        ".workflow/runtime/materials/source-index.json",
    ], "materials")
    for item in manifest.get("material_inputs", []):
        sid = source_id_for(item)
        add(f"material-facts:{sid}", ["material-index"], "material-facts", "material_fact_extraction", [
            f".workflow/runtime/materials/facts/{sid}.json",
        ], "materials")
    fact_ids = [t["task_id"] for t in tasks if t["task_id"].startswith("material-facts:")]
    add("material-merge", fact_ids or ["material-index"], "materials", "material_merge", [
        ".workflow/runtime/materials/facts.json",
    ], "materials")

    if mode == "simple":
        add("simple-design", ["material-merge"], "simple-design", "design_writer", [
            "output/design/design.md",
            "output/design/decision-notes.md",
        ], "simple")
        return tasks

    add("a-layer", ["material-merge"], "a-layer", "baseline", [
        ".workflow/runtime/context/design/baselines/a-baseline.json",
    ], "a")
    add("b-layer", ["a-layer"], "b-layer", "baseline", [
        ".workflow/runtime/context/design/baselines/b-baseline.json",
        ".workflow/runtime/context/design/conflicts/business-conflicts.json",
    ], "b")
    add("c-layer", ["a-layer", "b-layer"], "c-layer", "baseline", [
        ".workflow/runtime/context/design/baselines/c-baseline.json",
        ".workflow/runtime/context/design/conflicts/cross-layer-conflicts.json",
        ".workflow/runtime/context/design/baselines/design-brief.json",
    ], "c")
    add("design-editor", ["a-layer", "b-layer", "c-layer"], "editor", "design_writer", [
        "output/design/design.md",
        "output/design/decision-notes.md",
    ], "writing")
    return tasks

def task_map(mode: str, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {t["task_id"]: t for t in task_definitions(mode, manifest)}


def task_input_files(project_root: Path, task: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    task_id = task["task_id"]
    if task_id.startswith("material-facts:"):
        sid = task_id.split(":", 1)[1]
        return [item for item in manifest.get("material_inputs", []) if source_id_for(item) == sid]
    files = []
    if task_id == "align":
        files.extend([manifest.get("request_path"), *manifest.get("material_inputs", [])])
        return [item for item in dict.fromkeys(files) if item]
    if task["task_kind"] == "material_preparation":
        files.extend(manifest.get("material_inputs", []))
    elif task["task_kind"] == "material_merge":
        files.extend([f".workflow/runtime/materials/facts/{source_id_for(item)}.json" for item in manifest.get("material_inputs", [])])
    elif task_id == "a-layer":
        files.extend([manifest.get("align_path"),manifest.get("request_path"), ".workflow/runtime/materials/facts.json"])
    elif task_id == "b-layer":
        files.extend([manifest.get("align_path"),manifest.get("request_path"), ".workflow/runtime/materials/facts.json", ".workflow/runtime/context/design/baselines/a-baseline.json"])
    elif task_id == "c-layer":
        files.extend([manifest.get("align_path"),manifest.get("request_path"), ".workflow/runtime/materials/facts.json", ".workflow/runtime/context/design/baselines/a-baseline.json", ".workflow/runtime/context/design/baselines/b-baseline.json", ".workflow/runtime/context/design/conflicts/business-conflicts.json"])
    elif task_id == "design-editor":
        files.extend([manifest.get("align_path"),manifest.get("request_path"), ".workflow/runtime/materials/facts.json", ".workflow/runtime/context/design/baselines/a-baseline.json", ".workflow/runtime/context/design/baselines/b-baseline.json", ".workflow/runtime/context/design/baselines/c-baseline.json", ".workflow/runtime/context/design/baselines/design-brief.json", ".workflow/runtime/context/design/conflicts/business-conflicts.json", ".workflow/runtime/context/design/conflicts/cross-layer-conflicts.json"])
    else:
        for key in ("request_path", "align_path"):
            if manifest.get(key):
                files.append(manifest[key])
        if task["task_kind"] not in {"material_merge", "report"}:
            files.append(".workflow/runtime/materials/facts.json")
    return [item for item in dict.fromkeys(files) if item]


def input_hashes(project_root: Path, task: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {item: safe_file_hash(project_root, item) for item in task_input_files(project_root, task, manifest)}
    if task["task_id"].startswith("material-facts:"):
        # 分来源事实只绑定本来源，避免其他来源变化导致重复提取。
        return values
    values["__input_hash__"] = input_hash(
        project_root,
        manifest,
        include_align=task.get("task_id") not in {"align", "material-index", "material-merge"},
    )
    values["__material_revision__"] = material_revision(project_root, manifest)
    values["__answers__"] = answer_hash_for_task(project_root, task)
    values["__dependency_fingerprints__"] = dependency_fingerprints(project_root, task)
    return values


def output_valid(project_root: Path, raw: str) -> bool:
    path = resolve_rel(project_root, raw)
    if not path.exists():
        return False
    if path.suffix == ".json":
        return read_json(path) is not None
    return bool(path.read_text(encoding="utf-8").strip())


def outputs_valid(project_root: Path, task: dict[str, Any]) -> bool:
    return all(output_valid(project_root, raw) for raw in task["expected_outputs"])


def task_fresh(project_root: Path, task: dict[str, Any], manifest: dict[str, Any], state: dict[str, Any]) -> bool:
    if not outputs_valid(project_root, task):
        return False
    current_inputs = input_hashes(project_root, task, manifest)
    node = state.get("nodes", {}).get(task["task_id"], {})
    receipt = read_json(receipt_path(project_root, task["task_id"])) or {}
    accepted = node.get("last_input_hashes") or receipt.get("input_hashes")
    if accepted != current_inputs:
        return False
    recorded_outputs = node.get("accepted_output_hashes") if "accepted_output_hashes" in node else receipt.get("output_hashes")
    if recorded_outputs is None:
        return False
    return all(recorded_outputs.get(raw) == file_hash(resolve_rel(project_root, raw)) for raw in task["expected_outputs"])


def task_status(project_root: Path, task: dict[str, Any], manifest: dict[str, Any], state: dict[str, Any], tasks: dict[str, dict[str, Any]], cache: dict[str, str] | None = None) -> str:
    cache = cache if cache is not None else {}
    task_id = task["task_id"]
    if task_id in cache:
        return cache[task_id]
    node = state.get("nodes", {}).get(task_id, {})
    if task_fresh(project_root, task, manifest, state):
        cache[task_id] = "completed"
        return "completed"
    if node.get("status") == "failed" and node.get("attempts", 0) >= task.get("max_attempts", MAX_ACTION_ATTEMPTS):
        cache[task_id] = "failed"
        return "failed"
    if any(task_status(project_root, tasks[dep], manifest, state, tasks, cache) != "completed" for dep in task["depends_on"] if dep in tasks):
        cache[task_id] = "pending"
        return "pending"
    cache[task_id] = "ready"
    return "ready"


def command_for_task(task: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any] | None:
    if task["task_id"] != "material-index":
        return None
    args = [
        "scripts/python/source-index.py",
        "--project-root", ".",
        "--output-dir", ".workflow/runtime/materials",
    ]
    for item in manifest.get("material_inputs", []):
        args.extend(["--input", item])
    return {"program": "python", "script": "scripts/python/source-index.py", "args": args[1:]}


def output_contract(task: dict[str, Any]) -> dict[str, Any]:
    task_id = task["task_id"]
    task_kind = task["task_kind"]
    if task_kind == "align":
        return {
            "type": "object",
            "schema_ref": "$BUNDLE/templates/align.md",
            "required": ["blocking_gaps", "needs_ask_back", "ask_back_reason", "judgement_note", "last_updated_at"],
        }
    if task_id.startswith("material-facts:"):
        return {
            "type": "object",
            "schema_ref": "$BUNDLE/references/design-fact-format.md#分来源事实文件",
            "required": ["schema_version", "source_path", "source_hash", "material_revision", "facts"],
            "properties": {
                "schema_version": {"type": "string", "enum": ["material-fact/v2"]},
                "source_path": {"type": "string", "minLength": 1},
                "source_hash": {"type": "string", "minLength": 1},
                "material_revision": {"type": "string", "minLength": 1},
                "facts": {"type": "array"},
            },
        }
    if task_kind == "material_merge":
        return {
            "type": "object",
            "schema_ref": "$BUNDLE/references/design-fact-format.md#合并事实库",
            "required": ["version", "material_revision", "confirmed_facts", "source_conflicts", "missing_information", "non_derivable_items"],
            "properties": {
                "version": {"type": "integer", "enum": [1]},
                "material_revision": {"type": "string", "minLength": 1},
                "confirmed_facts": {"type": "array"},
                "source_conflicts": {"type": "array"},
                "missing_information": {"type": "array"},
                "non_derivable_items": {"type": "array"},
            },
        }
    if task_kind == "baseline":
        return {
            "type": "object",
            "schema_ref": "$BUNDLE/references/design-baseline-format.md#公共-json-包装",
            "required": ["schema_version", "task_id", "status", "coverage", "source_refs"],
            "properties": {
                "schema_version": {"type": "string", "enum": ["design-analysis/v2"]},
                "material_revision": {"type": "string", "minLength": 1},
                "task_id": {"type": "string", "minLength": 1},
                "status": {"type": "string", "enum": ["completed", "success"]},
                "coverage": {"type": "array"},
                "source_refs": {"type": "array"},
            },
        }
    return {"type": "object", "required": []}


def completion_checks(task: dict[str, Any]) -> list[str]:
    task_id = task["task_id"]
    task_kind = task["task_kind"]
    checks = ["输出文件存在", "输入哈希仍然匹配"]
    if task_kind == "align":
        checks.extend(["按 templates/align.md 写入完整需求事实对齐稿", "按 schemas/align-notes.schema.json 写入对齐结果和未决问题"])
    elif task_id.startswith("material-facts:"):
        checks.extend(["按 references/design-fact-format.md 写入 material-fact/v2 分来源事实", "source_path/source_hash/material_revision/facts 均存在"] )
    elif task_kind == "material_merge":
        checks.extend(["按 references/design-fact-format.md 写入 version=1 合并事实库", "四个事实分类数组均存在且每条事实可定位来源"] )
    elif task_kind == "baseline":
        checks.extend(["按 references/design-baseline-format.md 写入 design-analysis/v2 交接资产", "schema_version/status/coverage/source_refs 通过交接门禁"] )
    return checks


def make_action(project_root: Path, task: dict[str, Any], manifest: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
    mode = manifest.get("mode") or "full"
    isolated = task["task_kind"] not in {"material_preparation", "material_merge"}
    input_files = task_input_files(project_root, task, manifest)
    action = {"action_id": task["task_id"], "task_id": task["task_id"], "type": "run_isolated_agent" if isolated else "run_command", "role": task["task_kind"], "objective": f"完成 {task['task_id']} 的单一责任", "mode": mode, "task_kind": task["task_kind"], "depends_on": task["depends_on"], "batch_key": task["batch_key"], "input_files": input_files, "input_hashes": input_hashes(project_root, task, manifest), "rule_pack_ref": rule_pack(project_root, task["stage"], mode), "expected_outputs": task["expected_outputs"], "output_schema": output_contract(task), "completion_check": completion_checks(task), "forbidden_inputs": ["完整父对话历史", "未列出的原始材料", "其他专项的完整分析正文", "主任务自动规划的新动作"], "allowed_evidence_ranges": [{"path": item, "range": "必要的定点片段"} for item in input_files], "max_attempts": task.get("max_attempts", MAX_ACTION_ATTEMPTS)}
    command = command_for_task(task, manifest)
    if command:
        action["command"] = command
    if isolated:
        action["fork_context"] = False
    if reason:
        action["reason"] = reason
    return action


def compile_task(project_root: Path, action: dict[str, Any]) -> None:
    base = runtime_dir(project_root) / "tasks"
    base.mkdir(parents=True, exist_ok=True)
    safe = action["action_id"].replace(":", "--")
    json_path = base / f"{safe}.json"
    md_path = base / f"{safe}.md"
    action["task_json_path"] = rel_path(project_root, json_path)
    action["task_path"] = rel_path(project_root, md_path)
    write_json(json_path, action)
    md_path.write_text("# Design 编排任务\n\n" + "\n".join(f"- {k}：{v}" for k, v in action.items() if k not in {"input_hashes", "rule_pack_ref"}), encoding="utf-8")


def material_ready(project_root: Path, manifest: dict[str, Any], tasks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    valid, _ = valid_materials(project_root, manifest)
    if valid:
        return []
    result = []
    index = tasks["material-index"]
    cached = material_manifest(project_root)
    if not cached or cached.get("material_revision") != material_revision(project_root, manifest):
        return [make_action(project_root, index, manifest, "材料索引不存在或版本变化")]
    facts_missing = []
    state = load_state(project_root)
    for task_id, task in tasks.items():
        if task_id.startswith("material-facts:"):
            item = next((x for x in manifest.get("material_inputs", []) if source_id_for(x) == task_id.split(":", 1)[1]), None)
            if item and not task_fresh(project_root, task, manifest, state):
                facts_missing.append(make_action(project_root, task, manifest, "来源新增或内容变化"))
    if facts_missing:
        return facts_missing
    return [make_action(project_root, tasks["material-merge"], manifest, "分来源事实已完成，需合并材料事实库")] if not facts_valid(project_root, manifest) else []


def user_questions(project_root: Path) -> list[dict[str, Any]]:
    value = read_json(runtime_dir(project_root) / "conflicts/user-questions.json") or {"questions": []}
    return value.get("questions", []) if isinstance(value.get("questions", []), list) else []


def unanswered(project_root: Path) -> list[dict[str, Any]]:
    decisions = read_json(runtime_dir(project_root) / "inputs/user-decisions.json") or {"decisions": []}
    answered = {x.get("question_id") for x in decisions.get("decisions", []) if isinstance(x, dict)}
    return [q for q in user_questions(project_root) if q.get("blocking", True) and q.get("question_id") not in answered]


def migration_required(project_root: Path) -> dict[str, Any] | None:
    old = read_json(runtime_dir(project_root) / "run.json")
    if old and old.get("schema_version") not in (None, SCHEMA_VERSION):
        return {"state": "migration_required", "migration_required": True, "ready_actions": [], "message": "发现旧版 run.json，未自动迁移；请新建 v2 运行。"}
    return None


def preview_next(project_root: Path) -> dict[str, Any]:
    migration = migration_required(project_root)
    if migration:
        return migration
    manifest, error = read_input_manifest(project_root)
    if error:
        return {"state": "failed", "error": error, "ready_actions": [], "blocked_by_user_questions": [], "completed_actions": []}
    assert manifest is not None
    mode = manifest.get("mode")
    if mode is None:
        action = {"action_id": "select-mode", "type": "ask_user", "role": "mode_selection", "objective": "选择简单模式或完整模式", "options": list(SUPPORTED_MODES), "input_files": [], "input_hashes": {"__input_hash__": input_hash(project_root, manifest)}, "rule_pack_ref": rule_pack(project_root, "mode-selection", "simple"), "expected_outputs": [".workflow/runtime/context/design/inputs/input-manifest.json"], "output_schema": {"type": "object"}, "completion_check": ["用户只选择一次模式"], "forbidden_inputs": ["自动根据材料判断模式"], "allowed_evidence_ranges": []}
        compile_task(project_root, action)
        return {"state": "waiting_user", "ready_actions": [action], "blocked_by_user_questions": [], "completed_actions": []}
    state = load_state(project_root)
    tasks = task_map(mode, manifest)
    status_cache: dict[str, str] = {}
    align_status = task_status(project_root, tasks["align"], manifest, state, tasks, status_cache)
    if align_status == "ready":
        action = make_action(project_root, tasks["align"], manifest, "Design 必须先完成 Align 需求事实形成")
        compile_task(project_root, action)
        return {"state": "ready", "ready_actions": [action], "blocked_by_user_questions": [], "completed_actions": []}
    if align_status == "failed":
        return {"state": "failed", "error": "Align 动作已达到重试上限", "ready_actions": [], "blocked_by_user_questions": [], "completed_actions": []}
    blocked = unanswered(project_root)
    if blocked:
        questions = []
        for q in blocked:
            questions.append({"action_id": f"question:{q.get('question_id')}", "type": "ask_user", "role": "user_decision", "objective": q.get("question", "请补充高影响决策"), "question": q, "input_files": [".workflow/runtime/context/design/conflicts/user-questions.json"], "input_hashes": {"__answers__": answer_hash(project_root)}, "rule_pack_ref": rule_pack(project_root, "questions", mode), "expected_outputs": [".workflow/runtime/context/design/inputs/user-decisions.json"], "output_schema": {"type": "object"}, "completion_check": ["问题已回答"], "forbidden_inputs": [], "allowed_evidence_ranges": []})
        return {"state": "waiting_user", "ready_actions": questions, "blocked_by_user_questions": blocked, "completed_actions": []}
    ready = material_ready(project_root, manifest, tasks)
    if not ready:
        status_cache = {}
        for task_id, task in tasks.items():
            if task_id.startswith("material-") or task_id == "align":
                continue
            if task_status(project_root, task, manifest, state, tasks, status_cache) == "ready":
                ready.append(make_action(project_root, task, manifest, "依赖已满足"))
        completed = [task_id for task_id, task in tasks.items() if task_status(project_root, task, manifest, state, tasks, status_cache) == "completed"]
        if not ready and len(completed) == len(tasks):
            state["completed"] = True
            save_state(project_root, state)
            return {"state": "completed", "ready_actions": [], "blocked_by_user_questions": [], "completed_actions": completed}
    for action in ready:
        compile_task(project_root, action)
    return {"state": "ready" if ready else "failed", "ready_actions": ready, "blocked_by_user_questions": [], "completed_actions": [], "model_calls": load_state(project_root).get("model_calls", default_model_calls())}


def next_action(project_root: Path) -> dict[str, Any]:
    return preview_next(project_root)


def _schema_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }.get(expected, True)


def _validate_schema(value: Any, schema: dict[str, Any], path: str = "$", root: dict[str, Any] | None = None) -> str | None:
    root = root or schema
    expected_type = schema.get("type")
    if expected_type and not _schema_type_matches(value, expected_type):
        return f"{path} 类型应为 {expected_type}"
    if "enum" in schema and value not in schema["enum"]:
        return f"{path} 不在允许值范围内"
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            return f"{path} 不能为空"
    if isinstance(value, (int, float)) and "minimum" in schema and value < schema["minimum"]:
        return f"{path} 小于最小值"
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            return f"{path} 至少需要 {schema['minItems']} 项"
        if schema.get("uniqueItems"):
            serialized = [canonical(item) for item in value]
            if len(serialized) != len(set(serialized)):
                return f"{path} 不允许重复项"
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                error = _validate_schema(item, item_schema, f"{path}[{index}]", root)
                if error:
                    return error
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                return f"{path} 缺少字段: {key}"
        for key, child_schema in schema.get("properties", {}).items():
            if key in value and isinstance(child_schema, dict):
                error = _validate_schema(value[key], child_schema, f"{path}.{key}", root)
                if error:
                    return error
        for clause in schema.get("allOf", []):
            if not isinstance(clause, dict):
                continue
            if_clause = clause.get("if")
            then_clause = clause.get("then")
            else_clause = clause.get("else")
            if if_clause and (then_clause or else_clause):
                match = _evaluate_if_clause(value, if_clause)
                target = then_clause if match else else_clause
                if target:
                    for key in target.get("required", []):
                        if key not in value:
                            return f"{path} 缺少字段: {key}"
                    for key, child_schema in target.get("properties", {}).items():
                        if key in value and isinstance(child_schema, dict):
                            error = _validate_schema(value[key], child_schema, f"{path}.{key}", root)
                            if error:
                                return error
    return None


def _evaluate_if_clause(value: dict[str, Any], clause: dict[str, Any]) -> bool:
    props = clause.get("properties", {})
    for key, cond in props.items():
        if key not in value:
            return False
        if isinstance(cond, dict) and "const" in cond:
            if value[key] != cond["const"]:
                return False
    return True


def validate_task_contract(action: dict[str, Any]) -> tuple[bool, str]:
    try:
        schema = json.loads(ACTION_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"动作 Schema 无法加载: {exc}"
    error = _validate_schema(action, schema)
    if error:
        return False, f"动作 Schema 校验失败: {error}"
    if action["type"] == "run_isolated_agent" and action.get("fork_context") is not False:
        return False, "隔离动作必须使用 fork_context=false"
    if action["type"] == "run_command" and action.get("task_kind") == "material_preparation":
        command = action.get("command")
        if not isinstance(command, dict) or command.get("program") != "python" or not isinstance(command.get("script"), str) or not isinstance(command.get("args"), list) or not command["args"]:
            return False, "材料索引动作必须声明可执行命令"
    return True, "ok"



def active_input_matches(project_root: Path, action: dict[str, Any]) -> bool:
    manifest, error = read_input_manifest(project_root)
    if error or not manifest:
        return False
    task = {"task_id": action.get("task_id", action.get("action_id", "")), "task_kind": action.get("task_kind", ""), "expected_outputs": action.get("expected_outputs", []), "stage": action.get("rule_pack_ref", {}).get("stage", ""), "depends_on": action.get("depends_on", [])}
    return input_hashes(project_root, task, manifest) == action.get("input_hashes")


def _validate_design_writer_upstream(project_root: Path, action: dict[str, Any]) -> tuple[bool, str]:
    if action.get("task_kind") != "design_writer" or action.get("mode") == "simple":
        return True, "ok"
    required = [
        ".workflow/runtime/context/design/baselines/a-baseline.json",
        ".workflow/runtime/context/design/baselines/b-baseline.json",
        ".workflow/runtime/context/design/baselines/c-baseline.json",
        ".workflow/runtime/context/design/baselines/design-brief.json",
    ]
    for raw in required:
        if not output_valid(project_root, raw):
            return False, f"Design 写作上游基线缺失: {raw}"
    return True, "ok"

def accept_outputs(project_root: Path, action: dict[str, Any]) -> tuple[bool, str]:
    for raw in action.get("expected_outputs", []):
        if not output_valid(project_root, raw):
            return False, f"缺少或无效输出: {raw}"
    return _validate_design_writer_upstream(project_root, action)

def handle_accept(project_root: Path, action_id_value: str, result: str, error: str | None, fingerprint: str | None) -> dict[str, Any]:
    state = load_state(project_root)
    completed_node = state.get("nodes", {}).get(action_id_value, {})
    if completed_node.get("status") == "completed":
        manifest, manifest_error = read_input_manifest(project_root)
        if manifest and not manifest_error:
            tasks = task_map(manifest.get("mode") or "full", manifest)
            task = tasks.get(action_id_value)
            if task and task_fresh(project_root, task, manifest, state):
                return {"accepted": True, "idempotent": True, "action_id": action_id_value, "result": "success"}
    preview = preview_next(project_root)
    action = next((x for x in preview.get("ready_actions", []) if x.get("action_id") == action_id_value), None)
    if not action:
        manifest, manifest_error = read_input_manifest(project_root)
        if manifest and not manifest_error:
            tasks = task_map(manifest.get("mode") or "full", manifest)
            task = tasks.get(action_id_value)
            if task and outputs_valid(project_root, task):
                action = make_action(project_root, task, manifest, "输出已存在，补记接受结果")
                action["action_id"] = action_id_value
        if not action:
            return {"accepted": False, "error": "action_id 不属于当前 ready_actions[]"}
    if action.get("type") == "ask_user":
        return {"accepted": False, "error": "ask_user 动作不能通过 handle_accept 接受，请使用用户决策流程"}
    ok, message = validate_task_contract(action)
    if not ok:
        return {"accepted": False, "error": message}
    if not active_input_matches(project_root, action):
        return {"accepted": False, "error": "动作输入哈希已陈旧，请重新获取 ready_actions[]"}
    base_id = action.get("task_id", action_id_value)
    node = state.setdefault("nodes", {}).setdefault(base_id, {"status": "pending", "attempts": 0})
    node["attempts"] = int(node.get("attempts", 0)) + 1
    node["last_input_hashes"] = action.get("input_hashes", {})
    if result == "failure":
        node["status"] = "failed" if node["attempts"] >= action.get("max_attempts", MAX_ACTION_ATTEMPTS) else "pending"
        failure = {"action_id": action_id_value, "error": error or "未提供错误", "fingerprint": fingerprint, "attempt": node["attempts"], "at": now()}
        state.setdefault("failures", []).append(failure)
        save_state(project_root, state)
        return {"accepted": True, "action_id": action_id_value, "result": "failure", "attempt": node["attempts"]}
    output_ok, output_error = accept_outputs(project_root, action)
    if not output_ok:
        return {"accepted": False, "error": output_error}
    node["status"] = "completed"
    node["accepted_output_hashes"] = {raw: file_hash(resolve_rel(project_root, raw)) for raw in action.get("expected_outputs", [])}
    write_json(receipt_path(project_root, base_id), {
        "schema_version": SCHEMA_VERSION,
        "task_id": base_id,
        "action_id": action_id_value,
        "input_hashes": action.get("input_hashes", {}),
        "output_hashes": node["accepted_output_hashes"],
        "accepted_at": now(),
    })
    state.setdefault("events", []).append({"event": "accept_success", "action_id": action_id_value, "task_id": base_id, "at": now()})
    save_state(project_root, state)
    return {"accepted": True, "action_id": action_id_value, "result": "success", "output_hashes": node["accepted_output_hashes"]}


def handle_answer(project_root: Path, question_id: str, answer: str) -> dict[str, Any]:
    if not answer or not answer.strip():
        return {"accepted": False, "error": "答案不能为空"}
    manifest, error = read_input_manifest(project_root)
    if error or not manifest:
        return {"accepted": False, "error": error or "输入不存在"}
    if question_id in ("mode-selection", "select-mode"):
        if answer not in set(SUPPORTED_MODES):
            return {"accepted": False, "error": "模式只能是 simple 或 full"}
        manifest["mode"] = answer
        write_json(runtime_dir(project_root) / "inputs/input-manifest.json", manifest)
        return {"accepted": True, "question_id": question_id, "mode": answer}
    decisions = read_json(runtime_dir(project_root) / "inputs/user-decisions.json") or {"decisions": []}
    question = next((item for item in user_questions(project_root) if item.get("question_id") == question_id), {})
    values = [x for x in decisions.get("decisions", []) if x.get("question_id") != question_id]
    values.append({
        "question_id": question_id,
        "question": question.get("question", ""),
        "answer": answer,
        "answer_hash": f"sha256:{sha256_text(answer)}",
        "invalidates": question.get("invalidates", ["all"]),
        "answered_at": now(),
    })
    write_json(runtime_dir(project_root) / "inputs/user-decisions.json", {"decisions": values})
    return {"accepted": True, "question_id": question_id, "answer_hash": f"sha256:{sha256_text(answer)}"}


def handle_status(project_root: Path) -> dict[str, Any]:
    state = load_state(project_root)
    preview = preview_next(project_root)
    return {"schema_version": SCHEMA_VERSION, "run_id": state["run_id"], "completed": state.get("completed", False), "state": "completed" if state.get("completed") else preview.get("state"), "ready_actions": preview.get("ready_actions", []), "completed_actions": preview.get("completed_actions", []), "blocked_by_user_questions": preview.get("blocked_by_user_questions", []), "model_calls": state.get("model_calls", default_model_calls()), "failures": state.get("failures", [])}


def init_project(project_root: Path, request: str, mode: str | None, materials: list[str]) -> dict[str, Any]:
    root = runtime_dir(project_root) / "inputs"
    root.mkdir(parents=True, exist_ok=True)
    request_path = root / "request.md"
    request_path.write_text(request, encoding="utf-8")
    paths = []
    for item in materials:
        candidate = Path(item) if Path(item).is_absolute() else project_root / item
        paths.append(rel_path(project_root, candidate))
    manifest = {"schema_version": "design-input/v2", "request_path": rel_path(project_root, request_path), "align_path": "output/align/align.md", "material_inputs": paths, "created_at": now()}
    if mode:
        manifest["mode"] = mode
    write_json(root / "input-manifest.json", manifest)
    if not state_path(project_root).exists():
        save_state(project_root, load_state(project_root))
    return {"initialized": True, "schema_version": SCHEMA_VERSION, "input_hash": input_hash(project_root, manifest), "mode": mode}


def main() -> int:
    parser = argparse.ArgumentParser(description="Design v2 确定性编排器")
    parser.add_argument("command", choices=("init", "next", "accept", "answer", "status"))
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--request", default="")
    parser.add_argument("--mode", choices=SUPPORTED_MODES)
    parser.add_argument("--materials", action="append", default=[])
    parser.add_argument("--action-id")
    parser.add_argument("--result", choices=("success", "failure"), default="success")
    parser.add_argument("--error")
    parser.add_argument("--fingerprint")
    parser.add_argument("--question-id")
    parser.add_argument("--answer")
    parser.add_argument("--answer-file", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    try:
        if args.command == "init":
            result = init_project(root, args.request, args.mode, args.materials)
        elif args.command == "next":
            result = next_action(root)
        elif args.command == "accept":
            if not args.action_id:
                raise ValueError("accept 需要 --action-id")
            result = handle_accept(root, args.action_id, args.result, args.error, args.fingerprint)
        elif args.command == "answer":
            if not args.question_id:
                raise ValueError("answer 需要 --question-id")
            answer = args.answer if args.answer is not None else (args.answer_file.read_text(encoding="utf-8") if args.answer_file else None)
            if answer is None:
                raise ValueError("answer 需要 --answer 或 --answer-file")
            result = handle_answer(root, args.question_id, answer)
        else:
            result = handle_status(root)
    except (OSError, ValueError, KeyError) as exc:
        result = {"accepted": False, "state": "failed", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("accepted", True) is not False or args.command in ("next", "status") else 1


if __name__ == "__main__":
    raise SystemExit(main())







