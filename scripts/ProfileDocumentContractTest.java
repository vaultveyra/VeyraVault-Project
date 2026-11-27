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
        check(ip.status == ProfileFieldRegistry.ApplyStatus.NOT_APPLICABLE,
                "observed IP is telemetry, not an editable profile input");

        check(!clone.put("imei", "123456789"), "restricted identifiers cannot be profile inputs");
        check(!clone.put("phoneNumber", "+15551234567"), "service-owned identity cannot be configured");
        check(!clone.put("publicIpAddress", "203.0.113.1"), "observed IP cannot be configured");

        boolean restrictedStateRejected = false;
        try { clone.markInheritGlobal("imei"); }
        catch (IllegalArgumentException expected) { restrictedStateRejected = true; }
        check(restrictedStateRejected, "platform-restricted identifiers cannot carry profile field states");

        boolean observedStateRejected = false;
        try { clone.markSafeDefault("publicIpAddress"); }
        catch (IllegalArgumentException expected) { observedStateRejected = true; }
        check(observedStateRejected, "observed-only fields cannot carry profile field states");

        boolean serviceOwnedStateRejected = false;
        try { clone.markInheritGlobal("accountId"); }
        catch (IllegalArgumentException expected) { serviceOwnedStateRejected = true; }
        check(serviceOwnedStateRejected, "service-owned identity cannot carry profile field states");

        ProfileDocument explicitState = new ProfileDocument();
        explicitState.markInheritGlobal("timeZoneId");
        check(explicitState.state("timeZoneId") == ProfileDocument.FieldState.INHERIT_GLOBAL,
                "storable fields retain valid field states");

        // Explicit per-Clone Safe Default must override a configured Global value.
        ProfileDocument safeOverride = new ProfileDocument();
        safeOverride.markSafeDefault("timeZoneId");
        ProfileDocumentResolver.FieldResult explicitSafe =
                ProfileDocumentResolver.resolve("timeZoneId", safeOverride, global, safe);
        check("UTC".equals(explicitSafe.value)
                        && explicitSafe.source == ProfileDocumentResolver.Source.SAFE_DEFAULT,
                "explicit Clone Safe Default must block Global inheritance");

        // INHERIT_GLOBAL must skip the Clone layer and select Global when valid.
        ProfileDocument inheritGlobal = new ProfileDocument();
        inheritGlobal.put("timeZoneId", "Asia/Tokyo");
        inheritGlobal.markInheritGlobal("timeZoneId");
        ProfileDocumentResolver.FieldResult inherited =
                ProfileDocumentResolver.resolve("timeZoneId", inheritGlobal, global, safe);
        check("America/New_York".equals(inherited.value)
                        && inherited.source == ProfileDocumentResolver.Source.GLOBAL,
                "explicit Inherit Global must select Global instead of Clone");

        // If Global itself requests Safe Default, clones inheriting it must not reuse
        // an old Global value or fall through to a host-derived setting.
        ProfileDocument globalSafe = new ProfileDocument();
        globalSafe.put("timeZoneId", "America/New_York");
        globalSafe.markSafeDefault("timeZoneId");
        ProfileDocumentResolver.FieldResult globalSafeResult =
                ProfileDocumentResolver.resolve("timeZoneId", new ProfileDocument(), globalSafe, safe);
        check("UTC".equals(globalSafeResult.value)
                        && globalSafeResult.source == ProfileDocumentResolver.Source.SAFE_DEFAULT,
                "Global Safe Default must override its former value");
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

        ProfileDocument allClone = new ProfileDocument();
        check(allClone.put("timeZoneId", "America/Los_Angeles"), "resolveAll Clone fixture");
        java.util.Map<String, ProfileDocumentResolver.FieldResult> all =
                ProfileDocumentResolver.resolveAll(allClone, global);
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

        check(ProfileFieldRegistry.all().size() >= 90, "registry must cover the complete researched field inventory");
        for (ProfileFieldRegistry.Field field : ProfileFieldRegistry.all()) {
            check(field.id != null && !field.id.isEmpty() && field.id.equals(field.key),
                    "every field must have a stable ID: " + field.key);
            check(field.label != null && !field.label.isEmpty(),
                    "every field must have a UI label: " + field.key);
            check(field.adapterId != null && !field.adapterId.isEmpty(),
                    "every field must declare adapter mapping: " + field.key);
            check(field.apiSupport != null && !field.apiSupport.isEmpty(),
                    "every field must declare API support state: " + field.key);
            check(field.privacyClass != null && !field.privacyClass.isEmpty(),
                    "every field must declare privacy class: " + field.key);
            check(field.readbackMethod != null && !field.readbackMethod.isEmpty(),
                    "every field must declare readback method: " + field.key);
            check(field.unsupportedReason != null && !field.unsupportedReason.isEmpty(),
                    "every field must declare capability reason: " + field.key);
            check(field.editable == field.canBeStoredAsProfileInput(),
                    "field editability must match storage policy: " + field.key);
        }
        check(!ProfileFieldRegistry.get("imei").editable
                        && !ProfileFieldRegistry.get("publicIpAddress").editable
                        && !ProfileFieldRegistry.get("batteryState").editable,
                "restricted and observed-only values must never be editable");
        check(ProfileFieldRegistry.get("altitude") != null
                        && ProfileFieldRegistry.get("locationProviderState") != null,
                "location metadata inventory must be complete");
        check(ProfileFieldRegistry.get("ipv6LeakStatus") != null
                        && ProfileFieldRegistry.get("throughputMbps") != null,
                "network observation inventory must be complete");
        check(ProfileFieldRegistry.get("privateFilesIsolation") != null
                        && ProfileFieldRegistry.get("pushRegistrationPolicy") != null,
                "app-data isolation inventory must be complete");
        check(ProfileFieldRegistry.get("webViewLocalStorageIsolation") != null
                        && ProfileFieldRegistry.get("tlsNetworkStackProfile") != null,
                "browser/WebView inventory must be complete");
        check(!clone.put("ipv6LeakStatus", "PASS"),
                "observed network leak status cannot be manually asserted");
        check(!clone.put("batteryState", "100%"),
                "observed device telemetry cannot be manually asserted");
        System.out.println("Profile document/registry/resolver contract tests: PASS");
    }
}
