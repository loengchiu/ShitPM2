#!/usr/bin/env python3
"""verify-against-metadata.py"""

import argparse, json, re, sys
from pathlib import Path
from shared_md import parse_headings, parse_tables_with_context


def _fuzzy_field_match(token, ftid):
    if token in ftid: return ftid[token]
    stripped = re.sub(r"[（(][^）)][）)]", "", token).strip()
    if stripped and stripped in ftid: return ftid[stripped]
    for sfx in ("（必填）", "（选填）", "（多选）", "（单选）", "(必填)", "(选填)", "(多选)", "(单选)"):
        if token.endswith(sfx):
            clean = token[:-len(sfx)].strip()
            if clean in ftid: return ftid[clean]
    return None


def normalize_page_name(name: str) -> str:
    import re as _re
    s = name.strip()
    s = _re.sub(r'^\d+(?:\.\d+)*[\.、．]\s*', '', s)
    if s.endswith('页'):
        s = s[:-1]
    s = s.replace('列表页', '列表').replace('详情页', '详情').replace('编辑页', '编辑')
    return s.strip()


def _fuzzy_page_match(pt, ptid):
    if pt in ptid: return ptid[pt]
    import re as _re
    stripped = _re.sub(r'^\d+(?:\.\d+)*[\.、．]\s*', '', pt).strip()
    if stripped and stripped in ptid: return ptid[stripped]
    if stripped and stripped.endswith("页"):
        ns = stripped[:-1].strip()
        if ns in ptid: return ptid[ns]
    if stripped:
        ws = stripped + "页"
        if ws in ptid: return ptid[ws]
    if pt.endswith("页"):
        ns = pt[:-1].strip()
        if ns in ptid: return ptid[ns]
    ws = pt + "页"
    if ws in ptid: return ptid[ws]
    return None


def load_design_metadata(project_root):
    meta_dir = project_root / ".workflow" / "metadata" / "design"
    result = {"fields": [], "pages": [], "states": [], "permissions": [], "field_constraints": []}
    for fname in ["fields.json", "pages.json", "states.json", "permissions.json", "field-constraints.json"]:
        fpath = meta_dir / fname
        if fpath.exists():
            try:
                with open(fpath, encoding="utf-8") as f: data = json.load(f)
                key = fname.replace(".json", "").replace("-", "_")
                if isinstance(data, list): result[key] = data
            except (json.JSONDecodeError, OSError): pass
    return result


def load_design_md(project_root):
    p = project_root / "output" / "design" / "design.md"
    if p.exists():
        with open(p, encoding="utf-8") as f: return f.read()
    return ""


def extract_design_fields_from_md(content):
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    fields = {}
    for table in tables:
        headers = table["headers"]
        if "字段" in headers and "类型" in headers and len(headers) >= 2:
            fi, ti = headers.index("字段"), headers.index("类型")
            ri = headers.index("必填") if "必填" in headers else None
            ei = next((idx for idx, h in enumerate(headers) if "枚举" in h or "规则" in h), None)
            for row in table["rows"]:
                if fi < len(row) and row[fi]:
                    name = row[fi].strip()
                    if name in ("字段", "---", ""): continue
                    info = {}
                    if ti < len(row): info["type"] = row[ti].strip()
                    if ri is not None and ri < len(row): info["required"] = row[ri].strip()
                    if ei is not None and ei < len(row): info["enum"] = row[ei].strip()
                    fields[name] = info
    return fields


def extract_design_pages_from_md(content):
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    pages = set()
    for table in tables:
        headers = table["headers"]
        if any("页面" in h or "名称" in h for h in headers):
            ni = next((i for i, h in enumerate(headers) if h in ("名称", "页面") or "页面名称" in h), None)
            if ni is None:
                ni = next((i for i, h in enumerate(headers) if "页面" in h or "名称" in h), None)
            if ni is not None:
                for row in table["rows"]:
                    if ni < len(row) and row[ni] and row[ni] not in ("---", "名称"):
                        pages.add(row[ni].strip())
    return pages


def extract_prd_fields(content):
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    fields = set()
    for table in tables:
        headers = table["headers"]
        if "字段" in headers and "类型" in headers and len(headers) >= 2:
            fi = headers.index("字段")
            for row in table["rows"]:
                if fi < len(row) and row[fi]:
                    name = row[fi].strip()
                    if name not in ("字段", "---", ""): fields.add(name)
    return fields


def extract_prd_fields_detailed(content):
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    fields = {}
    for table in tables:
        headers = table["headers"]
        if "字段" in headers and "类型" in headers and len(headers) >= 2:
            fi, ti = headers.index("字段"), headers.index("类型")
            ri = headers.index("必填") if "必填" in headers else None
            ei = next((idx for idx, h in enumerate(headers) if "枚举" in h or "规则" in h or "说明" in h), None)
            for row in table["rows"]:
                if fi < len(row) and row[fi]:
                    name = row[fi].strip()
                    if name in ("字段", "---", ""): continue
                    info = {}
                    if ti < len(row): info["type"] = row[ti].strip()
                    if ri is not None and ri < len(row): info["required"] = row[ri].strip()
                    if ei is not None and ei < len(row): info["enum"] = row[ei].strip()
                    fields[name] = info
    return fields


