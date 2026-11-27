# Stage 8.9 — Pinned Engine device and environment capability audit

## Status

Source audit completed on 2026-11-22. This stage audits the exact BlackBox revision used by VeyraVault and the app's current profile transport. It does not add runtime hooks, modify the Engine, or change any Clone data.

## Exact source revision and method

VeyraVault's build workspace pins:

- Repository: https://github.com/ALEX5402/NewBlackbox
- Immutable Engine commit: 89b59836c66f173756a4ae258cf379a957649820
- Pin declaration: ENGINE_COMMIT in scripts/prepare_workspace.py.

The audit inspected the recursive source tree and relevant implementation at this immutable revision, then compared those hooks with the current VeyraVault profile schema, runtime provider and VirtualHookManager.

### Important clarification to the earlier Stage 6 finding

The Stage 6 statement that this revision does not contain BDeviceManager or BDeviceConfig is still accurate. It must not be interpreted as saying the Engine contains no device-related hooks at all.

The pinned Engine does register several service hooks for telephony, serial identifiers, Android ID, Wi-Fi and settings. The location service stores its per-user package settings in `SparseArray<HashMap<String, BLocationConfig>>`: the outer map is keyed by virtual user ID and the inner map is keyed by package name. The key distinction is that the presence of a service hook does not establish a configurable, durable, package/user-scoped device profile. Most of the hooks below return a host-derived value, a fixed constant, or an unstable fallback rather than reading a VeyraVault per-Clone setting.

## Virtual process isolation evidence

- BProcessManagerService.startProcessLocked derives a virtual UID using BUserHandle.getUid(userId, appId(packageName)) and stores process records under that virtual UID and process name.
- The process record retains the virtual package and user ID.
- BActivityThread.getAppPackageName() and getUserId() expose the current virtual package/user identity to Engine hooks.
- BActivityThread.initProcess rejects initialization of an already bound ActivityThread with a different package name.

This provides a package/user process context in which a future hook could resolve a Clone-specific value. It does not make a property per-Clone by itself; each property still needs an explicit scoped source, correct hook, lifecycle ordering, readback and cross-Clone tests.

Source references:
- BProcessManagerService.java: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/core/system/BProcessManagerService.java#L54-L85
- BActivityThread.java: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/app/BActivityThread.java#L136-L184

## Capability matrix

| Capability | Exact pinned Engine behavior | Per-Clone configurable value in current VeyraVault profile? | Audit classification |
|---|---|---:|---|
| Locale | VeyraVault resolves clone → global → system and applies locale in the virtual app process before target Application creation. | Yes | Implemented in source; physical-device verification remains open. |
| Time zone | VeyraVault resolves clone → global → system and applies TimeZone.setDefault in the virtual app process before target Application creation. | Yes | Implemented in source; physical-device verification remains open. |
| GPS location enable/latitude/longitude | Engine BLocationManager and BLocationManagerService accept both userId and package name; VeyraVault calls setLocation/setPattern and reads back pattern and coordinates. | Yes | Package/user-scoped path implemented. App readback verifies live Engine state, not independently durable storage after Engine process death. |
| Cell information | Engine stores BCell and cell lists in the same user/package BLocationConfig; getAllCellInfo reads the current virtual user/package entry. | Not yet in VeyraVault ProfileSettings | Partial Engine capability; telephony adapter behavior is incomplete (see below). |
| Build brand/model/device/product/fingerprint | No BuildProxy or BDeviceManager/BDeviceConfig profile setter was found in the pinned source. black.android.os.Build is only an empty BlackReflection class binding to android.os.Build; it is not a profile API. | No | Not supported by the current VeyraVault profile/Engine integration. Do not represent saved metadata as applied Build values. |
| IMEI/MEID/device ID/subscriber ID | Registered ITelephonyManagerProxy hooks return MD5(BlackBoxCore.getHostPkg()) for device ID, IMEI, MEID and subscriber ID methods. The hook does not read the virtual user ID or package profile. | No | A host-package-derived fallback, not a per-Clone identity profile. |
| Device serial | On Android versions where the hook is installed, IDeviceIdentifiersPolicyProxy.getSerialForPackage also returns MD5(BlackBoxCore.getHostPkg()). | No | Host-package-derived value, not a per-Clone setting. |
| Android ID | AndroidIdProxy returns the underlying result when it is non-empty and non-zero. It generates a random mock only for an invalid result or an exception; that fallback is not persisted as a stable per-Clone value. | No | Not a deterministic or configurable per-Clone profile. |
| Wi-Fi SSID/BSSID/MAC | Registered IWifiManagerProxy.getConnectionInfo overwrites the returned object with fixed BSSID/MAC ac:62:5a:82:65:c4 and SSID BlackBox_Wifi. No virtual user/package setting is read. | No | Fixed Engine hook output, not a per-Clone profile. |
| Mobile network operator/type | getNetworkOperator delegates to the underlying service; getNetworkTypeForSubscriber also delegates and only returns 0 on failure. | No | Host/service-derived behavior, not a VeyraVault profile override. |
| Generic system properties | SystemPropertiesCompat is a reflection-based getter for Android system properties; no per-Clone property store or setter is wired into VeyraVault profiles. | No | Host/system values, not a per-Clone profile. |

### Cell adapter defects that prevent a broad “cell profile supported” claim

The Engine's per-user/package storage exists, and getAllCellInfo returns the matching BCell list when fake location is enabled. However:

