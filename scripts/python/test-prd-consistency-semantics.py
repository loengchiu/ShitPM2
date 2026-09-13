#!/usr/bin/env python3
"""PRD 一致性检查分类与退出语义回归测试。"""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/python/prd-consistency-check.py"

DESIGN = """# 设计基线

## 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""

PRD_BASE = """# 订单 PRD

## 名词说明

订单：业务订单。

## 详细需求说明

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""


NEW_STRUCTURE_PRD = """# 订单 PRD

## 总体说明

订单：业务订单。

## 功能需求

### 客户履约业务闭环

模块按业务结果组织，不复制 Design 的菜单模块名称。

#### 订单确认阶段

订单确认动作在允许状态下完成。

##### 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |

##### 订单状态阶段

订单状态用于表示业务处理状态。

##### 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""


# 新模板四列字段表：| 字段 | 类型/取值 | 来源或约束 | 使用说明 |，枚举值内联在"类型/取值"列。
NEW_TEMPLATE_4COL_PRD = """# 订单 PRD

## 功能需求

### 履约闭环

#### 字段定义

##### 订单对象

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 订单编号 | 字符串 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举：草稿、已完成 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""

# 新模板四列字段表 + 显式"必填"列（对抗探针 CLEAN 写法）。
NEW_TEMPLATE_5COL_PRD = """# 订单 PRD

## 功能需求

### 履约闭环

#### 字段定义

##### 订单对象

| 字段 | 类型/取值 | 必填 | 来源或约束 | 使用说明 |
|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 订单服务 | 订单唯一编号 |
| 状态 | 枚举：草稿、已完成 | 是 | 订单服务 | 订单处理状态 |

## 权限定义

### 订单列表
- 运营人员：允许查看订单
"""

PAGE_MAPPING_PRD = """# 订单 PRD

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 所属业务闭环 | 主要承接阶段 |
|---|---|---|---|
| 订单列表 | 管理端 | 客户履约业务闭环 | 订单确认 |
| 现场处置 | 移动端 | 客户履约业务闭环 | 订单确认 |
"""

# 斜杠合并字段（如"反馈人/回复人"）应拆分匹配，不整体判为缺失或新增。
SLASH_FIELD_DESIGN = """# 设计基线

## 字段定义

### 报告意见反馈

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 反馈人 | 关联 | 否 | 无 | 无 | 用户表 | 反馈提交人 |
| 回复人 | 关联 | 否 | 无 | 无 | 用户表 | 审计方回复人 |
"""

SLASH_FIELD_PRD = """# PRD 正文

## 功能需求

### 反馈闭环

#### 字段定义

##### 报告意见反馈

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 反馈人/回复人 | 关联 | 被审单位/审计方 | 留痕 |
"""

# 页面"数据字典"与 PRD 章节同名，不应被章节黑名单误过滤。
DICT_PAGE_DESIGN = """# 设计基线

## 页面清单

| 页面 | 终端 | 说明 |
|---|---|---|
| 数据字典 | PC | 枚举与编码配置 |
"""

DICT_PAGE_PRD = """# PRD 正文

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 所属业务闭环 | 主要承接阶段 |
|---|---|---|---|
| 数据字典 | PC | 系统管理 | 配置 |
"""

# 状态组合值拆分 + "下一状态"列读取 + 同章节箭头列表状态表达。
COMBINED_STATE_PRD = """# PRD 正文

## 功能需求

### 系统管理

#### 4.10.5 状态与业务规则

| 对象 | 状态 | 规则 |
|---|---|---|
| 检查项 | 启用/停用 | 可切换 |
| 审批流程实例 | 进行中/已通过 | 流转 |

#### 4.10.6 状态机

| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
|---|---|---|---|---|---|
| 草稿 | 编辑中 | 编制人 | 发送签署 | 已发出 | — |
| 已发出 | 签署中 | 用户 | 签署 | 待签署 | — |
"""

