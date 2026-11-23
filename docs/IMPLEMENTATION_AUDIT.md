# VeyraVault implementation audit

Audit basis: checked-in `main` source tree and GitHub Actions logs reviewed on 2026-11-14. This is a static source audit; items marked as implemented are present in source, not necessarily verified on a physical device.

## Status key

- **Present in source**: corresponding classes or UI are present.
- **Partial / unverified**: some code exists, but runtime behavior, isolation, or completeness is not established.
- **Missing from current app source**: no complete implementation was found in the checked-in app source.
- **Build blocker**: prevents a trustworthy release build.

## Current build blocker

The V3 upgrade scripts generate a second package tree under `com.veyravault.app`, while the checked-in app and workspace configuration use `com.veyravault.space`. The generated V3 `MainActivity` imports classes such as `com.veyravault.app.core.Engine`, `GmsSupportManager`, `SecurityManager`, `VirtualHookManager`, and packages `.net` / `.util` that are not generated at the imported locations. It also references activities that exist only under the older `com.veyravault.space.ui` package. This caused the compile errors in Actions run 43635632903.

The stabilization workflow change keeps the existing checked-in app as the build input and syntax-checks the staged V3 scripts without overlaying their incomplete source tree. This is an interim build-stabilization measure, not completion of the V3 migration.

## Feature matrix

| Area | Source audit status | Evidence / remaining work |
|---|---|---|
| Main dashboard | Present in source | `MainActivity` lists spaces and provides navigation; runtime usability still needs device testing. |
| Add applications | Present in source | `AddAppActivity` supports selecting installed apps and batch selection for clone creation. |
| Multiple clones | Partial / unverified | `CloneStore` records package/user entries and `Engine` delegates to BlackBox. Real app-data/session separation must be tested on devices and across app versions. |
| Per-clone naming and metadata | Partial | Clone records store display name, GPS coordinates, device fields, and denied-permission flags. Full feature behavior is not proven. |
| Global environment | Present, limited | Global brand/model/country/operator fields and a global settings screen exist; a comprehensive country/city profile catalog is not present in the current app source. |
| Per-clone region profiles | Partial / missing | Some per-clone device/location fields exist. A complete reusable country/city profile manager and bulk profile application were not found in the current app source. |
| Location settings | Partial / unverified | UI stores coordinates and invokes reflection hooks. Hooks suppress errors; real behavior and app compatibility are unverified. |
| Device information configuration | Partial / unverified | Reflection changes selected Build fields and calls BlackBox device configuration. It does not prove that all APIs or remote services use those values consistently. |
| SIM/operator configuration | Partial / unverified | Global operator/country fields exist; real SIM state is not changed, and app/server observations are not guaranteed to match. |
| Network manager / VPN | Missing from current app source | The checked-in `space` app has no complete VPN service or per-clone traffic routing. V3 contains a generated service, but it is not currently integrated into the checked-in app; the generated service also does not implement packet forwarding to a VPN server. |
| Permissions UI | Present, enforcement missing | `PermissionsActivity` saves denied-permission flags in `CloneStore`. The current `VirtualHookManager` does not enforce those flags, so the toggles must not be represented as actual permission blocking. |
| Security lock | Present, weak credential storage | PIN/pattern flow exists. Current `SecurityManager` hashes with SHA-256 and a fixed prefix salt; replace with a password KDF and per-install random salt, plus lockout/rate limiting. |
| Device Admin / anti-uninstall | Present, claim inaccurate | Device Admin activation exists. Android Device Admin does not make an app impossible to uninstall; UI and explanatory text must describe the actual limitation. |
| App icon aliases | Present in source | Manifest aliases and disguise manager exist; test launcher behavior across launchers and Android versions. |
| GMS support | Partial / unverified | Reflection-based install/uninstall calls exist; success must be confirmed from actual engine results, not inferred from a void return. |
| Shortcuts | Present in source | Shortcut helper and dashboard launch handling exist; runtime test required. |
| Backup / restore | Missing from current app source | No complete per-clone encrypted backup/restore flow found. |
| Storage and resource manager | Missing from current app source | No complete per-clone storage/RAM reporting or quota manager found. |
| Batch management | Partial | Batch app selection exists; batch region, security, network, backup, and deletion policies are not comprehensively implemented. |
| Diagnostics / audit reports | Partial | Build-time source/APK audit scripts exist; no complete in-app diagnostic/export workflow found. |
| Dark mode / themes | Partial | V3 theme code is staged but not integrated into the current app build. |
| Localization | Present, limited | Persian/English strings and locale helper exist in the current app source. Full translation coverage requires review. |
| Build and signing | Partial | Actions separates unsigned build and signing; signing secrets are isolated. The signing job must fail when any required secret is missing. A successful signed artifact still needs a completed main-branch run. |

