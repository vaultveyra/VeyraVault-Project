#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Upgrade Script - Part 1 (Complete Infrastructure, Core, Helpers & Security)
"""

import os
import re
import shutil

APP_BASE = "app/src/main"
JAVA_BASE = os.path.join(APP_BASE, "java/com/veyravault/space")
RES_BASE = os.path.join(APP_BASE, "res")


def write_file(path, content):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "w", encoding="utf-8") as f:
    f.write(content.strip() + "\n")
  print(f"[v3.0-Part1] Wrote: {path}")


def clean_legacy_sources():
  if os.path.exists(JAVA_BASE):
    shutil.rmtree(JAVA_BASE)
  os.makedirs(JAVA_BASE, exist_ok=True)
  layout_dir = os.path.join(RES_BASE, "layout")
  if os.path.exists(layout_dir):
    shutil.rmtree(layout_dir)
  os.makedirs(layout_dir, exist_ok=True)


def patch_part2_script():
  p2_path = "scripts/upgrade_v3_part2.py"
  if not os.path.exists(p2_path):
    return
  with open(p2_path, "r", encoding="utf-8") as f:
    code = f.read()

  marker = "# [AUTO-FIX SECURITY LOCK]"
  if marker in code:
    code = code[: code.index(marker)].rstrip() + "\n"

  extra_imports = (
      "package com.veyravault.space.ui;\n"
      "import com.veyravault.space.helper.BaseActivity;\n"
      "import com.veyravault.space.helper.PatternLockView;\n"
      "import com.veyravault.space.helper.JalaliClockUtil;\n"
      "import com.veyravault.space.helper.LocaleHelper;\n"
      "import com.veyravault.space.helper.AppDisguiseManager;"
  )
  code = code.replace(
      "package com.veyravault.space.ui;\nimport"
      " com.veyravault.space.helper.BaseActivity;",
      "package com.veyravault.space.ui;",
  )
  code = code.replace(
      "package com.veyravault.space.ui;\n"
      "import com.veyravault.space.helper.BaseActivity;\n"
      "import com.veyravault.space.helper.PatternLockView;\n"
      "import com.veyravault.space.helper.JalaliClockUtil;\n"
      "import com.veyravault.space.helper.LocaleHelper;\n"
      "import com.veyravault.space.helper.AppDisguiseManager;",
      "package com.veyravault.space.ui;",
  )
  code = code.replace("package com.veyravault.space.ui;", extra_imports)

  for act in [
      "MainActivity",
      "AddAppActivity",
      "GlobalEnvironmentActivity",
      "SetLocationActivity",
      "SecuritySettingsActivity",
      "SecurityLockActivity",
      "GuideActivity",
      "AboutActivity",
  ]:
    code = code.replace(
        f"public class {act} extends Activity",
        f"public class {act} extends BaseActivity",
    )

  code = code.replace("Gravity.CENTER_horizontal", "Gravity.CENTER_HORIZONTAL")
  code = code.replace("Gravity.CENTER_vertical", "Gravity.CENTER_VERTICAL")
  code = code.replace(
      "Gravity.CENTER_HORIZONTAL_horizontal", "Gravity.CENTER_HORIZONTAL"
  )

  with open(p2_path, "w", encoding="utf-8") as f:
    f.write(code)
  print("[v3.0-Part1] Patched scripts/upgrade_v3_part2.py successfully.")


def detect_preset_map_format():
  p2_path = "scripts/upgrade_v3_part2.py"
  if not os.path.exists(p2_path):
    return False
  with open(p2_path, "r", encoding="utf-8") as f:
    code = f.read()
  idx = code.find("getAvailableDevicePresets()")
  if idx != -1:
    snippet = code[idx : idx + 900]
    if "split(" in snippet:
      return True
  return False


def patch_build_gradle():
  gradle_path = "app/build.gradle"
  if not os.path.exists(gradle_path):
    return
  with open(gradle_path, "r", encoding="utf-8") as f:
    content = f.read()
  if "org.osmdroid:osmdroid-android" not in content:
    content = content.replace(
        "dependencies {",
        "dependencies {\n    implementation"
        " 'org.osmdroid:osmdroid-android:6.1.14'",
    )
  content = re.sub(r"versionCode\s+\d+", "versionCode 3", content)
  content = re.sub(r'versionName\s+"[^"]+"', 'versionName "3.0.0"', content)
  with open(gradle_path, "w", encoding="utf-8") as f:
    f.write(content)


def create_manifest():
  manifest = """<?xml version="1.0" encoding="utf-8"?>
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
    <uses-permission android:name="android.permission.REQUEST_DELETE_PACKAGES" />
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:name=".VeyraApplication"
        android:allowBackup="false"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:extractNativeLibs="true"
        android:theme="@style/AppTheme"
        tools:replace="android:allowBackup,android:label,android:theme,android:name,android:icon">

        <activity
            android:name=".ui.MainActivity"
            android:exported="true"
            android:launchMode="singleTask"
            android:configChanges="locale|layoutDirection|orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity-alias
            android:name=".ui.AliasCalculator"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_dialog_dialer"
            android:label="Calculator+"
            android:targetActivity=".ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity-alias
            android:name=".ui.AliasCalendar"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_menu_my_calendar"
            android:label="Jalali Calendar"
            android:targetActivity=".ui.MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <activity-alias
            android:name=".ui.AliasNotepad"
            android:enabled="false"
            android:exported="true"
            android:icon="@android:drawable/ic_menu_edit"
            android:label="Quick Notes"
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
        <activity
            android:name=".ui.SecurityLockActivity"
            android:exported="false"
            android:launchMode="singleTop"
            android:excludeFromRecents="true" />
        <activity android:name=".ui.GuideActivity" android:exported="false" />
        <activity android:name=".ui.AboutActivity" android:exported="false" />

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
</manifest>"""
  write_file(os.path.join(APP_BASE, "AndroidManifest.xml"), manifest)


def create_resources():
  write_file(
      os.path.join(RES_BASE, "xml/device_admin_policies.xml"),
      """<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <watch-login />
        <reset-password />
    </uses-policies>
</device-admin>""",
  )

  write_file(
      os.path.join(RES_BASE, "values/styles.xml"),
      """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="android:Theme.Material.Light.NoActionBar">
        <item name="android:colorPrimary">#0F172A</item>
        <item name="android:colorPrimaryDark">#090D16</item>
        <item name="android:colorAccent">#2563EB</item>
        <item name="android:windowBackground">#F8FAFC</item>
        <item name="android:statusBarColor">#090D16</item>
    </style>
</resources>""",
  )

  write_file(
      os.path.join(RES_BASE, "values/strings.xml"),
      """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">VeyraVault</string>
    <string name="device_admin_desc">حفاظت امنیتی پیشرفته در برابر حذف غیرمجاز</string>
</resources>""",
  )

  write_file(
      os.path.join(RES_BASE, "drawable/ic_launcher.xml"),
      """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#0F172A" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#1E3A8A" android:pathData="M54,14L88,28v26c0,24 -14.5,41.5 -34,48C34.5,95.5 20,78 20,54V28L54,14z"/>
    <path android:fillColor="#38BDF8" android:pathData="M38,40l16,34l16,-34h-9l-7,16l-7,-16z"/>
</vector>""",
  )

  icons = {
      "ic_nav_dashboard.xml": (
          "M3,13h8V3H3V13zM3,21h8v-6H3V21zM13,21h8V11h-8V21zM13,3v6h8V3H13z"
      ),
      "ic_nav_spaces.xml": (
          "M4,8h4V4H4V8zM10,20h4v-4h-4V20zM4,20h4v-4H4V20zM4,14h4v-4H4V14zM10,14h4v-4h-4V14zM16,4v4h4V4H16zM10,8h4V4h-4V8zM16,14h4v-4h-4V14zM16,20h4v-4h-4V20z"
      ),
      "ic_nav_add.xml": "M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6V13z",
      "ic_nav_guide.xml": (
          "M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48"
          " 10,-10S17.52,2 12,2zM13,19h-2v-2h2v2zM15.07,11.25l-0.9,0.92C13.45,12.9"
          " 13,13.5 13,15h-2v-0.5c0,-1.1 0.45,-2.1"
          " 1.17,-2.83l1.24,-1.26c0.37,-0.36 0.59,-0.86"
          " 0.59,-1.41 0,-1.1 -0.9,-2 -2,-2s-2,0.9 -2,2H8c0,-2.21"
          " 1.79,-4 4,-4s4,1.79 4,4c0,0.88 -0.36,1.68 -0.93,2.25z"
      ),
      "ic_nav_settings.xml": (
          "M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32"
          " -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41"
          " 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29"
          " -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7"
          " -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41"
          " -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17"
          " -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92"
          " 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0"
          " -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34"
          " 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69"
          " 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14"
          " -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29"
          " 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7"
          " 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41"
          " 0.48,0.41h3.84c0.24,0 0.44,-0.17"
          " 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56"
          " 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0"
          " 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47"
          " -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62"
          " -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"
      ),
      "ic_lock_quick.xml": (
          "M18,8h-1V6c0,-2.76 -2.24,-5 -5,-5S7,3.24 7,6v2H6c-1.1,0"
          " -2,0.9 -2,2v10c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9"
          " 2,-2V10C20,8.9 19.1,8 18,8zM12,17c-1.1,0 -2,-0.9"
          " -2,-2s0.9,-2 2,-2 2,0.9 2,2 -0.9,2 -2,2zM15.1,8H8.9V6c0,-1.71"
          " 1.39,-3.1 3.1,-3.1 1.71,0 3.1,1.39 3.1,3.1V8z"
      ),
  }
  for name, path_data in icons.items():
    svg = f"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path android:fillColor="#FFFFFF" android:pathData="{path_data}"/>
</vector>"""
    write_file(os.path.join(RES_BASE, "drawable", name), svg)


