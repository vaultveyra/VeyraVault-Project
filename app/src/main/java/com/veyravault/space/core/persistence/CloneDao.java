package com.veyravault.space.core.persistence;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import java.util.List;

@Dao
public interface CloneDao {
    @Query("SELECT * FROM clones ORDER BY userId ASC, displayName COLLATE NOCASE ASC")
    List<CloneEntity> getAll();

    @Query("SELECT * FROM clones WHERE packageName = :packageName AND userId = :userId LIMIT 1")
    CloneEntity find(String packageName, int userId);

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insertOrReplace(CloneEntity entry);

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insertOrReplaceAll(List<CloneEntity> entries);

    @Query("DELETE FROM clones WHERE packageName = :packageName AND userId = :userId")
    int delete(String packageName, int userId);

    @Query("SELECT COUNT(*) FROM clones")
    int count();

    @Query("DELETE FROM clones")
    void deleteAll();
}
