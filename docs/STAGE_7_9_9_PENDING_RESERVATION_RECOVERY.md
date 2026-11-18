# Stage 7.9.9 — Pending Clone Reservation Diagnostics and Safe Manual Recovery

## Status

Implementation is committed on `feat/veyra-vault-product-foundation`. CI validation is pending for the current branch head. This stage follows the validated Stage 7.9.8 durable reservation journal; it does not replace or weaken the reservation invariants.

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

## Tests and CI wiring

- Add instrumentation coverage for the tri-state mapping of true/false/null.
- Add instrumentation proving pending reservation diagnostics are strict and read-only: both clone-registry JSON and reservation-journal bytes remain unchanged after loading.
- Add `scripts/test_pending_reservation_recovery_contract.py` to verify tri-state semantics, Settings/manifest wiring, no automatic release, no uninstall/data-clear/clone-write APIs in the diagnostics Activity, a confirmation dialog, and a fresh Engine-absence recheck before release.
- The pre-existing Room OS process-death harness was made more diagnosable after CI run #500 found one failure in `LegacyCloneRoomProcessDeathInstrumentationTest`. CI run #501 did not execute tests because the Emulator failed to install the debug split APK (0 tests). CI run #502 reached 39 tests but found a marker-publication race: the test process observed an empty marker before the Debug service finished writing its PID.
- Follow-up commits `359f9bfa07b145a999b3df29393753464860d076`, `32501b5c5a1f56fb8ec2f74df2aa2c8b1c63df4c`, and `7d695a1d52e732acf23d57528e3992e203d18a3f` make marker publication temp-file + fsync + rename, wait only for a non-empty marker, add named assertions for every Room table count, and extend the source wiring contract. They do not weaken or skip the process-death test.
- The current branch adds two Android instrumentation tests. The full Emulator suite is expected to contain 39 tests; the actual runner output is authoritative.

## Safety boundaries and limitations

- This is manual diagnostics and recovery, not an automatic startup reconciler.
- A reservation whose package is INSTALLED but has no registry row remains blocked. It requires a separate future recovery design because the original clone metadata may not be reconstructable safely from the reservation alone.
- UNKNOWN remains blocked; no timeout, forced uninstall, or guess-based release is used.
- This does not introduce a cross-process lock. Stage 7.9.8 reservation coordination remains limited to the host app process.
- Physical-device checks are still required for Engine reflection compatibility, interrupted installation, and process restart behavior.
- No Room runtime activation, migration/cutover, changes to CloneStore clone JSON, virtual package data, sessions/accounts, or main branch are performed.

## Current validation

- The new diagnostics source-contract steps pass in CI runs #500 and #502.
- CI #500 completed 39 tests with 38 passing and the existing Room process-death harness failing.
- CI #501 executed zero tests because Android Emulator failed to install the debug split APK.
- CI #502 completed the 39-test suite but the process-death harness failed with `Missing pid in marker:`; this exposed the test-harness marker-publication race described above.
- The follow-up atomic-marker commits are awaiting a fresh CI run on the new branch head. Stage 7.9.9 is not considered fully validated until that run passes the complete Emulator suite, Source Audit, Release build and APK Audit.

## Explicit non-goals

- No auto-expiry or time-based reservation cleanup.
- No automatic uninstall or clone registry reconstruction.
- No clone app-data/session/account deletion or restoration.
- No change to Room status or SharedPreferences runtime source of truth.
- No PR merge or direct main-branch edits.