## Security and reliability findings

1. Replace the fixed-prefix SHA-256 lock hash with a vetted password KDF (for example PBKDF2-HMAC-SHA-256 with a unique random salt and calibrated work factor, or a maintained Argon2id implementation where supported).
2. Correct the anti-uninstall wording. Device Admin is not an unremovable-app mechanism.
3. Do not claim 100% host-data or device-information isolation. Add observable tests and label any unverified behavior accurately.
4. Enforce permission policies in the virtualization engine; a stored checkbox value alone is not enforcement.
5. Review `usesCleartextTraffic=true` and remove or narrowly scope cleartext traffic if no documented dependency requires it.
6. Review broad storage, package visibility, install/delete, location, and other sensitive permissions; request only those required for each feature.
7. Add runtime diagnostics for reflection failures instead of silently swallowing every exception.
8. Pin and review the external BlackBox engine revision and its transitive dependencies.
9. Test clone persistence, app upgrades, process death, device reboot, Android version differences, and Huawei/Samsung-specific behavior before declaring isolation reliable.

## Recommended implementation order

1. Establish a reproducible build from the existing `com.veyravault.space` source tree.
2. Run and document an installation/smoke test on a physical Android device.
3. Complete a deliberate V3 migration: choose one package namespace, migrate all existing screens and core services together, update the manifest and Gradle namespace, then remove duplicate legacy sources only after tests pass.
4. Implement and test real permission enforcement, security credential storage, and accurate Device Admin behavior.
5. Add region profile catalog and per-clone profile inheritance.
6. Implement a real, explicitly configured VPN transport and per-app routing only where Android supports it; do not treat a TUN interface alone as a working VPN.
7. Add encrypted backup/restore, storage management, batch policies, and in-app diagnostics.
8. Expand automated tests and device compatibility coverage before release.

## Additional security changes on the stabilization branch

- The upstream default crash-log destination is explicitly disabled through the app's `ClientConfiguration` override. The upstream sender code remains in the third-party engine, so this configuration must not be removed; a future engine migration should remove or replace that feature deliberately.
- Cleartext HTTP traffic is disabled by the app manifest override.
- The upstream BlackBox engine is pinned to the audited commit listed above to make builds reproducible and prevent silent upstream changes.

## Release gate

Do not merge a build change until the unsigned APK build, source audit, APK audit, and (on a protected non-PR release run) keystore signature verification all pass. Do not claim a feature is complete until its behavior is tested, not merely because a screen or class exists.


## Feature branch updates — Stage 3 (2026-11-17)

A first read-only in-app compatibility report has been added on the feature branch:
- `CompatibilityManager` reports host Android/API, supported ABI, native library count, WebView provider (where supported), declared host permission count, and BlackBox core discoverability.
- `CompatibilityReportActivity` presents these values and states the limits of host-only diagnostics.
- The activity is non-exported and reachable from About.
- CI run 44146546804 completed successfully; APK compilation and binary audit passed, and the known remote log-upload endpoint count in the APK was zero.

