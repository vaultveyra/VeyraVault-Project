package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.AsyncCloneRepository;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.EngineOperationQueue;
import com.veyravault.space.core.LocaleHelper;

import java.util.ArrayList;
import java.util.List;

/**
 * Read-only diagnostics for durable pending Clone ID reservations.
 *
 * A reservation can only be released by an explicit user action followed by a fresh
 * Engine query that positively confirms the virtual package is absent. Installed or
 * unknown Engine states remain blocked; this screen never uninstalls packages or edits
 * clone records/session data.
 */
public class PendingReservationsActivity extends BaseActivity {
    private AsyncCloneRepository repository;
    private LinearLayout rows;
    private TextView status;
    private boolean fa;
    private int refreshGeneration;

    private static final class ReservationState {
        final CloneStore.CloneReservation reservation;
        final Engine.CloneInstallState engineState;

        ReservationState(CloneStore.CloneReservation reservation, Engine.CloneInstallState engineState) {
            this.reservation = reservation;
            this.engineState = engineState;
        }
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        fa = LocaleHelper.isPersian(this);
        repository = AsyncCloneRepository.getInstance(this);
        buildUi();
        refreshReservations();
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(40, 40, 40, 48);
        root.setBackgroundColor(UiPalette.page(getApplicationContext()));
        scroll.addView(root);

        TextView title = new TextView(this);
        title.setText(fa ? "بررسی رزروهای معلق شناسه" : "Pending Clone ID reservations");
        title.setTextSize(22f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        root.addView(title);

        TextView intro = new TextView(this);
        intro.setText(fa
                ? "این بخش فقط رزروهای باقی‌مانده را بررسی می‌کند. برنامه یا داده‌ای حذف نمی‌شود. آزادسازی فقط پس از تأیید دوبارهٔ نبودن بسته در موتور و تأیید شما انجام می‌شود."
                : "This screen inspects pending reservations only. It never uninstalls an app or changes clone/session data. A reservation can be released only after a fresh Engine check confirms the package is absent and you approve the action.");
        intro.setTextSize(14f);
        intro.setTextColor(UiPalette.textSecondary(getApplicationContext()));
        intro.setPadding(0, 16, 0, 20);
        root.addView(intro);

        status = new TextView(this);
        status.setTextSize(14f);
        status.setTextColor(UiPalette.textSecondary(getApplicationContext()));
        status.setPadding(0, 8, 0, 16);
        root.addView(status);

        Button refresh = new Button(this);
        refresh.setAllCaps(false);
        refresh.setText(fa ? "بررسی دوباره" : "Refresh status");
        refresh.setOnClickListener(v -> refreshReservations());
        root.addView(refresh);

        rows = new LinearLayout(this);
        rows.setOrientation(LinearLayout.VERTICAL);
        LinearLayout.LayoutParams rowsParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        rowsParams.topMargin = 16;
        root.addView(rows, rowsParams);

        setContentView(scroll);
    }

    private void refreshReservations() {
        final int generation = ++refreshGeneration;
        status.setText(fa ? "در حال خواندن رزروها..." : "Loading pending reservations...");
        rows.removeAllViews();

        repository.loadPendingReservations(result -> {
            if (!isCurrent(generation)) return;
            if (!result.isSuccess() || result.getValue() == null) {
                status.setText((fa ? "خواندن رزروها ناموفق بود: " : "Could not read reservations: ")
                        + result.getMessage());
                return;
            }

            final List<CloneStore.CloneReservation> pending =
                    new ArrayList<CloneStore.CloneReservation>(result.getValue());
            if (pending.isEmpty()) {
                status.setText(fa
                        ? "هیچ رزرو معلقی ثبت نشده است."
                        : "There are no pending Clone ID reservations.");
                return;
            }

            status.setText(fa
                    ? ("تعداد رزروهای معلق: " + pending.size() + " — در حال بررسی وضعیت موتور...")
                    : ("Pending reservations: " + pending.size() + " — checking Engine status..."));

            try {
                EngineOperationQueue.execute(() -> {
                    List<ReservationState> inspected = new ArrayList<ReservationState>();
                    for (CloneStore.CloneReservation reservation : pending) {
                        Engine.CloneInstallState engineState;
                        try {
                            engineState = Engine.getCloneInstallState(
                                    reservation.getPackageName(), reservation.getUserId());
                        } catch (Throwable error) {
                            engineState = Engine.CloneInstallState.UNKNOWN;
                        }
                        inspected.add(new ReservationState(reservation, engineState));
                    }
                    runOnUiThread(() -> {
                        if (!isCurrent(generation)) return;
                        status.setText(fa
                                ? ("رزروهای معلق: " + inspected.size() + " — وضعیت موتور فقط خوانده شده است.")
                                : ("Pending reservations: " + inspected.size() + " — Engine state was read only."));
                        rows.removeAllViews();
                        for (ReservationState item : inspected) addReservationRow(item);
                    });
                });
            } catch (RuntimeException rejected) {
                status.setText(fa
                        ? "امکان اجرای بررسی وضعیت موتور وجود ندارد."
                        : "Engine status inspection could not be started.");
            }
        });
    }

    private void addReservationRow(ReservationState item) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(28, 24, 28, 24);
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardParams.bottomMargin = 16;
        rows.addView(card, cardParams);

