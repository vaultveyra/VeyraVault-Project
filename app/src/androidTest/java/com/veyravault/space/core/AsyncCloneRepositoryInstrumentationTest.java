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

    private static CloneStore.CloneEntry cloneEntry(String packageName, int userId) {
        CloneStore.CloneEntry entry = new CloneStore.CloneEntry();
        entry.packageName = packageName;
        entry.userId = userId;
        entry.displayName = "Original";
        entry.deniedPermissions = new java.util.HashSet<String>(Collections.singleton("android.permission.CAMERA"));
        return entry;
    }
}