This is an initial diagnostics foundation, not a full compatibility certification. No physical-device test has been performed. The report does not verify permission grants, per-clone runtime behavior, or remote service observations. See `STAGE_3_COMPATIBILITY_DIAGNOSTICS.md`.

Outstanding high-priority reliability findings remain: `Engine.installPackageAsUser` currently returns success from its exception path, and process-wide hooks require cross-clone isolation review. These must be addressed with targeted tests before modifying the virtualization runtime.


## Stage 5 — Engine install/launch failure semantics

The pinned upstream BlackBox revision was inspected directly. Its `BlackBoxCore.installPackageAsUser(String, int)` returns an `InstallResult` with a public boolean `success` field; its `isInstalled(String, int)` method reports installation for a specific virtual user. The previous host wrapper returned `true` after reflection exceptions, masking failed installs.

The feature branch now fails closed when the core, reflected result, success field, or invocation is unavailable. The pinned `launchApk(String, int)` contract returns a primitive boolean, so the wrapper now requires an explicit `true` result; null is not treated as success. Clone launch first checks whether the package is already installed for its virtual user; only absent clones are installed, and a failed installation stops the launch attempt. This avoids reinstalling an existing clone on every launch while preventing failed installation from being treated as success.

This is a targeted reliability fix, not a claim that all engine operations are now verified. Other reflection paths still require method-by-method review. This change does not alter clone IDs, CloneStore persistence, session data, or VirtualHookManager behavior.


The Stage 5 reliability fix also updates both clone-creation entry points: Add App and Duplicate now save a CloneStore entry only after the engine confirms installation success. The Spaces launch action now surfaces a failure message rather than always displaying a launch toast. The regression contract test covers these guards. No existing clone records are migrated or rewritten by these changes.


## Feature branch updates — Stage 6 (2026-11-17)

The pinned BlackBox revision was traced beyond the public launch API:
- `BProcessManagerService` allocates virtual app processes in the host `:pN` process family and indexes process records by virtual UID and process name.
- `BActivityThread` binds the virtual app package/Application inside that managed process.
- The pinned engine's `BLocationManager` exposes package/user-scoped `setPattern(userId, packageName, ...)` and `setLocation(userId, packageName, ...)`.
- The pinned source tree does not contain the `BDeviceManager` or `BDeviceConfig` classes previously targeted by the app's reflection code.

Accordingly, the feature branch removes the host-process `Build` static-field override and host `LocationManager.mService` proxy from `VirtualHookManager`. Clone location configuration remains routed through the engine's package/user-scoped location manager. Existing device/SIM profile fields remain stored without migration or deletion, but the Persian and English UI now correctly describes them as metadata only because this pinned engine integration has no verified scoped API for applying them. CI adds `scripts/test_hook_isolation_contract.py` to prevent reintroducing host-global mutations or overstating device-profile behavior.

The active-clone marker is also persisted only after `launchApk` returns explicit `true`. These changes do not modify clone IDs, clone registry keys, virtual package data, or session data. Physical-device validation with multiple concurrent clones is still required.


## Stage 7 — Clone persistence migration readiness (2026-11-17)

A non-destructive migration inventory and plan is added in `docs/STAGE_7_CLONE_PERSISTENCE_MIGRATION_PLAN.md`. It records all five legacy persistence categories, every clone JSON field, the composite `packageName + userId` identity, the separate global profile and UI state, and the independent last-active-launch marker. The proposed Room schema and staged import/backup/verification/rollback sequence are documented, but Room is not yet added and `CloneStore` remains unchanged as the only source of truth.

The inventory identified important migration hazards: malformed clone JSON is currently converted to an empty list by `getAll()`, write failures are swallowed, and whole-array read/modify/write operations can lose concurrent updates. These behaviors must be addressed with explicit error reporting and transactional repository APIs before any persistence cutover. Room must not be queried on the main thread. The build uses a generated Gradle app module from `scripts/prepare_workspace.py`, so a future Room dependency must be added to that generated template after checking the pinned engine's Gradle/AGP compatibility.

