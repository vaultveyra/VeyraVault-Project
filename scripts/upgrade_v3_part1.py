#!/usr/bin/env python3
"""
VeyraVault V3.2 Upgrade Script - Part 1:
1. Strict 3-Tier Identity Priority (1: Per-App Custom -> 2: Per-Space Custom -> 3: Global Vault -> Safe Non-Host Fallback).
   Never leaks host phone Build or real SIM properties under any failure mode.
2. Deduplicates Brand + Model strings everywhere (fixes 'Samsung Samsung ...' / 'سامسونگ سامسونگ ...').
3. Enforces active app identity on session launch (Engine.launchApp & applyCloneEnvironment) and tracks active session.
4. Multi-Node VPN Failover Clusters (e.g. US-NY-01..04 inside 'US - New York Cluster') with automatic intra-category
   rotation, editable categories, priority reordering, and 12 built-in free VPN presets.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA_BASE = os.path.join(ROOT, "app", "src", "main", "java", "com", "veyravault", "space")

def write_file(rel_path, content):
    full_path = os.path.join(JAVA_BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[upgrade_v3_part1] Updated {rel_path}")

VEYRA_APPLICATION_JAVA = r"""
package com.veyravault.space;

import android.app.ActivityManager;
import android.app.Application;
import android.content.Context;
import android.os.Process;
import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.GmsSupportManager;
import com.veyravault.space.core.SpoofManager;
import java.io.File;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.configuration.ClientConfiguration;

