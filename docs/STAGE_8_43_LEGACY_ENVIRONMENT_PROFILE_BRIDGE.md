# Stage 8.43 — Read-only legacy environment metadata bridge

Status: implementation added on the feature branch; CI and Android instrumentation validation pending.

## Problem found in the current profile flow

The app had two legacy metadata sources in CloneStore:

- Global `GlobalEnvConfig`: brand/manufacturer, model, country ISO and SIM/operator metadata.
- Per-Clone `CloneEntry`: `customDeviceEnabled`, `deviceBrand` and `deviceModel`.

The 104-field typed profile resolver already read the typed `ProfileDocumentStore` and the five-field `ProfileStore`, but it did not include these older CloneStore metadata values. Consequently, an older per-Clone or Global metadata value could be visible in its legacy screen while absent from the full profile editor's effective-value resolution.

## Additive implementation

- Add `CloneStore.readGlobalEnvironmentMetadataProfileStrict`, a read-only adapter that imports only explicitly persisted values. It does not import constructor defaults when the legacy key is absent and ignores the legacy profile when its `enabled` flag is false.
- Add `ProfileLegacyEnvironmentBridge` to overlay legacy metadata only when the typed field is absent, valid, and has no explicit state.
- Resolve legacy Clone metadata by the exact composite identity `packageName#userId`. Two packages may share the same numeric Space/user ID without sharing metadata.
- Precedence is preserved per field: typed Clone value/state → legacy Clone metadata → typed Global value/state → legacy Global metadata → registry safe default.
- A typed `INHERIT_GLOBAL`, `SAFE_DEFAULT`, or invalid-field marker blocks the same-level legacy value. Resetting a field therefore cannot resurrect an older CloneStore override.
- The same bridge is used by the runtime Provider and the asynchronous profile-editor repository, so displayed effective values and the runtime snapshot share the same source precedence.
- Unknown/unregistered Clone identities receive no legacy Clone fallback. Strict CloneStore corruption remains an error.

## Strict capability boundaries

The bridge maps only:
- Clone `deviceBrand` → typed `manufacturer`
- Clone `deviceModel` → typed `deviceModel`
- Global `brand/manufacturer` → typed `manufacturer`
- Global `model` → typed `deviceModel`
- Global `countryIso` → typed `countryCode`

These remain `NOT_IMPLEMENTED` or `LOCAL_PREFERENCE_ONLY` metadata and are reported as `STORED_ONLY`, never `APPLIED`. The bridge does not map SIM/operator identity, IMEI/MEID/IMSI, serial, Android ID, IP address, or service-owned identity. It does not change Build properties, SIM state, network routing, GPS, accounts, cookies, sessions, or third-party service identity.

## Preservation guarantees

- Read-only bridge: no CloneStore, ProfileStore, ProfileDocumentStore, Room, session, account, cookie or app-data writes.
- No migration, destructive rewrite, cleanup, key retirement, ID remapping, or automatic data deletion.
- Existing legacy values remain in their original CloneStore records.
- Typed values and explicit reset/inherit states remain authoritative.
- Room remains inactive and SharedPreferences remains the active persistence path.

## Validation added

- Synthetic Android instrumentation uses two package names with the same numeric user ID to verify per-package isolation.
- Tests verify Clone metadata overrides Global metadata, a Clone without an override inherits Global, typed values win, reset states suppress legacy resurrection, disabled/absent Global metadata does not import constructor defaults, and SIM/operator identity is excluded.
- Provider integration is exercised through the complete typed runtime snapshot.
- A CI source-contract test guards Provider/repository wiring and the read-only boundary.

A green CI run is required before calling this stage validated. Physical-device testing is still required to determine what third-party apps actually observe. This stage does not claim that manufacturer/model/country metadata changes the Android Build API, SIM/carrier, network IP, or service behavior.
