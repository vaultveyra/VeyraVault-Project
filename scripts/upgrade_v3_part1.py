#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_BASE = "app/src/main"
JAVA_BASE = f"{APP_BASE}/java/com/veyravault/space"


def write_file(rel_path, content):
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    print(f"[v3.0-Part1] Wrote: {rel_path}")


# 1. APACHE 2.0 ATTRIBUTION
write_file(
    f"{APP_BASE}/assets/NOTICE_APACHE_2.txt",
    """VeyraVault v3.0.0
Copyright (C) 2025 VeyraVault Project (Vaultveyra@gmail.com | https://t.me/VaultVeyra)
Licensed under the Apache License, Version 2.0.
""",
)

# 2. DEVICE ADMIN XML & DRAWABLE VECTORS (INCLUDING APP LAUNCHER ICONS)
write_file(
    f"{APP_BASE}/res/xml/device_admin_receiver.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <force-lock />
    </uses-policies>
</device-admin>
""",
)

write_file(
    f"{APP_BASE}/res/xml/file_paths.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res/android">
    <files-path name="apk_vault" path="apk_vault/" />
    <cache-path name="picked_apks" path="picked_apks/" />
    <external-path name="external_files" path="." />
</paths>
""",
)

write_file(
    f"{APP_BASE}/res/drawable/ic_launcher.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#0F172A"
        android:pathData="M0,0h108v108h-108z" />
    <path
        android:fillColor="#0284C7"
        android:pathData="M54,16L22,30v24c0,22.2 13.6,42.9 32,50c18.4,-7.1 32,-27.8 32,-50V30L54,16z" />
    <path
        android:fillColor="#38BDF8"
        android:pathData="M54,26L30,36.5v17.5c0,16.6 10.2,32.1 24,37.5c13.8,-5.4 24,-20.9 24,-37.5V36.5L54,26z" />
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M42,44h8l4,16l4,-16h8l-8,26h-8L42,44z" />
</vector>
""",
)

write_file(
    f"{APP_BASE}/res/drawable/ic_launcher_round.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#0F172A"
        android:pathData="M54,4A50,50 0 1,1 54,104A50,50 0 1,1 54,4z" />
    <path
        android:fillColor="#0284C7"
        android:pathData="M54,18L24,31v23c0,20.8 12.8,40.2 30,46.8c17.2,-6.6 30,-26 30,-46.8V31L54,18z" />
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M42,44h8l4,16l4,-16h8l-8,26h-8L42,44z" />
</vector>
""",
)

write_file(
    f"{APP_BASE}/res/drawable/ic_nav_dashboard.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M3,13h8V3H3v10zm0,8h8v-6H3v6zm10,0h8V11h-8v10zm0,-18v6h8V3h-8z"/>
</vector>
""",
)

write_file(
    f"{APP_BASE}/res/drawable/ic_nav_spaces.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M4,8h4V4H4v4zm6,12h4v-4h-4v4zm-6,0h4v-4H4v4zm0,-6h4v-4H4v4zm6,0h4v-4h-4v4zm6,-10v4h4V4h-4zm-6,4h4V4h-4v4zm6,6h4v-4h-4v4zm0,6h4v-4h-4v4z"/>
</vector>
""",
)

write_file(
    f"{APP_BASE}/res/drawable/ic_nav_add.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
</vector>
""",
)

write_file(
    f"{APP_BASE}/res/drawable/ic_nav_guide.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M18,2H6c-1.1,0 -2,0.9 -2,2v16c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V4c0,-1.1 -0.9,-2 -2,-2zM6,4h5v8l-2.5,-1.5L6,12V4z"/>
</vector>
""",
)

write_file(
    f"{APP_BASE}/res/drawable/ic_nav_settings.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"/>
</vector>
""",
)

# 3. STRINGS XML (WITH MIPMAP ALIASES FOR UNIVERSAL COMPATIBILITY)
write_file(
    f"{APP_BASE}/res/values/strings.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="device_admin_label">محافظ ضدحذف VeyraVault</string>
    <string name="device_admin_desc">محافظت امنیتی در برابر حذف غیرمجاز برنامه</string>
    <item name="ic_launcher" type="mipmap">@drawable/ic_launcher</item>
    <item name="ic_launcher_round" type="mipmap">@drawable/ic_launcher_round</item>
</resources>
""",
)

write_file(
    f"{APP_BASE}/res/values-fa/strings.xml",
    """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="device_admin_label">محافظ ضدحذف VeyraVault</string>
    <string name="device_admin_desc">محافظت امنیتی در برابر حذف غیرمجاز برنامه</string>
</resources>
""",
)

