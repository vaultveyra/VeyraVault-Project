package com.veyravault.space.core;

/**
 * Nullable profile values represent inheritance: null means "not overridden".
 * This model intentionally contains user-configurable settings only.
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
        if (localeTag != null && localeTag.trim().isEmpty()) return false;
        if (timeZoneId != null && timeZoneId.trim().isEmpty()) return false;
        if (latitude != null && (Double.isNaN(latitude) || Double.isInfinite(latitude)
                || latitude < -90.0 || latitude > 90.0)) return false;
        return longitude == null || (!Double.isNaN(longitude) && !Double.isInfinite(longitude)
                && longitude >= -180.0 && longitude <= 180.0);
    }
}
