#!/usr/bin/env python3
"""design-confirmation.py — Design 确认标记读写工具

ShitPM：用户对当前 design.md 的最小确认机制。
- 不复制产品事实
- 不扩展为新的业务阶段
- 只记录确认对象、SHA-256 哈希和确认时间

子命令：
  confirm  计算当前 design.md 的 SHA-256 并写入确认文件。仅当用户明确确认时调用。
  check    重新计算 design.md 哈希并与确认文件比对，输出是否仍处于已确认状态。
  show     输出当前确认标记内容（如存在）。

用法：
  python design-confirmation.py --project-root <path> confirm [--by <name>] [--note <text>]
  python design-confirmation.py --project-root <path> check
  python design-confirmation.py --project-root <path> show

退出码：
  confirm: 0=写入成功, 1=错误（design.md 不存在等）
  check:   0=哈希一致（已确认有效）, 2=哈希不一致（需重新确认）, 3=无确认记录, 1=错误
  show:    0=输出确认内容, 3=无确认记录, 1=错误

仅修改 `output/design/decision-notes.md` 不影响 Design 确认状态，也不改变下游事实基线。

确认标记的契约定义见 `schemas/design-confirmation.schema.json`，本脚本用标准库实现等价必要校验，
不依赖可选 jsonschema 库。确认 Schema 已进入执行路径：cmd_check 和 cmd_show 在读取后立即校验。
"""

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path


DESIGN_ARTIFACT = "output/design/design.md"
CONFIRMATION_FILE = ".workflow/confirmations/design.json"


def _resolve(project_root: str) -> Path:
    root = Path(project_root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"项目根目录不存在: {root}")
    return root


def _design_path(root: Path) -> Path:
    return root / DESIGN_ARTIFACT


def _confirmation_path(root: Path) -> Path:
    return root / CONFIRMATION_FILE


def compute_sha256(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"design.md 不存在: {file_path}")
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_confirmation(root: Path) -> dict | None:
    path = _confirmation_path(root)
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        return {"__corrupted__": True, "source": str(path), "error": str(e)}
    if not isinstance(data, dict):
        return {
            "__corrupted__": True,
            "source": str(path),
            "error": f"confirmation JSON 必须是对象，实际为 {type(data).__name__}",
        }
    return data


def _validate_payload(payload: dict) -> list[str]:
    problems: list[str] = []
    if payload.get("artifact") != DESIGN_ARTIFACT:
        problems.append(f"artifact 必须等于 {DESIGN_ARTIFACT!r}")
    digest = payload.get("content_sha256")
    if not isinstance(digest, str) or not digest:
        problems.append("content_sha256 必须是非空字符串")
    else:
        if len(digest) != 64:
            problems.append(f"content_sha256 长度必须为 64，实际 {len(digest)}")
        else:
            try:
                int(digest, 16)
            except ValueError:
                problems.append("content_sha256 必须是十六进制字符串")
    confirmed_at = payload.get("confirmed_at")
    if not isinstance(confirmed_at, str) or not confirmed_at:
        problems.append("confirmed_at 必须是非空字符串")
    else:
        try:
            datetime.datetime.fromisoformat(confirmed_at.replace("Z", "+00:00"))
        except ValueError:
            problems.append("confirmed_at 必须是合法 ISO 8601 时间字符串")
    confirmed_by = payload.get("confirmed_by")
    if not (confirmed_by is None or isinstance(confirmed_by, str)):
        problems.append("confirmed_by 必须是字符串或 None")
    note = payload.get("note")
    if not (note is None or isinstance(note, str)):
        problems.append("note 必须是字符串或 None")
    return problems


