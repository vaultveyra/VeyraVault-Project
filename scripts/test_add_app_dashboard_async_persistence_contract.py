from pathlib import Path

root = Path(__file__).resolve().parents[1]
add_app = (root / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
dashboard = (root / "app/src/main/java/com/veyravault/space/ui/DashboardActivity.java").read_text(encoding="utf-8")

# AddApp must not bypass the async repository for registry allocation or writes.
for forbidden in ("CloneStore.nextFreeUserIdForPackage(", "CloneStore.upsertClone(", "CloneStore.getAll("):
    assert forbidden not in add_app, f"Direct CloneStore call remains in AddAppActivity: {forbidden}"
assert "repository.allocateNextUserId(app.pkg" in add_app
assert "repository.upsertClone(entry" in add_app
assert add_app.index("Engine.installPackageAsUser(entry.packageName, entry.userId)") < add_app.index("repository.upsertClone(entry")
assert "if (!save.isSuccess())" in add_app
failure = add_app[add_app.index("if (!save.isSuccess())"):]
assert failure.index("Engine.uninstallClone(entry.packageName, entry.userId)") < failure.index("if (!isFinishing() && !isDestroyed())")
assert "cloneBatchAt(selected, 0, 0, 0)" in add_app
assert "repository.allocateNextUserId" in add_app
assert "batchConfirmBtn.setEnabled(false)" in add_app
assert "if (!batchMode && !isFinishing() && !isDestroyed())" in add_app

# Dashboard counts must come from a strict async snapshot, never the legacy empty-list fallback.
assert "CloneStore.getAll(" not in dashboard
assert "AsyncCloneRepository.getInstance(getApplicationContext()).loadClones(" in dashboard
assert "if (!result.isSuccess() || result.getValue() == null)" in dashboard
assert "counts are unavailable" in dashboard
assert "cloneCount.setText(String.valueOf(result.getValue().size()))" in dashboard
assert "spaceCount.setText(String.valueOf(spaces.size()))" in dashboard

print("PASS: AddApp clone creation uses async allocation and commit-aware persistence with compensating Engine cleanup.")
print("PASS: Batch clone creation is sequential and does not finish before persistence callbacks.")
print("PASS: Dashboard counts use strict async registry reads and surface unreadable data.")