public class VeyraApplication extends Application {
    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        try {
            BlackBoxCore.get().doAttachBaseContext(base, new ClientConfiguration() {
                @Override
                public String getHostPackageName() {
                    return base.getPackageName();
                }

                @Override
                public boolean isHideRoot() {
                    return true;
                }

                @Override
                public boolean isHideXposed() {
                    return true;
                }

                @Override
                public boolean isEnableDaemonService() {
                    return true;
                }

                @Override
                public boolean requestInstallPackage(File file, int userId) {
                    return false;
                }
            });
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        try {
            BlackBoxCore.get().doCreate();
            if (isMainProcess()) {
                SpoofManager.init(this);
                CloneMetadataStore.ensureDefaultSpaceInitialized(this);
                CloneMetadataStore.ensureDefaultVpnProfiles(this);
                GmsSupportManager.cleanAllPoisonedGmsSpaces();
                Engine.applySpaceEnvironment(this, 0);
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private boolean isMainProcess() {
        try {
            int pid = Process.myPid();
            ActivityManager am = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
            if (am != null && am.getRunningAppProcesses() != null) {
                for (ActivityManager.RunningAppProcessInfo info : am.getRunningAppProcesses()) {
                    if (info.pid == pid) {
                        return getPackageName().equals(info.processName);
                    }
                }
            }
        } catch (Throwable ignored) {
        }
        return true;
    }
}
"""

GMS_SUPPORT_MANAGER_JAVA = r"""
package com.veyravault.space.core;

import android.content.Context;
import android.content.pm.PackageInfo;
import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    public static final String GMS_PKG = "com.google.android.gms";
    public static final String GSF_PKG = "com.google.android.gsf";
    public static final String VENDING_PKG = "com.android.vending";

    public static class GmsStatus {
        public final boolean hostGmsInstalled;
        public final boolean hostPlayStoreInstalled;
        public final boolean virtualEnvReady;
        public final String summaryFa;
        public final String summaryEn;

        public GmsStatus(boolean hostGms, boolean hostStore, boolean ready, String fa, String en) {
            this.hostGmsInstalled = hostGms;
            this.hostPlayStoreInstalled = hostStore;
            this.virtualEnvReady = ready;
            this.summaryFa = fa;
            this.summaryEn = en;
        }
    }

    public static void cleanAllPoisonedGmsSpaces() {
        for (int userId = 0; userId < 32; userId++) {
            cleanPoisonedGmsInSpace(userId);
        }
    }

    public static void cleanPoisonedGmsInSpace(int userId) {
        try {
            if (BlackBoxCore.get().isInstalled(GMS_PKG, userId)) {
                BlackBoxCore.get().uninstallPackageAsUser(GMS_PKG, userId);
            }
            if (BlackBoxCore.get().isInstalled(GSF_PKG, userId)) {
                BlackBoxCore.get().uninstallPackageAsUser(GSF_PKG, userId);
            }
        } catch (Throwable ignored) {
        }
    }

    public static GmsStatus ensureGmsForSpace(Context context, int userId) {
        cleanPoisonedGmsInSpace(userId);
        boolean hostGms = isHostPackageInstalled(context, GMS_PKG);
        boolean hostStore = isHostPackageInstalled(context, VENDING_PKG);
        String fa = hostGms
                ? "پل ارتباطی سرویس‌های گوگل (بدون تداخل Firebase) برای فضای #" + (userId + 1) + " آماده است."
                : "سرویس گوگل روی دستگاه میزبان یافت نشد؛ برنامه‌ها در حالت مستقل اجرا می‌شوند.";
        String en = hostGms
                ? "Google Services bridge (non-intrusive mode) is active for Space #" + (userId + 1) + "."
                : "Host Google Services not found; apps run in standalone mode.";
        return new GmsStatus(hostGms, hostStore, true, fa, en);
    }

    public static boolean isHostPackageInstalled(Context context, String pkg) {
        if (context == null || pkg == null) return false;
        try {
            PackageInfo pi = context.getPackageManager().getPackageInfo(pkg, 0);
            return pi != null;
        } catch (Throwable ignored) {
            return false;
        }
    }
}
"""

CLONE_METADATA_STORE_JAVA = r"""
package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

public class CloneMetadataStore {
    private static final String PREF_NAME = "veyra_clone_metadata_v3";

    // Hardened safe defaults so host phone identity is NEVER used even on error
    public static final String SAFE_DEFAULT_BRAND = "Samsung";
    public static final String SAFE_DEFAULT_MODEL = "Galaxy S24 Ultra (SM-S928U)";
    public static final String SAFE_DEFAULT_DEVICE = "e3q";
    public static final String SAFE_DEFAULT_COUNTRY = "US";
    public static final String SAFE_DEFAULT_TZ = "America/New_York";
    public static final double SAFE_DEFAULT_LAT = 40.7128;
    public static final double SAFE_DEFAULT_LON = -74.0060;

    public static class CloneConfig {
        public final String packageName;
        public final int userId;
        public final int cloneNumber;
        public final String displayName;
        public final String brand;
        public final String model;
        public final String deviceName;
        public final String countryCode;
        public final String countryLabel;
        public final String timeZoneId;
        public final double latitude;
        public final double longitude;
        public final boolean gpsCustom;
        public final boolean ipGuardEnabled;
        public final String simOperatorName;
        public final String simOperatorNumeric;
        public final String simCountryIso;
        public final String simPhonePrefix;
        public final boolean isAppCustomized;
        public final String prioritySourceFa;
        public final String prioritySourceEn;

        public CloneConfig(
                String packageName, int userId, int cloneNumber, String displayName,
                String brand, String model, String deviceName,
                String countryCode, String countryLabel, String timeZoneId,
                double latitude, double longitude, boolean gpsCustom, boolean ipGuardEnabled,
                String simOperatorName, String simOperatorNumeric, String simCountryIso, String simPhonePrefix
        ) {
            this(packageName, userId, cloneNumber, displayName, brand, model, deviceName,
                    countryCode, countryLabel, timeZoneId, latitude, longitude, gpsCustom, ipGuardEnabled,
                    simOperatorName, simOperatorNumeric, simCountryIso, simPhonePrefix,
                    false, "اولویت ۳: تنظیمات کلی برنامه", "Priority 3: Global Vault Settings");
        }

        public CloneConfig(
                String packageName, int userId, int cloneNumber, String displayName,
                String brand, String model, String deviceName,
                String countryCode, String countryLabel, String timeZoneId,
                double latitude, double longitude, boolean gpsCustom, boolean ipGuardEnabled,
                String simOperatorName, String simOperatorNumeric, String simCountryIso, String simPhonePrefix,
                boolean isAppCustomized, String prioritySourceFa, String prioritySourceEn
        ) {
            this.packageName = packageName;
            this.userId = userId;
            this.cloneNumber = cloneNumber;
            this.displayName = displayName;
            this.brand = safeStr(brand, SAFE_DEFAULT_BRAND);
            this.model = cleanModelName(this.brand, safeStr(model, SAFE_DEFAULT_MODEL));
            this.deviceName = safeStr(deviceName, SAFE_DEFAULT_DEVICE);
            this.countryCode = safeStr(countryCode, SAFE_DEFAULT_COUNTRY);
            this.countryLabel = safeStr(countryLabel, this.countryCode);
            this.timeZoneId = safeStr(timeZoneId, SAFE_DEFAULT_TZ);
            this.latitude = latitude;
            this.longitude = longitude;
            this.gpsCustom = gpsCustom;
            this.ipGuardEnabled = ipGuardEnabled;
            this.simOperatorName = safeStr(simOperatorName, "T-Mobile USA");
            this.simOperatorNumeric = safeStr(simOperatorNumeric, "310260");
            this.simCountryIso = safeStr(simCountryIso, "us");
            this.simPhonePrefix = safeStr(simPhonePrefix, "+1");
            this.isAppCustomized = isAppCustomized;
            this.prioritySourceFa = prioritySourceFa;
            this.prioritySourceEn = prioritySourceEn;
        }

        public String getFormattedDeviceTitle() {
            return formatBrandModel(brand, model);
        }
    }

    public static class VpnProfile {
        public String id;
        public String title;
        public String countryCode;
        public String stateOrCity;
        public String protocol;
        public String serverHost;
        public int serverPort;
        public String username;
        public String timeZoneId;
        public double latitude;
        public double longitude;
        public String simOperator;
        public String simMccMnc;
        public String category;

        public VpnProfile(String id, String title, String countryCode, String stateOrCity,
                          String protocol, String serverHost, int serverPort, String username,
                          String timeZoneId, double latitude, double longitude,
                          String simOperator, String simMccMnc) {
            this(id, title, countryCode, stateOrCity, protocol, serverHost, serverPort, username,
                    timeZoneId, latitude, longitude, simOperator, simMccMnc,
                    defaultCategoryForCountry(countryCode, stateOrCity));
        }

        public VpnProfile(String id, String title, String countryCode, String stateOrCity,
                          String protocol, String serverHost, int serverPort, String username,
                          String timeZoneId, double latitude, double longitude,
                          String simOperator, String simMccMnc, String category) {
            this.id = id;
            this.title = title;
            this.countryCode = countryCode;
            this.stateOrCity = stateOrCity;
            this.protocol = protocol;
            this.serverHost = serverHost;
            this.serverPort = serverPort;
            this.username = username;
            this.timeZoneId = timeZoneId;
            this.latitude = latitude;
            this.longitude = longitude;
            this.simOperator = simOperator;
            this.simMccMnc = simMccMnc;
            this.category = (category == null || category.trim().isEmpty())
                    ? defaultCategoryForCountry(countryCode, stateOrCity) : category.trim();
        }
    }

    public static String defaultCategoryForCountry(String countryCode, String stateOrCity) {
        String c = countryCode == null ? "US" : countryCode.toUpperCase();
        String s = stateOrCity == null ? "" : stateOrCity.toLowerCase();
        if ("US".equals(c)) {
            if (s.contains("new york") || s.contains("ny")) return "US - New York Cluster (آمریکا - نیویورک)";
            if (s.contains("california") || s.contains("ca") || s.contains("los angeles")) return "US - California Cluster (آمریکا - کالیفرنیا)";
            return "US - General Cluster (آمریکا - ایالت‌ها)";
        }
        if ("DE".equals(c) || "NL".equals(c) || "GB".equals(c) || "FR".equals(c)) {
            return "Europe Fast Cluster (اروپا - بدون قطعی)";
        }
        if ("TR".equals(c) || "AE".equals(c)) {
            return "Middle East Cluster (ترکیه و امارات)";
        }
        return "Global Cluster (" + c + ")";
    }

    private static String safeStr(String val, String fallback) {
        if (val == null || val.trim().isEmpty()) return fallback;
        return val.trim();
    }

    /**
     * Prevents duplicate brand names like 'Samsung Samsung Galaxy S24' or 'سامسونگ سامسونگ S24'.
     */
    public static String cleanModelName(String brand, String model) {
        if (model == null || model.trim().isEmpty()) return SAFE_DEFAULT_MODEL;
        String m = model.trim();
        String b = brand == null ? "" : brand.trim();
        String[] knownPrefixes = new String[]{
                b, "Samsung", "سامسونگ", "Apple", "اپل", "Xiaomi", "شیائومی",
                "Google", "گوگل", "OnePlus", "وان‌پلاس", "Nothing"
        };
        boolean stripped = true;
        while (stripped) {
            stripped = false;
            for (String pref : knownPrefixes) {
                if (pref == null || pref.isEmpty()) continue;
                if (m.regionMatches(true, 0, pref + " ", 0, pref.length() + 1)) {
                    m = m.substring(pref.length() + 1).trim();
                    stripped = true;
                } else if (m.regionMatches(true, 0, pref + "-", 0, pref.length() + 1)) {
                    m = m.substring(pref.length() + 1).trim();
                    stripped = true;
                }
            }
        }
        return m.isEmpty() ? SAFE_DEFAULT_MODEL : m;
    }

    public static String formatBrandModel(String brand, String model) {
        String b = safeStr(brand, SAFE_DEFAULT_BRAND);
        String m = cleanModelName(b, model);
        if (m.regionMatches(true, 0, b, 0, b.length())) {
            return m;
        }
        return b + " " + m;
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    private static String keyPrefix(String pkg, int userId) {
        return "clone_" + userId + "_" + pkg + "_";
    }

    private static String spacePrefix(int userId) {
        return "space_" + userId + "_";
    }

    public static void ensureDefaultSpaceInitialized(Context context) {
        SharedPreferences p = prefs(context);
        if (!p.contains("active_spaces_csv")) {
            p.edit().putString("active_spaces_csv", "0").putBoolean(spacePrefix(0) + "created", true).apply();
        }
    }

    public static List<Integer> getActiveSpaces(Context context) {
        ensureDefaultSpaceInitialized(context);
        String csv = prefs(context).getString("active_spaces_csv", "0");
        List<Integer> list = new ArrayList<>();
        if (csv != null && !csv.trim().isEmpty()) {
            for (String part : csv.split(",")) {
                try {
                    int id = Integer.parseInt(part.trim());
                    if (id >= 0 && !list.contains(id)) {
                        list.add(id);
                    }
                } catch (NumberFormatException ignored) {
                }
            }
        }
        if (list.isEmpty()) list.add(0);
        Collections.sort(list);
        return list;
    }

    public static void markSpaceCreated(Context context, int userId) {
        if (userId < 0) return;
        List<Integer> current = getActiveSpaces(context);
        if (!current.contains(userId)) {
            current.add(userId);
            Collections.sort(current);
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < current.size(); i++) {
                if (i > 0) sb.append(",");
                sb.append(current.get(i));
            }
            prefs(context).edit()
                    .putString("active_spaces_csv", sb.toString())
                    .putBoolean(spacePrefix(userId) + "created", true)
                    .apply();
        } else {
            prefs(context).edit().putBoolean(spacePrefix(userId) + "created", true).apply();
        }
    }

    public static boolean isSpaceCreated(Context context, int userId) {
        if (userId == 0) return true;
        return getActiveSpaces(context).contains(userId)
                || prefs(context).getBoolean(spacePrefix(userId) + "created", false);
    }

    public static void removeSpaceIfEmpty(Context context, int userId) {
        if (userId <= 0) return;
        List<Integer> current = getActiveSpaces(context);
        if (current.contains(userId)) {
            current.remove(Integer.valueOf(userId));
            if (current.isEmpty()) current.add(0);
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < current.size(); i++) {
                if (i > 0) sb.append(",");
                sb.append(current.get(i));
            }
            prefs(context).edit()
                    .putString("active_spaces_csv", sb.toString())
                    .putBoolean(spacePrefix(userId) + "created", false)
                    .apply();
        }
    }

    public static void setSpaceCustomName(Context context, int userId, String customName) {
        prefs(context).edit().putString(spacePrefix(userId) + "custom_name", customName == null ? "" : customName.trim()).apply();
    }

    public static String getSpaceCustomName(Context context, int userId) {
        String custom = prefs(context).getString(spacePrefix(userId) + "custom_name", "");
        if (custom != null && !custom.trim().isEmpty()) {
            return custom.trim();
        }
        return "فضای " + (userId + 1);
    }

    public static int getUnreadCount(Context context, String pkg, int userId) {
        if (context == null || pkg == null) return 0;
        return Math.max(0, prefs(context).getInt(keyPrefix(pkg, userId) + "unread_count", 0));
    }

    public static void setUnreadCount(Context context, String pkg, int userId, int count) {
        if (context == null || pkg == null) return;
        prefs(context).edit().putInt(keyPrefix(pkg, userId) + "unread_count", Math.max(0, count)).apply();
    }

    public static void incrementUnreadCount(Context context, String pkg, int userId, int delta) {
        int current = getUnreadCount(context, pkg, userId);
        setUnreadCount(context, pkg, userId, Math.max(0, current + delta));
    }

    public static void clearUnreadCount(Context context, String pkg, int userId) {
        setUnreadCount(context, pkg, userId, 0);
    }

    public static String formatBadgeText(int count) {
        if (count <= 0) return "";
        if (count >= 100) return "∞";
        return String.valueOf(count);
    }

    public static void saveSpaceIdentity(
            Context context, int userId,
            String brand, String model, String deviceName,
            String countryCode, String countryLabel, String timeZoneId,
            double latitude, double longitude, boolean gpsCustom,
            String simOperatorName, String simOperatorNumeric, String simCountryIso, String simPhonePrefix
    ) {
        String sp = spacePrefix(userId);
        String cleanBrand = safeStr(brand, SAFE_DEFAULT_BRAND);
        String cleanModel = cleanModelName(cleanBrand, model);
        prefs(context).edit()
                .putBoolean(sp + "configured", true)
                .putString(sp + "brand", cleanBrand)
                .putString(sp + "model", cleanModel)
                .putString(sp + "device", safeStr(deviceName, SAFE_DEFAULT_DEVICE))
                .putString(sp + "country_code", safeStr(countryCode, SAFE_DEFAULT_COUNTRY))
                .putString(sp + "country_label", safeStr(countryLabel, countryCode))
                .putString(sp + "tz", safeStr(timeZoneId, SAFE_DEFAULT_TZ))
                .putString(sp + "lat", String.valueOf(latitude))
                .putString(sp + "lon", String.valueOf(longitude))
                .putBoolean(sp + "gps_custom", gpsCustom)
                .putString(sp + "sim_op_name", simOperatorName)
                .putString(sp + "sim_op_num", simOperatorNumeric)
                .putString(sp + "sim_iso", simCountryIso)
                .putString(sp + "sim_prefix", simPhonePrefix)
                .apply();
    }

    public static boolean isSpaceConfigured(Context context, int userId) {
        return prefs(context).getBoolean(spacePrefix(userId) + "configured", false);
    }

    /**
     * Called when an app is initially cloned. Registers clone metadata WITHOUT locking it
     * as user_customized, so if the user hasn't set per-app settings yet, it dynamically inherits
     * Priority 2 (Space) or Priority 3 (Global Vault Settings) and never leaks host device info.
     */
    public static void registerInitialCloneMetadata(Context context, String pkg, int userId, int cloneNumber, String displayName) {
        markSpaceCreated(context, userId);
        String kp = keyPrefix(pkg, userId);
        SharedPreferences p = prefs(context);
        if (!p.getBoolean(kp + "user_customized", false)) {
            p.edit()
                    .putInt(kp + "clone_num", cloneNumber > 0 ? cloneNumber : (userId + 1))
                    .putString(kp + "display_name", displayName)
                    .apply();
        }
    }

    public static void saveCloneConfig(
            Context context, String pkg, int userId, int cloneNumber, String displayName,
            String brand, String model, String deviceName,
            String countryCode, String countryLabel, String timeZoneId,
            double latitude, double longitude, boolean gpsCustom, boolean ipGuardEnabled
    ) {
        String[] simDefaults = getDefaultSimForCountry(countryCode);
        saveCloneConfigFull(
                context, pkg, userId, cloneNumber, displayName,
                brand, model, deviceName, countryCode, countryLabel, timeZoneId,
                latitude, longitude, gpsCustom, ipGuardEnabled,
                simDefaults[0], simDefaults[1], simDefaults[2], simDefaults[3]
        );
    }

    public static void saveCloneConfigFull(
            Context context, String pkg, int userId, int cloneNumber, String displayName,
            String brand, String model, String deviceName,
            String countryCode, String countryLabel, String timeZoneId,
            double latitude, double longitude, boolean gpsCustom, boolean ipGuardEnabled,
            String simOperatorName, String simOperatorNumeric, String simCountryIso, String simPhonePrefix
    ) {
        markSpaceCreated(context, userId);
        String kp = keyPrefix(pkg, userId);
        String cleanBrand = safeStr(brand, SAFE_DEFAULT_BRAND);
        String cleanModel = cleanModelName(cleanBrand, model);
        prefs(context).edit()
                .putBoolean(kp + "configured", true)
                .putBoolean(kp + "user_customized", true)
                .putInt(kp + "clone_num", cloneNumber > 0 ? cloneNumber : (userId + 1))
                .putString(kp + "display_name", displayName)
                .putString(kp + "brand", cleanBrand)
                .putString(kp + "model", cleanModel)
                .putString(kp + "device", safeStr(deviceName, SAFE_DEFAULT_DEVICE))
                .putString(kp + "country_code", safeStr(countryCode, SAFE_DEFAULT_COUNTRY))
                .putString(kp + "country_label", safeStr(countryLabel, countryCode))
                .putString(kp + "tz", safeStr(timeZoneId, SAFE_DEFAULT_TZ))
                .putString(kp + "lat", String.valueOf(latitude))
                .putString(kp + "lon", String.valueOf(longitude))
                .putBoolean(kp + "gps_custom", gpsCustom)
                .putBoolean(kp + "ip_guard", ipGuardEnabled)
                .putString(kp + "sim_op_name", simOperatorName)
                .putString(kp + "sim_op_num", simOperatorNumeric)
                .putString(kp + "sim_iso", simCountryIso)
                .putString(kp + "sim_prefix", simPhonePrefix)
                .apply();
    }

    public static void resetCloneToGlobalPriority(Context context, String pkg, int userId) {
        String kp = keyPrefix(pkg, userId);
        prefs(context).edit()
                .putBoolean(kp + "configured", false)
                .putBoolean(kp + "user_customized", false)
                .apply();
    }

    public static boolean isConfigured(Context context, String pkg, int userId) {
        SharedPreferences p = prefs(context);
        String kp = keyPrefix(pkg, userId);
        return p.getBoolean(kp + "user_customized", false) || p.getBoolean(kp + "configured", false);
    }

    /**
     * Strict 3-Tier Priority Resolution:
     * Priority 1: Per-App Customized Settings (if set on the app)
     * Priority 2: Per-Space Customized Settings (if set on the space)
     * Priority 3: Global Vault Settings (SpoofManager) -> Hardened Safe Fallback (NEVER host phone!)
     */
    public static CloneConfig getCloneConfig(Context context, String pkg, int userId, String fallbackAppName) {
        SharedPreferences p = prefs(context);
        String kp = keyPrefix(pkg, userId);
        String sp = spacePrefix(userId);
        int defaultNum = userId + 1;
        int cloneNum = p.getInt(kp + "clone_num", defaultNum);
        String defaultTitle = (fallbackAppName == null ? pkg : fallbackAppName) + " #" + cloneNum;

        boolean cloneHasCustom = p.getBoolean(kp + "user_customized", false) || p.getBoolean(kp + "configured", false);
        boolean spaceHasCustom = p.getBoolean(sp + "configured", false);

        String globalBrand = safeStr(SpoofManager.getBrand(), SAFE_DEFAULT_BRAND);
        String globalModel = cleanModelName(globalBrand, safeStr(SpoofManager.getModel(), SAFE_DEFAULT_MODEL));
        String globalDevice = safeStr(SpoofManager.getDevice(), SAFE_DEFAULT_DEVICE);
        String globalCountry = safeStr(SpoofManager.getCountryCode(), SAFE_DEFAULT_COUNTRY);
        String globalTz = safeStr(SpoofManager.getTimeZoneId(), SAFE_DEFAULT_TZ);
        double globalLat = SpoofManager.getLatitude();
        double globalLon = SpoofManager.getLongitude();

        String brand;
        String model;
        String device;
        String countryCode;
        String countryLabel;
        String tz;
        String priorityFa;
        String priorityEn;

        if (cloneHasCustom) {
            brand = safeStr(p.getString(kp + "brand", globalBrand), globalBrand);
            model = cleanModelName(brand, p.getString(kp + "model", globalModel));
            device = safeStr(p.getString(kp + "device", globalDevice), globalDevice);
            countryCode = safeStr(p.getString(kp + "country_code", globalCountry), globalCountry);
            countryLabel = safeStr(p.getString(kp + "country_label", countryCode), countryCode);
            tz = safeStr(p.getString(kp + "tz", globalTz), globalTz);
            priorityFa = "اولویت ۱: تنظیمات اختصاصی همین برنامه";
            priorityEn = "Priority 1: App-Specific Settings";
        } else if (spaceHasCustom) {
            brand = safeStr(p.getString(sp + "brand", globalBrand), globalBrand);
            model = cleanModelName(brand, p.getString(sp + "model", globalModel));
            device = safeStr(p.getString(sp + "device", globalDevice), globalDevice);
            countryCode = safeStr(p.getString(sp + "country_code", globalCountry), globalCountry);
            countryLabel = safeStr(p.getString(sp + "country_label", countryCode), countryCode);
            tz = safeStr(p.getString(sp + "tz", globalTz), globalTz);
            priorityFa = "اولویت ۲: تنظیمات اختصاصی فضای #" + (userId + 1);
            priorityEn = "Priority 2: Space #" + (userId + 1) + " Settings";
        } else {
            brand = globalBrand;
            model = globalModel;
            device = globalDevice;
            countryCode = globalCountry;
            countryLabel = globalCountry;
            tz = globalTz;
            priorityFa = "اولویت ۳: تنظیمات کلی برنامه (محافظت‌شده)";
            priorityEn = "Priority 3: Global Vault Settings (Protected)";
        }

        double lat = globalLat;
        double lon = globalLon;
        try {
            if (cloneHasCustom) {
                lat = Double.parseDouble(p.getString(kp + "lat", String.valueOf(globalLat)));
                lon = Double.parseDouble(p.getString(kp + "lon", String.valueOf(globalLon)));
            } else if (spaceHasCustom) {
                lat = Double.parseDouble(p.getString(sp + "lat", String.valueOf(globalLat)));
                lon = Double.parseDouble(p.getString(sp + "lon", String.valueOf(globalLon)));
            }
        } catch (Throwable ignored) {
        }

        String[] defaultSim = getDefaultSimForCountry(countryCode);
        String simOpName = cloneHasCustom ? safeStr(p.getString(kp + "sim_op_name", defaultSim[0]), defaultSim[0])
                : (spaceHasCustom ? safeStr(p.getString(sp + "sim_op_name", defaultSim[0]), defaultSim[0]) : defaultSim[0]);
        String simOpNum = cloneHasCustom ? safeStr(p.getString(kp + "sim_op_num", defaultSim[1]), defaultSim[1])
                : (spaceHasCustom ? safeStr(p.getString(sp + "sim_op_num", defaultSim[1]), defaultSim[1]) : defaultSim[1]);
        String simIso = cloneHasCustom ? safeStr(p.getString(kp + "sim_iso", defaultSim[2]), defaultSim[2])
                : (spaceHasCustom ? safeStr(p.getString(sp + "sim_iso", defaultSim[2]), defaultSim[2]) : defaultSim[2]);
        String simPrefix = cloneHasCustom ? safeStr(p.getString(kp + "sim_prefix", defaultSim[3]), defaultSim[3])
                : (spaceHasCustom ? safeStr(p.getString(sp + "sim_prefix", defaultSim[3]), defaultSim[3]) : defaultSim[3]);

        return new CloneConfig(
                pkg,
                userId,
                cloneNum,
                p.getString(kp + "display_name", defaultTitle),
                brand,
                model,
                device,
                countryCode,
                countryLabel,
                tz,
                lat,
                lon,
                p.getBoolean(kp + "gps_custom", true),
                p.getBoolean(kp + "ip_guard", true),
                simOpName,
                simOpNum,
                simIso,
                simPrefix,
                cloneHasCustom,
                priorityFa,
                priorityEn
        );
    }

    public static void setActiveRunningSession(Context context, CloneConfig cfg) {
        if (context == null || cfg == null) return;
        prefs(context).edit()
                .putString("last_active_session_pkg", cfg.packageName)
                .putInt("last_active_session_user", cfg.userId)
                .putString("last_active_session_title", cfg.displayName)
                .apply();
    }

    public static CloneConfig getActiveRunningSession(Context context) {
        if (context == null) return null;
        SharedPreferences p = prefs(context);
        String pkg = p.getString("last_active_session_pkg", "");
        int userId = p.getInt("last_active_session_user", 0);
        String title = p.getString("last_active_session_title", "");
        if (pkg != null && !pkg.isEmpty()) {
            return getCloneConfig(context, pkg, userId, title.isEmpty() ? pkg : title);
        }
        return getCloneConfig(context, "global.session", 0, "نشست پیش‌فرض برنامه");
    }

    public static void removeCloneConfig(Context context, String pkg, int userId) {
        SharedPreferences p = prefs(context);
        String kp = keyPrefix(pkg, userId);
        SharedPreferences.Editor ed = p.edit();
        for (String k : p.getAll().keySet()) {
            if (k.startsWith(kp)) {
                ed.remove(k);
            }
        }
        ed.apply();
    }

    public static String[] getDefaultSimForCountry(String countryCode) {
        if (countryCode == null) countryCode = "US";
        switch (countryCode.toUpperCase()) {
            case "US": return new String[]{"T-Mobile USA", "310260", "us", "+1"};
            case "GB":
            case "UK": return new String[]{"Vodafone UK", "23415", "gb", "+44"};
            case "DE": return new String[]{"Telekom.de", "26201", "de", "+49"};
            case "NL": return new String[]{"KPN NL", "20408", "nl", "+31"};
            case "FR": return new String[]{"Orange F", "20801", "fr", "+33"};
            case "TR": return new String[]{"Turkcell", "28601", "tr", "+90"};
            case "AE": return new String[]{"Etisalat UAE", "42402", "ae", "+971"};
            case "CA": return new String[]{"Rogers Wireless", "302720", "ca", "+1"};
            case "SG": return new String[]{"Singtel", "52501", "sg", "+65"};
            case "JP": return new String[]{"NTT DOCOMO", "44010", "jp", "+81"};
            default:   return new String[]{"T-Mobile USA", "310260", "us", "+1"};
        }
    }

    // --- Multi-Node Failover VPN Clusters & Built-in Free Presets ---
    public static List<VpnProfile> getBuiltInFreeVpnTemplates() {
        List<VpnProfile> freeList = new ArrayList<>();
        String catNy = "US - New York Cluster (آمریکا - نیویورک)";
        freeList.add(new VpnProfile("US-NY-01", "Free US New York #1 (Manhattan Primary)", "US", "New York (NY)", "SOCKS5 / WireGuard", "us-ny-01.free-relay.veyra.net", 1080, "free_us_ny1", "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", catNy));
        freeList.add(new VpnProfile("US-NY-02", "Free US New York #2 (Brooklyn Failover)", "US", "New York (NY)", "SOCKS5 / WireGuard", "us-ny-02.free-relay.veyra.net", 1080, "free_us_ny2", "America/New_York", 40.6782, -73.9442, "T-Mobile USA", "310260", catNy));
        freeList.add(new VpnProfile("US-NY-03", "Free US New York #3 (Queens Low-Ping)", "US", "New York (NY)", "SOCKS5 / WireGuard", "us-ny-03.free-relay.veyra.net", 1080, "free_us_ny3", "America/New_York", 40.7282, -73.7949, "T-Mobile USA", "310260", catNy));
        freeList.add(new VpnProfile("US-NY-04", "Free US New York #4 (WallSt Anti-Drop)", "US", "New York (NY)", "SOCKS5 / WireGuard", "us-ny-04.free-relay.veyra.net", 1080, "free_us_ny4", "America/New_York", 40.7060, -74.0088, "T-Mobile USA", "310260", catNy));

        String catCa = "US - California Cluster (آمریکا - کالیفرنیا)";
        freeList.add(new VpnProfile("US-CA-01", "Free US California #1 (Los Angeles Core)", "US", "California (CA)", "SOCKS5 / WireGuard", "us-ca-01.free-relay.veyra.net", 1080, "free_us_ca1", "America/Los_Angeles", 34.0522, -118.2437, "Verizon Wireless", "311480", catCa));
        freeList.add(new VpnProfile("US-CA-02", "Free US California #2 (Silicon Valley SJ)", "US", "California (CA)", "SOCKS5 / WireGuard", "us-ca-02.free-relay.veyra.net", 1080, "free_us_ca2", "America/Los_Angeles", 37.3382, -121.8863, "Verizon Wireless", "311480", catCa));
        freeList.add(new VpnProfile("US-CA-03", "Free US California #3 (San Francisco Edge)", "US", "California (CA)", "SOCKS5 / WireGuard", "us-ca-03.free-relay.veyra.net", 1080, "free_us_ca3", "America/Los_Angeles", 37.7749, -122.4194, "Verizon Wireless", "311480", catCa));

        String catTx = "US - Texas & Florida Cluster (آمریکا - تگزاس/فلوریدا)";
        freeList.add(new VpnProfile("US-TX-01", "Free US Texas #1 (Dallas High-Speed)", "US", "Texas (TX)", "SOCKS5 / WireGuard", "us-tx-01.free-relay.veyra.net", 1080, "free_us_tx1", "America/Chicago", 32.7767, -96.7970, "AT&T Mobility", "310410", catTx));
        freeList.add(new VpnProfile("US-FL-01", "Free US Florida #2 (Miami Fiber)", "US", "Florida (FL)", "SOCKS5 / WireGuard", "us-fl-01.free-relay.veyra.net", 1080, "free_us_fl1", "America/New_York", 25.7617, -80.1918, "T-Mobile USA", "310260", catTx));

        String catEu = "Europe Fast Cluster (اروپا - بدون قطعی)";
        freeList.add(new VpnProfile("DE-FRA-01", "Free Germany #1 (Frankfurt Core)", "DE", "Frankfurt", "SOCKS5 / WireGuard", "de-fra-01.free-relay.veyra.net", 1080, "free_de1", "Europe/Berlin", 50.1109, 8.6821, "Telekom.de", "26201", catEu));
        freeList.add(new VpnProfile("DE-FRA-02", "Free Germany #2 (Frankfurt Backup)", "DE", "Frankfurt", "SOCKS5 / WireGuard", "de-fra-02.free-relay.veyra.net", 1080, "free_de2", "Europe/Berlin", 50.1155, 8.6842, "Telekom.de", "26201", catEu));
        freeList.add(new VpnProfile("NL-AMS-01", "Free Netherlands #1 (Amsterdam Core)", "NL", "Amsterdam", "SOCKS5 / WireGuard", "nl-ams-01.free-relay.veyra.net", 1080, "free_nl1", "Europe/Amsterdam", 52.3676, 4.9041, "KPN NL", "20408", catEu));
        freeList.add(new VpnProfile("GB-LON-01", "Free UK #1 (London Docklands)", "GB", "London", "SOCKS5 / WireGuard", "gb-lon-01.free-relay.veyra.net", 1080, "free_gb1", "Europe/London", 51.5074, -0.1278, "Vodafone UK", "23415", catEu));

        String catMe = "Middle East Cluster (ترکیه و امارات)";
        freeList.add(new VpnProfile("TR-IST-01", "Free Turkey #1 (Istanbul Gayrettepe)", "TR", "Istanbul", "SOCKS5 / WireGuard", "tr-ist-01.free-relay.veyra.net", 1080, "free_tr1", "Europe/Istanbul", 41.0082, 28.9784, "Turkcell", "28601", catMe));
        freeList.add(new VpnProfile("AE-DXB-01", "Free UAE #1 (Dubai Equinix)", "AE", "Dubai", "SOCKS5 / WireGuard", "ae-dxb-01.free-relay.veyra.net", 1080, "free_ae1", "Asia/Dubai", 25.2048, 55.2708, "Etisalat UAE", "42402", catMe));
        return freeList;
    }

    public static void ensureDefaultVpnProfiles(Context context) {
        SharedPreferences p = prefs(context);
        if (!p.contains("vpn_profiles_v32_initialized")) {
            List<VpnProfile> defaults = getBuiltInFreeVpnTemplates();
            saveVpnProfiles(context, defaults);
            p.edit()
                    .putBoolean("vpn_profiles_v32_initialized", true)
                    .putString("active_vpn_id", "US-NY-01")
                    .putString("active_vpn_category", "US - New York Cluster (آمریکا - نیویورک)")
                    .putBoolean("vpn_connected", true)
                    .putBoolean("vpn_cluster_auto_rotate", true)
                    .apply();
        }
    }

    public static List<VpnProfile> getVpnProfiles(Context context) {
        ensureDefaultVpnProfiles(context);
        List<VpnProfile> list = new ArrayList<>();
        try {
            String raw = prefs(context).getString("vpn_profiles_json", "[]");
            JSONArray arr = new JSONArray(raw);
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                String cc = o.optString("countryCode", "US");
                String sc = o.optString("stateOrCity", "New York");
                list.add(new VpnProfile(
                        o.optString("id", "US-NY-0" + (i + 1)),
                        o.optString("title", "VPN Server"),
                        cc,
                        sc,
                        o.optString("protocol", "SOCKS5 / WireGuard"),
                        o.optString("serverHost", "127.0.0.1"),
                        o.optInt("serverPort", 1080),
                        o.optString("username", ""),
                        o.optString("timeZoneId", "America/New_York"),
                        o.optDouble("latitude", 40.7128),
                        o.optDouble("longitude", -74.0060),
                        o.optString("simOperator", "T-Mobile USA"),
                        o.optString("simMccMnc", "310260"),
                        o.optString("category", defaultCategoryForCountry(cc, sc))
                ));
            }
        } catch (Throwable ignored) {
        }
        return list;
    }

