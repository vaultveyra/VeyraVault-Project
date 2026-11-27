package com.veyravault.space.core;

import android.content.Context;
import android.util.Log;

import top.niunaijun.blackbox.app.configuration.AppLifecycleCallback;

/**
 * Runs inside each BlackBox virtual package/user process at the Engine's verified
 * Application lifecycle boundaries. Profile data is read-only here; writes stay in
 * the host repository. Trace records contain only bounded technical metadata.
 */
public final class CloneProfileLifecycleCallback extends AppLifecycleCallback {
    private static final String TAG = "VeyraCloneProfile";
    private final Context appContext;

    public CloneProfileLifecycleCallback(Context context) {
        Context application = context == null ? null : context.getApplicationContext();
        this.appContext = application == null ? context : application;
    }

    private static String statusSummary(ProfileRuntimeClient.ResolvedDocument document) {
        int applied = 0, stored = 0, unsupported = 0, notTested = 0, failed = 0, notApplicable = 0;
        for (ProfileRuntimeClient.ResolvedField field : document.fields().values()) {
            switch (field.status) {
                case APPLIED: applied++; break;
                case STORED_ONLY: stored++; break;
                case UNSUPPORTED: unsupported++; break;
                case NOT_TESTED: notTested++; break;
                case FAILED: failed++; break;
                case NOT_APPLICABLE: notApplicable++; break;
                default: notTested++; break;
            }
        }
        return "revision_" + document.revision + "_fields_" + document.fields().size()
                + "_applied_" + applied + "_stored_" + stored + "_unsupported_" + unsupported
                + "_not_tested_" + notTested + "_failed_" + failed + "_not_applicable_" + notApplicable;
    }

    private boolean isTargetProcess(String packageName, int userId) {
        return appContext != null && packageName != null && !packageName.trim().isEmpty()
                && !packageName.equals(appContext.getPackageName()) && userId >= 0;
    }

    @Override
    public void beforeCreateApplication(String packageName, String processName,
                                        Context packageContext, int userId) {
        if (!isTargetProcess(packageName, userId) || packageContext == null) return;

        CloneRuntimeTrace.record(CloneRuntimeTrace.Event.VIRTUAL_PROCESS_BEFORE_APP_CREATE,
                packageName, processName, userId, "callback_entered");

        // Locale.setDefault and TimeZone.setDefault are process-global. Never execute them
        // in VeyraVault's main host process; only a pinned BlackBox host:pN worker may bind
        // a virtual package/user and receive these process-scoped settings.
        String hostProcessName = null;
        try {
            hostProcessName = ProcessUtils.currentProcessName(appContext);
        } catch (RuntimeException ignored) { }
        if (!ProcessUtils.isBlackBoxWorkerProcess(hostProcessName, appContext.getPackageName())) {
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.PROFILE_PROCESS_BOUNDARY_REJECTED,
                    packageName, processName, userId,
                    hostProcessName == null ? "host_process_unknown" : "not_blackbox_worker");
            Log.w(TAG, "Clone profile application rejected outside a BlackBox host worker for "
                    + packageName + "#" + userId);
            return;
        }
        if (!packageName.equals(packageContext.getPackageName())) {
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.PROFILE_PROCESS_BOUNDARY_REJECTED,
                    packageName, processName, userId, "target_context_mismatch");
            Log.w(TAG, "Clone profile application rejected because target Context identity mismatched for "
                    + packageName + "#" + userId);
            return;
        }

        try {
            // Never expose a previously bound Clone while this target process is being prepared.
            // The host main process has already been excluded by the worker-process gate above.
            ProfileRuntimeApplier.applySafeDefaults(packageContext);
            ProfileRuntimeClient.ResolvedDocument document =
                    ProfileRuntimeClient.resolveDocument(appContext, packageName, userId);
            ProfileResolver.ResolvedProfile resolved = document.toRuntimeProfile();
            ProfileRuntimeApplier.RuntimeApplyResult verification =
                    ProfileRuntimeApplier.applyAndVerify(packageContext, packageName, resolved);
            document = document.withRuntimeVerification(verification);
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.PROFILE_DOCUMENT_RESOLVED,
                    packageName, processName, userId, statusSummary(document));
            String verificationOutcome = "locale_" + verification.localeStatus.name()
                    + "_timezone_" + verification.timeZoneStatus.name()
                    + "_context_" + (verification.targetIdentityMatches ? "MATCH" : "MISMATCH");
            CloneRuntimeTrace.record(verification.isFullyVerified()
                            ? CloneRuntimeTrace.Event.PROFILE_READBACK_VERIFIED
                            : CloneRuntimeTrace.Event.PROFILE_READBACK_FAILED,
                    packageName, processName, userId, verificationOutcome);
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.PROFILE_APPLY_RETURNED,
                    packageName, processName, userId,
                    verification.isFullyVerified() ? "readback_verified" : "readback_incomplete");
            if (verification.isFullyVerified()) {
                Log.i(TAG, "Clone locale/time-zone readback verified before Application creation: "
                        + packageName + "#" + userId
                        + " localeSource=" + resolved.localeSource
                        + " timeZoneSource=" + resolved.timeZoneSource);
            } else {
                Log.w(TAG, "Clone locale/time-zone readback did not verify for "
                        + packageName + "#" + userId + " (" + verificationOutcome + ")");
            }
        } catch (Exception error) {
            // A malformed profile must not crash the target app or expose host/previous Clone
            // values. Keep the deterministic isolated defaults already applied above.
            CloneRuntimeTrace.record(CloneRuntimeTrace.Event.PROFILE_FALLBACK,
                    packageName, processName, userId, error.getClass().getSimpleName());
            ProfileRuntimeApplier.applySafeDefaults(packageContext);
            Log.w(TAG, "Clone profile could not be resolved; deterministic isolated defaults applied for "
                    + packageName + "#" + userId + " (" + error.getClass().getSimpleName() + ")");
        }
    }

    @Override
    public void beforeApplicationOnCreate(String packageName, String processName,
                                          android.app.Application application, int userId) {
        if (!isTargetProcess(packageName, userId)) return;
        CloneRuntimeTrace.record(CloneRuntimeTrace.Event.TARGET_APPLICATION_ONCREATE_BEGIN,
                packageName, processName, userId, "entered");
    }

    @Override
    public void afterApplicationOnCreate(String packageName, String processName,
                                         android.app.Application application, int userId) {
        if (!isTargetProcess(packageName, userId)) return;
        CloneRuntimeTrace.record(CloneRuntimeTrace.Event.TARGET_APPLICATION_ONCREATE_COMPLETE,
                packageName, processName, userId, "returned");
    }
}
