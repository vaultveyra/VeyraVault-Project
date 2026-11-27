package com.veyravault.space.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

/** Canonical registry for environment fields and their verified capability boundaries. */
public final class ProfileFieldRegistry {
    public enum ValueType { STRING, BOOLEAN, INTEGER, DECIMAL }
    public enum Capability {
        PROCESS_SCOPED, ENGINE_SCOPED, LOCAL_PREFERENCE_ONLY,
        NETWORK_PROVIDER_REQUIRED, PLATFORM_RESTRICTED, SERVICE_OWNED, NOT_IMPLEMENTED, OBSERVED_ONLY
    }
    public enum ApplyStatus { APPLIED, STORED_ONLY, UNSUPPORTED, NOT_TESTED, FAILED, NOT_APPLICABLE }

    public static final class Field {
        /** Stable machine identifier; once published it must never be renamed. */
        public final String id;
        public final String key;
        public final String label;
        public final ValueType type;
        public final Capability capability;
        public final Object safeDefault;
        public final String scope;
        public final String note;
        /** Explicit capability metadata; "NOT_VERIFIED" is not a support claim. */
        public final String adapterId;
        public final String apiSupport;
        public final String privacyClass;
        public final boolean editable;
        public final String readbackMethod;
        public final String unsupportedReason;

        private Field(String key, ValueType type, Capability capability,
                      Object safeDefault, String scope, String note) {
            this.id = key;
            this.key = key;
            this.label = humanize(key);
            this.type = type;
            this.capability = capability;
            this.safeDefault = safeDefault;
            this.scope = scope;
            this.note = note;
            this.editable = isEditableCapability(capability, scope);
            this.adapterId = adapterFor(capability, key);
            this.apiSupport = apiSupportFor(capability, key);
            this.privacyClass = privacyFor(capability, key);
            this.readbackMethod = readbackFor(capability, key);
            this.unsupportedReason = unsupportedFor(capability, key, note);
        }

        public boolean canBeStoredAsProfileInput() {
            return editable;
        }

        private static String humanize(String key) {
            if (key == null || key.isEmpty()) return "";
            StringBuilder label = new StringBuilder();
            for (int i = 0; i < key.length(); i++) {
                char ch = key.charAt(i);
                if (Character.isUpperCase(ch)) label.append(' ');
                label.append(ch);
            }
            label.setCharAt(0, Character.toUpperCase(label.charAt(0)));
            return label.toString();
        }

        private static boolean isEditableCapability(Capability capability, String scope) {
            return capability != Capability.PLATFORM_RESTRICTED
                    && capability != Capability.SERVICE_OWNED
                    && capability != Capability.OBSERVED_ONLY
                    && !"observed-only".equals(scope)
                    && !"read-only".equals(scope)
                    && !"service-owned".equals(scope);
        }

        private static String adapterFor(Capability capability, String key) {
            switch (capability) {
                case PROCESS_SCOPED:
                    return "profile-runtime-process";
                case ENGINE_SCOPED:
                    return "blackbox-engine";
                case NETWORK_PROVIDER_REQUIRED:
                    return "per-clone-network-provider";
                default:
                    return "none";
            }
        }

        private static String apiSupportFor(Capability capability, String key) {
            switch (capability) {
                case PROCESS_SCOPED:
                    return "API-gated; verify on each supported Android API";
                case ENGINE_SCOPED:
                    return "Pinned Engine API; per-field readback required";
                case NETWORK_PROVIDER_REQUIRED:
                    return "Requires a real network provider and external leak tests";
                default:
                    return "NOT_VERIFIED";
            }
        }

        private static String privacyFor(Capability capability, String key) {
            if (capability == Capability.PLATFORM_RESTRICTED
                    || capability == Capability.SERVICE_OWNED) return "restricted-sensitive";
            if (capability == Capability.OBSERVED_ONLY) return "observed-telemetry";
            if ("appInstallInstanceId".equals(key)) return "pseudonymous-internal";
            return "profile-preference";
        }

        private static String readbackFor(Capability capability, String key) {
            if ("localeTag".equals(key)) return "Locale.getDefault + Resources.Configuration";
            if ("timeZoneId".equals(key)) return "TimeZone.getDefault";
            if (capability == Capability.ENGINE_SCOPED) return "Engine package/user scoped API readback";
            if (capability == Capability.NETWORK_PROVIDER_REQUIRED) return "External egress, DNS, IPv4/IPv6 leak verification";
            if (capability == Capability.OBSERVED_ONLY) return "Live observation source; adapter not wired";
            return "No runtime readback adapter";
        }

