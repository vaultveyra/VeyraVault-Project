package com.veyravault.space.core;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/** Typed profile payload. Null means inherit; values are checked against the canonical registry. */
public final class ProfileDocument {
    private final Map<String, Object> values;

    public ProfileDocument() { values = new LinkedHashMap<>(); }
    private ProfileDocument(Map<String, Object> source) { values = new LinkedHashMap<>(source); }

    public boolean put(String key, Object value) {
        ProfileFieldRegistry.Field field = ProfileFieldRegistry.get(key);
        if (field == null) return false;
        if (value == null) { values.remove(key); return true; }
        if (!ProfileFieldRegistry.isValidValue(field, value)) return false;
        values.put(key, value);
        return true;
    }

    public Object get(String key) { return values.get(key); }
    public boolean contains(String key) { return values.containsKey(key); }
    public void remove(String key) { values.remove(key); }
    public Map<String, Object> values() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(values));
    }
    public ProfileDocument copy() { return new ProfileDocument(values); }
    public boolean isEmpty() { return values.isEmpty(); }
}
