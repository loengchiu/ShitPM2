#!/usr/bin/env python3
"""
prototype-shared-guard.py - 最小生成侧共享基础设施与规范守护脚本

准入范围（低误报、确定性判断）：
  G1: 页面层（src/modules/）直接 import @ant-design/icons 或第三方图标库
  G2: 页面层引入外部 CSS 文件
  G3: 页面层出现明确的版权文案重复实现
  G4: 页面层使用已废弃的主题变量（如 --spm-*）或旧主题入口
  G5: 模板工程与审计/目标工程 shared/ui/ 子集内同名文件内容不一致（仅比较 shared/ui/，不比 icons，不比特有文件）

返回值：
  0: 无命中，检查通过
  1: 命中规则违规
  2: 参数或工程路径错误
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Prototype 共享层与基础规范守护脚本")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--prototype-root", default=None, help="待检测的原型工程路径")
    parser.add_argument("--template-root", default=None, help="模板工程路径（用于 G5 比对）")
    return parser.parse_args()


def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def run_checks(proto_root: Path, tpl_root: Path | None) -> list[dict]:
    violations = []
    modules_dir = proto_root / "src" / "modules"

    jsx_files = sorted(list(modules_dir.glob("**/*.jsx"))) if modules_dir.exists() else []

    for fpath in jsx_files:
        rel = fpath.relative_to(proto_root).as_posix()
        try:
            content = fpath.read_text(encoding="utf-8")
        except Exception:
            continue

        lines = content.splitlines()

        # G1: 页面层直接 import 图标库
        # 允许从 shared/icons 引入，禁止从 @ant-design/icons 或 @tabler/icons 引入
        for idx, line in enumerate(lines, 1):
            if re.search(r"import\s+.*from\s+['\"]@ant-design/icons['\"]", line) or \
               re.search(r"import\s+.*from\s+['\"]@tabler/icons", line):
                violations.append({
                    "rule": "G1",
                    "file": rel,
                    "line": idx,
                    "desc": "页面层直接 import 图标库，应统一从 shared/icons 取用",
                    "code": line.strip()
                })

        # G2: 页面层引入外部 CSS
        for idx, line in enumerate(lines, 1):
            if re.search(r"import\s+['\"][^'\"]+\.css['\"]", line):
                violations.append({
                    "rule": "G2",
                    "file": rel,
                    "line": idx,
                    "desc": "页面层直接引入 CSS 文件，应使用共享主题与全局样式",
                    "code": line.strip()
                })

        # G3: 页面层出现明确的版权文案重复实现
        copyright_pattern = r"(?:研发单位：广西计算中心|<PageFooter)"
        matches = list(re.finditer(copyright_pattern, content))
        if len(matches) > 1:
            # 取第二个出现的位置
            line_no = content[:matches[1].start()].count("\n") + 1
            violations.append({
                "rule": "G3",
                "file": rel,
                "line": line_no,
                "desc": f"页面层存在重复的版权行实现（共发现 {len(matches)} 处）",
                "code": matches[1].group(0)
            })

        # G4: 页面层使用已废弃的主题变量
        for idx, line in enumerate(lines, 1):
            m = re.search(r"--spm-[a-zA-Z0-9_-]+", line)
            if m:
                violations.append({
                    "rule": "G4",
                    "file": rel,
                    "line": idx,
                    "desc": f"页面层使用了已废弃的主题变量 '{m.group(0)}'",
                    "code": line.strip()
                })

    # G5: 模板工程与目标工程 shared/ui/ 子集同名文件内容比对
    if tpl_root and tpl_root.exists() and (tpl_root / "src/shared/ui").exists() and (proto_root / "src/shared/ui").exists():
        tpl_ui = tpl_root / "src/shared/ui"
        proto_ui = proto_root / "src/shared/ui"

        # 仅比较 template shared/ui/ 包含的同名文件
        for tpl_file in sorted(tpl_ui.glob("*.jsx")):
            target_file = proto_ui / tpl_file.name
            if target_file.exists():
                if get_sha256(tpl_file) != get_sha256(target_file):
                    violations.append({
                        "rule": "G5",
                        "file": f"src/shared/ui/{tpl_file.name}",
                        "line": 1,
                        "desc": f"shared/ui/{tpl_file.name} 与模板权威源内容不一致",
                        "code": f"SHA256 mismatch vs template"
                    })

    return violations


def main():
    args = parse_args()
    proj_root = Path(args.project_root).resolve()

    if args.prototype_root:
        proto_root = Path(args.prototype_root).resolve()
    else:
        # 探测 output/prototype 或 templates/prototype-vite
        cand1 = proj_root / "output" / "prototype"
        cand2 = proj_root / "templates" / "prototype-vite"
        if cand1.exists() and (cand1 / "src").exists():
            proto_root = cand1
        elif cand2.exists() and (cand2 / "src").exists():
            proto_root = cand2
        else:
            print("错误: 未找到有效的原型工程路径，请通过 --prototype-root 指定", file=sys.stderr)
            sys.exit(2)

    if args.template_root:
        tpl_root = Path(args.template_root).resolve()
    else:
        cand_tpl = proj_root / "templates" / "prototype-vite"
        tpl_root = cand_tpl if cand_tpl.exists() else None

    # 如果检测的目标正是模板本身，不需要执行 G5 自身比对
    if tpl_root and proto_root == tpl_root:
        tpl_root = None

    violations = run_checks(proto_root, tpl_root)

    if violations:
        print(f"[FAIL] prototype-shared-guard 发现 {len(violations)} 项违规:")
        for v in violations:
            print(f"  [{v['rule']}] {v['file']}:{v['line']} - {v['desc']}")
            if v.get("code"):
                print(f"        代码: {v['code']}")
        sys.exit(1)
    else:
        print(f"[PASS] prototype-shared-guard 检查通过 ({proto_root})")
        sys.exit(0)


if __name__ == "__main__":
    main()
