from __future__ import annotations
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("design_orchestrator", SCRIPT.with_name("design-orchestrator.py"))
orch = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(orch)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_output(root: Path, action: dict[str, Any]) -> list[str]:
    written: list[str] = []
    revision = orch.read_input_manifest(root)[0]
    material_revision = orch.material_revision(root, revision) if revision else "sha256:unknown"
    for raw in action.get("expected_outputs", []):
        path = root / raw
        path.parent.mkdir(parents=True, exist_ok=True)
        if raw.endswith("align.md"):
            write_text(path, "# 对齐稿\n\n## 一、需求事实\n\n- 当前输入已记录，详细材料事实交由后续分析继续承接。\n\n## 六、待确认问题\n\n- 无。\n")
        elif raw.endswith("design.md"):
            simple = action.get("mode") == "simple"
            content = (
                "# 产品方案 Design\n\n"
                "## 一、方案摘要\n\n"
                "完成目标、范围、主路径、关键规则、必要状态与权限、功能、数据、异常和验收的最小闭环。\n\n"
                "## 二、用户、场景与目标\n\n"
                "覆盖主要用户的主路径和异常恢复。\n\n"
                "## 七、页面、区块、字段与操作设计\n\n"
                "### 页面清单（可选速览）\n\n"
                "| 页面 | 用户任务 | 适用角色 | 主要入口/去向 |\n"
                "| --- | --- | --- | --- |\n"
                "| 业务处理 | 填写并提交业务信息 | 业务人员 | 工作台进入，提交后进入处理结果页 |\n\n"
                "### 页面：业务处理\n\n"
                "- 页面目的：完成业务处理\n"
                "- 适用角色：业务人员、管理员\n"
                "- 进入条件：用户已登录\n"
                "- 数据范围：本人负责范围；管理员可查看组织范围\n"
                "- 主要状态：草稿、处理中、审批中、已通过、已驳回、已撤销、失败待重试\n\n"
                "#### 区块：基本信息\n\n"
                "- 区块目的：展示和填写业务信息\n\n"
                "##### 字段表\n\n"
                "| 字段名称 | 业务含义 | 字段来源 | 展示条件 | 输入与编辑规则 | 取值与默认规则 | 交互方式 | 校验与反馈 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| 业务名称 | 业务对象名称 | 用户输入 | 始终展示 | 草稿状态可编辑，提交时必填 | 默认空值 | 文本输入 | 不能为空，错误时提示 |\n\n"
                "#### 页面操作\n\n"
                "- 区块目的：定义本页面可执行的业务操作及其结果。\n\n"
                "##### 操作表\n\n"
                "| 操作 | 适用角色 | 入口/触发方式 | 输入（字段级） | 展示与可用条件 | 是否二次确认 | 成功结果 | 数据与状态变化 | 失败与恢复 | 后续去向 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| 提交 | 业务人员 | 页面上“提交”按钮 | 见基本信息字段表 | 信息完整时可用 | 否 | 进入审批中 | 状态变为审批中 | 缺少信息时保留输入并提示 | 进入处理结果页 |\n"
                "| 审批 | 管理员 | 页面上“审批”按钮 | 见审批意见字段 | 在本人负责组织范围内可用 | 是 | 进入已通过或已驳回 | 更新审批结果 | 权限不足或外部失败时保留待处理状态并允许重试 | 返回业务处理页 |\n"
                "| 撤销/重提 | 业务人员 | 页面上“撤销/重提”链接 | 无新增输入 | 满足状态条件时可用 | 是 | 撤销或重新进入审批中 | 记录状态变化 | 不满足条件时提示原因 | 返回处理结果页 |\n\n"
                "## 九、成功与验收\n\n"
                "主路径、异常、权限、状态变化和数据范围均可验证。\n"
            )
            if simple:
                content = content.replace("、审批中、已通过、已驳回、已撤销", "").replace("| 审批 | 管理员 | 页面上“审批”按钮 | 见审批意见字段 | 在本人负责组织范围内可用 | 是 | 进入已通过或已驳回 | 更新审批结果 | 权限不足或外部失败时保留待处理状态并允许重试 | 返回业务处理页 |\n", "").replace("| 撤销/重提 | 业务人员 | 页面上“撤销/重提”链接 | 无新增输入 | 满足状态条件时可用 | 是 | 撤销或重新进入审批中 | 记录状态变化 | 不满足条件时提示原因 | 返回处理结果页 |\n", "")
            write_text(path, content)
        elif raw.endswith("decision-notes.md"):
            write_text(path, "# 决策记录\n\n## 设计决策\n- 选择最小闭环。\n\n## 偏离\n- 材料冲突和缺失信息保留为待确认事项，不静默拍板。\n\n## 权衡\n- 外部失败采用保留输入并允许重试。\n\n## 待确认\n- 无。\n")
        elif raw.endswith(".json"):
            value: dict[str, Any] = {"schema_version": "design-analysis/v2", "task_id": action.get("task_id"), "input_fingerprint": action.get("input_hashes", {}).get("__input_hash__"), "status": "completed", "conclusions": [], "conflicts": [], "questions": [], "coverage": [action.get("task_id")], "source_refs": [], "payload": {}}
            if action.get("task_kind") == "align":
                value = {
                    "blocking_gaps": [],
                    "needs_ask_back": False,
                    "ask_back_reason": None,
                    "judgement_note": "合成测试中的 Align 已记录用户输入和材料范围。",
                    "last_updated_at": orch.now(),
                }
            elif action.get("task_kind") == "material_preparation":
                command = action.get("command") or {}
                script_name = Path(command.get("script", "source-index.py")).name
                script = SCRIPT.with_name(script_name)
                result = subprocess.run(
                    [sys.executable, str(script), *command.get("args", [])],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stdout + result.stderr)
                written.extend(raw for raw in action.get("expected_outputs", []) if (root / raw).exists())
                continue
            if action.get("task_kind") == "material_fact_extraction":
                item = action.get("input_files", [""])[0]
                source_hash = orch.safe_file_hash(root, item)
                line_end = max(1, len((root / item).read_text(encoding="utf-8").splitlines()))
                value = {
                    "schema_version": "material-fact/v2",
                    "source_path": item,
                    "source_hash": source_hash,
                    "material_revision": material_revision,
                    "facts": [{
                        "statement": "合成事实",
                        "source": {"path": item, "sha256": source_hash, "line_start": 1, "line_end": line_end},
                    }],
                }
            elif action.get("task_kind") == "material_merge":
                confirmed_facts = []
                for item in (orch.read_input_manifest(root)[0] or {}).get("material_inputs", []):
                    source_id = orch.source_id_for(item)
                    part = orch.read_json(orch.material_dir(root) / "facts" / f"{source_id}.json") or {}
                    source_hash = part.get("source_hash") or orch.safe_file_hash(root, item)
                    for fact in part.get("facts", []):
                        confirmed_facts.append({
                            "statement": fact.get("statement") or fact.get("fact") or "合成事实",
                            "source": {
                                "path": item,
                                "sha256": source_hash,
                                "line_start": 1,
                                "line_end": max(1, len((root / item).read_text(encoding="utf-8").splitlines())),
                            },
                        })
                value = {
                    "version": 1,
                    "material_revision": material_revision,
                    "confirmed_facts": confirmed_facts,
                    "source_conflicts": [],
                    "missing_information": [],
                    "non_derivable_items": [],
                }
            orch.write_json(path, value)
        else:
            write_text(path, "generated")
        written.append(raw)
    return written


