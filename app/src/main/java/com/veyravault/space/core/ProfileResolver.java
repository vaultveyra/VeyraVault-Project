package com.veyravault.space.core;

/**
 * Resolves each setting independently using clone override -> global default
 * -> supplied system fallback. Invalid individual values are treated as absent;
 * they do not suppress valid values in sibling fields or lower-priority profiles.
 */
public final class ProfileResolver {
    public enum Source { CLONE, GLOBAL, SYSTEM, UNSET }

    public static final class ResolvedProfile {
        public final String localeTag;
        public final Source localeSource;
        public final String timeZoneId;
        public final Source timeZoneSource;
        public final Boolean locationEnabled;
        public final Source locationEnabledSource;
        public final Double latitude;
        public final Source latitudeSource;
        public final Double longitude;
        public final Source longitudeSource;

        private ResolvedProfile(ProfileSettings clone, ProfileSettings global,
                                ProfileSettings system) {
            Value<String> locale = choose(clone.localeTag, global.localeTag, system.localeTag,
                    ProfileSettings.isLocaleTagValid(clone.localeTag),
                    ProfileSettings.isLocaleTagValid(global.localeTag),
                    ProfileSettings.isLocaleTagValid(system.localeTag));
            localeTag = locale.value;
            localeSource = locale.source;

            Value<String> zone = choose(clone.timeZoneId, global.timeZoneId, system.timeZoneId,
                    ProfileSettings.isTimeZoneIdValid(clone.timeZoneId),
                    ProfileSettings.isTimeZoneIdValid(global.timeZoneId),
                    ProfileSettings.isTimeZoneIdValid(system.timeZoneId));
            timeZoneId = zone.value;
            timeZoneSource = zone.source;

            Value<Boolean> enabled = choose(clone.locationEnabled, global.locationEnabled,
                    system.locationEnabled, true, true, true);
            locationEnabled = enabled.value;
            locationEnabledSource = enabled.source;

            Value<Double> lat = choose(clone.latitude, global.latitude, system.latitude,
                    ProfileSettings.isLatitudeValid(clone.latitude),
                    ProfileSettings.isLatitudeValid(global.latitude),
                    ProfileSettings.isLatitudeValid(system.latitude));
            latitude = lat.value;
            latitudeSource = lat.source;

            Value<Double> lng = choose(clone.longitude, global.longitude, system.longitude,
                    ProfileSettings.isLongitudeValid(clone.longitude),
                    ProfileSettings.isLongitudeValid(global.longitude),
                    ProfileSettings.isLongitudeValid(system.longitude));
            longitude = lng.value;
            longitudeSource = lng.source;
        }
    }

    private static final class Value<T> {
        final T value;
        final Source source;
        Value(T value, Source source) { this.value = value; this.source = source; }
    }

    private ProfileResolver() { }

    public static ResolvedProfile resolve(ProfileSettings cloneOverride,
                                          ProfileSettings globalDefault,
                                          ProfileSettings systemFallback) {
        ProfileSettings clone = safe(cloneOverride);
        ProfileSettings global = safe(globalDefault);
        ProfileSettings system = safe(systemFallback);
        return new ResolvedProfile(clone, global, system);
    }

    private static ProfileSettings safe(ProfileSettings value) {
        return value == null ? new ProfileSettings() : value;
    }

    private static <T> Value<T> choose(T clone, T global, T system,
                                       boolean cloneValid, boolean globalValid,
                                       boolean systemValid) {
        if (clone != null && cloneValid) return new Value<T>(clone, Source.CLONE);
        if (global != null && globalValid) return new Value<T>(global, Source.GLOBAL);
        if (system != null && systemValid) return new Value<T>(system, Source.SYSTEM);
        return new Value<T>(null, Source.UNSET);
    }
}