# 4. ANDROID MANIFEST
write_file(
    f"{APP_BASE}/AndroidManifest.xml",
    """<?xml version="1.0" encoding="utf-8"?>
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
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />

    <application
        android:name=".VeyraApplication"
        android:allowBackup="true"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@drawable/ic_launcher_round"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:extractNativeLibs="true"
        android:theme="@style/Theme.AppCompat.NoActionBar"
        tools:replace="android:icon,android:roundIcon,android:label,android:allowBackup,android:supportsRtl,android:theme">

        <activity
            android:name=".ui.MainActivity"
            android:exported="true"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity android:name=".ui.AddAppActivity" android:exported="false" />
        <activity android:name=".ui.SetLocationActivity" android:exported="false" />
        <activity android:name=".ui.GlobalEnvironmentActivity" android:exported="false" />
        <activity android:name=".ui.SecuritySettingsActivity" android:exported="false" />
        <activity android:name=".ui.SecurityLockActivity" android:exported="false" android:launchMode="singleTop" />
        <activity android:name=".ui.GuideActivity" android:exported="false" />
        <activity android:name=".ui.AboutActivity" android:exported="false" />

        <receiver
            android:name=".security.VaultDeviceAdminReceiver"
            android:label="@string/device_admin_label"
            android:description="@string/device_admin_desc"
            android:permission="android.permission.BIND_DEVICE_ADMIN"
            android:exported="true">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/device_admin_receiver" />
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

# 5. JALALI CLOCK UTIL
write_file(
    f"{JAVA_BASE}/helper/JalaliClockUtil.java",
    """package com.veyravault.space.helper;

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

    private static final String[] PERSIAN_MONTHS_EN = {
        "Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad", "Shahrivar",
        "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand"
    };

    private static final String[] PERSIAN_WEEKDAYS = {
        "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه"
    };

    public static String getTehranTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("Asia/Tehran"));
        return sdf.format(new Date());
    }

    public static String getTehranJalaliDate(boolean persianText) {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Tehran"));
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int dow = cal.get(Calendar.DAY_OF_WEEK) - 1;
        int[] j = gregorianToJalali(gy, gm, gd);
        if (persianText) {
            return PERSIAN_WEEKDAYS[dow] + " " + toPersianDigits(String.valueOf(j[2])) + " "
                    + PERSIAN_MONTHS[j[1] - 1] + " " + toPersianDigits(String.valueOf(j[0]));
        } else {
            return j[2] + " " + PERSIAN_MONTHS_EN[j[1] - 1] + " " + j[0] + " SH";
        }
    }

    public static String getNewYorkTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String getNewYorkGregorianDate(boolean persianText) {
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy", Locale.US);
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

# 6. LOCALE HELPER & BASE ACTIVITY
write_file(
    f"{JAVA_BASE}/helper/LocaleHelper.java",
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

    public static Context setLocale(Context context, String lang) {
        SharedPreferences sp = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        sp.edit().putString(KEY_LANG, lang).commit();
        Locale locale = new Locale(lang);
        Locale.setDefault(locale);
        Resources res = context.getResources();
        Configuration config = new Configuration(res.getConfiguration());
        if (Build.VERSION.SDK_INT >= 17) {
            config.setLocale(locale);
            config.setLayoutDirection(locale);
        } else {
            config.locale = locale;
        }
        res.updateConfiguration(config, res.getDisplayMetrics());
        return context;
    }
}
""",
)

write_file(
    f"{JAVA_BASE}/ui/BaseActivity.java",
    """package com.veyravault.space.ui;

import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.veyravault.space.helper.LocaleHelper;
import com.veyravault.space.security.SecurityManager;

public abstract class BaseActivity extends AppCompatActivity {

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.onAttach(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        LocaleHelper.onAttach(this);
        super.onCreate(savedInstanceState);
        applyDirection();
    }

    @Override
    protected void onResume() {
        super.onResume();
        applyDirection();
        if (!shouldBypassSecurityLock() && SecurityManager.isLockConfigured(this) && !SecurityManager.isSessionUnlocked()) {
            Intent lockIntent = new Intent(this, SecurityLockActivity.class);
            startActivity(lockIntent);
        }
    }

    protected boolean shouldBypassSecurityLock() {
        return false;
    }

    protected boolean isLockScreenActivity() {
        return shouldBypassSecurityLock();
    }

    protected void applyDirection() {
        if (Build.VERSION.SDK_INT >= 17 && getWindow() != null && getWindow().getDecorView() != null) {
            boolean fa = LocaleHelper.isPersian(this);
            getWindow().getDecorView().setLayoutDirection(
                    fa ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        }
    }

    protected boolean isPersian() {
        return LocaleHelper.isPersian(this);
    }

    protected void switchLanguageInstant() {
        LocaleHelper.toggleLanguage(this);
        recreate();
    }

    protected void triggerQuickLock() {
        if (!SecurityManager.isLockConfigured(this)) {
            Toast.makeText(this, isPersian()
                    ? "ابتدا در بخش تنظیمات امنیتی، پین یا الگو را فعال کنید"
                    : "Please set a PIN or Pattern in Security Settings first", Toast.LENGTH_SHORT).show();
            startActivity(new Intent(this, SecuritySettingsActivity.class));
            return;
        }
        SecurityManager.setSessionUnlocked(false);
        Intent lockIntent = new Intent(this, SecurityLockActivity.class);
        startActivity(lockIntent);
    }
}
""",
)

# 7. GMS SUPPORT MANAGER & APP DISGUISE MANAGER & PATTERN LOCK VIEW
write_file(
    f"{JAVA_BASE}/helper/GmsSupportManager.java",
    """package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;
import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    private static final String PREF = "veyra_gms_prefs";
    private static final String KEY_GMS = "gms_enabled";

    private static final String[] GMS_PACKAGES = {
        "com.google.android.gms",
        "com.google.android.gsf",
        "com.google.android.gsf.login",
        "com.android.vending",
        "com.google.android.webview",
        "com.android.chrome"
    };

    public static boolean isGmsEnabledPref(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREF, Context.MODE_PRIVATE);
        return sp.getBoolean(KEY_GMS, true);
    }

    public static boolean isGmsSupported(Context context) {
        return isGmsEnabledPref(context);
    }

    public static void setGmsEnabledPref(Context context, boolean enabled) {
        SharedPreferences sp = context.getSharedPreferences(PREF, Context.MODE_PRIVATE);
        sp.edit().putBoolean(KEY_GMS, enabled).commit();
    }

    public static void enableGmsForAllSpaces(Context context) {
        for (int spaceId : new int[]{0, 1, 2}) {
            ensureGmsEnabled(context, spaceId);
        }
    }

    public static void ensureGmsEnabled(Context context, int spaceId) {
        try {
            System.setProperty("veyra.gms.AutoAvailable", "true");
            if (!isGmsEnabledPref(context)) return;
            BlackBoxCore core = BlackBoxCore.get();
            for (String pkg : GMS_PACKAGES) {
                try {
                    context.getPackageManager().getPackageInfo(pkg, 0);
                    if (!core.isInstalled(pkg, spaceId)) {
                        core.installPackageAsUser(pkg, spaceId);
                    }
                } catch (Throwable ignored) {
                }
            }
        } catch (Throwable ignored) {
        }
    }
}
""",
)

write_file(
    f"{JAVA_BASE}/helper/AppDisguiseManager.java",
    """package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;

public class AppDisguiseManager {
    private static final String PREF = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode";

    public static final String MODE_DEFAULT = "default";
    public static final String MODE_CLOCK = "clock";
    public static final String MODE_CALCULATOR = "calculator";
    public static final String MODE_CALENDAR = "calendar";
    public static final String MODE_NOTEPAD = "notepad";

