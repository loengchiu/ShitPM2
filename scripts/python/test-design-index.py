#!/usr/bin/env python3
"""design-index.py 及其下游一致性接入的直接测试。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("design-index.py")


def load_module():
    spec = importlib.util.spec_from_file_location("design_index", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VALID_DESIGN = """# 设计基线

### 页面：订单列表
目的：查看和处理订单
角色：运营人员
进入条件：已登录
数据范围：本人所属组织订单
主要状态：待处理、已完成

#### 区块：筛选条件
目的：按条件缩小订单范围

##### 字段：订单编号
业务含义：订单的唯一业务编号
必填：是
来源：订单服务
展示条件：始终展示
输入编辑：可输入，不可修改已有值
取值默认：默认空值
交互：文本输入
校验反馈：格式错误时提示

##### 字段：状态
业务含义：订单当前处理状态
来源：订单服务
展示条件：始终展示
输入编辑：可选择
取值默认：默认全部
交互：单选
校验反馈：无

##### 操作：查询
适用角色：运营人员
可用条件：输入条件合法
确认：无需确认
成功结果：刷新订单列表
状态变化：无
失败恢复：保留当前筛选条件并提示
去向：仍停留在订单列表
"""

VALID_PRD = """# PRD
### 页面：订单列表
#### 区块：筛选条件
##### 字段：订单编号
必填：是
来源：订单服务
展示条件：始终展示
##### 字段：状态
来源：订单服务
展示条件：始终展示
##### 操作：查询
成功结果：刷新订单列表
状态变化：无
"""

VALID_HTML = """<main><section data-page="订单列表"><h1>订单列表</h1><div data-block="筛选条件"><h2>筛选条件</h2><label data-field="订单编号">订单编号</label><label data-field="状态">状态</label><button data-operation="查询">查询</button><span data-state="待处理">待处理</span><span data-state="已完成">已完成</span></div></section></main>"""


STANDARD_PRD = """# PRD

## 5. 详细需求说明

**5.1.1 订单列表**

· 查询
输入条件合法时刷新订单列表；失败时保留筛选条件并提示。

| 字段 | 类型 | 必填 | 取值约束 | 默认值 | 业务来源 | 说明 |
|------|------|------|----------|--------|----------|------|
| 订单编号 | 文本 | 是 | — | 默认空值 | 订单服务 | 订单的唯一业务编号 |
| 状态 | 单选 | 否 | — | 默认全部 | 订单服务 | 订单当前处理状态 |
"""

LEGACY_DESIGN = """# 设计基线

## 页面说明

| 页面 | 目的 | 角色 |
|---|---|---|
| 订单列表 | 查看和处理订单 | 运营人员 |

## 字段定义

| 字段 | 来源 |
|---|---|
| 订单编号 | 订单服务 |
"""

TABLE_DESIGN = """# 设计基线

## 七、页面、区块、字段与操作设计

### 页面清单（可选速览）

| 页面 | 用户任务 | 适用角色 | 主要入口/去向 |
| --- | --- | --- | --- |
| 订单列表 | 查看和处理订单 | 运营人员 | 工作台进入 |

### 页面：订单列表

- 页面目的：查看和处理订单
- 适用角色：运营人员
- 进入条件：已登录
- 数据范围：本人所属组织订单
- 主要状态：待处理、已完成

#### 区块：筛选条件

- 区块目的：按条件缩小订单范围

##### 字段表

| 字段名称 | 业务含义 | 字段来源 | 展示条件 | 输入与编辑规则 | 取值与默认规则 | 交互方式 | 校验与反馈 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 订单编号 | 订单的唯一业务编号 | 订单服务 | 始终展示 | 可输入，不可修改已有值 | 默认空值 | 文本输入 | 格式错误时提示 |
| 状态 | 订单当前处理状态 | 订单服务 | 始终展示 | 可选择 | 默认全部 | 单选 | 无 |

#### 页面操作

- 区块目的：定义本页面可执行的业务操作及其结果。

##### 操作表

