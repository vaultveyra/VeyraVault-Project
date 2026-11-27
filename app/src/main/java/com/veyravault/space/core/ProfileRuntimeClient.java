package com.veyravault.space.core;

import android.content.Context;
import android.net.Uri;
import android.os.Bundle;

/** Resolves a clone profile through the default-process provider, never a :pN prefs cache. */
public final class ProfileRuntimeClient {
    private ProfileRuntimeClient() { }

    public static ProfileResolver.ResolvedProfile resolve(
            Context context, String packageName, int userId) throws Exception {
        if (context == null || packageName == null || packageName.trim().isEmpty() || userId < 0) {
            throw new IllegalArgumentException("Clone identity is invalid");
        }
        Bundle request = new Bundle();
        request.putString("packageName", packageName);
        request.putInt("userId", userId);
        Uri endpoint = Uri.parse("content://" + context.getPackageName() + ".profile-runtime");
        Bundle response = context.getContentResolver().call(
                endpoint, ProfileRuntimeProvider.METHOD_RESOLVE_CLONE_PROFILE_DOCUMENT, null, request);
        if (response == null || !response.getBoolean("ok", false)) {
            String error = response == null ? "NO_RESPONSE" : response.getString("error", "UNKNOWN");
            throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:" + error);
        }
        Bundle fields = response.getBundle("fields");
        if (fields == null) throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:MISSING_FIELDS");
        return decodeResolved(fields);
    }

    private static ProfileResolver.ResolvedProfile decodeResolved(Bundle fields) {
        return ProfileResolver.fromResolvedValues(
                stringValue(fields, "localeTag"), source(fields, "localeTag"),
                stringValue(fields, "timeZoneId"), source(fields, "timeZoneId"),
                booleanValue(fields, "locationEnabled"), source(fields, "locationEnabled"),
                decimalValue(fields, "latitude"), source(fields, "latitude"),
                decimalValue(fields, "longitude"), source(fields, "longitude"));
    }

    private static Bundle field(Bundle fields, String key) {
        Bundle item = fields.getBundle(key);
        if (item == null) throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:MISSING_FIELD:" + key);
        return item;
    }

    private static Object rawValue(Bundle fields, String key) {
        Bundle item = field(fields, key);
        return item.containsKey("value") ? item.get("value") : null;
    }

    private static String stringValue(Bundle fields, String key) {
        Object value = rawValue(fields, key);
        if (value == null) return null;
        if (!(value instanceof String)) throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:INVALID_STRING:" + key);
        return (String) value;
    }

    private static Boolean booleanValue(Bundle fields, String key) {
        Object value = rawValue(fields, key);
        if (value == null) return null;
        if (!(value instanceof Boolean)) throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:INVALID_BOOLEAN:" + key);
        return (Boolean) value;
    }

    private static Double decimalValue(Bundle fields, String key) {
        Object value = rawValue(fields, key);
        if (value == null) return null;
        if (!(value instanceof Number)) throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:INVALID_NUMBER:" + key);
        return ((Number) value).doubleValue();
    }

    private static ProfileResolver.Source source(Bundle fields, String key) {
        String value = field(fields, key).getString("source");
        if (value == null) throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:MISSING_SOURCE:" + key);
        try {
            return ProfileResolver.Source.valueOf(value);
        } catch (IllegalArgumentException invalid) {
            throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:INVALID_SOURCE:" + key);
        }
    }
}
