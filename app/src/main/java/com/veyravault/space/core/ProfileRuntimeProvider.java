package com.veyravault.space.core;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.Binder;
import android.os.Bundle;
import android.os.Process;

/**
 * Same-UID IPC endpoint hosted in the default app process, which is the authoritative
 * SharedPreferences profile reader/writer. Virtual :pN processes must not read their own
 * potentially stale SharedPreferences caches.
 */
public final class ProfileRuntimeProvider extends ContentProvider {
    public static final String METHOD_RESOLVE_CLONE_PROFILE = "resolveCloneProfile";
    public static final String METHOD_RESOLVE_CLONE_PROFILE_DOCUMENT = "resolveCloneProfileDocument";
    public static final String METHOD_RECORD_CLONE_PROFILE_STATUS = "recordCloneProfileStatus";

    @Override public boolean onCreate() { return getContext() != null; }

    @Override public Bundle call(String method, String arg, Bundle extras) {
        Bundle response = new Bundle();
        boolean legacyRequest = METHOD_RESOLVE_CLONE_PROFILE.equals(method);
        boolean documentRequest = METHOD_RESOLVE_CLONE_PROFILE_DOCUMENT.equals(method);
        boolean statusRequest = METHOD_RECORD_CLONE_PROFILE_STATUS.equals(method);
        if (!legacyRequest && !documentRequest && !statusRequest) {
            response.putBoolean("ok", false);
            response.putString("error", "UNSUPPORTED_METHOD");
            return response;
        }
        if (Binder.getCallingUid() != Process.myUid()) {
            response.putBoolean("ok", false);
            response.putString("error", "CALLER_NOT_ALLOWED");
            return response;
        }
        Context context = getContext();
        if (context == null || extras == null) {
            response.putBoolean("ok", false);
            response.putString("error", "PROVIDER_UNAVAILABLE");
            return response;
        }
        String packageName = extras.getString("packageName");
        int userId = extras.getInt("userId", -1);
        try {
            if (packageName == null || packageName.trim().isEmpty() || userId < 0) {
                response.putBoolean("ok", false);
                response.putString("error", "INVALID_CLONE_IDENTITY");
                return response;
            }
            if (statusRequest) {
                String expectedProcessName = extras.getString("processName");
                if (expectedProcessName == null || expectedProcessName.trim().isEmpty()
                        || !isAuthorizedCaller(context, packageName, userId, expectedProcessName)) {
                    response.putBoolean("ok", false);
                    response.putString("error", "CALLER_CLONE_IDENTITY_MISMATCH");
                    return response;
                }
                if (!isRegisteredClone(context, packageName, userId)) {
                    response.putBoolean("ok", false);
                    response.putString("error", "CLONE_NOT_REGISTERED");
                    return response;
                }
                String profileFingerprint = extras.getString("profileFingerprint");
                if (!ProfileRuntimeFingerprint.isValid(profileFingerprint)) {
                    response.putBoolean("ok", false);
                    response.putString("error", "INVALID_PROFILE_FINGERPRINT");
                    return response;
                }
                Bundle statusBundle = extras.getBundle("statuses");
                if (statusBundle == null) {
                    response.putBoolean("ok", false);
                    response.putString("error", "MISSING_STATUS_BUNDLE");
                    return response;
                }
                java.util.Map<String, ProfileFieldRegistry.ApplyStatus> statuses =
                        new java.util.LinkedHashMap<>();
                for (String key : statusBundle.keySet()) {
                    String raw = statusBundle.getString(key);
                    if (raw == null) throw new IllegalArgumentException("INVALID_STATUS:" + key);
                    statuses.put(key, ProfileFieldRegistry.ApplyStatus.valueOf(raw));
                }
                boolean saved = ProfileRuntimeStatusStore.record(context, packageName, userId,
                        extras.getLong("revision", -1L), profileFingerprint,
                        extras.getString("processName"), statuses);
                response.putBoolean("ok", saved);
                if (!saved) response.putString("error", "STALE_OR_INVALID_STATUS");
                else response.putLong("revision", ProfileDocumentStore.readRevisionStrict(context));
                return response;
            }
            // The host main process is trusted internal code. A virtual worker must be
            // authenticated against the pinned Engine's PID -> ProcessRecord mapping before
            // it can select any Clone's profile, and must name a Clone still in CloneStore.
            if (!isAuthorizedCaller(context, packageName, userId, null)) {
                response.putBoolean("ok", false);
                response.putString("error", "CALLER_CLONE_IDENTITY_MISMATCH");
                return response;
            }
            if (Binder.getCallingPid() != Process.myPid()
                    && !isRegisteredClone(context, packageName, userId)) {
                response.putBoolean("ok", false);
                response.putString("error", "CLONE_NOT_REGISTERED");
                return response;
            }
            // Read both stores strictly. The five-field ProfileStore remains a live
            // compatibility source until every settings screen has moved to documents.
            ProfileSettings legacyClone = ProfileStore.readCloneOverrideStrict(context, packageName, userId);
            ProfileSettings legacyGlobal = ProfileStore.readGlobalStrict(context);
            ProfileDocument documentClone = ProfileDocumentStore.readCloneStrict(context, packageName, userId);
            ProfileDocument documentGlobal = ProfileDocumentStore.readGlobalStrict(context);

            // Explicit document values win field-by-field; missing document fields inherit
            // the previously saved legacy value. No migration write or destructive rewrite occurs.
            ProfileDocument mergedClone = mergeLegacyFields(documentClone, legacyClone);
            ProfileDocument mergedGlobal = mergeLegacyFields(documentGlobal, legacyGlobal);

            if (documentRequest) {
                java.util.Map<String, ProfileDocumentResolver.FieldResult> resolved =
                        ProfileDocumentResolver.resolveAll(mergedClone, mergedGlobal);
                Bundle fields = new Bundle();
                for (ProfileDocumentResolver.FieldResult field : resolved.values()) {
                    Bundle item = new Bundle();
                    ProfileFieldRegistry.Field definition = ProfileFieldRegistry.get(field.key);
                    if (definition == null) {
                        throw new IllegalStateException("PROFILE_REGISTRY_FIELD_MISSING:" + field.key);
                    }
                    item.putString("source", field.source.name());
                    item.putString("status", field.status.name());
                    item.putString("capability", definition.capability.name());
                    item.putString("type", definition.type.name());
                    item.putString("scope", definition.scope);
                    item.putString("label", definition.label);
                    item.putString("category", definition.category);
                    item.putString("validationRule", definition.validationRule);
                    item.putString("adapterId", definition.adapterId);
                    item.putString("apiSupport", definition.apiSupport);
                    item.putString("privacyClass", definition.privacyClass);
                    item.putBoolean("editable", definition.editable);
                    item.putString("readbackMethod", definition.readbackMethod);
                    item.putString("unsupportedReason", definition.unsupportedReason);
                    putTypedValue(item, field.value);
                    fields.putBundle(field.key, item);
                }
                response.putBoolean("ok", true);
                response.putBundle("fields", fields);
                response.putLong("revision", ProfileDocumentStore.readRevisionStrict(context));
            } else {
                // Existing ProfileRuntimeClient and lifecycle callback now receive the
                // merged supported fields without changing their established IPC contract.
                ProfileSettings clone = mergeDocumentFields(legacyClone, documentClone);
                ProfileSettings global = mergeDocumentFields(legacyGlobal, documentGlobal);
                response.putBoolean("ok", true);
                response.putBundle("clone", encode(clone));
                response.putBundle("global", encode(global));
            }
        } catch (Exception error) {
            response.putBoolean("ok", false);
            response.putString("error", error.getClass().getSimpleName());
        }
        return response;
    }

