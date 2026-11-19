package com.veyravault.space.core;

import android.content.Context;
import android.content.res.Configuration;
import android.content.res.Resources;

import java.util.Locale;
import java.util.TimeZone;

/**
 * Applies user-visible locale and time-zone preferences to the current virtual app
 * process only. This class is called from the pinned engine's pre-Application callback.
 */
public final class ProfileRuntimeApplier {
    private ProfileRuntimeApplier() { }

    /** System fallback is read from system Resources, not the host app's localized Resources. */
    public static ProfileSettings systemFallback() {
        ProfileSettings fallback = new ProfileSettings();
        Locale systemLocale = Resources.getSystem().getConfiguration().locale;
        if (systemLocale != null && !systemLocale.getLanguage().isEmpty()) {
            fallback.localeTag = systemLocale.toLanguageTag();
        }
        String systemZone = TimeZone.getDefault().getID();
        if (ProfileSettings.isTimeZoneIdValid(systemZone)) {
            fallback.timeZoneId = systemZone;
        }
        return fallback;
    }

    public static void apply(Context packageContext, ProfileResolver.ResolvedProfile profile) {
        if (packageContext == null || profile == null) return;

        if (profile.localeTag != null && ProfileSettings.isLocaleTagValid(profile.localeTag)) {
            Locale locale = Locale.forLanguageTag(profile.localeTag);
            if (!locale.getLanguage().isEmpty()) {
                Locale.setDefault(locale);
                Resources resources = packageContext.getResources();
                Configuration configuration = new Configuration(resources.getConfiguration());
                configuration.setLocale(locale);
                configuration.setLayoutDirection(locale);
                resources.updateConfiguration(configuration, resources.getDisplayMetrics());
            }
        }

        if (profile.timeZoneId != null && ProfileSettings.isTimeZoneIdValid(profile.timeZoneId)) {
            TimeZone.setDefault(TimeZone.getTimeZone(profile.timeZoneId));
        }
    }
}
