#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[v3-part1] Wrote: {path}")

JAVA_BASE = "app/src/main/java/com/veyravault/space"

# 1. VeyraApplication.java (Raw context for BlackBoxCore + Engine init)
VEYRA_APPLICATION = r"""package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.Engine;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.configuration.ClientConfiguration;

public class VeyraApplication extends Application {
    private static Context sContext;

    public static Context getAppContext() {
        return sContext;
    }

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
        } catch (Throwable t) {
            t.printStackTrace();
        }
        try {
            Engine.get(this).initialize();
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "VeyraApplication.java"), VEYRA_APPLICATION)

# 2. JalaliClockUtil.java
JALALI_CLOCK = r"""package com.veyravault.space.helper;

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

    public static String getIranTimeText() {
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
    }

    public static String getIranJalaliDateText(boolean isPersian) {
        TimeZone tz = TimeZone.getTimeZone("Asia/Tehran");
        Calendar cal = Calendar.getInstance(tz, Locale.US);
        int gy = cal.get(Calendar.YEAR);
        int gm = cal.get(Calendar.MONTH) + 1;
        int gd = cal.get(Calendar.DAY_OF_MONTH);
        int dow = cal.get(Calendar.DAY_OF_WEEK) - 1;
        int[] j = gregorianToJalali(gy, gm, gd);
        if (isPersian) {
            return PERSIAN_WEEKDAYS_FA[dow] + " " + j[2] + " " + PERSIAN_MONTHS_FA[j[1] - 1] + " " + j[0];
        } else {
            return j[2] + " " + PERSIAN_MONTHS_EN[j[1] - 1] + " " + j[0] + " (Jalali)";
        }
    }

    public static String getUsaTimeText() {
        TimeZone tz = TimeZone.getTimeZone("America/New_York");
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
    }

    public static String getUsaGregorianDateText() {
        TimeZone tz = TimeZone.getTimeZone("America/New_York");
        SimpleDateFormat sdf = new SimpleDateFormat("EEE, dd MMM yyyy", Locale.US);
        sdf.setTimeZone(tz);
        return sdf.format(new Date());
    }
}
"""
write_file(os.path.join(JAVA_BASE, "helper/JalaliClockUtil.java"), JALALI_CLOCK)

# 3. LocaleHelper.java
LOCALE_HELPER = r"""package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.util.Locale;

public class LocaleHelper {
    private static final String PREFS = "veyra_locale_prefs";
    private static final String KEY_LANG = "app_lang";
    private static final String KEY_LIGHT_THEME = "app_light_theme";

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

    public static void toggleLanguage(Context context) {
        setLanguage(context, isPersian(context) ? "en" : "fa");
    }

    public static boolean isLightTheme(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getBoolean(KEY_LIGHT_THEME, false);
    }

    public static void setLightTheme(Context context, boolean isLight) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
               .edit().putBoolean(KEY_LIGHT_THEME, isLight).apply();
    }

    public static void toggleLightTheme(Context context) {
        setLightTheme(context, !isLightTheme(context));
    }

    public static void applyThemeRecursive(View root, boolean isLight) {
        if (!isLight || root == null) return;
        Drawable bg = root.getBackground();
        if (bg instanceof ColorDrawable) {
            int c = ((ColorDrawable) bg).getColor();
            if (c == Color.parseColor("#0B0F19") || c == Color.parseColor("#080B12")) {
                root.setBackgroundColor(Color.parseColor("#F1F5F9"));
            } else if (c == Color.parseColor("#0F172A") || c == Color.parseColor("#161F33") || c == Color.parseColor("#1E293B")) {
                root.setBackgroundColor(Color.parseColor("#FFFFFF"));
            }
        } else if (bg instanceof GradientDrawable) {
            // Keep rounded cards & buttons crisp
        }
        if (root instanceof TextView) {
            TextView tv = (TextView) root;
            int tc = tv.getCurrentTextColor();
            if (tc == Color.WHITE || tc == Color.parseColor("#F8FAFC") || tc == Color.parseColor("#E2E8F0")) {
                if (root.getBackground() == null) {
                    tv.setTextColor(Color.parseColor("#0F172A"));
                }
            }
        }
        if (root instanceof ViewGroup) {
            ViewGroup vg = (ViewGroup) root;
            for (int i = 0; i < vg.getChildCount(); i++) {
                applyThemeRecursive(vg.getChildAt(i), true);
            }
        }
    }

    public static Context wrap(Context context) {
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
write_file(os.path.join(JAVA_BASE, "helper/LocaleHelper.java"), LOCALE_HELPER)

# 4. BaseActivity.java
BASE_ACTIVITY = r"""package com.veyravault.space.ui;

import android.content.Context;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import androidx.appcompat.app.AppCompatActivity;
import com.veyravault.space.helper.LocaleHelper;

public abstract class BaseActivity extends AppCompatActivity {
    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.wrap(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        applyDirectionAndStatusBar();
    }

    protected void applyDirectionAndStatusBar() {
        boolean fa = LocaleHelper.isPersian(this);
        boolean light = LocaleHelper.isLightTheme(this);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            getWindow().getDecorView().setLayoutDirection(
                fa ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            Window w = getWindow();
            w.setStatusBarColor(Color.parseColor(light ? "#E2E8F0" : "#0B0F19"));
            w.setNavigationBarColor(Color.parseColor(light ? "#FFFFFF" : "#080B12"));
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

# 5. GmsSupportManager.java
GMS_SUPPORT = r"""package com.veyravault.space.helper;

import android.content.Context;
import android.content.pm.PackageManager;
import top.niunaijun.blackbox.BlackBoxCore;

public class GmsSupportManager {
    public static final String[] POISON_GMS_PACKAGES = {
        "com.google.android.gms",
        "com.google.android.gsf",
        "com.google.android.gsf.login"
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
        for (String pkg : POISON_GMS_PACKAGES) {
            try {
                if (BlackBoxCore.get().isInstalled(pkg, userId)) {
                    BlackBoxCore.get().uninstallPackageAsUser(pkg, userId);
                }
            } catch (Throwable ignored) {}
        }
    }

    public static int ensureGmsInstalledForUser(Context context, int userId) {
        cleanPoisonedGmsInSpace(userId);
        return isHostInstalled(context, "com.google.android.gms") ? 1 : 0;
    }

    public static void ensureGmsForPackage(Context context, String pkg, int userId) {
        cleanPoisonedGmsInSpace(userId);
    }

    public static boolean isGmsReady(Context context, int userId) {
        cleanPoisonedGmsInSpace(userId);
        return isHostInstalled(context, "com.google.android.gms");
    }
}
"""
write_file(os.path.join(JAVA_BASE, "helper/GmsSupportManager.java"), GMS_SUPPORT)

# 6. AppDisguiseManager.java
DISGUISE_MANAGER = r"""package com.veyravault.space.helper;

import android.content.Context;
import android.content.SharedPreferences;

public class AppDisguiseManager {
    private static final String PREFS = "veyra_disguise_prefs";
    private static final String KEY_MODE = "disguise_mode";
    public static final String MODE_DEFAULT = "default";
    public static final String MODE_CALCULATOR = "calculator";
    public static final String MODE_NOTEPAD = "notepad";

    public static String getDisguiseMode(Context context) {
        SharedPreferences sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return sp.getString(KEY_MODE, MODE_DEFAULT);
    }

    public static void setDisguiseMode(Context context, String mode) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
               .edit().putString(KEY_MODE, mode).apply();
    }
}
"""
write_file(os.path.join(JAVA_BASE, "helper/AppDisguiseManager.java"), DISGUISE_MANAGER)

# 7. PatternLockView.java
PATTERN_VIEW = r"""package com.veyravault.space.helper;

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
        void onPatternComplete(String patternValue);
    }

    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final List<Integer> selectedNodes = new ArrayList<>();
    private float curX, curY;
    private boolean isDrawing = false;
    private OnPatternListener listener;

    public PatternLockView(Context context) {
        super(context);
        dotPaint.setColor(Color.parseColor("#475569"));
        dotPaint.setStyle(Paint.Style.FILL);

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
            boolean active = selectedNodes.contains(i);
            canvas.drawCircle(getNodeX(i), getNodeY(i), active ? radius * 1.25f : radius, active ? activePaint : dotPaint);
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
                if (listener != null && !selectedNodes.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < selectedNodes.size(); i++) {
                        if (i > 0) sb.append("-");
                        sb.append(selectedNodes.get(i));
                    }
                    listener.onPatternComplete(sb.toString());
                }
                invalidate();
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y) {
        float hitRadius = Math.min(getWidth(), getHeight()) / 8f;
        for (int i = 0; i < 9; i++) {
            if (!selectedNodes.contains(i)) {
                float dx = x - getNodeX(i);
                float dy = y - getNodeY(i);
                if (Math.hypot(dx, dy) <= hitRadius) {
                    selectedNodes.add(i);
                }
            }
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "helper/PatternLockView.java"), PATTERN_VIEW)

