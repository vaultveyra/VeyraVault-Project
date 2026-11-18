# Stage 7.9 — Async Persistence Repository: Runtime Call-Site Audit and Design

## Status and safety boundary

This document records the original source audit/design and the subsequent additive asynchronous repository foundation. The repository is implemented over the existing SharedPreferences-backed stores, but no runtime UI caller or startup/Engine flow has been switched, Room has not been instantiated for production, and no data migration/cutover has been performed.

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
| `AddAppActivity` | Stage 7.9.7: allocates through AsyncCloneRepository, installs through Engine, then persists asynchronously with compensating cleanup; batch creation is sequential. |
| `MainActivity` | Reads and groups clones; collapses Spaces; duplicates, renames, edits metadata, uninstalls single/batch clones. Stage 7.8 checks key mutation statuses. |
| `SetLocationActivity` | Reads clone and performs GPS enable/disable upserts. **Both upsert return values are currently ignored**, and the UI may show success/finish despite a failed commit. |
| `GlobalEnvironmentActivity` | Reads global metadata and master GPS; calls `saveGlobalEnv` and `setMasterMockGpsEnabled`, whose current APIs do not return persistence status; then syncs hooks and reports success. |
| `DashboardActivity` | Stage 7.9.7: reads a strict asynchronous clone snapshot for counts and shows unavailable state on read failure. |
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
- Read and write collapsed Space state with explicit commit result and strict stored-type validation.
- Read and write master GPS state with explicit commit result and strict stored-type validation.
- Read and write global device-profile metadata with explicit commit result and strict JSON field validation.
- Record/read the last confirmed active-launch marker with explicit commit/read result and strict identity validation.
- Read/write ProfileStore global and per-clone overrides through its own versioned namespace, with strict schema/field reads and defensive copies.
- Clear individual profile fields without erasing sibling overrides.
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


## Stage 7.9.1 — Initial async CloneStore repository foundation

Implementation added on the feature branch after the design-only audit:

- Add `AsyncCloneRepository`, an application-scoped accessor over an application-context-backed facade with one dedicated single-thread executor and main-looper callback dispatch.
- Add typed results and failure categories: invalid input, corrupt/unsupported stored data, persistence commit failure, closed/rejected executor, and unexpected internal failure.
- Add asynchronous strict clone-list read, next-user-ID lookup, save-all, upsert and remove operations. The allocator reports an available ID but does not reserve it.
- Copy clone records and permission sets on submission and before returning loaded lists. Validate clone identities, denied permissions and enabled GPS coordinates before queuing writes.
- Expose the package-private strict CloneStore reader to other classes in the same persistence package. Existing public UI fallback behavior remains unchanged.
- Correct the legacy ProfileStore location import to consume the strict CloneStore reader directly. Any malformed or semantically invalid registry now aborts the import before profile writes or the migration marker; the legacy CloneStore preferences remain untouched.
- Add Android instrumentation coverage for queue ordering, main-thread callbacks, returned-record isolation, corrupt-registry failure propagation, closed-repository rejection and strict ProfileStore migration-marker protection.
- Add a CI source-contract check for the repository's executor, callback, strict-read, defensive-copy and no-Room/no-Engine boundaries.

### Stage 7.9.2 — Expanded repository surface and strict settings reads

Implementation now also includes:
- Async read/write for collapsed Space keys, master GPS, global device/SIM metadata, and last confirmed active-launch marker.
- Commit-aware CloneStore setters for collapsed Spaces, master GPS, global metadata, and active launch marker. Existing call sites may ignore the returned boolean for source compatibility; they will be reviewed separately before async adoption.
- Strict validation of preference types, JSON field types, Space numbers, and active-launch composite identity. Repository writes preflight existing values so malformed settings are reported as corrupt data and are not overwritten.
- Strict ProfileStore reads for global and per-clone settings; unknown schema versions and malformed field types become typed failures rather than empty/default success.
- Async ProfileStore save and field-clear operations with defensive copies, plus queued legacy location import.
- Android instrumentation for round trips, malformed settings, active marker identity and unsupported ProfileStore schema.

### Stage 7.9 implementation scope and validation status

