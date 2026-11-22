package com.veyravault.space.security;

import android.app.Activity;
import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.SystemClock;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.core.app.ActivityScenario;

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

        ProbeActivityHandle firstActivity = null;
        ProbeActivityHandle secondActivity = null;
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

            firstActivity = launchProbeActivity(lifecycleObserver);
            assertTrue("First Activity should leave the test session unlocked",
                    SecurityManager.isSessionUnlocked(context));

            // The second Activity starts before the first finishes. The app must remain
            // foregrounded while at least one Activity is started.
            secondActivity = launchProbeActivity(lifecycleObserver);
            assertTrue("Opening a second Activity must not lock the session",
                    SecurityManager.isSessionUnlocked(context));

            finishProbeActivity(secondActivity, lifecycleObserver);
            secondActivity = null;
            assertTrue("Returning to the first Activity must cancel the pending background lock",
                    SecurityManager.isSessionUnlocked(context));

            finishProbeActivity(firstActivity, lifecycleObserver);
            firstActivity = null;

            assertTrue("The final Activity stop must trigger the configured background lock",
                    awaitSessionLock(context, LOCK_WAIT_TIMEOUT_MILLIS));
        } finally {
            // Finish any Activity left alive after an assertion failure. Avoid waitForIdleSync:
            // the lifecycle observer provides a direct signal for the actual stop callback.
            closeProbeActivityQuietly(secondActivity, lifecycleObserver);
            closeProbeActivityQuietly(firstActivity, lifecycleObserver);

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

    private static ProbeActivityHandle launchProbeActivity(
            ProbeLifecycleObserver observer) throws InterruptedException {
        // ActivityScenario owns launch and teardown, avoiding timing-sensitive manual launch
        // monitoring while still exercising Android's real Application lifecycle callbacks.
        ActivityScenario<AppLockLifecycleProbeActivity> scenario =
                ActivityScenario.launch(AppLockLifecycleProbeActivity.class);
        Activity[] activityHolder = new Activity[1];
        scenario.onActivity(activity -> activityHolder[0] = activity);
        Activity activity = activityHolder[0];
        assertNotNull("ActivityScenario did not provide the launched debug Activity", activity);
        assertTrue("Debug lifecycle probe Activity did not reach onActivityResumed",
                observer.awaitResumed(activity, ACTIVITY_EVENT_TIMEOUT_MILLIS));
        return new ProbeActivityHandle(scenario, activity);
    }

    private static void finishProbeActivity(
            ProbeActivityHandle handle,
            ProbeLifecycleObserver observer) throws InterruptedException {
        CountDownLatch stopped = observer.expectStopped(handle.activity);
        // ActivityScenario.close() drives the Activity to DESTROYED on the main thread and
        // waits for the lifecycle transition; the observer verifies the actual STOPPED event.
        handle.scenario.close();
        assertTrue("Debug lifecycle probe Activity did not reach onActivityStopped",
                stopped.await(ACTIVITY_EVENT_TIMEOUT_MILLIS, TimeUnit.MILLISECONDS));
        observer.clearStopWaiter(handle.activity);
    }

    private static void closeProbeActivityQuietly(
            ProbeActivityHandle handle,
            ProbeLifecycleObserver observer) {
        if (handle == null) return;
        try {
            CountDownLatch stopped = observer.expectStopped(handle.activity);
            handle.scenario.close();
            stopped.await(5L, TimeUnit.SECONDS);
            observer.clearStopWaiter(handle.activity);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
        } catch (RuntimeException ignored) {
            // Preserve the original assertion while still restoring the saved security state.
        }
    }

    private static final class ProbeActivityHandle {
        final ActivityScenario<AppLockLifecycleProbeActivity> scenario;
        final Activity activity;

        ProbeActivityHandle(
                ActivityScenario<AppLockLifecycleProbeActivity> scenario,
                Activity activity) {
            this.scenario = scenario;
            this.activity = activity;
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
        private final Map<Activity, CountDownLatch> resumeWaiters = new ConcurrentHashMap<>();
        private final Map<Activity, CountDownLatch> stopWaiters = new ConcurrentHashMap<>();
        private final java.util.Set<Activity> resumedActivities = ConcurrentHashMap.newKeySet();
        private final java.util.Set<Activity> stoppedActivities = ConcurrentHashMap.newKeySet();
        private volatile boolean registered = false;

        boolean awaitResumed(Activity activity, long timeoutMillis) throws InterruptedException {
            if (resumedActivities.contains(activity)) return true;
            CountDownLatch latch = new CountDownLatch(1);
            CountDownLatch existing = resumeWaiters.putIfAbsent(activity, latch);
            if (existing != null) latch = existing;
            if (resumedActivities.contains(activity)) latch.countDown();
            boolean resumed = latch.await(timeoutMillis, TimeUnit.MILLISECONDS);
            resumeWaiters.remove(activity, latch);
            return resumed;
        }

        CountDownLatch expectStopped(Activity activity) {
            CountDownLatch latch = new CountDownLatch(1);
            if (stoppedActivities.contains(activity)) {
                latch.countDown();
                return latch;
            }
            CountDownLatch existing = stopWaiters.putIfAbsent(activity, latch);
            if (existing != null) latch = existing;
            if (stoppedActivities.contains(activity)) latch.countDown();
            return latch;
        }

        void clearStopWaiter(Activity activity) {
            stopWaiters.remove(activity);
            resumeWaiters.remove(activity);
            resumedActivities.remove(activity);
            stoppedActivities.remove(activity);
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

        @Override public void onActivityStarted(Activity activity) { }

        @Override public void onActivityStopped(Activity activity) {
            if (activity instanceof AppLockLifecycleProbeActivity) {
                stoppedActivities.add(activity);
                CountDownLatch latch = stopWaiters.get(activity);
                if (latch != null) latch.countDown();
            }
        }

        @Override public void onActivityCreated(Activity activity, android.os.Bundle state) { }
        @Override public void onActivityResumed(Activity activity) {
            if (activity instanceof AppLockLifecycleProbeActivity) {
                resumedActivities.add(activity);
                CountDownLatch latch = resumeWaiters.get(activity);
                if (latch != null) latch.countDown();
            }
        }
        @Override public void onActivityPaused(Activity activity) { }
        @Override public void onActivitySaveInstanceState(Activity activity, android.os.Bundle state) { }
        @Override public void onActivityDestroyed(Activity activity) { }
    }
}
