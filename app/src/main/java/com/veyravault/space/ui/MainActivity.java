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
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.ShortcutHelper;
import com.veyravault.space.core.VirtualHookManager;
import java.util.List;
import java.util.Map;

public class MainActivity extends BaseActivity {

    private LinearLayout spacesContainer;
    private boolean fa;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        fa = LocaleHelper.isPersian(this);
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
        CloneStore.GlobalEnvConfig gCfg = CloneStore.getGlobalEnv(this);
        bTitle.setText(fa ? "فضاهای چندگانه و موقعیت مکانی هوشمند" : "Multi-Space & Global Virtual Locations");
        banner.addView(bTitle);

        TextView bSub = new TextView(this);
        bSub.setTextColor(Color.parseColor("#DBEAFE"));
        bSub.setTextSize(12f);
        bSub.setText(fa
                ? ("مدل سراسری فعال: " + gCfg.brand.toUpperCase() + " " + gCfg.model + " | منطقه: " + gCfg.countryIso.toUpperCase())
                : ("Global Device: " + gCfg.brand.toUpperCase() + " " + gCfg.model + " | Region: " + gCfg.countryIso.toUpperCase()));
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
        btnToggleAll.setOnClickListener(new View.OnClickListener() {
            boolean allCollapsed = false;
            @Override
            public void onClick(View v) {
                allCollapsed = !allCollapsed;
                Map<Integer, List<CloneStore.CloneEntry>> map = CloneStore.getGroupedBySpace(MainActivity.this);
                for (Integer s : map.keySet()) {
                    CloneStore.setSpaceCollapsed(MainActivity.this, s, allCollapsed);
                }
                refreshSpaces();
            }
        });
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

        bottomBar.addView(makeNavButton(getString(R.string.nav_clones), true, new View.OnClickListener() {
            @Override public void onClick(View v) { refreshSpaces(); }
        }), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        bottomBar.addView(makeNavButton(getString(R.string.nav_global_env), false, new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, GlobalEnvironmentActivity.class));
            }
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

        bottomBar.addView(makeNavButton(getString(R.string.nav_security), false, new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, SecuritySettingsActivity.class));
            }
        }), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        bottomBar.addView(makeNavButton(getString(R.string.nav_about), false, new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, AboutActivity.class));
            }
        }), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        root.addView(bottomBar, bottomLp);
        setContentView(root);
    }

    private void refreshSpaces() {
        if (spacesContainer == null) return;
        spacesContainer.removeAllViews();
        Map<Integer, List<CloneStore.CloneEntry>> grouped = CloneStore.getGroupedBySpace(this);
        for (Map.Entry<Integer, List<CloneStore.CloneEntry>> entry : grouped.entrySet()) {
            spacesContainer.addView(buildSpaceCard(entry.getKey(), entry.getValue()));
        }
    }

    private View buildSpaceCard(final int spaceNum, final List<CloneStore.CloneEntry> clones) {
        final boolean collapsed = CloneStore.isSpaceCollapsed(this, spaceNum);
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

        header.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                CloneStore.setSpaceCollapsed(MainActivity.this, spaceNum, !collapsed);
                refreshSpaces();
            }
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
                Toast.makeText(MainActivity.this,
                        (fa ? "در حال اجرای " : "Launching ") + item.displayName + "...",
                        Toast.LENGTH_SHORT).show();
                Engine.launchClone(MainActivity.this, item);
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
            devSub.setText("📱 " + item.deviceBrand + " " + item.deviceModel);
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
                CloneStore.CloneEntry copy = new CloneStore.CloneEntry();
                copy.packageName = item.packageName;
                copy.userId = nextUid;
                copy.displayName = item.displayName;
                Engine.installPackageAsUser(copy.packageName, copy.userId);
                CloneStore.upsertClone(MainActivity.this, copy);
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
                Engine.uninstallClone(item.packageName, item.userId);
                CloneStore.removeClone(MainActivity.this, item.packageName, item.userId);
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
                            CloneStore.upsertClone(MainActivity.this, item);
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
                .setTitle(fa ? ("هویت دستگاه برای " + item.displayName + " (فضای " + item.getSpaceNumber() + ")")
                             : ("Device Identity for " + item.displayName))
                .setView(box)
                .setPositiveButton(fa ? "فعال‌سازی و ذخیره" : "Enable & Save", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        item.customDeviceEnabled = true;
                        item.deviceBrand = brandEt.getText().toString().trim();
                        item.deviceModel = modelEt.getText().toString().trim();
                        CloneStore.upsertClone(MainActivity.this, item);
                        VirtualHookManager.syncCloneHooks(MainActivity.this, item);
                        Toast.makeText(MainActivity.this,
                                fa ? "مشخصات دستگاه برای این کلون ثبت شد" : "Custom device identity saved for this clone",
                                Toast.LENGTH_SHORT).show();
                    }
                })
                .setNeutralButton(fa ? "استفاده از مدل سراسری" : "Use Global Default", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        item.customDeviceEnabled = false;
                        CloneStore.upsertClone(MainActivity.this, item);
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
                                Engine.uninstallClone(e.packageName, e.userId);
                                CloneStore.removeClone(MainActivity.this, e.packageName, e.userId);
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
