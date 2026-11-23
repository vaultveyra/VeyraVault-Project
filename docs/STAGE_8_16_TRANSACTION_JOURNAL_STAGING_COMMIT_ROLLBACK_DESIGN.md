# Stage 8.16 — Transaction Journal, Staging, Commit, and Rollback Design

**Status:** Source-confirmed design only. No runtime implementation changes.
**VeyraVault base commit:** `822791ea9c5bef2fd7c698659ed78dada0e0f547`
**Audited Engine:** `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`

## 1. Goal and safety boundary

Stage 8.16 converts the Stage 8.15 finding into an implementable recovery protocol. The target is package-code and package-metadata replacement, not a rewrite of CloneStore or virtual-user storage.

The protocol must preserve the last-known-good package generation through validation, staging, commit, process death, and startup recovery. A transaction must not silently turn a failed metadata write into an apparently successful installation.

No Engine source, generated workspace, runtime Java, build configuration, Engine pin, ABI filter, CloneStore, SharedPreferences data, Room activation, virtual app data, account/session data, or signing configuration was modified in this stage.

## 2. Confirmed VeyraVault entry point and InstallOption

VeyraVault `Engine.installPackageAsUser(pkg, userId)` reflectively invokes the two-argument Engine method:

`BlackBoxCore.installPackageAsUser(String packageName, int userId)`.

At the pinned Engine commit, that method obtains the host-installed package's `ApplicationInfo.sourceDir` and calls the package manager with `InstallOption.installBySystem()`.

The audited flags are:

| Flag | Value | Factory behavior |
|---|---:|---|
| `FLAG_SYSTEM` | 1 | Set by `installBySystem()` |
| `FLAG_STORAGE` | 2 | Set by `installByStorage()`; not set by VeyraVault's current package-name call |
| `FLAG_URI_FILE` | 8 | Added by `makeUriFile()`; not set by the current package-name call |

Consequences for the current VeyraVault path:

1. The Engine parses the host package source APK and performs its ABI support check before calling the installer.
2. `CreateUserExecutor` still runs and deletes only the target virtual user's `data/user/<id>/<package>/lib` child before ensuring the user data directories exist.
3. `CreatePackageExecutor` still deletes the entire shared `data/app/<package>` directory, including its previous `package.conf`, stored base APK if present, and package-wide lib directory.
4. `CopyExecutor` skips native-library extraction when `FLAG_SYSTEM` is set. Since `FLAG_STORAGE` is not set, it also does not copy the base APK to Engine storage. The package's source path remains the host package's `sourceDir`.
5. After the executors return, the package manager marks the target user installed, saves package settings, refreshes component resolution, rescans the package, and emits an installed notification.

Therefore, the current VeyraVault package-name cloning path is a **system-source metadata installation**, not the Engine's file/storage APK-copy path. The package-wide destructive deletion nevertheless occurs in both cases.

## 3. Additional confirmed metadata hazards

### 3.1 Existing user-state map is shared, not copied

`Settings.getPackageLPw()` creates a new `BPackageSettings` and, when an existing package entry is present, assigns the previous `appId` and the previous `userState` map reference to the new settings object.

This is a shallow reference reuse. It is not an isolated snapshot. A later mutation such as `setInstalled(true, userId)` can therefore mutate the map also referenced by the old in-memory package settings before the new package record is durably committed.

A transactional replacement must create an isolated, deep-enough settings snapshot. Package and per-user state objects must not be shared with the active committed generation while a candidate is being prepared.

### 3.2 AtomicFile does not make the package-directory replacement transactional

`BPackageSettings.save()` uses Android `AtomicFile` for the individual `package.conf` file. It returns `true` on success and `false` on a caught write failure.

However, the current package manager ignores that boolean result. It continues to update component resolution and calls `Settings.scanPackage(packageName)`. The previous `package.conf` has already been removed by `CreatePackageExecutor`.

The scanner's `updatePackageLP()` catch path deletes the package directory, removes the package from the in-memory map, kills package processes, and emits an uninstall notification. The install method then continues after the scan call and emits its installed notification; `InstallResult` defaults to `success = true`.

This source flow establishes a concrete false-success risk: if the new settings save fails after the old package directory was deleted, the scan can remove the new directory and in-memory package entry while the outer install method still returns its default-success result. This is a source-level control-flow conclusion; an injected save failure has not yet been run against the Engine.