CI now runs `scripts/test_clone_store_migration_inventory.py` to guard the existing preference namespace, keys, serialized fields, composite clone identity, and migration safety-plan requirements. This stage does not change clone records, virtual app storage, account/session data, or runtime persistence. Room implementation, import, cutover, and legacy-key retirement are deferred to later independently reviewed stages.


### Stage 7.1 — Inactive Room schema foundation (2026-11-17)

Pinned upstream build configuration was verified at `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`: Gradle 8.14.5, AGP 8.13.2, Bcore Java 21, generated app Java 8, compileSdk 35, minSdk 21. Room 2.6.1 runtime and Java annotation processor are now included in the generated app module template in `scripts/prepare_workspace.py`.

Added a non-active Room schema under `core/persistence`: composite clone identity, normalized denied-permission rows with a cascading clone FK, exact string collapsed-space keys, singleton global profile/master GPS/last-active entities, DAOs, database, and opt-in provider. The provider is not called by application startup or CloneStore. There is no destructive migration fallback and no main-thread query opt-in. The old SharedPreferences CloneStore remains the sole active persistence path; no import, preference rewrite, clone/session data change, or cutover has occurred.

CI now checks the Room foundation boundary and will compile the Room annotations and generated DAO/database code as part of the release APK build. The schema is provisional until the next stage adds snapshot validation, backup/restore, transactional import and parity tests.


### Stage 7.2 — Read-only snapshot and verified backup (2026-11-17)

The exact legacy CloneStore preference namespace and all five keys are now captured by a strict read-only snapshot reader. It preserves key-presence flags and original clone JSON, validates composite identities and enabled coordinates, rejects malformed/ambiguous data, and produces a canonical SHA-256 digest. The opt-in backup writer uses app-private storage, Android AtomicFile, fsync, read-back verification and immutable existing-backup semantics. Neither class is wired to startup or normal runtime flows.

### Stage 7.3 — Opt-in transactional Room import and parity (2026-11-17)

The Room schema now retains each clone's original JSON and adds a migration-provenance singleton with the full canonical source payload and digest. An explicit worker-thread-only importer writes into an empty Room database inside one transaction and refuses to overwrite existing data. Repeat import is considered idempotent only when the digest matches and the parity verifier confirms every persisted row still matches the snapshot. The verifier checks clone identity/fields, raw clone JSON, denied permissions, collapsed keys, global profile, master GPS, optional/stale active marker and migration provenance.

The importer is not called from VaultApp, CloneStore, Activities or normal runtime flows. CI's new importer test is a source-contract regression check, while the APK build compiles Room and generated DAO code. This is not a substitute for Android instrumentation tests. Forced transaction rollback, process-death/restart, and real Room round-trip tests remain release gates. SharedPreferences remains authoritative; no cutover or legacy-key deletion has occurred.


### Stage 7.4 — Android Room instrumentation harness (2026-11-17)

Added AndroidX instrumentation tests against the actual Room database on an API 34 x86_64 emulator. Coverage includes populated import/parity, repeat-import idempotence, row-tamper detection, SQLite-trigger-induced transaction rollback across all tables, disk close/reopen durability, empty snapshots and absent/stale active markers. A debug-only test Application prevents the virtual-app engine from starting in the test process; debug packaging excludes native engine libraries and explicitly selects `x86_64` to match the CI emulator. The production release Application, manifest, ARM ABI filters and runtime persistence path are unchanged.

GitHub Actions runs `:app:connectedDebugAndroidTest` before the unsigned release build. The first completed emulator attempt identified an ABI mismatch (`No compatible devices connected`): the generated app inherited ARM-only ABI filters while the CI emulator was x86_64. The Debug-only ABI override and a source-contract assertion were added; the next run must confirm that instrumentation now reaches the five test methods. This stage adds no runtime migration wiring and does not modify CloneStore, legacy preferences, virtual package data, account/session data, or user clones. Emulator results must pass before treating Stage 7.4 as validated; physical-device upgrade, backup/restore and process-death testing remain required before any separately approved cutover.