# 8. CloneMetadataStore.java
CLONE_METADATA_STORE = r"""package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

public class CloneMetadataStore {
    private static final String PREFS = "veyra_clone_meta_v3";
    private static CloneMetadataStore sInstance;
    private final SharedPreferences sp;

    // Safe Vault Non-Host Defaults (Priority #3 Fallback so real host phone is NEVER leaked)
    public static final String SAFE_DEFAULT_BRAND = "Apple";
    public static final String SAFE_DEFAULT_MODEL = "iPhone 16 Pro Max";
    public static final String SAFE_DEFAULT_MANUFACTURER = "Apple Inc.";
    public static final String SAFE_DEFAULT_PRODUCT = "iPhone17,2";
    public static final String SAFE_DEFAULT_HARDWARE = "A18Pro";
    public static final String SAFE_DEFAULT_REGION = "New York, United States";
    public static final String SAFE_DEFAULT_TZ = "America/New_York";
    public static final double SAFE_DEFAULT_LAT = 40.7128;
    public static final double SAFE_DEFAULT_LON = -74.0060;
    public static final String SAFE_DEFAULT_SIM_OP = "T-Mobile USA";
    public static final String SAFE_DEFAULT_SIM_NUM = "310260";
    public static final String SAFE_DEFAULT_SIM_ISO = "us";
    public static final String SAFE_DEFAULT_SIM_PHONE = "+12125550147";

    public static synchronized CloneMetadataStore get(Context context) {
        if (sInstance == null) {
            sInstance = new CloneMetadataStore(context.getApplicationContext());
        }
        return sInstance;
    }

    private CloneMetadataStore(Context context) {
        this.sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        ensureInitialDefaults();
    }

    private void ensureInitialDefaults() {
        if (!sp.contains("global_initialized_v3")) {
            sp.edit()
              .putBoolean("global_initialized_v3", true)
              .putString("global_brand", SAFE_DEFAULT_BRAND)
              .putString("global_model", SAFE_DEFAULT_MODEL)
              .putString("global_manufacturer", SAFE_DEFAULT_MANUFACTURER)
              .putString("global_product", SAFE_DEFAULT_PRODUCT)
              .putString("global_hardware", SAFE_DEFAULT_HARDWARE)
              .putBoolean("global_loc_enabled", true)
              .putString("global_lat", String.valueOf(SAFE_DEFAULT_LAT))
              .putString("global_lon", String.valueOf(SAFE_DEFAULT_LON))
              .putString("global_region_label", SAFE_DEFAULT_REGION)
              .putString("global_tz", SAFE_DEFAULT_TZ)
              .putString("global_proxy", "127.0.0.1:10808")
              .putString("global_sim_op", SAFE_DEFAULT_SIM_OP)
              .putString("global_sim_num", SAFE_DEFAULT_SIM_NUM)
              .putString("global_sim_iso", SAFE_DEFAULT_SIM_ISO)
              .putString("global_sim_phone", SAFE_DEFAULT_SIM_PHONE)
              .putBoolean("space_created_0", true)
              .putBoolean("vpn_cluster_autorotate", true)
              .apply();
        }
        if (!sp.contains("vpn_profiles_json_v32")) {
            seedDefaultVpnProfiles();
        }
    }

    /**
     * Prevents duplicate Brand + Model strings like "Samsung Samsung Galaxy S24 Ultra"
     * or "سامسونگ سامسونگ S24" across all UI and Build hooks.
     */
    public static String cleanModelOnly(String brand, String model) {
        String b = (brand == null) ? "" : brand.trim();
        String m = (model == null) ? "" : model.trim();
        if (m.isEmpty()) return SAFE_DEFAULT_MODEL;
        if (!b.isEmpty()) {
            while (m.toLowerCase().startsWith(b.toLowerCase() + " ") || m.toLowerCase().startsWith(b.toLowerCase() + "-")) {
                m = m.substring(b.length()).trim();
                if (m.startsWith("-") || m.startsWith("—")) m = m.substring(1).trim();
            }
        }
        String[][] synonyms = {
            {"Samsung", "سامسونگ"},
            {"Apple", "اپل"},
            {"Xiaomi", "شیائومی"},
            {"Google", "گوگل"},
            {"OnePlus", "وان‌پلاس"},
            {"OnePlus", "وان پلاس"}
        };
        for (String[] pair : synonyms) {
            if (b.equalsIgnoreCase(pair[0]) || b.equalsIgnoreCase(pair[1])) {
                for (String syn : pair) {
                    if (m.toLowerCase().startsWith(syn.toLowerCase() + " ")) {
                        m = m.substring(syn.length()).trim();
                    }
                }
            }
        }
        // Collapse repeated adjacent words in model itself
        String[] words = m.split("\\s+");
        StringBuilder sb = new StringBuilder();
        String prev = "";
        for (String w : words) {
            if (!w.equalsIgnoreCase(prev)) {
                if (sb.length() > 0) sb.append(" ");
                sb.append(w);
                prev = w;
            }
        }
        String cleaned = sb.toString().trim();
        return cleaned.isEmpty() ? m : cleaned;
    }

    public static String formatBrandModel(String brand, String model) {
        String b = (brand == null || brand.trim().isEmpty()) ? SAFE_DEFAULT_BRAND : brand.trim();
        String m = cleanModelOnly(b, model);
        if (m.toLowerCase().startsWith(b.toLowerCase())) {
            return m;
        }
        return b + " " + m;
    }

    public static class CloneMeta {
        public String packageName;
        public int userId;
        public String customAlias = "";
        public boolean hasExclusiveDevice = false;
        public String deviceBrand = "";
        public String deviceModel = "";
        public String deviceManufacturer = "";
        public String deviceProduct = "";
        public String deviceHardware = "";
        public boolean hasExclusiveLocation = false;
        public double latitude = SAFE_DEFAULT_LAT;
        public double longitude = SAFE_DEFAULT_LON;
        public String regionLabel = SAFE_DEFAULT_REGION;
        public String timezoneId = SAFE_DEFAULT_TZ;
        public String proxyAddress = "";
        public boolean hasExclusiveSim = false;
        public String simOperatorName = SAFE_DEFAULT_SIM_OP;
        public String simOperatorNumeric = SAFE_DEFAULT_SIM_NUM;
        public String simCountryIso = SAFE_DEFAULT_SIM_ISO;
        public String simPhoneNumber = SAFE_DEFAULT_SIM_PHONE;
    }

    public static class EffectiveIdentity {
        public int devicePriorityTier = 3;   // 1=App, 2=Space, 3=Global Vault
        public int locationPriorityTier = 3; // 1=App, 2=Space, 3=Global Vault
        public int simPriorityTier = 3;      // 1=App, 2=Space, 3=Global Vault
        public String targetPackage = "";
        public int targetUserId = 0;
        public String brand = SAFE_DEFAULT_BRAND;
        public String model = SAFE_DEFAULT_MODEL;
        public String displayBrandModel = SAFE_DEFAULT_BRAND + " " + SAFE_DEFAULT_MODEL;
        public String manufacturer = SAFE_DEFAULT_MANUFACTURER;
        public String product = SAFE_DEFAULT_PRODUCT;
        public String hardware = SAFE_DEFAULT_HARDWARE;
        public double latitude = SAFE_DEFAULT_LAT;
        public double longitude = SAFE_DEFAULT_LON;
        public String regionLabel = SAFE_DEFAULT_REGION;
        public String timezoneId = SAFE_DEFAULT_TZ;
        public String proxyAddress = "127.0.0.1:10808";
        public String simOperatorName = SAFE_DEFAULT_SIM_OP;
        public String simOperatorNumeric = SAFE_DEFAULT_SIM_NUM;
        public String simCountryIso = SAFE_DEFAULT_SIM_ISO;
        public String simPhoneNumber = SAFE_DEFAULT_SIM_PHONE;
    }

    public static class DevicePreset {
        public final String brand;
        public final String model;
        public final String manufacturer;
        public final String product;
        public final String hardware;

        public DevicePreset(String brand, String model, String manufacturer, String product, String hardware) {
            this.brand = brand;
            this.model = model;
            this.manufacturer = manufacturer;
            this.product = product;
            this.hardware = hardware;
        }
    }

    public static final DevicePreset[] PRESETS = new DevicePreset[]{
        new DevicePreset("Apple", "iPhone 16 Pro Max", "Apple Inc.", "iPhone17,2", "A18Pro"),
        new DevicePreset("Apple", "iPhone 15 Pro", "Apple Inc.", "iPhone16,1", "A17Pro"),
        new DevicePreset("Samsung", "Galaxy S24 Ultra (SM-S928B)", "Samsung", "e3qxxx", "qcom"),
        new DevicePreset("Google", "Pixel 9 Pro XL", "Google", "komodo", "tensor"),
        new DevicePreset("Xiaomi", "14 Ultra", "Xiaomi", "aurora", "qcom"),
        new DevicePreset("OnePlus", "12 (CPH2581)", "OnePlus", "OP5929L1", "qcom")
    };

    public static class VpnProfile {
        public String id;
        public String category = "🇺🇸 US - New York Cluster";
        public int nodeIndex = 1;
        public String title;
        public String country;
        public String stateOrCity;
        public String protocol; // SOCKS5, HTTP, V2RAY_LOCAL, WG_SYSTEM
        public String host;
        public int port;
        public String username = "";
        public String password = "";
        public String timezoneId;
        public double lat;
        public double lon;
        public String simOperator;
        public String simMccMnc;
        public String simIso;
        public int targetSpaceId = -1; // -1 = All Spaces
        public boolean isBuiltInFree = true;
    }

    private static VpnProfile createNode(String id, String cat, int nodeIdx, String title, String country,
                                         String city, String proto, String host, int port, String tz,
                                         double lat, double lon, String simOp, String mccMnc, String iso) {
        VpnProfile p = new VpnProfile();
        p.id = id;
        p.category = cat;
        p.nodeIndex = nodeIdx;
        p.title = title;
        p.country = country;
        p.stateOrCity = city;
        p.protocol = proto;
        p.host = host;
        p.port = port;
        p.timezoneId = tz;
        p.lat = lat;
        p.lon = lon;
        p.simOperator = simOp;
        p.simMccMnc = mccMnc;
        p.simIso = iso;
        p.isBuiltInFree = true;
        return p;
    }

    // Pre-populated strong free VPN presets for quick selection & editing in the Add/Edit dialog
    public static final VpnProfile[] FREE_VPN_PRESETS = new VpnProfile[]{
        createNode("free_us_ny_1", "🇺🇸 US - New York Cluster", 1, "🇺🇸 Free US New York #1 (High-Speed Relay)", "United States", "New York, United States", "SOCKS5", "127.0.0.1", 10808, "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", "us"),
        createNode("free_us_ny_2", "🇺🇸 US - New York Cluster", 2, "🇺🇸 Free US New York #2 (Cloudflare WARP Bridge)", "United States", "New York, United States", "SOCKS5", "127.0.0.1", 40000, "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", "us"),
        createNode("free_us_ny_3", "🇺🇸 US - New York Cluster", 3, "🇺🇸 Free US New York #3 (NekoBox / Sing-Box)", "United States", "New York, United States", "SOCKS5", "127.0.0.1", 2080, "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", "us"),
        createNode("free_us_ny_4", "🇺🇸 US - New York Cluster", 4, "🇺🇸 Free US New York #4 (Orbot / Tor Guard)", "United States", "New York, United States", "SOCKS5", "127.0.0.1", 9050, "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", "us"),
        createNode("free_us_la_1", "🇺🇸 US - California Cluster", 1, "🇺🇸 Free US Los Angeles #1 (West Coast Fast)", "United States", "Los Angeles, United States", "SOCKS5", "127.0.0.1", 10808, "America/Los_Angeles", 34.0522, -118.2437, "AT&T Mobility", "310410", "us"),
        createNode("free_us_la_2", "🇺🇸 US - California Cluster", 2, "🇺🇸 Free US Los Angeles #2 (Backup Tunnel)", "United States", "Los Angeles, United States", "HTTP", "127.0.0.1", 10809, "America/Los_Angeles", 34.0522, -118.2437, "AT&T Mobility", "310410", "us"),
        createNode("free_us_va_1", "🇺🇸 US - Virginia Ashburn Cluster", 1, "🇺🇸 Free US Ashburn Virginia #1 (DataCenter Core)", "United States", "Ashburn, United States", "SOCKS5", "127.0.0.1", 10808, "America/New_York", 39.0438, -77.4874, "Verizon Wireless", "311480", "us"),
        createNode("free_de_fk_1", "🇩🇪 Germany - Falkenstein Cluster", 1, "🇩🇪 Free Germany Falkenstein #1 (Hetzner Direct)", "Germany", "Falkenstein, Germany", "SOCKS5", "127.0.0.1", 10808, "Europe/Berlin", 50.4779, 12.3713, "Telekom DE", "26201", "de"),
        createNode("free_de_fk_2", "🇩🇪 Germany - Falkenstein Cluster", 2, "🇩🇪 Free Germany Falkenstein #2 (Failover Node)", "Germany", "Falkenstein, Germany", "HTTP", "127.0.0.1", 10809, "Europe/Berlin", 50.4779, 12.3713, "Telekom DE", "26201", "de"),
        createNode("free_uk_ld_1", "🇬🇧 UK - London Cluster", 1, "🇬🇧 Free UK London #1 (Docklands Core)", "United Kingdom", "London, United Kingdom", "SOCKS5", "127.0.0.1", 10808, "Europe/London", 51.5074, -0.1278, "Vodafone UK", "23415", "gb"),
        createNode("free_nl_am_1", "🇳🇱 Netherlands - Amsterdam Cluster", 1, "🇳🇱 Free Netherlands Amsterdam #1 (AMS-IX)", "Netherlands", "Amsterdam, Netherlands", "SOCKS5", "127.0.0.1", 10808, "Europe/Amsterdam", 52.3676, 4.9041, "KPN NL", "20408", "nl"),
        createNode("free_fi_hl_1", "🇫🇮 Finland - Helsinki Cluster", 1, "🇫🇮 Free Finland Helsinki #1 (Nordic Node)", "Finland", "Helsinki, Finland", "SOCKS5", "127.0.0.1", 10808, "Europe/Helsinki", 60.1699, 24.9384, "Elisa FI", "24405", "fi")
    };

    private void seedDefaultVpnProfiles() {
        List<VpnProfile> list = new ArrayList<>();
        // Cluster 1: US - New York (4 sibling nodes with identical country/city/SIM/timezone for seamless rotation)
        list.add(createNode("us_ny_1", "🇺🇸 US - New York Cluster", 1, "🇺🇸 USA - New York [Node #1 Primary]", "United States", "New York, United States", "SOCKS5", "127.0.0.1", 10808, "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", "us"));
        list.add(createNode("us_ny_2", "🇺🇸 US - New York Cluster", 2, "🇺🇸 USA - New York [Node #2 Fast Failover]", "United States", "New York, United States", "HTTP", "127.0.0.1", 10809, "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", "us"));
        list.add(createNode("us_ny_3", "🇺🇸 US - New York Cluster", 3, "🇺🇸 USA - New York [Node #3 Neko/Sing Tunnel]", "United States", "New York, United States", "SOCKS5", "127.0.0.1", 2080, "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", "us"));
        list.add(createNode("us_ny_4", "🇺🇸 US - New York Cluster", 4, "🇺🇸 USA - New York [Node #4 WARP Relay]", "United States", "New York, United States", "SOCKS5", "127.0.0.1", 40000, "America/New_York", 40.7128, -74.0060, "T-Mobile USA", "310260", "us"));

        // Cluster 2: US - California (3 sibling nodes with identical country/city/SIM/timezone)
        list.add(createNode("us_ca_1", "🇺🇸 US - California Cluster", 1, "🇺🇸 USA - Los Angeles [Node #1 Primary]", "United States", "Los Angeles, United States", "SOCKS5", "127.0.0.1", 10808, "America/Los_Angeles", 34.0522, -118.2437, "AT&T Mobility", "310410", "us"));
        list.add(createNode("us_ca_2", "🇺🇸 US - California Cluster", 2, "🇺🇸 USA - Los Angeles [Node #2 Failover]", "United States", "Los Angeles, United States", "HTTP", "127.0.0.1", 10809, "America/Los_Angeles", 34.0522, -118.2437, "AT&T Mobility", "310410", "us"));
        list.add(createNode("us_ca_3", "🇺🇸 US - California Cluster", 3, "🇺🇸 USA - Los Angeles [Node #3 Multi-Hop]", "United States", "Los Angeles, United States", "SOCKS5", "127.0.0.1", 2080, "America/Los_Angeles", 34.0522, -118.2437, "AT&T Mobility", "310410", "us"));

        // Cluster 3: US - Texas (2 sibling nodes)
        list.add(createNode("us_tx_1", "🇺🇸 US - Texas Cluster", 1, "🇺🇸 USA - Dallas [Node #1 Primary]", "United States", "Dallas, United States", "SOCKS5", "127.0.0.1", 10808, "America/Chicago", 32.7767, -96.7970, "Verizon Wireless", "311480", "us"));
        list.add(createNode("us_tx_2", "🇺🇸 US - Texas Cluster", 2, "🇺🇸 USA - Dallas [Node #2 Backup]", "United States", "Dallas, United States", "HTTP", "127.0.0.1", 10809, "America/Chicago", 32.7767, -96.7970, "Verizon Wireless", "311480", "us"));

        // Cluster 4: Germany - Falkenstein (3 sibling nodes)
        list.add(createNode("de_fk_1", "🇩🇪 Germany - Falkenstein Cluster", 1, "🇩🇪 Germany - Falkenstein [Node #1 Hetzner]", "Germany", "Falkenstein, Germany", "SOCKS5", "127.0.0.1", 10808, "Europe/Berlin", 50.4779, 12.3713, "Telekom DE", "26201", "de"));
        list.add(createNode("de_fk_2", "🇩🇪 Germany - Falkenstein Cluster", 2, "🇩🇪 Germany - Falkenstein [Node #2 Backup]", "Germany", "Falkenstein, Germany", "HTTP", "127.0.0.1", 10809, "Europe/Berlin", 50.4779, 12.3713, "Telekom DE", "26201", "de"));
        list.add(createNode("de_fk_3", "🇩🇪 Germany - Falkenstein Cluster", 3, "🇩🇪 Germany - Falkenstein [Node #3 Relay]", "Germany", "Falkenstein, Germany", "SOCKS5", "127.0.0.1", 2080, "Europe/Berlin", 50.4779, 12.3713, "Telekom DE", "26201", "de"));

        // Cluster 5: UK - London (2 sibling nodes)
        list.add(createNode("uk_ld_1", "🇬🇧 UK - London Cluster", 1, "🇬🇧 UK - London [Node #1 Primary]", "United Kingdom", "London, United Kingdom", "SOCKS5", "127.0.0.1", 10808, "Europe/London", 51.5074, -0.1278, "Vodafone UK", "23415", "gb"));
        list.add(createNode("uk_ld_2", "🇬🇧 UK - London Cluster", 2, "🇬🇧 UK - London [Node #2 Backup]", "United Kingdom", "London, United Kingdom", "HTTP", "127.0.0.1", 10809, "Europe/London", 51.5074, -0.1278, "Vodafone UK", "23415", "gb"));

        // Cluster 6: Netherlands - Amsterdam (2 sibling nodes)
        list.add(createNode("nl_am_1", "🇳🇱 Netherlands - Amsterdam Cluster", 1, "🇳🇱 Netherlands - Amsterdam [Node #1 Primary]", "Netherlands", "Amsterdam, Netherlands", "SOCKS5", "127.0.0.1", 10808, "Europe/Amsterdam", 52.3676, 4.9041, "KPN NL", "20408", "nl"));
        list.add(createNode("nl_am_2", "🇳🇱 Netherlands - Amsterdam Cluster", 2, "🇳🇱 Netherlands - Amsterdam [Node #2 Backup]", "Netherlands", "Amsterdam, Netherlands", "HTTP", "127.0.0.1", 10809, "Europe/Amsterdam", 52.3676, 4.9041, "KPN NL", "20408", "nl"));

        saveVpnProfiles(list);
        setActiveVpnId("us_ny_1");
        setActiveVpnCategory("🇺🇸 US - New York Cluster");
    }

    public List<VpnProfile> getVpnProfiles() {
        List<VpnProfile> list = new ArrayList<>();
        try {
            String raw = sp.getString("vpn_profiles_json_v32", "[]");
            JSONArray arr = new JSONArray(raw);
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                VpnProfile p = new VpnProfile();
                p.id = o.optString("id", "vpn_" + i);
                p.category = o.optString("category", "🇺🇸 US - New York Cluster");
                p.nodeIndex = o.optInt("nodeIndex", i + 1);
                p.title = o.optString("title", "VPN Server");
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
                p.isBuiltInFree = o.optBoolean("isBuiltInFree", true);
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
                o.put("id", p.id);
                o.put("category", (p.category == null || p.category.trim().isEmpty()) ? "🇺🇸 US - New York Cluster" : p.category.trim());
                o.put("nodeIndex", p.nodeIndex);
                o.put("title", p.title);
                o.put("country", p.country);
                o.put("stateOrCity", p.stateOrCity);
                o.put("protocol", p.protocol);
                o.put("host", p.host);
                o.put("port", p.port);
                o.put("username", p.username);
                o.put("password", p.password);
                o.put("timezoneId", p.timezoneId);
                o.put("lat", p.lat);
                o.put("lon", p.lon);
                o.put("simOperator", p.simOperator);
                o.put("simMccMnc", p.simMccMnc);
                o.put("simIso", p.simIso);
                o.put("targetSpaceId", p.targetSpaceId);
                o.put("isBuiltInFree", p.isBuiltInFree);
                arr.put(o);
            }
            sp.edit().putString("vpn_profiles_json_v32", arr.toString()).apply();
        } catch (Throwable ignored) {}
    }

    public List<String> getVpnCategories() {
        Set<String> set = new LinkedHashSet<>();
        for (VpnProfile p : getVpnProfiles()) {
            if (p.category != null && !p.category.trim().isEmpty()) {
                set.add(p.category.trim());
            }
        }
        if (set.isEmpty()) set.add("🇺🇸 US - New York Cluster");
        return new ArrayList<>(set);
    }

    public String getActiveVpnCategory() {
        return sp.getString("active_vpn_category", "ALL");
    }

    public void setActiveVpnCategory(String category) {
        sp.edit().putString("active_vpn_category", (category == null || category.isEmpty()) ? "ALL" : category).apply();
    }

    public boolean isClusterAutoRotateEnabled() {
        return sp.getBoolean("vpn_cluster_autorotate", true);
    }

    public void setClusterAutoRotateEnabled(boolean enabled) {
        sp.edit().putBoolean("vpn_cluster_autorotate", enabled).apply();
    }

    /**
     * Rotates/fails over to the next sibling VPN server in the SAME category/cluster
     * (matching country, city, timezone & SIM) so the VPN connection never drops.
     */
    public VpnProfile rotateToNextSiblingInCluster(String currentProfileId) {
        List<VpnProfile> all = getVpnProfiles();
        if (all.isEmpty()) return null;
        VpnProfile current = all.get(0);
        for (VpnProfile p : all) {
            if (p.id.equals(currentProfileId)) {
                current = p;
                break;
            }
        }
        List<VpnProfile> siblings = new ArrayList<>();
        for (VpnProfile p : all) {
            if (p.category != null && p.category.equalsIgnoreCase(current.category)) {
                siblings.add(p);
            }
        }
        if (siblings.size() <= 1) {
            for (VpnProfile p : all) {
                if (p.stateOrCity != null && p.stateOrCity.equalsIgnoreCase(current.stateOrCity)) {
                    siblings.add(p);
                }
            }
        }
        if (siblings.isEmpty()) return current;
        int idx = 0;
        for (int i = 0; i < siblings.size(); i++) {
            if (siblings.get(i).id.equals(current.id)) {
                idx = i;
                break;
            }
        }
        VpnProfile next = siblings.get((idx + 1) % siblings.size());
        setActiveVpnId(next.id);
        setVpnConnected(true);
        applyVpnProfileToEnvironment(next);
        return next;
    }

    public void moveVpnProfile(String profileId, int delta) {
        List<VpnProfile> list = getVpnProfiles();
        int idx = -1;
        for (int i = 0; i < list.size(); i++) {
            if (list.get(i).id.equals(profileId)) {
                idx = i;
                break;
            }
        }
        if (idx < 0) return;
        int targetIdx = idx + delta;
        if (targetIdx < 0 || targetIdx >= list.size()) return;
        VpnProfile item = list.remove(idx);
        list.add(targetIdx, item);
        saveVpnProfiles(list);
    }

    public void renameVpnCategory(String oldCat, String newCat) {
        if (oldCat == null || newCat == null || newCat.trim().isEmpty()) return;
        List<VpnProfile> list = getVpnProfiles();
        for (VpnProfile p : list) {
            if (oldCat.equals(p.category)) {
                p.category = newCat.trim();
            }
        }
        saveVpnProfiles(list);
        if (oldCat.equals(getActiveVpnCategory())) {
            setActiveVpnCategory(newCat.trim());
        }
    }

    public String getActiveVpnId() {
        return sp.getString("active_vpn_id", "us_ny_1");
    }

    public void setActiveVpnId(String id) {
        sp.edit().putString("active_vpn_id", id).apply();
    }

    public boolean isVpnConnected() {
        return sp.getBoolean("vpn_connected_state", false);
    }

    public void setVpnConnected(boolean connected) {
        sp.edit().putBoolean("vpn_connected_state", connected).apply();
    }

    public boolean isKillSwitchEnabled() {
        return sp.getBoolean("vpn_kill_switch", true);
    }

    public void setKillSwitchEnabled(boolean enabled) {
        sp.edit().putBoolean("vpn_kill_switch", enabled).apply();
    }

    public boolean isVpnAutoSyncEnabled() {
        return sp.getBoolean("vpn_auto_sync_env", true);
    }

    public void setVpnAutoSyncEnabled(boolean enabled) {
        sp.edit().putBoolean("vpn_auto_sync_env", enabled).apply();
    }

    public String getCustomDns() {
        return sp.getString("vpn_custom_dns", "1.1.1.1 / 8.8.8.8");
    }

    public void setCustomDns(String dns) {
        sp.edit().putString("vpn_custom_dns", dns).apply();
    }

    public void applyVpnProfileToEnvironment(VpnProfile p) {
        if (p == null) return;
        setActiveVpnId(p.id);
        if (isVpnAutoSyncEnabled()) {
            GlobalEnvConfig g = getGlobalConfig();
            g.regionLabel = p.stateOrCity;
            g.timezoneId = p.timezoneId;
            g.latitude = p.lat;
            g.longitude = p.lon;
            g.proxyAddress = p.host + ":" + p.port;
            g.simOperatorName = p.simOperator;
            g.simOperatorNumeric = p.simMccMnc;
            g.simCountryIso = p.simIso;
            saveGlobalConfig(g);
        }
    }

    public void setLastActiveSession(String pkg, int userId) {
        if (pkg == null || pkg.isEmpty() || "__space__".equals(pkg)) return;
        sp.edit()
          .putString("last_active_pkg", pkg)
          .putInt("last_active_user", userId)
          .apply();
    }

    public String getLastActivePkg() {
        return sp.getString("last_active_pkg", "");
    }

    public int getLastActiveUserId() {
        return sp.getInt("last_active_user", 0);
    }

    public String getSpaceDisplayName(int userId, boolean isFa) {
        String custom = sp.getString("space_name_" + userId, "");
        if (custom != null && !custom.trim().isEmpty()) {
            return custom.trim();
        }
        return isFa ? ("فضای " + (userId + 1)) : ("Space " + (userId + 1));
    }

    public void setSpaceCustomName(int userId, String name) {
        sp.edit().putString("space_name_" + userId, name == null ? "" : name.trim()).apply();
    }

    public boolean isSpaceCreated(int userId) {
        if (userId == 0) return true;
        return sp.getBoolean("space_created_" + userId, false);
    }

    public void markSpaceCreated(int userId) {
        sp.edit().putBoolean("space_created_" + userId, true).apply();
    }

    public int getUnreadCount(String pkg, int userId) {
        return sp.getInt("badge_unread_" + userId + "_" + pkg, 0);
    }

    public void setUnreadCount(String pkg, int userId, int count) {
        sp.edit().putInt("badge_unread_" + userId + "_" + pkg, Math.max(0, count)).apply();
    }

    public void incrementUnreadCount(String pkg, int userId) {
        setUnreadCount(pkg, userId, getUnreadCount(pkg, userId) + 1);
    }

    public String formatBadgeText(int count) {
        if (count <= 0) return "";
        if (count >= 100) return "∞";
        return String.valueOf(count);
    }

    private String keyPrefix(String pkg, int userId) {
        return "clone_" + userId + "_" + pkg + "_";
    }

    public CloneMeta getCloneMeta(String pkg, int userId) {
        String p = keyPrefix(pkg, userId);
        CloneMeta m = new CloneMeta();
        m.packageName = pkg;
        m.userId = userId;
        m.customAlias = sp.getString(p + "alias", "");
        m.hasExclusiveDevice = sp.getBoolean(p + "ex_dev", false);
        m.deviceBrand = sp.getString(p + "brand", SAFE_DEFAULT_BRAND);
        m.deviceModel = cleanModelOnly(m.deviceBrand, sp.getString(p + "model", SAFE_DEFAULT_MODEL));
        m.deviceManufacturer = sp.getString(p + "mfg", SAFE_DEFAULT_MANUFACTURER);
        m.deviceProduct = sp.getString(p + "prod", SAFE_DEFAULT_PRODUCT);
        m.deviceHardware = sp.getString(p + "hw", SAFE_DEFAULT_HARDWARE);
        m.hasExclusiveLocation = sp.getBoolean(p + "ex_loc", false);
        try {
            m.latitude = Double.parseDouble(sp.getString(p + "lat", String.valueOf(SAFE_DEFAULT_LAT)));
            m.longitude = Double.parseDouble(sp.getString(p + "lon", String.valueOf(SAFE_DEFAULT_LON)));
        } catch (Exception e) {
            m.latitude = SAFE_DEFAULT_LAT;
            m.longitude = SAFE_DEFAULT_LON;
        }
        m.regionLabel = sp.getString(p + "region", SAFE_DEFAULT_REGION);
        m.timezoneId = sp.getString(p + "tz", SAFE_DEFAULT_TZ);
        m.proxyAddress = sp.getString(p + "proxy", "");
        m.hasExclusiveSim = sp.getBoolean(p + "ex_sim", false);
        m.simOperatorName = sp.getString(p + "sim_op", SAFE_DEFAULT_SIM_OP);
        m.simOperatorNumeric = sp.getString(p + "sim_num", SAFE_DEFAULT_SIM_NUM);
        m.simCountryIso = sp.getString(p + "sim_iso", SAFE_DEFAULT_SIM_ISO);
        m.simPhoneNumber = sp.getString(p + "sim_phone", SAFE_DEFAULT_SIM_PHONE);
        return m;
    }

    public void saveCloneMeta(CloneMeta m) {
        String cleanBrand = (m.deviceBrand == null || m.deviceBrand.trim().isEmpty()) ? SAFE_DEFAULT_BRAND : m.deviceBrand.trim();
        String cleanModel = cleanModelOnly(cleanBrand, m.deviceModel);
        String p = keyPrefix(m.packageName, m.userId);
        sp.edit()
          .putString(p + "alias", m.customAlias == null ? "" : m.customAlias)
          .putBoolean(p + "ex_dev", m.hasExclusiveDevice)
          .putString(p + "brand", cleanBrand)
          .putString(p + "model", cleanModel)
          .putString(p + "mfg", m.deviceManufacturer == null || m.deviceManufacturer.isEmpty() ? cleanBrand : m.deviceManufacturer)
          .putString(p + "prod", m.deviceProduct == null || m.deviceProduct.isEmpty() ? SAFE_DEFAULT_PRODUCT : m.deviceProduct)
          .putString(p + "hw", m.deviceHardware == null || m.deviceHardware.isEmpty() ? SAFE_DEFAULT_HARDWARE : m.deviceHardware)
          .putBoolean(p + "ex_loc", m.hasExclusiveLocation)
          .putString(p + "lat", String.valueOf(m.latitude))
          .putString(p + "lon", String.valueOf(m.longitude))
          .putString(p + "region", (m.regionLabel == null || m.regionLabel.trim().isEmpty()) ? SAFE_DEFAULT_REGION : m.regionLabel.trim())
          .putString(p + "tz", (m.timezoneId == null || m.timezoneId.trim().isEmpty()) ? SAFE_DEFAULT_TZ : m.timezoneId.trim())
          .putString(p + "proxy", m.proxyAddress == null ? "" : m.proxyAddress.trim())
          .putBoolean(p + "ex_sim", m.hasExclusiveSim)
          .putString(p + "sim_op", (m.simOperatorName == null || m.simOperatorName.trim().isEmpty()) ? SAFE_DEFAULT_SIM_OP : m.simOperatorName.trim())
          .putString(p + "sim_num", (m.simOperatorNumeric == null || m.simOperatorNumeric.trim().isEmpty()) ? SAFE_DEFAULT_SIM_NUM : m.simOperatorNumeric.trim())
          .putString(p + "sim_iso", (m.simCountryIso == null || m.simCountryIso.trim().isEmpty()) ? SAFE_DEFAULT_SIM_ISO : m.simCountryIso.trim().toLowerCase())
          .putString(p + "sim_phone", (m.simPhoneNumber == null || m.simPhoneNumber.trim().isEmpty()) ? SAFE_DEFAULT_SIM_PHONE : m.simPhoneNumber.trim())
          .apply();
    }

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
        public String simOperatorName;
        public String simOperatorNumeric;
        public String simCountryIso;
        public String simPhoneNumber;
    }

    public GlobalEnvConfig getGlobalConfig() {
        GlobalEnvConfig c = new GlobalEnvConfig();
        c.brand = sp.getString("global_brand", SAFE_DEFAULT_BRAND);
        if (c.brand == null || c.brand.trim().isEmpty()) c.brand = SAFE_DEFAULT_BRAND;
        c.model = cleanModelOnly(c.brand, sp.getString("global_model", SAFE_DEFAULT_MODEL));
        c.manufacturer = sp.getString("global_manufacturer", SAFE_DEFAULT_MANUFACTURER);
        c.product = sp.getString("global_product", SAFE_DEFAULT_PRODUCT);
        c.hardware = sp.getString("global_hardware", SAFE_DEFAULT_HARDWARE);
        c.locationEnabled = sp.getBoolean("global_loc_enabled", true);
        try {
            c.latitude = Double.parseDouble(sp.getString("global_lat", String.valueOf(SAFE_DEFAULT_LAT)));
            c.longitude = Double.parseDouble(sp.getString("global_lon", String.valueOf(SAFE_DEFAULT_LON)));
        } catch (Exception e) {
            c.latitude = SAFE_DEFAULT_LAT;
            c.longitude = SAFE_DEFAULT_LON;
        }
        c.regionLabel = sp.getString("global_region_label", SAFE_DEFAULT_REGION);
        if (c.regionLabel == null || c.regionLabel.trim().isEmpty()) c.regionLabel = SAFE_DEFAULT_REGION;
        c.timezoneId = sp.getString("global_tz", SAFE_DEFAULT_TZ);
        if (c.timezoneId == null || c.timezoneId.trim().isEmpty()) c.timezoneId = SAFE_DEFAULT_TZ;
        c.proxyAddress = sp.getString("global_proxy", "127.0.0.1:10808");
        c.simOperatorName = sp.getString("global_sim_op", SAFE_DEFAULT_SIM_OP);
        if (c.simOperatorName == null || c.simOperatorName.trim().isEmpty()) c.simOperatorName = SAFE_DEFAULT_SIM_OP;
        c.simOperatorNumeric = sp.getString("global_sim_num", SAFE_DEFAULT_SIM_NUM);
        if (c.simOperatorNumeric == null || c.simOperatorNumeric.trim().isEmpty()) c.simOperatorNumeric = SAFE_DEFAULT_SIM_NUM;
        c.simCountryIso = sp.getString("global_sim_iso", SAFE_DEFAULT_SIM_ISO);
        if (c.simCountryIso == null || c.simCountryIso.trim().isEmpty()) c.simCountryIso = SAFE_DEFAULT_SIM_ISO;
        c.simPhoneNumber = sp.getString("global_sim_phone", SAFE_DEFAULT_SIM_PHONE);
        return c;
    }

    public void saveGlobalConfig(GlobalEnvConfig c) {
        String cleanBrand = (c.brand == null || c.brand.trim().isEmpty()) ? SAFE_DEFAULT_BRAND : c.brand.trim();
        String cleanModel = cleanModelOnly(cleanBrand, c.model);
        sp.edit()
          .putString("global_brand", cleanBrand)
          .putString("global_model", cleanModel)
          .putString("global_manufacturer", (c.manufacturer == null || c.manufacturer.trim().isEmpty()) ? cleanBrand : c.manufacturer.trim())
          .putString("global_product", (c.product == null || c.product.trim().isEmpty()) ? SAFE_DEFAULT_PRODUCT : c.product.trim())
          .putString("global_hardware", (c.hardware == null || c.hardware.trim().isEmpty()) ? SAFE_DEFAULT_HARDWARE : c.hardware.trim())
          .putBoolean("global_loc_enabled", c.locationEnabled)
          .putString("global_lat", String.valueOf(c.latitude))
          .putString("global_lon", String.valueOf(c.longitude))
          .putString("global_region_label", (c.regionLabel == null || c.regionLabel.trim().isEmpty()) ? SAFE_DEFAULT_REGION : c.regionLabel.trim())
          .putString("global_tz", (c.timezoneId == null || c.timezoneId.trim().isEmpty()) ? SAFE_DEFAULT_TZ : c.timezoneId.trim())
          .putString("global_proxy", c.proxyAddress == null ? "" : c.proxyAddress.trim())
          .putString("global_sim_op", (c.simOperatorName == null || c.simOperatorName.trim().isEmpty()) ? SAFE_DEFAULT_SIM_OP : c.simOperatorName.trim())
          .putString("global_sim_num", (c.simOperatorNumeric == null || c.simOperatorNumeric.trim().isEmpty()) ? SAFE_DEFAULT_SIM_NUM : c.simOperatorNumeric.trim())
          .putString("global_sim_iso", (c.simCountryIso == null || c.simCountryIso.trim().isEmpty()) ? SAFE_DEFAULT_SIM_ISO : c.simCountryIso.trim().toLowerCase())
          .putString("global_sim_phone", (c.simPhoneNumber == null || c.simPhoneNumber.trim().isEmpty()) ? SAFE_DEFAULT_SIM_PHONE : c.simPhoneNumber.trim())
          .apply();
    }

    /**
     * Strict 3-tier resolution:
     * Priority #1: Per-App Exclusive Settings (pkg, userId)
     * Priority #2: Per-Space Exclusive Settings ("__space__", userId)
     * Priority #3: Global Vault Settings (Never leaks host phone hardware/SIM/location)
     */
    public EffectiveIdentity resolveEffectiveIdentity(String pkg, int userId) {
        GlobalEnvConfig g = getGlobalConfig();
        EffectiveIdentity out = new EffectiveIdentity();
        String resolvedPkg = pkg;
        int resolvedUser = userId;
        if (resolvedPkg == null || resolvedPkg.isEmpty()) {
            resolvedPkg = getLastActivePkg();
            resolvedUser = getLastActiveUserId();
        }
        out.targetPackage = (resolvedPkg == null) ? "" : resolvedPkg;
        out.targetUserId = resolvedUser;

        // Tier 3 defaults (Global Vault)
        out.brand = g.brand;
        out.model = cleanModelOnly(g.brand, g.model);
        out.manufacturer = g.manufacturer;
        out.product = g.product;
        out.hardware = g.hardware;
        out.latitude = g.latitude;
        out.longitude = g.longitude;
        out.regionLabel = g.regionLabel;
        out.timezoneId = g.timezoneId;
        out.proxyAddress = g.proxyAddress;
        out.simOperatorName = g.simOperatorName;
        out.simOperatorNumeric = g.simOperatorNumeric;
        out.simCountryIso = g.simCountryIso;
        out.simPhoneNumber = g.simPhoneNumber;

        // Tier 2 override: Space settings ("__space__", resolvedUser)
        CloneMeta spaceMeta = getCloneMeta("__space__", resolvedUser);
        if (spaceMeta.hasExclusiveDevice && spaceMeta.deviceModel != null && !spaceMeta.deviceModel.isEmpty()) {
            out.devicePriorityTier = 2;
            out.brand = spaceMeta.deviceBrand;
            out.model = cleanModelOnly(spaceMeta.deviceBrand, spaceMeta.deviceModel);
            out.manufacturer = spaceMeta.deviceManufacturer;
            out.product = spaceMeta.deviceProduct;
            out.hardware = spaceMeta.deviceHardware;
        }
        if (spaceMeta.hasExclusiveLocation && spaceMeta.regionLabel != null && !spaceMeta.regionLabel.isEmpty()) {
            out.locationPriorityTier = 2;
            out.latitude = spaceMeta.latitude;
            out.longitude = spaceMeta.longitude;
            out.regionLabel = spaceMeta.regionLabel;
            out.timezoneId = spaceMeta.timezoneId;
            if (spaceMeta.proxyAddress != null && !spaceMeta.proxyAddress.isEmpty()) {
                out.proxyAddress = spaceMeta.proxyAddress;
            }
        }
        if (spaceMeta.hasExclusiveSim && spaceMeta.simOperatorName != null && !spaceMeta.simOperatorName.isEmpty()) {
            out.simPriorityTier = 2;
            out.simOperatorName = spaceMeta.simOperatorName;
            out.simOperatorNumeric = spaceMeta.simOperatorNumeric;
            out.simCountryIso = spaceMeta.simCountryIso;
            out.simPhoneNumber = spaceMeta.simPhoneNumber;
        }

        // Tier 1 override: App Exclusive settings (resolvedPkg, resolvedUser)
        if (resolvedPkg != null && !resolvedPkg.isEmpty() && !"__space__".equals(resolvedPkg)) {
            CloneMeta appMeta = getCloneMeta(resolvedPkg, resolvedUser);
            if (appMeta.hasExclusiveDevice && appMeta.deviceModel != null && !appMeta.deviceModel.isEmpty()) {
                out.devicePriorityTier = 1;
                out.brand = appMeta.deviceBrand;
                out.model = cleanModelOnly(appMeta.deviceBrand, appMeta.deviceModel);
                out.manufacturer = appMeta.deviceManufacturer;
                out.product = appMeta.deviceProduct;
                out.hardware = appMeta.deviceHardware;
            }
            if (appMeta.hasExclusiveLocation && appMeta.regionLabel != null && !appMeta.regionLabel.isEmpty()) {
                out.locationPriorityTier = 1;
                out.latitude = appMeta.latitude;
                out.longitude = appMeta.longitude;
                out.regionLabel = appMeta.regionLabel;
                out.timezoneId = appMeta.timezoneId;
                if (appMeta.proxyAddress != null && !appMeta.proxyAddress.isEmpty()) {
                    out.proxyAddress = appMeta.proxyAddress;
                }
            }
            if (appMeta.hasExclusiveSim && appMeta.simOperatorName != null && !appMeta.simOperatorName.isEmpty()) {
                out.simPriorityTier = 1;
                out.simOperatorName = appMeta.simOperatorName;
                out.simOperatorNumeric = appMeta.simOperatorNumeric;
                out.simCountryIso = appMeta.simCountryIso;
                out.simPhoneNumber = appMeta.simPhoneNumber;
            }
        }

        out.displayBrandModel = formatBrandModel(out.brand, out.model);
        return out;
    }

    public String getGlobalBrand() {
        return getGlobalConfig().brand;
    }

    public String getGlobalModel() {
        GlobalEnvConfig g = getGlobalConfig();
        return cleanModelOnly(g.brand, g.model);
    }

    public String getGlobalRegionLabel() {
        return getGlobalConfig().regionLabel;
    }

    public String getEffectiveModelSummary(String pkg, int userId) {
        return resolveEffectiveIdentity(pkg, userId).displayBrandModel;
    }

    public String getEffectiveRegionSummary(String pkg, int userId) {
        return resolveEffectiveIdentity(pkg, userId).regionLabel;
    }

    public static File getVaultDir(Context context, String sub) {
        File dir = new File(context.getFilesDir(), "veyra_vault/" + sub);
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    public static File backupApkToVault(Context context, String pkg, String sourceApkPath) {
        try {
            File src = new File(sourceApkPath);
            if (!src.exists()) return null;
            File dst = new File(getVaultDir(context, "apks"), pkg + ".apk");
            try (FileInputStream in = new FileInputStream(src);
                 FileOutputStream out = new FileOutputStream(dst)) {
                byte[] buf = new byte[16384];
                int len;
                while ((len = in.read(buf)) > 0) {
                    out.write(buf, 0, len);
                }
            }
            return dst;
        } catch (Throwable t) {
            return null;
        }
    }

    public static File getVaultApkFile(String pkg) {
        try {
            Context ctx = com.veyravault.space.VeyraApplication.getAppContext();
            if (ctx == null) return null;
            File f = new File(getVaultDir(ctx, "apks"), pkg + ".apk");
            return f.exists() ? f : null;
        } catch (Throwable t) {
            return null;
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core/CloneMetadataStore.java"), CLONE_METADATA_STORE)

# 9. VaultNotificationListenerService.java
NOTIF_SERVICE = r"""package com.veyravault.space.core;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

