#!/usr/bin/env python3
"""state-machine-check.py — 状态机闭环结构层校验

职责：读 .workflow/metadata/design/states.json，按 entity 分组，对每个实体的状态机
做结构层 4 条图论校验（design-state-format.md 闭环要求的结构层部分）。
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
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

ROLLBACK_KEYWORDS = ("退回", "驳回", "撤回")


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
    forward_reachable = _forward_reachable(initial, state_map)
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


def _forward_reachable(initial, state_map):
    """从初始态经非回退边 BFS 的正向可达集"""
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
    return visited


def main():
    parser = argparse.ArgumentParser(description="状态机闭环结构层校验")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    states_file = Path(args.project_root) / ".workflow" / "metadata" / "design" / "states.json"
    if not states_file.exists():
        print(json.dumps({"error": f"states.json not found: {states_file}"}, ensure_ascii=False))
        return 1
    with open(states_file, encoding="utf-8") as f:
        states = json.load(f)

    violations = check_state_machines(states)
    p1 = sum(1 for x in violations if x["severity"] == "P1")
    p2 = sum(1 for x in violations if x["severity"] == "P2")
    result = {
        "stage": "design",
        "entity_count": len(set(s.get("entity") for s in states)),
        "violations": violations,
        "summary": {"total": len(violations), "P1": p1, "P2": p2},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
