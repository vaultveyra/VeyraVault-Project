# Stage 8.8.8 — App-lock fresh-process isolation

## Objective

Verify on Android that an authenticated in-memory app-lock session is not inherited by a newly created application process. This supplements the deterministic deadline and Activity-state tests from Stages 8.8.6 and 8.8.7.

## Implementation

- Add `AppLockSessionProbeService` under `app/src/debug` only.
- Register the probe in the Debug manifest with its own process, `:app_lock_session_probe`, and `android:exported="false"`.
- The service reports only the result of the production `SecurityManager.isSessionUnlocked()` API through a local Messenger binder.
- Add `AppLockProcessIsolationInstrumentationTest`: it creates a temporary test PIN using the production credential API, verifies the instrumentation process is unlocked, binds to the fresh isolated process, and asserts that process reports the session locked.
- The test snapshots and restores the two credential preference entries and the original in-process session flag in a `finally` block. It does not clear app data, CloneStore, clone package data, accounts, or user sessions.
- Add a source contract test and wire it into CI before emulator instrumentation.

## Validation boundary

This test proves fresh-process isolation on the Android Emulator. It does **not** claim to kill and restart the primary VeyraVault process itself, nor does it prove physical-device behavior. The Debug build continues to use `RoomTestApplication`, so the production `VaultApp` startup and `AppLockLifecycleController` registration are not exercised by this test. A separate non-destructive host-process restart test and physical-device validation remain outstanding.

No production manifest, `VaultApp`, `SecurityManager`, `AppLockLifecycleController`, credential algorithm, CloneStore key, clone data, account data, or Session data is changed by this stage.
