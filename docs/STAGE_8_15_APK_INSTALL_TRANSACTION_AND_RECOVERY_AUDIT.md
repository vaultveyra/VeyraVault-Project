# Stage 8.15 — APK Source Topology, Install Ownership, and Recovery Audit

**Status:** Source audit and design only. No runtime implementation changes.
**Audited Engine:** `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`
**VeyraVault base:** `24ca3391e1fc6de851a9c0d2b932b8300530b04d`

## 1. Scope and safety boundary

This stage audits the pinned Engine's package installation and package-rescan paths, with particular attention to replacement failures, package metadata, APK source paths, and virtual per-user data ownership.

No installer code, Engine pin, ABI filters, CloneStore schema, SharedPreferences data, virtual package records, credentials, account/session data, or Room activation was changed. The findings below are source-level observations, not physical-device test results.

## 2. Confirmed storage topology

The pinned Engine's `BEnvironment` defines these distinct locations below its private `blackbox` root:

| Purpose | Path builder | Ownership |
|---|---|---|
| Installed package code and package metadata | `getAppDir(packageName)` → `data/app/<package>` | Package-wide |
| Base APK | `getBaseApkDir(packageName)` → `data/app/<package>/base.apk` | Package-wide |
| Extracted native libraries | `getAppLibDir(packageName)` → `data/app/<package>/lib` | Package-wide |
| Package settings | `getPackageConf(packageName)` → `data/app/<package>/package.conf` | Package-wide |
| Credential-protected virtual app data | `getDataDir(packageName, userId)` → `data/user/<userId>/<package>` | Per virtual user |
| Device-protected virtual app data | `getDeDataDir(packageName, userId)` → `data/user_de/<userId>/<package>` | Per virtual user |
| External virtual app data | `getExternalDataDir(packageName, userId)` | Per virtual user |
| Engine user/account configuration | `getSystemDir()` files such as `user.conf`, `accounts.conf` | Engine-wide |

VeyraVault's host-side CloneStore is a separate application-private SharedPreferences store (`veyravault_clones_v2`), not a directory beneath Engine `data/app/<package>`.

**Important precision:** deleting an Engine package-code directory does not, by itself, prove deletion of CloneStore or the per-user virtual data directories. The audited methods show those as separate paths. Conversely, the installer has a separate per-user data-library deletion described below, so it is not accurate to say that every virtual-user subdirectory is always untouched.

## 3. Confirmed install sequence and destructive window

The pinned `BPackageInstallerService.installPackageAsUser()` executes, in this order:

1. `CreateUserExecutor`
2. `CreatePackageExecutor`
3. `CopyExecutor`

### 3.1 CreateUserExecutor

For the target package and user, it first deletes `getDataLibDir(packageName, userId)`, then ensures the per-user data, cache, files, databases, and device-encrypted directories exist.

It does **not** recursively delete the entire per-user `data/user/<id>/<package>` directory in this method. However, its explicit deletion of that user's `lib` child is a real mutation and must be accounted for during replacement/retry design.

### 3.2 CreatePackageExecutor

It unconditionally calls `FileUtils.deleteDir(BEnvironment.getAppDir(packageName))`, then recreates the package directory and package-wide native library directory.

Because `package.conf` and the stored base APK are children of this directory, this operation removes both the old package metadata and old stored base APK before the new copy is known to have succeeded.

### 3.3 CopyExecutor

For non-system packages, it extracts native libraries from **only** `ps.pkg.baseCodePath` into the package-wide library directory.

If `FLAG_STORAGE` is set, it copies or renames that same base APK to `getBaseApkDir(packageName)`, marks it read-only, and updates `ps.pkg.baseCodePath`. If `FLAG_STORAGE` is not set, this executor does not place the base APK into the Engine package directory and leaves the source path in use.

No split APK path list or split-aware extraction is represented in the inspected `BPackage` model: it stores a single `baseCodePath`. This confirms that the current audited install path is base-APK-oriented; it does not establish split APK support.

## 4. Confirmed metadata publication and failure behavior

The Engine package manager parses and collects certificates before invoking the installer. It then obtains a new `BPackageSettings` object, preserving the prior package's `appId` and virtual-user state when an existing in-memory entry is found.

After the installer returns success, the package manager marks the target user installed, calls `BPackageSettings.save()`, refreshes component resolution, and rescans the package directory.

This ordering has a critical gap:

- `CreatePackageExecutor` deletes the previous installed code directory and `package.conf` before `CopyExecutor` has completed.
- If extraction, APK copy/rename, or a later install step fails, the method returns an install error.
- The old package code and settings have already been deleted; the prior known-good install is not retained by this sequence.
- The new `package.conf` is saved only after the installer reports success.

The source therefore confirms a **non-transactional replacement window**. This is not merely a theoretical split-APK issue.

### 4.1 Startup package scan has a second destructive failure path

In `Settings.updatePackageLP()`, any thrown error while reading/unmarshalling `package.conf`, reconstructing settings, or generating package application information enters a catch block that:

1. deletes the entire package directory passed to the scan;
2. removes the package from the in-memory package map;
3. kills processes for that package; and
4. emits an uninstall notification.

