#!/usr/bin/env bash
set -euo pipefail

# Pin every ADB operation to the emulator created by android-emulator-runner.
adb -s emulator-5554 wait-for-device

SDK_LEVEL=""
BOOT_COMPLETED=""

# ADB transport readiness is not the same as Android finishing its boot.
for ATTEMPT in $(seq 1 90); do
  SDK_LEVEL="$(adb -s emulator-5554 shell getprop ro.build.version.sdk 2>/dev/null | tr -d '[:space:]' || true)"
  BOOT_COMPLETED="$(adb -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '[:space:]' || true)"
  if [[ "$SDK_LEVEL" == "27" && "$BOOT_COMPLETED" == "1" ]]; then
    break
  fi
  sleep 2
done

echo "Detected Android SDK level on emulator-5554: $SDK_LEVEL"
if [[ "$SDK_LEVEL" != "27" || "$BOOT_COMPLETED" != "1" ]]; then
  echo "::error::Expected a fully booted Android API 27 emulator; detected SDK=$SDK_LEVEL boot_completed=$BOOT_COMPLETED"
  adb devices -l || true
  adb -s emulator-5554 shell getprop ro.build.version.release || true
  exit 1
fi

# Run the full instrumentation suite on the Android 8.1 target API.
# The API-21-only contract test runs in its dedicated minimum-API step.
exec ./gradlew :app:connectedDebugAndroidTest --no-daemon --stacktrace -Pandroid.testInstrumentationRunnerArguments.notClass=com.veyravault.space.core.LegacyApi21CompatibilityInstrumentationTest
