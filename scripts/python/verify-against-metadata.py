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

from shared_md import load_json, METADATA_FILE_MAP

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
    _common = load_json(_SCHEMA_DIR / "common.schema.json")
    if _common:
        _REGISTRY = Registry().with_resource(
            "common.schema.json",
            Resource.from_contents(_common, default_specification=DRAFT7),
        )


def verify_schema(data, stage) -> list:
    """用 jsonschema 校验 metadata index.json，返回错误消息列表；依赖缺失返回空"""
    if not _HAS_JSONSCHEMA or _REGISTRY is None:
        return []
    schema_map = {"design": "design-metadata", "prd": "prd-metadata", "prototype": "prototype-metadata"}
    schema_name = schema_map.get(stage)
    if not schema_name:
        return []
    schema = load_json(_SCHEMA_DIR / f"{schema_name}.schema.json")
    if not schema:
        return []
    try:
        validator = jsonschema.Draft7Validator(schema, registry=_REGISTRY)
        return [f"schema 校验失败: {e.message} (at {list(e.absolute_path)})"
                for e in validator.iter_errors(data)]
    except Exception as e:
        return [f"schema 校验异常（已降级）: {e}"]


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
        errors.extend(verify_schema(index, stage))

    # 实体 ID 唯一性（含 states/permissions，这两类也有稳定 ID）
    entity_files = {"design": ["modules.json", "pages.json", "fields.json", "rules.json", "states.json", "permissions.json"],
                    "prd": [], "prototype": []}
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


# ── 主入口 ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="metadata 结构完整性校验")
    parser.add_argument("--stage", required=True, choices=["design", "prd", "prototype"])
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project_root = args.project_root.resolve()

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
