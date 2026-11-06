#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Upgrade Script - Part 1 (Fully Synchronized with Part 2 UI)
"""

import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_MAIN = os.path.join(ROOT, "app", "src", "main")
JAVA_BASE = os.path.join(APP_MAIN, "java", "com", "veyravault", "space")
RES_BASE = os.path.join(APP_MAIN, "res")


def write_file(rel_path, content):
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.lstrip())
    print(f"[v3-part1] Wrote: {rel_path}")


def clean_legacy_sources():
    if os.path.exists(JAVA_BASE):
        shutil.rmtree(JAVA_BASE)
        print("[v3-part1] Cleaned legacy Java directory.")
    layout_dir = os.path.join(RES_BASE, "layout")
    if os.path.exists(layout_dir):
        shutil.rmtree(layout_dir)
        print("[v3-part1] Cleaned legacy layout directory.")


def patch_build_gradle():
    gradle_path = os.path.join(ROOT, "app", "build.gradle")
    if not os.path.exists(gradle_path):
        return
    with open(gradle_path, "r", encoding="utf-8") as f:
        text = f.read()

    text = re.sub(r"versionCode\s+\d+", "versionCode 3", text)
    text = re.sub(r'versionName\s+"[^"]+"', 'versionName "3.0.0"', text)

    if "org.osmdroid:osmdroid-android" not in text:
        text = text.replace(
            "dependencies {",
            "dependencies {\n    implementation 'org.osmdroid:osmdroid-android:6.1.14'",
            1
        )
    with open(gradle_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("[v3-part1] Patched app/build.gradle for v3.0.0")


def create_resources():
    # 0. App Launcher Vector Icon (@drawable/ic_launcher)
    write_file("app/src/main/res/drawable/ic_launcher.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#1565C0"
        android:pathData="M0,0h108v108h-108z"/>
    <path
        android:fillColor="#0D47A1"
        android:pathData="M0,54h108v54h-108z"/>
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M54,20L24,34v22c0,19.5 12.8,37.7 30,43c17.2,-5.3 30,-23.5 30,-43V34L54,20zM54,53.9h22c-1.7,13.6 -10.4,25.9 -22,30.2V54H32V38.9l22,-10.2v25.2z"/>
</vector>
""")

    # 1. Vector Drawables for Bottom Navigation
    write_file("app/src/main/res/drawable/ic_nav_dashboard.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF1565C0"
        android:pathData="M3,13h8V3H3v10zm0,8h8v-6H3v6zm10,0h8V11h-8v10zm0,-18v6h8V3h-8z"/>
</vector>
""")

    write_file("app/src/main/res/drawable/ic_nav_spaces.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF1565C0"
        android:pathData="M4,8h4V4H4v4zm6,12h4v-4h-4v4zm-6,0h4v-4H4v4zm0,-6h4v-4H4v4zm6,0h4v-4h-4v4zm6,-10v4h4V4h-4zm-6,4h4V4h-4v4zm6,6h4v-4h-4v4zm0,6h4v-4h-4v4z"/>
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
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF1565C0"
        android:pathData="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zm1,17h-2v-2h2v2zm2.07,-7.75l-0.9,0.92C13.45,12.9 13,13.5 13,15h-2v-0.5c0,-1.1 0.45,-2.1 1.17,-2.83l1.24,-1.26c0.37,-0.36 0.59,-0.86 0.59,-1.41 0,-1.1 -0.9,-2 -2,-2s-2,0.9 -2,2H8c0,-2.21 1.79,-4 4,-4s4,1.79 4,4c0,0.88 -0.36,1.68 -0.93,2.25z"/>
</vector>
""")

    write_file("app/src/main/res/drawable/ic_nav_settings.xml", """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FF1565C0"
        android:pathData="M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94 0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6 3.6,1.62 3.6,3.6 -1.62,3.6 -3.6,3.6z"/>
</vector>
""")

    # 2. Device Admin XML
    write_file("app/src/main/res/xml/device_admin_policies.xml", """
<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <watch-login />
    </uses-policies>
</device-admin>
""")

    # 3. Styles XML
    write_file("app/src/main/res/values/styles.xml", """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="Theme.AppCompat.Light.NoActionBar">
        <item name="colorPrimary">#1565C0</item>
        <item name="colorPrimaryDark">#0D47A1</item>
        <item name="colorAccent">#00897B</item>
        <item name="android:windowBackground">#F4F7FC</item>
    </style>
</resources>
""")

    # 4. Default Strings (Persian Priority) & English Strings
    write_file("app/src/main/res/values/strings.xml", """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="disguise_name_calculator">ماشین‌حساب</string>
    <string name="disguise_name_calendar">تقویم هوشمند</string>
    <string name="disguise_name_notes">یادداشت‌ها</string>
    <string name="device_admin_label">محافظ امنیتی VeyraVault</string>
    <string name="device_admin_desc">جلوگیری از حذف غیرمجاز برنامه و محافظت از داده‌های خصوصی</string>
    <string name="anti_uninstall_warning">⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است.</string>
</resources>
""")

    write_file("app/src/main/res/values-en/strings.xml", """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="disguise_name_calculator">Calculator</string>
    <string name="disguise_name_calendar">Smart Calendar</string>
    <string name="disguise_name_notes">Quick Notes</string>
    <string name="device_admin_label">VeyraVault Security Guard</string>
    <string name="device_admin_desc">Prevents unauthorized uninstallation and protects private workspace data</string>
    <string name="anti_uninstall_warning">⛔ Uninstallation is not permitted! Removal or deactivation of this application is blocked.</string>
</resources>
""")

    # 5. AndroidManifest.xml with Disguise Aliases & Full v3.0 Activities
    write_file("app/src/main/AndroidManifest.xml", """
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    package="com.veyravault.space">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES"
        tools:ignore="QueryAllPackagesPermission" />

    <application
        android:name=".VeyraApplication"
        android:allowBackup="false"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:theme="@style/AppTheme"
        tools:replace="android:allowBackup,android:label,android:theme,android:icon">

        <!-- Primary Main Activity -->
        <activity
            android:name=".ui.MainActivity"
            android:exported="true"
            android:configChanges="locale|layoutDirection|orientation|screenSize">
        </activity>

        <!-- Default Launcher Alias -->
        <activity-alias
            android:name=".AliasDefault"
            android:enabled="true"
            android:exported="true"
            android:icon="@drawable/ic_launcher"
            android:label="@string/app_name"
            android:targetActivity=".ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <!-- Disguise Alias 1: Calculator -->
        <activity-alias
            android:name=".AliasCalculator"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_dialog_dialer"
            android:label="@string/disguise_name_calculator"
            android:targetActivity=".ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <!-- Disguise Alias 2: Smart Calendar -->
        <activity-alias
            android:name=".AliasCalendar"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_menu_my_calendar"
            android:label="@string/disguise_name_calendar"
            android:targetActivity=".ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <!-- Disguise Alias 3: Notes -->
        <activity-alias
            android:name=".AliasNotes"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_menu_edit"
            android:label="@string/disguise_name_notes"
            android:targetActivity=".ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity android:name=".ui.AddAppActivity" android:exported="false" />
        <activity android:name=".ui.GlobalEnvironmentActivity" android:exported="false" />
        <activity android:name=".ui.SetLocationActivity" android:exported="false" />
        <activity android:name=".ui.SecuritySettingsActivity" android:exported="false" />
        <activity android:name=".ui.SecurityLockActivity" android:exported="false"
            android:launchMode="singleTop" />
        <activity android:name=".ui.GuideActivity" android:exported="false" />
        <activity android:name=".ui.AboutActivity" android:exported="false" />

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
</manifest>
""")


