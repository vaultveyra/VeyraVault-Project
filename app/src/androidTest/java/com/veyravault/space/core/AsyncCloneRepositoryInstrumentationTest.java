package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Looper;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Collections;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AsyncCloneRepositoryInstrumentationTest {
    private Context context;
    private SharedPreferences preferences;
    private SharedPreferences profilePreferences;

    @Before public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        preferences = context.getSharedPreferences("veyravault_clones_v2", Context.MODE_PRIVATE);
        profilePreferences = context.getSharedPreferences("veyravault_profiles_v1", Context.MODE_PRIVATE);
        preferences.edit().clear().commit();
        profilePreferences.edit().clear().commit();
    }

    @After public void tearDown() {
        preferences.edit().clear().commit();
        profilePreferences.edit().clear().commit();
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

        first.reserveNextUserId("com.example.concurrent", result -> { a.set(result); done.countDown(); });
        second.reserveNextUserId("com.example.concurrent", result -> { b.set(result); done.countDown(); });

        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertTrue(a.get().isSuccess());
        assertTrue(b.get().isSuccess());
        assertNotEquals(a.get().getValue().getUserId(), b.get().getValue().getUserId());
        assertNotEquals(a.get().getValue().getToken(), b.get().getValue().getToken());
        assertEquals(2, CloneStore.readPendingReservationsStrict(context).size());
        first.close();
        second.close();
    }

    @Test public void reservationSurvivesRepositoryRecreationAndCommitConsumesOnlyItsToken() throws Exception {
        AsyncCloneRepository first = new AsyncCloneRepository(context);
        CountDownLatch reserved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> reservationRef = new AtomicReference<>();
        first.reserveNextUserId("com.example.durable", result -> {
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
        restarted.reserveNextUserId("com.example.durable", result -> {
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

    @Test public void reservationReleaseRequiresExplicitEngineAbsenceAndAllowsSafeReuse() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch reserved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> reservationRef = new AtomicReference<>();
        repository.reserveNextUserId("com.example.release", result -> {
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
        repository.reserveNextUserId("com.example.release", result -> {
            reusedRef.set(result);
            reused.countDown();
        });
        assertTrue(reused.await(10, TimeUnit.SECONDS));
        assertTrue(reusedRef.get().isSuccess());
        assertEquals(reservation.getUserId(), reusedRef.get().getValue().getUserId());
        repository.close();
    }

    @Test public void reservationReleaseRefusesRegistryConflictAndPreservesJournal() throws Exception {
        AsyncCloneRepository repository = new AsyncCloneRepository(context);
        CountDownLatch reserved = new CountDownLatch(1);
        AtomicReference<AsyncCloneRepository.Result<CloneStore.CloneReservation>> reservationRef = new AtomicReference<>();
        repository.reserveNextUserId("com.example.releaseconflict", result -> {
            reservationRef.set(result);
            reserved.countDown();
        });
        assertTrue(reserved.await(10, TimeUnit.SECONDS));
        assertTrue(reservationRef.get().isSuccess());
        CloneStore.CloneReservation reservation = reservationRef.get().getValue();
        String journalBefore = preferences.getString("pending_clone_reservations_json", null);
        assertNotNull(journalBefore);

        // Simulate an inconsistent persisted registry that collides with the pending identity.
        String conflictingClones = "[{\\"pkg\\":\\"com.example.releaseconflict\\",\\"uid\\":"
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
        repository.reserveNextUserId("com.example.steal", result -> {
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
        repository.reserveNextUserId("com.example.badjournal", value -> {
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
        repository.reserveNextUserId("com.example.conflict", value -> {
            result.set(value);
            done.countDown();
        });
        assertTrue(done.await(10, TimeUnit.SECONDS));
        assertEquals(AsyncCloneRepository.Failure.CORRUPT_DATA, result.get().getFailure());
        assertEquals(clones, preferences.getString("clones_json", null));
        assertEquals(journal, preferences.getString("pending_clone_reservations_json", null));
        repository.close();
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
