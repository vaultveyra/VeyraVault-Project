#!/usr/bin/env python3
"""Guard the atomic app-private snapshot backup and read-back verification."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "app/src/main/java/com/veyravault/space/core/persistence/LegacyCloneSnapshotBackup.java").read_text(encoding="utf-8")

for token in (
    'new File(context.getFilesDir(), DIRECTORY)',
    'private static final String DIRECTORY = "migration-backups"',
    'private static final String FILE_NAME = "clone-store-snapshot-v1.json"',
    "new AtomicFile(baseFile)",
    "if (baseFile.exists() || interruptedBackup.exists())",
    "refusing to overwrite it",
    "verifyBackupBytes(expectedBytes, existingBytes, digest)",
    "atomicFile.startWrite()",
    "output.getFD().sync()",
    "atomicFile.finishWrite(output)",
    "atomicFile.failWrite(output)",
    "atomicFile.openRead()",
    "MessageDigest.isEqual(expectedBytes, actualBytes)",
    'verified.getInt("formatVersion")',
    'verified.getString("snapshotSha256")',
    "MessageDigest.getInstance(\"SHA-256\")",
    "return new Receipt(digest, actualBytes.length)",
    "public static LegacyCloneSnapshot readAndVerify(Context context)",
    "atomicFile.openRead()",
    "LegacyCloneSnapshot.fromCanonicalPayload(payload)",
    "snapshot.sha256()",
    "Unsupported migration backup format version",

):
    assert token in source, "Atomic backup contract missing: " + token

for forbidden in (
    "getExternalFilesDir(",
    "Environment.getExternalStorage",
    "BlackBoxCore",
    "clone_sessions",
    "virtual-app",
    "deleteDatabase(",
    "fallbackToDestructiveMigration",
    "CloneStore.prefs",
):
    assert forbidden not in source, "Backup must remain isolated from engine/session storage: " + forbidden

app = (root / "app/src/main/java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
assert "LegacyCloneSnapshotBackup" not in app
print("Atomic app-private backup and fsync contract: PASS")
print("Read-back byte equality and SHA-256 envelope verification contract: PASS")
print("Backup remains opt-in and isolated from virtual-app/session storage: PASS")
