package com.veyravault.space.ui;

import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.veyravault.space.core.CompatibilityManager;
import com.veyravault.space.core.EngineOperationQueue;
import com.veyravault.space.core.LocaleHelper;

public class CompatibilityReportActivity extends BaseActivity {
    private LinearLayout diagnosticsRows;
    private boolean fa;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        fa = LocaleHelper.isPersian(this);
        int ink = UiPalette.textPrimary(getApplicationContext());
        int muted = UiPalette.textSecondary(getApplicationContext());
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(48, 40, 48, 40);

        TextView title = new TextView(this);
        title.setText(fa ? "گزارش سازگاری" : "Compatibility report");
        title.setTextSize(22);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        title.setTextColor(ink);
        root.addView(title);

        TextView intro = new TextView(this);
        intro.setText(fa
                ? "این بررسی فقط اطلاعات تشخیصیِ قابل مشاهده برای برنامه را می‌خواند و هیچ تنظیم، مجوز، شبکه یا دادهٔ کلونی را تغییر نمی‌دهد."
                : "Read-only diagnostics visible to the host app. No settings, permissions, network routes, or clone data are changed.");
        intro.setTextSize(14);
        intro.setTextColor(muted);
        intro.setPadding(0, 16, 0, 24);
        root.addView(intro);

        diagnosticsRows = new LinearLayout(this);
        diagnosticsRows.setOrientation(LinearLayout.VERTICAL);
        TextView loading = new TextView(this);
        loading.setText(fa ? "در حال بررسی وضعیت سازگاری..." : "Checking compatibility status...");
        loading.setTextSize(14);
        loading.setTextColor(ink);
        diagnosticsRows.addView(loading);
        root.addView(diagnosticsRows);

        Button cloneDiagnostics = new Button(this);
        cloneDiagnostics.setAllCaps(false);
        cloneDiagnostics.setText(fa ? "عیب‌یابی اختصاصی Cloneها" : "Per-Clone App Diagnostics");
        cloneDiagnostics.setOnClickListener(v ->
                startActivity(new android.content.Intent(
                        CompatibilityReportActivity.this, AppCompatibilityDiagnosticsActivity.class)));
        root.addView(cloneDiagnostics);

        TextView footer = new TextView(this);
        footer.setText(fa
                ? "محدودیت: این گزارش سازگاری برنامه‌های مجازی‌شده یا موفقیت نشست‌ها را تضمین نمی‌کند. خطاهای اختصاصی هر برنامه باید جداگانه بررسی شوند."
                : "Limit: this report does not certify compatibility of virtualized apps or session behavior. App-specific failures require separate diagnosis.");
        footer.setTextSize(13);
        footer.setTextColor(muted);
        footer.setPadding(0, 8, 0, 8);
        root.addView(footer);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(root);
        setContentView(scroll);
        loadCompatibilitySnapshot(ink);
    }

    private void loadCompatibilitySnapshot(final int ink) {
        EngineOperationQueue.submit(
                () -> CompatibilityManager.collect(getApplicationContext()),
                (items, failure) -> {
                    if (isFinishing() || isDestroyed() || diagnosticsRows == null) return;
                    diagnosticsRows.removeAllViews();
                    if (failure != null || items == null) {
                        TextView error = new TextView(this);
                        error.setText(fa
                                ? "خواندن وضعیت سازگاری ناموفق بود؛ هیچ تغییری اعمال نشد."
                                : "Compatibility diagnostics could not be read; no changes were made.");
                        error.setTextSize(14);
                        error.setTextColor(ink);
                        diagnosticsRows.addView(error);
                        return;
                    }
                    for (CompatibilityManager.CheckItem item : items) {
                        TextView row = new TextView(this);
                        String status = item.status.name();
                        row.setText(item.key.toUpperCase(java.util.Locale.ROOT)
                                + "  •  " + status + "\n" + item.detail);
                        row.setTextSize(14);
                        row.setTextColor(ink);
                        row.setPadding(24, 20, 24, 20);
                        row.setBackgroundColor(UiPalette.surfaceSecondary(getApplicationContext()));
                        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
                        lp.bottomMargin = 16;
                        diagnosticsRows.addView(row, lp);
                    }
                });
    }
}
