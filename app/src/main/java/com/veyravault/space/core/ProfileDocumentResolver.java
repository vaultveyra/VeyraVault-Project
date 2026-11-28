package com.veyravault.space.core;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/** Field-by-field Clone -> Global -> explicit Safe Isolated Default resolver. */
public final class ProfileDocumentResolver {
    public enum Source { CLONE, GLOBAL, SAFE_DEFAULT, UNSET }

    public static final class FieldResult {
        public final String key;
        public final Object value;
        public final Source source;
        public final ProfileFieldRegistry.ApplyStatus status;

        private FieldResult(String key, Object value, Source source,
                            ProfileFieldRegistry.ApplyStatus status) {
            this.key = key; this.value = value; this.source = source; this.status = status;
        }
    }

    private ProfileDocumentResolver() { }

    /** Resolves every registered field using the registry-owned Safe Isolated Defaults. */
    public static Map<String, FieldResult> resolveAll(ProfileDocument clone,
                                                       ProfileDocument global) {
        return resolveAll(clone, global, ProfileFieldRegistry.createSafeDefaults());
    }

    /** Resolves every registered field and returns an immutable, stable-order snapshot. */
    public static Map<String, FieldResult> resolveAll(ProfileDocument clone,
                                                       ProfileDocument global,
                                                       ProfileDocument safeDefaults) {
        ProfileDocument defaults = safeDefaults == null
                ? ProfileFieldRegistry.createSafeDefaults() : safeDefaults;
        Map<String, FieldResult> results = new LinkedHashMap<>();
        for (ProfileFieldRegistry.Field field : ProfileFieldRegistry.all()) {
            results.put(field.key, resolve(field.key, clone, global, defaults));
        }
        return Collections.unmodifiableMap(results);
    }

    public static FieldResult resolve(String key, ProfileDocument clone,
                                      ProfileDocument global, ProfileDocument safeDefaults) {
        ProfileFieldRegistry.Field field = ProfileFieldRegistry.get(key);
        if (field == null) return new FieldResult(key, null, Source.UNSET,
                ProfileFieldRegistry.ApplyStatus.UNSUPPORTED);

        ProfileDocument defaults = safeDefaults == null
                ? ProfileFieldRegistry.createSafeDefaults() : safeDefaults;
        Object value = null;
        Source source = Source.UNSET;

        // An explicit Clone Safe Default is a deliberate override of Global.
        // INHERIT_GLOBAL skips only the Clone layer; invalid/missing values also
        // fall through per field without affecting unrelated profile fields.
        boolean cloneForcesSafe = hasState(clone, key, ProfileDocument.FieldState.SAFE_DEFAULT);
        boolean cloneInherits = hasState(clone, key, ProfileDocument.FieldState.INHERIT_GLOBAL);
        if (cloneForcesSafe) {
            if (validValue(field, defaults)) {
                value = defaults.get(key);
                source = Source.SAFE_DEFAULT;
            }
        } else {
            if (!cloneInherits && validValue(field, clone)) {
                value = clone.get(key);
                source = Source.CLONE;
            }
            if (value == null) {
                if (hasState(global, key, ProfileDocument.FieldState.SAFE_DEFAULT)) {
                    // A Global Safe Default deliberately blocks registry-independent values.
                    if (validValue(field, defaults)) {
                        value = defaults.get(key);
                        source = Source.SAFE_DEFAULT;
                    }
                } else if (validValue(field, global)) {
                    value = global.get(key);
                    source = Source.GLOBAL;
                } else if (validValue(field, defaults)) {
                    value = defaults.get(key);
                    source = Source.SAFE_DEFAULT;
                }
            }
        }

        ProfileFieldRegistry.ApplyStatus status;
        switch (field.capability) {
            case PLATFORM_RESTRICTED:
            case SERVICE_OWNED:
            case NETWORK_PROVIDER_REQUIRED:
                status = ProfileFieldRegistry.ApplyStatus.UNSUPPORTED;
                break;
            case OBSERVED_ONLY:
                status = ProfileFieldRegistry.ApplyStatus.NOT_APPLICABLE;
                break;
            case LOCAL_PREFERENCE_ONLY:
            case NOT_IMPLEMENTED:
                status = value == null ? ProfileFieldRegistry.ApplyStatus.NOT_TESTED
                        : ProfileFieldRegistry.ApplyStatus.STORED_ONLY;
                break;
            case PROCESS_SCOPED:
            case ENGINE_SCOPED:
            default:
                status = ProfileFieldRegistry.ApplyStatus.NOT_TESTED;
                break;
        }
        return new FieldResult(key, value, source, status);
    }

    private static boolean hasState(ProfileDocument document, String key,
                                    ProfileDocument.FieldState state) {
        return document != null && document.state(key) == state;
    }

    private static boolean validValue(ProfileFieldRegistry.Field field, ProfileDocument document) {
        return document != null && !document.hasState(field.key) && !document.isInvalid(field.key)
                && document.contains(field.key)
                && ProfileFieldRegistry.isValidValue(field, document.get(field.key));
    }

    /** Only a verified runtime adapter may promote a supported field to APPLIED. */
    public static FieldResult withRuntimeStatus(FieldResult result,
                                                ProfileFieldRegistry.ApplyStatus verifiedStatus) {
        if (result == null || verifiedStatus == null) throw new IllegalArgumentException("Result/status required");
        ProfileFieldRegistry.Field field = ProfileFieldRegistry.get(result.key);
        if (verifiedStatus == ProfileFieldRegistry.ApplyStatus.APPLIED
                && (field == null || (field.capability != ProfileFieldRegistry.Capability.PROCESS_SCOPED
                && field.capability != ProfileFieldRegistry.Capability.ENGINE_SCOPED))) {
            throw new IllegalArgumentException("No verified runtime adapter is registered for " + result.key);
        }
        if (verifiedStatus == ProfileFieldRegistry.ApplyStatus.STORED_ONLY
                && field != null && field.capability != ProfileFieldRegistry.Capability.LOCAL_PREFERENCE_ONLY
                && field.capability != ProfileFieldRegistry.Capability.NOT_IMPLEMENTED) {
            throw new IllegalArgumentException("Field is not metadata-only: " + result.key);
        }
        return new FieldResult(result.key, result.value, result.source, verifiedStatus);
    }
}
