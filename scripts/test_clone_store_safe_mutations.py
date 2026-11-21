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
assert "repository.reserveNextUserId(app.pkg" in add_ui
assert "repository.commitReservedClone(entry, reservation" in add_ui
assert "if (!Engine.installPackageAsUser(entry.packageName, entry.userId))" in add_ui
assert add_ui.index("Engine.installPackageAsUser(entry.packageName, entry.userId)") < add_ui.index("repository.commitReservedClone(entry")
assert "repository.allocateNextUserId" not in add_ui
assert "repository.reserveNextUserId(item.packageName" in main_ui
assert "repository.commitReservedClone(copy, reservation" in main_ui
assert "repository.allocateNextUserId" not in main_ui
assert main_ui.index("Engine.installPackageAsUser(copy.packageName, copy.userId)") < main_ui.index("repository.commitReservedClone(copy")

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
