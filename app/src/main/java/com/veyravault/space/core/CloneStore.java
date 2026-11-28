package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

public class CloneStore {
    private static final String PREF = "veyravault_clones_v2";
    private static final String KEY_CLONES = "clones_json";
    private static final String KEY_COLLAPSED = "collapsed_spaces";
    private static final String KEY_MASTER_GPS = "master_mock_gps";
    private static final String KEY_GLOBAL_DEV = "global_device_json";
    private static final String KEY_ACTIVE_LAUNCH = "active_launch_json";
    private static final String KEY_PENDING_RESERVATIONS = "pending_clone_reservations_json";
    private static final String KEY_GLOBAL_HIGH_WATER_MARK = "last_reserved_global_user_id";
    private static final int RESERVATION_SCHEMA_VERSION = 1;

    /** Checked signal that SharedPreferences declined a durable commit. */
    static final class PersistenceException extends Exception {
        PersistenceException(String message) { super(message); }
    }

    /** Immutable handle for a durable package/user creation reservation. */
    public static final class CloneReservation {
        private final String token;
        private final String packageName;
        private final int userId;

        private CloneReservation(String token, String packageName, int userId) {
            this.token = token;
            this.packageName = packageName;
            this.userId = userId;
        }

        public String getToken() { return token; }
        public String getPackageName() { return packageName; }
        public int getUserId() { return userId; }
    }

    public static class CloneEntry {
        public String packageName;
        public int userId; // Space N -> userId = N - 1
        public String displayName;
        public boolean mockGpsEnabled;
        public double latitude;
        public double longitude;
        public String locationLabel = "";
        public boolean customDeviceEnabled;
        public String deviceBrand = "";
        public String deviceModel = "";
        public Set<String> deniedPermissions = new HashSet<String>();

        public int getSpaceNumber() {
            return userId + 1;
        }
    }

    public static class GlobalEnvConfig {
        public boolean enabled = true;
        public String brand = "samsung";
        public String manufacturer = "samsung";
        public String model = "SM-S928B"; // Saved profile metadata; not applied by the pinned engine.
        public String device = "e3q";
        public String countryIso = "us";
        public String simOperator = "310260";
        public String simOperatorName = "T-Mobile";
    }


    private static String identityKey(String packageName, int userId) {
        return packageName + "\\u0000" + userId;
    }

    private static List<CloneReservation> readReservationsStrict(Context c) throws Exception {
        if (c == null) throw new IllegalArgumentException("Context is required");
        Map<String, ?> values = prefs(c).getAll();
        if (!values.containsKey(KEY_PENDING_RESERVATIONS)) return new ArrayList<CloneReservation>();
        Object raw = values.get(KEY_PENDING_RESERVATIONS);
        if (!(raw instanceof String)) throw new IllegalStateException("Reservation journal is not a String");
        JSONObject root = new JSONObject((String) raw);
        Object version = root.opt("schemaVersion");
        if (!(version instanceof Number)
                || ((Number) version).intValue() != RESERVATION_SCHEMA_VERSION
                || ((Number) version).doubleValue() != RESERVATION_SCHEMA_VERSION) {
            throw new IllegalStateException("Reservation journal schema is unsupported");
        }
        Object rawItems = root.opt("reservations");
        if (!(rawItems instanceof JSONArray)) throw new IllegalStateException("Reservation journal entries are invalid");
        JSONArray array = (JSONArray) rawItems;
        List<CloneReservation> result = new ArrayList<CloneReservation>();
        Set<String> tokens = new HashSet<String>();
        Set<String> identities = new HashSet<String>();
        for (int i = 0; i < array.length(); i++) {
            JSONObject item = array.optJSONObject(i);
            if (item == null) throw new IllegalStateException("Reservation entry is not an object");
            Object rawToken = item.opt("token");
            Object rawPackage = item.opt("pkg");
            Object rawUserId = item.opt("uid");
            if (!(rawToken instanceof String) || ((String) rawToken).trim().isEmpty()
                    || !(rawPackage instanceof String) || ((String) rawPackage).trim().isEmpty()
                    || !(rawUserId instanceof Number) || ((Number) rawUserId).intValue() < 0
                    || ((Number) rawUserId).doubleValue() != ((Number) rawUserId).intValue()) {
                throw new IllegalStateException("Reservation entry identity or token is invalid");
            }
            String token = (String) rawToken;
            String packageName = (String) rawPackage;
            int userId = ((Number) rawUserId).intValue();
            if (!tokens.add(token) || !identities.add(identityKey(packageName, userId))) {
                throw new IllegalStateException("Reservation journal contains duplicate token or identity");
            }
            result.add(new CloneReservation(token, packageName, userId));
        }
        return result;
    }

