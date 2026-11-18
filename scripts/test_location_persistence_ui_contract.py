from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/SetLocationActivity.java").read_text(encoding="utf-8")
assert "AsyncCloneRepository.getInstance(getApplicationContext())" in source
assert source.count(".upsertClone(cloneEntry, result ->") == 2
assert "CloneStore.upsertClone" not in source
assert "A valid target clone is required." in source
assert "Clone not found or stored data is unreadable." in source
assert "Global Mock GPS" not in source
assert source.count("if (result.isSuccess())") >= 2
assert source.count("VirtualHookManager.syncCloneHooks(getApplicationContext(), cloneEntry);") == 2
assert "Location was not saved:" in source
assert "Change was not saved:" in source

save_start = source.index(".upsertClone(cloneEntry, result ->", source.index("btnSave.setOnClickListener"))
save_success = source.index("if (result.isSuccess())", save_start)
save_hook = source.index("VirtualHookManager.syncCloneHooks", save_success)
assert save_start < save_success < save_hook

reset_start = source.index(".upsertClone(cloneEntry, result ->", source.index("btnReset.setOnClickListener"))
reset_success = source.index("if (result.isSuccess())", reset_start)
reset_hook = source.index("VirtualHookManager.syncCloneHooks", reset_success)
assert reset_start < reset_success < reset_hook

print("PASS: SetLocationActivity persists clone changes asynchronously and fails closed.")
