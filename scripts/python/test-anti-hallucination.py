#!/usr/bin/env python3
"""test-anti-hallucination.py — 防幻觉机制测试框架

基于审计系统 PRD（1466 行，10 模块 30+ 实体 14 状态机）的固定测试案例。
测试流程：
  prepare  — 从固定 PRD 生成 design metadata + 注入幻觉的 PRD 副本
  verify   — 运行 prd-consistency-check.py 验证幻觉检出
  clean    — 清理测试产物（metadata 和幻觉 PRD）

用法：
  python test-anti-hallucination.py prepare
  python test-anti-hallucination.py verify
  python test-anti-hallucination.py clean
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_DIR = PROJECT_ROOT / "test-fixture"
FIXTURE_PRD = FIXTURE_DIR / "output" / "prd" / "prd.md"
FIXTURE_META_DIR = FIXTURE_DIR / ".workflow" / "metadata" / "design"
HALLUCINATION_PRD = FIXTURE_DIR / "output" / "prd" / "prd-hallucination.md"

# 预期注入的幻觉项（section → 关键词列表）
EXPECTED_HALLUCINATIONS = {
    "fields": ["幻觉字段_X"],
    "pages": ["幻觉页面Z"],
    "states": ["幻觉状态X"],
    "permissions": ["幻觉权限页Y"],
}



def _tables_in_range_compat(tables, start, end):
    """返回指定行范围内的表格"""
    return [t for t in tables if start <= t.get("line_offset", 0) < (end or float("inf"))]

def _gen_design_metadata():
    """从固定 PRD 反推生成 design metadata

    直接复用 prd-consistency-check.py 的提取函数，确保提取规则对称。
    """
    import importlib.util

    scripts_dir = PROJECT_ROOT / "scripts" / "python"
    sys.path.insert(0, str(scripts_dir))
    from shared_md import parse_headings, parse_tables_with_context

    # 文件名含连字符，需 importlib 加载
    spec = importlib.util.spec_from_file_location(
        "prd_consistency_check", scripts_dir / "prd-consistency-check.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    content = FIXTURE_PRD.read_text(encoding="utf-8")
    headings = parse_headings(content)
    tables = parse_tables_with_context(content, headings)

    prd_fields = mod.extract_prd_fields(headings, tables)
    prd_pages = mod.extract_prd_pages(content, headings)
    prd_states = mod.extract_prd_states(content, headings, tables)
    prd_perm_pages = mod.extract_prd_permission_pages(headings, tables)

    # 兼容旧格式：独立章节的数据字典、权限汇总、状态机
    # 如果 §5 详细需求说明中没有字段/状态/权限，从独立章节补提取
    if not prd_fields:
        data_dict_start, data_dict_end, _ = mod._find_section_range(headings, "数据字典")
        if data_dict_start:
            for table in _tables_in_range_compat(tables, data_dict_start, data_dict_end):
                headers = table.get("headers", [])
                if not headers:
                    continue
                header_text = "|".join(headers)
                if "字段" not in header_text or "类型" not in header_text:
                    continue
                name_idx = next((j for j, h in enumerate(headers) if "字段" in h), 0)
                type_idx = next((j for j, h in enumerate(headers) if "类型" in h), 1)
                for row in table["rows"]:
                    if not row or not row[0] or row[0] in ("---", "字段"):
                        continue
                    name = row[name_idx].strip() if name_idx < len(row) else ""
                    if name:
                        prd_fields.append(name)
    if not prd_states:
        sm_start, sm_end, _ = mod._find_section_range(headings, "状态机")
        if sm_start:
            for table in _tables_in_range_compat(tables, sm_start, sm_end):
                headers = table.get("headers", [])
                if not headers:
                    continue
                header_text = "|".join(headers)
                if "状态" not in header_text or "触发动作" not in header_text:
                    continue
                state_cols = [j for j, h in enumerate(headers) if "状态" in h]
                for row in table["rows"]:
                    for col_idx in state_cols:
                        if col_idx < len(row) and row[col_idx]:
                            cell = row[col_idx].strip().strip("")
                            if cell and cell not in ("—", "-", "状态", "任意状态"):
                                prd_states.append(cell)
    if not prd_perm_pages:
        perm_start, perm_end, _ = mod._find_section_range(headings, "权限汇总")
        if perm_start:
            for h in headings:
                if h["line"] < perm_start:
                    continue
                if perm_end and h["line"] >= perm_end:
                    continue
                if h["level"] == 3:
                    title = h["title"]
                    cleaned = re.sub(r'^\d+\.\d+\s*', '', title).strip()
                    if cleaned.endswith("模块"):
                        cleaned = cleaned[:-2].strip()
                    if cleaned:
                        prd_perm_pages.append(cleaned)

    # 将 PRD 提取结果封装为 design metadata 格式
    fields = [{"id": f"FIELD-design-{i+1:03d}", "type": "field", "title": t} for i, t in enumerate(prd_fields)]
    pages = [{"id": f"PAGE-design-{i+1:03d}", "type": "page", "title": t} for i, t in enumerate(prd_pages)]
    states = [{"id": f"STATE-design-{i+1:03d}", "type": "state", "title": t} for i, t in enumerate(prd_states)]
    perms = [{"id": f"PERM-design-{i+1:03d}", "type": "permission", "page": t} for i, t in enumerate(prd_perm_pages)]

    FIXTURE_META_DIR.mkdir(parents=True, exist_ok=True)
    (FIXTURE_META_DIR / "fields.json").write_text(json.dumps(fields, ensure_ascii=False, indent=2), encoding="utf-8")
    (FIXTURE_META_DIR / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    (FIXTURE_META_DIR / "states.json").write_text(json.dumps(states, ensure_ascii=False, indent=2), encoding="utf-8")
    (FIXTURE_META_DIR / "permissions.json").write_text(json.dumps(perms, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(fields), len(pages), len(states), len(perms)


def _inject_hallucinations():
    """向 PRD 副本注入 4 类幻觉"""
    content = FIXTURE_PRD.read_text(encoding="utf-8")

    # 1. 幻觉字段（数据字典第一行后加一行，保持 4 列对齐）
    content = content.replace(
        "| 计划 ID | 整数 | 是 | 系统自动生成，主键 |",
        "| 计划 ID | 整数 | 是 | 系统自动生成，主键 |\n| 幻觉字段_X | string | 是 | 不存在的字段 |",
        1,
    )
    # 2. 幻觉页面（权限汇总前加一个粗体块页面，匹配 extract_prd_pages 的解析格式）
    content = content.replace(
        "## 6. 权限汇总",
        "**5.99.1 幻觉页面Z**\n\n这个页面在 design 中不存在。\n\n## 6. 权限汇总",
        1,
    )
    # 3. 幻觉状态（状态机第一行后加一行，保持 6 列对齐）
    content = content.replace(
        "| 任意状态 | — | 管理员 | 手动归档停用 | 已停用 | 管理员操作 |",
        "| 任意状态 | — | 管理员 | 手动归档停用 | 已停用 | 管理员操作 |\n| 幻觉状态X | — | 不存在 | 触发动作 | 已幻觉 | — |",
        1,
    )
    # 4. 幻觉权限页面（在模块级权限矩阵表头追加一列，所有数据行同步追加）
    # 注：将表头第一列从"模块"改为"模块/角色"以匹配 extract_prd_permission_pages 的格式 B 判断（含"角色"关键字）
    old_perm_header = "| 模块 | 集团领导 | 公司领导 | 审计用户 | 外包审计用户 | 被审单位用户 |"
    new_perm_header = "| 模块/角色 | 集团领导 | 公司领导 | 审计用户 | 外包审计用户 | 被审单位用户 | 幻觉权限页Y |"
    content = content.replace(old_perm_header, new_perm_header, 1)
    # 同步给所有数据行追加一列
    import re
    for module_name in ["审计计划", "项目启动", "审计准备", "审计实施", "审计报告", "审计反馈", "审计知识库", "审计总览", "项目档案", "系统管理"]:
        pattern = re.compile(rf'(\| *{re.escape(module_name)} *\| [^\n]+)\n')
        content = pattern.sub(r'\1 | 查看 |\n', content, count=1)

    HALLUCINATION_PRD.write_text(content, encoding="utf-8")


def prepare():
    """生成 design metadata + 注入幻觉的 PRD 副本"""
    if not FIXTURE_PRD.exists():
        print(f"错误：固定测试 PRD 不存在：{FIXTURE_PRD}")
        sys.exit(1)

    print("=== 生成 design metadata ===")
    counts = _gen_design_metadata()
    print(f"fields: {counts[0]}, pages: {counts[1]}, states: {counts[2]}, permissions: {counts[3]}")

    print("\n=== 注入幻觉 ===")
    _inject_hallucinations()
    print(f"幻觉 PRD 已生成：{HALLUCINATION_PRD.name}")

    print("\n下一步：运行 verify 验证幻觉检出")


def verify():
    """运行 prd-consistency-check.py 验证幻觉检出"""
    if not HALLUCINATION_PRD.exists():
        print("错误：幻觉 PRD 不存在，请先运行 prepare")
        sys.exit(1)

    script = PROJECT_ROOT / "scripts" / "python" / "prd-consistency-check.py"
    test_content = HALLUCINATION_PRD.read_text(encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script), "--project-root", str(FIXTURE_DIR)],
        input=test_content, capture_output=True, text=True, encoding="utf-8",
    )

    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"错误：无法解析输出：{e}")
        print(f"stdout: {result.stdout[:500]}")
        print(f"stderr: {result.stderr[:500]}")
        sys.exit(1)

    # 收集各 section 的幻觉项
    section_hallucinated = {}
    all_hallucinated = []
    for key in ("fields", "pages", "states", "permissions"):
        section_hallucinated[key] = report.get(key, {}).get("hallucinated", [])
        for item in section_hallucinated[key]:
            all_hallucinated.append(f"{key}: {item}")

    print("=== 幻觉检出验证 ===")
    print(f"检出幻觉项：{len(all_hallucinated)}")
    for item in all_hallucinated:
        print(f"  - {item}")
    print()

    # 按 section 验证预期幻觉
    found, missing = [], []
    for section, keywords in EXPECTED_HALLUCINATIONS.items():
        section_str = str(section_hallucinated.get(section, []))
        for kw in keywords:
            if kw in section_str:
                found.append(f"{section}: {kw}")
            else:
                missing.append(f"{section}: {kw}")

    total = sum(len(v) for v in EXPECTED_HALLUCINATIONS.values())
    print("=== 预期幻觉验证 ===")
    print(f"预期：{total} 项")
    print(f"已检出：{len(found)} 项 - {', '.join(found)}")
    if missing:
        print(f"未检出：{len(missing)} 项 - {', '.join(missing)}")

    if len(found) == total:
        print(f"\n✓ 验证通过：全部 {total} 类预期幻觉均已检出")
        sys.exit(0)
    else:
        print(f"\n✗ 验证失败：仅检出 {len(found)}/{total} 类预期幻觉")
        sys.exit(1)


def clean():
    """清理测试产物（metadata + 幻觉 PRD），保留固定 PRD 和 design"""
    if HALLUCINATION_PRD.exists():
        HALLUCINATION_PRD.unlink()
    if FIXTURE_META_DIR.exists():
        shutil.rmtree(FIXTURE_META_DIR)
    print("测试产物已清理（固定 PRD 和 design 保留）")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    {"prepare": prepare, "verify": verify, "clean": clean}[cmd]()
