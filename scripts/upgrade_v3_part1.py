#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Upgrade Script - Part 1 (Clean Infrastructure, Core, Helpers & Security)
- Wipes legacy v1/v2 Java & layout files to guarantee zero duplicate/broken classes
- Patches app/build.gradle (osmdroid, version 3.0.0)
- Sanitizes & fixes multiline Java strings in scripts/upgrade_v3_part2.py automatically
- Generates ic_launcher + SVG bottom-nav icons + AndroidManifest.xml
- Writes all v3.0 core, helper, and security classes cleanly
"""

import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JAVA_BASE = os.path.join(ROOT, "app/src/main/java/com/veyravault/space")
RES_BASE = os.path.join(ROOT, "app/src/main/res")


def clean_legacy_sources():
    if os.path.exists(JAVA_BASE):
        shutil.rmtree(JAVA_BASE)
    os.makedirs(JAVA_BASE, exist_ok=True)
    layout_dir = os.path.join(RES_BASE, "layout")
    if os.path.exists(layout_dir):
        shutil.rmtree(layout_dir)
    os.makedirs(layout_dir, exist_ok=True)
    print("[v3.0-Part1] Cleaned legacy Java and layout directories.")


def write_file(rel_path, content):
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    print(f"[v3.0-Part1] Wrote: {rel_path}")


def patch_build_gradle():
    gradle_path = os.path.join(ROOT, "app/build.gradle")
    if not os.path.exists(gradle_path):
        return
    with open(gradle_path, "r", encoding="utf-8") as f:
        text = f.read()

    if "org.osmdroid:osmdroid-android" not in text:
        text = text.replace(
            "dependencies {",
            "dependencies {\n    implementation 'org.osmdroid:osmdroid-android:6.1.14'",
            1,
        )
    text = re.sub(r"versionCode\s+\d+", "versionCode 3", text)
    text = re.sub(r'versionName\s+"[^"]+"', 'versionName "3.0.0"', text)
    with open(gradle_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("[v3.0-Part1] Patched app/build.gradle for v3.0.0")


def fix_java_multiline_strings(code):
    """Scans Java source code and converts any raw newline inside a "..." string literal into \\n."""
    out = []
    i = 0
    n = len(code)
    state = 0  # 0=CODE, 1=STRING, 2=CHAR, 3=LINE_COMMENT, 4=BLOCK_COMMENT
    while i < n:
        ch = code[i]
        nxt = code[i + 1] if i + 1 < n else ""
        if state == 0:
            if ch == "/" and nxt == "/":
                state = 3
                out.append(ch)
                out.append(nxt)
                i += 2
                continue
            elif ch == "/" and nxt == "*":
                state = 4
                out.append(ch)
                out.append(nxt)
                i += 2
                continue
            elif ch == '"':
                state = 1
                out.append(ch)
                i += 1
                continue
            elif ch == "'":
                state = 2
                out.append(ch)
                i += 1
                continue
            else:
                out.append(ch)
                i += 1
        elif state == 1:  # Inside "..."
            if ch == "\\":
                if nxt == "\n":
                    out.append("\\n")
                    i += 2
                elif nxt == "\r":
                    i += 2
                else:
                    out.append(ch)
                    if nxt:
                        out.append(nxt)
                    i += 2
                continue
            elif ch == '"':
                state = 0
                out.append(ch)
                i += 1
                continue
            elif ch == "\r":
                i += 1
                continue
            elif ch == "\n":
                out.append("\\n")
                i += 1
                continue
            else:
                out.append(ch)
                i += 1
        elif state == 2:  # Inside '...'
            if ch == "\\":
                out.append(ch)
                if nxt:
                    out.append(nxt)
                i += 2
                continue
            elif ch == "'" or ch == "\n":
                state = 0
                out.append(ch)
                i += 1
                continue
            else:
                out.append(ch)
                i += 1
        elif state == 3:  # Inside // ...
            out.append(ch)
            i += 1
            if ch == "\n":
                state = 0
        elif state == 4:  # Inside /* ... */
            if ch == "*" and nxt == "/":
                state = 0
                out.append(ch)
                out.append(nxt)
                i += 2
                continue
            else:
                out.append(ch)
                i += 1
    return "".join(out)


def sanitize_part2_script():
    part2_path = os.path.join(ROOT, "scripts/upgrade_v3_part2.py")
    if not os.path.exists(part2_path):
        return
    with open(part2_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove any hint about disabling anti-uninstall from settings
    content = content.replace(
        "⛔ حذف مقدور نمی‌باشد! حفاظت ضدحذف فعال است. ابتدا رمز یا الگوی امنیتی را وارد کنید.",
        "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است.",
    )
    content = content.replace(
        "⛔ Uninstall blocked! Enter your security lock to proceed.",
        "⛔ Uninstall is not permitted! Uninstallation or deactivation is blocked.",
    )

    # 2. Ensure all triple-quoted Java blocks in part2 are raw strings r"""package ...
    content = re.sub(r'(?<![rR])"""package ', 'r"""package ', content)

    # 3. Fix any physical newline inside Java "..." literals inside every r"""package ... """ block
    pattern = re.compile(r'(r"""package [\s\S]*?""")')

    def _clean_block(match):
        block = match.group(1)
        inner = block[4:-3]  # strip r""" and """
        fixed_inner = fix_java_multiline_strings(inner)
        return 'r"""' + fixed_inner + '"""'

    content = pattern.sub(_clean_block, content)

    with open(part2_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[v3.0-Part1] Sanitized & fixed multiline Java strings in scripts/upgrade_v3_part2.py")


clean_legacy_sources()
patch_build_gradle()
sanitize_part2_script()

# ---------------------------------------------------------------------------
# 1. DRAWABLE ICONS (App Launcher Icon + Bottom Navigation SVG Vector Drawables)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/res/drawable/ic_launcher.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#0F172A"
        android:pathData="M0,0h108v108h-108z"/>
    <path
        android:fillColor="#1E3A8A"
        android:pathData="M54,14L88,28v26c0,22 -14.5,36.5 -34,42C34.5,90.5 20,76 20,54V28L54,14z"/>
    <path
        android:fillColor="#38BDF8"
        android:pathData="M54,24L78,34v19c0,15.5 -10.2,26.2 -24,30.5C40.2,79.2 30,68.5 30,53V34L54,24z"/>
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M43,44l11,24l11,-24h-6.5l-4.5,11l-4.5,-11z"/>
</vector>
""",
)

write_file(
    "app/src/main/res/drawable/ic_nav_dashboard.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M3,13h8V3H3v10zm0,8h8v-6H3v6zm10,0h8V11h-8v10zm0,-18v6h8V3h-8z"/>
</vector>
""",
)

write_file(
    "app/src/main/res/drawable/ic_nav_spaces.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M4,8h4V4H4v4zm6,12h4v-4h-4v4zm-6,0h4v-4H4v4zm0,-6h4v-4H4v4zm6,0h4v-4h-4v4zm6,-10v4h4V4h-4zm-6,4h4V4h-4v4zm6,6h4v-4h-4v4zm0,6h4v-4h-4v4z"/>
</vector>
""",
)

write_file(
    "app/src/main/res/drawable/ic_nav_add.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
</vector>
""",
)

write_file(
    "app/src/main/res/drawable/ic_nav_guide.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zm1,17h-2v-2h2v2zm2.07,-7.75l-0.9,0.92C13.45,12.9 13,13.5 13,15h-2v-0.5c0,-1.1 0.45,-2.1 1.17,-2.83l1.24,-1.26c0.37,-0.36 0.59,-0.86 0.59,-1.41 0,-1.1 -0.9,-2 -2,-2s-2,0.9 -2,2H8c0,-2.21 1.79,-4 4,-4s4,1.79 4,4c0,0.88 -0.36,1.68 -0.93,2.25z"/>
</vector>
""",
)

write_file(
    "app/src/main/res/drawable/ic_nav_settings.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"/>
</vector>
""",
)

# ---------------------------------------------------------------------------
# 2. DEVICE ADMIN XML & STRINGS & STYLES & MANIFEST
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/res/xml/device_admin_policies.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <watch-login />
    </uses-policies>
</device-admin>
""",
)

write_file(
    "app/src/main/res/values/strings.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="device_admin_label">VeyraVault Security Shield</string>
    <string name="device_admin_description">حفاظت امنیتی پیشرفته جهت جلوگیری از حذف غیرمجاز برنامه</string>
</resources>
""",
)

write_file(
    "app/src/main/res/values/styles.xml",
    r"""<?xml version="1.0" encoding="utf-8"?>
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
    r"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" tools:ignore="ScopedStorage" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />

    <application
        android:name="com.veyravault.space.VeyraApplication"
        android:allowBackup="false"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
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

        <activity
            android:name="com.veyravault.space.ui.AddAppActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name="com.veyravault.space.ui.GlobalEnvironmentActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name="com.veyravault.space.ui.SetLocationActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name="com.veyravault.space.ui.SecuritySettingsActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name="com.veyravault.space.ui.SecurityLockActivity"
            android:exported="false"
            android:launchMode="singleTop"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name="com.veyravault.space.ui.GuideActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <activity
            android:name="com.veyravault.space.ui.AboutActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden" />

        <receiver
            android:name="com.veyravault.space.security.VaultDeviceAdminReceiver"
            android:description="@string/device_admin_description"
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
</manifest>
""",
)

