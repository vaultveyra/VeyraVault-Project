#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Upgrade Script - Part 2 (All UI Activities)
- MainActivity (Stealth Dashboard with Dual Square Clocks [Tehran Jalali + NY Gregorian],
  Spaces tab with top blue active profile banner & 3-dots Space Rename menu,
  Per-clone 3-dots sheet with Apple/Samsung/Pixel/Xiaomi models & priority notice,
  Bottom Navigation Bar with SVG icons & compact + button, Quick Lock button, Instant Live Refresh)
- AddAppActivity (Fixed Top Card for External APK / Bazaar / Myket / Google Play + 3-way install dialog)
- GlobalEnvironmentActivity (Apple iPhone/iPad + Global Region City, Country + Session IP/Proxy Shield + GMS toggle)
- SetLocationActivity (OpenStreetMap + Server Region presets + Custom City, Country + Live result refresh)
- SecuritySettingsActivity (Simultaneous PIN + Pattern Dual Lock, Priority selector, Stealth Anti-Uninstall Shield, Disguise)
- SecurityLockActivity (Dual Lock screen with automatic fallback prompt after 2 failed attempts & Stealth Anti-Uninstall Blocker)
- GuideActivity & AboutActivity
"""

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def write_file(rel_path, content):
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    print(f"[v3.0-Part2] Wrote: {rel_path}")


# ---------------------------------------------------------------------------
# 1. MAIN ACTIVITY (MainActivity.java)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/ui/MainActivity.java",
    r"""package com.veyravault.space.ui;

import android.app.ActivityManager;
import android.app.AlertDialog;
import android.app.Dialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.Button;
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
import com.veyravault.space.helper.AppDisguiseManager;
import com.veyravault.space.helper.JalaliClockUtil;
import com.veyravault.space.security.SecurityManager;

import java.util.List;
import java.util.Locale;
import java.util.Map;

public class MainActivity extends BaseActivity {

    public static final int TAB_DASHBOARD = 0;
    public static final int TAB_SPACES = 1;
    public static final int TAB_GUIDE = 2;
    public static final int TAB_SETTINGS = 3;

    // Preserves active tab during current app session so returning from sub-screens
    // or dialogs never jumps back to Dashboard unexpectedly.
    private static int activeTabSession = TAB_DASHBOARD;

    private FrameLayout contentContainer;
    private TextView tvTehranTime;
    private TextView tvTehranDate;
    private TextView tvNyTime;
    private TextView tvNyDate;

    private final Handler clockHandler = new Handler(Looper.getMainLooper());
    private final Runnable clockTicker = new Runnable() {
        @Override
        public void run() {
            updateLiveClocks();
            clockHandler.postDelayed(this, 1000);
        }
    };

    private Dialog activeCloneSheetDialog;
    private String activeSheetPkg;
    private int activeSheetSpaceId = -1;

