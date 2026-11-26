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
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
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
        if (root.optInt("schemaVersion", -1) != SCHEMA_VERSION) {
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

    private static ProfileDocument parseDocument(JSONObject object) {
        ProfileDocument document = new ProfileDocument();
        for (ProfileFieldRegistry.Field field : ProfileFieldRegistry.all()) {
            Object value = object.opt(field.key);
            if (value == null || value == JSONObject.NULL) continue;
            if (!field.canBeStoredAsProfileInput() || !matchesJsonType(field, value)) {
                throw new IllegalStateException("Profile field has an invalid stored type or capability: " + field.key);
            }
            // Semantic invalidity is field-scoped: omit only this field so the resolver
            // can continue to Global or Safe Isolated Default for that field.
            if (ProfileFieldRegistry.isValidValue(field, value) && !document.put(field.key, value)) {
                throw new IllegalStateException("Valid profile field could not be decoded: " + field.key);
            }
        }
        return document;
    }

    public static synchronized ProfileDocument readGlobalStrict(Context context) throws Exception {
        JSONObject root = readRoot(context);
        return parseDocument(readProfileObject(root, null));
    }

    public static synchronized ProfileDocument readCloneStrict(
            Context context, String packageName, int userId) throws Exception {
        JSONObject root = readRoot(context);
        return parseDocument(readProfileObject(root, cloneKey(packageName, userId)));
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
            JSONObject updated = new JSONObject(existing.toString());

            // Replace only registered profile-input fields. Unknown future keys remain intact.
            for (ProfileFieldRegistry.Field field : ProfileFieldRegistry.all()) {
                if (!field.canBeStoredAsProfileInput()) continue;
                if (document.contains(field.key)) {
                    Object value = document.get(field.key);
                    if (!ProfileFieldRegistry.isValidValue(field, value)) return false;
                    updated.put(field.key, value);
                } else {
                    updated.remove(field.key);
                }
            }
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
            JSONObject updated = new JSONObject(existing.toString());
            updated.put(fieldKey, value);
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
            JSONObject updated = new JSONObject(existing.toString());
            updated.remove(fieldKey);
            if (cloneIdentity != null && updated.length() == 0) {
                JSONObject clones = root.optJSONObject("clones");
                if (clones != null) clones.remove(cloneIdentity);
                root.put("clones", clones == null ? new JSONObject() : clones);
                return commitRoot(context, root);
            }
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