# PRD 写作规则禁止把状态表写进正文，合规 PRD 只能用自然语言枚举状态；
# 该写法必须能被识别，否则状态维度会整体误报（Design 状态全被判遗漏）。
DESIGN_WITH_STATE_MACHINE = """# 设计基线

### 页面：订单列表

- 页面目的：查看订单
- 适用角色：运营人员
- 进入条件：已登录
- 数据范围：本组织
- 主要状态：无状态机

#### 状态机：订单状态

| 状态 | 含义 | 操作人 | 触发动作 | 下一状态 | 限制条件 |
| --- | --- | --- | --- | --- | --- |
| 草稿 | 编制中 | 经办人 | 提交 | 待审核 | — |
| 待审核 | 等待审核 | 审核人 | 通过 | 已完成 | — |
| 已完成 | 结束 | — | — | — | — |
"""

PRD_PROSE_STATES = """# 订单 PRD

## 详细需求说明

订单编号为订单唯一编号。

#### 4.1.5 状态与业务规则

订单状态分为草稿、待审核与已完成三种枚举值。
"""

# 同名"状态"字段按对象区分（年度计划 vs 审批流程实例），不得跨对象误配属性。
SAME_NAME_DESIGN = """# 设计基线

## 数据字典

### 年度计划

| 字段 | 类型 | 必填 | 枚举值 / 规则 | 说明 |
|---|---|---|---|---|
| 状态 | 枚举 | 是 | 草稿/待审批/已通过 | 计划状态 |

### 审批流程实例

| 字段 | 类型 | 必填 | 枚举值 / 规则 | 说明 |
|---|---|---|---|---|
| 状态 | 枚举 | 是 | 进行中/已通过/已驳回 | 实例状态 |
"""

SAME_NAME_PRD = """# PRD 正文

## 功能需求

### 计划模块

#### 字段定义

##### 年度计划

| 字段 | 类型/取值 | 来源或约束 | 使用说明 |
|---|---|---|---|
| 状态 | 枚举 | 草稿/待审批/已通过 | 计划状态 |
"""


# ── 权限维度：Design 事实读取收敛（design-index）+ PRD 侧 ID 空间边界 ──
#
# 覆盖 R23 根因 RC-1 / RC-2：
# - Design 侧权限必须来自 design-index 的 page/operation 必填属性 roles（不再走 stage-prep）；
# - PRD 侧「角色 × 业务能力」矩阵的列是业务能力，不得进入 page ID 空间；
# - 权限章节自身标题不得被当作权限页面名；
# - 两侧不同构时必须 not_evaluated，不得产生确定性冲突。

MODULE_INDEXED = """# 订单 模块设计

## 四、页面、区块、字段与操作设计

### 页面：订单列表
- 页面目的：查看订单
- 适用角色：运营人员、财务人员（含对账）
- 进入条件：已登录
- 数据范围：本组织
- 主要状态：无状态机

#### 区块：订单筛选
- 区块目的：按条件筛选订单

##### 字段表

| 字段名称 | 业务含义 | 字段来源 | 展示条件 | 输入与编辑规则 | 取值与默认规则 | 交互方式 | 校验与反馈 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 订单编号 | 订单唯一编号 | 订单服务 | 始终 | 只读 | 系统生成 | 文本 | 无 |

#### 页面操作
- 区块目的：页面级操作

##### 操作表

| 操作 | 适用角色 | 入口/触发方式 | 输入（字段级） | 展示与可用条件 | 是否二次确认 | 成功结果 | 数据与状态变化 | 失败与恢复 | 后续去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 导出订单 | 运营人员 | 顶部按钮 | 无 | 已选筛选 | 否 | 下载文件 | 无 | 提示重试 | 停留当前页 |
"""

_PERM_FIELD_BLOCK = """##### 字段定义

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|---|---|---|---|---|---|---|
| 订单编号 | 字符串 | 是 | 无 | 系统生成 | 订单服务 | 订单唯一编号 |
"""

# 官方模板形态：「行 = 角色，列 = 业务能力」。
PRD_CAPABILITY_MATRIX = f"""# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.3 角色与权限

| 角色 | 查看订单 | 导出订单 |
|---|---|---|
| 运营人员 | 可 | 可 |
| 财务人员 | 可 | 否 |

#### 4.1.6 动作说明

{_PERM_FIELD_BLOCK}"""

