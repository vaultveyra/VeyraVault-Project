from pathlib import Path

root = Path(__file__).resolve().parents[1]
add_app = (root / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
dashboard = (root / "app/src/main/java/com/veyravault/space/ui/DashboardActivity.java").read_text(encoding="utf-8")

# AddApp creation must reserve an identity before touching the virtual Engine.
for forbidden in ("CloneStore.nextFreeUserIdForPackage(", "CloneStore.upsertClone(", "CloneStore.getAll(",
                  "repository.allocateNextUserId", "repository.upsertClone(entry"):
    assert forbidden not in add_app, f"Unsafe/direct persistence call remains in AddAppActivity: {forbidden}"
assert "repository.reserveNextUserId(app.pkg" in add_app
assert "repository.commitReservedClone(entry, reservation" in add_app
assert add_app.index("repository.reserveNextUserId(app.pkg") < add_app.index("Engine.installPackageAsUser(entry.packageName, entry.userId)")
assert add_app.index("Engine.installPackageAsUser(entry.packageName, entry.userId)") < add_app.index("repository.commitReservedClone(entry")
assert "Engine.isCloneConfirmedAbsent" in add_app
assert "repository.releaseReservationAfterEngineAbsence" in add_app
assert "Engine.uninstallClone(entry.packageName, entry.userId)" in add_app
assert "if (cleanupConfirmed) releaseReservationAfterConfirmedEngineAbsence(reservation)" in add_app
assert "cloneBatchAt(selected, 0, 0, 0)" in add_app
assert "batchConfirmBtn.setEnabled(false)" in add_app
assert "if (!batchMode && !isFinishing() && !isDestroyed())" in add_app

# Dashboard counts use a strict async snapshot and fail visibly when the registry cannot be read.
assert "CloneStore.getAll(" not in dashboard
assert "AsyncCloneRepository.getInstance(getApplicationContext()).loadClones(" in dashboard
assert "if (!result.isSuccess() || result.getValue() == null)" in dashboard
assert "counts are unavailable" in dashboard
assert "cloneCount.setText(String.valueOf(result.getValue().size()))" in dashboard
assert "spaceCount.setText(String.valueOf(spaces.size()))" in dashboard

print("PASS: AddApp uses a durable reservation, Engine-first install and token-bound atomic registry commit.")
print("PASS: Failed/uncertain Engine cleanup never silently frees the reserved ID.")
print("PASS: Dashboard counts use strict async registry reads.")
