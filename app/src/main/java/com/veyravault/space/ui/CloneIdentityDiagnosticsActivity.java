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
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.EngineOperationQueue;
import com.veyravault.space.core.LocaleHelper;

import java.util.List;

/**
 * Read-only comparison of the current Clone registry with Engine virtual-user IDs.
 * It never reads Engine AccountManager or app-session state.
 */
public final class CloneIdentityDiagnosticsActivity extends BaseActivity {
    private AsyncCloneRepository repository;
    private LinearLayout rows;
    private TextView status;
    private boolean fa;
    private int refreshGeneration;

    private static final class EngineInventorySnapshot {
        final List<Integer> engineUserIds;
        final List<Integer> accountManagerUserIds;
        final Throwable engineFailure;
        final Throwable accountManagerFailure;

        EngineInventorySnapshot(List<Integer> engineIds, List<Integer> accountIds,
                                Throwable engineError, Throwable accountError) {
            this.engineUserIds = engineIds;
            this.accountManagerUserIds = accountIds;
            this.engineFailure = engineError;
            this.accountManagerFailure = accountError;
        }
    }

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
                ? "این گزارش فقط رجیستری Cloneها و دو فهرست عددی Engine را می‌خواند: شناسه کاربران مجازی و کلیدهای عددی AccountManager. هیچ نام حساب، رمز، userData، Token، Cookie، فایل خصوصی یا محتوای نشست خوانده نمی‌شود و هیچ شناسه یا داده‌ای تغییر نمی‌کند."
                : "This report reads the Clone registry and two numeric-only Engine inventories: virtual-user IDs and AccountManager bucket keys. It never reads account names, passwords, userData, tokens, cookies, private files or session content, and never changes an ID or stored record.");
        intro.setTextSize(13f);
        intro.setTextColor(UiPalette.textSecondary(this));
        intro.setPadding(0, dp(10), 0, dp(14));
        root.addView(intro);

        TextView limitation = new TextView(this);
        limitation.setText(fa
                ? "محدودیت مهم: کلید AccountManager فقط userId عددی است، نه شناسه ترکیبی بسته و کاربر. اگر چند بسته Clone یک userId مشترک داشته باشند، در سطح عددی به یک bucket اشاره می‌کنند؛ این گزارش bucket را به هیچ بسته‌ای نسبت نمی‌دهد و دسترسی قطعی به حساب‌ها یا Tokenها را اثبات نمی‌کند. کلیدهای باقی‌مانده پس از حذف کاربر قدیمی ممکن است دیگر در فهرست Engine دیده نشوند. این گزارش ثابت نمی‌کند bucketهای حسابِ کاربران حذف‌شده تاریخی خالی‌اند. شناسه غایب را آزاد فرض نکنید."
                : "Important limit: AccountManager keys use a numeric userId, not a package-and-user composite identity. Different Clone packages sharing one userId point at the same numeric bucket scope; this report never attributes that bucket to a package and does not prove account or token visibility. Keys left after an older user deletion may no longer appear in the Engine list. This does not prove historical deleted-user account buckets are empty. Missing IDs must not be assumed safe to reuse.");
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
                        () -> readEngineInventories(),
                        (inventories, failure) -> {
                            if (!isCurrent(generation)) return;
                            if (failure != null || inventories == null) {
                                renderRegistryOnly(snapshot, failure);
                                return;
                            }
                            if (inventories.engineFailure != null
                                    || inventories.accountManagerFailure != null
                                    || inventories.engineUserIds == null
                                    || inventories.accountManagerUserIds == null) {
                                renderPartialInventory(snapshot, inventories);
                                return;
                            }
                            try {
                                CloneIdentityAudit.InventoryReport report =
                                        CloneIdentityAudit.auditInventory(
                                                snapshot,
                                                inventories.engineUserIds,
                                                inventories.accountManagerUserIds);
                                renderInventoryReport(snapshot.size(), report);
                            } catch (RuntimeException invalid) {
                                status.setText(fa
                                        ? "گزارش متوقف شد؛ یکی از فهرست‌های عددی یا رجیستری معتبر نیست."
                                        : "Audit stopped because a numeric inventory or the Clone registry is invalid.");
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
                ? "فهرست Cloneها خوانده شد، اما فهرست شناسه‌های Engine و/یا AccountManager تأیید نشد. گزارش ناقص است و نتیجه بدون هم‌پوشانی قابل اعلام نیست."
                : "Clone registry read, but the Engine and/or AccountManager numeric inventory could not be confirmed. The report is incomplete; no all-clear result is reported.");
        if (failure != null) {
            TextView reason = new TextView(this);
            reason.setText((fa ? "علت: " : "Reason: ") + failure.getClass().getSimpleName());
            reason.setTextSize(11f);
            reason.setTextColor(UiPalette.textSecondary(this));
            rows.addView(reason);
        }
        for (CloneIdentityAudit.CollisionGroup group : collisions) addCollisionRow(group);
    }

    private EngineInventorySnapshot readEngineInventories() {
        List<Integer> engineIds = null;
        List<Integer> accountIds = null;
        Throwable engineError = null;
        Throwable accountError = null;
        try {
            engineIds = Engine.getKnownVirtualUserIds();
        } catch (Exception failure) {
            engineError = failure;
        }
        try {
            accountIds = Engine.getKnownAccountUserIds();
        } catch (Exception failure) {
            accountError = failure;
        }
        return new EngineInventorySnapshot(engineIds, accountIds, engineError, accountError);
    }

    private void renderPartialInventory(List<CloneStore.CloneEntry> snapshot,
                                        EngineInventorySnapshot inventories) {
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
                ? "گزارش ناقص است: دست‌کم یکی از دو فهرست Engine یا AccountManager تأیید نشد. هیچ نتیجه سالم یا بدون هم‌پوشانی اعلام نمی‌شود."
                : "Incomplete report: at least one Engine inventory could not be confirmed. No clean or all-clear result is reported.");

        for (CloneIdentityAudit.CollisionGroup group : collisions) addCollisionRow(group);

        if (inventories.engineUserIds != null) {
            addUserIdListRow(
                    fa ? "شناسه‌های کاربر مجازی تأییدشده Engine" : "Verified Engine virtual-user IDs",
                    inventories.engineUserIds,
                    fa ? "این فهرست به‌تنهایی محتوای حساب‌ها یا وضعیت داده‌های قدیمی را نشان نمی‌دهد."
                            : "This list alone does not show account contents or historical data state.");
        } else {
            addInventoryFailure(fa ? "فهرست کاربران مجازی Engine تأیید نشد" :
                    "Engine virtual-user inventory unavailable", inventories.engineFailure);
        }

        if (inventories.accountManagerUserIds != null) {
            addUserIdListRow(
                    fa ? "کلیدهای عددی AccountManager (فقط شناسه)" : "AccountManager numeric bucket keys (IDs only)",
                    inventories.accountManagerUserIds,
                    fa ? "این کلیدها به بسته مشخصی نسبت داده نمی‌شوند؛ تا تکمیل هر سه فهرست، هیچ شناسه‌ای آزاد فرض نشود."
                            : "These keys are not attributed to a package. Do not treat any ID as free while the three inventories are incomplete.");
        } else {
            addInventoryFailure(fa ? "فهرست عددی AccountManager تأیید نشد" :
                    "AccountManager numeric inventory unavailable", inventories.accountManagerFailure);
        }
    }

    private void addInventoryFailure(String label, Throwable failure) {
        TextView reason = new TextView(this);
        reason.setText(label + (failure == null ? "" :
                (fa ? "؛ علت: " : "; reason: ") + failure.getClass().getSimpleName()));
        reason.setTextSize(12f);
        reason.setTextColor(UiPalette.warning(this));
        reason.setPadding(0, dp(8), 0, dp(8));
        rows.addView(reason);
    }

    private void renderInventoryReport(int cloneCount,
                                       CloneIdentityAudit.InventoryReport report) {
        status.setText((fa ? "Cloneهای ثبت‌شده: " : "Registered Clones: ")
                + cloneCount
                + (fa ? "\nشناسه‌های کاربران مجازی Engine: " : "\nEngine virtual-user IDs: ")
                + report.knownEngineUserIds.size()
                + (fa ? "\nکلیدهای عددی AccountManager: " : "\nAccountManager numeric bucket keys: ")
                + report.knownAccountManagerUserIds.size()
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

        addUserIdListRow(
                fa ? "کلیدهای AccountManager بدون کاربر مجازی فعلی" : "AccountManager IDs without a current Engine user",
                report.accountManagerUserIdsWithoutCurrentEngineUser,
                fa
                        ? "این شناسه‌ها در Map حساب‌ها وجود دارند اما در فهرست فعلی کاربران موتور نیستند؛ نامزد رکورد تاریخی‌اند، نه شناسه آزاد."
                        : "These IDs exist as account-map keys but not in the current Engine user list. They are historical-record candidates, not free IDs.");

        addUserIdListRow(
                fa ? "کلیدهای AccountManager بدون Clone ثبت‌شده" : "AccountManager IDs without a registered Clone",
                report.accountManagerUserIdsWithoutRegisteredClone,
                fa
                        ? "هیچ Clone فعلی با این userId عددی در رجیستری پیدا نشد. این نتیجه فقط عددی است و به package خاصی نسبت داده نمی‌شود."
                        : "No current Clone uses this numeric userId in the registry. This is a numeric comparison only and is not attributed to a package.");

        addUserIdListRow(
                fa ? "کلیدهای AccountManager در محدوده چند بسته Clone" : "AccountManager IDs in a cross-package Clone overlap",
                report.accountManagerUserIdsSharedAcrossPackages,
                fa
                        ? "چند بسته Clone همین userId عددی را دارند و AccountManager نیز بر اساس همین عدد کلیدگذاری شده است. این هم‌محدوده بودن، دسترسی قطعی به همه حساب‌ها را ثابت نمی‌کند."
                        : "Multiple Clone packages use this numeric userId and AccountManager is keyed by that number. This shared scope does not prove that every app can access every account.");

        TextView scopeNote = new TextView(this);
        scopeNote.setText(fa
                ? "این گزارش فقط شناسه‌های عددی را مقایسه می‌کند. هیچ کلید AccountManager به یک package یا Clone مشخص منتسب نمی‌شود و هیچ رمز، نام حساب، userData یا Token خوانده نمی‌شود."
                : "No AccountManager key is attributed to a package or specific Clone. This report compares numeric IDs only and does not read account names, passwords, userData or tokens.");
        scopeNote.setTextSize(11f);
        scopeNote.setTextColor(UiPalette.textSecondary(this));
        scopeNote.setPadding(0, dp(10), 0, dp(10));
        rows.addView(scopeNote);

        if (report.crossPackageCollisions.isEmpty()
                && report.engineUserIdsWithoutRegisteredClone.isEmpty()
                && report.registeredCloneUserIdsMissingFromEngine.isEmpty()
                && report.accountManagerUserIdsWithoutCurrentEngineUser.isEmpty()
                && report.accountManagerUserIdsWithoutRegisteredClone.isEmpty()
                && report.accountManagerUserIdsSharedAcrossPackages.isEmpty()) {
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
        int visibleCount = Math.min(ids.size(), 100);
        for (int i = 0; i < visibleCount; i++) {
            if (joined.length() > 0) joined.append(", ");
            joined.append(ids.get(i));
        }
        if (ids.size() > visibleCount) {
            joined.append(fa ? "، ... و " : ", ... plus ");
            joined.append(ids.size() - visibleCount);
            joined.append(fa ? " مورد دیگر" : " more");
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
