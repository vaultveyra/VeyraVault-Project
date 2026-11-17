package com.veyravault.space.core.persistence;

import android.os.Looper;

import androidx.annotation.NonNull;

import java.util.ArrayList;
import java.util.List;

/**
 * Explicit, worker-thread-only, one-time import into an empty Room database.
 * Not wired to application startup, CloneStore, or any normal UI flow.
 */
public final class LegacyCloneRoomImporter {
    public enum Result {
        IMPORTED,
        ALREADY_IMPORTED
    }

    private LegacyCloneRoomImporter() { }

    public static Result importIntoEmptyDatabase(
            @NonNull final ClonePersistenceDatabase database,
            @NonNull final LegacyCloneSnapshot snapshot) {
        if (database == null) throw new IllegalArgumentException("Room database is required");
        if (snapshot == null) throw new IllegalArgumentException("Validated legacy snapshot is required");
        if (Looper.myLooper() == Looper.getMainLooper()) {
            throw new IllegalStateException("Legacy clone import must run on a worker thread");
        }

        final Result[] result = new Result[1];
        database.runInTransaction(new Runnable() {
            @Override public void run() {
                LegacyMigrationMetadataEntity prior = database.migrationMetadata().get();
                if (prior != null) {
                    if (prior.sourceSnapshotSha256.equals(snapshot.sha256())) {
                        result[0] = Result.ALREADY_IMPORTED;
                        return;
                    }
                    throw new IllegalStateException("Room already contains a different legacy migration snapshot");
                }

                if (database.clones().count() != 0
                        || database.deniedPermissions().count() != 0
                        || database.collapsedSpaces().count() != 0
                        || database.globalDeviceProfile().count() != 0
                        || database.persistenceSettings().count() != 0
                        || database.lastActiveLaunch().count() != 0) {
                    throw new IllegalStateException("Refusing to import into a non-empty Room database without migration provenance");
                }

                List<CloneEntity> clones = new ArrayList<>();
                List<DeniedPermissionEntity> permissions = new ArrayList<>();
                for (LegacyCloneSnapshot.CloneRecord record : snapshot.clones) {
                    CloneEntity entity = new CloneEntity();
                    entity.packageName = record.packageName;
                    entity.userId = record.userId;
                    entity.displayName = record.displayName;
                    entity.mockGpsEnabled = record.mockGpsEnabled;
                    entity.latitude = record.latitude;
                    entity.longitude = record.longitude;
                    entity.locationLabel = record.locationLabel;
                    entity.customDeviceEnabled = record.customDeviceEnabled;
                    entity.deviceBrand = record.deviceBrand;
                    entity.deviceModel = record.deviceModel;
                    entity.legacyJson = record.legacyJson;
                    clones.add(entity);

                    for (String permission : record.deniedPermissions) {
                        DeniedPermissionEntity denied = new DeniedPermissionEntity();
                        denied.packageName = record.packageName;
                        denied.userId = record.userId;
                        denied.permission = permission;
                        permissions.add(denied);
                    }
                }

                if (!clones.isEmpty()) database.clones().insertOrReplaceAll(clones);
                if (!permissions.isEmpty()) database.deniedPermissions().insertOrReplaceAll(permissions);

                List<CollapsedSpaceEntity> collapsed = new ArrayList<>();
                for (String key : snapshot.collapsedSpaces) {
                    CollapsedSpaceEntity entity = new CollapsedSpaceEntity();
                    entity.spaceKey = key;
                    collapsed.add(entity);
                }
                if (!collapsed.isEmpty()) database.collapsedSpaces().insertAll(collapsed);

                LegacyCloneSnapshot.GlobalProfile sourceProfile = snapshot.globalProfile;
                GlobalDeviceProfileEntity profile = new GlobalDeviceProfileEntity();
                profile.id = 1;
                profile.enabled = sourceProfile.enabled;
                profile.brand = sourceProfile.brand;
                profile.manufacturer = sourceProfile.manufacturer;
                profile.model = sourceProfile.model;
                profile.device = sourceProfile.device;
                profile.countryIso = sourceProfile.countryIso;
                profile.simOperator = sourceProfile.simOperator;
                profile.simOperatorName = sourceProfile.simOperatorName;
                database.globalDeviceProfile().save(profile);

                PersistenceSettingsEntity settings = new PersistenceSettingsEntity();
                settings.id = 1;
                settings.masterMockGpsEnabled = snapshot.masterMockGpsEnabled;
                database.persistenceSettings().save(settings);

                if (snapshot.activeLaunch != null) {
                    LastActiveLaunchEntity marker = new LastActiveLaunchEntity();
                    marker.id = 1;
                    marker.packageName = snapshot.activeLaunch.packageName;
                    marker.userId = snapshot.activeLaunch.userId;
                    database.lastActiveLaunch().save(marker);
                }

                LegacyMigrationMetadataEntity metadata = new LegacyMigrationMetadataEntity();
                metadata.id = 1;
                metadata.sourceSnapshotSha256 = snapshot.sha256();
                metadata.sourceSnapshotPayload = snapshot.canonicalPayload();
                metadata.sourceFormatVersion = 1;
                database.migrationMetadata().insert(metadata);
                result[0] = Result.IMPORTED;
            }
        });
        return result[0];
    }
}
