#!/usr/bin/env python3
"""test-shitpm-regression.py — ShitPM 回归测试套件

覆盖 ShitPM 修复包 G 要求的 9 个核心场景（A-I）、7 个补充场景（J-P）和 10 个对抗性场景（AD1-AD10），
共 26 个场景，作为统一回归入口。

补充场景 J-P 覆盖验收反馈要求的真实流程：
- J: Design-only 流程（无下游产物）
- K: 下游与 Design 冲突时 Design 获胜（权限角色幻觉）
- L: 无 metadata 完整工作流（从空项目逐步推进到 done）
- M: 旧项目兼容（有 metadata 目录）
- N/O/P: Fix 各分支的真实传播和重新确认时序

每个场景在独立的临时目录中 setup -> run -> assert，try/finally + shutil.rmtree 清理。
不依赖工作区预先 prepare 文件，所有 fixture 动态创建。

调用脚本：
- stage-context.py
- design-confirmation.py
- review-precheck.py
- prd-consistency-check.py

用法：
  python test-shitpm-regression.py
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent


# ── 辅助函数 ──────────────────────────────────────────────────

def write_fixture(root: Path, rel_path: str, content: str) -> Path:
    """在 root 下创建 rel_path 文件，自动创建父目录。返回文件绝对路径。"""
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def run_script(script_name: str, *args) -> tuple[int, dict | None, str]:
    """调用 scripts/python/<script_name>，返回 (exit_code, stdout_json, stderr)。

    stdout 非空时尝试解析为 JSON，失败则 stdout_json 为 None。
    stdin 显式关闭，避免 prd-consistency-check.py 的 stdin 读取逻辑产生不确定性。
    """
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name), *args]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        stdin=subprocess.DEVNULL,
    )
    stdout_json = None
    if proc.stdout.strip():
        try:
            stdout_json = json.loads(proc.stdout)
        except json.JSONDecodeError:
            stdout_json = None
    return proc.returncode, stdout_json, proc.stderr


def make_new_fixture_dir() -> Path:
    """创建临时目录用于测试 fixture。"""
    return Path(tempfile.mkdtemp(prefix="shitpm-test-"))


def confirm_design(fixture: Path) -> tuple[int, str]:
    """调用 design-confirmation.py confirm 写入正确哈希。返回 (exit_code, stderr)。"""
    code, _, err = run_script(
        "design-confirmation.py", "--project-root", str(fixture), "confirm"
    )
    return code, err


def test_scenario_F1_enum_and_state_drift():
    fixture = make_new_fixture_dir()
    try:
        design = """## 页面清单
| 页面 | 说明 |
| --- | --- |
| 首页 | 首页 |

## 字段定义
| 字段 | 类型 | 必填 | 枚举值 / 规则 | 说明 |
| --- | --- | --- | --- | --- |
| 状态 | string | 是 | draft, published | 状态 |

## 规则与状态定义
### 任务状态机
| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
| --- | --- | --- | --- | --- | --- |
| draft | 草稿 | member | 发布 | published | — |
| published | 已发布 | member | — | — | — |
"""
        prd = design.replace("draft, published | 状态", "draft, published, archived | 状态").replace(
            "| published | 已发布 | member | — | — | — |", "| published | 已发布 | member | — | — | — |\n| archived | 已归档 | member | — | — | — |"
        )
        write_fixture(fixture, "output/design/design.md", design)
        write_fixture(fixture, "output/prd/prd.md", prd)
        code, out, err = run_script("prd-consistency-check.py", "--project-root", str(fixture))
        if code != 1 or not out:
            return False, f"应报告漂移，exit={code}, stderr={err}"
        enums = out.get("classification", {}).get("deterministic_conflicts", {}).get("field_enums", [])
        states = out.get("states", {}).get("hallucinated", [])
        if not enums or "archived" not in states:
            return False, f"枚举/状态漂移未被捕获: enums={enums}, states={states}"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_F2_F3_F4_downstream_guards():
    fixture = make_new_fixture_dir()
    try:
        design = """## 页面清单
| 页面 | 说明 |
| --- | --- |
| 首页 | 首页 |
## 字段定义
| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| 用户名 | string | 是 | 用户名 |
## 规则与状态定义
### 任务状态机
| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
| --- | --- | --- | --- | --- | --- |
| draft | 草稿 | member | 发布 | published | — |
| published | 已发布 | member | — | — | — |
"""
        write_fixture(fixture, "output/design/design.md", design)
        write_fixture(fixture, "output/prd/prd.md", "## 页面说明\n### 首页\n首页内容\n\n" + design)
        write_fixture(fixture, "output/prototype/index.html", "<html><body>首页 用户名 draft published</body></html>")
        code, _, _ = run_script("artifact-guard.py", "--project-root", str(fixture), "check-input", "--stage", "prd")
        if code == 0:
            return False, "未确认 Design 不应通过 check-input"
        code, _, err = run_script("design-confirmation.py", "--project-root", str(fixture), "confirm")
        if code != 0:
            return False, f"确认失败: {err}"
        code, record_out, err = run_script("artifact-guard.py", "--project-root", str(fixture), "record", "--stage", "prd")
        if code != 0:
            return False, f"PRD provenance 登记失败: out={record_out}, stderr={err}"
        write_fixture(fixture, "output/design/design.md", design + "\n补充说明")
        code, out, _ = run_script("artifact-guard.py", "--project-root", str(fixture), "check", "--stage", "prd")
        if code == 0 or not out or out.get("reason") != "source_hash_mismatch":
            return False, f"Design 修改后未判陈旧: {out}"
        code, out, _ = run_script("prototype-consistency-check.py", "--project-root", str(fixture))
        if code != 0 or not out or out.get("summary", {}).get("total_missing") != 0:
            return False, f"Prototype 一致性检查异常: {out}"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


# ── Fixture 模板 ─────────────────────────────────────────────

DESIGN_MD_TEMPLATE = """\
# 设计文档

## 产品目标

构建一个简单可用的任务管理系统，支持任务创建、分配、完成。

## 非目标

不做任务依赖关系管理；不做跨项目资源调度。

## 目标用户

- 团队成员：创建和完成自己的任务
- 团队管理员：分配任务、查看团队进度

## 核心业务流程

1. 管理员创建任务并分配给成员
2. 成员接收任务并开始执行
3. 成员标记任务完成

## 数据范围

任务、成员、团队。

## 系统边界

不含通知系统；不含报表系统。

## 高影响待确认

- 任务是否支持子任务

## 角色定义

- `member`：团队成员，可创建和完成自己的任务
- `admin`：团队管理员，可分配任务

## 模块定义

- 任务管理：任务的创建、分配、完成

## 页面清单

| 页面 | 说明 |
| --- | --- |
| 任务列表 | 展示当前用户的任务 |
| 任务详情 | 展示任务详细信息 |

## 字段定义

