package com.veyravault.space;

import android.app.Application;
import android.content.Context;
import android.util.Log;

import com.veyravault.space.core.AsyncLocationHookRepository;
import com.veyravault.space.core.AppearanceManager;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.ProfileStore;
import com.veyravault.space.core.ProfileRuntimeApplier;
import com.veyravault.space.core.ProcessUtils;
import com.veyravault.space.security.AppLockLifecycleController;

public class VaultApp extends Application {
    private static final String TAG = "VeyraVault";
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
        AppearanceManager.apply(this);
        // Capture the actual system baseline before any virtual app can override process defaults.
        ProfileRuntimeApplier.initializeSystemFallback(this);
        Engine.doOnCreate(this);

        // SharedPreferences migration and bulk hook reconciliation belong to the default process.
        // Virtual :pN processes must not race writes or redundantly synchronize every clone.
        if (ProcessUtils.isMainProcess(this)) {
            // App-lock lifecycle belongs only to the main host process, never clone processes.
            AppLockLifecycleController.initialize(this);
            ProfileStore.migrateLegacyLocationSettings(this);
            AsyncLocationHookRepository.getInstance(this).syncAllCloneLocationHooks((summary, error) -> {
                if (error != null) {
                    Log.w(TAG, "Startup location hook reconciliation could not run: " + error);
                } else if (summary == null || !summary.registryReadable
                        || summary.failed > 0 || summary.unsupported > 0) {
                    Log.w(TAG, "Startup location hook reconciliation incomplete: "
                            + (summary == null ? "NO_SUMMARY" : summary.detail)
                            + (summary == null ? "" : " applied=" + summary.applied
                                    + " disabled=" + summary.disabled
                                    + " unsupported=" + summary.unsupported
                                    + " failed=" + summary.failed));
                }
            });
        }

        // Register the lifecycle callback in every BlackBox host process. Profile reads are
        // routed back to the default process through the non-exported runtime provider.
        Engine.registerCloneProfileLifecycleCallback(this);
    }

    public static VaultApp get() {
        return instance;
    }
}
