package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.LocaleHelper;
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
        VirtualHookManager.installProcessHooks(this);
        CloneStore.syncAllHooks(this);
    }

    public static VaultApp get() {
        return instance;
    }
}
