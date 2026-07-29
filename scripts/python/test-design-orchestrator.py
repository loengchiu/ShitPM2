from __future__ import annotations
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCH_PATH = ROOT / "scripts/python/design-orchestrator.py"
HOST_PATH = ROOT / "scripts/python/fake-design-host.py"
FIXTURE = ROOT / "test-fixture/design-orchestration/synthetic-full"
spec = importlib.util.spec_from_file_location("design_orchestrator", ORCH_PATH)
orch = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(orch)


def check(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def project(mode: str = "full", seed: bool = True) -> tuple[tempfile.TemporaryDirectory, Path]:
    holder = tempfile.TemporaryDirectory(prefix="spm-design-v2-")
    root = Path(holder.name)
    shutil.copytree(FIXTURE / "materials", root / "materials")
    paths = [str(path) for path in sorted((root / "materials").glob("*.md"))]
    orch.BUNDLE_ROOT = root / "bundle"
    orch.init_project(root, "生成设备借还 Design", mode, paths)
    if seed:
        manifest, error = orch.read_input_manifest(root)
        assert manifest, error
        revision = orch.material_revision(root, manifest)
        sources = [{"source_id": orch.source_id_for(item), "path": item} for item in manifest["material_inputs"]]
        orch.write_json(orch.material_dir(root) / "manifest.json", {"material_revision": revision, "sources": sources})
        orch.write_json(orch.material_dir(root) / "source-index.json", {"material_revision": revision, "files": sources})
        for item in manifest["material_inputs"]:
            orch.write_json(orch.material_dir(root) / "facts" / f"{orch.source_id_for(item)}.json", {"source_path": item, "source_hash": orch.safe_file_hash(root, item), "material_revision": revision, "facts": []})
        orch.write_json(orch.material_dir(root) / "facts.json", {"material_revision": revision, "sources": sources, "facts": [], "conflicts": []})
        tasks = orch.task_map(mode, manifest)
        for task_id in ("material-index", *[x for x in tasks if x.startswith("material-facts:")], "material-merge"):
            task = tasks[task_id]
            orch.write_json(orch.receipt_path(root, task_id), {
                "schema_version": orch.SCHEMA_VERSION,
                "task_id": task_id,
                "action_id": task_id,
                "input_hashes": orch.input_hashes(root, task, manifest),
                "output_hashes": {raw: orch.file_hash(orch.resolve_rel(root, raw)) for raw in task["expected_outputs"]},
                "accepted_at": orch.now(),
            })
    return holder, root


def host(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SHITPM_BUNDLE_ROOT"] = str(root / "bundle")
    return subprocess.run([sys.executable, str(HOST_PATH), "--project-root", str(root), *args], text=True, capture_output=True, encoding="utf-8", env=env)


def test_mode_selection_once() -> None:
    holder, root = project(mode="simple", seed=True)
    try:
        manifest_path = root / ".workflow/runtime/context/design/inputs/input-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")); manifest.pop("mode")
        orch.write_json(manifest_path, manifest)
        preview = orch.next_action(root)
        check(preview["state"] == "waiting_user", "未指定模式必须等待用户")
        check([x["action_id"] for x in preview["ready_actions"]] == ["select-mode"], "模式问题只能出现一次")
        orch.handle_answer(root, "mode-selection", "simple")
        check(orch.read_input_manifest(root)[0]["mode"] == "simple", "模式回答未写回")
    finally:
        holder.cleanup()


def test_simple_path_and_contract() -> None:
    holder, root = project("simple", True)
    try:
        preview = orch.next_action(root)
        check(preview["state"] == "ready", "简单模式应就绪")
        check("action" not in preview, "编排器不得再提供单动作兼容字段")
        check(preview["ready_actions"][0]["action_id"] == "simple-design", "缓存命中后简单模式首动作必须是 simple-design")
        action = preview["ready_actions"][0]
        for key in ("depends_on", "batch_key", "input_files", "input_hashes", "forbidden_inputs", "allowed_evidence_ranges"):
            check(key in action, f"动作缺少 {key}")
        check(action["fork_context"] is False, "简单模式写作也必须是新上下文动作")
    finally:
        holder.cleanup()


