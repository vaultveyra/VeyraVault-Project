package com.veyravault.space.core.persistence;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

/**
 * Strict, read-only snapshot of the legacy CloneStore preferences.
 *
 * This class deliberately does not open Room, write preferences, create backup files,
 * or access BlackBox/virtual-app storage. A malformed or ambiguous legacy value aborts
 * capture instead of being interpreted as an empty registry.
 */
public final class LegacyCloneSnapshot {
    public static final String PREFS_NAME = "veyravault_clones_v2";
    public static final String KEY_CLONES = "clones_json";
    public static final String KEY_COLLAPSED = "collapsed_spaces";
    public static final String KEY_MASTER_GPS = "master_mock_gps";
    public static final String KEY_GLOBAL_DEVICE = "global_device_json";
    public static final String KEY_ACTIVE_LAUNCH = "active_launch_json";

    public static final class CloneRecord {
        public final String packageName;
        public final int userId;
        public final String displayName;
        public final boolean mockGpsEnabled;
        public final double latitude;
        public final double longitude;
        public final String locationLabel;
        public final boolean customDeviceEnabled;
        public final String deviceBrand;
        public final String deviceModel;
        public final Set<String> deniedPermissions;
        /** Original JSON object retained losslessly for forward/unknown-field compatibility. */
        public final String legacyJson;

        private CloneRecord(JSONObject source) throws Exception {
            packageName = requiredString(source, "pkg", "");
            userId = requiredInt(source, "uid", 0);
            displayName = optionalString(source, "name", packageName);
            mockGpsEnabled = optionalBoolean(source, "gpsOn", false);
            latitude = optionalDouble(source, "lat", 0.0d);
            longitude = optionalDouble(source, "lng", 0.0d);
            locationLabel = optionalString(source, "locLabel", "");
            customDeviceEnabled = optionalBoolean(source, "devOn", false);
            deviceBrand = optionalString(source, "devBrand", "");
            deviceModel = optionalString(source, "devModel", "");
            deniedPermissions = Collections.unmodifiableSet(readPermissions(source));
            legacyJson = source.toString();
        }
    }

    public static final class GlobalProfile {
        public final boolean enabled;
        public final String brand;
        public final String manufacturer;
        public final String model;
        public final String device;
        public final String countryIso;
        public final String simOperator;
        public final String simOperatorName;

        private GlobalProfile(JSONObject source) throws Exception {
            enabled = optionalBoolean(source, "enabled", true);
            brand = optionalString(source, "brand", "samsung");
            manufacturer = optionalString(source, "manufacturer", "samsung");
            model = optionalString(source, "model", "SM-S928B");
            device = optionalString(source, "device", "e3q");
            countryIso = optionalString(source, "countryIso", "us");
            simOperator = optionalString(source, "simOperator", "310260");
            simOperatorName = optionalString(source, "simOperatorName", "T-Mobile");
        }
    }

    public static final class ActiveLaunch {
        public final String packageName;
        public final int userId;

        private ActiveLaunch(JSONObject source) throws Exception {
            packageName = requiredString(source, "pkg", "");
            userId = requiredInt(source, "uid", 0);
        }
    }

    public final List<CloneRecord> clones;
    public final Set<String> collapsedSpaces;
    public final boolean masterMockGpsEnabled;
    public final GlobalProfile globalProfile;
    public final ActiveLaunch activeLaunch;
    public final boolean hadClonesKey;
    public final boolean hadCollapsedSpacesKey;
    public final boolean hadMasterGpsKey;
    public final boolean hadGlobalProfileKey;
    public final boolean hadActiveLaunchKey;
    private final String rawClones;
    private final String rawGlobalProfile;
    private final String rawActiveLaunch;

    private LegacyCloneSnapshot(List<CloneRecord> clones, Set<String> collapsedSpaces,
            boolean masterMockGpsEnabled, GlobalProfile globalProfile, ActiveLaunch activeLaunch,
            boolean hadClonesKey, boolean hadCollapsedSpacesKey, boolean hadMasterGpsKey,
            boolean hadGlobalProfileKey, boolean hadActiveLaunchKey, String rawClones,
            String rawGlobalProfile, String rawActiveLaunch) {
        this.clones = Collections.unmodifiableList(new ArrayList<>(clones));
        this.collapsedSpaces = Collections.unmodifiableSet(new TreeSet<>(collapsedSpaces));
        this.masterMockGpsEnabled = masterMockGpsEnabled;
        this.globalProfile = globalProfile;
        this.activeLaunch = activeLaunch;
        this.hadClonesKey = hadClonesKey;
        this.hadCollapsedSpacesKey = hadCollapsedSpacesKey;
        this.hadMasterGpsKey = hadMasterGpsKey;
        this.hadGlobalProfileKey = hadGlobalProfileKey;
        this.hadActiveLaunchKey = hadActiveLaunchKey;
        this.rawClones = rawClones;
        this.rawGlobalProfile = rawGlobalProfile;
        this.rawActiveLaunch = rawActiveLaunch;
    }

