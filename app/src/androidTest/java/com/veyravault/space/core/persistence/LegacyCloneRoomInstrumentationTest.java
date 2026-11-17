package com.veyravault.space.core.persistence;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.room.Room;
import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.File;
import java.util.Arrays;
import java.util.HashSet;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class LegacyCloneRoomInstrumentationTest {
    private static final String TEST_DB = "room_instrumentation_test.db";
    private Context context;

    @Before public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        context.getSharedPreferences(LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE)
                .edit().clear().commit();
        context.deleteDatabase(TEST_DB);
    }

    @After public void tearDown() {
        context.getSharedPreferences(LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE)
                .edit().clear().commit();
        context.deleteDatabase(TEST_DB);
    }

    @Test public void importsAndVerifiesAllModeledRowsAndProvenance() throws Exception {
        LegacyCloneSnapshot snapshot = populatedSnapshot(true);
        ClonePersistenceDatabase db = inMemoryDb();
        try {
            assertEquals(LegacyCloneRoomImporter.Result.IMPORTED, importOnWorker(db, snapshot));
            assertTrue(LegacyCloneRoomVerifier.matches(db, snapshot));
            assertEquals(1, db.clones().count());
            assertEquals(1, db.deniedPermissions().count());
            assertEquals(1, db.collapsedSpaces().count());
            assertEquals(1, db.migrationMetadata().count());
            assertEquals("com.example.stale", db.lastActiveLaunch().get().packageName);
        } finally {
            db.close();
        }
    }

    @Test public void repeatedImportIsIdempotentOnlyWhenParityStillMatches() throws Exception {
        LegacyCloneSnapshot snapshot = populatedSnapshot(false);
        ClonePersistenceDatabase db = inMemoryDb();
        try {
            assertEquals(LegacyCloneRoomImporter.Result.IMPORTED, importOnWorker(db, snapshot));
            assertEquals(LegacyCloneRoomImporter.Result.ALREADY_IMPORTED, importOnWorker(db, snapshot));
            assertEquals(1, db.clones().count());
            db.getOpenHelper().getWritableDatabase().execSQL(
                    "UPDATE clones SET displayName='tampered' WHERE packageName='com.example.alpha' AND userId=10");
            assertFalse(LegacyCloneRoomVerifier.matches(db, snapshot));
            try {
                importOnWorker(db, snapshot);
                fail("An altered prior import must not be accepted as idempotent");
            } catch (Exception expected) {
                assertNotNull(expected);
            }
        } finally {
            db.close();
        }
    }

    @Test public void transactionRollsBackEveryTableWhenPermissionInsertFails() throws Exception {
        LegacyCloneSnapshot snapshot = populatedSnapshot(false);
        ClonePersistenceDatabase db = inMemoryDb();
        try {
            db.getOpenHelper().getWritableDatabase().execSQL(
                    "CREATE TRIGGER fail_permission_insert BEFORE INSERT ON clone_denied_permissions " +
                    "BEGIN SELECT RAISE(ABORT, 'injected instrumentation failure'); END");
            try {
                importOnWorker(db, snapshot);
                fail("Injected SQLite trigger should abort the import");
            } catch (Exception expected) {
                assertNotNull(expected);
            }
            assertEquals(0, db.clones().count());
            assertEquals(0, db.deniedPermissions().count());
            assertEquals(0, db.collapsedSpaces().count());
            assertEquals(0, db.globalDeviceProfile().count());
            assertEquals(0, db.persistenceSettings().count());
            assertEquals(0, db.lastActiveLaunch().count());
            assertEquals(0, db.migrationMetadata().count());
        } finally {
            db.close();
        }
    }

    @Test public void importedRowsSurviveDatabaseCloseAndReopen() throws Exception {
        LegacyCloneSnapshot snapshot = populatedSnapshot(true);
        ClonePersistenceDatabase first = Room.databaseBuilder(context,
                ClonePersistenceDatabase.class, TEST_DB).allowMainThreadQueries().build();
        assertEquals(LegacyCloneRoomImporter.Result.IMPORTED, importOnWorker(first, snapshot));
        first.close();

        ClonePersistenceDatabase reopened = Room.databaseBuilder(context,
                ClonePersistenceDatabase.class, TEST_DB).allowMainThreadQueries().build();
        try {
            assertTrue(LegacyCloneRoomVerifier.matches(reopened, snapshot));
            assertEquals(1, reopened.clones().count());
            assertEquals("com.example.stale", reopened.lastActiveLaunch().get().packageName);
        } finally {
            reopened.close();
        }
    }

    @Test public void emptySnapshotWithoutActiveMarkerImportsAndVerifies() throws Exception {
        SharedPreferences prefs = context.getSharedPreferences(
                LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE);
        assertTrue(prefs.edit().putString(LegacyCloneSnapshot.KEY_CLONES, "[]").commit());
        LegacyCloneSnapshot snapshot = LegacyCloneSnapshot.capture(context);
        ClonePersistenceDatabase db = inMemoryDb();
        try {
            assertEquals(LegacyCloneRoomImporter.Result.IMPORTED, importOnWorker(db, snapshot));
            assertTrue(LegacyCloneRoomVerifier.matches(db, snapshot));
            assertEquals(0, db.clones().count());
            assertNull(db.lastActiveLaunch().get());
            assertEquals(1, db.globalDeviceProfile().count());
            assertEquals(1, db.persistenceSettings().count());
        } finally {
            db.close();
        }
    }

    private ClonePersistenceDatabase inMemoryDb() {
        return Room.inMemoryDatabaseBuilder(context, ClonePersistenceDatabase.class)
                .allowMainThreadQueries().build();
    }

    private LegacyCloneSnapshot populatedSnapshot(boolean staleActiveMarker) {
        SharedPreferences prefs = context.getSharedPreferences(
                LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE);
        String clones = "[{\"pkg\":\"com.example.alpha\",\"uid\":10," +
                "\"name\":\"Alpha\",\"gpsOn\":true,\"lat\":40.7128,\"lng\":-74.006," +
                "\"locLabel\":\"New York\",\"devOn\":false,\"devBrand\":\"\"," +
                "\"devModel\":\"\",\"denied\":[\"android.permission.CAMERA\"]}]";
        SharedPreferences.Editor editor = prefs.edit()
                .putString(LegacyCloneSnapshot.KEY_CLONES, clones)
                .putStringSet(LegacyCloneSnapshot.KEY_COLLAPSED,
                        new HashSet<>(Arrays.asList("social")))
                .putBoolean(LegacyCloneSnapshot.KEY_MASTER_GPS, false)
                .putString(LegacyCloneSnapshot.KEY_GLOBAL_DEVICE,
                        "{\"enabled\":true,\"brand\":\"test\",\"manufacturer\":\"test-inc\"," +
                        "\"model\":\"Model-X\",\"device\":\"test-device\",\"countryIso\":\"us\"," +
                        "\"simOperator\":\"00101\",\"simOperatorName\":\"Test Carrier\"}");
        if (staleActiveMarker) {
            editor.putString(LegacyCloneSnapshot.KEY_ACTIVE_LAUNCH,
                    "{\"pkg\":\"com.example.stale\",\"uid\":99}");
        } else {
            editor.remove(LegacyCloneSnapshot.KEY_ACTIVE_LAUNCH);
        }
        assertTrue("Test preferences must be committed", editor.commit());
        return LegacyCloneSnapshot.capture(context);
    }

    private LegacyCloneRoomImporter.Result importOnWorker(
            final ClonePersistenceDatabase db, final LegacyCloneSnapshot snapshot) throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        try {
            Future<LegacyCloneRoomImporter.Result> future = executor.submit(
                    new Callable<LegacyCloneRoomImporter.Result>() {
                        @Override public LegacyCloneRoomImporter.Result call() {
                            return LegacyCloneRoomImporter.importIntoEmptyDatabase(db, snapshot);
                        }
                    });
            return future.get();
        } finally {
            executor.shutdownNow();
        }
    }
}
