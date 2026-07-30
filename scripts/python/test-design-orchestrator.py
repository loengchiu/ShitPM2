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


def project(mode: str = "full", seed: bool = False) -> tuple[tempfile.TemporaryDirectory, Path]:
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
            orch.write_json(
                orch.material_dir(root) / "facts" / f"{orch.source_id_for(item)}.json",
                {"source_path": item, "source_hash": orch.safe_file_hash(root, item), "material_revision": revision, "facts": []},
            )
        orch.write_json(
            orch.material_dir(root) / "facts.json",
            {"version": 1, "material_revision": revision, "confirmed_facts": [], "source_conflicts": [], "missing_information": [], "non_derivable_items": []},
        )
        tasks = orch.task_map(mode, manifest)
        for task_id in ("material-index", *[x for x in tasks if x.startswith("material-facts:")], "material-merge"):
            task = tasks[task_id]
            orch.write_json(
                orch.receipt_path(root, task_id),
                {
                    "schema_version": orch.SCHEMA_VERSION,
                    "task_id": task_id,
                    "action_id": task_id,
                    "input_hashes": orch.input_hashes(root, task, manifest),
                    "output_hashes": {raw: orch.file_hash(orch.resolve_rel(root, raw)) for raw in task["expected_outputs"]},
                    "accepted_at": orch.now(),
                },
            )
    return holder, root


