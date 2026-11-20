# Stage 8.7.1 — Appearance preferences and authenticated quick lock

## Scope implemented
- Add a separately persisted AppearanceManager preference with exactly three accepted modes: System, Light, and Dark.
- Apply the saved AppCompat DayNight mode before BaseActivity creation and during Application startup.
- Add light/night color resources and a semantic UiPalette for programmatic screens.
- Update primary screens and card/pill drawables to resolve colors from current day/night resources.
- Add System/Light/Dark selection to Settings while preserving language, About/Compatibility, Security, Permissions, Global Environment, and Pending Reservations entries.
- Add a quick-lock action to Dashboard, Spaces, and Settings headers.

## Security contract
- Quick Lock uses the existing SecurityManager lock state and existing SecurityLockActivity PIN/Pattern verification flow.
- The action first verifies that a PIN or Pattern is configured. If none exists, it directs the user to Security Settings instead of pretending to lock.
- For a configured lock, the action calls SecurityManager.lockSession() synchronously and opens the existing authenticated lock screen.
- No second credential store, bypass path, fake lock indicator, Device Admin escalation, or new exported component is introduced.
- The dedicated lock screen intentionally retains its existing dark high-contrast surface.

## Data and runtime boundaries
- Appearance is stored in a new preference namespace `veyra_appearance_prefs` under `theme_mode`.
- No CloneStore keys, clone package/user identities, clone data, account/session contents, Engine operations, GPS settings, or VPN state are changed.
- No Room migration or persistence cutover is introduced.
- Unsupported/unknown theme values are rejected and fall back to System when read.
- Theme preference commits are checked before AppCompat night mode is changed.

## Automated verification
- `scripts/test_appearance_preferences_quick_lock_contract.py` checks accepted modes, persistence wiring, DayNight palette resources, and that quick lock reuses the existing credential mechanism without touching CloneStore or Engine.
- `AppearanceManagerInstrumentationTest` tests default System behavior, Light/Dark persistence and AppCompat mode application, System reset, invalid-value rejection, and restores the original preference after each test.
- Both checks are part of the feature branch CI; Android Instrumentation and Release/Audit must pass before this stage is CI-verified.

## Not yet verified
- Physical-device rendering in Light/Dark/System, including Persian RTL and English LTR, has not been reviewed.
- Quick-lock user-flow validation on a physical device has not yet been performed.
- This is a functional foundation, not a complete visual redesign of every widget or third-party app screen.