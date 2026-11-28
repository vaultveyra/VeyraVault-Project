package com.veyravault.space.core.persistence;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

@Dao
public interface LastActiveLaunchDao {
    @Query("SELECT * FROM last_active_launch WHERE id = 1 LIMIT 1")
    LastActiveLaunchEntity get();

    @Query("SELECT COUNT(*) FROM last_active_launch")
    int count();

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void save(LastActiveLaunchEntity marker);

    @Query("DELETE FROM last_active_launch WHERE id = 1")
    void clear();
}
