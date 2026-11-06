#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.join(ROOT, "app")
MAIN_DIR = os.path.join(APP_DIR, "src", "main")
JAVA_BASE = os.path.join(MAIN_DIR, "java", "com", "veyravault", "space")
RES_DIR = os.path.join(MAIN_DIR, "res")


def write_file(rel_path, content):
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.lstrip())
    print(f"[v3-part1] Wrote: {rel_path}")


def clean_legacy_sources():
    if os.path.exists(JAVA_BASE):
        shutil.rmtree(JAVA_BASE)
    layout_dir = os.path.join(RES_DIR, "layout")
    if os.path.exists(layout_dir):
        shutil.rmtree(layout_dir)


def patch_app_build_gradle():
    gradle_path = os.path.join(APP_DIR, "build.gradle")
    if not os.path.exists(gradle_path):
        return
    with open(gradle_path, "r", encoding="utf-8") as f:
        txt = f.read()
    if "org.osmdroid:osmdroid-android" not in txt:
        txt = txt.replace(
            "dependencies {",
            "dependencies {\n    implementation 'org.osmdroid:osmdroid-android:6.1.14'",
            1,
        )
    txt = txt.replace("versionCode 1", "versionCode 3").replace("versionCode 2", "versionCode 3")
    txt = txt.replace('versionName "1.0.0"', 'versionName "3.0.0"').replace('versionName "2.0.0"', 'versionName "3.0.0"')
    with open(gradle_path, "w", encoding="utf-8") as f:
        f.write(txt)


def generate_resources():
    write_file(
        "app/src/main/assets/NOTICE_APACHE_2.txt",
        """VeyraVault v3.0 - Multi-Space & Privacy Virtualization Platform
Contact Email: Vaultveyra@gmail.com | Official Telegram: https://t.me/VaultVeyra
Licensed under the Apache License, Version 2.0.
Powered by open-source BlackBox Virtual Engine (https://github.com/ALEX5402/NewBlackbox).
""",
    )

    write_file(
        "app/src/main/res/xml/device_admin_policies.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies><watch-login /></uses-policies>
</device-admin>
""",
    )

    write_file(
        "app/src/main/res/drawable/ic_launcher.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#0F172A" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#1E293B" android:pathData="M54,14L88,30V56C88,77.5 73.5,95.2 54,100C34.5,95.2 20,77.5 20,56V30L54,14Z"/>
    <path android:fillColor="#38BDF8" android:pathData="M54,22L80,34.5V55C80,72.2 68.9,86.8 54,91C39.1,86.8 28,72.2 28,55V34.5L54,22Z"/>
    <path android:fillColor="#0F172A" android:pathData="M42,42L54,72L66,42H59L54,56L49,42H42Z"/>
</vector>
""",
    )

    icons = {
        "ic_nav_dashboard.xml": "M3,13h8V3H3V13zM3,21h8v-6H3V21zM13,21h8V11h-8V21zM13,3v6h8V3H13z",
        "ic_nav_spaces.xml": "M4,8h4V4H4V8zM10,20h4v-4h-4V20zM4,20h4v-4H4V20zM4,14h4v-4H4V14zM10,14h4v-4h-4V14zM16,4v4h4V4H16zM10,8h4V4h-4V8zM16,14h4v-4h-4V14zM16,20h4v-4h-4V20z",
        "ic_nav_add.xml": "M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6V13z",
        "ic_nav_guide.xml": "M18,2H6C4.9,2 4,2.9 4,4v16c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V4C20,2.9 19.1,2 18,2zM6,4h5v8l-2.5,-1.5L6,12V4z",
        "ic_nav_settings.xml": "M12,8c-2.21,0 -4,1.79 -4,4s1.79,4 4,4s4,-1.79 4,-4S14.21,8 12,8zM19.14,12.94l2.03,-1.58l-1.92,-3.32l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81h-4.8l-0.84,5.25c-0.59,0.24 -1.13,0.56 -1.62,0.94l-2.39,-0.96l-1.92,3.32l2.03,1.58L2.83,14.52l1.92,3.32l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94L9.6,21.19h4.8l0.84,-3.37c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96l1.92,-3.32L19.14,12.94z",
    }
    for name, path_data in icons.items():
        write_file(
            f"app/src/main/res/drawable/{name}",
            f"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="{path_data}"/>
</vector>
""",
        )

    write_file(
        "app/src/main/res/values/strings.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="disguise_calculator">Calculator+</string>
    <string name="disguise_calendar">Smart Calendar</string>
    <string name="disguise_notes">Private Notes</string>
</resources>
""",
    )

    write_file(
        "app/src/main/res/values/styles.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="android:Theme.Material.NoActionBar">
        <item name="android:colorPrimary">#0F172A</item>
        <item name="android:colorPrimaryDark">#090D16</item>
        <item name="android:colorAccent">#38BDF8</item>
        <item name="android:windowBackground">#090D16</item>
        <item name="android:statusBarColor">#090D16</item>
        <item name="android:navigationBarColor">#0F172A</item>
    </style>
</resources>
""",
    )

    write_file(
        "app/src/main/AndroidManifest.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" tools:ignore="ScopedStorage" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.REQUEST_DELETE_PACKAGES" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />

    <application
        android:name="com.veyravault.space.VeyraApplication"
        android:allowBackup="false"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@drawable/ic_launcher"
        android:supportsRtl="true"
        android:theme="@style/AppTheme"
        android:usesCleartextTraffic="true"
        tools:ignore="GoogleAppIndexingWarning,UnusedAttribute">

        <activity
            android:name="com.veyravault.space.ui.MainActivity"
            android:exported="true"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity-alias
            android:name="com.veyravault.space.AliasCalculator"
            android:enabled="false" android:exported="true"
            android:icon="@android:drawable/ic_dialog_dialer"
            android:label="@string/disguise_calculator"
            android:targetActivity="com.veyravault.space.ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity-alias
            android:name="com.veyravault.space.AliasCalendar"
            android:enabled="false" android:exported="true"
            android:icon="@android:drawable/ic_menu_my_calendar"
            android:label="@string/disguise_calendar"
            android:targetActivity="com.veyravault.space.ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity-alias
            android:name="com.veyravault.space.AliasNotes"
            android:enabled="false" android:exported="true"
            android:icon="@android:drawable/ic_menu_edit"
            android:label="@string/disguise_notes"
            android:targetActivity="com.veyravault.space.ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity android:name="com.veyravault.space.ui.AddAppActivity" android:exported="false" />
        <activity android:name="com.veyravault.space.ui.GlobalEnvironmentActivity" android:exported="false" />
        <activity android:name="com.veyravault.space.ui.SetLocationActivity" android:exported="false" />
        <activity android:name="com.veyravault.space.ui.SecuritySettingsActivity" android:exported="false" />
        <activity android:name="com.veyravault.space.ui.SecurityLockActivity" android:exported="false" android:launchMode="singleTop" />
        <activity android:name="com.veyravault.space.ui.GuideActivity" android:exported="false" />
        <activity android:name="com.veyravault.space.ui.AboutActivity" android:exported="false" />

        <receiver
            android:name="com.veyravault.space.security.VaultDeviceAdminReceiver"
            android:description="@string/app_name"
            android:label="@string/app_name"
            android:permission="android.permission.BIND_DEVICE_ADMIN"
            android:exported="true">
            <meta-data android:name="android.app.device_admin" android:resource="@xml/device_admin_policies" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
                <action android:name="android.app.action.DEVICE_ADMIN_DISABLE_REQUESTED" />
                <action android:name="android.app.action.DEVICE_ADMIN_DISABLED" />
            </intent-filter>
        </receiver>
    </application>
</manifest>
""",
    )


