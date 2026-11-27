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
    private final Map<String, FieldState> fieldStates;

    public enum FieldState { INHERIT_GLOBAL, SAFE_DEFAULT }

    public ProfileDocument() {
        values = new LinkedHashMap<>();
        invalidFields = new LinkedHashSet<>();
        fieldStates = new LinkedHashMap<>();
    }
    private ProfileDocument(Map<String, Object> source, Set<String> invalidSource, Map<String, FieldState> stateSource) {
        values = new LinkedHashMap<>(source);
        invalidFields = new LinkedHashSet<>(invalidSource);
        fieldStates = new LinkedHashMap<>(stateSource);
    }

    public boolean put(String key, Object value) {
        ProfileFieldRegistry.Field field = ProfileFieldRegistry.get(key);
        if (field == null) return false;
        if (value == null) { values.remove(key); invalidFields.remove(key); fieldStates.remove(key); return true; }
        if (!ProfileFieldRegistry.isValidValue(field, value)) return false;
        values.put(key, value);
        invalidFields.remove(key);
        fieldStates.remove(key);
        return true;
    }

    public Object get(String key) { return values.get(key); }
    public boolean contains(String key) { return values.containsKey(key); }
    public boolean isInvalid(String key) { return invalidFields.contains(key); }
    public FieldState state(String key) { return fieldStates.get(key); }
    public boolean hasState(String key) { return fieldStates.containsKey(key); }
    public Map<String, FieldState> fieldStates() { return Collections.unmodifiableMap(new LinkedHashMap<>(fieldStates)); }
    public void markInheritGlobal(String key) { markState(key, FieldState.INHERIT_GLOBAL); }
    public void markSafeDefault(String key) { markState(key, FieldState.SAFE_DEFAULT); }
    private void markState(String key, FieldState state) {
        if (ProfileFieldRegistry.get(key) == null) throw new IllegalArgumentException("Unknown profile field: " + key);
        values.remove(key); invalidFields.remove(key); fieldStates.put(key, state);
    }
    void markInvalid(String key) {
        if (ProfileFieldRegistry.get(key) == null) throw new IllegalArgumentException("Unknown profile field: " + key);
        values.remove(key);
        fieldStates.remove(key);
        invalidFields.add(key);
    }
    public void remove(String key) { values.remove(key); invalidFields.remove(key); fieldStates.remove(key); }
    public Map<String, Object> values() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(values));
    }
    public ProfileDocument copy() { return new ProfileDocument(values, invalidFields, fieldStates); }
    public boolean isEmpty() { return values.isEmpty() && invalidFields.isEmpty() && fieldStates.isEmpty(); }
}
