package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * Additive, versioned persistence for the expanded typed profile documents.
 *
 * This store is intentionally separate from ProfileStore: the existing five-field
 * runtime path remains authoritative until a separately reviewed provider/runtime
 * migration is complete. All operations are host-process serialized and commit-aware.
 */
public final class ProfileDocumentStore {
    private static final String PREFS = "veyravault_profile_documents_v1";
    private static final String KEY_DATA = "documents_json";
    private static final int SCHEMA_VERSION = 1;

    private ProfileDocumentStore() { }

    private static SharedPreferences prefs(Context context) {
        if (context == null) throw new IllegalArgumentException("Context is required");
        // Instrumentation and some wrapped/test Contexts may not expose an
        // Application Context. Fall back to the supplied Context without
        // switching packages or touching the target application's preferences.
        Context applicationContext = context.getApplicationContext();
        Context storageContext = applicationContext != null ? applicationContext : context;
        return storageContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static String cloneKey(String packageName, int userId) {
        if (packageName == null || packageName.trim().isEmpty() || userId < 0) {
            throw new IllegalArgumentException("Clone identity is invalid");
        }
        return packageName + "#" + userId;
    }

    private static JSONObject readRoot(Context context) throws JSONException {
        String raw = prefs(context).getString(KEY_DATA, "");
        if (raw == null || raw.trim().isEmpty()) {
            JSONObject empty = new JSONObject();
            empty.put("schemaVersion", SCHEMA_VERSION);
            empty.put("revision", 0L);
            empty.put("updatedAt", 0L);
            empty.put("clones", new JSONObject());
            return empty;
        }
        JSONObject root = new JSONObject(raw);
        Object schemaVersion = root.opt("schemaVersion");
        if (!(schemaVersion instanceof Number)
                || Double.compare(((Number) schemaVersion).doubleValue(), SCHEMA_VERSION) != 0) {
            throw new IllegalStateException("Profile document schema is unsupported");
        }
        Object revision = root.opt("revision");
        Object updatedAt = root.opt("updatedAt");
        Object global = root.opt("global");
        Object clones = root.opt("clones");
        if (!(revision instanceof Number) || !(updatedAt instanceof Number)
                || (global != null && global != JSONObject.NULL && !(global instanceof JSONObject))
                || (clones != null && !(clones instanceof JSONObject))) {
            throw new IllegalStateException("Profile document root is structurally invalid");
        }
        return root;
    }

    private static JSONObject readProfileObject(JSONObject root, String cloneIdentity) {
        if (cloneIdentity == null) {
            JSONObject global = root.optJSONObject("global");
            return global == null ? new JSONObject() : global;
        }
        JSONObject clones = root.optJSONObject("clones");
        if (clones == null) return new JSONObject();
        Object raw = clones.opt(cloneIdentity);
        if (raw == null) return new JSONObject();
        if (!(raw instanceof JSONObject)) {
            throw new IllegalStateException("Clone profile document is structurally invalid");
        }
        return (JSONObject) raw;
    }

    private static boolean matchesJsonType(ProfileFieldRegistry.Field field, Object value) {
        switch (field.type) {
            case STRING: return value instanceof String;
            case BOOLEAN: return value instanceof Boolean;
            case INTEGER:
                return value instanceof Integer || value instanceof Long;
            case DECIMAL: return value instanceof Number;
            default: return false;
        }
    }

    private static ProfileDocument parseDocument(JSONObject object, boolean cloneScope) {
        ProfileDocument document = new ProfileDocument();
        for (ProfileFieldRegistry.Field field : ProfileFieldRegistry.all()) {
            Object value = object.opt(field.key);
            if (value == null || value == JSONObject.NULL) continue;
            if (!matchesJsonType(field, value)) {
                throw new IllegalStateException("Profile field has an invalid stored type: " + field.key);
            }
            if (!field.canBeStoredAsProfileInput()) {
                // Older editor builds exposed this VeyraVault-owned internal ID as a
                // generic string. Preserve the stored bytes during additive updates,
                // but mark the value invalid so it can never become an effective profile
                // input. Other restricted fields remain structural errors.
                if ("appInstallInstanceId".equals(field.key) && value instanceof String) {
                    document.markInvalid(field.key);
                    continue;
                }
                throw new IllegalStateException("Profile field is not an editable profile input: " + field.key);
            }
            // JSON permits integral-looking decimals (for example 0.0) to be
            // serialized as 0. Normalize numeric values to the registry's canonical
            // Java type before validation and exposure so round-trips remain typed.
            if (value instanceof Number) {
                Number number = (Number) value;
                if (field.type == ProfileFieldRegistry.ValueType.DECIMAL) {
                    value = Double.valueOf(number.doubleValue());
                } else if (field.type == ProfileFieldRegistry.ValueType.INTEGER) {
                    value = Long.valueOf(number.longValue());
                }
            }
            // Semantic invalidity is field-scoped: omit only this field so the resolver
            // can continue to Global or Safe Isolated Default for that field.
            if (ProfileFieldRegistry.isValidValue(field, value)) {
                if (!document.put(field.key, value)) {
                    throw new IllegalStateException("Valid profile field could not be decoded: " + field.key);
                }
            } else {
                // Preserve presence without accepting the invalid value. The runtime
                // compatibility merge must not resurrect a stale same-level Legacy value.
                document.markInvalid(field.key);
            }
        }
        Object rawStates = object.opt("_fieldStates");
        if (rawStates != null && !(rawStates instanceof JSONObject)) throw new IllegalStateException("Profile field-state map is structurally invalid");
        JSONObject states = rawStates instanceof JSONObject ? (JSONObject) rawStates : new JSONObject();
        java.util.Iterator<String> stateKeys = states.keys();
        while (stateKeys.hasNext()) {
            String key = stateKeys.next();
            ProfileFieldRegistry.Field field = ProfileFieldRegistry.get(key);
            Object rawState = states.opt(key);
            if (field == null || !field.canBeStoredAsProfileInput() || !(rawState instanceof String) || object.has(key))
                throw new IllegalStateException("Profile field-state entry is invalid: " + key);
            if (cloneScope && "INHERIT_GLOBAL".equals(rawState)) document.markInheritGlobal(key);
            else if (cloneScope && "SAFE_DEFAULT".equals(rawState)) document.markSafeDefault(key);
            else if (!cloneScope && "SAFE_DEFAULT".equals(rawState)) document.markSafeDefault(key);
            else throw new IllegalStateException("Profile field-state is invalid for its scope: " + key);
        }
        return document;
    }

    public static synchronized ProfileDocument readGlobalStrict(Context context) throws Exception {
        JSONObject root = readRoot(context);
        return parseDocument(readProfileObject(root, null), false);
    }

    public static synchronized ProfileDocument readCloneStrict(
            Context context, String packageName, int userId) throws Exception {
        JSONObject root = readRoot(context);
        return parseDocument(readProfileObject(root, cloneKey(packageName, userId)), true);
    }

    public static synchronized long readRevisionStrict(Context context) throws Exception {
        return readRoot(context).getLong("revision");
    }

    public static synchronized boolean saveGlobalDocument(Context context, ProfileDocument document) {
        return saveDocument(context, null, document);
    }

    public static synchronized boolean saveCloneDocument(
            Context context, String packageName, int userId, ProfileDocument document) {
        try {
            return saveDocument(context, cloneKey(packageName, userId), document);
        } catch (RuntimeException invalidIdentity) {
            return false;
        }
    }

    private static boolean saveDocument(Context context, String cloneIdentity, ProfileDocument document) {
        if (document == null) return false;
        try {
            JSONObject root = readRoot(context);
            JSONObject existing = readProfileObject(root, cloneIdentity);
            parseDocument(existing, cloneIdentity != null); // Reject structural corruption before any read-modify-write.
            JSONObject updated = new JSONObject(existing.toString());

            // Replace only registered profile-input fields. Unknown future keys remain intact.
            JSONObject states = updated.optJSONObject("_fieldStates");
            if (states == null) states = new JSONObject();
            for (ProfileFieldRegistry.Field field : ProfileFieldRegistry.all()) {
                if (!field.canBeStoredAsProfileInput()) continue;
                if (document.contains(field.key)) {
                    Object value = document.get(field.key);
                    if (!ProfileFieldRegistry.isValidValue(field, value)) return false;
                    updated.put(field.key, value);
                } else updated.remove(field.key);
                ProfileDocument.FieldState state = document.state(field.key);
                if (state == null) states.remove(field.key);
                else {
                    if (cloneIdentity != null
                            && state != ProfileDocument.FieldState.INHERIT_GLOBAL
                            && state != ProfileDocument.FieldState.SAFE_DEFAULT) return false;
                    if (cloneIdentity == null && state != ProfileDocument.FieldState.SAFE_DEFAULT) return false;
                    states.put(field.key, state.name());
                }
            }
            if (states.length() == 0) updated.remove("_fieldStates");
            else updated.put("_fieldStates", states);
            return commitProfile(context, root, cloneIdentity, updated);
        } catch (Exception invalidOrCorrupt) {
            return false;
        }
    }

    public static synchronized boolean saveGlobalField(Context context, String fieldKey, Object value) {
        return saveField(context, null, fieldKey, value);
    }

    public static synchronized boolean saveCloneField(
            Context context, String packageName, int userId, String fieldKey, Object value) {
        try {
            return saveField(context, cloneKey(packageName, userId), fieldKey, value);
        } catch (RuntimeException invalidIdentity) {
            return false;
        }
    }

    private static boolean saveField(Context context, String cloneIdentity, String fieldKey, Object value) {
        ProfileFieldRegistry.Field field = ProfileFieldRegistry.get(fieldKey);
        if (field == null || !field.canBeStoredAsProfileInput()
                || !ProfileFieldRegistry.isValidValue(field, value)) return false;
        try {
            JSONObject root = readRoot(context);
            JSONObject existing = readProfileObject(root, cloneIdentity);
            parseDocument(existing, cloneIdentity != null); // Reject structural corruption before any read-modify-write.
            JSONObject updated = new JSONObject(existing.toString());
            updated.put(fieldKey, value);
            JSONObject states = updated.optJSONObject("_fieldStates");
            if (states != null) {
                states.remove(fieldKey);
                if (states.length() == 0) updated.remove("_fieldStates");
            }
            return commitProfile(context, root, cloneIdentity, updated);
        } catch (Exception invalidOrCorrupt) {
            return false;
        }
    }

    public static synchronized boolean clearGlobalField(Context context, String fieldKey) {
        return clearField(context, null, fieldKey);
    }

    public static synchronized boolean clearCloneField(
            Context context, String packageName, int userId, String fieldKey) {
        try {
            return clearField(context, cloneKey(packageName, userId), fieldKey);
        } catch (RuntimeException invalidIdentity) {
            return false;
        }
    }

    private static boolean clearField(Context context, String cloneIdentity, String fieldKey) {
        ProfileFieldRegistry.Field field = ProfileFieldRegistry.get(fieldKey);
        if (field == null || !field.canBeStoredAsProfileInput()) return false;
        try {
            JSONObject root = readRoot(context);
            JSONObject existing = readProfileObject(root, cloneIdentity);
            parseDocument(existing, cloneIdentity != null); // Reject structural corruption before any read-modify-write.
            JSONObject updated = new JSONObject(existing.toString());
            updated.remove(fieldKey);
            JSONObject states = updated.optJSONObject("_fieldStates");
            if (states == null) states = new JSONObject();
            states.put(fieldKey, cloneIdentity == null ? "SAFE_DEFAULT" : "INHERIT_GLOBAL");
            updated.put("_fieldStates", states);
            return commitProfile(context, root, cloneIdentity, updated);
        } catch (Exception invalidOrCorrupt) {
            return false;
        }
    }

    private static boolean commitProfile(Context context, JSONObject root,
                                         String cloneIdentity, JSONObject profile) throws JSONException {
        if (cloneIdentity == null) {
            if (profile.length() == 0) root.remove("global");
            else root.put("global", profile);
        } else {
            JSONObject clones = root.optJSONObject("clones");
            if (clones == null) clones = new JSONObject();
            if (profile.length() == 0) clones.remove(cloneIdentity);
            else clones.put(cloneIdentity, profile);
            root.put("clones", clones);
        }
        return commitRoot(context, root);
    }

    private static boolean commitRoot(Context context, JSONObject root) throws JSONException {
        long revision = root.optLong("revision", 0L);
        if (revision < 0L || revision == Long.MAX_VALUE) return false;
        root.put("schemaVersion", SCHEMA_VERSION);
        root.put("revision", revision + 1L);
        root.put("updatedAt", System.currentTimeMillis());
        return prefs(context).edit().putString(KEY_DATA, root.toString()).commit();
    }
}
