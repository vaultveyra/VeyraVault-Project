#!/usr/bin/env python3
"""Static contract for Stage 8.10's per-app diagnostic scope and safe launch guard."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
engine = (root / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
compatibility = (root / "app/src/main/java/com/veyravault/space/core/CompatibilityManager.java").read_text(encoding="utf-8")
doc = (root / "docs/STAGE_8_10_APP_COMPATIBILITY_DIAGNOSTICS.md").read_text(encoding="utf-8")

launch_start = engine.index("public static CloneLaunchResult launchCloneDetailed(")
launch_brace = engine.index("{", launch_start)
depth = 0
for i in range(launch_brace, len(engine)):
    if engine[i] == "{":
        depth += 1
    elif engine[i] == "}":
        depth -= 1
        if depth == 0:
            launch = engine[launch_brace + 1:i]
            break
else:
    raise AssertionError("Unclosed launchCloneDetailed method")

unknown = launch.index("installState == null || installState == CloneInstallState.UNKNOWN")
absent = launch.index("installState == CloneInstallState.ABSENT")
install = launch.index("installPackageAsUser(entry.packageName, entry.userId)")
hook = launch.index("VirtualHookManager.syncCloneHooks(ctx, entry)")
engine_launch = launch.index('getMethod("launchApk", String.class, int.class)')
persist = launch.index("CloneStore.recordActiveLaunch(ctx, entry)")

assert unknown < absent < install < hook < engine_launch < persist
assert 'new CloneLaunchResult(false, "ENGINE_INSTALL_STATE_UNKNOWN", null)' in launch
assert "isInstalledAsUser(" not in launch

# The current report's labels must remain explicitly host-scoped.
assert "native libraries detected in the host app directory" in compatibility
assert "Engine core is discoverable" in compatibility or "Virtualization engine core is discoverable" in compatibility
assert "host" in compatibility.lower()
assert "sourceDir" in doc and "splitSourceDirs" in doc
assert "89b59836c66f173756a4ae258cf379a957649820" in doc
assert "Chrome" in doc and "Instagram" in doc and "Soroush" in doc
assert "not proof" in doc.lower()
assert "physical-device reproduction" in doc.lower()

print("Stage 8.10: UNKNOWN install state fails closed without triggering install: PASS")
print("Stage 8.10: explicit ABSENT is the only launch-time install trigger: PASS")
print("Stage 8.10: hook, Engine launch and active-launch persistence ordering preserved: PASS")
print("Stage 8.10: host-only compatibility scope and per-app evidence boundary documented: PASS")
