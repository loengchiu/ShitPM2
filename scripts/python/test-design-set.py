#!/usr/bin/env python3
"""design-set.py 的直接测试：清单校验、闭包、单文件/多文件事务、中断恢复、下游依据。"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("design-set.py")
FIXTURES = ROOT / "test-fixture" / "design-set"


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def parse(stdout: str) -> dict:
    return json.loads(stdout)


def copy_fixture(name: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"spm-{name}-"))
    shutil.copytree(FIXTURES / name, tmp, dirs_exist_ok=True)
    return tmp


class ManifestCheckTests(unittest.TestCase):
    def test_valid_manifest_passes(self):
        tmp = copy_fixture("valid")
        try:
            proc = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue(parse(proc.stdout)["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_duplicate_id_fails_with_location(self):
        tmp = copy_fixture("invalid-duplicate-id")
        try:
            proc = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(proc.returncode, 2)
            errors = parse(proc.stdout)["errors"]
            self.assertTrue(any("重复文件 ID" in e for e in errors))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_invalid_paths_rejected(self):
        tmp = copy_fixture("invalid-path")
        try:
            proc = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(proc.returncode, 2)
            errors = parse(proc.stdout)["errors"]
            self.assertTrue(any("绝对路径" in e for e in errors))
            self.assertTrue(any(".." in e for e in errors))
            self.assertTrue(any("文件不存在" in e for e in errors))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_dependency_cycle_rejected(self):
        tmp = copy_fixture("invalid-dependency")
        try:
            proc = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(proc.returncode, 2)
            errors = parse(proc.stdout)["errors"]
            self.assertTrue(any("依赖环" in e for e in errors))
            self.assertTrue(any("引用不存在的 ID" in e for e in errors))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_fingerprint_mismatch_only_reports_target(self):
        tmp = copy_fixture("invalid-fingerprint")
        try:
            proc = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(proc.returncode, 2)
            errors = parse(proc.stdout)["errors"]
            mismatch = [e for e in errors if e.startswith("文件指纹不一致")]
            self.assertEqual(len(mismatch), 1)
            self.assertIn("MOD-001", mismatch[0])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_set_sha256_deterministic(self):
        tmp = copy_fixture("valid")
        try:
            first = parse(run_cli(tmp, "check", "--project-root", str(tmp)).stdout)
            second = parse(run_cli(tmp, "check", "--project-root", str(tmp)).stdout)
            self.assertEqual(first["set_sha256"], second["set_sha256"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ClosureTests(unittest.TestCase):
    def test_closure_respects_dependency_order(self):
        tmp = copy_fixture("valid")
        try:
            proc = run_cli(tmp, "closure", "--project-root", str(tmp), "--targets", "MOD-001")
            self.assertEqual(proc.returncode, 0, proc.stdout)
            data = parse(proc.stdout)
            self.assertEqual(data["closure_ids"], ["SYS-001", "CON-001", "MOD-001"])
            self.assertTrue(all(f["exists"] for f in data["files"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_closure_unknown_target_fails(self):
        tmp = copy_fixture("valid")
        try:
            proc = run_cli(tmp, "closure", "--project-root", str(tmp), "--targets", "MOD-999")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("MOD-999", parse(proc.stdout)["missing"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class SingleFileTransactionTests(unittest.TestCase):
    def test_single_success_updates_manifest_only(self):
        tmp = copy_fixture("valid")
        try:
            stage = run_cli(tmp, "stage-single", "--project-root", str(tmp), "--id", "MOD-001")
            self.assertEqual(stage.returncode, 0, stage.stdout)
            staged_path = Path(parse(stage.stdout)["staged_path"])
            new_content = "# 模块设计：订单管理 v2\n\n更新。\n"
            staged_path.write_text(new_content, encoding="utf-8", newline="\n")
            expected = hashlib.sha256(staged_path.read_bytes()).hexdigest()
            commit = run_cli(tmp, "commit-single", "--project-root", str(tmp))
            self.assertEqual(commit.returncode, 0, commit.stdout)
            manifest = parse((tmp / "output" / "design" / "设计集清单.json").read_text(encoding="utf-8"))
            mod = next(f for f in manifest["files"] if f["id"] == "MOD-001")
            self.assertEqual(mod["sha256"], expected)
            self.assertFalse((tmp / ".workflow" / "runtime" / "design-change" / "single").exists())
            # 无关文件保持原样
            other = parse((tmp / "output" / "design" / "设计集清单.json").read_text(encoding="utf-8"))
            mod2 = next(f for f in other["files"] if f["id"] == "MOD-002")
            self.assertEqual(mod2["sha256"], next(f for f in parse(
                (FIXTURES / "valid" / "output" / "design" / "设计集清单.json").read_text(encoding="utf-8")
            )["files"] if f["id"] == "MOD-002")["sha256"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_single_failed_check_keeps_formal_files(self):
        tmp = copy_fixture("valid")
        try:
            before = (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_text(encoding="utf-8")
            stage = run_cli(tmp, "stage-single", "--project-root", str(tmp), "--id", "MOD-001")
            self.assertEqual(stage.returncode, 0)
            # 不写 staged：commit 必须失败且正式文件不变
            commit = run_cli(tmp, "commit-single", "--project-root", str(tmp))
            self.assertEqual(commit.returncode, 2)
            after = (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertTrue((tmp / ".workflow" / "runtime" / "design-change" / "single" / "active.json").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_single_interrupted_recover_restores(self):
        tmp = copy_fixture("interrupted-single")
        try:
            before = (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_text(encoding="utf-8")
            # 模拟替换途中被中断：正式文件已是半成品
            (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text("# 半成品\n", encoding="utf-8")
            recover = run_cli(tmp, "recover", "--project-root", str(tmp))
            self.assertEqual(recover.returncode, 0, recover.stdout)
            after = (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertFalse((tmp / ".workflow" / "runtime" / "design-change" / "single").exists())
            check = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(check.returncode, 0, check.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class MultiFileTransactionTests(unittest.TestCase):
    def test_multi_success(self):
        tmp = copy_fixture("valid")
        try:
            begin = run_cli(tmp, "begin", "--project-root", str(tmp), "--ids", "MOD-001", "MOD-002")
            self.assertEqual(begin.returncode, 0, begin.stdout)
            info = parse(begin.stdout)
            sdir = Path(info["staged_dir"])
            (sdir / "MOD-001__模块设计_订单_订单管理.md").write_text("# 模块设计：订单管理 v3\n", encoding="utf-8")
            (sdir / "MOD-002__模块设计_库存_库存管理.md").write_text("# 模块设计：库存管理 v3\n", encoding="utf-8")
            commit = run_cli(tmp, "commit", "--project-root", str(tmp))
            self.assertEqual(commit.returncode, 0, commit.stdout)
            self.assertIn("v3", (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_text(encoding="utf-8"))
            self.assertIn("v3", (tmp / "output" / "design" / "模块设计" / "库存" / "库存管理.md").read_text(encoding="utf-8"))
            self.assertFalse((tmp / ".workflow" / "runtime" / "design-change").exists())
            check = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(check.returncode, 0, check.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_multi_staging_interrupt_recover_restores_old(self):
        tmp = copy_fixture("interrupted-multi")
        try:
            before1 = (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_text(encoding="utf-8")
            before2 = (tmp / "output" / "design" / "模块设计" / "库存" / "库存管理.md").read_text(encoding="utf-8")
            recover = run_cli(tmp, "recover", "--project-root", str(tmp))
            self.assertEqual(recover.returncode, 0, recover.stdout)
            after1 = (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_text(encoding="utf-8")
            after2 = (tmp / "output" / "design" / "模块设计" / "库存" / "库存管理.md").read_text(encoding="utf-8")
            self.assertEqual(before1, after1)
            self.assertEqual(before2, after2)
            check = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(check.returncode, 0, check.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_multi_replacing_completes_new_state(self):
        tmp = copy_fixture("interrupted-multi")
        try:
            w = tmp / ".workflow" / "runtime" / "design-change"
            sdir = w / "staged"
            active_path = w / "active.json"
            active = json.loads(active_path.read_text(encoding="utf-8"))
            active["phase"] = "replacing"
            active_path.write_text(json.dumps(active, ensure_ascii=False, indent=2), encoding="utf-8")
            (sdir / "MOD-001__模块设计_订单_订单管理.md").write_text("# 模块设计：订单管理 NEW\n", encoding="utf-8")
            (sdir / "MOD-002__模块设计_库存_库存管理.md").write_text("# 模块设计：库存管理 NEW\n", encoding="utf-8")
            recover = run_cli(tmp, "recover", "--project-root", str(tmp))
            self.assertEqual(recover.returncode, 0, recover.stdout)
            self.assertIn("NEW", (tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").read_text(encoding="utf-8"))
            check = run_cli(tmp, "check", "--project-root", str(tmp))
            self.assertEqual(check.returncode, 0, check.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = copy_fixture("valid")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_record_and_check_inputs(self):
        rec = run_cli(self.tmp, "record-inputs", "--project-root", str(self.tmp),
                      "--artifact", "prd", "--target-id", "prd:订单", "--target-name", "订单",
                      "--output-path", "output/prd/prd.md", "--output-locator", "## 4.6 订单",
                      "--inputs", "SYS-001,CON-001,MOD-001")
        self.assertEqual(rec.returncode, 0, rec.stdout)
        prov = json.loads((self.tmp / ".workflow" / "provenance" / "prd.json").read_text(encoding="utf-8"))
        self.assertEqual(prov["targets"][0]["status"], "current")
        self.assertEqual(len(prov["targets"][0]["design_inputs"]), 3)
        checked = parse(run_cli(self.tmp, "check-inputs", "--project-root", str(self.tmp), "--artifact", "prd").stdout)
        self.assertEqual(checked["targets"][0]["status"], "current")

    def test_external_change_marks_affected(self):
        run_cli(self.tmp, "record-inputs", "--project-root", str(self.tmp),
                "--artifact", "prd", "--target-id", "prd:订单", "--target-name", "订单",
                "--output-path", "output/prd/prd.md", "--output-locator", "## 4.6 订单",
                "--inputs", "SYS-001,CON-001,MOD-001")
        (self.tmp / "output" / "design" / "模块设计" / "订单" / "订单管理.md").write_text("# 外部修改\n", encoding="utf-8")
        checked = parse(run_cli(self.tmp, "check-inputs", "--project-root", str(self.tmp), "--artifact", "prd").stdout)
        self.assertEqual(checked["targets"][0]["status"], "affected")
        self.assertTrue(checked["targets"][0]["actual_mismatch"])

    def test_commit_marks_provenance_affected(self):
        run_cli(self.tmp, "record-inputs", "--project-root", str(self.tmp),
                "--artifact", "prd", "--target-id", "prd:订单", "--target-name", "订单",
                "--output-path", "output/prd/prd.md", "--output-locator", "## 4.6 订单",
                "--inputs", "SYS-001,CON-001,MOD-001")
        stage = run_cli(self.tmp, "stage-single", "--project-root", str(self.tmp), "--id", "MOD-001")
        staged_path = Path(parse(stage.stdout)["staged_path"])
        staged_path.write_text("# 模块设计：订单管理 v2\n", encoding="utf-8")
        commit = run_cli(self.tmp, "commit-single", "--project-root", str(self.tmp))
        self.assertEqual(commit.returncode, 0, commit.stdout)
        prov = json.loads((self.tmp / ".workflow" / "provenance" / "prd.json").read_text(encoding="utf-8"))
        t = prov["targets"][0]
        self.assertEqual(t["status"], "affected")
        self.assertEqual(t["affected_by"], ["MOD-001"])
        self.assertEqual(t["check_status"], "not_run")

    def test_commit_organization_keeps_provenance_current(self):
        # D-07 纯组织变化：commit --semantic organization 只更新指纹，下游保持 current
        run_cli(self.tmp, "record-inputs", "--project-root", str(self.tmp),
                "--artifact", "prd", "--target-id", "prd:订单", "--target-name", "订单",
                "--output-path", "output/prd/prd.md", "--output-locator", "## 4.6 订单",
                "--inputs", "SYS-001,CON-001,MOD-001")
        stage = run_cli(self.tmp, "stage-single", "--project-root", str(self.tmp), "--id", "MOD-001")
        staged_path = Path(parse(stage.stdout)["staged_path"])
        staged_path.write_text("# 模块设计：订单管理（组织整理）\n", encoding="utf-8")
        commit = run_cli(self.tmp, "commit-single", "--project-root", str(self.tmp), "--semantic", "organization")
        self.assertEqual(commit.returncode, 0, commit.stdout)
        prov = json.loads((self.tmp / ".workflow" / "provenance" / "prd.json").read_text(encoding="utf-8"))
        t = prov["targets"][0]
        self.assertEqual(t["status"], "current")
        self.assertEqual(t["affected_by"], [])
        self.assertEqual(t["check_status"], "passed")
        # 指纹已更新为 staged 新内容
        manifest = json.loads((self.tmp / "output" / "design" / "设计集清单.json").read_text(encoding="utf-8"))
        mod = next(f for f in manifest["files"] if f["id"] == "MOD-001")
        inp = next(i for i in t["design_inputs"] if i["id"] == "MOD-001")
        self.assertEqual(inp["sha256"], mod["sha256"])

    def test_check_inputs_reports_incomplete_when_provenance_missing(self):
        # F：下游产物存在但 provenance 缺失时，check-inputs 必须报 incomplete，不静默当无影响
        prd_dir = self.tmp / "output" / "prd"
        prd_dir.mkdir(parents=True, exist_ok=True)
        (prd_dir / "prd.md").write_text("# PRD 订单\n", encoding="utf-8")
        checked = parse(run_cli(self.tmp, "check-inputs", "--project-root", str(self.tmp), "--artifact", "prd").stdout)
        statuses = [t["status"] for t in checked["targets"]]
        self.assertIn("incomplete", statuses)
        incomplete = next(t for t in checked["targets"] if t["status"] == "incomplete")
        self.assertIn("provenance_missing", incomplete.get("reason", ""))


class RefreshTests(unittest.TestCase):
    def test_refresh_recomputes_fingerprints(self):
        # C：refresh 重算文件 sha256 与 set_sha256 并写回清单
        tmp = copy_fixture("valid")
        try:
            # 破坏一个指纹
            manifest_path = tmp / "output" / "design" / "设计集清单.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"][3]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            before = parse(run_cli(tmp, "check", "--project-root", str(tmp)).stdout)
            self.assertFalse(before["ok"])
            refreshed = parse(run_cli(tmp, "refresh", "--project-root", str(tmp)).stdout)
            self.assertTrue(refreshed["ok"])
            self.assertIn("MOD-001", refreshed["updated"])
            after = parse(run_cli(tmp, "check", "--project-root", str(tmp)).stdout)
            self.assertTrue(after["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
