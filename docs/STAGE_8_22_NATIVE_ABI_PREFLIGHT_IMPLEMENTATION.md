# Stage 8.22 — Read-only Native ABI preflight and install guard

**Status (2026-11-24): app-level preflight and Engine install guard are implemented at commit `732317564772613826018296c4c512e0cbda939d`. Push CI run `45439570658` completed successfully on this exact SHA, including Android Emulator instrumentation, source audit, unsigned Release APK build/audit, and isolated signed-artifact job. PR run `45439590270` attempt 1 failed before running any instrumentation tests because the hosted Emulator went offline and Android system services (`package`, `activity`, `settings`) were unavailable; the failed PR job was rerun as attempt 2 and was still in progress at the time this report was updated. No physical-device certification is claimed.**

## Scope and invariant

- Branch: `feat/veyra-vault-product-foundation`
- PR #4 remains Open and Draft; `main` is not modified.
- Pinned Engine remains `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`.
- The preflight must complete before reserving a Clone user ID and before calling the Engine installer.
- The check must not create/delete Clone records, clear target data, or change credentials, accounts, or sessions.

## Implementation

### 1. Pure-Java ABI policy

Added `NativeAbiPolicy` with explicit outcomes:

- `ALLOW_PURE_JAVA`: a readable base APK has no native `.so` entries. This is allowed even when process bitness cannot be read because no native library needs to be loaded.
- `ALLOW_ARM32` / `ALLOW_ARM64`: the target has a library path the pinned Engine can select for the current process and primary ABI.
- `REJECT_SPLIT_APK`: PackageManager reports one or more split APKs. The current Engine package-name installer passes only the base APK path; cloning is blocked rather than creating an incomplete virtual package.
- `REJECT_HOST_BITNESS_MISMATCH`: target native ABI or Engine process bitness does not match the Engine's primary ABI selection.
- `REJECT_EXTRACTOR_ABI_MISSING`: the APK has an ARM ABI the Engine's extractor cannot select through its current `Build.CPU_ABI` plus generic `armeabi` fallback.
- `REJECT_UNSUPPORTED_HOST_ABI` / `REJECT_UNSUPPORTED_NATIVE_ABI`: the host or target native architecture is outside the ARM ABI set supported by this pinned Engine.
- `UNKNOWN_HOST_BITNESS` / `UNKNOWN_APK_METADATA`: the required information is unavailable or unreadable. Unknown is not treated as compatible.

The policy intentionally models the current extraction order, not merely a broad 32/64-bit match:
- For `arm64-v8a`, the base APK must provide `lib/arm64-v8a/*.so`.
- For `armeabi-v7a`, the Engine tries the exact `armeabi-v7a` path, then its generic `armeabi` fallback.
- When the device's primary ABI is generic `armeabi`, a v7a-only APK is rejected because the current Engine does not fall back to `armeabi-v7a`.
- If `Process.is64Bit()` disagrees with `Build.CPU_ABI` bitness, native APKs are rejected. The existing extractor does not select native libraries from the process-matching ABI list.

### 2. Read-only PackageManager/APK adapter

Added `NativeAbiPreflight`:
- Reads the already-installed package's `ApplicationInfo.sourceDir` and `splitSourceDirs`.
- Scans only the base APK ZIP entry names for native `.so` ABI directories when no splits are present.
- Blocks all split-installed packages until the Engine has a complete split-aware installer.
- Uses `Process.is64Bit()` on API 23+.
- On API 21–22, attempts to read the runtime's own bitness via `dalvik.system.VMRuntime.is64Bit()`; if that hidden runtime signal is unavailable, it falls back to the device's primary ABI. The fallback is a compatibility heuristic and is not physical-device certification.
- Captures a package/APK file-stamp snapshot (source paths, file lengths and modification times) and revalidates it immediately before the Engine install call. A changed package snapshot fails closed.
- Does not call Engine installation, CloneStore mutation, uninstall, clear-data, or launch APIs.

### 3. Safe call ordering

The new check is run by `AsyncCloneRepository` on its worker thread.

For Add App / batch clone:
1. Read-only ABI preflight.
2. Reject incompatible, split, or unknown packages immediately.
3. Only for an allowed result, reserve the next Clone ID.
4. Revalidate the package snapshot.
5. Invoke the Engine installer.
6. Commit the Clone record using the existing reservation flow.

Therefore, a package rejected by preflight does not reserve a Clone ID and does not enter Engine installation.