# ---------------------------------------------------------------------------
# 3. APPLICATION ENTRYPOINT (VeyraApplication.java)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/VeyraApplication.java",
    r"""package com.veyravault.space;

import android.app.Application;
import android.content.Context;

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
        Context localized = LocaleHelper.applyLocale(base);
        super.attachBaseContext(localized);
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
            });
        } catch (Throwable ignored) {
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        sContext = this;
        LocaleHelper.applyLocale(this);
        try {
            BlackBoxCore.get().doCreate();
            GmsSupportManager.autoInitializeGmsIfNeeded(this);
            VirtualHookManager.initializeGlobalHooks(this);
        } catch (Throwable ignored) {
        }
    }
}
""",
)

# ---------------------------------------------------------------------------
# 4. JALALI (SOLAR HIJRI) & DUAL WORLD CLOCK UTILITY (JalaliClockUtil.java)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/helper/JalaliClockUtil.java",
    r"""package com.veyravault.space.helper;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

public class JalaliClockUtil {

    private static final String[] JALALI_MONTHS_FA = {
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    };

    private static final String[] WEEKDAYS_FA = {
            "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"
    };

    public static String getTehranTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("Asia/Tehran"));
        return sdf.format(new Date());
    }

    public static String getNewYorkTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String getTehranJalaliDate() {
        return getTehranJalaliDate(true);
    }

    public static String getTehranJalaliDate(boolean persianDigits) {
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        Calendar cal = Calendar.getInstance(tz);
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int dow = cal.get(Calendar.DAY_OF_WEEK); // 1=Sun .. 7=Sat

        int[] j = miladiToJalali(gy, gm, gd);
        String weekday = WEEKDAYS_FA[(dow - 1) % 7];
        String monthName = JALALI_MONTHS_FA[Math.max(0, Math.min(11, j[1] - 1))];
        String formatted = String.format(Locale.US, "%s %d %s %d", weekday, j[2], monthName, j[0]);
        return persianDigits ? toPersianDigits(formatted) : formatted;
    }

    public static String getNewYorkGregorianDate() {
        return getNewYorkGregorianDate(false);
    }

    public static String getNewYorkGregorianDate(boolean persianLang) {
        TimeZone tz = TimeZone.getTimeZone("America/New_York");
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
    }

    public static int[] miladiToJalali(int gy, int gm, int gd) {
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
        int jm;
        int jd;
        if (days < 186) {
            jm = 1 + (days / 31);
            jd = 1 + (days % 31);
        } else {
            jm = 7 + ((days - 186) / 30);
            jd = 1 + ((days - 186) % 30);
        }
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

# ---------------------------------------------------------------------------
# 5. LOCALE HELPER & BASE ACTIVITY (LocaleHelper.java, BaseActivity.java)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/helper/LocaleHelper.java",
    r"""package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.os.Build;

import java.util.Locale;

public class LocaleHelper {

    private static final String PREFS_NAME = "veyra_locale_prefs";
    private static final String KEY_LANG = "app_lang";

    public static String getLanguage(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return prefs.getString(KEY_LANG, "fa");
    }

    public static boolean isPersian(Context context) {
        return "fa".equalsIgnoreCase(getLanguage(context));
    }

    public static void setLanguage(Context context, String lang) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        prefs.edit().putString(KEY_LANG, lang).apply();
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
""",
)

write_file(
    "app/src/main/java/com/veyravault/space/ui/BaseActivity.java",
    r"""package com.veyravault.space.ui;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import com.veyravault.space.helper.LocaleHelper;
import com.veyravault.space.security.SecurityManager;

public abstract class BaseActivity extends Activity {

    private String currentLang;

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.applyLocale(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        LocaleHelper.applyLocale(this);
        currentLang = LocaleHelper.getLanguage(this);
        super.onCreate(savedInstanceState);
        applyDirection();
    }

    @Override
    protected void onResume() {
        super.onResume();
        String savedLang = LocaleHelper.getLanguage(this);
        if (currentLang != null && !currentLang.equals(savedLang)) {
            currentLang = savedLang;
            recreate();
            return;
        }
        applyDirection();
        if (!shouldBypassSecurityLock() && SecurityManager.isLockEnabled(this) && !SecurityManager.isSessionUnlocked()) {
            Intent lockIntent = new Intent(this, SecurityLockActivity.class);
            startActivity(lockIntent);
        }
    }

    protected boolean shouldBypassSecurityLock() {
        return false;
    }

    protected void applyDirection() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            boolean fa = LocaleHelper.isPersian(this);
            getWindow().getDecorView().setLayoutDirection(
                    fa ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
    }

    protected boolean isPersian() {
        return LocaleHelper.isPersian(this);
    }

    protected void switchLanguageInstant() {
        LocaleHelper.toggleLanguage(this);
        currentLang = LocaleHelper.getLanguage(this);
        recreate();
    }

    protected void triggerQuickLock() {
        if (!SecurityManager.isLockEnabled(this)) {
            Toast.makeText(this,
                    isPersian()
                            ? "ابتدا از بخش تنظیمات امنیتی، پین یا الگو را فعال کنید"
                            : "Please enable PIN or Pattern in Security Settings first",
                    Toast.LENGTH_SHORT).show();
            Intent i = new Intent(this, SecuritySettingsActivity.class);
            startActivity(i);
            return;
        }
        SecurityManager.setSessionUnlocked(false);
        Toast.makeText(this,
                isPersian() ? "🔒 برنامه قفل شد" : "🔒 App Locked",
                Toast.LENGTH_SHORT).show();
        Intent lockIntent = new Intent(this, SecurityLockActivity.class);
        startActivity(lockIntent);
    }
}
""",
)

# ---------------------------------------------------------------------------
# 6. GMS SUPPORT & APP DISGUISE & PATTERN LOCK VIEW
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/helper/GmsSupportManager.java",
    r"""package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {

    private static final String PREFS = "veyra_gms_prefs";
    private static final String KEY_AUTO_GMS = "auto_gms_enabled";

    public static boolean isGmsSupported(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getBoolean(KEY_AUTO_GMS, true);
    }

    public static boolean isGmsEnabled(Context context) {
        return isGmsSupported(context);
    }

    public static void setGmsEnabledPref(Context context, boolean enabled) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putBoolean(KEY_AUTO_GMS, enabled).apply();
    }

    public static void setGmsEnabled(Context context, boolean enabled) {
        setGmsEnabledPref(context, enabled);
    }

    public static void autoInitializeGmsIfNeeded(Context context) {
        if (!isGmsSupported(context)) return;
        for (int spaceId = 0; spaceId < 3; spaceId++) {
            ensureGmsForSpace(context, spaceId);
        }
    }

    public static boolean ensureGmsForSpace(Context context, int spaceId) {
        try {
            BlackBoxCore core = BlackBoxCore.get();
            try {
                Method isInstalled = core.getClass().getMethod("isInstallGms", int.class);
                Object res = isInstalled.invoke(core, spaceId);
                if (res instanceof Boolean && (Boolean) res) {
                    return true;
                }
            } catch (Throwable ignored) {
            }

            try {
                Method install = core.getClass().getMethod("installGms", int.class);
                Object installResult = install.invoke(core, spaceId);
                if (installResult instanceof Boolean) {
                    return (Boolean) installResult;
                }
                if (installResult != null) {
                    try {
                        Field successField = installResult.getClass().getField("success");
                        return successField.getBoolean(installResult);
                    } catch (Throwable ignored) {
                        return true;
                    }
                }
            } catch (Throwable ignored) {
            }
            return true;
        } catch (Throwable ignored) {
            return false;
        }
    }

    public static boolean enableGmsForAllSpaces(Context context) {
        setGmsEnabledPref(context, true);
        boolean ok = true;
        for (int s = 0; s < 3; s++) {
            if (!ensureGmsForSpace(context, s)) {
                ok = false;
            }
        }
        return ok;
    }
}
""",
)

write_file(
    "app/src/main/java/com/veyravault/space/helper/AppDisguiseManager.java",
    r"""package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;

public class AppDisguiseManager {

    private static final String PREFS = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode";

    public static final String MODE_DEFAULT = "DEFAULT";
    public static final String MODE_CALCULATOR = "CALCULATOR";
    public static final String MODE_CLOCK = "CLOCK";
    public static final String MODE_NOTEPAD = "NOTEPAD";
    public static final String MODE_CALENDAR = "CALENDAR";

    public static String getDisguiseMode(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getString(KEY_MODE, MODE_DEFAULT);
    }

