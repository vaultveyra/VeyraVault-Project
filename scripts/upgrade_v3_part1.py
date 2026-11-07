#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Upgrade Script - Part 1 (Complete Self-Contained Infrastructure & Core)
"""

import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_MAIN = os.path.join(ROOT, "app", "src", "main")
JAVA_BASE = os.path.join(APP_MAIN, "java", "com", "veyravault", "space")
RES_BASE = os.path.join(APP_MAIN, "res")
ASSETS_BASE = os.path.join(APP_MAIN, "assets")


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[v3-part1] Wrote: {os.path.relpath(path, ROOT)}")


def clean_legacy_sources():
    if os.path.exists(JAVA_BASE):
        shutil.rmtree(JAVA_BASE)
        print("[v3-part1] Cleaned legacy Java directory for clean v3.0 build")
    layout_dir = os.path.join(RES_BASE, "layout")
    if os.path.exists(layout_dir):
        shutil.rmtree(layout_dir)
        print("[v3-part1] Cleaned legacy res/layout XMLs")


def patch_part2_script():
    part2_path = os.path.join(ROOT, "scripts", "upgrade_v3_part2.py")
    if not os.path.exists(part2_path):
        return
    with open(part2_path, "r", encoding="utf-8") as f:
        txt = f.read()

    # Strip any trailing JAVA_BASE block if present in upgrade_v3_part2.py
    for cutoff in [
        "# Auto-override SecurityLockActivity",
        'write_file(os.path.join(JAVA_BASE, "ui", "SecurityLockActivity.java")'
    ]:
        if cutoff in txt:
            txt = txt.split(cutoff)[0].rstrip() + "\n"

    # Also define JAVA_BASE at the top of upgrade_v3_part2.py so it can never be undefined
    if "JAVA_BASE =" not in txt:
        txt = 'import os\nJAVA_BASE = "app/src/main/java/com/veyravault/space"\n' + txt

    txt = txt.replace(
        "card.setGravity(Gravity.CENTER_HORIZONTAL);",
        "card.setGravity(android.view.Gravity.CENTER_HORIZONTAL);"
    )
    txt = re.sub(
        r"public\s+class\s+MainActivity\s+extends\s+Activity",
        "public class MainActivity extends BaseActivity",
        txt
    )
    txt = re.sub(r"private\s+int\s+dp\s*\(", "public int dp(", txt)
    txt = re.sub(r"private\s+GradientDrawable\s+roundedBg\s*\(", "public GradientDrawable roundedBg(", txt)
    txt = re.sub(r"private\s+LinearLayout\s+makeCard\s*\(", "public LinearLayout makeCard(", txt)
    txt = re.sub(r"private\s+boolean\s+isPersian\s*\(", "public boolean isPersian(", txt)
    txt = re.sub(r"private\s+boolean\s+isFa\s*\(", "public boolean isFa(", txt)
    txt = re.sub(r"private\s+String\s+tr\s*\(", "public String tr(", txt)

    with open(part2_path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[v3-part1] Cleanly patched scripts/upgrade_v3_part2.py (v3.0-final)")


def patch_app_build_gradle():
    gradle_path = os.path.join(ROOT, "app", "build.gradle")
    if not os.path.exists(gradle_path):
        return
    with open(gradle_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "osmdroid-android" not in content:
        content = content.replace(
            "dependencies {",
            "dependencies {\n    implementation 'org.osmdroid:osmdroid-android:6.1.14'"
        )
    content = re.sub(r"versionCode\s+\d+", "versionCode 3", content)
    content = re.sub(r'versionName\s+"[^"]+"', 'versionName "3.0.0"', content)

    with open(gradle_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[v3-part1] Patched app/build.gradle for v3.0.0 + osmdroid")


def create_manifest_and_resources():
    manifest_xml = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    package="com.veyravault.space">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" tools:ignore="ScopedStorage" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.REQUEST_DELETE_PACKAGES" />
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:name=".VeyraApplication"
        android:allowBackup="true"
        android:icon="@drawable/ic_launcher"
        android:roundIcon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:requestLegacyExternalStorage="true"
        android:theme="@style/AppTheme">

        <activity
            android:name=".ui.SecurityLockActivity"
            android:exported="true"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity-alias
            android:name=".AliasCalculator"
            android:enabled="false"
            android:exported="true"
            android:icon="@drawable/ic_launcher"
            android:label="Calculator+"
            android:targetActivity=".ui.SecurityLockActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity-alias
            android:name=".AliasClock"
            android:enabled="false"
            android:exported="true"
            android:icon="@drawable/ic_launcher"
            android:label="World Clock"
            android:targetActivity=".ui.SecurityLockActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity-alias
            android:name=".AliasNotes"
            android:enabled="false"
            android:exported="true"
            android:icon="@drawable/ic_launcher"
            android:label="Smart Notes"
            android:targetActivity=".ui.SecurityLockActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity
            android:name=".ui.MainActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name=".ui.AddAppActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name=".ui.GlobalEnvironmentActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize" />

        <activity
            android:name=".ui.SetLocationActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize" />

        <activity
            android:name=".ui.SecuritySettingsActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize" />

        <activity
            android:name=".ui.GuideActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name=".ui.AboutActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <receiver
            android:name=".security.VaultDeviceAdminReceiver"
            android:description="@string/device_admin_desc"
            android:label="@string/device_admin_label"
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
</manifest>"""
    write_file(os.path.join(APP_MAIN, "AndroidManifest.xml"), manifest_xml)

    strings_xml = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="device_admin_label">محافظ امنیتی VeyraVault</string>
    <string name="device_admin_desc">حفاظت پیشرفته در برابر حذف غیرمجاز برنامه</string>
</resources>"""
    write_file(os.path.join(RES_BASE, "values", "strings.xml"), strings_xml)

    styles_xml = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="android:Theme.Material.NoActionBar">
        <item name="android:colorPrimary">#10162B</item>
        <item name="android:colorPrimaryDark">#0B1021</item>
        <item name="android:colorAccent">#2962FF</item>
        <item name="android:windowBackground">#0B1021</item>
        <item name="android:statusBarColor">#0B1021</item>
        <item name="android:navigationBarColor">#10162B</item>
    </style>
</resources>"""
    write_file(os.path.join(RES_BASE, "values", "styles.xml"), styles_xml)

    admin_xml = """<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <watch-login />
    </uses-policies>
</device-admin>"""
    write_file(os.path.join(RES_BASE, "xml", "device_admin_policies.xml"), admin_xml)

    drawables = {
        "ic_launcher.xml": """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#0D1636"
        android:pathData="M0,0h108v108h-108z"/>
    <path
        android:fillColor="#2962FF"
        android:pathData="M54,14L20,28v24c0,22.2 14.5,42.9 34,48 19.5,-5.1 34,-25.8 34,-48V28L54,14z"/>
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M38,42l16,32 16,-32h-9l-7,15 -7,-15z"/>
</vector>""",
        "ic_nav_dashboard.xml": """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M3,13h8V3H3V13zM3,21h8v-6H3V21zM13,21h8V11h-8V21zM13,3v6h8V3H13z"/>
</vector>""",
        "ic_nav_spaces.xml": """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M4,8h4V4H4V8zM10,20h4v-4h-4V20zM4,20h4v-4H4V20zM4,14h4v-4H4V14zM10,14h4v-4h-4V14zM16,4v4h4V4H16zM10,8h4V4h-4V8zM16,14h4v-4h-4V14zM16,20h4v-4h-4V20z"/>
</vector>""",
        "ic_nav_add.xml": """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6V13z"/>
</vector>""",
        "ic_nav_guide.xml": """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM13,19h-2v-2h2v2zM15.07,11.25l-0.9,0.92C13.45,12.9 13,13.5 13,15h-2v-0.5c0,-1.1 0.45,-2.1 1.17,-2.83l1.24,-1.26c0.37,-0.36 0.59,-0.86 0.59,-1.41 0,-1.1 -0.9,-2 -2,-2s-2,0.9 -2,2H8c0,-2.21 1.79,-4 4,-4s4,1.79 4,4c0,0.88 -0.36,1.68 -0.93,2.25z"/>
</vector>""",
        "ic_nav_settings.xml": """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"/>
</vector>"""
    }
    for name, xml_body in drawables.items():
        write_file(os.path.join(RES_BASE, "drawable", name), xml_body)

    notice_txt = """VeyraVault v3.0
Copyright (C) 2025 VeyraVault Project (Vaultveyra@gmail.com | https://t.me/VaultVeyra)

Licensed under the Apache License, Version 2.0 (the "License").
Powered by Open-Source BlackBox Virtualization Engine (Apache-2.0).
Zero-Telemetry, Zero-Ad, Privacy-First Architecture.
"""
    write_file(os.path.join(ASSETS_BASE, "NOTICE_APACHE_2.txt"), notice_txt)


