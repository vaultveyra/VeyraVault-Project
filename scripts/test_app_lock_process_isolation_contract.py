#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = (ROOT / "app/src/debug/AndroidManifest.xml").read_text(encoding="utf-8")
production_manifest = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
service = (ROOT / "app/src/debug/java/com/veyravault/space/security/AppLockSessionProbeService.java").read_text(encoding="utf-8")
test = (ROOT / "app/src/androidTest/java/com/veyravault/space/security/AppLockProcessIsolationInstrumentationTest.java").read_text(encoding="utf-8")
security = (ROOT / "app/src/main/java/com/veyravault/space/security/SecurityManager.java").read_text(encoding="utf-8")
prepare = (ROOT / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")

for marker in (
    "AppLockSessionProbeService",
    'android:process=":app_lock_session_probe"',
    'android:exported="false"',
):
    assert marker in manifest, f"Missing debug-only isolated-process manifest wiring: {marker}"

assert "AppLockSessionProbeService" not in production_manifest, (
    "The app-lock process probe must never enter the production manifest"
)
assert "android.app.Service" in service
assert "MSG_QUERY_SESSION_STATE" in service
assert "SecurityManager.isSessionUnlocked(getApplicationContext())" in service
assert "MSG_SESSION_STATE_RESULT" in service

for marker in (
    "freshAndroidProcessDoesNotInheritUnlockedHostSession",
    "SecurityManager.setLockCredential(context, SecurityManager.MODE_PIN, \"4286\")",
    "SecurityManager.isSessionUnlocked(context)",
    "context.bindService(intent, connection, Context.BIND_AUTO_CREATE)",
    "Boolean.FALSE",
    "CountDownLatch",
    "TimeUnit.SECONDS",
    "restoreCredentialPreferences(preferences, originalPreferences)",
    "unlockedField.setBoolean(null, originalUnlockedState)",
    "assertEquals(\"Credential preference values changed during the test\"",
):
    assert marker in test, f"Missing process-isolation assertion or safe cleanup: {marker}"

for marker in (
    "private static volatile boolean sessionUnlocked = false",
    "public static boolean isSessionUnlocked(Context c)",
    "return !isLockEnabled(c) || sessionUnlocked",
):
    assert marker in security, f"SecurityManager fail-closed session contract changed: {marker}"

assert 'testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"' in prepare
assert "androidx.test:runner:1.5.2" in prepare
assert "androidx.test:core:1.5.0" in prepare
assert "androidx.test.ext:junit:1.1.5" in prepare
assert "connectedDebugAndroidTest" in workflow
assert "test_app_lock_process_isolation_contract.py" in workflow

print("PASS: App-lock session probe is registered only in the Debug manifest and uses a separate Android process.")
print("PASS: Instrumentation verifies a fresh process starts locked and restores credential preferences and in-process state.")
print("PASS: CI runs the wiring contract and Android instrumentation suite.")