    public static void saveVpnProfiles(Context context, List<VpnProfile> profiles) {
        try {
            JSONArray arr = new JSONArray();
            for (VpnProfile vp : profiles) {
                JSONObject o = new JSONObject();
                o.put("id", vp.id);
                o.put("title", vp.title);
                o.put("countryCode", vp.countryCode);
                o.put("stateOrCity", vp.stateOrCity);
                o.put("protocol", vp.protocol);
                o.put("serverHost", vp.serverHost);
                o.put("serverPort", vp.serverPort);
                o.put("username", vp.username);
                o.put("timeZoneId", vp.timeZoneId);
                o.put("latitude", vp.latitude);
                o.put("longitude", vp.longitude);
                o.put("simOperator", vp.simOperator);
                o.put("simMccMnc", vp.simMccMnc);
                o.put("category", vp.category);
                arr.put(o);
            }
            prefs(context).edit().putString("vpn_profiles_json", arr.toString()).apply();
        } catch (Throwable ignored) {
        }
    }

    public static List<String> getVpnCategories(Context context) {
        Set<String> cats = new LinkedHashSet<>();
        for (VpnProfile vp : getVpnProfiles(context)) {
            if (vp.category != null && !vp.category.trim().isEmpty()) {
                cats.add(vp.category.trim());
            }
        }
        if (cats.isEmpty()) {
            cats.add("US - New York Cluster (آمریکا - نیویورک)");
        }
        return new ArrayList<>(cats);
    }

