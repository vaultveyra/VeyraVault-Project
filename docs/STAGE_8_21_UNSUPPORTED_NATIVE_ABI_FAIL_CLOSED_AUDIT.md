# Stage 8.21 — Pinned Engine unsupported-ABI false-positive audit

**Status: source audit and synthetic ZIP-fixture contract added. No Android runtime, ABI filters, Engine pin, CloneStore data, account/session data, or device state was changed.**

## Scope

This follow-up narrows the Stage 8.13 audit to the exact path from package ABI preflight through native extraction and install-result handling.

- VeyraVault branch: `feat/veyra-vault-product-foundation`
- Pinned Engine: `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`
- Release ABIs configured by the workspace generator: `armeabi-v7a`, `arm64-v8a`
- CI emulator: x86_64 Debug test harness with native libraries excluded; it does not certify the Release Engine.

## Confirmed source findings

### 1. Unknown native ABIs are conflated with apps that have no native libraries

The pinned `AbiUtils` only adds recognized entries for ARM paths. Its `isSupport()` method returns `true` when the recognized ABI set is empty.

That is valid for a pure-Java APK, but the same empty set is produced when an APK contains only `lib/x86/` or `lib/x86_64/` entries because those paths are not recognized by this helper.

**Consequence:** an x86-only or x86_64-only APK can pass this preflight as though it had no native libraries. This is a false-positive compatibility decision, not evidence that the Engine can execute those native libraries.

### 2. Native extraction can fail to find a library without propagating that fact

The pinned `NativeUtils.copyNativeLib()` tries the current `Build.CPU_ABI`, then tries only `armeabi`. It does not iterate `Build.SUPPORTED_ABIS` or search x86 directories.

The method is `void`; it does not turn a final “no matching .so found” result into an exception or an explicit failure status. The boolean returned by the final fallback search is not checked by the caller.

### 3. The install executor can therefore report success after no library was copied

The pinned `CopyExecutor` calls `NativeUtils.copyNativeLib()` using only `ps.pkg.baseCodePath`. It returns an error when an exception is thrown, but a normal no-match result from the current extraction helper does not throw; execution can reach its success return.

The pinned `BPackageInstallerService` checks the executor integer result and continues when it is zero. The package-manager install path then marks the package installed after the installer reports a non-negative result.

**Practical risk:** an x86-only package may appear installed in the virtual package store while its native library was never extracted. If the target later loads that library, runtime loading can fail (for example, with an unresolved native library). This is a source-derived risk; it has not been reproduced on a physical device or tied to a specific target app.

### 4. ARM process bitness remains a separate hard constraint

The pinned `AbiUtils.isSupport()` chooses the 32-bit or 64-bit test according to `BlackBoxCore.is64Bit()`. On Android M and later the Engine reads `Process.is64Bit()`; on older Android versions it compares `Build.CPU_ABI` with `arm64-v8a`.

Therefore:
- an ARMv7-only target is not accepted by a 64-bit Engine process;
- an ARM64-only target is not accepted by a 32-bit Engine process;
- a dual-ABI target may pass the matching bitness gate;
- the physical device's advertised ABI list alone does not prove that the running Engine process can load the target libraries.

This is the current Engine architecture, not a guarantee that the app can run both target bitnesses simultaneously.

### 5. The armeabi-v7a parser branch is shadowed by the generic armeabi prefix

The current branch checks `name.startsWith("lib/armeabi")` before checking `lib/armeabi-v7a`. An armeabi-v7a entry is therefore recorded under the generic `armeabi` label. The current 32-bit predicate still accepts it, so this is presently a loss of ABI specificity rather than an independently proven install failure.

### 6. Split APK native libraries remain outside this extraction path

The current diagnostics can inspect base and split APK ABI directories, but the pinned `CopyExecutor` supplies only `baseCodePath` to native extraction. Seeing native libraries in `splitSourceDirs` does not mean they are staged into the virtual package.

No split-aware installation behavior is claimed.

## Automated verification added

The existing CI-run Stage 8.13 source contract now creates synthetic APK-like ZIP fixtures for:
- pure-Java APK;
- ARMv7-only APK;
- ARM64-only APK;
- dual-ARM APK;
- x86-only APK;
- x86_64-only APK.

It models the audited source decision order and verifies the known false-positive and extraction gaps, while also asserting the related Engine install-call and executor-result paths remain the same.

**Important:** this is a source-behavior characterization test. A green result means the known limitation was detected and recorded; it does not mean x86 is supported, that a native library was loaded by Android, or that a real app launched successfully.

## Safe remediation design — not implemented in this stage

Before changing runtime behavior, implement and review a centralized, read-only native ABI preflight that distinguishes at least:

1. no native libraries (valid pure-Java case);
2. recognized and host-process-compatible ARM libraries;
3. recognized but host-process-incompatible ARM libraries;
4. unsupported/unknown native ABIs (must fail closed, not become “no native libraries”);
5. native libraries located only in splits or in a split not staged by the Engine;
6. unreadable or incomplete APK metadata (must remain unknown/fail closed).

Then connect that result to the Clone install orchestration so unsupported packages are rejected **before** Engine package state is changed. Do not delete or recreate Clone records, and do not clear target app data, credentials, account state, or sessions as part of this check.

A complete split-aware installer requires a separate transactional design covering base/split staging, ABI selection, package parsing, install ordering, native extraction, rollback and crash recovery. A simple loop over `splitSourceDirs` is not sufficient.

The Engine-side extraction path must also return an explicit result and propagate missing-library failures through `CopyExecutor` and `BPackageInstallerService`; otherwise the package manager can still mark an incomplete install as successful.

## Explicit non-actions

- No x86 or x86_64 ABI filters were added.
- No unsupported ABI was represented as supported.
- No Engine source or pinned commit was modified.
- No install/extraction code was patched.
- No Android SDK levels were changed.
- No Room cutover, CloneStore mutation, app-data reset, or account/session operation was performed.
- No physical-device certification is claimed.

## Next gate

Implement the preflight as a separately tested, non-destructive unit first. Add synthetic ZIP tests for base/split and unknown ABIs, then run CI. Only after those pass should the guard be integrated into Clone installation. Physical ARMv7 and ARM64 tests, including the Huawei DUB-LX1/API 27 reference device, remain required before any broad compatibility claim.