### 任务实体

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| 任务名称 | string | 是 | 任务标题 |
| 任务状态 | string | 是 | 任务当前状态 |

## 页面与字段落点

### 任务列表页

| 字段 | 来源 |
| --- | --- |
| 任务名称 | 任务实体 |
| 任务状态 | 任务实体 |

## 规则与状态定义

### 任务状态机

| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
| --- | --- | --- | --- | --- | --- |
| 待分配 | 任务已创建未分配 | admin | 分配任务 | 进行中 | — |
| 进行中 | 任务已分配待完成 | member | 标记完成 | 已完成 | — |
| 已完成 | 任务已完成 | — | — | — | — |

## 权限定义

### 任务列表

- `member`：可查看自己的任务
- `admin`：可查看所有任务

### 任务详情

- `member`：可查看自己的任务详情
- `admin`：可查看所有任务详情
"""


PRD_MD_TEMPLATE = """\
# PRD 文档

## 名词说明

- 任务：工作单元

## 详细需求说明

### 任务列表页

页面展示当前用户的任务。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| 任务名称 | string | 是 | 任务标题 |
| 任务状态 | string | 是 | 任务当前状态 |
"""


# ── 核心场景 A-I ─────────────────────────────────────────────

def test_scenario_A():
    """场景 A：复杂业务 - Design 首次生成责任

    验证：design.md 存在但未确认时，stage-context 输出
    - confirm-design.available = True（design.md 存在）
    - design_confirmation.confirmed = False (no_confirmation_record)
    - spm-prd.available = False（Design 未确认）
    - spm-prototype.available = False（Design 未确认）
    - status_source = "loaded"
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, ".workflow/status.json", json.dumps({
            "current_stage": "design",
            "artifacts": {"design": "output/design/design.md"}
        }, ensure_ascii=False))

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )

        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"
        if not out:
            return False, "stage-context 无 JSON 输出"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("confirm-design", {}).get("available"):
            return False, "confirm-design 应可用（design.md 存在）"

        dc = out.get("design_confirmation", {})
        if dc.get("confirmed") is not False:
            return False, f"design_confirmation.confirmed 应为 False，实际 {dc.get('confirmed')}"
        if dc.get("reason") != "no_confirmation_record":
            return False, f"reason 应为 no_confirmation_record，实际 {dc.get('reason')}"

        if actions.get("spm-prd", {}).get("available"):
            return False, "spm-prd 应不可用（Design 未确认）"
        if actions.get("spm-prototype", {}).get("available"):
            return False, "spm-prototype 应不可用（Design 未确认）"

        if out.get("status_source") != "loaded":
            return False, f"status_source 应为 loaded，实际 {out.get('status_source')}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_B():
    """场景 B：简单业务 - Design 双下游并列

    验证：design.md 已确认 + prd.md + prototype 都存在时
    - design_confirmation.confirmed = True (hash_match)
    - spm-prd.available = True
    - spm-prototype.available = True
    - actual_stage = "done"
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, "output/prd/prd.md", PRD_MD_TEMPLATE)
        write_fixture(fixture, "output/prototype/index.html",
                      "<!doctype html><html><body>ok</body></html>")

        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"confirm 失败：{cerr}"

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )

        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        dc = out.get("design_confirmation", {})
        if dc.get("confirmed") is not True:
            return False, f"design_confirmation.confirmed 应为 True，实际 {dc.get('confirmed')}"
        if dc.get("reason") != "hash_match":
            return False, f"reason 应为 hash_match，实际 {dc.get('reason')}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("spm-prd", {}).get("available"):
            return False, "spm-prd 应可用"
        if not actions.get("spm-prototype", {}).get("available"):
            return False, "spm-prototype 应可用"

        if out.get("actual_stage") != "done":
            return False, f"actual_stage 应为 done，实际 {out.get('actual_stage')}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_C():
    """场景 C：Prototype-only - 无 PRD 一致性检查

    验证：prototype 存在但无 prd.md，--allow-no-prd 时
    - exit_code = 0
    - skipped = true
    - exit_reason = "skipped"
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, "output/prototype/index.html",
                      "<!doctype html><html><body>ok</body></html>")

        code, out, err = run_script(
            "prd-consistency-check.py",
            "--project-root", str(fixture),
            "--allow-no-prd"
        )

        if code != 0:
            return False, f"退出码应为 0，实际 {code}，stderr: {err}"
        if not out:
            return False, "无 JSON 输出"
        if not out.get("skipped"):
            return False, f"skipped 应为 true，实际 {out.get('skipped')}"
        if out.get("exit_reason") != "skipped":
            return False, f"exit_reason 应为 skipped，实际 {out.get('exit_reason')}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_D():
    """场景 D：status.json 损坏 - canonical 探测接管

    验证：status.json 是非法 JSON 时
    - status_source = "corrupted"
    - confirm-design.available = True（canonical 探测识别 design.md）
    - artifacts_mirror.canonical_detected 含 design
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, ".workflow/status.json", "{bad json")

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )

        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        if out.get("status_source") != "corrupted":
            return False, f"status_source 应为 corrupted，实际 {out.get('status_source')}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("confirm-design", {}).get("available"):
            return False, "confirm-design 应可用（canonical 探测应识别 design.md）"

        mirror = out.get("artifacts_mirror", {})
        canonical = mirror.get("canonical_detected", {})
        if "design" not in canonical:
            return False, f"canonical_detected 应含 design，实际 {canonical}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_E():
    """场景 E：status.json 缺失 - 仍可输出上下文

    验证：无 status.json 时
    - status_source = "missing"
    - confirm-design.available = True
    - current_stage 回退到 actual_stage
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        # 不写 status.json

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )

        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        if out.get("status_source") != "missing":
            return False, f"status_source 应为 missing，实际 {out.get('status_source')}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("confirm-design", {}).get("available"):
            return False, "confirm-design 应可用"

        if out.get("current_stage") != out.get("actual_stage"):
            return False, (
                f"current_stage({out.get('current_stage')}) 应等于 "
                f"actual_stage({out.get('actual_stage')})"
            )

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_F():
    """场景 F：Design 修改后哈希不一致

    验证：先确认 design.md，修改后再 check
    - design-confirmation check 退出码 = 2，reason = "hash_mismatch"
    - stage-context design_confirmation.confirmed = False，reason = "hash_mismatch"
    - spm-prd.available = False
    - spm-prototype.available = False
    """
    fixture = make_new_fixture_dir()
    try:
        design_path = write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)

        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"confirm 失败：{cerr}"

        # 修改 design.md 触发哈希变化
        with open(design_path, "a", encoding="utf-8") as f:
            f.write("\n\n## 新增章节（触发哈希变化）\n")

        # design-confirmation check
        ccode, cout, cerr = run_script(
            "design-confirmation.py", "--project-root", str(fixture), "check"
        )
        if ccode != 2:
            return False, f"check 退出码应为 2，实际 {ccode}，stderr: {cerr}"
        if cout.get("reason") != "hash_mismatch":
            return False, f"check reason 应为 hash_mismatch，实际 {cout.get('reason')}"

        # stage-context
        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        dc = out.get("design_confirmation", {})
        if dc.get("confirmed") is not False:
            return False, f"design_confirmation.confirmed 应为 False，实际 {dc.get('confirmed')}"
        if dc.get("reason") != "hash_mismatch":
            return False, f"stage-context reason 应为 hash_mismatch，实际 {dc.get('reason')}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if actions.get("spm-prd", {}).get("available"):
            return False, "spm-prd 应不可用（哈希不一致）"
        if actions.get("spm-prototype", {}).get("available"):
            return False, "spm-prototype 应不可用（哈希不一致）"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_G():
    """场景 G：PRD 引入 design 未定义字段 - deterministic_conflict

    验证：prd.md 含 design.md 没有的幻觉字段
    - exit_code = 1
    - exit_reason = "deterministic_conflict"
    - fields.hallucinated 含幻觉字段
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)

        prd_with_hallucination = """\
