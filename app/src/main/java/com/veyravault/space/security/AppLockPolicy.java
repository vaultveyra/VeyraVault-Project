package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Main-app background lock policy. Kept separate from credential preferences so
 * changing a timeout never rewrites or clears an existing PIN/Pattern hash.
 */
public final class AppLockPolicy {
    private static final String PREFS = "veyra_security_policy_prefs";
    private static final String KEY_BACKGROUND_TIMEOUT_SECONDS = "background_lock_timeout_seconds";

    public static final int TIMEOUT_IMMEDIATELY = 0;
    public static final int TIMEOUT_30_SECONDS = 30;
    public static final int TIMEOUT_1_MINUTE = 60;
    public static final int TIMEOUT_5_MINUTES = 300;
    public static final int DEFAULT_BACKGROUND_TIMEOUT_SECONDS = TIMEOUT_IMMEDIATELY;

    private AppLockPolicy() { }

    private static SharedPreferences preferences(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static boolean isSupportedTimeout(int seconds) {
        return seconds == TIMEOUT_IMMEDIATELY
                || seconds == TIMEOUT_30_SECONDS
                || seconds == TIMEOUT_1_MINUTE
                || seconds == TIMEOUT_5_MINUTES;
    }

    public static int getBackgroundTimeoutSeconds(Context context) {
        if (context == null) return DEFAULT_BACKGROUND_TIMEOUT_SECONDS;
        try {
            int value = preferences(context).getInt(
                    KEY_BACKGROUND_TIMEOUT_SECONDS, DEFAULT_BACKGROUND_TIMEOUT_SECONDS);
            return isSupportedTimeout(value) ? value : DEFAULT_BACKGROUND_TIMEOUT_SECONDS;
        } catch (ClassCastException malformedPreference) {
            return DEFAULT_BACKGROUND_TIMEOUT_SECONDS;
        }
    }

    /** Returns false for unsupported values or a failed durable preference write. */
    public static boolean setBackgroundTimeoutSeconds(Context context, int seconds) {
        if (context == null || !isSupportedTimeout(seconds)) return false;
        return preferences(context).edit()
                .putInt(KEY_BACKGROUND_TIMEOUT_SECONDS, seconds)
                .commit();
    }
}
