package com.veyravault.space.security;

/**
 * Deterministic elapsed-realtime deadline math for the host app-lock lifecycle.
 * This class has no Android dependencies so production time logic can be tested
 * directly by JVM and Android instrumentation tests.
 */
public final class AppLockDeadline {
    public static final int TIMEOUT_IMMEDIATELY_SECONDS = 0;
    public static final int TIMEOUT_30_SECONDS = 30;
    public static final int TIMEOUT_1_MINUTE = 60;
    public static final int TIMEOUT_5_MINUTES = 300;
    public static final long IMMEDIATE_TRANSITION_GRACE_MILLIS = 250L;

    private static final long MILLIS_PER_SECOND = 1000L;

    private AppLockDeadline() { }

    /**
     * Converts a supported user timeout into milliseconds. Immediate locking keeps
     * a short transition grace so Activity-to-Activity changes do not cause flicker.
     * Unsupported/corrupt values fail closed to the immediate-lock behavior.
     */
    public static long timeoutMillis(int timeoutSeconds) {
        switch (timeoutSeconds) {
            case TIMEOUT_IMMEDIATELY_SECONDS:
                return IMMEDIATE_TRANSITION_GRACE_MILLIS;
            case TIMEOUT_30_SECONDS:
                return 30L * MILLIS_PER_SECOND;
            case TIMEOUT_1_MINUTE:
                return 60L * MILLIS_PER_SECOND;
            case TIMEOUT_5_MINUTES:
                return 300L * MILLIS_PER_SECOND;
            default:
                return IMMEDIATE_TRANSITION_GRACE_MILLIS;
        }
    }

    /** Creates a monotonic deadline, saturating instead of overflowing. */
    public static long deadlineAfter(long nowElapsedRealtime, int timeoutSeconds) {
        requireNonNegative(nowElapsedRealtime);
        long duration = timeoutMillis(timeoutSeconds);
        return nowElapsedRealtime > Long.MAX_VALUE - duration
                ? Long.MAX_VALUE : nowElapsedRealtime + duration;
    }

    /** A missing deadline is never expired; equality means the deadline has elapsed. */
    public static boolean isExpired(long deadlineElapsedRealtime, long nowElapsedRealtime) {
        requireNonNegative(nowElapsedRealtime);
        return deadlineElapsedRealtime >= 0L && nowElapsedRealtime >= deadlineElapsedRealtime;
    }

    /**
     * Returns -1 when no deadline exists, 0 when expired, or the positive time left.
     */
    public static long remainingMillis(long deadlineElapsedRealtime, long nowElapsedRealtime) {
        requireNonNegative(nowElapsedRealtime);
        if (deadlineElapsedRealtime < 0L) return -1L;
        if (nowElapsedRealtime >= deadlineElapsedRealtime) return 0L;
        return deadlineElapsedRealtime - nowElapsedRealtime;
    }

    private static void requireNonNegative(long elapsedRealtime) {
        if (elapsedRealtime < 0L) {
            throw new IllegalArgumentException("Elapsed realtime must be non-negative");
        }
    }
}
