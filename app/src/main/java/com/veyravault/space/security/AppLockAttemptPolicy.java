package com.veyravault.space.security;

/**
 * Deterministic, bounded backoff policy for local PIN/Pattern verification.
 *
 * The policy never permanently locks the user out. A correct credential clears
 * the counter; repeated incorrect attempts reach a maximum 15-minute delay.
 */
public final class AppLockAttemptPolicy {
    public static final int MAX_TRACKED_FAILURES = 1_000_000;
    public static final int UNTHROTTLED_FAILURES = 4;
    public static final long FIRST_LOCKOUT_MILLIS = 30_000L;
    public static final long SECOND_LOCKOUT_MILLIS = 60_000L;
    public static final long THIRD_LOCKOUT_MILLIS = 5L * 60_000L;
    public static final long MAX_LOCKOUT_MILLIS = 15L * 60_000L;

    // The process-local elapsed deadline is reconstructed from wall time exactly once.
    // Zero means it has not yet been initialized; -1 means no active deadline.
    public static final long ELAPSED_DEADLINE_UNINITIALIZED = 0L;
    public static final long ELAPSED_DEADLINE_NONE = -1L;

    private AppLockAttemptPolicy() { }

    public static int nextFailureCount(int currentFailures) {
        if (currentFailures < 0) return MAX_TRACKED_FAILURES;
        if (currentFailures >= MAX_TRACKED_FAILURES) return MAX_TRACKED_FAILURES;
        return currentFailures + 1;
    }

    public static long lockoutDurationMillis(int failureCount) {
        if (failureCount <= UNTHROTTLED_FAILURES) return 0L;
        if (failureCount == 5) return FIRST_LOCKOUT_MILLIS;
        if (failureCount == 6) return SECOND_LOCKOUT_MILLIS;
        if (failureCount == 7) return THIRD_LOCKOUT_MILLIS;
        return MAX_LOCKOUT_MILLIS;
    }

    public static long deadlineMillis(int failureCount, long nowMillis) {
        long duration = lockoutDurationMillis(failureCount);
        if (duration == 0L) return 0L;
        return safeAdd(nowMillis, duration);
    }

    public static long remainingMillis(long deadlineMillis, long nowMillis) {
        if (deadlineMillis <= 0L || deadlineMillis <= nowMillis) return 0L;
        return deadlineMillis - nowMillis;
    }

    /** A persisted wall-clock deadline can reconstruct at most the policy's maximum delay. */
    public static long boundedRemainingMillis(long deadlineMillis, long nowMillis) {
        return Math.min(MAX_LOCKOUT_MILLIS, remainingMillis(deadlineMillis, nowMillis));
    }

    /**
     * Reconstructs the monotonic deadline once after process creation.
     *
     * Subsequent calls preserve the existing elapsed deadline and never re-read wall time,
     * so a backwards wall-clock adjustment cannot continually restart the cooldown.
     */
    public static long initializeElapsedDeadline(
            long currentElapsedDeadline,
            long persistedWallDeadline,
            long nowWallMillis,
            long nowElapsedMillis) {
        if (currentElapsedDeadline != ELAPSED_DEADLINE_UNINITIALIZED) {
            return currentElapsedDeadline;
        }
        long remaining = boundedRemainingMillis(persistedWallDeadline, nowWallMillis);
        if (remaining == 0L) return ELAPSED_DEADLINE_NONE;
        return safeAdd(nowElapsedMillis, remaining);
    }

    /** Detects impossible pairs so malformed attempt metadata fails closed. */
    public static boolean isPersistedAttemptStateConsistent(
            int failureCount, long wallDeadlineMillis) {
        if (failureCount < 0 || failureCount > MAX_TRACKED_FAILURES
                || wallDeadlineMillis < 0L) {
            return false;
        }
        if (failureCount <= UNTHROTTLED_FAILURES) return wallDeadlineMillis == 0L;
        return wallDeadlineMillis > 0L;
    }

    private static long safeAdd(long left, long right) {
        if (right > 0L && left > Long.MAX_VALUE - right) return Long.MAX_VALUE;
        return left + right;
    }
}