The individual-file `AtomicFile` protects writes to a file that exists at the target path. It does not restore the package directory that was deleted before that write began.

### 3.3 Per-user data mutation must be separately journaled

The install executor's deletion of the selected user's `lib` child is separate from the package-wide `data/app/<package>` directory. A package transaction must not broaden that operation into deletion of the user's data, cache, files, databases, shared preferences, DE data, external data, profiles, or account/session state.

For replacement of an already-used virtual user, the selected `lib` child must itself have a preservation/rollback policy. For a newly reserved user ID, the transaction must still prove that the target user/package directory is not already owned by an unrelated or unresolved transaction before touching it.

## 4. Required transaction storage layout

Use a dedicated reserved transaction root under the Engine's private data root, on the same filesystem as the package directory. A candidate layout is:

```text
<engine-root>/
  data/
    app/
      <package-name>/                 # active committed package generation
      .veyravault-transactions/       # reserved; never a package
        <transaction-id>/
          journal
          staged-package/
          backup-package/
          staged-user-lib/
          backup-user-lib/
          validation/
```

The exact root may change after filesystem/API verification, but these invariants are mandatory:

- Staging and backup directory renames must be on the same filesystem as the final package directory.
- The scanner must explicitly skip the reserved transaction root and every transaction-owned temporary directory. It must never attempt to parse a transaction directory as a package.
- The journal must live outside the package directory that is being swapped.
- Staging must not be placed inside the active package directory because the current scanner and destructive executor operate on that directory.
- Backup generations must not be deleted until the committed new generation has been re-opened and validated.
- Transaction paths in the journal must be normalized, root-confined relative paths. Reject traversal, symlink escapes, duplicate transaction IDs, and unexpected directory types.

A dedicated transaction root inside Engine's private app-data partition is preferred over a second storage volume. The chosen location must be verified to share the filesystem used by `data/app`; do not assume this from path names alone.

## 5. Journal schema and durable phases

The journal must be versioned and self-validating. Minimum fields:

- journal schema version;
- unique transaction ID;
- package name;
- target virtual user ID, stored locally only when required for recovery;
- install-option flags and source kind (`SYSTEM_SOURCE`, `STORAGE_APK`, or `URI_APK`);
- expected package identity (package name, version code, version name, and signing-certificate/lineage digest);
- normalized relative paths for active, staged, backup, and any per-user-lib generations;
- hashes/lengths for staged package metadata and staged files where applicable;
- prior committed generation identifier or absence marker;
- transaction phase and monotonically increasing phase sequence;
- bounded diagnostic reason code, not raw exception text or private file content.

Write every journal transition with `AtomicFile` (or an equivalently verified durable mechanism), check the returned write outcome, flush the file, and verify the parent-directory durability strategy. Never treat a failed journal write as permission to continue to the next destructive step.

Required phases:

| Phase | Durable meaning | Recovery action |
|---|---|---|
| `PREPARING` | Intent recorded; active package untouched | Validate active generation; discard only unreferenced staging |
| `STAGED_VALIDATED` | Staged package and metadata passed all checks | Keep active generation; commit may begin |
| `OLD_GENERATION_BACKED_UP` | Existing active directory moved to backup | Publish staged generation or restore backup |
| `NEW_GENERATION_PUBLISHED` | Staged directory is active; transaction marker identifies it | Verify package.conf and expected staged identity; complete commit or restore backup |
| `PACKAGE_METADATA_COMMITTED` | New package settings have been written and re-read successfully | Rebuild in-memory package/component state; preserve backup until recovery checks pass |
| `COMPLETE` | New generation is authoritative and post-commit checks succeeded | Backup may be removed; journal may then be retired |

A transaction marker containing the transaction ID and generation digest must be written inside the staged generation **before** publication. It lets recovery distinguish a new active directory from an old or unrelated directory if process death occurs after a directory rename but before the next journal update.

## 6. Commit and rollback protocol

### 6.1 Preflight — no mutation

1. Acquire the Engine install lock and the package-level transaction lock.
2. Recover or refuse to proceed if an unresolved transaction already exists for this package.
3. Validate package identity, archive readability, package/version identity, certificate/signing lineage, and ABI compatibility.
4. For base/split APK inputs, validate the complete split set, package/version consistency, required split dependencies, and native payload in every relevant APK. Do not silently reduce a split set to the base APK.
5. Snapshot the prior package settings, app ID, all virtual-user states, active source path, and relevant generation metadata without sharing mutable maps or state objects.
6. Verify the target virtual user and per-user library path ownership. No CloneStore or app-private user content is read for diagnostic logging.

