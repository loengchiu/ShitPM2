#!/usr/bin/env python3
"""stage-prep.py — 机读镜像生成脚本

职责：从当前人读稿中抽取并生成 metadata anchor。
不判断是否允许进入该阶段，不修改人读稿正文。

用法：python stage-prep.py --stage <stage> [--project-root <path>] [--dry-run]

结构说明（按职责分组，便于维护时定位）：
- 通用 ID 工具：read_existing_entities / _scan_ids_recursive
- design 提取：generate_design_metadata 及辅助（infer_entities_from_headings /
  extract_entities_from_tables / _extract_design_page_field_map 等）
- prd/prototype：只生成 index + relations，不提取 anchor（语义检测交给 review skill LLM）
- 写入与状态：write_metadata / write_stage_context / update_status
- 调度：main
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from shared_md import (
    parse_headings, parse_tables_with_context,
    fuzzy_field_match, fuzzy_page_match,
    is_under_heading, clean_page_title,
    ID_PREFIXES,
    ARTIFACT_PATHS, METADATA_FILE_MAP,
)
VALID_STAGES = ["design"]


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
    "design": {"module", "page", "field", "rule", "flow"},
}

# 章节级标题模式（不应被识别为实体条目）
# 匹配 "## 一、角色定义"、"## 三、模块定义" 等纯章节标记
CHAPTER_HEADING_PATTERN = re.compile(r'^[一二三四五六七八九十]+[、．.]')

# 标题词黑名单：这些是章节容器标题本身，不是实体条目
# "业务规则" 含 "规则" 关键词但它是 ### 容器标题，不应识别为 rule 实体
HEADING_BLACKLIST = {
    "业务规则", "状态集合", "状态迁移", "状态机", "状态定义", "状态流转",
    "权限定义", "角色权限", "权限矩阵", "页面清单", "字段定义",
    "页面与字段落点", "页面数据落点", "非页面落点字段",
    "核心业务流程", "业务流程",
}


def read_existing_entities(stage: str, project_root: Path) -> tuple:
    """从已有 metadata 中读取已有实体的 {title: id} 映射和每种前缀的最大 ID 编号

    返回 (title_to_id, max_ids)
    - title_to_id: {entity_title: entity_id} 用于按标题匹配已有 ID
    - max_ids: {prefix: max_number} 用于为新实体分配 ID

    前缀校验：只复用 ID 前缀与 entity_type 匹配的条目，防止历史脏 ID（如 page
    误用 PERM- 前缀、rule 误用 STATE- 前缀）被 title 匹配后永久延续。
    """
    title_to_id = {}
    max_ids = {}
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    if not metadata_dir.exists():
        return title_to_id, max_ids

    id_pattern = re.compile(r'^(MODULE|PAGE|FIELD|RULE|FLOW|REL|PERM|STATE)-' + re.escape(stage) + r'-(\d{3})$')
    for json_file in metadata_dir.glob("*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if not (isinstance(item, dict) and "id" in item and "title" in item):
                        continue
                    eid = item["id"]
                    etype = item.get("type")
                    match = id_pattern.match(eid)
                    if not match:
                        continue
                    item_prefix = match.group(1)
                    # 前缀校验：ID 前缀必须与声明的 type 对应，不符则跳过（不自愈脏 ID）
                    expected_prefix = ID_PREFIXES.get(etype) if etype else None
                    if expected_prefix and item_prefix != expected_prefix:
                        continue
                    title_to_id[item["title"]] = eid
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
        # 跳过章节容器标题本身（"业务规则"/"状态集合" 等含关键词但是容器标题）
        if title in HEADING_BLACKLIST:
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


def _build_field_attributes(row: list, headers: list) -> dict:
    """根据列名适配 5 列或 9 列字段格式

    5 列格式（当前设计稿）：字段 | 类型 | 必填 | 枚举值 / 规则 | 说明
    9 列格式（原模板）：字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明

    判断依据：表头是否含"长度"和"默认值"列，而非列数阈值。
    """
    has_length = any("长度" in h for h in headers)
    has_default = any("默认值" in h for h in headers)
    if has_length and has_default:
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
        if is_under_heading(table["line_offset"], headings, "页面清单") and (any("页面" in h for h in headers) or any("名称" in h for h in headers)):
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
        if "字段" in headers and "类型" in headers and len(headers) >= 2:
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

    # 状态机表提取（迁移 + 实体归属）移至 _extract_states_from_tables 独立处理
    # 状态提取：优先状态机表解析（含迁移+ID），兜底从"状态集合"列表项解析（含ID）
    states = _extract_states_from_tables(tables, headings, stage, counter)
    if not states:
        states = _extract_states_from_content(content, stage, counter)

    # 权限深度提取：解析权限章节下 "### 页面名" 子标题内的 "- role：action" 列表项
    # 输出 (page_title, role, action_text) 三元组，不再把页面名当权限实体
    permissions = _extract_permissions_from_content(content)
    perm_counter = counter.get("PERM", 0)
    for p in permissions:
        if "id" not in p:
            perm_counter += 1
            p["id"] = f"PERM-{stage}-{perm_counter:03d}"
            p["type"] = "permission"
    counter["PERM"] = perm_counter

    return pages, fields, states, permissions


def _find_header_index(headers, candidates):
    """返回 headers 中第一个匹配 candidates 任一词的列索引，无匹配返回 None"""
    for i, h in enumerate(headers):
        for c in candidates:
            if c in h:
                return i
    return None


def _infer_entity_from_headings(table_line, headings):
    """从表格行号往上找最近的 ### 实体标题（跳过容器标题黑名单）

    状态机表通常在 ## 级章节下用 ### 分实体。遇 ## 级标题停止（实体不会在 ## 之上）。
    """
    for h in sorted(headings, key=lambda x: x["line"], reverse=True):
        if h["line"] >= table_line:
            continue
        if h["level"] == 3 and h["title"] not in HEADING_BLACKLIST:
            return h["title"]
        if h["level"] <= 2:
            break
    return None


def _extract_states_from_tables(tables, headings, stage, counter):
    """从状态机表提取状态 + 迁移 + 实体归属

    仅支持 6 列规范格式：状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件。
    识别条件：表头同时含"状态"+"操作人"+"触发动作"+"下一状态"四列。
    返回 states 列表，每个状态含 id/type/title/entity/is_terminal/transitions。
    "任意状态"通配 from_state 挂为该实体的伪状态（is_wildcard=True），供校验脚本特殊处理。
    终态推断：无自身出边且该实体无全局迁移出路 → 终态。
    ID 按 counter 顺序分配（不跨重跑稳定，states 无脚本消费者依赖 ID 稳定）。
    """
    state_map = {}
    entity_global = {}

    for table in tables:
        headers = table["headers"]
        from_idx = _find_header_index(headers, ["状态"])
        operator_idx = _find_header_index(headers, ["操作人"])
        trigger_idx = _find_header_index(headers, ["触发动作"])
        to_idx = _find_header_index(headers, ["下一状态"])
        if from_idx is None or operator_idx is None or trigger_idx is None or to_idx is None:
            # 4 列表头时友好提示（常见旧格式：状态|含义|说明|备注）
            from_only = _find_header_index(headers, ["状态"])
            if from_only is not None and len(headers) <= 4:
                print(f"  警告: 发现 4 列旧格式状态表（行 {table['line_offset']}），未提取状态机迁移数据。请改用 6 列规范格式：状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件", file=sys.stderr)
            continue

        condition_idx = _find_header_index(headers, ["限制条件"])
        entity = _infer_entity_from_headings(table["line_offset"], headings)
        line = table["line_offset"]
        last_from = None

        for row in table["rows"]:
            from_state = row[from_idx].strip() if from_idx < len(row) else ""
            if not from_state:
                from_state = last_from or ""
            if from_state:
                last_from = from_state
            trigger = row[trigger_idx].strip() if trigger_idx < len(row) else ""
            to_state = row[to_idx].strip() if to_idx < len(row) else ""
            operator = row[operator_idx].strip() if operator_idx is not None and operator_idx < len(row) else None
            condition = row[condition_idx].strip() if condition_idx is not None and condition_idx < len(row) else None
            is_terminal_row = trigger in ("—", "-", "") and to_state in ("—", "-", "")

            if from_state == "任意状态":
                if entity not in entity_global:
                    entity_global[entity] = []
                if not is_terminal_row and trigger and to_state and to_state not in ("—", "-"):
                    entity_global[entity].append({
                        "trigger": trigger, "to_state": to_state,
                        "operator": operator, "condition": condition, "line": line,
                    })
            elif from_state:
                key = (entity, from_state)
                if key not in state_map:
                    state_map[key] = {
                        "title": from_state, "entity": entity,
                        "transitions": [], "line": line, "is_terminal": False,
                    }
                if is_terminal_row:
                    state_map[key]["is_terminal"] = True
                elif trigger and to_state and to_state not in ("—", "-"):
                    state_map[key]["transitions"].append({
                        "trigger": trigger, "to_state": to_state,
                        "operator": operator, "condition": condition, "line": line,
                    })

            if to_state and to_state not in ("—", "-", "任意状态"):
                key = (entity, to_state)
                if key not in state_map:
                    state_map[key] = {
                        "title": to_state, "entity": entity,
                        "transitions": [], "line": line, "is_terminal": False,
                    }

    for entity, transits in entity_global.items():
        key = (entity, "任意状态")
        if key not in state_map:
            state_map[key] = {
                "title": "任意状态", "entity": entity,
                "transitions": transits, "line": 0,
                "is_terminal": False, "is_wildcard": True,
            }

    # 标记每个实体的初始态（第一个非通配、非终态状态，按行序）
    _entity_first = {}
    for key, s in state_map.items():
        entity_key = key[0]
        if s.get("is_wildcard"):
            continue
        if entity_key not in _entity_first or s.get("line", 9999) < _entity_first[entity_key].get("line", 9999):
            _entity_first[entity_key] = s
    for s in _entity_first.values():
        if not s.get("is_terminal"):
            s["is_initial"] = True

    states = []
    for s in state_map.values():
        state_counter = counter.get("STATE", 0) + 1
        counter["STATE"] = state_counter
        s["id"] = f"STATE-{stage}-{state_counter:03d}"
        s["type"] = "state"
        states.append(s)
    return states


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


# 键值列表项模式：- `key`：value / - key：value / - key: value
# 同时用于状态集合（key=状态名，value=含义）和权限列表（key=角色，value=动作）
_KEY_VALUE_LIST_PATTERN = re.compile(r'^[-*]\s*`?([^`：:\s]+)`?\s*[：:]\s*(.+)$')
# 状态章节关键词
_STATE_SECTION_KEYWORDS = ("状态集合", "状态定义", "状态流转", "状态机", "规则与状态")
# 权限章节关键词
_PERM_SECTION_KEYWORDS = ("权限定义", "角色权限", "权限矩阵")


def _extract_states_from_content(content: str, stage: str, counter: dict) -> list:
    """从"状态集合"子章节的列表项提取状态实体（含 ID 分配）

    design 格式：
      ### 状态集合
      - `draft`：草稿
      - `submitted`：已提交

    ID 分配与此函数内联，与 _extract_states_from_tables 对称。
    不再提取 h3 标题（"状态集合"/"状态迁移" 是容器标题不是状态）。
    """
    states = []
    lines = content.split('\n')
    in_state_section = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 检测进入状态子章节
        if re.match(r'^#{3,}\s+', stripped):
            if any(kw in stripped for kw in _STATE_SECTION_KEYWORDS):
                in_state_section = True
            else:
                in_state_section = False
            continue
        if not in_state_section:
            continue
        match = _KEY_VALUE_LIST_PATTERN.match(stripped)
        if match:
            state_name = match.group(1).strip()
            state_desc = match.group(2).strip()
            state_counter = counter.get("STATE", 0) + 1
            counter["STATE"] = state_counter
            states.append({
                "id": f"STATE-{stage}-{state_counter:03d}",
                "type": "state",
                "title": state_name,
                "detail": state_desc,
                "line": i + 1,
            })

    return states


def _extract_permissions_from_content(content: str) -> list:
    """从权限章节提取 (page_title, role, action_text) 三元组

    design 格式：
      ## 八、权限定义
      ### 我的周报列表
      - `member`：可查看自己的周报列表，可进入填写页
      - `admin`：可查看所有成员周报列表

    每个 ### 子标题是页面分组，其下的 - role：action 才是权限实体。
    不再把页面名当权限实体。
    """
    permissions = []
    lines = content.split('\n')
    in_perm_section = False
    current_page = ""

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 检测进入权限章节（h2 级别含权限关键词）
        if re.match(r'^#{1,2}\s+', stripped):
            if any(kw in stripped for kw in _PERM_SECTION_KEYWORDS):
                in_perm_section = True
            else:
                in_perm_section = False
            current_page = ""
            continue
        # 权限章节内的 h3 子标题 = 页面分组名
        if in_perm_section and re.match(r'^#{3,}\s+', stripped):
            current_page = re.sub(r'^#{3,}\s+', '', stripped).strip()
            continue
        if not in_perm_section:
            continue
        match = _KEY_VALUE_LIST_PATTERN.match(stripped)
        if match and current_page:
            role = match.group(1).strip()
            action = match.group(2).strip()
            permissions.append({
                "title": f"{current_page}-{role}",
                "page": current_page,
                "role": role,
                "action": action,
                "line": i + 1,
            })

    return permissions


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
        if in_section and h["level"] > section_level:
            page_title = clean_page_title(title)
            # 去"页"尾缀，与 pages.json 中页面名格式对齐
            page_key = page_title[:-1].strip() if page_title.endswith('页') else page_title
            if "非页面落点字段" in page_key:
                continue
            mappings.setdefault(page_key, {
                "page_title": page_title,
                "design_page": fuzzy_page_match(page_title, page_title_to_id),
                "line": h["line"],
                "field_refs": [],
                "field_titles": [],
                "unmatched_fields": [],
                "declared_empty": False,
            })

    for table in tables:
        if not (is_under_heading(table["line_offset"], headings, "页面与字段落点") or is_under_heading(table["line_offset"], headings, "页面数据落点")):
            continue
        page_title = clean_page_title(table["section_title"])
        page_key = page_title[:-1].strip() if page_title.endswith('页') else page_title
        if "非页面落点字段" in page_key:
            continue
        if not page_key:
            continue
        entry = mappings.setdefault(page_key, {
            "page_title": page_title,
            "design_page": fuzzy_page_match(page_title, page_title_to_id),
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
                design_field = fuzzy_field_match(token, field_title_to_id)
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
                    "design_field": fuzzy_field_match(token, field_title_to_id),
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


def _extract_numbered_rules_from_design(content: str, stage: str, counter: dict, title_to_id: dict) -> list:
    """从 design.md 的"规则"章节提取编号规则实体

    设计稿中规则通常以编号列表形式出现在 ### 规则 标题下：
    1. 每人每周仅可创建一份周报...
    2. 组长仅可查看本组...
    """
    entities = []
    lines = content.split('\n')
    in_rules_section = False
    rules_section_level = None
    rule_index = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 检测进入/退出"规则"章节（h3 级别，按层级退出更可靠）
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_title = heading_match.group(2)
            if "规则" in heading_title and "状态" not in heading_title:
                in_rules_section = True
                rules_section_level = level
                continue
            elif in_rules_section and level <= rules_section_level:
                in_rules_section = False
                continue

        if not in_rules_section:
            continue

        # 匹配编号规则：如 "1. xxx"、"1、xxx"、"1）xxx"
        match = re.match(r'^(\d+)[.、）)]\s*(.+)$', stripped)
        if match:
            rule_text = match.group(2).strip()
            rule_index += 1
            # 用编号做 title 保证唯一性，规则原文存 detail
            title = f"规则 {rule_index}"
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
                "detail": rule_text,
            })

    return entities


def generate_design_metadata(content: str, stage: str, project_root: Path) -> dict:
    """生成 design 阶段 metadata（含稳定 ID）

    三种提取方式合并，共享 title_to_id 和 counter：
    - 标题推断：模块、页面、字段、规则、流程（从 ###/#### 标题中识别）
    - 表格解析：页面、字段（从 Markdown 表格中提取）
    - 内容解析：状态、权限（从"状态集合"/"权限定义"章节列表项提取）
    - 编号规则提取：从"规则"章节的编号列表中提取独立规则实体
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

    # 合并所有实体（标题推断 + 表格解析 + 编号规则），按 (type, id) 去重
    raw_entities = heading_entities + table_pages + table_fields + numbered_rules
    seen = set()
    entities = []
    for e in raw_entities:
        key = (e.get("type"), e.get("id"))
        if key not in seen:
            seen.add(key)
            entities.append(e)

    relations = []
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
        "relations": relations,
        "modules": modules,
        "pages": pages,
        "fields": fields,
        "rules": rules,
        "page_fields": page_fields,
        "non_page_fields": non_page_fields,
        "entities": entities,  # 完整实体列表（含 flows），供 _count_entities 统一计数
    }
    # 始终写入 states 和 permissions，覆盖可能存在的陈旧文件
    result["states"] = table_states
    result["permissions"] = table_perms
    return result