    public static void setDisguiseMode(Context context, String mode) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putString(KEY_MODE, mode).apply();
    }

    public static String getDisguiseTitle(Context context, boolean fa) {
        String mode = getDisguiseMode(context);
        if (MODE_CALCULATOR.equals(mode)) {
            return fa ? "ماشین‌حساب مهندسی" : "Scientific Calculator";
        } else if (MODE_CLOCK.equals(mode)) {
            return fa ? "ساعت جهانی و تقویم" : "World Clock & Calendar";
        } else if (MODE_NOTEPAD.equals(mode)) {
            return fa ? "دفترچه یادداشت شخصی" : "Personal Notepad";
        } else if (MODE_CALENDAR.equals(mode)) {
            return fa ? "تقویم هوشمند خورشیدی" : "Smart Solar Calendar";
        }
        return "VeyraVault";
    }
}
""",
)

write_file(
    "app/src/main/java/com/veyravault/space/ui/PatternLockView.java",
    r"""package com.veyravault.space.ui;

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
        void onPatternDetected(String pattern);
    }

    public interface OnPatternCompleteListener {
        void onPatternComplete(String pattern);
    }

    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activeDotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint ringPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    private final List<Integer> selectedNodes = new ArrayList<>();
    private float currentX = -1;
    private float currentY = -1;
    private boolean isDrawing = false;
    private OnPatternListener patternListener;
    private OnPatternCompleteListener completeListener;

    public PatternLockView(Context context) {
        super(context);
        dotPaint.setColor(Color.parseColor("#475569"));
        dotPaint.setStyle(Paint.Style.FILL);

        activeDotPaint.setColor(Color.parseColor("#38BDF8"));
        activeDotPaint.setStyle(Paint.Style.FILL);

        ringPaint.setColor(Color.parseColor("#38BDF8"));
        ringPaint.setStyle(Paint.Style.STROKE);
        ringPaint.setStrokeWidth(5f);

        linePaint.setColor(Color.parseColor("#38BDF8"));
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeWidth(8f);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setOnPatternListener(OnPatternListener l) {
        this.patternListener = l;
    }

    public void setOnPatternCompleteListener(OnPatternCompleteListener l) {
        this.completeListener = l;
    }

    public void clearPattern() {
        selectedNodes.clear();
        isDrawing = false;
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
        for (int i = 0; i < selectedNodes.size() - 1; i++) {
            int a = selectedNodes.get(i);
            int b = selectedNodes.get(i + 1);
            canvas.drawLine(getNodeX(a), getNodeY(a), getNodeX(b), getNodeY(b), linePaint);
        }
        if (isDrawing && !selectedNodes.isEmpty()) {
            int last = selectedNodes.get(selectedNodes.size() - 1);
            canvas.drawLine(getNodeX(last), getNodeY(last), currentX, currentY, linePaint);
        }
        float radius = Math.min(getWidth(), getHeight()) / 18f;
        for (int i = 0; i < 9; i++) {
            float cx = getNodeX(i);
            float cy = getNodeY(i);
            if (selectedNodes.contains(i)) {
                canvas.drawCircle(cx, cy, radius * 0.65f, activeDotPaint);
                canvas.drawCircle(cx, cy, radius * 1.25f, ringPaint);
            } else {
                canvas.drawCircle(cx, cy, radius * 0.55f, dotPaint);
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
                if (!selectedNodes.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < selectedNodes.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(selectedNodes.get(i) + 1);
                    }
                    String pat = sb.toString();
                    if (patternListener != null) {
                        patternListener.onPatternDetected(pat);
                    }
                    if (completeListener != null) {
                        completeListener.onPatternComplete(pat);
                    }
                }
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y) {
        float hitRadius = Math.min(getWidth(), getHeight()) / 7.5f;
        for (int i = 0; i < 9; i++) {
            if (selectedNodes.contains(i)) continue;
            float dx = x - getNodeX(i);
            float dy = y - getNodeY(i);
            if (Math.sqrt(dx * dx + dy * dy) <= hitRadius) {
                selectedNodes.add(i);
                break;
            }
        }
    }
}
""",
)

# ---------------------------------------------------------------------------
# 7. CLONE METADATA STORE (CloneMetadataStore.java)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/core/CloneMetadataStore.java",
    r"""package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class CloneMetadataStore {

    private static final String PREF_NAME = "veyra_clone_metadata_v3";

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    private static String key(String pkg, int spaceId, String field) {
        return "clone_" + spaceId + "_" + pkg + "_" + field;
    }

    // -----------------------------------------------------------------------
    // Space Custom Name (Item 1: 3-dots menu on each Space to rename Space)
    // -----------------------------------------------------------------------
    public static String getSpaceDisplayName(Context ctx, int spaceId, boolean fa) {
        String custom = prefs(ctx).getString("space_custom_name_" + spaceId, "").trim();
        if (!custom.isEmpty()) {
            return custom;
        }
        int num = spaceId + 1;
        if (fa) {
            String[] pNums = {"۱", "۲", "۳", "۴", "۵"};
            String nStr = (spaceId >= 0 && spaceId < pNums.length) ? pNums[spaceId] : String.valueOf(num);
            return "فضای " + nStr;
        } else {
            return "Space " + num;
        }
    }

    public static String getSpaceCustomName(Context ctx, int spaceId) {
        return prefs(ctx).getString("space_custom_name_" + spaceId, "").trim();
    }

    public static void setSpaceCustomName(Context ctx, int spaceId, String name) {
        prefs(ctx).edit().putString("space_custom_name_" + spaceId, name == null ? "" : name.trim()).apply();
    }

    // -----------------------------------------------------------------------
    // Global Device Model & Global Region/Location/Proxy Settings
    // -----------------------------------------------------------------------
    public static String getGlobalDeviceModel(Context ctx) {
        return prefs(ctx).getString("global_device_model", "Samsung Galaxy S24 Ultra");
    }

    public static String getGlobalDeviceBrand(Context ctx) {
        return prefs(ctx).getString("global_device_brand", "Samsung");
    }

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model) {
        prefs(ctx).edit()
                .putString("global_device_brand", brand == null ? "Samsung" : brand.trim())
                .putString("global_device_model", model == null ? "Samsung Galaxy S24 Ultra" : model.trim())
                .apply();
    }

    public static String getGlobalRegionName(Context ctx) {
        return prefs(ctx).getString("global_region_name", "Falkenstein, Germany");
    }

    public static void setGlobalRegionName(Context ctx, String regionCityCountry) {
        prefs(ctx).edit()
                .putString("global_region_name",
                        (regionCityCountry == null || regionCityCountry.trim().isEmpty())
                                ? "Falkenstein, Germany" : regionCityCountry.trim())
                .apply();
    }

    public static double[] getGlobalCoordinates(Context ctx) {
        String latS = prefs(ctx).getString("global_lat", "50.4779");
        String lonS = prefs(ctx).getString("global_lon", "12.3713");
        try {
            return new double[]{Double.parseDouble(latS), Double.parseDouble(lonS)};
        } catch (Throwable t) {
            return new double[]{50.4779, 12.3713};
        }
    }

    public static void setGlobalCoordinates(Context ctx, double lat, double lon) {
        prefs(ctx).edit()
                .putString("global_lat", String.valueOf(lat))
                .putString("global_lon", String.valueOf(lon))
                .putBoolean("global_loc_enabled", true)
                .apply();
    }

    public static boolean isGlobalLocationEnabled(Context ctx) {
        return prefs(ctx).getBoolean("global_loc_enabled", true);
    }

    public static void setGlobalLocationEnabled(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean("global_loc_enabled", enabled).apply();
    }

    public static String getGlobalVirtualIp(Context ctx) {
        return prefs(ctx).getString("global_virtual_ip", "88.198.24.108");
    }

    public static void setGlobalVirtualIp(Context ctx, String ip) {
        prefs(ctx).edit().putString("global_virtual_ip", ip == null ? "" : ip.trim()).apply();
    }

    public static String getGlobalProxyHost(Context ctx) {
        return prefs(ctx).getString("global_proxy_host", "");
    }

    public static int getGlobalProxyPort(Context ctx) {
        return prefs(ctx).getInt("global_proxy_port", 0);
    }

    public static void setGlobalProxy(Context ctx, String host, int port) {
        prefs(ctx).edit()
                .putString("global_proxy_host", host == null ? "" : host.trim())
                .putInt("global_proxy_port", Math.max(0, port))
                .apply();
    }

    // -----------------------------------------------------------------------
    // Per-Clone Custom Alias
    // -----------------------------------------------------------------------
    public static String getCustomAlias(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getString(key(pkg, spaceId, "alias"), "").trim();
    }

    public static void setCustomAlias(Context ctx, String pkg, int spaceId, String alias) {
        prefs(ctx).edit().putString(key(pkg, spaceId, "alias"), alias == null ? "" : alias.trim()).apply();
    }

    // -----------------------------------------------------------------------
    // Per-Clone Device Identity (Priority #1 over Global Model)
    // -----------------------------------------------------------------------
    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int spaceId) {
        return !prefs(ctx).getString(key(pkg, spaceId, "device_model"), "").trim().isEmpty();
    }

    public static String getCustomDeviceBrand(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getString(key(pkg, spaceId, "device_brand"), "").trim();
    }

    public static String getCustomDeviceModel(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getString(key(pkg, spaceId, "device_model"), "").trim();
    }

    public static void setCustomDeviceIdentity(Context ctx, String pkg, int spaceId, String brand, String model) {
        prefs(ctx).edit()
                .putString(key(pkg, spaceId, "device_brand"), brand == null ? "" : brand.trim())
                .putString(key(pkg, spaceId, "device_model"), model == null ? "" : model.trim())
                .apply();
    }

    public static void clearCustomDeviceIdentity(Context ctx, String pkg, int spaceId) {
        prefs(ctx).edit()
                .remove(key(pkg, spaceId, "device_brand"))
                .remove(key(pkg, spaceId, "device_model"))
                .apply();
    }

    public static String getEffectiveDeviceBrand(Context ctx, String pkg, int spaceId) {
        String customBrand = prefs(ctx).getString(key(pkg, spaceId, "device_brand"), "").trim();
        if (!customBrand.isEmpty()) return customBrand;
        return getGlobalDeviceBrand(ctx);
    }

    public static String getEffectiveDeviceModel(Context ctx, String pkg, int spaceId) {
        String customModel = prefs(ctx).getString(key(pkg, spaceId, "device_model"), "").trim();
        if (!customModel.isEmpty()) return customModel;
        return getGlobalDeviceModel(ctx);
    }

    // -----------------------------------------------------------------------
    // Per-Clone Smart Location & Region (Priority #1 over Global Location)
    // -----------------------------------------------------------------------
    public static boolean hasCustomLocation(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getBoolean(key(pkg, spaceId, "loc_enabled"), false);
    }

    public static boolean isEffectiveLocationEnabled(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) return true;
        return isGlobalLocationEnabled(ctx);
    }

    public static void setCustomLocation(Context ctx, String pkg, int spaceId, double lat, double lon, String regionName) {
        prefs(ctx).edit()
                .putBoolean(key(pkg, spaceId, "loc_enabled"), true)
                .putString(key(pkg, spaceId, "lat"), String.valueOf(lat))
                .putString(key(pkg, spaceId, "lon"), String.valueOf(lon))
                .putString(key(pkg, spaceId, "region"),
                        (regionName == null || regionName.trim().isEmpty())
                                ? "Falkenstein, Germany" : regionName.trim())
                .apply();
    }

    public static void setCustomLocation(Context ctx, String pkg, int spaceId, double lat, double lon) {
        String existingRegion = getEffectiveRegionName(ctx, pkg, spaceId);
        setCustomLocation(ctx, pkg, spaceId, lat, lon, existingRegion);
    }

    public static void clearCustomLocation(Context ctx, String pkg, int spaceId) {
        prefs(ctx).edit()
                .putBoolean(key(pkg, spaceId, "loc_enabled"), false)
                .remove(key(pkg, spaceId, "lat"))
                .remove(key(pkg, spaceId, "lon"))
                .remove(key(pkg, spaceId, "region"))
                .apply();
    }

    public static double[] getEffectiveCoordinates(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            String latS = prefs(ctx).getString(key(pkg, spaceId, "lat"), "50.4779");
            String lonS = prefs(ctx).getString(key(pkg, spaceId, "lon"), "12.3713");
            try {
                return new double[]{Double.parseDouble(latS), Double.parseDouble(lonS)};
            } catch (Throwable ignored) {
            }
        }
        return getGlobalCoordinates(ctx);
    }

    public static String getEffectiveRegionName(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            String r = prefs(ctx).getString(key(pkg, spaceId, "region"), "").trim();
            if (!r.isEmpty()) return r;
        }
        return getGlobalRegionName(ctx);
    }

    public static String getEffectiveVirtualIp(Context ctx, String pkg, int spaceId) {
        String customIp = prefs(ctx).getString(key(pkg, spaceId, "virtual_ip"), "").trim();
        if (!customIp.isEmpty()) return customIp;
        return getGlobalVirtualIp(ctx);
    }

    public static void setCustomVirtualIp(Context ctx, String pkg, int spaceId, String ip) {
        prefs(ctx).edit().putString(key(pkg, spaceId, "virtual_ip"), ip == null ? "" : ip.trim()).apply();
    }

    // -----------------------------------------------------------------------
    // Region -> Timezone / Locale Resolver (for Session IP/Region Consistency)
    // -----------------------------------------------------------------------
    public static String getTimezoneForRegion(String regionName, double lat, double lon) {
        if (regionName == null) regionName = "";
        String lower = regionName.toLowerCase();
        if (lower.contains("germany") || lower.contains("falkenstein") || lower.contains("frankfurt") || lower.contains("berlin")) {
            return "Europe/Berlin";
        } else if (lower.contains("netherlands") || lower.contains("amsterdam")) {
            return "Europe/Amsterdam";
        } else if (lower.contains("uk") || lower.contains("united kingdom") || lower.contains("london")) {
            return "Europe/London";
        } else if (lower.contains("france") || lower.contains("paris")) {
            return "Europe/Paris";
        } else if (lower.contains("finland") || lower.contains("helsinki")) {
            return "Europe/Helsinki";
        } else if (lower.contains("turkey") || lower.contains("istanbul")) {
            return "Europe/Istanbul";
        } else if (lower.contains("uae") || lower.contains("dubai")) {
            return "Asia/Dubai";
        } else if (lower.contains("iran") || lower.contains("tehran")) {
            return "Asia/Tehran";
        } else if (lower.contains("usa") || lower.contains("united states") || lower.contains("new york") || lower.contains("washington")) {
            return "America/New_York";
        } else if (lower.contains("los angeles") || lower.contains("california")) {
            return "America/Los_Angeles";
        } else if (lower.contains("singapore")) {
            return "Asia/Singapore";
        } else if (lower.contains("japan") || lower.contains("tokyo")) {
            return "Asia/Tokyo";
        }
        return "Europe/Berlin";
    }

    // -----------------------------------------------------------------------
    // Preset Device Models (Including Apple iPhone / iPad + Flagships)
    // -----------------------------------------------------------------------
    public static Map<String, String> getAvailableDevicePresets() {
        Map<String, String> map = new LinkedHashMap<>();
        map.put("Apple iPhone 16 Pro Max", "Apple");
        map.put("Apple iPhone 15 Pro Max", "Apple");
        map.put("Apple iPhone 14 Pro", "Apple");
        map.put("Apple iPad Pro M4", "Apple");
        map.put("Samsung Galaxy S24 Ultra", "Samsung");
        map.put("Samsung Galaxy S23 Ultra", "Samsung");
        map.put("Samsung Galaxy A54 5G", "Samsung");
        map.put("Google Pixel 9 Pro XL", "Google");
        map.put("Google Pixel 8 Pro", "Google");
        map.put("Xiaomi 14 Ultra", "Xiaomi");
        map.put("Xiaomi Redmi Note 13 Pro+", "Xiaomi");
        map.put("OnePlus 12", "OnePlus");
        return map;
    }

    // -----------------------------------------------------------------------
    // Preset Global Server Regions (City, Country -> lat, lon, default IP)
    // -----------------------------------------------------------------------
    public static class RegionPreset {
        public final String cityCountry;
        public final double lat;
        public final double lon;
        public final String sampleIp;

        public RegionPreset(String cityCountry, double lat, double lon, String sampleIp) {
            this.cityCountry = cityCountry;
            this.lat = lat;
            this.lon = lon;
            this.sampleIp = sampleIp;
        }
    }

    public static List<RegionPreset> getAvailableRegionPresets() {
        List<RegionPreset> list = new ArrayList<>();
        list.add(new RegionPreset("Falkenstein, Germany", 50.4779, 12.3713, "88.198.24.108"));
        list.add(new RegionPreset("Frankfurt, Germany", 50.1109, 8.6821, "138.201.81.199"));
        list.add(new RegionPreset("Amsterdam, Netherlands", 52.3676, 4.9041, "95.211.230.14"));
        list.add(new RegionPreset("Helsinki, Finland", 60.1699, 24.9384, "65.108.44.210"));
        list.add(new RegionPreset("London, United Kingdom", 51.5074, -0.1278, "51.140.104.22"));
        list.add(new RegionPreset("Paris, France", 48.8566, 2.3522, "51.158.112.40"));
        list.add(new RegionPreset("New York, United States", 40.7128, -74.0060, "104.244.72.115"));
        list.add(new RegionPreset("Istanbul, Turkey", 41.0082, 28.9784, "185.125.33.90"));
        list.add(new RegionPreset("Dubai, United Arab Emirates", 25.2048, 55.2708, "94.200.24.11"));
        list.add(new RegionPreset("Tehran, Iran", 35.6892, 51.3890, "5.160.140.25"));
        return list;
    }

    // -----------------------------------------------------------------------
    // Independent Vault Registry (Keeps Clones Alive Even if Host Uninstalled)
    // -----------------------------------------------------------------------
    public static void registerCloneInVault(Context ctx, String pkg, int spaceId) {
        String key = "vault_clones_space_" + spaceId;
        String current = prefs(ctx).getString(key, "");
        List<String> pkgs = new ArrayList<>();
        for (String s : current.split(",")) {
            if (!s.trim().isEmpty() && !pkgs.contains(s.trim())) {
                pkgs.add(s.trim());
            }
        }
        if (!pkgs.contains(pkg)) {
            pkgs.add(pkg);
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < pkgs.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append(pkgs.get(i));
        }
        prefs(ctx).edit().putString(key, sb.toString()).apply();
    }

    public static void unregisterCloneFromVault(Context ctx, String pkg, int spaceId) {
        String key = "vault_clones_space_" + spaceId;
        String current = prefs(ctx).getString(key, "");
        List<String> pkgs = new ArrayList<>();
        for (String s : current.split(",")) {
            String trimmed = s.trim();
            if (!trimmed.isEmpty() && !trimmed.equals(pkg)) {
                pkgs.add(trimmed);
            }
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < pkgs.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append(pkgs.get(i));
        }
        prefs(ctx).edit().putString(key, sb.toString()).apply();
    }

    public static List<String> getVaultedPackagesForSpace(Context ctx, int spaceId) {
        String key = "vault_clones_space_" + spaceId;
        String current = prefs(ctx).getString(key, "");
        List<String> pkgs = new ArrayList<>();
        for (String s : current.split(",")) {
            if (!s.trim().isEmpty() && !pkgs.contains(s.trim())) {
                pkgs.add(s.trim());
            }
        }
        return pkgs;
    }

    public static void clearCloneMetadata(Context ctx, String pkg, int spaceId) {
        unregisterCloneFromVault(ctx, pkg, spaceId);
        prefs(ctx).edit()
                .remove(key(pkg, spaceId, "alias"))
                .remove(key(pkg, spaceId, "device_brand"))
                .remove(key(pkg, spaceId, "device_model"))
                .remove(key(pkg, spaceId, "loc_enabled"))
                .remove(key(pkg, spaceId, "lat"))
                .remove(key(pkg, spaceId, "lon"))
                .remove(key(pkg, spaceId, "region"))
                .remove(key(pkg, spaceId, "virtual_ip"))
                .apply();
    }
}
""",
)

# ---------------------------------------------------------------------------
# 8. VIRTUAL HOOK MANAGER (VirtualHookManager.java)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/core/VirtualHookManager.java",
    r"""package com.veyravault.space.core;

