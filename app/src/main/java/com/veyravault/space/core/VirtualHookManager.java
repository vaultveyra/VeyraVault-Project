package com.veyravault.space.core;

import android.content.Context;
import java.lang.reflect.Method;

/**
 * Applies clone settings through the pinned virtualization engine's package/user-scoped APIs.
 *
 * Host-process Build and LocationManager overrides are intentionally not used here:
 * BlackBox launches virtual apps in separate host:pN processes, so host statics are not
 * a per-clone configuration channel and can unexpectedly affect the host application.
 */
public class VirtualHookManager {

    public static void installProcessHooks(Context ctx) {
        try {
            CloneStore.CloneEntry last = CloneStore.getLastActiveLaunch(ctx);
            if (last != null) {
                syncCloneHooks(ctx, last);
            }
        } catch (Throwable ignored) {}
    }

    public static void syncCloneHooks(Context ctx, CloneStore.CloneEntry entry) {
        if (entry == null) return;
        boolean masterGps = CloneStore.isMasterMockGpsEnabled(ctx);
        boolean gpsOn = masterGps && entry.mockGpsEnabled;
        applyEngineLocationHook(entry.packageName, entry.userId, gpsOn, entry.latitude, entry.longitude);
    }

    public static void applyEngineLocationHook(String pkg, int userId, boolean enable, double lat, double lng) {
        String[] mgrClasses = {
            "top.niunaijun.blackbox.fake.frameworks.BLocationManager",
            "com.vcore.fake.frameworks.BLocationManager"
        };
        String[] locClasses = {
            "top.niunaijun.blackbox.entity.location.BLocation",
            "com.vcore.entity.location.BLocation"
        };
        for (int i = 0; i < mgrClasses.length; i++) {
            try {
                Class<?> mgrCls = Class.forName(mgrClasses[i]);
                Object mgr = mgrCls.getMethod("get").invoke(null);
                for (Method m : mgrCls.getMethods()) {
                    if (m.getName().equals("setPattern") && m.getParameterTypes().length == 3) {
                        m.invoke(mgr, userId, pkg, enable ? 2 : 0);
                    }
                }
                if (enable) {
                    Class<?> bLocCls = Class.forName(locClasses[i]);
                    Object bLoc = bLocCls.getConstructor(double.class, double.class).newInstance(lat, lng);
                    for (Method m : mgrCls.getMethods()) {
                        if (m.getName().equals("setLocation") && m.getParameterTypes().length == 3) {
                            m.invoke(mgr, userId, pkg, bLoc);
                        }
                    }
                }
            } catch (Throwable ignored) {}
        }
    }
}
