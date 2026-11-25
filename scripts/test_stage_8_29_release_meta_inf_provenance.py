#!/usr/bin/env python3
"""Stage 8.29 contracts for Release metadata controls and dependency provenance."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
prepare = (ROOT / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")
audit = (ROOT / "scripts/audit_apk.py").read_text(encoding="utf-8")
api21 = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/LegacyApi21CompatibilityInstrumentationTest.java").read_text(encoding="utf-8")
doc = ROOT / "docs/STAGE_8_29_RELEASE_META_INF_PROVENANCE.md"

assert "vcsInfo {{" in prepare
assert "include = false" in prepare
assert "packagingOptions {{" not in prepare
assert "packaging {{" in prepare
assert "resources {{" in prepare
assert "excludes += [" in prepare
for marker in (
    '"META-INF/*.version"',
    '"META-INF/com/android/build/gradle/app-metadata.properties"',
    '"META-INF/version-control-info.textproto"',
):
    assert marker in prepare
assert "META-INF/**" not in prepare
assert "META-INF/services/" not in prepare

# Debug still proves both ServiceLoader resources and provider classes on API 21.
for marker in (
    "META-INF/services/",
    "kotlinx.coroutines.internal.MainDispatcherFactory",
    "kotlinx.coroutines.CoroutineExceptionHandler",
    "AndroidDispatcherFactory",
    "AndroidExceptionPreHandler",
):
    assert marker in api21

# Record exact dependency paths from the generated Release runtime configuration.
for marker in (
    "Inspect Release runtime dependency provenance",
    "--configuration releaseRuntimeClasspath --dependency kotlinx-coroutines-android",
    "--configuration releaseRuntimeClasspath --dependency kotlinx-coroutines-core",
    "--configuration releaseRuntimeClasspath --dependency androidx.room:room-runtime",
):
    assert marker in workflow, f"Missing dependency provenance diagnostic: {marker}"

# Stage 8.30 supersedes the original blanket META-INF rejection with an exact policy.
for marker in (
    "EXPECTED_META_INF_ENTRIES",
    "REQUIRED_SERVICE_PROVIDERS",
    "validate_meta_inf_entries",
    "Unexpected META-INF entries",
):
    assert marker in audit
assert "outside V1 integrity coverage" not in audit
assert "UNPROTECTED_WARNINGS=" in workflow
assert "not protected by signature" in workflow
for signature in (
    "Verified using v1 scheme (JAR signing): true",
    "Verified using v2 scheme (APK Signature Scheme v2): true",
    "Verified using v3 scheme (APK Signature Scheme v3): true",
):
    assert signature in workflow
assert doc.is_file()

print("PASS: Release VCS metadata is disabled with AGP BuildType VcsInfo.")
print("PASS: Current AGP resources DSL uses exact metadata exclusions only.")
print("PASS: API-21 Debug ServiceLoader descriptors and provider classes remain covered.")
print("PASS: CI captures Coroutines and Room dependency provenance for releaseRuntimeClasspath.")
print("PASS: Stage 8.30 exact META-INF policy and V1/V2/V3 verification supersede the impossible blanket V1 warning ban.")
