package com.veyravault.space.core.persistence;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import java.util.List;

@Dao
public interface CollapsedSpaceDao {
    @Query("SELECT * FROM collapsed_spaces ORDER BY spaceKey ASC")
    List<CollapsedSpaceEntity> getAll();

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insertAll(List<CollapsedSpaceEntity> spaces);

    @Query("SELECT COUNT(*) FROM collapsed_spaces")
    int count();

    @Query("DELETE FROM collapsed_spaces")
    void deleteAll();
}
