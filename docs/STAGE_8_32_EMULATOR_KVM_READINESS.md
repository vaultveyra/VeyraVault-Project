# Stage 8.32 — Android Emulator KVM readiness and CI reliability

## Stage 8.31 CI failure evidence

On commit `70cb868e05f11cb6fe620e4ab9786434b877dd52`, both Push and Pull Request workflow runs passed all static contracts through Stage 8.31 and completed Debug APK assembly. Both failed during API-34 connected instrumentation, before API-21, Release compilation, or native APK audit.

The failed device was not reported as a test assertion failure. The logs showed:

- Emulator launched with `-accel off`.
- Repeated `adb: device offline`.
- `ShellCommandUnresponsiveException` while reading device properties.
- `Failed to start Emulator console for 5554`.
- Gradle reported `Unknown API Level` and `No compatible devices connected`.

This is consistent with the workflow not preparing access to `/dev/kvm` before invoking `reactivecircus/android-emulator-runner`. The action automatically disables Linux hardware acceleration when KVM is not accessible. On a standard runner, that can force slow TCG software emulation.

## Changes

- Add a pre-emulator step that checks for `/dev/kvm`, installs the recommended udev rule, reloads udev, and triggers the KVM device.
- Log whether KVM is actually readable/writable after the permission update. If it is unavailable, report the TCG fallback explicitly rather than claiming hardware acceleration.
- Set `disable-linux-hw-accel: auto` explicitly for API-34, API-27 and API-21 emulators.
- Retain `ANDROID_I_WANT_MY_TCG=yes` on all three emulator steps so a supported software fallback remains possible.
- Use a 1200-second emulator boot timeout for all three API levels and reduce API-34 virtual CPU count from four to two.
- Stop running duplicate Push and Pull Request builds for the feature branch. Feature commits are validated by the PR event; pushes to `main` still run the workflow.

## Validation

A new contract test verifies that KVM preparation precedes all three emulator steps, that the udev rule and fallback diagnostics remain present, and that API 34, API 27 and API 21 retain their required configuration. The next successful CI run must pass the API-34 full instrumentation suite, the API-27 full target-OS suite and the dedicated API-21 minimum-API smoke test; this stage does not turn an emulator boot into a passing test automatically.

## Scope

Only CI workflow orchestration, emulator readiness checks, a static contract test, and documentation change. App runtime code, the pinned Engine source, CloneStore, user Clone data, accounts, credentials, and sessions are untouched. No PR merge or main-branch modification is performed.