    public static String getDisguiseMode(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).getString(KEY_MODE, MODE_DEFAULT);
    }

    public static void setDisguiseMode(Context ctx, String mode) {
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putString(KEY_MODE, mode).commit();
    }

    public static String getDisguiseTitle(Context ctx, boolean fa) {
        String mode = getDisguiseMode(ctx);
        if (MODE_CLOCK.equals(mode)) {
            return fa ? "ساعت جهانی و تقویم" : "World Clock & Calendar";
        } else if (MODE_CALCULATOR.equals(mode)) {
            return fa ? "ماشین‌حساب مهندسی" : "Scientific Calculator";
        } else if (MODE_CALENDAR.equals(mode)) {
            return fa ? "تقویم هوشمند خورشیدی" : "Smart Solar Calendar";
        } else if (MODE_NOTEPAD.equals(mode)) {
            return fa ? "دفترچه یادداشت شخصی" : "Personal Notepad";
        }
        return "VeyraVault";
    }
}
""",
)

write_file(
    f"{JAVA_BASE}/helper/PatternLockView.java",
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
        void onPatternDetected(String pattern);
    }

    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final List<Integer> selectedDots = new ArrayList<>();
    private float curX, curY;
    private boolean isDrawing = false;
    private OnPatternListener listener;

    public PatternLockView(Context context) {
        super(context);
        dotPaint.setColor(Color.parseColor("#64748B"));
        dotPaint.setStyle(Paint.Style.FILL);
        activePaint.setColor(Color.parseColor("#38BDF8"));
        activePaint.setStyle(Paint.Style.FILL);
        linePaint.setColor(Color.parseColor("#38BDF8"));
        linePaint.setStrokeWidth(10f);
        linePaint.setStyle(Paint.Style.STROKE);
    }

    public void setOnPatternListener(OnPatternListener l) {
        this.listener = l;
    }

    public void clearPattern() {
        selectedDots.clear();
        invalidate();
    }

    private float getDotX(int index) {
        int col = index % 3;
        float step = getWidth() / 4f;
        return step * (col + 1);
    }

    private float getDotY(int index) {
        int row = index / 3;
        float step = getHeight() / 4f;
        return step * (row + 1);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        for (int i = 0; i < selectedDots.size() - 1; i++) {
            int a = selectedDots.get(i);
            int b = selectedDots.get(i + 1);
            canvas.drawLine(getDotX(a), getDotY(a), getDotX(b), getDotY(b), linePaint);
        }
        if (isDrawing && !selectedDots.isEmpty()) {
            int last = selectedDots.get(selectedDots.size() - 1);
            canvas.drawLine(getDotX(last), getDotY(last), curX, curY, linePaint);
        }
        for (int i = 0; i < 9; i++) {
            boolean active = selectedDots.contains(i);
            canvas.drawCircle(getDotX(i), getDotY(i), active ? 26f : 18f, active ? activePaint : dotPaint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        curX = event.getX();
        curY = event.getY();
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                selectedDots.clear();
                isDrawing = true;
                checkHit(curX, curY);
                invalidate();
                return true;
            case MotionEvent.ACTION_MOVE:
                checkHit(curX, curY);
                invalidate();
                return true;
            case MotionEvent.ACTION_UP:
                isDrawing = false;
                if (listener != null && !selectedDots.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < selectedDots.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(selectedDots.get(i));
                    }
                    listener.onPatternDetected(sb.toString());
                }
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y) {
        float radius = Math.min(getWidth(), getHeight()) / 7f;
        for (int i = 0; i < 9; i++) {
            if (!selectedDots.contains(i)) {
                float dx = x - getDotX(i);
                float dy = y - getDotY(i);
                if (Math.hypot(dx, dy) <= radius) {
                    selectedDots.add(i);
                }
            }
        }
    }
}
""",
)

