package com.veyravault.space.security;

import android.app.Service;
import android.content.Intent;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.RemoteException;

/**
 * Debug-only isolated-process probe used to verify that an unlocked host session
 * is not inherited by a freshly created Android process.
 */
public final class AppLockSessionProbeService extends Service {
    public static final int MSG_QUERY_SESSION_STATE = 1;
    public static final int MSG_SESSION_STATE_RESULT = 2;

    private final Messenger messenger = new Messenger(new Handler(Looper.getMainLooper(), message -> {
        if (message.what != MSG_QUERY_SESSION_STATE || message.replyTo == null) return false;

        Message reply = Message.obtain(null, MSG_SESSION_STATE_RESULT);
        reply.arg1 = SecurityManager.isSessionUnlocked(getApplicationContext()) ? 1 : 0;
        try {
            message.replyTo.send(reply);
        } catch (RemoteException ignored) {
            // The instrumentation client may have timed out or disconnected.
        }
        return true;
    }));

    @Override
    public IBinder onBind(Intent intent) {
        return messenger.getBinder();
    }
}
