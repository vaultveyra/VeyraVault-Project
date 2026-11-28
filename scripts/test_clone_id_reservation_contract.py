#!/usr/bin/env python3
"""Guard the durable, token-bound clone ID reservation contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
REPO = (ROOT / "app/src/main/java/com/veyravault/space/core/AsyncCloneRepository.java").read_text(encoding="utf-8")
ENGINE = (ROOT / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
ADD = (ROOT / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
MAIN = (ROOT / "app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
PROVISION = (ROOT / "app/src/main/java/com/veyravault/space/core/AsyncCloneProvisionRepository.java").read_text(encoding="utf-8")
QUEUE = (ROOT / "app/src/main/java/com/veyravault/space/core/EngineOperationQueue.java").read_text(encoding="utf-8")
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
assert "prefs(c).edit()" in reserve and "putString(KEY_PENDING_RESERVATIONS" in reserve
assert ".commit()" in reserve
assert "throw new PersistenceException(\"Global ID high-water and reservation commit failed\")" in reserve
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

# Both UIs delegate into one service that owns the entire preflight/reservation/install/commit transaction.
for ui in (ADD, MAIN):
    assert "provisionRepository.createClone(" in ui
    assert "Engine.installPackageAsUser(" not in ui
assert "persistence.inspectNativeAbi(packageName" in PROVISION
assert "persistence.reserveNextUserId(packageName, inventories.virtualUserIds" in PROVISION
assert "Engine.getKnownVirtualUserIds()" in PROVISION
assert "Engine.getKnownAccountUserIds()" in PROVISION
assert PROVISION.index("EngineOperationQueue.submit(") < PROVISION.index("Engine.getKnownVirtualUserIds()")
assert PROVISION.index("Engine.getKnownAccountUserIds()") < PROVISION.index("persistence.reserveNextUserId(packageName")
assert "Engine.installPackageAsUser(" in PROVISION
assert "persistence.commitReservedClone(entry, reservation" in PROVISION
assert PROVISION.index("persistence.inspectNativeAbi(packageName") < PROVISION.index("persistence.reserveNextUserId(packageName")
assert PROVISION.index("persistence.reserveNextUserId(packageName") < PROVISION.index("Engine.installPackageAsUser(")
assert PROVISION.index("Engine.installPackageAsUser(") < PROVISION.index("persistence.commitReservedClone(entry, reservation")
assert "Engine.CloneInstallState.ABSENT" in PROVISION
assert "releaseAfterConfirmedAbsence" in PROVISION
assert "reservation remains blocked" in PROVISION
assert "private static final ExecutorService ENGINE" in QUEUE
assert "veyravault-engine-operations" in QUEUE
assert "EngineOperationQueue.submit(" in PROVISION

# Concurrency, durable recreation, token mismatch, safe release, and collision protection are instrumented.
for test_name in (
    "independentRepositoriesCannotReserveSamePackageUserId",
    "reservationSurvivesRepositoryRecreationAndCommitConsumesOnlyItsToken",
    "reservationReleaseRequiresEngineAbsenceButNeverReusesTheGlobalId",
    "releasingLegacyPendingReservationSeedsGlobalHighWaterMark",
    "globalAllocatorUsesCloneEngineAndAccountManagerInventories",
    "missingOrInvalidEngineInventoriesBlockReservationWithoutChangingLedger",
    "globalAllocatorRejectsIntegerOverflowWithoutWrapping",
    "reservationReleaseRefusesRegistryConflictAndPreservesJournal",
    "pendingReservationCannotBeStolenByOrdinaryCloneUpsert",
    "malformedReservationJournalBlocksAllocationWithoutOverwritingIt",
    "reservationJournalConflictWithExistingCloneBlocksAllocation",
):
    assert test_name in TEST, test_name

print("Atomic clone ID reservation source contract: PASS")
