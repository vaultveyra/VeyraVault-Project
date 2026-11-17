#!/usr/bin/env python3
"""Regression checks that clone hooks stay inside the virtualization engine scope."""
from pathlib import Path

hooks = Path("app/src/main/java/com/veyravault/space/core/VirtualHookManager.java").read_text(encoding="utf-8")
store = Path("app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
global_ui = Path("app/src/main/java/com/veyravault/space/ui/GlobalEnvironmentActivity.java").read_text(encoding="utf-8")
main_ui = Path("app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")

# Host-process global mutation is not a valid per-clone hook channel.
for forbidden in (
    "android.os.Build",
    "import android.location.LocationManager;",
    "LocationManager.class",
    "mService",
    "activeMockGps",
    "activeLat",
    "activeLng",
    "BDeviceManager",
    "BDeviceConfig",
    "setStaticField",
):
    assert forbidden not in hooks, "Unexpected host/global hook remains: " + forbidden

# The pinned engine's location service accepts package + virtual-user scoped settings.
location_method = hooks.split("public static void applyEngineLocationHook", 1)[1]
assert 'm.getName().equals("setPattern")' in location_method
assert "m.invoke(mgr, userId, pkg, enable ? 2 : 0)" in location_method
assert 'm.getName().equals("setLocation")' in location_method
assert "m.invoke(mgr, userId, pkg, bLoc)" in location_method

# Startup synchronization must not attempt to apply unsupported device-profile APIs.
sync_method = store.split("public static void syncAllHooks", 1)[1]
assert "VirtualHookManager.syncCloneHooks(c, e)" in sync_method
assert "applyDeviceProperties" not in store

# UI must not claim that the unsupported device/SIM metadata is applied to clones.
assert "Metadata Only" in global_ui
assert "not applied" in global_ui
assert "Profile metadata saved" in main_ui
assert "Saved profile:" in main_ui

print("Host-global hook isolation contract: PASS")
print("Package/user-scoped engine location contract: PASS")
print("Device/SIM profile metadata disclosure contract: PASS")
