package com.veyravault.space.ui;

import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.veyravault.space.core.AsyncCloneRepository;
import com.veyravault.space.core.CloneIdentityAudit;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.LocaleHelper;

import java.util.List;

/**
 * Read-only report of numeric virtual user IDs shared by different package Clones
 * in the current validated Clone registry. It never reads Engine account state.
 */
public final class CloneIdentityDiagnosticsActivity extends BaseActivity {
    private AsyncCloneRepository repository;
    private LinearLayout rows;
    private TextView status;
    private boolean fa;
    private int refreshGeneration;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        fa = LocaleHelper.isPersian(this);
        repository = AsyncCloneRepository.getInstance(getApplicationContext());
        buildUi();
        refreshAudit();
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(24), dp(20), dp(40));
        root.setBackgroundColor(UiPalette.page(this));
        scroll.addView(root);

        TextView title = new TextView(this);
        title.setText(fa ? "گزارش هم‌پوشانی شناسه Clone" : "Clone Identity Overlap Audit");
        title.setTextSize(22f);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        root.addView(title);

        TextView intro = new TextView(this);
        intro.setText(fa
                ? "این گزارش فقط رجیستری Cloneها و فهرست شناسه‌های کاربر مجازی موتور را می‌خواند. هم‌پوشانی بسته‌ها و شناسه‌های بدون رکورد متناظر را نشان می‌دهد؛ هیچ حساب، رمز، Token، Cookie، فایل خصوصی یا نشست خوانده نمی‌شود و هیچ شناسه یا داده‌ای تغییر نمی‌کند."
                : "This report reads the current Clone registry and the Engine virtual-user ID list only. It lists cross-package numeric overlaps and unmatched Engine IDs. It does not read accounts, passwords, tokens, cookies, private files or sessions, and never changes an ID or stored record.");
        intro.setTextSize(13f);
        intro.setTextColor(UiPalette.textSecondary(this));
        intro.setPadding(0, dp(10), 0, dp(14));
        root.addView(intro);

        TextView limitation = new TextView(this);
        limitation.setText(fa
                ? "محدودیت: این گزارش فقط Cloneهای ثبت‌شدهٔ فعلی را می‌بیند؛ شناسه‌های استفاده‌شده در گذشته یا حساب‌های باقی‌مانده در موتور از این رجیستری قابل مشاهده نیستند. هم‌پوشانی، نشانهٔ اشتراک محدودهٔ کاربر مجازی است، نه اثبات دسترسی قطعی همه برنامه‌ها به همه حساب‌ها."
                : "Limit: this report sees only currently registered Clones. Historical IDs and account records retained inside the Engine are not visible here. An overlap indicates a shared virtual-user scope; it does not prove every app can see every account.");
        limitation.setTextSize(12f);
        limitation.setTextColor(UiPalette.warning(this));
        limitation.setPadding(dp(12), dp(12), dp(12), dp(12));
        limitation.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        root.addView(limitation);

        status = new TextView(this);
        status.setTextSize(13f);
        status.setTextColor(UiPalette.textSecondary(this));
        status.setPadding(0, dp(16), 0, dp(12));
        root.addView(status);

        Button refresh = new Button(this);
        refresh.setAllCaps(false);
        refresh.setText(fa ? "بررسی دوباره رجیستری و موتور" : "Refresh registry and Engine audit");
        refresh.setOnClickListener(v -> refreshAudit());
        root.addView(refresh);

        rows = new LinearLayout(this);
        rows.setOrientation(LinearLayout.VERTICAL);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(16);
        root.addView(rows, params);

        setContentView(scroll);
    }

    private void refreshAudit() {
        final int generation = ++refreshGeneration;
        status.setText(fa ? "در حال خواندن رجیستری Cloneها..." :
                "Reading the Clone registry...");
        rows.removeAllViews();

        repository.loadClones(result -> {
            if (!isCurrent(generation)) return;
            if (!result.isSuccess() || result.getValue() == null) {
                status.setText((fa ? "گزارش در دسترس نیست؛ رجیستری قابل تأیید نبود: " :
                        "Audit unavailable; the Clone registry could not be validated: ")
                        + result.getMessage());
                return;
            }

            final List<CloneStore.CloneEntry> snapshot = result.getValue();
            status.setText(fa
                    ? "در حال خواندن فهرست شناسه‌های کاربر مجازی موتور؛ فقط شناسه‌ها..."
                    : "Reading Engine virtual-user IDs only; no account data...");
            try {
                EngineOperationQueue.submit(
                        () -> Engine.getKnownVirtualUserIds(),
                        (engineIds, failure) -> {
                            if (!isCurrent(generation)) return;
                            if (failure != null || engineIds == null) {
                                renderRegistryOnly(snapshot, failure);
                                return;
                            }
                            try {
                                CloneIdentityAudit.InventoryReport report =
                                        CloneIdentityAudit.auditInventory(snapshot, engineIds);
                                renderInventoryReport(snapshot.size(), report);
                            } catch (RuntimeException invalid) {
                                status.setText(fa
                                        ? "گزارش متوقف شد؛ فهرست شناسه‌های موتور یا رجیستری معتبر نیست."
                                        : "Audit stopped because the Engine inventory or Clone registry is invalid.");
                            }
                        });
            } catch (RuntimeException rejected) {
                renderRegistryOnly(snapshot, rejected);
            }
        });
    }

    private void renderRegistryOnly(List<CloneStore.CloneEntry> snapshot, Throwable failure) {
        final List<CloneIdentityAudit.CollisionGroup> collisions;
        try {
            collisions = CloneIdentityAudit.findCrossPackageCollisions(snapshot);
        } catch (RuntimeException invalid) {
            status.setText(fa
                    ? "گزارش متوقف شد؛ ساختار هویت‌های رجیستری معتبر نیست."
                    : "Audit stopped because the registry identity structure is invalid.");
            return;
        }
        status.setText(fa
                ? "فهرست Cloneها خوانده شد، اما فهرست شناسه‌های موتور تأیید نشد. نبود هم‌پوشانی قابل اعلام نیست."
                : "Clone registry read, but the Engine user inventory could not be confirmed. No all-clear result is reported.");
        if (failure != null) {
            TextView reason = new TextView(this);
            reason.setText((fa ? "علت: " : "Reason: ") + failure.getClass().getSimpleName());
            reason.setTextSize(11f);
            reason.setTextColor(UiPalette.textSecondary(this));
            rows.addView(reason);
        }
        for (CloneIdentityAudit.CollisionGroup group : collisions) addCollisionRow(group);
    }

    private void renderInventoryReport(int cloneCount,
                                       CloneIdentityAudit.InventoryReport report) {
        status.setText((fa ? "Cloneهای ثبت‌شده: " : "Registered Clones: ")
                + cloneCount
                + (fa ? "\nشناسه‌های ثبت‌شده در موتور: " : "\nEngine virtual user IDs: ")
                + report.knownEngineUserIds.size()
                + (fa ? "\nگروه‌های هم‌پوشانی بین بسته‌ها: " : "\nCross-package overlap groups: ")
                + report.crossPackageCollisions.size());

        for (CloneIdentityAudit.CollisionGroup group : report.crossPackageCollisions) {
            addCollisionRow(group);
        }

        addUserIdListRow(
                fa ? "شناسه‌های موتور بدون رکورد Clone فعلی" : "Engine IDs without a current Clone record",
                report.engineUserIdsWithoutRegisteredClone,
                fa
                        ? "این شناسه‌ها در موتور هنوز ثبت هستند، اما در رجیستری فعلی Clone متناظر ندارند. آن‌ها را شناسه آزاد فرض نکنید؛ ممکن است وضعیت یا داده قدیمی موتور باقی مانده باشد."
                        : "These IDs still exist in the Engine but have no matching current Clone registry row. Do not treat them as free; old Engine state or account data may remain.");

        addUserIdListRow(
                fa ? "شناسه‌های Clone که در فهرست فعلی موتور نیستند" : "Clone IDs missing from the current Engine inventory",
                report.registeredCloneUserIdsMissingFromEngine,
                fa
                        ? "رجیستری به این شناسه‌ها اشاره می‌کند، اما موتور آن‌ها را در فهرست فعلی نشان نمی‌دهد. هیچ نصب، ترمیم یا حذف خودکاری انجام نشده است."
                        : "The Clone registry references these IDs, but the Engine does not list them now. No install, repair or removal was attempted.");

        if (report.crossPackageCollisions.isEmpty()
                && report.engineUserIdsWithoutRegisteredClone.isEmpty()
                && report.registeredCloneUserIdsMissingFromEngine.isEmpty()) {
            TextView note = new TextView(this);
            note.setText(fa
                    ? "در رجیستری و فهرست فعلی شناسه‌های موتور، ناسازگاری عددی پیدا نشد. این نتیجه پاک‌بودن حساب‌های حذف‌شده در گذشته یا جداسازی کامل نشست‌ها را ثابت نمی‌کند."
                    : "No numeric mismatch was found between the current Clone registry and Engine user list. This does not prove historical deleted-user account buckets are empty or certify full session isolation.");
            note.setTextSize(12f);
            note.setTextColor(UiPalette.textSecondary(this));
            note.setPadding(0, dp(12), 0, 0);
            rows.addView(note);
        }
    }

    private void addUserIdListRow(String headingText, List<Integer> ids, String detailText) {
        if (ids == null || ids.isEmpty()) return;
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.bottomMargin = dp(12);
        rows.addView(card, params);

        TextView heading = new TextView(this);
        heading.setText(headingText + " (" + ids.size() + ")");
        heading.setTextSize(14f);
        heading.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        heading.setTextColor(UiPalette.warning(this));
        card.addView(heading);

        TextView values = new TextView(this);
        StringBuilder joined = new StringBuilder();
        for (Integer id : ids) {
            if (joined.length() > 0) joined.append(", ");
            joined.append(id);
        }
        values.setText(joined.toString());
        values.setTextSize(13f);
        values.setTextColor(UiPalette.textPrimary(this));
        values.setPadding(0, dp(8), 0, 0);
        card.addView(values);

        TextView detail = new TextView(this);
        detail.setText(detailText);
        detail.setTextSize(11f);
        detail.setTextColor(UiPalette.textSecondary(this));
        detail.setPadding(0, dp(8), 0, 0);
        card.addView(detail);
    }

    private void addCollisionRow(CloneIdentityAudit.CollisionGroup group) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.bottomMargin = dp(12);
        rows.addView(card, params);

        TextView heading = new TextView(this);
        heading.setText((fa ? "شناسه کاربر مجازی: " : "Virtual user ID: ") + group.userId);
        heading.setTextSize(15f);
        heading.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        heading.setTextColor(UiPalette.warning(this));
        card.addView(heading);

        TextView identities = new TextView(this);
        StringBuilder text = new StringBuilder();
        for (CloneIdentityAudit.CloneIdentity clone : group.clones) {
            if (text.length() > 0) text.append("\n\n");
            text.append(clone.displayName)
                    .append("\n")
                    .append(clone.packageName);
        }
        identities.setText(text.toString());
        identities.setTextSize(12f);
        identities.setTextColor(UiPalette.textPrimary(this));
        identities.setPadding(0, dp(10), 0, 0);
        card.addView(identities);

        TextView detail = new TextView(this);
        detail.setText(fa
                ? "این بسته‌ها در محدوده userId یکسان موتور قرار می‌گیرند. هیچ اصلاح یا پاکسازی خودکاری انجام نشده است."
                : "These packages resolve to the same Engine virtual-user scope. No automatic repair or cleanup was performed.");
        detail.setTextSize(11f);
        detail.setTextColor(UiPalette.textSecondary(this));
        detail.setPadding(0, dp(10), 0, 0);
        card.addView(detail);
    }

    private boolean isCurrent(int generation) {
        return generation == refreshGeneration && !isFinishing() && !isDestroyed();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