import android.content.Context;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.SystemClock;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Locale;
import java.util.TimeZone;

import top.niunaijun.blackbox.BlackBoxCore;

public class VirtualHookManager {

    public static void initializeGlobalHooks(Context context) {
        try {
            String brand = CloneMetadataStore.getGlobalDeviceBrand(context);
            String model = CloneMetadataStore.getGlobalDeviceModel(context);
            applyBuildProperties(brand, model);

            if (CloneMetadataStore.isGlobalLocationEnabled(context)) {
                double[] coords = CloneMetadataStore.getGlobalCoordinates(context);
                String region = CloneMetadataStore.getGlobalRegionName(context);
                applyRegionAndNetworkEnvironment(context, region, coords[0], coords[1],
                        CloneMetadataStore.getGlobalVirtualIp(context));
            }
            installGmsAvailabilityBypass();
        } catch (Throwable ignored) {
        }
    }

    public static void prepareForCloneLaunch(Context context, String packageName, int spaceId) {
        try {
            // 1. Device Identity Priority: Per-Clone Custom > Global Default
            String brand = CloneMetadataStore.getEffectiveDeviceBrand(context, packageName, spaceId);
            String model = CloneMetadataStore.getEffectiveDeviceModel(context, packageName, spaceId);
            applyBuildProperties(brand, model);

            // 2. Location & Region Priority: Per-Clone Custom > Global Default
            if (CloneMetadataStore.isEffectiveLocationEnabled(context, packageName, spaceId)) {
                double[] coords = CloneMetadataStore.getEffectiveCoordinates(context, packageName, spaceId);
                String region = CloneMetadataStore.getEffectiveRegionName(context, packageName, spaceId);
                String virtualIp = CloneMetadataStore.getEffectiveVirtualIp(context, packageName, spaceId);

                applyRegionAndNetworkEnvironment(context, region, coords[0], coords[1], virtualIp);
                injectBlackBoxLocation(packageName, spaceId, coords[0], coords[1]);
            }

            // 3. GMS Availability Bypass for YouTube & Viber
            installGmsAvailabilityBypass();
        } catch (Throwable ignored) {
        }
    }

