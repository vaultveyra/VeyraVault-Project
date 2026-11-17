package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONException;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.List;

/**
 * Versioned, additive profile storage. Existing CloneStore preferences are read-only
 * migration input and are never deleted or rewritten by this class.
 */
public final class ProfileStore {
    private static final String PREFS = "veyravault_profiles_v1";
    private static final String KEY_DATA = "profiles_json";
    private static final String KEY_MIGRATED = "legacy_location_import_v1";
    private static final int SCHEMA_VERSION = 1;

    private ProfileStore() { }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static String cloneKey(String packageName, int userId) {
        return packageName + "#" + userId;
    }

    private static JSONObject readRoot(Context context) {
        try {
            String raw = prefs(context).getString(KEY_DATA, "");
            if (raw == null || raw.trim().isEmpty()) return new JSONObject();
            JSONObject root = new JSONObject(raw);
            if (root.optInt("schemaVersion", 0) != SCHEMA_VERSION) {
                // Unknown future schemas are not overwritten by an older app version.
                return root;
            }
            return root;
        } catch (Exception ignored) {
            // A malformed existing payload is quarantined in memory; never overwrite it.
            JSONObject invalid = new JSONObject();
            try { invalid.put("schemaVersion", -1); } catch (JSONException impossible) { }
            return invalid;
        }
    }

    private static boolean writeRoot(Context context, JSONObject root) {
        if (root.optInt("schemaVersion", SCHEMA_VERSION) != SCHEMA_VERSION) return false;
        try {
            root.put("schemaVersion", SCHEMA_VERSION);
            return prefs(context).edit().putString(KEY_DATA, root.toString()).commit();
        } catch (Exception ignored) {
            return false;
        }
    }

    public static synchronized ProfileSettings getGlobal(Context context) {
        return fromJson(readRoot(context).optJSONObject("global"));
    }

    public static synchronized ProfileSettings getCloneOverride(Context context,
                                                                 String packageName, int userId) {
        JSONObject clones = readRoot(context).optJSONObject("clones");
        return fromJson(clones == null ? null : clones.optJSONObject(cloneKey(packageName, userId)));
    }

    public static synchronized boolean saveGlobal(Context context, ProfileSettings settings) {
        if (settings == null || !settings.isValid()) return false;
        JSONObject root = readRoot(context);
        if (root.optInt("schemaVersion", SCHEMA_VERSION) != SCHEMA_VERSION) return false;
        try {
            root.put("global", toJson(settings, root.optJSONObject("global")));
            return writeRoot(context, root);
        } catch (Exception ignored) {
            return false;
        }
    }

