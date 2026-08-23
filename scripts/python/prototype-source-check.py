#!/usr/bin/env python3
"""Prototype 源码工程确定性检查。

检查 output/prototype 是否为标准 Vite 源码工程：
src 是唯一编辑源、dist 是可重建产物、原型工具.bat 是用户唯一操作入口。

行为：通过返回 0，失败返回 1；人读输出；不自动修复；不判断产品语义；不生成回执文件。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _check(problems: list[str], ok: bool, message: str) -> None:
    print(("PASS" if ok else "FAIL") + " | " + message)
    if not ok:
        problems.append(message)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prototype 源码工程确定性检查")
    parser.add_argument("--project-root", required=True, help="项目根目录（检查 output/prototype）")
    parser.add_argument("--prototype-root", type=Path, default=None, help="覆盖原型目录（默认 <project-root>/output/prototype）")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    proto = (args.prototype_root or (root / "output" / "prototype")).resolve()
    problems: list[str] = []

    print(f"检查原型目录：{proto}")

    # 1. index.html 存在
    index_html = proto / "index.html"
    _check(problems, index_html.is_file(), "index.html 存在")

    # 2. package.json + 锁文件 + Vite 配置 + src 存在
    package_json = proto / "package.json"
    _check(problems, package_json.is_file(), "package.json 存在")
    _check(problems, (proto / "package-lock.json").is_file(), "package-lock.json 存在")
    _check(
        problems,
        any((proto / name).is_file() for name in ("vite.config.js", "vite.config.mjs", "vite.config.cjs")),
        "Vite 配置存在（vite.config.js/mjs/cjs）",
    )
    _check(problems, (proto / "src").is_dir(), "src/ 目录存在")

    # 3. package scripts 包含 dev/build/preview
    scripts_ok = False
    if package_json.is_file():
        try:
            data = json.loads(_read_text(package_json))
            scripts = data.get("scripts", {})
            missing = [name for name in ("dev", "build", "preview") if not scripts.get(name)]
            scripts_ok = not missing
            if not scripts_ok:
                _check(problems, False, f"package scripts 缺少: {', '.join(missing)}")
        except (json.JSONDecodeError, OSError) as exc:
            _check(problems, False, f"package.json 无法解析: {exc}")
    if scripts_ok:
        _check(problems, True, "package scripts 包含 dev/build/preview")

    # 4. 入口与路由注册表存在
    src = proto / "src"
    _check(problems, (src / "main.jsx").is_file(), "src/main.jsx 存在")
    route_entry = any((src / name).is_file() for name in ("routes.jsx", "routes/index.jsx", "routes/index.js"))
    _check(problems, route_entry, "路由注册表存在（src/routes.jsx 或 src/routes/index.*）")

    # 5. src 不 import dist
    dist_imports: list[str] = []
    if src.is_dir():
        for path in sorted(src.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".mjs"}:
                text = _read_text(path)
                for match in re.finditer(r"""(?:from\s*|import\s*\(\s*|require\s*\(\s*)[`'"]([^`'"]+)[`'"]""", text):
                    target = match.group(1)
                    if re.search(r"(?:^|/)dist/", target):
                        dist_imports.append(f"{path.relative_to(proto).as_posix()} -> {target}")
    _check(problems, not dist_imports, "src 不引用 dist" + (f"：{'；'.join(dist_imports[:5])}" if dist_imports else ""))

    # 6. 不存在项目级 module-*.compiled.js 补丁链
    compiled = sorted(proto.rglob("module-*.compiled.js")) if proto.is_dir() else []
    compiled = [p for p in compiled if "node_modules" not in p.parts and "dist" not in p.parts]
    _check(problems, not compiled, "不存在 module-*.compiled.js 补丁链" + (f"：{compiled[0].relative_to(proto)}" if compiled else ""))

    # 7. 活动源码不依赖 prototype-p0 等兄弟目录
    p0_refs: list[str] = []
    if src.is_dir():
        for path in sorted(src.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".js", ".jsx", ".mjs"}:
                text = _read_text(path)
                for match in re.finditer(r"""(?:from\s*|import\s*\(\s*|require\s*\(\s*)[`'"]([^`'"]+)[`'"]""", text):
                    if "prototype-p0" in match.group(1):
                        p0_refs.append(f"{path.relative_to(proto).as_posix()} -> {match.group(1)}")
    _check(problems, not p0_refs, "src 不依赖 prototype-p0 等兄弟目录" + (f"：{'；'.join(p0_refs[:5])}" if p0_refs else ""))

    # 8. node_modules 不在 dist
    _check(problems, not (proto / "dist" / "node_modules").exists(), "node_modules 不在 dist")

    # 9. 原型工具.bat 存在并调用 package scripts（dev/build/preview）
    bat = proto / "原型工具.bat"
    bat_text = _read_text(bat) if bat.is_file() else ""
    _check(problems, bat.is_file(), "原型工具.bat 存在")
    if bat.is_file():
        missing_calls = [name for name in ("npm run dev", "npm run build", "npm run preview") if name not in bat_text]
        _check(problems, not missing_calls, "原型工具.bat 调用 dev/build/preview" + (f"，缺少: {', '.join(missing_calls)}" if missing_calls else ""))

    # 10. README 首屏将 BAT 作为用户唯一操作入口
    readme = proto / "README.md"
    readme_ok = False
    if readme.is_file():
        lines = _read_text(readme).splitlines()
        first_screen: list[str] = []
        heading_count = 0
        for line in lines:
            if line.startswith("##"):
                heading_count += 1
                if heading_count >= 2:
                    break
            first_screen.append(line)
        screen = "\n".join(first_screen)
        readme_ok = (
            "原型工具.bat" in screen
            and "双击" in screen
            and "npm run" not in screen
            and "打开 PowerShell" not in screen
            and "在 PowerShell 中执行" not in screen
        )
    _check(problems, readme_ok, "README 首屏以双击 原型工具.bat 为唯一用户操作入口（不含 npm/PowerShell 命令步骤）")

    print()
    if problems:
        print(f"结果：失败（{len(problems)} 项）")
        return 1
    print("结果：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
