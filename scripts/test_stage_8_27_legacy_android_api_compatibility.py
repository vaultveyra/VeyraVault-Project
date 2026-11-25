#!/usr/bin/env python3
"""Contracts for the Stage 8.27 minimum-API and legacy-signature validation."""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "prepare_workspace.py"
SPEC = importlib.util.spec_from_file_location("veyra_prepare_stage_827", PREPARE_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)

app_gradle = (ROOT / "app" / "build.gradle").read_text(encoding="utf-8")
prepare_source = PREPARE_PATH.read_text(encoding="utf-8")
workflow = (ROOT / ".github" / "workflows" / "build-and-audit.yml").read_text(encoding="utf-8")
preflight = (ROOT / "app/src/main/java/com/veyravault/space/core/NativeAbiPreflight.java").read_text(encoding="utf-8")
date_formatter = (ROOT / "app/src/main/java/com/veyravault/space/core/DashboardDateFormatter.java").read_text(encoding="utf-8")
policy_source = ROOT / "app/src/main/java/com/veyravault/space/core/NativeAbiPolicy.java"
date_source = ROOT / "app/src/main/java/com/veyravault/space/core/DashboardDateFormatter.java"
instrumentation_path = ROOT / "app/src/androidTest/java/com/veyravault/space/core/LegacyApi21CompatibilityInstrumentationTest.java"
docs_path = ROOT / "docs/STAGE_8_27_LEGACY_ANDROID_API21_COMPATIBILITY.md"

assert "minSdkVersion 21" in app_gradle
assert "JavaVersion.VERSION_1_8" in app_gradle
assert 'app_java_ver = detect_app_java_version(os.path.join(ROOT, "app", "build.gradle"))' in prepare_source
assert "sourceCompatibility JavaVersion.{app_java_ver}" in prepare_source
assert "targetCompatibility JavaVersion.{app_java_ver}" in prepare_source
assert "java_ver = m.group(1)" not in prepare_source, (
    "Engine Java 21 must not overwrite VeyraVault app Java 8 source compatibility."
)

# Prove the detector reads the app module's own Gradle file and cannot inherit
# a different Engine module's Java level.
with tempfile.TemporaryDirectory(prefix="veyra-stage-827-") as temp:
    app_fixture = Path(temp) / "app.gradle"
    engine_fixture = Path(temp) / "Bcore.gradle"
    app_fixture.write_text(
        "android { compileOptions { sourceCompatibility JavaVersion.VERSION_1_8 } }",
        encoding="utf-8",
    )
    engine_fixture.write_text(
        "android { compileOptions { sourceCompatibility JavaVersion.VERSION_21 } }",
        encoding="utf-8",
    )
    assert prepare.detect_app_java_version(str(app_fixture)) == "VERSION_1_8"
    assert prepare.detect_app_java_version(str(engine_fixture)) == "VERSION_21"
assert prepare.detect_app_java_version(str(ROOT / "app" / "build.gradle")) == "VERSION_1_8"

# Newer framework API calls must remain behind their introduction-level guards.
assert "if (Build.VERSION.SDK_INT >= 33)" in preflight
assert "if (Build.VERSION.SDK_INT >= 23)" in preflight
assert 'Class.forName("dalvik.system.VMRuntime")' in preflight
assert "Math.floorDiv(" not in date_formatter
assert "Math.floorMod(" not in date_formatter
assert instrumentation_path.is_file()
instrumentation = instrumentation_path.read_text(encoding="utf-8")
for marker in (
    'assertEquals("This test must run on Android API 21", 21, Build.VERSION.SDK_INT)',
    "NativeAbiPreflight.inspectInstalledPackage",
    "matchesInstalledPackage",
    "META-INF/services/",
    "AndroidDispatcherFactory",
    "AndroidExceptionPreHandler",
):
    assert marker in instrumentation, f"Missing API-21 runtime coverage: {marker}"

# CI must exercise both the declared minimum API and the API-34 instrumentation image.
api21 = workflow[workflow.index("Run Android API 21 legacy compatibility smoke tests"):]
assert "api-level: 21" in api21
assert "arch: x86_64" in api21
assert "LegacyApi21CompatibilityInstrumentationTest" in api21
assert "api-level: 34" in workflow

# Explicit signature policy: V1 for API 21/22 and V2/V3 for newer Android releases.
for marker in (
    "--v1-signing-enabled true",
    "--v2-signing-enabled true",
    "--v3-signing-enabled true",
    "--min-sdk-version 21",
    "Verified using v1 scheme (JAR signing): true",
    "Verified using v2 scheme (APK Signature Scheme v2): true",
    "Verified using v3 scheme (APK Signature Scheme v3): true",
):
    assert marker in workflow, f"Missing release signature assertion: {marker}"

# Do not strip ServiceLoader descriptors; they are runtime resources.
assert "META-INF/services/" not in prepare_source
assert docs_path.is_file()

# Compile production Java-only policy/date logic at the app's configured Java 8 level.
with tempfile.TemporaryDirectory(prefix="veyra-stage-827-javac-") as temp:
    result = subprocess.run(
        ["javac", "--release", "8", "-encoding", "UTF-8", "-d", temp,
         str(policy_source), str(date_source)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise SystemExit(result.stdout + result.stderr)

print("PASS: App Java compatibility is read from app/build.gradle and isolated from Engine Java 21.")
print("PASS: Android API 23/33 calls are guarded; API-21-specific test covers the legacy path.")
print("PASS: ServiceLoader resources remain packaged and are checked on an API-21 emulator.")
print("PASS: CI explicitly verifies V1, V2 and V3 signatures for minSdk 21.")
print("PASS: Native ABI policy and date formatter compile under Java 8.")
