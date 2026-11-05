package com.veyravault.space.core;

import java.lang.reflect.Method;

public class GmsSupportManager {

    public static boolean isGmsInstalled(int userId) {
        try {
            Object core = Engine.getCore();
            if (core == null) return false;
            Method m = core.getClass().getMethod("isInstallGms", int.class);
            return Boolean.TRUE.equals(m.invoke(core, userId));
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean setGmsEnabled(int userId, boolean enable) {
        try {
            Object core = Engine.getCore();
            if (core == null) return false;
            if (enable) {
                Method m = core.getClass().getMethod("installGms", int.class);
                Object r = m.invoke(core, userId);
                if (r != null) {
                    try {
                        return r.getClass().getField("success").getBoolean(r);
                    } catch (Throwable ignored) {}
                }
                return true;
            } else {
                Method m = core.getClass().getMethod("uninstallGms", int.class);
                m.invoke(core, userId);
                return true;
            }
        } catch (Throwable t) {
            return false;
        }
    }
}
