#!/usr/bin/env python3
"""state-machine-check.py — 状态机闭环结构层校验（ShitPM: 按需检查）

ShitPM 状态：此脚本保留为按需检查，不作为所有生成任务的硬门禁。
- 新主流程不默认调用此脚本。
- Review skill 可显式调用此脚本做结构层校验。
- ShitPM：无 states.json 时降级为基于 design.md 解析（调用 stage-prep.py 的解析函数）。
- 解析失败时跳过结构层检查，仅由 LLM 人审业务层。

职责：读 .workflow/metadata/design/states.json（ShitPM: 或直接从 design.md 解析），按 entity 分组，
对每个实体的状态机做结构层 4 条图论校验（design-state-format.md 闭环要求的结构层部分）。
业务层 4 条（合法出路全覆盖/二次流转闭环/操作人匹配角色/状态语义自洽）仍由 LLM 审查。

4 条结构层校验：
1. non_terminal_must_have_exit：非终态至少一条正向迁移，不悬空
2. non_initial_must_have_entry：非初始状态至少一条迁移指向它，不孤岛
3. rollback_target_illegal：回退/驳回的 to_state 必须在该实体正向可达路径上
4. transition_ambiguity：同 (trigger, operator) 在不同 from_state 指向冲突 to_state（P2，提示人审）

用法：python state-machine-check.py --project-root <path>
输出：violations JSON 到 stdout
"""

import argparse
import importlib.util
import json
import os
import sys
from collections import defaultdict, deque
from pathlib import Path

ROLLBACK_KEYWORDS = ("退回", "驳回", "撤回")


