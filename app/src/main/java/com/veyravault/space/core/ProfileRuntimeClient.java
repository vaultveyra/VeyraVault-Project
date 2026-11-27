package com.veyravault.space.core;

import android.content.Context;
import android.net.Uri;
import android.os.Bundle;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/** Resolves immutable per-Clone profile snapshots through the default-process provider. */
public final class ProfileRuntimeClient {
    public static final class ResolvedField {
        public final String key;
        public final Object value;
        public final ProfileDocumentResolver.Source source;
        public final ProfileFieldRegistry.ApplyStatus status;
        public final ProfileFieldRegistry.Capability capability;
        public final ProfileFieldRegistry.ValueType type;
        public final String scope;
        public final String label;
        public final String adapterId;
        public final String apiSupport;
        public final String privacyClass;
        public final boolean editable;
        public final String readbackMethod;
        public final String unsupportedReason;

        private ResolvedField(String key, Object value,
                              ProfileDocumentResolver.Source source,
                              ProfileFieldRegistry.ApplyStatus status,
                              ProfileFieldRegistry.Field definition) {
            this.key = key;
            this.value = value;
            this.source = source;
            this.status = status;
            this.capability = definition.capability;
            this.type = definition.type;
            this.scope = definition.scope;
            this.label = definition.label;
            this.adapterId = definition.adapterId;
            this.apiSupport = definition.apiSupport;
            this.privacyClass = definition.privacyClass;
            this.editable = definition.editable;
            this.readbackMethod = definition.readbackMethod;
            this.unsupportedReason = definition.unsupportedReason;
        }
    }

    public static final class ResolvedDocument {
        public final String packageName;
        public final int userId;
        public final long revision;
        private final Map<String, ResolvedField> fields;

        private ResolvedDocument(String packageName, int userId, long revision,
                                 Map<String, ResolvedField> fields) {
            this.packageName = packageName;
            this.userId = userId;
            this.revision = revision;
            this.fields = Collections.unmodifiableMap(new LinkedHashMap<>(fields));
        }

        public Map<String, ResolvedField> fields() { return fields; }
        public ResolvedField field(String key) { return fields.get(key); }

        /** Legacy runtime adapter view; only its verified supported fields are consumed. */
        public ProfileResolver.ResolvedProfile toRuntimeProfile() {
            return ProfileResolver.fromResolvedValues(
                    string("localeTag"), runtimeSource("localeTag"),
                    string("timeZoneId"), runtimeSource("timeZoneId"),
                    bool("locationEnabled"), runtimeSource("locationEnabled"),
                    decimal("latitude"), runtimeSource("latitude"),
                    decimal("longitude"), runtimeSource("longitude"));
        }

        private String string(String key) {
            Object value = required(key).value;
            if (value == null) return null;
            if (!(value instanceof String)) throw new IllegalStateException("PROFILE_VALUE_TYPE:" + key);
            return (String) value;
        }

        private Boolean bool(String key) {
            Object value = required(key).value;
            if (value == null) return null;
            if (!(value instanceof Boolean)) throw new IllegalStateException("PROFILE_VALUE_TYPE:" + key);
            return (Boolean) value;
        }

        private Double decimal(String key) {
            Object value = required(key).value;
            if (value == null) return null;
            if (!(value instanceof Number)) throw new IllegalStateException("PROFILE_VALUE_TYPE:" + key);
            return ((Number) value).doubleValue();
        }

        private ResolvedField required(String key) {
            ResolvedField field = fields.get(key);
            if (field == null) throw new IllegalStateException("PROFILE_FIELD_MISSING:" + key);
            return field;
        }

        private ProfileResolver.Source runtimeSource(String key) {
            switch (required(key).source) {
                case CLONE: return ProfileResolver.Source.CLONE;
                case GLOBAL: return ProfileResolver.Source.GLOBAL;
                case SAFE_DEFAULT: return ProfileResolver.Source.SAFE_DEFAULT;
                case UNSET:
                default: return ProfileResolver.Source.UNSET;
            }
        }
    }

    private ProfileRuntimeClient() { }

