package com.veyravault.space.core;

import android.content.Context;
import android.util.Log;

import top.niunaijun.blackbox.app.configuration.AppLifecycleCallback;

/**
 * Runs inside each BlackBox virtual package/user process before the target Application
 * is created. Profile data is read-only here; all writes remain in the host repository.
 */
public final class CloneProfileLifecycleCallback extends AppLifecycleCallback {
    private static final String TAG = "VeyraCloneProfile";
    private final Context appContext;

    public CloneProfileLifecycleCallback(Context context) {
        Context application = context == null ? null : context.getApplicationContext();
        this.appContext = application == null ? context : application;
    }

    @Override
    public void beforeCreateApplication(String packageName, String processName,
                                        Context packageContext, int userId) {
        if (appContext == null || packageContext == null
                || packageName == null || packageName.trim().isEmpty()
                || packageName.equals(appContext.getPackageName()) || userId < 0) {
            return;
        }
        try {
            // Reset process-wide defaults first so a prior clone cannot leak locale/time-zone.
            ProfileRuntimeApplier.restoreSystemDefaults(packageContext);
            ProfileResolver.ResolvedProfile resolved =
                    ProfileRuntimeClient.resolve(appContext, packageName, userId);
            ProfileRuntimeApplier.apply(packageContext, resolved);
            Log.i(TAG, "Applied clone locale/time-zone profile before Application creation: "
                    + packageName + "#" + userId
                    + " localeSource=" + resolved.localeSource
                    + " timeZoneSource=" + resolved.timeZoneSource);
        } catch (Exception error) {
            // A malformed profile must not crash the target app or be silently rewritten.
            ProfileRuntimeApplier.restoreSystemDefaults(packageContext);
            Log.w(TAG, "Clone profile could not be resolved; system process defaults retained for "
                    + packageName + "#" + userId, error);
        }
    }
}
