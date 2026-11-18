# Stage 7 — Clone persistence migration readiness

Date: 2026-11-17

## Decision

This stage is an inventory, compatibility contract, and migration plan only. It does **not** add Room, change the persistence implementation, rewrite existing preferences, or touch virtual-app storage. The current SharedPreferences implementation remains the sole source of truth until a later stage has a tested import, verification, rollback, and device-upgrade path.

## Existing persistence contract

CloneStore uses the SharedPreferences file `veyravault_clones_v2` and these keys:

| Key | Stored shape | Meaning |
|---|---|---|
| `clones_json` | JSON array | Clone registry; one record per package + virtual user |
| `collapsed_spaces` | String set | Collapsed Spaces UI groups |
| `master_mock_gps` | Boolean | Master location switch; default true |
| `global_device_json` | JSON object | Global device/SIM profile metadata |
| `active_launch_json` | JSON object | Last successfully launched package + virtual user |

A clone's identity is the composite pair `packageName + userId`; the displayed Space number is `userId + 1`. The persisted clone fields are package name, virtual user ID, display name, GPS enabled flag, latitude, longitude, location label, custom-device metadata enabled flag, device brand, device model, and the denied-permission string set.

The global profile stores enabled, brand, manufacturer, model, device, country ISO, SIM operator code, and SIM operator name. These are currently metadata only; this migration must preserve them without implying they are applied to the virtual device.

The active-launch marker is intentionally a separate record. A stale marker can exist after a clone is removed; current behavior resolves it to null when the clone no longer exists. A future schema must preserve this observable behavior rather than silently redirecting it.

## Important risks found

1. `getAll()` catches malformed JSON and returns an empty list. A subsequent `saveAll()` can therefore overwrite a damaged registry with an empty array. Migration code must never interpret parse failure as a valid empty database.
2. `saveAll()` catches serialization/storage exceptions and does not report failure to callers. The migration must add explicit success/failure reporting before any source-of-truth switch.
3. Clone records are currently read and written as a whole JSON array. Concurrent writers can overwrite one another; Room transactions and a single repository write path are required.
4. Current APIs are synchronous and called from Activities. Room must not be introduced with main-thread database queries as a shortcut. A repository/executor or lifecycle-aware asynchronous API must be planned, including UI loading/error states.
5. `deniedPermissions` is a set. Import must deduplicate values while preserving every distinct permission string.
6. Global settings, collapsed-space state, master GPS, and last-active marker are not clone rows; migrating only the clone JSON array would lose user settings.

## Proposed Room schema (not implemented in this stage)

- `clones`: composite primary key (`packageName`, `userId`); remaining clone scalar fields map one-to-one from the legacy JSON record.
- `clone_denied_permissions`: composite primary key (`packageName`, `userId`, `permission`), foreign key to `clones` with cascade delete.
- `collapsed_spaces`: primary key `spaceNumber`; rows represent members of the legacy collapsed set.
- `global_device_profile`: singleton row with fixed ID 1 and all eight existing profile values.
- `app_persistence_settings`: singleton row with fixed ID 1 for master GPS enabled state.
- `last_active_launch`: singleton row with fixed ID 1 and nullable package/user pair, preserving stale markers if the referenced clone no longer exists.

The Stage 1 profile settings in `veyravault_profiles_v1` are a separate store and are explicitly outside this CloneStore migration. BlackBox virtual package data, account/session data, and engine-owned files are also outside scope and must never be copied, renamed, cleared, or re-created by this migration.

## Required migration sequence

1. **Freeze and inventory**: retain the exact legacy preference file/key names and document every reader/writer. No schema or key renaming.
2. **Read-only snapshot**: read the raw legacy values without modifying them; distinguish missing keys from malformed values; compute a deterministic snapshot digest and item counts.
3. **Validate**: parse all clone records, require non-empty package names and non-negative user IDs, detect duplicate composite identities, validate coordinate ranges when GPS is enabled, and preserve unknown/optional legacy fields in a compatibility payload if encountered. Any ambiguity stops migration.
4. **Backup**: persist an immutable pre-migration snapshot in app-private storage and verify it can be read back byte-for-byte. Do not include engine session directories.
5. **Transactional import**: import all five persistence categories in one Room transaction. Do not mark migration complete until the transaction commits.
6. **Verify**: compare canonicalized legacy and Room snapshots, including row counts, composite identities, all scalar values, permission-set contents, collapsed spaces, global metadata, master GPS, and active-launch marker.
7. **Shadow-read period**: keep legacy preferences unchanged and compare repository reads against Room on test builds. Do not dual-write indefinitely; define one authoritative writer for the eventual cutover.
8. **Cutover and rollback**: only a later explicitly reviewed stage may switch reads/writes. Retain the backup and legacy keys for at least one verified upgrade cycle. If verification or database open fails, continue using legacy storage; never replace valid legacy data with an empty database.
9. **Retirement**: remove legacy keys only in a separate future change after successful upgrade-path tests and an explicit release decision.

