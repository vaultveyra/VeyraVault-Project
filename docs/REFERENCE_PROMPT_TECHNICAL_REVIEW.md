# VeyraVault Reference Prompt Review and Implementation Baseline

Date: 2026-11-17
Branch: feat/veyra-vault-product-foundation
Base product namespace: com.veyravault.space

## 1. Purpose

This document reviews the user's 143-line reference prompt and converts it into an implementable, testable engineering baseline for VeyraVault. It is a review and planning artifact, not a claim that the features below are already implemented.

The checked-in application source remains authoritative. Existing clone records, package/user identifiers, application identity, persisted preferences, and working session behavior are protected.

## 2. Repository inventory inspected

### Android application source

- app/src/main/AndroidManifest.xml
- app/build.gradle
- app/src/main/java/com/veyravault/space/VaultApp.java
- app/src/main/java/com/veyravault/space/core/CloneStore.java
- app/src/main/java/com/veyravault/space/core/Engine.java
- app/src/main/java/com/veyravault/space/core/GmsSupportManager.java
- app/src/main/java/com/veyravault/space/core/LocaleHelper.java
- app/src/main/java/com/veyravault/space/core/ShortcutHelper.java
- app/src/main/java/com/veyravault/space/core/VirtualHookManager.java
- app/src/main/java/com/veyravault/space/security/SecurityManager.java
- app/src/main/java/com/veyravault/space/security/AppDisguiseManager.java
- app/src/main/java/com/veyravault/space/security/VaultDeviceAdminReceiver.java
- app/src/main/java/com/veyravault/space/ui/MainActivity.java
- app/src/main/java/com/veyravault/space/ui/AddAppActivity.java
- app/src/main/java/com/veyravault/space/ui/GlobalEnvironmentActivity.java
- app/src/main/java/com/veyravault/space/ui/SetLocationActivity.java
- app/src/main/java/com/veyravault/space/ui/SecurityLockActivity.java
- app/src/main/java/com/veyravault/space/ui/SecuritySettingsActivity.java
- app/src/main/java/com/veyravault/space/ui/PermissionsActivity.java
- app/src/main/java/com/veyravault/space/ui/AboutActivity.java
- app/src/main/java/com/veyravault/space/ui/BaseActivity.java
- app/src/main/java/com/veyravault/space/ui/PatternLockView.java
- Existing drawable, values, values-fa, values-en, and device-admin XML resources.

### Build, automation, and staged migration

- app/build.gradle currently uses Java 8, minSdk 21, AppCompat, Material Components, RecyclerView, CardView, osmdroid, and the Bcore project dependency.
- .github/workflows/build-and-audit.yml
- scripts/prepare_workspace.py
- scripts/audit_source.py
- scripts/audit_apk.py
- scripts/apply_all_fixes.py
- scripts/upgrade_v3_part1.py
- scripts/upgrade_v3_part2.py
- docs/IMPLEMENTATION_AUDIT.md
- docs/PRODUCT_REQUIREMENTS_AND_IMPLEMENTATION_PLAN.md

The V3 scripts are staged migration material. They are not the currently compiled application source. Do not execute their generated source overlay as part of normal builds until the package namespace, references, manifest, dependencies, and tests are reconciled.

## 3. Findings from inspected source

### 3.1 Persistence and clone model

CloneStore currently stores clone records and global environment settings in SharedPreferences as JSON. Existing clone identity is the package name plus virtual userId. CloneEntry contains display name, GPS fields, selected device fields, and denied-permission flags. GlobalEnvConfig contains a small set of device/region/operator fields.

There is no Room database in the current app source. A Room migration may be appropriate, but it must be additive and must first import and verify existing JSON records. Never replace the current preference store before a tested migration and rollback strategy exist.

### 3.2 Profile precedence

The current model does not implement a complete per-field profile resolver. Global and per-clone settings are applied through separate paths. CloneStore.syncAllHooks applies global device properties and then iterates clones; VirtualHookManager.syncCloneHooks chooses either the clone's limited custom device values or the global values. This is not a general inheritance system and does not cover all requested domains.

Required future resolver, independently for each supported setting:
1. Explicit per-clone override.
2. Global VeyraVault default.
3. Native Android/device value only where the feature is explicitly designed to use the real system value and disclosure permits it.
4. If a security-critical policy cannot be satisfied, block or disable the affected feature with a clear reason rather than silently falling back.

Do not silently replace a clone override when global defaults change. Show inherited versus overridden state and allow reset-to-inherit.

### 3.3 Runtime and session lifecycle

