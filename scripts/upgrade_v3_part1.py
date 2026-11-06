#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Upgrade Script - Part 1 (Final Complete & Synchronized Edition)
Wipes legacy v1/v2 Java & layout files and generates all v3.0 Core, Helper, Security,
and Resource files with 100% matching method/field signatures for Part 2 UI Activities.
"""

import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.join(ROOT, "app")
MAIN_DIR = os.path.join(APP_DIR, "src", "main")
JAVA_BASE = os.path.join(MAIN_DIR, "java", "com", "veyravault", "space")
RES_DIR = os.path.join(MAIN_DIR, "res")
ASSETS_DIR = os.path.join(MAIN_DIR, "assets")


def write_file(rel_path, content):
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.lstrip())
    print(f"[v3-part1] Wrote: {rel_path}")


def clean_legacy_sources():
    if os.path.exists(JAVA_BASE):
        shutil.rmtree(JAVA_BASE)
        print(f"[v3-part1] Cleaned legacy Java directory: {JAVA_BASE}")
    layout_dir = os.path.join(RES_DIR, "layout")
    if os.path.exists(layout_dir):
        shutil.rmtree(layout_dir)
        print(f"[v3-part1] Cleaned legacy layout directory: {layout_dir}")


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
    txt = txt.replace('versionCode 1', 'versionCode 3').replace('versionCode 2', 'versionCode 3')
    txt = txt.replace('versionName "1.0.0"', 'versionName "3.0.0"').replace('versionName "2.0.0"', 'versionName "3.0.0"')
    with open(gradle_path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[v3-part1] Patched app/build.gradle for v3.0.0 + osmdroid")


def generate_resources():
    # 1. Apache 2.0 attribution
    write_file(
        "app/src/main/assets/NOTICE_APACHE_2.txt",
        """
VeyraVault v3.0 - Multi-Space & Privacy Virtualization Platform
Copyright (C) 2025 VeyraVault Project
Contact Email: Vaultveyra@gmail.com
Official Telegram: https://t.me/VaultVeyra

Licensed under the Apache License, Version 2.0 (the "License").
Powered by open-source BlackBox Virtual Engine (https://github.com/ALEX5402/NewBlackbox).
Zero Telemetry, Zero Ads, 100% Local & Independent Execution.
""",
    )

    # 2. Device Admin XML policy
    write_file(
        "app/src/main/res/xml/device_admin_policies.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <watch-login />
    </uses-policies>
</device-admin>
""",
    )

    # 3. Launcher Icon Drawable (@drawable/ic_launcher)
    write_file(
        "app/src/main/res/drawable/ic_launcher.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#0F172A"
        android:pathData="M0,0h108v108h-108z"/>
    <path
        android:fillColor="#1E293B"
        android:pathData="M54,14L88,30V56C88,77.5 73.5,95.2 54,100C34.5,95.2 20,77.5 20,56V30L54,14Z"/>
    <path
        android:fillColor="#38BDF8"
        android:pathData="M54,22L80,34.5V55C80,72.2 68.9,86.8 54,91C39.1,86.8 28,72.2 28,55V34.5L54,22Z"/>
    <path
        android:fillColor="#0F172A"
        android:pathData="M42,42L54,72L66,42H59L54,56L49,42H42Z"/>
</vector>
""",
    )

    # 4. SVG Navigation Bar Vector Icons
    write_file(
        "app/src/main/res/drawable/ic_nav_dashboard.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M3,13h8V3H3V13zM3,21h8v-6H3V21zM13,21h8V11h-8V21zM13,3v6h8V3H13z"/>
</vector>
""",
    )

    write_file(
        "app/src/main/res/drawable/ic_nav_spaces.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M4,8h4V4H4V8zM10,20h4v-4h-4V20zM4,20h4v-4H4V20zM4,14h4v-4H4V14zM10,14h4v-4h-4V14zM16,4v4h4V4H16zM10,8h4V4h-4V8zM16,14h4v-4h-4V14zM16,20h4v-4h-4V20z"/>
</vector>
""",
    )

    write_file(
        "app/src/main/res/drawable/ic_nav_add.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6V13z"/>
</vector>
""",
    )

    write_file(
        "app/src/main/res/drawable/ic_nav_guide.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M18,2H6C4.9,2 4,2.9 4,4v16c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V4C20,2.9 19.1,2 18,2zM6,4h5v8l-2.5,-1.5L6,12V4z"/>
</vector>
""",
    )

    write_file(
        "app/src/main/res/drawable/ic_nav_settings.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"/>
</vector>
""",
    )

    # 5. Strings & Styles
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

    # 6. AndroidManifest.xml
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

        <!-- Disguise Aliases -->
        <activity-alias
            android:name="com.veyravault.space.AliasCalculator"
            android:enabled="false"
            android:exported="true"
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
            android:enabled="false"
            android:exported="true"
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
            android:enabled="false"
            android:exported="true"
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
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/device_admin_policies" />
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
    # 1. VeyraApplication.java
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

    public static Context getAppContext() {
        return sContext;
    }

    @Override
    protected void attachBaseContext(Context base) {
        sContext = base;
        Context localized = LocaleHelper.onAttach(base);
        super.attachBaseContext(localized);
        try {
            BlackBoxCore.get().doAttachBaseContext(base, new ClientConfiguration() {
                @Override
                public String getHostPackageName() {
                    return base.getPackageName();
                }

                @Override
                public boolean isEnableDaemonService() {
                    return true;
                }

                public boolean isHideRoot() {
                    return true;
                }

                public boolean isHideXposed() {
                    return true;
                }
            });
        } catch (Throwable t) {
            t.printStackTrace();
        }
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
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
""",
    )

    # 2. JalaliClockUtil.java
    write_file(
        "app/src/main/java/com/veyravault/space/helper/JalaliClockUtil.java",
        """package com.veyravault.space.helper;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

public class JalaliClockUtil {

    private static final String[] PERSIAN_MONTHS_FA = {
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    };

    private static final String[] PERSIAN_MONTHS_EN = {
        "Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad", "Shahrivar",
        "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand"
    };

    private static final String[] PERSIAN_WEEKDAYS_FA = {
        "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"
    };

    private static final String[] PERSIAN_WEEKDAYS_EN = {
        "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
    };

    public static String getTehranTimeString() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("Asia/Tehran"));
        return sdf.format(new Date());
    }

    public static String getNewYorkTimeString() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
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
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        Calendar cal = Calendar.getInstance(tz, Locale.US);
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int dow = cal.get(Calendar.DAY_OF_WEEK) - 1;
        int[] jalali = gregorianToJalali(gy, gm, gd);
        int jy = jalali[0];
        int jm = jalali[1];
        int jd = jalali[2];
        if (isFa) {
            String wd = (dow >= 0 && dow < 7) ? PERSIAN_WEEKDAYS_FA[dow] : "";
            String mn = (jm >= 1 && jm <= 12) ? PERSIAN_MONTHS_FA[jm - 1] : "";
            return toPersianDigits(wd + " " + jd + " " + mn + " " + jy);
        } else {
            String wd = (dow >= 0 && dow < 7) ? PERSIAN_WEEKDAYS_EN[dow] : "";
            String mn = (jm >= 1 && jm <= 12) ? PERSIAN_MONTHS_EN[jm - 1] : "";
            return wd + ", " + jd + " " + mn + " " + jy;
        }
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

    public static String toPersianDigits(String input) {
        if (input == null) return "";
        char[] persian = {'۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'};
        StringBuilder sb = new StringBuilder(input.length());
        for (int i = 0; i < input.length(); i++) {
            char c = input.charAt(i);
            if (c >= '0' && c <= '9') {
                sb.append(persian[c - '0']);
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }
}
""",
    )

    # 3. LocaleHelper.java
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
    private static final String PREF_NAME = "veyra_locale_prefs";
    private static final String KEY_LANG = "app_lang";

    public static Context onAttach(Context context) {
        String lang = getLanguage(context);
        return setLocale(context, lang);
    }

    public static String getLanguage(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        return sp.getString(KEY_LANG, "fa");
    }

    public static boolean isPersian(Context context) {
        return "fa".equalsIgnoreCase(getLanguage(context));
    }

    public static Context toggleLanguage(Context context) {
        String next = isPersian(context) ? "en" : "fa";
        return setLocale(context, next);
    }

    public static Context setLocale(Context context, String language) {
        SharedPreferences sp = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        sp.edit().putString(KEY_LANG, language).apply();

        Locale locale = new Locale(language);
        Locale.setDefault(locale);

        Resources res = context.getResources();
        Configuration config = new Configuration(res.getConfiguration());
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            config.setLocale(locale);
            config.setLayoutDirection(locale);
            return context.createConfigurationContext(config);
        } else {
            config.locale = locale;
            res.updateConfiguration(config, res.getDisplayMetrics());
            return context;
        }
    }
}
""",
    )

    # 4. BaseActivity.java
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

    protected void applyDirection() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            getWindow().getDecorView().setLayoutDirection(
                 isPersian() ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
    }

    public boolean isFa() {
        return LocaleHelper.isPersian(this);
    }

    public boolean isPersian() {
        return LocaleHelper.isPersian(this);
    }

    public void switchLanguageInstant() {
        LocaleHelper.toggleLanguage(this);
        recreate();
    }

    public void triggerQuickLock() {
        if (SecurityManager.isLockEnabled(this)) {
            SecurityManager.setSessionUnlocked(false);
            Intent i = new Intent(this, SecurityLockActivity.class);
            startActivity(i);
        }
    }

    public String tr(String faText, String enText) {
        return isPersian() ? faText : enText;
    }

    public int dp(int value) {
        float density = getResources().getDisplayMetrics().density;
        return Math.round(value * density);
    }

    public GradientDrawable roundedBg(String fillHex, String strokeHex, int radiusDp, int strokeWidthDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(fillHex));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeWidthDp > 0) {
            gd.setStroke(dp(strokeWidthDp), Color.parseColor(strokeHex));
        }
        return gd;
    }

    public LinearLayout makeCard(String fillHex, String strokeHex, int radiusDp) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(roundedBg(fillHex, strokeHex, radiusDp, 1));
        int pad = dp(14);
        card.setPadding(pad, pad, pad, pad);
        return card;
    }
}
""",
    )

    # 5a. GmsSupportManager.java in helper package
    gms_code = """package %PKG%;

