package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.ProfileStore;
import com.veyravault.space.core.ProfileRuntimeApplier;
import com.veyravault.space.core.ProcessUtils;
import com.veyravault.space.core.VirtualHookManager;

public class VaultApp extends Application {
    private static VaultApp instance;

    @Override
    protected void attachBaseContext(Context base) {
        Context localized = LocaleHelper.applyLocale(base);
        super.attachBaseContext(localized);
        instance = this;
        Engine.doAttachBaseContext(this, localized);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        LocaleHelper.applyLocale(this);
        // Capture the actual system baseline before any virtual app can override process defaults.
        ProfileRuntimeApplier.initializeSystemFallback(this);
        Engine.doOnCreate(this);
        // SharedPreferences profile migration is authoritative in the default app process only.
        // BlackBox :pN processes are readers and must not race writes through independent caches.
        if (ProcessUtils.isMainProcess(this)) {
            ProfileStore.migrateLegacyLocationSettings(this);
        }
        // Register the lifecycle callback in every BlackBox host process. Profile reads are
        // routed back to the default process through the non-exported runtime provider.
        // The callback runs inside the virtual package/user process, not the host UI process.
        Engine.registerCloneProfileLifecycleCallback(this);
        VirtualHookManager.installProcessHooks(this);
        CloneStore.syncAllHooks(this);
    }

    public static VaultApp get() {
        return instance;
    }
}