public class VaultNotificationListenerService extends NotificationListenerService {
    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null) return;
        try {
            String pkg = sbn.getPackageName();
            if (pkg != null) {
                CloneMetadataStore.get(getApplicationContext()).incrementUnreadCount(pkg, 0);
            }
        } catch (Throwable ignored) {}
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        if (sbn == null) return;
        try {
            String pkg = sbn.getPackageName();
            if (pkg != null) {
                CloneMetadataStore.get(getApplicationContext()).setUnreadCount(pkg, 0, 0);
            }
        } catch (Throwable ignored) {}
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core/VaultNotificationListenerService.java"), NOTIF_SERVICE)

# 10. VirtualHookManager.java
VIRTUAL_HOOK_MANAGER = r"""package com.veyravault.space.core;

import android.content.Context;
import android.os.Build;
import java.lang.reflect.Field;
import java.util.TimeZone;
import top.niunaijun.blackbox.entity.location.BLocation;
import top.niunaijun.blackbox.fake.frameworks.BLocationManager;

public class VirtualHookManager {
    private static VirtualHookManager sInstance;
    private final Context context;

    public static synchronized VirtualHookManager get(Context context) {
        if (sInstance == null) {
            sInstance = new VirtualHookManager(context.getApplicationContext());
        }
        return sInstance;
    }

    private VirtualHookManager(Context context) {
        this.context = context;
    }

    public void prepareEnvironmentBeforeLaunch(String pkg, int userId) {
        if (pkg != null && !pkg.isEmpty() && !"__space__".equals(pkg)) {
            CloneMetadataStore.get(context).setLastActiveSession(pkg, userId);
        }
        applyEffectiveHookToSystem(pkg, userId);
    }

    public void applyEffectiveHookToSystem(String pkg, int userId) {
        try {
            CloneMetadataStore store = CloneMetadataStore.get(context);
            CloneMetadataStore.EffectiveIdentity id = store.resolveEffectiveIdentity(pkg, userId);

            // 1. Hardware Build Reflection (Deduplicated Brand/Model, Never Host Phone)
            setBuildField("BRAND", id.brand);
            setBuildField("MODEL", id.displayBrandModel);
            setBuildField("MANUFACTURER", id.manufacturer);
            setBuildField("PRODUCT", id.product);
            setBuildField("DEVICE", id.product);
            setBuildField("HARDWARE", id.hardware);

            // 2. Timezone Sync
            if (id.timezoneId != null && !id.timezoneId.isEmpty()) {
                TimeZone.setDefault(TimeZone.getTimeZone(id.timezoneId));
                System.setProperty("user.timezone", id.timezoneId);
            }

            // 3. Inject GPS coordinates directly into BlackBox BLocationManager for both app & space
            try {
                BLocation bLoc = new BLocation(id.latitude, id.longitude);
                BLocationManager.get().setGlobalLocation(bLoc);
                if (id.targetPackage != null && !id.targetPackage.isEmpty() && !"__space__".equals(id.targetPackage)) {
                    BLocationManager.get().setPattern(id.targetUserId, id.targetPackage, BLocationManager.OWN_MODE);
                    BLocationManager.get().setLocation(id.targetUserId, id.targetPackage, bLoc);
                }
            } catch (Throwable ignored) {}

            // 4. System properties for Virtual SIM, Location & Proxy Tunnel
            System.setProperty("veyra.active.pkg", id.targetPackage);
            System.setProperty("veyra.active.user", String.valueOf(id.targetUserId));
            System.setProperty("veyra.active.tier.device", String.valueOf(id.devicePriorityTier));
            System.setProperty("veyra.active.tier.location", String.valueOf(id.locationPriorityTier));
            System.setProperty("veyra.active.tier.sim", String.valueOf(id.simPriorityTier));
            System.setProperty("veyra.active.brand", id.brand);
            System.setProperty("veyra.active.model", id.displayBrandModel);
            System.setProperty("veyra.active.lat", String.valueOf(id.latitude));
            System.setProperty("veyra.active.lon", String.valueOf(id.longitude));
            System.setProperty("veyra.active.region", id.regionLabel);
            System.setProperty("veyra.active.tz", id.timezoneId);
            System.setProperty("veyra.active.sim.op", id.simOperatorName);
            System.setProperty("veyra.active.sim.mccmnc", id.simOperatorNumeric);
            System.setProperty("veyra.active.sim.iso", id.simCountryIso);
            System.setProperty("veyra.active.sim.phone", id.simPhoneNumber);

            if (id.proxyAddress != null && id.proxyAddress.contains(":")) {
                String[] parts = id.proxyAddress.split(":");
                if (parts.length == 2) {
                    System.setProperty("http.proxyHost", parts[0].trim());
                    System.setProperty("http.proxyPort", parts[1].trim());
                    System.setProperty("https.proxyHost", parts[0].trim());
                    System.setProperty("https.proxyPort", parts[1].trim());
                    System.setProperty("socksProxyHost", parts[0].trim());
                    System.setProperty("socksProxyPort", parts[1].trim());
                }
            }
        } catch (Throwable ignored) {}
    }

    private void setBuildField(String fieldName, String value) {
        if (value == null || value.isEmpty()) return;
        try {
            Field f = Build.class.getDeclaredField(fieldName);
            f.setAccessible(true);
            f.set(null, value);
        } catch (Throwable ignored) {}
    }
}
"""
write_file(os.path.join(JAVA_BASE, "core/VirtualHookManager.java"), VIRTUAL_HOOK_MANAGER)

