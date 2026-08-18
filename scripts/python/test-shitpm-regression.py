from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable
DESIGN_SET = ROOT / "scripts/python/design-set.py"
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
    "design-confirmation.py",
)
RETIRED_DOCS = (
    ("contracts", "design-orchestration-contract.md"),
    ("schemas", "design-orchestration-action.schema.json"),
    ("schemas", "design-confirmation.schema.json"),
    ("templates", "decision-notes.md"),
    ("templates", "design.md"),
)
RETIRED_DIRS = ("test-fixture/design-orchestration", "design-rule-cache", ".tmp-fusion")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args], cwd=cwd, capture_output=True, text=True, encoding='utf-8'
    )


def test_design_set_manifest_lifecycle() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-regression-") as temp:
        root = Path(temp)
        manifest_dir = root / "output" / "design"
        (manifest_dir / "系统级基线").mkdir(parents=True)
        map_path = manifest_dir / "设计地图.md"
        map_path.write_text("# 设计地图\n\n## 系统目标与边界\n测试项目。\n", encoding="utf-8")
        sys_path = manifest_dir / "系统级基线" / "系统边界.md"
        sys_path.write_text("# 系统边界\n\n边界内容。\n", encoding="utf-8")

        def sha(p: Path) -> str:
            return hashlib.sha256(p.read_bytes()).hexdigest()

        manifest = {
            "schema_version": "shitpm-design-set/v1",
            "set_sha256": "",
            "files": [
                {"id": "MAP-001", "path": "设计地图.md", "type": "map", "module": None, "business_chains": [], "depends_on": [], "sha256": sha(map_path)},
                {"id": "SYS-001", "path": "系统级基线/系统边界.md", "type": "system", "module": None, "business_chains": [], "depends_on": [], "sha256": sha(sys_path)},
            ],
            "decisions": [],
        }
        parts = []
        for f in sorted(manifest["files"], key=lambda x: x["id"]):
            parts.append(f["id"] + f["path"] + f["sha256"])
        manifest["set_sha256"] = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
        (manifest_dir / "设计集清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        checked = run(DESIGN_SET, "check", "--project-root", str(root), cwd=root)
        payload = json.loads(checked.stdout)
        check(checked.returncode == 0 and payload.get("ok") is True, "设计集清单检查失败")

        # 修改 Design 文件后 check 必须失败（指纹不一致）
        sys_path.write_text(sys_path.read_text(encoding="utf-8") + "\n发生修改。\n", encoding="utf-8")
        stale = run(DESIGN_SET, "check", "--project-root", str(root), cwd=root)
        stale_payload = json.loads(stale.stdout)
        check(
            stale.returncode == 2
            and any("指纹不一致" in e for e in stale_payload.get("errors", [])),
            "Design 文件修改后必须由指纹检查指出不一致",
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
        "design-set.py",
        "stage-prep.py",
        "prd-consistency-check.py",
        "prototype-consistency-check.py",
        "source-index.py",
        "context-runtime-check.py",
    ):
        check((ROOT / "scripts/python" / name).is_file(), f"应保留工具缺失: {name}")


def main() -> int:
    tests = [test_design_set_manifest_lifecycle, test_retired_assets_are_removed, test_retained_tools_still_exist]
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
