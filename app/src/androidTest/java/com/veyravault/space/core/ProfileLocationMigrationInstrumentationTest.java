package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public class ProfileLocationMigrationInstrumentationTest {

    @Test public void explicitResetToGlobalDoesNotReimportLegacyCloneLocation() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences profilePrefs = context.getSharedPreferences("veyravault_profiles_v1", Context.MODE_PRIVATE);
        Map<String, ?> profileSnapshot = profilePrefs.getAll();
        String packageName = "com.example.location.migration.fixture";
        int userId = 987654;

        try {
            profilePrefs.edit().clear().commit();
            CloneStore.CloneEntry legacy = new CloneStore.CloneEntry();
            legacy.packageName = packageName;
            legacy.userId = userId;
            legacy.displayName = "Location migration fixture";
            legacy.mockGpsEnabled = true;
            legacy.latitude = 40.7128d;
            legacy.longitude = -74.0060d;
            legacy.deniedPermissions = new HashSet<String>();
            java.util.List<CloneStore.CloneEntry> legacySnapshot = Collections.singletonList(legacy);
            assertTrue("legacy GPS profile import must succeed",
                    ProfileStore.importLegacyLocationSettings(context, legacySnapshot));

            ProfileSettings imported = ProfileStore.readCloneOverrideStrict(context, packageName, userId);
            assertEquals(Boolean.TRUE, imported.locationEnabled);
            assertEquals(Double.valueOf(40.7128d), imported.latitude);
            assertEquals(Double.valueOf(-74.0060d), imported.longitude);

            assertTrue("reset must commit", ProfileStore.clearCloneLocationOverrides(
                    context, packageName, userId));
            assertTrue("subsequent legacy scan must remain safe",
                    ProfileStore.importLegacyLocationSettings(context, legacySnapshot));

            ProfileSettings inherited = ProfileStore.readCloneOverrideStrict(context, packageName, userId);
            assertNull("explicit reset must not be resurrected from legacy CloneStore",
                    inherited.locationEnabled);
            assertNull(inherited.latitude);
            assertNull(inherited.longitude);

            ProfileSettings replacement = new ProfileSettings();
            replacement.locationEnabled = true;
            replacement.latitude = 51.5074d;
            replacement.longitude = -0.1278d;
            assertTrue("new profile override must commit",
                    ProfileStore.saveCloneOverride(context, packageName, userId, replacement));
            ProfileSettings saved = ProfileStore.readCloneOverrideStrict(context, packageName, userId);
            assertEquals(Boolean.TRUE, saved.locationEnabled);
            assertEquals(Double.valueOf(51.5074d), saved.latitude);
            assertEquals(Double.valueOf(-0.1278d), saved.longitude);
        } finally {
            restore(profilePrefs, profileSnapshot);
        }
    }

    @Test public void globalLocationSaveAndClearPreserveLocaleAndTimezone() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences prefs = context.getSharedPreferences("veyravault_profiles_v1", Context.MODE_PRIVATE);
        Map<String, ?> snapshot = prefs.getAll();
        try {
            prefs.edit().clear().commit();
            ProfileSettings base = new ProfileSettings();
            base.localeTag = "en-US";
            base.timeZoneId = "America/New_York";
            assertTrue(ProfileStore.saveGlobal(context, base));

            assertTrue(ProfileStore.saveGlobalLocationOverrides(context, true, 40.0d, -70.0d));
            ProfileSettings saved = ProfileStore.readGlobalStrict(context);
            assertEquals("en-US", saved.localeTag);
            assertEquals("America/New_York", saved.timeZoneId);
            assertEquals(Boolean.TRUE, saved.locationEnabled);
            assertEquals(Double.valueOf(40.0d), saved.latitude);
            assertEquals(Double.valueOf(-70.0d), saved.longitude);

            assertTrue(ProfileStore.clearGlobalLocationOverrides(context));
            ProfileSettings cleared = ProfileStore.readGlobalStrict(context);
            assertEquals("en-US", cleared.localeTag);
            assertEquals("America/New_York", cleared.timeZoneId);
            assertNull(cleared.locationEnabled);
            assertNull(cleared.latitude);
            assertNull(cleared.longitude);
        } finally {
            restore(prefs, snapshot);
        }
    }

    private static void restore(SharedPreferences preferences, Map<String, ?> snapshot) {
        SharedPreferences.Editor editor = preferences.edit().clear();
        for (Map.Entry<String, ?> entry : snapshot.entrySet()) {
            Object value = entry.getValue();
            String key = entry.getKey();
            if (value instanceof String) editor.putString(key, (String) value);
            else if (value instanceof Boolean) editor.putBoolean(key, (Boolean) value);
            else if (value instanceof Integer) editor.putInt(key, (Integer) value);
            else if (value instanceof Long) editor.putLong(key, (Long) value);
            else if (value instanceof Float) editor.putFloat(key, (Float) value);
            else if (value instanceof Set) {
                @SuppressWarnings("unchecked")
                Set<String> strings = new HashSet<String>((Set<String>) value);
                editor.putStringSet(key, strings);
            }
        }
        assertTrue("pre-test preferences must be restored", editor.commit());
    }
}
