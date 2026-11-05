package com.veyravault.space.security;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;

public class AppDisguiseManager {
    public static final String[] ALIASES = {
        "com.veyravault.space.AliasDefault",
        "com.veyravault.space.AliasCalculator",
        "com.veyravault.space.AliasCalendar",
        "com.veyravault.space.AliasNotes",
        "com.veyravault.space.AliasWeather"
    };

    public static int getActiveDisguiseIndex(Context ctx) {
        PackageManager pm = ctx.getPackageManager();
        for (int i = 0; i < ALIASES.length; i++) {
            int state = pm.getComponentEnabledSetting(new ComponentName(ctx, ALIASES[i]));
            if (state == PackageManager.COMPONENT_ENABLED_STATE_ENABLED) return i;
        }
        return 0;
    }

    public static void applyDisguise(Context ctx, int targetIndex) {
        PackageManager pm = ctx.getPackageManager();
        for (int i = 0; i < ALIASES.length; i++) {
            int newState = (i == targetIndex)
                    ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED
                    : PackageManager.COMPONENT_ENABLED_STATE_DISABLED;
            pm.setComponentEnabledSetting(
                    new ComponentName(ctx, ALIASES[i]),
                    newState,
                    PackageManager.DONT_KILL_APP
            );
        }
    }
}
