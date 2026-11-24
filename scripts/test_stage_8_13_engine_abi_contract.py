#!/usr/bin/env python3
"""Fail-closed source contract for the pinned Engine's known ABI limits.

This is a source audit plus a Python model of the audited Java decision paths.
The ZIP fixtures are synthetic; this is not Android runtime or physical-device
compatibility testing. Known unsafe behavior is characterized explicitly so CI
cannot mistake a green source audit for x86 support.
"""
from pathlib import Path
import tempfile
import zipfile
import subprocess

root = Path("build_workspace")
app_gradle = root / "app" / "build.gradle"
bcore_gradle = root / "Bcore" / "build.gradle"
abi_utils = root / "Bcore" / "src/main/java/top/niunaijun/blackbox/utils/AbiUtils.java"
native_utils = root / "Bcore" / "src/main/java/top/niunaijun/blackbox/utils/NativeUtils.java"
copy_executor = root / "Bcore" / "src/main/java/top/niunaijun/blackbox/core/system/pm/installer/CopyExecutor.java"
package_manager = root / "Bcore" / "src/main/java/top/niunaijun/blackbox/core/system/pm/BPackageManagerService.java"
package_installer = root / "Bcore" / "src/main/java/top/niunaijun/blackbox/core/system/pm/BPackageInstallerService.java"

required_files = (
    app_gradle,
    bcore_gradle,
    abi_utils,
    native_utils,
    copy_executor,
    package_manager,
    package_installer,
)
for path in required_files:
    assert path.is_file(), f"Expected pinned Engine/workspace source missing: {path}"

app = app_gradle.read_text(encoding="utf-8")
bcore = bcore_gradle.read_text(encoding="utf-8")
abi = abi_utils.read_text(encoding="utf-8")
native = native_utils.read_text(encoding="utf-8")
copy = copy_executor.read_text(encoding="utf-8")
pm = package_manager.read_text(encoding="utf-8")
installer = package_installer.read_text(encoding="utf-8")

# Release packaging must remain explicit: both ARM ABIs are built; this does
# not certify either ABI on a physical device.
assert 'abiFilters "armeabi-v7a", "arm64-v8a"' in app, (
    "Expected VeyraVault ARM release ABI filters"
)
assert "armeabi-v7a" in bcore and "arm64-v8a" in bcore, (
    "Pinned Bcore Gradle configuration no longer declares both ARM ABIs"
)

# Pin the known ABI decision: process bitness, not merely device capability,
# determines which target native ABI is accepted by this Engine build.
for token in ("arm64-v8a", "armeabi-v7a", "armeabi"):
    assert token in abi, f"Expected ARM ABI recognition missing: {token}"
assert "Process.is64Bit()" in (
    root / "Bcore/src/main/java/top/niunaijun/blackbox/BlackBoxCore.java"
).read_text(encoding="utf-8"), "Engine host process bitness source changed"
assert "if (abiUtils.isEmptyAib())" in abi and "return true;" in abi, (
    "The no-recognized-ABI decision changed; review before updating this contract"
)
assert '"x86"' not in abi and "x86_64" not in abi, (
    "Pinned Engine ABI parser changed: review x86 support and fail-closed behavior"
)

# Native extraction currently tries one Build.CPU_ABI and then only generic
# armeabi. The fallback's boolean result is ignored by this void method.
assert "Build.CPU_ABI" in native, "Native extraction ABI selection changed"
assert 'findAndCopyNativeLib(zipfile, "armeabi", nativeLibDir);' in native, (
    "Legacy native extraction fallback changed; review it"
)
assert "SUPPORTED_ABIS" not in native, (
    "Native extraction now iterates supported ABIs; review ordering/fallback semantics"
)
assert "NativeUtils.copyNativeLib(new File(ps.pkg.baseCodePath)" in copy, (
    "Installer native extraction input changed; review split-aware semantics"
)
assert "splitSourceDirs" not in copy, (
    "Installer now references split APKs; require end-to-end split install review"
)
assert "boolean support = AbiUtils.isSupport(apkFile);" in pm, (
    "Package-manager ABI preflight call changed"
)
assert "CopyExecutor" in installer and "if (exec != 0)" in installer, (
    "Package installer executor result handling changed"
)

