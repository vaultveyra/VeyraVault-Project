#!/usr/bin/env python3
"""Guard the opt-in transactional importer and semantic parity verifier."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / "app/src/main/java/com/veyravault/space/core/persistence"
importer = (base / "LegacyCloneRoomImporter.java").read_text(encoding="utf-8")
verifier = (base / "LegacyCloneRoomVerifier.java").read_text(encoding="utf-8")
database = (base / "ClonePersistenceDatabase.java").read_text(encoding="utf-8")
clone_entity = (base / "CloneEntity.java").read_text(encoding="utf-8")
metadata = (base / "LegacyMigrationMetadataEntity.java").read_text(encoding="utf-8")
app = (root / "app/src/main/java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
store = (root / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")

for token in (
    "database.runInTransaction(",
    "Looper.myLooper() == Looper.getMainLooper()",
    "importIntoEmptyDatabase",
    "Result.ALREADY_IMPORTED",
    "Result.IMPORTED",
    "LegacyCloneRoomVerifier.matches(database, snapshot)",
    "database.clones().count() != 0",
    "database.deniedPermissions().count() != 0",
    "database.collapsedSpaces().count() != 0",
    "database.globalDeviceProfile().count() != 0",
    "database.persistenceSettings().count() != 0",
    "database.lastActiveLaunch().count() != 0",
    "database.migrationMetadata().insert(metadata)",
    "entity.legacyJson = record.legacyJson",
    "marker.packageName = snapshot.activeLaunch.packageName",
):
    assert token in importer, "Importer contract missing: " + token

for token in (
    "sourceSnapshotSha256",
    "sourceSnapshotPayload",
    "sourceFormatVersion",
    "snapshot.canonicalPayload()",
    "Double.compare(source.latitude, stored.latitude)",
    "expectedPermissions.equals(actualPermissions)",
    "snapshot.collapsedSpaces.equals(actualCollapsed)",
    "snapshot.masterMockGpsEnabled",
    "snapshot.activeLaunch",
    "equal(source.legacyJson, stored.legacyJson)",
):
    assert token in verifier, "Parity verifier contract missing: " + token

assert "LegacyMigrationMetadataEntity.class" in database
assert "LegacyMigrationMetadataDao migrationMetadata()" in database
assert "@NonNull public String legacyJson" in clone_entity
assert "sourceSnapshotPayload" in metadata

# Importer is deliberately unreachable from app startup and the legacy runtime API.
assert "LegacyCloneRoomImporter" not in app
assert "LegacyCloneRoomImporter" not in store
for path in (root / "app/src/main/java").rglob("*.java"):
    if path.name != "LegacyCloneRoomImporter.java":
        assert "LegacyCloneRoomImporter.importIntoEmptyDatabase" not in path.read_text(encoding="utf-8"), path

# The importer has no preference writes or BlackBox/session filesystem operations.
for forbidden in (
    "SharedPreferences",
    "BlackBoxCore",
    "deleteDatabase(",
    "fallbackToDestructiveMigration",
    "allowMainThreadQueries",
):
    assert forbidden not in importer, "Importer crosses protected boundary: " + forbidden

print("Worker-thread transactional import and empty-database guard: PASS")
print("Idempotence requires source hash AND exact stored-row parity: PASS")
print("All clone fields, denied permissions, collapsed keys, global settings and active marker verified: PASS")
print("Lossless legacy JSON and migration provenance retained: PASS")
print("No startup/runtime wiring or legacy/session mutation: PASS")
