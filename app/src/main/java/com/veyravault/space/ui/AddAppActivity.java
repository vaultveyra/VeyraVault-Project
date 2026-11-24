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
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.AsyncCloneProvisionRepository;
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
    private AsyncCloneProvisionRepository provisionRepository;
    private boolean cloneOperationRunning;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        fa = LocaleHelper.isPersian(this);
        provisionRepository = AsyncCloneProvisionRepository.getInstance(getApplicationContext());

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(UiPalette.page(getApplicationContext()));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(20), dp(22), dp(20), dp(12));

        final TextView batchBtn = new TextView(this);
        batchBtn.setText(getString(R.string.batch_clone));
        batchBtn.setTextColor(UiPalette.accent(getApplicationContext()));
        batchBtn.setBackgroundResource(R.drawable.bg_pill_lightblue);
        batchBtn.setPadding(dp(16), dp(9), dp(16), dp(9));
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
        title.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        title.setGravity(Gravity.CENTER);
        header.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView backBtn = new TextView(this);
        backBtn.setText("→");
        backBtn.setTextSize(24f);
        backBtn.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        backBtn.setPadding(dp(12), 0, dp(12), 0);
        backBtn.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { finish(); }
        });
        header.addView(backBtn);
        root.addView(header);

        EditText searchEt = new EditText(this);
        searchEt.setHint("🔍  " + getString(R.string.search_apps));
        searchEt.setBackgroundResource(R.drawable.bg_card_rounded);
        searchEt.setSingleLine(true);
        searchEt.setTextSize(14f);
        searchEt.setPadding(dp(18), dp(13), dp(18), dp(13));
        LinearLayout.LayoutParams slp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        slp.setMargins(dp(20), dp(8), dp(20), dp(16));
        root.addView(searchEt, slp);

        ScrollView sv = new ScrollView(this);
        grid = new GridLayout(this);
        grid.setColumnCount(3);
        grid.setPadding(dp(14), dp(8), dp(14), dp(24));
        sv.addView(grid);
        root.addView(sv, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        batchConfirmBtn = new Button(this);
        batchConfirmBtn.setBackgroundResource(R.drawable.bg_pill_blue);
        batchConfirmBtn.setTextColor(Color.WHITE);
        batchConfirmBtn.setVisibility(View.GONE);
        batchConfirmBtn.setText(fa ? "کلون کردن برنامه‌های انتخابی" : "Clone Selected Apps");
        LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        blp.setMargins(dp(20), dp(10), dp(20), dp(20));
        batchConfirmBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (cloneOperationRunning || batchSelected.isEmpty()) return;
                List<InstalledApp> selected = new ArrayList<InstalledApp>();
                for (InstalledApp app : allApps) {
                    if (batchSelected.contains(app.pkg)) selected.add(app);
                }
                cloneOperationRunning = true;
                batchConfirmBtn.setEnabled(false);
                cloneBatchAt(selected, 0, 0, 0);
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

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
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
        int cellW = (getResources().getDisplayMetrics().widthPixels - dp(48)) / 3;
        for (final InstalledApp app : allApps) {
            if (!q.isEmpty() && !app.label.toLowerCase().contains(q) && !app.pkg.toLowerCase().contains(q)) {
                continue;
            }
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setGravity(Gravity.CENTER);
            card.setBackgroundResource(R.drawable.bg_card_rounded);
            card.setPadding(dp(12), dp(16), dp(12), dp(16));
            GridLayout.LayoutParams glp = new GridLayout.LayoutParams();
            glp.width = cellW - dp(12);
            glp.setMargins(dp(6), dp(6), dp(6), dp(6));
            card.setLayoutParams(glp);

            if (batchMode && batchSelected.contains(app.pkg)) {
                card.getBackground().setTint(UiPalette.accentSurface(getApplicationContext()));
            } else {
                card.getBackground().setTint(UiPalette.surface(getApplicationContext()));
            }

            ImageView iv = new ImageView(this);
            iv.setImageDrawable(app.icon);
            card.addView(iv, new LinearLayout.LayoutParams(dp(54), dp(54)));

            TextView tv = new TextView(this);
            tv.setText(app.label);
            tv.setTextSize(12f);
            tv.setTextColor(UiPalette.textPrimary(getApplicationContext()));
            tv.setSingleLine(true);
            tv.setEllipsize(TextUtils.TruncateAt.END);
            tv.setGravity(Gravity.CENTER);
            tv.setPadding(0, dp(10), 0, 0);
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
                        if (!cloneOperationRunning) {
                            cloneOperationRunning = true;
                            cloneSingleApp(app, new CloneCallback() {
                                @Override public void onComplete(boolean saved) {
                                    cloneOperationRunning = false;
                                    if (saved && !isFinishing() && !isDestroyed()) finish();
                                }
                            });
                        }
                    }
                }
            });
            grid.addView(card);
        }
    }

    private interface CloneCallback {
        void onComplete(boolean saved);
    }

    private void cloneBatchAt(final List<InstalledApp> selected, final int index,
                              final int savedCount, final int failedCount) {
        if (isFinishing() || isDestroyed()) return;
        if (index >= selected.size()) {
            cloneOperationRunning = false;
            if (batchConfirmBtn != null) batchConfirmBtn.setEnabled(true);
            Toast.makeText(this,
                    fa ? ("پایان عملیات: " + savedCount + " موفق، " + failedCount + " ناموفق")
                       : ("Batch complete: " + savedCount + " succeeded, " + failedCount + " failed"),
                    Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        cloneSingleApp(selected.get(index), new CloneCallback() {
            @Override public void onComplete(boolean saved) {
                if (isFinishing() || isDestroyed()) return;
                cloneBatchAt(selected, index + 1, savedCount + (saved ? 1 : 0),
                        failedCount + (saved ? 0 : 1));
            }
        });
    }

    private void cloneSingleApp(final InstalledApp app, final CloneCallback callback) {
        if (app == null || app.pkg == null || app.pkg.trim().isEmpty()) {
            showCloneError(fa ? "برنامهٔ انتخاب‌شده معتبر نیست." : "The selected app is invalid.");
            callback.onComplete(false);
            return;
        }
        // The app-scoped coordinator owns install/commit/rollback beyond Activity lifetime.
        provisionRepository.createClone(app.pkg, app.label, fa, outcome -> {
            if (outcome == null || !outcome.success) {
                showCloneError(outcome == null
                        ? (fa ? "نتیجهٔ نصب مشخص نشد؛ رزروهای معلق را بررسی کنید."
                              : "The install result is unknown; inspect pending reservations.")
                        : outcome.message);
                callback.onComplete(false);
                return;
            }
            if (!batchMode && !isFinishing() && !isDestroyed()) {
                Toast.makeText(AddAppActivity.this,
                        fa ? (app.label + " به فضای " + outcome.clone.getSpaceNumber() + " اضافه شد")
                           : (app.label + " cloned into Space " + outcome.clone.getSpaceNumber()),
                        Toast.LENGTH_SHORT).show();
            }
            callback.onComplete(true);
        });
    }

    private void showCloneError(String message) {
        if (isFinishing() || isDestroyed()) return;
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
}
