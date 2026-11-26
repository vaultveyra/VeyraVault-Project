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

    @Override public boolean onCreate() { return getContext() != null; }

    @Override public Bundle call(String method, String arg, Bundle extras) {
        Bundle response = new Bundle();
        boolean legacyRequest = METHOD_RESOLVE_CLONE_PROFILE.equals(method);
        boolean documentRequest = METHOD_RESOLVE_CLONE_PROFILE_DOCUMENT.equals(method);
        if (!legacyRequest && !documentRequest) {
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
                    item.putString("source", field.source.name());
                    item.putString("status", field.status.name());
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

    /** Add legacy supported values only where the typed document has no field override. */
    static ProfileDocument mergeLegacyFields(ProfileDocument document, ProfileSettings legacy) {
        ProfileDocument merged = document == null ? new ProfileDocument() : document.copy();
        if (legacy == null) return merged;
        putIfMissing(merged, "localeTag", legacy.localeTag);
        putIfMissing(merged, "timeZoneId", legacy.timeZoneId);
        putIfMissing(merged, "locationEnabled", legacy.locationEnabled);
        putIfMissing(merged, "latitude", legacy.latitude);
        putIfMissing(merged, "longitude", legacy.longitude);
        return merged;
    }

    private static void putIfMissing(ProfileDocument target, String key, Object value) {
        if (value != null && !target.contains(key) && target.put(key, value)) {
            // Value was validated and copied into the merged in-memory snapshot.
        }
    }

    /** Overlay typed document values onto a legacy runtime payload without changing storage. */
    static ProfileSettings mergeDocumentFields(ProfileSettings legacy, ProfileDocument document) {
        ProfileSettings merged = legacy == null ? new ProfileSettings() : legacy.copy();
        if (document == null) return merged;
        Object value = document.get("localeTag");
        if (value instanceof String) merged.localeTag = (String) value;
        value = document.get("timeZoneId");
        if (value instanceof String) merged.timeZoneId = (String) value;
        value = document.get("locationEnabled");
        if (value instanceof Boolean) merged.locationEnabled = (Boolean) value;
        value = document.get("latitude");
        if (value instanceof Number) merged.latitude = ((Number) value).doubleValue();
        value = document.get("longitude");
        if (value instanceof Number) merged.longitude = ((Number) value).doubleValue();
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
