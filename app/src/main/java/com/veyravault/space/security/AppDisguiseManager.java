package com.veyravault.space.security;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;

/** Manages only the launcher aliases explicitly bundled in this application manifest. */
public final class AppDisguiseManager {
    public static final String[] ALIASES = {
        "com.veyravault.space.AliasDefault",
        "com.veyravault.space.AliasCalculator",
        "com.veyravault.space.AliasCalendar",
        "com.veyravault.space.AliasNotes",
        "com.veyravault.space.AliasWeather"
    };

    private AppDisguiseManager() { }

    /**
     * Returns the sole enabled launcher alias, or -1 if the current component state is
     * ambiguous or no supported alias is enabled.
     */
    public static int getActiveDisguiseIndex(Context context) {
        if (context == null) return -1;
        PackageManager manager = context.getPackageManager();
        int activeIndex = -1;
        int enabledCount = 0;

        for (int i = 0; i < ALIASES.length; i++) {
            int state = manager.getComponentEnabledSetting(
                    new ComponentName(context, ALIASES[i]));
            boolean effectivelyEnabled = state == PackageManager.COMPONENT_ENABLED_STATE_ENABLED
                    || (state == PackageManager.COMPONENT_ENABLED_STATE_DEFAULT && i == 0);
            if (effectivelyEnabled) {
                activeIndex = i;
                enabledCount++;
            }
        }
        return enabledCount == 1 ? activeIndex : -1;
    }

    /**
     * Enables the requested alias first, disables the remaining aliases, and verifies the
     * final effective state. If any PackageManager operation fails, it makes a best-effort
     * restoration of the exact previous component override states and returns false.
     */
    public static boolean applyDisguise(Context context, int targetIndex) {
        if (context == null || targetIndex < 0 || targetIndex >= ALIASES.length) return false;

        PackageManager manager = context.getPackageManager();
        int[] previousStates = new int[ALIASES.length];
        for (int i = 0; i < ALIASES.length; i++) {
            previousStates[i] = manager.getComponentEnabledSetting(
                    new ComponentName(context, ALIASES[i]));
        }

        try {
            manager.setComponentEnabledSetting(
                    new ComponentName(context, ALIASES[targetIndex]),
                    PackageManager.COMPONENT_ENABLED_STATE_ENABLED,
                    PackageManager.DONT_KILL_APP);

            for (int i = 0; i < ALIASES.length; i++) {
                if (i == targetIndex) continue;
                manager.setComponentEnabledSetting(
                        new ComponentName(context, ALIASES[i]),
                        PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                        PackageManager.DONT_KILL_APP);
            }
            return getActiveDisguiseIndex(context) == targetIndex;
        } catch (RuntimeException failure) {
            for (int i = 0; i < ALIASES.length; i++) {
                try {
                    manager.setComponentEnabledSetting(
                            new ComponentName(context, ALIASES[i]),
                            previousStates[i],
                            PackageManager.DONT_KILL_APP);
                } catch (RuntimeException ignored) {
                    // Best-effort rollback; caller receives false and must not report success.
                }
            }
            return false;
        }
    }
}
