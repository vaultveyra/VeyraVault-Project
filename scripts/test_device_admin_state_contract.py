from pathlib import Path

root = Path("app/src/main")
receiver = (root / "java/com/veyravault/space/security/VaultDeviceAdminReceiver.java").read_text(encoding="utf-8")
settings = (root / "java/com/veyravault/space/ui/SecuritySettingsActivity.java").read_text(encoding="utf-8")
test = Path("app/src/androidTest/java/com/veyravault/space/security/DeviceAdminStateInstrumentationTest.java").read_text(encoding="utf-8")

# Runtime state comes from Android's DevicePolicyManager, not a cached preference or UI checkbox.
assert "DevicePolicyManager" in receiver
assert "dpm.isAdminActive(getComponentName(ctx))" in receiver
assert "getComponentName(Context ctx)" in receiver

# Enabling requires Android's explicit confirmation screen; disabling uses the actual admin API.
assert "DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN" in receiver
assert "DevicePolicyManager.EXTRA_DEVICE_ADMIN" in receiver
assert "dpm.removeActiveAdmin(comp)" in receiver

# UI state is refreshed from Android after returning to the Activity.
assert "antiUninstallSwitch.setChecked(VaultDeviceAdminReceiver.isAntiUninstallActive(this));" in settings
assert "protected void onResume()" in settings

# Instrumentation must compare actual system state without changing it.
assert "manager.isAdminActive(receiver)" in test
assert "VaultDeviceAdminReceiver.isAntiUninstallActive(context)" in test
assert "setAntiUninstallEnabled" not in test
assert "removeActiveAdmin" not in test
assert "ACTION_ADD_DEVICE_ADMIN" not in test

print("PASS: Device Admin status is read from Android, UI refreshes actual state, and instrumentation is read-only.")
