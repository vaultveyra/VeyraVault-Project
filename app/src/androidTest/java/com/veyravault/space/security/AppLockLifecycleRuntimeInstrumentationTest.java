package com.veyravault.space.security;

import android.app.Activity;
import android.app.Application;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.SystemClock;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import android.app.Instrumentation;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ConcurrentHashMap;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public final class AppLockLifecycleRuntimeInstrumentationTest {
    private static final String CREDENTIAL_PREFS = "veyra_security_prefs";
    private static final String KEY_MODE = "lock_mode";
    private static final String KEY_HASH = "lock_hash";
    private static final String POLICY_PREFS = "veyra_security_policy_prefs";
    private static final String KEY_TIMEOUT = "background_lock_timeout_seconds";
    private static final long ACTIVITY_EVENT_TIMEOUT_MILLIS = 15_000L;
    private static final long LOCK_WAIT_TIMEOUT_MILLIS = 4_000L;

    @Test
    public void realActivityCallbacksDoNotLockDuringTransitionAndLockAfterLastActivityStops()
            throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        Application application = (Application) context.getApplicationContext();
        Instrumentation instrumentation = InstrumentationRegistry.getInstrumentation();

        assertTrue("Instrumentation must be running in the host app main process",
                com.veyravault.space.core.ProcessUtils.isMainProcess(application));

        SharedPreferences credentialPreferences = context.getSharedPreferences(
                CREDENTIAL_PREFS, Context.MODE_PRIVATE);
        SharedPreferences policyPreferences = context.getSharedPreferences(
                POLICY_PREFS, Context.MODE_PRIVATE);
        Map<String, ?> originalCredentials = new HashMap<>(credentialPreferences.getAll());
        Map<String, ?> originalPolicy = new HashMap<>(policyPreferences.getAll());

        Field unlockedField = SecurityManager.class.getDeclaredField("sessionUnlocked");
        unlockedField.setAccessible(true);
        boolean originalUnlockedState = unlockedField.getBoolean(null);

        Activity firstActivity = null;
        Activity secondActivity = null;
        boolean controllerInitialized = false;
        ProbeLifecycleObserver lifecycleObserver = new ProbeLifecycleObserver();

        try {
            assertTrue("Temporary test credential must be durably stored",
                    SecurityManager.setLockCredential(
                            context, SecurityManager.MODE_PIN, "4286"));
            assertTrue("Immediate timeout policy must be durably stored",
                    AppLockPolicy.setBackgroundTimeoutSeconds(
                            context, AppLockPolicy.TIMEOUT_IMMEDIATELY));

            // Use the exact production registration entry point called by VaultApp.onCreate().
            controllerInitialized = AppLockLifecycleController.initialize(application);
            assertTrue("App-lock lifecycle controller did not initialize in the main process",
                    controllerInitialized);
            assertTrue("Test credential should establish an unlocked session",
                    SecurityManager.isSessionUnlocked(context));

            // Register after the production controller so its callback observes each event first.
            application.registerActivityLifecycleCallbacks(lifecycleObserver);
            lifecycleObserver.markRegistered();

            firstActivity = launchProbeActivity(context, instrumentation, lifecycleObserver);
            assertTrue("First Activity should leave the test session unlocked",
                    SecurityManager.isSessionUnlocked(context));

            // The second Activity starts before the first finishes. The app must remain
            // foregrounded while at least one Activity is started.
            secondActivity = launchProbeActivity(context, instrumentation, lifecycleObserver);
            assertTrue("Opening a second Activity must not lock the session",
                    SecurityManager.isSessionUnlocked(context));

            finishProbeActivity(secondActivity, instrumentation, lifecycleObserver);
            secondActivity = null;
            assertTrue("Returning to the first Activity must cancel the pending background lock",
                    SecurityManager.isSessionUnlocked(context));

            finishProbeActivity(firstActivity, instrumentation, lifecycleObserver);
            firstActivity = null;

            assertTrue("The final Activity stop must trigger the configured background lock",
                    awaitSessionLock(context, LOCK_WAIT_TIMEOUT_MILLIS));
        } finally {
            // Finish any Activity left alive after an assertion failure. Avoid waitForIdleSync:
            // the lifecycle observer provides a direct signal for the actual stop callback.
            closeProbeActivityQuietly(secondActivity, instrumentation, lifecycleObserver);
            closeProbeActivityQuietly(firstActivity, instrumentation, lifecycleObserver);

            if (controllerInitialized) {
                awaitSessionLock(context, LOCK_WAIT_TIMEOUT_MILLIS);
            }

            if (lifecycleObserver.isRegistered()) {
                application.unregisterActivityLifecycleCallbacks(lifecycleObserver);
                lifecycleObserver.markUnregistered();
            }

            restorePreferenceKey(credentialPreferences, originalCredentials, KEY_MODE);
            restorePreferenceKey(credentialPreferences, originalCredentials, KEY_HASH);
            restorePreferenceKey(policyPreferences, originalPolicy, KEY_TIMEOUT);
            unlockedField.setBoolean(null, originalUnlockedState);

            assertEquals("Credential preferences were not restored exactly",
                    originalCredentials, credentialPreferences.getAll());
            assertEquals("App-lock policy preferences were not restored exactly",
                    originalPolicy, policyPreferences.getAll());
        }
    }

    private static Activity launchProbeActivity(
            Context context,
            Instrumentation instrumentation,
            ProbeLifecycleObserver observer) throws InterruptedException {
        Intent intent = new Intent(context, AppLockLifecycleProbeActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);

        // ActivityMonitor independently confirms that Android launched the component.
        // The lifecycle observer remains responsible for observing the actual stop event.
        Instrumentation.ActivityMonitor monitor = instrumentation.addMonitor(
                AppLockLifecycleProbeActivity.class.getName(), null, false);
        try {
            context.startActivity(intent);
            Activity activity = monitor.waitForActivityWithTimeout(ACTIVITY_EVENT_TIMEOUT_MILLIS);
            assertNotNull("Debug lifecycle probe Activity was not launched by ActivityManager", activity);
            return activity;
        } finally {
            instrumentation.removeMonitor(monitor);
        }
    }

    private static void finishProbeActivity(
            Activity activity,
            Instrumentation instrumentation,
            ProbeLifecycleObserver observer) throws InterruptedException {
        CountDownLatch stopped = observer.expectStopped(activity);
        instrumentation.runOnMainSync(() -> {
            if (!activity.isFinishing()) activity.finish();
        });
        assertTrue("Debug lifecycle probe Activity did not reach onActivityStopped",
                stopped.await(ACTIVITY_EVENT_TIMEOUT_MILLIS, TimeUnit.MILLISECONDS));
        observer.clearStopWaiter(activity);
    }

    private static void closeProbeActivityQuietly(
            Activity activity,
            Instrumentation instrumentation,
            ProbeLifecycleObserver observer) {
        if (activity == null) return;
        try {
            CountDownLatch stopped = observer.expectStopped(activity);
            instrumentation.runOnMainSync(() -> {
                if (!activity.isFinishing()) activity.finish();
            });
            stopped.await(5L, TimeUnit.SECONDS);
            observer.clearStopWaiter(activity);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
        } catch (RuntimeException ignored) {
            // Preserve the original assertion while still restoring the saved security state.
        }
    }

    private static boolean awaitSessionLock(Context context, long timeoutMillis)
            throws InterruptedException {
        long deadline = SystemClock.elapsedRealtime() + timeoutMillis;
        while (SystemClock.elapsedRealtime() < deadline) {
            if (!SecurityManager.isSessionUnlocked(context)) return true;
            Thread.sleep(25L);
        }
        return !SecurityManager.isSessionUnlocked(context);
    }

    private static void restorePreferenceKey(
            SharedPreferences preferences, Map<String, ?> original, String key) {
        SharedPreferences.Editor editor = preferences.edit();
        if (!original.containsKey(key)) {
            editor.remove(key);
        } else {
            Object value = original.get(key);
            if (value instanceof Integer) editor.putInt(key, (Integer) value);
            else if (value instanceof String) editor.putString(key, (String) value);
            else throw new AssertionError("Unexpected preference type for " + key);
        }
        assertTrue("Could not restore preference key " + key, editor.commit());
        assertEquals("Preference key changed after restoration: " + key,
                original.get(key), preferences.getAll().get(key));
    }

    private static final class ProbeLifecycleObserver
            implements Application.ActivityLifecycleCallbacks {
        private final Map<Activity, CountDownLatch> stopWaiters = new ConcurrentHashMap<>();
        private volatile boolean registered = false;

        CountDownLatch expectStopped(Activity activity) {
            CountDownLatch latch = new CountDownLatch(1);
            stopWaiters.put(activity, latch);
            return latch;
        }

        void clearStopWaiter(Activity activity) {
            stopWaiters.remove(activity);
        }

        boolean isRegistered() {
            return registered;
        }

        void markRegistered() {
            registered = true;
        }

        void markUnregistered() {
            registered = false;
        }

        @Override public void onActivityStopped(Activity activity) {
            if (activity instanceof AppLockLifecycleProbeActivity) {
                CountDownLatch latch = stopWaiters.get(activity);
                if (latch != null) latch.countDown();
            }
        }

        @Override public void onActivityCreated(Activity activity, android.os.Bundle state) { }
        @Override public void onActivityResumed(Activity activity) { }
        @Override public void onActivityPaused(Activity activity) { }
        @Override public void onActivitySaveInstanceState(Activity activity, android.os.Bundle state) { }
        @Override public void onActivityDestroyed(Activity activity) { }
    }
}
