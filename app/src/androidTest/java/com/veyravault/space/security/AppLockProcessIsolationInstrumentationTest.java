package com.veyravault.space.security;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.RemoteException;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public final class AppLockProcessIsolationInstrumentationTest {
    private static final String CREDENTIAL_PREFS = "veyra_security_prefs";

    @Test
    public void freshAndroidProcessDoesNotInheritUnlockedHostSession() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        SharedPreferences preferences = context.getSharedPreferences(
                CREDENTIAL_PREFS, Context.MODE_PRIVATE);
        Map<String, ?> originalPreferences = new HashMap<>(preferences.getAll());

        Field unlockedField = SecurityManager.class.getDeclaredField("sessionUnlocked");
        Field failedAttemptsField =
                SecurityManager.class.getDeclaredField("processFailedAttempts");
        Field lockoutUntilElapsedField =
                SecurityManager.class.getDeclaredField("processLockoutUntilElapsed");
        unlockedField.setAccessible(true);
        failedAttemptsField.setAccessible(true);
        lockoutUntilElapsedField.setAccessible(true);
        boolean originalUnlockedState = unlockedField.getBoolean(null);
        int originalFailedAttempts = failedAttemptsField.getInt(null);
        long originalLockoutUntilElapsed = lockoutUntilElapsedField.getLong(null);

        final CountDownLatch resultLatch = new CountDownLatch(1);
        final AtomicReference<Boolean> remoteUnlockedState = new AtomicReference<>();
        final AtomicReference<Messenger> remoteMessenger = new AtomicReference<>();
        final Messenger responseMessenger = new Messenger(new Handler(Looper.getMainLooper(), message -> {
            if (message.what == AppLockSessionProbeService.MSG_SESSION_STATE_RESULT) {
                remoteUnlockedState.set(message.arg1 == 1);
                resultLatch.countDown();
                return true;
            }
            return false;
        }));

        ServiceConnection connection = new ServiceConnection() {
            @Override
            public void onServiceConnected(ComponentName name, IBinder service) {
                remoteMessenger.set(new Messenger(service));
                Message request = Message.obtain(
                        null, AppLockSessionProbeService.MSG_QUERY_SESSION_STATE);
                request.replyTo = responseMessenger;
                try {
                    remoteMessenger.get().send(request);
                } catch (RemoteException failure) {
                    remoteUnlockedState.set(null);
                    resultLatch.countDown();
                }
            }

            @Override
            public void onServiceDisconnected(ComponentName name) {
                remoteMessenger.set(null);
            }
        };

        boolean bound = false;
        try {
            assertTrue("A test PIN must be durably stored before probing the fresh process",
                    SecurityManager.setLockCredential(context, SecurityManager.MODE_PIN, "4286"));
            assertTrue("The test process should have an authenticated session",
                    SecurityManager.isSessionUnlocked(context));

            Intent intent = new Intent(context, AppLockSessionProbeService.class);
            bound = context.bindService(intent, connection, Context.BIND_AUTO_CREATE);
            assertTrue("Could not bind the isolated app-lock probe process", bound);
            assertTrue("The isolated process did not return its session state in time",
                    resultLatch.await(10, TimeUnit.SECONDS));
            assertNotNull("The isolated process did not return a result", remoteUnlockedState.get());
            assertEquals("A fresh Android process must start fail-closed",
                    Boolean.FALSE, remoteUnlockedState.get());
        } finally {
            if (bound) context.unbindService(connection);
            try {
                restoreCredentialPreferences(preferences, originalPreferences);
            } finally {
                // setLockCredential() clears the process-local throttle companion as well as
                // persisted counters. Restore both so this fixture cannot affect later tests.
                unlockedField.setBoolean(null, originalUnlockedState);
                failedAttemptsField.setInt(null, originalFailedAttempts);
                lockoutUntilElapsedField.setLong(null, originalLockoutUntilElapsed);
            }
        }
    }

    private static void restoreCredentialPreferences(
            SharedPreferences preferences, Map<String, ?> original) {
        SharedPreferences.Editor editor = preferences.edit().clear();
        for (Map.Entry<String, ?> entry : original.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();
            if (value instanceof String) editor.putString(key, (String) value);
            else if (value instanceof Integer) editor.putInt(key, (Integer) value);
            else if (value instanceof Boolean) editor.putBoolean(key, (Boolean) value);
            else if (value instanceof Long) editor.putLong(key, (Long) value);
            else if (value instanceof Float) editor.putFloat(key, (Float) value);
            else if (value instanceof Set) {
                @SuppressWarnings("unchecked")
                Set<String> strings = (Set<String>) value;
                editor.putStringSet(key, new java.util.HashSet<>(strings));
            } else {
                throw new AssertionError("Unexpected credential preference type for " + key);
            }
        }
        assertTrue("Credential preferences could not be restored after process-isolation test",
                editor.commit());
        assertEquals("Credential preference values changed during the test",
                original, preferences.getAll());
    }
}