## Stage 8.3 — Asynchronous Clone launch orchestration (validated on current implementation head; 2026-11-19)

- Added `AsyncCloneLaunchRepository`: strict CloneStore registry lookup, install-state check/install, location-hook synchronization, engine launch and active-launch marker persistence execute on one serialized worker.
- Added `Engine.launchCloneDetailed` so engine launch success/failure and the typed location-hook outcome are reported separately. The synchronous `Engine.launchClone` remains as a compatibility wrapper; MainActivity dashboard and shortcut UI use the asynchronous repository.
- MainActivity receives launch callbacks on the main thread. Feedback distinguishes engine launch failure from a launched app whose location hook is FAILED or UNSUPPORTED.
- Removed synchronous location-hook IPC from the per-clone metadata editor because metadata edits do not change location settings.
- Added `scripts/test_async_clone_launch_contract.py` and CI wiring; updated engine and MainActivity contract checks.
- Validated implementation head: `58a00fc1b5441f94b3e503cde2cacce4a06116ae`.
- Push CI run #686 (run ID `44561153783`): **46/46 Android Emulator instrumentation tests completed, 0 skipped, 0 failed**. All source/contract checks passed, source audit passed, unsigned Release APK compiled, APK audit passed, and isolated signing job succeeded.
- PR CI run #687 (run ID `44561170843`): **46/46 Android Emulator instrumentation tests completed, 0 skipped, 0 failed**. All source/contract checks passed, source audit passed, unsigned Release APK compiled and APK audit passed. Signing was skipped for the pull_request event as configured.
- The emulator bootstrap initially produced repeated ADB connection retries and an emulator-console warning; the instrumentation task subsequently completed all 46 tests successfully in both runs. The transient startup messages are not test failures.
- APK audit reported **0 forbidden remote log endpoints**.
- Push unsigned artifact ID `14552140234`, ZIP SHA-256 `c6ef4903640ffb16ae19dd254608f106cd621085f7457494ea6eb347fcb53b79`.
- Push signed artifact ID `14551755945`, ZIP SHA-256 `405203263125b69999e235cd2e574956e8dab96a341322bd255b90ac3714e291`. APK signature verification: v2=true, v3=true; v3.1/v3.2/v4=false.
- PR unsigned artifact ID `14550543052`, ZIP SHA-256 `7888f5a9107b503558907e88e4145558263ce8cb6eb2f2938c2591500e0f584d`.
- Physical-device validation of clone launch latency, lifecycle behavior, third-party app location observations, and actual process isolation remains outstanding. CI emulator success does not establish those physical-device behaviors.
- The synchronous Engine compatibility wrapper remains available for non-UI callers; a full caller audit/migration is still required before removing it.
- SharedPreferences/CloneStore remains the active runtime source of truth. Room remains inactive; no migration/cutover occurred. No Clone registry/session/account data was intentionally modified by this stage.


### Stage 8.3.1 — Production Clone-launch call-site audit (2026-11-19)

