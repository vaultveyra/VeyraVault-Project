package com.veyravault.space.core.persistence;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class LegacyCloneSnapshotBackupInstrumentationTest {
    private static final String BACKUP_DIRECTORY = "migration-backups";
    private static final String BACKUP_FILE = "clone-store-snapshot-v1.json";

    private Context context;
    private File backupFile;
    private File backupSidecar;

    @Before public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        context.getSharedPreferences(LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE)
                .edit().clear().commit();
        File directory = new File(context.getFilesDir(), BACKUP_DIRECTORY);
        backupFile = new File(directory, BACKUP_FILE);
        backupSidecar = new File(backupFile.getPath() + ".bak");
        deleteBackupFiles();
    }

    @After public void tearDown() {
        context.getSharedPreferences(LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE)
                .edit().clear().commit();
        deleteBackupFiles();
    }

    @Test public void backupIsWrittenReadBackAndReusedForExactSnapshot() throws Exception {
        LegacyCloneSnapshot snapshot = LegacyCloneSnapshot.capture(context);

        LegacyCloneSnapshotBackup.Receipt first =
                LegacyCloneSnapshotBackup.writeAndVerify(context, snapshot);
        assertEquals(snapshot.sha256(), first.sha256);
        assertTrue(first.byteCount > 0);
        assertTrue(backupFile.isFile());
        byte[] original = readFile(backupFile);

        LegacyCloneSnapshotBackup.Receipt second =
                LegacyCloneSnapshotBackup.writeAndVerify(context, snapshot);
        assertEquals(first.sha256, second.sha256);
        assertEquals(first.byteCount, second.byteCount);
        assertArrayEquals(original, readFile(backupFile));
    }

    @Test public void immutableBackupRejectsDifferentSnapshotWithoutChangingOriginal() throws Exception {
        LegacyCloneSnapshot firstSnapshot = LegacyCloneSnapshot.capture(context);
        LegacyCloneSnapshotBackup.writeAndVerify(context, firstSnapshot);
        byte[] original = readFile(backupFile);

        SharedPreferences prefs = context.getSharedPreferences(
                LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE);
        assertTrue(prefs.edit().putBoolean(LegacyCloneSnapshot.KEY_MASTER_GPS, false).commit());
        LegacyCloneSnapshot differentSnapshot = LegacyCloneSnapshot.capture(context);

        try {
            LegacyCloneSnapshotBackup.writeAndVerify(context, differentSnapshot);
            fail("A different snapshot must not replace the immutable pre-migration backup");
        } catch (IOException expected) {
            assertNotNull(expected.getMessage());
        }
        assertArrayEquals(original, readFile(backupFile));
    }

    @Test public void corruptExistingBackupIsRejectedAndNeverOverwritten() throws Exception {
        LegacyCloneSnapshot snapshot = LegacyCloneSnapshot.capture(context);
        LegacyCloneSnapshotBackup.writeAndVerify(context, snapshot);

        byte[] corrupt = "intentionally-corrupt-backup".getBytes(StandardCharsets.UTF_8);
        try (FileOutputStream output = new FileOutputStream(backupFile, false)) {
            output.write(corrupt);
            output.getFD().sync();
        }

        try {
            LegacyCloneSnapshotBackup.writeAndVerify(context, snapshot);
            fail("A corrupt existing backup must be rejected");
        } catch (IOException expected) {
            assertNotNull(expected.getMessage());
        }
        assertArrayEquals(corrupt, readFile(backupFile));
    }

    private byte[] readFile(File file) throws IOException {
        java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream();
        try (java.io.FileInputStream input = new java.io.FileInputStream(file)) {
            byte[] buffer = new byte[4096];
            int count;
            while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
        }
        return output.toByteArray();
    }

    private void deleteBackupFiles() {
        if (backupFile != null && backupFile.exists()) backupFile.delete();
        if (backupSidecar != null && backupSidecar.exists()) backupSidecar.delete();
        if (backupFile != null && backupFile.getParentFile() != null
                && backupFile.getParentFile().exists()) {
            backupFile.getParentFile().delete();
        }
    }
}
