package com.veyravault.space.core.persistence;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

@Dao
public interface PersistenceSettingsDao {
    @Query("SELECT * FROM persistence_settings WHERE id = 1 LIMIT 1")
    PersistenceSettingsEntity get();

    @Query("SELECT COUNT(*) FROM persistence_settings")
    int count();

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void save(PersistenceSettingsEntity settings);
}