def host(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SHITPM_BUNDLE_ROOT"] = str(root / "bundle")
    return subprocess.run(
        [sys.executable, str(HOST_PATH), "--project-root", str(root), *args],
        text=True,
        capture_output=True,
        encoding="utf-8",
        env=env,
    )


def trace(root: Path) -> list[dict]:
    path = root / ".workflow/runtime/context/design/host-execution-log.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_supported_modes_and_selection() -> None:
    check(orch.SUPPORTED_MODES == ("simple", "full"), "只允许 simple、full")
    holder, root = project("simple", True)
    try:
        manifest_path = root / ".workflow/runtime/context/design/inputs/input-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.pop("mode")
        orch.write_json(manifest_path, manifest)
        preview = orch.next_action(root)
        check(preview["state"] == "waiting_user", "未指定模式必须等待用户")
        check([x["action_id"] for x in preview["ready_actions"]] == ["select-mode"], "模式问题只能出现一次")
        check(orch.handle_answer(root, "mode-selection", "simple")["accepted"], "简单模式选择应被接受")
        check(orch.read_input_manifest(root)[0]["mode"] == "simple", "模式回答未写回")

        bad = dict(manifest)
        bad["mode"] = "full" + "-layered"
        orch.write_json(manifest_path, bad)
        _, error = orch.read_input_manifest(root)
        check(error and "simple、full" in error, "废弃模式必须被拒绝")
    finally:
        holder.cleanup()


def test_simple_graph_and_completion() -> None:
    holder, root = project("simple", False)
    try:
        result = host(root, "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        ids = [event["program_declared"]["task_id"] for event in trace(root)]
        check(ids[-1] == "simple-design", "简单模式必须停在 simple-design")
        check(ids[:1] == ["align"], "Design 必须先完成 Align")
        check(ids.index("align") < ids.index("material-index"), "Align 必须先于材料索引")
        check(any(task.startswith("material-facts:") for task in ids), "必须执行分来源事实提取")
        check("material-merge" in ids, "必须执行材料合并")
        check(not any("review" in task or "check" in task or "compile" in task or "report" in task for task in ids), "不得生成生成后检查、索引或完成回执动作")
        status = orch.handle_status(root)
        check(status["state"] == "completed", "所有任务完成后必须直接 completed")
    finally:
        holder.cleanup()


def empty_project(mode: str = "simple") -> tuple[tempfile.TemporaryDirectory, Path]:
    holder = tempfile.TemporaryDirectory(prefix="spm-design-empty-")
    root = Path(holder.name)
    orch.BUNDLE_ROOT = root / "bundle"
    orch.init_project(root, "没有原始材料时也要形成需求事实并生成 Design", mode, [])
    return holder, root


def test_no_materials_path() -> None:
    holder, root = empty_project("simple")
    try:
        result = host(root, "--max-steps", "100")
        check(result.returncode == 0, result.stdout + result.stderr)
        ids = [event["program_declared"]["task_id"] for event in trace(root)]
        check(ids == ["align", "material-index", "material-merge", "simple-design"], f"无材料路径顺序错误：{ids}")
        check(not any(task.startswith("material-facts:") for task in ids), "无材料路径不应伪造材料事实提取")
        check((root / "output/design/design.md").is_file(), "无材料路径仍应生成 Design")
        check(orch.handle_status(root)["state"] == "completed", "无材料路径必须 completed")
    finally:
        holder.cleanup()


def test_align_question_pause_and_answer_resume() -> None:
    holder, root = project("full", False)
    try:
        interrupted = host(root, "--interrupt-after", "material-index", "--max-steps", "20")
        check(interrupted.returncode == 75, "应在 Align 完成后暂停到材料准备前")
        orch.write_json(
            orch.runtime_dir(root) / "conflicts/user-questions.json",
            {
                "questions": [{
                    "question_id": "data-scope",
                    "question": "数据范围是仅本人负责范围，还是组织范围？",
                    "blocking": True,
                    "invalidates": ["align", "analysis", "writing"],
                }]
            },
        )
        waiting = orch.next_action(root)
        check(waiting["state"] == "waiting_user", "Align 高影响问题必须暂停下游")
        check(waiting["ready_actions"][0]["action_id"] == "question:data-scope", "暂停时应返回高影响问题")
        answered = orch.handle_answer(root, "data-scope", "仅本人负责范围")
        check(answered["accepted"], "用户回答必须被接受")
        decisions = orch.read_json(orch.runtime_dir(root) / "inputs/user-decisions.json")
        check(decisions and decisions["decisions"][0]["answer"] == "仅本人负责范围", "用户回答未写回")
        resumed = orch.next_action(root)
        check(resumed["state"] == "ready" and resumed["ready_actions"][0]["task_id"] == "align", "回答后应重新就绪 Align 并继续下游")
        completed = host(root, "--max-steps", "200")
        check(completed.returncode == 0, completed.stdout + completed.stderr)
        ids = [event["program_declared"]["task_id"] for event in trace(root)]
        check(ids.count("align") == 2 and ids[-1] == "design-editor", f"回答后恢复链路错误：{ids}")
    finally:
        holder.cleanup()


def test_full_graph_order() -> None:
    holder, root = project("full", False)
    try:
        result = host(root, "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        ids = [event["program_declared"]["task_id"] for event in trace(root)]
        positions = {task: ids.index(task) for task in ("a-layer", "b-layer", "c-layer", "design-editor")}
        check(positions["a-layer"] < positions["b-layer"] < positions["c-layer"] < positions["design-editor"], "完整模式顺序必须是 A → B → C → Design")
        check(not any(any(token in task for token in ("review", "check", "compile", "report")) for task in ids), "完整模式不得包含旧的生成后动作")
        check(orch.handle_status(root)["state"] == "completed", "完整模式完成后必须直接 completed")
    finally:
        holder.cleanup()


def test_failure_retry_and_material_invalidation() -> None:
    holder, root = project("full", False)
    try:
        result = host(root, "--fail-on", "a-layer=1", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        events = [event for event in trace(root) if event["program_declared"]["task_id"] == "a-layer"]
        check(len(events) == 2 and [event["result"] for event in events] == ["failure", "success"], "动作失败后应只重试当前动作")
        check(len(orch.load_state(root)["failures"]) == 1, "失败应写入状态")

        source = root / "materials/01-background.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n材料发生变化。", encoding="utf-8")
        preview = orch.next_action(root)
        check(preview["ready_actions"][0]["task_id"] == "align", "材料变化后必须先重新执行 Align")
    finally:
        holder.cleanup()


def test_action_contracts_and_design_upstream() -> None:
    holder, root = project("full", True)
    try:
        manifest, error = orch.read_input_manifest(root)
        check(manifest is not None, error or "输入清单不存在")
        tasks = orch.task_map("full", manifest)
        check(set(tasks) == {"align", "material-index", "material-merge", "a-layer", "b-layer", "c-layer", "design-editor", *[x for x in tasks if x.startswith("material-facts:")]}, "完整模式任务图不应包含旧细粒度节点")
        fact_task = next(task for task in tasks.values() if task["task_id"].startswith("material-facts:"))
        check(set(orch.output_contract(fact_task)["required"]) == {"schema_version", "source_path", "source_hash", "material_revision", "facts"}, "事实输出契约不完整")
        check("coverage" in orch.output_contract(tasks["a-layer"])["required"], "A 层必须有最小基线契约")
        check(orch.output_contract(tasks["design-editor"]) == {"type": "object", "required": []}, "Design 文本动作不应伪造检查 JSON 契约")

        action = orch.make_action(root, tasks["design-editor"], manifest)
        for raw in action["expected_outputs"]:
            path = root / raw
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("占位", encoding="utf-8")
        ok, message = orch.accept_outputs(root, action)
        check(not ok and "上游基线" in message, "Design 缺少 A/B/C 基线时不能接受")
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
    tests = [
        test_supported_modes_and_selection,
        test_simple_graph_and_completion,
        test_no_materials_path,
        test_align_question_pause_and_answer_resume,
        test_full_graph_order,
        test_failure_retry_and_material_invalidation,
        test_action_contracts_and_design_upstream,
        test_legacy_run_rejected,
    ]
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
    print(f"Design v2 编排器测试通过：{len(tests)} 个用例")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
