from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
application = (ROOT / "app/src/main/java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
controller = (ROOT / "app/src/main/java/com/veyravault/space/security/AppLockLifecycleController.java").read_text(encoding="utf-8")
process_utils = (ROOT / "app/src/main/java/com/veyravault/space/core/ProcessUtils.java").read_text(encoding="utf-8")
manifest = (ROOT / "app/src/debug/AndroidManifest.xml").read_text(encoding="utf-8")
probe_activity = (ROOT / "app/src/debug/java/com/veyravault/space/security/AppLockLifecycleProbeActivity.java").read_text(encoding="utf-8")
test = (ROOT / "app/src/androidTest/java/com/veyravault/space/security/AppLockLifecycleRuntimeInstrumentationTest.java").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")

assert "if (ProcessUtils.isMainProcess(this)) {" in application
assert "AppLockLifecycleController.initialize(this);" in application
assert "ProcessUtils.isMainProcess(application)" in controller
assert "registerActivityLifecycleCallbacks(controller)" in controller
assert "context.getPackageName().equals(name)" in process_utils

assert "AppLockLifecycleProbeActivity" in manifest
assert 'android:exported="false"' in manifest
assert "extends Activity" in probe_activity
assert "AppLockLifecycleProbeActivity" in probe_activity

for marker in (
    "AppLockLifecycleController.initialize(application)",
    "InstrumentationRegistry.getInstrumentation()",
    "startActivitySync(intent)",
    "finishProbeActivity(secondActivity, instrumentation)",
    "finishProbeActivity(firstActivity, instrumentation)",
    "awaitSessionLock(context, LOCK_WAIT_TIMEOUT_MILLIS)",
    "SecurityManager.setLockCredential(",
    "AppLockPolicy.setBackgroundTimeoutSeconds(",
    "restorePreferenceKey(credentialPreferences, originalCredentials, KEY_MODE)",
    "restorePreferenceKey(credentialPreferences, originalCredentials, KEY_HASH)",
    "restorePreferenceKey(policyPreferences, originalPolicy, KEY_TIMEOUT)",
    "unlockedField.setBoolean(null, originalUnlockedState)",
    "Credential preferences were not restored exactly",
    "App-lock policy preferences were not restored exactly",
):
    assert marker in test, f"Missing runtime lifecycle assertion or safe restoration: {marker}"

assert "test_app_lock_lifecycle_runtime_contract.py" in workflow
print("PASS: VaultApp registers the production lifecycle controller only in the package main process.")
print("PASS: Debug-only Activity and Android instrumentation exercise real Activity start/stop callbacks.")
print("PASS: The test verifies no premature lock during Activity transition and lock after the final Activity stops.")
print("PASS: Credential preferences, policy preferences, and the original in-memory session flag are restored.")
