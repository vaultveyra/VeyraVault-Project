# Stage 8.8.3 — Dashboard read-only security and Engine status

## Scope

Add a read-only Dashboard summary for four independently sourced states:

- App lock: not configured, configured with an unlocked session, or configured with a locked session.
- Android Device Admin: active or inactive, using the platform's actual administrator state.
- Engine Core: detected or not detected. Detecting the Core object does **not** prove that the Engine is fully initialized or ready.
- Clone profile lifecycle callback: a bounded human-readable mapping of the existing diagnostic value.

## Safety and lifecycle

- The Dashboard invokes only read APIs for these statuses. It does not verify credentials, unlock or lock the session, change lock configuration, activate/deactivate Device Admin, install/uninstall clones, or modify Clone data.
- Reflection and system-service reads run on a single background executor.
- Results are posted back to the main thread and discarded when the Activity is paused, destroyed, or superseded by a newer refresh.
- The executor is shut down when the Activity is destroyed.
- Diagnostic strings are mapped to known labels; raw diagnostic values are not displayed.

## Verification

The CI contract checks the read-only method allowlist, forbidden mutators, lifecycle handling, localized labels, safe diagnostic mapping, and the distinction between Core detection and full Engine readiness. Full Android compilation, instrumentation, source audit, release APK and APK audit remain required before this stage is considered CI-validated.

## Non-goals

No Engine lifecycle behavior, security policy, permission state, account/session data, Clone registry, SharedPreferences schema, Room activation, or startup sequence is changed.
