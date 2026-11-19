package com.veyravault.space.core;

import android.content.Context;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

/**
 * Applies location profiles through the exact package/user-scoped API exposed by the
 * pinned NewBlackbox engine. Host LocationManager statics are never modified.
 */
public final class VirtualHookManager {

    public enum LocationStatus { APPLIED, DISABLED, UNSUPPORTED, FAILED }

    public static final class LocationApplyResult {
        public final LocationStatus status;
        public final String detail;
        public final ProfileResolver.Source enabledSource;
        public final ProfileResolver.Source latitudeSource;
        public final ProfileResolver.Source longitudeSource;

        private LocationApplyResult(LocationStatus status, String detail,
                                    ProfileResolver.Source enabledSource,
                                    ProfileResolver.Source latitudeSource,
                                    ProfileResolver.Source longitudeSource) {
            this.status = status;
            this.detail = detail;
            this.enabledSource = enabledSource;
            this.latitudeSource = latitudeSource;
            this.longitudeSource = longitudeSource;
        }

        public boolean isApplied() { return status == LocationStatus.APPLIED; }
        public boolean isDisabled() { return status == LocationStatus.DISABLED; }
    }

    public static final class SyncSummary {
        public final boolean registryReadable;
        public final int applied;
        public final int disabled;
        public final int unsupported;
        public final int failed;
        public final String detail;

        private SyncSummary(boolean registryReadable, int applied, int disabled,
                            int unsupported, int failed, String detail) {
            this.registryReadable = registryReadable;
            this.applied = applied;
            this.disabled = disabled;
            this.unsupported = unsupported;
            this.failed = failed;
            this.detail = detail;
        }
    }

    private static volatile LocationApplyResult lastResult =
            new LocationApplyResult(LocationStatus.UNSUPPORTED, "NOT_ATTEMPTED",
                    ProfileResolver.Source.UNSET, ProfileResolver.Source.UNSET,
                    ProfileResolver.Source.UNSET);

    private VirtualHookManager() { }

    public static LocationApplyResult getLastLocationResult() { return lastResult; }

    /** Strictly reads the clone registry and returns every per-clone hook outcome. */
    public static SyncSummary syncAllClones(Context context) {
        if (context == null) return new SyncSummary(false, 0, 0, 0, 0, "INVALID_CONTEXT");
        final java.util.List<CloneStore.CloneEntry> clones;
        try {
            clones = CloneStore.readAllStrict(context);
        } catch (Exception error) {
            return new SyncSummary(false, 0, 0, 0, 0,
                    "CLONE_REGISTRY_UNREADABLE:" + error.getClass().getSimpleName());
        }
        int applied = 0;
        int disabled = 0;
        int unsupported = 0;
        int failed = 0;
        for (CloneStore.CloneEntry clone : clones) {
            LocationApplyResult outcome = syncCloneHooks(context, clone);
            switch (outcome.status) {
                case APPLIED: applied++; break;
                case DISABLED: disabled++; break;
                case UNSUPPORTED: unsupported++; break;
                case FAILED: failed++; break;
            }
        }
        return new SyncSummary(true, applied, disabled, unsupported, failed, "COMPLETE");
    }

    public static void installProcessHooks(Context context) {
        if (context == null) return;
        CloneStore.CloneEntry last = CloneStore.getLastActiveLaunch(context);
        if (last != null) syncCloneHooks(context, last);
    }

