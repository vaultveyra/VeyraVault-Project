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
        System.out.println("ProfileResolver contract tests: PASS");
    }

    private static ProfileSettings newInvalidSettings() {
        ProfileSettings value = new ProfileSettings();
        value.latitude = 91.0;
        return value;
    }
}
