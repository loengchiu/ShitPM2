#!/usr/bin/env python3
"""
test-prototype-shared-guard.py - prototype-shared-guard.py 回归测试套件
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_guard(proto_dir: Path, tpl_dir: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(Path("scripts/python/prototype-shared-guard.py").resolve()),
        "--prototype-root",
        str(proto_dir),
    ]
    if tpl_dir:
        cmd.extend(["--template-root", str(tpl_dir)])
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def test_clean_project_passes():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src" / "modules").mkdir(parents=True)
        page = root / "src" / "modules" / "TestPage.jsx"
        page.write_text("""
import React from 'react';
import { PageHeader, DataTable, PageFooter } from '../../shared/ui/index.jsx';
import { IconSearch } from '../../shared/icons';

export default function TestPage() {
  return (
    <div>
      <PageHeader title="测试" />
      <DataTable columns={[]} dataSource={[]} />
      <PageFooter />
    </div>
  );
}
""", encoding="utf-8")

        res = run_guard(root)
        assert res.returncode == 0, f"Expected 0, got {res.returncode}: {res.stdout}\n{res.stderr}"
        assert "[PASS]" in res.stdout
    print("test_clean_project_passes: PASS")


def test_g1_direct_icon_import():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src" / "modules").mkdir(parents=True)
        page = root / "src" / "modules" / "BadIcon.jsx"
        page.write_text("""
import { SearchOutlined } from '@ant-design/icons';
export default function BadIcon() { return <SearchOutlined />; }
""", encoding="utf-8")

        res = run_guard(root)
        assert res.returncode == 1, f"Expected 1, got {res.returncode}"
        assert "[G1]" in res.stdout
    print("test_g1_direct_icon_import: PASS")


def test_g2_external_css():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src" / "modules").mkdir(parents=True)
        page = root / "src" / "modules" / "BadCss.jsx"
        page.write_text("""
import './style.css';
export default function BadCss() { return <div />; }
""", encoding="utf-8")

        res = run_guard(root)
        assert res.returncode == 1, f"Expected 1, got {res.returncode}"
        assert "[G2]" in res.stdout
    print("test_g2_external_css: PASS")


def test_g3_duplicate_copyright():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src" / "modules").mkdir(parents=True)
        page = root / "src" / "modules" / "BadFooter.jsx"
        page.write_text("""
import { PageFooter } from '../../shared/ui/index.jsx';
export default function BadFooter() {
  return (
    <div>
      <PageFooter />
      <div>研发单位：广西计算中心</div>
    </div>
  );
}
""", encoding="utf-8")

        res = run_guard(root)
        assert res.returncode == 1, f"Expected 1, got {res.returncode}"
        assert "[G3]" in res.stdout
    print("test_g3_duplicate_copyright: PASS")


def test_g4_deprecated_tokens():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "src" / "modules").mkdir(parents=True)
        page = root / "src" / "modules" / "BadToken.jsx"
        page.write_text("""
export default function BadToken() {
  return <div style={{ color: 'var(--spm-color-primary)' }} />;
}
""", encoding="utf-8")

        res = run_guard(root)
        assert res.returncode == 1, f"Expected 1, got {res.returncode}"
        assert "[G4]" in res.stdout
    print("test_g4_deprecated_tokens: PASS")


def test_g5_shared_ui_drift():
    with tempfile.TemporaryDirectory() as tmp_tpl, tempfile.TemporaryDirectory() as tmp_proto:
        tpl = Path(tmp_tpl)
        proto = Path(tmp_proto)

        (tpl / "src" / "shared" / "ui").mkdir(parents=True)
        (proto / "src" / "shared" / "ui").mkdir(parents=True)

        (tpl / "src" / "shared" / "ui" / "index.jsx").write_text("export const A = 1;", encoding="utf-8")
        (proto / "src" / "shared" / "ui" / "index.jsx").write_text("export const A = 2;", encoding="utf-8")

        res = run_guard(proto, tpl)
        assert res.returncode == 1, f"Expected 1, got {res.returncode}"
        assert "[G5]" in res.stdout
    print("test_g5_shared_ui_drift: PASS")


def test_invalid_path():
    res = subprocess.run([
        sys.executable,
        str(Path("scripts/python/prototype-shared-guard.py").resolve()),
        "--prototype-root",
        "non_existent_dir_12345",
    ], capture_output=True, text=True)
    assert res.returncode == 2 or res.returncode == 0
    print("test_invalid_path: PASS")


def main():
    test_clean_project_passes()
    test_g1_direct_icon_import()
    test_g2_external_css()
    test_g3_duplicate_copyright()
    test_g4_deprecated_tokens()
    test_g5_shared_ui_drift()
    test_invalid_path()
    print("\nALL 7 prototype-shared-guard TESTS PASSED!")


if __name__ == "__main__":
    main()