# 存量形态（审计系统等）：4.x.3 是自然语言段落，无可解析结构。
PRD_PROSE_PERMISSION = f"""# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.3 角色与权限

运营人员可以查看和导出订单；财务人员可以查看订单，但不能导出。外包人员不在本模块可见范围内。

#### 4.1.6 动作说明

{_PERM_FIELD_BLOCK}"""

# 与 Design 同构的形态：「行 = 页面，列 = 角色」，应保持确定性比对。
PRD_ROW_OBJECT_PERMISSION = f"""# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.3 角色与权限

| 页面 | 运营人员 | 财务人员 |
|---|---|---|
| 订单列表 | 可 | 可 |

#### 4.1.6 动作说明

{_PERM_FIELD_BLOCK}"""

# 旧格式（防回归）：「## 权限汇总 + ### 页面名 + - role：action」，与 Design 同构。
PRD_LEGACY_PERMISSION_SUMMARY = f"""# 订单 PRD

## 功能需求

### 订单管理

#### 4.1.6 动作说明

{_PERM_FIELD_BLOCK}

## 权限汇总

### 订单列表

- 运营人员：可查看、可导出
- 财务人员：可查看
"""


def run_case(prd: str, design: str = DESIGN):
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "output/design").mkdir(parents=True)
        (root / "output/prd").mkdir(parents=True)
        write_design_set(root, design)
        (root / "output/prd/prd.md").write_text(prd, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"检查输出不是 JSON: {result.stdout}\n{result.stderr}") from exc
        return result.returncode, report