- UI adoption is staged separately from the repository foundation. SetLocationActivity, GlobalEnvironmentActivity and the Spaces dashboard are covered by the later sub-stages below; other mutation screens and startup/Engine lifecycle remain pending.
- The facade serializes only calls submitted to its own executor. Existing direct synchronous CloneStore writes are outside that queue; ID allocation is not an atomic reservation.
- Remaining MainActivity clone mutations, batch uninstall and shortcut launch reads still require separate review before async adoption.
- Baseline Stage 7.9.2 CI run #44288278229 completed successfully: 28/28 Android instrumentation tests passed (0 skipped, 0 failed), source audit passed, unsigned release APK compiled, and APK audit passed. Follow-up lifecycle hardening and Stage 7.9.3 UI adoption are under CI run #44292220009; that run is still pending.
- Room remains inactive; no data migration, cutover, session/account data operation or startup behavior change is introduced.


### Stage 7.9.3 — First UI caller adoption: per-clone location settings

- SetLocationActivity now requires an explicit valid clone identity and refuses to present a missing/corrupt clone as a global GPS target.
- Save and disable operations use AsyncCloneRepository.upsertClone; the UI disables the action while the write is pending and only requests package/user-scoped hook synchronization after confirmed persistence success.
- A failed write remains on-screen, re-enables the action, and displays the repository failure instead of showing success or closing the screen.
- Hook synchronization remains a separate engine side effect and is not represented as proof that a physical device or third-party app accepted the simulated location.
- The application-scoped repository singleton is recreated if a caller previously closed it. Unsupported profile-field clear requests are classified as invalid input before storage operations.
- Added source-contract coverage for location UI persistence ordering and fail-closed behavior.
- GlobalEnvironmentActivity, other clone mutation screens, startup hooks, Engine lifecycle, and Room runtime wiring remain unchanged in this substage.


### Stage 7.9.4 — Global environment settings UI adoption

- GlobalEnvironmentActivity now loads global device/SIM metadata and Master Mock GPS asynchronously through AsyncCloneRepository. Save remains disabled until both reads succeed; a corrupt/unreadable setting is surfaced rather than replaced with defaults.
- Global profile metadata is saved first, then Master Mock GPS is saved as a second independent commit. The UI does not claim these two writes are one atomic transaction.
- If the profile save fails, the screen reports failure and does not attempt the Master GPS write or hook synchronization.
- If the profile save succeeds but Master GPS fails, the UI explicitly reports the partial commit and does not request hook synchronization. The saved profile is not silently rolled back.
- Hook synchronization is requested only after both commits are confirmed. The message describes a request, not proof that a physical device or virtualized app accepted any location.
- Device model, country and SIM values remain metadata-only; no unsupported device/SIM identity hooks were introduced.
- Added a source-contract test and CI step for asynchronous reads/writes, partial-commit reporting and synchronization ordering.
- No other UI mutation callers, startup hooks, Engine lifecycle, Room runtime wiring, CloneStore migration/cutover, or account/session data are changed by this stage.


### Stage 7.9.5 — Spaces dashboard strict asynchronous reads and collapse persistence

- MainActivity now obtains the clone registry through AsyncCloneRepository.loadClones and collapsed Space numbers through loadCollapsedSpaces; grouping is performed from the strict returned snapshot.
- The dashboard keeps the last rendered Spaces UI intact when either read fails. Corrupt registry data is no longer silently presented as an empty Space list, and corrupt collapsed-state data is not silently interpreted as every Space being expanded.
- The global profile summary is loaded asynchronously; read failure is displayed as unavailable rather than showing CloneStore fallback defaults.
- Individual Space collapse/expand changes use setSpaceCollapsed and refresh only after the commit is confirmed. The header is disabled while the write is pending.
- Collapse/expand all reads the current clone and collapsed-state snapshots, then applies each Space update serially. If a later write fails, the UI reports that earlier Space changes may already have committed and reloads the current state; no false multi-key atomicity claim is made.
- Refresh generations discard stale asynchronous callbacks so an older request cannot overwrite a newer dashboard render.
- Added a CI source-contract test for strict async reads, commit-aware collapse behavior, partial batch status and preserved Engine install/uninstall ordering.
- Shortcut launch, duplicate, rename, clone metadata writes, single/batch uninstall and Engine operations remain unchanged in this sub-stage. No Room runtime wiring, migration/cutover, session/account data or startup behavior changes.
- Android Emulator, Source Audit, unsigned release build and APK Audit validation for this sub-stage are pending the current CI run.


### Stage 7.9.6 — MainActivity clone mutation caller adoption