    private static String serializeReservations(List<CloneReservation> reservations) throws Exception {
        JSONObject root = new JSONObject();
        root.put("schemaVersion", RESERVATION_SCHEMA_VERSION);
        JSONArray array = new JSONArray();
        for (CloneReservation reservation : reservations) {
            JSONObject item = new JSONObject();
            item.put("token", reservation.token);
            item.put("pkg", reservation.packageName);
            item.put("uid", reservation.userId);
            array.put(item);
        }
        root.put("reservations", array);
        return root.toString();
    }

    private static String serializeEntries(List<CloneEntry> list) throws Exception {
        JSONArray arr = new JSONArray();
        Set<String> identities = new HashSet<String>();
        for (CloneEntry e : list) {
            if (e == null || e.packageName == null || e.packageName.trim().isEmpty()
                    || e.userId < 0 || e.deniedPermissions == null) {
                throw new IllegalArgumentException("Clone entry is invalid");
            }
            if (e.mockGpsEnabled && (Double.isNaN(e.latitude) || Double.isInfinite(e.latitude)
                    || Double.isNaN(e.longitude) || Double.isInfinite(e.longitude)
                    || e.latitude < -90.0d || e.latitude > 90.0d
                    || e.longitude < -180.0d || e.longitude > 180.0d)) {
                throw new IllegalArgumentException("Enabled clone location is invalid");
            }
            if (!identities.add(identityKey(e.packageName, e.userId))) {
                throw new IllegalArgumentException("Duplicate clone identity");
            }
            JSONObject o = new JSONObject();
            o.put("pkg", e.packageName);
            o.put("uid", e.userId);
            o.put("name", e.displayName == null ? e.packageName : e.displayName);
            o.put("gpsOn", e.mockGpsEnabled);
            o.put("lat", e.latitude);
            o.put("lng", e.longitude);
            o.put("locLabel", e.locationLabel == null ? "" : e.locationLabel);
            o.put("devOn", e.customDeviceEnabled);
            o.put("devBrand", e.deviceBrand == null ? "" : e.deviceBrand);
            o.put("devModel", e.deviceModel == null ? "" : e.deviceModel);
            JSONArray permissions = new JSONArray();
            for (String permission : e.deniedPermissions) {
                if (permission == null || permission.trim().isEmpty())
                    throw new IllegalArgumentException("Denied permission is invalid");
                permissions.put(permission);
            }
            o.put("denied", permissions);
            arr.put(o);
        }
        return arr.toString();
    }

    private static boolean containsReservation(List<CloneReservation> reservations,
                                               String packageName, int userId) {
        String identity = identityKey(packageName, userId);
        for (CloneReservation reservation : reservations) {
            if (identity.equals(identityKey(reservation.packageName, reservation.userId))) return true;
        }
        return false;
    }

    private static Set<Integer> validateIdInventory(List<Integer> ids, String source) {
        if (ids == null) throw new IllegalArgumentException(source + " ID inventory is required");
        Set<Integer> validated = new HashSet<Integer>();
        for (Integer id : ids) {
            if (id == null || id < 0)
                throw new IllegalStateException(source + " ID inventory contains an invalid ID");
            if (!validated.add(id))
                throw new IllegalStateException(source + " ID inventory contains a duplicate ID");
        }
        return validated;
    }

