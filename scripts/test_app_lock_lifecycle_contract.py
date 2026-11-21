from pathlib import Path

root = Path("app/src/main")
policy = (root / "java/com/veyravault/space/security/AppLockPolicy.java").read_text(encoding="utf-8")
deadline = (root / "java/com/veyravault/space/security/AppLockDeadline.java").read_text(encoding="utf-8")
lifecycle = (root / "java/com/veyravault/space/security/AppLockLifecycleController.java").read_text(encoding="utf-8")
application = (root / "java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
process_utils = (root / "java/com/veyravault/space/core/ProcessUtils.java").read_text(encoding="utf-8")
settings = (root / "java/com/veyravault/space/ui/SecuritySettingsActivity.java").read_text(encoding="utf-8")
base = (root / "java/com/veyravault/space/ui/BaseActivity.java").read_text(encoding="utf-8")
test = Path("app/src/androidTest/java/com/veyravault/space/security/AppLockPolicyInstrumentationTest.java").read_text(encoding="utf-8")

# Timeout preferences are a separate namespace and accept only explicit values.
assert 'private static final String PREFS = "veyra_security_policy_prefs"' in policy
assert 'private static final String KEY_BACKGROUND_TIMEOUT_SECONDS = "background_lock_timeout_seconds"' in policy
for marker in (
    "TIMEOUT_IMMEDIATELY = 0",
    "TIMEOUT_30_SECONDS = 30",
    "TIMEOUT_1_MINUTE = 60",
    "TIMEOUT_5_MINUTES = 300",
    "DEFAULT_BACKGROUND_TIMEOUT_SECONDS = TIMEOUT_IMMEDIATELY",
    "isSupportedTimeout",
    ".commit()",
    "catch (ClassCastException malformedPreference)",
):
    assert marker in policy, f"Missing lock policy contract: {marker}"

# The lifecycle callback must be registered only in the main host process.
assert "if (ProcessUtils.isMainProcess(this)) {" in application
assert "AppLockLifecycleController.initialize(this);" in application
assert "context.getPackageName().equals(name)" in process_utils
assert "ProcessUtils.isMainProcess(application)" in lifecycle
assert "registerActivityLifecycleCallbacks(controller)" in lifecycle
assert "Engine.registerCloneProfileLifecycleCallback(this);" in application
assert "CloneStore." not in lifecycle
assert "Engine." not in lifecycle

# Last-Activity lifecycle, cancellable scheduling, and deep-sleep-safe deadline enforcement.
assert "AppLockDeadline.deadlineAfter(" in lifecycle
assert "AppLockDeadline.isExpired(" in lifecycle
assert "AppLockDeadline.remainingMillis(" in lifecycle
assert "AppLockDeadline.timeoutMillis(" in lifecycle
assert "IMMEDIATE_TRANSITION_GRACE_MILLIS = 250L" in deadline
for marker in (
    "implements Application.ActivityLifecycleCallbacks",
    "onActivityStarted(Activity activity)",
    "onActivityStopped(Activity activity)",
    "activity.isChangingConfigurations()",
    "startedActivityCount == 0",
    "mainHandler.postDelayed",
    "mainHandler.removeCallbacks",
    "SystemClock.elapsedRealtime()",
    "IMMEDIATE_LOCK_TRANSITION_GRACE_MILLIS = 250L",
    "SecurityManager.isLockEnabled(appContext)",
    "SecurityManager.lockSession()",
    "AppLockPolicy.getBackgroundTimeoutSeconds(appContext)",
):
    assert marker in lifecycle, f"Missing lifecycle behavior: {marker}"

# Settings exposes the four supported policy values and existing authenticated lock remains in place.
for marker in (
    "AppLockPolicy.TIMEOUT_IMMEDIATELY",
    "AppLockPolicy.TIMEOUT_30_SECONDS",
    "AppLockPolicy.TIMEOUT_1_MINUTE",
    "AppLockPolicy.TIMEOUT_5_MINUTES",
    "AppLockPolicy.setBackgroundTimeoutSeconds",
    "AppLockPolicy.getBackgroundTimeoutSeconds",
):
    assert marker in settings, f"Missing Security Settings UI behavior: {marker}"
assert "SecurityManager.isSessionUnlocked(this)" in base
assert "new Intent(this, SecurityLockActivity.class)" in base

for marker in (
    "missingPreferenceDefaultsToImmediateLock",
    "supportedTimeoutsPersistIndependently",
    "unsupportedTimeoutDoesNotOverwriteSavedValue",
    "unsupportedNumericTimeoutFallsBackToImmediateLock",
    "policyUpdateDoesNotModifyCredentialPreferences",
    "malformedPreferenceFallsBackToImmediateLock",
    "App lock policy preference restoration failed",
):
    assert marker in test, f"Missing app-lock policy instrumentation test: {marker}"

print("PASS: Main-process-only app lock lifecycle, deep-sleep-safe background timeout, separate validated policy preferences, and authenticated lock routing are present.")
