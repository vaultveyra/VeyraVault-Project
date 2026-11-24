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


def current_native_lib_match(entries, device_cpu_abi):
    # Mirrors findAndCopyNativeLib: the Engine searches the requested ABI and
    # then generic armeabi. A ZIP with no lib/ entries is a valid no-native app.
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
        assert not current_native_lib_match(fixture_names[fixture_name], "armeabi-v7a")
        assert not current_native_lib_match(fixture_names[fixture_name], "arm64-v8a")

    # Split-only native libraries are not supplied to CopyExecutor: its source
    # is baseCodePath only. This fixture documents the path gap, not APK install
    # behavior across PackageManager/device versions.
    base_names = ["classes.dex"]
    split_names = ["lib/arm64-v8a/libfixture.so"]
    assert current_engine_accepts(base_names, True)
    assert not current_native_lib_match(base_names, "arm64-v8a")
    assert current_native_lib_match(split_names, "arm64-v8a")
finally:
    for temp_dir in fixture_dirs:
        temp_dir.cleanup()

print("Stage 8.13 Engine ABI source contract: PASS")
print("Synthetic ABI decision fixtures: PASS (source-behavior model only)")
print("Known gap: x86/x86_64-only APKs can pass the current empty-recognized-ABI gate")
print("Known gap: unmatched native ABI extraction can return without a failure signal")
print("Known gap: CopyExecutor reads baseCodePath only; split native inputs are not staged")
print("ARM release packaging: armeabi-v7a + arm64-v8a (physical runtime not certified)")
print("Split APK support and physical-device Engine launch: NOT CERTIFIED")
