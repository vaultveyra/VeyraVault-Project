package com.veyravault.space.core;

/** Separate baseline CPU probe; never loads the NEON-enabled Engine library. */
public final class NativeNeonProbe {
    public static final int SUPPORTED = 1;
    public static final int UNSUPPORTED = 0;
    public static final int UNKNOWN = -1;
    private static final int NOT_INITIALIZED = Integer.MIN_VALUE;
    private static volatile int cachedStatus = NOT_INITIALIZED;

    private NativeNeonProbe() { }

    public static int detect() {
        int current = cachedStatus;
        if (current != NOT_INITIALIZED) return current;
        synchronized (NativeNeonProbe.class) {
            current = cachedStatus;
            if (current != NOT_INITIALIZED) return current;
            try {
                System.loadLibrary("veyra_neon_probe");
                int result = nativeProbe();
                cachedStatus = (result == SUPPORTED || result == UNSUPPORTED) ? result : UNKNOWN;
            } catch (LinkageError | SecurityException unavailable) {
                cachedStatus = UNKNOWN;
            }
            return cachedStatus;
        }
    }

    private static native int nativeProbe();
}
