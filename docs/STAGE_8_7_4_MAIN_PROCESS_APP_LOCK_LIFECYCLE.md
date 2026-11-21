# Stage 8.7.4 — Main-process app-lock lifecycle and background timeout

## Scope
- Add a dedicated `AppLockPolicy` preference namespace that is independent of the stored PIN/Pattern credential hash.
- Offer four explicit timeout values: immediately, 30 seconds, 1 minute, and 5 minutes.
- Default to immediate locking when the final host Activity leaves the foreground, but only when a PIN or Pattern is configured.
- Register `AppLockLifecycleController` only in the package's main process, using the exact process-name guard. BlackBox clone processes do not receive this controller.
- Keep all clone profile lifecycle callbacks unchanged.

## Runtime behavior
- The controller counts started Activities and schedules a lock only after the last host Activity stops.
- Returning to the foreground cancels an unexpired lock timer. Activity configuration recreation (rotation, locale/theme recreation) is explicitly excluded from background transitions; the immediate option also has a 250 ms main-loop grace.
- The deadline uses `SystemClock.elapsedRealtime()` so elapsed time remains meaningful across device deep sleep; a deadline already passed is enforced before `BaseActivity.onResume()` decides whether to show the existing authenticated lock screen.
- A pending timer re-checks that the app is still backgrounded and that a credential remains configured before calling `SecurityManager.lockSession()`.
- The existing PIN/Pattern screen remains the sole unlock path.

## Data and safety boundaries
- Timeout preferences use `veyra_security_policy_prefs`; credential storage remains in its existing namespace and keys.
- No PIN/Pattern hash is rewritten by a timeout selection.
- No CloneStore, clone data, package/user identity, account/session content, Engine callback, Room migration, VPN, GPS, or Device Admin state is modified.
- No lock behavior is registered into Clone processes.

## Verification
- Add instrumentation coverage for default behavior, all supported timeout values, invalid-value rejection without overwrite, malformed preference fallback, and exact restoration of the original preference.
- Add a source contract for main-process isolation, lifecycle scheduling, deep-sleep-safe deadline checks, policy settings, and existing authenticated unlock routing.
- Android Instrumentation, source audit, release compilation, APK audit, and upload must pass before the stage is CI-verified.
- Physical-device background/foreground timing and behavior under OEM task management remain to be tested.