# 8. CLONE METADATA STORE
write_file(
    f"{JAVA_BASE}/core/CloneMetadataStore.java",
    """package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class CloneMetadataStore {
    private static final String PREF = "veyra_clone_metadata_v3";

    private static final String KEY_GLOBAL_BRAND = "global_device_brand";
    private static final String KEY_GLOBAL_MODEL = "global_device_model";
    private static final String KEY_GLOBAL_LOC_ENABLED = "global_loc_enabled";
    private static final String KEY_GLOBAL_LAT = "global_lat";
    private static final String KEY_GLOBAL_LON = "global_lon";
    private static final String KEY_GLOBAL_REGION = "global_region_city_country";
    private static final String KEY_GLOBAL_VIRTUAL_IP = "global_virtual_ip";
    private static final String KEY_GLOBAL_PROXY_HOST = "global_proxy_host";
    private static final String KEY_GLOBAL_PROXY_PORT = "global_proxy_port";

    public static class RegionPreset {
        public final String cityCountry;
        public final double lat;
        public final double lon;
        public final String sampleIp;
        public final String timeZoneId;

        public RegionPreset(String cityCountry, double lat, double lon, String sampleIp, String timeZoneId) {
            this.cityCountry = cityCountry;
            this.lat = lat;
            this.lon = lon;
            this.sampleIp = sampleIp;
            this.timeZoneId = timeZoneId;
        }
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    private static String prefix(String pkg, int spaceId) {
        return "sp_" + spaceId + "_" + pkg + "_";
    }

    public static String getSpaceCustomName(Context ctx, int spaceId) {
        return prefs(ctx).getString("space_custom_name_" + spaceId, "");
    }

    public static void setSpaceCustomName(Context ctx, int spaceId, String customName) {
        prefs(ctx).edit().putString("space_custom_name_" + spaceId, customName == null ? "" : customName.trim()).commit();
    }

    public static String getSpaceDisplayName(Context ctx, int spaceId, boolean fa) {
        String custom = getSpaceCustomName(ctx, spaceId);
        if (custom != null && !custom.trim().isEmpty()) {
            return custom.trim();
        }
        int num = spaceId + 1;
        return fa ? ("فضای " + num) : ("Space " + num);
    }

    public static String getGlobalDeviceBrand(Context ctx) {
        return prefs(ctx).getString(KEY_GLOBAL_BRAND, "Apple");
    }

    public static String getGlobalDeviceModel(Context ctx) {
        return prefs(ctx).getString(KEY_GLOBAL_MODEL, "iPhone 16 Pro Max");
    }

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model) {
        prefs(ctx).edit()
                .putString(KEY_GLOBAL_BRAND, (brand == null || brand.trim().isEmpty()) ? "Apple" : brand.trim())
                .putString(KEY_GLOBAL_MODEL, (model == null || model.trim().isEmpty()) ? "iPhone 16 Pro Max" : model.trim())
                .commit();
    }

    public static boolean isGlobalLocationEnabled(Context ctx) {
        return prefs(ctx).getBoolean(KEY_GLOBAL_LOC_ENABLED, true);
    }

    public static void setGlobalLocationEnabled(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean(KEY_GLOBAL_LOC_ENABLED, enabled).commit();
    }

    public static String getGlobalRegionName(Context ctx) {
        return prefs(ctx).getString(KEY_GLOBAL_REGION, "Falkenstein, Germany");
    }

    public static void setGlobalRegionName(Context ctx, String region) {
        prefs(ctx).edit().putString(KEY_GLOBAL_REGION,
                (region == null || region.trim().isEmpty()) ? "Falkenstein, Germany" : region.trim()).commit();
    }

    public static double[] getGlobalCoordinates(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        double lat = Double.longBitsToDouble(sp.getLong(KEY_GLOBAL_LAT, Double.doubleToLongBits(50.4779)));
        double lon = Double.longBitsToDouble(sp.getLong(KEY_GLOBAL_LON, Double.doubleToLongBits(12.3713)));
        return new double[]{lat, lon};
    }

    public static void setGlobalCoordinates(Context ctx, double lat, double lon) {
        prefs(ctx).edit()
                .putLong(KEY_GLOBAL_LAT, Double.doubleToLongBits(lat))
                .putLong(KEY_GLOBAL_LON, Double.doubleToLongBits(lon))
                .commit();
    }

    public static String getGlobalVirtualIp(Context ctx) {
        return prefs(ctx).getString(KEY_GLOBAL_VIRTUAL_IP, "88.198.24.108");
    }

    public static void setGlobalVirtualIp(Context ctx, String ip) {
        prefs(ctx).edit().putString(KEY_GLOBAL_VIRTUAL_IP, ip == null ? "" : ip.trim()).commit();
    }

    public static String getGlobalProxyHost(Context ctx) {
        return prefs(ctx).getString(KEY_GLOBAL_PROXY_HOST, "");
    }

    public static int getGlobalProxyPort(Context ctx) {
        return prefs(ctx).getInt(KEY_GLOBAL_PROXY_PORT, 0);
    }

    public static void setGlobalProxy(Context ctx, String host, int port) {
        prefs(ctx).edit()
                .putString(KEY_GLOBAL_PROXY_HOST, host == null ? "" : host.trim())
                .putInt(KEY_GLOBAL_PROXY_PORT, Math.max(0, port))
                .commit();
    }

    public static String getCustomAlias(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getString(prefix(pkg, spaceId) + "alias", "");
    }

    public static void setCustomAlias(Context ctx, String pkg, int spaceId, String alias) {
        prefs(ctx).edit().putString(prefix(pkg, spaceId) + "alias", alias == null ? "" : alias.trim()).commit();
    }

    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getBoolean(prefix(pkg, spaceId) + "has_custom_device", false);
    }

    public static void setCustomDeviceIdentity(Context ctx, String pkg, int spaceId, String brand, String model) {
        prefs(ctx).edit()
                .putBoolean(prefix(pkg, spaceId) + "has_custom_device", true)
                .putString(prefix(pkg, spaceId) + "brand", brand == null ? "Apple" : brand.trim())
                .putString(prefix(pkg, spaceId) + "model", model == null ? "iPhone 16 Pro Max" : model.trim())
                .commit();
    }

    public static void clearCustomDeviceIdentity(Context ctx, String pkg, int spaceId) {
        prefs(ctx).edit()
                .putBoolean(prefix(pkg, spaceId) + "has_custom_device", false)
                .remove(prefix(pkg, spaceId) + "brand")
                .remove(prefix(pkg, spaceId) + "model")
                .commit();
    }

    public static String getEffectiveDeviceBrand(Context ctx, String pkg, int spaceId) {
        if (hasCustomDeviceIdentity(ctx, pkg, spaceId)) {
            return prefs(ctx).getString(prefix(pkg, spaceId) + "brand", getGlobalDeviceBrand(ctx));
        }
        return getGlobalDeviceBrand(ctx);
    }

    public static String getEffectiveDeviceModel(Context ctx, String pkg, int spaceId) {
        if (hasCustomDeviceIdentity(ctx, pkg, spaceId)) {
            return prefs(ctx).getString(prefix(pkg, spaceId) + "model", getGlobalDeviceModel(ctx));
        }
        return getGlobalDeviceModel(ctx);
    }

    public static boolean hasCustomLocation(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getBoolean(prefix(pkg, spaceId) + "has_custom_loc", false);
    }

    public static void setCustomLocation(Context ctx, String pkg, int spaceId, double lat, double lon, String regionName) {
        prefs(ctx).edit()
                .putBoolean(prefix(pkg, spaceId) + "has_custom_loc", true)
                .putLong(prefix(pkg, spaceId) + "lat", Double.doubleToLongBits(lat))
                .putLong(prefix(pkg, spaceId) + "lon", Double.doubleToLongBits(lon))
                .putString(prefix(pkg, spaceId) + "region",
                        (regionName == null || regionName.trim().isEmpty()) ? "Falkenstein, Germany" : regionName.trim())
                .commit();
    }

    public static void clearCustomLocation(Context ctx, String pkg, int spaceId) {
        prefs(ctx).edit()
                .putBoolean(prefix(pkg, spaceId) + "has_custom_loc", false)
                .remove(prefix(pkg, spaceId) + "lat")
                .remove(prefix(pkg, spaceId) + "lon")
                .remove(prefix(pkg, spaceId) + "region")
                .commit();
    }

    public static String getEffectiveRegionName(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            return prefs(ctx).getString(prefix(pkg, spaceId) + "region", getGlobalRegionName(ctx));
        }
        return getGlobalRegionName(ctx);
    }

    public static double[] getEffectiveCoordinates(Context ctx, String pkg, int spaceId) {
        if (hasCustomLocation(ctx, pkg, spaceId)) {
            SharedPreferences sp = prefs(ctx);
            double[] g = getGlobalCoordinates(ctx);
            double lat = Double.longBitsToDouble(sp.getLong(prefix(pkg, spaceId) + "lat", Double.doubleToLongBits(g[0])));
            double lon = Double.longBitsToDouble(sp.getLong(prefix(pkg, spaceId) + "lon", Double.doubleToLongBits(g[1])));
            return new double[]{lat, lon};
        }
        return getGlobalCoordinates(ctx);
    }

    public static Map<String, String> getAvailableDevicePresets() {
        Map<String, String> map = new LinkedHashMap<>();
        map.put("iPhone 16 Pro Max", "Apple");
        map.put("iPhone 15 Pro Max", "Apple");
        map.put("iPhone 14 Pro", "Apple");
        map.put("iPad Pro M4", "Apple");
        map.put("Samsung Galaxy S24 Ultra", "samsung");
        map.put("Samsung Galaxy S23 Ultra", "samsung");
        map.put("Google Pixel 9 Pro XL", "Google");
        map.put("Google Pixel 8 Pro", "Google");
        map.put("Xiaomi 14 Ultra", "Xiaomi");
        map.put("OnePlus 12", "OnePlus");
        map.put("Huawei Pura 70 Ultra", "HUAWEI");
        return map;
    }

    public static List<RegionPreset> getAvailableRegionPresets() {
        List<RegionPreset> list = new ArrayList<>();
        list.add(new RegionPreset("Falkenstein, Germany", 50.4779, 12.3713, "88.198.24.108", "Europe/Berlin"));
        list.add(new RegionPreset("Frankfurt, Germany", 50.1109, 8.6821, "138.201.81.199", "Europe/Berlin"));
        list.add(new RegionPreset("Amsterdam, Netherlands", 52.3676, 4.9041, "95.211.198.44", "Europe/Amsterdam"));
        list.add(new RegionPreset("New York, USA", 40.7128, -74.0060, "64.225.28.110", "America/New_York"));
        list.add(new RegionPreset("London, United Kingdom", 51.5074, -0.1278, "51.140.104.22", "Europe/London"));
        list.add(new RegionPreset("Helsinki, Finland", 60.1699, 24.9384, "65.108.44.19", "Europe/Helsinki"));
        list.add(new RegionPreset("Istanbul, Turkey", 41.0082, 28.9784, "185.125.33.12", "Europe/Istanbul"));
        list.add(new RegionPreset("Dubai, UAE", 25.2048, 55.2708, "94.200.14.88", "Asia/Dubai"));
        list.add(new RegionPreset("Tehran, Iran", 35.6892, 51.3890, "5.160.120.41", "Asia/Tehran"));
        return list;
    }
}
""",
)