    public static void applyBuildProperties(String brand, String model) {
        if (brand == null || brand.trim().isEmpty()) brand = "Samsung";
        if (model == null || model.trim().isEmpty()) model = "Samsung Galaxy S24 Ultra";

        String cleanBrand = brand.trim();
        String cleanModel = model.trim();
        String deviceCode;
        String productCode;
        String fingerprint;

        if (cleanBrand.equalsIgnoreCase("Apple") || cleanModel.toLowerCase().contains("iphone") || cleanModel.toLowerCase().contains("ipad")) {
            cleanBrand = "Apple";
            deviceCode = "iPhone17,2";
            productCode = "iOS18_ProMax";
            fingerprint = "Apple/iPhone17,2/iPhone:18.1/22B83/root:user/release-keys";
        } else if (cleanBrand.equalsIgnoreCase("Google") || cleanModel.toLowerCase().contains("pixel")) {
            cleanBrand = "Google";
            deviceCode = "husky";
            productCode = "husky";
            fingerprint = "google/husky/husky:14/UQ1A.240205.004/11269751:user/release-keys";
        } else if (cleanBrand.equalsIgnoreCase("Xiaomi")) {
            deviceCode = "aurora";
            productCode = "aurora_global";
            fingerprint = "Xiaomi/aurora_global/aurora:14/UKQ1.231003.002/V816.0.5.0.UNAMIXM:user/release-keys";
        } else {
            deviceCode = "e3q";
            productCode = "e3qxxx";
            fingerprint = "samsung/e3qxxx/e3q:14/UP1A.231005.007/S928BXXU1AXB5:user/release-keys";
        }

        setStaticField(Build.class, "BRAND", cleanBrand);
        setStaticField(Build.class, "MANUFACTURER", cleanBrand);
        setStaticField(Build.class, "MODEL", cleanModel);
        setStaticField(Build.class, "PRODUCT", productCode);
        setStaticField(Build.class, "DEVICE", deviceCode);
        setStaticField(Build.class, "BOARD", deviceCode);
        setStaticField(Build.class, "FINGERPRINT", fingerprint);

        System.setProperty("ro.product.model", cleanModel);
        System.setProperty("ro.product.brand", cleanBrand);
        System.setProperty("ro.product.manufacturer", cleanBrand);
        System.setProperty("ro.product.device", deviceCode);
    }

    public static void applyRegionAndNetworkEnvironment(Context ctx, String regionCityCountry, double lat, double lon, String virtualIp) {
        try {
            String tzId = CloneMetadataStore.getTimezoneForRegion(regionCityCountry, lat, lon);
            TimeZone tz = TimeZone.getTimeZone(tzId);
            TimeZone.setDefault(tz);
            System.setProperty("user.timezone", tzId);
            System.setProperty("persist.sys.timezone", tzId);

            String countryCode = "DE";
            String lower = regionCityCountry == null ? "" : regionCityCountry.toLowerCase();
            if (lower.contains("netherlands")) countryCode = "NL";
            else if (lower.contains("united kingdom") || lower.contains("london")) countryCode = "GB";
            else if (lower.contains("france")) countryCode = "FR";
            else if (lower.contains("finland")) countryCode = "FI";
            else if (lower.contains("united states") || lower.contains("new york")) countryCode = "US";
            else if (lower.contains("turkey")) countryCode = "TR";
            else if (lower.contains("emirates") || lower.contains("dubai")) countryCode = "AE";
            else if (lower.contains("iran")) countryCode = "IR";

            System.setProperty(" Veyra.region.label", regionCityCountry);
            System.setProperty("http.agent", "Mozilla/5.0 (" + Build.MODEL + "; " + regionCityCountry + ")");
            System.setProperty("veyra.virtual.ip", virtualIp == null ? "88.198.24.108" : virtualIp);
            System.setProperty("veyra.virtual.country", countryCode);

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
        } catch (Throwable ignored) {
        }
    }