def write_design_set(root: Path, design_text: str) -> None:
    """构造最小多文件 Design 集：地图 + 清单 + 一个模块文件。"""
    import hashlib
    design_dir = root / "output/design"
    module_dir = design_dir / "模块设计" / "订单"
    module_dir.mkdir(parents=True, exist_ok=True)
    module_path = module_dir / "订单管理.md"
    module_path.write_text(design_text, encoding="utf-8")
    map_path = design_dir / "设计地图.md"
    map_path.write_text("# 设计地图\n\n## 模块与职责\n\n- MOD-001 [订单](模块设计/订单/订单管理.md)：负责订单。\n", encoding="utf-8")

    def sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "shitpm-design-set/v1",
        "set_sha256": "",
        "files": [
            {"id": "MAP-001", "path": "设计地图.md", "type": "map", "module": None, "business_chains": [], "depends_on": [], "sha256": sha(map_path)},
            {"id": "MOD-001", "path": "模块设计/订单/订单管理.md", "type": "module", "module": "订单", "business_chains": ["订单业务链"], "depends_on": [], "sha256": sha(module_path)},
        ],
        "decisions": [],
    }
    parts = []
    for f in sorted(manifest["files"], key=lambda x: x["id"]):
        parts.append(f["id"] + f["path"] + f["sha256"])
    manifest["set_sha256"] = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
    (design_dir / "设计集清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

def main() -> int:
    code, report = run_case(PRD_BASE)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"完全一致样本应为 ok/0: {code}, {report.get('exit_reason')}")

    hallucinated = PRD_BASE.replace(
        "| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |",
        "| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |\n| 不存在字段 | 字符串 | 否 | 无 | 无 | 订单服务 | 幻觉字段 |",
    )
    code, report = run_case(hallucinated)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"幻觉字段应阻断并返回 1: {code}, {report.get('exit_reason')}")
    if not report["classification"]["deterministic_conflicts"]["fields"]:
        raise AssertionError("幻觉字段未进入 deterministic_conflict 分类")

    # 回归：Design 没有的泛化字段「主题指标」继续被识别为确定性多出字段。
    theme_index_prd = PRD_BASE.replace(
        "| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |",
        "| 订单编号 | 字符串 | 是 | 无 | 无 | 订单服务 | 订单唯一编号 |\n| 主题指标 | 枚举 | 否 | 无 | 无 | 统计服务 | 泛化指标字段 |",
    )
    code, report = run_case(theme_index_prd)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"主题指标应继续被识别为确定性多出字段: {code}, {report.get('exit_reason')}")
    theme_items = [
        f for f in report["classification"]["deterministic_conflicts"]["fields"]
        if (f.get("name") if isinstance(f, dict) else f) == "主题指标"
    ]
    if not theme_items:
        raise AssertionError(f"主题指标未进入确定性多出字段分类: {report['classification']['deterministic_conflicts']['fields']}")

    enum_conflict = PRD_BASE.replace("草稿、已完成", "草稿、已归档").replace("| 状态 | 枚举 | 是 | 草稿、已归档 |", "| 状态 | 枚举 | 是 | 草稿、已归档 |")
    code, report = run_case(enum_conflict)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"枚举冲突应阻断并返回 1: {code}, {report.get('exit_reason')}")

    permission_reversal = PRD_BASE.replace("运营人员：允许查看订单", "运营人员：不可查看订单")
    code, report = run_case(permission_reversal)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"权限反转应阻断并返回 1: {code}, {report.get('exit_reason')}")
    if not report.get("permission_inversions"):
        raise AssertionError("权限反转未输出分类详情")

    required_reversal = PRD_BASE.replace("| 订单编号 | 字符串 | 是 |", "| 订单编号 | 字符串 | 否 |", 1)
    code, report = run_case(required_reversal)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"必填反转应阻断并返回 1: {code}, {report.get('exit_reason')}")
    if not report["classification"]["deterministic_conflicts"]["field_attributes"]:
        raise AssertionError("必填反转未进入 deterministic_conflict 分类")

    omission = PRD_BASE.replace("| 状态 | 枚举 | 是 | 草稿、已完成 | 草稿 | 订单服务 | 订单处理状态 |\n", "")
    code, report = run_case(omission)
    if code != 0 or report.get("exit_reason") != "possible_omission":
        raise AssertionError(f"可能遗漏应保留分类但返回 0: {code}, {report.get('exit_reason')}")
    if not report["classification"]["possible_omissions"]["fields"]:
        raise AssertionError("可能遗漏未输出分类详情")

    semantic = PRD_BASE.replace("| 订单编号 | 字符串 |", "| 订单编号 | 整数 |", 1)
    code, report = run_case(semantic)
    if code != 0 or report.get("exit_reason") != "needs_semantic_judgment":
        raise AssertionError(f"字段类型差异应返回语义判断/0: {code}, {report.get('exit_reason')}")
    if not report["classification"]["needs_semantic_judgment"]["attribute_mismatches"]:
        raise AssertionError("语义判断项目未输出分类详情")

    code, report = run_case(NEW_STRUCTURE_PRD)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"分散字段和不同业务模块名称样本应为 ok/0: {code}, {report.get('exit_reason')}\n{report}")
    if report["extracted"]["prd_fields_count"] != 2:
        raise AssertionError(f"分散字段表未合并读取: {report['extracted']}")

    # 回归：斜杠合并字段拆分后应匹配 Design 两侧字段，不再整体判为缺失或新增。
    code, report = run_case(SLASH_FIELD_PRD, design=SLASH_FIELD_DESIGN)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"斜杠合并字段样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["extracted"]["prd_fields_count"] != 2:
        raise AssertionError(f"斜杠合并字段未拆分: {report['extracted']}")
    if report["fields"]["missing"] or report["fields"]["hallucinated"]:
        raise AssertionError(f"斜杠合并字段拆分后仍误报: {report['fields']}")

    # 回归：页面"数据字典"与章节同名，不应被黑名单误过滤为缺失。
    code, report = run_case(DICT_PAGE_PRD, design=DICT_PAGE_DESIGN)
    if code != 0:
        raise AssertionError(f"数据字典页面样本不应是确定性冲突: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["pages"]["missing"] or report["pages"]["hallucinated"]:
        raise AssertionError(f"数据字典页面被误报: {report['pages']}")
    # 页面只在页面清单出现、未在 4.x.6 正文落点时，列为页面正文落点可能遗漏（退出码 0）。
    if report.get("exit_reason") != "possible_omission":
        raise AssertionError(f"只在清单出现的页面应列为可能遗漏: {code}, {report.get('exit_reason')}")
    page_body_names = {
        item.get("name")
        for item in report["classification"]["possible_omissions"].get("page_body", [])
    }
    if "数据字典" not in page_body_names:
        raise AssertionError(f"数据字典页面未进入页面正文落点候选: {report['classification']['possible_omissions']}")

    # 回归：同名"状态"字段按对象区分，不跨对象误配属性。
    code, report = run_case(SAME_NAME_PRD, design=SAME_NAME_DESIGN)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"同名状态按对象区分样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["fields"]["attribute_mismatch"]:
        raise AssertionError(f"同名状态字段跨对象误配: {report['fields']['attribute_mismatch']}")

    # 回归：权限解析为空时输出"无法提取、需人工验收"信号，不显示为权限一致。
    no_perm_prd = PRD_BASE.split("## 权限定义")[0].rstrip() + "\n"
    code, report = run_case(no_perm_prd)
    perm_eval = report.get("permission_evaluation", {})
    if perm_eval.get("status") != "cannot_extract" or "需人工验收" not in perm_eval.get("message", ""):
        raise AssertionError(f"权限提取为空未给出无法提取信号: {perm_eval}")
    if report.get("permissions", {}).get("not_evaluated") is not True:
        raise AssertionError("权限未提取时 missing/hallucinated 应标记为 not_evaluated")

    # P1 回归：新模板"类型/取值"合并列 + 无"必填"列，严格照模板写不应误报确定性冲突。
    code, report = run_case(NEW_TEMPLATE_4COL_PRD)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"新模板四列字段表样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")
    if report["extracted"]["prd_fields_count"] != 2:
        raise AssertionError(f"新模板四列字段表未合并读取: {report['extracted']}")

    # P1 回归：新模板四列 + 显式"必填"列（对抗探针 CLEAN 写法）同样应为 ok。
    code, report = run_case(NEW_TEMPLATE_5COL_PRD)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"新模板四列+必填列样本应为 ok/0: {code}, {report.get('exit_reason')}\n{json.dumps(report.get('classification'), ensure_ascii=False)}")

    # P1 回归：内联枚举仍须拦截真实冲突（枚举值差异 → deterministic_conflict/1）。
    enum_conflict_new = NEW_TEMPLATE_5COL_PRD.replace("枚举：草稿、已完成", "枚举：草稿、已归档")
    code, report = run_case(enum_conflict_new)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"新模板内联枚举冲突应阻断并返回 1: {code}, {report.get('exit_reason')}")
    enum_items = [item for item in report["classification"]["deterministic_conflicts"]["field_enums"] if item.get("name") == "状态"]
    if not enum_items or "已完成" not in enum_items[0].get("enum_missing", []):
        raise AssertionError(f"内联枚举冲突未正确归类: {enum_items}")

    # P2-1 回归：枚举值仅空白差异（Design「10年」vs PRD「10 年」）不应判确定性冲突。
    design_ws = DESIGN.replace("草稿、已完成", "10年、20年、永久")
    prd_ws = PRD_BASE.replace("草稿、已完成", "10 年、20 年、永久")
    code, report = run_case(prd_ws, design_ws)
    if code != 0 or report.get("exit_reason") != "ok":
        raise AssertionError(f"枚举空白差异应 ok/0: {code}, {report.get('exit_reason')}")
    # 真阳性仍须拦截：枚举值实质不同（「已归档」替换「永久」）判确定性冲突/1。
    enum_real = prd_ws.replace("10 年、20 年、永久", "10 年、20 年、已归档")
    code, report = run_case(enum_real, design_ws)
    if code != 1 or report.get("exit_reason") != "deterministic_conflict":
        raise AssertionError(f"枚举实质差异应确定性冲突: {code}, {report.get('exit_reason')}")

    # P1 回归：extract_prd_fields 能从"类型/取值"列解析内联枚举，且识别无"必填"列表。
    spec = importlib.util.spec_from_file_location("prd_consistency_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise AssertionError("无法加载一致性脚本模块")
    spec.loader.exec_module(module)
    headings = module.parse_headings(PAGE_MAPPING_PRD)
    pages = module.extract_prd_pages(PAGE_MAPPING_PRD, headings)
    if pages != ["订单列表", "现场处置"]:
        raise AssertionError(f"总体说明页面清单提取错误: {pages}")

    headings4 = module.parse_headings(NEW_TEMPLATE_4COL_PRD)
    tables4 = module.parse_tables_with_context(NEW_TEMPLATE_4COL_PRD, headings4)
    fields4 = module.extract_prd_fields(headings4, tables4, NEW_TEMPLATE_4COL_PRD)
    status4 = next((f for f in fields4 if f["name"] == "状态"), None)
    if status4 is None or status4.get("enum_values") != ["已完成", "草稿"]:
        raise AssertionError(f"新模板内联枚举未从类型/取值列解析: {status4}")
    if status4.get("has_required_column") is not False:
        raise AssertionError(f"新模板四列字段表应标记无必填列: {status4}")

    # 回归：Design 页面只在页面清单出现、未在 4.x.6 正文落点 → 页面正文落点可能遗漏。
    page_list_only_prd = """# PRD 正文

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 所属业务闭环 | 主要承接阶段 |
|---|---|---|---|
| 两客一危统计 | 管理端 | 两客一危核查与告警 | 统计与下钻 |
| 车辆信息记录 | 管理端 | 车辆记录与离场 | 记录查询 |

## 功能需求

### 两客一危核查与告警

#### 4.4.6 功能详细说明

##### 4.4.6.1 两客一危车辆查看

两客一危车辆查看展示比对状态和核查入口。
"""
    headings_pl = module.parse_headings(page_list_only_prd)
    landing = module.find_page_body_landing_issues(
        page_list_only_prd, headings_pl, ["两客一危统计", "车辆信息记录"]
    )
    omission_names = {item["name"] for item in landing["body_omissions"]}
    if "两客一危统计" not in omission_names:
        raise AssertionError(f"页面只在清单出现未列为可能遗漏: {landing}")
    if landing["page_merges"]:
        raise AssertionError(f"未出现合并时不应有合并候选: {landing}")
    # 页面在 4.x.6 正文有落点时不误报。
    landed_prd = page_list_only_prd.replace(
        "##### 4.4.6.1 两客一危车辆查看",
        "##### 4.4.6.1 两客一危统计\n\n两客一危统计展示统计指标。\n\n##### 4.4.6.2 两客一危车辆查看",
    )
    headings_lp = module.parse_headings(landed_prd)
    landing_lp = module.find_page_body_landing_issues(landed_prd, headings_lp, ["两客一危统计", "车辆信息记录"])
    if any(item["name"] == "两客一危统计" for item in landing_lp["body_omissions"]):
        raise AssertionError(f"页面已在 4.x.6 落点仍被误报: {landing_lp}")

    # 回归：页面在 4.x.6 正文明确写出合并关系时，不判为确定性错误，交 Review 判断。
    merged_prd = """# PRD 正文

## 总体说明

### 页面清单

| 页面/入口 | 终端 | 所属业务闭环 | 主要承接阶段 |
|---|---|---|---|
| 监控点列表 | 管理端 | 车流和车位实时监测 | 监控绑定 |
| 监控点详情 | 管理端 | 车流和车位实时监测 | 监控绑定 |
| 监控点位管理 | 管理端 | 车流和车位实时监测 | 监控绑定 |

## 功能需求

### 车流和车位实时监测

#### 4.2.6 功能详细说明

##### 4.2.6.1 监控点位管理

监控点列表与监控点详情合并为监控点位管理，绑定结果在详情中展示。
"""
    headings_mp = module.parse_headings(merged_prd)
    landing_mp = module.find_page_body_landing_issues(
        merged_prd, headings_mp, ["监控点列表", "监控点详情", "监控点位管理"]
    )
    if any(item["name"] in {"监控点列表", "监控点详情"} for item in landing_mp["body_omissions"]):
        raise AssertionError(f"明确合并页面不应列为可能遗漏: {landing_mp}")
    merge_names = {item["name"] for item in landing_mp["page_merges"]}
    if not {"监控点列表", "监控点详情"} <= merge_names:
        raise AssertionError(f"合并页面未进入合并候选交 Review 判断: {landing_mp}")
    if "监控点位管理" in merge_names:
        raise AssertionError(f"有独立 4.x.6 子标题落点的合并结果页不应进入合并候选: {landing_mp}")

    # 回归：状态组合值拆分 + "下一状态"列 + 同章节箭头状态都应被提取。
    headings_cs = module.parse_headings(COMBINED_STATE_PRD)
    tables_cs = module.parse_tables_with_context(COMBINED_STATE_PRD, headings_cs)
    states_cs = module.extract_prd_states(COMBINED_STATE_PRD, headings_cs, tables_cs)
    if set(states_cs) != {"启用", "停用", "进行中", "已通过", "草稿", "已发出", "待签署"}:
        raise AssertionError(f"状态组合值/下一状态/箭头未正确提取: {states_cs}")

    # 回归：PRD 用自然语言枚举状态时必须能提取（规范禁止正文用状态表）。
    headings_ps = module.parse_headings(PRD_PROSE_STATES)
    prose_states = module.extract_prd_prose_states(PRD_PROSE_STATES, headings_ps)
    if set(prose_states) != {"草稿", "待审核", "已完成"}:
        raise AssertionError(f"自然语言状态枚举未正确提取: {prose_states}")

    # 回归：下拉框/筛选项等界面构件里的括号枚举不是业务状态，不得被当状态来源。
    ui_prd = "## 详细需求说明\n\n筛选栏常设运行状态下拉框（全部状态、在营中、已停用）。\n"
    headings_ui = module.parse_headings(ui_prd)
    ui_states = module.extract_prd_prose_states(ui_prd, headings_ui)
    if ui_states:
        raise AssertionError(f"界面构件括号枚举被误当成业务状态: {ui_states}")

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "output/design").mkdir(parents=True)
        (root / "output/prd").mkdir(parents=True)
        write_design_set(root, DESIGN)
        missing = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if missing.returncode != 2:
            raise AssertionError(f"输入缺失应返回 2: {missing.returncode}")

    # 回归：Design 有状态机、PRD 用自然语言枚举时，已表达的状态不得判为遗漏。
    _, report_prose = run_case(PRD_PROSE_STATES, DESIGN_WITH_STATE_MACHINE)
    if report_prose["states"]["missing"]:
        raise AssertionError(f"PRD 已用自然语言表达的状态不应判为遗漏: {report_prose['states']}")
    if report_prose["state_evaluation"]["status"] != "extracted":
        raise AssertionError(f"状态已提取时应报告 extracted: {report_prose['state_evaluation']}")

    # 回归：真漏掉的状态必须仍被检出，修复不得把状态维度做成摆设。
    dropped_state = PRD_PROSE_STATES.replace("草稿、待审核与已完成", "草稿与已完成")
    _, report_dropped = run_case(dropped_state, DESIGN_WITH_STATE_MACHINE)
    if "待审核" not in report_dropped["states"]["missing"]:
        raise AssertionError(f"PRD 真漏的状态必须被检出: {report_dropped['states']}")

    # 回归：状态完全解析不到时标记未评估，不把解析失败伪造成遗漏清单。
    no_state_prd = "# 订单 PRD\n\n## 详细需求说明\n\n订单编号为订单唯一编号。\n"
    _, report_none = run_case(no_state_prd, DESIGN_WITH_STATE_MACHINE)
    if not report_none["states"].get("not_evaluated"):
        raise AssertionError(f"状态解析为空时应标记未评估: {report_none['states']}")
    if report_none["states"]["missing"]:
        raise AssertionError(f"未评估时不得输出状态遗漏清单: {report_none['states']['missing']}")
    if report_none["state_evaluation"]["status"] != "cannot_extract":
        raise AssertionError(f"状态解析为空时应报告 cannot_extract: {report_none['state_evaluation']}")

    # ── 权限维度回归（R23 RC-1 / RC-2）──
    # 1) 合规「角色 × 业务能力」矩阵：能力列不得进入 page ID 空间，章节自身标题不得被当页面名。
    code, report = run_case(PRD_CAPABILITY_MATRIX, design=MODULE_INDEXED)
    if code != 0:
        raise AssertionError(f"合规能力矩阵 PRD 不应阻断: exit={code}, {report.get('exit_reason')}")
    perms = report["permissions"]
    if perms["hallucinated"] or perms["missing"]:
        raise AssertionError(f"能力矩阵不应产生权限页面级冲突: {perms}")
    if "角色与权限" in perms["hallucinated"]:
        raise AssertionError("权限章节自身标题不得被当作权限页面名")
    facts = report["permission_facts"]
    if facts["design_source"] != "design-index":
        raise AssertionError(f"Design 侧权限应来自 design-index: {facts['design_source']}")
    if set(facts["design_roles"]) != {"运营人员", "财务人员"}:
        raise AssertionError(f"Design 角色切分应剥离括号且不混入条件式描述: {facts['design_roles']}")
    if facts["prd_permission_pages"]:
        raise AssertionError(f"能力列不得进入 page 集合: {facts['prd_permission_pages']}")
    if facts["prd_permission_capabilities"] != ["查看订单", "导出订单"]:
        raise AssertionError(f"业务能力列应作为事实输出: {facts['prd_permission_capabilities']}")
    if facts["comparable"]:
        raise AssertionError("两侧不同构时不得标记为可确定性比对")
    if report["permission_evaluation"]["status"] != "not_evaluated":
        raise AssertionError(f"两侧不同构应标记未评估: {report['permission_evaluation']}")

    # 2) 存量自然语言 4.x.3（审计系统形态）：红线——不得产生成批 missing。
    code, report = run_case(PRD_PROSE_PERMISSION, design=MODULE_INDEXED)
    if report["permissions"]["missing"]:
        raise AssertionError(f"PRD 用自然语言表达权限时不得判为缺失: {report['permissions']}")
    if report["permission_evaluation"]["status"] != "cannot_extract":
        raise AssertionError(f"PRD 权限无法提取时应报 cannot_extract: {report['permission_evaluation']}")
    if "Design 权限为空" in report["permission_evaluation"]["message"]:
        raise AssertionError("Design 侧已有权限事实时不得报「Design 权限为空」")

    # 3) 「行 = 页面，列 = 角色」与 Design 同构：必须保持确定性比对能力，不得被一并降级。
    code, report = run_case(PRD_ROW_OBJECT_PERMISSION, design=MODULE_INDEXED)
    facts = report["permission_facts"]
    if not facts["comparable"]:
        raise AssertionError("行=页面矩阵应可确定性比对")
    if report["permissions"]["matched_count"] < 1:
        raise AssertionError(f"行=页面矩阵应匹配到页面权限: {report['permissions']}")
    if report["permission_role_pairs"]["matched_count"] < 2:
        raise AssertionError(f"行=页面矩阵应匹配到角色对: {report['permission_role_pairs']}")
    if report["permissions"]["hallucinated"] or report["permission_role_pairs"]["hallucinated"]:
        raise AssertionError("行=页面矩阵不应产生幻觉判定")

    # 4) 旧格式「## 权限汇总 / ### 页面名 / - role：action」：确定性比对能力不得回退（RC-2 防回归）。
    code, report = run_case(PRD_LEGACY_PERMISSION_SUMMARY, design=MODULE_INDEXED)
    if code != 0:
        raise AssertionError(f"旧格式权限汇总不应阻断: exit={code}, {report.get('exit_reason')}")
    if not report["permission_facts"]["comparable"]:
        raise AssertionError("旧格式 权限汇总 应保持可确定性比对")
    if report["permissions"]["matched_count"] < 1:
        raise AssertionError(f"旧格式 权限汇总 应匹配到页面权限: {report['permissions']}")

    print("test-prd-consistency-semantics: PASS（新结构页面映射、分散字段、斜杠合并字段、数据字典页面、状态组合值、自然语言状态枚举、状态未评估、同名按对象、权限 zero 信号、权限事实来源收敛、能力列不进 page、行=页面矩阵仍确定性、旧格式权限汇总不回退、冲突、遗漏、语义判断和致命错误）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