    /**
     * Resolves the authoritative five runtime fields from both typed and legacy stores.
     * This is shared by process IPC and Engine-scoped hooks so Location cannot lag behind
     * the typed profile document while older settings screens are being migrated.
     */
    static ProfileResolver.ResolvedProfile resolveMergedProfile(
            Context context, String packageName, int userId,
            ProfileSettings safeDefault) throws Exception {
        if (context == null || packageName == null || packageName.trim().isEmpty() || userId < 0) {
            throw new IllegalArgumentException("Clone identity and context are required");
        }
        ProfileSettings legacyClone = ProfileStore.readCloneOverrideStrict(context, packageName, userId);
        ProfileSettings legacyGlobal = ProfileStore.readGlobalStrict(context);
        ProfileDocument typedClone = ProfileDocumentStore.readCloneStrict(context, packageName, userId);
        ProfileDocument typedGlobal = ProfileDocumentStore.readGlobalStrict(context);
        ProfileDocument mergedClone = mergeLegacyFields(typedClone, legacyClone);
        ProfileDocument mergedGlobal = mergeLegacyFields(typedGlobal, legacyGlobal);
        // The typed resolver preserves explicit Clone SAFE_DEFAULT and INHERIT_GLOBAL
        // states. Flattening those states into nullable legacy fields would incorrectly
        // allow a Global value to override an explicit Clone Safe Default.
        return ProfileResolver.resolveDocuments(mergedClone, mergedGlobal);
    }

