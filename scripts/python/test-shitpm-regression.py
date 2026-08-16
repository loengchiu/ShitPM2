from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable
CONFIRM = ROOT / "scripts/python/design-confirmation.py"
RETIRED = (
    "design-orchestrator.py",
    "fake-design-host.py",
    "test-design-orchestrator.py",
    "test-design-orchestration-replay.py",
    "test-design-simplification.py",
    "review" + "-precheck.py",
    "artifact" + "-guard.py",
    "state-machine" + "-check.py",
    "verify-" + "against-metadata.py",
)
RETIRED_DOCS = (
    ("contracts", "design-orchestration-contract.md"),
    ("schemas", "design-orchestration-action.schema.json"),
)
RETIRED_DIRS = ("test-fixture/design-orchestration", "design-rule-cache", ".tmp-fusion")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )


def test_confirm_hash_lifecycle() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-regression-") as temp:
        root = Path(temp)
        design = root / "output" / "design" / "design.md"
        design.parent.mkdir(parents=True)
        design.write_text("# 产品方案设计\n\n测试项目。\n", encoding="utf-8")

        confirmed = run(CONFIRM, "--project-root", str(root), "confirm", cwd=root)
        check(confirmed.returncode == 0, confirmed.stdout + confirmed.stderr)
        checked = run(CONFIRM, "--project-root", str(root), "check", cwd=root)
        payload = json.loads(checked.stdout)
        check(checked.returncode == 0 and payload.get("confirmed") is True, "Design 确认哈希检查失败")

        design.write_text(design.read_text(encoding="utf-8") + "\n发生修改。\n", encoding="utf-8")
        stale = run(CONFIRM, "--project-root", str(root), "check", cwd=root)
        stale_payload = json.loads(stale.stdout)
        check(
            stale.returncode != 0 and stale_payload.get("reason") == "hash_mismatch",
            "Design 修改后必须由哈希失效",
        )


def test_retired_assets_are_removed() -> None:
    for name in RETIRED:
        check(not (ROOT / "scripts/python" / name).exists(), f"废弃脚本仍存在: {name}")
    for dirname, name in RETIRED_DOCS:
        check(not (ROOT / dirname / name).exists(), f"废弃文档仍存在: {dirname}/{name}")
    for rel in RETIRED_DIRS:
        check(not (ROOT / rel).exists(), f"废弃目录仍存在: {rel}")


def test_retained_tools_still_exist() -> None:
    for name in (
        "design-index.py",
        "stage-prep.py",
        "prd-consistency-check.py",
        "prototype-consistency-check.py",
        "source-index.py",
        "context-runtime-check.py",
    ):
        check((ROOT / "scripts/python" / name).is_file(), f"应保留工具缺失: {name}")


def main() -> int:
    tests = [test_confirm_hash_lifecycle, test_retired_assets_are_removed, test_retained_tools_still_exist]
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
