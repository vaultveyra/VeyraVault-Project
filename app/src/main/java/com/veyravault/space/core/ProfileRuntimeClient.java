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
                endpoint, ProfileRuntimeProvider.METHOD_RESOLVE_CLONE_PROFILE, null, request);
        if (response == null || !response.getBoolean("ok", false)) {
            String error = response == null ? "NO_RESPONSE" : response.getString("error", "UNKNOWN");
            throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:" + error);
        }
        ProfileSettings clone = decode(response.getBundle("clone"));
        ProfileSettings global = decode(response.getBundle("global"));
        return ProfileResolver.resolve(clone, global, ProfileRuntimeApplier.systemFallback());
    }

    private static ProfileSettings decode(Bundle values) {
        ProfileSettings settings = new ProfileSettings();
        if (values == null) return settings;
        if (values.containsKey("localeTag")) settings.localeTag = values.getString("localeTag");
        if (values.containsKey("timeZoneId")) settings.timeZoneId = values.getString("timeZoneId");
        if (values.containsKey("locationEnabled")) settings.locationEnabled = values.getBoolean("locationEnabled");
        if (values.containsKey("latitude")) settings.latitude = values.getDouble("latitude");
        if (values.containsKey("longitude")) settings.longitude = values.getDouble("longitude");
        return settings;
    }
}