Engine delegates installation, launch, stop, clear, and uninstall operations to the BlackBox engine through reflection. Several reflection failures are swallowed. installPackageAsUser currently returns true when reflection throws, which can falsely report installation success. This is a reliability defect to address with explicit result/error reporting and regression tests, without changing the clone lifecycle in the same patch as UI work.

VirtualHookManager applies process-wide Build field reflection and a LocationManager proxy, as well as per-user BlackBox device/location configuration. It catches broad Throwable exceptions silently. These mechanisms do not prove comprehensive isolation and may have cross-clone/process side effects. They require a dedicated audit and scoped diagnostics before modification.

The user's currently working clone/session behavior is a protected regression baseline. Do not alter session creation, storage, launch, package/user mapping, or engine initialization during visual redesign.

### 3.4 Security

SecurityManager currently hashes PIN/pattern material using SHA-256 with a fixed prefix salt. This is not an adequate password-storage KDF. A migration should use a vetted KDF with a unique random salt, calibrated parameters, constant-time comparison, attempt throttling, and backward-compatible credential re-enrollment. Do not silently invalidate existing credentials.

Device Admin is a revocable Android administrator capability. It cannot make an app undeletable. The UI must explain the Android system deactivation flow accurately.

App disguise aliases exist in the manifest. Any icon/name selector must use declared launcher aliases or supported launcher APIs and explain platform limitations. It must not be represented as stealth or as concealment from Android, security tools, or users.

### 3.5 Permissions and host-data isolation

The manifest currently declares broad permissions including location, storage, camera, microphone, contacts, Bluetooth, package visibility, install packages, and network access. Each permission must be justified by an actual feature, requested only when needed, and tested at runtime.

PermissionsActivity stores denied-permission flags, but the inspected audit reports that the current virtualization hook does not enforce those flags. UI toggles must not claim to block access until the engine enforces and tests them.

A virtual app container is not equivalent to an Android OS user/profile boundary. Do not promise that no app can ever observe host properties. Define a threat model, minimize host permissions, isolate app data through the engine, enforce permission policy where supported, and document residual exposure. For stronger OS-level isolation, evaluate Android managed profiles or dedicated Android users where the device supports them.

### 3.6 Device and identity parameters

The reference prompt proposes synthetic IMEI/IMSI/serial/MAC/GAID/GSF identifiers and broad fingerprint substitution. This is not accepted as a blanket implementation requirement. Do not generate or inject fabricated hardware identifiers, impersonate carriers/devices, bypass app integrity or anti-fraud checks, or promise consistency to remote services.

Permitted engineering scope: data isolation, explicit per-clone locale/time-zone preferences where supported, user-controlled location permissions and app-scoped location profiles where supported by the engine, honest device capability reporting, and real network/VPN routing with verified status. Distinguish GPS location from IP geolocation and selected VPN endpoint from observed public IP.

### 3.7 GMS

GmsSupportManager uses reflection to request engine GMS install/uninstall. A successful reflective call is not sufficient proof of an isolated Google account or working Play Services. Treat GMS support as partial/unverified until engine results, package state, sign-in behavior, data boundaries, and compatibility are tested. Do not claim per-space GMS sandboxing without evidence.

### 3.8 UI and navigation

MainActivity currently builds a programmatic dashboard and space list. AddAppActivity selects installed launcher apps and supports batch selection. GlobalEnvironmentActivity contains a small global profile form. Existing Persian/English resources and locale helper exist, but complete RTL/LTR behavior and translation coverage need tests.

The user's current product direction is a five-destination bottom navigation:
1. Dashboard
2. Spaces
3. Centered compact Add action
4. VPN
5. Settings

The attached reference prompt also proposes three tabs with a FAB. This conflicts with the user's later explicit five-item navigation request. The later five-item direction is the controlling product requirement unless the user changes it.

Dashboard requirements: Tehran clock and Jalali date; New York clock and Gregorian date; 12-hour presentation; verified device/region/network summary; clone count; engine and security status; clear unknown/unavailable states. Never display fabricated IP, carrier, connection, or security status.

### 3.9 VPN

The checked-in app source has no complete VPN service or traffic tunnel. A country list or selected country is not a VPN. A real implementation requires a configured provider or valid user-imported profile, Android VpnService consent, foreground service/notification, DNS and route handling, IPv4/IPv6 behavior, reconnect/error handling, and end-to-end tunnel tests.

Per-clone/per-app split routing depends on engine architecture and Android routing constraints. Simultaneous different exits for separate virtual apps may not be achievable by the current single-host-process architecture without a deeper routing design. Do not add a server catalog of invented IPs or fake ping/availability values. Use provider-supplied server metadata only.

