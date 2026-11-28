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
    // Deterministic isolated defaults: never expose the host phone's locale/time zone
    // to a virtual app when neither its Clone profile nor Global profile defines a value.
    private static final String SAFE_DEFAULT_LOCALE_TAG = "en-US";
    private static final String SAFE_DEFAULT_TIME_ZONE_ID = "UTC";

    private static volatile String systemLocaleTag;
    private static volatile String systemTimeZoneId;
    private static volatile boolean lastAppliedSystemLocale = true;
    private static volatile boolean lastAppliedSystemTimeZone = true;
    private static boolean receiverRegistered;

    private ProfileRuntimeApplier() { }

    /** Readback evidence gathered in the same virtual package process that applied the profile. */
    public static final class RuntimeApplyResult {
        public final String targetPackageName;
        public final boolean targetIdentityMatches;
        public final String expectedLocaleTag;
        public final String observedDefaultLocaleTag;
        public final String observedResourceLocaleTag;
        public final String expectedTimeZoneId;
        public final String observedTimeZoneId;
        public final ProfileFieldRegistry.ApplyStatus localeStatus;
        public final ProfileFieldRegistry.ApplyStatus timeZoneStatus;

        private RuntimeApplyResult(String targetPackageName, boolean targetIdentityMatches,
                                   String expectedLocaleTag, String observedDefaultLocaleTag,
                                   String observedResourceLocaleTag, String expectedTimeZoneId,
                                   String observedTimeZoneId,
                                   ProfileFieldRegistry.ApplyStatus localeStatus,
                                   ProfileFieldRegistry.ApplyStatus timeZoneStatus) {
            this.targetPackageName = targetPackageName;
            this.targetIdentityMatches = targetIdentityMatches;
            this.expectedLocaleTag = expectedLocaleTag;
            this.observedDefaultLocaleTag = observedDefaultLocaleTag;
            this.observedResourceLocaleTag = observedResourceLocaleTag;
            this.expectedTimeZoneId = expectedTimeZoneId;
            this.observedTimeZoneId = observedTimeZoneId;
            this.localeStatus = localeStatus;
            this.timeZoneStatus = timeZoneStatus;
        }

        public boolean isFullyVerified() {
            return targetIdentityMatches
                    && localeStatus == ProfileFieldRegistry.ApplyStatus.APPLIED
                    && timeZoneStatus == ProfileFieldRegistry.ApplyStatus.APPLIED;
        }
    }

    private static String localeTag(Locale locale) {
        if (locale == null || locale.getLanguage() == null || locale.getLanguage().isEmpty()) return null;
        return locale.toLanguageTag();
    }

    private static String readResourceLocaleTag(Context packageContext) {
        if (packageContext == null) return null;
        Configuration configuration = packageContext.getResources().getConfiguration();
        return configuration == null ? null : localeTag(configuration.locale);
    }

    /**
     * Applies and verifies supported process-scoped fields inside the supplied target package
     * Context. A field is APPLIED only when its value is read back and matches the request.
     * Callers must establish safe isolated defaults before resolving/calling this method.
     */
    public static RuntimeApplyResult applyAndVerify(Context packageContext,
                                                    String expectedPackageName,
                                                    ProfileResolver.ResolvedProfile profile) {
        String actualPackageName = null;
        try {
            if (packageContext != null) actualPackageName = packageContext.getPackageName();
        } catch (RuntimeException ignored) { }
        boolean identityMatches = packageContext != null
                && expectedPackageName != null && !expectedPackageName.trim().isEmpty()
                && expectedPackageName.equals(actualPackageName);

        String expectedLocale = profile != null && ProfileSettings.isLocaleTagValid(profile.localeTag)
                ? localeTag(Locale.forLanguageTag(profile.localeTag)) : null;
        String expectedZone = profile != null && ProfileSettings.isTimeZoneIdValid(profile.timeZoneId)
                ? profile.timeZoneId : null;

        if (!identityMatches) {
            return new RuntimeApplyResult(actualPackageName, false, expectedLocale,
                    safeDefaultLocaleTag(), safeResourceLocaleTag(packageContext), expectedZone,
                    safeDefaultTimeZoneId(), statusFor(false, expectedLocale),
                    statusFor(false, expectedZone));
        }

        try {
            apply(packageContext, profile);
        } catch (RuntimeException ignored) {
            // The readback below is authoritative per field; a partial apply must not be
            // mistaken for success merely because the method was entered.
        }

        String observedDefaultLocale = safeDefaultLocaleTag();
        String observedResourceLocale = safeResourceLocaleTag(packageContext);
        String observedZone = safeDefaultTimeZoneId();
        boolean localeMatches = expectedLocale != null
                && expectedLocale.equals(observedDefaultLocale)
                && expectedLocale.equals(observedResourceLocale);
        boolean zoneMatches = expectedZone != null && expectedZone.equals(observedZone);

        return new RuntimeApplyResult(actualPackageName, true, expectedLocale,
                observedDefaultLocale, observedResourceLocale, expectedZone, observedZone,
                statusFor(localeMatches, expectedLocale), statusFor(zoneMatches, expectedZone));
    }

    private static ProfileFieldRegistry.ApplyStatus statusFor(boolean matches, String expected) {
        if (expected == null) return ProfileFieldRegistry.ApplyStatus.NOT_TESTED;
        return matches ? ProfileFieldRegistry.ApplyStatus.APPLIED
                : ProfileFieldRegistry.ApplyStatus.FAILED;
    }

    private static String safeDefaultLocaleTag() {
        try { return localeTag(Locale.getDefault()); }
        catch (RuntimeException ignored) { return null; }
    }

    private static String safeResourceLocaleTag(Context packageContext) {
        try { return readResourceLocaleTag(packageContext); }
        catch (RuntimeException ignored) { return null; }
    }

    private static String safeDefaultTimeZoneId() {
        try {
            TimeZone zone = TimeZone.getDefault();
            return zone == null ? null : zone.getID();
        } catch (RuntimeException ignored) { return null; }
    }

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
                        if (zone != null && ProfileSettings.isTimeZoneIdValid(zone)) {
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

    /**
     * Returns deterministic isolated defaults, not values read from the host phone.
     * The host baseline is retained only internally so a reused virtual process can be
     * reset between package/user binds; it is never selected as a target app profile.
     */
    public static synchronized ProfileSettings systemFallback() {
        ProfileSettings fallback = new ProfileSettings();
        fallback.localeTag = SAFE_DEFAULT_LOCALE_TAG;
        fallback.timeZoneId = SAFE_DEFAULT_TIME_ZONE_ID;
        // Safe location fallback: never enable location without an explicit clone/global choice.
        fallback.locationEnabled = Boolean.FALSE;
        return fallback;
    }

    /**
     * Fail-closed target-process fallback used when profile IPC or validation fails.
     * Do not restore host-derived defaults into a target app after a profile error.
     */
    public static synchronized void applySafeDefaults(Context packageContext) {
        Locale locale = Locale.forLanguageTag(SAFE_DEFAULT_LOCALE_TAG);
        Locale.setDefault(locale);
        TimeZone.setDefault(TimeZone.getTimeZone(SAFE_DEFAULT_TIME_ZONE_ID));
        lastAppliedSystemLocale = false;
        lastAppliedSystemTimeZone = false;
        if (packageContext == null) return;
        Resources resources = packageContext.getResources();
        Configuration configuration = new Configuration(resources.getConfiguration());
        configuration.setLocale(locale);
        configuration.setLayoutDirection(locale);
        resources.updateConfiguration(configuration, resources.getDisplayMetrics());
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
                // Even SYSTEM means the deterministic isolated default, never the host locale.
                lastAppliedSystemLocale = false;
            }
        }

        if (profile.timeZoneId != null && ProfileSettings.isTimeZoneIdValid(profile.timeZoneId)) {
            TimeZone.setDefault(TimeZone.getTimeZone(profile.timeZoneId));
            // Never follow host time-zone broadcasts after binding a virtual app profile.
            lastAppliedSystemTimeZone = false;
        }
    }
}