    /**
     * Reserves a globally unique, monotonically increasing Engine user ID.
     * Every Engine inventory must be confirmed before this method is called.
     */
    static synchronized CloneReservation reserveNextUserId(Context c, String packageName,
            List<Integer> engineUserIds, List<Integer> accountUserIds) throws Exception {
        if (c == null) throw new IllegalArgumentException("Context is required");
        if (packageName == null || packageName.trim().isEmpty())
            throw new IllegalArgumentException("Package name is required");

        Set<Integer> engineIds = validateIdInventory(engineUserIds, "Engine virtual-user");
        Set<Integer> accountIds = validateIdInventory(accountUserIds, "AccountManager");
        List<CloneEntry> clones = readAllStrict(c);
        List<CloneReservation> reservations = readReservationsStrict(c);
        for (CloneEntry clone : clones) {
            if (clone.userId < 0)
                throw new IllegalStateException("Clone registry contains an invalid user ID");
            if (containsReservation(reservations, clone.packageName, clone.userId))
                throw new IllegalStateException("Reservation journal conflicts with the clone registry");
        }

        int maxKnownId = -1;
        for (CloneEntry entry : clones) maxKnownId = Math.max(maxKnownId, entry.userId);
        for (CloneReservation reservation : reservations) {
            if (reservation.userId < 0)
                throw new IllegalStateException("Reservation journal contains an invalid user ID");
            maxKnownId = Math.max(maxKnownId, reservation.userId);
        }
        for (Integer id : engineIds) maxKnownId = Math.max(maxKnownId, id);
        for (Integer id : accountIds) maxKnownId = Math.max(maxKnownId, id);

        Map<String, ?> storedValues = prefs(c).getAll();
        if (storedValues.containsKey(KEY_GLOBAL_HIGH_WATER_MARK)) {
            Object rawHighWater = storedValues.get(KEY_GLOBAL_HIGH_WATER_MARK);
            if (!(rawHighWater instanceof Integer) || ((Integer) rawHighWater) < 0)
                throw new IllegalStateException("Global user-ID high-water mark is malformed");
            maxKnownId = Math.max(maxKnownId, (Integer) rawHighWater);
        }
        if (maxKnownId == Integer.MAX_VALUE)
            throw new IllegalStateException("Global virtual user-ID space is exhausted");
        int candidate = maxKnownId + 1;

        CloneReservation reservation = new CloneReservation(
                UUID.randomUUID().toString(), packageName, candidate);
        reservations.add(reservation);
        SharedPreferences.Editor editor = prefs(c).edit()
                .putString(KEY_PENDING_RESERVATIONS, serializeReservations(reservations))
                .putInt(KEY_GLOBAL_HIGH_WATER_MARK, candidate);
        if (!editor.commit())
            throw new PersistenceException("Global ID high-water and reservation commit failed");
        return reservation;
    }

    static synchronized List<CloneReservation> readPendingReservationsStrict(Context c) throws Exception {
        List<CloneEntry> clones = readAllStrict(c);
        List<CloneReservation> reservations = readReservationsStrict(c);
        for (CloneReservation reservation : reservations) {
            for (CloneEntry clone : clones) {
                if (clone.packageName.equals(reservation.packageName) && clone.userId == reservation.userId)
                    throw new IllegalStateException("Reserved identity is already present in the clone registry");
            }
        }
        return new ArrayList<CloneReservation>(reservations);
    }

