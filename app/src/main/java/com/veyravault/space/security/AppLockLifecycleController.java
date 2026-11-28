package com.veyravault.space.security;

import android.app.Activity;
import android.app.Application;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import com.veyravault.space.core.ProcessUtils;

/** Locks only the host application's main process after its last Activity leaves the foreground. */
public final class AppLockLifecycleController implements Application.ActivityLifecycleCallbacks {
    private static volatile AppLockLifecycleController instance;
    private final Context appContext;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final AppLockLifecycleState lifecycleState = new AppLockLifecycleState();
    private Runnable pendingLockTask;

    private AppLockLifecycleController(Application application) {
        appContext = application.getApplicationContext();
    }

    public static synchronized boolean initialize(Application application) {
        if (application == null || !ProcessUtils.isMainProcess(application)) return false;
        if (instance != null) return true;
        AppLockLifecycleController controller = new AppLockLifecycleController(application);
        application.registerActivityLifecycleCallbacks(controller);
        instance = controller;
        return true;
    }

    @Override public void onActivityStarted(Activity activity) {
        boolean shouldLock = lifecycleState.onActivityStarted(
                SystemClock.elapsedRealtime(), SecurityManager.isLockEnabled(appContext));
        if (shouldLock) SecurityManager.lockSession();
        cancelPendingLock();
    }

    @Override public void onActivityStopped(Activity activity) {
        if (!lifecycleState.onActivityStopped()) return;
        if (activity != null && activity.isChangingConfigurations()) {
            cancelPendingLock();
            lifecycleState.clearBackgroundDeadline();
        } else {
            scheduleBackgroundLock();
        }
    }

    private void scheduleBackgroundLock() {
        cancelPendingLock();
        if (!SecurityManager.isLockEnabled(appContext)) {
            lifecycleState.clearBackgroundDeadline();
            return;
        }
        int configuredTimeoutSeconds = AppLockPolicy.getBackgroundTimeoutSeconds(appContext);
        long timeoutMillis = AppLockDeadline.timeoutMillis(configuredTimeoutSeconds);
        lifecycleState.beginBackgroundDeadline(SystemClock.elapsedRealtime(), configuredTimeoutSeconds, true);
        pendingLockTask = new Runnable() {
            @Override public void run() {
                pendingLockTask = null;
                if (lifecycleState.hasStartedActivities()
                        || lifecycleState.getBackgroundDeadlineElapsedRealtime() < 0L) return;
                long remaining = AppLockDeadline.remainingMillis(
                        lifecycleState.getBackgroundDeadlineElapsedRealtime(), SystemClock.elapsedRealtime());
                if (remaining < 0L) return;
                if (remaining > 0L) {
                    pendingLockTask = this;
                    mainHandler.postDelayed(this, remaining);
                    return;
                }
                if (SecurityManager.isLockEnabled(appContext)) SecurityManager.lockSession();
                lifecycleState.clearBackgroundDeadline();
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
