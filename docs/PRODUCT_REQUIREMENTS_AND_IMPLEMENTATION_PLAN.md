# VeyraVault Product Requirements and Safe Implementation Plan

## 1. Purpose

Evolve the existing VeyraVault Android application into a polished multi-space app manager with per-app environment profiles, a real VPN management experience, a security center, and a professional dashboard. Preserve the existing application source, package identity, stored clone data, and working session behavior.

This document is the implementation contract for the feature work. It does not claim that features listed as planned are already implemented.

## 2. Non-negotiable engineering constraints

1. Do not modify `main` directly. All work is performed on a feature branch and proposed through a pull request.
2. Do not delete, replace, or regenerate the existing `com.veyravault.space` application source as part of UI work.
3. Do not change clone/session creation, persistence, launch, or virtualization behavior during a visual redesign.
4. Before any change touching `CloneStore`, `Engine`, `VirtualHookManager`, package identity, Android manifest permissions, or virtual-user initialization, add targeted regression checks and review the impact.
5. Keep existing user data and preference keys compatible. Any migration must be additive, versioned, and backward-compatible.
6. No fake VPN state, fake IP display, or UI-only toggles presented as working system features.
7. Device, locale, carrier, GPS, and network properties must be represented honestly: Android APIs, VPN providers, carriers, and remote services may expose different values. Do not promise that an app server will observe a chosen device or location exactly.
8. Device Admin is a user-revocable Android administrator capability, not an uninstall-proof mechanism. UI copy must explain the actual system flow.
9. Keep signing keys and credentials out of source, logs, and artifacts.

## 3. Environment profile precedence

Each clone needs an independently stored profile. The effective configuration resolver must use this order **per setting**, not merely choose one entire profile:

- Explicit clone/app override, when configured and supported.
- Global VeyraVault default, when configured and supported.
- Android/device default.

An unset per-app field must inherit the corresponding global field. A set per-app field must not be overwritten by a global update. Users must be able to see whether a value is inherited or overridden and reset individual fields to inherit.

Profile domains:
- Device descriptor: manufacturer, brand, model and supported device properties.
- Region: country/region and locale.
- Time: timezone and display preferences where supported by the app/runtime.
- Location: optional per-clone location profile, clearly distinguished from IP geolocation.
- SIM/carrier: only values that the virtualization layer and Android version can safely and consistently support.
- Network: VPN connection/profile status and routing scope; IP is read from an actual network check or provider, never inferred from selected country.

Do not add unsupported spoofing claims. Where an Android or third-party API cannot be virtualized reliably, show the limitation.

## 4. Session and clone regression contract

The currently working session behavior observed by the user is a protected baseline. Before and after relevant changes, validate:
- Existing clone records remain present.
- Existing package/userId pairs remain stable.
- Existing app data is not cleared or re-created.
- Launching a clone continues to use its own persisted configuration.
- A clone's explicit profile takes precedence over global defaults.
- A clone without an explicit profile inherits global defaults.
- Switching between clones does not leak one clone's settings into another.
- Session display and server-reported session details are treated as external app behavior, not guaranteed by VeyraVault.

Do not make a claim of session equivalence based solely on local UI state.

## 5. Navigation and visual design

Bottom navigation has five destinations:
1. Dashboard
2. Spaces
3. Center add action (+), visually emphasized but compact
4. VPN
5. Settings

Top bar:
- VeyraVault identity.
- English/Persian language switch.
- Immediate lock action.

Dashboard:
- Tehran clock in 12-hour format with Jalali date.
- New York clock in 12-hour format with Gregorian date.
- Global device and region summary.
- Actual VPN connection status and actual IP information only when verified.
- Clone/space counts and engine/security status.
- Clear distinction between global defaults and active clone overrides.

Spaces:
- Preserve current clone cards and all existing actions.
- Use real installed application icons and names from PackageManager.
- Keep per-clone configuration accessible.
- Support grouping and space management without changing clone identity or storage.

VPN:
- Dedicated VPN experience with connection/disconnection, provider/profile selection, searchable country/city list, favorites, recent endpoints, connection status, elapsed time, and actual endpoint/IP details.
- The screen must not imply a connection until Android VPN service/provider confirms it.
- Provider/server inventory must come from a configured provider or user-imported profile. Never invent a server list.
- VPN implementation requires a real provider or valid VPN configuration and Android VpnService integration; until then, present a clearly marked setup/unconfigured state.

