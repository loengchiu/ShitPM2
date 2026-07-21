"""
下载 spm-prototype 所需的本地 CSS/JS 资源到项目根 lib/ 目录。
资源：Vue 3、Tailwind Play CDN、daisyUI 5（CSS only，无 JS 依赖）

daisyUI 5 是 CSS-only 库（无 JS），所有交互通过纯 CSS + tabindex 或 Vue 状态管理实现。
"""
import argparse
import urllib.request
import sys
from pathlib import Path

# 项目根 = scripts/python/ 的上两级
LIB_DIR = Path(__file__).resolve().parents[2] / "lib"

RESOURCES = [
    # (filename, url, expected_min_bytes)
    ("vue.global.prod.js",
     "https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js", 50000),
    ("tailwind.js",
     "https://cdn.tailwindcss.com/3.4.16", 200000),
    # daisyUI 5 完整 CSS（含全部组件类），~946KB
    ("daisyui.css",
     "https://cdn.jsdelivr.net/npm/daisyui@5.5.23/daisyui.css", 800000),
    # daisyUI 主题 CSS，~37KB
    ("daisyui-themes.css",
     "https://cdn.jsdelivr.net/npm/daisyui@5.5.23/themes.css", 20000),
]


def download(filename: str, url: str, expected_min_bytes: int = 0) -> int:
    target = LIB_DIR / filename
    print(f"[下载] {url} -> {target}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    actual_size = len(data)
    target.write_bytes(data)
    if expected_min_bytes and actual_size < expected_min_bytes:
        print(f"  WARN: {actual_size} bytes < expected {expected_min_bytes}, 可能下载不完整", file=sys.stderr)
    print(f"  OK: {actual_size} bytes")
    return actual_size


def main() -> int:
    parser = argparse.ArgumentParser(
        description="下载 spm-prototype 所需本地 CSS/JS 资源到 lib/（Vue 3 / Tailwind / daisyUI 5）",
    )
    parser.parse_args()  # 提供 -h/--help；拒绝未知参数。裸调用（无参数）仍执行下载。
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, url, expected_min in RESOURCES:
        try:
            total += download(name, url, expected_min)
        except Exception as e:
            print(f"  FAIL: {e}", file=sys.stderr)
            return 1
    # 校验
    print("\n[校验] lib/ 目录内容:")
    for f in LIB_DIR.iterdir():
        print(f"  {f.name}: {f.stat().st_size} bytes")
    print(f"\n总计下载: {total} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
