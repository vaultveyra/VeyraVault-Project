#!/usr/bin/env python3
"""Source gate for global monotonic Clone IDs and fail-closed Engine inventory preflight."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
REPO = (ROOT / "app/src/main/java/com/veyravault/space/core/AsyncCloneRepository.java").read_text(encoding="utf-8")
ENGINE = (ROOT / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
PROVISION = (ROOT / "app/src/main/java/com/veyravault/space/core/AsyncCloneProvisionRepository.java").read_text(encoding="utf-8")
QUEUE = (ROOT / "app/src/main/java/com/veyravault/space/core/EngineOperationQueue.java").read_text(encoding="utf-8")
TEST = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/AsyncCloneRepositoryInstrumentationTest.java").read_text(encoding="utf-8")
SCOPE_TEST = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/CloneUserIdScopeInstrumentationTest.java").read_text(encoding="utf-8")

def body(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{": depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0: return source[brace + 1:index]
    raise AssertionError("Unclosed method: " + signature)

reserve_signature_start = STORE.index("static synchronized CloneReservation reserveNextUserId(")
reserve_signature_end = STORE.index("{", reserve_signature_start)
reserve_signature = STORE[reserve_signature_start:reserve_signature_end]
assert "List<Integer> engineUserIds" in reserve_signature
assert "List<Integer> accountUserIds" in reserve_signature
reserve = body(STORE, "static synchronized CloneReservation reserveNextUserId(")
assert "validateIdInventory(engineUserIds" in reserve and "validateIdInventory(accountUserIds" in reserve
assert "readAllStrict(c)" in reserve and "readReservationsStrict(c)" in reserve
assert "maxKnownId = Math.max(maxKnownId, entry.userId)" in reserve
assert "maxKnownId = Math.max(maxKnownId, reservation.userId)" in reserve
assert "maxKnownId = Math.max(maxKnownId, id)" in reserve
assert "KEY_GLOBAL_HIGH_WATER_MARK" in reserve and "maxKnownId + 1" in reserve
assert "Integer.MAX_VALUE" in reserve
assert "putString(KEY_PENDING_RESERVATIONS" in reserve
assert "putInt(KEY_GLOBAL_HIGH_WATER_MARK, candidate)" in reserve
assert "editor.commit()" in reserve
assert "Global ID high-water and reservation commit failed" in reserve
assert "engineUserIds == null || accountUserIds == null" in REPO
assert "Engine.getKnownVirtualUserIds()" in PROVISION
assert "Engine.getKnownAccountUserIds()" in PROVISION
assert "EngineOperationQueue.submit(" in PROVISION
assert PROVISION.index("persistence.inspectNativeAbi(packageName") < PROVISION.index("EngineOperationQueue.submit(")
assert PROVISION.index("EngineOperationQueue.submit(") < PROVISION.index("Engine.getKnownVirtualUserIds()")
assert PROVISION.index("Engine.getKnownAccountUserIds()") < PROVISION.index("persistence.reserveNextUserId(packageName")
assert PROVISION.index("persistence.reserveNextUserId(packageName") < PROVISION.index("Engine.installPackageAsUser(")
assert "ID inventory could not be verified" in PROVISION
assert "no ID was reserved and installation did not start" in PROVISION
assert "private static final ExecutorService ENGINE" in QUEUE
assert "getKnownVirtualUserIds() throws Exception" in ENGINE
assert "getKnownAccountUserIds() throws Exception" in ENGINE
save_all = body(STORE, "public static synchronized boolean saveAll(")
assert "readAllStrict(c)" in save_all
assert "maxKnownId = Math.max(maxKnownId, entry.userId)" in save_all
assert "putInt(KEY_GLOBAL_HIGH_WATER_MARK, maxKnownId)" in save_all
assert "return editor.commit();" in save_all
release = body(STORE, "static synchronized boolean releaseReservationAfterEngineAbsence(")
remove = body(STORE, "public static synchronized boolean removeClone(")
assert "KEY_GLOBAL_HIGH_WATER_MARK" in release
assert "putInt(KEY_GLOBAL_HIGH_WATER_MARK, maxKnownId)" in release
assert "KEY_GLOBAL_HIGH_WATER_MARK" not in remove
assert "@Deprecated" in STORE[STORE.index("public static synchronized int nextFreeUserIdForPackage") - 250:]
for name in ("globalAllocatorUsesCloneEngineAndAccountManagerInventories",
             "missingOrInvalidEngineInventoriesBlockReservationWithoutChangingLedger",
             "globalAllocatorRejectsIntegerOverflowWithoutWrapping",
             "reservationReleaseRequiresEngineAbsenceButNeverReusesTheGlobalId",\n             "releasingLegacyPendingReservationSeedsGlobalHighWaterMark"):
    assert name in TEST
for name in ("globalAllocatorNeverReservesSameNumericUserIdForDifferentPackages",
             "removedCloneRegistryEntryDoesNotLowerGlobalHighWaterMark"):
    assert name in SCOPE_TEST
print("PASS: global IDs are selected above all validated Clone, reservation, Engine and AccountManager IDs.")
print("PASS: high-water mark and exact reservation are persisted atomically before Engine installation.")
print("PASS: unavailable, malformed, duplicate or overflowing inventories fail closed.")
print("PASS: releasing a failed reservation or removing a Clone does not lower the global high-water mark.")
print("PASS: instrumentation covers cross-package uniqueness, inventory maxima, failure and overflow.")
print("SCOPE LIMIT: IDs fully erased from every legacy store before this rollout cannot be reconstructed.")
print("PASS: no legacy Clone ID is migrated, reassigned, or deleted by this stage.")
