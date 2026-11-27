package com.veyravault.space.core;

import android.content.Context;
import android.content.ContextWrapper;
import android.content.SharedPreferences;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.json.JSONObject;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/**
 * Tests the additive profile-document store through real Android SharedPreferences.
 * The production preference name is redirected to a dedicated test-only file;
 * ProfileStore, CloneStore, accounts, sessions and production profile data stay untouched.
 */
@RunWith(AndroidJUnit4.class)
public class ProfileDocumentStoreInstrumentationTest {
    private static final String STORE_PREFS_NAME = "veyravault_profile_documents_v1";
    private static final String TEST_PREFS_NAME = STORE_PREFS_NAME + "_instrumentation";
    private static final String DATA_KEY = "documents_json";

    private Context testContext;
    private SharedPreferences testPrefs;
    private Map<String, ?> originalPreferences;

    @Before
    public void setUp() {
        Context targetContext =
                InstrumentationRegistry.getInstrumentation().getTargetContext();
        assertNotNull("Target application Context must be available", targetContext);

        // Android's instrumentation-package data directory is not writable in the
        // current emulator harness. Keep the real Android SharedPreferences backend,
        // but redirect the store's fixed production filename to a dedicated test file.
        // Returning this wrapper from getApplicationContext() retains the redirect when
        // ProfileDocumentStore resolves its storage Context.
        testContext = new ContextWrapper(targetContext) {
            @Override
            public Context getApplicationContext() {
                return this;
            }

            @Override
            public SharedPreferences getSharedPreferences(String name, int mode) {
                String isolatedName = STORE_PREFS_NAME.equals(name) ? TEST_PREFS_NAME : name;
                return super.getSharedPreferences(isolatedName, mode);
            }
        };

        testPrefs = targetContext.getSharedPreferences(TEST_PREFS_NAME, Context.MODE_PRIVATE);
        originalPreferences = testPrefs.getAll();
        assertTrue("Test-only preferences must be cleared successfully",
                testPrefs.edit().clear().commit());
        assertTrue("Test-only preferences must be empty before each test",
                testPrefs.getAll().isEmpty());
    }

    @After
    public void tearDown() {
        if (testPrefs != null && originalPreferences != null) {
            SharedPreferences.Editor editor = testPrefs.edit().clear();
            for (Map.Entry<String, ?> entry : originalPreferences.entrySet()) {
                Object value = entry.getValue();
                String key = entry.getKey();
                if (value instanceof String) editor.putString(key, (String) value);
                else if (value instanceof Boolean) editor.putBoolean(key, (Boolean) value);
                else if (value instanceof Integer) editor.putInt(key, (Integer) value);
                else if (value instanceof Long) editor.putLong(key, (Long) value);
                else if (value instanceof Float) editor.putFloat(key, (Float) value);
                else if (value instanceof Set) {
                    @SuppressWarnings("unchecked")
                    Set<String> strings = new HashSet<>((Set<String>) value);
                    editor.putStringSet(key, strings);
                }
            }
            assertTrue("Test-only preferences must be restored successfully", editor.commit());
            assertEquals("Test-only preferences must be restored",
                    originalPreferences, testPrefs.getAll());
        }
    }

