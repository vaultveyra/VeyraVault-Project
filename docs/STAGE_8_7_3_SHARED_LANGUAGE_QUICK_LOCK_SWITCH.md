# Stage 8.7.3 — Shared language and immediate-lock header switch

## User-facing behavior
- The language control and immediate-lock switch are placed together in the top header on Spaces, Dashboard, Settings, Launcher Icon & Label, and About.
- Settings no longer places language selection at the bottom of the page.
- The switch has explicit localized states: Persian «باز / قفل» and English «Open / Locked».
- The switch reflects the effective app-session lock state when the screen resumes.

## Security contract
- Turning the switch ON requires an already configured PIN or Pattern, calls the existing SecurityManager.lockSession(), and opens the existing SecurityLockActivity.
- If no PIN or Pattern exists, the switch returns to OFF and directs the user to Security Settings.
- Turning the switch OFF never unlocks the app and never changes credentials; the existing PIN/Pattern verification flow remains the only unlock path.
- The switch state is refreshed after the lock screen returns, so a successful credential verification updates it to OFF.
- The dedicated security lock screen remains independent of the header controls.

## Data and project boundaries
- No CloneStore, clone package/user identity, clone data, account/session contents, Engine, Room migration, VPN, GPS, or Device Admin state is modified.
- No new credential store, exported component, or authentication bypass is introduced.
- The existing PR remains open and Draft; main is not changed.

## Verification
- Extended scripts/test_appearance_preferences_quick_lock_contract.py to require the shared header controls, localized switch states, existing credential verification, lock-state refresh, and the absence of a language section at the bottom of Settings.
- The original CI attempt exposed stale quick-lock method calls in Launcher Icon & Label and About. Both screens are now migrated to the shared header controls, and the static contract includes all five headers. Android instrumentation, source audit, unsigned release compilation, APK audit, and artifact upload remain required.
- Physical-device layout and touch-flow validation in Persian RTL and English LTR remain outstanding.
