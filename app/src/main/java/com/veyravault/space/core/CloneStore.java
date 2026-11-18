package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class CloneStore {
    private static final String PREF = "veyravault_clones_v2";
    private static final String KEY_CLONES = "clones_json";
    private static final String KEY_COLLAPSED = "collapsed_spaces";
    private static final String KEY_MASTER_GPS = "master_mock_gps";
    private static final String KEY_GLOBAL_DEV = "global_device_json";
    private static final String KEY_ACTIVE_LAUNCH = "active_launch_json";

    public static class CloneEntry {
        public String packageName;
        public int userId; // Space N -> userId = N - 1
        public String displayName;
        public boolean mockGpsEnabled;
        public double latitude;
        public double longitude;
        public String locationLabel = "";
        public boolean customDeviceEnabled;
        public String deviceBrand = "";
        public String deviceModel = "";
        public Set<String> deniedPermissions = new HashSet<String>();

        public int getSpaceNumber() {
            return userId + 1;
        }
    }

    public static class GlobalEnvConfig {
        public boolean enabled = true;
        public String brand = "samsung";
        public String manufacturer = "samsung";
        public String model = "SM-S928B"; // Saved profile metadata; not applied by the pinned engine.
        public String device = "e3q";
        public String countryIso = "us";
        public String simOperator = "310260";
        public String simOperatorName = "T-Mobile";
    }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    /**
     * Strict registry reader for mutation paths. Unlike getAll(), this never converts
     * malformed or ambiguous persisted data into an empty registry.
     */
    static List<CloneEntry> readAllStrict(Context c) throws Exception {
        if (c == null) throw new IllegalArgumentException("Context is required");
        SharedPreferences store = prefs(c);
        Map<String, ?> values = store.getAll();
        Object rawValue = values.get(KEY_CLONES);
        if (rawValue == null) {
            if (values.containsKey(KEY_CLONES)) throw new IllegalStateException("Clone registry value is null");
            return new ArrayList<CloneEntry>();
        }
        if (!(rawValue instanceof String)) throw new IllegalStateException("Clone registry is not a String");
        JSONArray arr = new JSONArray((String) rawValue);
        List<CloneEntry> out = new ArrayList<CloneEntry>();
        Set<String> identities = new HashSet<String>();
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i);
            if (o == null) throw new IllegalStateException("Clone registry entry " + i + " is not an object");
            CloneEntry e = new CloneEntry();
            Object pkg = o.opt("pkg");
            Object uid = o.opt("uid");
            if (!(pkg instanceof String) || ((String) pkg).trim().isEmpty()) {
                throw new IllegalStateException("Clone registry entry " + i + " has an invalid package name");
            }
            if (!(uid instanceof Number) || ((Number) uid).intValue() < 0
                    || ((Number) uid).doubleValue() != ((Number) uid).intValue()) {
                throw new IllegalStateException("Clone registry entry " + i + " has an invalid virtual user ID");
            }
            e.packageName = (String) pkg;
            e.userId = ((Number) uid).intValue();

            e.displayName = readOptionalString(o, "name", e.packageName);
            e.mockGpsEnabled = readOptionalBoolean(o, "gpsOn", false);
            e.latitude = readOptionalDouble(o, "lat", 0.0d);
            e.longitude = readOptionalDouble(o, "lng", 0.0d);
            e.locationLabel = readOptionalString(o, "locLabel", "");
            e.customDeviceEnabled = readOptionalBoolean(o, "devOn", false);
            e.deviceBrand = readOptionalString(o, "devBrand", "");
            e.deviceModel = readOptionalString(o, "devModel", "");

            if (e.mockGpsEnabled && (Double.isNaN(e.latitude) || Double.isInfinite(e.latitude)
                    || Double.isNaN(e.longitude) || Double.isInfinite(e.longitude)
                    || e.latitude < -90.0d || e.latitude > 90.0d
                    || e.longitude < -180.0d || e.longitude > 180.0d)) {
                throw new IllegalStateException("Clone registry entry " + i + " has invalid enabled-location coordinates");
            }

            Object denied = o.opt("denied");
            if (denied != null) {
                if (!(denied instanceof JSONArray)) throw new IllegalStateException("Denied permissions are not an array");
                JSONArray permissions = (JSONArray) denied;
                for (int j = 0; j < permissions.length(); j++) {
                    Object permission = permissions.get(j);
                    if (!(permission instanceof String) || ((String) permission).trim().isEmpty()) {
                        throw new IllegalStateException("Denied permission at entry " + i + " is invalid");
                    }
                    e.deniedPermissions.add((String) permission);
                }
            }

            String identity = e.packageName + "\\u0000" + e.userId;
            if (!identities.add(identity)) throw new IllegalStateException("Duplicate clone identity");
            out.add(e);
        }
        Collections.sort(out, new Comparator<CloneEntry>() {
            @Override public int compare(CloneEntry a, CloneEntry b) {
                if (a.userId != b.userId) return a.userId - b.userId;
                return a.displayName.compareToIgnoreCase(b.displayName);
            }
        });
        return out;
    }

    private static String readOptionalString(JSONObject object, String key, String fallback) throws Exception {
        Object value = object.opt(key);
        if (value == null) return fallback;
        if (!(value instanceof String)) throw new IllegalStateException("Field " + key + " is not a String");
        return (String) value;
    }

    private static boolean readOptionalBoolean(JSONObject object, String key, boolean fallback) {
        Object value = object.opt(key);
        if (value == null) return fallback;
        if (!(value instanceof Boolean)) throw new IllegalStateException("Field " + key + " is not a Boolean");
        return (Boolean) value;
    }

    private static double readOptionalDouble(JSONObject object, String key, double fallback) {
        Object value = object.opt(key);
        if (value == null) return fallback;
        if (!(value instanceof Number)) throw new IllegalStateException("Field " + key + " is not numeric");
        return ((Number) value).doubleValue();
    }

    public static List<CloneEntry> getAll(Context c) {
        try {
            return readAllStrict(c);
        } catch (Exception ignored) {
            // Legacy UI callers retain their historical empty-list fallback.
            // All mutation/allocation paths use readAllStrict and fail closed.
            return new ArrayList<CloneEntry>();
        }
    }

    public static boolean saveAll(Context c, List<CloneEntry> list) {
        if (c == null || list == null) return false;
        try {
            JSONArray arr = new JSONArray();
            Set<String> identities = new HashSet<String>();
            for (CloneEntry e : list) {
                if (e == null || e.packageName == null || e.packageName.trim().isEmpty()
                        || e.userId < 0 || e.deniedPermissions == null) return false;
                if (e.mockGpsEnabled && (Double.isNaN(e.latitude) || Double.isInfinite(e.latitude)
                        || Double.isNaN(e.longitude) || Double.isInfinite(e.longitude)
                        || e.latitude < -90.0d || e.latitude > 90.0d
                        || e.longitude < -180.0d || e.longitude > 180.0d)) return false;
                if (!identities.add(e.packageName + "\\u0000" + e.userId)) return false;
                JSONObject o = new JSONObject();
                o.put("pkg", e.packageName);
                o.put("uid", e.userId);
                o.put("name", e.displayName == null ? e.packageName : e.displayName);
                o.put("gpsOn", e.mockGpsEnabled);
                o.put("lat", e.latitude);
                o.put("lng", e.longitude);
                o.put("locLabel", e.locationLabel == null ? "" : e.locationLabel);
                o.put("devOn", e.customDeviceEnabled);
                o.put("devBrand", e.deviceBrand == null ? "" : e.deviceBrand);
                o.put("devModel", e.deviceModel == null ? "" : e.deviceModel);
                JSONArray pArr = new JSONArray();
                for (String permission : e.deniedPermissions) {
                    if (permission == null || permission.trim().isEmpty()) return false;
                    pArr.put(permission);
                }
                o.put("denied", pArr);
                arr.put(o);
            }
            return prefs(c).edit().putString(KEY_CLONES, arr.toString()).commit();
        } catch (Exception ignored) {
            return false;
        }
    }

    public static CloneEntry getClone(Context c, String pkg, int userId) {
        for (CloneEntry e : getAll(c)) {
            if (e.packageName.equals(pkg) && e.userId == userId) return e;
        }
        return null;
    }

    public static boolean upsertClone(Context c, CloneEntry entry) {
        if (entry == null || entry.packageName == null || entry.packageName.trim().isEmpty()
                || entry.userId < 0) return false;
        try {
            List<CloneEntry> all = readAllStrict(c);
            boolean found = false;
            for (int i = 0; i < all.size(); i++) {
                CloneEntry cur = all.get(i);
                if (cur.packageName.equals(entry.packageName) && cur.userId == entry.userId) {
                    all.set(i, entry);
                    found = true;
                    break;
                }
            }
            if (!found) all.add(entry);
            return saveAll(c, all);
        } catch (Exception ignored) {
            return false;
        }
    }

    public static boolean removeClone(Context c, String pkg, int userId) {
        if (c == null || pkg == null || pkg.trim().isEmpty() || userId < 0) return false;
        try {
            List<CloneEntry> all = readAllStrict(c);
            List<CloneEntry> kept = new ArrayList<CloneEntry>();
            for (CloneEntry e : all) {
                if (!(e.packageName.equals(pkg) && e.userId == userId)) kept.add(e);
            }
            return saveAll(c, kept);
        } catch (Exception ignored) {
            return false;
        }
    }

    public static int nextFreeUserIdForPackage(Context c, String pkg) {
        if (c == null || pkg == null || pkg.trim().isEmpty()) return -1;
        try {
            Set<Integer> used = new HashSet<Integer>();
            for (CloneEntry e : readAllStrict(c)) {
                if (e.packageName.equals(pkg)) used.add(e.userId);
            }
            int uid = 0;
            while (used.contains(uid)) uid++;
            return uid;
        } catch (Exception ignored) {
            // -1 is an explicit allocation failure; never guess Space 1 on corrupt data.
            return -1;
        }
    }

    public static Map<Integer, List<CloneEntry>> getGroupedBySpace(Context c) {
        Map<Integer, List<CloneEntry>> map = new LinkedHashMap<Integer, List<CloneEntry>>();
        for (CloneEntry e : getAll(c)) {
            int spaceNum = e.getSpaceNumber();
            if (!map.containsKey(spaceNum)) map.put(spaceNum, new ArrayList<CloneEntry>());
            map.get(spaceNum).add(e);
        }
        if (map.isEmpty()) {
            map.put(1, new ArrayList<CloneEntry>());
        }
        return map;
    }

    public static boolean isSpaceCollapsed(Context c, int spaceNum) {
        return prefs(c).getStringSet(KEY_COLLAPSED, new HashSet<String>()).contains(String.valueOf(spaceNum));
    }

    public static void setSpaceCollapsed(Context c, int spaceNum, boolean collapsed) {
        Set<String> set = new HashSet<String>(prefs(c).getStringSet(KEY_COLLAPSED, new HashSet<String>()));
        if (collapsed) set.add(String.valueOf(spaceNum));
        else set.remove(String.valueOf(spaceNum));
        prefs(c).edit().putStringSet(KEY_COLLAPSED, set).apply();
    }

    public static boolean isMasterMockGpsEnabled(Context c) {
        return prefs(c).getBoolean(KEY_MASTER_GPS, true);
    }

    public static void setMasterMockGpsEnabled(Context c, boolean enabled) {
        prefs(c).edit().putBoolean(KEY_MASTER_GPS, enabled).commit();
    }

    public static GlobalEnvConfig getGlobalEnv(Context c) {
        GlobalEnvConfig cfg = new GlobalEnvConfig();
        try {
            String raw = prefs(c).getString(KEY_GLOBAL_DEV, "");
            if (!raw.isEmpty()) {
                JSONObject o = new JSONObject(raw);
                cfg.enabled = o.optBoolean("enabled", true);
                cfg.brand = o.optString("brand", "samsung");
                cfg.manufacturer = o.optString("manufacturer", "samsung");
                cfg.model = o.optString("model", "SM-S928B");
                cfg.device = o.optString("device", "e3q");
                cfg.countryIso = o.optString("countryIso", "us");
                cfg.simOperator = o.optString("simOperator", "310260");
                cfg.simOperatorName = o.optString("simOperatorName", "T-Mobile");
            }
        } catch (Exception ignored) {}
        return cfg;
    }

    public static void saveGlobalEnv(Context c, GlobalEnvConfig cfg) {
        try {
            JSONObject o = new JSONObject();
            o.put("enabled", cfg.enabled);
            o.put("brand", cfg.brand);
            o.put("manufacturer", cfg.manufacturer);
            o.put("model", cfg.model);
            o.put("device", cfg.device);
            o.put("countryIso", cfg.countryIso);
            o.put("simOperator", cfg.simOperator);
            o.put("simOperatorName", cfg.simOperatorName);
            prefs(c).edit().putString(KEY_GLOBAL_DEV, o.toString()).commit();
        } catch (Exception ignored) {}
    }

    public static void recordActiveLaunch(Context c, CloneEntry entry) {
        try {
            JSONObject o = new JSONObject();
            o.put("pkg", entry.packageName);
            o.put("uid", entry.userId);
            prefs(c).edit().putString(KEY_ACTIVE_LAUNCH, o.toString()).commit();
        } catch (Exception ignored) {}
    }

    public static CloneEntry getLastActiveLaunch(Context c) {
        try {
            String raw = prefs(c).getString(KEY_ACTIVE_LAUNCH, "");
            if (!raw.isEmpty()) {
                JSONObject o = new JSONObject(raw);
                return getClone(c, o.optString("pkg"), o.optInt("uid", 0));
            }
        } catch (Exception ignored) {}
        return null;
    }

    public static void syncAllHooks(Context c) {
        // Location settings are applied through engine APIs scoped to each package and virtual user.
        // Device/SIM profile fields remain stored as metadata until a supported scoped engine API exists.
        for (CloneEntry e : getAll(c)) {
            VirtualHookManager.syncCloneHooks(c, e);
        }
    }
}
