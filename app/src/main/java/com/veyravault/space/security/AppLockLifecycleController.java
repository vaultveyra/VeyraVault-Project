package com.veyravault.space.security;

import android.app.Activity;
import android.app.Application;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;

import com.veyravault.space.core.ProcessUtils;

/**
 * Locks only the host application's main process after its last Activity leaves
 * the foreground. It is deliberately not registered in BlackBox clone processes.
 */
public final class AppLockLifecycleController implements Application.ActivityLifecycleCallbacks {
    private static volatile AppLockLifecycleController instance;

    private final Context appContext;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private int startedActivityCount;
    private long backgroundDeadlineElapsedRealtime = -1L;
    private Runnable pendingLockTask;

    private AppLockLifecycleController(Application application) {
        appContext = application.getApplicationContext();
    }

    /**
     * Must be called by VaultApp. The exact process-name check is repeated here
     * so a future caller cannot accidentally install this controller in a clone.
     */
    public static synchronized boolean initialize(Application application) {
        if (application == null || !ProcessUtils.isMainProcess(application)) return false;
        if (instance != null) return true;

        AppLockLifecycleController controller = new AppLockLifecycleController(application);
        application.registerActivityLifecycleCallbacks(controller);
        instance = controller;
        return true;
    }

    @Override
    public void onActivityStarted(Activity activity) {
        if (startedActivityCount == 0) {
            // Handler delays use uptime; elapsedRealtime also includes deep sleep.
            // Enforce an expired deadline before BaseActivity.onResume decides whether
            // the existing authenticated lock screen must be shown.
            if (AppLockDeadline.isExpired(backgroundDeadlineElapsedRealtime,
                    SystemClock.elapsedRealtime())
                    && SecurityManager.isLockEnabled(appContext)) {
                SecurityManager.lockSession();
            }
            cancelPendingLock();
            backgroundDeadlineElapsedRealtime = -1L;
        }
        startedActivityCount++;
    }

    @Override
    public void onActivityStopped(Activity activity) {
        if (startedActivityCount > 0) startedActivityCount--;
        if (startedActivityCount == 0) {
            if (activity != null && activity.isChangingConfigurations()) {
                // Rotation, locale/theme recreation, and other configuration changes
                // are not genuine exits from the app.
                cancelPendingLock();
                backgroundDeadlineElapsedRealtime = -1L;
            } else {
                scheduleBackgroundLock();
            }
        }
    }

    private void scheduleBackgroundLock() {
        cancelPendingLock();
        if (!SecurityManager.isLockEnabled(appContext)) {
            backgroundDeadlineElapsedRealtime = -1L;
            return;
        }

        int configuredTimeoutSeconds = AppLockPolicy.getBackgroundTimeoutSeconds(appContext);
        // A tiny main-loop grace for the immediate option avoids treating an
        // Activity-to-Activity transition as an app exit.
        long timeoutMillis = AppLockDeadline.timeoutMillis(configuredTimeoutSeconds);
        backgroundDeadlineElapsedRealtime = AppLockDeadline.deadlineAfter(
                SystemClock.elapsedRealtime(), configuredTimeoutSeconds);
        pendingLockTask = new Runnable() {
            @Override
            public void run() {
                pendingLockTask = null;
                if (startedActivityCount != 0 || backgroundDeadlineElapsedRealtime < 0L) return;

                long remaining = AppLockDeadline.remainingMillis(
                        backgroundDeadlineElapsedRealtime, SystemClock.elapsedRealtime());
                if (remaining < 0L) return;
                if (remaining > 0L) {
                    pendingLockTask = this;
                    mainHandler.postDelayed(this, remaining);
                    return;
                }

                if (SecurityManager.isLockEnabled(appContext)) {
                    SecurityManager.lockSession();
                }
                backgroundDeadlineElapsedRealtime = -1L;
            }
        };

        mainHandler.postDelayed(pendingLockTask, timeoutMillis);
    }

    private void cancelPendingLock() {
        if (pendingLockTask != null) {
            mainHandler.removeCallbacks(pendingLockTask);
            pendingLockTask = null;
        }
    }

    @Override public void onActivityCreated(Activity activity, android.os.Bundle state) { }
    @Override public void onActivityResumed(Activity activity) { }
    @Override public void onActivityPaused(Activity activity) { }
    @Override public void onActivitySaveInstanceState(Activity activity, android.os.Bundle state) { }
    @Override public void onActivityDestroyed(Activity activity) { }
}
