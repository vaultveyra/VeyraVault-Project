import com.veyravault.space.core.ProfileSettings;
import com.veyravault.space.core.ProfileResolver;

public final class ProfileResolverContractTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        ProfileSettings safe = new ProfileSettings();
        safe.localeTag = "en-US"; safe.timeZoneId = "UTC"; safe.locationEnabled = false;
        ProfileSettings global = new ProfileSettings();
        global.localeTag = "fa-IR"; global.locationEnabled = true; global.latitude = 30.0;
        ProfileSettings clone = new ProfileSettings();
        clone.timeZoneId = "Asia/Tehran"; clone.locationEnabled = false; clone.longitude = 40.0;
        ProfileResolver.ResolvedProfile result = ProfileResolver.resolve(clone, global, safe);
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
                new ProfileSettings(), new ProfileSettings(), safe);
        check("en-US".equals(fallback.localeTag), "safe default should be used");
        check(fallback.localeSource == ProfileResolver.Source.SAFE_DEFAULT,
                "fallback source must be SAFE_DEFAULT, never host SYSTEM");
        ProfileResolver.ResolvedProfile unset = ProfileResolver.resolve(null, null, null);
        check(unset.localeTag == null && unset.localeSource == ProfileResolver.Source.UNSET,
                "missing values should remain explicitly unset");
        check(!newInvalidSettings().isValid(), "out-of-range coordinates must be rejected");
        check(!newNaNLatitude().isValid(), "NaN latitude must be rejected");
        check(!newInfiniteLongitude().isValid(), "infinite longitude must be rejected");
        ProfileSettings invalidClone = new ProfileSettings();
        invalidClone.localeTag = "not a valid tag"; invalidClone.timeZoneId = "Mars/Olympus";
        invalidClone.latitude = 999.0; invalidClone.longitude = 45.0; invalidClone.locationEnabled = false;
        ProfileSettings validGlobal = new ProfileSettings();
        validGlobal.localeTag = "fr-FR"; validGlobal.timeZoneId = "Europe/Paris";
        validGlobal.latitude = 48.0; validGlobal.longitude = 2.0; validGlobal.locationEnabled = true;
        ProfileResolver.ResolvedProfile invalidFallback = ProfileResolver.resolve(invalidClone, validGlobal, safe);
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
        ProfileSettings cloneA = new ProfileSettings(); cloneA.timeZoneId = "Asia/Tehran";
        ProfileSettings cloneB = new ProfileSettings(); cloneB.timeZoneId = "Europe/London";
        ProfileResolver.ResolvedProfile aBefore = ProfileResolver.resolve(cloneA, global, safe);
        ProfileResolver.ResolvedProfile bBefore = ProfileResolver.resolve(cloneB, global, safe);
        check("Asia/Tehran".equals(aBefore.timeZoneId), "clone A must keep its own timezone");
        check("Europe/London".equals(bBefore.timeZoneId), "clone B must keep its own timezone");
        ProfileResolver.ResolvedProfile aAfterClear = ProfileResolver.resolve(new ProfileSettings(), global, safe);
        check("UTC".equals(aAfterClear.timeZoneId), "cleared override must use safe default");
        ProfileSettings copied = cloneA.copy(); copied.timeZoneId = "UTC";
        check("Asia/Tehran".equals(cloneA.timeZoneId), "copy must not mutate original settings");
        System.out.println("ProfileResolver contract tests: PASS");
    }
    private static ProfileSettings newInvalidSettings() { ProfileSettings v = new ProfileSettings(); v.latitude = 91.0; return v; }
    private static ProfileSettings newNaNLatitude() { ProfileSettings v = new ProfileSettings(); v.latitude = Double.NaN; return v; }
    private static ProfileSettings newInfiniteLongitude() { ProfileSettings v = new ProfileSettings(); v.longitude = Double.POSITIVE_INFINITY; return v; }
}
