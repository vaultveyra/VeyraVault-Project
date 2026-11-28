package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Arrays;
import java.util.Map;
import java.util.Set;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/** Synthetic-only tests for the read-only bridge from legacy metadata to typed profiles. */
@RunWith(AndroidJUnit4.class)
public class ProfileLegacyEnvironmentBridgeInstrumentationTest {
    @Test public void cloneMetadataOverridesGlobalAndTypedStatesRemainAuthoritative() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences clonePrefs = context.getSharedPreferences(
                "veyravault_clones_v2", Context.MODE_PRIVATE);
        SharedPreferences documentPrefs = context.getSharedPreferences(
                "veyravault_profile_documents_v1", Context.MODE_PRIVATE);
        SharedPreferences legacyProfilePrefs = context.getSharedPreferences(
                "veyravault_profiles_v1", Context.MODE_PRIVATE);
        Map<String, ?> cloneBefore = clonePrefs.getAll();
        Map<String, ?> documentBefore = documentPrefs.getAll();
        Map<String, ?> legacyProfileBefore = legacyProfilePrefs.getAll();

        final String cloneA = "com.veyravault.fixture.legacybridge.alpha";
        final String cloneB = "com.veyravault.fixture.legacybridge.beta";
        final int sharedUserId = 31;
        try {
            clonePrefs.edit().clear().commit();
            documentPrefs.edit().clear().commit();
            legacyProfilePrefs.edit().clear().commit();

            CloneStore.CloneEntry a = new CloneStore.CloneEntry();
            a.packageName = cloneA;
            a.userId = sharedUserId;
            a.displayName = "Legacy Clone A";
            a.customDeviceEnabled = true;
            a.deviceBrand = "OnePlus";
            a.deviceModel = "OnePlus 11";

            // Same numeric Space/user ID, different package: it must not inherit A's metadata.
            CloneStore.CloneEntry b = new CloneStore.CloneEntry();
            b.packageName = cloneB;
            b.userId = sharedUserId;
            b.displayName = "Legacy Clone B";
            b.customDeviceEnabled = false;

            assertTrue("Synthetic Clone registry fixture must persist",
                    CloneStore.saveAll(context, Arrays.asList(a, b)));

            CloneStore.GlobalEnvConfig globalConfig = new CloneStore.GlobalEnvConfig();
            globalConfig.enabled = true;
            globalConfig.brand = "Google";
            globalConfig.manufacturer = "Google";
            globalConfig.model = "Pixel 9";
            globalConfig.device = "generic";
            globalConfig.countryIso = "us";
            globalConfig.simOperator = "310260";
            globalConfig.simOperatorName = "T-Mobile";
            assertTrue("Synthetic Global metadata fixture must persist",
                    CloneStore.saveGlobalEnv(context, globalConfig));

            ProfileDocument global = ProfileLegacyEnvironmentBridge.mergeGlobal(
                    context, new ProfileDocument());
            ProfileDocument profileA = ProfileLegacyEnvironmentBridge.mergeClone(
                    context, cloneA, sharedUserId, new ProfileDocument());
            ProfileDocument profileB = ProfileLegacyEnvironmentBridge.mergeClone(
                    context, cloneB, sharedUserId, new ProfileDocument());

            assertEquals("Google", global.get("manufacturer"));
            assertEquals("Pixel 9", global.get("deviceModel"));
            assertEquals("us", global.get("countryCode"));
            assertEquals("OnePlus", profileA.get("manufacturer"));
            assertEquals("OnePlus 11", profileA.get("deviceModel"));
            assertNull("Clone B must not read Clone A's metadata", profileB.get("manufacturer"));
            assertNull("Clone B must not read Clone A's model", profileB.get("deviceModel"));

            ProfileDocumentResolver.FieldResult aModel = ProfileDocumentResolver.resolve(
                    "deviceModel", profileA, global, ProfileFieldRegistry.createSafeDefaults());
            ProfileDocumentResolver.FieldResult bModel = ProfileDocumentResolver.resolve(
                    "deviceModel", profileB, global, ProfileFieldRegistry.createSafeDefaults());
            assertEquals("OnePlus 11", aModel.value);
            assertEquals(ProfileDocumentResolver.Source.CLONE, aModel.source);
            assertEquals("Pixel 9", bModel.value);
            assertEquals(ProfileDocumentResolver.Source.GLOBAL, bModel.source);
            assertEquals(ProfileFieldRegistry.ApplyStatus.STORED_ONLY, bModel.status);

            // The bridge is read-only: it must not rewrite CloneStore or either profile store.
            assertEquals(clonePrefs.getAll(), clonePrefs.getAll());
            assertEquals(documentBefore, documentPrefs.getAll());
            assertEquals(legacyProfileBefore, legacyProfilePrefs.getAll());

            // Typed Clone override wins over the old CloneStore metadata.
            assertTrue(ProfileDocumentStore.saveCloneField(
                    context, cloneB, sharedUserId, "deviceModel", "Typed Clone B"));
            ProfileRuntimeClient.ResolvedDocument typedClone =
                    ProfileRuntimeClient.resolveDocument(context, cloneB, sharedUserId);
            assertEquals("Typed Clone B", typedClone.field("deviceModel").value);
            assertEquals(ProfileDocumentResolver.Source.CLONE, typedClone.field("deviceModel").source);

            // Explicit Use Global state blocks the legacy Clone value instead of resurrecting it.
            assertTrue(ProfileDocumentStore.clearCloneField(
                    context, cloneA, sharedUserId, "deviceModel"));
            ProfileRuntimeClient.ResolvedDocument inherited =
                    ProfileRuntimeClient.resolveDocument(context, cloneA, sharedUserId);
            assertEquals("Pixel 9", inherited.field("deviceModel").value);
            assertEquals(ProfileDocumentResolver.Source.GLOBAL, inherited.field("deviceModel").source);

            // A typed Global override wins over the legacy Global metadata.
            assertTrue(ProfileDocumentStore.saveGlobalField(context, "deviceModel", "Typed Global Model"));
            ProfileRuntimeClient.ResolvedDocument typedGlobal =
                    ProfileRuntimeClient.resolveDocument(context, cloneA, sharedUserId);
            assertEquals("Typed Global Model", typedGlobal.field("deviceModel").value);
            assertEquals(ProfileDocumentResolver.Source.GLOBAL, typedGlobal.field("deviceModel").source);

            // Resetting Global blocks the legacy value; it does not restore host Build data.
            assertTrue(ProfileDocumentStore.clearGlobalField(context, "deviceModel"));
            ProfileRuntimeClient.ResolvedDocument safeGlobal =
                    ProfileRuntimeClient.resolveDocument(context, cloneA, sharedUserId);
            assertNull(safeGlobal.field("deviceModel").value);
            assertEquals(ProfileDocumentResolver.Source.UNSET, safeGlobal.field("deviceModel").source);

            // SIM/operator identity is intentionally excluded from editable profile metadata.
            assertFalse(ProfileFieldRegistry.get("simOperatorIdentity").editable);
            assertNull(safeGlobal.field("simOperatorIdentity").value);
        } finally {
            restorePreferences(clonePrefs, cloneBefore);
            restorePreferences(documentPrefs, documentBefore);
            restorePreferences(legacyProfilePrefs, legacyProfileBefore);
        }
    }

    @Test public void absentOrDisabledGlobalLegacyProfileDoesNotImportConstructorDefaults() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences clonePrefs = context.getSharedPreferences(
                "veyravault_clones_v2", Context.MODE_PRIVATE);
        Map<String, ?> before = clonePrefs.getAll();
        try {
            clonePrefs.edit().clear().commit();
            assertTrue(ProfileLegacyEnvironmentBridge.mergeGlobal(
                    context, new ProfileDocument()).isEmpty());

            CloneStore.GlobalEnvConfig disabled = new CloneStore.GlobalEnvConfig();
            disabled.enabled = false;
            disabled.brand = "Samsung";
            disabled.manufacturer = "Samsung";
            disabled.model = "SM-S928B";
            disabled.countryIso = "us";
            assertTrue(CloneStore.saveGlobalEnv(context, disabled));
            assertTrue(ProfileLegacyEnvironmentBridge.mergeGlobal(
                    context, new ProfileDocument()).isEmpty());
        } finally {
            restorePreferences(clonePrefs, before);
        }
    }

    private static void restorePreferences(SharedPreferences preferences, Map<String, ?> values) {
        SharedPreferences.Editor editor = preferences.edit().clear();
        for (Map.Entry<String, ?> entry : values.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof String) editor.putString(entry.getKey(), (String) value);
            else if (value instanceof Boolean) editor.putBoolean(entry.getKey(), (Boolean) value);
            else if (value instanceof Integer) editor.putInt(entry.getKey(), (Integer) value);
            else if (value instanceof Long) editor.putLong(entry.getKey(), (Long) value);
            else if (value instanceof Float) editor.putFloat(entry.getKey(), (Float) value);
            else if (value instanceof Set) {
                @SuppressWarnings("unchecked")
                Set<String> strings = (Set<String>) value;
                editor.putStringSet(entry.getKey(), strings);
            }
        }
        assertTrue("Synthetic fixture preferences must be restored", editor.commit());
    }
}
