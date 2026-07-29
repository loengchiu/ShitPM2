from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ORCH_PATH = ROOT / "scripts/python/design-orchestrator.py"
HOST_PATH = ROOT / "scripts/python/fake-design-host.py"
FIXTURE = ROOT / "test-fixture/design-orchestration/synthetic-full"
spec = importlib.util.spec_from_file_location("design_orchestrator", ORCH_PATH)
orch = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(orch)

TOTAL = 0
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_trace(root: Path) -> list[dict[str, Any]]:
    path = root / ".workflow/runtime/context/design/host-execution-log.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_host(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SHITPM_BUNDLE_ROOT"] = str(root / "bundle")
    return subprocess.run(
        [sys.executable, str(HOST_PATH), "--project-root", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def current_status(root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["SHITPM_BUNDLE_ROOT"] = str(root / "bundle")
    result = subprocess.run(
        [sys.executable, str(ORCH_PATH), "status", "--project-root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return json.loads(result.stdout)


def seed_materials(root: Path) -> None:
    manifest, error = orch.read_input_manifest(root)
    check(manifest is not None, error or "输入清单不存在")
    revision = orch.material_revision(root, manifest)
    sources = [{"source_id": orch.source_id_for(item), "path": item} for item in manifest["material_inputs"]]
    orch.write_json(orch.material_dir(root) / "manifest.json", {"material_revision": revision, "sources": sources})
    orch.write_json(orch.material_dir(root) / "source-index.json", {"material_revision": revision, "files": sources})
    for item in manifest["material_inputs"]:
        sid = orch.source_id_for(item)
        orch.write_json(
            orch.material_dir(root) / "facts" / f"{sid}.json",
            {
                "schema_version": "material-fact/v2",
                "source_path": item,
                "source_hash": orch.safe_file_hash(root, item),
                "material_revision": revision,
                "facts": [],
            },
        )
    orch.write_json(orch.material_dir(root) / "facts.json", {"material_revision": revision, "sources": sources, "facts": [], "conflicts": []})
    tasks = orch.task_map(manifest["mode"], manifest)
    for task_id in ("material-index", *[x for x in tasks if x.startswith("material-facts:")], "material-merge"):
        task = tasks[task_id]
        hashes = orch.input_hashes(root, task, manifest)
        outputs = {raw: orch.file_hash(orch.resolve_rel(root, raw)) for raw in task["expected_outputs"]}
        orch.write_json(orch.receipt_path(root, task_id), {"schema_version": orch.SCHEMA_VERSION, "task_id": task_id, "action_id": task_id, "input_hashes": hashes, "output_hashes": outputs, "accepted_at": orch.now()})


def make_project(mode: str, seed: bool = True) -> tuple[tempfile.TemporaryDirectory, Path]:
    holder = tempfile.TemporaryDirectory(prefix="spm-design-replay-")
    root = Path(holder.name)
    shutil.copytree(FIXTURE / "materials", root / "materials")
    materials = [str(path) for path in sorted((root / "materials").glob("*.md"))]
    orch.BUNDLE_ROOT = root / "bundle"
    orch.init_project(root, "生成设备借还 Design", mode, materials)
    if seed:
        seed_materials(root)
    return holder, root


def test_simple_action_trace() -> None:
    holder, root = make_project("simple")
    try:
        result = run_host(root, "--max-steps", "100")
        check(result.returncode == 0, result.stdout + result.stderr)
        trace = read_trace(root)
        ids = [event["program_declared"]["task_id"] for event in trace]
        check(ids == ["simple-design", "simple-generated-check", "compile-design-index", "report-completed"], f"简单模式轨迹不符合预期: {ids}")
        check(current_status(root)["model_calls"]["total"] == 0, "简单模式零模型测试不得调用模型")
        check(all(event["host_execution"]["isolation_status"] == "simulated_only" for event in trace), "伪造宿主必须明确仅为模拟")
    finally:
        holder.cleanup()


def test_full_ready_batches() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        trace = read_trace(root)
        check(trace, "完整模式必须有回放轨迹")
        executed = {event["program_declared"]["task_id"] for event in trace}
        for expected in ("a2-stakeholders", "a2-goals-success", "b1-business-process", "b1-use-cases", "c1-system-functions", "c1-permissions", "c1-integrations", "c1-product-nfr"):
            check(expected in executed, f"缺少完整模式动作: {expected}")
        batches = {tuple(event["ready_batch"]) for event in trace}
        check(any({"a2-stakeholders", "a2-goals-success"}.issubset(set(batch)) for batch in batches), "A2 无依赖专项未在同一 ready_actions 批次")
        check(any({"b1-business-process", "b1-use-cases"}.issubset(set(batch)) for batch in batches), "B1 无依赖专项未在同一 ready_actions 批次")
        check(not any("independent_final_review" in event["program_declared"]["task_id"] for event in trace), "不得出现独立第四次成品审查")
        check(current_status(root)["model_calls"]["total"] == 0, "完整模式零模型测试不得调用模型")
    finally:
        holder.cleanup()


def test_same_batch_reverse_order() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--reverse", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        trace = read_trace(root)
        a2 = [event for event in trace if set(event["ready_batch"]) >= {"a2-stakeholders", "a2-goals-success"}]
        check(a2, "未记录 A2 同批 ready_actions")
        first_a2 = [event["program_declared"]["task_id"] for event in a2[:2]]
        check(first_a2 == ["a2-goals-success", "a2-stakeholders"], f"乱序回放未按反向顺序执行: {first_a2}")
    finally:
        holder.cleanup()


def test_failure_recovery_current_node_only() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--fail-on", "a2-stakeholders=1", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        trace = read_trace(root)
        stakeholder_events = [event for event in trace if event["program_declared"]["task_id"] == "a2-stakeholders"]
        check([event["result"] for event in stakeholder_events] == ["failure", "success"], "失败节点应只在当前节点重试")
        a1_events = [event for event in trace if event["program_declared"]["task_id"] == "a1-requirement-clarification"]
        check(len(a1_events) == 1, "当前节点失败恢复不得重跑已完成上游")
        check(len(current_status(root)["failures"]) == 1, "失败必须进入状态记录")
    finally:
        holder.cleanup()


def test_interruption_recovery() -> None:
    holder, root = make_project("full")
    try:
        first = run_host(root, "--interrupt-after", "a2-stakeholders", "--max-steps", "200")
        check(first.returncode == 75, "中断注入必须返回中断码")
        preview = orch.next_action(root)
        ready_ids = {action["task_id"] for action in preview.get("ready_actions", [])}
        check("a2-stakeholders" in ready_ids, "中断后当前动作必须保持 ready")
        second = run_host(root, "--max-steps", "200")
        check(second.returncode == 0, second.stdout + second.stderr)
        trace = read_trace(root)
        a1_events = [event for event in trace if event["program_declared"]["task_id"] == "a1-requirement-clarification"]
        check(len(a1_events) == 1, "中断恢复不得重复执行已完成节点")
    finally:
        holder.cleanup()


def test_material_local_invalidation() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        source = root / "materials/02-roles-and-scope.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n变化", encoding="utf-8")
        first = orch.next_action(root)
        check([x["task_id"] for x in first["ready_actions"]] == ["material-index"], "材料变化必须先重建材料索引")
        one = run_host(root, "--max-steps", "1")
        check(one.returncode == 75, "只执行一步应停在未完成状态")
        second = orch.next_action(root)
        ids = [x["task_id"] for x in second["ready_actions"]]
        check(ids == ["material-facts:02-roles-and-scope"], f"材料变化必须只失效变化来源: {ids}")
    finally:
        holder.cleanup()


def test_state_file_recovery_from_receipts() -> None:
    holder, root = make_project("simple")
    try:
        result = run_host(root, "--max-steps", "100")
        check(result.returncode == 0, result.stdout + result.stderr)
        orch.state_path(root).unlink()
        recovered = orch.next_action(root)
        check(recovered["state"] == "completed", "状态文件丢失后应依据收据和输出哈希恢复")
        check(current_status(root)["model_calls"]["total"] == 0, "状态恢复不得调用模型")
    finally:
        holder.cleanup()


def test_legacy_state_requires_migration() -> None:
    holder, root = make_project("simple")
    try:
        orch.write_json(orch.runtime_dir(root) / "run.json", {"schema_version": "design-orchestration/v1"})
        result = orch.next_action(root)
        check(result["state"] == "migration_required", "旧版运行不得静默迁移")
    finally:
        holder.cleanup()


def task_events(root: Path, task_id: str) -> list[dict[str, Any]]:
    return [event for event in read_trace(root) if event["program_declared"]["task_id"] == task_id]


def test_c1_same_batch_single_failure() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--fail-on", "c1-permissions=1", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        check([event["result"] for event in task_events(root, "c1-permissions")] == ["failure", "success"], "C1 单节点失败必须只重试失败节点")
        for task_id in ("c1-system-functions", "c1-integrations", "c1-product-nfr"):
            check(len(task_events(root, task_id)) == 1, f"C1 同批其他节点不得重跑: {task_id}")
        check(len(task_events(root, "b6-model-review")) == 1, "C1 失败不得重跑已完成上游")
    finally:
        holder.cleanup()


def test_design_editor_failure_retries_writer_only() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--fail-on", "design-editor=1", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        check([event["result"] for event in task_events(root, "design-editor")] == ["failure", "success"], "设计总编失败必须只重试设计总编")
        for task_id in ("a5-merge-review", "b6-model-review", "c4-cross-layer-review"):
            check(len(task_events(root, task_id)) == 1, f"设计总编失败不得重跑上游: {task_id}")
    finally:
        holder.cleanup()


def test_single_review_failure_does_not_rerun_other_reviews() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--fail-on", "review-park-coverage=1", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        check([event["result"] for event in task_events(root, "review-park-coverage")] == ["failure", "success"], "单个成品检查失败必须只重试当前检查")
        for task_id in ("review-pm-readability", "review-downstream-sufficiency"):
            check(len(task_events(root, task_id)) == 1, f"其他成品检查不得重跑: {task_id}")
        check(len(task_events(root, "design-editor")) == 1, "成品检查失败不得重跑设计总编")
    finally:
        holder.cleanup()


def test_index_failure_does_not_call_writer_or_checks_again() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--fail-on", "compile-design-index=1", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        check([event["result"] for event in task_events(root, "compile-design-index")] == ["failure", "success"], "索引编译失败必须只重试索引编译")
        check(len(task_events(root, "design-editor")) == 1, "索引编译失败不得重跑设计总编")
        for task_id in ("review-pm-readability", "review-park-coverage", "review-downstream-sufficiency"):
            check(len(task_events(root, task_id)) == 1, f"索引编译失败不得重跑成品检查: {task_id}")
        check(current_status(root)["model_calls"]["total"] == 0, "索引编译失败回放不得调用模型")
    finally:
        holder.cleanup()


def test_b2_batch_interruption_recovery() -> None:
    holder, root = make_project("full")
    try:
        first = run_host(root, "--interrupt-after", "b2-business-objects", "--max-steps", "200")
        check(first.returncode == 75, "B2 中断注入必须返回中断码")
        ready_ids = {action["task_id"] for action in orch.next_action(root).get("ready_actions", [])}
        check({"b2-business-objects", "b2-business-rules", "b2-exceptions-boundaries"}.issubset(ready_ids), f"B2 中断后未保留未完成动作: {ready_ids}")
        second = run_host(root, "--max-steps", "200")
        check(second.returncode == 0, second.stdout + second.stderr)
        check(len(task_events(root, "b2-data-flow")) == 1, "B2 中断恢复不得重复执行已完成节点")
        for task_id in ("b2-business-objects", "b2-business-rules", "b2-exceptions-boundaries"):
            check(len(task_events(root, task_id)) == 1, f"B2 中断恢复必须执行未完成节点: {task_id}")
    finally:
        holder.cleanup()


def test_design_editor_interruption_recovery() -> None:
    holder, root = make_project("full")
    try:
        first = run_host(root, "--interrupt-after", "design-editor", "--max-steps", "200")
        check(first.returncode == 75, "设计总编后中断注入必须返回中断码")
        ready_ids = {action["task_id"] for action in orch.next_action(root).get("ready_actions", [])}
        check(ready_ids == {"design-editor"}, f"设计总编后中断应只保留设计总编: {ready_ids}")
        second = run_host(root, "--max-steps", "200")
        check(second.returncode == 0, second.stdout + second.stderr)
        check(len(task_events(root, "design-editor")) == 1, "中断前未产生有效输出时，设计总编应安全重试一次")
        check(len(task_events(root, "c4-cross-layer-review")) == 1, "设计总编后中断不得重跑跨层检查")
    finally:
        holder.cleanup()


def test_user_decision_local_invalidation() -> None:
    holder, root = make_project("full")
    try:
        orch.write_json(
            orch.runtime_dir(root) / "conflicts/user-questions.json",
            {"questions": [{"question_id": "permission-scope", "question": "权限范围如何确定？", "blocking": True, "invalidates": ["c1-permissions"]}]},
        )
        result = run_host(root, "--answer", "permission-scope=仅本部门", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        baseline = {task_id: len(task_events(root, task_id)) for task_id in ("a1-requirement-clarification", "c1-system-functions", "c1-permissions", "c3-acceptance")}
        orch.handle_answer(root, "permission-scope", "全公司")
        preview = orch.next_action(root)
        check([action["task_id"] for action in preview.get("ready_actions", [])] == ["c1-permissions"], f"用户决策变化应只让受影响节点 ready: {preview.get('ready_actions')}")
        result = run_host(root, "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        check(len(task_events(root, "a1-requirement-clarification")) == baseline["a1-requirement-clarification"], "不相关的 A 节点不得重跑")
        check(len(task_events(root, "c1-system-functions")) == baseline["c1-system-functions"], "不相关的 C1 节点不得重跑")
        check(len(task_events(root, "c1-permissions")) == baseline["c1-permissions"] + 1, "受影响的权限节点必须重跑")
        check(len(task_events(root, "c3-acceptance")) == baseline["c3-acceptance"] + 1, "受影响节点的下游必须重跑")
    finally:
        holder.cleanup()


def test_stale_action_and_tampered_output_rejected() -> None:
    holder, root = make_project("simple")
    try:
        action = orch.next_action(root)["ready_actions"][0]
        source = root / "materials/02-roles-and-scope.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n陈旧输入", encoding="utf-8")
        rejected = orch.handle_accept(root, action["action_id"], "failure", "陈旧动作", "sha256:stale")
        check(not rejected.get("accepted"), "输入哈希陈旧的动作必须拒绝")
        result = run_host(root, "--max-steps", "100")
        check(result.returncode == 0, result.stdout + result.stderr)
        design = root / "output/design/design.md"
        design.write_text(design.read_text(encoding="utf-8") + "\n篡改", encoding="utf-8")
        preview = orch.next_action(root)
        check([action["task_id"] for action in preview.get("ready_actions", [])] == ["simple-design"], "篡改后的 Design 输出不得被误认有效")
    finally:
        holder.cleanup()


def main() -> int:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for test in tests:
        global TOTAL
        TOTAL += 1
        try:
            test()
        except Exception as exc:
            FAILURES.append(f"{test.__name__}: {exc}")
    if FAILURES:
        print(f"Design 编排回放测试失败：{len(FAILURES)}/{TOTAL}")
        for item in FAILURES:
            print(f"- {item}")
        return 1
    print(f"Design 编排回放测试通过：{TOTAL} 个用例，模型调用 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
