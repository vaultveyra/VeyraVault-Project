#!/usr/bin/env python3
"""Guard fail-closed legacy CloneStore mutations and clone provisioning."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
store = (root / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
engine = (root / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
main_ui = (root / "app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
add_ui = (root / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
test = (root / "app/src/androidTest/java/com/veyravault/space/core/CloneStoreSafetyInstrumentationTest.java").read_text(encoding="utf-8")

def body(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError("Unclosed method: " + signature)

reader = body(store, "static List<CloneEntry> readAllStrict(")
assert "values.containsKey(KEY_CLONES)" in reader
assert "new JSONArray((String) rawValue)" in reader
assert "Duplicate clone identity" in reader
assert "invalid enabled-location coordinates" in reader

save = body(store, "public static synchronized boolean saveAll(")
assert "serializeEntries(list)" in save
assert "reserved.contains(identityKey(entry.packageName, entry.userId))" in save
assert "return false;" in save
serializer = body(store, "private static String serializeEntries(")
assert "identities.add(" in serializer
assert "e.mockGpsEnabled" in serializer and "e.latitude < -90.0d" in serializer

upsert = body(store, "public static synchronized boolean upsertClone(")
remove = body(store, "public static synchronized boolean removeClone(")
next_id = body(store, "public static synchronized int nextFreeUserIdForPackage(")
assert "readAllStrict(c)" in upsert and "return false;" in upsert
assert "readAllStrict(c)" in remove and "return false;" in remove
assert "readAllStrict(c)" in next_id and "readReservationsStrict(c)" in next_id and "return -1;" in next_id
reserve = body(store, "static synchronized CloneReservation reserveNextUserId(")
assert "KEY_PENDING_RESERVATIONS" in reserve and ".commit()" in reserve
assert "public static List<CloneEntry> getAll(Context c)" in store

assert "CloneStore.nextFreeUserIdForPackage(" not in add_ui
assert "CloneStore.upsertClone(" not in add_ui
add_clone = add_ui[add_ui.index("private void cloneSingleApp("):
                   add_ui.index("private void releaseReservationAfterConfirmedEngineAbsence(")]
assert "repository.inspectNativeAbi(app.pkg" in add_clone
assert "repository.reserveNextUserId(app.pkg" in add_clone
assert add_clone.index("repository.inspectNativeAbi(app.pkg") < add_clone.index("repository.reserveNextUserId(app.pkg")
assert "Engine.installPackageAsUser(AddAppActivity.this, entry.packageName, entry.userId, preflight)" in add_clone
assert add_clone.index("Engine.installPackageAsUser(AddAppActivity.this, entry.packageName, entry.userId, preflight)") < add_clone.index("repository.commitReservedClone(entry")
assert "repository.allocateNextUserId" not in add_ui

assert "duplicateCloneWithPreflight(item);" in main_ui
duplicate = main_ui[main_ui.index("private void duplicateCloneWithPreflight("):
                   main_ui.index("private void showRenameDialog(")]
assert "repository.inspectNativeAbi(item.packageName" in duplicate
assert "repository.reserveNextUserId(item.packageName" in duplicate
assert duplicate.index("repository.inspectNativeAbi(item.packageName") < duplicate.index("repository.reserveNextUserId(item.packageName")
assert "Engine.installPackageAsUser(MainActivity.this," in duplicate
assert "copy.packageName, copy.userId, preflight)" in duplicate
assert duplicate.index("Engine.installPackageAsUser(MainActivity.this,") < duplicate.index("repository.commitReservedClone(copy")
assert "repository.allocateNextUserId" not in main_ui

uninstall = body(engine, "public static boolean uninstallClone(")
assert "Boolean.FALSE.equals(queryInstalledAsUser(pkg, userId))" in uninstall
assert "return false;" in uninstall
assert "if (!Engine.uninstallClone(item.packageName, item.userId))" in main_ui
assert "repository.removeClone(item.packageName, item.userId" in main_ui
assert main_ui.index("if (!Engine.uninstallClone(item.packageName, item.userId))") < main_ui.index("repository.removeClone(item.packageName, item.userId")

for marker in (
    "malformedRegistryBlocksMutationAndUserIdAllocationWithoutChangingBytes",
    "duplicateCompositeIdentityBlocksMutationAndAllocation",
    "invalidEnabledCoordinatesAreNotPersisted",
    "validRegistryMutationsReturnCommitStatusAndPreserveCompositeIdentity",
):
    assert marker in test, "Missing Android safety test: " + marker

print("CloneStore strict mutation and allocation contract: PASS")
print("Clone provisioning and uninstall failure handling contract: PASS")
print("Android instrumentation coverage for malformed/duplicate/invalid/valid data: PASS")
