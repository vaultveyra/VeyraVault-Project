package com.veyravault.space.ui;

import android.content.Intent;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.veyravault.space.core.AsyncCloneRepository;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.CompatibilityManager;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.EngineOperationQueue;

import java.util.List;

/** Read-only per-Clone diagnostic snapshots with an explicit share action. */
public final class AppCompatibilityDiagnosticsActivity extends BaseActivity {
    private LinearLayout cloneList;
    private TextView reportView;
    private Button shareButton;
    private String currentReport;
    private boolean destroyed;
    private boolean fa;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        fa = LocaleHelper.isPersian(this);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(24), dp(20), dp(24));
        root.setBackgroundColor(UiPalette.page(this));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(android.view.Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText(fa ? "عیب‌یابی برنامه‌های Clone" : "Clone App Diagnostics");
        title.setTextSize(21f);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        header.addView(title, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        header.addView(createLanguageAction(fa));
        header.addView(createImmediateLockSwitch(fa));
        root.addView(header);

        TextView intro = new TextView(this);
        intro.setText(fa
                ? "یک Clone را انتخاب کنید تا گزارش فنیِ فقط‌خواندنی ساخته شود. این گزارش برنامه را اجرا نمی‌کند و داده‌های حساب، نشست یا فایل‌های خصوصی را نمی‌خواند."
                : "Select a Clone to create a read-only technical snapshot. This report does not launch the app or read account, session, or private app data.");
        intro.setTextSize(13f);
        intro.setTextColor(UiPalette.textSecondary(this));
        intro.setPadding(0, dp(10), 0, dp(14));
        root.addView(intro);

        cloneList = new LinearLayout(this);
        cloneList.setOrientation(LinearLayout.VERTICAL);
        root.addView(cloneList, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        reportView = new TextView(this);
        reportView.setText(fa ? "در حال خواندن فهرست Cloneها..." : "Reading the Clone registry...");
        reportView.setTextSize(12f);
        reportView.setTextColor(UiPalette.textPrimary(this));
        reportView.setPadding(dp(12), dp(12), dp(12), dp(12));
        reportView.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams reportParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        reportParams.topMargin = dp(14);
        root.addView(reportView, reportParams);

        shareButton = new Button(this);
        shareButton.setAllCaps(false);
        shareButton.setEnabled(false);
        shareButton.setText(fa ? "اشتراک‌گذاری گزارش" : "Share diagnostic report");
        shareButton.setOnClickListener(v -> shareCurrentReport());
        LinearLayout.LayoutParams shareParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        shareParams.topMargin = dp(10);
        root.addView(shareButton, shareParams);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(root);
        setContentView(scroll);
        loadClonesReadOnly();
    }

    private void loadClonesReadOnly() {
        AsyncCloneRepository.getInstance(getApplicationContext()).loadClones(result -> {
            if (destroyed || isFinishing() || isDestroyed()) return;
            cloneList.removeAllViews();
            if (result == null || !result.isSuccess() || result.getValue() == null) {
                reportView.setText(fa
                        ? "خواندن امن فهرست Cloneها ممکن نشد؛ هیچ تغییری اعمال نشد."
                        : "The Clone registry could not be read safely; no changes were made.");
                return;
            }
            List<CloneStore.CloneEntry> clones = result.getValue();
            if (clones.isEmpty()) {
                reportView.setText(fa ? "هنوز Cloneای برای بررسی ثبت نشده است."
                        : "No Clones are currently registered for diagnosis.");
                return;
            }
            for (CloneStore.CloneEntry clone : clones) {
                if (clone == null || clone.packageName == null || clone.packageName.trim().isEmpty()) continue;
                Button item = new Button(this);
                item.setAllCaps(false);
                String label = clone.displayName == null || clone.displayName.trim().isEmpty()
                        ? clone.packageName : clone.displayName;
                item.setText(label + "  •  " + (fa ? "فضای " : "Space ") + clone.getSpaceNumber());
                item.setOnClickListener(v -> createSnapshot(clone));
                LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
                params.bottomMargin = dp(6);
                cloneList.addView(item, params);
            }
        });
    }

    private void createSnapshot(CloneStore.CloneEntry clone) {
        currentReport = null;
        shareButton.setEnabled(false);
        reportView.setText(fa ? "در حال جمع‌آوری اطلاعات فقط‌خواندنی..." : "Collecting read-only diagnostics...");
        EngineOperationQueue.submit(
                () -> CompatibilityManager.formatCloneReport(getApplicationContext(), clone),
                (completedReport, failure) -> {
                    if (destroyed || isFinishing() || isDestroyed()) return;
                    String report = completedReport;
                    if (failure != null || report == null) {
                        report = "VeyraVault diagnostic generation failed: "
                                + (failure == null ? "UNKNOWN" : failure.getClass().getSimpleName())
                                + "\nNo Clone data or settings were changed.";
                    }
                    currentReport = report;
                    reportView.setText(report);
                    shareButton.setEnabled(!report.trim().isEmpty());
                });
    }

    private void shareCurrentReport() {
        if (currentReport == null || currentReport.trim().isEmpty()) return;
        Intent send = new Intent(Intent.ACTION_SEND);
        send.setType("text/plain");
        send.putExtra(Intent.EXTRA_TEXT, currentReport);
        startActivity(Intent.createChooser(send,
                fa ? "اشتراک‌گذاری گزارش فنی" : "Share technical diagnostic"));
    }

    @Override
    protected void onDestroy() {
        destroyed = true;
        super.onDestroy();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