# Reproduce the audited AbiUtils prefix order with synthetic APK ZIP entries.
# The generic 'lib/armeabi' prefix is checked before 'lib/armeabi-v7a', so
# v7a is recorded as generic armeabi. The current 32-bit predicate still
# accepts it, but the classification loses ABI precision.
def current_engine_abi_set(entries):
    found = set()
    for name in entries:
        if name.startswith("lib/arm64-v8a"):
            found.add("arm64-v8a")
        elif name.startswith("lib/armeabi"):
            found.add("armeabi")
        elif name.startswith("lib/armeabi-v7a"):
            found.add("armeabi-v7a")
    return found


def current_engine_accepts(entries, host_is_64_bit):
    found = current_engine_abi_set(entries)
    if not found:
        # This is also the path taken for unknown architectures such as x86.
        return True
    if host_is_64_bit:
        return "arm64-v8a" in found
    return "armeabi" in found or "armeabi-v7a" in found


def make_apk_fixture(entries):
    temp_dir = tempfile.TemporaryDirectory()
    apk_path = Path(temp_dir.name) / "fixture.apk"
    with zipfile.ZipFile(apk_path, "w") as apk:
        for entry in entries:
            apk.writestr(entry, b"synthetic-native-fixture")
    with zipfile.ZipFile(apk_path, "r") as apk:
        names = apk.namelist()
    return temp_dir, names


def current_native_extract_helper_succeeds(entries, device_cpu_abi):
    # Mirrors the helper's boolean: it returns True for an APK with no lib/
    # entries (fast skip), or when a matching requested/legacy ABI is found.
    # This does not mean libraries from an unpassed split APK were examined.
    if not any(name.startswith("lib/") for name in entries):
        return True
    requested = f"lib/{device_cpu_abi}/"
    legacy = "lib/armeabi/"
    requested_match = any(
        name.startswith(requested) and name.endswith(".so") for name in entries
    )
    legacy_match = any(
        name.startswith(legacy) and name.endswith(".so") for name in entries
    )
    return requested_match or legacy_match


fixtures = {
    "pure_java": ["classes.dex"],
    "armv7_only": ["classes.dex", "lib/armeabi-v7a/libfixture.so"],
    "arm64_only": ["classes.dex", "lib/arm64-v8a/libfixture.so"],
    "arm_dual": [
        "classes.dex",
        "lib/armeabi-v7a/libfixture.so",
        "lib/arm64-v8a/libfixture.so",
    ],
    "x86_only": ["classes.dex", "lib/x86/libfixture.so"],
    "x86_64_only": ["classes.dex", "lib/x86_64/libfixture.so"],
}

