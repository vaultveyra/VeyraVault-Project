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

# Remove only known build-time metadata. Never remove ServiceLoader resources.
for marker in (
    "exclude 'META-INF/*.version'",
    "exclude 'META-INF/com/android/build/gradle/app-metadata.properties'",
    "exclude 'META-INF/version-control-info.textproto'",
):
    assert marker in prepare, f"Missing precise metadata exclusion: {marker}"
assert "META-INF/services/" not in prepare
assert not re.search(r"exclude\\s+['\"]META-INF/\\*\\*", prepare), "Broad META-INF exclusion is forbidden"

# The unsigned Release APK is audited before signing: no ordinary META-INF entry
# may be shipped outside the V1 JAR coverage area.
for marker in ("meta_inf_entries = sorted(", "n.startswith('META-INF/')", "if meta_inf_entries:", "outside V1 integrity coverage"):
    assert marker in audit, f"Missing Release APK META-INF audit: {marker}"

# API-21 instrumentation continues to exercise the Debug test APK's service discovery.
for marker in (
    "coroutineServiceDescriptorsRemainDiscoverableOnApi21",
    "META-INF/services/",
    "kotlinx.coroutines.internal.MainDispatcherFactory",
    "kotlinx.coroutines.CoroutineExceptionHandler",
    "AndroidDispatcherFactory",
    "AndroidExceptionPreHandler",
):
    assert marker in api21_test, f"Debug ServiceLoader regression guard missing: {marker}"

# Signing must fail closed if apksigner still reports any V1-unprotected META-INF entry.
assert 'verify --verbose --min-sdk-version 21 signed/VeyraVault-release.apk 2>&1' in workflow
assert 'grep -Fq "not protected by signature" <<< "$VERIFY_OUTPUT"' in workflow

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
print("PASS: Only known build metadata is excluded; ServiceLoader resources are preserved in Debug.")
print("PASS: Unsigned Release APK audit rejects every non-directory META-INF entry.")
print("PASS: API-21 Debug instrumentation still validates both coroutine service descriptors.")
print("PASS: Signing fails closed if apksigner reports any V1-unprotected META-INF entry.")
print("PASS: CloneStore remains the active production persistence source; no Room provider caller exists.")
