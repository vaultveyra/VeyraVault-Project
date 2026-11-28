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

    private CloneIdentityAudit() { }

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
            String identityKey = entry.packageName + "\u0000" + entry.userId;
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