import android.content.Context;
import android.content.SharedPreferences;
import java.lang.reflect.Method;
import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    private static final String PREF = "veyra_gms_prefs";
    private static final String KEY_AUTO_GMS = "gms_auto_enabled";

    public static boolean isGmsEnabled(Context ctx) {
        SharedPreferences sp = ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
        return sp.getBoolean(KEY_AUTO_GMS, true);
    }

    public static void setGmsEnabled(Context ctx, boolean enabled) {
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE)
           .edit().putBoolean(KEY_AUTO_GMS, enabled).apply();
        if (enabled) {
            installGmsForAllSpaces();
        }
    }

    public static boolean enableGmsAcrossAllSpaces(Context ctx) {
        setGmsEnabled(ctx, true);
        return installGmsForAllSpaces();
    }

    public static void autoInitializeGmsIfNeeded(Context ctx) {
        if (isGmsEnabled(ctx)) {
            installGmsForAllSpaces();
        }
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
        for (int space = 0; space < 5; space++) {
            ensureGmsForSpace(space);
        }
        return true;
    }
}
"""
    write_file(
        "app/src/main/java/com/veyravault/space/helper/GmsSupportManager.java",
        gms_code.replace("%PKG%", "com.veyravault.space.helper"),
    )
    write_file(
        "app/src/main/java/com/veyravault/space/core/GmsSupportManager.java",
        gms_code.replace("%PKG%", "com.veyravault.space.core"),
    )

    # 6. AppDisguiseManager.java
    write_file(
        "app/src/main/java/com/veyravault/space/helper/AppDisguiseManager.java",
        """package com.veyravault.space.helper;

import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;

public class AppDisguiseManager {
    private static final String PREF = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode_v3";

    public static final String MODE_DEFAULT = "default";
    public static final String MODE_CALCULATOR = "calculator";
    public static final String MODE_CALENDAR = "calendar";
    public static final String MODE_NOTES = "notes";

