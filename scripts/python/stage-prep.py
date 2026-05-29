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
    "permission": "PERM",
    "state": "STATE",
    "role": "ROLE",
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
    "design": ["index.json", "entities.json", "relations.json", "modules.json", "pages.json", "fields.json", "rules.json", "states.json", "permissions.json", "page-fields.json", "non-page-fields.json", "field-constraints.json"],
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


def read_existing_entities(stage: str, project_root: Path) -> tuple:
    """从已有 metadata 中读取已有实体的 {title: id} 映射和每种前缀的最大 ID 编号

    返回 (title_to_id, max_ids)
    - title_to_id: {entity_title: entity_id} 用于按标题匹配已有 ID
    - max_ids: {prefix: max_number} 用于为新实体分配 ID
    """
    title_to_id = {}
    max_ids = {}
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    if not metadata_dir.exists():
        return title_to_id, max_ids

    id_pattern = re.compile(r'^(MODULE|PAGE|FIELD|RULE|FLOW|PERM|STATE|ROLE)-' + re.escape(stage) + r'-(\d{3})$')
    for json_file in metadata_dir.glob("*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "id" in item and "title" in item:
                        title_to_id[item["title"]] = item["id"]
            _scan_ids_recursive(data, id_pattern, max_ids)
        except (json.JSONDecodeError, OSError):
            continue
    return title_to_id, max_ids


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


def infer_entities_from_headings(headings: list, stage: str, project_root: Path = None, title_to_id: dict = None, counter: dict = None) -> list:
    """从标题结构推断实体

    区分章节标题和实体条目：
    - ## 一、模块定义 → 章节标题，跳过
    - ### 入库管理模块 → 实体条目，识别为 module

    ID 策略：优先按标题匹配已有 ID，无匹配时从 max+1 分配新 ID。
    """
    entities = []
    allowed = STAGE_ALLOWED_ENTITIES.get(stage, set())
    if title_to_id is None:
        title_to_id = {}
    if counter is None:
        counter = {}

    for h in headings:
        title = h["title"]

        # 跳过顶级章节标题（## 一、角色定义 等）
        if h["level"] <= 2:
            continue

        # 跳过纯章节编号标题（如 "一、角色定义"、"（一）入库管理"）
        if CHAPTER_HEADING_PATTERN.match(title):
            continue
        if "非页面落点字段" in title:
            continue

        entity_type = None
        for keyword, etype in HEADING_ENTITY_MAP.items():
            if keyword in title:
                entity_type = etype
                break

        if entity_type and entity_type in allowed:
            # 优先匹配已有 ID
            if title in title_to_id:
                entity_id = title_to_id[title]
            else:
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


def parse_tables_with_context(content: str, headings: list) -> list:
    """解析 Markdown 表格并关联到所在章节

    返回 [{section_title, section_line, headers, rows, line_offset}, ...]
    """
    lines = content.split('\n')
    tables = []
    current_section = ""
    current_section_line = 1

    # 建立行号到章节的映射
    heading_map = {}  # line_number -> heading_title
    for h in headings:
        heading_map[h["line"]] = h["title"]

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 更新当前章节
        if i + 1 in heading_map:
            current_section = heading_map[i + 1]
            current_section_line = i + 1

        # 检测表格开始（包含 | 的行，下一行是分隔行 |---|）
        if line.startswith('|') and '|' in line[1:] and i + 1 < len(lines):
            sep_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if re.match(r'^\|[\s\-:|]+\|$', sep_line):
                # 这是一个表格
                headers = [h.strip() for h in line.split('|')[1:-1]]
                rows = []
                j = i + 2  # 跳过表头和分隔行
                while j < len(lines) and lines[j].strip().startswith('|'):
                    row_text = lines[j].strip()
                    cells = [c.strip() for c in row_text.split('|')[1:-1]]
                    rows.append(cells)
                    j += 1
                tables.append({
                    "section_title": current_section,
                    "section_line": current_section_line,
                    "headers": headers,
                    "rows": rows,
                    "line_offset": i + 1,
                })
                i = j
                continue
        i += 1

    return tables


def _build_field_attributes(row: list, headers: list) -> dict:
    """根据列数适配 5 列或 9 列字段格式

    5 列格式（当前设计稿）：字段 | 类型 | 必填 | 枚举值 / 规则 | 说明
    9 列格式（原模板）：字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明
    """
    if len(headers) >= 7:
        # 9 列格式
        return {
            "数据类型": row[1] if len(row) > 1 else None,
            "长度": row[2] if len(row) > 2 else None,
            "必填": row[3] == "是" if len(row) > 3 else None,
            "默认值": row[4] if len(row) > 4 else None,
            "枚举值": row[5] if len(row) > 5 else None,
            "格式": row[6] if len(row) > 6 else None,
            "业务来源": row[7] if len(row) > 7 else None,
            "说明": row[8] if len(row) > 8 else None,
        }
    else:
        # 5 列格式
        return {
            "数据类型": row[1] if len(row) > 1 else None,
            "必填": row[2] == "是" if len(row) > 2 else None,
            "枚举值": row[3] if len(row) > 3 else None,
            "说明": row[4] if len(row) > 4 else None,
        }


def extract_entities_from_tables(content: str, headings: list, stage: str, counter: dict, title_to_id: dict = None) -> tuple:
    """从 design.md 的表格中提取页面和字段实体

    ID 策略：优先按标题匹配已有 ID，无匹配时从 max+1 分配新 ID。
    返回 (pages, fields, states, permissions) 四个列表
    """
    if title_to_id is None:
        title_to_id = {}
    tables = parse_tables_with_context(content, headings)
    pages = []
    fields = []
    states = []
    permissions = []

    for table in tables:
        section = table["section_title"]
        headers = table["headers"]

        # 页面清单表：检查是否在"页面清单"父标题下，且表头含"页面"或"名称"
        if _is_under_heading(table["line_offset"], headings, "页面清单") and (any("页面" in h for h in headers) or any("名称" in h for h in headers)):
            name_idx = next((i for i, h in enumerate(headers) if h == "名称" or "页面名称" in h or "页面" == h), None)
            if name_idx is None:
                name_idx = next((i for i, h in enumerate(headers) if "页面" in h or "名称" in h), None)
            if name_idx is not None:
                for row in table["rows"]:
                    if name_idx < len(row) and row[name_idx] and row[name_idx] not in ("---", "名称"):
                        title = row[name_idx]
                        if title in title_to_id:
                            entity_id = title_to_id[title]
                        else:
                            prefix = ID_PREFIXES.get("page", "PAGE")
                            count = counter.get(prefix, 0) + 1
                            counter[prefix] = count
                            entity_id = f"{prefix}-{stage}-{count:03d}"
                        pages.append({
                            "id": entity_id,
                            "type": "page",
                            "title": title,
                            "line": table["line_offset"],
                        })

        # 字段定义表：表头含"字段"和"类型"列（支持 5 列或 9 列格式）
        if "字段" in headers and "类型" in headers and len(headers) >= 4:
            for row in table["rows"]:
                if len(row) >= 2 and row[0] and row[0] not in ("---", "字段"):
                    title = row[0]
                    if title in title_to_id:
                        entity_id = title_to_id[title]
                    else:
                        prefix = ID_PREFIXES.get("field", "FIELD")
                        count = counter.get(prefix, 0) + 1
                        counter[prefix] = count
                        entity_id = f"{prefix}-{stage}-{count:03d}"
                    fields.append({
                        "id": entity_id,
                        "type": "field",
                        "title": title,
                        "line": table["line_offset"],
                        "attributes": _build_field_attributes(row, headers),
                    })

        # 规则与状态定义章节中的状态内容
        if "规则与状态" in section:
            for row in table["rows"]:
                if any("状态" in cell for cell in row):
                    states.append({"title": row[0] if row else "", "line": table["line_offset"]})

    # 如果表格解析没找到状态，从文本中提取
    if not states:
        for h in headings:
            if h["level"] >= 3 and "状态" in h["title"]:
                states.append({"title": h["title"], "line": h["line"]})

    # 权限定义：提取“权限定义”章节下的页面/角色小节
    in_permission_section = False
    section_level = None
    for h in headings:
        if "权限定义" in h["title"] and h["level"] <= 2:
            in_permission_section = True
            section_level = h["level"]
            continue
        if in_permission_section and h["level"] <= section_level:
            in_permission_section = False
            continue
        if in_permission_section and h["level"] >= 3:
            permissions.append({"title": h["title"], "line": h["line"]})

    return pages, fields, states, permissions


def _split_field_tokens(raw_text: str) -> list:
    """拆分字段单元格中的字段名列表"""
    if not raw_text:
        return []
    normalized = raw_text.replace("\n", "、")
    parts = re.split(r"[、，,；;/｜|]+", normalized)
    tokens = []
    for part in parts:
        token = part.strip()
        if not token or token in ("—", "-", "无", "无业务字段"):
            continue
        tokens.append(token)
    return tokens


def _extract_design_page_field_map(content: str, headings: list, pages: list, fields: list) -> list:
    """从“页面与字段落点”章节提取页面字段映射"""
    tables = parse_tables_with_context(content, headings)
    page_title_to_id = {p["title"]: p["id"] for p in pages}
    field_title_to_id = {f["title"]: f["id"] for f in fields}
    mappings = {}

    # 先登记“页面与字段落点”章节下出现过的页面小节，确保能做页面覆盖校验
    in_section = False
    section_level = None
    for h in headings:
        title = h["title"]
        if ("页面与字段落点" in title or "页面数据落点" in title) and h["level"] <= 2:
            in_section = True
            section_level = h["level"]
            continue
        if in_section and h["level"] <= section_level:
            break
        if in_section and h["level"] == section_level + 1:
            page_title = _clean_page_title(title)
            if "非页面落点字段" in page_title:
                continue
            mappings.setdefault(page_title, {
                "page_title": page_title,
                "design_page": page_title_to_id.get(page_title),
                "line": h["line"],
                "field_refs": [],
                "field_titles": [],
                "unmatched_fields": [],
                "declared_empty": False,
            })

    for table in tables:
        if not (_is_under_heading(table["line_offset"], headings, "页面与字段落点") or _is_under_heading(table["line_offset"], headings, "页面数据落点")):
            continue
        page_title = _clean_page_title(table["section_title"])
        if "非页面落点字段" in page_title:
            continue
        if not page_title:
            continue
        entry = mappings.setdefault(page_title, {
            "page_title": page_title,
            "design_page": page_title_to_id.get(page_title),
            "line": table["line_offset"],
            "field_refs": [],
            "field_titles": [],
            "unmatched_fields": [],
            "declared_empty": False,
        })

        headers = table["headers"]
        field_idx = next((i for i, h in enumerate(headers) if "字段" in h), None)
        if field_idx is None:
            continue

        for row in table["rows"]:
            cell = row[field_idx] if field_idx < len(row) else ""
            if any(flag in cell for flag in ("无业务字段", "无字段")):
                entry["declared_empty"] = True
                continue
            for token in _split_field_tokens(cell):
                design_field = field_title_to_id.get(token)
                if design_field:
                    entry["field_refs"].append(design_field)
                    entry["field_titles"].append(token)
                else:
                    entry["unmatched_fields"].append(token)

    results = []
    for entry in mappings.values():
        entry["field_refs"] = sorted(set(entry["field_refs"]))
        entry["field_titles"] = sorted(set(entry["field_titles"]))
        entry["unmatched_fields"] = sorted(set(entry["unmatched_fields"]))
        results.append(entry)
    return results


def _extract_design_non_page_fields(content: str, headings: list, fields: list) -> list:
    """从“非页面落点字段”例外表提取内部字段声明"""
    tables = parse_tables_with_context(content, headings)
    field_title_to_id = {f["title"]: f["id"] for f in fields}
    results = []

    for table in tables:
        section_title = table["section_title"]
        if "非页面落点字段" not in section_title:
            continue
        headers = table["headers"]
        field_idx = next((i for i, h in enumerate(headers) if "字段" in h), None)
        reason_idx = next((i for i, h in enumerate(headers) if "原因" in h or "说明" in h), None)
        if field_idx is None:
            continue

        for row in table["rows"]:
            raw_field = row[field_idx] if field_idx < len(row) else ""
            reason = row[reason_idx] if reason_idx is not None and reason_idx < len(row) else ""
            for token in _split_field_tokens(raw_field):
                results.append({
                    "field_title": token,
                    "design_field": field_title_to_id.get(token),
                    "reason": reason.strip(),
                    "line": table["line_offset"],
                })

    deduped = []
    seen = set()
    for item in results:
        key = item["field_title"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _build_page_field_relations(page_fields: list, stage: str, counter: dict) -> list:
    """基于页面字段落点生成 page -> field 的 uses 关系"""
    relations = []
    rel_counter = counter.get("REL", 0)
    for entry in page_fields:
        page_id = entry.get("design_page")
        if not page_id:
            continue
        for field_id in entry.get("field_refs", []):
            rel_counter += 1
            relations.append({
                "id": f"REL-{stage}-{rel_counter:03d}",
                "type": "uses",
                "from": page_id,
                "to": field_id,
            })
    counter["REL"] = rel_counter
    return relations


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


def _extract_numbered_rules_from_design(content: str, stage: str, counter: dict, title_to_id: dict) -> list:
    """从 design.md 的"规则"章节提取编号规则实体

    设计稿中规则通常以编号列表形式出现在 ### 规则 标题下：
    1. 每人每周仅可创建一份周报...
    2. 组长仅可查看本组...
    """
    entities = []
    lines = content.split('\n')
    in_rules_section = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 检测进入/退出"规则"章节（h3 级别）
        if re.match(r'^###\s+', stripped):
            if "规则" in stripped and "状态" not in stripped:
                in_rules_section = True
                continue
            elif in_rules_section:
                in_rules_section = False
                continue

        if not in_rules_section:
            continue

        # 匹配编号规则：如 "1. xxx"、"1、xxx"、"1）xxx"
        match = re.match(r'^(\d+)[.、）)]\s*(.+)$', stripped)
        if match:
            rule_text = match.group(2).strip()
            # 截取前 30 字符作为标题
            title = rule_text[:30] + ("..." if len(rule_text) > 30 else "")
            if title in title_to_id:
                entity_id = title_to_id[title]
            else:
                prefix = ID_PREFIXES.get("rule", "RULE")
                count = counter.get(prefix, 0) + 1
                counter[prefix] = count
                entity_id = f"{prefix}-{stage}-{count:03d}"
            entities.append({
                "id": entity_id,
                "type": "rule",
                "title": title,
                "line": i + 1,
            })

    return entities


def generate_design_metadata(content: str, stage: str, project_root: Path) -> dict:
    """生成 design 阶段 metadata（含稳定 ID）

    两种提取方式合并，共享 title_to_id 和 counter：
    - 标题推断：模块、规则（从 ###/#### 标题中识别）
    - 表格解析：页面、字段（从 Markdown 表格中提取）
    """
    headings = parse_headings(content)

    # 从已有 metadata 读取 {title: id} 映射和 max ID 计数
    title_to_id, counter = read_existing_entities(stage, project_root) if project_root else ({}, {})

    # 标题推断：模块、规则（传入共享 title_to_id 和 counter）
    heading_entities = infer_entities_from_headings(headings, stage, project_root, title_to_id, counter)

    # 表格解析：页面、字段、状态、权限（传入共享 title_to_id 和 counter）
    table_pages, table_fields, table_states, table_perms = extract_entities_from_tables(
        content, headings, stage, counter, title_to_id
    )

    # 编号规则提取：从"规则"章节的编号列表中提取独立规则实体
    numbered_rules = _extract_numbered_rules_from_design(content, stage, counter, title_to_id)

    # 抽取页面与字段落点（页面 -> 字段）
    page_fields = _extract_design_page_field_map(content, headings, table_pages, table_fields)
    non_page_fields = _extract_design_non_page_fields(content, headings, table_fields)

    # 合并所有实体（标题推断的 modules/rules + 表格解析的 pages/fields + 编号规则）
    entities = heading_entities + table_pages + table_fields + numbered_rules

    relations = infer_relations_from_content(content, entities, stage)
    relations.extend(_build_page_field_relations(page_fields, stage, counter))

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

    result = {
        "index": index,
        "entities": entities,
        "relations": relations,
        "modules": modules,
        "pages": pages,
        "fields": fields,
        "rules": rules,
        "page_fields": page_fields,
        "non_page_fields": non_page_fields,
    }
    # 始终写入 states 和 permissions，覆盖可能存在的陈旧文件
    result["states"] = table_states
    result["permissions"] = table_perms
    # 生成字段约束速查表（供 PRD 生成时防幻觉）
    result["field_constraints"] = generate_field_constraints(result)
    return result



def generate_field_constraints(design_data: dict) -> list:
    """从 design metadata 中提取字段约束速查表，供 PRD 生成时防幻觉使用。

    只保留：字段名、稳定ID、单选/多选、只读/可编辑、必填/选填、所属页面。
    目标 < 3KB，agent 生成 PRD 时只需读这一个文件即可确认字段约束。
    """
    fields = design_data.get("fields", [])
    page_fields = design_data.get("page_fields", [])
    rules = design_data.get("rules", [])

    # 构建 页面→字段 映射
    field_pages = {}
    for pf in page_fields:
        if isinstance(pf, dict):
            page_name = pf.get("page", "")
            for f in pf.get("fields", []):
                fname = f if isinstance(f, str) else f.get("name", "")
                if fname:
                    field_pages.setdefault(fname, []).append(page_name)

    # 从 rules 中提取数量规则（单选/多选）
    selection_rules = {}
    for rule in rules:
        if isinstance(rule, dict):
            title = rule.get("title", "")
            content_text = rule.get("content", "") or rule.get("detail", "")
            if "单选" in title or "默认带出" in title:
                # 提及的字段标记为单选
                pass
            if "备选" in title and "多选" in (content_text or ""):
                pass
            if "默认与备选数量" in title:
                selection_rules[title] = content_text

    # 从字段 attributes 中提取约束
    constraints = []
    for field in fields:
        if not isinstance(field, dict):
            continue
        field_id = field.get("id", "")
        title = field.get("title", "")
        attrs = field.get("attributes", {})

        if not title or not field_id:
            continue

        # 跳过元数据字段（字段权限例外等）
        if "权限例外" in title:
            continue

        data_type = attrs.get("数据类型", "")
        required = attrs.get("必填", None)
        enum_vals = attrs.get("枚举值", "")
        business_source = attrs.get("业务来源", "")
        detail = attrs.get("说明", "")

        # 推断编辑性
        editable = True
        if "自动带出" in str(business_source) or "系统生成" in str(business_source) or "系统同步" in str(business_source) or "NCC" in str(business_source):
            editable = False
        if "只读" in str(detail):
            editable = False
        if "科目编码" in title:
            editable = False  # 科目编码只读，科目名称自动带出

        # 推断选择方式
        select_mode = "input"
        if data_type == "enum" or "枚举" in str(enum_vals):
            select_mode = "enum"
        if "搜索弹窗" in str(detail) or "选择" in str(detail):
            select_mode = "popup-select"
        if "标签" in str(detail):
            select_mode = "tag-select"

        # 推断单选/多选（从规则或字段名推断）
        multi_select = None
        if "默认带出" in title:
            multi_select = False  # 默认带出 = 单选
        if "备选" in title:
            multi_select = True   # 备选 = 多选

        # 所属页面
        pages = field_pages.get(title, [])

        constraint = {
            "id": field_id,
            "name": title,
            "type": data_type,
            "required": required,
            "editable": editable,
            "select_mode": select_mode,
        }
        if multi_select is not None:
            constraint["multi_select"] = multi_select
        if pages:
            constraint["pages"] = pages
        if enum_vals and enum_vals != "—" and enum_vals != "沿用原系统":
            constraint["enum"] = enum_vals

        constraints.append(constraint)

    return constraints


def generate_prd_metadata(content: str, project_root: Path) -> dict:
    """生成 PRD 阶段 metadata（不含新稳定 ID，只引用 design）

    从 PRD 正文中提取字段名/规则描述/页面名，匹配 design 的稳定 ID。
    """
    headings = parse_headings(content)

    index = {
        "schema_version": "1.0.0",
        "stage": "prd",
        "artifact_path": "output/prd/prd.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # 读取 design metadata 作为匹配基准
    design_fields = _load_design_metadata(project_root, "fields.json")
    design_pages = _load_design_metadata(project_root, "pages.json")
    design_rules = _load_design_metadata(project_root, "rules.json")

    # 建立 title → id 映射
    field_title_to_id = {f["title"]: f["id"] for f in design_fields}
    page_title_to_id = {p["title"]: p["id"] for p in design_pages}
    rule_title_to_id = {r["title"]: r["id"] for r in design_rules}

    # 1. 从"数据字典"表格提取字段 anchor
    field_anchor = _extract_prd_field_anchors(content, headings, field_title_to_id)

    # 2. 从"详细需求说明"章节标题提取页面 anchor
    page_anchor = _extract_prd_page_anchors(content, headings, page_title_to_id)

    # 3. 从 PRD 正文提取规则 anchor（匹配 design 规则标题）
    rule_anchor = _extract_prd_rule_anchors(content, rule_title_to_id)

    # 4. 继承 design 的 entities 和 relations（PRD 是 design 的镜像）
    design_entities = _load_design_metadata(project_root, "entities.json")
    design_relations = _load_design_metadata(project_root, "relations.json")

    return {
        "index": index,
        "entities": design_entities,
        "relations": design_relations,
        "page_anchor": page_anchor,
        "rule_anchor": rule_anchor,
        "field_anchor": field_anchor,
    }


def _load_design_metadata(project_root: Path, filename: str) -> list:
    """加载 design 阶段的 metadata 文件"""
    meta_file = project_root / ".workflow" / "metadata" / "design" / filename
    if meta_file.exists():
        try:
            with open(meta_file, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _extract_prd_field_anchors(content: str, headings: list, field_title_to_id: dict) -> list:
    """从 PRD 数据字典表格中提取字段名，匹配 design FIELD ID

    数据字典表格可能在子标题（如 ### 周报实体）下，
    此时 section_title 是子标题名而非"数据字典"。
    需要回溯最近的 h2 标题确认是否在数据字典章节内。
    """
    anchors = []
    tables = parse_tables_with_context(content, headings)

    for table in tables:
        section = table["section_title"]
        # 检查当前 section 或最近的 h2 父标题是否包含"数据字典"
        in_data_dict = "数据字典" in section
        if not in_data_dict:
            in_data_dict = _is_under_heading(table["line_offset"], headings, "数据字典")
        if not in_data_dict:
            continue
        # 确认是 9 列数据字典格式
        if "字段" not in table["headers"] or "类型" not in table["headers"]:
            continue
        for row in table["rows"]:
            if len(row) >= 1 and row[0] and row[0] not in ("---", "字段"):
                field_name = row[0]
                design_id = field_title_to_id.get(field_name)
                anchors.append({
                    "prd_field": field_name,
                    "design_field": design_id,
                    "prd_line": table["line_offset"],
                    "data_dict": True,
                })
    return anchors


def _is_under_heading(table_line: int, headings: list, keyword: str) -> bool:
    """检查表格行号之前最近的 h2 标题是否包含指定关键词"""
    for h in sorted(headings, key=lambda x: x["line"], reverse=True):
        if h["line"] < table_line and h["level"] <= 2:
            return keyword in h["title"]
    return False


def _extract_prd_page_anchors(content: str, headings: list, page_title_to_id: dict) -> list:
    """从 PRD 详细需求说明章节的子标题中提取页面名，匹配 design PAGE ID"""
    anchors = []
    in_detail = False

    for h in headings:
        title = h["title"]
        # 进入详细需求说明章节
        if "详细需求" in title and h["level"] >= 2:
            in_detail = True
            continue
        # 离开详细需求说明章节
        if in_detail and h["level"] <= 2 and "详细需求" not in title:
            in_detail = False
            continue

        if not in_detail:
            continue

        # 在详细需求章节内的子标题（### 级别），匹配合并中文序号
        if h["level"] >= 3:
            clean_title = _clean_page_title(title)
            design_id = page_title_to_id.get(clean_title)
            if design_id:
                anchors.append({
                    "prd_page": clean_title,
                    "design_page": design_id,
                    "prd_line": h["line"],
                })

    return anchors


def _clean_page_title(title: str) -> str:
    """去除标题中的中文序号前缀
    如 '（一）我的周报列表页' → '我的周报列表页'
    如 '1．我的周报列表页' → '我的周报列表页'
    """
    cleaned = re.sub(r'^[（(][一二三四五六七八九十\d]+[）)]\s*', '', title)
    cleaned = re.sub(r'^\d+[．.]\s*', '', cleaned)
    cleaned = re.sub(r'^page[-_\s]?\d+\s*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _extract_prd_rule_anchors(content: str, rule_title_to_id: dict) -> list:
    """从 PRD 正文中提取规则描述，匹配 design RULE ID

    匹配策略：
    1. 对 PRD 全文逐行扫描
    2. 对每行文本，检查是否包含 design 规则标题中的关键词
    3. 如果匹配成功，建立 PRD 规则行 → design RULE ID 的 anchor
    """
    anchors = []
    if not rule_title_to_id:
        return anchors

    lines = content.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        for design_title, design_id in rule_title_to_id.items():
            if len(design_title) <= 3:
                continue
            if _fuzzy_match(stripped, design_title):
                anchors.append({
                    "prd_rule": design_title,
                    "design_rule": design_id,
                    "prd_line": i + 1,
                })

    seen_ids = set()
    deduped = []
    for a in anchors:
        if a["design_rule"] not in seen_ids:
            seen_ids.add(a["design_rule"])
            deduped.append(a)

    return deduped


def _extract_numbered_rules(content: str) -> list:
    """从 PRD 正文中提取编号规则文本

    搜索"规则"相关章节下的编号列表项（如 1. xxx / 1、xxx）。
    """
    rules = []
    lines = content.split('\n')
    in_rules_section = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 检测进入/退出"规则"章节（h2/h3 标题）
        if re.match(r'^#{1,3}\s+', stripped):
            if "规则" in stripped and "权限" not in stripped and "数据" not in stripped:
                in_rules_section = True
                continue
            elif in_rules_section:
                in_rules_section = False
                continue

        if not in_rules_section:
            continue

        # 匹配编号规则：如 "1. xxx"、"1、xxx"、"1）xxx"
        match = re.match(r'^(\d+)[.、）)]\s*(.+)$', stripped)
        if match:
            rules.append({
                "num": int(match.group(1)),
                "text": match.group(2),
                "line": i + 1,
            })

    return rules


def _fuzzy_match(prd_text: str, design_title: str) -> bool:
    """模糊匹配：PRD 规则文本是否与 design 规则标题实质相同

    策略：提取 design_title 中的关键短语（长度 >= 4 的非停顿词片段），
    检查是否出现在 prd_text 中。
    """
    if not prd_text or not design_title:
        return False
    # 提取 design_title 中的长片段（4+ 字符的子串）
    for start in range(len(design_title) - 3):
        fragment = design_title[start:start + 4]
        if fragment in prd_text:
            return True
    return False


def generate_prototype_metadata(content: str, project_root: Path) -> dict:
    """生成 prototype 阶段 metadata

    从 index.html 提取页面标题，匹配 design 的 PAGE ID，写入 page-map。
    """
    index = {
        "schema_version": "1.0.0",
        "stage": "prototype",
        "artifact_path": "output/prototype/index.html",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_count": 0,
        "relation_count": 0,
    }

    # 读取 design pages 作为匹配基准
    design_pages = _load_design_metadata(project_root, "pages.json")
    page_title_to_id = {p["title"]: p["id"] for p in design_pages}

    # 从 HTML 中提取页面标题
    page_map = _extract_html_page_titles(content, page_title_to_id)

    return {
        "index": index,
        "page_map": page_map,
    }


def _extract_html_page_titles(html_content: str, page_title_to_id: dict) -> list:
    """从 HTML 中提取页面标题，匹配 design PAGE ID

    提取策略：导航链接 → page-title 元素 → h2 标签。
    过滤规则：source_page_ref 为 null 的不写入；同一 design PAGE ID 只保留第一个匹配。
    """
    raw_matches = []
    seen_titles = set()

    def collect(pattern, html):
        for match in pattern.finditer(html):
            title = match.group(1).strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                ref = _match_page_title(title, page_title_to_id)
                raw_matches.append((title, ref))

    # 方法1：导航链接文本（通常最接近 design 页面名）
    nav_pattern = re.compile(r'<a[^>]*data-page=["\'][^"\']*["\'][^>]*>([^<]+)</a>', re.IGNORECASE)
    collect(nav_pattern, html_content)

    # 方法2：匹配 class="page-title" 的元素文本内容
    title_pattern = re.compile(r'class=["\'][^"\']*page-title[^"\']*["\'][^>]*>([^<]+)<', re.IGNORECASE)
    collect(title_pattern, html_content)

    # 方法3：匹配 <h2> 标签文本
    h2_pattern = re.compile(r'<h2[^>]*>([^<]+)</h2>', re.IGNORECASE)
    collect(h2_pattern, html_content)

    # 去重：过滤 null，同一 source_page_ref 只保留第一个
    page_map = []
    seen_refs = set()
    for title, ref in raw_matches:
        if ref is None:
            continue  # 无法追溯到 design 的条目不写入
        if ref in seen_refs:
            continue  # 同一 design PAGE ID 已匹配过
        seen_refs.add(ref)
        page_map.append({
            "page_id": f"page-{len(page_map) + 1}",
            "title": title,
            "source_page_ref": ref,
        })

    return page_map


def _match_page_title(html_title: str, page_title_to_id: dict) -> str:
    """将 HTML 页面标题匹配到 design PAGE ID

    先精确匹配，再子串包含匹配，最后关键字重叠匹配。
    """
    if html_title in page_title_to_id:
        return page_title_to_id[html_title]

    # 子串包含匹配：design 页面名包含 html_title 或 html_title 包含 design 页面名
    for design_title, design_id in page_title_to_id.items():
        if design_title in html_title or html_title in design_title:
            return design_id

    # 关键字重叠匹配：提取双方的关键字，有 2+ 字重叠则匹配
    html_keywords = _extract_keywords(html_title)
    for design_title, design_id in page_title_to_id.items():
        design_keywords = _extract_keywords(design_title)
        overlap = html_keywords & design_keywords
        if len(overlap) >= 2:
            return design_id

    return None


def _extract_keywords(title: str) -> set:
    """从标题中提取二字关键词"""
    keywords = set()
    # 提取二字词
    for i in range(len(title) - 1):
        kw = title[i:i+2]
        # 排除标点和数字
        if re.match(r'[一-鿿]{2}', kw):
            keywords.add(kw)
    return keywords


def write_metadata(stage: str, data: dict, project_root: Path, dry_run: bool = False, merge: bool = False) -> list:
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
        "page_fields": "page-fields.json",
        "non_page_fields": "non-page-fields.json",
        "field_constraints": "field-constraints.json",
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


def update_status(stage: str, project_root: Path, dry_run: bool = False):
    """stage-prep 完成后同步更新 status.json

    更新字段：
    - current_stage → 当前阶段
    - artifacts → 追加当前产物路径
    - metadata_paths → 追加当前 metadata 路径
    - next_recommended → 按阶段顺序映射
    - latest_reviews → 从 reviews/ 读取最新 review 的 verdict 和 reviewed_at
    """
    if dry_run:
        return
    status_path = project_root / ".workflow" / "status.json"
    if not status_path.exists():
        return
    with open(status_path, encoding="utf-8") as f:
        status = json.load(f)

    STAGE_ORDER = {"align": 0, "design": 1, "prd": 2, "prototype": 3}
    old_stage = status.get("current_stage", "align")
    if STAGE_ORDER.get(stage, 0) >= STAGE_ORDER.get(old_stage, 0):
        status["current_stage"] = stage
    artifact_path = ARTIFACT_PATHS.get(stage)
    if artifact_path:
        status.setdefault("artifacts", {})[stage] = artifact_path
    status.setdefault("metadata_paths", {})[stage] = f".workflow/metadata/{stage}/"

    next_map = {"align": "design", "design": "prd", "prd": "prototype", "prototype": "done", "fix": "design"}
    base_next = next_map.get(stage, stage)

    if base_next == "done":
        status["next_recommended"] = "done"
    else:
        latest_review = status.get("latest_reviews", {}).get(stage, {})
        if latest_review.get("verdict") == "通过":
            status["next_recommended"] = base_next
        else:
            status["next_recommended"] = f"{stage}-review"

    # 读取当前阶段的 review 文件，取最新的 verdict 和 reviewed_at
    reviews_dir = project_root / ".workflow" / "reviews"
    if reviews_dir.exists():
        review_prefix = f"{stage}-review"
        matching_reviews = []
        for review_file in reviews_dir.glob(f"{review_prefix}*.json"):
            try:
                with open(review_file, encoding="utf-8") as f:
                    review_data = json.load(f)
                matching_reviews.append({
                    "file": review_file.name,
                    "verdict": review_data.get("verdict"),
                    "reviewed_at": review_data.get("reviewed_at"),
                })
            except (json.JSONDecodeError, OSError):
                continue
        if matching_reviews:
            # 按 reviewed_at 排序，取最新
            matching_reviews.sort(key=lambda r: r.get("reviewed_at") or "", reverse=True)
            latest = matching_reviews[0]
            status.setdefault("latest_reviews", {})[stage] = {
                "verdict": latest["verdict"],
                "reviewed_at": latest["reviewed_at"],
            }

    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="机读镜像生成脚本")
    parser.add_argument("--stage", required=True, choices=VALID_STAGES, help="目标阶段")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不写入文件")
    parser.add_argument("--merge", action="store_true", help="合并所有 metadata 为单文件 metadata.json")
    parser.add_argument("--stdin-artifact", action="store_true", help="从 stdin 读取人读稿内容（避免重复读文件）")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    stage = args.stage

    # 读取人读产物
    if args.stdin_artifact:
        content = sys.stdin.read()
    else:
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
        data = generate_prototype_metadata(content, project_root)
    else:
        print(f"错误: 不支持的阶段: {stage}", file=sys.stderr)
        sys.exit(1)

    # 写入文件
    written_files = write_metadata(stage, data, project_root, dry_run=args.dry_run, merge=args.merge)
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

    # 同步更新 status.json
    update_status(stage, project_root, dry_run=args.dry_run)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
