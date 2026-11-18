#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "app/src/main/java/com/veyravault/space/core/AsyncCloneRepository.java"
STORE = ROOT / "app/src/main/java/com/veyravault/space/core/CloneStore.java"
PROFILE = ROOT / "app/src/main/java/com/veyravault/space/core/ProfileStore.java"
TEST = ROOT / "app/src/androidTest/java/com/veyravault/space/core/AsyncCloneRepositoryInstrumentationTest.java"

repo = REPO.read_text(encoding="utf-8")
store = STORE.read_text(encoding="utf-8")
profile = PROFILE.read_text(encoding="utf-8")
test = TEST.read_text(encoding="utf-8")

assert "Executors.newSingleThreadExecutor" in repo
assert "new Handler(Looper.getMainLooper())" in repo
assert "CloneStore.readAllStrict(appContext)" in repo
assert "Failure.CORRUPT_DATA" in repo
assert "Failure.PERSISTENCE_FAILURE" in repo
assert "copyEntries" in repo and "copyEntry" in repo
assert "ClonePersistenceDatabase" not in repo and "androidx.room" not in repo
assert "Engine." not in repo and "VirtualHookManager" not in repo
assert "static List<CloneEntry> readAllStrict" in store
assert "CloneStore.readAllStrict(context)" in profile
assert "CloneStore.getAll(context)" not in profile[profile.index("migrateLegacyLocationSettings"):profile.index("private static boolean validLatitude")]
for case in (
    "queuedUpsertThenReadPreservesSubmissionOrder",
    "callbacksAreDispatchedOnMainLooper",
    "returnedMutableRecordsDoNotMutatePersistedState",
    "corruptRegistryIsReturnedAsTypedFailure",
    "closedRepositoryRejectsNewWorkExplicitly",
    "profileMigrationDoesNotMarkCorruptRegistryAsImported",
):
    assert case in test, case

print("Async persistence repository contract: PASS")
