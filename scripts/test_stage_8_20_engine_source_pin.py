#!/usr/bin/env python3
"""Verify fail-closed Engine source identity checks in workspace preparation."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "prepare_workspace.py"
SPEC = importlib.util.spec_from_file_location("veyravault_prepare_workspace", PREPARE_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)

EXPECTED_COMMIT = "89b59836c66f173756a4ae258cf379a957649820"
EXPECTED_REMOTE = "https://github.com/ALEX5402/NewBlackbox.git"


class EngineSourcePinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".git").mkdir()
        (self.root / "Bcore").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def fake_git(self, head=EXPECTED_COMMIT, remote=EXPECTED_REMOTE, status="", ignored=""):
        outputs = {
            ("rev-parse", "HEAD"): head + "\n",
            ("remote", "get-url", "origin"): remote + "\n",
            ("status", "--porcelain", "--untracked-files=all"): status,
            ("ls-files", "--others", "--ignored", "--exclude-standard"): ignored,
        }

        def run(command, **kwargs):
            self.assertEqual(command[:2], ["git", "-C"])
            self.assertEqual(command[2], str(self.root))
            self.assertTrue(kwargs.get("check"))
            self.assertTrue(kwargs.get("capture_output"))
            self.assertTrue(kwargs.get("text"))
            key = tuple(command[3:])
            if key not in outputs:
                raise AssertionError("Unexpected Git command: " + repr(key))
            return SimpleNamespace(stdout=outputs[key], stderr="")

        return run

    def test_exact_origin_commit_and_clean_worktree_are_accepted(self):
        with patch.object(prepare.subprocess, "run", side_effect=self.fake_git()):
            prepare.verify_engine_source(str(self.root))

    def test_mismatched_head_is_rejected_before_remote_or_status_checks(self):
        fake = self.fake_git(head="0" * 40)
        with patch.object(prepare.subprocess, "run", side_effect=fake) as mocked:
            with self.assertRaisesRegex(RuntimeError, "HEAD does not match"):
                prepare.verify_engine_source(str(self.root))
            self.assertEqual(mocked.call_count, 1)

    def test_unapproved_remote_is_rejected(self):
        fake = self.fake_git(remote="https://example.invalid/untrusted/Engine.git")
        with patch.object(prepare.subprocess, "run", side_effect=fake) as mocked:
            with self.assertRaisesRegex(RuntimeError, "origin does not match"):
                prepare.verify_engine_source(str(self.root))
            self.assertEqual(mocked.call_count, 2)

    def test_dirty_or_untracked_worktree_is_rejected(self):
        fake = self.fake_git(status="?? injected-source.java\n")
        with patch.object(prepare.subprocess, "run", side_effect=fake):
            with self.assertRaisesRegex(RuntimeError, "working tree is not clean"):
                prepare.verify_engine_source(str(self.root))

    def test_ignored_untracked_source_files_are_rejected(self):
        fake = self.fake_git(ignored="injected/ignored-source.java\\n")
        with patch.object(prepare.subprocess, "run", side_effect=fake):
            with self.assertRaisesRegex(RuntimeError, "ignored untracked files"):
                prepare.verify_engine_source(str(self.root))

    def test_missing_git_metadata_is_rejected_without_invoking_git(self):
        (self.root / ".git").rmdir()
        with patch.object(prepare.subprocess, "run") as mocked:
            with self.assertRaisesRegex(RuntimeError, "full Git checkout"):
                prepare.verify_engine_source(str(self.root))
            mocked.assert_not_called()

    def test_git_metadata_file_and_symlink_are_rejected(self):
        (self.root / ".git").rmdir()
        (self.root / ".git").write_text("gitdir: /outside/repository", encoding="utf-8")
        with patch.object(prepare.subprocess, "run") as mocked:
            with self.assertRaisesRegex(RuntimeError, "full Git checkout"):
                prepare.verify_engine_source(str(self.root))
            mocked.assert_not_called()

    def test_missing_bcore_module_is_rejected(self):
        import shutil
        shutil.rmtree(self.root / "Bcore")
        with patch.object(prepare.subprocess, "run") as mocked:
            with self.assertRaisesRegex(RuntimeError, "missing the expected Bcore"):
                prepare.verify_engine_source(str(self.root))
            mocked.assert_not_called()

    def test_source_directory_symlink_is_rejected(self):
        outside = self.root.parent / (self.root.name + "-outside")
        outside.mkdir()
        link = self.root.parent / (self.root.name + "-link")
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation is unavailable on this test filesystem")
        try:
            with patch.object(prepare.subprocess, "run") as mocked:
                with self.assertRaisesRegex(RuntimeError, "symbolic link"):
                    prepare.verify_engine_source(str(link))
                mocked.assert_not_called()
        finally:
            link.unlink()
            outside.rmdir()

    def test_workspace_preparation_verifies_both_bundle_and_checked_out_sources(self):
        source = PREPARE_PATH.read_text(encoding="utf-8")
        self.assertIn('verify_engine_source(BUNDLED_ENGINE)', source)
        self.assertIn('verify_engine_source(WORKSPACE)', source)
        bundle_verify = source.index("verify_engine_source(BUNDLED_ENGINE)")
        bundle_copy = source.index("shutil.copytree(BUNDLED_ENGINE, WORKSPACE)")
        workspace_verify = source.index("verify_engine_source(WORKSPACE)")
        disable_logs = source.index("disable_remote_log_upload(WORKSPACE)")
        self.assertLess(bundle_verify, bundle_copy)
        self.assertLess(workspace_verify, disable_logs)
        self.assertIn(f'ENGINE_REPOSITORY = "{EXPECTED_REMOTE}"', source)
        self.assertIn(f'ENGINE_COMMIT = "{EXPECTED_COMMIT}"', source)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EngineSourcePinTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Stage 8.20 Engine source identity and clean-tree gate: PASS")
