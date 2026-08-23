from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "scripts/python/prototype-consistency-check.py"
INDEX = ROOT / "scripts/python/design-index.py"
PYTHON = sys.executable


DESIGN = """# 测试系统 Design

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
来源：订单服务
展示条件：始终展示
输入编辑：可输入
取值默认：默认空值
交互：文本输入
校验反馈：格式错误时提示

##### 操作：查询
适用角色：运营人员
可用条件：输入条件合法
确认：无需确认
成功结果：刷新订单列表
状态变化：无
失败恢复：保留当前筛选条件并提示
去向：仍停留在订单列表
"""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def write_fixture(root: Path, *, routes: str | None = None, source: str | None = None) -> None:
    design_dir = root / "output" / "design"
    module_dir = design_dir / "模块设计" / "测试"
    module_dir.mkdir(parents=True, exist_ok=True)
    design_path = module_dir / "测试系统.md"
    design_path.write_text(DESIGN, encoding="utf-8")
    digest = hashlib.sha256(design_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "shitpm-design-set/v1",
        "set_sha256": "",
        "files": [{
            "id": "MOD-001",
            "path": "模块设计/测试/测试系统.md",
            "type": "module",
            "module": "测试",
            "business_chains": [],
            "depends_on": [],
            "sha256": digest,
        }],
        "decisions": [],
    }
    manifest["set_sha256"] = hashlib.sha256(
        ("MOD-001模块设计/测试/测试系统.md" + digest).encode("utf-8")
    ).hexdigest()
    (design_dir / "设计集清单.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    src = root / "output" / "prototype" / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "routes.jsx").write_text(routes or """export const routes = [
  { path: '/orders', title: '订单列表', component: Orders, menu: true, module: '测试' },
  { path: '*', title: '页面不存在', component: NotFound, menu: false },
];
""", encoding="utf-8")
    (src / "Orders.jsx").write_text(source or """export default function Orders() {
  return <main data-page="订单列表"><section data-block="筛选条件">
    <input data-field="订单编号" />
    <button data-operation="查询">查询</button>
    <span data-state="待处理">待处理</span>
    <span data-state="已完成">已完成</span>
  </section></main>;
}
""", encoding="utf-8")
    result = run(INDEX, "compile", "--project-root", str(root))
    check(result.returncode == 0, "fixture Design Index 编译失败: " + result.stdout + result.stderr)


def payload(result: subprocess.CompletedProcess[str]) -> dict:
    check(result.stdout.strip(), result.stdout + result.stderr)
    return json.loads(result.stdout)


def test_valid_and_stable_output() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root)
        result = run(CHECK, "--project-root", str(root))
        data = payload(result)
        check(result.returncode == 0, result.stdout)
        check(set(data["classification"]) == {"deterministic_conflicts", "possible_omissions", "needs_semantic_judgment"}, result.stdout)
        check("summary" in data and "exit_reason" in data, result.stdout)
        check(data["summary"]["deterministic_conflicts"] == 0, result.stdout)


def test_unknown_route_is_deterministic_conflict() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, routes="""export const routes = [
  { path: '/evil', title: '未授权页面', component: Evil, module: '测试' },
];
""")
        data = payload(run(CHECK, "--project-root", str(root)))
        check(data["exit_reason"] == "deterministic_conflict", str(data))
        check(any(item["code"] == "unregistered_route" for item in data["classification"]["deterministic_conflicts"]), str(data))


def test_unknown_explicit_anchors_are_deterministic_conflicts() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, source='<main data-page="订单列表" data-field="未授权字段"><button data-operation="未授权操作">删库</button><span data-state="未授权状态" /></main>')
        data = payload(run(CHECK, "--project-root", str(root)))
        conflicts = data["classification"]["deterministic_conflicts"]
        check(run(CHECK, "--project-root", str(root)).returncode == 1, str(data))
        check(sum(item["code"] == "unknown_explicit_anchor" for item in conflicts) == 3, str(data))


def test_missing_route_and_anchors_are_not_blocking() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, routes="export const routes = [{ path: '*', title: '页面不存在', component: NotFound }];", source="export default function Orders() { return <button>普通按钮</button>; }")
        result = run(CHECK, "--project-root", str(root))
        data = payload(result)
        check(result.returncode == 0, result.stdout)
        check(data["summary"]["possible_omissions"] > 0, result.stdout)
        check(data["summary"]["needs_semantic_judgment"] > 0, result.stdout)
        check(data["exit_reason"] == "possible_omission", result.stdout)


def test_placeholder_route_and_unanchored_button_are_review_items() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, routes="""export const routes = [
  { path: '/orders', title: '订单列表', component: Placeholder, placeholder: '占位' },
];
""", source="export default function Orders() { return <button>查询</button>; }")
        data = payload(run(CHECK, "--project-root", str(root)))
        codes = {item["code"] for values in data["classification"].values() for item in values}
        check("placeholder_route" in codes and "unanchored_button" in codes, str(data))
        check(data["exit_reason"] == "possible_omission", str(data))


def test_route_title_variation_is_not_a_deterministic_conflict() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, routes="""export const routes = [{ path: '/orders', title: '订单管理', component: Orders, module: '测试' }];
""")
        data = payload(run(CHECK, "--project-root", str(root)))
        codes = {item["code"] for item in data["classification"]["possible_omissions"]}
        check(data["summary"]["deterministic_conflicts"] == 0, str(data))
        check("route_page_identity_unresolved" in codes, str(data))
        check(not any(item["code"] == "design_page_without_route" for item in data["classification"]["possible_omissions"]), str(data))


def test_element_route_without_title_is_not_a_deterministic_conflict() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, routes="""export const routes = [{ path: '/orders', element: <Orders /> }];
""")
        data = payload(run(CHECK, "--project-root", str(root)))
        check(data["summary"]["deterministic_conflicts"] == 0, str(data))
        check(any(item["code"] == "route_page_identity_unresolved" for item in data["classification"]["possible_omissions"]), str(data))


def test_js_string_html_is_not_an_explicit_anchor() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, source="const html = '<div data-page=\"未授权页面\"></div>';")
        data = payload(run(CHECK, "--project-root", str(root)))
        check(not any(item.get("name") == "未授权页面" for item in data["classification"]["deterministic_conflicts"]), str(data))


def test_self_closing_button_is_a_semantic_review_item() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, source="export default function Orders() { return <button aria-label=\"删除\" />; }")
        data = payload(run(CHECK, "--project-root", str(root)))
        items = data["classification"]["needs_semantic_judgment"]
        check(any(item["code"] == "unanchored_button" and item["name"] == "删除" for item in items), str(data))


def test_compact_route_array_does_not_hide_later_routes() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root, routes="export const routes = [{path:'/orders',title:'订单列表',component:Orders},{path:'/evil',title:'未授权页面',component:Evil}];")
        data = payload(run(CHECK, "--project-root", str(root)))
        conflicts = data["classification"]["deterministic_conflicts"]
        check(any(item["code"] == "unregistered_route" and item["path"] == "/evil" for item in conflicts), str(data))


def test_excluded_directories_and_hidden_content_are_ignored() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        write_fixture(root)
        proto = root / "output" / "prototype"
        for directory in ("dist", "node_modules", "prototype-p0"):
            target = proto / directory
            target.mkdir()
            (target / "bad.jsx").write_text('<div data-page="未授权页面" />', encoding="utf-8")
        (proto / "src" / "Hidden.jsx").write_text("/* <div data-page='未授权页面' /> */\nconst x = '<div data-page=\\\"未授权页面\\\" />';", encoding="utf-8")
        data = payload(run(CHECK, "--project-root", str(root)))
        check(not any(item.get("name") == "未授权页面" for item in data["classification"]["deterministic_conflicts"]), str(data))


def test_fatal_inputs_and_module_argument() -> None:
    with tempfile.TemporaryDirectory(prefix="spm-prototype-consistency-") as name:
        root = Path(name)
        result = run(CHECK, "--project-root", str(root))
        check(result.returncode == 2, result.stdout + result.stderr)
        data = payload(result)
        check(data["exit_reason"] == "fatal_input_error", result.stdout)
        result = run(CHECK, "--project-root", str(root), "--module", "测试")
        check(result.returncode == 2, result.stdout + result.stderr)
        check("unrecognized arguments: --module" in result.stderr, result.stderr)


def main() -> int:
    tests = [
        test_valid_and_stable_output,
        test_unknown_route_is_deterministic_conflict,
        test_unknown_explicit_anchors_are_deterministic_conflicts,
        test_missing_route_and_anchors_are_not_blocking,
        test_placeholder_route_and_unanchored_button_are_review_items,
        test_route_title_variation_is_not_a_deterministic_conflict,
        test_element_route_without_title_is_not_a_deterministic_conflict,
        test_js_string_html_is_not_an_explicit_anchor,
        test_self_closing_button_is_a_semantic_review_item,
        test_compact_route_array_does_not_hide_later_routes,
        test_excluded_directories_and_hidden_content_are_ignored,
        test_fatal_inputs_and_module_argument,
    ]
    failures: list[str] = []
    for test in tests:
        try:
            test()
        except Exception as exc:
            failures.append(f"{test.__name__}: {exc}")
    if failures:
        print(f"Prototype 一致性检查回归测试失败：{len(failures)}/{len(tests)}")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Prototype 一致性检查回归测试通过：{len(tests)} 个用例")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
