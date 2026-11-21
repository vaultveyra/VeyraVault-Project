import com.veyravault.space.core.ProfileSettings;
import com.veyravault.space.core.ProfileResolver;

public final class ProfileResolverContractTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        ProfileSettings system = new ProfileSettings();
        system.localeTag = "en-US";
        system.timeZoneId = "America/New_York";
        system.locationEnabled = false;
        system.latitude = 10.0;
        system.longitude = 20.0;

        ProfileSettings global = new ProfileSettings();
        global.localeTag = "fa-IR";
        global.locationEnabled = true;
        global.latitude = 30.0;

        ProfileSettings clone = new ProfileSettings();
        clone.timeZoneId = "Asia/Tehran";
        clone.locationEnabled = false;
        clone.longitude = 40.0;

        ProfileResolver.ResolvedProfile result = ProfileResolver.resolve(clone, global, system);
        check("fa-IR".equals(result.localeTag), "locale should inherit global");
        check(result.localeSource == ProfileResolver.Source.GLOBAL, "locale source should be global");
        check("Asia/Tehran".equals(result.timeZoneId), "timezone should use clone override");
        check(result.timeZoneSource == ProfileResolver.Source.CLONE, "timezone source should be clone");
        check(Boolean.FALSE.equals(result.locationEnabled), "explicit false must override true");
        check(result.locationEnabledSource == ProfileResolver.Source.CLONE, "false override source");
        check(Double.valueOf(30.0).equals(result.latitude), "latitude should inherit global");
        check(result.latitudeSource == ProfileResolver.Source.GLOBAL, "latitude source should be global");
        check(Double.valueOf(40.0).equals(result.longitude), "longitude should use clone override");
        check(result.longitudeSource == ProfileResolver.Source.CLONE, "longitude source should be clone");

        ProfileResolver.ResolvedProfile fallback = ProfileResolver.resolve(
                new ProfileSettings(), new ProfileSettings(), system);
        check("en-US".equals(fallback.localeTag), "system fallback should be used");
        check(fallback.localeSource == ProfileResolver.Source.SYSTEM, "fallback source should be system");

        ProfileResolver.ResolvedProfile unset = ProfileResolver.resolve(null, null, null);
        check(unset.localeTag == null && unset.localeSource == ProfileResolver.Source.UNSET,
                "missing values should remain explicitly unset");
        check(unset.locationEnabled == null, "unset must not be coerced to false");

        check(!newInvalidSettings().isValid(), "out-of-range coordinates must be rejected");
        check(!newNaNLatitude().isValid(), "NaN latitude must be rejected");
        check(!newInfiniteLongitude().isValid(), "infinite longitude must be rejected");

        // Invalid clone values fall back field-by-field without suppressing valid siblings.
        ProfileSettings invalidClone = new ProfileSettings();
        invalidClone.localeTag = "not a valid tag";
        invalidClone.timeZoneId = "Mars/Olympus";
        invalidClone.latitude = 999.0;
        invalidClone.longitude = 45.0;
        invalidClone.locationEnabled = false;
        ProfileSettings validGlobal = new ProfileSettings();
        validGlobal.localeTag = "fr-FR";
        validGlobal.timeZoneId = "Europe/Paris";
        validGlobal.latitude = 48.0;
        validGlobal.longitude = 2.0;
        validGlobal.locationEnabled = true;
        ProfileResolver.ResolvedProfile invalidFallback =
                ProfileResolver.resolve(invalidClone, validGlobal, system);
        check("fr-FR".equals(invalidFallback.localeTag)
                        && invalidFallback.localeSource == ProfileResolver.Source.GLOBAL,
                "invalid clone locale must fall back to global");
        check("Europe/Paris".equals(invalidFallback.timeZoneId)
                        && invalidFallback.timeZoneSource == ProfileResolver.Source.GLOBAL,
                "invalid clone timezone must fall back to global");
        check(Double.valueOf(48.0).equals(invalidFallback.latitude)
                        && invalidFallback.latitudeSource == ProfileResolver.Source.GLOBAL,
                "invalid latitude must fall back independently");
        check(Double.valueOf(45.0).equals(invalidFallback.longitude)
                        && invalidFallback.longitudeSource == ProfileResolver.Source.CLONE,
                "valid clone longitude must remain an override");
        check(Boolean.FALSE.equals(invalidFallback.locationEnabled)
                        && invalidFallback.locationEnabledSource == ProfileResolver.Source.CLONE,
                "valid explicit false must remain an override");

        // Invalid global values must fall through to system values independently.
        ProfileSettings invalidGlobal = new ProfileSettings();
        invalidGlobal.localeTag = "bad tag";
        invalidGlobal.timeZoneId = "Not/AZone";
        invalidGlobal.latitude = -999.0;
        invalidGlobal.longitude = 181.0;
        ProfileResolver.ResolvedProfile systemFallback =
                ProfileResolver.resolve(new ProfileSettings(), invalidGlobal, system);
        check("en-US".equals(systemFallback.localeTag)
                        && systemFallback.localeSource == ProfileResolver.Source.SYSTEM,
                "invalid global locale must fall back to system");
        check("America/New_York".equals(systemFallback.timeZoneId)
                        && systemFallback.timeZoneSource == ProfileResolver.Source.SYSTEM,
                "invalid global timezone must fall back to system");
        check(Double.valueOf(10.0).equals(systemFallback.latitude)
                        && systemFallback.latitudeSource == ProfileResolver.Source.SYSTEM,
                "invalid global latitude must fall back to system");
        check(Double.valueOf(20.0).equals(systemFallback.longitude)
                        && systemFallback.longitudeSource == ProfileResolver.Source.SYSTEM,
                "invalid global longitude must fall back to system");

        // Clearing one clone's override (represented by null) reveals the next fallback.
        ProfileSettings cloneA = new ProfileSettings();
        cloneA.timeZoneId = "Asia/Tehran";
        ProfileSettings cloneB = new ProfileSettings();
        cloneB.timeZoneId = "Europe/London";
        ProfileResolver.ResolvedProfile aBefore = ProfileResolver.resolve(cloneA, global, system);
        ProfileResolver.ResolvedProfile bBefore = ProfileResolver.resolve(cloneB, global, system);
        check("Asia/Tehran".equals(aBefore.timeZoneId), "clone A must keep its own timezone");
        check("Europe/London".equals(bBefore.timeZoneId), "clone B must keep its own timezone");
        ProfileResolver.ResolvedProfile aAfterClear = ProfileResolver.resolve(
                new ProfileSettings(), global, system);
        check("America/New_York".equals(aAfterClear.timeZoneId),
                "clearing clone override must reveal system fallback");

        ProfileSettings copied = cloneA.copy();
        copied.timeZoneId = "UTC";
        check("Asia/Tehran".equals(cloneA.timeZoneId), "copy must not mutate original settings");
        System.out.println("ProfileResolver contract tests: PASS");
    }

    private static ProfileSettings newInvalidSettings() {
        ProfileSettings value = new ProfileSettings();
        value.latitude = 91.0;
        return value;
    }

    private static ProfileSettings newNaNLatitude() {
        ProfileSettings value = new ProfileSettings();
        value.latitude = Double.NaN;
        return value;
    }

    private static ProfileSettings newInfiniteLongitude() {
        ProfileSettings value = new ProfileSettings();
        value.longitude = Double.POSITIVE_INFINITY;
        return value;
    }
}
