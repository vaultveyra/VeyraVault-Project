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

    @Override public boolean onCreate() { return getContext() != null; }

    @Override public Bundle call(String method, String arg, Bundle extras) {
        Bundle response = new Bundle();
        if (!METHOD_RESOLVE_CLONE_PROFILE.equals(method)) {
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
            ProfileSettings clone = ProfileStore.readCloneOverrideStrict(context, packageName, userId);
            ProfileSettings global = ProfileStore.readGlobalStrict(context);
            response.putBoolean("ok", true);
            response.putBundle("clone", encode(clone));
            response.putBundle("global", encode(global));
        } catch (Exception error) {
            response.putBoolean("ok", false);
            response.putString("error", error.getClass().getSimpleName());
        }
        return response;
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
