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
        assertTrue(ProcessUtils.isBlackBoxWorkerProcess(
                "com.veyravault.space:p0", host));
        assertTrue(ProcessUtils.isBlackBoxWorkerProcess(
                "com.veyravault.space:p12", host));
        assertFalse(ProcessUtils.isBlackBoxWorkerProcess(host, host));
        assertFalse(ProcessUtils.isBlackBoxWorkerProcess(
                "com.example.other:p0", host));
        assertFalse(ProcessUtils.isBlackBoxWorkerProcess("com.veyravault.space:remote", host));
        assertFalse(ProcessUtils.isBlackBoxWorkerProcess("com.veyravault.space:vpn", host));
        assertFalse(ProcessUtils.isBlackBoxWorkerProcess("com.veyravault.space:p", host));
        assertFalse(ProcessUtils.isBlackBoxWorkerProcess("com.veyravault.space:p2x", host));
        assertFalse(ProcessUtils.isBlackBoxWorkerProcess("com.veyravault.space:p0:extra", host));
        assertFalse(ProcessUtils.isBlackBoxWorkerProcess(null, host));
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

    @Test public void typedProviderRuntimeResolutionHonorsCloneSafeDefaultAndInheritGlobal() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences documents = context.getSharedPreferences(
                "veyravault_profile_documents_v1", Context.MODE_PRIVATE);
        SharedPreferences legacy = context.getSharedPreferences(
                "veyravault_profiles_v1", Context.MODE_PRIVATE);
        java.util.Map<String, ?> documentsBefore = documents.getAll();
        java.util.Map<String, ?> legacyBefore = legacy.getAll();
        String packageName = "com.veyravault.runtime.safe-default.fixture";
        int userId = 9917;
        try {
            documents.edit().clear().commit();
            legacy.edit().clear().commit();
            assertTrue(ProfileDocumentStore.saveGlobalField(
                    context, "timeZoneId", "America/New_York"));

            ProfileDocument cloneSafe = new ProfileDocument();
            cloneSafe.markSafeDefault("timeZoneId");
            assertTrue(ProfileDocumentStore.saveCloneDocument(
                    context, packageName, userId, cloneSafe));

            ProfileRuntimeClient.ResolvedDocument safeDocument =
                    ProfileRuntimeClient.resolveDocument(context, packageName, userId);
            assertEquals(ProfileFieldRegistry.all().size(), safeDocument.fields().size());
            assertEquals("UTC", safeDocument.field("timeZoneId").value);
            assertEquals(ProfileDocumentResolver.Source.SAFE_DEFAULT,
                    safeDocument.field("timeZoneId").source);
            assertEquals(ProfileFieldRegistry.ApplyStatus.NOT_TESTED,
                    safeDocument.field("timeZoneId").status);
            assertFalse(safeDocument.field("publicIpAddress").editable);
            assertEquals(ProfileFieldRegistry.ApplyStatus.NOT_APPLICABLE,
                    safeDocument.field("publicIpAddress").status);
            assertEquals(ProfileFieldRegistry.Capability.PLATFORM_RESTRICTED,
                    safeDocument.field("imei").capability);
            assertFalse(safeDocument.field("imei").editable);
            ProfileResolver.ResolvedProfile safe = safeDocument.toRuntimeProfile();
            assertEquals("UTC", safe.timeZoneId);
            assertEquals(ProfileResolver.Source.SAFE_DEFAULT, safe.timeZoneSource);

            ProfileDocument cloneInherit = new ProfileDocument();
            cloneInherit.markInheritGlobal("timeZoneId");
            assertTrue(ProfileDocumentStore.saveCloneDocument(
                    context, packageName, userId, cloneInherit));

            ProfileResolver.ResolvedProfile inherited = ProfileRuntimeClient.resolve(
                    context, packageName, userId);
            assertEquals("America/New_York", inherited.timeZoneId);
            assertEquals(ProfileResolver.Source.GLOBAL, inherited.timeZoneSource);
        } finally {
            restorePreferences(documents, documentsBefore);
            restorePreferences(legacy, legacyBefore);
        }
    }

    @Test public void fullSnapshotPromotesOnlyFieldsWithSuccessfulRuntimeReadback() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences documents = context.getSharedPreferences(
                "veyravault_profile_documents_v1", Context.MODE_PRIVATE);
        SharedPreferences legacy = context.getSharedPreferences(
                "veyravault_profiles_v1", Context.MODE_PRIVATE);
        java.util.Map<String, ?> documentsBefore = documents.getAll();
        java.util.Map<String, ?> legacyBefore = legacy.getAll();
        Locale originalLocale = Locale.getDefault();
        TimeZone originalZone = (TimeZone) TimeZone.getDefault().clone();
        Configuration originalConfiguration =
                new Configuration(context.getResources().getConfiguration());
        int userId = 9187;
        try {
            assertTrue(ProfileDocumentStore.saveCloneField(
                    context, context.getPackageName(), userId, "localeTag", "fr-FR"));
            assertTrue(ProfileDocumentStore.saveCloneField(
                    context, context.getPackageName(), userId, "timeZoneId", "Europe/Paris"));

            ProfileRuntimeClient.ResolvedDocument resolved =
                    ProfileRuntimeClient.resolveDocument(context, context.getPackageName(), userId);
            assertEquals(ProfileFieldRegistry.ApplyStatus.NOT_TESTED,
                    resolved.field("localeTag").status);
            assertEquals(ProfileFieldRegistry.ApplyStatus.NOT_TESTED,
                    resolved.field("timeZoneId").status);

            ProfileRuntimeApplier.applySafeDefaults(context);
            ProfileRuntimeApplier.RuntimeApplyResult readback =
                    ProfileRuntimeApplier.applyAndVerify(
                            context, context.getPackageName(), resolved.toRuntimeProfile());
            assertTrue(readback.isFullyVerified());

            ProfileRuntimeClient.ResolvedDocument verified =
                    resolved.withRuntimeVerification(readback);
            assertEquals(ProfileFieldRegistry.ApplyStatus.APPLIED,
                    verified.field("localeTag").status);
            assertEquals(ProfileFieldRegistry.ApplyStatus.APPLIED,
                    verified.field("timeZoneId").status);
            assertEquals(ProfileFieldRegistry.ApplyStatus.NOT_APPLICABLE,
                    verified.field("publicIpAddress").status);
            assertEquals(ProfileFieldRegistry.ApplyStatus.NOT_TESTED,
                    verified.field("locationEnabled").status);
        } finally {
            Locale.setDefault(originalLocale);
            TimeZone.setDefault(originalZone);
            context.getResources().updateConfiguration(
                    originalConfiguration, context.getResources().getDisplayMetrics());
            restorePreferences(documents, documentsBefore);
            restorePreferences(legacy, legacyBefore);
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

    private static void restorePreferences(SharedPreferences preferences,
                                            java.util.Map<String, ?> snapshot) {
        SharedPreferences.Editor editor = preferences.edit().clear();
        for (java.util.Map.Entry<String, ?> entry : snapshot.entrySet()) {
            Object value = entry.getValue();
            String key = entry.getKey();
            if (value instanceof String) editor.putString(key, (String) value);
            else if (value instanceof Boolean) editor.putBoolean(key, (Boolean) value);
            else if (value instanceof Integer) editor.putInt(key, (Integer) value);
            else if (value instanceof Long) editor.putLong(key, (Long) value);
            else if (value instanceof Float) editor.putFloat(key, (Float) value);
            else if (value instanceof java.util.Set) {
                @SuppressWarnings("unchecked")
                java.util.Set<String> strings = new java.util.HashSet<>((java.util.Set<String>) value);
                editor.putStringSet(key, strings);
            }
        }
        assertTrue("Instrumentation preferences must be restored", editor.commit());
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