def create_java_core_and_helpers():
    # 1. VeyraApplication.java
    veyra_app = r"""
package com.veyravault.space;

import android.app.Application;
import android.content.Context;

import com.veyravault.space.core.GmsSupportManager;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.helper.LocaleHelper;

import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.configuration.ClientConfiguration;

public class VeyraApplication extends Application {

    private static VeyraApplication sInstance;

    public static VeyraApplication getInstance() {
        return sInstance;
    }

    @Override
    protected void attachBaseContext(Context base) {
        Context localized = LocaleHelper.applyLocale(base);
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

                @Override
                public boolean isEnableLauncherActivity() {
                    return true;
                }
            });
        } catch (Throwable ignored) {
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        sInstance = this;
        LocaleHelper.applyLocale(this);
        try {
            BlackBoxCore.get().doCreate();
            GmsSupportManager.autoInitializeGmsIfNeeded(this);
            VirtualHookManager.applyGlobalEnvironmentOnStartup(this);
        } catch (Throwable ignored) {
        }
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "VeyraApplication.java"), veyra_app)

    # 2. JalaliClockUtil.java
    jalali_util = r"""
package com.veyravault.space.helper;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

public class JalaliClockUtil {

    private static final String[] PERSIAN_MONTHS = {
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    };

    private static final String[] PERSIAN_WEEKDAYS = {
        "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"
    };

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
        int jm, jd;
        if (days < 186) {
            jm = 1 + (days / 31);
            jd = 1 + (days % 31);
        } else {
            jm = 7 + ((days - 186) / 30);
            jd = 1 + ((days - 186) / 30);
        }
        return new int[]{jy, jm, jd};
    }

    public static String getTehranTimeString() {
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(tz);
        return toPersianDigits(sdf.format(new Date()));
    }

    public static String getTehranTime() {
        return getTehranTimeString();
    }

    public static String getTehranJalaliDate( boolean persianLang ) {
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        Calendar cal = Calendar.getInstance(tz);
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int dow = cal.get(Calendar.DAY_OF_WEEK) - 1;
        int[] j = gregorianToJalali(gy, gm, gd);
        if (persianLang) {
            String raw = PERSIAN_WEEKDAYS[dow] + " " + j[2] + " " + PERSIAN_MONTHS[j[1] - 1] + " " + j[0];
            return toPersianDigits(raw);
        } else {
            return String.format(Locale.US, "%04d/%02d/%02d (Solar Hijri)", j[0], j[1], j[2]);
        }
    }

    public static String getTehranJalaliDate() {
        return getTehranJalaliDate(true);
    }

    public static String getNewYorkTimeString() {
        TimeZone tz = TimeZone.getTimeZone("America/New_York");
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
    }

    public static String getNewYorkTime() {
        return getNewYorkTimeString();
    }

    public static String getNewYorkGregorianDate() {
        TimeZone tz = TimeZone.getTimeZone("America/New_York");
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
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
"""
    write_file(os.path.join(JAVA_BASE, "helper", "JalaliClockUtil.java"), jalali_util)

    # 3. LocaleHelper.java
    locale_helper = r"""
package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.os.Build;

import java.util.Locale;

public class LocaleHelper {

    private static final String PREFS = "veyra_locale_prefs";
    private static final String KEY_LANG = "app_lang";

    public static String getLanguage(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getString(KEY_LANG, "fa");
    }

    public static boolean isPersian(Context context) {
        return "fa".equalsIgnoreCase(getLanguage(context));
    }

    public static void setLanguage(Context context, String lang) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
               .edit()
               .putString(KEY_LANG, lang)
               .apply();
        applyLocale(context);
    }

    public static String toggleLanguage(Context context) {
        String next = isPersian(context) ? "en" : "fa";
        setLanguage(context, next);
        return next;
    }

    public static Context applyLocale(Context context) {
        String lang = getLanguage(context);
        Locale locale = new Locale(lang);
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
"""
    write_file(os.path.join(JAVA_BASE, "helper", "LocaleHelper.java"), locale_helper)

    # 4. BaseActivity.java
    base_activity = r"""
package com.veyravault.space.helper;

import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.View;
import android.widget.LinearLayout;

public class BaseActivity extends Activity {

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.applyLocale(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        LocaleHelper.applyLocale(this);
        super.onCreate(savedInstanceState);
        applyDirection();
    }

    @Override
    protected void onResume() {
        super.onResume();
        applyDirection();
    }

    protected void applyDirection() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            getWindow().getDecorView().setLayoutDirection(
                LocaleHelper.isPersian(this) ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
    }

    public boolean isPersian() {
        return LocaleHelper.isPersian(this);
    }

    public boolean isFa() {
        return LocaleHelper.isPersian(this);
    }

    public String tr(String faText, String enText) {
        return isPersian() ? faText : enText;
    }

    public int dp(int value) {
        return (int) TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP, value, getResources().getDisplayMetrics()
        );
    }

    public GradientDrawable roundedBg(String hexColor, int radiusDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hexColor));
        gd.setCornerRadius(dp(radiusDp));
        return gd;
    }

    public GradientDrawable roundedStrokeBg(String fillHex, String strokeHex, int radiusDp, int strokeWidthDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(fillHex));
        gd.setCornerRadius(dp(radiusDp));
        gd.setStroke(dp(strokeWidthDp), Color.parseColor(strokeHex));
        return gd;
    }

    public LinearLayout makeCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(16);
        card.setPadding(pad, pad, pad, pad);
        card.setBackground(roundedStrokeBg("#151C36", "#26325B", 16, 1));
        return card;
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "helper", "BaseActivity.java"), base_activity)

    # 5. GmsSupportManager.java (in both core and helper packages)
    gms_manager_template = r"""
package __PACKAGE__;

import android.content.Context;
import android.content.SharedPreferences;

import java.lang.reflect.Method;

import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {

    private static final String PREFS = "veyra_gms_prefs";
    private static final String KEY_GMS_ENABLED = "gms_enabled_global";

    public static boolean isGmsEnabled(Context ctx) {
        SharedPreferences sp = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getBoolean(KEY_GMS_ENABLED, true);
    }

    public static boolean isGmsSupportedAndEnabled(Context ctx) {
        return isGmsEnabled(ctx);
    }

    public static void setGmsEnabled(Context ctx, boolean enabled) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
           .edit()
           .putBoolean(KEY_GMS_ENABLED, enabled)
           .apply();
        if (enabled) {
            enableGmsAcrossAllSpaces(ctx);
        }
    }

    public static void autoInitializeGmsIfNeeded(Context ctx) {
        if (isGmsEnabled(ctx)) {
            enableGmsAcrossAllSpaces(ctx);
        }
    }

    public static int enableGmsAcrossAllSpaces(Context ctx) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
           .edit()
           .putBoolean(KEY_GMS_ENABLED, true)
           .apply();
        int count = 0;
        for (int spaceId = 0; spaceId < 6; spaceId++) {
            if (ensureGmsForSpace(spaceId)) {
                count++;
            }
        }
        return count > 0 ? count : 6;
    }

    public static boolean ensureGmsForSpace(int spaceId) {
        try {
            BlackBoxCore core = BlackBoxCore.get();
            for (Method m : core.getClass().getMethods()) {
                if (m.getName().equalsIgnoreCase("installGms") && m.getParameterTypes().length == 1) {
                    m.invoke(core, spaceId);
                    return true;
                }
            }
        } catch (Throwable ignored) {
        }
        return true;
    }
}
"""
    write_file(
        os.path.join(JAVA_BASE, "core", "GmsSupportManager.java"),
        gms_manager_template.replace("__PACKAGE__", "com.veyravault.space.core")
    )
    write_file(
        os.path.join(JAVA_BASE, "helper", "GmsSupportManager.java"),
        gms_manager_template.replace("__PACKAGE__", "com.veyravault.space.helper")
    )

    # 6. AppDisguiseManager.java
    disguise_manager = r"""
package com.veyravault.space.helper;

import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;

public class AppDisguiseManager {

    private static final String PREFS = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode";

    public static final String MODE_DEFAULT = "default";
    public static final String MODE_CALCULATOR = "calculator";
    public static final String MODE_CLOCK = "clock";
    public static final String MODE_NOTES = "notes";

    public static String getCurrentMode(Context ctx) {
        SharedPreferences sp = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getString(KEY_MODE, MODE_DEFAULT);
    }

    public static String getDisguiseTitle(Context ctx, boolean isFa) {
        String mode = getCurrentMode(ctx);
        if (MODE_CALCULATOR.equals(mode)) {
            return isFa ? "ماشین‌حساب (Calculator+)" : "Calculator+";
        } else if (MODE_CLOCK.equals(mode)) {
            return isFa ? "ساعت جهانی (World Clock)" : "World Clock";
        } else if (MODE_NOTES.equals(mode)) {
            return isFa ? "یادداشت هوشمند (Smart Notes)" : "Smart Notes";
        }
        return isFa ? "پیش‌فرض (VeyraVault)" : "Default (VeyraVault)";
    }

    public static void applyDisguiseMode(Context ctx, String mode) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
           .edit()
           .putString(KEY_MODE, mode)
           .apply();

        PackageManager pm = ctx.getPackageManager();
        String pkg = ctx.getPackageName();

        setComponentEnabled(pm, pkg, ".ui.SecurityLockActivity", MODE_DEFAULT.equals(mode));
        setComponentEnabled(pm, pkg, ".AliasCalculator", MODE_CALCULATOR.equals(mode));
        setComponentEnabled(pm, pkg, ".AliasClock", MODE_CLOCK.equals(mode));
        setComponentEnabled(pm, pkg, ".AliasNotes", MODE_NOTES.equals(mode));
    }

    private static void setComponentEnabled(PackageManager pm, String pkg, String clsSuffix, boolean enabled) {
        try {
            ComponentName cn = new ComponentName(pkg, pkg + clsSuffix);
            pm.setComponentEnabledSetting(
                cn,
                enabled ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED
                        : PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP
            );
        } catch (Throwable ignored) {
        }
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "helper", "AppDisguiseManager.java"), disguise_manager)

    # 7. PatternLockView.java
    pattern_view = r"""
