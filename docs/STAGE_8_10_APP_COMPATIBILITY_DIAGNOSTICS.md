# Stage 8.10 — Per-app compatibility diagnostics (initial source audit)

**Status: partial — static source audit, fail-closed launch correction and a read-only per-Clone report are implemented. Physical app reproduction is still outstanding.**

## Scope

The outstanding user-reported failures concern Chrome, Instagram and Soroush running in virtual Spaces. The prior acceptance audit records those observations but does not contain per-app install traces, clone-process startup traces or redacted exception reports. No root cause is assigned to any of the three apps by this commit.

The pinned engine revision inspected here is `ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820`, the exact revision resolved by `scripts/prepare_workspace.py`.

## Findings confirmed from source

1. **The existing Compatibility report is host-only.** It reads the host Android API, supported ABI list, host native-library directory, host WebView provider, declared host permissions and whether the Engine singleton can be resolved. It explicitly does not certify the runtime of a virtualized package. These host facts cannot by themselves explain a Chrome, Instagram or Soroush failure inside a Clone.
2. **An unknown Engine install query was previously treated as absence during launch.** `queryInstalledAsUser` returns `null` when reflection, binder/service access or result decoding fails. The old boolean helper converted that into `false`; `launchCloneDetailed` then attempted installation. This conflated “Engine confirms absent” with “Engine could not determine state”.
3. **Install source handling is base-APK-only in the pinned Engine path.** `BlackBoxCore.installPackageAsUser(String, int)` obtains `PackageInfo.applicationInfo.sourceDir` and passes that single path to `BPackageManagerService`. The inspected install parser, ABI check and `CopyExecutor` then operate on that APK file. This path does not pass `splitSourceDirs` to the installer. If a host-installed app depends on split APKs, the virtual installation may therefore be incomplete. This is a conditional compatibility risk, not proof that any named app on the user's device is split-installed or that this explains its failure.
4. **The pinned Engine ABI check is architecture-limited.** `AbiUtils` accepts arm64 only when an `arm64-v8a` library entry is present and 32-bit only for `armeabi` / `armeabi-v7a`; it does not recognize x86/x86_64 ABI directories. APKs without native libraries pass this particular check. Actual compatibility also depends on the host/runtime architecture and packaged libraries.
5. **A successful launch return is not proof that the target stayed alive.** `BlackBoxCore.launchApk` resolves a launch Activity, calls `startActivity`, and returns true. That confirms the Engine accepted the launch request; it does not prove the target Application completed startup or remained visible.
6. **Some adjacent signals require explicit unknown states.** The previous GMS convenience wrapper returned false both when GMS was absent and when its reflection call failed. Stage 8.10 now adds a tri-state read-only diagnostic query so those cases are not conflated. The pinned Engine also has an Android R+ all-files-access warning path; neither signal alone establishes a target-app failure cause.

## Changes in this increment

- `Engine.launchCloneDetailed` now uses the tri-state `getCloneInstallState` result. It installs only when the Engine explicitly returns `ABSENT` and fails closed with `ENGINE_INSTALL_STATE_UNKNOWN` for an indeterminate query.
- Added a tri-state read-only GMS query (`INSTALLED`, `ABSENT`, `UNKNOWN`) so a reflection failure is no longer displayed as proof that GMS is absent. The existing boolean helper remains as a backward-compatible convenience method.
- Added a per-Clone snapshot to `CompatibilityManager`. It records host-source package version (not virtual Clone version readback), base/split APK counts, base-versus-split native ABI directories read from APK ZIP metadata, Engine install state, GMS state for the selected virtual user, host ABI/bitness, WebView provider and host all-files-access state.
- Added `AppCompatibilityDiagnosticsActivity`: it reads the existing Clone registry through `AsyncCloneRepository.loadClones`, allows selecting a Clone, builds the report on a worker thread, and shares only the bounded text report with Android's share sheet.
- The report deliberately omits Clone user IDs, coordinates, denied-permission sets, credentials, messages, photos, app-private files and session data. It does not launch, install, uninstall, clear or change settings for a target app.
- Added a test contract for read-only report scope, tri-state GMS, manifest registration and sharing; CI executes it.
- `scripts/test_engine_contract.py` continues to assert fail-closed launch behavior and the hook/launch/active-marker ordering.
- `scripts/test_stage_8_10_compatibility_diagnostics.py` continues to preserve the source-audit findings and host-only scope boundary.

## Acceptance boundary / next evidence required

This is a source-level correction and read-only per-Clone report, not a physical-device reproduction. The report can be exported through Android's share sheet, but it does not capture the target process's actual startup or crash outcome. It does not establish the actual failure mode of Chrome, Instagram or Soroush.

A complete per-app diagnosis still needs a device-side run for each affected Clone, recording only redacted technical fields: package identifier, host package version, base/split APK counts and native ABI directories, Engine install-state result, install result category, launch-request result, clone-process/Application lifecycle outcome, WebView/GMS availability state where relevant, and a bounded exception class/code. Do not capture account credentials, messages, media, authentication tokens, precise location, raw unrestricted logcat, or third-party private data. Keep the capture read-only and do not clear/reinstall/reset existing Clone data as a diagnostic shortcut.

No split-APK installer patch is attempted here: the pinned Engine currently accepts a single APK path, and a correct split-aware implementation would need an end-to-end review of package parsing, package settings, ABI selection, native-library copying and rollback semantics before it could be safely introduced.

## Non-destructive invariants

- SharedPreferences / CloneStore remains the live clone/profile registry; Room remains inactive.
- No Clone records, reservations, account/session data or virtual app-private data are modified by this diagnostic correction.
- No host-global Build/device property changes, identifier spoofing or third-party integrity bypass is introduced.
- PR #4 must remain open and Draft; all work stays on the feature branch.
