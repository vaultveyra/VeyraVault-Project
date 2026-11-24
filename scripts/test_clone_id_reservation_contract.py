#!/usr/bin/env python3
"""Guard the durable, token-bound clone ID reservation contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
REPO = (ROOT / "app/src/main/java/com/veyravault/space/core/AsyncCloneRepository.java").read_text(encoding="utf-8")
ENGINE = (ROOT / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
ADD = (ROOT / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
MAIN = (ROOT / "app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
TEST = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/AsyncCloneRepositoryInstrumentationTest.java").read_text(encoding="utf-8")


def method_body(source: str, signature: str) -> str:
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


# Journal is versioned, strict, and persisted into the existing CloneStore preference file.
assert 'KEY_PENDING_RESERVATIONS = "pending_clone_reservations_json"' in STORE
assert "RESERVATION_SCHEMA_VERSION = 1" in STORE
assert "readReservationsStrict" in STORE
assert "Reservation journal schema is unsupported" in STORE
assert "duplicate token or identity" in STORE
assert "UUID.randomUUID().toString()" in STORE

reserve = method_body(STORE, "static synchronized CloneReservation reserveNextUserId(")
assert "readAllStrict(c)" in reserve
assert "readReservationsStrict(c)" in reserve
assert "Reservation journal conflicts with the clone registry" in reserve
assert "prefs(c).edit().putString(KEY_PENDING_RESERVATIONS" in reserve
assert ".commit()" in reserve
assert "throw new PersistenceException(\"Reservation journal commit failed\")" in reserve
assert "CloneStore.PersistenceException) return Failure.PERSISTENCE_FAILURE" in REPO
assert "reservationJournalCommitFailureIsClassifiedAsPersistenceFailure" in TEST

commit = method_body(STORE, "static synchronized boolean commitReservedClone(")
assert "reservation.token.equals(supplied.token)" in commit
assert "entry.userId != supplied.userId" in commit
assert "putString(KEY_CLONES, serializeEntries(clones))" in commit
assert "editor.remove(KEY_PENDING_RESERVATIONS)" in commit
assert "editor.putString(KEY_PENDING_RESERVATIONS" in commit
assert "return editor.commit();" in commit

release = method_body(STORE, "static synchronized boolean releaseReservationAfterEngineAbsence(")
assert "if (!engineAbsenceConfirmed) return false;" in release
assert "readPendingReservationsStrict(c)" in release
assert "reservation.token.equals(supplied.token)" in release
assert "return editor.commit();" in release

upsert = method_body(STORE, "public static synchronized boolean upsertClone(")
assert "containsReservation(reservations, entry.packageName, entry.userId)" in upsert
save_all = method_body(STORE, "public static synchronized boolean saveAll(")
assert "reserved.contains(identityKey(entry.packageName, entry.userId))" in save_all

# Engine absence is a positive-only check; reflection/query uncertainty cannot free a reservation.
absence = method_body(ENGINE, "public static boolean isCloneConfirmedAbsent(")
assert "getCloneInstallState(pkg, userId) == CloneInstallState.ABSENT" in absence
install_state = method_body(ENGINE, "public static CloneInstallState getCloneInstallState(")
assert "classifyInstalledQueryResult(queryInstalledAsUser(pkg, userId))" in install_state

# Repository APIs expose reservation operations without performing Engine side effects.
for api in (
    "reserveNextUserId", "commitReservedClone",
    "releaseReservationAfterEngineAbsence", "loadPendingReservations",
):
    assert api in REPO
assert "ENGINE_STATE_UNCONFIRMED" in REPO
assert "Engine." not in REPO
assert "ClonePersistenceDatabase" not in REPO

# Both supported clone-creation UIs reserve before install, then commit the exact token.
for source, pkg, entry in ((ADD, "app.pkg", "entry"), (MAIN, "item.packageName", "copy")):
    assert f"repository.reserveNextUserId({pkg}" in source
    assert f"repository.commitReservedClone({entry}, reservation" in source
    assert "repository.allocateNextUserId" not in source
add_clone = ADD[ADD.index("private void cloneSingleApp("):
                  ADD.index("private void releaseReservationAfterConfirmedEngineAbsence(")]
assert "repository.inspectNativeAbi(app.pkg" in add_clone
assert add_clone.index("repository.inspectNativeAbi(app.pkg") < add_clone.index("repository.reserveNextUserId(app.pkg")
assert "Engine.installPackageAsUser(AddAppActivity.this, entry.packageName, entry.userId, preflight)" in add_clone
assert add_clone.index("Engine.installPackageAsUser(AddAppActivity.this, entry.packageName, entry.userId, preflight)") < add_clone.index(
    "repository.commitReservedClone(entry, reservation"
)

duplicate = MAIN[MAIN.index("private void duplicateCloneWithPreflight("):
                 MAIN.index("private void showRenameDialog(")]
assert "repository.inspectNativeAbi(item.packageName" in duplicate
assert duplicate.index("repository.inspectNativeAbi(item.packageName") < duplicate.index("repository.reserveNextUserId(item.packageName")
assert "Engine.installPackageAsUser(MainActivity.this," in duplicate
assert "copy.packageName, copy.userId, preflight)" in duplicate
assert duplicate.index("Engine.installPackageAsUser(MainActivity.this,") < duplicate.index(
    "repository.commitReservedClone(copy, reservation"
)
assert "Engine.isCloneConfirmedAbsent" in ADD and "Engine.isCloneConfirmedAbsent" in MAIN
assert "releaseReservationAfterEngineAbsence" in ADD and "releaseReservationAfterEngineAbsence" in MAIN
assert "Engine.uninstallClone(entry.packageName, entry.userId)" in ADD
assert "Engine.uninstallClone(copy.packageName, copy.userId)" in MAIN

# Concurrency, durable recreation, token mismatch, safe release, and collision protection are instrumented.
for test_name in (
    "independentRepositoriesCannotReserveSamePackageUserId",
    "reservationSurvivesRepositoryRecreationAndCommitConsumesOnlyItsToken",
    "reservationReleaseRequiresExplicitEngineAbsenceAndAllowsSafeReuse",
    "reservationReleaseRefusesRegistryConflictAndPreservesJournal",
    "pendingReservationCannotBeStolenByOrdinaryCloneUpsert",
    "malformedReservationJournalBlocksAllocationWithoutOverwritingIt",
    "reservationJournalConflictWithExistingCloneBlocksAllocation",
):
    assert test_name in TEST, test_name

print("Atomic clone ID reservation source contract: PASS")