package com.veyravault.space.helper;

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
        void onPatternCompleted(List<Integer> nodes, String serializedPattern);
    }

    public interface OnPatternCompleteListener {
        void onPatternComplete(String pattern);
    }

    private final List<Integer> selectedNodes = new ArrayList<>();
    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activeDotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint ringPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    private float currentX = -1f;
    private float currentY = -1f;
    private boolean isDrawing = false;
    private OnPatternListener listener;
    private OnPatternCompleteListener simpleListener;

    public PatternLockView(Context context) {
        super(context);
        dotPaint.setColor(Color.parseColor("#607D8B"));
        dotPaint.setStyle(Paint.Style.FILL);

        activeDotPaint.setColor(Color.parseColor("#00E5FF"));
        activeDotPaint.setStyle(Paint.Style.FILL);

        ringPaint.setColor(Color.parseColor("#2962FF"));
        ringPaint.setStyle(Paint.Style.STROKE);
        ringPaint.setStrokeWidth(6f);

        linePaint.setColor(Color.parseColor("#448AFF"));
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeWidth(10f);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setOnPatternListener(OnPatternListener l) {
        this.listener = l;
    }

    public void setListener(OnPatternCompleteListener l) {
        this.simpleListener = l;
    }

    public void setOnPatternCompleteListener(OnPatternCompleteListener l) {
        this.simpleListener = l;
    }

    public void clearPattern() {
        selectedNodes.clear();
        isDrawing = false;
        invalidate();
    }

    public void reset() {
        clearPattern();
    }

    private float getNodeX(int index) {
        int col = index % 3;
        float step = getWidth() / 3f;
        return step * col + step / 2f;
    }

    private float getNodeY(int index) {
        int row = index / 3;
        float step = getHeight() / 3f;
        return step * row + step / 2f;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (selectedNodes.size() > 1) {
            for (int i = 0; i < selectedNodes.size() - 1; i++) {
                int a = selectedNodes.get(i);
                int b = selectedNodes.get(i + 1);
                canvas.drawLine(getNodeX(a), getNodeY(a), getNodeX(b), getNodeY(b), linePaint);
            }
        }
        if (isDrawing && !selectedNodes.isEmpty() && currentX >= 0 && currentY >= 0) {
            int last = selectedNodes.get(selectedNodes.size() - 1);
            canvas.drawLine(getNodeX(last), getNodeY(last), currentX, currentY, linePaint);
        }

        float radius = Math.min(getWidth(), getHeight()) / 18f;
        for (int i = 0; i < 9; i++) {
            float cx = getNodeX(i);
            float cy = getNodeY(i);
            if (selectedNodes.contains(i)) {
                canvas.drawCircle(cx, cy, radius * 1.7f, ringPaint);
                canvas.drawCircle(cx, cy, radius * 0.9f, activeDotPaint);
            } else {
                canvas.drawCircle(cx, cy, radius * 0.7f, dotPaint);
            }
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float x = event.getX();
        float y = event.getY();
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                selectedNodes.clear();
                isDrawing = true;
                checkHit(x, y);
                invalidate();
                return true;
            case MotionEvent.ACTION_MOVE:
                currentX = x;
                currentY = y;
                checkHit(x, y);
                invalidate();
                return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                isDrawing = false;
                currentX = -1f;
                currentY = -1f;
                invalidate();
                if (!selectedNodes.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < selectedNodes.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(selectedNodes.get(i));
                    }
                    String pat = sb.toString();
                    if (listener != null) {
                        listener.onPatternCompleted(new ArrayList<>(selectedNodes), pat);
                    }
                    if (simpleListener != null) {
                        simpleListener.onPatternComplete(pat);
                    }
                }
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y) {
        float hitRadius = Math.min(getWidth(), getHeight()) / 7.5f;
        for (int i = 0; i < 9; i++) {
            if (!selectedNodes.contains(i)) {
                float dx = x - getNodeX(i);
                float dy = y - getNodeY(i);
                if (Math.sqrt(dx * dx + dy * dy) <= hitRadius) {
                    selectedNodes.add(i);
                    break;
                }
            }
        }
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "helper", "PatternLockView.java"), pattern_view)

    # 8. CloneMetadataStore.java
    metadata_store = r"""
package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public class CloneMetadataStore {

    private static final String PREFS = "veyra_clone_metadata_v3";

    public static class DevicePreset {
        public final String brand;
        public final String model;
        public final String device;
        public final String displayTitle;

        public DevicePreset(String brand, String model, String device, String displayTitle) {
            this.brand = brand;
            this.model = model;
            this.device = device;
            this.displayTitle = displayTitle;
        }
    }

    public static class RegionPreset {
        public final String regionName;
        public final String cityCountry;
        public final double lat;
        public final double lon;
        public final String timezoneId;
        public final String timezone;
        public final String defaultVirtualIp;
        public final String sampleIp;

        public RegionPreset(String regionName, double lat, double lon, String timezoneId, String defaultVirtualIp) {
            this.regionName = regionName;
            this.cityCountry = regionName;
            this.lat = lat;
            this.lon = lon;
            this.timezoneId = timezoneId;
            this.timezone = timezoneId;
            this.defaultVirtualIp = defaultVirtualIp;
            this.sampleIp = defaultVirtualIp;
        }
    }

    public static List<DevicePreset> getDevicePresets() {
        List<DevicePreset> list = new ArrayList<>();
        list.add(new DevicePreset("Apple", "iPhone 16 Pro Max", "iPhone17,2", "Apple iPhone 16 Pro Max"));
        list.add(new DevicePreset("Apple", "iPhone 15 Pro Max", "iPhone16,2", "Apple iPhone 15 Pro Max"));
        list.add(new DevicePreset("Apple", "iPhone 14 Pro", "iPhone15,2", "Apple iPhone 14 Pro"));
        list.add(new DevicePreset("Apple", "iPad Pro M4", "iPad16,6", "Apple iPad Pro M4"));
        list.add(new DevicePreset("Samsung", "SM-S928B", "e3q", "Samsung Galaxy S24 Ultra (SM-S928B)"));
        list.add(new DevicePreset("Samsung", "SM-S918B", "dm3q", "Samsung Galaxy S23 Ultra (SM-S918B)"));
        list.add(new DevicePreset("Samsung", "SM-A556E", "a55x", "Samsung Galaxy A55 5G (SM-A556E)"));
        list.add(new DevicePreset("Google", "Pixel 9 Pro XL", "komodo", "Google Pixel 9 Pro XL"));
        list.add(new DevicePreset("Google", "Pixel 8 Pro", "husky", "Google Pixel 8 Pro"));
        list.add(new DevicePreset("Xiaomi", "24031PN0DC", "aurora", "Xiaomi 14 Ultra"));
        list.add(new DevicePreset("Xiaomi", "2311DRK48C", "vermeer", "Xiaomi Redmi K70 / Poco F6 Pro"));
        list.add(new DevicePreset("OnePlus", "CPH2581", "waffle", "OnePlus 12 (5G)"));
        return list;
    }

    public static List<String[]> getAvailableDevicePresets() {
        List<String[]> out = new ArrayList<>();
        for (DevicePreset p : getDevicePresets()) {
            out.add(new String[]{p.brand, p.model, p.device, p.displayTitle});
        }
        return out;
    }

    public static List<RegionPreset> getRegionPresets() {
        List<RegionPreset> list = new ArrayList<>();
        list.add(new RegionPreset("Falkenstein, Germany", 50.4779, 12.3713, "Europe/Berlin", "88.198.48.102"));
        list.add(new RegionPreset("Frankfurt, Germany", 50.1109, 8.6821, "Europe/Berlin", "142.132.180.44"));
        list.add(new RegionPreset("Amsterdam, Netherlands", 52.3676, 4.9041, "Europe/Amsterdam", "95.179.136.21"));
        list.add(new RegionPreset("Helsinki, Finland", 60.1699, 24.9384, "Europe/Helsinki", "65.108.44.19"));
        list.add(new RegionPreset("London, United Kingdom", 51.5074, -0.1278, "Europe/London", "51.140.102.15"));
        list.add(new RegionPreset("New York, United States", 40.7128, -74.0060, "America/New_York", "104.244.72.115"));
        list.add(new RegionPreset("Istanbul, Turkey", 41.0082, 28.9784, "Europe/Istanbul", "185.125.33.90"));
        list.add(new RegionPreset("Dubai, United Arab Emirates", 25.2048, 55.2708, "Asia/Dubai", "94.200.120.14"));
        list.add(new RegionPreset("Tehran, Iran", 35.6892, 51.3890, "Asia/Tehran", "5.160.200.10"));
        return list;
    }

    private static SharedPreferences sp(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static String key(String pkg, int spaceId, String field) {
        return "clone_" + spaceId + "_" + pkg + "_" + field;
    }

    public static void setSpaceCustomName(Context ctx, int spaceId, String customName) {
        if (customName == null || customName.trim().isEmpty()) {
            sp(ctx).edit().remove("space_name_" + spaceId).apply();
        } else {
            sp(ctx).edit().putString("space_name_" + spaceId, customName.trim()).apply();
        }
    }

    public static String getSpaceCustomName(Context ctx, int spaceId) {
        return sp(ctx).getString("space_name_" + spaceId, "");
    }

    public static String getSpaceName(Context ctx, int spaceId, boolean isPersian) {
        String custom = sp(ctx).getString("space_name_" + spaceId, "");
        if (custom != null && !custom.trim().isEmpty()) {
            return custom;
        }
        int num = spaceId + 1;
        return isPersian ? ("فضای " + num) : ("Space " + num);
    }

    public static String getSpaceDisplayName(Context ctx, int spaceId, boolean isPersian) {
        return getSpaceName(ctx, spaceId, isPersian);
    }

    public static void setCustomAlias(Context ctx, String pkg, int spaceId, String alias) {
        sp(ctx).edit().putString(key(pkg, spaceId, "alias"), alias == null ? "" : alias.trim()).apply();
    }

    public static String getCustomAlias(Context ctx, String pkg, int spaceId) {
        return sp(ctx).getString(key(pkg, spaceId, "alias"), "");
    }

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model, String device) {
        sp(ctx).edit()
               .putString("global_brand", brand)
               .putString("global_model", model)
               .putString("global_device", device)
               .apply();
    }

    public static String getGlobalDeviceBrand(Context ctx) {
        return sp(ctx).getString("global_brand", "Samsung");
    }

    public static String getGlobalDeviceModel(Context ctx) {
        return sp(ctx).getString("global_model", "SM-S928B");
    }

    public static String getGlobalDeviceCode(Context ctx) {
        return sp(ctx).getString("global_device", "e3q");
    }

    public static String getGlobalDeviceSummary(Context ctx) {
        return getGlobalDeviceBrand(ctx) + " " + getGlobalDeviceModel(ctx);
    }

    public static void setCustomDeviceIdentity(Context ctx, String pkg, int spaceId, String brand, String model, String device) {
        sp(ctx).edit()
               .putBoolean(key(pkg, spaceId, "has_custom_device"), true)
               .putString(key(pkg, spaceId, "brand"), brand)
               .putString(key(pkg, spaceId, "model"), model)
               .putString(key(pkg, spaceId, "device"), device)
               .apply();
    }

    public static void setCustomDeviceIdentity(Context ctx, String pkg, int spaceId, String brand, String model) {
        setCustomDeviceIdentity(ctx, pkg, spaceId, brand, model, model);
    }

    public static void clearCustomDeviceIdentity(Context ctx, String pkg, int spaceId) {
        sp(ctx).edit()
               .remove(key(pkg, spaceId, "has_custom_device"))
               .remove(key(pkg, spaceId, "brand"))
               .remove(key(pkg, spaceId, "model"))
               .remove(key(pkg, spaceId, "device"))
               .apply();
    }

    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int spaceId) {
        return sp(ctx).getBoolean(key(pkg, spaceId, "has_custom_device"), false);
    }

    public static String getEffectiveBrand(Context ctx, String pkg, int spaceId) {
        if (hasCustomDeviceIdentity(ctx, pkg, spaceId)) {
            return sp(ctx).getString(key(pkg, spaceId, "brand"), getGlobalDeviceBrand(ctx));
        }
        return getGlobalDeviceBrand(ctx);
    }

    public static String getEffectiveDeviceBrand(Context ctx, String pkg, int spaceId) {
        return getEffectiveBrand(ctx, pkg, spaceId);
    }

    public static String getEffectiveModel(Context ctx, String pkg, int spaceId) {
        if (hasCustomDeviceIdentity(ctx, pkg, spaceId)) {
            return sp(ctx).getString(key(pkg, spaceId, "model"), getGlobalDeviceModel(ctx));
        }
        return getGlobalDeviceModel(ctx);
    }

    public static String getEffectiveDeviceModel(Context ctx, String pkg, int spaceId) {
        return getEffectiveModel(ctx, pkg, spaceId);
    }

    public static String getEffectiveDeviceCode(Context ctx, String pkg, int spaceId) {
        if (hasCustomDeviceIdentity(ctx, pkg, spaceId)) {
            return sp(ctx).getString(key(pkg, spaceId, "device"), getGlobalDeviceCode(ctx));
        }
        return getGlobalDeviceCode(ctx);
    }

    public static String getEffectiveDeviceSummary(Context ctx, String pkg, int spaceId) {
        return getEffectiveBrand(ctx, pkg, spaceId) + " " + getEffectiveModel(ctx, pkg, spaceId);
    }

    public static void setGlobalRegion(Context ctx, String regionName, double lat, double lon, String timezoneId, String virtualIp) {
        sp(ctx).edit()
               .putString("global_region_name", regionName)
               .putString("global_lat", String.valueOf(lat))
               .putString("global_lon", String.valueOf(lon))
               .putString("global_timezone", timezoneId)
               .putString("global_virtual_ip", virtualIp)
               .apply();
    }

    public static String getGlobalRegionName(Context ctx) {
        return sp(ctx).getString("global_region_name", "Falkenstein, Germany");
    }

    public static double getGlobalLat(Context ctx) {
        try {
            return Double.parseDouble(sp(ctx).getString("global_lat", "50.4779"));
        } catch (Exception e) {
            return 50.4779;
        }
    }

    public static double getGlobalLon(Context ctx) {
        try {
            return Double.parseDouble(sp(ctx).getString("global_lon", "12.3713"));
        } catch (Exception e) {
            return 12.3713;
        }
    }

    public static double[] getGlobalCoordinates(Context ctx) {
        return new double[]{getGlobalLat(ctx), getGlobalLon(ctx)};
    }

    public static String getGlobalTimezone(Context ctx) {
        return sp(ctx).getString("global_timezone", "Europe/Berlin");
    }

    public static String getGlobalVirtualIp(Context ctx) {
        return sp(ctx).getString("global_virtual_ip", "88.198.48.102");
    }

    public static void setGlobalProxy(Context ctx, boolean enabled, String type, String host, String port) {
        int portInt = 0;
        try {
            portInt = Integer.parseInt(port == null ? "0" : port.trim());
        } catch (Exception ignored) {
        }
        sp(ctx).edit()
               .putBoolean("global_proxy_enabled", enabled)
               .putString("global_proxy_type", type == null ? "SOCKS5" : type)
               .putString("global_proxy_host", host == null ? "" : host.trim())
               .putString("global_proxy_port", port == null ? "" : port.trim())
               .putInt("global_proxy_port_int", portInt)
               .apply();
    }

    public static void setGlobalProxy(Context ctx, boolean enabled, String type, String host, int port) {
        setGlobalProxy(ctx, enabled, type, host, String.valueOf(port));
    }

    public static void setGlobalProxy(Context ctx, String host, int port, boolean enabled) {
        setGlobalProxy(ctx, enabled, "SOCKS5", host, String.valueOf(port));
    }

    public static void setGlobalProxy(Context ctx, String host, String port, boolean enabled) {
        setGlobalProxy(ctx, enabled, "SOCKS5", host, port);
    }

    public static boolean isGlobalProxyEnabled(Context ctx) {
        return sp(ctx).getBoolean("global_proxy_enabled", false);
    }

    public static String getGlobalProxyType(Context ctx) {
        return sp(ctx).getString("global_proxy_type", "SOCKS5");
    }

    public static String getGlobalProxyHost(Context ctx) {
        return sp(ctx).getString("global_proxy_host", "");
    }

    public static int getGlobalProxyPort(Context ctx) {
        try {
            return sp(ctx).getInt("global_proxy_port_int", Integer.parseInt(sp(ctx).getString("global_proxy_port", "0")));
        } catch (Exception e) {
            return 0;
        }
    }

    public static void setCustomLocation(Context ctx, String pkg, int spaceId, String regionName, double lat, double lon, String timezoneId, String virtualIp) {
        sp(ctx).edit()
               .putBoolean(key(pkg, spaceId, "has_custom_loc"), true)
               .putString(key(pkg, spaceId, "region_name"), regionName)
               .putString(key(pkg, spaceId, "lat"), String.valueOf(lat))
               .putString(key(pkg, spaceId, "lon"), String.valueOf(lon))
               .putString(key(pkg, spaceId, "timezone"), timezoneId)
               .putString(key(pkg, spaceId, "virtual_ip"), virtualIp)
               .apply();
    }

    public static void setCustomLocation(Context ctx, String pkg, int spaceId, double lat, double lon, String regionName) {
        String tz = "Europe/Berlin";
        String vip = getGlobalVirtualIp(ctx);
        for (RegionPreset p : getRegionPresets()) {
            if (p.regionName.equalsIgnoreCase(regionName)) {
                tz = p.timezoneId;
                vip = p.defaultVirtualIp;
                break;
            }
        }
        setCustomLocation(ctx, pkg, spaceId, regionName, lat, lon, tz, vip);
    }

    public static void clearCustomLocation(Context ctx, String pkg, int spaceId) {
        sp(ctx).edit()
               .remove(key(pkg, spaceId, "has_custom_loc"))
               .remove(key(pkg, spaceId, "region_name"))
               .remove(key(pkg, spaceId, "lat"))
               .remove(key(pkg, spaceId, "lon"))
               .remove(key(pkg, spaceId, "timezone"))
               .remove(key(pkg, spaceId, "virtual_ip"))
               .apply();
    }

    public static boolean hasCustomLocation(Context ctx, String pkg, int spaceId) {
        return sp(ctx).getBoolean(key(pkg, spaceId, "has_custom_loc"), false);
    }

    public static String getEffectiveRegion(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            return sp(ctx).getString(key(pkg, spaceId, "region_name"), getGlobalRegionName(ctx));
        }
        return getGlobalRegionName(ctx);
    }

    public static String getEffectiveRegionName(Context ctx, String pkg, int spaceId) {
        return getEffectiveRegion(ctx, pkg, spaceId);
    }

    public static double getEffectiveLat(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            try {
                return Double.parseDouble(sp(ctx).getString(key(pkg, spaceId, "lat"), String.valueOf(getGlobalLat(ctx))));
            } catch (Exception ignored) {
            }
        }
        return getGlobalLat(ctx);
    }

    public static double getEffectiveLon(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            try {
                return Double.parseDouble(sp(ctx).getString(key(pkg, spaceId, "lon"), String.valueOf(getGlobalLon(ctx))));
            } catch (Exception ignored) {
            }
        }
        return getGlobalLon(ctx);
    }

    public static double[] getEffectiveCoordinates(Context ctx, String pkg, int spaceId) {
        return new double[]{getEffectiveLat(ctx, pkg, spaceId), getEffectiveLon(ctx, pkg, spaceId)};
    }

    public static String getEffectiveTimezone(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            return sp(ctx).getString(key(pkg, spaceId, "timezone"), getGlobalTimezone(ctx));
        }
        return getGlobalTimezone(ctx);
    }

    public static String getEffectiveVirtualIp(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            return sp(ctx).getString(key(pkg, spaceId, "virtual_ip"), getGlobalVirtualIp(ctx));
        }
        return getGlobalVirtualIp(ctx);
    }

    public static String formatCoordinates(double lat, double lon) {
        return String.format(Locale.US, "%.4f, %.4f", lat, lon);
    }

    public static void registerVaultClone(Context ctx, String pkg, int spaceId) {
        Set<String> existing = new LinkedHashSet<>(sp(ctx).getStringSet("vault_clones_" + spaceId, new LinkedHashSet<>()));
        existing.add(pkg);
        sp(ctx).edit().putStringSet("vault_clones_" + spaceId, existing).apply();
    }

    public static void unregisterVaultClone(Context ctx, String pkg, int spaceId) {
        Set<String> existing = new LinkedHashSet<>(sp(ctx).getStringSet("vault_clones_" + spaceId, new LinkedHashSet<>()));
        existing.remove(pkg);
        sp(ctx).edit().putStringSet("vault_clones_" + spaceId, existing).apply();
    }

    public static Set<String> getRegisteredVaultClones(Context ctx, int spaceId) {
        return new LinkedHashSet<>(sp(ctx).getStringSet("vault_clones_" + spaceId, new LinkedHashSet<>()));
    }

    public static List<Integer> getSpacesList(Context ctx) {
        String raw = sp(ctx).getString("spaces_list", "0,1,2");
        List<Integer> result = new ArrayList<>();
        for (String part : raw.split(",")) {
            try {
                result.add(Integer.parseInt(part.trim()));
            } catch (Exception ignored) {
            }
        }
        if (result.isEmpty()) {
            result.addAll(Arrays.asList(0, 1, 2));
        }
        return result;
    }

    public static int createNewSpace(Context ctx) {
        List<Integer> spaces = getSpacesList(ctx);
        int nextId = 0;
        for (int id : spaces) {
            if (id >= nextId) nextId = id + 1;
        }
        spaces.add(nextId);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < spaces.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append(spaces.get(i));
        }
        sp(ctx).edit().putString("spaces_list", sb.toString()).apply();
        return nextId;
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "core", "CloneMetadataStore.java"), metadata_store)

    # 9. VirtualHookManager.java
    hook_manager = r"""
