# Stage 8.8.9 — Runtime App Lock Activity lifecycle verification

## Objective

Exercise the production `AppLockLifecycleController` through actual Android Activity lifecycle callbacks, rather than relying only on pure-Java deadline/state tests or source-text assertions.

## Implementation

- Add `AppLockLifecycleProbeActivity` under `app/src/debug` and declare it only in the Debug manifest. It is not part of the Release manifest.
- Add `AppLockLifecycleRuntimeInstrumentationTest` under `app/src/androidTest`.
- The test runs in the target app's main process, checks `ProcessUtils.isMainProcess`, and invokes the same production `AppLockLifecycleController.initialize(Application)` entry point called by `VaultApp.onCreate()`.
- Launch the initial probe Activity through `ActivityScenario`; launch the second probe Activity by calling `startActivity` from the first Activity itself. The test asserts both Activities have the same task ID, so the transition models normal in-app navigation rather than two independently launched test tasks.
- Observe actual `onActivityResumed`, `onActivityPaused`, and `onActivityStopped` deliveries using an additional `Application.ActivityLifecycleCallbacks` observer. The observer tracks which probe Activity is currently resumed and waits for the first Activity to resume again before checking that the session is still unlocked.
- Avoid `Instrumentation.startActivitySync` and `waitForIdleSync` because both introduce a global main-loop-idle dependency that proved unreliable in the hosted emulator.
- Verify that navigating from the first Activity to the second and back does not lock the session, then finish the final Activity and verify that the production main-thread Handler locks the session using the configured immediate timeout.
- Snapshot and restore the original credential keys, timeout preference, and in-process `sessionUnlocked` flag. Verify the preference values are exactly restored. No app data clearing or Clone/session/account mutation is performed.
- Add a source contract for the production startup call, main-process guard, Debug-only probe Activity, same-task navigation, callback-driven assertions, cleanup, and CI wiring.

## Validation boundary

- Android instrumentation is intended to exercise the production controller and real Activity callbacks on the GitHub-hosted Android Emulator.
- The Debug variant still uses `RoomTestApplication` to avoid starting the virtual Engine during Room instrumentation. Therefore this test does not execute the complete `VaultApp.onCreate()` method; the production call site and main-process guard are additionally source-contract checked.
- This does not replace physical-device validation, OEM background-management testing, or a full OS kill/restart test of the primary VeyraVault process.

## Safety and compatibility

- Release manifest and Release source behavior are unchanged by the Debug-only probe Activity.
- PIN/Pattern credential format and hashing remain unchanged.
- CloneStore, Clone package data, account/session data, Engine lifecycle, Room activation, and migration/cutover are not changed.
- PR #4 stays open and Draft; `main` is not modified.
