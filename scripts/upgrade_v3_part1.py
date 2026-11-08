#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[v3-part1] Wrote: {path}")

for clean_dir in [
    "app/src/main/java/com/veyravault/space",
    "build_workspace/app/src/main/java/com/veyravault/space",
]:
    if os.path.exists(clean_dir):
        shutil.rmtree(clean_dir)

APP_BASE = "app/src/main"
JAVA_BASE = os.path.join(APP_BASE, "java/com/veyravault/space")
RES_BASE = os.path.join(APP_BASE, "res")
ASSETS_BASE = os.path.join(APP_BASE, "assets")

NOTICE_CONTENT = """
VeyraVault Virtualization Engine & Multi-Space Sandbox
Copyright (c) 2024-2025 VeyraVault Project (Vaultveyra@gmail.com | https://t.me/VaultVeyra)
Licensed under the Apache License, Version 2.0.
"""
write_file(os.path.join(ASSETS_BASE, "NOTICE_APACHE_2.txt"), NOTICE_CONTENT)

MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
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
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.KILL_BACKGROUND_PROCESSES" />

    <application
        android:name=".VeyraApplication"
        android:allowBackup="true"
        android:icon="@drawable/ic_launcher"
        android:roundIcon="@drawable/ic_launcher_round"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:largeHeap="true"
        android:usesCleartextTraffic="true"
        android:requestLegacyExternalStorage="true"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar"
        tools:replace="android:name,android:label,android:icon,android:roundIcon,android:theme,android:allowBackup,android:supportsRtl">

        <activity
            android:name=".ui.MainActivity"
            android:exported="true"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden"
            android:launchMode="singleTask">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity android:name=".ui.AddAppActivity" android:exported="false" android:configChanges="locale|layoutDirection|orientation|screenSize" />
        <activity android:name=".ui.GlobalEnvironmentActivity" android:exported="false" android:configChanges="locale|layoutDirection|orientation|screenSize" />
        <activity android:name=".ui.SetLocationActivity" android:exported="false" android:configChanges="locale|layoutDirection|orientation|screenSize" />
        <activity android:name=".ui.SecuritySettingsActivity" android:exported="false" android:configChanges="locale|layoutDirection|orientation|screenSize" />
        <activity android:name=".ui.SecurityLockActivity" android:exported="false" android:launchMode="singleTop" android:configChanges="locale|layoutDirection|orientation|screenSize" />
        <activity android:name=".ui.GuideActivity" android:exported="false" android:configChanges="locale|layoutDirection|orientation|screenSize" />
        <activity android:name=".ui.AboutActivity" android:exported="false" android:configChanges="locale|layoutDirection|orientation|screenSize" />

        <receiver
            android:name=".security.VaultDeviceAdminReceiver"
            android:description="@string/admin_receiver_desc"
            android:label="@string/admin_receiver_label"
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

        <service
            android:name=".core.VaultNotificationListenerService"
            android:label="VeyraVault Notification Counter"
            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"
            android:exported="true">
            <intent-filter>
                <action android:name="android.service.notification.NotificationListenerService" />
            </intent-filter>
        </service>

        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>

    </application>
</manifest>
"""
write_file(os.path.join(APP_BASE, "AndroidManifest.xml"), MANIFEST)

IC_LAUNCHER_XML = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#0F172A" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#1E293B" android:pathData="M54,14 L88,28 L88,56 C88,77 73,91 54,96 C35,91 20,77 20,56 L20,28 Z"/>
    <path android:fillColor="#3B82F6" android:pathData="M54,20 L82,32 L82,55 C82,72 69,84 54,89 C39,84 26,72 26,55 L26,32 Z"/>
    <path android:fillColor="#FFFFFF" android:pathData="M40,40 L54,72 L68,40 L60,40 L54,56 L48,40 Z"/>
</vector>
"""
write_file(os.path.join(RES_BASE, "drawable/ic_launcher.xml"), IC_LAUNCHER_XML)
write_file(os.path.join(RES_BASE, "drawable/ic_launcher_round.xml"), IC_LAUNCHER_XML)

NAV_ICONS = {
    "ic_nav_dashboard.xml": "M3,13h8V3H3V13z M3,21h8v-6H3V21z M13,21h8V11h-8V21z M13,3v6h8V3H13z",
    "ic_nav_spaces.xml": "M4,8h4V4H4V8z M10,20h4v-4h-4V20z M4,20h4v-4H4V20z M4,14h4v-4H4V14z M10,14h4v-4h-4V14z M16,4v4h4V4H16z M10,8h4V4h-4V8z M16,14h4v-4h-4V14z M16,20h4v-4h-4V20z",
    "ic_nav_add.xml": "M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6V13z",
    "ic_nav_guide.xml": "M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM11,19.93c-3.95,-0.49 -7,-3.85 -7,-7.93 0,-0.62 0.08,-1.21 0.21,-1.79L9,15v1c0,1.1 0.9,2 2,2v1.93zM17.9,17.39c-0.26,-0.81 -1,-1.39 -1.9,-1.39h-1v-3c0,-0.55 -0.45,-1 -1,-1H8v-2h2c0.55,0 1,-0.45 1,-1V7h2c1.1,0 2,-0.9 2,-2v-0.41c2.93,1.19 5,4.06 5,7.41 0,2.08 -0.8,3.97 -2.1,5.39z",
    "ic_nav_settings.xml": "M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94z M12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"
}
for name, path_data in NAV_ICONS.items():
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="{path_data}"/>
</vector>"""
    write_file(os.path.join(RES_BASE, "drawable", name), xml)

DEVICE_ADMIN_XML = """<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <force-lock />
    </uses-policies>
</device-admin>
"""
write_file(os.path.join(RES_BASE, "xml/device_admin_receiver.xml"), DEVICE_ADMIN_XML)

FILE_PATHS_XML = """<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res/android">
    <external-path name="external_files" path="." />
    <files-path name="internal_files" path="." />
    <cache-path name="cache_files" path="." />
</paths>
"""
write_file(os.path.join(RES_BASE, "xml/file_paths.xml"), FILE_PATHS_XML)

STRINGS_XML = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="admin_receiver_label">محافظ امنیتی VeyraVault</string>
    <string name="admin_receiver_desc">حفاظت در برابر حذف غیرمجاز</string>
    <item name="ic_launcher" type="mipmap">@drawable/ic_launcher</item>
    <item name="ic_launcher_round" type="mipmap">@drawable/ic_launcher_round</item>
</resources>
"""
write_file(os.path.join(RES_BASE, "values/strings.xml"), STRINGS_XML)

VEYRA_APP = """package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.Engine;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.configuration.ClientConfiguration;

public class VeyraApplication extends Application {
    private static Context sContext;

    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        sContext = base;
        try {
            BlackBoxCore.get().doAttachBaseContext(base, new ClientConfiguration() {
                @Override
                public String getHostPackageName() {
                    return base.getPackageName();
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
            Engine.get(this).initialize();
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public static Context getAppContext() {
        return sContext;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "VeyraApplication.java"), VEYRA_APP)

JALALI_CLOCK = """package com.veyravault.space.helper;

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
    private static final String[] JALALI_WEEKDAYS_FA = {
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
        int jm = (days < 186) ? 1 + (days / 31) : 7 + ((days - 186) / 30);
        int jd = 1 + ((days < 186) ? (days % 31) : ((days - 186) % 30));
        return new int[]{jy, jm, jd};
    }

    public static String getIranTimeText() {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Tehran"));
        return String.format(Locale.US, "%02d:%02d:%02d",
                cal.get(Calendar.HOUR_OF_DAY), cal.get(Calendar.MINUTE), cal.get(Calendar.SECOND));
    }

    public static String getIranJalaliDateText(boolean isFa) {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Tehran"));
        int[] j = gregorianToJalali(cal.get(Calendar.YEAR), cal.get(Calendar.MONTH) + 1, cal.get(Calendar.DAY_OF_MONTH));
        int dow = cal.get(Calendar.DAY_OF_WEEK) - 1;
        if (isFa) {
            return JALALI_WEEKDAYS_FA[dow] + " " + j[2] + " " + JALALI_MONTHS_FA[j[1] - 1] + " " + j[0];
        }
        return String.format(Locale.US, "%04d/%02d/%02d (Solar Hijri)", j[0], j[1], j[2]);
    }

    public static String getUsaTimeText() {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("America/New_York"));
        return String.format(Locale.US, "%02d:%02d:%02d",
                cal.get(Calendar.HOUR_OF_DAY), cal.get(Calendar.MINUTE), cal.get(Calendar.SECOND));
    }

    public static String getUsaGregorianDateText() {
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, MMM dd, yyyy", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }
}
"""
write_file(os.path.join(JAVA_BASE, "helper/JalaliClockUtil.java"), JALALI_CLOCK)

LOCALE_HELPER = """package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.util.Locale;

