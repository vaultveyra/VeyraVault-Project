from pathlib import Path

root = Path(__file__).resolve().parents[1]
add_app = (root / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
dashboard = (root / "app/src/main/java/com/veyravault/space/ui/DashboardActivity.java").read_text(encoding="utf-8")

# AddApp delegates provisioning to the application-scoped transaction coordinator.
for forbidden in ("CloneStore.nextFreeUserIdForPackage(", "CloneStore.upsertClone(", "CloneStore.getAll(",
                  "repository.allocateNextUserId", "repository.upsertClone(entry",
                  "Engine.installPackageAsUser(", "Engine.uninstallClone(", "Engine.isCloneConfirmedAbsent("):
    assert forbidden not in add_app, f"Unsafe/direct operation remains in AddAppActivity: {forbidden}"
assert "provisionRepository.createClone(app.pkg, app.label, fa" in add_app

# Dashboard counts use a strict async snapshot and fail visibly when the registry cannot be read.
assert "CloneStore.getAll(" not in dashboard
assert "AsyncCloneRepository.getInstance(getApplicationContext()).loadClones(" in dashboard
assert "if (!result.isSuccess() || result.getValue() == null)" in dashboard
assert "counts are unavailable" in dashboard
assert "cloneCount.setText(String.valueOf(result.getValue().size()))" in dashboard
assert "spaceCount.setText(String.valueOf(spaces.size()))" in dashboard

print("PASS: AddApp delegates Clone creation to the application-scoped Engine transaction coordinator.")
print("PASS: Dashboard counts use strict async registry reads.")
