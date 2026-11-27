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

    private ResolvedProfile(String localeTag, Source localeSource,
                            String timeZoneId, Source timeZoneSource,
                            Boolean locationEnabled, Source locationEnabledSource,
                            Double latitude, Source latitudeSource,
                            Double longitude, Source longitudeSource) {
        this.localeTag = localeTag;
        this.localeSource = safeSource(localeSource);
        this.timeZoneId = timeZoneId;
        this.timeZoneSource = safeSource(timeZoneSource);
        this.locationEnabled = locationEnabled;
        this.locationEnabledSource = safeSource(locationEnabledSource);
        this.latitude = latitude;
        this.latitudeSource = safeSource(latitudeSource);
        this.longitude = longitude;
        this.longitudeSource = safeSource(longitudeSource);
    }

    private static Source safeSource(Source source) {
        return source == null ? Source.UNSET : source;
    }

    /** Builds the legacy runtime view from the canonical typed per-field resolver. */
    public static ResolvedProfile resolveDocuments(ProfileDocument clone, ProfileDocument global) {
        java.util.Map<String, ProfileDocumentResolver.FieldResult> fields =
                ProfileDocumentResolver.resolveAll(clone, global);
        return fromDocumentResults(fields);
    }

    /** Converts a provider-returned immutable typed result map into the supported runtime view. */
    public static ResolvedProfile fromDocumentResults(
            java.util.Map<String, ProfileDocumentResolver.FieldResult> fields) {
        if (fields == null) throw new IllegalArgumentException("Resolved profile fields are required");
        ProfileDocumentResolver.FieldResult locale = required(fields, "localeTag");
        ProfileDocumentResolver.FieldResult zone = required(fields, "timeZoneId");
        ProfileDocumentResolver.FieldResult enabled = required(fields, "locationEnabled");
        ProfileDocumentResolver.FieldResult latitude = required(fields, "latitude");
        ProfileDocumentResolver.FieldResult longitude = required(fields, "longitude");
        return fromResolvedValues(
                value(locale, String.class), source(locale),
                value(zone, String.class), source(zone),
                value(enabled, Boolean.class), source(enabled),
                value(latitude, Double.class), source(latitude),
                value(longitude, Double.class), source(longitude));
    }

    private static ProfileDocumentResolver.FieldResult required(
            java.util.Map<String, ProfileDocumentResolver.FieldResult> fields, String key) {
        ProfileDocumentResolver.FieldResult result = fields.get(key);
        if (result == null) throw new IllegalStateException("Resolved profile is missing " + key);
        return result;
    }

    private static <T> T value(ProfileDocumentResolver.FieldResult result, Class<T> type) {
        if (result.value == null) return null;
        if (!type.isInstance(result.value)) {
            if (type == Double.class && result.value instanceof Number) {
                return type.cast(Double.valueOf(((Number) result.value).doubleValue()));
            }
            throw new IllegalStateException("Resolved profile value has the wrong type: " + result.key);
        }
        return type.cast(result.value);
    }

    private static Source source(ProfileDocumentResolver.FieldResult result) {
        switch (result.source) {
            case CLONE: return Source.CLONE;
            case GLOBAL: return Source.GLOBAL;
            case SAFE_DEFAULT: return Source.SAFE_DEFAULT;
            case UNSET:
            default: return Source.UNSET;
        }
    }

    /** Constructs an immutable supported-field snapshot decoded from the trusted provider. */
    public static ResolvedProfile fromResolvedValues(
            String localeTag, Source localeSource,
            String timeZoneId, Source timeZoneSource,
            Boolean locationEnabled, Source locationEnabledSource,
            Double latitude, Source latitudeSource,
            Double longitude, Source longitudeSource) {
        return new ResolvedProfile(localeTag, localeSource, timeZoneId, timeZoneSource,
                locationEnabled, locationEnabledSource, latitude, latitudeSource,
                longitude, longitudeSource);
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
