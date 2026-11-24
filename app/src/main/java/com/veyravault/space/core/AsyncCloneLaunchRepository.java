package com.veyravault.space.core;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import java.util.List;
import java.util.concurrent.RejectedExecutionException;

/**
 * Runs the complete clone launch sequence away from the UI thread.
 * Registry lookup, installation, location-hook synchronization, engine launch and
 * active-launch persistence share the process-wide Engine operation queue.
 */
public final class AsyncCloneLaunchRepository {
    public interface Callback {
        void onComplete(Outcome outcome);
    }

    public static final class Outcome {
        public final CloneStore.CloneEntry clone;
        public final Engine.CloneLaunchResult launchResult;
        public final String error;

        private Outcome(CloneStore.CloneEntry clone, Engine.CloneLaunchResult launchResult, String error) {
            this.clone = clone;
            this.launchResult = launchResult;
            this.error = error;
        }

        public boolean isLaunched() {
            return launchResult != null && launchResult.launched;
        }
    }

    private static volatile AsyncCloneLaunchRepository instance;
    private final Context appContext;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private AsyncCloneLaunchRepository(Context context) {
        appContext = context.getApplicationContext();
    }

    public static AsyncCloneLaunchRepository getInstance(Context context) {
        if (context == null) throw new IllegalArgumentException("Context is required");
        AsyncCloneLaunchRepository current = instance;
        if (current != null) return current;
        synchronized (AsyncCloneLaunchRepository.class) {
            if (instance == null) instance = new AsyncCloneLaunchRepository(context);
            return instance;
        }
    }

    public void launchClone(String packageName, int userId, Callback callback) {
        if (callback == null) return;
        if (packageName == null || packageName.trim().isEmpty() || userId < 0) {
            deliver(callback, new Outcome(null, null, "INVALID_CLONE_IDENTITY"));
            return;
        }
        try {
            EngineOperationQueue.execute(() -> {
                Outcome outcome;
                try {
                    List<CloneStore.CloneEntry> entries = CloneStore.readAllStrict(appContext);
                    CloneStore.CloneEntry target = null;
                    for (CloneStore.CloneEntry entry : entries) {
                        if (entry != null && packageName.equals(entry.packageName)
                                && userId == entry.userId) {
                            target = entry;
                            break;
                        }
                    }
                    if (target == null) {
                        outcome = new Outcome(null, null, "CLONE_NOT_FOUND_IN_STRICT_REGISTRY");
                    } else {
                        Engine.CloneLaunchResult result = Engine.launchCloneDetailed(appContext, target);
                        outcome = new Outcome(target, result, null);
                    }
                } catch (Throwable failure) {
                    outcome = new Outcome(null, null, failure.getClass().getSimpleName() + ":"
                            + (failure.getMessage() == null ? "CLONE_LAUNCH_PREPARATION_FAILED" : failure.getMessage()));
                }
                deliver(callback, outcome);
            });
        } catch (RejectedExecutionException rejected) {
            deliver(callback, new Outcome(null, null, "CLONE_LAUNCH_WORKER_REJECTED"));
        }
    }

    private void deliver(Callback callback, Outcome outcome) {
        mainHandler.post(() -> callback.onComplete(outcome));
    }
}
