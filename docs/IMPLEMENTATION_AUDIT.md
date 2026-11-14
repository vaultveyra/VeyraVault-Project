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