    private LinearLayout navBtnDashboard;
    private LinearLayout navBtnSpaces;
    private LinearLayout navBtnGuide;
    private LinearLayout navBtnSettings;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        buildRootUi();
    }

    @Override
    protected void onResume() {
        super.onResume();
        clockHandler.removeCallbacks(clockTicker);
        clockHandler.post(clockTicker);
        renderCurrentTab();
        refreshOpenCloneSheetIfNeeded();
    }

    @Override
    protected void onPause() {
        super.onPause();
        clockHandler.removeCallbacks(clockTicker);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        renderCurrentTab();
        refreshOpenCloneSheetIfNeeded();
    }

    private int dp(int v) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    private GradientDrawable roundedBg(String hexColor, int radiusDp, String strokeHex, int strokeWidthDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hexColor));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeWidthDp > 0) {
            gd.setStroke(dp(strokeWidthDp), Color.parseColor(strokeHex));
        }
        return gd;
    }

    private void buildRootUi() {
        boolean fa = isPersian();
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#090D16"));
        root.setLayoutParams(new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        // -------------------------------------------------------------------
        // Top Header Bar: App Title + Quick Lock Button + Language Switch Button
        // -------------------------------------------------------------------
        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setBackgroundColor(Color.parseColor("#0F172A"));
        topBar.setPadding(dp(14), dp(12), dp(14), dp(12));

        TextView titleView = new TextView(this);
        titleView.setText(AppDisguiseManager.getDisguiseTitle(this, fa));
        titleView.setTextColor(Color.WHITE);
        titleView.setTextSize(18);
        titleView.setTypeface(Typeface.DEFAULT_BOLD);
        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        titleView.setLayoutParams(titleLp);
        topBar.addView(titleView);

        // Quick Lock Button (Item 8: Right next to language button)
        TextView btnQuickLock = new TextView(this);
        btnQuickLock.setText(fa ? "🔒 قفل سریع" : "🔒 Lock");
        btnQuickLock.setTextColor(Color.parseColor("#F8FAFC"));
        btnQuickLock.setTextSize(12);
        btnQuickLock.setTypeface(Typeface.DEFAULT_BOLD);
        btnQuickLock.setPadding(dp(10), dp(6), dp(10), dp(6));
        btnQuickLock.setBackground(roundedBg("#1E293B", 8, "#38BDF8", 1));
        LinearLayout.LayoutParams lockLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lockLp.setMargins(dp(6), 0, dp(6), 0);
        btnQuickLock.setLayoutParams(lockLp);
        btnQuickLock.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                triggerQuickLock();
            }
        });
        topBar.addView(btnQuickLock);

        // Language Toggle Button
        TextView btnLang = new TextView(this);
        btnLang.setText(fa ? "EN" : "فارسی");
        btnLang.setTextColor(Color.parseColor("#38BDF8"));
        btnLang.setTextSize(12);
        btnLang.setTypeface(Typeface.DEFAULT_BOLD);
        btnLang.setPadding(dp(10), dp(6), dp(10), dp(6));
        btnLang.setBackground(roundedBg("#1E293B", 8, "#334155", 1));
        btnLang.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                switchLanguageInstant();
            }
        });
        topBar.addView(btnLang);

        root.addView(topBar);

        // -------------------------------------------------------------------
        // Center Dynamic Content Container
        // -------------------------------------------------------------------
        contentContainer = new FrameLayout(this);
        LinearLayout.LayoutParams contentLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
        contentContainer.setLayoutParams(contentLp);
        root.addView(contentContainer);

        // -------------------------------------------------------------------
        // Bottom Navigation Bar with SVG Icons + Compact Central "+" Button
        // Order: Dashboard, Spaces, (+), Guide, Settings
        // -------------------------------------------------------------------
        LinearLayout bottomBar = new LinearLayout(this);
        bottomBar.setOrientation(LinearLayout.HORIZONTAL);
        bottomBar.setGravity(Gravity.CENTER_VERTICAL);
        bottomBar.setBackgroundColor(Color.parseColor("#0F172A"));
        bottomBar.setPadding(dp(6), dp(6), dp(6), dp(8));

        navBtnDashboard = createBottomNavItem(
                R.drawable.ic_nav_dashboard,
                fa ? "داشبورد" : "Dashboard",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        switchTab(TAB_DASHBOARD);
                    }
                });

        navBtnSpaces = createBottomNavItem(
                R.drawable.ic_nav_spaces,
                fa ? "فضاها" : "Spaces",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        switchTab(TAB_SPACES);
                    }
                });

        // Central "+" Button (Sleeker & slightly smaller 44dp circle)
        FrameLayout addWrap = new FrameLayout(this);
        LinearLayout.LayoutParams addWrapLp = new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        addWrap.setLayoutParams(addWrapLp);

        LinearLayout addCircle = new LinearLayout(this);
        addCircle.setGravity(Gravity.CENTER);
        addCircle.setBackground(roundedBg("#0284C7", 22, "#38BDF8", 1));
        FrameLayout.LayoutParams circleLp = new FrameLayout.LayoutParams(dp(44), dp(44));
        circleLp.gravity = Gravity.CENTER;
        addCircle.setLayoutParams(circleLp);

        ImageView plusIcon = new ImageView(this);
        plusIcon.setImageResource(R.drawable.ic_nav_add);
        LinearLayout.LayoutParams plusIconLp = new LinearLayout.LayoutParams(dp(22), dp(22));
        plusIcon.setLayoutParams(plusIconLp);
        addCircle.addView(plusIcon);

        addCircle.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent i = new Intent(MainActivity.this, AddAppActivity.class);
                startActivityForResult(i, 101);
            }
        });
        addWrap.addView(addCircle);

        navBtnGuide = createBottomNavItem(
                R.drawable.ic_nav_guide,
                fa ? "راهنما" : "Guide",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        switchTab(TAB_GUIDE);
                    }
                });

        navBtnSettings = createBottomNavItem(
                R.drawable.ic_nav_settings,
                fa ? "تنظیمات" : "Settings",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        switchTab(TAB_SETTINGS);
                    }
                });

        bottomBar.addView(navBtnDashboard);
        bottomBar.addView(navBtnSpaces);
        bottomBar.addView(addWrap);
        bottomBar.addView(navBtnGuide);
        bottomBar.addView(navBtnSettings);

        root.addView(bottomBar);
        setContentView(root);
        renderCurrentTab();
    }

    private LinearLayout createBottomNavItem(int iconRes, String label, View.OnClickListener listener) {
        LinearLayout item = new LinearLayout(this);
        item.setOrientation(LinearLayout.VERTICAL);
        item.setGravity(Gravity.CENTER);
        item.setPadding(dp(4), dp(4), dp(4), dp(4));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        item.setLayoutParams(lp);

        ImageView iv = new ImageView(this);
        iv.setImageResource(iconRes);
        iv.setTag("nav_icon");
        LinearLayout.LayoutParams ivLp = new LinearLayout.LayoutParams(dp(20), dp(20));
        iv.setLayoutParams(ivLp);
        item.addView(iv);

        TextView tv = new TextView(this);
        tv.setText(label);
        tv.setTag("nav_label");
        tv.setTextSize(11);
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(0, dp(3), 0, 0);
        item.addView(tv);

        item.setOnClickListener(listener);
        return item;
    }

    private void updateNavHighlight() {
        styleNavButton(navBtnDashboard, activeTabSession == TAB_DASHBOARD);
        styleNavButton(navBtnSpaces, activeTabSession == TAB_SPACES);
        styleNavButton(navBtnGuide, activeTabSession == TAB_GUIDE);
        styleNavButton(navBtnSettings, activeTabSession == TAB_SETTINGS);
    }

    private void styleNavButton(LinearLayout btn, boolean active) {
        if (btn == null) return;
        ImageView iv = btn.findViewWithTag("nav_icon");
        TextView tv = btn.findViewWithTag("nav_label");
        int color = Color.parseColor(active ? "#38BDF8" : "#94A3B8");
        if (iv != null) iv.setColorFilter(color);
        if (tv != null) {
            tv.setTextColor(color);
            tv.setTypeface(active ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        }
    }

    private void switchTab(int tab) {
        activeTabSession = tab;
        renderCurrentTab();
    }

    private void renderCurrentTab() {
        if (contentContainer == null) return;
        contentContainer.removeAllViews();
        updateNavHighlight();

        if (activeTabSession == TAB_DASHBOARD) {
            contentContainer.addView(buildDashboardTabView());
            updateLiveClocks();
        } else if (activeTabSession == TAB_SPACES) {
            contentContainer.addView(buildSpacesTabView());
        } else if (activeTabSession == TAB_GUIDE) {
            contentContainer.addView(buildInlineGuideView());
        } else if (activeTabSession == TAB_SETTINGS) {
            contentContainer.addView(buildSettingsHubTabView());
        }
    }

    // =======================================================================
    // TAB 1: STEALTH DASHBOARD VIEW (No mention of cloning/multi-space!)
    //        - Two Side-by-Side Square Clocks:
    //          Right: Iran - Tehran (Solar Hijri / Jalali Date)
    //          Left:  USA - New York (Gregorian Date)
    //        - Active Device & Region Profile Card
    //        - Memory & Speed Optimizer Card
    // =======================================================================
    private View buildDashboardTabView() {
        boolean fa = isPersian();
        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);

        LinearLayout container = new LinearLayout(this);
        container.setOrientation(LinearLayout.VERTICAL);
        container.setPadding(dp(14), dp(14), dp(14), dp(24));

        // 1. Two Side-by-Side Square World Clocks
        LinearLayout clockRow = new LinearLayout(this);
        clockRow.setOrientation(LinearLayout.HORIZONTAL);
        clockRow.setWeightSum(2f);
        LinearLayout.LayoutParams rowLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        rowLp.setMargins(0, 0, 0, dp(14));
        clockRow.setLayoutParams(rowLp);

        // Tehran Square Card
        LinearLayout tehranCard = new LinearLayout(this);
        tehranCard.setOrientation(LinearLayout.VERTICAL);
        tehranCard.setGravity(Gravity.CENTER);
        tehranCard.setPadding(dp(12), dp(18), dp(12), dp(18));
        tehranCard.setMinimumHeight(dp(142));
        tehranCard.setBackground(roundedBg("#111C33", 16, "#1E3A8A", 1));
        LinearLayout.LayoutParams c1Lp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        c1Lp.setMargins(dp(5), 0, dp(5), 0);
        tehranCard.setLayoutParams(c1Lp);

        TextView tvTehranTitle = new TextView(this);
        tvTehranTitle.setText(fa ? "🇮🇷 ایران - تهران" : "🇮🇷 Iran - Tehran");
        tvTehranTitle.setTextColor(Color.parseColor("#93C5FD"));
        tvTehranTitle.setTextSize(13);
        tvTehranTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvTehranTitle.setGravity(Gravity.CENTER);
        tehranCard.addView(tvTehranTitle);

        tvTehranTime = new TextView(this);
        tvTehranTime.setTextColor(Color.WHITE);
        tvTehranTime.setTextSize(22);
        tvTehranTime.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        tvTehranTime.setGravity(Gravity.CENTER);
        tvTehranTime.setPadding(0, dp(8), 0, dp(6));
        tehranCard.addView(tvTehranTime);

        tvTehranDate = new TextView(this);
        tvTehranDate.setTextColor(Color.parseColor("#38BDF8"));
        tvTehranDate.setTextSize(12);
        tvTehranDate.setGravity(Gravity.CENTER);
        tehranCard.addView(tvTehranDate);

        // New York Square Card
        LinearLayout nyCard = new LinearLayout(this);
        nyCard.setOrientation(LinearLayout.VERTICAL);
        nyCard.setGravity(Gravity.CENTER);
        nyCard.setPadding(dp(12), dp(18), dp(12), dp(18));
        nyCard.setMinimumHeight(dp(142));
        nyCard.setBackground(roundedBg("#111C33", 16, "#1E3A8A", 1));
        LinearLayout.LayoutParams c2Lp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        c2Lp.setMargins(dp(5), 0, dp(5), 0);
        nyCard.setLayoutParams(c2Lp);

        TextView tvNyTitle = new TextView(this);
        tvNyTitle.setText(fa ? "🇺🇸 آمریکا - نیویورک" : "🇺🇸 USA - New York");
        tvNyTitle.setTextColor(Color.parseColor("#93C5FD"));
        tvNyTitle.setTextSize(13);
        tvNyTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvNyTitle.setGravity(Gravity.CENTER);
        nyCard.addView(tvNyTitle);

        tvNyTime = new TextView(this);
        tvNyTime.setTextColor(Color.WHITE);
        tvNyTime.setTextSize(22);
        tvNyTime.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        tvNyTime.setGravity(Gravity.CENTER);
        tvNyTime.setPadding(0, dp(8), 0, dp(6));
        nyCard.addView(tvNyTime);

        tvNyDate = new TextView(this);
        tvNyDate.setTextColor(Color.parseColor("#38BDF8"));
        tvNyDate.setTextSize(12);
        tvNyDate.setGravity(Gravity.CENTER);
        nyCard.addView(tvNyDate);

        clockRow.addView(tehranCard);
        clockRow.addView(nyCard);
        container.addView(clockRow);

        // 2. Active Hardware & Region System Status Card (Stealth technical summary)
        LinearLayout statusCard = new LinearLayout(this);
        statusCard.setOrientation(LinearLayout.VERTICAL);
        statusCard.setPadding(dp(16), dp(14), dp(16), dp(14));
        statusCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
        LinearLayout.LayoutParams statusLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        statusLp.setMargins(0, 0, 0, dp(14));
        statusCard.setLayoutParams(statusLp);

        TextView statusHeader = new TextView(this);
        statusHeader.setText(fa ? "🌐 پروفایل سخت‌افزاری و منطقه زمانی فعال" : "🌐 Active Hardware & Region Profile");
        statusHeader.setTextColor(Color.parseColor("#38BDF8"));
        statusHeader.setTextSize(14);
        statusHeader.setTypeface(Typeface.DEFAULT_BOLD);
        statusCard.addView(statusHeader);

        String activeDev = CloneMetadataStore.getGlobalDeviceModel(this);
        String activeReg = CloneMetadataStore.getGlobalRegionName(this);
        double[] gc = CloneMetadataStore.getGlobalCoordinates(this);
        String activeIp = CloneMetadataStore.getGlobalVirtualIp(this);

        TextView statusDetails = new TextView(this);
        String detailsText = fa
                ? String.format(Locale.US, "• مدل دستگاه فعال: %s\n• منطقه کشور و شهر: %s\n• مختصات شبکه: %.4f, %.4f\n• آدرس شبکه هدف: %s",
                        activeDev, activeReg, gc[0], gc[1], activeIp)
                : String.format(Locale.US, "• Active Device Model: %s\n• Region (City, Country): %s\n• Network Coords: %.4f, %.4f\n• Target Network IP: %s",
                        activeDev, activeReg, gc[0], gc[1], activeIp);
        statusDetails.setText(detailsText);
        statusDetails.setTextColor(Color.parseColor("#E2E8F0"));
        statusDetails.setTextSize(13);
        statusDetails.setLineSpacing(dp(4), 1f);
        statusDetails.setPadding(0, dp(8), 0, 0);
        statusCard.addView(statusDetails);

        container.addView(statusCard);

        // 3. Memory & System Speed Optimizer Card
        LinearLayout ramCard = new LinearLayout(this);
        ramCard.setOrientation(LinearLayout.VERTICAL);
        ramCard.setPadding(dp(16), dp(14), dp(16), dp(14));
        ramCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
        LinearLayout.LayoutParams ramLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        ramLp.setMargins(0, 0, 0, dp(14));
        ramCard.setLayoutParams(ramLp);

        TextView ramTitle = new TextView(this);
        ramTitle.setText(fa ? "⚡ وضعیت حافظه رم و شتاب‌دهنده پردازنده" : "⚡ RAM Status & CPU Speed Optimizer");
        ramTitle.setTextColor(Color.parseColor("#38BDF8"));
        ramTitle.setTextSize(14);
        ramTitle.setTypeface(Typeface.DEFAULT_BOLD);
        ramCard.addView(ramTitle);

        ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
        ActivityManager am = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        if (am != null) am.getMemoryInfo(mi);
        long availMb = mi.availMem / (1024 * 1024);
        long totalMb = (mi.totalMem > 0 ? mi.totalMem : (3L * 1024 * 1024 * 1024)) / (1024 * 1024);
        long usedPct = totalMb > 0 ? ((totalMb - availMb) * 100 / totalMb) : 45;

        final TextView ramInfo = new TextView(this);
        ramInfo.setText(fa
                ? ("• حافظه آزاد: " + availMb + " مگابایت از " + totalMb + " مگابایت (مصرف: " + usedPct + "٪)\n• وضعیت موتور پردازشی: پایدار و بهینه")
                : ("• Free RAM: " + availMb + " MB / " + totalMb + " MB (" + usedPct + "% used)\n• Engine Status: Stable & Optimized"));
        ramInfo.setTextColor(Color.parseColor("#CBD5E1"));
        ramInfo.setTextSize(13);
        ramInfo.setLineSpacing(dp(3), 1f);
        ramInfo.setPadding(0, dp(8), 0, dp(10));
        ramCard.addView(ramInfo);

        Button btnBoost = new Button(this);
        btnBoost.setText(fa ? "🚀 بهینه‌سازی فوری حافظه و افزایش سرعت" : "🚀 Instant Memory Boost & Speed Up");
        btnBoost.setTextColor(Color.WHITE);
        btnBoost.setTextSize(13);
        btnBoost.setAllCaps(false);
        btnBoost.setBackground(roundedBg("#0284C7", 10, null, 0));
        btnBoost.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                System.gc();
                Toast.makeText(MainActivity.this,
                        isPersian() ? "⚡ حافظه کش پاکسازی شد و سرعت سیستم بهینه گردید" : "⚡ Cache cleared & system speed optimized",
                        Toast.LENGTH_SHORT).show();
                renderCurrentTab();
            }
        });
        ramCard.addView(btnBoost);

        container.addView(ramCard);

        sv.addView(container);
        return sv;
    }

    private void updateLiveClocks() {
        boolean fa = isPersian();
        if (tvTehranTime != null) {
            String t = JalaliClockUtil.getTehranTime();
            tvTehranTime.setText(fa ? JalaliClockUtil.toPersianDigits(t) : t);
        }
        if (tvTehranDate != null) {
            tvTehranDate.setText(JalaliClockUtil.getTehranJalaliDate(fa));
        }
        if (tvNyTime != null) {
            tvNyTime.setText(JalaliClockUtil.getNewYorkTime());
        }
        if (tvNyDate != null) {
            tvNyDate.setText(JalaliClockUtil.getNewYorkGregorianDate(fa));
        }
    }

    // =======================================================================
    // TAB 2: SPACES VIEW
    //        - Top Blue Banner:
    //          "فضاهای چندگانه و موقعیت مکانی هوشمند"
    //          "مدل سراسری فعال: [Model]"
    //          "منطقه: [City, Country e.g. Falkenstein, Germany]"
    //        - 3-dots button (⋮) next to each Space name to Rename that Space!
    //        - Grid of cloned apps with 3-dots menu for per-clone overrides
    // =======================================================================
    private View buildSpacesTabView() {
        final boolean fa = isPersian();
        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);

        LinearLayout container = new LinearLayout(this);
        container.setOrientation(LinearLayout.VERTICAL);
        container.setPadding(dp(14), dp(14), dp(14), dp(28));

        // 1. Top Blue Banner (Moved from Dashboard into Spaces tab as requested in Item 6)
        LinearLayout blueBanner = new LinearLayout(this);
        blueBanner.setOrientation(LinearLayout.VERTICAL);
        blueBanner.setPadding(dp(16), dp(14), dp(16), dp(14));
        blueBanner.setBackground(roundedBg("#1E3A8A", 14, "#38BDF8", 1));
        LinearLayout.LayoutParams bannerLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        bannerLp.setMargins(0, 0, 0, dp(12));
        blueBanner.setLayoutParams(bannerLp);

        TextView bannerTitle = new TextView(this);
        bannerTitle.setText(fa
                ? "فضاهای چندگانه و موقعیت مکانی هوشمند"
                : "Multi-Spaces & Smart Location");
        bannerTitle.setTextColor(Color.WHITE);
        bannerTitle.setTextSize(15);
        bannerTitle.setTypeface(Typeface.DEFAULT_BOLD);
        blueBanner.addView(bannerTitle);

        String globalModel = CloneMetadataStore.getGlobalDeviceModel(this);
        String globalRegion = CloneMetadataStore.getGlobalRegionName(this);

        TextView bannerSub1 = new TextView(this);
        bannerSub1.setText(fa
                ? ("مدل سراسری فعال: " + globalModel)
                : ("Active Global Model: " + globalModel));
        bannerSub1.setTextColor(Color.parseColor("#E0F2FE"));
        bannerSub1.setTextSize(13);
        bannerSub1.setPadding(0, dp(5), 0, 0);
        blueBanner.addView(bannerSub1);

        TextView bannerSub2 = new TextView(this);
        bannerSub2.setText(fa
                ? ("منطقه: " + globalRegion)
                : ("Region: " + globalRegion));
        bannerSub2.setTextColor(Color.parseColor("#7DD3FC"));
        bannerSub2.setTextSize(13);
        bannerSub2.setTypeface(Typeface.DEFAULT_BOLD);
        bannerSub2.setPadding(0, dp(2), 0, 0);
        blueBanner.addView(bannerSub2);

        TextView bannerPriorityHint = new TextView(this);
        bannerPriorityHint.setText(fa
                ? "💡 اولویت با تنظیمات اختصاصی هر برنامه (از منوی ⋮ کنار برنامه) است؛ در صورت عدم تنظیم اختصاصی، همه فضاها از مدل و منطقه سراسری بالا استفاده می‌کنند."
                : "💡 Per-app settings (via ⋮ on each app) take #1 priority; otherwise spaces use the global model & region above.");
        bannerPriorityHint.setTextColor(Color.parseColor("#BAE6FD"));
        bannerPriorityHint.setTextSize(11);
        bannerPriorityHint.setPadding(0, dp(6), 0, 0);
        blueBanner.addView(bannerPriorityHint);

        container.addView(blueBanner);

        // 2. Render Each Space Card with 3-dots Rename Option
        int[] spaces = Engine.getSpaces();
        for (final int spaceId : spaces) {
            LinearLayout spaceCard = new LinearLayout(this);
            spaceCard.setOrientation(LinearLayout.VERTICAL);
            spaceCard.setPadding(dp(12), dp(12), dp(12), dp(14));
            spaceCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
            LinearLayout.LayoutParams scLp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            scLp.setMargins(0, 0, 0, dp(14));
            spaceCard.setLayoutParams(scLp);

            // Space Header Row: Space Name + 3-dots Rename Button + "+ Add" Button
            LinearLayout headerRow = new LinearLayout(this);
            headerRow.setOrientation(LinearLayout.HORIZONTAL);
            headerRow.setGravity(Gravity.CENTER_VERTICAL);

            String spaceTitle = CloneMetadataStore.getSpaceDisplayName(this, spaceId, fa);
            TextView tvSpaceName = new TextView(this);
            tvSpaceName.setText("📂 " + spaceTitle);
            tvSpaceName.setTextColor(Color.parseColor("#38BDF8"));
            tvSpaceName.setTextSize(15);
            tvSpaceName.setTypeface(Typeface.DEFAULT_BOLD);
            headerRow.addView(tvSpaceName);

            // 3-Dots Button right beside the Space Name to Rename the Space (Item 1)
            TextView btnRenameSpace = new TextView(this);
            btnRenameSpace.setText("⋮");
            btnRenameSpace.setTextColor(Color.parseColor("#E2E8F0"));
            btnRenameSpace.setTextSize(18);
            btnRenameSpace.setTypeface(Typeface.DEFAULT_BOLD);
            btnRenameSpace.setPadding(dp(10), dp(2), dp(10), dp(2));
            btnRenameSpace.setBackground(roundedBg("#1E293B", 8, "#334155", 1));
            LinearLayout.LayoutParams dotsLp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            dotsLp.setMargins(dp(8), 0, dp(8), 0);
            btnRenameSpace.setLayoutParams(dotsLp);
            btnRenameSpace.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    showRenameSpaceDialog(spaceId);
                }
            });
            headerRow.addView(btnRenameSpace);

            View spacer = new View(this);
            spacer.setLayoutParams(new LinearLayout.LayoutParams(0, 1, 1f));
            headerRow.addView(spacer);

            TextView btnAddInSpace = new TextView(this);
            btnAddInSpace.setText(fa ? "+ افزودن برنامه" : "+ Add App");
            btnAddInSpace.setTextColor(Color.WHITE);
            btnAddInSpace.setTextSize(12);
            btnAddInSpace.setPadding(dp(10), dp(5), dp(10), dp(5));
            btnAddInSpace.setBackground(roundedBg("#0284C7", 8, null, 0));
            btnAddInSpace.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    Intent i = new Intent(MainActivity.this, AddAppActivity.class);
                    i.putExtra("target_space_id", spaceId);
                    startActivityForResult(i, 101);
                }
            });
            headerRow.addView(btnAddInSpace);

            spaceCard.addView(headerRow);

            List<Engine.ClonedApp> clones = Engine.getClonedApps(this, spaceId);
            if (clones.isEmpty()) {
                TextView emptyTv = new TextView(this);
                emptyTv.setText(fa
                        ? "هنوز برنامه‌ای در این فضا اضافه نشده است. روی «+ افزودن برنامه» بزنید."
                        : "No apps in this space yet. Tap '+ Add App' to clone or install an app.");
                emptyTv.setTextColor(Color.parseColor("#64748B"));
                emptyTv.setTextSize(12);
                emptyTv.setPadding(dp(4), dp(12), dp(4), dp(6));
                spaceCard.addView(emptyTv);
            } else {
                GridLayout grid = new GridLayout(this);
                grid.setColumnCount(3);
                grid.setPadding(0, dp(10), 0, 0);

                for (final Engine.ClonedApp app : clones) {
                    FrameLayout cell = new FrameLayout(this);
                    GridLayout.LayoutParams cellLp = new GridLayout.LayoutParams();
                    cellLp.width = 0;
                    cellLp.columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f);
                    cellLp.setMargins(dp(4), dp(4), dp(4), dp(4));
                    cell.setLayoutParams(cellLp);
                    cell.setBackground(roundedBg("#162032", 12, "#1E293B", 1));
                    cell.setPadding(dp(8), dp(10), dp(8), dp(10));

                    LinearLayout itemCol = new LinearLayout(this);
                    itemCol.setOrientation(LinearLayout.VERTICAL);
                    itemCol.setGravity(Gravity.CENTER_horizontal | Gravity.CENTER_VERTICAL);

                    ImageView iconIv = new ImageView(this);
                    iconIv.setImageDrawable(app.icon);
                    LinearLayout.LayoutParams iconLp = new LinearLayout.LayoutParams(dp(44), dp(44));
                    iconIv.setLayoutParams(iconLp);
                    itemCol.addView(iconIv);

                    TextView nameTv = new TextView(this);
                    nameTv.setText(app.name);
                    nameTv.setTextColor(Color.WHITE);
                    nameTv.setTextSize(12);
                    nameTv.setTypeface(Typeface.DEFAULT_BOLD);
                    nameTv.setSingleLine(true);
                    nameTv.setGravity(Gravity.CENTER);
                    nameTv.setPadding(0, dp(6), 0, dp(2));
                    itemCol.addView(nameTv);

                    TextView devBadge = new TextView(this);
                    devBadge.setText("📱 " + app.customDeviceName);
                    devBadge.setTextColor(Color.parseColor(app.hasCustomDevice ? "#38BDF8" : "#94A3B8"));
                    devBadge.setTextSize(10);
                    devBadge.setSingleLine(true);
                    devBadge.setGravity(Gravity.CENTER);
                    itemCol.addView(devBadge);

                    TextView locBadge = new TextView(this);
                    locBadge.setText("📍 " + app.effectiveRegion);
                    locBadge.setTextColor(Color.parseColor(app.hasCustomLoc ? "#4ADE80" : "#94A3B8"));
                    locBadge.setTextSize(10);
                    locBadge.setSingleLine(true);
                    locBadge.setGravity(Gravity.CENTER);
                    itemCol.addView(locBadge);

                    cell.addView(itemCol);

                    // 3-Dots Menu Button on top corner of each cloned app card
                    TextView menuDots = new TextView(this);
                    menuDots.setText("⋮");
                    menuDots.setTextColor(Color.WHITE);
                    menuDots.setTextSize(16);
                    menuDots.setTypeface(Typeface.DEFAULT_BOLD);
                    menuDots.setPadding(dp(8), dp(2), dp(8), dp(4));
                    menuDots.setBackground(roundedBg("#1E293B", 6, null, 0));
                    FrameLayout.LayoutParams menuLp = new FrameLayout.LayoutParams(
                            ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
                    menuLp.gravity = Gravity.TOP | (fa ? Gravity.LEFT : Gravity.RIGHT);
                    menuDots.setLayoutParams(menuLp);
                    menuDots.setOnClickListener(new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            showCloneOptionsBottomSheet(app.packageName, app.spaceId);
                        }
                    });
                    cell.addView(menuDots);

                    cell.setOnClickListener(new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            Toast.makeText(MainActivity.this,
                                    (fa ? "در حال اجرای " : "Launching ") + app.name + "...",
                                    Toast.LENGTH_SHORT).show();
                            Engine.launchClone(MainActivity.this, app.packageName, app.spaceId);
                        }
                    });

                    cell.setOnLongClickListener(new View.OnLongClickListener() {
                        @Override
                        public boolean onLongClick(View v) {
                            showCloneOptionsBottomSheet(app.packageName, app.spaceId);
                            return true;
                        }
                    });

                    grid.addView(cell);
                }
                spaceCard.addView(grid);
            }

            container.addView(spaceCard);
        }

        sv.addView(container);
        return sv;
    }

    // -----------------------------------------------------------------------
    // Space Renaming Dialog (Item 1: 3-dots next to Space 1 / Space 2 / Space 3)
    // -----------------------------------------------------------------------
    private void showRenameSpaceDialog(final int spaceId) {
        final boolean fa = isPersian();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "تغییر نام فضا" : "Rename Space");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(20), dp(14), dp(20), dp(6));

        final EditText input = new EditText(this);
        input.setHint(fa ? "نام دلخواه فضا (مثلاً: کاری، شخصی، آلمان)" : "Enter custom space name (e.g. Work, Personal)");
        input.setText(CloneMetadataStore.getSpaceCustomName(this, spaceId));
        layout.addView(input);
        b.setView(layout);

        b.setPositiveButton(fa ? "ذخیره فوری" : "Save Now", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                CloneMetadataStore.setSpaceCustomName(MainActivity.this, spaceId, input.getText().toString());
                renderCurrentTab(); // Instant live refresh without reopening app!
                Toast.makeText(MainActivity.this,
                        fa ? "✓ نام فضا فوراً بروزرسانی شد" : "✓ Space name updated immediately",
                        Toast.LENGTH_SHORT).show();
            }
        });

        b.setNeutralButton(fa ? "بازنشانی به پیش‌فرض" : "Reset Default", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                CloneMetadataStore.setSpaceCustomName(MainActivity.this, spaceId, "");
                renderCurrentTab();
            }
        });

        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    // -----------------------------------------------------------------------
    // Per-Clone 3-Dots Bottom Sheet (With Live Instant Refresh)
    // -----------------------------------------------------------------------
    private void showCloneOptionsBottomSheet(final String pkg, final int spaceId) {
        if (activeCloneSheetDialog != null && activeCloneSheetDialog.isShowing()) {
            try {
                activeCloneSheetDialog.dismiss();
            } catch (Throwable ignored) {
            }
        }
        activeSheetPkg = pkg;
        activeSheetSpaceId = spaceId;

        final boolean fa = isPersian();
        final Dialog sheet = new Dialog(this);
        sheet.requestWindowFeature(Window.FEATURE_NO_TITLE);
        activeCloneSheetDialog = sheet;

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(18), dp(18), dp(22));
        root.setBackground(roundedBg("#0F172A", 18, "#38BDF8", 1));

        String effModel = CloneMetadataStore.getEffectiveDeviceModel(this, pkg, spaceId);
        String effRegion = CloneMetadataStore.getEffectiveRegionName(this, pkg, spaceId);
        double[] coords = CloneMetadataStore.getEffectiveCoordinates(this, pkg, spaceId);
        boolean hasCustomDev = CloneMetadataStore.hasCustomDeviceIdentity(this, pkg, spaceId);
        boolean hasCustomLoc = CloneMetadataStore.hasCustomLocation(this, pkg, spaceId);
        String spaceName = CloneMetadataStore.getSpaceDisplayName(this, spaceId, fa);

        TextView header = new TextView(this);
        header.setText((fa ? "⚙ تنظیمات اختصاصی برنامه در " : "⚙ App Settings in ") + spaceName);
        header.setTextColor(Color.WHITE);
        header.setTextSize(16);
        header.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(header);

        TextView subStatus = new TextView(this);
        subStatus.setText(fa
                ? String.format(Locale.US, "📱 مدل فعال: %s (%s)\n📍 منطقه فعال: %s (%.4f, %.4f) [%s]",
                effModel,
                hasCustomDev ? "اختصاصی اولویت ۱" : "سراسری",
                effRegion,
                coords[0], coords[1],
                hasCustomLoc ? "اختصاصی اولویت ۱" : "سراسری")
                : String.format(Locale.US, "📱 Active Model: %s (%s)\n📍 Active Region: %s (%.4f, %.4f) [%s]",
                effModel,
                hasCustomDev ? "Custom Priority #1" : "Global",
                effRegion,
                coords[0], coords[1],
                hasCustomLoc ? "Custom Priority #1" : "Global"));
        subStatus.setTextColor(Color.parseColor("#7DD3FC"));
        subStatus.setTextSize(12);
        subStatus.setLineSpacing(dp(3), 1f);
        subStatus.setPadding(0, dp(8), 0, dp(14));
        root.addView(subStatus);

        // 1. Launch Clone
        root.addView(createSheetActionButton(
                fa ? "🚀 اجرای برنامه" : "🚀 Launch App",
                "#0284C7",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        sheet.dismiss();
                        activeSheetPkg = null;
                        Engine.launchClone(MainActivity.this, pkg, spaceId);
                    }
                }));

        // 2. Rename Clone Alias
        root.addView(createSheetActionButton(
                fa ? "✏ تغییر نام نمایشی برنامه" : "✏ Rename App Alias",
                "#1E293B",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        showRenameCloneAliasDialog(pkg, spaceId);
                    }
                }));

        // 3. Per-Clone Device Identity (Includes Apple iPhone 16 Pro Max + Flagships)
        root.addView(createSheetActionButton(
                fa ? "📱 هویت دستگاه اختصاصی (شامل Apple iPhone و پرچمداران)" : "📱 Custom Device Identity (Apple iPhone & Flagships)",
                "#1E293B",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        showPerCloneDevicePickerDialog(pkg, spaceId);
                    }
                }));

        // 4. Per-Clone Smart Location & Region Map
        root.addView(createSheetActionButton(
                fa ? "🗺 موقعیت مکانی و منطقه اختصاصی (نقشه + شهر و کشور)" : "🗺 Custom Smart Location & Region (Map + City, Country)",
                "#1E293B",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        Intent locIntent = new Intent(MainActivity.this, SetLocationActivity.class);
                        locIntent.putExtra("pkg", pkg);
                        locIntent.putExtra("spaceId", spaceId);
                        startActivityForResult(locIntent, 202);
                    }
                }));

        // 5. Reset Per-Clone Overrides back to Global
        if (hasCustomDev || hasCustomLoc) {
            root.addView(createSheetActionButton(
                    fa ? "🔄 بازگشت به مدل و منطقه سراسری" : "🔄 Reset to Global Model & Region",
                    "#334155",
                    new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            CloneMetadataStore.clearCustomDeviceIdentity(MainActivity.this, pkg, spaceId);
                            CloneMetadataStore.clearCustomLocation(MainActivity.this, pkg, spaceId);
                            renderCurrentTab();
                            refreshOpenCloneSheetIfNeeded();
                            Toast.makeText(MainActivity.this,
                                    fa ? "✓ به تنظیمات سراسری بازگردانده شد" : "✓ Reverted to global settings",
                                    Toast.LENGTH_SHORT).show();
                        }
                    }));
        }

        // 6. Delete Clone from Space
        root.addView(createSheetActionButton(
                fa ? "🗑 حذف این برنامه از فضا" : "🗑 Remove Clone from Space",
                "#7F1D1D",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        sheet.dismiss();
                        activeSheetPkg = null;
                        Engine.removeClone(MainActivity.this, pkg, spaceId);
                        renderCurrentTab();
                        Toast.makeText(MainActivity.this,
                                fa ? "برنامه از این فضا حذف شد" : "Removed from space",
                                Toast.LENGTH_SHORT).show();
                    }
                }));

        sheet.setContentView(root);
        if (sheet.getWindow() != null) {
            sheet.getWindow().setLayout(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT);
            sheet.getWindow().setBackgroundDrawableResource(android.R.color.transparent);
        }
        sheet.show();
    }

    private View createSheetActionButton(String text, String bgHex, View.OnClickListener l) {
        TextView btn = new TextView(this);
        btn.setText(text);
        btn.setTextColor(Color.WHITE);
        btn.setTextSize(13);
        btn.setTypeface(Typeface.DEFAULT_BOLD);
        btn.setPadding(dp(14), dp(12), dp(14), dp(12));
        btn.setBackground(roundedBg(bgHex, 10, "#334155", 1));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, 0, 0, dp(8));
        btn.setLayoutParams(lp);
        btn.setOnClickListener(l);
        return btn;
    }

    private void refreshOpenCloneSheetIfNeeded() {
        if (activeCloneSheetDialog != null && activeCloneSheetDialog.isShowing()
                && activeSheetPkg != null && activeSheetSpaceId >= 0) {
            showCloneOptionsBottomSheet(activeSheetPkg, activeSheetSpaceId);
        }
    }

    private void showRenameCloneAliasDialog(final String pkg, final int spaceId) {
        final boolean fa = isPersian();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "تغییر نام نمایشی برنامه" : "Rename App Alias");

        final EditText input = new EditText(this);
        input.setText(CloneMetadataStore.getCustomAlias(this, pkg, spaceId));
        input.setHint(fa ? "نام دلخواه (مثلاً واتساپ آلمان)" : "Custom alias");
        b.setView(input);

        b.setPositiveButton(fa ? "ذخیره فوری" : "Save Now", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                CloneMetadataStore.setCustomAlias(MainActivity.this, pkg, spaceId, input.getText().toString());
                renderCurrentTab();
                refreshOpenCloneSheetIfNeeded();
            }
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    private void showPerCloneDevicePickerDialog(final String pkg, final int spaceId) {
        final boolean fa = isPersian();
        final Map<String, String> presets = CloneMetadataStore.getAvailableDevicePresets();
        final String[] models = presets.keySet().toArray(new String[0]);
        final String[] displayItems = new String[models.length + 1];
        for (int i = 0; i < models.length; i++) {
            displayItems[i] = models[i] + " (" + presets.get(models[i]) + ")";
        }
        displayItems[models.length] = fa ? "✍ وارد کردن دستی برند و مدل دلخواه..." : "✍ Enter Custom Brand & Model...";

        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "انتخاب مدل گوشی اختصاصی (اولویت ۱)" : "Select Custom Device Model (Priority #1)");
        b.setItems(displayItems, new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                if (which < models.length) {
                    String m = models[which];
                    String br = presets.get(m);
                    CloneMetadataStore.setCustomDeviceIdentity(MainActivity.this, pkg, spaceId, br, m);
                    renderCurrentTab();
                    refreshOpenCloneSheetIfNeeded();
                    Toast.makeText(MainActivity.this,
                            (fa ? "✓ هویت اختصاصی ثبت شد: " : "✓ Custom identity set: ") + m,
                            Toast.LENGTH_SHORT).show();
                } else {
                    showManualDeviceEntryDialog(pkg, spaceId);
                }
            }
        });
        b.show();
    }

    private void showManualDeviceEntryDialog(final String pkg, final int spaceId) {
        final boolean fa = isPersian();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "ثبت دستی برند و مدل دستگاه" : "Custom Brand & Model");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(18), dp(12), dp(18), dp(6));

        final EditText etBrand = new EditText(this);
        etBrand.setHint(fa ? "برند (مثلاً Apple یا Samsung)" : "Brand (e.g. Apple, Samsung)");
        etBrand.setText(CloneMetadataStore.getEffectiveDeviceBrand(this, pkg, spaceId));
        layout.addView(etBrand);

        final EditText etModel = new EditText(this);
        etModel.setHint(fa ? "مدل (مثلاً iPhone 16 Pro Max)" : "Model (e.g. iPhone 16 Pro Max)");
        etModel.setText(CloneMetadataStore.getEffectiveDeviceModel(this, pkg, spaceId));
        layout.addView(etModel);

        b.setView(layout);
        b.setPositiveButton(fa ? "ذخیره فوری" : "Save Now", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                CloneMetadataStore.setCustomDeviceIdentity(
                        MainActivity.this, pkg, spaceId,
                        etBrand.getText().toString(),
                        etModel.getText().toString());
                renderCurrentTab();
                refreshOpenCloneSheetIfNeeded();
            }
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    // =======================================================================
    // TAB 3: INLINE GUIDE VIEW (Also offers full-page Guide)
    // =======================================================================
    private View buildInlineGuideView() {
        boolean fa = isPersian();
        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);

        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(dp(16), dp(16), dp(16), dp(28));

        TextView title = new TextView(this);
        title.setText(fa ? "📘 راهنمای جامع امکانات VeyraVault v3.0" : "📘 VeyraVault v3.0 Complete User Guide");
        title.setTextColor(Color.parseColor("#38BDF8"));
        title.setTextSize(17);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        col.addView(title);

        addGuideSection(col,
                fa ? "۱. تغییر نام فضاها (منوی ⋮ کنار نام هر فضا)" : "1. Renaming Spaces (⋮ beside Space Name)",
                fa ? "در تب «فضاها»، کنار نام هر فضا (مثلاً فضای ۱) روی دکمه سه نقطه (⋮) بزنید تا نام آن فضا را به دلخواه تغییر دهید."
                   : "In the 'Spaces' tab, tap the 3-dots (⋮) button right next to any Space title to rename that space.");

        addGuideSection(col,
                fa ? "۲. قانون اولویت مدل دستگاه (شامل Apple iPhone) و منطقه جغرافیایی" : "2. Device Model (Apple iPhone included) & Region Priority Rule",
                fa ? "تمام فضاها به صورت پیش‌فرض از مدل گوشی و منطقه‌ای (مثلاً Falkenstein, Germany) که در بخش تنظیمات کلی ثبت کرده‌اید استفاده می‌کنند. اما اگر روی سه نقطه (⋮) کنار یک برنامه بزنید و برای آن برنامه مدل گوشی (مثلاً آیفون ۱۶ پرو مکس) یا شهر/کشور جداگانه‌ای ثبت کنید، اولویت ۱۰۰٪ با تنظیمات اختصاصی همان برنامه خواهد بود."
                   : "All spaces use your Global Device Model & Global Region (e.g. Falkenstein, Germany) by default. However, if you set a custom model (including Apple iPhone) or custom location via a clone's ⋮ menu, that per-app setting takes 100% priority.");

        addGuideSection(col,
                fa ? "۳. مخزن مستقل برنامه‌ها و نصب مستقیم از فایل APK و مارکت‌ها" : "3. Independent App Vault & Installing External APKs/Stores",
                fa ? "هر برنامه‌ای که به فضاها اضافه می‌کنید در مخزن مستقل VeyraVault ذخیره می‌شود؛ حتی اگر برنامه اصلی را از روی گوشی خود پاک کنید، نسخه داخل برنامه حذف نمی‌شود! همچنین از دکمه (+) پایین صفحه می‌توانید برنامه‌هایی که روی گوشی ندارید را از فایل APK، بازار، مایکت یا گوگل‌پلی فقط داخل برنامه، فقط روی گوشی، یا هر دو نصب کنید."
                   : "Cloned apps are backed up into VeyraVault's independent vault—even if you uninstall the host app from your phone, your clone stays intact! Tap (+) to install apps from APK files, Bazaar, Myket, or Google Play inside the vault only, phone only, or both.");

        addGuideSection(col,
                fa ? "۴. قفل دوگانه همزمان (پین + الگو) و سپر ضدحذف مطلق" : "4. Simultaneous Dual Lock (PIN + Pattern) & Anti-Uninstall Shield",
                fa ? "در بخش تنظیمات امنیتی می‌توانید همزمان هم پین و هم الگو را ثبت کنید و اولویت قفل اول را تعیین نمایید. اگر در صفحه قفل ۲ بار رمز اول را اشتباه بزنید، گزینه ورود با رمز دوم ظاهر می‌شود. همچنین با فعال‌سازی سپر ضدحذف، هیچ فردی قادر به حذف برنامه از تنظیمات گوشی نخواهد بود."
                   : "You can configure BOTH a PIN and a Pattern simultaneously and choose which one has primary priority. Failing the primary lock twice automatically offers the secondary lock. Enabling the Anti-Uninstall Shield blocks unauthorized uninstallation.");

        sv.addView(col);
        return sv;
    }

    private void addGuideSection(LinearLayout parent, String head, String body) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackground(roundedBg("#0F172A", 12, "#1E293B", 1));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, dp(10), 0, 0);
        card.setLayoutParams(lp);

        TextView tvH = new TextView(this);
        tvH.setText(head);
        tvH.setTextColor(Color.WHITE);
        tvH.setTextSize(14);
        tvH.setTypeface(Typeface.DEFAULT_BOLD);
        card.addView(tvH);

        TextView tvB = new TextView(this);
        tvB.setText(body);
        tvB.setTextColor(Color.parseColor("#CBD5E1"));
        tvB.setTextSize(12);
        tvB.setLineSpacing(dp(3), 1f);
        tvB.setPadding(0, dp(6), 0, 0);
        card.addView(tvB);

        parent.addView(card);
    }

    // =======================================================================
    // TAB 4: SETTINGS HUB VIEW (Item 9: Houses Device/Location, Security, About Us)
    // =======================================================================
    private View buildSettingsHubTabView() {
        final boolean fa = isPersian();
        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);

        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(dp(16), dp(16), dp(16), dp(28));

        TextView header = new TextView(this);
        header.setText(fa ? "⚙ مرکز تنظیمات جامع VeyraVault" : "⚙ VeyraVault Settings Center");
        header.setTextColor(Color.parseColor("#38BDF8"));
        header.setTextSize(17);
        header.setTypeface(Typeface.DEFAULT_BOLD);
        header.setPadding(0, 0, 0, dp(12));
        col.addView(header);

        String gm = CloneMetadataStore.getGlobalDeviceModel(this);
        String gr = CloneMetadataStore.getGlobalRegionName(this);

        // Card 1: Global Device Model, Region, IP Shield & GMS Settings
        col.addView(createSettingsHubCard(
                fa ? "📱 تنظیمات مدل گوشی، منطقه (شهر/کشور) و سرویس گوگل" : "📱 Device Model, Region (City, Country) & GMS",
                fa ? ("مدل فعال: " + gm + " | منطقه: " + gr + "\nشامل مدل‌های Apple iPhone، تنظیمات IP/پروکسی نشست‌های فعال و GMS")
                   : ("Active: " + gm + " | Region: " + gr + "\nIncludes Apple iPhone presets, Session IP/Proxy Shield & GMS"),
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        startActivityForResult(new Intent(MainActivity.this, GlobalEnvironmentActivity.class), 301);
                    }
                }));

        boolean hasPin = SecurityManager.hasPin(this);
        boolean hasPat = SecurityManager.hasPattern(this);
        boolean antiUninst = SecurityManager.isDeviceAdminActive(this);

        // Card 2: Security, Dual Lock (PIN + Pattern), Anti-Uninstall & Disguise
        col.addView(createSettingsHubCard(
                fa ? "🛡 امنیت، قفل دوگانه (پین و الگو)، ضدحذف و استتار" : "🛡 Security, Dual Lock (PIN & Pattern), Anti-Uninstall & Disguise",
                fa ? ("وضعیت پین: " + (hasPin ? "فعال ✓" : "غیرفعال") + " | الگو: " + (hasPat ? "فعال ✓" : "غیرفعال")
                        + " | سپر ضدحذف: " + (antiUninst ? "فعال ✓" : "غیرفعال"))
                   : ("PIN: " + (hasPin ? "Set ✓" : "Off") + " | Pattern: " + (hasPat ? "Set ✓" : "Off")
                        + " | Anti-Uninstall: " + (antiUninst ? "Active ✓" : "Off")),
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        startActivityForResult(new Intent(MainActivity.this, SecuritySettingsActivity.class), 302);
                    }
                }));

        // Card 3: Interactive Map for Global Location
        col.addView(createSettingsHubCard(
                fa ? "🗺 انتخاب موقعیت سراسری از روی نقشه جهانی" : "🗺 Pick Global Location on World Map",
                fa ? "انتخاب دقیق مختصات GPS و شهر/کشور (مانند Falkenstein, Germany) روی نقشه OpenStreetMap"
                   : "Pinpoint exact GPS coordinates and City, Country (e.g. Falkenstein, Germany) on OpenStreetMap",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        Intent mapIntent = new Intent(MainActivity.this, SetLocationActivity.class);
                        mapIntent.putExtra("is_global", true);
                        startActivityForResult(mapIntent, 303);
                    }
                }));

        // Card 4: About Us & Contact
        col.addView(createSettingsHubCard(
                fa ? "ℹ درباره ما و راه‌های ارتباطی" : "ℹ About Us & Contact",
                fa ? "نسخه 3.0.0 | تلگرام @VaultVeyra | ایمیل Vaultveyra@gmail.com"
                   : "Version 3.0.0 | Telegram @VaultVeyra | Email Vaultveyra@gmail.com",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        startActivity(new Intent(MainActivity.this, AboutActivity.class));
                    }
                }));

        sv.addView(col);
        return sv;
    }

    private View createSettingsHubCard(String title, String subtitle, View.OnClickListener listener) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackground(roundedBg("#0F172A", 14, "#1E3A8A", 1));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, 0, 0, dp(12));
        card.setLayoutParams(lp);

        TextView tvT = new TextView(this);
        tvT.setText(title);
        tvT.setTextColor(Color.WHITE);
        tvT.setTextSize(14);
        tvT.setTypeface(Typeface.DEFAULT_BOLD);
        card.addView(tvT);

        TextView tvS = new TextView(this);
        tvS.setText(subtitle);
        tvS.setTextColor(Color.parseColor("#94A3B8"));
        tvS.setTextSize(12);
        tvS.setLineSpacing(dp(3), 1f);
        tvS.setPadding(0, dp(6), 0, 0);
        card.addView(tvS);

        card.setOnClickListener(listener);
        return card;
    }
}
""",
)

# ---------------------------------------------------------------------------
# 2. ADD APP ACTIVITY (AddAppActivity.java)
#    - Item 11 Part 2: Fixed Top Section for External APK & App Stores
#      (APK File, Cafe Bazaar, Myket, Google Play) + 3-Way Install Dialog:
#      1) Install inside VeyraVault App ONLY (100% Independent)
#      2) Install on Phone ONLY
#      3) Install on BOTH Phone & VeyraVault App
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java",
    r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.Engine;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

public class AddAppActivity extends BaseActivity {

    private static final int REQ_PICK_APK = 501;

    private int selectedSpaceId = 0;
    private List<Engine.InstallOptionCandidate> allHostApps = new ArrayList<>();
    private LinearLayout listContainer;
    private EditText searchInput;
    private TextView spaceSelectorBtn;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        selectedSpaceId = getIntent().getIntExtra("target_space_id", 0);
        allHostApps = Engine.getInstalledHostApps(this);
        buildUi();
    }

    private int dp(int v) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    private GradientDrawable roundedBg(String hex, int radiusDp, String strokeHex, int strokeDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hex));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeDp > 0) {
            gd.setStroke(dp(strokeDp), Color.parseColor(strokeHex));
        }
        return gd;
    }

    private void buildUi() {
        final boolean fa = isPersian();
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#090D16"));

        // Top Bar
        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setBackgroundColor(Color.parseColor("#0F172A"));
        topBar.setPadding(dp(14), dp(12), dp(14), dp(12));

        TextView btnBack = new TextView(this);
        btnBack.setText(fa ? " بازگشت ❯" : "❮ Back ");
        btnBack.setTextColor(Color.parseColor("#38BDF8"));
        btnBack.setTextSize(14);
        btnBack.setTypeface(Typeface.DEFAULT_BOLD);
        btnBack.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        topBar.addView(btnBack);

        TextView title = new TextView(this);
        title.setText(fa ? "افزودن و نصب برنامه در فضا" : "Add & Install App to Space");
        title.setTextColor(Color.WHITE);
        title.setTextSize(16);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setPadding(dp(12), 0, dp(12), 0);
        LinearLayout.LayoutParams tLp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        title.setLayoutParams(tLp);
        topBar.addView(title);

        root.addView(topBar);

        // Body
        LinearLayout headerSection = new LinearLayout(this);
        headerSection.setOrientation(LinearLayout.VERTICAL);
        headerSection.setPadding(dp(14), dp(12), dp(14), dp(8));

        // Target Space Selector Button
        spaceSelectorBtn = new TextView(this);
        updateSpaceSelectorText();
        spaceSelectorBtn.setTextColor(Color.WHITE);
        spaceSelectorBtn.setTextSize(13);
        spaceSelectorBtn.setTypeface(Typeface.DEFAULT_BOLD);
        spaceSelectorBtn.setPadding(dp(14), dp(10), dp(14), dp(10));
        spaceSelectorBtn.setBackground(roundedBg("#1E3A8A", 10, "#38BDF8", 1));
        spaceSelectorBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showTargetSpacePicker();
            }
        });
        headerSection.addView(spaceSelectorBtn);

        // -------------------------------------------------------------------
        // Fixed Top Card: Install External App (Not on Phone) via APK or Stores
        // -------------------------------------------------------------------
        LinearLayout extCard = new LinearLayout(this);
        extCard.setOrientation(LinearLayout.VERTICAL);
        extCard.setPadding(dp(14), dp(12), dp(14), dp(12));
        extCard.setBackground(roundedBg("#0F172A", 12, "#0284C7", 1));
        LinearLayout.LayoutParams extLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        extLp.setMargins(0, dp(10), 0, dp(10));
        extCard.setLayoutParams(extLp);

        TextView extTitle = new TextView(this);
        extTitle.setText(fa
                ? "📥 نصب برنامه جدید (از فایل APK یا مارکت‌ها - بدون نیاز به نصب روی گوشی)"
                : "📥 Install External App (From APK File or App Stores - Independent Vault)");
        extTitle.setTextColor(Color.parseColor("#38BDF8"));
        extTitle.setTextSize(13);
        extTitle.setTypeface(Typeface.DEFAULT_BOLD);
        extCard.addView(extTitle);

        TextView extSub = new TextView(this);
        extSub.setText(fa
                ? "می‌توانید برنامه‌ای که روی گوشی ندارید را انتخاب و مشخص کنید فقط داخل برنامه نصب شود، فقط روی گوشی، یا هر دو:"
                : "Choose an APK or download from a store, then install inside VeyraVault only, Phone only, or Both:");
        extSub.setTextColor(Color.parseColor("#CBD5E1"));
        extSub.setTextSize(11);
        extSub.setPadding(0, dp(4), 0, dp(8));
        extCard.addView(extSub);

        LinearLayout storeRow = new LinearLayout(this);
        storeRow.setOrientation(LinearLayout.HORIZONTAL);
        storeRow.setWeightSum(4f);

        storeRow.addView(createStoreButton(fa ? "📂 فایل APK" : "📂 APK File", "#0284C7", new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                pickExternalApkFile();
            }
        }));

        storeRow.addView(createStoreButton(fa ? "🛒 بازار" : "🛒 Bazaar", "#15803D", new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openMarketOrWeb("com.farsitel.bazaar", "https://cafebazaar.ir");
            }
        }));

        storeRow.addView(createStoreButton(fa ? "📦 مایکت" : "📦 Myket", "#0369A1", new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openMarketOrWeb("ir.mservices.market", "https://myket.ir");
            }
        }));

        storeRow.addView(createStoreButton(fa ? "▶ گوگل‌پلی" : "▶ Play", "#334155", new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openMarketOrWeb("com.android.vending", "https://play.google.com/store");
            }
        }));

        extCard.addView(storeRow);
        headerSection.addView(extCard);

        // Search Bar for Installed Phone Apps
        searchInput = new EditText(this);
        searchInput.setHint(fa ? "🔍 جستجوی برنامه‌های نصب‌شده روی گوشی..." : "🔍 Search apps installed on phone...");
        searchInput.setHintTextColor(Color.parseColor("#64748B"));
        searchInput.setTextColor(Color.WHITE);
        searchInput.setTextSize(13);
        searchInput.setPadding(dp(12), dp(10), dp(12), dp(10));
        searchInput.setBackground(roundedBg("#0F172A", 10, "#1E293B", 1));
        searchInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                populateAppList(s.toString());
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });
        headerSection.addView(searchInput);

        root.addView(headerSection);

        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);
        listContainer = new LinearLayout(this);
        listContainer.setOrientation(LinearLayout.VERTICAL);
        listContainer.setPadding(dp(14), dp(4), dp(14), dp(24));
        sv.addView(listContainer);
        root.addView(sv);

        setContentView(root);
        populateAppList("");
    }

    private View createStoreButton(String text, String bgHex, View.OnClickListener l) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(Color.WHITE);
        tv.setTextSize(11);
        tv.setTypeface(Typeface.DEFAULT_BOLD);
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(dp(6), dp(8), dp(6), dp(8));
        tv.setBackground(roundedBg(bgHex, 8, null, 0));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        lp.setMargins(dp(3), 0, dp(3), 0);
        tv.setLayoutParams(lp);
        tv.setOnClickListener(l);
        return tv;
    }

    private void updateSpaceSelectorText() {
        boolean fa = isPersian();
        String spName = CloneMetadataStore.getSpaceDisplayName(this, selectedSpaceId, fa);
        spaceSelectorBtn.setText(fa
                ? ("📂 فضای مقصد فعلی: " + spName + "  (برای تغییر فضا ضربه بزنید ▾)")
                : ("📂 Target Space: " + spName + "  (Tap to switch ▾)"));
    }

    private void showTargetSpacePicker() {
        final boolean fa = isPersian();
        final int[] spaces = Engine.getSpaces();
        String[] items = new String[spaces.length];
        for (int i = 0; i < spaces.length; i++) {
            items[i] = CloneMetadataStore.getSpaceDisplayName(this, spaces[i], fa);
        }
        new AlertDialog.Builder(this)
                .setTitle(fa ? "انتخاب فضای مقصد" : "Select Target Space")
                .setItems(items, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        selectedSpaceId = spaces[which];
                        updateSpaceSelectorText();
                    }
                })
                .show();
    }

    private void populateAppList(String query) {
        listContainer.removeAllViews();
        final boolean fa = isPersian();
        String q = query == null ? "" : query.trim().toLowerCase();

        for (final Engine.InstallOptionCandidate app : allHostApps) {
            if (!q.isEmpty()
                    && !app.name.toLowerCase().contains(q)
                    && !app.packageName.toLowerCase().contains(q)) {
                continue;
            }

            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER_VERTICAL);
            row.setPadding(dp(12), dp(10), dp(12), dp(10));
            row.setBackground(roundedBg("#0F172A", 12, "#1E293B", 1));
            LinearLayout.LayoutParams rLp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            rLp.setMargins(0, 0, 0, dp(8));
            row.setLayoutParams(rLp);

            ImageView iv = new ImageView(this);
            iv.setImageDrawable(app.icon);
            row.addView(iv, new LinearLayout.LayoutParams(dp(42), dp(42)));

            LinearLayout textCol = new LinearLayout(this);
            textCol.setOrientation(LinearLayout.VERTICAL);
            textCol.setPadding(dp(10), 0, dp(10), 0);
            textCol.setLayoutParams(new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            TextView tvName = new TextView(this);
            tvName.setText(app.name);
            tvName.setTextColor(Color.WHITE);
            tvName.setTextSize(14);
            tvName.setTypeface(Typeface.DEFAULT_BOLD);
            textCol.addView(tvName);

            TextView tvPkg = new TextView(this);
            tvPkg.setText(app.packageName + (fa ? " • ذخیره مستقل در مخزن" : " • Independent Vault Backup"));
            tvPkg.setTextColor(Color.parseColor("#64748B"));
            tvPkg.setTextSize(11);
            textCol.addView(tvPkg);

            row.addView(textCol);

            Button btnClone = new Button(this);
            btnClone.setText(fa ? "+ کلون مستقل" : "+ Clone");
            btnClone.setTextColor(Color.WHITE);
            btnClone.setTextSize(12);
            btnClone.setAllCaps(false);
            btnClone.setBackground(roundedBg("#0284C7", 8, null, 0));
            btnClone.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    boolean ok = Engine.cloneApp(AddAppActivity.this, app.packageName, selectedSpaceId);
                    if (ok) {
                        String spName = CloneMetadataStore.getSpaceDisplayName(AddAppActivity.this, selectedSpaceId, fa);
                        Toast.makeText(AddAppActivity.this,
                                fa ? ("✓ " + app.name + " به صورت مستقل در «" + spName + "» نصب شد (حتی با حذف از گوشی باقی می‌ماند)")
                                   : ("✓ " + app.name + " cloned independently into " + spName),
                                Toast.LENGTH_LONG).show();
                        setResult(RESULT_OK);
                        finish();
                    } else {
                        Toast.makeText(AddAppActivity.this,
                                fa ? "خطا در کلون‌سازی برنامه" : "Failed to clone app",
                                Toast.LENGTH_SHORT).show();
                    }
                }
            });
            row.addView(btnClone);

            listContainer.addView(row);
        }
    }

    private void pickExternalApkFile() {
        try {
            Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
            intent.setType("application/vnd.android.package-archive");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(Intent.createChooser(intent,
                    isPersian() ? "انتخاب فایل نصبی APK" : "Select APK File"), REQ_PICK_APK);
        } catch (Throwable t) {
            Intent fallback = new Intent(Intent.ACTION_GET_CONTENT);
            fallback.setType("*/*");
            startActivityForResult(fallback, REQ_PICK_APK);
        }
    }

    private void openMarketOrWeb(String marketPkg, String webUrl) {
        final boolean fa = isPersian();
        try {
            Intent launch = getPackageManager().getLaunchIntentForPackage(marketPkg);
            if (launch != null) {
                startActivity(launch);
                Toast.makeText(this,
                        fa ? "💡 پس از دانلود یا دریافت فایل APK، می‌توانید آن را از دکمه «📂 فایل APK» یا لیست برنامه‌ها فقط داخل VeyraVault نصب کنید."
                           : "💡 Once downloaded, tap '📂 APK File' to install inside VeyraVault only, Phone only, or Both.",
                        Toast.LENGTH_LONG).show();
                return;
            }
        } catch (Throwable ignored) {
        }
        try {
            Intent web = new Intent(Intent.ACTION_VIEW, Uri.parse(webUrl));
            startActivity(web);
        } catch (Throwable ignored) {
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_PICK_APK && resultCode == RESULT_OK && data != null && data.getData() != null) {
            Uri uri = data.getData();
            File cachedApk = copyUriToTempApk(uri);
            if (cachedApk != null && cachedApk.exists()) {
                showThreeWayInstallDialog(cachedApk);
            } else {
                Toast.makeText(this,
                        isPersian() ? "فایل APK قابل خواندن نیست" : "Could not read APK file",
                        Toast.LENGTH_SHORT).show();
            }
        }
    }

    private File copyUriToTempApk(Uri uri) {
        try {
            File dir = new File(getCacheDir(), "picked_apks");
            if (!dir.exists()) dir.mkdirs();
            String fileName = "external_" + System.currentTimeMillis() + ".apk";
            Cursor c = getContentResolver().query(uri, null, null, null, null);
            if (c != null) {
                int nameIndex = c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (c.moveToFirst() && nameIndex >= 0) {
                    String n = c.getString(nameIndex);
                    if (n != null && n.endsWith(".apk")) fileName = n;
                }
                c.close();
            }
            File out = new File(dir, fileName);
            InputStream is = getContentResolver().openInputStream(uri);
            if (is == null) return null;
            FileOutputStream fos = new FileOutputStream(out);
            byte[] buf = new byte[16384];
            int len;
            while ((len = is.read(buf)) > 0) {
                fos.write(buf, 0, len);
            }
            fos.flush();
            fos.close();
            is.close();
            return out;
        } catch (Throwable t) {
            return null;
        }
    }

    // -----------------------------------------------------------------------
    // 3-Way Installation Target Choice Dialog (Item 11 Part 2):
    //   1. Install inside VeyraVault App ONLY (100% Independent from Phone)
    //   2. Install on Phone ONLY
    //   3. Install on BOTH Phone & VeyraVault App
    // -----------------------------------------------------------------------
    private void showThreeWayInstallDialog(final File apkFile) {
        final boolean fa = isPersian();
        final String spName = CloneMetadataStore.getSpaceDisplayName(this, selectedSpaceId, fa);

        String[] options = new String[]{
                fa ? ("۱. نصب فقط داخل برنامه (" + spName + ") - کاملاً مخفی و مستقل از گوشی")
                   : ("1. Install inside VeyraVault (" + spName + ") ONLY - Independent"),
                fa ? "۲. نصب فقط روی گوشی اصلی"
                   : "2. Install on Phone ONLY",
                fa ? ("۳. نصب همزمان روی هر دو (هم گوشی و هم داخل " + spName + ")")
                   : ("3. Install on BOTH Phone & VeyraVault (" + spName + ")")
        };

        new AlertDialog.Builder(this)
                .setTitle(fa ? "انتخاب محل نصب فایل APK" : "Choose APK Installation Target")
                .setItems(options, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        if (which == 0) {
                            boolean ok = Engine.installApkIntoSpaceOnly(
                                    AddAppActivity.this, apkFile.getAbsolutePath(), selectedSpaceId);
                            Toast.makeText(AddAppActivity.this,
                                    ok
                                            ? (fa ? "✓ برنامه فقط در فضای داخلی VeyraVault نصب شد" : "✓ Installed inside VeyraVault space only")
                                            : (fa ? "خطا در نصب داخلی فایل APK" : "Failed to install APK into space"),
                                    Toast.LENGTH_LONG).show();
                            if (ok) {
                                setResult(RESULT_OK);
                                finish();
                            }
                        } else if (which == 1) {
                            Engine.promptHostInstallForApk(AddAppActivity.this, apkFile.getAbsolutePath());
                        } else if (which == 2) {
                            Engine.installApkIntoSpaceOnly(
                                    AddAppActivity.this, apkFile.getAbsolutePath(), selectedSpaceId);
                            Engine.promptHostInstallForApk(AddAppActivity.this, apkFile.getAbsolutePath());
                            setResult(RESULT_OK);
                            finish();
                        }
                    }
                })
                .show();
    }
}
""",
)

