# Stage 7.9.10 — Physical-device validation protocol for Clone reservations

## Status and intent

This document is a test protocol, not a claim that physical-device tests have been run. Automated CI validation for Stage 7.9.9 is complete; real-device compatibility and interruption behavior remain unverified.

Target implementation baseline:
- Stage 7.9.9 Android source: `26d0982f24b62ec6ab2a6dce75e5c25235bdb202`.
- Documentation-follow-up branch head at protocol creation: `5acfa24b9b155be4b860c5e9da1ef1fb6d55a74b`.
- Successful Emulator validation: CI #508/#509 and documentation-head CI #511; 39/39 instrumentation tests, 0 skipped, 0 failed.
- SharedPreferences/CloneStore remains the sole active runtime persistence source. Room remains inactive.

PR #4 must remain Draft, open and unmerged. Do not merge or change `main` as part of this protocol.

## Non-destructive test boundary

Run this protocol only on a spare physical device or an isolated test installation containing no valuable Clone data. Use a benign, dedicated test APK/package whose virtual installation can safely be created and removed. Do not use a Clone that contains a real account, active session, personal data, or irreplaceable app state.

Hard prohibitions:
- Do not clear VeyraVault application data or reset SharedPreferences.
- Do not clear, uninstall, overwrite, or restore any existing Clone's app-private data.
- Do not test with real account/session data.
- Do not force-uninstall an existing virtual package to make a test pass.
- Do not release a reservation when Engine state is UNKNOWN.
- Do not activate Room, import data, dual-write, or perform persistence cutover.
- Do not run destructive failure injection on the user's primary device.

A disposable test install must be created separately. If the test cannot be isolated from valuable Clone/session state, stop and do not run the physical interruption scenarios.

## Preflight record

Record only test-environment metadata:
- Device manufacturer/model and Android version/API level.
- CPU ABI and security patch date.
- VeyraVault version and source commit.
- Artifact origin and SHA-256.
- Whether the Engine/core is discoverable.
- Number of pre-existing test Clones, recorded as a count only.

Install only a signed APK whose signature is verified. The signed artifact from CI #508 is available at:
`https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44397505197/artifacts/14472396111`
Its ZIP SHA-256 is:
`73c57198625785fcf72c084eac6b6a9b88ba832b1aea72b7833eab0268838652`

The CI signing log verified APK signature schemes v1, v2 and v3. It also emitted META-INF signature-coverage warnings for dependency/build metadata; retain those warnings in release review.

## Test cases

### PD-01 — Baseline and app upgrade smoke check

1. Use the isolated test installation only.
2. Install/update the signed test build without clearing app data.
3. Open Dashboard, Spaces, Settings and Pending Clone ID reservations.
4. Confirm the screen opens, language selection works, and no pending reservations are fabricated.
5. Confirm the existing test Clone count and identities are unchanged.

Expected: no startup import, no Room activation, no journal mutation, and no changes to existing Clone/session state.

### PD-02 — Normal Clone creation

1. Select the dedicated benign test package in Add App.
2. Create one Clone and wait for the final success result.
3. Repeat creation for that same test package through the supported flow.
4. Inspect Spaces and the Pending reservations screen.

Expected:
- Each Clone has a unique package-scoped virtual user ID.
- A committed Clone has exactly one registry entry.
- The corresponding pending reservation is consumed.
- No reservation remains for a fully committed operation.
- Previously existing Clone identities remain unchanged.

### PD-03 — Sequential/batch creation

1. Select multiple benign test packages or use the supported batch flow.
2. Allow each operation to finish before evaluating the aggregate result.
3. Repeat the batch once.

Expected: IDs remain unique within each package; partial failures are surfaced; failed or uncertain Engine cleanup does not silently free a reservation; successful commits consume only their own tokens.

### PD-04 — Host-process restart with a pending reservation

This test requires a debug-only deterministic test seam or instrumentation controller. Do not attempt to time a force-stop manually on a production build.

1. In the isolated test installation, pause immediately after the reservation journal commit and before Engine installation.
2. Record the test reservation's package and virtual user ID in the test report (not in public logs).
3. Terminate only the isolated host test process.
4. Relaunch VeyraVault and open Pending Clone ID reservations.