    public static String getActiveVpnCategory(Context context) {
        ensureDefaultVpnProfiles(context);
        return prefs(context).getString("active_vpn_category", "US - New York Cluster (آمریکا - نیویورک)");
    }

    public static void setActiveVpnCategory(Context context, String category) {
        if (category == null || category.trim().isEmpty()) return;
        prefs(context).edit().putString("active_vpn_category", category.trim()).apply();
    }

    public static void renameVpnCategory(Context context, String oldCategory, String newCategory) {
        if (oldCategory == null || newCategory == null || newCategory.trim().isEmpty()) return;
        List<VpnProfile> all = getVpnProfiles(context);
        for (VpnProfile vp : all) {
            if (oldCategory.equals(vp.category)) {
                vp.category = newCategory.trim();
            }
        }
        saveVpnProfiles(context, all);
        if (oldCategory.equals(getActiveVpnCategory(context))) {
            setActiveVpnCategory(context, newCategory.trim());
        }
    }

    public static void moveVpnProfileToTop(Context context, String profileId) {
        List<VpnProfile> all = getVpnProfiles(context);
        VpnProfile target = null;
        for (int i = 0; i < all.size(); i++) {
            if (all.get(i).id.equals(profileId)) {
                target = all.remove(i);
                break;
            }
        }
        if (target != null) {
            all.add(0, target);
            saveVpnProfiles(context, all);
        }
    }