# PRD 文档

## 名词说明

- 任务：工作单元

## 详细需求说明

### 任务列表页

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| 任务名称 | string | 是 | 任务标题 |
| 任务状态 | string | 是 | 任务当前状态 |
| 幻觉字段A | string | 是 | design 中未定义 |
"""
        write_fixture(fixture, "output/prd/prd.md", prd_with_hallucination)

        code, out, err = run_script(
            "prd-consistency-check.py", "--project-root", str(fixture)
        )

        if code != 1:
            return False, f"退出码应为 1，实际 {code}，stderr: {err}"
        if out.get("exit_reason") != "deterministic_conflict":
            return False, f"exit_reason 应为 deterministic_conflict，实际 {out.get('exit_reason')}"

        fields = out.get("fields", {})
        hallucinated = fields.get("hallucinated", [])
        if not hallucinated:
            return False, f"fields.hallucinated 应非空，实际 {hallucinated}"
        if "幻觉字段A" not in hallucinated:
            return False, f"幻觉字段A 应在 hallucinated 中，实际 {hallucinated}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_H():
    """场景 H：design-confirmation.py 三态

    子态 1：无确认文件 -> check 退出码 3, reason=no_confirmation_record
    子态 2：confirm 后 check -> 退出码 0, reason=hash_match
    子态 3：修改 design.md 后 check -> 退出码 2, reason=hash_mismatch
    """
    fixture = make_new_fixture_dir()
    try:
        design_path = write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)

        # 子态 1：无确认文件
        c1, o1, _ = run_script(
            "design-confirmation.py", "--project-root", str(fixture), "check"
        )
        if c1 != 3:
            return False, f"子态1 退出码应为 3，实际 {c1}"
        if o1.get("reason") != "no_confirmation_record":
            return False, f"子态1 reason 应为 no_confirmation_record，实际 {o1.get('reason')}"

        # 子态 2：confirm 后 check
        cconf, econf = confirm_design(fixture)
        if cconf != 0:
            return False, f"confirm 失败：{econf}"

        c2, o2, _ = run_script(
            "design-confirmation.py", "--project-root", str(fixture), "check"
        )
        if c2 != 0:
            return False, f"子态2 退出码应为 0，实际 {c2}"
        if o2.get("reason") != "hash_match":
            return False, f"子态2 reason 应为 hash_match，实际 {o2.get('reason')}"

        # 子态 3：修改 design.md 后 check
        with open(design_path, "a", encoding="utf-8") as f:
            f.write("\n\n## 修改触发哈希变化\n")

        c3, o3, _ = run_script(
            "design-confirmation.py", "--project-root", str(fixture), "check"
        )
        if c3 != 2:
            return False, f"子态3 退出码应为 2，实际 {c3}"
        if o3.get("reason") != "hash_mismatch":
            return False, f"子态3 reason 应为 hash_mismatch，实际 {o3.get('reason')}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_I():
    """场景 I：review-precheck 三个 stage 的 can_start_review 语义

    验证：产物存在时
    - stage=design, can_start_review=True, exit_code=0
    - stage=prd, can_start_review=True, exit_code=0
    - stage=prototype, can_start_review=True, exit_code=0
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, "output/prd/prd.md", PRD_MD_TEMPLATE)
        write_fixture(fixture, "output/prototype/index.html",
                      "<!doctype html><html><body>ok</body></html>")

        for stage in ("design", "prd", "prototype"):
            code, out, err = run_script(
                "review-precheck.py", "--stage", stage,
                "--project-root", str(fixture)
            )
            if code != 0:
                return False, f"stage={stage} 退出码应为 0，实际 {code}，stderr: {err}"
            if not out.get("can_start_review"):
                return False, f"stage={stage} can_start_review 应为 True"
            if out.get("block_review"):
                return False, f"stage={stage} block_review 应为 False"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


# ── 补充场景 J-P（覆盖验收反馈中的真实流程场景） ────────────

