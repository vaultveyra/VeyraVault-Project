package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AppLockPolicyInstrumentationTest {
    private static final String PREFS = "veyra_security_policy_prefs";
    private static final String KEY = "background_lock_timeout_seconds";

    private Context context;
    private SharedPreferences preferences;
    private boolean hadOriginalValue;
    private Object originalValue;

    @Before
    public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        hadOriginalValue = preferences.contains(KEY);
        originalValue = preferences.getAll().get(KEY);
    }

    @After
    public void tearDown() {
        SharedPreferences.Editor editor = preferences.edit();
        if (!hadOriginalValue) {
            editor.remove(KEY);
        } else if (originalValue instanceof Integer) {
            editor.putInt(KEY, (Integer) originalValue);
        } else if (originalValue instanceof String) {
            editor.putString(KEY, (String) originalValue);
        } else if (originalValue instanceof Boolean) {
            editor.putBoolean(KEY, (Boolean) originalValue);
        } else if (originalValue instanceof Long) {
            editor.putLong(KEY, (Long) originalValue);
        } else if (originalValue instanceof Float) {
            editor.putFloat(KEY, (Float) originalValue);
        } else {
            editor.remove(KEY);
        }
        assertTrue("App lock policy preference restoration failed", editor.commit());
    }

    @Test
    public void missingPreferenceDefaultsToImmediateLock() {
        assertTrue(preferences.edit().remove(KEY).commit());
        assertEquals(AppLockPolicy.TIMEOUT_IMMEDIATELY,
                AppLockPolicy.getBackgroundTimeoutSeconds(context));
    }

    @Test
    public void supportedTimeoutsPersistIndependently() {
        int[] supported = {
                AppLockPolicy.TIMEOUT_IMMEDIATELY,
                AppLockPolicy.TIMEOUT_30_SECONDS,
                AppLockPolicy.TIMEOUT_1_MINUTE,
                AppLockPolicy.TIMEOUT_5_MINUTES
        };
        for (int value : supported) {
            assertTrue(AppLockPolicy.setBackgroundTimeoutSeconds(context, value));
            assertEquals(value, preferences.getInt(KEY, -1));
            assertEquals(value, AppLockPolicy.getBackgroundTimeoutSeconds(context));
        }
    }

    @Test
    public void unsupportedTimeoutDoesNotOverwriteSavedValue() {
        assertTrue(AppLockPolicy.setBackgroundTimeoutSeconds(
                context, AppLockPolicy.TIMEOUT_1_MINUTE));
        assertFalse(AppLockPolicy.setBackgroundTimeoutSeconds(context, 17));
        assertEquals(AppLockPolicy.TIMEOUT_1_MINUTE, preferences.getInt(KEY, -1));
    }

    @Test
    public void malformedPreferenceFallsBackToImmediateLock() {
        assertTrue(preferences.edit().putString(KEY, "sixty").commit());
        assertEquals(AppLockPolicy.TIMEOUT_IMMEDIATELY,
                AppLockPolicy.getBackgroundTimeoutSeconds(context));
    }
}