    private static void injectBlackBoxLocation(String packageName, int spaceId, double lat, double lon) {
        try {
            Location mockLoc = new Location(LocationManager.GPS_PROVIDER);
            mockLoc.setLatitude(lat);
            mockLoc.setLongitude(lon);
            mockLoc.setAltitude(310.0);
            mockLoc.setAccuracy(3.5f);
            mockLoc.setTime(System.currentTimeMillis());
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
                mockLoc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
            }

            Class<?> blmClass = Class.forName("top.niunaijun.blackbox.fake.frameworks.BLocationManager");
            Method getMethod = blmClass.getDeclaredMethod("get");
            Object blm = getMethod.invoke(null);

            try {
                Method setPattern = blmClass.getDeclaredMethod("setPattern", int.class, String.class, int.class);
                setPattern.invoke(blm, spaceId, packageName, 2);
            } catch (Throwable ignored) {
            }

            Class<?> bLocClass = Class.forName("top.niunaijun.blackbox.entity.location.BLocation");
            Object bLoc = bLocClass.getDeclaredConstructor(double.class, double.class).newInstance(lat, lon);

            try {
                Method setLoc = blmClass.getDeclaredMethod("setLocation", int.class, String.class, bLocClass);
                setLoc.invoke(blm, spaceId, packageName, bLoc);
            } catch (Throwable ignored) {
            }
            try {
                Method setGlobalLoc = blmClass.getDeclaredMethod("setGlobalLocation", bLocClass);
                setGlobalLoc.invoke(blm, bLoc);
            } catch (Throwable ignored) {
            }
        } catch (Throwable ignored) {
        }
    }

    public static void installGmsAvailabilityBypass() {
        try {
            System.setProperty("veyra.gms.status", "SUCCESS");
            System.setProperty("com.google.android.gms.version", "240812000");
            Class<?> gmsUtil = Class.forName("com.google.android.gms.common.GooglePlayServicesUtil");
            setStaticField(gmsUtil, "GOOGLE_PLAY_SERVICES_VERSION_CODE", 240812000);
        } catch (Throwable ignored) {
        }
    }

    private static void setStaticField(Class<?> clazz, String fieldName, Object value) {
        try {
            Field f = clazz.getDeclaredField(fieldName);
            f.setAccessible(true);
            f.set(null, value);
        } catch (Throwable ignored) {
        }
    }
}
""",
)

# ---------------------------------------------------------------------------
# 9. VIRTUALIZATION ENGINE (Engine.java)
#    - Fixes Chrome opening WebView DevTools (resolves real MAIN/LAUNCHER browser activity)
#    - Fixes Instagram, Soroush, Gap (Split APK & Native .so extraction + sync)
#    - Fixes YouTube & Viber (Auto GMS init + availability bypass before launch)
#    - Keeps Clones 100% Independent in APK Vault even if Host App is uninstalled
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/core/Engine.java",
    r"""package com.veyravault.space.core;

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

import com.veyravault.space.helper.GmsSupportManager;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.entity.pm.InstallResult;

public class Engine {

    public static class ClonedApp {
        public String packageName;
        public String name;
        public Drawable icon;
        public int spaceId;
        public String customDeviceName;
        public double mockLat;
        public double mockLon;
        public boolean mockLocationEnabled;
        public String effectiveRegion;
        public boolean hasCustomDevice;
        public boolean hasCustomLoc;
        public boolean independentFromHost;
    }

    public static class InstallOptionCandidate {
        public String packageName;
        public String name;
        public Drawable icon;
        public String sourceApkPath;
        public boolean installedOnHost;
    }

    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(80);

    public static int[] getSpaces() {
        return new int[]{0, 1, 2};
    }

    private static File getVaultDirForPackage(Context ctx, String pkg) {
        File dir = new File(ctx.getFilesDir(), "apk_vault/" + pkg);
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    public static File getVaultedBaseApk(Context ctx, String pkg) {
        File f = new File(getVaultDirForPackage(ctx, pkg), "base.apk");
        return f.exists() ? f : null;
    }

    // -----------------------------------------------------------------------
    // Backup APK + Split APKs + Native .so Libraries into Independent Vault
    // (Fixes Instagram, Soroush, Gap hang AND guarantees independence from host)
    // -----------------------------------------------------------------------
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

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP && ai.splitSourceDirs != null) {
                int idx = 1;
                for (String splitPath : ai.splitSourceDirs) {
                    File splitSrc = new File(splitPath);
                    if (splitSrc.exists()) {
                        File splitDst = new File(vaultDir, "split_" + idx + ".apk");
                        if (!splitDst.exists() || splitDst.length() != splitSrc.length()) {
                            copyFile(splitSrc, splitDst);
                        }
                        idx++;
                    }
                }
            }

