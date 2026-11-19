# Stage 7.9.9 — Pending Clone Reservation Diagnostics and Safe Manual Recovery

## Status

Implementation is committed on `feat/veyra-vault-product-foundation`. The Stage 7.9.9 implementation commit `26d0982f24b62ec6ab2a6dce75e5c25235bdb202` passed the complete CI validation in run #508 (push) and run #509 (pull request). This stage follows the validated Stage 7.9.8 durable reservation journal; it does not replace or weaken the reservation invariants.

PR #4 must remain Draft, open, and unmerged.

## Problem

Stage 7.9.8 intentionally retains a reservation if the host process is interrupted after a possible Engine install and before the clone registry commit. This prevents ID reuse, but without a diagnostics surface a user cannot distinguish:
- a package that the Engine explicitly reports as installed, but whose clone registry row is missing;
- a package that the Engine explicitly reports as absent and whose reservation can safely be released;
- an unknown Engine state caused by an unavailable core or reflection/query failure.

A timeout or age-based cleanup is unsafe: it could release an identity while a virtual package still exists.

## Implemented behavior

### Tri-state Engine query

- Add `Engine.CloneInstallState`: `INSTALLED`, `ABSENT`, and `UNKNOWN`.
- The query maps an explicit Boolean true/false from the pinned Engine `isInstalled(package,userId)` API to INSTALLED/ABSENT.
- Missing Engine core, reflection failure, invalid input, or an unexpected result maps to UNKNOWN.
- The existing `isCloneConfirmedAbsent` helper delegates to the tri-state API and returns true only for ABSENT.

### Pending reservation diagnostics UI

- Add non-exported `PendingReservationsActivity`, reachable from Settings.
- Read reservations through `AsyncCloneRepository.loadPendingReservations`; malformed or inconsistent journal data remains a typed failure and is not displayed as an empty list.
- Query each Engine state on a dedicated worker thread; do not block the UI while inspecting pending IDs.
- Display package name, virtual user ID, and one of the three explicit Engine states.
- INSTALLED reservations remain blocked and are described as possible orphaned virtual installs; the UI does not uninstall or auto-create registry rows.
- UNKNOWN reservations remain blocked.
- ABSENT reservations expose a manual release action only.

### Explicit release guard

- Opening the screen or refreshing it never releases a reservation.
- A release requires a user confirmation dialog.
- After confirmation, Engine state is queried again immediately before the repository release call.
- The release API is called only when this fresh query returns ABSENT. If the state changed to INSTALLED or UNKNOWN, the reservation stays blocked.
- The release operation removes only the matching reservation token. It does not uninstall a virtual package, clear clone data, mutate session/account data, or create a registry record.
- Immediately before removing the token, CloneStore also performs a strict consistency read of the clone registry and reservation journal. A package/user identity already present in the registry makes the release fail closed as corrupt/conflicting state; both persisted values remain untouched.

## Tests and CI wiring

- Add instrumentation coverage for the tri-state mapping of true/false/null.
- Add instrumentation proving pending reservation diagnostics are strict and read-only: both clone-registry JSON and reservation-journal bytes remain unchanged after loading.
- Add `scripts/test_pending_reservation_recovery_contract.py` to verify tri-state semantics, Settings/manifest wiring, no automatic release, no uninstall/data-clear/clone-write APIs in the diagnostics Activity, a confirmation dialog, and a fresh Engine-absence recheck before release.
- The pre-existing Room OS process-death harness was made more diagnosable after CI run #500 found one failure in `LegacyCloneRoomProcessDeathInstrumentationTest`. CI run #501 did not execute tests because the Emulator failed to install the debug split APK (0 tests). CI run #502 reached 39 tests but found a marker-publication race: the test process observed an empty marker before the Debug service finished writing its PID.
- Follow-up commits `359f9bfa07b145a999b3df29393753464860d076`, `32501b5c5a1f56fb8ec2f74df2aa2c8b1c63df4c`, and `7d695a1d52e732acf23d57528e3992e203d18a3f` make marker publication temp-file + fsync + rename, wait only for a non-empty marker, add named assertions for every Room table count, and extend the source wiring contract. They do not weaken or skip the process-death test.
- The current branch adds two Android instrumentation tests. On commit `26d0982f24b62ec6ab2a6dce75e5c25235bdb202`, the Emulator runner completed **39/39 tests, 0 skipped, 0 failed**. The newly added Stage 7.9.9 tests and the previously failing Room OS process-death test all passed.

## Safety boundaries and limitations

- This is manual diagnostics and recovery, not an automatic startup reconciler.
- A reservation whose package is INSTALLED but has no registry row remains blocked. It requires a separate future recovery design because the original clone metadata may not be reconstructable safely from the reservation alone.
- UNKNOWN remains blocked; no timeout, forced uninstall, or guess-based release is used.
- This does not introduce a cross-process lock. Stage 7.9.8 reservation coordination remains limited to the host app process.
- Physical-device checks are still required for Engine reflection compatibility, interrupted installation, and process restart behavior.
- No Room runtime activation, migration/cutover, changes to CloneStore clone JSON, virtual package data, sessions/accounts, or main branch are performed.

## Current validation

- CI run #508 (push; run ID `44397505197`) on implementation commit `26d0982f24b62ec6ab2a6dce75e5c25235bdb202`: **39/39 Android Emulator tests passed, 0 skipped, 0 failed**. Source Audit, unsigned Release APK compilation, package/APK audit and artifact upload all succeeded.
- CI run #509 (pull_request; run ID `44397514877`) on the same commit also completed successfully; its isolated signing job was skipped by the workflow for the PR event.
- The full process-death test passed after atomic marker publication (temporary file, flush/fsync, rename) and non-empty-marker polling. The test remains enabled; it was not skipped or weakened.
- [Signed release artifact](https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44397505197/artifacts/14472396111) — artifact ID `14472396111`, SHA-256 ZIP `73c57198625785fcf72c084eac6b6a9b88ba832b1aea72b7833eab0268838652`.
- [Unsigned build and audit artifact](https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44397505197/artifacts/14471299891) — artifact ID `14471299891`, SHA-256 ZIP `1ba33b5c7a27d176691e9641f9b2197b5f5e6dddec221d3d236b9184fcd000a9`.
- Isolated signing verified APK signature schemes v1, v2 and v3 and uploaded the signed artifact. The log also emitted META-INF signature-coverage warnings for build/dependency metadata entries; these were warnings, not CI failures, and should remain visible in release review.
- Runs #500–#502 remain recorded as diagnostic attempts preceding the harness fix; the authoritative passing validation is #508/#509 above.
- Documentation-head validation: CI #511 (run ID `44432122052`) on commit `5acfa24b9b155be4b860c5e9da1ef1fb6d55a74b` also passed **39/39 Emulator tests, 0 skipped, 0 failed**, Source Audit, unsigned Release compilation and APK Audit. [Unsigned build/audit artifact](https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44432122052/artifacts/14488041877) — artifact ID `14488041877`, ZIP SHA-256 `a9cb965de858850ace3fb2c3c96c4e300ab2ef68e02baf2d60c65a3909ed9598`. Signing was skipped for this PR-triggered run; the signed artifact from #508 remains the signed build for the same Android source commit.

## Explicit non-goals

- No auto-expiry or time-based reservation cleanup.
- No automatic uninstall or clone registry reconstruction.
- No clone app-data/session/account deletion or restoration.
- No change to Room status or SharedPreferences runtime source of truth.
- No PR merge or direct main-branch edits.
