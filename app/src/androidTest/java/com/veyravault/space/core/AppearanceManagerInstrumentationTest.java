package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.appcompat.app.AppCompatDelegate;
import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AppearanceManagerInstrumentationTest {
    private static final String PREFS = "veyra_appearance_prefs";
    private static final String KEY_THEME_MODE = "theme_mode";

    private Context context;
    private SharedPreferences preferences;
    private boolean hadOriginalValue;
    private String originalValue;

    @Before
    public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        hadOriginalValue = preferences.contains(KEY_THEME_MODE);
        originalValue = preferences.getString(KEY_THEME_MODE, null);
    }

    @After
    public void tearDown() {
        SharedPreferences.Editor editor = preferences.edit();
        if (hadOriginalValue) {
            editor.putString(KEY_THEME_MODE, originalValue);
        } else {
            editor.remove(KEY_THEME_MODE);
        }
        assertTrue("Appearance test preference restoration failed", editor.commit());
        AppearanceManager.apply(context);
        String restoredMode = hadOriginalValue && originalValue != null
                ? originalValue : AppearanceManager.MODE_SYSTEM;
        assertEquals(restoredMode, AppearanceManager.getThemeMode(context));
    }

    @Test
    public void missingPreferenceDefaultsToSystem() {
        preferences.edit().remove(KEY_THEME_MODE).commit();
        assertEquals(AppearanceManager.MODE_SYSTEM, AppearanceManager.getThemeMode(context));
        AppearanceManager.apply(context);
        assertEquals(AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM,
                AppCompatDelegate.getDefaultNightMode());
    }

    @Test
    public void lightAndDarkModesAreCommittedAndApplied() {
        assertTrue(AppearanceManager.setThemeMode(context, AppearanceManager.MODE_LIGHT));
        assertEquals(AppearanceManager.MODE_LIGHT, preferences.getString(KEY_THEME_MODE, null));
        assertEquals(AppCompatDelegate.MODE_NIGHT_NO, AppCompatDelegate.getDefaultNightMode());

        assertTrue(AppearanceManager.setThemeMode(context, AppearanceManager.MODE_DARK));
        assertEquals(AppearanceManager.MODE_DARK, preferences.getString(KEY_THEME_MODE, null));
        assertEquals(AppCompatDelegate.MODE_NIGHT_YES, AppCompatDelegate.getDefaultNightMode());
    }

    @Test
    public void systemModeIsPersistedAndApplied() {
        assertTrue(AppearanceManager.setThemeMode(context, AppearanceManager.MODE_DARK));
        assertTrue(AppearanceManager.setThemeMode(context, AppearanceManager.MODE_SYSTEM));
        assertEquals(AppearanceManager.MODE_SYSTEM, preferences.getString(KEY_THEME_MODE, null));
        assertEquals(AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM,
                AppCompatDelegate.getDefaultNightMode());
    }

    @Test
    public void malformedPreferenceTypeFallsBackToSystem() {
        assertTrue(preferences.edit().putBoolean(KEY_THEME_MODE, true).commit());
        assertEquals(AppearanceManager.MODE_SYSTEM, AppearanceManager.getThemeMode(context));
    }

    @Test
    public void invalidModeIsRejectedWithoutOverwritingSavedPreference() {
        assertTrue(AppearanceManager.setThemeMode(context, AppearanceManager.MODE_DARK));
        assertFalse(AppearanceManager.setThemeMode(context, "automatic-or-unknown"));
        assertEquals(AppearanceManager.MODE_DARK, preferences.getString(KEY_THEME_MODE, null));
        assertEquals(AppCompatDelegate.MODE_NIGHT_YES, AppCompatDelegate.getDefaultNightMode());
    }
}
