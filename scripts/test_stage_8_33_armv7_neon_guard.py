#!/usr/bin/env python3
"""Contract tests for the independently cross-compiled, fail-closed NEON probe."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
prepare_path = ROOT / "scripts/prepare_workspace.py"
prepare = prepare_path.read_text(encoding="utf-8")
prepare_ast = ast.parse(prepare, filename=str(prepare_path))
build_path = ROOT / "scripts/build_neon_probe.py"
build = build_path.read_text(encoding="utf-8")
ast.parse(build, filename=str(build_path))
cpp = (ROOT / "app/src/main/cpp/VeyraNeonProbe.cpp").read_text(encoding="utf-8")
java = (ROOT / "app/src/main/java/com/veyravault/space/core/NativeNeonProbe.java").read_text(encoding="utf-8")
vault_app = (ROOT / "app/src/main/java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
engine = (ROOT / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
host = (ROOT / "app/src/main/java/com/veyravault/space/core/HostCpuCompatibility.java").read_text(encoding="utf-8")
audit = (ROOT / "scripts/audit_apk.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")
instrumentation = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/NativeNeonPolicyInstrumentationTest.java").read_text(encoding="utf-8")
doc = ROOT / "docs/STAGE_8_33_ARMV7_NEON_RUNTIME_GUARD.md"

assert not any(node.name == "prepare_armv7_neon_probe" for node in prepare_ast.body if isinstance(node, ast.FunctionDef))
assert "prepare_armv7_neon_probe" not in prepare and "CPU_FEATURES_" not in prepare
assert 'NDK_VERSION = "27.0.12077973"' in prepare
assert 'NDK_VERSION = "23.2.8568313"' in build
assert '"-mfpu=vfpv3-d16"' in build and '"-mfloat-abi=softfp"' in build
assert '"-fno-vectorize"' in build and '"-fno-slp-vectorize"' in build
assert '("armeabi-v7a", "armv7a-linux-androideabi21"' in build
assert '("arm64-v8a", "aarch64-linux-android21"' in build
assert "jniLibs" in build and "LOCAL_ARM_NEON" not in build

assert "getauxval(AT_HWCAP)" in cpp
assert "HWCAP_NEON (1UL << 12)" in cpp
assert "errno == ENOENT || hwcap == 0" in cpp
assert "#if defined(__aarch64__)" in cpp and "return 1;" in cpp
assert "cpu_features" not in cpp
assert 'System.loadLibrary("veyra_neon_probe")' in java
assert "LinkageError" in java and "cachedStatus = UNKNOWN" in java
assert "HostCpuCompatibility.initialize()" in vault_app
assert vault_app.index("HostCpuCompatibility.initialize()") < vault_app.index("Engine.doAttachBaseContext(this, localized)")
assert "if (!HostCpuCompatibility.isEngineSupported()) return null;" in engine
assert "if (!HostCpuCompatibility.isEngineSupported()) return;" in engine
assert '"armeabi-v7a".equalsIgnoreCase(primaryAbi)' in host

assert "verify_neon_probe_elf" in audit
assert "lib/armeabi-v7a/libveyra_neon_probe.so" in audit
assert "Tag_Advanced_SIMD_arch: NEON" in audit
assert "Independent ARMv7 preflight probe is built without NEON." in audit
assert "Install isolated NDK r23 for baseline CPU probe" in workflow
assert "Build independent ARMv7/ARM64 NEON probe" in workflow
assert "build_neon_probe.py" in workflow
assert 'yes | "$SDKMANAGER" --licenses' not in workflow
assert "android-ndk-license" in workflow
assert "Test Stage 8.33 ARMv7 NEON preflight guard" in workflow

for expected in (
    "arm64HostAbiIsAcceptedWithoutOptionalArmv7Probe",
    "armv7RequiresPositiveRuntimeNeonDetection",
    "armv7WithoutNeonIsRejected",
    "unknownArmv7CapabilityFailsClosed",
    "unsupportedHostAbiIsRejected",
    "genericArmeabiIsRejectedBecauseReleaseDoesNotPackageIt",
    "processBitnessMismatchIsRejectedBeforeEngineStartup",
    "unknownProcessBitnessFailsClosed",
):
    assert expected in instrumentation
assert doc.is_file()
print("PASS: Engine workspace no longer injects the Probe into Engine ndk-build.")
print("PASS: dedicated NDK r23.2 compiler builds ARMv7 baseline and ARM64 Probe libraries.")
print("PASS: ARMv7 uses AT_HWCAP/HWCAP_NEON and treats missing evidence as unknown.")
print("PASS: Java startup gate executes before Engine initialization and fails closed.")
print("PASS: APK audit requires both ABI probes and rejects ARMv7 Probe NEON attributes.")
