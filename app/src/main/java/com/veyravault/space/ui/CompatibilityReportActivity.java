package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.veyravault.space.core.CompatibilityManager;
import com.veyravault.space.core.LocaleHelper;

public class CompatibilityReportActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        boolean fa = LocaleHelper.isPersian(this);
        int ink = UiPalette.textPrimary(getApplicationContext());
        int muted = UiPalette.textSecondary(getApplicationContext());
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(48, 40, 48, 40);

        TextView title = new TextView(this);
        title.setText(fa ? "گزارش سازگاری" : "Compatibility report");
        title.setTextSize(22);
        title.setTypeface(Typeface.DEFAULT_BOLD);
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

        for (CompatibilityManager.CheckItem item : CompatibilityManager.collect(this)) {
            TextView row = new TextView(this);
            String status = item.status.name();
            row.setText(item.key.toUpperCase() + "  •  " + status + "\n" + item.detail);
            row.setTextSize(14);
            row.setTextColor(ink);
            row.setPadding(24, 20, 24, 20);
            row.setBackgroundColor(UiPalette.surfaceSecondary(getApplicationContext()));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = 16;
            root.addView(row, lp);
        }

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
    }
}
