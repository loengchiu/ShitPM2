#!/usr/bin/env python3
"""PRD 全量分片流程的配置、Skill 和活动行为回归测试。"""

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
    if "生成内部 PRD 草稿" in roles["prd-module-writer"]["purpose"]:
        raise AssertionError("prd-module-writer 仍被授权生成内部 PRD 草稿")

    subagent_contract = (ROOT / "contracts/subagent-context-contract.md").read_text(encoding="utf-8-sig")
    if "可以产生内部模块草稿" in subagent_contract:
        raise AssertionError("Sub-agent 契约仍允许产生内部模块草稿")

    skill = (ROOT / "skills/spm-prd/SKILL.md").read_text(encoding="utf-8-sig")
    for forbidden in (
        "--pass plan", "--pass integration", "--pass verification",
        "prototype-structure.py", "检查回执", "机器签名", "综合门禁", "检查 JSON", "结果哈希链",
        "承接矩阵", "普通 PRD 只执行一次", "只用于超大型 PRD",
        "模块草稿只写入", "主 Agent 最终只写入一次完整 PRD", "先完整读取确认版 Design",
    ):
        if forbidden in skill:
            raise AssertionError(f"Skill 仍包含废弃路径或复杂度: {forbidden}")
    if "--pass writing" not in skill or "--pass module" not in skill:
        raise AssertionError("Skill 未说明 writing/module 路径")
    for required in (
        "全量分片", "不再根据 Design 大小", "阶段 A：全局扫描", "阶段 B：建立最终 PRD 骨架",
        "阶段 C：模块分片写入", "阶段 D：有限范围整合", "4.x.6 功能详细说明",
        "中断恢复", "不依赖 subagent",
    ):
        if required not in skill:
            raise AssertionError(f"Skill 缺少全量分片规则: {required}")

    template = (ROOT / "templates/prd.md").read_text(encoding="utf-8-sig")
    for required in (
        "功能模块必需章节", "不能以“无内容”为由省略", "页面字段表只补充",
    ):
        if required not in template:
            raise AssertionError(f"PRD 模板缺少 4.x.6 硬约束: {required}")

    rules = (ROOT / "references/prd-writing-rules.md").read_text(encoding="utf-8-sig")
    for required in (
        "所有 PRD 默认分片写作", "分片必须直接写入最终 `output/prd/prd.md`",
        "不得整篇重写", "每个功能模块必须包含 `4.x.6 功能详细说明`",
        "从最终 `prd.md` 的章节骨架", "不依赖 subagent",
    ):
        if required not in rules:
            raise AssertionError(f"写作规则缺少全量分片硬规则: {required}")

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

    print("test-prd-simplification: PASS（manifest、角色、Skill、模板、写作规则、Prototype 依赖和旧 pass 拒绝）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