# ---------------------------------------------------------------------------
# 3. GLOBAL ENVIRONMENT ACTIVITY (GlobalEnvironmentActivity.java)
#    - Includes Apple iPhone 16 Pro Max, iPhone 15 Pro Max, iPad Pro M4 + Android Flagships
#    - Priority Rule Notice Banner
#    - Global Region (City, Country e.g. Falkenstein, Germany) + Coordinates
#    - Session IP / Proxy Shield (Virtual IP + SOCKS5/HTTP Proxy so active session lists match region)
#    - GMS Support toggle for YouTube & Viber
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/ui/GlobalEnvironmentActivity.java",
    r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.helper.GmsSupportManager;

import java.util.List;
import java.util.Map;

public class GlobalEnvironmentActivity extends BaseActivity {

    private EditText etBrand;
    private EditText etModel;
    private EditText etRegionName;
    private EditText etLat;
    private EditText etLon;
    private EditText etVirtualIp;
    private EditText etProxyHost;
    private EditText etProxyPort;
    private CheckBox cbGlobalLocEnabled;
    private CheckBox cbGmsEnabled;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        buildUi();
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshFieldsFromStore();
    }

    private int dp(int v) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    private GradientDrawable roundedBg(String hex, int radiusDp, String strokeHex, int strokeDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hex));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeDp > 0) {
            gd.setStroke(dp(strokeDp), Color.parseColor(strokeHex));
        }
        return gd;
    }

    private void buildUi() {
        final boolean fa = isPersian();
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#090D16"));

        // Top Bar
        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setBackgroundColor(Color.parseColor("#0F172A"));
        topBar.setPadding(dp(14), dp(12), dp(14), dp(12));

        TextView btnBack = new TextView(this);
        btnBack.setText(fa ? " بازگشت ❯" : "❮ Back ");
        btnBack.setTextColor(Color.parseColor("#38BDF8"));
        btnBack.setTextSize(14);
        btnBack.setTypeface(Typeface.DEFAULT_BOLD);
        btnBack.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        topBar.addView(btnBack);

        TextView title = new TextView(this);
        title.setText(fa ? "تنظیمات مدل گوشی، منطقه و نشست‌ها" : "Device Model, Region & Session Shield");
        title.setTextColor(Color.WHITE);
        title.setTextSize(15);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setPadding(dp(10), 0, dp(10), 0);
        topBar.addView(title);

        root.addView(topBar);

        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(dp(16), dp(14), dp(16), dp(28));

        // Priority Rule Notice Card (Item 2)
        LinearLayout noticeCard = new LinearLayout(this);
        noticeCard.setOrientation(LinearLayout.VERTICAL);
        noticeCard.setPadding(dp(14), dp(12), dp(14), dp(12));
        noticeCard.setBackground(roundedBg("#1E3A8A", 12, "#38BDF8", 1));
        LinearLayout.LayoutParams nLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        nLp.setMargins(0, 0, 0, dp(14));
        noticeCard.setLayoutParams(nLp);

        TextView noticeTv = new TextView(this);
        noticeTv.setText(fa
                ? "📌 قانون اولویت هوشمند:\nتمام فضاها به صورت پیش‌فرض از مدل گوشی و منطقه (شهر/کشور) ثبت‌شده در این صفحه استفاده می‌کنند. اما اگر برای یک برنامه خاص از منوی سه نقطه (⋮) مدل گوشی یا موقعیت جداگانه‌ای تعیین کنید، اولویت اول با تنظیمات اختصاصی همان برنامه خواهد بود."
                : "📌 Smart Priority Rule:\nAll spaces use the Global Device Model & Region configured here by default. However, if you set a custom model or location for a specific app via its ⋮ menu, that per-app setting takes #1 priority.");
        noticeTv.setTextColor(Color.WHITE);
        noticeTv.setTextSize(12);
        noticeTv.setLineSpacing(dp(3), 1f);
        noticeCard.addView(noticeTv);
        col.addView(noticeCard);

        // Section 1: Global Device Model (Including Apple iPhone / iPad)
        LinearLayout devCard = new LinearLayout(this);
        devCard.setOrientation(LinearLayout.VERTICAL);
        devCard.setPadding(dp(14), dp(14), dp(14), dp(14));
        devCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
        LinearLayout.LayoutParams dLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        dLp.setMargins(0, 0, 0, dp(14));
        devCard.setLayoutParams(dLp);

        TextView devHeader = new TextView(this);
        devHeader.setText(fa ? "📱 ۱. مدل گوشی سراسری (شامل Apple iPhone و پرچمداران)" : "📱 1. Global Device Model (Apple iPhone & Flagships)");
        devHeader.setTextColor(Color.parseColor("#38BDF8"));
        devHeader.setTextSize(14);
        devHeader.setTypeface(Typeface.DEFAULT_BOLD);
        devCard.addView(devHeader);

        Button btnPickPresetModel = new Button(this);
        btnPickPresetModel.setText(fa ? "📋 انتخاب سریع از لیست مدل‌ها (Apple iPhone 16 Pro Max, S24 Ultra, Pixel...)" : "📋 Pick Preset Model (Apple iPhone 16 Pro Max, S24 Ultra, Pixel...)");
        btnPickPresetModel.setTextColor(Color.WHITE);
        btnPickPresetModel.setTextSize(12);
        btnPickPresetModel.setAllCaps(false);
        btnPickPresetModel.setBackground(roundedBg("#0284C7", 10, null, 0));
        LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        btnLp.setMargins(0, dp(10), 0, dp(10));
        btnPickPresetModel.setLayoutParams(btnLp);
        btnPickPresetModel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showGlobalModelPresetDialog();
            }
        });
        devCard.addView(btnPickPresetModel);

        etBrand = createLabeledInput(devCard, fa ? "برند دستگاه (Brand):" : "Device Brand:");
        etModel = createLabeledInput(devCard, fa ? "مدل دستگاه (Model):" : "Device Model:");
        col.addView(devCard);

        // Section 2: Global Region (City, Country like Falkenstein, Germany) & Coordinates
        LinearLayout locCard = new LinearLayout(this);
        locCard.setOrientation(LinearLayout.VERTICAL);
        locCard.setPadding(dp(14), dp(14), dp(14), dp(14));
        locCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
        locCard.setLayoutParams(dLp);

        TextView locHeader = new TextView(this);
        locHeader.setText(fa ? "🌍 ۲. منطقه جغرافیایی سراسری (شهر و کشور مانند Falkenstein, Germany)" : "🌍 2. Global Region (City, Country e.g. Falkenstein, Germany)");
        locHeader.setTextColor(Color.parseColor("#38BDF8"));
        locHeader.setTextSize(14);
        locHeader.setTypeface(Typeface.DEFAULT_BOLD);
        locCard.addView(locHeader);

        cbGlobalLocEnabled = new CheckBox(this);
        cbGlobalLocEnabled.setText(fa ? "فعال‌سازی موقعیت مکانی و منطقه سراسری در تمام فضاها" : "Enable Global Smart Location & Region across all spaces");
        cbGlobalLocEnabled.setTextColor(Color.WHITE);
        cbGlobalLocEnabled.setPadding(0, dp(8), 0, dp(8));
        locCard.addView(cbGlobalLocEnabled);

        Button btnPickRegionPreset = new Button(this);
        btnPickRegionPreset.setText(fa ? "🌐 انتخاب سریع شهر و کشور سرور (Falkenstein, Frankfurt, Amsterdam...)" : "🌐 Pick Server Region (Falkenstein, Frankfurt, Amsterdam...)");
        btnPickRegionPreset.setTextColor(Color.WHITE);
        btnPickRegionPreset.setTextSize(12);
        btnPickRegionPreset.setAllCaps(false);
        btnPickRegionPreset.setBackground(roundedBg("#0369A1", 10, null, 0));
        btnPickRegionPreset.setLayoutParams(btnLp);
        btnPickRegionPreset.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showRegionPresetsDialog();
            }
        });
        locCard.addView(btnPickRegionPreset);

        Button btnOpenMap = new Button(this);
        btnOpenMap.setText(fa ? "🗺 انتخاب دقیق از روی نقشه جهانی OpenStreetMap" : "🗺 Pick Exact Location on OpenStreetMap");
        btnOpenMap.setTextColor(Color.WHITE);
        btnOpenMap.setTextSize(12);
        btnOpenMap.setAllCaps(false);
        btnOpenMap.setBackground(roundedBg("#1E293B", 10, "#38BDF8", 1));
        btnOpenMap.setLayoutParams(btnLp);
        btnOpenMap.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent mapIntent = new Intent(GlobalEnvironmentActivity.this, SetLocationActivity.class);
                mapIntent.putExtra("is_global", true);
                startActivityForResult(mapIntent, 401);
            }
        });
        locCard.addView(btnOpenMap);

        etRegionName = createLabeledInput(locCard, fa ? "منطقه فعال (شهر، کشور - مثال: Falkenstein, Germany):" : "Active Region (City, Country - e.g. Falkenstein, Germany):");
        etLat = createLabeledInput(locCard, fa ? "عرض جغرافیایی (Latitude):" : "Latitude:");
        etLon = createLabeledInput(locCard, fa ? "طول جغرافیایی (Longitude):" : "Longitude:");
        col.addView(locCard);

        // Section 3: Session IP & Proxy Shield (Item 7: Fixes session list showing real country)
        LinearLayout netCard = new LinearLayout(this);
        netCard.setOrientation(LinearLayout.VERTICAL);
        netCard.setPadding(dp(14), dp(14), dp(14), dp(14));
        netCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
        netCard.setLayoutParams(dLp);

        TextView netHeader = new TextView(this);
        netHeader.setText(fa ? "🛡 ۳. سپر تطبیق IP و منطقه نشست‌های فعال (Session Region & Proxy)" : "🛡 3. Active Session IP & Proxy Region Shield");
        netHeader.setTextColor(Color.parseColor("#38BDF8"));
        netHeader.setTextSize(14);
        netHeader.setTypeface(Typeface.DEFAULT_BOLD);
        netCard.addView(netHeader);

        TextView netHint = new TextView(this);
        netHint.setText(fa
                ? "برای اینکه در بخش «نشست‌های فعال» (Active Sessions) برنامه‌ها، منطقه انتخابی شما (مثلاً Falkenstein, Germany) ثبت شود، منطقه زمانی و زبان شبکه به صورت خودکار قفل می‌شود. همچنین می‌توانید IP مجازی سرور یا پروکسی SOCKS5/HTTP منطقه را وارد کنید:"
                : "Locks timezone/locale properties to your chosen region (e.g. Falkenstein, Germany) and lets you bind a target Virtual IP or SOCKS5/HTTP proxy for session consistency:");
        netHint.setTextColor(Color.parseColor("#94A3B8"));
        netHint.setTextSize(11);
        netHint.setPadding(0, dp(4), 0, dp(8));
        netCard.addView(netHint);

        etVirtualIp = createLabeledInput(netCard, fa ? "آدرس IP منطقه هدف (مثال: 88.198.24.108 آلمان):" : "Target Region Virtual IP (e.g. 88.198.24.108):");
        etProxyHost = createLabeledInput(netCard, fa ? "هاست پروکسی SOCKS5/HTTP (اختیاری):" : "SOCKS5/HTTP Proxy Host (Optional):");
        etProxyPort = createLabeledInput(netCard, fa ? "پورت پروکسی (اختیاری - مثال: 1080):" : "Proxy Port (Optional - e.g. 1080):");
        col.addView(netCard);

        // Section 4: Google Play Services (GMS) Support for YouTube, Viber, Chrome
        LinearLayout gmsCard = new LinearLayout(this);
        gmsCard.setOrientation(LinearLayout.VERTICAL);
        gmsCard.setPadding(dp(14), dp(14), dp(14), dp(14));
        gmsCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
        gmsCard.setLayoutParams(dLp);

        TextView gmsHeader = new TextView(this);
        gmsHeader.setText(fa ? "⚙ ۴. پشتیبان سرویس‌های گوگل (مخصوص یوتیوب، وایبر و کروم)" : "⚙ 4. Google Play Services (GMS) for YouTube, Viber & Chrome");
        gmsHeader.setTextColor(Color.parseColor("#38BDF8"));
        gmsHeader.setTextSize(14);
        gmsHeader.setTypeface(Typeface.DEFAULT_BOLD);
        gmsCard.addView(gmsHeader);

        cbGmsEnabled = new CheckBox(this);
        cbGmsEnabled.setText(fa ? "فعال‌سازی خودکار هسته GMS و رفع خطای خدمات گوگل‌پلی در تمام فضاها" : "Auto-enable GMS Core & bypass Google Play Services check across all spaces");
        cbGmsEnabled.setTextColor(Color.WHITE);
        cbGmsEnabled.setPadding(0, dp(8), 0, dp(6));
        gmsCard.addView(cbGmsEnabled);

        col.addView(gmsCard);

        // Save Button (Instant Live Save)
        Button btnSave = new Button(this);
        btnSave.setText(fa ? "💾 ذخیره فوری و اعمال آنی در تمام فضاها" : "💾 Save & Apply Immediately");
        btnSave.setTextColor(Color.WHITE);
        btnSave.setTextSize(14);
        btnSave.setTypeface(Typeface.DEFAULT_BOLD);
        btnSave.setAllCaps(false);
        btnSave.setPadding(dp(14), dp(14), dp(14), dp(14));
        btnSave.setBackground(roundedBg("#16A34A", 12, null, 0));
        btnSave.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                saveAllGlobalSettings();
            }
        });
        col.addView(btnSave);

        sv.addView(col);
        root.addView(sv);
        setContentView(root);

        refreshFieldsFromStore();
    }

    private EditText createLabeledInput(LinearLayout parent, String label) {
        TextView tv = new TextView(this);
        tv.setText(label);
        tv.setTextColor(Color.parseColor("#CBD5E1"));
        tv.setTextSize(12);
        tv.setPadding(0, dp(6), 0, dp(4));
        parent.addView(tv);

        EditText et = new EditText(this);
        et.setTextColor(Color.WHITE);
        et.setTextSize(13);
        et.setSingleLine(true);
        et.setPadding(dp(12), dp(10), dp(12), dp(10));
        et.setBackground(roundedBg("#162032", 8, "#334155", 1));
        parent.addView(et);
        return et;
    }

    private void refreshFieldsFromStore() {
        if (etBrand == null) return;
        etBrand.setText(CloneMetadataStore.getGlobalDeviceBrand(this));
        etModel.setText(CloneMetadataStore.getGlobalDeviceModel(this));
        etRegionName.setText(CloneMetadataStore.getGlobalRegionName(this));
        double[] coords = CloneMetadataStore.getGlobalCoordinates(this);
        etLat.setText(String.valueOf(coords[0]));
        etLon.setText(String.valueOf(coords[1]));
        etVirtualIp.setText(CloneMetadataStore.getGlobalVirtualIp(this));
        etProxyHost.setText(CloneMetadataStore.getGlobalProxyHost(this));
        int port = CloneMetadataStore.getGlobalProxyPort(this);
        etProxyPort.setText(port > 0 ? String.valueOf(port) : "");
        cbGlobalLocEnabled.setChecked(CloneMetadataStore.isGlobalLocationEnabled(this));
        cbGmsEnabled.setChecked(GmsSupportManager.isGmsSupported(this));
    }

    private void showGlobalModelPresetDialog() {
        final Map<String, String> presets = CloneMetadataStore.getAvailableDevicePresets();
        final String[] models = presets.keySet().toArray(new String[0]);
        String[] labels = new String[models.length];
        for (int i = 0; i < models.length; i++) {
            labels[i] = models[i] + " (" + presets.get(models[i]) + ")";
        }
        new AlertDialog.Builder(this)
                .setTitle(isPersian() ? "انتخاب مدل گوشی سراسری" : "Select Global Device Model")
                .setItems(labels, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        String m = models[which];
                        String br = presets.get(m);
                        etBrand.setText(br);
                        etModel.setText(m);
                    }
                })
                .show();
    }

    private void showRegionPresetsDialog() {
        final List<CloneMetadataStore.RegionPreset> presets = CloneMetadataStore.getAvailableRegionPresets();
        String[] labels = new String[presets.size()];
        for (int i = 0; i < presets.size(); i++) {
            CloneMetadataStore.RegionPreset p = presets.get(i);
            labels[i] = "🌍 " + p.cityCountry + " (" + p.sampleIp + ")";
        }
        new AlertDialog.Builder(this)
                .setTitle(isPersian() ? "انتخاب منطقه (شهر و کشور)" : "Select Server Region (City, Country)")
                .setItems(labels, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        CloneMetadataStore.RegionPreset p = presets.get(which);
                        etRegionName.setText(p.cityCountry);
                        etLat.setText(String.valueOf(p.lat));
                        etLon.setText(String.valueOf(p.lon));
                        etVirtualIp.setText(p.sampleIp);
                        cbGlobalLocEnabled.setChecked(true);
                    }
                })
                .show();
    }

    private void saveAllGlobalSettings() {
        boolean fa = isPersian();
        String brand = etBrand.getText().toString().trim();
        String model = etModel.getText().toString().trim();
        String region = etRegionName.getText().toString().trim();
        double lat = 50.4779;
        double lon = 12.3713;
        try {
            lat = Double.parseDouble(etLat.getText().toString().trim());
            lon = Double.parseDouble(etLon.getText().toString().trim());
        } catch (Throwable ignored) {
        }

        CloneMetadataStore.setGlobalDeviceIdentity(this, brand, model);
        CloneMetadataStore.setGlobalRegionName(this, region);
        CloneMetadataStore.setGlobalCoordinates(this, lat, lon);
        CloneMetadataStore.setGlobalLocationEnabled(this, cbGlobalLocEnabled.isChecked());
        CloneMetadataStore.setGlobalVirtualIp(this, etVirtualIp.getText().toString().trim());

        int proxyPort = 0;
        try {
            proxyPort = Integer.parseInt(etProxyPort.getText().toString().trim());
        } catch (Throwable ignored) {
        }
        CloneMetadataStore.setGlobalProxy(this, etProxyHost.getText().toString().trim(), proxyPort);

        GmsSupportManager.setGmsEnabledPref(this, cbGmsEnabled.isChecked());
        if (cbGmsEnabled.isChecked()) {
            GmsSupportManager.enableGmsForAllSpaces(this);
        }

        VirtualHookManager.initializeGlobalHooks(this);

        Toast.makeText(this,
                fa ? "✓ تنظیمات مدل، منطقه (" + CloneMetadataStore.getGlobalRegionName(this) + ") و شبکه فوراً اعمال شد"
                   : "✓ Global device, region & network settings applied immediately",
                Toast.LENGTH_SHORT).show();
        setResult(RESULT_OK);
        finish();
    }
}
""",
)

# ---------------------------------------------------------------------------
# 4. SET LOCATION ACTIVITY (SetLocationActivity.java)
#    - Interactive OpenStreetMap + Server Region Presets (Falkenstein, Germany, etc.)
#    - Custom City, Country label input + Live immediate update on save
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/ui/SetLocationActivity.java",
    r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.VirtualHookManager;

import org.osmdroid.config.Configuration;
import org.osmdroid.tileprovider.tilesource.TileSourceFactory;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapView;

import java.util.List;
import java.util.Locale;

public class SetLocationActivity extends BaseActivity {

    private boolean isGlobalMode = false;
    private String pkg;
    private int spaceId = 0;

    private MapView mapView;
    private EditText etRegionCityCountry;
    private TextView tvCoordsPreview;
    private double currentLat = 50.4779;
    private double currentLon = 12.3713;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Configuration.getInstance().load(getApplicationContext(),
                PreferenceManager.getDefaultSharedPreferences(getApplicationContext()));
        Configuration.getInstance().setUserAgentValue(getPackageName());

        isGlobalMode = getIntent().getBooleanExtra("is_global", false);
        pkg = getIntent().getStringExtra("pkg");
        spaceId = getIntent().getIntExtra("spaceId", 0);

        if (isGlobalMode || pkg == null) {
            isGlobalMode = true;
            double[] gc = CloneMetadataStore.getGlobalCoordinates(this);
            currentLat = gc[0];
            currentLon = gc[1];
        } else {
            double[] cc = CloneMetadataStore.getEffectiveCoordinates(this, pkg, spaceId);
            currentLat = cc[0];
            currentLon = cc[1];
        }

        buildUi();
    }

    private int dp(int v) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    private GradientDrawable roundedBg(String hex, int radiusDp, String strokeHex, int strokeDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hex));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeDp > 0) {
            gd.setStroke(dp(strokeDp), Color.parseColor(strokeHex));
        }
        return gd;
    }

    private void buildUi() {
        final boolean fa = isPersian();
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#090D16"));

        // Top Bar
        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setBackgroundColor(Color.parseColor("#0F172A"));
        topBar.setPadding(dp(14), dp(10), dp(14), dp(10));

        TextView btnBack = new TextView(this);
        btnBack.setText(fa ? " بازگشت ❯" : "❮ Back ");
        btnBack.setTextColor(Color.parseColor("#38BDF8"));
        btnBack.setTextSize(14);
        btnBack.setTypeface(Typeface.DEFAULT_BOLD);
        btnBack.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        topBar.addView(btnBack);

        TextView title = new TextView(this);
        title.setText(isGlobalMode
                ? (fa ? "نقشه موقعیت و منطقه سراسری" : "Global Location & Region Map")
                : (fa ? "موقعیت و منطقه اختصاصی برنامه (اولویت ۱)" : "Per-App Custom Location & Region (#1)"));
        title.setTextColor(Color.WHITE);
        title.setTextSize(14);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setPadding(dp(10), 0, dp(10), 0);
        LinearLayout.LayoutParams tLp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        title.setLayoutParams(tLp);
        topBar.addView(title);

        Button btnPresets = new Button(this);
        btnPresets.setText(fa ? "🌐 شهرها" : "🌐 Cities");
        btnPresets.setTextColor(Color.WHITE);
        btnPresets.setTextSize(11);
        btnPresets.setAllCaps(false);
        btnPresets.setBackground(roundedBg("#0284C7", 8, null, 0));
        btnPresets.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showCityPresetsPopup();
            }
        });
        topBar.addView(btnPresets);

        root.addView(topBar);

        // Map Container with Center Crosshair Pin
        FrameLayout mapFrame = new FrameLayout(this);
        mapFrame.setLayoutParams(new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        mapView = new MapView(this);
        mapView.setTileSource(TileSourceFactory.MAPNIK);
        mapView.setMultiTouchControls(true);
        mapView.getController().setZoom(13.5);
        mapView.getController().setCenter(new GeoPoint(currentLat, currentLon));
        mapView.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (event.getAction() == MotionEvent.ACTION_UP || event.getAction() == MotionEvent.ACTION_MOVE) {
                    GeoPoint center = (GeoPoint) mapView.getMapCenter();
                    currentLat = center.getLatitude();
                    currentLon = center.getLongitude();
                    updateCoordsLabel();
                }
                return false;
            }
        });
        mapFrame.addView(mapView);

        TextView centerPin = new TextView(this);
        centerPin.setText("📍");
        centerPin.setTextSize(30);
        FrameLayout.LayoutParams pinLp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        pinLp.gravity = Gravity.CENTER;
        centerPin.setLayoutParams(pinLp);
        mapFrame.addView(centerPin);

        root.addView(mapFrame);

        // Bottom Control Panel: Region (City, Country) + Coordinates + Save
        LinearLayout bottomPanel = new LinearLayout(this);
        bottomPanel.setOrientation(LinearLayout.VERTICAL);
        bottomPanel.setBackgroundColor(Color.parseColor("#0F172A"));
        bottomPanel.setPadding(dp(16), dp(12), dp(16), dp(16));

        tvCoordsPreview = new TextView(this);
        tvCoordsPreview.setTextColor(Color.parseColor("#38BDF8"));
        tvCoordsPreview.setTextSize(12);
        tvCoordsPreview.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        bottomPanel.addView(tvCoordsPreview);

        TextView lblRegion = new TextView(this);
        lblRegion.setText(fa ? "نام شهر و کشور (جهت نمایش در منطقه و نشست‌ها - مثال: Falkenstein, Germany):" : "City, Country Label (e.g. Falkenstein, Germany):");
        lblRegion.setTextColor(Color.parseColor("#CBD5E1"));
        lblRegion.setTextSize(11);
        lblRegion.setPadding(0, dp(6), 0, dp(4));
        bottomPanel.addView(lblRegion);

        etRegionCityCountry = new EditText(this);
        etRegionCityCountry.setTextColor(Color.WHITE);
        etRegionCityCountry.setTextSize(13);
        etRegionCityCountry.setSingleLine(true);
        etRegionCityCountry.setPadding(dp(12), dp(8), dp(12), dp(8));
        etRegionCityCountry.setBackground(roundedBg("#162032", 8, "#334155", 1));
        String initialRegion = isGlobalMode
                ? CloneMetadataStore.getGlobalRegionName(this)
                : CloneMetadataStore.getEffectiveRegionName(this, pkg, spaceId);
        etRegionCityCountry.setText(initialRegion);
        bottomPanel.addView(etRegionCityCountry);

        LinearLayout btnRow = new LinearLayout(this);
        btnRow.setOrientation(LinearLayout.HORIZONTAL);
        btnRow.setPadding(0, dp(10), 0, 0);

        Button btnSave = new Button(this);
        btnSave.setText(fa ? "✓ ذخیره فوری موقعیت و منطقه" : "✓ Save Location & Region Now");
        btnSave.setTextColor(Color.WHITE);
        btnSave.setTextSize(13);
        btnSave.setTypeface(Typeface.DEFAULT_BOLD);
        btnSave.setAllCaps(false);
        btnSave.setBackground(roundedBg("#16A34A", 10, null, 0));
        LinearLayout.LayoutParams saveLp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        btnSave.setLayoutParams(saveLp);
        btnSave.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                GeoPoint c = (GeoPoint) mapView.getMapCenter();
                currentLat = c.getLatitude();
                currentLon = c.getLongitude();
                String regionName = etRegionCityCountry.getText().toString().trim();
                if (regionName.isEmpty()) regionName = "Falkenstein, Germany";

                if (isGlobalMode) {
                    CloneMetadataStore.setGlobalCoordinates(SetLocationActivity.this, currentLat, currentLon);
                    CloneMetadataStore.setGlobalRegionName(SetLocationActivity.this, regionName);
                    CloneMetadataStore.setGlobalLocationEnabled(SetLocationActivity.this, true);
                    VirtualHookManager.initializeGlobalHooks(SetLocationActivity.this);
                } else {
                    CloneMetadataStore.setCustomLocation(SetLocationActivity.this, pkg, spaceId, currentLat, currentLon, regionName);
                    VirtualHookManager.prepareForCloneLaunch(SetLocationActivity.this, pkg, spaceId);
                }

                Toast.makeText(SetLocationActivity.this,
                        (fa ? "📍 موقعیت و منطقه ثبت شد: " : "📍 Saved: ") + regionName,
                        Toast.LENGTH_SHORT).show();
                setResult(RESULT_OK);
                finish();
            }
        });
        btnRow.addView(btnSave);

        if (!isGlobalMode) {
            Button btnReset = new Button(this);
            btnReset.setText(fa ? "لغو اختصاصی" : "Use Global");
            btnReset.setTextColor(Color.WHITE);
            btnReset.setTextSize(12);
            btnReset.setAllCaps(false);
            btnReset.setBackground(roundedBg("#334155", 10, null, 0));
            LinearLayout.LayoutParams rstLp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            rstLp.setMargins(dp(8), 0, 0, 0);
            btnReset.setLayoutParams(rstLp);
            btnReset.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    CloneMetadataStore.clearCustomLocation(SetLocationActivity.this, pkg, spaceId);
                    setResult(RESULT_OK);
                    finish();
                }
            });
            btnRow.addView(btnReset);
        }

        bottomPanel.addView(btnRow);
        root.addView(bottomPanel);

        setContentView(root);
        updateCoordsLabel();
    }

    private void updateCoordsLabel() {
        if (tvCoordsPreview == null) return;
        tvCoordsPreview.setText(String.format(Locale.US, "GPS: %.5f , %.5f", currentLat, currentLon));
    }

    private void showCityPresetsPopup() {
        final List<CloneMetadataStore.RegionPreset> presets = CloneMetadataStore.getAvailableRegionPresets();
        String[] items = new String[presets.size()];
        for (int i = 0; i < presets.size(); i++) {
            items[i] = "📍 " + presets.get(i).cityCountry;
        }
        new AlertDialog.Builder(this)
                .setTitle(isPersian() ? "انتخاب سریع شهر و کشور" : "Quick Select City & Country")
                .setItems(items, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        CloneMetadataStore.RegionPreset p = presets.get(which);
                        currentLat = p.lat;
                        currentLon = p.lon;
                        etRegionCityCountry.setText(p.cityCountry);
                        mapView.getController().animateTo(new GeoPoint(currentLat, currentLon));
                        updateCoordsLabel();
                    }
                })
                .show();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (mapView != null) mapView.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (mapView != null) mapView.onPause();
    }
}
""",
)

