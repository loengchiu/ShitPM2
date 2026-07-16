#!/usr/bin/env python3
"""verify-against-metadata.py -- metadata 结构完整性校验

只做 schema 校验和 ID 唯一性校验，不做语义检测（幻觉/一致性交给 review skill 的 LLM 逐项 checklist）。

用法:
  python verify-against-metadata.py --stage <stage> --project-root .
"""

import argparse
import json
import sys
from pathlib import Path

from shared_md import load_json

# ── jsonschema 真校验（依赖缺失则降级跳过） ──────────────────
try:
    import jsonschema
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT7
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"
_REGISTRY = None
if _HAS_JSONSCHEMA:
    _registry = Registry()
    for _res_name in ["common.schema.json", "align-notes.schema.json"]:
        _res = load_json(_SCHEMA_DIR / _res_name)
        if _res:
            _registry = _registry.with_resource(
                _res_name,
                Resource.from_contents(_res, default_specification=DRAFT7),
            )
    _REGISTRY = _registry


def verify_schema(data, schema_key) -> tuple:
    """用 jsonschema 校验 data，返回 (errors, schema_validation_skipped)

    schema_key 取值：design/status/review
    返回 (errors_list, skipped_bool)。skipped=True 表示因依赖缺失跳过了 schema 校验。
    """
    if not _HAS_JSONSCHEMA or _REGISTRY is None:
        return [], True
    schema_map = {
        "design": "design-metadata",
        "status": "status",
        "review": "review-result",
    }
    schema_name = schema_map.get(schema_key)
    if not schema_name:
        return [], False
    schema = load_json(_SCHEMA_DIR / f"{schema_name}.schema.json")
    if not schema:
        return [], False
    try:
        validator = jsonschema.Draft7Validator(schema, registry=_REGISTRY)
        return [f"schema 校验失败: {e.message} (at {list(e.absolute_path)})"
                for e in validator.iter_errors(data)], False
    except Exception as e:
        return [f"schema 校验异常（已降级）: {e}"], False


# ── Metadata 结构完整性校验 ─────────────────────────────────

def verify_metadata_integrity(project_root, stage):
    """校验 metadata JSON 结构完整性，返回 errors 列表"""
    errors = []
    meta_dir = project_root / ".workflow" / "metadata" / stage
    if not meta_dir.exists():
        errors.append(f".workflow/metadata/{stage}/ 不存在")
        return errors

    index = load_json(meta_dir / "index.json")
    if not index or not isinstance(index, dict):
        errors.append("index.json 缺失或非 JSON 对象")
    else:
        for key in ["schema_version", "artifact_path", "stage"]:
            if key not in index:
                errors.append(f"index.json 缺少 {key}")
        if index.get("stage") != stage:
            errors.append(f"index.json stage={index.get('stage')}，期望 {stage}")
        # jsonschema 真校验（依赖缺失自动降级）
        schema_errs, schema_skipped = verify_schema(index, stage)
        errors.extend(schema_errs)
        if schema_skipped:
            errors.append("schema 校验已跳过（jsonschema 依赖缺失）")

    # 实体 ID 唯一性（含 states/permissions，这两类也有稳定 ID）
    entity_files = {
        "design": ["modules.json", "pages.json", "fields.json", "rules.json", "states.json", "permissions.json"],
        "prd": ["relations.json"],
        "prototype": [],
    }
    seen_ids = set()
    for fname in entity_files.get(stage, []):
        data = load_json(meta_dir / fname)
        if not data or not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            eid = item.get("id", "")
            if not eid:
                errors.append(f"{fname}: 实体缺少 id")
            elif eid in seen_ids:
                errors.append(f"{fname}: 重复 ID {eid}")
            else:
                seen_ids.add(eid)

    return errors


# ── status / review 校验 ────────────────────────────────────

def verify_status(project_root) -> list:
    """校验 .workflow/status.json 的结构完整性"""
    errors = []
    status_path = project_root / ".workflow" / "status.json"
    if not status_path.exists():
        return [".workflow/status.json 不存在"]

    status = load_json(status_path)
    if not status or not isinstance(status, dict):
        return [".workflow/status.json 缺失或非 JSON 对象"]

    schema_errs, schema_skipped = verify_schema(status, "status")
    errors.extend(schema_errs)
    if schema_skipped:
        errors.append("schema 校验已跳过（jsonschema 依赖缺失）")
    return errors


def verify_reviews(project_root) -> list:
    """校验 .workflow/reviews/ 下所有 review JSON 的结构完整性"""
    errors = []
    reviews_dir = project_root / ".workflow" / "reviews"
    if not reviews_dir.exists():
        return [".workflow/reviews/ 目录不存在"]

    review_files = sorted(reviews_dir.glob("*.json"))
    if not review_files:
        return [".workflow/reviews/ 无 review JSON 文件"]

    for review_file in review_files:
        review = load_json(review_file)
        if not review or not isinstance(review, dict):
            errors.append(f"{review_file.name}: 缺失或非 JSON 对象")
            continue
        file_errs, _ = verify_schema(review, "review")
        errors.extend(f"{review_file.name}: {e}" for e in file_errs)

    return errors


# ── 主入口 ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="metadata 结构完整性校验")
    parser.add_argument("--stage", required=True, choices=["design", "status", "review"])
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project_root = args.project_root.resolve()

    if args.stage == "status":
        integrity_errors = verify_status(project_root)
    elif args.stage == "review":
        integrity_errors = verify_reviews(project_root)
    else:
        integrity_errors = verify_metadata_integrity(project_root, args.stage)

    result = {
        "stage": args.stage,
        "integrity_errors": integrity_errors,
        "summary": "结构完整性校验通过" if not integrity_errors
                   else f"{len(integrity_errors)} 个结构完整性问题",
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if integrity_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
