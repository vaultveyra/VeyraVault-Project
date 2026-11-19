package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.ProfileStore;
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
        Engine.doOnCreate(this);
        // Additive import only: preserve legacy clone preferences and session lifecycle.
        ProfileStore.migrateLegacyLocationSettings(this);
        // Register per-clone locale/time-zone application after additive profile migration.
        // The callback runs inside the virtual package/user process, not the host UI process.
        Engine.registerCloneProfileLifecycleCallback(this);
        VirtualHookManager.installProcessHooks(this);
        CloneStore.syncAllHooks(this);
    }

    public static VaultApp get() {
        return instance;
    }
}
