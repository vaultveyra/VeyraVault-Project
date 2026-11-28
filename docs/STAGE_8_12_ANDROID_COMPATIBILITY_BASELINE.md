# Stage 8.12 — Android compatibility baseline and validation plan

**Status: source/build audit completed; production compatibility changes and device certification are not yet complete.**

## Purpose

Establish an evidence-based compatibility baseline before changing runtime or native-engine behavior. The goal is broad Android device support, with the user's Huawei Y7 2019 (DUB-LX1, Android 8.1.0 / API 27, EMUI 8.2.0, Snapdragon 450, approximately 3 GB RAM) as the first physical reference device.

This document does not claim universal compatibility. A device/API/ABI combination is supported only after its build, installation, launch, lifecycle, and relevant feature behavior have been validated.

## Confirmed build facts

Inspected on feature branch `feat/veyra-vault-product-foundation`, head commit `55b517730b7b7e5532f40182cfe0e12027b8eaba`:

1. `app/build.gradle` is a workspace template containing generated compile/target SDK placeholders. Its default configuration declares ABI filters `armeabi-v7a` and `arm64-v8a`.
2. `scripts/prepare_workspace.py` generates the actual workspace Gradle configuration. It initializes minimum SDK to 21, derives compile/min SDK and Java compatibility from the pinned Engine build files when present, and currently writes target SDK 28.
3. The 2026-11-23 CI log for run 1029 reported: compileSdk 35, minSdk 21, Java VERSION_21.
4. The same CI release build compiled the native Engine for both `arm64-v8a` and `armeabi-v7a`; the APK audit listed `lib/arm64-v8a/libblackbox.so` and `lib/armeabi-v7a/libblackbox.so`.
5. The Debug instrumentation configuration is intentionally different: it selects `x86_64`, excludes packaged `*.so` files, and uses `debugCompileOnly project(':Bcore')`. The CI emulator therefore exercises the Debug test harness, not the packaged ARM native Engine runtime.
6. The Stage 8.10 audit of pinned Engine revision `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820` found its ABI helper recognizes ARM `arm64-v8a`, `armeabi` and `armeabi-v7a`, but not x86/x86_64 ABI directories.
7. The Stage 8.10 audit found the pinned Engine install path passes the base `sourceDir` APK and does not pass `splitSourceDirs` to its installer. This is a conditional risk for split-installed apps, not a proven cause for Chrome, Instagram or Soroush on any particular device.

## Huawei Y7 2019 reference profile

The user's supplied About Phone screenshot confirms:

- Model: DUB-LX1
- Build: DUB-LX1 8.2.0.192(C185)
- EMUI: 8.2.0
- Android: 8.1.0 (API 27)
- CPU: Qualcomm Snapdragon 450
- RAM: approximately 3 GB
- Total internal storage: approximately 64 GB
- Security patch shown: 2021-01-01

Android API 27 is above the currently observed minSdk 21. This establishes manifest-level minimum-version eligibility only; it does not certify the virtual Engine, native libraries, OEM behavior, or any target Clone on this handset.

## Current validation boundary

CI run 1029 for commit `55b517730b7b7e5532f40182cfe0e12027b8eaba` completed successfully:

- 69/69 Android Emulator instrumentation tests passed; 0 skipped; 0 failed.
- Release APK compilation and source/APK audit steps passed.
- APK audit reported zero forbidden remote log endpoints.
- Release native build tasks ran for ARM64 and ARMv7.
- The uploaded artifact is unsigned in this PR workflow; isolated signing was skipped by pull-request workflow policy.

This CI result is not physical-device certification and does not prove the ARM native Engine executed in the x86_64 Debug emulator. The existing Room instrumentation harness also does not run the complete production `VaultApp.onCreate()` path.

## Compatibility risks that remain open

1. **x86/x86_64 Release support:** not currently packaged; pinned Engine ABI recognition is ARM-focused. Do not add x86 filters or claim x86 support without a compatible Engine build and runtime validation.
2. **Split APK installation:** current pinned Engine install API is base-APK-only. A safe split-aware installer requires end-to-end review of package parsing, package settings, ABI selection, native-library extraction/copying, install-session behavior and rollback.
3. **OEM process/background policies:** Huawei EMUI and other OEM power managers may affect process survival, background execution, permissions and WebView/GMS availability.
4. **WebView and Google Mobile Services:** presence, version and provider behavior vary by device; unknown must not be reported as absent.
5. **Memory pressure:** the Y7's approximately 3 GB RAM requires foreground/background, process recreation and low-memory tests. Do not infer stability from emulator tests alone.
6. **Android API behavior:** minSdk eligibility does not guarantee each feature or permission behaves identically across API levels.
7. **Target app compatibility:** Chrome, Instagram and Soroush need per-app install/launch/process/Activity evidence; no root cause is currently established.

## Required validation matrix

Use representative API levels and physical/OEM devices; expand the matrix when failures indicate a missing class:

| Track | Representative coverage | Required evidence |
|---|---|---|
| Minimum API | API 21 baseline | Install, startup, core navigation, permission paths |
| Legacy API | API 23 and API 27 | Runtime permissions, storage, WebView, lifecycle |
| Reference OEM | Huawei DUB-LX1, API 27, ARMv7/ARM64 OS as reported by device | Real Release install, Engine native load, Clone launch, memory/lifecycle |
| Mid-generation | API 29/30 | Scoped storage and background behavior |
| Recent Android | API 33/34/35 | Notification/runtime permission and modern platform behavior |
| ARM 32-bit | armeabi-v7a device/emulator where Engine runtime is available | Native library load and Engine launch |
| ARM 64-bit | arm64-v8a device | Native library load and Engine launch |
| x86/x86_64 | Only after Engine support decision | Compatible Engine binary and end-to-end runtime proof |
| OEM variation | Huawei/EMUI, Samsung/One UI, Xiaomi/HyperOS, Pixel/AOSP | OEM process, permission, WebView and service behavior |

For each device, record model, Android/API, build fingerprint category (no unique device identifiers), OS bitness, supported ABIs, RAM class, WebView provider/version, GMS state, install outcome, Engine native-load outcome, virtual-process entry, target Application lifecycle, Activity visibility and whether the process remains alive. Redact private/user data.

## Acceptance gates before declaring broad support

- The generated Gradle configuration and merged manifest are reproducible and their min/target/compile SDK values are explicit.
- Release APK contains only ABIs for which the pinned Engine and all native dependencies are actually available.
- Each advertised ABI passes native load and real Engine launch tests; build success alone is insufficient.
- Each declared Android API band passes install, permissions, lifecycle and core UI smoke tests.
- Huawei DUB-LX1 passes real-device Release install, Engine initialization and the three named Clone smoke tests before it is marked certified.
- Split APK handling is either implemented and validated end-to-end or explicitly reported as unsupported for affected packages; never silently install an incomplete package.
- Unknown diagnostics remain distinct from confirmed absence.
- No destructive CloneStore, virtual app data, account/session reset or Room cutover is used for compatibility testing.
- PR #4 remains open and Draft; all work stays on the feature branch; do not modify `main`.

## Next engineering increment

Perform a focused audit of generated/merged SDK configuration, native ABI packaging and runtime loading. Then design a non-destructive ARM physical-device validation path and per-app diagnostics sequence. Do not broaden ABI filters, change minSdk, patch the pinned Engine installer, or alter CloneStore until the required source review and regression tests are ready.
