package com.veyravault.space.core;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

/**
 * Coordinates safe Clone creation without running synchronous Engine work on the UI thread.
 * Activity callbacks are presentation-only: closing an Activity does not cancel a reserved
 * installation transaction or its confirmed rollback/recovery work.
 */
public final class AsyncCloneProvisionRepository {
    public interface Callback {
        void onComplete(Outcome outcome);
    }

    public static final class Outcome {
        public final boolean success;
        public final CloneStore.CloneEntry clone;
        public final String message;
        public final boolean reservationRetained;

        private Outcome(boolean success, CloneStore.CloneEntry clone,
                        String message, boolean reservationRetained) {
            this.success = success;
            this.clone = clone;
            this.message = message;
            this.reservationRetained = reservationRetained;
        }
    }

    private static final class InstallAttempt {
        final boolean installed;
        final boolean confirmedAbsent;
        final String diagnostic;
        final Engine.CloneInstallState state;

        InstallAttempt(boolean installed, boolean confirmedAbsent,
                       String diagnostic, Engine.CloneInstallState state) {
            this.installed = installed;
            this.confirmedAbsent = confirmedAbsent;
            this.diagnostic = diagnostic;
            this.state = state;
        }
    }

    private static volatile AsyncCloneProvisionRepository instance;
    private final Context appContext;
    private final AsyncCloneRepository persistence;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private AsyncCloneProvisionRepository(Context context) {
        Context application = context.getApplicationContext();
        appContext = application == null ? context : application;
        persistence = AsyncCloneRepository.getInstance(appContext);
    }

    public static AsyncCloneProvisionRepository getInstance(Context context) {
        if (context == null) throw new IllegalArgumentException("Context is required");
        AsyncCloneProvisionRepository current = instance;
        if (current != null) return current;
        synchronized (AsyncCloneProvisionRepository.class) {
            if (instance == null) instance = new AsyncCloneProvisionRepository(context);
            return instance;
        }
    }