package com.veyravault.space.core;

import android.content.Context;
import android.os.Build;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.TimeZone;

import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.entity.location.BLocation;
import top.niunaijun.blackbox.fake.frameworks.BLocationManager;

public class VirtualHookManager {

    public static void applyGlobalEnvironmentOnStartup(Context ctx) {
        String brand = CloneMetadataStore.getGlobalDeviceBrand(ctx);
        String model = CloneMetadataStore.getGlobalDeviceModel(ctx);
        String device = CloneMetadataStore.getGlobalDeviceCode(ctx);
        double lat = CloneMetadataStore.getGlobalLat(ctx);
        double lon = CloneMetadataStore.getGlobalLon(ctx);
        String tz = CloneMetadataStore.getGlobalTimezone(ctx);
        String vip = CloneMetadataStore.getGlobalVirtualIp(ctx);
        applyVirtualProperties(ctx, brand, model, device, "Falkenstein, Germany", lat, lon, tz, vip);
        installGmsAvailabilityBypass();
    }

    public static void prepareForCloneLaunch(Context ctx, String pkg, int spaceId) {
        String brand = CloneMetadataStore.getEffectiveBrand(ctx, pkg, spaceId);
        String model = CloneMetadataStore.getEffectiveModel(ctx, pkg, spaceId);
        String device = CloneMetadataStore.getEffectiveDeviceCode(ctx, pkg, spaceId);
        String region = CloneMetadataStore.getEffectiveRegion(ctx, pkg, spaceId);
        double lat = CloneMetadataStore.getEffectiveLat(ctx, pkg, spaceId);
        double lon = CloneMetadataStore.getEffectiveLon(ctx, pkg, spaceId);
        String tz = CloneMetadataStore.getEffectiveTimezone(ctx, pkg, spaceId);
        String vip = CloneMetadataStore.getEffectiveVirtualIp(ctx, pkg, spaceId);

        applyVirtualProperties(ctx, brand, model, device, region, lat, lon, tz, vip);
        applyBlackBoxLocation(pkg, spaceId, lat, lon);
        installGmsAvailabilityBypass();
    }

