package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Stores only verified per-Clone runtime status metadata.
 * No profile values, credentials, accounts, sessions, package data or network identifiers are stored.
 */
public final class ProfileRuntimeStatusStore {
    private static final String PREFS = "veyra_profile_runtime_status_v1";
    private static final String KEY = "runtime_status_json";
    private static final int SCHEMA_VERSION = 1;

    public static final class Snapshot {
        public final boolean exists;
        public final boolean current;
        public final long profileRevision;
        public final long updatedAt;
        public final String processName;
        public final Map<String, ProfileFieldRegistry.ApplyStatus> statuses;

        private Snapshot(boolean exists, boolean current, long profileRevision,
                         long updatedAt, String processName,
                         Map<String, ProfileFieldRegistry.ApplyStatus> statuses) {
            this.exists = exists;
            this.current = current;
            this.profileRevision = profileRevision;
            this.updatedAt = updatedAt;
            this.processName = processName;
            this.statuses = Collections.unmodifiableMap(new LinkedHashMap<>(statuses));
        }

        static Snapshot empty(long currentRevision) {
            return new Snapshot(false, false, currentRevision, 0L, null,
                    Collections.<String, ProfileFieldRegistry.ApplyStatus>emptyMap());
        }
    }

    private ProfileRuntimeStatusStore() { }

    public static synchronized boolean record(Context context, String packageName, int userId,
                                              long profileRevision, String processName,
                                              Map<String, ProfileFieldRegistry.ApplyStatus> statuses) {
        if (context == null || !validIdentity(packageName, userId) || profileRevision < 0
                || processName == null || processName.trim().isEmpty()
                || processName.length() > 255 || statuses == null || statuses.isEmpty()) return false;
        try {
            long currentRevision = ProfileDocumentStore.readRevisionStrict(context);
            if (currentRevision != profileRevision) return false;
            JSONObject root = readRoot(context);
            if (root == null) return false;
            JSONObject profiles = root.optJSONObject("profiles");
            if (profiles == null) profiles = new JSONObject();

            JSONObject fields = new JSONObject();
            for (Map.Entry<String, ProfileFieldRegistry.ApplyStatus> entry : statuses.entrySet()) {
                String key = entry.getKey();
                ProfileFieldRegistry.Field definition = ProfileFieldRegistry.get(key);
                ProfileFieldRegistry.ApplyStatus status = entry.getValue();
                if (definition == null
                        || definition.capability != ProfileFieldRegistry.Capability.PROCESS_SCOPED
                        || (status != ProfileFieldRegistry.ApplyStatus.APPLIED
                            && status != ProfileFieldRegistry.ApplyStatus.FAILED
                            && status != ProfileFieldRegistry.ApplyStatus.NOT_TESTED)) return false;
                fields.put(key, status.name());
            }

            JSONObject profile = new JSONObject();
            profile.put("packageName", packageName);
            profile.put("userId", userId);
            profile.put("profileRevision", profileRevision);
            profile.put("updatedAt", System.currentTimeMillis());
            profile.put("processName", processName);
            profile.put("fields", fields);
            profiles.put(cloneKey(packageName, userId), profile);
            root.put("schemaVersion", SCHEMA_VERSION);
            root.put("profiles", profiles);
            return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                    .edit().putString(KEY, root.toString()).commit();
        } catch (Exception invalid) {
            return false;
        }
    }

    public static synchronized Snapshot read(Context context, String packageName, int userId) {
        if (context == null || !validIdentity(packageName, userId)) {
            return Snapshot.empty(-1L);
        }
        try {
            long currentRevision = ProfileDocumentStore.readRevisionStrict(context);
            JSONObject root = readRoot(context);
            if (root == null) return Snapshot.empty(currentRevision);
            JSONObject profiles = root.optJSONObject("profiles");
            if (profiles == null) return Snapshot.empty(currentRevision);
            JSONObject profile = profiles.optJSONObject(cloneKey(packageName, userId));
            if (profile == null
                    || !packageName.equals(profile.optString("packageName", ""))
                    || profile.optInt("userId", -1) != userId) return Snapshot.empty(currentRevision);

            long revision = profile.optLong("profileRevision", -1L);
            long updatedAt = profile.optLong("updatedAt", 0L);
            String processName = profile.optString("processName", null);
            JSONObject fields = profile.optJSONObject("fields");
            if (revision < 0 || updatedAt <= 0 || processName == null || fields == null) {
                return Snapshot.empty(currentRevision);
            }
            if (revision != currentRevision) {
                return new Snapshot(true, false, revision, updatedAt, processName,
                        Collections.<String, ProfileFieldRegistry.ApplyStatus>emptyMap());
            }

            Map<String, ProfileFieldRegistry.ApplyStatus> decoded = new LinkedHashMap<>();
            java.util.Iterator<String> keys = fields.keys();
            while (keys.hasNext()) {
                String key = keys.next();
                ProfileFieldRegistry.Field definition = ProfileFieldRegistry.get(key);
                if (definition == null
                        || definition.capability != ProfileFieldRegistry.Capability.PROCESS_SCOPED) {
                    return Snapshot.empty(currentRevision);
                }
                String raw = fields.optString(key, null);
                try {
                    ProfileFieldRegistry.ApplyStatus status =
                            ProfileFieldRegistry.ApplyStatus.valueOf(raw);
                    if (status != ProfileFieldRegistry.ApplyStatus.APPLIED
                            && status != ProfileFieldRegistry.ApplyStatus.FAILED
                            && status != ProfileFieldRegistry.ApplyStatus.NOT_TESTED) {
                        return Snapshot.empty(currentRevision);
                    }
                    decoded.put(key, status);
                } catch (RuntimeException invalid) {
                    return Snapshot.empty(currentRevision);
                }
            }
            return new Snapshot(true, true, revision, updatedAt, processName, decoded);
        } catch (Exception invalid) {
            return Snapshot.empty(-1L);
        }
    }

    private static JSONObject readRoot(Context context) throws JSONException {
        SharedPreferences preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String raw = preferences.getString(KEY, null);
        if (raw == null || raw.trim().isEmpty()) return new JSONObject();
        JSONObject root = new JSONObject(raw);
        int version = root.optInt("schemaVersion", SCHEMA_VERSION);
        if (version != SCHEMA_VERSION) return null;
        return root;
    }

    private static boolean validIdentity(String packageName, int userId) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0
                || packageName.length() > 255) return false;
        for (int i = 0; i < packageName.length(); i++) {
            char c = packageName.charAt(i);
            if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
                    || (c >= '0' && c <= '9') || c == '.' || c == '_')) return false;
        }
        return true;
    }

    private static String cloneKey(String packageName, int userId) {
        return packageName + "#" + userId;
    }
}