    static synchronized boolean commitReservedClone(Context c, CloneEntry entry,
                                                     CloneReservation supplied) throws Exception {
        if (c == null || entry == null || supplied == null)
            throw new IllegalArgumentException("Clone entry and reservation are required");
        if (entry.packageName == null || !entry.packageName.equals(supplied.packageName)
                || entry.userId != supplied.userId)
            throw new IllegalArgumentException("Clone identity does not match its reservation");
        List<CloneEntry> clones = readAllStrict(c);
        List<CloneReservation> reservations = readPendingReservationsStrict(c);
        CloneReservation owned = null;
        for (CloneReservation reservation : reservations) {
            if (reservation.token.equals(supplied.token)) { owned = reservation; break; }
        }
        if (owned == null || !owned.packageName.equals(supplied.packageName)
                || owned.userId != supplied.userId)
            throw new IllegalStateException("Reservation is missing or does not belong to this operation");
        for (CloneEntry clone : clones) {
            if (clone.packageName.equals(entry.packageName) && clone.userId == entry.userId)
                throw new IllegalStateException("Reserved clone identity already exists");
        }
        clones.add(entry);
        List<CloneReservation> remaining = new ArrayList<CloneReservation>();
        for (CloneReservation reservation : reservations)
            if (!reservation.token.equals(supplied.token)) remaining.add(reservation);
        SharedPreferences.Editor editor = prefs(c).edit().putString(KEY_CLONES, serializeEntries(clones));
        if (remaining.isEmpty()) editor.remove(KEY_PENDING_RESERVATIONS);
        else editor.putString(KEY_PENDING_RESERVATIONS, serializeReservations(remaining));
        // A single Editor commit makes clone insertion and reservation consumption one transaction.
        return editor.commit();
    }

    static synchronized boolean releaseReservationAfterEngineAbsence(
            Context c, CloneReservation supplied, boolean engineAbsenceConfirmed) throws Exception {
        if (c == null || supplied == null) throw new IllegalArgumentException("Reservation is required");
        if (!engineAbsenceConfirmed) return false;
        List<CloneReservation> reservations = readPendingReservationsStrict(c);
        boolean found = false;
        List<CloneReservation> remaining = new ArrayList<CloneReservation>();
        for (CloneReservation reservation : reservations) {
            if (reservation.token.equals(supplied.token)
                    && reservation.packageName.equals(supplied.packageName)
                    && reservation.userId == supplied.userId) found = true;
            else remaining.add(reservation);
        }
        if (!found) return false;
        SharedPreferences.Editor editor = prefs(c).edit();
        if (remaining.isEmpty()) editor.remove(KEY_PENDING_RESERVATIONS);
        else editor.putString(KEY_PENDING_RESERVATIONS, serializeReservations(remaining));
        return editor.commit();
    }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    /**
     * Strict registry reader for mutation paths. Unlike getAll(), this never converts
     * malformed or ambiguous persisted data into an empty registry.
     */
    static List<CloneEntry> readAllStrict(Context c) throws Exception {
        if (c == null) throw new IllegalArgumentException("Context is required");
        SharedPreferences store = prefs(c);
        Map<String, ?> values = store.getAll();
        Object rawValue = values.get(KEY_CLONES);
        if (rawValue == null) {
            if (values.containsKey(KEY_CLONES)) throw new IllegalStateException("Clone registry value is null");
            return new ArrayList<CloneEntry>();
        }
        if (!(rawValue instanceof String)) throw new IllegalStateException("Clone registry is not a String");
        JSONArray arr = new JSONArray((String) rawValue);
        List<CloneEntry> out = new ArrayList<CloneEntry>();
        Set<String> identities = new HashSet<String>();
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i);
            if (o == null) throw new IllegalStateException("Clone registry entry " + i + " is not an object");
            CloneEntry e = new CloneEntry();
            Object pkg = o.opt("pkg");
            Object uid = o.opt("uid");
            if (!(pkg instanceof String) || ((String) pkg).trim().isEmpty()) {
                throw new IllegalStateException("Clone registry entry " + i + " has an invalid package name");
            }
            if (!(uid instanceof Number) || ((Number) uid).intValue() < 0
                    || ((Number) uid).doubleValue() != ((Number) uid).intValue()) {
                throw new IllegalStateException("Clone registry entry " + i + " has an invalid virtual user ID");
            }
            e.packageName = (String) pkg;
            e.userId = ((Number) uid).intValue();

