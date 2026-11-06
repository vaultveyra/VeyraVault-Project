#!/usr/bin/env python3
"""
VeyraVault v3.0 Upgrade - Part 1 (Self-contained Infrastructure, Gradle/Manifest, Core Engine, APK Vault, Hooks, Dual Lock, SVG Icons)
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JAVA_BASE = os.path.join(ROOT, "app", "src", "main", "java", "com", "veyravault", "space")
RES_BASE = os.path.join(ROOT, "app", "src", "main", "res")
MANIFEST_PATH = os.path.join(ROOT, "app", "src", "main", "AndroidManifest.xml")
APP_GRADLE_PATH = os.path.join(ROOT, "app", "build.gradle")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[v3-part1] Wrote {os.path.relpath(path, ROOT)}")

# ---------------------------------------------------------------------------
# 0. Clean up legacy v1.0 files & Patch app/build.gradle + AndroidManifest.xml
# ---------------------------------------------------------------------------
stale_files = [
    os.path.join(JAVA_BASE, "security", "PinLockActivity.java"),
    os.path.join(JAVA_BASE, "ui", "LocationPickerActivity.java"),
]
for sf in stale_files:
    if os.path.exists(sf):
        os.remove(sf)
        print(f"[v3-part1] Removed legacy file: {os.path.relpath(sf, ROOT)}")

if os.path.exists(APP_GRADLE_PATH):
    with open(APP_GRADLE_PATH, "r", encoding="utf-8") as f:
        gradle_txt = f.read()
    if "osmdroid-android" not in gradle_txt:
        gradle_txt = gradle_txt.replace(
            "dependencies {",
            "dependencies {\n    implementation 'org.osmdroid:osmdroid-android:6.1.14'"
        )
    gradle_txt = re.sub(r"versionCode\s+\d+", "versionCode 3", gradle_txt)
    gradle_txt = re.sub(r'versionName\s+"[^"]+"', 'versionName "3.0.0"', gradle_txt)
    with open(APP_GRADLE_PATH, "w", encoding="utf-8") as f:
        f.write(gradle_txt)
    print("[v3-part1] Patched app/build.gradle with osmdroid & v3.0.0")

DEVICE_ADMIN_XML = """
<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <force-lock />
    </uses-policies>
</device-admin>
"""
write_file(os.path.join(RES_BASE, "xml", "device_admin_policies.xml"), DEVICE_ADMIN_XML)

ANDROID_MANIFEST = """
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    package="com.veyravault.space">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <application
        android:name=".VeyraApplication"
        android:allowBackup="false"
        android:icon="@android:drawable/sym_def_app_icon"
        android:label="VeyraVault"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.AppCompat.NoActionBar"
        tools:replace="android:label,android:allowBackup,android:icon">

        <activity
            android:name=".ui.MainActivity"
            android:exported="true"
            android:configChanges="locale|layoutDirection|orientation|screenSize">
        </activity>

        <!-- Disguise Mode 0: Default VeyraVault -->
        <activity-alias
            android:name=".LauncherDefault"
            android:targetActivity=".ui.MainActivity"
            android:enabled="true"
            android:exported="true"
            android:icon="@android:drawable/sym_def_app_icon"
            android:label="VeyraVault">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <!-- Disguise Mode 1: Calculator -->
        <activity-alias
            android:name=".LauncherCalc"
            android:targetActivity=".ui.MainActivity"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_dialog_dialer"
            android:label="Calculator">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <!-- Disguise Mode 2: Calendar -->
        <activity-alias
            android:name=".LauncherCalendar"
            android:targetActivity=".ui.MainActivity"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_menu_my_calendar"
            android:label="Calendar">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <!-- Disguise Mode 3: Notepad -->
        <activity-alias
            android:name=".LauncherNotes"
            android:targetActivity=".ui.MainActivity"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_menu_edit"
            android:label="Notes">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity android:name=".ui.AddAppActivity" android:exported="false" />
        <activity android:name=".ui.GlobalEnvironmentActivity" android:exported="false" />
        <activity android:name=".ui.SetLocationActivity" android:exported="false" />
        <activity android:name=".ui.SecuritySettingsActivity" android:exported="false" />
        <activity android:name=".ui.SecurityLockActivity" android:exported="false" android:launchMode="singleTop" />
        <activity android:name=".ui.GuideActivity" android:exported="false" />
        <activity android:name=".ui.AboutActivity" android:exported="false" />

        <receiver
            android:name=".security.VaultDeviceAdminReceiver"
            android:description="@string/app_name"
            android:label="VeyraVault Security Guard"
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
"""
write_file(MANIFEST_PATH, ANDROID_MANIFEST)

# ---------------------------------------------------------------------------
# 1. SVG Vector Drawables for Bottom Navigation
# ---------------------------------------------------------------------------
IC_DASHBOARD = """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="M3,13h8V3H3v10zm0,8h8v-6H3v6zm10,0h8V11h-8v10zm0,-18v6h8V3h-8z"/>
</vector>
"""

IC_SPACES = """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="M4,8h4V4H4v4zm6,12h4v-4h-4v4zm-6,0h4v-4H4v4zm0,-6h4v-4H4v4zm6,0h4v-4h-4v4zm6,-10v4h4V4h-4zm-6,4h4V4h-4v4zm6,6h4v-4h-4v4zm0,6h4v-4h-4v4z"/>
</vector>
"""

IC_ADD = """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
</vector>
"""

IC_GUIDE = """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zm1,17h-2v-2h2v2zm2.07,-7.75l-0.9,0.92C13.45,12.9 13,13.5 13,15h-2v-0.5c0,-1.1 0.45,-2.1 1.17,-2.83l1.24,-1.26c0.37,-0.36 0.59,-0.86 0.59,-1.41 0,-1.1 -0.9,-2 -2,-2s-2,0.9 -2,2H8c0,-2.21 1.79,-4 4,-4s4,1.79 4,4c0,0.88 -0.36,1.68 -0.93,2.25z"/>
</vector>
"""

IC_SETTINGS = """
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94 0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6 3.6,1.62 3.6,3.6 -1.62,3.6 -3.6,3.6z"/>
</vector>
"""

write_file(os.path.join(RES_BASE, "drawable", "ic_nav_dashboard.xml"), IC_DASHBOARD)
write_file(os.path.join(RES_BASE, "drawable", "ic_nav_spaces.xml"), IC_SPACES)
write_file(os.path.join(RES_BASE, "drawable", "ic_nav_add.xml"), IC_ADD)
write_file(os.path.join(RES_BASE, "drawable", "ic_nav_guide.xml"), IC_GUIDE)
write_file(os.path.join(RES_BASE, "drawable", "ic_nav_settings.xml"), IC_SETTINGS)

# ---------------------------------------------------------------------------
# 2. Jalali (Solar Hijri) & World Clock Utility + LocaleHelper + BaseActivity
# ---------------------------------------------------------------------------
JALALI_UTIL = """
package com.veyravault.space.util;

import java.util.Calendar;
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

    private static final String[] GREG_MONTHS_EN = {
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
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

    public static String getTehranTimeFormatted() {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Tehran"));
        return String.format(Locale.US, "%02d:%02d:%02d",
                cal.get(Calendar.HOUR_OF_DAY),
                cal.get(Calendar.MINUTE),
                cal.get(Calendar.SECOND));
    }

    public static String getTehranJalaliDate(boolean persian) {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Tehran"));
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int[] j = gregorianToJalali(gy, gm, gd);
        String monthName = persian ? JALALI_MONTHS_FA[j[1] - 1] : JALALI_MONTHS_EN[j[1] - 1];
        return j[2] + " " + monthName + " " + j[0];
    }

    public static String getNewYorkTimeFormatted() {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("America/New_York"));
        return String.format(Locale.US, "%02d:%02d:%02d",
                cal.get(Calendar.HOUR_OF_DAY),
                cal.get(Calendar.MINUTE),
                cal.get(Calendar.SECOND));
    }

    public static String getNewYorkGregorianDate(boolean persian) {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("America/New_York"));
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH);
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        return GREG_MONTHS_EN[gm] + " " + gd + ", " + gy;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "util", "JalaliClockUtil.java"), JALALI_UTIL)

