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
        if (nowMillis > Long.MAX_VALUE - duration) return Long.MAX_VALUE;
        return nowMillis + duration;
    }

    public static long remainingMillis(long deadlineMillis, long nowMillis) {
        if (deadlineMillis <= 0L || deadlineMillis <= nowMillis) return 0L;
        return deadlineMillis - nowMillis;
    }
}