            e.displayName = readOptionalString(o, "name", e.packageName);
            e.mockGpsEnabled = readOptionalBoolean(o, "gpsOn", false);
            e.latitude = readOptionalDouble(o, "lat", 0.0d);
            e.longitude = readOptionalDouble(o, "lng", 0.0d);
            e.locationLabel = readOptionalString(o, "locLabel", "");
            e.customDeviceEnabled = readOptionalBoolean(o, "devOn", false);
            e.deviceBrand = readOptionalString(o, "devBrand", "");
            e.deviceModel = readOptionalString(o, "devModel", "");

            if (e.mockGpsEnabled && (Double.isNaN(e.latitude) || Double.isInfinite(e.latitude)
                    || Double.isNaN(e.longitude) || Double.isInfinite(e.longitude)
                    || e.latitude < -90.0d || e.latitude > 90.0d
                    || e.longitude < -180.0d || e.longitude > 180.0d)) {
                throw new IllegalStateException("Clone registry entry " + i + " has invalid enabled-location coordinates");
            }

            Object denied = o.opt("denied");
            if (denied != null) {
                if (!(denied instanceof JSONArray)) throw new IllegalStateException("Denied permissions are not an array");
                JSONArray permissions = (JSONArray) denied;
                for (int j = 0; j < permissions.length(); j++) {
                    Object permission = permissions.get(j);
                    if (!(permission instanceof String) || ((String) permission).trim().isEmpty()) {
                        throw new IllegalStateException("Denied permission at entry " + i + " is invalid");
                    }
                    e.deniedPermissions.add((String) permission);
                }
            }