fixture_names = {}
fixture_dirs = []
try:
    for fixture_name, entries in fixtures.items():
        temp_dir, names = make_apk_fixture(entries)
        fixture_dirs.append(temp_dir)
        fixture_names[fixture_name] = names

    assert current_engine_accepts(fixture_names["pure_java"], False)
    assert current_engine_accepts(fixture_names["pure_java"], True)
    assert current_engine_accepts(fixture_names["armv7_only"], False)
    assert not current_engine_accepts(fixture_names["armv7_only"], True)
    assert current_engine_accepts(fixture_names["arm64_only"], True)
    assert not current_engine_accepts(fixture_names["arm64_only"], False)
    assert current_engine_accepts(fixture_names["arm_dual"], False)
    assert current_engine_accepts(fixture_names["arm_dual"], True)

    assert current_engine_abi_set(fixture_names["armv7_only"]) == {"armeabi"}
    assert current_engine_abi_set(fixture_names["x86_only"]) == set()
    assert current_engine_abi_set(fixture_names["x86_64_only"]) == set()

    # Characterize (do not approve) the false-positive: x86-only packages are
    # treated like pure-Java packages by isEmptyAib(), then no ARM .so is found.
    for fixture_name in ("x86_only", "x86_64_only"):
        assert current_engine_accepts(fixture_names[fixture_name], False)
        assert current_engine_accepts(fixture_names[fixture_name], True)
        assert not current_native_extract_helper_succeeds(fixture_names[fixture_name], "armeabi-v7a")
        assert not current_native_extract_helper_succeeds(fixture_names[fixture_name], "arm64-v8a")

    # Split-only native libraries are not supplied to CopyExecutor: its source
    # is baseCodePath only. This fixture documents the path gap, not APK install
    # behavior across PackageManager/device versions.
    base_temp, base_names = make_apk_fixture(["classes.dex"])
    split_temp, split_names = make_apk_fixture(["lib/arm64-v8a/libfixture.so"])
    fixture_dirs.extend((base_temp, split_temp))
    assert current_engine_accepts(base_names, True)
    assert current_native_extract_helper_succeeds(base_names, "arm64-v8a")
    assert current_native_extract_helper_succeeds(split_names, "arm64-v8a")
    assert not any(name.endswith(".so") for name in base_names)
    assert any(name.endswith(".so") for name in split_names)
finally:
    for temp_dir in fixture_dirs:
        temp_dir.cleanup()

print("Stage 8.13 Engine ABI source contract: PASS")
print("Synthetic ABI decision fixtures: PASS (source-behavior model only)")
print("Known gap: x86/x86_64-only APKs can pass the current empty-recognized-ABI gate")
print("Known gap: unmatched native ABI extraction can return without a failure signal")
print("Known gap: CopyExecutor reads baseCodePath only; split native inputs are not staged")
print("ARM release packaging: armeabi-v7a + arm64-v8a (physical runtime not certified)")
print("Split APK Engine installation and physical-device Engine launch: NOT CERTIFIED")

# Compile and execute the actual production NativeAbiPolicy.java using javac.
# This validates the decision logic, not Android PackageManager or native loading.
project_root = Path(__file__).resolve().parents[1]
policy_source = project_root / "app/src/main/java/com/veyravault/space/core/NativeAbiPolicy.java"
preflight_source = project_root / "app/src/main/java/com/veyravault/space/core/NativeAbiPreflight.java"
add_app_source = project_root / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java"
async_repository_source = project_root / "app/src/main/java/com/veyravault/space/core/AsyncCloneRepository.java"
engine_source = project_root / "app/src/main/java/com/veyravault/space/core/Engine.java"
instrumentation_source = project_root / "app/src/androidTest/java/com/veyravault/space/core/NativeAbiPreflightInstrumentationTest.java"

for path in (
    policy_source, preflight_source, add_app_source,
    async_repository_source, engine_source, instrumentation_source
):
    assert path.is_file(), f"Native ABI preflight implementation/test missing: {path}"

policy = policy_source.read_text(encoding="utf-8")
preflight = preflight_source.read_text(encoding="utf-8")
add_app = add_app_source.read_text(encoding="utf-8")
async_repository = async_repository_source.read_text(encoding="utf-8")
engine = engine_source.read_text(encoding="utf-8")
instrumentation = instrumentation_source.read_text(encoding="utf-8")

