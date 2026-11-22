package com.veyravault.space.core;

import java.lang.reflect.Method;

/** Read-only and explicit GMS availability state for one virtual user. */
public final class GmsSupportManager {
    public enum GmsState { INSTALLED, ABSENT, UNKNOWN }

    private GmsSupportManager() { }

    /**
     * UNKNOWN is distinct from ABSENT: a missing Engine, reflection failure or
     * unexpected result must not be presented as proof that GMS is not installed.
     */
    public static GmsState getGmsState(int userId) {
        if (userId < 0) return GmsState.UNKNOWN;
        try {
            Object core = Engine.getCore();
            if (core == null) return GmsState.UNKNOWN;
            Method method = core.getClass().getMethod("isInstallGms", int.class);
            Object result = method.invoke(core, userId);
            if (!(result instanceof Boolean)) return GmsState.UNKNOWN;
            return ((Boolean) result) ? GmsState.INSTALLED : GmsState.ABSENT;
        } catch (Throwable unavailable) {
            return GmsState.UNKNOWN;
        }
    }

    /** Backwards-compatible convenience method; use getGmsState for diagnostics. */
    public static boolean isGmsInstalled(int userId) {
        return getGmsState(userId) == GmsState.INSTALLED;
    }

    public static boolean setGmsEnabled(int userId, boolean enable) {
        try {
            Object core = Engine.getCore();
            if (core == null) return false;
            if (enable) {
                Method method = core.getClass().getMethod("installGms", int.class);
                Object result = method.invoke(core, userId);
                if (result != null) {
                    try {
                        return result.getClass().getField("success").getBoolean(result);
                    } catch (Throwable ignored) { }
                }
                return true;
            } else {
                Method method = core.getClass().getMethod("uninstallGms", int.class);
                method.invoke(core, userId);
                return true;
            }
        } catch (Throwable failure) {
            return false;
        }
    }
}