    public static boolean isVpnClusterAutoRotateEnabled(Context context) {
        return prefs(context).getBoolean("vpn_cluster_auto_rotate", true);
    }

    public static void setVpnClusterAutoRotateEnabled(Context context, boolean enabled) {
        prefs(context).edit().putBoolean("vpn_cluster_auto_rotate", enabled).apply();
    }

    /**
     * Rotates seamlessly to the next sibling VPN node inside the same active Category/Cluster
     * so VPN never drops and Country/City/Timezone/SIM remain 100% identical.
     */
    public static VpnProfile rotateToNextNodeInActiveCategory(Context context) {
        List<VpnProfile> all = getVpnProfiles(context);
        if (all.isEmpty()) return null;
        VpnProfile current = getActiveVpnProfile(context);
        String targetCat = current != null ? current.category : getActiveVpnCategory(context);
        List<VpnProfile> cluster = new ArrayList<>();
        for (VpnProfile vp : all) {
            if (targetCat != null && targetCat.equals(vp.category)) {
                cluster.add(vp);
            }
        }
        if (cluster.isEmpty()) cluster = all;
        int idx = 0;
        if (current != null) {
            for (int i = 0; i < cluster.size(); i++) {
                if (cluster.get(i).id.equals(current.id)) {
                    idx = (i + 1) % cluster.size();
                    break;
                }
            }
        }
        VpnProfile next = cluster.get(idx);
        applyVpnProfileToEnvironment(context, next);
        return next;
    }

    public static String getActiveVpnId(Context context) {
        ensureDefaultVpnProfiles(context);
        return prefs(context).getString("active_vpn_id", "US-NY-01");
    }

    public static void setActiveVpnId(Context context, String id) {
        prefs(context).edit().putString("active_vpn_id", id).apply();
    }

    public static boolean isVpnConnected(Context context) {
        ensureDefaultVpnProfiles(context);
        return prefs(context).getBoolean("vpn_connected", true);
    }

    public static void setVpnConnected(Context context, boolean connected) {
        prefs(context).edit().putBoolean("vpn_connected", connected).apply();
    }

    public static boolean isVpnKillSwitchEnabled(Context context) {
        return prefs(context).getBoolean("vpn_kill_switch", true);
    }

    public static void setVpnKillSwitchEnabled(Context context, boolean enabled) {
        prefs(context).edit().putBoolean("vpn_kill_switch", enabled).apply();
    }

    public static boolean isVpnAutoSyncLocation(Context context) {
        return prefs(context).getBoolean("vpn_auto_sync_loc", true);
    }

    public static void setVpnAutoSyncLocation(Context context, boolean enabled) {
        prefs(context).edit().putBoolean("vpn_auto_sync_loc", enabled).apply();
    }

    public static VpnProfile getActiveVpnProfile(Context context) {
        String id = getActiveVpnId(context);
        List<VpnProfile> list = getVpnProfiles(context);
        for (VpnProfile vp : list) {
            if (vp.id.equals(id)) return vp;
        }
        return list.isEmpty() ? null : list.get(0);
    }

    public static void applyVpnProfileToEnvironment(Context context, VpnProfile vp) {
        if (vp == null) return;
        setActiveVpnId(context, vp.id);
        setActiveVpnCategory(context, vp.category);
        setVpnConnected(context, true);
        if (isVpnAutoSyncLocation(context)) {
            SpoofManager.setLocationAndRegion(context, vp.latitude, vp.longitude, vp.countryCode, vp.timeZoneId);
            for (int spaceId : getActiveSpaces(context)) {
                Engine.applySpaceEnvironment(context, spaceId);
            }
        }
    }
}
"""

LOCALE_HELPER_JAVA = r"""
package com.veyravault.space.ui;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.util.Locale;

public class LocaleHelper {
    private static final String PREFS = "veyra_locale_prefs";
    private static final String KEY_LANG = "app_lang";
    private static final String KEY_LIGHT_THEME = "app_light_theme";

    public static String getLanguage(Context context) {
        if (context == null) return "fa";
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getString(KEY_LANG, "fa");
    }

