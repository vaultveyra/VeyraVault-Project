#!/usr/bin/env python3
"""Fail-closed source contract for the pinned Engine's currently known ABI limits.

This is a source audit, not a runtime compatibility test. It deliberately records
known constraints so upstream Engine changes require explicit review before CI
can silently start making broader compatibility claims.
"""
from pathlib import Path

root = Path("build_workspace")
app_gradle = root / "app" / "build.gradle"
bcore_gradle = root / "Bcore" / "build.gradle"
abi_utils = root / "Bcore" / "src/main/java/top/niunaijun/blackbox/utils/AbiUtils.java"
native_utils = root / "Bcore" / "src/main/java/top/niunaijun/blackbox/utils/NativeUtils.java"
copy_executor = root / "Bcore" / "src/main/java/top/niunaijun/blackbox/core/system/pm/installer/CopyExecutor.java"

for path in (app_gradle, bcore_gradle, abi_utils, native_utils, copy_executor):
    assert path.is_file(), f"Expected pinned Engine/workspace source missing: {path}"

app = app_gradle.read_text(encoding="utf-8")
bcore = bcore_gradle.read_text(encoding="utf-8")
abi = abi_utils.read_text(encoding="utf-8")
native = native_utils.read_text(encoding="utf-8")
copy = copy_executor.read_text(encoding="utf-8")

# Release packaging must remain explicit: both ARM ABIs are built; this does
# not certify either ABI on a physical device.
for token in ('abiFilters "armeabi-v7a", "arm64-v8a"',):
    assert token in app, f"Expected VeyraVault ARM release ABI filters: {token}"
assert "armeabi-v7a" in bcore and "arm64-v8a" in bcore,     "Pinned Bcore Gradle configuration no longer declares both ARM ABIs"

# The pinned Engine's ABI helper remains ARM-focused. Any upstream change must
# trigger review of process bitness, ELF loading, native dependencies and tests.
for token in ("arm64-v8a", "armeabi-v7a", "armeabi"):
    assert token in abi, f"Expected ARM ABI recognition missing: {token}"
assert "x86_64" not in abi and '"x86"' not in abi,     "Pinned Engine ABI helper changed: review x86 support before changing this contract"

# Native extraction currently chooses a single ABI with a legacy fallback.
assert "Build.CPU_ABI" in native, "Native extraction ABI selection changed; review it"
assert "armeabi" in native, "Expected legacy native extraction fallback changed"
assert "SUPPORTED_ABIS" not in native,     "Native extraction now iterates supported ABIs; review ordering/fallback semantics"

# The pinned installer currently passes only baseCodePath into native extraction.
assert "NativeUtils.copyNativeLib(new File(ps.pkg.baseCodePath)" in copy,     "Installer native extraction input changed; review split-aware semantics"
assert "splitSourceDirs" not in copy,     "Installer now references split APKs; require end-to-end split install review"

print("Stage 8.13 Engine ABI source contract: PASS")
print("Confirmed scope: ARM release packaging and current pinned Engine behavior only")
print("x86/x86_64 production support: NOT CERTIFIED")
print("Split APK native extraction: NOT CERTIFIED")
print("Physical-device native loading and Clone launch: NOT TESTED")