def test_scenario_J():
    """场景 J：Design-only 流程

    验证：design.md 已确认，无 PRD、无 Prototype 时
    - design_confirmation.confirmed = True
    - spm-prd.available = True
    - spm-prototype.available = True
    - actual_stage = "design"（下游未生成，仍处于 design 阶段）
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)

        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"confirm 失败：{cerr}"

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        dc = out.get("design_confirmation", {})
        if dc.get("confirmed") is not True:
            return False, f"design_confirmation.confirmed 应为 True，实际 {dc.get('confirmed')}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("spm-prd", {}).get("available"):
            return False, "spm-prd 应可用（Design 已确认，可独立生成 PRD）"
        if not actions.get("spm-prototype", {}).get("available"):
            return False, "spm-prototype 应可用（Design 已确认，可独立生成 Prototype）"

        if out.get("actual_stage") != "design":
            return False, f"actual_stage 应为 design（无下游产物），实际 {out.get('actual_stage')}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_K():
    """场景 K：下游与 Design 冲突时 Design 获胜（权限角色幻觉）

    验证：PRD 权限表格引入 design 中不存在的"超级管理员"角色
    - exit_code = 1
    - exit_reason = "deterministic_conflict"
    - roles.hallucinated 含 "超级管理员"
    - permission_role_pairs.hallucinated 含 (page, "超级管理员") 二元组
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)

        # PRD 在权限表格中引入 design 不存在的"超级管理员"角色
        prd_with_fake_admin = """\
# PRD 文档

## 名词说明

- 任务：工作单元

## 详细需求说明

### 任务列表页

页面展示当前用户的任务。

#### 字段定义

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| 任务名称 | string | 是 | 任务标题 |
| 任务状态 | string | 是 | 任务当前状态 |

#### 权限规则

| 模块 | member | admin | 超级管理员 |
| --- | --- | --- | --- |
| 任务列表 | 查看 | 查看全部 | 查看和删除所有人的任务 |
"""
        write_fixture(fixture, "output/prd/prd.md", prd_with_fake_admin)

        code, out, err = run_script(
            "prd-consistency-check.py", "--project-root", str(fixture)
        )

        if code != 1:
            return False, f"退出码应为 1，实际 {code}，stderr: {err}"
        if out.get("exit_reason") != "deterministic_conflict":
            return False, f"exit_reason 应为 deterministic_conflict，实际 {out.get('exit_reason')}"

        roles = out.get("roles", {})
        hallucinated_roles = roles.get("hallucinated", [])
        if "超级管理员" not in hallucinated_roles:
            return False, f"roles.hallucinated 应含 '超级管理员'，实际 {hallucinated_roles}"

        perm_pairs = out.get("permission_role_pairs", {})
        hallucinated_pairs = perm_pairs.get("hallucinated", [])
        has_fake_admin_pair = any(
            isinstance(p, dict) and p.get("role") == "超级管理员"
            for p in hallucinated_pairs
        )
        if not has_fake_admin_pair:
            return False, f"permission_role_pairs.hallucinated 应含 role='超级管理员' 的二元组，实际 {hallucinated_pairs}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_L():
    """场景 L：无 metadata 完整工作流

    验证：从空项目逐步推进，每步 stage-context 输出符合预期
    - 步骤 1：空项目 -> actual_stage="empty", confirm-design 不可用
    - 步骤 2：写 design.md（未确认）-> actual_stage="design", confirm-design 可用, spm-prd 不可用
    - 步骤 3：confirm design -> confirmed=True, spm-prd 可用
    - 步骤 4：写 prd.md -> actual_stage="prd"
    - 步骤 5：写 prototype/index.html -> actual_stage="done"
    全程无 .workflow/metadata/ 目录
    """
    fixture = make_new_fixture_dir()
    try:
        # 步骤 1：空项目
        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"步骤1 stage-context 退出码 {code}，stderr: {err}"
        # 空项目默认阶段为 "align"（ShitPM 起始阶段，align 可选但 stage-context 用 align 作默认）
        if out.get("actual_stage") not in ("align", "empty"):
            return False, f"步骤1 actual_stage 应为 align 或 empty，实际 {out.get('actual_stage')}"
        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if actions.get("confirm-design", {}).get("available"):
            return False, "步骤1 confirm-design 应不可用（无 design.md）"

        # 步骤 2：写 design.md（未确认）
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"步骤2 stage-context 退出码 {code}，stderr: {err}"
        if out.get("actual_stage") != "design":
            return False, f"步骤2 actual_stage 应为 design，实际 {out.get('actual_stage')}"
        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("confirm-design", {}).get("available"):
            return False, "步骤2 confirm-design 应可用"
        if actions.get("spm-prd", {}).get("available"):
            return False, "步骤2 spm-prd 应不可用（Design 未确认）"

        # 步骤 3：confirm design
        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"步骤3 confirm 失败：{cerr}"
        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"步骤3 stage-context 退出码 {code}，stderr: {err}"
        dc = out.get("design_confirmation", {})
        if dc.get("confirmed") is not True:
            return False, f"步骤3 confirmed 应为 True，实际 {dc.get('confirmed')}"
        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("spm-prd", {}).get("available"):
            return False, "步骤3 spm-prd 应可用（Design 已确认）"

        # 步骤 4：写 prd.md（只有 PRD，无 Prototype）
        # ShitPM：双下游并列，只完成一项时 actual_stage 仍为 "design"
        write_fixture(fixture, "output/prd/prd.md", PRD_MD_TEMPLATE)
        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"步骤4 stage-context 退出码 {code}，stderr: {err}"
        if out.get("actual_stage") != "design":
            return False, f"步骤4 actual_stage 应为 design（双下游并列，只完成 PRD 不推进阶段），实际 {out.get('actual_stage')}"

        # 步骤 5：写 prototype（双下游都完成）
        write_fixture(fixture, "output/prototype/index.html",
                      "<!doctype html><html><body>ok</body></html>")
        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"步骤5 stage-context 退出码 {code}，stderr: {err}"
        if out.get("actual_stage") != "done":
            return False, f"步骤5 actual_stage 应为 done（双下游都完成），实际 {out.get('actual_stage')}"

        # 全程无 metadata
        if (fixture / ".workflow" / "metadata").exists():
            return False, "不应创建 .workflow/metadata/ 目录"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_M():
    """场景 M：旧项目兼容（有 metadata 目录）

    验证：旧项目存在 .workflow/metadata/design/ 目录时
    - stage-context 仍能正常输出（不报错）
    - metadata 检查作为 legacy 参考不阻塞
    - review-precheck 仍可执行（metadata 检查不阻塞）
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        # 创建 legacy metadata 目录和文件
        write_fixture(fixture, ".workflow/metadata/design/fields.json", "[]")
        write_fixture(fixture, ".workflow/metadata/design/pages.json", "[]")
        write_fixture(fixture, ".workflow/metadata/design/relations.json", "{}")

        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"confirm 失败：{cerr}"

        # stage-context 仍能正常工作
        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"
        if out.get("actual_stage") != "design":
            return False, f"actual_stage 应为 design，实际 {out.get('actual_stage')}"

        # review-precheck 仍可执行
        code, out, err = run_script(
            "review-precheck.py", "--stage", "design",
            "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"review-precheck 退出码 {code}，stderr: {err}"
        if not out.get("can_start_review"):
            return False, "can_start_review 应为 True（metadata 检查不阻塞）"
        # metadata 检查模式应为 legacy_optional
        if out.get("metadata_check_mode") != "legacy_optional":
            return False, f"metadata_check_mode 应为 legacy_optional，实际 {out.get('metadata_check_mode')}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_N():
    """场景 N：Fix 时序 - 修改 design 后下游被阻断

    验证：已确认 design → 修改 design.md → stage-context 输出
    - design_confirmation.confirmed = False（哈希不一致）
    - spm-prd.available = False
    - spm-prototype.available = False
    - confirm-design 可用（可重新确认）
    """
    fixture = make_new_fixture_dir()
    try:
        design_path = write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, "output/prd/prd.md", PRD_MD_TEMPLATE)
        write_fixture(fixture, "output/prototype/index.html",
                      "<!doctype html><html><body>ok</body></html>")

        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"confirm 失败：{cerr}"

        # 修改 design.md 触发哈希变化
        with open(design_path, "a", encoding="utf-8") as f:
            f.write("\n\n## 新增章节（Fix 修改）\n")

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        dc = out.get("design_confirmation", {})
        if dc.get("confirmed") is not False:
            return False, f"confirmed 应为 False（哈希不一致），实际 {dc.get('confirmed')}"
        if dc.get("reason") != "hash_mismatch":
            return False, f"reason 应为 hash_mismatch，实际 {dc.get('reason')}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if actions.get("spm-prd", {}).get("available"):
            return False, "spm-prd 应不可用（Design 修改后未重新确认）"
        if actions.get("spm-prototype", {}).get("available"):
            return False, "spm-prototype 应不可用（Design 修改后未重新确认）"
        if not actions.get("confirm-design", {}).get("available"):
            return False, "confirm-design 应可用（可重新确认）"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_O():
    """场景 O：Fix 时序 - 重新确认后下游恢复

    验证：场景 N 之后重新 confirm design → stage-context 输出
    - design_confirmation.confirmed = True（哈希重新一致）
    - spm-prd.available = True
    - spm-prototype.available = True
    """
    fixture = make_new_fixture_dir()
    try:
        design_path = write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, "output/prd/prd.md", PRD_MD_TEMPLATE)
        write_fixture(fixture, "output/prototype/index.html",
                      "<!doctype html><html><body>ok</body></html>")

        # 初次确认
        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"初次 confirm 失败：{cerr}"

        # 修改 design.md 触发失效
        with open(design_path, "a", encoding="utf-8") as f:
            f.write("\n\n## 新增章节（Fix 修改）\n")

        # 重新确认
        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"重新 confirm 失败：{cerr}"

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        dc = out.get("design_confirmation", {})
        if dc.get("confirmed") is not True:
            return False, f"confirmed 应为 True（重新确认后哈希一致），实际 {dc.get('confirmed')}"
        if dc.get("reason") != "hash_match":
            return False, f"reason 应为 hash_match，实际 {dc.get('reason')}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("spm-prd", {}).get("available"):
            return False, "spm-prd 应可用（Design 已重新确认）"
        if not actions.get("spm-prototype", {}).get("available"):
            return False, "spm-prototype 应可用（Design 已重新确认）"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_P():
    """场景 P：Fix 时序 - PRD 纯文案修改不触发 Design 失效

    验证：已确认 design → 修改 prd.md（不修改 design）→ stage-context 输出
    - design_confirmation.confirmed = True（design 未变，哈希仍一致）
    - spm-prd.available = True
    - spm-prototype.available = True
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        prd_path = write_fixture(fixture, "output/prd/prd.md", PRD_MD_TEMPLATE)
        write_fixture(fixture, "output/prototype/index.html",
                      "<!doctype html><html><body>ok</body></html>")

        ccode, cerr = confirm_design(fixture)
        if ccode != 0:
            return False, f"confirm 失败：{cerr}"

        # 修改 prd.md（纯文案，不动 design）
        with open(prd_path, "a", encoding="utf-8") as f:
            f.write("\n\n## 修订说明（纯文案修改）\n")

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )
        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        dc = out.get("design_confirmation", {})
        if dc.get("confirmed") is not True:
            return False, f"confirmed 应为 True（PRD 修改不影响 Design 确认），实际 {dc.get('confirmed')}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("spm-prd", {}).get("available"):
            return False, "spm-prd 应可用（Design 仍确认有效）"
        if not actions.get("spm-prototype", {}).get("available"):
            return False, "spm-prototype 应可用（Design 仍确认有效）"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


