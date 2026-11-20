package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.appcompat.app.AppCompatDelegate;

/** Persisted, app-wide appearance preference independent from Clone data. */
public final class AppearanceManager {
    public static final String MODE_SYSTEM = "system";
    public static final String MODE_LIGHT = "light";
    public static final String MODE_DARK = "dark";

    private static final String PREFS = "veyra_appearance_prefs";
    private static final String KEY_THEME_MODE = "theme_mode";

    private AppearanceManager() { }

    private static SharedPreferences preferences(Context context) {
        Context app = context.getApplicationContext();
        return (app == null ? context : app)
                .getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static String getThemeMode(Context context) {
        String stored = preferences(context).getString(KEY_THEME_MODE, MODE_SYSTEM);
        return isValidMode(stored) ? stored : MODE_SYSTEM;
    }

    public static boolean isValidMode(String mode) {
        return MODE_SYSTEM.equals(mode) || MODE_LIGHT.equals(mode) || MODE_DARK.equals(mode);
    }

    /** Apply the saved preference before an Activity creates its AppCompat delegate. */
    public static void apply(Context context) {
        applyMode(getThemeMode(context));
    }

    /** Persist first; apply only after the preference commit is confirmed. */
    public static boolean setThemeMode(Context context, String mode) {
        if (context == null || !isValidMode(mode)) return false;
        boolean committed = preferences(context).edit()
                .putString(KEY_THEME_MODE, mode)
                .commit();
        if (committed) applyMode(mode);
        return committed;
    }

    private static void applyMode(String mode) {
        final int delegateMode;
        if (MODE_LIGHT.equals(mode)) {
            delegateMode = AppCompatDelegate.MODE_NIGHT_NO;
        } else if (MODE_DARK.equals(mode)) {
            delegateMode = AppCompatDelegate.MODE_NIGHT_YES;
        } else {
            delegateMode = AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM;
        }
        if (AppCompatDelegate.getDefaultNightMode() != delegateMode) {
            AppCompatDelegate.setDefaultNightMode(delegateMode);
        }
    }
}
