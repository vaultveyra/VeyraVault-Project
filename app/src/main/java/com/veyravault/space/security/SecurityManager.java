package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;

/** Stores and verifies app-lock credentials without changing legacy preference keys. */
public final class SecurityManager {
    private static final String PREF = "veyra_security_prefs";
    private static final String KEY_MODE = "lock_mode"; // 0=None, 1=PIN, 2=Pattern
    private static final String KEY_HASH = "lock_hash";
    // Dashboard diagnostics read this flag off the UI thread; volatile guarantees
    // visibility of lock/unlock transitions across the host process threads.
    private static volatile boolean sessionUnlocked = false;

    public static final int MODE_NONE = 0;
    public static final int MODE_PIN = 1;
    public static final int MODE_PATTERN = 2;

    private SecurityManager() { }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public static int getLockMode(Context c) {
        return prefs(c).getInt(KEY_MODE, MODE_NONE);
    }

    public static boolean isLockEnabled(Context c) {
        return getLockMode(c) != MODE_NONE && !prefs(c).getString(KEY_HASH, "").isEmpty();
    }

    /** Returns false if secure derivation or durable preference storage fails. */
    public static boolean setLockCredential(Context c, int mode, String rawSecret) {
        SharedPreferences.Editor editor = prefs(c).edit();
        if (mode == MODE_NONE) {
            boolean saved = editor.putInt(KEY_MODE, MODE_NONE)
                    .putString(KEY_HASH, "").commit();
            if (saved) sessionUnlocked = true;
            return saved;
        }
        if ((mode != MODE_PIN && mode != MODE_PATTERN)
                || rawSecret == null || rawSecret.isEmpty()) {
            return false;
        }
        try {
            String hash = SecurityCredentialHasher.createHash(
                    rawSecret, Build.VERSION.SDK_INT >= Build.VERSION_CODES.O);
            boolean saved = editor.putInt(KEY_MODE, mode).putString(KEY_HASH, hash).commit();
            if (saved) sessionUnlocked = true;
            return saved;
        } catch (Exception cryptoOrStorageFailure) {
            return false;
        }
    }

    public static boolean verifyCredential(Context c, String rawSecret) {
        if (rawSecret == null) return false;
        SharedPreferences p = prefs(c);
        String stored = p.getString(KEY_HASH, "");
        if (stored.isEmpty()) return false;
        try {
            SecurityCredentialHasher.Verification result = SecurityCredentialHasher.verify(
                    rawSecret, stored, Build.VERSION.SDK_INT >= Build.VERSION_CODES.O);
            if (!result.valid) return false;

            // Upgrade legacy credentials only after successful verification. If the
            // write fails, retain the old hash and still allow this verified unlock.
            if (result.upgradedHash != null) {
                p.edit().putString(KEY_HASH, result.upgradedHash).commit();
            }
            sessionUnlocked = true;
            return true;
        } catch (Exception cryptoFailure) {
            return false;
        }
    }

    public static boolean isSessionUnlocked(Context c) {
        return !isLockEnabled(c) || sessionUnlocked;
    }

    public static void lockSession() {
        sessionUnlocked = false;
    }
}