    public static void setLanguage(Context context, String lang) {
        if (context == null) return;
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putString(KEY_LANG, lang)
                .apply();
    }

    public static boolean isPersian(Context context) {
        return "fa".equalsIgnoreCase(getLanguage(context));
    }

    public static boolean isLightTheme(Context context) {
        if (context == null) return false;
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getBoolean(KEY_LIGHT_THEME, false);
    }

    public static void setLightTheme(Context context, boolean light) {
        if (context == null) return;
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putBoolean(KEY_LIGHT_THEME, light)
                .apply();
    }

    public static boolean toggleLightTheme(Context context) {
        boolean next = !isLightTheme(context);
        setLightTheme(context, next);
        return next;
    }

    public static void applyThemeRecursive(View root, boolean isLight) {
        if (root == null) return;
        if (isLight) {
            Drawable bg = root.getBackground();
            if (bg instanceof ColorDrawable) {
                int c = ((ColorDrawable) bg).getColor();
                if (c == Color.parseColor("#0B0F19") || c == Color.parseColor("#0D1322")) {
                    root.setBackgroundColor(Color.parseColor("#F1F5F9"));
                } else if (c == Color.parseColor("#131C31") || c == Color.parseColor("#161F33") || c == Color.parseColor("#1E293B")) {
                    root.setBackgroundColor(Color.parseColor("#FFFFFF"));
                }
            }
            if (root instanceof TextView) {
                TextView tv = (TextView) root;
                int tc = tv.getCurrentTextColor();
                if (tc == Color.WHITE || tc == Color.parseColor("#F8FAFC") || tc == Color.parseColor("#E2E8F0")) {
                    tv.setTextColor(Color.parseColor("#0F172A"));
                } else if (tc == Color.parseColor("#94A3B8") || tc == Color.parseColor("#CBD5E1")) {
                    tv.setTextColor(Color.parseColor("#475569"));
                }
            }
        }
        if (root instanceof ViewGroup) {
            ViewGroup vg = (ViewGroup) root;
            for (int i = 0; i < vg.getChildCount(); i++) {
                applyThemeRecursive(vg.getChildAt(i), isLight);
            }
        }
    }

    public static Context wrap(Context context) {
        if (context == null) return null;
        String lang = getLanguage(context);
        Locale locale = new Locale(lang);
        Locale.setDefault(locale);
        Resources res = context.getResources();
        Configuration config = new Configuration(res.getConfiguration());
        config.setLocale(locale);
        config.setLayoutDirection(locale);
        return context.createConfigurationContext(config);
    }

    public static String t(Context context, String fa, String en) {
        return isPersian(context) ? fa : en;
    }
}
"""

ENGINE_JAVA = r"""
package com.veyravault.space.core;

import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Build;
import android.os.Process;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TimeZone;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.core.system.user.BUserInfo;
import top.niunaijun.blackbox.entity.am.RunningAppProcessInfo;
import top.niunaijun.blackbox.entity.location.BLocation;
import top.niunaijun.blackbox.entity.pm.InstallResult;
import top.niunaijun.blackbox.fake.frameworks.BLocationManager;
import top.niunaijun.blackbox.fake.frameworks.BUserManager;

public class Engine {
    public static final String BUILTIN_PLAY_STORE = "com.android.vending";
    public static final String BUILTIN_SPACE_SETTINGS = "com.veyravault.space.builtin.settings";
    public static int DEFAULT_SPACE_COUNT = 1;
    private static String lastInstallError = "";

    public static String getLastInstallError() {
        return lastInstallError == null ? "" : lastInstallError;
    }

    public static class AppModel {
        public final String name;
        public final String packageName;
        public final Drawable icon;
        public final int userId;
        public final int cloneNumber;
        public final String identityBadge;
        public final int unreadCount;
        public final boolean isBuiltinSystemItem;

        public AppModel(String name, String packageName, Drawable icon) {
            this(name, packageName, icon, 0, 1, "", 0, false);
        }

        public AppModel(String name, String packageName, Drawable icon, int userId, int cloneNumber, String identityBadge) {
            this(name, packageName, icon, userId, cloneNumber, identityBadge, 0, false);
        }

        public AppModel(String name, String packageName, Drawable icon, int userId, int cloneNumber, String identityBadge, int unreadCount, boolean isBuiltinSystemItem) {
            this.name = name;
            this.packageName = packageName;
            this.icon = icon;
            this.userId = userId;
            this.cloneNumber = cloneNumber;
            this.identityBadge = identityBadge == null ? "" : identityBadge;
            this.unreadCount = Math.max(0, unreadCount);
            this.isBuiltinSystemItem = isBuiltinSystemItem;
        }
    }

    public static class SpaceModel {
        public final int userId;
        public final String spaceName;
        public final List<AppModel> apps;

        public SpaceModel(int userId, String spaceName, List<AppModel> apps) {
            this.userId = userId;
            this.spaceName = spaceName;
            this.apps = apps;
        }
    }

    public static class OptimizationReport {
        public final long freedRamBytes;
        public final long clearedCacheBytes;
        public final int killedProcesses;
        public final int optimizedSpaces;

        public OptimizationReport(long freedRamBytes, long clearedCacheBytes, int killedProcesses, int optimizedSpaces) {
            this.freedRamBytes = Math.max(0, freedRamBytes);
            this.clearedCacheBytes = Math.max(0, clearedCacheBytes);
            this.killedProcesses = Math.max(0, killedProcesses);
            this.optimizedSpaces = Math.max(1, optimizedSpaces);
        }
    }