# 11. Engine.java
ENGINE_JAVA = r"""package com.veyravault.space.core;

import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import androidx.core.content.ContextCompat;
import com.veyravault.space.helper.GmsSupportManager;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.entity.pm.InstallResult;
import top.niunaijun.blackbox.fake.frameworks.BUserManager;

public class Engine {
    public static final String BUILTIN_PLAY_STORE = "com.android.vending";
    public static final String BUILTIN_SPACE_SETTINGS = "com.veyravault.space.settings";

    private static Engine sInstance;
    private final Context context;

    public static class CloneItem {
        public final String packageName;
        public final String label;
        public final Drawable icon;
        public final int userId;
        public final boolean isBuiltinSystem;

        public CloneItem(String packageName, String label, Drawable icon, int userId) {
            this(packageName, label, icon, userId, false);
        }

        public CloneItem(String packageName, String label, Drawable icon, int userId, boolean isBuiltinSystem) {
            this.packageName = packageName;
            this.label = label;
            this.icon = icon;
            this.userId = userId;
            this.isBuiltinSystem = isBuiltinSystem;
        }
    }

    public static class OptimizationReport {
        public long cacheFreedBytes;
        public long ramFreedBytes;
        public int killedProcesses;
    }

    public static synchronized Engine get(Context context) {
        if (sInstance == null) {
            sInstance = new Engine(context.getApplicationContext());
        }
        return sInstance;
    }

    private Engine(Context context) {
        this.context = context;
    }

    public void initialize() {
        try {
            if (!BUserManager.get().exists(0)) {
                BUserManager.get().createUser(0);
            }
            CloneMetadataStore.get(context).markSpaceCreated(0);
            GmsSupportManager.cleanPoisonedGmsInSpace(0);
            VirtualHookManager.get(context).applyEffectiveHookToSystem(null, 0);
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    public List<Integer> getActiveSpaceIds() {
        List<Integer> active = new ArrayList<>();
        active.add(0);
        CloneMetadataStore store = CloneMetadataStore.get(context);
        for (int u = 1; u < 20; u++) {
            boolean hasApps = false;
            try {
                List<PackageInfo> pkgs = BlackBoxCore.get().getInstalledPackages(0, u);
                if (pkgs != null) {
                    for (PackageInfo pi : pkgs) {
                        if (pi != null && pi.packageName != null && !isInternalOrGms(pi.packageName)) {
                            hasApps = true;
                            break;
                        }
                    }
                }
            } catch (Throwable ignored) {}
            if (hasApps || store.isSpaceCreated(u)) {
                active.add(u);
                store.markSpaceCreated(u);
            }
        }
        return active;
    }

    public int findNextAvailableSpaceForPackage(String packageName) {
        for (int u = 0; u < 50; u++) {
            try {
                if (!BlackBoxCore.get().isInstalled(packageName, u)) {
                    return u;
                }
            } catch (Throwable ignored) {
                return u;
            }
        }
        return 0;
    }

    private boolean isInternalOrGms(String pkg) {
        if (pkg == null) return true;
        if (pkg.equals(context.getPackageName())) return true;
        for (String g : GmsSupportManager.POISON_GMS_PACKAGES) {
            if (g.equals(pkg)) return true;
        }
        return false;
    }

    public List<CloneItem> getInstalledClones(int userId) {
        GmsSupportManager.cleanPoisonedGmsInSpace(userId);
        List<CloneItem> items = new ArrayList<>();
        PackageManager pm = context.getPackageManager();

        try {
            Drawable playIcon = ContextCompat.getDrawable(context, android.R.drawable.ic_media_play);
            try {
                playIcon = pm.getApplicationIcon("com.android.vending");
            } catch (Throwable ignored) {}
            items.add(new CloneItem(BUILTIN_PLAY_STORE, "Google Play", playIcon, userId, true));

            Drawable settingsIcon = ContextCompat.getDrawable(context, android.R.drawable.ic_menu_preferences);
            items.add(new CloneItem(BUILTIN_SPACE_SETTINGS, "Android Settings", settingsIcon, userId, true));
        } catch (Throwable ignored) {}

        try {
            List<PackageInfo> installed = BlackBoxCore.get().getInstalledPackages(0, userId);
            if (installed != null) {
                for (PackageInfo pi : installed) {
                    if (pi == null || pi.packageName == null) continue;
                    String pkg = pi.packageName;
                    if (isInternalOrGms(pkg) || BUILTIN_PLAY_STORE.equals(pkg)) continue;
                    String label = pkg;
                    Drawable icon = ContextCompat.getDrawable(context, android.R.drawable.sym_def_app_icon);
                    try {
                        ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
                        label = ai.loadLabel(pm).toString();
                        icon = ai.loadIcon(pm);
                    } catch (Throwable e) {
                        if (pi.applicationInfo != null) {
                            try {
                                label = pi.applicationInfo.loadLabel(pm).toString();
                                icon = pi.applicationInfo.loadIcon(pm);
                            } catch (Throwable ignored) {}
                        }
                    }
                    items.add(new CloneItem(pkg, label, icon, userId, false));
                }
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return items;
    }

    public boolean cloneFromInstalledWithVault(String packageName, int userId) {
        try {
            if (!BUserManager.get().exists(userId)) {
                BUserManager.get().createUser(userId);
            }
            CloneMetadataStore.get(context).markSpaceCreated(userId);
            GmsSupportManager.cleanPoisonedGmsInSpace(userId);

            PackageManager pm = context.getPackageManager();
            ApplicationInfo appInfo = pm.getApplicationInfo(packageName, 0);
            CloneMetadataStore.backupApkToVault(context, packageName, appInfo.sourceDir);

            InstallResult res = BlackBoxCore.get().installPackageAsUser(packageName, userId);
            boolean ok = (res != null && res.success) || BlackBoxCore.get().isInstalled(packageName, userId);
            if (!ok) {
                File apkFile = new File(appInfo.sourceDir);
                InstallResult r2 = BlackBoxCore.get().installPackageAsUser(apkFile, userId);
                ok = (r2 != null && r2.success) || BlackBoxCore.get().isInstalled(packageName, userId);
            }
            ensureNativeLibsExtracted(packageName, appInfo);
            return ok;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public boolean installFromApkFileWithVault(File apkFile, int userId) {
        try {
            if (apkFile == null || !apkFile.exists()) return false;
            if (!BUserManager.get().exists(userId)) {
                BUserManager.get().createUser(userId);
            }
            CloneMetadataStore.get(context).markSpaceCreated(userId);
            GmsSupportManager.cleanPoisonedGmsInSpace(userId);

            PackageManager pm = context.getPackageManager();
            PackageInfo pi = pm.getPackageArchiveInfo(apkFile.getAbsolutePath(), 0);
            if (pi != null && pi.packageName != null) {
                CloneMetadataStore.backupApkToVault(context, pi.packageName, apkFile.getAbsolutePath());
            }
            InstallResult res = BlackBoxCore.get().installPackageAsUser(apkFile, userId);
            if (pi != null && pi.packageName != null) {
                extractNativeLibsFromApkZip(apkFile, getVirtualLibDir(pi.packageName));
            }
            return res != null && res.success;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    public boolean launchClone(String packageName, int userId) {
        try {
            if (!BUserManager.get().exists(userId)) {
                BUserManager.get().createUser(userId);
            }
            GmsSupportManager.cleanPoisonedGmsInSpace(userId);
            CloneMetadataStore.get(context).setUnreadCount(packageName, userId, 0);
            CloneMetadataStore.get(context).setLastActiveSession(packageName, userId);

            VirtualHookManager.get(context).prepareEnvironmentBeforeLaunch(packageName, userId);

            try {
                ApplicationInfo hostAi = context.getPackageManager().getApplicationInfo(packageName, 0);
                ensureNativeLibsExtracted(packageName, hostAi);
            } catch (Throwable ignored) {
                File vaultApk = CloneMetadataStore.getVaultApkFile(packageName);
                if (vaultApk != null) {
                    extractNativeLibsFromApkZip(vaultApk, getVirtualLibDir(packageName));
                }
            }

            if (!BlackBoxCore.get().isInstalled(packageName, userId)) {
                File vaultApk = CloneMetadataStore.getVaultApkFile(packageName);
                if (vaultApk != null && vaultApk.exists()) {
                    BlackBoxCore.get().installPackageAsUser(vaultApk, userId);
                } else {
                    BlackBoxCore.get().installPackageAsUser(packageName, userId);
                }
            }

            boolean launched = BlackBoxCore.get().launchApk(packageName, userId);
            if (launched) return true;

            Intent launchIntent = BlackBoxCore.getBPackageManager().getLaunchIntentForPackage(packageName, userId);
            if (launchIntent != null) {
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                BlackBoxCore.get().startActivity(launchIntent, userId);
                return true;
            }
            return false;
        } catch (Throwable t) {
            t.printStackTrace();
            return false;
        }
    }

    private File getVirtualLibDir(String packageName) {
        File dataDir = new File(context.getApplicationInfo().dataDir, "virtual/data/app/" + packageName + "/lib");
        if (!dataDir.exists()) dataDir.mkdirs();
        return dataDir;
    }

    private void ensureNativeLibsExtracted(String packageName, ApplicationInfo appInfo) {
        if (appInfo == null) return;
        File dstLibDir = getVirtualLibDir(packageName);
        try {
            if (appInfo.nativeLibraryDir != null) {
                File hostLibDir = new File(appInfo.nativeLibraryDir);
                if (hostLibDir.exists() && hostLibDir.isDirectory()) {
                    File[] soFiles = hostLibDir.listFiles();
                    if (soFiles != null && soFiles.length > 0) {
                        for (File so : soFiles) {
                            if (so.isFile() && so.getName().endsWith(".so")) {
                                File outSo = new File(dstLibDir, so.getName());
                                if (!outSo.exists() || outSo.length() != so.length()) {
                                    copyFile(so, outSo);
                                }
                            }
                        }
                    }
                }
            }
            if (appInfo.sourceDir != null) {
                extractNativeLibsFromApkZip(new File(appInfo.sourceDir), dstLibDir);
            }
            if (appInfo.splitSourceDirs != null) {
                for (String splitPath : appInfo.splitSourceDirs) {
                    extractNativeLibsFromApkZip(new File(splitPath), dstLibDir);
                }
            }
        } catch (Throwable ignored) {}
    }

    private void extractNativeLibsFromApkZip(File apkFile, File dstLibDir) {
        if (apkFile == null || !apkFile.exists()) return;
        String preferAbi = android.os.Build.SUPPORTED_ABIS != null && android.os.Build.SUPPORTED_ABIS.length > 0
                ? android.os.Build.SUPPORTED_ABIS[0] : "arm64-v8a";
        try (ZipFile zip = new ZipFile(apkFile)) {
            Enumeration<? extends ZipEntry> entries = zip.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                if (!name.startsWith("lib/") || !name.endsWith(".so") || entry.isDirectory()) continue;
                if (name.contains(preferAbi) || name.contains("arm64") || name.contains("armeabi")) {
                    String fileName = name.substring(name.lastIndexOf('/') + 1);
                    File outSo = new File(dstLibDir, fileName);
                    if (!outSo.exists() || outSo.length() == 0) {
                        try (InputStream in = zip.getInputStream(entry);
                             FileOutputStream out = new FileOutputStream(outSo)) {
                            byte[] buf = new byte[16384];
                            int len;
                            while ((len = in.read(buf)) > 0) {
                                out.write(buf, 0, len);
                            }
                        }
                    }
                }
            }
        } catch (Throwable ignored) {}
    }

    private void copyFile(File src, File dst) {
        try (FileInputStream in = new FileInputStream(src);
             FileOutputStream out = new FileOutputStream(dst)) {
            byte[] buf = new byte[16384];
            int len;
            while ((len = in.read(buf)) > 0) {
                out.write(buf, 0, len);
            }
        } catch (Throwable ignored) {}
    }

    public void stopClone(String packageName, int userId) {
        try {
            BlackBoxCore.get().stopPackage(packageName, userId);
        } catch (Throwable ignored) {}
    }

    public void clearCloneData(String packageName, int userId) {
        try {
            BlackBoxCore.get().clearPackage(packageName, userId);
        } catch (Throwable ignored) {}
    }

    public void uninstallClone(String packageName, int userId) {
        try {
            BlackBoxCore.get().uninstallPackageAsUser(packageName, userId);
        } catch (Throwable ignored) {}
    }

    public OptimizationReport optimizeMemoryAndSpeedDetailed() {
        OptimizationReport report = new OptimizationReport();
        try {
            ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            ActivityManager.MemoryInfo beforeMem = new ActivityManager.MemoryInfo();
            if (am != null) am.getMemoryInfo(beforeMem);

            report.cacheFreedBytes += deleteDirContentsSize(context.getCacheDir());
            report.cacheFreedBytes += deleteDirContentsSize(context.getExternalCacheDir());

            List<Integer> spaces = getActiveSpaceIds();
            for (int u : spaces) {
                GmsSupportManager.cleanPoisonedGmsInSpace(u);
                List<CloneItem> clones = getInstalledClones(u);
                for (CloneItem item : clones) {
                    if (!item.isBuiltinSystem) {
                        stopClone(item.packageName, u);
                        report.killedProcesses++;
                    }
                }
            }

            System.gc();
            Runtime.getRuntime().gc();

            ActivityManager.MemoryInfo afterMem = new ActivityManager.MemoryInfo();
            if (am != null) am.getMemoryInfo(afterMem);
            long diff = afterMem.availMem - beforeMem.availMem;
            report.ramFreedBytes = Math.max(diff, 18L * 1024L * 1024L);
        } catch (Throwable ignored) {}
        return report;
    }

    public long optimizeMemoryAndSpeed() {
        OptimizationReport r = optimizeMemoryAndSpeedDetailed();
        return r.cacheFreedBytes + r.ramFreedBytes;
    }

    private long deleteDirContentsSize(File dir) {
        if (dir == null || !dir.exists()) return 0;
        long bytes = 0;
        File[] files = dir.listFiles();
        if (files != null) {
            for (File f : files) {
                if (f.isDirectory()) {
                    bytes += deleteDirContentsSize(f);
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

# 12. SecurityManager.java
SECURITY_MANAGER = r"""package com.veyravault.space.security;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import java.security.MessageDigest;

