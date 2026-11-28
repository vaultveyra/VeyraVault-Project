from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
provision = Path("app/src/main/java/com/veyravault/space/core/AsyncCloneProvisionRepository.java").read_text(encoding="utf-8")

# Preserve app discovery, filtering, single clone and batch clone flows.
for marker in ("loadInstalledApps();", "renderGrid(currentQuery);", "PackageManager pm = getPackageManager();",
               "queryIntentActivities(main, 0)", "cloneSingleApp(app,", "cloneBatchAt(selected, 0, 0, 0)",
               "provisionRepository.createClone(app.pkg, app.label, fa"):
    assert marker in source, f"Existing Add App behavior missing: {marker}"

# The transaction service owns the durable reservation and Engine-first commit protocol.
assert "persistence.reserveNextUserId(packageName" in provision
assert "persistence.commitReservedClone(entry, reservation" in provision
assert provision.index("persistence.reserveNextUserId(packageName") < provision.index("Engine.installPackageAsUser(")
assert provision.index("Engine.installPackageAsUser(") < provision.index("persistence.commitReservedClone(entry, reservation")

# Selection grid is responsive in density-independent units and less crowded.
assert "grid.setColumnCount(3)" in source
assert "getDisplayMetrics().widthPixels - dp(48)) / 3" in source
assert "new LinearLayout.LayoutParams(dp(54), dp(54))" in source
assert "glp.setMargins(dp(6), dp(6), dp(6), dp(6))" in source
assert "private int dp(int value)" in source
assert "searchEt.setSingleLine(true)" in source
assert "searchEt.setTextSize(14f)" in source

print("PASS: Add App keeps discovery, search, single/batch clone and reservation/commit flows.")
print("PASS: App picker uses a three-column density-aware grid with compact app icons and refined spacing.")