Settings sections:
1. Device & Region: global defaults, per-app profiles, inheritance indicators, device/region/time/locale/location/network settings and capability explanations.
2. Security & Lock: PIN/pattern security, immediate lock, timeout, administrator enrollment and status.
3. App Icon & Name: launcher aliases supported by the manifest, actual available icon choices, searchable list, custom display name only where Android launcher alias support permits it. Do not promise arbitrary icon search unless assets are bundled or installed icons are selectable.
4. Appearance: light, dark, and system theme.
5. About & Requirements: app version, build, Android compatibility, permissions, and honest feature status.

## 6. Security behavior

- Immediate lock must synchronously mark the app as locked and route to the lock screen when the user taps the top-bar action.
- Lock state must survive activity recreation and background/foreground transitions according to configured policy.
- Password/PIN storage must use a modern password-based KDF with per-install random salt and Android Keystore-backed protection where appropriate. Do not silently reinterpret existing hashes; plan a backward-compatible re-enrollment/migration.
- Device Admin activation must use the Android system confirmation UI.
- When enabled, explain that the user can revoke administrator status in Android Settings before uninstalling. Never display a false “uninstall impossible” guarantee.

## 7. Localization, time, and accessibility

- Persian RTL and English LTR layouts must both be supported.
- Tehran and New York clocks must use their named IANA time zones and update from the system clock.
- Jalali conversion must be tested around month/year boundaries and leap years.
- Use accessible labels, touch targets, contrast, and scalable text.
- Theme and navigation state must persist without affecting clone data.

## 8. VPN requirements and dependencies

A real VPN requires:
- A provider integration or user-supplied valid VPN configuration.
- Android VpnService permission/consent flow.
- A foreground service and persistent notification as required by Android.
- DNS, IPv4/IPv6, routing, reconnect, and failure handling.
- Clear privacy and traffic-routing disclosures.
- Tests that confirm traffic actually traverses the configured tunnel.

A country selector by itself is not a VPN. Do not show selected country as connected IP.

## 9. Delivery phases and acceptance gates

### Phase 0 — Baseline and source audit
- Inventory source, manifest, resources, Gradle dependencies, current preferences, clone persistence and CI.
- Document the current session/clone code paths.
- Record existing behavior and identify migration hazards.
- No runtime behavior changes.

### Phase 1 — Design system and navigation shell
- Introduce reusable colors, typography, spacing, cards, icons, and responsive components.
- Add the five-destination navigation shell and top-bar lock affordance.
- Preserve existing Spaces screen and actions.
- Add placeholder VPN setup state only; no false connected state.
- Build and test English/Persian layouts.

### Phase 2 — Dashboard and settings structure
- Implement dual clocks and date formats.
- Implement real system/global summary fields with unknown/unavailable states.
- Build Settings sections and theme persistence.
- Add actual installed-app icon selection where supported.

### Phase 3 — Per-clone profile model
- Add versioned, backward-compatible per-field overrides.
- Implement precedence resolver and inheritance/reset UI.
- Add unit tests for precedence, migration, isolation and clone switching.
- Do not change session lifecycle code except where strictly required and separately reviewed.

### Phase 4 — Security improvements
- Immediate lock and lifecycle handling.
- Password KDF migration plan and implementation.
- Accurate Device Admin activation/deactivation UX.

### Phase 5 — VPN provider integration
- Select a provider or define supported import format.
- Implement VpnService and verified connection state.
- Populate server list from actual provider/config data.
- Verify tunnel routing and failure behavior.

### Phase 6 — Regression and release
- Run CI build, source audit, unit tests and APK audit.
- Compare clone/session regression results to baseline.
- Produce a test APK on the feature branch.
- Open a PR for review. Do not merge without explicit user approval.

## 10. Definition of done

A feature is complete only when its implementation, persistence, localization, accessibility, error states, and tests are present. A successful APK compilation alone does not satisfy product acceptance. All changes remain on the feature branch until reviewed and explicitly approved for merge.
