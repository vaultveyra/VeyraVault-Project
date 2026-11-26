#!/usr/bin/env python3
"""Build the tiny CPU preflight libraries independently of the pinned Engine NDK."""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "build_workspace"
NDK_VERSION = "23.2.8568313"
SDK_ROOTS = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
             "/usr/local/lib/android/sdk"]

def fail(message):
    raise SystemExit("NEON probe build failed: " + message)

def main():
    sdk = next((Path(p) for p in SDK_ROOTS if p and (Path(p) / "ndk" / NDK_VERSION).is_dir()), None)
    if sdk is None:
        fail("Pinned side-by-side NDK {} is not installed".format(NDK_VERSION))
    toolchain = sdk / "ndk" / NDK_VERSION / "toolchains" / "llvm" / "prebuilt" / "linux-x86_64"
    clang = toolchain / "bin" / "clang++"
    sysroot = toolchain / "sysroot"
    source = ROOT / "app" / "src" / "main" / "cpp" / "VeyraNeonProbe.cpp"
    if not clang.is_file() or not source.is_file() or not (WORKSPACE / "app").is_dir():
        fail("NDK compiler, probe source, or prepared app workspace is missing")
    output_root = WORKSPACE / "app" / "src" / "main" / "jniLibs"
    targets = [
        ("armeabi-v7a", "armv7a-linux-androideabi21",
         ["-march=armv7-a", "-mfpu=vfpv3-d16", "-mfloat-abi=softfp"]),
        ("arm64-v8a", "aarch64-linux-android21", ["-march=armv8-a"]),
        # Debug-only test ABI: returns UNKNOWN and is never shipped in Release.
        ("x86_64", "x86_64-linux-android21", ["-march=x86-64"]),
    ]
    for abi, target, cpu_flags in targets:
        output_dir = output_root / abi
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / "libveyra_neon_probe.so"
        command = [str(clang), "--target=" + target, "--sysroot=" + str(sysroot),
                   "-std=c++17", "-O2", "-fPIC", "-shared", "-fno-exceptions",
                   "-fno-rtti", "-fno-vectorize", "-fno-slp-vectorize",
                   "-Wl,--no-undefined", "-Wl,-soname,libveyra_neon_probe.so"] + cpu_flags + [
                   str(source), "-o", str(output)]
        print("[+] Building {} probe with NDK {}: {}".format(abi, NDK_VERSION, " ".join(command)))
        subprocess.run(command, check=True)
        if not output.is_file() or output.stat().st_size == 0:
            fail("Compiler did not produce " + str(output))
        print("[+] Created {}".format(output))
    print("[+] Probe built independently; pinned Engine continues to use its configured NDK.")

if __name__ == "__main__":
    main()
