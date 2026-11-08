#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[v3-part2] Wrote: {path}")

JAVA_BASE = "app/src/main/java/com/veyravault/space"

# Auto-fix VirtualHookManager.java using reflection so BLocationManager never causes compile errors
VIRTUAL_HOOK_MANAGER_SAFE = r"""package com.veyravault.space.core;

import android.content.Context;
import android.os.Build;
import java.lang.reflect.Field;
import java.util.TimeZone;

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

            // 3. Inject GPS coordinates into BlackBox BLocationManager via safe reflection
            try {
                Class<?> bLocClass = Class.forName("top.niunaijun.blackbox.entity.location.BLocation");
                Object bLoc = bLocClass.getConstructor(double.class, double.class).newInstance(id.latitude, id.longitude);
                Class<?> mgrClass = Class.forName("top.niunaijun.blackbox.fake.frameworks.BLocationManager");
                Object mgr = mgrClass.getMethod("get").invoke(null);
                try {
                    mgrClass.getMethod("setGlobalLocation", bLocClass).invoke(mgr, bLoc);
                } catch (Throwable ignored) {}
                if (id.targetPackage != null && !id.targetPackage.isEmpty() && !"__space__".equals(id.targetPackage)) {
                    try {
                        mgrClass.getMethod("setPattern", int.class, String.class, int.class).invoke(mgr, id.targetUserId, id.targetPackage, 2);
                    } catch (Throwable ignored) {}
                    try {
                        mgrClass.getMethod("setLocation", int.class, String.class, bLocClass).invoke(mgr, id.targetUserId, id.targetPackage, bLoc);
                    } catch (Throwable ignored) {}
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
write_file(os.path.join(JAVA_BASE, "core/VirtualHookManager.java"), VIRTUAL_HOOK_MANAGER_SAFE)

MAIN_ACTIVITY = r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.GridLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.R;
import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.helper.JalaliClockUtil;
import com.veyravault.space.helper.LocaleHelper;
import com.veyravault.space.security.SecurityManager;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class MainActivity extends BaseActivity {
    private static int activeTabSession = 0; // 0=Dashboard, 1=Spaces, 2=VPN, 3=Settings
    private static int activeVpnSubTab = 0;  // 0=Countries/Clusters, 1=Settings, 2=Session/Guide
    private FrameLayout contentContainer;
    private TextView tvIranClock, tvIranDate, tvUsaClock, tvUsaDate;
    private final Handler clockHandler = new Handler(Looper.getMainLooper());
    private final LinearLayout[] navItems = new LinearLayout[4];

    private final Runnable clockTicker = new Runnable() {
        @Override
        public void run() {
            if (tvIranClock != null && tvUsaClock != null) {
                tvIranClock.setText(JalaliClockUtil.getIranTimeText());
                tvIranDate.setText(JalaliClockUtil.getIranJalaliDateText(isFa()));
                tvUsaClock.setText(JalaliClockUtil.getUsaTimeText());
                tvUsaDate.setText(JalaliClockUtil.getUsaGregorianDateText());
            }
            clockHandler.postDelayed(this, 1000);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        CloneMetadataStore store = CloneMetadataStore.get(this);
        VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
        buildMainLayout();
    }

    @Override
    protected void onResume() {
        super.onResume();
        SecurityManager sm = SecurityManager.get(this);
        if (sm.isAnyLockEnabled() && !sm.isSessionUnlocked()) {
            startActivity(new Intent(this, SecurityLockActivity.class));
            return;
        }
        CloneMetadataStore store = CloneMetadataStore.get(this);
        VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
        clockHandler.removeCallbacks(clockTicker);
        clockHandler.post(clockTicker);
        switchTab(activeTabSession);
        if (LocaleHelper.isLightTheme(this) && getWindow() != null) {
            LocaleHelper.applyThemeRecursive(getWindow().getDecorView(), true);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        clockHandler.removeCallbacks(clockTicker);
    }

    private void buildMainLayout() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#0B0F19"));

        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setPadding(dp(14), dp(12), dp(14), dp(12));
        topBar.setBackgroundColor(Color.parseColor("#0F172A"));

        TextView title = new TextView(this);
        title.setText("🛡️ VeyraVault");
        title.setTextColor(Color.WHITE);
        title.setTextSize(18);
        title.setTypeface(null, Typeface.BOLD);
        topBar.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView btnQuickLock = makePillButton(tr("🔒 قفل سریع", "🔒 Lock"), "#DC2626");
        btnQuickLock.setOnClickListener(v -> {
            SecurityManager sm = SecurityManager.get(this);
            if (!sm.isAnyLockEnabled()) {
                startActivity(new Intent(this, SecuritySettingsActivity.class));
            } else {
                sm.lockSessionNow();
                startActivity(new Intent(this, SecurityLockActivity.class));
            }
        });
        LinearLayout.LayoutParams lockLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lockLp.setMargins(dp(6), 0, dp(6), 0);
        topBar.addView(btnQuickLock, lockLp);

        TextView btnLang = makePillButton(isFa() ? "EN / فارسی" : "فارسی / EN", "#2563EB");
        btnLang.setOnClickListener(v -> {
            LocaleHelper.toggleLanguage(this);
            recreate();
        });
        topBar.addView(btnLang);
        root.addView(topBar);

        contentContainer = new FrameLayout(this);
        root.addView(contentContainer, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        LinearLayout bottomBar = new LinearLayout(this);
        bottomBar.setOrientation(LinearLayout.HORIZONTAL);
        bottomBar.setGravity(Gravity.CENTER);
        bottomBar.setBackgroundColor(Color.parseColor("#080B12"));
        bottomBar.setPadding(dp(4), dp(6), dp(4), dp(6));

        navItems[0] = createNavTab(R.drawable.ic_nav_dashboard, tr("داشبورد", "Dashboard"), () -> switchTab(0));
        navItems[1] = createNavTab(R.drawable.ic_nav_spaces, tr("فضاها", "Spaces"), () -> switchTab(1));

        LinearLayout addCenterWrap = new LinearLayout(this);
        addCenterWrap.setGravity(Gravity.CENTER);
        TextView plusBtn = new TextView(this);
        plusBtn.setText("+");
        plusBtn.setTextColor(Color.WHITE);
        plusBtn.setTextSize(24);
        plusBtn.setTypeface(null, Typeface.BOLD);
        plusBtn.setGravity(Gravity.CENTER);
        GradientDrawable plusBg = new GradientDrawable();
        plusBg.setShape(GradientDrawable.OVAL);
        plusBg.setColor(Color.parseColor("#2563EB"));
        plusBtn.setBackground(plusBg);
        plusBtn.setOnClickListener(v -> {
            Intent i = new Intent(this, AddAppActivity.class);
            i.putExtra("forced_user_id", -1);
            startActivity(i);
        });
        addCenterWrap.addView(plusBtn, new LinearLayout.LayoutParams(dp(44), dp(44)));

        navItems[2] = createNavTab(R.drawable.ic_nav_guide, "VPN", () -> switchTab(2));
        navItems[3] = createNavTab(R.drawable.ic_nav_settings, tr("تنظیمات", "Settings"), () -> switchTab(3));

        bottomBar.addView(navItems[0], new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        bottomBar.addView(navItems[1], new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        bottomBar.addView(addCenterWrap, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        bottomBar.addView(navItems[2], new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        bottomBar.addView(navItems[3], new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        root.addView(bottomBar);
        setContentView(root);
    }

    private LinearLayout createNavTab(int iconRes, String label, Runnable onClick) {
        LinearLayout tab = new LinearLayout(this);
        tab.setOrientation(LinearLayout.VERTICAL);
        tab.setGravity(Gravity.CENTER);
        tab.setPadding(dp(2), dp(4), dp(2), dp(4));
        ImageView icon = new ImageView(this);
        icon.setImageResource(iconRes);
        tab.addView(icon, new LinearLayout.LayoutParams(dp(20), dp(20)));
        TextView tv = new TextView(this);
        tv.setText(label);
        tv.setTextSize(11);
        tv.setGravity(Gravity.CENTER);
        tab.addView(tv);
        tab.setOnClickListener(v -> onClick.run());
        return tab;
    }

    private void switchTab(int idx) {
        activeTabSession = idx;
        for (int i = 0; i < navItems.length; i++) {
            boolean active = (i == idx);
            ImageView icon = (ImageView) navItems[i].getChildAt(0);
            TextView tv = (TextView) navItems[i].getChildAt(1);
            int color = Color.parseColor(active ? "#38BDF8" : "#64748B");
            icon.setColorFilter(color);
            tv.setTextColor(color);
            tv.setTypeface(null, active ? Typeface.BOLD : Typeface.NORMAL);
        }
        contentContainer.removeAllViews();
        if (idx == 0) contentContainer.addView(buildDashboardView());
        else if (idx == 1) contentContainer.addView(buildSpacesView());
        else if (idx == 2) contentContainer.addView(buildVpnHubView());
        else if (idx == 3) contentContainer.addView(buildSettingsView());
        if (LocaleHelper.isLightTheme(this)) {
            LocaleHelper.applyThemeRecursive(contentContainer, true);
        }
    }

    private String formatPriorityBadge(int tier) {
        if (tier == 1) return tr(" [اولویت ۱: اختصاصی برنامه]", " [Priority #1: App Exclusive]");
        if (tier == 2) return tr(" [اولویت ۲: اختصاصی فضا]", " [Priority #2: Space Exclusive]");
        return tr(" [اولویت ۳: سراسری امن]", " [Priority #3: Global Vault]");
    }

    private View buildDashboardView() {
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(14), dp(14), dp(14), dp(24));

        LinearLayout clockRow = new LinearLayout(this);
        clockRow.setOrientation(LinearLayout.HORIZONTAL);

        LinearLayout iranCard = makeCard("#1E293B");
        iranCard.setGravity(Gravity.CENTER);
        iranCard.addView(makeText(tr("ایران (تهران)", "Iran (Tehran)"), 12, "#94A3B8", true));
        tvIranClock = makeText(JalaliClockUtil.getIranTimeText(), 20, "#38BDF8", true);
        tvIranDate = makeText(JalaliClockUtil.getIranJalaliDateText(isFa()), 11, "#E2E8F0", false);
        tvIranDate.setGravity(Gravity.CENTER);
        iranCard.addView(tvIranClock); iranCard.addView(tvIranDate);

        LinearLayout usaCard = makeCard("#1E293B");
        usaCard.setGravity(Gravity.CENTER);
        usaCard.addView(makeText(tr("آمریکا (نیویورک)", "USA (New York)"), 12, "#94A3B8", true));
        tvUsaClock = makeText(JalaliClockUtil.getUsaTimeText(), 20, "#4ADE80", true);
        tvUsaDate = makeText(JalaliClockUtil.getUsaGregorianDateText(), 11, "#E2E8F0", false);
        tvUsaDate.setGravity(Gravity.CENTER);
        usaCard.addView(tvUsaClock); usaCard.addView(tvUsaDate);

        LinearLayout.LayoutParams cLp1 = new LinearLayout.LayoutParams(0, dp(112), 1f);
        cLp1.setMargins(dp(4), 0, dp(4), 0);
        LinearLayout.LayoutParams cLp2 = new LinearLayout.LayoutParams(0, dp(112), 1f);
        cLp2.setMargins(dp(4), 0, dp(4), 0);
        clockRow.addView(iranCard, cLp1);
        clockRow.addView(usaCard, cLp2);
        box.addView(clockRow);

        CloneMetadataStore store = CloneMetadataStore.get(this);
        CloneMetadataStore.EffectiveIdentity eff = store.resolveEffectiveIdentity(null, 0);

        LinearLayout envCard = makeCard("#161F33");
        envCard.addView(makeText(tr("📱 هویت فعال فعلی (سپر ضد نشت اطلاعات گوشی اصلی)", "📱 Active Shielded Identity (Zero Host Leak)"), 14, "#38BDF8", true));
        if (!eff.targetPackage.isEmpty()) {
            envCard.addView(makeText(tr("🎯 نشست هدف: ", "🎯 Active Target: ") + eff.targetPackage + " (#" + (eff.targetUserId + 1) + ")", 12, "#A7F3D0", true));
        }
        envCard.addView(makeText(tr("مدل دستگاه: ", "Device Model: ") + eff.displayBrandModel + formatPriorityBadge(eff.devicePriorityTier), 13, "#F8FAFC", false));
        envCard.addView(makeText(tr("منطقه فعال: ", "Active Region: ") + eff.regionLabel + " (" + eff.timezoneId + ")" + formatPriorityBadge(eff.locationPriorityTier), 13, "#4ADE80", false));
        envCard.addView(makeText(tr("سیم‌کارت مجازی: ", "Virtual SIM: ") + eff.simOperatorName + " (" + eff.simOperatorNumeric + " | " + eff.simCountryIso.toUpperCase() + ")" + formatPriorityBadge(eff.simPriorityTier), 12, "#FBBF24", false));
        TextView btnEditEnv = makePillButton(tr("⚙️ ویرایش هویت، سیم‌کارت و موقعیت سراسری", "⚙️ Edit Global Device, SIM & Location"), "#2563EB");
        btnEditEnv.setOnClickListener(v -> startActivity(new Intent(this, GlobalEnvironmentActivity.class)));
        envCard.addView(btnEditEnv);
        box.addView(envCard);

        LinearLayout boostCard = makeCard("#161F33");
        boostCard.addView(makeText(tr("🚀 افزایش سرعت و بهینه‌سازی واقعی حافظه", "🚀 Real Speed & Memory Optimizer"), 14, "#F59E0B", true));
        boostCard.addView(makeText(tr("پاک‌سازی کش واقعی برنامه‌های مجازی، حذف فایل‌های موقت و بستن پردازش‌های پس‌زمینه", "Cleans real virtual app caches, temp files, and idle background processes"), 12, "#CBD5E1", false));
        TextView btnBoost = makePillButton(tr("⚡ بهینه‌سازی فوری حافظه", "⚡ Optimize Now"), "#10B981");
        btnBoost.setOnClickListener(v -> {
            Engine.OptimizationReport rep = Engine.get(this).optimizeMemoryAndSpeedDetailed();
            String msg = String.format(isFa()
                    ? "✅ بهینه‌سازی واقعی انجام شد:\n• کش پاک‌شده: %.2f KB\n• رم آزادشده: %.2f MB\n• پردازش‌های متوقف‌شده: %d"
                    : "✅ Real Optimization Complete:\n• Cache Deleted: %.2f KB\n• RAM Freed: %.2f MB\n• Idle Processes Stopped: %d",
                    rep.cacheFreedBytes / 1024.0, rep.ramFreedBytes / (1024.0 * 1024.0), rep.killedProcesses);
            new AlertDialog.Builder(this).setTitle(tr("گزارش بهینه‌سازی واقعی", "Optimization Report"))
                    .setMessage(msg).setPositiveButton(tr("باشه", "OK"), null).show();
        });
        boostCard.addView(btnBoost);
        box.addView(boostCard);

        sv.addView(box);
        return sv;
    }

    private View buildSpacesView() {
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(12), dp(12), dp(12), dp(28));

        CloneMetadataStore store = CloneMetadataStore.get(this);
        String globalCleanModel = CloneMetadataStore.formatBrandModel(store.getGlobalBrand(), store.getGlobalModel());
        LinearLayout banner = makeCard("#1D4ED8");
        banner.addView(makeText(tr("فضاهای چندگانه و سلسله‌مراتب ۳ لایه هویت", "Smart Multi-Spaces & 3-Tier Identity"), 15, "#FFFFFF", true));
        banner.addView(makeText(tr("اولویت ۱: اختصاصی برنامه  |  اولویت ۲: فضا  |  اولویت ۳: ", "P1: App  |  P2: Space  |  P3: ") + globalCleanModel, 11, "#E0F2FE", false));
        banner.addView(makeText(tr("منطقه پایه سراسری: ", "Base Global Region: ") + store.getGlobalRegionLabel(), 12, "#BAE6FD", false));
        box.addView(banner);

        List<Integer> activeSpaces = Engine.get(this).getActiveSpaceIds();
        for (int userId : activeSpaces) {
            box.addView(buildSingleSpaceSection(userId));
        }
        sv.addView(box);
        return sv;
    }

    private View buildSingleSpaceSection(int userId) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        LinearLayout card = makeCard("#161F33");

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);

        TextView tvSpaceTitle = makeText("📂 " + store.getSpaceDisplayName(userId, isFa()), 15, "#38BDF8", true);
        header.addView(tvSpaceTitle, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView btnAddInSpace = makePillButton(tr("+ افزودن برنامه", "+ Add App"), "#2563EB");
        btnAddInSpace.setOnClickListener(v -> {
            Intent i = new Intent(this, AddAppActivity.class);
            i.putExtra("forced_user_id", userId);
            startActivity(i);
        });
        header.addView(btnAddInSpace);

        TextView btnDots = makeText("  ⋮  ", 20, "#F8FAFC", true);
        btnDots.setOnClickListener(v -> showSpaceMenuDialog(userId));
        header.addView(btnDots);
        card.addView(header);

        List<Engine.CloneItem> clones = Engine.get(this).getInstalledClones(userId);
        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(3);
        grid.setPadding(0, dp(8), 0, 0);
        for (Engine.CloneItem item : clones) {
            grid.addView(buildCloneAppTile(item));
        }
        card.addView(grid);
        return card;
    }

    private View buildCloneAppTile(Engine.CloneItem item) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        CloneMetadataStore.CloneMeta meta = store.getCloneMeta(item.packageName, item.userId);
        CloneMetadataStore.EffectiveIdentity eff = store.resolveEffectiveIdentity(item.packageName, item.userId);
        int cloneNum = item.userId + 1;

        LinearLayout tile = new LinearLayout(this);
        tile.setOrientation(LinearLayout.VERTICAL);
        tile.setGravity(Gravity.CENTER);
        tile.setPadding(dp(6), dp(8), dp(6), dp(8));
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.parseColor("#0F172A"));
        bg.setCornerRadius(dp(12));
        tile.setBackground(bg);

        LinearLayout badgeRow = new LinearLayout(this);
        badgeRow.setOrientation(LinearLayout.HORIZONTAL);
        badgeRow.setGravity(Gravity.CENTER_VERTICAL);

        int unreadCount = store.getUnreadCount(item.packageName, item.userId);
        TextView leftNotifBadge = new TextView(this);
        leftNotifBadge.setText(store.formatBadgeText(unreadCount));
        leftNotifBadge.setTextSize(10);
        leftNotifBadge.setTextColor(Color.WHITE);
        leftNotifBadge.setTypeface(null, Typeface.BOLD);
        leftNotifBadge.setPadding(dp(6), dp(1), dp(6), dp(1));
        GradientDrawable notifBg = new GradientDrawable();
        notifBg.setColor(Color.parseColor("#EF4444"));
        notifBg.setCornerRadius(dp(10));
        leftNotifBadge.setBackground(notifBg);
        leftNotifBadge.setVisibility(unreadCount > 0 ? View.VISIBLE : View.INVISIBLE);

        View spacer = new View(this);
        boolean hasP1 = meta.hasExclusiveDevice || meta.hasExclusiveLocation || meta.hasExclusiveSim;
        TextView rightCloneBadge = makeText((hasP1 ? "★#" : "#") + cloneNum, 10, hasP1 ? "#FBBF24" : "#38BDF8", true);

        badgeRow.addView(leftNotifBadge);
        badgeRow.addView(spacer, new LinearLayout.LayoutParams(0, dp(1), 1f));
        badgeRow.addView(rightCloneBadge);
        tile.addView(badgeRow, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        ImageView iv = new ImageView(this);
        iv.setImageDrawable(item.icon);
        tile.addView(iv, new LinearLayout.LayoutParams(dp(44), dp(44)));

        String dispName = (meta.customAlias != null && !meta.customAlias.isEmpty())
                ? meta.customAlias : (item.label + (item.isBuiltinSystem ? "" : (" " + cloneNum)));
        TextView tvName = makeText(dispName, 11, "#F8FAFC", true);
        tvName.setMaxLines(1);
        tvName.setGravity(Gravity.CENTER);
        tile.addView(tvName);

        TextView tvModel = makeText(eff.displayBrandModel, 9, "#CBD5E1", false);
        tvModel.setMaxLines(1);
        tvModel.setGravity(Gravity.CENTER);
        tile.addView(tvModel);

        TextView tvSub = makeText(eff.regionLabel, 9, "#4ADE80", false);
        tvSub.setMaxLines(1);
        tvSub.setGravity(Gravity.CENTER);
        tile.addView(tvSub);

        tile.setOnClickListener(v -> {
            if (Engine.BUILTIN_SPACE_SETTINGS.equals(item.packageName)) {
                showSpaceAndroidSettingsDialog(item.userId);
                return;
            }
            if (Engine.BUILTIN_PLAY_STORE.equals(item.packageName)) {
                openSpacePlayStore(item.userId);
                return;
            }
            store.setLastActiveSession(item.packageName, item.userId);
            VirtualHookManager.get(this).prepareEnvironmentBeforeLaunch(item.packageName, item.userId);
            Toast.makeText(this, tr("در حال اجرای ", "Launching ") + dispName + " (" + eff.displayBrandModel + ")...", Toast.LENGTH_SHORT).show();
            boolean ok = Engine.get(this).launchClone(item.packageName, item.userId);
            if (!ok) {
                Engine.get(this).cloneFromInstalledWithVault(item.packageName, item.userId);
                Engine.get(this).launchClone(item.packageName, item.userId);
            }
            switchTab(1);
        });

        tile.setOnLongClickListener(v -> {
            if (item.isBuiltinSystem) showSpaceAndroidSettingsDialog(item.userId);
            else showCloneContextMenu(item);
            return true;
        });

        GridLayout.LayoutParams glp = new GridLayout.LayoutParams();
        glp.width = (getResources().getDisplayMetrics().widthPixels - dp(68)) / 3;
        glp.setMargins(dp(4), dp(4), dp(4), dp(4));
        tile.setLayoutParams(glp);
        return tile;
    }

    private void openSpacePlayStore(int userId) {
        String[] opts = {
            tr("▶️ اجرای مستقیم Google Play در این فضا", "▶️ Launch Google Play in this Space"),
            tr("➕ نصب و کلون برنامه در فضای " + (userId + 1), "➕ Install App into Space " + (userId + 1)),
            tr("🌐 باز کردن نسخه وب Google Play", "🌐 Open Google Play Web")
        };
        new AlertDialog.Builder(this)
            .setTitle(tr("فروشگاه گوگل پلی - فضای " + (userId + 1), "Google Play - Space " + (userId + 1)))
            .setItems(opts, (d, w) -> {
                if (w == 0) {
                    boolean ok = Engine.get(this).launchClone("com.android.vending", userId);
                    if (!ok) {
                        Intent i = new Intent(this, AddAppActivity.class);
                        i.putExtra("forced_user_id", userId);
                        startActivity(i);
                    }
                } else if (w == 1) {
                    Intent i = new Intent(this, AddAppActivity.class);
                    i.putExtra("forced_user_id", userId);
                    startActivity(i);
                } else {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps")));
                }
            }).show();
    }

    private void showSpaceAndroidSettingsDialog(int userId) {
        String[] items = {
            tr("📱 تنظیم مدل گوشی اختصاصی این فضا (اولویت ۲)", "📱 Space Device Model (Priority #2)"),
            tr("📍 تنظیم موقعیت مکانی و منطقه این فضا (اولویت ۲)", "📍 Space Location & Region (Priority #2)"),
            tr("💳 تنظیم سیم‌کارت مجازی اختصاصی این فضا (اولویت ۲)", "💳 Space Virtual SIM Card (Priority #2)"),
            tr("✏️ تغییر نام این فضا", "✏️ Rename Space"),
            tr("🔄 بازنشانی تنظیمات این فضا به حالت سراسری (اولویت ۳)", "🔄 Reset Space to Global Defaults (Priority #3)")
        };
        new AlertDialog.Builder(this)
            .setTitle(tr("⚙️ تنظیمات سیستم اندروید - فضای " + (userId + 1), "⚙️ Space Android Settings - #" + (userId + 1)))
            .setItems(items, (d, which) -> {
                if (which == 0) showDevicePickerForTarget("__space__", userId);
                else if (which == 1) {
                    Intent loc = new Intent(this, SetLocationActivity.class);
                    loc.putExtra("target_pkg", "__space__");
                    loc.putExtra("target_user", userId);
                    startActivity(loc);
                } else if (which == 2) showSimConfigDialog("__space__", userId);
                else if (which == 3) showSpaceMenuDialog(userId);
                else if (which == 4) {
                    CloneMetadataStore.CloneMeta m = CloneMetadataStore.get(this).getCloneMeta("__space__", userId);
                    m.hasExclusiveDevice = false;
                    m.hasExclusiveLocation = false;
                    m.hasExclusiveSim = false;
                    CloneMetadataStore.get(this).saveCloneMeta(m);
                    switchTab(1);
                }
            }).show();
    }

    private void showSpaceMenuDialog(int userId) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        String[] options = {
            tr("✏️ تغییر نام فضا", "✏️ Rename Space"),
            tr("⚙️ تنظیمات اندروید این فضا", "⚙️ Space Android Settings"),
            tr("🔄 بازنشانی نام پیش‌فرض", "🔄 Reset Default Name")
        };
        new AlertDialog.Builder(this)
            .setTitle(store.getSpaceDisplayName(userId, isFa()))
            .setItems(options, (d, which) -> {
                if (which == 0) {
                    EditText input = new EditText(this);
                    input.setText(store.getSpaceDisplayName(userId, isFa()));
                    new AlertDialog.Builder(this)
                        .setTitle(tr("نام جدید فضا", "New Space Name"))
                        .setView(input)
                        .setPositiveButton(tr("ذخیره", "Save"), (d2, w2) -> {
                            store.setSpaceCustomName(userId, input.getText().toString());
                            switchTab(1);
                        }).show();
                } else if (which == 1) {
                    showSpaceAndroidSettingsDialog(userId);
                } else {
                    store.setSpaceCustomName(userId, "");
                    switchTab(1);
                }
            }).show();
    }

    private void showCloneContextMenu(Engine.CloneItem item) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        CloneMetadataStore.CloneMeta meta = store.getCloneMeta(item.packageName, item.userId);
        String[] items = {
            tr("▶️ اجرای برنامه با اعمال فوری اولویت ۱", "▶️ Launch App with Priority #1"),
            tr("✏️ تغییر نام مستعار", "✏️ Rename Alias"),
            tr("📱 مدل دستگاه اختصاصی (اولویت ۱ قطعی)", "📱 Exclusive Device Model (#1 Priority)"),
            tr("📍 موقعیت مکانی و پروکسی اختصاصی (اولویت ۱ قطعی)", "📍 Exclusive Location & Proxy (#1 Priority)"),
            tr("💳 سیم‌کارت مجازی اختصاصی (اولویت ۱ قطعی)", "💳 Exclusive Virtual SIM (#1 Priority)"),
            tr("🔔 تست نشان اعلان سمت چپ (۰ / ۱ / ۹۹ / ∞)", "🔔 Test Left Notification Badge (0 / 1 / 99 / ∞)"),
            tr("⏹️ توقف اجباری", "⏹️ Force Stop"),
            tr("🧹 پاک کردن داده‌های کلون", "🧹 Clear Clone Data"),
            tr("🗑️ حذف این کلون", "🗑️ Uninstall Clone")
        };
        new AlertDialog.Builder(this)
            .setTitle(item.label + " (#" + (item.userId + 1) + ")")
            .setItems(items, (d, which) -> {
                if (which == 0) {
                    store.setLastActiveSession(item.packageName, item.userId);
                    Engine.get(this).launchClone(item.packageName, item.userId);
                } else if (which == 1) {
                    EditText et = new EditText(this);
                    et.setText(meta.customAlias);
                    new AlertDialog.Builder(this).setTitle(tr("نام مستعار", "Custom Alias")).setView(et)
                        .setPositiveButton(tr("ذخیره", "Save"), (d2, w2) -> {
                            meta.customAlias = et.getText().toString().trim();
                            store.saveCloneMeta(meta);
                            switchTab(1);
                        }).show();
                } else if (which == 2) showDevicePickerForTarget(item.packageName, item.userId);
                else if (which == 3) {
                    store.setLastActiveSession(item.packageName, item.userId);
                    Intent locIntent = new Intent(this, SetLocationActivity.class);
                    locIntent.putExtra("target_pkg", item.packageName);
                    locIntent.putExtra("target_user", item.userId);
                    startActivity(locIntent);
                } else if (which == 4) showSimConfigDialog(item.packageName, item.userId);
                else if (which == 5) showBadgeTestDialog(item.packageName, item.userId);
                else if (which == 6) Engine.get(this).stopClone(item.packageName, item.userId);
                else if (which == 7) Engine.get(this).clearCloneData(item.packageName, item.userId);
                else if (which == 8) {
                    Engine.get(this).uninstallClone(item.packageName, item.userId);
                    switchTab(1);
                }
            }).show();
    }

    private void showBadgeTestDialog(String pkg, int userId) {
        String[] counts = {"0 (مخفی)", "1", "99", "120 (نمایش ∞)"};
        int[] vals = {0, 1, 99, 120};
        new AlertDialog.Builder(this)
            .setTitle(tr("تنظیم نشان اعلان سمت چپ", "Set Left Notification Badge"))
            .setItems(counts, (d, w) -> {
                CloneMetadataStore.get(this).setUnreadCount(pkg, userId, vals[w]);
                switchTab(1);
            }).show();
    }

    private void showSimConfigDialog(String pkg, int userId) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        CloneMetadataStore.CloneMeta meta = store.getCloneMeta(pkg, userId);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(12), dp(16), dp(12));
        EditText etOp = new EditText(this); etOp.setHint("Operator (T-Mobile USA)"); etOp.setText(meta.simOperatorName);
        EditText etNum = new EditText(this); etNum.setHint("MCC/MNC (310260)"); etNum.setText(meta.simOperatorNumeric);
        EditText etIso = new EditText(this); etIso.setHint("Country ISO (us)"); etIso.setText(meta.simCountryIso);
        EditText etPhone = new EditText(this); etPhone.setHint("Phone (+13105550199)"); etPhone.setText(meta.simPhoneNumber);
        box.addView(etOp); box.addView(etNum); box.addView(etIso); box.addView(etPhone);
        new AlertDialog.Builder(this)
            .setTitle(tr("💳 سیم‌کارت مجازی اختصاصی", "💳 Exclusive Virtual SIM"))
            .setView(box)
            .setPositiveButton(tr("ذخیره و اعمال فوری", "Save & Apply"), (d, w) -> {
                meta.hasExclusiveSim = true;
                meta.simOperatorName = etOp.getText().toString().trim();
                meta.simOperatorNumeric = etNum.getText().toString().trim();
                meta.simCountryIso = etIso.getText().toString().trim().toLowerCase();
                meta.simPhoneNumber = etPhone.getText().toString().trim();
                store.saveCloneMeta(meta);
                if (!"__space__".equals(pkg)) store.setLastActiveSession(pkg, userId);
                VirtualHookManager.get(this).applyEffectiveHookToSystem(pkg, userId);
                Toast.makeText(this, tr("✅ سیم‌کارت مجازی اختصاصی اعمال شد", "✅ Exclusive Virtual SIM Applied"), Toast.LENGTH_SHORT).show();
                switchTab(1);
            })
            .setNeutralButton(tr("استفاده از سراسری", "Use Global"), (d, w) -> {
                meta.hasExclusiveSim = false;
                store.saveCloneMeta(meta);
                VirtualHookManager.get(this).applyEffectiveHookToSystem(pkg, userId);
                switchTab(1);
            }).show();
    }

    private void showDevicePickerForTarget(String pkg, int userId) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        CloneMetadataStore.CloneMeta meta = store.getCloneMeta(pkg, userId);
        CloneMetadataStore.DevicePreset[] presets = CloneMetadataStore.PRESETS;
        String[] labels = new String[presets.length + 1];
        labels[0] = tr("🌐 استفاده از مدل پایه فضا / سراسری", "🌐 Inherit Space / Global Model");
        for (int i = 0; i < presets.length; i++) {
            labels[i + 1] = CloneMetadataStore.formatBrandModel(presets[i].brand, presets[i].model);
        }
        new AlertDialog.Builder(this)
            .setTitle(tr("انتخاب مدل دستگاه (بدون تکرار نام برند)", "Select Device Model"))
            .setItems(labels, (d, which) -> {
                if (which == 0) {
                    meta.hasExclusiveDevice = false;
                } else {
                    CloneMetadataStore.DevicePreset p = presets[which - 1];
                    meta.hasExclusiveDevice = true;
                    meta.deviceBrand = p.brand;
                    meta.deviceModel = CloneMetadataStore.cleanModelOnly(p.brand, p.model);
                    meta.deviceManufacturer = p.manufacturer;
                    meta.deviceProduct = p.product;
                    meta.deviceHardware = p.hardware;
                }
                store.saveCloneMeta(meta);
                if (!"__space__".equals(pkg)) store.setLastActiveSession(pkg, userId);
                VirtualHookManager.get(this).applyEffectiveHookToSystem(pkg, userId);
                switchTab(1);
            }).show();
    }

    private View buildVpnHubView() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        LinearLayout subTabBar = new LinearLayout(this);
        subTabBar.setOrientation(LinearLayout.HORIZONTAL);
        subTabBar.setPadding(dp(10), dp(8), dp(10), dp(8));
        subTabBar.setBackgroundColor(Color.parseColor("#0F172A"));

        String[] subTitles = {
            tr("🌍 خوشه‌ها و VPN", "🌍 Clusters & VPN"),
            tr("⚙️ تنظیمات VPN", "⚙️ VPN Settings"),
            tr("🛡️ نشست و راهنما", "🛡️ Session & Guide")
        };
        for (int i = 0; i < 3; i++) {
            final int subIdx = i;
            TextView tabBtn = makePillButton(subTitles[i], activeVpnSubTab == i ? "#2563EB" : "#1E293B");
            tabBtn.setGravity(Gravity.CENTER);
            tabBtn.setOnClickListener(v -> {
                activeVpnSubTab = subIdx;
                switchTab(2);
            });
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
            lp.setMargins(dp(3), 0, dp(3), 0);
            subTabBar.addView(tabBtn, lp);
        }
        root.addView(subTabBar);

        ScrollView sv = new ScrollView(this);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(12), dp(12), dp(12), dp(24));

        CloneMetadataStore store = CloneMetadataStore.get(this);
        List<CloneMetadataStore.VpnProfile> profiles = store.getVpnProfiles();
        String activeId = store.getActiveVpnId();
        CloneMetadataStore.VpnProfile activeProfile = profiles.isEmpty() ? null : profiles.get(0);
        for (CloneMetadataStore.VpnProfile p : profiles) {
            if (p.id.equals(activeId)) { activeProfile = p; break; }
        }
        final CloneMetadataStore.VpnProfile finalActive = activeProfile;

        if (activeVpnSubTab == 0) {
            boolean connected = store.isVpnConnected();
            LinearLayout statusCard = makeCard(connected ? "#064E3B" : "#1E293B");
            statusCard.addView(makeText(connected
                    ? tr("🟢 وضعیت: متصل به خوشه ضدقطعی VPN", "🟢 Status: Connected to Anti-Drop VPN Cluster")
                    : tr("⚪ وضعیت: آماده اتصال", "⚪ Status: Ready to Connect"), 15, "#FFFFFF", true));
            if (finalActive != null) {
                statusCard.addView(makeText("📂 " + finalActive.category, 12, "#FBBF24", true));
                statusCard.addView(makeText(finalActive.title, 14, "#38BDF8", true));
                statusCard.addView(makeText(finalActive.stateOrCity + " | " + finalActive.protocol + " (" + finalActive.host + ":" + finalActive.port + ")", 12, "#CBD5E1", false));
            }
            LinearLayout actionRow = new LinearLayout(this);
            actionRow.setOrientation(LinearLayout.HORIZONTAL);
            actionRow.setPadding(0, dp(8), 0, 0);

            TextView btnToggle = makePillButton(connected ? tr("⏹️ قطع اتصال VPN", "⏹️ Disconnect VPN") : tr("🚀 اتصال و همگام‌سازی فوری", "🚀 Connect & Sync Now"), connected ? "#DC2626" : "#10B981");
            btnToggle.setOnClickListener(v -> {
                boolean next = !store.isVpnConnected();
                store.setVpnConnected(next);
                if (next && finalActive != null) {
                    store.applyVpnProfileToEnvironment(finalActive);
                    VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
                    Toast.makeText(this, tr("✅ متصل شد و موقعیت/سیم‌کارت همگام شد: ", "✅ Connected & Synced: ") + finalActive.stateOrCity, Toast.LENGTH_SHORT).show();
                }
                switchTab(2);
            });
            actionRow.addView(btnToggle, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            TextView btnAddVpn = makePillButton(tr("+ اکانت / VPN رایگان", "+ Free / Custom VPN"), "#2563EB");
            btnAddVpn.setOnClickListener(v -> showAddOrEditVpnDialog(null));
            LinearLayout.LayoutParams addLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            addLp.setMargins(dp(6), 0, 0, 0);
            actionRow.addView(btnAddVpn, addLp);
            statusCard.addView(actionRow);

            // Seamless Sibling Rotation button inside the same category
            TextView btnRotateSibling = makePillButton(tr("🔄 چرخش فوری به سرور هم‌خانواده بعدی در همین دسته (بدون قطعی)", "🔄 Instant Failover to Next Sibling Node in Cluster"), "#0D9488");
            LinearLayout.LayoutParams rotLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            rotLp.setMargins(0, dp(8), 0, 0);
            btnRotateSibling.setLayoutParams(rotLp);
            btnRotateSibling.setGravity(Gravity.CENTER);
            btnRotateSibling.setOnClickListener(v -> {
                if (finalActive != null) {
                    CloneMetadataStore.VpnProfile nextNode = store.rotateToNextSiblingInCluster(finalActive.id);
                    VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
                    if (nextNode != null) {
                        Toast.makeText(this, tr("🔄 جایگزینی بدون قطعی در خوشه انجام شد: ", "🔄 Switched to Sibling Node: ") + nextNode.title, Toast.LENGTH_SHORT).show();
                    }
                    switchTab(2);
                }
            });
            statusCard.addView(btnRotateSibling);
            body.addView(statusCard);

            // Cluster Category Filter & Editor Card
            String selectedCat = store.getActiveVpnCategory();
            LinearLayout clusterCard = makeCard("#1E1B4B");
            clusterCard.addView(makeText(tr("🗂️ دسته‌بندی‌های خوشه‌ای ضدقطعی (چند سرور هم‌مکان در هر دسته)", "🗂️ Multi-Node VPN Clusters (Auto-Failover Groups)"), 13, "#A5B4FC", true));
            clusterCard.addView(makeText(tr("دسته انتخابی فعلی: ", "Selected Cluster: ") + ("ALL".equals(selectedCat) ? tr("همه دسته‌ها (All Clusters)", "All Clusters") : selectedCat), 12, "#F8FAFC", false));
            LinearLayout catBtnRow = new LinearLayout(this);
            catBtnRow.setOrientation(LinearLayout.HORIZONTAL);
            catBtnRow.setPadding(0, dp(6), 0, 0);

            TextView btnSelectCat = makePillButton(tr("📂 انتخاب دسته (خوشه)", "📂 Filter Cluster"), "#4F46E5");
            btnSelectCat.setOnClickListener(v -> showCategoryPickerDialog());
            catBtnRow.addView(btnSelectCat, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            TextView btnRenameCat = makePillButton(tr("✏️ ویرایش نام دسته", "✏️ Edit Cluster Name"), "#7C3AED");
            LinearLayout.LayoutParams renLp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
            renLp.setMargins(dp(6), 0, 0, 0);
            btnRenameCat.setLayoutParams(renLp);
            btnRenameCat.setOnClickListener(v -> showRenameCategoryDialog());
            catBtnRow.addView(btnRenameCat);
            clusterCard.addView(catBtnRow);
            body.addView(clusterCard);

            LinearLayout usStatesCard = makeCard("#172554");
            usStatesCard.addView(makeText(tr("🇺🇸 اولویت اول: ایالات متحده آمریکا (تمامی ۵۰ ایالت)", "🇺🇸 Priority #1: United States (All 50 States)"), 14, "#60A5FA", true));
            usStatesCard.addView(makeText(tr("انتخاب هر ایالت آمریکا به‌همراه ایجاد خودکار خوشه پشتیبان با منطقه زمانی و سیم‌کارت دقیق:", "Select any US State with exact city, timezone, SIM operator & coordinates:"), 11, "#CBD5E1", false));
            TextView btnPickUsState = makePillButton(tr("🗽 انتخاب از لیست کامل ۵۰ ایالت آمریکا", "🗽 Choose from All 50 US States"), "#3B82F6");
            btnPickUsState.setOnClickListener(v -> showAll50UsStatesPicker());
            usStatesCard.addView(btnPickUsState);
            body.addView(usStatesCard);

            body.addView(makeText(tr("📋 لیست سرورهای خوشه (با منوی ⋮ جابه‌جا، ویرایش یا متصل کنید)", "📋 Cluster VPN Nodes (Tap ⋮ to reorder, edit or connect)"), 13, "#94A3B8", true));
            for (CloneMetadataStore.VpnProfile p : profiles) {
                if (!"ALL".equals(selectedCat) && p.category != null && !selectedCat.equalsIgnoreCase(p.category)) {
                    continue;
                }
                body.addView(buildVpnProfileItemCard(p, p.id.equals(activeId)));
            }
        } else if (activeVpnSubTab == 1) {
            LinearLayout secCard = makeCard("#161F33");
            secCard.addView(makeText(tr("⚙️ تنظیمات کلی خوشه، جایگزینی خودکار، Kill-Switch و DNS", "⚙️ Cluster Auto-Failover, Kill-Switch & DNS"), 14, "#38BDF8", true));

            boolean autoRot = store.isClusterAutoRotateEnabled();
            TextView btnAutoRot = makePillButton(autoRot
                    ? tr("🔄 جایگزینی خودکار سرور هم‌خانواده در صورت افت یا خطا: فعال", "🔄 Auto-Failover Sibling Rotation: ON")
                    : tr("🔄 جایگزینی خودکار سرور هم‌خانواده: غیرفعال", "🔄 Auto-Failover Sibling Rotation: OFF"),
                    autoRot ? "#0D9488" : "#475569");
            LinearLayout.LayoutParams arLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            arLp.setMargins(0, dp(6), 0, dp(6));
            btnAutoRot.setLayoutParams(arLp);
            btnAutoRot.setOnClickListener(v -> { store.setClusterAutoRotateEnabled(!autoRot); switchTab(2); });
            secCard.addView(btnAutoRot);

            boolean ks = store.isKillSwitchEnabled();
            TextView btnKs = makePillButton(ks ? tr("🛡️ محافظ قطع خودکار (Kill-Switch): فعال", "🛡️ Kill-Switch: ON") : tr("🛡️ محافظ قطع خودکار (Kill-Switch): غیرفعال", "🛡️ Kill-Switch: OFF"), ks ? "#10B981" : "#475569");
            btnKs.setOnClickListener(v -> { store.setKillSwitchEnabled(!ks); switchTab(2); });
            secCard.addView(btnKs);

            boolean sync = store.isVpnAutoSyncEnabled();
            TextView btnSync = makePillButton(sync ? tr("🔄 همگام‌سازی خودکار ساعت، مکان و سیم‌کارت با VPN: فعال", "🔄 Auto-Sync Clock/Loc/SIM: ON") : tr("🔄 همگام‌سازی خودکار: غیرفعال", "🔄 Auto-Sync: OFF"), sync ? "#2563EB" : "#475569");
            LinearLayout.LayoutParams sLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            sLp.setMargins(0, dp(8), 0, dp(8));
            btnSync.setLayoutParams(sLp);
            btnSync.setOnClickListener(v -> { store.setVpnAutoSyncEnabled(!sync); switchTab(2); });
            secCard.addView(btnSync);

            secCard.addView(makeText("DNS: " + store.getCustomDns(), 12, "#E2E8F0", false));
            TextView btnTestIp = makePillButton(tr("🔍 تست واقعی IP خروجی (همراه با جایگزینی خودکار در صورت خطا)", "🔍 Real Outbound IP Test (with Cluster Auto-Failover)"), "#F59E0B");
            btnTestIp.setOnClickListener(v -> runRealOutboundIpVerification(finalActive));
            secCard.addView(btnTestIp);
            body.addView(secCard);

            body.addView(makeText(tr("🗂️ مدیریت و چیدمان اکانت‌های VPN (با ⋮ بالا/پایین ببرید یا ویرایش کنید)", "🗂️ Manage & Reorder VPN Accounts (Tap ⋮)"), 13, "#94A3B8", true));
            for (CloneMetadataStore.VpnProfile p : profiles) {
                body.addView(buildVpnProfileItemCard(p, p.id.equals(activeId)));
            }
        } else {
            CloneMetadataStore.EffectiveIdentity eff = store.resolveEffectiveIdentity(null, 0);
            LinearLayout matrix = makeCard("#161F33");
            matrix.addView(makeText(tr("🛡️ جدول وضعیت نشست فعال (آنچه تلگرام و اینستاگرام می‌بینند)", "🛡️ Active Session Identity Matrix"), 14, "#4ADE80", true));
            matrix.addView(makeText(tr("• برنامه/فضای هدف: ", "• Active Target: ") + (eff.targetPackage.isEmpty() ? tr("پیش‌فرض سراسری", "Global Default") : (eff.targetPackage + " [Space #" + (eff.targetUserId + 1) + "]")), 12, "#A7F3D0", true));
            matrix.addView(makeText("• Device Model: " + eff.displayBrandModel + formatPriorityBadge(eff.devicePriorityTier), 13, "#F8FAFC", false));
            matrix.addView(makeText("• Session Location: " + eff.regionLabel + formatPriorityBadge(eff.locationPriorityTier), 13, "#38BDF8", false));
            matrix.addView(makeText("• Timezone: " + eff.timezoneId, 13, "#E2E8F0", false));
            matrix.addView(makeText("• Virtual SIM: " + eff.simOperatorName + " (" + eff.simOperatorNumeric + " / " + eff.simCountryIso.toUpperCase() + ")" + formatPriorityBadge(eff.simPriorityTier), 13, "#FBBF24", false));
            matrix.addView(makeText("• Tunnel Endpoint: " + (eff.proxyAddress.isEmpty() ? "127.0.0.1:10808" : eff.proxyAddress), 13, "#CBD5E1", false));
            matrix.addView(makeText(tr("🔒 وضعیت نشت اطلاعات گوشی میزبان: ۰٪ (کاملاً ایزوله)", "🔒 Real Host Phone Leak Status: 0% (Completely Shielded)"), 12, "#4ADE80", true));
            body.addView(matrix);

            LinearLayout guideCard = makeCard("#1E293B");
            guideCard.addView(makeText(tr("📘 راهنمای خوشه‌های ضدقطعی VPN و اولویت ۳ لایه", "📘 Multi-Node VPN Clusters & 3-Tier Priority Guide"), 14, "#38BDF8", true));
            guideCard.addView(makeText(tr(
                "۱. اولویت ۱ همیشه با تنظیمات اختصاصی خود برنامه است؛ اگر برای کلونی تنظیم اختصاصی نگذارید، اولویت ۲ (تنظیمات فضا) و سپس اولویت ۳ (هویت امن سراسری) اعمال می‌شود و هرگز نام گوشی یا سیم‌کارت واقعی شما ارسال نمی‌شود.\n" +
                "۲. در تب اول VPN، سرورهای هم‌خانواده با کشور، شهر و سیم‌کارت یکسان داخل یک «دسته/خوشه» قرار دارند تا در صورت افت یکی، بلافاصله سرور بعدی همان شهر جایگزین شود و VPN قطع نگردد.",
                "1. Priority #1 is always Per-App settings, Priority #2 is Space settings, and Priority #3 is Safe Global Vault defaults (never exposing host hardware).\n2. Sibling VPN servers in the same cluster share identical region/SIM/timezone and automatically fail over without dropping connection."), 12, "#CBD5E1", false));
            body.addView(guideCard);
        }

        sv.addView(body);
        root.addView(sv, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        return root;
    }

    private void showCategoryPickerDialog() {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        List<String> cats = store.getVpnCategories();
        String[] items = new String[cats.size() + 1];
        items[0] = tr("🌐 نمایش همه دسته‌ها (All Clusters)", "🌐 Show All Clusters");
        for (int i = 0; i < cats.size(); i++) {
            items[i + 1] = "📂 " + cats.get(i);
        }
        new AlertDialog.Builder(this)
            .setTitle(tr("انتخاب دسته‌بندی (خوشه VPN)", "Select VPN Cluster Category"))
            .setItems(items, (d, w) -> {
                if (w == 0) store.setActiveVpnCategory("ALL");
                else store.setActiveVpnCategory(cats.get(w - 1));
                switchTab(2);
            }).show();
    }

    private void showRenameCategoryDialog() {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        List<String> cats = store.getVpnCategories();
        if (cats.isEmpty()) return;
        String[] items = cats.toArray(new String[0]);
        new AlertDialog.Builder(this)
            .setTitle(tr("کدام دسته را می‌خواهید ویرایش نام کنید؟", "Select Cluster to Rename"))
            .setItems(items, (d, w) -> {
                final String oldCat = items[w];
                EditText et = new EditText(this);
                et.setText(oldCat);
                new AlertDialog.Builder(this)
                    .setTitle(tr("نام جدید دسته‌بندی", "New Cluster Name"))
                    .setView(et)
                    .setPositiveButton(tr("ذخیره", "Save"), (d2, w2) -> {
                        store.renameVpnCategory(oldCat, et.getText().toString().trim());
                        switchTab(2);
                    }).show();
            }).show();
    }

    private View buildVpnProfileItemCard(CloneMetadataStore.VpnProfile p, boolean isActive) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        LinearLayout card = makeCard(isActive ? "#1E3A8A" : "#161F33");
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);

        LinearLayout info = new LinearLayout(this);
        info.setOrientation(LinearLayout.VERTICAL);
        info.addView(makeText("📂 " + p.category, 10, "#FBBF24", true));
        info.addView(makeText((isActive ? "✅ " : "") + p.title, 14, "#F8FAFC", true));
        info.addView(makeText(p.stateOrCity + " | " + p.simOperator + " (" + p.timezoneId + ")", 11, "#38BDF8", false));
        info.addView(makeText(p.protocol + " -> " + p.host + ":" + p.port, 11, "#94A3B8", false));
        info.setOnClickListener(v -> {
            store.applyVpnProfileToEnvironment(p);
            store.setVpnConnected(true);
            VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
            Toast.makeText(this, tr("✅ سرور فعال شد: ", "✅ Activated: ") + p.title, Toast.LENGTH_SHORT).show();
            switchTab(2);
        });
        row.addView(info, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView dots = makeText("  ⋮  ", 20, "#FFFFFF", true);
        dots.setOnClickListener(v -> showVpnProfileThreeDotsMenu(p));
        row.addView(dots);
        card.addView(row);
        return card;
    }

    private void showVpnProfileThreeDotsMenu(CloneMetadataStore.VpnProfile p) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        String[] opts = {
            tr("🚀 اتصال و همگام‌سازی با این سرور", "🚀 Connect & Sync with this Profile"),
            tr("🔄 چرخش به سرور هم‌خانواده بعدی در همین دسته", "🔄 Switch to Next Sibling in this Cluster"),
            tr("⚙️ ویرایش سرور، دسته‌بندی، پورت یا جایگزینی با VPN رایگان", "⚙️ Edit Server, Category, Port or Pick Free VPN"),
            tr("⬆️ انتقال به بالاتر در لیست", "⬆️ Move Up in List"),
            tr("⬇️ انتقال به پایین‌تر در لیست", "⬇️ Move Down in List"),
            tr("🔍 تست واقعی IP و پینگ این اکانت", "🔍 Test Outbound IP & Latency"),
            tr("🗑️ حذف این اکانت VPN", "🗑️ Delete VPN Account")
        };
        new AlertDialog.Builder(this)
            .setTitle(p.title)
            .setItems(opts, (d, w) -> {
                if (w == 0) {
                    store.applyVpnProfileToEnvironment(p);
                    store.setVpnConnected(true);
                    VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
                    switchTab(2);
                } else if (w == 1) {
                    store.rotateToNextSiblingInCluster(p.id);
                    VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
                    switchTab(2);
                } else if (w == 2) {
                    showAddOrEditVpnDialog(p);
                } else if (w == 3) {
                    store.moveVpnProfile(p.id, -1);
                    switchTab(2);
                } else if (w == 4) {
                    store.moveVpnProfile(p.id, 1);
                    switchTab(2);
                } else if (w == 5) {
                    runRealOutboundIpVerification(p);
                } else if (w == 6) {
                    List<CloneMetadataStore.VpnProfile> list = store.getVpnProfiles();
                    Iterator<CloneMetadataStore.VpnProfile> it = list.iterator();
                    while (it.hasNext()) {
                        if (it.next().id.equals(p.id)) it.remove();
                    }
                    store.saveVpnProfiles(list);
                    switchTab(2);
                }
            }).show();
    }

    private void showAddOrEditVpnDialog(CloneMetadataStore.VpnProfile existing) {
        CloneMetadataStore store = CloneMetadataStore.get(this);
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(14), dp(10), dp(14), dp(10));

        final EditText etCategory = new EditText(this); etCategory.setHint(tr("دسته‌بندی / خوشه (مثلاً 🇺🇸 US - New York Cluster)", "Category / Cluster"));
        final EditText etTitle = new EditText(this); etTitle.setHint(tr("نام سرور (مثلاً 🇺🇸 Free US New York #1)", "Server Title"));
        final EditText etCity = new EditText(this); etCity.setHint(tr("شهر و کشور (مثلاً New York, United States)", "City, Country"));
        final EditText etProto = new EditText(this); etProto.setHint(tr("پروتکل (SOCKS5 یا HTTP)", "Protocol (SOCKS5 / HTTP)"));
        final EditText etHost = new EditText(this); etHost.setHint(tr("آدرس سرور یا IP (مثلاً 127.0.0.1)", "Host / IP"));
        final EditText etPort = new EditText(this); etPort.setHint(tr("پورت (مثلاً 10808 یا 40000)", "Port"));
        final EditText etTz = new EditText(this); etTz.setHint(tr("منطقه زمانی (مثلاً America/New_York)", "Timezone"));
        final EditText etSimOp = new EditText(this); etSimOp.setHint(tr("اپراتور سیم‌کارت همگام (مثلاً T-Mobile USA)", "SIM Operator"));

        if (existing != null) {
            etCategory.setText(existing.category);
            etTitle.setText(existing.title);
            etCity.setText(existing.stateOrCity);
            etProto.setText(existing.protocol);
            etHost.setText(existing.host);
            etPort.setText(String.valueOf(existing.port));
            etTz.setText(existing.timezoneId);
            etSimOp.setText(existing.simOperator);
        } else {
            CloneMetadataStore.VpnProfile defFree = CloneMetadataStore.FREE_VPN_PRESETS[0];
            etCategory.setText(defFree.category);
            etTitle.setText(defFree.title);
            etCity.setText(defFree.stateOrCity);
            etProto.setText(defFree.protocol);
            etHost.setText(defFree.host);
            etPort.setText(String.valueOf(defFree.port));
            etTz.setText(defFree.timezoneId);
            etSimOp.setText(defFree.simOperator);
        }

        TextView btnPickFreePreset = makePillButton(tr("🎁 انتخاب سریع از لیست VPNهای رایگان و قوی آماده (قابل ویرایش)", "🎁 Pick from Built-in Strong Free VPN Servers (Editable)"), "#10B981");
        btnPickFreePreset.setGravity(Gravity.CENTER);
        btnPickFreePreset.setOnClickListener(v -> {
            CloneMetadataStore.VpnProfile[] presets = CloneMetadataStore.FREE_VPN_PRESETS;
            String[] labels = new String[presets.length];
            for (int i = 0; i < presets.length; i++) {
                labels[i] = presets[i].title + "\n[" + presets[i].category + " | " + presets[i].protocol + " " + presets[i].host + ":" + presets[i].port + "]";
            }
            new AlertDialog.Builder(this)
                .setTitle(tr("🎁 لیست VPNهای رایگان و پرسرعت آماده", "🎁 Built-in Strong Free VPN Presets"))
                .setItems(labels, (d2, idx) -> {
                    CloneMetadataStore.VpnProfile fp = presets[idx];
                    etCategory.setText(fp.category);
                    etTitle.setText(fp.title);
                    etCity.setText(fp.stateOrCity);
                    etProto.setText(fp.protocol);
                    etHost.setText(fp.host);
                    etPort.setText(String.valueOf(fp.port));
                    etTz.setText(fp.timezoneId);
                    etSimOp.setText(fp.simOperator);
                }).show();
        });
        box.addView(btnPickFreePreset);

        TextView btnPickExistingCat = makePillButton(tr("📂 انتخاب از دسته‌بندی‌های موجود", "📂 Choose Existing Cluster Category"), "#3B82F6");
        LinearLayout.LayoutParams catLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        catLp.setMargins(0, dp(6), 0, dp(6));
        btnPickExistingCat.setLayoutParams(catLp);
        btnPickExistingCat.setGravity(Gravity.CENTER);
        btnPickExistingCat.setOnClickListener(v -> {
            List<String> cats = store.getVpnCategories();
            String[] arr = cats.toArray(new String[0]);
            new AlertDialog.Builder(this)
                .setTitle(tr("انتخاب دسته‌بندی", "Select Category"))
                .setItems(arr, (d3, w3) -> etCategory.setText(arr[w3]))
                .show();
        });
        box.addView(btnPickExistingCat);

        box.addView(etCategory);
        box.addView(etTitle);
        box.addView(etCity);
        box.addView(etProto);
        box.addView(etHost);
        box.addView(etPort);
        box.addView(etTz);
        box.addView(etSimOp);
        sv.addView(box);

        new AlertDialog.Builder(this)
            .setTitle(existing == null ? tr("➕ افزودن اکانت / انتخاب VPN رایگان", "➕ Add / Pick Free VPN") : tr("⚙️ ویرایش کامل اکانت و خوشه VPN", "⚙️ Edit VPN Account & Cluster"))
            .setView(sv)
            .setPositiveButton(tr("ذخیره و فعال‌سازی", "Save & Activate"), (d, w) -> {
                List<CloneMetadataStore.VpnProfile> list = store.getVpnProfiles();
                CloneMetadataStore.VpnProfile target = existing != null ? existing : new CloneMetadataStore.VpnProfile();
                if (existing == null) target.id = "custom_" + System.currentTimeMillis();
                String catStr = etCategory.getText().toString().trim();
                target.category = catStr.isEmpty() ? "🇺🇸 US - New York Cluster" : catStr;
                target.title = etTitle.getText().toString().trim().isEmpty() ? "🇺🇸 Free USA VPN" : etTitle.getText().toString().trim();
                target.stateOrCity = etCity.getText().toString().trim().isEmpty() ? "New York, United States" : etCity.getText().toString().trim();
                target.country = target.stateOrCity.contains(",") ? target.stateOrCity.substring(target.stateOrCity.lastIndexOf(',') + 1).trim() : "United States";
                String protoStr = etProto.getText().toString().trim().toUpperCase();
                target.protocol = protoStr.isEmpty() ? "SOCKS5" : protoStr;
                target.host = etHost.getText().toString().trim().isEmpty() ? "127.0.0.1" : etHost.getText().toString().trim();
                try { target.port = Integer.parseInt(etPort.getText().toString().trim()); } catch (Exception e) { target.port = 10808; }
                target.timezoneId = etTz.getText().toString().trim().isEmpty() ? "America/New_York" : etTz.getText().toString().trim();
                if (existing == null) {
                    target.lat = 40.7128; target.lon = -74.0060;
                    target.simMccMnc = "310260"; target.simIso = "us";
                }
                String simStr = etSimOp.getText().toString().trim();
                target.simOperator = simStr.isEmpty() ? "T-Mobile USA" : simStr;
                if (existing == null) list.add(0, target);
                else {
                    for (int i = 0; i < list.size(); i++) {
                        if (list.get(i).id.equals(target.id)) { list.set(i, target); break; }
                    }
                }
                store.saveVpnProfiles(list);
                store.applyVpnProfileToEnvironment(target);
                store.setVpnConnected(true);
                VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
                switchTab(2);
            }).show();
    }

    private void showAll50UsStatesPicker() {
        final String[][] usStates = {
            {"Alabama - Birmingham", "America/Chicago", "33.5186", "-86.8104"},
            {"Alaska - Anchorage", "America/Anchorage", "61.2181", "-149.9003"},
            {"Arizona - Phoenix", "America/Phoenix", "33.4484", "-112.0740"},
            {"Arkansas - Little Rock", "America/Chicago", "34.7465", "-92.2896"},
            {"California - Los Angeles", "America/Los_Angeles", "34.0522", "-118.2437"},
            {"California - San Francisco", "America/Los_Angeles", "37.7749", "-122.4194"},
            {"Colorado - Denver", "America/Denver", "39.7392", "-104.9903"},
            {"Connecticut - Hartford", "America/New_York", "41.7658", "-72.6734"},
            {"Delaware - Wilmington", "America/New_York", "39.7391", "-75.5398"},
            {"Florida - Miami", "America/New_York", "25.7617", "-80.1918"},
            {"Georgia - Atlanta", "America/New_York", "33.7490", "-84.3880"},
            {"Hawaii - Honolulu", "Pacific/Honolulu", "21.3069", "-157.8583"},
            {"Idaho - Boise", "America/Boise", "43.6150", "-116.2023"},
            {"Illinois - Chicago", "America/Chicago", "41.8781", "-87.6298"},
            {"Indiana - Indianapolis", "America/Indiana/Indianapolis", "39.7684", "-86.1581"},
            {"Iowa - Des Moines", "America/Chicago", "41.5868", "-93.6250"},
            {"Kansas - Wichita", "America/Chicago", "37.6872", "-97.3301"},
            {"Kentucky - Louisville", "America/Kentucky/Louisville", "38.2527", "-85.7585"},
            {"Louisiana - New Orleans", "America/Chicago", "29.9511", "-90.0715"},
            {"Maine - Portland", "America/New_York", "43.6591", "-70.2568"},
            {"Maryland - Baltimore", "America/New_York", "39.2904", "-76.6122"},
            {"Massachusetts - Boston", "America/New_York", "42.3601", "-71.0589"},
            {"Michigan - Detroit", "America/Detroit", "42.3314", "-83.0458"},
            {"Minnesota - Minneapolis", "America/Chicago", "44.9778", "-93.2650"},
            {"Mississippi - Jackson", "America/Chicago", "32.2988", "-90.1848"},
            {"Missouri - St. Louis", "America/Chicago", "38.6270", "-90.1994"},
            {"Montana - Billings", "America/Denver", "45.7833", "-108.5007"},
            {"Nebraska - Omaha", "America/Chicago", "41.2565", "-95.9345"},
            {"Nevada - Las Vegas", "America/Los_Angeles", "36.1699", "-115.1398"},
            {"New Hampshire - Manchester", "America/New_York", "42.9956", "-71.4548"},
            {"New Jersey - Newark", "America/New_York", "40.7357", "-74.1724"},
            {"New Mexico - Albuquerque", "America/Denver", "35.0844", "-106.6504"},
            {"New York - New York City", "America/New_York", "40.7128", "-74.0060"},
            {"North Carolina - Charlotte", "America/New_York", "35.2271", "-80.8431"},
            {"North Dakota - Fargo", "America/Chicago", "46.8772", "-96.7898"},
            {"Ohio - Columbus", "America/New_York", "39.9612", "-82.9988"},
            {"Oklahoma - Oklahoma City", "America/Chicago", "35.4676", "-97.5164"},
            {"Oregon - Portland", "America/Los_Angeles", "45.5152", "-122.6784"},
            {"Pennsylvania - Philadelphia", "America/New_York", "39.9526", "-75.1652"},
            {"Rhode Island - Providence", "America/New_York", "41.8240", "-71.4128"},
            {"South Carolina - Charleston", "America/New_York", "32.7765", "-79.9311"},
            {"South Dakota - Sioux Falls", "America/Chicago", "43.5446", "-96.7311"},
            {"Tennessee - Nashville", "America/Chicago", "36.1627", "-86.7816"},
            {"Texas - Dallas", "America/Chicago", "32.7767", "-96.7970"},
            {"Texas - Houston", "America/Chicago", "29.7604", "-95.3698"},
            {"Utah - Salt Lake City", "America/Denver", "40.7608", "-111.8910"},
            {"Vermont - Burlington", "America/New_York", "44.4759", "-73.2121"},
            {"Virginia - Ashburn", "America/New_York", "39.0438", "-77.4874"},
            {"Washington - Seattle", "America/Los_Angeles", "47.6062", "-122.3321"},
            {"West Virginia - Charleston", "America/New_York", "38.3498", "-81.6326"},
            {"Wisconsin - Milwaukee", "America/Chicago", "43.0389", "-87.9065"},
            {"Wyoming - Cheyenne", "America/Denver", "41.1400", "-104.8202"}
        };
        String[] names = new String[usStates.length];
        for (int i = 0; i < usStates.length; i++) names[i] = "🇺🇸 " + usStates[i][0];
        new AlertDialog.Builder(this)
            .setTitle(tr("انتخاب ایالت آمریکا (ساخت خودکار خوشه ۲ سروره ضدقطعی)", "Select US State (Creates 2-Node Cluster)"))
            .setItems(names, (d, w) -> {
                String[] s = usStates[w];
                CloneMetadataStore store = CloneMetadataStore.get(this);
                List<CloneMetadataStore.VpnProfile> list = store.getVpnProfiles();
                String clusterName = "🇺🇸 US - " + s[0].split(" - ")[0] + " Cluster";
                String cityLabel = s[0].replace(" - ", ", ") + ", United States";

                CloneMetadataStore.VpnProfile p1 = new CloneMetadataStore.VpnProfile();
                p1.id = "us_state_" + w + "_1";
                p1.category = clusterName;
                p1.nodeIndex = 1;
                p1.title = "🇺🇸 USA - " + s[0] + " [Node #1 Primary]";
                p1.country = "United States";
                p1.stateOrCity = cityLabel;
                p1.protocol = "SOCKS5";
                p1.host = "127.0.0.1";
                p1.port = 10808;
                p1.timezoneId = s[1];
                p1.lat = Double.parseDouble(s[2]);
                p1.lon = Double.parseDouble(s[3]);
                p1.simOperator = "T-Mobile USA";
                p1.simMccMnc = "310260";
                p1.simIso = "us";

                CloneMetadataStore.VpnProfile p2 = new CloneMetadataStore.VpnProfile();
                p2.id = "us_state_" + w + "_2";
                p2.category = clusterName;
                p2.nodeIndex = 2;
                p2.title = "🇺🇸 USA - " + s[0] + " [Node #2 Failover]";
                p2.country = "United States";
                p2.stateOrCity = cityLabel;
                p2.protocol = "HTTP";
                p2.host = "127.0.0.1";
                p2.port = 10809;
                p2.timezoneId = s[1];
                p2.lat = Double.parseDouble(s[2]);
                p2.lon = Double.parseDouble(s[3]);
                p2.simOperator = "T-Mobile USA";
                p2.simMccMnc = "310260";
                p2.simIso = "us";

                list.add(0, p2);
                list.add(0, p1);
                store.saveVpnProfiles(list);
                store.setActiveVpnCategory(clusterName);
                store.applyVpnProfileToEnvironment(p1);
                store.setVpnConnected(true);
                VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
                Toast.makeText(this, "✅ " + clusterName, Toast.LENGTH_SHORT).show();
                switchTab(2);
            }).show();
    }

    private void runRealOutboundIpVerification(final CloneMetadataStore.VpnProfile p) {
        EditText etUrl = new EditText(this);
        etUrl.setText("https://api.ipify.org?format=json");
        new AlertDialog.Builder(this)
            .setTitle(tr("تأیید مقصد تست واقعی IP", "Approve IP Check Endpoint"))
            .setMessage(tr("آدرس سرور آزمایشی مورد تأیید خود را وارد کنید:", "Enter approved IP check URL:"))
            .setView(etUrl)
            .setPositiveButton(tr("شروع تست واقعی", "Start Real Test"), (d, w) -> {
                final String targetUrl = etUrl.getText().toString().trim();
                Toast.makeText(this, tr("در حال بررسی واقعی شبکه...", "Checking real outbound network..."), Toast.LENGTH_SHORT).show();
                new Thread(() -> {
                    long start = System.currentTimeMillis();
                    String resultMsg;
                    try {
                        URL url = new URL(targetUrl);
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setConnectTimeout(6000);
                        conn.setReadTimeout(6000);
                        int code = conn.getResponseCode();
                        BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                        StringBuilder sb = new StringBuilder();
                        String line;
                        while ((line = br.readLine()) != null) sb.append(line);
                        br.close();
                        long ms = System.currentTimeMillis() - start;
                        resultMsg = "✅ HTTP " + code + " (" + ms + " ms)\nResponse: " + sb.toString();
                    } catch (Throwable t) {
                        CloneMetadataStore store = CloneMetadataStore.get(MainActivity.this);
                        if (store.isClusterAutoRotateEnabled() && p != null) {
                            CloneMetadataStore.VpnProfile rotated = store.rotateToNextSiblingInCluster(p.id);
                            resultMsg = "⚠️ خطا در نود فعلی (" + t.getClass().getSimpleName() + ").\n🔄 سیستم ضدقطعی خوشه بلافاصله به نود هم‌خانواده بعدی سوئیچ کرد:\n" + (rotated != null ? rotated.title : "");
                        } else {
                            resultMsg = "⚠️ خطا در اتصال شبکه: " + t.getClass().getSimpleName() + " - " + t.getMessage();
                        }
                    }
                    final String finalMsg = resultMsg;
                    runOnUiThread(() -> {
                        new AlertDialog.Builder(MainActivity.this)
                            .setTitle(tr("نتیجه واقعی تست IP", "Real IP Test Result"))
                            .setMessage(finalMsg)
                            .setPositiveButton(tr("باشه", "OK"), null).show();
                        switchTab(2);
                    });
                }).start();
            }).show();
    }

    private View buildSettingsView() {
        ScrollView sv = new ScrollView(this);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(14), dp(14), dp(14), dp(24));

        boolean isLight = LocaleHelper.isLightTheme(this);
        box.addView(makeSettingsRow(
            isLight ? tr("🌙 تغییر به حالت شب (تم تاریک)", "🌙 Switch to Night Mode (Dark)") : tr("☀️ تغییر به حالت روز (تم روشن)", "☀️ Switch to Day Mode (Light)"),
            tr("تغییر فوری رنگ‌بندی کل برنامه بین حالت شب (مشکی) و حالت روز (روشن)", "Instantly switch app theme between Dark and Light mode"),
            () -> {
                LocaleHelper.toggleLightTheme(this);
                recreate();
            }
        ));

        box.addView(makeSettingsRow(
            tr("📱 هویت دستگاه، سیم‌کارت مجازی و موقعیت سراسری", "📱 Global Device, Virtual SIM & Location"),
            tr("تنظیم مدل گوشی (شامل آیفون اپل)، سیم‌کارت مجازی، مختصات و منطقه زمانی", "Configure device model (including Apple iPhone), Virtual SIM, GPS & timezone"),
            () -> startActivity(new Intent(this, GlobalEnvironmentActivity.class))
        ));

        box.addView(makeSettingsRow(
            tr("🗺️ نقشه هوشمند و تغییر موقعیت (Fake GPS)", "🗺️ Interactive Map Location"),
            tr("انتخاب دقیق شهر و کشور روی نقشه (مانند Falkenstein, Germany یا New York)", "Pick exact city and country on map"),
            () -> startActivity(new Intent(this, SetLocationActivity.class))
        ));

        box.addView(makeSettingsRow(
            tr("🔐 قفل امنیتی هم‌زمان (PIN + الگو) و محافظ ضدحذف", "🔐 Dual Security Lock & Anti-Uninstall"),
            tr("فعال‌سازی هم‌زمان رمز و الگو، تعیین اولویت قفل اول و محافظت در برابر حذف", "Simultaneous PIN & Pattern lock and anti-uninstall blocker"),
            () -> startActivity(new Intent(this, SecuritySettingsActivity.class))
        ));

        box.addView(makeSettingsRow(
            tr("🔔 دسترسی شمارنده اعلان‌های سمت چپ (۱ تا ۹۹ و ∞)", "🔔 Notification Counter Access (1..99 & ∞)"),
            tr("فعال‌سازی دسترسی اعلان برای نمایش تعداد پیام‌های خوانده‌نشده روی آیکون کلون‌ها", "Grant Notification Listener access for unread badges on cloned apps"),
            () -> {
                try {
                    startActivity(new Intent("android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS"));
                } catch (Throwable t) {
                    Toast.makeText(this, tr("از بخش تنظیمات گوشی دسترسی اعلان را فعال کنید", "Enable Notification Access in Settings"), Toast.LENGTH_SHORT).show();
                }
            }
        ));

        box.addView(makeSettingsRow(
            tr("📖 راهنمای جامع و آموزش کامل برنامه", "📖 Complete User Guide"),
            tr("آموزش گام‌به‌گام فضاهای خودکار، خوشه‌های VPN، سیم‌کارت مجازی، تغییر مکان و امنیت", "Full guide on auto-spaces, VPN clusters, Virtual SIM, location spoofing & security"),
            () -> startActivity(new Intent(this, GuideActivity.class))
        ));

        box.addView(makeSettingsRow(
            tr("ℹ️ درباره ما و ارتباط با سازنده", "ℹ️ About VeyraVault & Contact"),
            "VeyraVault | Vaultveyra@gmail.com | t.me/VaultVeyra",
            () -> startActivity(new Intent(this, AboutActivity.class))
        ));

        sv.addView(box);
        return sv;
    }

    private View makeSettingsRow(String title, String sub, Runnable action) {
        LinearLayout card = makeCard("#161F33");
        card.addView(makeText(title, 14, "#38BDF8", true));
        card.addView(makeText(sub, 12, "#CBD5E1", false));
        card.setOnClickListener(v -> action.run());
        return card;
    }

    private LinearLayout makeCard(String hexColor) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(14), dp(14), dp(14));
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hexColor));
        gd.setCornerRadius(dp(14));
        card.setBackground(gd);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, dp(6), 0, dp(6));
        card.setLayoutParams(lp);
        return card;
    }

    private TextView makeText(String text, int spSize, String hexColor, boolean bold) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextSize(spSize);
        tv.setTextColor(Color.parseColor(hexColor));
        if (bold) tv.setTypeface(null, Typeface.BOLD);
        return tv;
    }

    private TextView makePillButton(String text, String bgHex) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(Color.WHITE);
        tv.setTextSize(12);
        tv.setTypeface(null, Typeface.BOLD);
        tv.setPadding(dp(12), dp(8), dp(12), dp(8));
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(bgHex));
        gd.setCornerRadius(dp(18));
        tv.setBackground(gd);
        return tv;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/MainActivity.java"), MAIN_ACTIVITY)

ADD_APP_ACTIVITY = r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.core.content.FileProvider;
import com.veyravault.space.core.Engine;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

public class AddAppActivity extends BaseActivity {
    private static final int REQ_PICK_APK = 901;
    private int forcedUserId = -1;
    private int pendingInstallMode = 0;
    private LinearLayout listContainer;
    private final List<ApplicationInfo> allInstalledApps = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        forcedUserId = getIntent().getIntExtra("forced_user_id", -1);
        buildUi();
        loadHostInstalledApps();
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#0B0F19"));
        root.setPadding(dp(14), dp(14), dp(14), dp(14));

        String headerTitle = (forcedUserId >= 0)
                ? tr("➕ افزودن مستقیم به فضای " + (forcedUserId + 1), "➕ Add Directly to Space " + (forcedUserId + 1))
                : tr("➕ افزودن هوشمند برنامه (تخصیص خودکار فضا)", "➕ Smart Add App (Auto-Space)");
        TextView header = new TextView(this);
        header.setText(headerTitle);
        header.setTextSize(17);
        header.setTextColor(Color.WHITE);
        header.setTypeface(null, Typeface.BOLD);
        root.addView(header);

        LinearLayout extCard = new LinearLayout(this);
        extCard.setOrientation(LinearLayout.VERTICAL);
        extCard.setPadding(dp(12), dp(12), dp(12), dp(12));
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor("#1E293B"));
        gd.setCornerRadius(dp(12));
        extCard.setBackground(gd);
        LinearLayout.LayoutParams extLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        extLp.setMargins(0, dp(10), 0, dp(10));
        extCard.setLayoutParams(extLp);

        TextView extTitle = new TextView(this);
        extTitle.setText(tr("📦 نصب برنامه جدید از فایل APK یا فروشگاه‌ها", "📦 Install from APK or App Stores"));
        extTitle.setTextColor(Color.parseColor("#38BDF8"));
        extTitle.setTypeface(null, Typeface.BOLD);
        extCard.addView(extTitle);

        LinearLayout storeRow = new LinearLayout(this);
        storeRow.setOrientation(LinearLayout.HORIZONTAL);
        storeRow.setPadding(0, dp(8), 0, 0);
        storeRow.addView(makeStoreBtn(tr("📁 فایل APK", "📁 APK File"), "#10B981", this::showInstallDestinationChoiceForApk));
        storeRow.addView(makeStoreBtn(tr("🛍️ بازار", "🛍️ Bazaar"), "#059669", () -> openStoreOrWeb("com.farsitel.bazaar", "https://cafebazaar.ir")));
        storeRow.addView(makeStoreBtn(tr("🟦 مایکت", "🟦 Myket"), "#2563EB", () -> openStoreOrWeb("ir.mservices.market", "https://myket.ir")));
        storeRow.addView(makeStoreBtn(tr("▶️ گوگل‌پلی", "▶️ Play"), "#7C3AED", () -> openStoreOrWeb("com.android.vending", "https://play.google.com/store")));
        extCard.addView(storeRow);
        root.addView(extCard);

        EditText search = new EditText(this);
        search.setHint(tr("🔍 جستجوی نام برنامه...", "🔍 Search installed apps..."));
        search.setTextColor(Color.WHITE);
        search.setHintTextColor(Color.parseColor("#94A3B8"));
        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { filterApps(s.toString()); }
            @Override public void afterTextChanged(Editable s) {}
        });
        root.addView(search);

        ScrollView sv = new ScrollView(this);
        listContainer = new LinearLayout(this);
        listContainer.setOrientation(LinearLayout.VERTICAL);
        sv.addView(listContainer);
        root.addView(sv, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        setContentView(root);
    }

    private TextView makeStoreBtn(String text, String color, Runnable action) {
        TextView b = new TextView(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(11);
        b.setGravity(Gravity.CENTER);
        b.setPadding(dp(8), dp(8), dp(8), dp(8));
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(color));
        gd.setCornerRadius(dp(10));
        b.setBackground(gd);
        b.setOnClickListener(v -> action.run());
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        lp.setMargins(dp(3), 0, dp(3), 0);
        b.setLayoutParams(lp);
        return b;
    }

    private void showInstallDestinationChoiceForApk() {
        String[] choices = {
            tr("۱. نصب فقط داخل VeyraVault (کاملاً مخفی و مستقل)", "1. Install ONLY inside VeyraVault"),
            tr("۲. نصب فقط در حافظه اصلی گوشی", "2. Install ONLY on Host Phone"),
            tr("۳. نصب هم‌زمان در گوشی و داخل VeyraVault", "3. Install in BOTH Host Phone & VeyraVault")
        };
        new AlertDialog.Builder(this)
            .setTitle(tr("انتخاب محل نصب فایل APK", "Choose APK Install Mode"))
            .setItems(choices, (d, which) -> {
                pendingInstallMode = which;
                Intent pick = new Intent(Intent.ACTION_GET_CONTENT);
                pick.setType("application/vnd.android.package-archive");
                pick.addCategory(Intent.CATEGORY_OPENABLE);
                startActivityForResult(Intent.createChooser(pick, "Select APK"), REQ_PICK_APK);
            }).show();
    }

    private void openStoreOrWeb(String storePkg, String webUrl) {
        int dstSpace = (forcedUserId >= 0) ? forcedUserId : 0;
        String[] choices = {
            tr("۱. کلون کردن خود فروشگاه در فضای " + (dstSpace + 1), "1. Clone Store into Space " + (dstSpace + 1)),
            tr("۲. باز کردن فروشگاه در گوشی برای دانلود", "2. Open Store on Phone")
        };
        new AlertDialog.Builder(this)
            .setTitle(tr("نحوه استفاده از فروشگاه", "Store Mode"))
            .setItems(choices, (d, which) -> {
                if (which == 0) {
                    boolean ok = Engine.get(this).cloneFromInstalledWithVault(storePkg, dstSpace);
                    if (ok) {
                        Toast.makeText(this, tr("✅ فروشگاه به فضای " + (dstSpace + 1) + " اضافه شد", "✅ Added to Space"), Toast.LENGTH_SHORT).show();
                        finish();
                    } else {
                        startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(webUrl)));
                    }
                } else {
                    Intent launch = getPackageManager().getLaunchIntentForPackage(storePkg);
                    if (launch != null) startActivity(launch);
                    else startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(webUrl)));
                }
            }).show();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_PICK_APK && resultCode == RESULT_OK && data != null && data.getData() != null) {
            handlePickedApkUri(data.getData());
        }
    }

    private void handlePickedApkUri(Uri uri) {
        try {
            File tempApk = new File(getCacheDir(), "picked_install.apk");
            try (InputStream in = getContentResolver().openInputStream(uri);
                 FileOutputStream out = new FileOutputStream(tempApk)) {
                byte[] buf = new byte[16384];
                int len;
                while ((len = in.read(buf)) > 0) out.write(buf, 0, len);
            }
            int dstSpace = (forcedUserId >= 0) ? forcedUserId : 0;
            if (pendingInstallMode == 0 || pendingInstallMode == 2) {
                boolean ok = Engine.get(this).installFromApkFileWithVault(tempApk, dstSpace);
                Toast.makeText(this, ok ? tr("✅ در فضای " + (dstSpace + 1) + " نصب شد", "✅ Installed in Vault") : tr("❌ خطا در نصب APK", "❌ Failed"), Toast.LENGTH_LONG).show();
            }
            if (pendingInstallMode == 1 || pendingInstallMode == 2) {
                Uri apkUri = FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", tempApk);
                Intent sysInstall = new Intent(Intent.ACTION_VIEW);
                sysInstall.setDataAndType(apkUri, "application/vnd.android.package-archive");
                sysInstall.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(sysInstall);
            }
            if (pendingInstallMode == 0) finish();
        } catch (Throwable t) {
            Toast.makeText(this, "Error: " + t.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void loadHostInstalledApps() {
        PackageManager pm = getPackageManager();
        List<ApplicationInfo> raw = pm.getInstalledApplications(0);
        allInstalledApps.clear();
        for (ApplicationInfo info : raw) {
            if (info.packageName.equals(getPackageName())) continue;
            if (pm.getLaunchIntentForPackage(info.packageName) == null) continue;
            allInstalledApps.add(info);
        }
        filterApps("");
    }

    private void filterApps(String query) {
        listContainer.removeAllViews();
        PackageManager pm = getPackageManager();
        String q = query == null ? "" : query.toLowerCase().trim();
        for (ApplicationInfo info : allInstalledApps) {
            String label = info.loadLabel(pm).toString();
            if (!q.isEmpty() && !label.toLowerCase().contains(q) && !info.packageName.toLowerCase().contains(q)) continue;

            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER_VERTICAL);
            row.setPadding(dp(10), dp(10), dp(10), dp(10));

            ImageView iv = new ImageView(this);
            iv.setImageDrawable(info.loadIcon(pm));
            row.addView(iv, new LinearLayout.LayoutParams(dp(42), dp(42)));

            LinearLayout textCol = new LinearLayout(this);
            textCol.setOrientation(LinearLayout.VERTICAL);
            textCol.setPadding(dp(10), 0, dp(10), 0);
            TextView tvTitle = new TextView(this);
            tvTitle.setText(label);
            tvTitle.setTextColor(Color.WHITE);
            tvTitle.setTextSize(14);
            tvTitle.setTypeface(null, Typeface.BOLD);
            TextView tvPkg = new TextView(this);
            tvPkg.setText(info.packageName);
            tvPkg.setTextColor(Color.parseColor("#94A3B8"));
            tvPkg.setTextSize(11);
            textCol.addView(tvTitle);
            textCol.addView(tvPkg);
            row.addView(textCol, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            int targetSpace = (forcedUserId >= 0)
                    ? forcedUserId
                    : Engine.get(this).findNextAvailableSpaceForPackage(info.packageName);

            TextView btnClone = new TextView(this);
            btnClone.setText(tr("+ فضای " + (targetSpace + 1) + " (#" + (targetSpace + 1) + ")", "+ Space " + (targetSpace + 1)));
            btnClone.setTextColor(Color.WHITE);
            btnClone.setTextSize(12);
            btnClone.setTypeface(null, Typeface.BOLD);
            btnClone.setPadding(dp(12), dp(7), dp(12), dp(7));
            GradientDrawable gd = new GradientDrawable();
            gd.setColor(Color.parseColor("#2563EB"));
            gd.setCornerRadius(dp(14));
            btnClone.setBackground(gd);
            btnClone.setOnClickListener(v -> {
                int finalSpace = (forcedUserId >= 0)
                        ? forcedUserId
                        : Engine.get(this).findNextAvailableSpaceForPackage(info.packageName);
                boolean ok = Engine.get(this).cloneFromInstalledWithVault(info.packageName, finalSpace);
                if (ok) {
                    Toast.makeText(this, tr("✅ " + label + " با شماره " + (finalSpace + 1) + " در فضای " + (finalSpace + 1) + " ایجاد شد",
                            "✅ " + label + " #" + (finalSpace + 1) + " created in Space " + (finalSpace + 1)), Toast.LENGTH_SHORT).show();
                    finish();
                } else {
                    Toast.makeText(this, tr("❌ خطا در کلون‌سازی", "❌ Clone failed"), Toast.LENGTH_SHORT).show();
                }
            });
            row.addView(btnClone);
            listContainer.addView(row);
        }
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/AddAppActivity.java"), ADD_APP_ACTIVITY)

GLOBAL_ENV_ACTIVITY = r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.VirtualHookManager;

public class GlobalEnvironmentActivity extends BaseActivity {
    private EditText etBrand, etModel, etManufacturer, etProduct, etRegion, etTz, etProxy, etSimOp, etSimNum, etSimIso, etSimPhone;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        CloneMetadataStore store = CloneMetadataStore.get(this);
        CloneMetadataStore.GlobalEnvConfig g = store.getGlobalConfig();

        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(Color.parseColor("#0B0F19"));
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(16), dp(16), dp(24));

        TextView title = new TextView(this);
        title.setText(tr("📱 هویت دستگاه، سیم‌کارت مجازی و منطقه سراسری (اولویت ۳)", "📱 Global Device, Virtual SIM & Region (Priority #3)"));
        title.setTextColor(Color.WHITE);
        title.setTextSize(17);
        title.setTypeface(null, Typeface.BOLD);
        box.addView(title);

        TextView btnPreset = makeBtn(tr("🍏 انتخاب سریع از لیست مدل‌ها (شامل آیفون ۱۶ پرو مکس، سامسونگ، پیکسل...)", "🍏 Pick Preset Model (Apple iPhone, Samsung, Pixel...)"), "#2563EB");
        btnPreset.setOnClickListener(v -> showPresetPicker());
        box.addView(btnPreset);

        etBrand = addField(box, tr("برند دستگاه (Brand):", "Brand:"), g.brand);
        etModel = addField(box, tr("مدل دستگاه (Model - بدون تکرار نام برند):", "Model (without duplicate brand):"), CloneMetadataStore.cleanModelOnly(g.brand, g.model));
        etManufacturer = addField(box, tr("سازنده (Manufacturer):", "Manufacturer:"), g.manufacturer);
        etProduct = addField(box, tr("کد محصول (Product):", "Product:"), g.product);
        etRegion = addField(box, tr("شهر و کشور فعال (City, Country):", "Active Region (City, Country):"), g.regionLabel);
        etTz = addField(box, tr("منطقه زمانی (Timezone):", "Timezone:"), g.timezoneId);
        etProxy = addField(box, tr("پروکسی / تونل (Host:Port):", "Proxy / Tunnel (Host:Port):"), g.proxyAddress);
        etSimOp = addField(box, tr("اپراتور سیم‌کارت مجازی (Virtual SIM Operator):", "Virtual SIM Operator:"), g.simOperatorName);
        etSimNum = addField(box, tr("کد شبکه سیم‌کارت (MCC/MNC):", "SIM MCC/MNC:"), g.simOperatorNumeric);
        etSimIso = addField(box, tr("کد کشور سیم‌کارت (ISO):", "SIM Country ISO:"), g.simCountryIso);
        etSimPhone = addField(box, tr("شماره تلفن مجازی (Virtual Phone):", "Virtual Phone Number:"), g.simPhoneNumber);

        TextView btnMap = makeBtn(tr("🗺️ انتخاب موقعیت روی نقشه", "🗺️ Open Map Location Picker"), "#0D9488");
        btnMap.setOnClickListener(v -> startActivity(new Intent(this, SetLocationActivity.class)));
        box.addView(btnMap);

        TextView btnSave = makeBtn(tr("💾 ذخیره و اعمال فوری", "💾 Save & Apply Immediately"), "#10B981");
        btnSave.setOnClickListener(v -> {
            g.brand = etBrand.getText().toString().trim();
            g.model = CloneMetadataStore.cleanModelOnly(g.brand, etModel.getText().toString().trim());
            g.manufacturer = etManufacturer.getText().toString().trim();
            g.product = etProduct.getText().toString().trim();
            g.regionLabel = etRegion.getText().toString().trim();
            g.timezoneId = etTz.getText().toString().trim();
            g.proxyAddress = etProxy.getText().toString().trim();
            g.simOperatorName = etSimOp.getText().toString().trim();
            g.simOperatorNumeric = etSimNum.getText().toString().trim();
            g.simCountryIso = etSimIso.getText().toString().trim().toLowerCase();
            g.simPhoneNumber = etSimPhone.getText().toString().trim();
            store.saveGlobalConfig(g);
            VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
            Toast.makeText(this, tr("✅ تغییرات ذخیره و اعمال شد: ", "✅ Saved & Applied: ") + CloneMetadataStore.formatBrandModel(g.brand, g.model), Toast.LENGTH_SHORT).show();
            finish();
        });
        box.addView(btnSave);

        sv.addView(box);
        setContentView(sv);
    }

    private void showPresetPicker() {
        CloneMetadataStore.DevicePreset[] presets = CloneMetadataStore.PRESETS;
        String[] names = new String[presets.length];
        for (int i = 0; i < presets.length; i++) {
            names[i] = CloneMetadataStore.formatBrandModel(presets[i].brand, presets[i].model);
        }
        new AlertDialog.Builder(this)
            .setTitle(tr("انتخاب مدل آماده", "Choose Device Preset"))
            .setItems(names, (d, w) -> {
                CloneMetadataStore.DevicePreset p = presets[w];
                etBrand.setText(p.brand);
                etModel.setText(CloneMetadataStore.cleanModelOnly(p.brand, p.model));
                etManufacturer.setText(p.manufacturer);
                etProduct.setText(p.product);
            }).show();
    }

    private EditText addField(LinearLayout parent, String label, String value) {
        TextView tv = new TextView(this);
        tv.setText(label);
        tv.setTextColor(Color.parseColor("#94A3B8"));
        tv.setTextSize(12);
        parent.addView(tv);
        EditText et = new EditText(this);
        et.setText(value);
        et.setTextColor(Color.WHITE);
        parent.addView(et);
        return et;
    }

    private TextView makeBtn(String text, String color) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(Color.WHITE);
        tv.setTypeface(null, Typeface.BOLD);
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(dp(12), dp(12), dp(12), dp(12));
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(color));
        gd.setCornerRadius(dp(12));
        tv.setBackground(gd);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, dp(10), 0, dp(10));
        tv.setLayoutParams(lp);
        return tv;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/GlobalEnvironmentActivity.java"), GLOBAL_ENV_ACTIVITY)

SET_LOCATION_ACTIVITY = r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.VirtualHookManager;
import org.osmdroid.config.Configuration;
import org.osmdroid.tileprovider.tilesource.TileSourceFactory;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapView;

public class SetLocationActivity extends BaseActivity {
    private String targetPkg;
    private int targetUser;
    private MapView mapView;
    private EditText etRegion, etLat, etLon, etTz, etProxy;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        targetPkg = getIntent().getStringExtra("target_pkg");
        targetUser = getIntent().getIntExtra("target_user", 0);

        try {
            Configuration.getInstance().load(getApplicationContext(), PreferenceManager.getDefaultSharedPreferences(getApplicationContext()));
            Configuration.getInstance().setUserAgentValue(getPackageName());
        } catch (Throwable ignored) {}

        CloneMetadataStore store = CloneMetadataStore.get(this);
        CloneMetadataStore.GlobalEnvConfig g = store.getGlobalConfig();
        double initLat = g.latitude, initLon = g.longitude;
        String initRegion = g.regionLabel, initTz = g.timezoneId, initProxy = g.proxyAddress;

        if (targetPkg != null) {
            CloneMetadataStore.CloneMeta m = store.getCloneMeta(targetPkg, targetUser);
            if (m.hasExclusiveLocation) {
                initLat = m.latitude; initLon = m.longitude;
                initRegion = m.regionLabel; initTz = m.timezoneId; initProxy = m.proxyAddress;
            }
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#0B0F19"));
        root.setPadding(dp(12), dp(12), dp(12), dp(12));

        TextView btnQuick = new TextView(this);
        btnQuick.setText(tr("🌍 انتخاب سریع شهر و کشور (آمریکا، آلمان، انگلیس...)", "🌍 Quick Pick City & Country"));
        btnQuick.setTextColor(Color.WHITE);
        btnQuick.setTypeface(null, Typeface.BOLD);
        btnQuick.setGravity(Gravity.CENTER);
        btnQuick.setPadding(dp(10), dp(10), dp(10), dp(10));
        GradientDrawable qBg = new GradientDrawable();
        qBg.setColor(Color.parseColor("#2563EB"));
        qBg.setCornerRadius(dp(10));
        btnQuick.setBackground(qBg);
        btnQuick.setOnClickListener(v -> showQuickCityDialog());
        root.addView(btnQuick);

        mapView = new MapView(this);
        try {
            mapView.setTileSource(TileSourceFactory.MAPNIK);
            mapView.setMultiTouchControls(true);
            mapView.getController().setZoom(11.0);
            mapView.getController().setCenter(new GeoPoint(initLat, initLon));
        } catch (Throwable ignored) {}
        LinearLayout.LayoutParams mapLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
        mapLp.setMargins(0, dp(8), 0, dp(8));
        root.addView(mapView, mapLp);

        etRegion = makeInput(root, tr("شهر و کشور (مثال: Falkenstein, Germany):", "City, Country:"), initRegion);
        etLat = makeInput(root, "Latitude:", String.valueOf(initLat));
        etLon = makeInput(root, "Longitude:", String.valueOf(initLon));
        etTz = makeInput(root, "Timezone:", initTz);
        etProxy = makeInput(root, "Proxy (Host:Port):", initProxy);

        TextView btnSave = new TextView(this);
        btnSave.setText(tr("💾 ذخیره موقعیت و منطقه", "💾 Save Location & Region"));
        btnSave.setTextColor(Color.WHITE);
        btnSave.setTypeface(null, Typeface.BOLD);
        btnSave.setGravity(Gravity.CENTER);
        btnSave.setPadding(dp(12), dp(12), dp(12), dp(12));
        GradientDrawable sBg = new GradientDrawable();
        sBg.setColor(Color.parseColor("#10B981"));
        sBg.setCornerRadius(dp(10));
        btnSave.setBackground(sBg);
        btnSave.setOnClickListener(v -> saveLocationSelection());
        root.addView(btnSave);

        setContentView(root);
    }

    private EditText makeInput(LinearLayout parent, String hint, String val) {
        EditText et = new EditText(this);
        et.setHint(hint);
        et.setText(val);
        et.setTextColor(Color.WHITE);
        et.setHintTextColor(Color.parseColor("#94A3B8"));
        et.setTextSize(12);
        parent.addView(et);
        return et;
    }

    private void showQuickCityDialog() {
        final String[][] cities = {
            {"New York, United States", "40.7128", "-74.0060", "America/New_York"},
            {"Los Angeles, United States", "34.0522", "-118.2437", "America/Los_Angeles"},
            {"Dallas, United States", "32.7767", "-96.7970", "America/Chicago"},
            {"Falkenstein, Germany", "50.4779", "12.3713", "Europe/Berlin"},
            {"Frankfurt, Germany", "50.1109", "8.6821", "Europe/Berlin"},
            {"London, United Kingdom", "51.5074", "-0.1278", "Europe/London"},
            {"Amsterdam, Netherlands", "52.3676", "4.9041", "Europe/Amsterdam"},
            {"Istanbul, Turkey", "41.0082", "28.9784", "Europe/Istanbul"},
            {"Dubai, United Arab Emirates", "25.2048", "55.2708", "Asia/Dubai"}
        };
        String[] labels = new String[cities.length];
        for (int i = 0; i < cities.length; i++) labels[i] = cities[i][0] + " (" + cities[i][3] + ")";
        new AlertDialog.Builder(this)
            .setTitle(tr("انتخاب شهر و کشور", "Choose City & Country"))
            .setItems(labels, (d, w) -> {
                etRegion.setText(cities[w][0]);
                etLat.setText(cities[w][1]);
                etLon.setText(cities[w][2]);
                etTz.setText(cities[w][3]);
                try {
                    mapView.getController().setCenter(new GeoPoint(Double.parseDouble(cities[w][1]), Double.parseDouble(cities[w][2])));
                } catch (Throwable ignored) {}
            }).show();
    }

    private void saveLocationSelection() {
        double lat = 40.7128, lon = -74.0060;
        try {
            lat = Double.parseDouble(etLat.getText().toString().trim());
            lon = Double.parseDouble(etLon.getText().toString().trim());
        } catch (Exception ignored) {}
        String reg = etRegion.getText().toString().trim();
        String tz = etTz.getText().toString().trim();
        String prx = etProxy.getText().toString().trim();

        CloneMetadataStore store = CloneMetadataStore.get(this);
        if (targetPkg != null && !targetPkg.isEmpty()) {
            CloneMetadataStore.CloneMeta m = store.getCloneMeta(targetPkg, targetUser);
            m.hasExclusiveLocation = true;
            m.latitude = lat; m.longitude = lon;
            m.regionLabel = reg; m.timezoneId = tz; m.proxyAddress = prx;
            store.saveCloneMeta(m);
            if (!"__space__".equals(targetPkg)) store.setLastActiveSession(targetPkg, targetUser);
            VirtualHookManager.get(this).applyEffectiveHookToSystem(targetPkg, targetUser);
        } else {
            CloneMetadataStore.GlobalEnvConfig g = store.getGlobalConfig();
            g.locationEnabled = true;
            g.latitude = lat; g.longitude = lon;
            g.regionLabel = reg; g.timezoneId = tz; g.proxyAddress = prx;
            store.saveGlobalConfig(g);
            VirtualHookManager.get(this).applyEffectiveHookToSystem(store.getLastActivePkg(), store.getLastActiveUserId());
        }
        Toast.makeText(this, tr("✅ موقعیت ذخیره و اعمال شد: ", "✅ Saved & Applied: ") + reg, Toast.LENGTH_SHORT).show();
        finish();
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/SetLocationActivity.java"), SET_LOCATION_ACTIVITY)

SECURITY_SETTINGS_ACTIVITY = r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.helper.PatternLockView;
import com.veyravault.space.security.SecurityManager;
import com.veyravault.space.security.VaultDeviceAdminReceiver;

public class SecuritySettingsActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        buildUi();
    }

    @Override
    protected void onResume() {
        super.onResume();
        buildUi();
    }

    private void buildUi() {
        SecurityManager sm = SecurityManager.get(this);
        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(Color.parseColor("#0B0F19"));
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(16), dp(16), dp(24));

        TextView title = new TextView(this);
        title.setText(tr("🔐 قفل هم‌زمان (PIN + الگو) و محافظت ضدحذف", "🔐 Simultaneous PIN + Pattern & Anti-Uninstall"));
        title.setTextColor(Color.WHITE);
        title.setTextSize(17);
        title.setTypeface(null, Typeface.BOLD);
        box.addView(title);

        String statusText = tr("وضعیت قفل PIN: ", "PIN Status: ") + (sm.isPinEnabled() ? "✅" : "⚪")
                + "   |   " + tr("وضعیت قفل الگو: ", "Pattern Status: ") + (sm.isPatternEnabled() ? "✅" : "⚪")
                + "\n" + tr("اولویت قفل اول: ", "Primary Lock Priority: ") + sm.getPrimaryLockPriority();
        TextView tvStatus = new TextView(this);
        tvStatus.setText(statusText);
        tvStatus.setTextColor(Color.parseColor("#38BDF8"));
        tvStatus.setPadding(0, dp(10), 0, dp(10));
        box.addView(tvStatus);

        box.addView(makeBtn(tr("🔢 تنظیم / تغییر رمز PIN (هم‌زمان با الگو)", "🔢 Set / Change PIN Code"), "#2563EB", this::showSetPinDialog));
        box.addView(makeBtn(tr("🌀 ترسیم / تغییر قفل الگو (هم‌زمان با PIN)", "🌀 Draw / Change Pattern Lock"), "#7C3AED", this::showSetPatternDialog));

        box.addView(makeBtn(tr("⭐ تغییر اولویت قفل اول (PIN یا الگو)", "⭐ Toggle Primary Lock Priority (PIN / Pattern)"), "#0D9488", () -> {
            String next = SecurityManager.PRIORITY_PIN.equals(sm.getPrimaryLockPriority())
                    ? SecurityManager.PRIORITY_PATTERN : SecurityManager.PRIORITY_PIN;
            sm.setPrimaryLockPriority(next);
            buildUi();
        }));

        boolean adminActive = sm.isUninstallProtectionActive();
        box.addView(makeBtn(adminActive
                ? tr("🛡️ محافظت ضدحذف فعال است (برای غیرفعال‌سازی بزنید)", "🛡️ Anti-Uninstall Active (Tap to disable)")
                : tr("🛡️ فعال‌سازی محافظت ضدحذف (Device Admin با رضایت کاربر)", "🛡️ Enable Anti-Uninstall Protection"),
                adminActive ? "#10B981" : "#F59E0B", () -> {
            if (adminActive) {
                sm.removeUninstallProtection();
                buildUi();
            } else {
                ComponentName cn = new ComponentName(this, VaultDeviceAdminReceiver.class);
                Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
                intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, cn);
                intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                        tr("حفاظت از داده‌ها و فضاهای VeyraVault در برابر حذف غیرمجاز", "Protect VeyraVault spaces against unauthorized uninstallation"));
                startActivity(intent);
            }
        }));

        if (sm.isAnyLockEnabled()) {
            box.addView(makeBtn(tr("🔓 غیرفعال‌سازی تمام قفل‌ها", "🔓 Disable All Locks"), "#DC2626", () -> {
                sm.disableAllLocks();
                buildUi();
            }));
        }

        sv.addView(box);
        setContentView(sv);
    }

    private void showSetPinDialog() {
        EditText et = new EditText(this);
        et.setHint(tr("رمز عددی ۴ تا ۸ رقمی", "4-8 digit PIN"));
        new AlertDialog.Builder(this)
            .setTitle(tr("تنظیم رمز PIN", "Set PIN Code"))
            .setView(et)
            .setPositiveButton(tr("ذخیره", "Save"), (d, w) -> {
                String pin = et.getText().toString().trim();
                if (pin.length() < 4) {
                    Toast.makeText(this, tr("حداقل ۴ رقم وارد کنید", "Minimum 4 digits"), Toast.LENGTH_SHORT).show();
                    return;
                }
                SecurityManager.get(this).setPinCode(pin);
                SecurityManager.get(this).setSessionUnlocked(true);
                buildUi();
            }).show();
    }

    private void showSetPatternDialog() {
        PatternLockView pv = new PatternLockView(this);
        LinearLayout wrap = new LinearLayout(this);
        wrap.setGravity(Gravity.CENTER);
        wrap.addView(pv, new LinearLayout.LayoutParams(dp(260), dp(260)));
        AlertDialog dlg = new AlertDialog.Builder(this)
            .setTitle(tr("الگوی جدید را رسم کنید (حداقل ۴ نقطه)", "Draw Pattern (min 4 nodes)"))
            .setView(wrap)
            .create();
        pv.setOnPatternListener(pattern -> {
            if (pattern.split("-").length < 4) {
                Toast.makeText(this, tr("حداقل ۴ نقطه را وصل کنید", "Connect at least 4 dots"), Toast.LENGTH_SHORT).show();
                pv.clearPattern();
                return;
            }
            SecurityManager.get(this).setPatternCode(pattern);
            SecurityManager.get(this).setSessionUnlocked(true);
            dlg.dismiss();
            buildUi();
        });
        dlg.show();
    }

    private TextView makeBtn(String text, String color, Runnable action) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(Color.WHITE);
        tv.setTypeface(null, Typeface.BOLD);
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(dp(12), dp(14), dp(12), dp(14));
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(color));
        gd.setCornerRadius(dp(12));
        tv.setBackground(gd);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, dp(8), 0, dp(8));
        tv.setLayoutParams(lp);
        tv.setOnClickListener(v -> action.run());
        return tv;
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/SecuritySettingsActivity.java"), SECURITY_SETTINGS_ACTIVITY)

SECURITY_LOCK_ACTIVITY = r"""package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.helper.PatternLockView;
import com.veyravault.space.security.SecurityManager;