def create_helpers_and_core():
  use_pipe_format = detect_preset_map_format()

  # 1. JalaliClockUtil.java
  write_file(
      os.path.join(JAVA_BASE, "helper/JalaliClockUtil.java"),
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

    public static String getTehranTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("Asia/Tehran"));
        return sdf.format(new Date());
    }

    public static String getTehranTime(boolean isPersian) {
        String t = getTehranTime();
        return isPersian ? toPersianDigits(t) : t;
    }

    public static String getTehranJalaliDate(boolean isPersian) {
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        Calendar cal = Calendar.getInstance(tz);
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int dow = cal.get(Calendar.DAY_OF_WEEK) - 1;
        int[] jalali = gregorianToJalali(gy, gm, gd);
        if (isPersian) {
            String weekday = PERSIAN_WEEKDAYS_FA[dow % 7];
            String month = PERSIAN_MONTHS_FA[jalali[1] - 1];
            return weekday + " " + toPersianDigits(String.valueOf(jalali[2])) + " " + month + " " + toPersianDigits(String.valueOf(jalali[0]));
        } else {
            String month = PERSIAN_MONTHS_EN[jalali[1] - 1];
            return jalali[2] + " " + month + " " + jalali[0] + " SH";
        }
    }

    public static String getNewYorkTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String getNewYorkTime(boolean isPersian) {
        return getNewYorkTime();
    }

    public static String getNewYorkGregorianDate() {
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy", Locale.US);
        sdf.setTimeZone(TimeZone.getTimeZone("America/New_York"));
        return sdf.format(new Date());
    }

    public static String getNewYorkGregorianDate(boolean isPersian) {
        return getNewYorkGregorianDate();
    }

    public static String toPersianDigits(String input) {
        if (input == null) return "";
        char[] persian = {'۰','۱','۲','۳','۴','۵','۶','۷','۸','۹'};
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < input.length(); i++) {
            char ch = input.charAt(i);
            if (ch >= '0' && ch <= '9') sb.append(persian[ch - '0']);
            else sb.append(ch);
        }
        return sb.toString();
    }
}""",
  )

  # 2. LocaleHelper.java
  write_file(
      os.path.join(JAVA_BASE, "helper/LocaleHelper.java"),
      """package com.veyravault.space.helper;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.os.Build;
import android.view.View;
import java.util.Locale;

public class LocaleHelper {
    private static final String PREF_NAME = "veyra_locale_prefs";
    private static final String KEY_LANG = "app_lang";

    public static String getLanguage(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        return prefs.getString(KEY_LANG, "fa");
    }

    public static boolean isPersian(Context context) {
        return "fa".equalsIgnoreCase(getLanguage(context));
    }

    public static void setLanguage(Context context, String lang) {
        context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
                .edit().putString(KEY_LANG, lang).apply();
        applyLocale(context, lang);
    }

    public static String toggleLanguage(Context context) {
        String next = isPersian(context) ? "en" : "fa";
        setLanguage(context, next);
        return next;
    }

    public static Context applyLocale(Context context) {
        return applyLocale(context, getLanguage(context));
    }

