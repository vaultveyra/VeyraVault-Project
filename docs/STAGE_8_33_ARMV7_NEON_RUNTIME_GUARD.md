# Stage 8.33 — ARMv7 NEON runtime preflight guard

## Risk and startup order

The pinned Engine packages an ARMv7 `libblackbox.so` whose ELF attributes declare Advanced SIMD / NEON. NEON is optional on ARMv7, while the Engine's native build enables it. ABI and process-bitness checks alone therefore do not establish that an ARMv7 host can safely execute the Engine library.

The Engine's NativeCore class loads `libblackbox.so` in a static initializer. The guard must run before `Engine.doAttachBaseContext`; a check made only when a user adds a Clone would happen too late.

## Independent probe build

- The Engine remains pinned to NDK `27.0.12077973`; its source and native build are not modified to accommodate the Probe.
- CI installs NDK `23.2.8568313` side-by-side and invokes `scripts/build_neon_probe.py` after the temporary app workspace is prepared.
- The dedicated script uses the NDK r23 LLVM compiler directly, not ndk-build and not the Engine's `Android.mk`. It emits `libveyra_neon_probe.so` for `armeabi-v7a` and `arm64-v8a` into the app's `jniLibs` directory.
- ARMv7 uses an explicit `armv7-a`, `vfpv3-d16`, and `softfp` target with vectorization disabled. ARM64 is built separately for the Android arm64 ABI, where Advanced SIMD is mandatory.
- The Probe is a minimal JNI C++ source and does not import Google's cpu_features library or link the Engine. ARMv7 reads `AT_HWCAP` through Android libc `getauxval()` and tests `HWCAP_NEON` (bit 12). Missing/empty auxiliary-vector evidence returns UNKNOWN; it is never treated as proof that NEON is absent or present.
- NDK r24 and later reject `LOCAL_ARM_NEON := false`; therefore this setting is not used. NDK r23 is used only for the independent Probe and does not replace the Engine's NDK.
- No change is made to the pinned Engine's `libblackbox.so`. The Debug variant uses `debugCompileOnly` for Bcore and retains only the x86_64 test Probe; it does not package the Engine runtime.

## Runtime policy

- ARM64 is accepted because Advanced SIMD is mandatory for Android's arm64-v8a ABI.
- ARMv7 is accepted only after a positive runtime NEON result. A negative result or unknown/unloadable Probe fails closed.
- A 32-bit process on ARM64-capable hardware probes its active 32-bit execution ABI; it does not infer 32-bit NEON capability solely from a 64-bit ABI listing.
- The gate runs in `VaultApp.attachBaseContext` before Engine initialization. Engine entry points and Clone-install preflight retain their existing guard.
- Debug instrumentation omits the Release Engine native runtime and uses its pure-Java test path.

## Required validation

- Stage 8.33 source-contract test.
- NDK r23 compile for both ARM ABIs.
- ELF audit requires both Probe libraries, verifies that the ARMv7 Engine declares NEON, and rejects a NEON attribute in the ARMv7 Probe.
- Existing native ELF/API audit, API 21 compatibility smoke test, API 34 instrumentation, and full Release APK audit must all pass.
- The Android x86_64 emulator does not exercise real ARMv7 hardware. A physical ARMv7 device without NEON is still needed to validate the negative hardware case.
- Huawei `DUB-LX1` has not been physically tested; read the handset's actual ABI and runtime outcome before making a compatibility claim.

## Safety boundaries

The Probe does not load `libblackbox.so`, install or launch target apps, reserve Clone IDs, or read/write CloneStore data. This stage does not change main, merge PR #4, activate Room, or mutate user Clone/session data.