- getCellLocation returns null when a configured BCell is present.
- getNeighboringCellInfo obtains the configured list but returns null.

Therefore these methods must not be described as a complete working cell identity override. They require a separately scoped Engine integration fix and target-app verification before use.

Source references:
- HookManager.java — active proxy registration: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/fake/hook/HookManager.java#L110-L205
- ITelephonyManagerProxy.java — device IDs and cell information: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/fake/service/ITelephonyManagerProxy.java#L47-L151
- IDeviceIdentifiersPolicyProxy.java — serial result: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/fake/service/IDeviceIdentifiersPolicyProxy.java#L36-L44
- IWifiManagerProxy.java — fixed Wi-Fi values: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/fake/service/IWifiManagerProxy.java#L40-L49
- AndroidIdProxy.java — Android ID and random fallback: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/fake/service/AndroidIdProxy.java#L32-L168
- BLocationManager.java — user/package-scoped location and cell API: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/fake/frameworks/BLocationManager.java#L40-L151
- BLocationManagerService.java — per-user/per-package config map and persistence calls: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/top/niunaijun/blackbox/core/system/location/BLocationManagerService.java#L38-L180
- Build reflection binding: https://github.com/ALEX5402/NewBlackbox/blob/89b59836c66f173756a4ae258cf379a957649820/Bcore/src/main/java/black/android/os/Build.java#L1-L8

## Current VeyraVault profile boundary

At the current feature-branch implementation, two profile layers coexist intentionally:

- Legacy ProfileSettings/ProfileStore remain the compatibility source for five runtime fields: localeTag, timeZoneId, locationEnabled, latitude and longitude.
- The additive ProfileDocumentStore uses a typed 97-field ProfileFieldRegistry. It preserves independent Global and per-Clone documents and does not replace or destructively migrate the legacy store.
- The non-exported ProfileRuntimeProvider checks same-UID callers and returns an immutable per-field snapshot containing effective value, source, capability, editability, adapter mapping, API-support note, privacy class, readback method and unsupported reason.
- ProfileRuntimeClient validates the complete registry-sized snapshot and its metadata before exposing it to the lifecycle callback.
- CloneProfileLifecycleCallback resolves the full snapshot before target Application creation. The existing process-scoped Locale/Time Zone adapters remain the only fields promoted to APPLIED by this lifecycle readback. Package/user-scoped location continues through VirtualHookManager and its separate Engine API/readback path.
- Other fields remain STORED_ONLY, UNSUPPORTED, NOT_TESTED or NOT_APPLICABLE according to their capability. A full IPC snapshot is not proof that all fields have runtime adapters.

Brand, manufacturer, model, country/SIM and similar values elsewhere in legacy/global environment data remain metadata unless a separately verified scoped API applies them. The presence of a value in a form, registry or storage is not proof that a target app observes it.

### Dated update — 2026-11-27

The feature branch now contains the 97-field inventory and complete typed IPC snapshot described above. This update does not change the pinned Engine revision or claim new device/network identity capabilities. The original Engine findings and restrictions in the matrix above remain in force.

VeyraVault source references:
- ProfileSettings.java: https://github.com/vaultveyra/VeyraVault-Project/blob/bbef9fd41f98ee52959bac7915ec0b79c292415f/app/src/main/java/com/veyravault/space/core/ProfileSettings.java#L10-L40
- ProfileRuntimeProvider.java: https://github.com/vaultveyra/VeyraVault-Project/blob/bbef9fd41f98ee52959bac7915ec0b79c292415f/app/src/main/java/com/veyravault/space/core/ProfileRuntimeProvider.java#L35-L63
- CloneProfileLifecycleCallback.java: https://github.com/vaultveyra/VeyraVault-Project/blob/bbef9fd41f98ee52959bac7915ec0b79c292415f/app/src/main/java/com/veyravault/space/core/CloneProfileLifecycleCallback.java#L22-L45
- VirtualHookManager.java — location resolution and readback: https://github.com/vaultveyra/VeyraVault-Project/blob/bbef9fd41f98ee52959bac7915ec0b79c292415f/app/src/main/java/com/veyravault/space/core/VirtualHookManager.java#L99-L143

## Engineering decision

1. Keep the proven Locale, Time Zone and GPS-location flows unchanged.
2. Keep unsupported Build/SIM/device metadata explicitly identified as metadata; do not add a UI success state without a real target-process readback test.
3. Do not reintroduce host-process android.os.Build mutation. It is not a per-Clone API and can leak values across virtual apps sharing a host process.
4. Do not add IMEI, MEID, IMSI, serial, Android ID, Wi-Fi MAC or similar persistent identifiers as a way to impersonate a device or bypass third-party integrity/anti-fraud controls.
5. Any future non-sensitive compatibility property must use virtual package/user identity, be applied inside the isolated target process before the target reads it, have deterministic storage and reset semantics, and be tested with two concurrent Clones whose readbacks prove there is no cross-Clone leakage.
6. Physical-device checks remain required. Emulator source hooks and readbacks do not prove OEM behavior or what every third-party application observes.

## Change and data boundary

- Audit and contract test only; no production Engine or Android runtime hook changed.
- No CloneStore records, Clone package data, account/session data or app-private target data were read for mutation or modified.
- SharedPreferences remains the active profile source. Room remains inactive; no import, dual-write or persistence cutover.
- PR #4 remains open and Draft; main is not modified.