The Engine wrapper now requires a Context and the preflight result, and revalidates that result before reflection invokes the pinned Engine. The Clone launch recovery path also performs preflight before reinstalling a package the Engine explicitly reports as absent.

## Automated tests added

### Host-JVM policy matrix

The Stage 8.13 CI contract compiles and executes the actual production `NativeAbiPolicy.java` with `javac`. It covers:
- pure Java with unknown host bitness;
- ARMv7-only, ARM64-only and dual-ARM APKs;
- 32/64-bit process mismatch;
- primary ABI versus Engine extraction-path mismatch;
- generic `armeabi` fallback and missing v7a fallback;
- x86 and x86_64-only native packages;
- unsupported ABI folder names;
- split APKs, unreadable APK metadata and unknown process bitness.

The existing synthetic APK ZIP fixtures continue to characterize the pinned Engine's original false-positive behavior. A green result means the application guard detects and rejects the unsafe cases; it does not mean the upstream Engine defect itself has been repaired.

### Android instrumentation smoke tests

Added a read-only Android instrumentation test which:
- inspects the debug test APK itself (the Debug build excludes native libraries) and expects a pure-Java allow result;
- verifies the package/APK snapshot matches before installation;
- verifies the same preflight result cannot be reused for another package;
- verifies a missing package returns `UNKNOWN_APK_METADATA` and is not allowed.

These tests do not start the virtualization Engine, install a target app, or mutate Clone data.

### Process-isolation test timing

The isolated app-lock instrumentation test now measures service connection and service response separately:
- isolated process connection deadline: 30 seconds;
- reply deadline after connection: 15 seconds.

This makes a slow process start distinguishable from a connected process that fails to reply. It does not change the security assertion or the credential/session restoration behavior.

## Explicit remaining limitations

1. **No split APK installation:** split packages are currently blocked. Supporting them requires a separate end-to-end transactional Engine change for base/split staging, ABI selection, package parsing, native extraction, install ordering, rollback and process-death recovery.
2. **Pinned Engine defects remain:** x86 paths are still treated as an empty recognized-ABI set by upstream `AbiUtils`; native extraction remains void and does not report a no-match result. The VeyraVault preflight guards the current app entry paths; it does not patch the pinned Engine.
3. **Android 5.x bitness fallback:** where reflective `VMRuntime.is64Bit()` is unavailable, the primary ABI fallback may not perfectly represent the actual process bitness on every old OEM build. API 21–22 physical validation remains mandatory.
4. **Physical-device validation:** ARMv7 and ARM64 install/load/launch have not been certified on physical hardware. The Huawei DUB-LX1/API 27 reference device still requires real Release installation and per-app Clone tests.
5. **Existing installed Clones:** the new guard does not rewrite or delete packages already reported installed by the Engine. No existing Clone data is migrated, cleared, or reset by this stage.
6. **Target app behavior:** passing the preflight means only that the current ABI/split source gate allows the package to reach Engine installation. It does not prove Application startup, account/session isolation, WebView/GMS behavior, or full app compatibility.

## Non-actions

- No ABI filters were broadened.
- No x86/x86_64 production support was added or claimed.
- No Engine upstream source or pinned revision was changed.
- No split installer was implemented.
- No minSdk, targetSdk, compileSdk, Room runtime, or CloneStore schema was changed.
- No Clone record, credential, account, session, or target app data was cleared or reset.
- PR #4 was not merged; `main` was not modified.

## Next acceptance gate

Run the complete CI suite on this commit. If the host-JVM policy contract or Android instrumentation fails, fix that before proceeding. After CI succeeds, perform physical ARMv7 and ARM64 validation, beginning with the API 27 Huawei reference device. Until that evidence exists, describe the preflight as an app-level safety guard—not device certification.


## CI evidence update — 2026-11-24

- Exact tested feature SHA: `732317564772613826018296c4c512e0cbda939d`.
- Push run `45439570658` (run #1136): all jobs completed successfully. The build job passed the contract suite, Room Android instrumentation, source audit, unsigned release compilation, APK audit and artifact upload. The isolated signing job also succeeded.
- Push artifacts: unsigned `14944174166`; signed `14945119649`.
- PR run `45439590270` (run #1137), attempt 1: contract steps passed; the Emulator became offline, Android system services could not be found, and instrumentation reported zero tests executed. The failure is an infrastructure/Emulator boot-service failure, not an app assertion failure.
- Only the failed PR job was rerun. Attempt 2 was in progress at report update time; do not mark PR validation green until its final conclusion is fetched.
- PR #4 remains Open and Draft; no merge or `main` change occurred.
