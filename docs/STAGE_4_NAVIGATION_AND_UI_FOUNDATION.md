# Stage 4 — Navigation and UI Foundation

## Scope

This stage adds an incremental navigation foundation without replacing the existing clone-management screen or changing clone storage, identifiers, lifecycle, or engine behavior.

### Added screens

- `DashboardActivity`: a lightweight overview showing counts derived from the existing `CloneStore.getAll()` data, shortcuts to Spaces/Add App/VPN/Settings, and the device time-zone ID from Android's `TimeZone` API.
- `VpnStatusActivity`: read-only detection of Android's system VPN transport (API 23+). It explicitly states that this app version does not yet implement its own `VpnService`, server selection, or tunnel connection.
- `SettingsHubActivity`: a single entry point to the existing Global Environment, Security, Permissions, and About/Compatibility activities, plus the existing Persian/English language toggle.

### Navigation

The existing `MainActivity` remains the Spaces/clone-management screen and remains the target of the current launcher aliases and shortcut intents. Its bottom navigation is updated to:

1. Dashboard
2. Spaces
3. Add (+)
4. VPN
5. Settings

The Spaces list, clone cards, clone launch flow, per-clone configuration, collapse state, and existing data access remain in `MainActivity`. No data migration or destructive operation is part of this stage.

## Compatibility and honesty constraints

- Dashboard counts are read from the existing local clone registry; they do not claim to validate the underlying virtual engine or each clone's runtime health.
- The displayed time zone is the Android host device's configured time zone. It is not a GPS location or IP-geolocation result.
- VPN status is only a system-level transport observation. It does not prove that traffic is routed through a particular provider or server.
- No VPN connection, permission grant, system setting, or network route is changed by the VPN screen.
- Existing launcher aliases are intentionally unchanged in this incremental stage. A future launcher/dashboard transition should follow device-level smoke testing.

## Validation

The GitHub Actions release build and source/APK audit are triggered by the code changes in this stage. The build artifact is unsigned and is for CI validation only; it must not be installed as a production release.

## Deferred work

- A real VeyraVault VPN requires a separately designed Android `VpnService`, consent flow, tunnel protocol, server configuration, lifecycle handling, and security review.
- The dashboard remains a foundation, not a full telemetry or engine-health console.
- UI instrumentation/device smoke tests are still required for Persian RTL, English LTR, launcher aliases, shortcut launches, and back-stack behavior.
