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

# The pinned engine exposes a package/user-scoped service. The adapter calls
# the service proxy directly so RemoteException is not swallowed by BLocationManager's
# convenience wrappers, then verifies the stored pattern and coordinates.
assert "top.niunaijun.blackbox.fake.frameworks.BLocationManager" in hooks
assert 'managerClass.getMethod("getService")' in hooks
location_method = hooks.split("private static LocationApplyResult applyEngineLocationHook", 1)[1]
set_location = location_method.index('invoke(service, "setLocation"')
set_pattern = location_method.index('invoke(service, "setPattern"')
assert set_location < set_pattern
assert '"getPattern"' in location_method
assert '"getLocation"' in location_method
assert '"getLatitude"' in location_method
assert '"getLongitude"' in location_method
assert "failClosedAfterEnableFailure" in location_method
assert "catch (Throwable ignored)" not in hooks

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