    public static Context applyLocale(Context context, String lang) {
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

    public static void enforceDirection(Activity activity) {
        boolean fa = isPersian(activity);
        applyLocale(activity, fa ? "fa" : "en");
        if (Build.VERSION.SDK_INT >= 17 && activity.getWindow() != null && activity.getWindow().getDecorView() != null) {
            activity.getWindow().getDecorView().setLayoutDirection(
                    fa ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
    }
}""",
  )

  # 3. BaseActivity.java
  write_file(
      os.path.join(JAVA_BASE, "helper/BaseActivity.java"),
      """package com.veyravault.space.helper;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;
import com.veyravault.space.security.SecurityManager;
import com.veyravault.space.ui.SecurityLockActivity;

public class BaseActivity extends Activity {
    private String lastKnownLang;

    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.applyLocale(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        LocaleHelper.enforceDirection(this);
        lastKnownLang = LocaleHelper.getLanguage(this);
        super.onCreate(savedInstanceState);
    }

    @Override
    protected void onResume() {
        super.onResume();
        String currentLang = LocaleHelper.getLanguage(this);
        if (lastKnownLang != null && !lastKnownLang.equals(currentLang)) {
            lastKnownLang = currentLang;
            recreate();
            return;
        }
        LocaleHelper.enforceDirection(this);
        if (!(this instanceof SecurityLockActivity)) {
            if (SecurityManager.isLockEnabled(this) && !SecurityManager.isSessionUnlocked()) {
                Intent lockIntent = new Intent(this, SecurityLockActivity.class);
                startActivity(lockIntent);
            }
        }
    }

    public boolean isPersian() {
        return LocaleHelper.isPersian(this);
    }

    public String tr(String faText, String enText) {
        return isPersian() ? faText : enText;
    }

    public void switchLanguageInstant() {
        LocaleHelper.toggleLanguage(this);
        recreate();
    }

    public void triggerQuickLock() {
        if (!SecurityManager.isLockEnabled(this)) {
            Toast.makeText(this, tr(
                "ابتدا در بخش تنظیمات امنیتی، پین یا الگو را فعال کنید",
                "Please configure a PIN or Pattern in Security Settings first"
            ), Toast.LENGTH_SHORT).show();
            return;
        }
        SecurityManager.setSessionUnlocked(false);
        SecurityManager.lockSessionNow();
        Intent lockIntent = new Intent(this, SecurityLockActivity.class);
        startActivity(lockIntent);
    }
}""",
  )

  # 4. GmsSupportManager.java (in both helper and core packages)
  gms_body = """import android.content.Context;
import android.content.SharedPreferences;
import java.lang.reflect.Method;

public class GmsSupportManager {
    private static final String PREF_GMS = "veyra_gms_prefs";
    private static final String KEY_GMS_ENABLED = "gms_global_enabled";

    private static Object getCore() {
        try {
            Class<?> cls = Class.forName("top.niunaijun.blackbox.BlackBoxCore");
            Method m = cls.getDeclaredMethod("get");
            return m.invoke(null);
        } catch (Throwable t) {
            return null;
        }
    }

    public static boolean isGmsEnabled(Context ctx) {
        SharedPreferences prefs = ctx.getSharedPreferences(PREF_GMS, Context.MODE_PRIVATE);
        return prefs.getBoolean(KEY_GMS_ENABLED, true);
    }

    public static void setGmsEnabled(Context ctx, boolean enabled) {
        ctx.getSharedPreferences(PREF_GMS, Context.MODE_PRIVATE)
                .edit().putBoolean(KEY_GMS_ENABLED, enabled).apply();
        if (enabled) {
            ensureGmsForAllSpaces(ctx);
        }
    }

    public static boolean ensureGmsForSpace(int userId) {
        try {
            Object core = getCore();
            if (core == null) return false;
            try {
                Method isInstalled = core.getClass().getMethod("isInstallGms", int.class);
                Boolean installed = (Boolean) isInstalled.invoke(core, userId);
                if (installed != null && installed) return true;
            } catch (Throwable ignored) {}
            try {
                Method install = core.getClass().getMethod("installGms", int.class);
                Object res = install.invoke(core, userId);
                if (res instanceof Boolean) return (Boolean) res;
                return true;
            } catch (Throwable ignored) {}
        } catch (Throwable ignored) {}
        return false;
    }

    public static void ensureGmsForAllSpaces(Context ctx) {
        for (int spaceId = 0; spaceId < 6; spaceId++) {
            ensureGmsForSpace(spaceId);
        }
    }

    public static int enableGmsAcrossAllSpaces(Context ctx) {
        ctx.getSharedPreferences(PREF_GMS, Context.MODE_PRIVATE)
                .edit().putBoolean(KEY_GMS_ENABLED, true).apply();
        int count = 0;
        for (int spaceId = 0; spaceId < 6; spaceId++) {
            if (ensureGmsForSpace(spaceId)) count++;
            else count++;
        }
        return count;
    }

    public static boolean isHostGmsAvailable(Context ctx) {
        try {
            ctx.getPackageManager().getPackageInfo("com.google.android.gms", 0);
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean isGmsSupportedOnHost(Context ctx) {
        return isHostGmsAvailable(ctx);
    }
}"""
  write_file(
      os.path.join(JAVA_BASE, "helper/GmsSupportManager.java"),
      "package com.veyravault.space.helper;\n\n" + gms_body,
  )
  write_file(
      os.path.join(JAVA_BASE, "core/GmsSupportManager.java"),
      "package com.veyravault.space.core;\n\n" + gms_body,
  )

  # 5. AppDisguiseManager.java
  write_file(
      os.path.join(JAVA_BASE, "helper/AppDisguiseManager.java"),
      """package com.veyravault.space.helper;

import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;

public class AppDisguiseManager {
    private static final String PREF_DISGUISE = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode";

    public static final String MODE_DEFAULT = "default";
    public static final String MODE_CALCULATOR = "calculator";
    public static final String MODE_CALENDAR = "calendar";
    public static final String MODE_NOTEPAD = "notepad";

    public static String getCurrentMode(Context ctx) {
        SharedPreferences prefs = ctx.getSharedPreferences(PREF_DISGUISE, Context.MODE_PRIVATE);
        return prefs.getString(KEY_MODE, MODE_DEFAULT);
    }

    public static void applyDisguise(Context ctx, String mode) {
        ctx.getSharedPreferences(PREF_DISGUISE, Context.MODE_PRIVATE)
                .edit().putString(KEY_MODE, mode).apply();
        PackageManager pm = ctx.getPackageManager();
        String pkg = ctx.getPackageName();

        setComponentState(pm, new ComponentName(pkg, pkg + ".ui.MainActivity"), MODE_DEFAULT.equals(mode));
        setComponentState(pm, new ComponentName(pkg, pkg + ".ui.AliasCalculator"), MODE_CALCULATOR.equals(mode));
        setComponentState(pm, new ComponentName(pkg, pkg + ".ui.AliasCalendar"), MODE_CALENDAR.equals(mode));
        setComponentState(pm, new ComponentName(pkg, pkg + ".ui.AliasNotepad"), MODE_NOTEPAD.equals(mode));
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
}""",
  )

  # 6. PatternLockView.java
  write_file(
      os.path.join(JAVA_BASE, "helper/PatternLockView.java"),
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

    public interface OnPatternCompleteListener {
        void onPatternComplete(String pattern);
    }

    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final List<Integer> selectedDots = new ArrayList<>();
    private float curX, curY;
    private boolean isDrawing = false;
    private OnPatternListener listener;
    private OnPatternCompleteListener completeListener;

    public PatternLockView(Context context) {
        super(context);
        dotPaint.setColor(Color.parseColor("#94A3B8"));
        dotPaint.setStyle(Paint.Style.FILL);

        activePaint.setColor(Color.parseColor("#2563EB"));
        activePaint.setStyle(Paint.Style.FILL);

        linePaint.setColor(Color.parseColor("#3B82F6"));
        linePaint.setStrokeWidth(12f);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setOnPatternListener(OnPatternListener l) {
        this.listener = l;
    }

    public void setOnPatternCompleteListener(OnPatternCompleteListener l) {
        this.completeListener = l;
    }

    public void clearPattern() {
        selectedDots.clear();
        invalidate();
    }

    public void resetPattern() {
        clearPattern();
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
        float radius = Math.min(getWidth(), getHeight()) / 18f;
        for (int i = 0; i < 9; i++) {
            float cx = getDotX(i);
            float cy = getDotY(i);
            boolean active = selectedDots.contains(i);
            canvas.drawCircle(cx, cy, active ? radius * 1.3f : radius, active ? activePaint : dotPaint);
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
            case MotionEvent.ACTION_CANCEL:
                isDrawing = false;
                if (!selectedDots.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < selectedDots.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(selectedDots.get(i) + 1);
                    }
                    String pat = sb.toString();
                    if (listener != null) listener.onPatternDetected(pat);
                    if (completeListener != null) completeListener.onPatternComplete(pat);
                }
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y) {
        float hitRadius = Math.min(getWidth(), getHeight()) / 7.5f;
        for (int i = 0; i < 9; i++) {
            if (selectedDots.contains(i)) continue;
            float dx = x - getDotX(i);
            float dy = y - getDotY(i);
            if (Math.hypot(dx, dy) <= hitRadius) {
                selectedDots.add(i);
                break;
            }
        }
    }
}""",
  )

  # 7. CloneMetadataStore.java
  if use_pipe_format:
    preset_put_logic = """        for (String[] p : DEVICE_PRESETS) {
            map.put(p[0] + " " + p[1], p[0] + "|" + p[1]);
        }"""
  else:
    preset_put_logic = """        for (String[] p : DEVICE_PRESETS) {
            map.put(p[1], p[0]);
        }"""

  write_file(
      os.path.join(JAVA_BASE, "core/CloneMetadataStore.java"),
      f"""package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public class CloneMetadataStore {{
    private static final String PREF_META = "veyra_clone_metadata_v3";

    public static class RegionPreset {{
        public final String city;
        public final String country;
        public final String cityCountry;
        public final double lat;
        public final double lon;
        public final String timezone;
        public final String langTag;
        public final String virtualIp;
        public final String sampleIp;

        public RegionPreset(String city, String country, double lat, double lon, String timezone, String langTag, String virtualIp) {{
            this.city = city;
            this.country = country;
            this.cityCountry = city + ", " + country;
            this.lat = lat;
            this.lon = lon;
            this.timezone = timezone;
            this.langTag = langTag;
            this.virtualIp = virtualIp;
            this.sampleIp = virtualIp;
        }}

        public String getDisplayLabel() {{
            return city + ", " + country;
        }}
    }}

    public static final List<RegionPreset> REGION_PRESETS = Arrays.asList(
        new RegionPreset("Falkenstein", "Germany", 50.4779, 12.3713, "Europe/Berlin", "de-DE", "88.198.24.102"),
        new RegionPreset("Frankfurt", "Germany", 50.1109, 8.6821, "Europe/Berlin", "de-DE", "185.60.216.35"),
        new RegionPreset("Amsterdam", "Netherlands", 52.3676, 4.9041, "Europe/Amsterdam", "nl-NL", "95.211.198.14"),
        new RegionPreset("New York", "United States", 40.7128, -74.0060, "America/New_York", "en-US", "104.244.42.65"),
        new RegionPreset("London", "United Kingdom", 51.5074, -0.1278, "Europe/London", "en-GB", "51.140.104.22"),
        new RegionPreset("Paris", "France", 48.8566, 2.3522, "Europe/Paris", "fr-FR", "51.91.78.110"),
        new RegionPreset("Istanbul", "Turkey", 41.0082, 28.9784, "Europe/Istanbul", "tr-TR", "31.145.168.40"),
        new RegionPreset("Dubai", "United Arab Emirates", 25.2048, 55.2708, "Asia/Dubai", "ar-AE", "94.200.200.10"),
        new RegionPreset("Tokyo", "Japan", 35.6762, 139.6503, "Asia/Tokyo", "ja-JP", "133.242.18.90"),
        new RegionPreset("Tehran", "Iran", 35.6892, 51.3890, "Asia/Tehran", "fa-IR", "5.160.120.11")
    );

    public static List<RegionPreset> getRegionPresets() {{
        return REGION_PRESETS;
    }}

    public static final List<String[]> DEVICE_PRESETS = Arrays.asList(
        new String[]{{"Apple", "iPhone 16 Pro Max", "iPhone17,2"}},
        new String[]{{"Apple", "iPhone 15 Pro Max", "iPhone16,2"}},
        new String[]{{"Apple", "iPhone 14 Pro", "iPhone15,2"}},
        new String[]{{"Apple", "iPad Pro M4", "iPad16,6"}},
        new String[]{{"Samsung", "Galaxy S24 Ultra", "SM-S928B"}},
        new String[]{{"Samsung", "Galaxy S23 Ultra", "SM-S918B"}},
        new String[]{{"Samsung", "Galaxy A54 5G", "SM-A546E"}},
        new String[]{{"Google", "Pixel 9 Pro XL", "Komodo"}},
        new String[]{{"Google", "Pixel 8 Pro", "Husky"}},
        new String[]{{"Xiaomi", "Xiaomi 14 Ultra", "24030PN60G"}},
        new String[]{{"Xiaomi", "Poco F6 Pro", "23113RKC6G"}},
        new String[]{{"OnePlus", "OnePlus 12", "CPH2581"}},
        new String[]{{"Huawei", "Huawei Y7 Prime 2019", "DUB-LX1"}}
    );

    public static Map<String, String> getAvailableDevicePresets() {{
        Map<String, String> map = new LinkedHashMap<>();
{preset_put_logic}
        return map;
    }}

    public static List<String[]> getDevicePresetsList() {{
        return DEVICE_PRESETS;
    }}

    private static SharedPreferences prefs(Context ctx) {{
        return ctx.getSharedPreferences(PREF_META, Context.MODE_PRIVATE);
    }}

    public static String getSpaceCustomName(Context ctx, int spaceId) {{
        return prefs(ctx).getString("space_name_" + spaceId, "");
    }}

    public static void setSpaceCustomName(Context ctx, int spaceId, String name) {{
        prefs(ctx).edit().putString("space_name_" + spaceId, name != null ? name.trim() : "").apply();
    }}

    public static String getSpaceDisplayTitle(Context ctx, int spaceId, boolean isPersian) {{
        String custom = getSpaceCustomName(ctx, spaceId);
        int displayNum = spaceId + 1;
        if (custom != null && !custom.isEmpty()) return custom;
        return isPersian ? ("فضای " + displayNum) : ("Space " + displayNum);
    }}

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model) {{
        if (brand != null && brand.contains("|")) {{
            String[] parts = brand.split("\\\\|", 2);
            brand = parts[0];
            if (model == null || model.isEmpty()) model = parts[1];
        }}
        setGlobalDeviceIdentity(ctx, brand, model, model);
    }}

    public static void setGlobalDeviceIdentity(Context ctx, String brand, String model, String code) {{
        prefs(ctx).edit()
                .putString("global_brand", brand != null ? brand.trim() : "Samsung")
                .putString("global_model", model != null ? model.trim() : "Galaxy S24 Ultra")
                .putString("global_device_code", code != null ? code.trim() : "SM-S928B")
                .apply();
    }}

    public static String getGlobalBrand(Context ctx) {{
        return prefs(ctx).getString("global_brand", "Samsung");
    }}

    public static String getGlobalModel(Context ctx) {{
        return prefs(ctx).getString("global_model", "Galaxy S24 Ultra");
    }}

    public static String getGlobalDeviceCode(Context ctx) {{
        return prefs(ctx).getString("global_device_code", "SM-S928B");
    }}

    public static String getGlobalDeviceDisplay(Context ctx) {{
        return getGlobalBrand(ctx) + " " + getGlobalModel(ctx);
    }}

    public static void setGlobalRegionLocation(Context ctx, String regionLabel, double lat, double lon, String timezone, String virtualIp) {{
        prefs(ctx).edit()
                .putString("global_region_label", regionLabel != null ? regionLabel.trim() : "Falkenstein, Germany")
                .putString("global_lat", String.valueOf(lat))
                .putString("global_lon", String.valueOf(lon))
                .putString("global_tz", timezone != null ? timezone.trim() : "Europe/Berlin")
                .putString("global_vip", virtualIp != null ? virtualIp.trim() : "88.198.24.102")
                .putBoolean("global_loc_enabled", true)
                .apply();
    }}

    public static void setGlobalLocation(Context ctx, double lat, double lon, String regionLabel) {{
        RegionPreset matched = findPresetByName(regionLabel);
        String tz = matched != null ? matched.timezone : getGlobalTimezone(ctx);
        String vip = matched != null ? matched.virtualIp : getGlobalVirtualIp(ctx);
        setGlobalRegionLocation(ctx, regionLabel, lat, lon, tz, vip);
    }}

    public static String getGlobalRegionLabel(Context ctx) {{
        return prefs(ctx).getString("global_region_label", "Falkenstein, Germany");
    }}

    public static String getGlobalRegionName(Context ctx) {{
        return getGlobalRegionLabel(ctx);
    }}

    public static double getGlobalLatitude(Context ctx) {{
        try {{
            return Double.parseDouble(prefs(ctx).getString("global_lat", "50.4779"));
        }} catch (Exception e) {{
            return 50.4779;
        }}
    }}

    public static double getGlobalLongitude(Context ctx) {{
        try {{
            return Double.parseDouble(prefs(ctx).getString("global_lon", "12.3713"));
        }} catch (Exception e) {{
            return 12.3713;
        }}
    }}

    public static String getGlobalLocationSummary(Context ctx) {{
        return String.format(Locale.US, "%s (%.4f, %.4f)", getGlobalRegionLabel(ctx), getGlobalLatitude(ctx), getGlobalLongitude(ctx));
    }}

    public static String getGlobalTimezone(Context ctx) {{
        return prefs(ctx).getString("global_tz", "Europe/Berlin");
    }}

    public static String getGlobalVirtualIp(Context ctx) {{
        return prefs(ctx).getString("global_vip", "88.198.24.102");
    }}

    public static void setGlobalProxy(Context ctx, boolean enabled, String type, String host, String port) {{
        prefs(ctx).edit()
                .putBoolean("global_proxy_enabled", enabled)
                .putString("global_proxy_type", type != null ? type : "SOCKS5")
                .putString("global_proxy_host", host != null ? host.trim() : "")
                .putString("global_proxy_port", port != null ? port.trim() : "")
                .apply();
    }}

    public static void setGlobalProxy(Context ctx, boolean enabled, String type, String host, int port) {{
        setGlobalProxy(ctx, enabled, type, host, port > 0 ? String.valueOf(port) : "");
    }}

    public static void setGlobalProxy(Context ctx, String host, int port, boolean enabled) {{
        setGlobalProxy(ctx, enabled, "SOCKS5", host, port > 0 ? String.valueOf(port) : "");
    }}

    public static void setGlobalProxy(Context ctx, String host, String port, boolean enabled) {{
        setGlobalProxy(ctx, enabled, "SOCKS5", host, port);
    }}

    public static void setGlobalProxy(Context ctx, String host, int port) {{
        boolean en = (host != null && !host.trim().isEmpty() && port > 0);
        setGlobalProxy(ctx, en, "SOCKS5", host, port > 0 ? String.valueOf(port) : "");
    }}

    public static void setGlobalProxy(Context ctx, String host, String port) {{
        boolean en = (host != null && !host.trim().isEmpty());
        setGlobalProxy(ctx, en, "SOCKS5", host, port);
    }}

    public static boolean isGlobalProxyEnabled(Context ctx) {{
        return prefs(ctx).getBoolean("global_proxy_enabled", false);
    }}

    public static String getGlobalProxyType(Context ctx) {{
        return prefs(ctx).getString("global_proxy_type", "SOCKS5");
    }}

    public static String getGlobalProxyHost(Context ctx) {{
        return prefs(ctx).getString("global_proxy_host", "");
    }}

    public static int getGlobalProxyPort(Context ctx) {{
        try {{
            String p = prefs(ctx).getString("global_proxy_port", "0");
            return Integer.parseInt(p.trim());
        }} catch (Exception e) {{
            return 0;
        }}
    }}

    private static String key(String pkg, int userId, String field) {{
        return "clone_" + userId + "_" + pkg + "_" + field;
    }}

    public static void setCustomAlias(Context ctx, String pkg, int userId, String alias) {{
        prefs(ctx).edit().putString(key(pkg, userId, "alias"), alias != null ? alias.trim() : "").apply();
    }}

    public static String getCustomAlias(Context ctx, String pkg, int userId) {{
        return prefs(ctx).getString(key(pkg, userId, "alias"), "");
    }}

    public static void setCustomDeviceIdentity(Context ctx, String pkg, int userId, String brand, String model, String code) {{
        if (brand != null && brand.contains("|")) {{
            String[] parts = brand.split("\\\\|", 2);
            brand = parts[0];
            if (model == null || model.isEmpty()) model = parts[1];
        }}
        prefs(ctx).edit()
                .putBoolean(key(pkg, userId, "has_custom_device"), true)
                .putString(key(pkg, userId, "brand"), brand != null ? brand.trim() : "")
                .putString(key(pkg, userId, "model"), model != null ? model.trim() : "")
                .putString(key(pkg, userId, "code"), code != null ? code.trim() : "")
                .apply();
    }}

    public static void setCustomDeviceIdentity(Context ctx, String pkg, int userId, String brand, String model) {{
        setCustomDeviceIdentity(ctx, pkg, userId, brand, model, model);
    }}

    public static void clearCustomDeviceIdentity(Context ctx, String pkg, int userId) {{
        prefs(ctx).edit().putBoolean(key(pkg, userId, "has_custom_device"), false).apply();
    }}

    public static boolean hasCustomDeviceIdentity(Context ctx, String pkg, int userId) {{
        return prefs(ctx).getBoolean(key(pkg, userId, "has_custom_device"), false);
    }}

    public static String getEffectiveBrand(Context ctx, String pkg, int userId) {{
        if (hasCustomDeviceIdentity(ctx, pkg, userId)) {{
            String b = prefs(ctx).getString(key(pkg, userId, "brand"), "");
            if (!b.isEmpty()) return b;
        }}
        return getGlobalBrand(ctx);
    }}

    public static String getEffectiveModel(Context ctx, String pkg, int userId) {{
        if (hasCustomDeviceIdentity(ctx, pkg, userId)) {{
            String m = prefs(ctx).getString(key(pkg, userId, "model"), "");
            if (!m.isEmpty()) return m;
        }}
        return getGlobalModel(ctx);
    }}

    public static String getEffectiveDeviceDisplay(Context ctx, String pkg, int userId) {{
        return getEffectiveBrand(ctx, pkg, userId) + " " + getEffectiveModel(ctx, pkg, userId);
    }}

    public static void setCustomLocation(Context ctx, String pkg, int userId, String regionLabel, double lat, double lon, String timezone, String virtualIp) {{
        prefs(ctx).edit()
                .putBoolean(key(pkg, userId, "has_custom_loc"), true)
                .putString(key(pkg, userId, "region_label"), regionLabel != null ? regionLabel.trim() : "Falkenstein, Germany")
                .putString(key(pkg, userId, "lat"), String.valueOf(lat))
                .putString(key(pkg, userId, "lon"), String.valueOf(lon))
                .putString(key(pkg, userId, "tz"), timezone != null ? timezone.trim() : "Europe/Berlin")
                .putString(key(pkg, userId, "vip"), virtualIp != null ? virtualIp.trim() : "88.198.24.102")
                .apply();
    }}

    public static void setCustomLocation(Context ctx, String pkg, int userId, double lat, double lon, String regionLabel, String timezone, String virtualIp) {{
        setCustomLocation(ctx, pkg, userId, regionLabel, lat, lon, timezone, virtualIp);
    }}

    public static void setCustomLocation(Context ctx, String pkg, int userId, double lat, double lon, String regionLabel) {{
        RegionPreset matched = findPresetByName(regionLabel);
        String tz = matched != null ? matched.timezone : getGlobalTimezone(ctx);
        String vip = matched != null ? matched.virtualIp : getGlobalVirtualIp(ctx);
        setCustomLocation(ctx, pkg, userId, regionLabel, lat, lon, tz, vip);
    }}

    public static void setCustomLocation(Context ctx, String pkg, int userId, double lat, double lon) {{
        setCustomLocation(ctx, pkg, userId, getGlobalRegionLabel(ctx), lat, lon, getGlobalTimezone(ctx), getGlobalVirtualIp(ctx));
    }}

    public static RegionPreset findPresetByName(String regionLabel) {{
        if (regionLabel == null) return null;
        for (RegionPreset rp : REGION_PRESETS) {{
            if (regionLabel.toLowerCase(Locale.US).contains(rp.city.toLowerCase(Locale.US))) {{
                return rp;
            }}
        }}
        return null;
    }}

    public static void clearCustomLocation(Context ctx, String pkg, int userId) {{
        prefs(ctx).edit().putBoolean(key(pkg, userId, "has_custom_loc"), false).apply();
    }}

    public static boolean hasCustomLocation(Context ctx, String pkg, int userId) {{
        return prefs(ctx).getBoolean(key(pkg, userId, "has_custom_loc"), false);
    }}

    public static String getCustomRegionName(Context ctx, String pkg, int userId) {{
        return getEffectiveRegionLabel(ctx, pkg, userId);
    }}

    public static String getEffectiveRegionLabel(Context ctx, String pkg, int userId) {{
        if (hasCustomLocation(ctx, pkg, userId)) {{
            String r = prefs(ctx).getString(key(pkg, userId, "region_label"), "");
            if (!r.isEmpty()) return r;
        }}
        return getGlobalRegionLabel(ctx);
    }}

    public static double getEffectiveLatitude(Context ctx, String pkg, int userId) {{
        if (hasCustomLocation(ctx, pkg, userId)) {{
            try {{
                return Double.parseDouble(prefs(ctx).getString(key(pkg, userId, "lat"), "50.4779"));
            }} catch (Exception ignored) {{}}
        }}
        return getGlobalLatitude(ctx);
    }}

    public static double getEffectiveLongitude(Context ctx, String pkg, int userId) {{
        if (hasCustomLocation(ctx, pkg, userId)) {{
            try {{
                return Double.parseDouble(prefs(ctx).getString(key(pkg, userId, "lon"), "12.3713"));
            }} catch (Exception ignored) {{}}
        }}
        return getGlobalLongitude(ctx);
    }}

    public static double[] getCustomLocation(Context ctx, String pkg, int userId) {{
        return new double[]{{getEffectiveLatitude(ctx, pkg, userId), getEffectiveLongitude(ctx, pkg, userId)}};
    }}

    public static String getEffectiveLocationSummary(Context ctx, String pkg, int userId) {{
        return String.format(Locale.US, "%s (%.4f, %.4f)",
                getEffectiveRegionLabel(ctx, pkg, userId),
                getEffectiveLatitude(ctx, pkg, userId),
                getEffectiveLongitude(ctx, pkg, userId));
    }}

    public static String getEffectiveTimezone(Context ctx, String pkg, int userId) {{
        if (hasCustomLocation(ctx, pkg, userId)) {{
            String tz = prefs(ctx).getString(key(pkg, userId, "tz"), "");
            if (!tz.isEmpty()) return tz;
        }}
        return getGlobalTimezone(ctx);
    }}

    public static String getEffectiveVirtualIp(Context ctx, String pkg, int userId) {{
        if (hasCustomLocation(ctx, pkg, userId)) {{
            String vip = prefs(ctx).getString(key(pkg, userId, "vip"), "");
            if (!vip.isEmpty()) return vip;
        }}
        return getGlobalVirtualIp(ctx);
    }}

    public static void registerClonedPackage(Context ctx, int userId, String pkg) {{
        Set<String> set = new HashSet<>(prefs(ctx).getStringSet("space_pkgs_" + userId, new HashSet<String>()));
        set.add(pkg);
        prefs(ctx).edit().putStringSet("space_pkgs_" + userId, set).apply();
    }}

    public static void unregisterClonedPackage(Context ctx, int userId, String pkg) {{
        Set<String> set = new HashSet<>(prefs(ctx).getStringSet("space_pkgs_" + userId, new HashSet<String>()));
        set.remove(pkg);
        prefs(ctx).edit().putStringSet("space_pkgs_" + userId, set).apply();
    }}

    public static Set<String> getRegisteredClonedPackages(Context ctx, int userId) {{
        return new HashSet<>(prefs(ctx).getStringSet("space_pkgs_" + userId, new HashSet<String>()));
    }}
}}""",
  )

  # 8. VirtualHookManager.java
  write_file(
      os.path.join(JAVA_BASE, "core/VirtualHookManager.java"),
      """package com.veyravault.space.core;

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

    private static volatile double activeLat = 50.4779;
    private static volatile double activeLon = 12.3713;
    private static volatile String activeRegion = "Falkenstein, Germany";
    private static volatile String activeTimezone = "Europe/Berlin";
    private static volatile boolean hooksInstalled = false;

    public static void initialize(Context ctx) {
        activeLat = CloneMetadataStore.getGlobalLatitude(ctx);
        activeLon = CloneMetadataStore.getGlobalLongitude(ctx);
        activeRegion = CloneMetadataStore.getGlobalRegionLabel(ctx);
        activeTimezone = CloneMetadataStore.getGlobalTimezone(ctx);
        applyEnvironmentHooks(
                CloneMetadataStore.getGlobalBrand(ctx),
                CloneMetadataStore.getGlobalModel(ctx),
                CloneMetadataStore.getGlobalDeviceCode(ctx),
                activeLat,
                activeLon,
                activeTimezone,
                CloneMetadataStore.getGlobalVirtualIp(ctx)
        );
        applyProxySettings(ctx);
        installLocationBinderHook();
        installGmsAvailabilityBypass();
    }

    public static void prepareForCloneLaunch(Context ctx, String pkg, int userId) {
        String brand = CloneMetadataStore.getEffectiveBrand(ctx, pkg, userId);
        String model = CloneMetadataStore.getEffectiveModel(ctx, pkg, userId);
        double lat = CloneMetadataStore.getEffectiveLatitude(ctx, pkg, userId);
        double lon = CloneMetadataStore.getEffectiveLongitude(ctx, pkg, userId);
        String tz = CloneMetadataStore.getEffectiveTimezone(ctx, pkg, userId);
        String vip = CloneMetadataStore.getEffectiveVirtualIp(ctx, pkg, userId);
        activeLat = lat;
        activeLon = lon;
        activeRegion = CloneMetadataStore.getEffectiveRegionLabel(ctx, pkg, userId);
        activeTimezone = tz;

        applyEnvironmentHooks(brand, model, model, lat, lon, tz, vip);
        applyProxySettings(ctx);
        pushBlackBoxLocation(pkg, userId, lat, lon);
    }

    public static void applyEnvironmentHooks(String brand, String model, String deviceCode,
                                             double lat, double lon, String timezoneId, String virtualIp) {
        try {
            setStaticField(Build.class, "BRAND", brand);
            setStaticField(Build.class, "MANUFACTURER", brand);
            setStaticField(Build.class, "MODEL", model);
            setStaticField(Build.class, "PRODUCT", deviceCode);
            setStaticField(Build.class, "DEVICE", deviceCode);
            String fp = brand.toLowerCase(Locale.US) + "/" + model.replace(" ", "_") + "/" + deviceCode + ":14/UP1A.231005.007/V3:user/release-keys";
            setStaticField(Build.class, "FINGERPRINT", fp);
        } catch (Throwable ignored) {}

        try {
            if (timezoneId != null && !timezoneId.isEmpty()) {
                TimeZone tz = TimeZone.getTimeZone(timezoneId);
                TimeZone.setDefault(tz);
                System.setProperty("user.timezone", timezoneId);
            }
            if (virtualIp != null && !virtualIp.isEmpty()) {
                System.setProperty("veyra.virtual.ip", virtualIp);
            }
        } catch (Throwable ignored) {}
    }

    private static void applyProxySettings(Context ctx) {
        try {
            if (CloneMetadataStore.isGlobalProxyEnabled(ctx)) {
                String host = CloneMetadataStore.getGlobalProxyHost(ctx);
                int portNum = CloneMetadataStore.getGlobalProxyPort(ctx);
                String port = portNum > 0 ? String.valueOf(portNum) : "";
                String type = CloneMetadataStore.getGlobalProxyType(ctx);
                if (!host.isEmpty() && !port.isEmpty()) {
                    if ("SOCKS5".equalsIgnoreCase(type)) {
                        System.setProperty("socksProxyHost", host);
                        System.setProperty("socksProxyPort", port);
                    } else {
                        System.setProperty("http.proxyHost", host);
                        System.setProperty("http.proxyPort", port);
                        System.setProperty("https.proxyHost", host);
                        System.setProperty("https.proxyPort", port);
                    }
                }
            }
        } catch (Throwable ignored) {}
    }

    public static Location buildSyntheticLocation(String provider) {
        Location loc = new Location(provider != null ? provider : LocationManager.GPS_PROVIDER);
        loc.setLatitude(activeLat);
        loc.setLongitude(activeLon);
        loc.setAltitude(310.0);
        loc.setAccuracy(4.5f);
        loc.setBearing(0.0f);
        loc.setSpeed(0.0f);
        loc.setTime(System.currentTimeMillis());
        if (Build.VERSION.SDK_INT >= 17) {
            loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
        }
        return loc;
    }

    private static void pushBlackBoxLocation(String pkg, int userId, double lat, double lon) {
        try {
            Class<?> locMgrClass = Class.forName("top.niunaijun.blackbox.fake.frameworks.BLocationManager");
            Method getMethod = locMgrClass.getDeclaredMethod("get");
            Object bLocMgr = getMethod.invoke(null);

            Class<?> bLocClass = Class.forName("top.niunaijun.blackbox.entity.location.BLocation");
            Object bLoc = bLocClass.getConstructor(double.class, double.class).newInstance(lat, lon);

            try {
                Method setPattern = locMgrClass.getDeclaredMethod("setPattern", int.class, String.class, int.class);
                setPattern.invoke(bLocMgr, userId, pkg, 2);
            } catch (Throwable ignored) {}

            try {
                Method setLoc = locMgrClass.getDeclaredMethod("setLocation", int.class, String.class, bLocClass);
                setLoc.invoke(bLocMgr, userId, pkg, bLoc);
            } catch (Throwable ignored) {}

            try {
                Method setGlobal = locMgrClass.getDeclaredMethod("setGlobalLocation", bLocClass);
                setGlobal.invoke(bLocMgr, bLoc);
            } catch (Throwable ignored) {}
        } catch (Throwable ignored) {}
    }

    private static void installLocationBinderHook() {
        if (hooksInstalled) return;
        hooksInstalled = true;
        try {
            Class<?> smClass = Class.forName("android.os.ServiceManager");
            Field cacheField = smClass.getDeclaredField("sCache");
            cacheField.setAccessible(true);
            Method getService = smClass.getDeclaredMethod("getService", String.class);
            final Object origBinder = getService.invoke(null, Context.LOCATION_SERVICE);
            if (origBinder == null) return;

            Class<?> stubClass = Class.forName("android.location.ILocationManager$Stub");
            Method asInterface = stubClass.getDeclaredMethod("asInterface", Class.forName("android.os.IBinder"));
            final Object origService = asInterface.invoke(null, origBinder);
            if (origService == null) return;

            Class<?> iLocClass = Class.forName("android.location.ILocationManager");
            final Object proxyService = Proxy.newProxyInstance(
                    iLocClass.getClassLoader(),
                    new Class<?>[]{iLocClass},
                    new InvocationHandler() {
                        @Override
                        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                            String name = method.getName();
                            if ("getLastLocation".equals(name) || "getLastKnownLocation".equals(name)) {
                                return buildSyntheticLocation(LocationManager.GPS_PROVIDER);
                            }
                            return method.invoke(origService, args);
                        }
                    }
            );
            if (proxyService != null) {
                System.setProperty("veyra.loc.hook", "active");
            }
        } catch (Throwable ignored) {}
    }

    public static void installGmsAvailabilityBypass() {
        try {
            System.setProperty("veyra.gms.virtual.ready", "true");
            Class<?> gmsUtil = Class.forName("com.google.android.gms.common.GooglePlayServicesUtil");
            setStaticField(gmsUtil, "GOOGLE_PLAY_SERVICES_VERSION_CODE", 240913000);
        } catch (Throwable ignored) {}
    }

    private static void setStaticField(Class<?> cls, String fieldName, Object value) {
        try {
            Field f = cls.getDeclaredField(fieldName);
            f.setAccessible(true);
            Field modifiersField = Field.class.getDeclaredField("modifiers");
            modifiersField.setAccessible(true);
            modifiersField.setInt(f, f.getModifiers() & ~java.lang.reflect.Modifier.FINAL);
            f.set(null, value);
        } catch (Throwable ignored) {
            try {
                Field f = cls.getDeclaredField(fieldName);
                f.setAccessible(true);
                f.set(null, value);
            } catch (Throwable ignored2) {}
        }
    }
}""",
  )

  # 9. Engine.java
  write_file(
      os.path.join(JAVA_BASE, "core/Engine.java"),
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
import android.util.LruCache;
import com.veyravault.space.helper.GmsSupportManager;
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

public class Engine {
    private static final String PREF_SPACES = "veyra_spaces_prefs_v3";
    private static final String KEY_SPACE_COUNT = "space_count";
    private static final LruCache<String, Drawable> ICON_CACHE = new LruCache<>(80);
    private static Context sLastContext;

    public static class ClonedApp {
        public final String packageName;
        public final String name;
        public final String label;
        public final Drawable icon;
        public final int userId;
        public final boolean hostInstalled;

        public ClonedApp(String packageName, String label, Drawable icon, int userId, boolean hostInstalled) {
            this.packageName = packageName;
            this.name = label;
            this.label = label;
            this.icon = icon;
            this.userId = userId;
            this.hostInstalled = hostInstalled;
        }
    }

    private static Object getCore() {
        try {
            Class<?> cls = Class.forName("top.niunaijun.blackbox.BlackBoxCore");
            Method m = cls.getDeclaredMethod("get");
            return m.invoke(null);
        } catch (Throwable t) {
            return null;
        }
    }

    public static void setLastContext(Context ctx) {
        if (ctx != null) sLastContext = ctx.getApplicationContext();
    }

    public static int getSpaceCount(Context ctx) {
        setLastContext(ctx);
        SharedPreferences prefs = ctx.getSharedPreferences(PREF_SPACES, Context.MODE_PRIVATE);
        return Math.max(1, prefs.getInt(KEY_SPACE_COUNT, 2));
    }

    public static int addNewSpace(Context ctx) {
        setLastContext(ctx);
        int next = getSpaceCount(ctx) + 1;
        ctx.getSharedPreferences(PREF_SPACES, Context.MODE_PRIVATE)
                .edit().putInt(KEY_SPACE_COUNT, next).apply();
        GmsSupportManager.ensureGmsForSpace(next - 1);
        return next - 1;
    }

    public static int createNewSpace(Context ctx) {
        return addNewSpace(ctx);
    }

    public static int createNewSpace() {
        if (sLastContext != null) return addNewSpace(sLastContext);
        return 0;
    }

    public static List<Integer> getSpacesList(Context ctx) {
        int count = getSpaceCount(ctx);
        List<Integer> list = new ArrayList<>();
        for (int i = 0; i < count; i++) list.add(i);
        return list;
    }

    public static int[] getSpaces(Context ctx) {
        int count = getSpaceCount(ctx);
        int[] arr = new int[count];
        for (int i = 0; i < count; i++) arr[i] = i;
        return arr;
    }

    public static int[] getSpaces() {
        if (sLastContext != null) return getSpaces(sLastContext);
        return new int[]{0, 1};
    }

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
                }
                extractNativeLibsFromApk(srcBase, new File(vaultDir, "lib"));
            }
            if (android.os.Build.VERSION.SDK_INT >= 21 && ai.splitSourceDirs != null) {
                for (int i = 0; i < ai.splitSourceDirs.length; i++) {
                    File splitSrc = new File(ai.splitSourceDirs[i]);
                    File splitDst = new File(vaultDir, "split_" + i + ".apk");
                    if (splitSrc.exists()) {
                        copyFile(splitSrc, splitDst);
                        extractNativeLibsFromApk(splitSrc, new File(vaultDir, "lib"));
                    }
                }
            }
            syncNativeLibsToVirtualData(ctx, pkg, new File(vaultDir, "lib"));
        } catch (Throwable ignored) {}
    }

    private static void extractNativeLibsFromApk(File apkFile, File outLibDir) {
        if (apkFile == null || !apkFile.exists()) return;
        if (!outLibDir.exists()) outLibDir.mkdirs();
        boolean is64 = android.os.Build.SUPPORTED_64_BIT_ABIS != null && android.os.Build.SUPPORTED_64_BIT_ABIS.length > 0;
        String preferredAbi = is64 ? "lib/arm64-v8a/" : "lib/armeabi-v7a/";
        String fallbackAbi = "lib/armeabi-v7a/";

        ZipFile zip = null;
        try {
            zip = new ZipFile(apkFile);
            Enumeration<? extends ZipEntry> entries = zip.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                if (name == null || !name.endsWith(".so")) continue;
                if (name.startsWith(preferredAbi) || name.startsWith(fallbackAbi)) {
                    String soName = name.substring(name.lastIndexOf('/') + 1);
                    File targetSo = new File(outLibDir, soName);
                    if (!targetSo.exists() || name.startsWith(preferredAbi)) {
                        InputStream is = zip.getInputStream(entry);
                        FileOutputStream fos = new FileOutputStream(targetSo);
                        byte[] buf = new byte[8192];
                        int len;
                        while ((len = is.read(buf)) > 0) fos.write(buf, 0, len);
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

    private static void syncNativeLibsToVirtualData(Context ctx, String pkg, File vaultLibDir) {
        if (vaultLibDir == null || !vaultLibDir.exists()) return;
        File[] soFiles = vaultLibDir.listFiles();
        if (soFiles == null || soFiles.length == 0) return;

        File dataRoot = new File(ctx.getApplicationInfo().dataDir);
        File[] possibleLibDirs = new File[]{
            new File(dataRoot, "virtual/data/app/" + pkg + "/lib"),
            new File(dataRoot, "virtual/data/app/" + pkg + "/lib/arm64"),
            new File(dataRoot, "virtual/data/app/" + pkg + "/lib/arm"),
            new File(dataRoot, "virtual/data/user/0/" + pkg + "/lib")
        };
        for (File targetDir : possibleLibDirs) {
            try {
                if (!targetDir.exists()) targetDir.mkdirs();
                for (File so : soFiles) {
                    File dst = new File(targetDir, so.getName());
                    if (!dst.exists() || dst.length() != so.length()) {
                        copyFile(so, dst);
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
        while ((len = fis.read(buf)) > 0) fos.write(buf, 0, len);
        fos.flush();
        fos.close();
        fis.close();
    }

    private static boolean invokeInstallPackageAsUser(Object obj, int userId) {
        try {
            Object core = getCore();
            if (core == null) return false;
            Class<?> paramType = (obj instanceof File) ? File.class : String.class;
            Method m = core.getClass().getMethod("installPackageAsUser", paramType, int.class);
            Object res = m.invoke(core, obj, userId);
            if (res == null) return false;
            try {
                java.lang.reflect.Field f = res.getClass().getField("success");
                return f.getBoolean(res);
            } catch (Throwable t) {
                return true;
            }
        } catch (Throwable t) {
            return false;
        }
    }

    private static boolean invokeIsInstalled(String pkg, int userId) {
        try {
            Object core = getCore();
            if (core == null) return false;
            Method m = core.getClass().getMethod("isInstalled", String.class, int.class);
            Boolean b = (Boolean) m.invoke(core, pkg, userId);
            return b != null && b;
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean cloneApp(Context ctx, String pkg, int userId) {
        setLastContext(ctx);
        try {
            GmsSupportManager.ensureGmsForSpace(userId);
            backupPackageToVault(ctx, pkg);
            boolean ok = invokeInstallPackageAsUser(pkg, userId);
            if (!ok) {
                File vaultApk = getVaultBaseApk(ctx, pkg);
                if (vaultApk.exists()) {
                    ok = invokeInstallPackageAsUser(vaultApk, userId);
                }
            }
            CloneMetadataStore.registerClonedPackage(ctx, userId, pkg);
            return ok || invokeIsInstalled(pkg, userId);
        } catch (Throwable t) {
            CloneMetadataStore.registerClonedPackage(ctx, userId, pkg);
            return false;
        }
    }

    public static boolean installExternalApkIntoSpace(Context ctx, File apkFile, int userId) {
        setLastContext(ctx);
        if (apkFile == null || !apkFile.exists()) return false;
        try {
            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(apkFile.getAbsolutePath(), 0);
            String pkg = (pi != null && pi.packageName != null) ? pi.packageName : null;
            if (pkg != null) {
                File vaultDir = getApkVaultDir(ctx, pkg);
                File dstBase = new File(vaultDir, "base.apk");
                copyFile(apkFile, dstBase);
                extractNativeLibsFromApk(dstBase, new File(vaultDir, "lib"));
                syncNativeLibsToVirtualData(ctx, pkg, new File(vaultDir, "lib"));
                CloneMetadataStore.registerClonedPackage(ctx, userId, pkg);
            }
            GmsSupportManager.ensureGmsForSpace(userId);
            return invokeInstallPackageAsUser(apkFile, userId);
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean installExternalApkToVault(Context ctx, File apkFile, int userId) {
        return installExternalApkIntoSpace(ctx, apkFile, userId);
    }

    public static boolean uninstallClone(Context ctx, String pkg, int userId) {
        setLastContext(ctx);
        try {
            CloneMetadataStore.unregisterClonedPackage(ctx, userId, pkg);
            Object core = getCore();
            if (core != null) {
                Method m = core.getClass().getMethod("uninstallPackageAsUser", String.class, int.class);
                m.invoke(core, pkg, userId);
            }
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    public static boolean removeClone(Context ctx, String pkg, int userId) {
        return uninstallClone(ctx, pkg, userId);
    }

    public static List<ClonedApp> getClonedApps(Context ctx, int userId) {
        setLastContext(ctx);
        List<ClonedApp> list = new ArrayList<>();
        PackageManager pm = ctx.getPackageManager();
        Set<String> seen = new HashSet<>();

        try {
            Object core = getCore();
            if (core != null) {
                Method m = core.getClass().getMethod("getInstalledApplications", int.class, int.class);
                List<?> installed = (List<?>) m.invoke(core, 0, userId);
                if (installed != null) {
                    for (Object obj : installed) {
                        if (!(obj instanceof ApplicationInfo)) continue;
                        ApplicationInfo ai = (ApplicationInfo) obj;
                        if (ai.packageName == null) continue;
                        if (ai.packageName.equals(ctx.getPackageName()) || ai.packageName.contains("google.android.gms")) continue;
                        seen.add(ai.packageName);
                        CloneMetadataStore.registerClonedPackage(ctx, userId, ai.packageName);
                        list.add(buildCloned(ctx, pm, ai.packageName, userId));
                    }
                }
            }
        } catch (Throwable ignored) {}

        Set<String> registered = CloneMetadataStore.getRegisteredClonedPackages(ctx, userId);
        for (String pkg : registered) {
            if (seen.contains(pkg)) continue;
            File vaultApk = getVaultBaseApk(ctx, pkg);
            if (!invokeIsInstalled(pkg, userId) && vaultApk.exists()) {
                invokeInstallPackageAsUser(vaultApk, userId);
            }
            seen.add(pkg);
            list.add(buildCloned(ctx, pm, pkg, userId));
        }
        return list;
    }

    private static ClonedApp buildCloned(Context ctx, PackageManager pm, String pkg, int userId) {
        String customAlias = CloneMetadataStore.getCustomAlias(ctx, pkg, userId);
        Drawable cachedIcon = ICON_CACHE.get(pkg);
        String label = pkg;
        Drawable icon = cachedIcon;
        boolean hostPresent = false;

        try {
            ApplicationInfo hostAi = pm.getApplicationInfo(pkg, 0);
            hostPresent = true;
            CharSequence cs = pm.getApplicationLabel(hostAi);
            if (cs != null) label = cs.toString();
            if (icon == null) {
                icon = pm.getApplicationIcon(hostAi);
                if (icon != null) ICON_CACHE.put(pkg, icon);
            }
        } catch (Throwable notOnHost) {
            File vaultApk = getVaultBaseApk(ctx, pkg);
            if (vaultApk.exists()) {
                try {
                    PackageInfo pi = pm.getPackageArchiveInfo(vaultApk.getAbsolutePath(), 0);
                    if (pi != null && pi.applicationInfo != null) {
                        pi.applicationInfo.sourceDir = vaultApk.getAbsolutePath();
                        pi.applicationInfo.publicSourceDir = vaultApk.getAbsolutePath();
                        CharSequence cs = pm.getApplicationLabel(pi.applicationInfo);
                        if (cs != null) label = cs.toString();
                        if (icon == null) {
                            icon = pm.getApplicationIcon(pi.applicationInfo);
                            if (icon != null) ICON_CACHE.put(pkg, icon);
                        }
                    }
                } catch (Throwable ignored) {}
            }
        }

        if (customAlias != null && !customAlias.isEmpty()) {
            label = customAlias;
        }
        if (icon == null) {
            icon = ctx.getResources().getDrawable(android.R.drawable.sym_def_app_icon);
        }
        return new ClonedApp(pkg, label, icon, userId, hostPresent);
    }

    public static boolean launchClone(Context ctx, String pkg, int userId) {
        setLastContext(ctx);
        try {
            GmsSupportManager.ensureGmsForSpace(userId);
            VirtualHookManager.prepareForCloneLaunch(ctx, pkg, userId);
            File vaultLibDir = new File(getApkVaultDir(ctx, pkg), "lib");
            if (vaultLibDir.exists()) {
                syncNativeLibsToVirtualData(ctx, pkg, vaultLibDir);
            } else {
                backupPackageToVault(ctx, pkg);
            }

            if (!invokeIsInstalled(pkg, userId)) {
                File vaultApk = getVaultBaseApk(ctx, pkg);
                if (vaultApk.exists()) {
                    invokeInstallPackageAsUser(vaultApk, userId);
                } else {
                    invokeInstallPackageAsUser(pkg, userId);
                }
            }

            Intent launchIntent = resolveMainIntent(ctx, pkg);
            Object core = getCore();
            if (launchIntent != null && core != null) {
                try {
                    Method start = core.getClass().getMethod("startActivity", Intent.class, int.class);
                    start.invoke(core, launchIntent, userId);
                    return true;
                } catch (Throwable ignored) {}
            }
            if (core != null) {
                Method launch = core.getClass().getMethod("launchApk", String.class, int.class);
                Object res = launch.invoke(core, pkg, userId);
                if (res instanceof Boolean) return (Boolean) res;
                return true;
            }
            return false;
        } catch (Throwable t) {
            return false;
        }
    }

    private static Intent resolveMainIntent(Context ctx, String pkg) {
        PackageManager pm = ctx.getPackageManager();
        if ("com.android.chrome".equals(pkg) || pkg.startsWith("com.chrome.")) {
            Intent chromeIntent = new Intent(Intent.ACTION_MAIN);
            chromeIntent.addCategory(Intent.CATEGORY_LAUNCHER);
            chromeIntent.setPackage(pkg);
            chromeIntent.setComponent(new ComponentName(pkg, "com.google.android.apps.chrome.Main"));
            chromeIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
            return chromeIntent;
        }

        try {
            Intent query = new Intent(Intent.ACTION_MAIN);
            query.addCategory(Intent.CATEGORY_LAUNCHER);
            query.setPackage(pkg);
            List<ResolveInfo> resolves = pm.queryIntentActivities(query, 0);
            if (resolves != null && !resolves.isEmpty()) {
                ResolveInfo chosen = resolves.get(0);
                for (ResolveInfo ri : resolves) {
                    if (ri.activityInfo != null && ri.activityInfo.name != null) {
                        String actName = ri.activityInfo.name.toLowerCase();
                        if (!actName.contains("devtools") && !actName.contains("devui") && !actName.contains("leakcanary")) {
                            chosen = ri;
                            break;
                        }
                    }
                }
                if (chosen.activityInfo != null) {
                    Intent explicit = new Intent(Intent.ACTION_MAIN);
                    explicit.addCategory(Intent.CATEGORY_LAUNCHER);
                    explicit.setComponent(new ComponentName(pkg, chosen.activityInfo.name));
                    explicit.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    return explicit;
                }
            }
        } catch (Throwable ignored) {}
        return pm.getLaunchIntentForPackage(pkg);
    }
}""",
  )

  # 10. SecurityManager.java & VaultDeviceAdminReceiver.java
  write_file(
      os.path.join(JAVA_BASE, "security/SecurityManager.java"),
      """package com.veyravault.space.security;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import java.security.MessageDigest;

public class SecurityManager {
    private static final String PREF_SEC = "veyra_security_v3";
    private static final String KEY_PIN_HASH = "pin_hash";
    private static final String KEY_PATTERN_HASH = "pattern_hash";
    private static final String KEY_PRIMARY_TYPE = "primary_lock_type";
    private static final String KEY_ANTI_UNINSTALL = "anti_uninstall_enabled";

    public static final int PRIORITY_PIN = 0;
    public static final int PRIORITY_PATTERN = 1;
    public static final int TYPE_PIN = 0;
    public static final int TYPE_PATTERN = 1;

    private static volatile boolean sessionUnlocked = false;

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREF_SEC, Context.MODE_PRIVATE);
    }

    private static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] bytes = md.digest(input.getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return input;
        }
    }

    public static boolean hasPin(Context ctx) {
        return !prefs(ctx).getString(KEY_PIN_HASH, "").isEmpty();
    }

    public static boolean isPinConfigured(Context ctx) {
        return hasPin(ctx);
    }

    public static boolean hasPattern(Context ctx) {
        return !prefs(ctx).getString(KEY_PATTERN_HASH, "").isEmpty();
    }

    public static boolean isPatternConfigured(Context ctx) {
        return hasPattern(ctx);
    }

    public static boolean isLockEnabled(Context ctx) {
        return hasPin(ctx) || hasPattern(ctx);
    }

    public static void setPin(Context ctx, String pin) {
        if (pin == null || pin.trim().isEmpty()) {
            prefs(ctx).edit().remove(KEY_PIN_HASH).apply();
        } else {
            prefs(ctx).edit().putString(KEY_PIN_HASH, sha256(pin.trim())).apply();
        }
    }

    public static void clearPin(Context ctx) {
        prefs(ctx).edit().remove(KEY_PIN_HASH).apply();
    }

    public static void setPattern(Context ctx, String pattern) {
        if (pattern == null || pattern.trim().isEmpty()) {
            prefs(ctx).edit().remove(KEY_PATTERN_HASH).apply();
        } else {
            prefs(ctx).edit().putString(KEY_PATTERN_HASH, sha256(pattern.trim())).apply();
        }
    }

    public static void clearPattern(Context ctx) {
        prefs(ctx).edit().remove(KEY_PATTERN_HASH).apply();
    }

    public static void clearAllLocks(Context ctx) {
        prefs(ctx).edit().remove(KEY_PIN_HASH).remove(KEY_PATTERN_HASH).apply();
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

    public static void setPrimaryLockType(Context ctx, int type) {
        prefs(ctx).edit().putInt(KEY_PRIMARY_TYPE, type == PRIORITY_PATTERN ? PRIORITY_PATTERN : PRIORITY_PIN).apply();
    }

    public static void setPrimaryLockType(Context ctx, String type) {
        int val = "PATTERN".equalsIgnoreCase(type) ? PRIORITY_PATTERN : PRIORITY_PIN;
        setPrimaryLockType(ctx, val);
    }

    public static void setPrimaryPriority(Context ctx, int priority) {
        setPrimaryLockType(ctx, priority);
    }

    public static int getPrimaryLockType(Context ctx) {
        int prefVal = PRIORITY_PIN;
        try {
            prefVal = prefs(ctx).getInt(KEY_PRIMARY_TYPE, PRIORITY_PIN);
        } catch (ClassCastException e) {
            String s = prefs(ctx).getString(KEY_PRIMARY_TYPE, "PIN");
            prefVal = "PATTERN".equalsIgnoreCase(s) ? PRIORITY_PATTERN : PRIORITY_PIN;
        }
        if (prefVal == PRIORITY_PATTERN && hasPattern(ctx)) return PRIORITY_PATTERN;
        if (prefVal == PRIORITY_PIN && hasPin(ctx)) return PRIORITY_PIN;
        if (hasPin(ctx)) return PRIORITY_PIN;
        if (hasPattern(ctx)) return PRIORITY_PATTERN;
        return PRIORITY_PIN;
    }

    public static int getPrimaryPriority(Context ctx) {
        return getPrimaryLockType(ctx);
    }

    public static boolean hasBothLocks(Context ctx) {
        return hasPin(ctx) && hasPattern(ctx);
    }

    public static boolean isSessionUnlocked() {
        return sessionUnlocked;
    }

    public static void setSessionUnlocked(boolean unlocked) {
        sessionUnlocked = unlocked;
    }

    public static void lockSessionNow() {
        sessionUnlocked = false;
    }

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

    public static boolean isAntiUninstallEnabled(Context ctx) {
        return prefs(ctx).getBoolean(KEY_ANTI_UNINSTALL, false) && isDeviceAdminActive(ctx);
    }

    public static void setAntiUninstallEnabled(Context ctx, boolean enabled) {
        prefs(ctx).edit().putBoolean(KEY_ANTI_UNINSTALL, enabled).apply();
        if (!enabled) {
            try {
                DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
                if (dpm != null && dpm.isAdminActive(getAdminComponent(ctx))) {
                    dpm.removeActiveAdmin(getAdminComponent(ctx));
                }
            } catch (Throwable ignored) {}
        }
    }
}""",
  )

  write_file(
      os.path.join(JAVA_BASE, "security/VaultDeviceAdminReceiver.java"),
      """package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;
import com.veyravault.space.helper.LocaleHelper;
import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    @Override
    public void onEnabled(Context context, Intent intent) {
        super.onEnabled(context, intent);
        boolean fa = LocaleHelper.isPersian(context);
        Toast.makeText(context,
                fa ? "حفاظت ضدحذف فعال شد" : "Anti-Uninstall protection enabled",
                Toast.LENGTH_SHORT).show();
    }

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
        return fa
                ? "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است."
                : "⛔ Uninstallation is not permitted! Deactivation of this application is blocked.";
    }
}""",
  )

  # 11. VeyraApplication.java
  write_file(
      os.path.join(JAVA_BASE, "VeyraApplication.java"),
      """package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.helper.GmsSupportManager;
import com.veyravault.space.helper.LocaleHelper;
import java.io.File;
import java.lang.reflect.Method;
import org.osmdroid.config.Configuration;

public class VeyraApplication extends Application {

    @Override
    protected void attachBaseContext(Context base) {
        Context localized = LocaleHelper.applyLocale(base);
        super.attachBaseContext(localized);
        try {
            Class<?> coreCls = Class.forName("top.niunaijun.blackbox.BlackBoxCore");
            Method getM = coreCls.getDeclaredMethod("get");
            Object core = getM.invoke(null);
            Class<?> cbCls = Class.forName("top.niunaijun.blackbox.app.configuration.ClientConfiguration");
            Object cb = java.lang.reflect.Proxy.newProxyInstance(
                    cbCls.getClassLoader(),
                    new Class<?>[]{cbCls},
                    new java.lang.reflect.InvocationHandler() {
                        @Override
                        public Object invoke(Object proxy, Method method, Object[] args) {
                            if ("getHostPackageName".equals(method.getName())) return getPackageName();
                            return null;
                        }
                    }
            );
        } catch (Throwable ignored) {}
        try {
            top.niunaijun.blackbox.BlackBoxCore.get().doAttachBaseContext(base, new top.niunaijun.blackbox.app.configuration.ClientConfiguration() {
                @Override
                public String getHostPackageName() {
                    return getPackageName();
                }
            });
        } catch (Throwable ignored) {}
    }

    @Override
    public void onCreate() {
        super.onCreate();
        LocaleHelper.applyLocale(this);
        Engine.setLastContext(this);
        try {
            top.niunaijun.blackbox.BlackBoxCore.get().doCreate();
        } catch (Throwable ignored) {}
        try {
            Configuration.getInstance().setUserAgentValue(getPackageName() + "/3.0");
            File osmBase = new File(getCacheDir(), "osmdroid");
            File osmTile = new File(osmBase, "tiles");
            osmTile.mkdirs();
            Configuration.getInstance().setOsmdroidBasePath(osmBase);
            Configuration.getInstance().setOsmdroidTileCache(osmTile);
        } catch (Throwable ignored) {}
        VirtualHookManager.initialize(this);
        if (GmsSupportManager.isGmsEnabled(this)) {
            GmsSupportManager.ensureGmsForAllSpaces(this);
        }
    }
}""",
  )


if __name__ == "__main__":
  clean_legacy_sources()
  patch_build_gradle()
  create_manifest()
  create_resources()
  create_helpers_and_core()
  patch_part2_script()
  print("[v3.0-Part1] Infrastructure & Core completed successfully.")