This means a corrupt, truncated, unreadable, or temporarily inconsistent package metadata file can cause the scanner to delete the package-code directory instead of quarantining it for recovery. The current code does not distinguish a malformed package from a transient read/metadata failure before destructive cleanup.

## 5. Data that must remain separately protected

The following data domains must not be treated as replaceable package-code content:

- VeyraVault CloneStore registry and pending reservation journal.
- Per-user virtual app data under `data/user/<userId>/<package>`.
- Per-user device-protected data under `data/user_de/<userId>/<package>`.
- Per-user external virtual app data.
- Engine-wide user/account configuration and other system configuration.
- VeyraVault profile preferences and account/session continuity.

The audited `CreatePackageExecutor` targets the package-wide app directory, not those separate roots. The audited `CreateUserExecutor` deletes only the selected virtual user's data `lib` child, but that deletion still needs an explicit migration/rollback policy. Explicit uninstall/clear executors have broader per-user deletion behavior and must remain separate from install/replace operations.

## 6. Required safe replacement architecture

Do not patch the current executor sequence by simply adding another copy step. A safe design must be transactional and recoverable:

1. **Preflight:** validate package name, version, signing identity, base/split relationships, split dependencies, archive readability, and supported ABI set before touching the current installation.
2. **Staging:** copy all required APK artifacts into a unique staging directory on the same filesystem as the final package directory.
3. **Validation of staged files:** verify file length/readability and parse the staged base/splits again; verify the package identity and signing lineage match the preflight result.
4. **Native extraction:** extract ABI-compatible native libraries from every relevant APK artifact into a staging lib directory. Return a typed result distinguishing no-native APK, supported native payload, unsupported native-only payload, and malformed archive.
5. **Metadata staging:** build the new package settings and application metadata without overwriting the current committed settings.
6. **Commit protocol:** use a recoverable journal/state marker and same-filesystem atomic directory rename where supported. Keep a last-known-good generation until the new generation is fully published and reopened successfully.
7. **Settings publication:** atomically publish package settings only after staged code is committed and validated. Never delete the previous settings before the replacement is recoverable.
8. **Rollback/recovery:** on any failure or process death, restore the previous committed generation or retain it as active; clean abandoned staging only after journal reconciliation.
9. **Per-user preservation:** do not clear user data, profiles, CloneStore records, reservations, or account/session state as part of package-code replacement. Define a separate explicit policy for native data-library refresh.
10. **Observability:** report the failing phase and recovery outcome without logging credentials, app-private content, clone identifiers, or personal data.

Atomic rename behavior, directory fsync requirements, Android API-level compatibility, and filesystem behavior must be verified on the supported API range before implementation.

## 7. Required fixture and failure-injection matrix

Before runtime changes, add deterministic fixtures and tests for:

- Fresh base-only APK with no native libraries.
- Base APK with ARMv7 native libraries.
- Base APK with ARM64 native libraries.
- Base APK with both supported ARM ABIs.
- x86-only and x86_64-only native payloads.
- APK with malformed ZIP/native entries.
- Base plus ABI split(s), including missing split and mismatched package/version/signing identity.
- Existing valid install replaced by a valid newer install.
- Existing valid install followed by staged-copy failure.
- Native extraction failure after staging begins.
- Metadata serialization failure before commit.
- Process death before commit, during commit, and after code publication but before settings publication.
- Corrupt or unreadable `package.conf` during startup scan.
- Two virtual users with distinct data, including one user's `lib` directory.
- Verification that CloneStore, reservation journal, virtual user data, DE data, external data, profiles, and account/session state remain intact after every failed replacement.

Each test must assert both the returned error and the exact on-disk/in-memory recovery state. A passing source-contract test alone is not sufficient.

## 8. Compatibility and validation limits

- The pinned source is an upstream Engine source audit, not an Android-device execution.
- The CI run associated with the Stage 8.14 commit passed, including 69/69 instrumentation tests and the release build/audit. Those tests do not prove Engine APK replacement safety or physical ARM native loading.
- The CI emulator reported early ADB bootstrap failures and an emulator-console warning, but subsequently ran all 69 tests with zero skipped and zero failed; the workflow completed successfully.
- The isolated signing job uploaded a signed artifact. The signing certificate fingerprint has not yet been compared against the intended release key, so key continuity is not certified by this result.
- No physical-device test has been performed on the Huawei Y7 2019 reference device or any other device in this stage.

## 9. Stage 8.15 decision

**Decision: do not modify the runtime installer yet.** The current Engine install and scan paths have confirmed destructive failure windows. First implement the transaction/recovery design and fixture matrix in isolation, then test it against the pinned Engine and VeyraVault integration. Only after those tests pass should a narrowly scoped runtime patch be considered.

### Explicit non-actions

- No change to Engine pin or ABI filters.
- No split APK support claim.
- No change to CloneStore, reservations, SharedPreferences, Room, accounts, or session storage.
- No install/uninstall behavior change.
- No physical-device connection or test.
- No merge to `main`.

## 10. Next stage

Stage 8.16 should define the transaction journal, staging-directory layout, commit/rollback state machine, and Android API-level filesystem compatibility. It should also verify the exact `InstallOption` flags used by VeyraVault's reflection-based Engine entry point before choosing the final APK source-path policy.
