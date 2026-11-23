#!/usr/bin/env python3
"""Source contract for local PIN/Pattern attempt throttling."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
security = (ROOT / "app/src/main/java/com/veyravault/space/security/SecurityManager.java").read_text(encoding="utf-8")
policy = (ROOT / "app/src/main/java/com/veyravault/space/security/AppLockAttemptPolicy.java").read_text(encoding="utf-8")
activity = (ROOT / "app/src/main/java/com/veyravault/space/ui/SecurityLockActivity.java").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")
tests = (ROOT / "scripts/test_security_credentials.py").read_text(encoding="utf-8")


def method_body(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError("Unclosed method: " + signature)


verify = method_body(security, "public static synchronized boolean verifyCredential(")
assert verify.index("getCredentialLockoutRemainingMillis(c)") < verify.index("SecurityCredentialHasher.verify")
assert "recordFailedAttempt(c, p)" in verify
assert "clearAttemptState(editor)" in verify
assert "cryptoFailure" in verify

set_credential = method_body(security, "public static synchronized boolean setLockCredential(")
assert set_credential.count("clearAttemptState(editor)") >= 2
assert "if (saved)" in set_credential

remaining = method_body(security, "public static synchronized long getCredentialLockoutRemainingMillis(")
assert "System.currentTimeMillis()" in remaining
assert "SystemClock.elapsedRealtime()" in remaining
assert "processLockoutUntilElapsed" in security
assert "KEY_FAILED_ATTEMPTS" in security
assert "KEY_LOCKOUT_UNTIL" in security
assert "commit()" in security

assert "UNTHROTTLED_FAILURES = 4" in policy
assert "FIRST_LOCKOUT_MILLIS = 30_000L" in policy
assert "SECOND_LOCKOUT_MILLIS = 60_000L" in policy
assert "THIRD_LOCKOUT_MILLIS = 5L * 60_000L" in policy
assert "MAX_LOCKOUT_MILLIS = 15L * 60_000L" in policy
assert "MAX_TRACKED_FAILURES" in policy

assert "showCredentialFailure(fa)" in activity
assert "Too many incorrect attempts. Try again in " in activity
assert "ثانیه دیگر دوباره امتحان کنید" in activity
assert "pinInput.setText(\"\")" in activity
assert "Test app-lock attempt-throttling contract" in workflow
assert "scripts/test_app_lock_attempt_throttling_contract.py" in workflow
assert "AppLockAttemptPolicy.java" in tests
assert "AppLockAttemptPolicyTest" in tests

instrumentation = (
    ROOT / "app/src/androidTest/java/com/veyravault/space/security/"
    "AppLockAttemptThrottlingInstrumentationTest.java"
).read_text(encoding="utf-8")
assert "fifthIncorrectCredentialStartsCooldownAndCorrectCredentialResetsIt" in instrumentation
assert "A correct PIN must not bypass an active cooldown" in instrumentation
assert "Credential preference map must be restored exactly" in instrumentation
assert "CloneStore" not in instrumentation
assert "restorePreferences(preferences, originalPreferences)" in instrumentation

print("App lock attempt throttling: lockout check precedes credential derivation: PASS")
print("App lock attempt throttling: failure persistence and success/reset paths are wired: PASS")
print("App lock attempt throttling: monotonic in-process companion and wall-clock persistence are present: PASS")
print("App lock attempt throttling: Persian/English cooldown feedback is wired: PASS")
