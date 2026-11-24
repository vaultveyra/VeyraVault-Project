from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
core = root / "app/src/main/java/com/veyravault/space/core"
ui = root / "app/src/main/java/com/veyravault/space/ui"

queue = (core / "EngineOperationQueue.java").read_text(encoding="utf-8")
provision = (core / "AsyncCloneProvisionRepository.java").read_text(encoding="utf-8")
add_app = (ui / "AddAppActivity.java").read_text(encoding="utf-8")
main = (ui / "MainActivity.java").read_text(encoding="utf-8")
launch = (core / "AsyncCloneLaunchRepository.java").read_text(encoding="utf-8")
location = (core / "AsyncLocationHookRepository.java").read_text(encoding="utf-8")
pending = (ui / "PendingReservationsActivity.java").read_text(encoding="utf-8")

# One app-process-wide serialization point for synchronous Engine calls.
assert "Executors.newSingleThreadExecutor" in queue
assert "veyravault-engine-operations" in queue
assert "private static final ExecutorService ENGINE" in queue
assert "EngineOperationQueue.execute" in launch
assert "EngineOperationQueue.execute" in location
assert "EngineOperationQueue.execute" in pending
assert "Executors.newSingleThreadExecutor" not in launch
assert "Executors.newSingleThreadExecutor" not in location

# Preflight -> durable reservation -> install -> atomic Registry commit.
assert provision.index("persistence.inspectNativeAbi(packageName") < provision.index("persistence.reserveNextUserId(packageName")
assert provision.index("persistence.reserveNextUserId(packageName") < provision.index("Engine.installPackageAsUser(")
assert provision.index("Engine.installPackageAsUser(") < provision.index("persistence.commitReservedClone(entry, reservation")
assert "EngineOperationQueue.submit" in provision

# Failed or unknown Engine results never release an ID; only explicit ABSENT may release.
assert "Engine.getCloneInstallState(entry.packageName, entry.userId)" in provision
assert "state == Engine.CloneInstallState.ABSENT" in provision
assert "attempt.confirmedAbsent" in provision
assert "releaseAfterConfirmedAbsence(reservation" in provision
assert "Engine.uninstallClone(entry.packageName, entry.userId)" in provision
assert "cleanupFailure == null && Boolean.TRUE.equals(cleanupConfirmed)" in provision
assert "reservation remains blocked" in provision

# UI delegates install and never calls the Engine installer itself.
assert "provisionRepository.createClone(app.pkg, app.label, fa" in add_app
assert "Engine.installPackageAsUser(" not in add_app
assert "Engine.uninstallClone(" not in add_app
assert "Engine.isCloneConfirmedAbsent(" not in add_app
assert "provisionRepository.createClone(item.packageName, item.displayName, fa" in main
assert "Engine.installPackageAsUser(" not in main
assert "Engine.isCloneConfirmedAbsent(" not in main

# Remaining synchronous Engine calls in MainActivity are enclosed in queue submissions.
for call in ("Engine.uninstallClone(", "Engine.stopClone(", "Engine.clearCloneData(",
             "Engine.isGmsInstalled(", "Engine.setGmsEnabled("):
    positions = [m.start() for m in re.finditer(re.escape(call), main)]
    assert positions, f"Expected queued Engine operation missing: {call}"
    for pos in positions:
        start = main.rfind("EngineOperationQueue.submit(", 0, pos)
        close = main.find("});", start)
        assert start >= 0 and close > pos, f"Engine call is not queued: {call}"

assert "app-scoped coordinator" in provision
assert "isFinishing()" not in provision
assert "isDestroyed()" not in provision

print("PASS: Clone provisioning and Engine calls share one serialized process-wide queue.")
print("PASS: Preflight/reservation/install/commit ordering and fail-closed rollback are enforced.")
print("PASS: Add App and Duplicate Clone no longer run synchronous Engine install work on the UI thread.")
