# Stage 8.8.9 — Runtime App Lock Activity lifecycle verification

## Objective

Close the Android-runtime test gap left by Stage 8.8.8. Exercise the production `AppLockLifecycleController` through actual Activity lifecycle callbacks, instead of relying only on pure-Java deadline/state tests or source-text assertions.

## Implementation

- Add `AppLockLifecycleProbeActivity` under `app/src/debug` and declare it only in the Debug manifest. It is not part of the Release manifest.
- Add `AppLockLifecycleRuntimeInstrumentationTest` under `app/src/androidTest`.
- The test runs in the target app's main process, checks `ProcessUtils.isMainProcess`, and invokes the same production `AppLockLifecycleController.initialize(Application)` entry point called by `VaultApp.onCreate()`.
- Launch two real probe Activities. Verify that creating/transitioning between Activities does not lock while one remains started. Finish the second Activity and verify the first remains authenticated. Finish the final Activity and verify the configured immediate background lock is delivered by the production main-thread Handler.
- Snapshot and restore the original credential keys, timeout preference, and in-process `sessionUnlocked` flag. Verify the preference values are exactly restored. No app data clearing or Clone/session/account mutation is performed.
- Add a source contract for the production startup call, main-process guard, Debug-only probe Activity, test assertions, cleanup, and CI wiring.

## Validation boundary

- This Android instrumentation exercises the production controller and real Activity callbacks on the GitHub-hosted Android Emulator.
- The Debug variant still uses `RoomTestApplication` to avoid starting the virtual Engine during Room instrumentation. Therefore this test does not execute the complete `VaultApp.onCreate()` method; the production call site and main-process guard are additionally source-contract checked.
- This does not replace physical-device validation, OEM background-management testing, or a full OS kill/restart test of the primary VeyraVault process.

## Safety and compatibility

- Release manifest and Release source behavior are unchanged by the Debug-only probe Activity.
- PIN/Pattern credential format and hashing remain unchanged.
- CloneStore, Clone package data, account/session data, Engine lifecycle, Room activation, and migration/cutover are not changed.
- PR #4 stays open and Draft; `main` is not modified.
