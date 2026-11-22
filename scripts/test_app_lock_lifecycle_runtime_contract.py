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

for marker in (
    "AppLockLifecycleController.initialize(application)",
    "InstrumentationRegistry.getInstrumentation()",
    "application.registerActivityLifecycleCallbacks(lifecycleObserver)",
    "context.startActivity(intent)",
    "instrumentation.addMonitor(",
    "monitor.waitForActivityWithTimeout(ACTIVITY_EVENT_TIMEOUT_MILLIS)",
    "instrumentation.removeMonitor(monitor)",
    "observer.expectStopped(activity)",
    "CountDownLatch existing = resumeWaiters.putIfAbsent(activity, latch)",
    "stoppedActivities.add(activity)",
    "resumedActivities.add(activity)",
    "observer.awaitResumed(activity, ACTIVITY_EVENT_TIMEOUT_MILLIS)",
    "instrumentation.runOnMainSync",
    "finishProbeActivity(secondActivity, instrumentation, lifecycleObserver)",
    "finishProbeActivity(firstActivity, instrumentation, lifecycleObserver)",
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

assert "awaitStartedActivity(" not in test, "Activity launch detection must not depend on the observer callback queue."
assert "void markRegistered()" in test, "Lifecycle observer registration state must be explicitly recorded after registration."
assert "void markUnregistered()" in test, "Lifecycle observer unregistration state must be explicitly recorded after unregistration."
assert "startActivitySync(" not in test, "Do not introduce a global main-loop idle barrier in lifecycle instrumentation."
assert "waitForIdleSync(" not in test, "Lifecycle instrumentation must use callback signals rather than global idle waits."
assert "test_app_lock_lifecycle_runtime_contract.py" in workflow
print("PASS: VaultApp registers the production lifecycle controller only in the package main process.")
print("PASS: Debug-only Activity is launched by Context.startActivity and observed through real Application callbacks.")
print("PASS: The test verifies no premature lock during Activity transition and lock after the final Activity stops.")
print("PASS: No startActivitySync/waitForIdleSync global idle barrier is used.")
print("PASS: Credential preferences, policy preferences, and the original in-memory session flag are restored.")
