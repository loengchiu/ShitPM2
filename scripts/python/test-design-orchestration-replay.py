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


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_trace(root: Path) -> list[dict[str, Any]]:
    path = root / ".workflow/runtime/context/design/host-execution-log.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def task_events(root: Path, task_id: str) -> list[dict[str, Any]]:
    return [event for event in read_trace(root) if event.get("program_declared", {}).get("task_id") == task_id]


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
            {"schema_version": "material-fact/v2", "source_path": item, "source_hash": orch.safe_file_hash(root, item), "material_revision": revision, "facts": []},
        )
    orch.write_json(orch.material_dir(root) / "facts.json", {"version": 1, "material_revision": revision, "confirmed_facts": [], "source_conflicts": [], "missing_information": [], "non_derivable_items": []})
    tasks = orch.task_map(manifest["mode"], manifest)
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
    holder, root = make_project("simple", seed=False)
    try:
        result = run_host(root, "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        ids = [event["program_declared"]["task_id"] for event in read_trace(root)]
        check(ids[-1] == "simple-design", f"简单模式最后动作错误: {ids}")
        check(not any("review" in task or "check" in task or "compile" in task or "report" in task for task in ids), "简单模式不应有生成后检查动作")
        check(orch.handle_status(root)["state"] == "completed", "简单模式回放后必须 completed")
    finally:
        holder.cleanup()


def test_full_action_trace() -> None:
    holder, root = make_project("full", seed=False)
    try:
        result = run_host(root, "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        ids = [event["program_declared"]["task_id"] for event in read_trace(root)]
        check(ids.index("a-layer") < ids.index("b-layer") < ids.index("c-layer") < ids.index("design-editor"), f"完整模式顺序错误: {ids}")
        check(not any(task.startswith(("a1-", "a2-", "b1-", "b2-", "c1-", "c2-", "c3-", "c4-")) for task in ids), "不应回放旧的细粒度 A/B/C 节点")
        check(orch.handle_status(root)["state"] == "completed", "完整模式回放后必须 completed")
    finally:
        holder.cleanup()


def test_failure_retry_only_current_action() -> None:
    holder, root = make_project("full")
    try:
        result = run_host(root, "--fail-on", "b-layer=1", "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        events = task_events(root, "b-layer")
        check([event["result"] for event in events] == ["failure", "success"], "失败后必须只重试当前动作")
        check(len(task_events(root, "a-layer")) == 1, "上游 A 层不应因 B 层失败而重跑")
        check(len(orch.load_state(root)["failures"]) == 1, "失败记录必须保留")
    finally:
        holder.cleanup()


def test_design_editor_interruption_recovery() -> None:
    holder, root = make_project("full")
    try:
        first = run_host(root, "--interrupt-after", "design-editor", "--max-steps", "200")
        check(first.returncode == 75, "设计写作前中断注入必须返回中断码")
        ready_ids = {action["task_id"] for action in orch.next_action(root).get("ready_actions", [])}
        check(ready_ids == {"design-editor"}, f"中断后应只保留 Design 写作: {ready_ids}")
        second = run_host(root, "--max-steps", "200")
        check(second.returncode == 0, second.stdout + second.stderr)
        check(len(task_events(root, "design-editor")) == 1, "中断未产生输出时，Design 写作应安全重试")
    finally:
        holder.cleanup()


def test_align_and_abc_breakpoint_recovery() -> None:
    for target in ("align", "a-layer", "b-layer", "c-layer"):
        holder, root = make_project("full")
        try:
            first = run_host(root, "--interrupt-after", target, "--max-steps", "200")
            check(first.returncode == 75, f"{target} 中断注入必须返回中断码")
            ready_ids = {action["task_id"] for action in orch.next_action(root).get("ready_actions", [])}
            check(ready_ids == {target}, f"{target} 中断后应只恢复当前动作：{ready_ids}")
            second = run_host(root, "--max-steps", "200")
            check(second.returncode == 0, second.stdout + second.stderr)
            check(orch.handle_status(root)["state"] == "completed", f"{target} 断点恢复后必须 completed")
        finally:
            holder.cleanup()


def test_stale_action_and_tampered_output_rejected() -> None:
    holder, root = make_project("simple")
    try:
        action = orch.next_action(root)["ready_actions"][0]
        check(action["task_id"] == "align", "输入变化测试必须从 Align 开始")
        source = root / "materials/02-roles-and-scope.md"
        before = action["input_hashes"]
        source.write_text(source.read_text(encoding="utf-8") + "\n陈旧输入", encoding="utf-8")
        refreshed = orch.next_action(root)["ready_actions"][0]
        check(refreshed["task_id"] == "align" and refreshed["input_hashes"] != before, "输入变化后 Align 必须失效并刷新输入")
        result = run_host(root, "--max-steps", "200")
        check(result.returncode == 0, result.stdout + result.stderr)
        design = root / "output/design/design.md"
        design.write_text(design.read_text(encoding="utf-8") + "\n篡改", encoding="utf-8")
        preview = orch.next_action(root)
        check([action["task_id"] for action in preview.get("ready_actions", [])] == ["simple-design"], "被篡改的 Design 输出不得被误认有效")
    finally:
        holder.cleanup()


def main() -> int:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    failures = []
    for test in tests:
        try:
            test()
        except Exception as exc:
            failures.append(f"{test.__name__}: {exc}")
    if failures:
        print(f"Design 编排回放测试失败：{len(failures)}/{len(tests)}")
        for item in failures:
            print(f"- {item}")
        return 1
    print(f"Design 编排回放测试通过：{len(tests)} 个用例")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