    /**
     * Authenticates virtual-worker IPC against the pinned Engine's live PID mapping.
     * PID comes from Binder, not caller-controlled extras. Reflection keeps the Debug
     * instrumentation APK independent from the release-only virtual Engine dependency.
     * Failure to obtain an exact ProcessRecord is a denial, never a fallback to requested IDs.
     */
    private static boolean isAuthorizedCaller(Context context, String packageName, int userId,
                                              String expectedProcessName) {
        int callingPid = Binder.getCallingPid();
        if (callingPid == Process.myPid()) {
            // Only trusted code in VeyraVault's own default process may resolve arbitrary
            // registered identities; a virtual app must always arrive through its worker PID.
            return expectedProcessName == null && ProcessUtils.isMainProcess(context);
        }
        try {
            Class<?> managerClass = Class.forName(
                    "top.niunaijun.blackbox.core.system.BProcessManagerService");
            Object manager = managerClass.getMethod("get").invoke(null);
            if (manager == null) return false;
            Object processRecord = managerClass.getMethod("findProcessByPid", int.class)
                    .invoke(manager, callingPid);
            if (processRecord == null) return false;
            Class<?> recordClass = processRecord.getClass();
            String callerPackage = (String) recordClass.getMethod("getPackageName")
                    .invoke(processRecord);
            int callerUserId = recordClass.getField("userId").getInt(processRecord);
            String callerProcessName = (String) recordClass.getField("processName")
                    .get(processRecord);
            return matchesCloneIdentity(packageName, userId, callerPackage, callerUserId,
                    expectedProcessName, callerProcessName);
        } catch (Exception unavailableOrUntrusted) {
            return false;
        }
    }

    static boolean matchesCloneIdentity(String requestedPackage, int requestedUserId,
                                         String callerPackage, int callerUserId,
                                         String expectedProcessName, String callerProcessName) {
        if (requestedPackage == null || requestedPackage.trim().isEmpty() || requestedUserId < 0
                || callerPackage == null || callerProcessName == null) return false;
        if (!requestedPackage.equals(callerPackage) || requestedUserId != callerUserId) return false;
        return expectedProcessName == null || expectedProcessName.equals(callerProcessName);
    }

    private static boolean isRegisteredClone(Context context, String packageName, int userId)
            throws Exception {
        for (CloneStore.CloneEntry entry : CloneStore.readAllStrict(context)) {
            if (entry != null && packageName.equals(entry.packageName) && userId == entry.userId) return true;
        }
        return false;
    }

