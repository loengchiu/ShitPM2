from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable
ORCH = ROOT / "scripts/python/design-orchestrator.py"
HOST = ROOT / "scripts/python/fake-design-host.py"
CONFIRM = ROOT / "scripts/python/design-confirmation.py"
FIXTURE = ROOT / "test-fixture/design-orchestration/synthetic-full/materials"
RETIRED = (
    "review" + "-precheck.py",
    "artifact" + "-guard.py",
    "state-machine" + "-check.py",
    "verify-" + "against-metadata.py",
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if cwd:
        env["SHITPM_BUNDLE_ROOT"] = str(cwd / "bundle")
    return subprocess.run([PYTHON, str(script), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env)


def make_project() -> tuple[tempfile.TemporaryDirectory, Path]:
    holder = tempfile.TemporaryDirectory(prefix="spm-regression-")
    root = Path(holder.name)
    shutil.copytree(FIXTURE, root / "materials")
    materials = [str(path) for path in sorted((root / "materials").glob("*.md"))]
    result = run(ORCH, "init", "--project-root", str(root), "--request", "生成设备借还 Design", "--mode", "full", *sum((["--materials", item] for item in materials), []), cwd=root)
    check(result.returncode == 0, result.stdout + result.stderr)
    return holder, root


def test_end_to_end_and_hash_confirmation() -> None:
    holder, root = make_project()
    try:
        host = run(HOST, "--project-root", str(root), "--max-steps", "200", cwd=root)
        check(host.returncode == 0, host.stdout + host.stderr)
        design = root / "output/design/design.md"
        check(design.is_file() and design.read_text(encoding="utf-8").strip(), "Design 产物缺失")

        confirmed = run(CONFIRM, "--project-root", str(root), "confirm", cwd=root)
        check(confirmed.returncode == 0, confirmed.stdout + confirmed.stderr)
        checked = run(CONFIRM, "--project-root", str(root), "check", cwd=root)
        payload = json.loads(checked.stdout)
        check(checked.returncode == 0 and payload.get("confirmed") is True, "Design 确认哈希检查失败")

        design.write_text(design.read_text(encoding="utf-8") + "\n发生修改。", encoding="utf-8")
        stale = run(CONFIRM, "--project-root", str(root), "check", cwd=root)
        stale_payload = json.loads(stale.stdout)
        check(stale.returncode != 0 and stale_payload.get("reason") == "hash_mismatch", "Design 修改后必须由哈希失效")
    finally:
        holder.cleanup()


def test_retired_scripts_are_removed() -> None:
    for name in RETIRED:
        check(not (ROOT / "scripts/python" / name).exists(), f"废弃脚本仍存在: {name}")


def test_retained_tools_still_exist() -> None:
    for name in ("design-index.py", "stage-prep.py", "prd-consistency-check.py", "prototype-consistency-check.py"):
        check((ROOT / "scripts/python" / name).is_file(), f"应保留工具缺失: {name}")


def main() -> int:
    tests = [test_end_to_end_and_hash_confirmation, test_retired_scripts_are_removed, test_retained_tools_still_exist]
    failures = []
    for test in tests:
        try:
            test()
        except Exception as exc:
            failures.append(f"{test.__name__}: {exc}")
    if failures:
        print(f"ShitPM 回归测试失败：{len(failures)}/{len(tests)}")
        for item in failures:
            print(f"- {item}")
        return 1
    print(f"ShitPM 回归测试通过：{len(tests)} 个用例")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
