# Stage 8.31 — Native ELF ABI and minimum-API compatibility

## Signed Release artifact evidence

The signed Release APK from commit `cc4f9c230c15361ae52679d40773d7089d7293c7` was extracted and inspected. Both Engine libraries contain `.note.android.ident` metadata reporting Android API 21 and NDK r27 build 12077973:

- `lib/armeabi-v7a/libblackbox.so`: ELF32, EM_ARM, Android API 21.
- `lib/arm64-v8a/libblackbox.so`: ELF64, EM_AARCH64, Android API 21.

The package contains both required Engine libraries. The API-21 and API-34 CI suites and the Stage 8.30 Release inventory/signing gates passed on that build.

## Application.mk / Gradle alignment

The immutable pinned Engine contains `APP_PLATFORM := android-24` in `Bcore/src/main/cpp/Application.mk`, while its root Gradle configuration sets `minSdk = 21` and its native module uses Gradle `externalNativeBuild`.

Android's NDK documentation says that with Gradle `externalNativeBuild`, `APP_PLATFORM` should not be set directly; the module's `minSdkVersion` should control the native target. It warns that a native platform higher than the application's minimum can make libraries fail to load on older devices.

Stage 8.31 removes only the stale `APP_PLATFORM` assignment from the generated, ephemeral build workspace. The pinned upstream Engine checkout is not changed. The generated app and Engine-root Gradle minSdk values must agree or packaging fails.

## APK native ELF audit

The Release APK audit decodes ELF headers and `.note.android.ident` directly. It verifies:

- Both required Engine ABI paths are present.
- `armeabi-v7a` is ELF32 / EM_ARM.
- `arm64-v8a` is ELF64 / EM_AARCH64.
- Every packaged native library has valid Android API metadata.
- Every native library API target is less than or equal to the effective application minSdk.
- Duplicate paths, malformed ELF files, missing Engine ABIs and unsupported ABIs fail closed.

Synthetic fixtures cover valid API-21 libraries, API-24 rejection against minSdk 21, wrong ELF class/machine, malformed ELF, a missing Engine ABI and an unsupported ABI.

## ARMv7 NEON boundary

The 32-bit library reports `Tag_Advanced_SIMD_arch: NEONv1` and `Tag_VFP_arch: VFPv3`. Android's NDK enables NEON by default for ARM ABIs. Android documentation says almost all ARMv7 devices support NEON, including all devices that shipped with API 21 or later; older devices upgraded to API 21 can still be exceptions. The current Java Native ABI preflight checks ABI and process bitness; it does not yet prove NEON CPU support before Engine execution.

Accordingly, the API-21 ELF target is now verified, but universal support for every historically manufactured ARMv7 CPU is not claimed. A later hardware-readiness stage should add a safe pre-load NEON capability gate or verify a non-NEON 32-bit build, if supported by the immutable Engine and its Dobby libraries.

## Supported ABI and hardware boundary

The Release Engine currently packages `armeabi-v7a` and `arm64-v8a`. It does not package x86 or x86_64 Engine libraries. API-21/API-34 emulator tests validate Android/Java behavior, not physical ARM native execution. Huawei DUB-LX1 and other physical ARM devices remain untested.

## Safety and scope

Only generated workspace preparation, APK auditing, CI tests and engineering documentation change. The pinned Engine source, CloneStore, Room state, user Clone data, accounts, credentials and sessions are not modified.