    @Test
    public void everyEditableRegistryFieldRoundTripsAndCloneDocumentsRemainIndependent()
            throws Exception {
        ProfileDocument global = new ProfileDocument();
        Map<String, Object> expectedGlobal = new java.util.LinkedHashMap<>();
        for (ProfileFieldRegistry.Field field : ProfileFieldRegistry.all()) {
            if (!field.editable) continue;
            Object value = sampleValue(field);
            assertTrue("Registry field must accept its typed sample: " + field.key,
                    global.put(field.key, value));
            expectedGlobal.put(field.key, value);
        }
        assertTrue("All editable Global fields must persist",
                ProfileDocumentStore.saveGlobalDocument(testContext, global));
        ProfileDocument loadedGlobal = ProfileDocumentStore.readGlobalStrict(testContext);
        assertEquals(expectedGlobal.size(), loadedGlobal.values().size());
        for (Map.Entry<String, Object> entry : expectedGlobal.entrySet()) {
            assertEquals("Global field round-trip failed: " + entry.getKey(),
                    entry.getValue(), loadedGlobal.get(entry.getKey()));
        }

        String cloneA = "com.veyravault.fixture.registry-a";
        String cloneB = "com.veyravault.fixture.registry-b";
        ProfileDocument a = new ProfileDocument();
        ProfileDocument b = new ProfileDocument();
        assertTrue(a.put("deviceLabel", "Clone-A-Display"));
        assertTrue(a.put("timeZoneId", "America/New_York"));
        assertTrue(b.put("deviceLabel", "Clone-B-Display"));
        assertTrue(b.put("timeZoneId", "Asia/Tokyo"));
        assertTrue(ProfileDocumentStore.saveCloneDocument(testContext, cloneA, 101, a));
        assertTrue(ProfileDocumentStore.saveCloneDocument(testContext, cloneB, 102, b));

        ProfileDocument loadedA = ProfileDocumentStore.readCloneStrict(testContext, cloneA, 101);
        ProfileDocument loadedB = ProfileDocumentStore.readCloneStrict(testContext, cloneB, 102);
        assertEquals("Clone-A-Display", loadedA.get("deviceLabel"));
        assertEquals("America/New_York", loadedA.get("timeZoneId"));
        assertEquals("Clone-B-Display", loadedB.get("deviceLabel"));
        assertEquals("Asia/Tokyo", loadedB.get("timeZoneId"));
        assertEquals("Global data must remain independent",
                "UTC", loadedGlobal.get("timeZoneId"));
        assertEquals(ProfileFieldRegistry.all().size(),
                ProfileDocumentResolver.resolveAll(loadedA, loadedGlobal).size());
    }

    private static Object sampleValue(ProfileFieldRegistry.Field field) {
        if ("localeTag".equals(field.key)) return "en-US";
        if ("timeZoneId".equals(field.key)) return "UTC";
        if ("countryCode".equals(field.key)) return "US";
        if ("currencyCode".equals(field.key)) return "USD";
        if ("latitude".equals(field.key) || "longitude".equals(field.key)) return Double.valueOf(0.0d);
        switch (field.type) {
            case BOOLEAN: return Boolean.FALSE;
            case INTEGER: return Long.valueOf(123L);
            case DECIMAL: return Double.valueOf(1.25d);
            case STRING: return "fixture-" + field.key;
            default: throw new AssertionError("Unknown field type: " + field.key);
        }
    }

    @Test
    public void globalAndCloneDocumentsRoundTripIndependentlyWithPerFieldResolution()
            throws Exception {
        String cloneA = "com.veyravault.fixture.clonea";
        String cloneB = "com.veyravault.fixture.cloneb";

        assertTrue(ProfileDocumentStore.saveGlobalField(testContext, "localeTag", "fr-FR"));
        assertTrue(ProfileDocumentStore.saveGlobalField(
                testContext, "timeZoneId", "Europe/Berlin"));
        assertTrue(ProfileDocumentStore.saveCloneField(
                testContext, cloneA, 41, "timeZoneId", "Asia/Tokyo"));

        ProfileDocument global = ProfileDocumentStore.readGlobalStrict(testContext);
        ProfileDocument a = ProfileDocumentStore.readCloneStrict(testContext, cloneA, 41);
        ProfileDocument b = ProfileDocumentStore.readCloneStrict(testContext, cloneB, 42);

        assertEquals("fr-FR", global.get("localeTag"));
        assertEquals("Europe/Berlin", global.get("timeZoneId"));
        assertEquals("Asia/Tokyo", a.get("timeZoneId"));
        assertFalse("Clone A must not contain Global-only locale as an override",
                a.contains("localeTag"));
        assertTrue("Clone B must not inherit Clone A's private document",
                b.isEmpty());

        Map<String, ProfileDocumentResolver.FieldResult> resolvedA =
                ProfileDocumentResolver.resolveAll(a, global);
        Map<String, ProfileDocumentResolver.FieldResult> resolvedB =
                ProfileDocumentResolver.resolveAll(b, global);

        assertEquals("Asia/Tokyo", resolvedA.get("timeZoneId").value);
        assertEquals(ProfileDocumentResolver.Source.CLONE,
                resolvedA.get("timeZoneId").source);
        assertEquals("fr-FR", resolvedA.get("localeTag").value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL,
                resolvedA.get("localeTag").source);
        assertEquals("Europe/Berlin", resolvedB.get("timeZoneId").value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL,
                resolvedB.get("timeZoneId").source);
        assertTrue("Revision must advance for each committed write",
                ProfileDocumentStore.readRevisionStrict(testContext) >= 3L);
    }

