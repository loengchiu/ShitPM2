from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ORCH_PATH = ROOT / "scripts/python/design-orchestrator.py"
HOST_PATH = ROOT / "scripts/python/fake-design-host.py"
spec = importlib.util.spec_from_file_location("design_orchestrator", ORCH_PATH)
orch = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(orch)

PROJECTS = {
    "simple-display": {
        "mode": "simple",
        "materials": {"01-page.md": "# 展示页面\n展示设备名称、状态和位置。\n", "02-fields.md": "# 字段\n设备名称为只读字段。\n"},
        "required": ["页面：业务处理", "字段表", "操作表"],
    },
    "business-workflow": {
        "mode": "full",
        "materials": {"01-roles.md": "# 角色权限\n员工提交申请，管理员审批并查看组织范围数据。\n", "02-process.md": "# 流程状态\n草稿、处理中、失败待重试。页面支持提交操作。\n"},
        "required": ["业务人员", "管理员", "审批中", "已驳回", "数据范围"],
    },
    "complex-conflict": {
        "mode": "full",
        "materials": {"01-conflict.md": "# 材料冲突\n审批材料写成通过即预占，库存材料写成锁定成功后才预占。\n", "02-missing.md": "# 缺失信息\n逾期后是否允许再次申请尚未确认。\n", "03-exception.md": "# 异常分支\n外部锁定失败时需要释放或重试。\n"},
        "required": ["已撤销", "重提", "外部失败", "失败与恢复"],
    },
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_project(category: str) -> tuple[tempfile.TemporaryDirectory, Path]:
    config = PROJECTS[category]
    holder = tempfile.TemporaryDirectory(prefix=f"spm-simplification-{category}-")
    root = Path(holder.name)
    materials = root / "materials"
    materials.mkdir(parents=True)
    for name, content in config["materials"].items():
        (materials / name).write_text(content, encoding="utf-8")
    orch.BUNDLE_ROOT = root / "bundle"
    paths = [str(path) for path in sorted(materials.glob("*.md"))]
    orch.init_project(root, f"合成项目：{category}", config["mode"], paths)
    return holder, root


def run_host(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SHITPM_BUNDLE_ROOT"] = str(root / "bundle")
    return subprocess.run(
        [sys.executable, str(HOST_PATH), "--project-root", str(root), "--max-steps", "300", *extra],
        text=True,
        capture_output=True,
        encoding="utf-8",
        env=env,
        timeout=120,
    )


def events(root: Path) -> list[dict[str, Any]]:
    path = root / ".workflow/runtime/context/design/host-execution-log.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_three_synthetic_scenarios() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for category, config in PROJECTS.items():
        holder, root = make_project(category)
        try:
            run = run_host(root)
            check(run.returncode == 0, f"{category} 未完成：{run.stdout}{run.stderr}")
            design = (root / "output/design/design.md").read_text(encoding="utf-8")
            check(re.search(r"^### 页面：", design, re.M) is not None, f"{category} 缺少页面结构")
            check(re.search(r"^##### 字段表", design, re.M) is not None, f"{category} 缺少字段表")
            check(re.search(r"^##### 操作表", design, re.M) is not None, f"{category} 缺少操作表")
            for term in config["required"]:
                check(term in design, f"{category} 缺少关键设计信息：{term}")
            ids = [event["program_declared"]["task_id"] for event in events(root)]
            final_task = "simple-design" if config["mode"] == "simple" else "design-editor"
            check(ids[-1] == final_task, f"{category} 最终动作错误：{ids}")
            check(not any("review" in task or "check" in task or "compile" in task or "report" in task for task in ids), f"{category} 出现生成后检查动作")
            result[category] = {"mode": config["mode"], "completed": True, "tasks": len(ids), "final_task": final_task}
        finally:
            holder.cleanup()
    return result


def test_graph_size_and_removed_mode() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for category, config in PROJECTS.items():
        holder, root = make_project(category)
        try:
            manifest, error = orch.read_input_manifest(root)
            check(manifest is not None, error or "输入清单不存在")
            tasks = orch.task_map(config["mode"], manifest)
            source_count = len(manifest["material_inputs"])
            expected_count = source_count + (4 if config["mode"] == "simple" else 7)
            check(len(tasks) == expected_count, f"{category} 任务数量错误：{len(tasks)} != {expected_count}")
            check(("full" + "-layered") not in orch.SUPPORTED_MODES, "废弃模式不得再是模式")
            result[category] = {"task_count": len(tasks), "expected": expected_count}
        finally:
            holder.cleanup()
    return result


def test_recovery_and_acceptance_boundary() -> dict[str, Any]:
    holder, root = make_project("complex-conflict")
    try:
        cold = orch.next_action(root)["ready_actions"][0]
        rejected = orch.handle_accept(root, cold["action_id"], "success", None, None)
        check(not rejected.get("accepted"), "缺少材料索引输出时不能接受动作")
        source = root / "materials/01-conflict.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n陈旧动作测试。", encoding="utf-8")
        stale = orch.handle_accept(root, cold["action_id"], "success", None, None)
        check(not stale.get("accepted"), "输入变化后不能接受陈旧动作")

        run = run_host(root)
        check(run.returncode == 0, run.stdout + run.stderr)
        design_action = next(action for action in orch.next_action(root).get("ready_actions", []) if action["task_id"] == "design-editor") if orch.next_action(root).get("ready_actions") else None
        check(design_action is None, "完成后不应重复生成 Design 动作")
        check(orch.handle_status(root)["state"] == "completed", "恢复后必须 completed")
        return {"completed": True, "stale_rejected": True}
    finally:
        holder.cleanup()


def test_cross_layer_contracts_are_synced() -> dict[str, Any]:
    required = {
        ROOT / "skills/spm-design/SKILL.md": ["横切能力与事实状态识别", "已定义、局部定义、未定义或冲突", "自动动作"],
        ROOT / "templates/design.md": ["所属业务侧", "页面展示行为", "自动动作与生命周期传播"],
        ROOT / "references/design-writing.md": ["页面展示行为必须按实际适用情况落地", "横切能力、自动动作与生命周期"],
        ROOT / "references/design-state-format.md": ["页面状态与状态驱动展示", "置灰操作及原因"],
        ROOT / "skills/spm-design-review/SKILL.md": ["横切能力", "删除传播", "独立上限"],
        ROOT / "contracts/design-review-checklist.md": ["X1. 横切能力事实状态可判断", "X4. 自动动作失败闭环", "X6. 枚举与上限有来源"],
    }
    missing = []
    for path, terms in required.items():
        text = path.read_text(encoding="utf-8-sig")
        for term in terms:
            if term not in text:
                missing.append(f"{path.relative_to(ROOT)} 缺少 {term}")
    check(not missing, "Design 跨层契约未同步：" + "；".join(missing))
    return {"checked_files": len(required), "passed": True}


def main() -> int:
    try:
        output = {
            "scenarios": test_three_synthetic_scenarios(),
            "graph": test_graph_size_and_removed_mode(),
            "recovery": test_recovery_and_acceptance_boundary(),
            "cross_layer_contracts": test_cross_layer_contracts_are_synced(),
        }
    except Exception as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"passed": True, **output}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
