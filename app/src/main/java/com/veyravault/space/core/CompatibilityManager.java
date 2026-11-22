package com.veyravault.space.core;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Environment;
import android.os.Process;
import android.webkit.WebView;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * Read-only compatibility diagnostics. Host checks and Clone-scoped snapshots are
 * kept separate so host facts are never presented as proof of virtual-app behavior.
 * This class does not mutate settings, permissions, network routes, Engine packages,
 * CloneStore records or target-app data.
 */
public final class CompatibilityManager {
    public enum Status { OK, INFO, WARNING }

    public static final class CheckItem {
        public final String key;
        public final Status status;
        public final String detail;

        CheckItem(String key, Status status, String detail) {
            this.key = key;
            this.status = status;
            this.detail = detail;
        }
    }

    private static final class NativeAbiScan {
        final Set<String> baseApkAbis = new LinkedHashSet<>();
        final Set<String> splitApkAbis = new LinkedHashSet<>();
        int readableBaseApkCount;
        int readableSplitApkCount;
        int unreadableApkCount;
    }

    private CompatibilityManager() { }

    /** Existing host-only report. It does not certify a virtualized target app. */
    public static List<CheckItem> collect(Context context) {
        Context app = context.getApplicationContext();
        List<CheckItem> items = new ArrayList<>();

        items.add(new CheckItem("android", Status.INFO,
                "Android API " + Build.VERSION.SDK_INT + " ("
                        + Build.VERSION.RELEASE + ")"));

        String[] abis = Build.SUPPORTED_ABIS;
        boolean supportedAbi = false;
        StringBuilder abiText = new StringBuilder();
        if (abis != null) {
            for (String abi : abis) {
                if (abiText.length() > 0) abiText.append(", ");
                abiText.append(abi);
                if ("armeabi-v7a".equals(abi) || "arm64-v8a".equals(abi)) {
                    supportedAbi = true;
                }
            }
        }
        items.add(new CheckItem("abi", supportedAbi ? Status.OK : Status.WARNING,
                abiText.length() == 0 ? "No ABI information reported" : abiText.toString()));

        ApplicationInfo applicationInfo = app.getApplicationInfo();
        File nativeDir = applicationInfo.nativeLibraryDir == null
                ? null : new File(applicationInfo.nativeLibraryDir);
        File[] nativeFiles = nativeDir != null ? nativeDir.listFiles() : null;
        int nativeCount = 0;
        if (nativeFiles != null) {
            for (File file : nativeFiles) {
                if (file.isFile() && file.getName().endsWith(".so")) nativeCount++;
            }
        }
        items.add(new CheckItem("native", nativeCount > 0 ? Status.OK : Status.INFO,
                nativeCount + " native libraries detected in the host app directory"));

        addWebViewCheck(items);

        try {
            PackageInfo packageInfo = getPackageInfo(
                    app.getPackageManager(), app.getPackageName());
            int requested = packageInfo.requestedPermissions == null
                    ? 0 : packageInfo.requestedPermissions.length;
            items.add(new CheckItem("permissions", Status.INFO,
                    requested + " permissions declared by the host application; this is not a runtime-grant audit"));
        } catch (PackageManager.NameNotFoundException error) {
            items.add(new CheckItem("permissions", Status.WARNING,
                    "Could not inspect the host application's declared permissions"));
        }

        boolean engineAvailable = Engine.getCore() != null;
        items.add(new CheckItem("engine",
                engineAvailable ? Status.OK : Status.WARNING,
                engineAvailable
                        ? "Virtualization engine core is discoverable"
                        : "Virtualization engine core was not discoverable"));

        return Collections.unmodifiableList(items);
    }

