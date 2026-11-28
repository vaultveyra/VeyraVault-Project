package com.veyravault.space.core;

import android.content.Context;
import android.content.ContextWrapper;
import android.content.SharedPreferences;
import android.os.Looper;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AsyncCloneRepositoryInstrumentationTest {
    private Context context;
    private Context rawContext;
    private SharedPreferences preferences;
    private SharedPreferences profilePreferences;
    private SharedPreferences profileDocumentPreferences;

    @Before public void setUp() {
        rawContext = ApplicationProvider.getApplicationContext();
        // All repository/store preferences are redirected into test-only namespaces.
        // Instrumentation must never clear or overwrite a user's real Clone/session data.
        context = new IsolatedPreferencesContext(rawContext);
        preferences = context.getSharedPreferences("veyravault_clones_v2", Context.MODE_PRIVATE);
        profilePreferences = context.getSharedPreferences("veyravault_profiles_v1", Context.MODE_PRIVATE);
        profileDocumentPreferences = context.getSharedPreferences("veyravault_profile_documents_v1", Context.MODE_PRIVATE);
        preferences.edit().clear().commit();
        profilePreferences.edit().clear().commit();
        profileDocumentPreferences.edit().clear().commit();
    }

    @After public void tearDown() {
        preferences.edit().clear().commit();
        profilePreferences.edit().clear().commit();
        profileDocumentPreferences.edit().clear().commit();
    }

    @Test public void queuedUpsertThenReadPreservesSubmissionOrder() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(2);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> write = new AtomicReference<>();
        AtomicReference<AsyncCloneRepository.Result<List<CloneStore.CloneEntry>>> read = new AtomicReference<>();

        CloneStore.CloneEntry entry = cloneEntry("com.example.order", 0);
        repository.upsertClone(entry, result -> { write.set(result); done.countDown(); });
        repository.loadClones(result -> { read.set(result); done.countDown(); });

        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertTrue(write.get().isSuccess());
        assertTrue(read.get().isSuccess());
        assertEquals(1, read.get().getValue().size());
        assertEquals("com.example.order", read.get().getValue().get(0).packageName);
        repository.close();
    }

    @Test public void callbacksAreDispatchedOnMainLooper() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<Boolean> mainThread = new AtomicReference<>(false);
        repository.loadClones(result -> {
            mainThread.set(Looper.myLooper() == Looper.getMainLooper());
            done.countDown();
        });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertTrue(mainThread.get());
        repository.close();
    }

    @Test public void returnedMutableRecordsDoNotMutatePersistedState() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch first = new CountDownLatch(1);
        repository.upsertClone(cloneEntry("com.example.copy", 1), result -> {
            assertTrue(result.isSuccess());
            first.countDown();
        });
        assertTrue(first.await(10, TimeUnit.SECONDS));

        CountDownLatch second = new CountDownLatch(1);
        repository.loadClones(result -> {
            assertTrue(result.isSuccess());
            result.getValue().get(0).displayName = "tampered";
            result.getValue().get(0).deniedPermissions.add("tampered.permission");
            second.countDown();
        });
        assertTrue(second.await(10, TimeUnit.SECONDS));

        CountDownLatch third = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<List<CloneStore.CloneEntry>>> persisted = new AtomicReference<>();
        repository.loadClones(result -> { persisted.set(result); third.countDown(); });
        assertTrue(third.await(10, TimeUnit.SECONDS));
        assertEquals("Original", persisted.get().getValue().get(0).displayName);
        assertFalse(persisted.get().getValue().get(0).deniedPermissions.contains("tampered.permission"));
        repository.close();
    }

    @Test public void corruptRegistryIsReturnedAsTypedFailure() throws Exception {
        preferences.edit().putString("clones_json", "{not-json").commit();
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<List<CloneStore.CloneEntry>>> resultRef = new AtomicReference<>();
        repository.loadClones(result -> { resultRef.set(result); done.countDown(); });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertFalse(resultRef.get().isSuccess());
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, resultRef.get().getFailure());
        assertEquals("{not-json", preferences.getString("clones_json", null));
        repository.close();
    }

    @Test public void closedRepositoryRejectsNewWorkExplicitly() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        repository.close();
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<List<CloneStore.CloneEntry>>> resultRef = new AtomicReference<>();
        repository.loadClones(result -> { resultRef.set(result); done.countDown(); });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.EXECUTOR_CLOSED, resultRef.get().getFailure());
    }


    @Test public void profileMigrationDoesNotMarkCorruptRegistryAsImported() {
        preferences.edit().putString("clones_json",
                "[{\"pkg\":\"com.example.bad\",\"uid\":0,\"gpsOn\":\"true\"}]").commit();
        assertFalse(ProfileStore.migrateLegacyLocationSettings(context));
        assertFalse(profilePreferences.getBoolean("legacy_location_import_v1", false));
        assertTrue(preferences.getString("clones_json", "").contains("\"gpsOn\":\"true\""));
    }


    @Test public void collapsedSpacesAndMasterGpsRoundTripThroughRepository() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch writes = new CountDownLatch(2);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> collapsedWrite = new AtomicReference<>();
        AtomicReference<AsyncCloneRepository.Result<Boolean>> masterWrite = new AtomicReference<>();
        repository.setSpaceCollapsed(3, true, result -> { collapsedWrite.set(result); writes.countDown(); });
        repository.setMasterMockGpsEnabled(false, result -> { masterWrite.set(result); writes.countDown(); });
        assertTrue(writes.await(10, TimeUnit.SECONDS));
        assertTrue(collapsedWrite.get().isSuccess());
        assertTrue(masterWrite.get().isSuccess());

        CountDownLatch reads = new CountDownLatch(2);
        AtomicReference<AsyncCloneRepository.Result<java.util.Set<Integer>>> collapsedRead = new AtomicReference<>();
        AtomicReference<AsyncCloneRepository.Result<Boolean>> masterRead = new AtomicReference<>();
        repository.loadCollapsedSpaces(result -> { collapsedRead.set(result); reads.countDown(); });
        repository.loadMasterMockGpsEnabled(result -> { masterRead.set(result); reads.countDown(); });
        assertTrue(reads.await(10, TimeUnit.SECONDS));
        assertTrue(collapsedRead.get().isSuccess());
        assertTrue(collapsedRead.get().getValue().contains(3));
        assertTrue(masterRead.get().isSuccess());
        assertFalse(masterRead.get().getValue());
        repository.close();
    }

    @Test public void globalEnvironmentAndProfilesRoundTrip() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CloneStore.GlobalEnvConfig config = new CloneStore.GlobalEnvConfig();
        config.brand = "google";
        config.manufacturer = "Google";
        config.model = "Pixel 9";
        config.device = "tokay";
        config.countryIso = "gb";
        config.simOperator = "23415";
        config.simOperatorName = "Vodafone";
        CountDownLatch envSaved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> envSaveResult = new AtomicReference<>();
        repository.saveGlobalEnvironment(config, result -> { envSaveResult.set(result); envSaved.countDown(); });
        assertTrue(envSaved.await(10, TimeUnit.SECONDS));
        assertTrue(envSaveResult.get().isSuccess());

        CountDownLatch envLoaded = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.GlobalEnvConfig>> envLoadResult = new AtomicReference<>();
        repository.loadGlobalEnvironment(result -> { envLoadResult.set(result); envLoaded.countDown(); });
        assertTrue(envLoaded.await(10, TimeUnit.SECONDS));
        assertEquals("Pixel 9", envLoadResult.get().getValue().model);
        assertEquals("gb", envLoadResult.get().getValue().countryIso);

        ProfileSettings profile = new ProfileSettings();
        profile.localeTag = "en-GB";
        profile.timeZoneId = "Europe/London";
        profile.locationEnabled = Boolean.FALSE;
        CountDownLatch profileSaved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> profileSaveResult = new AtomicReference<>();
        repository.saveGlobalProfile(profile, result -> { profileSaveResult.set(result); profileSaved.countDown(); });
        assertTrue(profileSaved.await(10, TimeUnit.SECONDS));
        assertTrue(profileSaveResult.get().isSuccess());

        CountDownLatch profileLoaded = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<ProfileSettings>> profileLoadResult = new AtomicReference<>();
        repository.loadGlobalProfile(result -> { profileLoadResult.set(result); profileLoaded.countDown(); });
        assertTrue(profileLoaded.await(10, TimeUnit.SECONDS));
        assertEquals("en-GB", profileLoadResult.get().getValue().localeTag);
        assertEquals(Boolean.FALSE, profileLoadResult.get().getValue().locationEnabled);
        repository.close();
    }


    @Test public void globalLocaleAndTimeZoneDefaultsAreFieldScopedAndPreserveCloneOverrides() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        try {
            ProfileSettings cloneOverride = new ProfileSettings();
            cloneOverride.localeTag = "de-DE";
            cloneOverride.timeZoneId = "Europe/Berlin";
            AsyncCloneRepository.Result<Boolean> cloneSaved = awaitResult(
                    callback -> repository.saveCloneProfile("com.example.globaldefaults", 7,
                            cloneOverride, callback));
            assertTrue(cloneSaved.isSuccess());

            ProfileSettings globalLocale = new ProfileSettings();
            globalLocale.localeTag = "fr-FR";
            AsyncCloneRepository.Result<Boolean> localeSaved = awaitResult(
                    callback -> repository.saveGlobalProfile(globalLocale, callback));
            assertTrue(localeSaved.isSuccess());

            ProfileSettings globalTimeZone = new ProfileSettings();
            globalTimeZone.timeZoneId = "Europe/Paris";
            AsyncCloneRepository.Result<Boolean> timeZoneSaved = awaitResult(
                    callback -> repository.saveGlobalProfile(globalTimeZone, callback));
            assertTrue(timeZoneSaved.isSuccess());

            AsyncCloneRepository.Result<ProfileSettings> globalRead = awaitResult(
                    repository::loadGlobalProfile);
            AsyncCloneRepository.Result<ProfileSettings> cloneRead = awaitResult(
                    callback -> repository.loadCloneProfile("com.example.globaldefaults", 7, callback));
            assertTrue(globalRead.isSuccess());
            assertTrue(cloneRead.isSuccess());
            assertEquals("fr-FR", globalRead.getValue().localeTag);
            assertEquals("Europe/Paris", globalRead.getValue().timeZoneId);
            assertEquals("de-DE", cloneRead.getValue().localeTag);
            assertEquals("Europe/Berlin", cloneRead.getValue().timeZoneId);

            ProfileSettings system = new ProfileSettings();
            system.localeTag = "en-US";
            system.timeZoneId = "UTC";
            ProfileResolver.ResolvedProfile cloneEffective =
                    ProfileResolver.resolve(cloneRead.getValue(), globalRead.getValue(), system);
            assertEquals("de-DE", cloneEffective.localeTag);
            assertEquals(ProfileResolver.Source.CLONE, cloneEffective.localeSource);
            assertEquals("Europe/Berlin", cloneEffective.timeZoneId);
            assertEquals(ProfileResolver.Source.CLONE, cloneEffective.timeZoneSource);

            AsyncCloneRepository.Result<Boolean> localeCleared = awaitResult(
                    callback -> repository.clearGlobalProfileField("localeTag", callback));
            assertTrue(localeCleared.isSuccess());

            AsyncCloneRepository.Result<ProfileSettings> globalAfterReset = awaitResult(
                    repository::loadGlobalProfile);
            AsyncCloneRepository.Result<ProfileSettings> cloneAfterReset = awaitResult(
                    callback -> repository.loadCloneProfile("com.example.globaldefaults", 7, callback));
            assertTrue(globalAfterReset.isSuccess());
            assertTrue(cloneAfterReset.isSuccess());
            assertNull(globalAfterReset.getValue().localeTag);
            assertEquals("Europe/Paris", globalAfterReset.getValue().timeZoneId);
            assertEquals("de-DE", cloneAfterReset.getValue().localeTag);
            assertEquals("Europe/Berlin", cloneAfterReset.getValue().timeZoneId);

            ProfileResolver.ResolvedProfile globalFallback =
                    ProfileResolver.resolve(new ProfileSettings(), globalAfterReset.getValue(), system);
            assertEquals("en-US", globalFallback.localeTag);
            assertEquals(ProfileResolver.Source.SAFE_DEFAULT, globalFallback.localeSource);
            assertEquals("Europe/Paris", globalFallback.timeZoneId);
            assertEquals(ProfileResolver.Source.GLOBAL, globalFallback.timeZoneSource);
        } finally {
            repository.close();
        }
    }

    @Test public void invalidPersistedProfileValuesFallBackIndependently() throws Exception {
        profilePreferences.edit().putString("profiles_json",
                "{\"schemaVersion\":1,"
                + "\"global\":{\"localeTag\":\"fr-FR\",\"timeZoneId\":\"Europe/Paris\",\"latitude\":48.0,\"longitude\":2.0},"
                + "\"clones\":{\"com.example.profile#7\":{"
                + "\"localeTag\":\"invalid locale\",\"timeZoneId\":\"Mars/Olympus\","
                + "\"latitude\":999.0,\"longitude\":45.0,\"locationEnabled\":false}}}")
                .commit();

        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch loaded = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<ProfileSettings>> cloneResult = new AtomicReference<>();
        repository.loadCloneProfile("com.example.profile", 7,
                result -> { cloneResult.set(result); loaded.countDown(); });
        assertTrue(loaded.await(10, TimeUnit.SECONDS));
        assertTrue("Invalid semantic values must not fail the whole profile read",
                cloneResult.get().isSuccess());
        ProfileSettings parsed = cloneResult.get().getValue();
        assertNull(parsed.localeTag);
        assertNull(parsed.timeZoneId);
        assertNull(parsed.latitude);
        assertEquals(Double.valueOf(45.0), parsed.longitude);
        assertEquals(Boolean.FALSE, parsed.locationEnabled);

        ProfileResolver.ResolvedProfile effective = ProfileStore.resolve(
                context, "com.example.profile", 7, new ProfileSettings());
        assertEquals("fr-FR", effective.localeTag);
        assertEquals(ProfileResolver.Source.GLOBAL, effective.localeSource);
        assertEquals("Europe/Paris", effective.timeZoneId);
        assertEquals(ProfileResolver.Source.GLOBAL, effective.timeZoneSource);
        assertEquals(Double.valueOf(48.0), effective.latitude);
        assertEquals(ProfileResolver.Source.GLOBAL, effective.latitudeSource);
        assertEquals(Double.valueOf(45.0), effective.longitude);
        assertEquals(ProfileResolver.Source.CLONE, effective.longitudeSource);
        assertEquals(Boolean.FALSE, effective.locationEnabled);
        assertEquals(ProfileResolver.Source.CLONE, effective.locationEnabledSource);

        // Reading/resolving must not rewrite or erase the original persisted payload.
        assertTrue(profilePreferences.getString("profiles_json", "").contains("\"invalid locale\""));
        repository.close();
    }

    @Test public void activeLaunchMarkerRequiresAndReturnsExistingClone() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CloneStore.CloneEntry entry = cloneEntry("com.example.active", 2);
        CountDownLatch saved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> saveResult = new AtomicReference<>();
        repository.upsertClone(entry, result -> { saveResult.set(result); saved.countDown(); });
        assertTrue(saved.await(10, TimeUnit.SECONDS));
        assertTrue(saveResult.get().isSuccess());

        CountDownLatch recorded = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> recordResult = new AtomicReference<>();
        repository.recordActiveLaunch(entry, result -> { recordResult.set(result); recorded.countDown(); });
        assertTrue(recorded.await(10, TimeUnit.SECONDS));
        assertTrue(recordResult.get().isSuccess());

        CountDownLatch loaded = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneEntry>> loadResult = new AtomicReference<>();
        repository.loadLastActiveLaunch(result -> { loadResult.set(result); loaded.countDown(); });
        assertTrue(loaded.await(10, TimeUnit.SECONDS));
        assertTrue(loadResult.get().isSuccess());
        assertEquals("com.example.active", loadResult.get().getValue().packageName);
        assertEquals(2, loadResult.get().getValue().userId);
        repository.close();
    }

    @Test public void malformedSettingsAreReportedAsCorruptData() throws Exception {
        preferences.edit().putString("collapsed_spaces", "not-a-set")
                .putString("global_device_json", "{broken")
                .putString("master_mock_gps", "not-a-boolean").commit();
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(3);
        AtomicReference<AsyncCloneRepository.Result<java.util.Set<Integer>>> collapsed = new AtomicReference<>();
        AtomicReference<AsyncCloneRepository.Result<CloneStore.GlobalEnvConfig>> global = new AtomicReference<>();
        AtomicReference<AsyncCloneRepository.Result<Boolean>> master = new AtomicReference<>();
        repository.loadCollapsedSpaces(result -> { collapsed.set(result); done.countDown(); });
        repository.loadGlobalEnvironment(result -> { global.set(result); done.countDown(); });
        repository.loadMasterMockGpsEnabled(result -> { master.set(result); done.countDown(); });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, collapsed.get().getFailure());
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, global.get().getFailure());
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, master.get().getFailure());
        assertEquals("not-a-set", preferences.getString("collapsed_spaces", null));
        assertEquals("{broken", preferences.getString("global_device_json", null));
        assertEquals("not-a-boolean", preferences.getString("master_mock_gps", null));
        repository.close();
    }

    @Test public void unsupportedProfileSchemaIsNotReportedAsEmptySuccess() throws Exception {
        profilePreferences.edit().putString("profiles_json", "{\"schemaVersion\":999}").commit();
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<ProfileSettings>> resultRef = new AtomicReference<>();
        repository.loadGlobalProfile(result -> { resultRef.set(result); done.countDown(); });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, resultRef.get().getFailure());
        assertEquals("{\"schemaVersion\":999}", profilePreferences.getString("profiles_json", null));
        repository.close();
    }

    @Test public void unsupportedProfileFieldClearIsRejectedAsInvalidInput() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(2);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> global = new AtomicReference<>();
        AtomicReference<AsyncCloneRepository.Result<Boolean>> clone = new AtomicReference<>();
        repository.clearGlobalProfileField("unknownField", result -> { global.set(result); done.countDown(); });
        repository.clearCloneProfileField("com.example.invalid", 0, "unknownField",
                result -> { clone.set(result); done.countDown(); });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.INVALID_INPUT, global.get().getFailure());
        assertEquals(AsyncCloneRepository.Failure.INVALID_INPUT, clone.get().getFailure());
        repository.close();
    }

    @Test public void closedSingletonIsRecreatedOnNextAccess() throws Exception {
        AsyncCloneRepository first = AsyncCloneRepository.getInstance(context);
        first.close();
        AsyncCloneRepository second = AsyncCloneRepository.getInstance(context);
        assertNotSame(first, second);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<List<CloneStore.CloneEntry>>> resultRef = new AtomicReference<>();
        second.loadClones(result -> { resultRef.set(result); done.countDown(); });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertTrue(resultRef.get().isSuccess());
        second.close();
    }


    @Test public void independentRepositoriesCannotReserveSamePackageUserId() throws Exception {
        AsyncCloneRepository first = new AsyncCloneRepository(context);
        AsyncCloneRepository second = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(2);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> a = new AtomicReference<>();
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> b = new AtomicReference<>();

        first.reserveNextUserId("com.example.concurrent", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), result -> { a.set(result); done.countDown(); });
        second.reserveNextUserId("com.example.concurrent", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), result -> { b.set(result); done.countDown(); });

        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertTrue(a.get().isSuccess());
        assertTrue(b.get().isSuccess());
        assertNotEquals(a.get().getValue().getUserId(), b.get().getValue().getUserId());
        assertNotEquals(a.get().getValue().getToken(), b.get().getValue().getToken());
        assertEquals(2, CloneStore.readPendingReservationsStrict(context).size());
        first.close();
        second.close();
    }

    @Test public void globalAllocatorUsesCloneEngineAndAccountManagerInventories() throws Exception {
        CloneStore.CloneEntry existing = cloneEntry("com.example.legacy", 5);
        assertTrue(CloneStore.upsertClone(context, existing));
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> result = new AtomicReference<>();
        repository.reserveNextUserId("com.example.global",
                Arrays.asList(7, 11), Arrays.asList(13, 17), value -> {
                    result.set(value);
                    done.countDown();
                });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertTrue(result.get().isSuccess());
        assertEquals(18, result.get().getValue().getUserId());
        assertEquals(18, preferences.getInt("last_reserved_global_user_id", -1));

        CountDownLatch nextDone = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> next = new AtomicReference<>();
        repository.reserveNextUserId("com.example.other",
                Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), value -> {
                    next.set(value);
                    nextDone.countDown();
                });
        assertTrue(nextDone.await(10, TimeUnit.SECONDS));
        assertTrue(next.get().isSuccess());
        assertEquals(19, next.get().getValue().getUserId());
        repository.close();
    }

    @Test public void missingOrInvalidEngineInventoriesBlockReservationWithoutChangingLedger() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch missingDone = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> missing = new AtomicReference<>();
        repository.reserveNextUserId("com.example.missing", null,
                Collections.<Integer>emptyList(), value -> {
                    missing.set(value);
                    missingDone.countDown();
                });
        assertTrue(missingDone.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.INVALID_INPUT, missing.get().getFailure());
        assertFalse(preferences.contains("last_reserved_global_user_id"));
        assertTrue(CloneStore.readPendingReservationsStrict(context).isEmpty());

        CountDownLatch invalidDone = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> invalid = new AtomicReference<>();
        repository.reserveNextUserId("com.example.invalid",
                Arrays.asList(-1), Collections.<Integer>emptyList(), value -> {
                    invalid.set(value);
                    invalidDone.countDown();
                });
        assertTrue(invalidDone.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, invalid.get().getFailure());
        assertFalse(preferences.contains("last_reserved_global_user_id"));
        assertTrue(CloneStore.readPendingReservationsStrict(context).isEmpty());
        repository.close();
    }

    @Test public void globalAllocatorRejectsIntegerOverflowWithoutWrapping() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> result = new AtomicReference<>();
        repository.reserveNextUserId("com.example.exhausted",
                Arrays.asList(Integer.MAX_VALUE), Collections.<Integer>emptyList(), value -> {
                    result.set(value);
                    done.countDown();
                });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, result.get().getFailure());
        assertFalse(preferences.contains("last_reserved_global_user_id"));
        assertTrue(CloneStore.readPendingReservationsStrict(context).isEmpty());
        repository.close();
    }

    @Test public void reservationSurvivesRepositoryRecreationAndCommitConsumesOnlyItsToken() throws Exception {
        AsyncCloneRepository first = new AsyncCloneRepository(context);
        CountDownLatch reserved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> reservationRef = new AtomicReference<>();
        first.reserveNextUserId("com.example.durable", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), result -> {
            reservationRef.set(result);
            reserved.countDown();
        });
        assertTrue(reserved.await(10, TimeUnit.SECONDS));
        assertTrue(reservationRef.get().isSuccess());
        CloneStore.CloneReservation reservation = reservationRef.get().getValue();
        first.close();

        AsyncCloneRepository restarted = new AsyncCloneRepository(context);
        CountDownLatch nextReserved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> nextRef = new AtomicReference<>();
        restarted.reserveNextUserId("com.example.durable", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), result -> {
            nextRef.set(result);
            nextReserved.countDown();
        });
        assertTrue(nextReserved.await(10, TimeUnit.SECONDS));
        assertTrue(nextRef.get().isSuccess());
        assertEquals(reservation.getUserId() + 1, nextRef.get().getValue().getUserId());

        CloneStore.CloneEntry wrong = cloneEntry("com.example.other", reservation.getUserId());
        CountDownLatch mismatchDone = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> mismatch = new AtomicReference<>();
        restarted.commitReservedClone(wrong, reservation, result -> {
            mismatch.set(result);
            mismatchDone.countDown();
        });
        assertTrue(mismatchDone.await(10, TimeUnit.SECONDS));
        assertFalse(mismatch.get().isSuccess());
        assertEquals(2, CloneStore.readPendingReservationsStrict(context).size());

        CloneStore.CloneEntry correct = cloneEntry(reservation.getPackageName(), reservation.getUserId());
        CountDownLatch committed = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> commitResult = new AtomicReference<>();
        restarted.commitReservedClone(correct, reservation, result -> {
            commitResult.set(result);
            committed.countDown();
        });
        assertTrue(committed.await(10, TimeUnit.SECONDS));
        assertTrue(commitResult.get().isSuccess());
        assertEquals(1, CloneStore.readAllStrict(context).size());
        List<CloneStore.CloneReservation> remaining = CloneStore.readPendingReservationsStrict(context);
        assertEquals(1, remaining.size());
        assertEquals(nextRef.get().getValue().getToken(), remaining.get(0).getToken());
        restarted.close();
    }

    @Test public void reservationReleaseRequiresEngineAbsenceButNeverReusesTheGlobalId() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch reserved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> reservationRef = new AtomicReference<>();
        repository.reserveNextUserId("com.example.release", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), result -> {
            reservationRef.set(result);
            reserved.countDown();
        });
        assertTrue(reserved.await(10, TimeUnit.SECONDS));
        assertTrue(reservationRef.get().isSuccess());
        CloneStore.CloneReservation reservation = reservationRef.get().getValue();

        CountDownLatch refused = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> refusedRef = new AtomicReference<>();
        repository.releaseReservationAfterEngineAbsence(reservation, false, result -> {
            refusedRef.set(result);
            refused.countDown();
        });
        assertTrue(refused.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.ENGINE_STATE_UNCONFIRMED, refusedRef.get().getFailure());
        assertEquals(1, CloneStore.readPendingReservationsStrict(context).size());

        CountDownLatch released = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> releaseRef = new AtomicReference<>();
        repository.releaseReservationAfterEngineAbsence(reservation, true, result -> {
            releaseRef.set(result);
            released.countDown();
        });
        assertTrue(released.await(10, TimeUnit.SECONDS));
        assertTrue(releaseRef.get().isSuccess());
        assertTrue(CloneStore.readPendingReservationsStrict(context).isEmpty());

        CountDownLatch reused = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> reusedRef = new AtomicReference<>();
        repository.reserveNextUserId("com.example.release", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), result -> {
            reusedRef.set(result);
            reused.countDown();
        });
        assertTrue(reused.await(10, TimeUnit.SECONDS));
        assertTrue(reusedRef.get().isSuccess());
        assertEquals(reservation.getUserId() + 1, reusedRef.get().getValue().getUserId());
        assertEquals(reusedRef.get().getValue().getUserId(), preferences.getInt("last_reserved_global_user_id", -1));
        repository.close();
    }

    @Test public void releasingLegacyPendingReservationSeedsGlobalHighWaterMark() throws Exception {
        String legacyJournal = "{\"schemaVersion\":1,\"reservations\":[{"
                + "\"token\":\"legacy-release-token\","
                + "\"pkg\":\"com.example.legacyrelease\",\"uid\":41}]}";
        assertTrue(preferences.edit()
                .putString("pending_clone_reservations_json", legacyJournal).commit());
        assertFalse(preferences.contains("last_reserved_global_user_id"));

        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch loaded = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<List<CloneStore.CloneReservation>>> pending =
                new AtomicReference<>();
        repository.loadPendingReservations(result -> {
            pending.set(result);
            loaded.countDown();
        });
        assertTrue(loaded.await(10, TimeUnit.SECONDS));
        assertTrue(pending.get().isSuccess());
        assertEquals(1, pending.get().getValue().size());

        CountDownLatch released = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> releaseResult = new AtomicReference<>();
        repository.releaseReservationAfterEngineAbsence(
                pending.get().getValue().get(0), true, result -> {
                    releaseResult.set(result);
                    released.countDown();
                });
        assertTrue(released.await(10, TimeUnit.SECONDS));
        assertTrue(releaseResult.get().isSuccess());
        assertEquals(41, preferences.getInt("last_reserved_global_user_id", -1));
        assertFalse(preferences.contains("pending_clone_reservations_json"));
        repository.close();
    }

    @Test public void reservationReleaseRefusesRegistryConflictAndPreservesJournal() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch reserved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> reservationRef = new AtomicReference<>();
        repository.reserveNextUserId("com.example.releaseconflict", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), result -> {
            reservationRef.set(result);
            reserved.countDown();
        });
        assertTrue(reserved.await(10, TimeUnit.SECONDS));
        assertTrue(reservationRef.get().isSuccess());
        CloneStore.CloneReservation reservation = reservationRef.get().getValue();
        String journalBefore = preferences.getString("pending_clone_reservations_json", null);
        assertNotNull(journalBefore);

        // Simulate an inconsistent persisted registry that collides with the pending identity.
        String conflictingClones = "[{\"pkg\":\"com.example.releaseconflict\",\"uid\":"
                + reservation.getUserId() + "}]";
        assertTrue(preferences.edit().putString("clones_json", conflictingClones).commit());

        CountDownLatch released = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> releaseResult = new AtomicReference<>();
        repository.releaseReservationAfterEngineAbsence(reservation, true, result -> {
            releaseResult.set(result);
            released.countDown();
        });
        assertTrue(released.await(10, TimeUnit.SECONDS));
        assertFalse(releaseResult.get().isSuccess());
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, releaseResult.get().getFailure());
        assertEquals(conflictingClones, preferences.getString("clones_json", null));
        assertEquals(journalBefore, preferences.getString("pending_clone_reservations_json", null));
        repository.close();
    }

    @Test public void pendingReservationCannotBeStolenByOrdinaryCloneUpsert() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch reserved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> reservationRef = new AtomicReference<>();
        repository.reserveNextUserId("com.example.steal", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), result -> {
            reservationRef.set(result);
            reserved.countDown();
        });
        assertTrue(reserved.await(10, TimeUnit.SECONDS));
        CloneStore.CloneReservation reservation = reservationRef.get().getValue();

        CloneStore.CloneEntry competing = cloneEntry("com.example.steal", reservation.getUserId());
        CountDownLatch upserted = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<Boolean>> upsertRef = new AtomicReference<>();
        repository.upsertClone(competing, result -> {
            upsertRef.set(result);
            upserted.countDown();
        });
        assertTrue(upserted.await(10, TimeUnit.SECONDS));
        assertFalse(upsertRef.get().isSuccess());
        assertTrue(CloneStore.readAllStrict(context).isEmpty());
        assertEquals(1, CloneStore.readPendingReservationsStrict(context).size());
        repository.close();
    }


    @Test public void engineInstallStateMappingPreservesInstalledAbsentAndUnknown() {
        assertEquals(Engine.CloneInstallState.INSTALLED,
                Engine.classifyInstalledQueryResult(Boolean.TRUE));
        assertEquals(Engine.CloneInstallState.ABSENT,
                Engine.classifyInstalledQueryResult(Boolean.FALSE));
        assertEquals(Engine.CloneInstallState.UNKNOWN,
                Engine.classifyInstalledQueryResult(null));
    }

    @Test public void engineAbsenceRequiresPackageUserDataDirectoriesToBeAbsent() {
        assertEquals(Engine.CloneInstallState.UNKNOWN,
                Engine.classifyInstallStateWithDataCheck(
                        Engine.CloneInstallState.ABSENT, false));
        assertEquals(Engine.CloneInstallState.ABSENT,
                Engine.classifyInstallStateWithDataCheck(
                        Engine.CloneInstallState.ABSENT, true));
        assertEquals(Engine.CloneInstallState.INSTALLED,
                Engine.classifyInstallStateWithDataCheck(
                        Engine.CloneInstallState.INSTALLED, false));
        assertEquals(Engine.CloneInstallState.UNKNOWN,
                Engine.classifyInstallStateWithDataCheck(
                        Engine.CloneInstallState.UNKNOWN, true));
    }

    @Test public void pendingReservationDiagnosticsAreStrictAndReadOnly() throws Exception {
        String clones = "[{\"pkg\":\"com.example.existing\",\"uid\":0}]";
        String journal = "{\"schemaVersion\":1,\"reservations\":[{\"token\":\"read-only-token\",\"pkg\":\"com.example.pending\",\"uid\":1}]}";
        assertTrue(preferences.edit().putString("clones_json", clones)
                .putString("pending_clone_reservations_json", journal).commit());

        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<List<CloneStore.CloneReservation>>> loaded =
                new AtomicReference<>();
        repository.loadPendingReservations(result -> {
            loaded.set(result);
            done.countDown();
        });

        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertTrue(loaded.get().isSuccess());
        assertEquals(1, loaded.get().getValue().size());
        CloneStore.CloneReservation reservation = loaded.get().getValue().get(0);
        assertEquals("com.example.pending", reservation.getPackageName());
        assertEquals(1, reservation.getUserId());
        assertEquals("read-only-token", reservation.getToken());
        assertEquals(clones, preferences.getString("clones_json", null));
        assertEquals(journal, preferences.getString("pending_clone_reservations_json", null));
        repository.close();
    }

    @Test public void reservationJournalCommitFailureIsClassifiedAsPersistenceFailure() {
        assertEquals(AsyncCloneRepository.Failure.PERSISTENCE_FAILURE,
                AsyncCloneRepository.classify(
                        new CloneStore.PersistenceException("Reservation journal commit failed")));
    }

    @Test public void malformedReservationJournalBlocksAllocationWithoutOverwritingIt() throws Exception {
        String malformed = "{\"schemaVersion\":999,\"reservations\":[]}";
        assertTrue(preferences.edit().putString("pending_clone_reservations_json", malformed).commit());
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> result = new AtomicReference<>();
        repository.reserveNextUserId("com.example.badjournal", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), value -> {
            result.set(value);
            done.countDown();
        });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, result.get().getFailure());
        assertEquals(malformed, preferences.getString("pending_clone_reservations_json", null));
        repository.close();
    }

    @Test public void reservationJournalConflictWithExistingCloneBlocksAllocation() throws Exception {
        String clones = "[{\"pkg\":\"com.example.conflict\",\"uid\":0}]";
        String journal = "{\"schemaVersion\":1,\"reservations\":[{\"token\":\"fixture-token\",\"pkg\":\"com.example.conflict\",\"uid\":0}]}";
        assertTrue(preferences.edit().putString("clones_json", clones)
                .putString("pending_clone_reservations_json", journal).commit());
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> result = new AtomicReference<>();
        repository.reserveNextUserId("com.example.conflict", Collections.<Integer>emptyList(), Collections.<Integer>emptyList(), value -> {
            result.set(value);
            done.countDown();
        });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, result.get().getFailure());
        assertEquals(clones, preferences.getString("clones_json", null));
        assertEquals(journal, preferences.getString("pending_clone_reservations_json", null));
        repository.close();
    }


    @Test public void typedProfileDocumentsPersistIndependentlyAndResolvePerField() throws Exception {
        ProfileDocument global = new ProfileDocument();
        assertTrue(global.put("localeTag", "fr-FR"));
        assertTrue(global.put("timeZoneId", "America/New_York"));
        assertTrue(ProfileDocumentStore.saveGlobalDocument(context, global));

        ProfileDocument cloneA = new ProfileDocument();
        assertTrue(cloneA.put("timeZoneId", "Europe/Paris"));
        assertTrue(ProfileDocumentStore.saveCloneDocument(context, "com.example.documenta", 3, cloneA));

        ProfileDocument cloneB = new ProfileDocument();
        assertTrue(cloneB.put("localeTag", "de-DE"));
        assertTrue(ProfileDocumentStore.saveCloneDocument(context, "com.example.documentb", 8, cloneB));

        ProfileDocument globalRead = ProfileDocumentStore.readGlobalStrict(context);
        ProfileDocument cloneARead = ProfileDocumentStore.readCloneStrict(context, "com.example.documenta", 3);
        ProfileDocument cloneBRead = ProfileDocumentStore.readCloneStrict(context, "com.example.documentb", 8);
        ProfileDocumentResolver.FieldResult aLocale = ProfileDocumentResolver.resolve(
                "localeTag", cloneARead, globalRead, ProfileFieldRegistry.createSafeDefaults());
        ProfileDocumentResolver.FieldResult aZone = ProfileDocumentResolver.resolve(
                "timeZoneId", cloneARead, globalRead, ProfileFieldRegistry.createSafeDefaults());
        ProfileDocumentResolver.FieldResult bLocale = ProfileDocumentResolver.resolve(
                "localeTag", cloneBRead, globalRead, ProfileFieldRegistry.createSafeDefaults());
        ProfileDocumentResolver.FieldResult bZone = ProfileDocumentResolver.resolve(
                "timeZoneId", cloneBRead, globalRead, ProfileFieldRegistry.createSafeDefaults());

        assertEquals("fr-FR", aLocale.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, aLocale.source);
        assertEquals("Europe/Paris", aZone.value);
        assertEquals(ProfileDocumentResolver.Source.CLONE, aZone.source);
        assertEquals("de-DE", bLocale.value);
        assertEquals(ProfileDocumentResolver.Source.CLONE, bLocale.source);
        assertEquals("America/New_York", bZone.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, bZone.source);

        ProfileDocument updatedGlobal = new ProfileDocument();
        assertTrue(updatedGlobal.put("localeTag", "es-ES"));
        assertTrue(updatedGlobal.put("timeZoneId", "America/Chicago"));
        assertTrue(ProfileDocumentStore.saveGlobalDocument(context, updatedGlobal));
        ProfileDocument afterGlobalEditA = ProfileDocumentStore.readCloneStrict(
                context, "com.example.documenta", 3);
        assertEquals("Europe/Paris", afterGlobalEditA.get("timeZoneId"));
        assertFalse(afterGlobalEditA.contains("localeTag"));

        assertTrue(ProfileDocumentStore.clearCloneField(
                context, "com.example.documenta", 3, "timeZoneId"));
        ProfileDocument afterResetA = ProfileDocumentStore.readCloneStrict(
                context, "com.example.documenta", 3);
        ProfileDocument latestGlobal = ProfileDocumentStore.readGlobalStrict(context);
        ProfileDocumentResolver.FieldResult resetZone = ProfileDocumentResolver.resolve(
                "timeZoneId", afterResetA, latestGlobal, ProfileFieldRegistry.createSafeDefaults());
        assertEquals("America/Chicago", resetZone.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, resetZone.source);
        assertEquals("de-DE", ProfileDocumentStore.readCloneStrict(
                context, "com.example.documentb", 8).get("localeTag"));
        assertTrue(ProfileDocumentStore.readRevisionStrict(context) >= 5L);
    }

    @Test public void typedProfileDocumentSemanticInvalidityFallsBackPerFieldButStructuralCorruptionFailsClosed()
            throws Exception {
        String semantic = "{\"schemaVersion\":1,\"revision\":1,\"updatedAt\":1,"
                + "\"global\":{\"localeTag\":\"en-US\",\"timeZoneId\":\"Europe/Paris\"},"
                + "\"clones\":{\"com.example.semantic#2\":{\"timeZoneId\":\"Mars/Olympus\"}}}";
        assertTrue(profileDocumentPreferences.edit().putString("documents_json", semantic).commit());
        ProfileDocument clone = ProfileDocumentStore.readCloneStrict(context, "com.example.semantic", 2);
        ProfileDocument global = ProfileDocumentStore.readGlobalStrict(context);
        assertFalse(clone.contains("timeZoneId"));
        ProfileDocumentResolver.FieldResult zone = ProfileDocumentResolver.resolve(
                "timeZoneId", clone, global, ProfileFieldRegistry.createSafeDefaults());
        assertEquals("Europe/Paris", zone.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, zone.source);

        String structural = "{\"schemaVersion\":1,\"revision\":2,\"updatedAt\":2,"
                + "\"global\":{\"localeTag\":123},\"clones\":{}}";
        assertTrue(profileDocumentPreferences.edit().putString("documents_json", structural).commit());
        boolean rejected = false;
        try {
            ProfileDocumentStore.readGlobalStrict(context);
        } catch (Exception expected) {
            rejected = true;
        }
        assertTrue("Wrong stored field type must fail closed", rejected);
        assertFalse(ProfileDocumentStore.saveGlobalField(context, "localeTag", "it-IT"));
        assertEquals(structural, profileDocumentPreferences.getString("documents_json", null));
    }

    @Test public void invalidTypedFieldsSuppressSameLevelLegacyFallback() throws Exception {
        String cloneInvalid = "{\"schemaVersion\":1,\"revision\":1,\"updatedAt\":1,"
                + "\"global\":{\"timeZoneId\":\"Europe/Paris\"},"
                + "\"clones\":{\"com.example.invalidclone#6\":{\"timeZoneId\":\"Mars/Olympus\"}}}";
        assertTrue(profileDocumentPreferences.edit().putString("documents_json", cloneInvalid).commit());

        ProfileSettings legacyClone = new ProfileSettings();
        legacyClone.timeZoneId = "America/Chicago";
        ProfileSettings legacyGlobal = new ProfileSettings();
        legacyGlobal.timeZoneId = "Asia/Tokyo";
        ProfileDocument typedClone = ProfileDocumentStore.readCloneStrict(
                context, "com.example.invalidclone", 6);
        ProfileDocument typedGlobal = ProfileDocumentStore.readGlobalStrict(context);
        assertTrue(typedClone.isInvalid("timeZoneId"));
        ProfileDocument mergedClone = ProfileRuntimeProvider.mergeLegacyFields(typedClone, legacyClone);
        ProfileDocument mergedGlobal = ProfileRuntimeProvider.mergeLegacyFields(typedGlobal, legacyGlobal);
        assertFalse("Invalid typed Clone value must suppress same-level Legacy", mergedClone.contains("timeZoneId"));
        assertEquals("Europe/Paris", ProfileDocumentResolver.resolve(
                "timeZoneId", mergedClone, mergedGlobal, ProfileFieldRegistry.createSafeDefaults()).value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, ProfileDocumentResolver.resolve(
                "timeZoneId", mergedClone, mergedGlobal, ProfileFieldRegistry.createSafeDefaults()).source);

        String globalInvalid = "{\"schemaVersion\":1,\"revision\":2,\"updatedAt\":2,"
                + "\"global\":{\"timeZoneId\":\"Mars/Olympus\"},\"clones\":{}}";
        assertTrue(profileDocumentPreferences.edit().putString("documents_json", globalInvalid).commit());
        ProfileDocument invalidGlobal = ProfileDocumentStore.readGlobalStrict(context);
        assertTrue(invalidGlobal.isInvalid("timeZoneId"));
        ProfileDocument mergedInvalidGlobal = ProfileRuntimeProvider.mergeLegacyFields(
                invalidGlobal, legacyGlobal);
        assertFalse("Invalid typed Global value must suppress same-level Legacy",
                mergedInvalidGlobal.contains("timeZoneId"));
        ProfileDocumentResolver.FieldResult safe = ProfileDocumentResolver.resolve(
                "timeZoneId", new ProfileDocument(), mergedInvalidGlobal,
                ProfileFieldRegistry.createSafeDefaults());
        assertEquals("UTC", safe.value);
        assertEquals(ProfileDocumentResolver.Source.SAFE_DEFAULT, safe.source);

        // A truly absent typed field retains the backwards-compatible Legacy fallback.
        ProfileDocument absent = ProfileRuntimeProvider.mergeLegacyFields(
                new ProfileDocument(), legacyClone);
        assertEquals("America/Chicago", absent.get("timeZoneId"));
    }

    @Test public void profileDocumentRejectsStringSchemaVersionWithoutCoercion() throws Exception {
        String malformed = "{\"schemaVersion\":\"1\",\"revision\":1,\"updatedAt\":1,"
                + "\"global\":{},\"clones\":{}}";
        assertTrue(profileDocumentPreferences.edit().putString("documents_json", malformed).commit());
        try {
            ProfileDocumentStore.readGlobalStrict(context);
            fail("String schemaVersion must not be coerced into a numeric schema");
        } catch (IllegalStateException expected) {
            assertEquals(malformed, profileDocumentPreferences.getString("documents_json", null));
        }
    }

    @Test public void typedProfileDocumentRejectsRestrictedAndObservedOnlyFields() {
        assertFalse(ProfileDocumentStore.saveGlobalField(context, "imei", "000000000000000"));
        assertFalse(ProfileDocumentStore.saveGlobalField(context, "publicIpAddress", "203.0.113.4"));
        assertFalse(ProfileDocumentStore.saveCloneField(
                context, "com.example.restricted", 1, "phoneNumber", "+15550000000"));
        assertEquals("", profileDocumentPreferences.getString("documents_json", ""));
    }

    @Test public void repositoryPersistsAndResolvesTypedCloneAndGlobalDocumentsAsynchronously()
            throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        ProfileDocument global = new ProfileDocument();
        assertTrue(global.put("localeTag", "en-US"));
        assertTrue(global.put("timeZoneId", "America/New_York"));
        assertTrue(awaitResult((AsyncCloneRepository.Callback<Boolean> cb) -> repository.saveGlobalProfileDocument(global, cb)).isSuccess());

        ProfileDocument cloneA = new ProfileDocument();
        assertTrue(cloneA.put("timeZoneId", "Europe/Paris"));
        ProfileDocument cloneB = new ProfileDocument();
        assertTrue(cloneB.put("localeTag", "de-DE"));
        assertTrue(awaitResult((AsyncCloneRepository.Callback<Boolean> cb) -> repository.saveCloneProfileDocument(
                "com.example.repoa", 4, cloneA, cb)).isSuccess());
        assertTrue(awaitResult((AsyncCloneRepository.Callback<Boolean> cb) -> repository.saveCloneProfileDocument(
                "com.example.repob", 9, cloneB, cb)).isSuccess());

        ProfileDocument loadedA = awaitResult((AsyncCloneRepository.Callback<ProfileDocument> cb) ->
                repository.loadCloneProfileDocument("com.example.repoa", 4, cb)).getValue();
        ProfileDocument loadedB = awaitResult((AsyncCloneRepository.Callback<ProfileDocument> cb) ->
                repository.loadCloneProfileDocument("com.example.repob", 9, cb)).getValue();
        ProfileDocument loadedGlobal = awaitResult(repository::loadGlobalProfileDocument).getValue();

        ProfileDocumentResolver.FieldResult aLocale = ProfileDocumentResolver.resolve(
                "localeTag", loadedA, loadedGlobal, ProfileFieldRegistry.createSafeDefaults());
        ProfileDocumentResolver.FieldResult aZone = ProfileDocumentResolver.resolve(
                "timeZoneId", loadedA, loadedGlobal, ProfileFieldRegistry.createSafeDefaults());
        assertEquals("en-US", aLocale.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, aLocale.source);
        assertEquals("Europe/Paris", aZone.value);
        assertEquals(ProfileDocumentResolver.Source.CLONE, aZone.source);
        assertEquals("de-DE", loadedB.get("localeTag"));
        assertFalse(loadedB.contains("timeZoneId"));

        assertTrue(awaitResult((AsyncCloneRepository.Callback<Boolean> cb) -> repository.clearCloneProfileDocumentField(
                "com.example.repoa", 4, "timeZoneId", cb)).isSuccess());
        ProfileDocument afterReset = awaitResult((AsyncCloneRepository.Callback<ProfileDocument> cb) ->
                repository.loadCloneProfileDocument("com.example.repoa", 4, cb)).getValue();
        ProfileDocumentResolver.FieldResult resetZone = ProfileDocumentResolver.resolve(
                "timeZoneId", afterReset, loadedGlobal, ProfileFieldRegistry.createSafeDefaults());
        assertEquals("America/New_York", resetZone.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, resetZone.source);
        assertEquals("de-DE", awaitResult((AsyncCloneRepository.Callback<ProfileDocument> cb) ->
                repository.loadCloneProfileDocument("com.example.repob", 9, cb)).getValue().get("localeTag"));
        repository.close();
    }

    @Test public void typedResetMarkersPersistAndSuppressLegacyValues() throws Exception {
        ProfileDocument global = new ProfileDocument();
        assertTrue(global.put("localeTag", "fr-FR"));
        assertTrue(ProfileDocumentStore.saveGlobalDocument(context, global));
        ProfileDocument clone = new ProfileDocument();
        assertTrue(clone.put("localeTag", "de-DE"));
        assertTrue(ProfileDocumentStore.saveCloneDocument(context, "com.example.tombstone", 12, clone));
        assertTrue(ProfileDocumentStore.clearCloneField(context, "com.example.tombstone", 12, "localeTag"));
        ProfileDocument cloneReset = ProfileDocumentStore.readCloneStrict(context, "com.example.tombstone", 12);
        assertEquals(ProfileDocument.FieldState.INHERIT_GLOBAL, cloneReset.state("localeTag"));
        ProfileDocumentResolver.FieldResult inherited = ProfileDocumentResolver.resolve(
                "localeTag", cloneReset, ProfileDocumentStore.readGlobalStrict(context), ProfileFieldRegistry.createSafeDefaults());
        assertEquals("fr-FR", inherited.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, inherited.source);
        ProfileSettings staleClone = new ProfileSettings();
        staleClone.localeTag = "it-IT";
        ProfileDocument mergedClone = ProfileRuntimeProvider.mergeLegacyFields(cloneReset, staleClone);
        assertFalse(mergedClone.contains("localeTag"));
        assertTrue(mergedClone.hasState("localeTag"));
        assertTrue(ProfileDocumentStore.clearGlobalField(context, "localeTag"));
        ProfileDocument globalReset = ProfileDocumentStore.readGlobalStrict(context);
        assertEquals(ProfileDocument.FieldState.SAFE_DEFAULT, globalReset.state("localeTag"));
        ProfileDocumentResolver.FieldResult safe = ProfileDocumentResolver.resolve(
                "localeTag", new ProfileDocument(), globalReset, ProfileFieldRegistry.createSafeDefaults());
        assertEquals("en-US", safe.value);
        assertEquals(ProfileDocumentResolver.Source.SAFE_DEFAULT, safe.source);
        ProfileSettings staleGlobal = new ProfileSettings();
        staleGlobal.localeTag = "es-ES";
        ProfileDocument mergedGlobal = ProfileRuntimeProvider.mergeLegacyFields(globalReset, staleGlobal);
        assertFalse(mergedGlobal.contains("localeTag"));
        assertTrue(mergedGlobal.hasState("localeTag"));
    }

    @Test public void legacyUiRepositoryMethodsPersistTypedValuesAndResetMarkers() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        ProfileSettings global = new ProfileSettings();
        global.localeTag = "en-GB";
        assertTrue(awaitResult((AsyncRepositoryOperation<Boolean>) cb -> repository.saveGlobalProfile(global, cb)).isSuccess());
        ProfileSettings clone = new ProfileSettings();
        clone.localeTag = "ja-JP";
        assertTrue(awaitResult((AsyncRepositoryOperation<Boolean>) cb -> repository.saveCloneProfile("com.example.ui-bridge", 14, clone, cb)).isSuccess());
        assertEquals("ja-JP", ProfileDocumentStore.readCloneStrict(context, "com.example.ui-bridge", 14).get("localeTag"));
        assertEquals("en-GB", ProfileDocumentStore.readGlobalStrict(context).get("localeTag"));
        assertTrue(awaitResult((AsyncRepositoryOperation<Boolean>) cb -> repository.clearCloneProfileField("com.example.ui-bridge", 14, "localeTag", cb)).isSuccess());
        assertEquals(ProfileDocument.FieldState.INHERIT_GLOBAL, ProfileDocumentStore.readCloneStrict(context, "com.example.ui-bridge", 14).state("localeTag"));
        assertNull(awaitResult((AsyncRepositoryOperation<ProfileSettings>) cb -> repository.loadCloneProfile("com.example.ui-bridge", 14, cb)).getValue().localeTag);
        assertTrue(awaitResult((AsyncRepositoryOperation<Boolean>) cb -> repository.clearGlobalProfileField("localeTag", cb)).isSuccess());
        assertEquals(ProfileDocument.FieldState.SAFE_DEFAULT, ProfileDocumentStore.readGlobalStrict(context).state("localeTag"));
        repository.close();
    }

    @Test public void repositoryRejectsInvalidTypedProfileFieldWithoutWriting() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        AsyncCloneRepository.Result<Boolean> result = awaitResult((AsyncCloneRepository.Callback<Boolean> cb) ->
                repository.saveCloneProfileField("com.example.invaliddoc", 1, "imei",
                        "000000000000000", cb));
        assertEquals(AsyncCloneRepository.Failure.INVALID_INPUT, result.getFailure());
        assertEquals("", profileDocumentPreferences.getString("documents_json", ""));
        repository.close();
    }

    @Test public void typedRuntimeProfileMergesLegacyValuesPerFieldWithoutMutatingEitherStore() {
        ProfileSettings legacyClone = new ProfileSettings();
        legacyClone.localeTag = "de-DE";
        legacyClone.timeZoneId = "Europe/Berlin";
        legacyClone.locationEnabled = Boolean.FALSE;

        ProfileDocument typedClone = new ProfileDocument();
        assertTrue(typedClone.put("timeZoneId", "Europe/Paris"));

        ProfileSettings legacyGlobal = new ProfileSettings();
        legacyGlobal.localeTag = "fr-FR";
        legacyGlobal.timeZoneId = "America/Chicago";

        ProfileDocument typedGlobal = new ProfileDocument();
        assertTrue(typedGlobal.put("timeZoneId", "America/New_York"));

        ProfileDocument mergedClone = ProfileRuntimeProvider.mergeLegacyFields(
                typedClone, legacyClone);
        ProfileDocument mergedGlobal = ProfileRuntimeProvider.mergeLegacyFields(
                typedGlobal, legacyGlobal);

        assertEquals("de-DE", mergedClone.get("localeTag"));
        assertEquals("Europe/Paris", mergedClone.get("timeZoneId"));
        assertEquals(Boolean.FALSE, mergedClone.get("locationEnabled"));
        assertEquals("fr-FR", mergedGlobal.get("localeTag"));
        assertEquals("America/New_York", mergedGlobal.get("timeZoneId"));

        ProfileDocumentResolver.FieldResult cloneLocale = ProfileDocumentResolver.resolve(
                "localeTag", mergedClone, mergedGlobal, ProfileFieldRegistry.createSafeDefaults());
        ProfileDocumentResolver.FieldResult cloneZone = ProfileDocumentResolver.resolve(
                "timeZoneId", mergedClone, mergedGlobal, ProfileFieldRegistry.createSafeDefaults());
        ProfileDocumentResolver.FieldResult inheritedZone = ProfileDocumentResolver.resolve(
                "timeZoneId", new ProfileDocument(), mergedGlobal, ProfileFieldRegistry.createSafeDefaults());

        assertEquals("de-DE", cloneLocale.value);
        assertEquals(ProfileDocumentResolver.Source.CLONE, cloneLocale.source);
        assertEquals("Europe/Paris", cloneZone.value);
        assertEquals(ProfileDocumentResolver.Source.CLONE, cloneZone.source);
        assertEquals("America/New_York", inheritedZone.value);
        assertEquals(ProfileDocumentResolver.Source.GLOBAL, inheritedZone.source);

        ProfileSettings runtimeClone = ProfileRuntimeProvider.mergeDocumentFields(
                legacyClone, typedClone);
        assertEquals("de-DE", runtimeClone.localeTag);
        assertEquals("Europe/Paris", runtimeClone.timeZoneId);
        assertEquals(Boolean.FALSE, runtimeClone.locationEnabled);

        // These are in-memory compatibility merges only: persisted legacy and typed inputs stay intact.
        assertEquals("Europe/Berlin", legacyClone.timeZoneId);
        assertEquals("Europe/Paris", typedClone.get("timeZoneId"));
        assertEquals("America/Chicago", legacyGlobal.timeZoneId);
        assertEquals("America/New_York", typedGlobal.get("timeZoneId"));
    }

    @Test public void locationRuntimeResolverUsesTypedCloneAndGlobalValuesPerField() throws Exception {
        String packageName = "com.example.typedlocation";
        int userId = 7;

        ProfileSettings legacyClone = new ProfileSettings();
        legacyClone.locationEnabled = Boolean.FALSE;
        legacyClone.latitude = 12.5d;
        assertTrue(ProfileStore.saveCloneOverride(context, packageName, userId, legacyClone));

        ProfileSettings legacyGlobal = new ProfileSettings();
        legacyGlobal.longitude = 44.5d;
        assertTrue(ProfileStore.saveGlobal(context, legacyGlobal));

        assertTrue(ProfileDocumentStore.saveCloneField(
                context, packageName, userId, "locationEnabled", Boolean.TRUE));
        assertTrue(ProfileDocumentStore.saveCloneField(
                context, packageName, userId, "latitude", 31.25d));
        assertTrue(ProfileDocumentStore.saveGlobalField(context, "longitude", 48.75d));

        ProfileResolver.ResolvedProfile resolved = ProfileRuntimeProvider.resolveMergedProfile(
                context, packageName, userId, ProfileRuntimeApplier.systemFallback());

        assertEquals(Boolean.TRUE, resolved.locationEnabled);
        assertEquals(ProfileResolver.Source.CLONE, resolved.locationEnabledSource);
        assertEquals(Double.valueOf(31.25d), resolved.latitude);
        assertEquals(ProfileResolver.Source.CLONE, resolved.latitudeSource);
        assertEquals(Double.valueOf(48.75d), resolved.longitude);
        assertEquals(ProfileResolver.Source.GLOBAL, resolved.longitudeSource);

        // Resolution is read-only: neither legacy nor typed persisted values are rewritten.
        assertEquals(Boolean.FALSE,
                ProfileStore.readCloneOverrideStrict(context, packageName, userId).locationEnabled);
        assertEquals(Double.valueOf(12.5d),
                ProfileStore.readCloneOverrideStrict(context, packageName, userId).latitude);
        assertEquals(Boolean.TRUE, ProfileDocumentStore.readCloneStrict(
                context, packageName, userId).get("locationEnabled"));
        assertEquals(Double.valueOf(31.25d), ProfileDocumentStore.readCloneStrict(
                context, packageName, userId).get("latitude"));
        assertEquals(Double.valueOf(44.5d), ProfileStore.readGlobalStrict(context).longitude);
        assertEquals(Double.valueOf(48.75d), ProfileDocumentStore.readGlobalStrict(context).get("longitude"));
    }

    @Test public void invalidTypedFieldsFallThroughAtActualLocationRuntimeResolver() throws Exception {
        String packageName = "com.example.invalidtypedlocation";
        int userId = 11;

        ProfileSettings legacyClone = new ProfileSettings();
        legacyClone.timeZoneId = "America/Chicago";
        assertTrue(ProfileStore.saveCloneOverride(context, packageName, userId, legacyClone));

        ProfileSettings legacyGlobal = new ProfileSettings();
        legacyGlobal.timeZoneId = "Asia/Tokyo";
        assertTrue(ProfileStore.saveGlobal(context, legacyGlobal));

        String typedCloneInvalidGlobalValid = "{\"schemaVersion\":1,\"revision\":1,\"updatedAt\":1,"
                + "\"global\":{\"timeZoneId\":\"Europe/Paris\"},"
                + "\"clones\":{\"" + packageName + "#" + userId
                + "\":{\"timeZoneId\":\"Mars/Olympus\"}}}";
        assertTrue(profileDocumentPreferences.edit()
                .putString("documents_json", typedCloneInvalidGlobalValid).commit());

        ProfileResolver.ResolvedProfile inherited = ProfileRuntimeProvider.resolveMergedProfile(
                context, packageName, userId, ProfileRuntimeApplier.systemFallback());
        assertEquals("Europe/Paris", inherited.timeZoneId);
        assertEquals(ProfileResolver.Source.GLOBAL, inherited.timeZoneSource);

        String typedCloneAndGlobalInvalid = "{\"schemaVersion\":1,\"revision\":2,\"updatedAt\":2,"
                + "\"global\":{\"timeZoneId\":\"Mars/Olympus\"},"
                + "\"clones\":{\"" + packageName + "#" + userId
                + "\":{\"timeZoneId\":\"Mars/Olympus\"}}}";
        assertTrue(profileDocumentPreferences.edit()
                .putString("documents_json", typedCloneAndGlobalInvalid).commit());

        ProfileResolver.ResolvedProfile safe = ProfileRuntimeProvider.resolveMergedProfile(
                context, packageName, userId, ProfileRuntimeApplier.systemFallback());
        assertEquals("UTC", safe.timeZoneId);
        assertEquals(ProfileResolver.Source.SAFE_DEFAULT, safe.timeZoneSource);

        // Runtime resolution is read-only; neither legacy nor typed storage is rewritten.
        assertEquals("America/Chicago",
                ProfileStore.readCloneOverrideStrict(context, packageName, userId).timeZoneId);
        assertEquals("Asia/Tokyo", ProfileStore.readGlobalStrict(context).timeZoneId);
        assertEquals(typedCloneAndGlobalInvalid,
                profileDocumentPreferences.getString("documents_json", null));
    }

    @Test public void instrumentationPreferencesAreIsolatedFromProductionNamespaces() {
        String probe = "veyra_test_isolation_probe_20261127";
        assertTrue(preferences.edit().putString(probe, "isolated").commit());
        assertEquals("isolated", preferences.getString(probe, null));
        assertNull(rawContext.getSharedPreferences(
                "veyravault_clones_v2", Context.MODE_PRIVATE).getString(probe, null));
        preferences.edit().remove(probe).commit();
    }

    private static final class IsolatedPreferencesContext extends ContextWrapper {
        IsolatedPreferencesContext(Context base) {
            super(base);
        }

        @Override public Context getApplicationContext() {
            return this;
        }

        @Override public SharedPreferences getSharedPreferences(String name, int mode) {
            return super.getSharedPreferences("veyra_instrumentation_" + name, mode);
        }
    }

    private interface AsyncRepositoryOperation<T> {
        void execute(AsyncCloneRepository.Callback<T> callback);
    }

    private static <T> AsyncCloneRepository.Result<T> awaitResult(
            AsyncRepositoryOperation<T> operation) throws Exception {
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<T>> result = new AtomicReference<>();
        operation.execute(value -> {
            result.set(value);
            done.countDown();
        });
        assertTrue("Asynchronous repository operation timed out", done.await(10, TimeUnit.SECONDS));
        assertNotNull("Repository callback returned no result", result.get());
        return result.get();
    }

    private static CloneStore.CloneEntry cloneEntry(String packageName, int userId) {
        CloneStore.CloneEntry entry = new CloneStore.CloneEntry();
        entry.packageName = packageName;
        entry.userId = userId;
        entry.displayName = "Original";
        entry.deniedPermissions = new java.util.HashSet<String>(Collections.singleton("android.permission.CAMERA"));
        return entry;
    }
}
