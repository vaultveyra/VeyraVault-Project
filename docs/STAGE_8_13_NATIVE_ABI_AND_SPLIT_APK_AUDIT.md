# Stage 8.13 — Native ABI and package topology source audit

**Status: read-only source audit completed. No runtime code, ABI filters, CloneStore records, virtual package data, account/session data, or Engine pin was changed.**

## Scope

Continue Stage 8.12 by inspecting the VeyraVault workspace generator, app manifest, the exact pinned NewBlackbox Engine source, and the current diagnostic/launch integration.

- VeyraVault branch: `feat/veyra-vault-product-foundation`
- Pinned Engine: `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`
- Reference device: Huawei Y7 2019 DUB-LX1, Android 8.1.0 / API 27, EMUI 8.2.0, Snapdragon 450, approximately 3 GB RAM.
- PR #4 must remain open and Draft. Do not modify `main`.

## Confirmed source findings

### 1. Release ABI packaging is ARM-only

The generated app Gradle file and the pinned Engine's `Bcore/build.gradle` configure `armeabi-v7a` and `arm64-v8a`. The Debug test configuration separately selects x86_64 and excludes packaged native libraries; this is an emulator test harness, not proof of a packaged x86_64 production Engine.

The pinned Engine's `AbiUtils` recognizes ARM ABI directory names only. It does not recognize x86 or x86_64. Therefore, x86/x86_64 production support is not established and must not be claimed by changing ABI filters alone.

### 2. Clone native bitness is coupled to the Engine host process

In the pinned Engine, `AbiUtils.isSupport()` chooses either the 64-bit or 32-bit ABI test according to `BlackBoxCore.is64Bit()`. On Android M and later, that method uses `Process.is64Bit()`; on older releases it uses `Build.CPU_ABI.equals("arm64-v8a")`.

Consequently, an APK containing native libraries only for the bitness opposite to the Engine host process can be rejected even if the physical device advertises support for both 32-bit and 64-bit ABIs. This is an Engine architecture constraint requiring a separately designed and tested solution; it is not safe to work around by weakening the ABI check.

### 3. Native library extraction has a narrow ABI fallback

Pinned `NativeUtils.copyNativeLib()` first searches the base APK using `Build.CPU_ABI`, then falls back only to the directory named `armeabi`. It does not iterate the device's ordered supported ABI list and does not explicitly fall back to `armeabi-v7a`.

The pinned `CopyExecutor` calls this function with `ps.pkg.baseCodePath`. This is a concrete compatibility risk for APKs whose native libraries do not match the single selected ABI or are supplied in configuration splits. The actual impact depends on process bitness and the target APK's packaging; it must be reproduced before changing the implementation.

### 4. ABI parser branch ordering is misleading

In pinned `AbiUtils`, the check for `name.startsWith("lib/armeabi")` occurs before `name.startsWith("lib/armeabi-v7a")`. Thus an `armeabi-v7a` entry is classified into the generic `armeabi` set first. The current boolean 32-bit predicate still returns true, so this is a classification defect/maintainability hazard, not by itself proof of a failed install.

### 5. Split APK handling remains unproven

The current diagnostics inspect the base APK and split APKs separately and report split counts/ABI metadata. The pinned Engine install/extraction path inspected in the previous compatibility audit is base-APK-oriented. A diagnostic that sees split APKs does not mean the Engine installs or loads them.

Do not silently accept a base-only install for a package whose required code or native libraries reside in splits. A safe split-aware change requires an end-to-end design for package parsing, base/split staging, ABI selection, native-library extraction, package settings, install ordering, rollback and recovery.

### 6. Device eligibility is not device certification

The reference Huawei reports Android API 27, above the currently observed app minSdk 21. This only establishes manifest-level minimum API eligibility. The screenshot does not establish whether the installed OS is 32-bit or 64-bit. The Snapdragon 450's capabilities must not be used as a substitute for reading the handset's actual supported ABIs and process bitness.

## Required next engineering work

1. Add focused tests around the pinned Engine ABI decision using synthetic APK fixtures for:
   - arm64-only native libraries;
   - armeabi-v7a-only native libraries;
   - APKs containing both ARM ABIs;
   - APKs with no native libraries;
   - x86/x86_64-only libraries;
   - native libraries located in split APKs rather than the base APK.
2. Design a safe Engine process/ABI strategy so a device with both ARM ABIs can run compatible 32-bit and 64-bit target apps without mixing native libraries across process bitness.
3. Design split-aware installation as a separate reviewed unit, with transactional staging and rollback. Keep current base-only behavior fail-closed for packages that cannot be installed completely.
4. Preserve unknown-vs-absent distinctions in diagnostics and installation state.
5. Validate on physical API 27 Huawei Y7 and representative ARMv7/ARM64 devices before marking either ABI path certified.
6. Keep the existing CloneStore, virtual package data, credentials, account/session state and app-private data untouched during all compatibility tests.

## Explicit non-actions

- No ABI filters were broadened.
- No x86/x86_64 production support was claimed.
- No pinned Engine source or revision was modified.
- No Split APK installer patch was attempted.
- No minSdk, targetSdk or compileSdk values were changed.
- No CloneStore or Room runtime behavior was changed.
- No device reset, Clone removal, reinstall or app-data clearing was performed.

## Evidence boundary

The source findings above are static source observations. They do not prove a failure on the user's Huawei handset or on Chrome, Instagram, or Soroush. Per-app root causes remain unconfirmed until real package metadata, Engine trace events and physical-device outcomes are collected.
