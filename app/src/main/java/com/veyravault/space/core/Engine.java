package com.veyravault.space.core;

import android.app.Application;
import android.content.Context;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

public class Engine {

    public enum CloneInstallState {
        INSTALLED,
        ABSENT,
        UNKNOWN
    }

    static CloneInstallState classifyInstalledQueryResult(Boolean installed) {
        if (installed == null) return CloneInstallState.UNKNOWN;
        return installed ? CloneInstallState.INSTALLED : CloneInstallState.ABSENT;
    }

    private static final String[] CORE_CLASSES = {
        "top.niunaijun.blackbox.BlackBoxCore",
        "com.vcore.BlackBoxCore"
    };

    public static Object getCore() {
        for (String cn : CORE_CLASSES) {
            try {
                Class<?> cls = Class.forName(cn);
                Method get = cls.getDeclaredMethod("get");
                return get.invoke(null);
            } catch (Throwable ignored) {}
        }
        return null;
    }

    public static void doAttachBaseContext(Application app, final Context base) {
        try {
            Object core = getCore();
            if (core == null) return;
            for (Method m : core.getClass().getMethods()) {
                if (m.getName().equals("doAttachBaseContext") && m.getParameterTypes().length == 2) {
                    Object clientCfg = buildClientConfig(base);
                    if (clientCfg != null) {
                        m.invoke(core, base, clientCfg);
                        return;
                    }
                } else if (m.getName().equals("doAttachBaseContext") && m.getParameterTypes().length == 1) {
                    m.invoke(core, base);
                    return;
                }
            }
        } catch (Throwable ignored) {}
    }

    private static Object buildClientConfig(final Context ctx) {
        try {
            return new top.niunaijun.blackbox.app.configuration.ClientConfiguration() {
                @Override
                public String getHostPackageName() {
                    return ctx.getPackageName();
                }

                // Disable upstream automatic crash-log uploads by leaving no destination configured.
                @Override
                public String getLogSenderChatId() {
                    return null;
                }
            };
        } catch (Throwable t) {
            return null;
        }
    }

    public static void doOnCreate(Application app) {
        try {
            Object core = getCore();
            if (core == null) return;
            for (Method m : core.getClass().getMethods()) {
                if ((m.getName().equals("doCreate") || m.getName().equals("onCreate"))
                        && m.getParameterTypes().length == 0) {
                    m.invoke(core);
                    return;
                }
            }
        } catch (Throwable ignored) {}
    }

    private static volatile boolean profileLifecycleCallbackRegistered;
    private static volatile String profileLifecycleDiagnostic = "NOT_REGISTERED";

    /**
     * Register a callback in each BlackBox host process. The pinned engine invokes
     * beforeCreateApplication inside the package/user-scoped virtual process, before
     * the target Application is instantiated.
     */
    private static void recordLifecycleCallbackRegistration(
            Context context, CloneRuntimeTrace.Event event, String outcome) {
        String hostPackage = null;
        String processName = null;
        if (context != null) {
            hostPackage = context.getPackageName();
            try {
                processName = ProcessUtils.currentProcessName(context);
            } catch (Throwable ignored) {
                // Process identity is diagnostic-only; registration must not depend on it.
            }
        }
        CloneRuntimeTrace.record(event, hostPackage, processName, -1, outcome);
    }