- Shortcut launch now reads the clone registry through strict AsyncCloneRepository.loadClones, validates the shortcut package/user identity and launches only a matching registered clone. Corrupt/unreadable registry state no longer falls through a legacy getter.
- Clone duplication allocates the next package-scoped user ID through the repository, installs through the existing Engine API, then asynchronously persists the clone entry. If persistence fails, it attempts Engine uninstall even if the Activity is finishing, and reports whether cleanup was confirmed while the UI is still available. The Engine install-before-registry-write ordering is preserved.
- Rename and per-clone device/SIM metadata writes use AsyncCloneRepository.upsertClone. In-memory edited fields are restored on commit failure; metadata hook synchronization is requested only after confirmed persistence success. Device/SIM values remain metadata-only and are not claimed to be applied by the current engine.
- Single and batch uninstall still call Engine first. A registry record is removed asynchronously only after Engine confirms uninstall. Batch uninstall loads a strict snapshot, processes selected clones sequentially, waits for each registry commit before moving to the next, and reports separate counts for confirmed removals, Engine failures and registry commit failures.
- Batch uninstall continues after a registry commit failure because the Engine removal has already occurred; the stale registry record is retained and counted for later inspection. No claim of an atomic batch operation is made.
- Added a CI source-contract test covering strict shortcut reads, duplicate install/persist/cleanup order, rename/profile commit handling, uninstall ordering and batch sequencing.
- AsyncCloneRepository serializes its own queue only. User-ID allocation is not an atomic reservation across other legacy synchronous callers; this limitation remains until all allocation callers adopt a coordinated reservation API.
- This stage does not change Engine internals, clone app-private data, sessions/accounts, Room runtime wiring, migration/cutover or main branch. Android Emulator, Source Audit, unsigned release build and APK Audit for this sub-stage are pending.


### Stage 7.9.7 — AddApp creation and Dashboard read adoption

- AddAppActivity now obtains package-scoped user IDs through AsyncCloneRepository and persists new clone records asynchronously. Direct CloneStore allocation/upsert calls were removed from this Activity.
- Preserves the required Engine install-before-registry-write ordering. If the async registry commit fails, Engine uninstall cleanup is attempted even when the Activity has already been destroyed; cleanup is reported as confirmed only when Engine verifies package absence.
- Batch clone creation is now sequential: each selected app waits for its own allocation, Engine install and registry commit result before the next app begins. The screen does not finish before the batch callbacks complete, and it reports aggregate success/failure counts. Per-app success toasts are suppressed in batch mode.
- DashboardActivity no longer calls the legacy CloneStore.getAll fallback for its counts. It loads a strict async snapshot, computes clone/Space counts only on success, and displays unavailable counts plus an error message if the registry cannot be validated.
- Added `scripts/test_add_app_dashboard_async_persistence_contract.py` and wired it into the CI workflow.
- Allocation is still a lookup, not a durable reservation. AsyncCloneRepository serializes its own operations, but a second allocator may obtain the same free ID during the gap between allocation and the later Engine install/registry commit. A coordinated reservation protocol remains a separate hardening item; no atomicity claim is made.
- No Room runtime wiring, migration/cutover, startup hook changes, Engine internals, clone app-private data, sessions/accounts, or main branch changes. Physical-device validation remains outstanding.
- CI run #44357241095, commit `335bab1c1f5dcfbfec23b4564d760ba201f20c1d`: **30/30 Android Emulator tests completed, 0 skipped, 0 failed**; all contract tests, Source Audit, unsigned release APK build and APK Audit passed.
- Duplicate PR-triggered CI run #44357228454 also passed **30/30 Android Emulator tests**, Source Audit, APK build and APK Audit. Its isolated signing job succeeded and uploaded [VeyraVault-Signed-Release.zip](https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44357228454/artifacts/14456211086) (artifact ZIP SHA-256: `33dd9b6501d254361753b63cb101db1afb0bcc557e09b792581af9caeed0a60a`). The signing log includes non-blocking META-INF signature-coverage warnings.
- Unsigned build/audit artifact: [VeyraVault-unsigned-build](https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44357241095/artifacts/14453109885) (artifact ZIP SHA-256: `aeb07594efc675039b5c4efcd39d0c7f8bce44c5a8840df92457805945ae6bd2`).
- Allocation remains a lookup rather than a durable reservation; simultaneous allocator calls may still race between ID allocation and final upsert. No atomic reservation guarantee is claimed.
- No Room runtime wiring, migration/cutover, startup behavior, Engine internals, clone app-private data, sessions/accounts or main branch changes.