    @Test
    public void clearingCloneFieldInheritsGlobalAndClearingGlobalFieldSelectsSafeDefault()
            throws Exception {
        String clone = "com.veyravault.fixture.reset";
        assertTrue(ProfileDocumentStore.saveGlobalField(
                testContext, "timeZoneId", "Europe/Paris"));
        assertTrue(ProfileDocumentStore.saveCloneField(
                testContext, clone, 7, "timeZoneId", "Asia/Tokyo"));

        assertTrue(ProfileDocumentStore.clearCloneField(
                testContext, clone, 7, "timeZoneId"));
        ProfileDocument cloneAfterReset =
                ProfileDocumentStore.readCloneStrict(testContext, clone, 7);
        assertEquals(ProfileDocument.FieldState.INHERIT_GLOBAL,
                cloneAfterReset.state("timeZoneId"));
        ProfileDocumentResolver.FieldResult inherited =
                ProfileDocumentResolver.resolve("timeZoneId", cloneAfterReset,
                        ProfileDocumentStore.readGlobalStrict(testContext),
                        ProfileFieldRegistry.createSafeDefaults());
        assertEquals("Europe/Paris", inherited.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, inherited.source);

        assertTrue(ProfileDocumentStore.clearGlobalField(testContext, "timeZoneId"));
        ProfileDocument globalAfterClear =
                ProfileDocumentStore.readGlobalStrict(testContext);
        assertEquals(ProfileDocument.FieldState.SAFE_DEFAULT,
                globalAfterClear.state("timeZoneId"));
        ProfileDocumentResolver.FieldResult safe =
                ProfileDocumentResolver.resolve("timeZoneId", cloneAfterReset,
                        globalAfterClear, ProfileFieldRegistry.createSafeDefaults());
        assertEquals("UTC", safe.value);
        assertEquals(ProfileDocumentResolver.Source.SAFE_DEFAULT, safe.source);
    }

    @Test
    public void cloneSafeDefaultStatePersistsAndOverridesGlobal() throws Exception {
        String clone = "com.veyravault.fixture.clone-safe-default";
        assertTrue(ProfileDocumentStore.saveGlobalField(
                testContext, "timeZoneId", "America/New_York"));

        ProfileDocument safeOverride = new ProfileDocument();
        safeOverride.markSafeDefault("timeZoneId");
        assertTrue("Clone Safe Default state must persist",
                ProfileDocumentStore.saveCloneDocument(testContext, clone, 12, safeOverride));

        ProfileDocument loadedSafe = ProfileDocumentStore.readCloneStrict(testContext, clone, 12);
        assertEquals(ProfileDocument.FieldState.SAFE_DEFAULT,
                loadedSafe.state("timeZoneId"));
        ProfileDocumentResolver.FieldResult safe = ProfileDocumentResolver.resolve(
                "timeZoneId", loadedSafe, ProfileDocumentStore.readGlobalStrict(testContext),
                ProfileFieldRegistry.createSafeDefaults());
        assertEquals("UTC", safe.value);
        assertEquals(ProfileDocumentResolver.Source.SAFE_DEFAULT, safe.source);

        ProfileDocument inheritGlobal = new ProfileDocument();
        inheritGlobal.markInheritGlobal("timeZoneId");
        assertTrue("Clone Inherit Global state must remain persistable",
                ProfileDocumentStore.saveCloneDocument(testContext, clone, 12, inheritGlobal));
        ProfileDocument loadedInherited = ProfileDocumentStore.readCloneStrict(testContext, clone, 12);
        assertEquals(ProfileDocument.FieldState.INHERIT_GLOBAL,
                loadedInherited.state("timeZoneId"));
        ProfileDocumentResolver.FieldResult inherited = ProfileDocumentResolver.resolve(
                "timeZoneId", loadedInherited, ProfileDocumentStore.readGlobalStrict(testContext),
                ProfileFieldRegistry.createSafeDefaults());
        assertEquals("America/New_York", inherited.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, inherited.source);
    }

