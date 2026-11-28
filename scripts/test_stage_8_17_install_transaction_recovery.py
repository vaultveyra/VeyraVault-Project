#!/usr/bin/env python3
"""Isolated crash-recovery harness for the Stage 8.16 package transaction design.

This is a deterministic filesystem model, NOT the production Engine installer.
It injects process-death at journal and rename boundaries and verifies that
recovery either keeps the committed new generation or restores the old one.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from typing import Callable, Optional

SCHEMA_VERSION = 1
PHASES = {
    "PREPARING",
    "STAGED_VALIDATED",
    "OLD_GENERATION_BACKED_UP",
    "OLD_USER_LIB_BACKED_UP",
    "USER_LIB_PUBLISHED",
    "NEW_GENERATION_PUBLISHED",
    "PACKAGE_METADATA_COMMITTED",
    "COMPLETE",
}
PACKAGE_RE = re.compile(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+")
PHASE_EVENTS = [
    "journal:PREPARING",
    "stage:package-created",
    "stage:package-written",
    "stage:user-lib-written",
    "journal:STAGED_VALIDATED",
    "rename:old-package-to-backup",
    "journal:OLD_GENERATION_BACKED_UP",
    "rename:old-user-lib-to-backup",
    "journal:OLD_USER_LIB_BACKED_UP",
    "rename:staged-user-lib-to-active",
    "journal:USER_LIB_PUBLISHED",
    "rename:staged-package-to-active",
    "journal:NEW_GENERATION_PUBLISHED",
    "metadata:committed",
    "journal:PACKAGE_METADATA_COMMITTED",
    "journal:COMPLETE",
]


class InjectedCrash(RuntimeError):
    """Represents abrupt process death at a named durable boundary."""


class RecoveryError(RuntimeError):
    """Recovery cannot prove which generation is safe; preserve all candidates."""


def fsync_directory(path: Path) -> None:
    """Best-effort POSIX directory fsync; tests run on a local POSIX filesystem."""
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(str(path), flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_write(path: Path, data: bytes) -> None:
    """Write to a sibling temp file, fsync, replace, then fsync its directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    fd = os.open(str(temp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temp), str(path))
        fsync_directory(path.parent)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def durable_json(path: Path, value: dict) -> None:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    durable_write(path, payload)


def tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.is_dir() or path.is_symlink():
        raise RecoveryError("Expected a regular directory for generation digest")
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise RecoveryError("Symlink found in generation tree")
        if item.is_file():
            relative = item.relative_to(path).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            with item.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RecoveryError("Journal/metadata is unreadable") from error
    if not isinstance(value, dict):
        raise RecoveryError("Journal/metadata root must be an object")
    return value


