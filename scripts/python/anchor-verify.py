#!/usr/bin/env python3
"""anchor-verify.py — 人读稿与机读镜像一致性校验

职责：比对 design.md/prd.md 正文与 .workflow/metadata/ JSON，报告不一致项。
不自动修复。exit code 0=一致 1=不一致。

校验顺序（规约 §11.3 S-11.5）：
1. 提取校验（文件存在、可解析）
2. envelope 校验（index.json 结构完整）
3. artifact 校验（人读稿路径正确）
4. entities 校验（实体 ID 唯一、属性完整）
5. relations 校验（关系两端实体存在）
6. profile 校验（符合 prd-writing.profile.json 约束，仅 prd 阶段）

用法：python anchor-verify.py --stage <stage> [--project-root <path>]
"""

import argparse
import json
import re
import sys
from pathlib import Path

VALID_STAGES = ["design", "prd", "prototype"]

ARTIFACT_PATHS = {
    "design": "output/design/design.md",
    "prd": "output/prd/prd.md",
    "prototype": "output/prototype/index.html",
}

METADATA_FILE_MAP = {
    "design": ["index.json", "entities.json", "relations.json", "modules.json", "pages.json", "fields.json", "rules.json", "states.json", "permissions.json"],
    "prd": ["index.json", "entities.json", "relations.json", "page-anchor.json", "rule-anchor.json", "field-anchor.json"],
    "prototype": ["index.json", "page-map.json"],
}

STABLE_ID_PATTERN = re.compile(r'^(MODULE|PAGE|FIELD|RULE|FLOW|REL|PERM|STATE|ROLE|REQ|RISK|CASE|WVR)-(design|prd)-\d{3}$')


class VerifyResult:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, step, message):
        self.errors.append({"step": step, "message": message})

    def warn(self, step, message):
        self.warnings.append({"step": step, "message": message})

    @property
    def consistent(self):
        return len(self.errors) == 0


def step1_extraction(project_root: Path, stage: str, result: VerifyResult):
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    if not metadata_dir.exists():
        result.error("extraction", f".workflow/metadata/{stage}/ 目录不存在")
        return None

    loaded = {}
    for fname in METADATA_FILE_MAP.get(stage, []):
        fpath = metadata_dir / fname
        if not fpath.exists():
            result.error("extraction", f".workflow/metadata/{stage}/{fname} 不存在")
            continue
        try:
            with open(fpath, encoding="utf-8") as f:
                loaded[fname] = json.load(f)
        except json.JSONDecodeError as e:
            result.error("extraction", f".workflow/metadata/{stage}/{fname} JSON 解析失败: {e}")

    artifact_path = project_root / ARTIFACT_PATHS[stage]
    if not artifact_path.exists():
        result.error("extraction", f"{ARTIFACT_PATHS[stage]} 不存在")
    else:
        try:
            with open(artifact_path, encoding="utf-8") as f:
                loaded["_artifact_content"] = f.read()
        except OSError as e:
            result.error("extraction", f"读取 {ARTIFACT_PATHS[stage]} 失败: {e}")

    return loaded


def step2_envelope(loaded: dict, stage: str, result: VerifyResult):
    index = loaded.get("index.json")
    if index is None:
        result.error("envelope", "index.json 未加载，跳过 envelope 校验")
        return
    if not isinstance(index, dict):
        result.error("envelope", "index.json 不是 JSON 对象")
        return

    required_keys = ["schema_version", "artifact_path", "stage"]
    for key in required_keys:
        if key not in index:
            result.error("envelope", f"index.json 缺少必要字段: {key}")

    if "stage" in index and index["stage"] != stage:
        result.error("envelope", f"index.json stage={index['stage']}，期望 {stage}")


def step3_artifact(loaded: dict, stage: str, result: VerifyResult):
    index = loaded.get("index.json")
    if not isinstance(index, dict):
        return
    artifact_in_index = index.get("artifact_path", "")
    expected = ARTIFACT_PATHS.get(stage, "")
    if artifact_in_index and artifact_in_index != expected:
        result.error("artifact", f"index.json artifact_path={artifact_in_index}，期望 {expected}")


