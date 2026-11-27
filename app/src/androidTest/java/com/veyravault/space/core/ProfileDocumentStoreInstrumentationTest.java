package com.veyravault.space.core;

import android.content.Context;
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
 * Tests the additive profile-document store inside the instrumentation APK's
 * private preferences. It deliberately never opens or edits the target app's
 * ProfileStore, CloneStore, accounts, sessions, or app data.
 */
@RunWith(AndroidJUnit4.class)
public class ProfileDocumentStoreInstrumentationTest {
    private static final String PREFS_NAME = "veyravault_profile_documents_v1";
    private static final String DATA_KEY = "documents_json";

    private Context testContext;
    private SharedPreferences testPrefs;
    private Map<String, ?> originalPreferences;

    @Before
    public void setUp() {
        Context instrumentationContext =
                InstrumentationRegistry.getInstrumentation().getContext();
        Context targetContext =
                InstrumentationRegistry.getInstrumentation().getTargetContext();
        testContext = instrumentationContext.getApplicationContext();

        // Do not run this test against the production app's preference namespace.
        assertFalse("Instrumentation preferences must be separate from target app preferences",
                targetContext.getPackageName().equals(testContext.getPackageName()));

        testPrefs = testContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        originalPreferences = testPrefs.getAll();
        assertTrue("Test-only preferences must be isolated before each test",
                testPrefs.edit().clear().commit());
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
            assertTrue("Test-only preferences must be restored", editor.commit());
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
        ExecutorService executor = Executors.newFixedThreadPool(6);
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
