package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;
import java.security.MessageDigest;

public class SecurityManager {
    private static final String PREF = "veyra_security_prefs";
    private static final String KEY_MODE = "lock_mode"; // 0=None, 1=PIN, 2=Pattern
    private static final String KEY_HASH = "lock_hash";
    private static boolean sessionUnlocked = false;

    public static final int MODE_NONE = 0;
    public static final int MODE_PIN = 1;
    public static final int MODE_PATTERN = 2;

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public static int getLockMode(Context c) {
        return prefs(c).getInt(KEY_MODE, MODE_NONE);
    }

    public static boolean isLockEnabled(Context c) {
        return getLockMode(c) != MODE_NONE && !prefs(c).getString(KEY_HASH, "").isEmpty();
    }

    public static void setLockCredential(Context c, int mode, String rawSecret) {
        if (mode == MODE_NONE || rawSecret == null || rawSecret.isEmpty()) {
            prefs(c).edit().putInt(KEY_MODE, MODE_NONE).putString(KEY_HASH, "").commit();
        } else {
            prefs(c).edit().putInt(KEY_MODE, mode).putString(KEY_HASH, sha256(rawSecret)).commit();
        }
        sessionUnlocked = true;
    }

    public static boolean verifyCredential(Context c, String rawSecret) {
        String stored = prefs(c).getString(KEY_HASH, "");
        boolean ok = !stored.isEmpty() && stored.equals(sha256(rawSecret));
        if (ok) sessionUnlocked = true;
        return ok;
    }

    public static boolean isSessionUnlocked(Context c) {
        return !isLockEnabled(c) || sessionUnlocked;
    }

    public static void lockSession() {
        sessionUnlocked = false;
    }

    private static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest(("VeyraSalt_" + input).getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return input;
        }
    }
}
