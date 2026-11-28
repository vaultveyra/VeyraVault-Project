# Stage 6 — Process lifecycle and clone-hook isolation

## Scope and safety boundary

This stage audits the exact pinned BlackBox revision and removes host-process mutations that were incorrectly being used as if they were per-clone settings. It does not rewrite the virtualization engine, clone identifiers, clone persistence, or virtual app data. No session data is cleared or migrated.

## Pinned engine evidence

The audited engine revision is `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`.

Source review confirms:

- `BProcessManagerService.startProcessLocked()` tracks virtual processes by virtual UID and process name, allocates a BlackBox process slot, and starts the app through a generated host process name from `ProxyManifest.getProcessName(app.bpid)` (the `host:pN` process family).
- The process map is keyed using the virtual UID and process name; the process record carries package/process identity and virtual user ID.
- `BActivityThread.bindApplication(packageName, processName)` and `handleBindApplication()` create and bind the virtualized app Application inside that virtual process.
- The pinned engine includes `top.niunaijun.blackbox.fake.frameworks.BLocationManager`. Its `setPattern(userId, packageName, pattern)` and `setLocation(userId, packageName, location)` methods explicitly accept both virtual user ID and package name.
- The pinned source tree does not contain the previously reflected `BDeviceManager` or `BDeviceConfig` classes. The old reflective device-profile branch therefore could not be confirmed as a supported API in this engine revision.

## Confirmed problems in the app integration

### 1. Host-global location override was not clone-scoped

The old `VirtualHookManager` stored one mock-GPS state in static fields and replaced the host app's `LocationManager.mService`. Since virtual apps run in BlackBox-managed `host:pN` processes, this host-side proxy is not a reliable way to configure the target virtual app. Iterating clones also repeatedly overwrote the same static location values.

### 2. Host Build mutation was not a virtual-device API

The old `applyDeviceProperties()` directly rewrote static fields on `android.os.Build` in the host process, then attempted reflection against device manager/configuration classes absent from the pinned engine source. This was neither a supported per-clone engine contract nor a safe host integration.

### 3. UI overstated device/SIM profile support

The global and per-clone screens previously described saved brand/model/country/operator metadata as applied hardware or region overrides. The pinned engine source does not expose the reflected device API used by the app. Those values must therefore be presented as saved metadata only, not as applied device state or a way to bypass third-party regional controls.

## Changes in this stage

- Remove process-global static mock-location state and the host `LocationManager.mService` proxy.
- Remove host-process writes to `android.os.Build` and unsupported `BDeviceManager/BDeviceConfig` reflection.
- Keep location configuration through the pinned engine's package/user-scoped `BLocationManager` methods.
- Keep existing device/SIM profile fields and clone records intact for compatibility, but do not claim they are applied. No stored values are deleted or migrated.
- Update Persian and English UI wording so global/per-clone device values are explicitly identified as saved metadata only.
- Keep `CloneStore.syncAllHooks()` focused on per-clone engine location settings.
- Add `scripts/test_hook_isolation_contract.py` and a CI step to prevent host-global hook mutations and verify package/user-scoped location calls.
- Separately, `Engine.launchClone()` now persists the last-active marker only after an explicit successful engine launch.

## What remains unverified

- Physical-device behavior of location results across two or more concurrently running clones.
- OEM and Android-version differences in BlackBox's location hook behavior.
- Whether other virtualized framework APIs require additional compatibility work.
- Device/SIM profile application: currently not implemented by the pinned engine integration. Do not re-enable host Build mutation as a substitute.

## Validation

CI must pass the profile resolver, security credential, engine launch, hook-isolation, workspace preparation, source audit, unsigned APK compilation, and compiled APK audit steps.

This is source-level and CI validation. It is not a physical-device certification of clone isolation. The generated PR artifact is unsigned and is not a production-installable release.


## Clarification from Stage 8.9 — generic device-service hooks

The absence of BDeviceManager and BDeviceConfig means the pinned Engine does not provide those unified device-profile APIs. It does not mean the Engine contains no device-related service hooks. The pinned source also registers telephony, serial, Android ID and Wi-Fi proxies. Stage 8.9 distinguishes those hooks from a configurable per-Clone profile: the inspected implementations return host-package-derived values, fixed constants, or non-persisted fallback values. See docs/STAGE_8_9_ENGINE_DEVICE_CAPABILITY_AUDIT.md for exact source references and the capability matrix.
