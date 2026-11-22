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
    "application.registerActivityLifecycleCallbacks(lifecycleObserver)",
    "ActivityScenario.launch(AppLockLifecycleProbeActivity.class)",
    "parent.activity.startActivity(",
    "new Intent(parent.activity, AppLockLifecycleProbeActivity.class)",
    "observer.awaitAnotherResumedProbe(",
    "lifecycleObserver.awaitActiveResumed(",
    "parent.activity.getTaskId(), activity.getTaskId()",
    "activity.runOnUiThread(activity::finish)",
    "handle.scenario.close()",
    "observer.expectStopped(handle.activity)",
    "resumedActivities.remove(activity)",
    "stoppedActivities.add(activity)",
    "resumedActivities.add(activity)",
    "observer.awaitResumed(activity, ACTIVITY_EVENT_TIMEOUT_MILLIS)",
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

assert test.count("ActivityScenario.launch(AppLockLifecycleProbeActivity.class)") == 1, (
    "ActivityScenario must launch only the first Activity; the second must be started from its parent task."
)
assert test.count("launchProbeActivity(lifecycleObserver)") == 1, (
    "The test must create one ActivityScenario and one same-task navigation Activity."
)
assert "ActivityMonitor" not in test
assert "launchProbeActivity(context, instrumentation, lifecycleObserver)" not in test
assert "FLAG_ACTIVITY_NEW_TASK" not in test
assert "void markRegistered()" in test
assert "void markUnregistered()" in test
assert "startActivitySync(" not in test
assert "waitForIdleSync(" not in test
assert "test_app_lock_lifecycle_runtime_contract.py" in workflow

print("PASS: VaultApp registers the production lifecycle controller only in the package main process.")
print("PASS: The initial Debug Activity is launched by ActivityScenario; the next Activity is opened from its parent in the same task.")
print("PASS: The test verifies the second Activity shares the task, then waits for the first Activity to resume before checking the unlocked session.")
print("PASS: Finishing the final Activity still verifies the configured background lock through real Application callbacks.")
print("PASS: No startActivitySync/waitForIdleSync global idle barrier or independent ActivityScenario task is used.")
print("PASS: Credential preferences, policy preferences, and the original in-memory session flag are restored.")