If preflight fails, return a typed failure without altering active package files or the user's existing data.

### 6.2 Stage — active generation remains untouched

1. Create a unique transaction directory.
2. Build the staged package directory and staged settings independently of the active path.
3. For the current `SYSTEM_SOURCE` path, preserve the source-path semantics: stage a validated metadata generation referring to the host-managed `sourceDir`; do not pretend a private base APK copy has occurred.
4. For `STORAGE_APK` or `URI_APK`, stage the base APK and all supported split artifacts, then stage extracted native libraries using the explicit supported-ABI policy.
5. Apply the target user's installed state to an isolated settings snapshot. Do not mutate the current `mPackages` object's shared user-state map.
6. Stage any required per-user `lib` replacement separately. Do not copy, clear, or migrate the user's other data directories as part of code replacement.
7. Re-open and re-parse staged package metadata; verify signing identity, paths, lengths, hashes, ABI/native outcomes, and package identity.
8. Write and verify the transaction marker, then persist `STAGED_VALIDATED`.

No active package or user library path is deleted during staging.

### 6.3 Publish — preserve a recoverable old generation

1. Persist the intent to enter the publication phase.
2. If an active package exists, rename it to the transaction's backup path using a same-filesystem operation.
3. Persist `OLD_GENERATION_BACKED_UP`. If journal persistence fails, stop and restore the backup before returning.
4. Rename the staged package directory to the active package path.
5. Verify the marker and package settings at the active path, then persist `NEW_GENERATION_PUBLISHED`.
6. Apply the isolated settings state to the durable package metadata and re-read it. Check every write result; a false return is a failed commit, not success.
7. Publish the in-memory package map and component resolver only after durable metadata validation. Avoid mutating the prior map before this point.
8. Persist `PACKAGE_METADATA_COMMITTED`, run the post-publication checks, then persist `COMPLETE`.
9. Only after `COMPLETE` and a final recovery-safe verification may the backup generation and journal be retired.

If publication or metadata persistence fails before the commit point, restore the old package directory and old per-user library child from backup. Do not delete the backup until the restored paths and package metadata have been re-read successfully.

### 6.4 Startup recovery must run before package scanning

Recovery must run before `Settings.scanPackage()`, component registration, or clone launch.

- `PREPARING`: active generation must be untouched; retain active data and remove only transaction-owned staging proven not to be referenced.
- `STAGED_VALIDATED`: default to retaining the old active generation and discarding the candidate unless a deterministic commit continuation is explicitly proven safe.
- `OLD_GENERATION_BACKED_UP`: if active is absent and backup validates, restore backup. Do not infer success merely from the presence of a staged directory.
- `NEW_GENERATION_PUBLISHED`: verify the in-directory transaction marker and metadata digest. If valid, finish metadata publication; otherwise restore the backup.
- `PACKAGE_METADATA_COMMITTED`: validate the new active generation and reconstruct in-memory state; keep backup until the check completes.
- `COMPLETE`: validate active generation, then retire backup and journal.
- Missing, corrupt, unsupported-version, or contradictory journal/path state: fail closed. Preserve every plausible known-good generation, block further installs for the affected package, and expose a bounded recovery-required diagnostic. Never guess which directory is safe to delete.

If the transaction root contains orphaned files without a readable journal, quarantine them for investigation. No age-based cleanup is allowed to delete a possible last-known-good generation.

## 7. Android API and filesystem compatibility gates

The project currently builds with `minSdk 21`; the reference handset is Huawei Y7 2019 / DUB-LX1 on Android 8.1 (API 27). Design compatibility must cover API 21 through current supported Android releases, not only the CI API 34 emulator.

Candidate primitives include Android `AtomicFile` for journal/metadata files and `android.system.Os.rename` for same-filesystem directory publication. These are design candidates, not yet approved implementation choices.

Before selecting them, verify on API 21, API 23/24, API 27/28, API 29/30, API 31/32, API 33/34, and current target APIs:

