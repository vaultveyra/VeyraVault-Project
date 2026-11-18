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
        INTERNAL_ERROR
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

    public void allocateNextUserId(String packageName, Callback<Integer> callback) {
        if (packageName == null || packageName.trim().isEmpty()) {
            deliver(callback, Result.<Integer>failure(Failure.INVALID_INPUT, "Package name is required"));
            return;
        }
        enqueue(() -> {
            Set<Integer> used = new HashSet<Integer>();
            for (CloneStore.CloneEntry entry : CloneStore.readAllStrict(appContext)) {
                if (packageName.equals(entry.packageName)) used.add(entry.userId);
            }
            int candidate = 0;
            while (used.contains(candidate)) {
                if (candidate == Integer.MAX_VALUE)
                    throw new IllegalStateException("No virtual user ID is available");
                candidate++;
            }
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
            if (!CloneStore.removeClone(appContext, packageName, userId))
                throw new PersistenceFailureException("Clone registry removal was not committed");
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
                } catch (Throwable error) {
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

    private static Failure classify(Throwable error) {
        if (error instanceof PersistenceFailureException) return Failure.PERSISTENCE_FAILURE;
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
    public synchronized void close() {
        if (!closed) {
            closed = true;
            worker.shutdown();
        }
    }

    private static final class PersistenceFailureException extends Exception {
        PersistenceFailureException(String message) { super(message); }
    }
}