        TextView identity = new TextView(this);
        identity.setText(item.reservation.getPackageName()
                + "\n" + (fa ? "شناسهٔ کاربر مجازی: " : "Virtual user ID: ")
                + item.reservation.getUserId());
        identity.setTextSize(14f);
        identity.setTypeface(Typeface.DEFAULT_BOLD);
        identity.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        card.addView(identity);

        TextView detail = new TextView(this);
        detail.setTextSize(13f);
        detail.setPadding(0, 12, 0, 8);
        switch (item.engineState) {
            case ABSENT:
                detail.setText(fa
                        ? "موتور صریحاً تأیید می‌کند بسته نصب نیست. می‌توانید این رزرو را به‌صورت دستی آزاد کنید."
                        : "Engine explicitly confirms the package is absent. You may manually release this reservation.");
                detail.setTextColor(UiPalette.success(getApplicationContext()));
                break;
            case INSTALLED:
                detail.setText(fa
                        ? "بسته در موتور نصب است اما رکورد Clone متناظر وجود ندارد. رزرو حفظ می‌شود؛ حذف یا ثبت خودکار انجام نمی‌شود."
                        : "Engine reports the package installed but no matching Clone registry row exists. The reservation stays blocked; no uninstall or automatic registry repair is attempted.");
                detail.setTextColor(UiPalette.warning(getApplicationContext()));
                break;
            default:
                detail.setText(fa
                        ? "وضعیت موتور نامشخص است. برای جلوگیری از تداخل، رزرو آزاد نمی‌شود."
                        : "Engine state is unknown. The reservation remains blocked to prevent an ID collision.");
                detail.setTextColor(UiPalette.warning(getApplicationContext()));
                break;
        }
        card.addView(detail);

        if (item.engineState == Engine.CloneInstallState.ABSENT) {
            Button release = new Button(this);
            release.setAllCaps(false);
            release.setText(fa ? "آزادسازی دستی رزرو" : "Release reservation");
            release.setOnClickListener(v -> confirmAndRelease(item.reservation));
            card.addView(release);
        }
    }

    private void confirmAndRelease(CloneStore.CloneReservation reservation) {
        new AlertDialog.Builder(this)
                .setTitle(fa ? "آزادسازی رزرو شناسه؟" : "Release this ID reservation?")
                .setMessage(fa
                        ? "وضعیت موتور دوباره بررسی می‌شود. فقط اگر نبودن بسته تأیید شود، رزرو آزاد خواهد شد. این کار هیچ برنامه‌ای را حذف نمی‌کند و به داده‌های کلون یا نشست‌ها دست نمی‌زند."
                        : "Engine status will be checked again. The reservation is released only if the package is still confirmed absent. This does not uninstall an app or alter clone/session data.")
                .setPositiveButton(fa ? "تأیید و بررسی" : "Confirm and recheck", (dialog, which) -> {
                    status.setText(fa ? "در حال بررسی دوبارهٔ وضعیت موتور..." : "Rechecking Engine status...");
                    try {
                        EngineOperationQueue.execute(() -> {
                            Engine.CloneInstallState latest;
                            try {
                                latest = Engine.getCloneInstallState(
                                        reservation.getPackageName(), reservation.getUserId());
                            } catch (Throwable error) {
                                latest = Engine.CloneInstallState.UNKNOWN;
                            }

                            if (latest != Engine.CloneInstallState.ABSENT) {
                                final Engine.CloneInstallState state = latest;
                                runOnUiThread(() -> {
                                    if (isFinishing() || isDestroyed()) return;
                                    Toast.makeText(PendingReservationsActivity.this,
                                            state == Engine.CloneInstallState.INSTALLED
                                                    ? (fa ? "بسته نصب است؛ رزرو حفظ شد." : "Package is installed; reservation retained.")
                                                    : (fa ? "وضعیت موتور تأیید نشد؛ رزرو حفظ شد." : "Engine state is unconfirmed; reservation retained."),
                                            Toast.LENGTH_LONG).show();
                                    refreshReservations();
                                });
                                return;
                            }

                            repository.releaseReservationAfterEngineAbsence(reservation, true, result -> {
                                if (isFinishing() || isDestroyed()) return;
                                if (result.isSuccess()) {
                                    Toast.makeText(PendingReservationsActivity.this,
                                            fa ? "رزرو با موفقیت آزاد شد." : "Reservation released.",
                                            Toast.LENGTH_SHORT).show();
                                } else {
                                    Toast.makeText(PendingReservationsActivity.this,
                                            (fa ? "آزادسازی ناموفق بود: " : "Could not release reservation: ")
                                                    + result.getMessage(),
                                            Toast.LENGTH_LONG).show();
                                }
                                refreshReservations();
                            });
                        });
                    } catch (RuntimeException rejected) {
                        status.setText(fa
                                ? "بررسی موتور اجرا نشد؛ رزرو حفظ شد."
                                : "Engine check did not start; reservation retained.");
                    }
                })
                .setNegativeButton(fa ? "انصراف" : "Cancel", null)
                .show();
    }

    private boolean isCurrent(int generation) {
        return generation == refreshGeneration && !isFinishing() && !isDestroyed();
    }

    @Override
    protected void onDestroy() {
        refreshGeneration++;
        super.onDestroy();
    }
}