    /**
     * Collects a redacted, read-only snapshot for one existing Clone.
     * It reads host-installed APK metadata and the virtual Engine's state for the
     * exact package/user pair. It never launches, installs, clears or rewrites the Clone.
     */
    public static List<CheckItem> collectClone(Context context, CloneStore.CloneEntry clone) {
        List<CheckItem> items = new ArrayList<>();
        if (context == null || clone == null || clone.packageName == null
                || clone.packageName.trim().isEmpty() || clone.userId < 0) {
            items.add(new CheckItem("input", Status.WARNING, "Clone identity is invalid"));
            return Collections.unmodifiableList(items);
        }

        Context app = context.getApplicationContext();
        if (app == null) app = context;
        items.add(new CheckItem("android", Status.INFO,
                "Android API " + Build.VERSION.SDK_INT + " (" + Build.VERSION.RELEASE + ")"));
        items.add(new CheckItem("host_abi", Status.INFO,
                "Host process bitness: " + hostProcessBitness()
                        + "; supported ABIs: " + join(Build.SUPPORTED_ABIS)));

        boolean engineAvailable = Engine.getCore() != null;
        items.add(new CheckItem("engine_core",
                engineAvailable ? Status.OK : Status.WARNING,
                engineAvailable ? "Engine core is discoverable in the host process"
                        : "Engine core could not be resolved"));

        Engine.CloneInstallState installState =
                Engine.getCloneInstallState(clone.packageName, clone.userId);
        switch (installState) {
            case INSTALLED:
                items.add(new CheckItem("clone_install_state", Status.OK,
                        "Engine explicitly reports this package installed for the selected Clone"));
                break;
            case ABSENT:
                items.add(new CheckItem("clone_install_state", Status.WARNING,
                        "Engine explicitly reports this package absent for the selected Clone"));
                break;
            default:
                items.add(new CheckItem("clone_install_state", Status.WARNING,
                        "Engine could not determine the package install state; UNKNOWN is not treated as ABSENT"));
                break;
        }

        GmsSupportManager.GmsState gmsState = GmsSupportManager.getGmsState(clone.userId);
        switch (gmsState) {
            case INSTALLED:
                items.add(new CheckItem("gms", Status.OK,
                        "Engine reports GMS installed for this virtual user"));
                break;
            case ABSENT:
                items.add(new CheckItem("gms", Status.INFO,
                        "Engine reports GMS absent for this virtual user"));
                break;
            default:
                items.add(new CheckItem("gms", Status.WARNING,
                        "GMS state is unknown; the Engine query may be unavailable"));
                break;
        }

        try {
            PackageInfo packageInfo = getPackageInfo(app.getPackageManager(), clone.packageName);
            ApplicationInfo info = packageInfo.applicationInfo;
            String versionName = packageInfo.versionName == null
                    ? "unavailable" : packageInfo.versionName;
            long versionCode = Build.VERSION.SDK_INT >= 28
                    ? packageInfo.getLongVersionCode() : packageInfo.versionCode;
            String[] splits = info == null ? null : info.splitSourceDirs;
            int splitCount = splits == null ? 0 : splits.length;

            NativeAbiScan scan = new NativeAbiScan();
            if (info != null && info.sourceDir != null && !info.sourceDir.trim().isEmpty()) {
                scanNativeAbis(info.sourceDir, scan.baseApkAbis, scan, true);
            }
            if (splits != null) {
                for (String split : splits) {
                    if (split != null && !split.trim().isEmpty()) {
                        scanNativeAbis(split, scan.splitApkAbis, scan, false);
                    }
                }
            }
            items.add(new CheckItem("host_package", Status.OK,
                    "Host-installed package version " + versionName
                            + " (versionCode " + versionCode + "); base APK plus "
                            + splitCount + " split APK(s); this is host source metadata, not virtual Clone version readback"));
            if (splitCount > 0) {
                items.add(new CheckItem("split_apk_risk", Status.WARNING,
                        "Split APKs are present. The audited pinned Engine install entry point passes only ApplicationInfo.sourceDir; splitSourceDirs are not passed to its installer. Split-dependent resources or native libraries therefore require device validation."));
            } else {
                items.add(new CheckItem("split_apk_risk", Status.INFO,
                        "No split APKs were reported by the host PackageManager"));
            }

            String nativeDetail = "Base APK native ABI directories: "
                    + (scan.baseApkAbis.isEmpty() ? "none" : join(scan.baseApkAbis.toArray(new String[0])))
                    + "; split APK native ABI directories: "
                    + (scan.splitApkAbis.isEmpty() ? "none" : join(scan.splitApkAbis.toArray(new String[0])))
                    + "; readable base APKs: " + scan.readableBaseApkCount
                    + "; readable split APKs: " + scan.readableSplitApkCount
                    + "; unreadable APK archives: " + scan.unreadableApkCount;
            items.add(new CheckItem("package_native_abis",
                    scan.unreadableApkCount > 0 ? Status.WARNING : Status.INFO,
                    nativeDetail));
        } catch (PackageManager.NameNotFoundException missing) {
            items.add(new CheckItem("host_package", Status.WARNING,
                    "The package could not be read from the host PackageManager"));
        } catch (Throwable failure) {
            items.add(new CheckItem("host_package", Status.WARNING,
                    "Package metadata inspection failed: " + failure.getClass().getSimpleName()));
        }

        addWebViewCheck(items);
        if (Build.VERSION.SDK_INT >= 30) {
            boolean allFiles = Environment.isExternalStorageManager();
            items.add(new CheckItem("all_files_access",
                    allFiles ? Status.OK : Status.WARNING,
                    allFiles
                            ? "Host app currently has Android all-files access"
                            : "Host app does not currently have Android all-files access; the pinned Engine warns that some target file operations may fail"));
        } else {
            items.add(new CheckItem("all_files_access", Status.INFO,
                    "Android all-files access special access is not applicable on this API level"));
        }

        items.add(new CheckItem("launch_observation", Status.INFO,
                "This report did not launch the target app. It does not establish whether the Clone process starts, completes Application.onCreate, or remains alive."));
        return Collections.unmodifiableList(items);
    }

