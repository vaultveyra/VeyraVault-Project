package com.veyravault.space.core.persistence;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

@Dao
public interface GlobalDeviceProfileDao {
    @Query("SELECT * FROM global_device_profile WHERE id = 1 LIMIT 1")
    GlobalDeviceProfileEntity get();

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void save(GlobalDeviceProfileEntity profile);
}
