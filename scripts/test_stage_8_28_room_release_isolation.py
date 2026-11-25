#!/usr/bin/env python3
"""Fail-closed contracts for separating the opt-in Room harness from Release APKs."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
prepare = (ROOT / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
audit = (ROOT / "scripts/audit_apk.py").read_text(encoding="utf-8")
room_contract = (ROOT / "scripts/test_room_foundation_contract.py").read_text(encoding="utf-8")
api21_test = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/LegacyApi21CompatibilityInstrumentationTest.java").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")
doc = ROOT / "docs/STAGE_8_28_ROOM_RUNTIME_RELEASE_ISOLATION.md"

# Room's source/API remains available for Release compilation, but its runtime
# artifacts and annotation-generated implementation are packaged only in Debug.
assert "debugImplementation 'androidx.room:room-runtime:2.6.1'" in prepare
assert "releaseCompileOnly 'androidx.room:room-runtime:2.6.1'" in prepare
assert "implementation 'androidx.room:room-runtime:2.6.1'" not in prepare
assert "debugAnnotationProcessor 'androidx.room:room-compiler:2.6.1'" in prepare
assert "annotationProcessor 'androidx.room:room-compiler:2.6.1'" not in prepare

# Exclude only known metadata with AGP's modern DSL. Do not remove ServiceLoader files.
for marker in (
    '"META-INF/*.version"',
    '"META-INF/com/android/build/gradle/app-metadata.properties"',
    '"META-INF/version-control-info.textproto"',
    "resources {{",
    "excludes += [",
    "vcsInfo {{",
    "include = false",
):
    assert marker in prepare, f"Missing precise metadata exclusion: {marker}"
assert "META-INF/services/" not in prepare
assert "META-INF/**" not in prepare, "Broad META-INF exclusion is forbidden"
assert "packagingOptions {{" not in prepare, "Deprecated AGP packagingOptions block must not return"

# The unsigned APK audit has an exact allowlist and rejects unknown/duplicate META-INF files.
for marker in (
    "EXPECTED_META_INF_ENTRIES",
    "REQUIRED_SERVICE_PROVIDERS",
    "validate_meta_inf_entries",
    "Unexpected META-INF entries",
    "Duplicate META-INF entries",
):
    assert marker in audit, f"Missing strict META-INF inventory rule: {marker}"
assert "outside V1 integrity coverage" not in audit

# API-21 instrumentation continues to exercise the Debug variant's service discovery.
for marker in (
    "coroutineServiceDescriptorsRemainDiscoverableOnApi21",
    "META-INF/services/",
    "kotlinx.coroutines.internal.MainDispatcherFactory",
    "kotlinx.coroutines.CoroutineExceptionHandler",
    "AndroidDispatcherFactory",
    "AndroidExceptionPreHandler",
):
    assert marker in api21_test, f"Debug ServiceLoader regression guard missing: {marker}"

# Signing keeps V1 verification and the V2/V3 full-APK signature requirements.
assert 'verify --verbose --min-sdk-version 21 signed/VeyraVault-release.apk 2>&1' in workflow
for marker in (
    "UNPROTECTED_WARNINGS=",
    "not protected by signature",
    "Verified using v1 scheme (JAR signing): true",
    "Verified using v2 scheme (APK Signature Scheme v2): true",
    "Verified using v3 scheme (APK Signature Scheme v3): true",
):
    assert marker in workflow, f"Missing signature validation marker: {marker}"

# Room remains dormant in the production source graph; no production caller may
# activate the provider while its implementation is compile-only in Release.
main_java = ROOT / "app/src/main/java"
provider = main_java / "com/veyravault/space/core/persistence/ClonePersistenceDatabaseProvider.java"
assert provider.is_file()
for source_path in main_java.rglob("*.java"):
    if source_path != provider:
        assert "ClonePersistenceDatabaseProvider.get(" not in source_path.read_text(encoding="utf-8"), source_path
clone_store = (main_java / "com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
vault_app = (main_java / "com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
assert "ClonePersistenceDatabaseProvider.get(" not in clone_store
assert "ClonePersistenceDatabaseProvider.get(" not in vault_app

assert doc.is_file()
print("PASS: Room runtime and Room code generation are Debug-only; Release has compile-time types only.")
print("PASS: Packaging excludes only precise metadata; ServiceLoader resources are preserved.")
print("PASS: Unsigned Release APK allows only exact required META-INF resources and rejects unknown entries.")
print("PASS: API-21 Debug instrumentation validates both coroutine service descriptors.")
print("PASS: V1 is verified and V2/V3 remain mandatory; only the exact expected META-INF V1 warnings are allowed.")
print("PASS: CloneStore remains the active production persistence source; no Room provider caller exists.")
