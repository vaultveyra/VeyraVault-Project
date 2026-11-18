package com.veyravault.space.core.persistence;

import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Process;
import android.os.SystemClock;
import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class LegacyCloneRoomProcessDeathInstrumentationTest {
    private static final String DATABASE_NAME = "veyravault_clone_store_room.db";
    private static final String TEST_DIRECTORY = "migration-process-death-test";
    private Context context;
    private File markerDirectory;
    private int killedServicePid = -1;

    @Before public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        context.getSharedPreferences(LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE)
                .edit().clear().commit();
        context.deleteDatabase(DATABASE_NAME);
        markerDirectory = new File(context.getFilesDir(), TEST_DIRECTORY);
        deleteRecursively(markerDirectory);
        seedLegacySnapshot();
    }

    @After public void tearDown() {
        if (killedServicePid > 0) Process.killProcess(killedServicePid);
        context.stopService(new Intent(context, CloneMigrationCrashTestService.class));
        context.getSharedPreferences(LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE)
                .edit().clear().commit();
        context.deleteDatabase(DATABASE_NAME);
        deleteRecursively(markerDirectory);
    }

    @Test public void osProcessDeathDuringRoomImportRollsBackAndRestartSeesEmptyDatabase()
            throws Exception {
        Intent importIntent = new Intent(context, CloneMigrationCrashTestService.class)
                .setAction(CloneMigrationCrashTestService.ACTION_IMPORT_AND_PAUSE);
        assertNotNull(context.startService(importIntent));
        String checkpoint = waitForMarker("checkpoint.txt", 30000L);
        assertTrue(checkpoint, checkpoint.contains("checkpoint=after_clone_and_permission_inserts"));
        killedServicePid = parsePid(checkpoint);
        assertTrue("Service must run in a separate process", killedServicePid > 0
                && killedServicePid != Process.myPid());

        Process.killProcess(killedServicePid);
        waitForProcessExit(killedServicePid, 15000L);

        Intent verifyIntent = new Intent(context, CloneMigrationCrashTestService.class)
                .setAction(CloneMigrationCrashTestService.ACTION_VERIFY_EMPTY);
        assertNotNull(context.startService(verifyIntent));
        String verified = waitForMarker("verified.txt", 30000L);
        int restartedPid = parsePid(verified);
        assertTrue("Verification must run in a fresh OS process", restartedPid > 0
                && restartedPid != killedServicePid);

        assertEquals(0, parseCount(verified, "clones"));
        assertEquals(0, parseCount(verified, "permissions"));
        assertEquals(0, parseCount(verified, "collapsed"));
        assertEquals(0, parseCount(verified, "profile"));
        assertEquals(0, parseCount(verified, "settings"));
        assertEquals(0, parseCount(verified, "active"));
        assertEquals(0, parseCount(verified, "metadata"));
    }

    private void seedLegacySnapshot() {
        SharedPreferences prefs = context.getSharedPreferences(LegacyCloneSnapshot.PREFS_NAME, Context.MODE_PRIVATE);
        String clones = "[{\"pkg\":\"com.example.crash\",\"uid\":41,\"name\":\"Crash Test\","
                + "\"gpsOn\":false,\"lat\":0.0,\"lng\":0.0,\"locLabel\":\","
                + "\"devOn\":false,\"devBrand\":\",\"devModel\":\","
                + "\"denied\":[\"android.permission.CAMERA\"]}]";
        assertTrue(prefs.edit()
                .putString(LegacyCloneSnapshot.KEY_CLONES, clones)
                .putStringSet(LegacyCloneSnapshot.KEY_COLLAPSED, new HashSet<>(Arrays.asList("social")))
                .putBoolean(LegacyCloneSnapshot.KEY_MASTER_GPS, false)
                .putString(LegacyCloneSnapshot.KEY_GLOBAL_DEVICE,
                        "{\"enabled\":true,\"brand\":\"test\",\"manufacturer\":\"test\","
                                + "\"model\":\"test-model\",\"device\":\"test-device\","
                                + "\"countryIso\":\"us\",\"simOperator\":\"00101\","
                                + "\"simOperatorName\":\"test-carrier\"}")
                .commit());
    }

    private String waitForMarker(String name, long timeoutMillis) throws Exception {
        File marker = new File(markerDirectory, name);
        File error = new File(markerDirectory, "error.txt");
        long deadline = SystemClock.elapsedRealtime() + timeoutMillis;
        while (SystemClock.elapsedRealtime() < deadline) {
            if (error.isFile()) throw new AssertionError("Crash-test service error: " + readText(error));
            if (marker.isFile()) return readText(marker);
            Thread.sleep(100L);
        }
        throw new AssertionError("Timed out waiting for " + name);
    }

    private void waitForProcessExit(int pid, long timeoutMillis) throws Exception {
        ActivityManager manager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
        long deadline = SystemClock.elapsedRealtime() + timeoutMillis;
        while (SystemClock.elapsedRealtime() < deadline) {
            boolean alive = false;
            List<ActivityManager.RunningAppProcessInfo> processes = manager.getRunningAppProcesses();
            if (processes != null) for (ActivityManager.RunningAppProcessInfo process : processes) {
                if (process.pid == pid) { alive = true; break; }
            }
            if (!alive) return;
            Thread.sleep(100L);
        }
        throw new AssertionError("Dedicated migration service process did not terminate after SIGKILL");
    }

    private int parsePid(String marker) { return Integer.parseInt(parseField(marker, "pid")); }
    private int parseCount(String marker, String name) { return Integer.parseInt(parseField(marker, name)); }

    private String parseField(String marker, String name) {
        for (String field : marker.split(";")) {
            if (field.startsWith(name + "=")) return field.substring(name.length() + 1);
        }
        throw new AssertionError("Missing " + name + " in marker: " + marker);
    }

    private String readText(File file) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        try (FileInputStream input = new FileInputStream(file)) {
            byte[] buffer = new byte[2048];
            int count;
            while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
        }
        return new String(output.toByteArray(), java.nio.charset.StandardCharsets.UTF_8);
    }

    private void deleteRecursively(File file) {
        if (file == null || !file.exists()) return;
        if (file.isDirectory()) {
            File[] children = file.listFiles();
            if (children != null) for (File child : children) deleteRecursively(child);
        }
        file.delete();
    }
}
