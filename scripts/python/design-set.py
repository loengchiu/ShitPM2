#!/usr/bin/env python3
"""design-set.py — ShitPM 设计集确定性工具

职责（只处理确定性文件关系，不判断业务语义）：
  check          校验设计集清单：Schema、路径、ID、依赖、地图引用和指纹
  closure        根据目标文件 ID 沿 depends_on 输出递归依赖闭包
  stage-single   建立单文件轻量事务并返回临时写入路径
  commit-single  检查并提交单文件、候选清单和实际受影响的 provenance
  begin          创建多文件 active.json、staged 和 backup
  commit         检查并提交多文件修改
  recover        从单文件或多文件中断状态恢复旧完整集合或完成已准备完整的新集合
  record-inputs  写入 PRD / Prototype 模块依据
  check-inputs   检查指定下游模块是否 current / affected / incomplete

退出码：0=成功；1=用法或运行错误；2=校验失败（check/commit 发现清单问题）。
不调用模型、不联网、不生成证明性报告。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import shutil
from pathlib import Path
from typing import Any


SCHEMA_SET = "shitpm-design-set/v1"
SCHEMA_INPUTS = "shitpm-design-inputs/v1"
SCHEMA_CHANGE = "shitpm-design-change/v1"

MANIFEST_REL = Path("output/design/设计集清单.json")
DESIGN_ROOT_REL = Path("output/design")
SINGLE_REL = Path(".workflow/runtime/design-change/single")
MULTI_REL = Path(".workflow/runtime/design-change")
PRD_PROV_REL = Path(".workflow/provenance/prd.json")
PROTO_PROV_REL = Path(".workflow/provenance/prototype.json")

ID_RE = re.compile(r"^(MAP|SYS|CON|MOD)-\d{3}$")
DEC_RE = re.compile(r"^DEC-\d{3}$")
MAP_ID_RE = re.compile(r"\b(MAP|SYS|CON|MOD|DEC)-\d{3}\b")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

VALID_TYPES = ("map", "system", "contract", "module")
VALID_DECISION_STATUS = ("defined", "pending", "excluded")
VALID_TARGET_STATUS = ("current", "affected", "incomplete")
VALID_CHECK_STATUS = ("passed", "failed", "not_run")


# ── 基础工具 ────────────────────────────────────────────────


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_root_of(value: str) -> Path:
    root = Path(value).resolve()
    if not root.is_dir():
        raise SystemExit(f"项目根目录不存在: {root}")
    return root


# ── 设计集清单加载与校验 ─────────────────────────────────────


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_REL


def design_path(root: Path, rel: str) -> Path:
    return (root / DESIGN_ROOT_REL / rel).resolve()


def validate_path_field(rel: str) -> list[str]:
    problems: list[str] = []
    if not rel or rel.startswith(("/", "\\")):
        problems.append(f"path 不得是绝对路径: {rel!r}")
    if re.match(r"^[A-Za-z]:[/\\]", rel):
        problems.append(f"path 不得是绝对路径: {rel!r}")
    if ".." in rel.split("/"):
        problems.append(f"path 不得包含 ..: {rel!r}")
    if "\\" in rel:
        problems.append(f"path 必须使用 / 分隔: {rel!r}")
    if rel.endswith("/"):
        problems.append(f"path 不得以 / 结尾: {rel!r}")
    return problems


def load_manifest(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """加载设计集清单。返回 (数据, 问题列表)。"""
    path = manifest_path(root)
    if not path.is_file():
        return None, [f"设计集清单不存在: {MANIFEST_REL.as_posix()}"]
    data = load_json(path)
    if data is None:
        return None, [f"设计集清单不是有效 JSON: {MANIFEST_REL.as_posix()}"]
    return data, []


def check_manifest(root: Path, data: dict[str, Any]) -> list[str]:
    """校验清单的结构、ID、路径、依赖、类型规则和指纹。返回问题列表。"""
    problems: list[str] = []
    if data.get("schema_version") != SCHEMA_SET:
        problems.append(f"schema_version 必须为 {SCHEMA_SET}")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        problems.append("files 必须是非空数组")
        files = []

    seen_ids: set[str] = set()
    id_to_entry: dict[str, dict[str, Any]] = {}
    for i, entry in enumerate(files):
        if not isinstance(entry, dict):
            problems.append(f"files[{i}] 必须是对象")
            continue
        fid = entry.get("id")
        if not isinstance(fid, str) or not ID_RE.match(fid):
            problems.append(f"files[{i}].id 必须匹配 (MAP|SYS|CON|MOD)-NNN: {fid!r}")
        else:
            if fid in seen_ids:
                problems.append(f"重复文件 ID: {fid}")
            seen_ids.add(fid)
            id_to_entry[fid] = entry
        ftype = entry.get("type")
        if ftype not in VALID_TYPES:
            problems.append(f"files[{i}].type 只允许 {VALID_TYPES}: {ftype!r}")
        fpath = entry.get("path")
        if not isinstance(fpath, str):
            problems.append(f"files[{i}].path 必须是字符串")
        else:
            problems.extend(
                f"files[{i}].path {p}" for p in validate_path_field(fpath)
            )
            if isinstance(fpath, str):
                resolved = design_path(root, fpath)
                if not resolved.is_file():
                    problems.append(f"files[{i}].path 文件不存在: {fpath}")
        module = entry.get("module")
        if ftype == "module":
            if not isinstance(module, str) or not module:
                problems.append(f"files[{i}] type=module 时 module 必填")
        elif module is not None:
            problems.append(f"files[{i}] type={ftype} 时 module 必须为 null")
        chains = entry.get("business_chains")
        if not isinstance(chains, list) or not all(isinstance(c, str) for c in chains):
            problems.append(f"files[{i}].business_chains 必须是字符串数组")
        deps = entry.get("depends_on")
        if not isinstance(deps, list):
            problems.append(f"files[{i}].depends_on 必须是数组")
        else:
            for dep in deps:
                if not isinstance(dep, str) or not ID_RE.match(dep):
                    problems.append(f"files[{i}].depends_on 含非法 ID: {dep!r}")
        digest = entry.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            problems.append(f"files[{i}].sha256 必须是 64 位十六进制: {digest!r}")
        elif isinstance(fpath, str) and isinstance(fid, str) and ID_RE.match(fid):
            resolved = design_path(root, fpath)
            if resolved.is_file():
                actual = sha256_file(resolved)
                if actual != digest:
                    problems.append(f"文件指纹不一致: {fid} ({fpath}) 登记 {digest[:12]}… 实际 {actual[:12]}…")

    # 依赖引用与环
    for i, entry in enumerate(files):
        if not isinstance(entry, dict):
            continue
        fid = entry.get("id")
        deps = entry.get("depends_on")
        if not isinstance(fid, str) or not isinstance(deps, list):
            continue
        for dep in deps:
            if dep not in id_to_entry:
                problems.append(f"{fid}.depends_on 引用不存在的 ID: {dep}")
    for fid in id_to_entry:
        if _has_cycle(fid, id_to_entry, set(), set()):
            problems.append(f"依赖环: {fid}")

    # 决策登记
    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        problems.append("decisions 必须是数组")
        decisions = []
    seen_dec: set[str] = set()
    for i, dec in enumerate(decisions):
        if not isinstance(dec, dict):
            problems.append(f"decisions[{i}] 必须是对象")
            continue
        did = dec.get("id")
        if not isinstance(did, str) or not DEC_RE.match(did):
            problems.append(f"decisions[{i}].id 必须匹配 DEC-NNN: {did!r}")
        elif did in seen_dec:
            problems.append(f"重复决策 ID: {did}")
        seen_dec.add(did)
        owner = dec.get("owner_file_id")
        if not isinstance(owner, str) or owner not in id_to_entry:
            problems.append(f"decisions[{i}].owner_file_id 必须引用存在的文件 ID: {owner!r}")
        if dec.get("status") not in VALID_DECISION_STATUS:
            problems.append(f"decisions[{i}].status 只允许 {VALID_DECISION_STATUS}: {dec.get('status')!r}")
        affects = dec.get("affects")
        if not isinstance(affects, list):
            problems.append(f"decisions[{i}].affects 必须是数组")
        else:
            for af in affects:
                if af not in id_to_entry:
                    problems.append(f"decisions[{i}].affects 引用不存在的 ID: {af!r}")
    # 地图引用
    map_entry = next((e for e in files if isinstance(e, dict) and e.get("type") == "map"), None)
    if map_entry is None:
        problems.append("清单中缺少 type=map 的入口（设计地图）")
    else:
        map_path = design_path(root, map_entry.get("path", ""))
        if map_path.is_file():
            text = map_path.read_text(encoding="utf-8-sig")
            for m in MAP_ID_RE.finditer(text):
                token = m.group(0)
                if token.startswith("DEC-"):
                    if token not in {d.get("id") for d in decisions if isinstance(d, dict)}:
                        problems.append(f"设计地图引用了未登记的决策 ID: {token}")
                elif token not in id_to_entry:
                    problems.append(f"设计地图引用了未登记的文件 ID: {token}")
            for target in LINK_RE.findall(text):
                target = target.strip()
                if target.startswith(("http://", "https://", "#")):
                    continue
                target = target.split("#")[0]
                if not target:
                    continue
                # 地图链接使用相对 output/design/ 的中文路径（计划 5.1 格式）
                if not any(e.get("path") == target for e in files if isinstance(e, dict)):
                    problems.append(f"设计地图链接未在清单登记: {target}")
        else:
            problems.append(f"设计地图文件不存在: {map_entry.get('path')}")
    # set_sha256
    expected = compute_set_sha256(files)
    stored = data.get("set_sha256")
    if stored != expected:
        problems.append(f"set_sha256 不一致: 登记 {stored} 期望 {expected}")
    return problems


def _has_cycle(fid: str, id_to_entry: dict[str, dict[str, Any]], visiting: set[str], visited: set[str]) -> bool:
    if fid in visiting:
        return True
    if fid in visited:
        return False
    visiting.add(fid)
    entry = id_to_entry.get(fid)
    if entry:
        for dep in entry.get("depends_on", []):
            if dep in id_to_entry and _has_cycle(dep, id_to_entry, visiting, visited):
                return True
    visiting.discard(fid)
    visited.add(fid)
    return False


def compute_set_sha256(files: list[dict[str, Any]]) -> str:
    parts = []
    for entry in sorted(files, key=lambda e: e.get("id", "")):
        parts.append(str(entry.get("id", "")))
        parts.append(str(entry.get("path", "")))
        parts.append(str(entry.get("sha256", "")))
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()


def rewrite_set_sha256(data: dict[str, Any]) -> dict[str, Any]:
    data["set_sha256"] = compute_set_sha256(data.get("files", []))
    return data


def cmd_check(root: Path, args: argparse.Namespace) -> int:
    data, problems = load_manifest(root)
    if data is None:
        _emit({"ok": False, "errors": problems})
        return 2
    problems.extend(check_manifest(root, data))
    ok = not problems
    _emit({
        "ok": ok,
        "schema_version": data.get("schema_version"),
        "set_sha256": data.get("set_sha256"),
        "file_count": len(data.get("files", [])),
        "errors": problems,
    })
    return 0 if ok else 2


def cmd_refresh(root: Path, args: argparse.Namespace) -> int:
    """重算设计集清单：每个正式文件的 sha256 与集合 set_sha256 写回清单。

    只更新指纹字段，不修改清单中的 ID、路径、类型、依赖等结构；不判断业务语义。
    首次创建清单时先用此命令补全指纹，再运行 check 验证。
    """
    path = manifest_path(root)
    if not path.is_file():
        _emit({"ok": False, "errors": [f"设计集清单不存在: {MANIFEST_REL.as_posix()}"]})
        return 1
    data = load_json(path)
    if data is None:
        _emit({"ok": False, "errors": [f"设计集清单不是有效 JSON: {MANIFEST_REL.as_posix()}"]})
        return 1
    files = data.get("files")
    if not isinstance(files, list):
        _emit({"ok": False, "errors": ["设计集清单缺少 files 数组"]})
        return 1
    missing: list[str] = []
    updated: list[str] = []
    for entry in files:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("path")
        fid = entry.get("id")
        if not isinstance(rel, str) or not isinstance(fid, str):
            continue
        resolved = design_path(root, rel)
        if not resolved.is_file():
            missing.append(f"{fid} ({rel})")
            continue
        digest = sha256_file(resolved)
        if entry.get("sha256") != digest:
            entry["sha256"] = digest
            updated.append(fid)
    rewrite_set_sha256(data)
    save_json(path, data)
    _emit({
        "ok": not missing,
        "updated": updated,
        "missing": missing,
        "set_sha256": data.get("set_sha256"),
    })
    return 0 if not missing else 1


# ── 依赖闭包 ────────────────────────────────────────────────


def closure_ids(data: dict[str, Any], targets: list[str]) -> tuple[list[str], list[str]]:
    """沿 depends_on 计算正向递归闭包。返回 (有序闭包 ID 列表, 未找到 ID 列表)。"""
    id_to_entry = {e["id"]: e for e in data.get("files", []) if isinstance(e, dict) and "id" in e}
    missing = [t for t in targets if t not in id_to_entry]
    ordered: list[str] = []
    seen: set[str] = set()

    def visit(fid: str) -> None:
        entry = id_to_entry.get(fid)
        if entry is None:
            return
        for dep in entry.get("depends_on", []):
            if dep not in seen:
                visit(dep)
        if fid not in seen:
            seen.add(fid)
            ordered.append(fid)

    for t in targets:
        visit(t)
    return ordered, missing


def closure_files(root: Path, data: dict[str, Any], ordered: list[str]) -> list[dict[str, Any]]:
    id_to_entry = {e["id"]: e for e in data.get("files", [])}
    out = []
    for fid in ordered:
        entry = id_to_entry[fid]
        path = design_path(root, entry["path"])
        out.append({
            "id": fid,
            "path": entry["path"],
            "type": entry["type"],
            "module": entry.get("module"),
            "sha256": entry.get("sha256"),
            "exists": path.is_file(),
        })
    return out


def cmd_closure(root: Path, args: argparse.Namespace) -> int:
    data, problems = load_manifest(root)
    if data is None:
        _emit({"ok": False, "errors": problems})
        return 1
    ordered, missing = closure_ids(data, args.targets)
    files = closure_files(root, data, ordered)
    _emit({
        "ok": not missing,
        "targets": args.targets,
        "closure_ids": ordered,
        "missing": missing,
        "files": files,
    })
    return 0 if not missing else 1


# ── 下游 Design 依据 ────────────────────────────────────────


def provenance_path(root: Path, artifact: str) -> Path:
    return root / (PRD_PROV_REL if artifact == "prd" else PROTO_PROV_REL)


def load_provenance(root: Path, artifact: str) -> dict[str, Any]:
    path = provenance_path(root, artifact)
    if not path.is_file():
        return {"schema_version": SCHEMA_INPUTS, "artifact": artifact, "targets": []}
    data = load_json(path)
    if data is None:
        raise RuntimeError(f"provenance 不是有效 JSON: {path}")
    return data


def _validate_provenance(data: dict[str, Any], artifact: str) -> list[str]:
    problems: list[str] = []
    if data.get("schema_version") != SCHEMA_INPUTS:
        problems.append(f"schema_version 必须为 {SCHEMA_INPUTS}")
    if data.get("artifact") != artifact:
        problems.append(f"artifact 必须为 {artifact}")
    targets = data.get("targets")
    if not isinstance(targets, list):
        problems.append("targets 必须是数组")
        return problems
    seen: set[str] = set()
    for i, t in enumerate(targets):
        if not isinstance(t, dict):
            problems.append(f"targets[{i}] 必须是对象")
            continue
        tid = t.get("target_id")
        if not isinstance(tid, str) or not tid:
            problems.append(f"targets[{i}].target_id 必须是非空字符串")
        elif tid in seen:
            problems.append(f"重复 target_id: {tid}")
        seen.add(tid)
        if t.get("status") not in VALID_TARGET_STATUS:
            problems.append(f"targets[{i}].status 只允许 {VALID_TARGET_STATUS}")
        if t.get("check_status") not in VALID_CHECK_STATUS:
            problems.append(f"targets[{i}].check_status 只允许 {VALID_CHECK_STATUS}")
        affected = t.get("affected_by")
        if not isinstance(affected, list) or not all(isinstance(a, str) and ID_RE.match(a) for a in affected):
            problems.append(f"targets[{i}].affected_by 必须是 Design ID 数组")
        inputs = t.get("design_inputs")
        if not isinstance(inputs, list):
            problems.append(f"targets[{i}].design_inputs 必须是数组")
        else:
            for j, inp in enumerate(inputs):
                if not isinstance(inp, dict) or not ID_RE.match(str(inp.get("id", ""))):
                    problems.append(f"targets[{i}].design_inputs[{j}].id 非法")
                if not isinstance(inp.get("sha256"), str) or len(inp.get("sha256", "")) != 64:
                    problems.append(f"targets[{i}].design_inputs[{j}].sha256 必须是 64 位十六进制")
    return problems


def downstream_output_exists(root: Path, artifact: str) -> bool:
    """按固定产物路径探测下游是否实际存在。"""
    if artifact == "prd":
        return (root / "output" / "prd" / "prd.md").is_file()
    if artifact == "prototype":
        proto = root / "output" / "prototype"
        return proto.is_dir() and (proto / "src").is_dir()
    return False


def cmd_check_inputs(root: Path, args: argparse.Namespace) -> int:
    data, problems = load_manifest(root)
    if data is None:
        _emit({"ok": False, "errors": problems})
        return 1
    artifact = args.artifact
    prov_path = provenance_path(root, artifact)
    prov_missing = not prov_path.is_file()
    prov = load_provenance(root, artifact)
    problems.extend(_validate_provenance(prov, artifact))
    id_to_entry = {e["id"]: e for e in data.get("files", [])}
    # 外部未知修改：清单登记指纹与实际文件不一致的文件 ID
    manifest_problems = check_manifest(root, data)
    fingerprint_mismatch = set()
    for msg in manifest_problems:
        if msg.startswith("文件指纹不一致"):
            rest = msg[len("文件指纹不一致: "):]
            fid = rest.split(" ", 1)[0]
            if ID_RE.match(fid):
                fingerprint_mismatch.add(fid)
        if msg.startswith("设计地图引用了未登记"):
            # 地图级变化会波及全部下游；交由 AI 按实际依赖处理
            pass
    results: list[dict[str, Any]] = []
    for t in prov.get("targets", []):
        if args.target and t.get("target_id") != args.target:
            continue
        status = t.get("status")
        stale = []
        actual_mismatch = []
        for inp in t.get("design_inputs", []):
            entry = id_to_entry.get(inp.get("id"))
            if entry is None:
                stale.append({"id": inp.get("id"), "reason": "not_in_manifest"})
            elif entry.get("sha256") != inp.get("sha256"):
                stale.append({"id": inp.get("id"), "reason": "fingerprint_mismatch"})
            if inp.get("id") in fingerprint_mismatch:
                actual_mismatch.append({"id": inp.get("id"), "reason": "file_changed_externally"})
        effective_status = status
        if effective_status == "current" and (stale or actual_mismatch):
            effective_status = "affected"
        results.append({
            "target_id": t.get("target_id"),
            "target_name": t.get("target_name"),
            "status": effective_status,
            "check_status": t.get("check_status"),
            "affected_by": t.get("affected_by"),
            "stale_inputs": stale,
            "actual_mismatch": actual_mismatch,
        })
    # 下游产物存在但 provenance 缺失：不得静默当作“无受影响下游”，报 incomplete
    if prov_missing and downstream_output_exists(root, artifact):
        results.append({
            "target_id": f"{artifact}:unknown",
            "target_name": None,
            "status": "incomplete",
            "check_status": "not_run",
            "affected_by": [],
            "stale_inputs": [],
            "actual_mismatch": [],
            "reason": "provenance_missing: 下游产物存在但无 Design 依据记录，请先执行 record-inputs",
        })
    _emit({"ok": True, "artifact": artifact, "targets": results})
    return 0


def cmd_record_inputs(root: Path, args: argparse.Namespace) -> int:
    """写入或更新某个下游模块的 Design 依据。

    --target-id / --target-name / --output-path / --output-locator 描述下游模块；
    --inputs 传入逗号分隔的 Design 文件 ID。同步完成后 status 固定为 current/check_status=passed 并清空 affected_by；事实与组织变化由 commit 侧的 --semantic 区分，本命令不做区分。
    """
    data, problems = load_manifest(root)
    if data is None:
        _emit({"ok": False, "errors": problems})
        return 1
    artifact = args.artifact
    prov = load_provenance(root, artifact)
    id_to_entry = {e["id"]: e for e in data.get("files", [])}
    input_ids = [i.strip() for i in (args.inputs or "").split(",") if i.strip()]
    missing = [i for i in input_ids if i not in id_to_entry]
    if missing:
        _emit({"ok": False, "errors": [f"design_inputs 引用不存在的文件 ID: {missing}"]})
        return 1
    inputs = [{"id": i, "sha256": id_to_entry[i]["sha256"]} for i in input_ids]
    targets = prov.get("targets", [])
    existing = next((t for t in targets if t.get("target_id") == args.target_id), None)
    if existing is None:
        targets.append({
            "target_id": args.target_id,
            "target_name": args.target_name,
            "output_path": args.output_path,
            "output_locator": args.output_locator,
            "status": "current",
            "check_status": "passed",
            "affected_by": [],
            "design_inputs": inputs,
        })
    else:
        existing["target_name"] = args.target_name
        existing["output_path"] = args.output_path
        existing["output_locator"] = args.output_locator
        existing["design_inputs"] = inputs
        existing["status"] = "current"
        existing["check_status"] = "passed"
        existing["affected_by"] = []
    prov["targets"] = targets
    save_json(provenance_path(root, artifact), prov)
    _emit({"ok": True, "artifact": artifact, "target_id": args.target_id, "design_inputs": inputs})
    return 0


# ── 事务通用逻辑 ────────────────────────────────────────────


def change_dir(root: Path, mode: str) -> Path:
    return root / (SINGLE_REL if mode == "single" else MULTI_REL)


def active_path(root: Path, mode: str) -> Path:
    return change_dir(root, mode) / "active.json"


def staged_dir(root: Path, mode: str) -> Path:
    return change_dir(root, mode) / "staged"


def backup_dir(root: Path, mode: str) -> Path:
    return change_dir(root, mode) / "backup"


def find_active(root: Path) -> tuple[str | None, dict[str, Any] | None]:
    """查找任一活动事务。返回 (mode, active)。"""
    for mode in ("single", "multi"):
        path = active_path(root, mode)
        if path.is_file():
            data = load_json(path)
            return mode, data
    return None, None


def _backup_stem(entry: dict[str, Any]) -> str:
    fid = entry.get("id", "")
    rel = entry.get("path", "")
    return f"{fid}__{rel.replace('/', '_')}"


def backup_artifacts(root: Path, mode: str, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """备份登记文件；返回 artifacts 登记（含 before_sha256）。"""
    bdir = backup_dir(root, mode)
    bdir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    manifest = manifest_path(root)
    for entry in entries:
        src = design_path(root, entry["path"])
        if src.is_file():
            shutil.copy2(src, bdir / _backup_stem(entry))
        artifacts.append({
            "role": "file",
            "path": entry["path"],
            "before_sha256": sha256_file(src) if src.is_file() else None,
            "staged_sha256": None,
        })
    return artifacts


def backup_artifact_file(root: Path, mode: str, role: str, rel: Path) -> dict[str, Any]:
    bdir = backup_dir(root, mode)
    bdir.mkdir(parents=True, exist_ok=True)
    src = root / rel
    if src.is_file():
        shutil.copy2(src, bdir / f"{role}__{rel.name}")
    return {
        "role": role,
        "path": rel.as_posix(),
        "before_sha256": sha256_file(src) if src.is_file() else None,
        "staged_sha256": None,
    }


def artifacts_for_change(root: Path, mode: str, changed_ids: list[str]) -> list[dict[str, Any]]:
    """登记本次修改实际影响的 artifacts：设计集清单 + 真实存在的 provenance。"""
    arts = [backup_artifact_file(root, mode, "manifest", MANIFEST_REL)]
    for artifact in ("prd", "prototype"):
        prov = provenance_path(root, artifact)
        if not prov.is_file():
            continue
        data = load_json(prov)
        if data is None:
            continue
        touched = any(
            changed in set(t.get("affected_by", []))
            or changed in {i.get("id") for i in t.get("design_inputs", [])}
            for changed in changed_ids
            for t in data.get("targets", [])
        )
        if touched:
            arts.append(backup_artifact_file(root, mode, f"{artifact}_provenance", prov))
    return arts


def write_active(root: Path, mode: str, active: dict[str, Any]) -> None:
    path = active_path(root, mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_json(path, active)


def _active_entries(active: dict[str, Any]) -> list[dict[str, Any]]:
    return [e for e in active.get("files", []) if isinstance(e, dict)]


def _active_artifacts(active: dict[str, Any]) -> list[dict[str, Any]]:
    return [e for e in active.get("artifacts", []) if isinstance(e, dict)]


def check_no_active(root: Path) -> None:
    mode, _ = find_active(root)
    if mode is not None:
        raise RuntimeError(f"存在活动事务（{mode}）。请先执行 recover 或完成当前事务。")


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


# ── 单文件快速路径 ──────────────────────────────────────────


def cmd_stage_single(root: Path, args: argparse.Namespace) -> int:
    check_no_active(root)
    data, problems = load_manifest(root)
    if data is None:
        _emit({"ok": False, "errors": problems})
        return 1
    entries = {e["id"]: e for e in data.get("files", [])}
    entry = entries.get(args.id)
    if entry is None:
        _emit({"ok": False, "errors": [f"文件 ID 不存在: {args.id}"]})
        return 1
    src = design_path(root, entry["path"])
    if not src.is_file():
        _emit({"ok": False, "errors": [f"目标文件不存在: {entry['path']}"]})
        return 1
    changed_ids = [args.id]
    artifacts = artifacts_for_change(root, "single", changed_ids)
    active = {
        "schema_version": SCHEMA_CHANGE,
        "mode": "single",
        "phase": "staging",
        "files": [{
            "id": args.id,
            "path": entry["path"],
            "before_sha256": sha256_file(src),
            "staged_sha256": None,
        }],
        "artifacts": artifacts,
    }
    write_active(root, "single", active)
    staged = staged_dir(root, "single")
    staged.mkdir(parents=True, exist_ok=True)
    _emit({
        "ok": True,
        "mode": "single",
        "phase": "staging",
        "file_id": args.id,
        "staged_path": (staged / _backup_stem(entry)).as_posix(),
        "backup_dir": backup_dir(root, "single").as_posix(),
    })
    return 0


def _candidate_manifest(root: Path, active: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """基于 staged 内容构造候选设计集清单。返回 (候选清单, 问题)。"""
    mode = active.get("mode", "multi")
    data, problems = load_manifest(root)
    if data is None:
        return None, problems
    sdir = staged_dir(root, mode)
    changed = {e["id"]: e for e in _active_entries(active)}
    for i, entry in enumerate(data.get("files", [])):
        fid = entry.get("id")
        if fid not in changed:
            continue
        cand = sdir / _backup_stem(changed[fid])
        if not cand.is_file():
            problems.append(f"staged 缺少候选内容: {fid} ({changed[fid]['path']})")
            continue
        entry["sha256"] = sha256_file(cand)
    if not problems:
        rewrite_set_sha256(data)
    return data, problems


def _staged_provenance_updates(root: Path, active: dict[str, Any],
                               semantic: str = "fact",
                               candidate_manifest: dict[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
    """对受影响的 provenance 生成候选内容。返回 {artifact: 候选数据}。

    semantic=organization（纯组织变化：文件移动/拆分/排版/措辞）时只更新指纹，
    下游保持 current；semantic=fact（事实变化）时标记 affected + not_run。
    candidate_manifest 提供变化后的新指纹（organization 分支使用）。
    """
    mode = active.get("mode", "multi")
    sdir = staged_dir(root, mode)
    changed_ids = [e["id"] for e in _active_entries(active)]
    out: dict[str, list[dict[str, Any]]] = {}
    for artifact in ("prd", "prototype"):
        prov_path = provenance_path(root, artifact)
        if not prov_path.is_file():
            continue
        data = load_json(prov_path)
        if data is None:
            continue
        touched = False
        for t in data.get("targets", []):
            inputs = t.get("design_inputs", [])
            overlap = [c for c in changed_ids if c in {i.get("id") for i in inputs}]
            if not overlap:
                continue
            touched = True
            if semantic == "organization":
                # 纯组织变化：只更新实际发生变化文件的指纹，下游保持 current
                id_to_entry = {e["id"]: e for e in (candidate_manifest or {}).get("files", [])}
                for inp in inputs:
                    entry = id_to_entry.get(inp.get("id"))
                    if entry is not None and entry.get("sha256"):
                        inp["sha256"] = entry["sha256"]
                t["affected_by"] = []
                t["status"] = "current"
                t["check_status"] = "passed"
            else:
                t["affected_by"] = list(dict.fromkeys(t.get("affected_by", []) + overlap))
                t["status"] = "affected"
                t["check_status"] = "not_run"
        if touched:
            out[artifact] = data
    return out


def _verify_staged(active: dict[str, Any], sdir: Path) -> list[str]:
    problems: list[str] = []
    for entry in _active_entries(active):
        cand = sdir / _backup_stem(entry)
        if not cand.is_file():
            problems.append(f"staged 缺少候选内容: {entry['id']} ({entry['path']})")
            continue
        entry["staged_sha256"] = sha256_file(cand)
    return problems


def _replace_files(root: Path, active: dict[str, Any]) -> None:
    mode = active.get("mode", "multi")
    sdir = staged_dir(root, mode)
    for entry in _active_entries(active):
        cand = sdir / _backup_stem(entry)
        dst = design_path(root, entry["path"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cand, dst)


def _replace_artifacts(root: Path, active: dict[str, Any]) -> None:
    mode = active.get("mode", "multi")
    sdir = staged_dir(root, mode)
    for art in _active_artifacts(active):
        role = art.get("role")
        if role == "manifest":
            cand = sdir / "candidate-manifest.json"
            if cand.is_file():
                shutil.copy2(cand, manifest_path(root))
        elif role in ("prd_provenance", "prototype_provenance"):
            artifact = "prd" if role == "prd_provenance" else "prototype"
            cand = sdir / f"candidate-{artifact}-provenance.json"
            if cand.is_file():
                shutil.copy2(cand, provenance_path(root, artifact))


def _cleanup(root: Path, mode: str) -> None:
    d = change_dir(root, mode)
    if d.exists():
        shutil.rmtree(d)


def cmd_commit_single(root: Path, args: argparse.Namespace) -> int:
    mode, active = find_active(root)
    if mode != "single" or active is None:
        _emit({"ok": False, "errors": ["没有活动的单文件事务。请先执行 stage-single。"]})
        return 1
    return _commit(root, active, args)


def cmd_commit(root: Path, args: argparse.Namespace) -> int:
    mode, active = find_active(root)
    if mode != "multi" or active is None:
        _emit({"ok": False, "errors": ["没有活动的多文件事务。请先执行 begin。"]})
        return 1
    return _commit(root, active, args)


def _commit(root: Path, active: dict[str, Any], args: argparse.Namespace) -> int:
    mode = active.get("mode", "multi")
    if active.get("phase") not in ("staging", "replacing", "verifying"):
        _emit({"ok": False, "errors": [f"未知事务阶段: {active.get('phase')}"]})
        return 1
    sdir = staged_dir(root, mode)
    problems = _verify_staged(active, sdir)
    if problems:
        _emit({"ok": False, "phase": active.get("phase"), "errors": problems})
        return 2
    cand_manifest, mproblems = _candidate_manifest(root, active)
    if mproblems:
        _emit({"ok": False, "errors": mproblems})
        return 2
    # 针对性检查：候选清单（用 staged 内容替换正式文件后校验）
    problems = check_manifest_against(root, active, cand_manifest)
    if problems:
        _emit({"ok": False, "errors": problems, "note": "检查失败，正式文件保持修改前状态"})
        return 2
    active["phase"] = "replacing"
    write_active(root, mode, active)
    # 准备候选 artifacts
    (sdir / "candidate-manifest.json").write_text(
        json.dumps(cand_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for artifact, data in _staged_provenance_updates(root, active, args.semantic, cand_manifest).items():
        (sdir / f"candidate-{artifact}-provenance.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _replace_files(root, active)
    _replace_artifacts(root, active)
    active["phase"] = "verifying"
    write_active(root, mode, active)
    data, problems = load_manifest(root)
    if data is not None:
        problems = check_manifest(root, data)
    if problems:
        _emit({"ok": False, "phase": "verifying", "errors": problems, "note": "验证失败，请执行 recover 恢复"})
        return 2
    _cleanup(root, mode)
    _emit({"ok": True, "mode": mode, "phase": "committed", "files": [e["id"] for e in _active_entries(active)]})
    return 0


def check_manifest_against(root: Path, active: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    """用候选清单校验（staged 已就位时，正式文件尚未替换，需要临时校验候选）。"""
    mode = active.get("mode", "multi")
    sdir = staged_dir(root, mode)
    changed = {e["id"]: e for e in _active_entries(active)}
    problems: list[str] = []
    # 指纹：候选清单里的 sha256 必须等于 staged 内容
    for entry in candidate.get("files", []):
        fid = entry.get("id")
        if fid in changed:
            cand = sdir / _backup_stem(changed[fid])
            if cand.is_file() and entry.get("sha256") != sha256_file(cand):
                problems.append(f"候选清单指纹与 staged 内容不一致: {fid}")
    # 结构与依赖校验（不重复计算 set_sha256，避免正式文件指纹干扰）
    ids = {e.get("id") for e in candidate.get("files", [])}
    for entry in candidate.get("files", []):
        for dep in entry.get("depends_on", []):
            if dep not in ids:
                problems.append(f"{entry.get('id')}.depends_on 引用不存在的 ID: {dep}")
    return problems


def cmd_begin(root: Path, args: argparse.Namespace) -> int:
    check_no_active(root)
    data, problems = load_manifest(root)
    if data is None:
        _emit({"ok": False, "errors": problems})
        return 1
    entries = {e["id"]: e for e in data.get("files", [])}
    missing = [i for i in args.ids if i not in entries]
    if missing:
        _emit({"ok": False, "errors": [f"文件 ID 不存在: {missing}"]})
        return 1
    targets = [entries[i] for i in args.ids]
    if len(targets) < 2:
        _emit({"ok": False, "errors": ["多文件事务 begin 至少需要两个目标文件。单文件请用 stage-single。"]})
        return 1
    artifacts = artifacts_for_change(root, "multi", args.ids)
    active = {
        "schema_version": SCHEMA_CHANGE,
        "mode": "multi",
        "phase": "staging",
        "files": [{
            "id": e["id"],
            "path": e["path"],
            "before_sha256": sha256_file(design_path(root, e["path"])),
            "staged_sha256": None,
        } for e in targets],
        "artifacts": artifacts,
    }
    write_active(root, "multi", active)
    sdir = staged_dir(root, "multi")
    sdir.mkdir(parents=True, exist_ok=True)
    _emit({
        "ok": True,
        "mode": "multi",
        "phase": "staging",
        "file_ids": args.ids,
        "staged_dir": sdir.as_posix(),
        "backup_dir": backup_dir(root, "multi").as_posix(),
    })
    return 0


def cmd_recover(root: Path, args: argparse.Namespace) -> int:
    mode, active = find_active(root)
    if active is None:
        _emit({"ok": False, "errors": ["没有活动事务可恢复"]})
        return 1
    bdir = backup_dir(root, mode)
    sdir = staged_dir(root, mode)
    entries = _active_entries(active)
    staged_complete = all((sdir / _backup_stem(e)).is_file() for e in entries)
    if staged_complete and active.get("phase") in ("replacing", "verifying"):
        # 完成已准备完整的新状态
        rc = _commit(root, active, argparse.Namespace(semantic="fact"))
        if rc == 0:
            _emit({"ok": True, "mode": mode, "recover": "completed_new_state"})
        return rc
    # 恢复旧完整状态
    for entry in entries:
        src = bdir / _backup_stem(entry)
        dst = design_path(root, entry["path"])
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif entry.get("before_sha256") is None and dst.exists():
            dst.unlink()
    for art in _active_artifacts(active):
        role = art.get("role")
        rel = Path(art.get("path", ""))
        src = bdir / f"{role}__{rel.name}"
        dst = root / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif art.get("before_sha256") is None and dst.exists():
            dst.unlink()
    _cleanup(root, mode)
    _emit({"ok": True, "mode": mode, "recover": "restored_old_state"})
    return 0


# ── CLI ─────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="design-set.py",
        description="ShitPM 设计集确定性工具：清单校验、依赖闭包、单文件/多文件事务、下游依据。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check", help="校验清单、路径、ID、依赖、地图引用和指纹")
    p.add_argument("--project-root", required=True)

    p = sub.add_parser("refresh", help="重算清单中全部文件指纹与 set_sha256 并写回")
    p.add_argument("--project-root", required=True)

    p = sub.add_parser("closure", help="根据目标文件 ID 沿 depends_on 输出递归依赖闭包")
    p.add_argument("--project-root", required=True)
    p.add_argument("--targets", nargs="+", required=True)

    p = sub.add_parser("stage-single", help="建立单文件轻量事务并返回临时写入路径")
    p.add_argument("--project-root", required=True)
    p.add_argument("--id", required=True)

    p = sub.add_parser("commit-single", help="检查并提交单文件、候选清单和实际受影响的 provenance")
    p.add_argument("--project-root", required=True)
    p.add_argument("--semantic", choices=["fact", "organization"], default="fact")

    p = sub.add_parser("begin", help="创建多文件 active.json、staged 和 backup")
    p.add_argument("--project-root", required=True)
    p.add_argument("--ids", nargs="+", required=True)

    p = sub.add_parser("commit", help="检查并提交多文件修改")
    p.add_argument("--project-root", required=True)
    p.add_argument("--semantic", choices=["fact", "organization"], default="fact")

    p = sub.add_parser("recover", help="从单文件或多文件中断状态恢复旧完整集合或完成新集合")
    p.add_argument("--project-root", required=True)

    p = sub.add_parser("record-inputs", help="写入 PRD / Prototype 模块依据")
    p.add_argument("--project-root", required=True)
    p.add_argument("--artifact", choices=["prd", "prototype"], required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--target-name", required=True)
    p.add_argument("--output-path", required=True)
    p.add_argument("--output-locator", required=True)
    p.add_argument("--inputs", required=True, help="逗号分隔的 Design 文件 ID")

    p = sub.add_parser("check-inputs", help="检查指定下游模块是否 current / affected / incomplete")
    p.add_argument("--project-root", required=True)
    p.add_argument("--artifact", choices=["prd", "prototype"], required=True)
    p.add_argument("--target", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = project_root_of(args.project_root)
    except SystemExit:
        return 1
    handlers = {
        "check": cmd_check,
        "refresh": cmd_refresh,
        "closure": cmd_closure,
        "stage-single": cmd_stage_single,
        "commit-single": cmd_commit_single,
        "begin": cmd_begin,
        "commit": cmd_commit,
        "recover": cmd_recover,
        "record-inputs": cmd_record_inputs,
        "check-inputs": cmd_check_inputs,
    }
    try:
        return handlers[args.command](root, args)
    except RuntimeError as exc:
        _emit({"ok": False, "errors": [str(exc)]})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())