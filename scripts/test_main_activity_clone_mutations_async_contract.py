from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")

# No direct CloneStore persistence reads/writes remain in MainActivity mutation flows.
for forbidden in (
    "CloneStore.getClone(",
    "CloneStore.getAll(",
    "CloneStore.nextFreeUserIdForPackage(",
    "CloneStore.upsertClone(",
    "CloneStore.removeClone(",
):
    assert forbidden not in source, f"Direct persistence call remains: {forbidden}"

# Shortcut launch uses a strict repository snapshot and never launches from a fallback read.
shortcut_start = source.index("private void handleShortcutLaunch")
shortcut_end = source.index("@Override", shortcut_start)
shortcut = source[shortcut_start:shortcut_end]
assert "launchRepository.launchClone(pkg, uid" in shortcut
assert "Engine.launchClone(this, entry)" not in shortcut

# Duplication delegates to the app-scoped transaction coordinator.
duplicate_start = source.index('makeSheetActionBtn("⊞+"')
duplicate_end = source.index('makeSheetActionBtn("📱"', duplicate_start)
duplicate = source[duplicate_start:duplicate_end]
assert "duplicateCloneWithPreflight(item);" in duplicate
clone_creation = source[source.index("private void duplicateCloneWithPreflight("):
                        source.index("private void showRenameDialog(")]
assert "provisionRepository.createClone(item.packageName, item.displayName, fa" in clone_creation
assert "Engine.installPackageAsUser(" not in clone_creation
assert "Engine.uninstallClone(" not in clone_creation
assert "repository.allocateNextUserId" not in source

# Rename and per-clone profile writes are commit-aware; in-memory values are reverted on failure.
rename_start = source.index("private void showRenameDialog")
rename_end = source.index("private void showPerCloneDeviceIdentityDialog", rename_start)
rename = source[rename_start:rename_end]
assert "repository.upsertClone(item" in rename
assert "item.displayName = previousName" in rename
profile_start = source.index("private void showPerCloneDeviceIdentityDialog")
profile_end = source.index("private void showBatchUninstallDialog", profile_start)
profile = source[profile_start:profile_end]
assert profile.count("repository.upsertClone(item") == 2
assert "item.deviceBrand = previousBrand" in profile
assert "item.deviceModel = previousModel" in profile
assert "VirtualHookManager.syncCloneHooks" not in profile

# Single uninstall runs on the shared Engine queue before Registry removal.
single_start = source.index('makeSheetActionBtn("🗑️"')
single_end = source.index('makeSheetActionBtn("📦"', single_start)
single = source[single_start:single_end]
assert "EngineOperationQueue.submit(" in single
assert "Engine.uninstallClone(item.packageName, item.userId)" in single
assert "repository.removeClone(item.packageName, item.userId" in single

# Batch selection is loaded strictly and each Engine removal is followed by an async registry commit.
batch_start = source.index("private void showBatchUninstallDialog")
batch_end = source.index("private Drawable loadAppIcon", batch_start)
batch = source[batch_start:batch_end]
assert "repository.loadClones" in batch
assert "CloneStore.getAll" not in batch
assert "runBatchUninstall(all, checked, 0" in batch
assert "Engine.uninstallClone(entry.packageName, entry.userId)" in batch
assert "repository.removeClone(entry.packageName, entry.userId" in batch
assert batch.index("Engine.uninstallClone(entry.packageName, entry.userId)") < batch.index("repository.removeClone(entry.packageName, entry.userId")
assert "registry failures" in batch
assert "refreshSpaces();" in batch

assert "Engine.installPackageAsUser(" not in source
assert "Engine.isCloneConfirmedAbsent(" not in source
assert "EngineOperationQueue.submit(" in source
for call in ("Engine.stopClone(item.packageName, item.userId)",
             "Engine.clearCloneData(item.packageName, item.userId)",
             "Engine.uninstallClone(item.packageName, item.userId)"):
    pos = source.find(call)
    assert pos >= 0
    assert source.rfind("EngineOperationQueue.submit(", 0, pos) > source.rfind("});", 0, pos)

print("PASS: MainActivity delegates Clone provisioning and serializes synchronous Engine operations.")
print("PASS: Single and batch uninstall remain Engine-first and Registry-commit-aware.")
