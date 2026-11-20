#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
test = ROOT / "app/src/androidTest/java/com/veyravault/space/core/persistence/LegacyCloneRoomInstrumentationTest.java"
backup_test = ROOT / "app/src/androidTest/java/com/veyravault/space/core/persistence/LegacyCloneSnapshotBackupInstrumentationTest.java"
crash_test = ROOT / "app/src/androidTest/java/com/veyravault/space/core/persistence/LegacyCloneRoomProcessDeathInstrumentationTest.java"
crash_service = ROOT / "app/src/debug/java/com/veyravault/space/core/persistence/CloneMigrationCrashTestService.java"
importer_path = ROOT / "app/src/main/java/com/veyravault/space/core/persistence/LegacyCloneRoomImporter.java"
debug_manifest = ROOT / "app/src/debug/AndroidManifest.xml"
debug_app = ROOT / "app/src/debug/java/com/veyravault/space/RoomTestApplication.java"
prepare = (ROOT / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")

assert test.is_file(), "Android Room instrumentation test source is missing"
source = test.read_text(encoding="utf-8")
for marker in ("importsAndVerifiesAllModeledRowsAndProvenance",
               "repeatedImportIsIdempotentOnlyWhenParityStillMatches",
               "transactionRollsBackEveryTableWhenPermissionInsertFails",
               "importedRowsSurviveDatabaseCloseAndReopen",
               "emptySnapshotWithoutActiveMarkerImportsAndVerifies",
               "verifiedBackupSnapshotCanBeImportedWithoutOverwritingCurrentPreferences",
               "LegacyCloneSnapshotBackup.readAndVerify",
               "CREATE TRIGGER fail_permission_insert",
               "LegacyCloneRoomVerifier.matches"):
    assert marker in source, f"Missing instrumentation scenario: {marker}"

assert backup_test.is_file(), "Android backup integrity instrumentation test source is missing"
backup_source = backup_test.read_text(encoding="utf-8")
for marker in ("backupIsWrittenReadBackAndReusedForExactSnapshot",
               "interruptedAtomicFileSidecarIsRecoveredAndVerified",
               "immutableBackupRejectsDifferentSnapshotWithoutChangingOriginal",
               "corruptExistingBackupIsRejectedAndNeverOverwritten",
               "readAndVerifyReconstructsBackupWithoutReadingOrMutatingCurrentPreferences",
               "readAndVerifyRejectsUnsupportedEnvelopeVersion",
               "LegacyCloneSnapshotBackup.readAndVerify",
               "LegacyCloneSnapshotBackup.writeAndVerify",
               "assertArrayEquals(original, readFile(backupFile))"):
    assert marker in backup_source, f"Missing backup instrumentation scenario: {marker}"

assert crash_test.is_file(), "OS process-death instrumentation test source is missing"
crash_source = crash_test.read_text(encoding="utf-8")
for marker in ("osProcessDeathDuringRoomImportRollsBackAndRestartSeesEmptyDatabase",
               "Process.killProcess(killedServicePid)",
               "waitForProcessExit(killedServicePid",
               "ACTION_IMPORT_AND_PAUSE", "ACTION_VERIFY_EMPTY",
               'parseCount(verified, "metadata")'):
    assert marker in crash_source, f"Missing process-death scenario: {marker}"

assert crash_service.is_file(), "Debug-only process-death service is missing"
service_source = crash_service.read_text(encoding="utf-8")
for marker in ("android.app.Service", "ACTION_IMPORT_AND_PAUSE", "ACTION_VERIFY_EMPTY",
               "importIntoEmptyDatabaseWithCheckpoint", "CountDownLatch(1).await()",
               "migration-process-death-test"):
    assert marker in service_source, f"Missing isolated service behavior: {marker}"

# Marker files are published atomically so the instrumentation process cannot observe a
# zero-length file while the isolated service is still writing its PID/checkpoint payload.
for marker in ('name + ".tmp"', "output.getFD().sync()", "temporary.renameTo(target)"):
    assert marker in service_source, f"Missing atomic marker publication: {marker}"
assert "marker.length() > 0L" in crash_source
assert 'assertEquals("Clone rows must roll back after OS process death"' in crash_source

importer_source = importer_path.read_text(encoding="utf-8")
assert "importIntoEmptyDatabaseWithCheckpoint" in importer_source
assert "checkpoint.afterCloneAndPermissionRowsInserted()" in importer_source
assert importer_source.index("database.runInTransaction") < importer_source.index(
    "checkpoint.afterCloneAndPermissionRowsInserted()"), "Crash checkpoint must remain inside the Room transaction"

dao = (ROOT / "app/src/main/java/com/veyravault/space/core/persistence/LegacyMigrationMetadataDao.java").read_text(encoding="utf-8")
assert '@Query("SELECT COUNT(*) FROM legacy_migration_metadata")' in dao
assert "int count();" in dao

assert debug_manifest.is_file() and debug_app.is_file()
manifest_source = debug_manifest.read_text(encoding="utf-8")
assert "RoomTestApplication" in manifest_source
assert "CloneMigrationCrashTestService" in manifest_source
assert 'android:process=":migration_recovery_test"' in manifest_source
assert "CloneMigrationCrashTestService" not in (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8"), "Crash service must not enter release manifest"
assert "Engine.doOnCreate" not in debug_app.read_text(encoding="utf-8")
assert 'testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"' in prepare
for dep in ("androidx.test:runner:1.5.2", "androidx.test:core:1.5.0", "androidx.test.ext:junit:1.1.5"):
    assert dep in prepare, f"Missing instrumentation dependency: {dep}"
assert 'excludes += ["**/*.so"]' in prepare
assert "releaseImplementation project(':Bcore')" in prepare and "debugCompileOnly project(':Bcore')" in prepare
assert 'abiFilters "x86_64"' in prepare
assert "reactivecircus/android-emulator-runner@v2" in workflow
assert 'ANDROID_I_WANT_MY_TCG: "yes"' in workflow, "Hosted Linux emulator must explicitly allow TCG when KVM is unavailable"
assert ":app:connectedDebugAndroidTest" in workflow
assert ":app:assembleDebug :app:assembleDebugAndroidTest" in workflow
assert "DEBUG APK NATIVE LIBRARIES" in workflow and "ANDROID TEST APK NATIVE LIBRARIES" in workflow
assert "MERGED DEBUG NATIVE LIBRARY INPUTS" in workflow
clone_safety_test = ROOT / "app/src/androidTest/java/com/veyravault/space/core/CloneStoreSafetyInstrumentationTest.java"
assert clone_safety_test.is_file(), "CloneStore safety instrumentation test source is missing"
clone_safety_source = clone_safety_test.read_text(encoding="utf-8")
for marker in ("malformedRegistryBlocksMutationAndUserIdAllocationWithoutChangingBytes",
               "duplicateCompositeIdentityBlocksMutationAndAllocation",
               "invalidEnabledCoordinatesAreNotPersisted",
               "validRegistryMutationsReturnCommitStatusAndPreserveCompositeIdentity"):
    assert marker in clone_safety_source, f"Missing CloneStore safety instrumentation scenario: {marker}"

print("PASS: Room, backup-integrity, and OS process-death instrumentation harness wiring is present.")