class TransactionHarness:
    """Small isolated model of a package generation and its reversible user lib."""

    def __init__(self, root: Path):
        self.root = root
        self.data_root = root / "data"
        self.app_root = self.data_root / "app"
        self.user_root = self.data_root / "user"
        self.transaction_root = self.data_root / ".veyravault-transactions"

    def package_path(self, package_name: str) -> Path:
        return self.app_root / package_name

    def user_lib_path(self, package_name: str, user_id: int) -> Path:
        return self.user_root / str(user_id) / package_name / "lib"

    def transaction_path(self, transaction_id: str) -> Path:
        return self.transaction_root / transaction_id

    def _validate_identity(self, package_name: str, user_id: int) -> None:
        if not isinstance(package_name, str) or not PACKAGE_RE.fullmatch(package_name):
            raise ValueError("Invalid package name; no filesystem mutation performed")
        if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id < 0:
            raise ValueError("Invalid virtual user ID; no filesystem mutation performed")

    @staticmethod
    def _event(hook: Optional[Callable[[str], None]], name: str) -> None:
        if hook is not None:
            hook(name)

    @staticmethod
    def _generation_id(package_dir: Path) -> Optional[str]:
        if not package_dir.exists():
            return None
        if package_dir.is_symlink() or not package_dir.is_dir():
            raise RecoveryError("Package generation path is not a regular directory")
        metadata = read_json(package_dir / "generation.json")
        value = metadata.get("generationId")
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _is_new_package(package_dir: Path, transaction_id: str) -> bool:
        marker = package_dir / ".transaction-id"
        try:
            return package_dir.is_dir() and not package_dir.is_symlink() and marker.read_text(
                encoding="utf-8"
            ) == transaction_id
        except OSError:
            return False

    @staticmethod
    def _is_new_user_lib(user_lib: Path, transaction_id: str) -> bool:
        marker = user_lib / ".transaction-id"
        try:
            return user_lib.is_dir() and not user_lib.is_symlink() and marker.read_text(
                encoding="utf-8"
            ) == transaction_id
        except OSError:
            return False

    def begin(
        self,
        package_name: str,
        user_id: int,
        new_generation: str,
        replace_user_lib: bool = True,
        hook: Optional[Callable[[str], None]] = None,
    ) -> str:
        self._validate_identity(package_name, user_id)
        if not isinstance(new_generation, str) or not new_generation:
            raise ValueError("New generation identifier is required")
        active = self.package_path(package_name)
        active_user_lib = self.user_lib_path(package_name, user_id)
        had_old_package = active.exists()
        had_old_user_lib = active_user_lib.exists()
        old_users = []
        old_package_digest = None
        old_user_lib_digest = None
        if had_old_package:
            old_users = read_json(active / "package.conf").get("installedUsers", [])
            if not isinstance(old_users, list) or any(
                isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in old_users
            ):
                raise RecoveryError("Existing package user-state metadata is invalid")
            old_package_digest = tree_digest(active)
        if had_old_user_lib:
            old_user_lib_digest = tree_digest(active_user_lib)

        transaction_id = str(uuid.uuid4())
        transaction_dir = self.transaction_path(transaction_id)
        transaction_dir.mkdir(parents=True, exist_ok=False)
        journal = {
            "schemaVersion": SCHEMA_VERSION,
            "transactionId": transaction_id,
            "packageName": package_name,
            "userId": user_id,
            "phase": "PREPARING",
            "hadOldPackage": had_old_package,
            "oldPackageGeneration": self._generation_id(active) if had_old_package else None,
            "oldPackageDigest": old_package_digest,
            "hadOldUserLib": had_old_user_lib,
            "oldUserLibDigest": old_user_lib_digest,
            "replaceUserLib": bool(replace_user_lib),
            "newGeneration": new_generation,
            "installedUsers": sorted(set(old_users + [user_id])),
        }
        durable_json(transaction_dir / "journal.json", journal)
        self._event(hook, "journal:PREPARING")

        staged_package = transaction_dir / "staged-package"
        staged_package.mkdir()
        self._event(hook, "stage:package-created")
        durable_write(staged_package / ".transaction-id", transaction_id.encode("utf-8"))
        durable_json(staged_package / "generation.json", {"generationId": new_generation})
        durable_json(
            staged_package / "package.conf",
            {
                "packageName": package_name,
                "transactionId": transaction_id,
                "generationId": new_generation,
                "installedUsers": journal["installedUsers"],
            },
        )
        durable_write(staged_package / "payload.bin", ("payload:" + new_generation).encode("utf-8"))
        fsync_directory(staged_package)
        self._event(hook, "stage:package-written")

        if replace_user_lib:
            staged_user_lib = transaction_dir / "staged-user-lib"
            staged_user_lib.mkdir()
            durable_write(staged_user_lib / ".transaction-id", transaction_id.encode("utf-8"))
            durable_write(staged_user_lib / "libnew.so", b"simulated-new-native-library")
            fsync_directory(staged_user_lib)
            self._event(hook, "stage:user-lib-written")

        journal["phase"] = "STAGED_VALIDATED"
        durable_json(transaction_dir / "journal.json", journal)
        self._event(hook, "journal:STAGED_VALIDATED")
        return transaction_id

    def commit(
        self,
        transaction_id: str,
        hook: Optional[Callable[[str], None]] = None,
    ) -> None:
        transaction_dir = self.transaction_path(transaction_id)
        journal = self._load_journal(transaction_dir, transaction_id)
        if journal["phase"] != "STAGED_VALIDATED":
            raise RecoveryError("Only a validated staged transaction can be committed")

        package_name = journal["packageName"]
        user_id = journal["userId"]
        active = self.package_path(package_name)
        active_user_lib = self.user_lib_path(package_name, user_id)
        backup_package = transaction_dir / "backup-package"
        backup_user_lib = transaction_dir / "backup-user-lib"
        staged_package = transaction_dir / "staged-package"
        staged_user_lib = transaction_dir / "staged-user-lib"

        if active.exists():
            if backup_package.exists():
                raise RecoveryError("Package backup path unexpectedly exists")
            backup_package.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(active), str(backup_package))
            fsync_directory(active.parent)
            fsync_directory(backup_package.parent)
            self._event(hook, "rename:old-package-to-backup")
        elif journal["hadOldPackage"]:
            raise RecoveryError("Expected old package generation disappeared before commit")

        self._set_phase(transaction_dir, journal, "OLD_GENERATION_BACKED_UP", hook)

        if journal["replaceUserLib"]:
            if active_user_lib.exists():
                backup_user_lib.parent.mkdir(parents=True, exist_ok=True)
                os.replace(str(active_user_lib), str(backup_user_lib))
                fsync_directory(active_user_lib.parent)
                fsync_directory(backup_user_lib.parent)
                self._event(hook, "rename:old-user-lib-to-backup")
            self._set_phase(transaction_dir, journal, "OLD_USER_LIB_BACKED_UP", hook)

            if staged_user_lib.exists():
                active_user_lib.parent.mkdir(parents=True, exist_ok=True)
                os.replace(str(staged_user_lib), str(active_user_lib))
                fsync_directory(active_user_lib.parent)
                fsync_directory(active_user_lib.parent.parent)
                self._event(hook, "rename:staged-user-lib-to-active")
            self._set_phase(transaction_dir, journal, "USER_LIB_PUBLISHED", hook)

        active.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(staged_package), str(active))
        fsync_directory(active.parent)
        self._event(hook, "rename:staged-package-to-active")
        self._set_phase(transaction_dir, journal, "NEW_GENERATION_PUBLISHED", hook)

        self._validate_new_package(active, journal)
        if journal["replaceUserLib"]:
            self._validate_new_user_lib(active_user_lib, transaction_id)
        self._event(hook, "metadata:committed")
        self._set_phase(transaction_dir, journal, "PACKAGE_METADATA_COMMITTED", hook)
        self._set_phase(transaction_dir, journal, "COMPLETE", hook)
        self._cleanup_completed(transaction_dir, journal)

    def _set_phase(
        self,
        transaction_dir: Path,
        journal: dict,
        phase: str,
        hook: Optional[Callable[[str], None]],
    ) -> None:
        journal["phase"] = phase
        durable_json(transaction_dir / "journal.json", journal)
        self._event(hook, "journal:" + phase)

    def _load_journal(self, transaction_dir: Path, expected_id: str) -> dict:
        if transaction_dir.is_symlink() or not transaction_dir.is_dir():
            raise RecoveryError("Transaction path is not a regular directory")
        if transaction_dir.name != expected_id:
            raise RecoveryError("Transaction directory identity mismatch")
        try:
            uuid.UUID(expected_id)
        except (ValueError, AttributeError) as error:
            raise RecoveryError("Transaction ID is invalid") from error
        journal = read_json(transaction_dir / "journal.json")
        required = {
            "schemaVersion", "transactionId", "packageName", "userId", "phase",
            "hadOldPackage", "oldPackageGeneration", "oldPackageDigest",
            "hadOldUserLib", "oldUserLibDigest", "replaceUserLib",
            "newGeneration", "installedUsers",
        }
        if set(journal) != required:
            raise RecoveryError("Journal fields do not match the supported schema")
        if journal["schemaVersion"] != SCHEMA_VERSION:
            raise RecoveryError("Unsupported journal schema version")
        if journal["transactionId"] != expected_id:
            raise RecoveryError("Journal transaction ID mismatch")
        if journal["phase"] not in PHASES:
            raise RecoveryError("Unknown transaction phase")
        try:
            self._validate_identity(journal["packageName"], journal["userId"])
        except ValueError as error:
            raise RecoveryError("Journal identity is invalid") from error
        for key in ("hadOldPackage", "hadOldUserLib", "replaceUserLib"):
            if type(journal[key]) is not bool:
                raise RecoveryError("Journal boolean field is invalid")
        if not isinstance(journal["newGeneration"], str) or not journal["newGeneration"]:
            raise RecoveryError("Journal generation identifier is invalid")
        users = journal["installedUsers"]
        if not isinstance(users, list) or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in users
        ):
            raise RecoveryError("Journal installed-user list is invalid")
        return journal

    def recover_all(self) -> None:
        if not self.transaction_root.exists():
            return
        if self.transaction_root.is_symlink() or not self.transaction_root.is_dir():
            raise RecoveryError("Transaction root is not a regular directory")
        for transaction_dir in sorted(self.transaction_root.iterdir()):
            if transaction_dir.is_symlink() or not transaction_dir.is_dir():
                raise RecoveryError("Unexpected object in transaction root; left untouched")
            journal = self._load_journal(transaction_dir, transaction_dir.name)
            if journal["phase"] == "COMPLETE":
                self._validate_new_package(self.package_path(journal["packageName"]), journal)
                if journal["replaceUserLib"]:
                    self._validate_new_user_lib(
                        self.user_lib_path(journal["packageName"], journal["userId"]),
                        journal["transactionId"],
                    )
                self._cleanup_completed(transaction_dir, journal)
            else:
                self._rollback(transaction_dir, journal)

    @staticmethod
    def _validate_new_package(active: Path, journal: dict) -> None:
        if active.is_symlink() or not active.is_dir():
            raise RecoveryError("Published package generation is missing or unsafe")
        transaction_id = journal["transactionId"]
        if not TransactionHarness._is_new_package(active, transaction_id):
            raise RecoveryError("Published package marker does not match the journal")
        metadata = read_json(active / "package.conf")
        if (
            metadata.get("packageName") != journal["packageName"]
            or metadata.get("transactionId") != transaction_id
            or metadata.get("generationId") != journal["newGeneration"]
            or metadata.get("installedUsers") != journal["installedUsers"]
        ):
            raise RecoveryError("Published package metadata does not match the journal")

    @staticmethod
    def _validate_new_user_lib(active_user_lib: Path, transaction_id: str) -> None:
        if not TransactionHarness._is_new_user_lib(active_user_lib, transaction_id):
            raise RecoveryError("Published user library marker does not match the journal")
        if not (active_user_lib / "libnew.so").is_file():
            raise RecoveryError("Published user library payload is missing")

    def _rollback(self, transaction_dir: Path, journal: dict) -> None:
        transaction_id = journal["transactionId"]
        package_name = journal["packageName"]
        user_id = journal["userId"]
        active = self.package_path(package_name)
        backup_package = transaction_dir / "backup-package"

        if backup_package.exists():
            if active.exists():
                if not self._is_new_package(active, transaction_id):
                    raise RecoveryError("Ambiguous active and backup package generations; preserved")
                shutil.rmtree(active)
            os.replace(str(backup_package), str(active))
            fsync_directory(active.parent)
        elif journal["hadOldPackage"]:
            if not active.exists() or self._is_new_package(active, transaction_id):
                raise RecoveryError("Last-known-good package generation is missing; preserved")
        elif active.exists():
            if not self._is_new_package(active, transaction_id):
                raise RecoveryError("Unexpected package at fresh-install target; preserved")
            shutil.rmtree(active)

        if journal["hadOldPackage"]:
            if self._generation_id(active) != journal["oldPackageGeneration"]:
                raise RecoveryError("Restored package generation does not match journal")
            if tree_digest(active) != journal["oldPackageDigest"]:
                raise RecoveryError("Restored package digest does not match journal")

        if journal["replaceUserLib"]:
            active_user_lib = self.user_lib_path(package_name, user_id)
            backup_user_lib = transaction_dir / "backup-user-lib"
            if backup_user_lib.exists():
                if active_user_lib.exists():
                    if not self._is_new_user_lib(active_user_lib, transaction_id):
                        raise RecoveryError("Ambiguous active and backup user libraries; preserved")
                    shutil.rmtree(active_user_lib)
                active_user_lib.parent.mkdir(parents=True, exist_ok=True)
                os.replace(str(backup_user_lib), str(active_user_lib))
                fsync_directory(active_user_lib.parent)
            elif journal["hadOldUserLib"]:
                if not active_user_lib.exists() or self._is_new_user_lib(active_user_lib, transaction_id):
                    raise RecoveryError("Last-known-good user library is missing; preserved")
            elif active_user_lib.exists():
                if not self._is_new_user_lib(active_user_lib, transaction_id):
                    raise RecoveryError("Unexpected user library at fresh-install target; preserved")
                shutil.rmtree(active_user_lib)

            if journal["hadOldUserLib"]:
                if tree_digest(active_user_lib) != journal["oldUserLibDigest"]:
                    raise RecoveryError("Restored user library digest does not match journal")

        shutil.rmtree(transaction_dir)

    @staticmethod
    def _cleanup_completed(transaction_dir: Path, journal: dict) -> None:
        if journal["phase"] != "COMPLETE":
            raise RecoveryError("Cannot clean up an uncommitted transaction")
        if transaction_dir.exists():
            shutil.rmtree(transaction_dir)
            fsync_directory(transaction_dir.parent)


