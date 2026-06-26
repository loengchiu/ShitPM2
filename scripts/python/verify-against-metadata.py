#!/usr/bin/env python3
"""verify-against-metadata.py -- 幻觉检测与一致性校验（纯 JSON 对比）

从 stage-prep.py 生成的 metadata JSON 中比对 design 与 artifact，
报告幻觉项、缺失项、约束不一致。不再解析 Markdown。
合并了原 anchor-verify.py 的 metadata 结构完整性校验。

用法:
  python verify-against-metadata.py --stage prd --project-root .
  python verify-against-metadata.py --stage prototype --project-root .
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── JSON 加载 ────────────────────────────────────────────────

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_design_metadata(project_root):
    meta_dir = project_root / ".workflow" / "metadata" / "design"
    result = {}
    for fname in ["fields.json", "pages.json", "states.json", "permissions.json",
                   "modules.json", "rules.json"]:
        fpath = meta_dir / fname
        data = load_json(fpath)
        if data and isinstance(data, list):
            result[fname.replace(".json", "")] = data
    return result


def load_prd_metadata(project_root):
    meta_dir = project_root / ".workflow" / "metadata" / "prd"
    result = {}
    for fname in ["field_anchor.json", "page_anchor.json", "rule_anchor.json",
                   "index.json", "relations.json"]:
        fpath = meta_dir / fname
        data = load_json(fpath)
        if data is not None:
            result[fname.replace(".json", "")] = data
    return result


def load_prototype_metadata(project_root):
    meta_dir = project_root / ".workflow" / "metadata" / "prototype"
    result = {}
    for fname in ["index.json", "page-map.json"]:
        fpath = meta_dir / fname
        data = load_json(fpath)
        if data is not None:
            result[fname.replace(".json", "")] = data
    return result


# ── PRD 校验 ─────────────────────────────────────────────────

def verify_prd(project_root):
    design = load_design_metadata(project_root)
    prd_meta = load_prd_metadata(project_root)

    if not prd_meta.get("field_anchor") and not prd_meta.get("page_anchor"):
        return {"stage": "prd", "error": "PRD metadata not found. Run stage-prep.py --stage prd first."}

    design_fields = {f["title"]: f for f in design.get("fields", [])
                     if isinstance(f, dict) and f.get("title")}
    design_pages = {p["title"]: p for p in design.get("pages", [])
                    if isinstance(p, dict) and p.get("title")}

    field_anchors = prd_meta.get("field_anchor", [])
    page_anchors = prd_meta.get("page_anchor", [])

    # 幻觉字段：anchor 中 design_field 为空
    hallucinated_fields = [a["prd_field"] for a in field_anchors if not a.get("design_field")]

    # 缺失字段：design 字段不在任何 anchor 中
    matched_design_fields = {a["design_field"] for a in field_anchors if a.get("design_field")}
    missing_fields = sorted(f for f in design_fields if f not in matched_design_fields)

    # 幻觉页面：anchor 中 design_page 为空
    hallucinated_pages = [a["prd_page"] for a in page_anchors if not a.get("design_page")]

    # 缺失页面：design 页面不在任何 anchor 中
    matched_design_pages = {a["design_page"] for a in page_anchors if a.get("design_page")}
    missing_pages = sorted(p for p in design_pages if p not in matched_design_pages)

    # 约束一致性：字段类型/必填/枚举不匹配
    mismatches = []
    for a in field_anchors:
        dname = a.get("design_field")
        if not dname or dname not in design_fields:
            continue
        dinfo = design_fields[dname]
        if a.get("prd_type") and dinfo.get("type") and a["prd_type"] != dinfo["type"]:
            mismatches.append({"field": a["prd_field"], "attr": "type",
                               "prd": a["prd_type"], "design": dinfo["type"]})
        if a.get("prd_required") and dinfo.get("required") and a["prd_required"] != dinfo["required"]:
            mismatches.append({"field": a["prd_field"], "attr": "required",
                               "prd": a["prd_required"], "design": dinfo["required"]})
        de = dinfo.get("enum", "")
        pe = a.get("prd_enum", "")
        if de and de not in ("—", "", "沿用原系统") and pe in ("—", ""):
            mismatches.append({"field": a["prd_field"], "attr": "enum",
                               "prd": pe or "(空)", "design": de})

    all_h = sorted(set(hallucinated_fields + hallucinated_pages))
    fr = len(matched_design_fields) / len(design_fields) if design_fields else 1.0
    pr = len(matched_design_pages) / len(design_pages) if design_pages else 1.0

    return {
        "stage": "prd",
        "hallucinated_items": all_h,
        "metrics": {
            "field_coverage": {
                "in_output": len(field_anchors), "in_design": len(design_fields),
                "ratio": round(fr, 2),
                "hallucinated": sorted(hallucinated_fields),
                "missing": missing_fields[:20],
            },
            "page_coverage": {
                "in_output": len(page_anchors), "in_design": len(design_pages),
                "ratio": round(pr, 2),
                "hallucinated": sorted(hallucinated_pages),
                "missing": missing_pages[:20],
            },
            "constraint_mismatches": mismatches[:20],
        },
        "summary": f"字段覆盖率 {int(fr*100)}%，页面覆盖率 {int(pr*100)}%，{len(all_h)} 个幻觉项，{len(mismatches)} 个约束不一致",
    }


# ── Prototype 校验 ───────────────────────────────────────────

def extract_prototype_fields(html_content):
    fields = set()
    for m in re.finditer(r'<label[^>]*>([^<]+)</label>', html_content):
        t = m.group(1).strip()
        if t and len(t) <= 20:
            fields.add(t)
    for pat in [r'placeholder="([^"]+)"', r'label="([^"]+)"']:
        for m in re.finditer(pat, html_content):
            t = m.group(1).strip()
            if t and len(t) <= 20:
                fields.add(t)
    return fields


def extract_prototype_pages(html_content):
    pages = set()
    for m in re.finditer(r'<a\s+role="tab"\s+class="tab[^"]*"[^>]*>([^<]+)</a>', html_content):
        pages.add(m.group(1).strip())
    for m in re.finditer(r'<h[23][^>]*>([^<]+)</h[23]>', html_content):
        t = m.group(1).strip()
        if t and len(t) <= 30:
            pages.add(t)
    return pages


def verify_prototype(project_root):
    design = load_design_metadata(project_root)
    design_fields = {f["title"] for f in design.get("fields", [])
                     if isinstance(f, dict) and f.get("title")}
    design_pages = {p["title"] for p in design.get("pages", [])
                    if isinstance(p, dict) and p.get("title")}

    html_path = project_root / "output" / "prototype" / "index.html"
    if not html_path.exists():
        return {"stage": "prototype", "error": "index.html not found"}
    html = html_path.read_text(encoding="utf-8")

    pf = extract_prototype_fields(html)
    pp = extract_prototype_pages(html)

    generic = {"查询", "重置", "新增", "编辑", "删除", "查看", "导出", "导入",
               "提交", "保存", "取消", "确定", "关闭"}
    matched_f = {f for f in pf if f in design_fields}
    hf = sorted(f for f in pf - matched_f if f not in generic and len(f) > 1)

    matched_p = {p for p in pp if p in design_pages}
    hp = sorted(pp - matched_p)

    all_h = hf + hp
    fr = len(matched_f) / len(design_fields) if design_fields else 1.0
    pr = len(matched_p) / len(design_pages) if design_pages else 1.0

    return {
        "stage": "prototype",
        "hallucinated_items": all_h,
        "metrics": {
            "field_coverage": {"in_output": len(pf), "in_design": len(design_fields),
                               "ratio": round(fr, 2), "hallucinated": hf},
            "page_coverage": {"in_output": len(pp), "in_design": len(design_pages),
                              "ratio": round(pr, 2), "hallucinated": hp},
        },
        "summary": f"字段覆盖率 {int(fr*100)}%，页面覆盖率 {int(pr*100)}%，{len(all_h)} 个幻觉项",
    }


# ── Metadata 结构完整性校验（原 anchor-verify.py） ─────────

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

    # 实体 ID 唯一性
    entity_files = {"design": ["modules.json", "pages.json", "fields.json", "rules.json"],
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
    parser = argparse.ArgumentParser(description="幻觉检测与一致性校验")
    parser.add_argument("--stage", required=True, choices=["prd", "prototype"])
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project_root = args.project_root.resolve()

    # 1. Metadata 结构完整性
    integrity_errors = verify_metadata_integrity(project_root, args.stage)

    # 2. 幻觉检测
    if args.stage == "prd":
        result = verify_prd(project_root)
    else:
        result = verify_prototype(project_root)

    result["integrity_errors"] = integrity_errors
    if integrity_errors:
        result["summary"] += f"；{len(integrity_errors)} 个结构完整性问题"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("hallucinated_items") or integrity_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
