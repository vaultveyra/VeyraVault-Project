# Stage 8.8.1 — Dashboard five-destination navigation parity

## Scope
- Add a persistent bottom navigation bar to DashboardActivity, matching the five product destinations: Dashboard, Spaces, Add, VPN and Settings.
- Keep Dashboard selected while its screen is active.
- Route Spaces, Add, VPN and Settings to their existing Activities; do not create parallel destinations or new navigation state.
- Keep the center Add action compact (48dp), accessible, and connected to AddAppActivity.
- Keep the Dashboard content in a weighted ScrollView above the fixed navigation bar so long summaries remain scrollable.
- Reuse the current UiPalette and card drawable so the bar follows the saved System/Light/Dark appearance mode.
- Preserve the existing top-bar language and authenticated immediate-lock controls.

## Safety and compatibility
- This is a navigation/UI-only change. It does not call CloneStore writes, Engine operations, profile mutation, VPN configuration, or Device Admin APIs.
- Existing asynchronous Clone/Space counts, environment summaries, and truthful host-network labels remain unchanged.
- No clone records, package/user identities, app-private data, accounts, sessions, preferences, manifest entries, permissions, Room schema, or migration state are modified.

## Regression coverage
- Add `scripts/test_dashboard_bottom_navigation_contract.py` and run it in the GitHub Actions build workflow.
- The contract checks all five destinations, center Add click/accessibility wiring, and preservation of language/lock controls and asynchronous Dashboard registry reads.

## Verification boundary
- Implementation and source-contract changes are committed on `feat/veyra-vault-product-foundation`.
- GitHub Actions Android Instrumentation, source audit, Release APK build and APK audit must pass on this exact commit before CI validation is claimed.
- Physical-device visual/touch validation in Persian RTL and English LTR, including small screens and large font scaling, remains outstanding.