- Audited all 58 Java source files under `app/src/main/java` from immutable branch head `92360877fe0dac84bc16b00d19be2c6f70cf69b1`. The complete production source-path inventory came from the recursive Git tree for that exact commit; every listed source file was fetched and searched for direct `Engine.launchClone`, `.launchClone(`, and `launchApk(` call patterns.
- The only production launch-related call sites found were: `MainActivity.java` shortcut path calling `AsyncCloneLaunchRepository.launchClone`; `MainActivity.java` clone-icon path calling the same repository; and `AsyncCloneLaunchRepository.java` worker calling `Engine.launchCloneDetailed`.
- No in-repository production caller of the synchronous `Engine.launchClone` compatibility wrapper was found. The wrapper remains in place for compatibility; this audit does not justify removing a public method that may be used by code outside this app source tree.
- The only in-app reflective `launchApk` invocation is inside `Engine.launchCloneDetailed`, after location-hook synchronization. The two MainActivity paths dispatch through the serialized single-thread worker. Completion callbacks are posted to the main looper; the Activity callback paths check finishing/destroyed state. The clone-icon path disables its clickable frame while the launch is pending.
- This was a static source audit, not a new runtime test. It does not inspect opaque runtime-generated calls, external consumers of the public compatibility wrapper, or the pinned engine's internal implementation. CI emulator evidence remains the existing Stage 8.3 evidence; physical-device launch/lifecycle/process-isolation and third-party location-observation validation remain outstanding.
- No runtime source, CloneStore payload, Clone/session/account data, manifest, or engine dependency was changed by this audit. No Room migration/cutover was performed.


## Stage 8.4 — User acceptance and runtime gap audit (2026-11-19)

Added `docs/STAGE_8_4_USER_ACCEPTANCE_AND_RUNTIME_GAP_AUDIT.md` to reconcile the user's first installed-build walkthrough with the current source.

Confirmed gaps:
- Dashboard/navigation remains programmatic and text-led; the center add action is 132 x 132 and does not meet the requested compact icon-led design.
- The dashboard requirements for Tehran/New York clocks and verified device/network summaries are not met by the installed build reported by the user.
- SettingsHub has no persisted System/Light/Dark appearance selector.
- VPN status screen is explicitly read-only system-VPN detection; no VeyraVault VPN service/server tunnel is implemented.
- ProfileSettings/ProfileResolver/ProfileRuntimeClient/CloneProfileLifecycleCallback currently support locale, time zone and location fields only. Brand/model/country/SIM values in CloneStore remain metadata; the pinned engine review found no supported BDeviceManager/BDeviceConfig API. The user's observation that target apps still see host device properties is consistent with source.
- Chrome, Instagram and Soroush launch/runtime failures remain unclassified until redacted per-app diagnostics are available.

This is a static audit and user-reported acceptance record, not a runtime fix or physical-device certification. It defines Stages 8.5–8.10 and preserves the CloneStore/session, no-Room-cutover, feature-branch-only and Draft PR constraints.


## Stage 8.8.9 — Runtime App Lock Activity lifecycle verification (2026-11-22)

- Reworked the Debug instrumentation test to launch the first probe Activity with ActivityScenario, open the second Activity from the first Activity in the same task, verify matching task IDs, and wait for the first Activity to resume before asserting the session remains unlocked.
- Corrected the Stage 8.9 runtime test contract's observer variable marker.
- Final validated feature-branch head for this stage: bbef9fd41f98ee52959bac7915ec0b79c292415f.
- Push run 45063108486: 68/68 Android Emulator instrumentation tests passed, 0 skipped, 0 failed; all source/contract checks, Source Audit, unsigned Release APK build, APK audit and isolated signing job passed.
- PR run 45063112951: 68/68 Android Emulator instrumentation tests passed, 0 skipped, 0 failed; all source/contract checks, Source Audit, unsigned Release APK build and APK audit passed. Signing is skipped for pull_request events by workflow policy.
- Both APK audits reported 0 forbidden remote log endpoints.
- Push unsigned artifact 14770912029, ZIP SHA-256 8c3b50fe0e78f6187320452249aa41bd0676be14639868ae624e92ce043d54dc.
- Push signed artifact 14770594866, ZIP SHA-256 c89fec60a3c9a9d704f437fd4587770cb92f0d53fc52cbff23d6a557bcc534c1. apksigner verify --verbose: v1=true, v2=true, v3=true; v3.1/v3.2/v4=false. The log also reported META-INF metadata/dependency-entry signature-coverage warnings; these are retained as release-review notes.
- PR unsigned artifact 14770054296, ZIP SHA-256 5b2d30d82db5a0e1db59256ea89c4862813a43b29d15bbc868dbdd9cf3673007.
- Validation boundary: Debug Room instrumentation still uses RoomTestApplication and explicitly calls the production controller's initialize entry point. It does not execute the complete production VaultApp.onCreate() method or replace physical-device/OEM testing.
- PR #4 remains open and Draft; no merge or main modification occurred.