- directory rename semantics when destination exists or is absent;
- same-filesystem enforcement and cross-device error handling;
- file and parent-directory fsync behavior;
- crash/power-loss behavior at each journal/rename boundary;
- permissions, ownership, SELinux labels, and app-private directory access after rename;
- behavior when storage is low, read-only, full, or the process is killed;
- recovery when journal writes succeed but directory operations fail, and vice versa.

Do not assume Java `File.renameTo()` is atomic or that a successful return alone establishes crash durability. If the runtime primitive cannot provide the required guarantee on a supported API/filesystem combination, implement a tested alternative or block the unsafe replacement operation while preserving the prior generation.

## 8. Required failure-injection and preservation tests

The transaction harness must inject failure/process death after every durable boundary:

- before journal creation;
- after `PREPARING`;
- during archive staging;
- after staged validation;
- after old-directory rename but before phase update;
- after phase update but before new-directory rename;
- after new-directory rename but before phase update;
- during package.conf serialization;
- when AtomicFile returns failure;
- after durable package.conf write but before in-memory publication;
- during per-user `lib` replacement;
- during startup recovery itself;
- when journal is truncated, has an unknown schema version, or contains path traversal;
- when backup and active paths both exist, neither exists, or contain mismatched transaction markers.

For every case, assert:
- the API result and structured failure phase;
- which generation is active after recovery;
- whether the previous known-good generation remains launchable;
- package map, app ID, and every virtual-user install state;
- component resolver state after rebuild;
- per-user `lib` rollback;
- byte-for-byte or hash-based preservation of user data, DE data, external data, profiles, account/session state, CloneStore registry, and pending reservation journal;
- no false-success install result;
- no uninstall notification for a package whose old committed generation was successfully restored.

Include multi-user cases: two clones of the same package, a replacement of one clone, a fresh third clone, an existing per-user library child, and an existing package with multiple installed user IDs.

## 9. CI evidence for the audited base commit

Commit `822791ea9c5bef2fd7c698659ed78dada0e0f547` triggered two runs:

- **Run #1039** completed successfully. Its logs report 69/69 instrumentation tests completed, zero skipped and zero failed; release build and APK audit succeeded. The isolated signing job succeeded and `apksigner` verified v1, v2, and v3 signatures. v3.1, v3.2, and v4 were not enabled/verified. The signing certificate fingerprint was not compared with an independently recorded intended release fingerprint.
- **Run #1040** failed before tests could execute. The debug/test APK build succeeded, but `connectedDebugAndroidTest` failed while Android's package manager handled `install-create`: a `StorageManager.getVolumes()` call dereferenced null. The logs also show ADB bootstrap failures and emulator-console/service instability. This is an emulator/test-install infrastructure failure on the same source commit, not evidence of a failing application assertion; nevertheless the run remains failed and must not be relabelled as a pass.

Neither run is a physical ARM-device test, a Clone Engine native-loading test, or proof of the transaction/recovery behavior designed here.

## 10. Stage 8.16 decision and implementation gate

**Decision:** adopt a journaled, staged, recoverable package-generation transaction as the required design. Do not patch `CreatePackageExecutor`, `CopyExecutor`, `Settings`, or `BPackageManagerService` in this stage.

The following are hard blockers before a runtime patch:

1. A testable isolated transaction/journal implementation exists.
2. Recovery is proven for every phase and ambiguous rename/journal combination.
3. Package settings are isolated from the active in-memory state until commit.
4. Package settings write failures propagate to the caller and cannot produce a success result.
5. Package scanning cannot delete an active or backup generation on a transient/corrupt read; quarantine/recovery policy is tested.
6. Per-user library replacement is reversible and all other user data remains untouched.
7. The same safety suite passes on the agreed Android API/filesystem matrix, including the API 27 reference-device profile.
8. Only then may a narrowly scoped Engine runtime patch be proposed and tested.

### Explicit non-actions

- No runtime Java or upstream Engine code changed.
- No change to Engine revision, install flags, ABI filters, or split handling.
- No modification or migration of CloneStore, reservations, SharedPreferences, Room, profiles, accounts, sessions, or virtual-user data.
- No physical-device connection or test.
- No main-branch change and no pull-request merge.

## 11. Next stage

Stage 8.17 should implement and test the transaction journal/state machine in an isolated harness first, including simulated process-death recovery and failure injection. It should add a scanner quarantine contract and prove the settings-save false-success path is closed before any production installer integration is attempted.
