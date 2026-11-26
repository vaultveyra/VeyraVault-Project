#!/usr/bin/env python3
"""Source and build-contract tests for the fail-closed ARMv7 NEON startup guard."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

prepare_path = ROOT / "scripts/prepare_workspace.py"
prepare = prepare_path.read_text(encoding="utf-8")
vault_app = (ROOT / "app/src/main/java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
engine = (ROOT / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
policy = (ROOT / "app/src/main/java/com/veyravault/space/core/NativeAbiPolicy.java").read_text(encoding="utf-8")
preflight = (ROOT / "app/src/main/java/com/veyravault/space/core/NativeAbiPreflight.java").read_text(encoding="utf-8")
probe_java = (ROOT / "app/src/main/java/com/veyravault/space/core/NativeNeonProbe.java").read_text(encoding="utf-8")
host_java = (ROOT / "app/src/main/java/com/veyravault/space/core/HostCpuCompatibility.java").read_text(encoding="utf-8")
probe_cpp = (ROOT / "app/src/main/cpp/VeyraNeonProbe.cpp").read_text(encoding="utf-8")
audit = (ROOT / "scripts/audit_apk.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")
instrumentation = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/NativeNeonPolicyInstrumentationTest.java").read_text(encoding="utf-8")
doc = ROOT / "docs/STAGE_8_33_ARMV7_NEON_RUNTIME_GUARD.md"

# Parse, don't just grep, the workspace preparation script and its literal make fragment.
prepare_ast = ast.parse(prepare, filename=str(prepare_path))
probe_function = next(
    node for node in prepare_ast.body
    if isinstance(node, ast.FunctionDef) and node.name == "prepare_armv7_neon_probe"
)
module_assignment = next(
    node for node in ast.walk(probe_function)
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == "module" for target in node.targets)
)
module_text = ast.literal_eval(module_assignment.value)
assert "LOCAL_MODULE := veyra_neon_probe" in module_text
armv7_probe_block = module_text.split("ifeq ($(TARGET_ARCH_ABI),armeabi-v7a)", 1)[1].split("endif", 1)[0]
assert "LOCAL_ARM_NEON := false" in armv7_probe_block
assert "LOCAL_CFLAGS += -mfpu=vfpv3-d16" in module_text
assert "LOCAL_CPPFLAGS += -mfpu=vfpv3-d16" in module_text
armv7_probe_block = module_text.split("ifeq ($(TARGET_ARCH_ABI),armeabi-v7a)", 1)[1].split("endif", 1)[0]
assert "LOCAL_CFLAGS += -mfpu=vfpv3-d16" in armv7_probe_block
assert "LOCAL_CPPFLAGS += -mfpu=vfpv3-d16" in armv7_probe_block
assert module_text.count("-mfpu=vfpv3-d16") == 2
assert any(line.endswith("\\\n") for line in module_text.splitlines(keepends=True))
assert "veyra_cpu_features/src/impl_arm_linux_or_android.c" in module_text
assert "$(LOCAL_PATH)/veyra_cpu_features/include/internal" in module_text
assert "-DHAVE_STRONG_GETAUXVAL" in module_text
assert "-DHAVE_DLFCN_H" not in module_text
assert "LOCAL_LDLIBS += -ldl" not in module_text
assert "-DSTACK_LINE_READER_BUFFER_SIZE=1024" in module_text
assert "LOCAL_MODULE := blackbox" not in module_text

CPU_FEATURES_COMMIT = "4814778e45acc394b37ca0837441ad32a2305bb1"
assert CPU_FEATURES_COMMIT in prepare
assert 'CPU_FEATURES_REPOSITORY = "https://github.com/google/cpu_features.git"' in prepare
assert "prepare_armv7_neon_probe(WORKSPACE)" in prepare
assert "verify_engine_source(WORKSPACE)" in prepare
assert "libblackbox.so is unchanged" in prepare

assert 'System.loadLibrary("veyra_neon_probe")' in probe_java
assert "nativeProbe()" in probe_java
assert "LinkageError" in probe_java
assert "cachedStatus = UNKNOWN" in probe_java
assert "cpu_features::GetArmInfo()" in probe_cpp
assert "info.features.neon" in probe_cpp
assert "hasEvidence" in probe_cpp
assert "#elif defined(__arm__)" in probe_cpp

gate = "HostCpuCompatibility.initialize()"
engine_attach = "Engine.doAttachBaseContext(this, localized)"
assert gate in vault_app and engine_attach in vault_app
assert vault_app.index(gate) < vault_app.index(engine_attach)
assert "if (!HostCpuCompatibility.isEngineSupported()) return null;" in engine
assert "if (!HostCpuCompatibility.isEngineSupported()) return;" in engine
assert "HostCpuCompatibility.initialize()" in preflight
assert "NativeAbiPreflight.resolveHostBitness(primaryAbi)" in host_java
assert "evaluateHostCpu(" in host_java
assert "static NativeAbiPolicy.HostBitness resolveHostBitness(String primaryAbi)" in preflight
assert 'if ("armeabi-v7a".equalsIgnoreCase(primaryAbi))' in host_java

assert "REJECT_ARMV7_NEON_UNSUPPORTED" in policy
assert "UNKNOWN_ARMV7_NEON_CAPABILITY" in policy
assert "REJECT_UNSUPPORTED_ENGINE_HOST_ABI" in policy
assert "evaluateHostCpu(" in policy

assert "verify_neon_probe_elf" in audit
assert "lib/armeabi-v7a/libveyra_neon_probe.so" in audit
assert "Tag_Advanced_SIMD_arch: NEON" in audit
assert "Independent ARMv7 preflight probe is built without NEON." in audit
assert "Test Stage 8.33 ARMv7 NEON preflight guard" in workflow
assert "test_stage_8_33_armv7_neon_guard.py" in workflow

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

print("PASS: workspace preparation script parses and uses an immutable cpu_features source pin.")
print("PASS: the isolated ARMv7 probe disables module NEON and uses VFPv3-D16 compiler flags.")
print("PASS: ARMv7 policy permits only positive runtime NEON detection; unknown fails closed.")
print("PASS: VaultApp checks CPU compatibility before Engine.doAttachBaseContext.")
print("PASS: Engine reflection and Clone-install preflight are guarded before NativeCore can load.")
print("PASS: APK audit requires both probe ABIs and verifies the ARMv7 instruction attributes.")