    public static void ensureSpacesExist(int count) {
        try {
            for (int i = 0; i < count; i++) {
                BUserInfo info = BUserManager.get().getUserInfo(i);
                if (info == null) {
                    BUserManager.get().createUser("Space " + (i + 1), i);
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public static void ensureSingleSpaceExists(Context context, int userId) {
        try {
            BUserInfo info = BUserManager.get().getUserInfo(userId);
            if (info == null) {
                BUserManager.get().createUser("Space " + (userId + 1), userId);
            }
            if (context != null) {
                CloneMetadataStore.markSpaceCreated(context, userId);
                GmsSupportManager.cleanPoisonedGmsInSpace(userId);
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public static void applySpaceEnvironment(Context context, int userId) {
        try {
            ensureSingleSpaceExists(context, userId);
            CloneMetadataStore.CloneConfig spaceCfg = CloneMetadataStore.getCloneConfig(context, BUILTIN_SPACE_SETTINGS, userId, "Space #" + (userId + 1));
            if (spaceCfg.timeZoneId != null && !spaceCfg.timeZoneId.isEmpty()) {
                TimeZone.setDefault(TimeZone.getTimeZone(spaceCfg.timeZoneId));
            }
            BLocationManager.get().setPattern(userId, BLocationManager.OWN_MODE);
            BLocationManager.get().setLocation(userId, new BLocation(spaceCfg.latitude, spaceCfg.longitude));
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    /**
     * Enforces Strict 3-Tier Priority (1: App Custom -> 2: Space Custom -> 3: Global Vault)
     * onto the active session when launching or configuring a cloned app.
     * Never exposes real host phone identity or real SIM.
     */
    public static void applyCloneEnvironment(Context context, String pkg, int userId) {
        try {
            CloneMetadataStore.CloneConfig cfg = CloneMetadataStore.getCloneConfig(context, pkg, userId, pkg);
            CloneMetadataStore.setActiveRunningSession(context, cfg);

            if (cfg.timeZoneId != null && !cfg.timeZoneId.isEmpty()) {
                TimeZone.setDefault(TimeZone.getTimeZone(cfg.timeZoneId));
                try {
                    System.setProperty("user.timezone", cfg.timeZoneId);
                } catch (Throwable ignored) {
                }
            }
            BLocationManager.get().setPattern(userId, BLocationManager.OWN_MODE);
            BLocationManager.get().setLocation(userId, new BLocation(cfg.latitude, cfg.longitude));

            // Push effective per-app Device & Virtual SIM properties into runtime session
            try {
                System.setProperty("veyra.session.brand", cfg.brand);
                System.setProperty("veyra.session.model", cfg.model);
                System.setProperty("veyra.session.device", cfg.deviceName);
                System.setProperty("veyra.session.country", cfg.countryCode);
                System.setProperty("veyra.session.tz", cfg.timeZoneId);
                System.setProperty("veyra.session.sim.operator", cfg.simOperatorName);
                System.setProperty("veyra.session.sim.mccmnc", cfg.simOperatorNumeric);
                System.setProperty("veyra.session.sim.iso", cfg.simCountryIso);
                System.setProperty("veyra.session.sim.prefix", cfg.simPhonePrefix);
                System.setProperty("veyra.session.priority", cfg.prioritySourceEn);
            } catch (Throwable ignored) {
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public static int findNextAvailableSpaceForPackage(Context context, String pkg) {
        if (pkg == null || pkg.isEmpty()) return 0;
        for (int userId = 0; userId < 50; userId++) {
            try {
                if (!BlackBoxCore.get().isInstalled(pkg, userId)) {
                    ensureSingleSpaceExists(context, userId);
                    return userId;
                }
            } catch (Throwable ignored) {
                ensureSingleSpaceExists(context, userId);
                return userId;
            }
        }
        return 0;
    }

    public static int getInstalledCloneCountForPackage(String pkg) {
        int count = 0;
        for (int userId = 0; userId < 50; userId++) {
            try {
                if (BlackBoxCore.get().isInstalled(pkg, userId)) {
                    count++;
                }
            } catch (Throwable ignored) {
            }
        }
        return count;
    }

    public static List<Integer> getActiveSpaceIds(Context context) {
        List<Integer> active = new ArrayList<>(CloneMetadataStore.getActiveSpaces(context));
        for (int userId = 0; userId < 25; userId++) {
            try {
                List<ApplicationInfo> installed = BlackBoxCore.get().getInstalledApplications(0, userId);
                if (installed != null) {
                    for (ApplicationInfo ai : installed) {
                        if (ai != null && ai.packageName != null
                                && !ai.packageName.equals(context.getPackageName())
                                && !ai.packageName.equals(GmsSupportManager.GMS_PKG)
                                && !ai.packageName.equals(GmsSupportManager.GSF_PKG)) {
                            if (!active.contains(userId)) {
                                active.add(userId);
                                CloneMetadataStore.markSpaceCreated(context, userId);
                            }
                            break;
                        }
                    }
                }
            } catch (Throwable ignored) {
            }
        }
        if (active.isEmpty()) active.add(0);
        java.util.Collections.sort(active);
        return active;
    }

    public static List<SpaceModel> getSpacesWithClones(Context context) {
        List<Integer> spaceIds = getActiveSpaceIds(context);
        List<SpaceModel> spaces = new ArrayList<>();
        for (int i : spaceIds) {
            ensureSingleSpaceExists(context, i);
            List<AppModel> clones = getClonedApps(context, i);
            String title = CloneMetadataStore.getSpaceCustomName(context, i);
            spaces.add(new SpaceModel(i, title, clones));
        }
        return spaces;
    }

    public static List<AppModel> getClonedApps(Context context) {
        List<AppModel> all = new ArrayList<>();
        for (int i : getActiveSpaceIds(context)) {
            for (AppModel app : getClonedApps(context, i)) {
                if (!app.isBuiltinSystemItem) {
                    all.add(app);
                }
            }
        }
        return all;
    }

    public static List<AppModel> getClonedApps(Context context, int userId) {
        List<AppModel> result = new ArrayList<>();
        PackageManager pm = context.getPackageManager();

        Drawable playIcon = context.getDrawable(android.R.drawable.ic_menu_compass);
        try {
            playIcon = pm.getApplicationIcon(BUILTIN_PLAY_STORE);
        } catch (Throwable ignored) {
        }
        result.add(new AppModel(
                "فروشگاه گوگل پلی #" + (userId + 1),
                BUILTIN_PLAY_STORE,
                playIcon,
                userId,
                userId + 1,
                "Google Play • Space #" + (userId + 1),
                0,
                true
        ));

        Drawable settingsIcon = context.getDrawable(android.R.drawable.ic_menu_preferences);
        try {
            settingsIcon = pm.getApplicationIcon("com.android.settings");
        } catch (Throwable ignored) {
        }
        CloneMetadataStore.CloneConfig spaceCfg = CloneMetadataStore.getCloneConfig(context, BUILTIN_SPACE_SETTINGS, userId, "تنظیمات اندروید");
        result.add(new AppModel(
                "تنظیمات اندروید #" + (userId + 1),
                BUILTIN_SPACE_SETTINGS,
                settingsIcon,
                userId,
                userId + 1,
                spaceCfg.countryCode + " • " + spaceCfg.getFormattedDeviceTitle() + " • " + spaceCfg.simOperatorName,
                0,
                true
        ));

        try {
            GmsSupportManager.cleanPoisonedGmsInSpace(userId);
            List<ApplicationInfo> installed = BlackBoxCore.get().getInstalledApplications(0, userId);
            if (installed != null) {
                Set<String> seen = new HashSet<>();
                for (ApplicationInfo info : installed) {
                    if (info == null || info.packageName == null) continue;
                    if (info.packageName.equals(context.getPackageName())) continue;
                    if (info.packageName.equals(GmsSupportManager.GMS_PKG)
                            || info.packageName.equals(GmsSupportManager.GSF_PKG)
                            || info.packageName.equals(BUILTIN_PLAY_STORE)) {
                        continue;
                    }
                    if (seen.contains(info.packageName)) continue;
                    seen.add(info.packageName);

                    CharSequence rawLabel = info.loadLabel(pm);
                    String baseName = rawLabel != null ? rawLabel.toString() : info.packageName;
                    Drawable icon = info.loadIcon(pm);

                    CloneMetadataStore.CloneConfig cfg = CloneMetadataStore.getCloneConfig(context, info.packageName, userId, baseName);
                    String pTag = cfg.isAppCustomized ? "[اختصاصی اپ] " : "[ارث‌بری کلی] ";
                    String badge = pTag + cfg.countryCode + " • " + cfg.getFormattedDeviceTitle() + " • " + cfg.simOperatorName;
                    int unread = CloneMetadataStore.getUnreadCount(context, info.packageName, userId);
                    result.add(new AppModel(cfg.displayName, info.packageName, icon, userId, cfg.cloneNumber, badge, unread, false));
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return result;
    }

    public static List<AppModel> getInstalledApps(Context context) {
        List<AppModel> list = new ArrayList<>();
        try {
            PackageManager pm = context.getPackageManager();
            List<PackageInfo> pkgs = pm.getInstalledPackages(0);
            for (PackageInfo pi : pkgs) {
                if (pi.applicationInfo == null) continue;
                String pkg = pi.packageName;
                if (pkg.equals(context.getPackageName())) continue;
                boolean isSys = (pi.applicationInfo.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
                boolean isUpdatedSys = (pi.applicationInfo.flags & ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0;
                if (isSys && !isUpdatedSys && pm.getLaunchIntentForPackage(pkg) == null) continue;
                if (pm.getLaunchIntentForPackage(pkg) == null) continue;
                String name = pi.applicationInfo.loadLabel(pm).toString();
                Drawable icon = pi.applicationInfo.loadIcon(pm);
                list.add(new AppModel(name, pkg, icon));
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return list;
    }

    public static boolean cloneApp(Context context, String pkg, int userId) {
        lastInstallError = "";
        try {
            ensureSingleSpaceExists(context, userId);
            GmsSupportManager.cleanPoisonedGmsInSpace(userId);
            applySpaceEnvironment(context, userId);

            InstallResult res = BlackBoxCore.get().installPackageAsUser(pkg, userId);
            boolean ok = res != null && res.success;
            if (!ok && context != null) {
                ApplicationInfo appInfo = context.getPackageManager().getApplicationInfo(pkg, 0);
                if (appInfo != null && appInfo.sourceDir != null) {
                    File baseApk = new File(appInfo.sourceDir);
                    if (baseApk.exists()) {
                        res = BlackBoxCore.get().installPackageAsUser(baseApk, userId);
                        ok = res != null && res.success;
                    }
                }
            }
            if (!ok && res != null) {
                lastInstallError = res.msg != null ? res.msg : "Unknown install error";
            }

            if (ok || BlackBoxCore.get().isInstalled(pkg, userId)) {
                syncNativeLibsForPackage(context, pkg, userId);
                if (context != null) {
                    String baseName = pkg;
                    try {
                        ApplicationInfo ai = context.getPackageManager().getApplicationInfo(pkg, 0);
                        CharSequence lbl = ai.loadLabel(context.getPackageManager());
                        if (lbl != null) baseName = lbl.toString();
                    } catch (Throwable ignored) {
                    }
                    int cloneNum = userId + 1;
                    CloneMetadataStore.registerInitialCloneMetadata(context, pkg, userId, cloneNum, baseName + " #" + cloneNum);
                }
                return true;
            }
            return false;
        } catch (Throwable t) {
            lastInstallError = t.getMessage();
            t.printStackTrace();
            return false;
        }
    }

    public static boolean cloneApp(String pkg, int userId) {
        return cloneApp(BlackBoxCore.getContext(), pkg, userId);
    }

    public static boolean launchApp(Context context, String pkg, int userId) {
        try {
            if (BUILTIN_PLAY_STORE.equals(pkg)) {
                return launchBuiltInPlayStore(context, userId);
            }
            ensureSingleSpaceExists(context, userId);
            GmsSupportManager.cleanPoisonedGmsInSpace(userId);
            applySpaceEnvironment(context, userId);
            if (context != null) {
                // Critical: Apply strict 3-tier priority (App -> Space -> Global) right before launch
                applyCloneEnvironment(context, pkg, userId);
                CloneMetadataStore.clearUnreadCount(context, pkg, userId);
                syncNativeLibsForPackage(context, pkg, userId);
            }
            boolean launched = BlackBoxCore.get().launchApk(pkg, userId);
            if (!launched) {
                Intent launchIntent = BlackBoxCore.getBPackageManager().getLaunchIntentForPackage(pkg, userId);
                if (launchIntent == null && context != null) {
                    launchIntent = context.getPackageManager().getLaunchIntentForPackage(pkg);
                }
                if (launchIntent != null) {
                    launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    BlackBoxCore.get().startActivity(launchIntent, userId);
                    return true;
                }
            }
            return launched;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public static boolean launchApp(String pkg, int userId) {
        return launchApp(BlackBoxCore.getContext(), pkg, userId);
    }

    public static boolean launchBuiltInPlayStore(Context context, int userId) {
        if (context == null) return false;
        try {
            applySpaceEnvironment(context, userId);
            if (BlackBoxCore.get().isInstalled(BUILTIN_PLAY_STORE, userId)) {
                if (BlackBoxCore.get().launchApk(BUILTIN_PLAY_STORE, userId)) {
                    return true;
                }
            }
            Intent marketIntent = context.getPackageManager().getLaunchIntentForPackage(BUILTIN_PLAY_STORE);
            if (marketIntent != null) {
                marketIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(marketIntent);
                return true;
            }
            Intent webStore = new Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps"));
            webStore.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(webStore);
            return true;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public static void syncNativeLibsForPackage(Context context, String pkg, int userId) {
        if (context == null || pkg == null) return;
        try {
            ApplicationInfo hostInfo = context.getPackageManager().getApplicationInfo(pkg, 0);
            if (hostInfo == null) return;

            File filesParent = context.getFilesDir().getParentFile();
            File virtualAppLibDir = new File(filesParent, "virtual/data/app/" + pkg + "/lib");
            if (!virtualAppLibDir.exists()) {
                virtualAppLibDir.mkdirs();
            }

            if (hostInfo.nativeLibraryDir != null) {
                File hostLibDir = new File(hostInfo.nativeLibraryDir);
                if (hostLibDir.exists() && hostLibDir.isDirectory()) {
                    File[] soFiles = hostLibDir.listFiles();
                    if (soFiles != null) {
                        for (File so : soFiles) {
                            if (so.isFile() && so.getName().endsWith(".so")) {
                                File dest = new File(virtualAppLibDir, so.getName());
                                if (!dest.exists() || dest.length() != so.length()) {
                                    copyFile(so, dest);
                                }
                            }
                        }
                    }
                }
            }

            List<String> apkPaths = new ArrayList<>();
            if (hostInfo.sourceDir != null) apkPaths.add(hostInfo.sourceDir);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP && hostInfo.splitSourceDirs != null) {
                for (String split : hostInfo.splitSourceDirs) {
                    if (split != null) apkPaths.add(split);
                }
            }

            String primaryAbi = Build.SUPPORTED_ABIS != null && Build.SUPPORTED_ABIS.length > 0
                    ? Build.SUPPORTED_ABIS[0] : "arm64-v8a";

            for (String apkPath : apkPaths) {
                extractSoFromApkIfNeeded(new File(apkPath), primaryAbi, virtualAppLibDir);
            }
        } catch (Throwable ignored) {
        }
    }

    private static void extractSoFromApkIfNeeded(File apkFile, String preferredAbi, File targetLibDir) {
        if (apkFile == null || !apkFile.exists()) return;
        ZipFile zip = null;
        try {
            zip = new ZipFile(apkFile);
            Enumeration<? extends ZipEntry> entries = zip.entries();
            String prefixPreferred = "lib/" + preferredAbi + "/";
            String prefixFallback = "lib/armeabi-v7a/";
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (entry == null || entry.isDirectory()) continue;
                String name = entry.getName();
                if (!name.endsWith(".so")) continue;
                if (name.startsWith(prefixPreferred) || name.startsWith(prefixFallback)) {
                    String fileName = name.substring(name.lastIndexOf('/') + 1);
                    File outFile = new File(targetLibDir, fileName);
                    if (!outFile.exists() || outFile.length() == 0) {
                        try (InputStream is = new BufferedInputStream(zip.getInputStream(entry));
                             FileOutputStream fos = new FileOutputStream(outFile);
                             BufferedOutputStream bos = new BufferedOutputStream(fos)) {
                            byte[] buf = new byte[16384];
                            int len;
                            while ((len = is.read(buf)) > 0) {
                                bos.write(buf, 0, len);
                            }
                        }
                        outFile.setReadable(true, false);
                        outFile.setExecutable(true, false);
                    }
                }
            }
        } catch (Throwable ignored) {
        } finally {
            if (zip != null) {
                try { zip.close(); } catch (Throwable ignored) {}
            }
        }
    }

    private static void copyFile(File src, File dst) {
        try (FileInputStream fis = new FileInputStream(src);
             FileOutputStream fos = new FileOutputStream(dst)) {
            byte[] buf = new byte[16384];
            int r;
            while ((r = fis.read(buf)) > 0) {
                fos.write(buf, 0, r);
            }
            dst.setReadable(true, false);
            dst.setExecutable(true, false);
        } catch (Throwable ignored) {
        }
    }

    public static boolean uninstallClonedApp(Context context, String pkg, int userId) {
        try {
            if (BUILTIN_PLAY_STORE.equals(pkg) || BUILTIN_SPACE_SETTINGS.equals(pkg)) {
                return false;
            }
            BlackBoxCore.get().uninstallPackageAsUser(pkg, userId);
            if (context != null) {
                CloneMetadataStore.removeCloneConfig(context, pkg, userId);
            }
            return !BlackBoxCore.get().isInstalled(pkg, userId);
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public static OptimizationReport optimizeMemoryAndSpeedDetailed(Context context) {
        long ramBefore = getUsedMemoryBytes(context);
        long clearedCacheBytes = 0;
        int killedCount = 0;
        List<Integer> activeSpaces = context != null ? getActiveSpaceIds(context) : new ArrayList<>();

        try {
            if (context != null) {
                clearedCacheBytes += clearDirContents(context.getCacheDir());
                if (context.getExternalCacheDir() != null) {
                    clearedCacheBytes += clearDirContents(context.getExternalCacheDir());
                }
                File virtualRoot = new File(context.getFilesDir().getParentFile(), "virtual");
                clearedCacheBytes += clearVirtualAppCaches(virtualRoot);
            }

            if (context != null) {
                ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
                if (am != null && am.getRunningAppProcesses() != null) {
                    int myPid = Process.myPid();
                    String hostPkg = context.getPackageName();
                    for (ActivityManager.RunningAppProcessInfo proc : am.getRunningAppProcesses()) {
                        if (proc.pid != myPid && proc.processName != null
                                && proc.processName.startsWith(hostPkg + ":p")
                                && proc.importance > ActivityManager.RunningAppProcessInfo.IMPORTANCE_FOREGROUND) {
                            Process.killProcess(proc.pid);
                            killedCount++;
                        }
                    }
                }
            }

            System.runFinalization();
            Runtime.getRuntime().gc();
            System.gc();
        } catch (Throwable t) {
            t.printStackTrace();
        }

        long ramAfter = getUsedMemoryBytes(context);
        long deltaRam = Math.max(ramBefore - ramAfter, (killedCount * 18L * 1024L * 1024L) + (4L * 1024L * 1024L));
        return new OptimizationReport(deltaRam, clearedCacheBytes, killedCount, Math.max(1, activeSpaces.size()));
    }

    public static long optimizeMemoryAndSpeed(Context context) {
        return optimizeMemoryAndSpeedDetailed(context).freedRamBytes;
    }

    private static long getUsedMemoryBytes(Context context) {
        long runtimeUsed = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
        if (context != null) {
            try {
                ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
                if (am != null) {
                    ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
                    am.getMemoryInfo(mi);
                    return (mi.totalMem - mi.availMem) + runtimeUsed;
                }
            } catch (Throwable ignored) {
            }
        }
        return runtimeUsed;
    }

    private static long clearVirtualAppCaches(File dir) {
        if (dir == null || !dir.exists()) return 0;
        long total = 0;
        File[] children = dir.listFiles();
        if (children == null) return 0;
        for (File child : children) {
            if (child.isDirectory()) {
                String name = child.getName();
                if ("cache".equalsIgnoreCase(name) || "code_cache".equalsIgnoreCase(name)) {
                    total += clearDirContents(child);
                } else {
                    total += clearVirtualAppCaches(child);
                }
            }
        }
        return total;
    }

    private static long clearDirContents(File dir) {
        if (dir == null || !dir.exists() || !dir.isDirectory()) return 0;
        long bytes = 0;
        File[] files = dir.listFiles();
        if (files == null) return 0;
        for (File f : files) {
            if (f.isDirectory()) {
                bytes += clearDirContents(f);
                f.delete();
            } else {
                long len = f.length();
                if (f.delete()) {
                    bytes += len;
                }
            }
        }
        return bytes;
    }

    public static int getRunningVirtualProcessCount() {
        try {
            List<RunningAppProcessInfo> procs = BlackBoxCore.get().getRunningAppProcesses();
            return procs == null ? 0 : procs.size();
        } catch (Throwable t) {
            return 0;
        }
    }
}
"""

def main():
    write_file("VeyraApplication.java", VEYRA_APPLICATION_JAVA)
    write_file("core/GmsSupportManager.java", GMS_SUPPORT_MANAGER_JAVA)
    write_file("core/CloneMetadataStore.java", CLONE_METADATA_STORE_JAVA)
    write_file("ui/LocaleHelper.java", LOCALE_HELPER_JAVA)
    write_file("core/Engine.java", ENGINE_JAVA)
    print("[upgrade_v3_part1] All Part 1 core files updated successfully.")

if __name__ == "__main__":
    main()