assert "ApplicationInfo.splitSourceDirs" in preflight or "info.splitSourceDirs" in preflight
assert "info.sourceDir" in preflight and "new ZipFile(sourcePath)" in preflight
assert "Process.is64Bit()" in preflight
assert 'Class.forName("dalvik.system.VMRuntime")' in preflight
assert "CloneStore." not in preflight and "installPackageAsUser(" not in preflight
assert "NativeAbiPreflight.inspectInstalledPackage(appContext, packageName)" in async_repository
assert "enqueue(() -> NativeAbiPreflight.inspectInstalledPackage" in async_repository
assert "repository.inspectNativeAbi(app.pkg" in add_app
assert add_app.index("repository.inspectNativeAbi(app.pkg") < add_app.index("repository.reserveNextUserId(app.pkg"), (
    "ABI preflight must complete before reserving a Clone ID"
)
assert "Engine.installPackageAsUser(this, entry.packageName, entry.userId, preflight)" in add_app
assert "preflight.matchesInstalledPackage(context, pkg)" in engine
assert engine.index("preflight.matchesInstalledPackage(context, pkg)") < engine.index(
    'getMethod("installPackageAsUser", String.class, int.class)'
), "Engine must revalidate the package fingerprint before installation"
assert "NativeAbiPreflight.inspectInstalledPackage(ctx, entry.packageName)" in engine
assert "NATIVE_ABI_PREFLIGHT_BLOCKED:" in engine
assert "ALWAYS" not in policy  # guard against accidental placeholder implementation
assert "REJECT_SPLIT_APK" in policy
assert "REJECT_EXTRACTOR_ABI_MISSING" in policy
assert "UNKNOWN_APK_METADATA" in policy
assert "debugHarnessApkIsReadAsPureJava" in instrumentation
assert "missingPackageMetadataFailsClosed" in instrumentation
assert "matchesInstalledPackage" in instrumentation