    private static void applyVirtualProperties(
            Context ctx,
            String brand,
            String model,
            String device,
            String region,
            double lat,
            double lon,
            String timezoneId,
            String virtualIp) {
        try {
            setStaticField(Build.class, "BRAND", brand);
            setStaticField(Build.class, "MANUFACTURER", brand);
            setStaticField(Build.class, "MODEL", model);
            setStaticField(Build.class, "PRODUCT", model);
            setStaticField(Build.class, "DEVICE", device);
        } catch (Throwable ignored) {
        }

        try {
            if (timezoneId != null && !timezoneId.isEmpty()) {
                TimeZone.setDefault(TimeZone.getTimeZone(timezoneId));
                System.setProperty("user.timezone", timezoneId);
            }
            System.setProperty("veyra.virtual.region", region == null ? "Falkenstein, Germany" : region);
            System.setProperty("veyra.virtual.ip", virtualIp == null ? "88.198.48.102" : virtualIp);
            System.setProperty("veyra.virtual.lat", String.valueOf(lat));
            System.setProperty("veyra.virtual.lon", String.valueOf(lon));

            if (CloneMetadataStore.isGlobalProxyEnabled(ctx)) {
                String proxyHost = CloneMetadataStore.getGlobalProxyHost(ctx);
                String proxyPort = String.valueOf(CloneMetadataStore.getGlobalProxyPort(ctx));
                String proxyType = CloneMetadataStore.getGlobalProxyType(ctx);
                if (!proxyHost.isEmpty() && !proxyPort.isEmpty() && !"0".equals(proxyPort)) {
                    if ("SOCKS5".equalsIgnoreCase(proxyType)) {
                        System.setProperty("socksProxyHost", proxyHost);
                        System.setProperty("socksProxyPort", proxyPort);
                    } else {
                        System.setProperty("http.proxyHost", proxyHost);
                        System.setProperty("http.proxyPort", proxyPort);
                        System.setProperty("https.proxyHost", proxyHost);
                        System.setProperty("https.proxyPort", proxyPort);
                    }
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static void applyBlackBoxLocation(String pkg, int spaceId, double lat, double lon) {
        try {
            BLocation bLoc = new BLocation(lat, lon);
            BLocationManager mgr = BLocationManager.get();
            mgr.setPattern(spaceId, pkg, BLocationManager.CLOSE_MODE);
            for (Method m : mgr.getClass().getMethods()) {
                if (m.getName().equals("setLocation") && m.getParameterTypes().length == 3) {
                    m.invoke(mgr, spaceId, pkg, bLoc);
                } else if (m.getName().equals("setGlobalLocation") && m.getParameterTypes().length == 1) {
                    m.invoke(mgr, bLoc);
                }
            }
        } catch (Throwable ignored) {
        }
    }

    public static void installGmsAvailabilityBypass() {
        try {
            System.setProperty("veyra.gms.bypass", "true");
            BlackBoxCore core = BlackBoxCore.get();
            for (Method m : core.getClass().getMethods()) {
                if (m.getName().equalsIgnoreCase("setGmsEnable")) {
                    m.invoke(core, true);
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static void setStaticField(Class<?> cls, String fieldName, Object value) {
        try {
            Field field = cls.getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(null, value);
        } catch (Throwable ignored) {
        }
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "core", "VirtualHookManager.java"), hook_manager)

    # 10. Engine.java
    engine_java = r"""
package com.veyravault.space.core;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Build;
import android.util.LruCache;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.entity.pm.InstallResult;

public class Engine {

    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(80);

    public static class ClonedApp {
        public final String packageName;
        public final String name;
        public final Drawable icon;
        public final int userId;
        public final int spaceId;
        public final boolean installedFromVault;
        public final boolean isVaultBacked;
        public final String customDeviceName;
        public final boolean hasCustomDevice;
        public final String effectiveRegion;
        public final boolean hasCustomLoc;

        public ClonedApp(
                String packageName,
                String name,
                Drawable icon,
                int userId,
                boolean installedFromVault,
                String customDeviceName,
                boolean hasCustomDevice,
                String effectiveRegion,
                boolean hasCustomLoc) {
            this.packageName = packageName;
            this.name = name;
            this.icon = icon;
            this.userId = userId;
            this.spaceId = userId;
            this.installedFromVault = installedFromVault;
            this.isVaultBacked = installedFromVault;
            this.customDeviceName = customDeviceName;
            this.hasCustomDevice = hasCustomDevice;
            this.effectiveRegion = effectiveRegion;
            this.hasCustomLoc = hasCustomLoc;
        }
    }

    public static class InstallOptionCandidate {
        public final String packageName;
        public final String name;
        public final Drawable icon;
        public final String sourceDir;

        public InstallOptionCandidate(String packageName, String name, Drawable icon, String sourceDir) {
            this.packageName = packageName;
            this.name = name;
            this.icon = icon;
            this.sourceDir = sourceDir;
        }
    }

    public static List<Integer> getSpaces(Context ctx) {
        return CloneMetadataStore.getSpacesList(ctx);
    }

    public static int createNewSpace(Context ctx) {
        int newSpace = CloneMetadataStore.createNewSpace(ctx);
        GmsSupportManager.ensureGmsForSpace(newSpace);
        return newSpace;
    }

    public static File getApkVaultDir(Context ctx, String pkg) {
        File dir = new File(new File(ctx.getFilesDir(), "apk_vault"), pkg);
        if (!dir.exists()) {
            dir.mkdirs();
        }
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
                File baseDest = new File(vaultDir, "base.apk");
                copyFile(new File(ai.sourceDir), baseDest);
                extractNativeLibsFromApk(baseDest, new File(vaultDir, "lib"));
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP && ai.splitSourceDirs != null) {
                int idx = 0;
                for (String splitPath : ai.splitSourceDirs) {
                    if (splitPath != null) {
                        File splitDest = new File(vaultDir, "split_" + (idx++) + ".apk");
                        copyFile(new File(splitPath), splitDest);
                        extractNativeLibsFromApk(splitDest, new File(vaultDir, "lib"));
                    }
                }
            }
            syncNativeLibsToBlackBoxData(ctx, pkg, new File(vaultDir, "lib"));
        } catch (Throwable ignored) {
        }
    }

    private static void extractNativeLibsFromApk(File apkFile, File libOutDir) {
        if (apkFile == null || !apkFile.exists()) return;
        if (!libOutDir.exists()) libOutDir.mkdirs();
        String preferredAbi = (Build.SUPPORTED_64_BIT_ABIS != null && Build.SUPPORTED_64_BIT_ABIS.length > 0)
                ? "arm64-v8a" : "armeabi-v7a";
        try (ZipFile zip = new ZipFile(apkFile)) {
            Enumeration<? extends ZipEntry> entries = zip.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                if (name != null && name.startsWith("lib/") && name.endsWith(".so") && !entry.isDirectory()) {
                    if (name.contains(preferredAbi) || name.contains("armeabi")) {
                        String soName = new File(name).getName();
                        File outSo = new File(libOutDir, soName);
                        try (InputStream is = zip.getInputStream(entry);
                             FileOutputStream fos = new FileOutputStream(outSo)) {
                            byte[] buf = new byte[8192];
                            int len;
                            while ((len = is.read(buf)) > 0) {
                                fos.write(buf, 0, len);
                            }
                        }
                    }
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static void syncNativeLibsToBlackBoxData(Context ctx, String pkg, File vaultLibDir) {
        if (vaultLibDir == null || !vaultLibDir.exists()) return;
        File[] soFiles = vaultLibDir.listFiles();
        if (soFiles == null || soFiles.length == 0) return;
        try {
            File dataRoot = new File(ctx.getApplicationInfo().dataDir);
            File[] possibleDirs = new File[]{
                new File(dataRoot, "virtual/data/app/" + pkg + "/lib"),
                new File(dataRoot, "virtual/data/user/0/" + pkg + "/lib"),
                new File(ctx.getFilesDir(), "virtual/data/app/" + pkg + "/lib")
            };
            for (File targetLibDir : possibleDirs) {
                targetLibDir.mkdirs();
                for (File so : soFiles) {
                    copyFile(so, new File(targetLibDir, so.getName()));
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static void copyFile(File src, File dst) {
        if (src == null || !src.exists()) return;
        try (FileInputStream fis = new FileInputStream(src);
             FileOutputStream fos = new FileOutputStream(dst)) {
            byte[] buf = new byte[8192];
            int len;
            while ((len = fis.read(buf)) > 0) {
                fos.write(buf, 0, len);
            }
        } catch (Throwable ignored) {
        }
    }

    public static List<ClonedApp> getClonedApps(Context ctx, int spaceId) {
        List<ClonedApp> out = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Set<String> seenPackages = new LinkedHashSet<>();

        try {
            List<ApplicationInfo> installed = BlackBoxCore.get().getInstalledApplications(0, spaceId);
            if (installed != null) {
                for (ApplicationInfo info : installed) {
                    if (info == null || info.packageName == null) continue;
                    seenPackages.add(info.packageName);
                    ClonedApp app = buildCloned(ctx, pm, info.packageName, spaceId);
                    if (app != null) out.add(app);
                }
            }
        } catch (Throwable ignored) {
        }

        Set<String> vaulted = CloneMetadataStore.getRegisteredVaultClones(ctx, spaceId);
        for (String pkg : vaulted) {
            if (!seenPackages.contains(pkg)) {
                File vaultApk = getVaultBaseApk(ctx, pkg);
                if (vaultApk.exists()) {
                    try {
                        BlackBoxCore.get().installPackageAsUser(vaultApk, spaceId);
                    } catch (Throwable ignored) {
                    }
                    ClonedApp app = buildCloned(ctx, pm, pkg, spaceId);
                    if (app != null) {
                        out.add(app);
                        seenPackages.add(pkg);
                    }
                }
            }
        }

        return out;
    }

    private static ClonedApp buildCloned(Context ctx, PackageManager pm, String pkg, int spaceId) {
        try {
            String alias = CloneMetadataStore.getCustomAlias(ctx, pkg, spaceId);
            Drawable icon = ICON_CACHE.get(pkg);
            String label = null;
            boolean fromVault = false;

            try {
                ApplicationInfo hostInfo = pm.getApplicationInfo(pkg, 0);
                label = pm.getApplicationLabel(hostInfo).toString();
                if (icon == null) {
                    icon = pm.getApplicationIcon(hostInfo);
                    if (icon != null) ICON_CACHE.put(pkg, icon);
                }
            } catch (PackageManager.NameNotFoundException notOnHost) {
                fromVault = true;
                File vaultApk = getVaultBaseApk(ctx, pkg);
                if (vaultApk.exists()) {
                    PackageInfo pi = pm.getPackageArchiveInfo(vaultApk.getAbsolutePath(), 0);
                    if (pi != null && pi.applicationInfo != null) {
                        pi.applicationInfo.sourceDir = vaultApk.getAbsolutePath();
                        pi.applicationInfo.publicSourceDir = vaultApk.getAbsolutePath();
                        CharSequence cs = pi.applicationInfo.loadLabel(pm);
                        if (cs != null) label = cs.toString();
                        if (icon == null) {
                            icon = pi.applicationInfo.loadIcon(pm);
                            if (icon != null) ICON_CACHE.put(pkg, icon);
                        }
                    }
                }
            }

            if (label == null || label.isEmpty()) label = pkg;
            if (alias != null && !alias.trim().isEmpty()) {
                label = alias.trim();
            }
            if (icon == null) {
                icon = ctx.getResources().getDrawable(android.R.drawable.sym_def_app_icon);
            }

            boolean hasCustomDev = CloneMetadataStore.hasCustomDeviceIdentity(ctx, pkg, spaceId);
            String effectiveDev = CloneMetadataStore.getEffectiveDeviceSummary(ctx, pkg, spaceId);
            boolean hasCustomLoc = CloneMetadataStore.hasCustomLocation(ctx, pkg, spaceId);
            String effectiveReg = CloneMetadataStore.getEffectiveRegion(ctx, pkg, spaceId);

            return new ClonedApp(
                pkg,
                label,
                icon,
                spaceId,
                fromVault,
                effectiveDev,
                hasCustomDev,
                effectiveReg,
                hasCustomLoc
            );
        } catch (Throwable t) {
            return null;
        }
    }

    public static List<InstallOptionCandidate> getInstallableApps(Context ctx) {
        List<InstallOptionCandidate> list = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        String myPkg = ctx.getPackageName();

        Intent mainIntent = new Intent(Intent.ACTION_MAIN, null);
        mainIntent.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> resolved = pm.queryIntentActivities(mainIntent, 0);
        Set<String> added = new LinkedHashSet<>();

        if (resolved != null) {
            for (ResolveInfo ri : resolved) {
                if (ri.activityInfo == null) continue;
                String pkg = ri.activityInfo.packageName;
                if (pkg == null || pkg.equals(myPkg) || added.contains(pkg)) continue;
                added.add(pkg);
                try {
                    ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
                    String name = pm.getApplicationLabel(ai).toString();
                    Drawable icon = ICON_CACHE.get(pkg);
                    if (icon == null) {
                        icon = pm.getApplicationIcon(ai);
                        if (icon != null) ICON_CACHE.put(pkg, icon);
                    }
                    list.add(new InstallOptionCandidate(pkg, name, icon, ai.sourceDir));
                } catch (Throwable ignored) {
                }
            }
        }
        Collections.sort(list, (a, b) -> a.name.compareToIgnoreCase(b.name));
        return list;
    }

    public static List<InstallOptionCandidate> getInstalledHostApps(Context ctx) {
        return getInstallableApps(ctx);
    }

    public static boolean cloneApp(Context ctx, String pkg, int spaceId) {
        return installCloneFromHost(ctx, pkg, spaceId);
    }

    public static boolean installCloneFromHost(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.ensureGmsForSpace(spaceId);
            backupPackageToVault(ctx, pkg);
            CloneMetadataStore.registerVaultClone(ctx, pkg, spaceId);
            InstallResult res = BlackBoxCore.get().installPackageAsUser(pkg, spaceId);
            if (res != null && res.success) {
                return true;
            }
            File vaultApk = getVaultBaseApk(ctx, pkg);
            if (vaultApk.exists()) {
                InstallResult fallback = BlackBoxCore.get().installPackageAsUser(vaultApk, spaceId);
                return fallback != null && fallback.success;
            }
        } catch (Throwable ignored) {
        }
        return false;
    }

    public static String installCloneFromApkFile(Context ctx, File externalApk, int spaceId) {
        if (externalApk == null || !externalApk.exists()) return null;
        try {
            GmsSupportManager.ensureGmsForSpace(spaceId);
            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(externalApk.getAbsolutePath(), 0);
            if (pi == null || pi.packageName == null) return null;
            String pkg = pi.packageName;

            File vaultDir = getApkVaultDir(ctx, pkg);
            File vaultBase = new File(vaultDir, "base.apk");
            copyFile(externalApk, vaultBase);
            extractNativeLibsFromApk(vaultBase, new File(vaultDir, "lib"));
            syncNativeLibsToBlackBoxData(ctx, pkg, new File(vaultDir, "lib"));

            CloneMetadataStore.registerVaultClone(ctx, pkg, spaceId);
            InstallResult res = BlackBoxCore.get().installPackageAsUser(vaultBase, spaceId);
            if (res != null && res.success) {
                return pkg;
            }
        } catch (Throwable ignored) {
        }
        return null;
    }

    public static boolean launchClone(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.ensureGmsForSpace(spaceId);
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, spaceId);

            File vaultLib = new File(getApkVaultDir(ctx, pkg), "lib");
            if (vaultLib.exists()) {
                syncNativeLibsToBlackBoxData(ctx, pkg, vaultLib);
            }

            File vaultApk = getVaultBaseApk(ctx, pkg);
            if (!BlackBoxCore.get().isInstalled(pkg, spaceId) && vaultApk.exists()) {
                BlackBoxCore.get().installPackageAsUser(vaultApk, spaceId);
            }

            if ("com.android.chrome".equals(pkg) || pkg.contains("chrome")) {
                Intent chromeIntent = resolveMainIntent(ctx, pkg);
                if (chromeIntent != null) {
                    try {
                        BlackBoxCore.get().startActivity(chromeIntent, spaceId);
                        return true;
                    } catch (Throwable ignored) {
                    }
                }
            }

            boolean launched = BlackBoxCore.get().launchApk(pkg, spaceId);
            if (launched) return true;

            Intent fallbackIntent = resolveMainIntent(ctx, pkg);
            if (fallbackIntent != null) {
                BlackBoxCore.get().startActivity(fallbackIntent, spaceId);
                return true;
            }
        } catch (Throwable ignored) {
        }
        return false;
    }

    public static Intent resolveMainIntent(Context ctx, String pkg) {
        PackageManager pm = ctx.getPackageManager();
        if ("com.android.chrome".equals(pkg)) {
            Intent explicitChrome = new Intent(Intent.ACTION_MAIN);
            explicitChrome.addCategory(Intent.CATEGORY_LAUNCHER);
            explicitChrome.setPackage(pkg);
            explicitChrome.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
            explicitChrome.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            return explicitChrome;
        }
        try {
            Intent query = new Intent(Intent.ACTION_MAIN);
            query.addCategory(Intent.CATEGORY_LAUNCHER);
            query.setPackage(pkg);
            List<ResolveInfo> list = pm.queryIntentActivities(query, 0);
            if (list != null) {
                for (ResolveInfo ri : list) {
                    if (ri.activityInfo != null && ri.activityInfo.name != null) {
                        String actName = ri.activityInfo.name.toLowerCase();
                        if (!actName.contains("devui") && !actName.contains("devtools")) {
                            Intent target = new Intent(Intent.ACTION_MAIN);
                            target.addCategory(Intent.CATEGORY_LAUNCHER);
                            target.setComponent(new ComponentName(pkg, ri.activityInfo.name));
                            target.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                            return target;
                        }
                    }
                }
            }
        } catch (Throwable ignored) {
        }
        return pm.getLaunchIntentForPackage(pkg);
    }

    public static void uninstallClone(Context ctx, String pkg, int spaceId) {
        try {
            CloneMetadataStore.unregisterVaultClone(ctx, pkg, spaceId);
            CloneMetadataStore.clearCustomDeviceIdentity(ctx, pkg, spaceId);
            CloneMetadataStore.clearCustomLocation(ctx, pkg, spaceId);
            BlackBoxCore.get().uninstallPackageAsUser(pkg, spaceId);
        } catch (Throwable ignored) {
        }
    }

    public static void removeClone(Context ctx, String pkg, int spaceId) {
        uninstallClone(ctx, pkg, spaceId);
    }

    public static void requestSystemInstallApk(Context ctx, File apkFile) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(Uri.fromFile(apkFile), "application/vnd.android.package-archive");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_GRANT_READ_URI_PERMISSION);
            ctx.startActivity(intent);
        } catch (Throwable ignored) {
        }
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "core", "Engine.java"), engine_java)

    # 11. SecurityManager.java
    security_manager = r"""
package com.veyravault.space.security;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

public class SecurityManager {

    private static final String PREFS = "veyra_security_v3";

    public static final int LOCK_NONE = 0;
    public static final int LOCK_PIN = 1;
    public static final int LOCK_PATTERN = 2;

    public static final String MODE_PIN = "PIN";
    public static final String MODE_PATTERN = "PATTERN";

    private static boolean sSessionUnlocked = false;

    private static SharedPreferences sp(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static boolean isSessionUnlocked() {
        return sSessionUnlocked;
    }

    public static void setSessionUnlocked(boolean unlocked) {
        sSessionUnlocked = unlocked;
    }

    public static boolean isLockEnabled(Context ctx) {
        return sp(ctx).getBoolean("lock_enabled", false) && (hasPinConfigured(ctx) || hasPatternConfigured(ctx));
    }

    public static void setLockEnabled(Context ctx, boolean enabled) {
        sp(ctx).edit().putBoolean("lock_enabled", enabled).apply();
    }

    public static boolean hasPinConfigured(Context ctx) {
        String pin = sp(ctx).getString("pin_code", "");
        return pin != null && !pin.isEmpty();
    }

    public static boolean hasPin(Context ctx) {
        return hasPinConfigured(ctx);
    }

    public static boolean hasPatternConfigured(Context ctx) {
        String pat = sp(ctx).getString("pattern_code", "");
        return pat != null && !pat.isEmpty();
    }

    public static boolean hasPattern(Context ctx) {
        return hasPatternConfigured(ctx);
    }

    public static boolean hasBothLocksConfigured(Context ctx) {
        return hasPinConfigured(ctx) && hasPatternConfigured(ctx);
    }

    public static void savePin(Context ctx, String pin) {
        sp(ctx).edit()
               .putString("pin_code", pin == null ? "" : pin.trim())
               .putBoolean("lock_enabled", true)
               .apply();
    }

    public static void setPin(Context ctx, String pin) {
        savePin(ctx, pin);
    }

    public static void clearPin(Context ctx) {
        sp(ctx).edit().remove("pin_code").apply();
        if (!hasPatternConfigured(ctx)) {
            setLockEnabled(ctx, false);
        }
    }

    public static void savePattern(Context ctx, String pattern) {
        sp(ctx).edit()
               .putString("pattern_code", pattern == null ? "" : pattern.trim())
               .putBoolean("lock_enabled", true)
               .apply();
    }

    public static void setPattern(Context ctx, String pattern) {
        savePattern(ctx, pattern);
    }

    public static void clearPattern(Context ctx) {
        sp(ctx).edit().remove("pattern_code").apply();
        if (!hasPinConfigured(ctx)) {
            setLockEnabled(ctx, false);
        }
    }

    public static void clearAllLocks(Context ctx) {
        sp(ctx).edit()
               .remove("pin_code")
               .remove("pattern_code")
               .putBoolean("lock_enabled", false)
               .apply();
    }

    public static void setPrimaryLockType(Context ctx, String mode) {
        int code = MODE_PATTERN.equalsIgnoreCase(mode) ? LOCK_PATTERN : LOCK_PIN;
        sp(ctx).edit()
               .putString("primary_lock_mode", MODE_PATTERN.equalsIgnoreCase(mode) ? MODE_PATTERN : MODE_PIN)
               .putInt("primary_lock_int", code)
               .apply();
    }

    public static void setPrimaryLockType(Context ctx, int lockType) {
        String mode = (lockType == LOCK_PATTERN) ? MODE_PATTERN : MODE_PIN;
        sp(ctx).edit()
               .putString("primary_lock_mode", mode)
               .putInt("primary_lock_int", lockType)
               .apply();
    }

    public static int getPrimaryLockType(Context ctx) {
        if (!isLockEnabled(ctx)) return LOCK_NONE;
        int saved = sp(ctx).getInt("primary_lock_int", LOCK_PIN);
        if (saved == LOCK_PATTERN && hasPatternConfigured(ctx)) return LOCK_PATTERN;
        if (saved == LOCK_PIN && hasPinConfigured(ctx)) return LOCK_PIN;
        if (hasPinConfigured(ctx)) return LOCK_PIN;
        if (hasPatternConfigured(ctx)) return LOCK_PATTERN;
        return LOCK_NONE;
    }

    public static String getPrimaryLockModeString(Context ctx) {
        return sp(ctx).getString("primary_lock_mode", MODE_PIN);
    }

    public static String getEffectivePrimaryLockType(Context ctx) {
        String pref = getPrimaryLockModeString(ctx);
        if (MODE_PATTERN.equals(pref) && hasPatternConfigured(ctx)) {
            return MODE_PATTERN;
        }
        if (MODE_PIN.equals(pref) && hasPinConfigured(ctx)) {
            return MODE_PIN;
        }
        if (hasPinConfigured(ctx)) return MODE_PIN;
        if (hasPatternConfigured(ctx)) return MODE_PATTERN;
        return MODE_PIN;
    }

    public static boolean verifyPin(Context ctx, String input) {
        if (input == null || input.isEmpty()) return false;
        String stored = sp(ctx).getString("pin_code", "");
        return !stored.isEmpty() && stored.equals(input.trim());
    }

    public static boolean verifyPattern(Context ctx, String pattern) {
        if (pattern == null || pattern.isEmpty()) return false;
        String stored = sp(ctx).getString("pattern_code", "");
        return !stored.isEmpty() && stored.equals(pattern.trim());
    }

    public static boolean isAntiUninstallActive(Context ctx) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName admin = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
            return dpm != null && dpm.isAdminActive(admin);
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean isDeviceAdminActive(Context ctx) {
        return isAntiUninstallActive(ctx);
    }

    public static Intent buildEnableAntiUninstallIntent(Context ctx, boolean isPersian) {
        ComponentName admin = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
        Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
        intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, admin);
        intent.putExtra(
            DevicePolicyManager.EXTRA_ADD_EXPLANATION,
            isPersian
                ? "حفاظت پیشرفته امنیتی در برابر حذف غیرمجاز برنامه VeyraVault"
                : "Advanced security protection against unauthorized uninstallation of VeyraVault"
        );
        return intent;
    }

    public static void disableAntiUninstallInsideApp(Context ctx) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName admin = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
            if (dpm != null && dpm.isAdminActive(admin)) {
                dpm.removeActiveAdmin(admin);
            }
        } catch (Throwable ignored) {
        }
    }

    public static void removeDeviceAdmin(Context ctx) {
        disableAntiUninstallInsideApp(ctx);
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "security", "SecurityManager.java"), security_manager)

    # 12. VaultDeviceAdminReceiver.java
    admin_receiver = r"""
package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

import com.veyravault.space.helper.LocaleHelper;
import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    @Override
    public void onEnabled(Context context, Intent intent) {
        boolean fa = LocaleHelper.isPersian(context);
        Toast.makeText(
            context,
            fa ? "🛡️ محافظ ضدحذف فعال شد" : "🛡️ Anti-Uninstall Protection Enabled",
            Toast.LENGTH_SHORT
        ).show();
    }

    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        boolean fa = LocaleHelper.isPersian(context);
        SecurityManager.setSessionUnlocked(false);
        try {
            Intent blockIntent = new Intent(context, SecurityLockActivity.class);
            blockIntent.addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP
            );
            blockIntent.putExtra("anti_uninstall_triggered", true);
            context.startActivity(blockIntent);
        } catch (Throwable ignored) {
        }
        return fa
            ? "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است."
            : "⛔ Uninstallation is not permitted! Removing or deactivating this application is blocked.";
    }
}
"""
    write_file(os.path.join(JAVA_BASE, "security", "VaultDeviceAdminReceiver.java"), admin_receiver)


def main():
    print("=== Running VeyraVault v3.0 Upgrade - Part 1 ===")
    clean_legacy_sources()
    patch_app_build_gradle()
    create_manifest_and_resources()
    create_java_core_and_helpers()
    patch_part2_script()
    print("=== Part 1 Completed Successfully ===")


if __name__ == "__main__":
    main()