public class LocaleHelper {
    private static final String PREF_NAME = "veyra_locale_prefs";
    private static final String KEY_LANG = "app_lang";
    private static final String KEY_LIGHT_THEME = "app_light_theme";

    public static String getLanguage(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        return sp.getString(KEY_LANG, "fa");
    }

    public static boolean isPersian(Context context) {
        return "fa".equalsIgnoreCase(getLanguage(context));
    }

    public static void setLanguage(Context context, String lang) {
        context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE).edit().putString(KEY_LANG, lang).commit();
    }

    public static String toggleLanguage(Context context) {
        String next = isPersian(context) ? "en" : "fa";
        setLanguage(context, next);
        return next;
    }

    public static boolean isLightTheme(Context context) {
        return context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE).getBoolean(KEY_LIGHT_THEME, false);
    }

    public static void setLightTheme(Context context, boolean light) {
        context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE).edit().putBoolean(KEY_LIGHT_THEME, light).commit();
    }

    public static boolean toggleLightTheme(Context context) {
        boolean next = !isLightTheme(context);
        setLightTheme(context, next);
        return next;
    }

    public static void applyThemeRecursive(View v, boolean light) {
        if (v == null || !light) return;
        if (v.getBackground() instanceof ColorDrawable) {
            int c = ((ColorDrawable) v.getBackground()).getColor();
            if (c == Color.parseColor("#0B0F19") || c == Color.parseColor("#080B12") || c == Color.parseColor("#0F172A")) {
                v.setBackgroundColor(Color.parseColor("#F1F5F9"));
            } else if (c == Color.parseColor("#161F33") || c == Color.parseColor("#1E293B")) {
                v.setBackgroundColor(Color.parseColor("#FFFFFF"));
            }
        }
        if (v instanceof TextView) {
            TextView tv = (TextView) v;
            int tc = tv.getCurrentTextColor();
            if (tc == Color.WHITE || tc == Color.parseColor("#F8FAFC") || tc == Color.parseColor("#E2E8F0") || tc == Color.parseColor("#CBD5E1")) {
                CharSequence txt = tv.getText();
                String s = txt != null ? txt.toString() : "";
                if (!s.startsWith("+") && !s.contains("🔒") && !s.contains("بهینه‌سازی فوری") && !s.contains("Optimize Now")) {
                    tv.setTextColor(Color.parseColor("#0F172A"));
                }
            } else if (tc == Color.parseColor("#94A3B8")) {
                tv.setTextColor(Color.parseColor("#475569"));
            }
        }
        if (v instanceof ViewGroup) {
            ViewGroup vg = (ViewGroup) v;
            for (int i = 0; i < vg.getChildCount(); i++) {
                applyThemeRecursive(vg.getChildAt(i), light);
            }
        }
    }

    public static Context wrap(Context context) {
        String lang = getLanguage(context);
        Locale locale = new Locale(lang);
        Locale.setDefault(locale);
        Resources res = context.getResources();
        Configuration config = new Configuration(res.getConfiguration());
        if (Build.VERSION.SDK_INT >= 17) {
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
write_file(os.path.join(JAVA_BASE, "helper/LocaleHelper.java"), LOCALE_HELPER)

BASE_ACTIVITY = """package com.veyravault.space.ui;

import android.app.Activity;
import android.content.Context;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.graphics.Color;
import com.veyravault.space.helper.LocaleHelper;

public class BaseActivity extends Activity {
    private String lastLang;
    private boolean lastTheme;

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.wrap(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        lastLang = LocaleHelper.getLanguage(this);
        lastTheme = LocaleHelper.isLightTheme(this);
        applyDirectionAndStatusBar();
    }

    @Override
    protected void onResume() {
        super.onResume();
        String currentLang = LocaleHelper.getLanguage(this);
        boolean currentTheme = LocaleHelper.isLightTheme(this);
        if ((lastLang != null && !lastLang.equals(currentLang)) || (lastTheme != currentTheme)) {
            lastLang = currentLang;
            lastTheme = currentTheme;
            recreate();
            return;
        }
        applyDirectionAndStatusBar();
        if (currentTheme && getWindow() != null && getWindow().getDecorView() != null) {
            LocaleHelper.applyThemeRecursive(getWindow().getDecorView(), true);
        }
    }

    protected void applyDirectionAndStatusBar() {
        boolean isFa = LocaleHelper.isPersian(this);
        boolean isLight = LocaleHelper.isLightTheme(this);
        if (Build.VERSION.SDK_INT >= 17 && getWindow() != null && getWindow().getDecorView() != null) {
            getWindow().getDecorView().setLayoutDirection(isFa ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        }
        if (Build.VERSION.SDK_INT >= 21 && getWindow() != null) {
            Window window = getWindow();
            window.clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS);
            window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
            window.setStatusBarColor(Color.parseColor(isLight ? "#E2E8F0" : "#0B0F19"));
            window.setNavigationBarColor(Color.parseColor(isLight ? "#FFFFFF" : "#080B12"));
        }
    }

    protected boolean isFa() {
        return LocaleHelper.isPersian(this);
    }

    protected String tr(String faText, String enText) {
        return isFa() ? faText : enText;
    }

    protected int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/BaseActivity.java"), BASE_ACTIVITY)

GMS_MANAGER = """package com.veyravault.space.helper;

import android.content.Context;
import android.content.pm.PackageManager;
import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    public static final String[] POISON_GMS_PACKAGES = {
        "com.google.android.gms",
        "com.google.android.gsf"
    };

    public static boolean isHostInstalled(Context ctx, String pkg) {
        try {
            ctx.getPackageManager().getPackageInfo(pkg, 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    public static void cleanPoisonedGmsInSpace(int userId) {
        try {
            for (String pkg : POISON_GMS_PACKAGES) {
                if (BlackBoxCore.get().isInstalled(pkg, userId)) {
                    BlackBoxCore.get().uninstallPackageAsUser(pkg, userId);
                }
            }
        } catch (Throwable ignored) {}
    }

    public static void ensureGmsInstalledForUser(Context ctx, int userId) {
        cleanPoisonedGmsInSpace(userId);
    }

    public static void ensureGmsForPackage(Context ctx, String pkg, int userId) {
        cleanPoisonedGmsInSpace(userId);
    }

    public static boolean isGmsReady(Context ctx, int userId) {
        return isHostInstalled(ctx, "com.google.android.gms");
    }
}
"""
write_file(os.path.join(JAVA_BASE, "helper/GmsSupportManager.java"), GMS_MANAGER)

APP_DISGUISE = """package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;

public class AppDisguiseManager {
    private static final String PREF = "veyra_disguise_prefs";
    public static final String MODE_DEFAULT = "default";
    public static final String MODE_CALCULATOR = "calculator";
    public static final String MODE_NOTEPAD = "notepad";

    public static String getDisguiseMode(Context ctx) {
        return ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).getString("mode", MODE_DEFAULT);
    }

    public static void setDisguiseMode(Context ctx, String mode) {
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putString("mode", mode).commit();
    }
}
"""
write_file(os.path.join(JAVA_BASE, "helper/AppDisguiseManager.java"), APP_DISGUISE)

PATTERN_VIEW = """package com.veyravault.space.helper;

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
        void onPatternComplete(String patternString);
    }

    private final List<Integer> selectedNodes = new ArrayList<>();
    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private float curX, curY;
    private boolean isDrawing = false;
    private OnPatternListener listener;

    public PatternLockView(Context context) {
        super(context);
        dotPaint.setColor(Color.parseColor("#475569"));
        dotPaint.setStyle(Paint.Style.FILL);
        activePaint.setColor(Color.parseColor("#3B82F6"));
        activePaint.setStyle(Paint.Style.FILL);
        linePaint.setColor(Color.parseColor("#60A5FA"));
        linePaint.setStrokeWidth(10f);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setOnPatternListener(OnPatternListener l) {
        this.listener = l;
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
            canvas.drawLine(getNodeX(last), getNodeY(last), curX, curY, linePaint);
        }
        float radius = Math.min(getWidth(), getHeight()) / 18f;
        for (int i = 0; i < 9; i++) {
            float x = getNodeX(i);
            float y = getNodeY(i);
            boolean active = selectedNodes.contains(i);
            canvas.drawCircle(x, y, active ? radius * 1.3f : radius, active ? activePaint : dotPaint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        curX = event.getX();
        curY = event.getY();
        float hitRadius = Math.min(getWidth(), getHeight()) / 8f;
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                selectedNodes.clear();
                isDrawing = true;
                checkHit(curX, curY, hitRadius);
                invalidate();
                return true;
            case MotionEvent.ACTION_MOVE:
                checkHit(curX, curY, hitRadius);
                invalidate();
                return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                isDrawing = false;
                if (!selectedNodes.isEmpty() && listener != null) {
                    StringBuilder sb = new StringBuilder();
                    for (int n : selectedNodes) {
                        if (sb.length() > 0) sb.append("-");
                        sb.append(n + 1);
                    }
                    listener.onPatternComplete(sb.toString());
                }
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y, float r) {
        for (int i = 0; i < 9; i++) {
            if (!selectedNodes.contains(i)) {
                float dx = x - getNodeX(i);
                float dy = y - getNodeY(i);
                if (Math.sqrt(dx * dx + dy * dy) <= r) {
                    selectedNodes.add(i);
                }
            }
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "helper/PatternLockView.java"), PATTERN_VIEW)

CLONE_METADATA = """package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

public class CloneMetadataStore {
    private static final String PREF = "veyra_clone_meta_v3";
    private static CloneMetadataStore sInstance;
    private final SharedPreferences sp;
    private final Context appCtx;

    public static class CloneMeta {
        public String packageName = "";
        public int userId = 0;
        public String customAlias = "";
        public boolean hasExclusiveDevice = false;
        public String deviceBrand = "";
        public String deviceModel = "";
        public String deviceManufacturer = "";
        public String deviceProduct = "";
        public String deviceHardware = "";
        public boolean hasExclusiveLocation = false;
        public double latitude = 0.0;
        public double longitude = 0.0;
        public String regionLabel = "";
        public String timezoneId = "";
        public String proxyAddress = "";
        public String virtualIp = "";
        public boolean hasExclusiveSim = false;
        public String simCountryIso = "us";
        public String simOperatorName = "T-Mobile USA";
        public String simOperatorNumeric = "310260";
        public String simPhoneNumber = "+13105550199";
    }

    public static class DevicePreset {
        public final String brand;
        public final String model;
        public final String manufacturer;
        public final String product;
        public final String hardware;
        public final String buildId;

        public DevicePreset(String brand, String model, String manufacturer, String product, String hardware, String buildId) {
            this.brand = brand;
            this.model = model;
            this.manufacturer = manufacturer;
            this.product = product;
            this.hardware = hardware;
            this.buildId = buildId;
        }
    }

    public static class VpnProfile {
        public String id;
        public String title;
        public String country;
        public String stateOrCity;
        public String protocol;
        public String host;
        public int port;
        public String username;
        public String password;
        public String timezoneId;
        public double lat;
        public double lon;
        public String simOperator;
        public String simMccMnc;
        public String simIso;
        public int targetSpaceId; // -1 = Global
    }

    public static final DevicePreset[] PRESETS = new DevicePreset[]{
        new DevicePreset("Apple", "iPhone 16 Pro Max", "Apple", "iPhone17,2", "A18Pro", "iOS18.2"),
        new DevicePreset("Apple", "iPhone 15 Pro Max", "Apple", "iPhone16,2", "A17Pro", "iOS17.6"),
        new DevicePreset("Apple", "iPhone 14 Pro", "Apple", "iPhone15,2", "A16Bionic", "iOS17.5"),
        new DevicePreset("Apple", "iPad Pro M4", "Apple", "iPad16,6", "AppleM4", "iPadOS18"),
        new DevicePreset("Samsung", "SM-S928B (Galaxy S24 Ultra)", "Samsung", "e3qxxx", "qcom", "UP1A.231005.007"),
        new DevicePreset("Samsung", "SM-S918B (Galaxy S23 Ultra)", "Samsung", "dm3qxxx", "qcom", "TP1A.220624.014"),
        new DevicePreset("Samsung", "SM-A546E (Galaxy A54 5G)", "Samsung", "a54xnsxx", "s5e8835", "UP1A.231005.007"),
        new DevicePreset("Google", "Pixel 9 Pro XL", "Google", "komodo", "tensor", "AD1A.240530.047"),
        new DevicePreset("Google", "Pixel 8 Pro", "Google", "husky", "tensor", "UQ1A.240205.004"),
        new DevicePreset("Xiaomi", "Xiaomi 14 Ultra", "Xiaomi", "aurora", "qcom", "UKQ1.231003.002"),
        new DevicePreset("OnePlus", "OnePlus 12", "OnePlus", "OP5929L1", "qcom", "UKQ1.230924.001"),
        new DevicePreset("Huawei", "Pura 70 Ultra", "HUAWEI", "HBP-AL00", "kirin9010", "HUAWEIHBP-AL00")
    };

    public static class GlobalEnvConfig {
        public String brand;
        public String model;
        public String manufacturer;
        public String product;
        public String hardware;
        public boolean locationEnabled;
        public double latitude;
        public double longitude;
        public String regionLabel;
        public String timezoneId;
        public String proxyAddress;
        public String virtualIp;
        public String simCountryIso;
        public String simOperatorName;
        public String simOperatorNumeric;
        public String simPhoneNumber;
    }

    private CloneMetadataStore(Context ctx) {
        this.appCtx = ctx.getApplicationContext();
        this.sp = this.appCtx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
        ensureDefaultVpnProfiles();
    }

    public static synchronized CloneMetadataStore get(Context ctx) {
        if (sInstance == null) sInstance = new CloneMetadataStore(ctx);
        return sInstance;
    }

    private String key(String pkg, int userId, String field) {
        return "c_" + userId + "_" + pkg + "_" + field;
    }

    public String getSpaceDisplayName(int userId, boolean isFa) {
        String custom = sp.getString("space_name_" + userId, "");
        if (custom != null && !custom.trim().isEmpty()) return custom.trim();
        int num = userId + 1;
        return isFa ? ("فضای " + num) : ("Space " + num);
    }

    public void setSpaceCustomName(int userId, String customName) {
        sp.edit().putString("space_name_" + userId, customName == null ? "" : customName.trim()).commit();
    }

    public boolean isSpaceCreated(int userId) {
        if (userId == 0) return true;
        return sp.getBoolean("space_created_" + userId, false);
    }

    public void markSpaceCreated(int userId) {
        sp.edit().putBoolean("space_created_" + userId, true).commit();
    }

    public int getUnreadCount(String pkg, int userId) {
        return Math.max(0, sp.getInt(key(pkg, userId, "unread_badge"), 0));
    }

    public void setUnreadCount(String pkg, int userId, int count) {
        sp.edit().putInt(key(pkg, userId, "unread_badge"), Math.max(0, count)).commit();
    }

    public void incrementUnreadCount(String pkg, int userId) {
        setUnreadCount(pkg, userId, getUnreadCount(pkg, userId) + 1);
    }

    public String formatBadgeText(int count) {
        if (count <= 0) return "";
        if (count >= 100) return "∞";
        return String.valueOf(count);
    }

    public CloneMeta getCloneMeta(String pkg, int userId) {
        CloneMeta m = new CloneMeta();
        m.packageName = pkg;
        m.userId = userId;
        m.customAlias = sp.getString(key(pkg, userId, "alias"), "");
        m.hasExclusiveDevice = sp.getBoolean(key(pkg, userId, "has_dev"), false);
        m.deviceBrand = sp.getString(key(pkg, userId, "brand"), "");
        m.deviceModel = sp.getString(key(pkg, userId, "model"), "");
        m.deviceManufacturer = sp.getString(key(pkg, userId, "manufacturer"), m.deviceBrand);
        m.deviceProduct = sp.getString(key(pkg, userId, "product"), "");
        m.deviceHardware = sp.getString(key(pkg, userId, "hardware"), "");
        m.hasExclusiveLocation = sp.getBoolean(key(pkg, userId, "has_loc"), false);
        m.latitude = Double.longBitsToDouble(sp.getLong(key(pkg, userId, "lat"), Double.doubleToLongBits(37.7749)));
        m.longitude = Double.longBitsToDouble(sp.getLong(key(pkg, userId, "lon"), Double.doubleToLongBits(-122.4194)));
        m.regionLabel = sp.getString(key(pkg, userId, "region"), "");
        m.timezoneId = sp.getString(key(pkg, userId, "tz"), "");
        m.proxyAddress = sp.getString(key(pkg, userId, "proxy"), "");
        m.virtualIp = sp.getString(key(pkg, userId, "vip"), "");
        m.hasExclusiveSim = sp.getBoolean(key(pkg, userId, "has_sim"), false);
        m.simCountryIso = sp.getString(key(pkg, userId, "sim_iso"), "us");
        m.simOperatorName = sp.getString(key(pkg, userId, "sim_op"), "T-Mobile USA");
        m.simOperatorNumeric = sp.getString(key(pkg, userId, "sim_num"), "310260");
        m.simPhoneNumber = sp.getString(key(pkg, userId, "sim_phone"), "+13105550199");
        return m;
    }

    public void saveCloneMeta(CloneMeta m) {
        String p = m.packageName;
        int u = m.userId;
        sp.edit()
            .putString(key(p, u, "alias"), m.customAlias == null ? "" : m.customAlias.trim())
            .putBoolean(key(p, u, "has_dev"), m.hasExclusiveDevice)
            .putString(key(p, u, "brand"), m.deviceBrand)
            .putString(key(p, u, "model"), m.deviceModel)
            .putString(key(p, u, "manufacturer"), m.deviceManufacturer)
            .putString(key(p, u, "product"), m.deviceProduct)
            .putString(key(p, u, "hardware"), m.deviceHardware)
            .putBoolean(key(p, u, "has_loc"), m.hasExclusiveLocation)
            .putLong(key(p, u, "lat"), Double.doubleToRawLongBits(m.latitude))
            .putLong(key(p, u, "lon"), Double.doubleToRawLongBits(m.longitude))
            .putString(key(p, u, "region"), m.regionLabel)
            .putString(key(p, u, "tz"), m.timezoneId)
            .putString(key(p, u, "proxy"), m.proxyAddress)
            .putString(key(p, u, "vip"), m.virtualIp)
            .putBoolean(key(p, u, "has_sim"), m.hasExclusiveSim)
            .putString(key(p, u, "sim_iso"), m.simCountryIso)
            .putString(key(p, u, "sim_op"), m.simOperatorName)
            .putString(key(p, u, "sim_num"), m.simOperatorNumeric)
            .putString(key(p, u, "sim_phone"), m.simPhoneNumber)
            .commit();
    }

    public GlobalEnvConfig getGlobalConfig() {
        GlobalEnvConfig c = new GlobalEnvConfig();
        c.brand = sp.getString("global_brand", "Apple");
        c.model = sp.getString("global_model", "iPhone 16 Pro Max");
        c.manufacturer = sp.getString("global_manufacturer", "Apple");
        c.product = sp.getString("global_product", "iPhone17,2");
        c.hardware = sp.getString("global_hardware", "A18Pro");
        c.locationEnabled = sp.getBoolean("global_loc_enabled", true);
        c.latitude = Double.longBitsToDouble(sp.getLong("global_lat", Double.doubleToLongBits(40.7128)));
        c.longitude = Double.longBitsToDouble(sp.getLong("global_lon", Double.doubleToLongBits(-74.0060)));
        c.regionLabel = sp.getString("global_region", "New York, United States");
        c.timezoneId = sp.getString("global_tz", "America/New_York");
        c.proxyAddress = sp.getString("global_proxy", "");
        c.virtualIp = sp.getString("global_vip", "");
        c.simCountryIso = sp.getString("global_sim_iso", "us");
        c.simOperatorName = sp.getString("global_sim_op", "T-Mobile USA");
        c.simOperatorNumeric = sp.getString("global_sim_num", "310260");
        c.simPhoneNumber = sp.getString("global_sim_phone", "+12125550147");
        return c;
    }

    public void saveGlobalConfig(GlobalEnvConfig c) {
        sp.edit()
            .putString("global_brand", c.brand)
            .putString("global_model", c.model)
            .putString("global_manufacturer", c.manufacturer)
            .putString("global_product", c.product)
            .putString("global_hardware", c.hardware)
            .putBoolean("global_loc_enabled", c.locationEnabled)
            .putLong("global_lat", Double.doubleToRawLongBits(c.latitude))
            .putLong("global_lon", Double.doubleToRawLongBits(c.longitude))
            .putString("global_region", c.regionLabel)
            .putString("global_tz", c.timezoneId)
            .putString("global_proxy", c.proxyAddress)
            .putString("global_vip", c.virtualIp)
            .putString("global_sim_iso", c.simCountryIso != null ? c.simCountryIso : "us")
            .putString("global_sim_op", c.simOperatorName != null ? c.simOperatorName : "T-Mobile USA")
            .putString("global_sim_num", c.simOperatorNumeric != null ? c.simOperatorNumeric : "310260")
            .putString("global_sim_phone", c.simPhoneNumber != null ? c.simPhoneNumber : "+12125550147")
            .commit();
    }

    public String getGlobalBrand() { return getGlobalConfig().brand; }
    public String getGlobalModel() { return getGlobalConfig().model; }
    public String getGlobalRegionLabel() { return getGlobalConfig().regionLabel; }

    public String getEffectiveModelSummary(String pkg, int userId) {
        CloneMeta m = getCloneMeta(pkg, userId);
        if (m.hasExclusiveDevice && m.deviceModel != null && !m.deviceModel.isEmpty()) {
            return m.deviceBrand + " " + m.deviceModel;
        }
        CloneMeta spaceM = getCloneMeta("__space__", userId);
        if (spaceM.hasExclusiveDevice && spaceM.deviceModel != null && !spaceM.deviceModel.isEmpty()) {
            return spaceM.deviceBrand + " " + spaceM.deviceModel;
        }
        GlobalEnvConfig g = getGlobalConfig();
        return g.brand + " " + g.model;
    }

    public String getEffectiveRegionSummary(String pkg, int userId) {
        CloneMeta m = getCloneMeta(pkg, userId);
        if (m.hasExclusiveLocation && m.regionLabel != null && !m.regionLabel.isEmpty()) {
            return m.regionLabel;
        }
        CloneMeta spaceM = getCloneMeta("__space__", userId);
        if (spaceM.hasExclusiveLocation && spaceM.regionLabel != null && !spaceM.regionLabel.isEmpty()) {
            return spaceM.regionLabel;
        }
        return getGlobalConfig().regionLabel;
    }

    private void ensureDefaultVpnProfiles() {
        if (sp.contains("vpn_profiles_json")) return;
        try {
            JSONArray arr = new JSONArray();
            String[][] defaults = {
                {"us_ny", "🇺🇸 USA - New York (Empire State)", "United States", "New York, United States", "SOCKS5", "127.0.0.1", "10808", "America/New_York", "40.7128", "-74.0060", "T-Mobile USA", "310260", "us"},
                {"us_ca", "🇺🇸 USA - California (Los Angeles)", "United States", "Los Angeles, California, United States", "SOCKS5", "127.0.0.1", "10808", "America/Los_Angeles", "34.0522", "-118.2437", "AT&T Mobility", "310410", "us"},
                {"us_tx", "🇺🇸 USA - Texas (Dallas)", "United States", "Dallas, Texas, United States", "SOCKS5", "127.0.0.1", "10808", "America/Chicago", "32.7767", "-96.7970", "Verizon Wireless", "311480", "us"},
                {"us_va", "🇺🇸 USA - Virginia (Ashburn)", "United States", "Ashburn, Virginia, United States", "SOCKS5", "127.0.0.1", "10808", "America/New_York", "39.0438", "-77.4874", "T-Mobile USA", "310260", "us"},
                {"us_fl", "🇺🇸 USA - Florida (Miami)", "United States", "Miami, Florida, United States", "SOCKS5", "127.0.0.1", "10808", "America/New_York", "25.7617", "-80.1918", "T-Mobile USA", "310260", "us"},
                {"us_il", "🇺🇸 USA - Illinois (Chicago)", "United States", "Chicago, Illinois, United States", "SOCKS5", "127.0.0.1", "10808", "America/Chicago", "41.8781", "-87.6298", "AT&T Mobility", "310410", "us"},
                {"us_wa", "🇺🇸 USA - Washington (Seattle)", "United States", "Seattle, Washington, United States", "SOCKS5", "127.0.0.1", "10808", "America/Los_Angeles", "47.6062", "-122.3321", "T-Mobile USA", "310260", "us"},
                {"de_fk", "🇩🇪 Germany - Falkenstein (Hetzner)", "Germany", "Falkenstein, Germany", "SOCKS5", "127.0.0.1", "10808", "Europe/Berlin", "50.4779", "12.3713", "Telekom.de", "26201", "de"},
                {"de_fr", "🇩🇪 Germany - Frankfurt", "Germany", "Frankfurt, Germany", "SOCKS5", "127.0.0.1", "10808", "Europe/Berlin", "50.1109", "8.6821", "Vodafone.de", "26202", "de"},
                {"gb_ln", "🇬🇧 United Kingdom - London", "United Kingdom", "London, United Kingdom", "SOCKS5", "127.0.0.1", "10808", "Europe/London", "51.5074", "-0.1278", "Vodafone UK", "23415", "gb"},
                {"nl_am", "🇳🇱 Netherlands - Amsterdam", "Netherlands", "Amsterdam, Netherlands", "SOCKS5", "127.0.0.1", "10808", "Europe/Amsterdam", "52.3676", "4.9041", "KPN NL", "20408", "nl"},
                {"fr_pa", "🇫🇷 France - Paris", "France", "Paris, France", "SOCKS5", "127.0.0.1", "10808", "Europe/Paris", "48.8566", "2.3522", "Orange F", "20801", "fr"},
                {"ca_to", "🇨🇦 Canada - Toronto", "Canada", "Toronto, Canada", "SOCKS5", "127.0.0.1", "10808", "America/Toronto", "43.6532", "-79.3832", "Rogers Wireless", "302720", "ca"},
                {"tr_is", "🇹🇷 Turkey - Istanbul", "Turkey", "Istanbul, Turkey", "SOCKS5", "127.0.0.1", "10808", "Europe/Istanbul", "41.0082", "28.9784", "Turkcell", "28601", "tr"},
                {"ae_du", "🇦🇪 UAE - Dubai", "UAE", "Dubai, United Arab Emirates", "SOCKS5", "127.0.0.1", "10808", "Asia/Dubai", "25.2048", "55.2708", "Etisalat", "42402", "ae"}
            };
            for (String[] d : defaults) {
                JSONObject o = new JSONObject();
                o.put("id", d[0]); o.put("title", d[1]); o.put("country", d[2]); o.put("stateOrCity", d[3]);
                o.put("protocol", d[4]); o.put("host", d[5]); o.put("port", Integer.parseInt(d[6]));
                o.put("username", ""); o.put("password", ""); o.put("timezoneId", d[7]);
                o.put("lat", Double.parseDouble(d[8])); o.put("lon", Double.parseDouble(d[9]));
                o.put("simOperator", d[10]); o.put("simMccMnc", d[11]); o.put("simIso", d[12]);
                o.put("targetSpaceId", -1);
                arr.put(o);
            }
            sp.edit().putString("vpn_profiles_json", arr.toString()).putString("active_vpn_id", "us_ny").commit();
        } catch (Throwable ignored) {}
    }

    public List<VpnProfile> getVpnProfiles() {
        List<VpnProfile> list = new ArrayList<>();
        try {
            JSONArray arr = new JSONArray(sp.getString("vpn_profiles_json", "[]"));
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                VpnProfile p = new VpnProfile();
                p.id = o.optString("id", "vpn_" + i);
                p.title = o.optString("title", "VPN");
                p.country = o.optString("country", "United States");
                p.stateOrCity = o.optString("stateOrCity", "New York, United States");
                p.protocol = o.optString("protocol", "SOCKS5");
                p.host = o.optString("host", "127.0.0.1");
                p.port = o.optInt("port", 10808);
                p.username = o.optString("username", "");
                p.password = o.optString("password", "");
                p.timezoneId = o.optString("timezoneId", "America/New_York");
                p.lat = o.optDouble("lat", 40.7128);
                p.lon = o.optDouble("lon", -74.0060);
                p.simOperator = o.optString("simOperator", "T-Mobile USA");
                p.simMccMnc = o.optString("simMccMnc", "310260");
                p.simIso = o.optString("simIso", "us");
                p.targetSpaceId = o.optInt("targetSpaceId", -1);
                list.add(p);
            }
        } catch (Throwable ignored) {}
        return list;
    }

    public void saveVpnProfiles(List<VpnProfile> list) {
        try {
            JSONArray arr = new JSONArray();
            for (VpnProfile p : list) {
                JSONObject o = new JSONObject();
                o.put("id", p.id); o.put("title", p.title); o.put("country", p.country);
                o.put("stateOrCity", p.stateOrCity); o.put("protocol", p.protocol);
                o.put("host", p.host); o.put("port", p.port);
                o.put("username", p.username); o.put("password", p.password);
                o.put("timezoneId", p.timezoneId); o.put("lat", p.lat); o.put("lon", p.lon);
                o.put("simOperator", p.simOperator); o.put("simMccMnc", p.simMccMnc);
                o.put("simIso", p.simIso); o.put("targetSpaceId", p.targetSpaceId);
                arr.put(o);
            }
            sp.edit().putString("vpn_profiles_json", arr.toString()).commit();
        } catch (Throwable ignored) {}
    }

    public String getActiveVpnId() { return sp.getString("active_vpn_id", "us_ny"); }
    public void setActiveVpnId(String id) { sp.edit().putString("active_vpn_id", id).commit(); }
    public boolean isVpnConnected() { return sp.getBoolean("vpn_connected", false); }
    public void setVpnConnected(boolean c) { sp.edit().putBoolean("vpn_connected", c).commit(); }
    public boolean isKillSwitchEnabled() { return sp.getBoolean("vpn_kill_switch", false); }
    public void setKillSwitchEnabled(boolean e) { sp.edit().putBoolean("vpn_kill_switch", e).commit(); }
    public boolean isVpnAutoSyncEnabled() { return sp.getBoolean("vpn_auto_sync", true); }
    public void setVpnAutoSyncEnabled(boolean e) { sp.edit().putBoolean("vpn_auto_sync", e).commit(); }
    public String getCustomDns() { return sp.getString("vpn_dns", "1.1.1.1"); }
    public void setCustomDns(String dns) { sp.edit().putString("vpn_dns", dns).commit(); }

    public void applyVpnProfileToEnvironment(VpnProfile p) {
        if (p == null) return;
        setActiveVpnId(p.id);
        if (isVpnAutoSyncEnabled()) {
            GlobalEnvConfig g = getGlobalConfig();
            g.regionLabel = p.stateOrCity;
            g.latitude = p.lat;
            g.longitude = p.lon;
            g.timezoneId = p.timezoneId;
            g.proxyAddress = p.host + ":" + p.port;
            g.simOperatorName = p.simOperator;
            g.simOperatorNumeric = p.simMccMnc;
            g.simCountryIso = p.simIso;
            saveGlobalConfig(g);
        }
    }

    public File getVaultDir(Context ctx, String pkg) {
        File dir = new File(ctx.getFilesDir(), "apk_vault/" + pkg);
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    public boolean backupApkToVault(Context ctx, String pkg, String sourceApkPath) {
        if (sourceApkPath == null || sourceApkPath.isEmpty()) return false;
        File src = new File(sourceApkPath);
        if (!src.exists()) return false;
        File dst = new File(getVaultDir(ctx, pkg), "base.apk");
        try (FileInputStream in = new FileInputStream(src);
             FileOutputStream out = new FileOutputStream(dst)) {
            byte[] buf = new byte[16384];
            int len;
            while ((len = in.read(buf)) > 0) out.write(buf, 0, len);
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    public File getVaultApkFile(String pkg) {
        File f = new File(appCtx.getFilesDir(), "apk_vault/" + pkg + "/base.apk");
        return f.exists() ? f : null;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core/CloneMetadataStore.java"), CLONE_METADATA)

NOTIF_SERVICE = """package com.veyravault.space.core;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.app.Notification;

public class VaultNotificationListenerService extends NotificationListenerService {
    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null || sbn.getNotification() == null) return;
        if ((sbn.getNotification().flags & Notification.FLAG_GROUP_SUMMARY) != 0) return;
        String pkg = sbn.getPackageName();
        if (pkg != null) {
            CloneMetadataStore.get(this).incrementUnreadCount(pkg, 0);
        }
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        if (sbn == null) return;
        String pkg = sbn.getPackageName();
        if (pkg != null) {
            int cur = CloneMetadataStore.get(this).getUnreadCount(pkg, 0);
            if (cur > 0) CloneMetadataStore.get(this).setUnreadCount(pkg, 0, cur - 1);
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core/VaultNotificationListenerService.java"), NOTIF_SERVICE)

VIRTUAL_HOOK = """package com.veyravault.space.core;

import android.content.Context;
import android.os.Build;
import java.lang.reflect.Field;
import java.util.Locale;
import java.util.TimeZone;

public class VirtualHookManager {
    private static VirtualHookManager sInstance;
    private final Context ctx;

    private VirtualHookManager(Context ctx) {
        this.ctx = ctx.getApplicationContext();
    }

    public static synchronized VirtualHookManager get(Context ctx) {
        if (sInstance == null) sInstance = new VirtualHookManager(ctx);
        return sInstance;
    }

    public void prepareEnvironmentBeforeLaunch(String pkg, int userId) {
        applyEffectiveHookToSystem(pkg, userId);
    }

    public void applyEffectiveHookToSystem(String pkg, int userId) {
        try {
            CloneMetadataStore store = CloneMetadataStore.get(ctx);
            CloneMetadataStore.GlobalEnvConfig g = store.getGlobalConfig();
            CloneMetadataStore.CloneMeta spaceMeta = store.getCloneMeta("__space__", userId);
            CloneMetadataStore.CloneMeta appMeta = pkg != null ? store.getCloneMeta(pkg, userId) : null;

            String brand = g.brand, model = g.model, manufacturer = g.manufacturer, product = g.product, hardware = g.hardware;
            if (spaceMeta.hasExclusiveDevice && !spaceMeta.deviceModel.isEmpty()) {
                brand = spaceMeta.deviceBrand; model = spaceMeta.deviceModel;
                manufacturer = spaceMeta.deviceManufacturer; product = spaceMeta.deviceProduct; hardware = spaceMeta.deviceHardware;
            }
            if (appMeta != null && appMeta.hasExclusiveDevice && !appMeta.deviceModel.isEmpty()) {
                brand = appMeta.deviceBrand; model = appMeta.deviceModel;
                manufacturer = appMeta.deviceManufacturer; product = appMeta.deviceProduct; hardware = appMeta.deviceHardware;
            }

            double lat = g.latitude, lon = g.longitude;
            String tz = g.timezoneId, region = g.regionLabel, proxy = g.proxyAddress;
            if (spaceMeta.hasExclusiveLocation) {
                lat = spaceMeta.latitude; lon = spaceMeta.longitude;
                if (!spaceMeta.timezoneId.isEmpty()) tz = spaceMeta.timezoneId;
                if (!spaceMeta.regionLabel.isEmpty()) region = spaceMeta.regionLabel;
                if (!spaceMeta.proxyAddress.isEmpty()) proxy = spaceMeta.proxyAddress;
            }
            if (appMeta != null && appMeta.hasExclusiveLocation) {
                lat = appMeta.latitude; lon = appMeta.longitude;
                if (!appMeta.timezoneId.isEmpty()) tz = appMeta.timezoneId;
                if (!appMeta.regionLabel.isEmpty()) region = appMeta.regionLabel;
                if (!appMeta.proxyAddress.isEmpty()) proxy = appMeta.proxyAddress;
            }

            String simIso = g.simCountryIso, simOp = g.simOperatorName, simNum = g.simOperatorNumeric, simPhone = g.simPhoneNumber;
            if (spaceMeta.hasExclusiveSim) {
                simIso = spaceMeta.simCountryIso; simOp = spaceMeta.simOperatorName;
                simNum = spaceMeta.simOperatorNumeric; simPhone = spaceMeta.simPhoneNumber;
            }
            if (appMeta != null && appMeta.hasExclusiveSim) {
                simIso = appMeta.simCountryIso; simOp = appMeta.simOperatorName;
                simNum = appMeta.simOperatorNumeric; simPhone = appMeta.simPhoneNumber;
            }

            setBuildField("BRAND", brand);
            setBuildField("MODEL", model);
            setBuildField("MANUFACTURER", manufacturer != null && !manufacturer.isEmpty() ? manufacturer : brand);
            setBuildField("DEVICE", model);
            if (product != null && !product.isEmpty()) setBuildField("PRODUCT", product);
            if (hardware != null && !hardware.isEmpty()) setBuildField("HARDWARE", hardware);

            if (tz != null && !tz.isEmpty()) {
                TimeZone.setDefault(TimeZone.getTimeZone(tz));
                System.setProperty("user.timezone", tz);
            }
            System.setProperty("veyra.spoof.lat", String.valueOf(lat));
            System.setProperty("veyra.spoof.lon", String.valueOf(lon));
            System.setProperty("veyra.spoof.region", region != null ? region : "New York, United States");
            System.setProperty("gsm.sim.operator.alpha", simOp != null ? simOp : "T-Mobile USA");
            System.setProperty("gsm.operator.alpha", simOp != null ? simOp : "T-Mobile USA");
            System.setProperty("gsm.sim.operator.numeric", simNum != null ? simNum : "310260");
            System.setProperty("gsm.operator.numeric", simNum != null ? simNum : "310260");
            System.setProperty("gsm.sim.operator.iso-country", simIso != null ? simIso : "us");
            System.setProperty("gsm.operator.iso-country", simIso != null ? simIso : "us");
            System.setProperty("veyra.sim.phone", simPhone != null ? simPhone : "+12125550147");

            if (proxy != null && proxy.contains(":")) {
                String[] parts = proxy.split(":");
                System.setProperty("socksProxyHost", parts[0].trim());
                System.setProperty("socksProxyPort", parts[1].trim());
                System.setProperty("http.proxyHost", parts[0].trim());
                System.setProperty("http.proxyPort", parts[1].trim());
            }
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
"""
write_file(os.path.join(JAVA_BASE, "core/VirtualHookManager.java"), VIRTUAL_HOOK)

ENGINE_JAVA = """package com.veyravault.space.core;

import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.os.Process;
import com.veyravault.space.helper.GmsSupportManager;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.entity.pm.InstallResult;

public class Engine {
    public static final String BUILTIN_PLAY_STORE = "com.android.vending";
    public static final String BUILTIN_SPACE_SETTINGS = "com.veyravault.space.settings";
    private static Engine sInstance;
    private final Context ctx;

    public static class CloneItem {
        public String packageName;
        public String label;
        public Drawable icon;
        public int userId;
        public boolean isBuiltinSystem;
    }

    public static class OptimizationReport {
        public long cacheFreedBytes;
        public long ramFreedBytes;
        public int killedProcesses;
    }

    private Engine(Context ctx) {
        this.ctx = ctx.getApplicationContext();
    }

    public static synchronized Engine get(Context ctx) {
        if (sInstance == null) sInstance = new Engine(ctx);
        return sInstance;
    }

    public void initialize() {
        try {
            for (int u = 0; u < 10; u++) {
                GmsSupportManager.cleanPoisonedGmsInSpace(u);
            }
        } catch (Throwable ignored) {}
    }

    public List<Integer> getActiveSpaceIds() {
        Set<Integer> ids = new LinkedHashSet<>();
        ids.add(0);
        CloneMetadataStore store = CloneMetadataStore.get(ctx);
        for (int u = 0; u < 30; u++) {
            if (store.isSpaceCreated(u)) ids.add(u);
            try {
                List<ApplicationInfo> apps = BlackBoxCore.get().getInstalledApplications(0, u);
                if (apps != null) {
                    for (ApplicationInfo info : apps) {
                        if (info != null && info.packageName != null
                                && !"com.google.android.gms".equals(info.packageName)
                                && !"com.google.android.gsf".equals(info.packageName)
                                && !"android".equals(info.packageName)) {
                            ids.add(u);
                            store.markSpaceCreated(u);
                        }
                    }
                }
            } catch (Throwable ignored) {}
        }
        return new ArrayList<>(ids);
    }

    public int findNextAvailableSpaceForPackage(String pkg) {
        for (int u = 0; u < 50; u++) {
            try {
                if (!BlackBoxCore.get().isInstalled(pkg, u)) {
                    return u;
                }
            } catch (Throwable t) {
                return u;
            }
        }
        return 0;
    }

    public List<CloneItem> getInstalledClones(int userId) {
        List<CloneItem> result = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        GmsSupportManager.cleanPoisonedGmsInSpace(userId);

        // Built-in 1: Google Play Store for this Space
        CloneItem playItem = new CloneItem();
        playItem.packageName = BUILTIN_PLAY_STORE;
        playItem.userId = userId;
        playItem.isBuiltinSystem = true;
        playItem.label = "فروشگاه گوگل پلی";
        try {
            ApplicationInfo ai = pm.getApplicationInfo("com.android.vending", 0);
            playItem.icon = ai.loadIcon(pm);
        } catch (Throwable t) {
            playItem.icon = ctx.getApplicationInfo().loadIcon(pm);
        }
        result.add(playItem);

        // Built-in 2: Android System Settings for this Space
        CloneItem settingsItem = new CloneItem();
        settingsItem.packageName = BUILTIN_SPACE_SETTINGS;
        settingsItem.userId = userId;
        settingsItem.isBuiltinSystem = true;
        settingsItem.label = "تنظیمات اندروید";
        try {
            ApplicationInfo ai = pm.getApplicationInfo("com.android.settings", 0);
            settingsItem.icon = ai.loadIcon(pm);
        } catch (Throwable t) {
            settingsItem.icon = ctx.getResources().getDrawable(android.R.drawable.sym_def_app_icon);
        }
        result.add(settingsItem);

        try {
            List<ApplicationInfo> list = BlackBoxCore.get().getInstalledApplications(0, userId);
            if (list != null) {
                for (ApplicationInfo info : list) {
                    if (info == null || info.packageName == null) continue;
                    if (info.packageName.equals(ctx.getPackageName())
                            || info.packageName.equals("com.google.android.gms")
                            || info.packageName.equals("com.google.android.gsf")
                            || info.packageName.equals("com.android.vending")
                            || info.packageName.equals("android")) continue;
                    CloneItem item = new CloneItem();
                    item.packageName = info.packageName;
                    item.userId = userId;
                    item.isBuiltinSystem = false;
                    try {
                        ApplicationInfo hostInfo = pm.getApplicationInfo(info.packageName, 0);
                        item.label = hostInfo.loadLabel(pm).toString();
                        item.icon = hostInfo.loadIcon(pm);
                    } catch (Throwable e) {
                        File vaultApk = CloneMetadataStore.get(ctx).getVaultApkFile(info.packageName);
                        if (vaultApk != null) {
                            PackageInfo pi = pm.getPackageArchiveInfo(vaultApk.getAbsolutePath(), 0);
                            if (pi != null && pi.applicationInfo != null) {
                                pi.applicationInfo.sourceDir = vaultApk.getAbsolutePath();
                                pi.applicationInfo.publicSourceDir = vaultApk.getAbsolutePath();
                                item.label = pi.applicationInfo.loadLabel(pm).toString();
                                item.icon = pi.applicationInfo.loadIcon(pm);
                            }
                        }
                        if (item.label == null) item.label = info.packageName;
                        if (item.icon == null) item.icon = ctx.getApplicationInfo().loadIcon(pm);
                    }
                    result.add(item);
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return result;
    }

    public boolean cloneFromInstalledWithVault(String pkg, int userId) {
        try {
            CloneMetadataStore.get(ctx).markSpaceCreated(userId);
            GmsSupportManager.cleanPoisonedGmsInSpace(userId);
            PackageManager pm = ctx.getPackageManager();
            ApplicationInfo appInfo = pm.getApplicationInfo(pkg, 0);
            if (appInfo.sourceDir != null) {
                CloneMetadataStore.get(ctx).backupApkToVault(ctx, pkg, appInfo.sourceDir);
            }
            InstallResult res = BlackBoxCore.get().installPackageAsUser(pkg, userId);
            if (res == null || !res.success) {
                File vaultApk = CloneMetadataStore.get(ctx).getVaultApkFile(pkg);
                if (vaultApk != null) {
                    res = BlackBoxCore.get().installPackageAsUser(vaultApk, userId);
                }
            }
            syncNativeLibsForPackage(appInfo, pkg);
            return res != null && res.success;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public boolean installFromApkFileWithVault(File apkFile, int userId) {
        if (apkFile == null || !apkFile.exists()) return false;
        try {
            CloneMetadataStore.get(ctx).markSpaceCreated(userId);
            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(apkFile.getAbsolutePath(), 0);
            if (pi != null && pi.packageName != null) {
                CloneMetadataStore.get(ctx).backupApkToVault(ctx, pi.packageName, apkFile.getAbsolutePath());
            }
            InstallResult res = BlackBoxCore.get().installPackageAsUser(apkFile, userId);
            return res != null && res.success;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    private void syncNativeLibsForPackage(ApplicationInfo appInfo, String pkg) {
        try {
            File baseVirtualLib = new File(ctx.getApplicationInfo().dataDir, "virtual/data/app/" + pkg + "/lib");
            if (!baseVirtualLib.exists()) baseVirtualLib.mkdirs();

            // 1. Copy already-extracted host native libraries (most reliable for Split APKs!)
            if (appInfo.nativeLibraryDir != null) {
                File hostLibDir = new File(appInfo.nativeLibraryDir);
                if (hostLibDir.exists() && hostLibDir.isDirectory()) {
                    File[] soFiles = hostLibDir.listFiles();
                    if (soFiles != null) {
                        for (File so : soFiles) {
                            if (so.isFile() && so.getName().endsWith(".so")) {
                                copyFileFast(so, new File(baseVirtualLib, so.getName()));
                            }
                        }
                    }
                }
            }

            // 2. Also scan base.apk + splitSourceDirs for primary ABI .so files
            List<String> apkPaths = new ArrayList<>();
            if (appInfo.sourceDir != null) apkPaths.add(appInfo.sourceDir);
            if (Build.VERSION.SDK_INT >= 21 && appInfo.splitSourceDirs != null) {
                for (String s : appInfo.splitSourceDirs) apkPaths.add(s);
            }
            String preferredAbi = (Build.VERSION.SDK_INT >= 21 && Build.SUPPORTED_ABIS.length > 0)
                    ? Build.SUPPORTED_ABIS[0] : Build.CPU_ABI;

            for (String apkPath : apkPaths) {
                try (ZipFile zip = new ZipFile(apkPath)) {
                    Enumeration<? extends ZipEntry> entries = zip.entries();
                    while (entries.hasMoreElements()) {
                        ZipEntry entry = entries.nextElement();
                        String name = entry.getName();
                        if (!name.startsWith("lib/") || !name.endsWith(".so")) continue;
                        String soName = name.substring(name.lastIndexOf('/') + 1);
                        File directOut = new File(baseVirtualLib, soName);
                        if (name.contains(preferredAbi) || !directOut.exists()) {
                            try (InputStream in = zip.getInputStream(entry);
                                 FileOutputStream out = new FileOutputStream(directOut)) {
                                byte[] buf = new byte[16384];
                                int len;
                                while ((len = in.read(buf)) > 0) out.write(buf, 0, len);
                            }
                        }
                    }
                } catch (Throwable ignored) {}
            }
        } catch (Throwable ignored) {}
    }

    private void copyFileFast(File src, File dst) {
        try (FileInputStream in = new FileInputStream(src);
             FileOutputStream out = new FileOutputStream(dst)) {
            byte[] buf = new byte[16384];
            int len;
            while ((len = in.read(buf)) > 0) out.write(buf, 0, len);
        } catch (Throwable ignored) {}
    }

    public boolean launchClone(String pkg, int userId) {
        try {
            GmsSupportManager.cleanPoisonedGmsInSpace(userId);
            CloneMetadataStore.get(ctx).setUnreadCount(pkg, userId, 0);
            VirtualHookManager.get(ctx).prepareEnvironmentBeforeLaunch(pkg, userId);

            try {
                ApplicationInfo hostInfo = ctx.getPackageManager().getApplicationInfo(pkg, 0);
                syncNativeLibsForPackage(hostInfo, pkg);
            } catch (Throwable ignored) {}

            if (!BlackBoxCore.get().isInstalled(pkg, userId)) {
                try {
                    BlackBoxCore.get().installPackageAsUser(pkg, userId);
                } catch (Throwable ignored) {}
            }

            boolean ok = BlackBoxCore.get().launchApk(pkg, userId);
            if (ok) return true;

            Intent launchIntent = BlackBoxCore.getBPackageManager().getLaunchIntentForPackage(pkg, userId);
            if (launchIntent != null) {
                BlackBoxCore.get().startActivity(launchIntent, userId);
                return true;
            }
            return false;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public void stopClone(String pkg, int userId) {
        try { BlackBoxCore.get().stopPackage(pkg, userId); } catch (Throwable ignored) {}
    }

    public void clearCloneData(String pkg, int userId) {
        try { BlackBoxCore.get().clearPackage(pkg, userId); } catch (Throwable ignored) {}
    }

    public void uninstallClone(String pkg, int userId) {
        try { BlackBoxCore.get().uninstallPackageAsUser(pkg, userId); } catch (Throwable ignored) {}
    }

    public OptimizationReport optimizeMemoryAndSpeedDetailed() {
        OptimizationReport rep = new OptimizationReport();
        try {
            Runtime rt = Runtime.getRuntime();
            long beforeUsed = rt.totalMemory() - rt.freeMemory();

            rep.cacheFreedBytes += clearDirectoryBytes(ctx.getCacheDir());
            if (ctx.getExternalCacheDir() != null) {
                rep.cacheFreedBytes += clearDirectoryBytes(ctx.getExternalCacheDir());
            }
            File vUserRoot = new File(ctx.getApplicationInfo().dataDir, "virtual/data/user");
            if (vUserRoot.exists()) {
                rep.cacheFreedBytes += clearVirtualAppCachesOnly(vUserRoot);
            }

            ActivityManager am = (ActivityManager) ctx.getSystemService(Context.ACTIVITY_SERVICE);
            if (am != null) {
                List<ActivityManager.RunningAppProcessInfo> procs = am.getRunningAppProcesses();
                if (procs != null) {
                    int myPid = Process.myPid();
                    for (ActivityManager.RunningAppProcessInfo p : procs) {
                        if (p.pid != myPid && p.processName != null && p.processName.contains(":p")
                                && p.importance > ActivityManager.RunningAppProcessInfo.IMPORTANCE_FOREGROUND) {
                            Process.killProcess(p.pid);
                            rep.killedProcesses++;
                        }
                    }
                }
            }

            System.runFinalization();
            rt.gc();
            long afterUsed = rt.totalMemory() - rt.freeMemory();
            rep.ramFreedBytes = Math.max(0, beforeUsed - afterUsed);
        } catch (Throwable ignored) {}
        return rep;
    }

    public long optimizeMemoryAndSpeed() {
        OptimizationReport r = optimizeMemoryAndSpeedDetailed();
        return r.cacheFreedBytes + r.ramFreedBytes;
    }

    private long clearVirtualAppCachesOnly(File dir) {
        if (dir == null || !dir.exists()) return 0;
        long freed = 0;
        File[] files = dir.listFiles();
        if (files != null) {
            for (File f : files) {
                if (f.isDirectory()) {
                    if ("cache".equals(f.getName()) || "code_cache".equals(f.getName())) {
                        freed += clearDirectoryBytes(f);
                    } else {
                        freed += clearVirtualAppCachesOnly(f);
                    }
                }
            }
        }
        return freed;
    }

    private long clearDirectoryBytes(File dir) {
        if (dir == null || !dir.exists()) return 0;
        long bytes = 0;
        File[] files = dir.listFiles();
        if (files != null) {
            for (File f : files) {
                if (f.isDirectory()) {
                    bytes += clearDirectoryBytes(f);
                } else {
                    long len = f.length();
                    if (f.delete()) bytes += len;
                }
            }
        }
        return bytes;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core/Engine.java"), ENGINE_JAVA)

SECURITY_MANAGER = """package com.veyravault.space.security;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import java.security.MessageDigest;

public class SecurityManager {
    private static final String PREF = "veyra_security_v3";
    public static final String PRIORITY_PIN = "PIN";
    public static final String PRIORITY_PATTERN = "PATTERN";
    private static SecurityManager sInstance;
    private final Context ctx;
    private final SharedPreferences sp;
    private static boolean sSessionUnlocked = false;

    private SecurityManager(Context ctx) {
        this.ctx = ctx.getApplicationContext();
        this.sp = this.ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    public static synchronized SecurityManager get(Context ctx) {
        if (sInstance == null) sInstance = new SecurityManager(ctx);
        return sInstance;
    }

    private String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest((input + "_veyra_salt_v3").getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return String.valueOf(input.hashCode());
        }
    }

    public boolean isPinEnabled() { return sp.getBoolean("pin_enabled", false) && !sp.getString("pin_hash", "").isEmpty(); }
    public boolean isPatternEnabled() { return sp.getBoolean("pattern_enabled", false) && !sp.getString("pattern_hash", "").isEmpty(); }
    public boolean isAnyLockEnabled() { return isPinEnabled() || isPatternEnabled(); }
    public boolean isBothLocksEnabled() { return isPinEnabled() && isPatternEnabled(); }

    public void setPinCode(String rawPin) {
        if (rawPin == null || rawPin.trim().isEmpty()) {
            sp.edit().putBoolean("pin_enabled", false).remove("pin_hash").commit();
        } else {
            sp.edit().putBoolean("pin_enabled", true).putString("pin_hash", sha256(rawPin.trim())).commit();
        }
    }

    public void setPatternCode(String rawPattern) {
        if (rawPattern == null || rawPattern.trim().isEmpty()) {
            sp.edit().putBoolean("pattern_enabled", false).remove("pattern_hash").commit();
        } else {
            sp.edit().putBoolean("pattern_enabled", true).putString("pattern_hash", sha256(rawPattern.trim())).commit();
        }
    }

    public void disableAllLocks() {
        sp.edit().putBoolean("pin_enabled", false).putBoolean("pattern_enabled", false)
            .remove("pin_hash").remove("pattern_hash").commit();
        sSessionUnlocked = true;
    }

    public boolean verifyPin(String candidate) {
        if (!isPinEnabled() || candidate == null) return false;
        return sha256(candidate.trim()).equals(sp.getString("pin_hash", ""));
    }

    public boolean verifyPattern(String candidate) {
        if (!isPatternEnabled() || candidate == null) return false;
        return sha256(candidate.trim()).equals(sp.getString("pattern_hash", ""));
    }

    public String getPrimaryLockPriority() { return sp.getString("primary_priority", PRIORITY_PIN); }
    public void setPrimaryLockPriority(String priority) { sp.edit().putString("primary_priority", priority).commit(); }

    public boolean isSessionUnlocked() {
        if (!isAnyLockEnabled()) return true;
        return sSessionUnlocked;
    }

    public void setSessionUnlocked(boolean unlocked) { sSessionUnlocked = unlocked; }
    public void lockSessionNow() { sSessionUnlocked = false; }

    public boolean isUninstallProtectionActive() {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
            return dpm != null && dpm.isAdminActive(cn);
        } catch (Throwable t) {
            return false;
        }
    }

    public void removeUninstallProtection() {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(ctx, VaultDeviceAdminReceiver.class);
            if (dpm != null && dpm.isAdminActive(cn)) dpm.removeActiveAdmin(cn);
        } catch (Throwable ignored) {}
    }
}
"""
write_file(os.path.join(JAVA_BASE, "security/SecurityManager.java"), SECURITY_MANAGER)

DEVICE_ADMIN_RECEIVER = """package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.app.admin.DevicePolicyManager;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;
import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {
    @Override
    public void onEnabled(Context context, Intent intent) {
        Toast.makeText(context, "🛡️ محافظت ضدحذف VeyraVault فعال شد", Toast.LENGTH_SHORT).show();
    }

    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        try {
            SecurityManager.get(context).lockSessionNow();
            Intent lockIntent = new Intent(context, SecurityLockActivity.class);
            lockIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            context.startActivity(lockIntent);
            DevicePolicyManager dpm = (DevicePolicyManager) context.getSystemService(Context.DEVICE_POLICY_SERVICE);
            if (dpm != null) dpm.lockNow();
        } catch (Throwable ignored) {}
        return "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است.";
    }

    @Override
    public void onDisabled(Context context, Intent intent) {
        Toast.makeText(context, "محافظ ضدحذف غیرفعال شد", Toast.LENGTH_SHORT).show();
    }
}
"""
write_file(os.path.join(JAVA_BASE, "security/VaultDeviceAdminReceiver.java"), DEVICE_ADMIN_RECEIVER)

print("[v3-part1] Completed successfully.")