    public static boolean registerCloneProfileLifecycleCallback(Context context) {
        if (context == null) {
            profileLifecycleDiagnostic = "INVALID_CONTEXT";
            recordLifecycleCallbackRegistration(null,
                    CloneRuntimeTrace.Event.ENGINE_LIFECYCLE_CALLBACK_REGISTRATION_FAILED,
                    "invalid_context");
            return false;
        }
        if (profileLifecycleCallbackRegistered) {
            recordLifecycleCallbackRegistration(context,
                    CloneRuntimeTrace.Event.ENGINE_LIFECYCLE_CALLBACK_REGISTERED,
                    "already_registered");
            return true;
        }
        synchronized (Engine.class) {
            if (profileLifecycleCallbackRegistered) {
                recordLifecycleCallbackRegistration(context,
                        CloneRuntimeTrace.Event.ENGINE_LIFECYCLE_CALLBACK_REGISTERED,
                        "already_registered");
                return true;
            }
            Object core = getCore();
            if (core == null) {
                profileLifecycleDiagnostic = "ENGINE_UNAVAILABLE";
                recordLifecycleCallbackRegistration(context,
                        CloneRuntimeTrace.Event.ENGINE_LIFECYCLE_CALLBACK_REGISTRATION_FAILED,
                        "engine_unavailable");
                return false;
            }
            try {
                Class<?> callbackBase = Class.forName(
                        "top.niunaijun.blackbox.app.configuration.AppLifecycleCallback");
                Class<?> callbackImpl = Class.forName(
                        "com.veyravault.space.core.CloneProfileLifecycleCallback");
                Object callback = callbackImpl.getConstructor(Context.class)
                        .newInstance(context.getApplicationContext());
                Method add = core.getClass().getMethod("addAppLifecycleCallback", callbackBase);
                add.invoke(core, callback);
                profileLifecycleCallbackRegistered = true;
                profileLifecycleDiagnostic = "REGISTERED";
                recordLifecycleCallbackRegistration(context,
                        CloneRuntimeTrace.Event.ENGINE_LIFECYCLE_CALLBACK_REGISTERED,
                        "registered");
                return true;
            } catch (Throwable error) {
                profileLifecycleDiagnostic = "REGISTRATION_FAILED: "
                        + error.getClass().getSimpleName();
                recordLifecycleCallbackRegistration(context,
                        CloneRuntimeTrace.Event.ENGINE_LIFECYCLE_CALLBACK_REGISTRATION_FAILED,
                        error.getClass().getSimpleName());
                return false;
            }
        }
    }

    public static String getProfileLifecycleDiagnostic() {
        return profileLifecycleDiagnostic;
    }

    private static volatile String lastInstallDiagnostic = "No install attempt has been made.";

    /** A bounded, non-sensitive explanation of the most recent install failure. */
    public static String getLastInstallDiagnostic() {
        return lastInstallDiagnostic;
    }

    private static String safeEngineMessage(String message) {
        if (message == null) return "";
        StringBuilder safe = new StringBuilder();
        for (int i = 0; i < message.length() && safe.length() < 180; i++) {
            char c = message.charAt(i);
            if (c >= 32 && c != 127) safe.append(c == '\t' ? ' ' : c);
        }
        return safe.toString().trim();
    }

    public static boolean installPackageAsUser(
            Context context, String pkg, int userId, NativeAbiPreflight.Result preflight) {
        if (context == null || pkg == null || pkg.trim().isEmpty() || userId < 0 || preflight == null) {
            lastInstallDiagnostic = "NATIVE_ABI_PREFLIGHT_INVALID_INPUT";
            return false;
        }
        if (!preflight.isAllowed()) {
            lastInstallDiagnostic = "NATIVE_ABI_PREFLIGHT_BLOCKED:" + preflight.getDiagnosticCode();
            return false;
        }
        if (!preflight.matchesInstalledPackage(context, pkg)) {
            lastInstallDiagnostic = "NATIVE_ABI_PREFLIGHT_PACKAGE_CHANGED";
            return false;
        }

        lastInstallDiagnostic = "INSTALL_STARTED";
        try {
            Object core = getCore();
            if (core == null) {
                lastInstallDiagnostic = "ENGINE_UNAVAILABLE: core could not be resolved";
                return false;
            }
            Method m = core.getClass().getMethod("installPackageAsUser", String.class, int.class);
            Object res = m.invoke(core, pkg, userId);
            if (res == null) {
                lastInstallDiagnostic = "ENGINE_INVALID_RESULT: install returned null";
                return false;
            }
            Field success = res.getClass().getField("success");
            boolean installed = success.getBoolean(res);
            if (installed) {
                lastInstallDiagnostic = "INSTALL_SUCCEEDED";
                return true;
            }
            String detail = "";
            try {
                Field message = res.getClass().getField("msg");
                Object value = message.get(res);
                if (value instanceof String) detail = safeEngineMessage((String) value);
            } catch (Throwable ignored) {
                // Some engine versions do not expose a diagnostic message.
            }
            lastInstallDiagnostic = detail.isEmpty()
                    ? "ENGINE_REJECTED_INSTALL: engine reported success=false"
                    : "ENGINE_REJECTED_INSTALL: " + detail;
            return false;
        } catch (Throwable error) {
            Throwable cause = error.getCause();
            String type = error.getClass().getSimpleName();
            if (cause != null) type += " (cause: " + cause.getClass().getSimpleName() + ")";
            lastInstallDiagnostic = "ENGINE_INSTALL_EXCEPTION: " + type;
            return false;
        }
    }

