package com.veyravault.space.core;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Process;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Method;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.Enumeration;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * Read-only preflight for apps already installed on the host device.
 *
 * It only reads PackageManager metadata and APK ZIP entry names. It does not
 * install, launch, uninstall, clear, or modify a target app or Clone.
 */
public final class NativeAbiPreflight {
    public static final class Result {
        private final String packageName;
        private final String packageFingerprint;
        private final NativeAbiPolicy.Result policyResult;

        private Result(String packageName, String packageFingerprint,
                       NativeAbiPolicy.Result policyResult) {
            this.packageName = packageName;
            this.packageFingerprint = packageFingerprint;
            this.policyResult = policyResult;
        }

        public boolean isAllowed() {
            return policyResult != null && policyResult.isAllowed();
        }

        public NativeAbiPolicy.Decision getDecision() {
            return policyResult == null
                    ? NativeAbiPolicy.Decision.UNKNOWN_APK_METADATA
                    : policyResult.getDecision();
        }

        public String getDiagnosticCode() {
            return policyResult == null
                    ? "NATIVE_ABI_PREFLIGHT_UNKNOWN_APK_METADATA"
                    : policyResult.getDiagnosticCode();
        }

        public String getUserMessage(boolean persian) {
            return policyResult == null
                    ? NativeAbiPolicy.unknownResult().getUserMessage(persian)
                    : policyResult.getUserMessage(persian);
        }

        /**
         * Re-check PackageManager identity and APK file stamps immediately before
         * Engine installation. A package update between preflight and install fails closed.
         */
        public boolean matchesInstalledPackage(Context context, String requestedPackageName) {
            if (!isAllowed() || context == null || packageName == null
                    || !packageName.equals(requestedPackageName) || packageFingerprint == null) {
                return false;
            }
            try {
                ApplicationInfo info = getApplicationInfo(context.getPackageManager(), packageName);
                return packageFingerprint.equals(fingerprint(info));
            } catch (Exception failure) {
                return false;
            }
        }
    }

    private NativeAbiPreflight() { }

    public static Result inspectInstalledPackage(Context context, String packageName) {
        Context app = context == null ? null : context.getApplicationContext();
        if (app == null) app = context;
        if (app == null || packageName == null || packageName.trim().isEmpty())
            return unknown(packageName, null);

        // Host Engine compatibility applies even when the target APK is pure Java.
        NativeAbiPolicy.Result hostCompatibility = HostCpuCompatibility.initialize();
        if (!hostCompatibility.isAllowed())
            return new Result(packageName, null, hostCompatibility);

        try {
            ApplicationInfo info = getApplicationInfo(app.getPackageManager(), packageName);
            if (info == null || info.sourceDir == null || info.sourceDir.trim().isEmpty())
                return unknown(packageName, null);

            String packageFingerprint = fingerprint(info);
            String[] splitPaths = info.splitSourceDirs;
            int splitCount = splitPaths == null ? 0 : splitPaths.length;
            String primaryAbi = Build.CPU_ABI;
            NativeAbiPolicy.HostBitness bitness = resolveHostBitness(primaryAbi);

            // The pinned Engine package-name installer passes only sourceDir. Do not
            // inspect one split and then pretend the Engine will receive all splits.
            if (splitCount > 0) {
                NativeAbiPolicy.Result decision = NativeAbiPolicy.evaluate(
                        Collections.<String>emptySet(), splitCount, bitness, primaryAbi, true);
                return new Result(packageName, packageFingerprint, decision);
            }

            Set<String> nativeAbis = scanBaseApk(info.sourceDir);
            NativeAbiPolicy.Result decision = NativeAbiPolicy.evaluate(
                    nativeAbis, 0, bitness, primaryAbi, true);
            return new Result(packageName, packageFingerprint, decision);
        } catch (Exception failure) {
            return unknown(packageName, null);
        }
    }

    private static Result unknown(String packageName, String fingerprint) {
        NativeAbiPolicy.Result decision = NativeAbiPolicy.evaluate(
                null, 0, NativeAbiPolicy.HostBitness.UNKNOWN, null, false);
        return new Result(packageName, fingerprint, decision);
    }

    @SuppressWarnings("deprecation")
    private static ApplicationInfo getApplicationInfo(
            PackageManager packageManager, String packageName)
            throws PackageManager.NameNotFoundException {
        if (Build.VERSION.SDK_INT >= 33) {
            return packageManager.getApplicationInfo(
                    packageName, PackageManager.ApplicationInfoFlags.of(0));
        }
        return packageManager.getApplicationInfo(packageName, 0);
    }

    static NativeAbiPolicy.HostBitness resolveHostBitness(String primaryAbi) {
        if (Build.VERSION.SDK_INT >= 23) {
            return Process.is64Bit()
                    ? NativeAbiPolicy.HostBitness.BIT_64
                    : NativeAbiPolicy.HostBitness.BIT_32;
        }

        // Android 5.x does not expose Process.is64Bit(). Try the runtime's own
        // bitness signal first; on older releases where it is unavailable, use
        // the device's primary ABI as the compatibility fallback.
        Boolean runtimeBitness = queryLegacyRuntimeBitness();
        if (runtimeBitness != null) {
            return runtimeBitness
                    ? NativeAbiPolicy.HostBitness.BIT_64
                    : NativeAbiPolicy.HostBitness.BIT_32;
        }
        return NativeAbiPolicy.bitnessForAbi(primaryAbi);
    }

    private static Boolean queryLegacyRuntimeBitness() {
        try {
            Class<?> runtimeClass = Class.forName("dalvik.system.VMRuntime");
            Method getRuntime = runtimeClass.getDeclaredMethod("getRuntime");
            getRuntime.setAccessible(true);
            Object runtime = getRuntime.invoke(null);
            Method is64Bit = runtimeClass.getDeclaredMethod("is64Bit");
            is64Bit.setAccessible(true);
            Object value = is64Bit.invoke(runtime);
            return value instanceof Boolean ? (Boolean) value : null;
        } catch (Throwable unavailable) {
            return null;
        }
    }

    private static Set<String> scanBaseApk(String sourcePath) throws IOException {
        if (sourcePath == null || sourcePath.trim().isEmpty())
            throw new IOException("Base APK source path is unavailable");

        Set<String> abis = new LinkedHashSet<String>();
        try (ZipFile archive = new ZipFile(sourcePath)) {
            Enumeration<? extends ZipEntry> entries = archive.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (entry.isDirectory()) continue;
                String name = entry.getName();
                if (!name.startsWith("lib/") || !name.endsWith(".so")) continue;
                String[] parts = name.split("/");
                if (parts.length == 3 && "lib".equals(parts[0]) && !parts[1].trim().isEmpty()) {
                    abis.add(parts[1]);
                }
            }
        }
        return abis;
    }

    private static String fingerprint(ApplicationInfo info) {
        if (info == null || info.sourceDir == null) return null;
        StringBuilder value = new StringBuilder();
        appendFileStamp(value, info.sourceDir);
        String[] splits = info.splitSourceDirs;
        if (splits != null) {
            for (String split : splits) appendFileStamp(value, split);
        }
        return value.toString();
    }

    private static void appendFileStamp(StringBuilder value, String path) {
        if (value.length() > 0) value.append('|');
        value.append(path == null ? "" : path);
        if (path == null) return;
        File file = new File(path);
        value.append('#').append(file.length()).append('#').append(file.lastModified());
    }
}