# ── 对抗性场景 AD1-AD10 ──────────────────────────────────────

def test_scenario_AD1():
    """AD1：confirmation.json 损坏（非 JSON）

    验证：design-confirmation check
    - exit_code = 1
    - stderr 含 "corrupted"
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, ".workflow/confirmations/design.json", "{not json")

        code, out, err = run_script(
            "design-confirmation.py", "--project-root", str(fixture), "check"
        )

        if code != 1:
            return False, f"退出码应为 1，实际 {code}"
        if "corrupted" not in err:
            return False, f"stderr 应含 'corrupted'，实际: {err}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD2():
    """AD2：confirmation.json artifact 字段错误

    验证：design-confirmation check
    - exit_code = 1
    - reason = "confirmation_invalid"
    - problems 非空
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, ".workflow/confirmations/design.json", json.dumps({
            "artifact": "output/design/other.md",
            "content_sha256": "a" * 64,
            "confirmed_at": "2026-07-20T00:00:00+08:00"
        }, ensure_ascii=False))

        code, out, err = run_script(
            "design-confirmation.py", "--project-root", str(fixture), "check"
        )

        if code != 1:
            return False, f"退出码应为 1，实际 {code}"
        if out.get("reason") != "confirmation_invalid":
            return False, f"reason 应为 confirmation_invalid，实际 {out.get('reason')}"
        if not out.get("problems"):
            return False, "problems 应非空"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD3():
    """AD3：confirmation.json 缺 confirmed_at

    验证：design-confirmation check
    - exit_code = 1
    - reason = "confirmation_invalid"
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, ".workflow/confirmations/design.json", json.dumps({
            "artifact": "output/design/design.md",
            "content_sha256": "a" * 64
        }, ensure_ascii=False))

        code, out, err = run_script(
            "design-confirmation.py", "--project-root", str(fixture), "check"
        )

        if code != 1:
            return False, f"退出码应为 1，实际 {code}"
        if out.get("reason") != "confirmation_invalid":
            return False, f"reason 应为 confirmation_invalid，实际 {out.get('reason')}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD4():
    """AD4：status.json current_stage 非法值

    验证：stage-context 应将非法 current_stage 回退到 actual_stage
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, ".workflow/status.json", json.dumps({
            "current_stage": "invalid_stage",
            "artifacts": {}
        }, ensure_ascii=False))

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )

        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        current = out.get("current_stage")
        actual = out.get("actual_stage")
        if current != actual:
            return False, (
                f"非法 current_stage 应回退到 actual_stage({actual})，"
                f"实际 current_stage={current}"
            )
        if current == "invalid_stage":
            return False, "current_stage 不应保留非法值"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD5():
    """AD5：status.json artifacts 为空但 design.md 存在

    验证：canonical 探测应识别 design.md
    - artifacts_mirror.canonical_detected.design = "output/design/design.md"
    - confirm-design.available = True
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        write_fixture(fixture, ".workflow/status.json", json.dumps({
            "current_stage": "design",
            "artifacts": {}
        }, ensure_ascii=False))

        code, out, err = run_script(
            "stage-context.py", "--project-root", str(fixture)
        )

        if code != 0:
            return False, f"stage-context 退出码 {code}，stderr: {err}"

        mirror = out.get("artifacts_mirror", {})
        canonical = mirror.get("canonical_detected", {})
        if canonical.get("design") != "output/design/design.md":
            return False, f"canonical_detected.design 应为 output/design/design.md，实际 {canonical}"

        actions = {a["action"]: a for a in out.get("available_actions", [])}
        if not actions.get("confirm-design", {}).get("available"):
            return False, "confirm-design 应可用（canonical 探测识别 design.md）"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD6():
    """AD6：PRD 不存在且未传 --allow-no-prd

    验证：prd-consistency-check（无 --allow-no-prd）
    - exit_code = 2
    - JSON 含 error 字段
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)
        # 不写 prd.md，不加 --allow-no-prd

        code, out, err = run_script(
            "prd-consistency-check.py", "--project-root", str(fixture)
        )

        if code != 2:
            return False, f"退出码应为 2，实际 {code}"
        if not out or "error" not in out:
            return False, f"JSON 应含 error 字段，实际 {out}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD7():
    """AD7：design.md 不存在时调用 prd-consistency-check

    验证：
    - exit_code = 2
    - error 含 "design.md not found"
    """
    fixture = make_new_fixture_dir()
    try:
        # 只写 prd.md，不写 design.md
        write_fixture(fixture, "output/prd/prd.md", PRD_MD_TEMPLATE)

        code, out, err = run_script(
            "prd-consistency-check.py", "--project-root", str(fixture)
        )

        if code != 2:
            return False, f"退出码应为 2，实际 {code}"
        err_msg = out.get("error", "") if out else ""
        if "design.md not found" not in err_msg and "design" not in err_msg.lower():
            return False, f"error 应提及 design.md，实际: {err_msg}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD8():
    """AD8：review-precheck stage=design 但 design.md 不存在

    验证：
    - exit_code = 1
    - can_start_review = False
    - blocking_issues 非空
    """
    fixture = make_new_fixture_dir()
    try:
        # 空目录，不写 design.md

        code, out, err = run_script(
            "review-precheck.py", "--stage", "design",
            "--project-root", str(fixture)
        )

        if code != 1:
            return False, f"退出码应为 1，实际 {code}"
        if out.get("can_start_review") is not False:
            return False, f"can_start_review 应为 False，实际 {out.get('can_start_review')}"
        if not out.get("blocking_issues"):
            return False, "blocking_issues 应非空"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD9():
    """AD9：PRD 含 Mermaid 状态图 - state 提取不应误识别

    验证：prd.md 含 ```mermaid 块（含 A[草稿] --> B 等语法）
    - states.hallucinated 不应含 Mermaid 语法片段（A[草稿]、B[已发布]、--> 等）
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)

        prd_with_mermaid = """\
