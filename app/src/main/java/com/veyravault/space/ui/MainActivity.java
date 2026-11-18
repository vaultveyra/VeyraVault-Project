package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.text.TextUtils;
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
import com.google.android.material.bottomsheet.BottomSheetDialog;
import com.veyravault.space.R;
import com.veyravault.space.core.AsyncCloneRepository;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.ShortcutHelper;
import com.veyravault.space.core.VirtualHookManager;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class MainActivity extends BaseActivity {

    private LinearLayout spacesContainer;
    private boolean fa;
    private AsyncCloneRepository repository;
    private long refreshGeneration;
    private View toggleAllButton;
    private TextView globalProfileSummary;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        fa = LocaleHelper.isPersian(this);
        repository = AsyncCloneRepository.getInstance(getApplicationContext());
        buildDashboardUi();
        handleShortcutLaunch(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        handleShortcutLaunch(intent);
    }

    private void handleShortcutLaunch(Intent intent) {
        if (intent != null && intent.hasExtra("shortcut_pkg")) {
            String pkg = intent.getStringExtra("shortcut_pkg");
            int uid = intent.getIntExtra("shortcut_uid", 0);
            CloneStore.CloneEntry e = CloneStore.getClone(this, pkg, uid);
            if (e != null) Engine.launchClone(this, e);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadGlobalProfileSummary();
        refreshSpaces();
    }

    private void buildDashboardUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#F3F5F9"));

        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setPadding(36, 32, 36, 20);

        TextView brandTitle = new TextView(this);
        brandTitle.setText("VeyraVault");
        brandTitle.setTextSize(22f);
        brandTitle.setTypeface(Typeface.DEFAULT_BOLD);
        brandTitle.setTextColor(Color.parseColor("#111827"));
        topBar.addView(brandTitle, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView btnLang = makePillChip(getString(R.string.lang_switch), "#DBEAFE", "#2563EB");
        btnLang.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                LocaleHelper.toggleLanguage(MainActivity.this);
                recreate();
            }
        });
        topBar.addView(btnLang);
        root.addView(topBar);

        LinearLayout banner = new LinearLayout(this);
        banner.setOrientation(LinearLayout.VERTICAL);
        banner.setBackgroundResource(R.drawable.bg_pill_blue);
        banner.setPadding(42, 32, 42, 32);
        LinearLayout.LayoutParams bannerLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        bannerLp.setMargins(36, 8, 36, 20);

        TextView bTitle = new TextView(this);
        bTitle.setTextColor(Color.WHITE);
        bTitle.setTextSize(16f);
        bTitle.setTypeface(Typeface.DEFAULT_BOLD);
        bTitle.setText(fa ? "فضاهای چندگانه و موقعیت مکانی هوشمند" : "Multi-Space & Global Virtual Locations");
        banner.addView(bTitle);

        TextView bSub = new TextView(this);
        bSub.setTextColor(Color.parseColor("#DBEAFE"));
        bSub.setTextSize(12f);
        bSub.setText(fa ? "در حال خواندن پروفایل ذخیره‌شده..." : "Loading saved profile...");
        globalProfileSummary = bSub;
        banner.addView(bSub);
        banner.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, GlobalEnvironmentActivity.class));
            }
        });
        root.addView(banner, bannerLp);

        LinearLayout secRow = new LinearLayout(this);
        secRow.setOrientation(LinearLayout.HORIZONTAL);
        secRow.setGravity(Gravity.CENTER_VERTICAL);
        secRow.setPadding(42, 8, 42, 12);

        TextView myClonesTv = new TextView(this);
        myClonesTv.setText(getString(R.string.my_clones));
        myClonesTv.setTextSize(18f);
        myClonesTv.setTypeface(Typeface.DEFAULT_BOLD);
        myClonesTv.setTextColor(Color.parseColor("#111827"));
        secRow.addView(myClonesTv, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView btnToggleAll = makePillChip(fa ? "جمع/باز کردن همه ⊞" : "Collapse/Expand All ⊞", "#FFFFFF", "#374151");
        toggleAllButton = btnToggleAll;
        btnToggleAll.setOnClickListener(v -> toggleAllSpaces());
        secRow.addView(btnToggleAll);
        root.addView(secRow);

        ScrollView sv = new ScrollView(this);
        spacesContainer = new LinearLayout(this);
        spacesContainer.setOrientation(LinearLayout.VERTICAL);
        spacesContainer.setPadding(32, 8, 32, 40);
        sv.addView(spacesContainer);
        root.addView(sv, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        LinearLayout bottomBar = new LinearLayout(this);
        bottomBar.setOrientation(LinearLayout.HORIZONTAL);
        bottomBar.setGravity(Gravity.CENTER);
        bottomBar.setBackgroundResource(R.drawable.bg_card_rounded);
        bottomBar.setPadding(20, 18, 20, 18);
        LinearLayout.LayoutParams bottomLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        bottomLp.setMargins(28, 8, 28, 24);

        bottomBar.addView(makeNavButton(fa ? "خانه" : "Dashboard", false, new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, DashboardActivity.class));
            }
        }), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        bottomBar.addView(makeNavButton(fa ? "فضاها" : "Spaces", true, new View.OnClickListener() {
            @Override public void onClick(View v) { refreshSpaces(); }
        }), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView fabPlus = new TextView(this);
        fabPlus.setText("+");
        fabPlus.setTextColor(Color.WHITE);
        fabPlus.setTextSize(28f);
        fabPlus.setGravity(Gravity.CENTER);
        fabPlus.setBackgroundResource(R.drawable.bg_pill_blue);
        LinearLayout.LayoutParams fabLp = new LinearLayout.LayoutParams(132, 132);
        fabLp.setMargins(16, 0, 16, 0);
        fabPlus.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, AddAppActivity.class));
            }
        });
        bottomBar.addView(fabPlus, fabLp);

        bottomBar.addView(makeNavButton("VPN", false, new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, VpnStatusActivity.class));
            }
        }), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        bottomBar.addView(makeNavButton(fa ? "تنظیمات" : "Settings", false, new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, SettingsHubActivity.class));
            }
        }), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        root.addView(bottomBar, bottomLp);
        setContentView(root);
    }

    private void loadGlobalProfileSummary() {
        repository.loadGlobalEnvironment(result -> {
            if (isFinishing() || isDestroyed() || globalProfileSummary == null) return;
            if (!result.isSuccess() || result.getValue() == null) {
                globalProfileSummary.setText(fa ? "پروفایل ذخیره‌شده در دسترس نیست" : "Saved profile is unavailable");
                return;
            }
            CloneStore.GlobalEnvConfig profile = result.getValue();
            globalProfileSummary.setText(fa
                    ? ("پروفایل ذخیره‌شده: " + profile.brand.toUpperCase(java.util.Locale.ROOT)
                            + " " + profile.model + " | منطقه: " + profile.countryIso.toUpperCase(java.util.Locale.ROOT))
                    : ("Saved Profile: " + profile.brand.toUpperCase(java.util.Locale.ROOT)
                            + " " + profile.model + " | Region: " + profile.countryIso.toUpperCase(java.util.Locale.ROOT)));
        });
    }

    private void refreshSpaces() {
        if (spacesContainer == null) return;
        final long request = ++refreshGeneration;
        repository.loadClones(cloneResult -> {
            if (!isCurrentRefresh(request)) return;
            if (!cloneResult.isSuccess()) {
                showSpaceLoadFailure(cloneResult.getMessage());
                return; // Preserve the last known UI; never render corrupt data as an empty registry.
            }
            repository.loadCollapsedSpaces(collapsedResult -> {
                if (!isCurrentRefresh(request)) return;
                if (!collapsedResult.isSuccess() || collapsedResult.getValue() == null) {
                    showSpaceLoadFailure(collapsedResult.getMessage());
                    return; // Do not silently expand every Space when collapsed-state data is unreadable.
                }
                Map<Integer, List<CloneStore.CloneEntry>> grouped = groupClonesBySpace(cloneResult.getValue());
                Set<Integer> collapsedSpaces = collapsedResult.getValue();
                spacesContainer.removeAllViews();
                for (Map.Entry<Integer, List<CloneStore.CloneEntry>> entry : grouped.entrySet()) {
                    spacesContainer.addView(buildSpaceCard(entry.getKey(), entry.getValue(),
                            collapsedSpaces.contains(entry.getKey())));
                }
            });
        });
    }

    private boolean isCurrentRefresh(long request) {
        return request == refreshGeneration && !isFinishing() && !isDestroyed();
    }

    private void showSpaceLoadFailure(String detail) {
        if (isFinishing() || isDestroyed()) return;
        String message = fa ? "خواندن فهرست فضاها ناموفق بود؛ اطلاعات قبلی نمایش‌داده‌شده حفظ شد."
                : "Could not read Spaces; the previously displayed data was preserved.";
        if (detail != null && !detail.trim().isEmpty()) message += " " + detail;
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private Map<Integer, List<CloneStore.CloneEntry>> groupClonesBySpace(List<CloneStore.CloneEntry> clones) {
        Map<Integer, List<CloneStore.CloneEntry>> grouped = new LinkedHashMap<Integer, List<CloneStore.CloneEntry>>();
        for (CloneStore.CloneEntry clone : clones) {
            int spaceNumber = clone.getSpaceNumber();
            if (!grouped.containsKey(spaceNumber)) grouped.put(spaceNumber, new ArrayList<CloneStore.CloneEntry>());
            grouped.get(spaceNumber).add(clone);
        }
        if (grouped.isEmpty()) grouped.put(1, new ArrayList<CloneStore.CloneEntry>());
        return grouped;
    }

    private void toggleAllSpaces() {
        if (toggleAllButton != null) toggleAllButton.setEnabled(false);
        repository.loadClones(cloneResult -> {
            if (isFinishing() || isDestroyed()) return;
            if (!cloneResult.isSuccess()) {
                finishToggleAllWithFailure(cloneResult.getMessage());
                return;
            }
            repository.loadCollapsedSpaces(collapsedResult -> {
                if (isFinishing() || isDestroyed()) return;
                if (!collapsedResult.isSuccess() || collapsedResult.getValue() == null) {
                    finishToggleAllWithFailure(collapsedResult.getMessage());
                    return;
                }
                Map<Integer, List<CloneStore.CloneEntry>> grouped = groupClonesBySpace(cloneResult.getValue());
                Set<Integer> collapsed = new HashSet<Integer>(collapsedResult.getValue());
                boolean allCollapsed = true;
                List<Integer> spaceNumbers = new ArrayList<Integer>(grouped.keySet());
                for (Integer number : spaceNumbers) {
                    if (!collapsed.contains(number)) { allCollapsed = false; break; }
                }
                setAllSpacesCollapsed(spaceNumbers, !allCollapsed, 0);
            });
        });
    }

    private void setAllSpacesCollapsed(final List<Integer> spaceNumbers, final boolean collapsed, final int index) {
        if (isFinishing() || isDestroyed()) return;
        if (index >= spaceNumbers.size()) {
            if (toggleAllButton != null) toggleAllButton.setEnabled(true);
            refreshSpaces();
            return;
        }
        repository.setSpaceCollapsed(spaceNumbers.get(index), collapsed, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                finishToggleAllWithFailure(result.getMessage());
                return; // Earlier commits may have succeeded; reload and report the partial outcome.
            }
            setAllSpacesCollapsed(spaceNumbers, collapsed, index + 1);
        });
    }

    private void finishToggleAllWithFailure(String detail) {
        if (toggleAllButton != null) toggleAllButton.setEnabled(true);
        if (isFinishing() || isDestroyed()) return;
        String message = fa ? "تغییر همه فضاها کامل نشد؛ ممکن است بخشی از تغییرات ذخیره شده باشد."
                : "Could not update every Space; some earlier changes may already be saved.";
        if (detail != null && !detail.trim().isEmpty()) message += " " + detail;
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
        refreshSpaces();
    }

    private View buildSpaceCard(final int spaceNum, final List<CloneStore.CloneEntry> clones,
                                final boolean collapsed) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackgroundResource(R.drawable.bg_card_rounded);
        card.setPadding(32, 28, 32, 28);
        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardLp.bottomMargin = 28;
        card.setLayoutParams(cardLp);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);

        TextView chevron = new TextView(this);
        chevron.setText(collapsed ? "⌄" : "⌃");
        chevron.setTextSize(22f);
        chevron.setTextColor(Color.parseColor("#6B7280"));
        chevron.setPadding(12, 0, 20, 0);
        header.addView(chevron);

        LinearLayout previewBox = new LinearLayout(this);
        previewBox.setOrientation(LinearLayout.HORIZONTAL);
        previewBox.setGravity(Gravity.CENTER_VERTICAL);
        if (collapsed && !clones.isEmpty()) {
            int maxIcons = Math.min(3, clones.size());
            for (int i = 0; i < maxIcons; i++) {
                ImageView mini = new ImageView(this);
                mini.setImageDrawable(loadAppIcon(clones.get(i).packageName));
                LinearLayout.LayoutParams mlp = new LinearLayout.LayoutParams(68, 68);
                if (i > 0) mlp.setMargins(-18, 0, 0, 0);
                previewBox.addView(mini, mlp);
            }
            TextView countPill = makePillChip(clones.size() + "+", "#E5E7EB", "#4B5563");
            LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            clp.setMargins(12, 0, 12, 0);
            previewBox.addView(countPill, clp);
        }
        header.addView(previewBox, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        final int uid = spaceNum - 1;
        boolean gmsOn = Engine.isGmsInstalled(uid);
        TextView gmsChip = makePillChip(gmsOn ? "GMS ✓" : "GMS +", gmsOn ? "#D1FAE5" : "#F3F4F6", gmsOn ? "#065F46" : "#6B7280");
        gmsChip.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                boolean next = !Engine.isGmsInstalled(uid);
                Engine.setGmsEnabled(uid, next);
                Toast.makeText(MainActivity.this,
                        fa ? ("سرویس گوگل‌پلی (GMS) برای فضای " + spaceNum + (next ? " فعال شد" : " غیرفعال شد"))
                           : ("Google Play Services for Space " + spaceNum + (next ? " enabled" : " disabled")),
                        Toast.LENGTH_SHORT).show();
                refreshSpaces();
            }
        });
        LinearLayout.LayoutParams gmlp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        gmlp.setMargins(12, 0, 12, 0);
        header.addView(gmsChip, gmlp);

        TextView badge = makePillChip(String.valueOf(spaceNum), "#2563EB", "#FFFFFF");
        header.addView(badge);

        TextView spaceTitle = new TextView(this);
        spaceTitle.setText("  " + getString(R.string.space_label));
        spaceTitle.setTextSize(17f);
        spaceTitle.setTypeface(Typeface.DEFAULT_BOLD);
        spaceTitle.setTextColor(Color.parseColor("#111827"));
        header.addView(spaceTitle);

        header.setOnClickListener(v -> {
            header.setEnabled(false);
            repository.setSpaceCollapsed(spaceNum, !collapsed, result -> {
                if (isFinishing() || isDestroyed()) return;
                header.setEnabled(true);
                if (result.isSuccess()) {
                    refreshSpaces();
                } else {
                    Toast.makeText(MainActivity.this,
                            (fa ? "وضعیت باز/بسته ذخیره نشد: " : "Space collapse state was not saved: ")
                                    + result.getMessage(),
                            Toast.LENGTH_LONG).show();
                }
            });
        });
        card.addView(header);

        if (!collapsed) {
            if (clones.isEmpty()) {
                TextView emptyTv = new TextView(this);
                emptyTv.setText(fa ? "هنوز برنامه‌ای در این فضا نیست. دکمه + پایین را بزنید." : "No apps in this space yet. Tap + below to add.");
                emptyTv.setTextColor(Color.parseColor("#9CA3AF"));
                emptyTv.setPadding(16, 32, 16, 16);
                card.addView(emptyTv);
            } else {
                GridLayout grid = new GridLayout(this);
                grid.setColumnCount(4);
                grid.setPadding(0, 24, 0, 8);
                int cellWidth = (getResources().getDisplayMetrics().widthPixels - 160) / 4;
                for (final CloneStore.CloneEntry item : clones) {
                    grid.addView(buildCloneCell(item, cellWidth));
                }
                card.addView(grid);
            }
        }
        return card;
    }

    private View buildCloneCell(final CloneStore.CloneEntry item, int width) {
        LinearLayout cell = new LinearLayout(this);
        cell.setOrientation(LinearLayout.VERTICAL);
        cell.setGravity(Gravity.CENTER_HORIZONTAL);
        cell.setPadding(8, 16, 8, 16);
        cell.setLayoutParams(new ViewGroup.LayoutParams(width, ViewGroup.LayoutParams.WRAP_CONTENT));

        FrameLayout iconFrame = new FrameLayout(this);
        ImageView iconIv = new ImageView(this);
        iconIv.setImageDrawable(loadAppIcon(item.packageName));
        FrameLayout.LayoutParams iconLp = new FrameLayout.LayoutParams(126, 126, Gravity.CENTER);
        iconFrame.addView(iconIv, iconLp);

        TextView spaceBadge = new TextView(this);
        spaceBadge.setText(String.valueOf(item.getSpaceNumber()));
        spaceBadge.setTextColor(Color.WHITE);
        spaceBadge.setTextSize(10f);
        spaceBadge.setTypeface(Typeface.DEFAULT_BOLD);
        spaceBadge.setBackgroundResource(R.drawable.bg_pill_blue);
        spaceBadge.setPadding(14, 2, 14, 2);
        FrameLayout.LayoutParams badgeLp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP | Gravity.START);
        iconFrame.addView(spaceBadge, badgeLp);

        iconFrame.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                boolean launched = Engine.launchClone(MainActivity.this, item);
                Toast.makeText(MainActivity.this,
                        launched
                                ? ((fa ? "در حال اجرای " : "Launching ") + item.displayName + "...")
                                : (fa ? "اجرای کلون ناموفق بود؛ وضعیت نصب و موتور را بررسی کنید." : "Clone launch failed. Check installation and engine status."),
                        Toast.LENGTH_SHORT).show();
            }
        });
        cell.addView(iconFrame);

        LinearLayout labelRow = new LinearLayout(this);
        labelRow.setOrientation(LinearLayout.HORIZONTAL);
        labelRow.setGravity(Gravity.CENTER);
        labelRow.setPadding(0, 10, 0, 0);

        TextView dots = new TextView(this);
        dots.setText("⋮");
        dots.setTextSize(17f);
        dots.setTypeface(Typeface.DEFAULT_BOLD);
        dots.setTextColor(Color.parseColor("#6B7280"));
        dots.setPadding(10, 0, 10, 0);
        dots.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showCloneConfigBottomSheet(item);
            }
        });
        labelRow.addView(dots);

        TextView nameTv = new TextView(this);
        nameTv.setText(item.displayName);
        nameTv.setTextSize(12f);
        nameTv.setTextColor(Color.parseColor("#374151"));
        nameTv.setSingleLine(true);
        nameTv.setEllipsize(TextUtils.TruncateAt.END);
        labelRow.addView(nameTv);

        labelRow.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showCloneConfigBottomSheet(item);
            }
        });
        cell.addView(labelRow);
        return cell;
    }

    private void showCloneConfigBottomSheet(final CloneStore.CloneEntry item) {
        final BottomSheetDialog sheet = new BottomSheetDialog(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundResource(R.drawable.bg_card_rounded);
        root.setPadding(42, 32, 42, 48);

        LinearLayout topRow = new LinearLayout(this);
        topRow.setOrientation(LinearLayout.HORIZONTAL);
        topRow.setGravity(Gravity.CENTER_VERTICAL);

        TextView btnSetLoc = new TextView(this);
        btnSetLoc.setText(getString(R.string.set_location));
        btnSetLoc.setTextColor(Color.WHITE);
        btnSetLoc.setTextSize(14f);
        btnSetLoc.setTypeface(Typeface.DEFAULT_BOLD);
        btnSetLoc.setBackgroundResource(R.drawable.bg_pill_blue);
        btnSetLoc.setPadding(42, 22, 42, 22);
        btnSetLoc.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                sheet.dismiss();
                Intent i = new Intent(MainActivity.this, SetLocationActivity.class);
                i.putExtra("pkg", item.packageName);
                i.putExtra("uid", item.userId);
                startActivity(i);
            }
        });
        topRow.addView(btnSetLoc);

        LinearLayout infoCol = new LinearLayout(this);
        infoCol.setOrientation(LinearLayout.VERTICAL);
        infoCol.setGravity(Gravity.END);
        infoCol.setPadding(24, 0, 24, 0);

        TextView titleTv = new TextView(this);
        titleTv.setText(item.displayName);
        titleTv.setTextSize(17f);
        titleTv.setTypeface(Typeface.DEFAULT_BOLD);
        titleTv.setTextColor(Color.parseColor("#111827"));
        infoCol.addView(titleTv);

        TextView locSub = new TextView(this);
        locSub.setTextSize(12f);
        locSub.setTextColor(item.mockGpsEnabled ? Color.parseColor("#2563EB") : Color.parseColor("#9CA3AF"));
        locSub.setText(item.mockGpsEnabled
                ? String.format("📍 %.4f, %.4f", item.latitude, item.longitude)
                : (getString(R.string.no_location_set) + " 📍"));
        infoCol.addView(locSub);

        if (item.customDeviceEnabled && !item.deviceModel.isEmpty()) {
            TextView devSub = new TextView(this);
            devSub.setTextSize(11f);
            devSub.setTextColor(Color.parseColor("#10B981"));
            devSub.setText((fa ? "📱 پروفایل ذخیره‌شده: " : "📱 Saved profile: ") + item.deviceBrand + " " + item.deviceModel);
            infoCol.addView(devSub);
        }

        topRow.addView(infoCol, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        ImageView iconIv = new ImageView(this);
        iconIv.setImageDrawable(loadAppIcon(item.packageName));
        topRow.addView(iconIv, new LinearLayout.LayoutParams(120, 120));
        root.addView(topRow);

        TextView cfgHeader = new TextView(this);
        cfgHeader.setText(getString(R.string.configuration));
        cfgHeader.setTextSize(16f);
        cfgHeader.setTypeface(Typeface.DEFAULT_BOLD);
        cfgHeader.setTextColor(Color.parseColor("#111827"));
        cfgHeader.setPadding(0, 36, 0, 24);
        root.addView(cfgHeader);

        GridLayout actionGrid = new GridLayout(this);
        actionGrid.setColumnCount(3);
        int btnW = (getResources().getDisplayMetrics().widthPixels - 120) / 3;

        actionGrid.addView(makeSheetActionBtn("🏠", getString(R.string.add_to_home), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                ShortcutHelper.addCloneToHome(MainActivity.this, item);
            }
        }));

        actionGrid.addView(makeSheetActionBtn("✏️", getString(R.string.rename), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                showRenameDialog(item);
            }
        }));

        actionGrid.addView(makeSheetActionBtn("⊞+", getString(R.string.duplicate), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                int nextUid = CloneStore.nextFreeUserIdForPackage(MainActivity.this, item.packageName);
                if (nextUid < 0) {
                    Toast.makeText(MainActivity.this,
                            fa ? "فهرست کلون‌ها قابل اعتبارسنجی نیست؛ تکثیر متوقف شد."
                               : "Clone registry could not be validated; duplication was stopped.",
                            Toast.LENGTH_LONG).show();
                    return;
                }
                CloneStore.CloneEntry copy = new CloneStore.CloneEntry();
                copy.packageName = item.packageName;
                copy.userId = nextUid;
                copy.displayName = item.displayName;
                if (!Engine.installPackageAsUser(copy.packageName, copy.userId)) {
                    Toast.makeText(MainActivity.this,
                            fa ? "ساخت کلون ناموفق بود؛ اطلاعات فضا ثبت نشد." : "Clone installation failed; no space entry was saved.",
                            Toast.LENGTH_LONG).show();
                    return;
                }
                if (!CloneStore.upsertClone(MainActivity.this, copy)) {
                    boolean cleanupConfirmed = Engine.uninstallClone(copy.packageName, copy.userId);
                    Toast.makeText(MainActivity.this,
                            fa ? (cleanupConfirmed
                                    ? "ثبت کلون جدید ناموفق بود؛ نصب جدید پاک شد."
                                    : "ثبت کلون جدید ناموفق بود و حذف نصب تأیید نشد؛ وضعیت را بررسی کن.")
                               : (cleanupConfirmed
                                    ? "Clone registry save failed; the new installation was removed."
                                    : "Clone registry save failed and uninstall could not be confirmed; inspect this clone."),
                            Toast.LENGTH_LONG).show();
                    return;
                }
                refreshSpaces();
            }
        }));

        actionGrid.addView(makeSheetActionBtn("📱", getString(R.string.device_identity), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                showPerCloneDeviceIdentityDialog(item);
            }
        }));

        actionGrid.addView(makeSheetActionBtn("🛡️", getString(R.string.permissions), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                Intent i = new Intent(MainActivity.this, PermissionsActivity.class);
                i.putExtra("pkg", item.packageName);
                i.putExtra("uid", item.userId);
                startActivity(i);
            }
        }));

        actionGrid.addView(makeSheetActionBtn("⏻", getString(R.string.stop_app), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                Engine.stopClone(item.packageName, item.userId);
                Toast.makeText(MainActivity.this, fa ? "برنامه متوقف شد" : "Clone stopped", Toast.LENGTH_SHORT).show();
            }
        }));

        actionGrid.addView(makeSheetActionBtn("🧹", getString(R.string.clear_data), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                Engine.clearCloneData(item.packageName, item.userId);
                Toast.makeText(MainActivity.this, fa ? "داده‌های کلون پاکسازی شد" : "Clone data cleared", Toast.LENGTH_SHORT).show();
            }
        }));

        actionGrid.addView(makeSheetActionBtn("🗑️", getString(R.string.uninstall), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                if (!Engine.uninstallClone(item.packageName, item.userId)) {
                    Toast.makeText(MainActivity.this,
                            fa ? "حذف کلون از موتور تأیید نشد؛ رکورد فضا حفظ شد."
                               : "The engine did not confirm uninstall; the Space record was preserved.",
                            Toast.LENGTH_LONG).show();
                    return;
                }
                if (!CloneStore.removeClone(MainActivity.this, item.packageName, item.userId)) {
                    Toast.makeText(MainActivity.this,
                            fa ? "برنامه حذف شد، اما به‌روزرسانی فهرست فضاها ناموفق بود."
                               : "The virtual app was uninstalled, but the Space registry could not be updated.",
                            Toast.LENGTH_LONG).show();
                }
                refreshSpaces();
            }
        }));

        actionGrid.addView(makeSheetActionBtn("📦", getString(R.string.batch_uninstall), btnW, new View.OnClickListener() {
            @Override public void onClick(View v) {
                sheet.dismiss();
                showBatchUninstallDialog();
            }
        }));

        root.addView(actionGrid);
        sheet.setContentView(root);
        sheet.show();
    }

    private View makeSheetActionBtn(String emoji, String label, int width, View.OnClickListener listener) {
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setGravity(Gravity.CENTER);
        wrap.setPadding(12, 16, 12, 16);
        wrap.setLayoutParams(new ViewGroup.LayoutParams(width, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView iconBox = new TextView(this);
        iconBox.setText(emoji);
        iconBox.setTextSize(22f);
        iconBox.setGravity(Gravity.CENTER);
        iconBox.setBackgroundResource(R.drawable.bg_square_action);
        wrap.addView(iconBox, new LinearLayout.LayoutParams(144, 144));

        TextView tv = new TextView(this);
        tv.setText(label);
        tv.setTextSize(12f);
        tv.setTextColor(Color.parseColor("#374151"));
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(0, 10, 0, 0);
        wrap.addView(tv);

        wrap.setOnClickListener(listener);
        return wrap;
    }

    private void showRenameDialog(final CloneStore.CloneEntry item) {
        final EditText et = new EditText(this);
        et.setText(item.displayName);
        new AlertDialog.Builder(this)
                .setTitle(getString(R.string.rename))
                .setView(et)
                .setPositiveButton("OK", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        String n = et.getText().toString().trim();
                        if (!n.isEmpty()) {
                            item.displayName = n;
                            if (!CloneStore.upsertClone(MainActivity.this, item)) {
                                Toast.makeText(MainActivity.this,
                                        fa ? "ذخیره ناموفق بود؛ اطلاعات قبلی حفظ شد."
                                           : "Save failed; the previous registry data was preserved.",
                                        Toast.LENGTH_LONG).show();
                                return;
                            }
                            refreshSpaces();
                        }
                    }
                })
                .setNegativeButton(fa ? "انصراف" : "Cancel", null)
                .show();
    }

    private void showPerCloneDeviceIdentityDialog(final CloneStore.CloneEntry item) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(48, 32, 48, 16);

        final String[] presets = {
            fa ? "سفارشی" : "Custom",
            "Samsung | SM-S928B (Galaxy S24 Ultra)",
            "Samsung | SM-A546E (Galaxy A54 5G)",
            "Xiaomi | 23078PND5G (Xiaomi 13T Pro)",
            "Google | Pixel 8 Pro",
            "OnePlus | CPH2449 (OnePlus 11)",
            "Desktop | Web Browser Session"
        };

        final EditText brandEt = new EditText(this);
        brandEt.setHint(fa ? "برند (مثلاً Samsung)" : "Brand (e.g. Samsung)");
        brandEt.setText(item.deviceBrand.isEmpty() ? "Samsung" : item.deviceBrand);
        box.addView(brandEt);

        final EditText modelEt = new EditText(this);
        modelEt.setHint(fa ? "مدل دستگاه در نشست‌ها (مثلاً Galaxy S24 Ultra)" : "Session Device Model (e.g. Galaxy S24 Ultra)");
        modelEt.setText(item.deviceModel);
        box.addView(modelEt);

        for (int i = 1; i < presets.length; i++) {
            final String p = presets[i];
            TextView chip = makePillChip(p, "#F3F4F6", "#1F2937");
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.topMargin = 10;
            chip.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    String[] parts = p.split("\\|");
                    brandEt.setText(parts[0].trim());
                    modelEt.setText(parts[1].trim());
                }
            });
            box.addView(chip, lp);
        }

        new AlertDialog.Builder(this)
                .setTitle(fa ? ("اطلاعات پروفایل دستگاه برای " + item.displayName + " (فضای " + item.getSpaceNumber() + ")")
                             : ("Saved Device Profile for " + item.displayName))
                .setView(box)
                .setPositiveButton(fa ? "ذخیره اطلاعات پروفایل" : "Save Profile Metadata", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        item.customDeviceEnabled = true;
                        item.deviceBrand = brandEt.getText().toString().trim();
                        item.deviceModel = modelEt.getText().toString().trim();
                        if (!CloneStore.upsertClone(MainActivity.this, item)) {
                            Toast.makeText(MainActivity.this,
                                    fa ? "ذخیره پروفایل ناموفق بود؛ تغییر اعمال نشد."
                                       : "Profile save failed; the change was not applied.",
                                    Toast.LENGTH_LONG).show();
                            return;
                        }
                        VirtualHookManager.syncCloneHooks(MainActivity.this, item);
                        Toast.makeText(MainActivity.this,
                                fa ? "اطلاعات پروفایل ذخیره شد؛ موتور فعلی آن را روی کلون اعمال نمی‌کند." : "Profile metadata saved; the current engine does not apply it to this clone.",
                                Toast.LENGTH_SHORT).show();
                    }
                })
                .setNeutralButton(fa ? "استفاده از پروفایل سراسری ذخیره‌شده" : "Use Saved Global Profile", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        item.customDeviceEnabled = false;
                        if (!CloneStore.upsertClone(MainActivity.this, item)) {
                            Toast.makeText(MainActivity.this,
                                    fa ? "ذخیره تنظیمات ناموفق بود؛ اطلاعات قبلی حفظ شد."
                                       : "Settings save failed; previous data was preserved.",
                                    Toast.LENGTH_LONG).show();
                        }
                    }
                })
                .setNegativeButton(fa ? "بستن" : "Close", null)
                .show();
    }

    private void showBatchUninstallDialog() {
        final List<CloneStore.CloneEntry> all = CloneStore.getAll(this);
        if (all.isEmpty()) return;
        String[] labels = new String[all.size()];
        final boolean[] checked = new boolean[all.size()];
        for (int i = 0; i < all.size(); i++) {
            CloneStore.CloneEntry e = all.get(i);
            labels[i] = e.displayName + " (" + getString(R.string.space_label) + " " + e.getSpaceNumber() + ")";
        }
        new AlertDialog.Builder(this)
                .setTitle(getString(R.string.batch_uninstall))
                .setMultiChoiceItems(labels, checked, new DialogInterface.OnMultiChoiceClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int which, boolean isChecked) {
                        checked[which] = isChecked;
                    }
                })
                .setPositiveButton(getString(R.string.uninstall), new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        for (int i = 0; i < all.size(); i++) {
                            if (checked[i]) {
                                CloneStore.CloneEntry e = all.get(i);
                                if (Engine.uninstallClone(e.packageName, e.userId)) {
                                    if (!CloneStore.removeClone(MainActivity.this, e.packageName, e.userId)) {
                                        Toast.makeText(MainActivity.this,
                                                fa ? "حذف برنامه انجام شد اما ثبت فهرست به‌روزرسانی نشد."
                                                   : "App uninstall succeeded, but the Space registry update failed.",
                                                Toast.LENGTH_LONG).show();
                                    }
                                } else {
                                    Toast.makeText(MainActivity.this,
                                            fa ? "حذف یک کلون تأیید نشد؛ رکورد آن حفظ شد."
                                               : "One clone uninstall was not confirmed; its registry entry was preserved.",
                                            Toast.LENGTH_LONG).show();
                                }
                            }
                        }
                        refreshSpaces();
                    }
                })
                .setNegativeButton(fa ? "انصراف" : "Cancel", null)
                .show();
    }

    private Drawable loadAppIcon(String pkg) {
        try {
            return getPackageManager().getApplicationIcon(pkg);
        } catch (PackageManager.NameNotFoundException e) {
            return getResources().getDrawable(R.drawable.ic_launcher_vault);
        }
    }

    private TextView makePillChip(String text, String bgHex, String fgHex) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextSize(12f);
        tv.setTypeface(Typeface.DEFAULT_BOLD);
        tv.setTextColor(Color.parseColor(fgHex));
        tv.setBackgroundResource(R.drawable.bg_pill_lightblue);
        tv.getBackground().setTint(Color.parseColor(bgHex));
        tv.setPadding(28, 12, 28, 12);
        return tv;
    }

    private View makeNavButton(String title, boolean active, View.OnClickListener l) {
        TextView tv = new TextView(this);
        tv.setText(title);
        tv.setGravity(Gravity.CENTER);
        tv.setTextSize(12f);
        tv.setTypeface(active ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        tv.setTextColor(Color.parseColor(active ? "#2563EB" : "#6B7280"));
        tv.setPadding(8, 16, 8, 16);
        tv.setOnClickListener(l);
        return tv;
    }
}