    private static Boolean queryInstalledAsUser(String pkg, int userId) {
        try {
            Object core = getCore();
            if (core == null) return null;
            Method m = core.getClass().getMethod("isInstalled", String.class, int.class);
            Object result = m.invoke(core, pkg, userId);
            return result instanceof Boolean ? (Boolean) result : null;
        } catch (Throwable ignored) {
            return null;
        }
    }

    /** Returns a tri-state Engine result; reflection/query failures remain UNKNOWN. */
    public static CloneInstallState getCloneInstallState(String pkg, int userId) {
        if (pkg == null || pkg.trim().isEmpty() || userId < 0)
            return CloneInstallState.UNKNOWN;
        return classifyInstalledQueryResult(queryInstalledAsUser(pkg, userId));
    }

    /** True only when the engine explicitly reports that this virtual package is absent. */
    public static boolean isCloneConfirmedAbsent(String pkg, int userId) {
        return getCloneInstallState(pkg, userId) == CloneInstallState.ABSENT;
    }

    public static final class CloneLaunchResult {
        public final boolean launched;
        public final String failure;
        public final VirtualHookManager.LocationApplyResult locationResult;

        private CloneLaunchResult(boolean launched, String failure,
                VirtualHookManager.LocationApplyResult locationResult) {
            this.launched = launched;
            this.failure = failure;
            this.locationResult = locationResult;
        }
    }

    /**
     * Performs the complete launch sequence. Call from a worker thread: installation checks,
     * profile/engine hook IPC, launch reflection and active-launch persistence are synchronous.
     * Hook outcome is reported separately and does not change the historical launch policy.
     */
    public static CloneLaunchResult launchCloneDetailed(Context ctx, CloneStore.CloneEntry entry) {
        if (ctx == null || entry == null || entry.packageName == null
                || entry.packageName.trim().isEmpty() || entry.userId < 0) {
            return new CloneLaunchResult(false, "INVALID_CLONE_IDENTITY", null);
        }
        CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_LAUNCH_REQUEST,
                entry.packageName, null, entry.userId, "requested");

