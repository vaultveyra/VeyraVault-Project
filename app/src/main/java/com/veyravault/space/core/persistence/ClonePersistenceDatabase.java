package com.veyravault.space.core.persistence;

import androidx.room.Database;
import androidx.room.RoomDatabase;

@Database(
    entities = {
        CloneEntity.class,
        DeniedPermissionEntity.class,
        CollapsedSpaceEntity.class,
        GlobalDeviceProfileEntity.class,
        PersistenceSettingsEntity.class,
        LastActiveLaunchEntity.class
    },
    version = 1,
    exportSchema = true
)
public abstract class ClonePersistenceDatabase extends RoomDatabase {
    public abstract CloneDao clones();
    public abstract DeniedPermissionDao deniedPermissions();
    public abstract CollapsedSpaceDao collapsedSpaces();
    public abstract GlobalDeviceProfileDao globalDeviceProfile();
    public abstract PersistenceSettingsDao persistenceSettings();
    public abstract LastActiveLaunchDao lastActiveLaunch();
}
