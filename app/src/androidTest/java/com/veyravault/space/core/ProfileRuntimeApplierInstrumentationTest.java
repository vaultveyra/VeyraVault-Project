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
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public class ProfileRuntimeApplierInstrumentationTest {
    @Test public void blackBoxWorkerGateRejectsMainHostAndForeignProcesses() {
        String host = "com.veyravault.space";
        assertTrue(CloneProfileLifecycleCallback.isBlackBoxWorkerProcess(
                "com.veyravault.space:p0", host));
        assertTrue(CloneProfileLifecycleCallback.isBlackBoxWorkerProcess(
                "com.veyravault.space:p12", host));
        assertFalse(CloneProfileLifecycleCallback.isBlackBoxWorkerProcess(host, host));
        assertFalse(CloneProfileLifecycleCallback.isBlackBoxWorkerProcess(
                "com.example.other:p0", host));
        assertFalse(CloneProfileLifecycleCallback.isBlackBoxWorkerProcess(null, host));
    }

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
            ProfileRuntimeApplier.applySafeDefaults(context);
            ProfileRuntimeApplier.RuntimeApplyResult verification =
                    ProfileRuntimeApplier.applyAndVerify(context, context.getPackageName(), resolved);

            assertEquals(ProfileResolver.Source.CLONE, resolved.localeSource);
            assertEquals(ProfileResolver.Source.CLONE, resolved.timeZoneSource);
            assertTrue(verification.isFullyVerified());
            assertEquals(ProfileFieldRegistry.ApplyStatus.APPLIED, verification.localeStatus);
            assertEquals(ProfileFieldRegistry.ApplyStatus.APPLIED, verification.timeZoneStatus);
            assertEquals(context.getPackageName(), verification.targetPackageName);
            assertEquals("fr-FR", verification.expectedLocaleTag);
            assertEquals("fr-FR", verification.observedDefaultLocaleTag);
            assertEquals("fr-FR", verification.observedResourceLocaleTag);
            assertEquals("Europe/Paris", verification.observedTimeZoneId);
        } finally {
            Locale.setDefault(originalLocale);
            TimeZone.setDefault(originalZone);
            context.getResources().updateConfiguration(
                    originalConfiguration, context.getResources().getDisplayMetrics());
        }
    }

    @Test public void applyAndVerifyRejectsWrongTargetContextWithoutApplyingProfile() {
        Context context = ApplicationProvider.getApplicationContext();
        Locale originalLocale = Locale.getDefault();
        TimeZone originalZone = (TimeZone) TimeZone.getDefault().clone();
        Configuration originalConfiguration =
                new Configuration(context.getResources().getConfiguration());
        try {
            ProfileRuntimeApplier.applySafeDefaults(context);
            Locale safeLocale = Locale.getDefault();
            TimeZone safeZone = (TimeZone) TimeZone.getDefault().clone();

            ProfileSettings clone = new ProfileSettings();
            clone.localeTag = "fr-FR";
            clone.timeZoneId = "Europe/Paris";
            ProfileResolver.ResolvedProfile resolved = ProfileResolver.resolve(
                    clone, new ProfileSettings(), ProfileRuntimeApplier.systemFallback());

            ProfileRuntimeApplier.RuntimeApplyResult result =
                    ProfileRuntimeApplier.applyAndVerify(context, "com.example.not.the.target", resolved);

            assertFalse(result.targetIdentityMatches);
            assertFalse(result.isFullyVerified());
            assertEquals(ProfileFieldRegistry.ApplyStatus.FAILED, result.localeStatus);
            assertEquals(ProfileFieldRegistry.ApplyStatus.FAILED, result.timeZoneStatus);
            assertEquals(safeLocale, Locale.getDefault());
            assertEquals(safeZone.getID(), TimeZone.getDefault().getID());
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

    @Test public void nextCloneBindStartsFromSafeDefaultsWithoutHostOrPreviousCloneLeakage() {
        Context context = ApplicationProvider.getApplicationContext();
        Locale originalLocale = Locale.getDefault();
        TimeZone originalZone = (TimeZone) TimeZone.getDefault().clone();
        Configuration originalConfiguration =
                new Configuration(context.getResources().getConfiguration());
        try {
            Locale.setDefault(Locale.forLanguageTag("ja-JP"));
            TimeZone.setDefault(TimeZone.getTimeZone("Asia/Tokyo"));

            ProfileSettings cloneA = new ProfileSettings();
            cloneA.timeZoneId = "Europe/Paris";
            ProfileResolver.ResolvedProfile first =
                    ProfileResolver.resolve(cloneA, new ProfileSettings(),
                            ProfileRuntimeApplier.systemFallback());
            ProfileRuntimeApplier.apply(context, first);
            assertEquals("Europe/Paris", TimeZone.getDefault().getID());

            // The next target bind must clear Clone A directly to safe values, never host values.
            ProfileRuntimeApplier.applySafeDefaults(context);
            assertEquals("en", Locale.getDefault().getLanguage());
            assertEquals("UTC", TimeZone.getDefault().getID());

            ProfileSettings cloneB = new ProfileSettings();
            ProfileSettings global = new ProfileSettings();
            global.timeZoneId = "Europe/Berlin";
            ProfileResolver.ResolvedProfile second =
                    ProfileResolver.resolve(cloneB, global, ProfileRuntimeApplier.systemFallback());
            ProfileRuntimeApplier.apply(context, second);
            assertEquals(ProfileResolver.Source.GLOBAL, second.timeZoneSource);
            assertEquals("Europe/Berlin", TimeZone.getDefault().getID());

            // A Clone with no override and no Global value receives only the deterministic default.
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
