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
