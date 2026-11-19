package com.veyravault.space.core;

import android.app.ActivityManager;
import android.app.Application;
import android.content.Context;
import android.os.Build;
import android.os.Process;

import java.util.List;

/** Process-name helper compatible with the app's minSdk 21. */
public final class ProcessUtils {
    private ProcessUtils() { }

    public static String currentProcessName(Context context) {
        if (Build.VERSION.SDK_INT >= 28) {
            String name = Application.getProcessName();
            if (name != null && !name.trim().isEmpty()) return name;
        }
        if (context == null) return null;
        Object service = context.getSystemService(Context.ACTIVITY_SERVICE);
        if (!(service instanceof ActivityManager)) return null;
        List<ActivityManager.RunningAppProcessInfo> processes =
                ((ActivityManager) service).getRunningAppProcesses();
        if (processes == null) return null;
        int pid = Process.myPid();
        for (ActivityManager.RunningAppProcessInfo process : processes) {
            if (process != null && process.pid == pid) return process.processName;
        }
        return null;
    }

    /** Returns false when the process name cannot be established; migration then fails closed. */
    public static boolean isMainProcess(Context context) {
        if (context == null) return false;
        String name = currentProcessName(context);
        return name != null && context.getPackageName().equals(name);
    }
}
