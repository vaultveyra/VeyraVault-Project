#!/usr/bin/env python3
"""Guard the per-clone locale/time-zone runtime integration boundary."""
from pathlib import Path

root = Path("app/src/main/java/com/veyravault/space")
engine = (root / "core/Engine.java").read_text(encoding="utf-8")
vault = (root / "VaultApp.java").read_text(encoding="utf-8")
store = (root / "core/ProfileStore.java").read_text(encoding="utf-8")
callback = (root / "core/CloneProfileLifecycleCallback.java").read_text(encoding="utf-8")
applier = (root / "core/ProfileRuntimeApplier.java").read_text(encoding="utf-8")

assert "registerCloneProfileLifecycleCallback(this)" in vault
assert vault.index("ProfileStore.migrateLegacyLocationSettings(this)") < vault.index(
    "Engine.registerCloneProfileLifecycleCallback(this)"
)
assert "addAppLifecycleCallback" in engine
assert "AppLifecycleCallback" in engine
assert "beforeCreateApplication" in callback
assert "ProfileStore.resolveStrict" in callback
assert "packageName.equals(appContext.getPackageName())" in callback
assert "Resources.getSystem().getConfiguration().locale" in applier
assert "Locale.setDefault(locale)" in applier
assert "TimeZone.setDefault(TimeZone.getTimeZone(profile.timeZoneId))" in applier
assert "packageContext.getResources().updateConfiguration" in applier
assert "readCloneOverrideStrict(context, packageName, userId)" in store
assert "readGlobalStrict(context)" in store

# Locale/time-zone changes must not mutate the host process from the launch screen.
assert "Locale.setDefault" not in engine
assert "TimeZone.setDefault" not in engine

print("Clone lifecycle callback registration contract: PASS")
print("Pre-Application package/user profile resolution contract: PASS")
print("Process-scoped locale/time-zone application contract: PASS")
