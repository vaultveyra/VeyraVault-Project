package com.veyravault.space.core.persistence;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.Process;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CountDownLatch;

/** Debug-only secondary-process service for real OS-kill/SQLite recovery instrumentation. */
public final class CloneMigrationCrashTestService extends Service {
    public static final String ACTION_IMPORT_AND_PAUSE = "com.veyravault.space.test.IMPORT_AND_PAUSE";
    public static final String ACTION_VERIFY_EMPTY = "com.veyravault.space.test.VERIFY_EMPTY";
    private static final String TEST_DIRECTORY = "migration-process-death-test";

    @Override public int onStartCommand(Intent intent, int flags, final int startId) {
        String action = intent == null ? null : intent.getAction();
        if (ACTION_IMPORT_AND_PAUSE.equals(action)) {
            new Thread(new Runnable() { @Override public void run() { runImportAndPause(); } },
                    "migration-crash-import").start();
        } else if (ACTION_VERIFY_EMPTY.equals(action)) {
            new Thread(new Runnable() { @Override public void run() { verifyEmptyAfterRestart(startId); } },
                    "migration-crash-verify").start();
        } else {
            stopSelf(startId);
        }
        return START_NOT_STICKY;
    }

    private void runImportAndPause() {
        try {
            LegacyCloneSnapshot snapshot = LegacyCloneSnapshot.capture(getApplicationContext());
            ClonePersistenceDatabase database = ClonePersistenceDatabaseProvider.get(getApplicationContext());
            LegacyCloneRoomImporter.importIntoEmptyDatabaseWithCheckpoint(
                    database, snapshot, new LegacyCloneRoomImporter.TransactionCheckpoint() {
                        @Override public void afterCloneAndPermissionRowsInserted() {
                            try {
                                writeMarker("checkpoint.txt", "pid=" + Process.myPid()
                                        + ";checkpoint=after_clone_and_permission_inserts");
                                new CountDownLatch(1).await();
                            } catch (InterruptedException error) {
                                Thread.currentThread().interrupt();
                                throw new IllegalStateException("Crash-test checkpoint interrupted", error);
                            } catch (IOException error) {
                                throw new IllegalStateException("Unable to persist crash-test checkpoint", error);
                            }
                        }
                    });
            writeMarker("error.txt", "Import returned without reaching the process-death checkpoint");
        } catch (Throwable error) {
            try { writeMarker("error.txt", error.getClass().getName() + ": " + String.valueOf(error.getMessage())); }
            catch (IOException ignored) { }
        }
    }

    private void verifyEmptyAfterRestart(int startId) {
        try {
            ClonePersistenceDatabase database = ClonePersistenceDatabaseProvider.get(getApplicationContext());
            String result = "pid=" + Process.myPid()
                    + ";clones=" + database.clones().count()
                    + ";permissions=" + database.deniedPermissions().count()
                    + ";collapsed=" + database.collapsedSpaces().count()
                    + ";profile=" + database.globalDeviceProfile().count()
                    + ";settings=" + database.persistenceSettings().count()
                    + ";active=" + database.lastActiveLaunch().count()
                    + ";metadata=" + database.migrationMetadata().count();
            database.close();
            writeMarker("verified.txt", result);
        } catch (Throwable error) {
            try { writeMarker("error.txt", error.getClass().getName() + ": " + String.valueOf(error.getMessage())); }
            catch (IOException ignored) { }
        } finally {
            stopSelf(startId);
        }
    }

    private void writeMarker(String name, String value) throws IOException {
        File directory = new File(getFilesDir(), TEST_DIRECTORY);
        if (!directory.exists() && !directory.mkdirs()) throw new IOException("Cannot create test marker directory");
        try (FileOutputStream output = new FileOutputStream(new File(directory, name), false)) {
            output.write(value.getBytes(StandardCharsets.UTF_8));
            output.flush();
            output.getFD().sync();
        }
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