    public static LegacyCloneSnapshot capture(Context context) {
        if (context == null) throw new IllegalArgumentException("Context is required");
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        Map<String, ?> values = prefs.getAll();

        boolean hasClones = values.containsKey(KEY_CLONES);
        boolean hasCollapsed = values.containsKey(KEY_COLLAPSED);
        boolean hasMasterGps = values.containsKey(KEY_MASTER_GPS);
        boolean hasGlobal = values.containsKey(KEY_GLOBAL_DEVICE);
        boolean hasActive = values.containsKey(KEY_ACTIVE_LAUNCH);

        String rawClones = readPreferenceString(values, KEY_CLONES, "[]");
        String rawGlobal = readPreferenceString(values, KEY_GLOBAL_DEVICE, "");
        String rawActive = readPreferenceString(values, KEY_ACTIVE_LAUNCH, "");
        boolean masterGps = readPreferenceBoolean(values, KEY_MASTER_GPS, true);
        Set<String> collapsed = readPreferenceStringSet(values, KEY_COLLAPSED);

        try {
            JSONArray array = new JSONArray(rawClones);
            List<CloneRecord> clones = new ArrayList<>();
            Set<String> identities = new HashSet<>();
            for (int i = 0; i < array.length(); i++) {
                JSONObject object = array.optJSONObject(i);
                if (object == null) throw new IllegalStateException("Clone entry " + i + " is not a JSON object");
                CloneRecord record = new CloneRecord(object);
                if (record.packageName.trim().isEmpty()) throw new IllegalStateException("Clone entry " + i + " has an empty package name");
                if (record.userId < 0) throw new IllegalStateException("Clone entry " + i + " has a negative virtual user ID");
                if (record.mockGpsEnabled && (!isFinite(record.latitude) || !isFinite(record.longitude)
                        || record.latitude < -90.0d || record.latitude > 90.0d
                        || record.longitude < -180.0d || record.longitude > 180.0d)) {
                    throw new IllegalStateException("Clone entry " + i + " has invalid enabled-location coordinates");
                }
                String identity = record.packageName + "\u0000" + record.userId;
                if (!identities.add(identity)) throw new IllegalStateException("Duplicate clone identity: " + record.packageName + "/" + record.userId);
                clones.add(record);
            }
            Collections.sort(clones, new Comparator<CloneRecord>() {
                @Override public int compare(CloneRecord a, CloneRecord b) {
                    int byPackage = a.packageName.compareTo(b.packageName);
                    return byPackage != 0 ? byPackage : Integer.compare(a.userId, b.userId);
                }
            });

            GlobalProfile profile = new GlobalProfile(rawGlobal.isEmpty() ? new JSONObject() : new JSONObject(rawGlobal));
            ActiveLaunch active = rawActive.isEmpty() ? null : new ActiveLaunch(new JSONObject(rawActive));
            if (active != null && (active.packageName.trim().isEmpty() || active.userId < 0)) {
                throw new IllegalStateException("Invalid last-active-launch marker");
            }
            return new LegacyCloneSnapshot(clones, collapsed, masterGps, profile, active,
                    hasClones, hasCollapsed, hasMasterGps, hasGlobal, hasActive,
                    rawClones, rawGlobal, rawActive);
        } catch (Exception error) {
            throw new IllegalStateException("Legacy CloneStore snapshot rejected; original preferences were not changed", error);
        }
    }