    public static String getCurrentMode(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).getString(KEY_MODE, MODE_DEFAULT);
    }

    public static String getCurrentDisguiseMode(Context ctx) {
        return getCurrentMode(ctx);
    }

    public static void applyDisguiseMode(Context ctx, String mode) {
        if (mode == null) mode = MODE_DEFAULT;
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putString(KEY_MODE, mode).apply();
        PackageManager pm = ctx.getPackageManager();
        String pkg = ctx.getPackageName();

        setComponentState(pm, new ComponentName(pkg, "com.veyravault.space.ui.MainActivity"), MODE_DEFAULT.equals(mode));
        setComponentState(pm, new ComponentName(pkg, "com.veyravault.space.AliasCalculator"), MODE_CALCULATOR.equals(mode));
        setComponentState(pm, new ComponentName(pkg, "com.veyravault.space.AliasCalendar"), MODE_CALENDAR.equals(mode));
        setComponentState(pm, new ComponentName(pkg, "com.veyravault.space.AliasNotes"), MODE_NOTES.equals(mode));
    }

    private static void setComponentState(PackageManager pm, ComponentName cn, boolean enable) {
        try {
            pm.setComponentEnabledSetting(
                cn,
                enable ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED : PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP
            );
        } catch (Throwable ignored) {}
    }
}
""",
    )

    # 7. PatternLockView.java
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

    public interface OnPatternListener {
        void onPatternDetected(String patternValue);
    }

    private final List<Integer> selectedNodes = new ArrayList<>();
    private final Paint circlePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private float curX, curY;
    private boolean isDrawing = false;
    private OnPatternListener listener;

    public PatternLockView(Context context) {
        super(context);
        circlePaint.setColor(Color.parseColor("#334155"));
        circlePaint.setStyle(Paint.Style.FILL);

        activePaint.setColor(Color.parseColor("#38BDF8"));
        activePaint.setStyle(Paint.Style.FILL);

        linePaint.setColor(Color.parseColor("#38BDF8"));
        linePaint.setStrokeWidth(10f);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setOnPatternListener(OnPatternListener l) {
        this.listener = l;
    }

    public void clearPattern() {
        selectedNodes.clear();
        invalidate();
    }

    private float getNodeX(int index) {
        int col = index % 3;
        float step = getWidth() / 4f;
        return step * (col + 1);
    }

    private float getNodeY(int index) {
        int row = index / 3;
        float step = getHeight() / 4f;
        return step * (row + 1);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float radius = Math.min(getWidth(), getHeight()) / 14f;

        for (int i = 0; i < selectedNodes.size() - 1; i++) {
            int a = selectedNodes.get(i);
            int b = selectedNodes.get(i + 1);
            canvas.drawLine(getNodeX(a), getNodeY(a), getNodeX(b), getNodeY(b), linePaint);
        }
        if (isDrawing && !selectedNodes.isEmpty()) {
            int last = selectedNodes.get(selectedNodes.size() - 1);
            canvas.drawLine(getNodeX(last), getNodeY(last), curX, curY, linePaint);
        }

        for (int i = 0; i < 9; i++) {
            float nx = getNodeX(i);
            float ny = getNodeY(i);
            boolean active = selectedNodes.contains(i);
            canvas.drawCircle(nx, ny, radius, active ? activePaint : circlePaint);
            if (active) {
                Paint center = new Paint(Paint.ANTI_ALIAS_FLAG);
                center.setColor(Color.WHITE);
                canvas.drawCircle(nx, ny, radius * 0.4f, center);
            }
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        curX = event.getX();
        curY = event.getY();
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                selectedNodes.clear();
                isDrawing = true;
                checkHit(curX, curY);
                invalidate();
                return true;
            case MotionEvent.ACTION_MOVE:
                checkHit(curX, curY);
                invalidate();
                return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                isDrawing = false;
                if (!selectedNodes.isEmpty() && listener != null) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < selectedNodes.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(selectedNodes.get(i) + 1);
                    }
                    listener.onPatternDetected(sb.toString());
                }
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y) {
        float hitRadius = Math.min(getWidth(), getHeight()) / 8f;
        for (int i = 0; i < 9; i++) {
            if (selectedNodes.contains(i)) continue;
            float dx = x - getNodeX(i);
            float dy = y - getNodeY(i);
            if (Math.hypot(dx, dy) <= hitRadius) {
                selectedNodes.add(i);
                break;
            }
        }
    }
}
""",
    )

    # 8. CloneMetadataStore.java
    write_file(
        "app/src/main/java/com/veyravault/space/core/CloneMetadataStore.java",
        """package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class CloneMetadataStore {
    private static final String PREF = "veyra_clone_metadata_v3";

    public static class DevicePreset {
        public final String displayTitle;
        public final String brand;
        public final String model;
        public final String deviceCode;

        public DevicePreset(String displayTitle, String brand, String model, String deviceCode) {
            this.displayTitle = displayTitle;
            this.brand = brand;
            this.model = model;
            this.deviceCode = deviceCode;
        }
    }

    public static class RegionPreset {
        public final String regionName;
        public final double lat;
        public final double lon;
        public final String timezoneId;
        public final String simulatedIp;

        public RegionPreset(String regionName, double lat, double lon, String timezoneId, String simulatedIp) {
            this.regionName = regionName;
            this.lat = lat;
            this.lon = lon;
            this.timezoneId = timezoneId;
            this.simulatedIp = simulatedIp;
        }
    }

    public static List<DevicePreset> getDevicePresets() {
        List<DevicePreset> list = new ArrayList<>();
        list.add(new DevicePreset("Samsung Galaxy S24 Ultra", "samsung", "SM-S928B", "e3q"));
        list.add(new DevicePreset("Samsung Galaxy S23 Ultra", "samsung", "SM-S918B", "dm3q"));
        list.add(new DevicePreset("Apple iPhone 16 Pro Max", "Apple", "iPhone17,2 (iOS 18)", "iPhone16ProMax"));
        list.add(new DevicePreset("Apple iPhone 15 Pro Max", "Apple", "iPhone16,2 (iOS 17)", "iPhone15ProMax"));
        list.add(new DevicePreset("Apple iPhone 14 Pro", "Apple", "iPhone15,2", "iPhone14Pro"));
        list.add(new DevicePreset("Apple iPad Pro M4", "Apple", "iPad16,6", "iPadProM4"));
        list.add(new DevicePreset("Google Pixel 9 Pro XL", "google", "Pixel 9 Pro XL", "komodo"));
        list.add(new DevicePreset("Google Pixel 8 Pro", "google", "Pixel 8 Pro", "husky"));
        list.add(new DevicePreset("Xiaomi 14 Ultra", "Xiaomi", "24030PN60G", "aurora"));
        list.add(new DevicePreset("OnePlus 12 (Global)", "OnePlus", "CPH2581", "waffle"));
        return list;
    }

    public static List<RegionPreset> getRegionPresets() {
        List<RegionPreset> list = new ArrayList<>();
        list.add(new RegionPreset("Falkenstein, Germany", 50.4779, 12.3713, "Europe/Berlin", "88.198.48.21"));
        list.add(new RegionPreset("Frankfurt, Germany", 50.1109, 8.6821, "Europe/Berlin", "138.201.92.14"));
        list.add(new RegionPreset("Amsterdam, Netherlands", 52.3676, 4.9041, "Europe/Amsterdam", "95.211.198.45"));
        list.add(new RegionPreset("London, United Kingdom", 51.5074, -0.1278, "Europe/London", "51.140.104.22"));
        list.add(new RegionPreset("New York, United States", 40.7128, -74.0060, "America/New_York", "104.244.42.65"));
        list.add(new RegionPreset("Helsinki, Finland", 60.1699, 24.9384, "Europe/Helsinki", "65.108.44.10"));
        list.add(new RegionPreset("Istanbul, Turkey", 41.0082, 28.9784, "Europe/Istanbul", "185.125.33.19"));
        list.add(new RegionPreset("Dubai, UAE", 25.2048, 55.2708, "Asia/Dubai", "94.200.14.88"));
        list.add(new RegionPreset("Tehran, Iran", 35.6892, 51.3890, "Asia/Tehran", "5.160.120.11"));
        return list;
    }

    private static SharedPreferences sp(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public static void ensureDefaultsInitialized(Context ctx) {
        SharedPreferences p = sp(ctx);
        if (!p.contains("global_initialized_v3")) {
            p.edit()
                .putBoolean("global_initialized_v3", true)
                .putString("global_brand", "samsung")
                .putString("global_model", "SM-S928B")
                .putString("global_display", "Samsung Galaxy S24 Ultra")
                .putString("global_region", "Falkenstein, Germany")
                .putString("global_lat", "50.4779")
                .putString("global_lon", "12.3713")
                .putString("global_tz", "Europe/Berlin")
                .putString("global_sim_ip", "88.198.48.21")
                .apply();
        }
    }

    public static String getSpaceName(Context ctx, int spaceId, boolean isFa) {
        String custom = sp(ctx).getString("space_custom_name_" + spaceId, "");
        if (custom != null && !custom.trim().isEmpty()) {
            return custom.trim();
        }
        int num = spaceId + 1;
        return isFa ? ("فضای " + num) : ("Space " + num);
    }

    public static void setSpaceCustomName(Context ctx, int spaceId, String name) {
        sp(ctx).edit().putString("space_custom_name_" + spaceId, name == null ? "" : name.trim()).apply();
    }

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model) {
        String b = brand == null ? "samsung" : brand.trim();
        String m = model == null ? "SM-S928B" : model.trim();
        String display = b + " " + m;
        for (DevicePreset dp : getDevicePresets()) {
            if (dp.brand.equalsIgnoreCase(b) && dp.model.equalsIgnoreCase(m)) {
                display = dp.displayTitle;
                break;
            }
        }
        setGlobalDeviceIdentity(ctx, display, b, m);
    }

    public static void setGlobalDeviceIdentity(Context ctx, String display, String brand, String model) {
        sp(ctx).edit()
            .putString("global_display", display)
            .putString("global_brand", brand)
            .putString("global_model", model)
            .apply();
        VirtualHookManager.applyGlobalEnvironmentHooks(ctx);
    }

    public static String getGlobalDeviceDisplay(Context ctx) {
        ensureDefaultsInitialized(ctx);
        return sp(ctx).getString("global_display", "Samsung Galaxy S24 Ultra");
    }

    public static String getGlobalDeviceBrand(Context ctx) {
        ensureDefaultsInitialized(ctx);
        return sp(ctx).getString("global_brand", "samsung");
    }

    public static String getGlobalDeviceModel(Context ctx) {
        ensureDefaultsInitialized(ctx);
        return sp(ctx).getString("global_model", "SM-S928B");
    }

    public static void setGlobalRegionLocation(Context ctx, String regionName, double lat, double lon, String tz, String simIp) {
        sp(ctx).edit()
            .putString("global_region", regionName)
            .putString("global_lat", String.valueOf(lat))
            .putString("global_lon", String.valueOf(lon))
            .putString("global_tz", tz == null || tz.isEmpty() ? "Europe/Berlin" : tz)
            .putString("global_sim_ip", simIp == null || simIp.isEmpty() ? "88.198.48.21" : simIp)
            .apply();
        VirtualHookManager.applyGlobalEnvironmentHooks(ctx);
    }

    public static String getGlobalRegionName(Context ctx) {
        ensureDefaultsInitialized(ctx);
        return sp(ctx).getString("global_region", "Falkenstein, Germany");
    }

    public static double getGlobalLat(Context ctx) {
        ensureDefaultsInitialized(ctx);
        try {
            return Double.parseDouble(sp(ctx).getString("global_lat", "50.4779"));
        } catch (Exception e) {
            return 50.4779;
        }
    }

    public static double getGlobalLon(Context ctx) {
        ensureDefaultsInitialized(ctx);
        try {
            return Double.parseDouble(sp(ctx).getString("global_lon", "12.3713"));
        } catch (Exception e) {
            return 12.3713;
        }
    }

    public static String getGlobalTimezone(Context ctx) {
        ensureDefaultsInitialized(ctx);
        return sp(ctx).getString("global_tz", "Europe/Berlin");
    }

    public static String getGlobalSimulatedIp(Context ctx) {
        ensureDefaultsInitialized(ctx);
        return sp(ctx).getString("global_sim_ip", "88.198.48.21");
    }

    public static void setGlobalProxy(Context ctx, String host, int port) {
        setGlobalProxy(ctx, host, String.valueOf(port > 0 ? port : 0));
    }

    public static void setGlobalProxy(Context ctx, String host, String port) {
        sp(ctx).edit()
            .putString("proxy_host", host == null ? "" : host.trim())
            .putString("proxy_port", port == null ? "" : port.trim())
            .apply();
        VirtualHookManager.applyGlobalEnvironmentHooks(ctx);
    }

    public static String getGlobalProxyHost(Context ctx) {
        return sp(ctx).getString("proxy_host", "");
    }

    public static String getGlobalProxyPort(Context ctx) {
        return sp(ctx).getString("proxy_port", "");
    }

    private static String key(String pkg, int userId, String suffix) {
        return "clone_" + userId + "_" + pkg + "_" + suffix;
    }

    public static void setCustomAlias(Context ctx, String pkg, int userId, String alias) {
        sp(ctx).edit().putString(key(pkg, userId, "alias"), alias == null ? "" : alias.trim()).apply();
    }

    public static String getCustomAlias(Context ctx, String pkg, int userId) {
        return sp(ctx).getString(key(pkg, userId, "alias"), "");
    }

    public static void setCustomDeviceIdentity(Context ctx, String pkg, int userId, String display, String brand, String model) {
        sp(ctx).edit()
            .putBoolean(key(pkg, userId, "has_dev"), true)
            .putString(key(pkg, userId, "dev_display"), display)
            .putString(key(pkg, userId, "dev_brand"), brand)
            .putString(key(pkg, userId, "dev_model"), model)
            .apply();
    }

    public static void clearCustomDeviceIdentity(Context ctx, String pkg, int userId) {
        sp(ctx).edit()
            .putBoolean(key(pkg, userId, "has_dev"), false)
            .remove(key(pkg, userId, "dev_display"))
            .remove(key(pkg, userId, "dev_brand"))
            .remove(key(pkg, userId, "dev_model"))
            .apply();
    }

    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int userId) {
        return sp(ctx).getBoolean(key(pkg, userId, "has_dev"), false);
    }

    public static String getEffectiveDeviceDisplay(Context ctx, String pkg, int userId) {
        if (hasCustomDeviceIdentity(ctx, pkg, userId)) {
            return sp(ctx).getString(key(pkg, userId, "dev_display"), getGlobalDeviceDisplay(ctx));
        }
        return getGlobalDeviceDisplay(ctx);
    }

    public static String getEffectiveBrand(Context ctx, String pkg, int userId) {
        if (hasCustomDeviceIdentity(ctx, pkg, userId)) {
            return sp(ctx).getString(key(pkg, userId, "dev_brand"), getGlobalDeviceBrand(ctx));
        }
        return getGlobalDeviceBrand(ctx);
    }

    public static String getEffectiveModel(Context ctx, String pkg, int userId) {
        if (hasCustomDeviceIdentity(ctx, pkg, userId)) {
            return sp(ctx).getString(key(pkg, userId, "dev_model"), getGlobalDeviceModel(ctx));
        }
        return getGlobalDeviceModel(ctx);
    }

    public static void setCustomLocation(Context ctx, String pkg, int userId, String regionName, double lat, double lon, String tz, String simIp) {
        sp(ctx).edit()
            .putBoolean(key(pkg, userId, "has_loc"), true)
            .putString(key(pkg, userId, "loc_region"), regionName == null || regionName.isEmpty() ? "Falkenstein, Germany" : regionName)
            .putString(key(pkg, userId, "loc_lat"), String.valueOf(lat))
            .putString(key(pkg, userId, "loc_lon"), String.valueOf(lon))
            .putString(key(pkg, userId, "loc_tz"), tz == null || tz.isEmpty() ? "Europe/Berlin" : tz)
            .putString(key(pkg, userId, "loc_ip"), simIp == null || simIp.isEmpty() ? "88.198.48.21" : simIp)
            .apply();
    }

    public static void clearCustomLocation(Context ctx, String pkg, int userId) {
        sp(ctx).edit()
            .putBoolean(key(pkg, userId, "has_loc"), false)
            .remove(key(pkg, userId, "loc_region"))
            .remove(key(pkg, userId, "loc_lat"))
            .remove(key(pkg, userId, "loc_lon"))
            .remove(key(pkg, userId, "loc_tz"))
            .remove(key(pkg, userId, "loc_ip"))
            .apply();
    }

    public static boolean hasCustomLocation(Context ctx, String pkg, int userId) {
        return sp(ctx).getBoolean(key(pkg, userId, "has_loc"), false);
    }

    public static String getEffectiveRegionDisplay(Context ctx, String pkg, int userId) {
        if (hasCustomLocation(ctx, pkg, userId)) {
            return sp(ctx).getString(key(pkg, userId, "loc_region"), getGlobalRegionName(ctx));
        }
        return getGlobalRegionName(ctx);
    }

    public static double getEffectiveLat(Context ctx, String pkg, int userId) {
        if (hasCustomLocation(ctx, pkg, userId)) {
            try {
                return Double.parseDouble(sp(ctx).getString(key(pkg, userId, "loc_lat"), "50.4779"));
            } catch (Exception ignored) {}
        }
        return getGlobalLat(ctx);
    }

    public static double getEffectiveLon(Context ctx, String pkg, int userId) {
        if (hasCustomLocation(ctx, pkg, userId)) {
            try {
                return Double.parseDouble(sp(ctx).getString(key(pkg, userId, "loc_lon"), "12.3713"));
            } catch (Exception ignored) {}
        }
        return getGlobalLon(ctx);
    }

    public static String getEffectiveTimezone(Context ctx, String pkg, int userId) {
        if (hasCustomLocation(ctx, pkg, userId)) {
            return sp(ctx).getString(key(pkg, userId, "loc_tz"), getGlobalTimezone(ctx));
        }
        return getGlobalTimezone(ctx);
    }

    public static String getEffectiveSimulatedIp(Context ctx, String pkg, int userId) {
        if (hasCustomLocation(ctx, pkg, userId)) {
            return sp(ctx).getString(key(pkg, userId, "loc_ip"), getGlobalSimulatedIp(ctx));
        }
        return getGlobalSimulatedIp(ctx);
    }

    public static void registerVaultedClone(Context ctx, String pkg, int userId) {
        SharedPreferences p = sp(ctx);
        Set<String> existing = new HashSet<>(p.getStringSet("vaulted_clones_" + userId, new HashSet<String>()));
        existing.add(pkg);
        p.edit().putStringSet("vaulted_clones_" + userId, existing).apply();
    }

    public static void unregisterVaultedClone(Context ctx, String pkg, int userId) {
        SharedPreferences p = sp(ctx);
        Set<String> existing = new HashSet<>(p.getStringSet("vaulted_clones_" + userId, new HashSet<String>()));
        existing.remove(pkg);
        p.edit().putStringSet("vaulted_clones_" + userId, existing).apply();
    }

    public static Set<String> getVaultedClones(Context ctx, int userId) {
        return new HashSet<>(sp(ctx).getStringSet("vaulted_clones_" + userId, new HashSet<String>()));
    }
}
""",
    )

    # 9. VirtualHookManager.java
    write_file(
        "app/src/main/java/com/veyravault/space/core/VirtualHookManager.java",
        """package com.veyravault.space.core;

import android.content.Context;
import android.os.Build;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Locale;
import java.util.TimeZone;

public class VirtualHookManager {

    public static void applyGlobalEnvironmentHooks(Context ctx) {
        try {
            String brand = CloneMetadataStore.getGlobalDeviceBrand(ctx);
            String model = CloneMetadataStore.getGlobalDeviceModel(ctx);
            String tz = CloneMetadataStore.getGlobalTimezone(ctx);
            String region = CloneMetadataStore.getGlobalRegionName(ctx);
            double lat = CloneMetadataStore.getGlobalLat(ctx);
            double lon = CloneMetadataStore.getGlobalLon(ctx);
            String simIp = CloneMetadataStore.getGlobalSimulatedIp(ctx);
            applyRuntimeIdentityAndRegion(brand, model, tz, region, lat, lon, simIp, ctx);
        } catch (Throwable ignored) {}
    }

    public static void prepareForCloneLaunch(Context ctx, String pkg, int userId) {
        try {
            String brand = CloneMetadataStore.getEffectiveBrand(ctx, pkg, userId);
            String model = CloneMetadataStore.getEffectiveModel(ctx, pkg, userId);
            String tz = CloneMetadataStore.getEffectiveTimezone(ctx, pkg, userId);
            String region = CloneMetadataStore.getEffectiveRegionDisplay(ctx, pkg, userId);
            double lat = CloneMetadataStore.getEffectiveLat(ctx, pkg, userId);
            double lon = CloneMetadataStore.getEffectiveLon(ctx, pkg, userId);
            String simIp = CloneMetadataStore.getEffectiveSimulatedIp(ctx, pkg, userId);

            applyRuntimeIdentityAndRegion(brand, model, tz, region, lat, lon, simIp, ctx);
            applyBlackBoxLocationAndDevice(pkg, userId, brand, model, lat, lon);
            installGmsAvailabilityBypass();
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private static void applyRuntimeIdentityAndRegion(
            String brand, String model, String tzId, String regionName,
            double lat, double lon, String simIp, Context ctx) {
        try {
            setBuildField("BRAND", brand);
            setBuildField("MANUFACTURER", brand);
            setBuildField("MODEL", model);
            setBuildField("PRODUCT", model);
            setBuildField("DEVICE", model.replaceAll("\\\\s+", ""));

            if (tzId != null && !tzId.isEmpty()) {
                TimeZone.setDefault(TimeZone.getTimeZone(tzId));
                System.setProperty("user.timezone", tzId);
            }

            System.setProperty("veyra.virtual.region", regionName);
            System.setProperty("veyra.virtual.lat", String.valueOf(lat));
            System.setProperty("veyra.virtual.lon", String.valueOf(lon));
            System.setProperty("veyra.virtual.ip", simIp);

            if (regionName != null && regionName.toLowerCase(Locale.US).contains("germany")) {
                System.setProperty("gsm.sim.operator.iso-country", "de");
                System.setProperty("gsm.operator.iso-country", "de");
            } else if (regionName != null && regionName.toLowerCase(Locale.US).contains("united states")) {
                System.setProperty("gsm.sim.operator.iso-country", "us");
                System.setProperty("gsm.operator.iso-country", "us");
            }

            String proxyHost = CloneMetadataStore.getGlobalProxyHost(ctx);
            String proxyPort = CloneMetadataStore.getGlobalProxyPort(ctx);
            if (proxyHost != null && !proxyHost.isEmpty() && proxyPort != null && !proxyPort.isEmpty() && !"0".equals(proxyPort)) {
                System.setProperty("socksProxyHost", proxyHost);
                System.setProperty("socksProxyPort", proxyPort);
                System.setProperty("http.proxyHost", proxyHost);
                System.setProperty("http.proxyPort", proxyPort);
                System.setProperty("https.proxyHost", proxyHost);
                System.setProperty("https.proxyPort", proxyPort);
            }
        } catch (Throwable ignored) {}
    }

    private static void applyBlackBoxLocationAndDevice(
            String pkg, int userId, String brand, String model, double lat, double lon) {
        try {
            Class<?> locMgrClass = Class.forName("top.niunaijun.blackbox.fake.frameworks.BLocationManager");
            Object locMgr = locMgrClass.getMethod("get").invoke(null);
            Class<?> bLocClass = Class.forName("top.niunaijun.blackbox.entity.location.BLocation");
            Object bLoc = bLocClass.getConstructor(double.class, double.class).newInstance(lat, lon);

            for (Method m : locMgrClass.getMethods()) {
                if (m.getName().equals("setPattern") && m.getParameterTypes().length == 1) {
                    m.invoke(locMgr, 2);
                } else if (m.getName().equals("setLocation") && m.getParameterTypes().length == 3) {
                    m.invoke(locMgr, userId, pkg, bLoc);
                } else if (m.getName().equals("setGlobalLocation") && m.getParameterTypes().length == 1) {
                    m.invoke(locMgr, bLoc);
                }
            }
        } catch (Throwable ignored) {}
    }

    public static void installGmsAvailabilityBypass() {
        try {
            System.setProperty("veyra.gms.SpoofAvailable", "true");
            Class<?> gmsUtil = Class.forName("com.google.android.gms.common.GooglePlayServicesUtil");
            Field f = gmsUtil.getDeclaredField("GOOGLE_PLAY_SERVICES_VERSION_CODE");
            f.setAccessible(true);
        } catch (Throwable ignored) {}
    }

    private static void setBuildField(String fieldName, String value) {
        if (value == null || value.isEmpty()) return;
        try {
            Field f = Build.class.getDeclaredField(fieldName);
            f.setAccessible(true);
            f.set(null, value);
        } catch (Throwable ignored) {}
    }
}
""",
    )

    # 10. Engine.java (Includes spaceId, customDeviceName, hasCustomDevice, effectiveRegion, hasCustomLoc)
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

    public static class ClonedApp extends AppModel {
    }

    public static class InstallOptionCandidate extends AppModel {
    }

    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(120);

    public static File getApkVaultDir(Context ctx, String pkg) {
        File dir = new File(ctx.getFilesDir(), "apk_vault/" + pkg);
        if (!dir.exists()) dir.mkdirs();
        return dir;
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
                File srcBase = new File(ai.sourceDir);
                File dstBase = new File(vaultDir, "base.apk");
                if (srcBase.exists() && (!dstBase.exists() || dstBase.length() != srcBase.length())) {
                    copyFile(srcBase, dstBase);
                    extractNativeLibsFromApk(dstBase, new File(vaultDir, "lib"));
                }
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP && ai.splitSourceDirs != null) {
                int idx = 0;
                for (String splitPath : ai.splitSourceDirs) {
                    idx++;
                    File splitSrc = new File(splitPath);
                    File splitDst = new File(vaultDir, "split_" + idx + ".apk");
                    if (splitSrc.exists()) {
                        if (!splitDst.exists() || splitDst.length() != splitSrc.length()) {
                            copyFile(splitSrc, splitDst);
                        }
                        extractNativeLibsFromApk(splitDst, new File(vaultDir, "lib"));
                    }
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    private static void extractNativeLibsFromApk(File apkFile, File outLibDir) {
        if (apkFile == null || !apkFile.exists()) return;
        String preferredAbi = (Build.SUPPORTED_ABIS != null && Build.SUPPORTED_ABIS.length > 0)
                ? Build.SUPPORTED_ABIS[0] : "arm64-v8a";
        ZipFile zf = null;
        try {
            zf = new ZipFile(apkFile);
            Enumeration<? extends ZipEntry> entries = zf.entries();
            while (entries.hasMoreElements()) {
                ZipEntry ze = entries.nextElement();
                String name = ze.getName();
                if (!ze.isDirectory() && name.startsWith("lib/") && name.endsWith(".so")) {
                    if (name.contains(preferredAbi) || name.contains("armeabi-v7a") || name.contains("arm64-v8a")) {
                        String soName = name.substring(name.lastIndexOf('/') + 1);
                        if (!outLibDir.exists()) outLibDir.mkdirs();
                        File outSo = new File(outLibDir, soName);
                        if (!outSo.exists() || outSo.length() != ze.getSize()) {
                            InputStream is = zf.getInputStream(ze);
                            FileOutputStream fos = new FileOutputStream(outSo);
                            byte[] buf = new byte[8192];
                            int len;
                            while ((len = is.read(buf)) > 0) {
                                fos.write(buf, 0, len);
                            }
                            fos.close();
                            is.close();
                        }
                    }
                }
            }
        } catch (Throwable ignored) {
        } finally {
            try { if (zf != null) zf.close(); } catch (Throwable ignored) {}
        }
    }

    private static void syncVaultLibsToBlackBoxAppDir(Context ctx, String pkg) {
        try {
            File vaultLib = new File(getApkVaultDir(ctx, pkg), "lib");
            if (!vaultLib.exists()) return;
            File[] soFiles = vaultLib.listFiles();
            if (soFiles == null || soFiles.length == 0) return;

            File dataDir = new File(ctx.getApplicationInfo().dataDir);
            File[] possibleAppLibDirs = new File[] {
                new File(dataDir, "virtual/data/app/" + pkg + "/lib"),
                new File(dataDir, "virtual/data/app/" + pkg + "/lib/arm64"),
                new File(dataDir, "virtual/data/app/" + pkg + "/lib/arm"),
                new File(ctx.getFilesDir(), "virtual/data/app/" + pkg + "/lib")
            };
            for (File targetDir : possibleAppLibDirs) {
                targetDir.mkdirs();
                for (File so : soFiles) {
                    File dst = new File(targetDir, so.getName());
                    if (!dst.exists() || dst.length() != so.length()) {
                        copyFile(so, dst);
                    }
                }
            }
        } catch (Throwable ignored) {}
    }

    private static void copyFile(File src, File dst) throws Exception {
        FileInputStream fis = new FileInputStream(src);
        FileOutputStream fos = new FileOutputStream(dst);
        byte[] buf = new byte[16384];
        int r;
        while ((r = fis.read(buf)) > 0) {
            fos.write(buf, 0, r);
        }
        fos.flush();
        fos.close();
        fis.close();
    }

    public static List<InstallOptionCandidate> getInstallCandidates(Context ctx) {
        List<AppModel> raw = getInstalledHostApps(ctx);
        List<InstallOptionCandidate> out = new ArrayList<>();
        for (AppModel m : raw) {
            InstallOptionCandidate c = new InstallOptionCandidate();
            c.packageName = m.packageName;
            c.name = m.name;
            c.icon = m.icon;
            c.isSystem = m.isSystem;
            out.add(c);
        }
        return out;
    }

    public static List<AppModel> getInstalledHostApps(Context ctx) {
        List<AppModel> result = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        String ownPkg = ctx.getPackageName();

        Intent mainIntent = new Intent(Intent.ACTION_MAIN, null);
        mainIntent.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> resolved = pm.queryIntentActivities(mainIntent, 0);
        Set<String> seen = new HashSet<>();

        for (ResolveInfo ri : resolved) {
            if (ri.activityInfo == null) continue;
            String pkg = ri.activityInfo.packageName;
            if (pkg == null || pkg.equals(ownPkg) || seen.contains(pkg)) continue;
            seen.add(pkg);

            try {
                ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
                AppModel m = new AppModel();
                m.packageName = pkg;
                CharSequence label = ai.loadLabel(pm);
                m.name = label != null ? label.toString() : pkg;
                m.icon = loadCachedIcon(pm, ai, pkg);
                m.isSystem = (ai.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
                result.add(m);
            } catch (Throwable ignored) {}
        }

        Collections.sort(result, new Comparator<AppModel>() {
            @Override
            public int compare(AppModel a, AppModel b) {
                if (a.isSystem != b.isSystem) {
                    return a.isSystem ? 1 : -1;
                }
                return a.name.compareToIgnoreCase(b.name);
            }
        });
        return result;
    }

    public static List<ClonedApp> getClonedApps(Context ctx, int userId) {
        List<ClonedApp> list = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Set<String> added = new HashSet<>();

        try {
            List<ApplicationInfo> installed = BlackBoxCore.get().getInstalledApplications(0, userId);
            if (installed != null) {
                for (ApplicationInfo info : installed) {
                    if (info == null || info.packageName == null) continue;
                    String pkg = info.packageName;
                    if (pkg.contains("google.android.gms") || pkg.contains("google.android.gsf") || pkg.equals(ctx.getPackageName())) {
                        continue;
                    }
                    ClonedApp model = buildClonedAppModel(ctx, pm, pkg, userId);
                    if (model != null) {
                        list.add(model);
                        added.add(pkg);
                        CloneMetadataStore.registerVaultedClone(ctx, pkg, userId);
                    }
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }

        Set<String> vaulted = CloneMetadataStore.getVaultedClones(ctx, userId);
        for (String pkg : vaulted) {
            if (added.contains(pkg)) continue;
            File vaultApk = getVaultBaseApk(ctx, pkg);
            if (vaultApk.exists()) {
                try {
                    BlackBoxCore.get().installPackageAsUser(vaultApk, userId);
                } catch (Throwable ignored) {}
                ClonedApp model = buildClonedAppModel(ctx, pm, pkg, userId);
                if (model != null) {
                    list.add(model);
                    added.add(pkg);
                }
            }
        }

        return list;
    }

    private static ClonedApp buildClonedAppModel(Context ctx, PackageManager pm, String pkg, int userId) {
        try {
            ClonedApp m = new ClonedApp();
            m.packageName = pkg;
            m.userId = userId;
            m.spaceId = userId;

            String baseName = pkg;
            Drawable icon = ICON_CACHE.get(pkg);
            boolean loadedFromHost = false;

            try {
                ApplicationInfo hostAi = pm.getApplicationInfo(pkg, 0);
                CharSequence label = hostAi.loadLabel(pm);
                if (label != null) baseName = label.toString();
                if (icon == null) {
                    icon = hostAi.loadIcon(pm);
                    if (icon != null) ICON_CACHE.put(pkg, icon);
                }
                loadedFromHost = true;
            } catch (Throwable notOnHost) {
                loadedFromHost = false;
            }

            File vaultApk = getVaultBaseApk(ctx, pkg);
            m.isVaultBacked = vaultApk.exists();

            if (!loadedFromHost && vaultApk.exists()) {
                PackageInfo archiveInfo = pm.getPackageArchiveInfo(vaultApk.getAbsolutePath(), 0);
                if (archiveInfo != null && archiveInfo.applicationInfo != null) {
                    ApplicationInfo aInfo = archiveInfo.applicationInfo;
                    aInfo.sourceDir = vaultApk.getAbsolutePath();
                    aInfo.publicSourceDir = vaultApk.getAbsolutePath();
                    CharSequence label = aInfo.loadLabel(pm);
                    if (label != null) baseName = label.toString();
                    if (icon == null) {
                        icon = aInfo.loadIcon(pm);
                        if (icon != null) ICON_CACHE.put(pkg, icon);
                    }
                }
            }

            if (icon == null) {
                icon = ctx.getResources().getDrawable(android.R.drawable.sym_def_app_icon);
            }

            String customAlias = CloneMetadataStore.getCustomAlias(ctx, pkg, userId);
            m.name = (customAlias != null && !customAlias.isEmpty()) ? customAlias : baseName;
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
        } catch (Throwable t) {
            return null;
        }
    }

    public static boolean cloneAppToSpace(Context ctx, String pkg, int userId) {
        return clonePackage(ctx, pkg, userId);
    }

    public static boolean clonePackage(Context ctx, String pkg, int userId) {
        try {
            GmsSupportManager.ensureGmsForSpace(userId);
            backupPackageToVault(ctx, pkg);

            File vaultBase = getVaultBaseApk(ctx, pkg);
            InstallResult res;
            if (vaultBase.exists()) {
                res = BlackBoxCore.get().installPackageAsUser(vaultBase, userId);
            } else {
                res = BlackBoxCore.get().installPackageAsUser(pkg, userId);
            }
            syncVaultLibsToBlackBoxAppDir(ctx, pkg);
            CloneMetadataStore.registerVaultedClone(ctx, pkg, userId);
            return res != null && res.success;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public static boolean installExternalApkFileToSpace(Context ctx, File apkFile, int userId) {
        return installApkFileToVaultOnly(ctx, apkFile, userId);
    }

    public static boolean installApkFileToVaultOnly(Context ctx, File apkFile, int userId) {
        if (apkFile == null || !apkFile.exists()) return false;
        try {
            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(apkFile.getAbsolutePath(), 0);
            String pkg = (pi != null && pi.packageName != null) ? pi.packageName : ("vault.app." + System.currentTimeMillis());

            File vaultDir = getApkVaultDir(ctx, pkg);
            File dstBase = new File(vaultDir, "base.apk");
            copyFile(apkFile, dstBase);
            extractNativeLibsFromApk(dstBase, new File(vaultDir, "lib"));

            GmsSupportManager.ensureGmsForSpace(userId);
            InstallResult res = BlackBoxCore.get().installPackageAsUser(dstBase, userId);
            syncVaultLibsToBlackBoxAppDir(ctx, pkg);
            CloneMetadataStore.registerVaultedClone(ctx, pkg, userId);
            return res != null && res.success;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public static boolean launchClone(Context ctx, String pkg, int userId) {
        try {
            GmsSupportManager.ensureGmsForSpace(userId);
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, userId);
            syncVaultLibsToBlackBoxAppDir(ctx, pkg);

            File vaultBase = getVaultBaseApk(ctx, pkg);
            if (!BlackBoxCore.get().isInstalled(pkg, userId) && vaultBase.exists()) {
                BlackBoxCore.get().installPackageAsUser(vaultBase, userId);
            }

            Intent explicitMain = resolveRealMainLauncherIntent(ctx, pkg);
            if (explicitMain != null) {
                try {
                    for (Method m : BlackBoxCore.get().getClass().getMethods()) {
                        if (m.getName().equals("startActivity") && m.getParameterTypes().length == 2) {
                            m.invoke(BlackBoxCore.get(), explicitMain, userId);
                            return true;
                        }
                    }
                } catch (Throwable ignored) {}
            }

            return BlackBoxCore.get().launchApk(pkg, userId);
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    private static Intent resolveRealMainLauncherIntent(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            if (pkg.contains("chrome")) {
                Intent chromeIntent = new Intent(Intent.ACTION_MAIN);
                chromeIntent.addCategory(Intent.CATEGORY_LAUNCHER);
                chromeIntent.setPackage(pkg);
                chromeIntent.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
                chromeIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                return chromeIntent;
            }

            Intent query = new Intent(Intent.ACTION_MAIN, null);
            query.addCategory(Intent.CATEGORY_LAUNCHER);
            query.setPackage(pkg);
            List<ResolveInfo> list = pm.queryIntentActivities(query, 0);
            if (list != null && !list.isEmpty()) {
                ActivityInfo chosen = null;
                for (ResolveInfo ri : list) {
                    if (ri.activityInfo == null || ri.activityInfo.name == null) continue;
                    String actName = ri.activityInfo.name.toLowerCase(Locale.US);
                    if (actName.contains("devui") || actName.contains("devtools") || actName.contains(" leak") || actName.contains("crash")) {
                        continue;
                    }
                    chosen = ri.activityInfo;
                    break;
                }
                if (chosen == null) chosen = list.get(0).activityInfo;
                if (chosen != null) {
                    Intent launch = new Intent(Intent.ACTION_MAIN);
                    launch.addCategory(Intent.CATEGORY_LAUNCHER);
                    launch.setComponent(new ComponentName(pkg, chosen.name));
                    launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                    return launch;
                }
            }
        } catch (Throwable ignored) {}
        return null;
    }

    public static void uninstallClone(Context ctx, String pkg, int userId) {
        try {
            BlackBoxCore.get().uninstallPackageAsUser(pkg, userId);
        } catch (Throwable ignored) {}
        CloneMetadataStore.unregisterVaultedClone(ctx, pkg, userId);
        CloneMetadataStore.clearCustomDeviceIdentity(ctx, pkg, userId);
        CloneMetadataStore.clearCustomLocation(ctx, pkg, userId);
        CloneMetadataStore.setCustomAlias(ctx, pkg, userId, "");
    }

    private static Drawable loadCachedIcon(PackageManager pm, ApplicationInfo ai, String pkg) {
        Drawable d = ICON_CACHE.get(pkg);
        if (d == null) {
            d = ai.loadIcon(pm);
            if (d != null) ICON_CACHE.put(pkg, d);
        }
        return d;
    }

    public static void clearMemoryCaches() {
        ICON_CACHE.evictAll();
        System.gc();
    }
}
""",
    )

    # 11. SecurityManager.java (Supports both String priorities AND int LOCK_* constants)
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
    private static final String KEY_PIN_HASH = "pin_hash_v3";
    private static final String KEY_PATTERN_HASH = "pattern_hash_v3";
    private static final String KEY_PRIMARY_PRIORITY = "primary_priority_v3";

    public static final String PRIORITY_PIN = "PIN";
    public static final String PRIORITY_PATTERN = "PATTERN";

    public static final int LOCK_NONE = 0;
    public static final int LOCK_PIN = 1;
    public static final int LOCK_PATTERN = 2;

    private static boolean sSessionUnlocked = false;

    private static SharedPreferences sp(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public static boolean isSessionUnlocked() {
        return sSessionUnlocked;
    }

    public static void setSessionUnlocked(boolean unlocked) {
        sSessionUnlocked = unlocked;
    }

    public static boolean isPinConfigured(Context ctx) {
        String h = sp(ctx).getString(KEY_PIN_HASH, "");
        return h != null && !h.isEmpty();
    }

    public static boolean isPatternConfigured(Context ctx) {
        String h = sp(ctx).getString(KEY_PATTERN_HASH, "");
        return h != null && !h.isEmpty();
    }

    public static boolean isLockEnabled(Context ctx) {
        return isPinConfigured(ctx) || isPatternConfigured(ctx);
    }

    public static boolean hasBothLocksConfigured(Context ctx) {
        return isPinConfigured(ctx) && isPatternConfigured(ctx);
    }

    public static void savePin(Context ctx, String rawPin) {
        if (rawPin == null || rawPin.trim().isEmpty()) return;
        sp(ctx).edit().putString(KEY_PIN_HASH, sha256(rawPin.trim())).apply();
    }

    public static void savePattern(Context ctx, String rawPattern) {
        if (rawPattern == null || rawPattern.trim().isEmpty()) return;
        sp(ctx).edit().putString(KEY_PATTERN_HASH, sha256(rawPattern.trim())).apply();
    }

    public static void clearPin(Context ctx) {
        sp(ctx).edit().remove(KEY_PIN_HASH).apply();
    }

    public static void clearPattern(Context ctx) {
        sp(ctx).edit().remove(KEY_PATTERN_HASH).apply();
    }

    public static void clearAllLocks(Context ctx) {
        sp(ctx).edit().remove(KEY_PIN_HASH).remove(KEY_PATTERN_HASH).apply();
        sSessionUnlocked = true;
    }

    public static void setPrimaryPriority(Context ctx, String priority) {
        sp(ctx).edit().putString(KEY_PRIMARY_PRIORITY, priority).apply();
    }

    public static String getPrimaryPriority(Context ctx) {
        return sp(ctx).getString(KEY_PRIMARY_PRIORITY, PRIORITY_PIN);
    }

    public static String getEffectivePrimaryLockMode(Context ctx) {
        String pref = getPrimaryPriority(ctx);
        if (PRIORITY_PATTERN.equals(pref) && isPatternConfigured(ctx)) {
            return PRIORITY_PATTERN;
        }
        if (PRIORITY_PIN.equals(pref) && isPinConfigured(ctx)) {
            return PRIORITY_PIN;
        }
        if (isPinConfigured(ctx)) return PRIORITY_PIN;
        if (isPatternConfigured(ctx)) return PRIORITY_PATTERN;
        return PRIORITY_PIN;
    }

    public static int getPrimaryLockType(Context ctx) {
        if (!isLockEnabled(ctx)) return LOCK_NONE;
        String mode = getEffectivePrimaryLockMode(ctx);
        return PRIORITY_PATTERN.equals(mode) ? LOCK_PATTERN : LOCK_PIN;
    }

    public static boolean verifyPin(Context ctx, String candidate) {
        if (candidate == null) return false;
        String saved = sp(ctx).getString(KEY_PIN_HASH, "");
        return !saved.isEmpty() && saved.equals(sha256(candidate.trim()));
    }

    public static boolean verifyPattern(Context ctx, String candidate) {
        if (candidate == null) return false;
        String saved = sp(ctx).getString(KEY_PATTERN_HASH, "");
        return !saved.isEmpty() && saved.equals(sha256(candidate.trim()));
    }

    public static boolean isAntiUninstallActive(Context ctx) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
            return dpm != null && dpm.isAdminActive(cn);
        } catch (Throwable t) {
            return false;
        }
    }

    public static void requestEnableAntiUninstall(Activity activity, int reqCode) {
        try {
            ComponentName cn = new ComponentName(activity, VaultDeviceAdminReceiver.class);
            Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
            intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, cn);
            intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                "حفاظت امنیتی پیشرفته در برابر حذف غیرمجاز / Anti-Uninstall Protection");
            activity.startActivityForResult(intent, reqCode);
        } catch (Throwable ignored) {}
    }

    public static void disableAntiUninstall(Context ctx) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
            if (dpm != null && dpm.isAdminActive(cn)) {
                dpm.removeActiveAdmin(cn);
            }
        } catch (Throwable ignored) {}
    }

    private static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(input.getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            return input;
        }
    }
}
""",
    )

    # 12. VaultDeviceAdminReceiver.java
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
            Intent lockIntent = new Intent(context, SecurityLockActivity.class);
            lockIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            lockIntent.putExtra("anti_uninstall_block", true);
            context.startActivity(lockIntent);
        } catch (Throwable ignored) {}

        boolean fa = LocaleHelper.isPersian(context);
        String msg = fa
            ? "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است."
            : "⛔ Uninstall is not permitted! Removal or deactivation of this app is blocked.";
        Toast.makeText(context, msg, Toast.LENGTH_LONG).show();
        return msg;
    }
}
""",
    )

    # 13. Auto-patch upgrade_v3_part2.py so MainActivity & SecurityLockActivity are 100% synchronized
    part2_path = os.path.join(ROOT, "scripts", "upgrade_v3_part2.py")
    if os.path.exists(part2_path):
        with open(part2_path, "r", encoding="utf-8") as f:
            p2 = f.read()
        p2 = p2.replace("Gravity.CENTER_horizontal", "Gravity.CENTER_HORIZONTAL")

        marker = "# [AUTO-SYNC-SECURITY-LOCK-V3]"
        if marker not in p2:
            sync_block = '''

# [AUTO-SYNC-SECURITY-LOCK-V3]
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
        boolean antiUninstallBlock = getIntent() != null && getIntent().getBooleanExtra(EXTRA_ANTI_UNINSTALL_BLOCK, false);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.parseColor("#090D16"));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        int pad = dp(24);
        root.setPadding(pad, pad, pad, pad);

        if (antiUninstallBlock) {
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

        TextView iconTv = new TextView(this);
        iconTv.setText("🔒");
        iconTv.setTextSize(36f);
        iconTv.setGravity(Gravity.CENTER);
        lockCard.addView(iconTv);

        TextView title = new TextView(this);
        title.setText(fa ? "ورود امنیتی VeyraVault" : "VeyraVault Security Lock");
        title.setTextColor(Color.WHITE);
        title.setTextSize(19f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(8), 0, dp(6));
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
                } else if (SecurityManager. isPinConfigured(SecurityLockActivity.this)) {
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
            TextView sub = new TextView(this);
            sub.setText(fa ? "الگوی امنیتی خود را رسم کنید" : "Draw your security pattern");
            sub.setTextColor(Color.parseColor("#94A3B8"));
            sub.setGravity(Gravity.CENTER);
            sub.setPadding(0, 0, 0, dp(10));
            modeContainer.addView(sub);

            patternView = new PatternLockView(this);
            LinearLayout.LayoutParams plp = new LinearLayout.LayoutParams(dp(250), dp(250));
            plp.gravity = Gravity.CENTER_HORIZONTAL;
            patternView.setOnPatternListener(new PatternLockView.OnPatternListener() {
                @Override
                public void onPatternDetected(String patternValue) {
                    if (SecurityManager.verifyPattern(SecurityLockActivity.this, patternValue)) {
                        onUnlockSuccess();
                    } else {
                        patternView.clearPattern();
                        onUnlockFailed();
                    }
                }
            });
            modeContainer.addView(patternView, plp);
        } else {
            TextView sub = new TextView(this);
            sub.setText(fa ? "رمز پین (PIN) خود را وارد کنید" : "Enter your security PIN");
            sub.setTextColor(Color.parseColor("#94A3B8"));
            sub.setGravity(Gravity.CENTER);
            sub.setPadding(0, 0, 0, dp(10));
            modeContainer.addView(sub);

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
                    String candidate = pinInput.getText().toString().trim();
                    if (SecurityManager.verifyPin(SecurityLockActivity.this, candidate)) {
                        onUnlockSuccess();
                    } else {
                        pinInput.setText("");
                        onUnlockFailed();
                    }
                }
            });
            modeContainer.addView(unlockBtn, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        }

        updateFallbackPrompt();
    }

    private void onUnlockSuccess() {
        SecurityManager.setSessionUnlocked(true);
        finish();
    }

    private void onUnlockFailed() {
        failedAttempts++;
        boolean fa = isPersian();
        Toast.makeText(this,
            fa ? "اطلاعات وارد شده اشتباه است!" : "Incorrect credentials!",
            Toast.LENGTH_SHORT).show();
        updateFallbackPrompt();
    }

    private void updateFallbackPrompt() {
        boolean fa = isPersian();
        if (SecurityManager.hasBothLocksConfigured(this) && failedAttempts >= 2) {
            fallbackSwitchBtn.setVisibility(View.VISIBLE);
            if (SecurityManager.PRIORITY_PIN.equals(currentMode)) {
                fallbackSwitchBtn.setText(fa
                    ? "آیا از الگو استفاده می‌کنید؟ ورود با الگو ⬅"
                    : "Using Pattern instead? Switch to Pattern ⬅");
            } else {
                fallbackSwitchBtn.setText(fa
                    ? "آیا از رمز پین استفاده می‌کنید؟ ورود با پین ⬅"
                    : "Using PIN instead? Switch to PIN ⬅");
            }
        } else if (SecurityManager.hasBothLocksConfigured(this)) {
            fallbackSwitchBtn.setVisibility(View.VISIBLE);
            if (SecurityManager.PRIORITY_PIN.equals(currentMode)) {
                fallbackSwitchBtn.setText(fa ? "تغییر به قفل الگو" : "Switch to Pattern Lock");
            } else {
                fallbackSwitchBtn.setText(fa ? "تغییر به رمز پین" : "Switch to PIN Lock");
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
            p2 = p2 + sync_block
        with open(part2_path, "w", encoding="utf-8") as f:
            f.write(p2)
        print("[v3-part1] Patched upgrade_v3_part2.py (MainActivity & SecurityLockActivity synchronized)")


if __name__ == "__main__":
    print("=== Running VeyraVault v3.0 Upgrade Part 1 (Final Synchronized Edition) ===")
    clean_legacy_sources()
    patch_app_build_gradle()
    generate_resources()
    generate_java_core()
    print("=== Part 1 Completed Successfully ===")