LOCALE_HELPER = """
package com.veyravault.space.util;

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
                .edit().putString(KEY_LANG, lang).apply();
    }

    public static String toggleLanguage(Context context) {
        String next = isPersian(context) ? "en" : "fa";
        setLanguage(context, next);
        return next;
    }

    public static Context onAttach(Context context) {
        return applyLocale(context);
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
write_file(os.path.join(JAVA_BASE, "util", "LocaleHelper.java"), LOCALE_HELPER)

BASE_ACTIVITY = """
package com.veyravault.space.ui;

import android.content.Context;
import android.os.Bundle;
import android.view.View;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.veyravault.space.util.LocaleHelper;

public abstract class BaseActivity extends AppCompatActivity {

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.applyLocale(newBase));
    }

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean fa = LocaleHelper.isPersian(this);
        getWindow().getDecorView().setLayoutDirection(
                fa ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
        );
    }

    protected boolean isFa() {
        return LocaleHelper.isPersian(this);
    }

    protected String tr(String fa, String en) {
        return isFa() ? fa : en;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui", "BaseActivity.java"), BASE_ACTIVITY)

GMS_SUPPORT = """
package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import java.lang.reflect.Method;

import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    private static final String PREFS = "veyra_gms_prefs";

    public static boolean isGmsInstalled(Context ctx, int userId) {
        SharedPreferences sp = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (sp.getBoolean("gms_enabled_" + userId, true)) {
            return true;
        }
        try {
            Method m = BlackBoxCore.class.getMethod("isInstallGms", int.class);
            Object r = m.invoke(BlackBoxCore.get(), userId);
            if (r instanceof Boolean) return (Boolean) r;
        } catch (Throwable ignored) {}
        return true;
    }

    public static boolean installGms(Context ctx, int userId) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putBoolean("gms_enabled_" + userId, true).apply();
        try {
            Method m = BlackBoxCore.class.getMethod("installGms", int.class);
            m.invoke(BlackBoxCore.get(), userId);
        } catch (Throwable ignored) {}
        return true;
    }

    public static void uninstallGms(Context ctx, int userId) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putBoolean("gms_enabled_" + userId, false).apply();
        try {
            Method m = BlackBoxCore.class.getMethod("uninstallGms", int.class);
            m.invoke(BlackBoxCore.get(), userId);
        } catch (Throwable ignored) {}
    }

    public static void ensureGmsForAllSpaces(Context ctx) {
        for (int i = 0; i < 3; i++) {
            if (isGmsInstalled(ctx, i)) {
                installGms(ctx, i);
            }
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core", "GmsSupportManager.java"), GMS_SUPPORT)

APP_DISGUISE = """
package com.veyravault.space.security;

import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;

public class AppDisguiseManager {
    private static final String PREFS = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode";

    public static final int MODE_DEFAULT = 0;
    public static final int MODE_CALCULATOR = 1;
    public static final int MODE_CALENDAR = 2;
    public static final int MODE_NOTEPAD = 3;

    private static final String[] ALIASES = {
        "com.veyravault.space.LauncherDefault",
        "com.veyravault.space.LauncherCalc",
        "com.veyravault.space.LauncherCalendar",
        "com.veyravault.space.LauncherNotes"
    };

    public static int getDisguiseMode(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getInt(KEY_MODE, MODE_DEFAULT);
    }

    public static void applyDisguise(Context ctx, int mode) {
        if (mode < 0 || mode >= ALIASES.length) mode = MODE_DEFAULT;
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putInt(KEY_MODE, mode).apply();
        PackageManager pm = ctx.getPackageManager();
        String pkg = ctx.getPackageName();
        for (int i = 0; i < ALIASES.length; i++) {
            ComponentName cn = new ComponentName(pkg, ALIASES[i]);
            int state = (i == mode)
                    ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED
                    : PackageManager.COMPONENT_ENABLED_STATE_DISABLED;
            try {
                pm.setComponentEnabledSetting(cn, state, PackageManager.DONT_KILL_APP);
            } catch (Throwable ignored) {}
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "security", "AppDisguiseManager.java"), APP_DISGUISE)

PATTERN_VIEW = """
package com.veyravault.space.ui;

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
        void onPatternComplete(String pattern);
    }

    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final List<Integer> selected = new ArrayList<>();
    private float curX, curY;
    private boolean tracking = false;
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

    public void setOnPatternListener(OnPatternListener listener) {
        this.listener = listener;
    }

    public void clearPattern() {
        selected.clear();
        invalidate();
    }

    private float getDotX(int idx) {
        int col = idx % 3;
        float step = getWidth() / 4f;
        return step * (col + 1);
    }

    private float getDotY(int idx) {
        int row = idx / 3;
        float step = getHeight() / 4f;
        return step * (row + 1);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        for (int i = 0; i < selected.size() - 1; i++) {
            int a = selected.get(i);
            int b = selected.get(i + 1);
            canvas.drawLine(getDotX(a), getDotY(a), getDotX(b), getDotY(b), linePaint);
        }
        if (tracking && !selected.isEmpty()) {
            int last = selected.get(selected.size() - 1);
            canvas.drawLine(getDotX(last), getDotY(last), curX, curY, linePaint);
        }
        float radius = Math.min(getWidth(), getHeight()) / 18f;
        for (int i = 0; i < 9; i++) {
            boolean isSel = selected.contains(i);
            canvas.drawCircle(getDotX(i), getDotY(i), isSel ? radius * 1.3f : radius, isSel ? activePaint : dotPaint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        curX = event.getX();
        curY = event.getY();
        float hitRadius = Math.min(getWidth(), getHeight()) / 7f;
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                selected.clear();
                tracking = true;
                checkHit(curX, curY, hitRadius);
                invalidate();
                return true;
            case MotionEvent.ACTION_MOVE:
                checkHit(curX, curY, hitRadius);
                invalidate();
                return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                tracking = false;
                if (!selected.isEmpty() && listener != null) {
                    StringBuilder sb = new StringBuilder();
                    for (int idx : selected) sb.append(idx);
                    listener.onPatternComplete(sb.toString());
                }
                selected.clear();
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y, float r) {
        for (int i = 0; i < 9; i++) {
            if (!selected.contains(i)) {
                float dx = x - getDotX(i);
                float dy = y - getDotY(i);
                if (Math.sqrt(dx * dx + dy * dy) <= r) {
                    selected.add(i);
                }
            }
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui", "PatternLockView.java"), PATTERN_VIEW)

# ---------------------------------------------------------------------------
# 3. CloneMetadataStore
# ---------------------------------------------------------------------------
CLONE_METADATA_STORE = """
package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import java.util.ArrayList;
import java.util.List;

public class CloneMetadataStore {
    private static final String PREFS = "veyra_clone_metadata_v3";

    public static class DeviceIdentity {
        public final String brand;
        public final String manufacturer;
        public final String model;
        public final String device;
        public final String product;

        public DeviceIdentity(String brand, String manufacturer, String model, String device, String product) {
            this.brand = brand;
            this.manufacturer = manufacturer;
            this.model = model;
            this.device = device;
            this.product = product;
        }
    }

    public static final DeviceIdentity[] PRESET_MODELS = new DeviceIdentity[]{
        new DeviceIdentity("Apple", "Apple", "iPhone 16 Pro Max", "iPhone17,2", "iPhone16ProMax"),
        new DeviceIdentity("Apple", "Apple", "iPhone 15 Pro Max", "iPhone16,2", "iPhone15ProMax"),
        new DeviceIdentity("Apple", "Apple", "iPhone 14 Pro", "iPhone15,2", "iPhone14Pro"),
        new DeviceIdentity("Apple", "Apple", "iPad Pro M4", "iPad16,6", "iPadProM4"),
        new DeviceIdentity("samsung", "Samsung", "SM-S928B (Galaxy S24 Ultra)", "e3q", "e3qxeea"),
        new DeviceIdentity("samsung", "Samsung", "SM-S918B (Galaxy S23 Ultra)", "dm3q", "dm3qxeea"),
        new DeviceIdentity("samsung", "Samsung", "SM-A546E (Galaxy A54 5G)", "a54x", "a54xnsxx"),
        new DeviceIdentity("Google", "Google", "Pixel 8 Pro", "husky", "husky"),
        new DeviceIdentity("Google", "Google", "Pixel 7a", "lynx", "lynx"),
        new DeviceIdentity("Xiaomi", "Xiaomi", "Xiaomi 14 Ultra", "aurora", "aurora_global"),
        new DeviceIdentity("Xiaomi", "Xiaomi", "Redmi Note 13 Pro+", "zircon", "zircon_global"),
        new DeviceIdentity("OnePlus", "OnePlus", "OnePlus 12", "OP5929L1", "CPH2581")
    };

    public static class RegionPreset {
        public final String regionName;
        public final double lat;
        public final double lon;
        public final String timeZoneId;
        public final String virtualIp;

        public RegionPreset(String regionName, double lat, double lon, String timeZoneId, String virtualIp) {
            this.regionName = regionName;
            this.lat = lat;
            this.lon = lon;
            this.timeZoneId = timeZoneId;
            this.virtualIp = virtualIp;
        }
    }

    public static final RegionPreset[] PRESET_REGIONS = new RegionPreset[]{
        new RegionPreset("Falkenstein, Germany", 50.4779, 12.3713, "Europe/Berlin", "88.198.48.210"),
        new RegionPreset("Frankfurt, Germany", 50.1109, 8.6821, "Europe/Berlin", "142.132.180.44"),
        new RegionPreset("New York, United States", 40.7128, -74.0060, "America/New_York", "104.244.72.115"),
        new RegionPreset("London, United Kingdom", 51.5074, -0.1278, "Europe/London", "51.140.104.22"),
        new RegionPreset("Amsterdam, Netherlands", 52.3676, 4.9041, "Europe/Amsterdam", "95.211.201.88"),
        new RegionPreset("Istanbul, Turkey", 41.0082, 28.9784, "Europe/Istanbul", "185.125.33.90"),
        new RegionPreset("Dubai, UAE", 25.2048, 55.2708, "Asia/Dubai", "94.200.140.19"),
        new RegionPreset("Tehran, Iran", 35.6892, 51.3890, "Asia/Tehran", "5.160.120.14")
    };

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static String getSpaceName(Context ctx, int userId, boolean isFa) {
        String custom = prefs(ctx).getString("space_custom_name_" + userId, "");
        if (custom != null && !custom.trim().isEmpty()) {
            return custom.trim();
        }
        if (userId == 0) return isFa ? "فضای ۱ (اصلی)" : "Space 1 (Primary)";
        if (userId == 1) return isFa ? "فضای ۲ (کار)" : "Space 2 (Work)";
        return isFa ? "فضای ۳ (محرمانه)" : "Space 3 (Private)";
    }

    public static void setSpaceCustomName(Context ctx, int userId, String customName) {
        prefs(ctx).edit().putString("space_custom_name_" + userId, customName == null ? "" : customName.trim()).apply();
    }

    public static boolean hasSpaceCustomName(Context ctx, int userId) {
        String custom = prefs(ctx).getString("space_custom_name_" + userId, "");
        return custom != null && !custom.trim().isEmpty();
    }

    public static void registerClonedPackage(Context ctx, String pkg, int userId, String appLabel) {
        SharedPreferences sp = prefs(ctx);
        String key = "registered_pkgs_space_" + userId;
        try {
            JSONArray arr = new JSONArray(sp.getString(key, "[]"));
            boolean exists = false;
            for (int i = 0; i < arr.length(); i++) {
                if (pkg.equals(arr.getString(i))) {
                    exists = true;
                    break;
                }
            }
            if (!exists) {
                arr.put(pkg);
                sp.edit().putString(key, arr.toString()).apply();
            }
            if (appLabel != null && !appLabel.isEmpty()) {
                sp.edit().putString("vault_label_" + pkg, appLabel).apply();
            }
        } catch (Exception ignored) {}
    }

    public static void unregisterClonedPackage(Context ctx, String pkg, int userId) {
        SharedPreferences sp = prefs(ctx);
        String key = "registered_pkgs_space_" + userId;
        try {
            JSONArray arr = new JSONArray(sp.getString(key, "[]"));
            JSONArray next = new JSONArray();
            for (int i = 0; i < arr.length(); i++) {
                String p = arr.getString(i);
                if (!pkg.equals(p)) next.put(p);
            }
            sp.edit().putString(key, next.toString()).apply();
        } catch (Exception ignored) {}
    }

    public static List<String> getRegisteredPackagesForSpace(Context ctx, int userId) {
        List<String> list = new ArrayList<>();
        try {
            JSONArray arr = new JSONArray(prefs(ctx).getString("registered_pkgs_space_" + userId, "[]"));
            for (int i = 0; i < arr.length(); i++) {
                list.add(arr.getString(i));
            }
        } catch (Exception ignored) {}
        return list;
    }

    public static String getVaultedAppLabel(Context ctx, String pkg) {
        return prefs(ctx).getString("vault_label_" + pkg, pkg);
    }

    public static void setVaultedApkPath(Context ctx, String pkg, String path) {
        prefs(ctx).edit().putString("vault_apk_" + pkg, path).apply();
    }

    public static String getVaultedApkPath(Context ctx, String pkg) {
        return prefs(ctx).getString("vault_apk_" + pkg, "");
    }

    private static String key(String pkg, int userId, String suffix) {
        return pkg + "_u" + userId + "_" + suffix;
    }

    public static String getAlias(Context ctx, String pkg, int userId, String defaultName) {
        String alias = prefs(ctx).getString(key(pkg, userId, "alias"), "");
        return (alias == null || alias.trim().isEmpty()) ? defaultName : alias.trim();
    }

    public static void setAlias(Context ctx, String pkg, int userId, String alias) {
        prefs(ctx).edit().putString(key(pkg, userId, "alias"), alias == null ? "" : alias.trim()).apply();
    }

    public static boolean isGlobalSpoofEnabled(Context ctx) {
        return prefs(ctx).getBoolean("global_spoof_enabled", true);
    }

    public static void setGlobalSpoofEnabled(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean("global_spoof_enabled", enabled).apply();
    }

    public static DeviceIdentity getGlobalDeviceIdentity(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        String brand = sp.getString("global_brand", "samsung");
        String manufacturer = sp.getString("global_manufacturer", "Samsung");
        String model = sp.getString("global_model", "SM-S928B (Galaxy S24 Ultra)");
        String device = sp.getString("global_device", "e3q");
        String product = sp.getString("global_product", "e3qxeea");
        return new DeviceIdentity(brand, manufacturer, model, device, product);
    }

    public static void setGlobalDeviceIdentity(Context ctx, DeviceIdentity id) {
        prefs(ctx).edit()
                .putString("global_brand", id.brand)
                .putString("global_manufacturer", id.manufacturer)
                .putString("global_model", id.model)
                .putString("global_device", id.device)
                .putString("global_product", id.product)
                .putBoolean("global_spoof_enabled", true)
                .apply();
    }

    public static String getGlobalRegionName(Context ctx) {
        return prefs(ctx).getString("global_region_name", "Falkenstein, Germany");
    }

    public static void setGlobalRegion(Context ctx, String regionName, double lat, double lon, String timeZoneId, String virtualIp) {
        prefs(ctx).edit()
                .putString("global_region_name", regionName)
                .putString("global_lat", String.valueOf(lat))
                .putString("global_lon", String.valueOf(lon))
                .putString("global_tz", timeZoneId)
                .putString("global_vip", virtualIp)
                .putBoolean("global_loc_enabled", true)
                .apply();
    }

    public static boolean isGlobalLocationEnabled(Context ctx) {
        return prefs(ctx).getBoolean("global_loc_enabled", true);
    }

    public static void setGlobalLocationEnabled(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean("global_loc_enabled", enabled).apply();
    }

    public static double[] getGlobalLocation(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        try {
            double lat = Double.parseDouble(sp.getString("global_lat", "50.4779"));
            double lon = Double.parseDouble(sp.getString("global_lon", "12.3713"));
            return new double[]{lat, lon};
        } catch (Exception e) {
            return new double[]{50.4779, 12.3713};
        }
    }

    public static String getGlobalTimeZone(Context ctx) {
        return prefs(ctx).getString("global_tz", "Europe/Berlin");
    }

    public static String getGlobalVirtualIp(Context ctx) {
        return prefs(ctx).getString("global_vip", "88.198.48.210");
    }

    public static void setGlobalProxy(Context ctx, boolean enabled, String host, int port) {
        prefs(ctx).edit()
                .putBoolean("global_proxy_enabled", enabled)
                .putString("global_proxy_host", host == null ? "" : host.trim())
                .putInt("global_proxy_port", port)
                .apply();
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

    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int userId) {
        return prefs(ctx).getBoolean(key(pkg, userId, "has_custom_device"), false);
    }

    public static void setCustomDeviceIdentity(Context ctx, String pkg, int userId, DeviceIdentity id) {
        prefs(ctx).edit()
                .putBoolean(key(pkg, userId, "has_custom_device"), true)
                .putString(key(pkg, userId, "brand"), id.brand)
                .putString(key(pkg, userId, "manufacturer"), id.manufacturer)
                .putString(key(pkg, userId, "model"), id.model)
                .putString(key(pkg, userId, "device"), id.device)
                .putString(key(pkg, userId, "product"), id.product)
                .apply();
    }

    public static void clearCustomDeviceIdentity(Context ctx, String pkg, int userId) {
        prefs(ctx).edit().putBoolean(key(pkg, userId, "has_custom_device"), false).apply();
    }

    public static DeviceIdentity getEffectiveDeviceIdentity(Context ctx, String pkg, int userId) {
        SharedPreferences sp = prefs(ctx);
        if (hasCustomDeviceIdentity(ctx, pkg, userId)) {
            return new DeviceIdentity(
                    sp.getString(key(pkg, userId, "brand"), "Apple"),
                    sp.getString(key(pkg, userId, "manufacturer"), "Apple"),
                    sp.getString(key(pkg, userId, "model"), "iPhone 16 Pro Max"),
                    sp.getString(key(pkg, userId, "device"), "iPhone17,2"),
                    sp.getString(key(pkg, userId, "product"), "iPhone16ProMax")
            );
        }
        return getGlobalDeviceIdentity(ctx);
    }

    public static boolean hasMockLocation(Context ctx, String pkg, int userId) {
        return prefs(ctx).getBoolean(key(pkg, userId, "has_loc"), false);
    }

    public static void setMockLocation(Context ctx, String pkg, int userId, double lat, double lon) {
        setMockLocationWithRegion(ctx, pkg, userId, lat, lon, inferRegionFromCoords(lat, lon));
    }

    public static void setMockLocationWithRegion(Context ctx, String pkg, int userId, double lat, double lon, String regionName) {
        prefs(ctx).edit()
                .putBoolean(key(pkg, userId, "has_loc"), true)
                .putString(key(pkg, userId, "lat"), String.valueOf(lat))
                .putString(key(pkg, userId, "lon"), String.valueOf(lon))
                .putString(key(pkg, userId, "region_name"), (regionName == null || regionName.trim().isEmpty()) ? inferRegionFromCoords(lat, lon) : regionName.trim())
                .apply();
    }

    public static void clearMockLocation(Context ctx, String pkg, int userId) {
        prefs(ctx).edit()
                .putBoolean(key(pkg, userId, "has_loc"), false)
                .remove(key(pkg, userId, "region_name"))
                .apply();
    }

    public static double[] getMockLocation(Context ctx, String pkg, int userId) {
        SharedPreferences sp = prefs(ctx);
        try {
            double lat = Double.parseDouble(sp.getString(key(pkg, userId, "lat"), "50.4779"));
            double lon = Double.parseDouble(sp.getString(key(pkg, userId, "lon"), "12.3713"));
            return new double[]{lat, lon};
        } catch (Exception e) {
            return new double[]{50.4779, 12.3713};
        }
    }

    public static double[] getEffectiveLocation(Context ctx, String pkg, int userId) {
        if (hasMockLocation(ctx, pkg, userId)) {
            return getMockLocation(ctx, pkg, userId);
        }
        return getGlobalLocation(ctx);
    }

    public static String getEffectiveRegionName(Context ctx, String pkg, int userId) {
        if (hasMockLocation(ctx, pkg, userId)) {
            String r = prefs(ctx).getString(key(pkg, userId, "region_name"), "");
            if (r != null && !r.isEmpty()) return r;
            double[] c = getMockLocation(ctx, pkg, userId);
            return inferRegionFromCoords(c[0], c[1]);
        }
        return getGlobalRegionName(ctx);
    }

    public static String inferRegionFromCoords(double lat, double lon) {
        double bestDist = Double.MAX_VALUE;
        String bestName = String.format(java.util.Locale.US, "Custom Region (%.2f, %.2f)", lat, lon);
        for (RegionPreset p : PRESET_REGIONS) {
            double d = Math.hypot(lat - p.lat, lon - p.lon);
            if (d < bestDist && d < 4.5) {
                bestDist = d;
                bestName = p.regionName;
            }
        }
        return bestName;
    }

    public static void clearAllForClone(Context ctx, String pkg, int userId) {
        prefs(ctx).edit()
                .remove(key(pkg, userId, "alias"))
                .remove(key(pkg, userId, "has_custom_device"))
                .remove(key(pkg, userId, "has_loc"))
                .remove(key(pkg, userId, "region_name"))
                .apply();
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core", "CloneMetadataStore.java"), CLONE_METADATA_STORE)

# ---------------------------------------------------------------------------
# 4. VirtualHookManager
# ---------------------------------------------------------------------------
VIRTUAL_HOOK_MANAGER = """
package com.veyravault.space.core;

import android.content.Context;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.SystemClock;
import android.util.Log;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.Locale;
import java.util.TimeZone;

public class VirtualHookManager {
    private static final String TAG = "VeyraHook";

    private static volatile double activeLat = 50.4779;
    private static volatile double activeLon = 12.3713;
    private static volatile String activeRegionName = "Falkenstein, Germany";
    private static volatile String activeVirtualIp = "88.198.48.210";
    private static volatile boolean locationSpoofActive = true;

    public static void installProcessHooks(Context context) {
        try {
            if (CloneMetadataStore.isGlobalSpoofEnabled(context)) {
                CloneMetadataStore.DeviceIdentity globalId = CloneMetadataStore.getGlobalDeviceIdentity(context);
                applyBuildFields(globalId);
            }
            if (CloneMetadataStore.isGlobalLocationEnabled(context)) {
                double[] loc = CloneMetadataStore.getGlobalLocation(context);
                activeLat = loc[0];
                activeLon = loc[1];
                activeRegionName = CloneMetadataStore.getGlobalRegionName(context);
                activeVirtualIp = CloneMetadataStore.getGlobalVirtualIp(context);
                locationSpoofActive = true;
                applyRegionTimeZoneAndNetworkProps(context);
            }
            installGmsAvailabilityBypass();
        } catch (Throwable t) {
            Log.w(TAG, "installProcessHooks warning: " + t.getMessage());
        }
    }

    public static void prepareForCloneLaunch(Context context, String packageName, int userId) {
        try {
            if (CloneMetadataStore.hasCustomDeviceIdentity(context, packageName, userId)) {
                CloneMetadataStore.DeviceIdentity customId = CloneMetadataStore.getEffectiveDeviceIdentity(context, packageName, userId);
                applyBuildFields(customId);
            } else if (CloneMetadataStore.isGlobalSpoofEnabled(context)) {
                CloneMetadataStore.DeviceIdentity globalId = CloneMetadataStore.getGlobalDeviceIdentity(context);
                applyBuildFields(globalId);
            }

            if (CloneMetadataStore.hasMockLocation(context, packageName, userId)) {
                double[] coords = CloneMetadataStore.getMockLocation(context, packageName, userId);
                activeLat = coords[0];
                activeLon = coords[1];
                activeRegionName = CloneMetadataStore.getEffectiveRegionName(context, packageName, userId);
                locationSpoofActive = true;
                pushBlackBoxMockLocation(packageName, userId, activeLat, activeLon);
            } else if (CloneMetadataStore.isGlobalLocationEnabled(context)) {
                double[] coords = CloneMetadataStore.getGlobalLocation(context);
                activeLat = coords[0];
                activeLon = coords[1];
                activeRegionName = CloneMetadataStore.getGlobalRegionName(context);
                locationSpoofActive = true;
                pushBlackBoxMockLocation(packageName, userId, activeLat, activeLon);
            } else {
                locationSpoofActive = false;
            }

            applyRegionTimeZoneAndNetworkProps(context);
            installGmsAvailabilityBypass();
        } catch (Throwable t) {
            Log.w(TAG, "prepareForCloneLaunch error: " + t.getMessage());
        }
    }

    private static void applyRegionTimeZoneAndNetworkProps(Context context) {
        try {
            String tzId = CloneMetadataStore.getGlobalTimeZone(context);
            if (activeRegionName.contains("Germany")) tzId = "Europe/Berlin";
            else if (activeRegionName.contains("United States") || activeRegionName.contains("New York")) tzId = "America/New_York";
            else if (activeRegionName.contains("United Kingdom") || activeRegionName.contains("London")) tzId = "Europe/London";
            else if (activeRegionName.contains("Netherlands")) tzId = "Europe/Amsterdam";
            else if (activeRegionName.contains("Turkey")) tzId = "Europe/Istanbul";
            else if (activeRegionName.contains("UAE") || activeRegionName.contains("Dubai")) tzId = "Asia/Dubai";

            TimeZone.setDefault(TimeZone.getTimeZone(tzId));
            System.setProperty("user.timezone", tzId);
            System.setProperty("veyra.virtual.region", activeRegionName);
            System.setProperty("veyra.virtual.ip", CloneMetadataStore.getGlobalVirtualIp(context));

            if (CloneMetadataStore.isGlobalProxyEnabled(context)) {
                String host = CloneMetadataStore.getGlobalProxyHost(context);
                int port = CloneMetadataStore.getGlobalProxyPort(context);
                if (host != null && !host.isEmpty()) {
                    System.setProperty("socksProxyHost", host);
                    System.setProperty("socksProxyPort", String.valueOf(port));
                    System.setProperty("http.proxyHost", host);
                    System.setProperty("http.proxyPort", String.valueOf(port));
                    System.setProperty("https.proxyHost", host);
                    System.setProperty("https.proxyPort", String.valueOf(port));
                }
            }
        } catch (Throwable ignored) {}
    }

    private static void pushBlackBoxMockLocation(String pkg, int userId, double lat, double lon) {
        try {
            Class<?> lmClass = Class.forName("top.niunaijun.blackbox.fake.frameworks.BLocationManager");
            Method getMethod = lmClass.getDeclaredMethod("get");
            Object blm = getMethod.invoke(null);
            if (blm != null) {
                Method setPattern = lmClass.getDeclaredMethod("setPattern", int.class, int.class);
                setPattern.invoke(blm, userId, 2);
                Class<?> bLocClass = Class.forName("top.niunaijun.blackbox.entity.location.BLocation");
                Constructor<?> cons = bLocClass.getDeclaredConstructor(double.class, double.class);
                cons.setAccessible(true);
                Object bLoc = cons.newInstance(lat, lon);
                Method setLocation = lmClass.getDeclaredMethod("setLocation", int.class, String.class, bLocClass);
                setLocation.invoke(blm, userId, pkg, bLoc);
            }
        } catch (Throwable ignored) {}
    }

    public static void installGmsAvailabilityBypass() {
        try {
            System.setProperty("veyra.gms.pretend_available", "true");
            try {
                Class<?> gmsUtil = Class.forName("com.google.android.gms.common.GooglePlayServicesUtil");
                setStaticIntField(gmsUtil, "GOOGLE_PLAY_SERVICES_VERSION_CODE", 240815000);
            } catch (Throwable ignored) {}
        } catch (Throwable ignored) {}
    }

    public static void applyBuildFields(CloneMetadataStore.DeviceIdentity id) {
        if (id == null) return;
        String cleanModel = id.model;
        int paren = cleanModel.indexOf(" (");
        if (paren > 0) cleanModel = cleanModel.substring(0, paren).trim();

        setStaticField(Build.class, "BRAND", id.brand);
        setStaticField(Build.class, "MANUFACTURER", id.manufacturer);
        setStaticField(Build.class, "MODEL", cleanModel);
        setStaticField(Build.class, "DEVICE", id.device);
        setStaticField(Build.class, "PRODUCT", id.product);
        setStaticField(Build.class, "BOARD", id.device);
        setStaticField(Build.class, "HARDWARE", id.device);

        String fp = String.format(Locale.US, "%s/%s/%s:14/UP1A.231005.007/VeyraVault3:user/release-keys",
                id.brand, id.product, id.device);
        setStaticField(Build.class, "FINGERPRINT", fp);
        System.setProperty("ro.product.model", cleanModel);
        System.setProperty("ro.product.brand", id.brand);
        System.setProperty("ro.product.manufacturer", id.manufacturer);
    }

    private static void setStaticField(Class<?> clazz, String fieldName, Object value) {
        try {
            Field field = clazz.getDeclaredField(fieldName);
            field.setAccessible(true);
            try {
                Field modifiersField = Field.class.getDeclaredField("modifiers");
                modifiersField.setAccessible(true);
                modifiersField.setInt(field, field.getModifiers() & ~Modifier.FINAL);
            } catch (Throwable ignored) {}
            field.set(null, value);
        } catch (Throwable ignored) {}
    }

    private static void setStaticIntField(Class<?> clazz, String fieldName, int value) {
        try {
            Field field = clazz.getDeclaredField(fieldName);
            field.setAccessible(true);
            field.setInt(null, value);
        } catch (Throwable ignored) {}
    }

    public static Location buildSpoofedLocation(String provider) {
        Location loc = new Location(provider != null ? provider : LocationManager.GPS_PROVIDER);
        loc.setLatitude(activeLat);
        loc.setLongitude(activeLon);
        loc.setAccuracy(4.5f);
        loc.setAltitude(115.0);
        loc.setTime(System.currentTimeMillis());
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
        }
        return loc;
    }

    public static boolean isLocationSpoofActive() {
        return locationSpoofActive;
    }

    public static String getActiveRegionName() {
        return activeRegionName;
    }

    public static String getActiveVirtualIp() {
        return activeVirtualIp;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core", "VirtualHookManager.java"), VIRTUAL_HOOK_MANAGER)

# ---------------------------------------------------------------------------
# 5. Engine.java
# ---------------------------------------------------------------------------
ENGINE_JAVA = """
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
import android.util.Log;
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
    private static final String TAG = "VeyraEngine";
    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(80);

    public static class AppModel {
        public final String name;
        public final String packageName;
        public final Drawable icon;
        public final int userId;

        public AppModel(String name, String packageName, Drawable icon, int userId) {
            this.name = name;
            this.packageName = packageName;
            this.icon = icon;
            this.userId = userId;
        }
    }

    public static void init(Context context) {
        try {
            VirtualHookManager.installProcessHooks(context);
            GmsSupportManager.ensureGmsForAllSpaces(context);
        } catch (Throwable t) {
            Log.e(TAG, "Engine.init warning", t);
        }
    }

    public static List<AppModel> getInstalledApps(Context context) {
        PackageManager pm = context.getPackageManager();
        List<ApplicationInfo> apps = pm.getInstalledApplications(PackageManager.GET_META_DATA);
        List<AppModel> result = new ArrayList<>();
        String ownPkg = context.getPackageName();

        for (ApplicationInfo info : apps) {
            if (ownPkg.equals(info.packageName)) continue;
            boolean isUserApp = (info.flags & ApplicationInfo.FLAG_SYSTEM) == 0
                    || (info.flags & ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0;
            boolean isPopularPreload = info.packageName.contains("chrome")
                    || info.packageName.contains("youtube")
                    || info.packageName.contains("whatsapp")
                    || info.packageName.contains("telegram")
                    || info.packageName.contains("instagram")
                    || info.packageName.contains("facebook");

            if (!isUserApp && !isPopularPreload) continue;
            if (pm.getLaunchIntentForPackage(info.packageName) == null && !isPopularPreload) continue;

            String label = info.loadLabel(pm).toString();
            Drawable icon = getCachedIcon(info.packageName, info, pm);
            result.add(new AppModel(label, info.packageName, icon, 0));
        }

        Collections.sort(result, (a, b) -> a.name.compareToIgnoreCase(b.name));
        return result;
    }

    public static List<AppModel> getClonedApps(Context context, int userId) {
        List<AppModel> list = new ArrayList<>();
        PackageManager pm = context.getPackageManager();
        Set<String> seen = new HashSet<>();

        try {
            List<ApplicationInfo> installed = BlackBoxCore.get().getInstalledApplications(0, userId);
            if (installed != null) {
                for (ApplicationInfo info : installed) {
                    if (info == null || info.packageName == null) continue;
                    if (info.packageName.contains("google.android.gms") || info.packageName.contains("google.android.gsf")) continue;
                    seen.add(info.packageName);
                    AppModel model = buildClonedAppModel(context, pm, info.packageName, info, userId);
                    if (model != null) list.add(model);
                }
            }
        } catch (Throwable t) {
            Log.e(TAG, "getClonedApps BCore error", t);
        }

        List<String> registered = CloneMetadataStore.getRegisteredPackagesForSpace(context, userId);
        for (String pkg : registered) {
            if (seen.contains(pkg)) continue;
            seen.add(pkg);
            String vaultApk = CloneMetadataStore.getVaultedApkPath(context, pkg);
            if (vaultApk != null && !vaultApk.isEmpty() && new File(vaultApk).exists()) {
                try {
                    if (!BlackBoxCore.get().isInstalled(pkg, userId)) {
                        BlackBoxCore.get().installPackageAsUser(new File(vaultApk), userId);
                    }
                } catch (Throwable ignored) {}
            }
            AppModel model = buildClonedAppModel(context, pm, pkg, null, userId);
            if (model != null) list.add(model);
        }

        return list;
    }

    private static AppModel buildClonedAppModel(Context context, PackageManager pm, String pkg, ApplicationInfo bcoreInfo, int userId) {
        try {
            String baseName = null;
            Drawable icon = ICON_CACHE.get(pkg);

            try {
                ApplicationInfo hostInfo = pm.getApplicationInfo(pkg, 0);
                baseName = hostInfo.loadLabel(pm).toString();
                if (icon == null) {
                    icon = hostInfo.loadIcon(pm);
                    if (icon != null) ICON_CACHE.put(pkg, icon);
                }
            } catch (Throwable ignored) {}

            if (baseName == null || icon == null) {
                String vaultApk = CloneMetadataStore.getVaultedApkPath(context, pkg);
                if (vaultApk != null && !vaultApk.isEmpty() && new File(vaultApk).exists()) {
                    PackageInfo pi = pm.getPackageArchiveInfo(vaultApk, 0);
                    if (pi != null && pi.applicationInfo != null) {
                        pi.applicationInfo.sourceDir = vaultApk;
                        pi.applicationInfo.publicSourceDir = vaultApk;
                        if (baseName == null) baseName = pi.applicationInfo.loadLabel(pm).toString();
                        if (icon == null) {
                            icon = pi.applicationInfo.loadIcon(pm);
                            if (icon != null) ICON_CACHE.put(pkg, icon);
                        }
                    }
                }
            }

            if ((baseName == null || icon == null) && bcoreInfo != null) {
                if (baseName == null) baseName = bcoreInfo.loadLabel(pm).toString();
                if (icon == null) icon = bcoreInfo.loadIcon(pm);
            }

            if (baseName == null || baseName.trim().isEmpty()) {
                baseName = CloneMetadataStore.getVaultedAppLabel(context, pkg);
            }
            if (icon == null) {
                icon = context.getApplicationInfo().loadIcon(pm);
            }

            String displayName = CloneMetadataStore.getAlias(context, pkg, userId, baseName);
            return new AppModel(displayName, pkg, icon, userId);
        } catch (Throwable t) {
            return null;
        }
    }

    public static boolean cloneApp(Context context, String packageName, int userId) {
        try {
            GmsSupportManager.installGms(context, userId);
            PackageManager pm = context.getPackageManager();
            ApplicationInfo appInfo = pm.getApplicationInfo(packageName, 0);
            String appLabel = appInfo.loadLabel(pm).toString();

            File vaultedBaseApk = backupPackageToVault(context, packageName, appInfo);

            InstallResult res;
            if (vaultedBaseApk != null && vaultedBaseApk.exists()) {
                res = BlackBoxCore.get().installPackageAsUser(vaultedBaseApk, userId);
            } else {
                res = BlackBoxCore.get().installPackageAsUser(packageName, userId);
            }

            boolean ok = res != null && res.success;
            if (!ok) {
                res = BlackBoxCore.get().installPackageAsUser(packageName, userId);
                ok = res != null && res.success;
            }

            if (ok) {
                extractNativeLibsToVirtualApp(context, packageName, appInfo);
                CloneMetadataStore.registerClonedPackage(context, packageName, userId, appLabel);
            }
            return ok;
        } catch (Throwable t) {
            Log.e(TAG, "cloneApp failed: " + packageName, t);
            return false;
        }
    }

    public static boolean installExternalApkFileToVault(Context context, File externalApk, int userId) {
        try {
            if (externalApk == null || !externalApk.exists()) return false;
            PackageManager pm = context.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(externalApk.getAbsolutePath(), 0);
            if (pi == null || pi.packageName == null) return false;

            String pkg = pi.packageName;
            pi.applicationInfo.sourceDir = externalApk.getAbsolutePath();
            pi.applicationInfo.publicSourceDir = externalApk.getAbsolutePath();
            String label = pi.applicationInfo.loadLabel(pm).toString();

            GmsSupportManager.installGms(context, userId);

            File vaultDir = new File(context.getFilesDir(), "apk_vault/" + pkg);
            if (!vaultDir.exists()) vaultDir.mkdirs();
            File vaultBase = new File(vaultDir, "base.apk");
            copyFile(externalApk, vaultBase);
            CloneMetadataStore.setVaultedApkPath(context, pkg, vaultBase.getAbsolutePath());

            InstallResult res = BlackBoxCore.get().installPackageAsUser(vaultBase, userId);
            boolean ok = res != null && res.success;
            if (ok) {
                extractAbiFromApkZip(vaultBase, new File(vaultDir, "lib"));
                syncLibsToBlackBoxDir(context, pkg, new File(vaultDir, "lib"));
                CloneMetadataStore.registerClonedPackage(context, pkg, userId, label);
            }
            return ok;
        } catch (Throwable t) {
            Log.e(TAG, "installExternalApkFileToVault error", t);
            return false;
        }
    }

    private static File backupPackageToVault(Context context, String pkg, ApplicationInfo appInfo) {
        try {
            File vaultDir = new File(context.getFilesDir(), "apk_vault/" + pkg);
            if (!vaultDir.exists()) vaultDir.mkdirs();

            File baseSrc = new File(appInfo.sourceDir);
            File baseDst = new File(vaultDir, "base.apk");
            if (baseSrc.exists()) {
                copyFile(baseSrc, baseDst);
                CloneMetadataStore.setVaultedApkPath(context, pkg, baseDst.getAbsolutePath());
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP && appInfo.splitSourceDirs != null) {
                int idx = 0;
                for (String splitPath : appInfo.splitSourceDirs) {
                    File splitSrc = new File(splitPath);
                    if (splitSrc.exists()) {
                        copyFile(splitSrc, new File(vaultDir, "split_" + (idx++) + ".apk"));
                    }
                }
            }
            return baseDst;
        } catch (Throwable t) {
            return null;
        }
    }

    private static void extractNativeLibsToVirtualApp(Context context, String pkg, ApplicationInfo appInfo) {
        try {
            File vaultLibDir = new File(context.getFilesDir(), "apk_vault/" + pkg + "/lib");
            if (!vaultLibDir.exists()) vaultLibDir.mkdirs();

            if (appInfo.sourceDir != null) {
                extractAbiFromApkZip(new File(appInfo.sourceDir), vaultLibDir);
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP && appInfo.splitSourceDirs != null) {
                for (String split : appInfo.splitSourceDirs) {
                    extractAbiFromApkZip(new File(split), vaultLibDir);
                }
            }
            syncLibsToBlackBoxDir(context, pkg, vaultLibDir);
        } catch (Throwable t) {
            Log.w(TAG, "extractNativeLibs warning: " + t.getMessage());
        }
    }

    private static void extractAbiFromApkZip(File apkFile, File outLibDir) {
        if (apkFile == null || !apkFile.exists()) return;
        String primaryAbi = Build.CPU_ABI != null && Build.CPU_ABI.contains("64") ? "arm64-v8a" : "armeabi-v7a";
        try (ZipFile zip = new ZipFile(apkFile)) {
            Enumeration<? extends ZipEntry> entries = zip.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                if (!entry.isDirectory() && name.startsWith("lib/") && name.endsWith(".so")) {
                    if (name.contains(primaryAbi) || name.contains("armeabi-v7a")) {
                        String fileName = name.substring(name.lastIndexOf('/') + 1);
                        File target = new File(outLibDir, fileName);
                        if (!target.exists() || target.length() != entry.getSize()) {
                            try (InputStream is = zip.getInputStream(entry);
                                 FileOutputStream fos = new FileOutputStream(target)) {
                                byte[] buf = new byte[8192];
                                int len;
                                while ((len = is.read(buf)) > 0) fos.write(buf, 0, len);
                            }
                        }
                    }
                }
            }
        } catch (Throwable ignored) {}
    }

    private static void syncLibsToBlackBoxDir(Context context, String pkg, File vaultLibDir) {
        try {
            File[] soFiles = vaultLibDir.listFiles();
            if (soFiles == null || soFiles.length == 0) return;

            File dataDir = context.getDataDir();
            File[] possibleDirs = new File[]{
                new File(dataDir, "virtual/data/app/" + pkg + "/lib"),
                new File(dataDir, "virtual/data/app/" + pkg + "/lib/arm64"),
                new File(dataDir, "virtual/data/app/" + pkg + "/lib/arm"),
                new File(context.getFilesDir(), "virtual/data/app/" + pkg + "/lib")
            };
            for (File dir : possibleDirs) {
                dir.mkdirs();
                for (File so : soFiles) {
                    File dst = new File(dir, so.getName());
                    if (!dst.exists()) copyFile(so, dst);
                }
            }
        } catch (Throwable ignored) {}
    }

    private static void copyFile(File src, File dst) throws Exception {
        try (FileInputStream fis = new FileInputStream(src);
             FileOutputStream fos = new FileOutputStream(dst)) {
            byte[] buf = new byte[16384];
            int len;
            while ((len = fis.read(buf)) > 0) fos.write(buf, 0, len);
        }
    }

    public static boolean launchClone(Context context, String packageName, int userId) {
        try {
            GmsSupportManager.installGms(context, userId);
            VirtualHookManager.prepareForCloneLaunch(context, packageName, userId);

            File vaultLibDir = new File(context.getFilesDir(), "apk_vault/" + packageName + "/lib");
            if (vaultLibDir.exists()) {
                syncLibsToBlackBoxDir(context, packageName, vaultLibDir);
            }

            Intent explicitIntent = resolveRealMainLauncherIntent(context, packageName);
            if (explicitIntent != null) {
                try {
                    Method launchByIntent = BlackBoxCore.class.getMethod("launchApk", Intent.class, int.class);
                    Object r = launchByIntent.invoke(BlackBoxCore.get(), explicitIntent, userId);
                    if (r instanceof Boolean && (Boolean) r) return true;
                } catch (Throwable ignored) {}
            }

            return BlackBoxCore.get().launchApk(packageName, userId);
        } catch (Throwable t) {
            Log.e(TAG, "launchClone error: " + packageName, t);
            return false;
        }
    }

    private static Intent resolveRealMainLauncherIntent(Context context, String pkg) {
        try {
            PackageManager pm = context.getPackageManager();
            if (pkg.contains("chrome")) {
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
                    if (ri.activityInfo != null && ri.activityInfo.name != null) {
                        String actName = ri.activityInfo.name.toLowerCase();
                        if (actName.contains("devui") || actName.contains("devtools") || actName.contains("debug")) {
                            continue;
                        }
                        Intent mainIntent = new Intent(Intent.ACTION_MAIN);
                        mainIntent.addCategory(Intent.CATEGORY_LAUNCHER);
                        mainIntent.setComponent(new ComponentName(pkg, ri.activityInfo.name));
                        mainIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        return mainIntent;
                    }
                }
            }
        } catch (Throwable ignored) {}
        return null;
    }

    public static void stopClone(String packageName, int userId) {
        try {
            for (Method m : BlackBoxCore.class.getMethods()) {
                if (m.getName().equals("stopPackage") && m.getParameterTypes().length == 2) {
                    m.invoke(BlackBoxCore.get(), packageName, userId);
                    return;
                }
            }
        } catch (Throwable ignored) {}
    }

    public static void clearCloneData(String packageName, int userId) {
        try {
            for (Method m : BlackBoxCore.class.getMethods()) {
                if (m.getName().equals("clearPackage") && m.getParameterTypes().length == 2) {
                    m.invoke(BlackBoxCore.get(), packageName, userId);
                    return;
                }
            }
        } catch (Throwable ignored) {}
    }

    public static void uninstallClone(Context context, String packageName, int userId) {
        try {
            for (Method m : BlackBoxCore.class.getMethods()) {
                if (m.getName().equals("uninstallPackageAsUser") && m.getParameterTypes().length == 2) {
                    m.invoke(BlackBoxCore.get(), packageName, userId);
                    break;
                }
            }
        } catch (Throwable ignored) {}
        CloneMetadataStore.unregisterClonedPackage(context, packageName, userId);
        CloneMetadataStore.clearAllForClone(context, packageName, userId);
    }

    private static Drawable getCachedIcon(String pkg, ApplicationInfo info, PackageManager pm) {
        Drawable d = ICON_CACHE.get(pkg);
        if (d == null) {
            d = info.loadIcon(pm);
            if (d != null) ICON_CACHE.put(pkg, d);
        }
        return d;
    }

    public static void trimCache() {
        ICON_CACHE.evictAll();
        System.gc();
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core", "Engine.java"), ENGINE_JAVA)

# ---------------------------------------------------------------------------
# 6. SecurityManager & VaultDeviceAdminReceiver
# ---------------------------------------------------------------------------
SECURITY_MANAGER = """
package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;
import java.security.MessageDigest;

public class SecurityManager {
    private static final String PREFS = "veyra_security_v3";
    private static final String KEY_LOCK_ENABLED = "lock_enabled";
    private static final String KEY_PRIMARY_MODE = "primary_mode";
    private static final String KEY_PIN_HASH = "pin_hash";
    private static final String KEY_PATTERN_HASH = "pattern_hash";

    public static final int MODE_PIN = 1;
    public static final int MODE_PATTERN = 2;

    private static volatile boolean sessionUnlocked = false;

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static boolean isLockEnabled(Context ctx) {
        return prefs(ctx).getBoolean(KEY_LOCK_ENABLED, false)
                && (hasPinConfigured(ctx) || hasPatternConfigured(ctx));
    }

    public static void setLockEnabled(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean(KEY_LOCK_ENABLED, enabled).apply();
    }

    public static boolean hasPinConfigured(Context ctx) {
        String h = prefs(ctx).getString(KEY_PIN_HASH, "");
        return h != null && !h.isEmpty();
    }

    public static boolean hasPatternConfigured(Context ctx) {
        String h = prefs(ctx).getString(KEY_PATTERN_HASH, "");
        return h != null && !h.isEmpty();
    }

    public static boolean hasBothConfigured(Context ctx) {
        return hasPinConfigured(ctx) && hasPatternConfigured(ctx);
    }

    public static int getPrimaryLockMode(Context ctx) {
        int mode = prefs(ctx).getInt(KEY_PRIMARY_MODE, MODE_PIN);
        if (mode == MODE_PIN && !hasPinConfigured(ctx) && hasPatternConfigured(ctx)) {
            return MODE_PATTERN;
        }
        if (mode == MODE_PATTERN && !hasPatternConfigured(ctx) && hasPinConfigured(ctx)) {
            return MODE_PIN;
        }
        return mode;
    }

    public static void setPrimaryLockMode(Context ctx, int mode) {
        prefs(ctx).edit().putInt(KEY_PRIMARY_MODE, mode).apply();
    }

    public static void savePin(Context ctx, String pin) {
        prefs(ctx).edit()
                .putString(KEY_PIN_HASH, sha256(pin))
                .putBoolean(KEY_LOCK_ENABLED, true)
                .apply();
        if (!hasPatternConfigured(ctx)) {
            setPrimaryLockMode(ctx, MODE_PIN);
        }
    }

    public static void savePattern(Context ctx, String pattern) {
        prefs(ctx).edit()
                .putString(KEY_PATTERN_HASH, sha256(pattern))
                .putBoolean(KEY_LOCK_ENABLED, true)
                .apply();
        if (!hasPinConfigured(ctx)) {
            setPrimaryLockMode(ctx, MODE_PATTERN);
        }
    }

    public static void disableAllLocks(Context ctx) {
        prefs(ctx).edit()
                .putBoolean(KEY_LOCK_ENABLED, false)
                .remove(KEY_PIN_HASH)
                .remove(KEY_PATTERN_HASH)
                .apply();
        sessionUnlocked = true;
    }

    public static boolean verifyPin(Context ctx, String inputPin) {
        String stored = prefs(ctx).getString(KEY_PIN_HASH, "");
        return !stored.isEmpty() && stored.equals(sha256(inputPin));
    }

    public static boolean verifyPattern(Context ctx, String inputPattern) {
        String stored = prefs(ctx).getString(KEY_PATTERN_HASH, "");
        return !stored.isEmpty() && stored.equals(sha256(inputPattern));
    }

    public static boolean isSessionUnlocked() {
        return sessionUnlocked;
    }

    public static void setSessionUnlocked(boolean unlocked) {
        sessionUnlocked = unlocked;
    }

    public static boolean isUninstallGuardAuthorizedRemoval(Context ctx) {
        return prefs(ctx).getBoolean("allow_admin_removal_now", false);
    }

    public static void setAllowAdminRemovalNow(Context ctx, boolean allow) {
        prefs(ctx).edit().putBoolean("allow_admin_removal_now", allow).apply();
    }

    private static String sha256(String input) {
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
}
"""
write_file(os.path.join(JAVA_BASE, "security", "SecurityManager.java"), SECURITY_MANAGER)

DEVICE_ADMIN_RECEIVER = """
package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    @Override
    public void onEnabled(Context context, Intent intent) {
        SecurityManager.setAllowAdminRemovalNow(context, false);
        Toast.makeText(context, "محافظ ضدحذف VeyraVault فعال شد", Toast.LENGTH_SHORT).show();
    }

    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        if (!SecurityManager.isUninstallGuardAuthorizedRemoval(context)) {
            SecurityManager.setSessionUnlocked(false);
            try {
                Intent lockIntent = new Intent(context, SecurityLockActivity.class);
                lockIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                lockIntent.putExtra("FORCE_ADMIN_PROTECT", true);
                context.startActivity(lockIntent);
            } catch (Throwable ignored) {}
            Toast.makeText(context, "⛔ حذف مقدور نمی‌باشد! ابتدا رمز VeyraVault را وارد کنید.", Toast.LENGTH_LONG).show();
        }
        return "⛔ حذف مقدور نمی‌باشد! غیرفعال‌سازی فقط از داخل تنظیمات امنیتی VeyraVault با رمز عبور مجاز است.";
    }

    @Override
    public void onDisabled(Context context, Intent intent) {
        Toast.makeText(context, "محافظ ضدحذف غیرفعال شد", Toast.LENGTH_SHORT).show();
    }
}
"""
write_file(os.path.join(JAVA_BASE, "security", "VaultDeviceAdminReceiver.java"), DEVICE_ADMIN_RECEIVER)

print("[v3-part1] Completed successfully.")
