# Stage 7.9 — Async Persistence Repository: Runtime Call-Site Audit and Design

## Status and safety boundary

This document records the source audit and the proposed contract for the next persistence layer. It does **not** implement the repository, switch any runtime caller, instantiate Room, migrate data, or change the SharedPreferences source of truth.

- PR4 remains Draft and must not be merged.
- SharedPreferences / CloneStore remains the active runtime source of truth.
- Room remains an opt-in migration target only.
- No startup migration, data cutover, destructive fallback, or session-data operation is permitted in this stage.
- All asynchronous repository work must be additive and independently testable before any UI/runtime adoption.

## Stage 7.8 validation baseline

CI run #294, attempt 2, commit `3cb0f6342b5e71757cc4e10925aecaac24e49a9d` completed successfully:
- 17/17 Android Emulator tests, 0 skipped, 0 failed.
- All contract and instrumentation-wiring checks passed.
- Source audit, unsigned release APK compilation, and APK audit passed.
- Artifact ZIP SHA-256: `46150313c7e3c5e7f0e9c01c89726e6ec9c54da10e268fbb253fc1f5e85fdcff`.

## Runtime call-site audit

The following CloneStore consumers were inspected on the feature branch:

| File | Operations / concern |
|---|---|
| `AddAppActivity` | Allocates next virtual user ID, installs through Engine, then upserts clone; checks allocation and upsert status. |
| `MainActivity` | Reads and groups clones; collapses Spaces; duplicates, renames, edits metadata, uninstalls single/batch clones. Stage 7.8 checks key mutation statuses. |
| `SetLocationActivity` | Reads clone and performs GPS enable/disable upserts. **Both upsert return values are currently ignored**, and the UI may show success/finish despite a failed commit. |
| `GlobalEnvironmentActivity` | Reads global metadata and master GPS; calls `saveGlobalEnv` and `setMasterMockGpsEnabled`, whose current APIs do not return persistence status; then syncs hooks and reports success. |
| `DashboardActivity` | Reads clone registry for counts. |
| `VaultApp` | Calls `CloneStore.syncAllHooks` during app startup. This remains existing runtime behavior and must not be changed as part of the repository foundation. |
| `VirtualHookManager` / `Engine` | Read active clone/master GPS and record confirmed active launch. Active launch marker write currently has no surfaced status. |
| `PermissionsActivity` | Read-only clone metadata display. |
| `ProfileStore` | Legacy GPS profile import reads CloneStore after a shallow JSON-object check. It should use the same strict validated snapshot/read path so invalid field types, duplicate identities, or invalid enabled coordinates cannot be silently treated as an empty list and then marked migrated. |

This inventory distinguishes CloneStore registry operations from the separate versioned ProfileStore. The next implementation must not accidentally combine their preference namespaces or schemas.

## Design decision

Introduce one application-scoped, single-writer asynchronous repository facade over the existing SharedPreferences-backed stores. Its first implementation is a compatibility layer, not a Room repository.

### Required properties

1. **Single serialized writer:** one dedicated single-thread executor serializes repository reads and writes in submission order. No disk operation runs on the main thread.
2. **Main-thread callbacks:** completion callbacks are dispatched through a main-thread executor/Handler by default. Tests can inject deterministic executors.
3. **Typed result:** every operation returns an explicit result with success/value or a stable failure category (invalid input, corrupt/unsupported stored data, persistence commit failure, executor closed/rejected, unexpected internal failure). Do not collapse errors into empty collections, default values, or a generic success.
4. **Strict reads:** registry reads use the same strict validation as Stage 7.8. Corrupt registry state is an error, not an empty registry.
5. **Commit-aware writes:** all writes return and propagate actual `commit()` status. APIs that currently swallow errors or use `apply()` must be upgraded to report persistence status before they are exposed through the repository.
6. **Input/output isolation:** mutable clone records and collections are defensively copied when submitted and before callback delivery.
7. **Lifecycle safety:** application context only; deterministic shutdown/rejection behavior; no Activity references retained by worker tasks.
8. **No implicit fallback:** never switch to Room, recreate an empty registry, or overwrite corrupt data after an error.
9. **No false atomicity claims:** serialized repository calls are ordered only relative to calls submitted to that repository instance. Existing direct synchronous CloneStore callers remain outside that queue until a separately reviewed caller migration.
10. **No engine side effects:** repository operations do not install, launch, stop, clear, uninstall, hook, or otherwise mutate virtual app runtime state.

### Initial operation surface

- Strictly load clone registry.
- Allocate next user ID with an explicit error result.
- Upsert and remove clone with explicit commit result.
- Save the complete validated clone list with explicit commit result.
- Read and write collapsed Space state with explicit commit result.
- Read and write master GPS state with explicit commit result.
- Read and write global device-profile metadata with explicit commit result.
- Record/read the last confirmed active-launch marker with explicit commit/read result.
- Read/write ProfileStore global and per-clone overrides through its own versioned namespace.
- Run legacy profile import only from a strict validated CloneStore snapshot; report whether import committed.

No operation should accept an arbitrary callback that performs Android UI or Engine work on the persistence thread.

## Important ordering constraint for Add/Duplicate flows

The existing safe sequence is: determine an available virtual user ID, ask Engine to install, then persist the CloneStore record; if persistence fails, attempt Engine cleanup and only report cleanup success after the engine confirms absence.

A serialized async facade alone does not reserve an ID against callers that still use direct synchronous APIs or against a gap between allocation and later persistence. Do not claim allocation is globally atomic. Any future async Add/Duplicate integration needs an explicit reservation/operation design and compensating cleanup, tested against concurrent requests, before it replaces the existing flow.

## Implementation and test gates

Before any runtime caller is switched:
- Add the repository and typed result model without wiring Activities or startup.
- Add deterministic unit/contract tests for executor ordering, callback dispatch, error mapping, defensive copies, closed-executor behavior, and strict corrupt-store propagation.
- Add Android instrumentation tests for persisted read/write round trips, commit failure/error reporting where injectable, and concurrent queued mutations.
- Add tests that prove ProfileStore legacy import rejects a strict CloneStore read failure and never sets its migration marker on incomplete input.
- Run the full Android Emulator suite, source audit, unsigned release build, and APK audit.
- Inspect the diff and verify PR4 remains Draft/open/unmerged with `main` unchanged.

Only after all gates pass should a separate reviewed stage migrate a small number of callers. The first candidates should be UI-only settings operations; startup hooks and Engine lifecycle flows are explicitly excluded until ordering and failure behavior are independently proven.

## Known limitations not solved by this design

- The current app does not have a complete app-private clone/session backup system.
- This repository does not make Android Keystore-bound credentials portable.
- No guarantee is made that virtual app accounts or sessions can be restored on another device.
- Device/SIM metadata remains metadata-only where no supported scoped Engine API exists.
- Physical-device upgrade and clone/session regression tests remain required.
