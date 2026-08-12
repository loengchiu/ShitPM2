from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable
TEMPLATE = ROOT / "templates" / "prototype-vite"
SOURCE_CHECK = ROOT / "scripts/python/prototype-source-check.py"
CONSISTENCY = ROOT / "scripts/python/prototype-consistency-check.py"
STRUCTURE = ROOT / "scripts/python/prototype-structure.py"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def make_project() -> tuple[tempfile.TemporaryDirectory, Path]:
    holder = tempfile.TemporaryDirectory(prefix="spm-prototype-src-")
    root = Path(holder.name)
    target = root / "output" / "prototype"
    shutil.copytree(TEMPLATE, target)
    return holder, root


def test_valid_project_passes() -> None:
    holder, root = make_project()
    try:
        result = run(SOURCE_CHECK, "--project-root", str(root))
        check(result.returncode == 0, result.stdout + result.stderr)
        check("结果：通过" in result.stdout, result.stdout)
    finally:
        holder.cleanup()


def test_missing_src_fails() -> None:
    holder, root = make_project()
    try:
        shutil.rmtree(root / "output" / "prototype" / "src")
        result = run(SOURCE_CHECK, "--project-root", str(root))
        check(result.returncode == 1, result.stdout + result.stderr)
        check("src/ 目录存在" in result.stdout and "FAIL" in result.stdout, result.stdout)
    finally:
        holder.cleanup()


def test_missing_build_script_fails() -> None:
    holder, root = make_project()
    try:
        package = root / "output" / "prototype" / "package.json"
        data = json.loads(package.read_text(encoding="utf-8"))
        del data["scripts"]["build"]
        package.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        result = run(SOURCE_CHECK, "--project-root", str(root))
        check(result.returncode == 1, result.stdout + result.stderr)
        check("build" in result.stdout and "FAIL" in result.stdout, result.stdout)
    finally:
        holder.cleanup()


def test_src_imports_dist_fails() -> None:
    holder, root = make_project()
    try:
        src = root / "output" / "prototype" / "src"
        (src / "bad.js").write_text("import x from '../dist/assets/x.js';\n", encoding="utf-8")
        result = run(SOURCE_CHECK, "--project-root", str(root))
        check(result.returncode == 1, result.stdout + result.stderr)
        check("src 不引用 dist" in result.stdout and "FAIL" in result.stdout, result.stdout)
    finally:
        holder.cleanup()


def test_compiled_only_fails() -> None:
    holder = tempfile.TemporaryDirectory(prefix="spm-prototype-compiled-")
    try:
        root = Path(holder.name)
        proto = root / "output" / "prototype"
        proto.mkdir(parents=True)
        (proto / "index.html").write_text("<html><body>旧静态原型</body></html>", encoding="utf-8")
        (proto / "module-home.compiled.js").write_text("const a = 1;", encoding="utf-8")
        result = run(SOURCE_CHECK, "--project-root", str(root))
        check(result.returncode == 1, result.stdout + result.stderr)
        check("package.json 存在" in result.stdout and "module-*.compiled.js" in result.stdout, result.stdout)
    finally:
        holder.cleanup()


def test_template_has_single_menu_bat() -> None:
    bats = list(TEMPLATE.glob("原型工具.bat"))
    check(len(bats) == 1, "模板必须只有一个面向用户的菜单 BAT")
    text = bats[0].read_text(encoding="utf-8")
    for label in ("启动本地即时预览", "构建并预览发布版本", "重新构建部署包", "上传到 Cloudflare", "修复依赖并重新构建", "0. 退出"):
        check(label in text, f"BAT 菜单缺少: {label}")
    for call in ("npm run dev", "npm run build", "npm run preview"):
        check(call in text, f"BAT 未调用 {call}")
    check("wrangler.toml" in text, "BAT 缺少 Cloudflare 配置检查")
    check("audit-system" not in text, "模板 BAT 不得硬编码项目名")
    readme = TEMPLATE / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines()
    screen_lines = []
    heading_count = 0
    for line in lines:
        if line.startswith("##"):
            heading_count += 1
            if heading_count >= 2:
                break
        screen_lines.append(line)
    screen = "\n".join(screen_lines)
    check("原型工具.bat" in screen and "双击" in screen, "README 首屏未把 BAT 作为唯一用户入口")


