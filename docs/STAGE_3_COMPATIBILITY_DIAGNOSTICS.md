# Stage 3 — Compatibility diagnostics (initial implementation)

## Scope

This increment adds a read-only, host-application compatibility report. It is intentionally limited to facts available to the VeyraVault host process and does not claim that a third-party app running inside a virtual space will observe the same environment.

## Files added or changed

- `app/src/main/java/com/veyravault/space/core/CompatibilityManager.java`
  - Collects Android API/release, supported ABI list, host native-library count, WebView provider (API 26+), declared host permission count, and whether the BlackBox core singleton is discoverable.
  - Returns immutable check results with OK / INFO / WARNING states.
  - Does not request permissions or change device/app configuration.
- `app/src/main/java/com/veyravault/space/ui/CompatibilityReportActivity.java`
  - Displays the diagnostic results and an explicit limitation notice.
- `app/src/main/AndroidManifest.xml`
  - Registers the report activity as non-exported.
- `app/src/main/java/com/veyravault/space/ui/AboutActivity.java`
  - Adds a navigation action to the report screen.

## Validation

- GitHub Actions run: 44146546804
- Commit: 22d8a38637110a38dca31e67766563f95a4a0fdf
- Profile resolver tests: PASS
- Security credential tests: PASS
- Workspace preparation: PASS
- Source audit: PASS; forbidden remote log endpoints: 0
- Release APK compilation: PASS
- APK package/binary audit: PASS; forbidden remote log endpoints in APK: 0
- Artifact SHA-256: `99eb3099bd5609a252197e3ba656a924d435925cf001b3572f15f58555a9a762`
- APK SHA-256: `c0404673990cb0e2db988127f276d16f5208e88188efa3aa128a6cb1e950ef95`
- The downloaded APK was inspected: both `CompatibilityManager` and `CompatibilityReportActivity` are present in DEX; native libraries for arm64-v8a and armeabi-v7a are packaged.

## Known limitations / not yet accepted

- No physical-device execution or UI test has been performed.
- The report inspects the host app only; it does not inspect every virtualized app's runtime compatibility.
- Declared permission count is not a permission-grant or enforcement audit.
- Native library count is not a compatibility certification.
- Engine singleton discovery is not proof that clone install/launch works.
- This initial report does not yet provide export/share, device-specific remediation, or structured diagnostic logging.
- The build workflow's signing job was skipped for this run; the APK is unsigned and must not be installed as an update over the user's signed production build.

## Next engineering work

1. Add focused unit/contract tests for diagnostic result collection, including API-level guards and unavailable WebView/provider states.
2. Add an explicit compatibility check for supported ABIs against packaged native ABIs.
3. Review reflection error handling in `Engine`; especially ensure failed reflective install calls cannot be reported as successful.
4. Review process-wide virtual hooks for cross-clone leakage, with isolation tests before any runtime-hook changes.
5. Add device-level smoke tests before declaring the diagnostics feature complete.
