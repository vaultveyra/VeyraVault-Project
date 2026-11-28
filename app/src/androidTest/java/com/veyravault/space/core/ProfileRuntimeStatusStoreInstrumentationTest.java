package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public class ProfileRuntimeStatusStoreInstrumentationTest {
    @Test public void legacyProfileEditsInvalidateReadbackWithoutTypedRevisionChange() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences documents = context.getSharedPreferences(
                "veyravault_profile_documents_v1", Context.MODE_PRIVATE);
        SharedPreferences legacy = context.getSharedPreferences(
                "veyravault_profiles_v1", Context.MODE_PRIVATE);
        SharedPreferences runtime = context.getSharedPreferences(
                "veyra_profile_runtime_status_v1", Context.MODE_PRIVATE);
        Map<String, ?> documentsBefore = documents.getAll();
        Map<String, ?> legacyBefore = legacy.getAll();
        Map<String, ?> runtimeBefore = runtime.getAll();
        String packageName = "com.example.clone.legacyfingerprint";
        int userId = 1201;
        try {
            documents.edit().clear().commit();
            legacy.edit().clear().commit();
            runtime.edit().clear().commit();

            assertTrue(ProfileDocumentStore.saveGlobalField(
                    context, "timeZoneId", "Europe/Paris"));
            ProfileSettings legacyGlobal = new ProfileSettings();
            legacyGlobal.localeTag = "fr-FR";
            assertTrue(ProfileStore.saveGlobal(context, legacyGlobal));

            long revision = ProfileDocumentStore.readRevisionStrict(context);
            ProfileResolver.ResolvedProfile before = ProfileRuntimeProvider.resolveMergedProfile(
                    context, packageName, userId, null);
            String fingerprint = ProfileRuntimeFingerprint.compute(before);
            assertTrue(ProfileRuntimeStatusStore.record(context, packageName, userId,
                    revision, fingerprint, "com.veyravault.space:p0", verifiedStatuses()));

            ProfileRuntimeStatusStore.Snapshot current =
                    ProfileRuntimeStatusStore.read(context, packageName, userId);
            assertTrue(current.exists);
            assertTrue(current.current);
            assertEquals(ProfileFieldRegistry.ApplyStatus.APPLIED,
                    current.statuses.get("localeTag"));
            assertEquals(ProfileFieldRegistry.ApplyStatus.APPLIED,
                    current.statuses.get("timeZoneId"));

            String stored = runtime.getString("runtime_status_json", "");
            assertTrue(stored.contains("profileFingerprint"));
            assertFalse(stored.contains("fr-FR"));
            assertFalse(stored.contains("Europe/Paris"));

            ProfileSettings changedLegacy = new ProfileSettings();
            changedLegacy.localeTag = "de-DE";
            assertTrue(ProfileStore.saveGlobal(context, changedLegacy));
            assertEquals(revision, ProfileDocumentStore.readRevisionStrict(context));

            ProfileRuntimeStatusStore.Snapshot stale =
                    ProfileRuntimeStatusStore.read(context, packageName, userId);
            assertTrue(stale.exists);
            assertFalse(stale.current);
            assertTrue(stale.statuses.isEmpty());
            assertFalse(ProfileRuntimeStatusStore.record(context, packageName, userId,
                    revision, fingerprint, "com.veyravault.space:p0", verifiedStatuses()));
        } finally {
            restorePreferences(documents, documentsBefore);
            restorePreferences(legacy, legacyBefore);
            restorePreferences(runtime, runtimeBefore);
        }
    }

    @Test public void cloneReadbacksRemainScopedAndOnlyEffectiveRuntimeChangesInvalidate() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences documents = context.getSharedPreferences(
                "veyravault_profile_documents_v1", Context.MODE_PRIVATE);
        SharedPreferences legacy = context.getSharedPreferences(
                "veyravault_profiles_v1", Context.MODE_PRIVATE);
        SharedPreferences runtime = context.getSharedPreferences(
                "veyra_profile_runtime_status_v1", Context.MODE_PRIVATE);
        Map<String, ?> documentsBefore = documents.getAll();
        Map<String, ?> legacyBefore = legacy.getAll();
        Map<String, ?> runtimeBefore = runtime.getAll();
        String cloneA = "com.example.clone.alpha";
        String cloneB = "com.example.clone.beta";
        int userA = 21;
        int userB = 22;
        try {
            documents.edit().clear().commit();
            legacy.edit().clear().commit();
            runtime.edit().clear().commit();

            assertTrue(ProfileDocumentStore.saveGlobalField(
                    context, "timeZoneId", "UTC"));
            assertTrue(ProfileDocumentStore.saveCloneField(context, cloneA, userA, "localeTag", "fr-FR"));
            assertTrue(ProfileDocumentStore.saveCloneField(context, cloneB, userB, "localeTag", "de-DE"));

            long revision = ProfileDocumentStore.readRevisionStrict(context);
            ProfileResolver.ResolvedProfile resolvedA =
                    ProfileRuntimeProvider.resolveMergedProfile(context, cloneA, userA, null);
            ProfileResolver.ResolvedProfile resolvedB =
                    ProfileRuntimeProvider.resolveMergedProfile(context, cloneB, userB, null);
            assertTrue(ProfileRuntimeStatusStore.record(context, cloneA, userA, revision,
                    ProfileRuntimeFingerprint.compute(resolvedA), "com.veyravault.space:p0",
                    verifiedStatuses()));
            Map<String, ProfileFieldRegistry.ApplyStatus> failedB = new LinkedHashMap<>();
            failedB.put("localeTag", ProfileFieldRegistry.ApplyStatus.FAILED);
            failedB.put("timeZoneId", ProfileFieldRegistry.ApplyStatus.APPLIED);
            assertTrue(ProfileRuntimeStatusStore.record(context, cloneB, userB, revision,
                    ProfileRuntimeFingerprint.compute(resolvedB), "com.veyravault.space:p1", failedB));

            ProfileRuntimeStatusStore.Snapshot snapshotA =
                    ProfileRuntimeStatusStore.read(context, cloneA, userA);
            ProfileRuntimeStatusStore.Snapshot snapshotB =
                    ProfileRuntimeStatusStore.read(context, cloneB, userB);
            assertTrue(snapshotA.current);
            assertTrue(snapshotB.current);
            assertEquals(ProfileFieldRegistry.ApplyStatus.APPLIED, snapshotA.statuses.get("localeTag"));
            assertEquals(ProfileFieldRegistry.ApplyStatus.FAILED, snapshotB.statuses.get("localeTag"));

            // An Engine-scoped edit changes the global document revision but does not
            // change either effective Locale/Time Zone value verified by this status store.
            assertTrue(ProfileDocumentStore.saveGlobalField(context, "latitude", 35.7d));
            ProfileRuntimeStatusStore.Snapshot afterUnrelatedEditA =
                    ProfileRuntimeStatusStore.read(context, cloneA, userA);
            ProfileRuntimeStatusStore.Snapshot afterUnrelatedEditB =
                    ProfileRuntimeStatusStore.read(context, cloneB, userB);
            assertTrue(afterUnrelatedEditA.current);
            assertTrue(afterUnrelatedEditB.current);
            assertEquals(ProfileFieldRegistry.ApplyStatus.FAILED,
                    afterUnrelatedEditB.statuses.get("localeTag"));

            // Editing Clone A's effective Locale must stale A, but must not stale Clone B.
            assertTrue(ProfileDocumentStore.saveCloneField(
                    context, cloneA, userA, "localeTag", "it-IT"));
            ProfileRuntimeStatusStore.Snapshot staleA =
                    ProfileRuntimeStatusStore.read(context, cloneA, userA);
            ProfileRuntimeStatusStore.Snapshot stillCurrentB =
                    ProfileRuntimeStatusStore.read(context, cloneB, userB);
            assertFalse(staleA.current);
            assertTrue(staleA.statuses.isEmpty());
            assertTrue(stillCurrentB.current);
            assertEquals(ProfileFieldRegistry.ApplyStatus.FAILED,
                    stillCurrentB.statuses.get("localeTag"));

            // The stale runtime must not be re-recorded against an older document revision.
            assertFalse(ProfileRuntimeStatusStore.record(context, cloneA, userA, revision,
                    ProfileRuntimeFingerprint.compute(resolvedA),
                    "com.veyravault.space:p0", verifiedStatuses()));

            // Both Clones inherit Global Time Zone, so changing it invalidates both readbacks.
            assertTrue(ProfileDocumentStore.saveGlobalField(
                    context, "timeZoneId", "Europe/London"));
            ProfileRuntimeStatusStore.Snapshot staleAfterGlobalRuntimeEditA =
                    ProfileRuntimeStatusStore.read(context, cloneA, userA);
            ProfileRuntimeStatusStore.Snapshot staleAfterGlobalRuntimeEditB =
                    ProfileRuntimeStatusStore.read(context, cloneB, userB);
            assertFalse(staleAfterGlobalRuntimeEditA.current);
            assertFalse(staleAfterGlobalRuntimeEditB.current);
            assertTrue(staleAfterGlobalRuntimeEditA.statuses.isEmpty());
            assertTrue(staleAfterGlobalRuntimeEditB.statuses.isEmpty());
        } finally {
            restorePreferences(documents, documentsBefore);
            restorePreferences(legacy, legacyBefore);
            restorePreferences(runtime, runtimeBefore);
        }
    }

    private static Map<String, ProfileFieldRegistry.ApplyStatus> verifiedStatuses() {
        Map<String, ProfileFieldRegistry.ApplyStatus> statuses = new LinkedHashMap<>();
        statuses.put("localeTag", ProfileFieldRegistry.ApplyStatus.APPLIED);
        statuses.put("timeZoneId", ProfileFieldRegistry.ApplyStatus.APPLIED);
        return statuses;
    }

    private static void restorePreferences(SharedPreferences preferences, Map<String, ?> snapshot) {
        SharedPreferences.Editor editor = preferences.edit().clear();
        for (Map.Entry<String, ?> entry : snapshot.entrySet()) {
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
}
