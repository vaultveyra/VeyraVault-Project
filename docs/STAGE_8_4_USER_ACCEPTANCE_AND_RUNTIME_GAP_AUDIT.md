# Stage 8.4 — User acceptance findings and runtime capability boundary

Date: 2026-11-19
Branch: `feat/veyra-vault-product-foundation`
Audit base: `aa64eb41a0773a2299e19a1ed127c13531480679`
Scope: reconcile the user's first installed-build walkthrough with the checked-in source. This is a source audit and acceptance record, not a claim that the reported defects have been fixed.

## 1. User-observed acceptance results

The user reports the following from the installed build:

- Dashboard opens without a reported crash.
- Clone/Space count is correct.
- Bottom navigation actions work, but its appearance and icons are not acceptable; the center add action is too large.
- Tehran and New York clocks are absent.
- Device summary and IP information are absent; time-zone text appears in a visually disorganized position.
- Spaces core actions and app selection appear to work, but both screens need visual refinement.
- VPN page opens but contains no usable server/connection experience.
- Settings appearance is not acceptable. The user reports no theme selector, immediate-lock action, or About entry in the settings experience.
- Per-clone device/environment settings do not take effect in target apps; target apps appear to observe the host device environment.
- Chrome, Instagram and Soroush have launch/runtime problems. Exact failure causes are not yet established.

These are user-observed results, not automated test results. No account/session contents were requested or inspected.

## 2. Confirmed source findings

### 2.1 Dashboard and navigation

At audit base, `ui/MainActivity.java` builds the Spaces screen and its bottom navigation programmatically. The center add control is a text `+` with explicit 132 x 132 layout dimensions. Navigation controls are text labels rather than a consistent icon-based destination component. The app therefore does not yet meet the requested compact, icon-led five-destination visual treatment.

The existing `ui/DashboardActivity.java` is a separate destination. Dashboard requirements in `docs/REFERENCE_PROMPT_TECHNICAL_REVIEW.md` specify Tehran and New York clocks, their respective date formats, verified device/region/network summaries, clone count, and truthful unknown/unavailable states. The user confirms the clocks and meaningful device/IP summaries are missing in the installed build.

### 2.2 Appearance and settings

The manifest applies `@style/AppTheme`, whose current parent is `Theme.AppCompat.Light.NoActionBar`. `ui/SettingsHubActivity.java` is a programmatically assembled light-background list. It links to Global Environment, Security & App Lock, Permissions, About & Compatibility and pending reservations, and provides language switching. It has no appearance/theme preference control in the inspected source.

The source has a Security Settings screen and a Security Lock Activity, but the user's requested one-tap immediate-lock affordance is not established by the inspected SettingsHub screen. Do not conflate an existing PIN/lock screen with a verified quick-lock action.

### 2.3 VPN

`ui/VpnStatusActivity.java` only checks Android's current system VPN transport and explicitly states that VeyraVault has no dedicated VPN service or server connection. This is an honest status page, not a functional VPN. No connected state, server list, public IP, ping or routing claim may be fabricated.

### 2.4 Device/environment profile

At audit base:

- `ProfileSettings` contains only locale, time zone and location fields.
- `ProfileResolver` resolves those fields independently using Clone -> Global -> System precedence.
- `ProfileRuntimeClient` transports only those fields through the non-exported provider.
- `CloneProfileLifecycleCallback` runs before target Application creation and applies the resolved locale/time-zone settings.
- `ProfileRuntimeApplier` applies locale and time zone to the virtual package context/process.
- `CloneStore.GlobalEnvConfig` still stores Brand, Manufacturer, Model, Device, Country ISO and SIM/operator metadata, but comments explicitly identify device/SIM fields as metadata until a supported scoped engine API exists.
- `GlobalEnvironmentActivity` saves device metadata separately from the supported location profile and its confirmation text says device/SIM values remain metadata only.
- The pinned engine review in `docs/STAGE_6_PROCESS_AND_HOOK_ISOLATION_AUDIT.md` reports that the pinned source does not contain the previously reflected `BDeviceManager` or `BDeviceConfig` APIs. Earlier host-global Build mutation was removed because it was not a valid per-clone mechanism.

Conclusion: the user's report that device identity settings are not reflected inside target apps is consistent with the checked-in implementation. The missing behavior is not fixed by UI work or by simply adding fields to `ProfileSettings`. Do not reintroduce host-process Build mutation or undocumented reflection. First inspect the exact pinned engine revision for a documented, package/user-scoped capability. If no such API exists, mark those fields unsupported/metadata-only and do not claim application.

The existing per-field resolver is valid only for its currently supported fields. It is not a complete device/region profile resolver for all metadata currently displayed in the UI.

### 2.5 Third-party app compatibility

The user reports problems with Chrome, Instagram and Soroush. This audit has not obtained per-app exception traces, engine install results, WebView diagnostics, ABI/native-library failures, or package-specific launch logs. Therefore no single root cause is assigned. Diagnose each app independently using redacted, app-scoped diagnostics; do not change clone/session data or bypass app integrity/anti-fraud controls.

## 3. Corrective implementation order

1. **Stage 8.5 — Dashboard/navigation design foundation:** introduce reusable design tokens/components compatible with the existing Java/AppCompat stack; compact five-destination icon navigation; reduce center add affordance; preserve existing Spaces actions and navigation destinations. Test Persian RTL and English LTR.
2. **Stage 8.6 — Dashboard data:** implement Tehran and New York clocks with IANA time zones and appropriate date formats; display only verified host/device/network data and explicit unavailable states. Never infer public IP from VPN country selection.
3. **Stage 8.7 — Settings and appearance:** add persisted System/Light/Dark theme selection and apply it consistently; expose immediate lock only after verifying a safe synchronous lock-state transition; retain About/Compatibility navigation and make sections visually coherent.
4. **Stage 8.8 — Per-clone supported profile UX:** make supported Locale/Time Zone/Location values editable per Clone, show effective value and source for each field, and prove Clone > Global > System fallback with tests. Do not represent unsupported device/SIM metadata as applied values.
5. **Stage 8.9 — Engine capability audit:** inspect the exact pinned engine commit and its public/package-scoped APIs for any supported virtual device-property interfaces. Add only verified scoped capabilities with tests; otherwise retain explicit unsupported status.
6. **Stage 8.10 — App compatibility diagnostics:** reproduce Chrome, Instagram and Soroush failures individually and capture redacted failure categories before attempting targeted fixes.
7. **VPN remains a separate provider-dependent stage:** no server inventory or connected UI until a real provider/profile and VpnService tunnel are implemented and end-to-end routing is verified.

## 4. Non-destructive regression constraints

- Do not clear, rewrite, migrate, or replace CloneStore records or app-private clone data.
- Do not alter packageName/userId mappings, clone creation, session storage, or account/session state during visual work.
- Keep SharedPreferences/CloneStore as the active runtime source; no Room cutover.
- Keep PR #4 open and Draft. Do not merge. Do not change `main`.
- Preserve the distinction between host device properties, virtual app process settings, GPS location and IP geolocation.
- Do not spoof sensitive hardware identifiers or bypass third-party integrity/security checks.
- Do not claim a physical-device fix based on static source checks or CI alone.

## 5. Verification status

This Stage 8.4 document records a static source review plus the user's reported walkthrough. It does not modify runtime code and does not claim any of the user-reported defects are fixed. Each implementation stage must report exact changed files, automated tests, CI result, physical-device status and remaining limitations.