# 9. VIRTUAL HOOK MANAGER & ENGINE
write_file(
    f"{JAVA_BASE}/core/VirtualHookManager.java",
    """package com.veyravault.space.core;

import android.content.Context;
import android.os.Build;
import java.lang.reflect.Field;
import java.util.TimeZone;

public class VirtualHookManager {

    public static void initializeGlobalHooks(Context ctx) {
        String brand = CloneMetadataStore.getGlobalDeviceBrand(ctx);
        String model = CloneMetadataStore.getGlobalDeviceModel(ctx);
        double[] coords = CloneMetadataStore.getGlobalCoordinates(ctx);
        String region = CloneMetadataStore.getGlobalRegionName(ctx);
        applyHardwareIdentity(brand, model);
        applyLocationAndRegionProperties(ctx, coords[0], coords[1], region);
    }

    public static void prepareForCloneLaunch(Context ctx, String pkg, int spaceId) {
        String brand = CloneMetadataStore.getEffectiveDeviceBrand(ctx, pkg, spaceId);
        String model = CloneMetadataStore.getEffectiveDeviceModel(ctx, pkg, spaceId);
        double[] coords = CloneMetadataStore.getEffectiveCoordinates(ctx, pkg, spaceId);
        String region = CloneMetadataStore.getEffectiveRegionName(ctx, pkg, spaceId);
        applyHardwareIdentity(brand, model);
        applyLocationAndRegionProperties(ctx, coords[0], coords[1], region);
    }

    private static void applyHardwareIdentity(String brand, String model) {
        try {
            setStaticField(Build.class, "BRAND", brand);
            setStaticField(Build.class, "MANUFACTURER", brand);
            setStaticField(Build.class, "MODEL", model);
            setStaticField(Build.class, "PRODUCT", model);
            setStaticField(Build.class, "DEVICE", model.replace(" ", "_"));
            System.setProperty("veyra.spoof.brand", brand);
            System.setProperty("veyra.spoof.model", model);
        } catch (Throwable ignored) {
        }
    }

    private static void applyLocationAndRegionProperties(Context ctx, double lat, double lon, String region) {
        try {
            System.setProperty("veyra.spoof.lat", String.valueOf(lat));
            System.setProperty("veyra.spoof.lon", String.valueOf(lon));
            System.setProperty("veyra.spoof.region", region);
            System.setProperty("veyra.spoof.ip", CloneMetadataStore.getGlobalVirtualIp(ctx));

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

            String lower = region == null ? "" : region.toLowerCase();
            if (lower.contains("germany") || lower.contains("falkenstein") || lower.contains("frankfurt")) {
                TimeZone.setDefault(TimeZone.getTimeZone("Europe/Berlin"));
            } else if (lower.contains("netherlands") || lower.contains("amsterdam")) {
                TimeZone.setDefault(TimeZone.getTimeZone("Europe/Amsterdam"));
            } else if (lower.contains("usa") || lower.contains("new york")) {
                TimeZone.setDefault(TimeZone.getTimeZone("America/New_York"));
            } else if (lower.contains("uk") || lower.contains("london") || lower.contains("united kingdom")) {
                TimeZone.setDefault(TimeZone.getTimeZone("Europe/London"));
            }
        } catch (Throwable ignored) {
        }
    }

    private static void setStaticField(Class<?> cls, String fieldName, Object val) {
        try {
            Field f = cls.getDeclaredField(fieldName);
            f.setAccessible(true);
            f.set(null, val);
        } catch (Throwable ignored) {
        }
    }
}
""",
)

