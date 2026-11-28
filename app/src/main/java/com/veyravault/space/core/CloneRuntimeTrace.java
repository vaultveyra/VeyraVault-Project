package com.veyravault.space.core;

import android.util.Log;

/**
 * Bounded, local-only lifecycle breadcrumbs for diagnosing virtual app startup.
 *
 * This class intentionally has no persistence, file, network, account, or session access.
 * The only output is a small allowlisted line to Android Logcat.
 */
public final class CloneRuntimeTrace {
    public static final String TAG = "VeyraCloneRuntime";

    public enum Event {
        ENGINE_LAUNCH_REQUEST,
        ENGINE_INSTALL_STATE_UNKNOWN,
        ENGINE_INSTALL_REQUIRED,
        ENGINE_INSTALL_FAILED,
        ENGINE_HOOK_SYNC_BEGIN,
        ENGINE_HOOK_SYNC_COMPLETE,
        ENGINE_HOOK_SYNC_FAILED,
        ENGINE_LAUNCH_CALL,
        ENGINE_LAUNCH_ACCEPTED,
        ENGINE_LAUNCH_REJECTED,
        ENGINE_LAUNCH_EXCEPTION,
        ENGINE_LIFECYCLE_CALLBACK_REGISTERED,
        ENGINE_LIFECYCLE_CALLBACK_REGISTRATION_FAILED,
        VIRTUAL_PROCESS_BEFORE_APP_CREATE,
        TARGET_APPLICATION_ONCREATE_BEGIN,
        TARGET_APPLICATION_ONCREATE_COMPLETE,
        PROFILE_DOCUMENT_RESOLVED,
        PROFILE_APPLY_RETURNED,
        PROFILE_READBACK_VERIFIED,
        PROFILE_READBACK_FAILED,
        PROFILE_PROCESS_BOUNDARY_REJECTED,
        PROFILE_FALLBACK
    }

    private CloneRuntimeTrace() { }

    public static void record(Event event, String packageName, String processName,
                              int virtualUserId, String outcome) {
        if (event == null) return;
        StringBuilder line = new StringBuilder(160);
        line.append("event=").append(event.name());
        append(line, "package", packageName);
        append(line, "process", processName);
        if (virtualUserId >= 0) {
            line.append(" userId=").append(virtualUserId);
        }
        append(line, "outcome", outcome);
        Log.i(TAG, line.toString());
    }

    private static void append(StringBuilder target, String key, String value) {
        if (value == null || value.trim().isEmpty()) return;
        target.append(' ').append(key).append('=').append(sanitize(value));
    }

    /** Prevents control characters, whitespace and unbounded values from entering Logcat. */
    private static String sanitize(String value) {
        int length = Math.min(value.length(), 96);
        StringBuilder safe = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            char c = value.charAt(i);
            boolean allowed = (c >= 'a' && c <= 'z')
                    || (c >= 'A' && c <= 'Z')
                    || (c >= '0' && c <= '9')
                    || c == '.' || c == '_' || c == ':' || c == '-';
            safe.append(allowed ? c : '_');
        }
        return safe.toString();
    }
}