def extract_prd_pages(content):
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    pages = set()
    kws = ("页面", "列表", "详情", "编辑", "首页", "登录", "设置", "配置", "管理", "查看", "新建")
    for h in headings:
        if "模块" in h["title"]:
            continue
        if 3 <= h["level"] <= 4 and any(kw in h["title"] for kw in kws):
            pages.add(h["title"])
    for table in tables:
        headers = table["headers"]
        sec = table.get("section_title", "")
        if not any(("页面" in h) or ("页面名称" in h) for h in headers):
            continue
        if "模块" not in sec and not any(("页面清单" in sec) or ("页面" in h) for h in headers):
            continue
        ni = next((i for i, h in enumerate(headers) if h in ("页面名称", "页面") or h == "名称"), None)
        if ni is None:
            continue
        for row in table["rows"]:
            if ni < len(row) and row[ni] and row[ni] not in ("---", "名称", "页面名称"):
                pages.add(row[ni].strip())
    return pages


def extract_prd_states(content):
    headings = parse_headings(content)
    entities, in_sec, sec_lv = set(), False, None
    for h in headings:
        if "状态" in h["title"] and h["level"] <= 2: in_sec, sec_lv = True, h["level"]; continue
        if in_sec and h["level"] <= sec_lv: in_sec = False; continue
        if in_sec and h["level"] >= 3: entities.add(h["title"])
    return entities


def extract_prd_permissions(content):
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)
    perms = set()
    for table in tables:
        if "权限" not in table["section_title"]: continue
        for row in table["rows"]:
            if row: perms.add("、".join(c.strip() for c in row if c.strip()))
    return perms


def extract_prototype_fields(html_content):
    fields = set()
    for m in re.finditer(r"<label[^>]*>([^<]+)</label>", html_content):
        t = m.group(1).strip()
        if t and len(t) <= 20: fields.add(t)
    pat_ph = r'placeholder="([^"]+)"'
    pat_lb = r'label="([^"]+)"'
    for m in re.finditer(pat_ph, html_content):
        t = m.group(1).strip()
        if t and len(t) <= 20: fields.add(t)
    for m in re.finditer(pat_lb, html_content):
        t = m.group(1).strip()
        if t and len(t) <= 20: fields.add(t)
    return fields


def extract_prototype_pages(html_content):
    pages = set()
    pat_tab = r'<el-tab-pane[^>]*label="([^"]+)"'
    for m in re.finditer(pat_tab, html_content):
        pages.add(m.group(1).strip())
    for m in re.finditer(r"<h[23][^>]*>([^<]+)</h[23]>", html_content):
        t = m.group(1).strip()
        if t and len(t) <= 30: pages.add(t)
    return pages


def check_constraint_consistency(prd_fields, design_fields):
    mismatches = []
    for fname, pinfo in prd_fields.items():
        dname = fname if fname in design_fields else None
        if not dname:
            stripped = re.sub(r"[（(][^）)][）)]", "", fname).strip()
            if stripped in design_fields: dname = stripped
        if not dname: continue
        dinfo = design_fields[dname]
        if pinfo.get("required","") and dinfo.get("required","") and pinfo["required"] != dinfo["required"]:
            mismatches.append({"field": fname, "attribute": "required", "prd_value": pinfo["required"], "design_value": dinfo["required"]})
        de, pe = dinfo.get("enum",""), pinfo.get("enum","")
        if de and de not in ("—", "", "沿用原系统") and pe in ("—", ""):
            mismatches.append({"field": fname, "attribute": "enum", "prd_value": pe or "(空)", "design_value": de})
    return mismatches