def generate_java_core():
    write_file(
        "app/src/main/java/com/veyravault/space/VeyraApplication.java",
        """package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.helper.GmsSupportManager;
import com.veyravault.space.helper.LocaleHelper;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.configuration.ClientConfiguration;

public class VeyraApplication extends Application {
    private static Context sContext;
    public static Context getAppContext() { return sContext; }

    @Override
    protected void attachBaseContext(Context base) {
        sContext = base;
        super.attachBaseContext(LocaleHelper.onAttach(base));
        try {
            BlackBoxCore.get().doAttachBaseContext(base, new ClientConfiguration() {
                @Override public String getHostPackageName() { return base.getPackageName(); }
                @Override public boolean isEnableDaemonService() { return true; }
                public boolean isHideRoot() { return true; }
                public boolean isHideXposed() { return true; }
            });
        } catch (Throwable t) { t.printStackTrace(); }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        sContext = this;
        try {
            BlackBoxCore.get().doCreate();
            CloneMetadataStore.ensureDefaultsInitialized(this);
            GmsSupportManager.autoInitializeGmsIfNeeded(this);
            VirtualHookManager.applyGlobalEnvironmentHooks(this);
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/helper/JalaliClockUtil.java",
        """package com.veyravault.space.helper;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

public class JalaliClockUtil {
    private static final String[] MONTHS_FA = {"فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"};
    private static final String[] MONTHS_EN = {"Farvardin","Ordibehesht","Khordad","Tir","Mordad","Shahrivar","Mehr","Aban","Azar","Dey","Bahman","Esfand"};
    private static final String[] DAYS_FA = {"یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه"};
    private static final String[] DAYS_EN = {"Sun","Mon","Tue","Wed","Thu","Fri","Sat"};

    public static String getTehranTimeString() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("Asia/Tehran"));
        return sdf.format(new Date());
    }

    public static String getTehranTime() {
        return getTehranTimeString();
    }

    public static String getNewYorkTimeString() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String getNewYorkTime() {
        return getNewYorkTimeString();
    }

    public static String getNewYorkGregorianDate() {
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String getNewYorkGregorianDate(boolean isFa) {
        return getNewYorkGregorianDate();
    }

    public static String getTehranJalaliDate(boolean isFa) {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Tehran"), Locale.US);
        int[] j = gregorianToJalali(cal.get(Calendar.YEAR), cal.get(Calendar.MONTH) + 1, cal.get(Calendar.DAY_OF_MONTH));
        int dow = cal.get(Calendar.DAY_OF_WEEK) - 1;
        if (isFa) {
            return toPersianDigits(DAYS_FA[dow] + " " + j[2] + " " + MONTHS_FA[j[1] - 1] + " " + j[0]);
        }
        return DAYS_EN[dow] + ", " + j[2] + " " + MONTHS_EN[j[1] - 1] + " " + j[0];
    }

    public static int[] gregorianToJalali(int gy, int gm, int gd) {
        int[] g_d_m = {0,31,59,90,120,151,181,212,243,273,304,334};
        int gy2 = (gm > 2) ? (gy + 1) : gy;
        int days = 355666 + (365 * gy) + ((gy2 + 3) / 4) - ((gy2 + 99) / 100) + ((gy2 + 399) / 400) + gd + g_d_m[gm - 1];
        int jy = -1595 + (33 * (days / 12053));
        days %= 12053;
        jy += 4 * (days / 1461);
        days %= 1461;
        if (days > 365) { jy += (days - 1) / 365; days = (days - 1) % 365; }
        int jm = (days < 186) ? 1 + (days / 31) : 7 + ((days - 186) / 30);
        int jd = 1 + ((days < 186) ? (days % 31) : ((days - 186) % 30));
        return new int[]{jy, jm, jd};
    }

    public static String toPersianDigits(String s) {
        if (s == null) return "";
        char[] p = {'۰','۱','۲','۳','۴','۵','۶','۷','۸','۹'};
        StringBuilder sb = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            sb.append((c >= '0' && c <= '9') ? p[c - '0'] : c);
        }
        return sb.toString();
    }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/helper/LocaleHelper.java",
        """package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.os.Build;
import java.util.Locale;

public class LocaleHelper {
    private static final String PREF = "veyra_locale_prefs";
    private static final String KEY = "app_lang";

    public static Context onAttach(Context ctx) { return setLocale(ctx, getLanguage(ctx)); }
    public static String getLanguage(Context ctx) { return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).getString(KEY, "fa"); }
    public static boolean isPersian(Context ctx) { return "fa".equalsIgnoreCase(getLanguage(ctx)); }
    public static Context toggleLanguage(Context ctx) { return setLocale(ctx, isPersian(ctx) ? "en" : "fa"); }

    public static Context setLocale(Context ctx, String lang) {
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putString(KEY, lang).apply();
        Locale locale = new Locale(lang);
        Locale.setDefault(locale);
        Resources res = ctx.getResources();
        Configuration cfg = new Configuration(res.getConfiguration());
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            cfg.setLocale(locale);
            cfg.setLayoutDirection(locale);
            return ctx.createConfigurationContext(cfg);
        }
        cfg.locale = locale;
        res.updateConfiguration(cfg, res.getDisplayMetrics());
        return ctx;
    }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/helper/BaseActivity.java",
        """package com.veyravault.space.helper;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.widget.LinearLayout;
import com.veyravault.space.security.SecurityManager;
import com.veyravault.space.ui.SecurityLockActivity;

public class BaseActivity extends Activity {
    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.onAttach(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        applyDirection();
        Window w = getWindow();
        if (w != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            w.setStatusBarColor(Color.parseColor("#090D16"));
            w.setNavigationBarColor(Color.parseColor("#0F172A"));
        }
    }

    public void applyDirection() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            getWindow().getDecorView().setLayoutDirection(isPersian() ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        }
    }

    public boolean isFa() { return LocaleHelper.isPersian(this); }
    public boolean isPersian() { return LocaleHelper.isPersian(this); }
    public String tr(String fa, String en) { return isPersian() ? fa : en; }
    public int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }

    public void switchLanguageInstant() {
        LocaleHelper.toggleLanguage(this);
        recreate();
    }

    public void triggerQuickLock() {
        if (SecurityManager.isLockEnabled(this)) {
            SecurityManager.setSessionUnlocked(false);
            startActivity(new Intent(this, SecurityLockActivity.class));
        }
    }

    public GradientDrawable roundedBg(String fillHex, String strokeHex, int radiusDp, int strokeWidthDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(fillHex));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeWidthDp > 0) gd.setStroke(dp(strokeWidthDp), Color.parseColor(strokeHex));
        return gd;
    }

    public LinearLayout makeCard(String fillHex, String strokeHex, int radiusDp) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(roundedBg(fillHex, strokeHex, radiusDp, 1));
        int p = dp(14);
        card.setPadding(p, p, p, p);
        return card;
    }
}
""",
    )

    gms_src = """package %PKG%;

import android.content.Context;
import java.lang.reflect.Method;
import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    private static final String PREF = "veyra_gms_prefs";
    private static final String KEY = "gms_auto_enabled";

    public static boolean isGmsEnabled(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).getBoolean(KEY, true);
    }

    public static void setGmsEnabled(Context ctx, boolean enabled) {
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putBoolean(KEY, enabled).apply();
        if (enabled) installGmsForAllSpaces();
    }

    public static boolean enableGmsAcrossAllSpaces(Context ctx) {
        setGmsEnabled(ctx, true);
        return installGmsForAllSpaces();
    }

    public static void autoInitializeGmsIfNeeded(Context ctx) {
        if (isGmsEnabled(ctx)) installGmsForAllSpaces();
    }

    public static boolean ensureGmsForSpace(int userId) {
        try {
            BlackBoxCore core = BlackBoxCore.get();
            for (Method m : core.getClass().getMethods()) {
                if (m.getName().equalsIgnoreCase("installGms") && m.getParameterTypes().length == 1) {
                    m.invoke(core, userId);
                    return true;
                }
            }
        } catch (Throwable ignored) {}
        return true;
    }

    public static boolean installGmsForAllSpaces() {
        for (int i = 0; i < 5; i++) ensureGmsForSpace(i);
        return true;
    }
}
"""
    write_file("app/src/main/java/com/veyravault/space/helper/GmsSupportManager.java", gms_src.replace("%PKG%", "com.veyravault.space.helper"))
    write_file("app/src/main/java/com/veyravault/space/core/GmsSupportManager.java", gms_src.replace("%PKG%", "com.veyravault.space.core"))

    write_file(
        "app/src/main/java/com/veyravault/space/helper/AppDisguiseManager.java",
        """package com.veyravault.space.helper;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;

public class AppDisguiseManager {
    private static final String PREF = "veyra_disguise_prefs";
    private static final String KEY = "disguise_mode_v3";

    public static final String MODE_DEFAULT = "default";
    public static final String MODE_CALCULATOR = "calculator";
    public static final String MODE_CALENDAR = "calendar";
    public static final String MODE_NOTES = "notes";

