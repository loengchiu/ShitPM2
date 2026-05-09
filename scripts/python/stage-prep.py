#!/usr/bin/env python3
"""stage-prep.py — 机读镜像生成脚本

职责：从当前人读稿中抽取并生成 metadata anchor。
不判断是否允许进入该阶段，不修改人读稿正文。

用法：python stage-prep.py --stage <stage> [--project-root <path>] [--dry-run]
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_STAGES = ["align", "design", "prd", "prototype"]

# 稳定 ID 前缀映射（规约 §3.6 只允许 6 种前缀）
ID_PREFIXES = {
    "module": "MODULE",
    "page": "PAGE",
    "field": "FIELD",
    "rule": "RULE",
    "flow": "FLOW",
}

# 中文关键词到实体类型的映射
# 只映射能生成稳定 ID 的实体类型
# 角色、状态、权限在 design 中有结构意义但不生成独立稳定 ID
HEADING_ENTITY_MAP = {
    "模块": "module",
    "页面": "page",
    "字段": "field",
    "规则": "rule",
    "流程": "flow",
}

# 每个阶段允许生成的实体类型
STAGE_ALLOWED_ENTITIES = {
    "align": set(),  # align 不生成稳定 ID
    "design": {"module", "page", "field", "rule", "flow"},
    "prd": set(),  # prd 不新增实体，只引用 design
    "prototype": set(),
}

# 章节级标题模式（不应被识别为实体条目）
# 匹配 "## 一、角色定义"、"## 三、模块定义" 等纯章节标记
CHAPTER_HEADING_PATTERN = re.compile(r'^[一二三四五六七八九十]+[、．.]')

# Metadata 文件映射
METADATA_FILE_MAP = {
    "align": ["index.json", "entities.json", "relations.json"],
    "design": ["index.json", "entities.json", "relations.json", "modules.json", "pages.json", "fields.json", "rules.json", "states.json", "permissions.json"],
    "prd": ["index.json", "entities.json", "relations.json", "page-anchor.json", "rule-anchor.json", "field-anchor.json"],
    "prototype": ["index.json", "page-map.json"],
}

ARTIFACT_PATHS = {
    "align": "output/align/align.md",
    "design": "output/design/design.md",
    "prd": "output/prd/prd.md",
    "prototype": "output/prototype/index.html",
}


def slug_from_heading(heading: str) -> str:
    """从标题生成稳定 slug（MD5 前 8 位 + 标题前 12 字符）"""
    clean = re.sub(r'[#\*\[\]()（）]', '', heading).strip()
    md5_prefix = hashlib.md5(clean.encode()).hexdigest()[:8]
    title_prefix = re.sub(r'[^a-zA-Z0-9一-鿿]', '', clean)[:12]
    return f"{md5_prefix}-{title_prefix}"


def parse_headings(content: str) -> list:
    """解析 Markdown 标题结构"""
    headings = []
    for i, line in enumerate(content.split('\n')):
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append({
                "level": level,
                "title": title,
                "line": i + 1,
            })
    return headings


def read_existing_max_ids(stage: str, project_root: Path) -> dict:
    """从已有 metadata 中读取每种前缀的最大 ID 编号"""
    max_ids = {}
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    if not metadata_dir.exists():
        return max_ids

    # 扫描所有 JSON 文件中的 ID
    id_pattern = re.compile(r'^(MODULE|PAGE|FIELD|RULE|FLOW)-' + re.escape(stage) + r'-(\d{3})$')
    for json_file in metadata_dir.glob("*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            # 递归搜索所有字符串值中的 ID
            _scan_ids_recursive(data, id_pattern, max_ids)
        except (json.JSONDecodeError, OSError):
            continue
    return max_ids


def _scan_ids_recursive(obj, pattern, max_ids: dict):
    """递归扫描 JSON 对象中的稳定 ID"""
    if isinstance(obj, str):
        match = pattern.match(obj)
        if match:
            prefix = match.group(1)
            num = int(match.group(2))
            max_ids[prefix] = max(max_ids.get(prefix, 0), num)
    elif isinstance(obj, dict):
        for v in obj.values():
            _scan_ids_recursive(v, pattern, max_ids)
    elif isinstance(obj, list):
        for item in obj:
            _scan_ids_recursive(item, pattern, max_ids)


def infer_entities_from_headings(headings: list, stage: str, project_root: Path = None) -> list:
    """从标题结构推断实体

    区分章节标题和实体条目：
    - ## 一、模块定义 → 章节标题，跳过
    - ### 入库管理模块 → 实体条目，识别为 module
    - #### 1. 入库记录列表 → 实体条目，识别为 page

    ID 持久化：先读取已有 metadata 中的最大编号，从 max+1 继续。
    """
    entities = []
    allowed = STAGE_ALLOWED_ENTITIES.get(stage, set())

    # 读取已有最大 ID，保证多次运行不覆盖
    counter = {}
    if project_root:
        counter = read_existing_max_ids(stage, project_root)

    for h in headings:
        title = h["title"]

        # 跳过顶级章节标题（## 一、角色定义 等）
        if h["level"] <= 2:
            continue

        # 跳过纯章节编号标题（如 "一、角色定义"、"（一）入库管理"）
        if CHAPTER_HEADING_PATTERN.match(title):
            continue

        entity_type = None
        for keyword, etype in HEADING_ENTITY_MAP.items():
            if keyword in title:
                entity_type = etype
                break

        if entity_type and entity_type in allowed:
            prefix = ID_PREFIXES[entity_type]
            count = counter.get(prefix, 0) + 1
            counter[prefix] = count
            entity_id = f"{prefix}-{stage}-{count:03d}"
            entities.append({
                "id": entity_id,
                "type": entity_type,
                "title": title,
                "line": h["line"],
            })

    return entities


def infer_relations_from_content(content: str, entities: list, stage: str) -> list:
    """从内容推断实体间关系"""
    relations = []
    rel_counter = 1

    source_keywords = ["来源", "依据", "基于", "引用", "对齐"]
    contain_keywords = ["包含", "含", "下属"]

    sections = re.split(r'\n#{1,6}\s+', content)

    entity_ids = {e["id"]: e for e in entities}
    if not entity_ids:
        return relations

    id_pattern = "|".join(re.escape(eid) for eid in entity_ids.keys())

    for section in sections:
        found_ids = re.findall(id_pattern, section)
        if len(found_ids) >= 2:
            has_source = any(kw in section for kw in source_keywords)
            has_contain = any(kw in section for kw in contain_keywords)

            rel_type = "derived_from" if has_source else ("contains" if has_contain else "refines")

            for i in range(len(found_ids) - 1):
                relations.append({
                    "id": f"REL-{stage}-{rel_counter:03d}",
                    "type": rel_type,
                    "from": found_ids[i],
                    "to": found_ids[i + 1],
                })
                rel_counter += 1

    return relations


def generate_align_metadata(content: str, project_root: Path) -> dict:
    """生成 align 阶段 metadata（不含稳定 ID）"""
    index = {
        "schema_version": "1.0.0",
        "stage": "align",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "request_summary": "",
        "solution_shape": "",
        "business_stage": "",
        "context_gaps": [],
    }

    entities = {
        "system_or_page_clues": [],
        "material_paths": [],
        "confirmed_roles": [],
        "confirmed_scenes": [],
        "confirmed_objects": [],
    }

    relations = []

    return {
        "index": index,
        "entities": entities,
        "relations": relations,
    }


def generate_design_metadata(content: str, stage: str, project_root: Path) -> dict:
    """生成 design 阶段 metadata（含稳定 ID）"""
    headings = parse_headings(content)
    entities = infer_entities_from_headings(headings, stage, project_root)
    relations = infer_relations_from_content(content, entities, stage)

    index = {
        "schema_version": "1.0.0",
        "stage": stage,
        "artifact_path": f"output/{stage}/{stage}.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_count": len(entities),
        "relation_count": len(relations),
    }

    # 按类型分组
    modules = [e for e in entities if e["type"] == "module"]
    pages = [e for e in entities if e["type"] == "page"]
    fields = [e for e in entities if e["type"] == "field"]
    rules = [e for e in entities if e["type"] == "rule"]

    # 状态和权限不含稳定 ID，从标题轻量抽取
    states = []
    permissions = []
    for h in headings:
        if h["level"] >= 3 and "状态" in h["title"] and "定义" in h["title"]:
            states.append({"title": h["title"], "line": h["line"]})
        if h["level"] >= 3 and "权限" in h["title"]:
            permissions.append({"title": h["title"], "line": h["line"]})

    return {
        "index": index,
        "entities": entities,
        "relations": relations,
        "modules": modules,
        "pages": pages,
        "fields": fields,
        "rules": rules,
        "states": states,
        "permissions": permissions,
    }


def generate_prd_metadata(content: str, project_root: Path) -> dict:
    """生成 PRD 阶段 metadata（不含新稳定 ID，只引用 design）"""
    headings = parse_headings(content)

    index = {
        "schema_version": "1.0.0",
        "stage": "prd",
        "artifact_path": "output/prd/prd.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    page_anchor = []
    rule_anchor = []
    field_anchor = []

    for h in headings:
        if "页面" in h["title"] or "详细需求" in h["title"]:
            page_anchor.append({
                "title": h["title"],
                "line": h["line"],
            })

    return {
        "index": index,
        "entities": [],
        "relations": [],
        "page_anchor": page_anchor,
        "rule_anchor": rule_anchor,
        "field_anchor": field_anchor,
    }


def generate_prototype_metadata(project_root: Path) -> dict:
    """生成 prototype 阶段 metadata"""
    return {
        "schema_version": "1.0.0",
        "stage": "prototype",
        "artifact_path": "output/prototype/index.html",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "page_map": [],
    }


def write_metadata(stage: str, data: dict, project_root: Path, dry_run: bool = False) -> list:
    """将 metadata 写入文件"""
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    if not dry_run:
        metadata_dir.mkdir(parents=True, exist_ok=True)

    files = METADATA_FILE_MAP.get(stage, [])

    key_file_map = {
        "index": "index.json",
        "entities": "entities.json",
        "relations": "relations.json",
        "modules": "modules.json",
        "pages": "pages.json",
        "fields": "fields.json",
        "rules": "rules.json",
        "states": "states.json",
        "permissions": "permissions.json",
        "page_anchor": "page-anchor.json",
        "rule_anchor": "rule-anchor.json",
        "field_anchor": "field-anchor.json",
        "page_map": "page-map.json",
    }

    written = []
    for key, filename in key_file_map.items():
        if key in data and filename in files:
            target = metadata_dir / filename
            content = json.dumps(data[key], ensure_ascii=False, indent=2)
            if not dry_run:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
            written.append(str(target))

    return written


def write_align_notes(project_root: Path, dry_run: bool = False) -> str:
    """写入 align-notes.json 默认值（AI skill 层会更新实际判断结论）"""
    notes_dir = project_root / ".workflow" / "runtime" / "align"
    if not dry_run:
        notes_dir.mkdir(parents=True, exist_ok=True)

    notes = {
        "blocking_gaps": [],
        "needs_ask_back": False,
        "ask_back_reason": None,
        "can_enter_design": False,
        "judgement_note": "由 stage-prep.py 生成的默认值，需 AI skill 层更新实际判断结论",
        "last_updated_at": datetime.now(timezone.utc).isoformat(),
    }

    target = notes_dir / "align-notes.json"
    if not dry_run:
        with open(target, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)

    return str(target)


def write_stage_context(stage: str, data: dict, project_root: Path, dry_run: bool = False) -> str:
    """写入 stage-context.json"""
    ctx_dir = project_root / ".workflow" / "runtime" / stage
    if not dry_run:
        ctx_dir.mkdir(parents=True, exist_ok=True)

    entities = data.get("entities", [])
    relations = data.get("relations", [])

    ctx = {
        "stage": stage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_count": len(entities) if isinstance(entities, list) else 0,
        "relation_count": len(relations) if isinstance(relations, list) else 0,
        "metadata_files": METADATA_FILE_MAP.get(stage, []),
    }

    target = ctx_dir / "stage-context.json"
    if not dry_run:
        with open(target, "w", encoding="utf-8") as f:
            json.dump(ctx, f, ensure_ascii=False, indent=2)

    return str(target)


def main():
    parser = argparse.ArgumentParser(description="机读镜像生成脚本")
    parser.add_argument("--stage", required=True, choices=VALID_STAGES, help="目标阶段")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不写入文件")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    stage = args.stage

    # 读取人读产物
    artifact_path = project_root / ARTIFACT_PATHS[stage]
    if not artifact_path.exists():
        print(f"错误: 人读产物不存在: {artifact_path}", file=sys.stderr)
        sys.exit(1)

    with open(artifact_path, encoding="utf-8") as f:
        content = f.read()

    # 根据阶段生成 metadata
    if stage == "align":
        data = generate_align_metadata(content, project_root)
    elif stage == "design":
        data = generate_design_metadata(content, stage, project_root)
    elif stage == "prd":
        data = generate_prd_metadata(content, project_root)
    elif stage == "prototype":
        data = generate_prototype_metadata(project_root)
    else:
        print(f"错误: 不支持的阶段: {stage}", file=sys.stderr)
        sys.exit(1)

    # 写入文件
    written_files = write_metadata(stage, data, project_root, dry_run=args.dry_run)
    ctx_file = write_stage_context(stage, data, project_root, dry_run=args.dry_run)

    # align 阶段额外写入 align-notes.json
    align_notes_file = None
    if stage == "align":
        align_notes_file = write_align_notes(project_root, dry_run=args.dry_run)

    entities = data.get("entities", [])
    relations = data.get("relations", [])

    result = {
        "stage": stage,
        "dry_run": args.dry_run,
        "metadata_files_written": written_files,
        "stage_context_file": ctx_file,
        "entity_count": len(entities) if isinstance(entities, list) else 0,
        "relation_count": len(relations) if isinstance(relations, list) else 0,
    }
    if align_notes_file:
        result["align_notes_file"] = align_notes_file

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