        private static String unsupportedFor(Capability capability, String key, String note) {
            switch (capability) {
                case PROCESS_SCOPED:
                case ENGINE_SCOPED:
                    return "Readback evidence required before APPLIED";
                case NETWORK_PROVIDER_REQUIRED:
                    return "Real per-Clone network provider is required";
                case OBSERVED_ONLY:
                    return "Read-only telemetry; no profile write is permitted";
                case PLATFORM_RESTRICTED:
                    return "Platform-controlled or restricted; never fabricate";
                case SERVICE_OWNED:
                    return "Third-party/platform service owns this value";
                case LOCAL_PREFERENCE_ONLY:
                    return "Preference metadata only; no runtime adapter";
                case NOT_IMPLEMENTED:
                default:
                    return note == null ? "Adapter not implemented" : note;
            }
        }
    }

    private static final Map<String, Field> FIELDS;
    private static final Pattern COUNTRY = Pattern.compile("^[A-Za-z]{2}$");
    private static final Pattern CURRENCY = Pattern.compile("^[A-Za-z]{3}$");

    static {
        Map<String, Field> fields = new LinkedHashMap<>();
        add(fields, "localeTag", ValueType.STRING, Capability.PROCESS_SCOPED, "en-US", "clone/global", "Applied to virtual app process; runtime readback required.");
        add(fields, "timeZoneId", ValueType.STRING, Capability.PROCESS_SCOPED, "UTC", "clone/global", "Applied to virtual app process; runtime readback required.");
        add(fields, "locationEnabled", ValueType.BOOLEAN, Capability.ENGINE_SCOPED, Boolean.FALSE, "clone/global", "Package/user-scoped Engine location gate.");
        add(fields, "latitude", ValueType.DECIMAL, Capability.ENGINE_SCOPED, null, "clone/global", "Requires a valid explicit coordinate pair.");
        add(fields, "longitude", ValueType.DECIMAL, Capability.ENGINE_SCOPED, null, "clone/global", "Requires a valid explicit coordinate pair.");

        add(fields, "countryCode", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only; not IP/SIM/account country.");
        add(fields, "regionCode", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");
        add(fields, "cityName", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only; not GPS or IP geolocation.");
        add(fields, "currencyCode", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Locale preference metadata only.");
        add(fields, "dateFormat", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");
        add(fields, "timeFormat", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");
        add(fields, "measurementSystem", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");
        add(fields, "distanceUnit", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");
        add(fields, "temperatureUnit", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");
        add(fields, "weightUnit", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");
        add(fields, "lengthUnit", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");
        add(fields, "weekStart", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Preference metadata only.");

        add(fields, "deviceLabel", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "No verified package/user-scoped Engine adapter yet.");
        add(fields, "manufacturer", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "No verified package/user-scoped Engine adapter yet.");
        add(fields, "deviceModel", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "No verified package/user-scoped Engine adapter yet.");
        add(fields, "androidRelease", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "No verified package/user-scoped Engine adapter yet.");
        add(fields, "screenProfile", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "No verified virtual display adapter yet.");
        add(fields, "webViewUserAgentProfile", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "No verified per-Clone WebView adapter yet.");
        add(fields, "cookieStorageIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires verified Engine-owned per-Clone WebView/storage isolation.");
        add(fields, "permissionPolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires enforced package/user-scoped permission hooks.");
        add(fields, "sensorPolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires verified package/user-scoped sensor adapters.");
        add(fields, "appInstallInstanceId", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Must be generated and stored internally per Clone; not yet wired.");
        add(fields, "advertisingIdPolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires a compliant app-scoped identifier adapter.");

        add(fields, "networkRouteProfileId", ValueType.STRING, Capability.NETWORK_PROVIDER_REQUIRED, null, "clone/global", "Requires a real per-Clone traffic-routing provider.");
        add(fields, "dnsMode", ValueType.STRING, Capability.NETWORK_PROVIDER_REQUIRED, null, "clone/global", "Requires a real network adapter and leak tests.");
        add(fields, "dnsServers", ValueType.STRING, Capability.NETWORK_PROVIDER_REQUIRED, null, "clone/global", "Requires a real network adapter and leak tests.");
        add(fields, "publicIpAddress", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Observed egress result, never a manually asserted profile value.");

        add(fields, "buildFingerprint", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "Host OS/build identity is not an editable profile input.");
        add(fields, "cpuAbiProfile", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "Native ABI must match the actual host process and packaged libraries.");
        add(fields, "imei", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "Restricted hardware identifier; never configurable.");
        add(fields, "meid", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "Restricted hardware identifier; never configurable.");
        add(fields, "imsi", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "Restricted SIM identifier; never configurable.");
        add(fields, "serialNumber", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "Restricted hardware identifier; never configurable.");
        add(fields, "androidId", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "OS/app-scoped identifier; no generic editable hardware override.");
        add(fields, "wifiMac", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "OS-controlled identifier; never configurable.");
        add(fields, "wifiBssid", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "OS/network-controlled value; never configurable.");
        add(fields, "phoneNumber", ValueType.STRING, Capability.SERVICE_OWNED, null, "service-owned", "SIM/account/provider-owned data, not a VeyraVault profile field.");
        add(fields, "accountId", ValueType.STRING, Capability.SERVICE_OWNED, null, "service-owned", "Third-party service account identity is not controlled by this profile.");
        add(fields, "playIntegrityVerdict", ValueType.STRING, Capability.SERVICE_OWNED, null, "observed-only", "Security verdict is platform/service-owned and must remain truthful.");

        // Additional inventory required by the authoritative Clone/Global engine spec.
        // These entries make capability boundaries explicit; definitions do not imply adapters.
        add(fields, "calendarFormat", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Calendar formatting preference only; no verified Android adapter.");
        add(fields, "numberFormat", ValueType.STRING, Capability.LOCAL_PREFERENCE_ONLY, null, "clone/global", "Number formatting preference only; no verified Android adapter.");

        add(fields, "altitude", ValueType.DECIMAL, Capability.NOT_IMPLEMENTED, null, "clone/global", "Authorized test-location metadata only; no verified altitude adapter.");
        add(fields, "locationAccuracy", ValueType.DECIMAL, Capability.NOT_IMPLEMENTED, null, "clone/global", "Authorized test-location metadata only; no verified accuracy adapter.");
        add(fields, "locationBearing", ValueType.DECIMAL, Capability.NOT_IMPLEMENTED, null, "clone/global", "Authorized test-location metadata only; no verified bearing adapter.");
        add(fields, "locationSpeed", ValueType.DECIMAL, Capability.NOT_IMPLEMENTED, null, "clone/global", "Authorized test-location metadata only; no verified speed adapter.");
        add(fields, "locationTimestamp", ValueType.INTEGER, Capability.NOT_IMPLEMENTED, null, "clone/global", "Authorized test-location metadata only; timestamp is not a live location readback.");
        add(fields, "locationPermissionState", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Effective permission state must be observed from the platform; not user-asserted.");
        add(fields, "locationProviderState", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Provider availability must be measured from the actual runtime.");

        add(fields, "screenMetrics", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Actual display metrics are observed compatibility data; no virtual display adapter.");
        add(fields, "screenDensity", ValueType.DECIMAL, Capability.OBSERVED_ONLY, null, "observed-only", "Actual display density is observed compatibility data.");
        add(fields, "hardwareFeatures", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Actual hardware feature availability must not be fabricated.");
        add(fields, "batteryState", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Battery telemetry is measured, not a profile override.");
        add(fields, "memoryState", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Memory telemetry is measured, not a profile override.");
        add(fields, "storageState", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Storage telemetry is measured, not a profile override.");
        add(fields, "sensorAvailability", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Sensor availability is observed; no synthetic safety-critical readings.");

        add(fields, "ipv4RoutingStatus", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "IPv4 route status requires live route observation.");
        add(fields, "ipv6RoutingStatus", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "IPv6 route status requires live route observation.");
        add(fields, "networkTransport", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Network transport/type is measured from the active route.");
        add(fields, "vpnRouteStatus", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "VPN route status requires verified route observation.");
        add(fields, "proxyStatus", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "Proxy state is observed from the actual network path.");
        add(fields, "dnsLeakStatus", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "DNS leak result requires an external leak test.");
        add(fields, "ipv4LeakStatus", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "IPv4 leak result requires external egress verification.");
        add(fields, "ipv6LeakStatus", ValueType.STRING, Capability.OBSERVED_ONLY, null, "observed-only", "IPv6 leak result requires external egress verification.");
        add(fields, "latencyMs", ValueType.DECIMAL, Capability.OBSERVED_ONLY, null, "observed-only", "Latency is a measured observation, never a configured value.");
        add(fields, "pingMs", ValueType.DECIMAL, Capability.OBSERVED_ONLY, null, "observed-only", "Ping is a measured observation, never a configured value.");
        add(fields, "throughputMbps", ValueType.DECIMAL, Capability.OBSERVED_ONLY, null, "observed-only", "Throughput is a measured observation, never a configured value.");

        add(fields, "appSetId", ValueType.STRING, Capability.SERVICE_OWNED, null, "service-owned", "Google Play services-owned identifier; never fabricate or configure.");
        add(fields, "firebaseInstallationId", ValueType.STRING, Capability.SERVICE_OWNED, null, "service-owned", "Firebase service-owned installation identifier.");
        add(fields, "iccid", ValueType.STRING, Capability.PLATFORM_RESTRICTED, null, "read-only", "Restricted SIM identifier; never configurable.");
        add(fields, "purchaseState", ValueType.STRING, Capability.SERVICE_OWNED, null, "service-owned", "Purchase entitlement is store/service-owned and must remain truthful.");

        add(fields, "privateFilesIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires per-Clone private-directory isolation tests.");
        add(fields, "databaseIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires per-Clone database isolation tests.");
        add(fields, "sharedPreferencesIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires per-Clone preferences isolation tests.");
        add(fields, "downloadsMediaDocumentsIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires URI/media/document isolation tests.");
        add(fields, "contactsIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires explicit provider/permission isolation tests.");
        add(fields, "calendarDataIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires explicit provider/permission isolation tests.");
        add(fields, "accountsIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires account-provider isolation; cannot imply independent Android accounts.");
        add(fields, "clipboardPolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires verified package/user-scoped clipboard adapter.");
        add(fields, "notificationPolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires notification and listener isolation tests.");
        add(fields, "microphonePolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires verified package/user-scoped microphone permission adapter.");
        add(fields, "backgroundExecutionPolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires lifecycle and background execution isolation tests.");
        add(fields, "packageVisibilityPolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires package visibility enforcement and tests.");
        add(fields, "pushRegistrationPolicy", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Push tokens and service registrations remain provider-owned until isolated.");

        add(fields, "webViewLocalStorageIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires per-Clone WebView local-storage isolation tests.");
        add(fields, "webViewCacheIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires per-Clone WebView cache isolation tests.");
        add(fields, "serviceWorkerIsolation", ValueType.BOOLEAN, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires per-Clone Service Worker isolation tests.");
        add(fields, "javascriptLocaleTimeZone", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires WebView JavaScript API readback; User-Agent alone is insufficient.");
        add(fields, "screenSurfaceProfile", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires verified screen-surface adapter; no fingerprint evasion.");
        add(fields, "fontSurfaceProfile", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires verified font-surface adapter; no fingerprint evasion.");
        add(fields, "canvasSurfaceProfile", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires verified canvas-surface adapter; no fingerprint evasion.");
        add(fields, "webGlSurfaceProfile", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "Requires verified WebGL-surface adapter; no fingerprint evasion.");
        add(fields, "tlsNetworkStackProfile", ValueType.STRING, Capability.NOT_IMPLEMENTED, null, "clone/global", "TLS/network stack is not a cosmetic profile; requires supported engine routing and security review.");

        FIELDS = Collections.unmodifiableMap(fields);
    }

    private ProfileFieldRegistry() { }

    private static void add(Map<String, Field> fields, String key, ValueType type,
                            Capability capability, Object safeDefault, String scope, String note) {
        fields.put(key, new Field(key, type, capability, safeDefault, scope, note));
    }

    public static Field get(String key) { return FIELDS.get(key); }
    public static List<Field> all() {
        return Collections.unmodifiableList(new ArrayList<>(FIELDS.values()));
    }

    /** Builds the canonical deterministic defaults without consulting Android host state. */
    public static ProfileDocument createSafeDefaults() {
        ProfileDocument defaults = new ProfileDocument();
        for (Field field : all()) {
            if (field.safeDefault != null && isValidValue(field, field.safeDefault)) {
                if (!defaults.put(field.key, field.safeDefault)) {
                    throw new IllegalStateException("Invalid registry safe default: " + field.key);
                }
            }
        }
        return defaults;
    }

    public static boolean isValidValue(Field field, Object value) {
        if (field == null || value == null || !field.canBeStoredAsProfileInput()) return false;
        switch (field.type) {
            case STRING:
                if (!(value instanceof String) || ((String) value).trim().isEmpty()
                        || ((String) value).length() > 256) return false;
                String text = (String) value;
                if ("countryCode".equals(field.key)) return COUNTRY.matcher(text).matches();
                if ("currencyCode".equals(field.key)) return CURRENCY.matcher(text).matches();
                if ("localeTag".equals(field.key)) {
                    try { return !new java.util.Locale.Builder().setLanguageTag(text).build().getLanguage().isEmpty(); }
                    catch (RuntimeException invalid) { return false; }
                }
                if ("timeZoneId".equals(field.key)) {
                    if ("UTC".equals(text) || "GMT".equals(text)) return true;
                    return text.equals(java.util.TimeZone.getTimeZone(text).getID());
                }
                return true;
            case BOOLEAN:
                return value instanceof Boolean;
            case INTEGER:
                return value instanceof Integer || value instanceof Long;
            case DECIMAL:
                if (!(value instanceof Number)) return false;
                double number = ((Number) value).doubleValue();
                if (Double.isNaN(number) || Double.isInfinite(number)) return false;
                if ("latitude".equals(field.key)) return number >= -90.0 && number <= 90.0;
                if ("longitude".equals(field.key)) return number >= -180.0 && number <= 180.0;
                return true;
            default:
                return false;
        }
    }
}
