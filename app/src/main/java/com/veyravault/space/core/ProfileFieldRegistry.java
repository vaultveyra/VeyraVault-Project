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
        NETWORK_PROVIDER_REQUIRED, PLATFORM_RESTRICTED, SERVICE_OWNED, NOT_IMPLEMENTED
    }
    public enum ApplyStatus { APPLIED, STORED_ONLY, UNSUPPORTED, NOT_TESTED, FAILED }

    public static final class Field {
        public final String key;
        public final ValueType type;
        public final Capability capability;
        public final Object safeDefault;
        public final String scope;
        public final String note;

        private Field(String key, ValueType type, Capability capability,
                      Object safeDefault, String scope, String note) {
            this.key = key;
            this.type = type;
            this.capability = capability;
            this.safeDefault = safeDefault;
            this.scope = scope;
            this.note = note;
        }

        public boolean canBeStoredAsProfileInput() {
            return capability != Capability.PLATFORM_RESTRICTED
                    && capability != Capability.SERVICE_OWNED
                    && !"observed-only".equals(scope) && !"read-only".equals(scope);
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
        add(fields, "publicIpAddress", ValueType.STRING, Capability.NETWORK_PROVIDER_REQUIRED, null, "observed-only", "Observed egress result, never a manually asserted profile value.");

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
