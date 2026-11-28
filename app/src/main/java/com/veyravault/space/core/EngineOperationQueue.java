package com.veyravault.space.core;

import android.os.Handler;
import android.os.Looper;

import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;

/** Process-wide serialization point for synchronous calls into the pinned virtualization Engine. */
public final class EngineOperationQueue {
    public interface Callback<T> {
        void onComplete(T value, Throwable failure);
    }

    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final ExecutorService ENGINE = Executors.newSingleThreadExecutor(r -> {
        Thread thread = new Thread(r, "veyravault-engine-operations");
        thread.setDaemon(true);
        return thread;
    });

    private EngineOperationQueue() { }

    public static void execute(Runnable operation) {
        if (operation == null) throw new IllegalArgumentException("Engine operation is required");
        ENGINE.execute(operation);
    }

    /** Executes one Engine operation and posts its result to the main thread. */
    public static <T> void submit(Callable<T> operation, Callback<T> callback) {
        if (operation == null || callback == null)
            throw new IllegalArgumentException("Engine operation and callback are required");
        try {
            ENGINE.execute(() -> {
                T value = null;
                Throwable failure = null;
                try {
                    value = operation.call();
                } catch (Throwable error) {
                    failure = error;
                }
                final T result = value;
                final Throwable error = failure;
                MAIN.post(() -> callback.onComplete(result, error));
            });
        } catch (RejectedExecutionException rejected) {
            MAIN.post(() -> callback.onComplete(null, rejected));
        }
    }
}
