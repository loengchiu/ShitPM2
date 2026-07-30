#!/usr/bin/env python3
"""PRD 极简流程的配置、Skill 和活动行为回归测试。"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    manifest = json.loads((ROOT / "contracts/context-loading.manifest.json").read_text(encoding="utf-8-sig"))
    prd = manifest["stages"]["prd"]
    if set(prd["passes"]) != {"writing", "module"}:
        raise AssertionError(f"PRD pass 不符合目标: {prd['passes']}")
    if prd["passes"]["writing"] != [
        "prd-core", "prd-writing-structure", "prd-writing-action",
        "prd-writing-glossary", "prd-writing-versioning", "prd-verification",
    ]:
        raise AssertionError(f"writing pack 不完整: {prd['passes']['writing']}")
    if prd["passes"]["module"] != [
        "prd-core", "prd-writing-structure", "prd-writing-action", "prd-cards",
    ]:
        raise AssertionError(f"module pack 不符合目标: {prd['passes']['module']}")

    roles = manifest["subagent_roles"]
    if "module-verifier" in roles:
        raise AssertionError("module-verifier 仍存在")
    if "prd" in roles["material-reader"].get("allowed", {}):
        raise AssertionError("material-reader 仍拥有 PRD 授权")
    if roles["prd-module-writer"]["allowed"]["prd"]["passes"] != ["module"]:
        raise AssertionError("prd-module-writer 未收敛到 module")

    skill = (ROOT / "skills/spm-prd/SKILL.md").read_text(encoding="utf-8-sig")
    for forbidden in (
        "--pass plan", "--pass integration", "--pass verification",
        "prototype-structure.py", "检查回执", "机器签名", "综合门禁", "检查 JSON", "结果哈希链",
        "承接矩阵",
    ):
        if forbidden in skill:
            raise AssertionError(f"Skill 仍包含废弃复杂度: {forbidden}")
    if "--pass writing" not in skill or "--pass module" not in skill:
        raise AssertionError("Skill 未说明 writing/module 路径")
    if "普通 PRD" not in skill or "只执行一次 `writing`" not in skill:
        raise AssertionError("Skill 未明确普通 PRD 只走 writing")
    if "只用于超大型 PRD" not in skill:
        raise AssertionError("Skill 未明确 module 只用于超大型 PRD")

    stage_source = (ROOT / "scripts/python/stage-context.py").read_text(encoding="utf-8-sig")
    if '"scripts/python/prototype-structure.py"' in stage_source:
        raise AssertionError("PRD 最小读取集合仍包含 Prototype 结构提取")

    consistency_source = (ROOT / "scripts/python/prd-consistency-check.py").read_text(encoding="utf-8-sig")
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

    print("test-prd-simplification: PASS（manifest、角色、Skill、Prototype 依赖和旧 pass 拒绝）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