write_file(
    f"{JAVA_BASE}/core/Engine.java",
    """package com.veyravault.space.core;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Build;
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
    private static final String PREF_VAULT = "veyra_independent_vault_v3";

    public static class ClonedApp {
        public String packageName;
        public String name;
        public Drawable icon;
        public int spaceId;
        public String customDeviceName;
        public boolean hasCustomDevice;
        public String effectiveRegion;
        public boolean hasCustomLoc;
    }

    public static class InstallOptionCandidate {
        public String packageName;
        public String name;
        public Drawable icon;
        public String sourceDir;
    }

    public static int[] getSpaces() {
        return new int[]{0, 1, 2};
    }

    private static File getVaultDirForPackage(Context ctx, String pkg) {
        File dir = new File(ctx.getFilesDir(), "apk_vault/" + pkg);
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    public static File getVaultBaseApk(Context ctx, String pkg) {
        return new File(getVaultDirForPackage(ctx, pkg), "base.apk");
    }

    private static void registerSpaceClone(Context ctx, String pkg, int spaceId) {
        SharedPreferences sp = ctx.getSharedPreferences(PREF_VAULT, Context.MODE_PRIVATE);
        Set<String> set = new HashSet<>(sp.getStringSet("space_pkgs_" + spaceId, new HashSet<String>()));
        set.add(pkg);
        sp.edit().putStringSet("space_pkgs_" + spaceId, set).commit();
    }

    private static void unregisterSpaceClone(Context ctx, String pkg, int spaceId) {
        SharedPreferences sp = ctx.getSharedPreferences(PREF_VAULT, Context.MODE_PRIVATE);
        Set<String> set = new HashSet<>(sp.getStringSet("space_pkgs_" + spaceId, new HashSet<String>()));
        set.remove(pkg);
        sp.edit().putStringSet("space_pkgs_" + spaceId, set).commit();
    }

    private static Set<String> getRegisteredSpacePackages(Context ctx, int spaceId) {
        SharedPreferences sp = ctx.getSharedPreferences(PREF_VAULT, Context.MODE_PRIVATE);
        return new HashSet<>(sp.getStringSet("space_pkgs_" + spaceId, new HashSet<String>()));
    }

    private static void backupPackageApksToVault(Context ctx, String pkg) {
        try {
            PackageInfo pi = ctx.getPackageManager().getPackageInfo(pkg, 0);
            if (pi == null || pi.applicationInfo == null) return;
            File vaultDir = getVaultDirForPackage(ctx, pkg);
            File srcBase = new File(pi.applicationInfo.sourceDir);
            File dstBase = new File(vaultDir, "base.apk");
            if (srcBase.exists() && (!dstBase.exists() || dstBase.length() != srcBase.length())) {
                copyFile(srcBase, dstBase);
            }
            if (Build.VERSION.SDK_INT >= 21 && pi.applicationInfo.splitSourceDirs != null) {
                int idx = 0;
                for (String splitPath : pi.applicationInfo.splitSourceDirs) {
                    File splitFile = new File(splitPath);
                    if (splitFile.exists()) {
                        copyFile(splitFile, new File(vaultDir, "split_" + idx + ".apk"));
                        idx++;
                    }
                }
            }
            extractNativeLibsFromVault(vaultDir);
        } catch (Throwable ignored) {
        }
    }

    private static void extractNativeLibsFromVault(File vaultDir) {
        File libOutDir = new File(vaultDir, "lib");
        if (!libOutDir.exists()) libOutDir.mkdirs();
        File[] apks = vaultDir.listFiles();
        if (apks == null) return;
        String preferAbi = (Build.SUPPORTED_64_BIT_ABIS != null && Build.SUPPORTED_64_BIT_ABIS.length > 0)
                ? "arm64-v8a" : "armeabi-v7a";
        for (File f : apks) {
            if (!f.getName().endsWith(".apk")) continue;
            ZipFile zf = null;
            try {
                zf = new ZipFile(f);
                Enumeration<? extends ZipEntry> entries = zf.entries();
                while (entries.hasMoreElements()) {
                    ZipEntry ze = entries.nextElement();
                    String name = ze.getName();
                    if (name.startsWith("lib/") && name.endsWith(".so")) {
                        if (name.contains(preferAbi) || name.contains("armeabi")) {
                            String soName = name.substring(name.lastIndexOf('/') + 1);
                            File outSo = new File(libOutDir, soName);
                            if (!outSo.exists() || outSo.length() != ze.getSize()) {
                                InputStream is = zf.getInputStream(ze);
                                FileOutputStream fos = new FileOutputStream(outSo);
                                byte[] buf = new byte[16384];
                                int r;
                                while ((r = is.read(buf)) != -1) fos.write(buf, 0, r);
                                fos.close();
                                is.close();
                            }
                        }
                    }
                }
            } catch (Throwable ignored) {
            } finally {
                try {
                    if (zf != null) zf.close();
                } catch (Throwable ignored) {
                }
            }
        }
    }

    private static void copyFile(File src, File dst) throws Exception {
        FileInputStream fis = new FileInputStream(src);
        FileOutputStream fos = new FileOutputStream(dst);
        byte[] buf = new byte[32768];
        int len;
        while ((len = fis.read(buf)) > 0) {
            fos.write(buf, 0, len);
        }
        fos.flush();
        fos.close();
        fis.close();
    }

    public static List<ClonedApp> getClonedApps(Context ctx, int spaceId) {
        List<ClonedApp> result = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Set<String> tracked = getRegisteredSpacePackages(ctx, spaceId);

        try {
            List<ApplicationInfo> bApps = BlackBoxCore.get().getInstalledApplications(0, spaceId);
            if (bApps != null) {
                for (ApplicationInfo ai : bApps) {
                    if (ai != null && ai.packageName != null) {
                        tracked.add(ai.packageName);
                    }
                }
            }
        } catch (Throwable ignored) {
        }

        for (String pkg : tracked) {
            if (pkg == null || pkg.equals(ctx.getPackageName())) continue;
            if (pkg.startsWith("com.google.android.gms") || pkg.startsWith("com.google.android.gsf")) continue;

            ClonedApp item = new ClonedApp();
            item.packageName = pkg;
            item.spaceId = spaceId;
            item.hasCustomDevice = CloneMetadataStore.hasCustomDeviceIdentity(ctx, pkg, spaceId);
            item.customDeviceName = CloneMetadataStore.getEffectiveDeviceModel(ctx, pkg, spaceId);
            item.hasCustomLoc = CloneMetadataStore.hasCustomLocation(ctx, pkg, spaceId);
            item.effectiveRegion = CloneMetadataStore.getEffectiveRegionName(ctx, pkg, spaceId);

            boolean resolved = false;
            try {
                ApplicationInfo hostAi = pm.getApplicationInfo(pkg, 0);
                item.name = hostAi.loadLabel(pm).toString();
                item.icon = hostAi.loadIcon(pm);
                resolved = true;
            } catch (Throwable ignored) {
            }

            if (!resolved) {
                File vaultApk = getVaultBaseApk(ctx, pkg);
                if (vaultApk.exists()) {
                    try {
                        PackageInfo archivePi = pm.getPackageArchiveInfo(vaultApk.getAbsolutePath(), 0);
                        if (archivePi != null && archivePi.applicationInfo != null) {
                            archivePi.applicationInfo.sourceDir = vaultApk.getAbsolutePath();
                            archivePi.applicationInfo.publicSourceDir = vaultApk.getAbsolutePath();
                            item.name = archivePi.applicationInfo.loadLabel(pm).toString();
                            item.icon = archivePi.applicationInfo.loadIcon(pm);
                            resolved = true;
                        }
                    } catch (Throwable ignored) {
                    }
                }
            }

            if (!resolved) {
                item.name = pkg;
                item.icon = ctx.getApplicationInfo().loadIcon(pm);
            }

            String alias = CloneMetadataStore.getCustomAlias(ctx, pkg, spaceId);
            if (alias != null && !alias.trim().isEmpty()) {
                item.name = alias.trim();
            }

            result.add(item);
        }
        return result;
    }

    public static List<InstallOptionCandidate> getInstalledHostApps(Context ctx) {
        List<InstallOptionCandidate> list = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Intent mainIntent = new Intent(Intent.ACTION_MAIN, null);
        mainIntent.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> infos = pm.queryIntentActivities(mainIntent, 0);
        Set<String> seen = new HashSet<>();
        if (infos != null) {
            for (ResolveInfo ri : infos) {
                if (ri.activityInfo == null) continue;
                String pkg = ri.activityInfo.packageName;
                if (pkg == null || pkg.equals(ctx.getPackageName()) || seen.contains(pkg)) continue;
                seen.add(pkg);
                InstallOptionCandidate c = new InstallOptionCandidate();
                c.packageName = pkg;
                c.name = ri.loadLabel(pm).toString();
                c.icon = ri.loadIcon(pm);
                c.sourceDir = ri.activityInfo.applicationInfo.sourceDir;
                list.add(c);
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

    public static boolean cloneApp(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.ensureGmsEnabled(ctx, spaceId);
            backupPackageApksToVault(ctx, pkg);
            registerSpaceClone(ctx, pkg, spaceId);
            File vaultApk = getVaultBaseApk(ctx, pkg);
            InstallResult res;
            if (vaultApk.exists()) {
                res = BlackBoxCore.get().installPackageAsUser(vaultApk, spaceId);
                if (res == null || !res.success) {
                    res = BlackBoxCore.get().installPackageAsUser(pkg, spaceId);
                }
            } else {
                res = BlackBoxCore.get().installPackageAsUser(pkg, spaceId);
            }
            return true;
        } catch (Throwable t) {
            registerSpaceClone(ctx, pkg, spaceId);
            return true;
        }
    }

    public static boolean installApkIntoSpaceOnly(Context ctx, String apkPath, int spaceId) {
        try {
            File src = new File(apkPath);
            if (!src.exists()) return false;
            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(src.getAbsolutePath(), 0);
            if (pi == null || pi.packageName == null) return false;
            String pkg = pi.packageName;

            File vaultDir = getVaultDirForPackage(ctx, pkg);
            File dstBase = new File(vaultDir, "base.apk");
            copyFile(src, dstBase);
            extractNativeLibsFromVault(vaultDir);

            GmsSupportManager.ensureGmsEnabled(ctx, spaceId);
            registerSpaceClone(ctx, pkg, spaceId);
            BlackBoxCore.get().installPackageAsUser(dstBase, spaceId);
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    public static void promptHostInstallForApk(Context ctx, String apkPath) {
        try {
            File f = new File(apkPath);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(Uri.fromFile(f), "application/vnd.android.package-archive");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_GRANT_READ_URI_PERMISSION);
            ctx.startActivity(intent);
        } catch (Throwable ignored) {
        }
    }

    public static void launchClone(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.ensureGmsEnabled(ctx, spaceId);
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, spaceId);
            BlackBoxCore core = BlackBoxCore.get();

            File vaultApk = getVaultBaseApk(ctx, pkg);
            if (!core.isInstalled(pkg, spaceId) && vaultApk.exists()) {
                core.installPackageAsUser(vaultApk, spaceId);
            }

            if ("com.android.chrome".equals(pkg) || "com.chrome.beta".equals(pkg)) {
                Intent chromeMain = new Intent(Intent.ACTION_MAIN);
                chromeMain.addCategory(Intent.CATEGORY_LAUNCHER);
                chromeMain.setPackage(pkg);
                chromeMain.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
                chromeMain.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                boolean launched = core.launchApk(pkg, spaceId);
                if (!launched) {
                    ctx.startActivity(chromeMain);
                }
                return;
            }

            boolean ok = core.launchApk(pkg, spaceId);
            if (!ok && vaultApk.exists()) {
                core.installPackageAsUser(vaultApk, spaceId);
                core.launchApk(pkg, spaceId);
            }
        } catch (Throwable ignored) {
        }
    }

    public static void removeClone(Context ctx, String pkg, int spaceId) {
        try {
            unregisterSpaceClone(ctx, pkg, spaceId);
            CloneMetadataStore.clearCustomDeviceIdentity(ctx, pkg, spaceId);
            CloneMetadataStore.clearCustomLocation(ctx, pkg, spaceId);
            BlackBoxCore.get().uninstallPackageAsUser(pkg, spaceId);
        } catch (Throwable ignored) {
        }
    }
}
""",
)

