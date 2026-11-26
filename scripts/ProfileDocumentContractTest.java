import com.veyravault.space.core.ProfileDocument;
import com.veyravault.space.core.ProfileDocumentResolver;
import com.veyravault.space.core.ProfileFieldRegistry;

public final class ProfileDocumentContractTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        ProfileDocument clone = new ProfileDocument();
        ProfileDocument global = new ProfileDocument();
        ProfileDocument safe = ProfileFieldRegistry.createSafeDefaults();
        check(clone.put("timeZoneId", "America/Los_Angeles"), "valid clone timezone");
        check(global.put("localeTag", "en-US"), "valid global locale");
        check(global.put("timeZoneId", "America/New_York"), "valid global timezone");
        check("en-US".equals(safe.get("localeTag")), "registry safe locale");
        check("UTC".equals(safe.get("timeZoneId")), "registry safe timezone");
        check(Boolean.FALSE.equals(safe.get("locationEnabled")), "registry safe location disabled");

        ProfileDocumentResolver.FieldResult tz =
                ProfileDocumentResolver.resolve("timeZoneId", clone, global, safe);
        check("America/Los_Angeles".equals(tz.value)
                && tz.source == ProfileDocumentResolver.Source.CLONE, "Clone must win");
        check(tz.status == ProfileFieldRegistry.ApplyStatus.NOT_TESTED,
                "stored supported value is not automatically reported as applied");

        ProfileDocumentResolver.FieldResult locale =
                ProfileDocumentResolver.resolve("localeTag", clone, global, safe);
        check("en-US".equals(locale.value)
                && locale.source == ProfileDocumentResolver.Source.GLOBAL, "Global must inherit per field");

        ProfileDocumentResolver.FieldResult location =
                ProfileDocumentResolver.resolve("locationEnabled", clone, global, safe);
        check(Boolean.FALSE.equals(location.value)
                && location.source == ProfileDocumentResolver.Source.SAFE_DEFAULT,
                "safe default must be selected without host fallback");

        ProfileDocumentResolver.FieldResult country =
                ProfileDocumentResolver.resolve("countryCode", clone, global, safe);
        check(country.source == ProfileDocumentResolver.Source.UNSET,
                "no host country fallback is allowed");
        check(country.status == ProfileFieldRegistry.ApplyStatus.NOT_TESTED,
                "unconfigured local preference is not applied");

        ProfileDocumentResolver.FieldResult ip =
                ProfileDocumentResolver.resolve("publicIpAddress", clone, global, safe);
        check(ip.status == ProfileFieldRegistry.ApplyStatus.UNSUPPORTED,
                "IP observation requires a real network provider");

        check(!clone.put("imei", "123456789"), "restricted identifiers cannot be profile inputs");
        check(!clone.put("phoneNumber", "+15551234567"), "service-owned identity cannot be configured");
        check(!clone.put("publicIpAddress", "203.0.113.1"), "observed IP cannot be configured");
        check(!clone.put("latitude", 91.0), "invalid coordinates rejected");
        check(!clone.put("countryCode", "USA"), "country must be ISO alpha-2");
        check(!clone.put("currencyCode", "US"), "currency must be ISO alpha-3");
        check(clone.put("locationEnabled", Boolean.FALSE), "explicit false is a valid override");

        ProfileDocument cloneB = new ProfileDocument();
        check(cloneB.put("timeZoneId", "Europe/Paris"), "Clone B timezone");
        ProfileDocumentResolver.FieldResult a =
                ProfileDocumentResolver.resolve("timeZoneId", clone, global, safe);
        ProfileDocumentResolver.FieldResult b =
                ProfileDocumentResolver.resolve("timeZoneId", cloneB, global, safe);
        check("America/Los_Angeles".equals(a.value), "Clone A remains independent");
        check("Europe/Paris".equals(b.value), "Clone B remains independent");

        ProfileDocument copy = clone.copy();
        copy.put("timeZoneId", "UTC");
        check("America/Los_Angeles".equals(clone.get("timeZoneId")), "copy must be defensive");

        ProfileDocumentResolver.FieldResult promoted = ProfileDocumentResolver.withRuntimeStatus(
                tz, ProfileFieldRegistry.ApplyStatus.APPLIED);
        check(promoted.status == ProfileFieldRegistry.ApplyStatus.APPLIED, "runtime readback may promote status");
        boolean rejected = false;
        try {
            ProfileDocumentResolver.withRuntimeStatus(country, ProfileFieldRegistry.ApplyStatus.APPLIED);
        } catch (IllegalArgumentException expected) { rejected = true; }
        check(rejected, "metadata-only fields cannot be reported applied without an adapter");

        java.util.Map<String, ProfileDocumentResolver.FieldResult> all =
                ProfileDocumentResolver.resolveAll(clone, global);
        check(all.size() == ProfileFieldRegistry.all().size(), "resolveAll must cover every registered field");
        check(all.get("timeZoneId").source == ProfileDocumentResolver.Source.CLONE,
                "resolveAll must preserve Clone precedence");
        check(all.get("localeTag").source == ProfileDocumentResolver.Source.GLOBAL,
                "resolveAll must preserve per-field Global fallback");
        check(all.get("locationEnabled").source == ProfileDocumentResolver.Source.SAFE_DEFAULT,
                "resolveAll must use registry safe defaults");
        boolean immutable = false;
        try { all.clear(); } catch (UnsupportedOperationException expected) { immutable = true; }
        check(immutable, "resolveAll snapshot must be immutable");

        check(ProfileFieldRegistry.all().size() >= 40, "registry must cover the researched field inventory");
        System.out.println("Profile document/registry/resolver contract tests: PASS");
    }
}
