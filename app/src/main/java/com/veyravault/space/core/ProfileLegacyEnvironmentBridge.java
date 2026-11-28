package com.veyravault.space.core;

import android.content.Context;

import java.util.List;
import java.util.Map;

/**
 * Read-only bridge from legacy CloneStore device metadata into the typed profile resolver.
 *
 * Typed profile values and explicit field states always win. Legacy values are considered
 * only when the corresponding typed field is absent, valid, and not explicitly inherited
 * or reset. No legacy data is migrated, rewritten, or deleted by this bridge.
 *
 * The bridged manufacturer/model/country values remain metadata-only under the registry;
 * this class does not alter Android Build, SIM, network, account, or service-owned identity.
 */
public final class ProfileLegacyEnvironmentBridge {
    private ProfileLegacyEnvironmentBridge() { }

    /** Adds explicitly saved Global metadata beneath typed Global profile values. */
    public static ProfileDocument mergeGlobal(Context context, ProfileDocument typed)
            throws Exception {
        ProfileDocument legacy = CloneStore.readGlobalEnvironmentMetadataProfileStrict(context);
        return overlay(typed, legacy);
    }

    /**
     * Adds one exact Clone's legacy device metadata beneath typed Clone profile values.
     * The composite packageName + userId identity is mandatory; a missing Clone fails closed.
     */
    public static ProfileDocument mergeClone(Context context, String packageName, int userId,
                                             ProfileDocument typed) throws Exception {
        if (context == null || packageName == null || packageName.trim().isEmpty() || userId < 0) {
            throw new IllegalArgumentException("Clone identity is invalid");
        }

        List<CloneStore.CloneEntry> clones = CloneStore.readAllStrict(context);
        CloneStore.CloneEntry match = null;
        for (CloneStore.CloneEntry entry : clones) {
            if (entry != null && packageName.equals(entry.packageName) && userId == entry.userId) {
                match = entry;
                break;
            }
        }
        if (match == null) {
            throw new IllegalStateException("Clone identity is not registered");
        }

        ProfileDocument legacy = new ProfileDocument();
        if (match.customDeviceEnabled) {
            putNonEmpty(legacy, "manufacturer", match.deviceBrand);
            putNonEmpty(legacy, "deviceModel", match.deviceModel);
        }
        return overlay(typed, legacy);
    }

    private static void putNonEmpty(ProfileDocument target, String key, String value) {
        if (value != null && !value.trim().isEmpty()) {
            // Invalid values are ignored by the typed registry; no host value is substituted.
            target.put(key, value.trim());
        }
    }

    private static ProfileDocument overlay(ProfileDocument typed, ProfileDocument legacy) {
        ProfileDocument merged = typed == null ? new ProfileDocument() : typed.copy();
        if (legacy == null) return merged;

        for (Map.Entry<String, Object> entry : legacy.values().entrySet()) {
            String key = entry.getKey();
            // An explicit typed value, invalid typed presence, or explicit field state
            // blocks the legacy layer. In particular, INHERIT_GLOBAL must not resurrect
            // an old Clone override after the user resets that field to Global.
            if (!merged.contains(key) && !merged.isInvalid(key) && !merged.hasState(key)) {
                merged.put(key, entry.getValue());
            }
        }
        return merged;
    }
}
