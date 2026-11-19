package com.veyravault.space.core;

import android.app.Application;
import android.content.Context;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

public class Engine {

    public enum CloneInstallState {
        INSTALLED,
        ABSENT,
        UNKNOWN
    }

    static CloneInstallState classifyInstalledQueryResult(Boolean installed) {
        if (installed == null) return CloneInstallState.UNKNOWN;
        return installed ? CloneInstallState.INSTALLED : CloneInstallState.ABSENT;
    }

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

                // Disable upstream automatic crash-log uploads by leaving no destination configured.
                @Override
                public String getLogSenderChatId() {
                    return null;
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

    private static volatile String lastInstallDiagnostic = "No install attempt has been made.";

    /** A bounded, non-sensitive explanation of the most recent install failure. */
    public static String getLastInstallDiagnostic() {
        return lastInstallDiagnostic;
    }

    private static String safeEngineMessage(String message) {
        if (message == null) return "";
        StringBuilder safe = new StringBuilder();
        for (int i = 0; i < message.length() && safe.length() < 180; i++) {
            char c = message.charAt(i);
            if (c >= 32 && c != 127) safe.append(c == '\\t' ? ' ' : c);
        }
        return safe.toString().trim();
    }

    public static boolean installPackageAsUser(String pkg, int userId) {
        lastInstallDiagnostic = "INSTALL_STARTED";
        try {
            Object core = getCore();
            if (core == null) {
                lastInstallDiagnostic = "ENGINE_UNAVAILABLE: core could not be resolved";
                return false;
            }
            Method m = core.getClass().getMethod("installPackageAsUser", String.class, int.class);
            Object res = m.invoke(core, pkg, userId);
            if (res == null) {
                lastInstallDiagnostic = "ENGINE_INVALID_RESULT: install returned null";
                return false;
            }
            Field success = res.getClass().getField("success");
            boolean installed = success.getBoolean(res);
            if (installed) {
                lastInstallDiagnostic = "INSTALL_SUCCEEDED";
                return true;
            }
            String detail = "";
            try {
                Field message = res.getClass().getField("msg");
                Object value = message.get(res);
                if (value instanceof String) detail = safeEngineMessage((String) value);
            } catch (Throwable ignored) {
                // Some engine versions do not expose a diagnostic message.
            }
            lastInstallDiagnostic = detail.isEmpty()
                    ? "ENGINE_REJECTED_INSTALL: engine reported success=false"
                    : "ENGINE_REJECTED_INSTALL: " + detail;
            return false;
        } catch (Throwable error) {
            Throwable cause = error.getCause();
            String type = error.getClass().getSimpleName();
            if (cause != null) type += " (cause: " + cause.getClass().getSimpleName() + ")";
            lastInstallDiagnostic = "ENGINE_INSTALL_EXCEPTION: " + type;
            return false;
        }
    }

    private static Boolean queryInstalledAsUser(String pkg, int userId) {
        try {
            Object core = getCore();
            if (core == null) return null;
            Method m = core.getClass().getMethod("isInstalled", String.class, int.class);
            Object result = m.invoke(core, pkg, userId);
            return result instanceof Boolean ? (Boolean) result : null;
        } catch (Throwable ignored) {
            return null;
        }
    }

    private static boolean isInstalledAsUser(String pkg, int userId) {
        return Boolean.TRUE.equals(queryInstalledAsUser(pkg, userId));
    }

    /** Returns a tri-state Engine result; reflection/query failures remain UNKNOWN. */
    public static CloneInstallState getCloneInstallState(String pkg, int userId) {
        if (pkg == null || pkg.trim().isEmpty() || userId < 0)
            return CloneInstallState.UNKNOWN;
        return classifyInstalledQueryResult(queryInstalledAsUser(pkg, userId));
    }

    /** True only when the engine explicitly reports that this virtual package is absent. */
    public static boolean isCloneConfirmedAbsent(String pkg, int userId) {
        return getCloneInstallState(pkg, userId) == CloneInstallState.ABSENT;
    }

    public static boolean launchClone(Context ctx, CloneStore.CloneEntry entry) {
        if (!isInstalledAsUser(entry.packageName, entry.userId)
                && !installPackageAsUser(entry.packageName, entry.userId)) {
            return false;
        }
        // Apply per-clone engine configuration before starting the virtual app process.
        VirtualHookManager.syncCloneHooks(ctx, entry);
        try {
            Object core = getCore();
            if (core == null) return false;
            Method m = core.getClass().getMethod("launchApk", String.class, int.class);
            Object r = m.invoke(core, entry.packageName, entry.userId);
            boolean launched = Boolean.TRUE.equals(r);
            if (!launched) return false;

            // Persist only a confirmed successful launch; failed attempts must not replace
            // the last-known successful clone in the host-side active-launch marker.
            CloneStore.recordActiveLaunch(ctx, entry);
            return true;
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

    public static boolean uninstallClone(String pkg, int userId) {
        if (pkg == null || pkg.trim().isEmpty() || userId < 0) return false;
        try {
            Object core = getCore();
            if (core == null) return false;
            Method m = core.getClass().getMethod("uninstallPackageAsUser", String.class, int.class);
            m.invoke(core, pkg, userId);
            // A successful reflection call is not enough: confirm the engine reports
            // the virtual package absent. Unknown/error state is never success.
            return Boolean.FALSE.equals(queryInstalledAsUser(pkg, userId));
        } catch (Throwable ignored) {
            return false;
        }
    }

    public static boolean isGmsInstalled(int userId) {
        return GmsSupportManager.isGmsInstalled(userId);
    }

    public static boolean setGmsEnabled(int userId, boolean enable) {
        return GmsSupportManager.setGmsEnabled(userId, enable);
    }
}
