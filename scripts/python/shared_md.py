"""shared_md.py — Markdown 解析、模糊匹配、常量 共用模块

设计原则：只放被多个脚本重复实现的函数和常量。
"""

import json
import re
import importlib.util
import hashlib
from pathlib import Path


# ── 同目录脚本加载 ────────────────────────────────────────────

def load_sibling(filename: str, alias: str):
    """加载同目录下的脚本模块（文件名含连字符时无法用普通 import）。"""
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_design_manifest(project_root):
    """加载设计集清单 → (manifest_dict, files_list, error_message_or_None)。"""
    path = Path(project_root) / "output" / "design" / "设计集清单.json"
    if not path.is_file():
        return None, None, f"设计集清单不存在: {path}"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, None, f"设计集清单无法解析: {path}: {exc}"
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list) or not manifest["files"]:
        return None, None, f"设计集清单缺少有效的 files 数组: {path}"
    return manifest, manifest["files"], None


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    return sha256_text(Path(path).read_text(encoding="utf-8-sig"))


def heading_scope_end(headings, index, total_lines):
    """当前标题的作用域到下一个同级或更高级标题为止。"""
    current = headings[index]
    for next_heading in headings[index + 1:]:
        if next_heading["level"] <= current["level"]:
            return next_heading["line"] - 1
    return total_lines


# ── 常量 ──────────────────────────────────────────────────────

STABLE_ID_PATTERN = re.compile(r'(MODULE|PAGE|FIELD|RULE|FLOW|REL|PERM|STATE)-(design|prd|prototype)-\d{3}')

ARTIFACT_PATHS = {
    "align": "output/align/align.md",
    "design": "output/design/设计地图.md",
    "design_manifest": "output/design/设计集清单.json",
    "prd": "output/prd/prd.md",
    "prototype": "output/prototype/index.html",
}

METADATA_FILE_MAP = {
    "design": ["index.json", "relations.json", "modules.json", "pages.json",
               "fields.json", "rules.json", "states.json", "permissions.json",
               "page-fields.json", "non-page-fields.json"],
}

ID_PREFIXES = {
    "module": "MODULE", "page": "PAGE", "field": "FIELD",
    "rule": "RULE", "flow": "FLOW", "permission": "PERM",
    "state": "STATE", "relation": "REL",
}


# ── 章节标题辅助 ──────────────────────────────────────────────


def strip_heading_number(title: str) -> str:
    """去除 Markdown 标题的编号前缀（阿拉伯/中文序号），返回纯文本标题"""
    text_str = title.strip()
    # 1) 阿拉伯数字编号
    text_str = re.sub(r'^\d+(?:\.\d+)*[.\s]*', '', text_str)
    text_str = re.sub(r'^[（(]\d+[）)]\s*', '', text_str)
    # 2) 中文序号
    text_str = re.sub(r'^[（(]([一二三四五六七八九十]+)[）)]\s*', lambda m: '', text_str)
    text_str = re.sub(r'^([一二三四五六七八九十]+)[、，。,\.]\s*', lambda m: '', text_str)
    return text_str



# ── JSON 工具 ─────────────────────────────────────────────────