def write_metadata(stage: str, data: dict, project_root: Path, dry_run: bool = False) -> list:
    """将 metadata 写入文件"""
    metadata_dir = project_root / ".workflow" / "metadata" / stage
    if not dry_run:
        metadata_dir.mkdir(parents=True, exist_ok=True)

    files = METADATA_FILE_MAP.get(stage, [])

    key_file_map = {
        "index": "index.json",
        "relations": "relations.json",
        "modules": "modules.json",
        "pages": "pages.json",
        "fields": "fields.json",
        "rules": "rules.json",
        "states": "states.json",
        "permissions": "permissions.json",
        "page_fields": "page-fields.json",
        "non_page_fields": "non-page-fields.json",
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


def _count_entities(data: dict) -> int:
    """统计实际写入的实体数

    与 index.json 的 entity_count 口径一致：design 阶段含 modules/pages/fields/rules/flows
    （不含 states/permissions，这两类是结构实体而非业务实体）；其他阶段无实体。
    """
    entities = data.get("entities", [])
    return len(entities) if isinstance(entities, list) else 0


def write_stage_context(stage: str, data: dict, project_root: Path, dry_run: bool = False) -> str:
    """写入 stage-context.json"""
    ctx_dir = project_root / ".workflow" / "runtime" / stage
    if not dry_run:
        ctx_dir.mkdir(parents=True, exist_ok=True)

    relations = data.get("relations", [])

    ctx = {
        "stage": stage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entity_count": _count_entities(data),
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

    # 含 review 子阶段的阶段顺序（与 status.schema.json current_stage 枚举一致）
    STAGE_ORDER = {
        "align": 0, "design": 1, "design-review": 1,
        "prd": 2, "prd-review": 2,
        "prototype": 3, "prototype-review": 3,
        "fix": 0, "done": 4,
    }
    old_stage = status.get("current_stage", "align")
    # stage-prep 只处理主阶段（design/prd/prototype），不处理 review 子阶段
    # 但 old_stage 可能是 review 子阶段，需正确比较避免回退
    if STAGE_ORDER.get(stage, 0) >= STAGE_ORDER.get(old_stage, 0):
        status["current_stage"] = stage
    artifact_path = ARTIFACT_PATHS.get(stage)
    if artifact_path:
        status.setdefault("artifacts", {})[stage] = artifact_path
    status.setdefault("metadata_paths", {})[stage] = f".workflow/metadata/{stage}/"

    next_map = {
        "align": "design", "design": "prd", "design-review": "prd",
        "prd": "prototype", "prd-review": "prototype",
        "prototype": "done", "prototype-review": "done",
        "fix": "design", "done": "done",
    }
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
    if stage in ("design", "prd", "prototype"):
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
            else:
                # review 文件缺失时清空过期数据，避免基于过时 review 做错误判定
                status.setdefault("latest_reviews", {}).pop(stage, None)

    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="机读镜像生成脚本")
    parser.add_argument("--stage", required=True, choices=VALID_STAGES, help="目标阶段")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不写入文件")
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
        if not content.strip():
            print(f"错误: 人读产物为空: {artifact_path}", file=sys.stderr)
            sys.exit(1)

    # 根据阶段生成 metadata
    if stage == "design":
        data = generate_design_metadata(content, stage, project_root)
    else:
        print(f"错误: 不支持的阶段: {stage}", file=sys.stderr)
        sys.exit(1)

    # 写入文件
    written_files = write_metadata(stage, data, project_root, dry_run=args.dry_run)
    ctx_file = write_stage_context(stage, data, project_root, dry_run=args.dry_run)

    entities = data.get("entities", [])
    relations = data.get("relations", [])

    result = {
        "stage": stage,
        "dry_run": args.dry_run,
        "metadata_files_written": written_files,
        "stage_context_file": ctx_file,
        "entity_count": _count_entities(data),
        "relation_count": len(relations) if isinstance(relations, list) else 0,
    }

    # 同步更新 status.json
    update_status(stage, project_root, dry_run=args.dry_run)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
