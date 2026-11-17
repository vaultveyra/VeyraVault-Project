# Stage 1 — Profile Persistence Foundation

## Scope

This stage adds a separate, versioned persistence namespace for user-configurable profile overrides. It does not replace CloneStore, change the clone identity model, or modify the Engine/session lifecycle.

## Resolution contract

Each field resolves independently in this order:

1. Clone override
2. Global default
3. Supplied system fallback
4. Unset

A nullable value means that the field is not overridden. An explicit Boolean false is a value and must not be confused with an absent override.

The current model covers locale tag, time-zone ID, location-enabled state, latitude, and longitude. This is a foundation; it is not yet a complete device-profile schema.

## Persistence behavior

- New preference namespace: veyravault_profiles_v1.
- JSON schema version: 1.
- Legacy clone preferences remain read-only migration input.
- Saving non-null fields is additive: omitted/null fields do not erase sibling values.
- clearCloneOverrideField and clearGlobalField remove exactly one named, allow-listed field.
- Unknown schema versions and malformed root/nested structures are not overwritten.
- Clone profiles are keyed by package name and virtual user ID.

## Legacy import

At application startup, the importer validates the legacy clones_json array before asking CloneStore to read it. It imports only entries with a non-empty package name, non-negative user ID, and GPS enabled.

The legacy model stores GPS enabled as a primitive boolean, so a legacy false value cannot reliably distinguish explicitly disabled from never configured. For that reason false is not imported as an explicit override.

The importer only fills fields that are absent in the new profile. It can safely run again, including after additional clones have been added. Original legacy preferences are not deleted or rewritten.

## Validation performed

The standalone Java contract test covers:

- Clone → global → system priority, independently per field.
- Explicit false as an override.
- Unset values remaining unset.
- Clone profile independence.
- Clearing an override revealing the next fallback.
- Copy isolation.
- Out-of-range, NaN, and infinite coordinate rejection.

The Android CI build additionally compiles the new persistence classes, runs source audit, assembles the release APK, and audits/packages the APK.

## Deliberate non-goals in this stage

- No new settings UI.
- No application of profile values to runtime hooks.
- No Engine, VirtualHookManager, launch, or session-lifecycle changes.
- No Room migration yet; the current persistence layer remains additive SharedPreferences JSON until a separately tested database migration is justified.
- No synthetic hardware identifiers or bypass behavior.

## Remaining verification

A device-level test is still required to validate actual SharedPreferences migration and profile read/write behavior against an installed app with pre-existing clone data. The current CI contract tests do not substitute for that on-device migration test.
