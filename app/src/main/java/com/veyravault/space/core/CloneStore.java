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
        public String model = "SM-S928B"; // Galaxy S24 Ultra (Masks Huawei/old device)
        public String device = "e3q";
        public String countryIso = "us";
        public String simOperator = "310260";
        public String simOperatorName = "T-Mobile";
    }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public static List<CloneEntry> getAll(Context c) {
        List<CloneEntry> out = new ArrayList<CloneEntry>();
        try {
            String raw = prefs(c).getString(KEY_CLONES, "[]");
            JSONArray arr = new JSONArray(raw);
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                CloneEntry e = new CloneEntry();
                e.packageName = o.optString("pkg");
                e.userId = o.optInt("uid", 0);
                e.displayName = o.optString("name", e.packageName);
                e.mockGpsEnabled = o.optBoolean("gpsOn", false);
                e.latitude = o.optDouble("lat", 0.0);
                e.longitude = o.optDouble("lng", 0.0);
                e.locationLabel = o.optString("locLabel", "");
                e.customDeviceEnabled = o.optBoolean("devOn", false);
                e.deviceBrand = o.optString("devBrand", "");
                e.deviceModel = o.optString("devModel", "");
                JSONArray pArr = o.optJSONArray("denied");
                if (pArr != null) {
                    for (int j = 0; j < pArr.length(); j++) e.deniedPermissions.add(pArr.optString(j));
                }
                out.add(e);
            }
        } catch (Exception ignored) {}
        Collections.sort(out, new Comparator<CloneEntry>() {
            @Override
            public int compare(CloneEntry a, CloneEntry b) {
                if (a.userId != b.userId) return a.userId - b.userId;
                return a.displayName.compareToIgnoreCase(b.displayName);
            }
        });
        return out;
    }

    public static void saveAll(Context c, List<CloneEntry> list) {
        try {
            JSONArray arr = new JSONArray();
            for (CloneEntry e : list) {
                JSONObject o = new JSONObject();
                o.put("pkg", e.packageName);
                o.put("uid", e.userId);
                o.put("name", e.displayName);
                o.put("gpsOn", e.mockGpsEnabled);
                o.put("lat", e.latitude);
                o.put("lng", e.longitude);
                o.put("locLabel", e.locationLabel);
                o.put("devOn", e.customDeviceEnabled);
                o.put("devBrand", e.deviceBrand);
                o.put("devModel", e.deviceModel);
                JSONArray pArr = new JSONArray();
                for (String p : e.deniedPermissions) pArr.put(p);
                o.put("denied", pArr);
                arr.put(o);
            }
            prefs(c).edit().putString(KEY_CLONES, arr.toString()).commit();
        } catch (Exception ignored) {}
    }

    public static CloneEntry getClone(Context c, String pkg, int userId) {
        for (CloneEntry e : getAll(c)) {
            if (e.packageName.equals(pkg) && e.userId == userId) return e;
        }
        return null;
    }

    public static void upsertClone(Context c, CloneEntry entry) {
        List<CloneEntry> all = getAll(c);
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
        saveAll(c, all);
    }

    public static void removeClone(Context c, String pkg, int userId) {
        List<CloneEntry> all = getAll(c);
        List<CloneEntry> kept = new ArrayList<CloneEntry>();
        for (CloneEntry e : all) {
            if (!(e.packageName.equals(pkg) && e.userId == userId)) kept.add(e);
        }
        saveAll(c, kept);
    }

    public static int nextFreeUserIdForPackage(Context c, String pkg) {
        Set<Integer> used = new HashSet<Integer>();
        for (CloneEntry e : getAll(c)) {
            if (e.packageName.equals(pkg)) used.add(e.userId);
        }
        int uid = 0;
        while (used.contains(uid)) uid++;
        return uid;
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
        GlobalEnvConfig g = getGlobalEnv(c);
        if (g.enabled) {
            VirtualHookManager.applyDeviceProperties(0, g.brand, g.manufacturer, g.model, g.device,
                    g.countryIso, g.simOperator, g.simOperatorName);
        }
        for (CloneEntry e : getAll(c)) {
            VirtualHookManager.syncCloneHooks(c, e);
        }
    }
}