# PRD 文档

## 名词说明

- 任务：工作单元

## 详细需求说明

### 任务列表页

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| 任务名称 | string | 是 | 任务标题 |
| 任务状态 | string | 是 | 任务当前状态 |

### 任务状态流转

```mermaid
stateDiagram-v2
    [*] --> 草稿
    草稿 --> 已发布 : 发布
    已发布 --> 已归档 : 归档
    A[草稿] --> B[已发布]
```
"""
        write_fixture(fixture, "output/prd/prd.md", prd_with_mermaid)

        code, out, err = run_script(
            "prd-consistency-check.py", "--project-root", str(fixture)
        )

        if not out:
            return False, f"无 JSON 输出，stderr: {err}"

        states = out.get("states", {})
        hallucinated = states.get("hallucinated", [])

        # 期望：不应含 Mermaid 语法片段
        forbidden_fragments = ["A[草稿]", "B[已发布]", "[*]", "stateDiagram", "-->", "Diagram"]
        for frag in forbidden_fragments:
            for h in hallucinated:
                if frag in h:
                    return False, (
                        f"hallucinated 含 Mermaid 片段 '{frag}'：{hallucinated}"
                    )

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_AD10():
    """AD10：PRD 含旧模板 `### page-N 页面名` - page 提取应识别

    验证：prd.md 使用旧模板格式
    - pages.matched_count > 0（页面能被识别）
    - pages.hallucinated 不含已知页面名（任务列表、任务详情）
    """
    fixture = make_new_fixture_dir()
    try:
        write_fixture(fixture, "output/design/design.md", DESIGN_MD_TEMPLATE)

        prd_legacy = """\
# PRD 文档

## 名词说明

- 任务：工作单元

## 页面说明

### page-1 任务列表

展示当前用户的任务。

### page-2 任务详情

展示任务详细信息。

## 详细需求说明

### page-1 任务列表

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| 任务名称 | string | 是 | 任务标题 |
| 任务状态 | string | 是 | 任务当前状态 |
"""
        write_fixture(fixture, "output/prd/prd.md", prd_legacy)

        code, out, err = run_script(
            "prd-consistency-check.py", "--project-root", str(fixture)
        )

        if not out:
            return False, f"无 JSON 输出，stderr: {err}"

        pages = out.get("pages", {})
        matched_count = pages.get("matched_count", 0)
        if matched_count == 0:
            return False, f"pages.matched_count 应 > 0，实际 {matched_count}，pages: {pages}"

        hallucinated = pages.get("hallucinated", [])
        if "任务列表" in hallucinated or "任务详情" in hallucinated:
            return False, f"已知页面不应在 hallucinated 中，实际 {hallucinated}"

        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_G5_state_machine_fail_closed():
    """坏 Design 含状态孤岛时，状态检查和确认都必须失败关闭。"""
    fixture = make_new_fixture_dir()
    try:
        design = """# 坏 Design

## 规则与状态定义
### 任务状态机
| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
| --- | --- | --- | --- | --- | --- |
| 草稿 | 草稿 | 成员 | 提交 | 已提交 | — |
| 孤岛 | 无来源状态 | 成员 | — | — | — |
| 已提交 | 已提交 | — | — | — | — |
"""
        write_fixture(fixture, "output/design/design.md", design)
        code, out, err = run_script("state-machine-check.py", "--project-root", str(fixture), "--source", "design")
        if code != 1 or not out:
            return False, f"状态孤岛应失败关闭，exit={code}, stdout={out}, stderr={err}"
        if out.get("summary", {}).get("P1", 0) < 1:
            return False, f"应报告 P1，实际 {out}"
        ccode, _, cerr = run_script("design-confirmation.py", "--project-root", str(fixture), "confirm")
        if ccode == 0 or "确定性检查未通过" not in cerr:
            return False, f"坏 Design 不应确认，exit={ccode}, stderr={cerr}"
        if (fixture / ".workflow" / "confirmations" / "design.json").exists():
            return False, "失败确认不应写入 confirmation.json"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_G6_explicit_no_state_machine():
    """明确声明无状态机或不发生状态变化的 Design 不应被误杀。"""
    declarations = ("无状态机", "本设计无状态变更", "该对象不发生状态变化")
    for declaration in declarations:
        fixture = make_new_fixture_dir()
        try:
            design = f"""# 查询设计

## 规则与状态定义

资产查询只读展示，明确声明：{declaration}。
"""
            write_fixture(fixture, "output/design/design.md", design)
            ccode, _, cerr = run_script("design-confirmation.py", "--project-root", str(fixture), "confirm")
            if ccode != 0:
                return False, f"无状态 Design 应可确认，声明={declaration}，exit={ccode}, stderr={cerr}"
            code, out, err = run_script("state-machine-check.py", "--project-root", str(fixture), "--source", "design")
            if code != 0 or not out.get("no_state_machine_declared"):
                return False, f"无状态声明未被识别，声明={declaration}，exit={code}, out={out}, stderr={err}"
        finally:
            shutil.rmtree(fixture, ignore_errors=True)

    comment_fixture = make_new_fixture_dir()
    try:
        design = """# 查询设计

