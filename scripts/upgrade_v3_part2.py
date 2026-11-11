#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA_BASE = os.path.join(BASE_DIR, "app/src/main/java/com/veyravault/app")


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[PART2] Wrote: {path}")


# ---------------------------------------------------------------------------
# 1. CloneMetadataStore.java
# ---------------------------------------------------------------------------
CLONE_METADATA_STORE = """package com.veyravault.app.core;

import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

public class CloneMetadataStore {
    private static final String PREF_NAME = "veyra_clone_metadata_v3";

    public static class CloneMeta {
        public String customName = "";
        public String deviceBrand = "";
        public String deviceModel = "";
        public String regionLabel = "";
        public String timezone = "";
        public String simCarrier = "";
        public String simMccMnc = "";
        public String simCountryIso = "";
        public double latitude = 40.7128;
        public double longitude = -74.0060;
        public boolean locationSpoofEnabled = false;
        public boolean priorityEnabled = true;
    }

    public static class GlobalEnvConfig {
        public String brand = "Samsung";
        public String model = "Galaxy S24 Ultra";
        public String regionLabel = "New York, United States";
        public String timezone = "America/New_York";
        public String simCarrier = "T-Mobile USA";
        public String simMccMnc = "310260";
        public String simCountryIso = "US";
        public double latitude = 40.7128;
        public double longitude = -74.0060;
        public boolean antiHostLeakStrict = true;
    }

    public static class EffectiveIdentity {
        public String brand;
        public String model;
        public String brandModelDisplay;
        public String regionLabel;
        public String timezone;
        public String simCarrier;
        public String simMccMnc;
        public String simCountryIso;
        public double latitude;
        public double longitude;
        public String prioritySource;
        public int priorityLevel;
    }

    public static class VpnProfile {
        public String id;
        public String name;
        public String category;
        public String countryCode;
        public String flagEmoji;
        public String city;
        public String protocol;
        public String serverHost;
        public int serverPort;
        public String username;
        public String password;
        public String sniOrBugHost;
        public String dnsServer;
        public String timezone;
        public String simCarrier;
        public String simMccMnc;
        public double latitude;
        public double longitude;
        public int nodeIndex;
        public int powerPercent = 96;
        public boolean isBuiltInFree;
    }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    public static boolean isAppPrioritySwitchOn(Context c) {
        return prefs(c).getBoolean("switch_priority_1_app", true);
    }

    public static void setAppPrioritySwitchOn(Context c, boolean v) {
        prefs(c).edit().putBoolean("switch_priority_1_app", v).apply();
    }

    public static boolean isSpacePrioritySwitchOn(Context c) {
        return prefs(c).getBoolean("switch_priority_2_space", true);
    }

    public static void setSpacePrioritySwitchOn(Context c, boolean v) {
        prefs(c).edit().putBoolean("switch_priority_2_space", v).apply();
    }

    public static boolean isGlobalPrioritySwitchOn(Context c) {
        return prefs(c).getBoolean("switch_priority_3_global", true);
    }

    public static void setGlobalPrioritySwitchOn(Context c, boolean v) {
        prefs(c).edit().putBoolean("switch_priority_3_global", v).apply();
    }

    public static String getActiveDisguiseMode(Context c) {
        return prefs(c).getString("active_disguise_mode", "default");
    }

    public static void applyDisguiseMode(Context c, String mode) {
        prefs(c).edit().putString("active_disguise_mode", mode).apply();
        PackageManager pm = c.getPackageManager();
        String pkg = c.getPackageName();
        String[] aliases = new String[]{
                pkg + ".AliasCalculator",
                pkg + ".AliasNotes",
                pkg + ".AliasBattery",
                pkg + ".AliasWeather"
        };
        String target = null;
        if ("calculator".equals(mode)) target = pkg + ".AliasCalculator";
        else if ("notes".equals(mode)) target = pkg + ".AliasNotes";
        else if ("battery".equals(mode)) target = pkg + ".AliasBattery";
        else if ("weather".equals(mode)) target = pkg + ".AliasWeather";

        for (String al : aliases) {
            try {
                pm.setComponentEnabledSetting(
                        new ComponentName(pkg, al),
                        al.equals(target)
                                ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED
                                : PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                        PackageManager.DONT_KILL_APP
                );
            } catch (Throwable ignored) {}
        }
    }

    public static String getDisguiseTitle(Context c) {
        String m = getActiveDisguiseMode(c);
        if ("calculator".equals(m)) return "ماشین‌حساب مهندسی";
        if ("notes".equals(m)) return "یادداشت و تقویم";
        if ("battery".equals(m)) return "بهینه‌ساز باتری";
        if ("weather".equals(m)) return "هواشناسی دقیق";
        return "VeyraVault (پیش‌فرض)";
    }

    public static void markAppClonedInSpace(Context c, String pkg, int u, boolean cl) {
        Set<String> s = new LinkedHashSet<>(getMarkedClonedAppsInSpace(c, u));
        if (cl) s.add(pkg);
        else s.remove(pkg);
        JSONArray a = new JSONArray();
        for (String x : s) a.put(x);
        prefs(c).edit().putString("marked_clones_u" + u, a.toString()).apply();
    }

    public static List<String> getMarkedClonedAppsInSpace(Context c, int u) {
        List<String> l = new ArrayList<>();
        String r = prefs(c).getString("marked_clones_u" + u, "[]");
        try {
            JSONArray a = new JSONArray(r);
            for (int i = 0; i < a.length(); i++) {
                String s = a.optString(i, "");
                if (!s.isEmpty()) l.add(s);
            }
        } catch (Throwable ignored) {}
        return l;
    }

    public static String cleanModelOnly(String brand, String model) {
        String b = brand == null ? "" : brand.trim();
        String m = model == null ? "" : model.trim();
        if (m.isEmpty()) return b;
        if (b.isEmpty()) return m;
        while (m.toLowerCase().startsWith(b.toLowerCase() + " ")) {
            m = m.substring(b.length()).trim();
        }
        String[] kb = new String[]{"Samsung", "سامسونگ", "Apple", "اپل", "Xiaomi", "شیائومی", "Google", "گوگل", "OnePlus", "وان‌پلاس"};
        for (String k : kb) {
            if (m.toLowerCase().startsWith(k.toLowerCase() + " ") && b.toLowerCase().contains(k.toLowerCase())) {
                m = m.substring(k.length()).trim();
            }
            if (m.toLowerCase().startsWith(k.toLowerCase() + " " + k.toLowerCase())) {
                m = m.substring(k.length()).trim();
            }
        }
        return m.isEmpty() ? b : m;
    }

    public static String formatBrandModel(String brand, String model) {
        String b = brand == null ? "" : brand.trim();
        String m = cleanModelOnly(b, model);
        if (b.isEmpty()) return m.isEmpty() ? "Samsung Galaxy S24 Ultra" : m;
        if (m.isEmpty() || m.equalsIgnoreCase(b)) return b;
        if (m.toLowerCase().startsWith(b.toLowerCase())) return m;
        return b + " " + m;
    }

    public static EffectiveIdentity resolveEffectiveIdentity(Context c, String pkg, int u) {
        GlobalEnvConfig g = getGlobalConfig(c);
        CloneMeta sm = getCloneMeta(c, "__space__", u);
        CloneMeta am = (pkg != null && !pkg.isEmpty() && !"__space__".equals(pkg) && !"__global__".equals(pkg))
                ? getCloneMeta(c, pkg, u) : null;
        boolean p1 = isAppPrioritySwitchOn(c);
        boolean p2 = isSpacePrioritySwitchOn(c);

        EffectiveIdentity o = new EffectiveIdentity();
        String sb = (g.brand == null || g.brand.trim().isEmpty()) ? "Samsung" : g.brand.trim();
        String smo = (g.model == null || g.model.trim().isEmpty()) ? "Galaxy S24 Ultra" : g.model.trim();
        o.brand = sb;
        o.model = cleanModelOnly(sb, smo);
        o.regionLabel = (g.regionLabel == null || g.regionLabel.trim().isEmpty()) ? "New York, United States" : g.regionLabel.trim();
        o.timezone = (g.timezone == null || g.timezone.trim().isEmpty()) ? "America/New_York" : g.timezone.trim();
        o.simCarrier = (g.simCarrier == null || g.simCarrier.trim().isEmpty()) ? "T-Mobile USA" : g.simCarrier.trim();
        o.simMccMnc = (g.simMccMnc == null || g.simMccMnc.trim().isEmpty()) ? "310260" : g.simMccMnc.trim();
        o.simCountryIso = (g.simCountryIso == null || g.simCountryIso.trim().isEmpty()) ? "US" : g.simCountryIso.trim();
        o.latitude = (g.latitude == 0.0 && g.longitude == 0.0) ? 40.7128 : g.latitude;
        o.longitude = (g.latitude == 0.0 && g.longitude == 0.0) ? -74.0060 : g.longitude;
        o.priorityLevel = 3;
        o.prioritySource = "اولویت ۳: تنظیمات کلی برنامه";

        if (p2 && sm != null && sm.priorityEnabled) {
            boolean hd = (sm.deviceModel != null && !sm.deviceModel.trim().isEmpty())
                    || (sm.deviceBrand != null && !sm.deviceBrand.trim().isEmpty());
            if (hd) {
                o.brand = (sm.deviceBrand != null && !sm.deviceBrand.trim().isEmpty()) ? sm.deviceBrand.trim() : o.brand;
                o.model = cleanModelOnly(o.brand, (sm.deviceModel != null && !sm.deviceModel.trim().isEmpty()) ? sm.deviceModel.trim() : o.model);
                o.priorityLevel = 2;
                o.prioritySource = "اولویت ۲: تنظیمات اختصاصی فضا (" + getSpaceDisplayName(c, u) + ")";
            }
            if (sm.locationSpoofEnabled || (sm.regionLabel != null && !sm.regionLabel.trim().isEmpty())) {
                if (sm.regionLabel != null && !sm.regionLabel.trim().isEmpty()) o.regionLabel = sm.regionLabel.trim();
                if (sm.timezone != null && !sm.timezone.trim().isEmpty()) o.timezone = sm.timezone.trim();
                if (sm.simCarrier != null && !sm.simCarrier.trim().isEmpty()) o.simCarrier = sm.simCarrier.trim();
                if (sm.simMccMnc != null && !sm.simMccMnc.trim().isEmpty()) o.simMccMnc = sm.simMccMnc.trim();
                if (sm.simCountryIso != null && !sm.simCountryIso.trim().isEmpty()) o.simCountryIso = sm.simCountryIso.trim();
                if (sm.latitude != 0.0 || sm.longitude != 0.0) {
                    o.latitude = sm.latitude;
                    o.longitude = sm.longitude;
                }
                o.priorityLevel = 2;
                o.prioritySource = "اولویت ۲: تنظیمات اختصاصی فضا (" + getSpaceDisplayName(c, u) + ")";
            }
        }

        if (p1 && am != null && am.priorityEnabled) {
            boolean hd = (am.deviceModel != null && !am.deviceModel.trim().isEmpty())
                    || (am.deviceBrand != null && !am.deviceBrand.trim().isEmpty());
            if (hd) {
                o.brand = (am.deviceBrand != null && !am.deviceBrand.trim().isEmpty()) ? am.deviceBrand.trim() : o.brand;
                o.model = cleanModelOnly(o.brand, (am.deviceModel != null && !am.deviceModel.trim().isEmpty()) ? am.deviceModel.trim() : o.model);
                o.priorityLevel = 1;
                o.prioritySource = "اولویت ۱: تنظیمات اختصاصی اپ (" + pkg + ")";
            }
            if (am.locationSpoofEnabled || (am.regionLabel != null && !am.regionLabel.trim().isEmpty())) {
                if (am.regionLabel != null && !am.regionLabel.trim().isEmpty()) o.regionLabel = am.regionLabel.trim();
                if (am.timezone != null && !am.timezone.trim().isEmpty()) o.timezone = am.timezone.trim();
                if (am.simCarrier != null && !am.simCarrier.trim().isEmpty()) o.simCarrier = am.simCarrier.trim();
                if (am.simMccMnc != null && !am.simMccMnc.trim().isEmpty()) o.simMccMnc = am.simMccMnc.trim();
                if (am.simCountryIso != null && !am.simCountryIso.trim().isEmpty()) o.simCountryIso = am.simCountryIso.trim();
                if (am.latitude != 0.0 || am.longitude != 0.0) {
                    o.latitude = am.latitude;
                    o.longitude = am.longitude;
                }
                o.priorityLevel = 1;
                o.prioritySource = "اولویت ۱: تنظیمات اختصاصی اپ (" + pkg + ")";
            }
        }

        o.brandModelDisplay = formatBrandModel(o.brand, o.model);
        return o;
    }

    public static void setLastActiveSession(Context c, String pkg, int u) {
        prefs(c).edit().putString("last_active_pkg", pkg == null ? "" : pkg).putInt("last_active_user", u).apply();
    }

    public static String getLastActivePkg(Context c) {
        return prefs(c).getString("last_active_pkg", "");
    }

    public static int getLastActiveUserId(Context c) {
        return prefs(c).getInt("last_active_user", 0);
    }

    public static String getSpaceDisplayName(Context c, int u) {
        String cu = prefs(c).getString("space_name_" + u, "");
        if (cu != null && !cu.trim().isEmpty()) return cu.trim();
        return "فضای " + (u + 1);
    }

    public static void setSpaceCustomName(Context c, int u, String n) {
        prefs(c).edit().putString("space_name_" + u, n == null ? "" : n.trim()).apply();
    }

    public static boolean isSpaceCreated(Context c, int u) {
        if (u == 0) return true;
        return prefs(c).getBoolean("space_created_" + u, false);
    }

    public static void markSpaceCreated(Context c, int u, boolean cr) {
        prefs(c).edit().putBoolean("space_created_" + u, cr).apply();
    }

    public static int getUnreadCount(Context c, String pkg, int u) {
        return prefs(c).getInt("badge_" + u + "_" + pkg, 0);
    }

    public static void setUnreadCount(Context c, String pkg, int u, int n) {
        prefs(c).edit().putInt("badge_" + u + "_" + pkg, Math.max(0, n)).apply();
    }

    public static void incrementUnreadCount(Context c, String pkg, int u) {
        setUnreadCount(c, pkg, u, getUnreadCount(c, pkg, u) + 1);
    }

    public static String formatBadgeText(int n) {
        if (n <= 0) return "";
        if (n >= 100) return "∞";
        return String.valueOf(n);
    }

    public static CloneMeta getCloneMeta(Context c, String pkg, int u) {
        CloneMeta m = new CloneMeta();
        String r = prefs(c).getString("meta_" + u + "_" + pkg, "");
        if (r == null || r.isEmpty()) return m;
        try {
            JSONObject o = new JSONObject(r);
            m.customName = o.optString("customName", "");
            m.deviceBrand = o.optString("deviceBrand", "");
            m.deviceModel = cleanModelOnly(m.deviceBrand, o.optString("deviceModel", ""));
            m.regionLabel = o.optString("regionLabel", "");
            m.timezone = o.optString("timezone", "");
            m.simCarrier = o.optString("simCarrier", "");
            m.simMccMnc = o.optString("simMccMnc", "");
            m.simCountryIso = o.optString("simCountryIso", "");
            m.latitude = o.optDouble("latitude", 40.7128);
            m.longitude = o.optDouble("longitude", -74.0060);
            m.locationSpoofEnabled = o.optBoolean("locationSpoofEnabled", false);
            m.priorityEnabled = o.optBoolean("priorityEnabled", true);
        } catch (Throwable ignored) {}
        return m;
    }

    public static void saveCloneMeta(Context c, String pkg, int u, CloneMeta m) {
        try {
            JSONObject o = new JSONObject();
            o.put("customName", m.customName == null ? "" : m.customName);
            o.put("deviceBrand", m.deviceBrand == null ? "" : m.deviceBrand);
            o.put("deviceModel", cleanModelOnly(m.deviceBrand, m.deviceModel));
            o.put("regionLabel", m.regionLabel == null ? "" : m.regionLabel);
            o.put("timezone", m.timezone == null ? "" : m.timezone);
            o.put("simCarrier", m.simCarrier == null ? "" : m.simCarrier);
            o.put("simMccMnc", m.simMccMnc == null ? "" : m.simMccMnc);
            o.put("simCountryIso", m.simCountryIso == null ? "" : m.simCountryIso);
            o.put("latitude", m.latitude);
            o.put("longitude", m.longitude);
            o.put("locationSpoofEnabled", m.locationSpoofEnabled);
            o.put("priorityEnabled", m.priorityEnabled);
            prefs(c).edit().putString("meta_" + u + "_" + pkg, o.toString()).apply();
        } catch (Throwable ignored) {}
    }

    public static GlobalEnvConfig getGlobalConfig(Context c) {
        GlobalEnvConfig g = new GlobalEnvConfig();
        String r = prefs(c).getString("global_env_v3", "");
        if (r == null || r.isEmpty()) return g;
        try {
            JSONObject o = new JSONObject(r);
            g.brand = o.optString("brand", "Samsung");
            g.model = cleanModelOnly(g.brand, o.optString("model", "Galaxy S24 Ultra"));
            g.regionLabel = o.optString("regionLabel", "New York, United States");
            g.timezone = o.optString("timezone", "America/New_York");
            g.simCarrier = o.optString("simCarrier", "T-Mobile USA");
            g.simMccMnc = o.optString("simMccMnc", "310260");
            g.simCountryIso = o.optString("simCountryIso", "US");
            g.latitude = o.optDouble("latitude", 40.7128);
            g.longitude = o.optDouble("longitude", -74.0060);
            g.antiHostLeakStrict = o.optBoolean("antiHostLeakStrict", true);
        } catch (Throwable ignored) {}
        return g;
    }

    public static void saveGlobalConfigQuietly(Context c, GlobalEnvConfig g) {
        try {
            JSONObject o = new JSONObject();
            o.put("brand", g.brand);
            o.put("model", cleanModelOnly(g.brand, g.model));
            o.put("regionLabel", g.regionLabel);
            o.put("timezone", g.timezone);
            o.put("simCarrier", g.simCarrier);
            o.put("simMccMnc", g.simMccMnc);
            o.put("simCountryIso", g.simCountryIso);
            o.put("latitude", g.latitude);
            o.put("longitude", g.longitude);
            o.put("antiHostLeakStrict", g.antiHostLeakStrict);
            prefs(c).edit().putString("global_env_v3", o.toString()).apply();
        } catch (Throwable ignored) {}
    }

    public static void saveGlobalConfig(Context c, GlobalEnvConfig g) {
        saveGlobalConfigQuietly(c, g);
        VirtualHookManager.applyEffectiveHookToSystem(c, getLastActivePkg(c), getLastActiveUserId(c));
    }

    public static String getGlobalBrand(Context c) {
        return getGlobalConfig(c).brand;
    }

    public static String getGlobalModel(Context c) {
        return getGlobalConfig(c).model;
    }

    public static String getGlobalRegionLabel(Context c) {
        return getGlobalConfig(c).regionLabel;
    }

    public static String getEffectiveModelSummary(Context c, String pkg, int u) {
        return resolveEffectiveIdentity(c, pkg, u).brandModelDisplay;
    }

    public static String getEffectiveRegionSummary(Context c, String pkg, int u) {
        return resolveEffectiveIdentity(c, pkg, u).regionLabel;
    }

    private static VpnProfile cp(String id, String n, String cat, String cc, String fl, String city, String pr,
                                 String h, int po, String tz, String ca, String mc, double la, double lo,
                                 String dns, int ni, int pw, boolean fr) {
        VpnProfile p = new VpnProfile();
        p.id = id;
        p.name = n;
        p.category = cat;
        p.countryCode = cc;
        p.flagEmoji = fl;
        p.city = city;
        p.protocol = pr;
        p.serverHost = h;
        p.serverPort = po;
        p.username = "";
        p.password = "";
        p.sniOrBugHost = "speed.cloudflare.com";
        p.dnsServer = dns;
        p.timezone = tz;
        p.simCarrier = ca;
        p.simMccMnc = mc;
        p.latitude = la;
        p.longitude = lo;
        p.nodeIndex = ni;
        p.powerPercent = pw;
        p.isBuiltInFree = fr;
        return p;
    }

    public static List<VpnProfile> getFreeBuiltInPresets() {
        List<VpnProfile> l = new ArrayList<>();
        l.add(cp("free_us_ny_1", "US New York • نود ۱", "ایالات متحده (United States)", "US", "🇺🇸", "New York", "SOCKS5/TLS", "us-ny1.freevault.net", 443, "America/New_York", "T-Mobile USA", "310260", 40.7128, -74.0060, "1.1.1.1", 1, 99, true));
        l.add(cp("free_us_ny_2", "US New York • نود ۲", "ایالات متحده (United States)", "US", "🇺🇸", "New York", "HTTP-CONNECT", "us-ny2.freevault.net", 8443, "America/New_York", "T-Mobile USA", "310260", 40.7128, -74.0060, "1.1.1.1", 2, 97, true));
        l.add(cp("free_us_ny_3", "US New York • نود ۳", "ایالات متحده (United States)", "US", "🇺🇸", "New York", "V2Ray-WS-TLS", "us-ny3.freevault.net", 443, "America/New_York", "T-Mobile USA", "310260", 40.7128, -74.0060, "8.8.8.8", 3, 95, true));
        l.add(cp("free_us_la_1", "US Los Angeles • نود ۴", "ایالات متحده (United States)", "US", "🇺🇸", "Los Angeles", "SOCKS5/TLS", "us-la1.freevault.net", 443, "America/Los_Angeles", "Verizon Wireless", "311480", 34.0522, -118.2437, "1.1.1.1", 4, 94, true));
        l.add(cp("free_de_fra_1", "Germany Frankfurt • نود ۱", "آلمان (Germany)", "DE", "🇩🇪", "Frankfurt", "SOCKS5/TLS", "de-fra1.freevault.net", 443, "Europe/Berlin", "Telekom DE", "26201", 50.1109, 8.6821, "1.1.1.1", 1, 98, true));
        l.add(cp("free_de_fra_2", "Germany Frankfurt • نود ۲", "آلمان (Germany)", "DE", "🇩🇪", "Frankfurt", "V2Ray-WS-TLS", "de-fra2.freevault.net", 8443, "Europe/Berlin", "Telekom DE", "26201", 50.1109, 8.6821, "1.1.1.1", 2, 96, true));
        l.add(cp("free_de_fra_3", "Germany Berlin • نود ۳", "آلمان (Germany)", "DE", "🇩🇪", "Berlin", "HTTP-CONNECT", "de-ber1.freevault.net", 443, "Europe/Berlin", "Vodafone DE", "26202", 52.5200, 13.4050, "8.8.8.8", 3, 93, true));
        l.add(cp("free_gb_lon_1", "UK London • نود ۱", "انگلستان (United Kingdom)", "GB", "🇬🇧", "London", "SOCKS5/TLS", "uk-lon1.freevault.net", 443, "Europe/London", "Vodafone UK", "23415", 51.5074, -0.1278, "1.1.1.1", 1, 97, true));
        l.add(cp("free_gb_lon_2", "UK London • نود ۲", "انگلستان (United Kingdom)", "GB", "🇬🇧", "London", "V2Ray-WS-TLS", "uk-lon2.freevault.net", 8443, "Europe/London", "Vodafone UK", "23415", 51.5074, -0.1278, "8.8.4.4", 2, 95, true));
        l.add(cp("free_nl_ams_1", "Netherlands Amsterdam • نود ۱", "هلند (Netherlands)", "NL", "🇳🇱", "Amsterdam", "SOCKS5/TLS", "nl-ams1.freevault.net", 443, "Europe/Amsterdam", "KPN NL", "20408", 52.3676, 4.9041, "1.1.1.1", 1, 98, true));
        l.add(cp("free_nl_ams_2", "Netherlands Amsterdam • نود ۲", "هلند (Netherlands)", "NL", "🇳🇱", "Amsterdam", "HTTP-CONNECT", "nl-ams2.freevault.net", 8080, "Europe/Amsterdam", "KPN NL", "20408", 52.3676, 4.9041, "1.1.1.1", 2, 94, true));
        l.add(cp("free_tr_ist_1", "Turkey Istanbul • نود ۱", "ترکیه (Turkey)", "TR", "🇹🇷", "Istanbul", "SOCKS5/TLS", "tr-ist1.freevault.net", 443, "Europe/Istanbul", "Turkcell", "28601", 41.0082, 28.9784, "1.1.1.1", 1, 96, true));
        return l;
    }

    public static List<VpnProfile> getVpnProfiles(Context c) {
        List<VpnProfile> l = new ArrayList<>();
        String r = prefs(c).getString("vpn_profiles_v5", "");
        if (r != null && !r.isEmpty()) {
            try {
                JSONArray a = new JSONArray(r);
                for (int i = 0; i < a.length(); i++) {
                    JSONObject o = a.getJSONObject(i);
                    VpnProfile p = new VpnProfile();
                    p.id = o.optString("id", "vpn_" + i);
                    p.name = o.optString("name", "Server " + (i + 1));
                    p.category = o.optString("category", "ایالات متحده (United States)");
                    p.countryCode = o.optString("countryCode", "US");
                    p.flagEmoji = o.optString("flagEmoji", "🇺🇸");
                    p.city = o.optString("city", "New York");
                    p.protocol = o.optString("protocol", "SOCKS5/TLS");
                    p.serverHost = o.optString("serverHost", "us-ny1.freevault.net");
                    p.serverPort = o.optInt("serverPort", 443);
                    p.username = o.optString("username", "");
                    p.password = o.optString("password", "");
                    p.sniOrBugHost = o.optString("sniOrBugHost", "cloudflare.com");
                    p.dnsServer = o.optString("dnsServer", "1.1.1.1");
                    p.timezone = o.optString("timezone", "America/New_York");
                    p.simCarrier = o.optString("simCarrier", "T-Mobile USA");
                    p.simMccMnc = o.optString("simMccMnc", "310260");
                    p.latitude = o.optDouble("latitude", 40.7128);
                    p.longitude = o.optDouble("longitude", -74.0060);
                    p.nodeIndex = o.optInt("nodeIndex", 1);
                    p.powerPercent = o.optInt("powerPercent", 96);
                    p.isBuiltInFree = o.optBoolean("isBuiltInFree", true);
                    l.add(p);
                }
            } catch (Throwable ignored) {}
        }
        if (l.isEmpty()) {
            l.addAll(getFreeBuiltInPresets());
            saveVpnProfiles(c, l);
        }
        return l;
    }

    public static void saveVpnProfiles(Context c, List<VpnProfile> l) {
        try {
            JSONArray a = new JSONArray();
            for (VpnProfile p : l) {
                JSONObject o = new JSONObject();
                o.put("id", p.id);
                o.put("name", p.name);
                o.put("category", p.category == null || p.category.isEmpty() ? "ایالات متحده (United States)" : p.category);
                o.put("countryCode", p.countryCode);
                o.put("flagEmoji", p.flagEmoji);
                o.put("city", p.city);
                o.put("protocol", p.protocol);
                o.put("serverHost", p.serverHost);
                o.put("serverPort", p.serverPort);
                o.put("username", p.username == null ? "" : p.username);
                o.put("password", p.password == null ? "" : p.password);
                o.put("sniOrBugHost", p.sniOrBugHost == null ? "" : p.sniOrBugHost);
                o.put("dnsServer", p.dnsServer == null ? "1.1.1.1" : p.dnsServer);
                o.put("timezone", p.timezone);
                o.put("simCarrier", p.simCarrier);
                o.put("simMccMnc", p.simMccMnc);
                o.put("latitude", p.latitude);
                o.put("longitude", p.longitude);
                o.put("nodeIndex", p.nodeIndex);
                o.put("powerPercent", p.powerPercent <= 0 ? 95 : p.powerPercent);
                o.put("isBuiltInFree", p.isBuiltInFree);
                a.put(o);
            }
            prefs(c).edit().putString("vpn_profiles_v5", a.toString()).apply();
        } catch (Throwable ignored) {}
    }

    public static List<String> getVpnCategories(Context c) {
        Set<String> s = new LinkedHashSet<>();
        for (VpnProfile p : getVpnProfiles(c)) {
            if (p.category != null && !p.category.trim().isEmpty()) {
                s.add(p.category.trim());
            }
        }
        if (s.isEmpty()) s.add("ایالات متحده (United States)");
        return new ArrayList<>(s);
    }

    public static String getActiveVpnCategory(Context c) {
        return prefs(c).getString("active_vpn_category", "ایالات متحده (United States)");
    }

    public static void setActiveVpnCategory(Context c, String v) {
        prefs(c).edit().putString("active_vpn_category", v == null ? "ایالات متحده (United States)" : v).apply();
    }

    public static boolean isCategoryExpanded(Context c, String cat) {
        String a = getActiveVpnCategory(c);
        return prefs(c).getBoolean("cat_exp_" + cat, cat != null && cat.equals(a));
    }

    public static void setCategoryExpanded(Context c, String cat, boolean e) {
        prefs(c).edit().putBoolean("cat_exp_" + cat, e).apply();
    }

    public static boolean isClusterAutoRotateEnabled(Context c) {
        return prefs(c).getBoolean("vpn_cluster_auto_rotate", true);
    }

    public static void setClusterAutoRotateEnabled(Context c, boolean e) {
        prefs(c).edit().putBoolean("vpn_cluster_auto_rotate", e).apply();
    }

    public static VpnProfile rotateToNextSiblingInCluster(Context c) {
        List<VpnProfile> all = getVpnProfiles(c);
        if (all.isEmpty()) return null;
        String aid = getActiveVpnId(c);
        VpnProfile cur = null;
        for (VpnProfile p : all) {
            if (p.id.equals(aid)) {
                cur = p;
                break;
            }
        }
        if (cur == null) cur = all.get(0);
        List<VpnProfile> sib = new ArrayList<>();
        for (VpnProfile p : all) {
            if (p.category != null && p.category.equals(cur.category)) sib.add(p);
        }
        if (sib.size() <= 1) return cur;
        int idx = 0;
        for (int i = 0; i < sib.size(); i++) {
            if (sib.get(i).id.equals(cur.id)) {
                idx = i;
                break;
            }
        }
        VpnProfile nx = sib.get((idx + 1) % sib.size());
        setActiveVpnId(c, nx.id);
        if (isVpnAutoSyncEnabled(c)) applyVpnProfileToEnvironment(c, nx);
        return nx;
    }

    public static String getActiveVpnId(Context c) {
        return prefs(c).getString("active_vpn_id", "free_us_ny_1");
    }

    public static void setActiveVpnId(Context c, String id) {
        prefs(c).edit().putString("active_vpn_id", id).apply();
    }

    public static boolean isVpnConnected(Context c) {
        return prefs(c).getBoolean("vpn_connected_state", false);
    }

    public static void setVpnConnected(Context c, boolean v) {
        prefs(c).edit().putBoolean("vpn_connected_state", v).apply();
    }

    public static boolean isKillSwitchEnabled(Context c) {
        return prefs(c).getBoolean("vpn_kill_switch", true);
    }

    public static void setKillSwitchEnabled(Context c, boolean v) {
        prefs(c).edit().putBoolean("vpn_kill_switch", v).apply();
    }

    public static boolean isVpnAutoSyncEnabled(Context c) {
        return prefs(c).getBoolean("vpn_auto_sync_env", true);
    }

    public static void setVpnAutoSyncEnabled(Context c, boolean v) {
        prefs(c).edit().putBoolean("vpn_auto_sync_env", v).apply();
    }

    public static String getCustomDns(Context c) {
        return prefs(c).getString("vpn_custom_dns", "1.1.1.1");
    }

    public static void setCustomDns(Context c, String d) {
        prefs(c).edit().putString("vpn_custom_dns", d == null || d.trim().isEmpty() ? "1.1.1.1" : d.trim()).apply();
    }

    public static void applyVpnProfileToEnvironment(Context c, VpnProfile p) {
        if (p == null) return;
        GlobalEnvConfig g = getGlobalConfig(c);
        g.regionLabel = p.city + " (" + p.countryCode + ")";
        g.timezone = p.timezone;
        g.simCarrier = p.simCarrier;
        g.simMccMnc = p.simMccMnc;
        g.simCountryIso = p.countryCode;
        g.latitude = p.latitude;
        g.longitude = p.longitude;
        saveGlobalConfig(c, g);
    }

    public static File getVaultDir(Context c) {
        File d = new File(c.getFilesDir(), "vault_apks");
        if (!d.exists()) d.mkdirs();
        return d;
    }

    public static boolean backupApkToVault(Context c, String pkg, String src) {
        if (src == null) return false;
        File s = new File(src);
        if (!s.exists()) return false;
        File d = new File(getVaultDir(c), pkg + ".apk");
        try (FileInputStream in = new FileInputStream(s);
             FileOutputStream out = new FileOutputStream(d)) {
            byte[] b = new byte[8192];
            int l;
            while ((l = in.read(b)) > 0) out.write(b, 0, l);
            return true;
        } catch (Throwable e) {
            return false;
        }
    }

    public static File getVaultApkFile(Context c, String pkg) {
        return new File(getVaultDir(c), pkg + ".apk");
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core/CloneMetadataStore.java"), CLONE_METADATA_STORE)


# ---------------------------------------------------------------------------
# 2. MainActivity.java (100% Native AppCompat-Safe UI, Custom 6-Slot Bottom Bar)
# ---------------------------------------------------------------------------
MAIN_ACTIVITY = """package com.veyravault.app.ui;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.VpnService;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.InputType;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.animation.Animation;
import android.view.animation.LinearInterpolator;
import android.view.animation.RotateAnimation;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.GridLayout;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.veyravault.app.core.CloneMetadataStore;
import com.veyravault.app.core.Engine;
import com.veyravault.app.core.GmsSupportManager;
import com.veyravault.app.core.SecurityManager;
import com.veyravault.app.core.VirtualHookManager;
import com.veyravault.app.net.VaultVpnService;
import com.veyravault.app.util.JalaliCalendarUtil;
import com.veyravault.app.util.LocaleHelper;
import com.veyravault.app.util.ThemeHelper;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

