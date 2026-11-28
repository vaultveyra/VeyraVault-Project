package com.veyravault.space.core;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * One-way freshness fingerprint for the two process-scoped values verified by the
 * Locale/Time Zone runtime adapter. It stores no profile values and is not an identity token.
 */
public final class ProfileRuntimeFingerprint {
    private static final String SCHEMA = "veyra-runtime-profile-v1";
    private static final char[] HEX = "0123456789abcdef".toCharArray();

    private ProfileRuntimeFingerprint() { }

    public static String compute(ProfileResolver.ResolvedProfile profile) {
        if (profile == null) throw new IllegalArgumentException("Resolved runtime profile is required");
        return compute(profile.localeTag, profile.timeZoneId);
    }

    public static String compute(String localeTag, String timeZoneId) {
        StringBuilder canonical = new StringBuilder(SCHEMA).append('\n');
        append(canonical, "localeTag", localeTag);
        append(canonical, "timeZoneId", timeZoneId);
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(canonical.toString().getBytes(StandardCharsets.UTF_8));
            char[] encoded = new char[digest.length * 2];
            for (int i = 0; i < digest.length; i++) {
                int value = digest[i] & 0xff;
                encoded[i * 2] = HEX[value >>> 4];
                encoded[i * 2 + 1] = HEX[value & 0x0f];
            }
            return new String(encoded);
        } catch (NoSuchAlgorithmException impossible) {
            throw new IllegalStateException("SHA-256 is unavailable", impossible);
        }
    }

    private static void append(StringBuilder out, String key, String value) {
        out.append(key).append(':');
        if (value == null) out.append("-1:");
        else out.append(value.length()).append(':').append(value);
        out.append('\n');
    }

    public static boolean isValid(String fingerprint) {
        if (fingerprint == null || fingerprint.length() != 64) return false;
        for (int i = 0; i < fingerprint.length(); i++) {
            char value = fingerprint.charAt(i);
            if (!((value >= '0' && value <= '9') || (value >= 'a' && value <= 'f'))) return false;
        }
        return true;
    }

    public static boolean matches(String expected, String actual) {
        if (!isValid(expected) || !isValid(actual)) return false;
        return MessageDigest.isEqual(
                expected.getBytes(StandardCharsets.US_ASCII),
                actual.getBytes(StandardCharsets.US_ASCII));
    }
}
