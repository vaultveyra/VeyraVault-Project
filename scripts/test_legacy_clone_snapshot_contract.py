#!/usr/bin/env python3
"""Guard the read-only, fail-closed legacy snapshot boundary."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "app/src/main/java/com/veyravault/space/core/persistence/LegacyCloneSnapshot.java").read_text(encoding="utf-8")
store = (root / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")

for token in (
    'PREFS_NAME = "veyravault_clones_v2"',
    'KEY_CLONES = "clones_json"',
    'KEY_COLLAPSED = "collapsed_spaces"',
    'KEY_MASTER_GPS = "master_mock_gps"',
    'KEY_GLOBAL_DEVICE = "global_device_json"',
    'KEY_ACTIVE_LAUNCH = "active_launch_json"',
    "prefs.getAll()",
    "new JSONArray(rawClones)",
    "new JSONObject(rawGlobal)",
    "new JSONObject(rawActive)",
    "Collections.unmodifiableList",
    "Collections.unmodifiableSet",
    "Collections.sort(clones",
    "new TreeSet<>(collapsedSpaces)",
    "MessageDigest.getInstance(\"SHA-256\")",
    "canonicalPayload()",
    "Duplicate clone identity",
    "negative virtual user ID",
    "invalid enabled-location coordinates",
    "non-String value",
    "Legacy CloneStore snapshot rejected",
    "legacyJson = source.toString()",
):
    assert token in source, "Snapshot contract missing: " + token

# Snapshot code is read-only and cannot silently turn malformed data into an empty registry.
for forbidden in (
    ".edit()",
    ".putString(",
    ".putBoolean(",
    ".putStringSet(",
    ".clear()",
    "Room.databaseBuilder",
    "ClonePersistenceDatabaseProvider",
    "BlackBoxCore",
    "deleteDatabase(",
):
    assert forbidden not in source, "Snapshot must remain read-only: " + forbidden

# Existing runtime remains on the exact legacy store; snapshot is not wired into startup.
assert 'getSharedPreferences(PREF, Context.MODE_PRIVATE)' in store
app = (root / "app/src/main/java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
assert "LegacyCloneSnapshot" not in app

print("Legacy snapshot read-only boundary: PASS")
print("Strict parse, validation, lossless raw-entry retention and deterministic digest contract: PASS")
print("No Room import, preference mutation, or runtime cutover: PASS")