def verify_prd(project_root, artifact_content):
    design_md = load_design_md(project_root)
    design_meta = load_design_metadata(project_root)
    df_md = extract_design_fields_from_md(design_md)
    dp_meta = [p.get("title", "") for p in design_meta.get("pages", []) if isinstance(p, dict) and p.get("title")]
    dp_md = set(dp_meta) if dp_meta else extract_design_pages_from_md(design_md)
    dc = {c["name"]: c for c in design_meta.get("field_constraints", []) if isinstance(c, dict) and c.get("name")}
    dfn = set(df_md.keys()) | set(dc.keys())
    pf = extract_prd_fields(artifact_content)
    pp = extract_prd_pages(artifact_content)
    ps = extract_prd_states(artifact_content)
    prm = extract_prd_permissions(artifact_content)
    ds = {s.get("title","") for s in design_meta.get("states",[]) if isinstance(s, dict)}
    dp = {p.get("title","") for p in design_meta.get("permissions",[]) if isinstance(p, dict)}
    # fuzzy match: exact hit returns immediately; fallback strips suffixes
    matched = {f for f in pf if f in dfn or _fuzzy_field_match(f, {n: n for n in dfn})}
    generic = {"字段","类型","必填","说明","备注","状态","操作","编号","名称","创建时间","更新时间"}
    hf = {f for f in pf - matched if f not in generic and len(f) > 1}
    mf = {f for f in dfn - pf if f not in ("字段权限例外","权限例外")}
    npp = {normalize_page_name(p): p for p in pp}
    ndp = {normalize_page_name(p): p for p in dp_md}
    norm_to_orig = {normalize_page_name(p): p for p in dp_md}
    prd_text = artifact_content
    prd_text_norm = prd_text.replace('　', ' ')
    mp_norm = set()
    for n, orig in norm_to_orig.items():
        if n in npp:
            mp_norm.add(n)
            continue
        if _fuzzy_page_match(n, {nn: nn for nn in ndp}):
            mp_norm.add(n)
            continue
        if n and n in prd_text_norm:
            mp_norm.add(n)
    mp = {norm_to_orig[n] for n in mp_norm}
    hp = set(npp[n] for n in set(npp) - mp_norm)
    pfi = extract_prd_fields_detailed(artifact_content)
    cm = check_constraint_consistency(pfi, df_md)
    all_h = sorted(hf) + sorted(hp)
    fr = len(matched) / len(dfn) if dfn else 1.0
    prr = len(mp_norm) / len(ndp) if ndp else 1.0
    pct = lambda v: str(int(v * 100)) + "%"
    return {
        "stage": "prd",
        "metrics": {
            "field_coverage": {"in_output": len(pf), "in_design": len(dfn), "ratio": round(fr, 2), "missing": sorted(mf)[:20], "hallucinated": sorted(hf)},
            "page_coverage": {"in_output": len(pp), "in_design": len(ndp), "ratio": round(prr, 2), "missing": sorted(set(norm_to_orig[n] for n in set(ndp) - mp_norm))[:20]},
            "state_coverage": {"in_output": len(ps), "in_design": len(ds), "missing_entities": sorted(ds - ps)[:10]},
            "permission_coverage": {"in_output": len(prm), "in_design": len(dp), "missing": sorted(dp - prm)[:10]},
            "constraint_mismatches": cm[:20],
        },
        "hallucinated_items": all_h,
        "summary": "字段覆盖率 " + pct(fr) + "，页面覆盖率 " + pct(prr) + "，" + str(len(all_h)) + " 个幻觉项，" + str(len(cm)) + " 个约束不一致",
    }


def verify_prototype(project_root, artifact_content):
    design_md = load_design_md(project_root)
    design_meta = load_design_metadata(project_root)
    df_md = extract_design_fields_from_md(design_md)
    dp_meta = [p.get("title", "") for p in design_meta.get("pages", []) if isinstance(p, dict) and p.get("title")]
    dp_md = set(dp_meta) if dp_meta else extract_design_pages_from_md(design_md)
    dfn = set(df_md.keys())
    pf = extract_prototype_fields(artifact_content)
    pp = extract_prototype_pages(artifact_content)
    # fuzzy match: exact hit returns immediately; fallback strips suffixes
    matched = {f for f in pf if f in dfn or _fuzzy_field_match(f, {n: n for n in dfn})}
    generic = {"查询","重置","新增","编辑","删除","查看","导出","导入","提交","保存","取消","确定","关闭"}
    hf = {f for f in pf - matched if f not in generic and len(f) > 1}
    npp = {normalize_page_name(p): p for p in pp}
    ndp = {normalize_page_name(p): p for p in dp_md}
    pmap = {n: n for n in dp_md}
    mp_norm = {n for n in npp if n in ndp or _fuzzy_page_match(n, {nn: nn for nn in ndp})}
    mp = {npp[n] for n in mp_norm}
    hp = set(npp[n] for n in set(npp) - mp_norm)
    all_h = sorted(hf) + sorted(hp)
    fr = len(matched) / len(dfn) if dfn else 1.0
    prr = len(mp_norm) / len(ndp) if ndp else 1.0
    pct = lambda v: str(int(v * 100)) + "%"
    return {
        "stage": "prototype",
        "metrics": {
            "field_coverage": {"in_output": len(pf), "in_design": len(dfn), "ratio": round(fr, 2), "hallucinated": sorted(hf)},
            "page_coverage": {"in_output": len(pp), "in_design": len(ndp), "ratio": round(prr, 2), "hallucinated": sorted(hp)},
        },
        "hallucinated_items": all_h,
        "summary": "字段覆盖率 " + pct(fr) + "，页面覆盖率 " + pct(prr) + "，" + str(len(all_h)) + " 个幻觉项",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=["prd", "prototype"])
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--stdin-artifact", action="store_true")
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    if args.stdin_artifact:
        artifact_content = sys.stdin.read()
    else:
        ap = project_root / ("output/prd/prd.md" if args.stage == "prd" else "output/prototype/index.html")
        if not ap.exists():
            print(json.dumps({"error": "not found"}, ensure_ascii=False))
            sys.exit(1)
        with open(ap, encoding="utf-8") as f: artifact_content = f.read()
    result = verify_prd(project_root, artifact_content) if args.stage == "prd" else verify_prototype(project_root, artifact_content)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("hallucinated_items"): sys.exit(1)


if __name__ == "__main__":
    main()
