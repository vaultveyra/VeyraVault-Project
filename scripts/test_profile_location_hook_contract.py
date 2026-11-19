from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/core/VirtualHookManager.java").read_text(encoding="utf-8")
assert "enum LocationStatus { APPLIED, DISABLED, UNSUPPORTED, FAILED }" in source
assert "class SyncSummary" in source
assert "syncAllClones(Context context)" in source
assert "CloneStore.readAllStrict(context)" in source
assert "ProfileStore.resolveStrict(context, entry.packageName, entry.userId" in source
assert "CloneStore.readMasterMockGpsEnabledStrict(context)" in source
assert "if (!masterEnabled)" in source
assert "Boolean.TRUE.equals(resolved.locationEnabled)" in source
assert "resolved.latitude == null || resolved.longitude == null" in source
assert "top.niunaijun.blackbox.fake.frameworks.BLocationManager" in source
assert 'managerClass.getMethod("getService")' in source
assert '"setLocation"' in source and '"setPattern"' in source
assert '"getPattern"' in source and '"getLocation"' in source
assert '"getLatitude"' in source and '"getLongitude"' in source
assert "LOCATION_ENABLE_READBACK_MISMATCH" in source
assert "LOCATION_COORDINATE_READBACK_MISMATCH" in source
assert "failClosedAfterEnableFailure" in source
assert "entry.mockGpsEnabled" not in source
assert "entry.latitude" not in source
assert "entry.longitude" not in source
assert "catch (Throwable ignored)" not in source

store = Path("app/src/main/java/com/veyravault/space/core/ProfileStore.java").read_text(encoding="utf-8")
assert "clearCloneLocationOverrides(" in store
assert "legacyLocationCleared" in store
assert "legacyLocationCleared is invalid" in store
assert "Boolean.TRUE.equals(tombstone)" in store
assert "out.remove(KEY_LEGACY_LOCATION_CLEARED)" in store
assert "saveGlobalLocationOverrides(" in store
assert "clearGlobalLocationOverrides(" in store

repository = Path("app/src/main/java/com/veyravault/space/core/AsyncCloneRepository.java").read_text(encoding="utf-8")
assert "clearCloneLocationOverrides(" in repository
assert "saveGlobalLocationProfile(" in repository
assert "clearGlobalLocationOverrides(" in repository
hook_repository = Path("app/src/main/java/com/veyravault/space/core/AsyncLocationHookRepository.java").read_text(encoding="utf-8")
assert "syncCloneLocationHook(" in hook_repository
assert "syncAllCloneLocationHooks(" in hook_repository
assert "CloneStore.readAllStrict(appContext)" in hook_repository

print("PASS: Location hook resolves strict profiles, honors Master GPS, verifies pinned-engine readback, and preserves explicit inheritance resets.")
