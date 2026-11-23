# Stage 8.14 — ABI classification and Engine process-architecture design

**Status: read-only design audit completed. No runtime code, ABI filters, Engine pin, CloneStore, virtual package data, account/session data, or Room runtime behavior was changed.**

## Scope and controlling constraints

- Repository: `vaultveyra/VeyraVault-Project`
- Branch: `feat/veyra-vault-product-foundation`
- Parent checkpoint: `274f0eb27981da89dddbc5046536d3cc65621e09`
- PR #4 remains open, Draft and unmerged; do not modify `main`.
- Pinned Engine: `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`.
- Release ABI filters remain `armeabi-v7a` and `arm64-v8a`.
- Reference device: Huawei Y7 2019 DUB-LX1, Android 8.1 / API 27. Physical-device validation has not been performed.

This stage turns the Stage 8.13 source observations into a process/ABI decision and a test plan. It does not implement an ABI workaround.

## 1. Newly confirmed ABI-classification defect

Pinned source: `Bcore/src/main/java/top/niunaijun/blackbox/utils/AbiUtils.java`.

The current parser recognizes ARM directory names only. Its branch order is:

1. `lib/arm64-v8a...`
2. `lib/armeabi...`
3. `lib/armeabi-v7a...`

Because the generic `armeabi` prefix check occurs before the `armeabi-v7a` check, a v7a entry is classified as generic `armeabi`; the later v7a branch is unreachable for normal v7a paths. The current boolean 32-bit predicate still returns true for this classification, so this ordering defect alone does not prove an install failure.

A more important semantic problem follows from the same ARM-only scan:

- x86/x86_64-only native directories are not added to the recognized set.
- A valid APK containing only x86/x86_64 native libraries can therefore leave the recognized set empty.
- `isSupport()` returns true when that set is empty, treating “no recognized ABI found” as “APK has no native libraries”.

Those states are not equivalent. An APK with no `lib/<abi>/*.so` entries may be ABI-neutral; an APK with native libraries for an unsupported ABI is not ABI-neutral. The current helper does not preserve that distinction.

The constructor also catches ZIP parsing exceptions and leaves the set empty. The package-manager path performs an earlier archive-info check, but the ABI helper itself still conflates malformed/unreadable input with an empty recognized set. The future contract must model parse failure separately.

**Required correction direction (not implemented):** classify the complete set of native ABI directories independently of the Engine's supported ABI set, then return a typed decision such as `NO_NATIVE_LIBRARIES`, `SUPPORTED_ABI_MATCH`, `UNSUPPORTED_ABI_ONLY`, `MIXED_ABI_NO_MATCH`, or `INVALID_ARCHIVE`. A boolean-only helper is insufficient for diagnostics and safe install decisions.

## 2. Engine process bitness is host-process scoped

Pinned source: `BlackBoxCore.is64Bit()` delegates to `Process.is64Bit()` on Android M+ and uses `Build.CPU_ABI.equals("arm64-v8a")` on older supported releases.

Pinned source: `BPackageManagerService.installPackageAsUserLocked()` calls `AbiUtils.isSupport(apkFile)` before parsing/installing the package. The ABI decision is therefore based on the Engine host process bitness, not a separately selected bitness for each target Clone.

Pinned source: `BProcessManagerService.startProcessLocked()` allocates a free proxy process slot and initializes the app process through that slot. The Engine manifest declares a server process and proxy Activity processes `:p0` through `:p31`. These are process slots within the same installed host application package; the inspected source does not define a per-Clone ABI selector or a 32-bit/64-bit slot pool.

Consequences:

- Adding more proxy process slots does not by itself create a second process architecture.
- Assigning one slot number to 32-bit targets and another to 64-bit targets is not a valid design without proving that Android can launch those components at the requested bitness and that the host package/Engine supports it.
- Weakening the ABI gate would not make a 32-bit Engine load 64-bit native libraries, or vice versa.
- A device that supports both ARM ABIs is not, by that fact alone, proof that one installed Engine host can execute both target process bitnesses.

## 3. Current build topology and validation boundary

The workspace generator currently writes:

- Release ABI filters: `armeabi-v7a`, `arm64-v8a`.
- Debug ABI filter: `x86_64`.
- Debug JNI packaging excludes `**/*.so`.
- Release includes the pinned `:Bcore` project; Debug uses `debugCompileOnly project(':Bcore')` for the Room-only instrumentation harness.

Therefore the x86_64 Debug emulator test lane intentionally does not package or execute the production ARM Engine native libraries. It cannot certify x86_64 Engine support, ARM native loading, or cross-bitness Clone execution.

CI run #1035 (run ID `45225674207`) on parent commit `274f0eb27981da89dddbc5046536d3cc65621e09` completed successfully. The build/audit job and isolated signing job both reported success; the Stage 8.13 source-contract step completed. This is build/source-contract evidence, not runtime ABI certification. The APK signing job's success does not, by itself, verify that its certificate fingerprint matches the intended release key.

## 4. Architecture options and decision

### Option A — Single-bitness Engine host per installation

The installed VeyraVault host and all of its Engine proxy processes use the architecture selected for that installed host package. A target APK is admitted only when its native requirements are compatible with that Engine process, or when it has no native libraries.

- Advantages: smallest change; one host data directory; no cross-package clone-state synchronization; preserves the current process and storage model.
- Limitations: a target with native libraries only for the opposite bitness remains unsupported on that installation, even if the physical device CPU supports both ABIs.
- Safety: incompatible or ambiguous APKs must fail closed with a truthful diagnostic; never silently proceed as if they were ABI-neutral.

This is the only option consistent with the currently inspected process topology without introducing a second host architecture.

### Option B — Separate 32-bit and 64-bit Engine host packages

