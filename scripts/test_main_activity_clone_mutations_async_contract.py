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
assert "repository.loadClones" in shortcut
assert "if (!result.isSuccess()" in shortcut
assert "Engine.launchClone(this, entry)" in shortcut

# Duplication keeps the Engine install before registry persistence and cleans up on failed save.
duplicate_start = source.index('makeSheetActionBtn("⊞+"')
duplicate_end = source.index('makeSheetActionBtn("📱"', duplicate_start)
duplicate = source[duplicate_start:duplicate_end]
assert "repository.allocateNextUserId" in duplicate
assert "Engine.installPackageAsUser" in duplicate
assert "repository.upsertClone(copy" in duplicate
assert duplicate.index("Engine.installPackageAsUser") < duplicate.index("repository.upsertClone(copy")
assert "Engine.uninstallClone(copy.packageName, copy.userId)" in duplicate
assert duplicate.index("if (!save.isSuccess())") < duplicate.index("Engine.uninstallClone(copy.packageName, copy.userId)")
save_callback = duplicate[duplicate.index("repository.upsertClone(copy"):]
assert save_callback.index("if (!save.isSuccess())") < save_callback.index("if (isFinishing() || isDestroyed()) return;")

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
assert "VirtualHookManager.syncCloneHooks(MainActivity.this, item)" in profile
assert profile.index("if (!result.isSuccess())") < profile.index("VirtualHookManager.syncCloneHooks")

# Uninstall registry removal happens only after Engine confirms absence.
single_start = source.index('makeSheetActionBtn("🗑️"')
single_end = source.index('makeSheetActionBtn("📦"', single_start)
single = source[single_start:single_end]
assert "if (!Engine.uninstallClone(item.packageName, item.userId))" in single
assert "repository.removeClone(item.packageName, item.userId" in single
assert single.index("Engine.uninstallClone") < single.index("repository.removeClone")

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

print("PASS: MainActivity shortcut, duplicate, rename, profile metadata and uninstall registry persistence use AsyncCloneRepository.")
print("PASS: Engine install/uninstall ordering and cleanup-on-save-failure are preserved.")
print("PASS: Batch uninstall is sequential, commit-aware and reports partial outcomes.")
