#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Complete Upgrade Script - Part 1 (Self-Contained Infrastructure + Core + Security)
"""

import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA_BASE = os.path.join(ROOT, "app", "src", "main", "java", "com", "veyravault", "space")
RES_BASE = os.path.join(ROOT, "app", "src", "main", "res")
MANIFEST_PATH = os.path.join(ROOT, "app", "src", "main", "AndroidManifest.xml")
APP_GRADLE_PATH = os.path.join(ROOT, "app", "build.gradle")

def write_file(rel_dir, filename, content, base=JAVA_BASE):
    target_dir = os.path.join(base, rel_dir) if rel_dir else base
    os.makedirs(target_dir, exist_ok=True)
    full_path = os.path.join(target_dir, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[v3-Part1] Wrote: {full_path}")

def clean_legacy_sources():
    if os.path.exists(JAVA_BASE):
        shutil.rmtree(JAVA_BASE)
    os.makedirs(JAVA_BASE, exist_ok=True)
    layout_dir = os.path.join(RES_BASE, "layout")
    if os.path.exists(layout_dir):
        shutil.rmtree(layout_dir)

def patch_app_build_gradle():
    if not os.path.exists(APP_GRADLE_PATH):
        return
    with open(APP_GRADLE_PATH, "r", encoding="utf-8") as f:
        txt = f.read()
    if "osmdroid-android" not in txt:
        txt = txt.replace(
            "dependencies {",
            "dependencies {\n    implementation 'org.osmdroid:osmdroid-android:6.1.14'"
        )
    txt = txt.replace('versionName "1.0.0"', 'versionName "3.0.0"').replace('versionName "2.0.0"', 'versionName "3.0.0"')
    txt = txt.replace('versionCode 1', 'versionCode 3').replace('versionCode 2', 'versionCode 3')
    with open(APP_GRADLE_PATH, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[v3-Part1] Patched app/build.gradle with osmdroid & version 3.0.0")

# ---------------------------------------------------------------------------
# 0. ANDROID MANIFEST, STRINGS, STYLES, DEVICE ADMIN XML & APPLICATION CLASS
# ---------------------------------------------------------------------------

ANDROID_MANIFEST_XML = r'''
<?xml version="1.0" encoding="utf-8"?>
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
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />

    <application
        android:name=".VeyraApplication"
        android:allowBackup="false"
        android:icon="@drawable/ic_launcher"
        android:roundIcon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:largeHeap="true"
        android:usesCleartextTraffic="true"
        android:theme="@style/AppTheme"
        tools:replace="android:allowBackup,android:icon,android:roundIcon,android:label,android:theme">

        <activity
            android:name=".ui.MainActivity"
            android:exported="true"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- Disguise Aliases -->
        <activity-alias
            android:name=".AliasCalculator"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_dialog_dialer"
            android:label="Calculator"
            android:targetActivity=".ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity-alias
            android:name=".AliasNotepad"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_menu_edit"
            android:label="Notes"
            android:targetActivity=".ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity
            android:name=".ui.AddAppActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize" />

        <activity
            android:name=".ui.SetLocationActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize" />

        <activity
            android:name=".ui.GlobalEnvironmentActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize" />

        <activity
            android:name=".ui.SecuritySettingsActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize" />

        <activity
            android:name=".ui.SecurityLockActivity"
            android:exported="false"
            android:launchMode="singleTop"
            android:configChanges="locale|layoutDirection|orientation|screenSize" />

        <activity
            android:name=".ui.GuideActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize" />

        <activity
            android:name=".ui.AboutActivity"
            android:exported="false"
            android:configChanges="locale|layoutDirection|orientation|screenSize" />

        <receiver
            android:name=".security.VaultDeviceAdminReceiver"
            android:description="@string/device_admin_desc"
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
'''

IC_LAUNCHER_XML = r'''
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#0F172A"
        android:pathData="M0,0h108v108h-108z"/>
    <path
        android:fillColor="#2563EB"
        android:pathData="M54,16L22,30v24c0,22.2 13.6,42.9 32,48c18.4,-5.1 32,-25.8 32,-48V30L54,16z"/>
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M54,32c-8.8,0 -16,7.2 -16,16v6h-4v22h40V54h-4v-6c0,-8.8 -7.2,-16 -16,-16zM44,48c0,-5.5 4.5,-10 10,-10s10,4.5 10,10v6H44v-6z"/>
</vector>
'''

DEVICE_ADMIN_XML = r'''
<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <force-lock />
    </uses-policies>
</device-admin>
'''

STRINGS_XML = r'''
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="device_admin_desc">حفاظت در برابر حذف غیرمجاز برنامه VeyraVault</string>
</resources>
'''

STYLES_XML = r'''
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="android:Theme.Material.Light.NoActionBar">
        <item name="android:colorPrimary">#0F172A</item>
        <item name="android:colorPrimaryDark">#090D16</item>
        <item name="android:colorAccent">#2563EB</item>
        <item name="android:windowBackground">#F1F5F9</item>
    </style>
</resources>
'''

VEYRA_APPLICATION_JAVA = r'''
package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.Engine;
import com.veyravault.space.helper.LocaleHelper;

public class VeyraApplication extends Application {
    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(LocaleHelper.applyLocale(base));
        Engine.doAttachBaseContext(base);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        LocaleHelper.applyLocale(this);
        Engine.doOnCreate(this);
    }
}
'''

# ---------------------------------------------------------------------------
# 1. VECTOR DRAWABLE ICONS FOR BOTTOM NAVIGATION BAR
# ---------------------------------------------------------------------------
IC_DASHBOARD_XML = r'''
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M3,13h8V3H3V13zM3,21h8v-6H3V21zM13,21h8V11h-8V21zM13,3v6h8V3H13z"/>
</vector>
'''

IC_SPACES_XML = r'''
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M4,8h4V4H4V8zM10,20h4v-4h-4V20zM4,20h4v-4H4V20zM4,14h4v-4H4V14zM10,14h4v-4h-4V14zM16,4v4h4V4H16zM10,8h4V4h-4V8zM16,14h4v-4h-4V14zM16,20h4v-4h-4V20z"/>
</vector>
'''

IC_ADD_XML = r'''
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
</vector>
'''

IC_GUIDE_XML = r'''
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM13,19h-2v-2h2v2zM15.07,11.25l-0.9,0.92C13.45,12.9 13,13.5 13,15h-2v-0.5c0,-1.1 0.45,-2.1 1.17,-2.83l1.24,-1.26c0.37,-0.36 0.59,-0.86 0.59,-1.41 0,-1.1 -0.9,-2 -2,-2s-2,0.9 -2,2H8c0,-2.21 1.79,-4 4,-4s4,1.79 4,4c0,0.88 -0.36,1.68 -0.93,2.25z"/>
</vector>
'''

IC_SETTINGS_XML = r'''
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"/>
</vector>
'''

# ---------------------------------------------------------------------------
# 2. JALALI (SOLAR HIJRI) & WORLD CLOCK UTILITY
# ---------------------------------------------------------------------------
JALALI_CLOCK_UTIL_JAVA = r'''
package com.veyravault.space.helper;

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
            jd = 1 + ((days - 186) % 30);
        }
        return new int[]{jy, jm, jd};
    }

    public static String getTehranTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("Asia/Tehran"));
        return sdf.format(new Date());
    }

    public static String getTehranJalaliDate(boolean persian) {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("Asia/Tehran"));
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int dow = cal.get(Calendar.DAY_OF_WEEK);
        int[] jalali = gregorianToJalali(gy, gm, gd);
        if (persian) {
            String wd = PERSIAN_WEEKDAYS_FA[dow - 1];
            String monthName = PERSIAN_MONTHS_FA[jalali[1] - 1];
            return wd + " " + toPersianDigits(String.valueOf(jalali[2])) + " " + monthName + " " + toPersianDigits(String.valueOf(jalali[0]));
        } else {
            String monthName = PERSIAN_MONTHS_EN[jalali[1] - 1];
            return jalali[2] + " " + monthName + " " + jalali[0] + " SH";
        }
    }

    public static String getNewYorkTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String getNewYorkGregorianDate(boolean persian) {
        SimpleDateFormat sdf = new SimpleDateFormat(persian ? "yyyy/MM/dd (EEEE)" : "EEE, MMM dd, yyyy", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String toPersianDigits(String s) {
        if (s == null) return "";
        char[] PersianDigits = {'۰','۱','۲','۳','۴','۵','۶','۷','۸','۹'};
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c >= '0' && c <= '9') {
                out.append(PersianDigits[c - '0']);
            } else {
                out.append(c);
            }
        }
        return out.toString();
    }
}
'''

# ---------------------------------------------------------------------------
# 3. LOCALE HELPER, BASE ACTIVITY, GMS SUPPORT, APP DISGUISE & PATTERN VIEW
# ---------------------------------------------------------------------------
LOCALE_HELPER_JAVA = r'''
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

    public static String getLanguage(Context ctx) {
        SharedPreferences sp = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getString(KEY_LANG, "fa");
    }

    public static boolean isPersian(Context ctx) {
        return "fa".equalsIgnoreCase(getLanguage(ctx));
    }

    public static void setLanguage(Context ctx, String lang) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
           .edit().putString(KEY_LANG, lang).apply();
    }

    public static String toggleLanguage(Context ctx) {
        String next = isPersian(ctx) ? "en" : "fa";
        setLanguage(ctx, next);
        applyLocale(ctx);
        return next;
    }

    public static Context applyLocale(Context context) {
        String lang = getLanguage(context);
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
'''

BASE_ACTIVITY_JAVA = r'''
package com.veyravault.space.helper;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.security.SecurityManager;
import com.veyravault.space.ui.SecurityLockActivity;

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
        LocaleHelper.applyLocale(this);
        applyDirection();
    }

    protected void applyDirection() {
        if (Build.VERSION.SDK_INT >= 17) {
            getWindow().getDecorView().setLayoutDirection(
                LocaleHelper.isPersian(this) ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
    }

    protected int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }

    protected LinearLayout createHeader(String titleText, final boolean showBack) {
        final boolean fa = LocaleHelper.isPersian(this);
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setBackgroundColor(Color.parseColor("#0F172A"));
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(14), dp(12), dp(14), dp(12));

        if (showBack) {
            TextView backBtn = new TextView(this);
            backBtn.setText(fa ? "→" : "←");
            backBtn.setTextColor(Color.WHITE);
            backBtn.setTextSize(20f);
            backBtn.setTypeface(Typeface.DEFAULT_BOLD);
            backBtn.setPadding(dp(8), dp(2), dp(12), dp(2));
            backBtn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    finish();
                }
            });
            bar.addView(backBtn);
        }

        TextView title = new TextView(this);
        title.setText(titleText);
        title.setTextColor(Color.WHITE);
        title.setTextSize(17f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        LinearLayout.LayoutParams tLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        bar.addView(title, tLp);

        TextView lockBtn = new TextView(this);
        lockBtn.setText(fa ? "🔒 قفل سریع" : "🔒 Lock");
        lockBtn.setTextColor(Color.parseColor("#FDE047"));
        lockBtn.setTextSize(12f);
        lockBtn.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable lockBg = new GradientDrawable();
        lockBg.setColor(Color.parseColor("#1E293B"));
        lockBg.setCornerRadius(dp(8));
        lockBg.setStroke(dp(1), Color.parseColor("#475569"));
        lockBtn.setBackground(lockBg);
        lockBtn.setPadding(dp(10), dp(6), dp(10), dp(6));
        LinearLayout.LayoutParams lockLp = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT
        );
        lockLp.setMargins(dp(6), 0, dp(6), 0);
        lockBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (!SecurityManager.isSecurityEnabled(BaseActivity.this)) {
                    Toast.makeText(BaseActivity.this,
                        fa ? "ابتدا از بخش تنظیمات امنیتی، پین یا الگو را فعال کنید" : "Please configure PIN or Pattern in Security Settings first",
                        Toast.LENGTH_SHORT).show();
                    return;
                }
                SecurityManager.setSessionUnlocked(false);
                Intent i = new Intent(BaseActivity.this, SecurityLockActivity.class);
                startActivity(i);
            }
        });
        bar.addView(lockBtn, lockLp);

        TextView langBtn = new TextView(this);
        langBtn.setText(fa ? "EN" : "فارسی");
        langBtn.setTextColor(Color.WHITE);
        langBtn.setTextSize(12f);
        langBtn.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable langBg = new GradientDrawable();
        langBg.setColor(Color.parseColor("#2563EB"));
        langBg.setCornerRadius(dp(8));
        langBtn.setBackground(langBg);
        langBtn.setPadding(dp(10), dp(6), dp(10), dp(6));
        langBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                LocaleHelper.toggleLanguage(BaseActivity.this);
                recreate();
            }
        });
        bar.addView(langBtn);

        return bar;
    }
}
'''

GMS_SUPPORT_MANAGER_JAVA = r'''
package com.veyravault.space.core;

import android.content.Context;
import android.content.pm.PackageManager;
import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    public static boolean isGmsSupported(Context ctx) {
        try {
            ctx.getPackageManager().getPackageInfo("com.google.android.gms", 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    public static boolean isGmsInstalled(int spaceId) {
        try {
            return BlackBoxCore.get().isInstallGms(spaceId);
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean installGms(int spaceId) {
        try {
            if (!BlackBoxCore.get().isInstallGms(spaceId)) {
                return BlackBoxCore.get().installGms(spaceId);
            }
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean installGmsForAllSpaces(Context ctx) {
        boolean ok = true;
        for (int i = 0; i < 4; i++) {
            if (!installGms(i)) {
                ok = false;
            }
        }
        return ok;
    }
}
'''

APP_DISGUISE_MANAGER_JAVA = r'''
package com.veyravault.space.helper;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;

public class AppDisguiseManager {
    private static final String PREFS = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode";

    public static final int MODE_DEFAULT = 0;
    public static final int MODE_CALCULATOR = 1;
    public static final int MODE_NOTEPAD = 2;

    public static int getCurrentDisguise(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getInt(KEY_MODE, MODE_DEFAULT);
    }

    public static void applyDisguise(Context ctx, int mode) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putInt(KEY_MODE, mode).apply();
        PackageManager pm = ctx.getPackageManager();
        String pkg = ctx.getPackageName();

        ComponentName mainComp = new ComponentName(pkg, pkg + ".ui.MainActivity");
        ComponentName calcComp = new ComponentName(pkg, pkg + ".AliasCalculator");
        ComponentName noteComp = new ComponentName(pkg, pkg + ".AliasNotepad");

        try {
            pm.setComponentEnabledSetting(mainComp,
                mode == MODE_DEFAULT ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED : PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP);
            pm.setComponentEnabledSetting(calcComp,
                mode == MODE_CALCULATOR ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED : PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP);
            pm.setComponentEnabledSetting(noteComp,
                mode == MODE_NOTEPAD ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED : PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP);
        } catch (Throwable ignored) {}
    }
}
'''

PATTERN_LOCK_VIEW_JAVA = r'''
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
        void onPatternDetected(String pattern);
    }

    public interface OnPatternCompleteListener {
        void onPatternComplete(String patternString);
    }

    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final List<Integer> selectedDots = new ArrayList<>();
    private float currentX, currentY;
    private boolean isDrawing = false;
    private OnPatternListener patternListener;
    private OnPatternCompleteListener completeListener;

    public PatternLockView(Context context, OnPatternListener l) {
        super(context);
        this.patternListener = l;
        initPaints();
    }

    public PatternLockView(Context context, OnPatternCompleteListener l) {
        super(context);
        this.completeListener = l;
        initPaints();
    }

    private void initPaints() {
        dotPaint.setColor(Color.parseColor("#64748B"));
        dotPaint.setStyle(Paint.Style.FILL);

        activePaint.setColor(Color.parseColor("#38BDF8"));
        activePaint.setStyle(Paint.Style.FILL);

        linePaint.setColor(Color.parseColor("#38BDF8"));
        linePaint.setStrokeWidth(10f);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
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
            canvas.drawLine(getDotX(last), getDotY(last), currentX, currentY, linePaint);
        }
        for (int i = 0; i < 9; i++) {
            boolean active = selectedDots.contains(i);
            canvas.drawCircle(getDotX(i), getDotY(i), active ? 24f : 16f, active ? activePaint : dotPaint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        currentX = event.getX();
        currentY = event.getY();
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                selectedDots.clear();
                isDrawing = true;
                checkHit(currentX, currentY);
                invalidate();
                return true;
            case MotionEvent.ACTION_MOVE:
                checkHit(currentX, currentY);
                invalidate();
                return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                isDrawing = false;
                if (!selectedDots.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < selectedDots.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(selectedDots.get(i));
                    }
                    String result = sb.toString();
                    if (patternListener != null) {
                        patternListener.onPatternDetected(result);
                    }
                    if (completeListener != null) {
                        completeListener.onPatternComplete(result);
                    }
                }
                selectedDots.clear();
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y) {
        float hitRadius = Math.min(getWidth(), getHeight()) / 7f;
        for (int i = 0; i < 9; i++) {
            if (!selectedDots.contains(i)) {
                float dx = x - getDotX(i);
                float dy = y - getDotY(i);
                if (Math.sqrt(dx * dx + dy * dy) <= hitRadius) {
                    selectedDots.add(i);
                }
            }
        }
    }
}
'''

# ---------------------------------------------------------------------------
# 4. CLONE METADATA STORE
# ---------------------------------------------------------------------------
CLONE_METADATA_STORE_JAVA = r'''
package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.HashSet;
import java.util.Set;

public class CloneMetadataStore {
    private static final String PREFS = "veyravault_clone_meta_v3";

    public static class DeviceIdentity {
        public final String brand;
        public final String model;
        public final String device;
        public final String regionCityCountry;

        public DeviceIdentity(String brand, String model, String device, String regionCityCountry) {
            this.brand = brand;
            this.model = model;
            this.device = device;
            this.regionCityCountry = regionCityCountry;
        }
    }

    public static class VirtualLocation {
        public final double lat;
        public final double lon;
        public final String regionName;
        public final String timeZoneId;
        public final String virtualIp;
        public final String proxyHost;
        public final int proxyPort;

        public VirtualLocation(double lat, double lon, String regionName, String timeZoneId,
                               String virtualIp, String proxyHost, int proxyPort) {
            this.lat = lat;
            this.lon = lon;
            this.regionName = (regionName == null || regionName.trim().isEmpty())
                    ? "Falkenstein, Germany" : regionName.trim();
            this.timeZoneId = (timeZoneId == null || timeZoneId.trim().isEmpty())
                    ? "Europe/Berlin" : timeZoneId.trim();
            this.virtualIp = (virtualIp == null) ? "" : virtualIp.trim();
            this.proxyHost = (proxyHost == null) ? "" : proxyHost.trim();
            this.proxyPort = proxyPort;
        }
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static String keyPrefix(String pkg, int spaceId) {
        return "s" + spaceId + "_" + pkg + "_";
    }

    public static String getSpaceCustomName(Context ctx, int spaceId) {
        return prefs(ctx).getString("space_custom_name_" + spaceId, "");
    }

    public static void setSpaceCustomName(Context ctx, int spaceId, String customName) {
        prefs(ctx).edit().putString("space_custom_name_" + spaceId,
                customName == null ? "" : customName.trim()).apply();
    }

    public static String getSpaceDisplayName(Context ctx, int spaceId, boolean isPersian) {
        String custom = getSpaceCustomName(ctx, spaceId);
        if (custom != null && !custom.trim().isEmpty()) {
            return custom.trim();
        }
        if (isPersian) {
            String[] nums = {"۱", "۲", "۳", "۴", "۵"};
            String n = (spaceId >= 0 && spaceId < nums.length) ? nums[spaceId] : String.valueOf(spaceId + 1);
            return "فضای " + n;
        } else {
            return "Space " + (spaceId + 1);
        }
    }

    public static String getCustomAlias(Context ctx, String pkg, int spaceId) {
        return prefs(ctx).getString(keyPrefix(pkg, spaceId) + "alias", "");
    }

    public static void setCustomAlias(Context ctx, String pkg, int spaceId, String alias) {
        prefs(ctx).edit().putString(keyPrefix(pkg, spaceId) + "alias",
                alias == null ? "" : alias.trim()).apply();
    }

    public static DeviceIdentity getGlobalDeviceIdentity(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        String brand = sp.getString("global_brand", "Samsung");
        String model = sp.getString("global_model", "SM-S928B (Galaxy S24 Ultra)");
        String device = sp.getString("global_device", "e3q");
        String region = sp.getString("global_region_label", "Falkenstein, Germany");
        return new DeviceIdentity(brand, model, device, region);
    }

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model, String device, String regionLabel) {
        prefs(ctx).edit()
            .putString("global_brand", brand == null || brand.trim().isEmpty() ? "Samsung" : brand.trim())
            .putString("global_model", model == null || model.trim().isEmpty() ? "SM-S928B" : model.trim())
            .putString("global_device", device == null || device.trim().isEmpty() ? "generic" : device.trim())
            .putString("global_region_label", regionLabel == null || regionLabel.trim().isEmpty() ? "Falkenstein, Germany" : regionLabel.trim())
            .apply();
    }

    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int spaceId) {
        String b = prefs(ctx).getString(keyPrefix(pkg, spaceId) + "brand", "");
        String m = prefs(ctx).getString(keyPrefix(pkg, spaceId) + "model", "");
        return (b != null && !b.isEmpty()) || (m != null && !m.isEmpty());
    }

    public static DeviceIdentity getCloneDeviceIdentity(Context ctx, String pkg, int spaceId) {
        if (!hasCustomDeviceIdentity(ctx, pkg, spaceId)) return null;
        SharedPreferences sp = prefs(ctx);
        String p = keyPrefix(pkg, spaceId);
        return new DeviceIdentity(
            sp.getString(p + "brand", ""),
            sp.getString(p + "model", ""),
            sp.getString(p + "device", "generic"),
            sp.getString(p + "region", getGlobalDeviceIdentity(ctx).regionCityCountry)
        );
    }

    public static void setCloneDeviceIdentity(Context ctx, String pkg, int spaceId,
                                              String brand, String model, String device, String region) {
        String p = keyPrefix(pkg, spaceId);
        prefs(ctx).edit()
            .putString(p + "brand", brand == null ? "" : brand.trim())
            .putString(p + "model", model == null ? "" : model.trim())
            .putString(p + "device", device == null || device.trim().isEmpty() ? "generic" : device.trim())
            .putString(p + "region", region == null ? "" : region.trim())
            .apply();
    }

    public static void clearCloneDeviceIdentity(Context ctx, String pkg, int spaceId) {
        String p = keyPrefix(pkg, spaceId);
        prefs(ctx).edit()
            .remove(p + "brand")
            .remove(p + "model")
            .remove(p + "device")
            .remove(p + "region")
            .apply();
    }

    public static DeviceIdentity getEffectiveDeviceIdentity(Context ctx, String pkg, int spaceId) {
        DeviceIdentity custom = getCloneDeviceIdentity(ctx, pkg, spaceId);
        if (custom != null) return custom;
        return getGlobalDeviceIdentity(ctx);
    }

    public static VirtualLocation getGlobalLocation(Context ctx) {
        SharedPreferences sp = prefs(ctx);
        double lat = Double.longBitsToDouble(sp.getLong("global_lat", Double.doubleToLongBits(50.4779)));
        double lon = Double.longBitsToDouble(sp.getLong("global_lon", Double.doubleToLongBits(12.3713)));
        String region = sp.getString("global_loc_region", "Falkenstein, Germany");
        String tz = sp.getString("global_loc_tz", "Europe/Berlin");
        String vip = sp.getString("global_loc_vip", "88.198.0.1");
        String pHost = sp.getString("global_proxy_host", "");
        int pPort = sp.getInt("global_proxy_port", 0);
        return new VirtualLocation(lat, lon, region, tz, vip, pHost, pPort);
    }

    public static void setGlobalLocation(Context ctx, double lat, double lon, String regionName,
                                         String tzId, String virtualIp, String proxyHost, int proxyPort) {
        prefs(ctx).edit()
            .putLong("global_lat", Double.doubleToLongBits(lat))
            .putLong("global_lon", Double.doubleToLongBits(lon))
            .putString("global_loc_region", regionName == null || regionName.trim().isEmpty() ? "Falkenstein, Germany" : regionName.trim())
            .putString("global_loc_tz", tzId == null || tzId.trim().isEmpty() ? "Europe/Berlin" : tzId.trim())
            .putString("global_loc_vip", virtualIp == null ? "" : virtualIp.trim())
            .putString("global_proxy_host", proxyHost == null ? "" : proxyHost.trim())
            .putInt("global_proxy_port", proxyPort)
            .putString("global_region_label", regionName == null || regionName.trim().isEmpty() ? "Falkenstein, Germany" : regionName.trim())
            .apply();
    }

    public static VirtualLocation getLocation(Context ctx, String pkg, int spaceId) {
        SharedPreferences sp = prefs(ctx);
        String p = keyPrefix(pkg, spaceId);
        if (!sp.contains(p + "lat")) return null;
        double lat = Double.longBitsToDouble(sp.getLong(p + "lat", 0));
        double lon = Double.longBitsToDouble(sp.getLong(p + "lon", 0));
        String reg = sp.getString(p + "loc_region", "Falkenstein, Germany");
        String tz = sp.getString(p + "loc_tz", "Europe/Berlin");
        String vip = sp.getString(p + "loc_vip", "");
        String pHost = sp.getString(p + "proxy_host", "");
        int pPort = sp.getInt(p + "proxy_port", 0);
        return new VirtualLocation(lat, lon, reg, tz, vip, pHost, pPort);
    }

    public static void saveLocation(Context ctx, String pkg, int spaceId, double lat, double lon,
                                    String regionName, String tzId, String virtualIp, String proxyHost, int proxyPort) {
        String p = keyPrefix(pkg, spaceId);
        prefs(ctx).edit()
            .putLong(p + "lat", Double.doubleToLongBits(lat))
            .putLong(p + "lon", Double.doubleToLongBits(lon))
            .putString(p + "loc_region", regionName == null || regionName.trim().isEmpty() ? "Falkenstein, Germany" : regionName.trim())
            .putString(p + "loc_tz", tzId == null || tzId.trim().isEmpty() ? "Europe/Berlin" : tzId.trim())
            .putString(p + "loc_vip", virtualIp == null ? "" : virtualIp.trim())
            .putString(p + "proxy_host", proxyHost == null ? "" : proxyHost.trim())
            .putInt(p + "proxy_port", proxyPort)
            .apply();
    }

    public static void clearLocation(Context ctx, String pkg, int spaceId) {
        String p = keyPrefix(pkg, spaceId);
        prefs(ctx).edit()
            .remove(p + "lat")
            .remove(p + "lon")
            .remove(p + "loc_region")
            .remove(p + "loc_tz")
            .remove(p + "loc_vip")
            .remove(p + "proxy_host")
            .remove(p + "proxy_port")
            .apply();
    }

    public static VirtualLocation getEffectiveLocation(Context ctx, String pkg, int spaceId) {
        VirtualLocation custom = getLocation(ctx, pkg, spaceId);
        if (custom != null) return custom;
        return getGlobalLocation(ctx);
    }

    public static Set<String> getClonedPackagesForSpace(Context ctx, int spaceId) {
        return new HashSet<>(prefs(ctx).getStringSet("independent_clones_space_" + spaceId, new HashSet<String>()));
    }

    public static void registerClonedPackage(Context ctx, String pkg, int spaceId) {
        Set<String> set = getClonedPackagesForSpace(ctx, spaceId);
        set.add(pkg);
        prefs(ctx).edit().putStringSet("independent_clones_space_" + spaceId, set).apply();
    }

    public static void unregisterClonedPackage(Context ctx, String pkg, int spaceId) {
        Set<String> set = getClonedPackagesForSpace(ctx, spaceId);
        set.remove(pkg);
        prefs(ctx).edit().putStringSet("independent_clones_space_" + spaceId, set).apply();
    }

    public static String[][] getPresetDeviceList() {
        return new String[][]{
            {"Apple", "iPhone 16 Pro Max", "iPhone17,2", "Cupertino, United States"},
            {"Apple", "iPhone 15 Pro Max", "iPhone16,2", "New York, United States"},
            {"Apple", "iPhone 14 Pro", "iPhone15,2", "London, United Kingdom"},
            {"Apple", "iPad Pro M4 (13-inch)", "iPad16,6", "Cupertino, United States"},
            {"Samsung", "SM-S928B (Galaxy S24 Ultra)", "e3q", "Falkenstein, Germany"},
            {"Samsung", "SM-S918B (Galaxy S23 Ultra)", "dm3q", "Frankfurt, Germany"},
            {"Samsung", "SM-A556E (Galaxy A55 5G)", "a55x", "Amsterdam, Netherlands"},
            {"Google", "Pixel 9 Pro XL", "komodo", "New York, United States"},
            {"Google", "Pixel 8 Pro", "husky", "Toronto, Canada"},
            {"Xiaomi", "Xiaomi 14 Ultra", "aurora", "Singapore, Singapore"},
            {"Xiaomi", "Poco F6 Pro", "vermeer", "Istanbul, Turkey"},
            {"OnePlus", "OnePlus 12", "waffle", "Helsinki, Finland"}
        };
    }

    public static String[][] getPresetRegionsList() {
        return new String[][]{
            {"Falkenstein, Germany", "50.4779", "12.3713", "Europe/Berlin", "88.198.45.12"},
            {"Frankfurt, Germany", "50.1109", "8.6821", "Europe/Berlin", "138.201.92.10"},
            {"Amsterdam, Netherlands", "52.3676", "4.9041", "Europe/Amsterdam", "95.211.18.44"},
            {"New York, United States", "40.7128", "-74.0060", "America/New_York", "104.244.72.115"},
            {"London, United Kingdom", "51.5074", "-0.1278", "Europe/London", "51.140.10.22"},
            {"Istanbul, Turkey", "41.0082", "28.9784", "Europe/Istanbul", "185.125.33.19"},
            {"Dubai, United Arab Emirates", "25.2048", "55.2708", "Asia/Dubai", "94.200.12.80"},
            {"Tehran, Iran", "35.6892", "51.3890", "Asia/Tehran", "5.160.40.11"},
            {"Singapore, Singapore", "1.3521", "103.8198", "Asia/Singapore", "128.199.88.5"}
        };
    }
}
'''

# ---------------------------------------------------------------------------
# 5. VIRTUAL HOOK MANAGER
# ---------------------------------------------------------------------------
VIRTUAL_HOOK_MANAGER_JAVA = r'''
package com.veyravault.space.core;

import android.content.Context;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.SystemClock;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.Locale;
import java.util.TimeZone;

public class VirtualHookManager {

    private static CloneMetadataStore.VirtualLocation activeLocation;
    private static CloneMetadataStore.DeviceIdentity activeIdentity;
    private static boolean hooksInstalled = false;

    public static synchronized void prepareForCloneLaunch(Context ctx, String pkg, int spaceId) {
        activeIdentity = CloneMetadataStore.getEffectiveDeviceIdentity(ctx, pkg, spaceId);
        activeLocation = CloneMetadataStore.getEffectiveLocation(ctx, pkg, spaceId);

        applyDeviceBuildFields(activeIdentity, pkg, spaceId);
        applyRegionNetworkAndProxy(activeLocation);
        installLocationServiceHook(ctx);
        installGmsAvailabilityBypass();
    }

    private static void applyDeviceBuildFields(CloneMetadataStore.DeviceIdentity id, String pkg, int spaceId) {
        if (id == null) return;
        try {
            setStaticField(Build.class, "BRAND", id.brand);
            setStaticField(Build.class, "MANUFACTURER", id.brand);
            setStaticField(Build.class, "MODEL", id.model);
            setStaticField(Build.class, "PRODUCT", id.device);
            setStaticField(Build.class, "DEVICE", id.device);

            String fp = String.format(Locale.US, "%s/%s/%s:14/UP1A.231005.007/V%d%d:user/release-keys",
                    id.brand, id.device, id.device, spaceId + 1, Math.abs(pkg.hashCode() % 9000) + 1000);
            setStaticField(Build.class, "FINGERPRINT", fp);
        } catch (Throwable ignored) {}
    }

    private static void applyRegionNetworkAndProxy(CloneMetadataStore.VirtualLocation loc) {
        if (loc == null) return;
        try {
            TimeZone tz = TimeZone.getTimeZone(loc.timeZoneId);
            TimeZone.setDefault(tz);
            System.setProperty("user.timezone", loc.timeZoneId);

            if (loc.regionName.toLowerCase(Locale.US).contains("germany")) {
                System.setProperty("user.Region", "DE");
                System.setProperty("veyra.virtual.country", "DE");
            } else if (loc.regionName.toLowerCase(Locale.US).contains("united states")) {
                System.setProperty("user.Region", "US");
                System.setProperty("veyra.virtual.country", "US");
            } else if (loc.regionName.toLowerCase(Locale.US).contains("netherlands")) {
                System.setProperty("user.Region", "NL");
                System.setProperty("veyra.virtual.country", "NL");
            }
            System.setProperty("veyra.virtual.region_label", loc.regionName);

            if (!loc.virtualIp.isEmpty()) {
                System.setProperty("veyra.virtual.ip", loc.virtualIp);
            }

            if (!loc.proxyHost.isEmpty() && loc.proxyPort > 0) {
                System.setProperty("socksProxyHost", loc.proxyHost);
                System.setProperty("socksProxyPort", String.valueOf(loc.proxyPort));
                System.setProperty("http.proxyHost", loc.proxyHost);
                System.setProperty("http.proxyPort", String.valueOf(loc.proxyPort));
                System.setProperty("https.proxyHost", loc.proxyHost);
                System.setProperty("https.proxyPort", String.valueOf(loc.proxyPort));
            }
        } catch (Throwable ignored) {}
    }

    public static Location buildSpoofedLocation(String provider) {
        CloneMetadataStore.VirtualLocation v = activeLocation;
        if (v == null) return null;
        Location loc = new Location(provider == null ? LocationManager.GPS_PROVIDER : provider);
        loc.setLatitude(v.lat);
        loc.setLongitude(v.lon);
        loc.setAccuracy(3.5f);
        loc.setAltitude(120.0);
        loc.setTime(System.currentTimeMillis());
        if (Build.VERSION.SDK_INT >= 17) {
            loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
        }
        return loc;
    }

    private static void installLocationServiceHook(Context ctx) {
        if (hooksInstalled) return;
        try {
            LocationManager lm = (LocationManager) ctx.getSystemService(Context.LOCATION_SERVICE);
            if (lm == null) return;
            Field serviceField = LocationManager.class.getDeclaredField("mService");
            serviceField.setAccessible(true);
            final Object realService = serviceField.get(lm);
            if (realService == null) return;

            Class<?> iLocInterface = Class.forName("android.location.ILocationManager");
            Object proxy = Proxy.newProxyInstance(
                iLocInterface.getClassLoader(),
                new Class<?>[]{iLocInterface},
                new InvocationHandler() {
                    @Override
                    public Object invoke(Object proxyObj, Method method, Object[] args) throws Throwable {
                        String name = method.getName();
                        if ("getLastLocation".equals(name) || "getLastKnownLocation".equals(name)) {
                            Location fake = buildSpoofedLocation(LocationManager.GPS_PROVIDER);
                            if (fake != null) return fake;
                        }
                        return method.invoke(realService, args);
                    }
                }
            );
            serviceField.set(lm, proxy);
            hooksInstalled = true;
        } catch (Throwable ignored) {}
    }

    private static void installGmsAvailabilityBypass() {
        try {
            System.setProperty("veyra.gms.PretendAvailable", "true");
            Class<?> gmsUtil = Class.forName("com.google.android.gms.common.GooglePlayServicesUtil");
            Field f = gmsUtil.getDeclaredField("GOOGLE_PLAY_SERVICES_VERSION_CODE");
            f.setAccessible(true);
        } catch (Throwable ignored) {}
    }

    private static void setStaticField(Class<?> cls, String fieldName, Object value) {
        try {
            Field f = cls.getDeclaredField(fieldName);
            f.setAccessible(true);
            f.set(null, value);
        } catch (Throwable ignored) {}
    }
}
'''

# ---------------------------------------------------------------------------
# 6. ENGINE
# ---------------------------------------------------------------------------
ENGINE_JAVA = r'''
package com.veyravault.space.core;

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
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.configuration.ClientConfiguration;
import top.niunaijun.blackbox.entity.pm.InstallResult;

public class Engine {

    public static class ClonedApp {
        public final String packageName;
        public final String label;
        public final Drawable icon;
        public final int spaceId;
        public final boolean independentVaultReady;

        public ClonedApp(String packageName, String label, Drawable icon, int spaceId, boolean independentVaultReady) {
            this.packageName = packageName;
            this.label = label;
            this.icon = icon;
            this.spaceId = spaceId;
            this.independentVaultReady = independentVaultReady;
        }
    }

    public static class AvailableApp {
        public final String packageName;
        public final String label;
        public final Drawable icon;
        public final boolean alreadyClonedInSpace;

        public AvailableApp(String packageName, String label, Drawable icon, boolean alreadyClonedInSpace) {
            this.packageName = packageName;
            this.label = label;
            this.icon = icon;
            this.alreadyClonedInSpace = alreadyClonedInSpace;
        }
    }

    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(120);
    private static final LruCache<String, String> LABEL_CACHE = new LruCache<>(120);

    public static void doAttachBaseContext(Context base) {
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

    public static void doOnCreate(Context ctx) {
        try {
            BlackBoxCore.get().doCreate();
            for (int space = 0; space < 4; space++) {
                GmsSupportManager.installGms(space);
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public static File getVaultDirForPackage(Context ctx, String pkg) {
        File dir = new File(ctx.getFilesDir(), "apk_vault/" + pkg);
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    public static File getVaultBaseApk(Context ctx, String pkg) {
        return new File(getVaultDirForPackage(ctx, pkg), "base.apk");
    }

    public static void backupPackageToVault(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
            File vaultDir = getVaultDirForPackage(ctx, pkg);

            if (ai.sourceDir != null) {
                File srcBase = new File(ai.sourceDir);
                File dstBase = new File(vaultDir, "base.apk");
                if (srcBase.exists() && (!dstBase.exists() || dstBase.length() != srcBase.length())) {
                    copyFile(srcBase, dstBase);
                }
                extractNativeLibsFromApk(srcBase, new File(vaultDir, "lib"));
            }

            if (Build.VERSION.SDK_INT >= 21 && ai.splitSourceDirs != null) {
                int idx = 0;
                for (String splitPath : ai.splitSourceDirs) {
                    if (splitPath == null) continue;
                    File splitFile = new File(splitPath);
                    if (splitFile.exists()) {
                        File dstSplit = new File(vaultDir, "split_" + idx + ".apk");
                        if (!dstSplit.exists() || dstSplit.length() != splitFile.length()) {
                            copyFile(splitFile, dstSplit);
                        }
                        extractNativeLibsFromApk(splitFile, new File(vaultDir, "lib"));
                        idx++;
                    }
                }
            }

            syncExtractedLibsIntoBlackBoxData(ctx, pkg, new File(vaultDir, "lib"));
        } catch (Throwable ignored) {}
    }

    private static void extractNativeLibsFromApk(File apkFile, File outLibDir) {
        if (apkFile == null || !apkFile.exists()) return;
        if (!outLibDir.exists()) outLibDir.mkdirs();
        String primaryAbi = Build.SUPPORTED_ABIS != null && Build.SUPPORTED_ABIS.length > 0
                ? Build.SUPPORTED_ABIS[0] : "arm64-v8a";
        ZipFile zf = null;
        try {
            zf = new ZipFile(apkFile);
            Enumeration<? extends ZipEntry> entries = zf.entries();
            while (entries.hasMoreElements()) {
                ZipEntry ze = entries.nextElement();
                String name = ze.getName();
                if (name.startsWith("lib/") && name.endsWith(".so") && !ze.isDirectory()) {
                    if (name.contains(primaryAbi) || name.contains("armeabi-v7a") || name.contains("arm64-v8a")) {
                        String soName = name.substring(name.lastIndexOf('/') + 1);
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
                            outSo.setReadable(true, false);
                            outSo.setExecutable(true, false);
                        }
                    }
                }
            }
        } catch (Throwable ignored) {
        } finally {
            try { if (zf != null) zf.close(); } catch (Throwable ignored) {}
        }
    }

    private static void syncExtractedLibsIntoBlackBoxData(Context ctx, String pkg, File vaultLibDir) {
        if (vaultLibDir == null || !vaultLibDir.exists()) return;
        File[] soFiles = vaultLibDir.listFiles();
        if (soFiles == null || soFiles.length == 0) return;

        File dataRoot = ctx.getDataDir();
        File[] candidates = new File[]{
            new File(dataRoot, "virtual/data/app/" + pkg + "/lib"),
            new File(dataRoot, "virtual/data/user/0/" + pkg + "/lib"),
            new File(ctx.getFilesDir().getParentFile(), "virtual/data/app/" + pkg + "/lib")
        };
        for (File targetDir : candidates) {
            try {
                if (!targetDir.exists()) targetDir.mkdirs();
                for (File so : soFiles) {
                    File dst = new File(targetDir, so.getName());
                    if (!dst.exists() || dst.length() != so.length()) {
                        copyFile(so, dst);
                        dst.setReadable(true, false);
                        dst.setExecutable(true, false);
                    }
                }
            } catch (Throwable ignored) {}
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

    @SuppressWarnings("unchecked")
    private static List<ApplicationInfo> queryBlackBoxInstalledApplications(int spaceId) {
        try {
            BlackBoxCore core = BlackBoxCore.get();
            for (Method m : core.getClass().getMethods()) {
                if ("getInstalledApplications".equals(m.getName())) {
                    Class<?>[] params = m.getParameterTypes();
                    if (params.length == 2) {
                        Object res = m.invoke(core, 0, spaceId);
                        if (res instanceof List) return (List<ApplicationInfo>) res;
                    } else if (params.length == 1) {
                        Object res = m.invoke(core, spaceId);
                        if (res instanceof List) return (List<ApplicationInfo>) res;
                    }
                }
            }
        } catch (Throwable ignored) {}
        return new ArrayList<>();
    }

    public static List<ClonedApp> getClonedApps(Context ctx, int spaceId) {
        List<ClonedApp> result = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Set<String> seen = new HashSet<>();

        try {
            List<ApplicationInfo> installed = queryBlackBoxInstalledApplications(spaceId);
            if (installed != null) {
                for (ApplicationInfo info : installed) {
                    if (info == null || info.packageName == null) continue;
                    if (info.packageName.equals(ctx.getPackageName())) continue;
                    if (info.packageName.startsWith("com.google.android.gms")
                            || info.packageName.startsWith("com.google.android.gsf")
                            || info.packageName.startsWith("com.android.vending")) {
                        continue;
                    }
                    seen.add(info.packageName);
                    CloneMetadataStore.registerClonedPackage(ctx, info.packageName, spaceId);
                    result.add(buildClonedAppModel(ctx, pm, info.packageName, spaceId));
                }
            }
        } catch (Throwable ignored) {}

        Set<String> registered = CloneMetadataStore.getClonedPackagesForSpace(ctx, spaceId);
        for (String pkg : registered) {
            if (!seen.contains(pkg)) {
                File vaultApk = getVaultBaseApk(ctx, pkg);
                if (vaultApk.exists() && !BlackBoxCore.get().isInstalled(pkg, spaceId)) {
                    try {
                        BlackBoxCore.get().installPackageAsUser(vaultApk, spaceId);
                    } catch (Throwable ignored) {}
                }
                if (BlackBoxCore.get().isInstalled(pkg, spaceId) || vaultApk.exists()) {
                    seen.add(pkg);
                    result.add(buildClonedAppModel(ctx, pm, pkg, spaceId));
                }
            }
        }

        return result;
    }

    private static ClonedApp buildClonedAppModel(Context ctx, PackageManager pm, String pkg, int spaceId) {
        String alias = CloneMetadataStore.getCustomAlias(ctx, pkg, spaceId);
        Drawable icon = ICON_CACHE.get(pkg);
        String baseLabel = LABEL_CACHE.get(pkg);
        File vaultApk = getVaultBaseApk(ctx, pkg);

        if (icon == null || baseLabel == null) {
            try {
                ApplicationInfo hostAi = pm.getApplicationInfo(pkg, 0);
                icon = hostAi.loadIcon(pm);
                baseLabel = hostAi.loadLabel(pm).toString();
            } catch (Throwable notOnHost) {
                if (vaultApk.exists()) {
                    try {
                        PackageInfo pi = pm.getPackageArchiveInfo(vaultApk.getAbsolutePath(), 0);
                        if (pi != null && pi.applicationInfo != null) {
                            pi.applicationInfo.sourceDir = vaultApk.getAbsolutePath();
                            pi.applicationInfo.publicSourceDir = vaultApk.getAbsolutePath();
                            icon = pi.applicationInfo.loadIcon(pm);
                            CharSequence cs = pi.applicationInfo.loadLabel(pm);
                            if (cs != null) baseLabel = cs.toString();
                        }
                    } catch (Throwable ignored) {}
                }
            }
            if (icon == null) icon = ctx.getApplicationInfo().loadIcon(pm);
            if (baseLabel == null || baseLabel.isEmpty()) baseLabel = pkg;
            ICON_CACHE.put(pkg, icon);
            LABEL_CACHE.put(pkg, baseLabel);
        }

        String finalLabel = (alias != null && !alias.trim().isEmpty()) ? alias.trim() : baseLabel;
        return new ClonedApp(pkg, finalLabel, icon, spaceId, vaultApk.exists());
    }

    public static List<AvailableApp> getInstalledApps(Context ctx, int spaceId) {
        List<AvailableApp> list = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Set<String> clonedInSpace = CloneMetadataStore.getClonedPackagesForSpace(ctx, spaceId);

        Intent mainIntent = new Intent(Intent.ACTION_MAIN, null);
        mainIntent.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> resolves = pm.queryIntentActivities(mainIntent, 0);
        Set<String> added = new HashSet<>();

        if (resolves != null) {
            for (ResolveInfo ri : resolves) {
                if (ri.activityInfo == null) continue;
                String pkg = ri.activityInfo.packageName;
                if (pkg == null || pkg.equals(ctx.getPackageName()) || added.contains(pkg)) continue;
                added.add(pkg);

                Drawable icon = ICON_CACHE.get(pkg);
                String label = LABEL_CACHE.get(pkg);
                if (icon == null || label == null) {
                    icon = ri.loadIcon(pm);
                    CharSequence cs = ri.loadLabel(pm);
                    label = cs != null ? cs.toString() : pkg;
                    if (icon != null) ICON_CACHE.put(pkg, icon);
                    LABEL_CACHE.put(pkg, label);
                }

                boolean already = clonedInSpace.contains(pkg) || BlackBoxCore.get().isInstalled(pkg, spaceId);
                list.add(new AvailableApp(pkg, label, icon, already));
            }
        }
        return list;
    }

    public static boolean cloneApp(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.installGms(spaceId);
            backupPackageToVault(ctx, pkg);

            InstallResult res = BlackBoxCore.get().installPackageAsUser(pkg, spaceId);
            if (res == null || !res.success) {
                File vaultApk = getVaultBaseApk(ctx, pkg);
                if (vaultApk.exists()) {
                    res = BlackBoxCore.get().installPackageAsUser(vaultApk, spaceId);
                }
            }
            File vaultDir = getVaultDirForPackage(ctx, pkg);
            syncExtractedLibsIntoBlackBoxData(ctx, pkg, new File(vaultDir, "lib"));

            boolean ok = (res != null && res.success) || BlackBoxCore.get().isInstalled(pkg, spaceId);
            if (ok) {
                CloneMetadataStore.registerClonedPackage(ctx, pkg, spaceId);
            }
            return ok;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public static boolean installExternalApkFile(Context ctx, String apkFilePath, int spaceId, boolean keepInVault) {
        try {
            if (apkFilePath == null || apkFilePath.trim().isEmpty()) return false;
            File srcApk = new File(apkFilePath.trim());
            if (!srcApk.exists()) return false;

            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(srcApk.getAbsolutePath(), 0);
            String pkg = (pi != null && pi.packageName != null) ? pi.packageName : null;

            GmsSupportManager.installGms(spaceId);

            if (pkg != null && keepInVault) {
                File vaultDir = getVaultDirForPackage(ctx, pkg);
                File dstBase = new File(vaultDir, "base.apk");
                copyFile(srcApk, dstBase);
                extractNativeLibsFromApk(srcApk, new File(vaultDir, "lib"));
                InstallResult r = BlackBoxCore.get().installPackageAsUser(dstBase, spaceId);
                syncExtractedLibsIntoBlackBoxData(ctx, pkg, new File(vaultDir, "lib"));
                if (r != null && r.success) {
                    CloneMetadataStore.registerClonedPackage(ctx, pkg, spaceId);
                    return true;
                }
            } else {
                InstallResult r = BlackBoxCore.get().installPackageAsUser(srcApk, spaceId);
                if (r != null && r.success) {
                    if (pkg != null) CloneMetadataStore.registerClonedPackage(ctx, pkg, spaceId);
                    return true;
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return false;
    }

    public static boolean launchClonedApp(Context ctx, String pkg, int spaceId) {
        try {
            GmsSupportManager.installGms(spaceId);
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, spaceId);

            File vaultDir = getVaultDirForPackage(ctx, pkg);
            File vaultApk = new File(vaultDir, "base.apk");
            if (!BlackBoxCore.get().isInstalled(pkg, spaceId) && vaultApk.exists()) {
                BlackBoxCore.get().installPackageAsUser(vaultApk, spaceId);
            }
            syncExtractedLibsIntoBlackBoxData(ctx, pkg, new File(vaultDir, "lib"));

            if (pkg.contains("chrome") || pkg.equals("com.android.chrome")) {
                Intent chromeMain = resolveRealMainLauncherIntent(ctx, pkg);
                if (chromeMain != null && invokeBlackBoxStartActivity(chromeMain, spaceId)) {
                    return true;
                }
            }

            boolean launched = BlackBoxCore.get().launchApk(pkg, spaceId);
            if (!launched) {
                Intent fallback = resolveRealMainLauncherIntent(ctx, pkg);
                if (fallback != null) {
                    return invokeBlackBoxStartActivity(fallback, spaceId);
                }
            }
            return launched;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    private static boolean invokeBlackBoxStartActivity(Intent intent, int spaceId) {
        try {
            BlackBoxCore core = BlackBoxCore.get();
            for (Method m : core.getClass().getMethods()) {
                if ("startActivity".equals(m.getName())) {
                    Class<?>[] p = m.getParameterTypes();
                    if (p.length == 2 && p[0] == Intent.class && p[1] == int.class) {
                        m.invoke(core, intent, spaceId);
                        return true;
                    }
                }
            }
        } catch (Throwable ignored) {}
        return false;
    }

    private static Intent resolveRealMainLauncherIntent(Context ctx, String pkg) {
        try {
            PackageManager pm = ctx.getPackageManager();
            if ("com.android.chrome".equals(pkg) || pkg.contains("chrome")) {
                Intent explicitChrome = new Intent(Intent.ACTION_MAIN);
                explicitChrome.addCategory(Intent.CATEGORY_LAUNCHER);
                explicitChrome.setPackage(pkg);
                explicitChrome.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
                explicitChrome.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                return explicitChrome;
            }

            Intent query = new Intent(Intent.ACTION_MAIN);
            query.addCategory(Intent.CATEGORY_LAUNCHER);
            query.setPackage(pkg);
            List<ResolveInfo> list = pm.queryIntentActivities(query, 0);
            if (list != null) {
                for (ResolveInfo ri : list) {
                    ActivityInfo ai = ri.activityInfo;
                    if (ai == null || ai.name == null) continue;
                    String lower = ai.name.toLowerCase();
                    if (lower.contains("devui") || lower.contains("devtools") || lower.contains("webview")) {
                        continue;
                    }
                    Intent i = new Intent(Intent.ACTION_MAIN);
                    i.addCategory(Intent.CATEGORY_LAUNCHER);
                    i.setComponent(new ComponentName(pkg, ai.name));
                    i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    return i;
                }
            }
        } catch (Throwable ignored) {}
        return null;
    }

    public static void uninstallClone(Context ctx, String pkg, int spaceId) {
        try {
            BlackBoxCore.get().uninstallPackageAsUser(pkg, spaceId);
        } catch (Throwable ignored) {}
        CloneMetadataStore.unregisterClonedPackage(ctx, pkg, spaceId);
        CloneMetadataStore.clearCloneDeviceIdentity(ctx, pkg, spaceId);
        CloneMetadataStore.clearLocation(ctx, pkg, spaceId);
        CloneMetadataStore.setCustomAlias(ctx, pkg, spaceId, "");
    }

    public static void clearAppCache(Context ctx, String pkg, int spaceId) {
        try {
            BlackBoxCore core = BlackBoxCore.get();
            for (Method m : core.getClass().getMethods()) {
                if ("clearPackage".equals(m.getName()) && m.getParameterTypes().length == 2) {
                    m.invoke(core, pkg, spaceId);
                    break;
                }
            }
        } catch (Throwable ignored) {}
    }
}
'''

# ---------------------------------------------------------------------------
# 7. SECURITY MANAGER & DEVICE ADMIN RECEIVER
# ---------------------------------------------------------------------------
SECURITY_MANAGER_JAVA = r'''
package com.veyravault.space.security;

import android.content.Context;
import android.content.SharedPreferences;
import java.security.MessageDigest;

public class SecurityManager {
    private static final String PREFS = "veyravault_security_v3";

    public static final int LOCK_TYPE_PIN = 0;
    public static final int LOCK_TYPE_PATTERN = 1;

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

    public static boolean hasPinConfigured(Context ctx) {
        String h = prefs(ctx).getString("pin_hash_v3", "");
        return h != null && !h.isEmpty();
    }

    public static boolean hasPatternConfigured(Context ctx) {
        String h = prefs(ctx).getString("pattern_hash_v3", "");
        return h != null && !h.isEmpty();
    }

    public static boolean isSecurityEnabled(Context ctx) {
        return hasPinConfigured(ctx) || hasPatternConfigured(ctx);
    }

    public static int getPrimaryLockType(Context ctx) {
        return prefs(ctx).getInt("primary_lock_type", LOCK_TYPE_PIN);
    }

    public static void setPrimaryLockType(Context ctx, int type) {
        prefs(ctx).edit().putInt("primary_lock_type", type).apply();
    }

    public static int getActivePrimaryLockType(Context ctx) {
        int preferred = getPrimaryLockType(ctx);
        if (preferred == LOCK_TYPE_PIN && hasPinConfigured(ctx)) return LOCK_TYPE_PIN;
        if (preferred == LOCK_TYPE_PATTERN && hasPatternConfigured(ctx)) return LOCK_TYPE_PATTERN;
        if (hasPinConfigured(ctx)) return LOCK_TYPE_PIN;
        return LOCK_TYPE_PATTERN;
    }

    public static boolean hasSecondaryFallbackLock(Context ctx) {
        return hasPinConfigured(ctx) && hasPatternConfigured(ctx);
    }

    public static void savePin(Context ctx, String rawPin) {
        prefs(ctx).edit()
            .putString("pin_hash_v3", sha256(rawPin))
            .apply();
        if (!hasPatternConfigured(ctx)) {
            setPrimaryLockType(ctx, LOCK_TYPE_PIN);
        }
    }

    public static void clearPin(Context ctx) {
        prefs(ctx).edit().remove("pin_hash_v3").apply();
        if (hasPatternConfigured(ctx)) {
            setPrimaryLockType(ctx, LOCK_TYPE_PATTERN);
        }
    }

    public static void savePattern(Context ctx, String patternStr) {
        prefs(ctx).edit()
            .putString("pattern_hash_v3", sha256(patternStr))
            .apply();
        if (!hasPinConfigured(ctx)) {
            setPrimaryLockType(ctx, LOCK_TYPE_PATTERN);
        }
    }

    public static void clearPattern(Context ctx) {
        prefs(ctx).edit().remove("pattern_hash_v3").apply();
        if (hasPinConfigured(ctx)) {
            setPrimaryLockType(ctx, LOCK_TYPE_PIN);
        }
    }

    public static void disableAllLocks(Context ctx) {
        prefs(ctx).edit()
            .remove("pin_hash_v3")
            .remove("pattern_hash_v3")
            .apply();
        sessionUnlocked = true;
    }

    public static boolean verifyPin(Context ctx, String rawInput) {
        if (rawInput == null || !hasPinConfigured(ctx)) return false;
        String stored = prefs(ctx).getString("pin_hash_v3", "");
        return stored.equals(sha256(rawInput));
    }

    public static boolean verifyPattern(Context ctx, String patternInput) {
        if (patternInput == null || !hasPatternConfigured(ctx)) return false;
        String stored = prefs(ctx).getString("pattern_hash_v3", "");
        return stored.equals(sha256(patternInput));
    }

    private static String sha256(String s) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest(("veyra_salt_v3_" + s).getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            return String.valueOf(s.hashCode());
        }
    }
}
'''

VAULT_DEVICE_ADMIN_RECEIVER_JAVA = r'''
package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;
import com.veyravault.space.helper.LocaleHelper;
import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    private static volatile boolean internalAdminChangeAllowed = false;

    public static void setInternalAdminChangeAllowed(boolean allowed) {
        internalAdminChangeAllowed = allowed;
    }

    @Override
    public void onEnabled(Context context, Intent intent) {
        boolean fa = LocaleHelper.isPersian(context);
        Toast.makeText(context,
            fa ? "🛡️ قفل ضدحذف VeyraVault فعال شد (حذف برنامه مسدود است)"
               : "🛡️ VeyraVault Anti-Uninstall Protection Enabled",
            Toast.LENGTH_LONG).show();
    }

    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        boolean fa = LocaleHelper.isPersian(context);
        if (!internalAdminChangeAllowed) {
            SecurityManager.setSessionUnlocked(false);
            try {
                Intent lockIntent = new Intent(context, SecurityLockActivity.class);
                lockIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                        | Intent.FLAG_ACTIVITY_CLEAR_TOP
                        | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                lockIntent.putExtra("anti_tamper_intercept", true);
                context.startActivity(lockIntent);
            } catch (Throwable ignored) {}

            Toast.makeText(context,
                fa ? "⛔ حذف مقدور نمی‌باشد! غیرفعال‌سازی فقط از داخل تنظیمات امنیتی برنامه مجاز است."
                   : "⛔ Uninstallation is not permitted! Disable only inside VeyraVault Security Settings.",
                Toast.LENGTH_LONG).show();
        }
        return fa
            ? "⛔ حذف مقدور نمی‌باشد!\nاین برنامه توسط قفل امنیتی VeyraVault محافظت می‌شود و خارج از محیط برنامه قابل غیرفعال‌سازی یا حذف نیست."
            : "⛔ Uninstallation is NOT permitted!\nProtected by VeyraVault Security Lock.";
    }

    @Override
    public void onDisabled(Context context, Intent intent) {
        internalAdminChangeAllowed = false;
    }
}
'''

def main():
    clean_legacy_sources()
    patch_app_build_gradle()

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(ANDROID_MANIFEST_XML.strip() + "\n")
    print(f"[v3-Part1] Wrote: {MANIFEST_PATH}")

    write_file("xml", "device_admin_policies.xml", DEVICE_ADMIN_XML, base=RES_BASE)
    write_file("values", "strings.xml", STRINGS_XML, base=RES_BASE)
    write_file("values", "styles.xml", STYLES_XML, base=RES_BASE)
    write_file("drawable", "ic_launcher.xml", IC_LAUNCHER_XML, base=RES_BASE)
    write_file("drawable", "ic_nav_dashboard.xml", IC_DASHBOARD_XML, base=RES_BASE)
    write_file("drawable", "ic_nav_spaces.xml", IC_SPACES_XML, base=RES_BASE)
    write_file("drawable", "ic_nav_add.xml", IC_ADD_XML, base=RES_BASE)
    write_file("drawable", "ic_nav_guide.xml", IC_GUIDE_XML, base=RES_BASE)
    write_file("drawable", "ic_nav_settings.xml", IC_SETTINGS_XML, base=RES_BASE)

    write_file("", "VeyraApplication.java", VEYRA_APPLICATION_JAVA)
    write_file("helper", "JalaliClockUtil.java", JALALI_CLOCK_UTIL_JAVA)
    write_file("helper", "LocaleHelper.java", LOCALE_HELPER_JAVA)
    write_file("helper", "BaseActivity.java", BASE_ACTIVITY_JAVA)
    write_file("helper", "AppDisguiseManager.java", APP_DISGUISE_MANAGER_JAVA)
    write_file("ui", "PatternLockView.java", PATTERN_LOCK_VIEW_JAVA)
    write_file("core", "GmsSupportManager.java", GMS_SUPPORT_MANAGER_JAVA)
    write_file("core", "CloneMetadataStore.java", CLONE_METADATA_STORE_JAVA)
    write_file("core", "VirtualHookManager.java", VIRTUAL_HOOK_MANAGER_JAVA)
    write_file("core", "Engine.java", ENGINE_JAVA)
    write_file("security", "SecurityManager.java", SECURITY_MANAGER_JAVA)
    write_file("security", "VaultDeviceAdminReceiver.java", VAULT_DEVICE_ADMIN_RECEIVER_JAVA)
    print("[v3-Part1] Core, Manifest, Resources & Security upgrade completed successfully.")

if __name__ == "__main__":
    main()
