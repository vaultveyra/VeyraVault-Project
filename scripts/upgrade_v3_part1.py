#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Upgrade Script - Part 1
Core Virtualization Engine, Independent APK Vault, Split-APK Native Libs,
Apple/iPhone Profiles, Region (City, Country) + IP/Proxy Shield,
Dual Lock (PIN + Pattern with Priority & Fallback), Solar Hijri Clock & SVG Icons.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write_file(rel_path, content):
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[v3-Part1] Updated: {rel_path}")

def apply_part1():
    # 1. SVG Vector Drawables for Bottom Navigation & Top Quick Lock
    write_file("app/src/main/res/drawable/ic_nav_dashboard.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="22dp" android:height="22dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF2563EB"
        android:pathData="M3,13h8V3H3v10zm0,8h8v-6H3v6zm10,0h8V11h-8v10zm0-18v6h8V3h-8z"/>
</vector>
""")

    write_file("app/src/main/res/drawable/ic_nav_spaces.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="22dp" android:height="22dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF2563EB"
        android:pathData="M4,8h4V4H4v4zm6,12h4v-4h-4v4zm-6,0h4v-4H4v4zm0-6h4v-4H4v4zm6,0h4v-4h-4v4zm6-10v4h4V4h-4zm-6,4h4V4h-4v4zm6,6h4v-4h-4v4zm0,6h4v-4h-4v4z"/>
</vector>
""")

    write_file("app/src/main/res/drawable/ic_nav_add.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
</vector>
""")

    write_file("app/src/main/res/drawable/ic_nav_guide.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="22dp" android:height="22dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF2563EB"
        android:pathData="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zm1,17h-2v-2h2v2zm2.07,-7.75l-0.9,0.92C13.45,12.9 13,13.5 13,15h-2v-0.5c0,-1.1 0.45,-2.1 1.17,-2.83l1.24,-1.26c0.37,-0.36 0.59,-0.86 0.59,-1.41 0,-1.1 -0.9,-2 -2,-2s-2,0.9 -2,2H8c0,-2.21 1.79,-4 4,-4s4,1.79 4,4c0,0.88 -0.36,1.68 -0.93,2.25z"/>
</vector>
""")

    write_file("app/src/main/res/drawable/ic_nav_settings.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="22dp" android:height="22dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF2563EB"
        android:pathData="M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"/>
</vector>
""")

    write_file("app/src/main/res/drawable/ic_quick_lock.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="18dp" android:height="18dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF1E40AF"
        android:pathData="M18,8h-1V6c0,-2.76 -2.24,-5 -5,-5S7,3.24 7,6v2H6c-1.1,0 -2,0.9 -2,2v10c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V10c0,-1.1 -0.9,-2 -2,-2zM12,17c-1.1,0 -2,-0.9 -2,-2s0.9,-2 2,-2 2,0.9 2,2 -0.9,2 -2,2zM15.1,8H8.9V6c0,-1.71 1.39,-3.1 3.1,-3.1 1.71,0 3.1,1.39 3.1,3.1v2z"/>
</vector>
""")

    # 2. Solar Hijri (Jalali) & World Clock Utility for Stealth Dashboard
    write_file("app/src/main/java/com/veyravault/space/util/JalaliClockUtil.java", """
package com.veyravault.space.util;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

public class JalaliClockUtil {

    public static String getTehranTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("Asia/Tehran"));
        return toPersianDigits(sdf.format(new Date()));
    }

    public static String getTehranJalaliDate() {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Tehran"));
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int[] j = gregorianToJalali(gy, gm, gd);
        String[] months = {
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        };
        String mName = (j[1] >= 1 && j[1] <= 12) ? months[j[1] - 1] : String.valueOf(j[1]);
        String formatted = String.format(Locale.US, "%04d/%02d/%02d (%s %s)", j[0], j[1], j[2], j[2], mName);
        return toPersianDigits(formatted);
    }

    public static String getNewYorkTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String getNewYorkGregorianDate() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd (EEE, MMM d)", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static int[] gregorianToJalali(int gy, int gm, int gd) {
        int[] g_d_m = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
        int gy2 = (gm > 2) ? (gy + 1) : gy;
        int days = 355666 + (365 * gy) + ((gy2 + 3) / 4) - ((gy2 + 99) / 100) + ((gy2 + 399) / 400) + gd + g_d_m[gm - 1];
        int jy = -1595 + (33 * (days / 12053));
        days %= 12053;
        jy += 4 * (days / 1461);
        days %= 1461;
        if (days > 365) {
            jy += (days - 1) / 365;
            days = (days - 1) % 365;
        }
        int jm = (days < 186) ? 1 + (days / 31) : 7 + ((days - 186) / 30);
        int jd = 1 + ((days < 186) ? (days % 31) : ((days - 186) % 30));
        return new int[]{jy, jm, jd};
    }

    public static String toPersianDigits(String s) {
        if (s == null) return "";
        char[] p = {'۰','۱','۲','۳','۴','۵','۶','۷','۸','۹'};
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c >= '0' && c <= '9') sb.append(p[c - '0']);
            else sb.append(c);
        }
        return sb.toString();
    }
}
""")

    # 3. Upgraded CloneMetadataStore: Space Renaming + Independent Vault Registry + Region (City, Country) + IP/Proxy
    write_file("app/src/main/java/com/veyravault/space/core/CloneMetadataStore.java", """
package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.HashSet;
import java.util.Set;

public class CloneMetadataStore {
    private static final String PREF = "veyravault_clone_meta_v3";

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    private static String key(String pkg, int userId, String suffix) {
        return pkg + "_u" + userId + "_" + suffix;
    }

    // --- Independent Clone Registry (Survives Host App Uninstall) ---
    public static void registerClonedApp(Context ctx, String pkg, int userId) {
        SharedPreferences sp = prefs(ctx);
        Set<String> all = new HashSet<>(sp.getStringSet("registered_clones_u" + userId, new HashSet<String>()));
        all.add(pkg);
        sp.edit().putStringSet("registered_clones_u" + userId, all).apply();
    }

    public static void unregisterClonedApp(Context ctx, String pkg, int userId) {
        SharedPreferences sp = prefs(ctx);
        Set<String> all = new HashSet<>(sp.getStringSet("registered_clones_u" + userId, new HashSet<String>()));
        all.remove(pkg);
        sp.edit().putStringSet("registered_clones_u" + userId, all).apply();
    }

    public static Set<String> getRegisteredClones(Context ctx, int userId) {
        return new HashSet<>(prefs(ctx).getStringSet("registered_clones_u" + userId, new HashSet<String>()));
    }

    public static void saveAppLabel(Context ctx, String pkg, String label) {
        if (label != null && !label.trim().isEmpty()) {
            prefs(ctx).edit().putString("cached_label_" + pkg, label.trim()).apply();
        }
    }

    public static String getCachedAppLabel(Context ctx, String pkg) {
        return prefs(ctx).getString("cached_label_" + pkg, pkg);
    }

    // --- Space Custom Naming ---
    public static void setSpaceCustomName(Context ctx, int userId, String customName) {
        prefs(ctx).edit().putString("space_custom_name_" + userId, customName == null ? "" : customName.trim()).apply();
    }

    public static String getSpaceCustomName(Context ctx, int userId) {
        return prefs(ctx).getString("space_custom_name_" + userId, "");
    }

    public static String getSpaceDisplayTitle(Context ctx, int userId, String defaultPrefix) {
        String custom = getSpaceCustomName(ctx, userId);
        if (custom != null && !custom.trim().isEmpty()) {
            return custom.trim();
        }
        return defaultPrefix + " " + (userId + 1);
    }

    // --- Per-Clone Custom Alias ---
    public static void setAlias(Context ctx, String pkg, int userId, String alias) {
        prefs(ctx).edit().putString(key(pkg, userId, "alias"), alias == null ? "" : alias.trim()).apply();
    }

    public static String getAlias(Context ctx, String pkg, int userId, String defaultName) {
        String val = prefs(ctx).getString(key(pkg, userId, "alias"), "");
        return (val == null || val.isEmpty()) ? defaultName : val;
    }

    // --- Per-Clone Mock Location & Region (City, Country + Coordinates) with Global Fallback ---
    public static void setMockLocationWithRegion(Context ctx, String pkg, int userId, double lat, double lon, String cityCountry, String timezoneId) {
        prefs(ctx).edit()
            .putBoolean(key(pkg, userId, "loc_enabled"), true)
            .putString(key(pkg, userId, "lat"), String.valueOf(lat))
            .putString(key(pkg, userId, "lon"), String.valueOf(lon))
            .putString(key(pkg, userId, "city_country"), cityCountry == null ? "Falkenstein, Germany" : cityCountry.trim())
            .putString(key(pkg, userId, "tz"), timezoneId == null ? "Europe/Berlin" : timezoneId.trim())
            .apply();
    }

    public static void setMockLocation(Context ctx, String pkg, int userId, double lat, double lon) {
        String existingRegion = prefs(ctx).getString(key(pkg, userId, "city_country"), "");
        if (existingRegion == null || existingRegion.isEmpty()) {
            existingRegion = getGlobalRegionLabel(ctx);
        }
        setMockLocationWithRegion(ctx, pkg, userId, lat, lon, existingRegion, getGlobalTimezone(ctx));
    }

    public static void clearMockLocation(Context ctx, String pkg, int userId) {
        prefs(ctx).edit()
            .putBoolean(key(pkg, userId, "loc_enabled"), false)
            .remove(key(pkg, userId, "lat"))
            .remove(key(pkg, userId, "lon"))
            .remove(key(pkg, userId, "city_country"))
            .remove(key(pkg, userId, "tz"))
            .apply();
    }

    public static boolean hasMockLocation(Context ctx, String pkg, int userId) {
        return prefs(ctx).getBoolean(key(pkg, userId, "loc_enabled"), false);
    }

    public static double[] getMockLocation(Context ctx, String pkg, int userId) {
        if (hasMockLocation(ctx, pkg, userId)) {
            try {
                double lat = Double.parseDouble(prefs(ctx).getString(key(pkg, userId, "lat"), "50.4779"));
                double lon = Double.parseDouble(prefs(ctx).getString(key(pkg, userId, "lon"), "12.3713"));
                return new double[]{lat, lon};
            } catch (Exception e) {
                return new double[]{50.4779, 12.3713};
            }
        }
        // Fallback to Global Coordinates if Global Spoof or Global Location is active
        return getGlobalCoordinates(ctx);
    }

    public static String getEffectiveRegionLabel(Context ctx, String pkg, int userId) {
        if (hasMockLocation(ctx, pkg, userId)) {
            String r = prefs(ctx).getString(key(pkg, userId, "city_country"), "");
            if (r != null && !r.isEmpty()) return r;
        }
        return getGlobalRegionLabel(ctx);
    }

    public static String getEffectiveTimezone(Context ctx, String pkg, int userId) {
        if (hasMockLocation(ctx, pkg, userId)) {
            String tz = prefs(ctx).getString(key(pkg, userId, "tz"), "");
            if (tz != null && !tz.isEmpty()) return tz;
        }
        return getGlobalTimezone(ctx);
    }

    public static String getLocationSummary(Context ctx, String pkg, int userId, String noLocText) {
        if (hasMockLocation(ctx, pkg, userId)) {
            double[] c = getMockLocation(ctx, pkg, userId);
            String reg = getEffectiveRegionLabel(ctx, pkg, userId);
            return String.format(java.util.Locale.US, "📍 %s (%.4f, %.4f) [اختصاصی اپ]", reg, c[0], c[1]);
        }
        String globalReg = getGlobalRegionLabel(ctx);
        double[] gc = getGlobalCoordinates(ctx);
        return String.format(java.util.Locale.US, "🌐 %s (%.4f, %.4f) [سراسری]", globalReg, gc[0], gc[1]);
    }

    // --- Per-Clone Custom Device Identity (Priority 1 over Global) ---
    public static void setCustomDeviceIdentity(Context ctx, String pkg, int userId, String brand, String model, String deviceCode) {
        prefs(ctx).edit()
            .putBoolean(key(pkg, userId, "dev_custom"), true)
            .putString(key(pkg, userId, "dev_brand"), brand == null ? "" : brand.trim())
            .putString(key(pkg, userId, "dev_model"), model == null ? "" : model.trim())
            .putString(key(pkg, userId, "dev_code"), deviceCode == null ? "" : deviceCode.trim())
            .apply();
    }

    public static void clearCustomDeviceIdentity(Context ctx, String pkg, int userId) {
        prefs(ctx).edit()
            .putBoolean(key(pkg, userId, "dev_custom"), false)
            .remove(key(pkg, userId, "dev_brand"))
            .remove(key(pkg, userId, "dev_model"))
            .remove(key(pkg, userId, "dev_code"))
            .apply();
    }

    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int userId) {
        return prefs(ctx).getBoolean(key(pkg, userId, "dev_custom"), false);
    }

    public static String[] getCustomDeviceIdentity(Context ctx, String pkg, int userId) {
        if (!hasCustomDeviceIdentity(ctx, pkg, userId)) return null;
        return new String[]{
            prefs(ctx).getString(key(pkg, userId, "dev_brand"), "Apple"),
            prefs(ctx).getString(key(pkg, userId, "dev_model"), "iPhone 16 Pro Max"),
            prefs(ctx).getString(key(pkg, userId, "dev_code"), "iPhone17,2")
        };
    }

    public static String getDeviceIdentitySummary(Context ctx, String pkg, int userId, String defaultLabel) {
        String[] custom = getCustomDeviceIdentity(ctx, pkg, userId);
        if (custom != null) {
            return "📱 " + custom[0] + " " + custom[1] + " (اولویت اختصاصی اپ)";
        }
        return "🌐 " + getGlobalDeviceSummary(ctx) + " (سراسری)";
    }

    // --- Tier 1: Global Device, Region (City, Country), Coordinates & Network Proxy ---
    public static void setGlobalDeviceSpoof(Context ctx, boolean enabled, String brand, String model,
                                            String device, String countryIso, String simOp, String simName) {
        prefs(ctx).edit()
            .putBoolean("global_spoof_enabled", enabled)
            .putString("global_brand", brand)
            .putString("global_model", model)
            .putString("global_device", device)
            .putString("global_country_iso", countryIso)
            .putString("global_sim_op", simOp)
            .putString("global_sim_name", simName)
            .apply();
    }

    public static void setGlobalRegionAndNetwork(Context ctx, String cityCountry, double lat, double lon,
                                                 String timezoneId, String proxyHost, int proxyPort, String virtualIp) {
        prefs(ctx).edit()
            .putString("global_city_country", cityCountry == null || cityCountry.isEmpty() ? "Falkenstein, Germany" : cityCountry.trim())
            .putString("global_lat", String.valueOf(lat))
            .putString("global_lon", String.valueOf(lon))
            .putString("global_tz", timezoneId == null || timezoneId.isEmpty() ? "Europe/Berlin" : timezoneId.trim())
            .putString("global_proxy_host", proxyHost == null ? "" : proxyHost.trim())
            .putInt("global_proxy_port", proxyPort)
            .putString("global_virtual_ip", virtualIp == null || virtualIp.isEmpty() ? "88.198.24.108" : virtualIp.trim())
            .apply();
    }

    public static String getGlobalRegionLabel(Context ctx) {
        return prefs(ctx).getString("global_city_country", "Falkenstein, Germany");
    }

    public static double[] getGlobalCoordinates(Context ctx) {
        try {
            double lat = Double.parseDouble(prefs(ctx).getString("global_lat", "50.4779"));
            double lon = Double.parseDouble(prefs(ctx).getString("global_lon", "12.3713"));
            return new double[]{lat, lon};
        } catch (Exception e) {
            return new double[]{50.4779, 12.3713};
        }
    }

    public static String getGlobalTimezone(Context ctx) {
        return prefs(ctx).getString("global_tz", "Europe/Berlin");
    }

    public static String getGlobalProxyHost(Context ctx) {
        return prefs(ctx).getString("global_proxy_host", "");
    }

    public static int getGlobalProxyPort(Context ctx) {
        return prefs(ctx).getInt("global_proxy_port", 0);
    }

    public static String getGlobalVirtualIp(Context ctx) {
        return prefs(ctx).getString("global_virtual_ip", "88.198.24.108");
    }

    public static boolean isGlobalDeviceSpoofEnabled(Context ctx) {
        return prefs(ctx).getBoolean("global_spoof_enabled", true);
    }

    public static String[] getGlobalDeviceSpoof(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        return new String[]{
            sp.getString("global_brand", "Samsung"),
            sp.getString("global_model", "SM-S928B (Galaxy S24 Ultra)"),
            sp.getString("global_device", "e3q"),
            sp.getString("global_country_iso", "de"),
            sp.getString("global_sim_op", "26201"),
            sp.getString("global_sim_name", "Telekom.de")
        };
    }

    public static String getGlobalDeviceSummary(Context ctx) {
        String[] g = getGlobalDeviceSpoof(ctx);
        return g[0] + " " + g[1];
    }

    public static void clearAllForClone(Context ctx, String pkg, int userId) {
        clearMockLocation(ctx, pkg, userId);
        clearCustomDeviceIdentity(ctx, pkg, userId);
        setAlias(ctx, pkg, userId, "");
        unregisterClonedApp(ctx, pkg, userId);
    }
}
""")

    # 4. Upgraded VirtualHookManager: Priority Order + Region/Timezone/Proxy + GMS Availability Bypass
    write_file("app/src/main/java/com/veyravault/space/core/VirtualHookManager.java", """
package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.SystemClock;

import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.net.InetAddress;
import java.util.Locale;
import java.util.TimeZone;

public class VirtualHookManager {
    private static final String PREF_NAME = "veyravault_hooks_prefs";
    private static final String KEY_MOCK_GPS_MASTER = "mock_gps_master_enabled";

    private static volatile double activeLat = 50.4779;
    private static volatile double activeLon = 12.3713;
    private static volatile boolean activeMockForCurrentLaunch = true;

    public static boolean isMockGpsEnabled(Context ctx) {
        return prefs(ctx).getBoolean(KEY_MOCK_GPS_MASTER, true);
    }

    public static void setMockGpsEnabled(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean(KEY_MOCK_GPS_MASTER, enabled).apply();
    }

    /**
     * Prepare hooks before launching a specific clone.
     * STRICT PRIORITY RULE:
     * 1) Per-Clone Custom Device Identity & Location override Global Settings.
     * 2) If Per-Clone is not set, Global Device Identity & Global Region (e.g. Falkenstein, Germany) apply.
     */
    public static void prepareForCloneLaunch(Context ctx, String pkg, int userId) {
        // 1. Determine Effective Location & Region
        double[] coords = CloneMetadataStore.getMockLocation(ctx, pkg, userId);
        activeLat = coords[0];
        activeLon = coords[1];
        activeMockForCurrentLaunch = isMockGpsEnabled(ctx) || CloneMetadataStore.hasMockLocation(ctx, pkg, userId);

        String effectiveTz = CloneMetadataStore.getEffectiveTimezone(ctx, pkg, userId);
        String effectiveRegion = CloneMetadataStore.getEffectiveRegionLabel(ctx, pkg, userId);

        // Apply TimeZone & Locale so sessions report the target region instead of host phone
        applyRegionAndNetworkShield(ctx, effectiveRegion, effectiveTz);

        // Apply GPS Location to BlackBox BLocationManager + In-process Hook
        applyBlackBoxVirtualLocation(pkg, userId, activeLat, activeLon, true);
        installLocationHook(ctx);

        // 2. Determine Effective Device Model (Per-App Priority -> Global Fallback)
        if (CloneMetadataStore.hasCustomDeviceIdentity(ctx, pkg, userId)) {
            String[] customDev = CloneMetadataStore.getCustomDeviceIdentity(ctx, pkg, userId);
            if (customDev != null) {
                spoofBuildFields(customDev[0], customDev[1], customDev[2], inferCountryIso(effectiveRegion));
                applyBlackBoxDeviceProfile(userId, customDev[0], customDev[1], customDev[2],
                        inferCountryIso(effectiveRegion), "26201", "Telekom.de");
            }
        } else {
            String[] globalDev = CloneMetadataStore.getGlobalDeviceSpoof(ctx);
            spoofBuildFields(globalDev[0], globalDev[1], globalDev[2], globalDev[3]);
            applyBlackBoxDeviceProfile(userId, globalDev[0], globalDev[1], globalDev[2],
                    globalDev[3], globalDev[4], globalDev[5]);
        }

        // 3. Bypass Google Play Services (GMS) check for YouTube, Viber, etc.
        installGmsAvailabilityBypass();
    }

    public static void applyGlobalEnvironmentToRuntime(Context ctx) {
        String[] g = CloneMetadataStore.getGlobalDeviceSpoof(ctx);
        spoofBuildFields(g[0], g[1], g[2], g[3]);
        String reg = CloneMetadataStore.getGlobalRegionLabel(ctx);
        String tz = CloneMetadataStore.getGlobalTimezone(ctx);
        applyRegionAndNetworkShield(ctx, reg, tz);
        for (int spaceId = 0; spaceId < 10; spaceId++) {
            applyBlackBoxDeviceProfile(spaceId, g[0], g[1], g[2], g[3], g[4], g[5]);
        }
    }

    private static String inferCountryIso(String cityCountry) {
        if (cityCountry == null) return "de";
        String low = cityCountry.toLowerCase(Locale.US);
        if (low.contains("germany") || low.contains("falkenstein") || low.contains("frankfurt")) return "de";
        if (low.contains("united states") || low.contains("usa") || low.contains("new york")) return "us";
        if (low.contains("united kingdom") || low.contains("london")) return "gb";
        if (low.contains("turkey") || low.contains("istanbul")) return "tr";
        if (low.contains("uae") || low.contains("dubai")) return "ae";
        if (low.contains("iran") || low.contains("tehran")) return "ir";
        if (low.contains("singapore")) return "sg";
        if (low.contains("japan") || low.contains("tokyo")) return "jp";
        return "de";
    }

    public static void applyRegionAndNetworkShield(Context ctx, String cityCountry, String timezoneId) {
        try {
            if (timezoneId != null && !timezoneId.isEmpty()) {
                TimeZone tz = TimeZone.getTimeZone(timezoneId);
                TimeZone.setDefault(tz);
                System.setProperty("user.timezone", timezoneId);
            }
            String iso = inferCountryIso(cityCountry);
            System.setProperty("user.region", iso.toUpperCase(Locale.US));
            System.setProperty("veyravault.active.region", cityCountry);

            // Apply SOCKS5 / HTTP Proxy tunnel if configured by user so real phone IP is never used
            String proxyHost = CloneMetadataStore.getGlobalProxyHost(ctx);
            int proxyPort = CloneMetadataStore.getGlobalProxyPort(ctx);
            if (proxyHost != null && !proxyHost.isEmpty() && proxyPort > 0) {
                System.setProperty("socksProxyHost", proxyHost);
                System.setProperty("socksProxyPort", String.valueOf(proxyPort));
                System.setProperty("http.proxyHost", proxyHost);
                System.setProperty("http.proxyPort", String.valueOf(proxyPort));
                System.setProperty("https.proxyHost", proxyHost);
                System.setProperty("https.proxyPort", String.valueOf(proxyPort));
            }
        } catch (Throwable ignored) {}
    }

    public static void installGmsAvailabilityBypass() {
        try {
            System.setProperty("veyravault.gms.bypass", "true");
            Class<?> gUtil = Class.forName("com.google.android.gms.common.GooglePlayServicesUtil");
            setStaticField(gUtil, "GOOGLE_PLAY_SERVICES_VERSION_CODE", 240000000);
        } catch (Throwable ignored) {}
    }

    public static void applyBlackBoxVirtualLocation(String pkg, int userId, double lat, double lon, boolean enable) {
        String[] managerClasses = {
            "top.niunaijun.blackbox.fake.frameworks.BLocationManager",
            "com.vcore.fake.frameworks.BLocationManager"
        };
        String[] entityClasses = {
            "top.niunaijun.blackbox.entity.location.BLocation",
            "com.vcore.entity.location.BLocation"
        };
        for (int i = 0; i < managerClasses.length; i++) {
            try {
                Class<?> mgrCls = Class.forName(managerClasses[i]);
                Object mgr = mgrCls.getDeclaredMethod("get").invoke(null);
                Method setPattern = mgrCls.getDeclaredMethod("setPattern", int.class, String.class, int.class);
                setPattern.invoke(mgr, userId, pkg, enable ? 2 : 0);
                if (enable) {
                    Class<?> locCls = Class.forName(entityClasses[i]);
                    Object bLoc = locCls.getDeclaredConstructor(double.class, double.class).newInstance(lat, lon);
                    Method setLocation = mgrCls.getDeclaredMethod("setLocation", int.class, String.class, locCls);
                    setLocation.invoke(mgr, userId, pkg, bLoc);
                }
                return;
            } catch (Throwable ignored) {}
        }
    }

    public static void installLocationHook(Context context) {
        try {
            LocationManager lm = (LocationManager) context.getSystemService(Context.LOCATION_SERVICE);
            if (lm == null) return;
            Field serviceField = LocationManager.class.getDeclaredField("mService");
            serviceField.setAccessible(true);
            final Object realService = serviceField.get(lm);
            if (realService == null || Proxy.isProxyClass(realService.getClass())) return;

            Class<?> iLocMgrClass = Class.forName("android.location.ILocationManager");
            Object proxy = Proxy.newProxyInstance(
                iLocMgrClass.getClassLoader(),
                new Class<?>[]{iLocMgrClass},
                new InvocationHandler() {
                    @Override
                    public Object invoke(Object proxyObj, Method method, Object[] args) throws Throwable {
                        String name = method.getName();
                        if ("getLastLocation".equals(name) || "getLastKnownLocation".equals(name)) {
                            return buildFakeLocation("gps", activeLat, activeLon);
                        }
                        return method.invoke(realService, args);
                    }
                }
            );
            serviceField.set(lm, proxy);
        } catch (Throwable ignored) {}
    }

    public static void spoofBuildFields(String brand, String model, String deviceCode, String countryIso) {
        try {
            String cleanModel = model;
            if (cleanModel != null && cleanModel.contains("(")) {
                cleanModel = cleanModel.substring(0, cleanModel.indexOf("(")).trim();
            }
            setStaticField(Build.class, "BRAND", brand);
            setStaticField(Build.class, "MANUFACTURER", brand);
            setStaticField(Build.class, "MODEL", cleanModel);
            setStaticField(Build.class, "PRODUCT", deviceCode);
            setStaticField(Build.class, "DEVICE", deviceCode);
            setStaticField(Build.class, "HARDWARE", deviceCode);
            String fp = brand.toLowerCase(Locale.US) + "/" + deviceCode + "/" + deviceCode
                    + ":14/UP1A.231005.007/S928BXXU1AWM9:user/release-keys";
            setStaticField(Build.class, "FINGERPRINT", fp);
        } catch (Throwable ignored) {}
    }

    private static void applyBlackBoxDeviceProfile(int userId, String brand, String model, String device,
                                                   String countryIso, String simOp, String simName) {
        String[] devMgrs = {
            "top.niunaijun.blackbox.fake.frameworks.BDeviceManager",
            "com.vcore.fake.frameworks.BDeviceManager"
        };
        for (String clsName : devMgrs) {
            try {
                Class<?> mgrCls = Class.forName(clsName);
                Object mgr = mgrCls.getDeclaredMethod("get").invoke(null);
                for (Method m : mgrCls.getDeclaredMethods()) {
                    if (m.getParameterTypes().length == 2 && m.getParameterTypes()[0] == int.class) {
                        Class<?> paramType = m.getParameterTypes()[1];
                        Object configObj = paramType.getDeclaredConstructor().newInstance();
                        setObjectFieldIfPresent(configObj, "BRAND", brand);
                        setObjectFieldIfPresent(configObj, "MANUFACTURER", brand);
                        setObjectFieldIfPresent(configObj, "MODEL", model);
                        setObjectFieldIfPresent(configObj, "PRODUCT", device);
                        setObjectFieldIfPresent(configObj, "DEVICE", device);
                        setObjectFieldIfPresent(configObj, "simCountryIso", countryIso);
                        setObjectFieldIfPresent(configObj, "networkCountryIso", countryIso);
                        setObjectFieldIfPresent(configObj, "simOperator", simOp);
                        setObjectFieldIfPresent(configObj, "simOperatorName", simName);
                        setObjectFieldIfPresent(configObj, "networkOperatorName", simName);
                        setObjectFieldIfPresent(configObj, "locale", countryIso);
                        m.setAccessible(true);
                        m.invoke(mgr, userId, configObj);
                        break;
                    }
                }
            } catch (Throwable ignored) {}
        }
    }

    private static void setObjectFieldIfPresent(Object target, String fieldName, Object value) {
        try {
            Field f = target.getClass().getDeclaredField(fieldName);
            f.setAccessible(true);
            f.set(target, value);
        } catch (Throwable ignored) {}
    }

    private static void setStaticField(Class<?> cls, String fieldName, Object value) {
        try {
            Field f = cls.getDeclaredField(fieldName);
            f.setAccessible(true);
            f.set(null, value);
        } catch (Throwable ignored) {}
    }

    private static Location buildFakeLocation(String provider, double lat, double lon) {
        Location loc = new Location(provider != null ? provider : LocationManager.GPS_PROVIDER);
        loc.setLatitude(lat);
        loc.setLongitude(lon);
        loc.setAltitude(35.0d);
        loc.setAccuracy(3.2f);
        loc.setSpeed(0.0f);
        loc.setBearing(0.0f);
        loc.setTime(System.currentTimeMillis());
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
        }
        return loc;
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }
}
""")

    # 5. Upgraded Engine.java: Independent APK Vault + Split-APK Native Libs (Instagram/Soroush/Gap) + Chrome Main Activity Fix + LruCache
    write_file("app/src/main/java/com/veyravault/space/core/Engine.java", """
package com.veyravault.space.core;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.util.LruCache;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.entity.pm.InstallResult;

public class Engine {
    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(120);

    public static class AppModel {
        public String packageName;
        public String name;
        public Drawable icon;
        public int userId;

        public AppModel(String pkg, String name, Drawable icon, int userId) {
            this.packageName = pkg;
            this.name = name;
            this.icon = icon;
            this.userId = userId;
        }
    }

    public static File getVaultDirForPackage(Context ctx, String pkg) {
        File dir = new File(ctx.getFilesDir(), "apk_vault/" + pkg);
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    public static File getVaultedBaseApk(Context ctx, String pkg) {
        return new File(getVaultDirForPackage(ctx, pkg), "base.apk");
    }

    /**
     * Backs up the host app's base.apk AND all split APKs into our Independent APK Vault,
     * and extracts native .so libraries so Instagram, Soroush, Gap, Viber work seamlessly
     * AND survive even if the original app is uninstalled from the phone!
     */
    public static File backupPackageToVault(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
            File vaultDir = getVaultDirForPackage(ctx, pkg);
            File destBase = new File(vaultDir, "base.apk");

            if (ai.sourceDir != null) {
                File srcBase = new File(ai.sourceDir);
                if (srcBase.exists() && (!destBase.exists() || destBase.length() != srcBase.length())) {
                    copyFile(srcBase, destBase);
                }
            }

            // Copy Split APKs (critical for Instagram, Soroush, Gap, Chrome)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP && ai.splitSourceDirs != null) {
                int idx = 0;
                for (String splitPath : ai.splitSourceDirs) {
                    if (splitPath != null) {
                        File splitFile = new File(splitPath);
                        if (splitFile.exists()) {
                            File destSplit = new File(vaultDir, "split_" + (idx++) + "_" + splitFile.getName());
                            if (!destSplit.exists() || destSplit.length() != splitFile.length()) {
                                copyFile(splitFile, destSplit);
                            }
                            extractNativeLibsFromApk(ctx, pkg, splitFile);
                        }
                    }
                }
            }
            if (destBase.exists()) {
                extractNativeLibsFromApk(ctx, pkg, destBase);
            }

            CharSequence label = ai.loadLabel(pm);
            if (label != null) {
                CloneMetadataStore.saveAppLabel(ctx, pkg, label.toString());
            }
            return destBase.exists() ? destBase : null;
        } catch (Throwable t) {
            File fallback = getVaultedBaseApk(ctx, pkg);
            return fallback.exists() ? fallback : null;
        }
    }

    /**
     * Extracts .so libraries from base or split APKs directly into BlackBox's virtual app lib folder
     * so apps like Instagram, Soroush, Gap, Viber never hang on missing native libraries.
     */
    private static void extractNativeLibsFromApk(Context ctx, String pkg, File apkFile) {
        ZipFile zf = null;
        try {
            String primaryAbi = Build.SUPPORTED_ABIS != null && Build.SUPPORTED_ABIS.length > 0
                    ? Build.SUPPORTED_ABIS[0] : "arm64-v8a";
            zf = new ZipFile(apkFile);
            Enumeration<? extends ZipEntry> entries = zf.entries();

            File vaultLibDir = new File(getVaultDirForPackage(ctx, pkg), "lib");
            if (!vaultLibDir.exists()) vaultLibDir.mkdirs();

            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                if (name != null && name.startsWith("lib/") && name.endsWith(".so") && !entry.isDirectory()) {
                    if (name.contains(primaryAbi) || name.contains("armeabi-v7a") || name.contains("arm64-v8a")) {
                        String soName = name.substring(name.lastIndexOf('/') + 1);
                        File outSo = new File(vaultLibDir, soName);
                        if (!outSo.exists() || outSo.length() != entry.getSize()) {
                            try (InputStream is = zf.getInputStream(entry);
                                 FileOutputStream fos = new FileOutputStream(outSo)) {
                                byte[] buf = new byte[16384];
                                int len;
                                while ((len = is.read(buf)) > 0) {
                                    fos.write(buf, 0, len);
                                }
                            }
                        }
                    }
                }
            }
            syncVaultLibsToBlackBoxDataDir(ctx, pkg, vaultLibDir);
        } catch (Throwable ignored) {
        } finally {
            if (zf != null) {
                try { zf.close(); } catch (Exception ignored) {}
            }
        }
    }

    private static void syncVaultLibsToBlackBoxDataDir(Context ctx, String pkg, File vaultLibDir) {
        try {
            File[] soFiles = vaultLibDir.listFiles();
            if (soFiles == null || soFiles.length == 0) return;

            File dataRoot = ctx.getFilesDir().getParentFile();
            String[] candidatePaths = {
                "virtual/data/app/" + pkg + "/lib",
                "virtual/data/app/" + pkg + "/lib/arm64",
                "virtual/data/app/" + pkg + "/lib/arm",
                "blackbox/data/app/" + pkg + "/lib"
            };
            for (String rel : candidatePaths) {
                File targetDir = new File(dataRoot, rel);
                if (targetDir.getParentFile() != null && targetDir.getParentFile().exists()) {
                    if (!targetDir.exists()) targetDir.mkdirs();
                    for (File so : soFiles) {
                        File dst = new File(targetDir, so.getName());
                        if (!dst.exists() || dst.length() != so.length()) {
                            copyFile(so, dst);
                        }
                    }
                }
            }
        } catch (Throwable ignored) {}
    }

    private static void copyFile(File src, File dst) throws Exception {
        try (FileInputStream fis = new FileInputStream(src);
             FileOutputStream fos = new FileOutputStream(dst)) {
            byte[] buf = new byte[32768];
            int len;
            while ((len = fis.read(buf)) > 0) {
                fos.write(buf, 0, len);
            }
        }
    }

    public static List<AppModel> getInstalledApps(Context context) {
        PackageManager pm = context.getPackageManager();
        Intent mainIntent = new Intent(Intent.ACTION_MAIN, null);
        mainIntent.addCategory(Intent.CATEGORY_LAUNCHER);

        List<ResolveInfo> resolved = pm.queryIntentActivities(mainIntent, 0);
        Set<String> seen = new HashSet<>();
        List<AppModel> result = new ArrayList<>();

        for (ResolveInfo ri : resolved) {
            if (ri.activityInfo == null) continue;
            String pkg = ri.activityInfo.packageName;
            if (pkg.equals(context.getPackageName()) || seen.contains(pkg)) continue;
            seen.add(pkg);

            ApplicationInfo ai = ri.activityInfo.applicationInfo;
            CharSequence labelCs = ai.loadLabel(pm);
            String label = labelCs != null ? labelCs.toString() : pkg;
            Drawable icon = getCachedIcon(pm, ai, pkg);
            result.add(new AppModel(pkg, label, icon, 0));
        }

        Collections.sort(result, (a, b) -> a.name.compareToIgnoreCase(b.name));
        return result;
    }

    private static Drawable getCachedIcon(PackageManager pm, ApplicationInfo ai, String pkg) {
        Drawable cached = ICON_CACHE.get(pkg);
        if (cached != null) return cached;
        try {
            Drawable d = ai.loadIcon(pm);
            if (d != null) ICON_CACHE.put(pkg, d);
            return d;
        } catch (Throwable t) {
            return null;
        }
    }

    public static List<AppModel> getClonedApps(Context context, int userId) {
        List<AppModel> list = new ArrayList<>();
        PackageManager pm = context.getPackageManager();
        Set<String> added = new HashSet<>();

        try {
            List<ApplicationInfo> installed = BlackBoxCore.get().getInstalledApplications(0, userId);
            if (installed != null) {
                for (ApplicationInfo info : installed) {
                    if (info == null || info.packageName == null) continue;
                    if (info.packageName.equals(context.getPackageName())) continue;
                    // Hide internal GMS packages from user app grid
                    if (info.packageName.equals("com.google.android.gms") || info.packageName.equals("com.google.android.gsf")) continue;

                    added.add(info.packageName);
                    CloneMetadataStore.registerClonedApp(context, info.packageName, userId);
                    list.add(buildClonedAppModel(context, pm, info.packageName, info, userId));
                }
            }
        } catch (Throwable ignored) {}

        // Also check our Independent Registry: if the user uninstalled the original app from their phone,
        // automatically re-verify/keep the clone alive from our Independent APK Vault!
        Set<String> registered = CloneMetadataStore.getRegisteredClones(context, userId);
        for (String pkg : registered) {
            if (!added.contains(pkg)) {
                File vaultedApk = getVaultedBaseApk(context, pkg);
                if (vaultedApk.exists()) {
                    try {
                        BlackBoxCore.get().installPackageAsUser(vaultedApk, userId);
                        added.add(pkg);
                        list.add(buildClonedAppModel(context, pm, pkg, null, userId));
                    } catch (Throwable ignored) {}
                }
            }
        }
        return list;
    }

    private static AppModel buildClonedAppModel(Context context, PackageManager pm, String pkg, ApplicationInfo fallbackInfo, int userId) {
        String baseName = CloneMetadataStore.getCachedAppLabel(context, pkg);
        Drawable icon = ICON_CACHE.get(pkg);

        try {
            ApplicationInfo hostInfo = pm.getApplicationInfo(pkg, 0);
            baseName = hostInfo.loadLabel(pm).toString();
            CloneMetadataStore.saveAppLabel(context, pkg, baseName);
            if (icon == null) {
                icon = hostInfo.loadIcon(pm);
                if (icon != null) ICON_CACHE.put(pkg, icon);
            }
        } catch (Throwable notOnHost) {
            // Host app was uninstalled from phone! Load icon & label directly from our Independent APK Vault!
            File vaultedApk = getVaultedBaseApk(context, pkg);
            if (vaultedApk.exists()) {
                try {
                    PackageInfo pi = pm.getPackageArchiveInfo(vaultedApk.getAbsolutePath(), 0);
                    if (pi != null && pi.applicationInfo != null) {
                        pi.applicationInfo.sourceDir = vaultedApk.getAbsolutePath();
                        pi.applicationInfo.publicSourceDir = vaultedApk.getAbsolutePath();
                        CharSequence lbl = pi.applicationInfo.loadLabel(pm);
                        if (lbl != null) baseName = lbl.toString();
                        if (icon == null) {
                            icon = pi.applicationInfo.loadIcon(pm);
                            if (icon != null) ICON_CACHE.put(pkg, icon);
                        }
                    }
                } catch (Throwable ignored) {}
            }
            if ((icon == null) && fallbackInfo != null) {
                try { icon = fallbackInfo.loadIcon(pm); } catch (Throwable ignored) {}
            }
        }
        if (icon == null) {
            icon = context.getApplicationInfo().loadIcon(pm);
        }
        String finalName = CloneMetadataStore.getAlias(context, pkg, userId, baseName);
        return new AppModel(pkg, finalName, icon, userId);
    }

    public static int findNextAvailableUserIdForPackage(Context context, String pkg, int maxSpaces) {
        for (int userId = 0; userId < maxSpaces; userId++) {
            boolean existsInSpace = false;
            for (AppModel app : getClonedApps(context, userId)) {
                if (app.packageName.equals(pkg)) {
                    existsInSpace = true;
                    break;
                }
            }
            if (!existsInSpace) return userId;
        }
        return 0;
    }

    /**
     * Installs a clone using the Independent APK Vault so that:
     * 1) Uninstalling the app from the real phone NEVER deletes the clone inside VeyraVault.
     * 2) Split APKs & native .so libs (Instagram, Soroush, Gap, Chrome) are properly linked.
     */
    public static boolean installClone(Context ctx, String pkg, int userId) {
        try {
            GmsSupportManager.installGms(userId);
            File vaultedBase = backupPackageToVault(ctx, pkg);
            InstallResult res = null;
            if (vaultedBase != null && vaultedBase.exists()) {
                res = BlackBoxCore.get().installPackageAsUser(vaultedBase, userId);
            }
            if (res == null || !res.success) {
                res = BlackBoxCore.get().installPackageAsUser(pkg, userId);
            }
            if (res != null && res.success) {
                CloneMetadataStore.registerClonedApp(ctx, pkg, userId);
                File vaultLibDir = new File(getVaultDirForPackage(ctx, pkg), "lib");
                syncVaultLibsToBlackBoxDataDir(ctx, pkg, vaultLibDir);
                return true;
            }
            return false;
        } catch (Throwable t) {
            return false;
        }
    }

    /**
     * Installs an external APK file directly into a virtual space (without needing it installed on the phone).
     */
    public static boolean installExternalApkFile(Context ctx, File apkFile, int userId) {
        try {
            if (apkFile == null || !apkFile.exists()) return false;
            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(apkFile.getAbsolutePath(), 0);
            String pkg = (pi != null && pi.packageName != null) ? pi.packageName : null;
            if (pkg != null) {
                File destBase = getVaultedBaseApk(ctx, pkg);
                copyFile(apkFile, destBase);
                extractNativeLibsFromApk(ctx, pkg, destBase);
                if (pi.applicationInfo != null) {
                    pi.applicationInfo.sourceDir = destBase.getAbsolutePath();
                    pi.applicationInfo.publicSourceDir = destBase.getAbsolutePath();
                    CharSequence lbl = pi.applicationInfo.loadLabel(pm);
                    if (lbl != null) CloneMetadataStore.saveAppLabel(ctx, pkg, lbl.toString());
                }
                GmsSupportManager.installGms(userId);
                InstallResult res = BlackBoxCore.get().installPackageAsUser(destBase, userId);
                if (res != null && res.success) {
                    CloneMetadataStore.registerClonedApp(ctx, pkg, userId);
                    return true;
                }
            }
            InstallResult res = BlackBoxCore.get().installPackageAsUser(apkFile, userId);
            return res != null && res.success;
        } catch (Throwable t) {
            return false;
        }
    }

    /**
     * Launches a cloned app with:
     * 1) Strict Priority Device & Location/Region Hooks
     * 2) Automatic GMS support (for YouTube, Viber, etc.)
     * 3) Explicit Main Browser Activity resolution (fixes Chrome opening WebView DevTools!)
     */
    public static boolean launchClone(Context ctx, String pkg, int userId) {
        try {
            // Ensure GMS is enabled for YouTube, Viber, etc.
            if (!GmsSupportManager.isGmsInstalled(userId)) {
                GmsSupportManager.installGms(userId);
            }

            // Re-sync any Split APK native libraries for Instagram, Soroush, Gap
            File vaultLibDir = new File(getVaultDirForPackage(ctx, pkg), "lib");
            if (vaultLibDir.exists()) {
                syncVaultLibsToBlackBoxDataDir(ctx, pkg, vaultLibDir);
            }

            // Apply Priority 1 (Per-App) or Priority 2 (Global) Device, Region & Location Hooks
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, userId);

            // Special fix for Chrome & Browsers: prevent opening WebView DevTools!
            Intent explicitLauncher = resolveRealMainLauncherIntent(ctx, pkg);
            if (explicitLauncher != null) {
                try {
                    Method startAct = BlackBoxCore.class.getDeclaredMethod("startActivity", Intent.class, int.class);
                    startAct.setAccessible(true);
                    startAct.invoke(BlackBoxCore.get(), explicitLauncher, userId);
                    return true;
                } catch (Throwable ignored) {}
            }

            return BlackBoxCore.get().launchApk(pkg, userId);
        } catch (Throwable t) {
            return false;
        }
    }

    private static Intent resolveRealMainLauncherIntent(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            if ("com.android.chrome".equals(pkg) || pkg.contains("chrome")) {
                Intent chromeIntent = new Intent(Intent.ACTION_MAIN);
                chromeIntent.addCategory(Intent.CATEGORY_LAUNCHER);
                chromeIntent.setPackage(pkg);
                chromeIntent.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
                chromeIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                return chromeIntent;
            }
            Intent query = new Intent(Intent.ACTION_MAIN, null);
            query.addCategory(Intent.CATEGORY_LAUNCHER);
            query.setPackage(pkg);
            List<ResolveInfo> list = pm.queryIntentActivities(query, 0);
            if (list != null && !list.isEmpty()) {
                for (ResolveInfo ri : list) {
                    if (ri.activityInfo != null && ri.activityInfo.name != null) {
                        String actName = ri.activityInfo.name;
                        // Never pick WebView DevTools!
                        if (!actName.toLowerCase().contains("devui") && !actName.toLowerCase().contains("devtools")) {
                            Intent launch = new Intent(Intent.ACTION_MAIN);
                            launch.addCategory(Intent.CATEGORY_LAUNCHER);
                            launch.setComponent(new ComponentName(pkg, actName));
                            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                            return launch;
                        }
                    }
                }
            }
        } catch (Throwable ignored) {}
        return null;
    }

    public static void stopClone(String pkg, int userId) {
        try {
            BlackBoxCore.get().stopPackage(pkg, userId);
        } catch (Throwable ignored) {}
    }

    public static void clearCloneData(String pkg, int userId) {
        try {
            BlackBoxCore.get().clearPackage(pkg, userId);
        } catch (Throwable ignored) {}
    }

    public static void uninstallClone(Context ctx, String pkg, int userId) {
        try {
            CloneMetadataStore.clearAllForClone(ctx, pkg, userId);
            BlackBoxCore.get().uninstallPackageAsUser(pkg, userId);
        } catch (Throwable ignored) {}
    }
}
""")

    # 6. Upgraded SecurityManager: Simultaneous PIN & Pattern + Priority Selector + Auto-Fallback
    write_file("app/src/main/java/com/veyravault/space/security/SecurityManager.java", """
package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.UUID;

public class SecurityManager {
    private static final String PREF = "veyravault_security_v3";
    private static final String KEY_LOCK_ENABLED = "lock_enabled";
    private static final String KEY_PRIORITY_MODE = "priority_mode"; // "PIN" or "PATTERN"
    private static final String KEY_PIN_SALT = "pin_salt";
    private static final String KEY_PIN_HASH = "pin_hash";
    private static final String KEY_PAT_SALT = "pat_salt";
    private static final String KEY_PAT_HASH = "pat_hash";

    private static volatile boolean sessionUnlocked = false;

    public static boolean isSessionUnlocked() {
        return sessionUnlocked;
    }

    public static void setSessionUnlocked(boolean unlocked) {
        sessionUnlocked = unlocked;
    }

    public static boolean isLockEnabled(Context ctx) {
        return prefs(ctx).getBoolean(KEY_LOCK_ENABLED, false) && (hasPinConfigured(ctx) || hasPatternConfigured(ctx));
    }

    public static boolean hasPinConfigured(Context ctx) {
        String h = prefs(ctx).getString(KEY_PIN_HASH, "");
        return h != null && !h.isEmpty();
    }

    public static boolean hasPatternConfigured(Context ctx) {
        String h = prefs(ctx).getString(KEY_PAT_HASH, "");
        return h != null && !h.isEmpty();
    }

    public static boolean hasBothConfigured(Context ctx) {
        return hasPinConfigured(ctx) && hasPatternConfigured(ctx);
    }

    public static void setPriorityMode(Context ctx, String mode) {
        prefs(ctx).edit().putString(KEY_PRIORITY_MODE, "PIN".equals(mode) ? "PIN" : "PATTERN").apply();
    }

    public static String getPriorityMode(Context ctx) {
        String mode = prefs(ctx).getString(KEY_PRIORITY_MODE, "PIN");
        if ("PIN".equals(mode) && !hasPinConfigured(ctx) && hasPatternConfigured(ctx)) {
            return "PATTERN";
        }
        if ("PATTERN".equals(mode) && !hasPatternConfigured(ctx) && hasPinConfigured(ctx)) {
            return "PIN";
        }
        return mode;
    }

    public static String getLockMode(Context ctx) {
        return getPriorityMode(ctx);
    }

    public static void savePinPasscode(Context ctx, String rawPin) {
        if (rawPin == null || rawPin.trim().isEmpty()) return;
        String salt = UUID.randomUUID().toString();
        String hash = sha256(salt + ":" + rawPin.trim());
        SharedPreferences.Editor ed = prefs(ctx).edit();
        ed.putBoolean(KEY_LOCK_ENABLED, true)
          .putString(KEY_PIN_SALT, salt)
          .putString(KEY_PIN_HASH, hash);
        if (!hasPatternConfigured(ctx)) {
            ed.putString(KEY_PRIORITY_MODE, "PIN");
        }
        ed.apply();
    }

    public static void savePatternPasscode(Context ctx, String rawPattern) {
        if (rawPattern == null || rawPattern.trim().isEmpty()) return;
        String salt = UUID.randomUUID().toString();
        String hash = sha256(salt + ":" + rawPattern.trim());
        SharedPreferences.Editor ed = prefs(ctx).edit();
        ed.putBoolean(KEY_LOCK_ENABLED, true)
          .putString(KEY_PAT_SALT, salt)
          .putString(KEY_PAT_HASH, hash);
        if (!hasPinConfigured(ctx)) {
            ed.putString(KEY_PRIORITY_MODE, "PATTERN");
        }
        ed.apply();
    }

    public static void savePasscode(Context ctx, String mode, String rawSecret) {
        if ("PIN".equals(mode)) {
            savePinPasscode(ctx, rawSecret);
        } else {
            savePatternPasscode(ctx, rawSecret);
        }
    }

    public static boolean verifyPin(Context ctx, String candidate) {
        if (candidate == null) return false;
        SharedPreferences sp = prefs(ctx);
        String salt = sp.getString(KEY_PIN_SALT, "");
        String expected = sp.getString(KEY_PIN_HASH, "");
        if (salt.isEmpty() || expected.isEmpty()) return false;
        return expected.equals(sha256(salt + ":" + candidate.trim()));
    }

    public static boolean verifyPattern(Context ctx, String candidate) {
        if (candidate == null) return false;
        SharedPreferences sp = prefs(ctx);
        String salt = sp.getString(KEY_PAT_SALT, "");
        String expected = sp.getString(KEY_PAT_HASH, "");
        if (salt.isEmpty() || expected.isEmpty()) return false;
        return expected.equals(sha256(salt + ":" + candidate.trim()));
    }

    public static boolean verifyPasscode(Context ctx, String candidate) {
        return verifyPin(ctx, candidate) || verifyPattern(ctx, candidate);
    }

    public static void disableLock(Context ctx) {
        prefs(ctx).edit()
            .putBoolean(KEY_LOCK_ENABLED, false)
            .remove(KEY_PIN_SALT)
            .remove(KEY_PIN_HASH)
            .remove(KEY_PAT_SALT)
            .remove(KEY_PAT_HASH)
            .apply();
        sessionUnlocked = true;
    }

    private static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }
}
""")

    print("[v3-Part1] Core Engine, Vault, Hooks, Dual Lock & SVG Icons updated successfully.")

if __name__ == "__main__":
    apply_part1()