# 10. SECURITY MANAGER & VAULT DEVICE ADMIN RECEIVER
write_file(
    f"{JAVA_BASE}/security/SecurityManager.java",
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
    private static final String KEY_PIN_HASH = "pin_hash";
    private static final String KEY_PATTERN_HASH = "pattern_hash";
    private static final String KEY_PRIORITY = "lock_priority";
    private static final String KEY_ADMIN_AUTH_UNINSTALL = "authorized_uninstall";

    public static final int LOCK_NONE = 0;
    public static final int LOCK_PIN = 1;
    public static final int LOCK_PATTERN = 2;

    private static boolean sessionUnlocked = false;

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    private static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] b = md.digest(input.getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte v : b) sb.append(String.format("%02x", v));
            return sb.toString();
        } catch (Exception e) {
            return input;
        }
    }

    public static boolean hasPin(Context ctx) {
        return !prefs(ctx).getString(KEY_PIN_HASH, "").isEmpty();
    }

    public static boolean hasPattern(Context ctx) {
        return !prefs(ctx).getString(KEY_PATTERN_HASH, "").isEmpty();
    }

    public static boolean isLockConfigured(Context ctx) {
        return hasPin(ctx) || hasPattern(ctx);
    }

    public static void setPin(Context ctx, String pin) {
        prefs(ctx).edit().putString(KEY_PIN_HASH, sha256(pin.trim())).commit();
        sessionUnlocked = true;
    }

    public static void setPattern(Context ctx, String pattern) {
        prefs(ctx).edit().putString(KEY_PATTERN_HASH, sha256(pattern.trim())).commit();
        sessionUnlocked = true;
    }

    public static boolean verifyPin(Context ctx, String pin) {
        if (pin == null) return false;
        String stored = prefs(ctx).getString(KEY_PIN_HASH, "");
        return !stored.isEmpty() && stored.equals(sha256(pin.trim()));
    }

    public static boolean verifyPattern(Context ctx, String pattern) {
        if (pattern == null) return false;
        String stored = prefs(ctx).getString(KEY_PATTERN_HASH, "");
        return !stored.isEmpty() && stored.equals(sha256(pattern.trim()));
    }

    public static int getPrimaryLockPriority(Context ctx) {
        int pref = prefs(ctx).getInt(KEY_PRIORITY, LOCK_PIN);
        if (pref == LOCK_PIN && hasPin(ctx)) return LOCK_PIN;
        if (pref == LOCK_PATTERN && hasPattern(ctx)) return LOCK_PATTERN;
        if (hasPin(ctx)) return LOCK_PIN;
        if (hasPattern(ctx)) return LOCK_PATTERN;
        return LOCK_NONE;
    }

    public static void setPrimaryLockPriority(Context ctx, int priority) {
        prefs(ctx).edit().putInt(KEY_PRIORITY, priority).commit();
    }

    public static void disableAllLocks(Context ctx) {
        prefs(ctx).edit()
                .remove(KEY_PIN_HASH)
                .remove(KEY_PATTERN_HASH)
                .commit();
        sessionUnlocked = true;
    }

    public static boolean isSessionUnlocked() {
        return sessionUnlocked;
    }

    public static void setSessionUnlocked(boolean unlocked) {
        sessionUnlocked = unlocked;
    }

    public static boolean isAuthorizedAdminDeactivation(Context ctx) {
        return prefs(ctx).getBoolean(KEY_ADMIN_AUTH_UNINSTALL, false);
    }

    public static void setAuthorizedAdminDeactivation(Context ctx, boolean allowed) {
        prefs(ctx).edit().putBoolean(KEY_ADMIN_AUTH_UNINSTALL, allowed).commit();
    }

    public static boolean isDeviceAdminActive(Context ctx) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
            return dpm != null && dpm.isAdminActive(cn);
        } catch (Throwable t) {
            return false;
        }
    }

    public static void requestEnableDeviceAdmin(Activity act, int reqCode) {
        try {
            setAuthorizedAdminDeactivation(act, false);
            ComponentName cn = new ComponentName(act, VaultDeviceAdminReceiver.class);
            Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
            intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, cn);
            intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                    "فعال‌سازی محافظ امنیتی ضدحذف VeyraVault");
            act.startActivityForResult(intent, reqCode);
        } catch (Throwable ignored) {
        }
    }

    public static void disableDeviceAdminByAuthorizedOwner(Context ctx) {
        try {
            setAuthorizedAdminDeactivation(ctx, true);
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
            if (dpm != null && dpm.isAdminActive(cn)) {
                dpm.removeActiveAdmin(cn);
            }
        } catch (Throwable ignored) {
        }
    }
}
""",
)

write_file(
    f"{JAVA_BASE}/security/VaultDeviceAdminReceiver.java",
    """package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    @Override
    public void onEnabled(Context context, Intent intent) {
        SecurityManager.setAuthorizedAdminDeactivation(context, false);
    }

    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        if (!SecurityManager.isAuthorizedAdminDeactivation(context)) {
            SecurityManager.setSessionUnlocked(false);
            try {
                Intent lockIntent = new Intent(context, SecurityLockActivity.class);
                lockIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                lockIntent.putExtra("anti_uninstall_intercept", true);
                context.startActivity(lockIntent);
            } catch (Throwable ignored) {
            }
        }
        return "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است.";
    }
}
""",
)

# 11. VEYRA APPLICATION
write_file(
    f"{JAVA_BASE}/VeyraApplication.java",
    """package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.helper.GmsSupportManager;
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
        try {
            BlackBoxCore.get().doCreate();
            VirtualHookManager.initializeGlobalHooks(this);
            GmsSupportManager.enableGmsForAllSpaces(this);
        } catch (Throwable ignored) {
        }
    }
}
""",
)


def patch_part2():
    part2_path = os.path.join(ROOT, "scripts", "upgrade_v3_part2.py")
    if os.path.exists(part2_path):
        with open(part2_path, "r", encoding="utf-8") as f:
            txt = f.read()
        txt = txt.replace("Gravity.CENTER_horizontal", "Gravity.CENTER_HORIZONTAL")
        if "import com.veyravault.space.helper.PatternLockView;" not in txt:
            txt = txt.replace(
                "import com.veyravault.space.security.SecurityManager;",
                "import com.veyravault.space.security.SecurityManager;\nimport com.veyravault.space.helper.PatternLockView;",
            )
        with open(part2_path, "w", encoding="utf-8") as f:
            f.write(txt)
        print("[v3.0-Part1] Patched upgrade_v3_part2.py imports and constants.")


patch_part2()
print("[v3.0-Part1] Core v3.0 infrastructure generated successfully.")