    public static synchronized boolean saveCloneOverride(Context context, String packageName,
                                                          int userId, ProfileSettings settings) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0
                || settings == null || !settings.isValid()) return false;
        JSONObject root = readRoot(context);
        if (root.optInt("schemaVersion", SCHEMA_VERSION) != SCHEMA_VERSION) return false;
        try {
            JSONObject clones = root.optJSONObject("clones");
            if (clones == null) clones = new JSONObject();
            clones.put(cloneKey(packageName, userId),
                    toJson(settings, clones.optJSONObject(cloneKey(packageName, userId))));
            root.put("clones", clones);
            return writeRoot(context, root);
        } catch (Exception ignored) {
            return false;
        }
    }

    public static synchronized ProfileResolver.ResolvedProfile resolve(
            Context context, String packageName, int userId, ProfileSettings systemFallback) {
        return ProfileResolver.resolve(getCloneOverride(context, packageName, userId),
                getGlobal(context), systemFallback);
    }

    /**
     * Imports only unambiguous legacy GPS-enabled clone values. A legacy false value
     * is not imported because the old model cannot distinguish "off" from "unset".
     * The old preferences remain untouched; repeated calls are safe.
     */
    public static synchronized boolean migrateLegacyLocationSettings(Context context) {
        SharedPreferences p = prefs(context);
        // Re-scan on later launches as new clones may be added after the first import.
        // Existing profile fields are never overwritten, so this remains idempotent.

        // Validate the legacy JSON before reading through CloneStore, whose public
        // accessor intentionally returns an empty list when parsing fails.
        try {
            String legacyRaw = context.getSharedPreferences("veyravault_clones_v2", Context.MODE_PRIVATE)
                    .getString("clones_json", "[]");
            JSONArray legacyArray = new JSONArray(legacyRaw == null ? "[]" : legacyRaw);
            for (int i = 0; i < legacyArray.length(); i++) {
                if (!(legacyArray.opt(i) instanceof JSONObject)) return false;
            }
        } catch (Exception invalidLegacyData) {
            return false;
        }

        JSONObject root = readRoot(context);
        if (root.optInt("schemaVersion", SCHEMA_VERSION) != SCHEMA_VERSION) return false;
        try {
            JSONObject clones = root.optJSONObject("clones");
            if (clones == null) clones = new JSONObject();
            boolean changed = false;
            List<CloneStore.CloneEntry> legacy = CloneStore.getAll(context);
            for (CloneStore.CloneEntry entry : legacy) {
                if (entry == null || entry.packageName == null || !entry.mockGpsEnabled) continue;
                String key = cloneKey(entry.packageName, entry.userId);
                JSONObject existing = clones.optJSONObject(key);
                JSONObject imported = existing == null ? new JSONObject() : new JSONObject(existing.toString());
                boolean entryChanged = false;
                if (!imported.has("locationEnabled")) {
                    imported.put("locationEnabled", true);
                    entryChanged = true;
                }
                if (!imported.has("latitude") && validLatitude(entry.latitude)) {
                    imported.put("latitude", entry.latitude);
                    entryChanged = true;
                }
                if (!imported.has("longitude") && validLongitude(entry.longitude)) {
                    imported.put("longitude", entry.longitude);
                    entryChanged = true;
                }
                if (entryChanged) {
                    clones.put(key, imported);
                    changed = true;
                }
            }
            if (changed) {
                root.put("clones", clones);
                if (!writeRoot(context, root)) return false;
            }
            return p.edit().putBoolean(KEY_MIGRATED, true).commit();
        } catch (Exception ignored) {
            return false;
        }
    }

    private static boolean validLatitude(double value) {
        return !Double.isNaN(value) && !Double.isInfinite(value) && value >= -90.0 && value <= 90.0;
    }

    private static boolean validLongitude(double value) {
        return !Double.isNaN(value) && !Double.isInfinite(value) && value >= -180.0 && value <= 180.0;
    }

    private static JSONObject toJson(ProfileSettings settings, JSONObject existing) throws JSONException {
        JSONObject out = existing == null ? new JSONObject() : new JSONObject(existing.toString());
        putNullable(out, "localeTag", settings.localeTag);
        putNullable(out, "timeZoneId", settings.timeZoneId);
        putNullable(out, "locationEnabled", settings.locationEnabled);
        putNullable(out, "latitude", settings.latitude);
        putNullable(out, "longitude", settings.longitude);
        return out;
    }

    private static void putNullable(JSONObject out, String key, Object value) throws JSONException {
        if (value == null) out.remove(key);
        else out.put(key, value);
    }

    private static ProfileSettings fromJson(JSONObject json) {
        ProfileSettings out = new ProfileSettings();
        if (json == null) return out;
        if (json.has("localeTag") && !json.isNull("localeTag")) out.localeTag = json.optString("localeTag", null);
        if (json.has("timeZoneId") && !json.isNull("timeZoneId")) out.timeZoneId = json.optString("timeZoneId", null);
        if (json.has("locationEnabled") && !json.isNull("locationEnabled"))
            out.locationEnabled = json.optBoolean("locationEnabled");
        if (json.has("latitude") && !json.isNull("latitude")) out.latitude = json.optDouble("latitude");
        if (json.has("longitude") && !json.isNull("longitude")) out.longitude = json.optDouble("longitude");
        return out;
    }
}
