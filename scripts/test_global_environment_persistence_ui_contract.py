from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/GlobalEnvironmentActivity.java").read_text(encoding="utf-8")

assert "AsyncCloneRepository.getInstance(getApplicationContext())" in source
assert "repository.loadGlobalEnvironment" in source
assert "repository.loadMasterMockGpsEnabled" in source
assert "repository.saveGlobalEnvironment" in source
assert "repository.setMasterMockGpsEnabled" in source
assert "CloneStore.getGlobalEnv" not in source
assert "CloneStore.isMasterMockGpsEnabled" not in source
assert "CloneStore.saveGlobalEnv" not in source
assert "CloneStore.setMasterMockGpsEnabled" not in source
assert "CloneStore.syncAllHooks" not in source
assert "VirtualHookManager.syncAllHooks(getApplicationContext())" in source
assert "profileLoaded && masterGpsLoaded && !loadFailed" in source

profile_save = source.index("repository.saveGlobalEnvironment(updated, profileResult ->")
profile_success = source.index("if (!profileResult.isSuccess())", profile_save)
gps_save = source.index("repository.setMasterMockGpsEnabled(masterGpsEnabled, gpsResult ->", profile_success)
gps_failure = source.index("if (!gpsResult.isSuccess())", gps_save)
sync = source.index("VirtualHookManager.syncAllHooks(getApplicationContext())", gps_failure)
assert profile_save < profile_success < gps_save < gps_failure < sync

partial_failure = source[gps_failure:sync]
assert "Profile was saved, but Master GPS was not" in partial_failure
assert "Hook synchronization was not run" in partial_failure
assert "Profile and Master GPS were saved" in source
assert "setControlsEnabled(false)" in source

print("PASS: GlobalEnvironmentActivity loads and saves settings asynchronously, reports partial commits, and syncs hooks only after both commits succeed.")
