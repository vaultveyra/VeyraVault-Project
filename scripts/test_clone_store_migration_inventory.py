#!/usr/bin/env python3
"""Guard the legacy CloneStore schema while Room migration is being prepared."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
store = (root / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
doc = (root / "docs/STAGE_7_CLONE_PERSISTENCE_MIGRATION_PLAN.md").read_text(encoding="utf-8")

# Keep the existing preference namespace and every independent settings key.
for token in (
    '"veyravault_clones_v2"',
    '"clones_json"',
    '"collapsed_spaces"',
    '"master_mock_gps"',
    '"global_device_json"',
    '"active_launch_json"',
):
    assert token in store, "Legacy persistence contract missing: " + token

# Every existing clone field must remain represented in both JSON directions.
fields = {
    "pkg": "packageName",
    "uid": "userId",
    "name": "displayName",
    "gpsOn": "mockGpsEnabled",
    "lat": "latitude",
    "lng": "longitude",
    "locLabel": "locationLabel",
    "devOn": "customDeviceEnabled",
    "devBrand": "deviceBrand",
    "devModel": "deviceModel",
}
for key, field in fields.items():
    assert f'o.opt' in store and f'"{key}"' in store and field in store, (key, field)
    assert f'o.put("{key}",' in store and f'e.{field}' in store, "Write mapping missing: " + key

assert 'Object pkg = marker.opt("pkg")' in store
assert 'Object uid = marker.opt("uid")' in store
assert 'readLastActiveLaunchStrict' in store
assert 'return prefs(c).edit().putString(KEY_ACTIVE_LAUNCH, o.toString()).commit();' in store
assert 'Object denied = o.opt("denied")' in store
assert 'denied instanceof JSONArray' in store
assert 'o.put("denied", pArr)' in store
assert 'e.deniedPermissions.add((String) permission)' in store
assert 'readCollapsedSpaceNumbersStrict' in store
assert 'readMasterMockGpsEnabledStrict' in store
assert 'readGlobalEnvStrict' in store
assert 'return prefs(c).edit().putString(KEY_GLOBAL_DEV, o.toString()).commit();' in store

# Clone identity is a package + virtual-user pair, not package name alone.
assert 'cur.packageName.equals(entry.packageName) && cur.userId == entry.userId' in store
assert 'e.packageName.equals(pkg) && e.userId == userId' in store

# Guard all separate persistence categories and the last-successful-launch marker.
for method in (
    "isSpaceCollapsed", "setSpaceCollapsed",
    "isMasterMockGpsEnabled", "setMasterMockGpsEnabled",
    "getGlobalEnv", "saveGlobalEnv",
    "recordActiveLaunch", "getLastActiveLaunch",
):
    assert f" {method}(" in store, "Persistence API missing: " + method

# This stage must remain a plan: no Room cutover or legacy deletion.
for phrase in (
    "migration plan only",
    "sole source of truth",
    "virtual-app storage",
    "Malformed JSON",
    "rollback",
):
    assert phrase.lower() in doc.lower(), "Migration safety plan missing: " + phrase

print("CloneStore legacy schema inventory: PASS")
print("All clone fields and independent settings categories accounted for: PASS")
print("Composite clone identity contract: PASS")
print("Non-destructive migration/rollback plan: PASS")