harness = r"""
import com.veyravault.space.core.NativeAbiPolicy;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

public final class NativeAbiPolicyContractTest {
    private static Set<String> abis(String... values) {
        return new HashSet<String>(Arrays.asList(values));
    }

    private static void expect(NativeAbiPolicy.Decision actual,
                               NativeAbiPolicy.Decision expected, String label) {
        if (actual != expected) {
            throw new AssertionError(label + ": expected " + expected + " but got " + actual);
        }
    }

    private static NativeAbiPolicy.Result evaluate(
            Set<String> dirs, int splits, NativeAbiPolicy.HostBitness bitness,
            String primary, boolean readable) {
        return NativeAbiPolicy.evaluate(dirs, splits, bitness, primary, readable);
    }

    public static void main(String[] args) {
        NativeAbiPolicy.HostBitness b32 = NativeAbiPolicy.HostBitness.BIT_32;
        NativeAbiPolicy.HostBitness b64 = NativeAbiPolicy.HostBitness.BIT_64;
        NativeAbiPolicy.HostBitness unknown = NativeAbiPolicy.HostBitness.UNKNOWN;

        NativeAbiPolicy.Result pureJava = evaluate(Collections.<String>emptySet(), 0,
                unknown, null, true);
        expect(pureJava.getDecision(), NativeAbiPolicy.Decision.ALLOW_PURE_JAVA,
                "pure-Java APK remains compatible without a known process bitness");
        if (!pureJava.isAllowed()) throw new AssertionError("pure-Java APK must be allowed");

        expect(evaluate(abis("arm64-v8a"), 0, b64, "arm64-v8a", true).getDecision(),
                NativeAbiPolicy.Decision.ALLOW_ARM64, "ARM64-only APK on 64-bit ARM Engine");
        expect(evaluate(abis("armeabi-v7a"), 0, b32, "armeabi-v7a", true).getDecision(),
                NativeAbiPolicy.Decision.ALLOW_ARM32, "ARMv7-only APK on 32-bit ARM Engine");
        expect(evaluate(abis("armeabi"), 0, b32, "armeabi-v7a", true).getDecision(),
                NativeAbiPolicy.Decision.ALLOW_ARM32, "generic armeabi extractor fallback");
        expect(evaluate(abis("arm64-v8a", "armeabi-v7a"), 0, b64, "arm64-v8a", true).getDecision(),
                NativeAbiPolicy.Decision.ALLOW_ARM64, "dual ARM APK on 64-bit process");
        expect(evaluate(abis("arm64-v8a", "armeabi-v7a"), 0, b32, "armeabi-v7a", true).getDecision(),
                NativeAbiPolicy.Decision.ALLOW_ARM32, "dual ARM APK on 32-bit process");

        expect(evaluate(abis("armeabi-v7a"), 0, b64, "arm64-v8a", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_HOST_BITNESS_MISMATCH,
                "32-bit-only APK on 64-bit Engine process");
        expect(evaluate(abis("arm64-v8a"), 0, b32, "armeabi-v7a", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_HOST_BITNESS_MISMATCH,
                "64-bit-only APK on 32-bit Engine process");
        expect(evaluate(abis("arm64-v8a", "armeabi-v7a"), 0, b32, "arm64-v8a", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_HOST_BITNESS_MISMATCH,
                "process bitness disagrees with Build.CPU_ABI extractor selection");
        expect(evaluate(abis("armeabi-v7a"), 0, b32, "armeabi", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_EXTRACTOR_ABI_MISSING,
                "Engine extractor has no v7a fallback when primary ABI is generic armeabi");

        expect(evaluate(abis("x86"), 0, b32, "armeabi-v7a", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_UNSUPPORTED_NATIVE_ABI,
                "x86-only APK on ARM host");
        expect(evaluate(abis("x86_64"), 0, b64, "arm64-v8a", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_UNSUPPORTED_NATIVE_ABI,
                "x86_64-only APK on ARM host");
        expect(evaluate(abis("arm64-v8a"), 0, b64, "x86_64", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_UNSUPPORTED_HOST_ABI,
                "unsupported x86_64 host architecture");
        expect(evaluate(abis("riscv64"), 0, b64, "arm64-v8a", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_UNSUPPORTED_NATIVE_ABI,
                "unknown native ABI must not be treated as pure Java");

        expect(evaluate(Collections.<String>emptySet(), 1, b64, "arm64-v8a", true).getDecision(),
                NativeAbiPolicy.Decision.REJECT_SPLIT_APK,
                "split package is blocked even when base is pure Java");
        expect(evaluate(null, 0, unknown, null, false).getDecision(),
                NativeAbiPolicy.Decision.UNKNOWN_APK_METADATA,
                "unreadable APK fails closed");
        expect(evaluate(abis("arm64-v8a"), 0, unknown, "arm64-v8a", true).getDecision(),
                NativeAbiPolicy.Decision.UNKNOWN_HOST_BITNESS,
                "unknown process bitness fails closed for native APK");

        if (NativeAbiPolicy.bitnessForAbi("arm64-v8a") != b64
                || NativeAbiPolicy.bitnessForAbi("armeabi-v7a") != b32
                || NativeAbiPolicy.bitnessForAbi("unknown") != unknown) {
            throw new AssertionError("ABI bitness classification changed");
        }

        System.out.println("PASS: NativeAbiPolicy production Java decision matrix.");
        System.out.println("PASS: pure-Java, ARM32/ARM64, x86, split, unreadable and unknown cases.");
        System.out.println("PASS: Extractor-primary ABI and process-bitness mismatches fail closed.");
    }
}
"""

with tempfile.TemporaryDirectory(prefix="veyravault-native-abi-policy-") as temp:
    temp_path = Path(temp)
    harness_path = temp_path / "NativeAbiPolicyContractTest.java"
    harness_path.write_text(harness, encoding="utf-8")
    compile_result = subprocess.run(
        ["javac", "-encoding", "UTF-8", "-d", str(temp_path),
         str(policy_source), str(harness_path)],
        cwd=project_root, text=True, capture_output=True
    )
    if compile_result.returncode != 0:
        raise SystemExit(compile_result.stdout + compile_result.stderr)
    run_result = subprocess.run(
        ["java", "-cp", str(temp_path), "NativeAbiPolicyContractTest"],
        cwd=project_root, text=True, capture_output=True
    )
    if run_result.returncode != 0:
        raise SystemExit(run_result.stdout + run_result.stderr)
    print(run_result.stdout, end="")