def create_core_and_helper_classes():
    # 1. VeyraApplication.java
    write_file("app/src/main/java/com/veyravault/space/VeyraApplication.java", """
package com.veyravault.space;

import android.app.Application;
import android.content.Context;

import com.veyravault.space.helper.GmsSupportManager;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.helper.LocaleHelper;

import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.configuration.ClientConfiguration;

public class VeyraApplication extends Application {

    @Override
    protected void attachBaseContext(Context base) {
        Context localized = LocaleHelper.onAttach(base);
        super.attachBaseContext(localized);
        try {
            BlackBoxCore.get().doAttachBaseContext(base, new ClientConfiguration() {
                @Override
                public String getHostPackageName() {
                    return base.getPackageName();
                }

                public boolean isHideRoot() {
                    return true;
                }

                public boolean isHideXposed() {
                    return true;
                }
            });
        } catch (Throwable ignored) {
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        try {
            BlackBoxCore.get().doCreate();
            GmsSupportManager.autoInitializeGms(this);
            VirtualHookManager.applyGlobalEnvironmentOnStartup(this);
        } catch (Throwable ignored) {
        }
    }
}
""")

    # 2. JalaliClockUtil.java
    write_file("app/src/main/java/com/veyravault/space/helper/JalaliClockUtil.java", """
package com.veyravault.space.helper;

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

    private static final String[] JALALI_MONTHS_EN = {
        "Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad", "Shahrivar",
        "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand"
    };

    private static final String[] WEEKDAYS_FA = {
        "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"
    };

    public static int[] gregorianToJalali(int gy, int gm, int gd) {
        int[] g_d_m = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
        int gy2 = (gm > 2) ? (gy + 1) : gy;
        int days = 355666 + (365 * gy) + ((gy2 + 3) / 4) - ((gy2 + 99) / 100)
                + ((gy2 + 399) / 400) + gd + g_d_m[gm - 1];
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
            jd = 1 + ((days - 186) % 30);
        }
        return new int[]{jy, jm, jd};
    }

    public static String getTehranTime() {
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
    }

    public static String getTehranJalaliDate(boolean isFa) {
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        Calendar cal = Calendar.getInstance(tz);
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int dow = cal.get(Calendar.DAY_OF_WEEK);
        int[] jalali = gregorianToJalali(gy, gm, gd);
        if (isFa) {
            String dayName = WEEKDAYS_FA[dow - 1];
            String monthName = JALALI_MONTHS_FA[jalali[1] - 1];
            return toPersianDigits(dayName + "، " + jalali[2] + " " + monthName + " " + jalali[0]);
        } else {
            String monthName = JALALI_MONTHS_EN[jalali[1] - 1];
            return String.format(Locale.US, "%02d %s %d (Solar Hijri)", jalali[2], monthName, jalali[0]);
        }
    }

    public static String getNewYorkTime() {
        TimeZone tz = TimeZone.getTimeZone("America/New_York");
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
    }

    public static String getNewYorkGregorianDate() {
        TimeZone tz = TimeZone.getTimeZone("America/New_York");
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
    }

    public static String getNewYorkGregorianDate(boolean isFa) {
        return getNewYorkGregorianDate();
    }

    public static String toPersianDigits(String input) {
        if (input == null) return "";
        char[] persian = {'۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'};
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < input.length(); i++) {
            char ch = input.charAt(i);
            if (ch >= '0' && ch <= '9') {
                sb.append(persian[ch - '0']);
            } else {
                sb.append(ch);
            }
        }
        return sb.toString();
    }
}
""")

    # 3. LocaleHelper.java
    write_file("app/src/main/java/com/veyravault/space/helper/LocaleHelper.java", """
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

    public static Context onAttach(Context context) {
        String lang = getLanguage(context);
        return setLocale(context, lang);
    }

    public static String getLanguage(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getString(KEY_LANG, "fa");
    }

    public static boolean isPersian(Context context) {
        return "fa".equalsIgnoreCase(getLanguage(context));
    }

    public static Context toggleLanguage(Context context) {
        String next = isPersian(context) ? "en" : "fa";
        return setLocale(context, next);
    }

    public static Context setLocale(Context context, String lang) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        sp.edit().putString(KEY_LANG, lang).apply();

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
""")

    # 4. BaseActivity.java
    write_file("app/src/main/java/com/veyravault/space/ui/BaseActivity.java", """
package com.veyravault.space.ui;

import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.veyravault.space.helper.LocaleHelper;
import com.veyravault.space.security.SecurityManager;

public abstract class BaseActivity extends AppCompatActivity {

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.onAttach(newBase));
    }

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        applyDirection();
    }

    protected void applyDirection() {
        boolean fa = LocaleHelper.isPersian(this);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            getWindow().getDecorView().setLayoutDirection(
                    fa ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
    }

    protected boolean isFa() {
        return LocaleHelper.isPersian(this);
    }

    protected boolean isPersian() {
        return LocaleHelper.isPersian(this);
    }

    protected String tr(String faText, String enText) {
        return isFa() ? faText : enText;
    }

    protected void switchLanguageInstant() {
        LocaleHelper.toggleLanguage(this);
        recreate();
    }

    protected void triggerQuickLock() {
        if (SecurityManager.isLockEnabled(this)) {
            SecurityManager.setSessionUnlocked(false);
            Intent lockIntent = new Intent(this, SecurityLockActivity.class);
            startActivity(lockIntent);
        } else {
            Toast.makeText(
                    this,
                    isFa()
                            ? "🔒 ابتدا از بخش «امنیت و قفل دوگانه» یک رمز پین یا الگو ثبت کنید."
                            : "🔒 Please configure a PIN or Pattern in Security Settings first.",
                    Toast.LENGTH_SHORT
            ).show();
            Intent secIntent = new Intent(this, SecuritySettingsActivity.class);
            startActivity(secIntent);
        }
    }
}
""")

    # 5A. GmsSupportManager.java in com.veyravault.space.helper (Used by GlobalEnvironmentActivity & VeyraApplication)
    write_file("app/src/main/java/com/veyravault/space/helper/GmsSupportManager.java", """
package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;

import java.lang.reflect.Method;

import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    private static final String PREFS = "veyra_gms_prefs";
    private static final String KEY_GMS_ENABLED = "gms_enabled";

    public static boolean isGmsEnabled(Context ctx) {
        SharedPreferences sp = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getBoolean(KEY_GMS_ENABLED, true);
    }

    public static void setGmsEnabled(Context ctx, boolean enabled) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putBoolean(KEY_GMS_ENABLED, enabled).apply();
        if (enabled) {
            autoInitializeGms(ctx);
        }
    }

    public static void enableGmsAcrossAllSpaces(Context ctx) {
        setGmsEnabled(ctx, true);
        for (int spaceId = 0; spaceId < 5; spaceId++) {
            ensureGmsForSpace(spaceId);
        }
    }

    public static void autoInitializeGms(Context ctx) {
        if (!isGmsEnabled(ctx)) return;
        for (int spaceId = 0; spaceId < 5; spaceId++) {
            ensureGmsForSpace(spaceId);
        }
    }

    public static boolean ensureGmsForSpace(int spaceId) {
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
                install.invoke(core, spaceId);
            } catch (Throwable ignored) {
            }
            return true;
        } catch (Throwable ignored) {
            return true;
        }
    }
}
""")

    # 5B. GmsSupportManager.java in com.veyravault.space.core (Delegates to helper so both packages work)
    write_file("app/src/main/java/com/veyravault/space/core/GmsSupportManager.java", """
package com.veyravault.space.core;

import android.content.Context;

public class GmsSupportManager {
    public static boolean isGmsEnabled(Context ctx) {
        return com.veyravault.space.helper.GmsSupportManager.isGmsEnabled(ctx);
    }

    public static void setGmsEnabled(Context ctx, boolean enabled) {
        com.veyravault.space.helper.GmsSupportManager.setGmsEnabled(ctx, enabled);
    }

    public static void enableGmsAcrossAllSpaces(Context ctx) {
        com.veyravault.space.helper.GmsSupportManager.enableGmsAcrossAllSpaces(ctx);
    }

    public static void autoInitializeGms(Context ctx) {
        com.veyravault.space.helper.GmsSupportManager.autoInitializeGms(ctx);
    }

    public static boolean ensureGmsForSpace(int spaceId) {
        return com.veyravault.space.helper.GmsSupportManager.ensureGmsForSpace(spaceId);
    }
}
""")

    # 6. AppDisguiseManager.java (String constants matching SecuritySettingsActivity)
    write_file("app/src/main/java/com/veyravault/space/helper/AppDisguiseManager.java", """
package com.veyravault.space.helper;

import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;

public class AppDisguiseManager {
    private static final String PREFS = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode_str";

    public static final String MODE_DEFAULT = "default";
    public static final String MODE_CALCULATOR = "calculator";
    public static final String MODE_CALENDAR = "calendar";
    public static final String MODE_NOTES = "notes";

    private static final String[] MODES = {
        MODE_DEFAULT,
        MODE_CALCULATOR,
        MODE_CALENDAR,
        MODE_NOTES
    };

    private static final String[] ALIASES = {
        "com.veyravault.space.AliasDefault",
        "com.veyravault.space.AliasCalculator",
        "com.veyravault.space.AliasCalendar",
        "com.veyravault.space.AliasNotes"
    };

    public static String getCurrentDisguiseMode(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY_MODE, MODE_DEFAULT);
    }

    public static void applyDisguiseMode(Context ctx, String mode) {
        if (mode == null) mode = MODE_DEFAULT;
        int targetIdx = 0;
        for (int i = 0; i < MODES.length; i++) {
            if (MODES[i].equalsIgnoreCase(mode)) {
                targetIdx = i;
                break;
            }
        }
        SharedPreferences sp = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        sp.edit().putString(KEY_MODE, MODES[targetIdx]).apply();

        PackageManager pm = ctx.getPackageManager();
        for (int i = 0; i < ALIASES.length; i++) {
            ComponentName cn = new ComponentName(ctx.getPackageName(), ALIASES[i]);
            int state = (i == targetIdx)
                    ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED
                    : PackageManager.COMPONENT_ENABLED_STATE_DISABLED;
            try {
                pm.setComponentEnabledSetting(cn, state, PackageManager.DONT_KILL_APP);
            } catch (Throwable ignored) {
            }
        }
    }
}
""")

    # 7. PatternLockView.java
    write_file("app/src/main/java/com/veyravault/space/ui/PatternLockView.java", """
package com.veyravault.space.ui;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

import java.util.ArrayList;
import java.util.List;

public class PatternLockView extends View {

    public interface OnPatternCompleteListener {
        void onPatternComplete(String patternString);
    }

    public interface OnPatternListener {
        void onPatternDetected(String patternValue);
    }

    private final List<Integer> selectedNodes = new ArrayList<>();
    private final Paint nodePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    private float currentX = -1;
    private float currentY = -1;
    private boolean isTracking = false;
    private OnPatternCompleteListener completeListener;
    private OnPatternListener patternListener;

    public PatternLockView(Context context) {
        super(context);
        init();
    }

    public PatternLockView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        nodePaint.setColor(Color.parseColor("#90CAF9"));
        nodePaint.setStyle(Paint.Style.FILL);

        activePaint.setColor(Color.parseColor("#1565C0"));
        activePaint.setStyle(Paint.Style.FILL);

        linePaint.setColor(Color.parseColor("#1E88E5"));
        linePaint.setStrokeWidth(12f);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setOnPatternCompleteListener(OnPatternCompleteListener l) {
        this.completeListener = l;
    }

    public void setOnPatternListener(OnPatternListener l) {
        this.patternListener = l;
    }

    public void clearPattern() {
        selectedNodes.clear();
        isTracking = false;
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

        if (!selectedNodes.isEmpty()) {
            for (int i = 0; i < selectedNodes.size() - 1; i++) {
                int a = selectedNodes.get(i);
                int b = selectedNodes.get(i + 1);
                canvas.drawLine(getNodeX(a), getNodeY(a), getNodeX(b), getNodeY(b), linePaint);
            }
            if (isTracking && currentX >= 0 && currentY >= 0) {
                int last = selectedNodes.get(selectedNodes.size() - 1);
                canvas.drawLine(getNodeX(last), getNodeY(last), currentX, currentY, linePaint);
            }
        }

        for (int i = 0; i < 9; i++) {
            float cx = getNodeX(i);
            float cy = getNodeY(i);
            boolean active = selectedNodes.contains(i);
            canvas.drawCircle(cx, cy, active ? radius * 1.15f : radius * 0.85f,
                    active ? activePaint : nodePaint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float x = event.getX();
        float y = event.getY();
        float hitRadius = Math.min(getWidth(), getHeight()) / 8f;

        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                selectedNodes.clear();
                isTracking = true;
                checkHit(x, y, hitRadius);
                invalidate();
                return true;

            case MotionEvent.ACTION_MOVE:
                currentX = x;
                currentY = y;
                checkHit(x, y, hitRadius);
                invalidate();
                return true;

            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                isTracking = false;
                if (!selectedNodes.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < selectedNodes.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(selectedNodes.get(i) + 1);
                    }
                    String result = sb.toString();
                    if (completeListener != null) {
                        completeListener.onPatternComplete(result);
                    }
                    if (patternListener != null) {
                        patternListener.onPatternDetected(result);
                    }
                }
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y, float hitRadius) {
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
""")

    # 8. CloneMetadataStore.java (All overloads included)
    write_file("app/src/main/java/com/veyravault/space/core/CloneMetadataStore.java", """
package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import android.text.TextUtils;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public class CloneMetadataStore {

    private static final String PREFS = "veyra_clone_metadata_v3";

    public static class DevicePreset {
        public final String title;
        public final String brand;
        public final String model;
        public final String device;

        public DevicePreset(String title, String brand, String model, String device) {
            this.title = title;
            this.brand = brand;
            this.model = model;
            this.device = device;
        }
    }

    public static class RegionPreset {
        public final String labelFa;
        public final String labelEn;
        public final String cityCountry;
        public final double lat;
        public final double lon;
        public final String timeZoneId;
        public final String defaultSimIso;
        public final String sampleVirtualIp;

        public RegionPreset(String labelFa, String labelEn, String cityCountry,
                            double lat, double lon, String timeZoneId,
                            String defaultSimIso, String sampleVirtualIp) {
            this.labelFa = labelFa;
            this.labelEn = labelEn;
            this.cityCountry = cityCountry;
            this.lat = lat;
            this.lon = lon;
            this.timeZoneId = timeZoneId;
            this.defaultSimIso = defaultSimIso;
            this.sampleVirtualIp = sampleVirtualIp;
        }
    }

    public static List<DevicePreset> getDevicePresets() {
        List<DevicePreset> list = new ArrayList<>();
        list.add(new DevicePreset("Apple iPhone 16 Pro Max", "Apple", "iPhone 16 Pro Max", "iPhone17,2"));
        list.add(new DevicePreset("Apple iPhone 15 Pro Max", "Apple", "iPhone 15 Pro Max", "iPhone16,2"));
        list.add(new DevicePreset("Apple iPhone 14 Pro", "Apple", "iPhone 14 Pro", "iPhone15,2"));
        list.add(new DevicePreset("Apple iPad Pro M4", "Apple", "iPad Pro 13-inch (M4)", "iPad16,6"));
        list.add(new DevicePreset("Samsung Galaxy S24 Ultra", "samsung", "SM-S928B", "e3q"));
        list.add(new DevicePreset("Samsung Galaxy S23 Ultra", "samsung", "SM-S918B", "dm3q"));
        list.add(new DevicePreset("Samsung Galaxy A54 5G", "samsung", "SM-A546E", "a54x"));
        list.add(new DevicePreset("Google Pixel 8 Pro", "Google", "Pixel 8 Pro", "husky"));
        list.add(new DevicePreset("Google Pixel 7", "Google", "Pixel 7", "panther"));
        list.add(new DevicePreset("Xiaomi 14 Ultra", "Xiaomi", "24030PN60G", "aurora"));
        list.add(new DevicePreset("Xiaomi Redmi Note 13 Pro", "Xiaomi", "2312DRA50G", "garnet"));
        list.add(new DevicePreset("OnePlus 12", "OnePlus", "CPH2581", "waffle"));
        return list;
    }

    public static List<RegionPreset> getRegionPresets() {
        List<RegionPreset> list = new ArrayList<>();
        list.add(new RegionPreset(
                "آلمان - فالکن‌اشتاین (Falkenstein, Germany)",
                "Falkenstein, Germany (Hetzner DC)",
                "Falkenstein, Germany",
                50.4779, 12.3713, "Europe/Berlin", "de", "88.198.48.10"
        ));
        list.add(new RegionPreset(
                "آلمان - فرانکفورت (Frankfurt, Germany)",
                "Frankfurt, Germany",
                "Frankfurt, Germany",
                50.1109, 8.6821, "Europe/Berlin", "de", "138.201.92.14"
        ));
        list.add(new RegionPreset(
                "آمریکا - نیویورک (New York, United States)",
                "New York, United States",
                "New York, United States",
                40.7128, -74.0060, "America/New_York", "us", "104.244.42.65"
        ));
        list.add(new RegionPreset(
                "هلند - آمستردام (Amsterdam, Netherlands)",
                "Amsterdam, Netherlands",
                "Amsterdam, Netherlands",
                52.3676, 4.9041, "Europe/Amsterdam", "nl", "95.211.198.20"
        ));
        list.add(new RegionPreset(
                "انگلیس - لندن (London, United Kingdom)",
                "London, United Kingdom",
                "London, United Kingdom",
                51.5074, -0.1278, "Europe/London", "gb", "51.140.104.11"
        ));
        list.add(new RegionPreset(
                "فنلاند - هلسینکی (Helsinki, Finland)",
                "Helsinki, Finland",
                "Helsinki, Finland",
                60.1699, 24.9384, "Europe/Helsinki", "fi", "65.108.44.19"
        ));
        list.add(new RegionPreset(
                "ترکیه - استانبول (Istanbul, Turkey)",
                "Istanbul, Turkey",
                "Istanbul, Turkey",
                41.0082, 28.9784, "Europe/Istanbul", "tr", "185.125.33.12"
        ));
        list.add(new RegionPreset(
                "امارات - دبی (Dubai, UAE)",
                "Dubai, United Arab Emirates",
                "Dubai, United Arab Emirates",
                25.2048, 55.2708, "Asia/Dubai", "ae", "94.200.112.40"
        ));
        list.add(new RegionPreset(
                "ایران - تهران (Tehran, Iran)",
                "Tehran, Iran",
                "Tehran, Iran",
                35.6892, 51.3890, "Asia/Tehran", "ir", "5.160.120.10"
        ));
        return list;
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static String key(String pkg, int spaceId, String suffix) {
        return pkg + "_s" + spaceId + "_" + suffix;
    }

    public static void setSpaceCustomName(Context ctx, int spaceId, String name) {
        prefs(ctx).edit().putString("space_custom_name_" + spaceId, name == null ? "" : name.trim()).apply();
    }

    public static String getSpaceCustomName(Context ctx, int spaceId) {
        return prefs(ctx).getString("space_custom_name_" + spaceId, "");
    }

    public static String getSpaceDisplayTitle(Context ctx, int spaceId, boolean isFa) {
        String custom = getSpaceCustomName(ctx, spaceId);
        int num = spaceId + 1;
        if (!TextUtils.isEmpty(custom)) {
            return custom;
        }
        return isFa ? ("فضای " + num) : ("Space " + num);
    }

    public static void registerClonedPackage(Context ctx, String pkg, int spaceId) {
        SharedPreferences sp = prefs(ctx);
        Set<String> existing = new HashSet<>(sp.getStringSet("space_pkgs_" + spaceId, new HashSet<String>()));
        existing.add(pkg);
        sp.edit().putStringSet("space_pkgs_" + spaceId, existing).apply();
    }

    public static void unregisterClonedPackage(Context ctx, String pkg, int spaceId) {
        SharedPreferences sp = prefs(ctx);
        Set<String> existing = new HashSet<>(sp.getStringSet("space_pkgs_" + spaceId, new HashSet<String>()));
        existing.remove(pkg);
        sp.edit().putStringSet("space_pkgs_" + spaceId, existing).apply();
    }

    public static Set<String> getRegisteredPackagesForSpace(Context ctx, int spaceId) {
        return new HashSet<>(prefs(ctx).getStringSet("space_pkgs_" + spaceId, new HashSet<String>()));
    }

    public static void setCustomLabel(Context ctx, String pkg, int spaceId, String label) {
        prefs(ctx).edit().putString(key(pkg, spaceId, "label"), label == null ? "" : label.trim()).apply();
    }

    public static String getCustomLabel(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getString(key(pkg, spaceId, "label"), "");
    }

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model, String device) {
        prefs(ctx).edit()
                .putString("global_brand", brand == null ? "Apple" : brand.trim())
                .putString("global_model", model == null ? "iPhone 16 Pro Max" : model.trim())
                .putString("global_device", device == null ? "iPhone17,2" : device.trim())
                .apply();
    }

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model) {
        String safeDevice = TextUtils.isEmpty(model) ? "e3q" : model.trim().replaceAll("\\\\s+", "_");
        for (DevicePreset dp : getDevicePresets()) {
            if (dp.model.equalsIgnoreCase(model) || dp.title.equalsIgnoreCase(model)) {
                safeDevice = dp.device;
                break;
            }
        }
        setGlobalDeviceIdentity(ctx, brand, model, safeDevice);
    }

    public static String getGlobalBrand(Context ctx) {
        return prefs(ctx).getString("global_brand", "Samsung");
    }

    public static String getGlobalModel(Context ctx) {
        return prefs(ctx).getString("global_model", "SM-S928B (Galaxy S24 Ultra)");
    }

    public static String getGlobalDevice(Context ctx) {
        return prefs(ctx).getString("global_device", "e3q");
    }

    public static void setDeviceIdentity(Context ctx, String pkg, int spaceId, String brand, String model) {
        prefs(ctx).edit()
                .putString(key(pkg, spaceId, "brand"), brand == null ? "" : brand.trim())
                .putString(key(pkg, spaceId, "model"), model == null ? "" : model.trim())
                .apply();
    }

    public static void clearDeviceIdentity(Context ctx, String pkg, int spaceId) {
        prefs(ctx).edit()
                .remove(key(pkg, spaceId, "brand"))
                .remove(key(pkg, spaceId, "model"))
                .apply();
    }

    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int spaceId) {
        return !TextUtils.isEmpty(prefs(ctx).getString(key(pkg, spaceId, "model"), ""));
    }

    public static String getEffectiveBrand(Context ctx, String pkg, int spaceId) {
        String custom = prefs(ctx).getString(key(pkg, spaceId, "brand"), "");
        if (!TextUtils.isEmpty(custom)) return custom;
        return getGlobalBrand(ctx);
    }

    public static String getEffectiveModel(Context ctx, String pkg, int spaceId) {
        String custom = prefs(ctx).getString(key(pkg, spaceId, "model"), "");
        if (!TextUtils.isEmpty(custom)) return custom;
        return getGlobalModel(ctx);
    }

    public static String getDeviceSummary(Context ctx, String pkg, int spaceId) {
        if (hasCustomDeviceIdentity(ctx, pkg, spaceId)) {
            return prefs(ctx).getString(key(pkg, spaceId, "brand"), "") + " "
                    + prefs(ctx).getString(key(pkg, spaceId, "model"), "");
        }
        return "";
    }

    // Both 7-arg and 6-arg overloads for setGlobalRegionLocation
    public static void setGlobalRegionLocation(Context ctx, String cityCountry, double lat, double lon,
                                               String timeZoneId, String simIso, String virtualIp) {
        prefs(ctx).edit()
                .putBoolean("global_loc_enabled", true)
                .putString("global_region_name", cityCountry)
                .putString("global_lat", String.valueOf(lat))
                .putString("global_lon", String.valueOf(lon))
                .putString("global_tz", timeZoneId)
                .putString("global_sim_iso", simIso)
                .putString("global_virtual_ip", virtualIp)
                .apply();
    }

    public static void setGlobalRegionLocation(Context ctx, String cityCountry, double lat, double lon,
                                               String timeZoneId, String virtualIp) {
        String simIso = "de";
        for (RegionPreset rp : getRegionPresets()) {
            if (rp.cityCountry.equalsIgnoreCase(cityCountry)) {
                simIso = rp.defaultSimIso;
                break;
            }
        }
        setGlobalRegionLocation(ctx, cityCountry, lat, lon, timeZoneId, simIso, virtualIp);
    }

    public static boolean isGlobalLocationEnabled(Context ctx) {
        return prefs(ctx).getBoolean("global_loc_enabled", true);
    }

    public static String getGlobalRegionName(Context ctx) {
        return prefs(ctx).getString("global_region_name", "Falkenstein, Germany");
    }

    public static double getGlobalLat(Context ctx) {
        try {
            return Double.parseDouble(prefs(ctx).getString("global_lat", "50.4779"));
        } catch (Exception e) {
            return 50.4779;
        }
    }

    public static double getGlobalLon(Context ctx) {
        try {
            return Double.parseDouble(prefs(ctx).getString("global_lon", "12.3713"));
        } catch (Exception e) {
            return 12.3713;
        }
    }

    public static String getGlobalTimeZone(Context ctx) {
        return prefs(ctx).getString("global_tz", "Europe/Berlin");
    }

    public static String getGlobalSimIso(Context ctx) {
        return prefs(ctx).getString("global_sim_iso", "de");
    }

    public static String getGlobalVirtualIp(Context ctx) {
        return prefs(ctx).getString("global_virtual_ip", "88.198.48.10");
    }

    // Both 4-arg and 3-arg overloads for setGlobalProxy
    public static void setGlobalProxy(Context ctx, boolean enabled, String host, int port) {
        prefs(ctx).edit()
                .putBoolean("global_proxy_enabled", enabled)
                .putString("global_proxy_host", host == null ? "" : host.trim())
                .putInt("global_proxy_port", port)
                .apply();
    }

    public static void setGlobalProxy(Context ctx, String host, int port) {
        boolean enabled = (host != null && !host.trim().isEmpty() && port > 0);
        setGlobalProxy(ctx, enabled, host, port);
    }

    public static boolean isGlobalProxyEnabled(Context ctx) {
        return prefs(ctx).getBoolean("global_proxy_enabled", false);
    }

    public static String getGlobalProxyHost(Context ctx) {
        return prefs(ctx).getString("global_proxy_host", "");
    }

    public static int getGlobalProxyPort(Context ctx) {
        return prefs(ctx).getInt("global_proxy_port", 1080);
    }

    public static void setCustomLocation(Context ctx, String pkg, int spaceId,
                                         double lat, double lon, String regionCityCountry) {
        prefs(ctx).edit()
                .putBoolean(key(pkg, spaceId, "has_loc"), true)
                .putString(key(pkg, spaceId, "lat"), String.valueOf(lat))
                .putString(key(pkg, spaceId, "lon"), String.valueOf(lon))
                .putString(key(pkg, spaceId, "region"),
                        TextUtils.isEmpty(regionCityCountry) ? "Falkenstein, Germany" : regionCityCountry)
                .apply();
    }

    public static void setCustomLocation(Context ctx, String pkg, int spaceId, double lat, double lon) {
        String detectedRegion = guessRegionFromCoordinates(lat, lon);
        setCustomLocation(ctx, pkg, spaceId, lat, lon, detectedRegion);
    }

    public static void clearCustomLocation(Context ctx, String pkg, int spaceId) {
        prefs(ctx).edit()
                .remove(key(pkg, spaceId, "has_loc"))
                .remove(key(pkg, spaceId, "lat"))
                .remove(key(pkg, spaceId, "lon"))
                .remove(key(pkg, spaceId, "region"))
                .apply();
    }

    public static boolean hasCustomLocation(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getBoolean(key(pkg, spaceId, "has_loc"), false);
    }

    public static double[] getCustomLocation(Context ctx, String pkg, int spaceId) {
        if (!hasCustomLocation(ctx, pkg, spaceId)) return null;
        try {
            double lat = Double.parseDouble(prefs(ctx).getString(key(pkg, spaceId, "lat"), "50.4779"));
            double lon = Double.parseDouble(prefs(ctx).getString(key(pkg, spaceId, "lon"), "12.3713"));
            return new double[]{lat, lon};
        } catch (Exception e) {
            return null;
        }
    }

    public static String getCustomRegionName(Context ctx, String pkg, int spaceId) {
        if (!hasCustomLocation(ctx, pkg, spaceId)) return "";
        String r = prefs(ctx).getString(key(pkg, spaceId, "region"), "");
        if (!TextUtils.isEmpty(r)) return r;
        double[] c = getCustomLocation(ctx, pkg, spaceId);
        if (c != null) return guessRegionFromCoordinates(c[0], c[1]);
        return "";
    }

    public static String getEffectiveRegionName(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            return getCustomRegionName(ctx, pkg, spaceId);
        }
        return getGlobalRegionName(ctx);
    }

    public static double[] getEffectiveCoordinates(Context ctx, String pkg, int spaceId) {
        double[] custom = getCustomLocation(ctx, pkg, spaceId);
        if (custom != null) return custom;
        return new double[]{getGlobalLat(ctx), getGlobalLon(ctx)};
    }

    public static String getLocationSummary(Context ctx, String pkg, int spaceId) {
        double[] coords = getCustomLocation(ctx, pkg, spaceId);
        if (coords == null) return "";
        String region = getCustomRegionName(ctx, pkg, spaceId);
        return String.format(Locale.US, "%s (%.4f, %.4f)", region, coords[0], coords[1]);
    }

    public static String guessRegionFromCoordinates(double lat, double lon) {
        List<RegionPreset> presets = getRegionPresets();
        RegionPreset closest = presets.get(0);
        double bestDist = Double.MAX_VALUE;
        for (RegionPreset p : presets) {
            double d = Math.hypot(lat - p.lat, lon - p.lon);
            if (d < bestDist) {
                bestDist = d;
                closest = p;
            }
        }
        if (bestDist < 1.8) {
            return closest.cityCountry;
        }
        if (lat >= 47.0 && lat <= 55.0 && lon >= 6.0 && lon <= 15.0) return "Falkenstein, Germany";
        if (lat >= 24.0 && lat <= 40.0 && lon >= 44.0 && lon <= 63.0) return "Tehran, Iran";
        if (lat >= 25.0 && lat <= 49.0 && lon >= -125.0 && lon <= -66.0) return "New York, United States";
        return String.format(Locale.US, "Region (%.2f, %.2f)", lat, lon);
    }
}
""")

    # 9. VirtualHookManager.java
    write_file("app/src/main/java/com/veyravault/space/core/VirtualHookManager.java", """
package com.veyravault.space.core;

import android.content.Context;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.SystemClock;
import android.text.TextUtils;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Locale;
import java.util.TimeZone;

public class VirtualHookManager {

    public static void applyGlobalEnvironmentOnStartup(Context ctx) {
        String brand = CloneMetadataStore.getGlobalBrand(ctx);
        String model = CloneMetadataStore.getGlobalModel(ctx);
        String device = CloneMetadataStore.getGlobalDevice(ctx);
        applyBuildFields(brand, model, device);

        String tz = CloneMetadataStore.getGlobalTimeZone(ctx);
        String simIso = CloneMetadataStore.getGlobalSimIso(ctx);
        String virtualIp = CloneMetadataStore.getGlobalVirtualIp(ctx);
        applyRegionAndNetworkProperties(ctx, tz, simIso, virtualIp);
        installGmsAvailabilityBypass();
    }

    public static void prepareForCloneLaunch(Context ctx, String pkg, int spaceId) {
        String brand = CloneMetadataStore.getEffectiveBrand(ctx, pkg, spaceId);
        String model = CloneMetadataStore.getEffectiveModel(ctx, pkg, spaceId);
        String device = CloneMetadataStore.hasCustomDeviceIdentity(ctx, pkg, spaceId)
                ? model.replaceAll("\\\\s+", "_")
                : CloneMetadataStore.getGlobalDevice(ctx);
        applyBuildFields(brand, model, device);

        double[] coords = CloneMetadataStore.getEffectiveCoordinates(ctx, pkg, spaceId);
        String regionName = CloneMetadataStore.getEffectiveRegionName(ctx, pkg, spaceId);
        injectVirtualGpsLocation(spaceId, pkg, coords[0], coords[1]);

        String tz = CloneMetadataStore.getGlobalTimeZone(ctx);
        String simIso = CloneMetadataStore.getGlobalSimIso(ctx);
        String virtualIp = CloneMetadataStore.getGlobalVirtualIp(ctx);
        for (CloneMetadataStore.RegionPreset p : CloneMetadataStore.getRegionPresets()) {
            if (p.cityCountry.equalsIgnoreCase(regionName)) {
                tz = p.timeZoneId;
                simIso = p.defaultSimIso;
                virtualIp = p.sampleVirtualIp;
                break;
            }
        }
        applyRegionAndNetworkProperties(ctx, tz, simIso, virtualIp);
        installGmsAvailabilityBypass();
    }

    public static void applyBuildFields(String brand, String model, String device) {
        if (TextUtils.isEmpty(model)) return;
        String safeBrand = TextUtils.isEmpty(brand) ? "Apple" : brand;
        String safeDevice = TextUtils.isEmpty(device) ? model : device;

        setStaticField(Build.class, "MANUFACTURER", safeBrand);
        setStaticField(Build.class, "BRAND", safeBrand);
        setStaticField(Build.class, "MODEL", model);
        setStaticField(Build.class, "PRODUCT", safeDevice);
        setStaticField(Build.class, "DEVICE", safeDevice);
        setStaticField(Build.class, "BOARD", safeDevice);

        String fingerprint = safeBrand + "/" + safeDevice + "/" + safeDevice + ":14/UP1A.231005.007/V300:user/release-keys";
        setStaticField(Build.class, "FINGERPRINT", fingerprint);

        System.setProperty("ro.product.brand", safeBrand);
        System.setProperty("ro.product.manufacturer", safeBrand);
        System.setProperty("ro.product.model", model);
        System.setProperty("ro.product.name", model);
        System.setProperty("ro.product.device", safeDevice);
        System.setProperty("http.agent",
                "Mozilla/5.0 (Linux; Android 14; " + model + ") AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36");
    }

    private static void applyRegionAndNetworkProperties(Context ctx, String tzId, String countryIso, String virtualIp) {
        try {
            if (!TextUtils.isEmpty(tzId)) {
                TimeZone tz = TimeZone.getTimeZone(tzId);
                TimeZone.setDefault(tz);
                System.setProperty("persist.sys.timezone", tzId);
                System.setProperty("user.timezone", tzId);
            }
            if (!TextUtils.isEmpty(countryIso)) {
                System.setProperty("gsm.sim.operator.iso-country", countryIso.toLowerCase(Locale.US));
                System.setProperty("gsm.operator.iso-country", countryIso.toLowerCase(Locale.US));
                System.setProperty("persist.sys.country", countryIso.toUpperCase(Locale.US));
            }
            if (!TextUtils.isEmpty(virtualIp)) {
                System.setProperty("veyra.virtual.ip", virtualIp);
            }
            if (CloneMetadataStore.isGlobalProxyEnabled(ctx)) {
                String host = CloneMetadataStore.getGlobalProxyHost(ctx);
                int port = CloneMetadataStore.getGlobalProxyPort(ctx);
                if (!TextUtils.isEmpty(host) && port > 0) {
                    System.setProperty("socksProxyHost", host);
                    System.setProperty("socksProxyPort", String.valueOf(port));
                    System.setProperty("http.proxyHost", host);
                    System.setProperty("http.proxyPort", String.valueOf(port));
                    System.setProperty("https.proxyHost", host);
                    System.setProperty("https.proxyPort", String.valueOf(port));
                }
            } else {
                System.clearProperty("socksProxyHost");
                System.clearProperty("socksProxyPort");
                System.clearProperty("http.proxyHost");
                System.clearProperty("http.proxyPort");
                System.clearProperty("https.proxyHost");
                System.clearProperty("https.proxyPort");
            }
        } catch (Throwable ignored) {
        }
    }

    public static void injectVirtualGpsLocation(int spaceId, String pkg, double lat, double lon) {
        try {
            Location loc = new Location(LocationManager.GPS_PROVIDER);
            loc.setLatitude(lat);
            loc.setLongitude(lon);
            loc.setAltitude(42.0);
            loc.setAccuracy(3.5f);
            loc.setTime(System.currentTimeMillis());
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
                loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
            }

            Class<?> bLocMgrClass = Class.forName("top.niunaijun.blackbox.fake.frameworks.BLocationManager");
            Method getMethod = bLocMgrClass.getDeclaredMethod("get");
            Object mgr = getMethod.invoke(null);

            try {
                Class<?> bLocClass = Class.forName("top.niunaijun.blackbox.entity.location.BLocation");
                Object bLoc = bLocClass.getConstructor(double.class, double.class).newInstance(lat, lon);
                for (Method m : bLocMgrClass.getDeclaredMethods()) {
                    if (m.getName().equals("setLocation") && m.getParameterTypes().length == 3) {
                        m.setAccessible(true);
                        m.invoke(mgr, spaceId, pkg, bLoc);
                    }
                    if (m.getName().equals("setPattern") && m.getParameterTypes().length == 3) {
                        m.setAccessible(true);
                        m.invoke(mgr, spaceId, pkg, 2);
                    }
                }
            } catch (Throwable ignored) {
            }
        } catch (Throwable ignored) {
        }
    }

    public static void installGmsAvailabilityBypass() {
        try {
            System.setProperty("veyra.gms.PretendAvailable", "true");
            Class<?> gmsUtil = Class.forName("com.google.android.gms.common.GooglePlayServicesUtil");
            setStaticField(gmsUtil, "GOOGLE_PLAY_SERVICES_VERSION_CODE", 241516000);
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
""")

    # 10. Engine.java (Provides ClonedApp, InstallOptionCandidate, getInstallCandidates, cloneAppToSpace, installExternalApkFileToSpace)
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
import android.text.TextUtils;
import android.util.LruCache;

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
        public String sourceDir;
        public boolean isIndependentVaulted;
        public boolean isVaultBacked;
    }

    public static class ClonedApp extends AppModel {
    }

    public static class InstallOptionCandidate extends AppModel {
    }

    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(120);

    public static File getApkVaultDir(Context ctx, String pkg) {
        File dir = new File(ctx.getFilesDir(), "apk_vault/" + pkg);
        if (!dir.exists()) {
            dir.mkdirs();
        }
        return dir;
    }

    public static File getVaultedBaseApk(Context ctx, String pkg) {
        return new File(getApkVaultDir(ctx, pkg), "base.apk");
    }

    public static File backupPackageToVault(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
            File vaultDir = getApkVaultDir(ctx, pkg);
            File dstBase = new File(vaultDir, "base.apk");

            if (ai.sourceDir != null) {
                File srcBase = new File(ai.sourceDir);
                if (srcBase.exists() && (!dstBase.exists() || dstBase.length() != srcBase.length())) {
                    copyFile(srcBase, dstBase);
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

            extractNativeLibrariesFromVault(ctx, pkg, vaultDir);
            return dstBase.exists() ? dstBase : null;
        } catch (Throwable ignored) {
            File existing = getVaultedBaseApk(ctx, pkg);
            return existing.exists() ? existing : null;
        }
    }

    private static void extractNativeLibrariesFromVault(Context ctx, String pkg, File vaultDir) {
        File libOutDir = new File(vaultDir, "lib");
        if (!libOutDir.exists()) libOutDir.mkdirs();

        String primaryAbi = Build.CPU_ABI != null ? Build.CPU_ABI : "arm64-v8a";
        File[] apks = vaultDir.listFiles();
        if (apks == null) return;

        for (File apk : apks) {
            if (!apk.getName().endsWith(".apk")) continue;
            ZipFile zip = null;
            try {
                zip = new ZipFile(apk);
                Enumeration<? extends ZipEntry> entries = zip.entries();
                while (entries.hasMoreElements()) {
                    ZipEntry entry = entries.nextElement();
                    String name = entry.getName();
                    if (!name.startsWith("lib/") || !name.endsWith(".so")) continue;
                    if (name.contains(primaryAbi) || name.contains("arm64-v8a") || name.contains("armeabi-v7a")) {
                        String soFileName = name.substring(name.lastIndexOf('/') + 1);
                        File outSo = new File(libOutDir, soFileName);
                        if (!outSo.exists() || outSo.length() != entry.getSize()) {
                            InputStream is = zip.getInputStream(entry);
                            FileOutputStream fos = new FileOutputStream(outSo);
                            byte[] buf = new byte[16384];
                            int len;
                            while ((len = is.read(buf)) > 0) {
                                fos.write(buf, 0, len);
                            }
                            fos.close();
                            is.close();
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

        syncNativeLibsToBlackBoxDataDir(ctx, pkg, libOutDir);
    }

    private static void syncNativeLibsToBlackBoxDataDir(Context ctx, String pkg, File vaultLibDir) {
        try {
            File[] soFiles = vaultLibDir.listFiles();
            if (soFiles == null || soFiles.length == 0) return;

            File dataDir = new File(ctx.getApplicationInfo().dataDir);
            File[] possibleAppDirs = new File[]{
                new File(dataDir, "virtual/data/app/" + pkg + "/lib"),
                new File(dataDir, "virtual/data/user/0/" + pkg + "/lib"),
                new File(ctx.getFilesDir(), "virtual/data/app/" + pkg + "/lib")
            };

            for (File targetLibDir : possibleAppDirs) {
                targetLibDir.mkdirs();
                for (File so : soFiles) {
                    File dst = new File(targetLibDir, so.getName());
                    if (!dst.exists() || dst.length() != so.length()) {
                        copyFile(so, dst);
                    }
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static void copyFile(File src, File dst) throws Exception {
        FileInputStream fis = new FileInputStream(src);
        FileOutputStream fos = new FileOutputStream(dst);
        byte[] buf = new byte[32768];
        int read;
        while ((read = fis.read(buf)) > 0) {
            fos.write(buf, 0, read);
        }
        fos.flush();
        fos.close();
        fis.close();
    }

    public static List<InstallOptionCandidate> getInstallCandidates(Context ctx) {
        PackageManager pm = ctx.getPackageManager();
        List<ApplicationInfo> apps = pm.getInstalledApplications(PackageManager.GET_META_DATA);
        List<InstallOptionCandidate> result = new ArrayList<>();
        String myPkg = ctx.getPackageName();

        for (ApplicationInfo ai : apps) {
            if (myPkg.equals(ai.packageName)) continue;
            Intent launchIntent = pm.getLaunchIntentForPackage(ai.packageName);
            if (launchIntent == null) continue;

            InstallOptionCandidate m = new InstallOptionCandidate();
            m.packageName = ai.packageName;
            m.name = ai.loadLabel(pm).toString();
            m.icon = loadCachedIcon(pm, ai, ai.packageName);
            m.sourceDir = ai.sourceDir;
            result.add(m);
        }

        Collections.sort(result, new Comparator<InstallOptionCandidate>() {
            @Override
            public int compare(InstallOptionCandidate a, InstallOptionCandidate b) {
                return a.name.compareToIgnoreCase(b.name);
            }
        });
        return result;
    }

    public static List<ClonedApp> getClonedApps(Context ctx, int spaceId) {
        PackageManager pm = ctx.getPackageManager();
        List<ClonedApp> list = new ArrayList<>();
        Set<String> seenPackages = new HashSet<>();

        try {
            List<PackageInfo> installed = BlackBoxCore.get().getInstalledPackages(0, spaceId);
            if (installed != null) {
                for (PackageInfo pi : installed) {
                    if (pi == null || TextUtils.isEmpty(pi.packageName)) continue;
                    if (ctx.getPackageName().equals(pi.packageName)) continue;
                    if (pi.packageName.contains("google.android.gms") || pi.packageName.contains("google.android.gsf")) {
                        continue;
                    }
                    seenPackages.add(pi.packageName);
                    CloneMetadataStore.registerClonedPackage(ctx, pi.packageName, spaceId);
                    ClonedApp m = buildClonedAppModel(ctx, pm, pi.packageName, pi.applicationInfo, spaceId);
                    if (m != null) list.add(m);
                }
            }
        } catch (Throwable ignored) {
        }

        Set<String> registered = CloneMetadataStore.getRegisteredPackagesForSpace(ctx, spaceId);
        for (String pkg : registered) {
            if (seenPackages.contains(pkg)) continue;
            File vaultedApk = getVaultedBaseApk(ctx, pkg);
            boolean stillInBlackBox = false;
            try {
                stillInBlackBox = BlackBoxCore.get().isInstalled(pkg, spaceId);
            } catch (Throwable ignored) {
            }
            if (!stillInBlackBox && vaultedApk.exists()) {
                try {
                    BlackBoxCore.get().installPackageAsUser(vaultedApk, spaceId);
                    stillInBlackBox = true;
                } catch (Throwable ignored) {
                }
            }
            if (stillInBlackBox || vaultedApk.exists()) {
                ClonedApp m = buildClonedAppModel(ctx, pm, pkg, null, spaceId);
                if (m != null) {
                    seenPackages.add(pkg);
                    list.add(m);
                }
            }
        }

        return list;
    }

    private static ClonedApp buildClonedAppModel(Context ctx, PackageManager pm, String pkg,
                                                 ApplicationInfo fallbackAi, int spaceId) {
        ClonedApp m = new ClonedApp();
        m.packageName = pkg;

        try {
            ApplicationInfo hostAi = pm.getApplicationInfo(pkg, 0);
            m.name = hostAi.loadLabel(pm).toString();
            m.icon = loadCachedIcon(pm, hostAi, pkg);
            boolean vaulted = getVaultedBaseApk(ctx, pkg).exists();
            m.isIndependentVaulted = vaulted;
            m.isVaultBacked = vaulted;
        } catch (Throwable notOnHost) {
            File vaultedApk = getVaultedBaseApk(ctx, pkg);
            if (vaultedApk.exists()) {
                PackageInfo archiveInfo = pm.getPackageArchiveInfo(vaultedApk.getAbsolutePath(), 0);
                if (archiveInfo != null && archiveInfo.applicationInfo != null) {
                    ApplicationInfo aInfo = archiveInfo.applicationInfo;
                    aInfo.sourceDir = vaultedApk.getAbsolutePath();
                    aInfo.publicSourceDir = vaultedApk.getAbsolutePath();
                    CharSequence lbl = pm.getApplicationLabel(aInfo);
                    m.name = lbl != null ? lbl.toString() : pkg;
                    m.icon = pm.getApplicationIcon(aInfo);
                    m.isIndependentVaulted = true;
                    m.isVaultBacked = true;
                }
            }
            if (m.name == null && fallbackAi != null) {
                CharSequence lbl = fallbackAi.loadLabel(pm);
                m.name = lbl != null ? lbl.toString() : pkg;
                m.icon = fallbackAi.loadIcon(pm);
            }
        }

        if (TextUtils.isEmpty(m.name)) m.name = pkg;
        if (m.icon == null) {
            m.icon = ctx.getResources().getDrawable(android.R.drawable.sym_def_app_icon);
        }

        String alias = CloneMetadataStore.getCustomLabel(ctx, pkg, spaceId);
        if (!TextUtils.isEmpty(alias)) {
            m.name = alias;
        }
        return m;
    }

    private static Drawable loadCachedIcon(PackageManager pm, ApplicationInfo ai, String key) {
        Drawable cached = ICON_CACHE.get(key);
        if (cached != null) return cached;
        try {
            Drawable d = ai.loadIcon(pm);
            if (d != null) ICON_CACHE.put(key, d);
            return d;
        } catch (Throwable e) {
            return null;
        }
    }

    public static boolean cloneAppToSpace(Context ctx, String pkg, int spaceId) {
        return cloneApp(ctx, pkg, spaceId);
    }

    public static boolean cloneApp(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.ensureGmsForSpace(spaceId);
            File vaultedApk = backupPackageToVault(ctx, pkg);
            InstallResult res;
            if (vaultedApk != null && vaultedApk.exists()) {
                res = BlackBoxCore.get().installPackageAsUser(vaultedApk, spaceId);
                if (res == null || !res.success) {
                    res = BlackBoxCore.get().installPackageAsUser(pkg, spaceId);
                }
            } else {
                res = BlackBoxCore.get().installPackageAsUser(pkg, spaceId);
            }
            if (res != null && res.success) {
                CloneMetadataStore.registerClonedPackage(ctx, pkg, spaceId);
                return true;
            }
            return false;
        } catch (Throwable e) {
            return false;
        }
    }

    public static boolean installExternalApkFileToSpace(Context ctx, File externalApkFile, int spaceId) {
        return installApkFileIntoSpace(ctx, externalApkFile, spaceId) != null;
    }

    public static String installApkFileIntoSpace(Context ctx, File externalApkFile, int spaceId) {
        if (externalApkFile == null || !externalApkFile.exists()) return null;
        try {
            PackageManager pm = ctx.getPackageManager();
            PackageInfo archive = pm.getPackageArchiveInfo(externalApkFile.getAbsolutePath(), 0);
            String pkgName = (archive != null && !TextUtils.isEmpty(archive.packageName))
                    ? archive.packageName
                    : null;

            File apkToInstall = externalApkFile;
            if (pkgName != null) {
                File vaultDir = getApkVaultDir(ctx, pkgName);
                File dstBase = new File(vaultDir, "base.apk");
                copyFile(externalApkFile, dstBase);
                extractNativeLibrariesFromVault(ctx, pkgName, vaultDir);
                apkToInstall = dstBase;
            }

            GmsSupportManager.ensureGmsForSpace(spaceId);
            InstallResult res = BlackBoxCore.get().installPackageAsUser(apkToInstall, spaceId);
            if (res != null && res.success) {
                String finalPkg = !TextUtils.isEmpty(res.packageName) ? res.packageName : pkgName;
                if (!TextUtils.isEmpty(finalPkg)) {
                    CloneMetadataStore.registerClonedPackage(ctx, finalPkg, spaceId);
                }
                return finalPkg != null ? finalPkg : "installed";
            }
        } catch (Throwable ignored) {
        }
        return null;
    }

    public static boolean removeClone(Context ctx, String pkg, int spaceId) {
        try {
            CloneMetadataStore.unregisterClonedPackage(ctx, pkg, spaceId);
            CloneMetadataStore.clearDeviceIdentity(ctx, pkg, spaceId);
            CloneMetadataStore.clearCustomLocation(ctx, pkg, spaceId);
            CloneMetadataStore.setCustomLabel(ctx, pkg, spaceId, "");
            BlackBoxCore.get().uninstallPackageAsUser(pkg, spaceId);
            return true;
        } catch (Throwable e) {
            return false;
        }
    }

    public static boolean launchClone(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.ensureGmsForSpace(spaceId);
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, spaceId);

            File vaultDir = getApkVaultDir(ctx, pkg);
            File vaultLibDir = new File(vaultDir, "lib");
            if (vaultLibDir.exists()) {
                syncNativeLibsToBlackBoxDataDir(ctx, pkg, vaultLibDir);
            } else {
                backupPackageToVault(ctx, pkg);
            }

            if (!BlackBoxCore.get().isInstalled(pkg, spaceId)) {
                File vaultedBase = getVaultedBaseApk(ctx, pkg);
                if (vaultedBase.exists()) {
                    BlackBoxCore.get().installPackageAsUser(vaultedBase, spaceId);
                }
            }

            Intent explicitMainIntent = resolveRealMainLauncherIntent(ctx, pkg);
            if (explicitMainIntent != null) {
                try {
                    Method launchIntentMethod = BlackBoxCore.class.getDeclaredMethod(
                            "launchIntent", Intent.class, int.class
                    );
                    launchIntentMethod.setAccessible(true);
                    Object launched = launchIntentMethod.invoke(BlackBoxCore.get(), explicitMainIntent, spaceId);
                    if (launched instanceof Boolean && (Boolean) launched) {
                        return true;
                    }
                } catch (Throwable ignored) {
                }
            }

            return BlackBoxCore.get().launchApk(pkg, spaceId);
        } catch (Throwable e) {
            return false;
        }
    }

    private static Intent resolveRealMainLauncherIntent(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            if ("com.android.chrome".equals(pkg) || "com.chrome.beta".equals(pkg) || "com.chrome.dev".equals(pkg)) {
                Intent chromeIntent = new Intent(Intent.ACTION_MAIN);
                chromeIntent.addCategory(Intent.CATEGORY_LAUNCHER);
                chromeIntent.setPackage(pkg);
                chromeIntent.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
                chromeIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                return chromeIntent;
            }

            Intent query = new Intent(Intent.ACTION_MAIN);
            query.addCategory(Intent.CATEGORY_LAUNCHER);
            query.setPackage(pkg);
            List<ResolveInfo> resolves = pm.queryIntentActivities(query, 0);
            if (resolves != null && !resolves.isEmpty()) {
                for (ResolveInfo ri : resolves) {
                    if (ri.activityInfo == null) continue;
                    String actName = ri.activityInfo.name;
                    if (actName != null && !actName.toLowerCase().contains("devui")
                            && !actName.toLowerCase().contains("devtools")) {
                        Intent intent = new Intent(Intent.ACTION_MAIN);
                        intent.addCategory(Intent.CATEGORY_LAUNCHER);
                        intent.setComponent(new ComponentName(pkg, actName));
                        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        return intent;
                    }
                }
            }
        } catch (Throwable ignored) {
        }
        return null;
    }

    public static void clearMemoryCache() {
        ICON_CACHE.evictAll();
        System.gc();
    }
}
""")

    # 11. SecurityManager.java (Includes requestEnableAntiUninstall and disableAntiUninstall)
    write_file("app/src/main/java/com/veyravault/space/security/SecurityManager.java", """
package com.veyravault.space.security;

import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.text.TextUtils;

import com.veyravault.space.R;

import java.security.MessageDigest;

public class SecurityManager {

    private static final String PREFS = "veyra_security_v3";
    private static final String KEY_LOCK_ENABLED = "lock_enabled";
    private static final String KEY_PRIMARY_TYPE = "primary_lock_type";
    private static final String KEY_PIN_HASH = "pin_hash";
    private static final String KEY_PATTERN_HASH = "pattern_hash";
    private static final String KEY_LEGACY_HASH = "secret_hash";
    private static final String KEY_LEGACY_MODE = "lock_mode";

    public static final String TYPE_PIN = "PIN";
    public static final String TYPE_PATTERN = "PATTERN";

    private static boolean sessionUnlocked = false;

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static boolean isSessionUnlocked() {
        return sessionUnlocked;
    }

    public static void setSessionUnlocked(boolean unlocked) {
        sessionUnlocked = unlocked;
    }

    public static boolean isLockEnabled(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        migrateLegacyIfNeeded(sp);
        return sp.getBoolean(KEY_LOCK_ENABLED, false) && (hasPinConfigured(ctx) || hasPatternConfigured(ctx));
    }

    public static void setLockEnabled(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean(KEY_LOCK_ENABLED, enabled).apply();
        if (!enabled) {
            sessionUnlocked = true;
        }
    }

    private static void migrateLegacyIfNeeded(SharedPreferences sp) {
        if (sp.contains(KEY_LEGACY_HASH) && !sp.contains(KEY_PIN_HASH) && !sp.contains(KEY_PATTERN_HASH)) {
            String legacyHash = sp.getString(KEY_LEGACY_HASH, "");
            String legacyMode = sp.getString(KEY_LEGACY_MODE, TYPE_PIN);
            if (!TextUtils.isEmpty(legacyHash)) {
                SharedPreferences.Editor ed = sp.edit();
                if (TYPE_PATTERN.equalsIgnoreCase(legacyMode)) {
                    ed.putString(KEY_PATTERN_HASH, legacyHash);
                    ed.putString(KEY_PRIMARY_TYPE, TYPE_PATTERN);
                } else {
                    ed.putString(KEY_PIN_HASH, legacyHash);
                    ed.putString(KEY_PRIMARY_TYPE, TYPE_PIN);
                }
                ed.apply();
            }
        }
    }

    public static boolean hasPinConfigured(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        migrateLegacyIfNeeded(sp);
        return !TextUtils.isEmpty(sp.getString(KEY_PIN_HASH, ""));
    }

    public static boolean hasPatternConfigured(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        migrateLegacyIfNeeded(sp);
        return !TextUtils.isEmpty(sp.getString(KEY_PATTERN_HASH, ""));
    }

    public static boolean hasBothLocksConfigured(Context ctx) {
        return hasPinConfigured(ctx) && hasPatternConfigured(ctx);
    }

    public static void savePinLock(Context ctx, String rawPin, boolean makePrimary) {
        if (TextUtils.isEmpty(rawPin)) return;
        SharedPreferences.Editor ed = prefs(ctx).edit();
        ed.putString(KEY_PIN_HASH, sha256(rawPin.trim()));
        ed.putBoolean(KEY_LOCK_ENABLED, true);
        if (makePrimary || !hasPatternConfigured(ctx)) {
            ed.putString(KEY_PRIMARY_TYPE, TYPE_PIN);
        }
        ed.apply();
        sessionUnlocked = true;
    }

    public static void savePatternLock(Context ctx, String rawPattern, boolean makePrimary) {
        if (TextUtils.isEmpty(rawPattern)) return;
        SharedPreferences.Editor ed = prefs(ctx).edit();
        ed.putString(KEY_PATTERN_HASH, sha256(rawPattern.trim()));
        ed.putBoolean(KEY_LOCK_ENABLED, true);
        if (makePrimary || !hasPinConfigured(ctx)) {
            ed.putString(KEY_PRIMARY_TYPE, TYPE_PATTERN);
        }
        ed.apply();
        sessionUnlocked = true;
    }

    public static String getPrimaryLockType(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        migrateLegacyIfNeeded(sp);
        String primary = sp.getString(KEY_PRIMARY_TYPE, TYPE_PIN);
        if (TYPE_PATTERN.equals(primary) && hasPatternConfigured(ctx)) {
            return TYPE_PATTERN;
        }
        if (TYPE_PIN.equals(primary) && hasPinConfigured(ctx)) {
            return TYPE_PIN;
        }
        if (hasPinConfigured(ctx)) return TYPE_PIN;
        if (hasPatternConfigured(ctx)) return TYPE_PATTERN;
        return TYPE_PIN;
    }

    public static void setPrimaryLockType(Context ctx, String lockType) {
        prefs(ctx).edit().putString(KEY_PRIMARY_TYPE, lockType).apply();
    }

    public static boolean verifyPin(Context ctx, String rawPin) {
        if (TextUtils.isEmpty(rawPin)) return false;
        String stored = prefs(ctx).getString(KEY_PIN_HASH, "");
        return !TextUtils.isEmpty(stored) && stored.equals(sha256(rawPin.trim()));
    }

    public static boolean verifyPattern(Context ctx, String rawPattern) {
        if (TextUtils.isEmpty(rawPattern)) return false;
        String stored = prefs(ctx).getString(KEY_PATTERN_HASH, "");
        return !TextUtils.isEmpty(stored) && stored.equals(sha256(rawPattern.trim()));
    }

    public static boolean verifySecret(Context ctx, String input) {
        return verifyPin(ctx, input) || verifyPattern(ctx, input);
    }

    public static void clearAllLocks(Context ctx) {
        prefs(ctx).edit()
                .remove(KEY_PIN_HASH)
                .remove(KEY_PATTERN_HASH)
                .remove(KEY_LEGACY_HASH)
                .putBoolean(KEY_LOCK_ENABLED, false)
                .apply();
        sessionUnlocked = true;
    }

    private static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest(("veyra_v3_salt_" + input).getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            return String.valueOf(input.hashCode());
        }
    }

    public static ComponentName getAdminComponent(Context ctx) {
        return new ComponentName(ctx, VaultDeviceAdminReceiver.class);
    }

    public static boolean isAntiUninstallActive(Context ctx) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            return dpm != null && dpm.isAdminActive(getAdminComponent(ctx));
        } catch (Throwable e) {
            return false;
        }
    }

    public static Intent createActivateAdminIntent(Context ctx, String explanation) {
        Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
        intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, getAdminComponent(ctx));
        intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION, explanation);
        return intent;
    }

    public static void requestEnableAntiUninstall(Activity activity, int requestCode) {
        try {
            String desc = activity.getString(R.string.device_admin_desc);
            Intent intent = createActivateAdminIntent(activity, desc);
            activity.startActivityForResult(intent, requestCode);
        } catch (Throwable ignored) {
        }
    }

    public static void disableAntiUninstall(Context ctx) {
        deactivateAntiUninstall(ctx);
    }

    public static void deactivateAntiUninstall(Context ctx) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            if (dpm != null && dpm.isAdminActive(getAdminComponent(ctx))) {
                dpm.removeActiveAdmin(getAdminComponent(ctx));
            }
        } catch (Throwable ignored) {
        }
    }
}
""")

    # 12. VaultDeviceAdminReceiver.java
    write_file("app/src/main/java/com/veyravault/space/security/VaultDeviceAdminReceiver.java", """
package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

import com.veyravault.space.R;
import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    @Override
    public void onEnabled(Context context, Intent intent) {
        super.onEnabled(context, intent);
    }

    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
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
        String msg = context.getString(R.string.anti_uninstall_warning);
        Toast.makeText(context, msg, Toast.LENGTH_LONG).show();
        return msg;
    }

    @Override
    public void onDisabled(Context context, Intent intent) {
        super.onDisabled(context, intent);
    }
}
""")


def patch_part2_if_present():
    part2_path = os.path.join(ROOT, "scripts", "upgrade_v3_part2.py")
    if not os.path.exists(part2_path):
        return
    with open(part2_path, "r", encoding="utf-8") as f:
        txt = f.read()

    txt = txt.replace("CENTER_horizontal", "CENTER_HORIZONTAL")

    with open(part2_path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[v3-part1] Auto-patched scripts/upgrade_v3_part2.py successfully.")


if __name__ == "__main__":
    clean_legacy_sources()
    patch_build_gradle()
    create_resources()
    create_core_and_helper_classes()
    patch_part2_if_present()
    print("[v3-part1] Completed successfully.")
