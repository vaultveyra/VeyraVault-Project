#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
test = ROOT / "app/src/androidTest/java/com/veyravault/space/core/persistence/LegacyCloneRoomInstrumentationTest.java"
debug_manifest = ROOT / "app/src/debug/AndroidManifest.xml"
debug_app = ROOT / "app/src/debug/java/com/veyravault/space/RoomTestApplication.java"
prepare = (ROOT / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")

assert test.is_file(), "Android Room instrumentation test source is missing"
source = test.read_text(encoding="utf-8")
for marker in (
    "importsAndVerifiesAllModeledRowsAndProvenance",
    "repeatedImportIsIdempotentOnlyWhenParityStillMatches",
    "transactionRollsBackEveryTableWhenPermissionInsertFails",
    "importedRowsSurviveDatabaseCloseAndReopen",
    "emptySnapshotWithoutActiveMarkerImportsAndVerifies",
    "CREATE TRIGGER fail_permission_insert",
    "LegacyCloneRoomVerifier.matches",
):
    assert marker in source, f"Missing instrumentation scenario: {marker}"

dao = (ROOT / "app/src/main/java/com/veyravault/space/core/persistence/LegacyMigrationMetadataDao.java").read_text(encoding="utf-8")
assert '@Query("SELECT COUNT(*) FROM legacy_migration_metadata")' in dao
assert "int count();" in dao

assert debug_manifest.is_file() and debug_app.is_file()
assert "RoomTestApplication" in debug_manifest.read_text(encoding="utf-8")
assert "Engine.doOnCreate" not in debug_app.read_text(encoding="utf-8")
assert 'testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"' in prepare
for dep in (
    "androidx.test:runner:1.5.2",
    "androidx.test:core:1.5.0",
    "androidx.test.ext:junit:1.1.5",
):
    assert dep in prepare, f"Missing instrumentation dependency: {dep}"
assert 'excludes += ["**/*.so"]' in prepare, "Debug Room test APK must not package virtual-engine native libraries"
assert "releaseImplementation project(':Bcore')" in prepare and "debugCompileOnly project(':Bcore')" in prepare, "Debug Room harness must compile against Bcore without packaging its ARM-only engine/native runtime"
assert 'abiFilters "x86_64"' in prepare, "Debug instrumentation variant must match the x86_64 CI emulator"
assert "reactivecircus/android-emulator-runner@v2" in workflow
assert ":app:connectedDebugAndroidTest" in workflow
assert ":app:assembleDebug :app:assembleDebugAndroidTest" in workflow, "Build debug APKs before native ABI diagnostics"
assert "DEBUG APK NATIVE LIBRARIES" in workflow and "ANDROID TEST APK NATIVE LIBRARIES" in workflow, "CI must report native libraries in both instrumentation APKs before install"
assert "MERGED DEBUG NATIVE LIBRARY INPUTS" in workflow, "CI must report merged debug native-library inputs"
print("PASS: Android Room instrumentation harness and emulator CI wiring are present.")
