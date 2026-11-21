# Stage 8.7.2 — Launcher icon selection and About requirements

## Launcher icon and label
- Add a dedicated searchable Settings destination for launcher icon/label options.
- Expose only the five launcher aliases bundled in `AndroidManifest.xml`: VeyraVault, Calculator, Calendar, Notes, and Weather.
- Use the actual vector drawable for every option; no arbitrary image upload, installed-app impersonation, or unsupported dynamic icon behavior is claimed.
- State clearly that this changes the app's launcher entry only and is not a security/concealment feature.
- `AppDisguiseManager` rejects invalid indices, enables the selected alias first, disables all other bundled aliases, then verifies that exactly one supported alias is effectively enabled.
- On PackageManager runtime failure, attempt to restore the exact prior component override states and return false. The UI only displays success after verified state.
- Existing Security Settings route opens the dedicated selector rather than maintaining a second set of icon controls.

## About and requirements
- Read application ID, version name/code, Android release/API, target SDK, and requested permission/grant flags from PackageManager and platform APIs.
- Show explicit capability boundaries for Locale/Time Zone, Location, device/SIM metadata, VPN, public IP, App Lock/Device Admin, Backup/Restore, and GMS/third-party compatibility.
- Do not claim zero telemetry, complete device/session isolation, live VPN, a real IP lookup, or complete physical-device validation.
- Keep compatibility report and contact actions available.

## Tests and safety
- `AppDisguiseManagerInstrumentationTest` cycles through every manifest-backed alias, verifies the single-active-alias invariant, rejects invalid indices, repairs an ambiguous alias configuration, and restores every original PackageManager component state after the test.
- `scripts/test_launcher_icon_and_about_contract.py` checks manifest-backed resources, search and truthful result handling, PackageManager-derived About data, and capability disclosures.
- CI executes the new contract test and full Android Instrumentation suite.
- No CloneStore or ProfileStore records, clone data, package/user identities, accounts, sessions, Engine lifecycle, or Room state are modified.
- Launcher component state is app metadata only. Changing it does not hide the app from Android system settings, security tools, or other installed-app inventories.

## Verification status
- Source and instrumentation tests are implemented on the feature branch.
- CI, APK audit, and physical launcher behavior must pass before this stage is called verified.
- Physical launcher refresh behavior may vary by launcher; the UI tells the user it may take a moment to refresh.