# ---------------------------------------------------------------------------
# 5. SECURITY SETTINGS ACTIVITY (SecuritySettingsActivity.java)
#    - Item 10: Simultaneous Dual Lock (BOTH PIN and Pattern can be set at the same time!)
#      + Primary Lock Priority Selector (PIN first or Pattern first)
#    - Item 11 Part 1: Strict Anti-Uninstall Protection (DevicePolicyManager)
#    - App Title Disguise Mode
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/ui/SecuritySettingsActivity.java",
    r"""package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.helper.AppDisguiseManager;
import com.veyravault.space.security.SecurityManager;

public class SecuritySettingsActivity extends BaseActivity {

    private static final int REQ_DEVICE_ADMIN = 701;

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

    private int dp(int v) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    private GradientDrawable roundedBg(String hex, int radiusDp, String strokeHex, int strokeDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hex));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeDp > 0) {
            gd.setStroke(dp(strokeDp), Color.parseColor(strokeHex));
        }
        return gd;
    }

    private void buildUi() {
        final boolean fa = isPersian();
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#090D16"));

        // Top Bar
        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setBackgroundColor(Color.parseColor("#0F172A"));
        topBar.setPadding(dp(14), dp(12), dp(14), dp(12));

        TextView btnBack = new TextView(this);
        btnBack.setText(fa ? " بازگشت ❯" : "❮ Back ");
        btnBack.setTextColor(Color.parseColor("#38BDF8"));
        btnBack.setTextSize(14);
        btnBack.setTypeface(Typeface.DEFAULT_BOLD);
        btnBack.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        topBar.addView(btnBack);

        TextView title = new TextView(this);
        title.setText(fa ? "امنیت، قفل دوگانه و سپر ضدحذف" : "Security, Dual Lock & Anti-Uninstall");
        title.setTextColor(Color.WHITE);
        title.setTextSize(15);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setPadding(dp(10), 0, dp(10), 0);
        topBar.addView(title);

        root.addView(topBar);

        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(dp(16), dp(14), dp(16), dp(28));

        boolean hasPin = SecurityManager.hasPin(this);
        boolean hasPattern = SecurityManager.hasPattern(this);
        int prio = SecurityManager.getPrimaryLockPriority(this);

        // -------------------------------------------------------------------
        // Section 1: Simultaneous Dual Lock (PIN + Pattern) & Priority (Item 10)
        // -------------------------------------------------------------------
        LinearLayout lockCard = new LinearLayout(this);
        lockCard.setOrientation(LinearLayout.VERTICAL);
        lockCard.setPadding(dp(16), dp(14), dp(16), dp(16));
        lockCard.setBackground(roundedBg("#0F172A", 14, "#1E3A8A", 1));
        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardLp.setMargins(0, 0, 0, dp(14));
        lockCard.setLayoutParams(cardLp);

        TextView lockTitle = new TextView(this);
        lockTitle.setText(fa ? "🔐 ۱. قفل امنیتی دوگانه همزمان (پین + الگو با تعیین اولویت)" : "🔐 1. Simultaneous Dual Lock (PIN + Pattern with Priority)");
        lockTitle.setTextColor(Color.parseColor("#38BDF8"));
        lockTitle.setTextSize(14);
        lockTitle.setTypeface(Typeface.DEFAULT_BOLD);
        lockCard.addView(lockTitle);

        TextView lockStatus = new TextView(this);
        String prioText = (prio == SecurityManager.LOCK_PIN)
                ? (fa ? "رمز پین (PIN)" : "PIN Code")
                : ((prio == SecurityManager.LOCK_PATTERN) ? (fa ? "الگوی ترسیمی (Pattern)" : "Pattern") : (fa ? "غیرفعال" : "None"));
        lockStatus.setText(fa
                ? ("• وضعیت پین (PIN): " + (hasPin ? "ثبت شده ✓" : "خالی ✗")
                        + "\n• وضعیت الگو (Pattern): " + (hasPattern ? "ثبت شده ✓" : "خالی ✗")
                        + "\n• اولویت قفل اول هنگام ورود: " + prioText
                        + "\n💡 شما می‌توانید هر دو را همزمان ثبت کنید! در صفحه قفل اگر ۲ بار قفل اول را اشتباه بزنید، برنامه خودکار پیشنهاد ورود با قفل دوم را نمایش می‌دهد.")
                : ("• PIN Status: " + (hasPin ? "Configured ✓" : "Not set ✗")
                        + "\n• Pattern Status: " + (hasPattern ? "Configured ✓" : "Not set ✗")
                        + "\n• Primary Lock Priority: " + prioText
                        + "\n💡 Both can be active simultaneously! Failing the primary lock twice automatically offers the secondary lock."));
        lockStatus.setTextColor(Color.parseColor("#CBD5E1"));
        lockStatus.setTextSize(12);
        lockStatus.setLineSpacing(dp(3), 1f);
        lockStatus.setPadding(0, dp(8), 0, dp(12));
        lockCard.addView(lockStatus);

        // Button: Set or Change PIN (Does NOT erase Pattern!)
        lockCard.addView(createActionBtn(
                fa ? (hasPin ? "🔢 تغییر رمز پین (بدون پاک شدن الگو)" : "🔢 ثبت رمز پین عددی (PIN)")
                   : (hasPin ? "🔢 Change PIN Code (Keeps Pattern)" : "🔢 Set Numeric PIN Code"),
                "#0284C7",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        showSetPinDialog();
                    }
                }));

        // Button: Set or Change Pattern (Does NOT erase PIN!)
        lockCard.addView(createActionBtn(
                fa ? (hasPattern ? "❇ تغییر الگوی ترسیمی (بدون پاک شدن پین)" : "❇ ثبت الگوی ترسیمی ۹ نقطه‌ای (Pattern)")
                   : (hasPattern ? "❇ Change Pattern Lock (Keeps PIN)" : "❇ Set 9-Dot Pattern Lock"),
                "#0369A1",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        showSetPatternDialog();
                    }
                }));

        // Priority Selector Button when at least one lock is set
        if (hasPin || hasPattern) {
            lockCard.addView(createActionBtn(
                    fa ? "⭐ تعیین اولویت قفل اول (پین اول باشد یا الگو؟)" : "⭐ Choose Primary Lock Priority (PIN vs Pattern)",
                    "#1E293B",
                    new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            showPriorityPickerDialog();
                        }
                    }));

            lockCard.addView(createActionBtn(
                    fa ? "🔓 حذف کامل پین و الگو (غیرفعال‌سازی قفل)" : "🔓 Remove All Locks (Disable)",
                    "#7F1D1D",
                    new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            SecurityManager.disableAllLocks(SecuritySettingsActivity.this);
                            buildUi();
                            Toast.makeText(SecuritySettingsActivity.this,
                                    fa ? "قفل برنامه غیرفعال شد" : "Locks disabled",
                                    Toast.LENGTH_SHORT).show();
                        }
                    }));
        }

        col.addView(lockCard);

        // -------------------------------------------------------------------
        // Section 2: Strict Anti-Uninstall Protection (Item 11 Part 1)
        // -------------------------------------------------------------------
        LinearLayout adminCard = new LinearLayout(this);
        adminCard.setOrientation(LinearLayout.VERTICAL);
        adminCard.setPadding(dp(16), dp(14), dp(16), dp(16));
        adminCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
        adminCard.setLayoutParams(cardLp);

        boolean adminActive = SecurityManager.isDeviceAdminActive(this);

        TextView adminTitle = new TextView(this);
        adminTitle.setText(fa ? "🛡 ۲. سپر ضدحذف مطلق (جلوگیری ۱۰۰٪ از حذف برنامه از گوشی)" : "🛡 2. Strict Anti-Uninstall Shield");
        adminTitle.setTextColor(Color.parseColor("#38BDF8"));
        adminTitle.setTextSize(14);
        adminTitle.setTypeface(Typeface.DEFAULT_BOLD);
        adminCard.addView(adminTitle);

        TextView adminDesc = new TextView(this);
        adminDesc.setText(fa
                ? ("وضعیت فعلی: " + (adminActive ? "فعال و قفل‌شده ✓ (هیچ‌کس نمی‌تواند برنامه را حذف کند)" : "غیرفعال ✗")
                        + "\nبا فعال‌سازی این سپر، حتی اگر فردی از طریق تنظیمات گوشی تلاش کند دسترسی سرپرست را غیرفعال یا برنامه را حذف کند، صفحه قفل امنیتی VeyraVault فوراً روی تنظیمات گوشی ظاهر شده و مانع حذف می‌شود.")
                : ("Current Status: " + (adminActive ? "ACTIVE & PROTECTED ✓" : "Inactive ✗")
                        + "\nWhen active, any attempt to deactivate admin or uninstall VeyraVault from system settings is immediately intercepted by the VeyraVault security lock screen."));
        adminDesc.setTextColor(Color.parseColor("#CBD5E1"));
        adminDesc.setTextSize(12);
        adminDesc.setLineSpacing(dp(3), 1f);
        adminDesc.setPadding(0, dp(8), 0, dp(12));
        adminCard.addView(adminDesc);

        if (!adminActive) {
            adminCard.addView(createActionBtn(
                    fa ? "🛡 فعال‌سازی سپر ضدحذف پیشرفته" : "🛡 Enable Anti-Uninstall Shield",
                    "#16A34A",
                    new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            SecurityManager.requestEnableDeviceAdmin(SecuritySettingsActivity.this, REQ_DEVICE_ADMIN);
                        }
                    }));
        } else {
            adminCard.addView(createActionBtn(
                    fa ? "🔓 غیرفعال‌سازی سپر ضدحذف (توسط مالک مجاز)" : "🔓 Disable Anti-Uninstall Shield (Authorized Owner)",
                    "#7F1D1D",
                    new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            SecurityManager.disableDeviceAdminByAuthorizedOwner(SecuritySettingsActivity.this);
                            Toast.makeText(SecuritySettingsActivity.this,
                                    fa ? "سپر ضدحذف غیرفعال شد؛ اکنون امکان حذف برنامه باز است." : "Anti-Uninstall Shield disabled.",
                                    Toast.LENGTH_LONG).show();
                            buildUi();
                        }
                    }));
        }

        col.addView(adminCard);

        // -------------------------------------------------------------------
        // Section 3: App Header Disguise
        // -------------------------------------------------------------------
        LinearLayout disguiseCard = new LinearLayout(this);
        disguiseCard.setOrientation(LinearLayout.VERTICAL);
        disguiseCard.setPadding(dp(16), dp(14), dp(16), dp(16));
        disguiseCard.setBackground(roundedBg("#0F172A", 14, "#1E293B", 1));
        disguiseCard.setLayoutParams(cardLp);

        TextView disTitle = new TextView(this);
        disTitle.setText(fa ? "🎭 ۳. عنوان ظاهری و استتار برنامه" : "🎭 3. App Title Disguise");
        disTitle.setTextColor(Color.parseColor("#38BDF8"));
        disTitle.setTextSize(14);
        disTitle.setTypeface(Typeface.DEFAULT_BOLD);
        disguiseCard.addView(disTitle);

        TextView disCurr = new TextView(this);
        disCurr.setText((fa ? "عنوان فعلی هدر: " : "Current Header Title: ") + AppDisguiseManager.getDisguiseTitle(this, fa));
        disCurr.setTextColor(Color.parseColor("#CBD5E1"));
        disCurr.setTextSize(12);
        disCurr.setPadding(0, dp(6), 0, dp(10));
        disguiseCard.addView(disCurr);

        disguiseCard.addView(createActionBtn(
                fa ? "🎭 تغییر عنوان ظاهری برنامه" : "🎭 Change Disguise Title",
                "#1E293B",
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        showDisguisePickerDialog();
                    }
                }));

        col.addView(disguiseCard);

        sv.addView(col);
        root.addView(sv);
        setContentView(root);
    }

    private View createActionBtn(String text, String bgHex, View.OnClickListener l) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(12);
        b.setAllCaps(false);
        b.setBackground(roundedBg(bgHex, 10, null, 0));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, 0, 0, dp(8));
        b.setLayoutParams(lp);
        b.setOnClickListener(l);
        return b;
    }

    private void showSetPinDialog() {
        final boolean fa = isPersian();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "ثبت رمز پین عددی (PIN)" : "Set Numeric PIN");

        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        input.setHint(fa ? "حداقل ۴ رقم وارد کنید" : "Enter at least 4 digits");
        b.setView(input);

        b.setPositiveButton(fa ? "ذخیره پین" : "Save PIN", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                String pin = input.getText().toString().trim();
                if (pin.length() < 4) {
                    Toast.makeText(SecuritySettingsActivity.this,
                            fa ? "پین باید حداقل ۴ رقم باشد" : "PIN must be at least 4 digits",
                            Toast.LENGTH_SHORT).show();
                    return;
                }
                SecurityManager.setPin(SecuritySettingsActivity.this, pin);
                Toast.makeText(SecuritySettingsActivity.this,
                        fa ? "✓ رمز پین ذخیره شد (الگوی قبلی نیز حفظ گردید)" : "✓ PIN saved",
                        Toast.LENGTH_SHORT).show();
                buildUi();
            }
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    private void showSetPatternDialog() {
        final boolean fa = isPersian();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "ترسیم الگوی امنیتی (حداقل ۴ نقطه)" : "Draw Security Pattern (Min 4 dots)");

        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setGravity(Gravity.CENTER);
        wrap.setPadding(dp(16), dp(16), dp(16), dp(16));
        wrap.setBackgroundColor(Color.parseColor("#0F172A"));

        final PatternLockView plv = new PatternLockView(this);
        plv.setLayoutParams(new LinearLayout.LayoutParams(dp(250), dp(250)));
        wrap.addView(plv);

        b.setView(wrap);
        final AlertDialog dlg = b.create();

        plv.setOnPatternListener(new PatternLockView.OnPatternListener() {
            @Override
            public void onPatternDetected(String pattern) {
                String[] parts = pattern.split("-");
                if (parts.length < 4) {
                    Toast.makeText(SecuritySettingsActivity.this,
                            fa ? "حداقل ۴ نقطه را به هم وصل کنید" : "Connect at least 4 dots",
                            Toast.LENGTH_SHORT).show();
                    plv.clearPattern();
                    return;
                }
                SecurityManager.setPattern(SecuritySettingsActivity.this, pattern);
                Toast.makeText(SecuritySettingsActivity.this,
                        fa ? "✓ الگوی ترسیمی ذخیره شد (پین قبلی نیز حفظ گردید)" : "✓ Pattern saved",
                        Toast.LENGTH_SHORT).show();
                dlg.dismiss();
                buildUi();
            }
        });

        dlg.show();
    }

    private void showPriorityPickerDialog() {
        final boolean fa = isPersian();
        String[] opts = new String[]{
                fa ? "۱. اولویت اول با رمز پین (PIN) - در صورت فراموشی، ورود با الگو" : "1. Primary Priority: PIN Code (Fallback to Pattern)",
                fa ? "۲. اولویت اول با الگوی ترسیمی (Pattern) - در صورت فراموشی، ورود با پین" : "2. Primary Priority: Pattern (Fallback to PIN)"
        };
        new AlertDialog.Builder(this)
                .setTitle(fa ? "انتخاب اولویت قفل اول" : "Select Primary Lock Priority")
                .setItems(opts, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        SecurityManager.setPrimaryLockPriority(
                                SecuritySettingsActivity.this,
                                which == 0 ? SecurityManager.LOCK_PIN : SecurityManager.LOCK_PATTERN);
                        buildUi();
                    }
                })
                .show();
    }

    private void showDisguisePickerDialog() {
        final boolean fa = isPersian();
        final String[] modes = new String[]{
                AppDisguiseManager.MODE_DEFAULT,
                AppDisguiseManager.MODE_CLOCK,
                AppDisguiseManager.MODE_CALCULATOR,
                AppDisguiseManager.MODE_CALENDAR,
                AppDisguiseManager.MODE_NOTEPAD
        };
        String[] labels = new String[]{
                "VeyraVault (Default)",
                fa ? "ساعت جهانی و تقویم" : "World Clock & Calendar",
                fa ? "ماشین‌حساب مهندسی" : "Scientific Calculator",
                fa ? "تقویم هوشمند خورشیدی" : "Smart Solar Calendar",
                fa ? "دفترچه یادداشت شخصی" : "Personal Notepad"
        };
        new AlertDialog.Builder(this)
                .setTitle(fa ? "انتخاب عنوان ظاهری هدر" : "Select Header Disguise")
                .setItems(labels, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        AppDisguiseManager.setDisguiseMode(SecuritySettingsActivity.this, modes[which]);
                        buildUi();
                    }
                })
                .show();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        buildUi();
    }
}
""",
)