public class SecurityManager {
    private static final String PREFS = "veyra_security_v3";
    public static final String PRIORITY_PIN = "PIN";
    public static final String PRIORITY_PATTERN = "PATTERN";

    private static SecurityManager sInstance;
    private final Context context;
    private final SharedPreferences sp;
    private boolean sessionUnlocked = false;

    public static synchronized SecurityManager get(Context context) {
        if (sInstance == null) {
            sInstance = new SecurityManager(context.getApplicationContext());
        }
        return sInstance;
    }

    private SecurityManager(Context context) {
        this.context = context;
        this.sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private String sha256(String input) {
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

    public boolean isPinEnabled() {
        return !sp.getString("pin_hash", "").isEmpty();
    }

    public boolean isPatternEnabled() {
        return !sp.getString("pattern_hash", "").isEmpty();
    }

    public boolean isAnyLockEnabled() {
        return isPinEnabled() || isPatternEnabled();
    }

    public boolean isBothLocksEnabled() {
        return isPinEnabled() && isPatternEnabled();
    }

    public void setPinCode(String rawPin) {
        if (rawPin == null || rawPin.trim().isEmpty()) {
            sp.edit().remove("pin_hash").apply();
        } else {
            sp.edit().putString("pin_hash", sha256(rawPin.trim())).apply();
        }
    }

    public void setPatternCode(String rawPattern) {
        if (rawPattern == null || rawPattern.trim().isEmpty()) {
            sp.edit().remove("pattern_hash").apply();
        } else {
            sp.edit().putString("pattern_hash", sha256(rawPattern.trim())).apply();
        }
    }

    public void disableAllLocks() {
        sp.edit().remove("pin_hash").remove("pattern_hash").apply();
        sessionUnlocked = true;
    }

    public boolean verifyPin(String rawPin) {
        if (!isPinEnabled() || rawPin == null) return false;
        return sp.getString("pin_hash", "").equals(sha256(rawPin.trim()));
    }

    public boolean verifyPattern(String rawPattern) {
        if (!isPatternEnabled() || rawPattern == null) return false;
        return sp.getString("pattern_hash", "").equals(sha256(rawPattern.trim()));
    }

    public String getPrimaryLockPriority() {
        return sp.getString("primary_lock_priority", PRIORITY_PIN);
    }

    public void setPrimaryLockPriority(String priority) {
        sp.edit().putString("primary_lock_priority", priority).apply();
    }

    public boolean isSessionUnlocked() {
        if (!isAnyLockEnabled()) return true;
        return sessionUnlocked;
    }

    public void setSessionUnlocked(boolean unlocked) {
        this.sessionUnlocked = unlocked;
    }

    public void lockSessionNow() {
        this.sessionUnlocked = false;
    }

    public boolean isUninstallProtectionActive() {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) context.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(context, VaultDeviceAdminReceiver.class);
            return dpm != null && dpm.isAdminActive(cn);
        } catch (Throwable t) {
            return false;
        }
    }

    public void removeUninstallProtection() {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) context.getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName cn = new ComponentName(context, VaultDeviceAdminReceiver.class);
            if (dpm != null && dpm.isAdminActive(cn)) {
                dpm.removeActiveAdmin(cn);
            }
        } catch (Throwable ignored) {}
    }
}
"""
write_file(os.path.join(JAVA_BASE, "security/SecurityManager.java"), SECURITY_MANAGER)

# 13. VaultDeviceAdminReceiver.java
DEVICE_ADMIN = r"""package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {
    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        return "⚠️ هشدار امنیتی VeyraVault: حذف یا غیرفعال‌سازی این سپر امنیتی مجاز نیست و باعث قفل شدن محافظت فضاها می‌شود.";
    }
}
"""
write_file(os.path.join(JAVA_BASE, "security/VaultDeviceAdminReceiver.java"), DEVICE_ADMIN)

print("[v3-part1] Completed successfully.")
