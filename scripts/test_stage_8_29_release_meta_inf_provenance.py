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

# Debug still proves ServiceLoader resources are discoverable on API 21.
for marker in (
    "META-INF/services/",
    "kotlinx.coroutines.internal.MainDispatcherFactory",
    "kotlinx.coroutines.CoroutineExceptionHandler",
    "AndroidDispatcherFactory",
    "AndroidExceptionPreHandler",
):
    assert marker in api21

# Record the exact dependency paths from the Release runtime configuration.
for marker in (
    "Inspect Release runtime dependency provenance",
    "--configuration releaseRuntimeClasspath --dependency kotlinx-coroutines-android",
    "--configuration releaseRuntimeClasspath --dependency kotlinx-coroutines-core",
    "--configuration releaseRuntimeClasspath --dependency androidx.room:room-runtime",
):
    assert marker in workflow, f"Missing dependency provenance diagnostic: {marker}"

# Keep the package and signer gates fail-closed until the resources are explained.
assert "outside V1 integrity coverage" in audit
assert 'grep -Fq "not protected by signature" <<< "$VERIFY_OUTPUT"' in workflow
assert doc.is_file()

print("PASS: Release VCS metadata is explicitly disabled through AGP BuildType VcsInfo.")
print("PASS: Packaging uses current AGP resources DSL and exact metadata exclusions only.")
print("PASS: ServiceLoader resources remain in API-21 Debug tests and are not blindly excluded.")
print("PASS: CI records Release runtime dependencyInsight for Coroutines and Room.")
print("PASS: APK audit and V1 signing warning guards remain fail-closed.")
