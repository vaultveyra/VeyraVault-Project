package com.veyravault.space.core;

import android.os.Build;
import com.veyravault.space.BuildConfig;

/** Startup gate for the pinned Engine host-native ABI requirements. */
public final class HostCpuCompatibility {
    private static volatile NativeAbiPolicy.Result cachedResult;

    private HostCpuCompatibility() { }

    public static NativeAbiPolicy.Result initialize() {
        NativeAbiPolicy.Result current = cachedResult;
        if (current != null) return current;
        synchronized (HostCpuCompatibility.class) {
            current = cachedResult;
            if (current != null) return current;

            if (BuildConfig.DEBUG) {
                // Debug instrumentation omits the runtime Engine native module.
                cachedResult = NativeAbiPolicy.resultFor(NativeAbiPolicy.Decision.ALLOW_PURE_JAVA);
                return cachedResult;
            }

            String primaryAbi = Build.CPU_ABI;
            int neonStatus = NativeNeonProbe.UNKNOWN;
            if ("armeabi-v7a".equalsIgnoreCase(primaryAbi)) {
                // Probe the actual 32-bit execution mode even on an arm64-capable handset.
                neonStatus = NativeNeonProbe.detect();
            }

            cachedResult = NativeAbiPolicy.evaluateHostCpu(primaryAbi, neonStatus);
            return cachedResult;
        }
    }

    public static boolean isEngineSupported() {
        return initialize().isAllowed();
    }
}
