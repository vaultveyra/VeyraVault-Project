package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.SystemClock;

public final class SecurityManager {
    private static final String PREF = "veyra_security_prefs";
    private static final String KEY_MODE = "lock_mode"; // 0=None, 1=PIN, 2=Pattern
    private static final String KEY_HASH = "lock_hash";
    private static final String KEY_FAILED_ATTEMPTS = "lock_failed_attempts";
    private static final String KEY_LOCKOUT_UNTIL = "lockout_until_epoch_millis";
    // Dashboard diagnostics read this flag off the UI thread; volatile guarantees
    // visibility of lock/unlock transitions across the host process threads.
    private static volatile boolean sessionUnlocked = false;

    // Monotonic companion prevents wall-clock changes from shortening OR extending
    // an active cooldown while this process remains alive. Zero means "not loaded yet";
    // -1 means "loaded and there is no active deadline".
    private static volatile int processFailedAttempts = 0;
    private static volatile long processLockoutUntilElapsed =
            AppLockAttemptPolicy.ELAPSED_DEADLINE_UNINITIALIZED;

    public static final int MODE_NONE = 0;
    public static final int MODE_PIN = 1;
    public static final int MODE_PATTERN = 2;

    private SecurityManager() { }

    private static SharedPreferences prefs(Context c) {
        return c.getApplicationContext().getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public static int getLockMode(Context c) {
        return prefs(c).getInt(KEY_MODE, MODE_NONE);
    }

    public static boolean isLockEnabled(Context c) {
        return getLockMode(c) != MODE_NONE && !prefs(c).getString(KEY_HASH, "").isEmpty();
    }

    /** Remaining cooldown in milliseconds; zero means the user may submit a credential. */
    public static synchronized long getCredentialLockoutRemainingMillis(Context c) {
        if (c == null) return 0L;
        SharedPreferences p = prefs(c);
        long nowWall = System.currentTimeMillis();
        long nowElapsed = SystemClock.elapsedRealtime();
        final int storedFailures;
        final long storedDeadline;
        try {
            storedFailures = p.getInt(KEY_FAILED_ATTEMPTS, 0);
            storedDeadline = p.getLong(KEY_LOCKOUT_UNTIL, 0L);
        } catch (ClassCastException malformedAttemptState) {
            return activateCorruptAttemptState(p, nowWall, nowElapsed);
        }

        if (!AppLockAttemptPolicy.isPersistedAttemptStateConsistent(
                storedFailures, storedDeadline)) {
            return activateCorruptAttemptState(p, nowWall, nowElapsed);
        }

        processFailedAttempts = Math.max(processFailedAttempts, storedFailures);
        processLockoutUntilElapsed = AppLockAttemptPolicy.initializeElapsedDeadline(
                processLockoutUntilElapsed, storedDeadline, nowWall, nowElapsed);
        return AppLockAttemptPolicy.remainingMillis(processLockoutUntilElapsed, nowElapsed);
    }

    private static long activateCorruptAttemptState(
            SharedPreferences p, long nowWall, long nowElapsed) {
        long cooldown = AppLockAttemptPolicy.MAX_LOCKOUT_MILLIS;
        long wallDeadline = safeAdd(nowWall, cooldown);
        processFailedAttempts = AppLockAttemptPolicy.MAX_TRACKED_FAILURES;
        processLockoutUntilElapsed = safeAdd(nowElapsed, cooldown);
        // Normalize malformed metadata without touching the credential hash or lock mode.
        p.edit()
                .putInt(KEY_FAILED_ATTEMPTS, processFailedAttempts)
                .putLong(KEY_LOCKOUT_UNTIL, wallDeadline)
                .commit();
        return cooldown;
    }

    private static long safeAdd(long left, long right) {
        if (right > 0L && left > Long.MAX_VALUE - right) return Long.MAX_VALUE;
        return left + right;
    }

    /** Stores the failure count and its matching cooldown as one durable preference update. */
    private static void recordFailedAttempt(SharedPreferences p) {
        final int storedFailures;
        final long storedDeadline;
        try {
            storedFailures = p.getInt(KEY_FAILED_ATTEMPTS, 0);
            storedDeadline = p.getLong(KEY_LOCKOUT_UNTIL, 0L);
        } catch (ClassCastException malformedAttemptState) {
            activateCorruptAttemptState(p, System.currentTimeMillis(),
                    SystemClock.elapsedRealtime());
            return;
        }
        if (!AppLockAttemptPolicy.isPersistedAttemptStateConsistent(
                storedFailures, storedDeadline)) {
            activateCorruptAttemptState(p, System.currentTimeMillis(),
                    SystemClock.elapsedRealtime());
            return;
        }

        int failures = AppLockAttemptPolicy.nextFailureCount(
                Math.max(storedFailures, processFailedAttempts));
        long nowWall = System.currentTimeMillis();
        long nowElapsed = SystemClock.elapsedRealtime();
        long cooldown = AppLockAttemptPolicy.lockoutDurationMillis(failures);
        long deadline = AppLockAttemptPolicy.deadlineMillis(failures, nowWall);
        boolean saved = p.edit()
                .putInt(KEY_FAILED_ATTEMPTS, failures)
                .putLong(KEY_LOCKOUT_UNTIL, deadline)
                .commit();

        processFailedAttempts = failures;
        if (cooldown > 0L) {
            processLockoutUntilElapsed = safeAdd(nowElapsed, cooldown);
        } else if (!saved) {
            // Storage failure must not permit rapid retries within this process.
            processLockoutUntilElapsed = safeAdd(
                    nowElapsed, AppLockAttemptPolicy.FIRST_LOCKOUT_MILLIS);
        } else {
            processLockoutUntilElapsed = AppLockAttemptPolicy.ELAPSED_DEADLINE_NONE;
        }
    }

    private static void clearAttemptState(SharedPreferences.Editor editor) {
        editor.putInt(KEY_FAILED_ATTEMPTS, 0);
        editor.putLong(KEY_LOCKOUT_UNTIL, 0L);
    }

    private static void clearProcessAttemptState() {
        processFailedAttempts = 0;
        processLockoutUntilElapsed = AppLockAttemptPolicy.ELAPSED_DEADLINE_NONE;
    }

    /** Returns false if secure derivation or durable preference storage fails. */
    public static synchronized boolean setLockCredential(Context c, int mode, String rawSecret) {
        if (c == null) return false;
        SharedPreferences p = prefs(c);
        SharedPreferences.Editor editor = p.edit();
        if (mode == MODE_NONE) {
            clearAttemptState(editor);
            boolean saved = editor.putInt(KEY_MODE, MODE_NONE)
                    .putString(KEY_HASH, "").commit();
            if (saved) {
                clearProcessAttemptState();
                sessionUnlocked = true;
            }
            return saved;
        }
        if ((mode != MODE_PIN && mode != MODE_PATTERN)
                || rawSecret == null || rawSecret.isEmpty()) {
            return false;
        }
        try {
            String hash = SecurityCredentialHasher.createHash(
                    rawSecret, Build.VERSION.SDK_INT >= Build.VERSION_CODES.O);
            clearAttemptState(editor);
            boolean saved = editor.putInt(KEY_MODE, mode).putString(KEY_HASH, hash).commit();
            if (saved) {
                clearProcessAttemptState();
                sessionUnlocked = true;
            }
            return saved;
        } catch (Exception cryptoOrStorageFailure) {
            return false;
        }
    }

    public static synchronized boolean verifyCredential(Context c, String rawSecret) {
        if (c == null || rawSecret == null) return false;
        SharedPreferences p = prefs(c);
        if (getCredentialLockoutRemainingMillis(c) > 0L) return false;

        try {
            String stored = p.getString(KEY_HASH, "");
            if (stored.isEmpty()) return false;
            SecurityCredentialHasher.Verification result = SecurityCredentialHasher.verify(
                    rawSecret, stored, Build.VERSION.SDK_INT >= Build.VERSION_CODES.O);
            if (!result.valid) {
                recordFailedAttempt(p);
                return false;
            }

            // Upgrade a legacy hash and clear throttling metadata in one preference commit.
            // As before, a verified unlock is allowed even if the optional upgrade write fails.
            SharedPreferences.Editor editor = p.edit();
            if (result.upgradedHash != null) editor.putString(KEY_HASH, result.upgradedHash);
            clearAttemptState(editor);
            editor.commit();
            clearProcessAttemptState();
            sessionUnlocked = true;
            return true;
        } catch (Exception cryptoFailure) {
            // A crypto/provider failure is not evidence that the user entered a wrong secret.
            return false;
        }
    }

    public static boolean isSessionUnlocked(Context c) {
        return !isLockEnabled(c) || sessionUnlocked;
    }

    public static void lockSession() {
        sessionUnlocked = false;
    }
}