def _load_states_from_design_md(project_root: Path):
    """ShitPM: 无 states.json 时，从 design.md 直接解析状态机

    复用 stage-prep.py 的 generate_design_metadata 函数（标记为 legacy 但解析逻辑仍可复用）。
    返回 (states_list, error_message)；成功时 error_message 为 None。
    """
    design_path = project_root / "output" / "design" / "design.md"
    if not design_path.exists():
        return None, f"design.md not found: {design_path}"
    try:
        with open(design_path, encoding="utf-8") as f:
            content = f.read()
        # 用 importlib 加载 stage-prep.py（文件名含连字符，无法用普通 import）
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("stage_prep", os.path.join(scripts_dir, "stage-prep.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        data = mod.generate_design_metadata(content, "design", project_root)
        states = data.get("states", [])
        return states, None
    except Exception as e:
        return None, f"从 design.md 解析状态机失败: {e}"


def check_state_machines(states):
    """对 states 列表做结构层 4 条校验，返回 violations 列表"""
    violations = []
    entities = defaultdict(list)
    for s in states:
        entities[s.get("entity")].append(s)
    for entity, ent_states in entities.items():
        violations.extend(_check_entity(entity, ent_states))
    return violations


def _check_entity(entity, ent_states):
    v = []
    global_transitions = []
    state_map = {}
    for s in ent_states:
        if s.get("is_wildcard"):
            global_transitions.extend(s.get("transitions", []))
        else:
            state_map[s["title"]] = s

    all_to = set()
    for s in ent_states:
        for t in s.get("transitions", []):
            all_to.add(t["to_state"])

    non_wildcard = [s for s in ent_states if not s.get("is_wildcard")]
    non_wildcard.sort(key=lambda x: x.get("line", 0))

    # 初始态判定优先级：1) is_initial 标注 > 2) 行首非终态 > 3) 第一个非通配
    initial = None
    initial_method = None
    for s in non_wildcard:
        if s.get("is_initial"):
            initial = s["title"]
            initial_method = "explicit"
            break
    if initial is None:
        for s in non_wildcard:
            if not s.get("is_terminal"):
                initial = s["title"]
                initial_method = "first_non_terminal"
                break
    if initial_method == "first_non_terminal":
        v.append({
            "rule": "initial_state_inferred",
            "entity": entity, "state": initial,
            "severity": "P2",
            "detail": f"初始态从行首非终态推断为'{initial}'，请确认。建议在 states.json 中显式标注 is_initial",
            "line": non_wildcard[0].get("line", 0),
        })
    if initial is None and non_wildcard:
        initial = non_wildcard[0]["title"]
        initial_method = "fallback_first"
    if initial_method == "fallback_first":
        v.append({
            "rule": "initial_state_ambiguous",
            "entity": entity, "state": initial,
            "severity": "P1",
            "detail": "未找到明确初始态标记，已按行序选第一个非通配状态为初始态，回退合法性校验可能误报",
            "line": non_wildcard[0].get("line", 0),
        })

    # 规则1：非终态必有出路
    for s in non_wildcard:
        if not s.get("is_terminal") and not s.get("transitions"):
            if not global_transitions:
                v.append({
                    "rule": "non_terminal_must_have_exit",
                    "entity": entity, "state": s["title"],
                    "severity": "P1",
                    "detail": "非终态但无任何出路，悬空",
                    "line": s.get("line", 0),
                })

    # 规则2：非初始态必有入路
    for s in non_wildcard:
        if s["title"] == initial:
            continue
        if s["title"] not in all_to:
            v.append({
                "rule": "non_initial_must_have_entry",
                "entity": entity, "state": s["title"],
                "severity": "P1",
                "detail": "非初始状态但无任何入路，孤岛",
                "line": s.get("line", 0),
            })

    # 规则3：回退目标合法（须在正向可达集内）
    forward_reachable = _forward_reachable(initial, state_map, global_transitions)
    for s in non_wildcard:
        for t in s.get("transitions", []):
            trig = t["trigger"]
            if any(k in trig for k in ROLLBACK_KEYWORDS):
                to = t["to_state"]
                if to not in forward_reachable:
                    v.append({
                        "rule": "rollback_target_illegal",
                        "entity": entity, "state": s["title"],
                        "severity": "P1",
                        "detail": f"回退目标'{to}'不在正向可达路径上",
                        "line": t.get("line", s.get("line", 0)),
                    })

    # 规则4：迁移无歧义（同 trigger+operator 不同 from 指向不同 to）
    trigger_map = defaultdict(list)
    for s in non_wildcard:
        for t in s.get("transitions", []):
            key = (t["trigger"], t.get("operator"))
            trigger_map[key].append((s["title"], t["to_state"]))
    for key, pairs in trigger_map.items():
        tos = set(p[1] for p in pairs)
        if len(tos) > 1:
            froms = set(p[0] for p in pairs)
            v.append({
                "rule": "transition_ambiguity",
                "entity": entity,
                "severity": "P2",
                "detail": f"trigger'{key[0]}'在状态{froms}指向不同目标{tos}，需人审是否有业务理由",
                "line": 0,
            })
    return v


def _forward_reachable(initial, state_map, global_transitions=None):
    """从初始态经非回退边 BFS 的正向可达集（含全局迁移目标状态扩张）"""
    if not initial:
        return set()
    queue = deque([initial])
    visited = set()
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        s = state_map.get(cur)
        if not s:
            continue
        for t in s.get("transitions", []):
            trig = t["trigger"]
            if any(k in trig for k in ROLLBACK_KEYWORDS):
                continue
            to = t["to_state"]
            if to not in visited:
                queue.append(to)
    # 纳入全局迁移（通配状态）的目标状态做二次扩张
    if global_transitions:
        for gt in global_transitions:
            to = gt.get("to_state")
            if to and to not in visited:
                visited.add(to)
                queue.append(to)
        while queue:
            cur = queue.popleft()
            if cur in visited:
                continue
            visited.add(cur)
            s = state_map.get(cur)
            if not s:
                continue
            for t in s.get("transitions", []):
                trig = t["trigger"]
                if any(k in trig for k in ROLLBACK_KEYWORDS):
                    continue
                to = t["to_state"]
                if to not in visited:
                    queue.append(to)
    return visited


def main():
    parser = argparse.ArgumentParser(description="状态机闭环结构层校验（ShitPM: 按需检查）")
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--source",
        choices=["auto", "design", "states-json"],
        default="auto",
        help="状态机数据来源：auto（默认 design.md，缺失时降级 states.json）/ design（强制 design.md）/ states-json（强制旧 metadata）",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    states_file = project_root / ".workflow" / "metadata" / "design" / "states.json"
    design_path = project_root / "output" / "design" / "design.md"

    states = None
    source = None
    errors = []

    # ShitPM: Design 是唯一事实源，默认从 design.md 解析
    # 仅当 --source=states-json 或 design.md 不存在时才读 states.json
    use_design_first = args.source in ("auto", "design")
    use_states_json = args.source in ("auto", "states-json")

    if use_design_first and design_path.exists():
        states, err = _load_states_from_design_md(project_root)
        if states is not None:
            source = "design.md"
        elif err:
            errors.append(err)

    if states is None and use_states_json and states_file.exists():
        try:
            with open(states_file, encoding="utf-8") as f:
                states = json.load(f)
            source = "states.json"
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"states.json 解析失败: {e}")

    if states is None:
        combined_err = "; ".join(errors) if errors else "未找到状态机数据（design.md 和 states.json 均不可用）"
        print(json.dumps({"error": combined_err}, ensure_ascii=False))
        return 1

    if not states:
        print(json.dumps({
            "stage": "design",
            "source": source,
            "entity_count": 0,
            "violations": [],
            "summary": {"total": 0, "P1": 0, "P2": 0},
            "note": "未找到状态机数据，跳过结构层校验",
        }, ensure_ascii=False, indent=2))
        return 0

    violations = check_state_machines(states)
    p1 = sum(1 for x in violations if x["severity"] == "P1")
    p2 = sum(1 for x in violations if x["severity"] == "P2")
    result = {
        "stage": "design",
        "source": source,
        "entity_count": len(set(s.get("entity") for s in states if isinstance(s, dict))),
        "violations": violations,
        "summary": {"total": len(violations), "P1": p1, "P2": p2},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if p1 > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
