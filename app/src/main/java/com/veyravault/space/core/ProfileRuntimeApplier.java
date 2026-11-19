package com.veyravault.space.core;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.os.Build;

import java.util.Locale;
import java.util.TimeZone;

/**
 * Applies user-visible locale and time-zone preferences to the current virtual app process.
 * A clean system baseline is captured before the first virtual app starts and restored before
 * every subsequent package/user bind, preventing one clone from leaking defaults into another.
 */
public final class ProfileRuntimeApplier {
    private static volatile String systemLocaleTag;
    private static volatile String systemTimeZoneId;
    private static volatile boolean lastAppliedSystemLocale = true;
    private static volatile boolean lastAppliedSystemTimeZone = true;
    private static boolean receiverRegistered;

    private ProfileRuntimeApplier() { }

    public static synchronized void initializeSystemFallback(Context context) {
        if (systemLocaleTag == null) systemLocaleTag = readSystemLocaleTag();
        if (systemTimeZoneId == null) {
            String zone = TimeZone.getDefault().getID();
            if (ProfileSettings.isTimeZoneIdValid(zone)) systemTimeZoneId = zone;
        }
        if (context == null || receiverRegistered) return;

        final Context app = context.getApplicationContext();
        BroadcastReceiver receiver = new BroadcastReceiver() {
            @Override public void onReceive(Context ignored, Intent intent) {
                if (intent == null) return;
                synchronized (ProfileRuntimeApplier.class) {
                    if (Intent.ACTION_TIMEZONE_CHANGED.equals(intent.getAction())) {
                        String zone = intent.getStringExtra(Intent.EXTRA_TIMEZONE);
                        if (ProfileSettings.isTimeZoneIdValid(zone)) {
                            systemTimeZoneId = zone;
                            if (lastAppliedSystemTimeZone) {
                                TimeZone.setDefault(TimeZone.getTimeZone(zone));
                            }
                        }
                    } else if (Intent.ACTION_LOCALE_CHANGED.equals(intent.getAction())) {
                        String locale = readSystemLocaleTag();
                        if (ProfileSettings.isLocaleTagValid(locale) && locale != null) {
                            systemLocaleTag = locale;
                            if (lastAppliedSystemLocale) {
                                Locale.setDefault(Locale.forLanguageTag(locale));
                            }
                        }
                    }
                }
            }
        };
        IntentFilter filter = new IntentFilter();
        filter.addAction(Intent.ACTION_TIMEZONE_CHANGED);
        filter.addAction(Intent.ACTION_LOCALE_CHANGED);
        if (Build.VERSION.SDK_INT >= 33) {
            app.registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            app.registerReceiver(receiver, filter);
        }
        receiverRegistered = true;
    }

    private static String readSystemLocaleTag() {
        Locale locale = Resources.getSystem().getConfiguration().locale;
        if (locale == null || locale.getLanguage() == null || locale.getLanguage().isEmpty()) return null;
        return locale.toLanguageTag();
    }

    /** System fallback is stable across virtual package/user launches in this host process. */
    public static synchronized ProfileSettings systemFallback() {
        initializeSystemFallback(null);
        ProfileSettings fallback = new ProfileSettings();
        fallback.localeTag = systemLocaleTag;
        fallback.timeZoneId = systemTimeZoneId;
        // Safe location fallback: never enable location without an explicit clone/global choice.
        fallback.locationEnabled = Boolean.FALSE;
        return fallback;
    }

    /** Restore process-global defaults before reading/applying the next virtual app profile. */
    public static synchronized void restoreSystemDefaults() {
        if (systemLocaleTag != null && ProfileSettings.isLocaleTagValid(systemLocaleTag)) {
            Locale.setDefault(Locale.forLanguageTag(systemLocaleTag));
        }
        if (systemTimeZoneId != null && ProfileSettings.isTimeZoneIdValid(systemTimeZoneId)) {
            TimeZone.setDefault(TimeZone.getTimeZone(systemTimeZoneId));
        }
        lastAppliedSystemLocale = true;
        lastAppliedSystemTimeZone = true;
    }

    public static void restoreSystemDefaults(Context packageContext) {
        restoreSystemDefaults();
        if (packageContext == null || systemLocaleTag == null
                || !ProfileSettings.isLocaleTagValid(systemLocaleTag)) return;
        Locale locale = Locale.forLanguageTag(systemLocaleTag);
        Resources resources = packageContext.getResources();
        Configuration configuration = new Configuration(resources.getConfiguration());
        configuration.setLocale(locale);
        configuration.setLayoutDirection(locale);
        resources.updateConfiguration(configuration, resources.getDisplayMetrics());
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
                lastAppliedSystemLocale = profile.localeSource == ProfileResolver.Source.SYSTEM;
            }
        }

        if (profile.timeZoneId != null && ProfileSettings.isTimeZoneIdValid(profile.timeZoneId)) {
            TimeZone.setDefault(TimeZone.getTimeZone(profile.timeZoneId));
            lastAppliedSystemTimeZone = profile.timeZoneSource == ProfileResolver.Source.SYSTEM;
        }
    }
}
