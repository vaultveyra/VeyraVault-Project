package com.veyravault.space.core;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;

/**
 * Serialized asynchronous compatibility facade over the existing CloneStore.
 *
 * This class deliberately does not use Room and has no Engine or UI side effects.
 * Existing synchronous CloneStore callers are not serialized with this queue.
 */
public final class AsyncCloneRepository implements AutoCloseable {
    public enum Failure {
        INVALID_INPUT,
        CORRUPT_DATA,
        PERSISTENCE_FAILURE,
        EXECUTOR_CLOSED,
        INTERNAL_ERROR,
        ENGINE_STATE_UNCONFIRMED
    }

    public static final class Result<T> {
        private final T value;
        private final Failure failure;
        private final String message;

        private Result(T value, Failure failure, String message) {
            this.value = value;
            this.failure = failure;
            this.message = message;
        }

        static <T> Result<T> success(T value) {
            return new Result<T>(value, null, null);
        }

        static <T> Result<T> failure(Failure failure, String message) {
            return new Result<T>(null, failure, message);
        }

        public boolean isSuccess() { return failure == null; }
        public T getValue() { return value; }
        public Failure getFailure() { return failure; }
        public String getMessage() { return message; }
    }

    public interface Callback<T> {
        void onComplete(Result<T> result);
    }

    private interface Operation<T> {
        T run() throws Exception;
    }

    private static volatile AsyncCloneRepository instance;

    public static synchronized AsyncCloneRepository getInstance(Context context) {
        if (context == null) throw new IllegalArgumentException("Context is required");
        AsyncCloneRepository current = instance;
        if (current == null || current.closed) {
            current = new AsyncCloneRepository(context);
            instance = current;
        }
        return current;
    }

    private final Context appContext;
    private final ExecutorService worker;
    private final Executor callbackExecutor;
    private volatile boolean closed;

    public AsyncCloneRepository(Context context) {
        if (context == null) throw new IllegalArgumentException("Context is required");
        Context application = context.getApplicationContext();
        this.appContext = application == null ? context : application;
        this.worker = Executors.newSingleThreadExecutor(r -> {
            Thread thread = new Thread(r, "veyravault-persistence");
            thread.setDaemon(true);
            return thread;
        });
        final Handler main = new Handler(Looper.getMainLooper());
        this.callbackExecutor = command -> main.post(command);
    }

    // Package-private injection point for deterministic tests.
    AsyncCloneRepository(Context context, ExecutorService worker, Executor callbackExecutor) {
        if (context == null || worker == null || callbackExecutor == null)
            throw new IllegalArgumentException("Context and executors are required");
        Context application = context.getApplicationContext();
        this.appContext = application == null ? context : application;
        this.worker = worker;
        this.callbackExecutor = callbackExecutor;
    }

    public void loadClones(Callback<List<CloneStore.CloneEntry>> callback) {
        enqueue(() -> copyEntries(CloneStore.readAllStrict(appContext)), callback);
    }


    /** Durably reserves the next package-scoped virtual user ID before Engine installation. */
    public void reserveNextUserId(String packageName, Callback<CloneStore.CloneReservation> callback) {
        if (packageName == null || packageName.trim().isEmpty()) {
            deliver(callback, Result.<CloneStore.CloneReservation>failure(
                    Failure.INVALID_INPUT, "Package name is required"));
            return;
        }
        enqueue(() -> CloneStore.reserveNextUserId(appContext, packageName), callback);
    }

