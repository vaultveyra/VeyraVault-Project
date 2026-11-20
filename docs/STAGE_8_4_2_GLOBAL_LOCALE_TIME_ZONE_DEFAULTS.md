# Stage 8.4.2 — Global Locale and Time Zone defaults

## Scope
- Add Global BCP-47 Locale and IANA Time Zone defaults to the existing Global Environment screen.
- Show the effective Locale and Time Zone after resolving Global values against safe System fallbacks.
- Save Locale and Time Zone independently through the asynchronous `AsyncCloneRepository.saveGlobalProfile` API.
- Reset one selected Global field through `clearGlobalProfileField`; do not clear sibling fields.
- Validate values before dispatching writes.
- Provide common Locale and Time Zone presets.
- Explain that Global defaults apply only when a Clone has no per-field override and take effect on the Clone's next launch.

## Data and precedence guarantees
- Per-field precedence remains Clone > Global > System.
- Global partial writes set only the supplied field. Existing `ProfileStore.toJson` semantics preserve unspecified siblings.
- Reset removes only `localeTag` or `timeZoneId` from the Global profile.
- Clone override storage is not called by this screen. Existing per-Clone values remain untouched.
- The Locale/Time Zone actions do not call location-hook synchronization or modify Master Mock GPS.
- Existing device metadata, Global location defaults, and Master Mock GPS workflows remain separate and unchanged.
- Room remains inactive. No migration, cutover, or schema change is introduced.

## Verification
- Source-contract checks are added to `scripts/test_global_environment_persistence_ui_contract.py`, which is already wired into CI.
- `AsyncCloneRepositoryInstrumentationTest.globalLocaleAndTimeZoneDefaultsAreFieldScopedAndPreserveCloneOverrides` verifies asynchronous persistence, per-field reset, Clone override preservation, and resolver source selection.
- CI's Android Instrumentation run exercises the added test.
- Physical-device testing with two disposable test Clones remains necessary to confirm third-party app Locale/Time Zone observations; CI emulator success is not a substitute for that test.
