package com.veyravault.space.core.persistence;

import android.content.Context;
import android.util.AtomicFile;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Writes and verifies an app-private, atomic backup of a validated legacy snapshot.
 * This class is opt-in and is not called by application startup or runtime CloneStore flows.
 */
public final class LegacyCloneSnapshotBackup {
    private static final int FORMAT_VERSION = 1;
    private static final String DIRECTORY = "migration-backups";
    private static final String FILE_NAME = "clone-store-snapshot-v1.json";

    public static final class Receipt {
        public final String sha256;
        public final int byteCount;

        private Receipt(String sha256, int byteCount) {
            this.sha256 = sha256;
            this.byteCount = byteCount;
        }
    }

    private LegacyCloneSnapshotBackup() { }

    public static Receipt writeAndVerify(Context context, LegacyCloneSnapshot snapshot) throws IOException {
        if (context == null) throw new IllegalArgumentException("Context is required");
        if (snapshot == null) throw new IllegalArgumentException("Validated snapshot is required");

        File directory = new File(context.getFilesDir(), DIRECTORY);
        if (!directory.exists() && !directory.mkdirs()) {
            throw new IOException("Unable to create app-private migration backup directory");
        }
        if (!directory.isDirectory()) throw new IOException("Migration backup path is not a directory");

        File baseFile = new File(directory, FILE_NAME);
        AtomicFile atomicFile = new AtomicFile(baseFile);
        String payload = snapshot.canonicalPayload();
        String digest = snapshot.sha256();
        byte[] expectedBytes;
        try {
            JSONObject envelope = new JSONObject();
            envelope.put("formatVersion", FORMAT_VERSION);
            envelope.put("snapshotSha256", digest);
            envelope.put("payload", payload);
            expectedBytes = envelope.toString().getBytes(StandardCharsets.UTF_8);
        } catch (Exception error) {
            throw new IOException("Unable to encode migration backup envelope", error);
        }

        FileOutputStream output = null;
        try {
            output = atomicFile.startWrite();
            output.write(expectedBytes);
            output.flush();
            output.getFD().sync();
            atomicFile.finishWrite(output);
            output = null;
        } catch (Exception error) {
            if (output != null) atomicFile.failWrite(output);
            throw new IOException("Atomic legacy snapshot backup write failed", error);
        }

        byte[] actualBytes;
        try (FileInputStream input = atomicFile.openRead()) {
            actualBytes = readFully(input);
        } catch (Exception error) {
            throw new IOException("Unable to read back migration backup", error);
        }
        if (!MessageDigest.isEqual(expectedBytes, actualBytes)) {
            throw new IOException("Migration backup read-back differs from the written bytes");
        }

        try {
            JSONObject verified = new JSONObject(new String(actualBytes, StandardCharsets.UTF_8));
            if (verified.getInt("formatVersion") != FORMAT_VERSION) {
                throw new IOException("Unsupported migration backup format version");
            }
            String storedPayload = verified.getString("payload");
            String storedDigest = verified.getString("snapshotSha256");
            String actualDigest = sha256(storedPayload);
            if (!MessageDigest.isEqual(
                    storedDigest.getBytes(StandardCharsets.US_ASCII),
                    actualDigest.getBytes(StandardCharsets.US_ASCII))) {
                throw new IOException("Migration backup checksum verification failed");
            }
            if (!MessageDigest.isEqual(
                    digest.getBytes(StandardCharsets.US_ASCII),
                    storedDigest.getBytes(StandardCharsets.US_ASCII))) {
                throw new IOException("Backup digest does not match the captured snapshot");
            }
        } catch (IOException error) {
            throw error;
        } catch (Exception error) {
            throw new IOException("Migration backup envelope is invalid", error);
        }
        return new Receipt(digest, actualBytes.length);
    }

    private static byte[] readFully(FileInputStream input) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int count;
        while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
        return output.toByteArray();
    }

    private static String sha256(String value) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder(digest.length * 2);
        for (byte item : digest) hex.append(String.format(java.util.Locale.ROOT, "%02x", item & 0xff));
        return hex.toString();
    }
}