    /**
     * Reconstructs a validated snapshot from a canonical backup payload without reading
     * or mutating the device's current SharedPreferences.
     */
    public static LegacyCloneSnapshot fromCanonicalPayload(String payload) {
        if (payload == null || payload.trim().isEmpty()) {
            throw new IllegalArgumentException("Canonical migration payload is required");
        }
        try {
            JSONObject root = new JSONObject(payload);
            String rawClones = root.getString("rawClones");
            String rawGlobal = root.getString("globalProfileRaw");
            String rawActive = root.getString("activeLaunchRaw");
            boolean hadClones = requireBoolean(root, "hadClonesKey");
            boolean hadCollapsed = requireBoolean(root, "hadCollapsedSpacesKey");
            boolean hadMasterGps = requireBoolean(root, "hadMasterGpsKey");
            boolean hadGlobal = requireBoolean(root, "hadGlobalProfileKey");
            boolean hadActive = requireBoolean(root, "hadActiveLaunchKey");
            boolean masterGps = requireBoolean(root, "masterMockGpsEnabled");

            JSONArray array = new JSONArray(rawClones);
            List<CloneRecord> clones = new ArrayList<>();
            Set<String> identities = new HashSet<>();
            for (int i = 0; i < array.length(); i++) {
                JSONObject object = array.optJSONObject(i);
                if (object == null) throw new IllegalStateException("Clone entry " + i + " is not a JSON object");
                CloneRecord record = new CloneRecord(object);
                if (record.packageName.trim().isEmpty()) throw new IllegalStateException("Clone entry " + i + " has an empty package name");
                if (record.userId < 0) throw new IllegalStateException("Clone entry " + i + " has a negative virtual user ID");
                if (record.mockGpsEnabled && (!isFinite(record.latitude) || !isFinite(record.longitude)
                        || record.latitude < -90.0d || record.latitude > 90.0d
                        || record.longitude < -180.0d || record.longitude > 180.0d)) {
                    throw new IllegalStateException("Clone entry " + i + " has invalid enabled-location coordinates");
                }
                String identity = record.packageName + "\\u0000" + record.userId;
                if (!identities.add(identity)) throw new IllegalStateException("Duplicate clone identity: " + record.packageName + "/" + record.userId);
                clones.add(record);
            }
            Collections.sort(clones, new Comparator<CloneRecord>() {
                @Override public int compare(CloneRecord a, CloneRecord b) {
                    int byPackage = a.packageName.compareTo(b.packageName);
                    return byPackage != 0 ? byPackage : Integer.compare(a.userId, b.userId);
                }
            });

            JSONArray collapsedArray = root.getJSONArray("collapsedSpaces");
            Set<String> collapsed = new TreeSet<>();
            for (int i = 0; i < collapsedArray.length(); i++) {
                Object value = collapsedArray.get(i);
                if (!(value instanceof String)) throw new IllegalStateException("Collapsed space at index " + i + " is not a String");
                collapsed.add((String) value);
            }
            GlobalProfile profile = new GlobalProfile(rawGlobal.isEmpty() ? new JSONObject() : new JSONObject(rawGlobal));
            ActiveLaunch active = rawActive.isEmpty() ? null : new ActiveLaunch(new JSONObject(rawActive));
            if (active != null && (active.packageName.trim().isEmpty() || active.userId < 0)) {
                throw new IllegalStateException("Invalid last-active-launch marker");
            }
            LegacyCloneSnapshot snapshot = new LegacyCloneSnapshot(clones, collapsed, masterGps,
                    profile, active, hadClones, hadCollapsed, hadMasterGps, hadGlobal, hadActive,
                    rawClones, rawGlobal, rawActive);
            if (!snapshot.canonicalPayload().equals(payload)) {
                throw new IllegalStateException("Backup payload is not in canonical form or contains unsupported fields");
            }
            return snapshot;
        } catch (Exception error) {
            throw new IllegalArgumentException("Canonical migration backup payload rejected", error);
        }
    }

    private static boolean requireBoolean(JSONObject object, String key) throws Exception {
        Object value = object.get(key);
        if (!(value instanceof Boolean)) throw new IllegalStateException("Canonical field " + key + " is not a Boolean");
        return (Boolean) value;
    }

    /** Deterministic envelope for checksum and later backup verification. */
    public String canonicalPayload() {
        try {
            JSONObject root = new JSONObject();
            JSONArray cloneArray = new JSONArray();
            for (CloneRecord clone : clones) {
                JSONObject item = new JSONObject();
                item.put("packageName", clone.packageName);
                item.put("userId", clone.userId);
                item.put("legacyJson", clone.legacyJson);
                JSONArray permissions = new JSONArray();
                List<String> sortedPermissions = new ArrayList<>(clone.deniedPermissions);
                Collections.sort(sortedPermissions);
                for (String permission : sortedPermissions) permissions.put(permission);
                item.put("deniedPermissions", permissions);
                cloneArray.put(item);
            }
            root.put("clones", cloneArray);
            JSONArray collapsed = new JSONArray();
            for (String value : collapsedSpaces) collapsed.put(value);
            root.put("collapsedSpaces", collapsed);
            root.put("masterMockGpsEnabled", masterMockGpsEnabled);
            root.put("globalProfileRaw", rawGlobalProfile);
            root.put("activeLaunchRaw", rawActiveLaunch);
            root.put("hadClonesKey", hadClonesKey);
            root.put("hadCollapsedSpacesKey", hadCollapsedSpacesKey);
            root.put("hadMasterGpsKey", hadMasterGpsKey);
            root.put("hadGlobalProfileKey", hadGlobalProfileKey);
            root.put("hadActiveLaunchKey", hadActiveLaunchKey);
            root.put("rawClones", rawClones);
            return root.toString();
        } catch (Exception error) {
            throw new IllegalStateException("Unable to canonicalize legacy snapshot", error);
        }
    }

