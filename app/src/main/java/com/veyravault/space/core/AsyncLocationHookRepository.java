package com.veyravault.space.core;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import java.util.List;
import java.util.concurrent.RejectedExecutionException;

/**
 * Runs synchronous BlackBox location-service IPC on the shared Engine operation queue.
 * Persistence remains owned by AsyncCloneRepository; this class only synchronizes Engine hooks.
 */
public final class AsyncLocationHookRepository {
    public interface Callback<T> {
        void onComplete(T value, String error);
    }

    private static volatile AsyncLocationHookRepository instance;
    private final Context appContext;
    private final Handler callbackHandler = new Handler(Looper.getMainLooper());

    private AsyncLocationHookRepository(Context context) {
        appContext = context.getApplicationContext();
    }

    public static AsyncLocationHookRepository getInstance(Context context) {
        if (context == null) throw new IllegalArgumentException("Context is required");
        AsyncLocationHookRepository current = instance;
        if (current != null) return current;
        synchronized (AsyncLocationHookRepository.class) {
            if (instance == null) instance = new AsyncLocationHookRepository(context);
            return instance;
        }
    }

    public void syncCloneLocationHook(String packageName, int userId,
            Callback<VirtualHookManager.LocationApplyResult> callback) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0) {
            deliver(callback, null, "Clone identity is invalid");
            return;
        }
        submit(() -> {
            CloneStore.CloneEntry target = null;
            List<CloneStore.CloneEntry> clones = CloneStore.readAllStrict(appContext);
            for (CloneStore.CloneEntry entry : clones) {
                if (packageName.equals(entry.packageName) && userId == entry.userId) {
                    target = entry;
                    break;
                }
            }
            if (target == null) throw new IllegalStateException(
                    "Clone identity is not present in the strict registry");
            return VirtualHookManager.syncCloneHooks(appContext, target);
        }, callback);
    }

    public void syncAllCloneLocationHooks(Callback<VirtualHookManager.SyncSummary> callback) {
        submit(() -> VirtualHookManager.syncAllClones(appContext), callback);
    }

    private <T> void submit(Operation<T> operation, Callback<T> callback) {
        if (callback == null) return;
        try {
            EngineOperationQueue.execute(() -> {
                T value = null;
                String error = null;
                try {
                    value = operation.run();
                } catch (Exception failure) {
                    error = failure.getClass().getSimpleName() + ": "
                            + (failure.getMessage() == null ? "Location hook operation failed" : failure.getMessage());
                }
                deliver(callback, value, error);
            });
        } catch (RejectedExecutionException rejected) {
            deliver(callback, null, "Location hook worker rejected the operation");
        }
    }

    private <T> void deliver(Callback<T> callback, T value, String error) {
        if (callback != null) callbackHandler.post(() -> callback.onComplete(value, error));
    }

    private interface Operation<T> {
        T run() throws Exception;
    }
}
