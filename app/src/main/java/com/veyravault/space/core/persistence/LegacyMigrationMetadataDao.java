package com.veyravault.space.core.persistence;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

@Dao
public interface LegacyMigrationMetadataDao {
    @Query("SELECT * FROM legacy_migration_metadata WHERE id = 1 LIMIT 1")
    LegacyMigrationMetadataEntity get();

    @Query("SELECT COUNT(*) FROM legacy_migration_metadata")
    int count();

    @Insert(onConflict = OnConflictStrategy.ABORT)
    void insert(LegacyMigrationMetadataEntity metadata);
}
