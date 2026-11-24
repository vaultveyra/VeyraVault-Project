#!/usr/bin/env python3
"""Isolated fail-safe package-scan quarantine model for Stage 8.19.

This is not the production Engine scanner. It demonstrates a safe policy:
a metadata read/parse problem records a recovery-required marker outside the
active package path, retains package files and prior in-memory/resolver state,
and never emits an uninstall notification.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unittest
import uuid
from pathlib import Path
from typing import Callable, Optional

SCHEMA_VERSION = 1
PACKAGE_RE = re.compile(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+")
VALID_REASONS = {
    "METADATA_UNREADABLE",
    "METADATA_MALFORMED",
    "METADATA_SCHEMA_INVALID",
}


class RecoveryRequired(RuntimeError):
    pass


def fsync_dir(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(str(path), flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise OSError("Recovery directory cannot be a symlink")
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    fd = os.open(str(temp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(json.dumps(value, sort_keys=True).encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temp), str(path))
        fsync_dir(path.parent)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def stable_tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    if root.is_symlink() or not root.is_dir():
        raise OSError("Expected package directory")
    for item in sorted(root.rglob("*")):
        if item.is_symlink():
            raise OSError("Symlink inside package tree")
        if item.is_file():
            rel = item.relative_to(root).as_posix().encode("utf-8")
            digest.update(len(rel).to_bytes(4, "big"))
            digest.update(rel)
            digest.update(item.read_bytes())
    return digest.hexdigest()


class SafePackageScanner:
    """Isolated model of non-destructive package metadata scanning."""

    def __init__(self, root: Path):
        self.root = root
        self.app_root = root / "data" / "app"
        self.recovery_root = root / "data" / ".veyravault-recovery"
        self.records_root = self.recovery_root / "records"
        self.loaded: dict[str, dict] = {}
        self.resolver: dict[str, tuple[str, ...]] = {}
        self.uninstall_notifications: list[tuple[str, str]] = []

    def _package_dir(self, package_name: str) -> Path:
        if not isinstance(package_name, str) or not PACKAGE_RE.fullmatch(package_name):
            raise ValueError("Invalid package name")
        package_dir = self.app_root / package_name
        if package_dir.parent != self.app_root:
            raise ValueError("Package path escaped app root")
        return package_dir

    def _record_path(self, package_name: str) -> Path:
        if self.records_root.is_symlink():
            raise OSError("Recovery record root cannot be a symlink")
        path = self.records_root / (package_name + ".json")
        if path.parent != self.records_root:
            raise ValueError("Recovery record path escaped reserved root")
        return path

    def _write_recovery_record(
        self,
        package_name: str,
        reason: str,
        phase: str,
        writer: Optional[Callable[[Path, dict], None]] = None,
    ) -> bool:
        record = {
            "schemaVersion": SCHEMA_VERSION,
            "packageName": package_name,
            "status": "RECOVERY_REQUIRED",
            "reason": reason,
            "phase": phase,
        }
        path = self._record_path(package_name)
        try:
            (writer or atomic_json)(path, record)
            return True
        except (OSError, TypeError, ValueError):
            return False

    def _record_is_valid(self, package_name: str) -> bool:
        path = self._record_path(package_name)
        if not path.exists():
            return True
        if path.is_symlink() or not path.is_file():
            return False
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False
        return (
            isinstance(record, dict)
            and record.get("schemaVersion") == SCHEMA_VERSION
            and record.get("packageName") == package_name
            and record.get("status") == "RECOVERY_REQUIRED"
            and record.get("reason") in VALID_REASONS
            and record.get("phase") == "PACKAGE_SCAN"
        )

    def _clear_recovery_record(self, package_name: str) -> bool:
        path = self._record_path(package_name)
        if path.is_symlink():
            return False
        if not path.exists():
            return True
        if not path.is_file() or not self._record_is_valid(package_name):
            return False
        try:
            path.unlink()
            fsync_dir(path.parent)
            return True
        except OSError:
            return False

    @staticmethod
    def _parse_metadata(raw: bytes, package_name: str) -> dict:
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise RecoveryRequired("METADATA_MALFORMED") from error
        if not isinstance(value, dict):
            raise RecoveryRequired("METADATA_SCHEMA_INVALID")
        if value.get("packageName") != package_name:
            raise RecoveryRequired("METADATA_SCHEMA_INVALID")
        generation = value.get("generationId")
        if not isinstance(generation, str) or not generation:
            raise RecoveryRequired("METADATA_SCHEMA_INVALID")
        users = value.get("installedUsers")
        if not isinstance(users, list) or any(
            isinstance(user, bool) or not isinstance(user, int) or user < 0
            for user in users
        ):
            raise RecoveryRequired("METADATA_SCHEMA_INVALID")
        components = value.get("componentNames", [])
        if not isinstance(components, list) or any(
            not isinstance(item, str) or not item for item in components
        ):
            raise RecoveryRequired("METADATA_SCHEMA_INVALID")
        return value

    def scan(
        self,
        package_name: str,
        *,
        reader: Optional[Callable[[Path], bytes]] = None,
        record_writer: Optional[Callable[[Path, dict], None]] = None,
    ) -> str:
        package_dir = self._package_dir(package_name)
        if package_dir.is_symlink():
            return "UNSAFE_PACKAGE_PATH"
        if not package_dir.exists():
            return "PACKAGE_NOT_PRESENT"
        if not package_dir.is_dir():
            return "UNSAFE_PACKAGE_PATH"

        # A corrupt recovery marker is itself ambiguous. Do not overwrite it,
        # clear it, or publish new in-memory state on top of it.
        if not self._record_is_valid(package_name):
            return "RECOVERY_RECORD_INVALID"

        try:
            raw = (reader or (lambda path: path.read_bytes()))(
                package_dir / "package.conf"
            )
        except OSError:
            reason = "METADATA_UNREADABLE"
            if not self._write_recovery_record(
                package_name, reason, "PACKAGE_SCAN", record_writer
            ):
                return "RECOVERY_MARKER_WRITE_FAILED"
            return "RECOVERY_REQUIRED"

        try:
            metadata = self._parse_metadata(raw, package_name)
        except RecoveryRequired as error:
            reason = str(error)
            if reason not in VALID_REASONS:
                reason = "METADATA_SCHEMA_INVALID"
            if not self._write_recovery_record(
                package_name, reason, "PACKAGE_SCAN", record_writer
            ):
                return "RECOVERY_MARKER_WRITE_FAILED"
            return "RECOVERY_REQUIRED"

        if not self._clear_recovery_record(package_name):
            return "RECOVERY_MARKER_CLEAR_FAILED"

        # Publish memory and resolver only after metadata validation and
        # recovery-marker reconciliation have succeeded.
        self.loaded[package_name] = dict(metadata)
        self.resolver[package_name] = tuple(metadata.get("componentNames", []))
        return "LOADED"

    def recovery_record(self, package_name: str) -> Optional[dict]:
        path = self._record_path(package_name)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None


def seed_package(scanner: SafePackageScanner, package_name: str) -> None:
    package_dir = scanner._package_dir(package_name)
    package_dir.mkdir(parents=True)
    atomic_json(
        package_dir / "package.conf",
        {
            "packageName": package_name,
            "generationId": "generation-v1",
            "installedUsers": [10, 11],
            "componentNames": ["MainActivity", "SyncService"],
        },
    )
    (package_dir / "base.apk").write_bytes(b"preserve-package-code")
    (package_dir / "package-extra.bin").write_bytes(b"preserve-metadata-neighbour")
    user = scanner.root / "data" / "user" / "10" / package_name
    (user / "files").mkdir(parents=True)
    (user / "files" / "important.bin").write_bytes(b"preserve-user-data")
    de = scanner.root / "data" / "user_de" / "10" / package_name
    de.mkdir(parents=True)
    (de / "device-protected.bin").write_bytes(b"preserve-de-data")
    external = scanner.root / "external" / "10" / package_name
    external.mkdir(parents=True)
    (external / "external.bin").write_bytes(b"preserve-external-data")
    host = scanner.root / "host"
    host.mkdir(parents=True)
    (host / "veyravault_clones_v2.xml").write_bytes(b"preserve-clonestore")
    (host / "pending-reservations.json").write_bytes(b"preserve-reservations")


def snapshot_protected_state(scanner: SafePackageScanner, package_name: str) -> dict:
    package_dir = scanner._package_dir(package_name)
    paths = [
        package_dir,
        scanner.root / "data" / "user" / "10" / package_name,
        scanner.root / "data" / "user_de" / "10" / package_name,
        scanner.root / "external" / "10" / package_name,
        scanner.root / "host",
    ]
    return {str(path.relative_to(scanner.root)): stable_tree_digest(path) for path in paths}


class PackageScanQuarantineTests(unittest.TestCase):
    PACKAGE = "com.example.scanner"

    def test_unreadable_metadata_preserves_files_maps_resolver_and_suppresses_uninstall(self):
        with tempfile.TemporaryDirectory() as temp:
            scanner = SafePackageScanner(Path(temp))
            seed_package(scanner, self.PACKAGE)
            self.assertEqual(scanner.scan(self.PACKAGE), "LOADED")
            before = snapshot_protected_state(scanner, self.PACKAGE)
            old_loaded = dict(scanner.loaded[self.PACKAGE])
            old_resolver = scanner.resolver[self.PACKAGE]

            def unreadable(_path: Path) -> bytes:
                raise PermissionError("simulated transient permission/read failure")

            self.assertEqual(
                scanner.scan(self.PACKAGE, reader=unreadable),
                "RECOVERY_REQUIRED",
            )
            self.assertEqual(snapshot_protected_state(scanner, self.PACKAGE), before)
            self.assertEqual(scanner.loaded[self.PACKAGE], old_loaded)
            self.assertEqual(scanner.resolver[self.PACKAGE], old_resolver)
            self.assertEqual(scanner.uninstall_notifications, [])
            record = scanner.recovery_record(self.PACKAGE)
            self.assertEqual(record["reason"], "METADATA_UNREADABLE")
            self.assertEqual(record["status"], "RECOVERY_REQUIRED")

    def test_malformed_metadata_is_preserved_and_is_not_reported_as_uninstall(self):
        with tempfile.TemporaryDirectory() as temp:
            scanner = SafePackageScanner(Path(temp))
            seed_package(scanner, self.PACKAGE)
            self.assertEqual(scanner.scan(self.PACKAGE), "LOADED")
            before = snapshot_protected_state(scanner, self.PACKAGE)
            (scanner._package_dir(self.PACKAGE) / "package.conf").write_bytes(b'{"broken":')
            damaged_snapshot = snapshot_protected_state(scanner, self.PACKAGE)

            self.assertEqual(scanner.scan(self.PACKAGE), "RECOVERY_REQUIRED")
            self.assertEqual(snapshot_protected_state(scanner, self.PACKAGE), damaged_snapshot)
            self.assertEqual(scanner.uninstall_notifications, [])
            self.assertEqual(
                scanner.recovery_record(self.PACKAGE)["reason"],
                "METADATA_MALFORMED",
            )
            self.assertTrue((scanner._package_dir(self.PACKAGE) / "base.apk").is_file())
            self.assertNotEqual(before, damaged_snapshot)

    def test_next_valid_scan_clears_recovery_record_and_republishes_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            scanner = SafePackageScanner(Path(temp))
            seed_package(scanner, self.PACKAGE)
            original = (scanner._package_dir(self.PACKAGE) / "package.conf").read_bytes()
            (scanner._package_dir(self.PACKAGE) / "package.conf").write_bytes(b"{")
            self.assertEqual(scanner.scan(self.PACKAGE), "RECOVERY_REQUIRED")
            self.assertIsNotNone(scanner.recovery_record(self.PACKAGE))

            (scanner._package_dir(self.PACKAGE) / "package.conf").write_bytes(original)
            self.assertEqual(scanner.scan(self.PACKAGE), "LOADED")
            self.assertIsNone(scanner.recovery_record(self.PACKAGE))
            self.assertEqual(scanner.loaded[self.PACKAGE]["generationId"], "generation-v1")
            self.assertEqual(
                scanner.resolver[self.PACKAGE],
                ("MainActivity", "SyncService"),
            )
            self.assertEqual(scanner.uninstall_notifications, [])

    def test_startup_scan_without_memory_retains_package_and_marks_recovery_required(self):
        with tempfile.TemporaryDirectory() as temp:
            seed = SafePackageScanner(Path(temp))
            seed_package(seed, self.PACKAGE)
            (seed._package_dir(self.PACKAGE) / "package.conf").write_bytes(b"not-json")
            before = snapshot_protected_state(seed, self.PACKAGE)

            fresh_process = SafePackageScanner(Path(temp))
            self.assertEqual(fresh_process.scan(self.PACKAGE), "RECOVERY_REQUIRED")
            self.assertEqual(snapshot_protected_state(fresh_process, self.PACKAGE), before)
            self.assertNotIn(self.PACKAGE, fresh_process.loaded)
            self.assertNotIn(self.PACKAGE, fresh_process.resolver)
            self.assertEqual(fresh_process.uninstall_notifications, [])
            self.assertEqual(
                fresh_process.recovery_record(self.PACKAGE)["reason"],
                "METADATA_MALFORMED",
            )

    def test_recovery_marker_write_failure_still_preserves_package_and_old_memory(self):
        with tempfile.TemporaryDirectory() as temp:
            scanner = SafePackageScanner(Path(temp))
            seed_package(scanner, self.PACKAGE)
            scanner.scan(self.PACKAGE)
            old_loaded = dict(scanner.loaded[self.PACKAGE])
            old_resolver = scanner.resolver[self.PACKAGE]
            bad = scanner._package_dir(self.PACKAGE) / "package.conf"
            bad.write_bytes(b"{")
            before_failure = snapshot_protected_state(scanner, self.PACKAGE)

            def fail_writer(_path: Path, _data: dict) -> None:
                raise OSError("simulated full/read-only recovery storage")

            self.assertEqual(
                scanner.scan(self.PACKAGE, record_writer=fail_writer),
                "RECOVERY_MARKER_WRITE_FAILED",
            )
            expected = snapshot_protected_state(scanner, self.PACKAGE)
            self.assertEqual(expected, before_failure)
            self.assertEqual(scanner.loaded[self.PACKAGE], old_loaded)
            self.assertEqual(scanner.resolver[self.PACKAGE], old_resolver)
            self.assertEqual(scanner.uninstall_notifications, [])
            self.assertFalse(scanner._record_path(self.PACKAGE).exists())
            self.assertTrue((scanner._package_dir(self.PACKAGE) / "base.apk").is_file())
            # Non-package user/host data remains byte-for-byte unchanged.
            for key in before:
                if key != "data/app/" + self.PACKAGE:
                    self.assertEqual(before[key], expected[key])

    def test_invalid_existing_recovery_marker_blocks_scan_without_deleting_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            scanner = SafePackageScanner(Path(temp))
            seed_package(scanner, self.PACKAGE)
            scanner.scan(self.PACKAGE)
            before = snapshot_protected_state(scanner, self.PACKAGE)
            record_path = scanner._record_path(self.PACKAGE)
            record_path.parent.mkdir(parents=True, exist_ok=True)
            record_path.write_text('{"schemaVersion":999}', encoding="utf-8")

            self.assertEqual(scanner.scan(self.PACKAGE), "RECOVERY_RECORD_INVALID")
            self.assertEqual(snapshot_protected_state(scanner, self.PACKAGE), before)
            self.assertEqual(scanner.loaded[self.PACKAGE]["generationId"], "generation-v1")
            self.assertEqual(scanner.uninstall_notifications, [])
            self.assertTrue(record_path.exists())

    def test_invalid_package_path_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            scanner = SafePackageScanner(Path(temp))
            with self.assertRaises(ValueError):
                scanner.scan("../escape")
            self.assertFalse(scanner.app_root.exists())

            scanner.app_root.mkdir(parents=True)
            outside = scanner.root / "outside"
            outside.mkdir()
            link = scanner.app_root / self.PACKAGE
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Symlink creation is unavailable on this test filesystem")
            self.assertEqual(scanner.scan(self.PACKAGE), "UNSAFE_PACKAGE_PATH")
            self.assertTrue(outside.is_dir())
            self.assertEqual(list(outside.iterdir()), [])

    def test_missing_metadata_is_quarantined_without_removing_package_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            scanner = SafePackageScanner(Path(temp))
            seed_package(scanner, self.PACKAGE)
            conf = scanner._package_dir(self.PACKAGE) / "package.conf"
            conf.unlink()
            self.assertEqual(scanner.scan(self.PACKAGE), "RECOVERY_REQUIRED")
            self.assertTrue(scanner._package_dir(self.PACKAGE).is_dir())
            self.assertTrue((scanner._package_dir(self.PACKAGE) / "base.apk").is_file())
            self.assertEqual(
                scanner.recovery_record(self.PACKAGE)["reason"],
                "METADATA_UNREADABLE",
            )
            self.assertEqual(scanner.uninstall_notifications, [])


def audit_production_scanner_is_still_blocked() -> None:
    source = (
        Path("build_workspace")
        / "Bcore/src/main/java/top/niunaijun/blackbox/core/system/pm/Settings.java"
    )
    if not source.is_file():
        raise AssertionError("Pinned Engine Settings.java missing; scanner audit cannot continue")
    text = source.read_text(encoding="utf-8")
    start = text.find("private void updatePackageLP(File app)")
    assert start >= 0, "Engine package scanner method changed; review quarantine integration"
    end = text.find("private BPackageSettings reInstallBySystem", start)
    assert end > start, "Could not isolate package scanner method for audit"
    method = text[start:end]
    catch = method.find("catch (Throwable e)")
    assert catch >= 0, "Scanner error handling changed; re-audit recovery behavior"
    catch_text = method[catch:]
    assert "FileUtils.deleteDir(app);" in catch_text, (
        "Known destructive scanner deletion changed; Stage 8.19 must be re-reviewed"
    )
    assert "removePackage(packageName);" in catch_text
    assert "onPackageUninstalled(packageName, true, BUserHandle.USER_ALL);" in catch_text
    print("Production Engine scanner integration: BLOCKED — current scan catch still deletes package directory.")
    print("The isolated quarantine model is not wired into production Engine.")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PackageScanQuarantineTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    audit_production_scanner_is_still_blocked()
    print("Stage 8.19 isolated package-scan quarantine harness: PASS")