    /**
     * Resolves each location field independently (clone -> global -> safe system fallback),
     * then applies only when the Master Mock GPS gate and the resolved profile both allow it.
     */
    public static LocationApplyResult syncCloneHooks(Context context, CloneStore.CloneEntry entry) {
        if (context == null || entry == null || entry.packageName == null
                || entry.packageName.trim().isEmpty() || entry.userId < 0) {
            return remember(result(LocationStatus.FAILED, "INVALID_CLONE_IDENTITY", null));
        }

        final boolean masterEnabled;
        final ProfileResolver.ResolvedProfile resolved;
        try {
            masterEnabled = CloneStore.readMasterMockGpsEnabledStrict(context);
            resolved = ProfileStore.resolveStrict(context, entry.packageName, entry.userId,
                    ProfileRuntimeApplier.systemFallback());
        } catch (Exception error) {
            LocationApplyResult disabled = disableEngineLocationHook(entry.packageName, entry.userId,
                    null, null, null);
            String detail = "PROFILE_RESOLUTION_FAILED:" + error.getClass().getSimpleName()
                    + "; fail-closed disable=" + disabled.status;
            return remember(result(LocationStatus.FAILED, detail, null));
        }

        if (!masterEnabled) {
            return remember(disableEngineLocationHook(entry.packageName, entry.userId,
                    resolved.locationEnabledSource, resolved.latitudeSource, resolved.longitudeSource));
        }
        if (!Boolean.TRUE.equals(resolved.locationEnabled)) {
            return remember(disableEngineLocationHook(entry.packageName, entry.userId,
                    resolved.locationEnabledSource, resolved.latitudeSource, resolved.longitudeSource));
        }
        if (resolved.latitude == null || resolved.longitude == null) {
            LocationApplyResult disabled = disableEngineLocationHook(entry.packageName, entry.userId,
                    resolved.locationEnabledSource, resolved.latitudeSource, resolved.longitudeSource);
            if (disabled.status == LocationStatus.DISABLED) {
                return remember(result(LocationStatus.FAILED,
                        "LOCATION_ENABLED_BUT_COORDINATES_MISSING; hook disabled", resolved));
            }
            return remember(disabled);
        }

        return remember(applyEngineLocationHook(entry.packageName, entry.userId,
                resolved.latitude, resolved.longitude, resolved));
    }

    private static LocationApplyResult disableEngineLocationHook(
            String packageName, int userId, ProfileResolver.Source enabledSource,
            ProfileResolver.Source latitudeSource, ProfileResolver.Source longitudeSource) {
        try {
            Object service = resolveLocationService();
            if (service == null) return result(LocationStatus.FAILED, "LOCATION_SERVICE_UNAVAILABLE",
                    enabledSource, latitudeSource, longitudeSource);
            invoke(service, "setPattern", new Class<?>[]{int.class, String.class, int.class},
                    userId, packageName, 0);
            Object pattern = invoke(service, "getPattern",
                    new Class<?>[]{int.class, String.class}, userId, packageName);
            if (!(pattern instanceof Integer) || ((Integer) pattern) != 0) {
                return result(LocationStatus.FAILED, "DISABLE_READBACK_MISMATCH",
                        enabledSource, latitudeSource, longitudeSource);
            }
            return result(LocationStatus.DISABLED, "PATTERN_CLOSED_AND_READ_BACK",
                    enabledSource, latitudeSource, longitudeSource);
        } catch (ClassNotFoundException | NoSuchMethodException unsupported) {
            return result(LocationStatus.UNSUPPORTED,
                    "PINNED_ENGINE_LOCATION_API_UNAVAILABLE:" + unsupported.getClass().getSimpleName(),
                    enabledSource, latitudeSource, longitudeSource);
        } catch (Exception failure) {
            return result(LocationStatus.FAILED,
                    "LOCATION_DISABLE_FAILED:" + rootCauseName(failure),
                    enabledSource, latitudeSource, longitudeSource);
        }
    }