    public String sha256() {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(canonicalPayload().getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder(digest.length * 2);
            for (byte value : digest) hex.append(String.format(java.util.Locale.ROOT, "%02x", value & 0xff));
            return hex.toString();
        } catch (Exception error) {
            throw new IllegalStateException("Unable to hash legacy snapshot", error);
        }
    }

    private static String readPreferenceString(Map<String, ?> values, String key, String fallback) {
        if (!values.containsKey(key)) return fallback;
        Object value = values.get(key);
        if (!(value instanceof String)) throw new IllegalStateException("Preference " + key + " is not a String");
        return (String) value;
    }

    private static boolean readPreferenceBoolean(Map<String, ?> values, String key, boolean fallback) {
        if (!values.containsKey(key)) return fallback;
        Object value = values.get(key);
        if (!(value instanceof Boolean)) throw new IllegalStateException("Preference " + key + " is not a Boolean");
        return (Boolean) value;
    }

    private static Set<String> readPreferenceStringSet(Map<String, ?> values, String key) {
        Set<String> result = new TreeSet<>();
        if (!values.containsKey(key)) return result;
        Object value = values.get(key);
        if (!(value instanceof Set)) throw new IllegalStateException("Preference " + key + " is not a String set");
        for (Object item : (Set<?>) value) {
            if (!(item instanceof String)) throw new IllegalStateException("Preference " + key + " contains a non-String value");
            result.add((String) item);
        }
        return result;
    }

    private static Set<String> readPermissions(JSONObject source) throws Exception {
        if (!source.has("denied") || source.isNull("denied")) return new TreeSet<>();
        Object raw = source.get("denied");
        if (!(raw instanceof JSONArray)) throw new IllegalStateException("Denied permissions field is not a JSON array");
        return readStringSet((JSONArray) raw);
    }

    private static Set<String> readStringSet(JSONArray array) throws Exception {
        Set<String> result = new TreeSet<>();
        if (array == null) return result;
        for (int i = 0; i < array.length(); i++) {
            Object value = array.get(i);
            if (!(value instanceof String)) throw new IllegalStateException("Denied permission at index " + i + " is not a String");
            result.add((String) value);
        }
        return result;
    }

    private static String requiredString(JSONObject object, String key, String fallback) throws Exception {
        if (!object.has(key) || object.isNull(key)) return fallback;
        Object value = object.get(key);
        if (!(value instanceof String)) throw new IllegalStateException("Field " + key + " is not a String");
        return (String) value;
    }

    private static String optionalString(JSONObject object, String key, String fallback) throws Exception {
        return requiredString(object, key, fallback);
    }

    private static boolean optionalBoolean(JSONObject object, String key, boolean fallback) throws Exception {
        if (!object.has(key) || object.isNull(key)) return fallback;
        Object value = object.get(key);
        if (!(value instanceof Boolean)) throw new IllegalStateException("Field " + key + " is not a Boolean");
        return (Boolean) value;
    }

    private static int requiredInt(JSONObject object, String key, int fallback) throws Exception {
        if (!object.has(key) || object.isNull(key)) return fallback;
        Object value = object.get(key);
        if (!(value instanceof Number)) throw new IllegalStateException("Field " + key + " is not numeric");
        double number = ((Number) value).doubleValue();
        if (!isFinite(number) || number != Math.rint(number) || number < Integer.MIN_VALUE || number > Integer.MAX_VALUE) {
            throw new IllegalStateException("Field " + key + " is not a valid integer");
        }
        return (int) number;
    }

    private static double optionalDouble(JSONObject object, String key, double fallback) throws Exception {
        if (!object.has(key) || object.isNull(key)) return fallback;
        Object value = object.get(key);
        if (!(value instanceof Number)) throw new IllegalStateException("Field " + key + " is not numeric");
        double number = ((Number) value).doubleValue();
        if (!isFinite(number)) throw new IllegalStateException("Field " + key + " is not finite");
        return number;
    }

    private static boolean isFinite(double value) {
        return !Double.isNaN(value) && !Double.isInfinite(value);
    }
}
