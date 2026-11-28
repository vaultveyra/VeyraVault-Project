package com.veyravault.space.core;

import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

@RunWith(AndroidJUnit4.class)
public class CloneIdentityAuditInstrumentationTest {
    @Test public void reportsOnlyDifferentPackagesSharingTheSameNumericUserId() {
        CloneStore.CloneEntry alpha = entry("com.example.alpha", 0, "Alpha");
        CloneStore.CloneEntry beta = entry("com.example.beta", 0, "Beta");
        CloneStore.CloneEntry alphaSecond = entry("com.example.alpha", 1, "Alpha Space 2");
        CloneStore.CloneEntry gamma = entry("com.example.gamma", 5, "Gamma");

        List<CloneIdentityAudit.CollisionGroup> groups =
                CloneIdentityAudit.findCrossPackageCollisions(
                        Arrays.asList(gamma, beta, alphaSecond, alpha));

        assertEquals(1, groups.size());
        CloneIdentityAudit.CollisionGroup collision = groups.get(0);
        assertEquals(0, collision.userId);
        assertEquals(2, collision.clones.size());
        assertEquals("com.example.alpha", collision.clones.get(0).packageName);
        assertEquals("com.example.beta", collision.clones.get(1).packageName);
        assertEquals("Alpha", collision.clones.get(0).displayName);
        assertEquals("Beta", collision.clones.get(1).displayName);
    }

    @Test public void returnsNoCollisionForOnePackageOrUniqueNumericIds() {
        List<CloneIdentityAudit.CollisionGroup> groups =
                CloneIdentityAudit.findCrossPackageCollisions(Arrays.asList(
                        entry("com.example.single", 0, "One"),
                        entry("com.example.single", 1, "Two"),
                        entry("com.example.other", 2, "Other")));
        assertTrue(groups.isEmpty());
    }

    @Test public void rejectsDuplicateCompositeIdentityInsteadOfHidingCorruptRegistryData() {
        try {
            CloneIdentityAudit.findCrossPackageCollisions(Arrays.asList(
                    entry("com.example.duplicate", 3, "First"),
                    entry("com.example.duplicate", 3, "Second")));
            fail("A duplicate package/user identity must fail closed");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("duplicate composite identity"));
        }
    }

    @Test public void collisionReportIsImmutable() {
        List<CloneIdentityAudit.CollisionGroup> groups =
                CloneIdentityAudit.findCrossPackageCollisions(Arrays.asList(
                        entry("com.example.alpha", 0, "Alpha"),
                        entry("com.example.beta", 0, "Beta")));
        try {
            groups.clear();
            fail("Top-level collision report must be immutable");
        } catch (UnsupportedOperationException expected) {
            assertEquals(1, groups.size());
        }
        try {
            groups.get(0).clones.clear();
            fail("Collision identity list must be immutable");
        } catch (UnsupportedOperationException expected) {
            assertEquals(2, groups.get(0).clones.size());
        }
    }

    @Test public void engineInventoryReportsUnlinkedAndMissingCloneUserIds() {
        List<CloneStore.CloneEntry> entries = Arrays.asList(
                entry("com.example.alpha", 0, "Alpha"),
                entry("com.example.beta", 0, "Beta"),
                entry("com.example.alpha", 1, "Alpha Space 2"));

        CloneIdentityAudit.InventoryReport report =
                CloneIdentityAudit.auditInventory(entries, Arrays.asList(2, 0));

        assertEquals(1, report.crossPackageCollisions.size());
        assertEquals(0, report.crossPackageCollisions.get(0).userId);
        assertEquals(Arrays.asList(2), report.engineUserIdsWithoutRegisteredClone);
        assertEquals(Arrays.asList(1), report.registeredCloneUserIdsMissingFromEngine);
        assertEquals(Arrays.asList(0, 2), report.knownEngineUserIds);
    }

    @Test public void engineInventoryRejectsDuplicateOrInvalidIds() {
        List<CloneStore.CloneEntry> entries =
                Arrays.asList(entry("com.example.alpha", 0, "Alpha"));
        for (List<Integer> ids : Arrays.asList(
                Arrays.asList(0, 0),
                Arrays.asList(-1),
                Arrays.asList((Integer) null))) {
            try {
                CloneIdentityAudit.auditInventory(entries, ids);
                fail("Invalid Engine virtual-user inventory must fail closed");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("Engine"));
            }
        }
    }

    @Test public void inventoryReportCollectionsAreImmutable() {
        CloneIdentityAudit.InventoryReport report = CloneIdentityAudit.auditInventory(
                Arrays.asList(entry("com.example.alpha", 0, "Alpha")),
                Arrays.asList(0, 4));
        try {
            report.knownEngineUserIds.clear();
            fail("Engine ID inventory must be immutable");
        } catch (UnsupportedOperationException expected) {
            assertEquals(Arrays.asList(0, 4), report.knownEngineUserIds);
        }
        try {
            report.engineUserIdsWithoutRegisteredClone.clear();
            fail("Unlinked Engine ID inventory must be immutable");
        } catch (UnsupportedOperationException expected) {
            assertEquals(Arrays.asList(4), report.engineUserIdsWithoutRegisteredClone);
        }
    }

    private static CloneStore.CloneEntry entry(String packageName, int userId, String displayName) {
        CloneStore.CloneEntry entry = new CloneStore.CloneEntry();
        entry.packageName = packageName;
        entry.userId = userId;
        entry.displayName = displayName;
        return entry;
    }
}
