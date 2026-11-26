# Stage 8.33 — ARMv7 NEON runtime preflight guard

## Risk and startup order

The pinned Engine packages an ARMv7 libblackbox.so whose ELF attributes declare Advanced SIMD / NEON. NEON is optional on ARMv7, while the Engine's native build enables it. ABI and process bitness checks alone therefore do not establish that an ARMv7 host can safely execute the Engine library.

The ordering is critical: the pinned Engine's NativeCore class loads libblackbox.so in a static initializer. The guard must run before Engine.doAttachBaseContext; a check made only when a user adds a Clone would happen too late.

## Implementation contract

- Build a separate libveyra_neon_probe.so in the temporary Engine workspace. It is not linked into or merged with libblackbox.so.
- Keep the Probe separate from the pinned Engine. For the `armeabi-v7a` module only, set `LOCAL_ARM_NEON := false` (the documented ndk-build per-module opt-out) and compile the Probe's C and C++ sources with `-mfpu=vfpv3-d16`. Do not apply that ARMv7 flag to the ARM64 build. Only the ARMv7 Probe includes Google's C99 runtime CPU-feature implementation. The isolated ARMv7 module selects cpu_features' `HAVE_STRONG_GETAUXVAL` path: Android's `getauxval()` is available from API 18, so the project's API 21 minimum can use `<sys/auxv.h>` directly instead of the optional `dlopen` fallback. This also ensures the ELF auxiliary-vector `AT_HWCAP` constants come from the NDK headers.
- Pin google/cpu_features to immutable commit 4814778e45acc394b37ca0837441ad32a2305bb1 and verify its repository URL, HEAD, and clean worktree before copying its sources and Apache-2.0 license into the ephemeral workspace.
- Read ARMv7 feature flags using cpu_features::GetArmInfo(). A positive NEON result allows the ARMv7 Engine; an explicit negative result rejects it; an unknown or unloadable probe also rejects it.
- Accept arm64-v8a directly because Advanced SIMD is mandatory for the Android arm64 ABI. A 32-bit process on ARM64-capable hardware still probes its active ARMv7 execution ABI rather than assuming that the 64-bit ABI list proves NEON in 32-bit mode.
- Run the gate in VaultApp.attachBaseContext before Engine initialization. Resolve the actual process bitness and fail closed on unknown or mismatched process/ABI state. Add a second guard to Engine core resolution and lifecycle entry points, and apply the same host check before Clone reservation.
- Debug instrumentation omits the Release Engine native runtime and uses a pure-Java test path.
- The APK audit requires the probe library for both packaged ABIs, verifies the pinned Engine's ARMv7 NEON attribute, and rejects a NEON attribute in the independent ARMv7 probe.

## Validation boundary

- Pure policy instrumentation covers ARM64, ARMv7 supported, unsupported, unknown, unsupported host ABI, and generic armeabi cases.
- CI must cross-compile the probe for both ARM ABIs, verify that the ARMv7 module has `LOCAL_ARM_NEON := false` and `-mfpu=vfpv3-d16`, inspect the packaged ELF attributes to prove the probe contains no NEON, and run the existing API 21/API 34 suites and APK audits.
- Android emulator x86_64 does not exercise the real ARMv7 hardware path. A physical ARMv7 device without NEON is still needed to validate the negative hardware case.
- Huawei DUB-LX1 has not been physically tested. The actual ABI and runtime outcome must be read from the handset before making a compatibility claim.
- The probe does not load libblackbox.so, install or launch target apps, reserve Clone IDs, or read/write CloneStore data.

No main-branch change, PR merge, Room activation, Clone data mutation, or account/session mutation is part of this stage.


## CI follow-up — cpu_features Android auxiliary-vector configuration

The first Release compile after the NEON probe was introduced reached the ARMv7 Probe but failed because the pinned `google/cpu_features` Android fallback path expected `AT_HWCAP`, `AT_HWCAP2`, `AT_PLATFORM`, and `AT_BASE_PLATFORM` definitions that were not supplied by its `HAVE_DLFCN_H` branch in this ndk-build integration. The Probe now selects `HAVE_STRONG_GETAUXVAL`, which includes `<sys/auxv.h>` and calls Android libc `getauxval()` directly. This is compatible with the app's minSdk 21 because Android provides `getauxval()` from API 18. The change is isolated to the ARMv7 Probe; it does not alter the pinned Engine source or `libblackbox.so`.

Validation required on the new head: Stage 8.33 contract, API 34/API 21 instrumentation, ARMv7 and ARM64 Release compilation, ELF audit proving the Probe remains non-NEON, and full APK audit. No new APK is considered available until those gates pass.
