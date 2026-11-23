package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public final class AppLockAttemptThrottlingInstrumentationTest {
    private static final String PREFS = "veyra_security_prefs";
    private static final String KEY_MODE = "lock_mode";
    private static final String KEY_HASH = "lock_hash";
    private static final String KEY_FAILED_ATTEMPTS = "lock_failed_attempts";
    private static final String KEY_LOCKOUT_UNTIL = "lockout_until_epoch_millis";

    @Test
    public void fifthIncorrectCredentialStartsCooldownAndCorrectCredentialResetsIt()
            throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences preferences =
                context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Map<String, ?> originalPreferences = new HashMap<>(preferences.getAll());

        Field unlockedField = SecurityManager.class.getDeclaredField("sessionUnlocked");
        Field failuresField = SecurityManager.class.getDeclaredField("processFailedAttempts");
        Field elapsedDeadlineField =
                SecurityManager.class.getDeclaredField("processLockoutUntilElapsed");
        unlockedField.setAccessible(true);
        failuresField.setAccessible(true);
        elapsedDeadlineField.setAccessible(true);

        boolean originalUnlocked = unlockedField.getBoolean(null);
        int originalFailures = failuresField.getInt(null);
        long originalElapsedDeadline = elapsedDeadlineField.getLong(null);

        try {
            assertTrue("Temporary test PIN must be stored",
                    SecurityManager.setLockCredential(
                            context, SecurityManager.MODE_PIN, "4286"));
            String storedHash = preferences.getString(KEY_HASH, "");
            assertFalse("Test PIN hash must be present", storedHash.isEmpty());

            for (int attempt = 1; attempt <= 4; attempt++) {
                assertFalse("Incorrect PIN must be rejected at attempt " + attempt,
                        SecurityManager.verifyCredential(context, "0000"));
                assertEquals("No cooldown is expected before the fifth failure",
                        0L, SecurityManager.getCredentialLockoutRemainingMillis(context));
            }

            assertFalse("Fifth incorrect PIN must be rejected",
                    SecurityManager.verifyCredential(context, "1111"));
            long remaining = SecurityManager.getCredentialLockoutRemainingMillis(context);
            assertTrue("Fifth failure must start a positive cooldown", remaining > 0L);
            assertTrue("Initial cooldown must not exceed 30 seconds", remaining <= 30_000L);
            assertEquals(5, preferences.getInt(KEY_FAILED_ATTEMPTS, 0));
            assertTrue("Persisted deadline must be in the future",
                    preferences.getLong(KEY_LOCKOUT_UNTIL, 0L) > System.currentTimeMillis());

            assertFalse("A correct PIN must not bypass an active cooldown",
                    SecurityManager.verifyCredential(context, "4286"));
            assertEquals("Blocked correct PIN must not reset failure count",
                    5, preferences.getInt(KEY_FAILED_ATTEMPTS, 0));
            assertEquals("Blocked correct PIN must not rewrite the credential",
                    storedHash, preferences.getString(KEY_HASH, ""));

            // Simulate the deadline naturally expiring without sleeping for 30 seconds.
            // The real elapsed-time companion is reset only by the test fixture.
            assertTrue("Test must persist the expired-deadline fixture",
                    preferences.edit().putLong(KEY_LOCKOUT_UNTIL, 0L).commit());
            elapsedDeadlineField.setLong(null, 0L);

            assertTrue("Correct PIN must unlock after cooldown expiry",
                    SecurityManager.verifyCredential(context, "4286"));
            assertEquals("Successful authentication must reset failures",
                    0, preferences.getInt(KEY_FAILED_ATTEMPTS, -1));
            assertEquals("Successful authentication must clear the deadline",
                    0L, preferences.getLong(KEY_LOCKOUT_UNTIL, -1L));
            assertTrue("Successful authentication must mark the session unlocked",
                    SecurityManager.isSessionUnlocked(context));
        } finally {
            restorePreferences(preferences, originalPreferences);
            unlockedField.setBoolean(null, originalUnlocked);
            failuresField.setInt(null, originalFailures);
            elapsedDeadlineField.setLong(null, originalElapsedDeadline);
            assertEquals("Credential preference map must be restored exactly",
                    originalPreferences, preferences.getAll());
        }
    }

    private static void restorePreferences(
            SharedPreferences preferences, Map<String, ?> original) {
        SharedPreferences.Editor editor = preferences.edit().clear();
        for (Map.Entry<String, ?> entry : original.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();
            if (value instanceof String) editor.putString(key, (String) value);
            else if (value instanceof Integer) editor.putInt(key, (Integer) value);
            else if (value instanceof Long) editor.putLong(key, (Long) value);
            else if (value instanceof Boolean) editor.putBoolean(key, (Boolean) value);
            else if (value instanceof Float) editor.putFloat(key, (Float) value);
            else if (value instanceof Set) {
                @SuppressWarnings("unchecked")
                Set<String> strings = (Set<String>) value;
                editor.putStringSet(key, strings);
            } else {
                throw new AssertionError("Unsupported preference value type for " + key);
            }
        }
        assertTrue("Could not restore app-lock preferences", editor.commit());
    }
}