def step4_entities(loaded: dict, stage: str, result: VerifyResult):
    entities = loaded.get("entities.json")
    if entities is None:
        result.warn("entities", "entities.json 未加载，跳过实体校验")
        return
    if not isinstance(entities, list):
        result.error("entities", "entities.json 不是数组")
        return

    seen_ids = {}
    for i, entity in enumerate(entities):
        if not isinstance(entity, dict):
            result.error("entities", f"entities[{i}] 不是对象")
            continue
        eid = entity.get("id", "")
        if not eid:
            result.error("entities", f"entities[{i}] 缺少 id 字段")
            continue
        if eid in seen_ids:
            result.error("entities", f"实体 ID 重复: {eid}（出现在 entities[{seen_ids[eid]}] 和 entities[{i}]）")
        else:
            seen_ids[eid] = i

        if not STABLE_ID_PATTERN.match(eid):
            result.warn("entities", f"实体 ID 格式不规范: {eid}")

        if "title" not in entity:
            result.warn("entities", f"实体 {eid} 缺少 title 字段")


def step5_relations(loaded: dict, stage: str, result: VerifyResult):
    relations = loaded.get("relations.json")
    if relations is None:
        result.warn("relations", "relations.json 未加载，跳过关系校验")
        return
    if not isinstance(relations, list):
        result.error("relations", "relations.json 不是数组")
        return

    entities = loaded.get("entities.json", [])
    entity_ids = set()
    if isinstance(entities, list):
        for e in entities:
            if isinstance(e, dict) and "id" in e:
                entity_ids.add(e["id"])

    for i, rel in enumerate(relations):
        if not isinstance(rel, dict):
            result.error("relations", f"relations[{i}] 不是对象")
            continue
        from_id = rel.get("from", "")
        to_id = rel.get("to", "")
        if from_id and from_id not in entity_ids:
            result.error("relations", f"relations[{i}] from={from_id} 不在 entities 中")
        if to_id and to_id not in entity_ids:
            result.error("relations", f"relations[{i}] to={to_id} 不在 entities 中")


def step6_profile(loaded: dict, stage: str, project_root: Path, result: VerifyResult):
    if stage != "prd":
        return

    profile_path = project_root / "references" / "prd-writing.profile.json"
    if not profile_path.exists():
        result.warn("profile", "references/prd-writing.profile.json 不存在，跳过 profile 校验")
        return

    try:
        with open(profile_path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError:
        result.error("profile", "references/prd-writing.profile.json JSON 解析失败")
        return

    artifact_content = loaded.get("_artifact_content", "")
    if not artifact_content:
        result.warn("profile", "人读稿未加载，跳过 profile 校验")
        return

    constraints = profile.get("constraints", {})
    required_sections = constraints.get("required_sections", [])
    for section in required_sections:
        if section not in artifact_content:
            result.error("profile", f"PRD 缺少必要章节: {section}")

    forbidden = constraints.get("forbidden_expressions", [])
    for expr in forbidden:
        if expr in artifact_content:
            result.warn("profile", f"PRD 包含禁止表达: {expr}")


def main():
    parser = argparse.ArgumentParser(description="人读稿与机读镜像一致性校验")
    parser.add_argument("--stage", required=True, choices=VALID_STAGES, help="校验阶段")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="项目根目录")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    stage = args.stage
    result = VerifyResult()

    loaded = step1_extraction(project_root, stage, result)
    if loaded is not None:
        step2_envelope(loaded, stage, result)
        step3_artifact(loaded, stage, result)
        step4_entities(loaded, stage, result)
        step5_relations(loaded, stage, result)
        step6_profile(loaded, stage, project_root, result)

    output = {
        "stage": stage,
        "consistent": result.consistent,
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "errors": result.errors,
        "warnings": result.warnings,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0 if result.consistent else 1)


if __name__ == "__main__":
    main()