    /** Formats only the bounded CheckItem values above; no account or app-private data is read. */
    public static String formatCloneReport(Context context, CloneStore.CloneEntry clone) {
        if (clone == null || clone.packageName == null) {
            return "VeyraVault Clone diagnostic\nClone identity is unavailable.\n";
        }
        StringBuilder report = new StringBuilder();
        report.append("VeyraVault read-only Clone compatibility snapshot\n");
        report.append("Package: ").append(clone.packageName).append('\n');
        for (CheckItem item : collectClone(context, clone)) {
            report.append('\n').append(item.key).append(" [")
                    .append(item.status.name()).append("]\n")
                    .append(item.detail).append('\n');
        }
        report.append("\nPrivacy boundary: this report reads package metadata and Engine status only. ");
        report.append("It does not read account credentials, messages, photos, app-private files, ");
        report.append("precise location or session contents; it does not change permissions, settings, ");
        report.append("network routes or Clone data. Target-app startup is not tested by this snapshot.\n");
        return report.toString();
    }

    private static String hostProcessBitness() {
        return Build.VERSION.SDK_INT >= 23
                ? (Process.is64Bit() ? "64-bit" : "32-bit")
                : "unavailable on Android API below 23";
    }

    private static String join(String[] values) {
        if (values == null || values.length == 0) return "unavailable";
        StringBuilder output = new StringBuilder();
        for (String value : values) {
            if (value == null || value.trim().isEmpty()) continue;
            if (output.length() > 0) output.append(", ");
            output.append(value);
        }
        return output.length() == 0 ? "unavailable" : output.toString();
    }

    private static PackageInfo getPackageInfo(PackageManager packageManager, String packageName)
            throws PackageManager.NameNotFoundException {
        if (Build.VERSION.SDK_INT >= 33) {
            return packageManager.getPackageInfo(packageName,
                    PackageManager.PackageInfoFlags.of(PackageManager.GET_PERMISSIONS));
        }
        //noinspection deprecation
        return packageManager.getPackageInfo(packageName, PackageManager.GET_PERMISSIONS);
    }

    private static void scanNativeAbis(String path, Set<String> destination,
                                       NativeAbiScan result, boolean baseApk) {
        try (ZipFile archive = new ZipFile(path)) {
            if (baseApk) result.readableBaseApkCount++;
            else result.readableSplitApkCount++;
            Enumeration<? extends ZipEntry> entries = archive.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                if (!entry.isDirectory() && name.startsWith("lib/") && name.endsWith(".so")) {
                    String[] parts = name.split("/");
                    if (parts.length >= 3 && !parts[1].trim().isEmpty()) destination.add(parts[1]);
                }
            }
        } catch (IOException unreadable) {
            result.unreadableApkCount++;
        }
    }

    private static void addWebViewCheck(List<CheckItem> items) {
        if (Build.VERSION.SDK_INT >= 26) {
            try {
                PackageInfo webView = WebView.getCurrentWebViewPackage();
                if (webView != null) {
                    String version = webView.versionName == null
                            ? "version unavailable" : webView.versionName;
                    items.add(new CheckItem("webview", Status.OK,
                            webView.packageName + " (" + version + ")"));
                } else {
                    items.add(new CheckItem("webview", Status.WARNING,
                            "No current WebView provider was reported by Android"));
                }
            } catch (Throwable error) {
                items.add(new CheckItem("webview", Status.WARNING,
                        "WebView provider query failed: " + error.getClass().getSimpleName()));
            }
        } else {
            items.add(new CheckItem("webview", Status.INFO,
                    "Provider version query requires Android 8.0 or later"));
        }
    }
}
