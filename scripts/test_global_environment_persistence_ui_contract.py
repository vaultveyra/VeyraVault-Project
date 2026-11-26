from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/GlobalEnvironmentActivity.java").read_text(encoding="utf-8")

assert "AsyncCloneRepository.getInstance(getApplicationContext())" in source
assert "repository.loadGlobalEnvironment" in source
assert "repository.loadGlobalProfile" in source
assert "repository.loadMasterMockGpsEnabled" in source
assert "repository.saveGlobalEnvironment" in source
assert "repository.saveGlobalLocationProfile" in source
assert "repository.clearGlobalLocationOverrides" in source
assert "repository.setMasterMockGpsEnabled" in source
assert "CloneStore.getGlobalEnv" not in source
assert "CloneStore.isMasterMockGpsEnabled" not in source
assert "CloneStore.saveGlobalEnv" not in source
assert "CloneStore.setMasterMockGpsEnabled" not in source
assert "hookRepository.syncAllCloneLocationHooks((summary, error) ->" in source
assert "formatSyncSummary(summary)" in source
assert "summary.registryReadable" in source
assert "summary.unsupported" in source and "summary.failed" in source
assert "profileLoaded && locationProfileLoaded && masterGpsLoaded && !loadFailed" in source
assert "Both global coordinates are required when global location is enabled." in source
assert "parseOptionalCoordinate" in source
assert "Clear Global location defaults (inherit Safe Isolated Default)" in source
assert "Inherit Safe Isolated Default (no Global override)" in source
assert "globalProfile.locationEnabled == null" in source
assert "globalLocationInherit.isChecked()" in source
assert "Boolean.TRUE.equals(locationEnabled)" in source

profile_save = source.index("repository.saveGlobalEnvironment(updated, profileResult ->")
profile_success = source.index("if (!profileResult.isSuccess())", profile_save)
location_save = source.index("repository.saveGlobalLocationProfile(locationEnabled, latitude, longitude", profile_success)
location_failure = source.index("if (!locationResult.isSuccess())", location_save)
gps_save = source.index("repository.setMasterMockGpsEnabled(masterGpsEnabled, gpsResult ->", location_failure)
gps_failure = source.index("if (!gpsResult.isSuccess())", gps_save)
sync = source.index("hookRepository.syncAllCloneLocationHooks((summary, error) ->", gps_failure)
assert profile_save < profile_success < location_save < location_failure < gps_save < gps_failure < sync

location_partial_failure = source[location_failure:gps_save]
assert "Device metadata was saved, but Global location profile was not" in location_partial_failure
gps_partial_failure = source[gps_failure:sync]
assert "Master GPS was not" in gps_partial_failure
assert "hooks were not synchronized" in gps_partial_failure
assert "setControlsEnabled(false)" in source

profile_store = Path("app/src/main/java/com/veyravault/space/core/ProfileStore.java").read_text(encoding="utf-8")
repository = Path("app/src/main/java/com/veyravault/space/core/AsyncCloneRepository.java").read_text(encoding="utf-8")

# Global Locale/Time Zone defaults are independent profile fields, not device or GPS metadata.
for marker in (
    "buildGlobalLocaleTimeZoneSection()",
    "buildGlobalProfileField(true)",
    "buildGlobalProfileField(false)",
    "repository.saveGlobalProfile(update, result ->",
    "repository.clearGlobalProfileField(field, result ->",
    "ProfileResolver.resolve(",
    "ProfileRuntimeApplier.systemFallback()",
    "ProfileSettings.isLocaleTagValid(value)",
    "ProfileSettings.isTimeZoneIdValid(value)",
    "next clone launch",
    "Clone-specific values always take precedence",
    "Reset to Safe Default",
):
    assert marker in source, f"Missing Global Locale/Time Zone UI behavior: {marker}"

assert "repository.saveCloneProfile" not in source, "Global defaults UI must not write clone overrides"
assert "repository.clearCloneProfileField" not in source, "Global defaults UI must not clear clone overrides"
assert "repository.setMasterMockGpsEnabled" not in source[source.index("private void saveGlobalProfileField"):source.index("private void showGlobalProfilePresets")], \
    "Locale/Time Zone save must not change Master GPS"
assert "hookRepository.syncAllCloneLocationHooks" not in source[source.index("private void saveGlobalProfileField"):source.index("private void showGlobalProfilePresets")], \
    "Locale/Time Zone changes must not trigger location hook synchronization"

assert "ProfileStore.clearGlobalField(appContext, field)" in repository
assert 'return "localeTag".equals(field) || "timeZoneId".equals(field)' in repository
assert 'if (settings.localeTag != null) out.put("localeTag", settings.localeTag);' in profile_store
assert 'if (settings.timeZoneId != null) out.put("timeZoneId", settings.timeZoneId);' in profile_store
assert "public static synchronized boolean clearGlobalField" in profile_store
assert "if (settings.localeTag != null) out.put" in profile_store, \
    "Partial Global profile saves must preserve unspecified sibling fields"

print("PASS: Global metadata/location persistence remains safe; independent Global Locale/Time Zone defaults use validated async field-level save/reset and preserve clone overrides.")
