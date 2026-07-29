from __future__ import annotations
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("design_orchestrator", SCRIPT.with_name("design-orchestrator.py"))
orch = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(orch)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_output(root: Path, action: dict[str, Any]) -> list[str]:
    written: list[str] = []
    revision = orch.read_input_manifest(root)[0]
    material_revision = orch.material_revision(root, revision) if revision else "sha256:unknown"
    for raw in action.get("expected_outputs", []):
        path = root / raw
        path.parent.mkdir(parents=True, exist_ok=True)
        if raw.endswith("design.md"):
            write_text(path, """# 产品方案 Design\n\n## 一、方案摘要\n\n完成核心业务闭环。\n\n## 二、用户、场景与目标\n\n覆盖主要用户的主路径和异常恢复。\n\n## 七、页面、区块与字段设计\n\n### 页面：业务处理\n\n- 页面目的：完成业务处理\n- 适用角色：业务人员\n- 进入条件：用户已登录\n- 数据范围：本人负责范围\n- 主要状态：无特殊规则\n\n#### 区块：基本信息\n\n- 区块目的：展示和填写业务信息\n\n##### 字段：业务名称\n\n- 业务含义：业务对象名称\n- 字段来源：用户输入\n- 展示条件：始终展示\n- 输入与编辑：可输入和编辑\n- 取值与默认：默认空值\n- 交互方式：文本输入\n- 校验与反馈：不能为空，错误时提示\n\n##### 操作：提交\n\n- 适用角色：业务人员\n- 展示与可用条件：信息完整时可用\n- 二次确认：无需确认\n- 成功结果：提交成功并进入处理状态\n- 数据与状态变化：状态变为处理中\n- 失败与恢复：保留输入并提示重试\n- 后续去向：进入处理结果页\n\n## 九、成功与验收\n\n主路径、异常和权限均可验证。\n""")
        elif raw.endswith("decision-notes.md"):
            write_text(path, "# 决策记录\n\n## 设计决策\n- 选择最小闭环。\n\n## 偏离\n- 无。\n\n## 权衡\n- 无。\n\n## 待确认\n- 无。\n")
        elif raw.endswith(".json"):
            value: dict[str, Any] = {"schema_version": "design-analysis/v2", "task_id": action.get("task_id"), "input_fingerprint": action.get("input_hashes", {}).get("__input_hash__"), "status": "completed", "conclusions": [], "conflicts": [], "questions": [], "coverage": [action.get("task_id")], "source_refs": [], "payload": {}}
            if action.get("task_kind") == "material_preparation":
                manifest = orch.read_input_manifest(root)[0] or {}
                sources = [{"source_id": orch.source_id_for(item), "path": item} for item in manifest.get("material_inputs", [])]
                value = {"schema_version": "material-manifest/v2", "material_revision": material_revision, "sources": sources}
                orch.write_json(path, value)
                written.append(raw)
                if raw.endswith("manifest.json"):
                    orch.write_json(root / ".workflow/runtime/materials/source-index.json", {"schema_version": "source-index/v2", "material_revision": material_revision, "files": sources})
                    written.append(".workflow/runtime/materials/source-index.json")
                continue
            if action.get("task_kind") == "material_fact_extraction":
                item = action.get("input_files", [""])[0]
                value = {"schema_version": "material-fact/v2", "source_path": item, "source_hash": orch.safe_file_hash(root, item), "material_revision": material_revision, "facts": [{"id": f"fact-{orch.source_id_for(item)}", "fact": "合成事实", "source_refs": [orch.source_id_for(item)]}]}
            elif action.get("task_kind") == "material_merge":
                facts = []
                for item in (orch.read_input_manifest(root)[0] or {}).get("material_inputs", []):
                    part = orch.read_json(orch.material_dir(root) / "facts" / f"{orch.source_id_for(item)}.json") or {}
                    facts.extend(part.get("facts", []))
                value = {"schema_version": "facts/v2", "material_revision": material_revision, "sources": (orch.read_input_manifest(root)[0] or {}).get("material_inputs", []), "facts": facts, "conflicts": [], "missing_high_impact": [], "not_applicable": [], "tradeoffs": []}
            elif action.get("task_kind") == "generated_check":
                value = {"schema_version": "design-check/v2", "status": "passed", "findings": [], "input_fingerprint": action.get("input_hashes", {}).get("__input_hash__")}
            elif action.get("task_kind") == "compile_index":
                cmd = [sys.executable, str(SCRIPT.with_name("design-index.py")), "compile", "--project-root", str(root)]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
                if result.returncode != 0:
                    raise RuntimeError(result.stdout + result.stderr)
                continue
            orch.write_json(path, value)
        else:
            write_text(path, "generated")
        written.append(raw)
    return written