# ---------------------------------------------------------------------------
# 6. SECURITY LOCK ACTIVITY (SecurityLockActivity.java)
#    - Item 10: Supports BOTH PIN and Pattern!
#      Starts with the user's Primary Priority Lock.
#      If the user fails 2+ times (or taps the switch button), prompts:
#      "آیا از الگو استفاده می‌کنید؟ ورود با الگو" / "آیا از پین استفاده می‌کنید؟ ورود با پین"
#    - Item 11 Part 1: Stealth Anti-Uninstall Blocker (ZERO hint about disabling in settings)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/ui/SecurityLockActivity.java",
    r"""package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.security.SecurityManager;

public class SecurityLockActivity extends BaseActivity {

    private int currentDisplayedMode = SecurityManager.LOCK_PIN;
    private int failedAttempts = 0;
    private TextView tvErrorPrompt;
    private TextView btnSwitchSecondaryLock;

    @Override
    protected boolean shouldBypassSecurityLock() {
        return true;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        currentDisplayedMode = SecurityManager.getPrimaryLockPriority(this);
        if (currentDisplayedMode == SecurityManager.LOCK_NONE) {
            SecurityManager.setSessionUnlocked(true);
            finish();
            return;
        }
        renderLockScreen();
    }

    private int dp(int v) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    private GradientDrawable roundedBg(String hex, int radiusDp, String strokeHex, int strokeDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hex));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeDp > 0) {
            gd.setStroke(dp(strokeDp), Color.parseColor(strokeHex));
        }
        return gd;
    }

    private void renderLockScreen() {
        final boolean fa = isPersian();
        final boolean bothConfigured = SecurityManager.hasPin(this) && SecurityManager.hasPattern(this);
        boolean antiUninstallIntercept = getIntent().getBooleanExtra("anti_uninstall_intercept", false);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.parseColor("#090D16"));
        root.setPadding(dp(24), dp(24), dp(24), dp(24));

        if (antiUninstallIntercept) {
            TextView shieldAlert = new TextView(this);
            shieldAlert.setText(fa
                    ? "⛔ حذف مقدور نمی‌باشد! عملیات حذف یا غیرفعال‌سازی این برنامه مسدود است."
                    : "⛔ Uninstall is not permitted! Uninstallation or deactivation is blocked.");
            shieldAlert.setTextColor(Color.parseColor("#FCA5A5"));
            shieldAlert.setTextSize(13);
            shieldAlert.setTypeface(Typeface.DEFAULT_BOLD);
            shieldAlert.setGravity(Gravity.CENTER);
            shieldAlert.setPadding(dp(14), dp(10), dp(14), dp(10));
            shieldAlert.setBackground(roundedBg("#7F1D1D", 10, "#EF4444", 1));
            LinearLayout.LayoutParams aLp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            aLp.setMargins(0, 0, 0, dp(18));
            shieldAlert.setLayoutParams(aLp);
            root.addView(shieldAlert);
        }

        TextView lockIcon = new TextView(this);
        lockIcon.setText("🔒");
        lockIcon.setTextSize(42);
        lockIcon.setGravity(Gravity.CENTER);
        root.addView(lockIcon);

        TextView title = new TextView(this);
        title.setText(currentDisplayedMode == SecurityManager.LOCK_PIN
                ? (fa ? "ورود با رمز پین امنیتی" : "Enter Security PIN")
                : (fa ? "ترسیم الگوی امنیتی" : "Draw Security Pattern"));
        title.setTextColor(Color.WHITE);
        title.setTextSize(18);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(10), 0, dp(6));
        root.addView(title);

        tvErrorPrompt = new TextView(this);
        tvErrorPrompt.setTextColor(Color.parseColor("#F87171"));
        tvErrorPrompt.setTextSize(13);
        tvErrorPrompt.setGravity(Gravity.CENTER);
        tvErrorPrompt.setPadding(0, dp(4), 0, dp(12));
        root.addView(tvErrorPrompt);

        if (currentDisplayedMode == SecurityManager.LOCK_PIN) {
            final EditText pinInput = new EditText(this);
            pinInput.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
            pinInput.setHint(fa ? "رمز پین خود را وارد کنید" : "Enter PIN code");
            pinInput.setHintTextColor(Color.parseColor("#64748B"));
            pinInput.setTextColor(Color.WHITE);
            pinInput.setTextSize(18);
            pinInput.setGravity(Gravity.CENTER);
            pinInput.setPadding(dp(16), dp(12), dp(16), dp(12));
            pinInput.setBackground(roundedBg("#0F172A", 12, "#38BDF8", 1));
            LinearLayout.LayoutParams pLp = new LinearLayout.LayoutParams(
                    dp(240), ViewGroup.LayoutParams.WRAP_CONTENT);
            pLp.setMargins(0, 0, 0, dp(14));
            pinInput.setLayoutParams(pLp);
            root.addView(pinInput);

            Button btnUnlock = new Button(this);
            btnUnlock.setText(fa ? "🔓 باز کردن قفل" : "🔓 Unlock");
            btnUnlock.setTextColor(Color.WHITE);
            btnUnlock.setTextSize(14);
            btnUnlock.setTypeface(Typeface.DEFAULT_BOLD);
            btnUnlock.setAllCaps(false);
            btnUnlock.setBackground(roundedBg("#0284C7", 10, null, 0));
            btnUnlock.setLayoutParams(new LinearLayout.LayoutParams(dp(240), ViewGroup.LayoutParams.WRAP_CONTENT));
            btnUnlock.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    String entered = pinInput.getText().toString().trim();
                    if (SecurityManager.verifyPin(SecurityLockActivity.this, entered)) {
                        onUnlockSuccess();
                    } else {
                        pinInput.setText("");
                        onUnlockFailed(bothConfigured);
                    }
                }
            });
            root.addView(btnUnlock);
        } else {
            final PatternLockView plv = new PatternLockView(this);
            LinearLayout.LayoutParams plvLp = new LinearLayout.LayoutParams(dp(260), dp(260));
            plv.setLayoutParams(plvLp);
            plv.setOnPatternListener(new PatternLockView.OnPatternListener() {
                @Override
                public void onPatternDetected(String pattern) {
                    if (SecurityManager.verifyPattern(SecurityLockActivity.this, pattern)) {
                        onUnlockSuccess();
                    } else {
                        plv.clearPattern();
                        onUnlockFailed(bothConfigured);
                    }
                }
            });
            root.addView(plv);
        }

        // Secondary Lock Switch Button (Appears automatically after 2 failed attempts, or when tapped)
        btnSwitchSecondaryLock = new TextView(this);
        if (bothConfigured) {
            boolean switchedToPin = (currentDisplayedMode == SecurityManager.LOCK_PATTERN);
            btnSwitchSecondaryLock.setText(switchedToPin
                    ? (fa ? "🔄 آیا از رمز پین استفاده می‌کنید؟ ورود با پین ⬅" : "🔄 Using PIN instead? Switch to PIN Lock ⬅")
                    : (fa ? "🔄 آیا از الگو استفاده می‌کنید؟ ورود با الگو ⬅" : "🔄 Using Pattern instead? Switch to Pattern Lock ⬅"));
            btnSwitchSecondaryLock.setTextColor(Color.parseColor("#38BDF8"));
            btnSwitchSecondaryLock.setTextSize(13);
            btnSwitchSecondaryLock.setTypeface(Typeface.DEFAULT_BOLD);
            btnSwitchSecondaryLock.setGravity(Gravity.CENTER);
            btnSwitchSecondaryLock.setPadding(dp(16), dp(12), dp(16), dp(12));
            btnSwitchSecondaryLock.setBackground(roundedBg("#1E293B", 10, "#38BDF8", 1));
            LinearLayout.LayoutParams swLp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            swLp.setMargins(0, dp(20), 0, 0);
            btnSwitchSecondaryLock.setLayoutParams(swLp);
            btnSwitchSecondaryLock.setVisibility(failedAttempts >= 2 ? View.VISIBLE : View.GONE);
            btnSwitchSecondaryLock.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    currentDisplayedMode = (currentDisplayedMode == SecurityManager.LOCK_PIN)
                            ? SecurityManager.LOCK_PATTERN
                            : SecurityManager.LOCK_PIN;
                    failedAttempts = 0;
                    renderLockScreen();
                }
            });
            root.addView(btnSwitchSecondaryLock);
        }

        setContentView(root);
    }

    private void onUnlockSuccess() {
        SecurityManager.setSessionUnlocked(true);
        finish();
    }

    private void onUnlockFailed(boolean bothConfigured) {
        failedAttempts++;
        boolean fa = isPersian();
        if (bothConfigured && failedAttempts >= 2) {
            if (currentDisplayedMode == SecurityManager.LOCK_PIN) {
                tvErrorPrompt.setText(fa
                        ? "❌ رمز پین اشتباه است! در صورت تمایل از دکمه زیر با «الگو» وارد شوید:"
                        : "❌ Incorrect PIN! You can switch to Pattern Lock below:");
            } else {
                tvErrorPrompt.setText(fa
                        ? "❌ الگو اشتباه است! در صورت تمایل از دکمه زیر با «رمز پین» وارد شوید:"
                        : "❌ Incorrect Pattern! You can switch to PIN Lock below:");
            }
            if (btnSwitchSecondaryLock != null) {
                btnSwitchSecondaryLock.setVisibility(View.VISIBLE);
            }
        } else {
            tvErrorPrompt.setText(fa
                    ? ("❌ ورودی نامعتبر است (تلاش " + failedAttempts + ")")
                    : ("❌ Invalid credential (Attempt " + failedAttempts + ")"));
        }
    }

    @Override
    public void onBackPressed() {
        moveTaskToBack(true);
    }
}
""",
)