    @Test
    public void semanticInvalidityFallsBackForOnlyThatField() throws Exception {
        String clone = "com.veyravault.fixture.invalid";
        JSONObject global = new JSONObject();
        global.put("localeTag", "de-DE");
        JSONObject cloneDocument = new JSONObject();
        cloneDocument.put("localeTag", "not a valid locale tag");
        cloneDocument.put("timeZoneId", "Asia/Tokyo");
        JSONObject clones = new JSONObject();
        clones.put(clone + "#9", cloneDocument);
        JSONObject root = new JSONObject();
        root.put("schemaVersion", 1);
        root.put("revision", 12L);
        root.put("updatedAt", 100L);
        root.put("global", global);
        root.put("clones", clones);
        assertTrue(testPrefs.edit().putString(DATA_KEY, root.toString()).commit());

        ProfileDocument loadedClone =
                ProfileDocumentStore.readCloneStrict(testContext, clone, 9);
        ProfileDocument loadedGlobal =
                ProfileDocumentStore.readGlobalStrict(testContext);
        assertTrue("Invalid stored field presence must be retained as an invalid marker",
                loadedClone.isInvalid("localeTag"));

        ProfileDocumentResolver.FieldResult locale =
                ProfileDocumentResolver.resolve("localeTag", loadedClone, loadedGlobal,
                        ProfileFieldRegistry.createSafeDefaults());
        ProfileDocumentResolver.FieldResult zone =
                ProfileDocumentResolver.resolve("timeZoneId", loadedClone, loadedGlobal,
                        ProfileFieldRegistry.createSafeDefaults());
        assertEquals("de-DE", locale.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, locale.source);
        assertEquals("Asia/Tokyo", zone.value);
        assertEquals(ProfileDocumentResolver.Source.CLONE, zone.source);
    }

    @Test
    public void malformedRootAndStructurallyInvalidCloneAreRejectedWithoutOverwrite()
            throws Exception {
        String malformed = "{not-json";
        assertTrue(testPrefs.edit().putString(DATA_KEY, malformed).commit());
        assertFalse(ProfileDocumentStore.saveGlobalField(
                testContext, "localeTag", "en-US"));
        assertEquals("Malformed root must remain untouched", malformed,
                testPrefs.getString(DATA_KEY, null));

        String clone = "com.veyravault.fixture.corrupt";
        JSONObject clones = new JSONObject();
        clones.put(clone + "#3", "not-an-object");
        JSONObject root = new JSONObject();
        root.put("schemaVersion", 1);
        root.put("revision", 4L);
        root.put("updatedAt", 2L);
        root.put("clones", clones);
        String corruptClonePayload = root.toString();
        assertTrue(testPrefs.edit().putString(DATA_KEY, corruptClonePayload).commit());

        assertFalse(ProfileDocumentStore.saveCloneField(
                testContext, clone, 3, "timeZoneId", "UTC"));
        assertEquals("Structurally invalid Clone document must not be overwritten",
                corruptClonePayload, testPrefs.getString(DATA_KEY, null));
    }

    @Test
    public void invalidLocationTelemetryIsRejectedBeforePersistence() throws Exception {
        long before = ProfileDocumentStore.readRevisionStrict(testContext);
        assertFalse(ProfileDocumentStore.saveGlobalField(testContext, "locationAccuracy", -1.0d));
        assertFalse(ProfileDocumentStore.saveGlobalField(testContext, "locationSpeed", -1.0d));
        assertFalse(ProfileDocumentStore.saveGlobalField(testContext, "locationBearing", 361.0d));
        assertFalse(ProfileDocumentStore.saveGlobalField(testContext, "locationTimestamp", -1L));
        assertEquals("Rejected telemetry values must not advance the document revision",
                before, ProfileDocumentStore.readRevisionStrict(testContext));
        assertTrue(ProfileDocumentStore.saveGlobalField(testContext, "locationBearing", 360.0d));
        assertEquals(Double.valueOf(360.0d),
                ProfileDocumentStore.readGlobalStrict(testContext).get("locationBearing"));
    }

