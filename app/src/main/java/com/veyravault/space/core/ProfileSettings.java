package com.veyravault.space.core;

import java.util.Locale;
import java.util.TimeZone;

/**
 * Nullable profile values represent inheritance: null means "not overridden".
 * Validation is field-scoped so one invalid field cannot suppress valid siblings.
 */
public final class ProfileSettings {
    public String localeTag;
    public String timeZoneId;
    public Boolean locationEnabled;
    public Double latitude;
    public Double longitude;

    public ProfileSettings copy() {
        ProfileSettings copy = new ProfileSettings();
        copy.localeTag = localeTag;
        copy.timeZoneId = timeZoneId;
        copy.locationEnabled = locationEnabled;
        copy.latitude = latitude;
        copy.longitude = longitude;
        return copy;
    }

    public boolean hasAnyOverride() {
        return localeTag != null || timeZoneId != null || locationEnabled != null
                || latitude != null || longitude != null;
    }

    public boolean isValid() {
        return isLocaleTagValid(localeTag) && isTimeZoneIdValid(timeZoneId)
                && isLatitudeValid(latitude) && isLongitudeValid(longitude);
    }

    public static boolean isLocaleTagValid(String value) {
        if (value == null) return true;
        if (value.trim().isEmpty()) return false;
        try {
            return !new Locale.Builder().setLanguageTag(value).build().getLanguage().isEmpty();
        } catch (RuntimeException invalidTag) {
            return false;
        }
    }

    public static boolean isTimeZoneIdValid(String value) {
        if (value == null) return true;
        if (value.trim().isEmpty()) return false;
        if ("UTC".equals(value) || "GMT".equals(value)) return true;
        return value.equals(TimeZone.getTimeZone(value).getID());
    }

    public static boolean isLatitudeValid(Double value) {
        return value == null || (!Double.isNaN(value) && !Double.isInfinite(value)
                && value >= -90.0 && value <= 90.0);
    }

    public static boolean isLongitudeValid(Double value) {
        return value == null || (!Double.isNaN(value) && !Double.isInfinite(value)
                && value >= -180.0 && value <= 180.0);
    }
}