def seed_existing_state(manager: TransactionHarness, package_name: str, user_id: int) -> None:
    package = manager.package_path(package_name)
    package.mkdir(parents=True)
    durable_json(package / "generation.json", {"generationId": "known-good-v1"})
    durable_json(
        package / "package.conf",
        {
            "packageName": package_name,
            "generationId": "known-good-v1",
            "installedUsers": [user_id, user_id + 1],
        },
    )
    durable_write(package / "payload.bin", b"known-good-package-payload")

    user_lib = manager.user_lib_path(package_name, user_id)
    user_lib.mkdir(parents=True)
    durable_write(user_lib / "libold.so", b"known-good-native-library")
    user_data = manager.user_root / str(user_id) / package_name
    durable_write(user_data / "files" / "user-data.bin", b"must-survive")
    durable_write(user_data / "shared_prefs" / "settings.xml", b"<settings>keep</settings>")
    durable_write(
        manager.data_root / "user_de" / str(user_id) / package_name / "de-data.bin",
        b"device-protected-data",
    )
    durable_write(
        manager.data_root / "external" / str(user_id) / package_name / "external.bin",
        b"external-data",
    )
    durable_write(manager.root / "host" / "veyravault_clones_v2.xml", b"clone-store-registry")
    durable_write(manager.root / "host" / "pending-reservations.json", b"reservation-journal")


