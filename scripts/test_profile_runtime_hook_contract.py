#!/usr/bin/env python3
"""Guard the per-clone locale/time-zone runtime integration boundary."""
from pathlib import Path

root = Path("app/src/main/java/com/veyravault/space")
engine = (root / "core/Engine.java").read_text(encoding="utf-8")
vault = (root / "VaultApp.java").read_text(encoding="utf-8")
store = (root / "core/ProfileStore.java").read_text(encoding="utf-8")
callback = (root / "core/CloneProfileLifecycleCallback.java").read_text(encoding="utf-8")
applier = (root / "core/ProfileRuntimeApplier.java").read_text(encoding="utf-8")
client = (root / "core/ProfileRuntimeClient.java").read_text(encoding="utf-8")
provider = (root / "core/ProfileRuntimeProvider.java").read_text(encoding="utf-8")
process = (root / "core/ProcessUtils.java").read_text(encoding="utf-8")
manifest = Path("app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")

assert "registerCloneProfileLifecycleCallback(this)" in vault
assert vault.index("ProfileStore.migrateLegacyLocationSettings(this)") < vault.index(
    "Engine.registerCloneProfileLifecycleCallback(this)"
)
assert "addAppLifecycleCallback" in engine
assert "AppLifecycleCallback" in engine
assert "beforeCreateApplication" in callback
assert "ProfileRuntimeClient.resolve" in callback
assert "ProfileStore.resolveStrict" not in callback
assert "ContentResolver().call" in client
assert "ProfileStore.readCloneOverrideStrict" in provider
assert "ProfileStore.readGlobalStrict" in provider
assert 'android:exported="false"' in manifest
assert 'android:authorities="${applicationId}.profile-runtime"' in manifest
assert "Binder.getCallingUid() != Process.myUid()" in provider
assert "ProcessUtils.isMainProcess(this)" in vault
assert "ProfileStore.migrateLegacyLocationSettings(this)" in vault
assert "Application.getProcessName()" in process
assert "ActivityManager.getRunningAppProcesses" in process
assert "ProfileRuntimeApplier.initializeSystemFallback(this)" in vault
assert "ProfileRuntimeApplier.restoreSystemDefaults(packageContext)" in callback
assert "packageName.equals(appContext.getPackageName())" in callback
assert "Resources.getSystem().getConfiguration().locale" in applier
assert "ContentResolver().call" in client
assert "Locale.setDefault(locale)" in applier
assert "TimeZone.setDefault(TimeZone.getTimeZone(profile.timeZoneId))" in applier
assert "systemTimeZoneId" in applier
assert "Intent.ACTION_TIMEZONE_CHANGED" in applier
assert "lastAppliedSystemTimeZone" in applier
assert "nextCloneSystemFallbackDoesNotInheritPreviousCloneTimeZone" in (
    Path("app/src/androidTest/java/com/veyravault/space/core/ProfileRuntimeApplierInstrumentationTest.java")
    .read_text(encoding="utf-8")
)
assert "Resources resources = packageContext.getResources()" in applier
assert "resources.updateConfiguration(configuration, resources.getDisplayMetrics())" in applier
assert "readCloneOverrideStrict(context, packageName, userId)" in store
assert "readGlobalStrict(context)" in store

# Locale/time-zone changes must not mutate the host process from the launch screen.
assert "Locale.setDefault" not in engine
assert "TimeZone.setDefault" not in engine

print("Clone lifecycle callback registration contract: PASS")
print("Pre-Application package/user profile resolution contract: PASS")
print("Process-scoped locale/time-zone application contract: PASS")
