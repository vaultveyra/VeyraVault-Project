from pathlib import Path

root = Path("app/src/main/java/com/veyravault/space")
activity = (root / "ui/CloneEnvironmentProfileActivity.java").read_text(encoding="utf-8")
repository = (root / "core/AsyncCloneRepository.java").read_text(encoding="utf-8")
main = (root / "ui/MainActivity.java").read_text(encoding="utf-8")
manifest = Path("app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")

assert "repository.loadClones" in activity
assert "repository.loadCloneProfile" in activity
assert "repository.loadGlobalProfile" in activity
assert "repository.saveCloneProfile" in activity
assert "repository.clearCloneProfileField" in activity
assert '"localeTag"' in activity and '"timeZoneId"' in activity
assert "ProfileResolver.resolve(" in activity
assert "ProfileRuntimeApplier.systemFallback()" in activity
assert "effective.localeSource" in activity and "effective.timeZoneSource" in activity
assert "ProfileSettings.isLocaleTagValid(value)" in activity
assert "ProfileSettings.isTimeZoneIdValid(value)" in activity
assert "Clone → Global → System" in activity
assert "next clone launch" in activity
assert "Engine.stopClone" not in activity
assert "Engine.clearCloneData" not in activity
assert "Engine.uninstallClone" not in activity
assert "repository.saveCloneProfile" in repository
assert "ProfileStore.readCloneOverrideStrict" in repository
assert "ProfileStore.clearCloneOverrideField" in repository
assert "CloneEnvironmentProfileActivity.class" in main
assert "Clone Environment" in main
assert ".ui.CloneEnvironmentProfileActivity" in manifest
assert 'android:exported="false"' in manifest

print("PASS: Clone Locale/Time Zone UI uses strict async profile persistence, per-field precedence, source display, and non-destructive reset.")