def assert_preserved_state(test: unittest.TestCase, manager: TransactionHarness, package_name: str, user_id: int) -> None:
    user_data = manager.user_root / str(user_id) / package_name
    test.assertEqual((user_data / "files" / "user-data.bin").read_bytes(), b"must-survive")
    test.assertEqual((user_data / "shared_prefs" / "settings.xml").read_bytes(), b"<settings>keep</settings>")
    test.assertEqual(
        (manager.data_root / "user_de" / str(user_id) / package_name / "de-data.bin").read_bytes(),
        b"device-protected-data",
    )
    test.assertEqual(
        (manager.data_root / "external" / str(user_id) / package_name / "external.bin").read_bytes(),
        b"external-data",
    )
    test.assertEqual((manager.root / "host" / "veyravault_clones_v2.xml").read_bytes(), b"clone-store-registry")
    test.assertEqual((manager.root / "host" / "pending-reservations.json").read_bytes(), b"reservation-journal")


class TransactionRecoveryTests(unittest.TestCase):
    PACKAGE = "com.example.vault"
    USER_ID = 42

    def test_successful_replacement_preserves_users_and_all_non_library_data(self):
        with tempfile.TemporaryDirectory() as temp:
            manager = TransactionHarness(Path(temp))
            seed_existing_state(manager, self.PACKAGE, self.USER_ID)
            transaction_id = manager.begin(self.PACKAGE, self.USER_ID, "known-good-v2")
            manager.commit(transaction_id)

            active = manager.package_path(self.PACKAGE)
            metadata = read_json(active / "package.conf")
            self.assertEqual(metadata["generationId"], "known-good-v2")
            self.assertEqual(metadata["installedUsers"], [42, 43])
            self.assertEqual((manager.user_lib_path(self.PACKAGE, self.USER_ID) / "libnew.so").read_bytes(),
                             b"simulated-new-native-library")
            self.assertFalse(manager.transaction_root.exists() and list(manager.transaction_root.iterdir()))
            assert_preserved_state(self, manager, self.PACKAGE, self.USER_ID)

    def test_crash_at_every_durable_boundary_recovers_to_old_or_completed_new(self):
        for crash_point in PHASE_EVENTS:
            with self.subTest(crash_point=crash_point), tempfile.TemporaryDirectory() as temp:
                manager = TransactionHarness(Path(temp))
                seed_existing_state(manager, self.PACKAGE, self.USER_ID)

                def crash_hook(event: str) -> None:
                    if event == crash_point:
                        raise InjectedCrash(event)

                with self.assertRaises(InjectedCrash):
                    transaction_id = manager.begin(
                        self.PACKAGE, self.USER_ID, "known-good-v2", hook=crash_hook
                    )
                    manager.commit(transaction_id, hook=crash_hook)

                TransactionHarness(Path(temp)).recover_all()
                active = manager.package_path(self.PACKAGE)
                expected_new = crash_point == "journal:COMPLETE"
                expected_generation = "known-good-v2" if expected_new else "known-good-v1"
                self.assertEqual(self._generation(active), expected_generation)
                if expected_new:
                    self.assertEqual(
                        (manager.user_lib_path(self.PACKAGE, self.USER_ID) / "libnew.so").read_bytes(),
                        b"simulated-new-native-library",
                    )
                else:
                    self.assertEqual(
                        (manager.user_lib_path(self.PACKAGE, self.USER_ID) / "libold.so").read_bytes(),
                        b"known-good-native-library",
                    )
                assert_preserved_state(self, manager, self.PACKAGE, self.USER_ID)

    def test_fresh_install_crash_rolls_back_without_touching_user_data(self):
        with tempfile.TemporaryDirectory() as temp:
            manager = TransactionHarness(Path(temp))
            package_user_data = manager.user_root / str(self.USER_ID) / self.PACKAGE
            durable_write(package_user_data / "files" / "keep.bin", b"existing-user-content")
            transaction_id = manager.begin(self.PACKAGE, self.USER_ID, "fresh-v1")
            with self.assertRaises(InjectedCrash):
                manager.commit(
                    transaction_id,
                    hook=lambda event: (_ for _ in ()).throw(InjectedCrash(event))
                    if event == "journal:NEW_GENERATION_PUBLISHED" else None,
                )
            manager.recover_all()
            self.assertFalse(manager.package_path(self.PACKAGE).exists())
            self.assertFalse(manager.user_lib_path(self.PACKAGE, self.USER_ID).exists())
            self.assertEqual((package_user_data / "files" / "keep.bin").read_bytes(),
                             b"existing-user-content")

    def test_invalid_package_name_is_rejected_before_filesystem_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            manager = TransactionHarness(Path(temp))
            with self.assertRaises(ValueError):
                manager.begin("../../outside", self.USER_ID, "bad")
            self.assertFalse((Path(temp) / "outside").exists())
            self.assertFalse(manager.transaction_root.exists())

    def test_corrupt_journal_fails_closed_and_preserves_active_and_backup_generations(self):
        with tempfile.TemporaryDirectory() as temp:
            manager = TransactionHarness(Path(temp))
            seed_existing_state(manager, self.PACKAGE, self.USER_ID)
            transaction_id = manager.begin(self.PACKAGE, self.USER_ID, "candidate-v2")
            with self.assertRaises(InjectedCrash):
                manager.commit(
                    transaction_id,
                    hook=lambda event: (_ for _ in ()).throw(InjectedCrash(event))
                    if event == "rename:staged-package-to-active" else None,
                )
            tx_dir = manager.transaction_path(transaction_id)
            active = manager.package_path(self.PACKAGE)
            backup = tx_dir / "backup-package"
            self.assertEqual(self._generation(active), "candidate-v2")
            self.assertEqual(self._generation(backup), "known-good-v1")
            durable_write(tx_dir / "journal.json", b'{"truncated":')
            with self.assertRaises(RecoveryError):
                manager.recover_all()
            self.assertEqual(self._generation(active), "candidate-v2")
            self.assertEqual(self._generation(backup), "known-good-v1")
            self.assertTrue((tx_dir / "staged-user-lib").exists() is False)

    def test_unknown_schema_and_path_tampering_fail_closed(self):
        for mutation in ("schema", "package"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                manager = TransactionHarness(Path(temp))
                seed_existing_state(manager, self.PACKAGE, self.USER_ID)
                transaction_id = manager.begin(self.PACKAGE, self.USER_ID, "candidate-v2")
                tx_dir = manager.transaction_path(transaction_id)
                journal = read_json(tx_dir / "journal.json")
                if mutation == "schema":
                    journal["schemaVersion"] = 999
                else:
                    journal["packageName"] = "../../outside"
                durable_json(tx_dir / "journal.json", journal)
                with self.assertRaises(RecoveryError):
                    manager.recover_all()
                self.assertEqual(self._generation(manager.package_path(self.PACKAGE)),
                                 "known-good-v1")
                self.assertTrue(tx_dir.exists())

    def test_missing_backup_with_missing_old_active_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            manager = TransactionHarness(Path(temp))
            seed_existing_state(manager, self.PACKAGE, self.USER_ID)
            transaction_id = manager.begin(self.PACKAGE, self.USER_ID, "candidate-v2")
            with self.assertRaises(InjectedCrash):
                manager.commit(
                    transaction_id,
                    hook=lambda event: (_ for _ in ()).throw(InjectedCrash(event))
                    if event == "rename:old-package-to-backup" else None,
                )
            tx_dir = manager.transaction_path(transaction_id)
            shutil.rmtree(tx_dir / "backup-package")
            with self.assertRaises(RecoveryError):
                manager.recover_all()
            self.assertFalse(manager.package_path(self.PACKAGE).exists())
            self.assertTrue(tx_dir.exists())

    @staticmethod
    def _generation(package_dir: Path) -> Optional[str]:
        return TransactionHarness._generation_id(package_dir)


def audit_known_production_blockers() -> None:
    """Require an explicit re-audit if the pinned Engine source changes these blockers."""
    root = Path("build_workspace") / "Bcore" / "src" / "main" / "java" / "top" / "niunaijun" / "blackbox"
    settings_file = root / "core" / "system" / "pm" / "Settings.java"
    manager_file = root / "core" / "system" / "pm" / "BPackageManagerService.java"
    package_settings_file = root / "core" / "system" / "pm" / "BPackageSettings.java"
    create_executor_file = root / "core" / "system" / "pm" / "installer" / "CreatePackageExecutor.java"
    for source in (settings_file, manager_file, package_settings_file, create_executor_file):
        if not source.is_file():
            raise AssertionError("Pinned Engine source missing; transaction blocker audit requires review: " + str(source))

    settings = settings_file.read_text(encoding="utf-8")
    manager = manager_file.read_text(encoding="utf-8")
    package_settings = package_settings_file.read_text(encoding="utf-8")
    create_executor = create_executor_file.read_text(encoding="utf-8")

    assert "public boolean save()" in package_settings
    assert "return false;" in package_settings
    save_pos = manager.find("bPackageSettings.save();")
    scan_pos = manager.find("mSettings.scanPackage(aPackage.packageName);", save_pos)
    success_pos = manager.find("return result;", scan_pos)
    assert save_pos >= 0 and scan_pos > save_pos and success_pos > scan_pos, (
        "Engine install-save/scan/return control flow changed; re-audit false-success risk"
    )
    assert "FileUtils.deleteDir(app);" in settings, (
        "Engine scan cleanup changed; re-audit quarantine and recovery semantics"
    )
    assert "FileUtils.deleteDir(BEnvironment.getAppDir(ps.pkg.packageName));" in create_executor, (
        "Engine package replacement deletion changed; re-audit commit ordering"
    )

    print("Production Engine integration status: BLOCKED by known source-level hazards.")
    print("  - package settings save result is still ignored by install caller")
    print("  - package scan catch path still deletes the package directory")
    print("  - package installer still deletes the active package directory before publication")
    print("This is a blocker inventory, not a passing production-safety test.")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TransactionRecoveryTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    audit_known_production_blockers()
    print("Stage 8.17 isolated install transaction recovery harness: PASS")
