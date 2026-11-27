package com.veyravault.space.core;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/** Typed profile payload. Null means inherit; values are checked against the canonical registry. */
public final class ProfileDocument {
    private final Map<String, Object> values;
    // A semantic-invalid stored value is distinct from an absent override. This marker
    // exists only in the in-memory snapshot and is never persisted as a usable value.
    private final Set<String> invalidFields;

    public ProfileDocument() {
        values = new LinkedHashMap<>();
        invalidFields = new LinkedHashSet<>();
    }
    private ProfileDocument(Map<String, Object> source, Set<String> invalidSource) {
        values = new LinkedHashMap<>(source);
        invalidFields = new LinkedHashSet<>(invalidSource);
    }

    public boolean put(String key, Object value) {
        ProfileFieldRegistry.Field field = ProfileFieldRegistry.get(key);
        if (field == null) return false;
        if (value == null) { values.remove(key); invalidFields.remove(key); return true; }
        if (!ProfileFieldRegistry.isValidValue(field, value)) return false;
        values.put(key, value);
        invalidFields.remove(key);
        return true;
    }

    public Object get(String key) { return values.get(key); }
    public boolean contains(String key) { return values.containsKey(key); }
    public boolean isInvalid(String key) { return invalidFields.contains(key); }
    void markInvalid(String key) {
        if (ProfileFieldRegistry.get(key) == null) throw new IllegalArgumentException("Unknown profile field: " + key);
        values.remove(key);
        invalidFields.add(key);
    }
    public void remove(String key) { values.remove(key); invalidFields.remove(key); }
    public Map<String, Object> values() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(values));
    }
    public ProfileDocument copy() { return new ProfileDocument(values, invalidFields); }
    public boolean isEmpty() { return values.isEmpty() && invalidFields.isEmpty(); }
}