    /** Commits the clone record and consumes its exact reservation in one SharedPreferences commit. */
    public void commitReservedClone(CloneStore.CloneEntry entry, CloneStore.CloneReservation reservation,
                                    Callback<Boolean> callback) {
        if (entry == null || reservation == null) {
            deliver(callback, Result.<Boolean>failure(
                    Failure.INVALID_INPUT, "Clone entry and reservation are required"));
            return;
        }
        final CloneStore.CloneEntry snapshot = copyEntry(entry);
        try {
            validateEntry(snapshot);
        } catch (RuntimeException invalid) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, invalid.getMessage()));
            return;
        }
        enqueue(() -> {
            if (!CloneStore.commitReservedClone(appContext, copyEntry(snapshot), reservation))
                throw new PersistenceFailureException("Reserved clone commit was not durable");
            return Boolean.TRUE;
        }, callback);
    }

    /**
     * Releases a pending reservation only after the caller has positively verified that
     * Engine reports the corresponding virtual package absent. False/unknown never releases it.
     */
    public void releaseReservationAfterEngineAbsence(CloneStore.CloneReservation reservation,
                                                       boolean engineAbsenceConfirmed,
                                                       Callback<Boolean> callback) {
        if (reservation == null) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Reservation is required"));
            return;
        }
        if (!engineAbsenceConfirmed) {
            deliver(callback, Result.<Boolean>failure(Failure.ENGINE_STATE_UNCONFIRMED,
                    "Engine absence was not confirmed; reservation remains blocked"));
            return;
        }
        enqueue(() -> {
            if (!CloneStore.releaseReservationAfterEngineAbsence(appContext, reservation, true))
                throw new PersistenceFailureException("Reservation release was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void loadPendingReservations(Callback<List<CloneStore.CloneReservation>> callback) {
        enqueue(() -> new ArrayList<CloneStore.CloneReservation>(
                CloneStore.readPendingReservationsStrict(appContext)), callback);
    }

    /** @deprecated Use reserveNextUserId for every Engine-backed clone creation flow. */
    @Deprecated
    public void allocateNextUserId(String packageName, Callback<Integer> callback) {
        if (packageName == null || packageName.trim().isEmpty()) {
            deliver(callback, Result.<Integer>failure(Failure.INVALID_INPUT, "Package name is required"));
            return;
        }
        enqueue(() -> {
            int candidate = CloneStore.nextFreeUserIdForPackage(appContext, packageName);
            if (candidate < 0) throw new IllegalStateException(
                    "Clone registry or reservation journal could not be validated");
            return candidate;
        }, callback);
    }

    public void saveClones(List<CloneStore.CloneEntry> entries, Callback<Boolean> callback) {
        if (entries == null) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Clone list is required"));
            return;
        }
        final List<CloneStore.CloneEntry> snapshot;
        try {
            snapshot = copyEntries(entries);
            validateEntries(snapshot);
        } catch (RuntimeException invalid) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, invalid.getMessage()));
            return;
        }
        enqueue(() -> {
            CloneStore.readAllStrict(appContext);
            if (!CloneStore.saveAll(appContext, copyEntries(snapshot)))
                throw new PersistenceFailureException("Clone registry commit failed");
            return Boolean.TRUE;
        }, callback);
    }

    public void upsertClone(CloneStore.CloneEntry entry, Callback<Boolean> callback) {
        if (entry == null || entry.packageName == null || entry.packageName.trim().isEmpty()
                || entry.userId < 0) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Clone identity is invalid"));
            return;
        }
        final CloneStore.CloneEntry snapshot = copyEntry(entry);
        try {
            validateEntry(snapshot);
        } catch (RuntimeException invalid) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, invalid.getMessage()));
            return;
        }
        enqueue(() -> {
            CloneStore.readAllStrict(appContext);
            if (!CloneStore.upsertClone(appContext, copyEntry(snapshot)))
                throw new PersistenceFailureException("Clone registry upsert was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void removeClone(String packageName, int userId, Callback<Boolean> callback) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Clone identity is invalid"));
            return;
        }
        enqueue(() -> {
            CloneStore.readAllStrict(appContext);
            if (!CloneStore.removeClone(appContext, packageName, userId))
                throw new PersistenceFailureException("Clone registry removal was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void loadCollapsedSpaces(Callback<Set<Integer>> callback) {
        enqueue(() -> new HashSet<Integer>(CloneStore.readCollapsedSpaceNumbersStrict(appContext)), callback);
    }

    public void setSpaceCollapsed(int spaceNumber, boolean collapsed, Callback<Boolean> callback) {
        if (spaceNumber < 1) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Space number must be positive"));
            return;
        }
        enqueue(() -> {
            CloneStore.readCollapsedSpaceNumbersStrict(appContext);
            if (!CloneStore.setSpaceCollapsed(appContext, spaceNumber, collapsed))
                throw new PersistenceFailureException("Collapsed Spaces update was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void loadMasterMockGpsEnabled(Callback<Boolean> callback) {
        enqueue(() -> CloneStore.readMasterMockGpsEnabledStrict(appContext), callback);
    }

    public void setMasterMockGpsEnabled(boolean enabled, Callback<Boolean> callback) {
        enqueue(() -> {
            CloneStore.readMasterMockGpsEnabledStrict(appContext);
            if (!CloneStore.setMasterMockGpsEnabled(appContext, enabled))
                throw new PersistenceFailureException("Master GPS update was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void loadGlobalEnvironment(Callback<CloneStore.GlobalEnvConfig> callback) {
        enqueue(() -> copyGlobalEnvironment(CloneStore.readGlobalEnvStrict(appContext)), callback);
    }

    public void saveGlobalEnvironment(CloneStore.GlobalEnvConfig config, Callback<Boolean> callback) {
        if (config == null || config.brand == null || config.manufacturer == null
                || config.model == null || config.device == null || config.countryIso == null
                || config.simOperator == null || config.simOperatorName == null) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Global environment profile is invalid"));
            return;
        }
        final CloneStore.GlobalEnvConfig snapshot = copyGlobalEnvironment(config);
        enqueue(() -> {
            CloneStore.readGlobalEnvStrict(appContext);
            if (!CloneStore.saveGlobalEnv(appContext, snapshot))
                throw new PersistenceFailureException("Global environment profile was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void loadLastActiveLaunch(Callback<CloneStore.CloneEntry> callback) {
        enqueue(() -> {
            CloneStore.CloneEntry entry = CloneStore.readLastActiveLaunchStrict(appContext);
            return entry == null ? null : copyEntry(entry);
        }, callback);
    }

    public void recordActiveLaunch(CloneStore.CloneEntry entry, Callback<Boolean> callback) {
        if (entry == null || entry.packageName == null || entry.packageName.trim().isEmpty()
                || entry.userId < 0) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Active clone identity is invalid"));
            return;
        }
        final CloneStore.CloneEntry snapshot = copyEntry(entry);
        enqueue(() -> {
            CloneStore.readAllStrict(appContext);
            if (!CloneStore.recordActiveLaunch(appContext, snapshot))
                throw new PersistenceFailureException("Active launch marker was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void loadGlobalProfile(Callback<ProfileSettings> callback) {
        enqueue(() -> ProfileStore.readGlobalStrict(appContext).copy(), callback);
    }

    public void saveGlobalProfile(ProfileSettings settings, Callback<Boolean> callback) {
        if (settings == null || !settings.isValid()) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Global profile is invalid"));
            return;
        }
        final ProfileSettings snapshot = settings.copy();
        enqueue(() -> {
            ProfileStore.readGlobalStrict(appContext);
            if (!ProfileStore.saveGlobal(appContext, snapshot))
                throw new PersistenceFailureException("Global profile was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void loadCloneProfile(String packageName, int userId, Callback<ProfileSettings> callback) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0) {
            deliver(callback, Result.<ProfileSettings>failure(Failure.INVALID_INPUT, "Clone identity is invalid"));
            return;
        }
        enqueue(() -> ProfileStore.readCloneOverrideStrict(appContext, packageName, userId).copy(), callback);
    }

    public void saveCloneProfile(String packageName, int userId, ProfileSettings settings,
                                 Callback<Boolean> callback) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0
                || settings == null || !settings.isValid()) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Clone profile is invalid"));
            return;
        }
        final ProfileSettings snapshot = settings.copy();
        enqueue(() -> {
            ProfileStore.readCloneOverrideStrict(appContext, packageName, userId);
            if (!ProfileStore.saveCloneOverride(appContext, packageName, userId, snapshot))
                throw new PersistenceFailureException("Clone profile was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void clearCloneProfileField(String packageName, int userId, String field,
                                       Callback<Boolean> callback) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0
                || !isSupportedProfileField(field)) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Clone profile field request is invalid"));
            return;
        }
        enqueue(() -> {
            ProfileStore.readCloneOverrideStrict(appContext, packageName, userId);
            if (!ProfileStore.clearCloneOverrideField(appContext, packageName, userId, field))
                throw new PersistenceFailureException("Clone profile field clear was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void clearGlobalProfileField(String field, Callback<Boolean> callback) {
        if (!isSupportedProfileField(field)) {
            deliver(callback, Result.<Boolean>failure(Failure.INVALID_INPUT, "Profile field is unsupported or missing"));
            return;
        }
        enqueue(() -> {
            ProfileStore.readGlobalStrict(appContext);
            if (!ProfileStore.clearGlobalField(appContext, field))
                throw new PersistenceFailureException("Global profile field clear was not committed");
            return Boolean.TRUE;
        }, callback);
    }

    public void migrateLegacyLocationProfiles(Callback<Boolean> callback) {
        enqueue(() -> {
            if (!ProfileStore.migrateLegacyLocationSettings(appContext))
                throw new PersistenceFailureException("Legacy profile import was not completed");
            return Boolean.TRUE;
        }, callback);
    }

    private <T> void enqueue(Operation<T> operation, Callback<T> callback) {
        if (callback == null) return;
        if (closed) {
            deliver(callback, Result.<T>failure(Failure.EXECUTOR_CLOSED, "Repository is closed"));
            return;
        }
        try {
            worker.execute(() -> {
                Result<T> result;
                try {
                    result = Result.success(operation.run());
                } catch (Exception error) {
                    result = Result.failure(classify(error), safeMessage(error));
                }
                deliver(callback, result);
            });
        } catch (RejectedExecutionException rejected) {
            deliver(callback, Result.<T>failure(
                    closed ? Failure.EXECUTOR_CLOSED : Failure.INTERNAL_ERROR,
                    "Persistence task was rejected"));
        }
    }

    private <T> void deliver(Callback<T> callback, Result<T> result) {
        if (callback == null) return;
        try {
            callbackExecutor.execute(() -> callback.onComplete(result));
        } catch (RuntimeException ignored) {
            // A shutting-down callback executor must not cause a false persistence result.
        }
    }

    static Failure classify(Throwable error) {
        if (error instanceof PersistenceFailureException
                || error instanceof CloneStore.PersistenceException) return Failure.PERSISTENCE_FAILURE;
        if (error instanceof IllegalArgumentException) return Failure.INVALID_INPUT;
        if (error instanceof IllegalStateException
                || error instanceof org.json.JSONException) return Failure.CORRUPT_DATA;
        return Failure.INTERNAL_ERROR;
    }

    private static String safeMessage(Throwable error) {
        String message = error == null ? null : error.getMessage();
        return message == null || message.trim().isEmpty()
                ? "Persistence operation failed" : message;
    }

    private static boolean isSupportedProfileField(String field) {
        return "localeTag".equals(field) || "timeZoneId".equals(field)
                || "locationEnabled".equals(field) || "latitude".equals(field)
                || "longitude".equals(field);
    }

    private static void validateEntries(List<CloneStore.CloneEntry> entries) {
        Set<String> identities = new HashSet<String>();
        for (CloneStore.CloneEntry entry : entries) {
            validateEntry(entry);
            if (!identities.add(entry.packageName + "\\u0000" + entry.userId))
                throw new IllegalArgumentException("Duplicate clone identity");
        }
    }

    private static void validateEntry(CloneStore.CloneEntry entry) {
        if (entry == null || entry.packageName == null || entry.packageName.trim().isEmpty()
                || entry.userId < 0 || entry.deniedPermissions == null)
            throw new IllegalArgumentException("Clone entry is invalid");
        if (entry.mockGpsEnabled && (Double.isNaN(entry.latitude) || Double.isInfinite(entry.latitude)
                || Double.isNaN(entry.longitude) || Double.isInfinite(entry.longitude)
                || entry.latitude < -90.0d || entry.latitude > 90.0d
                || entry.longitude < -180.0d || entry.longitude > 180.0d))
            throw new IllegalArgumentException("Enabled clone location is invalid");
        for (String permission : entry.deniedPermissions) {
            if (permission == null || permission.trim().isEmpty())
                throw new IllegalArgumentException("Denied permission is invalid");
        }
    }

    private static CloneStore.GlobalEnvConfig copyGlobalEnvironment(CloneStore.GlobalEnvConfig source) {
        CloneStore.GlobalEnvConfig copy = new CloneStore.GlobalEnvConfig();
        copy.enabled = source.enabled;
        copy.brand = source.brand;
        copy.manufacturer = source.manufacturer;
        copy.model = source.model;
        copy.device = source.device;
        copy.countryIso = source.countryIso;
        copy.simOperator = source.simOperator;
        copy.simOperatorName = source.simOperatorName;
        return copy;
    }

    private static List<CloneStore.CloneEntry> copyEntries(List<CloneStore.CloneEntry> entries) {
        List<CloneStore.CloneEntry> copy = new ArrayList<CloneStore.CloneEntry>(entries.size());
        for (CloneStore.CloneEntry entry : entries) copy.add(copyEntry(entry));
        return copy;
    }

    private static CloneStore.CloneEntry copyEntry(CloneStore.CloneEntry source) {
        if (source == null) throw new IllegalArgumentException("Clone entry is null");
        CloneStore.CloneEntry copy = new CloneStore.CloneEntry();
        copy.packageName = source.packageName;
        copy.userId = source.userId;
        copy.displayName = source.displayName;
        copy.mockGpsEnabled = source.mockGpsEnabled;
        copy.latitude = source.latitude;
        copy.longitude = source.longitude;
        copy.locationLabel = source.locationLabel;
        copy.customDeviceEnabled = source.customDeviceEnabled;
        copy.deviceBrand = source.deviceBrand;
        copy.deviceModel = source.deviceModel;
        copy.deniedPermissions = source.deniedPermissions == null
                ? null : new HashSet<String>(source.deniedPermissions);
        return copy;
    }

    @Override
    public void close() {
        synchronized (AsyncCloneRepository.class) {
            if (!closed) {
                closed = true;
                worker.shutdown();
                if (instance == this) instance = null;
            }
        }
    }

    private static final class PersistenceFailureException extends Exception {
        PersistenceFailureException(String message) { super(message); }
    }
}