## Acceptance tests required before cutover

- Empty first install and upgrade from every supported legacy preference shape.
- Exact round-trip of all clone fields and denied-permission sets.
- Duplicate package names across different virtual users remain distinct.
- Same package + same virtual user is treated as one identity.
- Collapsed Spaces, global metadata, master GPS default/value, and active-launch marker all survive.
- Malformed JSON, wrong JSON types, truncated data, duplicate identities, and failed backup/import cause a safe abort with original preferences untouched.
- Process death before, during, and after import is recoverable and idempotent.
- Re-running migration does not duplicate rows or overwrite newer data.
- Clone create, duplicate, rename, configure, permission metadata update, remove, and launch flows still behave correctly.
- Existing virtual app package data and account/session state remain untouched across upgrade, rollback, and app restart.
- Android API 21 compatibility, app upgrade, and physical-device tests pass.

## Build-system gate

The checked-in app's Gradle file is a source template: `scripts/prepare_workspace.py` generates the actual app Gradle file in the pinned BlackBox workspace. Any future Room dependency must be added to that generated dependency block, not only to the checked-in template. Before choosing Room/compiler versions, inspect the pinned engine's Gradle wrapper, Android Gradle Plugin, Kotlin/Java toolchain, and repository constraints. The app currently targets Java 8 source compatibility and minSdk 21. No dependency version is selected in this stage.

## Stage 7 result

Migration inventory and regression guard are added to CI. Runtime persistence is unchanged. Room dependency selection, database classes, data import, read/write cutover, and legacy-key retirement remain intentionally deferred to separately testable stages.


## Stage 7.1 — Inactive Room schema foundation

The pinned engine build configuration was inspected directly at commit `89b59836c66f173756a4ae258cf379a957649820`:

- Gradle Wrapper: 8.14.5
- Android Gradle Plugin: 8.13.2
- Engine Bcore compile options: Java 21
- Generated app module compile options: Java 8
- compileSdk: 35; minSdk: 21; generated targetSdk: 28

Room 2.6.1 was selected as a conservative Java annotation-processor/runtime line compatible with the app's Java 8 source target and legacy minSdk 21. The dependency is added to the generated app Gradle block in `scripts/prepare_workspace.py`; adding it only to the checked-in app Gradle template would have no effect on the actual CI build.

An inactive schema foundation now exists under `app/src/main/java/com/veyravault/space/core/persistence/`:

- `CloneEntity` uses the composite primary key (`packageName`, `userId`).
- `DeniedPermissionEntity` stores each permission separately and has a cascading composite foreign key to its clone.
- `CollapsedSpaceEntity` retains the original string key exactly instead of converting it to an integer.
- Singleton entities represent global device metadata, master GPS state, and the last-active marker.
- DAOs and `ClonePersistenceDatabase` define the first Room schema.
- `ClonePersistenceDatabaseProvider` creates the database without destructive fallback and is not called from `VaultApp`, `CloneStore`, or current runtime flows.

The CI contract test verifies the generated Gradle dependency, presence of all schema/DAO types, the inactive runtime boundary, absence of destructive fallback/main-thread query opt-ins, and preservation of legacy collapsed-key and stale-active-marker semantics. Room schema export is enabled and directed to the version-controlled `app/schemas` directory so future schema versions can be reviewed and migration-tested.

**Important:** this is schema scaffolding only. No data is imported, no Room query is invoked by the app, no legacy preference is modified, and `CloneStore` remains the only active persistence implementation. The next stage must add deterministic legacy snapshot parsing, backup verification, transactional import, and round-trip comparison tests before any runtime cutover is considered.


## Stage 7.2 — Read-only legacy snapshot and validation foundation

A first implementation of the pre-migration snapshot boundary is now present in
`core/persistence/LegacyCloneSnapshot.java`.

### Exact caller inventory

The existing runtime callers were inspected across the checked-in Java source:

- `VaultApp` invokes `CloneStore.syncAllHooks`; `VirtualHookManager` reads the last-active marker and master GPS setting.
- `AddAppActivity` allocates a package-scoped virtual user and writes a clone after engine installation succeeds.
- `MainActivity` reads and updates clone entries, collapsed Spaces, clone duplication/removal, rename, per-clone metadata, and active launch flows.
- `DashboardActivity` reads the clone registry for counts.
- `GlobalEnvironmentActivity` reads/writes global profile metadata and master GPS.
- `SetLocationActivity` reads and updates a clone's location values.

The existing `CloneStore` remains the active runtime API and the only authoritative store. No caller was redirected.

### Snapshot behavior

