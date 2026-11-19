from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/SetLocationActivity.java").read_text(encoding="utf-8")
assert "AsyncCloneRepository.getInstance(getApplicationContext())" in source
assert "repository.saveCloneProfile(cloneEntry.packageName, cloneEntry.userId, updated" in source
assert "repository.clearCloneLocationOverrides(cloneEntry.packageName, cloneEntry.userId" in source
assert "repository.loadCloneProfile(cloneEntry.packageName, cloneEntry.userId" in source
assert "repository.loadGlobalProfile" in source
assert "ProfileResolver.resolve(" in source
assert "effective.locationEnabledSource" in source
assert "effective.latitudeSource" in source and "effective.longitudeSource" in source
assert "CloneStore.upsertClone" not in source
assert "upsertClone(cloneEntry" not in source
assert "cloneEntry.mockGpsEnabled =" not in source
assert "cloneEntry.latitude =" not in source
assert "cloneEntry.longitude =" not in source
assert "A valid target clone is required." in source
assert "Clone not found or stored data is unreadable." in source
assert "Engine result verified:" in source
assert "Profile saved, but engine application was not verified:" in source

save_start = source.index("repository.saveCloneProfile(")
save_success = source.index("if (!result.isSuccess())", save_start)
save_hook = source.index("VirtualHookManager.syncCloneHooks", save_success)
assert save_start < save_success < save_hook

reset_start = source.index("repository.clearCloneLocationOverrides(")
reset_success = source.index("if (!result.isSuccess())", reset_start)
reset_hook = source.index("VirtualHookManager.syncCloneHooks", reset_success)
assert reset_start < reset_success < reset_hook

store = Path("app/src/main/java/com/veyravault/space/core/ProfileStore.java").read_text(encoding="utf-8")
assert "clearCloneLocationOverrides(" in store
assert "KEY_LEGACY_LOCATION_CLEARED" in store
assert "legacyLocationCleared" in store
assert "KEY_LEGACY_LOCATION_CLEARED" in store[store.index("migrateLegacyLocationSettings"):]

repository = Path("app/src/main/java/com/veyravault/space/core/AsyncCloneRepository.java").read_text(encoding="utf-8")
assert "clearCloneLocationOverrides(" in repository

print("PASS: Clone location UI uses isolated profile persistence, field-source resolution, and explicit reset-to-Global tombstone.")