def run_deterministic_gate(root: Path) -> tuple[bool, dict | None, str | None]:
    """确认前执行确定性安全网；缺失、崩溃、不可解析或 P1 均失败关闭。"""
    checker = Path(__file__).with_name("state-machine-check.py")
    if not checker.exists():
        return False, None, f"确定性检查器不存在: {checker}"
    try:
        proc = subprocess.run(
            [sys.executable, str(checker), "--project-root", str(root), "--source", "design"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            stdin=subprocess.DEVNULL,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return False, None, f"确定性检查器执行失败: {e}"

    stdout = proc.stdout.strip()
    if not stdout:
        detail = proc.stderr.strip() or "检查器没有输出"
        return False, None, f"确定性检查器输出为空: {detail}"
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError as e:
        return False, None, f"确定性检查器输出无法解析为 JSON: {e}"
    if not isinstance(report, dict):
        return False, None, "确定性检查器输出必须是 JSON 对象"

    summary = report.get("summary") or {}
    p1 = summary.get("P1", 0)
    if not isinstance(p1, int):
        return False, report, "确定性检查器的 P1 汇总不是整数"
    if proc.returncode != 0 or report.get("ok") is False or p1 > 0:
        detail = report.get("error") or report.get("violations") or proc.stderr.strip() or "检查器报告失败"
        return False, report, f"确定性检查未通过: {detail}"
    return True, report, None


def save_confirmation(root: Path, payload: dict) -> None:
    path = _confirmation_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def cmd_confirm(root: Path, by: str | None, note: str | None) -> int:
    design = _design_path(root)
    try:
        digest = compute_sha256(design)
    except FileNotFoundError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1

    gate_ok, gate_report, gate_error = run_deterministic_gate(root)
    if not gate_ok:
        print(json.dumps({
            "ok": False,
            "error": gate_error,
            "deterministic_gate": gate_report,
            "hint": "请修复可证明的 Design 结构错误，或明确声明无状态机后再确认。",
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    payload = {
        "artifact": DESIGN_ARTIFACT,
        "content_sha256": digest,
        "confirmed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if by is not None:
        payload["confirmed_by"] = by
    if note is not None:
        payload["note"] = note

    save_confirmation(root, payload)
    print(json.dumps({"ok": True, "confirmation": payload, "deterministic_gate": gate_report}, ensure_ascii=False, indent=2))
    return 0


def cmd_check(root: Path) -> int:
    design = _design_path(root)
    confirmation = load_confirmation(root)

    if confirmation is None:
        print(json.dumps({
            "ok": True,
            "confirmed": False,
            "reason": "no_confirmation_record",
            "hint": "用户尚未确认当前 Design。请由用户明确确认后再调用 confirm。",
        }, ensure_ascii=False, indent=2))
        return 3

    if confirmation.get("__corrupted__"):
        print(json.dumps({
            "ok": False,
            "error": f"confirmation JSON corrupted: {confirmation.get('error', '')}",
            "source": confirmation.get("source", ""),
            "hint": "请用 design-confirmation.py confirm 重新写入。",
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    problems = _validate_payload(confirmation)
    if problems:
        print(json.dumps({
            "ok": True,
            "confirmed": False,
            "reason": "confirmation_invalid",
            "problems": problems,
            "hint": "确认文件字段不合规。请用 design-confirmation.py confirm 重新写入。",
        }, ensure_ascii=False, indent=2))
        return 1

    gate_ok, gate_report, gate_error = run_deterministic_gate(root)
    if not gate_ok:
        print(json.dumps({
            "ok": False,
            "confirmed": False,
            "reason": "deterministic_gate_failed",
            "error": gate_error,
            "deterministic_gate": gate_report,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    try:
        current_digest = compute_sha256(design)
    except FileNotFoundError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1

    stored_digest = confirmation.get("content_sha256", "")
    match = (current_digest == stored_digest)

    result = {
        "ok": True,
        "confirmed": match,
        "artifact": DESIGN_ARTIFACT,
        "current_sha256": current_digest,
        "confirmed_sha256": stored_digest,
        "confirmed_at": confirmation.get("confirmed_at"),
        "deterministic_gate": gate_report,
    }
    if match:
        result["reason"] = "hash_match"
    else:
        result["reason"] = "hash_mismatch"
        result["hint"] = "design.md 在上次确认后被修改。需要用户重新确认后下游才能继续。"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if match else 2


def cmd_show(root: Path) -> int:
    confirmation = load_confirmation(root)
    if confirmation is None:
        print(json.dumps({
            "ok": True,
            "confirmed": False,
            "reason": "no_confirmation_record",
        }, ensure_ascii=False, indent=2))
        return 3

    if confirmation.get("__corrupted__"):
        print(json.dumps({
            "ok": False,
            "error": f"confirmation JSON corrupted: {confirmation.get('error', '')}",
            "source": confirmation.get("source", ""),
            "hint": "请用 design-confirmation.py confirm 重新写入。",
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    problems = _validate_payload(confirmation)
    if problems:
        print(json.dumps({
            "ok": True,
            "confirmed": False,
            "reason": "confirmation_invalid",
            "problems": problems,
            "hint": "确认文件字段不合规。请用 design-confirmation.py confirm 重新写入。",
        }, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps({"ok": True, "confirmation": confirmation}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Design 确认标记读写工具")
    parser.add_argument("--project-root", required=True, help="项目根目录")
    sub = parser.add_subparsers(dest="command", required=True)

    p_confirm = sub.add_parser("confirm", help="写入确认标记（仅在用户明确确认后调用）")
    p_confirm.add_argument("--by", help="可选：确认人标识")
    p_confirm.add_argument("--note", help="可选：用户附注")

    sub.add_parser("check", help="检查 design.md 哈希是否仍与确认记录一致")
    sub.add_parser("show", help="输出当前确认标记内容")

    args = parser.parse_args()

    try:
        root = _resolve(args.project_root)
    except FileNotFoundError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1

    if args.command == "confirm":
        return cmd_confirm(root, args.by, args.note)
    if args.command == "check":
        return cmd_check(root)
    if args.command == "show":
        return cmd_show(root)

    parser.error(f"未知子命令: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
