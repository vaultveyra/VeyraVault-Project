#!/usr/bin/env python3
"""Guard fail-closed legacy CloneStore mutations and clone provisioning."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
store = (root / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
engine = (root / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
main_ui = (root / "app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
add_ui = (root / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
test = (root / "app/src/androidTest/java/com/veyravault/space/core/CloneStoreSafetyInstrumentationTest.java").read_text(encoding="utf-8")
provision = (root / "app/src/main/java/com/veyravault/space/core/AsyncCloneProvisionRepository.java").read_text(encoding="utf-8")
queue = (root / "app/src/main/java/com/veyravault/space/core/EngineOperationQueue.java").read_text(encoding="utf-8")

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
                   add_ui.index("private void showCloneError(")]
assert "provisionRepository.createClone(app.pkg, app.label, fa" in add_clone
assert "Engine.installPackageAsUser(" not in add_clone
assert "Engine.uninstallClone(" not in add_clone
assert "repository.allocateNextUserId" not in add_ui

assert "duplicateCloneWithPreflight(item);" in main_ui
duplicate = main_ui[main_ui.index("private void duplicateCloneWithPreflight("):
                   main_ui.index("private void showRenameDialog(")]
assert "provisionRepository.createClone(item.packageName, item.displayName, fa" in duplicate
assert "Engine.installPackageAsUser(" not in duplicate
assert "Engine.uninstallClone(" not in duplicate
assert "repository.allocateNextUserId" not in main_ui

assert "persistence.inspectNativeAbi(packageName" in provision
assert "persistence.reserveNextUserId(packageName" in provision
assert "Engine.installPackageAsUser(" in provision
assert "persistence.commitReservedClone(entry, reservation" in provision
assert provision.index("persistence.inspectNativeAbi(packageName") < provision.index("persistence.reserveNextUserId(packageName")
assert provision.index("persistence.reserveNextUserId(packageName") < provision.index("Engine.installPackageAsUser(")
assert provision.index("Engine.installPackageAsUser(") < provision.index("persistence.commitReservedClone(entry, reservation")
assert "Engine.CloneInstallState.ABSENT" in provision
assert "releaseAfterConfirmedAbsence" in provision
assert "reservation remains blocked" in provision
assert "private static final ExecutorService ENGINE" in queue

uninstall = body(engine, "public static boolean uninstallClone(")
assert "Boolean.FALSE.equals(queryInstalledAsUser(pkg, userId))" in uninstall
assert "return false;" in uninstall
single_start = main_ui.index("private void confirmUninstallClone(")
single_end = main_ui.index("private void confirmBatchUninstall(", single_start)
single = main_ui[single_start:single_end]
assert "EngineOperationQueue.submit(" in single
assert "Engine.uninstallClone(item.packageName, item.userId)" in single
assert "repository.removeClone(item.packageName, item.userId" in single
assert single.index("EngineOperationQueue.submit(") < single.index("Engine.uninstallClone(item.packageName, item.userId)") < single.index("repository.removeClone(item.packageName, item.userId")
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