## 规则与状态定义

<!-- 无状态机是模板指令，不是业务声明。 -->
"""
        write_fixture(comment_fixture, "output/design/design.md", design)
        code, out, err = run_script(
            "state-machine-check.py", "--project-root", str(comment_fixture), "--source", "design"
        )
        if code != 1 or out.get("violations", [{}])[0].get("rule") != "state_machine_not_declared":
            return False, f"模板注释不应被当成声明，exit={code}, out={out}, stderr={err}"
    finally:
        shutil.rmtree(comment_fixture, ignore_errors=True)

    return True, ""


def test_scenario_G7_state_parser_failure():
    """Design 编码/解析失败时，确认不能把失败当作通过。"""
    fixture = make_new_fixture_dir()
    design_path = fixture / "output" / "design" / "design.md"
    try:
        design_path.parent.mkdir(parents=True, exist_ok=True)
        design_path.write_bytes(b"# Design\n\xff\xfe\n")
        code, out, err = run_script("state-machine-check.py", "--project-root", str(fixture), "--source", "design")
        if code != 1 or not out or "解析" not in out.get("error", ""):
            return False, f"解析失败应失败关闭，exit={code}, out={out}, stderr={err}"
        ccode, _, cerr = run_script("design-confirmation.py", "--project-root", str(fixture), "confirm")
        if ccode == 0 or "确定性检查" not in cerr:
            return False, f"解析失败不应确认，exit={ccode}, stderr={cerr}"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_G8_confirmation_bypass_blocked():
    """即使预先伪造正确哈希，check 也必须重新执行确定性门禁。"""
    fixture = make_new_fixture_dir()
    try:
        design = """# 坏 Design

## 规则与状态定义
### 任务状态机
| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
| --- | --- | --- | --- | --- | --- |
| 草稿 | 草稿 | 成员 | 提交 | 已提交 | — |
| 孤岛 | 无来源状态 | 成员 | — | — | — |
| 已提交 | 已提交 | — | — | — | — |
"""
        design_path = write_fixture(fixture, "output/design/design.md", design)
        digest = __import__("hashlib").sha256(design_path.read_bytes()).hexdigest()
        write_fixture(fixture, ".workflow/confirmations/design.json", json.dumps({
            "artifact": "output/design/design.md",
            "content_sha256": digest,
            "confirmed_at": "2026-07-28T00:00:00+08:00",
        }, ensure_ascii=False))
        code, out, err = run_script("design-confirmation.py", "--project-root", str(fixture), "check")
        if code != 1 or "deterministic_gate_failed" not in err:
            return False, f"伪造哈希不应绕过门禁，exit={code}, stdout={out}, stderr={err}"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_H1_field_delivery_guards():
    """字段属性、内部字段缺失和内部用途必须被确定性检查捕获。"""
    fixture = make_new_fixture_dir()
    try:
        design = """# Design

## 字段定义

| 字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| task.status | enum | 16 | 是 | draft | draft、done | 枚举 | 系统生成 | 状态 |
| task.owner_id | string | 64 | 是 | 当前登录人 ID | — | UUID | 系统生成 | 创建人内部标识 |

## 页面与字段落点

### 非页面落点字段

| 字段 | 原因 |
| --- | --- |
| task.owner_id | 内部关联字段，不在页面展示 |
"""
        incomplete_prd = """# PRD

## 名词说明

- 任务：工作单元

## 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| task.status | enum | 是 | 枚举：draft、done | — | — | 状态 |
| task.owner_id | string | 是 | 长度：64；格式：UUID | 当前登录人 ID | 系统生成 | 创建人标识 |
"""
        write_fixture(fixture, "output/design/design.md", design)
        write_fixture(fixture, "output/prd/prd.md", incomplete_prd)
        code, out, err = run_script("prd-consistency-check.py", "--project-root", str(fixture))
        if code != 1 or not out:
            return False, f"字段属性缺失应失败，exit={code}, stderr={err}"
        mismatches = {
            item.get("name"): set(item.get("mismatch_kinds", []))
            for item in out.get("fields", {}).get("deterministic_attribute_mismatch", [])
        }
        expected = {"length", "default", "format", "source"}
        if not expected.issubset(mismatches.get("task.status", set())):
            return False, f"task.status 属性缺失未完整捕获: {mismatches}"
        internal = out.get("fields", {}).get("internal_field_issues", [])
        if not any(item.get("name") == "task.owner_id" and item.get("issue") == "internal_usage_missing" for item in internal):
            return False, f"内部字段用途缺失未捕获: {internal}"

        missing_internal_prd = incomplete_prd.replace(
            "| task.owner_id | string | 是 | 长度：64；格式：UUID | 当前登录人 ID | 系统生成 | 创建人标识 |\n",
            "",
        )
        write_fixture(fixture, "output/prd/prd.md", missing_internal_prd)
        code, out, err = run_script("prd-consistency-check.py", "--project-root", str(fixture))
        internal = (out or {}).get("fields", {}).get("internal_field_issues", [])
        if code != 1 or not any(item.get("name") == "task.owner_id" and item.get("issue") == "missing" for item in internal):
            return False, f"内部字段整体缺失未捕获: exit={code}, internal={internal}, stderr={err}"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_H2_complete_field_delivery_passes():
    """7 列 PRD 完整承接 9 列 Design 字段属性时应通过。"""
    fixture = make_new_fixture_dir()
    try:
        design = """# Design

## 字段定义

| 字段 | 类型 | 长度 | 必填 | 默认值 | 枚举值 | 格式 | 业务来源 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| task.status | enum | 16 | 是 | draft | draft、done | 枚举 | 系统生成 | 状态 |
| task.owner_id | string | 64 | 是 | 当前登录人 ID | — | UUID | 系统生成 | 创建人内部标识 |

## 页面与字段落点

### 非页面落点字段

| 字段 | 原因 |
| --- | --- |
| task.owner_id | 内部关联字段，不在页面展示 |
"""
        prd = """# PRD

## 名词说明

- 任务：工作单元

## 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| task.status | enum | 是 | 长度：16；枚举：draft、done；格式：枚举 | draft | 系统生成 | 状态 |
| task.owner_id | string | 是 | 长度：64；格式：UUID | 当前登录人 ID | 系统生成 | 内部关联标识，不在页面展示 |
"""
        write_fixture(fixture, "output/design/design.md", design)
        write_fixture(fixture, "output/prd/prd.md", prd)
        code, out, err = run_script("prd-consistency-check.py", "--project-root", str(fixture))
        if code != 0 or not out or out.get("exit_reason") != "ok":
            return False, f"完整字段承接应通过，exit={code}, out={out}, stderr={err}"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_H3_permission_polarity_guards():
    """明确权限反转应失败，混合权限表达不应被机械误判。"""
    fixture = make_new_fixture_dir()
    try:
        design = """# Design