    public void createClone(String packageName, String displayName, boolean persian, Callback callback) {
        if (callback == null) return;
        if (packageName == null || packageName.trim().isEmpty()) {
            deliver(callback, failure("CLONE_PACKAGE_INVALID", false));
            return;
        }

        // Read-only APK/ABI check must finish before any ID reservation is made.
        persistence.inspectNativeAbi(packageName, inspection -> {
            if (!inspection.isSuccess() || inspection.getValue() == null) {
                deliver(callback, failure((persian
                        ? "بررسی سازگاری APK ناموفق بود؛ شناسه‌ای رزرو نشد. "
                        : "APK compatibility inspection failed; no ID was reserved. ")
                        + inspection.getMessage(), false));
                return;
            }

            final NativeAbiPreflight.Result preflight = inspection.getValue();
            if (!preflight.isAllowed()) {
                deliver(callback, failure(preflight.getUserMessage(persian)
                        + " [" + preflight.getDiagnosticCode() + "]", false));
                return;
            }

            // The reservation is durable and token-bound before Engine installation begins.
            persistence.reserveNextUserId(packageName, allocation -> {
                if (!allocation.isSuccess() || allocation.getValue() == null) {
                    deliver(callback, failure((persian
                            ? "رزرو امن شناسه انجام نشد؛ نصب آغاز نشد. "
                            : "A safe Clone ID could not be reserved; installation did not start. ")
                            + allocation.getMessage(), false));
                    return;
                }

                final CloneStore.CloneReservation reservation = allocation.getValue();
                final CloneStore.CloneEntry entry = new CloneStore.CloneEntry();
                entry.packageName = packageName;
                entry.userId = reservation.getUserId();
                entry.displayName = displayName == null || displayName.trim().isEmpty()
                        ? packageName : displayName;

                try {
                    EngineOperationQueue.submit(() -> {
                        boolean installed = Engine.installPackageAsUser(
                                appContext, entry.packageName, entry.userId, preflight);
                        String diagnostic = Engine.getLastInstallDiagnostic();
                        Engine.CloneInstallState state = installed
                                ? Engine.CloneInstallState.INSTALLED
                                : Engine.getCloneInstallState(entry.packageName, entry.userId);
                        return new InstallAttempt(installed,
                                !installed && state == Engine.CloneInstallState.ABSENT,
                                diagnostic, state);
                    }, (attempt, engineFailure) -> {
                        if (engineFailure != null || attempt == null) {
                            deliver(callback, failure((persian
                                    ? "نتیجهٔ موتور قابل تأیید نیست؛ رزرو شناسه برای جلوگیری از تداخل حفظ شد. "
                                    : "The Engine result could not be confirmed; the ID reservation remains blocked. ")
                                    + safeError(engineFailure), true));
                            return;
                        }

                        if (!attempt.installed) {
                            String message = (persian ? "نصب کلون ناموفق بود: " : "Clone installation failed: ")
                                    + attempt.diagnostic + " [" + attempt.state + "]";
                            if (attempt.confirmedAbsent) {
                                releaseAfterConfirmedAbsence(reservation, message, persian, callback);
                            } else {
                                deliver(callback, failure(message + (persian
                                        ? "؛ نبودن بسته تأیید نشد و رزرو حفظ شد."
                                        : "; package absence was not confirmed and the reservation remains blocked."),
                                        true));
                            }
                            return;
                        }

                        // The registry row and this exact reservation are committed atomically.
                        persistence.commitReservedClone(entry, reservation, save -> {
                            if (save.isSuccess()) {
                                deliver(callback, new Outcome(true, entry,
                                        persian ? "کلون با موفقیت به فهرست فضاها اضافه شد."
                                                : "Clone was added to the Spaces registry.", false));
                                return;
                            }

                            // Registry failure must not leave an untracked Engine package.
                            try {
                                EngineOperationQueue.submit(
                                        () -> Engine.uninstallClone(entry.packageName, entry.userId),
                                        (cleanupConfirmed, cleanupFailure) -> {
                                            String message = (persian
                                                    ? "ثبت کلون در فهرست ناموفق بود. "
                                                    : "The Clone registry commit failed. ")
                                                    + save.getMessage();
                                            if (cleanupFailure == null && Boolean.TRUE.equals(cleanupConfirmed)) {
                                                releaseAfterConfirmedAbsence(reservation, message, persian, callback);
                                            } else {
                                                deliver(callback, failure(message + (persian
                                                        ? "؛ حذف نصب تأیید نشد و رزرو برای بررسی بعدی حفظ شد."
                                                        : "; uninstall was not confirmed and the reservation remains blocked for recovery."),
                                                        true));
                                            }
                                        });
                            } catch (RuntimeException rejected) {
                                deliver(callback, failure((persian
                                        ? "ثبت فهرست ناموفق بود و پاکسازی موتور اجرا نشد؛ رزرو حفظ شد. "
                                        : "Registry commit failed and Engine cleanup could not be queued; the reservation remains blocked. ")
                                        + safeError(rejected), true));
                            }
                        });
                    });
                } catch (RuntimeException rejected) {
                    deliver(callback, failure((persian
                            ? "صف عملیات موتور در دسترس نیست؛ رزرو شناسه حفظ شد. "
                            : "The Engine operation queue is unavailable; the ID reservation remains blocked. ")
                            + safeError(rejected), true));
                }
            });
        });
    }

    private void releaseAfterConfirmedAbsence(CloneStore.CloneReservation reservation,
            String reason, boolean persian, Callback callback) {
        persistence.releaseReservationAfterEngineAbsence(reservation, true, release -> {
            if (release.isSuccess()) {
                deliver(callback, failure(reason + (persian
                        ? " نبودن بسته تأیید شد و رزرو آزاد شد."
                        : " Engine confirmed absence and the reservation was released."), false));
            } else {
                deliver(callback, failure(reason + (persian
                        ? " نبودن بسته تأیید شد، اما ثبت آزادسازی ناموفق بود؛ شناسه مسدود ماند."
                        : " Engine confirmed absence, but reservation release was not committed; the ID remains blocked."),
                        true));
            }
        });
    }

    private void deliver(Callback callback, Outcome outcome) {
        mainHandler.post(() -> callback.onComplete(outcome));
    }

    private static Outcome failure(String message, boolean reservationRetained) {
        return new Outcome(false, null, message, reservationRetained);
    }

    private static String safeError(Throwable error) {
        if (error == null) return "UNKNOWN";
        String message = error.getMessage();
        return error.getClass().getSimpleName()
                + (message == null || message.trim().isEmpty() ? "" : ": " + message);
    }
}