# ---------------------------------------------------------------------------
# 7. GUIDE ACTIVITY & ABOUT ACTIVITY (GuideActivity.java, AboutActivity.java)
# ---------------------------------------------------------------------------
write_file(
    "app/src/main/java/com/veyravault/space/ui/GuideActivity.java",
    r"""package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class GuideActivity extends BaseActivity {

    private int dp(int v) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean fa = isPersian();

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#090D16"));

        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setBackgroundColor(Color.parseColor("#0F172A"));
        topBar.setPadding(dp(14), dp(12), dp(14), dp(12));

        TextView back = new TextView(this);
        back.setText(fa ? " بازگشت ❯" : "❮ Back ");
        back.setTextColor(Color.parseColor("#38BDF8"));
        back.setTextSize(14);
        back.setTypeface(Typeface.DEFAULT_BOLD);
        back.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        topBar.addView(back);

        TextView title = new TextView(this);
        title.setText(fa ? "راهنمای کامل VeyraVault v3.0" : "VeyraVault v3.0 Guide");
        title.setTextColor(Color.WHITE);
        title.setTextSize(16);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setPadding(dp(12), 0, dp(12), 0);
        topBar.addView(title);

        root.addView(topBar);

        ScrollView sv = new ScrollView(this);
        TextView body = new TextView(this);
        body.setPadding(dp(18), dp(18), dp(18), dp(24));
        body.setTextColor(Color.parseColor("#E2E8F0"));
        body.setTextSize(13);
        body.setLineSpacing(dp(4), 1f);
        body.setText(fa
                ? "• تغییر نام هر فضا با دکمه سه نقطه (⋮) کنار نام فضا\n• مدل‌های Apple iPhone و پرچمداران اندروید با اولویت اختصاصی هر برنامه\n• نمایش منطقه به صورت شهر و کشور (مانند Falkenstein, Germany) و سپر IP نشست‌های فعال\n• مخزن مستقل APK (با حذف برنامه از گوشی، کلون داخل برنامه حذف نمی‌شود)\n• قفل دوگانه همزمان (پین و الگو) + سپر ضدحذف مطلق"
                : "• Rename any space via the 3-dots (⋮) button\n• Apple iPhone & flagship device models with per-app priority #1\n• City, Country region labels (e.g. Falkenstein, Germany) & Session IP Shield\n• Independent APK Vault (clones survive host app uninstallation)\n• Simultaneous PIN + Pattern Dual Lock & Anti-Uninstall Shield");
        sv.addView(body);
        root.addView(sv);

        setContentView(root);
    }
}
""",
)