## 权限定义

### 团队汇总

- `member`：无权限
"""
        prd = """# PRD

## 权限汇总

| 页面/对象 | member |
| --- | --- |
| 团队汇总 | 查看团队汇总 |
"""
        write_fixture(fixture, "output/design/design.md", design)
        write_fixture(fixture, "output/prd/prd.md", prd)
        code, out, err = run_script("prd-consistency-check.py", "--project-root", str(fixture))
        inversions = (out or {}).get("permission_inversions", [])
        if code != 1 or not any(item.get("page") == "团队汇总" and item.get("role") == "member" for item in inversions):
            return False, f"明确权限反转未捕获: exit={code}, inversions={inversions}, stderr={err}"

        mixed_design = design.replace("无权限", "可查看，不可编辑")
        mixed_prd = prd.replace("查看团队汇总", "不可查看，可编辑")
        write_fixture(fixture, "output/design/design.md", mixed_design)
        write_fixture(fixture, "output/prd/prd.md", mixed_prd)
        code, out, err = run_script("prd-consistency-check.py", "--project-root", str(fixture))
        inversions = (out or {}).get("permission_inversions", [])
        if inversions:
            return False, f"混合权限不应机械判断为反转: {inversions}"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


def test_scenario_H4_field_table_style_lint():
    """旧 4 列字段表触发 STYLE010，7 列字段表不触发。"""
    fixture = make_new_fixture_dir()
    try:
        old_prd = """# PRD

## 名词说明

- 任务：工作单元

## 字段定义

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| task.name | string | 是 | 任务名称 |
"""
        path = write_fixture(fixture, "prd.md", old_prd)
        code, out, err = run_script("prd-style-lint.py", str(path), "--format", "json")
        codes = {item.get("code") for item in (out or {}).get("issues", [])}
        if code != 1 or "STYLE010" not in codes:
            return False, f"旧字段表应触发 STYLE010: exit={code}, codes={codes}, stderr={err}"

        new_prd = old_prd.replace(
            "| 字段 | 类型 | 必填 | 说明 |\n| --- | --- | --- | --- |\n| task.name | string | 是 | 任务名称 |",
            "| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |\n| --- | --- | --- | --- | --- | --- | --- |\n| task.name | string | 是 | 长度：100；格式：文本 | — | 用户填写 | 任务名称 |",
        )
        path = write_fixture(fixture, "prd.md", new_prd)
        code, out, err = run_script("prd-style-lint.py", str(path), "--format", "json")
        codes = {item.get("code") for item in (out or {}).get("issues", [])}
        if "STYLE010" in codes:
            return False, f"7 列字段表不应触发 STYLE010: codes={codes}"
        if code != 0:
            return False, f"完整字段表 lint 应通过: exit={code}, out={out}, stderr={err}"
        return True, ""
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


# ── 主入口 ───────────────────────────────────────────────────

SCENARIOS = [
    ("A", "复杂业务 - Design 首次生成责任", test_scenario_A),
    ("B", "简单业务 - Design 双下游并列", test_scenario_B),
    ("C", "Prototype-only - 无 PRD 一致性检查", test_scenario_C),
    ("D", "status.json 损坏 - canonical 探测接管", test_scenario_D),
    ("E", "status.json 缺失 - 仍可输出上下文", test_scenario_E),
    ("F", "Design 修改后哈希不一致", test_scenario_F),
    ("G", "PRD 引入 design 未定义字段", test_scenario_G),
    ("H", "design-confirmation 三态", test_scenario_H),
    ("I", "review-precheck 三 stage 语义", test_scenario_I),
    ("J", "Design-only 流程（无下游产物）", test_scenario_J),
    ("K", "下游冲突 Design 获胜（权限角色幻觉）", test_scenario_K),
    ("L", "无 metadata 完整工作流", test_scenario_L),
    ("M", "旧项目兼容（有 metadata 目录）", test_scenario_M),
    ("N", "Fix 时序 - 修改 design 后下游阻断", test_scenario_N),
    ("O", "Fix 时序 - 重新确认后下游恢复", test_scenario_O),
    ("P", "Fix 时序 - PRD 纯文案修改不触发 Design 失效", test_scenario_P),
    ("AD1", "confirmation.json 损坏", test_scenario_AD1),
    ("AD2", "confirmation.json artifact 错误", test_scenario_AD2),
    ("AD3", "confirmation.json 缺 confirmed_at", test_scenario_AD3),
    ("AD4", "status.json current_stage 非法", test_scenario_AD4),
    ("AD5", "status.json artifacts 空但 design 存在", test_scenario_AD5),
    ("AD6", "PRD 不存在且未传 --allow-no-prd", test_scenario_AD6),
    ("AD7", "design.md 不存在调用 prd-check", test_scenario_AD7),
    ("AD8", "review-precheck 无 design.md", test_scenario_AD8),
    ("AD9", "PRD 含 Mermaid 不误识别", test_scenario_AD9),
    ("AD10", "PRD 旧模板 page-N 识别", test_scenario_AD10),
    ("F1", "PRD 枚举和状态值级漂移", test_scenario_F1_enum_and_state_drift),
    ("F2-F4", "下游 provenance、门禁和 Prototype 检查", test_scenario_F2_F3_F4_downstream_guards),
    ("G5", "坏 Design 状态检查失败关闭", test_scenario_G5_state_machine_fail_closed),
    ("G6", "明确无状态机声明可通过", test_scenario_G6_explicit_no_state_machine),
    ("G7", "状态解析失败不能确认", test_scenario_G7_state_parser_failure),
    ("G8", "伪造哈希不能绕过确认门禁", test_scenario_G8_confirmation_bypass_blocked),
    ("H1", "字段属性与内部字段交付防丢失", test_scenario_H1_field_delivery_guards),
    ("H2", "完整字段属性承接可通过", test_scenario_H2_complete_field_delivery_passes),
    ("H3", "明确权限反转与混合权限边界", test_scenario_H3_permission_polarity_guards),
    ("H4", "PRD 字段表 7 列结构检查", test_scenario_H4_field_table_style_lint),
]


def main() -> int:
    print("ShitPM 回归测试开始")
    print()

    passed = 0
    failed = 0
    failures = []

    for name, desc, func in SCENARIOS:
        try:
            ok, reason = func()
        except Exception as e:
            ok, reason = False, f"异常: {type(e).__name__}: {e}"

        status = "PASS" if ok else "FAIL"
        print(f"[{name}] {desc} {status}")
        if not ok:
            failed += 1
            failures.append((name, desc, reason))
        else:
            passed += 1

    print()
    print(f"汇总：{passed} 通过，{failed} 失败")

    if failures:
        print()
        print("失败详情：")
        for name, desc, reason in failures:
            print(f"  [{name}] {desc}")
            print(f"    原因：{reason}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