public class MainActivity extends AppCompatActivity {

    private static final int REQ_VPN_PERMISSION = 901;
    private static final int REQ_ADD_APP_AUTO = 902;
    private static final int REQ_ADD_APP_SPACE = 903;

    private FrameLayout contentContainer;
    private final LinearLayout[] navTabViews = new LinearLayout[7];
    private final ImageView[] navTabIcons = new ImageView[7];
    private final TextView[] navTabLabels = new TextView[7];

    private int currentTabId = 1;
    private int selectedSpaceId = 0;
    private boolean isVpnTransitioning = false;

    private final Handler clockHandler = new Handler(Looper.getMainLooper());
    private TextView tvIranClockLive;
    private TextView tvUsaClockLive;

    private final Runnable clockTicker = new Runnable() {
        @Override
        public void run() {
            updateLiveClocks();
            clockHandler.postDelayed(this, 1000);
        }
    };

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.wrap(newBase));
    }

    private int resDrawable(String n) {
        int id = getResources().getIdentifier(n, "drawable", getPackageName());
        return id != 0 ? id : android.R.drawable.ic_menu_manage;
    }

    private int bgPage(boolean d) {
        return d ? Color.parseColor("#0A0F1D") : Color.parseColor("#F1F5F9");
    }

    private int bgCard(boolean d) {
        return d ? Color.parseColor("#131C31") : Color.parseColor("#FFFFFF");
    }

    private int bgCardInner(boolean d) {
        return d ? Color.parseColor("#0D1424") : Color.parseColor("#F8FAFC");
    }

    private int borderCard(boolean d) {
        return d ? Color.parseColor("#263554") : Color.parseColor("#CBD5E1");
    }

    private int txtPrimary(boolean d) {
        return d ? Color.parseColor("#F8FAFC") : Color.parseColor("#0F172A");
    }

    private int txtSecondary(boolean d) {
        return d ? Color.parseColor("#94A3B8") : Color.parseColor("#475569");
    }

    private GradientDrawable makeSurfaceBox(boolean d, int r, int s) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(bgCard(d));
        g.setCornerRadius(dp(r));
        g.setStroke(dp(1), s != 0 ? s : borderCard(d));
        return g;
    }

    private GradientDrawable makeInnerBox(boolean d, int r) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(bgCardInner(d));
        g.setCornerRadius(dp(r));
        g.setStroke(dp(1), borderCard(d));
        return g;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        ThemeHelper.applyTheme(this);
        super.onCreate(savedInstanceState);
        LocaleHelper.applyRtlIfSupported(this);

        if (SecurityManager.isLockEnabled(this) && !getIntent().getBooleanExtra("unlocked", false)) {
            startActivity(new Intent(this, SecurityLockActivity.class));
            finish();
            return;
        }

        VirtualHookManager.initializeDefaults(this);
        buildRootInterface();
        switchTab(1);
    }

    @Override
    protected void onResume() {
        super.onResume();
        clockHandler.removeCallbacks(clockTicker);
        clockHandler.post(clockTicker);
        if (contentContainer != null) {
            switchTab(currentTabId);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        clockHandler.removeCallbacks(clockTicker);
    }

    private void updateBottomNavSelection(int activeId) {
        boolean d = ThemeHelper.isDarkMode(this);
        int activeColor = Color.parseColor("#3B82F6");
        int inactiveColor = d ? Color.parseColor("#94A3B8") : Color.parseColor("#64748B");
        int[] ids = new int[]{1, 2, 4, 5, 6};
        for (int id : ids) {
            if (navTabIcons[id] != null) {
                navTabIcons[id].setColorFilter(id == activeId ? activeColor : inactiveColor);
            }
            if (navTabLabels[id] != null) {
                navTabLabels[id].setTextColor(id == activeId ? activeColor : inactiveColor);
                navTabLabels[id].setTypeface(Typeface.DEFAULT, id == activeId ? Typeface.BOLD : Typeface.NORMAL);
            }
        }
    }

    private View createNavTab(int id, String title, String iconName) {
        LinearLayout tab = new LinearLayout(this);
        tab.setOrientation(LinearLayout.VERTICAL);
        tab.setGravity(Gravity.CENTER);
        tab.setPadding(dp(2), dp(8), dp(2), dp(8));

        ImageView iv = new ImageView(this);
        iv.setImageResource(resDrawable(iconName));
        tab.addView(iv, new LinearLayout.LayoutParams(dp(22), dp(22)));

        TextView tv = new TextView(this);
        tv.setText(title);
        tv.setTextSize(10f);
        tv.setGravity(Gravity.CENTER);
        tv.setSingleLine(true);
        LinearLayout.LayoutParams tlp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT
        );
        tlp.topMargin = dp(3);
        tab.addView(tv, tlp);

        navTabViews[id] = tab;
        navTabIcons[id] = iv;
        navTabLabels[id] = tv;
        tab.setOnClickListener(v -> switchTab(id));
        return tab;
    }

    private void buildRootInterface() {
        boolean d = ThemeHelper.isDarkMode(this);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(bgPage(d));

        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);

        contentContainer = new FrameLayout(this);
        col.addView(contentContainer, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        LinearLayout navBar = new LinearLayout(this);
        navBar.setOrientation(LinearLayout.HORIZONTAL);
        navBar.setGravity(Gravity.CENTER_VERTICAL);
        navBar.setBackgroundColor(bgCard(d));
        navBar.setPadding(dp(4), dp(6), dp(4), dp(6));

        navBar.addView(createNavTab(1, "داشبورد", "ic_nav_dashboard"), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        navBar.addView(createNavTab(2, "فضاها", "ic_nav_spaces"), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        FrameLayout centerSlot = new FrameLayout(this);
        LinearLayout plusBtn = new LinearLayout(this);
        plusBtn.setGravity(Gravity.CENTER);
        GradientDrawable plusBg = new GradientDrawable();
        plusBg.setShape(GradientDrawable.OVAL);
        plusBg.setColor(Color.parseColor("#0284C7"));
        plusBg.setStroke(dp(2), Color.parseColor("#38BDF8"));
        plusBtn.setBackground(plusBg);

        ImageView plusIcon = new ImageView(this);
        plusIcon.setImageResource(resDrawable("ic_nav_add"));
        plusIcon.setColorFilter(Color.WHITE);
        plusBtn.addView(plusIcon, new LinearLayout.LayoutParams(dp(24), dp(24)));
        plusBtn.setOnClickListener(v -> openSmartAutoSpaceCloner());

        FrameLayout.LayoutParams cLp = new FrameLayout.LayoutParams(dp(46), dp(46));
        cLp.gravity = Gravity.CENTER;
        centerSlot.addView(plusBtn, cLp);
        navBar.addView(centerSlot, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        navBar.addView(createNavTab(4, "مرکز VPN", "ic_nav_vpn"), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        navBar.addView(createNavTab(5, "نشست‌ها", "ic_nav_session"), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        navBar.addView(createNavTab(6, "تنظیمات", "ic_nav_settings"), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        col.addView(navBar, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(col, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);
        updateBottomNavSelection(1);
    }

    private void openSmartAutoSpaceCloner() {
        Intent i = new Intent(this, AddAppActivity.class);
        i.putExtra("auto_assign_space", true);
        startActivityForResult(i, REQ_ADD_APP_AUTO);
    }

    private void openSpaceCloner(int s) {
        Intent i = new Intent(this, AddAppActivity.class);
        i.putExtra("auto_assign_space", false);
        i.putExtra("target_space_id", s);
        startActivityForResult(i, REQ_ADD_APP_SPACE);
    }

    @Override
    protected void onActivityResult(int rc, int res, Intent data) {
        super.onActivityResult(rc, res, data);
        if (rc == REQ_VPN_PERMISSION && res == RESULT_OK) {
            startVaultVpnService();
            switchTab(4);
        } else if ((rc == REQ_ADD_APP_AUTO || rc == REQ_ADD_APP_SPACE) && res == RESULT_OK) {
            if (data != null) selectedSpaceId = data.getIntExtra("assigned_space_id", selectedSpaceId);
            switchTab(2);
        }
    }

    private void switchTab(int t) {
        currentTabId = t;
        updateBottomNavSelection(t);
        if (contentContainer == null) return;
        contentContainer.removeAllViews();
        if (t == 1) contentContainer.addView(buildDashboardView());
        else if (t == 2) contentContainer.addView(buildSpacesView());
        else if (t == 4) contentContainer.addView(buildVpnHubView());
        else if (t == 5) contentContainer.addView(buildSessionAndGuideView());
        else if (t == 6) contentContainer.addView(buildSettingsView());
    }

    private View buildDashboardView() {
        boolean d = ThemeHelper.isDarkMode(this);
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(18), dp(16), dp(96));

        String lp = CloneMetadataStore.getLastActivePkg(this);
        int lu = CloneMetadataStore.getLastActiveUserId(this);
        CloneMetadataStore.EffectiveIdentity eff = CloneMetadataStore.resolveEffectiveIdentity(
                this, lp.isEmpty() ? "__global__" : lp, lu
        );
        boolean von = CloneMetadataStore.isVpnConnected(this);

        LinearLayout hero = new LinearLayout(this);
        hero.setOrientation(LinearLayout.VERTICAL);
        hero.setPadding(dp(18), dp(18), dp(18), dp(18));
        GradientDrawable hb = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                d ? new int[]{Color.parseColor("#0F172A"), Color.parseColor("#1E3A8A")}
                        : new int[]{Color.parseColor("#EFF6FF"), Color.parseColor("#DBEAFE")}
        );
        hb.setCornerRadius(dp(18));
        hb.setStroke(dp(1), Color.parseColor("#38BDF8"));
        hero.setBackground(hb);

        LinearLayout tr = new LinearLayout(this);
        tr.setOrientation(LinearLayout.HORIZONTAL);
        tr.setGravity(Gravity.CENTER_VERTICAL);

        TextView bt = new TextView(this);
        bt.setText("🛡️ VeyraVault Pro • مرکز فرماندهی ایزوله");
        bt.setTextSize(17f);
        bt.setTypeface(null, Typeface.BOLD);
        bt.setTextColor(d ? Color.WHITE : Color.parseColor("#0F172A"));
        tr.addView(bt, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView pill = new TextView(this);
        pill.setText("ضد نشت ۱۰۰٪ فعال");
        pill.setTextSize(11f);
        pill.setTypeface(null, Typeface.BOLD);
        pill.setTextColor(Color.WHITE);
        GradientDrawable pb = new GradientDrawable();
        pb.setColor(Color.parseColor("#10B981"));
        pb.setCornerRadius(dp(20));
        pill.setBackground(pb);
        pill.setPadding(dp(10), dp(4), dp(10), dp(4));
        tr.addView(pill);
        hero.addView(tr);

        TextView sub = new TextView(this);
        sub.setText("منبع هویت فعال: " + eff.prioritySource + "\\nمشخصات گوشی واقعی شما به هیچ برنامه‌ای ارسال نمی‌شود.");
        sub.setTextSize(12.5f);
        sub.setTextColor(d ? Color.parseColor("#BAE6FD") : Color.parseColor("#1E40AF"));
        sub.setPadding(0, dp(8), 0, dp(10));
        hero.addView(sub);

        LinearLayout pr = new LinearLayout(this);
        pr.setOrientation(LinearLayout.HORIZONTAL);
        pr.addView(makeMiniStatusPill(d, "📱 " + eff.brandModelDisplay, "#0284C7"), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        pr.addView(new View(this), new LinearLayout.LayoutParams(dp(8), dp(1)));
        pr.addView(makeMiniStatusPill(d, von ? "🟢 تونل VPN متصل" : "🟠 بدون VPN (هویت مجازی فعال)", von ? "#10B981" : "#F59E0B"), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        hero.addView(pr);

        LinearLayout.LayoutParams hl = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        hl.bottomMargin = dp(14);
        box.addView(hero, hl);

        LinearLayout cr = new LinearLayout(this);
        cr.setOrientation(LinearLayout.HORIZONTAL);

        LinearLayout ic = new LinearLayout(this);
        ic.setOrientation(LinearLayout.VERTICAL);
        ic.setPadding(dp(12), dp(12), dp(12), dp(12));
        ic.setBackground(makeSurfaceBox(d, 14, 0));
        TextView it = new TextView(this);
        it.setText("🇮🇷 زمان تهران (شمسی)");
        it.setTextSize(12f);
        it.setTypeface(null, Typeface.BOLD);
        it.setTextColor(Color.parseColor("#10B981"));
        ic.addView(it);
        tvIranClockLive = new TextView(this);
        tvIranClockLive.setTextSize(12f);
        tvIranClockLive.setTextColor(txtPrimary(d));
        tvIranClockLive.setPadding(0, dp(4), 0, 0);
        ic.addView(tvIranClockLive);

        LinearLayout uc = new LinearLayout(this);
        uc.setOrientation(LinearLayout.VERTICAL);
        uc.setPadding(dp(12), dp(12), dp(12), dp(12));
        uc.setBackground(makeSurfaceBox(d, 14, 0));
        TextView ut = new TextView(this);
        ut.setText("🇺🇸 نیویورک (میلادی)");
        ut.setTextSize(12f);
        ut.setTypeface(null, Typeface.BOLD);
        ut.setTextColor(Color.parseColor("#38BDF8"));
        uc.addView(ut);
        tvUsaClockLive = new TextView(this);
        tvUsaClockLive.setTextSize(12f);
        tvUsaClockLive.setTextColor(txtPrimary(d));
        tvUsaClockLive.setPadding(0, dp(4), 0, 0);
        uc.addView(tvUsaClockLive);

        cr.addView(ic, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        cr.addView(new View(this), new LinearLayout.LayoutParams(dp(10), dp(1)));
        cr.addView(uc, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        LinearLayout.LayoutParams cl = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cl.bottomMargin = dp(14);
        box.addView(cr, cl);
        updateLiveClocks();

        LinearLayout mc = createCard(d, "🌐 ماتریس هویت، سیم‌کارت و مختصات نشست فعال");
        GridLayout mg = new GridLayout(this);
        mg.setColumnCount(2);
        String[][] tiles = new String[][]{
                {"📱 نام و مدل دستگاه", eff.brandModelDisplay},
                {"📍 منطقه و مختصات", eff.regionLabel + "\\n(" + String.format(Locale.US, "%.4f, %.4f", eff.latitude, eff.longitude) + ")"},
                {"📶 سیم‌کارت مجازی", eff.simCarrier + " (" + eff.simMccMnc + ")"},
                {"🕒 منطقه زمانی و کشور", eff.timezone + " • ISO: " + eff.simCountryIso}
        };
        for (String[] t : tiles) {
            LinearLayout cell = new LinearLayout(this);
            cell.setOrientation(LinearLayout.VERTICAL);
            cell.setPadding(dp(10), dp(10), dp(10), dp(10));
            cell.setBackground(makeInnerBox(d, 10));
            TextView k = new TextView(this);
            k.setText(t[0]);
            k.setTextSize(11.5f);
            k.setTypeface(null, Typeface.BOLD);
            k.setTextColor(Color.parseColor("#0284C7"));
            cell.addView(k);
            TextView v = new TextView(this);
            v.setText(t[1]);
            v.setTextSize(12f);
            v.setTextColor(txtPrimary(d));
            v.setPadding(0, dp(4), 0, 0);
            cell.addView(v);
            GridLayout.LayoutParams gl = new GridLayout.LayoutParams();
            gl.width = 0;
            gl.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
            gl.setMargins(dp(4), dp(4), dp(4), dp(4));
            mg.addView(cell, gl);
        }
        mc.addView(mg);

        LinearLayout br = new LinearLayout(this);
        br.setOrientation(LinearLayout.HORIZONTAL);
        br.setPadding(0, dp(8), 0, 0);
        Button be = makePrimaryButton("⚙️ تغییر مدل گوشی و مکان کلی");
        be.setOnClickListener(v -> startActivity(new Intent(this, GlobalEnvironmentActivity.class)));
        br.addView(be, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        br.addView(new View(this), new LinearLayout.LayoutParams(dp(8), dp(1)));
        Button bs = makeSecondaryButton("🚀 ورود به فضاها", d);
        bs.setOnClickListener(v -> switchTab(2));
        br.addView(bs, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        mc.addView(br);
        box.addView(mc);

        LinearLayout pc = createCard(d, "🔀 سوییچ‌های هوشمند اولویت هویت (اپ ← فضا ← برنامه)");
        pc.addView(buildPrioritySwitchRow(d, "اولویت ۱: تنظیمات اختصاصی هر اپ (چرخ‌دنده کنار اپ)", CloneMetadataStore.isAppPrioritySwitchOn(this), v -> CloneMetadataStore.setAppPrioritySwitchOn(this, v)));
        pc.addView(buildPrioritySwitchRow(d, "اولویت ۲: تنظیمات اختصاصی هر فضا", CloneMetadataStore.isSpacePrioritySwitchOn(this), v -> CloneMetadataStore.setSpacePrioritySwitchOn(this, v)));
        pc.addView(buildPrioritySwitchRow(d, "اولویت ۳: تنظیمات کلی برنامه (ضد نشت گوشی واقعی)", CloneMetadataStore.isGlobalPrioritySwitchOn(this), v -> CloneMetadataStore.setGlobalPrioritySwitchOn(this, v)));
        box.addView(pc);

        LinearLayout rc = createCard(d, "⚡ شتاب‌دهنده سخت‌افزار و بهینه‌ساز واقعی حافظه RAM");
        final TextView rep = new TextView(this);
        Engine.MemoryOptimizationResult ir = Engine.optimizeMemoryAndSpeedDetailed(this);
        rep.setText("وضعیت فعلی رم: " + ir.afterUsedMb + " MB درگیر از کل " + ir.totalRamMb + " MB");
        rep.setTextColor(txtSecondary(d));
        rep.setTextSize(13f);
        rep.setPadding(0, 0, 0, dp(10));
        rc.addView(rep);

        Button bo = makePrimaryButton("🚀 اجرای بهینه‌سازی توربو و آزادسازی حافظه");
        bo.setOnClickListener(v -> {
            Engine.MemoryOptimizationResult r = Engine.optimizeMemoryAndSpeedDetailed(this);
            rep.setText("✅ بهینه‌سازی انجام شد:\\n• قبل: " + r.beforeUsedMb + " MB\\n• پس از عملیات: " + r.afterUsedMb + " MB\\n• رم آزاد شده: " + r.freedMb + " MB | کش پاک‌شده: " + r.clearedCacheFiles + " فایل");
            rep.setTextColor(Color.parseColor("#10B981"));
            Toast.makeText(this, "رم آزاد شد: " + r.freedMb + " مگابایت", Toast.LENGTH_SHORT).show();
        });
        rc.addView(bo);
        box.addView(rc);

        sv.addView(box);
        return sv;
    }

    private interface SwitchCallback {
        void onChanged(boolean c);
    }

    private View buildPrioritySwitchRow(boolean d, String t, boolean ch, SwitchCallback cb) {
        LinearLayout r = new LinearLayout(this);
        r.setOrientation(LinearLayout.HORIZONTAL);
        r.setGravity(Gravity.CENTER_VERTICAL);
        r.setPadding(dp(8), dp(6), dp(8), dp(6));

        TextView tv = new TextView(this);
        tv.setText(t);
        tv.setTextSize(12.5f);
        tv.setTextColor(txtPrimary(d));
        r.addView(tv, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Switch sw = new Switch(this);
        sw.setChecked(ch);
        sw.setOnCheckedChangeListener((b, c) -> {
            cb.onChanged(c);
            VirtualHookManager.applyEffectiveHookToSystem(
                    this,
                    CloneMetadataStore.getLastActivePkg(this),
                    CloneMetadataStore.getLastActiveUserId(this)
            );
        });
        r.addView(sw);
        return r;
    }

    private TextView makeMiniStatusPill(boolean d, String t, String hex) {
        TextView tv = new TextView(this);
        tv.setText(t);
        tv.setTextSize(11.5f);
        tv.setTypeface(null, Typeface.BOLD);
        tv.setTextColor(Color.parseColor(hex));
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(dp(8), dp(6), dp(8), dp(6));
        GradientDrawable g = new GradientDrawable();
        g.setColor(d ? Color.parseColor("#0F172A") : Color.WHITE);
        g.setCornerRadius(dp(10));
        g.setStroke(dp(1), Color.parseColor(hex));
        tv.setBackground(g);
        return tv;
    }

    private void updateLiveClocks() {
        try {
            if (tvIranClockLive != null) {
                tvIranClockLive.setText(JalaliCalendarUtil.getIranFullDateTime());
            }
            if (tvUsaClockLive != null) {
                SimpleDateFormat s = new SimpleDateFormat("yyyy/MM/dd | HH:mm:ss", Locale.US);
                s.setTimeZone(TimeZone.getTimeZone("America/New_York"));
                tvUsaClockLive.setText(s.format(new Date()) + " EST");
            }
        } catch (Throwable ignored) {}
    }

    private View buildSpacesView() {
        boolean d = ThemeHelper.isDarkMode(this);
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(14), dp(16), dp(14), dp(96));

        HorizontalScrollView hsv = new HorizontalScrollView(this);
        hsv.setHorizontalScrollBarEnabled(false);
        LinearLayout chips = new LinearLayout(this);
        chips.setOrientation(LinearLayout.HORIZONTAL);
        chips.setPadding(0, 0, 0, dp(12));

        List<Integer> act = new ArrayList<>();
        act.add(0);
        for (int u = 1; u < 10; u++) {
            if (CloneMetadataStore.isSpaceCreated(this, u) || !Engine.getClonedAppsForUser(this, u).isEmpty()) {
                CloneMetadataStore.markSpaceCreated(this, u, true);
                act.add(u);
            }
        }
        if (!act.contains(selectedSpaceId)) selectedSpaceId = 0;

        for (final int sid : act) {
            boolean sel = (sid == selectedSpaceId);
            TextView ch = new TextView(this);
            ch.setText(CloneMetadataStore.getSpaceDisplayName(this, sid));
            ch.setTextSize(13f);
            ch.setTypeface(null, Typeface.BOLD);
            ch.setPadding(dp(16), dp(8), dp(16), dp(8));
            ch.setTextColor(sel ? Color.WHITE : txtPrimary(d));

            GradientDrawable bg = new GradientDrawable();
            bg.setColor(sel ? Color.parseColor("#0284C7") : bgCard(d));
            bg.setCornerRadius(dp(20));
            bg.setStroke(dp(1), sel ? Color.parseColor("#38BDF8") : borderCard(d));
            ch.setBackground(bg);

            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT
            );
            lp.setMargins(dp(4), 0, dp(4), 0);
            ch.setOnClickListener(v -> {
                selectedSpaceId = sid;
                switchTab(2);
            });
            chips.addView(ch, lp);
        }

        TextView ns = new TextView(this);
        ns.setText("＋ فضای جدید");
        ns.setTextSize(13f);
        ns.setTypeface(null, Typeface.BOLD);
        ns.setPadding(dp(14), dp(8), dp(14), dp(8));
        ns.setTextColor(Color.parseColor("#10B981"));
        GradientDrawable ab = new GradientDrawable();
        ab.setColor(bgCard(d));
        ab.setCornerRadius(dp(20));
        ab.setStroke(dp(1), Color.parseColor("#10B981"));
        ns.setBackground(ab);
        ns.setOnClickListener(v -> {
            for (int u = 1; u < 10; u++) {
                if (!CloneMetadataStore.isSpaceCreated(this, u)) {
                    CloneMetadataStore.markSpaceCreated(this, u, true);
                    selectedSpaceId = u;
                    Toast.makeText(this, "فضای " + (u + 1) + " ساخته شد", Toast.LENGTH_SHORT).show();
                    switchTab(2);
                    return;
                }
            }
        });
        chips.addView(ns);
        hsv.addView(chips);
        box.addView(hsv);

        LinearLayout sh = new LinearLayout(this);
        sh.setOrientation(LinearLayout.VERTICAL);
        sh.setPadding(dp(12), dp(12), dp(12), dp(12));
        sh.setBackground(makeSurfaceBox(d, 14, 0));

        LinearLayout tr = new LinearLayout(this);
        tr.setOrientation(LinearLayout.HORIZONTAL);
        tr.setGravity(Gravity.CENTER_VERTICAL);
        TextView st = new TextView(this);
        st.setText("📦 " + CloneMetadataStore.getSpaceDisplayName(this, selectedSpaceId));
        st.setTextSize(15f);
        st.setTypeface(null, Typeface.BOLD);
        st.setTextColor(txtPrimary(d));
        tr.addView(st, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button rn = makeSecondaryButton("✏️ نام فضا", d);
        rn.setOnClickListener(v -> showRenameSpaceDialog(selectedSpaceId));
        tr.addView(rn);
        tr.addView(new View(this), new LinearLayout.LayoutParams(dp(6), dp(1)));

        Button si = makeSecondaryButton("🎭 هویت فضا", d);
        si.setOnClickListener(v -> showAppSettingsDialog("__space__", selectedSpaceId, "هویت اختصاصی " + CloneMetadataStore.getSpaceDisplayName(this, selectedSpaceId)));
        tr.addView(si);
        tr.addView(new View(this), new LinearLayout.LayoutParams(dp(6), dp(1)));

        Button ad = makePrimaryButton("＋ افزودن اپ");
        ad.setOnClickListener(v -> openSpaceCloner(selectedSpaceId));
        tr.addView(ad);
        sh.addView(tr);

        CloneMetadataStore.EffectiveIdentity se = CloneMetadataStore.resolveEffectiveIdentity(this, "__space__", selectedSpaceId);
        TextView ss = new TextView(this);
        ss.setText("هویت پایه این فضا: " + se.brandModelDisplay + " | " + se.regionLabel + " (" + se.prioritySource + ")");
        ss.setTextSize(11.5f);
        ss.setTextColor(Color.parseColor("#0284C7"));
        ss.setPadding(0, dp(6), 0, 0);
        sh.addView(ss);

        LinearLayout.LayoutParams sl = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        sl.bottomMargin = dp(12);
        box.addView(sh, sl);

        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(2);
        grid.addView(buildAppCard("فروشگاه گوگل‌پلی", "com.android.vending", getResources().getDrawable(android.R.drawable.sym_def_app_icon), selectedSpaceId, true, d));
        grid.addView(buildAppCard("تنظیمات اندروید فضا", "com.veyravault.space.settings", getResources().getDrawable(android.R.drawable.ic_menu_preferences), selectedSpaceId, true, d));

        List<Engine.ClonedAppItem> apps = Engine.getClonedAppsForUser(this, selectedSpaceId);
        for (Engine.ClonedAppItem it : apps) {
            CloneMetadataStore.CloneMeta m = CloneMetadataStore.getCloneMeta(this, it.packageName, selectedSpaceId);
            String dn = (m.customName != null && !m.customName.trim().isEmpty()) ? m.customName : it.name;
            grid.addView(buildAppCard(dn, it.packageName, it.icon, selectedSpaceId, false, d));
        }
        box.addView(grid);
        sv.addView(box);
        return sv;
    }

    private View buildAppCard(String title, String pkg, android.graphics.drawable.Drawable icon, int uid, boolean builtIn, boolean d) {
        FrameLayout cf = new FrameLayout(this);
        cf.setBackground(makeSurfaceBox(d, 14, 0));

        LinearLayout co = new LinearLayout(this);
        co.setOrientation(LinearLayout.VERTICAL);
        co.setGravity(Gravity.CENTER_HORIZONTAL);
        co.setPadding(dp(10), dp(14), dp(10), dp(12));

        ImageView iv = new ImageView(this);
        iv.setImageDrawable(icon);
        co.addView(iv, new LinearLayout.LayoutParams(dp(48), dp(48)));

        TextView tn = new TextView(this);
        tn.setText(title);
        tn.setTextColor(txtPrimary(d));
        tn.setTextSize(13f);
        tn.setTypeface(null, Typeface.BOLD);
        tn.setSingleLine(true);
        tn.setEllipsize(TextUtils.TruncateAt.END);
        tn.setGravity(Gravity.CENTER);
        tn.setPadding(0, dp(6), 0, dp(2));
        co.addView(tn);

        CloneMetadataStore.EffectiveIdentity ae = CloneMetadataStore.resolveEffectiveIdentity(this, pkg, uid);
        TextView te = new TextView(this);
        String pre = (ae.priorityLevel == 1) ? "★ اپ: " : (ae.priorityLevel == 2 ? "◆ فضا: " : "");
        te.setText(pre + ae.brandModelDisplay + "\\n" + ae.regionLabel);
        te.setTextColor(ae.priorityLevel == 1 ? Color.parseColor("#10B981") : txtSecondary(d));
        te.setTextSize(10.5f);
        te.setGravity(Gravity.CENTER);
        co.addView(te);
        cf.addView(co);

        int un = CloneMetadataStore.getUnreadCount(this, pkg, uid);
        String bt = CloneMetadataStore.formatBadgeText(un);
        if (!bt.isEmpty()) {
            TextView bd = new TextView(this);
            bd.setText(bt);
            bd.setTextColor(Color.WHITE);
            bd.setTextSize(11f);
            bd.setTypeface(null, Typeface.BOLD);
            bd.setGravity(Gravity.CENTER);
            bd.setPadding(dp(7), dp(2), dp(7), dp(2));
            GradientDrawable bb = new GradientDrawable();
            bb.setColor(Color.parseColor("#EF4444"));
            bb.setCornerRadius(dp(12));
            bd.setBackground(bb);
            FrameLayout.LayoutParams bl = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            bl.gravity = Gravity.TOP | Gravity.LEFT;
            bl.setMargins(dp(8), dp(8), 0, 0);
            cf.addView(bd, bl);
        }

        TextView gear = new TextView(this);
        gear.setText("⚙️");
        gear.setTextSize(15f);
        gear.setPadding(dp(6), dp(4), dp(6), dp(4));
        FrameLayout.LayoutParams gl = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        gl.gravity = Gravity.TOP | Gravity.RIGHT;
        gl.setMargins(0, dp(4), dp(4), 0);
        gear.setOnClickListener(v -> showAppSettingsDialog(pkg, uid, title));
        cf.addView(gear, gl);

        cf.setOnClickListener(v -> {
            CloneMetadataStore.setUnreadCount(this, pkg, uid, 0);
            if ("com.veyravault.space.settings".equals(pkg)) {
                showSpaceAndroidSettingsDialog(uid);
            } else if ("com.android.vending".equals(pkg)) {
                GmsSupportManager.launchGooglePlayForSpace(this, uid);
                switchTab(2);
            } else {
                Toast.makeText(this, "در حال اجرای ایزوله " + title + " (" + ae.brandModelDisplay + ")...", Toast.LENGTH_SHORT).show();
                boolean ok = Engine.launchClone(this, pkg, uid);
                if (!ok) Toast.makeText(this, "خطا در اجرای برنامه", Toast.LENGTH_LONG).show();
            }
        });

        GridLayout.LayoutParams gp = new GridLayout.LayoutParams();
        gp.width = 0;
        gp.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
        gp.setMargins(dp(6), dp(6), dp(6), dp(6));
        cf.setLayoutParams(gp);
        return cf;
    }

    private void showRenameSpaceDialog(final int sid) {
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle("تغییر نام " + CloneMetadataStore.getSpaceDisplayName(this, sid));
        final EditText et = new EditText(this);
        et.setHint("مثلاً: فضای کاری");
        et.setText(CloneMetadataStore.getSpaceDisplayName(this, sid));
        b.setView(et);
        b.setPositiveButton("ذخیره", (dd, w) -> {
            CloneMetadataStore.setSpaceCustomName(this, sid, et.getText().toString());
            switchTab(2);
        });
        b.setNegativeButton("انصراف", null);
        b.show();
    }

    private void showSpaceAndroidSettingsDialog(int uid) {
        String sn = CloneMetadataStore.getSpaceDisplayName(this, uid);
        CloneMetadataStore.EffectiveIdentity e = CloneMetadataStore.resolveEffectiveIdentity(this, "__space__", uid);
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle("⚙️ تنظیمات اندروید " + sn);
        String info = "• منبع هویت فعال: " + e.prioritySource
                + "\\n• برند و مدل دستگاه: " + e.brandModelDisplay
                + "\\n• منطقه و کشور: " + e.regionLabel
                + "\\n• منطقه زمانی: " + e.timezone
                + "\\n• سیم‌کارت مجازی: " + e.simCarrier + " (" + e.simMccMnc + ")"
                + "\\n• مختصات GPS: " + e.latitude + ", " + e.longitude
                + "\\n• حفاظت در برابر نشت گوشی واقعی: فعال (۱۰۰٪)";
        b.setMessage(info);
        b.setPositiveButton("ویرایش هویت اختصاصی این فضا (اولویت ۲)", (dd, w) -> showAppSettingsDialog("__space__", uid, "هویت اختصاصی " + sn));
        b.setNeutralButton("تغییر هویت کلی برنامه (اولویت ۳)", (dd, w) -> startActivity(new Intent(this, GlobalEnvironmentActivity.class)));
        b.setNegativeButton("بستن", null);
        b.show();
    }

    private void showAppSettingsDialog(final String pkg, final int uid, String curTitle) {
        final boolean isSpace = "__space__".equals(pkg);
        final CloneMetadataStore.CloneMeta meta = CloneMetadataStore.getCloneMeta(this, pkg, uid);
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle((isSpace ? "🎭 تنظیمات اولویت ۲: " : "⚙️ تنظیمات اولویت ۱: ") + curTitle);

        ScrollView sv = new ScrollView(this);
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(dp(18), dp(12), dp(18), dp(8));

        final Switch swP = new Switch(this);
        swP.setText(isSpace ? "فعال‌سازی اولویت ۲ برای این فضا" : "فعال‌سازی اولویت ۱ اختصاصی برای این برنامه");
        swP.setChecked(meta.priorityEnabled);
        l.addView(swP);

        final EditText etN = new EditText(this);
        etN.setHint("نام دلخواه برنامه");
        etN.setText(meta.customName);
        if (!isSpace) l.addView(etN);

        TextView dl = new TextView(this);
        dl.setText("انتخاب سریع مدل گوشی خارجی (بدون تکرار برند):");
        dl.setPadding(0, dp(8), 0, dp(4));
        l.addView(dl);

        final String[][] dev = new String[][]{
                {"— استفاده از اولویت پایین‌تر —", "", ""},
                {"Samsung Galaxy S24 Ultra (USA)", "Samsung", "Galaxy S24 Ultra"},
                {"Apple iPhone 16 Pro Max (USA)", "Apple", "iPhone 16 Pro Max"},
                {"Google Pixel 9 Pro XL (USA)", "Google", "Pixel 9 Pro XL"},
                {"Xiaomi 14 Ultra (Global)", "Xiaomi", "14 Ultra"},
                {"OnePlus 12 Pro (Global)", "OnePlus", "12 Pro"}
        };
        String[] dt = new String[dev.length];
        for (int i = 0; i < dev.length; i++) dt[i] = dev[i][0];
        Spinner spD = new Spinner(this);
        spD.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, dt));
        l.addView(spD);

        final EditText etB = new EditText(this);
        etB.setHint("برند دستگاه (مثلاً Samsung یا Apple)");
        etB.setText(meta.deviceBrand);
        l.addView(etB);

        final EditText etM = new EditText(this);
        etM.setHint("مدل دستگاه (مثلاً Galaxy S24 Ultra)");
        etM.setText(meta.deviceModel);
        l.addView(etM);

        spD.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(android.widget.AdapterView<?> p, View v, int pos, long id) {
                if (pos > 0) {
                    etB.setText(dev[pos][1]);
                    etM.setText(dev[pos][2]);
                }
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> p) {}
        });

        TextView ll = new TextView(this);
        ll.setText("انتخاب سریع کشور، سیم‌کارت و مختصات:");
        ll.setPadding(0, dp(8), 0, dp(4));
        l.addView(ll);

        final String[][] loc = new String[][]{
                {"— انتخاب سریع کشور —", "", "", "", "", "", "", ""},
                {"🇺🇸 آمریکا (New York • T-Mobile)", "New York, United States", "America/New_York", "T-Mobile USA", "310260", "US", "40.7128", "-74.0060"},
                {"🇺🇸 آمریکا (Los Angeles • Verizon)", "Los Angeles, United States", "America/Los_Angeles", "Verizon", "311480", "US", "34.0522", "-118.2437"},
                {"🇩🇪 آلمان (Frankfurt • Telekom)", "Frankfurt, Germany", "Europe/Berlin", "Telekom DE", "26201", "DE", "50.1109", "8.6821"},
                {"🇬🇧 انگلستان (London • Vodafone)", "London, United Kingdom", "Europe/London", "Vodafone UK", "23415", "GB", "51.5074", "-0.1278"},
                {"🇳🇱 هلند (Amsterdam • KPN)", "Amsterdam, Netherlands", "Europe/Amsterdam", "KPN NL", "20408", "NL", "52.3676", "4.9041"}
        };
        String[] lt = new String[loc.length];
        for (int i = 0; i < loc.length; i++) lt[i] = loc[i][0];
        Spinner spL = new Spinner(this);
        spL.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, lt));
        l.addView(spL);

        final EditText etR = new EditText(this);
        etR.setHint("منطقه مکانی (مثلاً New York, United States)");
        etR.setText(meta.regionLabel);
        l.addView(etR);

        final EditText etT = new EditText(this);
        etT.setHint("منطقه زمانی (مثلاً America/New_York)");
        etT.setText(meta.timezone);
        l.addView(etT);

        final EditText etC = new EditText(this);
        etC.setHint("اپراتور سیم‌کارت (مثلاً T-Mobile USA)");
        etC.setText(meta.simCarrier);
        l.addView(etC);

        final EditText etMc = new EditText(this);
        etMc.setHint("کد سیم‌کارت MCC/MNC (مثلاً 310260)");
        etMc.setText(meta.simMccMnc);
        l.addView(etMc);

        final EditText etLa = new EditText(this);
        etLa.setHint("عرض جغرافیایی (Latitude)");
        etLa.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL | InputType.TYPE_NUMBER_FLAG_SIGNED);
        etLa.setText(String.valueOf(meta.latitude));
        l.addView(etLa);

        final EditText etLo = new EditText(this);
        etLo.setHint("طول جغرافیایی (Longitude)");
        etLo.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL | InputType.TYPE_NUMBER_FLAG_SIGNED);
        etLo.setText(String.valueOf(meta.longitude));
        l.addView(etLo);

        final Switch swL = new Switch(this);
        swL.setText("اعمال مختصات اختصاصی GPS");
        swL.setChecked(meta.locationSpoofEnabled);
        l.addView(swL);

        spL.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(android.widget.AdapterView<?> p, View v, int pos, long id) {
                if (pos > 0) {
                    etR.setText(loc[pos][1]);
                    etT.setText(loc[pos][2]);
                    etC.setText(loc[pos][3]);
                    etMc.setText(loc[pos][4]);
                    etLa.setText(loc[pos][6]);
                    etLo.setText(loc[pos][7]);
                    swL.setChecked(true);
                }
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> p) {}
        });

        sv.addView(l);
        b.setView(sv);
        b.setPositiveButton("ذخیره و اعمال در نشست", (dd, w) -> {
            meta.priorityEnabled = swP.isChecked();
            meta.customName = etN.getText().toString().trim();
            meta.deviceBrand = etB.getText().toString().trim();
            meta.deviceModel = CloneMetadataStore.cleanModelOnly(meta.deviceBrand, etM.getText().toString().trim());
            meta.regionLabel = etR.getText().toString().trim();
            meta.timezone = etT.getText().toString().trim();
            meta.simCarrier = etC.getText().toString().trim();
            meta.simMccMnc = etMc.getText().toString().trim();
            try {
                meta.latitude = Double.parseDouble(etLa.getText().toString().trim());
                meta.longitude = Double.parseDouble(etLo.getText().toString().trim());
            } catch (Throwable ignored) {}
            meta.locationSpoofEnabled = swL.isChecked();
            VirtualHookManager.applyHookConfig(this, pkg, uid, meta);
            Toast.makeText(this, "تنظیمات در حافظه و نشست ثبت شد", Toast.LENGTH_SHORT).show();
            switchTab(2);
        });
        if (!isSpace && !"com.android.vending".equals(pkg) && !"com.veyravault.space.settings".equals(pkg)) {
            b.setNeutralButton("حذف برنامه از فضا", (dd, w) -> {
                Engine.deleteClone(this, pkg, uid);
                switchTab(2);
            });
        }
        b.setNegativeButton("انصراف", null);
        b.show();
    }

    private View buildVpnHubView() {
        boolean d = ThemeHelper.isDarkMode(this);
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(16), dp(16), dp(96));

        final boolean conn = CloneMetadataStore.isVpnConnected(this);
        final List<CloneMetadataStore.VpnProfile> all = CloneMetadataStore.getVpnProfiles(this);
        final String aid = CloneMetadataStore.getActiveVpnId(this);
        CloneMetadataStore.VpnProfile cur = all.get(0);
        for (CloneMetadataStore.VpnProfile p : all) {
            if (p.id.equals(aid)) {
                cur = p;
                break;
            }
        }
        final CloneMetadataStore.VpnProfile fin = cur;

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.setPadding(dp(16), dp(12), dp(16), dp(12));
        top.setBackground(makeSurfaceBox(d, 24, conn ? Color.parseColor("#10B981") : Color.parseColor("#38BDF8")));

        TextView fl = new TextView(this);
        fl.setText(fin.flagEmoji);
        fl.setTextSize(24f);
        top.addView(fl);

        LinearLayout info = new LinearLayout(this);
        info.setOrientation(LinearLayout.VERTICAL);
        info.setPadding(dp(12), 0, dp(12), 0);
        TextView sc = new TextView(this);
        sc.setText(fin.category + " • سوییچ خودکار روشن");
        sc.setTextSize(11.5f);
        sc.setTextColor(Color.parseColor("#0284C7"));
        sc.setTypeface(null, Typeface.BOLD);
        info.addView(sc);

        TextView sn = new TextView(this);
        sn.setText(fin.name + " (" + fin.city + " • ⚡" + fin.powerPercent + "%)");
        sn.setTextSize(14f);
        sn.setTypeface(null, Typeface.BOLD);
        sn.setTextColor(txtPrimary(d));
        info.addView(sn);
        top.addView(info, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView rot = new TextView(this);
        rot.setText("🔄 نود بعدی");
        rot.setTextSize(12f);
        rot.setTypeface(null, Typeface.BOLD);
        rot.setTextColor(Color.WHITE);
        GradientDrawable rb = new GradientDrawable();
        rb.setColor(Color.parseColor("#0284C7"));
        rb.setCornerRadius(dp(14));
        rot.setBackground(rb);
        rot.setPadding(dp(10), dp(6), dp(10), dp(6));
        rot.setOnClickListener(v -> {
            CloneMetadataStore.VpnProfile nx = CloneMetadataStore.rotateToNextSiblingInCluster(this);
            if (nx != null) {
                if (CloneMetadataStore.isVpnConnected(this)) startVaultVpnService();
                Toast.makeText(this, "سوییچ خودکار در همان کشور به: " + nx.name, Toast.LENGTH_SHORT).show();
                switchTab(4);
            }
        });
        top.addView(rot);

        LinearLayout.LayoutParams tl = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        tl.bottomMargin = dp(20);
        box.addView(top, tl);

        LinearLayout sec = new LinearLayout(this);
        sec.setOrientation(LinearLayout.VERTICAL);
        sec.setGravity(Gravity.CENTER);
        sec.setPadding(dp(16), dp(18), dp(16), dp(18));
        sec.setBackground(makeSurfaceBox(d, 22, 0));

        FrameLayout cc = new FrameLayout(this);
        int os = dp(176);
        int isz = dp(148);
        final View ring = new View(this);
        GradientDrawable rd = new GradientDrawable();
        rd.setShape(GradientDrawable.OVAL);
        if (isVpnTransitioning) {
            rd.setColors(new int[]{Color.parseColor("#EF4444"), Color.TRANSPARENT, Color.parseColor("#EF4444")});
            rd.setGradientType(GradientDrawable.SWEEP_GRADIENT);
        } else {
            rd.setColor(Color.TRANSPARENT);
            rd.setStroke(dp(5), conn ? Color.parseColor("#34D399") : Color.parseColor("#F87171"));
        }
        ring.setBackground(rd);
        cc.addView(ring, new FrameLayout.LayoutParams(os, os, Gravity.CENTER));

        LinearLayout mc = new LinearLayout(this);
        mc.setOrientation(LinearLayout.VERTICAL);
        mc.setGravity(Gravity.CENTER);
        GradientDrawable cb = new GradientDrawable();
        cb.setShape(GradientDrawable.OVAL);
        cb.setColor(conn ? Color.parseColor("#10B981") : Color.parseColor("#EF4444"));
        cb.setStroke(dp(4), Color.WHITE);
        mc.setBackground(cb);

        TextView pi = new TextView(this);
        pi.setText(conn ? "🛡️" : "⏻");
        pi.setTextSize(38f);
        pi.setTextColor(Color.WHITE);
        pi.setGravity(Gravity.CENTER);
        mc.addView(pi);

        TextView cs = new TextView(this);
        cs.setText(isVpnTransitioning ? "WAIT..." : (conn ? "ONLINE" : "OFFLINE"));
        cs.setTextSize(13f);
        cs.setTypeface(null, Typeface.BOLD);
        cs.setTextColor(Color.WHITE);
        mc.addView(cs);
        cc.addView(mc, new FrameLayout.LayoutParams(isz, isz, Gravity.CENTER));
        sec.addView(cc, new LinearLayout.LayoutParams(os, os));

        final TextView cw = new TextView(this);
        cw.setText(isVpnTransitioning ? "در حال برقراری تونل..." : (conn ? "CONNECTED (متصل)" : "CONNECT"));
        cw.setTextSize(20f);
        cw.setTypeface(null, Typeface.BOLD);
        cw.setTextColor(conn ? Color.parseColor("#10B981") : Color.parseColor("#EF4444"));
        cw.setGravity(Gravity.CENTER);
        cw.setPadding(0, dp(12), 0, dp(4));
        sec.addView(cw);

        TextView csub = new TextView(this);
        csub.setText(conn
                ? "خوشه فعال: " + fin.category + " | در صورت افت، سوییچ خودکار به سرور بعدی انجام می‌شود"
                : "برای اتصال و همگام‌سازی خودکار موقعیت، سیم‌کارت و آی‌پی روی دایره بزنید");
        csub.setTextSize(12f);
        csub.setTextColor(txtSecondary(d));
        csub.setGravity(Gravity.CENTER);
        sec.addView(csub);

        View.OnClickListener tog = v -> {
            if (isVpnTransitioning) return;
            isVpnTransitioning = true;
            GradientDrawable rr = new GradientDrawable();
            rr.setShape(GradientDrawable.OVAL);
            rr.setStroke(dp(6), Color.parseColor("#EF4444"), dp(18), dp(10));
            ring.setBackground(rr);
            RotateAnimation ra = new RotateAnimation(0f, 360f, Animation.RELATIVE_TO_SELF, 0.5f, Animation.RELATIVE_TO_SELF, 0.5f);
            ra.setDuration(750);
            ra.setRepeatCount(Animation.INFINITE);
            ra.setInterpolator(new LinearInterpolator());
            ring.startAnimation(ra);
            cw.setText(conn ? "DISCONNECTING..." : "CONNECTING...");
            clockHandler.postDelayed(() -> {
                ring.clearAnimation();
                isVpnTransitioning = false;
                if (conn) {
                    stopVaultVpnService();
                    switchTab(4);
                } else {
                    if (CloneMetadataStore.isVpnAutoSyncEnabled(this)) {
                        CloneMetadataStore.applyVpnProfileToEnvironment(this, fin);
                    }
                    Intent prep = VpnService.prepare(this);
                    if (prep != null) {
                        startActivityForResult(prep, REQ_VPN_PERMISSION);
                    } else {
                        startVaultVpnService();
                        switchTab(4);
                    }
                }
            }, 900);
        };
        mc.setOnClickListener(tog);
        cw.setOnClickListener(tog);

        LinearLayout.LayoutParams sl = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        sl.bottomMargin = dp(16);
        box.addView(sec, sl);

        LinearLayout list = createCard(d, "🌍 لیست کشورها و دسته‌بندی سرورهای VPN");
        TextView hint = new TextView(this);
        hint.setText("روی نام هر کشور بزنید تا لیست سرورهایش باز یا بسته شود. با دکمه «＋» روبه‌روی هر کشور، یک VPN جدید در همان کشور بسازید.");
        hint.setTextSize(11.5f);
        hint.setTextColor(txtSecondary(d));
        hint.setPadding(0, 0, 0, dp(10));
        list.addView(hint);

        List<String> cats = CloneMetadataStore.getVpnCategories(this);
        for (final String cat : cats) {
            List<CloneMetadataStore.VpnProfile> cp = new ArrayList<>();
            for (CloneMetadataStore.VpnProfile p : all) {
                if (cat.equals(p.category)) cp.add(p);
            }
            if (cp.isEmpty()) continue;
            final CloneMetadataStore.VpnProfile sample = cp.get(0);
            final boolean exp = CloneMetadataStore.isCategoryExpanded(this, cat);

            LinearLayout cont = new LinearLayout(this);
            cont.setOrientation(LinearLayout.VERTICAL);
            cont.setBackground(makeInnerBox(d, 14));
            LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            clp.bottomMargin = dp(10);
            cont.setLayoutParams(clp);

            LinearLayout head = new LinearLayout(this);
            head.setOrientation(LinearLayout.HORIZONTAL);
            head.setGravity(Gravity.CENTER_VERTICAL);
            head.setPadding(dp(12), dp(12), dp(12), dp(12));

            TextView cf = new TextView(this);
            cf.setText(sample.flagEmoji);
            cf.setTextSize(22f);
            head.addView(cf);

            LinearLayout tc = new LinearLayout(this);
            tc.setOrientation(LinearLayout.VERTICAL);
            tc.setPadding(dp(10), 0, dp(8), 0);
            TextView ct = new TextView(this);
            ct.setText(cat);
            ct.setTextSize(14f);
            ct.setTypeface(null, Typeface.BOLD);
            ct.setTextColor(txtPrimary(d));
            tc.addView(ct);

            TextView csb = new TextView(this);
            csb.setText(cp.size() + " سرور هم‌خانواده • پشتیبانی سوییچ خودکار");
            csb.setTextSize(11f);
            csb.setTextColor(txtSecondary(d));
            tc.addView(csb);
            head.addView(tc, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            TextView add = new TextView(this);
            add.setText("＋");
            add.setTextSize(17f);
            add.setTypeface(null, Typeface.BOLD);
            add.setTextColor(Color.WHITE);
            add.setGravity(Gravity.CENTER);
            GradientDrawable ab = new GradientDrawable();
            ab.setColor(Color.parseColor("#10B981"));
            ab.setCornerRadius(dp(10));
            add.setBackground(ab);
            add.setPadding(dp(10), dp(4), dp(10), dp(4));
            add.setOnClickListener(v -> {
                CloneMetadataStore.VpnProfile t = new CloneMetadataStore.VpnProfile();
                t.id = "";
                t.category = cat;
                t.countryCode = sample.countryCode;
                t.flagEmoji = sample.flagEmoji;
                t.city = sample.city;
                t.timezone = sample.timezone;
                t.simCarrier = sample.simCarrier;
                t.simMccMnc = sample.simMccMnc;
                t.latitude = sample.latitude;
                t.longitude = sample.longitude;
                t.protocol = "SOCKS5/TLS";
                t.serverHost = "";
                t.serverPort = 443;
                t.dnsServer = "1.1.1.1";
                t.powerPercent = 98;
                showAddOrEditVpnDialog(t, true);
            });
            head.addView(add);

            TextView ar = new TextView(this);
            ar.setText(exp ? "  ▼" : "  ◀");
            ar.setTextSize(14f);
            ar.setTextColor(txtSecondary(d));
            head.addView(ar);
            head.setOnClickListener(v -> {
                CloneMetadataStore.setCategoryExpanded(this, cat, !exp);
                CloneMetadataStore.setActiveVpnCategory(this, cat);
                switchTab(4);
            });
            cont.addView(head);

            if (exp) {
                for (final CloneMetadataStore.VpnProfile p : cp) {
                    boolean sel = p.id.equals(aid);
                    LinearLayout row = new LinearLayout(this);
                    row.setOrientation(LinearLayout.HORIZONTAL);
                    row.setGravity(Gravity.CENTER_VERTICAL);
                    row.setPadding(dp(12), dp(10), dp(12), dp(10));
                    GradientDrawable rbg = new GradientDrawable();
                    rbg.setColor(sel ? (d ? Color.parseColor("#0F2942") : Color.parseColor("#E0F2FE")) : bgCard(d));
                    rbg.setCornerRadius(dp(10));
                    rbg.setStroke(dp(1), sel ? Color.parseColor("#0284C7") : borderCard(d));
                    row.setBackground(rbg);
                    LinearLayout.LayoutParams rlp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
                    rlp.setMargins(dp(8), 0, dp(8), dp(8));
                    row.setLayoutParams(rlp);

                    TextView rf = new TextView(this);
                    rf.setText(p.flagEmoji);
                    rf.setTextSize(18f);
                    row.addView(rf);

                    LinearLayout ic = new LinearLayout(this);
                    ic.setOrientation(LinearLayout.VERTICAL);
                    ic.setPadding(dp(8), 0, dp(6), 0);
                    TextView pn = new TextView(this);
                    pn.setText((sel ? "✅ " : "") + p.name);
                    pn.setTextSize(13f);
                    pn.setTypeface(null, Typeface.BOLD);
                    pn.setTextColor(txtPrimary(d));
                    ic.addView(pn);

                    TextView ps = new TextView(this);
                    ps.setText(p.city + " • " + p.protocol + " • " + p.simCarrier);
                    ps.setTextSize(11f);
                    ps.setTextColor(txtSecondary(d));
                    ic.addView(ps);
                    row.addView(ic, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

                    TextView pw = new TextView(this);
                    int pv = p.powerPercent <= 0 ? 96 : p.powerPercent;
                    pw.setText("⚡ " + pv + "%");
                    pw.setTextSize(11.5f);
                    pw.setTypeface(null, Typeface.BOLD);
                    pw.setTextColor(Color.parseColor("#10B981"));
                    pw.setPadding(dp(6), dp(4), dp(8), dp(4));
                    row.addView(pw);

                    TextView ed = new TextView(this);
                    ed.setText("✏️");
                    ed.setTextSize(14f);
                    ed.setPadding(dp(8), dp(4), dp(8), dp(4));
                    GradientDrawable eb = new GradientDrawable();
                    eb.setColor(bgCardInner(d));
                    eb.setCornerRadius(dp(8));
                    eb.setStroke(dp(1), borderCard(d));
                    ed.setBackground(eb);
                    ed.setOnClickListener(v -> showAddOrEditVpnDialog(p, false));
                    row.addView(ed);

                    row.setOnClickListener(v -> {
                        CloneMetadataStore.setActiveVpnCategory(this, p.category);
                        CloneMetadataStore.setActiveVpnId(this, p.id);
                        if (CloneMetadataStore.isVpnAutoSyncEnabled(this)) {
                            CloneMetadataStore.applyVpnProfileToEnvironment(this, p);
                        }
                        if (CloneMetadataStore.isVpnConnected(this)) startVaultVpnService();
                        Toast.makeText(this, "سرور انتخاب شد: " + p.name, Toast.LENGTH_SHORT).show();
                        switchTab(4);
                    });
                    cont.addView(row);
                }
            }
            list.addView(cont);
        }

        Button ag = makePrimaryButton("➕ افزودن دسته/کشور جدید یا انتخاب از ۱۲ سرور رایگان");
        ag.setOnClickListener(v -> showAddOrEditVpnDialog(null, false));
        list.addView(ag);
        box.addView(list);

        LinearLayout sync = createCard(d, "🛡️ تنظیمات همگام‌سازی خودکار موقعیت و تست شبکه");
        Switch sw = new Switch(this);
        sw.setText("همگام‌سازی خودکار GPS، منطقه زمانی و سیم‌کارت با کشورِ سرور VPN");
        sw.setTextColor(txtPrimary(d));
        sw.setChecked(CloneMetadataStore.isVpnAutoSyncEnabled(this));
        sw.setOnCheckedChangeListener((b, c) -> CloneMetadataStore.setVpnAutoSyncEnabled(this, c));
        sync.addView(sw);

        Button ti = makeSecondaryButton("🔍 تست زنده آی‌پی خروجی و بررسی Failover خودکار", d);
        ti.setOnClickListener(v -> runRealOutboundIpVerification(fin));
        sync.addView(ti);
        box.addView(sync);

        sv.addView(box);
        return sv;
    }

    private void showAddOrEditVpnDialog(final CloneMetadataStore.VpnProfile ex, final boolean isTpl) {
        final boolean isEdit = (ex != null && !isTpl && ex.id != null && !ex.id.isEmpty());
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(isEdit ? "✏️ ویرایش پروفایل VPN" : "➕ ساخت یا انتخاب پروفایل VPN");

        ScrollView sv = new ScrollView(this);
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(dp(18), dp(12), dp(18), dp(8));

        final List<CloneMetadataStore.VpnProfile> free = CloneMetadataStore.getFreeBuiltInPresets();
        String[] pt = new String[free.size() + 1];
        pt[0] = "— پر کردن سریع از ۱۲ سرور رایگان آماده —";
        for (int i = 0; i < free.size(); i++) {
            CloneMetadataStore.VpnProfile fp = free.get(i);
            pt[i + 1] = fp.flagEmoji + " " + fp.name + " (⚡" + fp.powerPercent + "%)";
        }
        Spinner sp = new Spinner(this);
        sp.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, pt));
        l.addView(sp);

        final EditText etCat = new EditText(this);
        etCat.setHint("نام دسته کشور (مثلاً: ایالات متحده (United States))");
        etCat.setText(ex != null ? ex.category : CloneMetadataStore.getActiveVpnCategory(this));
        l.addView(etCat);

        final EditText etFlag = new EditText(this);
        etFlag.setHint("پرچم کشور (مثلاً 🇺🇸 یا 🇩🇪)");
        etFlag.setText(ex != null ? ex.flagEmoji : "🇺🇸");
        l.addView(etFlag);

        final EditText etName = new EditText(this);
        etName.setHint("نام سرور (مثلاً US New York • نود ۵)");
        if (ex != null && ex.name != null) etName.setText(ex.name);
        l.addView(etName);

        final EditText etHost = new EditText(this);
        etHost.setHint("آدرس سرور یا Host/IP");
        if (ex != null && ex.serverHost != null) etHost.setText(ex.serverHost);
        l.addView(etHost);

        final EditText etPort = new EditText(this);
        etPort.setHint("پورت (مثلاً 443)");
        etPort.setInputType(InputType.TYPE_CLASS_NUMBER);
        etPort.setText(ex != null ? String.valueOf(ex.serverPort) : "443");
        l.addView(etPort);

        final EditText etPow = new EditText(this);
        etPow.setHint("قدرت سرور به درصد (مثلاً 98)");
        etPow.setInputType(InputType.TYPE_CLASS_NUMBER);
        etPow.setText(ex != null ? String.valueOf(ex.powerPercent) : "98");
        l.addView(etPow);

        final EditText etCity = new EditText(this);
        etCity.setHint("شهر (مثلاً New York)");
        etCity.setText(ex != null ? ex.city : "New York");
        l.addView(etCity);

        final EditText etCc = new EditText(this);
        etCc.setHint("کد کشور دوحرفی (مثلاً US یا DE)");
        etCc.setText(ex != null ? ex.countryCode : "US");
        l.addView(etCc);

        final EditText etTz = new EditText(this);
        etTz.setHint("منطقه زمانی (مثلاً America/New_York)");
        etTz.setText(ex != null ? ex.timezone : "America/New_York");
        l.addView(etTz);

        final EditText etCar = new EditText(this);
        etCar.setHint("اپراتور سیم‌کارت (مثلاً T-Mobile USA)");
        etCar.setText(ex != null ? ex.simCarrier : "T-Mobile USA");
        l.addView(etCar);

        final EditText etMc = new EditText(this);
        etMc.setHint("کد MCC/MNC (مثلاً 310260)");
        etMc.setText(ex != null ? ex.simMccMnc : "310260");
        l.addView(etMc);

        final EditText etLa = new EditText(this);
        etLa.setHint("عرض جغرافیایی (Latitude)");
        etLa.setText(ex != null ? String.valueOf(ex.latitude) : "40.7128");
        l.addView(etLa);

        final EditText etLo = new EditText(this);
        etLo.setHint("طول جغرافیایی (Longitude)");
        etLo.setText(ex != null ? String.valueOf(ex.longitude) : "-74.0060");
        l.addView(etLo);

        sp.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(android.widget.AdapterView<?> p, View v, int pos, long id) {
                if (pos > 0) {
                    CloneMetadataStore.VpnProfile fp = free.get(pos - 1);
                    etCat.setText(fp.category);
                    etFlag.setText(fp.flagEmoji);
                    etName.setText(fp.name);
                    etHost.setText(fp.serverHost);
                    etPort.setText(String.valueOf(fp.serverPort));
                    etPow.setText(String.valueOf(fp.powerPercent));
                    etCity.setText(fp.city);
                    etCc.setText(fp.countryCode);
                    etTz.setText(fp.timezone);
                    etCar.setText(fp.simCarrier);
                    etMc.setText(fp.simMccMnc);
                    etLa.setText(String.valueOf(fp.latitude));
                    etLo.setText(String.valueOf(fp.longitude));
                }
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> p) {}
        });

        sv.addView(l);
        b.setView(sv);
        b.setPositiveButton("ذخیره", (dd, w) -> {
            List<CloneMetadataStore.VpnProfile> list = CloneMetadataStore.getVpnProfiles(this);
            CloneMetadataStore.VpnProfile p = isEdit ? ex : new CloneMetadataStore.VpnProfile();
            if (!isEdit) p.id = "custom_" + System.currentTimeMillis();
            p.category = etCat.getText().toString().trim().isEmpty() ? "ایالات متحده (United States)" : etCat.getText().toString().trim();
            p.flagEmoji = etFlag.getText().toString().trim().isEmpty() ? "🇺🇸" : etFlag.getText().toString().trim();
            p.name = etName.getText().toString().trim().isEmpty() ? "Custom VPN" : etName.getText().toString().trim();
            p.serverHost = etHost.getText().toString().trim().isEmpty() ? "us-ny1.freevault.net" : etHost.getText().toString().trim();
            try {
                p.serverPort = Integer.parseInt(etPort.getText().toString().trim());
            } catch (Throwable ignored) {
                p.serverPort = 443;
            }
            try {
                p.powerPercent = Integer.parseInt(etPow.getText().toString().trim());
            } catch (Throwable ignored) {
                p.powerPercent = 98;
            }
            p.city = etCity.getText().toString().trim().isEmpty() ? "New York" : etCity.getText().toString().trim();
            p.countryCode = etCc.getText().toString().trim().isEmpty() ? "US" : etCc.getText().toString().trim().toUpperCase(Locale.US);
            p.protocol = "SOCKS5/TLS";
            p.dnsServer = "1.1.1.1";
            p.timezone = etTz.getText().toString().trim();
            p.simCarrier = etCar.getText().toString().trim();
            p.simMccMnc = etMc.getText().toString().trim();
            try {
                p.latitude = Double.parseDouble(etLa.getText().toString().trim());
                p.longitude = Double.parseDouble(etLo.getText().toString().trim());
            } catch (Throwable ignored) {
                p.latitude = 40.7128;
                p.longitude = -74.0060;
            }
            if (isEdit) {
                for (int i = 0; i < list.size(); i++) {
                    if (list.get(i).id.equals(p.id)) {
                        list.set(i, p);
                        break;
                    }
                }
            } else {
                list.add(p);
            }
            CloneMetadataStore.saveVpnProfiles(this, list);
            CloneMetadataStore.setActiveVpnCategory(this, p.category);
            CloneMetadataStore.setCategoryExpanded(this, p.category, true);
            CloneMetadataStore.setActiveVpnId(this, p.id);
            switchTab(4);
        });
        if (isEdit) {
            b.setNeutralButton("حذف سرور", (dd, w) -> {
                List<CloneMetadataStore.VpnProfile> list = CloneMetadataStore.getVpnProfiles(this);
                if (list.size() > 1) {
                    Iterator<CloneMetadataStore.VpnProfile> it = list.iterator();
                    while (it.hasNext()) {
                        if (it.next().id.equals(ex.id)) {
                            it.remove();
                            break;
                        }
                    }
                    CloneMetadataStore.saveVpnProfiles(this, list);
                    switchTab(4);
                }
            });
        }
        b.setNegativeButton("انصراف", null);
        b.show();
    }

    private void startVaultVpnService() {
        Intent i = new Intent(this, VaultVpnService.class);
        i.setAction(VaultVpnService.ACTION_CONNECT);
        startService(i);
        CloneMetadataStore.setVpnConnected(this, true);
    }

    private void stopVaultVpnService() {
        Intent i = new Intent(this, VaultVpnService.class);
        i.setAction(VaultVpnService.ACTION_DISCONNECT);
        startService(i);
        CloneMetadataStore.setVpnConnected(this, false);
    }

    private void runRealOutboundIpVerification(final CloneMetadataStore.VpnProfile prof) {
        Toast.makeText(this, "در حال بررسی شبکه و وضعیت خوشه...", Toast.LENGTH_SHORT).show();
        new Thread(() -> {
            String msg;
            try {
                ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
                boolean tun = false;
                if (cm != null && android.os.Build.VERSION.SDK_INT >= 23) {
                    Network an = cm.getActiveNetwork();
                    if (an != null) {
                        NetworkCapabilities caps = cm.getNetworkCapabilities(an);
                        if (caps != null && caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) tun = true;
                    }
                }
                URL url = new URL("https://ipwho.is/");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);
                BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) sb.append(line);
                br.close();
                JSONObject j = new JSONObject(sb.toString());
                String ip = j.optString("ip", "نامشخص");
                String co = j.optString("country", "نامشخص");
                String ci = j.optString("city", "نامشخص");
                CloneMetadataStore.EffectiveIdentity e = CloneMetadataStore.resolveEffectiveIdentity(
                        this,
                        CloneMetadataStore.getLastActivePkg(this),
                        CloneMetadataStore.getLastActiveUserId(this)
                );
                msg = "🌐 گزارش وضعیت شبکه و هویت:\\n\\n• رابط تونل (tun0): " + (tun ? "✅ فعال" : "⚪ غیرفعال")
                        + "\\n• آی‌پی خروجی شبکه: " + ip + " (" + ci + ", " + co + ")"
                        + "\\n\\n📱 هویت تزریق‌شده به اپ‌ها:\\n• منبع فعال: " + e.prioritySource
                        + "\\n• دستگاه: " + e.brandModelDisplay
                        + "\\n• سیم‌کارت: " + e.simCarrier + " (" + e.simMccMnc + ")"
                        + "\\n• مختصات GPS: " + e.latitude + ", " + e.longitude;
            } catch (Throwable ex) {
                if (CloneMetadataStore.isClusterAutoRotateEnabled(this)) {
                    CloneMetadataStore.VpnProfile r = CloneMetadataStore.rotateToNextSiblingInCluster(this);
                    msg = "🔄 سوییچ خودکار خوشه فعال شد!\\nبه دلیل عدم پاسخ نود قبلی، ارتباط بدون قطعی به سرور هم‌خانواده منتقل شد:\\n⬅️ " + (r != null ? r.name : "");
                } else {
                    msg = "⚠️ خطا در استعلام آی‌پی: " + ex.getMessage();
                }
            }
            final String fm = msg;
            runOnUiThread(() -> new AlertDialog.Builder(this)
                    .setTitle("گزارش کامل شبکه و هویت")
                    .setMessage(fm)
                    .setPositiveButton("متوجه شدم", (d, w) -> switchTab(4))
                    .show());
        }).start();
    }

    private View buildSessionAndGuideView() {
        boolean d = ThemeHelper.isDarkMode(this);
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(16), dp(16), dp(96));

        String lp = CloneMetadataStore.getLastActivePkg(this);
        int lu = CloneMetadataStore.getLastActiveUserId(this);
        CloneMetadataStore.EffectiveIdentity e = CloneMetadataStore.resolveEffectiveIdentity(
                this, lp.isEmpty() ? "__global__" : lp, lu
        );
        boolean vc = CloneMetadataStore.isVpnConnected(this);

        LinearLayout card = createCard(d, "🛡️ مانیتورینگ زنده نشست (اعمال‌شده در پردازش برنامه‌ها)");
        String code = e.model.replaceAll("[^A-Za-z0-9]", "").toLowerCase(Locale.US);
        if (code.isEmpty()) code = "s24ultra";
        String bl = e.brand.replaceAll("[^A-Za-z0-9]", "").toLowerCase(Locale.US);
        String fp = bl + "/" + code + "ue/" + code + ":14/UP1A.231005.007/S928U1UES1AXB4:user/release-keys";

        String[][] rows = new String[][]{
                {"آخرین برنامه اجراشده در نشست", lp.isEmpty() ? "آماده اجرای برنامه" : lp + " (" + CloneMetadataStore.getSpaceDisplayName(this, lu) + ")"},
                {"اولویت فعال در حافظه", e.prioritySource},
                {"نام دستگاه در نشست‌ها (Build.MODEL)", e.brandModelDisplay},
                {"اثر انگشت سیستم (Device Fingerprint)", fp},
                {"موقعیت مکانی و کشور", e.regionLabel},
                {"منطقه زمانی (Timezone)", e.timezone},
                {"سیم‌کارت مجازی (Carrier & MCC/MNC)", e.simCarrier + " (" + e.simMccMnc + " / " + e.simCountryIso + ")"},
                {"مختصات GPS تزریق‌شده", String.format(Locale.US, "%.4f, %.4f", e.latitude, e.longitude)},
                {"وضعیت تونل VPN", vc ? "متصل (تونل فعال)" : "غیرفعال (هویت مجازی همچنان فعال)"},
                {"وضعیت اطلاعات گوشی واقعی شما", "مسدود شده (Anti-Host Leak = 100%)"}
        };
        for (String[] r : rows) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(dp(10), dp(8), dp(10), dp(8));
            row.setBackground(makeInnerBox(d, 10));
            LinearLayout.LayoutParams rlp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            rlp.bottomMargin = dp(6);
            row.setLayoutParams(rlp);

            TextView k = new TextView(this);
            k.setText("• " + r[0]);
            k.setTextColor(Color.parseColor("#0284C7"));
            k.setTextSize(12f);
            k.setTypeface(null, Typeface.BOLD);

            TextView v = new TextView(this);
            v.setText(r[1]);
            v.setTextColor(txtPrimary(d));
            v.setTextSize(12.5f);
            v.setPadding(0, dp(2), 0, 0);
            row.addView(k);
            row.addView(v);
            card.addView(row);
        }

        Button bs = makePrimaryButton("🔄 بازنویسی فوری هویت در تمام پردازش‌ها");
        bs.setOnClickListener(v -> {
            VirtualHookManager.applyEffectiveHookToSystem(this, lp, lu);
            Toast.makeText(this, "هویت در حافظه و پردازش‌ها قفل شد", Toast.LENGTH_SHORT).show();
            switchTab(5);
        });
        card.addView(bs);
        box.addView(card);
        sv.addView(box);
        return sv;
    }

    private View buildSettingsView() {
        boolean d = ThemeHelper.isDarkMode(this);
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(16), dp(16), dp(96));

        LinearLayout dc = createCard(d, "🎭 تغییر آیکون و نام برنامه (استتار هوشمند روی گوشی)");
        TextView cur = new TextView(this);
        cur.setText("ظاهر فعلی برنامه: " + CloneMetadataStore.getDisguiseTitle(this) + "\\nبا انتخاب هر گزینه، آیکون و نام استتاری روی صفحه اصلی گوشی ثبت می‌شود تا هیچ‌کس متوجه وجود برنامه نشود.");
        cur.setTextSize(12.5f);
        cur.setTextColor(txtSecondary(d));
        cur.setPadding(0, 0, 0, dp(10));
        dc.addView(cur);

        String[][] modes = new String[][]{
                {"default", "🛡️ پیش‌فرض (VeyraVault)"},
                {"calculator", "🧮 ماشین‌حساب مهندسی (استتار کامل)"},
                {"notes", "📝 یادداشت و تقویم روزانه"},
                {"battery", "🔋 بهینه‌ساز هوشمند باتری"},
                {"weather", "⛅ هواشناسی دقیق"}
        };
        String cm = CloneMetadataStore.getActiveDisguiseMode(this);
        for (final String[] m : modes) {
            boolean sel = m[0].equals(cm);
            Button bm = sel ? makePrimaryButton("✅ " + m[1]) : makeSecondaryButton(m[1], d);
            bm.setOnClickListener(v -> {
                CloneMetadataStore.applyDisguiseMode(this, m[0]);
                setTitle(CloneMetadataStore.getDisguiseTitle(this));
                Toast.makeText(this, "آیکون و نام برنامه تغییر یافت به: " + m[1], Toast.LENGTH_LONG).show();
                switchTab(6);
            });
            dc.addView(bm);
        }
        box.addView(dc);

        LinearLayout tc = createCard(d, "🌓 ظاهر برنامه (حالت روز روشن / حالت شب تیره)");
        Button bt = makePrimaryButton(d ? "☀️ تغییر به حالت روز (کادرهای روشن با حاشیه مشخص)" : "🌙 تغییر به حالت شب (تم تیره حرفه‌ای)");
        bt.setOnClickListener(v -> {
            ThemeHelper.toggleTheme(this);
            recreate();
        });
        tc.addView(bt);
        box.addView(tc);

        LinearLayout ec = createCard(d, "🌍 تنظیمات کلی دستگاه، مکان و سیم‌کارت (اولویت ۳)");
        Button bg = makeSecondaryButton("تغییر مدل گوشی، منطقه زمانی و سیم‌کارت پیش‌فرض", d);
        bg.setOnClickListener(v -> startActivity(new Intent(this, GlobalEnvironmentActivity.class)));
        ec.addView(bg);
        Button bm2 = makeSecondaryButton("تنظیم دقیق مختصات جغرافیایی (GPS)", d);
        bm2.setOnClickListener(v -> startActivity(new Intent(this, SetLocationActivity.class)));
        ec.addView(bm2);
        box.addView(ec);

        LinearLayout sc = createCard(d, "🔐 امنیت، قفل ورود و نشانگر اعلان‌ها");
        Button bs = makeSecondaryButton("مدیریت رمز عبور، پین، الگو و حفاظت عدم حذف", d);
        bs.setOnClickListener(v -> startActivity(new Intent(this, SecuritySettingsActivity.class)));
        sc.addView(bs);
        Button bn = makeSecondaryButton("🔔 فعال‌سازی شمارنده اعلان برنامه‌ها (۱ تا ۹۹ و ∞)", d);
        bn.setOnClickListener(v -> {
            try {
                startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
            } catch (Throwable ex) {
                Toast.makeText(this, "از تنظیمات گوشی بخش Notification Access را فعال کنید", Toast.LENGTH_LONG).show();
            }
        });
        sc.addView(bn);
        box.addView(sc);

        LinearLayout ic = createCard(d, "📘 آموزش کامل و درباره سازنده");
        Button bf = makePrimaryButton("📖 راهنمای جامع کار با VeyraVault");
        bf.setOnClickListener(v -> startActivity(new Intent(this, GuideActivity.class)));
        ic.addView(bf);
        Button ba = makeSecondaryButton("ℹ️ درباره ما و مشخصات نسخه", d);
        ba.setOnClickListener(v -> startActivity(new Intent(this, AboutActivity.class)));
        ic.addView(ba);
        box.addView(ic);

        sv.addView(box);
        return sv;
    }

    private LinearLayout createCard(boolean d, String t) {
        LinearLayout c = new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setPadding(dp(14), dp(14), dp(14), dp(14));
        c.setBackground(makeSurfaceBox(d, 16, 0));

        TextView tv = new TextView(this);
        tv.setText(t);
        tv.setTextSize(14.5f);
        tv.setTypeface(null, Typeface.BOLD);
        tv.setTextColor(txtPrimary(d));
        tv.setPadding(0, 0, 0, dp(10));
        c.addView(tv);

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = dp(14);
        c.setLayoutParams(lp);
        return c;
    }

    private Button makePrimaryButton(String t) {
        Button b = new Button(this);
        b.setText(t);
        b.setAllCaps(false);
        b.setTextColor(Color.WHITE);
        b.setTextSize(13f);
        b.setTypeface(null, Typeface.BOLD);
        GradientDrawable g = new GradientDrawable();
        g.setColor(Color.parseColor("#0284C7"));
        g.setCornerRadius(dp(12));
        b.setBackground(g);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(6);
        b.setLayoutParams(lp);
        return b;
    }

    private Button makeSecondaryButton(String t, boolean d) {
        Button b = new Button(this);
        b.setText(t);
        b.setAllCaps(false);
        b.setTextColor(txtPrimary(d));
        b.setTextSize(12.5f);
        GradientDrawable g = new GradientDrawable();
        g.setColor(bgCardInner(d));
        g.setCornerRadius(dp(10));
        g.setStroke(dp(1), borderCard(d));
        b.setBackground(g);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(6);
        b.setLayoutParams(lp);
        return b;
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/MainActivity.java"), MAIN_ACTIVITY)

print("[PART2] Upgrade V3 Part 2 completed successfully.")