    public static String getCurrentMode(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).getString(KEY, MODE_DEFAULT);
    }

    public static String getCurrentDisguiseMode(Context ctx) { return getCurrentMode(ctx); }

    public static String getDisguiseTitle(Context ctx, boolean isFa) {
        String m = getCurrentMode(ctx);
        if (MODE_CALCULATOR.equals(m)) return isFa ? "ماشین‌حساب+" : "Calculator+";
        if (MODE_CALENDAR.equals(m)) return isFa ? "تقویم هوشمند" : "Smart Calendar";
        if (MODE_NOTES.equals(m)) return isFa ? "یادداشت‌های خصوصی" : "Private Notes";
        return "VeyraVault";
    }

    public static void applyDisguiseMode(Context ctx, String mode) {
        if (mode == null) mode = MODE_DEFAULT;
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putString(KEY, mode).apply();
        PackageManager pm = ctx.getPackageManager();
        String pkg = ctx.getPackageName();
        setComp(pm, new ComponentName(pkg, "com.veyravault.space.ui.MainActivity"), MODE_DEFAULT.equals(mode));
        setComp(pm, new ComponentName(pkg, "com.veyravault.space.AliasCalculator"), MODE_CALCULATOR.equals(mode));
        setComp(pm, new ComponentName(pkg, "com.veyravault.space.AliasCalendar"), MODE_CALENDAR.equals(mode));
        setComp(pm, new ComponentName(pkg, "com.veyravault.space.AliasNotes"), MODE_NOTES.equals(mode));
    }

    private static void setComp(PackageManager pm, ComponentName cn, boolean en) {
        try {
            pm.setComponentEnabledSetting(cn, en ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED : PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
        } catch (Throwable ignored) {}
    }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/helper/PatternLockView.java",
        """package com.veyravault.space.helper;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.View;
import java.util.ArrayList;
import java.util.List;

public class PatternLockView extends View {
    public interface OnPatternListener { void onPatternDetected(String patternValue); }
    private final List<Integer> nodes = new ArrayList<>();
    private final Paint circlePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private float curX, curY;
    private boolean drawing = false;
    private OnPatternListener listener;

    public PatternLockView(Context context) {
        super(context);
        circlePaint.setColor(Color.parseColor("#334155"));
        activePaint.setColor(Color.parseColor("#38BDF8"));
        linePaint.setColor(Color.parseColor("#38BDF8"));
        linePaint.setStrokeWidth(10f);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setOnPatternListener(OnPatternListener l) { this.listener = l; }
    public void clearPattern() { nodes.clear(); invalidate(); }
    private float nx(int i) { return (getWidth() / 4f) * ((i % 3) + 1); }
    private float ny(int i) { return (getHeight() / 4f) * ((i / 3) + 1); }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float r = Math.min(getWidth(), getHeight()) / 14f;
        for (int i = 0; i < nodes.size() - 1; i++) {
            canvas.drawLine(nx(nodes.get(i)), ny(nodes.get(i)), nx(nodes.get(i + 1)), ny(nodes.get(i + 1)), linePaint);
        }
        if (drawing && !nodes.isEmpty()) {
            int last = nodes.get(nodes.size() - 1);
            canvas.drawLine(nx(last), ny(last), curX, curY, linePaint);
        }
        for (int i = 0; i < 9; i++) {
            boolean act = nodes.contains(i);
            canvas.drawCircle(nx(i), ny(i), r, act ? activePaint : circlePaint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        curX = e.getX(); curY = e.getY();
        switch (e.getAction()) {
            case MotionEvent.ACTION_DOWN:
                nodes.clear(); drawing = true; hit(curX, curY); invalidate(); return true;
            case MotionEvent.ACTION_MOVE:
                hit(curX, curY); invalidate(); return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                drawing = false;
                if (!nodes.isEmpty() && listener != null) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < nodes.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(nodes.get(i) + 1);
                    }
                    listener.onPatternDetected(sb.toString());
                }
                invalidate();
                return true;
        }
        return super.onTouchEvent(e);
    }

    private void hit(float x, float y) {
        float hr = Math.min(getWidth(), getHeight()) / 8f;
        for (int i = 0; i < 9; i++) {
            if (!nodes.contains(i) && Math.hypot(x - nx(i), y - ny(i)) <= hr) {
                nodes.add(i);
                break;
            }
        }
    }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/core/CloneMetadataStore.java",
        """package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class CloneMetadataStore {
    private static final String PREF = "veyra_clone_metadata_v3";

    public static class DevicePreset {
        public final String displayTitle, brand, model, deviceCode;
        public DevicePreset(String d, String b, String m, String c) { displayTitle = d; brand = b; model = m; deviceCode = c; }
    }

    public static class RegionPreset {
        public final String regionName, timezoneId, simulatedIp;
        public final double lat, lon;
        public RegionPreset(String r, double la, double lo, String tz, String ip) { regionName = r; lat = la; lon = lo; timezoneId = tz; simulatedIp = ip; }
    }

    public static List<DevicePreset> getDevicePresets() {
        List<DevicePreset> l = new ArrayList<>();
        l.add(new DevicePreset("Samsung Galaxy S24 Ultra", "samsung", "SM-S928B", "e3q"));
        l.add(new DevicePreset("Samsung Galaxy S23 Ultra", "samsung", "SM-S918B", "dm3q"));
        l.add(new DevicePreset("Apple iPhone 16 Pro Max", "Apple", "iPhone17,2 (iOS 18)", "iPhone16ProMax"));
        l.add(new DevicePreset("Apple iPhone 15 Pro Max", "Apple", "iPhone16,2 (iOS 17)", "iPhone15ProMax"));
        l.add(new DevicePreset("Apple iPhone 14 Pro", "Apple", "iPhone15,2", "iPhone14Pro"));
        l.add(new DevicePreset("Apple iPad Pro M4", "Apple", "iPad16,6", "iPadProM4"));
        l.add(new DevicePreset("Google Pixel 9 Pro XL", "google", "Pixel 9 Pro XL", "komodo"));
        l.add(new DevicePreset("Google Pixel 8 Pro", "google", "Pixel 8 Pro", "husky"));
        l.add(new DevicePreset("Xiaomi 14 Ultra", "Xiaomi", "24030PN60G", "aurora"));
        l.add(new DevicePreset("OnePlus 12 (Global)", "OnePlus", "CPH2581", "waffle"));
        return l;
    }

    public static Map<String, String> getAvailableDevicePresets() {
        Map<String, String> map = new LinkedHashMap<>();
        for (DevicePreset dp : getDevicePresets()) {
            map.put(dp.displayTitle + " (" + dp.model + ")", dp.brand);
        }
        return map;
    }

    public static List<RegionPreset> getRegionPresets() {
        List<RegionPreset> l = new ArrayList<>();
        l.add(new RegionPreset("Falkenstein, Germany", 50.4779, 12.3713, "Europe/Berlin", "88.198.48.21"));
        l.add(new RegionPreset("Frankfurt, Germany", 50.1109, 8.6821, "Europe/Berlin", "138.201.92.14"));
        l.add(new RegionPreset("Amsterdam, Netherlands", 52.3676, 4.9041, "Europe/Amsterdam", "95.211.198.45"));
        l.add(new RegionPreset("London, United Kingdom", 51.5074, -0.1278, "Europe/London", "51.140.104.22"));
        l.add(new RegionPreset("New York, United States", 40.7128, -74.0060, "America/New_York", "104.244.42.65"));
        l.add(new RegionPreset("Helsinki, Finland", 60.1699, 24.9384, "Europe/Helsinki", "65.108.44.10"));
        l.add(new RegionPreset("Istanbul, Turkey", 41.0082, 28.9784, "Europe/Istanbul", "185.125.33.19"));
        l.add(new RegionPreset("Dubai, UAE", 25.2048, 55.2708, "Asia/Dubai", "94.200.14.88"));
        l.add(new RegionPreset("Tehran, Iran", 35.6892, 51.3890, "Asia/Tehran", "5.160.120.11"));
        return l;
    }

    private static SharedPreferences sp(Context c) { return c.getSharedPreferences(PREF, Context.MODE_PRIVATE); }

    public static void ensureDefaultsInitialized(Context c) {
        SharedPreferences p = sp(c);
        if (!p.contains("global_initialized_v3")) {
            p.edit().putBoolean("global_initialized_v3", true)
                .putString("global_brand", "samsung").putString("global_model", "SM-S928B")
                .putString("global_display", "Samsung Galaxy S24 Ultra")
                .putString("global_region", "Falkenstein, Germany")
                .putString("global_lat", "50.4779").putString("global_lon", "12.3713")
                .putString("global_tz", "Europe/Berlin").putString("global_sim_ip", "88.198.48.21").apply();
        }
    }

    public static String getSpaceName(Context c, int spaceId, boolean isFa) {
        String custom = sp(c).getString("space_custom_name_" + spaceId, "");
        if (custom != null && !custom.trim().isEmpty()) return custom.trim();
        return isFa ? ("فضای " + (spaceId + 1)) : ("Space " + (spaceId + 1));
    }

    public static String getSpaceDisplayName(Context c, int spaceId, boolean isFa) {
        return getSpaceName(c, spaceId, isFa);
    }

    public static String getSpaceCustomName(Context c, int spaceId) {
        return sp(c).getString("space_custom_name_" + spaceId, "");
    }

    public static void setSpaceCustomName(Context c, int spaceId, String name) {
        sp(c).edit().putString("space_custom_name_" + spaceId, name == null ? "" : name.trim()).apply();
    }

    public static void setGlobalDeviceIdentity(Context c, String brand, String model) {
        String b = brand == null ? "samsung" : brand.trim();
        String m = model == null ? "SM-S928B" : model.trim();
        String d = b + " " + m;
        for (DevicePreset dp : getDevicePresets()) {
            if (dp.brand.equalsIgnoreCase(b) && dp.model.equalsIgnoreCase(m)) { d = dp.displayTitle; break; }
        }
        setGlobalDeviceIdentity(c, d, b, m);
    }

    public static void setGlobalDeviceIdentity(Context c, String display, String brand, String model) {
        sp(c).edit().putString("global_display", display).putString("global_brand", brand).putString("global_model", model).apply();
        VirtualHookManager.applyGlobalEnvironmentHooks(c);
    }

    public static String getGlobalDeviceDisplay(Context c) { ensureDefaultsInitialized(c); return sp(c).getString("global_display", "Samsung Galaxy S24 Ultra"); }
    public static String getGlobalDeviceBrand(Context c) { ensureDefaultsInitialized(c); return sp(c).getString("global_brand", "samsung"); }
    public static String getGlobalDeviceModel(Context c) { ensureDefaultsInitialized(c); return sp(c).getString("global_model", "SM-S928B"); }

    public static void setGlobalRegionLocation(Context c, String r, double lat, double lon, String tz, String ip) {
        sp(c).edit().putString("global_region", r).putString("global_lat", String.valueOf(lat)).putString("global_lon", String.valueOf(lon))
            .putString("global_tz", tz == null || tz.isEmpty() ? "Europe/Berlin" : tz)
            .putString("global_sim_ip", ip == null || ip.isEmpty() ? "88.198.48.21" : ip).apply();
        VirtualHookManager.applyGlobalEnvironmentHooks(c);
    }

    public static String getGlobalRegionName(Context c) { ensureDefaultsInitialized(c); return sp(c).getString("global_region", "Falkenstein, Germany"); }
    public static double getGlobalLat(Context c) { try { return Double.parseDouble(sp(c).getString("global_lat", "50.4779")); } catch (Exception e) { return 50.4779; } }
    public static double getGlobalLon(Context c) { try { return Double.parseDouble(sp(c).getString("global_lon", "12.3713")); } catch (Exception e) { return 12.3713; } }
    public static double[] getGlobalCoordinates(Context c) { return new double[]{ getGlobalLat(c), getGlobalLon(c) }; }
    public static String getGlobalTimezone(Context c) { return sp(c).getString("global_tz", "Europe/Berlin"); }
    public static String getGlobalSimulatedIp(Context c) { return sp(c).getString("global_sim_ip", "88.198.48.21"); }
    public static String getGlobalVirtualIp(Context c) { return getGlobalSimulatedIp(c); }

    public static void setGlobalProxy(Context c, String host, int port) { setGlobalProxy(c, host, String.valueOf(Math.max(0, port))); }
    public static void setGlobalProxy(Context c, String host, String port) {
        sp(c).edit().putString("proxy_host", host == null ? "" : host.trim()).putString("proxy_port", port == null ? "" : port.trim()).apply();
        VirtualHookManager.applyGlobalEnvironmentHooks(c);
    }
    public static String getGlobalProxyHost(Context c) { return sp(c).getString("proxy_host", ""); }
    public static String getGlobalProxyPort(Context c) { return sp(c).getString("proxy_port", ""); }

    private static String k(String pkg, int u, String s) { return "clone_" + u + "_" + pkg + "_" + s; }
    public static void setCustomAlias(Context c, String pkg, int u, String a) { sp(c).edit().putString(k(pkg, u, "alias"), a == null ? "" : a.trim()).apply(); }
    public static String getCustomAlias(Context c, String pkg, int u) { return sp(c).getString(k(pkg, u, "alias"), ""); }

    public static void setCustomDeviceIdentity(Context c, String pkg, int u, String brand, String model) {
        String b = brand == null ? "samsung" : brand.trim();
        String m = model == null ? "SM-S928B" : model.trim();
        setCustomDeviceIdentity(c, pkg, u, m.contains(b) ? m : (b + " " + m), b, m);
    }

    public static void setCustomDeviceIdentity(Context c, String pkg, int u, String d, String b, String m) {
        sp(c).edit().putBoolean(k(pkg, u, "has_dev"), true).putString(k(pkg, u, "dev_display"), d).putString(k(pkg, u, "dev_brand"), b).putString(k(pkg, u, "dev_model"), m).apply();
    }
    public static void clearCustomDeviceIdentity(Context c, String pkg, int u) { sp(c).edit().putBoolean(k(pkg, u, "has_dev"), false).apply(); }
    public static boolean hasCustomDeviceIdentity(Context c, String pkg, int u) { return sp(c).getBoolean(k(pkg, u, "has_dev"), false); }
    public static String getEffectiveDeviceDisplay(Context c, String pkg, int u) { return hasCustomDeviceIdentity(c, pkg, u) ? sp(c).getString(k(pkg, u, "dev_display"), getGlobalDeviceDisplay(c)) : getGlobalDeviceDisplay(c); }
    public static String getEffectiveBrand(Context c, String pkg, int u) { return hasCustomDeviceIdentity(c, pkg, u) ? sp(c).getString(k(pkg, u, "dev_brand"), getGlobalDeviceBrand(c)) : getGlobalDeviceBrand(c); }
    public static String getEffectiveDeviceBrand(Context c, String pkg, int u) { return getEffectiveBrand(c, pkg, u); }
    public static String getEffectiveModel(Context c, String pkg, int u) { return hasCustomDeviceIdentity(c, pkg, u) ? sp(c).getString(k(pkg, u, "dev_model"), getGlobalDeviceModel(c)) : getGlobalDeviceModel(c); }
    public static String getEffectiveDeviceModel(Context c, String pkg, int u) { return getEffectiveModel(c, pkg, u); }

    public static void setCustomLocation(Context c, String pkg, int u, String r, double lat, double lon, String tz, String ip) {
        sp(c).edit().putBoolean(k(pkg, u, "has_loc"), true)
            .putString(k(pkg, u, "loc_region"), r == null || r.isEmpty() ? "Falkenstein, Germany" : r)
            .putString(k(pkg, u, "loc_lat"), String.valueOf(lat)).putString(k(pkg, u, "loc_lon"), String.valueOf(lon))
            .putString(k(pkg, u, "loc_tz"), tz == null || tz.isEmpty() ? "Europe/Berlin" : tz)
            .putString(k(pkg, u, "loc_ip"), ip == null || ip.isEmpty() ? "88.198.48.21" : ip).apply();
    }
    public static void clearCustomLocation(Context c, String pkg, int u) { sp(c).edit().putBoolean(k(pkg, u, "has_loc"), false).apply(); }
    public static boolean hasCustomLocation(Context c, String pkg, int u) { return sp(c).getBoolean(k(pkg, u, "has_loc"), false); }
    public static String getEffectiveRegionDisplay(Context c, String pkg, int u) { return hasCustomLocation(c, pkg, u) ? sp(c).getString(k(pkg, u, "loc_region"), getGlobalRegionName(c)) : getGlobalRegionName(c); }
    public static String getEffectiveRegionName(Context c, String pkg, int u) { return getEffectiveRegionDisplay(c, pkg, u); }
    public static double getEffectiveLat(Context c, String pkg, int u) { if (hasCustomLocation(c, pkg, u)) { try { return Double.parseDouble(sp(c).getString(k(pkg, u, "loc_lat"), "50.4779")); } catch (Exception ignored) {} } return getGlobalLat(c); }
    public static double getEffectiveLon(Context c, String pkg, int u) { if (hasCustomLocation(c, pkg, u)) { try { return Double.parseDouble(sp(c).getString(k(pkg, u, "loc_lon"), "12.3713")); } catch (Exception ignored) {} } return getGlobalLon(c); }
    public static double[] getEffectiveCoordinates(Context c, String pkg, int u) { return new double[]{ getEffectiveLat(c, pkg, u), getEffectiveLon(c, pkg, u) }; }
    public static String getEffectiveTimezone(Context c, String pkg, int u) { return hasCustomLocation(c, pkg, u) ? sp(c).getString(k(pkg, u, "loc_tz"), getGlobalTimezone(c)) : getGlobalTimezone(c); }
    public static String getEffectiveSimulatedIp(Context c, String pkg, int u) { return hasCustomLocation(c, pkg, u) ? sp(c).getString(k(pkg, u, "loc_ip"), getGlobalSimulatedIp(c)) : getGlobalSimulatedIp(c); }

    public static void registerVaultedClone(Context c, String pkg, int u) {
        Set<String> s = new HashSet<>(sp(c).getStringSet("vaulted_clones_" + u, new HashSet<String>()));
        s.add(pkg);
        sp(c).edit().putStringSet("vaulted_clones_" + u, s).apply();
    }
    public static void unregisterVaultedClone(Context c, String pkg, int u) {
        Set<String> s = new HashSet<>(sp(c).getStringSet("vaulted_clones_" + u, new HashSet<String>()));
        s.remove(pkg);
        sp(c).edit().putStringSet("vaulted_clones_" + u, s).apply();
    }
    public static Set<String> getVaultedClones(Context c, int u) {
        return new HashSet<>(sp(c).getStringSet("vaulted_clones_" + u, new HashSet<String>()));
    }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/core/VirtualHookManager.java",
        """package com.veyravault.space.core;

import android.content.Context;
import android.os.Build;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.TimeZone;

public class VirtualHookManager {
    public static void applyGlobalEnvironmentHooks(Context ctx) {
        try {
            applyRuntime(CloneMetadataStore.getGlobalDeviceBrand(ctx), CloneMetadataStore.getGlobalDeviceModel(ctx),
                CloneMetadataStore.getGlobalTimezone(ctx), CloneMetadataStore.getGlobalRegionName(ctx),
                CloneMetadataStore.getGlobalLat(ctx), CloneMetadataStore.getGlobalLon(ctx),
                CloneMetadataStore.getGlobalSimulatedIp(ctx), ctx);
        } catch (Throwable ignored) {}
    }

    public static void prepareForCloneLaunch(Context ctx, String pkg, int userId) {
        try {
            String b = CloneMetadataStore.getEffectiveBrand(ctx, pkg, userId);
            String m = CloneMetadataStore.getEffectiveModel(ctx, pkg, userId);
            double lat = CloneMetadataStore.getEffectiveLat(ctx, pkg, userId);
            double lon = CloneMetadataStore.getEffectiveLon(ctx, pkg, userId);
            applyRuntime(b, m, CloneMetadataStore.getEffectiveTimezone(ctx, pkg, userId),
                CloneMetadataStore.getEffectiveRegionDisplay(ctx, pkg, userId), lat, lon,
                CloneMetadataStore.getEffectiveSimulatedIp(ctx, pkg, userId), ctx);
            applyBlackBoxLoc(pkg, userId, lat, lon);
            installGmsAvailabilityBypass();
        } catch (Throwable ignored) {}
    }

    private static void applyRuntime(String brand, String model, String tz, String region, double lat, double lon, String ip, Context ctx) {
        try {
            setField("BRAND", brand); setField("MANUFACTURER", brand); setField("MODEL", model); setField("PRODUCT", model);
            if (tz != null && !tz.isEmpty()) { TimeZone.setDefault(TimeZone.getTimeZone(tz)); System.setProperty("user.timezone", tz); }
            System.setProperty("veyra.virtual.region", region);
            System.setProperty("veyra.virtual.lat", String.valueOf(lat));
            System.setProperty("veyra.virtual.lon", String.valueOf(lon));
            System.setProperty("veyra.virtual.ip", ip);
            String ph = CloneMetadataStore.getGlobalProxyHost(ctx);
            String pp = CloneMetadataStore.getGlobalProxyPort(ctx);
            if (ph != null && !ph.isEmpty() && pp != null && !pp.isEmpty() && !"0".equals(pp)) {
                System.setProperty("socksProxyHost", ph); System.setProperty("socksProxyPort", pp);
                System.setProperty("http.proxyHost", ph); System.setProperty("http.proxyPort", pp);
            }
        } catch (Throwable ignored) {}
    }

    private static void applyBlackBoxLoc(String pkg, int userId, double lat, double lon) {
        try {
            Class<?> lmCls = Class.forName("top.niunaijun.blackbox.fake.frameworks.BLocationManager");
            Object lm = lmCls.getMethod("get").invoke(null);
            Class<?> blCls = Class.forName("top.niunaijun.blackbox.entity.location.BLocation");
            Object bl = blCls.getConstructor(double.class, double.class).newInstance(lat, lon);
            for (Method m : lmCls.getMethods()) {
                if (m.getName().equals("setPattern") && m.getParameterTypes().length == 1) m.invoke(lm, 2);
                else if (m.getName().equals("setLocation") && m.getParameterTypes().length == 3) m.invoke(lm, userId, pkg, bl);
            }
        } catch (Throwable ignored) {}
    }

    public static void installGmsAvailabilityBypass() {
        try { System.setProperty("veyra.gms.SpoofAvailable", "true"); } catch (Throwable ignored) {}
    }

    private static void setField(String name, String val) {
        if (val == null || val.isEmpty()) return;
        try { Field f = Build.class.getDeclaredField(name); f.setAccessible(true); f.set(null, val); } catch (Throwable ignored) {}
    }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/core/Engine.java",
        """package com.veyravault.space.core;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.util.LruCache;
import com.veyravault.space.helper.GmsSupportManager;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.entity.pm.InstallResult;

public class Engine {
    public static class AppModel {
        public String packageName;
        public String name;
        public Drawable icon;
        public int userId;
        public int spaceId;
        public boolean isSystem;
        public boolean hasCustomDeviceIdentity;
        public boolean hasCustomDevice;
        public String effectiveDeviceDisplay;
        public String customDeviceName;
        public boolean hasCustomLocation;
        public boolean hasCustomLoc;
        public String effectiveRegionDisplay;
        public String effectiveRegion;
        public boolean isVaultBacked;
    }

    public static class ClonedApp extends AppModel {}
    public static class InstallOptionCandidate extends AppModel {}

    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(120);

    public static int[] getSpaces() {
        return new int[]{0, 1, 2};
    }

    public static File getApkVaultDir(Context ctx, String pkg) {
        File d = new File(ctx.getFilesDir(), "apk_vault/" + pkg);
        if (!d.exists()) d.mkdirs();
        return d;
    }

    public static File getVaultBaseApk(Context ctx, String pkg) {
        return new File(getApkVaultDir(ctx, pkg), "base.apk");
    }

    public static void backupPackageToVault(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
            File vaultDir = getApkVaultDir(ctx, pkg);
            if (ai.sourceDir != null) {
                File src = new File(ai.sourceDir);
                File dst = new File(vaultDir, "base.apk");
                if (src.exists() && (!dst.exists() || dst.length() != src.length())) {
                    copyFile(src, dst);
                    extractNativeLibs(dst, new File(vaultDir, "lib"));
                }
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP && ai.splitSourceDirs != null) {
                int i = 0;
                for (String sp : ai.splitSourceDirs) {
                    i++;
                    File sSrc = new File(sp);
                    File sDst = new File(vaultDir, "split_" + i + ".apk");
                    if (sSrc.exists()) {
                        if (!sDst.exists() || sDst.length() != sSrc.length()) copyFile(sSrc, sDst);
                        extractNativeLibs(sDst, new File(vaultDir, "lib"));
                    }
                }
            }
        } catch (Throwable ignored) {}
    }

    private static void extractNativeLibs(File apk, File outDir) {
        if (apk == null || !apk.exists()) return;
        String abi = (Build.SUPPORTED_ABIS != null && Build.SUPPORTED_ABIS.length > 0) ? Build.SUPPORTED_ABIS[0] : "arm64-v8a";
        ZipFile zf = null;
        try {
            zf = new ZipFile(apk);
            Enumeration<? extends ZipEntry> en = zf.entries();
            while (en.hasMoreElements()) {
                ZipEntry ze = en.nextElement();
                String n = ze.getName();
                if (!ze.isDirectory() && n.startsWith("lib/") && n.endsWith(".so") && (n.contains(abi) || n.contains("armeabi-v7a") || n.contains("arm64-v8a"))) {
                    if (!outDir.exists()) outDir.mkdirs();
                    File outSo = new File(outDir, n.substring(n.lastIndexOf('/') + 1));
                    if (!outSo.exists() || outSo.length() != ze.getSize()) {
                        InputStream is = zf.getInputStream(ze);
                        FileOutputStream fos = new FileOutputStream(outSo);
                        byte[] b = new byte[8192]; int r;
                        while ((r = is.read(b)) > 0) fos.write(b, 0, r);
                        fos.close(); is.close();
                    }
                }
            }
        } catch (Throwable ignored) {
        } finally { try { if (zf != null) zf.close(); } catch (Throwable ignored) {} }
    }

    private static void syncVaultLibs(Context ctx, String pkg) {
        try {
            File vLib = new File(getApkVaultDir(ctx, pkg), "lib");
            File[] sos = vLib.exists() ? vLib.listFiles() : null;
            if (sos == null || sos.length == 0) return;
            File dataDir = new File(ctx.getApplicationInfo().dataDir);
            File[] dirs = new File[]{
                new File(dataDir, "virtual/data/app/" + pkg + "/lib"),
                new File(dataDir, "virtual/data/app/" + pkg + "/lib/arm64"),
                new File(dataDir, "virtual/data/app/" + pkg + "/lib/arm")
            };
            for (File d : dirs) {
                d.mkdirs();
                for (File so : sos) {
                    File dst = new File(d, so.getName());
                    if (!dst.exists() || dst.length() != so.length()) copyFile(so, dst);
                }
            }
        } catch (Throwable ignored) {}
    }

    private static void copyFile(File src, File dst) throws Exception {
        FileInputStream fis = new FileInputStream(src);
        FileOutputStream fos = new FileOutputStream(dst);
        byte[] b = new byte[16384]; int r;
        while ((r = fis.read(b)) > 0) fos.write(b, 0, r);
        fos.close(); fis.close();
    }

    public static List<InstallOptionCandidate> getInstallCandidates(Context ctx) {
        List<AppModel> raw = getInstalledHostApps(ctx);
        List<InstallOptionCandidate> out = new ArrayList<>();
        for (AppModel m : raw) {
            InstallOptionCandidate c = new InstallOptionCandidate();
            c.packageName = m.packageName; c.name = m.name; c.icon = m.icon; c.isSystem = m.isSystem;
            out.add(c);
        }
        return out;
    }

    public static List<AppModel> getInstalledHostApps(Context ctx) {
        List<AppModel> res = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        String own = ctx.getPackageName();
        Intent mi = new Intent(Intent.ACTION_MAIN, null);
        mi.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> list = pm.queryIntentActivities(mi, 0);
        Set<String> seen = new HashSet<>();
        for (ResolveInfo ri : list) {
            if (ri.activityInfo == null) continue;
            String pkg = ri.activityInfo.packageName;
            if (pkg == null || pkg.equals(own) || seen.contains(pkg)) continue;
            seen.add(pkg);
            try {
                ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
                AppModel m = new AppModel();
                m.packageName = pkg;
                CharSequence lb = ai.loadLabel(pm);
                m.name = lb != null ? lb.toString() : pkg;
                m.icon = loadCachedIcon(pm, ai, pkg);
                m.isSystem = (ai.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
                res.add(m);
            } catch (Throwable ignored) {}
        }
        Collections.sort(res, new Comparator<AppModel>() {
            @Override public int compare(AppModel a, AppModel b) {
                if (a.isSystem != b.isSystem) return a.isSystem ? 1 : -1;
                return a.name.compareToIgnoreCase(b.name);
            }
        });
        return res;
    }

    public static List<ClonedApp> getClonedApps(Context ctx, int userId) {
        List<ClonedApp> list = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Set<String> added = new HashSet<>();
        try {
            List<ApplicationInfo> ins = BlackBoxCore.get().getInstalledApplications(0, userId);
            if (ins != null) {
                for (ApplicationInfo info : ins) {
                    if (info == null || info.packageName == null) continue;
                    String pkg = info.packageName;
                    if (pkg.contains("google.android.gms") || pkg.contains("google.android.gsf") || pkg.equals(ctx.getPackageName())) continue;
                    ClonedApp m = buildCloned(ctx, pm, pkg, userId);
                    if (m != null) { list.add(m); added.add(pkg); CloneMetadataStore.registerVaultedClone(ctx, pkg, userId); }
                }
            }
        } catch (Throwable ignored) {}
        for (String pkg : CloneMetadataStore.getVaultedClones(ctx, userId)) {
            if (added.contains(pkg)) continue;
            File vApk = getVaultBaseApk(ctx, pkg);
            if (vApk.exists()) {
                try { BlackBoxCore.get().installPackageAsUser(vApk, userId); } catch (Throwable ignored) {}
                ClonedApp m = buildCloned(ctx, pm, pkg, userId);
                if (m != null) { list.add(m); added.add(pkg); }
            }
        }
        return list;
    }

    private static ClonedApp buildCloned(Context ctx, PackageManager pm, String pkg, int userId) {
        try {
            ClonedApp m = new ClonedApp();
            m.packageName = pkg; m.userId = userId; m.spaceId = userId;
            String baseName = pkg;
            Drawable icon = ICON_CACHE.get(pkg);
            boolean hostOk = false;
            try {
                ApplicationInfo hai = pm.getApplicationInfo(pkg, 0);
                CharSequence lb = hai.loadLabel(pm);
                if (lb != null) baseName = lb.toString();
                if (icon == null) { icon = hai.loadIcon(pm); if (icon != null) ICON_CACHE.put(pkg, icon); }
                hostOk = true;
            } catch (Throwable ignored) {}
            File vApk = getVaultBaseApk(ctx, pkg);
            m.isVaultBacked = vApk.exists();
            if (!hostOk && vApk.exists()) {
                PackageInfo pi = pm.getPackageArchiveInfo(vApk.getAbsolutePath(), 0);
                if (pi != null && pi.applicationInfo != null) {
                    ApplicationInfo ai = pi.applicationInfo;
                    ai.sourceDir = vApk.getAbsolutePath(); ai.publicSourceDir = vApk.getAbsolutePath();
                    CharSequence lb = ai.loadLabel(pm);
                    if (lb != null) baseName = lb.toString();
                    if (icon == null) { icon = ai.loadIcon(pm); if (icon != null) ICON_CACHE.put(pkg, icon); }
                }
            }
            if (icon == null) icon = ctx.getResources().getDrawable(android.R.drawable.sym_def_app_icon);
            String alias = CloneMetadataStore.getCustomAlias(ctx, pkg, userId);
            m.name = (alias != null && !alias.isEmpty()) ? alias : baseName;
            m.icon = icon;
            m.hasCustomDeviceIdentity = CloneMetadataStore.hasCustomDeviceIdentity(ctx, pkg, userId);
            m.hasCustomDevice = m.hasCustomDeviceIdentity;
            m.effectiveDeviceDisplay = CloneMetadataStore.getEffectiveDeviceDisplay(ctx, pkg, userId);
            m.customDeviceName = m.effectiveDeviceDisplay;
            m.hasCustomLocation = CloneMetadataStore.hasCustomLocation(ctx, pkg, userId);
            m.hasCustomLoc = m.hasCustomLocation;
            m.effectiveRegionDisplay = CloneMetadataStore.getEffectiveRegionDisplay(ctx, pkg, userId);
            m.effectiveRegion = m.effectiveRegionDisplay;
            return m;
        } catch (Throwable t) { return null; }
    }

    public static boolean cloneAppToSpace(Context ctx, String pkg, int userId) { return clonePackage(ctx, pkg, userId); }

    public static boolean clonePackage(Context ctx, String pkg, int userId) {
        try {
            GmsSupportManager.ensureGmsForSpace(userId);
            backupPackageToVault(ctx, pkg);
            File vBase = getVaultBaseApk(ctx, pkg);
            InstallResult r = vBase.exists() ? BlackBoxCore.get().installPackageAsUser(vBase, userId) : BlackBoxCore.get().installPackageAsUser(pkg, userId);
            syncVaultLibs(ctx, pkg);
            CloneMetadataStore.registerVaultedClone(ctx, pkg, userId);
            return r != null && r.success;
        } catch (Throwable t) { return false; }
    }

    public static boolean installExternalApkFileToSpace(Context ctx, File apk, int userId) { return installApkFileToVaultOnly(ctx, apk, userId); }

    public static boolean installApkFileToVaultOnly(Context ctx, File apk, int userId) {
        if (apk == null || !apk.exists()) return false;
        try {
            PackageInfo pi = ctx.getPackageManager().getPackageArchiveInfo(apk.getAbsolutePath(), 0);
            String pkg = (pi != null && pi.packageName != null) ? pi.packageName : ("vault.app." + System.currentTimeMillis());
            File vDir = getApkVaultDir(ctx, pkg);
            File dst = new File(vDir, "base.apk");
            copyFile(apk, dst);
            extractNativeLibs(dst, new File(vDir, "lib"));
            GmsSupportManager.ensureGmsForSpace(userId);
            InstallResult r = BlackBoxCore.get().installPackageAsUser(dst, userId);
            syncVaultLibs(ctx, pkg);
            CloneMetadataStore.registerVaultedClone(ctx, pkg, userId);
            return r != null && r.success;
        } catch (Throwable t) { return false; }
    }

    public static boolean launchClone(Context ctx, String pkg, int userId) {
        try {
            GmsSupportManager.ensureGmsForSpace(userId);
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, userId);
            syncVaultLibs(ctx, pkg);
            File vBase = getVaultBaseApk(ctx, pkg);
            if (!BlackBoxCore.get().isInstalled(pkg, userId) && vBase.exists()) {
                BlackBoxCore.get().installPackageAsUser(vBase, userId);
            }
            Intent main = resolveMainIntent(ctx, pkg);
            if (main != null) {
                try {
                    for (Method m : BlackBoxCore.get().getClass().getMethods()) {
                        if (m.getName().equals("startActivity") && m.getParameterTypes().length == 2) {
                            m.invoke(BlackBoxCore.get(), main, userId);
                            return true;
                        }
                    }
                } catch (Throwable ignored) {}
            }
            return BlackBoxCore.get().launchApk(pkg, userId);
        } catch (Throwable t) { return false; }
    }

    private static Intent resolveMainIntent(Context ctx, String pkg) {
        try {
            if (pkg.contains("chrome")) {
                Intent ci = new Intent(Intent.ACTION_MAIN);
                ci.addCategory(Intent.CATEGORY_LAUNCHER);
                ci.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
                ci.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                return ci;
            }
            Intent q = new Intent(Intent.ACTION_MAIN, null);
            q.addCategory(Intent.CATEGORY_LAUNCHER);
            q.setPackage(pkg);
            List<ResolveInfo> list = ctx.getPackageManager().queryIntentActivities(q, 0);
            if (list != null && !list.isEmpty()) {
                ActivityInfo chosen = null;
                for (ResolveInfo ri : list) {
                    if (ri.activityInfo == null || ri.activityInfo.name == null) continue;
                    String an = ri.activityInfo.name.toLowerCase(Locale.US);
                    if (!an.contains("devui") && !an.contains("devtools") && !an.contains("crash")) {
                        chosen = ri.activityInfo; break;
                    }
                }
                if (chosen == null) chosen = list.get(0).activityInfo;
                if (chosen != null) {
                    Intent li = new Intent(Intent.ACTION_MAIN);
                    li.addCategory(Intent.CATEGORY_LAUNCHER);
                    li.setComponent(new ComponentName(pkg, chosen.name));
                    li.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                    return li;
                }
            }
        } catch (Throwable ignored) {}
        return null;
    }

    public static void removeClone(Context ctx, String pkg, int userId) {
        uninstallClone(ctx, pkg, userId);
    }

    public static void uninstallClone(Context ctx, String pkg, int userId) {
        try { BlackBoxCore.get().uninstallPackageAsUser(pkg, userId); } catch (Throwable ignored) {}
        CloneMetadataStore.unregisterVaultedClone(ctx, pkg, userId);
        CloneMetadataStore.clearCustomDeviceIdentity(ctx, pkg, userId);
        CloneMetadataStore.clearCustomLocation(ctx, pkg, userId);
        CloneMetadataStore.setCustomAlias(ctx, pkg, userId, "");
    }

    private static Drawable loadCachedIcon(PackageManager pm, ApplicationInfo ai, String pkg) {
        Drawable d = ICON_CACHE.get(pkg);
        if (d == null) { d = ai.loadIcon(pm); if (d != null) ICON_CACHE.put(pkg, d); }
        return d;
    }

    public static void clearMemoryCaches() { ICON_CACHE.evictAll(); System.gc(); }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/security/SecurityManager.java",
        """package com.veyravault.space.security;

import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import java.security.MessageDigest;

public class SecurityManager {
    private static final String PREF = "veyra_security_v3";
    private static final String KEY_PIN = "pin_hash_v3";
    private static final String KEY_PAT = "pattern_hash_v3";
    private static final String KEY_PRI = "primary_priority_v3";

    public static final String PRIORITY_PIN = "PIN";
    public static final String PRIORITY_PATTERN = "PATTERN";
    public static final int LOCK_NONE = 0;
    public static final int LOCK_PIN = 1;
    public static final int LOCK_PATTERN = 2;

    private static boolean sUnlocked = false;
    private static SharedPreferences sp(Context c) { return c.getSharedPreferences(PREF, Context.MODE_PRIVATE); }

    public static boolean isSessionUnlocked() { return sUnlocked; }
    public static void setSessionUnlocked(boolean u) { sUnlocked = u; }
    public static boolean isPinConfigured(Context c) { return !sp(c).getString(KEY_PIN, "").isEmpty(); }
    public static boolean hasPin(Context c) { return isPinConfigured(c); }
    public static boolean isPatternConfigured(Context c) { return !sp(c).getString(KEY_PAT, "").isEmpty(); }
    public static boolean hasPattern(Context c) { return isPatternConfigured(c); }
    public static boolean isLockEnabled(Context c) { return isPinConfigured(c) || isPatternConfigured(c); }
    public static boolean hasBothLocksConfigured(Context c) { return isPinConfigured(c) && isPatternConfigured(c); }

    public static void savePin(Context c, String pin) { if (pin != null && !pin.trim().isEmpty()) sp(c).edit().putString(KEY_PIN, sha(pin.trim())).apply(); }
    public static void savePattern(Context c, String pat) { if (pat != null && !pat.trim().isEmpty()) sp(c).edit().putString(KEY_PAT, sha(pat.trim())).apply(); }
    public static void clearPin(Context c) { sp(c).edit().remove(KEY_PIN).apply(); }
    public static void clearPattern(Context c) { sp(c).edit().remove(KEY_PAT).apply(); }
    public static void clearAllLocks(Context c) { sp(c).edit().remove(KEY_PIN).remove(KEY_PAT).apply(); sUnlocked = true; }

    public static void setPrimaryPriority(Context c, String p) { sp(c).edit().putString(KEY_PRI, p).apply(); }
    public static String getPrimaryPriority(Context c) { return sp(c).getString(KEY_PRI, PRIORITY_PIN); }

    public static String getEffectivePrimaryLockMode(Context c) {
        String p = getPrimaryPriority(c);
        if (PRIORITY_PATTERN.equals(p) && isPatternConfigured(c)) return PRIORITY_PATTERN;
        if (PRIORITY_PIN.equals(p) && isPinConfigured(c)) return PRIORITY_PIN;
        if (isPinConfigured(c)) return PRIORITY_PIN;
        if (isPatternConfigured(c)) return PRIORITY_PATTERN;
        return PRIORITY_PIN;
    }

    public static int getPrimaryLockType(Context c) {
        if (!isLockEnabled(c)) return LOCK_NONE;
        return PRIORITY_PATTERN.equals(getEffectivePrimaryLockMode(c)) ? LOCK_PATTERN : LOCK_PIN;
    }

    public static boolean verifyPin(Context c, String v) { return v != null && !sp(c).getString(KEY_PIN, "").isEmpty() && sp(c).getString(KEY_PIN, "").equals(sha(v.trim())); }
    public static boolean verifyPattern(Context c, String v) { return v != null && !sp(c).getString(KEY_PAT, "").isEmpty() && sp(c).getString(KEY_PAT, "").equals(sha(v.trim())); }

    public static boolean isAntiUninstallActive(Context c) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) c.getSystemService(Context.DEVICE_POLICY_SERVICE);
            return dpm != null && dpm.isAdminActive(new ComponentName(c, VaultDeviceAdminReceiver.class));
        } catch (Throwable t) { return false; }
    }

    public static boolean isDeviceAdminActive(Context c) {
        return isAntiUninstallActive(c);
    }

    public static void requestEnableAntiUninstall(Activity act, int reqCode) {
        try {
            Intent i = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
            i.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, new ComponentName(act, VaultDeviceAdminReceiver.class));
            act.startActivityForResult(i, reqCode);
        } catch (Throwable ignored) {}
    }

    public static void disableAntiUninstall(Context c) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) c.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(c, VaultDeviceAdminReceiver.class);
            if (dpm != null && dpm.isAdminActive(cn)) dpm.removeActiveAdmin(cn);
        } catch (Throwable ignored) {}
    }

    private static String sha(String s) {
        try {
            byte[] d = MessageDigest.getInstance("SHA-256").digest(s.getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : d) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) { return s; }
    }
}
""",
    )

    write_file(
        "app/src/main/java/com/veyravault/space/security/VaultDeviceAdminReceiver.java",
        """package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;
import com.veyravault.space.helper.LocaleHelper;
import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {
    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        SecurityManager.setSessionUnlocked(false);
        try {
            Intent li = new Intent(context, SecurityLockActivity.class);
            li.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            li.putExtra("anti_uninstall_block", true);
            context.startActivity(li);
        } catch (Throwable ignored) {}
        String msg = LocaleHelper.isPersian(context)
            ? "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است."
            : "⛔ Uninstall is not permitted! Removal or deactivation of this app is blocked.";
        Toast.makeText(context, msg, Toast.LENGTH_LONG).show();
        return msg;
    }
}
""",
    )

    part2_path = os.path.join(ROOT, "scripts", "upgrade_v3_part2.py")
    if os.path.exists(part2_path):
        with open(part2_path, "r", encoding="utf-8") as f:
            p2 = f.read()
        p2 = p2.replace("Gravity.CENTER_horizontal", "Gravity.CENTER_HORIZONTAL")
        p2 = p2.replace(
            "package com.veyravault.space.ui;\n",
            "package com.veyravault.space.ui;\nimport com.veyravault.space.helper.BaseActivity;\n",
        )
        p2 = re.sub(
            r"public\s+class\s+MainActivity\b[^{]*\{",
            "public class MainActivity extends BaseActivity {",
            p2,
        )
        for fn in ["dp", "roundedBg", "makeCard", "isPersian", "isFa", "tr"]:
            p2 = re.sub(r"private\s+(\w+\s+" + fn + r"\s*\()", r"public \1", p2)

        marker = "# [AUTO-SYNC-SECURITY-LOCK-V3-FINAL]"
        if marker not in p2:
            p2 += '''

# [AUTO-SYNC-SECURITY-LOCK-V3-FINAL]
write_file(
    "app/src/main/java/com/veyravault/space/ui/SecurityLockActivity.java",
    r"""package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.helper.BaseActivity;
import com.veyravault.space.helper.PatternLockView;
import com.veyravault.space.security.SecurityManager;

public class SecurityLockActivity extends BaseActivity {
    public static final String EXTRA_ANTI_UNINSTALL_BLOCK = "anti_uninstall_block";
    private String currentMode;
    private int failedAttempts = 0;
    private LinearLayout modeContainer;
    private TextView fallbackSwitchBtn;
    private EditText pinInput;
    private PatternLockView patternView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (!SecurityManager.isLockEnabled(this)) {
            SecurityManager.setSessionUnlocked(true);
            finish();
            return;
        }
        currentMode = SecurityManager.getEffectivePrimaryLockMode(this);
        buildUi();
    }

    private void buildUi() {
        boolean fa = isPersian();
        boolean antiBlock = getIntent() != null && getIntent().getBooleanExtra(EXTRA_ANTI_UNINSTALL_BLOCK, false);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.parseColor("#090D16"));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        int pad = dp(24);
        root.setPadding(pad, pad, pad, pad);

        if (antiBlock) {
            LinearLayout alertCard = makeCard("#450A0A", "#EF4444", 14);
            TextView alertTxt = new TextView(this);
            alertTxt.setTextColor(Color.parseColor("#FCA5A5"));
            alertTxt.setTextSize(14f);
            alertTxt.setTypeface(Typeface.DEFAULT_BOLD);
            alertTxt.setGravity(Gravity.CENTER);
            alertTxt.setText(fa
                ? "⛔ حذف مقدور نمی‌باشد!\\nعملیات حذف یا غیرفعال‌سازی این برنامه مسدود است."
                : "⛔ Uninstall is not permitted!\\nRemoval or deactivation of this app is blocked.");
            alertCard.addView(alertTxt);
            LinearLayout.LayoutParams alp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            alp.bottomMargin = dp(18);
            root.addView(alertCard, alp);
        }

        LinearLayout lockCard = makeCard("#111827", "#1E293B", 18);
        lockCard.setGravity(Gravity.CENTER_HORIZONTAL);

        TextView title = new TextView(this);
        title.setText(fa ? "🔒 ورود امنیتی VeyraVault" : "🔒 VeyraVault Security Lock");
        title.setTextColor(Color.WHITE);
        title.setTextSize(19f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(4), 0, dp(10));
        lockCard.addView(title);

        modeContainer = new LinearLayout(this);
        modeContainer.setOrientation(LinearLayout.VERTICAL);
        modeContainer.setGravity(Gravity.CENTER_HORIZONTAL);
        lockCard.addView(modeContainer, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));

        fallbackSwitchBtn = new TextView(this);
        fallbackSwitchBtn.setTextColor(Color.parseColor("#38BDF8"));
        fallbackSwitchBtn.setTextSize(14f);
        fallbackSwitchBtn.setTypeface(Typeface.DEFAULT_BOLD);
        fallbackSwitchBtn.setGravity(Gravity.CENTER);
        fallbackSwitchBtn.setPadding(dp(10), dp(14), dp(10), dp(6));
        fallbackSwitchBtn.setVisibility(View.GONE);
        fallbackSwitchBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (SecurityManager.PRIORITY_PIN.equals(currentMode) && SecurityManager.isPatternConfigured(SecurityLockActivity.this)) {
                    currentMode = SecurityManager.PRIORITY_PATTERN;
                } else if (SecurityManager.isPinConfigured(SecurityLockActivity.this)) {
                    currentMode = SecurityManager.PRIORITY_PIN;
                }
                renderActiveLockMode();
            }
        });
        lockCard.addView(fallbackSwitchBtn);
        root.addView(lockCard, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        scroll.addView(root);
        setContentView(scroll);
        renderActiveLockMode();
    }

    private void renderActiveLockMode() {
        boolean fa = isPersian();
        modeContainer.removeAllViews();
        if (SecurityManager.PRIORITY_PATTERN.equals(currentMode) && SecurityManager.isPatternConfigured(this)) {
            patternView = new PatternLockView(this);
            LinearLayout.LayoutParams plp = new LinearLayout.LayoutParams(dp(250), dp(250));
            plp.gravity = Gravity.CENTER_HORIZONTAL;
            patternView.setOnPatternListener(new PatternLockView.OnPatternListener() {
                @Override
                public void onPatternDetected(String patternValue) {
                    if (SecurityManager.verifyPattern(SecurityLockActivity.this, patternValue)) {
                        SecurityManager.setSessionUnlocked(true);
                        finish();
                    } else {
                        patternView.clearPattern();
                        failedAttempts++;
                        Toast.makeText(SecurityLockActivity.this, fa ? "الگو اشتباه است!" : "Incorrect pattern!", Toast.LENGTH_SHORT).show();
                        updateFallbackPrompt();
                    }
                }
            });
            modeContainer.addView(patternView, plp);
        } else {
            pinInput = new EditText(this);
            pinInput.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
            pinInput.setTextColor(Color.WHITE);
            pinInput.setHintTextColor(Color.parseColor("#64748B"));
            pinInput.setHint(fa ? "رمز پین..." : "PIN code...");
            pinInput.setGravity(Gravity.CENTER);
            pinInput.setBackground(roundedBg("#1E293B", "#334155", 10, 1));
            pinInput.setPadding(dp(14), dp(12), dp(14), dp(12));
            LinearLayout.LayoutParams elp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            elp.bottomMargin = dp(12);
            modeContainer.addView(pinInput, elp);

            Button unlockBtn = new Button(this);
            unlockBtn.setText(fa ? "بازگشایی قفل ✓" : "Unlock ✓");
            unlockBtn.setTextColor(Color.WHITE);
            unlockBtn.setBackground(roundedBg("#0284C7", "#38BDF8", 10, 1));
            unlockBtn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    if (SecurityManager.verifyPin(SecurityLockActivity.this, pinInput.getText().toString().trim())) {
                        SecurityManager.setSessionUnlocked(true);
                        finish();
                    } else {
                        pinInput.setText("");
                        failedAttempts++;
                        Toast.makeText(SecurityLockActivity.this, fa ? "رمز اشتباه است!" : "Incorrect PIN!", Toast.LENGTH_SHORT).show();
                        updateFallbackPrompt();
                    }
                }
            });
            modeContainer.addView(unlockBtn, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        }
        updateFallbackPrompt();
    }

    private void updateFallbackPrompt() {
        boolean fa = isPersian();
        if (SecurityManager.hasBothLocksConfigured(this)) {
            fallbackSwitchBtn.setVisibility(View.VISIBLE);
            if (SecurityManager.PRIORITY_PIN.equals(currentMode)) {
                fallbackSwitchBtn.setText(fa ? "آیا از الگو استفاده می‌کنید؟ ورود با الگو ⬅" : "Switch to Pattern ⬅");
            } else {
                fallbackSwitchBtn.setText(fa ? "آیا از رمز پین استفاده می‌کنید؟ ورود با پین ⬅" : "Switch to PIN ⬅");
            }
        } else {
            fallbackSwitchBtn.setVisibility(View.GONE);
        }
    }

    @Override
    public void onBackPressed() {
        moveTaskToBack(true);
    }
}
""",
)
'''
        with open(part2_path, "w", encoding="utf-8") as f:
            f.write(p2)


if __name__ == "__main__":
    clean_legacy_sources()
    patch_app_build_gradle()
    generate_resources()
    generate_java_core()
    print("=== Part 1 Completed Successfully ===")
