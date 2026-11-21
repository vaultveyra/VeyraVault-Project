from pathlib import Path
root = Path("app/src/main")
policy = (root / "java/com/veyravault/space/security/AppLockPolicy.java").read_text(encoding="utf-8")
deadline = (root / "java/com/veyravault/space/security/AppLockDeadline.java").read_text(encoding="utf-8")
state = (root / "java/com/veyravault/space/security/AppLockLifecycleState.java").read_text(encoding="utf-8")
lifecycle = (root / "java/com/veyravault/space/security/AppLockLifecycleController.java").read_text(encoding="utf-8")
application = (root / "java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
process_utils = (root / "java/com/veyravault/space/core/ProcessUtils.java").read_text(encoding="utf-8")
settings = (root / "java/com/veyravault/space/ui/SecuritySettingsActivity.java").read_text(encoding="utf-8")
base = (root / "java/com/veyravault/space/ui/BaseActivity.java").read_text(encoding="utf-8")
test = Path("app/src/androidTest/java/com/veyravault/space/security/AppLockPolicyInstrumentationTest.java").read_text(encoding="utf-8")

for marker in (
    'private static final String PREFS = "veyra_security_policy_prefs"',
    'private static final String KEY_BACKGROUND_TIMEOUT_SECONDS = "background_lock_timeout_seconds"',
    "TIMEOUT_IMMEDIATELY = AppLockDeadline.TIMEOUT_IMMEDIATELY_SECONDS",
    "TIMEOUT_30_SECONDS = AppLockDeadline.TIMEOUT_30_SECONDS",
    "TIMEOUT_1_MINUTE = AppLockDeadline.TIMEOUT_1_MINUTE",
    "TIMEOUT_5_MINUTES = AppLockDeadline.TIMEOUT_5_MINUTES",
    "DEFAULT_BACKGROUND_TIMEOUT_SECONDS = TIMEOUT_IMMEDIATELY",
    "isSupportedTimeout", ".commit()", "catch (ClassCastException malformedPreference)",
):
    assert marker in policy, f"Missing lock policy contract: {marker}"

for marker in ("TIMEOUT_IMMEDIATELY_SECONDS = 0", "TIMEOUT_30_SECONDS = 30",
               "TIMEOUT_1_MINUTE = 60", "TIMEOUT_5_MINUTES = 300",
               "IMMEDIATE_TRANSITION_GRACE_MILLIS = 250L"):
    assert marker in deadline, f"Missing canonical deadline constant: {marker}"

assert "if (ProcessUtils.isMainProcess(this)) {" in application
assert "AppLockLifecycleController.initialize(this);" in application
assert "context.getPackageName().equals(name)" in process_utils
assert "ProcessUtils.isMainProcess(application)" in lifecycle
assert "registerActivityLifecycleCallbacks(controller)" in lifecycle
assert "Engine.registerCloneProfileLifecycleCallback(this);" in application
assert "CloneStore." not in lifecycle and "Engine." not in lifecycle

for marker in (
    "lifecycleState.onActivityStarted(", "lifecycleState.onActivityStopped()",
    "lifecycleState.beginBackgroundDeadline(", "lifecycleState.clearBackgroundDeadline()",
    "lifecycleState.getBackgroundDeadlineElapsedRealtime()", "lifecycleState.hasStartedActivities()",
    "AppLockDeadline.remainingMillis(", "AppLockDeadline.timeoutMillis(",
    "activity.isChangingConfigurations()", "mainHandler.postDelayed", "mainHandler.removeCallbacks",
    "SystemClock.elapsedRealtime()", "SecurityManager.isLockEnabled(appContext)",
    "SecurityManager.lockSession()", "AppLockPolicy.getBackgroundTimeoutSeconds(appContext)",
):
    assert marker in lifecycle, f"Missing lifecycle controller behavior: {marker}"

for marker in ("onActivityStarted(long nowElapsedRealtime, boolean lockEnabled)", "onActivityStopped()",
               "beginBackgroundDeadline(long nowElapsedRealtime, int timeoutSeconds,",
               "clearBackgroundDeadline()", "getBackgroundDeadlineElapsedRealtime()",
               "getStartedActivityCount()", "hasStartedActivities()", "AppLockDeadline.isExpired("):
    assert marker in state, f"Missing deterministic lifecycle state behavior: {marker}"

for marker in ("AppLockPolicy.TIMEOUT_IMMEDIATELY", "AppLockPolicy.TIMEOUT_30_SECONDS",
               "AppLockPolicy.TIMEOUT_1_MINUTE", "AppLockPolicy.TIMEOUT_5_MINUTES",
               "AppLockPolicy.setBackgroundTimeoutSeconds", "AppLockPolicy.getBackgroundTimeoutSeconds"):
    assert marker in settings, f"Missing Security Settings UI behavior: {marker}"
assert "SecurityManager.isSessionUnlocked(this)" in base
assert "new Intent(this, SecurityLockActivity.class)" in base
for marker in ("missingPreferenceDefaultsToImmediateLock", "supportedTimeoutsPersistIndependently",
               "unsupportedTimeoutDoesNotOverwriteSavedValue", "unsupportedNumericTimeoutFallsBackToImmediateLock",
               "policyUpdateDoesNotModifyCredentialPreferences", "malformedPreferenceFallsBackToImmediateLock",
               "App lock policy preference restoration failed"):
    assert marker in test, f"Missing app-lock policy instrumentation test: {marker}"
print("PASS: Main-process-only app-lock lifecycle, deterministic Activity state, deep-sleep-safe deadlines, separate validated policy preferences, and authenticated lock routing are present.")