| 操作 | 适用角色 | 入口/触发方式 | 输入（字段级） | 展示与可用条件 | 是否二次确认 | 成功结果 | 数据与状态变化 | 失败与恢复 | 后续去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 查询 | 运营人员 | 页面上“查询”按钮 | 见筛选区块字段表 | 输入条件合法 | 否 | 刷新订单列表 | 无 | 保留当前筛选条件并提示 | 仍停留在订单列表 |
"""


class DesignIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        design_dir = self.root / "output" / "design"
        module_dir = design_dir / "模块设计" / "订单"
        module_dir.mkdir(parents=True)
        module_path = module_dir / "订单管理.md"
        module_path.write_text(VALID_DESIGN, encoding="utf-8")
        map_path = design_dir / "设计地图.md"
        map_path.write_text("# 设计地图\n\n## 模块与职责\n\n- MOD-001 [订单](模块设计/订单/订单管理.md)：负责订单。\n", encoding="utf-8")
        manifest = {
            "schema_version": "shitpm-design-set/v1",
            "set_sha256": "",
            "files": [
                {"id": "MAP-001", "path": "设计地图.md", "type": "map", "module": None, "business_chains": [], "depends_on": [], "sha256": hashlib.sha256(map_path.read_bytes()).hexdigest()},
                {"id": "MOD-001", "path": "模块设计/订单/订单管理.md", "type": "module", "module": "订单", "business_chains": ["订单业务链"], "depends_on": [], "sha256": hashlib.sha256(module_path.read_bytes()).hexdigest()},
            ],
            "decisions": [],
        }
        parts = []
        for f in sorted(manifest["files"], key=lambda x: x["id"]):
            parts.append(f["id"] + f["path"] + f["sha256"])
        manifest["set_sha256"] = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
        (design_dir / "设计集清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        self.mod = load_module()

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, command, *extra):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), command, "--project-root", str(self.root), *extra],
            text=True,
            capture_output=True,
            check=False,
        )
        return completed.returncode, json.loads(completed.stdout)

    def write_downstream(self, prd=None, html=None):
        if prd is not None:
            path = self.root / "output" / "prd"
            path.mkdir(parents=True, exist_ok=True)
            (path / "prd.md").write_text(prd, encoding="utf-8")
        if html is not None:
            path = self.root / "output" / "prototype" / "src"
            path.mkdir(parents=True, exist_ok=True)
            (path / "OrderPage.jsx").write_text(html, encoding="utf-8")
            (path / "routes.jsx").write_text(
                'export const routes = [{ path: "/orders", title: "订单列表", module: "订单", component: OrderPage }, { path: "*", element: <Placeholder /> }];\n',
                encoding="utf-8",
            )
        code, output = self.run_cli("compile")
        self.assertEqual(code, 0, output)

    def run_downstream(self, script_name):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "python" / script_name), "--project-root", str(self.root)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_compile_and_check_are_deterministic(self):
        first = self.mod.compile_index(self.root)
        second = self.mod.compile_index(self.root)
        self.assertEqual(first, second)
        self.assertEqual(first["file_sha256"]["MOD-001"], hashlib.sha256((self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_bytes()).hexdigest())
        self.assertEqual(first["summary"], {"files": 2, "pages": 1, "blocks": 1, "fields": 2, "operations": 1, "errors": 0})
        self.assertEqual(first["pages"][0]["blocks"][0]["fields"][0]["name"], "订单编号")
        self.assertEqual(first["pages"][0]["blocks"][0]["operations"][0]["attributes"]["success_result"], "刷新订单列表")
        self.assertEqual({item["name"] for item in first["states"]}, {"待处理", "已完成"})

        code, output = self.run_cli("compile")
        self.assertEqual(code, 0, output)
        self.assertTrue((self.root / self.mod.INDEX_RELATIVE_PATH).is_file())
        code, output = self.run_cli("check")
        self.assertEqual(code, 0, output)
        self.assertTrue(output["ok"])

    def test_missing_attribute_and_invalid_level_fail(self):
        bad = VALID_DESIGN.replace("校验反馈：格式错误时提示\n", "").replace("#### 区块：筛选条件", "### 区块：筛选条件")
        (self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text(bad, encoding="utf-8")
        data = self.mod.compile_index(self.root)
        codes = {item["code"] for item in data["errors"]}
        self.assertIn("missing_attribute", codes)
        self.assertIn("block_without_page", codes)
        code, output = self.run_cli("compile")
        self.assertEqual(code, 1, output)
        self.assertFalse(output["ok"])

    def test_duplicate_and_semantic_conflict_fail(self):
        duplicate = VALID_DESIGN.replace(
            "##### 字段：状态\n业务含义：订单当前处理状态",
            "##### 字段：状态\n业务含义：另一个含义\n来源：其他服务\n展示条件：始终展示\n输入编辑：可选择\n取值默认：默认全部\n交互：单选\n校验反馈：无\n\n##### 字段：状态\n业务含义：订单当前处理状态",
        )
        (self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text(duplicate, encoding="utf-8")
        data = self.mod.compile_index(self.root)
        codes = {item["code"] for item in data["errors"]}
        self.assertIn("duplicate_entity", codes)
        self.assertIn("semantic_conflict", codes)

    def test_check_rejects_hash_or_index_tampering(self):
        code, output = self.run_cli("compile")
        self.assertEqual(code, 0, output)
        design_path = self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md"
        design_path.write_text(VALID_DESIGN.replace("订单列表", "我的订单列表", 1), encoding="utf-8")
        code, output = self.run_cli("check")
        self.assertEqual(code, 1, output)
        self.assertFalse(output["ok"])
        self.assertIn("指纹", output.get("error", ""))

        design_path.write_text(VALID_DESIGN, encoding="utf-8")
        index_path = self.root / self.mod.INDEX_RELATIVE_PATH
        data = json.loads(index_path.read_text(encoding="utf-8"))
        data["pages"][0]["name"] = "不存在的页面"
        index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        code, output = self.run_cli("check")
        self.assertEqual(code, 1, output)
        self.assertIn("索引内容", output.get("error", ""))

    def test_standard_prd_format_accepts_indexed_design(self):
        self.write_downstream(STANDARD_PRD)
        run = self.run_downstream("prd-consistency-check.py")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["design_index"]["structure"]["missing"], [])
        self.assertEqual(result["design_index"]["structure"]["hallucinated"], [])

    def test_standard_prd_missing_field_is_rejected(self):
        self.write_downstream(STANDARD_PRD.replace("| 状态 | 单选 | 否 | — | 默认全部 | 订单服务 | 订单当前处理状态 |\n", ""))
        run = self.run_downstream("prd-consistency-check.py")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        missing = json.loads(run.stdout)["design_index"]["structure"]["missing"]
        self.assertTrue(any(item.get("name") == "状态" for item in missing))

    def test_table_preamble_does_not_discard_valid_table(self):
        with_preamble = TABLE_DESIGN.replace(
            "##### 字段表\n\n|",
            "##### 字段表\n\n以下字段用于描述订单筛选条件。\n\n<!-- 表格说明 -->\n\n|",
        ).replace(
            "##### 操作表\n\n|",
            "##### 操作表\n\n以下操作用于完成订单查询。\n\n<!-- 操作说明 -->\n\n|",
        )
        (self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text(with_preamble, encoding="utf-8")
        code, output = self.run_cli("compile", "--require-current-format")
        self.assertEqual(code, 0, output)
        self.assertTrue(output["ok"])

    def test_table_format_compiles_with_complete_field_and_operation_index(self):
        (self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text(TABLE_DESIGN, encoding="utf-8")
        code, output = self.run_cli("compile", "--require-current-format")
        self.assertEqual(code, 0, output)
        self.assertEqual(output["summary"], {"files": 2, "pages": 1, "blocks": 2, "fields": 2, "operations": 1, "errors": 0})
        index = json.loads((self.root / self.mod.INDEX_RELATIVE_PATH).read_text(encoding="utf-8"))
        self.assertEqual([item["name"] for item in index["fields"]], ["订单编号", "状态"])
        self.assertEqual(index["operations"][0]["name"], "查询")
        self.assertEqual(index["operations"][0]["attributes"]["state_change"], "无")

    def test_current_format_rejects_legacy_field_and_operation_headings(self):
        code, output = self.run_cli("compile", "--require-current-format")
        self.assertEqual(code, 1, output)
        codes = {item["code"] for item in output["errors"]}
        self.assertIn("outdated_field_format", codes)
        self.assertIn("outdated_operation_format", codes)

    def test_table_headers_and_page_summary_are_gated(self):
        invalid = TABLE_DESIGN.replace("| 字段名称 | 业务含义 | 字段来源 | 展示条件 | 输入与编辑规则 | 取值与默认规则 | 交互方式 | 校验与反馈 |", "| 字段名称 | 业务含义 | 字段来源 | 展示条件 | 交互方式 | 校验与反馈 |")
        (self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text(invalid, encoding="utf-8")
        code, output = self.run_cli("compile", "--require-current-format")
        self.assertEqual(code, 1, output)
        self.assertTrue(any(item["code"] == "invalid_field_table_headers" for item in output["errors"]))

        mismatch = TABLE_DESIGN.replace("| 订单列表 | 查看和处理订单 | 运营人员 | 工作台进入 |", "| 其他页面 | 其他任务 | 运营人员 | 工作台进入 |")
        (self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text(mismatch, encoding="utf-8")
        code, output = self.run_cli("compile", "--require-current-format")
        self.assertEqual(code, 1, output)
        codes = {item["code"] for item in output["errors"]}
        self.assertIn("page_summary_missing_detail", codes)
        self.assertIn("page_detail_missing_summary", codes)

    def test_combined_field_and_empty_blocks_are_gated(self):
        combined = TABLE_DESIGN.replace("| 状态 | 订单当前处理状态 |", "| 状态 / 订单状态 | 订单当前处理状态 |")
        (self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text(combined, encoding="utf-8")
        code, output = self.run_cli("compile", "--require-current-format")
        self.assertEqual(code, 1, output)
        self.assertTrue(any(item["code"] == "combined_field_name" for item in output["errors"]))

        empty = TABLE_DESIGN.replace("#### 区块：筛选条件", "#### 区块：空区块\n\n- 区块目的：暂未定义\n\n#### 区块：筛选条件")
        (self.root / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text(empty, encoding="utf-8")
        code, output = self.run_cli("compile", "--require-current-format")
        self.assertEqual(code, 1, output)
        self.assertTrue(any(item["code"] == "block_without_items" for item in output["errors"]))

    def test_prd_and_prototype_accept_complete_structure(self):
        self.write_downstream(VALID_PRD, VALID_HTML)
        prd_run = self.run_downstream("prd-consistency-check.py")
        self.assertEqual(prd_run.returncode, 0, prd_run.stdout + prd_run.stderr)
        prd_result = json.loads(prd_run.stdout)
        self.assertTrue(prd_result["design_index"]["used"])
        self.assertEqual(prd_result["design_index"]["structure"]["missing"], [])
        prototype_run = self.run_downstream("prototype-consistency-check.py")
        self.assertEqual(prototype_run.returncode, 0, prototype_run.stdout + prototype_run.stderr)
        prototype_result = json.loads(prototype_run.stdout)
        self.assertFalse(prototype_result["classification"]["deterministic_conflicts"])

    def test_prd_detects_missing_added_and_changed_indexed_items(self):
        # 新格式（design-index 激活）下：页面/字段按名称级确定比较；
        # 缺失字段只输出 possible_omission 候选（退出码 0）；新增字段为确定性幻觉（退出码 1）；
        # 新格式正文属性（必填/来源/成功结果）不再逐字比较，差异归语义判断，不产生 attribute_mismatch。
        self.write_downstream(STANDARD_PRD)
        missing = STANDARD_PRD.replace("| 状态 | 单选 | 否 | — | 默认全部 | 订单服务 | 订单当前处理状态 |\n", "")
        (self.root / "output" / "prd" / "prd.md").write_text(missing, encoding="utf-8")
        run = self.run_downstream("prd-consistency-check.py")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        report = json.loads(run.stdout)
        self.assertTrue(any(item.get("name") == "状态" for item in report["design_index"]["structure"]["missing"]))
        self.assertEqual(report.get("exit_reason"), "possible_omission")

        added = STANDARD_PRD.replace(
            "| 状态 | 单选 | 否 | — | 默认全部 | 订单服务 | 订单当前处理状态 |\n",
            "| 状态 | 单选 | 否 | — | 默认全部 | 订单服务 | 订单当前处理状态 |\n"
            "| 额外字段 | 文本 | 否 | — | — | 订单服务 | 幻觉字段 |\n",
        )
        (self.root / "output" / "prd" / "prd.md").write_text(added, encoding="utf-8")
        run = self.run_downstream("prd-consistency-check.py")
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        report = json.loads(run.stdout)
        self.assertTrue(any(item.get("name") == "额外字段" for item in report["design_index"]["structure"]["hallucinated"]))
        self.assertEqual(report.get("exit_reason"), "deterministic_conflict")

        changed = STANDARD_PRD.replace("| 订单编号 | 文本 | 是 |", "| 订单编号 | 文本 | 否 |", 1)
        (self.root / "output" / "prd" / "prd.md").write_text(changed, encoding="utf-8")
        run = self.run_downstream("prd-consistency-check.py")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["design_index"]["structure"]["attribute_mismatch"], [])
        self.assertTrue(any(
            item.get("issue") == "operations_semantic"
            for item in report["classification"]["needs_semantic_judgment"]["attribute_mismatches"]
        ))

    def test_prototype_detects_missing_state_and_added_operation(self):
        self.write_downstream(html=VALID_HTML)
        missing = VALID_HTML.replace('data-state="已完成">已完成', "")
        (self.root / "output" / "prototype" / "src" / "OrderPage.jsx").write_text(missing, encoding="utf-8")
        run = self.run_downstream("prototype-consistency-check.py")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        report = json.loads(run.stdout)
        self.assertTrue(any(
            item.get("name") == "已完成"
            for item in report["classification"]["needs_semantic_judgment"]
        ))

        added = VALID_HTML.replace('<button data-operation="查询">查询</button>', '<button data-operation="查询">查询</button><button data-operation="删除">删除</button>')
        (self.root / "output" / "prototype" / "src" / "OrderPage.jsx").write_text(added, encoding="utf-8")
        run = self.run_downstream("prototype-consistency-check.py")
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        report = json.loads(run.stdout)
        self.assertTrue(any(
            item.get("name") == "删除"
            for item in report["classification"]["deterministic_conflicts"]
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