def load_json(path, default=None):
    """加载 JSON 文件，失败返回 default"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def find_stable_id_leaks(text: str) -> list:
    """扫描文本中的稳定 ID 泄漏，返回 [(line_no, matched_str), ...]"""
    leaks = []
    for i, line in enumerate(text.split('\n')):
        for m in STABLE_ID_PATTERN.finditer(line):
            leaks.append((i + 1, m.group(0)))
    return leaks


# ── Markdown 解析 ─────────────────────────────────────────────

def parse_headings(content: str) -> list:
    """解析 Markdown 标题结构 → [{level, title, line}, ...]"""
    headings = []
    for i, line in enumerate(content.split('\n')):
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            headings.append({
                "level": len(match.group(1)),
                "title": match.group(2).strip(),
                "line": i + 1,
            })
    return headings


def parse_tables_with_context(content: str, headings: list) -> list:
    """解析 Markdown 表格并关联到所在章节 → [{section_title, section_line, headers, rows, line_offset}]"""
    lines = content.split('\n')
    tables = []
    current_section = ""
    current_section_line = 1
    heading_map = {h["line"]: h["title"] for h in headings}

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if i + 1 in heading_map:
            current_section = heading_map[i + 1]
            current_section_line = i + 1
        if line.startswith("|") and "|" in line[1:] and i + 1 < len(lines):
            sep_line = lines[i + 1].strip()
            if re.match(r'^\|[\s\-:|]+\|$', sep_line):
                headers = [h.strip() for h in line.split("|")[1:-1]]
                rows = []
                j = i + 2
                while j < len(lines):
                    if lines[j].strip() == "":
                        j += 1
                        continue
                    if not lines[j].strip().startswith("|"):
                        break
                    rows.append([c.strip() for c in lines[j].strip().split("|")[1:-1]])
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


# ── 模糊匹配 ─────────────────────────────────────────────────

def fuzzy_field_match(token: str, field_title_to_id: dict) -> str | None:
    """模糊匹配字段名 → 稳定 ID"""
    if not token:
        return None
    if token in field_title_to_id:
        return field_title_to_id[token]
    # 去括号
    stripped = re.sub(r'[（(][^）)]*[）)]', '', token).strip()
    if stripped and stripped in field_title_to_id:
        return field_title_to_id[stripped]
    # 去尾部标注
    for suffix in ('（必填）', '（选填）', '（多选）', '（单选）', '(必填)', '(选填)', '(多选)', '(单选)'):
        if token.endswith(suffix):
            clean = token[:-len(suffix)].strip()
            if clean in field_title_to_id:
                return field_title_to_id[clean]
    return None


def fuzzy_page_match(page_title: str, page_title_to_id: dict) -> str | None:
    """模糊匹配页面名 → 稳定 ID"""
    if not page_title:
        return None
    if page_title in page_title_to_id:
        return page_title_to_id[page_title]
    # 去尾缀"页"
    if page_title.endswith('页'):
        no_suffix = page_title[:-1].strip()
        if no_suffix in page_title_to_id:
            return page_title_to_id[no_suffix]
    # 加尾缀"页"
    with_suffix = page_title + '页'
    if with_suffix in page_title_to_id:
        return page_title_to_id[with_suffix]
    return None


def fuzzy_state_match(state_name: str, state_title_to_id: dict) -> str | None:
    """模糊匹配状态名 → 稳定 ID"""
    if not state_name:
        return None
    if state_name in state_title_to_id:
        return state_title_to_id[state_name]
    # 去"状态"后缀
    if state_name.endswith('状态'):
        no_suffix = state_name[:-2].strip()
        if no_suffix in state_title_to_id:
            return state_title_to_id[no_suffix]
    # 加"状态"后缀
    with_suffix = state_name + '状态'
    if with_suffix in state_title_to_id:
        return state_title_to_id[with_suffix]
    # 去括号内容
    stripped = re.sub(r'[（(][^）)]*[）)]', '', state_name).strip()
    if stripped and stripped in state_title_to_id:
        return state_title_to_id[stripped]
    return None


# ── 章节与页面辅助 ───────────────────────────────────────────

def is_under_heading(table_line: int, headings: list, keyword: str) -> bool:
    """检查 table_line 之前最近的 h2 标题是否含 keyword"""
    for h in sorted(headings, key=lambda x: x["line"], reverse=True):
        if h["line"] < table_line and h["level"] <= 2:
            return keyword in h["title"]
    return False


def clean_page_title(title: str) -> str:
    """去编号前缀：'5.1.1.1 我的周报列表页' / '（一）我的周报列表页' → '我的周报列表页'"""
    # 数字编号前缀（如 5.1.1.1）
    cleaned = re.sub(r'^\d+(?:\.\d+)*\s+', '', title)
    # 中文序号前缀（如 （一））
    cleaned = re.sub(r'^[（(][一二三四五六七八九十\d]+[）)]\s*', '', cleaned)
    # 单数字前缀（如 1. / 1．）
    cleaned = re.sub(r'^\d+[．.]\s*', '', cleaned)
    cleaned = re.sub(r'^page[-_\s]?\d+\s*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


# ── ID 分配 ─────────────────────────────────────────────────
# 注：ID 分配逻辑由 stage-prep.py 各提取函数内联实现（标题匹配优先，否则 counter+1），
# 无需独立函数。