## Stage 8.9 — Pinned Engine device and environment capability audit (2026-11-22)

- Audited the exact ALEX5402/NewBlackbox revision 89b59836c66f173756a4ae258cf379a957649820 pinned in scripts/prepare_workspace.py.
- Confirmed the Engine has package/user process isolation and active telephony, serial, Android ID and Wi-Fi hooks, but those hooks do not expose configurable per-Clone values: some derive values from the host package, some return fixed Wi-Fi constants, and Android ID only generates a random fallback for invalid underlying results.
- Confirmed the Engine's location service stores its configuration by virtual user ID and package name. VeyraVault uses this scoped location API with readback. Cell list storage exists, but two telephony adapter methods return null and therefore do not establish complete cell-profile support.
- Confirmed current VeyraVault ProfileSettings transports exactly Locale, Time Zone, location-enabled, latitude and longitude. Other device/SIM data remains metadata unless a separately verified scoped implementation is added.
- Added docs/STAGE_8_9_ENGINE_DEVICE_CAPABILITY_AUDIT.md, a source-contract test, and CI wiring. No production hook or Engine source was changed.
- No CloneStore records, virtual package data, account/session data or Room migration state was modified. SharedPreferences remains the active profile source; Room remains inactive.
- Physical-device and target-app readback validation remain outstanding for OEM-specific behavior.


## Stage 8.10 — Per-app compatibility diagnostics (partial source audit)

- Inspected the existing compatibility report and confirmed it reports host-only facts; it does not certify Chrome, Instagram or Soroush inside a virtual Clone.
- Audited the pinned Engine install path and found it passes only the base `sourceDir` APK to the installer rather than `splitSourceDirs`. This is a conditional risk for split-installed apps, not a confirmed cause on the user's device.
- Found the launch flow previously treated an indeterminate Engine install query as package absence and could attempt installation. Corrected it to fail closed with `ENGINE_INSTALL_STATE_UNKNOWN`; only an explicit Engine `ABSENT` result can trigger installation.
- Added a static contract test and CI wiring. No split installer changes, CloneStore edits, app-data clearing or account/session changes were made.
- Stage 8.10 remains incomplete until per-app redacted device traces and physical-device smoke tests identify actual startup outcomes.


## Stage 8.10 — Read-only per-Clone diagnostic report (2026-11-22)

- Added a per-Clone diagnostics screen reachable from the existing Compatibility Report. It reads Clone entries asynchronously and generates each snapshot on a worker thread.
- The snapshot reports only package metadata, base/split APK counts, native ABI directory names, Engine install state, tri-state GMS availability, host architecture, WebView provider and all-files-access state. It explicitly states that target startup was not tested.
- Reports can be shared through Android's standard share chooser. They omit account/session contents, credentials, messages, photos, precise coordinates, Clone user IDs, denied-permission sets and private app files.
- GMS availability is now tri-state for diagnostics; Engine query errors are no longer conflated with confirmed absence.
- This remains a read-only diagnostic snapshot, not an automatic repair or a physical-device compatibility certification. Chrome, Instagram and Soroush still require separate device-side launch traces.


### Stage 8.10 — Bounded Clone runtime lifecycle trace (2026-11-22)

