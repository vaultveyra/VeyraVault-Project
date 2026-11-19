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
    private static final String KEY_LEGACY_LOCATION_CLEARED = "legacyLocationCleared";
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

    private static boolean isCompatibleRoot(JSONObject root) {
        if (root == null || root.optInt("schemaVersion", SCHEMA_VERSION) != SCHEMA_VERSION) return false;
        Object global = root.opt("global");
        Object clones = root.opt("clones");
        return (global == null || global instanceof JSONObject)
                && (clones == null || clones instanceof JSONObject);
    }

    private static boolean writeRoot(Context context, JSONObject root) {
        if (!isCompatibleRoot(root)) return false;
        try {
            root.put("schemaVersion", SCHEMA_VERSION);
            return prefs(context).edit().putString(KEY_DATA, root.toString()).commit();
        } catch (Exception ignored) {
            return false;
        }
    }

    static synchronized ProfileSettings readGlobalStrict(Context context) throws Exception {
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) throw new IllegalStateException("Profile schema is malformed or unsupported");
        return fromJsonStrict(root.optJSONObject("global"));
    }

    static synchronized ProfileSettings readCloneOverrideStrict(Context context,
                                                                  String packageName, int userId) throws Exception {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0)
            throw new IllegalArgumentException("Clone identity is invalid");
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) throw new IllegalStateException("Profile schema is malformed or unsupported");
        JSONObject clones = root.optJSONObject("clones");
        Object raw = clones == null ? null : clones.opt(cloneKey(packageName, userId));
        if (raw != null && !(raw instanceof JSONObject))
            throw new IllegalStateException("Clone profile entry is malformed");
        return fromJsonStrict((JSONObject) raw);
    }

    private static ProfileSettings fromJsonStrict(JSONObject json) throws Exception {
        ProfileSettings out = new ProfileSettings();
        if (json == null) return out;
        Object locale = json.opt("localeTag");
        Object zone = json.opt("timeZoneId");
        Object enabled = json.opt("locationEnabled");
        Object latitude = json.opt("latitude");
        Object longitude = json.opt("longitude");
        Object legacyLocationCleared = json.opt(KEY_LEGACY_LOCATION_CLEARED);
        if (legacyLocationCleared != null && !(legacyLocationCleared instanceof Boolean))
            throw new IllegalStateException("legacyLocationCleared is invalid");
        if (locale != null && !(locale instanceof String)) throw new IllegalStateException("localeTag is invalid");
        if (zone != null && !(zone instanceof String)) throw new IllegalStateException("timeZoneId is invalid");
        if (enabled != null && !(enabled instanceof Boolean)) throw new IllegalStateException("locationEnabled is invalid");
        if (latitude != null && !(latitude instanceof Number)) throw new IllegalStateException("latitude is invalid");
        if (longitude != null && !(longitude instanceof Number)) throw new IllegalStateException("longitude is invalid");
        // Semantic invalidity is field-scoped: ignore only the bad value so the
        // resolver can continue to the next source for that field. Structural type
        // errors still fail the strict read and are never silently coerced.
        out.localeTag = ProfileSettings.isLocaleTagValid((String) locale) ? (String) locale : null;
        out.timeZoneId = ProfileSettings.isTimeZoneIdValid((String) zone) ? (String) zone : null;
        out.locationEnabled = (Boolean) enabled;
        Double lat = latitude == null ? null : ((Number) latitude).doubleValue();
        Double lng = longitude == null ? null : ((Number) longitude).doubleValue();
        out.latitude = ProfileSettings.isLatitudeValid(lat) ? lat : null;
        out.longitude = ProfileSettings.isLongitudeValid(lng) ? lng : null;
        return out;
    }

    public static synchronized ProfileSettings getGlobal(Context context) {
        return fromJson(readRoot(context).optJSONObject("global"));
    }

    public static synchronized ProfileSettings getCloneOverride(Context context,
                                                                 String packageName, int userId) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0)
            return new ProfileSettings();
        JSONObject clones = readRoot(context).optJSONObject("clones");
        return fromJson(clones == null ? null : clones.optJSONObject(cloneKey(packageName, userId)));
    }

    public static synchronized boolean saveGlobal(Context context, ProfileSettings settings) {
        if (settings == null || !settings.isValid()) return false;
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) return false;
        try {
            JSONObject global = toJson(settings, root.optJSONObject("global"));
            if (global.length() == 0) root.remove("global");
            else root.put("global", global);
            return writeRoot(context, root);
        } catch (Exception ignored) {
            return false;
        }
    }

    private static boolean isKnownField(String field) {
        return "localeTag".equals(field) || "timeZoneId".equals(field)
                || "locationEnabled".equals(field) || "latitude".equals(field)
                || "longitude".equals(field);
    }

    /**
     * Clears all clone location fields in one profile commit and records an import tombstone.
     * The tombstone prevents a later additive legacy scan from resurrecting the old CloneStore
     * location after the user explicitly chose inheritance from the Global/System profile.
     */
    public static synchronized boolean clearCloneLocationOverrides(
            Context context, String packageName, int userId) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0) return false;
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) return false;
        try {
            JSONObject clones = root.optJSONObject("clones");
            if (clones == null) clones = new JSONObject();
            String key = cloneKey(packageName, userId);
            JSONObject profile = clones.optJSONObject(key);
            if (profile == null) profile = new JSONObject();
            profile.remove("locationEnabled");
            profile.remove("latitude");
            profile.remove("longitude");
            profile.put(KEY_LEGACY_LOCATION_CLEARED, true);
            clones.put(key, profile);
            root.put("clones", clones);
            return writeRoot(context, root);
        } catch (Exception error) {
            return false;
        }
    }

    /** Remove one clone override only; all other fields and other clones are retained. */
    public static synchronized boolean clearCloneOverrideField(Context context, String packageName,
                                                                 int userId, String field) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0
                || !isKnownField(field)) return false;
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) return false;
        try {
            JSONObject clones = root.optJSONObject("clones");
            if (clones == null) return true;
            String key = cloneKey(packageName, userId);
            JSONObject profile = clones.optJSONObject(key);
            if (profile == null || !profile.has(field)) return true;
            profile.remove(field);
            if (profile.length() == 0) clones.remove(key);
            root.put("clones", clones);
            return writeRoot(context, root);
        } catch (Exception ignored) {
            return false;
        }
    }

    /** Atomically replaces the global location fields while preserving locale/time-zone defaults. */
    public static synchronized boolean saveGlobalLocationOverrides(
            Context context, Boolean enabled, Double latitude, Double longitude) {
        if (!ProfileSettings.isLatitudeValid(latitude) || !ProfileSettings.isLongitudeValid(longitude)) {
            return false;
        }
        if (Boolean.TRUE.equals(enabled) && (latitude == null || longitude == null)) return false;
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) return false;
        try {
            JSONObject global = root.optJSONObject("global");
            if (global == null) global = new JSONObject();
            if (enabled == null) global.remove("locationEnabled");
            else global.put("locationEnabled", enabled);
            if (latitude == null) global.remove("latitude");
            else global.put("latitude", latitude);
            if (longitude == null) global.remove("longitude");
            else global.put("longitude", longitude);
            if (global.length() == 0) root.remove("global");
            else root.put("global", global);
            return writeRoot(context, root);
        } catch (Exception error) {
            return false;
        }
    }

    /** Clears the three global location fields together while preserving locale/time-zone defaults. */
    public static synchronized boolean clearGlobalLocationOverrides(Context context) {
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) return false;
        try {
            JSONObject global = root.optJSONObject("global");
            if (global == null) return true;
            global.remove("locationEnabled");
            global.remove("latitude");
            global.remove("longitude");
            if (global.length() == 0) root.remove("global");
            else root.put("global", global);
            return writeRoot(context, root);
        } catch (Exception error) {
            return false;
        }
    }

    /** Remove one global default only; all other defaults and clone overrides are retained. */
    public static synchronized boolean clearGlobalField(Context context, String field) {
        if (!isKnownField(field)) return false;
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) return false;
        try {
            JSONObject global = root.optJSONObject("global");
            if (global == null || !global.has(field)) return true;
            global.remove(field);
            if (global.length() == 0) root.remove("global");
            else root.put("global", global);
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
        if (!isCompatibleRoot(root)) return false;
        try {
            JSONObject clones = root.optJSONObject("clones");
            if (clones == null) clones = new JSONObject();
            String key = cloneKey(packageName, userId);
            JSONObject profile = toJson(settings, clones.optJSONObject(key));
            if (profile.length() == 0) clones.remove(key);
            else clones.put(key, profile);
            root.put("clones", clones);
            return writeRoot(context, root);
        } catch (Exception ignored) {
            return false;
        }
    }

    /** Strict runtime resolver: malformed profile structure is reported, never treated as empty. */
    public static synchronized ProfileResolver.ResolvedProfile resolveStrict(
            Context context, String packageName, int userId, ProfileSettings systemFallback) throws Exception {
        return ProfileResolver.resolve(
                readCloneOverrideStrict(context, packageName, userId),
                readGlobalStrict(context),
                systemFallback);
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
    public static boolean migrateLegacyLocationSettings(Context context) {
        // Strictly validate the entire legacy registry before importing anything.
        final List<CloneStore.CloneEntry> legacy;
        try {
            legacy = CloneStore.readAllStrict(context);
        } catch (Exception invalidLegacyData) {
            return false;
        }
        return importLegacyLocationSettings(context, legacy);
    }

    /**
     * Applies an already validated legacy snapshot. Package-private for instrumentation so
     * migration semantics can be tested without writing to the CloneStore preference namespace.
     */
    static synchronized boolean importLegacyLocationSettings(
            Context context, List<CloneStore.CloneEntry> legacy) {
        if (context == null || legacy == null) return false;
        SharedPreferences p = prefs(context);
        JSONObject root = readRoot(context);
        if (!isCompatibleRoot(root)) return false;
        try {
            JSONObject clones = root.optJSONObject("clones");
            if (clones == null) clones = new JSONObject();
            boolean changed = false;
            for (CloneStore.CloneEntry entry : legacy) {
                if (entry == null || entry.packageName == null || entry.packageName.trim().isEmpty()
                        || entry.userId < 0 || !entry.mockGpsEnabled) continue;
                String key = cloneKey(entry.packageName, entry.userId);
                Object existingValue = clones.opt(key);
                if (existingValue != null && !(existingValue instanceof JSONObject)) return false;
                if (existingValue instanceof JSONObject) {
                    Object tombstone = ((JSONObject) existingValue).opt(KEY_LEGACY_LOCATION_CLEARED);
                    if (tombstone != null && !(tombstone instanceof Boolean)) return false;
                    if (Boolean.TRUE.equals(tombstone)) continue;
                }
                JSONObject existing = existingValue instanceof JSONObject
                        ? (JSONObject) existingValue : null;
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
        // Null means "not supplied" during save, so a partial update cannot erase
        // sibling overrides. Explicit clear methods remove one selected field.
        if (settings.localeTag != null) out.put("localeTag", settings.localeTag);
        if (settings.timeZoneId != null) out.put("timeZoneId", settings.timeZoneId);
        if (settings.locationEnabled != null) out.put("locationEnabled", settings.locationEnabled);
        if (settings.latitude != null) out.put("latitude", settings.latitude);
        if (settings.longitude != null) out.put("longitude", settings.longitude);
        if (settings.locationEnabled != null || settings.latitude != null || settings.longitude != null) {
            out.remove(KEY_LEGACY_LOCATION_CLEARED);
        }
        return out;
    }

    private static ProfileSettings fromJson(JSONObject json) {
        ProfileSettings out = new ProfileSettings();
        if (json == null) return out;
        Object locale = json.opt("localeTag");
        Object zone = json.opt("timeZoneId");
        Object enabled = json.opt("locationEnabled");
        Object latitude = json.opt("latitude");
        Object longitude = json.opt("longitude");
        if (locale instanceof String && ProfileSettings.isLocaleTagValid((String) locale))
            out.localeTag = (String) locale;
        if (zone instanceof String && ProfileSettings.isTimeZoneIdValid((String) zone))
            out.timeZoneId = (String) zone;
        if (enabled instanceof Boolean) out.locationEnabled = (Boolean) enabled;
        if (latitude instanceof Number) {
            double value = ((Number) latitude).doubleValue();
            if (ProfileSettings.isLatitudeValid(value)) out.latitude = value;
        }
        if (longitude instanceof Number) {
            double value = ((Number) longitude).doubleValue();
            if (ProfileSettings.isLongitudeValid(value)) out.longitude = value;
        }
        return out;
    }
}
