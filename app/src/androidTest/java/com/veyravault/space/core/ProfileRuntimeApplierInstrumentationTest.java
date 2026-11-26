package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Locale;
import java.util.TimeZone;

import static org.junit.Assert.assertEquals;

@RunWith(AndroidJUnit4.class)
public class ProfileRuntimeApplierInstrumentationTest {
    @Test public void cloneLocaleAndTimeZoneAreAppliedToCurrentProcess() {
        Context context = ApplicationProvider.getApplicationContext();
        Locale originalLocale = Locale.getDefault();
        TimeZone originalZone = (TimeZone) TimeZone.getDefault().clone();
        Configuration originalConfiguration =
                new Configuration(context.getResources().getConfiguration());
        try {
            ProfileSettings clone = new ProfileSettings();
            clone.localeTag = "fr-FR";
            clone.timeZoneId = "Europe/Paris";
            ProfileSettings global = new ProfileSettings();
            global.localeTag = "de-DE";
            global.timeZoneId = "Europe/Berlin";
            ProfileSettings system = ProfileRuntimeApplier.systemFallback();

            ProfileResolver.ResolvedProfile resolved =
                    ProfileResolver.resolve(clone, global, system);
            ProfileRuntimeApplier.apply(context, resolved);

            assertEquals(ProfileResolver.Source.CLONE, resolved.localeSource);
            assertEquals(ProfileResolver.Source.CLONE, resolved.timeZoneSource);
            assertEquals("fr", Locale.getDefault().getLanguage());
            assertEquals("Europe/Paris", TimeZone.getDefault().getID());
            assertEquals("fr", context.getResources().getConfiguration().locale.getLanguage());
        } finally {
            Locale.setDefault(originalLocale);
            TimeZone.setDefault(originalZone);
            context.getResources().updateConfiguration(
                    originalConfiguration, context.getResources().getDisplayMetrics());
        }
    }

    @Test public void strictResolverReadsCloneAndGlobalFieldsIndependently() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences prefs = context.getSharedPreferences(
                "veyravault_profiles_v1", Context.MODE_PRIVATE);
        String before = prefs.getString("profiles_json", null);
        try {
            String payload = "{\"schemaVersion\":1,"
                    + "\"global\":{\"localeTag\":\"de-DE\",\"timeZoneId\":\"Europe/Berlin\"},"
                    + "\"clones\":{\"com.example.runtime#3\":{\"localeTag\":\"fr-FR\"}}}";
            assertEquals(true, prefs.edit().putString("profiles_json", payload).commit());

            ProfileSettings system = new ProfileSettings();
            system.localeTag = "en-US";
            system.timeZoneId = "UTC";
            ProfileResolver.ResolvedProfile resolved =
                    ProfileRuntimeClient.resolve(context, "com.example.runtime", 3);

            assertEquals("fr-FR", resolved.localeTag);
            assertEquals(ProfileResolver.Source.CLONE, resolved.localeSource);
            assertEquals("Europe/Berlin", resolved.timeZoneId);
            assertEquals(ProfileResolver.Source.GLOBAL, resolved.timeZoneSource);
        } finally {
            if (before == null) prefs.edit().remove("profiles_json").commit();
            else prefs.edit().putString("profiles_json", before).commit();
        }
    }
    @Test public void nextCloneBindRestoresProcessBaselineWithoutUsingItAsProfileFallback() {
        Context context = ApplicationProvider.getApplicationContext();
        Locale originalLocale = Locale.getDefault();
        TimeZone originalZone = (TimeZone) TimeZone.getDefault().clone();
        Configuration originalConfiguration =
                new Configuration(context.getResources().getConfiguration());
        String hostBaselineZone = TimeZone.getDefault().getID();
        ProfileRuntimeApplier.initializeSystemFallback(context);
        try {
            ProfileSettings cloneA = new ProfileSettings();
            cloneA.timeZoneId = "Europe/Paris";
            ProfileResolver.ResolvedProfile first =
                    ProfileResolver.resolve(cloneA, new ProfileSettings(),
                            ProfileRuntimeApplier.systemFallback());
            ProfileRuntimeApplier.apply(context, first);
            assertEquals("Europe/Paris", TimeZone.getDefault().getID());

            // The internal baseline clears Clone A before the next bind. The target profile
            // fallback remains deterministic and is applied before target Application creation.
            ProfileRuntimeApplier.restoreSystemDefaults(context);
            assertEquals(hostBaselineZone, TimeZone.getDefault().getID());
            assertEquals("UTC", ProfileRuntimeApplier.systemFallback().timeZoneId);
        } finally {
            Locale.setDefault(originalLocale);
            TimeZone.setDefault(originalZone);
            context.getResources().updateConfiguration(
                    originalConfiguration, context.getResources().getDisplayMetrics());
        }
    }

    @Test public void safeFallbackNeverUsesHostLocaleOrTimeZone() {
        Context context = ApplicationProvider.getApplicationContext();
        Locale originalLocale = Locale.getDefault();
        TimeZone originalZone = (TimeZone) TimeZone.getDefault().clone();
        Configuration originalConfiguration =
                new Configuration(context.getResources().getConfiguration());
        try {
            Locale.setDefault(Locale.forLanguageTag("ja-JP"));
            TimeZone.setDefault(TimeZone.getTimeZone("Asia/Tokyo"));

            ProfileResolver.ResolvedProfile resolved = ProfileResolver.resolve(
                    new ProfileSettings(), new ProfileSettings(),
                    ProfileRuntimeApplier.systemFallback());
            assertEquals("en-US", resolved.localeTag);
            assertEquals("UTC", resolved.timeZoneId);
            ProfileRuntimeApplier.apply(context, resolved);
            assertEquals("en", Locale.getDefault().getLanguage());
            assertEquals("UTC", TimeZone.getDefault().getID());
            assertEquals("en", context.getResources().getConfiguration().locale.getLanguage());

            ProfileRuntimeApplier.applySafeDefaults(context);
            assertEquals("en", Locale.getDefault().getLanguage());
            assertEquals("UTC", TimeZone.getDefault().getID());
        } finally {
            Locale.setDefault(originalLocale);
            TimeZone.setDefault(originalZone);
            context.getResources().updateConfiguration(
                    originalConfiguration, context.getResources().getDisplayMetrics());
        }
    }

}