- Added local Logcat milestones at Engine launch request/accept/reject, hook preparation, virtual-process callback entry, and target Application.onCreate begin/complete.
- The callback milestones are wired to the pinned Engine's verified invocation order. Engine acceptance and Application.onCreate completion are explicitly not treated as proof that the app Activity rendered or remained alive.
- Trace fields are allowlisted, sanitized and truncated. No trace file, SharedPreferences/CloneStore write, network upload, credentials, messages, media, location, or session data is read or emitted.
- Added CI contract coverage for event ordering and the no-persistence/no-upload boundary.
- Physical-device traces for Chrome, Instagram and Soroush remain required; no app-specific root cause is asserted.


### Stage 8.10 — Per-process lifecycle callback registration observability (2026-11-22)

- Closed a trace-visibility gap: lifecycle-callback registration success and failure are now logged to the bounded local `VeyraCloneRuntime` stream.
- Each marker includes the sanitized VeyraVault host package/process name when Android can resolve it, allowing the main UI process to be distinguished from separate virtual host processes.
- Failure outcomes are limited to fixed categories or exception class names; exception messages, stack traces, persistent storage, network transmission, Clone data and session data are not included.
- Extended the Stage 8.10 source contract to require both registration outcomes and the process-name source.
- This remains diagnostic instrumentation only. It does not retry registration, change callback order, or prove third-party app startup; physical-device traces are still required.


### Stage 8.10 — Profile trace semantic precision (2026-11-22)

- Renamed the profile milestone from `PROFILE_APPLIED` to `PROFILE_APPLY_RETURNED` and changed its outcome to `apply_returned`.
- The callback logs now state that the profile apply operation returned, rather than claiming verified device/runtime application. The applier has no readback API; the trace therefore cannot claim that the target app observed the resolved Locale/TimeZone.
- Extended the source contract to reject the old over-strong event name and require the conservative event, outcome and documentation.
- No profile resolution, setting application, fallback behavior, clone launch sequence or persisted data changed.


## Stage 8.11 — App-lock failed-attempt throttling (2026-11-23)

- Added deterministic exponential backoff to the main VeyraVault PIN/Pattern credential verifier: four initial incorrect attempts are unthrottled; subsequent wrong attempts trigger 30 seconds, 1 minute, 5 minutes and a maximum 15-minute cooldown.
- Active cooldown is checked before PBKDF2 derivation. Repeated submissions during a cooldown neither hash the supplied secret nor increment the count.
- A successful verification clears attempt metadata and retains the existing legacy-hash upgrade behavior. Setting a new credential or disabling App Lock also resets attempt metadata.
- The cooldown deadline and attempt count are stored as non-secret metadata in the existing private security preferences, without changing credential hash or mode keys. A monotonic in-process companion prevents wall-clock adjustment from shortening a cooldown while the host process remains alive.
- Added Persian/English cooldown messaging and cleared a failed PIN from the input field.
- Added pure-Java boundary tests, extended the KDF test harness, and added CI source-contract coverage.
- Limitations: this is application-level throttling, not Keystore/hardware-backed rate limiting. A failed preference commit receives only a process-local fallback; reboot/time-tampering behavior is not claimed as tamper-proof.
- No CloneStore, virtual app package, account/session, profile or Engine state was modified. SharedPreferences remains active; Room remains inactive.


### Stage 8.11 — Restore full app-lock test fixture state (2026-11-23)

- Fixed the existing AppLock lifecycle instrumentation fixture to snapshot and restore the two new attempt-throttling preference keys and both associated in-memory fields.
- Extended its preference restoration helper to retain Long values exactly.
- Extended the source contract to require complete cleanup, preserving the original security preference map and in-memory process state.
- CI's first Android run reached 69/69 tests with one failure in the older lifecycle test's exact preference-map cleanup assertion; ADB also emitted transient offline messages earlier in boot. The observed assertion was caused by the older fixture not knowing about the newly added zero-valued attempt metadata keys.
- The new attempt-throttling instrumentation itself did not appear among the failed test names. Re-run is required to verify the fixture correction and the new test together.
- No production credential, CloneStore, Engine, account/session or profile behavior was changed in this correction.
