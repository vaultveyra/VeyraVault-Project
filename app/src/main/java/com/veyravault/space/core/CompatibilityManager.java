package com.veyravault.space.core;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Build;
import android.webkit.WebView;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Read-only, app-scoped compatibility diagnostics.
 * This class does not change device settings, permissions, network routing or clone state.
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

    private CompatibilityManager() {}

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

        if (Build.VERSION.SDK_INT >= 26) {
            try {
                PackageInfo webView = WebView.getCurrentWebViewPackage();
                if (webView != null) {
                    String version = webView.versionName == null ? "version unavailable" : webView.versionName;
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

        try {
            PackageInfo packageInfo;
            if (Build.VERSION.SDK_INT >= 33) {
                packageInfo = app.getPackageManager().getPackageInfo(
                        app.getPackageName(), PackageManager.PackageInfoFlags.of(
                                PackageManager.GET_PERMISSIONS));
            } else {
                //noinspection deprecation
                packageInfo = app.getPackageManager().getPackageInfo(
                        app.getPackageName(), PackageManager.GET_PERMISSIONS);
            }
            int requested = packageInfo.requestedPermissions == null
                    ? 0 : packageInfo.requestedPermissions.length;
            items.add(new CheckItem("permissions", Status.INFO,
                    requested + " permissions declared by the host application; this is not a runtime-grant audit"));
        } catch (PackageManager.NameNotFoundException error) {
            items.add(new CheckItem("permissions", Status.WARNING,
                    "Could not inspect the host application's declared permissions"));
        }

        items.add(new CheckItem("engine",
                Engine.getCore() != null ? Status.OK : Status.WARNING,
                Engine.getCore() != null
                        ? "Virtualization engine core is discoverable"
                        : "Virtualization engine core was not discoverable"));

        return Collections.unmodifiableList(items);
    }
}
