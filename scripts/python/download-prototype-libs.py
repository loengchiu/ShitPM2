"""
下载 spm-prototype 所需的本地 CSS/JS 资源到项目根 lib/react-antd/ 目录。
资源：React 18 UMD、ReactDOM 18 UMD、Ant Design 6.5.4 UMD（含中文 locale）、
      antd.css（v6 纯 CSS 变量主题）、reset.css、dayjs（含 zh-cn locale）、babel-standalone。

架构固定为 React 18 + Ant Design 6（无构建、离线双击即用）：
- React 19 官方移除了 UMD 构建，无构建方案只能用 React 18（antd 6 peer 为 react>=18）。
- antd 6 改回纯 CSS（CSS 变量主题），需显式加载 antd.css，不再像 v5 那样 CSS-in-JS 注入。
"""
import argparse
import urllib.request
import sys
from pathlib import Path

# 项目根 = scripts/python/ 的上两级
LIB_DIR = Path(__file__).resolve().parents[2] / "lib" / "react-antd"

RESOURCES = [
    # (filename, url, expected_min_bytes)
    ("react.production.min.js",
     "https://unpkg.com/react@18.3.1/umd/react.production.min.js", 9000),
    ("react-dom.production.min.js",
     "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js", 120000),
    ("dayjs.min.js",
     "https://unpkg.com/dayjs@1.11.21/dayjs.min.js", 6000),
    ("locale-zh-cn.js",
     "https://unpkg.com/dayjs@1.11.21/locale/zh-cn.js", 1200),
    ("antd-with-locales.min.js",
     "https://unpkg.com/antd@6.5.4/dist/antd-with-locales.min.js", 1500000),
    ("antd.css",
     "https://unpkg.com/antd@6.5.4/dist/antd.css", 800000),
    ("reset.css",
     "https://unpkg.com/antd@6.5.4/dist/reset.css", 3000),
    ("echarts.min.js",
     "https://unpkg.com/echarts@5/dist/echarts.min.js", 900000),
    ("babel.min.js",
     "https://unpkg.com/@babel/standalone@7/babel.min.js", 2000000),
]


def download(filename: str, url: str, expected_min_bytes: int = 0) -> int:
    target = LIB_DIR / filename
    print(f"[下载] {url} -> {target}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = resp.read()
    actual_size = len(data)
    target.write_bytes(data)
    if expected_min_bytes and actual_size < expected_min_bytes:
        print(f"  WARN: {actual_size} bytes < expected {expected_min_bytes}, 可能下载不完整", file=sys.stderr)
    print(f"  OK: {actual_size} bytes")
    return actual_size


def main() -> int:
    parser = argparse.ArgumentParser(
        description="下载 spm-prototype 所需本地 CSS/JS 资源到 lib/react-antd/（React 18 / Ant Design 6.5.4 / babel / dayjs）",
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
    print("\n[校验] lib/react-antd/ 目录内容:")
    for f in sorted(LIB_DIR.iterdir()):
        print(f"  {f.name}: {f.stat().st_size} bytes")
    print(f"\n总计下载: {total} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