    @Test
    public void restrictedServiceOwnedAndObservedOnlyValuesAreRejectedWithoutRevisionChange()
            throws Exception {
        assertFalse(ProfileDocumentStore.saveGlobalField(
                testContext, "imei", "not-a-real-id"));
        assertFalse(ProfileDocumentStore.saveGlobalField(
                testContext, "accountId", "fixture-account"));
        assertFalse(ProfileDocumentStore.saveGlobalField(
                testContext, "publicIpAddress", "203.0.113.7"));
        assertEquals(0L, ProfileDocumentStore.readRevisionStrict(testContext));
        assertTrue("No rejected profile input may be persisted",
                ProfileDocumentStore.readGlobalStrict(testContext).isEmpty());
    }

    @Test
    public void unknownFutureKeysSurviveRegisteredFieldUpdates() throws Exception {
        String clone = "com.veyravault.fixture.forwardcompat";
        JSONObject cloneDocument = new JSONObject();
        cloneDocument.put("futureFieldFromNewerSchema", "preserve-me");
        JSONObject clones = new JSONObject();
        clones.put(clone + "#5", cloneDocument);
        JSONObject root = new JSONObject();
        root.put("schemaVersion", 1);
        root.put("revision", 1L);
        root.put("updatedAt", 1L);
        root.put("clones", clones);
        assertTrue(testPrefs.edit().putString(DATA_KEY, root.toString()).commit());

        assertTrue(ProfileDocumentStore.saveCloneField(
                testContext, clone, 5, "localeTag", "it-IT"));

        JSONObject persisted = new JSONObject(testPrefs.getString(DATA_KEY, ""));
        JSONObject savedClone = persisted.getJSONObject("clones")
                .getJSONObject(clone + "#5");
        assertEquals("preserve-me", savedClone.getString("futureFieldFromNewerSchema"));
        assertEquals("it-IT", savedClone.getString("localeTag"));
    }

    @Test
    public void concurrentCloneFieldWritesDoNotLoseCommittedFields() throws Exception {
        final String clone = "com.veyravault.fixture.concurrent";
        final String[][] fields = new String[][] {
                {"countryCode", "US"},
                {"regionCode", "CA"},
                {"cityName", "Boston"},
                {"currencyCode", "USD"},
                {"dateFormat", "MM/dd/yyyy"},
                {"timeFormat", "12-hour"},
                {"measurementSystem", "US"},
                {"distanceUnit", "mi"},
                {"temperatureUnit", "F"},
                {"weightUnit", "lb"},
                {"lengthUnit", "in"},
                {"weekStart", "Sunday"}
        };
        ExecutorService executor = Executors.newFixedThreadPool(fields.length);
        final CountDownLatch ready = new CountDownLatch(fields.length);
        final CountDownLatch start = new CountDownLatch(1);
        List<Future<Boolean>> writes = new ArrayList<>();

        try {
            for (final String[] field : fields) {
                writes.add(executor.submit(() -> {
                    ready.countDown();
                    if (!start.await(10, TimeUnit.SECONDS)) return false;
                    return ProfileDocumentStore.saveCloneField(
                            testContext, clone, 11, field[0], field[1]);
                }));
            }

            assertTrue("Concurrent writers must reach the start gate",
                    ready.await(10, TimeUnit.SECONDS));
            start.countDown();
            for (Future<Boolean> write : writes) {
                assertTrue("Every serialized field update must commit",
                        write.get(15, TimeUnit.SECONDS));
            }
        } finally {
            start.countDown();
            executor.shutdownNow();
            assertTrue("Writer pool must terminate",
                    executor.awaitTermination(10, TimeUnit.SECONDS));
        }

        ProfileDocument stored =
                ProfileDocumentStore.readCloneStrict(testContext, clone, 11);
        for (String[] field : fields) {
            assertEquals("Concurrent update lost field " + field[0],
                    field[1], stored.get(field[0]));
        }
        assertNotNull("Committed revision must be readable",
                ProfileDocumentStore.readRevisionStrict(testContext));
        assertEquals((long) fields.length,
                ProfileDocumentStore.readRevisionStrict(testContext));
    }
}
