#!/usr/bin/env python3
"""下游产物的确认门禁、来源登记和陈旧检查。"""

import argparse
import datetime
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


DESIGN = "output/design/design.md"
ARTIFACTS = {"prd": "output/prd/prd.md", "prototype": "output/prototype/index.html"}


def _load_confirmation_module():
    path = Path(__file__).with_name("design-confirmation.py")
    spec = importlib.util.spec_from_file_location("design_confirmation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _provenance_path(root: Path, stage: str) -> Path:
    return root / ".workflow" / "provenance" / f"{stage}.json"


def _run_confirmation(root: Path) -> tuple[int, dict]:
    module = _load_confirmation_module()
    confirmation = module.load_confirmation(root)
    if confirmation is None:
        return 3, {"confirmed": False, "reason": "no_confirmation_record"}
    if confirmation.get("__corrupted__"):
        return 1, {"confirmed": False, "reason": "confirmation_corrupted"}
    problems = module._validate_payload(confirmation)
    if problems:
        return 1, {"confirmed": False, "reason": "confirmation_invalid", "problems": problems}
    try:
        current = module.compute_sha256(root / DESIGN)
    except FileNotFoundError as exc:
        return 1, {"confirmed": False, "reason": "design_missing", "error": str(exc)}
    stored = confirmation.get("content_sha256")
    if current != stored:
        return 2, {
            "confirmed": False,
            "reason": "source_hash_mismatch",
            "current_sha256": current,
            "confirmed_sha256": stored,
        }
    return 0, {"confirmed": True, "reason": "hash_match", "current_sha256": current}


def _run_checker(root: Path, stage: str) -> tuple[int, dict]:
    script = "prd-consistency-check.py" if stage == "prd" else "prototype-consistency-check.py"
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).with_name(script)), "--project-root", str(root)],
        capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL,
    )
    try:
        result = json.loads(proc.stdout) if proc.stdout.strip() else {"error": proc.stderr}
    except json.JSONDecodeError:
        result = {"error": proc.stdout or proc.stderr}
    return proc.returncode, result


def cmd_check_input(root: Path, stage: str) -> int:
    code, confirmation = _run_confirmation(root)
    result = {"ok": code == 0, "stage": stage, "confirmation": confirmation}
    if code != 0:
        result["reason"] = "design_not_confirmed"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


def cmd_record(root: Path, stage: str) -> int:
    input_code, confirmation = _run_confirmation(root)
    artifact = root / ARTIFACTS[stage]
    if input_code != 0:
        print(json.dumps({"ok": False, "reason": "design_not_confirmed", "confirmation": confirmation}, ensure_ascii=False, indent=2))
        return input_code
    if not artifact.is_file():
        print(json.dumps({"ok": False, "reason": "artifact_missing", "artifact": ARTIFACTS[stage]}, ensure_ascii=False, indent=2))
        return 2
    checker_code, checker = _run_checker(root, stage)
    if checker_code != 0:
        print(json.dumps({"ok": False, "reason": "consistency_check_failed", "checker": checker}, ensure_ascii=False, indent=2))
        return checker_code
    provenance = {
        "artifact": ARTIFACTS[stage],
        "source_artifact": DESIGN,
        "source_sha256": confirmation["current_sha256"],
        "artifact_sha256": _sha256(artifact),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checker": stage + "-consistency-check.py",
    }
    path = _provenance_path(root, stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "stage": stage, "provenance": provenance}, ensure_ascii=False, indent=2))
    return 0


def cmd_check(root: Path, stage: str) -> int:
    input_code, confirmation = _run_confirmation(root)
    artifact = root / ARTIFACTS[stage]
    path = _provenance_path(root, stage)
    result = {"stage": stage, "confirmation": confirmation, "artifact": ARTIFACTS[stage], "stale": True}
    reason = confirmation.get("reason", "design_not_confirmed") if isinstance(confirmation, dict) else "design_not_confirmed"
    if input_code == 0 and not artifact.is_file():
        reason = "artifact_missing"
    elif input_code == 0 and not path.is_file():
        reason = "no_provenance_record"
    elif input_code == 0:
        try:
            provenance = json.loads(path.read_text(encoding="utf-8"))
            current_artifact = _sha256(artifact)
            if provenance.get("source_sha256") != confirmation["current_sha256"]:
                reason = "source_hash_mismatch"
            elif provenance.get("artifact_sha256") != current_artifact:
                reason = "artifact_hash_mismatch"
            else:
                checker_code, checker = _run_checker(root, stage)
                result["checker"] = checker
                if checker_code == 0:
                    result["stale"] = False
                    reason = "fresh"
                else:
                    reason = "consistency_check_failed"
            result["provenance"] = provenance
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            reason = "provenance_invalid"
            result["error"] = str(exc)
    result["reason"] = reason
    result["ok"] = not result["stale"]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="下游产物 guard")
    parser.add_argument("--project-root", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("check-input", "record", "check"):
        child = sub.add_parser(command)
        child.add_argument("--stage", choices=sorted(ARTIFACTS), required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(json.dumps({"ok": False, "reason": "project_root_missing"}, ensure_ascii=False))
        return 2
    if args.command == "check-input":
        return cmd_check_input(root, args.stage)
    if args.command == "record":
        return cmd_record(root, args.stage)
    return cmd_check(root, args.stage)


if __name__ == "__main__":
    sys.exit(main())
