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
DESIGN_INDEX = ROOT / "scripts/python/design-index.py"
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
    shutil.copytree(TEMPLATE, target, ignore=shutil.ignore_patterns("node_modules", "dist"))
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

### 页面：测试列表页
目的：查看测试列表
角色：测试人员
进入条件：已登录
数据范围：测试数据
主要状态：可用、已停用

#### 区块：筛选条件
目的：按名称筛选

##### 字段：测试名称
业务含义：测试名称
来源：测试服务
展示条件：始终展示
输入编辑：可输入
取值默认：默认空值
交互：文本输入
校验反馈：无

##### 字段：测试字段二
业务含义：空串后字段
来源：测试服务
展示条件：始终展示
输入编辑：只读
取值默认：默认空值
交互：文本展示
校验反馈：无

##### 操作：查询
适用角色：测试人员
可用条件：输入条件合法
确认：无需确认
成功结果：刷新测试列表
状态变化：无
失败恢复：保留当前筛选条件并提示
去向：仍停留在测试列表页

### 页面：测试详情页
目的：查看测试详情
角色：测试人员
进入条件：已登录
数据范围：测试数据
主要状态：可用、已停用

#### 区块：详情信息
目的：展示详情

##### 字段：详情名称
业务含义：测试详情名称
来源：测试服务
展示条件：始终展示
输入编辑：只读
取值默认：默认空值
交互：文本展示
校验反馈：无
"""
    import hashlib
    design_dir = root / "output" / "design"
    (design_dir / "模块设计" / "测试").mkdir(parents=True, exist_ok=True)
    module_path = design_dir / "模块设计" / "测试" / "测试系统.md"
    module_path.write_text(design, encoding="utf-8")
    map_path = design_dir / "设计地图.md"
    map_path.write_text("# 设计地图\n\n## 模块与职责\n\n- MOD-001 [测试](模块设计/测试/测试系统.md)：测试系统。\n", encoding="utf-8")
    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "shitpm-design-set/v1",
        "set_sha256": "",
        "files": [
            {"id": "MAP-001", "path": "设计地图.md", "type": "map", "module": None, "business_chains": [], "depends_on": [], "sha256": sha(map_path)},
            {"id": "MOD-001", "path": "模块设计/测试/测试系统.md", "type": "module", "module": "测试", "business_chains": ["测试业务链"], "depends_on": [], "sha256": sha(module_path)},
        ],
        "decisions": [],
    }
    parts = []
    for f in sorted(manifest["files"], key=lambda x: x["id"]):
        parts.append(f["id"] + f["path"] + f["sha256"])
    manifest["set_sha256"] = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
    (design_dir / "设计集清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    dist = proto / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html><body>仅存在于dist的页面</body></html>", encoding="utf-8")
    node_modules = proto / "node_modules"
    node_modules.mkdir()
    (node_modules / "evil.js").write_text("仅存在于node_modules的页面", encoding="utf-8")
    (proto / "src" / "routes.jsx").write_text(
        "export const routes = [\n  { path: '/test-detail', title: '测试详情页', component: Detail },\n  { path: '*', title: 'NotFound', component: NotFound },\n];\n",
        encoding="utf-8",
    )


def test_consistency_reads_jsx_and_excludes_dist() -> None:
    holder, root = make_project()
    try:
        _write_business_fixture(root)
        index_result = run(DESIGN_INDEX, "compile", "--project-root", str(root))
        check(index_result.returncode == 0, index_result.stdout + index_result.stderr)
        result = run(CONSISTENCY, "--project-root", str(root))
        check(result.returncode == 0, "可能遗漏和语义项不应阻断：" + result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        possible = payload["classification"]["possible_omissions"]
        check(any(item.get("name") == "测试列表页" for item in possible), f"源码缺失页面未进入可能遗漏: {result.stdout}")
        scanned = set(payload["source"]["scanned_files"])
        check(not any("dist" in item or "node_modules" in item for item in scanned), f"排除目录被扫描: {result.stdout}")
        check(not any(item.get("name") in {"仅存在于dist的页面", "仅存在于node_modules的页面"} for item in possible), f"排除目录内容被当作事实: {result.stdout}")
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
