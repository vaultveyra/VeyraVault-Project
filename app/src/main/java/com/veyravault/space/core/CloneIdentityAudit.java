package com.veyravault.space.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;

/**
 * Pure, read-only analysis of Clone, Engine virtual-user and AccountManager bucket IDs.
 *
 * AccountManager data is represented only by numeric userId map keys. A numeric key is not
 * a package identity and is never attributed to a specific Clone by this helper.
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
        public final List<Integer> knownAccountManagerUserIds;
        public final List<Integer> accountManagerUserIdsWithoutCurrentEngineUser;
        public final List<Integer> accountManagerUserIdsWithoutRegisteredClone;
        public final List<Integer> accountManagerUserIdsSharedAcrossPackages;

        private InventoryReport(List<CollisionGroup> collisions, List<Integer> engineOnly,
                                List<Integer> cloneOnly, List<Integer> engineIds,
                                List<Integer> accountIds, List<Integer> accountWithoutEngine,
                                List<Integer> accountWithoutClone, List<Integer> sharedAccountIds) {
            this.crossPackageCollisions = Collections.unmodifiableList(
                    new ArrayList<CollisionGroup>(collisions));
            this.engineUserIdsWithoutRegisteredClone = Collections.unmodifiableList(
                    new ArrayList<Integer>(engineOnly));
            this.registeredCloneUserIdsMissingFromEngine = Collections.unmodifiableList(
                    new ArrayList<Integer>(cloneOnly));
            this.knownEngineUserIds = Collections.unmodifiableList(
                    new ArrayList<Integer>(engineIds));
            this.knownAccountManagerUserIds = Collections.unmodifiableList(
                    new ArrayList<Integer>(accountIds));
            this.accountManagerUserIdsWithoutCurrentEngineUser = Collections.unmodifiableList(
                    new ArrayList<Integer>(accountWithoutEngine));
            this.accountManagerUserIdsWithoutRegisteredClone = Collections.unmodifiableList(
                    new ArrayList<Integer>(accountWithoutClone));
            this.accountManagerUserIdsSharedAcrossPackages = Collections.unmodifiableList(
                    new ArrayList<Integer>(sharedAccountIds));
        }
    }

    private CloneIdentityAudit() { }

    /**
     * Compares strict Clone registry data with two independent, ID-only Engine inventories.
     * AccountManager bucket IDs are never mapped to package names or account records.
     */
    public static InventoryReport auditInventory(List<CloneStore.CloneEntry> entries,
                                                 List<Integer> engineUserIds,
                                                 List<Integer> accountManagerUserIds) {
        List<CollisionGroup> collisions = findCrossPackageCollisions(entries);
        TreeSet<Integer> engineIds = validateIds(engineUserIds, "Engine");
        TreeSet<Integer> accountIds = validateIds(accountManagerUserIds, "AccountManager");

        TreeSet<Integer> cloneIds = new TreeSet<Integer>();
        for (CloneStore.CloneEntry entry : entries) cloneIds.add(entry.userId);

        List<Integer> engineOnly = new ArrayList<Integer>();
        for (Integer id : engineIds) if (!cloneIds.contains(id)) engineOnly.add(id);

        List<Integer> cloneOnly = new ArrayList<Integer>();
        for (Integer id : cloneIds) if (!engineIds.contains(id)) cloneOnly.add(id);

        List<Integer> accountWithoutEngine = new ArrayList<Integer>();
        for (Integer id : accountIds) if (!engineIds.contains(id)) accountWithoutEngine.add(id);

        List<Integer> accountWithoutClone = new ArrayList<Integer>();
        for (Integer id : accountIds) if (!cloneIds.contains(id)) accountWithoutClone.add(id);

        List<Integer> sharedAccountIds = new ArrayList<Integer>();
        for (CollisionGroup collision : collisions) {
            if (accountIds.contains(collision.userId)) sharedAccountIds.add(collision.userId);
        }

        return new InventoryReport(collisions, engineOnly, cloneOnly,
                new ArrayList<Integer>(engineIds), new ArrayList<Integer>(accountIds),
                accountWithoutEngine, accountWithoutClone, sharedAccountIds);
    }

    private static TreeSet<Integer> validateIds(List<Integer> values, String source) {
        if (values == null) {
            throw new IllegalArgumentException(source + " numeric user-ID inventory is required");
        }
        TreeSet<Integer> ids = new TreeSet<Integer>();
        for (Integer id : values) {
            if (id == null || id < 0) {
                throw new IllegalArgumentException(source + " inventory contains an invalid user ID");
            }
            if (!ids.add(id)) {
                throw new IllegalArgumentException(source + " inventory contains a duplicate user ID");
            }
        }
        return ids;
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
