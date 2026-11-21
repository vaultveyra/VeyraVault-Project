package com.veyravault.space.core.persistence;

import androidx.annotation.NonNull;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Exact semantic verifier for an imported snapshot; read-only and worker-thread only. */
public final class LegacyCloneRoomVerifier {
    private LegacyCloneRoomVerifier() { }

    public static boolean matches(
            @NonNull ClonePersistenceDatabase database,
            @NonNull LegacyCloneSnapshot snapshot) {
        if (database == null || snapshot == null) return false;

        LegacyMigrationMetadataEntity metadata = database.migrationMetadata().get();
        if (metadata == null
                || !snapshot.sha256().equals(metadata.sourceSnapshotSha256)
                || !snapshot.canonicalPayload().equals(metadata.sourceSnapshotPayload)
                || metadata.sourceFormatVersion != 1) return false;

        List<CloneEntity> storedClones = database.clones().getAll();
        if (storedClones.size() != snapshot.clones.size()) return false;
        Map<String, CloneEntity> byIdentity = new HashMap<>();
        for (CloneEntity entity : storedClones) {
            String key = identity(entity.packageName, entity.userId);
            if (byIdentity.put(key, entity) != null) return false;
        }

        for (LegacyCloneSnapshot.CloneRecord source : snapshot.clones) {
            CloneEntity stored = byIdentity.get(identity(source.packageName, source.userId));
            if (stored == null
                    || !equal(source.displayName, stored.displayName)
                    || source.mockGpsEnabled != stored.mockGpsEnabled
                    || Double.compare(source.latitude, stored.latitude) != 0
                    || Double.compare(source.longitude, stored.longitude) != 0
                    || !equal(source.locationLabel, stored.locationLabel)
                    || source.customDeviceEnabled != stored.customDeviceEnabled
                    || !equal(source.deviceBrand, stored.deviceBrand)
                    || !equal(source.deviceModel, stored.deviceModel)
                    || !equal(source.legacyJson, stored.legacyJson)) return false;
        }

        Set<String> expectedPermissions = new HashSet<>();
        for (LegacyCloneSnapshot.CloneRecord clone : snapshot.clones) {
            for (String permission : clone.deniedPermissions) {
                expectedPermissions.add(identity(clone.packageName, clone.userId) + "\u0000" + permission);
            }
        }
        Set<String> actualPermissions = new HashSet<>();
        for (DeniedPermissionEntity permission : database.deniedPermissions().getAll()) {
            actualPermissions.add(identity(permission.packageName, permission.userId) + "\u0000" + permission.permission);
        }
        if (!expectedPermissions.equals(actualPermissions)) return false;

        Set<String> actualCollapsed = new HashSet<>();
        for (CollapsedSpaceEntity item : database.collapsedSpaces().getAll()) actualCollapsed.add(item.spaceKey);
        if (!snapshot.collapsedSpaces.equals(actualCollapsed)) return false;

        GlobalDeviceProfileEntity profile = database.globalDeviceProfile().get();
        LegacyCloneSnapshot.GlobalProfile expectedProfile = snapshot.globalProfile;
        if (profile == null
                || profile.id != 1
                || profile.enabled != expectedProfile.enabled
                || !equal(profile.brand, expectedProfile.brand)
                || !equal(profile.manufacturer, expectedProfile.manufacturer)
                || !equal(profile.model, expectedProfile.model)
                || !equal(profile.device, expectedProfile.device)
                || !equal(profile.countryIso, expectedProfile.countryIso)
                || !equal(profile.simOperator, expectedProfile.simOperator)
                || !equal(profile.simOperatorName, expectedProfile.simOperatorName)) return false;

        PersistenceSettingsEntity settings = database.persistenceSettings().get();
        if (settings == null || settings.id != 1
                || settings.masterMockGpsEnabled != snapshot.masterMockGpsEnabled) return false;

        LastActiveLaunchEntity active = database.lastActiveLaunch().get();
        if (snapshot.activeLaunch == null) {
            if (active != null) return false;
        } else if (active == null
                || active.id != 1
                || !equal(active.packageName, snapshot.activeLaunch.packageName)
                || active.userId != snapshot.activeLaunch.userId) return false;

        return true;
    }

    private static String identity(String packageName, int userId) {
        return packageName + "\u0000" + userId;
    }

    private static boolean equal(String left, String right) {
        return left == null ? right == null : left.equals(right);
    }
}