    /** Returns the complete immutable field snapshot, not merely the five legacy runtime fields. */
    public static ResolvedDocument resolveDocument(
            Context context, String packageName, int userId) throws Exception {
        if (context == null || packageName == null || packageName.trim().isEmpty() || userId < 0) {
            throw new IllegalArgumentException("Clone identity is invalid");
        }
        Bundle request = new Bundle();
        request.putString("packageName", packageName);
        request.putInt("userId", userId);
        Uri endpoint = Uri.parse("content://" + context.getPackageName() + ".profile-runtime");
        Bundle response = context.getContentResolver().call(
                endpoint, ProfileRuntimeProvider.METHOD_RESOLVE_CLONE_PROFILE_DOCUMENT, null, request);
        if (response == null || !response.getBoolean("ok", false)) {
            String error = response == null ? "NO_RESPONSE" : response.getString("error", "UNKNOWN");
            throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:" + error);
        }
        Bundle bundles = response.getBundle("fields");
        if (bundles == null) throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:MISSING_FIELDS");

        Map<String, ResolvedField> decoded = new LinkedHashMap<>();
        for (ProfileFieldRegistry.Field definition : ProfileFieldRegistry.all()) {
            Bundle item = bundles.getBundle(definition.key);
            if (item == null) {
                throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:MISSING_FIELD:" + definition.key);
            }
            Object value = item.containsKey("value") ? item.get("value") : null;
            if (value != null && !ProfileFieldRegistry.isValidValue(definition, value)) {
                throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:INVALID_VALUE:" + definition.key);
            }
            ProfileDocumentResolver.Source source = enumValue(
                    item.getString("source"), ProfileDocumentResolver.Source.class, definition.key, "SOURCE");
            ProfileFieldRegistry.ApplyStatus status = enumValue(
                    item.getString("status"), ProfileFieldRegistry.ApplyStatus.class, definition.key, "STATUS");
            verifyMetadata(item, definition);
            validateStatus(definition, value, source, status);
            decoded.put(definition.key, new ResolvedField(
                    definition.key, value, source, status, definition));
        }
        if (bundles.size() != ProfileFieldRegistry.all().size()) {
            throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:FIELD_COUNT_MISMATCH");
        }
        return new ResolvedDocument(packageName, userId,
                response.getLong("revision", -1L), decoded);
    }

    /** Compatibility facade for the existing Locale/Time Zone/Location runtime adapters. */
    public static ProfileResolver.ResolvedProfile resolve(
            Context context, String packageName, int userId) throws Exception {
        return resolveDocument(context, packageName, userId).toRuntimeProfile();
    }

    private static void validateStatus(ProfileFieldRegistry.Field field, Object value,
                                        ProfileDocumentResolver.Source source,
                                        ProfileFieldRegistry.ApplyStatus status) {
        if (value != null && source == ProfileDocumentResolver.Source.UNSET) {
            throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:VALUE_WITHOUT_SOURCE:" + field.key);
        }
        switch (field.capability) {
            case OBSERVED_ONLY:
                if (status != ProfileFieldRegistry.ApplyStatus.NOT_APPLICABLE || value != null
                        || source != ProfileDocumentResolver.Source.UNSET) {
                    throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:OBSERVED_ONLY_POLICY:" + field.key);
                }
                break;
            case PLATFORM_RESTRICTED:
            case SERVICE_OWNED:
            case NETWORK_PROVIDER_REQUIRED:
                if (status != ProfileFieldRegistry.ApplyStatus.UNSUPPORTED) {
                    throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:UNSUPPORTED_POLICY:" + field.key);
                }
                break;
            case LOCAL_PREFERENCE_ONLY:
            case NOT_IMPLEMENTED:
                if (status != (value == null ? ProfileFieldRegistry.ApplyStatus.NOT_TESTED
                        : ProfileFieldRegistry.ApplyStatus.STORED_ONLY)) {
                    throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:STORAGE_STATUS:" + field.key);
                }
                break;
            case PROCESS_SCOPED:
            case ENGINE_SCOPED:
                if (status != ProfileFieldRegistry.ApplyStatus.NOT_TESTED
                        && status != ProfileFieldRegistry.ApplyStatus.APPLIED
                        && status != ProfileFieldRegistry.ApplyStatus.FAILED) {
                    throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:RUNTIME_STATUS:" + field.key);
                }
                break;
            default:
                throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:UNKNOWN_CAPABILITY:" + field.key);
        }
    }

    private static void verifyMetadata(Bundle item, ProfileFieldRegistry.Field field) {
        if (!field.capability.name().equals(item.getString("capability"))
                || !field.type.name().equals(item.getString("type"))
                || !field.scope.equals(item.getString("scope"))
                || !field.adapterId.equals(item.getString("adapterId"))
                || !field.apiSupport.equals(item.getString("apiSupport"))
                || !field.privacyClass.equals(item.getString("privacyClass"))
                || field.editable != item.getBoolean("editable", !field.editable)
                || !field.label.equals(item.getString("label"))
                || !field.readbackMethod.equals(item.getString("readbackMethod"))
                || !field.unsupportedReason.equals(item.getString("unsupportedReason"))) {
            throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:METADATA_MISMATCH:" + field.key);
        }
    }

    private static <T extends Enum<T>> T enumValue(String value, Class<T> type,
                                                   String key, String label) {
        if (value == null) throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:MISSING_" + label + ":" + key);
        try {
            return Enum.valueOf(type, value);
        } catch (IllegalArgumentException invalid) {
            throw new IllegalStateException("PROFILE_PROVIDER_FAILURE:INVALID_" + label + ":" + key);
        }
    }
}
