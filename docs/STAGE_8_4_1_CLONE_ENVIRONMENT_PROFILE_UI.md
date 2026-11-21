# Stage 8.4.1 — Per-clone Locale and Time Zone editor

## Scope
- Add a dedicated Clone Environment Profile screen reachable from each clone's configuration sheet.
- Edit Locale (BCP-47 tag) and Time Zone (IANA ID) independently.
- Show each effective value and its source (CLONE, GLOBAL, SYSTEM, or UNSET).
- Reset one field by clearing only that clone override, revealing the Global/System fallback.
- Validate the clone identity against a strict asynchronous registry snapshot before enabling edits.
- Use AsyncCloneRepository for all profile reads and writes; no disk I/O on the UI thread.
- Settings apply on the next virtual process launch. The screen does not stop running apps.

## Safety boundaries
- No CloneStore registry mutation, virtual package data mutation, account/session mutation, uninstall, or process stop.
- Existing ProfileStore schema and SharedPreferences namespace remain unchanged.
- Global profile and system fallback are read-only in this screen.
- Location and Master Mock GPS controls are not modified.
- Room remains inactive; no migration or cutover.

## Validation
- Source-contract test: `scripts/test_clone_environment_profile_ui_contract.py`.
- Android instrumentation: existing ProfileStore/ProfileResolver/runtime tests remain in place; physical-device confirmation of third-party app Locale/Time Zone observations remains required.
- A source-contract pass is not runtime proof. Confirm behavior on a physical device with two disposable test clones and distinct time zones before release.
