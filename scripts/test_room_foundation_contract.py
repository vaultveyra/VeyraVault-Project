#!/usr/bin/env python3
"""Guard the inactive Room foundation and the legacy persistence cutover boundary."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
java_root = root / "app/src/main/java"
room_root = java_root / "com/veyravault/space/core/persistence"
prepare = (root / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
clone_store = (java_root / "com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")

assert "androidx.room:room-runtime:2.6.1" in prepare
assert "androidx.room:room-compiler:2.6.1" in prepare
assert "annotationProcessor" in prepare
assert '"room.schemaLocation": "$projectDir/schemas".toString()' in prepare

expected = {
    "CloneEntity.java", "DeniedPermissionEntity.java", "CollapsedSpaceEntity.java",
    "GlobalDeviceProfileEntity.java", "PersistenceSettingsEntity.java",
    "LastActiveLaunchEntity.java", "CloneDao.java", "DeniedPermissionDao.java",
    "CollapsedSpaceDao.java", "GlobalDeviceProfileDao.java",
    "PersistenceSettingsDao.java", "LastActiveLaunchDao.java",
    "ClonePersistenceDatabase.java", "ClonePersistenceDatabaseProvider.java",
}
present = {p.name for p in room_root.glob("*.java")}
assert expected <= present, "Room foundation files missing: " + repr(sorted(expected - present))

# The old store remains the runtime source of truth in this stage.
assert 'getSharedPreferences(PREF, Context.MODE_PRIVATE)' in clone_store
assert "ClonePersistenceDatabaseProvider.get(" not in clone_store
assert "ClonePersistenceDatabaseProvider.get(" not in (
    java_root / "com/veyravault/space/VaultApp.java"
).read_text(encoding="utf-8")

# No destructive fallback and no main-thread query opt-in anywhere in persistence package.
for path in room_root.glob("*.java"):
    source = path.read_text(encoding="utf-8")
    assert "fallbackToDestructiveMigration" not in source, path.name
    assert "allowMainThreadQueries" not in source, path.name

# The collapsed-space key remains a String to preserve its exact legacy representation.
collapsed = (room_root / "CollapsedSpaceEntity.java").read_text(encoding="utf-8")
assert "@NonNull @PrimaryKey public String spaceKey" in collapsed

# The last-launch marker intentionally has no FK to clones, preserving stale legacy markers.
active = (room_root / "LastActiveLaunchEntity.java").read_text(encoding="utf-8")
assert "no FK" in active

database = (room_root / "ClonePersistenceDatabase.java").read_text(encoding="utf-8")
assert "exportSchema = true" in database
assert (root / "app/schemas/README.md").is_file()

print("Room 2.6.1 generated Gradle dependency contract: PASS")
print("Room entities, DAOs and database schema inventory: PASS")
print("Legacy CloneStore remains the only active persistence path: PASS")
print("No destructive migration or main-thread query escape hatch: PASS")
print("Legacy collapsed-key and stale active-marker semantics preserved: PASS")
print("Versioned Room schema export configuration: PASS")