    private static LocationApplyResult applyEngineLocationHook(
            String packageName, int userId, double latitude, double longitude,
            ProfileResolver.ResolvedProfile resolved) {
        try {
            Object service = resolveLocationService();
            if (service == null) return result(LocationStatus.FAILED, "LOCATION_SERVICE_UNAVAILABLE", resolved);
            Class<?> locationClass = Class.forName(
                    "top.niunaijun.blackbox.entity.location.BLocation");
            Object location = locationClass.getConstructor(double.class, double.class)
                    .newInstance(latitude, longitude);

            // Store the coordinates first; enable OWN_MODE only after setLocation returns.
            invoke(service, "setLocation",
                    new Class<?>[]{int.class, String.class, locationClass},
                    userId, packageName, location);
            invoke(service, "setPattern",
                    new Class<?>[]{int.class, String.class, int.class},
                    userId, packageName, 2);

            Object pattern = invoke(service, "getPattern",
                    new Class<?>[]{int.class, String.class}, userId, packageName);
            Object stored = invoke(service, "getLocation",
                    new Class<?>[]{int.class, String.class}, userId, packageName);
            if (!(pattern instanceof Integer) || ((Integer) pattern) != 2 || stored == null) {
                return failClosedAfterEnableFailure(packageName, userId,
                        "LOCATION_ENABLE_READBACK_MISMATCH", resolved);
            }
            double actualLat = ((Number) invoke(stored, "getLatitude", new Class<?>[0])).doubleValue();
            double actualLng = ((Number) invoke(stored, "getLongitude", new Class<?>[0])).doubleValue();
            if (Math.abs(actualLat - latitude) > 0.000001d
                    || Math.abs(actualLng - longitude) > 0.000001d) {
                return failClosedAfterEnableFailure(packageName, userId,
                        "LOCATION_COORDINATE_READBACK_MISMATCH", resolved);
            }
            return result(LocationStatus.APPLIED, "OWN_MODE_AND_COORDINATES_READ_BACK", resolved);
        } catch (ClassNotFoundException | NoSuchMethodException unsupported) {
            LocationApplyResult disabled = disableEngineLocationHook(
                    packageName, userId, resolved.locationEnabledSource,
                    resolved.latitudeSource, resolved.longitudeSource);
            return result(LocationStatus.UNSUPPORTED,
                    "PINNED_ENGINE_LOCATION_API_UNAVAILABLE:" + unsupported.getClass().getSimpleName()
                            + "; fail-closed disable=" + disabled.status, resolved);
        } catch (Exception failure) {
            // A partially configured hook is closed before returning a failure.
            LocationApplyResult disabled = disableEngineLocationHook(
                    packageName, userId, resolved.locationEnabledSource,
                    resolved.latitudeSource, resolved.longitudeSource);
            return result(LocationStatus.FAILED,
                    "LOCATION_ENABLE_FAILED:" + rootCauseName(failure)
                            + "; fail-closed disable=" + disabled.status, resolved);
        }
    }

    private static LocationApplyResult failClosedAfterEnableFailure(
            String packageName, int userId, String reason,
            ProfileResolver.ResolvedProfile resolved) {
        LocationApplyResult disabled = disableEngineLocationHook(
                packageName, userId, resolved.locationEnabledSource,
                resolved.latitudeSource, resolved.longitudeSource);
        return result(LocationStatus.FAILED,
                reason + "; fail-closed disable=" + disabled.status, resolved);
    }

    private static Object resolveLocationService() throws Exception {
        Class<?> managerClass = Class.forName(
                "top.niunaijun.blackbox.fake.frameworks.BLocationManager");
        Object manager = managerClass.getMethod("get").invoke(null);
        if (manager == null) return null;
        // getService() is public in the pinned engine's BlackManager base class.
        return managerClass.getMethod("getService").invoke(manager);
    }

    private static Object invoke(Object target, String name, Class<?>[] parameterTypes,
                                 Object... arguments) throws Exception {
        Method method = target.getClass().getMethod(name, parameterTypes);
        try {
            return method.invoke(target, arguments);
        } catch (InvocationTargetException wrapped) {
            Throwable cause = wrapped.getCause();
            if (cause instanceof Exception) throw (Exception) cause;
            throw wrapped;
        }
    }

    private static String rootCauseName(Throwable error) {
        Throwable cause = error;
        while (cause.getCause() != null && cause.getCause() != cause) cause = cause.getCause();
        return cause.getClass().getSimpleName();
    }

    private static LocationApplyResult result(LocationStatus status, String detail,
                                               ProfileResolver.ResolvedProfile resolved) {
        if (resolved == null) return result(status, detail, null, null, null);
        return result(status, detail, resolved.locationEnabledSource,
                resolved.latitudeSource, resolved.longitudeSource);
    }

    private static LocationApplyResult result(LocationStatus status, String detail,
                                               ProfileResolver.Source enabled,
                                               ProfileResolver.Source latitude,
                                               ProfileResolver.Source longitude) {
        return new LocationApplyResult(status, detail,
                enabled == null ? ProfileResolver.Source.UNSET : enabled,
                latitude == null ? ProfileResolver.Source.UNSET : latitude,
                longitude == null ? ProfileResolver.Source.UNSET : longitude);
    }

    private static LocationApplyResult remember(LocationApplyResult result) {
        lastResult = result;
        return result;
    }
}