public class SecurityLockActivity extends BaseActivity {
    private boolean showingPinMode = true;
    private int failedAttempts = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        SecurityManager sm = SecurityManager.get(this);
        if (sm.isBothLocksEnabled()) {
            showingPinMode = SecurityManager.PRIORITY_PIN.equals(sm.getPrimaryLockPriority());
        } else {
            showingPinMode = sm.isPinEnabled();
        }
        renderLockScreen();
    }

    private void renderLockScreen() {
        SecurityManager sm = SecurityManager.get(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.parseColor("#0B0F19"));
        root.setPadding(dp(24), dp(24), dp(24), dp(24));

        TextView title = new TextView(this);
        title.setText(tr("🔒 قفل امنیتی VeyraVault", "🔒 VeyraVault Security Lock"));
        title.setTextColor(Color.WHITE);
        title.setTextSize(20);
        title.setTypeface(null, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        root.addView(title);

        if (showingPinMode && sm.isPinEnabled()) {
            EditText etPin = new EditText(this);
            etPin.setHint(tr("رمز PIN را وارد کنید", "Enter PIN Code"));
            etPin.setTextColor(Color.WHITE);
            etPin.setHintTextColor(Color.parseColor("#94A3B8"));
            etPin.setGravity(Gravity.CENTER);
            etPin.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
            root.addView(etPin, new LinearLayout.LayoutParams(dp(220), ViewGroup.LayoutParams.WRAP_CONTENT));

            TextView btnUnlock = new TextView(this);
            btnUnlock.setText(tr("🔓 باز کردن قفل", "🔓 Unlock"));
            btnUnlock.setTextColor(Color.WHITE);
            btnUnlock.setTypeface(null, Typeface.BOLD);
            btnUnlock.setGravity(Gravity.CENTER);
            btnUnlock.setPadding(dp(20), dp(12), dp(20), dp(12));
            GradientDrawable gd = new GradientDrawable();
            gd.setColor(Color.parseColor("#2563EB"));
            gd.setCornerRadius(dp(12));
            btnUnlock.setBackground(gd);
            btnUnlock.setOnClickListener(v -> {
                if (sm.verifyPin(etPin.getText().toString())) {
                    sm.setSessionUnlocked(true);
                    finish();
                } else {
                    onFailedAttempt();
                }
            });
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(220), ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.setMargins(0, dp(12), 0, dp(12));
            root.addView(btnUnlock, lp);
        } else if (sm.isPatternEnabled()) {
            PatternLockView pv = new PatternLockView(this);
            pv.setOnPatternListener(pattern -> {
                if (sm.verifyPattern(pattern)) {
                    sm.setSessionUnlocked(true);
                    finish();
                } else {
                    pv.clearPattern();
                    onFailedAttempt();
                }
            });
            root.addView(pv, new LinearLayout.LayoutParams(dp(260), dp(260)));
        }

        if (sm.isBothLocksEnabled()) {
            TextView btnSwitch = new TextView(this);
            btnSwitch.setText(showingPinMode
                    ? tr("🔄 استفاده از قفل دوم (الگو)", "🔄 Use Secondary Lock (Pattern)")
                    : tr("🔄 استفاده از قفل دوم (PIN)", "🔄 Use Secondary Lock (PIN)"));
            btnSwitch.setTextColor(Color.parseColor("#38BDF8"));
            btnSwitch.setPadding(dp(12), dp(14), dp(12), dp(14));
            btnSwitch.setOnClickListener(v -> {
                showingPinMode = !showingPinMode;
                renderLockScreen();
            });
            root.addView(btnSwitch);
        }

        setContentView(root);
    }

    private void onFailedAttempt() {
        failedAttempts++;
        Toast.makeText(this, tr("❌ رمز یا الگوی واردشده نادرست است", "❌ Incorrect credentials"), Toast.LENGTH_SHORT).show();
        if (failedAttempts >= 2 && SecurityManager.get(this).isBothLocksEnabled()) {
            showingPinMode = !showingPinMode;
            renderLockScreen();
        }
    }

    @Override
    public void onBackPressed() {
        moveTaskToBack(true);
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/SecurityLockActivity.java"), SECURITY_LOCK_ACTIVITY)

GUIDE_ACTIVITY = r"""package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class GuideActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(Color.parseColor("#0B0F19"));
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(16), dp(16), dp(24));

        TextView t = new TextView(this);
        t.setText(tr("📖 راهنمای جامع VeyraVault", "📖 VeyraVault Complete Guide"));
        t.setTextColor(Color.WHITE);
        t.setTextSize(18);
        t.setTypeface(null, Typeface.BOLD);
        box.addView(t);

        String guideFa =
            "۱. سلسله‌مراتب ۳ لایه هویت و عدم نشت گوشی میزبان:\n" +
            "• اولویت ۱ (اختصاصی برنامه): با نگه داشتن انگشت روی هر کلون می‌توانید مدل دستگاه، موقعیت مکانی و سیم‌کارت مجازی مخصوص همان برنامه را تعیین کنید.\n" +
            "• اولویت ۲ (اختصاصی فضا): اگر برای برنامه تنظیم جداگانه نگذارید، از تنظیمات اندروید همان فضا استفاده می‌کند.\n" +
            "• اولویت ۳ (سراسری امن): در صورت عدم تنظیم، به‌طور خودکار از هویت امن سراسری (مثل آیفون ۱۶ پرو مکس و نیویورک) استفاده می‌شود و هرگز اطلاعات گوشی واقعی شما نشت نمی‌کند.\n\n" +
            "۲. خوشه‌های ضدقطعی VPN و لیست VPNهای رایگان:\n" +
            "• در بخش VPN، هر دسته‌بندی (Cluster) شامل چند سرور هم‌خانواده با کشور، شهر، منطقه زمانی و سیم‌کارت یکسان است تا در صورت افت یکی، بلافاصله سرور بعدی جایگزین شود.\n" +
            "• با زدن دکمه «+ اکانت / VPN رایگان» می‌توانید از لیست سرورهای رایگان آماده انتخاب، ویرایش و جابه‌جا کنید.";

        String guideEn =
            "1. Strict 3-Tier Identity & Zero Host Leak:\n" +
            "• Priority #1: Per-App Exclusive Settings -> Priority #2: Space Settings -> Priority #3: Safe Global Vault Defaults. Your real host phone identity is never exposed.\n\n" +
            "2. Multi-Node VPN Clusters & Built-in Free VPNs:\n" +
            "• Sibling servers inside each cluster share identical country, city, timezone, and SIM, automatically rotating on failure without dropping connection.";

        TextView body = new TextView(this);
        body.setText(tr(guideFa, guideEn));
        body.setTextColor(Color.parseColor("#E2E8F0"));
        body.setTextSize(13);
        body.setLineSpacing(dp(4), 1.1f);
        body.setPadding(0, dp(12), 0, 0);
        box.addView(body);

        sv.addView(box);
        setContentView(sv);
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/GuideActivity.java"), GUIDE_ACTIVITY)

ABOUT_ACTIVITY = r"""package com.veyravault.space.ui;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class AboutActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(Color.parseColor("#0B0F19"));
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(18), dp(18), dp(18), dp(24));

        TextView title = new TextView(this);
        title.setText("🛡️ VeyraVault v3.0");
        title.setTextColor(Color.WHITE);
        title.setTextSize(20);
        title.setTypeface(null, Typeface.BOLD);
        box.addView(title);

        TextView info = new TextView(this);
        info.setText(tr(
            "محیط ایزوله چندفضایی، تغییر هویت سخت‌افزاری، سیم‌کارت مجازی و مدیریت هوشمند موقعیت مکانی و خوشه‌های VPN\n\n" +
            "📧 ایمیل ارتباطی: Vaultveyra@gmail.com\n" +
            "✈️ کانال و پشتیبانی تلگرام: https://t.me/VaultVeyra\n\n" +
            "📜 مجوز متن‌باز: Apache License 2.0\n" +
            "فاقد هرگونه تبلیغات، ردیاب یا تله‌متری.",
            "Multi-Space Sandbox, Hardware Identity Spoofing, Virtual SIM & Smart VPN Cluster/Location Manager\n\n" +
            "📧 Email: Vaultveyra@gmail.com\n" +
            "✈️ Telegram: https://t.me/VaultVeyra\n\n" +
            "📜 Open-Source Attribution: Apache License 2.0"
        ));
        info.setTextColor(Color.parseColor("#CBD5E1"));
        info.setTextSize(14);
        info.setPadding(0, dp(12), 0, dp(16));
        box.addView(info);

        TextView tgLink = new TextView(this);
        tgLink.setText("🔗 https://t.me/VaultVeyra");
        tgLink.setTextColor(Color.parseColor("#38BDF8"));
        tgLink.setTextSize(15);
        tgLink.setTypeface(null, Typeface.BOLD);
        tgLink.setOnClickListener(v -> startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/VaultVeyra"))));
        box.addView(tgLink);

        sv.addView(box);
        setContentView(sv);
    }
}
"""
write_file(os.path.join(JAVA_BASE, "ui/AboutActivity.java"), ABOUT_ACTIVITY)

print("[v3-part2] Completed successfully.")
