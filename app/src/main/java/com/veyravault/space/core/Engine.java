package com.veyravault.space.core;

import android.app.Application;
import android.content.Context;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

public class Engine {

    private static final String[] CORE_CLASSES = {
        "top.niunaijun.blackbox.BlackBoxCore",
        "com.vcore.BlackBoxCore"
    };

    public static Object getCore() {
        for (String cn : CORE_CLASSES) {
            try {
                Class<?> cls = Class.forName(cn);
                Method get = cls.getDeclaredMethod("get");
                return get.invoke(null);
            } catch (Throwable ignored) {}
        }
        return null;
    }

    public static void doAttachBaseContext(Application app, final Context base) {
        try {
            Object core = getCore();
            if (core == null) return;
            for (Method m : core.getClass().getMethods()) {
                if (m.getName().equals("doAttachBaseContext") && m.getParameterTypes().length == 2) {
                    Object clientCfg = buildClientConfig(base);
                    if (clientCfg != null) {
                        m.invoke(core, base, clientCfg);
                        return;
                    }
                } else if (m.getName().equals("doAttachBaseContext") && m.getParameterTypes().length == 1) {
                    m.invoke(core, base);
                    return;
                }
            }
        } catch (Throwable ignored) {}
    }

    private static Object buildClientConfig(final Context ctx) {
        try {
            return new top.niunaijun.blackbox.app.configuration.ClientConfiguration() {
                @Override
                public String getHostPackageName() {
                    return ctx.getPackageName();
                }
            };
        } catch (Throwable t) {
            return null;
        }
    }

    public static void doOnCreate(Application app) {
        try {
            Object core = getCore();
            if (core == null) return;
            for (Method m : core.getClass().getMethods()) {
                if ((m.getName().equals("doCreate") || m.getName().equals("onCreate"))
                        && m.getParameterTypes().length == 0) {
                    m.invoke(core);
                    return;
                }
            }
        } catch (Throwable ignored) {}
    }

    public static boolean installPackageAsUser(String pkg, int userId) {
        try {
            Object core = getCore();
            if (core == null) return false;
            Method m = core.getClass().getMethod("installPackageAsUser", String.class, int.class);
            Object res = m.invoke(core, pkg, userId);
            if (res == null) return true;
            Field f = res.getClass().getField("success");
            return f.getBoolean(res);
        } catch (Throwable t) {
            return true;
        }
    }

    public static boolean launchClone(Context ctx, CloneStore.CloneEntry entry) {
        CloneStore.recordActiveLaunch(ctx, entry);
        VirtualHookManager.syncCloneHooks(ctx, entry);
        installPackageAsUser(entry.packageName, entry.userId);
        try {
            Object core = getCore();
            if (core == null) return false;
            Method m = core.getClass().getMethod("launchApk", String.class, int.class);
            Object r = m.invoke(core, entry.packageName, entry.userId);
            return r == null || Boolean.TRUE.equals(r);
        } catch (Throwable t) {
            return false;
        }
    }

    public static void stopClone(String pkg, int userId) {
        try {
            Object core = getCore();
            if (core == null) return;
            for (Method m : core.getClass().getMethods()) {
                if ((m.getName().equals("stopPackage") || m.getName().equals("killApplication"))
                        && m.getParameterTypes().length == 2) {
                    m.invoke(core, pkg, userId);
                    return;
                }
            }
        } catch (Throwable ignored) {}
    }

    public static void clearCloneData(String pkg, int userId) {
        try {
            Object core = getCore();
            if (core == null) return;
            Method m = core.getClass().getMethod("clearPackage", String.class, int.class);
            m.invoke(core, pkg, userId);
        } catch (Throwable ignored) {}
    }

    public static void uninstallClone(String pkg, int userId) {
        try {
            Object core = getCore();
            if (core == null) return;
            Method m = core.getClass().getMethod("uninstallPackageAsUser", String.class, int.class);
            m.invoke(core, pkg, userId);
        } catch (Throwable ignored) {}
    }

    public static boolean isGmsInstalled(int userId) {
        return GmsSupportManager.isGmsInstalled(userId);
    }

    public static boolean setGmsEnabled(int userId, boolean enable) {
        return GmsSupportManager.setGmsEnabled(userId, enable);
    }
}