Expected:
- The reservation survives process death.
- It is not automatically released at startup.
- The same identity is not allocated to another Clone while the reservation remains present.
- If a fresh Engine query confirms ABSENT, manual release is offered and requires confirmation.
- If query returns UNKNOWN, the reservation remains blocked.

### PD-05 — Engine-installed, registry-not-yet-committed interruption

This test also requires the isolated debug-only seam, paused after Engine installation succeeds but before `commitReservedClone`.

1. Use only the disposable test package and test installation.
2. Pause after the Engine confirms installation but before the registry commit.
3. Terminate the isolated host test process.
4. Relaunch and inspect pending reservations.

Expected:
- The reservation remains present.
- Engine reports INSTALLED on a supported device.
- The UI does not uninstall the virtual package or reconstruct a Clone row automatically.
- The ID remains blocked.
- The test is recorded as an orphaned-install recovery case requiring a separately reviewed recovery design.

Do not attempt to repair this test case by deleting the virtual package or editing SharedPreferences manually.

### PD-06 — Manual release guard

Use a disposable test reservation for which Engine explicitly reports ABSENT.

1. Open Pending Clone ID reservations and verify ABSENT is shown.
2. Tap Release reservation, then Cancel.

Expected: reservation bytes remain unchanged.

3. Open the confirmation again and confirm.

Expected: Engine is queried again immediately before release; only if the fresh result is ABSENT is the exact token/package/user reservation removed. The operation does not delete an app, Clone record, account, session, or app data.

The transition from ABSENT to INSTALLED/UNKNOWN must be covered with an instrumented fake/query seam in automated tests; do not try to create this race by manipulating a real Engine installation during a user test.

### PD-07 — Unknown Engine state

Use an automated fake/core-unavailable test for the UNKNOWN branch. Do not break or uninstall the real Engine on a device holding test or user data.

Expected: UNKNOWN is displayed distinctly, release is not offered, and the reservation remains persisted.

### PD-08 — Reboot persistence (optional)

On the isolated test installation, reboot the device while a harmless pending reservation exists. Reopen the diagnostics screen.

Expected: the journal is still parseable, and the reservation remains blocked until a fresh Engine query and the normal explicit recovery flow.

## Required debug-only test seam

PD-04 and PD-05 cannot be made deterministic by tapping quickly or relying on timing. Before executing them, add a debug-only fault-injection controller that:
- Pauses at the two exact checkpoints: after reservation journal commit/before Engine install, and after Engine install/before registry commit.
- Is compiled only into the Debug/test variant and is absent from the Release manifest and APK.
- Uses a dedicated fixture package and test-only state.
- Has an explicit timeout and a safe test-runner abort path.
- Does not expose a public/exported production component.
- Never changes real Clone records, session data, or app-private package data.

Add instrumentation proving the release build does not contain the test seam. This is a separate reviewed change; do not add the seam to release code merely to make device testing easier.

## Evidence and acceptance

For each test, record:
- Test ID and pass/fail/not-run.
- Device/API/ABI and app commit.
- Before/after Clone counts and test package identities only.
- Whether reservation journal bytes were preserved, consumed, or exactly one token was released.
- Engine state observed (INSTALLED/ABSENT/UNKNOWN).
- Relevant filtered logs with tokens, account identifiers, session contents and personal data redacted.

Accept Stage 7.9.10 only when:
1. PD-01 through PD-03 pass on a real supported device.
2. PD-04 and PD-05 pass using the debug-only deterministic seam on the disposable installation.
3. PD-06 and PD-07 pass with automated race/state coverage and the physical-device UI flow.
4. PD-08 passes where the device is available.
5. No pre-existing Clone identity or user data changed.
6. The Release APK contains no debug test controller.
7. Any Engine reflection incompatibility is reported as UNKNOWN and never bypassed.

## Known limitations

- The existing reservation synchronization is static and protects callers only within the host app process. It is not a cross-process mutex.
- The successful Emulator Room process-death test validates transactional Room-import rollback, not process death during actual Clone provisioning.
- Stage 7.9.9 provides safe manual release for confirmed-absent reservations. It does not reconstruct metadata for an INSTALLED orphan.
- The physical-device protocol has not been executed. A completed CI run is not physical-device evidence.
- No Room runtime activation, migration/cutover, or user-facing complete backup/restore is part of this stage.