def parse_budgets(values: list[str]) -> dict[str, int]:
    result = {}
    for value in values:
        if "=" in value:
            key, count = value.split("=", 1)
            result[key] = int(count)
    return result


def run(args: argparse.Namespace) -> int:
    root = args.project_root.resolve()
    budgets = parse_budgets(args.fail_on)
    used: dict[str, int] = {}
    answers = {}
    for item in args.answer:
        if "=" in item:
            key, value = item.split("=", 1)
            answers[key] = value
    steps = 0
    trace_path = root / ".workflow/runtime/context/design/host-execution-log.jsonl"
    while steps < args.max_steps:
        steps += 1
        preview = orch.next_action(root)
        if preview.get("state") == "waiting_user":
            actions = preview.get("ready_actions", [])
            if not actions:
                return 2
            unresolved = []
            for action in actions:
                question_id = action.get("question", {}).get("question_id") or action.get("action_id", "").split(":", 1)[-1]
                if question_id in answers:
                    orch.handle_answer(root, question_id, answers[question_id])
                elif action.get("action_id") == "select-mode":
                    orch.handle_answer(root, "mode-selection", args.mode_answer)
                else:
                    unresolved.append(question_id)
            if unresolved:
                return 2
            continue
        if preview.get("state") == "completed":
            return 0
        if preview.get("state") != "ready":
            return 1
        actions = list(preview.get("ready_actions", []))
        ready_batch = [action.get("task_id", action.get("action_id")) for action in actions]
        process_actions = list(reversed(actions)) if args.reverse else actions
        for action in process_actions:
            task_id = action.get("task_id", action.get("action_id"))
            program_declared = {
                "action_id": action.get("action_id"),
                "task_id": task_id,
                "task_kind": action.get("task_kind"),
                "stage": action.get("rule_pack_ref", {}).get("stage"),
                "input_files": action.get("input_files", []),
                "allowed_evidence_ranges": action.get("allowed_evidence_ranges", []),
                "fork_context": action.get("fork_context"),
                "expected_outputs": action.get("expected_outputs", []),
                "command": action.get("command"),
            }
            stage_count = used.get(task_id, 0)
            if args.interrupt_after and args.interrupt_after == task_id:
                return 75
            started = time.perf_counter()
            action_card_chars = len(json.dumps(action, ensure_ascii=False, separators=(",", ":")))
            raw_model_reads = sum(1 for raw in action.get("input_files", []) if raw.startswith("materials/")) if action.get("task_kind") == "material_fact_extraction" else 0
            if stage_count < budgets.get(task_id, 0):
                used[task_id] = stage_count + 1
                fingerprint = f"sha256:failure-{task_id}"
                accepted = orch.handle_accept(root, action["action_id"], "failure", "模拟失败", fingerprint)
                if not accepted.get("accepted"):
                    return 1
                finished = time.perf_counter()
                event = {
                    "ready_batch": ready_batch,
                    "program_declared": program_declared,
                    "host_execution": {
                        "isolation_status": "simulated_only",
                        "program_reads": action.get("input_files", []),
                        "declared_agent_reads": action.get("input_files", []),
                        "actual_agent_reads": [],
                        "written_files": [],
                    },
                    "result": "failure",
                    "error": "模拟失败",
                    "metrics": {
                        "started_at": started,
                        "finished_at": finished,
                        "duration_ms": round((finished - started) * 1000, 3),
                        "action_card_chars": action_card_chars,
                        "main_agent_receipt_chars": len(json.dumps(accepted, ensure_ascii=False, separators=(",", ":"))),
                        "child_body_return_chars": 0,
                        "material_raw_model_reads": raw_model_reads,
                        "estimated": False,
                        "host_real_token_data": False,
                    },
                }
                with trace_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
                continue
            written = write_output(root, action)
            accepted = orch.handle_accept(root, action["action_id"], "success", None, None)
            if not accepted.get("accepted"):
                return 1
            finished = time.perf_counter()
            event = {
                "ready_batch": ready_batch,
                "program_declared": program_declared,
                "host_execution": {
                    "isolation_status": "simulated_only",
                    "program_reads": action.get("input_files", []),
                    "declared_agent_reads": action.get("input_files", []),
                    "actual_agent_reads": [],
                    "written_files": written,
                },
                "result": "success",
                "metrics": {
                    "started_at": started,
                    "finished_at": finished,
                    "duration_ms": round((finished - started) * 1000, 3),
                    "action_card_chars": action_card_chars,
                    "main_agent_receipt_chars": len(json.dumps(accepted, ensure_ascii=False, separators=(",", ":"))),
                    "child_body_return_chars": 0,
                    "material_raw_model_reads": raw_model_reads,
                    "estimated": False,
                    "host_real_token_data": False,
                },
            }
            with trace_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return 75


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--fail-on", action="append", default=[])
    parser.add_argument("--interrupt-after")
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--answer", action="append", default=[])
    parser.add_argument("--mode-answer", choices=("simple", "full"), default="full")
    args = parser.parse_args()
    try:
        return run(args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
