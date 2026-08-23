#!/usr/bin/env python3
"""PRD Skill 精简后：manifest 装载面、SKILL 规模、规则唯一性和活动行为回归测试。"""

import importlib.util
import json
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
        "prd-core", "prd-writing-structure", "prd-writing-template",
        "prd-writing-glossary", "prd-writing-versioning",
    ]:
        raise AssertionError(f"writing pack 不符合精简装载面: {prd['passes']['writing']}")
    if prd["passes"]["module"] != [
        "prd-core", "prd-writing-spec", "prd-cards", "prd-writing-examples",
    ]:
        raise AssertionError(f"module pack 不符合精简装载面: {prd['passes']['module']}")

    # module pass 不装载完整模板、完整 profile、完整版本规则、完整场景清单和反例组
    examples_pack = prd["packs"]["prd-writing-examples"]
    if set(examples_pack.get("sections", [])) != {"prd-example-simple-readonly", "prd-example-multi-role-state"}:
        raise AssertionError(f"module pass 自动示例不符合两份正例: {examples_pack.get('sections')}")
    if "prd-example-dashboard" in examples_pack.get("sections", []):
        raise AssertionError("看板示例仍被 module pass 自动装载")
    for required_key in (
        "dashboard", "list-detail-query", "form-config", "multi-role-state",
        "mobile-cross-terminal", "external-auto", "simple-readonly",
    ):
        if required_key not in examples_pack.get("example_sections", {}):
            raise AssertionError(f"按需 --example 键缺失: {required_key}")
    module_sections = []
    for pack_name in prd["passes"]["module"]:
        pack = prd["packs"][pack_name]
        module_sections.extend(pack.get("sections", []))
        for group in pack.get("card_sections", {}).values():
            module_sections.extend(group)
    for forbidden in ("prd-template", "prd-profile", "prd-writing-versioning", "prd-writing-glossary"):
        if forbidden in module_sections:
            raise AssertionError(f"module pass 仍装载非模块写作章节: {forbidden}")

    roles = manifest["subagent_roles"]
    if "module-verifier" in roles:
        raise AssertionError("module-verifier 仍存在")
    if "prd" in roles["material-reader"].get("allowed", {}):
        raise AssertionError("material-reader 仍拥有 PRD 授权")
    if roles["prd-module-writer"]["allowed"]["prd"]["passes"] != ["module"]:
        raise AssertionError("prd-module-writer 未收敛到 module")
    if roles["prd-module-writer"]["allowed"]["prd"]["packs"] != [
        "prd-core", "prd-writing-spec", "prd-cards", "prd-writing-examples",
    ]:
        raise AssertionError(f"prd-module-writer pack 白名单未同步: {roles['prd-module-writer']['allowed']['prd']['packs']}")
    if "生成内部 PRD 草稿" in roles["prd-module-writer"]["purpose"]:
        raise AssertionError("prd-module-writer 仍被授权生成内部 PRD 草稿")

    subagent_contract = (ROOT / "contracts/subagent-context-contract.md").read_text(encoding="utf-8-sig")
    if "可以产生内部模块草稿" in subagent_contract:
        raise AssertionError("Sub-agent 契约仍允许产生内部模块草稿")
    if "prd-writing-spec" not in subagent_contract:
        raise AssertionError("Sub-agent 契约未同步 prd-writing-spec 白名单")

    skill = (ROOT / "skills/spm-prd/SKILL.md").read_text(encoding="utf-8-sig")
    skill_lines = len(skill.splitlines())
    skill_tokens = estimate_tokens(skill)
    if skill_lines > 160:
        raise AssertionError(f"SKILL.md 超过 160 行: {skill_lines}")
    if skill_tokens > 3000:
        raise AssertionError(f"SKILL.md 超过约 3000 token: {skill_tokens}")
    for forbidden in (
        "--pass plan", "--pass integration", "--pass verification",
        "prototype-structure.py", "检查回执", "机器签名", "综合门禁", "检查 JSON", "结果哈希链",
        "承接矩阵", "普通 PRD 只执行一次", "只用于超大型 PRD",
        "模块草稿只写入", "主 Agent 最终只写入一次完整 PRD", "先完整读取 Design 事实闭包",
    ):
        if forbidden in skill:
            raise AssertionError(f"Skill 仍包含废弃路径或复杂度: {forbidden}")
    if "--pass writing" not in skill or "--pass module" not in skill:
        raise AssertionError("Skill 未说明 writing/module 路径")
    for required in (
        "全量分片", "不再根据 Design 大小", "阶段 A：全局扫描", "阶段 B：建立最终 PRD 骨架",
        "阶段 C：模块分片写入", "阶段 D：有限范围整合", "4.x.6 功能详细说明",
        "中断恢复", "不依赖 subagent", "无活动事务",
        "重新生成", "局部修复",
    ):
        if required not in skill:
            raise AssertionError(f"Skill 缺少全量分片规则: {required}")
    for required in (
        "业务判断链", "动作按业务结果重组", "动作按复杂度", "数据型功能",
        "高影响未知", "直接回读", "详细需求说明写作规范", "--example <键>",
        "跨页面推进", "跨角色协作", "跨系统交互", "关键业务状态变化",
        "output/prd/diagrams/", "2 倍分辨率", "流程图只辅助理解",
    ):
        if required not in skill:
            raise AssertionError(f"Skill 缺少核心语义责任: {required}")
    for required in (
        "设计集清单", "目标业务模块",
        "--module <模块名>", "禁止一次性全读整套 Design",
        "片段不得包含无关模块内容", "sed 1,$p",
    ):
        if required not in skill:
            raise AssertionError(f"Skill 缺少 Design 分片读取指令: {required}")

    rules = (ROOT / "references/prd-writing-rules.md").read_text(encoding="utf-8-sig")
    for marker in ("prd-writing-structure", "prd-writing-spec", "prd-core-boundary"):
        if f"<!-- context:{marker}:start -->" not in rules or f"<!-- context:{marker}:end -->" not in rules:
            raise AssertionError(f"写作规则缺少装载标记: {marker}")
    for required in (
        "详细需求说明写作规范", "研发只读", "自然语言硬约束",
        "按实际适用覆盖", "前端事实承接", "后端事实承接",
        "动作按业务结果重组", "动作按复杂度写", "跨前后端的完整业务链",
        "事实边界与信息密度", "不得从“立即生效”等生效描述推导",
        "行首标签", "每个有页面或业务动作的功能模块必须包含 `4.x.6 功能详细说明`",
        "业务流程图", "跨页面推进", "每个命中模块至少一张图",
        "output/prd/diagrams/<图名>.drawio", "2 倍分辨率", "流程图只辅助理解",
    ):
        if required not in rules:
            raise AssertionError(f"写作规则缺少精简后唯一规范项: {required}")

    scenes = (ROOT / "references/prd-scene-checklist.md").read_text(encoding="utf-8-sig")
    for required in (
        "适用 / 不适用 / 待确认",
        "谁在什么业务前提和状态下操作", "判断依据来自哪里",
        "下一步由谁继续", "是否新增 Design 未确认事实",
    ):
        if required not in scenes:
            raise AssertionError(f"场景清单缺少语义自检项: {required}")
    if "context-pack.py --module" in scenes:
        raise AssertionError("场景清单仍包含 context pack 运行记录自检")

    examples = (ROOT / "references/prd-writing-examples.md").read_text(encoding="utf-8-sig")
    for marker in (
        "prd-example-simple-readonly", "prd-example-dashboard",
        "prd-example-list-detail-query", "prd-example-form-config",
        "prd-example-multi-role-state", "prd-example-mobile-cross-terminal",
        "prd-example-external-auto",
    ):
        if f"<!-- context:{marker}:start -->" not in examples:
            raise AssertionError(f"示例缺少页面类型章节: {marker}")
    if "反例" in examples:
        raise AssertionError("示例不应保留反例（坏味道由 lint 识别）")

    template = (ROOT / "templates/prd.md").read_text(encoding="utf-8-sig")
    for required in (
        "功能模块必需章节", "不能以“无内容”为由省略", "页面字段表只补充",
        "跨页面推进", "每个命中模块至少一张图", "2 倍分辨率", "不使用 Mermaid",
    ):
        if required not in template:
            raise AssertionError(f"PRD 模板缺少 4.x.6 硬约束: {required}")
    for required in (
        "###### Design 中定义的页面名称", "**动作名称**",
        "PC 管理端页面名称不加", "（移动端）",
    ):
        if required not in template:
            raise AssertionError(f"PRD 模板缺少新页面/动作格式: {required}")
    for forbidden in ("**页面名称**", "###### 动作标题：业务结果", "车辆信息记录（管理端）"):
        if forbidden in template:
            raise AssertionError(f"PRD 模板仍保留旧格式: {forbidden}")

    review = (ROOT / "contracts/prd-review-checklist.md").read_text(encoding="utf-8-sig")
    for required in (
        "无效引用", "时间范围", "页面操作承接与合并", "检查后修改", "格式统一",
        "页面展示行为完整", "自动动作失败闭环", "删除传播完整", "枚举和独立上限有来源",
        "Design 全读痕迹", "上下文爆栈", "一次性全读整套 Design",
        "详细需求说明语义专项检查", "数据范围与统计口径专项检查",
        "跨页面推进", "2 倍 PNG", "PRD 内嵌引用",
    ):
        if required not in review:
            raise AssertionError(f"Review 清单缺少本轮检查项: {required}")

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

    print("test-prd-simplification: PASS（manifest 精简装载面、SKILL 规模、规则唯一性、示例按需装载和旧 pass 拒绝）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
