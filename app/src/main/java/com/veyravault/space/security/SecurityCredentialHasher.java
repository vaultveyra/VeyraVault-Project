package com.veyravault.space.security;

import java.nio.charset.Charset;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/**
 * Versioned password derivation for the local app lock.
 * Format: v2$pbkdf2-sha{1|256}$iterations$saltHex$derivedKeyHex
 */
public final class SecurityCredentialHasher {
    private static final String LEGACY_PREFIX = "VeyraSalt_";
    private static final String VERSION = "v2";
    private static final int ITERATIONS = 120000;
    private static final int SALT_BYTES = 16;
    private static final int KEY_BITS = 256;
    private static final Charset UTF8 = Charset.forName("UTF-8");
    private static final SecureRandom RANDOM = new SecureRandom();

    private SecurityCredentialHasher() {}

    public static final class Verification {
        public final boolean valid;
        /** Non-null only when a verified legacy/older credential should be upgraded. */
        public final String upgradedHash;

        private Verification(boolean valid, String upgradedHash) {
            this.valid = valid;
            this.upgradedHash = upgradedHash;
        }
    }

    public static String createHash(String secret, boolean preferSha256) throws GeneralSecurityException {
        if (secret == null || secret.length() == 0) {
            throw new IllegalArgumentException("Credential must not be empty");
        }
        byte[] salt = new byte[SALT_BYTES];
        RANDOM.nextBytes(salt);
        String algorithm = preferSha256 ? "pbkdf2-sha256" : "pbkdf2-sha1";
        byte[] derived = derive(secret, salt, ITERATIONS, preferSha256);
        return VERSION + "$" + algorithm + "$" + ITERATIONS + "$"
                + toHex(salt) + "$" + toHex(derived);
    }

    public static Verification verify(String secret, String stored, boolean preferSha256)
            throws GeneralSecurityException {
        if (secret == null || stored == null || stored.length() == 0) {
            return new Verification(false, null);
        }

        if (stored.startsWith(VERSION + "$")) {
            String[] parts = stored.split("\\$", -1);
            if (parts.length != 5 || !VERSION.equals(parts[0])) {
                return new Verification(false, null);
            }
            final boolean sha256;
            if ("pbkdf2-sha256".equals(parts[1])) sha256 = true;
            else if ("pbkdf2-sha1".equals(parts[1])) sha256 = false;
            else return new Verification(false, null);

            int iterations;
            try {
                iterations = Integer.parseInt(parts[2]);
            } catch (NumberFormatException e) {
                return new Verification(false, null);
            }
            // Bound work factor to prevent corrupted preference data from causing a DoS.
            if (iterations < 10000 || iterations > 1000000) {
                return new Verification(false, null);
            }
            byte[] salt = fromHex(parts[3]);
            byte[] expected = fromHex(parts[4]);
            if (salt == null || salt.length != SALT_BYTES
                    || expected == null || expected.length != KEY_BITS / 8) {
                return new Verification(false, null);
            }
            byte[] actual = derive(secret, salt, iterations, sha256);
            return new Verification(MessageDigest.isEqual(expected, actual), null);
        }

        // Backward-compatible verification of the exact Stage-0 SHA-256 format.
        byte[] legacy = fromHex(stored);
        if (legacy == null || legacy.length != 32) {
            return new Verification(false, null);
        }
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] actual = digest.digest((LEGACY_PREFIX + secret).getBytes(UTF8));
        if (!MessageDigest.isEqual(legacy, actual)) {
            return new Verification(false, null);
        }
        return new Verification(true, createHash(secret, preferSha256));
    }

    private static byte[] derive(String secret, byte[] salt, int iterations, boolean sha256)
            throws GeneralSecurityException {
        String factoryName = sha256 ? "PBKDF2WithHmacSHA256" : "PBKDF2WithHmacSHA1";
        PBEKeySpec spec = new PBEKeySpec(secret.toCharArray(), salt, iterations, KEY_BITS);
        try {
            return SecretKeyFactory.getInstance(factoryName).generateSecret(spec).getEncoded();
        } finally {
            spec.clearPassword();
        }
    }

    private static String toHex(byte[] bytes) {
        char[] out = new char[bytes.length * 2];
        final char[] digits = "0123456789abcdef".toCharArray();
        for (int i = 0; i < bytes.length; i++) {
            int value = bytes[i] & 0xff;
            out[i * 2] = digits[value >>> 4];
            out[i * 2 + 1] = digits[value & 0x0f];
        }
        return new String(out);
    }

    private static byte[] fromHex(String value) {
        if (value == null || (value.length() & 1) != 0) return null;
        byte[] out = new byte[value.length() / 2];
        for (int i = 0; i < out.length; i++) {
            int high = Character.digit(value.charAt(i * 2), 16);
            int low = Character.digit(value.charAt(i * 2 + 1), 16);
            if (high < 0 || low < 0) return null;
            out[i] = (byte) ((high << 4) | low);
        }
        return out;
    }
}
