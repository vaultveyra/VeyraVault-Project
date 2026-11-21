package com.veyravault.space.security;

/** Deterministic Activity foreground/background state for the host app lock. */
public final class AppLockLifecycleState {
    private int startedActivityCount;
    private long backgroundDeadlineElapsedRealtime = -1L;

    public boolean onActivityStarted(long nowElapsedRealtime, boolean lockEnabled) {
        if (nowElapsedRealtime < 0L) throw new IllegalArgumentException("Elapsed realtime must be non-negative");
        boolean shouldLock = false;
        if (startedActivityCount == 0) {
            shouldLock = lockEnabled && AppLockDeadline.isExpired(backgroundDeadlineElapsedRealtime, nowElapsedRealtime);
            backgroundDeadlineElapsedRealtime = -1L;
        }
        if (startedActivityCount == Integer.MAX_VALUE) throw new IllegalStateException("Started Activity count overflow");
        startedActivityCount++;
        return shouldLock;
    }

    public boolean onActivityStopped() {
        if (startedActivityCount > 0) startedActivityCount--;
        return startedActivityCount == 0;
    }

    public long beginBackgroundDeadline(long nowElapsedRealtime, int timeoutSeconds, boolean lockEnabled) {
        if (!lockEnabled) {
            clearBackgroundDeadline();
            return -1L;
        }
        backgroundDeadlineElapsedRealtime = AppLockDeadline.deadlineAfter(nowElapsedRealtime, timeoutSeconds);
        return backgroundDeadlineElapsedRealtime;
    }

    public void clearBackgroundDeadline() { backgroundDeadlineElapsedRealtime = -1L; }
    public long getBackgroundDeadlineElapsedRealtime() { return backgroundDeadlineElapsedRealtime; }
    public int getStartedActivityCount() { return startedActivityCount; }
    public boolean hasStartedActivities() { return startedActivityCount > 0; }
}