### 3.10 Compatibility work

Create a CompatibilityManager for supported diagnostics and compatibility workarounds, not for hiding virtualization or defeating app security. It may:
- Inspect installed app metadata and required ABI/native libraries.
- Validate WebView provider presence/version and report initialization errors.
- Collect redacted, app-scoped crash diagnostics.
- Check declared permissions and supported runtime capabilities.
- Apply documented compatibility settings that do not bypass integrity or anti-fraud controls.
- Produce actionable error messages and a reproducible compatibility report.

Do not implement package/process hiding, SafetyNet/Play Integrity bypass, root concealment, anti-cheat bypass, signature-check circumvention, or fake camera/microphone identity. For apps that intentionally reject virtualized environments, report incompatibility and suggest a supported installation/profile path.

## 4. Corrections to the reference prompt, section by section

- Steps 1 and 2: retain structured profiles and deterministic per-field precedence; remove synthetic sensitive hardware identifiers and blanket spoofing. Add explicit capability metadata and validation.
- Step 3: retain Material 3, accessible components, Persian RTL/English LTR, and the user's five-destination navigation. Add the top-bar immediate lock.
- Step 4: retain country/city/time-zone metadata only as configuration data. Do not seed fictitious IP pools, server inventories, or ping values. VPN endpoints must come from real provider data.
- Step 5: retain CompatibilityManager, diagnostics, and staged tests. Replace anti-detection/bypass instructions with supported compatibility diagnosis and safe fixes.
- Final execution instructions: inventory first; work on a feature branch; deliver one stage at a time; run tests/build; report evidence; wait for user approval before the next major stage and never merge without explicit permission.

## 5. Proposed implementation sequence

### Stage 0 — Baseline audit (this document)
- Inventory source and dependencies.
- Record current clone/session and data model.
- Identify migration hazards and unsupported claims.
- No runtime code changes.

### Stage 1 — Persistence and profile foundation
- Define versioned profile models and per-field override semantics.
- Add a migration adapter from existing CloneStore JSON/preferences.
- Add tests for import/export, clone identity stability, precedence, inheritance, reset-to-inherit, and global-update non-overwrite.
- Select Room only after verifying Gradle/plugin compatibility and migration design.
- Preserve old keys until migration verification and rollback are proven.
- Do not change Engine launch/session behavior in this stage.

### Stage 2 — Security and permission policy
- KDF migration with legacy credential transition.
- Attempt throttling and lock lifecycle tests.
- Correct Device Admin UX.
- Audit manifest permissions and implement truthful permission enforcement only where supported.

### Stage 3 — Compatibility diagnostics
- Add CompatibilityManager diagnostics and reports.
- Test WebView/native library/ABI/permission failures.
- No app-security bypasses.

### Stage 4 — UI design system and navigation
- Build five-destination navigation and top bar.
- Preserve current Spaces actions.
- Add responsive Material 3-style cards and tested RTL/LTR.
- Keep VPN in a truthful unconfigured/setup state until a real provider exists.

### Stage 5 — Dashboard and settings
- Live Tehran/New York clocks and correct calendars.
- Verified system/device summaries and unknown states.
- Settings sections, theme persistence, supported icon aliases, quick lock.

### Stage 6 — Real VPN architecture
- Select provider/config format.
- Implement VpnService and tunnel.
- Verify routing and failure behavior before exposing connected status.
- Evaluate feasibility of per-clone split routing before promising simultaneous independent exits.

### Stage 7 — Regression, device tests, and release candidate
- Build and source/APK audits.
- Verify existing clone records and package/user IDs.
- Compare launch/session behavior to baseline.
- Test on supported Android versions and target devices.
- Open PR; never merge without explicit approval.

## 6. Acceptance and safety gates

- No direct commits to main.
- No deletion or replacement of existing app source or stored clone data.
- No package/applicationId change without a separately approved migration plan.
- No silent preference/database migration.
- No false success when reflective engine calls fail.
- No false VPN/IP/security status.
- No claim of complete host-data isolation without a demonstrated OS boundary and tests.
- No bypass of third-party app integrity, anti-fraud, root-detection, or anti-cheat systems.
- Every stage ends with changed-file inventory, test/build evidence, known limitations, and a request for approval before the next major stage.
- A successful APK build is not proof of feature completeness.

## 7. Current stage status

Stage 0 source inventory and static review: completed for the files listed above.
Runtime behavior and device-specific isolation: not yet independently verified in this review.
No runtime source code has been changed by this review document.