def _write_business_fixture(root: Path) -> None:
    proto = root / "output" / "prototype"
    (proto / "src" / "modules" / "home" / "Home.jsx").write_text(
        """import { Card, Form, Input, Table } from 'antd';

const c4 = '', c5 = '';

export default function Home() {
  const columns = [{ title: '测试名称', dataIndex: 'name' }];
  return (
    <Card>
      <div>测试字段二</div>
      <Form layout="inline">
        <Form.Item label="查询名称"><Input placeholder="请输入测试名称" /></Form.Item>
      </Form>
      <Table columns={columns} dataSource={[]} pagination={false} />
      <a href="#/test-detail">测试详情页</a>
    </Card>
  );
}
""",
        encoding="utf-8",
    )
    design = """# 测试系统 Design

## 页面清单

| 页面名称 | 页面说明 |
| --- | --- |
| 测试列表页 | 列表 |
| 测试详情页 | 详情 |
| 仅存在于dist的页面 | 不应被扫描 |
| 仅存在于node_modules的页面 | 不应被扫描 |

## 字段定义

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| 测试名称 | 文本 | 名称 |
| 测试字段二 | 文本 | 空串后字段 |
"""
    (root / "output" / "design" / "design.md").parent.mkdir(parents=True)
    (root / "output" / "design" / "design.md").write_text(design, encoding="utf-8")
    dist = proto / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html><body>仅存在于dist的页面</body></html>", encoding="utf-8")
    node_modules = proto / "node_modules"
    node_modules.mkdir()
    (node_modules / "evil.js").write_text("仅存在于node_modules的页面", encoding="utf-8")


def test_consistency_reads_jsx_and_excludes_dist() -> None:
    holder, root = make_project()
    try:
        _write_business_fixture(root)
        result = run(CONSISTENCY, "--project-root", str(root))
        check(result.returncode == 1, "仅 dist/node_modules 存在的页面应缺失：" + result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        matched_pages = set(payload["pages"]["expected"]) - set(payload["pages"]["missing"])
        check("测试详情页" in matched_pages, f"一致性检查未从 JSX 识别页面: {result.stdout}")
        check("测试列表页" in set(payload["pages"]["missing"]), f"源码缺失页面未报告: {result.stdout}")
        missing = set(payload["pages"]["missing"])
        check("仅存在于dist的页面" in missing, f"dist 被误扫: {result.stdout}")
        check("仅存在于node_modules的页面" in missing, f"node_modules 被误扫: {result.stdout}")
        check("测试名称" not in payload["fields"]["missing"], f"字段未从 JSX 识别: {result.stdout}")
        check("测试字段二" not in payload["fields"]["missing"], f"空字符串后的字段未识别（引号配对漂移）: {result.stdout}")
    finally:
        holder.cleanup()


def test_structure_extracts_routes_from_jsx() -> None:
    holder, root = make_project()
    try:
        _write_business_fixture(root)
        result = run(STRUCTURE, "--project-root", str(root), "--input", str(root / "output" / "prototype"))
        check(result.returncode == 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        check("/" in payload["routes"] and "*" in payload["routes"], f"路由未从 JSX 提取: {payload['routes']}")
        check(payload["fields"], f"字段线索为空: {payload['fields']}")
        check(payload["actions"], f"操作线索为空: {payload['actions']}")
        check(payload["source_hash"], "缺少确定性 source_hash")
    finally:
        holder.cleanup()


def main() -> int:
    tests = [
        test_valid_project_passes,
        test_missing_src_fails,
        test_missing_build_script_fails,
        test_src_imports_dist_fails,
        test_compiled_only_fails,
        test_template_has_single_menu_bat,
        test_consistency_reads_jsx_and_excludes_dist,
        test_structure_extracts_routes_from_jsx,
    ]
    failures = []
    for test in tests:
        try:
            test()
        except Exception as exc:
            failures.append(f"{test.__name__}: {exc}")
    if failures:
        print(f"Prototype 源码工程回归测试失败：{len(failures)}/{len(tests)}")
        for item in failures:
            print(f"- {item}")
        return 1
    print(f"Prototype 源码工程回归测试通过：{len(tests)} 个用例")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