def test_full_ready_batches() -> None:
    holder, root = project("full", True)
    try:
        result = host(root, "--answer", "overdue-reapply=允许再次申请", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        events = [json.loads(line) for line in (root / ".workflow/runtime/context/design/host-execution-log.jsonl").read_text(encoding="utf-8").splitlines()]
        by_batch = {}
        for event in events:
            task_id = event.get("program_declared", {}).get("task_id", "")
            by_batch.setdefault(task_id.split("-", 1)[0], []).append(task_id)
        executed = {event.get("program_declared", {}).get("task_id") for event in events}
        check({"a2-stakeholders", "a2-goals-success"}.issubset(executed), "A2 并行动作未执行")
        check({"b1-business-process", "b1-use-cases"}.issubset(executed), "B1 并行动作未执行")
        check({"c1-system-functions", "c1-permissions", "c1-integrations", "c1-product-nfr"}.issubset(executed), "C1 并行动作未执行")
        check(not any("independent" in str(event) for event in events), "不应出现独立第四次审查")
    finally:
        holder.cleanup()


def test_failure_and_material_invalidation() -> None:
    holder, root = project("full", True)
    try:
        result = host(root, "--fail-on", "a2-stakeholders=1", "--answer", "overdue-reapply=允许再次申请", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        state = orch.load_state(root)
        check(len(state["failures"]) == 1, "失败应写入状态")
        source = root / "materials/01-background.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n变化", encoding="utf-8")
        next_result = orch.next_action(root)
        ids = {x["action_id"] for x in next_result.get("ready_actions", [])}
        check("material-index" in ids, "材料变化必须先失效材料索引")
    finally:
        holder.cleanup()


def test_action_schema_is_loaded() -> None:
    holder, root = project("simple", True)
    try:
        action = orch.next_action(root)["ready_actions"][0]
        invalid = dict(action)
        invalid["depends_on"] = list(action.get("depends_on", [])) + list(action.get("depends_on", []))
        ok, message = orch.validate_task_contract(invalid)
        check(not ok and "Schema" in message, "动作校验必须加载 JSON Schema 并拒绝重复依赖")
    finally:
        holder.cleanup()


def test_v2_handoff_gate() -> None:
    holder, root = project("full", True)
    try:
        action = {
            "task_id": "b6-model-review",
            "task_kind": "baseline",
            "expected_outputs": [
                ".workflow/runtime/context/design/baselines/b-baseline.json",
                ".workflow/runtime/context/design/conflicts/business-conflicts.json",
            ],
        }
        ok, message = orch.accept_outputs(root, action)
        check(not ok, "缺少 v2 交接文件时必须被拒绝")
        for raw in action["expected_outputs"]:
            orch.write_json(root / raw, {"schema_version": "design-analysis/v2"})
        ok, message = orch.accept_outputs(root, action)
        check(not ok and "交接门禁" in message, "损坏的 v2 交接文件必须被门禁拒绝")
        for raw in action["expected_outputs"]:
            orch.write_json(root / raw, {
                "schema_version": "design-analysis/v2", "task_id": action["task_id"],
                "status": "completed", "coverage": [], "source_refs": [],
            })
        ok, message = orch.accept_outputs(root, action)
        check(ok, message)

        a_action = {
            "task_id": "a5-merge-review",
            "task_kind": "baseline",
            "expected_outputs": [
                ".workflow/runtime/context/design/baselines/a-baseline.json",
            ],
        }
        orch.write_json(root / a_action["expected_outputs"][0], {"schema_version": "design-analysis/v2"})
        ok, message = orch.accept_outputs(root, a_action)
        check(not ok and "交接门禁" in message, "A 层基线必须经过 v2 交接门禁")
        orch.write_json(root / a_action["expected_outputs"][0], {
            "schema_version": "design-analysis/v2", "task_id": a_action["task_id"],
            "status": "completed", "coverage": [], "source_refs": [],
        })
        ok, message = orch.accept_outputs(root, a_action)
        check(ok, message)
    finally:
        holder.cleanup()


def test_legacy_run_rejected() -> None:
    holder, root = project("simple", True)
    try:
        orch.write_json(orch.runtime_dir(root) / "run.json", {"schema_version": "design-orchestration/v1"})
        result = orch.next_action(root)
        check(result["state"] == "migration_required", "旧 v1 运行不得静默迁移")
    finally:
        holder.cleanup()


def main() -> int:
    tests = [test_mode_selection_once, test_simple_path_and_contract, test_full_ready_batches, test_failure_and_material_invalidation, test_action_schema_is_loaded, test_v2_handoff_gate, test_legacy_run_rejected]
    failures = []
    for test in tests:
        try:
            test()
        except Exception as exc:
            failures.append(f"{test.__name__}: {exc}")
    if failures:
        print(f"Design v2 编排器测试失败：{len(failures)}/{len(tests)}")
        print("\n".join(f"- {item}" for item in failures))
        return 1
    print(f"Design v2 编排器测试通过：{len(tests)} 个用例，模型调用 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
