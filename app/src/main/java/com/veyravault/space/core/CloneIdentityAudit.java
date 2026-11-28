package com.veyravault.space.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Pure, read-only analysis of current Clone registry identities.
 *
 * It reports different package names that currently share one numeric virtual user ID.
 * It does not read Engine account data, credentials, tokens, app-private storage or sessions.
 */
public final class CloneIdentityAudit {
    public static final class CloneIdentity {
        public final String packageName;
        public final String displayName;
        public final int userId;

        private CloneIdentity(String packageName, String displayName, int userId) {
            this.packageName = packageName;
            this.displayName = displayName;
            this.userId = userId;
        }
    }

    public static final class CollisionGroup {
        public final int userId;
        public final List<CloneIdentity> clones;

        private CollisionGroup(int userId, List<CloneIdentity> clones) {
            this.userId = userId;
            this.clones = Collections.unmodifiableList(new ArrayList<>(clones));
        }
    }

    public static final class InventoryReport {
        public final List<CollisionGroup> crossPackageCollisions;
        public final List<Integer> engineUserIdsWithoutRegisteredClone;
        public final List<Integer> registeredCloneUserIdsMissingFromEngine;
        public final List<Integer> knownEngineUserIds;

        private InventoryReport(List<CollisionGroup> collisions, List<Integer> engineOnly,
                                List<Integer> cloneOnly, List<Integer> engineIds) {
            this.crossPackageCollisions = Collections.unmodifiableList(
                    new ArrayList<CollisionGroup>(collisions));
            this.engineUserIdsWithoutRegisteredClone = Collections.unmodifiableList(
                    new ArrayList<Integer>(engineOnly));
            this.registeredCloneUserIdsMissingFromEngine = Collections.unmodifiableList(
                    new ArrayList<Integer>(cloneOnly));
            this.knownEngineUserIds = Collections.unmodifiableList(
                    new ArrayList<Integer>(engineIds));
        }
    }

    private CloneIdentityAudit() { }

    /**
     * Compares a strict Clone registry snapshot with IDs exposed by the Engine's read-only
     * virtual-user inventory. The Engine list contains IDs only, never account/session data.
     */
    public static InventoryReport auditInventory(List<CloneStore.CloneEntry> entries,
                                                 List<Integer> engineUserIds) {
        List<CollisionGroup> collisions = findCrossPackageCollisions(entries);
        if (engineUserIds == null) {
            throw new IllegalArgumentException("Engine virtual-user inventory is required");
        }

        TreeSet<Integer> engineIds = new TreeSet<Integer>();
        for (Integer id : engineUserIds) {
            if (id == null || id < 0) {
                throw new IllegalArgumentException("Engine inventory contains an invalid virtual user ID");
            }
            if (!engineIds.add(id)) {
                throw new IllegalArgumentException("Engine inventory contains a duplicate virtual user ID");
            }
        }

        TreeSet<Integer> cloneIds = new TreeSet<Integer>();
        for (CloneStore.CloneEntry entry : entries) cloneIds.add(entry.userId);

        List<Integer> engineOnly = new ArrayList<Integer>();
        for (Integer id : engineIds) if (!cloneIds.contains(id)) engineOnly.add(id);

        List<Integer> cloneOnly = new ArrayList<Integer>();
        for (Integer id : cloneIds) if (!engineIds.contains(id)) cloneOnly.add(id);

        return new InventoryReport(collisions, engineOnly, cloneOnly,
                new ArrayList<Integer>(engineIds));
    }

    /**
     * Returns only cross-package numeric ID overlaps in a strict Clone registry snapshot.
     * Invalid input fails closed instead of being silently omitted from the diagnostic.
     */
    public static List<CollisionGroup> findCrossPackageCollisions(
            List<CloneStore.CloneEntry> entries) {
        if (entries == null) throw new IllegalArgumentException("Clone registry snapshot is required");

        Map<Integer, Map<String, CloneIdentity>> byUserId =
                new TreeMap<Integer, Map<String, CloneIdentity>>();
        Map<String, Boolean> compositeIdentities = new LinkedHashMap<String, Boolean>();

        for (CloneStore.CloneEntry entry : entries) {
            if (entry == null || entry.packageName == null || entry.packageName.trim().isEmpty()
                    || entry.userId < 0) {
                throw new IllegalArgumentException("Clone registry contains an invalid identity");
            }
            String identityKey = entry.packageName.length() + ":" + entry.packageName + ":" + entry.userId;
            if (compositeIdentities.put(identityKey, Boolean.TRUE) != null) {
                throw new IllegalArgumentException("Clone registry contains a duplicate composite identity");
            }

            Map<String, CloneIdentity> packages = byUserId.get(entry.userId);
            if (packages == null) {
                packages = new TreeMap<String, CloneIdentity>();
                byUserId.put(entry.userId, packages);
            }
            packages.put(entry.packageName, new CloneIdentity(
                    entry.packageName,
                    entry.displayName == null || entry.displayName.trim().isEmpty()
                            ? entry.packageName : entry.displayName,
                    entry.userId));
        }

        List<CollisionGroup> collisions = new ArrayList<CollisionGroup>();
        for (Map.Entry<Integer, Map<String, CloneIdentity>> group : byUserId.entrySet()) {
            if (group.getValue().size() <= 1) continue;
            collisions.add(new CollisionGroup(group.getKey(),
                    new ArrayList<CloneIdentity>(group.getValue().values())));
        }
        return Collections.unmodifiableList(collisions);
    }
}