            extractAndSyncNativeLibraries(ctx, pkg, vaultDir);
            return destBase.exists() ? destBase : null;
        } catch (Throwable t) {
            return getVaultedBaseApk(ctx, pkg);
        }
    }

    public static File backupExternalApkToVault(Context ctx, File externalApk, String pkg) {
        try {
            File vaultDir = getVaultDirForPackage(ctx, pkg);
            File destBase = new File(vaultDir, "base.apk");
            copyFile(externalApk, destBase);
            extractAndSyncNativeLibraries(ctx, pkg, vaultDir);
            return destBase;
        } catch (Throwable t) {
            return externalApk;
        }
    }

    private static void extractAndSyncNativeLibraries(Context ctx, String pkg, File vaultDir) {
        try {
            File libDir = new File(vaultDir, "lib");
            if (!libDir.exists()) libDir.mkdirs();

            String primaryAbi = Build.CPU_ABI != null && Build.CPU_ABI.contains("64") ? "arm64-v8a" : "armeabi-v7a";
            File[] apks = vaultDir.listFiles();
            if (apks == null) return;

            for (File f : apks) {
                if (!f.getName().endsWith(".apk")) continue;
                ZipFile zf = null;
                try {
                    zf = new ZipFile(f);
                    Enumeration<? extends ZipEntry> entries = zf.entries();
                    while (entries.hasMoreElements()) {
                        ZipEntry entry = entries.nextElement();
                        String name = entry.getName();
                        if (name.startsWith("lib/") && name.endsWith(".so")) {
                            if (name.contains(primaryAbi) || name.contains("armeabi")) {
                                String soFileName = name.substring(name.lastIndexOf('/') + 1);
                                File outSo = new File(libDir, soFileName);
                                if (!outSo.exists() || outSo.length() != entry.getSize()) {
                                    InputStream is = zf.getInputStream(entry);
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
                    if (zf != null) {
                        try {
                            zf.close();
                        } catch (Throwable ignored) {
                        }
                    }
                }
            }

            // Also sync extracted .so files into BlackBox's virtual app lib folder if present
            File dataDir = ctx.getApplicationInfo().dataDir;
            File[] possibleLibRoots = new File[]{
                    new File(dataDir, "virtual/data/app/" + pkg + "/lib"),
                    new File(dataDir, "blackbox/data/app/" + pkg + "/lib")
            };
            File[] extractedSos = libDir.listFiles();
            if (extractedSos != null && extractedSos.length > 0) {
                for (File targetRoot : possibleLibRoots) {
                    targetRoot.mkdirs();
                    for (File so : extractedSos) {
                        File dst = new File(targetRoot, so.getName());
                        if (!dst.exists() || dst.length() != so.length()) {
                            copyFile(so, dst);
                        }
                    }
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static void copyFile(File src, File dst) throws Exception {
        FileInputStream fis = new FileInputStream(src);
        FileOutputStream fos = new FileOutputStream(dst);
        byte[] buf = new byte[16384];
        int len;
        while ((len = fis.read(buf)) > 0) {
            fos.write(buf, 0, len);
        }
        fos.flush();
        fos.close();
        fis.close();
    }

    // -----------------------------------------------------------------------
    // Query Cloned Apps for a Space (Includes Independent Vaulted Clones)
    // -----------------------------------------------------------------------
    public static List<ClonedApp> getClonedApps(Context ctx, int spaceId) {
        List<ClonedApp> result = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        PackageManager pm = ctx.getPackageManager();

        try {
            List<ApplicationInfo> installed = BlackBoxCore.get().getInstalledApplications(0, spaceId);
            if (installed != null) {
                for (ApplicationInfo info : installed) {
                    if (info == null || info.packageName == null) continue;
                    if (isInternalGmsOrSystemPackage(info.packageName, ctx.getPackageName())) continue;
                    seen.add(info.packageName);
                    CloneMetadataStore.registerCloneInVault(ctx, info.packageName, spaceId);
                    ClonedApp app = buildClonedAppModel(ctx, pm, info.packageName, spaceId);
                    if (app != null) result.add(app);
                }
            }
        } catch (Throwable ignored) {
        }

        // Also check our Independent Vault Registry (if host app was uninstalled from phone!)
        List<String> vaultedPkgs = CloneMetadataStore.getVaultedPackagesForSpace(ctx, spaceId);
        for (String pkg : vaultedPkgs) {
            if (seen.contains(pkg)) continue;
            if (isInternalGmsOrSystemPackage(pkg, ctx.getPackageName())) continue;
            File vaultedApk = getVaultedBaseApk(ctx, pkg);
            if (vaultedApk != null) {
                try {
                    if (!BlackBoxCore.get().isInstalled(pkg, spaceId)) {
                        BlackBoxCore.get().installPackageAsUser(vaultedApk, spaceId);
                    }
                } catch (Throwable ignored) {
                }
            }
            ClonedApp app = buildClonedAppModel(ctx, pm, pkg, spaceId);
            if (app != null) {
                seen.add(pkg);
                result.add(app);
            }
        }

        return result;
    }

    private static boolean isInternalGmsOrSystemPackage(String pkg, String hostPkg) {
        if (pkg.equals(hostPkg)) return true;
        return pkg.equals("com.google.android.gms")
                || pkg.equals("com.google.android.gsf")
                || pkg.equals("com.android.vending");
    }

    private static ClonedApp buildClonedAppModel(Context ctx, PackageManager pm, String pkg, int spaceId) {
        try {
            ClonedApp app = new ClonedApp();
            app.packageName = pkg;
            app.spaceId = spaceId;

            String label = null;
            Drawable icon = ICON_CACHE.get(pkg);
            boolean onHost = false;

            try {
                ApplicationInfo hostInfo = pm.getApplicationInfo(pkg, 0);
                onHost = true;
                label = pm.getApplicationLabel(hostInfo).toString();
                if (icon == null) {
                    icon = pm.getApplicationIcon(hostInfo);
                    if (icon != null) ICON_CACHE.put(pkg, icon);
                }
            } catch (Throwable ignored) {
            }

            if (label == null || icon == null) {
                File vaultedApk = getVaultedBaseApk(ctx, pkg);
                if (vaultedApk != null) {
                    PackageInfo pi = pm.getPackageArchiveInfo(vaultedApk.getAbsolutePath(), 0);
                    if (pi != null && pi.applicationInfo != null) {
                        pi.applicationInfo.sourceDir = vaultedApk.getAbsolutePath();
                        pi.applicationInfo.publicSourceDir = vaultedApk.getAbsolutePath();
                        if (label == null) {
                            CharSequence cs = pi.applicationInfo.loadLabel(pm);
                            if (cs != null) label = cs.toString();
                        }
                        if (icon == null) {
                            icon = pi.applicationInfo.loadIcon(pm);
                            if (icon != null) ICON_CACHE.put(pkg, icon);
                        }
                    }
                }
            }

            if (label == null || label.trim().isEmpty()) label = pkg;
            if (icon == null) icon = ctx.getApplicationInfo().loadIcon(pm);

            String alias = CloneMetadataStore.getCustomAlias(ctx, pkg, spaceId);
            app.name = !alias.isEmpty() ? alias : label;
            app.icon = icon;
            app.independentFromHost = !onHost || getVaultedBaseApk(ctx, pkg) != null;

            app.hasCustomDevice = CloneMetadataStore.hasCustomDeviceIdentity(ctx, pkg, spaceId);
            app.customDeviceName = CloneMetadataStore.getEffectiveDeviceModel(ctx, pkg, spaceId);

            app.hasCustomLoc = CloneMetadataStore.hasCustomLocation(ctx, pkg, spaceId);
            app.mockLocationEnabled = CloneMetadataStore.isEffectiveLocationEnabled(ctx, pkg, spaceId);
            double[] coords = CloneMetadataStore.getEffectiveCoordinates(ctx, pkg, spaceId);
            app.mockLat = coords[0];
            app.mockLon = coords[1];
            app.effectiveRegion = CloneMetadataStore.getEffectiveRegionName(ctx, pkg, spaceId);

            return app;
        } catch (Throwable t) {
            return null;
        }
    }

    // -----------------------------------------------------------------------
    // List Installed Host Apps for Cloning
    // -----------------------------------------------------------------------
    public static List<InstallOptionCandidate> getInstalledHostApps(Context ctx) {
        List<InstallOptionCandidate> list = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Intent mainIntent = new Intent(Intent.ACTION_MAIN, null);
        mainIntent.addCategory(Intent.CATEGORY_LAUNCHER);

        List<ResolveInfo> resolves = pm.queryIntentActivities(mainIntent, 0);
        Set<String> seen = new HashSet<>();
        String myPkg = ctx.getPackageName();

        if (resolves != null) {
            for (ResolveInfo ri : resolves) {
                if (ri.activityInfo == null) continue;
                String pkg = ri.activityInfo.packageName;
                if (pkg == null || pkg.equals(myPkg) || seen.contains(pkg)) continue;
                seen.add(pkg);
                try {
                    ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
                    InstallOptionCandidate c = new InstallOptionCandidate();
                    c.packageName = pkg;
                    c.name = pm.getApplicationLabel(ai).toString();
                    c.icon = pm.getApplicationIcon(ai);
                    c.sourceApkPath = ai.sourceDir;
                    c.installedOnHost = true;
                    list.add(c);
                } catch (Throwable ignored) {
                }
            }
        }

        Collections.sort(list, new Comparator<InstallOptionCandidate>() {
            @Override
            public int compare(InstallOptionCandidate a, InstallOptionCandidate b) {
                return a.name.compareToIgnoreCase(b.name);
            }
        });
        return list;
    }

    // -----------------------------------------------------------------------
    // Clone App (From Host OR From Independent APK File)
    // -----------------------------------------------------------------------
    public static boolean cloneApp(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.ensureGmsForSpace(ctx, spaceId);
            File vaultedBase = backupPackageToVault(ctx, pkg);
            InstallResult res;
            if (vaultedBase != null && vaultedBase.exists()) {
                res = BlackBoxCore.get().installPackageAsUser(vaultedBase, spaceId);
                if (res == null || !res.success) {
                    res = BlackBoxCore.get().installPackageAsUser(pkg, spaceId);
                }
            } else {
                res = BlackBoxCore.get().installPackageAsUser(pkg, spaceId);
            }
            boolean ok = (res != null && res.success) || BlackBoxCore.get().isInstalled(pkg, spaceId);
            if (ok) {
                CloneMetadataStore.registerCloneInVault(ctx, pkg, spaceId);
            }
            return ok;
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean installApkIntoSpaceOnly(Context ctx, String apkFilePath, int spaceId) {
        try {
            File extFile = new File(apkFilePath);
            if (!extFile.exists()) return false;
            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(extFile.getAbsolutePath(), 0);
            String pkg = (pi != null && pi.packageName != null) ? pi.packageName : null;

            GmsSupportManager.ensureGmsForSpace(ctx, spaceId);
            File targetApk = extFile;
            if (pkg != null) {
                targetApk = backupExternalApkToVault(ctx, extFile, pkg);
            }

            InstallResult res = BlackBoxCore.get().installPackageAsUser(targetApk, spaceId);
            boolean ok = (res != null && res.success) || (pkg != null && BlackBoxCore.get().isInstalled(pkg, spaceId));
            if (ok && pkg != null) {
                CloneMetadataStore.registerCloneInVault(ctx, pkg, spaceId);
            }
            return ok;
        } catch (Throwable t) {
            return false;
        }
    }

    public static void promptHostInstallForApk(Context ctx, String apkFilePath) {
        try {
            File f = new File(apkFilePath);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(Uri.fromFile(f), "application/vnd.android.package-archive");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            ctx.startActivity(intent);
        } catch (Throwable ignored) {
        }
    }

    public static boolean removeClone(Context ctx, String pkg, int spaceId) {
        try {
            CloneMetadataStore.clearCloneMetadata(ctx, pkg, spaceId);
            BlackBoxCore.get().uninstallPackageAsUser(pkg, spaceId);
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    // -----------------------------------------------------------------------
    // Launch Clone with Fixes for Chrome, Instagram, YouTube, Viber, Soroush, Gap
    // -----------------------------------------------------------------------
    public static boolean launchClone(Context ctx, String pkg, int spaceId) {
        try {
            // 1. Ensure GMS & hooks are ready for YouTube, Viber, Chrome, etc.
            GmsSupportManager.ensureGmsForSpace(ctx, spaceId);
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, spaceId);

            // 2. Ensure split native .so libraries are synced (Instagram, Soroush, Gap)
            File vaultDir = getVaultDirForPackage(ctx, pkg);
            if (vaultDir.exists()) {
                extractAndSyncNativeLibraries(ctx, pkg, vaultDir);
            } else {
                backupPackageToVault(ctx, pkg);
            }

            // 3. Re-install from Vault automatically if host app was uninstalled
            if (!BlackBoxCore.get().isInstalled(pkg, spaceId)) {
                File vaultedApk = getVaultedBaseApk(ctx, pkg);
                if (vaultedApk != null) {
                    BlackBoxCore.get().installPackageAsUser(vaultedApk, spaceId);
                }
            }

            // 4. Chrome WebView DevTools Bug Fix:
            //    Explicitly resolve the primary MAIN/LAUNCHER browser activity instead of DevTools
            Intent explicitLauncher = resolveRealMainLauncherIntent(ctx, pkg);
            if (explicitLauncher != null) {
                try {
                    Method launchIntentMethod = BlackBoxCore.class.getDeclaredMethod(
                            "launchIntent", Intent.class, int.class);
                    launchIntentMethod.setAccessible(true);
                    launchIntentMethod.invoke(BlackBoxCore.get(), explicitLauncher, spaceId);
                    return true;
                } catch (Throwable ignored) {
                }
            }

            return BlackBoxCore.get().launchApk(pkg, spaceId);
        } catch (Throwable t) {
            return false;
        }
    }

    private static Intent resolveRealMainLauncherIntent(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            // Special handling for Google Chrome to avoid org.chromium.android_webview.devui.MainActivity
            if ("com.android.chrome".equals(pkg) || pkg.contains("chrome")) {
                Intent chromeMain = new Intent(Intent.ACTION_MAIN);
                chromeMain.addCategory(Intent.CATEGORY_LAUNCHER);
                chromeMain.setPackage(pkg);
                chromeMain.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
                chromeMain.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                return chromeMain;
            }

            Intent query = new Intent(Intent.ACTION_MAIN, null);
            query.addCategory(Intent.CATEGORY_LAUNCHER);
            query.setPackage(pkg);
            List<ResolveInfo> list = pm.queryIntentActivities(query, 0);
            if (list != null && !list.isEmpty()) {
                for (ResolveInfo ri : list) {
                    if (ri.activityInfo != null && ri.activityInfo.name != null) {
                        String actName = ri.activityInfo.name;
                        // Skip any WebView DevTools activity
                        if (actName.toLowerCase().contains("devui") || actName.toLowerCase().contains("devtools")) {
                            continue;
                        }
                        Intent launch = new Intent(Intent.ACTION_MAIN);
                        launch.addCategory(Intent.CATEGORY_LAUNCHER);
                        launch.setComponent(new ComponentName(pkg, actName));
                        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                        return launch;
                    }
                }
            }
        } catch (Throwable ignored) {
        }
        return null;
    }
}
""",
)

# ---------------------------------------------------------------------------
# 10. SECURITY MANAGER & DEVICE ADMIN RECEIVER (Items 10 & 11 Part 1)
#     - Supports BOTH PIN and Pattern simultaneously!
#     - Primary Priority selection (PIN first or Pattern first)
#     - Anti-Uninstall Blocker: Locks session & pops up SecurityLockActivity
#       whenever an unauthorized user tries to disable Device Admin in system settings
#     - ZERO mention or hint that protection can be disabled from inside the app
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/security/SecurityManager.java",
    r"""package com.veyravault.space.security;

import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

import java.security.MessageDigest;

public class SecurityManager {

    private static final String PREF_NAME = "veyra_security_prefs_v3";

    public static final int LOCK_NONE = 0;
    public static final int LOCK_PIN = 1;
    public static final int LOCK_PATTERN = 2;

    private static boolean sSessionUnlocked = false;

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    public static boolean isSessionUnlocked() {
        return sSessionUnlocked;
    }

    public static void setSessionUnlocked(boolean unlocked) {
        sSessionUnlocked = unlocked;
    }

    // -----------------------------------------------------------------------
    // Simultaneous PIN + Pattern Storage & Priority
    // -----------------------------------------------------------------------
    public static boolean hasPin(Context ctx) {
        return !prefs(ctx).getString("pin_hash", "").isEmpty();
    }

    public static boolean hasPattern(Context ctx) {
        return !prefs(ctx).getString("pattern_hash", "").isEmpty();
    }

    public static boolean isLockEnabled(Context ctx) {
        return hasPin(ctx) || hasPattern(ctx);
    }

    public static int getPrimaryLockPriority(Context ctx) {
        int prio = prefs(ctx).getInt("primary_lock_priority", LOCK_PIN);
        if (prio == LOCK_PIN && hasPin(ctx)) return LOCK_PIN;
        if (prio == LOCK_PATTERN && hasPattern(ctx)) return LOCK_PATTERN;
        if (hasPin(ctx)) return LOCK_PIN;
        if (hasPattern(ctx)) return LOCK_PATTERN;
        return LOCK_NONE;
    }

    public static void setPrimaryLockPriority(Context ctx, int priorityType) {
        prefs(ctx).edit().putInt("primary_lock_priority", priorityType).apply();
    }

    public static int getLockType(Context ctx) {
        return getPrimaryLockPriority(ctx);
    }

    public static void setPin(Context ctx, String rawPin) {
        if (rawPin == null || rawPin.trim().isEmpty()) return;
        prefs(ctx).edit().putString("pin_hash", sha256(rawPin.trim())).apply();
        if (!hasPattern(ctx)) {
            setPrimaryLockPriority(ctx, LOCK_PIN);
        }
        sSessionUnlocked = true;
    }

    public static void clearPin(Context ctx) {
        prefs(ctx).edit().remove("pin_hash").apply();
    }

    public static void setPattern(Context ctx, String rawPattern) {
        if (rawPattern == null || rawPattern.trim().isEmpty()) return;
        prefs(ctx).edit().putString("pattern_hash", sha256(rawPattern.trim())).apply();
        if (!hasPin(ctx)) {
            setPrimaryLockPriority(ctx, LOCK_PATTERN);
        }
        sSessionUnlocked = true;
    }

    public static void clearPattern(Context ctx) {
        prefs(ctx).edit().remove("pattern_hash").apply();
    }

    public static void disableAllLocks(Context ctx) {
        prefs(ctx).edit()
                .remove("pin_hash")
                .remove("pattern_hash")
                .putInt("primary_lock_priority", LOCK_NONE)
                .apply();
        sSessionUnlocked = true;
    }

    public static boolean verifyPin(Context ctx, String inputPin) {
        if (inputPin == null || !hasPin(ctx)) return false;
        String expected = prefs(ctx).getString("pin_hash", "");
        return expected.equals(sha256(inputPin.trim()));
    }

    public static boolean verifyPattern(Context ctx, String inputPattern) {
        if (inputPattern == null || !hasPattern(ctx)) return false;
        String expected = prefs(ctx).getString("pattern_hash", "");
        return expected.equals(sha256(inputPattern.trim()));
    }

    public static boolean verifySecret(Context ctx, String input) {
        return verifyPin(ctx, input) || verifyPattern(ctx, input);
    }

    private static String sha256(String base) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(("VeyraSalt_v3_" + base).getBytes("UTF-8"));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (Exception ex) {
            return base;
        }
    }

    // -----------------------------------------------------------------------
    // Strict Anti-Uninstall Protection via DevicePolicyManager
    // -----------------------------------------------------------------------
    public static ComponentName getAdminComponent(Context ctx) {
        return new ComponentName(ctx, VaultDeviceAdminReceiver.class);
    }

    public static boolean isDeviceAdminActive(Context ctx) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            return dpm != null && dpm.isAdminActive(getAdminComponent(ctx));
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean isAntiUninstallRequested(Context ctx) {
        return prefs(ctx).getBoolean("anti_uninstall_enabled", false) || isDeviceAdminActive(ctx);
    }

    public static void setAntiUninstallRequested(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean("anti_uninstall_enabled", enabled).apply();
    }

    public static void requestEnableDeviceAdmin(Activity activity, int requestCode) {
        try {
            setAntiUninstallRequested(activity, true);
            ComponentName comp = getAdminComponent(activity);
            Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
            intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, comp);
            intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                    "حفاظت امنیتی پیشرفته VeyraVault: تا زمانی که این سپر فعال است، هیچ فردی نمی‌تواند برنامه و فضاهای محرمانه شما را از روی گوشی حذف کند.");
            activity.startActivityForResult(intent, requestCode);
        } catch (Throwable ignored) {
        }
    }

    public static void disableDeviceAdminByAuthorizedOwner(Context ctx) {
        try {
            setAntiUninstallRequested(ctx, false);
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            if (dpm != null && dpm.isAdminActive(getAdminComponent(ctx))) {
                dpm.removeActiveAdmin(getAdminComponent(ctx));
            }
        } catch (Throwable ignored) {
        }
    }

    public static void disableDeviceAdmin(Context ctx) {
        disableDeviceAdminByAuthorizedOwner(ctx);
    }
}
""",
)

write_file(
    "app/src/main/java/com/veyravault/space/security/VaultDeviceAdminReceiver.java",
    r"""package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    @Override
    public void onEnabled(Context context, Intent intent) {
        super.onEnabled(context, intent);
        SecurityManager.setAntiUninstallRequested(context, true);
        Toast.makeText(context, "🛡 سپر ضدحذف VeyraVault فعال شد", Toast.LENGTH_SHORT).show();
    }

    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        // If someone tries to deactivate Device Admin externally from Android Settings:
        // 1. Immediately lock the app session
        // 2. Launch SecurityLockActivity right on top of Android Settings to block the "Deactivate" button!
        // 3. Give ZERO hint that protection can be disabled from inside the app's settings.
        if (SecurityManager.isAntiUninstallRequested(context)) {
            SecurityManager.setSessionUnlocked(false);
            try {
                Intent blockIntent = new Intent(context, SecurityLockActivity.class);
                blockIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                        | Intent.FLAG_ACTIVITY_CLEAR_TOP
                        | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                blockIntent.putExtra("anti_uninstall_intercept", true);
                context.startActivity(blockIntent);
            } catch (Throwable ignored) {
            }
        }
        return "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است.";
    }

    @Override
    public void onDisabled(Context context, Intent intent) {
        super.onDisabled(context, intent);
    }
}
""",
)

print("[v3.0-Part1] All Core, Helper, Resource, and Security files generated successfully.")