def parse_budgets(values: list[str]) -> dict[str, int]:
    result = {}
    for value in values:
        if "=" in value:
            key, count = value.split("=", 1)
            result[key] = int(count)
    return result


def run(args: argparse.Namespace) -> int:
    root = args.project_root.resolve()
    budgets = parse_budgets(args.fail_on)
    used: dict[str, int] = {}
    answers = {}
    for item in args.answer:
        if "=" in item:
            key, value = item.split("=", 1)
            answers[key] = value
    steps = 0
    trace_path = root / ".workflow/runtime/context/design/host-execution-log.jsonl"
    while steps < args.max_steps:
        steps += 1
        preview = orch.next_action(root)
        if preview.get("state") == "waiting_user":
            actions = preview.get("ready_actions", [])
            if not actions:
                return 2
            unresolved = []
            for action in actions:
                question_id = action.get("question", {}).get("question_id") or action.get("action_id", "").split(":", 1)[-1]
                if question_id in answers:
                    orch.handle_answer(root, question_id, answers[question_id])
                elif action.get("action_id") == "select-mode":
                    orch.handle_answer(root, "mode-selection", args.mode_answer)
                else:
                    unresolved.append(question_id)
            if unresolved:
                return 2
            continue
        if preview.get("state") == "completed":
            return 0
        if preview.get("state") != "ready":
            return 1
        actions = list(preview.get("ready_actions", []))
        ready_batch = [action.get("task_id", action.get("action_id")) for action in actions]
        process_actions = list(reversed(actions)) if args.reverse else actions
        for action in process_actions:
            task_id = action.get("task_id", action.get("action_id"))
            program_declared = {
                "action_id": action.get("action_id"),
                "task_id": task_id,
                "input_files": action.get("input_files", []),
                "allowed_evidence_ranges": action.get("allowed_evidence_ranges", []),
                "fork_context": action.get("fork_context"),
                "expected_outputs": action.get("expected_outputs", []),
            }
            stage_count = used.get(task_id, 0)
            if stage_count < budgets.get(task_id, 0):
                used[task_id] = stage_count + 1
                fingerprint = f"sha256:failure-{task_id}"
                accepted = orch.handle_accept(root, action["action_id"], "failure", "模拟失败", fingerprint)
                if not accepted.get("accepted"):
                    return 1
                event = {
                    "ready_batch": ready_batch,
                    "program_declared": program_declared,
                    "host_execution": {
                        "isolation_status": "simulated_only",
                        "program_reads": action.get("input_files", []),
                        "declared_agent_reads": action.get("input_files", []),
                        "actual_agent_reads": [],
                        "written_files": [],
                    },
                    "result": "failure",
                    "error": "模拟失败",
                }
                with trace_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
                continue
            if args.interrupt_after and args.interrupt_after == task_id:
                return 75
            written = write_output(root, action)
            event = {
                "ready_batch": ready_batch,
                "program_declared": program_declared,
                "host_execution": {
                    "isolation_status": "simulated_only",
                    "program_reads": action.get("input_files", []),
                    "declared_agent_reads": action.get("input_files", []),
                    "actual_agent_reads": [],
                    "written_files": written,
                },
                "result": "success",
            }
            with trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            accepted = orch.handle_accept(root, action["action_id"], "success", None, None)
            if not accepted.get("accepted"):
                return 1
    return 75


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--fail-on", action="append", default=[])
    parser.add_argument("--interrupt-after")
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--answer", action="append", default=[])
    parser.add_argument("--mode-answer", choices=("simple", "full"), default="full")
    args = parser.parse_args()
    try:
        return run(args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
