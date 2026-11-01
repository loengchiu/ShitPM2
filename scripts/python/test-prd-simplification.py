#!/usr/bin/env python3
"""PRD Skill 精简后：manifest 装载面、SKILL 规模、规则唯一性和活动行为回归测试。"""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def estimate_tokens(text: str) -> int:
    spec = importlib.util.spec_from_file_location("token_estimate", ROOT / "scripts/python/token_estimate.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.estimate_tokens(text)


def main() -> int:
    manifest = json.loads((ROOT / "contracts/context-loading.manifest.json").read_text(encoding="utf-8-sig"))
    prd = manifest["stages"]["prd"]
    if set(prd["passes"]) != {"writing", "module"}:
        raise AssertionError(f"PRD pass 不符合目标: {prd['passes']}")
    if prd["passes"]["writing"] != [
        "prd-core", "prd-writing-template", "prd-writing-glossary", "prd-writing-versioning",
    ]:
        raise AssertionError(f"writing pack 不符合目标: {prd['passes']['writing']}")
    if prd["passes"]["module"] != ["prd-core", "prd-cards", "prd-writing-examples"]:
        raise AssertionError(f"module pack 不符合目标: {prd['passes']['module']}")

    if prd["packs"]["prd-core"].get("sections") != ["prd-object-unit-spec"]:
        raise AssertionError("PRD 核心 pack 未收敛到对象单元规范")
    if prd["packs"]["prd-writing-examples"].get("sections") != ["prd-object-unit-sample"]:
        raise AssertionError("模块写作未只装载一个真实对象单元样板")
    card_sections = prd["packs"]["prd-cards"].get("card_sections", {})
    if card_sections.get("scenes") != ["prd-verification-scenes"]:
        raise AssertionError(f"scenes 卡章节错误: {card_sections.get('scenes')}")
    if card_sections.get("data") != ["prd-card-data"]:
        raise AssertionError(f"data 卡章节错误: {card_sections.get('data')}")

    module_sections = []
    for pack_name in prd["passes"]["module"]:
        module_sections.extend(prd["packs"][pack_name].get("sections", []))
        for group in prd["packs"][pack_name].get("card_sections", {}).values():
            module_sections.extend(group)
    for forbidden in ("prd-template", "prd-profile", "prd-writing-versioning", "prd-writing-glossary"):
        if forbidden in module_sections:
            raise AssertionError(f"module pass 仍装载非模块写作章节: {forbidden}")
    for forbidden in module_sections:
        if forbidden.startswith("prd-example-"):
            raise AssertionError(f"module pass 仍装载旧页面型示例: {forbidden}")

    roles = manifest["subagent_roles"]
    if "module-verifier" in roles:
        raise AssertionError("module-verifier 仍存在")
    if "prd" in roles["material-reader"].get("allowed", {}):
        raise AssertionError("material-reader 仍拥有 PRD 授权")
    writer = roles["prd-module-writer"]["allowed"]["prd"]
    if writer.get("passes") != ["module"]:
        raise AssertionError(f"prd-module-writer 未收敛到 module: {writer.get('passes')}")
    if writer.get("packs") != ["prd-core", "prd-cards", "prd-writing-examples"]:
        raise AssertionError(f"prd-module-writer pack 白名单未同步: {writer.get('packs')}")

    skill = (ROOT / "skills/spm-prd/SKILL.md").read_text(encoding="utf-8-sig")
    if len(skill.splitlines()) > 180 or estimate_tokens(skill) > 3500:
        raise AssertionError("spm-prd/SKILL.md 超出规模上限")
    for required in (
        "模块概览", "对象单元", "共用规则", "页面功能", "跨对象异常",
        "验收场景直接写输入、预期和精度", "不写规则 ID", "只有一个完整归属位置", "后端只读当前模块",
        "--pass writing", "--pass module",
    ):
        if required not in skill:
            raise AssertionError(f"spm-prd 缺少对象单元写作责任: {required}")
    for forbidden in (
        "4.x.6 功能详细说明", "承接矩阵", "检查回执", "检查 JSON",
        "结果哈希链", "模块草稿只写入",
    ):
        if forbidden in skill:
            raise AssertionError(f"spm-prd 仍包含废弃路径或复杂度: {forbidden}")

    rules = (ROOT / "references/prd-writing-rules.md").read_text(encoding="utf-8-sig")
    for marker in ("prd-object-unit-spec",):
        if f"<!-- context:{marker}:start -->" not in rules or f"<!-- context:{marker}:end -->" not in rules:
            raise AssertionError(f"写作规则缺少装载标记: {marker}")
    for required in (
        "模块结构", "对象单元", "业务过程", "状态迁移", "对象规则", "异常与边界",
        "验收场景", "待确认", "单一归属", "页面功能", "只允许四类表",
        "验收场景表的列为：场景、输入、预期输出、精度或判定", "不写规则 ID",
        "不写作者说明和过程记录", "每条事实只在",
    ):
        if required not in rules:
            raise AssertionError(f"写作规则缺少对象单元规范项: {required}")
    for forbidden in ("## 13", "增加新信息的重复", "初稿", "终稿", "作者说明可"):
        if forbidden in rules:
            raise AssertionError(f"写作规则仍保留无读者价值内容: {forbidden}")

    examples = (ROOT / "references/prd-writing-examples.md").read_text(encoding="utf-8-sig")
    if examples.count("<!-- context:prd-object-unit-sample:start -->") != 1:
        raise AssertionError("对象单元样板标记必须且只能出现一次")
    for forbidden in (
        "prd-example-simple-readonly", "prd-example-workflow-calculation",
        "prd-example-dashboard", "prd-example-multi-role-state", "反例",
    ):
        if forbidden in examples:
            raise AssertionError(f"示例仍保留旧页面型样板: {forbidden}")

    template = (ROOT / "templates/prd.md").read_text(encoding="utf-8-sig")
    template_headings = (
        "模块概览", "对象名称", "业务过程", "状态迁移", "对象规则", "异常与边界",
        "验收场景", "待确认", "共用规则", "页面功能", "跨对象异常",
    )
    matches = [
        re.search(rf"(?m)^#{{3,6}}\s+(?:\d+(?:\.\d+)*\s+)?{re.escape(title)}\s*$", template)
        for title in template_headings
    ]
    positions = [match.start() if match else -1 for match in matches]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        raise AssertionError(f"PRD 模板对象单元顺序错误: {positions}")
    for forbidden in ("4.x.6", "规则 ID：", "引用规则 ID", "所属对象：", "只读承接", "验收标准"):
        if forbidden in template:
            raise AssertionError(f"PRD 模板仍保留旧结构或追溯标注: {forbidden}")

    review = (ROOT / "contracts/prd-review-checklist.md").read_text(encoding="utf-8-sig")
    for required in (
        "读者任务试读", "后端任务", "前端任务", "测试任务", "单一归属抽查",
        "页面功能", "状态迁移", "无规则 ID", "未评估",
    ):
        if required not in review:
            raise AssertionError(f"Review 清单缺少对象单元审查项: {required}")
    for forbidden in ("4.x.6", "4.x.9", "详细需求说明语义专项检查", "PRD 内嵌引用"):
        if forbidden in review:
            raise AssertionError(f"Review 清单仍绑定旧结构: {forbidden}")

    verification = (ROOT / "references/verification-and-oracle.md").read_text(encoding="utf-8-sig")
    for required in ("对象单元的“验收场景”", "写输入、预期输出和精度或判定", "不写规则 ID", "作者核对"):
        if required not in verification:
            raise AssertionError(f"验证包与 PRD 边界缺少: {required}")
    for forbidden in ("4.x.9", "4.x.5", "4.x.6", "引用验证包中的规则 ID"):
        if forbidden in verification:
            raise AssertionError(f"验证包仍要求 PRD 使用固定编号或规则 ID: {forbidden}")

    consistency_source = (ROOT / "scripts/python/prd-consistency-check.py").read_text(encoding="utf-8-sig")
    for required in ("evaluate_prd_object_structure", "页面功能", "状态迁移", "not_evaluated"):
        if required not in consistency_source:
            raise AssertionError(f"一致性检查缺少标题名定位入口: {required}")
    for forbidden in ("4.x.6", "4.x.3", "4.x.9"):
        if forbidden in consistency_source:
            raise AssertionError(f"一致性检查仍绑定固定编号: {forbidden}")
    if 'if exit_reason == "deterministic_conflict":' not in consistency_source:
        raise AssertionError("一致性检查退出语义未收窄到 deterministic_conflict")

    for old_pass in ("plan", "integration", "verification"):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/python/context-pack.py"),
             "--bundle-root", str(ROOT), "--project-root", str(ROOT),
             "--stage", "prd", "--pass", old_pass],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode == 0 or "不存在 pass" not in result.stderr:
            raise AssertionError(f"废弃 pass 未被清晰拒绝: {old_pass}, {result.returncode}, {result.stderr}")

    print("test-prd-simplification: PASS（对象单元规范、单一样板、标题名检查与旧结构未评估）")
    return 0


def test_prd_simplification() -> None:
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