    /** Add legacy supported values only where the typed document has no field override. */
    static ProfileDocument mergeLegacyFields(ProfileDocument document, ProfileSettings legacy) {
        ProfileDocument merged = document == null ? new ProfileDocument() : document.copy();
        if (legacy == null) return merged;
        putLegacyIfAbsentAndValid(merged, "localeTag", legacy.localeTag);
        putLegacyIfAbsentAndValid(merged, "timeZoneId", legacy.timeZoneId);
        putLegacyIfAbsentAndValid(merged, "locationEnabled", legacy.locationEnabled);
        putLegacyIfAbsentAndValid(merged, "latitude", legacy.latitude);
        putLegacyIfAbsentAndValid(merged, "longitude", legacy.longitude);
        return merged;
    }

    private static void putLegacyIfAbsentAndValid(ProfileDocument target, String key, Object value) {
        // Invalid typed presence intentionally suppresses same-level Legacy fallback.
        if (value != null && !target.contains(key) && !target.isInvalid(key) && !target.hasState(key) && target.put(key, value)) {
            // Value was validated and copied into the merged in-memory snapshot.
        }
    }

    /** Overlay typed document values onto a legacy runtime payload without changing storage. */
    static ProfileSettings mergeDocumentFields(ProfileSettings legacy, ProfileDocument document) {
        ProfileSettings merged = legacy == null ? new ProfileSettings() : legacy.copy();
        if (document == null) return merged;
        if (document.isInvalid("localeTag") || document.hasState("localeTag")) merged.localeTag = null;
        else {
            Object value = document.get("localeTag");
            if (value instanceof String) merged.localeTag = (String) value;
        }
        if (document.isInvalid("timeZoneId") || document.hasState("timeZoneId")) merged.timeZoneId = null;
        else {
            Object value = document.get("timeZoneId");
            if (value instanceof String) merged.timeZoneId = (String) value;
        }
        if (document.isInvalid("locationEnabled") || document.hasState("locationEnabled")) merged.locationEnabled = null;
        else {
            Object value = document.get("locationEnabled");
            if (value instanceof Boolean) merged.locationEnabled = (Boolean) value;
        }
        if (document.isInvalid("latitude") || document.hasState("latitude")) merged.latitude = null;
        else {
            Object value = document.get("latitude");
            if (value instanceof Number) merged.latitude = ((Number) value).doubleValue();
        }
        if (document.isInvalid("longitude") || document.hasState("longitude")) merged.longitude = null;
        else {
            Object value = document.get("longitude");
            if (value instanceof Number) merged.longitude = ((Number) value).doubleValue();
        }
        return merged;
    }

    private static void putTypedValue(Bundle out, Object value) {
        if (value instanceof String) out.putString("value", (String) value);
        else if (value instanceof Boolean) out.putBoolean("value", (Boolean) value);
        else if (value instanceof Integer) out.putInt("value", (Integer) value);
        else if (value instanceof Long) out.putLong("value", (Long) value);
        else if (value instanceof Number) out.putDouble("value", ((Number) value).doubleValue());
    }

    private static Bundle encode(ProfileSettings settings) {
        Bundle out = new Bundle();
        if (settings == null) return out;
        if (settings.localeTag != null) out.putString("localeTag", settings.localeTag);
        if (settings.timeZoneId != null) out.putString("timeZoneId", settings.timeZoneId);
        if (settings.locationEnabled != null) out.putBoolean("locationEnabled", settings.locationEnabled);
        if (settings.latitude != null) out.putDouble("latitude", settings.latitude);
        if (settings.longitude != null) out.putDouble("longitude", settings.longitude);
        return out;
    }

    @Override public Cursor query(Uri uri, String[] projection, String selection,
                                  String[] selectionArgs, String sortOrder) { return null; }
    @Override public String getType(Uri uri) { return null; }
    @Override public Uri insert(Uri uri, ContentValues values) { return null; }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) { return 0; }
    @Override public int update(Uri uri, ContentValues values, String selection,
                                String[] selectionArgs) { return 0; }
}