            String identity = e.packageName + "\\u0000" + e.userId;
            if (!identities.add(identity)) throw new IllegalStateException("Duplicate clone identity");
            out.add(e);
        }
        Collections.sort(out, new Comparator<CloneEntry>() {
            @Override public int compare(CloneEntry a, CloneEntry b) {
                if (a.userId != b.userId) return a.userId - b.userId;
                return a.displayName.compareToIgnoreCase(b.displayName);
            }
        });
        return out;
    }

    private static String readOptionalString(JSONObject object, String key, String fallback) throws Exception {
        Object value = object.opt(key);
        if (value == null) return fallback;
        if (!(value instanceof String)) throw new IllegalStateException("Field " + key + " is not a String");
        return (String) value;
    }

    private static boolean readOptionalBoolean(JSONObject object, String key, boolean fallback) {
        Object value = object.opt(key);
        if (value == null) return fallback;
        if (!(value instanceof Boolean)) throw new IllegalStateException("Field " + key + " is not a Boolean");
        return (Boolean) value;
    }

    private static double readOptionalDouble(JSONObject object, String key, double fallback) {
        Object value = object.opt(key);
        if (value == null) return fallback;
        if (!(value instanceof Number)) throw new IllegalStateException("Field " + key + " is not numeric");
        return ((Number) value).doubleValue();
    }

    public static List<CloneEntry> getAll(Context c) {
        try {
            return readAllStrict(c);
        } catch (Exception ignored) {
            // Legacy UI callers retain their historical empty-list fallback.
            // All mutation/allocation paths use readAllStrict and fail closed.
            return new ArrayList<CloneEntry>();
        }
    }

    public static synchronized boolean saveAll(Context c, List<CloneEntry> list) {
        if (c == null || list == null) return false;
        try {
            // Preserve the maximum ID from both sides of a registry update. This is
            // important when a legacy Clone row is removed before the first new reservation.
            List<CloneEntry> existing = readAllStrict(c);
            List<CloneReservation> reservations = readReservationsStrict(c);
            Set<String> reserved = new HashSet<String>();
            for (CloneReservation reservation : reservations)
                reserved.add(identityKey(reservation.packageName, reservation.userId));
            int maxKnownId = -1;
            for (CloneEntry entry : existing) {
                if (entry.userId < 0) throw new IllegalStateException("Existing Clone ID is invalid");
                maxKnownId = Math.max(maxKnownId, entry.userId);
            }
            for (CloneEntry entry : list) {
                if (entry == null || entry.userId < 0)
                    throw new IllegalStateException("New Clone registry contains an invalid entry");
                if (reserved.contains(identityKey(entry.packageName, entry.userId))) return false;
                maxKnownId = Math.max(maxKnownId, entry.userId);
            }
            Map<String, ?> storedValues = prefs(c).getAll();
            if (storedValues.containsKey(KEY_GLOBAL_HIGH_WATER_MARK)) {
                Object rawHighWater = storedValues.get(KEY_GLOBAL_HIGH_WATER_MARK);
                if (!(rawHighWater instanceof Integer) || ((Integer) rawHighWater) < 0)
                    throw new IllegalStateException("Global user-ID high-water mark is malformed");
                maxKnownId = Math.max(maxKnownId, (Integer) rawHighWater);
            }
            SharedPreferences.Editor editor = prefs(c).edit()
                    .putString(KEY_CLONES, serializeEntries(list));
            if (maxKnownId >= 0) editor.putInt(KEY_GLOBAL_HIGH_WATER_MARK, maxKnownId);
            return editor.commit();
        } catch (Exception ignored) {
            return false;
        }
    }

        public static CloneEntry getClone(Context c, String pkg, int userId) {
        for (CloneEntry e : getAll(c)) {
            if (e.packageName.equals(pkg) && e.userId == userId) return e;
        }
        return null;
    }

    public static synchronized boolean upsertClone(Context c, CloneEntry entry) {
        if (entry == null || entry.packageName == null || entry.packageName.trim().isEmpty()
                || entry.userId < 0) return false;
        try {
            List<CloneEntry> all = readAllStrict(c);
            boolean found = false;
            for (int i = 0; i < all.size(); i++) {
                CloneEntry current = all.get(i);
                if (current.packageName.equals(entry.packageName) && current.userId == entry.userId) {
                    all.set(i, entry);
                    found = true;
                    break;
                }
            }
            List<CloneReservation> reservations = readReservationsStrict(c);
            if (!found && containsReservation(reservations, entry.packageName, entry.userId)) return false;
            if (!found) all.add(entry);
            return saveAll(c, all);
        } catch (Exception ignored) {
            return false;
        }
    }

        public static synchronized boolean removeClone(Context c, String pkg, int userId) {
        if (c == null || pkg == null || pkg.trim().isEmpty() || userId < 0) return false;
        try {
            List<CloneEntry> all = readAllStrict(c);
            List<CloneEntry> kept = new ArrayList<CloneEntry>();
            for (CloneEntry entry : all)
                if (!(entry.packageName.equals(pkg) && entry.userId == userId)) kept.add(entry);
            return saveAll(c, kept);
        } catch (Exception ignored) {
            return false;
        }
    }

        /** Legacy package-scoped preview only; never use this value to install a Clone. */
        @Deprecated
        public static synchronized int nextFreeUserIdForPackage(Context c, String pkg) {
        if (c == null || pkg == null || pkg.trim().isEmpty()) return -1;
        try {
            Set<Integer> used = new HashSet<Integer>();
            for (CloneEntry entry : readAllStrict(c))
                if (entry.packageName.equals(pkg)) used.add(entry.userId);
            for (CloneReservation reservation : readReservationsStrict(c))
                if (reservation.packageName.equals(pkg)) used.add(reservation.userId);
            int uid = 0;
            while (used.contains(uid)) {
                if (uid == Integer.MAX_VALUE) return -1;
                uid++;
            }
            return uid;
        } catch (Exception ignored) {
            return -1;
        }
    }

        public static Map<Integer, List<CloneEntry>> getGroupedBySpace(Context c) {
        Map<Integer, List<CloneEntry>> map = new LinkedHashMap<Integer, List<CloneEntry>>();
        for (CloneEntry e : getAll(c)) {
            int spaceNum = e.getSpaceNumber();
            if (!map.containsKey(spaceNum)) map.put(spaceNum, new ArrayList<CloneEntry>());
            map.get(spaceNum).add(e);
        }
        if (map.isEmpty()) {
            map.put(1, new ArrayList<CloneEntry>());
        }
        return map;
    }

    static Set<Integer> readCollapsedSpaceNumbersStrict(Context c) throws Exception {
        if (c == null) throw new IllegalArgumentException("Context is required");
        Map<String, ?> values = prefs(c).getAll();
        if (!values.containsKey(KEY_COLLAPSED)) return new HashSet<Integer>();
        Object raw = values.get(KEY_COLLAPSED);
        if (!(raw instanceof Set)) throw new IllegalStateException("Collapsed Spaces value is not a String set");
        Set<Integer> result = new HashSet<Integer>();
        for (Object item : (Set<?>) raw) {
            if (!(item instanceof String)) throw new IllegalStateException("Collapsed Space key is not a String");
            int number;
            try { number = Integer.parseInt((String) item); }
            catch (NumberFormatException invalid) { throw new IllegalStateException("Collapsed Space key is invalid"); }
            if (number < 1 || !result.add(number)) throw new IllegalStateException("Collapsed Space key is out of range or duplicated");
        }
        return result;
    }

    public static boolean isSpaceCollapsed(Context c, int spaceNum) {
        if (spaceNum < 1) return false;
        try { return readCollapsedSpaceNumbersStrict(c).contains(spaceNum); }
        catch (Exception invalid) { return false; }
    }

    public static boolean setSpaceCollapsed(Context c, int spaceNum, boolean collapsed) {
        if (c == null || spaceNum < 1) return false;
        try {
            Set<String> values = new HashSet<String>();
            for (Integer number : readCollapsedSpaceNumbersStrict(c)) values.add(String.valueOf(number));
            if (collapsed) values.add(String.valueOf(spaceNum));
            else values.remove(String.valueOf(spaceNum));
            return prefs(c).edit().putStringSet(KEY_COLLAPSED, values).commit();
        } catch (Exception invalid) { return false; }
    }

    static boolean readMasterMockGpsEnabledStrict(Context c) throws Exception {
        if (c == null) throw new IllegalArgumentException("Context is required");
        Map<String, ?> values = prefs(c).getAll();
        if (!values.containsKey(KEY_MASTER_GPS)) return true;
        Object raw = values.get(KEY_MASTER_GPS);
        if (!(raw instanceof Boolean)) throw new IllegalStateException("Master GPS value is not Boolean");
        return (Boolean) raw;
    }

    public static boolean isMasterMockGpsEnabled(Context c) {
        try { return readMasterMockGpsEnabledStrict(c); }
        catch (Exception invalid) { return true; }
    }

    public static boolean setMasterMockGpsEnabled(Context c, boolean enabled) {
        if (c == null) return false;
        try {
            readMasterMockGpsEnabledStrict(c);
            return prefs(c).edit().putBoolean(KEY_MASTER_GPS, enabled).commit();
        } catch (Exception invalid) { return false; }
    }

    static GlobalEnvConfig readGlobalEnvStrict(Context c) throws Exception {
        if (c == null) throw new IllegalArgumentException("Context is required");
        GlobalEnvConfig cfg = new GlobalEnvConfig();
        Map<String, ?> values = prefs(c).getAll();
        if (!values.containsKey(KEY_GLOBAL_DEV)) return cfg;
        Object raw = values.get(KEY_GLOBAL_DEV);
        if (!(raw instanceof String)) throw new IllegalStateException("Global device profile is not a String");
        String json = (String) raw;
        if (json.trim().isEmpty()) return cfg;
        JSONObject o = new JSONObject(json);
        cfg.enabled = readOptionalBoolean(o, "enabled", cfg.enabled);
        cfg.brand = readOptionalString(o, "brand", cfg.brand);
        cfg.manufacturer = readOptionalString(o, "manufacturer", cfg.manufacturer);
        cfg.model = readOptionalString(o, "model", cfg.model);
        cfg.device = readOptionalString(o, "device", cfg.device);
        cfg.countryIso = readOptionalString(o, "countryIso", cfg.countryIso);
        cfg.simOperator = readOptionalString(o, "simOperator", cfg.simOperator);
        cfg.simOperatorName = readOptionalString(o, "simOperatorName", cfg.simOperatorName);
        return cfg;
    }

    public static GlobalEnvConfig getGlobalEnv(Context c) {
        try { return readGlobalEnvStrict(c); }
        catch (Exception ignored) { return new GlobalEnvConfig(); }
    }

    public static boolean saveGlobalEnv(Context c, GlobalEnvConfig cfg) {
        if (c == null || cfg == null || cfg.brand == null || cfg.manufacturer == null
                || cfg.model == null || cfg.device == null || cfg.countryIso == null
                || cfg.simOperator == null || cfg.simOperatorName == null) return false;
        try {
            readGlobalEnvStrict(c);
            JSONObject o = new JSONObject();
            o.put("enabled", cfg.enabled);
            o.put("brand", cfg.brand);
            o.put("manufacturer", cfg.manufacturer);
            o.put("model", cfg.model);
            o.put("device", cfg.device);
            o.put("countryIso", cfg.countryIso);
            o.put("simOperator", cfg.simOperator);
            o.put("simOperatorName", cfg.simOperatorName);
            return prefs(c).edit().putString(KEY_GLOBAL_DEV, o.toString()).commit();
        } catch (Exception ignored) { return false; }
    }

    static CloneEntry readLastActiveLaunchStrict(Context c) throws Exception {
        if (c == null) throw new IllegalArgumentException("Context is required");
        Map<String, ?> values = prefs(c).getAll();
        if (!values.containsKey(KEY_ACTIVE_LAUNCH)) return null;
        Object raw = values.get(KEY_ACTIVE_LAUNCH);
        if (!(raw instanceof String)) throw new IllegalStateException("Active launch marker is not a String");
        String json = (String) raw;
        if (json.trim().isEmpty()) return null;
        JSONObject marker = new JSONObject(json);
        Object pkg = marker.opt("pkg");
        Object uid = marker.opt("uid");
        if (!(pkg instanceof String) || ((String) pkg).trim().isEmpty()
                || !(uid instanceof Number) || ((Number) uid).intValue() < 0
                || ((Number) uid).doubleValue() != ((Number) uid).intValue())
            throw new IllegalStateException("Active launch marker identity is invalid");
        for (CloneEntry entry : readAllStrict(c)) {
            if (entry.packageName.equals(pkg) && entry.userId == ((Number) uid).intValue()) return entry;
        }
        return null;
    }

    public static boolean recordActiveLaunch(Context c, CloneEntry entry) {
        if (c == null || entry == null || entry.packageName == null
                || entry.packageName.trim().isEmpty() || entry.userId < 0) return false;
        try {
            boolean exists = false;
            for (CloneEntry current : readAllStrict(c)) {
                if (current.packageName.equals(entry.packageName) && current.userId == entry.userId) {
                    exists = true; break;
                }
            }
            if (!exists) return false;
            JSONObject o = new JSONObject();
            o.put("pkg", entry.packageName);
            o.put("uid", entry.userId);
            return prefs(c).edit().putString(KEY_ACTIVE_LAUNCH, o.toString()).commit();
        } catch (Exception ignored) { return false; }
    }

    public static CloneEntry getLastActiveLaunch(Context c) {
        try { return readLastActiveLaunchStrict(c); }
        catch (Exception ignored) { return null; }
    }

    public static VirtualHookManager.SyncSummary syncAllHooks(Context c) {
        // Location settings are applied through verified engine APIs scoped to each package/user.
        // Strict registry reads prevent corrupt data from being reported as an empty successful sync.
        // Device/SIM profile fields remain metadata until a supported scoped engine API exists.
        return VirtualHookManager.syncAllClones(c);
    }
}
