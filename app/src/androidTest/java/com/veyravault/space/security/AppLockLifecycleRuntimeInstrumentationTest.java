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

            firstActivity = launchProbeActivity(context, instrumentation);
            assertTrue("First Activity should leave the test session unlocked",
                    SecurityManager.isSessionUnlocked(context));

            // The second Activity starts before the first finishes. The app must remain
            // foregrounded while at least one Activity is started.
            secondActivity = launchProbeActivity(context, instrumentation);
            assertTrue("Opening a second Activity must not lock the session",
                    SecurityManager.isSessionUnlocked(context));

            finishProbeActivity(secondActivity, instrumentation);
            secondActivity = null;
            assertTrue("Returning to the first Activity must cancel the pending background lock",
                    SecurityManager.isSessionUnlocked(context));

            finishProbeActivity(firstActivity, instrumentation);
            firstActivity = null;

            assertTrue("The final Activity stop must trigger the configured background lock",
                    awaitSessionLock(context, LOCK_WAIT_TIMEOUT_MILLIS));
        } finally {
            // Close any Activity left alive by an assertion failure, then let a possible
            // immediate-lock callback drain before restoring the caller's original state.
            finishProbeActivity(secondActivity, instrumentation);
            finishProbeActivity(firstActivity, instrumentation);
            if (controllerInitialized) {
                awaitSessionLock(context, LOCK_WAIT_TIMEOUT_MILLIS);
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
            Context context, Instrumentation instrumentation) {
        Intent intent = new Intent(context, AppLockLifecycleProbeActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Activity activity = instrumentation.startActivitySync(intent);
        assertNotNull("Debug lifecycle probe Activity failed to launch", activity);
        instrumentation.waitForIdleSync();
        return activity;
    }

    private static void finishProbeActivity(
            Activity activity, Instrumentation instrumentation) {
        if (activity == null) return;
        instrumentation.runOnMainSync(() -> {
            if (!activity.isFinishing()) activity.finish();
        });
        instrumentation.waitForIdleSync();
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
}