        // A failed/indeterminate Engine query is not proof that the package is absent.
        // Never start a second installation attempt unless absence is explicitly confirmed.
        CloneInstallState installState = getCloneInstallState(entry.packageName, entry.userId);
        if (installState == null || installState == CloneInstallState.UNKNOWN) {
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_INSTALL_STATE_UNKNOWN,
                    entry.packageName, null, entry.userId, "query_unknown");
            return new CloneLaunchResult(false, "ENGINE_INSTALL_STATE_UNKNOWN", null);
        }
        if (installState == CloneInstallState.ABSENT) {
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_INSTALL_REQUIRED,
                    entry.packageName, null, entry.userId, "confirmed_absent");
        }
        if (installState == CloneInstallState.ABSENT) {
            NativeAbiPreflight.Result preflight =
                    NativeAbiPreflight.inspectInstalledPackage(ctx, entry.packageName);
            if (!preflight.isAllowed()) {
                CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_INSTALL_FAILED,
                        entry.packageName, null, entry.userId, preflight.getDiagnosticCode());
                return new CloneLaunchResult(false,
                        "NATIVE_ABI_PREFLIGHT_BLOCKED:" + preflight.getDiagnosticCode(), null);
            }
            if (!installPackageAsUser(ctx, entry.packageName, entry.userId, preflight)) {
                CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_INSTALL_FAILED,
                        entry.packageName, null, entry.userId, "install_returned_false");
                return new CloneLaunchResult(false, "ENGINE_INSTALL_FAILED", null);
            }
        }

        // Preserve hook-before-launch ordering and make hook preparation failures observable.
        CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_HOOK_SYNC_BEGIN,
                entry.packageName, null, entry.userId, "begin");
        final VirtualHookManager.LocationApplyResult hookResult;
        try {
            hookResult = VirtualHookManager.syncCloneHooks(ctx, entry);
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_HOOK_SYNC_COMPLETE,
                    entry.packageName, null, entry.userId, "returned");
        } catch (Throwable failure) {
            String type = failure.getClass().getSimpleName();
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_HOOK_SYNC_FAILED,
                    entry.packageName, null, entry.userId, type);
            return new CloneLaunchResult(false, "ENGINE_HOOK_SYNC_EXCEPTION:" + type, null);
        }

        try {
            Object core = getCore();
            if (core == null) {
                CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_LAUNCH_REJECTED,
                        entry.packageName, null, entry.userId, "engine_unavailable");
                return new CloneLaunchResult(false, "ENGINE_UNAVAILABLE", hookResult);
            }
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_LAUNCH_CALL,
                    entry.packageName, null, entry.userId, "calling_engine");
            Method m = core.getClass().getMethod("launchApk", String.class, int.class);
            Object value = m.invoke(core, entry.packageName, entry.userId);
            if (!Boolean.TRUE.equals(value)) {
                CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_LAUNCH_REJECTED,
                        entry.packageName, null, entry.userId, "engine_returned_false");
                return new CloneLaunchResult(false, "ENGINE_REJECTED_LAUNCH", hookResult);
            }

            // Engine acceptance confirms only the launch request, not Application startup.
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_LAUNCH_ACCEPTED,
                    entry.packageName, null, entry.userId, "engine_returned_true");
            // Persist only a confirmed successful launch; failed attempts must not replace
            // the last-known successful clone in the host-side active-launch marker.
            CloneStore.recordActiveLaunch(ctx, entry);
            return new CloneLaunchResult(true, null, hookResult);
        } catch (Throwable failure) {
            String type = failure.getClass().getSimpleName();
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.ENGINE_LAUNCH_EXCEPTION,
                    entry.packageName, null, entry.userId, type);
            String detail = type;
            if (failure.getCause() != null) detail += ":" + failure.getCause().getClass().getSimpleName();
            return new CloneLaunchResult(false, "ENGINE_LAUNCH_EXCEPTION:" + detail, hookResult);
        }
    }

    /** Synchronous compatibility wrapper. UI callers should use AsyncCloneLaunchRepository. */
    public static boolean launchClone(Context ctx, CloneStore.CloneEntry entry) {
        return launchCloneDetailed(ctx, entry).launched;
    }

    /**
     * Returns true only when a supported stop method was invoked without a reflection error.
     * The pinned Engine API does not expose a verified process-termination result.
     */
    public static boolean stopClone(String pkg, int userId) {
        if (pkg == null || pkg.trim().isEmpty() || userId < 0) return false;
        try {
            Object core = getCore();
            if (core == null) return false;
            for (Method method : core.getClass().getMethods()) {
                if ((method.getName().equals("stopPackage") || method.getName().equals("killApplication"))
                        && method.getParameterTypes().length == 2
                        && method.getParameterTypes()[0] == String.class
                        && method.getParameterTypes()[1] == int.class) {
                    method.invoke(core, pkg, userId);
                    return true;
                }
            }
        } catch (Throwable ignored) {
            return false;
        }
        return false;
    }

    /**
     * Returns true only when clearPackage was invoked without a reflection error.
     * The pinned upstream API returns void and suppresses its internal file-operation result;
     * true therefore means "request dispatched", never "all data files verified deleted".
     */
    public static boolean clearCloneData(String pkg, int userId) {
        if (pkg == null || pkg.trim().isEmpty() || userId < 0) return false;
        try {
            Object core = getCore();
            if (core == null) return false;
            Method method = core.getClass().getMethod("clearPackage", String.class, int.class);
            method.invoke(core, pkg, userId);
            return true;
        } catch (Throwable ignored) {
            return false;
        }
    }

    public static boolean uninstallClone(String pkg, int userId) {
        if (pkg == null || pkg.trim().isEmpty() || userId < 0) return false;
        try {
            Object core = getCore();
            if (core == null) return false;
            Method m = core.getClass().getMethod("uninstallPackageAsUser", String.class, int.class);
            m.invoke(core, pkg, userId);
            // A successful reflection call is not enough: confirm the engine reports
            // the virtual package absent. Unknown/error state is never success.
            return Boolean.FALSE.equals(queryInstalledAsUser(pkg, userId));
        } catch (Throwable ignored) {
            return false;
        }
    }

    public static boolean isGmsInstalled(int userId) {
        return GmsSupportManager.isGmsInstalled(userId);
    }

    public static boolean setGmsEnabled(int userId, boolean enable) {
        return GmsSupportManager.setGmsEnabled(userId, enable);
    }
}