- Reads the exact `veyravault_clones_v2` SharedPreferences file and all five existing keys.
- Captures the original presence/absence of each key, preserving the distinction between a missing key and an explicitly stored default.
- Applies the legacy defaults only when a key/field is absent, matching existing CloneStore behavior.
- Strictly rejects wrong preference types, malformed JSON, non-object clone entries, invalid scalar types, negative virtual user IDs, duplicate composite identities, malformed permission arrays, and invalid coordinates when per-clone GPS is enabled.
- Preserves each complete original clone JSON object as a compatibility payload, so unrecognized optional fields are not silently discarded by the snapshot layer.
- Retains stale last-active markers rather than requiring a matching clone row.
- Produces a deterministic canonical payload and SHA-256 digest.
- Does not mutate preferences, create a backup, access Room, or touch BlackBox/session storage.

### Boundary

This is a read-only capture API. It is not invoked from app startup or ordinary CloneStore operations. A rejected snapshot leaves the original preferences unchanged.


## Stage 7.2 — Atomic app-private snapshot backup

`LegacyCloneSnapshotBackup.java` adds an explicit, opt-in backup operation:

- Stores the validated snapshot under app-private `filesDir/migration-backups/`.
- Uses Android `AtomicFile`, flushes and fsyncs the write, finishes atomically, and reads the file back.
- Verifies exact byte equality, envelope format version, payload SHA-256, and equality with the captured snapshot digest.
- Treats a prior backup as immutable: exact same snapshot can reuse it; a different, unreadable, or corrupt prior backup is rejected rather than overwritten.
- Detects an interrupted `.bak` sidecar and uses `AtomicFile.openRead()` recovery semantics before considering the backup reusable.
- Does not use external storage, does not delete databases, and does not access BlackBox/virtual-app/session data.
- Is not called by `VaultApp` or runtime CloneStore flows.

The source-contract test checks the atomic write, fsync, read-back verification, checksum, immutability, and isolation boundaries.


## Stage 7.3 — Opt-in transactional Room importer and parity verifier

`LegacyCloneRoomImporter.java` adds a worker-thread-only, explicit importer:

- Refuses main-thread execution.
- Imports only into an empty Room database, inside one Room transaction.
- Refuses an existing non-empty database without matching migration provenance.
- Repeated import is idempotent only if the snapshot digest matches and the verifier confirms every persisted row still matches exactly.
- Same digest with altered/missing rows is an error; a different digest with prior provenance is an error.
- Preserves clone composite identity, modeled fields, exact original clone JSON, denied permissions, collapsed keys, global profile, master GPS, optional/stale active marker, and full migration provenance.
- Does not read or write SharedPreferences, call BlackBox, or manipulate engine/session files.

`LegacyCloneRoomVerifier.matches(...)` compares all imported tables against the captured snapshot, including the canonical payload and digest.

The source-level contract test protects the worker-thread guard, transaction, empty database guard, row mappings, parity checks, and no-runtime-wiring boundary.


## Stage 7.4 — Android Room instrumentation test harness

An AndroidX instrumentation suite is now added under `app/src/androidTest`. It uses the actual Room-generated database and SQLite implementation rather than source-text assertions.

### Covered runtime scenarios

- Import a populated snapshot and verify all modeled rows and migration provenance.
- Repeat the same import and require `ALREADY_IMPORTED`; then mutate a persisted row and require parity verification to fail and re-import to be rejected.
- Inject a SQLite trigger failure during denied-permission insertion after clone insertion, then verify the Room transaction leaves every table empty.
- Close and reopen an on-disk Room database and verify the imported snapshot, including a stale active marker.
- Import an empty snapshot with no active marker and verify singleton defaults and absence of an active row.

The test APK uses a debug-only `RoomTestApplication` so the instrumentation process does not start the virtual-app engine. The generated Debug variant explicitly targets the CI emulator's `x86_64` ABI and excludes native shared libraries because these tests exercise persistence only; the production `VaultApp`, release manifest, release ARM ABI filters and release APK packaging remain unchanged. The test suite runs on an x86_64 Android API 34 emulator through GitHub Actions. An initial emulator run exposed the inherited ARM-only ABI filter as the cause of `No compatible devices connected`; the Debug-only ABI override now addresses that mismatch.

### Boundary and remaining validation

These are automated emulator tests, not physical-device upgrade tests. They do not invoke the importer from startup and do not change the production persistence provider. Before any production cutover, still require an upgrade test against a real legacy installation, a verified backup/restore drill, app-process death during an import, and device-level clone/session regression checks. SharedPreferences remains authoritative.


## Stage 7.5 — Android backup integrity instrumentation coverage

This follow-up adds Android instrumentation coverage for the opt-in `LegacyCloneSnapshotBackup` implementation:

- Valid snapshot write/read-back and receipt digest/byte count.
- Exact-snapshot reuse without changing immutable backup bytes.
- Rejection of a different snapshot without replacing the original backup.
- Rejection of corrupt existing backup bytes without overwriting them.
- Recovery of a complete AtomicFile `.bak` sidecar when the base file is absent.

The separate AndroidX backup instrumentation class is discovered by `:app:connectedDebugAndroidTest`. The source-contract test requires all four backup scenarios.

**CI validation:** PR-triggered Run `#230` for commit `8bfbcb1a64a9aacc08c537564e5e72e7750cf784` completed successfully. The emulator reported **9/9 instrumentation tests completed, 0 skipped, 0 failed**; source audit, unsigned release APK compilation, and APK audit also passed. The duplicate Push-triggered Run `#229` failed before test execution because the emulator's Package Manager service was unavailable (`Can't find service: package`); its failed job was submitted for retry. The successful PR-triggered run is the verified Stage 7.5 result.

**Limitations:** the sidecar test uses a controlled filesystem fixture and is not itself an OS process-kill test. The backup class still has no standalone restore API. No production import, startup wiring, SharedPreferences mutation, database cutover, or virtual-app/session operation is introduced. SharedPreferences remains the sole runtime source of truth.


## Stage 7.6 — Abrupt process death during a Room import

A debug-only Android service runs in a dedicated OS process (`:migration_recovery_test`) so instrumentation can terminate that process without killing the test runner. The service starts the explicit Room importer and pauses at a package-private checkpoint **inside the Room transaction**, after clone and denied-permission rows have been inserted but before the remaining tables and migration provenance are written.

The instrumentation test then:

1. Waits for an fsynced checkpoint marker and captures the service process ID.
2. Sends SIGKILL to that dedicated process and waits for Android to report that it has exited.
3. Starts the service again, causing Android to create a fresh process that reopens the same on-disk Room database.
4. Verifies that all seven tables are empty: clones, denied permissions, collapsed spaces, global profile, persistence settings, active marker, and migration provenance.

The crash service is declared only in the debug manifest. The release manifest, `VaultApp`, CloneStore preferences, virtual package data, and account/session directories are not changed. The importer remains opt-in and is not called by startup or normal runtime flows.

**CI validation:** PR Run #244 (run ID 44223327104) on commit `39f53dc088a3239bc94326ded5a0ad5dfd077ba3` completed successfully. The Android emulator executed **10/10 instrumentation tests, 0 skipped, 0 failed**; the Gradle connected instrumentation task completed successfully. The same run completed all source-contract checks, source audit, unsigned release APK compilation, and compiled APK audit. The separate signing job also succeeded: `apksigner verify --verbose` reported v1, v2, and v3 signature verification as true, with one signer. Run: https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44223327104

**Remaining boundary:** this is automated emulator evidence, not a physical-device upgrade test or a production migration. A separately reviewed backup restore/read API and physical-device upgrade/backup-restore drills remain mandatory before any production migration or cutover. SharedPreferences remains the sole runtime source of truth.


## Stage 7.7 — Verified read/restore API for the migration snapshot

`LegacyCloneSnapshot.fromCanonicalPayload(...)` reconstructs a strict snapshot from the backup's canonical payload without consulting or mutating the device's current SharedPreferences. It repeats validation of clone JSON types, composite identities, GPS coordinate ranges, denied-permission values, collapsed-space values, global profile metadata, and the optional/stale active-launch marker; the reconstructed canonical payload must exactly equal the supplied payload.

`LegacyCloneSnapshotBackup.readAndVerify(...)` is an explicit read-only restore API for the existing app-private migration backup. It uses AtomicFile recovery semantics, validates the envelope version and SHA-256, reconstructs the snapshot, and verifies both the reconstructed digest and canonical payload before returning it. Missing, malformed, unsupported-version, or checksum-mismatched backups fail closed. The method does not write SharedPreferences, open Room, invoke BlackBox, or touch virtual-app/session files.

The returned validated snapshot can be passed explicitly to the existing worker-thread-only `LegacyCloneRoomImporter.importIntoEmptyDatabase(...)`. This enables a tested backup-to- Room import path without silently replacing the active legacy store.

Instrumentation now covers:
- Read a backup after current SharedPreferences have changed; recover the original snapshot while proving current preferences remain unchanged.
- Reject an unsupported backup envelope version.
- Import a snapshot returned by the verified backup reader into an empty Room database and compare all rows/provenance, while confirming the current legacy preferences remain untouched.

**Scope boundary:** this is a restore/read API for the small internal CloneStore migration snapshot only. It is not the future user-facing Complete Backup & Restore feature and does not include virtual app package data, account/session state, media, or app-internal settings. Room remains inactive and SharedPreferences remains the sole runtime source of truth. Physical-device upgrade and backup/restore drills remain outstanding.
