package com.veyravault.space.core;

/** Resolves each setting independently using Clone -> Global -> Safe Isolated Default. */
public final class ProfileResolver {
    public enum Source { CLONE, GLOBAL, SAFE_DEFAULT, SYSTEM, UNSET }

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
                                ProfileSettings safeDefault) {
            Value<String> locale = choose(clone.localeTag, global.localeTag, safeDefault.localeTag,
                    ProfileSettings.isLocaleTagValid(clone.localeTag),
                    ProfileSettings.isLocaleTagValid(global.localeTag),
                    ProfileSettings.isLocaleTagValid(safeDefault.localeTag));
            localeTag = locale.value; localeSource = locale.source;
            Value<String> zone = choose(clone.timeZoneId, global.timeZoneId, safeDefault.timeZoneId,
                    ProfileSettings.isTimeZoneIdValid(clone.timeZoneId),
                    ProfileSettings.isTimeZoneIdValid(global.timeZoneId),
                    ProfileSettings.isTimeZoneIdValid(safeDefault.timeZoneId));
            timeZoneId = zone.value; timeZoneSource = zone.source;
            Value<Boolean> enabled = choose(clone.locationEnabled, global.locationEnabled,
                    safeDefault.locationEnabled, true, true, true);
            locationEnabled = enabled.value; locationEnabledSource = enabled.source;
            Value<Double> lat = choose(clone.latitude, global.latitude, safeDefault.latitude,
                    ProfileSettings.isLatitudeValid(clone.latitude),
                    ProfileSettings.isLatitudeValid(global.latitude),
                    ProfileSettings.isLatitudeValid(safeDefault.latitude));
            latitude = lat.value; latitudeSource = lat.source;
            Value<Double> lng = choose(clone.longitude, global.longitude, safeDefault.longitude,
                    ProfileSettings.isLongitudeValid(clone.longitude),
                    ProfileSettings.isLongitudeValid(global.longitude),
                    ProfileSettings.isLongitudeValid(safeDefault.longitude));
            longitude = lng.value; longitudeSource = lng.source;
        }
    }
    private static final class Value<T> {
        final T value; final Source source;
        Value(T value, Source source) { this.value = value; this.source = source; }
    }
    private ProfileResolver() { }
    public static ResolvedProfile resolve(ProfileSettings cloneOverride,
                                          ProfileSettings globalDefault,
                                          ProfileSettings safeDefault) {
        return new ResolvedProfile(safe(cloneOverride), safe(globalDefault), safe(safeDefault));
    }
    private static ProfileSettings safe(ProfileSettings value) {
        return value == null ? new ProfileSettings() : value;
    }
    private static <T> Value<T> choose(T clone, T global, T fallback,
                                       boolean cloneValid, boolean globalValid, boolean fallbackValid) {
        if (clone != null && cloneValid) return new Value<T>(clone, Source.CLONE);
        if (global != null && globalValid) return new Value<T>(global, Source.GLOBAL);
        if (fallback != null && fallbackValid) return new Value<T>(fallback, Source.SAFE_DEFAULT);
        return new Value<T>(null, Source.UNSET);
    }
}
