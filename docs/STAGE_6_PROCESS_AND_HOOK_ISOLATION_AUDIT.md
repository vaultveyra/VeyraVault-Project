# Stage 6 — Process lifecycle and clone-hook isolation audit

## Scope and safety boundary

This stage performs a source-level audit of host application startup, clone launch bookkeeping, and the existing environment hooks. It deliberately does not rewrite the BlackBox process model, clone identifiers, stored clone records, or virtual app data. No session data is cleared or migrated.

## Confirmed source findings

### 1. Host startup currently applies more than one clone's settings to process-global state

- `VaultApp.onCreate()` calls `VirtualHookManager.installProcessHooks()` and then `CloneStore.syncAllHooks()`.
- `CloneStore.syncAllHooks()` iterates every saved clone and calls `VirtualHookManager.syncCloneHooks()`.
- `VirtualHookManager` stores mock-location state in static fields (`activeMockGps`, `activeLat`, and `activeLng`).
- The same manager replaces the host `LocationManager.mService` with a proxy whose location response reads those static fields.
- Consequently, iterating multiple clone records can overwrite the single process-wide location state repeatedly. The final static values depend on iteration order, not on an independently isolated per-clone context. This is a confirmed source-level isolation hazard; exact runtime impact depends on the engine's process topology and API call paths.

### 2. Device Build fields are modified in the host process

`VirtualHookManager.applyDeviceProperties()` writes static fields on `android.os.Build` before it attempts the BlackBox `BDeviceManager.setDeviceConfig(userId, config)` call. The static Build writes are process-wide and do not carry a package or virtual-user scope. The engine configuration call is explicitly passed a virtual user ID, but its effective behavior still requires runtime verification.

This means the host-side Build mutation must not be described as per-clone isolation. It can affect other code executing in the same process and can be overwritten by subsequent clone configuration calls.

### 3. Clone launch bookkeeping now records only successful launches

Previously, `Engine.launchClone()` wrote the last-active-clone marker before invoking the engine launch method. A failed or exceptional launch could therefore replace the marker even though the app did not start.

The method now:
1. Confirms the package is installed for the requested virtual user (or installs it successfully).
2. Applies the requested clone's engine configuration.
3. Calls the pinned engine's `launchApk(packageName, userId)`.
4. Requires an explicit boolean `true`.
5. Only then writes `CloneStore.recordActiveLaunch()`.

A failed launch leaves the previous last-successful-launch marker unchanged. Clone IDs, clone records, session data, and install state are not rewritten by this adjustment.

## What is not yet proven

- Whether each virtual app runs in a dedicated process, a shared virtual process, or a process selected dynamically by BlackBox.
- Whether the pinned engine's location and device hooks are applied inside the target virtual process and consistently isolated by both package name and virtual user ID.
- Whether any virtualized app reads host-process `Build` or host `LocationManager` directly rather than through the engine's fake framework.
- Whether the startup-time host proxy is required by a supported engine path. It must not be removed until the pinned engine process lifecycle and device behavior are verified.

## Next engineering steps

1. Trace the pinned BlackBox process startup, process selection, application binding, and fake-framework initialization against the exact vendored revision.
2. Add runtime diagnostics that report process name and hook installation outcome without collecting app content or session data.
3. Prefer engine APIs explicitly scoped by `(packageName, userId)`; isolate or remove process-global host mutations only after compatibility tests demonstrate the replacement behavior.
4. Add device tests with at least two clones configured with distinct locations and device profiles, launch them in alternating order, and verify that one clone's configuration does not leak into another or the host app.
5. Keep all persistence changes additive and separately tested. No Room migration is included in this stage.

## Validation

- `scripts/test_engine_contract.py` now checks that the active-launch marker is written only after an explicit successful engine launch.
- GitHub Actions must pass the engine contract test, profile/security tests, workspace preparation, source audit, release compilation, and APK binary audit.
- This remains a static/source-and-CI validation until physical-device tests are performed. It is not a certification of cross-clone isolation.