write_file(
    "app/src/main/java/com/veyravault/space/ui/AboutActivity.java",
    r"""package com.veyravault.space.ui;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class AboutActivity extends BaseActivity {

    private int dp(int v) {
        return (int) TypedValue.applyDimension(
                TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
    }

    private GradientDrawable roundedBg(String hex, int radiusDp, String strokeHex, int strokeDp) {
        GradientDrawable gd = new GradientDrawable();
        gd.setColor(Color.parseColor(hex));
        gd.setCornerRadius(dp(radiusDp));
        if (strokeHex != null && strokeDp > 0) {
            gd.setStroke(dp(strokeDp), Color.parseColor(strokeHex));
        }
        return gd;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        final boolean fa = isPersian();

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#090D16"));

        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setBackgroundColor(Color.parseColor("#0F172A"));
        topBar.setPadding(dp(14), dp(12), dp(14), dp(12));

        TextView back = new TextView(this);
        back.setText(fa ? " بازگشت ❯" : "❮ Back ");
        back.setTextColor(Color.parseColor("#38BDF8"));
        back.setTextSize(14);
        back.setTypeface(Typeface.DEFAULT_BOLD);
        back.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        topBar.addView(back);

        TextView title = new TextView(this);
        title.setText(fa ? "درباره ما و ارتباط با سازنده" : "About Us & Contact");
        title.setTextColor(Color.WHITE);
        title.setTextSize(16);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setPadding(dp(12), 0, dp(12), 0);
        topBar.addView(title);

        root.addView(topBar);

        ScrollView sv = new ScrollView(this);
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(dp(18), dp(18), dp(18), dp(28));

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(18), dp(18), dp(18));
        card.setBackground(roundedBg("#0F172A", 16, "#1E3A8A", 1));

        TextView appTitle = new TextView(this);
        appTitle.setText("VeyraVault v3.0.0");
        appTitle.setTextColor(Color.parseColor("#38BDF8"));
        appTitle.setTextSize(20);
        appTitle.setTypeface(Typeface.DEFAULT_BOLD);
        card.addView(appTitle);

        TextView desc = new TextView(this);
        desc.setText(fa
                ? "پلتفرم پیشرفته ایزوله‌سازی، مدیریت هوشمند هویت سخت‌افزاری، موقعیت جغرافیایی و امنیت چندلایه بدون هیچ‌گونه تبلیغات یا ردیابی.\n\n• ایمیل رسمی: Vaultveyra@gmail.com\n• کانال و پشتیبانی تلگرام: @VaultVeyra\n• مجوز متن‌باز: Apache License 2.0"
                : "Advanced zero-telemetry virtualization, hardware identity management, smart location & multi-layer security platform.\n\n• Official Email: Vaultveyra@gmail.com\n• Telegram: @VaultVeyra\n• Open-Source License: Apache License 2.0");
        desc.setTextColor(Color.parseColor("#E2E8F0"));
        desc.setTextSize(13);
        desc.setLineSpacing(dp(4), 1f);
        desc.setPadding(0, dp(10), 0, dp(16));
        card.addView(desc);

        Button btnTg = new Button(this);
        btnTg.setText(fa ? "✈ ارتباط در تلگرام (@VaultVeyra)" : "✈ Contact on Telegram (@VaultVeyra)");
        btnTg.setTextColor(Color.WHITE);
        btnTg.setAllCaps(false);
        btnTg.setBackground(roundedBg("#0284C7", 10, null, 0));
        btnTg.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/VaultVeyra")));
                } catch (Throwable ignored) {
                }
            }
        });
        card.addView(btnTg);

        Button btnMail = new Button(this);
        btnMail.setText(fa ? "✉ ارسال ایمیل (Vaultveyra@gmail.com)" : "✉ Send Email (Vaultveyra@gmail.com)");
        btnMail.setTextColor(Color.WHITE);
        btnMail.setAllCaps(false);
        btnMail.setBackground(roundedBg("#1E293B", 10, "#38BDF8", 1));
        LinearLayout.LayoutParams mLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        mLp.setMargins(0, dp(10), 0, 0);
        btnMail.setLayoutParams(mLp);
        btnMail.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    Intent email = new Intent(Intent.ACTION_SENDTO, Uri.parse("mailto:Vaultveyra@gmail.com"));
                    startActivity(email);
                } catch (Throwable ignored) {
                }
            }
        });
        card.addView(btnMail);

        col.addView(card);
        sv.addView(col);
        root.addView(sv);
        setContentView(root);
    }
}
""",
)

print("[v3.0-Part2] All v3.0 UI Activity files generated cleanly with zero multiline string issues.")
