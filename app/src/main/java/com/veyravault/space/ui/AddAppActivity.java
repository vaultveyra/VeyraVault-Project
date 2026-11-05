package com.veyravault.space.ui;

import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.GridLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.R;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.LocaleHelper;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class AddAppActivity extends BaseActivity {

    private static class InstalledApp {
        String pkg;
        String label;
        Drawable icon;
    }

    private final List<InstalledApp> allApps = new ArrayList<InstalledApp>();
    private final Set<String> batchSelected = new HashSet<String>();
    private boolean batchMode = false;
    private GridLayout grid;
    private Button batchConfirmBtn;
    private boolean fa;
    private String currentQuery = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        fa = LocaleHelper.isPersian(this);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#F3F5F9"));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(36, 32, 36, 20);

        final TextView batchBtn = new TextView(this);
        batchBtn.setText(getString(R.string.batch_clone));
        batchBtn.setTextColor(Color.parseColor("#2563EB"));
        batchBtn.setBackgroundResource(R.drawable.bg_pill_lightblue);
        batchBtn.setPadding(32, 16, 32, 16);
        batchBtn.setTypeface(Typeface.DEFAULT_BOLD);
        batchBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                batchMode = !batchMode;
                batchSelected.clear();
                batchConfirmBtn.setVisibility(batchMode ? View.VISIBLE : View.GONE);
                renderGrid(currentQuery);
            }
        });
        header.addView(batchBtn);

        TextView title = new TextView(this);
        title.setText(getString(R.string.my_apps));
        title.setTextSize(20f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.parseColor("#111827"));
        title.setGravity(Gravity.CENTER);
        header.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView backBtn = new TextView(this);
        backBtn.setText("→");
        backBtn.setTextSize(24f);
        backBtn.setTextColor(Color.parseColor("#111827"));
        backBtn.setPadding(20, 0, 20, 0);
        backBtn.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { finish(); }
        });
        header.addView(backBtn);
        root.addView(header);

        EditText searchEt = new EditText(this);
        searchEt.setHint("🔍  " + getString(R.string.search_apps));
        searchEt.setBackgroundResource(R.drawable.bg_card_rounded);
        searchEt.setPadding(42, 28, 42, 28);
        LinearLayout.LayoutParams slp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        slp.setMargins(36, 12, 36, 20);
        root.addView(searchEt, slp);

        ScrollView sv = new ScrollView(this);
        grid = new GridLayout(this);
        grid.setColumnCount(4);
        grid.setPadding(24, 12, 24, 32);
        sv.addView(grid);
        root.addView(sv, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        batchConfirmBtn = new Button(this);
        batchConfirmBtn.setBackgroundResource(R.drawable.bg_pill_blue);
        batchConfirmBtn.setTextColor(Color.WHITE);
        batchConfirmBtn.setVisibility(View.GONE);
        batchConfirmBtn.setText(fa ? "کلون کردن برنامه‌های انتخابی" : "Clone Selected Apps");
        LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        blp.setMargins(36, 12, 36, 28);
        batchConfirmBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                for (InstalledApp app : allApps) {
                    if (batchSelected.contains(app.pkg)) {
                        cloneSingleApp(app);
                    }
                }
                finish();
            }
        });
        root.addView(batchConfirmBtn, blp);

        setContentView(root);
        loadInstalledApps();
        renderGrid("");

        searchEt.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                currentQuery = s.toString();
                renderGrid(currentQuery);
            }
            @Override public void afterTextChanged(Editable s) {}
        });
    }

    private void loadInstalledApps() {
        allApps.clear();
        PackageManager pm = getPackageManager();
        Intent main = new Intent(Intent.ACTION_MAIN, null);
        main.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> list = pm.queryIntentActivities(main, 0);
        Set<String> seen = new HashSet<String>();
        for (ResolveInfo ri : list) {
            String pkg = ri.activityInfo.packageName;
            if (pkg.equals(getPackageName()) || seen.contains(pkg)) continue;
            seen.add(pkg);
            InstalledApp app = new InstalledApp();
            app.pkg = pkg;
            app.label = String.valueOf(ri.loadLabel(pm));
            app.icon = ri.loadIcon(pm);
            allApps.add(app);
        }
        Collections.sort(allApps, new Comparator<InstalledApp>() {
            @Override
            public int compare(InstalledApp a, InstalledApp b) {
                return a.label.compareToIgnoreCase(b.label);
            }
        });
    }

    private void renderGrid(final String query) {
        grid.removeAllViews();
        String q = query.trim().toLowerCase();
        int cellW = (getResources().getDisplayMetrics().widthPixels - 96) / 4;
        for (final InstalledApp app : allApps) {
            if (!q.isEmpty() && !app.label.toLowerCase().contains(q) && !app.pkg.toLowerCase().contains(q)) {
                continue;
            }
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setGravity(Gravity.CENTER);
            card.setBackgroundResource(R.drawable.bg_card_rounded);
            card.setPadding(16, 28, 16, 28);
            GridLayout.LayoutParams glp = new GridLayout.LayoutParams();
            glp.width = cellW - 16;
            glp.setMargins(8, 8, 8, 8);
            card.setLayoutParams(glp);

            if (batchMode && batchSelected.contains(app.pkg)) {
                card.getBackground().setTint(Color.parseColor("#DBEAFE"));
            } else {
                card.getBackground().setTint(Color.WHITE);
            }

            ImageView iv = new ImageView(this);
            iv.setImageDrawable(app.icon);
            card.addView(iv, new LinearLayout.LayoutParams(116, 116));

            TextView tv = new TextView(this);
            tv.setText(app.label);
            tv.setTextSize(12f);
            tv.setTextColor(Color.parseColor("#1F2937"));
            tv.setSingleLine(true);
            tv.setEllipsize(TextUtils.TruncateAt.END);
            tv.setGravity(Gravity.CENTER);
            tv.setPadding(0, 14, 0, 0);
            card.addView(tv);

            card.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    if (batchMode) {
                        if (batchSelected.contains(app.pkg)) batchSelected.remove(app.pkg);
                        else batchSelected.add(app.pkg);
                        batchConfirmBtn.setText((fa ? "کلون کردن (" : "Clone (") + batchSelected.size() + ")");
                        renderGrid(query);
                    } else {
                        cloneSingleApp(app);
                        finish();
                    }
                }
            });
            grid.addView(card);
        }
    }

    private void cloneSingleApp(InstalledApp app) {
        int nextUid = CloneStore.nextFreeUserIdForPackage(this, app.pkg);
        CloneStore.CloneEntry e = new CloneStore.CloneEntry();
        e.packageName = app.pkg;
        e.userId = nextUid;
        e.displayName = app.label;
        Engine.installPackageAsUser(e.packageName, e.userId);
        CloneStore.upsertClone(this, e);
        Toast.makeText(this,
                fa ? (app.label + " به فضای " + e.getSpaceNumber() + " اضافه شد")
                   : (app.label + " cloned into Space " + e.getSpaceNumber()),
                Toast.LENGTH_SHORT).show();
    }
}