This could potentially provide two host process architectures on devices that support both, but it is a major architecture change, not an ABI-filter edit.

Before considering it, design and prove:

- distinct package identity and install/update lifecycle for each host architecture;
- authenticated, least-privilege IPC between hosts;
- a single authoritative owner for CloneStore and profile state;
- stable Clone/Space identity across hosts;
- safe access to virtual package files without copying or resetting user data;
- account/session continuity and process-death recovery;
- cross-host install/uninstall locking and transactional coordination;
- upgrade, rollback, backup and recovery behavior;
- prevention of concurrent mutation of the same Clone.

Separate Android package sandboxes do not automatically share app-private files or SharedPreferences. A dual-host proposal must not duplicate or independently mutate CloneStore and must not require users to reinstall or reset existing Clones. No such design is approved by this stage.

### Option C — Native translation/bridge

No evidence in the pinned Engine or current VeyraVault build establishes a supported ARM32↔ARM64 or x86↔ARM translation layer. This option is not assumed available and is not a permissible shortcut around ABI checks.

### Stage decision

Proceed with Option A as the safe baseline for the current architecture. Keep Option B as a separately gated research track only if broad mixed-bitness support is a product requirement and a non-destructive data/IPC architecture can be proven. Do not implement Option B or C in this stage.

## 5. Required ABI test fixtures

Build deterministic synthetic APK ZIP fixtures and test the parser/decision contract independently of device execution.

| Fixture | Required semantic result |
|---|---|
| Valid APK with no `lib/` entries | `NO_NATIVE_LIBRARIES`; eligible for ABI-neutral path |
| ARM64-only native libraries | Match only a 64-bit Engine |
| ARMv7-only native libraries | Match only a 32-bit Engine |
| Both ARM64 and ARMv7 libraries | Match the current Engine process ABI and select only that ABI's libraries |
| x86-only native libraries | `UNSUPPORTED_ABI_ONLY` for current ARM-only Engine; must not be treated as no-native |
| x86_64-only native libraries | `UNSUPPORTED_ABI_ONLY` for current ARM-only Engine; must not be treated as no-native |
| Mixed ARM + x86 libraries | Select a compatible ARM ABI; do not copy unrelated ABI directories |
| Empty, truncated or invalid ZIP | `INVALID_ARCHIVE`; must not be treated as no-native |
| Directory-like names such as `lib/armeabi-v7a-extra/` | Must not be accepted as an exact ABI directory |
| ARM libraries only in a split APK | Deferred to Stage 8.15; base-only path must not claim complete installation |

Tests must assert both the decision and the exact set of libraries selected/copied. They must not depend on the current machine's `Build.CPU_ABI`; the Engine bitness/ABI environment should be injected or represented by explicit test inputs.

## 6. Native extraction contract required before implementation

The current `NativeUtils.copyNativeLib()`:

- chooses `Build.CPU_ABI` as its first candidate;
- falls back only to `armeabi`;
- does not iterate a verified ordered ABI candidate list;
- returns no typed result describing no libraries, unsupported ABI, successful extraction, or partial failure;
- is called by `CopyExecutor` using `ps.pkg.baseCodePath`.

Before changing it, define a pure selection function and a transactional extraction API. The selection function must receive the actual Engine process bitness and a verified ABI capability list; it must not infer process bitness from a device marketing specification. Extraction must stage into a temporary directory, verify expected library names and sizes/checksums, and only then publish the selected set. Failure must leave the previously active native library directory intact.

Split APK source enumeration and merge rules belong to Stage 8.15 and must not be improvised in this stage.

## 7. Cross-cutting install safety blocker

The pinned `CreatePackageExecutor` currently deletes `BEnvironment.getAppDir(packageName)` before recreating the package and library directories. This is a destructive install/update behavior within the Engine's app directory.

This stage does not prove that this directory contains CloneStore or account/session data. It does establish that a future split/native extraction patch must not assume the destination is disposable. Stage 8.15 must first map exact directory ownership and add staged install plus rollback semantics before modifying this executor. Do not run destructive tests against existing user Clones.

## 8. Acceptance gates before ABI implementation

1. Typed ABI classification distinguishes no-native, unsupported-native, supported-native and invalid archive.
2. Exact ABI directory parsing is covered, including v7a branch ordering and x86-only false-positive cases.
3. Process bitness is an explicit input to the decision and is sourced from the actual Engine process.
4. Extraction selects only the ABI compatible with that process and reports complete/failed outcomes.
5. Failure cannot overwrite the last known-good native library directory.
6. No x86/x86_64 production support is claimed until compatible Engine native binaries and end-to-end tests exist.
7. Both ARM32 and ARM64 paths pass real Engine native-load tests on matching physical devices.
8. The Huawei DUB-LX1's actual OS bitness and supported ABI list are read from the handset before selecting its expected path; Snapdragon 450 capability alone is not used as proof.
9. CloneStore, virtual package data, credentials, accounts, sessions and app-private data remain intact.
10. PR #4 remains open and Draft; all changes remain on the feature branch; `main` is not modified.

## 9. Explicit non-actions

- No runtime Java/Kotlin/C/C++ code changed.
- No ABI filters were broadened or narrowed.
- No Engine revision or dependency was changed.
- No x86/x86_64 production support was claimed.
- No Split APK installer was implemented.
- No SDK levels or manifest process declarations were changed.
- No CloneStore, virtual package data, account/session data or Room runtime was changed.
- No physical-device test was performed.
- No certificate fingerprint comparison was performed.

## Next stage

Stage 8.15 should audit package source topology and install-directory ownership, then design a transactional base+split staging and rollback protocol. Only after that design is accepted should implementation begin. The ABI parser/extraction changes should remain a separate implementation unit with the fixtures in Section 5.
